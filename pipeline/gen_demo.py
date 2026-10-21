#!/usr/bin/env python3
"""gen_demo.py - genereert C-headers voor de schermen-demo uit ui.py en het storyboard."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import ui as U
import mockups as M

SRC = os.path.join(U.ROOT, "demo", "src")
GAME_SRC = os.path.join(U.ROOT, "src")


def c_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    for d in (SRC, GAME_SRC):
        os.makedirs(d, exist_ok=True)
        with open(f"{d}/ui_codes.h", "w") as f:
            f.write("/* gegenereerd door pipeline/gen_demo.py - niet met de hand wijzigen */\n#ifndef ASHKARA_UI_CODES_H\n#define ASHKARA_UI_CODES_H\n")
            for k, v in {**U.FRAME_CODES, **U.HIRES_CODES}.items():
                f.write(f"#define UI_{k:<6s} {v}\n")
            f.write(f"#define GLOBE_X    {U.SPRITE_X + 24}\n#define GLOBE_Y    {U.SPRITE_Y + 50}\n#define GLOBE_PTR0 16\n#endif\n")
    with open(f"{SRC}/slides.h", "w") as f:
        f.write("/* gegenereerd door pipeline/gen_demo.py uit het storyboard (pipeline/mockups.py) */\n")
        f.write("typedef struct {\n    const char* scene; const char* patch;\n    const char* lines[6]; unsigned char colors[6];\n"
                "    unsigned int day, amber, warriors; unsigned char green, night;\n} slide_t;\n\n")
        f.write("static const slide_t slides[] = {\n")
        for sid, scene, char, mouth, lines, status, caption in M.STORY:
            patch = c_str(char.lower() + ".pat") if char else "0"
            lines = lines or []
            ls = [c_str(t) for t, _ in lines] + ["0"] * (6 - len(lines))
            cs = [str(c) for _, c in lines] + ["1"] * (6 - len(lines))
            st = status or dict(dag=0, amber=0, krijgers=0, groen=0)
            f.write(f"  /* {sid} */ {{ {c_str(scene.lower() + '.scn')}, {patch},\n    {{ {', '.join(ls)} }},\n"
                    f"    {{ {', '.join(cs)} }}, {st['dag']}, {st['amber']}, {st['krijgers']}, {st.get('groen', 0)}, {st.get('nacht', 0)} }},\n")
        f.write("};\n#define NSLIDES (sizeof(slides) / sizeof(slides[0]))\n")
    print("headers geschreven in", SRC)


if __name__ == "__main__":
    main()
