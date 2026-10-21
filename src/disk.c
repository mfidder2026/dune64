/* disk.c - laden via de Kernal. Zie DESIGN.md §11. */
#include <cbm.h>
#include "disk.h"

static unsigned char drive(void)
{
    unsigned char d = *(unsigned char*)0xBA;   /* laatst gebruikte drive */
    return (d >= 8 && d <= 11) ? d : 8;
}

unsigned int disk_load(const char* name, void* addr)
{
    return cbm_load(name, drive(), addr);
}
