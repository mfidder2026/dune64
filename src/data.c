/* gegenereerd door pipeline/scriptc.py - niet met de hand wijzigen */
#include "game.h"

const char* const scene_files[] = { 0, "titel.scn", "ruimte.scn", "raadzaal.scn", "balkon.scn", "comms.scn", "hangar.scn", "kaart.scn", "woestijn.scn", "kloof.scn", "grot.scn", "oogst.scn", "nacht.scn", "storm.scn", "vesting.scn", "oase.scn", "einde.scn", "vlucht.scn" };
const char* const char_files[] = { 0, "doran.pat", "vesna.pat", "vorr.pat", "mardo.pat", "saira.pat", "tarik.pat" };
const char* const script_files[NLANGS][NSCRIPTS] = {
    { "h1.scr", "h1w.scr" },
    { "h1e.scr", "h1we.scr" }
};

/* engine-nodes (ids.txt 'node') en aankomst-nodes per locatie: script-id, offset */
const noderef_t enodes[] = {
    { 0, 0x0119 },   /* tiende_waarschuwing */
    { 0, 0x013C },   /* gameover_tiende */
    { 0, 0x0124 },   /* overval */
    { 0, 0x012F },   /* gameover_bezet */
};
const noderef_t loc_nodes[] = {
    { 0, 0x0149 },   /* fort -> hangar */
    { 1, 0x0003 },   /* urkesh -> kloof */
    { 1, 0x0108 },   /* sheb -> kamp */
    { 1, 0x0108 },   /* kaim -> kamp */
    { 1, 0x0108 },   /* telmoran -> kamp */
    { 1, 0x0108 },   /* khesset -> kamp */
    { 1, 0x0108 },   /* iruun -> kamp */
    { 1, 0x0108 },   /* varrak -> kamp */
    { 1, 0x0108 },   /* daresh -> kamp */
    { 1, 0x0108 },   /* shaal -> kamp */
    { 1, 0x0108 },   /* khimar -> kamp */
    { 1, 0x0108 },   /* irtessa -> kamp */
    { 1, 0x0108 },   /* oenvaro -> kamp */
    { 1, 0x015B },   /* mijnnoord -> voorpost */
    { 1, 0x015B },   /* mijnoost -> voorpost */
    { 1, 0x015B },   /* zoutmijn -> voorpost */
    { 1, 0x015B },   /* diepemijn -> voorpost */
    { 1, 0x0171 },   /* citadel -> citadel */
    { 1, 0x0182 },   /* mer -> mer */
};

/* ON_DAY-regels op topniveau van alle blokken: game_init() zet ze klaar */
const event_t init_events[] = {
    { 0, { NO_SCRIPT, 0 } }
};

/* startwaarden: type, x, y, status, size, trust, job, skill, equip, richness, green, flags */
const loc_t loc_init[] = {
    { 0, 20,  9, 1,   0,   0, 0, 0, 0,   0, 0, 0x00 },   /* fort */
    { 1, 24, 14, 1,  40,  30, 0, 0, 0, 120, 0, 0x00 },   /* urkesh */
    { 1,  8,  6, 0,  25,  25, 0, 0, 0, 160, 0, 0x04 },   /* sheb */
    { 1, 31,  4, 0,  30,  25, 0, 0, 0,  90, 0, 0x00 },   /* kaim */
    { 1,  4, 13, 0,  15,  35, 0, 0, 0,  70, 0, 0x00 },   /* telmoran */
    { 1, 14, 12, 0,  50,  20, 0, 0, 0, 200, 0, 0x04 },   /* khesset */
    { 1, 33, 13, 0,  35,  30, 0, 0, 0, 140, 0, 0x00 },   /* iruun */
    { 1, 28,  6, 0,  20,  40, 0, 0, 0,  60, 0, 0x00 },   /* varrak */
    { 1, 11,  9, 0,  60,  15, 0, 0, 0, 220, 0, 0x04 },   /* daresh */
    { 1, 37,  6, 0,  45,  20, 0, 0, 0, 110, 0, 0x00 },   /* shaal */
    { 1, 19, 15, 0,  25,  35, 0, 0, 0,  90, 0, 0x00 },   /* khimar */
    { 1,  2,  2, 0,  90,  10, 0, 0, 0, 180, 0, 0x00 },   /* irtessa */
    { 1, 36, 15, 0,  30,  25, 0, 0, 0, 130, 0, 0x00 },   /* oenvaro */
    { 2, 13,  3, 1,  30,   0, 0, 0, 0,   0, 0, 0x00 },   /* mijnnoord */
    { 2, 35, 10, 1,  45,   0, 0, 0, 0,   0, 0, 0x00 },   /* mijnoost */
    { 2,  9, 15, 1,  55,   0, 0, 0, 0,   0, 0, 0x00 },   /* zoutmijn */
    { 2, 28,  2, 1,  75,   0, 0, 0, 0,   0, 0, 0x00 },   /* diepemijn */
    { 3, 21,  1, 1, 150,   0, 0, 0, 0,   0, 0, 0x00 },   /* citadel */
    { 4,  5,  4, 1,   0,   0, 0, 0, 0,   0, 0, 0x00 },   /* mer */
};

/* namen in screen codes, $FF-afgesloten; per taal */
static const unsigned char n0[] = { 0x46, 0x0F, 0x12, 0x14, 0x20, 0x56, 0x01, 0x12, 0x0F, 0xFF };
static const unsigned char n1[] = { 0x52, 0x0F, 0x04, 0x05, 0x20, 0x4B, 0x0C, 0x0F, 0x0F, 0x06, 0xFF };
static const unsigned char e1[] = { 0x52, 0x05, 0x04, 0x20, 0x47, 0x0F, 0x12, 0x07, 0x05, 0xFF };
static const unsigned char n2[] = { 0x53, 0x08, 0x05, 0x02, 0x2D, 0x41, 0x0E, 0x01, 0x12, 0xFF };
static const unsigned char n3[] = { 0x4B, 0x01, 0x09, 0x0D, 0xFF };
static const unsigned char n4[] = { 0x54, 0x05, 0x0C, 0x2D, 0x4D, 0x0F, 0x12, 0x01, 0x0E, 0xFF };
static const unsigned char n5[] = { 0x4F, 0x15, 0x04, 0x2D, 0x4B, 0x08, 0x05, 0x13, 0x13, 0x05, 0x14, 0xFF };
static const unsigned char n6[] = { 0x5A, 0x01, 0x0E, 0x04, 0x2D, 0x49, 0x12, 0x15, 0x15, 0x0E, 0xFF };
static const unsigned char n7[] = { 0x56, 0x01, 0x12, 0x12, 0x01, 0x0B, 0xFF };
static const unsigned char n8[] = { 0x44, 0x01, 0x12, 0x05, 0x13, 0x08, 0xFF };
static const unsigned char n9[] = { 0x53, 0x08, 0x01, 0x01, 0x0C, 0xFF };
static const unsigned char n10[] = { 0x4B, 0x08, 0x09, 0x0D, 0x01, 0x12, 0xFF };
static const unsigned char n11[] = { 0x49, 0x12, 0x2D, 0x54, 0x05, 0x13, 0x13, 0x01, 0xFF };
static const unsigned char n12[] = { 0x4F, 0x05, 0x0E, 0x2D, 0x56, 0x01, 0x12, 0x0F, 0xFF };
static const unsigned char n13[] = { 0x4D, 0x09, 0x0A, 0x0E, 0x20, 0x4E, 0x0F, 0x0F, 0x12, 0x04, 0xFF };
static const unsigned char e13[] = { 0x4E, 0x0F, 0x12, 0x14, 0x08, 0x20, 0x4D, 0x09, 0x0E, 0x05, 0xFF };
static const unsigned char n14[] = { 0x4D, 0x09, 0x0A, 0x0E, 0x20, 0x4F, 0x0F, 0x13, 0x14, 0xFF };
static const unsigned char e14[] = { 0x45, 0x01, 0x13, 0x14, 0x20, 0x4D, 0x09, 0x0E, 0x05, 0xFF };
static const unsigned char n15[] = { 0x5A, 0x0F, 0x15, 0x14, 0x0D, 0x09, 0x0A, 0x0E, 0xFF };
static const unsigned char e15[] = { 0x53, 0x01, 0x0C, 0x14, 0x20, 0x4D, 0x09, 0x0E, 0x05, 0xFF };
static const unsigned char n16[] = { 0x44, 0x09, 0x05, 0x10, 0x05, 0x20, 0x4D, 0x09, 0x0A, 0x0E, 0xFF };
static const unsigned char e16[] = { 0x44, 0x05, 0x05, 0x10, 0x20, 0x4D, 0x09, 0x0E, 0x05, 0xFF };
static const unsigned char n17[] = { 0x44, 0x05, 0x20, 0x43, 0x09, 0x14, 0x01, 0x04, 0x05, 0x0C, 0xFF };
static const unsigned char e17[] = { 0x54, 0x08, 0x05, 0x20, 0x43, 0x09, 0x14, 0x01, 0x04, 0x05, 0x0C, 0xFF };
static const unsigned char n18[] = { 0x5A, 0x0F, 0x15, 0x14, 0x16, 0x0C, 0x01, 0x0B, 0x14, 0x05, 0x20, 0x4D, 0x05, 0x12, 0xFF };
static const unsigned char e18[] = { 0x4D, 0x05, 0x12, 0x20, 0x53, 0x01, 0x0C, 0x14, 0x20, 0x46, 0x0C, 0x01, 0x14, 0xFF };
const unsigned char* const loc_names[NLANGS][NLOCS] = {
    { n0, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, n16, n17, n18 },
    { n0, e1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, e13, e14, e15, e16, e17, e18 }
};
