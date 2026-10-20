"""Keep redistributed notice paths short without losing provenance or texts."""
from pathlib import Path


def test_license_collection_shortens_paths_and_preserves_duplicate_names(tmp_path, monkeypatch):
    from tools import collect_licenses
    source=tmp_path/'wheel'
    files=[Path('package-1.0.dist-info/licenses/component_alpha/nested/LICENSE.txt'),
           Path('package-1.0.dist-info/licenses/component_beta/nested/LICENSE.txt')]
    for path,text in zip(files,['Test fixture license A','Test fixture license B']):
        target=source/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf-8')
    class Distribution:
        version='1.0'
        metadata={'License':'Test-only fixture'}
        def locate_file(self,path):return source/path
    distribution=Distribution();distribution.files=files
    monkeypatch.setattr(collect_licenses,'NAMES',['Fixture'])
    monkeypatch.setattr(collect_licenses.metadata,'distribution',lambda name:distribution)
    output=tmp_path/'notices'
    packages=collect_licenses.collect(output)
    collected=packages[0]['license_files']
    assert len(collected)==2 and len(set(collected))==2
    assert max(len(name) for name in collected)<70
    assert {(output/name).read_text(encoding='utf-8') for name in collected}=={'Test fixture license A','Test fixture license B'}
    assert set(packages[0]['license_sources'].values())=={str(path).replace('\\','/') for path in files}


def test_window_verifier_retries_stale_handle_but_keeps_real_close_check(monkeypatch):
    import ctypes
    from ctypes import wintypes
    from tools import verify_frozen
    now=[0.0]
    posts=[]
    class Function:
        def __init__(self,call):self.call=call
        def __call__(self,*args):return self.call(*args)
    class User:pass
    user=User()
    def owner(handle,pointer):ctypes.cast(pointer,ctypes.POINTER(wintypes.DWORD)).contents.value=123
    def title(handle,buffer,length):buffer.value=verify_frozen.TITLE
    def enumerate_windows(callback,parameter):callback(202 if posts else 101,0)
    def post(handle,*args):posts.append(handle);return len(posts)>1
    for name,call in [('GetWindowThreadProcessId',owner),('GetWindowTextLengthW',lambda h:len(verify_frozen.TITLE)),
                      ('GetWindowTextW',title),('IsWindowVisible',lambda h:True),('EnumWindows',enumerate_windows),('PostMessageW',post)]:
        setattr(user,name,Function(call))
    monkeypatch.setattr(ctypes,'WinDLL',lambda *args,**kwargs:user)
    monkeypatch.setattr(ctypes,'get_last_error',lambda:1400)
    monkeypatch.setattr(verify_frozen.time,'monotonic',lambda:now[0])
    monkeypatch.setattr(verify_frozen.time,'sleep',lambda seconds:now.__setitem__(0,now[0]+seconds))
    verify_frozen.close_visible_window(123,lambda:True)
    assert posts==[101,202]


def test_window_verifier_does_not_ignore_permission_errors(monkeypatch):
    import ctypes
    from ctypes import wintypes
    from tools import verify_frozen
    import pytest
    now=[0.0]
    class Function:
        def __init__(self,call):self.call=call
        def __call__(self,*args):return self.call(*args)
    class User:pass
    user=User()
    def owner(handle,pointer):ctypes.cast(pointer,ctypes.POINTER(wintypes.DWORD)).contents.value=123
    def title(handle,buffer,length):buffer.value=verify_frozen.TITLE
    for name,call in [('GetWindowThreadProcessId',owner),('GetWindowTextLengthW',lambda h:len(verify_frozen.TITLE)),
                      ('GetWindowTextW',title),('IsWindowVisible',lambda h:True),('EnumWindows',lambda cb,p:cb(101,0)),('PostMessageW',lambda *a:False)]:
        setattr(user,name,Function(call))
    monkeypatch.setattr(ctypes,'WinDLL',lambda *args,**kwargs:user)
    monkeypatch.setattr(ctypes,'get_last_error',lambda:5)
    monkeypatch.setattr(verify_frozen.time,'monotonic',lambda:now[0])
    monkeypatch.setattr(verify_frozen.time,'sleep',lambda seconds:now.__setitem__(0,now[0]+seconds))
    with pytest.raises(OSError):verify_frozen.close_visible_window(123,lambda:True)
