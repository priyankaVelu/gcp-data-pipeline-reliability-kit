"""Expose build evidence through GitHub API when artifact downloads are blocked.

Only creates an unreferenced Git blob; never changes a branch or merges anything.
The caller records its SHA in a CI annotation. Do not package environment/secrets.
"""
import base64
import io
import json
from pathlib import Path
import sys
import zipfile

folder,driver,output=map(Path,sys.argv[1:])
buffer=io.BytesIO()
with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
    if folder.exists():
        for path in sorted(folder.rglob('*')):
            if path.is_file():archive.write(path,str(path.relative_to(folder)))
    if driver.exists():archive.write(driver,'driver.log')
output.write_text(json.dumps(dict(encoding='base64',content=base64.b64encode(buffer.getvalue()).decode())))
if driver.exists():
    tail=driver.read_text()[-2500:]
    if 'Traceback' in tail:
        message=tail.replace('%','%25').replace('\r','%0D').replace('\n','%0A')
        print('::warning title=Production build diagnostic::'+message)
