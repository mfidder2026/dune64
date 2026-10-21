/* main.c - ASHKARA: opstart, titelscherm, daarna de verhaal-VM (DESIGN.md §10).
   Game over springt via longjmp(restart) terug naar het titelscherm. */
#include <setjmp.h>
#include <stdlib.h>
#include "gfx.h"
#include "ui.h"
#include "input.h"
#include "game.h"
#include "sim.h"
#include "text.h"
#include "vm.h"
#include "disk.h"

jmp_buf restart;

void music_init(void);                 /* music.s */
void music_silence(void);
extern unsigned char music_on;

#define EXTRA_NAME   "extra.bin"       /* drivecode + muziek, hoort onder de I/O ($D000) */
#define FIRE_SPR     24                /* spriteblokken 24-27 "DRUK OP VUUR", 28-31 "PRESS FIRE" */
#define FIRE_X       136
#define FIRE_Y       224
#define FIRE_SWAP    100               /* frames per taal */

static void load_extra(void)
{
    unsigned int n = disk_load(EXTRA_NAME, LOADBUF);
    if (n < 0x200) return;             /* zonder extra.bin: geen muziek, geen fastloader */
    io_copy(IOBUF, LOADBUF, n);
    disk_set_drive_code();
    music_init();
    music_on = 1;
}

/* "DRUK OP VUUR" en "PRESS FIRE" om en om, als hires-sprites onder in het titelbeeld */
static void fire_sprites(unsigned char which)
{
    unsigned char i;
    for (i = 0; i < 4; ++i) {
        SPRPTR[i] = FIRE_SPR + which * 4 + i;
        *(unsigned char*)(0xD000 + i * 2) = FIRE_X + i * 24;
        *(unsigned char*)(0xD001 + i * 2) = FIRE_Y;
        *(unsigned char*)(0xD027 + i) = which ? 1 : 7;   /* wit / geel */
    }
    *(unsigned char*)0xD010 = 0;
    *(unsigned char*)0xD01C = 0;       /* hires */
    *(unsigned char*)0xD015 = 0x0F;
}

static const char* const lang_items[] = { "Nederlands", "English" };

/* Taalkeuze na het titelscherm (ook later te wisselen via F7). */
static void choose_language(void)
{
    vm_scene(SCENE_RUIMTE);
    vm_show();
    txt_title("TAAL / LANGUAGE");
    lang = ui_menu_str(lang_items, 2);
    txt_clear();
    game_draw_status();                /* DAG / DAY */
}

static void title(void)
{
    ui_globe(0);
    screen_on = 0;
    split_enabled = 0;
    ui_wait_frame();
    vm_forget_scene();
    if (!gfx_load_scene("titel.scn")) { *(unsigned char*)0xD020 = 2; for (;;) ; }
    ui_wait_frame();
    screen_on = 0x10;
    input_flush();
    {
        unsigned char t = 0, which = 0;
        fire_sprites(0);
        while (!(input_poll() & IN_FIRE)) {
            ui_wait_frame();
            if (++t == FIRE_SWAP) { t = 0; which ^= 1; fire_sprites(which); }
        }
    }
    *(unsigned char*)0xD015 = 0;
    SPRPTR[0] = GLOBE_PTR0;
}

int main(void)
{
    gfx_init();
    gfx_load_raw("ui.chr");            /* -> $C800 (laadadres in bestand) */
    gfx_load_raw("globe.spr");         /* -> $C400 */
    SPRPTR[0] = GLOBE_PTR0;
    irq_install();
    load_extra();
#ifndef NOFAST
    disk_fast_install();               /* 1541? dan snelladen, anders gewoon via de Kernal */
#endif
#ifdef TESTMODE
    srand(1);                          /* reproduceerbare ontdekkingen in tests */
#else
    _randomize();
#endif
    setjmp(restart);
    game_init();
    sim_update_totals();
    title();
    choose_language();
    vm_run(SCRIPT_H1, NODE_START);
    return 0;
}
