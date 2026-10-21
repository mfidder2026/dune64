#!/usr/bin/env python3
"""
characters.py - originele personages als borstbeeld, gecomponeerd in hun thuisscène.
Per personage ontstaat een patchset (.PAT): [lichaam, mond_dicht, mond_half, mond_open].
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from c64art import *
import c64gfx as G
import scenes as S

ROOT = S.ROOT
CHARS = {}


def char(name, scene):
    def deco(fn):
        CHARS[name] = (fn, scene)
        return fn
    return deco


def bust(cv, cx, cy, rx, ry, skin, robe, shoulder=2.5, robe_light=-1, outline=True, neck=True):
    """Romp met ronde schouders + nek + hoofd. Retourneert (head_mask, body_mask)."""
    top = cy + ry * 0.92
    sw = rx * shoulder
    dome = cv.ellipse(cx, top + ry * 0.75, sw, ry * 0.85) & (cv.Y < top + ry * 0.75)
    trunk = cv.rect(cx - sw, top + ry * 0.75, cx + sw, cv.h + 2)
    body = dome | trunk
    t = (cv.X - (cx - sw)) / (2 * sw)
    val = (0.85 - 0.55 * t) if robe_light < 0 else (0.3 + 0.55 * t)
    val = val + 0.10 * np.sin((cv.X - cx) / 11.0 + np.sin(cv.Y / 25.0)) * (cv.Y > top + ry * 0.6)
    dy = np.clip((cv.Y - top) / (ry * 0.8), 0, 1)
    val = val + 0.12 * (1 - dy)   # schouders vangen licht
    cv.ramp(body, np.clip(val, 0, 1), robe)
    for s in (-1, 1):   # armplooi
        crease = cv.line([(cx + s * sw * 0.66, top + ry * 0.75), (cx + s * sw * 0.72, cv.h)], 1) & body
        cv.fill(crease, robe[0])
    if neck:
        nk = cv.rect(cx - rx * 0.45, cy + ry * 0.5, cx + rx * 0.45, top + ry * 0.2)
        cv.ramp(nk, np.clip(0.4 - (cv.X - cx) / (rx * 2.5), 0, 1), skin)
        cv.fill(cv.rect(cx - rx * 0.45, top + ry * 0.05, cx + rx * 0.45, top + ry * 0.2) & nk, skin[0])
    hm = S.head(cv, cx, cy, rx, ry, skin)
    if outline:
        cv.outline(body | hm | (cv.rect(cx - rx * 0.45, cy, cx + rx * 0.45, top + 4)), BLK)
    return hm, body


def eyes(cv, cx, cy, rx, ry, white, iris=BLK, brow=BLK, shadow=BRN, ey=-0.02, gap=0.40, frown=0, look=0.5):
    y = cy + ry * ey
    for s in (-1, 1):
        ex = cx + s * rx * gap
        ew = rx * 0.26
        cv.fill(cv.ellipse(ex, y, ew, 2.2), white)
        ix = ex + look
        cv.fill(cv.rect(ix - 2, y - 2, ix + 2, y + 2), iris)
        cv.fill(cv.rect(ex - ew, y - 3.2, ex + ew, y - 2.0), shadow)      # ooglid
        cv.fill(cv.rect(ex - ew * 0.8, y + 2.2, ex + ew * 0.8, y + 3.0), shadow)  # wal
        f = frown * s
        cv.fill(cv.line([(ex - ew * 1.2, y - 6 - f), (ex + ew * 1.2, y - 6 + f)], 2), brow)


def nose_mouth(cv, cx, cy, rx, ry, shadow, mouth_col, mouth=0, mw=0.3):
    ny = cy + ry * 0.33
    cv.fill(cv.line([(cx + 2, cy + ry * 0.05), (cx + 4, ny), (cx, ny + 1.5)], 2), shadow)
    cv.fill(cv.rect(cx - 3, ny + 1, cx + 1, ny + 2), shadow)
    my = cy + ry * 0.58
    if mouth == 0:
        cv.fill(cv.rect(cx - rx * mw, my, cx + rx * mw, my + 1.2), mouth_col)
    elif mouth == 1:
        cv.fill(cv.ellipse(cx, my + 0.5, rx * mw * 0.9, 1.6), BLK)
    else:
        cv.fill(cv.ellipse(cx, my + 1.2, rx * mw * 0.85, 3.0), BLK)
        cv.fill(cv.rect(cx - rx * mw * 0.5, my - 0.5, cx + rx * mw * 0.5, my + 0.6), mouth_col)


def mouth_rect(cx, cy, rx, ry):
    return (cx - rx * 0.45, cy + ry * 0.45, cx + rx * 0.45, cy + ry * 0.85)


# ------------------------------------------------------------------ personages
@char("DORAN", "RAADZAAL")
def c_doran(cv, mouth=0):
    """Maarschalk Doran Keyl - wapenmeester, grijs, litteken, blauw uniform met goud."""
    cx, cy, rx, ry = 244, 46, 20, 26
    skin = [BRN, LRD, LGR]
    hm, body = bust(cv, cx, cy, rx, ry, skin, [BLK, BLU, LBL], shoulder=2.7)
    # schouderstukken en kraag
    top = cy + ry * 0.92; sw = rx * 2.7
    for s in (-1, 1):
        ep = cv.poly([(cx + s * rx * 1.0, top + ry * 0.12), (cx + s * sw * 0.78, top + ry * 0.38),
                      (cx + s * sw * 0.9, top + ry * 0.62), (cx + s * rx * 1.1, top + ry * 0.42)])
        cv.ramp(ep, 0.75 if s < 0 else 0.4, [BRN, ORA, YEL])
        cv.outline(ep, BLK)
        for k in range(4):
            fx = cx + s * (sw * 0.55 + k * 4)
            cv.fill(cv.rect(fx, top + ry * 0.5 + k * 1.5, fx + 1.5, top + ry * 0.5 + k * 1.5 + 5), YEL)
    cv.fill(cv.poly([(cx - 8, cy + ry * 0.85), (cx, cy + ry * 1.45), (cx + 8, cy + ry * 0.85)]), BLK)
    for k in range(3):
        cv.fill(cv.rect(cx - 2, cy + ry * 1.6 + k * 9, cx + 2, cy + ry * 1.6 + k * 9 + 3), YEL)
    # kort grijs haar
    hair = cv.ellipse(cx, cy - ry * 0.45, rx * 1.02, ry * 0.62) & (cv.Y < cy - ry * 0.32) & hm
    cv.ramp(hair, np.clip(0.8 - (cv.X - cx + rx) / (2 * rx) * 0.6, 0, 1), [BRN, LGR, LGR])
    side = hm & (cv.Y < cy + ry * 0.05) & (np.abs(cv.X - cx) > rx * 0.82)
    cv.fill(side, LGR)
    eyes(cv, cx, cy, rx, ry, white=LRD, shadow=BRN, frown=1)
    # litteken
    cv.fill(cv.line([(cx + rx * 0.25, cy - ry * 0.25), (cx + rx * 0.6, cy + ry * 0.35)], 1), BRN)
    # snor
    nose_mouth(cv, cx, cy, rx, ry, BRN, BRN, mouth)
    cv.fill(cv.rect(cx - rx * 0.4, cy + ry * 0.46, cx + rx * 0.4, cy + ry * 0.52), LGR)


@char("VESNA", "BALKON")
def c_vesna(cv, mouth=0):
    """Vesna Adair - raadsvrouw en spionnenmeester; donker haar in een knot, paarse gewaden."""
    cx, cy, rx, ry = 78, 46, 18, 25
    skin = [BRN, ORA, LRD]
    # knot achter het hoofd
    bun = cv.ellipse(cx + rx * 0.9, cy - ry * 0.75, rx * 0.6, ry * 0.4)
    cv.ramp(bun, 0.4, [BLK, BRN])
    hm, body = bust(cv, cx, cy, rx, ry, skin, [BLK, PUR, LRD], shoulder=2.3, robe_light=1)
    # hoge kraag
    collar = cv.poly([(cx - rx * 1.1, cy + ry * 0.7), (cx - rx * 0.5, cy + ry * 1.25), (cx + rx * 0.5, cy + ry * 1.25),
                      (cx + rx * 1.1, cy + ry * 0.7), (cx + rx * 1.25, cy + ry * 1.45), (cx - rx * 1.25, cy + ry * 1.45)])
    cv.ramp(collar, 0.55, [BLK, PUR, LRD])
    cv.outline(collar, BLK)
    # haar strak naar achteren
    hair = hm & (cv.Y < cy - ry * 0.3 + 0.18 * (cv.X - cx))
    cv.ramp(hair, np.clip(0.3 + 0.3 * np.sin(cv.X * 0.7), 0, 1), [BLK, BRN])
    cv.fill(hm & (cv.X > cx + rx * 0.72) & (cv.Y < cy + ry * 0.3), BLK)
    eyes(cv, cx, cy, rx, ry, white=LRD, shadow=BRN, gap=0.4, frown=-1)
    nose_mouth(cv, cx, cy, rx, ry, BRN, BRN, mouth, mw=0.25)
    # hanger
    cv.fill(cv.ellipse(cx, cy + ry * 1.75, 3, 3), YEL)


@char("VORR", "COMMS")
def c_vorr(cv, mouth=0):
    """Gouverneur Kasimir Vorr van het Consortium - verschijnt als hologram op het scherm."""
    cx, cy, rx, ry = 160, 38, 16, 19
    scr = cv.rect(96, 16, 224, 78)
    sub = Canvas(cv.h); sub.px[:] = cv.px
    skin = [BLK, BLU, LBL, CYN]
    hm, body = bust(sub, cx, cy, rx, ry, skin, [BLK, BLK, BLU], shoulder=2.6)
    # hoge kraag met punten
    for s in (-1, 1):
        cv_ = sub
        spike = cv_.poly([(cx + s * rx * 0.6, cy + ry * 0.75), (cx + s * rx * 2.0, cy + ry * 0.2), (cx + s * rx * 1.6, cy + ry * 1.3)])
        cv_.fill(spike, BLU); cv_.outline(spike, BLK)
    eyes(sub, cx, cy, rx, ry, white=CYN, iris=BLK, brow=BLK, shadow=BLU, frown=2)
    nose_mouth(sub, cx, cy, rx, ry, BLU, BLK, mouth, mw=0.32)
    # zware kaak / plooien
    sub.fill(sub.line([(cx - rx * 0.6, cy + ry * 0.35), (cx - rx * 0.5, cy + ry * 0.7)], 1), BLU)
    sub.fill(sub.line([(cx + rx * 0.6, cy + ry * 0.35), (cx + rx * 0.5, cy + ry * 0.7)], 1), BLU)
    # scanlines
    sl = (np.arange(cv.h)[:, None] % 3 == 0) & (sub.px != BLK)
    sub.px[sl & (sub.px == CYN)] = LBL
    sub.px[sl & (sub.px == LBL)] = BLU
    cv.px[scr] = sub.px[scr]


@char("MARDO", "HANGAR")
def c_mardo(cv, mouth=0):
    """Dr. Ilse Mardo - planetoloog; rossig kort haar, zonnebril op het voorhoofd, lichte jas."""
    cx, cy, rx, ry = 70, 46, 18, 25
    skin = [BRN, ORA, LRD]
    bob = cv.ellipse(cx, cy - ry * 0.05, rx * 1.22, ry * 1.02) & (cv.Y < cy + ry * 0.5)
    cv.ramp(bob, np.clip(0.75 - (cv.X - cx + rx) / (2.4 * rx) * 0.7, 0, 1), [BRN, ORA, ORA])
    cv.outline(bob, BLK)
    hm, body = bust(cv, cx, cy, rx, ry, skin, [BLK, DGR, GRY, LGR], shoulder=2.4)
    cv.fill(bob & ~hm & (cv.Y < cy + ry * 0.5), ORA)
    cv.ramp(bob & ~hm & (cv.X > cx), 0.2, [BRN, ORA])
    # revers
    for s in (-1, 1):
        lap = cv.poly([(cx + s * rx * 0.4, cy + ry * 0.9), (cx + s * rx * 1.2, cy + ry * 1.4), (cx + s * rx * 0.3, cy + ry * 2.4)])
        cv.fill(lap, LGR); cv.outline(lap, BLK)
    cv.fill(cv.poly([(cx - rx * 0.4, cy + ry * 0.9), (cx + rx * 0.4, cy + ry * 0.9), (cx, cy + ry * 1.6)]), ORA)
    hair = hm & (cv.Y < cy - ry * 0.38 + 0.15 * np.abs(cv.X - cx))
    cv.ramp(hair, np.clip(0.75 - (cv.X - cx + rx) / (2 * rx) * 0.6, 0, 1), [BRN, ORA, ORA])
    cv.fill(hm & (np.abs(cv.X - cx) > rx * 0.86) & (cv.Y < cy + ry * 0.3), ORA)
    # zonnebril op het voorhoofd
    for s in (-1, 1):
        g = cv.ellipse(cx + s * rx * 0.45, cy - ry * 0.52, rx * 0.33, 3.2)
        cv.fill(g, BLK)
        cv.fill(cv.ellipse(cx + s * rx * 0.45 - 1, cy - ry * 0.55, rx * 0.18, 1.6), LBL)
    cv.fill(cv.rect(cx - rx * 1.0, cy - ry * 0.56, cx + rx * 1.0, cy - ry * 0.48) & ~hm, BLK)
    eyes(cv, cx, cy, rx, ry, white=LRD, shadow=BRN)
    nose_mouth(cv, cx, cy, rx, ry, BRN, BRN, mouth, mw=0.27)
    # sproeten
    for dx, dy in ((-6, 3), (-3, 4), (5, 3), (8, 4)):
        cv.fill(cv.rect(cx + dx, cy + ry * 0.15 + dy * 0.6, cx + dx + 2, cy + ry * 0.15 + dy * 0.6 + 1), BRN)


@char("SAIRA", "KLOOF")
def c_saira(cv, mouth=0):
    """Saïra - jonge Kethari-verkenner; gezichtsdoek omlaag, stippeltatoeage op de jukbeenderen."""
    cx, cy, rx, ry = 248, 48, 18, 25
    skin = [BRN, ORA, LRD]
    # lang donker haar achter het hoofd
    back = cv.ellipse(cx, cy + ry * 0.3, rx * 1.35, ry * 1.25) & (cv.Y > cy - ry)
    cv.ramp(back, 0.3, [BLK, BRN])
    hm, body = bust(cv, cx, cy, rx, ry, skin, [BLK, BRN, ORA], shoulder=2.3, robe_light=-1)
    # sjaal / gezichtsdoek om de hals
    scarf = cv.ellipse(cx, cy + ry * 1.0, rx * 1.05, ry * 0.26) | cv.poly([(cx - rx * 0.9, cy + ry * 1.05), (cx - rx * 0.3, cy + ry * 1.1), (cx - rx * 1.4, cy + ry * 2.2), (cx - rx * 1.9, cy + ry * 2.0)])
    cv.ramp(scarf, np.clip(0.55 + 0.25 * np.sin(cv.X / 5.0 - cv.Y / 3.0), 0, 1), [BRN, ORA, YEL])
    cv.outline(scarf, BLK)
    hair = hm & (cv.Y < cy - ry * 0.28 - 0.25 * (cv.X - cx))
    cv.ramp(hair, 0.35, [BLK, BRN])
    cv.fill(hm & (np.abs(cv.X - cx) > rx * 0.8) & (cv.Y < cy + ry * 0.45), BLK)
    eyes(cv, cx, cy, rx, ry, white=LRD, shadow=BRN, gap=0.42)
    for s in (-1, 1):
        for k in range(3):
            cv.fill(cv.rect(cx + s * rx * (0.3 + k * 0.16), cy + ry * 0.2 + k * 1.2,
                            cx + s * rx * (0.3 + k * 0.16) + 2, cy + ry * 0.2 + k * 1.2 + 1), BLK)
    nose_mouth(cv, cx, cy, rx, ry, BRN, BRN, mouth, mw=0.24)


@char("TARIK", "GROT")
def c_tarik(cv, mouth=0):
    """Tarik Ur-Kesh - leider van de Kethari; kap, volle baard, staf."""
    cx, cy, rx, ry = 172, 46, 20, 26
    skin = [BLK, BRN, ORA]
    # staf
    staff = cv.rect(cx + rx * 2.6, 8, cx + rx * 2.6 + 4, 136)
    cv.ramp(staff, 0.5, [BLK, BRN, ORA]); cv.outline(staff, BLK)
    cv.fill(cv.ellipse(cx + rx * 2.6 + 2, 10, 5, 5), YEL)
    cv.fill(cv.ellipse(cx + rx * 2.6 + 2, 10, 2.5, 2.5), WHT)
    # kap achter het hoofd
    hood = cv.ellipse(cx, cy - 2, rx * 1.55, ry * 1.32)
    cv.ramp(hood, np.clip(0.6 - (cv.X - cx) / (rx * 4), 0, 1), [BLK, RED, LRD])
    hm, body = bust(cv, cx, cy, rx, ry, skin, [BLK, RED, LRD], shoulder=2.8)
    # kap over het voorhoofd
    brim = hm & (cv.Y < cy - ry * 0.42)
    cv.ramp(brim, 0.45, [BLK, RED, LRD])
    cv.outline(hood, BLK)
    eyes(cv, cx, cy, rx, ry, white=ORA, shadow=BLK, frown=1)
    beard = cv.ellipse(cx, cy + ry * 0.62, rx * 0.98, ry * 0.62) & (cv.Y > cy + ry * 0.3)
    cv.ramp(beard, np.clip(0.3 + 0.25 * np.sin(cv.X * 1.1 + cv.Y * 0.5), 0, 1), [BLK, BRN])
    nose_mouth(cv, cx, cy, rx, ry, BLK, BLK, mouth, mw=0.28)
    # tatoeagelijn op het voorhoofd
    cv.fill(cv.rect(cx - 1, cy - ry * 0.32, cx + 1, cy - ry * 0.12), ORA)


# ------------------------------------------------------------------ build
def render_scene(name):
    fn, rows = S.SCENES[name]
    cv = Canvas(rows * 8); fn(cv); return cv


def union_rect(rects):
    rects = [r for r in rects if r]
    x0 = min(r[0] for r in rects); y0 = min(r[1] for r in rects)
    x1 = max(r[0] + r[2] for r in rects); y1 = max(r[1] + r[3] for r in rects)
    return (x0, y0, x1 - x0, y1 - y0)


def build_char(name):
    fn, scene = CHARS[name]
    base = render_scene(scene)
    base_conv = G.convert_mc(base.px)
    frames = []
    for m in (0, 1, 2):
        cv = render_scene(scene); fn(cv, mouth=m)
        frames.append((cv, G.convert_mc(cv.px)))
    body_rect = G.cell_rect_diff(base_conv[3], frames[0][1][3])
    mrect = union_rect([G.cell_rect_diff(frames[0][1][3], f[1][3]) for f in frames[1:]])
    patches = [G.patch_bytes(frames[0][1][:3], body_rect)] + [G.patch_bytes(f[1][:3], mrect) for f in frames]
    n = G.write_pat(f"{ROOT}/assets/{name.lower()}.pat", patches)
    frames[0][0].save_png(f"{ROOT}/art/{scene}+{name}.png")
    G.render_rgb(frames[0][1][3]).save(f"{ROOT}/preview/{scene}+{name}.png")
    G.render_rgb(frames[2][1][3]).save(f"{ROOT}/preview/{scene}+{name}_praat.png")
    print(f"{name:6s} in {scene:9s} lichaam={body_rect} mond={mrect} disk={n} B")
    return body_rect, mrect


if __name__ == "__main__":
    for n in (sys.argv[1:] or list(CHARS)):
        build_char(n)
