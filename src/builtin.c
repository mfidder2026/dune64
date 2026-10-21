/* builtin.c - kaart, Tiende, werven, taken, kampacties, rusten, game over (DESIGN.md §4).
   Een builtin die ergens anders heen moet (aankomst na een reis) zet vm_next. */
#include <setjmp.h>
#include "ui.h"
#include "game.h"
#include "sim.h"
#include "text.h"
#include "map.h"
#include "vm.h"
#include "builtin.h"

extern jmp_buf restart;                 /* main.c */

#define TRUST_MIN_WERVEN 50
#define ZEGEN_BONUS      20             /* Tariks zegen telt mee bij andere kampen */
#define TRUST_GESCHENK   15
#define TRUST_PRAAT      5

static loc_t* camp_here(void)
{
    loc_t* l = HERE;
    if (l->type != LT_KAMP) {
        txt_message("HIER NIET", "Dit is geen kamp van de Kethari.");
        return 0;
    }
    return l;
}

static void add_trust(loc_t* l, unsigned char n)
{
    l->trust = (l->trust + n > 100) ? 100 : l->trust + n;
}

static void kaart(void)
{
    unsigned char dest = map_run();
    if (dest == MAP_CANCEL) return;     /* terug naar het menu waar je was */
    vars[VAR_LOC] = dest;
    vm_next = loc_nodes[dest];
}

static void tiende(void)
{
    if (flag_get(FLAG_TIENDE_OPEN) && vars[VAR_AMBER] >= vars[VAR_TIENDE_EIS]) {
        vars[VAR_AMBER] -= vars[VAR_TIENDE_EIS];
        ++vars[VAR_TIENDE_N];
        flag_clr(FLAG_TIENDE_OPEN);
        flag_clr(FLAG_TIENDE_UITSTEL);
        game_draw_status();
    }
}

static void status(void)
{
    loc_t* l = camp_here();
    static const char* const st[] = { "onbekend", "bekend", "bondgenoot", "bezet", "groen" };
    static const char* const job[] = { "geen", "oogsten", "strijd", "vergroenen" };
    if (!l) return;
    txt_title("STATUS");
    txt_begin();
    txt_name((unsigned char)vars[VAR_LOC]);
    txt_str(": "); txt_str(st[l->status]); txt_str(". ");
    txt_num(l->size); txt_str(" Kethari, vertrouwen "); txt_num(l->trust);
    txt_str(". Taak: "); txt_str(job[l->job]);
    txt_str(". Amber in de bodem: "); txt_num(l->richness); txt_str(".");
    if (l->job == JOB_OOGST) { txt_str(" Opbrengst: "); txt_num(sim_yield(l)); txt_str(" per dag."); }
    if (l->flags & LF_HARVESTER) txt_str(" Met oogstmachine.");
    txt_show();
}

static void werven(void)
{
    loc_t* l = camp_here();
    unsigned char eff;
    if (!l) return;
    txt_title("WERVEN");
    if (l->status == ST_BONDGENOOT) {
        txt_message("WERVEN", "Ze staan al aan jouw kant.");
        return;
    }
    if (!flag_get(FLAG_F_TARIK_ZEGEN)) {
        txt_message("WERVEN", "Zonder de zegen van Tarik Ur-Kesh volgt geen Kethari een landvoogd.");
        return;
    }
    eff = l->trust + ((unsigned char)vars[VAR_LOC] == LOC_URKESH ? 0 : ZEGEN_BONUS);
    txt_begin();
    if (eff < TRUST_MIN_WERVEN) {
        txt_str("Ze vertrouwen je nog niet genoeg (");
        txt_num(eff); txt_str(" van "); txt_num(TRUST_MIN_WERVEN);
        txt_str("). Praat met ze, of breng water.");
    } else {
        l->status = ST_BONDGENOOT;
        txt_str("De "); txt_num(l->size); txt_str(" Kethari van ");
        txt_name((unsigned char)vars[VAR_LOC]);
        txt_str(" sluiten zich bij je aan. Geef ze een taak.");
    }
    txt_show();
}

static const char* const taak_items[] = { "Oogsten", "Strijd oefenen", "Geen taak", "Terug" };

static void taak(void)
{
    loc_t* l = camp_here();
    unsigned char k;
    if (!l) return;
    if (l->status != ST_BONDGENOOT) {
        txt_message("TAAK", "Dit kamp volgt je (nog) niet.");
        return;
    }
    txt_title("WELKE TAAK?");
    k = ui_menu_str(taak_items, 4);
    if (k == 3) return;
    l->job = (k == 0) ? JOB_OOGST : (k == 1) ? JOB_STRIJD : JOB_GEEN;
    txt_title("TAAK");
    txt_begin();
    if (l->job == JOB_OOGST) {
        if (flag_get(FLAG_OOGSTMACHINE) && !(l->flags & LF_HARVESTER)) {
            flag_clr(FLAG_OOGSTMACHINE);
            l->flags |= LF_HARVESTER;
            txt_str("De oogstmachine van Mardo rolt het zand in. ");
        }
        txt_str("Ze delven nu "); txt_num(sim_yield(l));
        txt_str(" amber per dag. Hoe dieper ze graven, hoe minder de bodem geeft.");
    } else if (l->job == JOB_STRIJD) {
        txt_str("Ze oefenen met messen en lansen. Hun vaardigheid groeit elke dag.");
    } else {
        txt_str("Ze gaan terug naar hun eigen werk.");
    }
    sim_update_totals();
    game_draw_status();
    txt_show();
}

static void geschenk(void)
{
    loc_t* l = camp_here();
    if (!l) return;
    txt_title("GESCHENK");
    if (l->flags & LF_GESCHENK) {
        txt_message("GESCHENK", "Ze hebben al water van je gekregen.");
        return;
    }
    l->flags |= LF_GESCHENK;
    add_trust(l, TRUST_GESCHENK);
    txt_message("GESCHENK", "Je laat vaten water uit de glider dragen. De kinderen drinken eerst.");
}

static void praat(void)
{
    loc_t* l = camp_here();
    const char* s;
    if (!l) return;
    if (!(l->flags & LF_GESPROKEN)) {
        l->flags |= LF_GESPROKEN;
        add_trust(l, TRUST_PRAAT);
    }
    if (l->status == ST_BONDGENOOT)  s = "De oudste knikt. Je bent een van ons, landvoogd.";
    else if (l->trust < 30)          s = "De oudste kijkt je wantrouwig aan. Stedelingen brengen nooit iets goeds.";
    else if (l->trust < 50)          s = "De oudste luistert. Hij heeft van je gehoord, maar woorden zijn zand.";
    else                             s = "De oudste glimlacht. Het zand fluistert je naam al.";
    txt_message("DE OUDSTE", s);
}

static void rust(void)
{
    sim_day();
    txt_title("RUST");
    txt_begin();
    txt_str("Een dag gaat voorbij. Het is nu dag "); txt_num(vars[VAR_DAY]);
    txt_str(". Amber in het fort: "); txt_num(vars[VAR_AMBER]); txt_str(".");
    txt_show();
}

static void gameover(void)
{
    vm_char(0);
    txt_message("SPEL VOORBIJ", "Ashkara blijft in handen van het Consortium. Druk op vuur om opnieuw te beginnen.");
    longjmp(restart, 1);
}

void builtin(unsigned char id)
{
    switch (id) {
    case BI_KAART:    kaart(); break;
    case BI_TIENDE:   tiende(); break;
    case BI_STATUS:   status(); break;
    case BI_WERVEN:   werven(); break;
    case BI_TAAK:     taak(); break;
    case BI_GESCHENK: geschenk(); break;
    case BI_PRAAT:    praat(); break;
    case BI_RUST:     rust(); break;
    case BI_GAMEOVER: gameover(); break;
    case BI_GEVECHT:  txt_message("AANVAL", "Met wachters en messen win je geen vesting. Later, landvoogd."); break;
    default:          txt_message("NOG NIET GEBOUWD", "Deze functie volgt later."); break;
    }
}
