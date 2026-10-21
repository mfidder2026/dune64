/* disk.c - laden en opslaan. Met een 1541 (of een exacte emulatie: VICE true drive, Ultimate)
   gaat laden via de eigen fastloader (src/fastload.s + src/drive/drive.s); antwoordt de drive
   niet (SD2IEC, VICE virtual device), dan blijft alles via de Kernal lopen. Zie DESIGN.md §11. */
#include <cbm.h>
#include <string.h>
#include "gfx.h"
#include "disk.h"
#include "sound.h"

#define DRIVE_ADDR 0x0500
#define MW_CHUNK   32
#define PING_REPLY 0xA5

unsigned char __fastcall__ fl_command(unsigned char cmd);           /* fastload.s */
unsigned int  __fastcall__ fl_load(const char* name, void* addr);

static unsigned char fast;          /* 1 = drivecode draait, bus is van ons */
static unsigned char have_code;     /* drivecode staat onder de I/O */

static unsigned char drive(void)
{
    unsigned char d = *(unsigned char*)0xBA;   /* laatst gebruikte drive */
    return (d >= 8 && d <= 11) ? d : 8;
}

/* kopiëren van/naar de RAM onder de I/O ($D000-$DFFF) */
void io_copy(void* dst, const void* src, unsigned int n)
{
    unsigned char old = *(unsigned char*)0x01;
    __asm__("sei");
    *(unsigned char*)0x01 = 0x34;
    memcpy(dst, src, n);
    *(unsigned char*)0x01 = old;
    __asm__("cli");
}

/* ~20 ms per stap, zonder de raster-IRQ (zo werkt ook tests/fltest.c) */
static void wait_frames(unsigned char n)
{
    unsigned int i;
    while (n--) for (i = 0; i < 1000; ++i) __asm__("nop");
}

unsigned char disk_fast_install(void)
{
    static unsigned char cmd[6 + MW_CHUNK];
    unsigned int len, pos = 0, addr = DRIVE_ADDR;
    unsigned char n, dev = drive();

    if (fast) return 1;
    if (!have_code) return 0;
    io_copy(LOADBUF, IOBUF_DRIVE, 2);                       /* lengte van de drivecode */
    len = LOADBUF[0] | (LOADBUF[1] << 8);
    io_copy(LOADBUF, IOBUF_DRIVE + 2, len);
    if (cbm_open(15, dev, 15, "")) return 0;
    cmd[0] = 'm'; cmd[1] = '-'; cmd[2] = 'w';               /* cc65: 'm' -> PETSCII "M" */
    while (pos < len) {
        n = (len - pos > MW_CHUNK) ? MW_CHUNK : (unsigned char)(len - pos);
        cmd[3] = (unsigned char)addr; cmd[4] = (unsigned char)(addr >> 8); cmd[5] = n;
        memcpy(cmd + 6, LOADBUF + pos, n);
        cbm_write(15, cmd, 6 + n);
        pos += n; addr += n;
    }
    cmd[2] = 'e'; cmd[3] = (unsigned char)DRIVE_ADDR; cmd[4] = (unsigned char)(DRIVE_ADDR >> 8);
    cbm_write(15, cmd, 5);                                  /* M-E: de drive start onze code */
    wait_frames(3);
    if (fl_command(3) == PING_REPLY) {
        fast = 1;                   /* kanaal 15 blijft open tot fl_command(2) */
        return 1;
    }
    cbm_close(15);
    have_code = 0;                  /* geen 1541: niet opnieuw proberen */
    return 0;
}

static void fast_quit(void)
{
    if (!fast) return;
    fl_command(2);                  /* drive terug naar DOS */
    wait_frames(3);
    cbm_close(15);
    fast = 0;
}

unsigned char disk_fast_active(void) { return fast; }

/* De bootloader (src/boot/boot.s) laat "FL" op $02FC achter als hij het spel via de fastloader
   heeft geladen: de drivecode draait dan al en kanaal 15 is open. */
#define BOOT_MAGIC ((unsigned char*)0x02FC)

void disk_init(void)
{
    if (BOOT_MAGIC[0] == 0x46 && BOOT_MAGIC[1] == 0x4C) fast = 1;
    BOOT_MAGIC[0] = 0;
}

void disk_set_drive_code(void) { have_code = 1; }

unsigned int disk_load(const char* name, void* addr)
{
    unsigned int n;
    sound_hold(1);
    n = fast ? fl_load(name, addr) : cbm_load(name, drive(), addr);
    sound_hold(0);
    return n;
}

unsigned char disk_save(const char* name, const void* addr, unsigned int size)
{
    static char scratch[24] = "s0:";
    unsigned char dev = drive(), ok, was_fast = fast;
    fast_quit();
    strcpy(scratch + 3, name);
    if (cbm_open(15, dev, 15, scratch) == 0) cbm_close(15);
    ok = cbm_save(name, dev, addr, size) == 0;
    if (was_fast) disk_fast_install();
    return ok;
}
