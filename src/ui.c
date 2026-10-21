/* ui.c - paneel tekenen. Tekst komt binnen als PETSCII (cc65-stringliterals) en wordt
   omgezet naar screen codes van de eigen charset (zie DESIGN.md §5.3). */
#include <string.h>
#include "gfx.h"
#include "ui.h"
#include "input.h"

#define PSCR (SCREEN + PANEL_ROW * 40)
#define PCOL (COLRAM + PANEL_ROW * 40)

extern unsigned char lang;          /* game.c */

static unsigned char petscii_to_screen(unsigned char c)
{
    if (c >= 0x40 && c < 0x60) return c - 0x40;   /* a-z (cc65 'a' -> $41) -> 1..26 */
    if (c >= 0xC0 && c < 0xE0) return c - 0x80;   /* A-Z (cc65 'A' -> $C1) -> 65..90 */
    if (c >= 0x20 && c < 0x40) return c;          /* spatie, cijfers, leestekens */
    return 32;
}

static void put(unsigned char row, unsigned char col, unsigned char code, unsigned char color)
{
    PSCR[row * 40 + col] = code;
    PCOL[row * 40 + col] = color;
}

void ui_draw_frame(void)
{
    unsigned char c, r;
    for (c = 0; c < 40; ++c) { put(0, c, UI_H, COL_GOLD); put(7, c, UI_HB, COL_GOLD); }
    for (r = 1; r < 7; ++r) {
        put(r, 0, UI_VL, COL_GOLD); put(r, 39, UI_VR, COL_GOLD); put(r, 27, UI_VD, COL_GOLD);
        for (c = 1; c < 27; ++c) put(r, c, 32, COL_WHITE);
        for (c = 28; c < 39; ++c) put(r, c, 32, COL_WHITE);
    }
    put(0, 0, UI_TL, COL_GOLD); put(0, 39, UI_TR, COL_GOLD);
    put(7, 0, UI_BL, COL_GOLD); put(7, 39, UI_BR, COL_GOLD);
    put(0, 27, UI_TD, COL_GOLD); put(7, 27, UI_BD, COL_GOLD);
    put(0, 12, UI_ORN_L, COL_GOLD); put(0, 13, UI_ORN_M, COL_GOLD); put(0, 14, UI_ORN_R, COL_GOLD);
}

void ui_clear_text(void)
{
    unsigned char r;
    for (r = 1; r < 7; ++r) memset(PSCR + r * 40 + TEXT_COL, 32, TEXT_WIDTH);
}

void ui_text_at(unsigned char line, unsigned char col, const char* s, unsigned char color)
{
    unsigned char row = line + 1;
    while (*s && col < TEXT_WIDTH) { put(row, TEXT_COL + col, petscii_to_screen(*s++), color); ++col; }
}

void ui_sc(const char* s, unsigned char* dst)
{
    unsigned char c = 0;
    while (s[c] && c < TEXT_WIDTH - 1) { dst[c] = petscii_to_screen(s[c]); ++c; }
    dst[c] = SC_END;
}

void ui_text(unsigned char line, const char* s, unsigned char color)
{
    unsigned char c = 0, row = line + 1;
    while (s[c] && c < TEXT_WIDTH) { put(row, TEXT_COL + c, petscii_to_screen(s[c]), color); ++c; }
    while (c < TEXT_WIDTH) { put(row, TEXT_COL + c, 32, color); ++c; }
}

static void num(unsigned char row, unsigned char col, unsigned int v, unsigned char width, unsigned char color)
{
    unsigned char i;
    for (i = 0; i < width; ++i) {
        put(row, col + width - 1 - i, (v || i == 0) ? (48 + v % 10) : 32, color);
        v /= 10;
    }
}

void ui_status(unsigned int day, unsigned int amber, unsigned int warriors, unsigned char green, unsigned char night)
{
    put(1, STAT_COL, night ? UI_MOON : UI_SUN, COL_GOLD);
    put(1, STAT_COL + 1, 68, COL_YELLOW); put(1, STAT_COL + 2, 65, COL_YELLOW);
    put(1, STAT_COL + 3, lang ? 89 : 71, COL_YELLOW);       /* DAG / DAY */
    num(1, STAT_COL + 4, day, 3, COL_YELLOW);
    put(2, STAT_COL, UI_AMBER, COL_GOLD);  num(2, STAT_COL + 1, amber, 5, COL_YELLOW);
    put(3, STAT_COL, UI_SWORD, COL_GOLD);  num(3, STAT_COL + 1, warriors, 5, COL_WHITE);
    put(4, STAT_COL, UI_LEAF, COL_GOLD);   num(4, STAT_COL + 1, green, 4, COL_GREEN);
    put(4, STAT_COL + 5, 37, COL_GREEN);   /* % */
}

static unsigned char globe_frame, globe_on;

void ui_globe(unsigned char on)
{
    globe_on = on;
    if (on) {
        *(unsigned char*)0xD000 = (unsigned char)(GLOBE_X & 0xFF);
        *(unsigned char*)0xD010 = (GLOBE_X > 255) ? 1 : 0;
        *(unsigned char*)0xD001 = GLOBE_Y;
        *(unsigned char*)0xD01C = 1;      /* multicolor */
        *(unsigned char*)0xD027 = 8;      /* oranje */
        *(unsigned char*)0xD025 = 9;      /* bruin */
        *(unsigned char*)0xD026 = 7;      /* geel */
        *(unsigned char*)0xD015 = 1;
    } else {
        *(unsigned char*)0xD015 = 0;
    }
}

void ui_globe_tick(void)
{
    globe_frame = (globe_frame + 1) & 7;
    SPRPTR[0] = GLOBE_PTR0 + globe_frame;
}

void ui_put(unsigned char line, unsigned char col, unsigned char code, unsigned char color)
{
    put(line + 1, TEXT_COL + col, code, color);
}

/* Screen-code-string vanaf (line, col) tot een terminator (>= $FD), rest van de regel leeg.
   Geeft de positie van de terminator terug. */
const unsigned char* ui_line(unsigned char line, unsigned char col, const unsigned char* sc, unsigned char color)
{
    unsigned char* scr = PSCR + (line + 1) * 40 + TEXT_COL;
    unsigned char* clr = PCOL + (line + 1) * 40 + TEXT_COL;
    while (col < TEXT_WIDTH && *sc < SC_PAGE) { scr[col] = *sc++; clr[col] = color; ++col; }
    while (col < TEXT_WIDTH) { scr[col] = 32; clr[col] = color; ++col; }
    return sc;
}

void ui_wait_frame(void)
{
    unsigned char f = frame_count;
    while (f == frame_count) ;
    if (globe_on && (f & 7) == 0) ui_globe_tick();
}

void ui_wait_fire(void)
{
    do ui_wait_frame(); while (!(input_poll() & IN_FIRE));
}

static const unsigned char sc_end = SC_END;

void (*ui_menu_hook)(unsigned char sel);
unsigned char ui_menu_keys;
unsigned char ui_menu_sel;

/* Menu in regels 1..5 met cursor '>'; meer dan 5 opties schuiven mee, met een pijl rechtsonder.
   Links/rechts bladert per 5. */
unsigned char ui_menu(const unsigned char* const* items, unsigned char n)
{
    unsigned char sel = ui_menu_sel, top = 0, i, k, color, ev, redraw = 1;
    ui_menu_sel = 0;
    if (sel >= n) sel = 0;
    for (;;) {
        if (redraw) {
            if (sel < top) top = sel;
            if (sel >= top + 5) top = sel - 4;
            for (i = 0; i < 5; ++i) {
                k = top + i;
                if (k < n) {
                    color = (k == sel) ? COL_YELLOW : COL_WHITE;
                    ui_put(i + 1, 0, (k == sel) ? 62 : 32, color);   /* '>' */
                    ui_put(i + 1, 1, 32, color);
                    ui_line(i + 1, 2, items[k], color);
                } else {
                    ui_line(i + 1, 0, &sc_end, COL_WHITE);
                }
            }
            if (top + 5 < n) ui_put(5, TEXT_WIDTH - 1, UI_MORE, COL_WHITE);
            redraw = 0;
        }
        if (ui_menu_hook) ui_menu_hook(sel);
        ui_wait_frame();
        ev = input_poll();
        if ((ev & IN_UP) && sel) { --sel; redraw = 1; }
        if ((ev & IN_DOWN) && sel + 1 < n) { ++sel; redraw = 1; }
        if (ev & IN_LEFT) { sel = (sel > 5) ? sel - 5 : 0; redraw = 1; }
        if (ev & IN_RIGHT) { sel = (sel + 5 < n) ? sel + 5 : n - 1; redraw = 1; }
        if (ev & IN_FIRE) return sel;
        if (ui_menu_keys && (ev & IN_DISK)) return MENU_KEY_DISK;
        if (ui_menu_keys && (ev & IN_MAP)) return MENU_KEY_MAP;
    }
}

#define STR_ITEMS 6
static unsigned char str_buf[STR_ITEMS][TEXT_WIDTH];

unsigned char ui_menu_str(const char* const* items, unsigned char n)
{
    static const unsigned char* ptrs[STR_ITEMS];
    unsigned char i, c;
    const char* s;
    for (i = 0; i < n; ++i) {
        s = items[i];
        for (c = 0; s[c] && c < TEXT_WIDTH - 3; ++c) str_buf[i][c] = petscii_to_screen(s[c]);
        str_buf[i][c] = SC_END;
        ptrs[i] = str_buf[i];
    }
    return ui_menu(ptrs, n);
}

void ui_number(unsigned char line, unsigned char col, unsigned int v, unsigned char color)
{
    unsigned char d[5], n = 0;
    do { d[n++] = 48 + v % 10; v /= 10; } while (v);
    while (n) ui_put(line, col++, d[--n], color);
}
