/* input.h - joystick poort 2 + toetsenbord (DESIGN.md §5.4) */
#ifndef ASHKARA_INPUT_H
#define ASHKARA_INPUT_H

/* bits gelijk aan de joystickbits van $DC00 (actief hoog gemaakt) */
#define IN_UP     0x01
#define IN_DOWN   0x02
#define IN_LEFT   0x04
#define IN_RIGHT  0x08
#define IN_FIRE   0x10
#define IN_BACK   0x20   /* RUN/STOP */
#define IN_MAP    0x40   /* K */
#define IN_DISK   0x80   /* F7 */

/* 1x per frame aanroepen: geeft de NIEUWE gebeurtenissen van dit frame (flank-getriggerd,
   met herhaling voor op/neer als de joystick vast wordt gehouden). */
unsigned char input_poll(void);
void          input_flush(void);

#endif
