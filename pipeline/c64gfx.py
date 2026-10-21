#!/usr/bin/env python3
"""
c64gfx.py - C64 multicolor-bitmap converter voor het ASHKARA-project.

Input : PNG in "fat pixel"-ruimte (160 px breed, hoogte veelvoud van 8),
        geïndexeerd met het C64-palet (of RGB; wordt naar dichtstbijzijnde
        paletkleur gemapt).
Output: C64-data die gegarandeerd binnen de multicolor-regels valt:
        - achtergrond ($D021) = 1 globale kleur (standaard 0 = zwart)
        - per 4x8 cel max. 3 extra kleuren (scherm-RAM hi/lo nibble + kleur-RAM)

Bestanden:
  .scn  scène (17 of 25 rijen), deflate-gecomprimeerd, zie DESIGN.md §8.2
  .pat  patchset (personage/overlay + mondframes), zie DESIGN.md §8.3
  .kla  Koala Painter (voor bekijken in externe tools)
  .png  preview zoals de C64 hem toont

Gebruik:
  python3 c64gfx.py scene  art.png  out.scn  [--preview p.png] [--koala k.kla]
  python3 c64gfx.py patch  base.png comp.png [mond1.png ...] out.pat
"""
import sys, zlib, struct, itertools, argparse
import numpy as np
from PIL import Image

# Colodore-palet (VICE: "colodore"); index = C64 kleurnummer
PALETTE = np.array([
    (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x81, 0x33, 0x38), (0x75, 0xCE, 0xC8),
    (0x8E, 0x3C, 0x97), (0x56, 0xAC, 0x4D), (0x2E, 0x2C, 0x9B), (0xED, 0xF1, 0x71),
    (0x8E, 0x50, 0x29), (0x55, 0x38, 0x00), (0xC4, 0x6C, 0x71), (0x4A, 0x4A, 0x4A),
    (0x7B, 0x7B, 0x7B), (0xA9, 0xFF, 0x9F), (0x70, 0x6D, 0xEB), (0xB2, 0xB2, 0xB2),
], dtype=np.float64)
NAMES = ["zwart", "wit", "rood", "cyaan", "paars", "groen", "blauw", "geel",
         "oranje", "bruin", "lichtrood", "donkergrijs", "grijs", "lichtgroen",
         "lichtblauw", "lichtgrijs"]

def _lab(rgb):
    """Ruwe perceptuele ruimte (gewogen RGB) - goed genoeg voor 16 kleuren."""
    rgb = np.asarray(rgb, dtype=np.float64)
    return rgb * np.array([0.30, 0.59, 0.11]) ** 0.5

PAL_LAB = _lab(PALETTE)
DIST = ((PAL_LAB[:, None, :] - PAL_LAB[None, :, :]) ** 2).sum(-1)  # 16x16


def palette_image(idx):
    """numpy index-array -> PIL 'P'-image met C64-palet."""
    im = Image.fromarray(idx.astype(np.uint8), "P")
    flat = PALETTE.astype(np.uint8).flatten().tolist()
    im.putpalette(flat + [0] * (768 - len(flat)))
    return im


def load_indexed(path):
    im = Image.open(path)
    if im.mode == "P":
        # vertrouw op paletindex als het palet overeenkomt, anders via RGB
        pal = np.array(im.getpalette()[:48]).reshape(-1, 3)
        if len(pal) == 16 and np.abs(pal - PALETTE).max() < 2:
            return np.array(im, dtype=np.uint8)
    rgb = np.array(im.convert("RGB"), dtype=np.float64)
    d = ((_lab(rgb)[:, :, None, :] - PAL_LAB[None, None]) ** 2).sum(-1)
    return d.argmin(-1).astype(np.uint8)


def convert_mc(pix, bg=0, maxc=3):
    """
    pix: (H,160) uint8 C64-kleurindices, H % 8 == 0.
    Retourneert (bitmap bytes, screen bytes, colram bytes, gecorrigeerde pix).
    Per cel worden de (max. maxc) kleuren gekozen die de totale fout minimaliseren.
    maxc=2 houdt bitpaar %11 (kleur-RAM) vrij, bijv. voor kaartmarkers.
    """
    H, W = pix.shape
    assert W == 160 and H % 8 == 0, "verwacht 160 x (veelvoud van 8)"
    rows, cols = H // 8, 40
    bitmap = bytearray(rows * cols * 8)
    screen = bytearray(rows * cols)
    colram = bytearray(rows * cols)
    out = pix.copy()
    for cy in range(rows):
        for cx in range(cols):
            cell = pix[cy * 8:cy * 8 + 8, cx * 4:cx * 4 + 4]
            vals, counts = np.unique(cell, return_counts=True)
            others = [int(v) for v in vals if v != bg]
            if len(others) <= maxc:
                chosen = others
            else:
                best, besterr = None, None
                for combo in itertools.combinations(others, maxc):
                    cand = [bg] + list(combo)
                    err = sum(int(c) * min(DIST[int(v), k] for k in cand)
                              for v, c in zip(vals, counts))
                    if besterr is None or err < besterr:
                        best, besterr = list(combo), err
                chosen = best
            # sorteer: meest gebruikte kleur -> kleur-RAM is vrij te kiezen
            chosen = sorted(chosen, key=lambda c: -int(counts[list(vals).index(c)]) if c in vals else 0)
            while len(chosen) < 3:
                chosen.append(0)   # ongebruikt bitpaar -> zwart
            c01, c10, c11 = chosen[0], chosen[1], chosen[2]
            cand = [bg, c01, c10, c11]
            # map elke pixel op dichtstbijzijnde kandidaat
            m = np.array([[min(range(4), key=lambda k: DIST[int(v), cand[k]]) for v in row] for row in cell])
            out[cy * 8:cy * 8 + 8, cx * 4:cx * 4 + 4] = np.array(cand)[m]
            base = (cy * cols + cx) * 8
            for line in range(8):
                b = 0
                for p in range(4):
                    b = (b << 2) | int(m[line, p])
                bitmap[base + line] = b
            screen[cy * cols + cx] = ((c01 & 15) << 4) | (c10 & 15)
            colram[cy * cols + cx] = c11 & 15
    return bytes(bitmap), bytes(screen), bytes(colram), out


def decode_mc(bitmap, screen, colram, rows, bg=0):
    """Onafhankelijke decoder (controle): C64-data -> (rows*8,160) indices."""
    out = np.zeros((rows * 8, 160), np.uint8)
    for cy in range(rows):
        for cx in range(40):
            i = cy * 40 + cx
            cand = [bg, screen[i] >> 4, screen[i] & 15, colram[i] & 15]
            for line in range(8):
                b = bitmap[i * 8 + line]
                for p in range(4):
                    out[cy * 8 + line, cx * 4 + p] = cand[(b >> (6 - 2 * p)) & 3]
    return out


def render_rgb(idx, scale=2, border=None, hires_rows=None):
    """Fat-pixel indices -> RGB PIL image (2x breed), optioneel met C64-rand."""
    rgb = PALETTE[idx].astype(np.uint8)
    rgb = np.repeat(rgb, 2, axis=1)  # fat pixel = 2 hires pixels
    im = Image.fromarray(rgb, "RGB")
    if border is not None:
        b = Image.new("RGB", (im.width + 64, im.height + 70), tuple(PALETTE[border].astype(int)))
        b.paste(im, (32, 35))
        im = b
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def deflate(data):
    c = zlib.compressobj(9, zlib.DEFLATED, -15, 9)
    return c.compress(data) + c.flush()


def write_scn(path, bitmap, screen, colram, rows, bg=0, load_addr=0xA000):
    bm = deflate(bitmap)
    cl = deflate(screen + colram)
    payload = struct.pack("<BBBBHH", ord("S"), rows, 0x01, bg, len(bm), len(cl)) + bm + cl
    with open(path, "wb") as f:
        f.write(struct.pack("<H", load_addr) + payload)
    return len(payload) + 2


def write_koala(path, bitmap, screen, colram, rows, bg=0):
    bm = bytearray(8000); sc = bytearray(1000); co = bytearray(1000)
    bm[:len(bitmap)] = bitmap; sc[:len(screen)] = screen; co[:len(colram)] = colram
    with open(path, "wb") as f:
        f.write(struct.pack("<H", 0x6000) + bytes(bm) + bytes(sc) + bytes(co) + bytes([bg]))


def cell_rect_diff(a, b):
    """Kleinste celrechthoek waarin twee (H,160) beelden verschillen."""
    rows = a.shape[0] // 8
    diff = np.zeros((rows, 40), bool)
    for cy in range(rows):
        for cx in range(40):
            if not np.array_equal(a[cy*8:cy*8+8, cx*4:cx*4+4], b[cy*8:cy*8+8, cx*4:cx*4+4]):
                diff[cy, cx] = True
    if not diff.any():
        return None
    ys, xs = np.where(diff)
    return int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)


def patch_bytes(conv, rect):
    """Haal celrechthoek uit geconverteerde scène (bitmap, screen, colram)."""
    bitmap, screen, colram = conv
    x, y, w, h = rect
    bm, sc, co = bytearray(), bytearray(), bytearray()
    for cy in range(y, y + h):
        for cx in range(x, x + w):
            i = cy * 40 + cx
            bm += bitmap[i * 8:i * 8 + 8]
            sc.append(screen[i]); co.append(colram[i])
    return struct.pack("<BBBB", x, y, w, h) + bytes(bm) + bytes(sc) + bytes(co)


def write_pat(path, patches, load_addr=0xA000):
    """patches: lijst van bytes (elk uit patch_bytes). Container: 'P', n, flags, size, deflate."""
    raw = bytes([len(patches)]) + b"".join(patches)
    comp = deflate(raw)
    payload = struct.pack("<BBH", ord("P"), 0x01, len(raw)) + comp
    with open(path, "wb") as f:
        f.write(struct.pack("<H", load_addr) + payload)
    return len(payload) + 2


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scene"); s.add_argument("png"); s.add_argument("out")
    s.add_argument("--preview"); s.add_argument("--koala"); s.add_argument("--bg", type=int, default=0)
    s.add_argument("--maxc", type=int, default=3, help="max. kleuren per cel naast achtergrond (2 = %%11 vrij)")
    p = sub.add_parser("patch"); p.add_argument("files", nargs="+")
    a = ap.parse_args()
    if a.cmd == "scene":
        pix = load_indexed(a.png)
        bm, sc, co, fixed = convert_mc(pix, a.bg, a.maxc)
        rows = pix.shape[0] // 8
        n = write_scn(a.out, bm, sc, co, rows, a.bg)
        assert np.array_equal(decode_mc(bm, sc, co, rows, a.bg), fixed)
        if a.preview: render_rgb(fixed).save(a.preview)
        if a.koala: write_koala(a.koala, bm, sc, co, rows, a.bg)
        print(f"{a.out}: {rows} rijen, {n} bytes op disk")
    else:
        *ins, out = a.files
        base = convert_mc(load_indexed(ins[0]))
        patches = []
        for f in ins[1:]:
            conv = convert_mc(load_indexed(f))
            rect = cell_rect_diff(base[3], conv[3])
            if rect: patches.append(patch_bytes(conv[:3], rect))
        n = write_pat(out, patches)
        print(f"{out}: {len(patches)} patches, {n} bytes op disk")


if __name__ == "__main__":
    main()
