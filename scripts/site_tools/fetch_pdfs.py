"""Download a PDF for every paper (for teaser extraction). Writes out/pdfs/<id>.pdf and out/pdfs/sources.json."""
import json
import os
import re
import shutil

from common import ROOT, get_json, http_get, load_pubs, out_path, q


def europepmc_pdf_urls(pmcid):
    return [
        f'https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmcid}&blobtype=pdf',
        f'https://europepmc.org/articles/{pmcid}?pdf=render',
        f'https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/',
    ]


def pmid_to_pmcid(pmid):
    j = get_json('https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&query=' + q('EXT_ID:' + pmid + ' AND SRC:MED'))
    try:
        return j['resultList']['result'][0].get('pmcid')
    except Exception:  # noqa: BLE001
        return None


def cvf_pdf(index_url, match):
    st, _, body, _ = http_get(index_url)
    if st != 200:
        return None
    html = body.decode('utf-8', 'ignore')
    for m in re.finditer(r'href="([^"]+_paper\.pdf)"', html):
        href = m.group(1)
        name = href.rsplit('/', 1)[-1]
        if match.replace(' ', '_').lower()[:25] in name.lower():
            return 'https://openaccess.thecvf.com' + href if href.startswith('/') else href
    return None


def candidates(p):
    s = p.get('_sources') or {}
    c = []
    if s.get('pdf'):
        c.append(s['pdf'])
    if s.get('arxiv'):
        c.append('https://arxiv.org/pdf/' + s['arxiv'])
    pmcid = s.get('pmcid') or (pmid_to_pmcid(s['pmid']) if s.get('pmid') else None)
    if pmcid:
        c += europepmc_pdf_urls(pmcid)
    if s.get('cvf_index'):
        u = cvf_pdf(s['cvf_index'], s.get('cvf_match', ''))
        if u:
            c.append(u)
    for l in p.get('links') or []:
        if l['url'].lower().endswith('.pdf') and l['url'] not in c:
            c.append(l['url'])
    return c


def main():
    pubs = load_pubs()
    log = {}
    for p in pubs:
        dest = out_path('pdfs', p['id'] + '.pdf')
        got = None
        tried = []
        for u in candidates(p):
            tried.append(u)
            if u.startswith('/'):
                local = os.path.join(ROOT, u.lstrip('/'))
                if os.path.exists(local):
                    shutil.copy(local, dest)
                    got = u
                    break
                continue
            st, final, body, ctype = http_get(u, accept='application/pdf', timeout=90)
            if st == 200 and body[:5] == b'%PDF-':
                with open(dest, 'wb') as f:
                    f.write(body)
                got = final
                break
        log[p['id']] = {'pdf': got, 'tried': tried}
        print(p['id'], 'OK' if got else 'MISSING', got or '', flush=True)
    with open(out_path('pdfs', 'sources.json'), 'w') as f:
        json.dump(log, f, indent=1)


if __name__ == '__main__':
    main()
