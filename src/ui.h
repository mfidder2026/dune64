/* ui.h - UI-paneel in de onderste 8 tekstrijen (rij 17-24). Zie DESIGN.md §5. */
#ifndef ASHKARA_UI_H
#define ASHKARA_UI_H
#include "ui_codes.h"

#define PANEL_ROW   17
#define TEXT_COL    1
#define TEXT_WIDTH  26
#define TEXT_LINES  6     /* regel 0 = spreker, 1..5 = tekst/menu */
#define STAT_COL    28
#define COL_WHITE   1
#define COL_YELLOW  7
#define COL_GREEN   5
#define COL_GOLD    (8 + 7)   /* multicolor-teken, %11 = geel */

/* stringterminators in screen-code-strings van de scriptcompiler (§9.2) */
#define SC_NL   0xFE
#define SC_PAGE 0xFD
#define SC_END  0xFF

void ui_draw_frame(void);
void ui_clear_text(void);
void ui_text(unsigned char line, const char* s, unsigned char color);  /* PETSCII (C-strings), line 0..5 */
void ui_put(unsigned char line, unsigned char col, unsigned char code, unsigned char color);
const unsigned char* ui_line(unsigned char line, unsigned char col, const unsigned char* sc, unsigned char color);
void ui_status(unsigned int day, unsigned int amber, unsigned int warriors, unsigned char green, unsigned char night);
void ui_globe(unsigned char on);
void ui_globe_tick(void);

void ui_wait_frame(void);      /* wacht 1 frame, draait de globe */
void ui_wait_fire(void);       /* wacht op een nieuwe vuurdruk */
unsigned char ui_menu(const unsigned char* const* items, unsigned char n);  /* keuze 0..n-1 */
unsigned char ui_menu_str(const char* const* items, unsigned char n);      /* idem met C-strings (max 6) */
void ui_number(unsigned char line, unsigned char col, unsigned int v, unsigned char color);  /* links uitgelijnd */

/* Met ui_menu_keys = 1 geeft ui_menu ook deze waarden terug (alleen de VM-menu's) */
#define MENU_KEY_DISK 0xFE   /* F7 */
#define MENU_KEY_MAP  0xFD   /* K  */
extern unsigned char ui_menu_keys;

/* Wordt elk frame van ui_menu aangeroepen met de huidige keuze (kaart: knipperende marker). */
extern void (*ui_menu_hook)(unsigned char sel);
#endif
