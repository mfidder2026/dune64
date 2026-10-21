#!/usr/bin/env python3
"""
build.py - bouwt het hele ASHKARA-project, cross-platform (Windows/Linux/macOS).

  python build.py            assets genereren + demo + spel compileren + D64's maken
  python build.py run        assets + demo en de demo starten in VICE (x64sc)
  python build.py assets     alleen de asset-pijplijn (scènes, personages, UI, mockups)
  python build.py demo       alleen de schermen-demo compileren + D64
  python build.py game       scripts compileren + spel compileren + build/ashkara.d64
  python build.py play       idem en het spel starten in VICE
  python build.py test       headless VICE-tests: screenshots in build/test/ (DESIGN.md §12.3)

cc65 (cl65) en VICE (x64sc, c1541) worden gezocht in: PATH, ./tools, ../tools en ../c64
(recursief). Overschrijven kan met omgevingsvariabelen CL65, X64SC, C1541.
Vereist Python 3.9+ met Pillow en numpy  (pip install pillow numpy).
"""
import os, sys, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PIPE = ROOT / "pipeline"
DEMO = ROOT / "demo"
SRC = ROOT / "src"
BUILD = ROOT / "build"
EXE = ".exe" if os.name == "nt" else ""

SCENES = ["titel", "ruimte", "raadzaal", "balkon", "comms", "hangar", "kaart", "woestijn", "kloof",
          "grot", "oogst", "nacht", "storm", "vesting", "oase", "einde"]
CHARS = ["doran", "vesna", "vorr", "mardo", "saira", "tarik"]
GAME_SRC = ["main.c", "gfx.c", "ui.c", "input.c", "disk.c", "game.c", "text.c", "vm.c", "builtin.c", "sim.c", "map.c", "data.c", "irq.s"]

# Headless tests: invoer (U/D/L/R/F/B/K, W = wachten), één toets per TEST_RATE frames,
# en de momenten (seconden emulatietijd) waarop een screenshot wordt gemaakt.
TEST_RATE = 80          # > 1 pagina typen (125 tekens / 2 per frame): elke F = volgende pagina
FORT_START = ("F" "F" "FF" "F"      # titel, startmenu: nieuw spel, intro (2+1)
              "FF" "DDF" "F" "DF"   # Doran (2), menu -> comms, Vorr (1), menu -> terug
              "DDDF" "FFF")         # menu -> hangar, Mardo (1+2)
RUST_FORT = "DDDDF" "F"             # raadzaal-menu -> Rust een dag, melding
TO_OOGST = (FORT_START + "F" "F"    # hangar: opstijgen, kaart: Rode Kloof (1 dag)
            "F" "F" "FF" "F"        # Saira (1), keuze water, antwoord (2), kloof: grot
            "F" "DDF" "F"           # Tarik (1), geschenk, melding
            "F" "F" "F"             # krijgers: zegen (1), werven (1)
            "F" "F" "FF")           # taak -> oogsten, melding (2)
RUST_GROT = "DDDDDF" "F"            # grot-menu -> Rust een dag, melding
TESTS = {
    # H1 tot en met de Tiende: Rode Kloof, Saira (water), Tarik (geschenk, zegen, werven, OOGST),
    # status, 3x rusten, +500 amber (testtoets A), terug naar het fort, Tiende verschepen.
    "h1_tiende": (TO_OOGST + "DDDDF" "FF" + RUST_GROT * 3 +
                  "A" "DDDDDDF" "DDF" "F"       # +500, vertrek, kaart, Fort Varo
                  "DDF" "DDF" "F" "F" "FF" "W", # hangar -> raadzaal -> comms -> verschepen, Vorr, einde H1
                  list(range(20, 241, 20))),
    # Tiende missen: 16x rusten -> waarschuwing (+3 dagen), 3x rusten -> game over -> titel
    "h1_gameover": (FORT_START + "DDF" + RUST_FORT * 16 + "F" + RUST_FORT * 3 + "F" "F" "W",
                    list(range(220, 341, 15))),
    # opslaan op dag 1, 3 dagen rusten, laden -> weer dag 1 in de hangar; dan K = kaart
    "save_load": (FORT_START + "DDF" "DDDDDF" "F" "F" + RUST_FORT * 3 +
                  "DDDDDF" "DF" "F" "W" "K" "W",
                  [62, 66, 130, 136, 142, 150, 160]),
    # 60 speldagen zonder Tiende (T), met oogsten: geen crash, dag ~63
    "days60": (TO_OOGST + "T" + RUST_GROT * 60 + "W", [240, 400, 560, 700]),
    # overvallen aan (O): rusten tot Ur-Kesh overvallen wordt -> bericht -> dag erna game over
    "raid": (TO_OOGST + "TO" + RUST_GROT * 40 + "W", [160, 240, 320, 400, 480]),
}


def scripts():
    """Scriptblokken in id-volgorde uit script/ids.txt."""
    out = []
    for line in (ROOT / "script" / "ids.txt").read_text(encoding="utf-8").splitlines():
        parts = line.split(";", 1)[0].split()
        if len(parts) == 2 and parts[0] == "script":
            out.append(parts[1])
    return out


def find_tool(name, env):
    if os.environ.get(env):
        return os.environ[env]
    p = shutil.which(name)
    if p:
        return p
    for base in (ROOT / "tools", ROOT.parent / "tools", ROOT.parent / "c64"):
        if base.is_dir():
            for hit in base.rglob(name + EXE):
                return str(hit)
    return None


def need(name, env):
    t = find_tool(name, env)
    if not t:
        sys.exit(f"{name} niet gevonden: zet cc65/VICE in ./tools, ../tools of ../c64, in PATH, of zet {env}=...")
    return t


def run(cmd, cwd=None):
    print(">", " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], cwd=cwd, check=True)


def assets():
    py = sys.executable
    for script in ("scenes.py", "characters.py", "ui.py", "mockups.py", "gen_demo.py"):
        run([py, PIPE / script], cwd=PIPE)


def make_d64(d64, title, files):
    c1541 = find_tool("c1541", "C1541")
    if d64.exists():
        d64.unlink()
    if c1541:
        cmd = [c1541, "-format", title, "d64", d64]
        for f in files:
            cmd += ["-write", f, f.name]
        run(cmd)
    else:
        run([sys.executable, PIPE / "mkd64.py", d64, title.upper()] + files)
    print(f"klaar: {d64}")
    return d64


def asset_files():
    a = ROOT / "assets"
    return [a / "ui.chr", a / "globe.spr"] + [a / f"{s}.scn" for s in SCENES] + [a / f"{c}.pat" for c in CHARS]


def demo():
    cl65 = need("cl65", "CL65")
    src = [DEMO / "src" / f for f in ("main.c", "gfx.c", "ui.c", "irq.s")]
    prg = DEMO / "ashkara"
    run([cl65, "-t", "c64", "-O", "-C", DEMO / "dune64.cfg", "-m", DEMO / "ashkara.map", "-o", prg] + src)
    return make_d64(DEMO / "ashkara-demo.d64", "ashkara demo,a1", [prg] + asset_files())


def game(defines=(), out=None):
    cl65 = need("cl65", "CL65")
    BUILD.mkdir(exist_ok=True)
    run([sys.executable, PIPE / "scriptc.py"])
    out = out or BUILD / "ashkara"
    out.parent.mkdir(parents=True, exist_ok=True)
    flags = []
    for d in defines:
        flags += ["-D", d]
    run([cl65, "-t", "c64", "-O", "-I", SRC, "-I", BUILD, *flags, "-C", SRC / "ashkara.cfg",
         "-m", out.with_suffix(".map"), "-o", out] + [SRC / f for f in GAME_SRC])
    prg = out
    scr = [ROOT / "assets" / f"{s}.scr" for s in scripts()]
    return make_d64(out.with_suffix(".d64"), "ashkara,a1", [prg] + asset_files() + scr)


def vice(d64):
    run([need("x64sc", "X64SC"), "-autostart", d64])


def test():
    x64 = need("x64sc", "X64SC")
    tdir = BUILD / "test"
    tdir.mkdir(parents=True, exist_ok=True)
    only = sys.argv[2:]
    for name, (keys, shots) in TESTS.items():
        if only and name not in only:
            continue
        (BUILD / "testkeys.h").write_text(
            f'/* gegenereerd door build.py test */\n#define TEST_RATE {TEST_RATE}\n'
            f'static const char test_keys[] = "{keys}";\n')
        d64 = game(["TESTMODE"], tdir / name / "ashkara")
        for sec in shots:
            png = tdir / f"{name}_{sec:03d}s.png"
            if png.exists():
                png.unlink()
            # eigen kopie per run: opslaan schrijft op de diskette, en Windows kan het vorige
            # image nog even vasthouden terwijl VICE afsluit (dan mislukt de autostart)
            run_d64 = tdir / name / f"run_{sec:03d}.d64"
            shutil.copyfile(d64, run_d64)
            cmd = [x64, "-default", "-warp", "-sounddev", "dummy", "+drive8truedrive", "-virtualdev8",
                   "-autostart", run_d64, "-limitcycles", str(985248 * sec), "-exitscreenshot", png]
            print(">", " ".join(str(c) for c in cmd))
            # VICE stopt met exitcode 1 als de cycluslimiet bereikt is: dat is hier de bedoeling
            subprocess.run([str(c) for c in cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("screenshot:", png if png.exists() else "MISLUKT")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("all", "assets", "run"):
        assets()
    if what in ("all", "demo", "run"):
        d = demo()
        if what == "run":
            vice(d)
    if what in ("all", "game", "play"):
        d = game()
        if what == "play":
            vice(d)
    if what == "test":
        test()
