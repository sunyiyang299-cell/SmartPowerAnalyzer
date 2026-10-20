"""Isolated real Inno Setup install/uninstall/reinstall verification.

Creates only a new QA install directory and a unique Start Menu group. Refuses
an existing product registration. Existing personal application data is unused.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import uuid
import winreg

from verify_frozen import normal_launch, TITLE

KEY=r'Software\Microsoft\Windows\CurrentVersion\Uninstall\{CF8757AD-241E-49A0-8CCE-B1EA917D976A}_is1'


def shortcut_launch(path, environment):
    class Info(ctypes.Structure):
        _fields_=[('cbSize',wintypes.DWORD),('fMask',wintypes.ULONG),('hwnd',wintypes.HWND),
                  ('lpVerb',wintypes.LPCWSTR),('lpFile',wintypes.LPCWSTR),('lpParameters',wintypes.LPCWSTR),
                  ('lpDirectory',wintypes.LPCWSTR),('nShow',ctypes.c_int),('hInstApp',wintypes.HINSTANCE),
                  ('lpIDList',ctypes.c_void_p),('lpClass',wintypes.LPCWSTR),('hkeyClass',wintypes.HKEY),
                  ('dwHotKey',wintypes.DWORD),('hIcon',wintypes.HANDLE),('hProcess',wintypes.HANDLE)]
    shell=ctypes.WinDLL('shell32',use_last_error=True)
    shell.ShellExecuteExW.argtypes=[ctypes.POINTER(Info)]
    info=Info();info.cbSize=ctypes.sizeof(info);info.fMask=0x40;info.lpVerb='open';info.lpFile=str(path);info.nShow=1
    saved=os.environ.copy();os.environ.update(environment)
    try:assert shell.ShellExecuteExW(ctypes.byref(info)),ctypes.WinError(ctypes.get_last_error())
    finally:os.environ.clear();os.environ.update(saved)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetProcessId.argtypes=[wintypes.HANDLE];kernel.GetProcessId.restype=wintypes.DWORD
    kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    pid=kernel.GetProcessId(info.hProcess)
    user=ctypes.WinDLL('user32')
    CB=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    user.EnumWindows.argtypes=[CB,wintypes.LPARAM]
    user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
    user.PostMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
    user.IsWindowVisible.argtypes=[wintypes.HWND]
    found=[]
    def callback(handle, parameter):
        owner=wintypes.DWORD();user.GetWindowThreadProcessId(handle,ctypes.byref(owner))
        if owner.value==pid and user.IsWindowVisible(handle):
            text=ctypes.create_unicode_buffer(400);user.GetWindowTextW(handle,text,len(text))
            if text.value==TITLE:found.append(handle)
        return True
    handler=CB(callback)
    try:
        deadline=time.monotonic()+60
        while time.monotonic()<deadline and not found:
            user.EnumWindows(handler,0);time.sleep(.1)
        assert found,'Start Menu shortcut did not open the real main window'
        user.PostMessageW(found[0],0x10,0,0)
        assert kernel.WaitForSingleObject(info.hProcess,30000)==0
    finally:kernel.CloseHandle(info.hProcess)


def verify(installer, output):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,KEY):pass
    except FileNotFoundError:pass
    else:raise RuntimeError('Product already installed: refusing to alter an existing installation')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    install=output/'安装目录'
    group='SmartPowerAnalyzer-QA-'+uuid.uuid4().hex[:10]
    group_path=Path(os.environ['APPDATA'])/'Microsoft/Windows/Start Menu/Programs'/group
    assert not group_path.exists()
    env=os.environ.copy()
    env['TEMP']=env['TMP']=str(output)
    env['SMARTPOWER_DB_PATH']=str(output/'ordinary-isolated.sqlite3')
    env['SMARTPOWER_SETTINGS_PATH']=str(output/'ordinary-settings.json')
    env['QT_QPA_PLATFORM']='windows'
    env['PATH']=os.path.join(os.environ['WINDIR'],'System32')+';'+os.environ['WINDIR']
    for key in ['PYTHONHOME','PYTHONPATH','VIRTUAL_ENV']:env.pop(key,None)
    evidence={'ordinary_user':not bool(ctypes.windll.shell32.IsUserAnAdmin()),'desktop_shortcut':'NOT TESTED (optional task not selected)','clean_machine':False}
    def run_install(label):
        args=[str(Path(installer).resolve()),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CURRENTUSER',f'/DIR={install}',f'/GROUP={group}','/TASKS=',f'/LOG={output/(label+".log")}']
        completed=subprocess.run(args,env=env,timeout=180)
        assert completed.returncode==0,completed.returncode
        assert (install/'SmartPowerAnalyzer.exe').is_file()
        assert (group_path/'智电析 V1.0.lnk').is_file()
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,KEY) as key:
            assert winreg.QueryValueEx(key,'DisplayVersion')[0]=='1.0.0'
        evidence[label]='PASS'
    def uninstall(label):
        assert install.is_relative_to(output) and install.name=='安装目录'
        completed=subprocess.run([str(install/'unins000.exe'),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',f'/LOG={output/(label+".log")}'],env=env,timeout=120)
        assert completed.returncode==0,completed.returncode
        deadline=time.monotonic()+10
        while time.monotonic()<deadline and (install.exists() or group_path.exists()):time.sleep(.1)
        assert not (install/'SmartPowerAnalyzer.exe').exists()
        assert not group_path.exists()
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,KEY):pass
        except FileNotFoundError:pass
        else:raise AssertionError('Uninstall registration not removed')
        evidence[label]='PASS'
    run_install('install')
    exe=install/'SmartPowerAnalyzer.exe'
    normal_launch(exe,output,env);evidence['installed_directory_launch']='PASS'
    shortcut_launch(group_path/'智电析 V1.0.lnk',env);evidence['start_menu_launch']='PASS'
    user_data=output/'隔离用户数据'
    first=subprocess.run([str(exe),'--release-check',str(user_data)],cwd=output,env=env,timeout=180)
    assert first.returncode==0
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [user_data/'isolated.sqlite3',user_data/'settings.json',*user_data.glob('*.pdf'),*user_data.glob('*.xlsx')]}
    assert json.loads((user_data/'result.json').read_text(encoding='utf-8'))['status']=='PASS'
    evidence['installed_full_business']='PASS'
    uninstall('uninstall')
    assert all(hashlib.sha256((user_data/name).read_bytes()).hexdigest()==digest for name,digest in before.items())
    evidence['user_data_retained_byte_for_byte']='PASS'
    run_install('reinstall')
    second=subprocess.run([str(install/'SmartPowerAnalyzer.exe'),'--release-reopen',str(user_data)],cwd=output,env=env,timeout=120)
    assert second.returncode==0
    assert json.loads((user_data/'reopen-result.json').read_text(encoding='utf-8'))['status']=='PASS'
    evidence['data_read_after_reinstall']='PASS'
    uninstall('final_uninstall')
    assert not install.exists(), 'Installer left unexpected installation contents'
    evidence['installation_directory_clean']='PASS'
    evidence['status']='PASS'
    (output/'installer-verification.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(evidence,ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('installer');parser.add_argument('output')
    args=parser.parse_args();verify(args.installer,args.output)
