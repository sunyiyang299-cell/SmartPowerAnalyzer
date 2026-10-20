"""Isolated, repeatable performance probe; synthetic data only, no network.

Run from the repository: python tools/quality_benchmark.py --count 1000 --output <directory>
Produces JSON lines with wall/CPU time, Windows process peak working set, and GUI
heartbeat gaps. Output files include a complete PDF anomaly listing (no truncation).
"""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QEventLoop, QTimer
from smartpower.application import create_application
from smartpower.analysis.service import analyze_dataset
from smartpower.anomaly.detector import detect_anomalies
from smartpower.anomaly.models import Thresholds
from smartpower.data.demo import generate_demo, export_demo
from smartpower.data.importer import import_file
from smartpower.reporting.service import build_report_snapshot
from smartpower.reporting.pdf_exporter import export_pdf
from smartpower.reporting.excel_exporter import export_excel
from smartpower.storage.repository import DatasetRepository
from smartpower.ui.tasks import TaskThread
from smartpower.visualization.plot_widget import TimePlotWidget


def peak_mib():
    if os.name != 'nt':
        return None
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [(name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    get_info = ctypes.WinDLL('psapi').GetProcessMemoryInfo
    get_info.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    if not get_info(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return round(counters.PeakWorkingSetSize / 2**20, 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeat', type=int, default=1)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ['SMARTPOWER_SETTINGS_PATH'] = str(args.output / 'settings.json')
    os.environ['SMARTPOWER_DB_PATH'] = str(args.output / 'unused.sqlite3')
    app = create_application([])
    for iteration in range(args.repeat):
        directory = args.output / str(iteration)
        directory.mkdir()
        last_tick = [time.perf_counter()]
        gaps = []
        heartbeat = QTimer()
        heartbeat.setInterval(10)
        def tick():
            now = time.perf_counter()
            gaps.append(now - last_tick[0])
            last_tick[0] = now
        heartbeat.timeout.connect(tick)
        def measure(name, operation, background=True):
            gaps.clear()
            last_tick[0] = start = time.perf_counter()
            cpu = time.process_time()
            heartbeat.start()
            if background:
                loop = QEventLoop()
                thread = TaskThread(operation)
                thread.finished.connect(loop.quit)
                thread.start()
                loop.exec()
                thread.wait()
                if thread.error:
                    raise RuntimeError(thread.error)
                result = thread.result
            else:
                result = operation()
                app.processEvents()
            tick()
            heartbeat.stop()
            print(json.dumps(dict(count=args.count, iteration=iteration, task=name,
                                  seconds=round(time.perf_counter()-start, 4),
                                  cpu_seconds=round(time.process_time()-cpu, 4),
                                  process_peak_mib=peak_mib(), heartbeat_count=len(gaps),
                                  max_heartbeat_gap_seconds=round(max(gaps), 4)), ensure_ascii=False), flush=True)
            return result
        dataset = generate_demo(args.count)
        csv = directory / '模拟输入.csv'
        export_demo(dataset, csv)
        loaded = measure('import_csv', lambda: import_file(csv))
        repo = DatasetRepository(directory / 'isolated.sqlite3')
        identifier = measure('sqlite_save', lambda: repo.save(loaded, loaded.name))
        saved = measure('sqlite_load', lambda: repo.load(identifier))
        analysis = measure('analysis', lambda: analyze_dataset(saved, dataset_id=identifier))
        thresholds = Thresholds(220, 240, 20)
        detection = measure('anomaly', lambda: detect_anomalies(saved, thresholds, identifier))
        chart = TimePlotWidget('voltage')
        chart.resize(900, 650)
        chart.show()
        def draw():
            chart.set_result(analysis)
            chart.set_detection(detection)
            app.processEvents()
            assert chart.grab().save(str(directory / '图表.png'))
        measure('plot_and_png', draw, background=False)
        chart.close()
        chart.deleteLater()
        snapshot = measure('report_snapshot', lambda: build_report_snapshot(repo, identifier, thresholds=thresholds))
        measure('pdf', lambda: export_pdf(snapshot, directory / '报告.pdf'))
        measure('xlsx', lambda: export_excel(snapshot, directory / '报告.xlsx'))
        print(json.dumps(dict(count=args.count, iteration=iteration, events=len(detection.events),
                              unique_samples=detection.unique_sample_count,
                              bytes={p.suffix:p.stat().st_size for p in directory.iterdir() if p.suffix in ('.pdf','.xlsx','.png')})), flush=True)
    app.quit()


if __name__ == '__main__':
    main()
