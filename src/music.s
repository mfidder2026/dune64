; music.s - kleine SID-player (DESIGN.md §6, fase 5). music_play draait 1x per frame vanuit de
; raster-IRQ (onderrand, irq.s). De muziekdata (pipeline/music.py) ligt in de RAM onder de I/O,
; zodat ze geen programmageheugen kost: lezen met $01=$34, de SID schrijven met $01=$35.
;
; Data op MUSIC_BASE:
;   +0        tempo (frames per tick)
;   +1..+6    startadres stem 1..3 (LE, absoluut)
;   +7..+46   8 instrumenten x 5: AD, SR, golfvorm (zonder gate), pulsbreedte lo, hi
;   +47..+142 frequentie lo voor noot 0..95; +143..+238 frequentie hi
;   stemmen:  $00-$5F noot + duur (ticks) | $60 rust + duur | $70+i instrument i |
;             $FF terug naar het begin van de stem

        .export _music_init, _music_on, _music_silence, music_play

MUSIC_BASE = $D200
VSTART     = MUSIC_BASE + 1
INSTR      = MUSIC_BASE + 7
FREQLO     = MUSIC_BASE + 47
FREQHI     = MUSIC_BASE + 143
SID        = $D400
ZPTR       = $FB                    ; $FB/$FC: vrij voor eigen asm (DESIGN.md §7)

        .segment "DATA"
_music_on:  .byte 0                 ; 0 = stil; de engine zet hem aan na music_init

        .segment "BSS"
vptr_lo:    .res 3
vptr_hi:    .res 3
vdur:       .res 3
vwave:      .res 3
tick:       .res 1
old01:      .res 1
cur_v:      .res 1
tmp_y:      .res 1
ins_b:      .res 5

        .segment "RODATA"
voff:       .byte 0, 7, 14          ; SID-registeroffset per stem

        .segment "CODE"

; A = (ZPTR),Y met alle RAM zichtbaar, daarna I/O weer aan; Y++
getb:
        lda #$34
        sta $01
        lda (ZPTR),y
        ldx #$35
        stx $01
        iny
        rts

; ZPTR = startadres-tabel + 2 * stem (A = stem)
vstart_ptr:
        asl a
        clc
        adc #<VSTART
        sta ZPTR
        lda #>VSTART
        adc #0
        sta ZPTR+1
        ldy #0
        rts

; ------------------------------------------------------------------ init (vanuit C)
_music_init:
        lda $01
        sta old01
        sei
        lda #0
        sta cur_v
@v:     lda cur_v
        jsr vstart_ptr
        jsr getb
        pha
        jsr getb
        ldx cur_v
        sta vptr_hi,x
        pla
        sta vptr_lo,x
        lda #1
        sta vdur,x
        lda #0
        sta vwave,x
        inc cur_v
        lda cur_v
        cmp #3
        bne @v
        lda #0
        sta tick
        lda old01
        sta $01
        cli
        lda #$0F
        sta SID + $18               ; volume
        rts

_music_silence:
        lda #0
        ldx #$18
@c:     sta SID,x
        dex
        bpl @c
        rts

; ------------------------------------------------------------------ per frame (in de IRQ)
music_play:
        lda _music_on
        bne :+
        rts
:       lda $01
        sta old01
        dec tick
        bpl @out
        lda #<MUSIC_BASE            ; tempo
        sta ZPTR
        lda #>MUSIC_BASE
        sta ZPTR+1
        ldy #0
        jsr getb
        sta tick
        dec tick
        lda #0
        sta cur_v
@voice: ldx cur_v
        dec vdur,x
        beq @event                  ; duur op: volgende gebeurtenis
        lda vdur,x
        cmp #1
        bne @nextv
        ldy voff,x                  ; laatste tick: gate los (release)
        lda vwave,x
        sta SID + 4,y
@nextv: inc cur_v
        lda cur_v
        cmp #3
        bne @voice
@out:   lda old01
        sta $01
        rts

@event: lda vptr_lo,x
        sta ZPTR
        lda vptr_hi,x
        sta ZPTR+1
        ldy #0
@cmd:   jsr getb
        cmp #$FF
        bne @notff
        lda cur_v                   ; terug naar het begin van de stem
        jsr vstart_ptr
        jsr getb
        pha
        jsr getb
        sta ZPTR+1
        pla
        sta ZPTR
        ldy #0
        jmp @cmd
@notff: cmp #$70
        bcc @noteorrest
        and #$07
        sty tmp_y
        jsr instrument
        ldy tmp_y
        jmp @cmd
@noteorrest:
        cmp #$60
        beq @rest
        sty tmp_y
        jsr note
        ldy tmp_y
        jmp @dur
@rest:  ldx cur_v
        ldy voff,x
        lda vwave,x
        sta SID + 4,y               ; gate los
        ldy tmp_y
@dur:   jsr getb                    ; duur in ticks
        ldx cur_v
        sta vdur,x
        tya                         ; pointer += Y
        clc
        adc ZPTR
        sta vptr_lo,x
        lda ZPTR+1
        adc #0
        sta vptr_hi,x
        jmp @nextv

; noot in A -> frequentie van stem cur_v, aanslag opnieuw (gate uit, aan)
note:
        tay
        lda #$34
        sta $01
        lda FREQLO,y
        sta ins_b
        lda FREQHI,y
        sta ins_b + 1
        lda #$35
        sta $01
        ldx cur_v
        ldy voff,x
        lda vwave,x
        sta SID + 4,y
        lda ins_b
        sta SID,y
        lda ins_b + 1
        sta SID + 1,y
        lda vwave,x
        ora #$01
        sta SID + 4,y
        rts

; instrument A (0-7) op stem cur_v: ADSR, pulsbreedte, golfvorm
instrument:
        sta ins_b
        asl a
        asl a
        adc ins_b                   ; x5 (carry is 0)
        tay
        lda #$34
        sta $01
        ldx #0
@cp:    lda INSTR,y
        sta ins_b,x
        iny
        inx
        cpx #5
        bne @cp
        lda #$35
        sta $01
        ldx cur_v
        ldy voff,x
        lda ins_b
        sta SID + 5,y
        lda ins_b + 1
        sta SID + 6,y
        lda ins_b + 3
        sta SID + 2,y
        lda ins_b + 4
        sta SID + 3,y
        lda ins_b + 2
        sta vwave,x
        rts
