/* disk.h - alle disk-I/O loopt hierlangs (DESIGN.md §11): Kernal of de eigen fastloader */
#ifndef ASHKARA_DISK_H
#define ASHKARA_DISK_H

/* Laadt de payload van een PRG naar addr (zonder de 2 adresbytes), of naar het eigen
   laadadres als addr == 0. Geeft het aantal geladen bytes terug, 0 = fout. */
unsigned int disk_load(const char* name, void* addr);

/* Schrijft size bytes vanaf addr als PRG. Een bestaand bestand wordt eerst gescratcht
   (geen "@0:"-replace: bekende bug in de 1541-ROM). 1 = gelukt. Een actieve fastloader
   wordt daarvoor even gestopt en daarna opnieuw geïnstalleerd. */
unsigned char disk_save(const char* name, const void* addr, unsigned int size);

/* Fastloader: drivecode staat (na het laden van extra.bin) onder de I/O; installeren lukt
   alleen als de drive 1541-code draait en op de ping antwoordt. */
void          disk_set_drive_code(void);
unsigned char disk_fast_install(void);
unsigned char disk_fast_active(void);

/* kopiëren van/naar de RAM onder de I/O ($D000-$DFFF) */
void io_copy(void* dst, const void* src, unsigned int n);

#endif
