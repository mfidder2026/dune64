/* flight.h - vluchtanimatie: cockpitzicht over de woestijn via kleurcycli (pipeline/flight.py) */
#ifndef ASHKARA_FLIGHT_H
#define ASHKARA_FLIGHT_H

void          flight_begin(void);                 /* vluchtscène laden en kleuren zetten */
void          flight_night(unsigned char night);  /* dag- of nachtpalet */
unsigned char flight_frames(unsigned char n);     /* n frames animeren; 1 = vuur: rest overslaan */

#endif
