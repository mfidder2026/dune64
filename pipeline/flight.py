#!/usr/bin/env python3
"""
flight.py - de vluchtscène (DESIGN.md §4.2): uitzicht uit de cockpit van de glider over de
woestijn, geanimeerd met kleurcycli in plaats van het bitmap opnieuw te tekenen.

Hoe het werkt: elke pixel van de grond hoort bij een "duinband" b op perspectivische afstand.
Pixel-slot = 1 + (b mod 3) (multicolor %01/%10/%11). Per tekenrij kiest de engine drie kleuren
(scherm-RAM hoog/laag + kleur-RAM). Wie de drie kleuren elke tick een plaats doordraait, ziet
de banden naar zich toe schuiven: kleur(b, t) = palet[(b + t) mod 3]. Per tick 800 bytes
memset, geen bitmapwerk. Lucht, horizon en dashboard staan stil; nacht = andere paletten.

Uitvoer: assets/vlucht.scn, src/flight_tab.h (rijpaletten dag/nacht), preview/VLUCHT*.png
"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import c64gfx as G
from c64art import BLK, WHT, RED, CYN, PUR, GRN, BLU, YEL, ORA, BRN, LRD, DGR, GRY, LGN, LBL, LGR

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
W, H, ROWS = 160, 136, 17
HORIZON = 40                  # pixelrij; rij 5 begint hier
GROUND_ROWS = (5, 15)         # tekenrijen die cyclen (5..14)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0

# per rij drie kleuren voor slot 1, 2, 3 (scherm hoog, scherm laag, kleur-RAM)
SKY_DAY = [BLU, LBL, LGR, WHT]                    # boven -> horizon
SKY_NIGHT = [BLK, BLU, BLU, PUR]
GROUND_DAY = {5: (YEL, LRD, YEL), 6: (ORA, LRD, YEL), 7: (ORA, LRD, YEL), 8: (ORA, LRD, YEL),
              9: (BRN, ORA, YEL), 10: (BRN, ORA, YEL), 11: (BRN, ORA, YEL), 12: (BRN, ORA, YEL),
              13: (BRN, ORA, YEL), 14: (BRN, ORA, YEL)}
GROUND_NIGHT = {5: (BLU, PUR, BLU), 6: (BLK, BLU, PUR), 7: (BLK, BLU, PUR), 8: (BLK, BLU, PUR),
                9: (BLK, BLU, LBL), 10: (BLK, BLU, LBL), 11: (BLK, BLU, LBL), 12: (BLK, BLU, LBL),
                13: (BLK, BLU, LBL), 14: (BLK, BLU, LBL)}
DASH = {15: (RED, GRN, YEL), 16: (DGR, GRY, LGR)}


def sky_rows(ramp):
    """Per luchtrij: (slots voor die 8 pixelrijen, palet van 3 kleuren)."""
    out = {}
    ys, xs = np.mgrid[0:HORIZON, 0:W]
    pos = ys / (HORIZON - 1) * (len(ramp) - 1) + (BAYER[ys % 4, xs % 4] - 0.5) * 0.9
    idx = np.clip(np.round(pos), 0, len(ramp) - 1).astype(int)
    for r in range(HORIZON // 8):
        block = idx[r * 8:(r + 1) * 8]
        used = sorted(set(block.ravel().tolist()))
        while len(used) < 3: used.append(used[-1])
        pal = [ramp[i] for i in used[:3]]
        slots = np.zeros_like(block)
        for s, i in enumerate(used[:3]):
            slots[block == i] = s + 1
        out[r] = (slots, pal)
    return out


def build_slots():
    S = np.zeros((H, W), np.uint8)
    sky = sky_rows(SKY_DAY)
    for r, (slots, _) in sky.items():
        S[r * 8:(r + 1) * 8] = slots
    # grond: duinbanden in perspectief, golvend in de breedte
    ys, xs = np.mgrid[HORIZON:120, 0:W]
    d = (ys - HORIZON) + 3.0
    z = 260.0 / d                                  # afstand
    xw = (xs - 80) * z / 40.0                      # wereld-x
    u = z + 1.3 * np.sin(xw * 0.45 + z * 0.3) + 0.45 * np.sin(xw * 1.2 - z * 0.7)
    S[HORIZON:120] = 1 + (np.floor(u).astype(int) % 3)
    # tafelbergen aan de horizon (zwart = achtergrond, staat stil)
    xx = np.arange(W)
    mesa = np.zeros(W)
    for cx, w, h in ((22, 16, 7), (40, 7, 4), (112, 22, 9), (140, 9, 5)):
        mesa = np.maximum(mesa, np.where(abs(xx - cx) < w, h - np.maximum(0, abs(xx - cx) - w + 3), 0))
    for x in range(W):
        S[HORIZON - int(mesa[x]):HORIZON, x] = 0
    # cockpit: dakbalk, schuine stijlen, middenstijl boven
    yy, xx2 = np.mgrid[0:H, 0:W]
    left = 16 - yy * 0.10                          # stijlen lopen naar boven toe naar binnen
    S[(xx2 < left) | (xx2 > W - 1 - left)] = 0
    S[(yy < 5)] = 0
    S[(yy < 18) & (abs(xx2 - 79.5) < 2)] = 0
    # dashboard (rij 14 deels, 15-16): zwart met wijzerplaten
    top = 116 + ((xx2 - 80) / 80.0) ** 2 * 8
    S[yy >= top] = 0
    for cx in (52, 80, 108):
        r2 = (xx2 - cx) ** 2 * 4 + (yy - 127) ** 2
        S[(r2 < 30) & (r2 >= 18)] = 3              # rand van de wijzer (geel / lichtgrijs)
        S[(r2 < 18) & (abs((xx2 - cx) * 2 - (yy - 127) * 0.6) < 1.2)] = 1   # naald
    S[(abs(yy - 121) < 1) & (abs(xx2 - 80) < 30) & (xx2 % 4 == 0)] = 2   # lampjes
    S[134:] = 0                                    # onderste 2 pixelrijen zwart (split)
    return S


def row_palettes(night):
    sky = sky_rows(SKY_NIGHT if night else SKY_DAY)
    ground = GROUND_NIGHT if night else GROUND_DAY
    pals = []
    for r in range(ROWS):
        if r in sky: pals.append(tuple(sky[r][1]))
        elif r in ground: pals.append(ground[r])
        else: pals.append(DASH.get(r, (BLK, BLK, BLK)))
    return pals


def encode(S):
    """slots -> bitmap (cel-volgorde), plus lege scherm/kleur-RAM (de engine vult ze)."""
    bm = bytearray()
    for cy in range(ROWS):
        for cx in range(40):
            for y in range(8):
                px = S[cy * 8 + y, cx * 4:cx * 4 + 4]
                bm.append(int(px[0]) << 6 | int(px[1]) << 4 | int(px[2]) << 2 | int(px[3]))
    return bytes(bm)


def render(S, pals, t):
    """Wat de C64 toont bij cyclus-stap t (alleen de grondrijen draaien)."""
    img = np.zeros((H, W), np.uint8)
    for r in range(ROWS):
        pal = pals[r]
        rot = t if GROUND_ROWS[0] <= r < GROUND_ROWS[1] else 0
        for s in (1, 2, 3):
            c = pal[(s - 1 + rot) % 3]
            blk = S[r * 8:(r + 1) * 8]
            img[r * 8:(r + 1) * 8][blk == s] = c
    return img


def main():
    S = build_slots()
    day, night = row_palettes(False), row_palettes(True)
    bm = encode(S)
    sc = bytes(((p[0] << 4) | p[1]) for p in day for _ in range(40))
    co = bytes(p[2] for p in day for _ in range(40))
    os.makedirs(f"{ROOT}/assets", exist_ok=True); os.makedirs(f"{ROOT}/preview", exist_ok=True)
    n = G.write_scn(f"{ROOT}/assets/vlucht.scn", bm, sc, co, ROWS)
    frames = [render(S, day, t) for t in range(3)] + [render(S, night, 0)]
    strip = np.hstack([np.pad(f, ((0, 0), (0, 4))) for f in frames])
    G.render_rgb(strip).save(f"{ROOT}/preview/VLUCHT.png")
    gif = [Image.fromarray(G.PALETTE[np.repeat(f, 2, axis=1)].astype(np.uint8)).resize((640, 272), Image.NEAREST)
           for f in frames[:3]] * 4
    gif[0].save(f"{ROOT}/preview/VLUCHT.gif", save_all=True, append_images=gif[1:], duration=60, loop=0)
    with open(f"{ROOT}/src/flight_tab.h", "w") as f:
        f.write("/* gegenereerd door pipeline/flight.py - niet met de hand wijzigen */\n")
        f.write(f"#define FL_GROUND_FIRST {GROUND_ROWS[0]}\n#define FL_GROUND_END {GROUND_ROWS[1]}\n")
        for name, pals in (("fl_day", day), ("fl_night", night)):
            rows = ", ".join("{ %d, %d, %d }" % p for p in pals)
            f.write(f"static const unsigned char {name}[{ROWS}][3] = {{ {rows} }};\n")
    print(f"vlucht.scn: {n} bytes; preview/VLUCHT.png, preview/VLUCHT.gif, src/flight_tab.h")


if __name__ == "__main__":
    main()
