#!/usr/bin/env python3
"""
scenes.py - genereert de bronkunst van alle ASHKARA-scènes (procedureel),
converteert ze naar C64-data en maakt previews.

  python3 scenes.py            # alles
  python3 scenes.py WOESTIJN   # één scène
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from c64art import *
import c64gfx as G

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# DejaVu Serif Bold (Linux, waarmee de oorspronkelijke scènes zijn gemaakt); op Windows Georgia Bold
SERIF = next((f for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
                          "C:/Windows/Fonts/DejaVuSerif-Bold.ttf", "C:/Windows/Fonts/georgiab.ttf",
                          "C:/Windows/Fonts/timesbd.ttf") if os.path.exists(f)),
             "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf")
SCENES = {}


MAXC = {}   # per scène: max. kleuren per cel (standaard 3)


def scene(name, rows=17):
    def deco(fn):
        SCENES[name] = (fn, rows)
        return fn
    return deco


# ---------------------------------------------------------------- helpers
def sun(cv, cx, cy, r, ramp=(ORA, YEL, WHT), glow=None, glow_ramp=None, mask=None):
    m = cv.ellipse(cx, cy, r, r)
    if mask is not None: m &= mask
    if glow:
        g = cv.ellipse(cx, cy, r + glow, r + glow) & ~m
        if mask is not None: g &= mask
        d = np.sqrt((cv.X - cx) ** 2 + (cv.Y - cy) ** 2)
        cv.ramp(g, 1 - (d - r) / glow, glow_ramp)
    d = np.sqrt((cv.X - cx) ** 2 + (cv.Y - cy) ** 2) / r
    cv.ramp(m, 1 - d * 0.6, list(ramp))
    return m


def mesa(cv, x0, x1, top, base, seed, ramp=ROCK, light_left=True):
    """Tafelberg met afgebrokkelde randen en horizontale lagen."""
    r = np.random.default_rng(seed)
    xs = np.linspace(x0, x1, 9)
    tops = top + r.normal(0, 2.0, 9); tops[0] = base; tops[-1] = base
    pts = [(x0 - 6, base)] + [(xs[1] - 4, top + 3)] + list(zip(xs[1:-1], tops[1:-1])) + [(xs[-2] + 5, top + 4), (x1 + 8, base)]
    m = cv.poly(pts)
    t = (cv.X - x0) / max(x1 - x0, 1)
    shade = (1 - t) if light_left else t
    strata = 0.12 * np.sin(cv.Y * 1.3 + value_noise(cv.h, 160, 14, seed) * 4)
    cv.ramp(m, np.clip(0.25 + 0.55 * shade + strata, 0, 1), ramp)
    return m


def character_body(cv, cx, top, width, ramp, base_y=None, folds=True, seed=1):
    """Romp/mantel: trapezium van schouders tot onderrand, met plooien."""
    base_y = base_y or cv.h + 2
    sh = width / 2
    pts = [(cx - sh * 0.55, top), (cx + sh * 0.55, top), (cx + sh * 1.05, top + 18),
           (cx + sh * 1.2, base_y), (cx - sh * 1.2, base_y), (cx - sh * 1.05, top + 18)]
    m = cv.poly(pts)
    t = (cv.X - (cx - sh)) / (2 * sh)
    val = 0.75 - 0.6 * t
    if folds:
        val = val + 0.18 * np.sin((cv.X - cx) / 7.0 + np.sin(cv.Y / 23.0) * 1.5)
    cv.ramp(m, np.clip(val, 0, 1), ramp)
    return m


def head(cv, cx, cy, rx, ry, skin, light=(-0.65, -0.35, 0.68)):
    """Hoofd als belichte ellipsoïde; retourneert masker."""
    dx = (cv.X - cx) / rx; dy = (cv.Y - cy) / ry
    # smallere kin
    dy_adj = np.where(dy > 0, dy, dy)
    width_scale = np.where(dy > 0.2, 1 + (dy - 0.2) * 0.55, 1.0)
    d2 = (dx * width_scale) ** 2 + dy_adj ** 2
    m = d2 <= 1
    dz = np.sqrt(np.clip(1 - d2, 0, 1))
    L = np.array(light) / np.linalg.norm(light)
    val = np.clip(dx * width_scale * L[0] + dy * L[1] + dz * L[2], 0, 1) ** 0.9
    cv.ramp(m, val, skin)
    return m


def face(cv, cx, cy, rx, ry, eye_col=BLK, brow=BLK, mouth=RED, skin_dark=BRN,
         eye_white=LGR, nose=True, mouth_open=0, beard=None, eye_y=-0.05):
    """Gezichtstrekken op een hoofd (schermcoördinaten)."""
    ey = cy + ry * eye_y
    for side in (-1, 1):
        ex = cx + side * rx * 0.42
        # oogwit + iris
        cv.fill(cv.ellipse(ex, ey, rx * 0.22, 1.6), eye_white)
        cv.fill(cv.rect(ex - 1.5 + side * 0.0, ey - 1.5, ex + 2.5, ey + 1.5), eye_col)
        # wenkbrauw
        cv.fill(cv.line([(ex - rx * 0.28, ey - 5 + (1 if side > 0 else 0)), (ex + rx * 0.28, ey - 5 - (0 if side > 0 else 1))], 2), brow)
        # oogkas-schaduw
        cv.fill(cv.rect(ex - rx * 0.25, ey - 3.5, ex + rx * 0.25, ey - 2.5) & (cv.px != brow), skin_dark)
    if nose:
        ny = cy + ry * 0.32
        cv.fill(cv.line([(cx + 1, ey + 2), (cx + 3, ny), (cx - 1, ny + 1)], 2), skin_dark)
    my = cy + ry * 0.58
    if mouth_open:
        cv.fill(cv.ellipse(cx, my + 1, rx * 0.26, 1.5 + mouth_open), BLK)
    else:
        cv.fill(cv.line([(cx - rx * 0.28, my), (cx + rx * 0.28, my)], 2), mouth)
    if beard is not None:
        bm = cv.ellipse(cx, cy + ry * 0.62, rx * 0.95, ry * 0.5) & (cv.Y > cy + ry * 0.38)
        bm &= ~cv.ellipse(cx, my + 0.5, rx * 0.3, 2.2)
        cv.ramp(bm, 0.45 + 0.25 * np.sin(cv.X * 0.9), beard)


# ---------------------------------------------------------------- scènes
def sky(cv, mask, y0, y1, ramp, glow=None, curve=1.0, glow_pow=1.6):
    """Lucht-gradiënt met geïntegreerde zongloed (glow = (x, y, radius, sterkte))."""
    t = np.clip((cv.Y - y0) / max(y1 - y0, 1e-6), 0, 1) ** curve
    if glow:
        gx, gy, gr, gs = glow
        d = np.sqrt((cv.X - gx) ** 2 + ((cv.Y - gy) * 1.25) ** 2)
        t = t + gs * np.clip(1 - d / gr, 0, 1) ** glow_pow
    cv.ramp(mask, np.clip(t, 0, 1), ramp)


@scene("WOESTIJN")
def s_woestijn(cv):
    """Open woestijn overdag: verre tafelbergen, duinzee onder een hoge zon."""
    sky(cv, cv.all(), 0, 64, [BLU, BLU, LBL, LBL, LGR, WHT], glow=(250, 18, 90, 0.35))
    sun(cv, 250, 18, 8, ramp=(YEL, WHT, WHT))
    mesa(cv, 14, 96, 50, 66, seed=4, ramp=[PUR, LRD, LGR])
    mesa(cv, 196, 296, 55, 66, seed=9, ramp=[PUR, LRD, LGR], light_left=False)
    dune_layer(cv, 70, 8, 11, [LRD, LGR, LGR], [PUR, PUR], n_peaks=6, light_left=False, depth=20, slant=0.6)
    dune_layer(cv, 86, 14, 12, [ORA, LRD, YEL], [BRN, BRN], n_peaks=5, light_left=False, depth=25, slant=0.55)
    dune_layer(cv, 106, 22, 13, [ORA, YEL, YEL], [BRN, ORA], n_peaks=4, light_left=False, depth=35, slant=0.5)
    dune_layer(cv, 136, 32, 14, [ORA, YEL, YEL, WHT], [BLK, BRN, BRN], n_peaks=3, light_left=False,
               depth=45, wind=(80, 150), lee=(30, 60), slant=0.45)
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


@scene("BALKON")
def s_balkon(cv):
    """Balkon van Fort Varo bij zonsondergang: silhouet-architectuur tegen de gloed."""
    sky(cv, cv.all(), 0, 96, [BLU, PUR, PUR, RED, LRD, ORA, YEL], glow=(168, 88, 120, 0.45), curve=1.2)
    sun(cv, 168, 88, 20, ramp=(ORA, YEL, WHT))
    for y in (80, 84, 87):
        cv.fill(cv.rect(140, y, 196, y + 1) & cv.ellipse(168, 88, 20, 20), ORA)
    cv.stars(cv.Y < 26, 40, seed=3, colors=(LBL, WHT))
    mesa(cv, 6, 76, 76, 94, seed=2, ramp=[BLK, BLK, PUR])
    mesa(cv, 240, 318, 72, 94, seed=5, ramp=[BLK, BLK, PUR], light_left=False)
    dune_layer(cv, 96, 6, 41, [RED, LRD, ORA], [PUR, PUR], n_peaks=6, depth=10, slant=0.6)
    dune_layer(cv, 110, 12, 42, [PUR, RED, LRD], [BLK, PUR], n_peaks=5, depth=20, slant=0.5)
    dune_layer(cv, 136, 18, 43, [BLK, PUR, RED], [BLK, BLK], n_peaks=4, depth=30, slant=0.5)
    arch = (cv.rect(0, 0, 320, 136) & ~cv.ellipse(160, 150, 150, 142)) | cv.rect(0, 0, 18, 136) | cv.rect(302, 0, 320, 136)
    rail = cv.rect(0, 106, 320, 112) | cv.rect(0, 128, 320, 136)
    bal = np.zeros_like(rail)
    for x in range(14, 320, 22):
        bal |= cv.ellipse(x, 120, 4.5, 8) | cv.rect(x - 3, 111, x + 3, 114) | cv.rect(x - 3, 126, x + 3, 129)
    sil = arch | rail | bal
    cv.fill(sil, BLK)
    rim2 = sil & ~np.roll(sil, 1, axis=0)
    cv.fill(rim2 & (cv.Y > 100) & (cv.X > 20) & (cv.X < 300), ORA)
    inner = cv.ellipse(160, 150, 150, 142) & ~cv.ellipse(160, 150, 147, 139) & (cv.Y < 100)
    cv.fill(inner, RED)


@scene("TITEL", rows=25)
def s_titel(cv):
    """Titelscherm (volledig bitmap, geen split)."""
    sky(cv, cv.all(), 20, 158, [BLK, BLU, PUR, RED, LRD, ORA, YEL], glow=(110, 150, 140, 0.4), curve=1.3)
    cv.stars(cv.Y < 96, 80, seed=7)
    m1, v1 = sphere_shade(cv, 268, 96, 12, light=(-0.9, -0.1, 0.3))
    cv.ramp(m1, v1 ** 0.6, [BLU, LBL, LGR, WHT])
    m2, v2 = sphere_shade(cv, 238, 84, 4.5, light=(-0.9, -0.1, 0.3))
    cv.ramp(m2, v2 ** 0.6, [BLU, LBL, LGR])
    sun(cv, 110, 154, 30, ramp=(ORA, YEL, WHT))
    for y in (140, 145, 149, 152):
        cv.fill(cv.rect(60, y, 160, y + 1) & cv.ellipse(110, 154, 30, 30), LRD)
    mesa(cv, 196, 304, 138, 158, seed=31, ramp=[BLK, PUR, RED], light_left=True)
    dune_layer(cv, 162, 8, 51, [RED, RED], [PUR, PUR], n_peaks=6, depth=10, slant=0.7, light_left=False, rim=LRD)
    dune_layer(cv, 178, 14, 52, [PUR, PUR], [BLK, BLK], n_peaks=5, depth=20, slant=0.6, light_left=False, rim=RED)
    dune_layer(cv, 202, 24, 53, [BLK, BLK], [BLK, BLK], n_peaks=4, depth=30, slant=0.5, light_left=False, rim=ORA)
    logo = cv.text_mask("ASHKARA", SERIF, 44, 160, 36, spacing=3, anchor="mm")
    shadow = np.roll(np.roll(logo, 2, axis=0), 1, axis=1)
    cv.fill(shadow & ~logo, BLK)
    cv.vgrad(logo, 20, 52, [WHT, YEL, YEL, ORA, LRD, RED], curve=1.0)
    cv.outline(logo | shadow, BLK)
    sub = cv.text_mask("DE AMBERWOESTIJN", SERIF, 12, 160, 68, spacing=4, anchor="mm")
    cv.outline(sub, BLK)
    cv.fill(sub, LRD)


@scene("RUIMTE")
def s_ruimte(cv):
    """Intro: nadering van Ashkara vanuit de ruimte."""
    cv.fill(cv.all(), BLK)
    cv.stars(cv.all(), 120, seed=61)
    cv.stars(cv.all(), 25, seed=62, colors=(WHT,))
    # planeet
    m, v = sphere_shade(cv, 236, 150, 120, light=(-0.75, -0.45, 0.5))
    bands = 0.12 * np.sin(cv.Y / 9.0 + fbm(cv.h, 160, 30, 63) * 5)
    val = np.clip(v ** 0.8 + bands * (v > 0.05), 0, 1)
    cv.ramp(m, val, [BLK, BRN, ORA, ORA, LRD, YEL])
    rim = cv.ellipse(236, 150, 123, 123) & ~m
    d = np.sqrt((cv.X - 236) ** 2 + (cv.Y - 150) ** 2)
    ang = np.clip(-(cv.X - 236) / 123 - (cv.Y - 150) / 160, 0, 1)
    cv.ramp(rim & (ang > 0.25), ang, [BLU, LBL, LRD, YEL])
    # maan
    m2, v2 = sphere_shade(cv, 70, 30, 9, light=(0.4, -0.3, 0.6))
    cv.ramp(m2, v2, [BLK, DGR, GRY, LGR])
    # schip (generiek)
    hull = cv.poly([(60, 98), (138, 84), (150, 88), (138, 93), (66, 103)])
    cv.ramp(hull, np.clip((cv.Y - 84) / 18, 0, 1)[...] * -1 + 1, [DGR, GRY, LGR, WHT])
    fin = cv.poly([(96, 92), (118, 74), (126, 76), (112, 92)])
    cv.ramp(fin, 0.6, [DGR, GRY, LGR])
    cv.outline(hull | fin, BLK)
    cv.fill(cv.ellipse(56, 100, 6, 3), LBL)
    cv.fill(cv.ellipse(52, 100, 3, 2), WHT)
    cv.fill(cv.rect(118, 87, 130, 88), LBL)


def perspective_room(cv, vp, back, wall_ramp, floor_ramp, ceil_ramp, side_shade=0.35):
    """Eén-punts perspectief kamer. back = (x0,y0,x1,y1) van de achterwand."""
    x0, y0, x1, y1 = back
    W, Hh = 320, cv.h
    left = cv.poly([(0, 0), (x0, y0), (x0, y1), (0, Hh)])
    right = cv.poly([(W, 0), (x1, y0), (x1, y1), (W, Hh)])
    ceil = cv.poly([(0, 0), (W, 0), (x1, y0), (x0, y0)])
    floor = cv.poly([(0, Hh), (W, Hh), (x1, y1), (x0, y1)])
    backm = cv.rect(x0, y0, x1, y1)
    cv.vgrad(backm, y0, y1, wall_ramp[::-1][:3][::-1] if False else wall_ramp)
    t = np.clip(cv.X / x0, 0, 1)
    cv.ramp(left, side_shade + 0.45 * t, wall_ramp)
    t = np.clip((W - cv.X) / (W - x1), 0, 1)
    cv.ramp(right, side_shade * 0.6 + 0.4 * t, wall_ramp)
    cv.vgrad(ceil, 0, y0, ceil_ramp)
    cv.vgrad(floor, y1, Hh, floor_ramp, curve=0.8)
    return left, right, ceil, floor, backm


def column(cv, x, y0, y1, w, ramp, light_left=True):
    m = cv.rect(x - w / 2, y0, x + w / 2, y1)
    t = (cv.X - (x - w / 2)) / w
    val = np.sin(np.clip(t, 0, 1) * np.pi) * (0.9 - 0.5 * t if light_left else 0.4 + 0.5 * t)
    cv.ramp(m, np.clip(val, 0, 1), ramp)
    cap = cv.rect(x - w / 2 - 3, y0, x + w / 2 + 3, y0 + 4) | cv.rect(x - w / 2 - 3, y1 - 4, x + w / 2 + 3, y1)
    cv.ramp(cap, 0.55, ramp)
    cv.fill(cv.rect(x - w / 2 - 3, y0 + 4, x + w / 2 + 3, y0 + 5) | cv.rect(x - w / 2 - 3, y1 - 5, x + w / 2 + 3, y1 - 4), BLK)
    return m | cap


def emblem(cv, cx, cy, r, col_ring, col_center):
    ring = cv.ellipse(cx, cy, r, r) & ~cv.ellipse(cx, cy, r - 2, r - 2)
    cv.fill(ring, col_ring)
    cv.fill(cv.ellipse(cx, cy, r * 0.45, r * 0.45), col_center)
    for a in np.linspace(0, 2 * np.pi, 8, endpoint=False):
        cv.fill(cv.line([(cx + np.cos(a) * r * 0.55, cy + np.sin(a) * r * 0.55),
                         (cx + np.cos(a) * r * 0.85, cy + np.sin(a) * r * 0.85)], 2), col_center)


@scene("RAADZAAL")
def s_raadzaal(cv):
    """Raadzaal van Fort Varo: zuilen, banieren, boogvenster op de woestijn."""
    left, right, ceil, floor, back = perspective_room(
        cv, (160, 60), (84, 16, 236, 88),
        wall_ramp=[BLK, BRN, ORA, LGR], floor_ramp=[BRN, ORA, BRN, BLK], ceil_ramp=[BLK, BRN])
    # tegels op de vloer (perspectief)
    for i in range(-8, 9):
        cv.fill(cv.line([(160 + i * 9.5, 88), (160 + i * 46, 136)], 1) & floor, BLK)
    for y in (94, 102, 113, 128):
        cv.fill(cv.rect(0, y, 320, y + 1) & floor, BLK)
    # lichtbaan van het venster op de vloer
    beam = cv.poly([(140, 88), (180, 88), (230, 136), (110, 136)]) & floor
    cv.ramp(beam, 0.55 + 0.35 * np.clip((136 - cv.Y) / 48, 0, 1), [ORA, LGR, YEL])
    # boogvenster
    win = cv.rect(132, 34, 188, 88) | cv.ellipse(160, 34, 28, 22)
    win &= cv.Y < 88
    sky(cv, win, 14, 74, [LBL, LGR, WHT, YEL])
    dune_layer(cv, 80, 6, 71, [ORA, YEL], [BRN], n_peaks=3, mask=win, x_range=(120, 200), wind=(20, 40), lee=(8, 16), depth=8, slant=0.5)
    dune_layer(cv, 90, 6, 72, [ORA, YEL, YEL], [BRN], n_peaks=3, mask=win, x_range=(120, 200), wind=(20, 40), lee=(8, 16), depth=8, slant=0.5)
    frame = cv.outline(win, BLK, 1)
    cv.fill(cv.rect(158, 14, 162, 88) & win, BLK)
    cv.fill(cv.rect(132, 56, 188, 58) & win, BLK)
    # banieren op de achterwand
    for bx in (104, 216):
        ban = cv.poly([(bx - 9, 22), (bx + 9, 22), (bx + 9, 70), (bx, 76), (bx - 9, 70)])
        t = (cv.X - (bx - 9)) / 18
        cv.ramp(ban, np.clip(0.9 - 0.6 * t + 0.1 * np.sin(cv.X), 0, 1), [BLK, RED, LRD])
        emblem(cv, bx, 42, 6, ORA, YEL)
        cv.fill(cv.rect(bx - 11, 20, bx + 11, 22), ORA)
    # zuilen
    for x, w in ((26, 22), (70, 14)):
        column(cv, x, 0, 136 if x == 26 else 104, w, [BLK, BRN, ORA, LGR])
    for x, w in ((294, 22), (250, 14)):
        column(cv, x, 0, 136 if x == 294 else 104, w, [BLK, BRN, ORA, LGR], light_left=False)
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


@scene("COMMS")
def s_comms(cv):
    """Communicatiekamer: groot scherm, console met lampjes."""
    cv.fill(cv.all(), BLK)
    left, right, ceil, floor, back = perspective_room(
        cv, (160, 60), (60, 10, 260, 92),
        wall_ramp=[BLK, DGR, GRY], floor_ramp=[DGR, BLK], ceil_ramp=[BLK, DGR])
    # wandpanelen
    for x in range(64, 260, 28):
        cv.fill(cv.rect(x, 12, x + 1, 92), BLK)
    for x in (68, 236):
        rack = cv.rect(x, 22, x + 20, 86)
        cv.ramp(rack, 0.3, [BLK, DGR, GRY])
        r = np.random.default_rng(x)
        for yy in range(26, 84, 6):
            for xx in range(x + 3, x + 18, 5):
                cv.fill(cv.rect(xx, yy, xx + 2, yy + 2), r.choice([RED, GRN, YEL, LBL, DGR]))
    # groot scherm
    scr = cv.rect(96, 16, 224, 78)
    cv.fill(cv.rect(92, 13, 228, 81), DGR)
    cv.fill(cv.rect(92, 13, 228, 14) | cv.rect(92, 80, 228, 81), GRY)
    noise = fbm(cv.h, 160, 6, 81, octaves=2)
    cv.ramp(scr, 0.25 + 0.35 * noise + 0.1 * np.sin(cv.Y * 2.2), [BLK, BLU, LBL, CYN])
    cv.fill(scr & (np.arange(cv.h)[:, None] % 2 == 0) & (cv.px == BLU), BLK)
    # console
    desk = cv.poly([(0, 108), (320, 108), (320, 136), (0, 136)])
    top = cv.poly([(20, 96), (300, 96), (320, 108), (0, 108)])
    cv.ramp(top, np.clip((cv.Y - 96) / 12, 0, 1) * 0.5 + 0.3, [BLK, DGR, GRY])
    cv.ramp(desk, 0.2, [BLK, DGR])
    r = np.random.default_rng(5)
    for i in range(44):
        x = r.uniform(24, 296); y = r.uniform(98, 106)
        cv.fill(cv.rect(x, y, x + 3, y + 1.5), r.choice([RED, YEL, GRN, LBL, WHT, ORA]))
    cv.fill(cv.rect(0, 108, 320, 109), GRY)
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


@scene("HANGAR")
def s_hangar(cv):
    """Hangar met zweefglider, open poort naar de woestijn."""
    left, right, ceil, floor, back = perspective_room(
        cv, (160, 62), (72, 14, 248, 84),
        wall_ramp=[BLK, DGR, GRY], floor_ramp=[DGR, GRY, DGR, BLK], ceil_ramp=[BLK, DGR])
    door = cv.rect(96, 26, 224, 84)
    sky(cv, door, 26, 70, [LBL, LGR, WHT])
    dune_layer(cv, 74, 8, 91, [LRD, LGR], [PUR], n_peaks=4, mask=door, x_range=(90, 230), wind=(25, 50), lee=(10, 20), depth=8, slant=0.6)
    dune_layer(cv, 86, 10, 92, [ORA, YEL], [BRN], n_peaks=3, mask=door, x_range=(90, 230), wind=(30, 60), lee=(12, 22), depth=10, slant=0.5)
    cv.outline(door, BLK, 1)
    # dakspanten
    for i in range(0, 9):
        x = 72 + i * 22
        cv.fill(cv.line([(x, 14), (160 + (x - 160) * 3.2, 0)], 2) & ceil, GRY)
    for x in range(78, 248, 12):
        cv.fill(cv.rect(x, 14, x + 1, 26), DGR)
    cv.fill(cv.rect(72, 24, 248, 26), GRY)
    # vloermarkering
    for k in range(6):
        y = 90 + k * 8
        cv.fill(cv.poly([(150, y), (170, y), (172 + k, y + 3), (148 - k, y + 3)]), YEL)
    # glider (generiek VTOL)
    body = cv.poly([(84, 100), (196, 92), (222, 98), (200, 108), (92, 110)])
    cv.ramp(body, np.clip(1 - (cv.Y - 92) / 18, 0, 1), [DGR, GRY, LGR, WHT])
    wing = cv.poly([(118, 98), (176, 96), (238, 82), (244, 86), (186, 102), (122, 104)])
    cv.ramp(wing, 0.55, [DGR, GRY, LGR])
    wing2 = cv.poly([(110, 104), (170, 104), (128, 120), (114, 120)])
    cv.ramp(wing2, 0.35, [DGR, GRY, LGR])
    canopy = cv.ellipse(196, 96, 14, 5) & (cv.Y < 98)
    cv.ramp(canopy, 0.6, [BLU, LBL, WHT])
    for ex, ey in ((150, 112), (226, 90)):
        cv.fill(cv.ellipse(ex, ey, 10, 5), DGR)
        cv.fill(cv.ellipse(ex, ey, 6, 3), BLK)
    cv.outline(body | wing | wing2, BLK)
    cv.fill(cv.rect(96, 110, 100, 120) | cv.rect(180, 106, 184, 118), DGR)
    # kisten
    for x, y, s in ((18, 112, 22), (36, 120, 16), (276, 116, 24)):
        c = cv.rect(x, y, x + s, 136)
        cv.ramp(c, 0.5, [BLK, BRN, ORA])
        cv.fill(cv.rect(x, y, x + s, y + 1) | cv.rect(x, y, x + 1, 136) | cv.rect(x + s - 1, y, x + s, 136), BLK)
        cv.fill(cv.line([(x, y), (x + s, 136)], 1), BLK)
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


def rock_wall(cv, mask, seed, ramp=ROCK, light_left=True, strata=True):
    n = fbm(cv.h, 160, 22, seed, octaves=4)
    t = cv.X / 320.0
    shade = (1 - t) if light_left else t
    val = 0.18 + 0.45 * n + 0.25 * shade
    if strata:
        val += 0.10 * np.sin(cv.Y / 2.8 + n * 6)
    cv.ramp(mask, np.clip(val, 0, 1), ramp)


@scene("KLOOF")
def s_kloof(cv):
    """Rotskloof met de verborgen ingang van een Kethari-grotkamp."""
    sky(cv, cv.all(), 0, 40, [BLU, LBL, LGR])
    backrock = cv.poly([(70, 136), (80, 30), (130, 18), (200, 22), (250, 34), (256, 136)])
    rock_wall(cv, backrock, 101, ramp=[BLK, BRN, RED, LRD, ORA], light_left=True)
    cave = cv.ellipse(166, 98, 30, 34) & (cv.Y < 112)
    cv.fill(cave.copy(), BLK)
    cv.outline(cave, BRN, 2)
    inner = cv.ellipse(166, 104, 18, 22) & (cv.Y < 112)
    cv.ramp(inner, 0.4 + 0.3 * np.clip((cv.Y - 86) / 24, 0, 1), [BLK, RED, ORA])  # vuurschijn diep binnen
    leftw = cv.poly([(0, 0), (40, 0), (72, 30), (96, 136), (0, 136)])
    rightw = cv.poly([(320, 0), (282, 0), (252, 26), (232, 136), (320, 136)])
    rock_wall(cv, leftw, 102, ramp=[BLK, BRN, RED, LRD], light_left=False)
    rock_wall(cv, rightw, 103, ramp=[BLK, BRN, RED, LRD], light_left=True)
    cv.outline(leftw | rightw, BLK)
    ground = cv.poly([(60, 112), (260, 112), (320, 136), (0, 136)])
    cv.vgrad(ground, 112, 136, [ORA, YEL, ORA, BRN])
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


@scene("GROT")
def s_grot(cv):
    """Binnen in het grotkamp: lantaarns, waterbassin, doeken."""
    cv.fill(cv.all(), BLK)
    room = cv.ellipse(160, 80, 175, 110)
    rock_wall(cv, room, 111, ramp=[BLK, BRN, RED, ORA], light_left=True)
    # vignet
    d = np.sqrt(((cv.X - 160) / 175) ** 2 + ((cv.Y - 70) / 100) ** 2)
    cv.fill(room & (d > 0.92) & (cv.bx < (d - 0.92) * 9), BLK)
    # lantaarngloed
    for lx, ly in ((60, 40), (262, 46)):
        g = cv.ellipse(lx, ly, 44, 38)
        dd = np.sqrt(((cv.X - lx) / 44) ** 2 + ((cv.Y - ly) / 38) ** 2)
        cv.ramp(g & (cv.px != BLK), np.clip(1 - dd, 0, 1) * 0.9 + 0.1, [BRN, RED, ORA, YEL])
        cv.fill(cv.rect(lx - 3, ly - 4, lx + 3, ly + 5), YEL)
        cv.fill(cv.rect(lx - 2, ly - 2, lx + 2, ly + 3), WHT)
        cv.fill(cv.rect(lx - 4, ly - 6, lx + 4, ly - 4) | cv.rect(lx - 4, ly + 5, lx + 4, ly + 7), BLK)
        cv.fill(cv.rect(lx - 1, 0, lx + 1, ly - 6), BLK)
    # doeken
    for x0, col in ((96, PUR), (204, RED)):
        cloth = cv.poly([(x0, 8), (x0 + 22, 8), (x0 + 18, 70), (x0 + 11, 64), (x0 + 4, 72)])
        cv.ramp(cloth, np.clip(0.5 + 0.35 * np.sin((cv.X - x0) / 3.0), 0, 1), [BLK, col, LRD])
    # treden en bassin
    for k, y in enumerate((96, 104, 113)):
        st = cv.rect(40 + k * 4, y, 280 - k * 4, y + 3)
        cv.ramp(st, 0.55, [BLK, BRN, ORA])
        cv.fill(cv.rect(40 + k * 4, y + 3, 280 - k * 4, y + 4), BLK)
    pool = cv.ellipse(160, 126, 92, 12)
    cv.ramp(pool, 0.45 + 0.35 * np.sin(cv.X / 6.0 + cv.Y * 1.7) * (cv.Y < 128), [BLK, BLU, LBL, CYN])
    cv.outline(pool, BRN)
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


@scene("OOGST")
def s_oogst(cv):
    """Amberiet-oogstmachine op een duin, stofpluim, gloeiende kristallen in het zand."""
    sky(cv, cv.all(), 0, 70, [LRD, LRD, ORA, YEL, YEL], glow=(60, 30, 120, 0.3))
    dune_layer(cv, 66, 8, 121, [LRD, YEL], [ORA], n_peaks=6, depth=14, slant=0.6)
    dune_layer(cv, 84, 14, 122, [ORA, YEL], [BRN], n_peaks=4, depth=24, slant=0.5)
    # machine op middelste laag
    tracks = cv.rect(132, 88, 248, 100)
    cv.fill(tracks, BLK)
    for x in range(134, 248, 6):
        cv.fill(cv.rect(x, 89, x + 3, 99), DGR)
    body = cv.poly([(126, 88), (138, 54), (232, 54), (254, 88)])
    t = (cv.X - 126) / 128
    cv.ramp(body, np.clip(0.85 - 0.6 * t, 0, 1), [BLK, DGR, GRY, LGR])
    cab = cv.rect(214, 40, 242, 56)
    cv.ramp(cab, 0.5, [DGR, GRY, LGR])
    cv.fill(cv.rect(218, 44, 238, 50), LBL)
    arm = cv.line([(150, 60), (110, 34), (78, 70)], 4)
    cv.fill(arm, GRY)
    cv.fill(cv.line([(150, 58), (110, 32)], 1), LGR)
    for x in range(146, 214, 16):
        cv.fill(cv.rect(x, 62, x + 10, 66), YEL)
        cv.fill(cv.rect(x, 66, x + 10, 68), BLK)
    cv.outline(body | cab | tracks, BLK)
    # stofpluim
    plume = cv.ellipse(78, 76, 36, 16) | cv.ellipse(52, 64, 30, 18) | cv.ellipse(34, 50, 26, 16)
    n = fbm(cv.h, 160, 10, 123, octaves=3)
    cv.ramp(plume & (n > 0.38), n, [ORA, LRD, YEL, WHT])
    dune_layer(cv, 136, 26, 124, [ORA, YEL, YEL], [BLK, BRN], n_peaks=3, depth=40, wind=(80, 140), lee=(30, 60), slant=0.5)
    # amberglinsters
    r = np.random.default_rng(7)
    for _ in range(36):
        x = r.uniform(0, 320); y = r.uniform(110, 132)
        if cv.px[int(y), int(x / 2)] in (ORA, YEL, BRN):
            cv.fill(cv.rect(x, y, x + 2, y + 1), WHT if r.random() < 0.3 else YEL)
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


@scene("NACHT")
def s_nacht(cv):
    """Nachtelijke woestijn met twee manen en een verre kampvuurgloed."""
    sky(cv, cv.all(), 0, 96, [BLK, BLK, BLU, BLU, LBL], curve=1.6)
    cv.stars(cv.Y < 70, 110, seed=131)
    m1, v1 = sphere_shade(cv, 236, 30, 15, light=(-0.95, -0.1, 0.15))
    cv.ramp(m1, np.clip(v1 * 1.4, 0, 1), [BLK, BLU, LBL, WHT])
    m2, v2 = sphere_shade(cv, 92, 22, 5, light=(-0.95, -0.1, 0.3))
    cv.ramp(m2, v2 ** 0.6, [BLU, LBL, LGR])
    dune_layer(cv, 84, 8, 132, [BLU, BLU, LBL], [BLK], n_peaks=6, depth=14, slant=0.6, light_left=False, lit_grad=0.8)
    cv.fill(cv.rect(196, 80, 200, 82), ORA); cv.fill(cv.rect(197, 79, 199, 80), YEL)
    glow = cv.ellipse(198, 80, 12, 4) & (cv.px == BLU)
    cv.fill(glow & (cv.bx < 0.5), PUR)
    # lichtende amber-velden op de verre duinen
    n = fbm(cv.h, 160, 10, 135, octaves=3)
    fieldm = (cv.Y > 84) & (cv.Y < 98) & (n > 0.6) & (cv.px != BLK)
    cv.ramp(fieldm, np.clip((n - 0.6) * 4, 0, 1), [PUR, ORA, YEL])
    dune_layer(cv, 104, 16, 133, [BLU, LBL], [BLK], n_peaks=4, depth=22, slant=0.55, light_left=False, rim=LGR, lit_grad=0.9)
    dune_layer(cv, 136, 26, 134, [BLK, BLU, BLU], [BLK], n_peaks=3, depth=40, wind=(80, 140), lee=(30, 60), slant=0.5, light_left=False, rim=LBL, lit_grad=0.9)
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


@scene("STORM")
def s_storm(cv):
    """Zandstorm: wervelende banden, zon als bleke schijf."""
    n1 = fbm(cv.h, 160, 40, 141, octaves=4)
    swirl = np.sin((cv.X * 0.6 + cv.Y * 1.4) / 26.0 + n1 * 7.0)
    val = 0.45 + 0.28 * swirl + 0.25 * (n1 - 0.5) - 0.25 * (cv.Y / 136.0)
    cv.ramp(cv.all(), np.clip(val, 0, 1), [BRN, ORA, LRD, YEL])
    s = cv.ellipse(222, 40, 12, 12)
    cv.fill(s & (cv.bx < 0.7), YEL)
    cv.fill(cv.ellipse(222, 40, 7, 7) & (cv.bx < 0.6), WHT)
    dune_layer(cv, 118, 18, 142, [BRN, ORA], [BRN, BRN], n_peaks=4, depth=30, slant=0.5)
    # strepen
    r = np.random.default_rng(143)
    for _ in range(50):
        x = r.uniform(-40, 320); y = r.uniform(0, 130); L = r.uniform(14, 40)
        cv.fill(cv.line([(x, y), (x + L, y + L * 0.28)], 1), r.choice([YEL, LRD, ORA]))
    dune_layer(cv, 136, 16, 144, [BLK, BRN], [BLK], n_peaks=3, depth=20, slant=0.5)
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


@scene("VESTING")
def s_vesting(cv):
    """De vesting van het Consortium onder een rode nachthemel."""
    sky(cv, cv.all(), 0, 90, [BLK, BLK, RED, RED, LRD, ORA], curve=1.2, glow=(166, 70, 110, 0.35))
    cv.stars(cv.Y < 40, 40, seed=151, colors=(LRD, GRY))
    # zoeklichten
    for x0, ang in ((132, -0.45), (206, 0.35)):
        beam = cv.poly([(x0, 46), (x0 + 6, 46), (x0 + 6 + 140 * ang + 12, -10), (x0 + 140 * ang - 12, -10)])
        cv.fill(beam & (cv.bx < 0.35) & (cv.px != BLK), LGR)
    rock = cv.poly([(0, 136), (0, 104), (60, 92), (110, 76), (220, 74), (270, 90), (320, 98), (320, 136)])
    rock_wall(cv, rock, 152, ramp=[BLK, BLK, BRN, RED], light_left=False)
    fort = cv.rect(104, 46, 228, 82)
    for tx, tw, th in ((96, 18, 24), (126, 12, 34), (150, 16, 8), (180, 22, 18), (210, 12, 30), (232, 18, 26)):
        fort |= cv.rect(tx, th, tx + tw, 82)
        for cx in range(int(tx), int(tx + tw), 6):
            fort |= cv.rect(cx, th - 4, cx + 3, th)
    cv.fill(fort, BLK)
    cv.fill(fort & ~np.roll(fort, 1, axis=1) & (cv.Y > 20), RED)
    r = np.random.default_rng(153)
    for _ in range(34):
        x = r.uniform(106, 240); y = r.uniform(18, 78)
        if cv.px[int(y), int(x / 2)] in (BLK, DGR):
            cv.fill(cv.rect(x, y, x + 2, y + 2), r.choice([YEL, ORA, ORA, RED]))
    cv.fill(cv.rect(132, 44, 138, 48) | cv.rect(206, 44, 212, 48), WHT)
    # vuren aan de voet
    for fx in (60, 280):
        cv.fill(cv.ellipse(fx, 104, 6, 6), ORA); cv.fill(cv.ellipse(fx, 105, 3, 3), YEL)
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


@scene("OASE")
def s_oase(cv):
    """Een groene oase: het resultaat van de vergroening."""
    sky(cv, cv.all(), 0, 70, [BLU, LBL, LBL, LGR, WHT])
    for cx, cy, rx in ((60, 24, 30), (90, 20, 22), (238, 30, 34)):
        cl = cv.ellipse(cx, cy, rx, rx * 0.35) | cv.ellipse(cx + rx * 0.4, cy - 3, rx * 0.6, rx * 0.3)
        cv.ramp(cl, np.clip(1 - (cv.Y - cy + 8) / 16, 0, 1), [LGR, WHT])
    dune_layer(cv, 74, 10, 161, [LRD, YEL], [ORA], n_peaks=6, depth=12, slant=0.6)
    dune_layer(cv, 88, 10, 162, [ORA, YEL], [BRN], n_peaks=5, depth=16, slant=0.55)
    grass = cv.poly([(0, 96), (80, 88), (240, 90), (320, 96), (320, 136), (0, 136)])
    n = fbm(cv.h, 160, 8, 163)
    cv.ramp(grass, np.clip(0.3 + 0.6 * n, 0, 1), [BLK, GRN, LGN])
    pool = cv.ellipse(170, 112, 100, 14)
    cv.ramp(pool, np.clip(0.4 + 0.4 * np.sin(cv.X / 7 + cv.Y * 2.0), 0, 1), [BLU, LBL, WHT])
    cv.outline(pool, GRN)
    def palm(x, base, h, lean):
        trunk = cv.line([(x, base), (x + lean * 0.5, base - h * 0.5), (x + lean, base - h)], 4)
        cv.fill(trunk, BRN)
        cv.fill(cv.line([(x + 1, base), (x + lean * 0.5 + 1, base - h * 0.5), (x + lean + 1, base - h)], 1), ORA)
        tx, ty = x + lean, base - h
        for a in np.linspace(-2.8, -0.3, 6):
            pts = [(tx, ty)]
            for k in range(1, 5):
                pts.append((tx + np.cos(a) * k * 7 * 1.6, ty + np.sin(a) * k * 6 + k * k * 1.1))
            cv.fill(cv.line(pts, 3), GRN)
            cv.fill(cv.line(pts[:3], 1), LGN)
        for a in np.linspace(0.3, 0.9, 2):
            pts = [(tx, ty)] + [(tx + np.cos(a) * k * 9, ty + k * 4) for k in range(1, 4)]
            cv.fill(cv.line(pts, 3), GRN)
    palm(40, 120, 70, 14); palm(70, 116, 52, -8); palm(272, 122, 66, -16); palm(300, 128, 44, 6)
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


@scene("KAART")
def s_kaart(cv):
    """Strategische kaart (bovenaanzicht). Markers zet de engine als hele cellen (DESIGN.md §4.2)."""
    n = fbm(cv.h, 160, 50, 171, octaves=4)
    m2 = fbm(cv.h, 160, 22, 172, octaves=2)
    sand = n < 0.50
    rockm = (n >= 0.50) & (n < 0.63)
    mount = n >= 0.63
    salt = (m2 > 0.66) & sand & (n < 0.42)
    stripes = np.sin((cv.X * 0.55 + cv.Y * 1.3) / 5.0 + m2 * 6)
    cv.ramp(sand, np.clip(0.42 + 0.3 * stripes, 0, 1), [ORA, ORA, YEL])
    cv.ramp(rockm, np.clip(0.3 + 0.5 * (n - 0.5) / 0.13, 0, 1), [BRN, RED, LRD])
    cv.ramp(mount, np.clip((n - 0.63) / 0.15, 0, 1), [BLK, BRN, LGR])
    cv.ramp(salt, np.clip(0.5 + 0.4 * m2, 0, 1), [YEL, LGR, WHT])
    for region in (rockm | mount, mount, salt):
        edge = region & ~(np.roll(region, 1, 0) & np.roll(region, -1, 0) & np.roll(region, 1, 1) & np.roll(region, -1, 1))
        cv.fill(edge, BLK)
    grid = ((np.arange(160)[None, :] % 40) == 0) | ((np.arange(cv.h)[:, None] % 34) == 0)
    cv.fill(grid & (cv.bx < 0.3), BRN)
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


@scene("EINDE", rows=25)
def s_einde(cv, text="ASHKARA IS VRIJ"):
    """Einde: dageraad, de eerste regenwolken boven een groenende woestijn."""
    sky(cv, cv.all(), 0, 140, [BLU, LBL, LBL, LRD, ORA, YEL], glow=(230, 132, 120, 0.35))
    sun(cv, 230, 132, 18, ramp=(YEL, WHT, WHT))
    for cx, cy, rx in ((50, 84, 46), (120, 70, 50), (280, 76, 40), (190, 98, 36)):
        cl = cv.ellipse(cx, cy, rx, rx * 0.32) | cv.ellipse(cx - rx * 0.4, cy + 2, rx * 0.6, rx * 0.25)
        cv.ramp(cl, np.clip(1 - (cv.Y - cy + 10) / 20, 0, 1), [GRY, LGR, WHT])
        rain = cv.rect(cx - rx * 0.5, cy + 8, cx + rx * 0.5, cy + 40) & ~cl
        cv.fill(rain & ((np.arange(160)[None, :] + np.arange(cv.h)[:, None] // 3) % 5 == 0) & (cv.bx < 0.45), LGR)
    dune_layer(cv, 146, 10, 181, [LRD, YEL], [ORA], n_peaks=6, depth=12, slant=0.6)
    land = dune_layer(cv, 170, 16, 182, [ORA, YEL], [BRN], n_peaks=5, depth=20, slant=0.55)
    n = fbm(cv.h, 160, 10, 183)
    cv.ramp(land & (n > 0.55) & (cv.Y > 160), n, [GRN, LGN])
    near = dune_layer(cv, 200, 22, 184, [GRN, LGN], [BLK, GRN], n_peaks=4, depth=30, slant=0.5)
    lake = cv.ellipse(120, 186, 70, 7)
    cv.ramp(lake, 0.5 + 0.4 * np.sin(cv.X / 6), [BLU, LBL, WHT])
    t = cv.text_mask(text, SERIF, 22, 160, 32, spacing=2, anchor="mm")
    shadow = np.roll(np.roll(t, 2, axis=0), 1, axis=1)
    cv.fill(shadow & ~t, BLK)
    cv.vgrad(t, 22, 42, [WHT, YEL, ORA])
    cv.outline(t | shadow, BLK)


@scene("EINDE_EN", rows=25)
def s_einde_en(cv):
    """Engels eindbeeld: hetzelfde landschap, tekst ASHKARA IS FREE."""
    s_einde(cv, text="ASHKARA IS FREE")


@scene("HANDELSPOST")
def s_handelspost(cv):
    """Zoutvlakte van Mer: wit gebarsten zout, gestreepte kramen, zoutpilaren, kisten."""
    sky(cv, cv.all(), 0, 60, [BLU, LBL, LBL, LGR, WHT], glow=(70, 20, 80, 0.3))
    sun(cv, 70, 18, 7, ramp=(YEL, WHT, WHT))
    mesa(cv, 180, 250, 46, 60, seed=301, ramp=[PUR, LRD, LGR], light_left=False)
    mesa(cv, 262, 318, 50, 60, seed=302, ramp=[PUR, LRD, LGR], light_left=False)
    salt = cv.rect(0, 60, 320, 136)
    n = fbm(cv.h, 160, 12, 303)
    cv.ramp(salt, np.clip(0.55 + 0.35 * n + (cv.Y - 60) / 160, 0, 1), [LGR, LGR, WHT, WHT])
    # zeshoekige barsten in perspectief
    zx = (cv.X - 160) / np.maximum(cv.Y - 52, 1) * 30
    zy = 300 / np.maximum(cv.Y - 52, 1)
    cracks = (np.abs(np.sin(zx * 0.9 + np.sin(zy * 1.7))) < 0.08) | (np.abs(np.sin(zy * 2.2 + zx * 0.3)) < 0.06)
    cv.fill(salt & cracks & (cv.Y > 66), GRY)
    # zoutpilaren
    for x, top, w in ((24, 34, 10), (44, 50, 7), (292, 40, 9)):
        pil = cv.poly([(x - w, 100), (x - w * 0.6, top), (x + w * 0.6, top + 3), (x + w, 100)])
        cv.ramp(pil, np.clip((cv.X - (x - w)) / (2 * w), 0, 1), [GRY, LGR, WHT])
        cv.outline(pil, DGR)
    # kramen met gestreepte luifels
    for x0, x1, base, c1, c2 in ((70, 132, 100, RED, YEL), (150, 214, 96, BLU, WHT), (226, 282, 104, PUR, ORA)):
        roof = cv.poly([(x0 - 6, base - 30), (x1 + 6, base - 30), (x1, base - 22), (x0, base - 22)])
        stripes = ((cv.X - x0) // 8).astype(int) % 2 == 0
        cv.fill(roof & stripes, c1); cv.fill(roof & ~stripes, c2)
        cv.outline(roof, BLK)
        for px in (x0 + 2, x1 - 4):
            cv.fill(cv.rect(px, base - 22, px + 2, base), BRN)
        table = cv.rect(x0 + 4, base - 10, x1 - 4, base - 6)
        cv.ramp(table, 0.5, [BRN, ORA])
        r = np.random.default_rng(int(x0))
        for _ in range(5):
            gx = r.uniform(x0 + 8, x1 - 10)
            cv.fill(cv.rect(gx, base - 14, gx + 5, base - 10), r.choice([CYN, YEL, GRN, LRD, WHT]))
        cv.fill(cv.rect(x0 + 4, base - 6, x1 - 4, base - 5), BLK)
    # kisten op de voorgrond
    for x, y in ((40, 116), (58, 120), (250, 118)):
        box = cv.rect(x, y, x + 16, y + 10)
        cv.ramp(box, 0.5, [BRN, ORA, YEL])
        cv.outline(box, BLK)
        cv.fill(cv.rect(x, y + 4, x + 16, y + 5), BRN)
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


@scene("CITADEL")
def s_citadel(cv):
    """De Citadel van Kasimir Vorr: rotsmassief, centrale toren, schilddome, zoeklichten."""
    sky(cv, cv.all(), 0, 100, [BLK, BLK, BLU, PUR, RED, LRD], curve=1.1, glow=(160, 96, 140, 0.3))
    cv.stars(cv.Y < 50, 60, seed=401, colors=(WHT, LGR, LBL))
    for x0, ang in ((96, -0.55), (232, 0.5), (160, 0.08)):
        beam = cv.poly([(x0, 50), (x0 + 5, 50), (x0 + 5 + 150 * ang + 10, -10), (x0 + 150 * ang - 10, -10)])
        cv.fill(beam & (cv.bx < 0.3), LGR)
    rock = cv.poly([(0, 136), (0, 112), (50, 100), (96, 78), (124, 66), (200, 64), (232, 80), (280, 98), (320, 104), (320, 136)])
    rock_wall(cv, rock, 402, ramp=[BLK, BLK, DGR, GRY], light_left=False)
    walls = cv.rect(92, 52, 236, 74)
    for tx, tw, th in ((88, 16, 40), (226, 16, 42), (118, 12, 48), (202, 12, 46)):
        walls |= cv.rect(tx, th, tx + tw, 74)
        for cx in range(int(tx), int(tx + tw), 5):
            walls |= cv.rect(cx, th - 3, cx + 3, th)
    tower = cv.poly([(146, 74), (150, 14), (156, 6), (164, 6), (170, 14), (174, 74)])
    cv.fill(walls | tower, BLK)
    cv.fill((walls | tower) & ~np.roll(walls | tower, 1, axis=1) & (cv.Y > 4), DGR)
    cv.fill(cv.rect(156, 2, 164, 7), RED)
    r = np.random.default_rng(403)
    for _ in range(40):
        x = r.uniform(92, 236); y = r.uniform(12, 72)
        if cv.px[int(y), int(x / 2)] == BLK and (walls | tower)[int(y), int(x / 2)]:
            cv.fill(cv.rect(x, y, x + 2, y + 2), r.choice([YEL, ORA, LBL]))
    # schilddome: gestippelde boog
    d = np.sqrt(((cv.X - 162) / 104) ** 2 + ((cv.Y - 80) / 82) ** 2)
    dome = (d > 0.93) & (d < 1.0) & (cv.Y < 80)
    cv.fill(dome & (cv.bx < 0.55), CYN)
    inner = (d < 0.93) & (cv.Y < 80) & (cv.px != BLK) & (cv.bx < 0.12)
    cv.fill(inner, LBL)
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


@scene("KAMP")
def s_kamp(cv):
    """Een open Kethari-kamp bij schemering: koepeltenten van huiden, kampvuur, rotswand."""
    sky(cv, cv.all(), 0, 80, [BLU, PUR, RED, LRD, ORA, YEL], glow=(250, 70, 90, 0.4))
    sun(cv, 250, 74, 12, ramp=(ORA, YEL, WHT))
    cliff = cv.poly([(0, 136), (0, 20), (30, 14), (60, 30), (74, 60), (90, 90), (100, 136)])
    rock_wall(cv, cliff, 501, ramp=[BLK, BRN, RED, LRD], light_left=False)
    ground = cv.poly([(0, 136), (0, 94), (120, 88), (320, 92), (320, 136)])
    n = fbm(cv.h, 160, 10, 502)
    cv.ramp(ground & ~cliff, np.clip(0.3 + 0.5 * n, 0, 1), [BRN, ORA, ORA, YEL])
    for cx, base, rx, ry, col in ((132, 104, 34, 26, [BLK, BRN, ORA, LRD]), (204, 98, 26, 20, [BLK, BRN, RED, LRD]),
                                  (272, 108, 30, 24, [BLK, BRN, ORA, YEL])):
        tent = cv.ellipse(cx, base, rx, ry) & (cv.Y < base)
        cv.ramp(tent, np.clip(0.2 + 0.7 * (cv.X - (cx - rx)) / (2 * rx) - (cv.Y - base + ry) * 0.004, 0, 1), col)
        seams = tent & (np.abs(((cv.X - cx) / rx) * 3 - np.round(((cv.X - cx) / rx) * 3)) < 0.08)
        cv.fill(seams, BRN)
        cv.outline(tent, BLK)
        cv.fill(cv.poly([(cx - 6, base), (cx, base - ry * 0.55), (cx + 6, base)]), BLK)
    # kampvuur met rook
    cv.fill(cv.rect(176, 122, 196, 125), BRN)
    flame = cv.poly([(178, 122), (183, 108), (186, 114), (190, 104), (194, 122)])
    cv.ramp(flame, np.clip((122 - cv.Y) / 18, 0, 1), [RED, ORA, YEL, WHT])
    smoke = cv.ellipse(190, 84, 10, 14) | cv.ellipse(196, 64, 12, 12) | cv.ellipse(206, 46, 14, 10)
    cv.fill(smoke & (cv.bx < 0.35), GRY)
    glow = cv.ellipse(186, 124, 40, 8) & ~flame
    cv.fill(glow & (cv.bx < 0.4) & (cv.px != BLK), YEL)
    cv.fill(cv.rect(0, 134, 320, 136), BLK)


# ---------------------------------------------------------------- build
def build(name):
    fn, rows = SCENES[name]
    cv = Canvas(h=rows * 8)
    fn(cv)
    os.makedirs(f"{ROOT}/art/koala", exist_ok=True)
    os.makedirs(f"{ROOT}/assets", exist_ok=True)
    os.makedirs(f"{ROOT}/preview", exist_ok=True)
    cv.save_png(f"{ROOT}/art/{name}.png")
    bm, sc, co, fixed = G.convert_mc(cv.px, maxc=MAXC.get(name, 3))
    assert np.array_equal(G.decode_mc(bm, sc, co, rows), fixed)
    n = G.write_scn(f"{ROOT}/assets/{name.lower()}.scn", bm, sc, co, rows)
    G.write_koala(f"{ROOT}/art/koala/{name.lower()}.kla", bm, sc, co, rows)
    G.render_rgb(fixed).save(f"{ROOT}/preview/{name}.png")
    changed = int((fixed != cv.px).sum())
    print(f"{name:10s} rows={rows} disk={n:5d} B  pixels gecorrigeerd door celregels: {changed}")
    return fixed


if __name__ == "__main__":
    names = sys.argv[1:] or list(SCENES)
    for n in names:
        build(n)
