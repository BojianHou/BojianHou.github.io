"""Collect title, full author list and abstract for every paper.

Sources: arXiv API (arXiv ids), Europe PMC (PMC ids / PubMed ids), Crossref (DOIs found in links).
Writes out/metadata.json keyed by publication id. Used to check author lists and to write one-sentence summaries.
"""
import json
import re
import time
import xml.etree.ElementTree as ET

from common import get_json, http_get, load_pubs, out_path, q

ATOM = '{http://www.w3.org/2005/Atom}'


def arxiv_meta(ids):
    res = {}
    for i in range(0, len(ids), 20):
        chunk = ids[i:i + 20]
        url = 'https://export.arxiv.org/api/query?max_results=50&id_list=' + ','.join(chunk)
        st, _, body, _ = http_get(url)
        if st != 200:
            continue
        root = ET.fromstring(body)
        for e in root.findall(ATOM + 'entry'):
            aid = e.findtext(ATOM + 'id', '').rsplit('/', 1)[-1]
            aid = re.sub(r'v\d+$', '', aid)
            res[aid] = {
                'source': 'arxiv',
                'title': ' '.join(e.findtext(ATOM + 'title', '').split()),
                'authors': [a.findtext(ATOM + 'name', '').strip() for a in e.findall(ATOM + 'author')],
                'abstract': ' '.join(e.findtext(ATOM + 'summary', '').split()),
                'comment': ' '.join((e.findtext('{http://arxiv.org/schemas/atom}comment') or '').split()),
                'journal_ref': ' '.join((e.findtext('{http://arxiv.org/schemas/atom}journal_ref') or '').split()),
            }
        time.sleep(3)
    return res


def europepmc(query):
    url = ('https://www.ebi.ac.uk/europepmc/webservices/rest/search?resultType=core&format=json&pageSize=1&query=' + q(query))
    j = get_json(url)
    if not j or not j.get('resultList', {}).get('result'):
        return None
    r = j['resultList']['result'][0]
    authors = [a.get('fullName') for a in r.get('authorList', {}).get('author', [])]
    return {
        'source': 'europepmc', 'title': r.get('title', ''), 'authors': authors,
        'abstract': re.sub(r'<[^>]+>', '', r.get('abstractText', '') or ''),
        'pmcid': r.get('pmcid'), 'pmid': r.get('pmid'), 'doi': r.get('doi'),
        'journal': (r.get('journalInfo') or {}).get('journal', {}).get('title'),
    }


def crossref(doi):
    j = get_json('https://api.crossref.org/works/' + q(doi))
    if not j:
        return None
    m = j['message']
    authors = [' '.join(x for x in [a.get('given'), a.get('family')] if x) for a in m.get('author', [])]
    return {
        'source': 'crossref', 'title': ' '.join((m.get('title') or [''])[0].split()), 'authors': authors,
        'abstract': re.sub(r'<[^>]+>', '', m.get('abstract', '') or ''),
        'container': (m.get('container-title') or [''])[0],
    }


def main():
    pubs = load_pubs()
    arx = sorted({p['_sources']['arxiv'] for p in pubs if p.get('_sources', {}).get('arxiv')})
    amap = arxiv_meta(arx)
    out = {}
    for p in pubs:
        s = p.get('_sources') or {}
        rec = {'site_title': p['title'], 'records': []}
        if s.get('arxiv') and s['arxiv'] in amap:
            rec['records'].append(amap[s['arxiv']])
        if s.get('pmcid'):
            r = europepmc('PMCID:' + s['pmcid'])
            if r:
                rec['records'].append(r)
        if s.get('pmid'):
            r = europepmc('EXT_ID:' + s['pmid'] + ' AND SRC:MED')
            if r:
                rec['records'].append(r)
        dois = set()
        if s.get('doi'):
            dois.add(s['doi'])
        for l in p.get('links') or []:
            m = re.match(r'https?://(?:dx\.)?doi\.org/(.+)$', l['url'])
            if m:
                dois.add(m.group(1))
        for d in sorted(dois):
            r = crossref(d)
            if r:
                r['doi'] = d
                rec['records'].append(r)
        if not rec['records']:
            # last resort: Europe PMC title search
            r = europepmc('TITLE:"' + p['title'][:180].replace('"', '') + '"')
            if r:
                rec['records'].append(r)
        out[p['id']] = rec
        print(p['id'], len(rec['records']), flush=True)
    with open(out_path('metadata.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
