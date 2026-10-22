/* fltest.c - diagnose van de fastloader (DESIGN.md §11.2). Toont eerst welke drive er antwoordt
   (ROM-tekst via M-R), laadt een paar bestanden via de Kernal als referentie, installeert dan de
   fastloader (met het ping-antwoord) en laadt ze opnieuw. Per bestand: lengte, checksum, tijd.
   Bedoeld voor echte hardware: python build.py fltest. */
#include <cbm.h>
#include <conio.h>
#include <string.h>
#include "../src/gfx.h"
#include "../src/disk.h"

#define REF ((unsigned char*)0x4000)
#define GOT ((unsigned char*)0x5800)
#define SPR ((unsigned char*)0xC400)

/* jiffy-klok van de Kernal: 1/60 s */
#define JIFFY (*(unsigned char*)0xA2 | (*(unsigned char*)0xA1 << 8))

static const char* const files[] = { "ui.chr", "titel.scn", "h1.scr", "kaart.scn", "bestaatniet", "globe.spr" };
#define NFILES (sizeof(files) / sizeof(files[0]))
#define GLOBE  (NFILES - 1)

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

/* Wie is drive 8? "UI" reset de drive; de status is dan zijn opstartmelding, bijvoorbeeld
   "73,CBM DOS V2.6 1541,00,00" of "73,SD2IEC ...". */
static void drive_info(void)
{
    static char buf[41];
    int n;
    unsigned char i;
    if (cbm_open(15, 8, 15, "ui")) { cprintf("drive 8: geen antwoord\r\n"); return; }
    n = cbm_read(15, buf, 40);
    cbm_close(15);
    cprintf("drive: ");
    for (i = 0; n > 0 && i < (unsigned char)n && buf[i] != 13; ++i) cputc(buf[i]);
    cprintf("\r\n");
}

int main(void)
{
    unsigned char i, ok = 0, good;
    unsigned int n, t, ft, kt = 0, ftot = 0;
    clrscr();
    cprintf("ASHKARA FASTLOADER-TEST v2\r\n");
    drive_info();
    n = cbm_load("extra.bin", 8, LOADBUF);
    cprintf("extra.bin: %u bytes\r\n", n);
    if (n < 0x200) { cprintf("geen extra.bin\r\n"); return 1; }
    io_copy(IOBUF, LOADBUF, n);
    disk_set_drive_code();
    for (i = 0; i < NFILES; ++i) {
        t = JIFFY;
        ref_len[i] = cbm_load(files[i], 8, REF);
        ref_t[i] = JIFFY - t;
        ref_sum[i] = sum(REF, ref_len[i]);
    }
    good = disk_fast_install();
    cprintf("install: %s (ping %02x, goed = a5)\r\n", good ? "OK" : "MISLUKT -> kernal", disk_ping_reply);
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
    /* laadadres uit het bestand (addr == 0), zoals de bootloader "main" laadt. De Kernal-weg
       (cc65 cbm_load) geeft dan het eindadres terug, de fastloader de lengte: alleen de
       inhoud op $C400 telt. */
    memset(SPR, 0, 1024);
    n = disk_load("globe.spr", 0);
    good = (n != 0 && sum(SPR, ref_len[GLOBE]) == ref_sum[GLOBE]);
    ok += good;
    cprintf("globe.spr naar $c400: %s\r\n", good ? "ok" : "FOUT");
    cprintf("%u van %u goed. kernal ", ok, (unsigned char)(NFILES + 1));
    secs(kt);
    cprintf("s, fast ");
    secs(ftot);
    cprintf("s\r\n");
    return 0;
}
