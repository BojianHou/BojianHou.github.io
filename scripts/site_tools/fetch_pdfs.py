"""Download a PDF for every paper (for teaser extraction).

Order of attempts: explicit pdf, arXiv, Europe PMC / PMC renderings, CVF open access, any .pdf link, then an arXiv
title search. When no PDF can be fetched but the paper is in PMC, the Figure 1 image itself is downloaded from
Europe PMC (out/figs/<id>.<ext>). Writes out/pdfs/<id>.pdf and out/pdfs/sources.json.
"""
import json
import os
import re
import shutil
import time
import urllib.parse
import xml.etree.ElementTree as ET

from common import ROOT, get_json, http_get, load_pubs, out_path, q

ATOM = '{http://www.w3.org/2005/Atom}'


def norm(t):
    return re.sub(r'[^a-z0-9]', '', t.lower())


def europepmc_pdf_urls(pmcid):
    return [
        f'https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmcid}&blobtype=pdf',
        f'https://europepmc.org/articles/{pmcid}?pdf=render',
        f'https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/',
    ]


def pmcid_for(p):
    s = p.get('_sources') or {}
    if s.get('pmcid'):
        return s['pmcid']
    query = 'EXT_ID:' + s['pmid'] + ' AND SRC:MED' if s.get('pmid') else 'TITLE:"' + p['title'][:180].replace('"', '') + '"'
    j = get_json('https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&resultType=lite&query=' + q(query))
    try:
        for r in j['resultList']['result']:
            if r.get('pmcid') and (s.get('pmid') or norm(r.get('title', '')).startswith(norm(p['title'])[:60])):
                return r['pmcid']
    except Exception:  # noqa: BLE001
        pass
    return None


def cvf_pdf(index_url, match):
    st, _, body, _ = http_get(index_url)
    if st != 200:
        return None
    html = body.decode('utf-8', 'ignore')
    key = norm(match)[:25]
    for m in re.finditer(r'href="([^"]+?\.pdf)"', html):
        href = m.group(1)
        if key in norm(href.rsplit('/', 1)[-1]):
            return urllib.parse.urljoin(index_url, href)
    return None


def arxiv_by_title(title):
    url = 'https://export.arxiv.org/api/query?max_results=5&search_query=' + q('ti:"' + re.sub(r'[^\w\s-]', ' ', title)[:200] + '"')
    st, _, body, _ = http_get(url)
    if st != 200:
        return None
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return None
    for e in root.findall(ATOM + 'entry'):
        if norm(e.findtext(ATOM + 'title', '')) == norm(title):
            aid = e.findtext(ATOM + 'id', '').rsplit('/abs/', 1)[-1]
            return re.sub(r'v\d+$', '', aid)
    return None


def pmc_first_figure(pmcid, dest_noext):
    """Download Figure 1 of a PMC article via Europe PMC full-text XML."""
    st, _, body, _ = http_get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML')
    if st != 200:
        return None
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return None
    for fig in root.iter('fig'):
        g = fig.find('.//graphic')
        if g is None:
            continue
        href = g.get('{http://www.w3.org/1999/xlink}href')
        if not href:
            continue
        for ext in ('jpg', 'png', 'gif', 'tif'):
            for base in (f'https://europepmc.org/articles/{pmcid}/bin/', f'https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/bin/'):
                u = base + href + ('' if href.lower().endswith(('.jpg', '.png', '.gif')) else '.' + ext)
                st2, final, img, ctype = http_get(u, timeout=60, retries=0)
                if st2 == 200 and img[:4] in (b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1', b'\xff\xd8\xff\xdb', b'\x89PNG', b'GIF8') or (st2 == 200 and 'image' in ctype):
                    path = dest_noext + '.' + ext
                    with open(path, 'wb') as f:
                        f.write(img)
                    label = (fig.findtext('label') or '').strip()
                    return {'image': u, 'label': label}
        break  # only the first figure
    return None


def candidates(p):
    s = p.get('_sources') or {}
    c = []
    if s.get('pdf'):
        c.append(s['pdf'])
    if s.get('arxiv'):
        c.append('https://arxiv.org/pdf/' + s['arxiv'])
    for u in s.get('pdf_alt', []) or []:
        c.append(u)
    if s.get('cvf_index'):
        u = cvf_pdf(s['cvf_index'], s.get('cvf_match', ''))
        if u:
            c.append(u)
    for l in p.get('links') or []:
        if l['url'].lower().endswith('.pdf') and l['url'] not in c:
            c.append(l['url'])
    return c


def try_download(u, dest):
    if u.startswith('/'):
        local = os.path.join(ROOT, u.lstrip('/'))
        if os.path.exists(local):
            shutil.copy(local, dest)
            return u
        return None
    st, final, body, ctype = http_get(u, accept='application/pdf', timeout=90, retries=1)
    if st == 200 and body[:5] == b'%PDF-':
        with open(dest, 'wb') as f:
            f.write(body)
        return final
    return None


def main():
    pubs = load_pubs()
    log = {}
    for p in pubs:
        dest = out_path('pdfs', p['id'] + '.pdf')
        got, tried, extra = None, [], {}
        for u in candidates(p):
            tried.append(u)
            got = try_download(u, dest)
            if got:
                break
        pmcid = None
        if not got:
            pmcid = pmcid_for(p)
            if pmcid:
                extra['pmcid'] = pmcid
                for u in europepmc_pdf_urls(pmcid):
                    tried.append(u)
                    got = try_download(u, dest)
                    if got:
                        break
        if not got and not (p.get('_sources') or {}).get('arxiv'):
            aid = arxiv_by_title(p['title'])
            time.sleep(3)
            if aid:
                extra['arxiv_found'] = aid
                u = 'https://arxiv.org/pdf/' + aid
                tried.append(u)
                got = try_download(u, dest)
        img_url = (p.get('_sources') or {}).get('img')
        if not got and img_url:
            st, final, img, ctype = http_get(img_url, timeout=60, retries=1)
            if st == 200 and 'image' in ctype:
                ext = 'png' if 'png' in ctype else 'jpg'
                with open(out_path('figs', p['id'] + '.' + ext), 'wb') as f:
                    f.write(img)
                extra['figure'] = {'image': img_url}
        if not got and pmcid and 'figure' not in extra:
            fig = pmc_first_figure(pmcid, out_path('figs', p['id']))
            if fig:
                extra['figure'] = fig
        log[p['id']] = {'pdf': got, 'tried': tried, **extra}
        print(p['id'], 'PDF' if got else ('FIG' if extra.get('figure') else 'MISSING'), got or extra.get('figure', {}).get('image', ''), flush=True)
    with open(out_path('pdfs', 'sources.json'), 'w') as f:
        json.dump(log, f, indent=1)


if __name__ == '__main__':
    main()
