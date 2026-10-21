; fastload.s - fastloader, C64-kant (DESIGN.md §11.2, fase 5). Protocol: zie src/drive/drive.s.
; De C64 is de klok (ATN), dus geen SEI nodig en geen last van badlines of de raster-IRQ.
; $DD00: bit 0-1 VIC-bank (blijven zoals ze zijn: bankbits), bit 3 ATN uit, bit 4 CLK uit, bit 5 DATA uit
; (1 = lijn laag), bit 6 CLK in, bit 7 DATA in (1 = lijn hoog).

        .export _fl_command, _fl_load
        .import popax
        .importzp ptr1, ptr2, tmp1, tmp2, tmp3, tmp4

ATNO  = $08
CLKO  = $10
DATAO = $20

        .segment "BSS"
atnstate:   .res 1
bankbits:   .res 1                  ; bit 0-1 van $DD00 (VIC-bank), bij elke schrijfactie erbij
va:         .res 1                  ; $DD00 met ATN laag
vr:         .res 1                  ; $DD00 met ATN los
count:      .res 1
hdr:        .res 1                  ; nog over te slaan bytes laadadres
fromfile:   .res 1                  ; 1 = laadadres uit het bestand halen
len:        .res 2

        .segment "CODE"

delay:  ldx #12                     ; ~75 cycli incl. jsr/rts (drive heeft er ~45 nodig)
:       dex
        bne :-
        rts

toggle: lda atnstate                ; ATN wisselen, CLK/DATA los
        eor #ATNO
        sta atnstate
        ora bankbits
        sta $DD00
        rts

getbank:                            ; begin van elk commando
        lda $DD00
        and #$03
        sta bankbits
        sta vr                      ; ATN los
        ora #ATNO
        sta va                      ; ATN laag
        rts

; byte in A sturen: 4 paren, laagste eerst; lijnen en ATN-wisseling in één schrijfactie
sendbyte:
        sta tmp1
        ldy #4
@p:     lda #0
        lsr tmp1
        bcc :+
        ora #DATAO
:       lsr tmp1
        bcc :+
        ora #CLKO
:       sta tmp2
        lda atnstate
        eor #ATNO
        sta atnstate
        ora tmp2
        ora bankbits
        sta $DD00
        jsr delay
        dey
        bne @p
        rts

; byte ontvangen, snel: ATN aan/uit/aan/uit met vooraf berekende waarden (va/vr), tussen
; schrijven en lezen ~28 cycli (de drive antwoordt binnen ~13). Lijnen: 1 = hoog, dus aan het
; eind omkeren.
recvbyte:
        lda va
        sta $DD00
        jsr d28
        lda $DD00
        asl a
        ror tmp1
        asl a
        ror tmp1
        lda vr
        sta $DD00
        jsr d28
        lda $DD00
        asl a
        ror tmp1
        asl a
        ror tmp1
        lda va
        sta $DD00
        jsr d28
        lda $DD00
        asl a
        ror tmp1
        asl a
        ror tmp1
        lda vr
        sta $DD00
        jsr d28
        lda $DD00
        asl a
        ror tmp1
        asl a
        ror tmp1
        lda tmp1
        eor #$FF
        rts

d28:    nop                         ; jsr + 6 nops + rts: lezen 28 cycli na het schrijven
        nop
        nop
        nop
        nop
        nop
        rts

ack:    jsr toggle
        jsr delay
        jsr toggle
        jmp delay

; wacht tot de drive klaar is (CLK los). C = 1 na ~4,5 s zonder antwoord.
waitready:
        lda atnstate                ; eigen CLK/DATA los (de laatste bits van een commando
        ora bankbits                ; kunnen CLK nog laag houden), ATN blijft zoals hij is
        sta $DD00
        jsr toggle_free             ; eerst de drive tijd geven om "bezig" te melden
        lda #0
        sta tmp3
        sta tmp4
        lda #5                      ; ~4,5 s
        sta tmp2
@poll:  bit $DD00
        bvs @ok                     ; bit 6: CLK in hoog = klaar
        dec tmp3
        bne @poll
        dec tmp4
        bne @poll
        dec tmp2
        bne @poll
        sec
        rts
@ok:    jsr delay                   ; de drive berekent nog het eerste paar
        clc
        rts

toggle_free:                        ; ~300 cycli wachten zonder de bus te raken
        jsr delay
        jsr delay
        jsr delay
        jmp delay

; ------------------------------------------------------------------ C-interface
; unsigned char __fastcall__ fl_command(unsigned char cmd)
;   2 = stoppen (geen antwoord, geeft 0), 3 = ping (geeft $A5 als de drive antwoordt, anders 0)
_fl_command:
        pha
        jsr getbank
        pla
        pha
        jsr sendbyte
        pla
        cmp #3
        bne @none
        jsr waitready
        bcs @none
        jsr recvbyte                ; aantal (1)
        jsr recvbyte                ; $A5
        pha
        jsr ack                     ; bevestiging: de drive gaat terug naar de commandolus
        pla
        ldx #0
        rts
@none:  lda #0
        tax
        rts

; ------------------------------------------------------------------ blok ontvangen (snel)
; count bytes naar (ptr1),Y. Per paar: ATN wisselen, en in de wachttijd het vorige paar
; verwerken; tussen schrijven en lezen zitten >= 20 cycli (de drive antwoordt binnen 13).
; Een badline of IRQ maakt de wachttijd alleen langer. ptr2 = va/vr (zero page, snel).
recvblock:
        ldy #0
@b:     nop                         ; ruimte voor de drive tussen twee bytes
        nop
        nop
        nop
        lda ptr2                    ; paar 0: ATN laag
        sta $DD00
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        lda $DD00
        sta tmp2
        lda ptr2+1                  ; paar 1: ATN los
        sta $DD00
        lda tmp2
        asl a
        ror tmp1
        asl a
        ror tmp1
        lda $DD00
        sta tmp2
        lda ptr2                    ; paar 2
        sta $DD00
        lda tmp2
        asl a
        ror tmp1
        asl a
        ror tmp1
        lda $DD00
        sta tmp2
        lda ptr2+1                  ; paar 3
        sta $DD00
        lda tmp2
        asl a
        ror tmp1
        asl a
        ror tmp1
        lda $DD00
        asl a
        ror tmp1
        asl a
        ror tmp1
        lda tmp1
        eor #$FF                    ; lijn hoog = 0
        sta (ptr1),y
        iny
        cpy count
        bne @b
        rts

; A/X += count-bytes naar ptr1 en len (na een blok)
advance:
        clc
        adc ptr1
        sta ptr1
        bcc :+
        inc ptr1+1
:       rts

; unsigned int __fastcall__ fl_load(const char* name, void* addr)
;   addr == 0: naar het laadadres uit het bestand. Geeft het aantal geladen bytes, 0 = fout.
;   Het eerste blok begint met het laadadres: dat blok komt eerst op dest (of, bij addr == 0,
;   in LOADBUF) en wordt daarna 2 bytes opgeschoven naar zijn plek.
FIRSTBUF = $9700                    ; LOADBUF (src/gfx.h): kladruimte voor het eerste blok

_fl_load:
        sta ptr1
        stx ptr1+1
        ora ptr1+1
        bne :+
        lda #1
        .byte $2C                   ; bit abs: sla de volgende lda over
:       lda #0
        sta fromfile
        beq :+
        lda #<FIRSTBUF
        sta ptr1
        lda #>FIRSTBUF
        sta ptr1+1
:       jsr popax
        sta ptr2
        stx ptr2+1
        jsr getbank
        lda #1
        jsr sendbyte                ; commando laden
        lda #0
        sta tmp3                    ; index in de naam
        sta tmp4                    ; teller 16 tekens
        sta len
        sta len+1
        lda #1
        sta hdr                     ; 1 = het eerste blok komt nog
@name:  ldy tmp3
        lda (ptr2),y
        beq @pad
        inc tmp3
        jmp @send
@pad:   lda #$A0
@send:  jsr sendbyte
        inc tmp4
        lda tmp4
        cmp #16
        bne @name
        lda va                      ; vanaf hier: ptr2 = va/vr voor recvblock
        sta ptr2
        lda vr
        sta ptr2+1
@blocks:
        jsr waitready
        bcc :+
        jmp @err
:       jsr recvbyte
        sta count
        bne :+
        jmp @eof
:       jsr delay                   ; de drive pakt de eerste databyte
        jsr recvblock
        jsr ack
        lda hdr
        bne @first
        lda count                   ; volgend blok: gewoon verder
        jsr addlen
        lda count
        jsr advance
        jmp @blocks
@first: lda #0
        sta hdr
        lda count                   ; 2 bytes laadadres eraf
        sec
        sbc #2
        sta count
        jsr addlen
        ldy #0
        lda fromfile
        beq @shift
        lda (ptr1),y                ; laadadres uit het bestand
        sta tmp3
        iny
        lda (ptr1),y
        sta tmp4
        lda ptr1                    ; bron = FIRSTBUF + 2
        clc
        adc #2
        sta ptr2
        lda ptr1+1
        adc #0
        sta ptr2+1
        lda tmp3
        sta ptr1
        lda tmp4
        sta ptr1+1
        jmp @copy
@shift: lda ptr1                    ; bron = dest + 2, doel = dest
        clc
        adc #2
        sta ptr2
        lda ptr1+1
        adc #0
        sta ptr2+1
@copy:  ldy #0
        lda count
        beq @copied
@cp:    lda (ptr2),y
        sta (ptr1),y
        iny
        cpy count
        bne @cp
@copied:
        lda count
        jsr advance
        lda va                      ; ptr2 weer va/vr
        sta ptr2
        lda vr
        sta ptr2+1
        jmp @blocks
@eof:   jsr ack
        lda len
        ldx len+1
        rts
@err:   lda #0
        tax
        rts

addlen: clc
        adc len
        sta len
        bcc :+
        inc len+1
:       rts
