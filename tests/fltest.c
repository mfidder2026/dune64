/* fltest.c - diagnose van de fastloader (DESIGN.md §11.2). Laadt eerst een paar bestanden via
   de Kernal als referentie, installeert dan de fastloader en laadt ze opnieuw. Toont per bestand
   lengte, checksum en laadtijd van beide manieren. Ook voor echte hardware: python build.py fltest. */
#include <cbm.h>
#include <conio.h>
#include <string.h>
#include "../src/gfx.h"
#include "../src/disk.h"

#define REF ((unsigned char*)0x4000)
#define GOT ((unsigned char*)0x5800)

/* jiffy-klok van de Kernal: 1/60 s */
#define JIFFY (*(unsigned char*)0xA2 | (*(unsigned char*)0xA1 << 8))

static const char* const files[] = { "ui.chr", "titel.scn", "h1.scr", "kaart.scn", "bestaatniet", "globe.spr" };
#define NFILES (sizeof(files) / sizeof(files[0]))

static unsigned int ref_len[NFILES], ref_sum[NFILES], ref_t[NFILES];

volatile unsigned char frame_count;                     /* gfx.h verwacht ze (irq.s) */
unsigned char split_enabled, screen_on;

static unsigned int sum(const unsigned char* p, unsigned int n)
{
    unsigned int s = 0;
    while (n--) s = (s << 1 | s >> 15) ^ *p++;
    return s;
}

static void secs(unsigned int jiffies)
{
    cprintf("%2u.%u", jiffies / 60, jiffies % 60 / 6);
}

int main(void)
{
    unsigned char i, ok = 0, good;
    unsigned int n, t, ft, kt = 0, ftot = 0;
    clrscr();
    cprintf("ASHKARA FASTLOADER-TEST\r\n\r\n");
    n = cbm_load("extra.bin", 8, LOADBUF);
    cprintf("extra.bin: %u bytes\r\n", n);
    if (n < 0x200) { cprintf("geen extra.bin\r\n"); return 1; }
    io_copy(IOBUF, LOADBUF, n);
    disk_set_drive_code();
    for (i = 0; i < NFILES; ++i) {
        t = JIFFY;
        ref_len[i] = cbm_load(files[i], 8, REF + 0);
        ref_t[i] = JIFFY - t;
        ref_sum[i] = sum(REF, ref_len[i]);
    }
    cprintf("install: %s\r\n\r\n", disk_fast_install() ? "OK (1541-code draait)" : "MISLUKT -> kernal");
    cprintf("bestand     kernal         fastloader\r\n");
    for (i = 0; i < NFILES; ++i) {
        memset(GOT, 0, 0x1000);
        t = JIFFY;
        n = disk_load(files[i], GOT);
        ft = JIFFY - t;
        good = (n == ref_len[i] && sum(GOT, n) == ref_sum[i]);
        ok += good;
        kt += ref_t[i];
        ftot += ft;
        cprintf("%-11s %4u ", files[i], ref_len[i]);
        secs(ref_t[i]);
        cprintf("s  %4u ", n);
        secs(ft);
        cprintf("s %s\r\n", good ? "ok" : "FOUT");
    }
    /* laadadres uit het bestand (addr == 0), zoals de bootloader "main" laadt: globe.spr -> $C400 */
    memset((void*)0xC400, 0, 1024);
    n = disk_load("globe.spr", 0);
    good = (n == ref_len[NFILES - 1] && sum((unsigned char*)0xC400, n) == ref_sum[NFILES - 1]);
    ok += good;
    cprintf("globe.spr naar eigen adres: %u %04x %s\r\n", n, sum((unsigned char*)0xC400, n), good ? "ok" : "FOUT");
    cprintf("\r\n%u van %u goed\r\ntotaal kernal ", ok, (unsigned char)(NFILES + 1));
    secs(kt);
    cprintf("s, fastloader ");
    secs(ftot);
    cprintf("s\r\n");
    return 0;
}
