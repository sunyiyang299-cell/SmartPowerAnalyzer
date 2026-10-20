"""Collect installed distribution notices without private paths or test data."""
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['PySide6','PySide6_Essentials','PySide6_Addons','shiboken6','numpy','pandas',
         'pyqtgraph','openpyxl','reportlab','pillow','charset-normalizer','python-dateutil',
         'six','tzdata','colorama','et-xmlfile','packaging','pyinstaller','pyinstaller-hooks-contrib']


def collect(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    packages=[]
    for name in NAMES:
        dist=metadata.distribution(name)
        licenses=[]
        for file in dist.files or []:
            lower=str(file).lower()
            if any(marker in lower for marker in ['license','copying','notice']) and not lower.endswith(('.py','.pyc','.dll','.pyd','.h','.html','.json')):
                source=Path(dist.locate_file(file))
                if not source.is_file():continue
                relative=Path(str(file))
                if '..' in relative.parts:continue
                target=output / name / relative
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source,target)
                licenses.append(str(Path(name)/relative).replace('\\','/'))
        packages.append({'name':name,'version':dist.version,'license':dist.metadata.get('License-Expression') or (dist.metadata.get('License') or 'UNCONFIRMED').splitlines()[0], 'license_files':licenses})
    shutil.copyfile(Path(sys.base_prefix)/'LICENSE.txt', output/'Python-LICENSE.txt')
    for source in (ROOT/'packaging/licenses').iterdir():shutil.copyfile(source,output/source.name)
    (output/'inventory.json').write_text(json.dumps({'python':sys.version.split()[0],'packages':packages},ensure_ascii=False,indent=2),encoding='utf-8')
    return packages


if __name__=='__main__':
    target=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'build/notices'
    print(json.dumps(collect(target),ensure_ascii=True))
