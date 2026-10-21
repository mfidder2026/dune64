/* vm.h - verhaal-VM: voert de bytecode van pipeline/scriptc.py uit (DESIGN.md §9) */
#ifndef ASHKARA_VM_H
#define ASHKARA_VM_H
#include "game.h"

#define NODE_START 0     /* node-argument: begin van het blok (first_node uit de header) */

/* Laadt scriptblok `script` en voert vanaf `node` uit. Komt niet terug. */
void vm_run(unsigned char script, unsigned int node);

/* Voor builtins en de kaart */
void vm_scene(unsigned char id);   /* scène laden (zelfde scène = niets), paneel tekenen */
void vm_char(unsigned char id);    /* personage tonen (0 = geen) */
void vm_show(void);                /* beeld aan als een scène net geladen is */

/* Na een builtin: hierheen springen in plaats van terug naar het menu (script == NO_SCRIPT: niet). */
extern noderef_t vm_next;

#endif
