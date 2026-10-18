; ============================================================================
;  VrijKB 1.0 - vrije ruimte op een volume in KB, met minimumcontrole
;
;  Gebruik:  VrijKB PAD/A,NODIG/A/N
;            VrijKB Work: 700
;  Uitvoer:  Vrij op Work: 123456 KB (nodig: 700 KB)
;  Returncode:
;     0 = genoeg ruimte en het volume is schrijfbaar (ID_VALIDATED)
;     5 = te weinig vrije ruimte (WARN)
;    10 = volume schrijfbeveiligd of nog aan het valideren (ERROR)
;    20 = pad niet gevonden / argumentfout (FAIL)
;
;  Alleen lezend: Lock + Info + UnLock. Pure 68000, AmigaOS 2.04+ (ReadArgs,
;  VPrintf, PrintFault). Alleen dos.library. Eén code-hunk, geen relocaties.
;  Assembleren: python3 asm68k.py VrijKB.s VrijKB
; ============================================================================

_LVOCloseLibrary  equ   -414
_LVOOpenLibrary   equ   -552
_LVOLock          equ   -84
_LVOUnLock        equ   -90
_LVOInfo          equ   -114
_LVOIoErr         equ   -132
_LVOPrintFault    equ   -474
_LVOReadArgs      equ   -798
_LVOFreeArgs      equ   -858
_LVOVPrintf       equ   -954
ACCESS_READ       equ   -2
ID_VALIDATED      equ   82

; ---- variabelen (a5 = vars, longword-uitgelijnd; zie build-controle) -------
ARG0    equ     0                       ; ReadArgs: PAD (STRPTR)
ARG1    equ     4                       ; ReadArgs: NODIG (LONG *)
PPATH   equ     8                       ; VPrintf-argumenten: pad,
FREEKB  equ     12                      ;   vrij KB,
NEEDKB  equ     16                      ;   nodig KB
INFO    equ     20                      ; struct InfoData, 36 bytes
VARSIZE equ     56

start:
        movem.l d2-d7/a2-a6,-(sp)
        lea     vars(pc),a5
        move.l  a5,a0
        moveq   #VARSIZE/4-1,d0
clrvars:
        clr.l   (a0)+
        dbra    d0,clrvars
        moveq   #20,d7                  ; returncode
        moveq   #0,d6                   ; RDArgs
        move.l  4.w,a6
        lea     dosname(pc),a1
        moveq   #36,d0
        jsr     _LVOOpenLibrary(a6)
        tst.l   d0
        beq.w   exit
        move.l  d0,a6

        lea     template(pc),a0
        move.l  a0,d1
        move.l  a5,d2                   ; ARG0 = offset 0
        moveq   #0,d3
        jsr     _LVOReadArgs(a6)
        move.l  d0,d6
        beq.w   fault

        move.l  ARG0(a5),d1
        moveq   #ACCESS_READ,d2
        jsr     _LVOLock(a6)
        move.l  d0,d5
        beq.w   fault
        move.l  d5,d1
        lea     INFO(a5),a0
        move.l  a0,d2
        jsr     _LVOInfo(a6)
        move.l  d0,d4
        move.l  d5,d1
        jsr     _LVOUnLock(a6)
        tst.l   d4
        beq.w   fault

; ---- vrij = (NumBlocks - NumBlocksUsed) * BytesPerBlock / 1024 --------------
; BytesPerBlock is een macht van 2: schuiven i.p.v. 32-bit vermenigvuldigen.
        move.l  INFO+12(a5),d0
        sub.l   INFO+16(a5),d0
        move.l  INFO+20(a5),d1
        beq.w   fault
norm:
        cmpi.l  #1024,d1
        beq.w   normok
        bhi.w   normhi
        lsr.l   #1,d0
        add.l   d1,d1
        bra.w   norm
normhi:
        add.l   d0,d0
        lsr.l   #1,d1
        bra.w   norm
normok:
        move.l  d0,FREEKB(a5)
        move.l  ARG1(a5),a0
        move.l  (a0),NEEDKB(a5)
        move.l  ARG0(a5),PPATH(a5)
        lea     fmt(pc),a0
        move.l  a0,d1
        lea     PPATH(a5),a0
        move.l  a0,d2
        jsr     _LVOVPrintf(a6)

        moveq   #0,d7
        move.l  FREEKB(a5),d0
        cmp.l   NEEDKB(a5),d0
        bcc.w   genoeg
        moveq   #5,d7
        lea     msgweinig(pc),a0
        move.l  a0,d1
        moveq   #0,d2
        jsr     _LVOVPrintf(a6)
genoeg:
        cmpi.l  #ID_VALIDATED,INFO+8(a5)
        beq.w   klaar
        moveq   #10,d7
        lea     msgschrijf(pc),a0
        move.l  a0,d1
        moveq   #0,d2
        jsr     _LVOVPrintf(a6)
        bra.w   klaar

fault:
        jsr     _LVOIoErr(a6)
        move.l  d0,d1
        lea     progname(pc),a0
        move.l  a0,d2
        jsr     _LVOPrintFault(a6)
        moveq   #20,d7
klaar:
        move.l  d6,d1
        beq.w   closedos
        jsr     _LVOFreeArgs(a6)
closedos:
        move.l  a6,a1
        move.l  4.w,a6
        jsr     _LVOCloseLibrary(a6)
exit:
        move.l  d7,d0
        movem.l (sp)+,d2-d7/a2-a6
        rts

; ---- data -------------------------------------------------------------------
dosname:    dc.b    "dos.library",0
template:   dc.b    "PAD/A,NODIG/A/N",0
progname:   dc.b    "VrijKB",0
fmt:        dc.b    "Vrij op %s %ld KB (nodig: %ld KB)",10,0
msgweinig:  dc.b    "TE WEINIG vrije ruimte.",10,0
msgschrijf: dc.b    "Volume is niet schrijfbaar (beveiligd of valideren).",10,0
verstr:     dc.b    "$VER: VrijKB 1.0 (08.10.2026) WodemNet",0
            even
PAD
vars:       ds.b    VARSIZE
            end
