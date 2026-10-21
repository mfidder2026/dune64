/* battle.h - abstracte gevechten (DESIGN.md §4.5) */
#ifndef ASHKARA_BATTLE_H
#define ASHKARA_BATTLE_H
#include "game.h"

unsigned int battle_power(const loc_t* l);     /* gevechtskracht van één kamp */
void         battle(void);                     /* @GEVECHT op de huidige locatie */

#endif
