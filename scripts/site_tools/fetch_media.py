"""Download the conference-hosted posters and slides listed in media.yml into <out>/posters/ or slides/<id>.<ext>.

Usage: python scripts/site_tools/fetch_media.py <out dir>. Prints one line per file (size, type) and writes report.json.
"""
import json
import os
import sys
import urllib.request

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
report = []
for m in yaml.safe_load(open(os.path.join(HERE, 'media.yml'))):
    ext = os.path.splitext(m['url'].split('?')[0])[1].lower() or '.pdf'
    folder = {'poster': 'posters', 'slides': 'slides'}.get(m['kind'], m['kind'])
    dest = os.path.join(out, folder, m['id'] + ext)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        req = urllib.request.Request(m['url'], headers={'User-Agent': 'Mozilla/5.0 (site-tools; bojianhou.com)'})
        with urllib.request.urlopen(req, timeout=60) as r:
            data, ctype = r.read(), r.headers.get('Content-Type', '')
        open(dest, 'wb').write(data)
        report.append({**m, 'file': os.path.relpath(dest, out), 'bytes': len(data), 'type': ctype})
    except Exception as e:  # keep going; the error is in the report
        report.append({**m, 'error': str(e)[:300]})
    print(report[-1])
json.dump(report, open(os.path.join(out, 'report.json'), 'w'), indent=2)
