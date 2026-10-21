/* sim.h - de strategielaag per dag (DESIGN.md §4.7) */
#ifndef ASHKARA_SIM_H
#define ASHKARA_SIM_H
#include "game.h"

#define AMBER_MAX 60000u

/* Script-node die na de huidige actie moet draaien (Tiende-waarschuwing, game over,
   ON_DAY-event). script == NO_SCRIPT: niets. Game over gaat altijd voor. */
extern noderef_t sim_pending;

void          sim_day(void);
void          sim_pend(const noderef_t* n, unsigned char force);   /* force: gaat voor (game over, einde) */
unsigned int  sim_yield(const loc_t* l);   /* amber per dag van een OOGST-kamp */
void          sim_update_totals(void);     /* krijgers en groen % voor het paneel */

#endif
