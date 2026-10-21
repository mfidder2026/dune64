/* input.c - joystick via $DC00, toetsenbord via de Kernal-buffer (gevuld door de raster-IRQ).
   Met -DTESTMODE komt de invoer uit src/testkeys.h (headless testen in VICE, DESIGN.md §12.3). */
#include <cbm.h>
#include "input.h"

#define REPEAT_DELAY 20   /* frames vasthouden voor de eerste herhaling */
#define REPEAT_RATE  6

static unsigned char prev, held;

#ifdef TESTMODE
#include "game.h"
#include "testkeys.h"     /* static const char test_keys[] = "FFDF..."; TEST_RATE = frames per toets */
static unsigned int test_i;
static unsigned char test_t;

static unsigned char test_poll(void)
{
    unsigned char c;
    if (++test_t < TEST_RATE) return 0;
    test_t = 0;
    c = test_keys[test_i];
    if (!c) return 0;
    ++test_i;
    switch (c) {
    case 'U': return IN_UP;
    case 'D': return IN_DOWN;
    case 'L': return IN_LEFT;
    case 'R': return IN_RIGHT;
    case 'F': return IN_FIRE;
    case 'B': return IN_BACK;
    case 'K': return IN_MAP;
    /* alleen in tests: */
    case 'A': vars[VAR_AMBER] += 500; return 0;            /* Tiende-flow los van de balans */
    case 'T': flag_clr(FLAG_TIENDE_OPEN); return 0;        /* geen Tiende: lange runs */
    case 'O': flag_set(FLAG_F_OVERVALLEN); return 0;       /* overvallen nu al aan */
    case 'S': return IN_DISK;                              /* F7 */
    }
    return 0;             /* 'W' en de rest: wachten */
}
#endif

unsigned char input_poll(void)
{
    unsigned char joy, ev;
#ifdef TESTMODE
    return test_poll();
#endif
    joy = ~*(unsigned char*)0xDC00 & 0x1F;
    ev = joy & ~prev;
    if ((joy & (IN_UP | IN_DOWN)) && joy == prev) {
        if (++held >= REPEAT_DELAY) {
            held = REPEAT_DELAY - REPEAT_RATE;
            ev |= joy & (IN_UP | IN_DOWN);
        }
    } else {
        held = 0;
    }
    prev = joy;

    switch (cbm_k_getin()) {
    case 0x91: ev |= IN_UP;    break;   /* cursor op    */
    case 0x11: ev |= IN_DOWN;  break;   /* cursor neer  */
    case 0x9D: ev |= IN_LEFT;  break;   /* cursor links */
    case 0x1D: ev |= IN_RIGHT; break;   /* cursor rechts */
    case 0x0D:                          /* return */
    case 0x20: ev |= IN_FIRE;  break;   /* spatie */
    case 0x03: ev |= IN_BACK;  break;   /* RUN/STOP */
    case 0x4B:                          /* k */
    case 0xCB: ev |= IN_MAP;   break;   /* K */
    case 0x88: ev |= IN_DISK;  break;   /* F7 */
    }
    return ev;
}

void input_flush(void)
{
    while (cbm_k_getin()) ;
    prev = ~*(unsigned char*)0xDC00 & 0x1F;   /* nu ingedrukte knoppen tellen niet als nieuw */
}
