/* main.c - ASHKARA: opstart, titelscherm, daarna de verhaal-VM (DESIGN.md §10).
   Game over springt via longjmp(restart) terug naar het titelscherm. */
#include <setjmp.h>
#include <stdlib.h>
#include "gfx.h"
#include "ui.h"
#include "input.h"
#include "game.h"
#include "sim.h"
#include "vm.h"

jmp_buf restart;

static void title(void)
{
    ui_globe(0);
    screen_on = 0;
    split_enabled = 0;
    ui_wait_frame();
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
    vm_run(SCRIPT_H1, NODE_START);
    return 0;
}
