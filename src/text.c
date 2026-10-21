/* text.c - tekstbuffer en weergave. De scriptcompiler breekt niet af: dat gebeurt hier,
   zodat getallen ({amber}) en namen ({loc}) in de tekst passen. */
#include "gfx.h"
#include "ui.h"
#include "input.h"
#include "game.h"
#include "text.h"

#define TBUF_SIZE 600
#define TEXT_W    25          /* kolom 26 is voor het ▼-teken */
#define LAST_LINE 5

unsigned char txt_mouth;

static unsigned char tbuf[TBUF_SIZE];
static unsigned int  tlen;

static const unsigned char talk_seq[8] = { 3, 2, 1, 2, 3, 2, 1, 1 };  /* patch 1=dicht 2=half 3=open */
static const unsigned char sc_end = SC_END;

static unsigned char petscii_to_screen(unsigned char c)
{
    if (c >= 0x40 && c < 0x60) return c - 0x40;   /* a-z (cc65 'a' -> $41) -> 1..26 */
    if (c >= 0xC0 && c < 0xE0) return c - 0x80;   /* A-Z (cc65 'A' -> $C1) -> 65..90 */
    if (c >= 0x20 && c < 0x40) return c;          /* spatie, cijfers, leestekens */
    return 32;
}

static void add(unsigned char c)
{
    if (tlen < TBUF_SIZE - 1) tbuf[tlen++] = c;
}

void txt_begin(void) { tlen = 0; }

void txt_num(unsigned int v)
{
    unsigned char d[5], n = 0;
    do { d[n++] = 48 + v % 10; v /= 10; } while (v);
    while (n) add(d[--n]);
}

void txt_name(unsigned char loc)
{
    const unsigned char* s = loc_names[loc];
    while (*s != SC_END) add(*s++);
}

void txt_sc(const unsigned char* sc)
{
    unsigned char c;
    while ((c = *sc++) != SC_END) {
        if (c == SC_VAR)      txt_num(vars[*sc++]);
        else if (c == SC_LOC) txt_name((unsigned char)vars[VAR_LOC]);
        else if (c == SC_PLACE) txt_name((unsigned char)vars[*sc++]);
        else                  add(c);
    }
}

void txt_str(const char* s)
{
    while (*s) add(petscii_to_screen(*s++));
}

void txt_clear(void)
{
    unsigned char i;
    for (i = 1; i <= LAST_LINE; ++i) ui_line(i, 0, &sc_end, COL_WHITE);
}

/* ------------------------------------------------------------------ weergave */

static unsigned char line, col, fast, t, page_full;

static void mouth(unsigned char p)
{
    if (txt_mouth) gfx_apply_patch(p);
}

static void new_page(void)
{
    mouth(1);
    ui_put(LAST_LINE, TEXT_W, UI_MORE, COL_WHITE);
    ui_wait_fire();
    txt_clear();
    line = 1; col = 0; fast = 0; page_full = 0;
}

static void newline(void)
{
    col = 0;
    if (++line > LAST_LINE) page_full = 1;   /* pas pagineren als er nog tekst komt */
}

static void put(unsigned char c)
{
    if (page_full) new_page();
    ui_put(line, col++, c, COL_WHITE);
    if (fast || (col & 1)) return;           /* 2 tekens per frame */
    ui_wait_frame();
    ++t;
    if (t % 6 == 0) mouth(talk_seq[(t / 6) & 7]);
    if (input_poll() & IN_FIRE) fast = 1;    /* vuur tijdens typen: pagina meteen af */
}

void txt_show(void)
{
    unsigned int p = 0, q;
    unsigned char c;

    txt_clear();
    line = 1; col = 0; fast = 0; t = 0; page_full = 0;
    while (p < tlen) {
        c = tbuf[p];
        if (c == SC_NL)   { ++p; newline(); continue; }
        if (c == SC_PAGE) { ++p; if (line > 1 || col) page_full = 1; continue; }
        if (c == 32)      { ++p; if (col && col < TEXT_W) ui_put(line, col++, 32, COL_WHITE); continue; }
        for (q = p; q < tlen && tbuf[q] != 32 && tbuf[q] < SC_PAGE; ++q) ;
        if (col && col + (q - p) > TEXT_W) newline();
        while (p < q) {
            if (col >= TEXT_W) newline();
            put(tbuf[p++]);
        }
    }
    mouth(1);
    ui_wait_fire();
}

/* ------------------------------------------------------------------ regel 0 en meldingen */

void txt_say(const unsigned char* sc)
{
    txt_begin();
    txt_sc(sc);
    tbuf[tlen] = SC_END;
    ui_line(0, 0, tbuf, COL_YELLOW);
}

void txt_title(const char* s)
{
    ui_text(0, s, COL_YELLOW);
}

void txt_message(const char* title, const char* s)
{
    txt_title(title);
    txt_begin();
    txt_str(s);
    txt_show();
}
