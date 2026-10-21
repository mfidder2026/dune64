; music.s - kleine SID-player met geluidseffecten (DESIGN.md §6). music_play draait 1x per frame
; vanuit de raster-IRQ (onderrand, irq.s). De muziekdata (pipeline/music.py) ligt in de RAM onder
; de I/O, zodat ze geen programmageheugen kost: lezen met $01=$34, de SID schrijven met $01=$35.
;
; Data op MUSIC_BASE:
;   +0        tempo (frames per tick)
;   +1..+6    startadres stem 1..3 (LE, absoluut)
;   +7..+46   8 instrumenten x 5: AD, SR, golfvorm (zonder gate), pulsbreedte lo, hi
;   +47..+142 frequentie lo voor noot 0..95; +143..+238 frequentie hi
;   stemmen:  $00-$5F noot + duur (ticks) | $60 rust + duur | $70+i instrument i |
;             $FF terug naar het begin van de stem
;
; Geluid stil (sound_hold): tijdens laden en uitpakken staat de IRQ soms seconden uit (SEI); dan
; zou de SID op de laatste toon blijven hangen. sound_hold(1) zet alle stemmen uit en het volume
; op 0, sound_hold(0) zet het terug; de teller maakt nesten mogelijk.
; Effecten (sfx) spelen op stem 3; de melodie loopt in de tijd door en krijgt daarna haar
; instrument terug.

        .export _music_init, _music_on, _music_set, _sfx_on, _sfx, _sound_hold, music_play

MUSIC_BASE = $D200
VSTART     = MUSIC_BASE + 1
INSTR      = MUSIC_BASE + 7
FREQLO     = MUSIC_BASE + 47
FREQHI     = MUSIC_BASE + 143
SID        = $D400
V3         = SID + 14               ; stem 3 (effecten)
ZPTR       = $FB                    ; $FB/$FC: vrij voor eigen asm (DESIGN.md §7)

        .segment "DATA"
_music_on:  .byte 0                 ; 0 = stil; de engine zet hem aan na music_init
_sfx_on:    .byte 1                 ; geluidseffecten aan

        .segment "BSS"
vptr_lo:    .res 3
vptr_hi:    .res 3
vdur:       .res 3
vwave:      .res 3
vinstr:     .res 3                  ; laatste instrument per stem (terugzetten na een effect)
tick:       .res 1
old01:      .res 1
cur_v:      .res 1
tmp_y:      .res 1
ins_b:      .res 5
hold:       .res 1                  ; > 0: alles stil
sfx_t:      .res 1                  ; frames over van het lopende effect (0 = geen)
sfx_f:      .res 1                  ; frequentie (hoog byte)
sfx_s:      .res 1                  ; glijden per frame (signed)
sfx_w:      .res 1                  ; golfvorm

        .segment "RODATA"
voff:       .byte 0, 7, 14          ; SID-registeroffset per stem
; effecten: golfvorm, AD, SR, frequentie (hoog), glijden, frames
;   0 tik (menu), 1 keuze, 2 opstijgen (ruis), 3 alarm (overval, nederlaag)
sfx_tab:    .byte $10, $00, $00, $30,   0,  2
            .byte $40, $00, $00, $18,   6,  6
            .byte $80, $0A, $00, $06,   1, 45
            .byte $20, $00, $F0, $28, $FD, 30

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

; C = 1 als stem cur_v nu van een effect is (dan de SID niet aanraken)
vbusy:  lda cur_v
        cmp #2
        bne @no
        lda sfx_t
        beq @no
        sec
        rts
@no:    clc
        rts

; ------------------------------------------------------------------ vanuit C
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

; void __fastcall__ music_set(unsigned char on): muziek aan (opnieuw vanaf het begin) of uit
_music_set:
        sta _music_on
        cmp #0
        bne _music_init
        ldx #0                      ; uit: gates van de muziekstemmen dicht
@g:     ldy voff,x
        lda vwave,x
        sta SID + 4,y
        inx
        cpx #3
        bne @g
        rts

; void __fastcall__ sound_hold(unsigned char on)
_sound_hold:
        cmp #0
        beq @release
        inc hold
        lda hold
        cmp #1
        bne @done
        lda #0                      ; eerste hold: alles stil
        sta sfx_t
        sta SID + 4
        sta SID + 11
        sta SID + 18
        sta SID + $18
@done:  rts
@release:
        lda hold
        beq @done
        dec hold
        bne @done
        lda #$0F
        sta SID + $18
        rts

; void __fastcall__ sfx(unsigned char id)
_sfx:
        ldx _sfx_on
        beq @done
        ldx hold
        bne @done
        sta tmp_y                   ; x6
        asl a
        adc tmp_y
        asl a
        tax
        sei
        lda #0
        sta V3 + 4                  ; gate uit
        lda sfx_tab,x
        sta sfx_w
        lda sfx_tab + 1,x
        sta V3 + 5
        lda sfx_tab + 2,x
        sta V3 + 6
        lda sfx_tab + 3,x
        sta sfx_f
        sta V3 + 1
        lda #0
        sta V3
        sta V3 + 2
        lda #$08
        sta V3 + 3                  ; pulsbreedte 50 %
        lda sfx_tab + 4,x
        sta sfx_s
        lda sfx_tab + 5,x
        sta sfx_t
        lda #$0F
        sta SID + $18
        lda sfx_w
        ora #$01
        sta V3 + 4
        cli
@done:  rts

; ------------------------------------------------------------------ per frame (in de IRQ)
music_play:
        lda hold
        beq :+
        rts
:       lda $01
        sta old01
        lda sfx_t                   ; lopend effect: glijden, en aan het eind melodie terug
        beq @music
        dec sfx_t
        bne @slide
        lda sfx_w
        sta V3 + 4                  ; gate uit
        lda #2
        sta cur_v
        lda vinstr + 2
        jsr instrument
        jmp @music
@slide: lda sfx_f
        clc
        adc sfx_s
        sta sfx_f
        sta V3 + 1
@music: lda _music_on
        beq @out
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
        jsr vbusy
        bcs @nextv
        ldx cur_v
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
@rest:  sty tmp_y
        jsr vbusy
        bcs :+
        ldx cur_v
        ldy voff,x
        lda vwave,x
        sta SID + 4,y               ; gate los
:       ldy tmp_y
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
        jsr vbusy
        bcs @skip
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
@skip:  rts

; instrument A (0-7) op stem cur_v: ADSR, pulsbreedte, golfvorm
instrument:
        ldx cur_v
        sta vinstr,x
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
        lda ins_b + 2
        sta vwave,x
        jsr vbusy
        bcs @skip
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
@skip:  rts
