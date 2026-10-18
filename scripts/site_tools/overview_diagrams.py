"""Draw overview diagrams for papers whose own figures are all results, data or background.

Each diagram is an SVG (1280 x 800) written to scripts/site_tools/overviews/<id>.svg. Every label paraphrases the
paper's abstract or method section; nothing is added that the paper does not state. These papers are marked
`skip: true` in teaser_overrides.yml so extract_teasers.py leaves their thumbnails alone.

    python3 scripts/site_tools/overview_diagrams.py                 # write the SVGs
    node scripts/site_tools/render_overviews.mjs <png dir>          # rasterize with the site's fonts (Playwright)
    python3 scripts/site_tools/overview_diagrams.py webp <png dir>  # save images/pubs/<id>.webp (640 x 400)
"""
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'overviews')
W, H = 1280, 800

C = dict(ink='#0D1424', t2='#36425A', t3='#5B677D', line='#AEB8C6', grid='#DCE2EA', paper='#FFFFFF', grey='#F1F3F7',
         blue='#2D4BE0', blueT='#E9EDFF', violet='#6D3FE0', violetT='#F0EAFF', teal='#0B8574', tealT='#E0F3EF',
         amber='#B8620E', amberT='#FFF0DC', rose='#C93A72', roseT='#FDE7F0')


def esc(s):
    return html.escape(s, quote=True)


def text(x, y, s, size=28, col='t2', weight=500, anchor='middle', family='Geist', italic=False):
    lines = s.split('\n')
    lh = size * 1.22
    y0 = y - (len(lines) - 1) * lh / 2
    out = []
    for i, ln in enumerate(lines):
        out.append(f'<text x="{x}" y="{y0 + i * lh:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
                   f'fill="{C.get(col, col)}" text-anchor="{anchor}" dominant-baseline="central"'
                   f'{" font-style=\"italic\"" if italic else ""}>{esc(ln)}</text>')
    return ''.join(out)


def box(x, y, w, h, s='', col='blue', size=30, weight=600, rx=22, tcol=None, fill=None, dash=False, sw=3):
    f = fill or C[col + 'T'] if col in ('blue', 'violet', 'teal', 'amber', 'rose') else (fill or C['grey'])
    st = C[col] if col in C else col
    d = ' stroke-dasharray="10 8"' if dash else ''
    r = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{f}" stroke="{st}" stroke-width="{sw}"{d}/>'
    if s:
        r += text(x + w / 2, y + h / 2, s, size, tcol or 'ink', weight)
    return r


def pill(cx, cy, s, col='blue', size=24, pad=18, h=None, filled=False, weight=600):
    w = len(s) * size * 0.55 + 2 * pad
    h = h or size * 1.7
    f = C[col] if filled else C[col + 'T']
    t = '#FFFFFF' if filled else C[col]
    return (f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{f}"/>'
            + text(cx, cy, s, size, t, weight))


def arrow(pts, col='line', w=4, head=True, dash=False):
    p = ' '.join(f'{x},{y}' for x, y in pts)
    d = ' stroke-dasharray="9 8"' if dash else ''
    m = f' marker-end="url(#ah-{col})"' if head else ''
    return f'<polyline points="{p}" fill="none" stroke="{C.get(col, col)}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"{d}{m}/>'


def title(s):
    return text(56, 64, s, 40, 'ink', 700, 'start', 'Bricolage Grotesque')


def db(cx, cy, w, h, s, col='blue', size=26):
    """Database cylinder."""
    e = h * 0.14
    f, st = C[col + 'T'], C[col]
    return (f'<path d="M{cx - w / 2},{cy - h / 2 + e} v{h - 2 * e} a{w / 2},{e} 0 0 0 {w},0 v{-(h - 2 * e)}" fill="{f}" stroke="{st}" stroke-width="3"/>'
            f'<ellipse cx="{cx}" cy="{cy - h / 2 + e}" rx="{w / 2}" ry="{e}" fill="{f}" stroke="{st}" stroke-width="3"/>'
            + text(cx, cy + e * 0.6, s, size, 'ink', 600))


def bars(x, y, w, h, vals, col='blue'):
    n = len(vals)
    bw = w / n * 0.68
    out = [f'<line x1="{x}" y1="{y + h}" x2="{x + w}" y2="{y + h}" stroke="{C["line"]}" stroke-width="3"/>']
    for i, v in enumerate(vals):
        bh = h * v
        out.append(f'<rect x="{x + i * w / n + (w / n - bw) / 2:.1f}" y="{y + h - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="4" fill="{C[col]}"/>')
    return ''.join(out)


def dots(cx, cy, n, col, r=9, spread=34, seed=0):
    import math
    out = []
    for i in range(n):
        a = (i * 2.399 + seed)
        rr = spread * math.sqrt((i + 0.5) / max(n, 1))
        out.append(f'<circle cx="{cx + rr * math.cos(a):.1f}" cy="{cy + rr * math.sin(a):.1f}" r="{r}" fill="{C[col]}"/>')
    return ''.join(out)


def svg(body):
    markers = ''.join(
        f'<marker id="ah-{k}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{C[k]}"/></marker>' for k in ('line', 'ink', 'blue', 'violet', 'teal', 'amber', 'rose', 't3'))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<defs>{markers}</defs><rect width="{W}" height="{H}" fill="#FFFFFF"/>{body}</svg>')


# ------------------------------------------------------------------ diagrams
def sem_ece():
    b = [title('Sem-ECE: calibration of open-ended answers')]
    b.append(box(56, 250, 220, 150, 'Open-ended\nquestion', 'grey', 30, tcol='ink', fill=C['grey'], dash=False))
    b.append(arrow([(286, 325), (336, 325)]))
    b.append(box(346, 270, 150, 110, 'LLM', 'violet', 36, 700))
    b.append(arrow([(506, 325), (556, 325)]))
    b.append(text(660, 150, 'sample n answers', 26, 't3'))
    for i, s in enumerate(['answer 1', 'answer 2', 'answer 3', '…', 'answer n']):
        b.append(pill(660, 205 + i * 60, s, 'violet', 24) if s != '…' else text(660, 205 + i * 60, '…', 30, 't3'))
    b.append(arrow([(770, 325), (812, 325)]))
    b.append(text(930, 150, 'group by meaning', 26, 't3'))
    for (cy, n, col, lab) in [(215, 6, 'blue', 'class A'), (325, 3, 'teal', 'class B'), (435, 1, 'amber', 'class C')]:
        b.append(f'<rect x="842" y="{cy - 42}" width="176" height="84" rx="42" fill="#FFFFFF" stroke="{C[col]}" stroke-width="3"/>')
        b.append(dots(890, cy, n, col, 8, 22))
        b.append(text(965, cy, lab, 24, col, 600))
    b.append(arrow([(1030, 325), (1068, 325)]))
    b.append(text(1155, 150, 'confidence', 26, 't3'))
    b.append(bars(1080, 215, 150, 200, [0.6, 0.3, 0.1], 'blue'))
    b.append(text(1155, 490, '= class frequency', 22, 't3'))
    b.append(text(1155, 445, 'A   B   C', 24, 't3'))
    b.append(box(110, 560, 500, 170, '', 'blue'))
    b.append(text(360, 610, 'Sem₁-ECE', 32, 'blue', 700))
    b.append(text(360, 672, 'the same samples pick the answer\nand give its confidence', 26, 'ink'))
    b.append(box(670, 560, 500, 170, '', 'teal'))
    b.append(text(920, 610, 'Sem₂-ECE', 32, 'teal', 700))
    b.append(text(920, 672, 'held-out samples give the confidence\nof the selected answer', 26, 'ink'))
    return svg(''.join(b))


def bilevel_calibration():
    b = [title('Bilevel optimization for LLM calibration')]
    b.append(box(56, 260, 250, 270, '', 'rose'))
    b.append(text(181, 305, 'Aligned LLM', 30, 'ink', 700))
    b.append(text(181, 345, 'overconfident', 26, 'rose', 600))
    b.append(bars(96, 375, 170, 120, [0.06, 0.95, 0.08, 0.05], 'rose'))
    b.append(arrow([(316, 395), (380, 395)]))
    b.append(box(392, 150, 500, 190, '', 'violet'))
    b.append(text(642, 196, 'Upper level', 30, 'violet', 700))
    b.append(text(642, 264, 'choose loss hyperparameters λ\nto maximize predictive entropy', 27, 'ink'))
    b.append(box(392, 450, 500, 190, '', 'blue'))
    b.append(text(642, 496, 'Lower level', 30, 'blue', 700))
    b.append(text(642, 564, 'train the LLM θ under\nthe parametric loss L(θ; λ)', 27, 'ink'))
    b.append(arrow([(520, 346), (520, 440)], 'violet', 5))
    b.append(text(488, 393, 'λ', 32, 'violet', 700))
    b.append(arrow([(764, 444), (764, 350)], 'blue', 5))
    b.append(text(822, 397, 'θ*(λ)', 30, 'blue', 700))
    b.append(text(642, 700, 'first-order approximation: no second-order terms, practical at LLM scale', 25, 't3'))
    b.append(arrow([(902, 395), (966, 395)]))
    b.append(box(976, 260, 250, 270, '', 'teal'))
    b.append(text(1101, 305, 'Calibrated LLM', 30, 'ink', 700))
    b.append(text(1101, 345, 'also out of domain', 26, 'teal', 600))
    b.append(bars(1016, 375, 170, 120, [0.32, 0.55, 0.38, 0.25], 'teal'))
    return svg(''.join(b))


def calibration_aligned():
    b = [title('Why alignment hurts calibration, and a fix')]
    b.append(box(56, 160, 250, 150, 'Pre-trained LLM\nwell calibrated', 'teal', 27))
    b.append(arrow([(316, 235), (366, 235)]))
    b.append(box(376, 160, 250, 150, 'Preference\nalignment', 'grey', 28, fill=C['grey'], tcol='ink'))
    b.append(arrow([(636, 235), (686, 235)]))
    b.append(box(696, 160, 270, 150, 'Aligned LLM\noverconfident', 'rose', 27))
    b.append(text(1100, 235, 'cause: preference\ncollapse carries\nover to calibration', 24, 'rose', 500))
    b.append(arrow([(831, 320), (831, 380)]))
    b.append(box(56, 390, 900, 330, '', 'blue', fill='#FFFFFF'))
    b.append(text(506, 432, 'Fine-tuning with domain knowledge', 28, 'ink', 700))
    b.append(box(90, 475, 400, 210, '', 'blue'))
    b.append(text(290, 520, 'Calibratable regime', 27, 'blue', 700))
    b.append(text(290, 600, 'CFT: calibration-aware\nfine-tuning', 25, 'ink'))
    b.append(box(522, 475, 400, 210, '', 'violet'))
    b.append(text(722, 520, 'Non-calibratable regime', 27, 'violet', 700))
    b.append(text(722, 600, 'RCFT: EM-based ECE\nregularizer in the loss', 25, 'ink'))
    b.append(arrow([(966, 555), (1016, 555)]))
    b.append(box(1026, 470, 200, 170, 'Calibrated,\naccuracy\nkept', 'teal', 27))
    return svg(''.join(b))


def online_bilevel_aistats():
    b = [title('Online bilevel optimization')]
    b.append(arrow([(80, 330), (1210, 330)], 't3', 4))
    b.append(text(1225, 300, 'time', 24, 't3', 500, 'end'))
    for i, (x, lab) in enumerate([(120, 't = 1'), (380, 't = 2'), (820, 't = T')]):
        b.append(box(x, 140, 220, 160, '', 'grey', fill='#FFFFFF', tcol='ink'))
        b.append(f'<rect x="{x}" y="140" width="220" height="80" rx="22" fill="{C["violetT"]}"/>')
        b.append(text(x + 110, 180, 'outer  fₜ(x, y)', 26, 'violet', 600))
        b.append(text(x + 110, 258, 'inner  gₜ(x, y)', 26, 'blue', 600))
        b.append(text(x + 110, 362, lab, 24, 't3'))
    b.append(text(710, 220, '…', 44, 't3'))
    b.append(box(120, 440, 700, 280, '', 'blue', fill='#FFFFFF'))
    b.append(text(470, 488, 'Online alternating time-averaged gradient', 28, 'ink', 700))
    b.append(box(150, 530, 270, 160, 'inner step:\nupdate y', 'blue', 27))
    b.append(box(480, 530, 310, 160, 'outer step: update x\nwith a time-averaged\nhypergradient', 'violet', 24))
    b.append(arrow([(426, 585), (474, 585)], 'blue'))
    b.append(arrow([(474, 640), (426, 640)], 'violet'))
    b.append(box(880, 470, 340, 220, '', 'teal'))
    b.append(text(1050, 520, 'Bilevel regret', 28, 'teal', 700))
    b.append(text(1050, 610, 'bounded by the path length\nof the inner and outer\nminimizer sequences', 25, 'ink'))
    b.append(arrow([(826, 580), (874, 580)]))
    return svg(''.join(b))


def online_bilevel_regret():
    b = [title('Stochastic online bilevel optimization')]
    b.append(box(56, 170, 300, 300, '', 'grey', fill=C['grey']))
    b.append(text(206, 215, 'fₜ and gₜ change fast', 26, 'ink', 700))
    path = 'M86,330 C120,250 150,390 185,300 S245,220 275,350 S320,270 330,300'
    b.append(f'<path d="{path}" fill="none" stroke="{C["violet"]}" stroke-width="5"/>')
    b.append(text(206, 430, 'noisy (stochastic) oracles', 24, 't3'))
    b.append(arrow([(366, 320), (416, 320)]))
    b.append(box(426, 170, 420, 300, '', 'blue', fill='#FFFFFF'))
    b.append(text(636, 215, 'New search direction', 30, 'blue', 700))
    b.append(box(456, 260, 170, 170, 'first-\norder', 'blue', 27))
    b.append(box(646, 260, 170, 170, 'zeroth-\norder', 'violet', 27))
    b.append(text(731, 450, 'function values only', 20, 'violet'))
    b.append(arrow([(856, 320), (906, 320)]))
    b.append(box(916, 170, 310, 300, '', 'teal'))
    b.append(text(1071, 245, 'Sublinear\nstochastic\nbilevel regret', 30, 'ink', 700))
    b.append(text(1071, 400, 'without window\nsmoothing', 26, 'teal', 600))
    for i, s in enumerate(['fewer oracle calls for\nthe hypergradient', 'inner, outer and linear-\nsystem updates together', 'zeroth-order estimates of\nHessians, Jacobians, gradients']):
        x = 56 + i * 395
        b.append(box(x, 540, 375, 130, s, 'blue' if i < 2 else 'violet', 23, 500))
    b.append(text(640, 730, 'applications: online parametric loss tuning, black-box adversarial attacks', 24, 't3'))
    return svg(''.join(b))


def sfl():
    b = [title('Storage fit learning with unlabeled data')]
    import random
    rnd = random.Random(3)
    b.append(box(56, 190, 230, 300, '', 'grey', fill=C['grey']))
    for i in range(34):
        x, y = 80 + rnd.random() * 180, 215 + rnd.random() * 200
        col = C['blue'] if i < 3 else (C['rose'] if i < 6 else '#AEB8C6')
        b.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="8" fill="{col}"/>')
    b.append(text(171, 455, 'few labeled,\nmany unlabeled', 23, 't3'))
    b.append(arrow([(296, 340), (340, 340)]))
    # n x n similarity matrix
    for i in range(10):
        for j in range(10):
            v = 0.15 + 0.85 * (1 if abs(i - j) < 2 else rnd.random() * 0.5)
            b.append(f'<rect x="{352 + j * 22}" y="{230 + i * 22}" width="21" height="21" fill="{C["blue"]}" fill-opacity="{v * 0.7:.2f}"/>')
    b.append(text(462, 490, 'similarity matrix\nn × n', 24, 't3'))
    b.append(text(612, 340, '≈', 60, 'ink', 500))
    for i in range(10):
        for j in range(3):
            b.append(f'<rect x="{660 + j * 22}" y="{230 + i * 22}" width="21" height="21" fill="{C["teal"]}" fill-opacity="{0.25 + rnd.random() * 0.5:.2f}"/>')
    b.append(text(693, 490, 'n × r', 24, 't3'))
    for i in range(3):
        for j in range(10):
            b.append(f'<rect x="{750 + j * 22}" y="{230 + i * 22}" width="21" height="21" fill="{C["teal"]}" fill-opacity="{0.25 + rnd.random() * 0.5:.2f}"/>')
    b.append(text(860, 330, 'r × n', 24, 't3'))
    b.append(box(740, 372, 290, 64, '', 'amber'))
    b.append(text(885, 404, 'storage budget sets r', 23, 'amber', 700))
    b.append(arrow([(1040, 340), (1084, 340)]))
    b.append(box(1094, 230, 140, 220, 'graph-\nbased\nSSL', 'blue', 27))
    b.append(box(110, 580, 500, 140, '', 'violet'))
    b.append(text(360, 620, 'Stochastic optimization', 28, 'violet', 700))
    b.append(text(360, 678, 'converges to the optimal\nlow-rank approximator', 24, 'ink'))
    b.append(box(670, 580, 500, 140, '', 'teal'))
    b.append(text(920, 620, 'Nyström method', 28, 'teal', 700))
    b.append(text(920, 678, 'finds a good approximator\nfast, for real-time use', 24, 'ink'))
    return svg(''.join(b))


def association_mining():
    b = [title('Risk features of neurodegenerative disorders in EHRs')]
    b.append(db(180, 340, 230, 260, 'EHR\n70,420\npatients', 'blue', 28))
    b.append(text(180, 505, 'Penn Medicine', 24, 't3'))
    b.append(arrow([(305, 340), (355, 340)]))
    for i, s in enumerate(['AD', 'PD', 'OD']):
        b.append(pill(420, 250 + i * 90, s, 'rose', 30, 24))
    b.append(text(420, 520, 'three NDD types', 23, 't3'))
    b.append(arrow([(478, 300), (520, 262)]))
    b.append(arrow([(478, 380), (520, 418)]))
    b.append(box(530, 195, 270, 125, 'univariate\nmethods', 'teal', 28))
    b.append(box(530, 360, 270, 125, 'multivariate\nML methods', 'violet', 28))
    b.append(arrow([(808, 258), (846, 288)]))
    b.append(arrow([(808, 422), (846, 392)]))
    b.append(f'<circle cx="965" cy="340" r="125" fill="{C["tealT"]}" stroke="{C["teal"]}" stroke-width="3"/>')
    b.append(f'<circle cx="1105" cy="340" r="125" fill="{C["violetT"]}" fill-opacity="0.7" stroke="{C["violet"]}" stroke-width="3"/>')
    b.append(text(905, 340, 'rare,\ntype-\nspecific', 21, 'teal', 600))
    b.append(text(1035, 340, 'shared:\nmost\nrobust', 22, 'ink', 700))
    b.append(text(1163, 340, 'multi-\nvariate\nonly', 21, 'violet', 600))
    b.append(text(640, 640, 'compare accuracy and the features each method finds:\noverlapping features are the most robust; univariate methods surface rare,\nNDD-specific features that matter clinically', 25, 't3'))
    return svg(''.join(b))


def clinical_modalities():
    b = [title('Survival analysis of fall and injury risk')]
    b.append(db(170, 330, 220, 250, 'EHR\n29,045\npatients', 'blue', 27))
    b.append(text(170, 485, 'aged 65+: NDD, MCI\nor another disease', 22, 't3'))
    b.append(arrow([(290, 330), (340, 330)]))
    for i, (s, col) in enumerate([('medications', 'violet'), ('laboratory tests', 'teal'), ('race, ethnicity, sex', 'amber')]):
        b.append(box(350, 200 + i * 95, 290, 75, s, col, 26, 600))
    b.append(text(495, 505, 'modalities and\nsensitive attributes', 22, 't3'))
    b.append(arrow([(650, 330), (700, 330)]))
    b.append(box(710, 220, 260, 220, '', 'blue', fill='#FFFFFF'))
    b.append(text(840, 262, 'survival models', 27, 'ink', 700))
    b.append(text(840, 300, 'several methods', 22, 't3'))
    b.append(f'<path d="M745,330 h40 v20 h45 v30 h40 v25 h60" fill="none" stroke="{C["blue"]}" stroke-width="5"/>')
    b.append(text(840, 420, 'time to fall or injury', 21, 't3'))
    b.append(arrow([(980, 330), (1030, 330)]))
    b.append(box(1040, 200, 190, 120, 'C-index', 'teal', 28))
    b.append(box(1040, 340, 190, 120, 'hazard\nratios', 'violet', 28))
    b.append(box(110, 590, 1060, 130, '', 'teal'))
    b.append(text(640, 655, 'combining medications and laboratory tests raises the C-index across methods\nand removes the association between Black race and fall/injury risk', 25, 'ink'))
    return svg(''.join(b))


def pferm():
    b = [title('PFERM: fairness with prior knowledge')]
    b.append(box(56, 170, 330, 330, '', 'grey', fill=C['grey']))
    b.append(text(221, 210, 'groups differ in prevalence', 24, 'ink', 700))
    b.append(bars(110, 250, 220, 170, [0.85, 0.5], 'rose'))
    b.append(text(166, 455, 'group A', 24, 't3'))
    b.append(text(276, 455, 'group B', 24, 't3'))
    b.append(text(221, 535, 'e.g., Alzheimer’s disease is\nmore prevalent in women', 22, 't3'))
    b.append(arrow([(396, 335), (446, 335)]))
    b.append(pill(560, 230, 'prior knowledge', 'amber', 26))
    b.append(text(560, 290, 'prevalence ratio\nbetween groups', 24, 'amber', 600))
    b.append(arrow([(560, 335), (560, 385), (690, 385)], 'amber'))
    b.append(box(700, 230, 320, 300, '', 'blue', fill='#FFFFFF'))
    b.append(text(860, 280, 'Fair ERM', 30, 'blue', 700))
    b.append(text(860, 380, 'minimize expected risk\nsubject to a fairness\nconstraint that includes\nthe prevalence ratio', 24, 'ink'))
    b.append(arrow([(1028, 380), (1054, 380)]))
    b.append(box(1060, 270, 170, 220, 'accurate\nand fair\nclassifier', 'teal', 26))
    b.append(text(640, 650, 'strict equal treatment can sacrifice accuracy when prevalence differs;\nthe prior keeps fairness while preserving accuracy', 25, 't3'))
    return svg(''.join(b))


def amyloid_subtypes():
    b = [title('Data-driven MCI subtypes from amyloid PET')]
    b.append(box(56, 180, 280, 300, '', 'blue'))
    b.append(text(196, 222, 'amyloid PET', 28, 'ink', 700))
    import math
    for i in range(68):
        a = i * 2.399
        r = 95 * math.sqrt((i + 0.5) / 68)
        b.append(f'<circle cx="{196 + r * math.cos(a) * 1.15:.1f}" cy="{345 + r * math.sin(a) * 0.8:.1f}" r="6" fill="{C["blue"]}" fill-opacity="{0.35 + (i % 5) * 0.13:.2f}"/>')
    b.append(text(196, 455, '68 cortical features', 22, 't3'))
    b.append(text(196, 525, 'MCI patients\n(EMCI and LMCI)', 22, 't3'))
    b.append(arrow([(346, 330), (396, 330)]))
    b.append(box(406, 210, 300, 240, '', 'violet', fill='#FFFFFF'))
    b.append(text(556, 250, 'clustering', 28, 'violet', 700))
    for i, s in enumerate(['k-means', 'spectral', 'agglomerative']):
        b.append(pill(556, 305 + i * 50, s, 'violet', 22))
    b.append(arrow([(716, 330), (766, 330)]))
    b.append(f'<circle cx="840" cy="265" r="62" fill="{C["tealT"]}" stroke="{C["teal"]}" stroke-width="3"/>')
    b.append(text(840, 265, 'subtype\n1', 24, 'teal', 700))
    b.append(f'<circle cx="840" cy="410" r="62" fill="{C["amberT"]}" stroke="{C["amber"]}" stroke-width="3"/>')
    b.append(text(840, 410, 'subtype\n2', 24, 'amber', 700))
    b.append(arrow([(912, 330), (962, 330)]))
    b.append(box(972, 170, 258, 330, '', 'grey', fill=C['grey']))
    b.append(text(1101, 210, 'evaluation', 26, 'ink', 700))
    for i, s in enumerate(['2D cluster maps', 'Kaplan–Meier', 'genetic association', 'biomarkers']):
        b.append(pill(1101, 270 + i * 58, s, 'blue', 21))
    b.append(text(640, 640, 'each subtype has a homogeneous cortical amyloid pattern; the subtypes\nscore better than the clinical EMCI and LMCI grouping on every metric', 25, 't3'))
    return svg(''.join(b))


def mg_tcca(variant):
    b = [title('MG-TCCA: multi-group tensor CCA')]

    def cube(x, y, s, col, lab):
        d = s * 0.35
        f = C[col + 'T']
        st = C[col]
        return (f'<path d="M{x},{y + d} h{s} v{s} h{-s} z" fill="{f}" stroke="{st}" stroke-width="3"/>'
                f'<path d="M{x},{y + d} l{d},{-d} h{s} l{-d},{d} z" fill="{f}" stroke="{st}" stroke-width="3"/>'
                f'<path d="M{x + s},{y + d} l{d},{-d} v{s} l{-d},{d} z" fill="{f}" stroke="{st}" stroke-width="3"/>'
                + text(x + s / 2 + d / 2, y + s + d + 32, lab, 22, 't3'))
    b.append(text(250, 150, 'two PET modalities, several groups', 24, 't3'))
    b.append(cube(70, 185, 120, 'blue', 'AV-45, group 1'))
    b.append(cube(250, 185, 120, 'blue', 'AV-45, group 2'))
    b.append(cube(70, 400, 120, 'violet', 'FDG, group 1'))
    b.append(cube(250, 400, 120, 'violet', 'FDG, group 2'))
    b.append(arrow([(430, 380), (480, 380)]))
    b.append(box(490, 250, 330, 260, '', 'blue', fill='#FFFFFF'))
    b.append(text(655, 300, 'Joint analysis', 28, 'ink', 700))
    b.append(text(655, 395, 'dual sparsity:\nshared + individual\nstructure;\nblock coordinate ascent', 24, 'ink'))
    b.append(arrow([(830, 380), (880, 380)]))
    b.append(box(890, 200, 340, 130, '', 'teal'))
    b.append(text(1060, 240, 'shared weights', 26, 'teal', 700))
    b.append(text(1060, 288, 'consistent across groups', 22, 'ink'))
    b.append(box(890, 360, 340, 160, '', 'amber'))
    b.append(text(1060, 400, 'group-specific weights', 26, 'amber', 700))
    b.append(text(1060, 458, 'e.g., sex-specific cross-\nmodality correlations', 22, 'ink'))
    note = ('finds sex-specific correlations between AV-45 and FDG PET in an Alzheimer’s cohort\nthat TCCA misses'
            if variant == 'bcb' else
            'finds sex-specific correlations between AV-45 and FDG PET in an Alzheimer’s cohort\nthat TCCA and sparse TCCA miss')
    b.append(text(640, 720, note, 25, 't3'))
    return svg(''.join(b))


def ovfm():
    b = [title('OVFM: online learning in variable feature spaces')]
    b.append(box(56, 160, 330, 340, '', 'grey', fill=C['grey']))
    b.append(text(221, 200, 'mixed-type data stream', 24, 'ink', 700))
    cols = [('blue', 'Boolean'), ('violet', 'ordinal'), ('teal', 'continuous')]
    for r in range(5):
        for c in range(5):
            alive = not ((r >= 3 and c == 0) or (r <= 1 and c == 4))
            col = cols[c % 3][0]
            op = '1' if alive else '0.12'
            b.append(f'<rect x="{96 + c * 52}" y="{235 + r * 40}" width="44" height="32" rx="6" fill="{C[col]}" fill-opacity="{op}"/>')
    b.append(text(221, 455, 'old features vanish,\nnew ones appear', 22, 't3'))
    b.append(text(221, 535, 'Boolean, ordinal, continuous', 21, 't3'))
    b.append(arrow([(396, 330), (446, 330)]))
    b.append(box(456, 190, 300, 130, 'Gaussian copula:\nmap to a latent\nnormal space', 'violet', 24))
    b.append(box(456, 350, 300, 110, 'online EM:\nfeature correlations', 'blue', 24))
    b.append(text(606, 520, 'reconstructs missed old features\nand warm-starts new ones', 22, 't3'))
    b.append(arrow([(766, 255), (816, 280)]))
    b.append(arrow([(766, 405), (816, 380)]))
    b.append(box(826, 200, 230, 110, 'learner on\nobserved features', 'teal', 22))
    b.append(box(826, 350, 230, 110, 'learner on\nlatent features', 'teal', 22))
    b.append(arrow([(1066, 255), (1110, 300)]))
    b.append(arrow([(1066, 405), (1110, 360)]))
    b.append(box(1120, 260, 110, 140, 'en-\nsemble', 'amber', 23))
    b.append(text(640, 660, 'models the joint distribution of mixed data without assuming a linear map\nor a Gaussian joint; the ensemble speeds up online convergence', 24, 't3'))
    return svg(''.join(b))


def rnn_fsa():
    b = [title('Interpretability of RNNs under feature changes')]
    for i, s in enumerate(['x₁', 'x₂', '…', 'xₙ']):
        b.append(pill(120, 210 + i * 75, s, 'grey' if s == '…' else 'blue', 26) if s != '…' else text(120, 210 + i * 75, '…', 30, 't3'))
    b.append(arrow([(180, 320), (230, 320)]))
    b.append(box(240, 200, 250, 240, '', 'violet', fill='#FFFFFF'))
    b.append(text(365, 240, 'RNN', 30, 'violet', 700))
    for i, s in enumerate(['SRN', 'MGU', 'GRU', 'LSTM']):
        b.append(pill(365, 290 + i * 40, s, 'violet', 20))
    b.append(text(365, 470, 'different numbers of gates', 21, 't3'))
    b.append(arrow([(500, 320), (550, 320)]))
    b.append(box(560, 200, 250, 240, '', 'blue', fill='#FFFFFF'))
    b.append(text(685, 240, 'hidden states', 28, 'blue', 700))
    for (cx, cy, col) in [(625, 320, 'blue'), (735, 300, 'teal'), (690, 390, 'amber')]:
        b.append(dots(cx, cy, 7, col, 7, 22))
    b.append(text(685, 470, 'cluster into states', 21, 't3'))
    b.append(arrow([(820, 320), (870, 320)]))
    b.append(box(880, 200, 350, 240, '', 'teal', fill='#FFFFFF'))
    b.append(text(1055, 240, 'finite state automaton', 26, 'teal', 700))
    for (cx, cy, s) in [(950, 330, 'S0'), (1055, 300, 'S1'), (1160, 360, 'S2')]:
        b.append(f'<circle cx="{cx}" cy="{cy}" r="34" fill="{C["tealT"]}" stroke="{C["teal"]}" stroke-width="3"/>')
        b.append(text(cx, cy, s, 22, 'teal', 700))
    b.append(arrow([(984, 322), (1018, 308)], 'teal', 3))
    b.append(arrow([(1089, 312), (1124, 344)], 'teal', 3))
    b.append(text(1055, 410, 'humans can simulate it', 21, 't3'))
    b.append(box(110, 560, 1060, 140, '', 'amber'))
    b.append(text(640, 630, 'in open environments features change: we study how feature changes and the number\nof gates affect RNN performance and the FSA learned from it', 25, 'ink'))
    return svg(''.join(b))


DIAGRAMS = {
    'sem-ece-neurips26': sem_ece,
    'bilevel-calibration-colm26': bilevel_calibration,
    'calibration-aligned-llm-icml25': calibration_aligned,
    'online-bilevel-aistats24': online_bilevel_aistats,
    'online-bilevel-regret-neurips25': online_bilevel_regret,
    'sfl-ijcai17': sfl,
    'association-mining-psb25': association_mining,
    'clinical-modalities-amia25': clinical_modalities,
    'pferm-amia24': pferm,
    'amyloid-subtypes-amia24': amyloid_subtypes,
    'mg-tcca-bcb23': lambda: mg_tcca('bcb'),
    'mg-tcca-tcbb24': lambda: mg_tcca('tcbb'),
    'ovfm-icdm21': ovfm,
    'rnn-interpretability-ccfai19': rnn_fsa,
}

def to_webp(png_dir):
    from PIL import Image
    dest = os.path.join(HERE, '..', '..', 'images', 'pubs')
    for pid in DIAGRAMS:
        im = Image.open(os.path.join(png_dir, pid + '.png')).convert('RGB').resize((640, 400), Image.LANCZOS)
        im.save(os.path.join(dest, pid + '.webp'), 'WEBP', quality=90, method=6)
    print(len(DIAGRAMS), 'thumbnails written to images/pubs')


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == 'webp':
        to_webp(sys.argv[2])
        sys.exit()
    os.makedirs(OUT, exist_ok=True)
    for pid, fn in DIAGRAMS.items():
        with open(os.path.join(OUT, pid + '.svg'), 'w', encoding='utf-8') as f:
            f.write(fn())
    print(len(DIAGRAMS), 'diagrams written to', OUT)
