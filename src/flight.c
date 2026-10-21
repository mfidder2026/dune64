/* flight.c - de duinen schuiven naar je toe doordat de drie kleuren van elke grondrij per tick
   een plaats doordraaien (zie de kop van pipeline/flight.py). Het bitmap blijft ongemoeid:
   per tick 10 rijen x 80 bytes scherm- en kleur-RAM. */
#include <string.h>
#include "gfx.h"
#include "ui.h"
#include "input.h"
#include "game.h"
#include "vm.h"
#include "flight.h"
#include "flight_tab.h"

#define FLIGHT_SPEED 4     /* frames per cyclus-stap */

static unsigned char phase, tick, night_pal;

static void row_colors(unsigned char r, unsigned char rot)
{
    const unsigned char* p = night_pal ? fl_night[r] : fl_day[r];
    unsigned char s1 = p[rot], s2 = p[rot == 2 ? 0 : rot + 1], s3 = p[rot == 0 ? 2 : rot - 1];
    memset(SCREEN + r * 40, (s1 << 4) | s2, 40);
    memset(COLRAM + r * 40, s3, 40);
}

static void paint_all(void)
{
    unsigned char r;
    for (r = 0; r < SCENE_ROWS; ++r)
        row_colors(r, (r >= FL_GROUND_FIRST && r < FL_GROUND_END) ? phase : 0);
}

void flight_begin(void)
{
    vm_char(0);
    vm_scene(SCENE_VLUCHT);
    phase = 0;
    tick = 0;
    paint_all();
    vm_show();
}

void flight_night(unsigned char night)
{
    if (night == night_pal) return;
    night_pal = night;
    paint_all();
}

unsigned char flight_frames(unsigned char n)
{
    unsigned char r;
    while (n--) {
        ui_wait_frame();
        if (++tick >= FLIGHT_SPEED) {
            tick = 0;
            phase = (phase == 2) ? 0 : phase + 1;
            for (r = FL_GROUND_FIRST; r < FL_GROUND_END; ++r) row_colors(r, phase);
        }
#ifndef TESTMODE                   /* tests sturen geen toetsen tijdens een vlucht */
        if (input_poll() & IN_FIRE) return 1;
#endif
    }
    return 0;
}
