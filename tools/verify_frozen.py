"""Launch the real onedir EXE with no Python/Git PATH and a separate working directory."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

TITLE='智电析电力系统运行数据分析与可视化软件 V1.0'


def normal_launch(exe, cwd, env):
    process=subprocess.Popen([str(exe)],cwd=cwd,env=env)
    user=ctypes.WinDLL('user32',use_last_error=True)
    user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowTextLengthW.argtypes=[wintypes.HWND]
    user.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
    user.IsWindowVisible.argtypes=[wintypes.HWND]
    user.PostMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
    callback_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    user.EnumWindows.argtypes=[callback_type,wintypes.LPARAM]
    found=[]
    def callback(handle, parameter):
        pid=wintypes.DWORD()
        user.GetWindowThreadProcessId(handle,ctypes.byref(pid))
        if pid.value==process.pid and user.IsWindowVisible(handle):
            length=user.GetWindowTextLengthW(handle)
            text=ctypes.create_unicode_buffer(length+1)
            user.GetWindowTextW(handle,text,length+1)
            if text.value==TITLE: found.append(handle)
        return True
    listener=callback_type(callback)
    try:
        deadline=time.monotonic()+60
        while time.monotonic()<deadline and process.poll() is None and not found:
            user.EnumWindows(listener,0)
            time.sleep(.1)
        assert found, 'No visible real EXE main window with official title'
        # HWND visibility occurs during synchronous ShowWindow. Let Qt finish
        # the initial paint/show event before exercising normal close.
        time.sleep(1)
        assert user.PostMessageW(found[0],0x0010,0,0), ctypes.WinError(ctypes.get_last_error())
        assert process.wait(timeout=30)==0
    finally:
        if process.poll() is None:
            process.kill(); process.wait()


def verify(package, output):
    package=Path(package).resolve()
    output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    copied=output/'中文分发目录'/'SmartPowerAnalyzer'
    shutil.copytree(package,copied)
    exe=copied/'SmartPowerAnalyzer.exe'
    assert exe.is_file()
    unrelated=output/'独立工作目录'; unrelated.mkdir()
    env=os.environ.copy()
    for key in ['PYTHONHOME','PYTHONPATH','VIRTUAL_ENV','QT_PLUGIN_PATH','QML2_IMPORT_PATH']:
        env.pop(key,None)
    env['PATH']=os.path.join(os.environ['WINDIR'],'System32')+';'+os.environ['WINDIR']
    env['QT_QPA_PLATFORM']='windows'
    env['TEMP']=env['TMP']=str(unrelated)
    env['SMARTPOWER_DB_PATH']=str(output/'ordinary-isolated.sqlite3')
    env['SMARTPOWER_SETTINGS_PATH']=str(output/'ordinary-settings.json')
    normal_launch(exe,unrelated,env)
    evidence={'ordinary_launch':'PASS','normal_close':'PASS','no_python_git_path':True,'independent_working_directory':True,'clean_machine':False}
    business=output/'业务验证'
    for flag,name in [('--release-check','result.json'),('--release-reopen','reopen-result.json')]:
        process=subprocess.run([str(exe),flag,str(business)],cwd=unrelated,env=env,timeout=180)
        assert process.returncode==0, (flag, process.returncode)
        result=json.loads((business/name).read_text(encoding='utf-8'))
        assert result['frozen'] and result['status']=='PASS' and result['version']=='1.0.0'
        evidence[flag]=result
    with exe.open('rb') as stream:
        evidence['exe_sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
    evidence['status']='PASS'
    (output/'frozen-verification.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(evidence,ensure_ascii=True))
    return evidence


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package');parser.add_argument('output')
    args=parser.parse_args(); verify(args.package,args.output)
