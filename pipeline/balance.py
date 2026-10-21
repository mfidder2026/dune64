#!/usr/bin/env python3
"""
balance.py - balanstest met een gesimuleerde speler (DESIGN.md §14, fase 4).

Een Python-port van de regels in src/sim.c en src/battle.c (oogst, training, overvallen,
vergroening, gevechten) plus een eenvoudige, redelijke speler. Per strategie (militair, groen)
worden N spellen gespeeld met verschillende seeds; het script meldt hoe vaak en op welke dag
het einde gehaald wordt, en hoe vaak het spel verloren gaat.

  python pipeline/balance.py [N]
"""
import os, sys, random, statistics
sys.path.insert(0, os.path.dirname(__file__))
import datac

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAID_RANGE, ABANDON_RANGE = 6, 8
FACTOR10 = [10, 14, 20, 30]
WEAPON_PRICE = [80, 200, 300]
VERRAAD, DORAN, WINDVANGER, MAX_DAY = 34, 40, 44, 150
ATTACK_AT = 65        # de gesimuleerde speler valt aan vanaf deze kans (%)


def dist(a, b):
    return abs(a["x"] - b["x"]) + abs(a["y"] - b["y"])


def yield_(c):
    y = c["size"] * min(c["richness"], 100) // 200
    return y * 2 if c["harv"] else y


def power(c):
    return c["size"] * (50 + c["skill"]) * FACTOR10[c["equip"]] // 500


def garrison(t):
    return t["size"] * 4 if t["type"] in (2, 3) else 60


class Game:
    def __init__(self, seed, strategy):
        self.rng = random.Random(seed)
        self.strategy = strategy
        self.locs = [dict(l, status=l["status"], job=0, skill=0, equip=0, green=0, harv=False, wind=False)
                     for l in datac.load_locations(f"{ROOT}/data/locations.json")]
        self.day, self.amber, self.verraad, self.citadel, self.won = 1, 0, False, False, 0
        self.result = None

    def camps(self, status=None):
        return [c for c in self.locs if c["type"] == 1 and (status is None or c["status"] == status)]

    # ---- één dag, zoals sim_day()
    def sim_day(self):
        for c in self.camps(2):
            if self.verraad and self.day % 5 == 0 and c["size"] < 90: c["size"] += 1
            if c["job"] == 1:
                y = yield_(c); self.amber += y; c["richness"] = max(0, c["richness"] - y // 4)
            elif c["job"] == 2:
                c["skill"] = min(100, c["skill"] + (4 if self.day >= DORAN and self.verraad else 2))
            elif c["job"] == 3 and c["wind"]:
                c["green"] = min(100, c["green"] + 2)
                if c["green"] >= 60: c["richness"] = 0
        if self.day >= 15:                           # overvallen vanaf hoofdstuk 2
            raided = False
            for c in self.camps(2):
                if c["job"] != 1: continue
                if any(p is not c and p["status"] == 2 and p["job"] == 2 and dist(p, c) <= RAID_RANGE for p in self.camps()):
                    continue
                if self.rng.randrange(100) < 2 + yield_(c) // 20:
                    c["status"], c["job"], c["trust"] = 3, 0, max(0, c["trust"] - 20); raided = True
            if not self.camps(2) and self.camps(3) and not raided:
                self.result = ("verloren", self.day); return
        if self.verraad:
            outposts = 0
            for v in self.locs:
                if v["type"] != 2: continue
                near = [c["green"] for c in self.camps() if c["status"] != 3 and dist(c, v) <= ABANDON_RANGE]
                if near and sum(near) // len(near) >= 60:
                    v.update(type=1, status=2, size=10, trust=60, green=60, richness=0, job=0)
                else:
                    outposts += 1
            area = [c["green"] for c in self.locs if c["type"] in (1, 2)]
            if not outposts and sum(area) // len(area) >= 50:
                self.result = ("groen", self.day); return
        self.day += 1
        if self.day >= VERRAAD: self.verraad = True

    def rest(self, days):
        for _ in range(days):
            if self.result: return
            self.sim_day()

    # ---- de speler
    def recruit_phase(self):
        """H1-H2: kampen ontdekken en werven (gemiddeld 2 reisdagen per kamp), oogsten."""
        urkesh = self.locs[1]
        urkesh.update(status=2, trust=55, job=1, harv=True)
        order = sorted(self.camps(0), key=lambda c: -c["size"])
        for c in order:
            if self.day > 30: break
            self.rest(2 + self.rng.randrange(3))      # reizen + zoeken
            if self.result: return
            if c["trust"] + 20 + 20 >= 50:           # zegen + water + praten
                c["status"], c["trust"] = 2, c["trust"] + 20
                # oogsten, met elke derde kamp op STRIJD als bescherming tegen overvallen
                c["job"] = 2 if len(self.camps(2)) % 3 == 0 else 1

    def military(self):
        for c in sorted(self.camps(2), key=lambda c: -c["size"])[:4]:
            c["job"] = 2                                  # na het verraad: de sterkste trainen
        while not self.result and self.day < MAX_DAY:
            allies = sorted(self.camps(2), key=power, reverse=True)
            for c in allies:                          # wapens kopen
                if c["equip"] < 3 and self.amber >= WEAPON_PRICE[c["equip"]] and c["job"] == 2:
                    self.amber -= WEAPON_PRICE[c["equip"]]; c["equip"] += 1
            fighters = [c for c in allies if c["job"] == 2][:3] or allies[:3]
            k = sum(power(c) for c in fighters)
            outposts = [v for v in self.locs if v["type"] == 2]
            t = self.locs[17] if self.citadel else (min(outposts, key=garrison) if outposts else None)
            if t is None:
                self.rest(1); continue
            g = garrison(t)
            if self.verraad and k * 100 // (k + g) >= ATTACK_AT:
                self.rest(2)                          # vliegen + een dag aanval
                if self.result: return
                if self.rng.randrange(256) < k * 255 // (k + g):
                    for c in fighters: c["size"] -= c["size"] // 10
                    if t["type"] == 3:
                        self.result = ("militair", self.day); return
                    t.update(type=1, status=2, size=g // 8, trust=80, skill=20, equip=1, richness=100, job=2)
                    self.won += 1
                    if self.won >= 2: self.citadel = True
                else:
                    for c in fighters: c["size"] -= c["size"] // 2
            else:
                self.rest(1)

    def green(self):
        while not self.result and self.day < MAX_DAY:
            if self.verraad and self.day >= WINDVANGER:
                for c in sorted(self.camps(2), key=lambda c: c["job"] != 1):   # oogsters als laatste
                    if not c["wind"] and self.amber >= 150 and len([x for x in self.camps(2) if x["job"] == 1]) > 1 or \
                       (not c["wind"] and self.amber >= 150 and c["job"] != 1):
                        self.amber -= 150; c["wind"] = True; c["job"] = 3
            self.rest(1)

    def play(self):
        self.recruit_phase()
        if not self.result:
            self.rest(max(0, VERRAAD - self.day))
        if not self.result:
            self.military() if self.strategy == "militair" else self.green()
        return self.result or ("niet gehaald", self.day)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    for strategy in ("militair", "groen"):
        res = [Game(seed, strategy).play() for seed in range(n)]
        wins = [d for r, d in res if r == strategy]
        lost = sum(1 for r, _ in res if r == "verloren")
        other = sum(1 for r, _ in res if r not in (strategy, "verloren"))
        line = f"{strategy:9s}: gewonnen {len(wins):3d}/{n}"
        if wins: line += f", dag mediaan {statistics.median(wins):.0f} (min {min(wins)}, max {max(wins)})"
        print(line + f", verloren {lost}, niet gehaald binnen {MAX_DAY} dagen {other}")


if __name__ == "__main__":
    main()
