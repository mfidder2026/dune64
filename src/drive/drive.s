; drive.s - fastloader, 1541-kant (DESIGN.md §11.2, fase 5). Draait op $0500 in de drive; de
; C64 zet het erin met M-W en start het met M-E (src/fastload.s). Tot het commando "stoppen"
; blijft de drive in deze lus en luistert hij niet naar de normale seriële bus.
;
; Protocol: de C64 is de klok. Elke wisseling van ATN = één paar van 2 bits, het laagste paar
; eerst. Bit 0 op DATA, bit 1 op CLK; een 1 = lijn laag. Na elke wisseling wacht de C64 vast
; >= 50 cycli voor hij leest of de lijnen weer verandert; de drive reageert binnen ~36 cycli.
; Vertraging aan de C64-kant (badline, IRQ) maakt het dus alleen trager, nooit fout.
; Bezig = de drive houdt CLK laag (sector lezen, directory zoeken); klaar = CLK los.
;
; Snel verzenden (drive -> C64): binnen een byte gaat ATN altijd aan, uit, aan, uit (tussen
; transacties is ATN los). De drive wacht dus met een lus van 7 cycli op precies die flank en
; schrijft meteen de vooraf berekende waarde (tabellen per nibble): antwoord binnen ~13 cycli.
;
; Commando's (1 byte, dan argumenten): 1 = laden + 16 tekens naam ($A0 = opvulling),
;   2 = stoppen (terug naar DOS), 3 = ping (antwoord: blok met 1 byte $A5).
; Laden: per sector een blok "aantal, aantal x data" (aantal 1..254), einde = blok met aantal 0
;   (ook bij niet gevonden of leesfout). Na elk blok bevestigt de C64 met 2 ATN-wisselingen,
;   zodat ATN tussen transacties altijd los is.

VIA1PB   = $1800              ; bit0 DATA IN, bit1 DATA OUT, bit2 CLK IN, bit3 CLK OUT,
                              ; bit4 ATNA, bit7 ATN IN (ingangen: 1 = lijn laag)
VIA1IER  = $180E
JOB0     = $00                ; jobcode buffer 0
TRACK0   = $06
SECTOR0  = $07
BUF0     = $0300

        .segment "CODE"

start:
        sei
        lda VIA1IER
        sta saveier
        lda #$7F
        sta VIA1IER           ; geen VIA1-interrupts (ATN!) zolang wij de bus hebben
        lda #0
        sta atn
        sta atnbit
        sta VIA1PB            ; alles los

cmdloop:
        jsr getbyte
        cmp #1
        beq load
        cmp #3
        beq ping
        lda saveier           ; stoppen: alles terug zoals DOS het had
        ora #$80
        sta VIA1IER
        lda #0
        sta VIA1PB
        cli
        rts

ping:
        jsr busy
        lda #1
        sta count
        lda #$A5
        sta BUF0 + 2
        jsr sendblock_noack
        jmp idle

load:
        ldx #0
@name:  jsr getbyte
        sta name,x
        inx
        cpx #16
        bne @name
        jsr busy
        lda #18               ; directory: 18/1 en verder
        ldx #1
@dirsec:
        jsr readsec
        bcs eof
        ldx #0
@entry: lda BUF0 + 2,x        ; bestandstype; 0 = leeg
        beq @skip
        stx entry
        ldy #0
@cmp:   lda BUF0 + 5,x
        cmp name,y
        bne @nope
        inx
        iny
        cpy #16
        bne @cmp
        ldx entry             ; gevonden
        lda BUF0 + 3,x
        pha
        lda BUF0 + 4,x
        tax
        pla
        jmp file
@nope:  ldx entry
@skip:  txa
        clc
        adc #32
        tax
        bne @entry
        lda BUF0              ; volgende directorysector
        beq eof
        ldx BUF0 + 1
        jmp @dirsec

file:   jsr readsec           ; A = spoor, X = sector
        bcs eof
        lda BUF0
        beq @last
        lda #254
        sta count
        jsr sendblock
        lda BUF0
        ldx BUF0 + 1
        jmp file
@last:  ldx BUF0 + 1          ; laatste sector: data t/m index BUF0+1
        dex
        stx count
        txa
        beq eof
        jsr sendblock
eof:    lda #0
        sta count
        jsr sendblock_noack   ; blok met aantal 0
idle:   jsr ack
        jsr release
        jmp cmdloop

; ------------------------------------------------------------------ blok sturen
; count bytes vanaf BUF0+2; daarna ack van de C64 en weer bezig
sendblock:
        jsr sendblock_noack
        jsr ack
        jmp busy

sendblock_noack:
        jsr release           ; klaar: CLK los
        lda count
        jsr putbyte
        lda count
        beq @done
        ldx #0
@b:     lda BUF0 + 2,x
        jsr putbyte
        inx
        cpx count
        bne @b
@done:  lda #0                ; ATN is na elke byte weer los
        sta atn
        sta atnbit
        rts

ack:    jsr waitatn           ; twee wisselingen: ATN is daarna weer los
        sta VIA1PB
        jsr waitatn
        sta VIA1PB
        rts

; ------------------------------------------------------------------ bus
; wacht op een ATN-wisseling; A = ATNA-bit voor de nieuwe toestand (lijnen los)
waitatn:
        lda VIA1PB
        and #$80
        cmp atn
        beq waitatn
        sta atn
        lsr a
        lsr a
        lsr a
        sta atnbit            ; $10 als ATN laag is: dan geen automatische DATA-ack
        rts

busy:   lda atnbit
        ora #$08              ; CLK laag
        sta VIA1PB
        rts

release:
        lda atnbit
        sta VIA1PB
        rts

; byte in A, 4 paren, laagste eerst; X blijft bewaard. ATN: aan, uit, aan, uit.
putbyte:
        sta shift
        and #$0F
        tay
        lda tlo,y             ; paar 0 (bits 0-1), ATN wordt laag: ATNA = 1
        tay
@w0:    bit VIA1PB
        bpl @w0
        sty VIA1PB
        lda shift
        and #$0F
        tay
        lda thi,y             ; paar 1 (bits 2-3), ATN los
        tay
@w1:    bit VIA1PB
        bmi @w1
        sty VIA1PB
        lda shift
        lsr a
        lsr a
        lsr a
        lsr a
        tay
        lda tlo,y             ; paar 2 (bits 4-5)
        tay
@w2:    bit VIA1PB
        bpl @w2
        sty VIA1PB
        lda shift
        lsr a
        lsr a
        lsr a
        lsr a
        tay
        lda thi,y             ; paar 3 (bits 6-7)
        tay
@w3:    bit VIA1PB
        bmi @w3
        sty VIA1PB
        rts

; uitvoerwaarde per nibble: bit 0 -> DATA uit ($02), bit 1 -> CLK uit ($08); 1 = lijn laag
tlo:    .byte $10, $12, $18, $1A, $10, $12, $18, $1A, $10, $12, $18, $1A, $10, $12, $18, $1A
thi:    .byte $00, $00, $00, $00, $02, $02, $02, $02, $08, $08, $08, $08, $0A, $0A, $0A, $0A

; byte ontvangen in A; X blijft bewaard
getbyte:
        ldy #4
@p:     jsr waitatn
        sta VIA1PB            ; onze lijnen los, ATNA goed
        nop                   ; ~20 us: een echte kabel heeft stijgtijd nodig (VICE niet);
        nop                   ; X niet gebruiken, die is de index in de naamlus
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        lda VIA1PB
        lsr a                 ; C = DATA (1 = laag)
        ror shift
        lsr a
        lsr a                 ; C = CLK
        ror shift
        dey
        bne @p
        lda shift
        rts

; ------------------------------------------------------------------ sector lezen
; A = spoor, X = sector -> BUF0; C = 1 bij een fout. De job-lus van DOS draait in de IRQ.
readsec:
        sta TRACK0
        stx SECTOR0
        lda #$80
        sta JOB0
        cli
@w:     lda JOB0
        bmi @w
        sei
        cmp #2                ; 1 = OK
        rts

; ------------------------------------------------------------------ variabelen
saveier: .byte 0
atn:     .byte 0
atnbit:  .byte 0
shift:   .byte 0
count:   .byte 0
entry:   .byte 0
name:    .res 16
