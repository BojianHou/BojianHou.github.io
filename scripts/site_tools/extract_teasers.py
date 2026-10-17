"""Crop each paper's Figure 1 into a 16:10 WebP thumbnail.

For every out/pdfs/<id>.pdf: find the caption "Figure 1" / "Fig. 1" (or "图 1"), take the figure region above it
(images and vector drawings between the caption and the body text above, within the caption's column), render it,
trim whitespace, pad to 16:10 and save images/pubs/<id>.webp (640 px wide).
Manual fixes go in teaser_overrides.yml:  <id>: {page: 3, clip: [x0, y0, x1, y1]}  (PDF points, page is 1-based)
or <id>: {figure: 2} to use another figure, or <id>: {skip: true}.
Also writes out/teasers/contact_sheet.png and out/teasers/report.json for review.
"""
import io
import json
import os
import re
import sys

import pymupdf
import yaml
from PIL import Image, ImageChops, ImageDraw, ImageFont

from common import OUT, ROOT, load_pubs, out_path

HERE = os.path.dirname(__file__)
OVR = yaml.safe_load(open(os.path.join(HERE, 'teaser_overrides.yml'))) if os.path.exists(os.path.join(HERE, 'teaser_overrides.yml')) else {}
OVR = OVR or {}
DEST = os.path.join(ROOT, 'images', 'pubs')
W, H = 640, 400


def cap_re(n):
    return re.compile(r'^\s*(?:Figure|Fig\.?|FIGURE|FIG\.?|图)\s*' + str(n) + r'(?!\d)\s*[:.|：\s]', re.U)


def block_text(b):
    return ' '.join(s['text'] for l in b.get('lines', []) for s in l.get('spans', [])).strip()


def find_caption(doc, n, max_pages=8):
    rx = cap_re(n)
    for pno in range(min(len(doc), max_pages)):
        page = doc[pno]
        for b in page.get_text('dict')['blocks']:
            if b.get('type') != 0:
                continue
            t = block_text(b)
            if rx.match(t):
                return pno, pymupdf.Rect(b['bbox']), t
    return None


def graphics_rects(page):
    pr = page.rect
    rects = []
    for info in page.get_image_info():
        r = pymupdf.Rect(info['bbox'])
        if r.width > 8 and r.height > 8:
            rects.append(r)
    for d in page.get_drawings():
        r = pymupdf.Rect(d['rect'])
        if r.is_empty and (r.width < 1 and r.height < 1):
            continue
        # skip header/footer rules and full-page frames
        if r.y1 < pr.height * 0.06 or r.y0 > pr.height * 0.95:
            continue
        if r.width > pr.width * 0.9 and r.height > pr.height * 0.9:
            continue
        rects.append(r)
    return rects


def body_blocks(page):
    out = []
    for b in page.get_text('dict')['blocks']:
        if b.get('type') != 0:
            continue
        t = block_text(b)
        if len(t) > 160 and len(b.get('lines', [])) >= 2:
            out.append((pymupdf.Rect(b['bbox']), t))
    return out


def overlap_x(a, x0, x1):
    return max(0, min(a.x1, x1) - max(a.x0, x0))


def figure_region(page, cap):
    pr = page.rect
    full = cap.width > pr.width * 0.55
    if full:
        x0, x1 = pr.width * 0.04, pr.width * 0.96
    elif cap.x1 <= pr.width * 0.55:
        x0, x1 = pr.width * 0.04, pr.width * 0.52
    else:
        x0, x1 = pr.width * 0.48, pr.width * 0.96
    # top boundary: lowest body-text block above the caption in the same column
    top = pr.height * 0.05
    for r, _ in body_blocks(page):
        if r.y1 <= cap.y0 - 2 and overlap_x(r, x0, x1) > 0.5 * min(r.width, x1 - x0):
            top = max(top, r.y1)
    g = [r for r in graphics_rects(page)
         if r.y0 >= top - 2 and r.y1 <= cap.y0 + 3 and overlap_x(r, x0, x1) > 0.3 * max(r.width, 1)]
    if g:
        reg = pymupdf.Rect(g[0])
        for r in g[1:]:
            reg |= r
        # include text labels inside the graphic area
        reg = pymupdf.Rect(max(reg.x0, x0 - 4), max(reg.y0, top), min(reg.x1, x1 + 4), min(reg.y1, cap.y0))
        if reg.height > 30 and reg.width > 60:
            return reg, 'graphics'
    reg = pymupdf.Rect(x0, top, x1, cap.y0 - 1)
    if reg.height > 40:
        return reg, 'band'
    return None, 'none'


def largest_image(doc, max_pages=3):
    best = None
    for pno in range(min(len(doc), max_pages)):
        page = doc[pno]
        for info in page.get_image_info():
            r = pymupdf.Rect(info['bbox'])
            a = r.width * r.height
            if a > page.rect.width * page.rect.height * 0.08 and (best is None or a > best[2]):
                best = (pno, r, a)
    return best


def render(page, clip):
    pix = page.get_pixmap(clip=clip, matrix=pymupdf.Matrix(3, 3), alpha=False)
    return Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')


def trim(img):
    bg = Image.new('RGB', img.size, (255, 255, 255))
    diff = ImageChops.difference(img, bg).convert('L').point(lambda v: 255 if v > 18 else 0)
    box = diff.getbbox()
    return img.crop(box) if box else img


def fit(img):
    pad = int(max(img.size) * 0.04)
    w, h = img.size[0] + 2 * pad, img.size[1] + 2 * pad
    target = W / H
    if w / h > target:
        cw, ch = w, int(round(w / target))
    else:
        cw, ch = int(round(h * target)), h
    canvas = Image.new('RGB', (cw, ch), (255, 255, 255))
    canvas.paste(img, ((cw - img.size[0]) // 2, (ch - img.size[1]) // 2))
    return canvas.resize((W, H), Image.LANCZOS)


def process(pid, pdf):
    doc = pymupdf.open(pdf)
    o = OVR.get(pid) or {}
    if o.get('skip'):
        return None, {'method': 'skip'}
    if 'clip' in o:
        page = doc[o['page'] - 1]
        img = render(page, pymupdf.Rect(*o['clip']))
        return fit(trim(img)), {'method': 'override-clip', 'page': o['page']}
    n = o.get('figure', 1)
    found = find_caption(doc, n)
    if found:
        pno, cap, text = found
        reg, how = figure_region(doc[pno], cap)
        if reg is not None:
            img = trim(render(doc[pno], reg))
            if img.size[0] > 120 and img.size[1] > 80:
                return fit(img), {'method': how, 'figure': n, 'page': pno + 1, 'caption': text[:200], 'clip': [round(v, 1) for v in reg]}
    li = largest_image(doc)
    if li:
        pno, r, _ = li
        return fit(trim(render(doc[pno], r))), {'method': 'largest-image', 'page': pno + 1, 'clip': [round(v, 1) for v in r]}
    return None, {'method': 'none'}


def contact_sheet(items, path):
    cols, tw, th, lab = 4, 320, 200, 34
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * (tw + 10) + 10, rows * (th + lab + 10) + 10), (240, 240, 240))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 13)
    except Exception:  # noqa: BLE001
        font = ImageFont.load_default()
    for i, (pid, img) in enumerate(items):
        x, y = 10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + lab + 10)
        if img is not None:
            sheet.paste(img.resize((tw, th)), (x, y))
        else:
            draw.rectangle([x, y, x + tw, y + th], outline=(180, 0, 0), width=2)
        draw.text((x, y + th + 4), f'{i:02d} {pid}'[:44], fill=(0, 0, 0), font=font)
    sheet.save(path)


def main(only=None):
    os.makedirs(DEST, exist_ok=True)
    pubs = load_pubs()
    report, items = {}, []
    for p in pubs:
        pid = p['id']
        if only and pid not in only:
            continue
        pdf = os.path.join(OUT, 'pdfs', pid + '.pdf')
        if not os.path.exists(pdf):
            report[pid] = {'method': 'no-pdf'}
            items.append((pid, None))
            continue
        try:
            img, info = process(pid, pdf)
        except Exception as e:  # noqa: BLE001
            img, info = None, {'method': 'error', 'error': str(e)}
        if img is not None:
            img.save(os.path.join(DEST, pid + '.webp'), 'WEBP', quality=82, method=6)
            img.save(out_path('teasers', pid + '.png'))
        report[pid] = info
        items.append((pid, img))
        print(pid, info.get('method'), info.get('page', ''), flush=True)
    for k in range(0, len(items), 16):
        contact_sheet(items[k:k + 16], out_path('teasers', f'contact_sheet_{k // 16 + 1}.png'))
    with open(out_path('teasers', 'report.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main(set(sys.argv[1:]) or None)
