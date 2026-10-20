"""Offline vector charts from V0.4 samples; no UI grabs or power formulas."""

import numpy as np
from reportlab.graphics.shapes import Drawing, Line, PolyLine, String
from reportlab.lib.colors import HexColor


def representative_indices(values, limit=1800):
    """Preserve bucket extrema for display only, retaining original time mapping."""
    if len(values) <= limit:
        return np.arange(len(values))
    selected = {0, len(values) - 1}
    for bucket in np.array_split(np.arange(len(values)), max(1, (limit - 2) // 2)):
        selected.add(int(bucket[np.argmin(values[bucket])]))
        selected.add(int(bucket[np.argmax(values[bucket])]))
    return np.array(sorted(selected))


def render_chart(snapshot, mode, font):
    a, sample = snapshot.analysis, snapshot.analysis.samples
    titles = {"voltage": "电压有效值时间曲线（V）", "current": "电流有效值时间曲线（A）",
              "power": "单相功率曲线：P（W）、S（VA）、|Q|（var）"}
    series = ({"voltage": [("电压有效值 V", sample.voltage, "#2563eb")],
               "current": [("电流有效值 A", sample.current, "#16805d")],
               "power": [("P（W）", a.power.active, "#2563eb"), ("S（VA）", a.power.apparent, "#16805d"),
                         ("|Q|（var，绝对值）", a.power.reactive_abs, "#9b44b5")]}[mode])
    drawing = Drawing(480, 260)
    drawing.add(String(0, 247, titles[mode], fontName=font, fontSize=10, fillColor=HexColor("#183153")))
    drawing.add(String(0, 230, snapshot.source_label, fontName=font, fontSize=8))
    left, bottom, width, height = 64, 52, 406, 146
    ymax = max(float(np.max(values)) for _, values, _ in series) or 1.0
    xmax = float(sample.seconds[-1]) or 1.0
    for j in range(5):
        y = bottom + height * j / 4
        drawing.add(Line(left, y, left + width, y, strokeColor=HexColor("#dce4ee"), strokeWidth=0.4))
        drawing.add(String(left - 5, y - 3, f"{ymax * (j / 4):.5g}", textAnchor="end", fontName=font, fontSize=7))
    drawing.add(Line(left, bottom, left, bottom + height, strokeColor=HexColor("#708198")))
    drawing.add(Line(left, bottom, left + width, bottom, strokeColor=HexColor("#708198")))
    for j in range(4):
        seconds = xmax * j / 3 if sample.seconds[-1] else 0
        stamp = sample.origin.astype("datetime64[ms]") + np.timedelta64(round(seconds * 1000), "ms")
        date, time = np.datetime_as_string(stamp, unit="s").split("T")
        x = left + width * j / 3
        drawing.add(String(x, 35, date, textAnchor="middle", fontName=font, fontSize=7))
        drawing.add(String(x, 24, time, textAnchor="middle", fontName=font, fontSize=7))
    drawing.add(String(240, 7, "采样时间（本地无时区）；稳定时间排序，重复时间保留", textAnchor="middle", fontName=font, fontSize=8))
    for k, (name, raw, color) in enumerate(series):
        values = raw[sample.order]
        indices = representative_indices(values)
        points = np.column_stack((left + sample.seconds[indices] / xmax * width,
                                  bottom + values[indices] / ymax * height)).ravel().tolist()
        if len(indices) == 1:
            points += [points[0] + 0.8, points[1]]
        drawing.add(PolyLine(points, strokeColor=HexColor(color), strokeWidth=0.65))
        drawing.add(Line(64 + k * 132, 213, 80 + k * 132, 213, strokeColor=HexColor(color)))
        drawing.add(String(84 + k * 132, 210, name, fontName=font, fontSize=8))
    return drawing
