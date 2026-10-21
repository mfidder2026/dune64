#!/usr/bin/env python3
"""
ui.py - UI-charset, globe-sprite en complete schermmockups voor ASHKARA.

Charset-indeling (screen codes, compatibel met de C64 'kleine letters'-set):
    0       '@'        1-26  a-z      27-31 [ £ ] ^ _
    32-63   spatie ! " # ... 0-9 : ; < = > ?
    64      '`'        65-90 A-Z      91-95 { | } ~ (vrij)
    96-127  UI-kader en iconen (multicolor; kleur-RAM >= 8)
    128-255 vrij (reserve: extra iconen, accenten)
Tekst (hires) gebruikt kleur-RAM 0-7, kader-tekens kleur-RAM 8+7 (=geel als %11).
Multicolor-registers voor het paneel: $D021=zwart, $D022=bruin(9), $D023=oranje(8).
"""
import os, re, sys, struct
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import c64gfx as G
from c64art import *

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D022, D023 = BRN, ORA


def load_font8x8():
    src = open(os.path.join(os.path.dirname(__file__), "third_party", "font8x8_basic.h")).read()
    rows = re.findall(r"\{\s*((?:0x[0-9A-Fa-f]{2}\s*,\s*){7}0x[0-9A-Fa-f]{2})\s*\}", src)
    font = []
    for r in rows[:128]:
        bs = [int(x, 16) for x in r.split(",")]
        font.append([int(f"{b:08b}"[::-1], 2) for b in bs])  # LSB-links -> MSB-links
    return font


# --- multicolor kadertekens (4x8 fat pixels, waarden 0..3) ---
def mc(rows):
    return [int("".join(f"{int(c):02b}" for c in r), 2) for r in rows]

FRAME = {
    "H":   mc(["0000", "1111", "3333", "2222", "1111", "0000", "0000", "0000"]),
    "HB":  mc(["0000", "0000", "0000", "1111", "2222", "3333", "1111", "0000"]),
    "VL":  mc(["0132"] * 8),
    "VR":  mc(["2310"] * 8),
    "VD":  mc(["0120"] * 8),
    "TL":  mc(["0000", "0111", "0133", "0132", "0131", "0132", "0132", "0132"]),
    "TR":  mc(["0000", "1110", "3310", "2310", "1310", "2310", "2310", "2310"]),
    "BL":  mc(["0132", "0132", "0132", "0131", "0132", "0133", "0111", "0000"]),
    "BR":  mc(["2310", "2310", "2310", "1310", "2310", "3310", "1110", "0000"]),
    "TD":  mc(["0000", "1111", "3333", "2222", "1221", "0120", "0120", "0120"]),
    "BD":  mc(["0120", "0120", "0120", "1221", "2222", "3333", "1111", "0000"]),
    "ORN_L": mc(["0000", "1112", "3323", "2233", "1123", "0012", "0001", "0000"]),
    # bovenste pixelrij leeg: de raster-split schakelt pas rond die lijn naar tekstmodus, dus
    # pixels daar knipperen (DESIGN.md §6). Alle tekens op paneelrij 17 houden rij 0 leeg.
    "ORN_M": mc(["0000", "0330", "2332", "3223", "3113", "3223", "2332", "1331"]),
    "ORN_R": mc(["0000", "2111", "3233", "3322", "3211", "2100", "1000", "0000"]),
    # iconen (multicolor)
    "SUN":   mc(["0000", "0330", "3223", "3223", "0330", "0000", "0000", "0000"]),
    "MOON":  mc(["0000", "0330", "3300", "3300", "0330", "0000", "0000", "0000"]),
    "AMBER": mc(["0030", "0323", "3223", "2332", "2112", "0210", "0000", "0000"]),
    "SWORD": mc(["0003", "0030", "0300", "2200", "1200", "0000", "0000", "0000"]),
    "LEAF":  mc(["0003", "0033", "0323", "0330", "1100", "1000", "0000", "0000"]),
}
FRAME_CODES = {k: 96 + i for i, k in enumerate(FRAME)}
CURSOR = 0x3E  # '>'

# hires-tekens na het kader (115+): paginerings-pijl en accenten (DESIGN.md §5.3)
HIRES_CODES = {"MORE": 115, "E_UML": 116, "I_UML": 117, "E_ACU": 118}
ACCENTS = {"ë": "E_UML", "ï": "I_UML", "é": "E_ACU"}   # ë ï é -> screen code


def accent(base, top):
    """Kleine letter met eigen bovenste twee rijen (font8x8 laat die leeg voor a-z)."""
    g = list(base)
    g[0], g[1] = top
    return g


def build_charset():
    font = load_font8x8()
    cs = [[0] * 8 for _ in range(256)]
    cs[0] = font[ord("@")]
    for i, ch in enumerate("abcdefghijklmnopqrstuvwxyz"):
        cs[1 + i] = font[ord(ch)]
    for code in range(32, 64):
        cs[code] = font[code]
    for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        cs[65 + i] = font[ord(ch)]
    for k, code in FRAME_CODES.items():
        cs[code] = FRAME[k]
    H = HIRES_CODES
    cs[H["MORE"]] = [0x00, 0x00, 0x7E, 0x3C, 0x18, 0x00, 0x00, 0x00]
    cs[H["E_UML"]] = accent(font[ord("e")], (0x48, 0x00))
    cs[H["I_UML"]] = accent(font[ord("i")], (0x48, 0x00))
    cs[H["E_ACU"]] = accent(font[ord("e")], (0x18, 0x30))
    return cs


def scr(s):
    """ASCII -> screen codes van deze charset."""
    out = []
    for ch in s:
        o = ord(ch)
        if "a" <= ch <= "z": out.append(o - 96)
        elif "A" <= ch <= "Z": out.append(o - 0)
        elif ch == "@": out.append(0)
        elif 32 <= o < 64: out.append(o)
        elif ch in ACCENTS: out.append(HIRES_CODES[ACCENTS[ch]])
        else: out.append(32)
    return out


# --- paneel opbouwen: 8 rijen x 40 kolommen ---
TEXT_COL0, TEXT_W = 1, 26
SPRITE_X, SPRITE_Y = 284, 136 + 2 * 8 + 1   # schermpixel (zonder rand); VIC: x+24, y+50
STAT_COL0 = 28


def panel(lines, status, title=None):
    """lines: lijst van (tekst, kleur) max 6; status: dict(dag, amber, krijgers, groen, nacht)."""
    chars = np.full((8, 40), 32, np.uint8)
    cols = np.full((8, 40), 1, np.uint8)
    F = FRAME_CODES; GOLD = 8 + YEL
    def put(r, c, code, col=GOLD): chars[r, c] = code; cols[r, c] = col
    for c in range(40):
        put(0, c, F["H"]); put(7, c, F["HB"])
    put(0, 0, F["TL"]); put(0, 39, F["TR"]); put(7, 0, F["BL"]); put(7, 39, F["BR"])
    for r in range(1, 7):
        put(r, 0, F["VL"]); put(r, 39, F["VR"]); put(r, 27, F["VD"])
    put(0, 27, F["TD"]); put(7, 27, F["BD"])
    put(0, 12, F["ORN_L"]); put(0, 13, F["ORN_M"]); put(0, 14, F["ORN_R"])
    for i, (txt, col) in enumerate(lines[:6]):
        codes = scr(txt[:TEXT_W])
        chars[1 + i, TEXT_COL0:TEXT_COL0 + len(codes)] = codes
        cols[1 + i, TEXT_COL0:TEXT_COL0 + TEXT_W] = col
    # status
    icon = F["MOON"] if status.get("nacht") else F["SUN"]
    rows = [(icon, f"DAG{status['dag']:3d}", YEL), (F["AMBER"], f"{status['amber']:5d}", YEL),
            (F["SWORD"], f"{status['krijgers']:5d}", WHT), (F["LEAF"], f"{status.get('groen', 0):4d}%", GRN)]
    for i, (ic, txt, col) in enumerate(rows):
        put(1 + i, STAT_COL0, ic)
        codes = scr(txt)
        chars[1 + i, STAT_COL0 + 1:STAT_COL0 + 1 + len(codes)] = codes
        cols[1 + i, STAT_COL0 + 1:STAT_COL0 + 1 + len(codes)] = col
    return chars, cols


def render_panel(chars, cols, cs):
    """Render 8x40 tekens in multicolor-tekstmodus -> (64,320) RGB-index (hires-resolutie)."""
    R, C = chars.shape
    out = np.zeros((R * 8, C * 8), np.uint8)
    for r in range(R):
        for c in range(C):
            code, col = chars[r, c], cols[r, c]
            g = cs[code]
            for y in range(8):
                b = g[y]
                if col >= 8:
                    pal = [BLK, D022, D023, col & 7]
                    for p in range(4):
                        v = (b >> (6 - 2 * p)) & 3
                        out[r * 8 + y, c * 8 + p * 2:c * 8 + p * 2 + 2] = pal[v]
                else:
                    for p in range(8):
                        out[r * 8 + y, c * 8 + p] = col if (b >> (7 - p)) & 1 else BLK
    return out


# --- globe-sprite (multicolor, 12x21 fat pixels, 8 frames) ---
SPR_COL, SPR_D025, SPR_D026 = ORA, BRN, YEL


def globe_frames(n=8):
    frames = []
    for f in range(n):
        img = np.zeros((21, 12), np.uint8)  # waarden 0..3
        for y in range(21):
            for x in range(12):
                dx = (x + 0.5 - 6) / 6.0; dy = (y + 0.5 - 10.5) / 10.5
                d2 = dx * dx + dy * dy
                if d2 > 1: continue
                dz = np.sqrt(1 - d2)
                lon = np.arctan2(dx, dz) + f * 2 * np.pi / n
                lat = np.arcsin(dy)
                v = fbm2(np.array(lon * 2.2), np.array(lat * 3.0 + 7), 5, 3)
                light = np.clip(-dx * 0.6 - dy * 0.3 + dz * 0.7, 0, 1)
                if light < 0.18: val = 1
                elif v > 0.55: val = 1 if light < 0.5 else 2
                else: val = 2 if light < 0.45 else 3
                img[y, x] = val
        frames.append(img)
    return frames


def sprite_bytes(img):
    out = bytearray()
    for y in range(21):
        for bx in range(3):
            b = 0
            for p in range(4):
                b = (b << 2) | int(img[y, bx * 4 + p])
            out.append(b)
    return bytes(out) + b"\x00"


def render_sprite(img):
    pal = [None, SPR_D025, SPR_COL, SPR_D026]  # %01=$D025 %10=sprite kleur %11=$D026
    out = np.full((21, 24), 255, np.uint8)
    for y in range(21):
        for x in range(12):
            v = img[y, x]
            if v: out[y, x * 2:x * 2 + 2] = pal[v]
    return out


# --- volledige mockup ---
def mockup(scene_fixed, lines, status, path, globe_frame=0):
    cs = build_charset()
    top = np.repeat(scene_fixed, 2, axis=1)  # (136,320)
    ch, co = panel(lines, status)
    bottom = render_panel(ch, co, cs)
    full = np.vstack([top, bottom])
    spr = render_sprite(globe_frames()[globe_frame])
    sx, sy = SPRITE_X, SPRITE_Y
    m = spr != 255
    full[sy:sy + 21, sx:sx + 24][m] = spr[m]
    rgb = G.PALETTE[full].astype(np.uint8)
    im = Image.fromarray(rgb, "RGB")
    b = Image.new("RGB", (im.width + 64, im.height + 70), tuple(G.PALETTE[BLK].astype(int)))
    b.paste(im, (32, 35))
    b.resize((b.width * 2, b.height * 2), Image.NEAREST).save(path)


def export():
    cs = build_charset()
    os.makedirs(f"{ROOT}/assets", exist_ok=True); os.makedirs(f"{ROOT}/preview", exist_ok=True)
    data = bytes(b for g in cs for b in g)
    with open(f"{ROOT}/assets/ui.chr", "wb") as f:
        f.write(struct.pack("<H", 0xC800) + data)
    spr = b"".join(sprite_bytes(fr) for fr in globe_frames())
    with open(f"{ROOT}/assets/globe.spr", "wb") as f:
        f.write(struct.pack("<H", 0xC400) + spr)
    # charset-sheet als preview
    sheet = np.zeros((16 * 9, 16 * 9 * 2), np.uint8)
    for code in range(256):
        r, c = divmod(code, 16)
        col = (8 + YEL) if 96 <= code < 128 else WHT
        tile = render_panel(np.array([[code]]), np.array([[col]]), cs)[:8, :8]
        sheet[r * 9:r * 9 + 8, c * 18:c * 18 + 8] = tile
    Image.fromarray(G.PALETTE[sheet].astype(np.uint8)).resize((sheet.shape[1] * 3, sheet.shape[0] * 3), Image.NEAREST).save(f"{ROOT}/preview/UI_charset.png")
    print("ui.chr", len(data), "bytes; globe.spr", len(spr), "bytes")


if __name__ == "__main__":
    export()
