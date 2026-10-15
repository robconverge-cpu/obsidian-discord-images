# Animated Obsidian banners from the approved downloads banner (OBSIDIAN title, crystal O, tower, water).
#   python make_banner_gif.py <out.gif> [SUBTITLE] [--font]
# No subtitle keeps "CLIENT DOWNLOADS". A subtitle is rebuilt from the banner's own letters when they cover it,
# otherwise (--font, or missing letters) it is set in Lexend Zetta 500 (OFL, fonts/) to match.
import math, os, random, sys
import numpy as np
from PIL import Image, ImageFilter, ImageFont, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r'C:\dev\obsidian-discord-images\images\obsidian-downloads.png'
OUT = sys.argv[1]
SUB = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
base = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float32)
H, W, _ = base.shape


def blur(a, r):
    return np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32)


# ── Subtitle ─────────────────────────────────────────────────────────────────────────────────
y0, y1, x0, x1 = 392, 458, 596, 1500
lum = base.mean(axis=2)
text = np.zeros((H, W), bool)
text[y0:y1, x0:x1] = lum[y0:y1, x0:x1] > 45
hole = np.asarray(Image.fromarray((text * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(15))) > 0
keep = (~hole).astype(np.float32)
fill = np.zeros_like(base)
for c in range(3):
    fill[:, :, c] = blur(base[:, :, c] * keep, 18) / np.maximum(blur(keep * 255, 18) / 255, 1e-3)
clean = np.where(hole[:, :, None], fill, base)
TEXT = np.array([169, 150, 241], np.float32)
gy0, gy1, CAP, GAP, SPACE, CENTRE = 402, 448, 36, 23, 52, 1047
SPANS = {'C': (608, 647), 'L': (667, 699), 'I': (718, 727), 'E': (750, 784), 'N': (804, 843), 'T': (864, 901),
         'D': (952, 993), 'O': (1012, 1056), 'W': (1073, 1135), 'A': (1325, 1368), 'S': (1446, 1488)}


def own_glyph(ch):
    a, b = SPANS[ch]
    crop, bg = base[gy0:gy1, a:b + 1], clean[gy0:gy1, a:b + 1]
    return np.clip((crop.mean(axis=2) - bg.mean(axis=2)) / (TEXT.mean() - bg.mean(axis=2) + 1e-3), 0, 1)


def zetta(size):
    f = ImageFont.truetype(os.path.join(HERE, 'fonts', 'LexendZetta.ttf'), size)
    f.set_variation_by_axes([500])
    return f


def font_glyph(ch):
    probe = zetta(100)
    cap = probe.getbbox('H')[3] - probe.getbbox('H')[1]
    f = zetta(round(100 * CAP / cap))              # a capital is CAP pixels tall, like the banner's letters
    l, _, r, _ = f.getbbox(ch)
    ht = f.getbbox('H')[1]
    img = Image.new('L', (r - l + 4, gy1 - gy0))
    ImageDraw.Draw(img).text((2 - l, (gy1 - gy0 - CAP) // 2 - ht), ch, font=f, fill=255)
    g = np.asarray(img, np.float32) / 255
    return np.maximum(g, np.asarray(img.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255 * 0.35)  # soft glow


sub = base.copy()
if SUB:
    use_font = '--font' in sys.argv or any(ch not in SPANS for ch in SUB if ch != ' ')
    pairs = sum(1 for i in range(len(SUB) - 1) if SUB[i] != ' ' and SUB[i + 1] != ' ')
    MAXW = 900                                      # no wider than OBSIDIAN, clear of the O and the tower
    while True:
        glyphs = [None if ch == ' ' else (font_glyph(ch) if use_font else own_glyph(ch)) for ch in SUB]
        letters = sum(SPACE if g is None else g.shape[1] for g in glyphs)
        GAP = min(GAP, max(15, (MAXW - letters) // max(pairs, 1)))    # tighten the tracking first
        SPACE = min(SPACE, int(GAP * 2.6))                            # words stay clearly apart
        width = sum(SPACE if g is None else g.shape[1] for g in glyphs) + GAP * pairs
        if width <= MAXW or not use_font or CAP <= 22:
            break
        CAP -= 2                                                       # then shrink the letters
    assert width <= MAXW or not use_font, f'subtitle too wide: {width}px'
    sub = clean.copy()
    x = int(CENTRE - width / 2)
    for i, g in enumerate(glyphs):
        if g is None:
            x += SPACE
            continue
        w = g.shape[1]
        sub[gy0:gy1, x:x + w] = sub[gy0:gy1, x:x + w] * (1 - g[:, :, None]) + TEXT * g[:, :, None]
        x += w + (GAP if i + 1 < len(SUB) and SUB[i + 1] != ' ' else 0)

# ── Animated layers ──────────────────────────────────────────────────────────────────────────
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
tl = sub.mean(axis=2)
title = np.zeros((H, W), np.float32)
title[262:370, 600:1496] = np.clip((tl[262:370, 600:1496] - 150) / 90, 0, 1)
subt = np.zeros((H, W), np.float32)
subt[gy0:gy1, 590:1510] = np.clip((tl - clean.mean(axis=2))[gy0:gy1, 590:1510] / 60, 0, 1)
lb = sub[160:560, 170:560]
ring = np.zeros((H, W), np.float32)
ring[160:560, 170:560] = np.clip((lb[:, :, 2] - lb[:, :, 0] - 40) / 120, 0, 1)
ring_glow = blur(ring * 255, 16) / 255
tb = sub[40:620, 1540:1990]
tower = np.zeros((H, W), np.float32)
tower[40:620, 1540:1990] = np.clip((tb.mean(axis=2) - 100) / 110, 0, 1)
tower_glow = blur(tower * 255, 24) / 255
sky = np.clip((sub[:, :, 2] - sub[:, :, 1] - 30) / 90, 0, 1) * (yy < 560)        # violet nebula and arcs
water = np.zeros((H, W), np.float32)
water[600:H] = np.clip((sub[600:H].mean(axis=2) - 40) / 120, 0, 1)
title_glow = blur(title * 255, 12) / 255
subt_glow = blur(subt * 255, 8) / 255

CX, CY, RA, RB = 360.0, 357.0, 62.0, 108.0                    # the O's inner ring as a tilted ellipse
n = math.hypot(0.30, 0.95)
ux, uy = 0.30 / n, -0.95 / n
vx, vy = -uy, ux


def spot(f, px, py, sigma, colour, amount):
    r = int(sigma * 3) + 1
    a0, a1, b0, b1 = max(int(px) - r, 0), min(int(px) + r + 1, W), max(int(py) - r, 0), min(int(py) + r + 1, H)
    if a1 <= a0 or b1 <= b0:
        return
    d = np.exp(-(((xx[b0:b1, a0:a1] - px) ** 2 + (yy[b0:b1, a0:a1] - py) ** 2) / (2 * sigma ** 2)))
    f[b0:b1, a0:a1] += (d * amount)[:, :, None] * np.array(colour)


random.seed(11)
N, OUT_W, OUT_H, MS = 40, 1080, 360, 60
# Each spark rises a whole number of screen heights per loop, so the loop is seamless.
sparks = [dict(x=random.uniform(30, 2140), y=random.uniform(0, H), laps=random.choice([1, 2, 2, 3]),
               drift=random.uniform(-40, 40), r=random.uniform(2.5, 6.0), a=random.uniform(0.6, 1.3),
               c=random.choice([(190, 165, 255), (150, 190, 255), (235, 220, 255)])) for _ in range(120)]

frames = []
for i in range(N):
    t = i / N
    f = sub.copy()
    beat = 0.5 - 0.5 * math.cos(2 * math.pi * t)
    f += sky[:, :, None] * np.array([40, 10, 90]) * (0.6 * beat - 0.2)
    f += ring_glow[:, :, None] * np.array([110, 160, 255]) * (0.3 + 1.8 * beat)
    f += tower_glow[:, :, None] * np.array([170, 100, 255]) * (0.2 + 1.4 * (0.5 - 0.5 * math.cos(2 * math.pi * (t + 0.5))))
    for k in range(18):                                        # energy round the ring, two laps per loop
        th = 2 * math.pi * 2 * t - k * 0.08
        px = CX + RB * math.cos(th) * ux + RA * math.sin(th) * vx
        py = CY + RB * math.cos(th) * uy + RA * math.sin(th) * vy
        spot(f, px, py, 11 - k * 0.45, (210, 235, 255), 2.2 * (1 - k / 18))
    for t0, t1, glow, mask, mid, k in ((0.0, 0.45, title_glow, title, 316, 1.0), (0.25, 0.7, subt_glow, subt, 425, 0.9)):
        p = (t - t0) / (t1 - t0)
        if 0 <= p <= 1:                                        # violet shine: the letters are already white
            band = np.exp(-((xx + (yy - mid) * 0.35 - (480 + p * 1250)) / 50) ** 2)
            f += (glow * band)[:, :, None] * np.array([180, 120, 255]) * 2.6 * k
            f += (mask * band)[:, :, None] * np.array([130, 130, 70]) * k
    ripple = 0.5 + 0.5 * np.sin(xx[600:H] / 21 + yy[600:H] / 4 - 2 * math.pi * 2 * t)
    f[600:H] += (water[600:H] * ripple)[:, :, None] * np.array([80, 50, 160])
    for s in sparks:
        y = (s['y'] - t * s['laps'] * H) % H
        x = s['x'] + s['drift'] * math.sin(2 * math.pi * (t + s['y'] / H))
        fade = min(1.0, y / 100) * min(1.0, (H - y) / 100)
        spot(f, x, y, s['r'], s['c'], s['a'] * fade)
    frames.append(Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).resize((OUT_W, OUT_H), Image.LANCZOS))

frames[0].save(OUT.replace('.gif', '-still.png'))
pal = [fr.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG) for fr in frames]
pal[0].save(OUT, save_all=True, append_images=pal[1:], duration=MS, loop=0, optimize=True, disposal=1)
print(OUT, 'frames', N, os.path.getsize(OUT) // 1024, 'KB')
