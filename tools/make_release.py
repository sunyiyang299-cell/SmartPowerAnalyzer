"""Archive all of onedir, validate ZIP CRCs and write real SHA-256 checksums."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile


def make_release(package, output):
    package, output=Path(package).resolve(),Path(output).resolve()
    assert (package/'SmartPowerAnalyzer.exe').is_file()
    output.mkdir(parents=True,exist_ok=True)
    archive=output/'SmartPowerAnalyzer-Portable-1.0.0.zip'
    if archive.exists():raise FileExistsError('Refusing to replace an existing release archive')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as zipped:
        for path in sorted(package.rglob('*')):
            if path.is_file():
                if path.suffix.lower() in ['.sqlite3','.log'] or path.name=='settings.json':
                    raise ValueError('Private/generated data found in package: '+path.name)
                zipped.write(path,Path('SmartPowerAnalyzer')/path.relative_to(package))
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        assert 'SmartPowerAnalyzer/SmartPowerAnalyzer.exe' in zipped.namelist()
        assert any(name.endswith('/python313.dll') for name in zipped.namelist())
        entries=len(zipped.namelist())
    files=sorted([*output.glob('*.exe'),*output.glob('*.pdf'),*output.glob('*.md'),archive])
    checks=[]
    for path in files:
        with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        checks.append({'file':path.name,'bytes':path.stat().st_size,'sha256':digest})
    (output/'SHA256SUMS.txt').write_text(''.join(f"{item['sha256']}  {item['file']}\n" for item in checks),encoding='ascii')
    (output/'ARTIFACTS.json').write_text(json.dumps({'zip_entries':entries,'files':checks},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'zip_entries':entries,'files':checks}))
    return checks


if __name__=='__main__':make_release(sys.argv[1],sys.argv[2])
