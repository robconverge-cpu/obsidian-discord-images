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
stars = [(random.randint(80, 2090), random.randint(30, 300), random.random()) for _ in range(14)]
stars = [s for s in stars if not (560 < s[0] < 1520 and 240 < s[1] < 470)]

N, OUT_W, OUT_H = 36, 1200, 400
frames = []
for i in range(N):
    t = i / N
    f = sub.copy()
    pulse = 0.5 - 0.5 * math.cos(2 * math.pi * t)
    f += ring_glow[:, :, None] * np.array([70, 110, 255]) * (0.25 + 0.75 * pulse)
    f += tower_glow[:, :, None] * np.array([120, 70, 255]) * (0.15 + 0.35 * pulse)
    # a diagonal shine passes over OBSIDIAN in the first 60% of the loop
    p = t / 0.6
    if p <= 1:
        cx = 520 + p * 1150
        band = np.exp(-((xx + (yy - 316) * 0.35 - cx) / 55) ** 2)
        f += (title * band)[:, :, None] * np.array([90, 80, 120])
    for sx, sy, ph in stars:
        a = max(0.0, math.sin(2 * math.pi * (t + ph))) ** 3
        if a < 0.02: continue
        r = 9
        d = np.exp(-(((xx[sy - r:sy + r + 1, sx - r:sx + r + 1] - sx) ** 2 + (yy[sy - r:sy + r + 1, sx - r:sx + r + 1] - sy) ** 2) / 6))
        f[sy - r:sy + r + 1, sx - r:sx + r + 1] += (d * a)[:, :, None] * np.array([200, 190, 255])
    img = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).resize((OUT_W, OUT_H), Image.LANCZOS)
    frames.append(img)

frames[0].save(OUT.replace('.gif', '-still.png'))
pal = [fr.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG) for fr in frames]
pal[0].save(OUT, save_all=True, append_images=pal[1:], duration=70, loop=0, optimize=True, disposal=1)
print('frames', N, 'size', OUT_W, OUT_H)
