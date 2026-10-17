/* CRCLijst - A600AirPrint: legt CRC32 + grootte van bestanden vast en controleert ze later.
   Afgeleid van CRCCheck 1.0 (WodemNB), met een extra MAAK-stand.
   Gebruik:
     CRCLijst <lijst> MAAK <patroon> [<patroon> ...]   schrijft "crc32hex grootte pad" per bestand
     CRCLijst <lijst>                                  controleert alle regels van de lijst
     CRCLijst VRIJ <pad> MIN <KB>                      rc 0 als het volume van <pad> beschrijfbaar is
                                                       en minstens <KB> KB vrij heeft, anders 5
   Patronen zijn gewone AmigaDOS-patronen (bv. DEVS:Networks/#?). Een patroon zonder treffers
   (of een volume/assign dat niet bestaat) komt als "# geen: <patroon>" in de lijst; er
   verschijnt nooit een "Please insert volume"-requester (pr_WindowPtr = -1).
   rc 0 = OK, 5 = afwijking/ontbrekend, 20 = lijst niet te openen/schrijven.
   68000, alleen exec.library en dos.library. Leest alleen; schrijft alleen <lijst>. */
#include <exec/types.h>
#include <exec/memory.h>
#include <dos/dos.h>
#include <dos/dosasl.h>
#include <dos/dosextens.h>
#include <proto/exec.h>
#include <proto/dos.h>

static const char ver[] = "$VER: CRCLijst 1.0 (16.10.2026) A600AirPrint";
static ULONG tab[256];
#define BUFSZ 8192
#define PADSZ 256

static void mktab(void) {
    ULONG i, j, c;
    for (i = 0; i < 256; i++) { c = i; for (j = 0; j < 8; j++) c = (c & 1) ? (c >> 1) ^ 0xEDB88320UL : c >> 1; tab[i] = c; }
}
static ULONG hexv(const char **p) {
    ULONG v = 0; char c;
    while ((c = **p) && c != ' ' && c != '\t') {
        v <<= 4;
        if (c >= '0' && c <= '9') v |= c - '0'; else if (c >= 'a' && c <= 'f') v |= c - 'a' + 10; else if (c >= 'A' && c <= 'F') v |= c - 'A' + 10;
        (*p)++;
    }
    return v;
}
static ULONG decv(const char **p) { ULONG v = 0; while (**p >= '0' && **p <= '9') { v = v * 10 + (**p - '0'); (*p)++; } return v; }

/* 0 = OK, 1 = niet te openen, 2 = leesfout */
static int crcfile(const char *pad, UBYTE *buf, ULONG *crcp, ULONG *sizep) {
    BPTR fh = Open((STRPTR)pad, MODE_OLDFILE); LONG n, i; ULONG crc = 0xFFFFFFFFUL, got = 0;
    if (!fh) return 1;
    while ((n = Read(fh, buf, BUFSZ)) > 0) { got += n; for (i = 0; i < n; i++) crc = tab[(crc ^ buf[i]) & 0xFF] ^ (crc >> 8); }
    Close(fh);
    if (n < 0) return 2;
    *crcp = crc ^ 0xFFFFFFFFUL; *sizep = got; return 0;
}

static LONG maak(BPTR out, STRPTR *pat, UBYTE *buf) {
    struct AnchorPath *ap; LONG nfile = 0;
    ap = AllocMem(sizeof(struct AnchorPath) + PADSZ, MEMF_ANY | MEMF_CLEAR);
    if (!ap) return -1;
    for (; *pat; pat++) {
        LONG err, hits = 0;
        ap->ap_Strlen = PADSZ; ap->ap_BreakBits = 0; ap->ap_Flags = 0;
        for (err = MatchFirst(*pat, ap); !err; err = MatchNext(ap)) {
            ULONG crc, size; int r;
            if (ap->ap_Info.fib_DirEntryType >= 0) continue;          /* lades overslaan */
            r = crcfile((char *)ap->ap_Buf, buf, &crc, &size);
            if (r == 0) { FPrintf(out, "%08lx %ld %s\n", crc, size, (LONG)ap->ap_Buf); hits++; nfile++; }
            else FPrintf(out, "# leesfout: %s\n", (LONG)ap->ap_Buf);
        }
        MatchEnd(ap);
        if (!hits) FPrintf(out, "# geen: %s\n", (LONG)*pat);
    }
    FreeMem(ap, sizeof(struct AnchorPath) + PADSZ);
    return nfile;
}

static LONG controle(BPTR lst, UBYTE *buf, LONG *okp) {
    char line[PADSZ + 32]; LONG bad = 0, ok = 0;
    while (FGets(lst, line, sizeof(line) - 1)) {
        const char *p = line; ULONG want, size, crc, got; char *e; int r;
        if (line[0] == '#' || line[0] == '\n' || line[0] == 0) continue;
        for (e = line; *e; e++) if (*e == '\n' || *e == '\r') { *e = 0; break; }
        want = hexv(&p); while (*p == ' ') p++;
        size = decv(&p); while (*p == ' ') p++;
        r = crcfile(p, buf, &crc, &got);
        if (r == 1) { Printf("  ONTBREEKT  %s\n", (LONG)p); bad++; }
        else if (r == 2) { Printf("  LEESFOUT   %s\n", (LONG)p); bad++; }
        else if (got != size || crc != want) { Printf("  GEWIJZIGD  %s (%ld bytes, crc %08lx; vastgelegd %ld / %08lx)\n", (LONG)p, got, crc, size, want); bad++; }
        else ok++;
    }
    *okp = ok; return bad;
}

/* schrijfbaar + vrije ruimte van het volume waar pad op staat (werkt ook voor assigns als SYS:) */
static LONG vrij(STRPTR pad, LONG min) {
    struct InfoData *id = AllocMem(sizeof(struct InfoData), MEMF_ANY | MEMF_CLEAR);
    BPTR lk = Lock(pad, ACCESS_READ); LONG rc = 5;
    if (lk && id && Info(lk, id)) {
        ULONG kb = (id->id_NumBlocks - id->id_NumBlocksUsed) * (id->id_BytesPerBlock / 512) / 2;
        BOOL rw = id->id_DiskState == ID_VALIDATED;
        Printf("%s %s, %ld KB vrij (nodig %ld KB)\n", (LONG)pad, (LONG)(rw ? "beschrijfbaar" : "NIET beschrijfbaar"), kb, min);
        if (rw && kb >= (ULONG)min) rc = 0;
    } else Printf("%s: niet gevonden\n", (LONG)pad);
    if (lk) UnLock(lk);
    if (id) FreeMem(id, sizeof(struct InfoData));
    return rc;
}

int main(void) {
    struct RDArgs *ra; LONG arg[5] = {0, 0, 0, 0, 0};
    struct Process *me = (struct Process *)FindTask(NULL); APTR oldwin = me->pr_WindowPtr;
    UBYTE *buf; BPTR fh; LONG rc = 20;
    mktab();
    ra = ReadArgs("LIJST,MAAK/S,VRIJ/K,MIN/K/N,PATRONEN/M", arg, NULL);
    if (!ra || (!arg[0] && !arg[2])) { PutStr("CRCLijst: gebruik CRCLijst <lijst> [MAAK <patroon> ...] | VRIJ <pad> MIN <KB>\n"); if (ra) FreeArgs(ra); return 20; }
    buf = AllocMem(BUFSZ, MEMF_ANY);
    if (!buf) { FreeArgs(ra); return 20; }
    me->pr_WindowPtr = (APTR)-1;
    if (arg[2]) {
        rc = vrij((STRPTR)arg[2], arg[3] ? *(LONG *)arg[3] : 0);
    } else if (arg[1]) {
        if (!arg[4]) PutStr("CRCLijst: MAAK zonder patronen\n");
        else if ((fh = Open((STRPTR)arg[0], MODE_NEWFILE))) {
            LONG n;
            FPrintf(fh, "# CRCLijst 1.0: crc32 grootte pad\n");
            n = maak(fh, (STRPTR *)arg[4], buf);
            Close(fh);
            if (n >= 0) { Printf("CRCLijst: %ld bestanden vastgelegd in %s\n", n, arg[0]); rc = 0; }
        } else PutStr("CRCLijst: lijst niet te schrijven\n");
    } else if ((fh = Open((STRPTR)arg[0], MODE_OLDFILE))) {
        LONG ok, bad = controle(fh, buf, &ok);
        Close(fh);
        Printf("CRCLijst: %ld ongewijzigd, %ld afwijkend\n", ok, bad);
        rc = bad ? 5 : 0;
    } else PutStr("CRCLijst: lijst niet leesbaar\n");
    me->pr_WindowPtr = oldwin;
    FreeMem(buf, BUFSZ); FreeArgs(ra);
    return rc;
}
