/* map.c - kaartscherm (DESIGN.md §4.2). Markers overschrijven een hele cel van de kaartscène;
   de scène wordt bij vertrek opnieuw geladen, dus terugzetten is niet nodig. */
#include <stdlib.h>
#include <string.h>
#include "gfx.h"
#include "ui.h"
#include "game.h"
#include "sim.h"
#include "text.h"
#include "vm.h"
#include "flight.h"
#include "map.h"

#define COL_BLACK  0
#define COL_WHT    1
#define COL_RED    2
#define COL_CYAN   3
#define COL_PURPLE 4
#define COL_GRN    5
#define COL_YEL    7
#define COL_LGR    15

#define DISCOVER_RANGE 4       /* cellen van de rechte lijn (Manhattan) */
#define DAY_FRAMES     75      /* vluchtanimatie per reisdag (1,5 s) */

/* MARKER uit pipeline/mockups.py: %11 = kleur-RAM (markerkleur), %01 = scherm-RAM hoog (binnenkleur) */
static const unsigned char marker_bm[8] = { 0x00, 0x3C, 0xD7, 0xD7, 0xD7, 0x3C, 0x00, 0x00 };
static const unsigned char sc_back[NLANGS][6] = { { 20, 5, 18, 21, 7, SC_END }, { 2, 1, 3, 11, SC_END } };  /* terug / back */

static unsigned char dest_idx[NLOCS + 1];
static const unsigned char* items[NLOCS + 1];
static unsigned char n_items, last_sel, blink_on;

static unsigned char marker_color(unsigned char i)
{
    const loc_t* l = &locs[i];
    if (l->status == ST_BEZET) return (l->type == LT_FORT) ? COL_RED : COL_PURPLE;
    if (l->type == LT_KAMP && l->green >= 60) return COL_GRN;
    switch (l->type) {
    case LT_FORT:     return COL_WHT;
    case LT_VOORPOST:
    case LT_CITADEL:  return COL_RED;
    case LT_HANDEL:   return COL_CYAN;
    }
    switch (l->status) {
    case ST_BONDGENOOT: return COL_YEL;
    case ST_BEZET:      return COL_PURPLE;
    case ST_GROEN:      return COL_GRN;
    }
    return COL_LGR;
}

static unsigned int cell(unsigned char i)
{
    return locs[i].y * 40 + locs[i].x;
}

static void draw_marker(unsigned char i)
{
    unsigned int c = cell(i);
    unsigned char inner = COL_BLACK;
    if (locs[i].type == LT_FORT) inner = COL_YEL;
    if (i == (unsigned char)vars[VAR_LOC]) inner = COL_WHT;   /* hier ben je */
    memcpy(BITMAP + (c << 3), marker_bm, 8);
    SCREEN[c] = inner << 4;
    COLRAM[c] = marker_color(i);
}

static void set_blink(unsigned char sel, unsigned char on)
{
    if (sel < n_items - 1) COLRAM[cell(dest_idx[sel])] = on ? marker_color(dest_idx[sel]) : COL_BLACK;
}

static unsigned char distance(unsigned char a, unsigned char b)
{
    return (unsigned char)(abs((int)locs[a].x - locs[b].x) + abs((int)locs[a].y - locs[b].y));
}

static unsigned char travel_days(unsigned char a, unsigned char b)
{
    unsigned char d = (distance(a, b) + 9) / 10;
    return d ? d : 1;
}

/* menu-hook: knipperende bestemming (16 frames) en reisduur in de kopregel */
static void hook(unsigned char sel)
{
    if (sel != last_sel) {
        set_blink(last_sel, 1);
        last_sel = sel;
        txt_title(L(L("BESTEMMING", "DESTINATION"), "DESTINATION"));
        if (sel < n_items - 1) {
            ui_number(0, 12, travel_days((unsigned char)vars[VAR_LOC], dest_idx[sel]), COL_WHITE);
            ui_text_at(0, 14, L("dagen", "days"), COL_WHITE);
        }
    }
    if ((frame_count & 15) == 0) {
        blink_on ^= 1;
        set_blink(sel, blink_on);
    }
}

/* Onbekend kamp binnen DISCOVER_RANGE van de lijn a-b dat deze reis ontdekt wordt, of MAP_CANCEL. */
static unsigned char discover(unsigned char a, unsigned char b)
{
    int ax = locs[a].x, ay = locs[a].y, dx = (int)locs[b].x - ax, dy = (int)locs[b].y - ay;
    int steps = abs(dx) > abs(dy) ? abs(dx) : abs(dy), s, x, y;
    unsigned char i, chance;
    const loc_t* l;
    if (!steps) return MAP_CANCEL;
    for (i = 0; i < NLOCS; ++i) {
        l = &locs[i];
        if (l->type != LT_KAMP || l->status != ST_ONBEKEND) continue;
        for (s = 0; s <= steps; ++s) {
            x = ax + dx * s / steps;
            y = ay + dy * s / steps;
            if (abs(l->x - x) + abs(l->y - y) <= DISCOVER_RANGE) break;
        }
        if (s > steps) continue;
        chance = 25;
        if (flag_get(FLAG_SAIRA_MEE)) chance += 25;
        if (l->flags & LF_LICHTEND) chance += 15;
        if ((unsigned char)(rand() % 100) < chance) return i;
    }
    return MAP_CANCEL;
}

static const char* const land_items[NLANGS][2] = { { "Landen", "Doorvliegen" }, { "Land", "Fly on" } };

static unsigned char fast;          /* vuur tijdens de vlucht: rest van de reis zonder animatie */

static void flight_panel(unsigned char to)
{
    txt_title(L("ONDERWEG NAAR", "FLYING TO"));
    txt_clear();
    ui_line(1, 0, loc_names[lang][to], COL_WHITE);
}

/* Reisdagen first..last-1 van een reis van `days` dagen: per dag sim_day() en de animatie.
   Nacht in de tweede helft van de reis (cosmetisch, §4.1). */
static void fly(unsigned char first, unsigned char last, unsigned char days)
{
    unsigned char d;
    for (d = first; d < last; ++d) {
        vars[VAR_NACHT] = (d * 2 + 1 >= days) && days > 1;
        flight_night((unsigned char)vars[VAR_NACHT]);
        sim_day();
        if (!fast && flight_frames(DAY_FRAMES)) fast = 1;
    }
}

static unsigned char travel(unsigned char from, unsigned char to)
{
    unsigned char days = travel_days(from, to), half, hit;

    fast = 0;
    hit = discover(from, to);
    flight_begin();
    flight_panel(to);
    if (hit == MAP_CANCEL) {
        fly(0, days, days);
    } else {
        half = days / 2;
        fly(0, half, days);
        if (!half && !fast) flight_frames(DAY_FRAMES);   /* altijd even vliegen voor de ontdekking */
        vm_scene(SCENE_WOESTIJN);
        vm_show();
        txt_title(L("ONDERWEG", "EN ROUTE"));
        txt_begin();
        txt_str(L("De glider scheert over de duinen. Tussen de rotsen stijgt rook op: een kamp van de Kethari.", "The glider skims over the dunes. Smoke rises between the rocks: a Kethari camp."));
        if (flag_get(FLAG_SAIRA_MEE)) txt_str(L(" Saira wijst: daar!", " Saira points: there!"));
        txt_show();
        if (ui_menu_str(land_items[lang], 2) == 0) {
            locs[hit].status = ST_BEKEND;
            to = hit;
            if (!half) fly(0, 1, 1);                      /* landen kost minstens een dag */
        } else {
            flight_begin();
            flight_panel(to);
            fly(half, days, days);
        }
    }
    vars[VAR_NACHT] = 0;
    flight_night(0);
    game_draw_status();
    return to;
}

unsigned char map_run(void)
{
    unsigned char i, here = (unsigned char)vars[VAR_LOC], sel;

    vm_char(0);
    vm_scene(SCENE_KAART);
    n_items = 0;
    for (i = 0; i < NLOCS; ++i) {
        if (locs[i].status == ST_ONBEKEND) continue;
        draw_marker(i);
        if (i == here) continue;
        dest_idx[n_items] = i;
        items[n_items++] = loc_names[lang][i];
    }
    items[n_items++] = sc_back[lang];
    vm_show();

    last_sel = 0xFE;
    blink_on = 1;
    ui_menu_hook = hook;
    sel = ui_menu(items, n_items);
    ui_menu_hook = 0;
    set_blink(sel, 1);
    if (sel == n_items - 1) return MAP_CANCEL;
    return travel(here, dest_idx[sel]);
}
