; boot.s - bootloader (DESIGN.md §11.2c). Het eerste bestand op de diskette ("ashkara"), klein
; genoeg om snel via de Kernal te laden. Kopieert zich naar $C000, zet de fastloader in de
; 1541 (dezelfde drive.s/fastload.s als het spel), laadt het hoofdprogramma "main" snel en
; start het via zijn BASIC-SYS-regel. Antwoordt de drive niet, dan laadt hij "main" via de
; Kernal. Een marker op $02FC ("FL") vertelt het spel dat de drivecode al draait.

        .export popax
        .exportzp ptr1, ptr2, tmp1, tmp2, tmp3, tmp4
        .import _fl_command, _fl_load
        .import __CODE_LOAD__, __CODE_RUN__, __CODE_SIZE__, __BSS_RUN__, __BSS_SIZE__

ptr1  = $FB                         ; zero page voor fastload.s (geen cc65-runtime hier)
ptr2  = $FD
tmp1  = $F7
tmp2  = $F8
tmp3  = $F9
tmp4  = $FA

SETLFS = $FFBA
SETNAM = $FFBD
OPEN   = $FFC0
CLOSE  = $FFC3
CHKOUT = $FFC9
CLRCHN = $FFCC
CHROUT = $FFD2
LOAD   = $FFD5

DRIVE_ADDR = $0500
MW_CHUNK   = 32
MAGIC      = $02FC                  ; "F", "L": fastloader draait al (src/disk.c)

; ------------------------------------------------------------------ laadadres + BASIC-regel
        .segment "LOADADDR"
        .word $0801

        .segment "EXEHDR"
        .word @next                 ; 10 SYS2061
        .word 10
        .byte $9E, "2061", 0
@next:  .word 0

; ------------------------------------------------------------------ $080D: naar $C000
        .segment "STARTUP"
        lda #<__CODE_LOAD__
        sta ptr1
        lda #>__CODE_LOAD__
        sta ptr1+1
        lda #<__CODE_RUN__
        sta ptr2
        lda #>__CODE_RUN__
        sta ptr2+1
        ldx #>(__CODE_SIZE__ + 255)
        ldy #0
@cp:    lda (ptr1),y
        sta (ptr2),y
        iny
        bne @cp
        inc ptr1+1
        inc ptr2+1
        dex
        bne @cp
        jmp start

; ------------------------------------------------------------------ resident op $C000
        .segment "CODE"

start:
        lda #<__BSS_RUN__           ; BSS leeg (o.a. atnstate van fastload.s: ATN begint los)
        sta ptr1
        lda #>__BSS_RUN__
        sta ptr1+1
        ldx #>(__BSS_SIZE__ + 255)
        lda #0
        tay
@clr:   sta (ptr1),y
        iny
        bne @clr
        inc ptr1+1
        dex
        bne @clr
        sta MAGIC
        lda $BA                     ; laatst gebruikte drive (8..11)
        cmp #8
        bcc :+
        cmp #12
        bcc :++
:       lda #8
:       sta dev
        jsr print_loading

        ; drivecode naar $0500 via M-W in stukken van 32 bytes
        lda #15
        ldx dev
        ldy #15
        jsr SETLFS
        lda #0
        jsr SETNAM
        jsr OPEN
        lda #<drive_code            ; bron in ptr1 (zero page, voor (ptr1),y)
        sta ptr1
        lda #>drive_code
        sta ptr1+1
        lda #<DRIVE_ADDR
        sta dst
        lda #>DRIVE_ADDR
        sta dst+1
        lda #<(drive_end - drive_code)
        sta left
        lda #>(drive_end - drive_code)
        sta left+1
@chunk: lda left
        ora left+1
        bne :+
        jmp @exec
:
        lda left+1                  ; n = min(32, left)
        bne @full
        lda left
        cmp #MW_CHUNK
        bcc @part
@full:  lda #MW_CHUNK
@part:  sta n
        ldx #15
        jsr CHKOUT
        lda #$4D                    ; "M-W"
        jsr CHROUT
        lda #$2D
        jsr CHROUT
        lda #$57
        jsr CHROUT
        lda dst
        jsr CHROUT
        lda dst+1
        jsr CHROUT
        lda n
        jsr CHROUT
        lda #0
        sta i
@byte:  ldy i
        lda (ptr1),y
        jsr CHROUT
        inc i
        lda i
        cmp n
        bne @byte
        jsr CLRCHN
        lda ptr1                    ; bron += n, dst += n, left -= n
        clc
        adc n
        sta ptr1
        bcc :+
        inc ptr1+1
:       lda dst
        clc
        adc n
        sta dst
        bcc :+
        inc dst+1
:       lda left
        sec
        sbc n
        sta left
        bcs :+
        dec left+1
:       jmp @chunk

@exec:  ldx #15                     ; "M-E" $0500: de drive start de loader
        jsr CHKOUT
        lda #$4D
        jsr CHROUT
        lda #$2D
        jsr CHROUT
        lda #$45
        jsr CHROUT
        lda #<DRIVE_ADDR
        jsr CHROUT
        lda #>DRIVE_ADDR
        jsr CHROUT
        jsr CLRCHN
        jsr wait                    ; de drive even laten opstarten

        lda #3                      ; ping
        jsr _fl_command
        cmp #$A5
        bne kernal
        lda #$50                    ; "P": de drive antwoordt
        jsr CHROUT

        lda #0                      ; snel laden naar het laadadres uit het bestand
        tax
        jsr _fl_load
        stx tmp1
        ora tmp1
        beq kernal_quit             ; mislukt: drive terug naar DOS, dan via de Kernal
        lda #$46                    ; "F" op het scherm
        jsr CHROUT
        lda #$46                    ; "FL": kanaal 15 blijft open, de drivecode draait
        sta MAGIC
        lda #$4C
        sta MAGIC+1
        jmp run_main

kernal_quit:
        lda #2
        jsr _fl_command
        jsr wait
kernal: lda #$4B                    ; "K": via de Kernal
        jsr CHROUT
        lda #15
        jsr CLOSE
        lda #1
        ldx dev
        ldy #1                      ; naar het laadadres uit het bestand
        jsr SETLFS
        lda #main_name_end - main_name
        ldx #<main_name
        ldy #>main_name
        jsr SETNAM
        lda #0
        jsr LOAD
        bcc run_main
        inc $D020                   ; laadfout: rand knippert
        jmp *-3

; startadres uit de BASIC-regel op $0801: link (2), regelnummer (2), $9E, cijfers
run_main:
        lda #0
        sta target
        sta target+1
        ldy #4
        lda $0801,y
        cmp #$9E
        bne @go
@skip:  iny
        lda $0801,y
        cmp #$20
        beq @skip
@dig:   sec
        sbc #$30
        cmp #10
        bcs @go
        pha                         ; target = target * 10 + cijfer
        lda target
        ldx target+1
        asl target
        rol target+1
        asl target
        rol target+1
        clc
        adc target
        sta target
        txa
        adc target+1
        sta target+1
        asl target
        rol target+1
        pla
        clc
        adc target
        sta target
        bcc :+
        inc target+1
:       iny
        lda $0801,y
        jmp @dig
@go:    lda target+1
        bne :+
        lda #<$080D                 ; geen SYS gevonden: cc65-standaard
        sta target
        lda #>$080D
        sta target+1
:       jmp (target)

wait:   ldx #0                      ; ~250 ms: DOS moet de M-E eerst afhandelen
        ldy #200
:       dex
        bne :-
        dey
        bne :-
        rts

; voor fl_load: de naam komt via popax (cc65-aanroepconventie)
popax:  lda #<main_name
        ldx #>main_name
        rts

print_loading:
        ldx #0
:       lda loading_text,x
        beq :+
        jsr CHROUT
        inx
        bne :-
:       rts

loading_text:
        .byte $0D, "ashkara ...", $0D, 0   ; kleine letters: cc65 maakt er PETSCII-hoofdletters van
main_name:
        .byte $4D, $41, $49, $4E    ; "MAIN" (PETSCII, zoals in de directory)
main_name_end:
        .byte 0

drive_code:
        .incbin "drive.bin"
drive_end:

        .segment "BSS"
dev:    .res 1
dst:    .res 2
left:   .res 2
n:      .res 1
i:      .res 1
target: .res 2
