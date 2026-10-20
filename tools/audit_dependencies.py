"""Time-bounded PyPI advisory query for the actual installed build environment."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import importlib.metadata as metadata
import json
from pathlib import Path
import sys
from urllib.request import urlopen


def scan(output):
    versions=sorted({(dist.metadata['Name'], dist.version) for dist in metadata.distributions()})
    def query(item):
        name, version=item
        url=f'https://pypi.org/pypi/{name}/{version}/json'
        row={'name':name,'version':version,'source':url}
        try:
            with urlopen(url,timeout=15) as response:
                payload=json.load(response)
            row.update(status='PASS' if not payload.get('vulnerabilities') else 'FAIL',
                       vulnerabilities=payload.get('vulnerabilities',[]))
        except Exception as error:
            row.update(status='NOT TESTED',error=type(error).__name__+': '+str(error))
        return row
    with ThreadPoolExecutor(max_workers=8) as pool: results=list(pool.map(query,versions))
    report={'tool':'stdlib PyPI JSON advisory query (not pip-audit)', 'date':datetime.now(timezone.utc).isoformat(),
            'scope':'Installed runtime, dev and build distributions; PyPI version advisories only, not binary/OS/Qt component source audit',
            'packages':results}
    report['status']='FAIL' if any(r['status']=='FAIL' for r in results) else ('NOT TESTED' if any(r['status']=='NOT TESTED' for r in results) else 'PASS')
    Path(output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'packages':len(results),'vulnerable':[r['name'] for r in results if r['status']=='FAIL'],'unqueried':[r['name'] for r in results if r['status']=='NOT TESTED']}))


if __name__=='__main__':scan(sys.argv[1])
