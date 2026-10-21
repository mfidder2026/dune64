/* vm.c - verhaal-VM. "Blocking per instructie": TEXT en MENU wachten intern per frame
   (animatie + invoer). Formaat en opcodes: DESIGN.md §9.2 en de kop van pipeline/scriptc.py. */
#include <zlib.h>
#include "gfx.h"
#include "ui.h"
#include "disk.h"
#include "game.h"
#include "sim.h"
#include "text.h"
#include "builtin.h"
#include "vm.h"
#include "sound.h"

#define MAGIC_SCRIPT   0x54        /* 'T' */
#define BUILTIN_TARGET 0xFF00      /* menu-doel $FFxx = builtin xx */
#define HERE_LOC       0xFF        /* cond $05: huidige locatie */

enum {
    OP_SCENE = 0x01, OP_CHAR, OP_SAY, OP_TEXT, OP_MENU, OP_JUMP, OP_IF, OP_SET, OP_CLR,
    OP_ADD, OP_CALL, OP_WAIT, OP_TIENDE, OP_ONDAY, OP_LOAD, OP_MUSIC, OP_SKIP, OP_TRUST,
    OP_LOCSTATUS, OP_LET,
    OP_END = 0xFF
};

#define MAX_OPTS 16

noderef_t vm_next;

static unsigned char* pc;
static unsigned int   cur_node;
static noderef_t      home;                    /* node van het laatste MENU: doel van END */
static unsigned char  cur_script, cur_scene, cur_char, screen_pending;

static void fail(unsigned char code)
{
    /* rode rand + foutcode als dagteller: zichtbaar in VICE-screenshots */
    *(unsigned char*)0xD020 = 2;
    ui_status(code, (unsigned int)(pc - SCRIPTBUF), 0, 0, 0);
    for (;;) ;
}

static unsigned int rd16(void)
{
    unsigned int v = pc[0] | ((unsigned int)pc[1] << 8);
    pc += 2;
    return v;
}

/* ------------------------------------------------------------------ blokken en sprongen */

/* De ON_DAY-tabel in de blokkop wordt niet gebruikt: game_init() zet alle tijd-events
   klaar uit init_events[], zodat een afgevuurd event niet terugkomt als het blok opnieuw laadt. */
static void load_script(unsigned char sid)
{
    if (sid == cur_script) return;
    if (!disk_load(script_files[lang][sid], LOADBUF) || LOADBUF[0] != MAGIC_SCRIPT) fail(1);
    sound_hold(1);
    inflatemem(SCRIPTBUF, LOADBUF + 4);
    sound_hold(0);
    cur_script = sid;
}

static void jump(unsigned int node)
{
    cur_node = node;
    pc = SCRIPTBUF + node;
}

static void go(const noderef_t* n)
{
    load_script(n->script);
    jump(n->node);
}

/* Na een builtin of menu-keuze: eerst een event van de simulatie (Tiende, game over),
   dan een sprong die de builtin vroeg (aankomst na een reis). 1 = er is gesprongen. */
static unsigned char redirect(void)
{
    noderef_t n;
    if (vm_next.script != NO_SCRIPT) {
        home = vm_next;                     /* END in het event: naar de aankomst-node */
        vm_next.script = NO_SCRIPT;
    }
    if (sim_pending.script != NO_SCRIPT) {
        n = sim_pending;
        sim_pending.script = NO_SCRIPT;
        go(&n);
        return 1;
    }
    if (home.script != cur_script || home.node != cur_node) {
        go(&home);
        return 1;
    }
    return 0;
}

/* ------------------------------------------------------------------ condities */

static unsigned char cond(void)
{
    unsigned char a, b;
    unsigned int v;
    switch (*pc++) {
    case 0x00: return 1;
    case 0x01: return flag_get(*pc++) != 0;
    case 0x02: return flag_get(*pc++) == 0;
    case 0x03: a = *pc++; v = rd16(); return vars[a] >= v;
    case 0x04: a = *pc++; v = rd16(); return vars[a] < v;
    case 0x05:
        a = *pc++; b = *pc++;
        if (a == HERE_LOC) a = (unsigned char)vars[VAR_LOC];
        return locs[a].status == b;
    case 0x06: a = *pc++; b = *pc++; return vars[a] >= vars[b];
    case 0x07: a = *pc++; b = *pc++; return vars[a] < vars[b];
    case 0x08: a = cond(); b = cond(); return a && b;    /* beide evalueren: pc moet door */
    case 0x09: a = *pc++; v = rd16(); return vars[a] == v;
    case 0x0A: return !cond();
    case 0x0B: return HERE->trust >= *pc++;
    case 0x0C: return HERE->green >= *pc++;
    }
    fail(2);
    return 0;
}

/* ------------------------------------------------------------------ scène en personage */

void vm_show(void)
{
    if (!screen_pending) return;
    ui_wait_frame();
    screen_on = 0x10;
    ui_globe(split_enabled);
    screen_pending = 0;
}

void vm_forget_scene(void)
{
    cur_scene = cur_char = 0;
    txt_mouth = 0;
}

void vm_set_lang(unsigned char l)
{
    lang = l;
    game_draw_status();                   /* DAG / DAY */
    if (cur_script == NO_SCRIPT) return;
    vm_next.script = cur_script;          /* na de builtin: menu-node opnieuw, in de nieuwe taal */
    vm_next.node = home.node;
    cur_script = NO_SCRIPT;
}

void vm_scene(unsigned char id)
{
    unsigned char rows;
    if (id == cur_scene) return;
    screen_on = 0;                     /* beeld uit tijdens laden en uitpakken */
    ui_globe(0);
    ui_wait_frame();
    rows = gfx_load_scene(scene_files[id]);
    if (!rows) fail(3);
    cur_scene = id;
    cur_char = 0;
    txt_mouth = 0;
    split_enabled = (rows != 25);
    if (split_enabled) {
        ui_draw_frame();
        game_draw_status();
    }
    screen_pending = 1;                /* aan bij de eerste instructie die iets toont */
}

void vm_char(unsigned char id)
{
    unsigned char s;
    if (id == cur_char) return;
    txt_clear();                       /* oude tekst hoort bij het oude personage */
    if (cur_char) {                    /* oud personage weg: scène opnieuw laden */
        s = cur_scene;
        cur_scene = 0;
        vm_scene(s);
    }
    if (id) {
        if (gfx_load_patch(char_files[id]) < 4) fail(4);
        gfx_apply_patch(0);            /* lichaam */
        gfx_apply_patch(1);            /* mond dicht */
        cur_char = id;
        txt_mouth = 1;
    }
}

/* ------------------------------------------------------------------ menu */

static void op_menu(void)
{
    static const unsigned char* items[MAX_OPTS];
    static unsigned int targets[MAX_OPTS];
    unsigned char n = *pc++, k = 0, i, ok;
    unsigned int str, target;

    vm_show();
    home.script = cur_script;
    home.node = cur_node;
    for (i = 0; i < n; ++i) {
        ok = cond();
        str = rd16();
        target = rd16();
        if (ok && k < MAX_OPTS) { items[k] = SCRIPTBUF + str; targets[k] = target; ++k; }
    }
    if (!k) fail(5);
    ui_menu_keys = 1;
    i = ui_menu(items, k);
    ui_menu_keys = 0;
    txt_clear();
    if (i == MENU_KEY_DISK || i == MENU_KEY_MAP) {      /* F7: schijfmenu, K: kaart */
        if (i == MENU_KEY_MAP && !flag_get(FLAG_GLIDER)) { jump(cur_node); return; }
        builtin(i == MENU_KEY_DISK ? BI_OPSLAAN : BI_KAART);
        if (!redirect()) jump(cur_node);
        return;
    }
    target = targets[i];
    if (target >= BUILTIN_TARGET) {
        builtin((unsigned char)target);
        if (!redirect()) jump(cur_node);   /* opnieuw: menu bijwerken */
    } else {
        jump(target);
    }
}

/* ------------------------------------------------------------------ hoofdlus */

void vm_run(unsigned char script, unsigned int node)
{
    unsigned char a;
    unsigned int v;

    cur_script = NO_SCRIPT;
    screen_pending = 0;
    vm_next.script = NO_SCRIPT;
    sim_pending.script = NO_SCRIPT;
    load_script(script);
    if (node == NODE_START) node = SCRIPTBUF[0] | ((unsigned int)SCRIPTBUF[1] << 8);
    jump(node);
    home.script = script;
    home.node = node;

    for (;;) {
        switch (*pc++) {
        case OP_SCENE: vm_scene(*pc++); break;
        case OP_CHAR:  vm_char(*pc++); break;
        case OP_SAY:   vm_show(); txt_say(SCRIPTBUF + rd16()); break;
        case OP_TEXT:  vm_show(); txt_begin(); txt_sc(SCRIPTBUF + rd16()); txt_show(); break;
        case OP_MENU:  op_menu(); break;
        case OP_JUMP:  jump(rd16()); break;
        case OP_IF:    a = cond(); v = rd16(); if (!a) pc += v; break;
        case OP_SKIP:  v = rd16(); pc += v; break;
        case OP_SET:   flag_set(*pc++); break;
        case OP_CLR:   flag_clr(*pc++); break;
        case OP_ADD:   a = *pc++; vars[a] += rd16(); game_draw_status(); break;
        case OP_TRUST:
            a = *pc++;
            v = HERE->trust + (signed char)a;
            HERE->trust = ((int)v < 0) ? 0 : (v > 100) ? 100 : (unsigned char)v;
            break;
        case OP_LOCSTATUS:
            a = *pc++;
            if (a == HERE_LOC) a = (unsigned char)vars[VAR_LOC];
            locs[a].status = *pc++;
            sim_update_totals();
            break;
        case OP_LET:   a = *pc++; vars[a] = rd16(); game_draw_status(); break;
        case OP_CALL:
            builtin(*pc++);
            if (vm_next.script != NO_SCRIPT || sim_pending.script != NO_SCRIPT) redirect();
            break;
        case OP_WAIT:  vm_show(); for (a = *pc++; a; --a) ui_wait_frame(); break;
        case OP_TIENDE:
            vars[VAR_TIENDE_EIS] = rd16();
            vars[VAR_TIENDE_DAG] = vars[VAR_DAY] + *pc++;
            flag_set(FLAG_TIENDE_OPEN);
            flag_clr(FLAG_TIENDE_UITSTEL);
            break;
        case OP_ONDAY:
            v = rd16(); a = *pc++;
            game_add_event(v, a, rd16());
            break;
        case OP_LOAD:
            a = *pc++; v = rd16();
            load_script(a);
            jump(v);
            break;
        case OP_MUSIC: ++pc; break;    /* fase 5 */
        case OP_END:   go(&home); break;
        default:       --pc; fail(6);
        }
    }
}
