/* game.c - spelstatus. Alles ligt in BSS zodat opslaan het later 1-op-1 kan wegschrijven (§11.3). */
#include <string.h>
#include "game.h"
#include "ui.h"

unsigned int  vars[NVARS];
unsigned char flags[NFLAGS / 8];
loc_t         locs[NLOCS];
event_t       events[NEVENTS];

static const unsigned char bit[8] = { 1, 2, 4, 8, 16, 32, 64, 128 };

void game_init(void)
{
    unsigned char i;
    memset(vars, 0, sizeof(vars));
    memset(flags, 0, sizeof(flags));
    memcpy(locs, loc_init, sizeof(locs));
    for (i = 0; i < NEVENTS; ++i) events[i].target.script = NO_SCRIPT;
    vars[VAR_DAY] = 1;
    vars[VAR_LOC] = LOC_FORT;
}

unsigned char flag_get(unsigned char f) { return flags[f >> 3] & bit[f & 7]; }
void flag_set(unsigned char f)          { flags[f >> 3] |= bit[f & 7]; }
void flag_clr(unsigned char f)          { flags[f >> 3] &= ~bit[f & 7]; }

void game_add_event(unsigned int day, unsigned char script, unsigned int node)
{
    unsigned char i, free = 0xFF;
    event_t* e;
    for (i = 0; i < NEVENTS; ++i) {
        e = &events[i];
        if (e->target.script == NO_SCRIPT) { if (free == 0xFF) free = i; continue; }
        if (e->day == day && e->target.script == script && e->target.node == node) return;
    }
    if (free == 0xFF) return;          /* vol: het ontwerp houdt het onder 8 */
    e = &events[free];
    e->day = day;
    e->target.script = script;
    e->target.node = node;
}

void game_draw_status(void)
{
    ui_status(vars[VAR_DAY], vars[VAR_AMBER], vars[VAR_KRIJGERS],
              (unsigned char)vars[VAR_GROEN], (unsigned char)vars[VAR_NACHT]);
}
