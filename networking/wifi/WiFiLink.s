; ============================================================================
;  WiFiLink 1.0 - wacht (begrensd) tot een SANA-II-wifidriver verbonden is
;
;  Gebruik:  WiFiLink DEVICE/A,UNIT/K/N,TIMEOUT/K/N,QUIET/S
;            WiFiLink DEVS:Networks/wifipi.device TIMEOUT 45
;
;  Vervangt WaitForLink 1.1 (prism2v2) voor wifipi.device: WaitForLink wacht
;  op S2EVENT_LINKUP (1<<16) en dat event zit niet in wifipi's EVENT_MASK
;  (unit.c: CONNECT/DISCONNECT/ONLINE/...), zodat S2_ONEVENT direct met
;  S2ERR_NOT_SUPPORTED terugkomt. Een S2_ONEVENT op S2EVENT_CONNECT kent een
;  race: is de verbinding er al, dan komt het event nooit meer.
;  Daarom vraagt WiFiLink elke seconde S2_GETSIGNALQUALITY ($C010): wifipi
;  antwoordt pas zonder fout als de unit online EN verbonden is
;  (IFF_ONLINE + IFF_CONNECTED, gezet bij BRCMF_E_LINK up).
;
;  Opent het device gedeeld (flags 0), zoals AmiTCP en WirelessManager.
;  Stuurt alleen S2_GETSIGNALQUALITY; verandert niets aan de driver.
;
;  Returncode: 0  = verbonden (signaalsterkte wordt getoond)
;              5  = niet verbonden binnen TIMEOUT seconden, of Ctrl-C
;              10 = device kent S2_GETSIGNALQUALITY niet (geen wifidriver?)
;              20 = argumentfout of device niet te openen
;  Pure 68000, AmigaOS 2.04+ (V37). Een CODE-hunk zonder relocaties;
;  variabelen in AllocMem-geheugen (niets schrijft in de code-hunk).
; ============================================================================

_LVOSetSignal       equ   -306
_LVOAllocMem        equ   -198
_LVOFreeMem         equ   -210
_LVOCloseLibrary    equ   -414
_LVOOpenDevice      equ   -444
_LVOCloseDevice     equ   -450
_LVODoIO            equ   -456
_LVOOpenLibrary     equ   -552
_LVOCreateIORequest equ   -654
_LVODeleteIORequest equ   -660
_LVOCreateMsgPort   equ   -666
_LVODeleteMsgPort   equ   -672
_LVODelay           equ   -198
_LVOPrintFault      equ   -474
_LVOIoErr           equ   -132
_LVOReadArgs        equ   -798
_LVOFreeArgs        equ   -858
_LVOVPrintf         equ   -954

IO_COMMAND      equ   28
IO_FLAGS        equ   30
IO_ERROR        equ   31
IOS2_WIREERROR  equ   32
IOS2_STATDATA   equ   80
IOS2SIZE        equ   88
S2_GETSIGQUAL   equ   $C010
S2ERR_OUTOFSERV equ   10
SIGF_CTRLC      equ   $1000

; ---- variabelen (AllocMem, a5) ---------------------------------------------
ARGDEV  equ     0                       ; DEVICE/A  (STRPTR)
ARGUNIT equ     4                       ; UNIT/K/N  (LONG *)
ARGTMO  equ     8                       ; TIMEOUT/K/N (LONG *)
ARGQ    equ     12                      ; QUIET/S
DOSB    equ     16
RDA     equ     20
PORT    equ     24
IOR     equ     28
OPENED  equ     32
UNIT    equ     36
TMO     equ     40
LEFT    equ     44
P       equ     48                      ; VPrintf-argumenten, 4 longs
QUAL    equ     64                      ; Sana2SignalQuality: Signal, Noise
VARSIZE equ     80

start:
        movem.l d2-d7/a2-a6,-(sp)
        moveq   #20,d7                  ; returncode
        move.l  4.w,a6
        lea     dosname(pc),a1
        moveq   #37,d0
        jsr     _LVOOpenLibrary(a6)
        move.l  d0,d6                   ; dos.library
        beq.w   exit0
        moveq   #VARSIZE,d0
        move.l  #$10001,d1              ; MEMF_PUBLIC|MEMF_CLEAR
        jsr     _LVOAllocMem(a6)
        tst.l   d0
        beq.w   closedos
        move.l  d0,a5
        move.l  d6,DOSB(a5)

        move.l  DOSB(a5),a6
        lea     template(pc),a0
        move.l  a0,d1
        move.l  a5,d2
        moveq   #0,d3
        jsr     _LVOReadArgs(a6)
        move.l  d0,RDA(a5)
        beq.w   fault

        moveq   #0,d0                   ; UNIT, standaard 0
        tst.l   ARGUNIT(a5)
        beq.w   unitok
        move.l  ARGUNIT(a5),a0
        move.l  (a0),d0
unitok:
        move.l  d0,UNIT(a5)
        moveq   #30,d0                  ; TIMEOUT, standaard 30 s
        tst.l   ARGTMO(a5)
        beq.w   tmook
        move.l  ARGTMO(a5),a0
        move.l  (a0),d0
tmook:
        moveq   #1,d1                   ; begrenzen op 1..600
        cmp.l   d1,d0
        bge.w   tmomin
        moveq   #1,d0
tmomin:
        move.l  #600,d1
        cmp.l   d1,d0
        ble.w   tmomax
        move.l  #600,d0
tmomax:
        move.l  d0,TMO(a5)
        move.l  d0,LEFT(a5)

        move.l  4.w,a6
        jsr     _LVOCreateMsgPort(a6)
        move.l  d0,PORT(a5)
        beq.w   nomem
        move.l  d0,a0
        moveq   #IOS2SIZE,d0
        jsr     _LVOCreateIORequest(a6)
        move.l  d0,IOR(a5)
        beq.w   nomem

        move.l  ARGDEV(a5),a0
        move.l  UNIT(a5),d0
        move.l  IOR(a5),a1
        moveq   #0,d1                   ; gedeeld openen
        jsr     _LVOOpenDevice(a6)
        tst.l   d0
        beq.w   devopen
        ext.w   d0
        ext.l   d0
        move.l  ARGDEV(a5),P(a5)
        move.l  UNIT(a5),P+4(a5)
        move.l  d0,P+8(a5)
        lea     fmtnoopen(pc),a0
        bsr.w   print
        bra.w   cleanup
devopen:
        moveq   #1,d0
        move.l  d0,OPENED(a5)
        tst.l   ARGQ(a5)
        bne.w   poll
        move.l  ARGDEV(a5),P(a5)
        move.l  TMO(a5),P+4(a5)
        lea     fmtwait(pc),a0
        bsr.w   print

; ---- elke seconde S2_GETSIGNALQUALITY ---------------------------------------
poll:
        move.l  IOR(a5),a1
        move.w  #S2_GETSIGQUAL,IO_COMMAND(a1)
        clr.b   IO_FLAGS(a1)
        clr.b   IO_ERROR(a1)
        clr.l   IOS2_WIREERROR(a1)
        lea     QUAL(a5),a0
        clr.l   (a0)
        clr.l   4(a0)
        move.l  a0,IOS2_STATDATA(a1)
        move.l  4.w,a6
        jsr     _LVODoIO(a6)
        move.l  IOR(a5),a1
        move.b  IO_ERROR(a1),d0
        tst.b   d0
        beq.w   linked
        cmpi.b  #S2ERR_OUTOFSERV,d0
        bne.w   nosupport
        moveq   #0,d0                   ; Ctrl-C?
        move.l  #SIGF_CTRLC,d1
        jsr     _LVOSetSignal(a6)
        andi.l  #SIGF_CTRLC,d0
        bne.w   broken
        subq.l  #1,LEFT(a5)
        ble.w   timeout
        move.l  DOSB(a5),a6
        moveq   #50,d1                  ; 1 seconde
        jsr     _LVODelay(a6)
        bra.w   poll

linked:
        moveq   #0,d7
        tst.l   ARGQ(a5)
        bne.w   cleanup
        move.l  QUAL(a5),P(a5)
        move.l  QUAL+4(a5),P+4(a5)
        lea     fmtok(pc),a0
        bsr.w   print
        bra.w   cleanup
nosupport:
        moveq   #10,d7
        ext.w   d0
        ext.l   d0
        move.l  d0,P(a5)
        move.l  IOR(a5),a1
        move.l  IOS2_WIREERROR(a1),P+4(a5)
        lea     fmtnosup(pc),a0
        bsr.w   print
        bra.w   cleanup
broken:
        moveq   #5,d7
        lea     fmtbreak(pc),a0
        bsr.w   print
        bra.w   cleanup
timeout:
        moveq   #5,d7
        move.l  TMO(a5),P(a5)
        lea     fmttmo(pc),a0
        bsr.w   print
        bra.w   cleanup

nomem:
        lea     fmtnomem(pc),a0
        bsr.w   print
        bra.w   cleanup
fault:
        move.l  DOSB(a5),a6
        jsr     _LVOIoErr(a6)
        move.l  d0,d1
        lea     progname(pc),a0
        move.l  a0,d2
        jsr     _LVOPrintFault(a6)

cleanup:
        move.l  4.w,a6
        tst.l   OPENED(a5)
        beq.w   noclose
        move.l  IOR(a5),a1
        jsr     _LVOCloseDevice(a6)
noclose:
        move.l  IOR(a5),a0
        move.l  a0,d0
        beq.w   noior
        jsr     _LVODeleteIORequest(a6)
noior:
        move.l  PORT(a5),a0
        move.l  a0,d0
        beq.w   noport
        jsr     _LVODeleteMsgPort(a6)
noport:
        move.l  RDA(a5),d1
        beq.w   noargs
        move.l  DOSB(a5),a6
        jsr     _LVOFreeArgs(a6)
noargs:
        move.l  4.w,a6
        move.l  a5,a1
        moveq   #VARSIZE,d0
        jsr     _LVOFreeMem(a6)
closedos:
        move.l  4.w,a6
        move.l  d6,a1
        jsr     _LVOCloseLibrary(a6)
exit0:
        move.l  d7,d0
        movem.l (sp)+,d2-d7/a2-a6
        rts

print:
        movem.l d0-d2/a0-a1/a6,-(sp)
        move.l  a0,d1
        lea     P(a5),a0
        move.l  a0,d2
        move.l  DOSB(a5),a6
        jsr     _LVOVPrintf(a6)
        movem.l (sp)+,d0-d2/a0-a1/a6
        rts

dosname:
        dc.b    "dos.library",0
progname:
        dc.b    "WiFiLink",0
template:
        dc.b    "DEVICE/A,UNIT/K/N,TIMEOUT/K/N,QUIET/S",0
version:
        dc.b    "$VER: WiFiLink 1.0 (12.10.2026) WiFiNet A500",0
fmtwait:
        dc.b    "    Wachten op wifi-verbinding van %s (max. %ld s)...",10,0
fmtok:
        dc.b    "    Wifi verbonden: signaal %ld dBm, ruis %ld dBm.",10,0
fmttmo:
        dc.b    "    Geen wifi-verbinding binnen %ld s.",10,0
fmtbreak:
        dc.b    "    Afgebroken (Ctrl-C).",10,0
fmtnosup:
        dc.b    "    Device geeft geen verbindingsstatus (fout %ld/%ld).",10,0
fmtnoopen:
        dc.b    "    %s unit %ld kon niet geopend worden (fout %ld).",10,0
fmtnomem:
        dc.b    "    Te weinig geheugen.",10,0
        even
        end
