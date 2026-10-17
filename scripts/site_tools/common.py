"""Shared helpers for the site maintenance scripts (run in GitHub Actions or locally)."""
import json
import os
import time
import urllib.parse
import urllib.request

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA = os.path.join(ROOT, '_data', 'publications.yml')
OUT = os.environ.get('SITE_TOOLS_OUT', os.path.join(ROOT, 'scripts', 'site_tools', 'out'))
UA = 'Mozilla/5.0 (bojianhou.com site maintenance; +https://bojianhou.com)'


def load_pubs():
    with open(DATA, encoding='utf-8') as f:
        return yaml.safe_load(f)


def out_path(*parts):
    p = os.path.join(OUT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def http_get(url, accept=None, timeout=40, retries=2):
    """GET a URL; returns (status, final_url, bytes, content_type). Never raises."""
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={'User-Agent': UA, **({'Accept': accept} if accept else {})})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.geturl(), r.read(), r.headers.get('Content-Type', '')
        except urllib.error.HTTPError as e:
            last = (e.code, url, e.read() if hasattr(e, 'read') else b'', e.headers.get('Content-Type', '') if e.headers else '')
            if e.code in (404, 410):
                break
        except Exception as e:  # noqa: BLE001
            last = (0, url, str(e).encode(), '')
        time.sleep(2 * (attempt + 1))
    return last


def get_json(url):
    st, _, body, _ = http_get(url, accept='application/json')
    if st != 200:
        return None
    try:
        return json.loads(body)
    except Exception:  # noqa: BLE001
        return None


def q(s):
    return urllib.parse.quote(s, safe='')
