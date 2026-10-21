"""
c64art.py - tekenhulpmiddelen voor C64 multicolor-kunst (fat pixels, 160 breed).

Alle geometrie werkt in 'schermcoördinaten' (320 x H), zodat cirkels rond
blijven; de canvas zelf bewaart C64-kleurindices op 160 x H fat pixels.
Dithering gebruikt een 4x4 Bayer-matrix op fat pixels (de klassieke C64-look).
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], float) / 16 + 1 / 32

# Kleurnamen (C64-nummers)
BLK, WHT, RED, CYN, PUR, GRN, BLU, YEL, ORA, BRN, LRD, DGR, GRY, LGN, LBL, LGR = range(16)

# Kleurladders donker -> licht
SAND = [BRN, ORA, LRD, YEL]
SAND_WARM = [BLK, BRN, ORA, YEL]
SUNSET = [BLK, BLU, PUR, RED, LRD, ORA, YEL]
DAYSKY = [BLU, LBL, LGR, WHT]
NIGHT = [BLK, BLU, LBL]
ROCK = [BLK, BRN, RED, LRD]
STONE = [BLK, DGR, GRY, LGR, WHT]
WARMSTONE = [BLK, BRN, ORA, LGR]
GREEN = [BLK, GRN, LGN]
FIRE = [RED, ORA, YEL, WHT]


def _rng(seed):
    return np.random.default_rng(seed)


def value_noise(h, w, cell, seed, xscale=2.0):
    """Gladde ruis 0..1 op een (h,w) fat-pixel raster; cell in schermpixels."""
    r = _rng(seed)
    gw = int(w * xscale / cell) + 3
    gh = int(h / cell) + 3
    g = r.random((gh, gw))
    yy, xx = np.mgrid[0:h, 0:w]
    fx = xx * xscale / cell
    fy = yy / cell
    x0 = fx.astype(int); y0 = fy.astype(int)
    tx = fx - x0; ty = fy - y0
    tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty)
    a = g[y0, x0]; b = g[y0, x0 + 1]; c = g[y0 + 1, x0]; d = g[y0 + 1, x0 + 1]
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def fbm(h, w, cell, seed, octaves=4, gain=0.5):
    tot = np.zeros((h, w)); amp = 1.0; norm = 0
    for o in range(octaves):
        tot += amp * value_noise(h, w, max(cell / (2 ** o), 1.5), seed + o * 17)
        norm += amp; amp *= gain
    return tot / norm


class Canvas:
    def __init__(self, h=136, fill=BLK):
        self.h, self.w = h, 160
        self.px = np.full((h, 160), fill, np.uint8)
        yy, xx = np.mgrid[0:h, 0:160]
        self.X = xx * 2 + 1.0          # schermcoördinaat x (0..320)
        self.Y = yy + 0.5              # schermcoördinaat y
        self.bx = BAYER[yy % 4, xx % 4]

    # ---------- maskers ----------
    def _draw_mask(self, fn):
        im = Image.new("L", (320, self.h), 0)
        fn(ImageDraw.Draw(im))
        return np.array(im)[:, 1::2] > 127

    def poly(self, pts):
        return self._draw_mask(lambda d: d.polygon([tuple(p) for p in pts], fill=255))

    def rect(self, x0, y0, x1, y1):
        return (self.X >= x0) & (self.X < x1) & (self.Y >= y0) & (self.Y < y1)

    def ellipse(self, cx, cy, rx, ry):
        return ((self.X - cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2 <= 1.0

    def line(self, pts, width=2):
        return self._draw_mask(lambda d: d.line([tuple(p) for p in pts], fill=255, width=width))

    def text_mask(self, text, font_path, size, x, y, spacing=0, anchor="la"):
        im = Image.new("L", (320, self.h), 0)
        d = ImageDraw.Draw(im)
        f = ImageFont.truetype(font_path, size)
        if spacing == 0:
            d.text((x, y), text, font=f, fill=255, anchor=anchor)
        else:
            # handmatige letterspatiëring, gecentreerd rond x als anchor 'm'
            widths = [d.textlength(ch, font=f) for ch in text]
            total = sum(widths) + spacing * (len(text) - 1)
            cx = x - total / 2 if anchor[0] == "m" else x
            for ch, wdt in zip(text, widths):
                d.text((cx, y), ch, font=f, fill=255, anchor="l" + anchor[1])
                cx += wdt + spacing
        return np.array(im)[:, 1::2] > 110

    # ---------- verven ----------
    def fill(self, mask, color):
        self.px[mask] = color

    def ramp(self, mask, value, ramp):
        """value: scalar of array 0..1 -> kleur uit ramp met Bayer-dithering."""
        v = np.clip(np.broadcast_to(value, self.px.shape), 0, 0.9999) * (len(ramp) - 1)
        i = np.floor(v).astype(int)
        f = v - i
        i = np.clip(i + (f > self.bx), 0, len(ramp) - 1)
        out = np.array(ramp, np.uint8)[i]
        self.px[mask] = out[mask]

    def vgrad(self, mask, y0, y1, ramp, curve=1.0):
        t = np.clip((self.Y - y0) / max(y1 - y0, 1e-6), 0, 1) ** curve
        self.ramp(mask, t, ramp)

    def stars(self, mask, n, seed, colors=(WHT, LGR, GRY, LBL)):
        r = _rng(seed)
        ys = r.integers(0, self.h, n); xs = r.integers(0, 160, n)
        for y, x, c in zip(ys, xs, r.choice(colors, n)):
            if mask[y, x]:
                self.px[y, x] = c

    def all(self):
        return np.ones(self.px.shape, bool)

    def save_png(self, path):
        from c64gfx import palette_image
        palette_image(self.px).save(path)

    def outline(self, mask, color=BLK, thick=1):
        """Teken rand rond masker (buitenkant)."""
        m = mask.copy()
        grown = m.copy()
        for _ in range(thick):
            g = grown.copy()
            g[1:, :] |= grown[:-1, :]; g[:-1, :] |= grown[1:, :]
            g[:, 1:] |= grown[:, :-1]; g[:, :-1] |= grown[:, 1:]
            grown = g
        self.px[grown & ~m] = color
        return grown


def dunes(cv, y_base, amp, seed, wavelength=120, light_from=-1, ramp=SAND, mask=None,
          shade_bias=0.55, detail=0.35, top_ramp=None):
    """Teken een duinrug-laag: hoogteprofiel + schaduw naar lichtrichting."""
    r = _rng(seed)
    xs = np.arange(160) * 2 + 1.0
    prof = np.zeros(160)
    for k, wl in enumerate([wavelength, wavelength / 2.3, wavelength / 5.1]):
        ph = r.random() * 6.28
        prof += (amp / (k + 1) ** 1.3) * np.sin(xs / wl * 6.28 + ph)
    # scherpe kammen (sinus -> abs geeft rug)
    ridge = y_base - prof
    slope = np.gradient(ridge)
    m = cv.Y >= ridge[None, :]
    if mask is not None:
        m &= mask
    depth = np.clip((cv.Y - ridge[None, :]) / (amp * 2.5 + 8), 0, 1)
    lit = np.clip(shade_bias - light_from * slope[None, :] * 0.9, 0, 1)
    val = lit * (1 - 0.45 * depth) + 0.12 * depth
    noise = value_noise(cv.h, 160, 9, seed + 3)
    val = np.clip(val + (noise - 0.5) * detail * 0.4, 0, 1)
    cv.ramp(m, val, ramp)
    return ridge


def _hash2(ix, iz, seed):
    v = np.sin(ix * 127.1 + iz * 311.7 + seed * 74.7) * 43758.5453
    return v - np.floor(v)


def noise2(x, z, seed=0):
    """Value noise op willekeurige (wereld)coördinaten, 0..1."""
    ix = np.floor(x); iz = np.floor(z)
    fx = x - ix; fz = z - iz
    fx = fx * fx * (3 - 2 * fx); fz = fz * fz * (3 - 2 * fz)
    a = _hash2(ix, iz, seed); b = _hash2(ix + 1, iz, seed)
    c = _hash2(ix, iz + 1, seed); d = _hash2(ix + 1, iz + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fz) + (c * (1 - fx) + d * fx) * fz


def fbm2(x, z, seed=0, octaves=4):
    tot = 0; amp = 1; norm = 0; f = 1
    for o in range(octaves):
        tot = tot + amp * noise2(x * f, z * f, seed + o * 13)
        norm += amp; amp *= 0.5; f *= 2.03
    return tot / norm


def dune_field(wl=34.0, amp=7.0, seed=1, angle=0.35, warp=1.4, base=0.0, roll=6.0):
    """Asymmetrische duinen (zachte loefzijde, steil lijzijde) met kromming via warping."""
    ca, sa = np.cos(angle), np.sin(angle)
    def H(x, z):
        w = fbm2(x / 55.0, z / 55.0, seed, 3)
        u = (x * ca + z * sa) / wl + warp * w
        f = u - np.floor(u)
        prof = np.where(f < 0.8, (f / 0.8) ** 1.7, (1 - f) / 0.2)
        local = 0.55 + 0.45 * noise2(np.floor(u) * 3.1, z / 40.0, seed + 5)
        return base + amp * prof * local + roll * (fbm2(x / 120.0, z / 120.0, seed + 9, 2) - 0.5)
    return H


def voxel_terrain(cv, H, horizon, cam_h, near_ramp, far_ramp=None, mask=None, cam_x=0.0,
                  z_near=4.0, z_far=900.0, steps=520, proj=150.0, fov=1.0,
                  light=(-0.8, 0.55, -0.25), fog_start=0.08, fog_pow=0.7, ambient=0.18,
                  contrast=1.0, colorfn=None, y_limit=None):
    """
    Voxel-landschap (Comanche-stijl) van achter de camera de diepte in.
    Retourneert (masker van getekend terrein, diepte-array).
    colorfn(x, z, h, val) -> optioneel per-punt overschrijving (retourneert val).
    """
    hgt, wdt = cv.h, 160
    xs = (np.arange(wdt) * 2 + 1.0 - 160.0) / 160.0 * fov
    ybuf = np.full(wdt, float(y_limit if y_limit is not None else hgt))
    V = np.full((hgt, wdt), np.nan)
    D = np.full((hgt, wdt), np.nan)
    L = np.array(light, float); L /= np.linalg.norm(L)
    zs = np.geomspace(z_near, z_far, steps)
    rows = np.arange(hgt)[:, None] + 0.5
    for z in zs:
        wx = cam_x + xs * z
        h = H(wx, np.full_like(wx, z))
        e = 0.6
        sx = (H(wx + e, np.full_like(wx, z)) - H(wx - e, np.full_like(wx, z))) / (2 * e)
        sz = (H(wx, np.full_like(wx, z + e)) - H(wx, np.full_like(wx, z - e))) / (2 * e)
        n = np.stack([-sx, np.ones_like(sx), -sz]); n /= np.linalg.norm(n, axis=0)
        lam = np.clip(n[0] * L[0] + n[1] * L[1] + n[2] * L[2], 0, 1)
        val = np.clip(ambient + (1 - ambient) * lam * contrast, 0, 1)
        if colorfn is not None:
            val = colorfn(wx, z, h, val)
        y = horizon + (cam_h - h) * proj / z
        m = (rows >= y[None, :]) & (rows < ybuf[None, :])
        if m.any():
            V[m] = np.broadcast_to(val, (hgt, wdt))[m]
            D[m] = z
            ybuf = np.minimum(ybuf, np.maximum(y, 0))
    drawn = ~np.isnan(V)
    if mask is not None:
        drawn &= mask
    fog = np.clip((np.nan_to_num(D, nan=z_far) - z_far * fog_start) / (z_far * (1 - fog_start)), 0, 1) ** fog_pow
    Vn = np.nan_to_num(V)
    if far_ramp is None:
        cv.ramp(drawn, Vn, near_ramp)
    else:
        sel = fog > BAYER[(np.arange(hgt)[:, None] + 2) % 4, (np.arange(wdt)[None, :] + 1) % 4]
        cv.ramp(drawn & ~sel, Vn, near_ramp)
        cv.ramp(drawn & sel, Vn, far_ramp)
    return drawn, D


def dune_layer(cv, y_base, height, seed, lit_ramp, shadow_ramp, n_peaks=4, light_left=True,
               slant=1.3, rim=None, mask=None, x_range=(-60, 380), lee=(18, 40), wind=(45, 95),
               lit_grad=0.55, depth=40, ripple=0.0):
    """
    Schilderachtige duinlaag: silhouet uit asymmetrische toppen, per top een
    diagonale licht/schaduwgrens (lijzijde). Retourneert het masker van de laag.
    """
    r = _rng(seed)
    X = cv.X[0]
    pxs = np.sort(r.uniform(*x_range, n_peaks))
    hs = height * r.uniform(0.55, 1.0, n_peaks)
    wls = r.uniform(*wind, n_peaks); wrs = r.uniform(*lee, n_peaks)
    sl = slant * r.uniform(0.7, 1.3, n_peaks)
    hump = np.zeros((n_peaks, 160))
    for i in range(n_peaks):
        d = X - pxs[i]
        if not light_left:
            d = -d
        left = np.clip(1 - (-d / wls[i]) ** 2, 0, 1) ** 1.6
        right = np.clip(1 - (d / wrs[i]) ** 2, 0, 1) ** 0.9
        hump[i] = hs[i] * np.where(d < 0, left, right)
    dom = hump.argmax(0)
    crest = y_base - hump.max(0)
    if ripple:
        crest = crest + ripple * np.sin(X / 7.0 + seed)
    m = cv.Y >= crest[None, :]
    if mask is not None:
        m &= mask
    pi = pxs[dom][None, :]; top = (y_base - hs[dom])[None, :]; s = sl[dom][None, :]
    d = (cv.X - pi) if light_left else (pi - cv.X)
    dy = np.clip(cv.Y - top, 0, None)
    boundary = s * dy + 0.012 * dy ** 2 * s
    shadow = m & (d > boundary) & (d > 0)
    # binnen de laag: licht boven bij de kam, donkerder naar beneden
    tdown = np.clip((cv.Y - crest[None, :]) / depth, 0, 1)
    cv.ramp(m & ~shadow, np.clip(1 - lit_grad * tdown, 0, 1), lit_ramp)
    cv.ramp(shadow, np.clip(0.75 - 0.5 * tdown + 0.25 * np.clip((d - boundary) / 30, 0, 1) * 0, 0, 1), shadow_ramp)
    if rim is not None:
        edge = m & ~np.roll(m, 1, axis=0)
        cv.fill(edge & ~shadow, rim)
    return m


def sphere_shade(cv, cx, cy, r, light=(-0.6, -0.5, 0.62)):
    """Lambert-schaduw van een bol (schermcoördinaten); retourneert (masker, waarde)."""
    dx = (cv.X - cx) / r; dy = (cv.Y - cy) / r
    d2 = dx * dx + dy * dy
    m = d2 <= 1
    dz = np.sqrt(np.clip(1 - d2, 0, 1))
    L = np.array(light) / np.linalg.norm(light)
    val = np.clip(dx * L[0] + dy * L[1] + dz * L[2], 0, 1)
    return m, val
