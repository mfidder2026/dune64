#!/usr/bin/env python3
"""
music.py - de muziek van ASHKARA (eigen compositie) -> data voor src/music.s.

"Amberwind": D harmonisch mineur (de overmatige secunde Bes-Cis geeft de woestijnklank),
akkoorden Dm - Bes - Gm - A, 2 maten per akkoord. Stem 1 bas (driehoek), stem 2 arpeggio
(korte puls, zestienden), stem 3 melodie (puls) met een variatie bij de herhaling.
Een tick = 6 frames (PAL: 8,3 ticks/s), een maat = 16 ticks.

Uitvoer: build/music.bin (raw, hoort op $D200: zie de kop van src/music.s).
"""
import os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE = 0xD200
TEMPO = 6
PAL_CLOCK = 985248
NOTE_NAMES = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6,
              "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}

# AD, SR, golfvorm, pulsbreedte (12 bit)
INSTRUMENTS = [
    (0x08, 0xA6, 0x10, 0x000),   # 0 bas: driehoek, stevig
    (0x04, 0x00, 0x40, 0x380),   # 1 arpeggio: smalle puls, kort getokkeld
    (0x29, 0x88, 0x40, 0x800),   # 2 melodie: brede puls, zacht aanzetten
    (0x0A, 0x00, 0x80, 0x000),   # 3 ruis: zachte tik (niet gebruikt in de lus)
]

CHORDS = {"Dm": ["D", "F", "A"], "Bb": ["Bb", "D", "F"], "Gm": ["G", "Bb", "D"], "A": ["A", "C#", "E"]}
PROGRESSION = ["Dm", "Dm", "Bb", "Bb", "Gm", "Gm", "A", "A"]

MELODY_A = [  # maat voor maat: (noot, ticks)
    [("A4", 8), ("G4", 4), ("F4", 4)],
    [("E4", 6), ("F4", 2), ("D4", 8)],
    [("D4", 4), ("F4", 4), ("Bb4", 8)],
    [("A4", 6), ("G4", 2), ("F4", 8)],
    [("G4", 8), ("Bb4", 4), ("D5", 4)],
    [("C#5", 6), ("D5", 2), ("Bb4", 8)],
    [("A4", 4), ("C#5", 4), ("E5", 8)],
    [("D5", 2), ("C#5", 2), ("Bb4", 2), ("A4", 2), ("G4", 4), ("E4", 4)],
]
MELODY_B = [
    [("D5", 12), ("C#5", 2), ("D5", 2)],
    [("E5", 4), ("F5", 4), ("E5", 4), ("D5", 4)],
    [("F5", 8), ("E5", 4), ("D5", 4)],
    [("D5", 16)],
    [("Bb4", 6), ("A4", 2), ("G4", 8)],
    [("Bb4", 4), ("C#5", 4), ("D5", 8)],
    [("E5", 8), ("C#5", 8)],
    [("A4", 14), ("-", 2)],
]


def note_num(name):
    """'C#4' -> 0..95 (C0 = 0)."""
    pitch, octave = name[:-1], int(name[-1])
    return octave * 12 + NOTE_NAMES[pitch]


def freq_table():
    lo, hi = [], []
    for n in range(96):
        hz = 16.3516 * 2 ** (n / 12)
        f = min(0xFFFF, round(hz * 16777216 / PAL_CLOCK))
        lo.append(f & 0xFF); hi.append(f >> 8)
    return lo, hi


def ev_note(name, ticks):
    if name == "-": return [0x60, ticks]
    return [note_num(name), ticks]


def bass_voice():
    out = [0x70 + 0]
    for ch in PROGRESSION:
        root = CHORDS[ch][0]
        fifth = CHORDS[ch][2]
        out += ev_note(root + "2", 4) + ev_note(root + "2", 2) + ev_note(fifth + "2", 2)
        out += ev_note(root + "3", 4) + ev_note(root + "2", 4)
    return out + [0xFF]


def arp_voice():
    out = [0x70 + 1]
    for ch in PROGRESSION:
        a, b, c = CHORDS[ch]
        pattern = [a + "4", b + "4", c + "4", a + "5", c + "4", b + "4", a + "4", b + "4"]
        for i in range(16):
            out += ev_note(pattern[i % 8], 1)
    return out + [0xFF]


def melody_voice():
    out = [0x70 + 2]
    for bar in MELODY_A + MELODY_B:
        assert sum(t for _, t in bar) == 16, bar
        for n, t in bar:
            out += ev_note(n, t)
    return out + [0xFF]


def build():
    voices = [bass_voice(), arp_voice(), melody_voice()]   # bas en arpeggio: 8 maten, melodie 16
    header_len = 1 + 6 + 8 * 5 + 96 * 2
    lo, hi = freq_table()
    data = bytearray([TEMPO])
    addr = BASE + header_len
    starts = []
    for v in voices:
        starts.append(addr); addr += len(v)
    for a in starts:
        data += bytes([a & 0xFF, a >> 8])
    for i in range(8):
        ad, sr, wave, pw = INSTRUMENTS[i] if i < len(INSTRUMENTS) else (0, 0, 0, 0)
        data += bytes([ad, sr, wave, pw & 0xFF, pw >> 8])
    data += bytes(lo) + bytes(hi)
    assert len(data) == header_len
    for v in voices:
        data += bytes(v)
    return bytes(data)


def main():
    data = build()
    os.makedirs(f"{ROOT}/build", exist_ok=True)
    with open(f"{ROOT}/build/music.bin", "wb") as f:
        f.write(data)
    print(f"music.bin: {len(data)} bytes (op ${BASE:04X})")


if __name__ == "__main__":
    main()
