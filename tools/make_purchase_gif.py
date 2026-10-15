# Animated "OBSIDIAN / CLIENT ACCESS" header from the approved downloads banner.
# Subtitle letters are reused from the banner's own lettering, so the type matches exactly.
import math, random, sys
import numpy as np
from PIL import Image, ImageFilter

SRC = r'C:\dev\obsidian-discord-images\images\obsidian-downloads.png'
OUT = sys.argv[1]
base = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float32)
H, W, _ = base.shape

# 1. Lift the old subtitle out: text mask (dilated) refilled from a masked blur of the surrounding sky.
y0, y1, x0, x1 = 392, 458, 596, 1500
lum = base.mean(axis=2)
text = np.zeros((H, W), bool); text[y0:y1, x0:x1] = lum[y0:y1, x0:x1] > 45
m = Image.fromarray((text * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(15))
hole = np.asarray(m) > 0
keep = (~hole).astype(np.float32)
def blur(a, r): return np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32)
fill = np.zeros_like(base)
for c in range(3):
    num = blur(base[:, :, c] * keep, 18); den = blur(keep * 255, 18) / 255
    fill[:, :, c] = num / np.maximum(den, 1e-3)
clean = np.where(hole[:, :, None], fill, base)

# 2. Glyphs from the original subtitle (x spans measured from the banner), alpha from brightness over the sky.
spans = {'C': (608, 647), 'L': (667, 699), 'I': (718, 727), 'E': (750, 784), 'N': (804, 843), 'T': (864, 901),
         'A': (1325, 1368), 'S': (1446, 1488)}
gy0, gy1 = 402, 448
TEXT = np.array([169, 150, 241], np.float32)
def glyph(ch):
    a, b = spans[ch]
    crop = base[gy0:gy1, a:b + 1]; bg = clean[gy0:gy1, a:b + 1]
    alpha = np.clip((crop.mean(axis=2) - bg.mean(axis=2)) / (TEXT.mean() - bg.mean(axis=2) + 1e-3), 0, 1)
    return alpha
word = 'CLIENT ACCESS'
gap, space = 23, 52
glyphs = [None if ch == ' ' else glyph(ch) for ch in word]
width = sum(space if g is None else g.shape[1] for g in glyphs) + gap * (len(word) - 1 - 2 * word.count(' '))
x = int(1047 - width / 2)
sub = clean.copy()
for g in glyphs:
    if g is None: x += space - gap; continue
    h, w = g.shape
    region = sub[gy0:gy1, x:x + w]
    sub[gy0:gy1, x:x + w] = region * (1 - g[:, :, None]) + TEXT * g[:, :, None]
    x += w + gap

# 3. Animation layers.
title = np.zeros((H, W), np.float32); tl = sub.mean(axis=2)
title[262:370, 600:1496] = np.clip((tl[262:370, 600:1496] - 150) / 90, 0, 1)          # OBSIDIAN letters
ring = np.zeros((H, W), np.float32)
lb = sub[160:560, 170:560]
ring[160:560, 170:560] = np.clip((lb[:, :, 2] - lb[:, :, 0] - 40) / 120, 0, 1)        # the O's blue core
ring_glow = blur((ring * 255).astype(np.uint8), 14) / 255
tower = np.zeros((H, W), np.float32)
tb = sub[40:560, 1560:1960]
tower[40:560, 1560:1960] = np.clip((tb.mean(axis=2) - 110) / 120, 0, 1)
tower_glow = blur((tower * 255).astype(np.uint8), 20) / 255
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

random.seed(7)
N, OUT_W, OUT_H = 44, 1080, 360
# Rising sparks: each travels a whole number of screen-heights per loop, so the loop is seamless.
sparks = [dict(x=random.uniform(40, 2130), y=random.uniform(0, H), laps=random.choice([1, 1, 2]),
               drift=random.uniform(-25, 25), r=random.uniform(2.2, 4.5), a=random.uniform(0.45, 1.0),
               c=random.choice([(190, 170, 255), (150, 190, 255), (230, 215, 255)])) for _ in range(75)]
# The O's inner ring as a tilted ellipse (measured from the bright-blue mask).
CX, CY, RA, RB = 360.0, 357.0, 62.0, 108.0
ux, uy = 0.30, -0.95; n = math.hypot(ux, uy); ux, uy = ux / n, uy / n      # major axis direction
vx, vy = -uy, ux
def spot(f, px, py, sigma, colour, amount):
    r = int(sigma * 3)
    x0, x1, y0_, y1_ = int(px) - r, int(px) + r + 1, int(py) - r, int(py) + r + 1
    if x1 <= 0 or y1_ <= 0 or x0 >= W or y0_ >= H: return
    x0c, y0c, x1c, y1c = max(x0, 0), max(y0_, 0), min(x1, W), min(y1_, H)
    d = np.exp(-(((xx[y0c:y1c, x0c:x1c] - px) ** 2 + (yy[y0c:y1c, x0c:x1c] - py) ** 2) / (2 * sigma ** 2)))
    f[y0c:y1c, x0c:x1c] += (d * amount)[:, :, None] * np.array(colour)
water = np.zeros((H, W), np.float32); wb = sub[600:H].mean(axis=2)
water[600:H] = np.clip((wb - 40) / 120, 0, 1)

frames = []
for i in range(N):
    t = i / N
    f = sub.copy()
    pulse = 0.5 - 0.5 * math.cos(2 * math.pi * t)
    f += ring_glow[:, :, None] * np.array([90, 140, 255]) * (0.2 + 1.3 * pulse)
    f += tower_glow[:, :, None] * np.array([150, 90, 255]) * (0.15 + 0.9 * (0.5 - 0.5 * math.cos(2 * math.pi * (t + 0.5))))
    # energy running round the O's ring, with a fading tail
    for k in range(14):
        th = 2 * math.pi * (t * 2) - k * 0.09
        px = CX + RB * math.cos(th) * ux + RA * math.sin(th) * vx
        py = CY + RB * math.cos(th) * uy + RA * math.sin(th) * vy
        spot(f, px, py, 9 - k * 0.4, (200, 230, 255), 1.6 * (1 - k / 14))
    # bright shine over OBSIDIAN, then over the subtitle
    for t0, t1, top, bottom, strength in ((0.05, 0.5, 262, 370, 1.0), (0.3, 0.75, 400, 452, 0.8)):
        p = (t - t0) / (t1 - t0)
        if 0 <= p <= 1:
            cx = 520 + p * 1150
            band = np.exp(-((xx + (yy - (top + bottom) / 2) * 0.35 - cx) / 45) ** 2)
            mask = title if top < 380 else np.clip((sub.mean(axis=2) - clean.mean(axis=2)) / 60, 0, 1) * ((yy >= top) & (yy < bottom))
            # the letters are already white, so the shine is a violet bloom around them plus a lift on the glyphs
            f += (blur(mask * 255, 10) / 255 * band)[:, :, None] * np.array([170, 120, 255]) * 2.2 * strength
            f += (mask * band)[:, :, None] * np.array([120, 120, 60]) * strength
    # water shimmer
    ripple = 0.5 + 0.5 * np.sin(xx[600:H] / 23 + yy[600:H] / 5 - 2 * math.pi * t * 2)
    f[600:H] += (water[600:H] * ripple)[:, :, None] * np.array([60, 40, 120])
    # rising sparks
    for s in sparks:
        y = (s['y'] - t * s['laps'] * H) % H
        x = s['x'] + s['drift'] * math.sin(2 * math.pi * (t + s['y'] / H))
        fade = min(1.0, y / 120) * min(1.0, (H - y) / 120)
        spot(f, x, y, s['r'], s['c'], s['a'] * fade)
    img = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).resize((OUT_W, OUT_H), Image.LANCZOS)
    frames.append(img)

frames[0].save(OUT.replace('.gif', '-still.png'))
pal = [fr.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG) for fr in frames]
pal[0].save(OUT, save_all=True, append_images=pal[1:], duration=60, loop=0, optimize=True, disposal=1)
print('frames', N, 'size', OUT_W, OUT_H)
