#!/usr/bin/env python3
"""
datac.py - spel-data (DESIGN.md §8.6): data/locations.json -> tabellen voor src/data.c.

Wordt aangeroepen door scriptc.py, omdat elke locatie naar een script-node verwijst
(node-pointers zijn pas na het compileren van de scripts bekend).
De startwaarden gaan als C-tabel in het programma (19 x 12 bytes); een apart .dat-bestand
is daardoor niet nodig. game_init() kopieert ze naar de spelstatus.
"""
import json

LOC_TYPES = ["FORT", "KAMP", "VOORPOST", "CITADEL", "HANDEL"]
LOC_STATUS = ["ONBEKEND", "BEKEND", "BONDGENOOT", "BEZET", "GROEN"]
LOC_FLAGS = {"HARVESTER": 0x01, "WINDVANGER": 0x02, "LICHTEND": 0x04, "GESCHENK": 0x08, "GESPROKEN": 0x10}
NAME_MAX = 14
MAP_W, MAP_H = 40, 17
MAX_LOCS = 32


class DataError(Exception):
    pass


def load_locations(path):
    data = json.load(open(path, encoding="utf-8"))
    locs, seen = [], set()
    for i, d in enumerate(data["locations"]):
        where = f"locations.json[{i}]"
        try:
            lid, name, typ, x, y = d["id"], d["name"], d["type"], d["x"], d["y"]
        except KeyError as e:
            raise DataError(f"{where}: veld {e} ontbreekt")
        if lid in seen: raise DataError(f"{where}: id '{lid}' dubbel")
        seen.add(lid)
        if typ not in LOC_TYPES: raise DataError(f"{where}: type {typ!r} (kies uit {LOC_TYPES})")
        status = d.get("status", "ONBEKEND")
        if status not in LOC_STATUS: raise DataError(f"{where}: status {status!r}")
        if not (0 <= x < MAP_W and 0 <= y < MAP_H): raise DataError(f"{where}: ({x},{y}) buiten de kaart")
        if len(name) > NAME_MAX: raise DataError(f"{where}: naam langer dan {NAME_MAX} tekens")
        flags = 0
        for f in d.get("flags", []):
            if f not in LOC_FLAGS: raise DataError(f"{where}: vlag {f!r}")
            flags |= LOC_FLAGS[f]
        locs.append(dict(id=lid, name=name, type=LOC_TYPES.index(typ), x=x, y=y,
                         status=LOC_STATUS.index(status), node=d.get("node"),
                         size=d.get("size", 0), trust=d.get("trust", 0), richness=d.get("richness", 0),
                         flags=flags))
    if len(locs) > MAX_LOCS: raise DataError(f"meer dan {MAX_LOCS} locaties")
    for a in locs:
        for b in locs:
            if a is not b and (a["x"], a["y"]) == (b["x"], b["y"]):
                raise DataError(f"{a['id']} en {b['id']} liggen op dezelfde cel")
    return locs


def c_loc_init(locs):
    """Regels voor `const loc_t loc_init[]` (veldvolgorde van loc_t in game.h)."""
    out = []
    for l in locs:
        out.append(f"    {{ {l['type']}, {l['x']:2d}, {l['y']:2d}, {l['status']}, {l['size']:3d}, {l['trust']:3d}, "
                   f"0, 0, 0, {l['richness']:3d}, 0, 0x{l['flags']:02X} }},   /* {l['id']} */")
    return out
