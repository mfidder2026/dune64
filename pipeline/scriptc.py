#!/usr/bin/env python3
"""
scriptc.py - compiler voor de verhaalscripts van ASHKARA (DESIGN.md §9).

  python scriptc.py                 script/*.ash + data/locations.json -> assets/<naam>.scr, src/ids.h, src/data.c
  python scriptc.py --check         alleen controleren, niets schrijven

Invoer: script/ids.txt (namen -> id's), script/<naam>.ash per scriptblok uit ids.txt en
data/locations.json (via datac.py; elke locatie verwijst naar een script-node).
Uitvoer per blok: PRG (laadadres $B000) met container 'T', flags, size (LE16), deflate(raw).

raw-blok (alle pointers relatief t.o.v. het begin van raw):
  0  first_node (2)          node waar het blok begint (eerste node in het bestand)
  2  n_ondays (1)            tijd-events op topniveau (ON_DAY buiten een node)
  3  n x [dag (2), script-id (1), node (2)]
  .. code, daarna strings

Strings: screen codes. TEXT wordt door de ENGINE afgebroken en gepagineerd (zodat getallen en
namen erin kunnen); de compiler controleert alleen de woordlengte. In TEXT/SAY:
  $FE nieuwe regel ('|')   $FD nieuwe pagina ('||')   $FF einde
  $FC var  getal uit een variabele ('{amber}')   $FB naam van de huidige locatie ('{loc}')

Afwijkingen/aanvullingen op de tabel in §9.2 (bewust, zie DESIGN.md):
  ONDAY  dag (2), script-id (1), node (2)  - het doel mag in een ander blok liggen
  MENU-doel $FFxx = builtin xx (CALL), daarna terug naar de menu-node
  JUMP naar een node in een ander blok wordt LOAD script-id node
  SKIP   offset (2)          relatieve sprong vooruit (ELSE); JUMP is voor nodes
  TRUST  delta (1, signed)   vertrouwen van het kamp op de huidige locatie (0..100)
  cond $06 var var2 (>=)  $07 var var2 (<)  $08 c1 c2 (EN)  $09 var waarde16 (=)
       $0A c (NIET)  $0B n (vertrouwen huidige locatie >= n)
       $05 loc status: loc $FF = huidige locatie
"""
import os, re, sys, zlib, struct, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import datac

OP = dict(SCENE=0x01, CHAR=0x02, SAY=0x03, TEXT=0x04, MENU=0x05, JUMP=0x06, IF=0x07, SET=0x08, CLR=0x09,
          ADD=0x0A, CALL=0x0B, WAIT=0x0C, TIENDE=0x0D, ONDAY=0x0E, LOAD=0x0F, MUSIC=0x10, SKIP=0x11,
          TRUST=0x12, END=0xFF)
BUILTINS = ["KAART", "TIENDE", "WERVEN", "TAAK", "GEVECHT", "HANDEL", "OPSLAAN", "EINDE",
            "STATUS", "RUST", "GESCHENK", "PRAAT", "GAMEOVER"]
CAMP_STATUS = datac.LOC_STATUS
TEXT_W = 25          # kolom 26 blijft vrij voor het ▼-teken
LINE_W = 26          # SAY
OPT_W = 24           # "> " + optie
VAR_W = 5            # breedte van een getal ({var}) bij de controles
BLOCK_MAX = 4096     # SCRIPTBUF
LOAD_ADDR = 0xB000
NL, NP, EOS, ESC_VAR, ESC_LOC = 0xFE, 0xFD, 0xFF, 0xFC, 0xFB
BUILTIN_TARGET = 0xFF00
HERE_LOC = 0xFF


class ScriptError(Exception):
    pass


# ------------------------------------------------------------------ tekst

def screen_codes(s, where):
    from ui import HIRES_CODES, ACCENTS
    out = []
    for ch in s:
        o = ord(ch)
        if "a" <= ch <= "z": out.append(o - 96)
        elif "A" <= ch <= "Z": out.append(o)
        elif ch == "@": out.append(0)
        elif ch == "[": out.append(27)
        elif ch == "]": out.append(29)
        elif 32 <= o < 64: out.append(o)
        elif ch in ACCENTS: out.append(HIRES_CODES[ACCENTS[ch]])
        else: raise ScriptError(f"{where}: teken {ch!r} zit niet in de charset")
    return out


ESCAPE = re.compile(r"\{(\w+)\}")


class TextEncoder:
    def __init__(self, ids):
        self.ids = ids

    def piece(self, s, where):
        """Tekst met {var}/{loc} -> (bytes, zichtbare breedte in het ergste geval)."""
        out, width, pos = [], 0, 0
        for m in ESCAPE.finditer(s):
            out += screen_codes(s[pos:m.start()], where); width += m.start() - pos
            name = m.group(1)
            if name == "loc":
                out.append(ESC_LOC); width += datac.NAME_MAX
            elif name in self.ids["var"]:
                out += [ESC_VAR, self.ids["var"][name]]; width += VAR_W
            else:
                raise ScriptError(f"{where}: onbekende variabele {{{name}}}")
            pos = m.end()
        out += screen_codes(s[pos:], where); width += len(s) - pos
        return out, width

    def text(self, text, where):
        out = []
        for pi, page in enumerate(text.split("||")):
            if pi: out.append(NP)
            for li, line in enumerate(page.split("|")):
                if li: out.append(NL)
                for wi, word in enumerate(line.split()):
                    codes, w = self.piece(word, where)
                    if w > TEXT_W:
                        raise ScriptError(f"{where}: woord langer dan {TEXT_W} tekens: {word!r}")
                    if wi: out.append(32)
                    out += codes
        return bytes(out + [EOS])

    def line(self, text, width, where, escapes=True):
        codes, w = self.piece(text, where) if escapes else (screen_codes(text, where), len(text))
        if w > width:
            raise ScriptError(f"{where}: tekst langer dan {width} tekens: {text!r}")
        return bytes(codes + [EOS])


# ------------------------------------------------------------------ ids

def load_ids(path):
    ids = {k: {} for k in ("scene", "char", "script", "var", "flag", "node")}
    base = dict(scene=1, char=1, script=0, var=0, flag=0, node=0)
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.split(";", 1)[0].strip()
        if not line: continue
        parts = line.split()
        if len(parts) != 2 or parts[0] not in ids:
            raise ScriptError(f"ids.txt:{n}: verwacht '<soort> <naam>'")
        kind, name = parts
        if name in ids[kind]:
            raise ScriptError(f"ids.txt:{n}: {kind} {name} staat er dubbel in")
        ids[kind][name] = base[kind] + len(ids[kind])
    if len(ids["var"]) > 32: raise ScriptError("ids.txt: meer dan 32 variabelen")
    if len(ids["flag"]) > 256: raise ScriptError("ids.txt: meer dan 256 vlaggen")
    return ids


# ------------------------------------------------------------------ parser

TOKEN = re.compile(r'"([^"]*)"|(\S+)')


def tokenize(line):
    """Splitst een regel in tokens; strings worden ('str', tekst). ';' buiten strings = commentaar."""
    toks = []
    for m in TOKEN.finditer(line):
        if m.group(1) is not None:
            toks.append(("str", m.group(1)))
        else:
            w = m.group(2)
            if w.startswith(";"): break
            toks.append(w)
    return toks


class Block:
    def __init__(self, name, sid, path):
        self.name, self.sid, self.path = name, sid, path
        self.code = bytearray()
        self.nodes = {}            # naam -> code-offset
        self.node_order = []
        self.fix_node = []         # (pos, node, where)  -> absolute raw-offset van node (in welk blok dan ook)
        self.fix_str = []          # (pos, bytes)
        self.ondays = []           # (dag, node, where)
        self.edges = []            # (van, naar) voor de scriptgraaf
        self.raw = None


class Compiler:
    def __init__(self, ids, locs):
        self.ids = ids
        self.locs = locs
        self.loc_index = {l["id"]: i for i, l in enumerate(locs)}
        self.enc = TextEncoder(ids)
        self.blocks = []
        self.node_block = {}       # node -> Block

    def err(self, where, msg):
        raise ScriptError(f"{where}: {msg}")

    def lookup(self, kind, name, where):
        if name not in self.ids[kind]:
            self.err(where, f"onbekende {kind} '{name}' (voeg toe aan script/ids.txt)")
        return self.ids[kind][name]

    def node_ref(self, node):
        """(script-id, raw-offset) van een node; pas geldig na compile_block van alle blokken."""
        b = self.node_block[node]
        return b.sid, self.header_size(b) + b.nodes[node]

    # -- condities
    def cond(self, toks, where):
        if not toks: return bytes([0x00])
        if "AND" in toks:
            i = toks.index("AND")
            return bytes([0x08]) + self.cond(toks[:i], where) + self.cond(toks[i + 1:], where)
        if toks[0] == "NOT":
            if len(toks) == 2 and toks[1] in self.ids["flag"]:
                return bytes([0x02, self.ids["flag"][toks[1]]])
            return bytes([0x0A]) + self.cond(toks[1:], where)
        if toks[0] == "KAMP":
            if len(toks) != 4 or toks[2] != "=" or toks[3] not in CAMP_STATUS:
                self.err(where, "verwacht: KAMP HIER|<locatie-id> = " + "|".join(CAMP_STATUS))
            if toks[1] == "HIER": loc = HERE_LOC
            elif toks[1] in self.loc_index: loc = self.loc_index[toks[1]]
            else: self.err(where, f"onbekende locatie '{toks[1]}' (zie data/locations.json)")
            return bytes([0x05, loc, CAMP_STATUS.index(toks[3])])
        if toks[0] == "VERTROUWEN":
            if len(toks) != 3 or toks[1] != ">=": self.err(where, "verwacht: VERTROUWEN >= <n>")
            return bytes([0x0B, int(toks[2])])
        if len(toks) == 1:
            return bytes([0x01, self.lookup("flag", toks[0], where)])
        if len(toks) == 3 and toks[1] in (">=", "<", "="):
            v = self.lookup("var", toks[0], where)
            if re.fullmatch(r"-?\d+", toks[2]):
                op = {">=": 0x03, "<": 0x04, "=": 0x09}[toks[1]]
                return bytes([op, v]) + struct.pack("<H", int(toks[2]) & 0xFFFF)
            if toks[1] == "=": self.err(where, "= alleen met een getal")
            v2 = self.lookup("var", toks[2], where)
            return bytes([0x06 if toks[1] == ">=" else 0x07, v, v2])
        self.err(where, "onbekende conditie: " + " ".join(t if isinstance(t, str) else '"..."' for t in toks))

    def string_tok(self, toks, i, where):
        if i >= len(toks) or not isinstance(toks[i], tuple):
            self.err(where, "tekst tussen aanhalingstekens verwacht")
        return toks[i][1]

    # -- code-emissie
    def emit_node_ref(self, blk, node, where):
        blk.fix_node.append((len(blk.code), node, where))
        blk.code += b"\0\0"

    def emit_str(self, blk, data):
        blk.fix_str.append((len(blk.code), data))
        blk.code += b"\0\0"

    def emit_jump(self, blk, node, cur, where):
        if node not in self.node_block: self.err(where, f"onbekende node '{node}'")
        blk.edges.append((cur, node))
        target = self.node_block[node]
        if target is blk:
            blk.code.append(OP["JUMP"]); self.emit_node_ref(blk, node, where)
        else:
            blk.code += bytes([OP["LOAD"], target.sid]); self.emit_node_ref(blk, node, where)

    def compile_block(self, blk):
        lines = open(blk.path, encoding="utf-8").read().splitlines()
        cur = None                       # huidige node
        stack = []                       # open IF-blokken: [soort, pos_skip, else_pos, where]
        last_op = None
        menu = None
        fname = os.path.basename(blk.path)

        def close_node(where):
            if cur is not None and last_op not in ("JUMP", "MENU", "END", "LOAD"):
                blk.code.append(OP["END"])        # val nooit door naar de volgende node

        for n, raw in enumerate(lines, 1):
            where = f"{fname}:{n}"
            toks = tokenize(raw)
            if not toks: continue
            head = toks[0] if isinstance(toks[0], str) else None
            if head is None: self.err(where, "regel begint met een string")

            if menu is not None:        # binnen MENU ... END
                if head == "END":
                    if not menu: self.err(where, "MENU zonder opties")
                    blk.code += bytes([OP["MENU"], len(menu)])
                    for text, target, cond, w in menu:
                        blk.code += cond
                        self.emit_str(blk, self.enc.line(text, OPT_W, w, escapes=False))
                        if target.startswith("@"):
                            if target[1:] not in BUILTINS: self.err(w, f"onbekende builtin {target}")
                            blk.code += struct.pack("<H", BUILTIN_TARGET | BUILTINS.index(target[1:]))
                        else:
                            if target not in self.node_block: self.err(w, f"onbekende node '{target}'")
                            if self.node_block[target] is not blk:
                                self.err(w, f"menu-doel '{target}' ligt in een ander blok; gebruik een node met JUMP")
                            blk.edges.append((cur, target))
                            self.emit_node_ref(blk, target, w)
                    menu = None; last_op = "MENU"
                    continue
                if head != "OPT": self.err(where, "binnen MENU alleen OPT of END")
                text = self.string_tok(toks, 1, where)
                if len(toks) < 3 or not isinstance(toks[2], str): self.err(where, "OPT \"tekst\" <doel> [IF cond]")
                cond = b"\0"
                if len(toks) > 3:
                    if toks[3] != "IF": self.err(where, "na het doel alleen IF <cond>")
                    cond = self.cond(toks[4:], where)
                menu.append((text, toks[2], cond, where))
                if len(menu) > 16: self.err(where, "meer dan 16 opties in een MENU")
                continue

            if head.startswith(":"):
                if stack: self.err(where, f"node begint terwijl {stack[-1][0]} nog open staat")
                close_node(where)
                cur = head[1:]
                blk.nodes[cur] = len(blk.code); blk.node_order.append(cur)
                last_op = None
                continue

            if head == "ON_DAY" and cur is None:
                if len(toks) != 3: self.err(where, "ON_DAY <dag> <node>")
                blk.ondays.append((int(toks[1]), toks[2], where))
                continue

            if cur is None: self.err(where, "instructie buiten een node")
            op = head
            if op == "SCENE":
                blk.code += bytes([OP[op], self.lookup("scene", toks[1], where)])
                if not os.path.exists(f"{ROOT}/assets/{toks[1]}.scn"): self.err(where, f"assets/{toks[1]}.scn bestaat niet")
            elif op == "CHAR":
                cid = 0 if toks[1] == "none" else self.lookup("char", toks[1], where)
                if cid and not os.path.exists(f"{ROOT}/assets/{toks[1]}.pat"): self.err(where, f"assets/{toks[1]}.pat bestaat niet")
                blk.code += bytes([OP[op], cid])
            elif op == "SAY":
                blk.code.append(OP[op]); self.emit_str(blk, self.enc.line(self.string_tok(toks, 1, where), LINE_W, where))
            elif op == "TEXT":
                text = " ".join(self.string_tok(toks, i, where) for i in range(1, len(toks)))
                blk.code.append(OP[op]); self.emit_str(blk, self.enc.text(text, where))
            elif op == "MENU":
                menu = []
                continue
            elif op == "JUMP":
                self.emit_jump(blk, toks[1], cur, where)
            elif op == "IF":
                blk.code.append(OP["IF"]); blk.code += self.cond(toks[1:], where)
                stack.append(["IF", len(blk.code), None, where]); blk.code += b"\0\0"
            elif op == "ELSE":
                if not stack or stack[-1][0] != "IF" or stack[-1][2] is not None: self.err(where, "ELSE zonder IF")
                blk.code.append(OP["SKIP"]); jpos = len(blk.code); blk.code += b"\0\0"
                ent = stack[-1]
                skip = len(blk.code) - (ent[1] + 2)
                blk.code[ent[1]:ent[1] + 2] = struct.pack("<H", skip)
                ent[2] = jpos
            elif op == "END" and stack:
                kind, pos, else_pos, w0 = stack.pop()
                if else_pos is None:
                    blk.code[pos:pos + 2] = struct.pack("<H", len(blk.code) - (pos + 2))
                else:
                    blk.code[else_pos:else_pos + 2] = struct.pack("<H", len(blk.code) - (else_pos + 2))
                continue                   # last_op ongewijzigd: END sluit alleen het blok
            elif op in ("END", "RETURN"):
                blk.code.append(OP["END"]); op = "END"
            elif op in ("SET", "CLR"):
                blk.code += bytes([OP[op], self.lookup("flag", toks[1], where)])
            elif op == "ADD":
                blk.code += bytes([OP[op], self.lookup("var", toks[1], where)]) + struct.pack("<h", int(toks[2]))
            elif op == "TRUST":
                blk.code += bytes([OP[op]]) + struct.pack("<b", int(toks[1]))
            elif op == "CALL":
                if not toks[1].startswith("@") or toks[1][1:] not in BUILTINS: self.err(where, f"onbekende builtin {toks[1]}")
                blk.code += bytes([OP[op], BUILTINS.index(toks[1][1:])])
            elif op == "WAIT":
                blk.code += bytes([OP[op], int(toks[1])])
            elif op == "TIENDE":
                blk.code.append(OP[op]); blk.code += struct.pack("<HB", int(toks[1]), int(toks[2]))
            elif op == "ON_DAY":
                node = toks[2]
                if node not in self.node_block: self.err(where, f"onbekende node '{node}'")
                blk.code.append(OP["ONDAY"]); blk.code += struct.pack("<HB", int(toks[1]), self.node_block[node].sid)
                self.emit_node_ref(blk, node, where); blk.edges.append((cur, node))
                op = "ONDAY"
            elif op == "MUSIC":
                blk.code += bytes([OP[op], int(toks[1])])
            else:
                self.err(where, f"onbekende instructie '{op}'")
            last_op = op

        if menu is not None: self.err(fname, "MENU niet afgesloten met END")
        if stack: self.err(stack[-1][3], f"{stack[-1][0]} niet afgesloten met END")
        close_node(fname)
        if not blk.node_order: self.err(fname, "geen enkele node")

    def header_size(self, blk):
        return 3 + 5 * len(blk.ondays)

    def link(self, blk):
        hs = self.header_size(blk)
        code = bytearray(blk.code)
        strings = bytearray(); str_ofs = {}
        for pos, data in blk.fix_str:
            if data not in str_ofs:
                str_ofs[data] = len(strings); strings += data
            code[pos:pos + 2] = struct.pack("<H", hs + len(code) + str_ofs[data])
        for pos, node, where in blk.fix_node:
            code[pos:pos + 2] = struct.pack("<H", self.node_ref(node)[1])
        head = bytearray(struct.pack("<HB", hs + blk.nodes[blk.node_order[0]], len(blk.ondays)))
        for day, node, where in blk.ondays:
            if node not in self.node_block: self.err(where, f"onbekende node '{node}'")
            head += struct.pack("<HBH", day, *self.node_ref(node))
            blk.edges.append(("<ON_DAY>", node))
        raw = bytes(head + code + strings)
        if len(raw) > BLOCK_MAX:
            raise ScriptError(f"{blk.name}: blok is {len(raw)} bytes (max {BLOCK_MAX}); splits het hoofdstuk met LOAD")
        blk.raw = raw
        blk.stats = dict(code=len(code), strings=len(strings), total=len(raw))

    def compile(self, script_dir):
        for name, sid in sorted(self.ids["script"].items(), key=lambda kv: kv[1]):
            path = os.path.join(script_dir, name + ".ash")
            if not os.path.exists(path): raise ScriptError(f"script/{name}.ash ontbreekt (staat in ids.txt)")
            self.blocks.append(Block(name, sid, path))
        for blk in self.blocks:          # eerst alle node-namen verzamelen (sprongen tussen blokken)
            for n, line in enumerate(open(blk.path, encoding="utf-8"), 1):
                toks = tokenize(line)
                if toks and isinstance(toks[0], str) and toks[0].startswith(":"):
                    node = toks[0][1:]
                    if node in self.node_block:
                        raise ScriptError(f"{blk.name}.ash:{n}: node '{node}' bestaat al in {self.node_block[node].name}.ash")
                    self.node_block[node] = blk
        for name in self.ids["node"]:
            if name not in self.node_block: raise ScriptError(f"ids.txt: engine-node '{name}' bestaat in geen enkel script")
        for l in self.locs:
            if l["node"] not in self.node_block:
                raise ScriptError(f"locations.json: {l['id']}: node '{l['node']}' bestaat in geen enkel script")
        for blk in self.blocks: self.compile_block(blk)
        for blk in self.blocks: self.link(blk)
        used = ({b for blk in self.blocks for _, b in blk.edges} | {blk.node_order[0] for blk in self.blocks}
                | set(self.ids["node"]) | {l["node"] for l in self.locs})
        warnings = [f"waarschuwing: node '{n}' ({b.name}.ash) wordt nergens gebruikt"
                    for n, b in self.node_block.items() if n not in used]
        return warnings


def c_bytes(b):
    return ", ".join(f"0x{x:02X}" for x in b)


def write_outputs(comp, ids):
    os.makedirs(f"{ROOT}/assets", exist_ok=True); os.makedirs(f"{ROOT}/build", exist_ok=True)
    for blk in comp.blocks:
        z = zlib.compressobj(9, zlib.DEFLATED, -15)
        packed = z.compress(blk.raw) + z.flush()
        with open(f"{ROOT}/assets/{blk.name}.scr", "wb") as f:
            f.write(struct.pack("<HBBH", LOAD_ADDR, 0x54, 1, len(blk.raw)) + packed)
        s = blk.stats
        print(f"{blk.name}.scr: {s['total']} bytes (code {s['code']}, tekst {s['strings']}) -> {len(packed)} gecomprimeerd")
    with open(f"{ROOT}/build/script_graph.txt", "w", encoding="utf-8") as f:
        for blk in comp.blocks:
            f.write(f"[{blk.name}]\n")
            for node in blk.node_order:
                outs = sorted({b for a, b in blk.edges if a == node})
                f.write(f"  {node:20s} -> {', '.join(outs) or '(menu/einde)'}\n")
            for a, b in blk.edges:
                if a == "<ON_DAY>": f.write(f"  ON_DAY               -> {b}\n")

    locs = comp.locs
    with open(f"{ROOT}/src/ids.h", "w") as f:
        f.write("/* gegenereerd door pipeline/scriptc.py uit script/ids.txt en data/locations.json - niet met de hand wijzigen */\n")
        f.write("#ifndef ASHKARA_IDS_H\n#define ASHKARA_IDS_H\n")
        for kind in ("scene", "char", "script", "var", "flag"):
            for name, i in ids[kind].items():
                f.write(f"#define {kind.upper()}_{name.upper()} {i}\n")
        for name, i in ids["node"].items():
            f.write(f"#define ENODE_{name.upper()} {i}\n")
        for i, b in enumerate(BUILTINS):
            f.write(f"#define BI_{b} {i}\n")
        for i, l in enumerate(locs):
            f.write(f"#define LOC_{l['id'].upper()} {i}\n")
        for i, t in enumerate(datac.LOC_TYPES):
            f.write(f"#define LT_{t} {i}\n")
        for k, v in datac.LOC_FLAGS.items():
            f.write(f"#define LF_{k} 0x{v:02X}\n")
        f.write(f"#define NSCENES {len(ids['scene'])}\n#define NCHARS {len(ids['char'])}\n"
                f"#define NSCRIPTS {len(ids['script'])}\n#define NLOCS {len(locs)}\n#define NENODES {len(ids['node'])}\n")
        f.write("#endif\n")
    with open(f"{ROOT}/src/data.c", "w") as f:
        f.write("/* gegenereerd door pipeline/scriptc.py - niet met de hand wijzigen */\n#include \"game.h\"\n\n")
        for kind, ext in (("scene", "scn"), ("char", "pat"), ("script", "scr")):
            names = [f'"{n}.{ext}"' for n, _ in sorted(ids[kind].items(), key=lambda kv: kv[1])]
            if kind != "script": names = ["0"] + names       # id 0 = geen
            f.write(f"const char* const {kind}_files[] = {{ {', '.join(names)} }};\n")
        f.write("\n/* engine-nodes (ids.txt 'node') en aankomst-nodes per locatie: script-id, offset */\nconst noderef_t enodes[] = {\n")
        for name in ids["node"]:
            sid, ptr = comp.node_ref(name)
            f.write(f"    {{ {sid}, 0x{ptr:04X} }},   /* {name} */\n")
        f.write("};\nconst noderef_t loc_nodes[] = {\n")
        for l in locs:
            sid, ptr = comp.node_ref(l["node"])
            f.write(f"    {{ {sid}, 0x{ptr:04X} }},   /* {l['id']} -> {l['node']} */\n")
        f.write("};\n\n/* startwaarden: type, x, y, status, size, trust, job, skill, equip, richness, green, flags */\n")
        f.write("const loc_t loc_init[] = {\n" + "\n".join(datac.c_loc_init(locs)) + "\n};\n\n")
        f.write("/* namen in screen codes, $FF-afgesloten */\n")
        for i, l in enumerate(locs):
            f.write(f"static const unsigned char n{i}[] = {{ {c_bytes(screen_codes(l['name'], l['id']) + [EOS])} }};\n")
        f.write("const unsigned char* const loc_names[] = { " + ", ".join(f"n{i}" for i in range(len(locs))) + " };\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    try:
        ids = load_ids(f"{ROOT}/script/ids.txt")
        locs = datac.load_locations(f"{ROOT}/data/locations.json")
        comp = Compiler(ids, locs)
        for w in comp.compile(f"{ROOT}/script"): print(w)
    except (ScriptError, datac.DataError) as e:
        sys.exit(f"scriptfout: {e}")
    if not args.check:
        write_outputs(comp, ids)


if __name__ == "__main__":
    main()
