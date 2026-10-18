"""Generate overview thumbnails with PaperBanana for the papers listed under `run:` in papers.yml.

Needs GOOGLE_API_KEY (the figs job maps it from the GEMINI_API_KEY secret). Usage:
    python scripts/site_tools/paperbanana/run.py <out dir>
Writes <out>/<id>/ with each final image and candidate, metadata (cost) and the log, plus <out>/sheet_<id>.jpg
(all candidates side by side) and <out>/summary.json.
"""
import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
cfg = yaml.safe_load((HERE / 'papers.yml').read_text(encoding='utf-8'))
out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=True)
S = cfg['settings']


def caption(p):
    c = p['caption'].strip()
    if p.get('palette'):
        c += f" Color palette: {p['palette']}, on a white background; avoid the default pastel blue/green/purple scheme."
    return c + ' ' + cfg['thumbnail_note'].strip()


def edit(e, n=2):
    """Apply a text instruction to an existing image with the image model (n tries); save edit_<k>.png."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ['GOOGLE_API_KEY'])
    d = out / e['id']
    d.mkdir(parents=True, exist_ok=True)
    src = Image.open(HERE / e['image'])
    saved = []
    for k in range(1, n + 1):
        try:
            resp = client.models.generate_content(
                model=S['image_model'], contents=[src, e['instruction']],
                config=types.GenerateContentConfig(response_modalities=['IMAGE'],
                                                   image_config=types.ImageConfig(aspect_ratio=S['aspect_ratio'], image_size='2K')))
            for part in resp.candidates[0].content.parts:
                data = getattr(getattr(part, 'inline_data', None), 'data', None)
                if data:
                    from io import BytesIO
                    im = Image.open(BytesIO(data)).convert('RGB')
                    im.thumbnail((1800, 1800))
                    im.save(d / f'edit_{k}.png', optimize=True)
                    saved.append(f'edit_{k}.png')
                    break
        except Exception as ex:  # keep going; the error is recorded in the summary
            saved.append(f'error: {str(ex)[:300]}')
    return {'id': e['id'], 'edit': e['instruction'], 'images': saved}


def generate(pid):
    p = cfg['papers'][pid]
    d = out / pid
    d.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(p['method'])
        method_path = f.name
    cmd = ['paperbanana', 'generate', '--input', method_path,
           '--caption', caption(p),
           '--output-dir', str(d / 'runs'), '--aspect-ratio', S['aspect_ratio'],
           '--num-candidates', str(S['num_candidates']), '--budget', str(S['budget_usd']),
           '--vlm-provider', 'gemini', '--vlm-model', S['vlm_model'],
           '--image-provider', 'google_imagen', '--image-model', S['image_model'],
           '--format', 'png', '--verbose']
    with open(d / 'log.txt', 'w', encoding='utf-8') as log:
        rc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT).returncode
    return pid, rc


def collect(pid, rc):
    d = out / pid
    finals = sorted((d / 'runs').rglob('final_output.png'))
    cost = None
    for m in (d / 'runs').rglob('metadata.json'):
        try:
            c = json.loads(m.read_text()).get('cost', {})
            if m.parent.parent.name == 'runs':   # run-level metadata covers all candidates
                cost = c.get('total_cost_usd', c.get('total_usd', c))
        except (OSError, ValueError):
            pass
    imgs = []
    for i, f in enumerate(finals):
        rel = f.relative_to(d / 'runs')
        name = ('final' if len(rel.parts) == 2 else rel.parts[-2]) + '.png'
        im = Image.open(f).convert('RGB')
        im.thumbnail((1800, 1800))
        im.save(d / name, optimize=True)
        imgs.append((name, im))
    if imgs:
        h = 600
        tiles = [im.resize((int(im.width * h / im.height), h)) for _, im in imgs]
        sheet = Image.new('RGB', (sum(t.width for t in tiles) + 20 * (len(tiles) + 1), h + 70), 'white')
        x = 20
        dr = ImageDraw.Draw(sheet)
        for (name, _), t in zip(imgs, tiles):
            sheet.paste(t, (x, 50))
            dr.text((x, 15), f'{pid} / {name}', fill='black')
            x += t.width + 20
        sheet.save(out / f'sheet_{pid}.jpg', quality=88)
    return {'id': pid, 'returncode': rc, 'images': [n for n, _ in imgs], 'cost': cost}


if __name__ == '__main__':
    ids = cfg['run']
    with ThreadPoolExecutor(max_workers=S.get('parallel', 3)) as ex:
        results = list(ex.map(generate, ids))
    summary = [collect(pid, rc) for pid, rc in results]
    summary += [edit(e) for e in cfg.get('edits') or []]
    (out / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
