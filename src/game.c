/* game.c - spelstatus. Alles ligt in BSS zodat opslaan het later 1-op-1 kan wegschrijven (§11.3). */
#include <string.h>
#include "gfx.h"
#include "game.h"
#include "disk.h"
#include "ui.h"

#define SAVE_NAME "ashkara.sav"

state_t state;
unsigned char lang;

static const unsigned char bit[8] = { 1, 2, 4, 8, 16, 32, 64, 128 };

void game_init(void)
{
    unsigned char i;
    const event_t* e;
    memset(&state, 0, sizeof(state));
    state.magic = SAVE_MAGIC;
    state.version = SAVE_VERSION;
    memcpy(locs, loc_init, sizeof(locs));
    for (i = 0; i < NEVENTS; ++i) events[i].target.script = NO_SCRIPT;
    for (e = init_events; e->target.script != NO_SCRIPT; ++e)
        game_add_event(e->day, e->target.script, e->target.node);
    vars[VAR_DAY] = 1;
    vars[VAR_LOC] = LOC_FORT;
}

unsigned char flag_get(unsigned char f) { return state.flags[f >> 3] & bit[f & 7]; }
void flag_set(unsigned char f)          { state.flags[f >> 3] |= bit[f & 7]; }
void flag_clr(unsigned char f)          { state.flags[f >> 3] &= ~bit[f & 7]; }

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

unsigned char game_save(void)
{
    return disk_save(SAVE_NAME, &state, sizeof(state));
}

/* Eerst naar LOADBUF, controleren, dan pas overnemen: een kapot of oud bestand laat het
   lopende spel heel. */
unsigned char game_load(void)
{
    const state_t* s = (const state_t*)LOADBUF;
    if (disk_load(SAVE_NAME, LOADBUF) != sizeof(state)) return 0;
    if (s->magic != SAVE_MAGIC || s->version != SAVE_VERSION) return 0;
    memcpy(&state, s, sizeof(state));
    return 1;
}
