/* disk.c - laden via de Kernal. Zie DESIGN.md §11. */
#include <cbm.h>
#include <string.h>
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

unsigned char disk_save(const char* name, const void* addr, unsigned int size)
{
    static char cmd[24] = "s0:";
    unsigned char dev = drive();
    strcpy(cmd + 3, name);
    if (cbm_open(15, dev, 15, cmd) == 0) cbm_close(15);
    return cbm_save(name, dev, addr, size) == 0;
}
