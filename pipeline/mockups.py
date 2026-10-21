#!/usr/bin/env python3
"""mockups.py - storyboard: volledige C64-schermen (scène + personage + UI-paneel) in verhaalvolgorde."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from c64art import *
import c64gfx as G
import scenes as S
import characters as C
import ui as U

ROOT = S.ROOT
W, Y_ = WHT, YEL

STORY = [
 ("01", "TITEL", None, 0, None, None, "Titelscherm (volledig bitmap). 'DRUK OP VUUR' als hires-sprites eroverheen."),
 ("02", "RUIMTE", None, 0, [("Ashkara, jaar 812.", Y_), ("De Hoge Raad stuurt Ilan", W), ("Varo als landvoogd naar", W),
   ("de amberwoestijn. Wie het", W), ("amber beheerst, beheerst", W), ("de sprongroutes.", W)],
   dict(dag=1, amber=0, krijgers=0, groen=0), "Intro: vertelling over de planeet."),
 ("03", "RAADZAAL", "DORAN", 2, [("DORAN KEYL", Y_), ("Het fort is van ons, heer.", W), ("Maar met veertig wachters", W),
   ("houden we de Citadel van", W), ("het Consortium niet lang", W), ("op afstand.", W)],
   dict(dag=1, amber=0, krijgers=0, groen=0), "Hoofdstuk 1 - Aankomst. Doran praat (mondframe 'open')."),
 ("04", "BALKON", "VESNA", 0, [("VESNA ADAIR", Y_), ("Vorr glimlacht te veel.", W), ("Mijn mensen zien zijn", W),
   ("schepen 's nachts landen", W), ("bij de oude mijnen. Hij", W), ("wacht op een fout van ons.", W)],
   dict(dag=1, amber=0, krijgers=0, groen=0, nacht=1), "Vesna op het balkon bij zonsondergang."),
 ("05", "COMMS", "VORR", 1, [("GOUVERNEUR VORR", Y_), ("De Raad verwacht de eerste", W), ("Tiende, landvoogd: 500", W),
   ("amber binnen 15 dagen.", W), ("Ik zou het jammer vinden", W), ("als u zou falen.", W)],
   dict(dag=2, amber=0, krijgers=0, groen=0), "Eerste eis van het Consortium; start van de Tiende-klok."),
 ("06", "HANGAR", "MARDO", 0, [("DR. ILSE MARDO", Y_), ("Uw glider staat klaar. Ik", W), ("meet al jaren de diepe", W),
   ("waterlagen. Ze zakken", W), ("sneller dan het Consortium", W), ("toegeeft.", W)],
   dict(dag=2, amber=0, krijgers=0, groen=0), "Hangar: de glider wordt beschikbaar, Mardo zaait het ecologie-plot."),
 ("07", "KAART", None, 0, [("BESTEMMING", Y_), ("> Fort Varo", Y_), ("  Rode Kloof", W), ("  Diepe Zandzee", W),
   ("  Zoutvlakte Mer", W), ("  Terug", W)],
   dict(dag=3, amber=0, krijgers=0, groen=0), "Strategische kaart; markers en cursor zijn sprites."),
 ("08", "WOESTIJN", None, 0, [("ONDERWEG", Y_), ("De glider scheert over de", W), ("duinen. In het zuiden zie", W),
   ("je een rode kloof.", W), ("> Landen", Y_), ("  Doorvliegen", W)],
   dict(dag=3, amber=0, krijgers=0, groen=0), "Reizen: onderweg kunnen nieuwe locaties ontdekt worden."),
 ("09", "KLOOF", "SAIRA", 0, [("SAIRA", Y_), ("Je draagt laarzen van de", W), ("stad en ruikt naar olie.", W),
   ("Waarom zou Tarik met een", W), ("landvoogd praten?", W), ("> Ik breng water mee.", Y_)],
   dict(dag=4, amber=0, krijgers=0, groen=0), "Eerste ontmoeting met de Kethari; keuze beinvloedt vertrouwen."),
 ("10", "GROT", "TARIK", 0, [("TARIK UR-KESH", Y_), ("> Vraag om krijgers", Y_), ("  Vraag naar het water", W),
   ("  Bied een geschenk aan", W), ("  Vraag naar andere kampen", W), ("  Vertrek", W)],
   dict(dag=5, amber=0, krijgers=0, groen=0), "Dialoogmenu in het grotkamp; hier rekruteer je het eerste kamp."),
 ("11", "OOGST", None, 0, [("KAMP UR-KESH: OOGST", Y_), ("Veertig Kethari werken nu", W), ("met de oogstmachine. Ze", W),
   ("delven 18 amber per dag.", W), ("Let op: de machine trekt", W), ("patrouilles aan.", W)],
   dict(dag=7, amber=36, krijgers=40, groen=0), "Strategielaag: een kamp is toegewezen aan OOGST."),
 ("12", "NACHT", "", 0, [("SAIRA", Y_), ("Kijk daar. Waar het amber", W), ("dicht onder het zand ligt,", W),
   ("gloeien de duinen. Wij", W), ("noemen ze de lichtende", W), ("velden.", W)],
   dict(dag=19, amber=410, krijgers=150, groen=0, nacht=1), "Hoofdstuk 2 - Het Zandvolk. Vertrouwen groeit; lore."),
 ("13", "STORM", None, 0, [("HOOFDSTUK 3: VERRAAD", Y_), ("Het fort brandt. Met Saira", W), ("en een handvol wachters", W),
   ("vlucht je de storm in. Het", W), ("zand verbergt je, maar het", W), ("vreet aan de glider.", W)],
   dict(dag=34, amber=120, krijgers=210, groen=0), "Gescripte wending: het fort valt, de Tiende vervalt."),
 ("14", "VESTING", None, 0, [("VOORPOST NOORD", Y_), ("Garnizoen:          220", W), ("Jouw krijgers:      340", W),
   ("Uitrusting: zandmessen", W), ("> Aanvallen", Y_), ("  Terugtrekken", W)],
   dict(dag=52, amber=260, krijgers=340, groen=4, nacht=1), "Hoofdstuk 4 - Opstand: voorposten veroveren."),
 ("15", "OASE", None, 0, [("DR. ILSE MARDO", Y_), ("Drie seizoenen planten,", W), ("en kijk: het water komt", W),
   ("terug. Waar het groen", W), ("groeit, kan het Consortium", W), ("niet meer delven.", W)],
   dict(dag=71, amber=300, krijgers=520, groen=18), "Ecologische route: vergroende gebieden worden opgegeven."),
 ("16", "EINDE", None, 0, None, None, "Einde (volledig bitmap): de regen keert terug."),
]


# kaartlocaties (cel x, cel y, kleur) - zie DESIGN.md §4.2
MAP_MARKERS = [(20, 9, WHT, YEL), (8, 6, YEL, BLK), (31, 4, YEL, BLK), (26, 13, YEL, BLK), (13, 3, RED, BLK), (35, 10, RED, BLK), (4, 13, LGR, BLK)]


MARKER = ["0000", "0330", "3113", "3113", "3113", "0330", "0000", "0000"]   # 4x8 fat px, 3=%11 1=%01


def plot_marker(fixed, cx, cy, color, inner=BLK):
    """Marker vervangt een hele cel: bitmap = MARKER, kleur-RAM = color, scherm-RAM hi = inner."""
    for dy, row in enumerate(MARKER):
        for dx, v in enumerate(row):
            fixed[cy * 8 + dy, cx * 4 + dx] = {"0": BLK, "1": inner, "3": color}[v]


def composite(scene, char, mouth):
    cv = C.render_scene(scene)
    if char:
        C.CHARS[char][0](cv, mouth=mouth)
    fixed = G.convert_mc(cv.px, maxc=S.MAXC.get(scene, 3))[3]
    if scene == "KAART":
        for cx, cy, col, inner in MAP_MARKERS:
            plot_marker(fixed, cx, cy, col, inner)
    return fixed


def full_bitmap_png(fixed, path):
    G.render_rgb(fixed, scale=2, border=BLK).save(path)


def build():
    os.makedirs(f"{ROOT}/mockups", exist_ok=True)
    out = []
    for sid, scene, char, mouth, lines, status, caption in STORY:
        fixed = composite(scene, char, mouth)
        path = f"{ROOT}/mockups/{sid}_{scene}{('_' + char) if char else ''}.png"
        if lines is None:
            full_bitmap_png(fixed, path)
            if scene == "TITEL":
                im = Image.open(path); d = ImageDraw.Draw(im)
                # 'DRUK OP VUUR' als hires-sprite-tekst (C64-font)
                cs = U.build_charset()
                codes = U.scr("DRUK OP VUUR")
                arr = U.render_panel(np.array([codes]), np.array([[YEL] * len(codes)]), cs)
                rgb = Image.fromarray(G.PALETTE[arr].astype(np.uint8)).resize((arr.shape[1] * 2, 16), Image.NEAREST)
                mask = Image.fromarray(((arr != 0) * 255).astype(np.uint8)).resize((arr.shape[1] * 2, 16), Image.NEAREST)
                im.paste(rgb, (64 + 320 - arr.shape[1], 70 + 2 * 180), mask)
                im.save(path)
        else:
            U.mockup(fixed, lines, status, path)
        out.append((sid, scene, char, caption, path))
        print(path)
    return out


def storyboard(items, path):
    thumbs = [Image.open(p).resize((384, 272), Image.LANCZOS) for *_, p in items]
    cols = 4; rows = (len(thumbs) + cols - 1) // cols
    W_, H_ = 384, 272 + 54
    sheet = Image.new("RGB", (cols * W_ + (cols + 1) * 12, rows * H_ + (rows + 1) * 12 + 50), (24, 22, 30))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    d.text((12, 14), "ASHKARA - storyboard (C64, multicolor bitmap + UI-paneel)", font=fb, fill=(240, 200, 120))
    for i, (im, (sid, scene, char, caption, _)) in enumerate(zip(thumbs, items)):
        r, c = divmod(i, cols)
        x = 12 + c * (W_ + 12); y = 62 + r * (H_ + 12)
        sheet.paste(im, (x, y))
        d.text((x, y + 276), f"{sid}  {scene}{(' + ' + char) if char else ''}", font=f, fill=(240, 220, 160))
        import textwrap
        for k, ln in enumerate(textwrap.wrap(caption, 56)[:2]):
            d.text((x, y + 292 + k * 15), ln, font=f, fill=(190, 190, 200))
    sheet.save(path)


if __name__ == "__main__":
    items = build()
    storyboard(items, f"{ROOT}/mockups/STORYBOARD.png")
