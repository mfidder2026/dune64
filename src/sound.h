/* sound.h - muziek en geluidseffecten (src/music.s) */
#ifndef ASHKARA_SOUND_H
#define ASHKARA_SOUND_H

enum { SFX_TICK, SFX_SELECT, SFX_WHOOSH, SFX_ALARM };

extern unsigned char music_on, sfx_on;

void music_init(void);
void __fastcall__ music_set(unsigned char on);     /* F1 */
void __fastcall__ sfx(unsigned char id);           /* niets als sfx_on == 0 (F3) */
/* Stil tijdens laden/uitpakken (de raster-IRQ staat dan soms uit): 1 = stil, 0 = weer aan.
   Nestbaar. */
void __fastcall__ sound_hold(unsigned char on);

#endif
