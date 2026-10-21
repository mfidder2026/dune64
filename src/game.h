/* game.h - spelstatus: vlaggen, variabelen, locaties, tijd-events (DESIGN.md §4, §9) */
#ifndef ASHKARA_GAME_H
#define ASHKARA_GAME_H
#include "ids.h"

#define NVARS   32
#define NFLAGS  256
#define NEVENTS 8
#define NO_SCRIPT 0xFF

/* locatiestatus en taken (§4.3) */
enum { ST_ONBEKEND, ST_BEKEND, ST_BONDGENOOT, ST_BEZET, ST_GROEN };
enum { JOB_GEEN, JOB_OOGST, JOB_STRIJD, JOB_GROEN };

/* Eén record per locatie op de kaart (fort, kampen, voorposten, Citadel, handelspost).
   Voor kampen zijn alle velden zinvol; voor voorposten is size = garnizoen / 4. */
typedef struct {
    unsigned char type;      /* LT_*                                        */
    unsigned char x, y;      /* kaartcel                                    */
    unsigned char status;    /* ST_*                                        */
    unsigned char size;      /* aantal Kethari (10..90)                     */
    unsigned char trust;     /* 0..100 (werven kan vanaf 50)               */
    unsigned char job;       /* JOB_*                                       */
    unsigned char skill;     /* 0..100                                      */
    unsigned char equip;     /* 0..3                                        */
    unsigned char richness;  /* resterend amber in de bodem                 */
    unsigned char green;     /* 0..100                                      */
    unsigned char flags;     /* LF_*                                        */
} loc_t;                     /* 12 bytes                                    */

typedef struct {
    unsigned char script;    /* NO_SCRIPT = geen */
    unsigned int  node;      /* offset in het scriptblok */
} noderef_t;

typedef struct {
    unsigned int  day;
    noderef_t     target;    /* target.script == NO_SCRIPT: vrij slot */
} event_t;

/* De complete spelstatus in één blok: opslaan = dit blok 1-op-1 wegschrijven (§11.3).
   Verander je de indeling (meer vars, locaties ...), verhoog dan SAVE_VERSION. */
#define SAVE_MAGIC   0xA5
#define SAVE_VERSION 1

typedef struct {
    unsigned char magic, version;
    unsigned int  vars[NVARS];
    unsigned char flags[NFLAGS / 8];
    loc_t         locs[NLOCS];
    event_t       events[NEVENTS];
} state_t;

extern state_t state;
#define vars   (state.vars)
#define locs   (state.locs)
#define events (state.events)

/* data.c (gegenereerd door scriptc.py) */
extern const char* const scene_files[];
extern const char* const char_files[];
extern const char* const script_files[NLANGS][NSCRIPTS];
extern const noderef_t enodes[];
extern const noderef_t loc_nodes[];
extern const loc_t loc_init[];
extern const event_t init_events[];       /* afgesloten met target.script == NO_SCRIPT */
extern const unsigned char* const loc_names[NLANGS][NLOCS];

/* Taal (LANG_NL / LANG_EN): een voorkeur, geen spelstatus, dus niet in de savegame. */
extern unsigned char lang;
#define L(nl, en) (lang ? (en) : (nl))

#define HERE (&locs[(unsigned char)vars[VAR_LOC]])

void          game_init(void);
unsigned char flag_get(unsigned char f);
void          flag_set(unsigned char f);
void          flag_clr(unsigned char f);
void          game_add_event(unsigned int day, unsigned char script, unsigned int node);
void          game_draw_status(void);
unsigned char game_save(void);           /* 1 = gelukt */
unsigned char game_load(void);           /* 1 = gelukt; status ongewijzigd bij een fout */

#endif
