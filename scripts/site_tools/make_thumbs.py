"""Make the 480-px copies of the paper thumbnails that the site serves through srcset.

Each images/pubs/<id>.webp (640x400) gets images/pubs/<id>-480.webp. Pages pick the smaller file where it is enough
(Recent papers figures, list rows on the publications page, 1x screens) and fall back to the 640-px file otherwise; a
thumbnail without a 480-px copy still works, just without srcset. Run after adding or replacing a thumbnail:
    python scripts/site_tools/make_thumbs.py
"""
from pathlib import Path

from PIL import Image

PUBS = Path(__file__).resolve().parents[2] / 'images' / 'pubs'
made = 0
for src in sorted(PUBS.glob('*.webp')):
    if src.stem.endswith('-480'):
        continue
    dst = src.with_name(src.stem + '-480.webp')
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        continue
    im = Image.open(src).convert('RGB')
    w = 480
    im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(dst, quality=82, method=6)
    made += 1
    print(f'{dst.name}: {src.stat().st_size // 1024} KB -> {dst.stat().st_size // 1024} KB')
print(f'{made} made')
