/* battle.c - @GEVECHT (DESIGN.md §4.5): kies tot 3 kampen en of Ilan meegaat, zie de kans,
   val aan. De uitslag draait als script-node (gevecht_gewonnen, kamp_bevrijd, einde_militair,
   gevecht_verloren, gameover_gesneuveld) via sim_pending, met de plaats in gevecht_loc. */
#include <stdlib.h>
#include <string.h>
#include "ui.h"
#include "game.h"
#include "sim.h"
#include "text.h"
#include "battle.h"
#include "sound.h"

#define MAX_SIDE        3
#define GARRISON_BEZET  60      /* bezet kamp: een kleine wacht */
#define CITADEL_HINTS   2       /* na zoveel veroverde voorposten verraden officieren de Citadel */

static const unsigned char factor10[4] = { 10, 14, 20, 30 };   /* uitrusting x1.0 .. x3.0 */

static unsigned char cand[NLOCS], n_cand, chosen[NLOCS], ilan;
static unsigned char item_buf[NLOCS + 2][TEXT_WIDTH];
static const unsigned char* items[NLOCS + 2];

/* size x (1 + skill/50) x factor */
unsigned int battle_power(const loc_t* l)
{
    return (unsigned int)((unsigned long)l->size * (50 + l->skill) * factor10[l->equip] / 500);
}

static unsigned int garrison(const loc_t* t)
{
    if (t->type == LT_VOORPOST || t->type == LT_CITADEL) return t->size * 4;
    return GARRISON_BEZET;
}

static unsigned int side_power(void)
{
    unsigned char i;
    unsigned int k = 0;
    for (i = 0; i < n_cand; ++i)
        if (chosen[i]) k += battle_power(&locs[cand[i]]);
    return ilan ? k + k / 5 : k;              /* Ilan mee: x1.2 */
}

static unsigned char chance256(unsigned int k, unsigned int g)
{
    if (!k) return 0;
    return (unsigned char)((unsigned long)k * 255 / (k + g));
}

static unsigned char n_chosen(void)
{
    unsigned char i, n = 0;
    for (i = 0; i < n_cand; ++i) n += chosen[i];
    return n;
}

/* één regel: "* Naam 132" in screen codes */
static void camp_item(unsigned char i)
{
    unsigned char* d = item_buf[i];
    const unsigned char* s = loc_names[lang][cand[i]];
    unsigned int p = battle_power(&locs[cand[i]]);
    unsigned char c = 0, n = 0, dig[5];
    d[c++] = chosen[i] ? 42 : 45;             /* '*' gekozen, '-' niet */
    d[c++] = 32;
    while (*s != SC_END && c < 17) d[c++] = *s++;
    d[c++] = 32;
    do { dig[n++] = 48 + p % 10; p /= 10; } while (p);
    while (n) d[c++] = dig[--n];
    d[c] = SC_END;
    items[i] = d;
}

static unsigned char digits(unsigned int v)
{
    unsigned char n = 1;
    while (v >= 10) { v /= 10; ++n; }
    return n;
}

/* kopregel: "KRACHT 528 TEGEN 120 81%" */
static void header(unsigned int k, unsigned int g)
{
    unsigned char pct = (unsigned char)((unsigned int)chance256(k, g) * 100 / 255), c;
    ui_text(0, L("KRACHT", "STRENGTH"), COL_YELLOW);
    c = lang ? 9 : 7;
    ui_number(0, c, k, COL_WHITE);  c += digits(k) + 1;
    ui_text_at(0, c, L("TEGEN", "VS"), COL_YELLOW);  c += lang ? 3 : 6;
    ui_number(0, c, g, COL_WHITE);  c += digits(g) + 1;
    ui_number(0, c, pct, COL_GREEN);  c += digits(pct);
    ui_text_at(0, c, "%", COL_GREEN);
}

static void hurt(unsigned char half)
{
    unsigned char i;
    loc_t* l;
    for (i = 0; i < n_cand; ++i) {
        if (!chosen[i]) continue;
        l = &locs[cand[i]];
        l->size -= half ? l->size / 2 : l->size / 10;
    }
}

void battle(void)
{
    unsigned char i, sel, target = (unsigned char)vars[VAR_LOC], won;
    loc_t* t = &locs[target];
    unsigned int k, g = garrison(t);

    if (!(t->type == LT_VOORPOST || t->type == LT_CITADEL || t->status == ST_BEZET)) {
        txt_message(L("AANVAL", "ATTACK"), L("Hier valt niets aan te vallen.", "There is nothing to attack here."));
        return;
    }
    n_cand = 0;
    for (i = 0; i < NLOCS; ++i)
        if (locs[i].type == LT_KAMP && locs[i].status == ST_BONDGENOOT && locs[i].size && i != target)
            cand[n_cand++] = i;
    if (!n_cand) {
        txt_message(L("AANVAL", "ATTACK"), L("Geen enkel kamp kan voor je vechten. Werf eerst krijgers.",
                                             "No camp can fight for you. Recruit warriors first."));
        return;
    }
    memset(chosen, 0, sizeof(chosen));
    ilan = 0;
    sel = 0;
    for (;;) {
        for (i = 0; i < n_cand; ++i) camp_item(i);
        ui_sc(ilan ? L("Ilan gaat mee: ja", "Ilan joins: yes") : L("Ilan gaat mee: nee", "Ilan joins: no"), item_buf[n_cand]);
        items[n_cand] = item_buf[n_cand];
        ui_sc(L("AANVALLEN!", "ATTACK!"), item_buf[n_cand + 1]);
        items[n_cand + 1] = item_buf[n_cand + 1];
        ui_sc(L("Terug", "Back"), item_buf[NLOCS + 1]);
        items[n_cand + 2] = item_buf[NLOCS + 1];
        k = side_power();
        header(k, g);
        ui_menu_sel = sel;
        sel = ui_menu(items, n_cand + 3);
        if (sel < n_cand) {
            if (chosen[sel] || n_chosen() < MAX_SIDE) chosen[sel] ^= 1;
        } else if (sel == n_cand) {
            ilan ^= 1;
        } else if (sel == n_cand + 1) {
            if (n_chosen()) break;
        } else {
            txt_clear();
            return;
        }
    }

    sim_day();                                   /* een aanval kost een dag */
    won = (unsigned char)(rand() & 0xFF) < chance256(k, g);
    vars[VAR_GEVECHT_LOC] = target;
    if (won) {
        hurt(0);
        if (t->type == LT_CITADEL) {
            sim_pend(&enodes[ENODE_EINDE_MILITAIR], 1);
        } else if (t->type == LT_VOORPOST) {
            t->type = LT_KAMP;                       /* gevangenen komen vrij en sluiten zich aan */
            t->status = ST_BONDGENOOT;
            t->size = (unsigned char)(g / 8);
            t->trust = 80;
            t->job = JOB_GEEN;
            t->skill = 20;
            t->equip = 1;
            t->richness = 100;
            if (++vars[VAR_VEROVERD] >= CITADEL_HINTS) flag_set(FLAG_F_CITADEL);
            sim_pend(&enodes[ENODE_GEVECHT_GEWONNEN], 1);
        } else {
            t->status = ST_BONDGENOOT;               /* bevrijd kamp: +30 vertrouwen */
            t->trust = (t->trust + 30 > 100) ? 100 : t->trust + 30;
            sim_pend(&enodes[ENODE_KAMP_BEVRIJD], 1);
        }
    } else {
        hurt(1);
        sfx(SFX_ALARM);
        sim_pend(&enodes[ilan ? ENODE_GAMEOVER_GESNEUVELD : ENODE_GEVECHT_VERLOREN], 1);
    }
    sim_update_totals();
    game_draw_status();
    txt_clear();
}
