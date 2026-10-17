"""Check every publication link: HTTP status, final URL and page title. Writes out/link_report.md and out/link_report.json.

A link passes when it returns any 2xx status. Pages that refuse automated clients (403 from DOI publishers that
block bots) are reported as 'blocked' rather than broken; check those in a browser.
"""
import html
import json
import os
import re

from common import ROOT, http_get, load_pubs, out_path


def title_of(body, ctype):
    if body[:5] == b'%PDF-':
        return '(PDF)'
    m = re.search(rb'<title[^>]*>(.*?)</title>', body[:200000], re.S | re.I)
    return html.unescape(' '.join(m.group(1).decode('utf-8', 'ignore').split()))[:160] if m else ''


def main():
    pubs = load_pubs()
    rows = []
    for p in pubs:
        for l in p.get('links') or []:
            u = l['url']
            if u.startswith('/'):
                ok = os.path.exists(os.path.join(ROOT, u.lstrip('/')))
                rows.append({'id': p['id'], 'name': l['name'], 'url': u, 'status': 200 if ok else 404, 'final': u, 'title': '(local file)', 'verdict': 'ok' if ok else 'BROKEN'})
                continue
            st, final, body, ctype = http_get(u, timeout=45, retries=1)
            t = title_of(body or b'', ctype) if 200 <= st < 300 else ''
            verdict = 'ok' if 200 <= st < 300 else ('blocked' if st in (401, 403, 418, 429) else 'BROKEN')
            rows.append({'id': p['id'], 'name': l['name'], 'url': u, 'status': st, 'final': final, 'title': t, 'verdict': verdict})
            print(st, p['id'], l['name'], u, flush=True)
    with open(out_path('link_report.json'), 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    bad = [r for r in rows if r['verdict'] != 'ok']
    with open(out_path('link_report.md'), 'w', encoding='utf-8') as f:
        f.write(f'# Link report\n\n{len(rows)} links, {len(rows) - len(bad)} ok, '
                f'{sum(r["verdict"] == "blocked" for r in rows)} blocked for bots, {sum(r["verdict"] == "BROKEN" for r in rows)} broken.\n\n')
        f.write('| verdict | status | paper | link | url | page title |\n|---|---|---|---|---|---|\n')
        for r in sorted(rows, key=lambda r: (r['verdict'] == 'ok', r['id'])):
            f.write(f"| {r['verdict']} | {r['status']} | {r['id']} | {r['name']} | {r['url']} | {r['title'].replace('|', '/')} |\n")


if __name__ == '__main__':
    main()
