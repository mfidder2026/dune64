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
        txt_message(L("HIER NIET", "NOT HERE"), L("Dit is geen kamp van de Kethari.", "This is not a Kethari camp."));
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
    static const char* const st[NLANGS][5] = {
        { "onbekend", "bekend", "bondgenoot", "bezet", "groen" },
        { "unknown", "known", "ally", "occupied", "green" } };
    static const char* const job[NLANGS][4] = {
        { "geen", "oogsten", "strijd", "vergroenen" },
        { "none", "harvest", "battle training", "greening" } };
    if (!l) return;
    txt_title(L("STATUS", L("STATUS", "STATUS")));
    txt_begin();
    txt_name((unsigned char)vars[VAR_LOC]);
    txt_str(": "); txt_str(st[lang][l->status]); txt_str(". ");
    txt_num(l->size); txt_str(L(" Kethari, vertrouwen ", " Kethari, trust ")); txt_num(l->trust);
    txt_str(L(". Taak: ", ". Task: ")); txt_str(job[lang][l->job]);
    txt_str(L(". Amber in de bodem: ", ". Amber in the ground: ")); txt_num(l->richness); txt_str(".");
    if (l->job == JOB_OOGST) { txt_str(L(" Opbrengst: ", " Yield: ")); txt_num(sim_yield(l)); txt_str(L(" per dag.", " per day.")); }
    if (l->flags & LF_HARVESTER) txt_str(L(" Met oogstmachine.", " With harvester."));
    txt_show();
}

static void werven(void)
{
    loc_t* l = camp_here();
    unsigned char eff;
    if (!l) return;
    txt_title(L("WERVEN", "RECRUIT"));
    if (l->status == ST_BONDGENOOT) {
        txt_message(L("WERVEN", "RECRUIT"), L("Ze staan al aan jouw kant.", "They are already on your side."));
        return;
    }
    if (l->status == ST_BEZET) {
        txt_message(L("WERVEN", "RECRUIT"), L("Het Consortium houdt dit kamp bezet.", "The Consortium occupies this camp."));
        return;
    }
    if (!flag_get(FLAG_F_TARIK_ZEGEN)) {
        txt_message(L("WERVEN", "RECRUIT"), L("Zonder de zegen van Tarik Ur-Kesh volgt geen Kethari een landvoogd.", "Without the blessing of Tarik Ur-Kesh, no Kethari will follow a governor."));
        return;
    }
    eff = l->trust + ((unsigned char)vars[VAR_LOC] == LOC_URKESH ? 0 : ZEGEN_BONUS);
    txt_begin();
    if (eff < TRUST_MIN_WERVEN) {
        txt_str(L("Ze vertrouwen je nog niet genoeg (", "They do not trust you enough yet ("));
        txt_num(eff); txt_str(L(" van ", " of ")); txt_num(TRUST_MIN_WERVEN);
        txt_str(L("). Praat met ze, of breng water.", "). Talk to them, or bring water."));
    } else {
        l->status = ST_BONDGENOOT;
        txt_str(L("De ", "The ")); txt_num(l->size); txt_str(L(" Kethari van ", " Kethari of "));
        txt_name((unsigned char)vars[VAR_LOC]);
        txt_str(L(" sluiten zich bij je aan. Geef ze een taak.", " join you. Give them a task."));
    }
    txt_show();
}

static const char* const taak_items[NLANGS][4] = {
    { "Oogsten", "Strijd oefenen", "Geen taak", "Terug" },
    { "Harvest", "Train for battle", "No task", "Back" } };

static void taak(void)
{
    loc_t* l = camp_here();
    unsigned char k;
    if (!l) return;
    if (l->status != ST_BONDGENOOT) {
        txt_message(L("TAAK", "TASK"), L("Dit kamp volgt je (nog) niet.", "This camp does not follow you (yet)."));
        return;
    }
    txt_title(L("WELKE TAAK?", "WHICH TASK?"));
    k = ui_menu_str(taak_items[lang], 4);
    if (k == 3) return;
    l->job = (k == 0) ? JOB_OOGST : (k == 1) ? JOB_STRIJD : JOB_GEEN;
    txt_title(L("TAAK", "TASK"));
    txt_begin();
    if (l->job == JOB_OOGST) {
        if (flag_get(FLAG_OOGSTMACHINE) && !(l->flags & LF_HARVESTER)) {
            flag_clr(FLAG_OOGSTMACHINE);
            l->flags |= LF_HARVESTER;
            txt_str(L("De oogstmachine van Mardo rolt het zand in. ", "Mardo's harvester rolls out onto the sand. "));
        }
        txt_str(L("Ze delven nu ", "They now mine ")); txt_num(sim_yield(l));
        txt_str(L(" amber per dag. Hoe dieper ze graven, hoe minder de bodem geeft.", " amber per day. The deeper they dig, the less the ground gives."));
    } else if (l->job == JOB_STRIJD) {
        txt_str(L("Ze oefenen met messen en lansen. Hun vaardigheid groeit elke dag.", "They train with knives and lances. Their skill grows every day."));
    } else {
        txt_str(L("Ze gaan terug naar hun eigen werk.", "They go back to their own work."));
    }
    sim_update_totals();
    game_draw_status();
    txt_show();
}

static void geschenk(void)
{
    loc_t* l = camp_here();
    if (!l) return;
    txt_title(L("GESCHENK", "GIFT"));
    if (l->flags & LF_GESCHENK) {
        txt_message(L("GESCHENK", "GIFT"), L("Ze hebben al water van je gekregen.", "They have already had water from you."));
        return;
    }
    l->flags |= LF_GESCHENK;
    add_trust(l, TRUST_GESCHENK);
    txt_message(L("GESCHENK", "GIFT"), L("Je laat vaten water uit de glider dragen. De kinderen drinken eerst.", "You have barrels of water carried from the glider. The children drink first."));
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
    if (l->status == ST_BONDGENOOT)  s = L("De oudste knikt. Je bent een van ons, landvoogd.", "The elder nods. You are one of us, governor.");
    else if (l->trust < 30)          s = L("De oudste kijkt je wantrouwig aan. Stedelingen brengen nooit iets goeds.", "The elder eyes you warily. City folk never bring anything good.");
    else if (l->trust < 50)          s = L("De oudste luistert. Hij heeft van je gehoord, maar woorden zijn zand.", "The elder listens. He has heard of you, but words are sand.");
    else                             s = L("De oudste glimlacht. Het zand fluistert je naam al.", "The elder smiles. The sand already whispers your name.");
    txt_message(L("DE OUDSTE", "THE ELDER"), s);
}

static void rust(void)
{
    sim_day();
    txt_title(L("RUST", "REST"));
    txt_begin();
    txt_str(L("Een dag gaat voorbij. Het is nu dag ", "A day passes. It is now day ")); txt_num(vars[VAR_DAY]);
    txt_str(L(". Amber in het fort: ", ". Amber in the fort: ")); txt_num(vars[VAR_AMBER]); txt_str(".");
    txt_show();
}

static void laden(void)
{
    txt_title(L("LADEN", "LOAD"));
    if (!game_load()) {
        txt_message(L("LADEN", "LOAD"), L("Geen opgeslagen spel gevonden (of van een oudere versie).", "No saved game found (or from an older version)."));
        return;
    }
    sim_pending.script = NO_SCRIPT;
    sim_update_totals();
    game_draw_status();
    txt_begin();
    txt_str(L("Spel geladen: dag ", "Game loaded: day ")); txt_num(vars[VAR_DAY]); txt_str(", ");
    txt_name((unsigned char)vars[VAR_LOC]); txt_str(".");
    txt_show();
    vm_next = loc_nodes[(unsigned char)vars[VAR_LOC]];
}

static const char* const disk_items[NLANGS][4] = {
    { "Spel opslaan", "Spel laden", "Language: English", "Terug" },
    { "Save game", "Load game", "Taal: Nederlands", "Back" } };

static void opslaan(void)
{
    unsigned char k;
    txt_title(L("OPSLAAN / LADEN", "SAVE / LOAD"));
    k = ui_menu_str(disk_items[lang], 4);
    if (k == 1) { laden(); return; }
    if (k == 2) { vm_set_lang(!lang); return; }
    if (k != 0) return;
    txt_title(L("OPSLAAN", "SAVE"));
    txt_clear();
    ui_text(1, L("Bezig met opslaan...", "Saving..."), COL_WHITE);
    if (game_save()) txt_message(L("OPSLAAN", "SAVE"), L("Opgeslagen als ASHKARA.SAV.", "Saved as ASHKARA.SAV."));
    else             txt_message(L("OPSLAAN", "SAVE"), L("Opslaan mislukt. Is de diskette beveiligd of vol?", "Saving failed. Is the disk write-protected or full?"));
}

static void gameover(void)
{
    vm_char(0);
    txt_message(L("SPEL VOORBIJ", "GAME OVER"), L("Ashkara blijft in handen van het Consortium. Druk op vuur om opnieuw te beginnen.", "Ashkara remains in the hands of the Consortium. Press fire to start again."));
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
    case BI_OPSLAAN:  opslaan(); break;
    case BI_LADEN:    laden(); break;
    case BI_GEVECHT:  txt_message(L("AANVAL", "ATTACK"), L("Met wachters en messen win je geen vesting. Later, landvoogd.", "Guards and knives will not take a fortress. Later, governor.")); break;
    default:          txt_message(L("NOG NIET GEBOUWD", "NOT BUILT YET"), L("Deze functie volgt later.", "This feature comes later.")); break;
    }
}
