; ============================================================================
;  Geladen 1.0 - staat een library, device of publieke poort in het geheugen?
;
;  Gebruik:  Geladen NAAM/A,DEV/S,PORT/S
;            Geladen bsdsocket.library          (library-lijst)
;            Geladen slip.device DEV            (device-lijst)
;            Geladen AMITCP PORT                (publieke poorten)
;  Returncode: 0 = aanwezig, 5 = niet aanwezig (WARN), 20 = argumentfout.
;  Geen uitvoer, geen requesters, opent niets: alleen FindName/FindPort onder
;  Forbid. (AmiTCP's ifconfig toont een requester als AmiTCP niet draait;
;  daarom deze stille controle.) Pure 68000, AmigaOS 2.04+. Alleen dos.library.
; ============================================================================

_LVOForbid        equ   -132
_LVOPermit        equ   -138
_LVOFindName      equ   -276
_LVOFindPort      equ   -390
_LVOCloseLibrary  equ   -414
_LVOOpenLibrary   equ   -552
_LVOIoErr         equ   -132
_LVOPrintFault    equ   -474
_LVOReadArgs      equ   -798
_LVOFreeArgs      equ   -858
DeviceList        equ   350
LibList           equ   378

ARG0    equ     0                       ; NAAM
ARGDEV  equ     4                       ; DEV/S
ARGPORT equ     8                       ; PORT/S
VARSIZE equ     12

start:
        movem.l d2-d7/a2-a6,-(sp)
        lea     vars(pc),a5
        clr.l   ARG0(a5)
        clr.l   ARGDEV(a5)
        clr.l   ARGPORT(a5)
        moveq   #20,d7
        moveq   #0,d6
        move.l  4.w,a6
        lea     dosname(pc),a1
        moveq   #36,d0
        jsr     _LVOOpenLibrary(a6)
        tst.l   d0
        beq.w   exit
        move.l  d0,a4                   ; a4 = DOSBase
        move.l  a4,a6
        lea     template(pc),a0
        move.l  a0,d1
        move.l  a5,d2
        moveq   #0,d3
        jsr     _LVOReadArgs(a6)
        move.l  d0,d6
        beq.w   fault

        move.l  4.w,a6
        jsr     _LVOForbid(a6)
        move.l  ARG0(a5),a1
        tst.l   ARGPORT(a5)
        bne.w   zoekpoort
        lea     LibList(a6),a0
        tst.l   ARGDEV(a5)
        beq.w   zoeknaam
        lea     DeviceList(a6),a0
zoeknaam:
        jsr     _LVOFindName(a6)
        bra.w   gevonden
zoekpoort:
        jsr     _LVOFindPort(a6)
gevonden:
        move.l  d0,d4
        jsr     _LVOPermit(a6)
        moveq   #0,d7
        tst.l   d4
        bne.w   klaar
        moveq   #5,d7
        bra.w   klaar

fault:
        jsr     _LVOIoErr(a6)
        move.l  d0,d1
        lea     progname(pc),a0
        move.l  a0,d2
        jsr     _LVOPrintFault(a6)
        moveq   #20,d7
klaar:
        move.l  a4,a6
        move.l  d6,d1
        beq.w   closedos
        jsr     _LVOFreeArgs(a6)
closedos:
        move.l  a4,a1
        move.l  4.w,a6
        jsr     _LVOCloseLibrary(a6)
exit:
        move.l  d7,d0
        movem.l (sp)+,d2-d7/a2-a6
        rts

dosname:    dc.b    "dos.library",0
template:   dc.b    "NAAM/A,DEV/S,PORT/S",0
progname:   dc.b    "Geladen",0
verstr:     dc.b    "$VER: Geladen 1.0 (08.10.2026) WodemNet",0
            even
PAD
vars:       ds.b    VARSIZE
            end
