#!/usr/bin/env python3
"""
mkd64.py - maak een 1541 D64-image (35 sporen) met PRG-bestanden.
Alternatief voor VICE's c1541 als die niet in het pad staat.

  python3 mkd64.py out.d64 "SCHIJFNAAM,ID" bestand1 [bestand2 ...]
De C64-bestandsnaam is de bestandsnaam zonder pad, in hoofdletters PETSCII.
"""
import os, sys

SPT = [21] * 17 + [19] * 7 + [18] * 6 + [17] * 5   # sectoren per spoor 1..35


def ts_offset(t, s):
    return (sum(SPT[:t - 1]) + s) * 256


def petscii_name(name, n=16):
    b = bytes(ord(c.upper()) if 32 <= ord(c) < 96 or c.isalpha() else 0x2E for c in name)[:n]
    return b + b"\xA0" * (n - len(b))


def make(out, label, files, interleave=10):
    img = bytearray(sum(SPT) * 256)
    used = {t: set() for t in range(1, 36)}
    used[18] |= {0, 1}
    order = list(range(17, 0, -1)) + list(range(19, 36))   # zoals de 1541: dicht bij de directory eerst

    def alloc(prev_t, prev_s):
        tracks = order if prev_t is None else order[order.index(prev_t):] + order[:order.index(prev_t)]
        for t in tracks:
            n = SPT[t - 1]
            start = 0 if (prev_t != t or prev_s is None) else (prev_s + interleave) % n
            for k in range(n):
                s = (start + k) % n
                if s not in used[t]:
                    used[t].add(s); return t, s
        raise SystemExit("disk vol")

    entries = []
    for path in files:
        data = open(path, "rb").read()
        chunks = [data[i:i + 254] for i in range(0, len(data), 254)] or [b""]
        t = s = None; first = None; prev = None
        for i, ch in enumerate(chunks):
            t, s = alloc(t, s)
            if first is None: first = (t, s)
            if prev:
                o = ts_offset(*prev); img[o] = t; img[o + 1] = s
            o = ts_offset(t, s)
            img[o + 2:o + 2 + len(ch)] = ch
            img[o] = 0; img[o + 1] = len(ch) + 1
            prev = (t, s)
        entries.append((os.path.basename(path), first, len(chunks)))

    # directory (18/1 ...)
    dir_secs = [1]
    nsec = (len(entries) + 7) // 8
    s = 1
    for _ in range(nsec - 1):
        s = (s + 3) % 19
        while s in used[18]: s = (s + 1) % 19
        used[18].add(s); dir_secs.append(s)
    for i, (name, (ft, fs), blocks) in enumerate(entries):
        sec = dir_secs[i // 8]; o = ts_offset(18, sec) + (i % 8) * 32
        img[o + 2] = 0x82; img[o + 3] = ft; img[o + 4] = fs
        img[o + 5:o + 21] = petscii_name(name)
        img[o + 30] = blocks & 0xFF; img[o + 31] = blocks >> 8
    for k, sec in enumerate(dir_secs):
        o = ts_offset(18, sec)
        if k + 1 < len(dir_secs): img[o] = 18; img[o + 1] = dir_secs[k + 1]
        else: img[o] = 0; img[o + 1] = 0xFF
    # BAM
    o = ts_offset(18, 0)
    img[o] = 18; img[o + 1] = 1; img[o + 2] = 0x41
    for t in range(1, 36):
        n = SPT[t - 1]
        bits = sum(1 << s for s in range(n) if s not in used[t])
        img[o + 4 * t] = n - len(used[t])
        img[o + 4 * t + 1] = bits & 0xFF; img[o + 4 * t + 2] = (bits >> 8) & 0xFF; img[o + 4 * t + 3] = (bits >> 16) & 0xFF
    name, _, did = label.partition(",")
    img[o + 0x90:o + 0xA0] = petscii_name(name)
    img[o + 0xA0:o + 0xAB] = b"\xA0\xA0" + petscii_name(did or "01", 2) + b"\xA0" + b"2A" + b"\xA0" * 4
    open(out, "wb").write(img)
    free = sum(SPT[t - 1] - len(used[t]) for t in range(1, 36) if t != 18)
    print(f"{out}: {len(entries)} bestanden, {free} blokken vrij")


if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2], sys.argv[3:])
