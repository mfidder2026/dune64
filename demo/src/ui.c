/* ui.c - paneel tekenen. Tekst komt binnen als PETSCII (cc65-stringliterals) en wordt
   omgezet naar screen codes van de eigen charset (zie DESIGN.md §5.3). */
#include <string.h>
#include "gfx.h"
#include "ui.h"

#define PSCR (SCREEN + PANEL_ROW * 40)
#define PCOL (COLRAM + PANEL_ROW * 40)

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
    put(1, STAT_COL + 1, 68, COL_YELLOW); put(1, STAT_COL + 2, 65, COL_YELLOW); put(1, STAT_COL + 3, 71, COL_YELLOW); /* DAG */
    num(1, STAT_COL + 4, day, 3, COL_YELLOW);
    put(2, STAT_COL, UI_AMBER, COL_GOLD);  num(2, STAT_COL + 1, amber, 5, COL_YELLOW);
    put(3, STAT_COL, UI_SWORD, COL_GOLD);  num(3, STAT_COL + 1, warriors, 5, COL_WHITE);
    put(4, STAT_COL, UI_LEAF, COL_GOLD);   num(4, STAT_COL + 1, green, 4, COL_GREEN);
    put(4, STAT_COL + 5, 37, COL_GREEN);   /* % */
}

static unsigned char globe_frame;

void ui_globe(unsigned char on)
{
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
