/* sim.c - sim_day(): één speldag (DESIGN.md §4.7): taken (OOGST, STRIJD), overvallen van het
   Consortium, de Tiende en tijd-events. Vergroening volgt in fase 4. */
#include <stdlib.h>
#include "game.h"
#include "sim.h"

noderef_t sim_pending = { NO_SCRIPT, 0 };

void sim_pend(const noderef_t* n, unsigned char force)
{
    if (force || sim_pending.script == NO_SCRIPT) sim_pending = *n;
}

/* §4.3: size x min(richness, 100) / 200, x2 met oogstmachine.
   40 Kethari, richness 100, met machine -> 40 amber per dag. */
unsigned int sim_yield(const loc_t* l)
{
    unsigned int y = (unsigned int)l->size * (l->richness < 100 ? l->richness : 100) / 200;
    return (l->flags & LF_HARVESTER) ? y * 2 : y;
}

void sim_update_totals(void)
{
    unsigned char i, n = 0;
    unsigned int krijgers = 0, green = 0;
    const loc_t* l;
    for (i = 0; i < NLOCS; ++i) {
        l = &locs[i];
        if (l->type != LT_KAMP && l->type != LT_VOORPOST) continue;
        green += l->green; ++n;
        if (l->status == ST_BONDGENOOT && l->job == JOB_STRIJD) krijgers += l->size;
    }
    vars[VAR_KRIJGERS] = krijgers;
    vars[VAR_GROEN] = n ? green / n : 0;
}

#define RAID_RANGE  6     /* een STRIJD-kamp beschermt kampen binnen 6 cellen (Manhattan) */
#define RAID_TRUST 20     /* vertrouwensverlies van een overvallen kamp */

static unsigned char protected_by_strijd(const loc_t* c)
{
    unsigned char i;
    const loc_t* l;
    for (i = 0; i < NLOCS; ++i) {
        l = &locs[i];
        if (l == c || l->status != ST_BONDGENOOT || l->job != JOB_STRIJD) continue;
        if (abs((int)l->x - c->x) + abs((int)l->y - c->y) <= RAID_RANGE) return 1;
    }
    return 0;
}

/* §4.5: per onbeschermd OOGST-kamp per dag 2 % + 1 % per 20 amber/dag. Het kamp wordt BEZET,
   de taak vervalt en het vertrouwen daalt. Geen bondgenoot meer over = game over, maar pas
   een dag na de laatste overval, zodat de speler eerst het bericht ziet. */
static void raids(void)
{
    unsigned char i, chance, allies = 0, occupied = 0, raided = 0;
    loc_t* l;
    for (i = 0; i < NLOCS; ++i) {
        l = &locs[i];
        if (l->type != LT_KAMP) continue;
        if (l->status == ST_BONDGENOOT && l->job == JOB_OOGST && !protected_by_strijd(l)) {
            chance = 2 + sim_yield(l) / 20;
            if ((unsigned char)(rand() % 100) < chance) {
                l->status = ST_BEZET;
                l->job = JOB_GEEN;
                l->trust = (l->trust > RAID_TRUST) ? l->trust - RAID_TRUST : 0;
                vars[VAR_OVERVAL_LOC] = i;
                raided = 1;
                sim_pend(&enodes[ENODE_OVERVAL], 0);
            }
        }
        if (l->status == ST_BONDGENOOT) ++allies;
        if (l->status == ST_BEZET) ++occupied;
    }
    if (!allies && occupied && !raided) sim_pend(&enodes[ENODE_GAMEOVER_BEZET], 1);
}

#define GREEN_ABANDON 60      /* gemiddeld groen rond een voorpost waarbij het Consortium vertrekt */
#define ABANDON_RANGE 8       /* ruimer dan RAID_RANGE: elke voorpost heeft zo een kamp in de buurt */
#define GREEN_WIN     50      /* groen % voor de groene overwinning (zonder voorposten) */

/* §4.6: voorposten in een groen gebied worden opgegeven; genoeg groen = de Citadel geeft op. */
static void greening(void)
{
    unsigned char i, j, n, outposts = 0;
    unsigned int sum;
    loc_t* v;
    const loc_t* c;
    for (i = 0; i < NLOCS; ++i) {
        v = &locs[i];
        if (v->type != LT_VOORPOST) continue;
        sum = 0; n = 0;
        for (j = 0; j < NLOCS; ++j) {
            c = &locs[j];
            if (c->type != LT_KAMP || c->status == ST_BEZET) continue;      /* bezet: telt niet mee */
            if (abs((int)c->x - v->x) + abs((int)c->y - v->y) > ABANDON_RANGE) continue;
            sum += c->green; ++n;
        }
        if (n && sum / n >= GREEN_ABANDON) {
            v->type = LT_KAMP;                   /* het land is groen: een nieuw kamp */
            v->status = ST_BONDGENOOT;
            v->size = 10; v->trust = 60; v->green = GREEN_ABANDON; v->richness = 0; v->job = JOB_GEEN;
            vars[VAR_GEVECHT_LOC] = i;
            sim_pend(&enodes[ENODE_VOORPOST_VERLATEN], 0);
        } else {
            ++outposts;
        }
    }
    sim_update_totals();
    if (!outposts && vars[VAR_GROEN] >= GREEN_WIN) sim_pend(&enodes[ENODE_EINDE_GROEN], 1);
}

void sim_day(void)
{
    unsigned char i, d, grow;
    unsigned int y;
    loc_t* l;
    event_t* e;

    /* 1. taken van de kampen; na het verraad groeit de opstand: elke 5 dagen +1 per kamp */
    grow = flag_get(FLAG_F_VERRAAD) && vars[VAR_DAY] % 5 == 0;
    for (i = 0; i < NLOCS; ++i) {
        l = &locs[i];
        if (l->status != ST_BONDGENOOT) continue;
        if (grow && l->type == LT_KAMP && l->size < 90) ++l->size;
        switch (l->job) {
        case JOB_OOGST:
            y = sim_yield(l);
            vars[VAR_AMBER] = (vars[VAR_AMBER] + y > AMBER_MAX) ? AMBER_MAX : vars[VAR_AMBER] + y;
            d = (unsigned char)(y / 4);
            l->richness = (l->richness > d) ? l->richness - d : 0;
            break;
        case JOB_STRIJD:                        /* Doran traint mee: +4 */
            d = flag_get(FLAG_F_DORAN_TERUG) ? 4 : 2;
            l->skill = (l->skill + d > 100) ? 100 : l->skill + d;
            break;
        case JOB_GROEN:                         /* alleen met windvanger (§4.3) */
            if (!(l->flags & LF_WINDVANGER)) break;
            l->green = (l->green + 2 > 100) ? 100 : l->green + 2;
            if (l->green >= 60) l->richness = 0;
            break;
        }
    }
    /* 2. overvallen (vanaf hoofdstuk 2), 3. vergroening: fase 4 */
    if (flag_get(FLAG_F_OVERVALLEN)) raids();
    if (flag_get(FLAG_F_VERRAAD)) greening();

    ++vars[VAR_DAY];

    /* 4. de Tiende: na de deadline één keer 3 dagen uitstel, daarna game over */
    if (flag_get(FLAG_TIENDE_OPEN) && vars[VAR_DAY] > vars[VAR_TIENDE_DAG]) {
        if (!flag_get(FLAG_TIENDE_UITSTEL)) {
            flag_set(FLAG_TIENDE_UITSTEL);
            vars[VAR_TIENDE_DAG] += 3;
            sim_pend(&enodes[ENODE_TIENDE_WAARSCHUWING], 0);
        } else {
            sim_pend(&enodes[ENODE_GAMEOVER_TIENDE], 1);
        }
    }

    /* 5. tijd-events uit de scripts */
    for (i = 0; i < NEVENTS; ++i) {
        e = &events[i];
        if (e->target.script != NO_SCRIPT && vars[VAR_DAY] >= e->day && sim_pending.script == NO_SCRIPT) {
            sim_pend(&e->target, 0);
            e->target.script = NO_SCRIPT;
        }
    }

    sim_update_totals();
    game_draw_status();
}
