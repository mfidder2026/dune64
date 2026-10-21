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

jmp_buf restart;

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
    ui_wait_fire();
}

int main(void)
{
    gfx_init();
    gfx_load_raw("ui.chr");            /* -> $C800 (laadadres in bestand) */
    gfx_load_raw("globe.spr");         /* -> $C400 */
    SPRPTR[0] = GLOBE_PTR0;
    irq_install();
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
