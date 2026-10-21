/* ui.h - UI-paneel in de onderste 8 tekstrijen (rij 17-24). Zie DESIGN.md §5. */
#ifndef ASHKARA_UI_H
#define ASHKARA_UI_H
#include "ui_codes.h"

#define PANEL_ROW   17
#define TEXT_COL    1
#define TEXT_WIDTH  26
#define STAT_COL    28
#define COL_WHITE   1
#define COL_YELLOW  7
#define COL_GREEN   5
#define COL_GOLD    (8 + 7)   /* multicolor-teken, %11 = geel */

void ui_draw_frame(void);
void ui_clear_text(void);
void ui_text(unsigned char line, const char* s, unsigned char color);  /* line 0..5 */
void ui_status(unsigned int day, unsigned int amber, unsigned int warriors, unsigned char green, unsigned char night);
void ui_globe(unsigned char on);
void ui_globe_tick(void);
#endif
