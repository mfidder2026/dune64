/* gfx.c - scènes en patches laden/uitpakken. Zie DESIGN.md §8. */
#include <string.h>
#include <zlib.h>
#include "gfx.h"
#include "disk.h"
#include "sound.h"

#define MAGIC_SCENE 0x53   /* 'S' als ruwe byte (niet als C-tekenliteral: cc65 vertaalt naar PETSCII) */
#define MAGIC_PATCH 0x50   /* 'P' */

unsigned char scene_rows;

void gfx_init(void)
{
    /* RAM-vectoren onder de Kernal-ROM: nodig zolang de Kernal is weggebankt ($01=$35) */
    *(unsigned int*)0xFFFA = (unsigned int)nmi_stub;
    *(unsigned int*)0xFFFE = (unsigned int)nmi_stub;

    *(unsigned char*)0xDD00 = (*(unsigned char*)0xDD00 & 0xFC);  /* VIC-bank 3: $C000-$FFFF */
    *(unsigned char*)0xD016 = 0x18;     /* multicolor aan, 40 kolommen */
    *(unsigned char*)0xD020 = 0;        /* rand zwart */
    *(unsigned char*)0xD021 = 0;        /* achtergrond zwart (ook bitmap-%00) */
    *(unsigned char*)0xD022 = 9;        /* paneel multicolor 1: bruin  */
    *(unsigned char*)0xD023 = 8;        /* paneel multicolor 2: oranje */
    memset(SCREEN, 32, 1000);
    memset(COLRAM, 0, 1000);
    memset(BITMAP, 0, 8000);
}

unsigned char gfx_load_raw(const char* name)
{
    return disk_load(name, 0) != 0;
}

unsigned char gfx_load_scene(const char* name)
{
    unsigned int bmlen;
    unsigned char rows, old01, n;

    if (disk_load(name, LOADBUF) == 0 || LOADBUF[0] != MAGIC_SCENE)
        return 0;
    sound_hold(1);                     /* uitpakken: de IRQ staat even uit */
    rows  = LOADBUF[1];
    bmlen = LOADBUF[4] | ((unsigned int)LOADBUF[5] << 8);

    /* Bitmap-stroom direct naar $E000 uitpakken. Inflate leest terug uit zijn eigen
       uitvoer; onder $E000 zit de Kernal-ROM, dus die moet even weg ($01=$35). */
    __asm__("sei");
    old01 = *(unsigned char*)0x01;
    *(unsigned char*)0x01 = (old01 & 0xF8) | 0x05;
    inflatemem(BITMAP, LOADBUF + 8);
    *(unsigned char*)0x01 = old01;
    __asm__("cli");

    /* Kleurstroom naar COLBUF, dan kopiëren (kleur-RAM is nibble-RAM: niet uitpakken in-place) */
    inflatemem(COLBUF, LOADBUF + 8 + bmlen);
    n = rows;
    memcpy(SCREEN, COLBUF, n * 40);
    memcpy(COLRAM, COLBUF + n * 40, n * 40);
    /* Bitmaprij 17 leeg: valt de split een paar cycli te laat, dan toont de VIC daar nog
       bitmap (resten van een volledig scherm zoals de titel) in plaats van het paneel. */
    if (n < 25) memset(BITMAP + n * 320, 0, 320);
    scene_rows = rows;
    sound_hold(0);
    return rows;
}

unsigned char gfx_load_patch(const char* name)
{
    if (disk_load(name, LOADBUF) == 0 || LOADBUF[0] != MAGIC_PATCH)
        return 0;
    sound_hold(1);
    inflatemem(PATBUF, LOADBUF + 4);
    sound_hold(0);
    return PATBUF[0];
}

void gfx_apply_patch(unsigned char index)
{
    unsigned char* p = PATBUF + 1;
    unsigned char i, x, y, w, h, r, w8;
    for (i = 0; i < index; ++i)
        p += 4 + (unsigned int)p[2] * p[3] * 10;
    x = p[0]; y = p[1]; w = p[2]; h = p[3]; p += 4;
    w8 = w << 3;
    for (r = 0; r < h; ++r) { memcpy(BITMAP + (((y + r) * 40 + x) << 3), p, w8); p += w8; }
    for (r = 0; r < h; ++r) { memcpy(SCREEN + (y + r) * 40 + x, p, w); p += w; }
    for (r = 0; r < h; ++r) { memcpy(COLRAM + (y + r) * 40 + x, p, w); p += w; }
}
