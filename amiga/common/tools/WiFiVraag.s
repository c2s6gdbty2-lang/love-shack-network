; ============================================================================
;  WiFiVraag 1.0 - vraagt in het Shell/IconX-venster om een waarde, controleert
;                  die en schrijft ze als een regel naar een bestand
;
;  Gebruik:  WiFiVraag PROMPT/A,TO/A/K,IP/S,NET/K,MIN/K/N,MAX/K/N,
;                      PREFIX/K,SUFFIX/K,HIDE/S,APPEND/S,NOLF/S
;    IP      waarde moet een IPv4-adres a.b.c.d zijn (0..255, laatste 1..254)
;    NET     waarde moet met deze tekst beginnen (bv. "192.168.1.")
;    MIN/MAX lengte voor tekst (standaard 1..63)
;    PREFIX/SUFFIX  tekst voor/na de waarde op dezelfde regel
;    HIDE    invoer niet tonen (sterretjes; RAW-modus van het console)
;    APPEND  achter het bestand toevoegen in plaats van het te vervangen
;    NOLF    geen regeleinde schrijven (voor `Type` in een backtick)
;  Tekst mag alleen afdrukbare ASCII bevatten (geen aanhalingsteken ").
;  Een lege invoer (alleen Return) of Ctrl-C/Ctrl-\ breekt af.
;  Na drie ongeldige pogingen stopt WiFiVraag.
;
;  Returncode: 0 = geschreven, 5 = afgebroken, 10 = drie keer ongeldig,
;              20 = argument- of schrijffout.
;  Pure 68000, AmigaOS 2.04+ (V37). Een CODE-hunk zonder relocaties;
;  variabelen in AllocMem-geheugen.
; ============================================================================

_LVOAllocMem        equ   -198
_LVOFreeMem         equ   -210
_LVOCloseLibrary    equ   -414
_LVOOpenLibrary     equ   -552
_LVOOpen            equ   -30
_LVOClose           equ   -36
_LVORead            equ   -42
_LVOWrite           equ   -48
_LVOInput           equ   -54
_LVOOutput          equ   -60
_LVOSeek            equ   -66
_LVOIoErr           equ   -132
_LVOSetMode         equ   -426
_LVOPrintFault      equ   -474
_LVOReadArgs        equ   -798
_LVOFreeArgs        equ   -858
_LVOPutStr          equ   -948

MODE_OLDFILE    equ   1005
MODE_NEWFILE    equ   1006

; ---- variabelen (AllocMem, a5) ---------------------------------------------
ARGPROMPT equ   0
ARGTO     equ   4
ARGIP     equ   8
ARGNET    equ   12
ARGMIN    equ   16
ARGMAX    equ   20
ARGPRE    equ   24
ARGSUF    equ   28
ARGHIDE   equ   32
ARGAPP    equ   36
ARGNOLF   equ   40
DOSB      equ   44
RDA       equ   48
INFH      equ   52
OUTFH     equ   56
MINL      equ   60
MAXL      equ   64
LEN       equ   68
TRIES     equ   72
RAW       equ   76
FH        equ   80
CH        equ   84                    ; 1 teken (RAW-modus)
BUF       equ   88                    ; invoerbuffer, 256
BUFSIZE   equ   256
VARSIZE   equ   348

start:
        movem.l d2-d7/a2-a6,-(sp)
        moveq   #20,d7
        move.l  4.w,a6
        lea     dosname(pc),a1
        moveq   #37,d0
        jsr     _LVOOpenLibrary(a6)
        move.l  d0,d6
        beq.w   exit0
        move.l  #VARSIZE,d0
        move.l  #$10001,d1
        jsr     _LVOAllocMem(a6)
        tst.l   d0
        beq.w   closedos
        move.l  d0,a5
        move.l  d6,DOSB(a5)
        move.l  d6,a6
        lea     template(pc),a0
        move.l  a0,d1
        move.l  a5,d2
        moveq   #0,d3
        jsr     _LVOReadArgs(a6)
        move.l  d0,RDA(a5)
        beq.w   fault
        jsr     _LVOInput(a6)
        move.l  d0,INFH(a5)
        jsr     _LVOOutput(a6)
        move.l  d0,OUTFH(a5)
        moveq   #1,d0
        tst.l   ARGMIN(a5)
        beq.w   minok
        move.l  ARGMIN(a5),a0
        move.l  (a0),d0
minok:
        move.l  d0,MINL(a5)
        moveq   #63,d0
        tst.l   ARGMAX(a5)
        beq.w   maxok
        move.l  ARGMAX(a5),a0
        move.l  (a0),d0
maxok:
        move.l  #BUFSIZE-2,d1
        cmp.l   d1,d0
        ble.w   maxok2
        move.l  d1,d0
maxok2:
        move.l  d0,MAXL(a5)
        moveq   #3,d0
        move.l  d0,TRIES(a5)

; ---- vragen -----------------------------------------------------------------
ask:
        move.l  ARGPROMPT(a5),a0        ; vraag ongebufferd tonen: PutStr
        bsr.w   wout                    ; zou bufferen tot na de invoer
        tst.l   ARGHIDE(a5)
        beq.w   readline
        bsr.w   readraw
        bra.w   gotline
readline:
        move.l  INFH(a5),d1
        lea     BUF(a5),a0
        move.l  a0,d2
        move.l  #BUFSIZE-1,d3
        jsr     _LVORead(a6)
        tst.l   d0
        beq.w   cancel                  ; EOF (Ctrl-\)
        bmi.w   rderr
        bsr.w   termstrip
gotline:
        tst.l   d0                      ; d0 < 0: afgebroken in readraw
        bmi.w   cancel
        tst.l   LEN(a5)
        beq.w   cancel                  ; lege invoer = afbreken

        tst.l   ARGIP(a5)
        beq.w   chktext
        bsr.w   checkip
        tst.l   d0
        bne.w   invalid
        bra.w   valid
chktext:
        move.l  LEN(a5),d0
        cmp.l   MINL(a5),d0
        blt.w   badlen
        cmp.l   MAXL(a5),d0
        bgt.w   badlen
        lea     BUF(a5),a0
chkch:
        move.b  (a0)+,d0
        beq.w   valid
        cmpi.b  #32,d0
        blo.w   badch
        cmpi.b  #126,d0
        bhi.w   badch
        cmpi.b  #34,d0
        beq.w   badch
        bra.w   chkch
badlen:
        lea     msglen(pc),a0
        bra.w   invmsg
badch:
        lea     msgch(pc),a0
        bra.w   invmsg
invalid:
        lea     msgip(pc),a0
invmsg:
        bsr.w   wout                    ; ongebufferd (Write)
        subq.l  #1,TRIES(a5)
        bgt.w   ask
        moveq   #10,d7
        lea     msgstop(pc),a0
        bsr.w   wout                    ; ongebufferd (Write)
        bra.w   cleanup

; ---- schrijven ----------------------------------------------------------------
valid:
        moveq   #0,d0
        move.l  d0,FH(a5)
        tst.l   ARGAPP(a5)
        beq.w   opennew
        move.l  ARGTO(a5),d1
        move.l  #MODE_OLDFILE,d2
        jsr     _LVOOpen(a6)
        move.l  d0,FH(a5)
        beq.w   opennew
        move.l  d0,d1
        moveq   #0,d2
        moveq   #1,d3                   ; OFFSET_END
        jsr     _LVOSeek(a6)
        bra.w   opened
opennew:
        move.l  ARGTO(a5),d1
        move.l  #MODE_NEWFILE,d2
        jsr     _LVOOpen(a6)
        move.l  d0,FH(a5)
        beq.w   wrerr
opened:
        move.l  ARGPRE(a5),a0
        bsr.w   wstr
        bmi.w   wrerrc
        lea     BUF(a5),a0
        bsr.w   wstr
        bmi.w   wrerrc
        move.l  ARGSUF(a5),a0
        bsr.w   wstr
        bmi.w   wrerrc
        tst.l   ARGNOLF(a5)
        bne.w   nolf
        lea     lf(pc),a0
        bsr.w   wstr
        bmi.w   wrerrc
nolf:
        move.l  FH(a5),d1
        jsr     _LVOClose(a6)
        moveq   #0,d7
        bra.w   cleanup
wrerrc:
        move.l  FH(a5),d1
        jsr     _LVOClose(a6)
wrerr:
        lea     msgwr(pc),a0
        bsr.w   wout                    ; ongebufferd (Write)
        moveq   #20,d7
        bra.w   cleanup
rderr:
        lea     msgrd(pc),a0
        bsr.w   wout                    ; ongebufferd (Write)
        moveq   #20,d7
        bra.w   cleanup
cancel:
        lea     msgcancel(pc),a0
        bsr.w   wout                    ; ongebufferd (Write)
        moveq   #5,d7
        bra.w   cleanup
fault:
        jsr     _LVOIoErr(a6)
        move.l  d0,d1
        lea     progname(pc),a0
        move.l  a0,d2
        jsr     _LVOPrintFault(a6)
cleanup:
        move.l  RDA(a5),d1
        beq.w   noargs
        move.l  DOSB(a5),a6
        jsr     _LVOFreeArgs(a6)
noargs:
        move.l  4.w,a6
        move.l  a5,a1
        move.l  #VARSIZE,d0
        jsr     _LVOFreeMem(a6)
closedos:
        move.l  4.w,a6
        move.l  d6,a1
        jsr     _LVOCloseLibrary(a6)
exit0:
        move.l  d7,d0
        movem.l (sp)+,d2-d7/a2-a6
        rts

; ---- wstr: schrijf C-string a0 (mag 0 zijn) naar FH; N-vlag bij fout ----------
wstr:
        move.l  a0,d0
        beq.w   wsok
        move.l  a0,d2
        moveq   #0,d3
wslen:
        tst.b   (a0)+
        beq.w   wsgo
        addq.l  #1,d3
        bra.w   wslen
wsgo:
        tst.l   d3
        beq.w   wsok
        move.l  FH(a5),d1
        jsr     _LVOWrite(a6)
        cmp.l   d3,d0
        bne.w   wsbad
wsok:
        moveq   #0,d0
        rts
wsbad:
        moveq   #-1,d0
        rts

; ---- readraw: invoer met sterretjes; d0 = 0 klaar, -1 afgebroken -------------
readraw:
        clr.l   LEN(a5)
        clr.l   RAW(a5)
        move.l  INFH(a5),d1
        moveq   #1,d2
        jsr     _LVOSetMode(a6)
        tst.l   d0
        beq.w   rawfail
        moveq   #1,d0
        move.l  d0,RAW(a5)
rawloop:
        move.l  INFH(a5),d1
        lea     CH(a5),a0
        move.l  a0,d2
        moveq   #1,d3
        jsr     _LVORead(a6)
        tst.l   d0
        ble.w   rawabort
        move.b  CH(a5),d0
        cmpi.b  #13,d0
        beq.w   rawdone
        cmpi.b  #10,d0
        beq.w   rawdone
        cmpi.b  #3,d0                   ; Ctrl-C
        beq.w   rawabort
        cmpi.b  #28,d0                  ; Ctrl-\
        beq.w   rawabort
        cmpi.b  #8,d0                   ; Backspace
        beq.w   rawbs
        cmpi.b  #127,d0                 ; Del
        beq.w   rawbs
        cmpi.b  #155,d0                 ; CSI: reeks overslaan
        beq.w   rawcsi
        cmpi.b  #32,d0
        blo.w   rawloop
        move.l  LEN(a5),d1
        cmp.l   MAXL(a5),d1
        bge.w   rawloop                 ; vol: negeren
        lea     BUF(a5),a0
        move.l  a0,d2
        add.l   d1,d2
        move.l  d2,a0
        move.b  d0,(a0)
        addq.l  #1,LEN(a5)
        lea     star(pc),a0
        bsr.w   wout
        bra.w   rawloop
rawbs:
        tst.l   LEN(a5)
        beq.w   rawloop
        subq.l  #1,LEN(a5)
        lea     bsseq(pc),a0
        bsr.w   wout
        bra.w   rawloop
rawcsi:
        move.l  INFH(a5),d1
        lea     CH(a5),a0
        move.l  a0,d2
        moveq   #1,d3
        jsr     _LVORead(a6)
        tst.l   d0
        ble.w   rawabort
        move.b  CH(a5),d0
        cmpi.b  #64,d0
        blo.w   rawcsi
        bra.w   rawloop
rawdone:
        lea     BUF(a5),a0
        move.l  a0,d2
        add.l   LEN(a5),d2
        move.l  d2,a0
        clr.b   (a0)
        bsr.w   rawoff
        lea     lf(pc),a0
        bsr.w   wout
        moveq   #0,d0
        rts
rawabort:
        bsr.w   rawoff
        lea     lf(pc),a0
        bsr.w   wout
        moveq   #-1,d0
        rts
rawfail:                                ; geen console: gewone regel lezen
        lea     msgnoraw(pc),a0
        bsr.w   wout                    ; ongebufferd (Write)
        move.l  INFH(a5),d1
        lea     BUF(a5),a0
        move.l  a0,d2
        move.l  #BUFSIZE-1,d3
        jsr     _LVORead(a6)
        tst.l   d0
        ble.w   rawabort2
        bsr.w   termstrip
        moveq   #0,d0
        rts
rawabort2:
        moveq   #-1,d0
        rts
rawoff:
        tst.l   RAW(a5)
        beq.w   rawoffx
        move.l  INFH(a5),d1
        moveq   #0,d2
        jsr     _LVOSetMode(a6)
        clr.l   RAW(a5)
rawoffx:
        rts
wout:                                   ; C-string a0 naar Output()
        move.l  a0,d2
        moveq   #0,d3
wolen:
        tst.b   (a0)+
        beq.w   wogo
        addq.l  #1,d3
        bra.w   wolen
wogo:
        move.l  OUTFH(a5),d1
        jsr     _LVOWrite(a6)
        rts

; ---- termstrip: BUF afsluiten na d0 bytes, afkappen bij CR/LF; LEN invullen --
termstrip:
        lea     BUF(a5),a0
        move.l  a0,d2
        add.l   d0,d2
        move.l  d2,a1
        clr.b   (a1)
        moveq   #0,d1
tsloop:
        move.b  (a0),d2
        beq.w   tsdone
        cmpi.b  #10,d2
        beq.w   tsdone
        cmpi.b  #13,d2
        beq.w   tsdone
        addq.l  #1,a0
        addq.l  #1,d1
        bra.w   tsloop
tsdone:
        clr.b   (a0)
        move.l  d1,LEN(a5)
        rts

; ---- checkip: BUF = a.b.c.d (0..255, laatste 1..254), begint met NET ---------
;      d0 = 0 geldig, anders ongeldig
checkip:
        lea     BUF(a5),a0
        move.l  ARGNET(a5),d0
        beq.w   ipparse
        move.l  d0,a1
netcmp:
        move.b  (a1)+,d0
        beq.w   ipparse
        cmp.b   (a0)+,d0
        bne.w   ipbad
        bra.w   netcmp
ipparse:
        lea     BUF(a5),a0
        moveq   #0,d4                   ; aantal getallen
ipnum:
        moveq   #0,d1                   ; waarde
        moveq   #0,d2                   ; cijfers
ipdig:
        move.b  (a0)+,d0
        cmpi.b  #48,d0
        blo.w   ipend
        cmpi.b  #57,d0
        bhi.w   ipend
        subi.b  #48,d0
        ext.w   d0
        tst.l   d2                      ; voorloopnul gevolgd door cijfer?
        beq.w   ipfirst
        tst.l   d1
        beq.w   ipbad
ipfirst:
        mulu.w  #10,d1
        add.w   d0,d1
        addq.l  #1,d2
        cmpi.l  #3,d2
        bgt.w   ipbad
        bra.w   ipdig
ipend:
        tst.l   d2
        beq.w   ipbad
        cmpi.l  #255,d1
        bgt.w   ipbad
        addq.l  #1,d4
        cmpi.b  #46,d0                  ; '.'
        beq.w   ipdot
        tst.b   d0
        bne.w   ipbad
        cmpi.l  #4,d4
        bne.w   ipbad
        tst.l   d1                      ; laatste deel 1..254
        beq.w   ipbad
        cmpi.l  #255,d1
        beq.w   ipbad
        moveq   #0,d0
        rts
ipdot:
        cmpi.l  #4,d4
        bge.w   ipbad
        bra.w   ipnum
ipbad:
        moveq   #1,d0
        rts

dosname:
        dc.b    "dos.library",0
progname:
        dc.b    "WiFiVraag",0
template:
        dc.b    "PROMPT/A,TO/A/K,IP/S,NET/K,MIN/K/N,MAX/K/N,PREFIX/K,SUFFIX/K,HIDE/S,APPEND/S,NOLF/S",0
version:
        dc.b    "$VER: WiFiVraag 1.0 (12.10.2026) WiFiNet A500",0
msgip:
        dc.b    "  Ongeldig adres. Voorbeeld: 192.168.10.70",10,0
msglen:
        dc.b    "  Ongeldige lengte.",10,0
msgch:
        dc.b    "  Ongeldig teken (alleen gewone letters, cijfers en leestekens; geen aanhalingsteken).",10,0
msgstop:
        dc.b    "  Drie keer ongeldig: gestopt.",10,0
msgcancel:
        dc.b    "  Afgebroken.",10,0
msgwr:
        dc.b    "  Schrijven mislukt.",10,0
msgrd:
        dc.b    "  Lezen van de invoer mislukt.",10,0
msgnoraw:
        dc.b    "(invoer is zichtbaar) ",0
star:
        dc.b    "*",0
bsseq:
        dc.b    8,32,8,0
lf:
        dc.b    10,0
        even
        end
