; irq.s - raster-split: bovenste 17 tekenrijen multicolor bitmap, onderste 8 rijen
;         multicolor tekstmodus (UI-paneel). Zie DESIGN.md §6.
;
; Twee raster-IRQ's per frame:
;   SPLIT_LINE  (186): bitmap -> tekst  (laatste pixelrij van tekenrij 16 is zwart)
;   BOTTOM_LINE (252): tekst -> bitmap  (in de onderrand, onzichtbaar)
; CIA1-timer-IRQ staat uit; het toetsenbord wordt 1x per frame gescand via $EA31.

        .export _irq_install, _frame_count, _split_enabled, _screen_on, _nmi_stub

SPLIT_LINE  = 186
BOTTOM_LINE = 252

        .segment "DATA"
_frame_count:   .byte 0
_split_enabled: .byte 1
_screen_on:     .byte $10           ; $10 = beeld aan (DEN), $00 = uit (tijdens laden)
state:          .byte 0

        .segment "CODE"

_nmi_stub:
        rti

_irq_install:
        sei
        lda #$7f
        sta $dc0d           ; CIA1-interrupts uit
        lda $dc0d
        lda #<irq
        sta $0314
        lda #>irq
        sta $0315
        lda #BOTTOM_LINE
        sta $d012
        lda $d011
        and #$7f            ; raster bit 8 = 0
        sta $d011
        lda #$01
        sta $d01a           ; raster-IRQ aan
        sta $d019
        lda #0
        sta state
        cli
        rts

irq:
        lda $d019
        sta $d019           ; bevestig VIC-IRQ
        lda state
        bne @bottom
        ; ---- bitmap -> tekst
        lda _split_enabled
        beq @nosplit
        lda _screen_on
        ora #$0b            ; ECM=0 BMM=0 RSEL=1 YSCROLL=3
        sta $d011
        lda #$02            ; scherm $C000, charset $C800
        sta $d018
@nosplit:
        lda #BOTTOM_LINE
        sta $d012
        lda #1
        sta state
        jmp $ea81           ; registers terug, RTI
@bottom:
        ; ---- tekst -> bitmap (voor het volgende frame)
        lda _screen_on
        ora #$2b            ; BMM=1
        sta $d011
        lda #$08            ; scherm $C000, bitmap $E000
        sta $d018
        inc _frame_count
        lda #SPLIT_LINE
        sta $d012
        lda #0
        sta state
        jmp $ea31           ; Kernal: jiffy-klok + toetsenbord, daarna RTI
