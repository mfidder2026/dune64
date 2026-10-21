/* disk.h - alle disk-I/O loopt hierlangs (DESIGN.md §11.2: later een fastloader inpluggen) */
#ifndef ASHKARA_DISK_H
#define ASHKARA_DISK_H

/* Laadt de payload van een PRG naar addr (zonder de 2 adresbytes), of naar het eigen
   laadadres als addr == 0. Geeft het aantal geladen bytes terug, 0 = fout. */
unsigned int disk_load(const char* name, void* addr);

/* Schrijft size bytes vanaf addr als PRG. Een bestaand bestand wordt eerst gescratcht
   (geen "@0:"-replace: bekende bug in de 1541-ROM). 1 = gelukt. */
unsigned char disk_save(const char* name, const void* addr, unsigned int size);

#endif
