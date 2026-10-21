/* gfx.h - geheugenkaart en grafische routines (zie DESIGN.md §7 en §8) */
#ifndef ASHKARA_GFX_H
#define ASHKARA_GFX_H

/* Grenzen bewaakt door build.py (check_buffers); zie DESIGN.md §7 */
#define LOADBUF  ((unsigned char*)0x9700)   /* 3,75 KB: gecomprimeerd bestand van disk */
#define PATBUF   ((unsigned char*)0xA600)   /* 3 KB: uitgepakte patchset (personage)   */
/* COLBUF deelt PATBUF: alleen nodig tijdens het uitpakken van een scène, en een nieuwe scène
   wist het personage toch (vm_scene: cur_char = 0, daarna laadt CHAR de patch opnieuw). */
#define COLBUF   PATBUF                     /* 2 KB: uitgepakt scherm-RAM + kleur-RAM  */
#define SCRIPTBUF ((unsigned char*)0xB200)  /* 3,5 KB: script/tekst van het hoofdstuk  */
#define IOBUF    ((unsigned char*)0xD000)   /* 4 KB RAM onder de I/O: drivecode + muziek */
#define IOBUF_DRIVE ((unsigned char*)0xD000)  /* fastloader-drivecode (max 512 B)      */
#define SCREEN   ((unsigned char*)0xC000)   /* VIC-bank 3: scherm-matrix              */
#define SPRPTR   ((unsigned char*)0xC3F8)   /* sprite-pointers                        */
#define SPRDATA  ((unsigned char*)0xC400)   /* 16 sprites (blokken 16..31)            */
#define CHARSET  ((unsigned char*)0xC800)   /* UI-charset (2 KB)                      */
#define COLRAM   ((unsigned char*)0xD800)
#define BITMAP   ((unsigned char*)0xE000)   /* onder de Kernal-ROM                    */

#define SCENE_ROWS 17                       /* bitmap-rijen boven het paneel          */

extern unsigned char scene_rows;

void          gfx_init(void);
unsigned char gfx_load_scene(const char* name);        /* 0 = fout, anders aantal rijen */
unsigned char gfx_load_patch(const char* name);        /* 0 = fout, anders aantal patches */
void          gfx_apply_patch(unsigned char index);
unsigned char gfx_load_raw(const char* name);          /* naar eigen laadadres (charset/sprites) */

/* irq.s */
void irq_install(void);
void nmi_stub(void);
extern volatile unsigned char frame_count;
extern unsigned char split_enabled;
extern unsigned char screen_on;

#endif
