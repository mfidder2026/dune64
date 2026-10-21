/* main.c - ASHKARA schermen-demo: doorloopt het storyboard met de echte engine-onderdelen
   (raster-split, scène laden + uitpakken, personage-patches, praat-animatie, UI-paneel).
   Vuur (joystick poort 2) of een toets = volgende scherm. */
#include <cbm.h>
#include "gfx.h"
#include "ui.h"
#include "slides.h"

static const char empty[] = "";
#ifdef AUTOADVANCE
unsigned int auto_t;
#endif
static const unsigned char talk_seq[8] = { 3, 2, 1, 2, 3, 2, 1, 1 };  /* patch 1=dicht 2=half 3=open */

static void wait_frame(void)
{
    unsigned char f = frame_count;
    while (f == frame_count) ;
}

static unsigned char pressed(void)
{
#ifdef AUTOADVANCE
    extern unsigned int auto_t;
    if (auto_t >= AUTOADVANCE) return 1;
#endif
    if (cbm_k_getin()) return 1;
    return !(*(unsigned char*)0xDC00 & 0x10);    /* vuurknop poort 2 */
}

static void show(const slide_t* s)
{
    unsigned char i, rows, has_char = 0;
    unsigned int t = 0;

    screen_on = 0;                     /* beeld uit tijdens laden */
    ui_globe(0);
    wait_frame();

    rows = gfx_load_scene(s->scene);
    if (rows == 0) { *(unsigned char*)0xD020 = 2; return; }   /* rode rand = laadfout */
    split_enabled = (rows != 25);
    if (split_enabled) {
        ui_draw_frame();
        for (i = 0; i < 6; ++i)
            ui_text(i, s->lines[i] ? s->lines[i] : empty, s->colors[i]);
        ui_status(s->day, s->amber, s->warriors, s->green, s->night);
    }
    if (s->patch && gfx_load_patch(s->patch) >= 4) {
        gfx_apply_patch(0);            /* lichaam */
        gfx_apply_patch(1);            /* mond dicht */
        has_char = 1;
    }
    wait_frame();
    screen_on = 0x10;
    ui_globe(split_enabled);

    while (!pressed()) {
        wait_frame();
        ++t;
#ifdef AUTOADVANCE
        auto_t = t;
#endif
        if (split_enabled && (t & 7) == 0) ui_globe_tick();
        if (has_char && t < 160 && (t % 6) == 0) gfx_apply_patch(talk_seq[(t / 6) & 7]);
        if (has_char && t == 160) gfx_apply_patch(1);
    }
#ifdef AUTOADVANCE
    auto_t = 0;
#endif
    while (pressed()) wait_frame();
}

int main(void)
{
    unsigned char i;
    gfx_init();
    gfx_load_raw("ui.chr");            /* -> $C800 (laadadres in bestand) */
    gfx_load_raw("globe.spr");         /* -> $C400 */
    SPRPTR[0] = GLOBE_PTR0;
    irq_install();
    for (;;)
        for (i = 0; i < NSLIDES; ++i)
            show(&slides[i]);
    return 0;
}
