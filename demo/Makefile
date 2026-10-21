# ASHKARA schermen-demo
# Vereist: cc65 (cl65) en Python 3 met Pillow + numpy. VICE (x64sc, c1541) voor testen.
# Eenvoudiger (ook op Windows): python build.py  (zoekt cc65/VICE zelf in ./tools of ../tools)
CL65   ?= cl65
PYTHON ?= python3
X64    ?= x64sc
ASSETS := ../assets
SRC    := src/main.c src/gfx.c src/ui.c src/irq.s
FILES  := ashkara $(addprefix $(ASSETS)/, ui.chr globe.spr titel.scn ruimte.scn raadzaal.scn balkon.scn comms.scn \
          hangar.scn kaart.scn woestijn.scn kloof.scn grot.scn oogst.scn nacht.scn storm.scn vesting.scn oase.scn einde.scn \
          doran.pat vesna.pat vorr.pat mardo.pat saira.pat tarik.pat)

all: ashkara-demo.d64

ashkara: $(SRC) src/gfx.h src/ui.h src/ui_codes.h src/slides.h dune64.cfg
	$(CL65) -t c64 -O -C dune64.cfg -m ashkara.map -o $@ $(SRC)

ashkara-demo.d64: ashkara
	$(PYTHON) ../pipeline/mkd64.py $@ "ASHKARA DEMO,A1" $(FILES)

run: ashkara-demo.d64
	$(X64) -autostart ashkara-demo.d64

clean:
	rm -f ashkara ashkara.map ashkara-demo.d64 src/*.o
