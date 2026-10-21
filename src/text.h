/* text.h - tekst in het paneel: opbouwen, afbreken op 25 kolommen, pagineren per 5 regels,
   typemachine met praatanimatie (DESIGN.md §5.1, §5.5, §9.2). */
#ifndef ASHKARA_TEXT_H
#define ASHKARA_TEXT_H

/* escapes in script-strings (scriptc.py) */
#define SC_VAR  0xFC     /* gevolgd door var-id: getal */
#define SC_LOC  0xFB     /* naam van de huidige locatie */
#define SC_PLACE 0xFA    /* gevolgd door var-id: naam van de locatie met die index */

extern unsigned char txt_mouth;    /* 1 = personage in beeld: mond animeren tijdens het typen */

void txt_begin(void);
void txt_sc(const unsigned char* sc);     /* script-string (screen codes + escapes) tot $FF */
void txt_str(const char* s);              /* C-string (PETSCII) */
void txt_num(unsigned int v);
void txt_name(unsigned char loc);
void txt_show(void);                      /* tonen; wacht op vuur na elke pagina */

void txt_say(const unsigned char* sc);    /* regel 0 (geel), met escapes */
void txt_title(const char* s);            /* regel 0 (geel), C-string */
void txt_clear(void);                     /* regels 1..5 leeg */

/* korte melding: titel + tekst, wacht op vuur */
void txt_message(const char* title, const char* s);

#endif
