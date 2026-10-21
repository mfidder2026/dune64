/* map.h - kaartscherm: markers, bestemmingsmenu, reizen, ontdekken (DESIGN.md §4.2) */
#ifndef ASHKARA_MAP_H
#define ASHKARA_MAP_H

#define MAP_CANCEL 0xFF

/* Toont de kaart en laat een bestemming kiezen; reist erheen (dagen tikken, ontdekken onderweg).
   Geeft de locatie van aankomst terug, of MAP_CANCEL bij "Terug". */
unsigned char map_run(void);

#endif
