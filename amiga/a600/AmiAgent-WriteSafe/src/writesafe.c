/* writesafe.c - LSN 0004: WRITE-SAFE (The Love Shack Network).
 *
 * Included by amiagent.c, only in the AMIAGENT_WRITESAFE build. Adds one
 * command, COPYIN: copy one new file from a fixed share folder to a local
 * folder. Everything else stays exactly as in the READONLY build: PUT, AREXX,
 * INPUT, UIACT and BREAK stay refused, EXEC stays the fixed word list.
 *
 * The mandate is local and single-use. It exists only as arguments of this
 * process, set by a script somebody started at the machine. It lives in RAM,
 * cannot be extended or re-armed over the network, and once closed (time up,
 * count used, or Ctrl-C) it stays closed until the process is started again.
 *
 * Paths are judged by what they are on disk, never by their text: the parent
 * lock is walked up with ParentDir()/SameLock() until it meets the held root
 * lock, which assigns, "/" paths, links and duplicate volume names cannot fool.
 *
 * Never overwrite, in independent layers:
 *   1. a directory scan with ExNext() sees every entry, dangling links too,
 *      where Lock() would say "not found". Runs before the copy and again
 *      right before the rename.
 *   2. Rename(), which is one packet to the filesystem and does not replace.
 *   3. a live probe at arming time proves (2) on this very filesystem; if
 *      Rename() would replace a file, the mandate is refused.
 * The final name is never opened for writing: only an agent-made temporary
 * name is, in the same folder, and that name is scanned first as well.
 */
#include <dos/dostags.h>
#include <dos/filehandler.h>

#define CMD_COPYIN   0x40
#define WS_F_CHECK   0x01
#define WS_TMPPREFIX ".ws-tmp-"
#define WS_MAXNAME   30
#define WS_MAXPATH   200
#define WS_RESERVEKB 64
#define WS_MAXNOREAD 6
#define WS_LOG       "PROGDIR:Log/write.log"
#define WS_ID(a,b,c,d) (((ULONG)(a)<<24)|((ULONG)(b)<<16)|((ULONG)(c)<<8)|(ULONG)(d))

static struct {
    int configured;           /* a mandate was given on the command line */
    int closed;               /* irreversible within this process */
    BPTR root;
    char rootname[WS_MAXPATH];
    char srcroot[WS_MAXPATH];
    char client[32];
    LONG start, deadline;     /* seconds since 1978 */
    LONG writes_left;
    ULONG maxbytes;
    ULONG seq;
    BPTR noread[WS_MAXNOREAD];
    int nnoread;
} g_ws;

static ULONG g_crctab[256];

#ifdef AMIAGENT_WS_TEST
/* Fault injection. Only in the emulator build amiagent-ws-test. */
static char g_wshook[80];
#define WS_HOOK(n) (strstr(g_wshook, n) != NULL)
static LONG ws_hookval(const char *n)
{
    const char *p = strstr(g_wshook, n);
    return p && p[strlen(n)] == ':' ? atol(p + strlen(n) + 1) : 0;   /* '=' would split in ReadArgs */
}
#else
#define WS_HOOK(n) 0
#endif

static LONG ws_now(void)
{
    struct DateStamp ds;
    DateStamp(&ds);
    return (ds.ds_Days * 1440L + ds.ds_Minute) * 60L + ds.ds_Tick / TICKS_PER_SECOND;
}

/* Write one line to the local log. Returns 0 when it did not reach the disk. */
static int ws_log(const char *what, const char *detail)
{
    char line[WS_MAXPATH * 2 + 80];
    LONG n, ok;
    BPTR fh = Open((STRPTR)WS_LOG, MODE_READWRITE);
    if (!fh) return 0;
    Seek(fh, 0, OFFSET_END);
    sprintf(line, "%ld #%lu %s %s\n", (long)ws_now(), (unsigned long)g_ws.seq, what, detail);
    n = (LONG)strlen(line);
    ok = Write(fh, line, n) == n;
    return Close(fh) && ok;
}

static void crc_init(void)
{
    ULONG i, c;
    int k;
    for (i = 0; i < 256; i++) {
        c = i;
        for (k = 0; k < 8; k++) c = (c & 1) ? 0xEDB88320UL ^ (c >> 1) : c >> 1;
        g_crctab[i] = c;
    }
}

static ULONG crc_add(ULONG c, const UBYTE *p, LONG n)
{
    while (n-- > 0) c = g_crctab[(c ^ *p++) & 0xFF] ^ (c >> 8);
    return c;
}

/* Is the object behind lock inside (or equal to) root? */
static int ws_under(BPTR lock, BPTR root)
{
    BPTR cur = DupLock(lock), up;
    while (cur) {
        if (SameLock(cur, root) == LOCK_SAME) { UnLock(cur); return 1; }
        up = ParentDir(cur);
        UnLock(cur);
        cur = up;
    }
    return 0;
}

static int ws_isdir(BPTR lock)
{
    struct FileInfoBlock *fib = (struct FileInfoBlock *)AllocDosObject(DOS_FIB, NULL);
    int dir = 0;
    if (fib) {
        if (Examine(lock, fib)) dir = fib->fib_DirEntryType >= 0;
        FreeDosObject(DOS_FIB, fib);
    }
    return dir;
}

static int ws_ieq(const char *a, const char *b)
{
    for (;;) {
        char x = *a++, y = *b++;
        if (x >= 'a' && x <= 'z') x -= 32;
        if (y >= 'a' && y <= 'z') y -= 32;
        if (x != y) return 0;
        if (!x) return 1;
    }
}

/* Look for an entry by name, or (prefix set) for the first name that starts
 * with prefix. Every directory entry counts, whatever it is. Returns 1 found
 * (copied to out), 0 not found, -1 the scan failed: callers must refuse then. */
static int ws_scan(BPTR dir, const char *name, const char *prefix, char *out)
{
    struct FileInfoBlock *fib = (struct FileInfoBlock *)AllocDosObject(DOS_FIB, NULL);
    int r = 0;
    if (!fib) return -1;
    if (!Examine(dir, fib)) { FreeDosObject(DOS_FIB, fib); return -1; }
    while (ExNext(dir, fib)) {
        const char *n = (const char *)fib->fib_FileName;
        if ((name && ws_ieq(n, name)) ||
            (prefix && strncmp(n, prefix, strlen(prefix)) == 0)) {
            if (out) strcpy(out, n);
            r = 1;
            break;
        }
    }
    if (!r && IoErr() != ERROR_NO_MORE_ENTRIES) r = -1;
    FreeDosObject(DOS_FIB, fib);
    return r;
}

/* A plain name: no path of any kind, no way to be a device or a wildcard. */
static int ws_name_ok(const char *s)
{
    int i, n = (int)strlen(s);
    if (n < 1 || n > WS_MAXNAME || s[0] == '.' || s[n - 1] == '.' || s[n - 1] == ' ') return 0;
    for (i = 0; i < n; i++) {
        char c = s[i];
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') ||
              c == '.' || c == '_' || c == '-' || c == '+' || c == ' ')) return 0;
    }
    if (n >= 5 && ws_ieq(s + n - 5, ".info")) return 0;
    return 1;
}

static int ws_path_ok(const char *s)
{
    int n = 0;
    for (; *s; s++, n++)
        if ((UBYTE)*s < 32 || (UBYTE)*s > 126) return 0;
    return n >= 1 && n < WS_MAXPATH;
}

static int ws_rename(const char *from, const char *to)
{
#ifdef AMIAGENT_WS_TEST
    if (WS_HOOK("clobber")) DeleteFile((STRPTR)to);  /* a filesystem that replaces */
#endif
    return Rename((STRPTR)from, (STRPTR)to) != 0;
}

/* Make a temporary name that does not exist in dir. */
static int ws_tmpname(BPTR dir, char *out)
{
    int i;
    for (i = 0; i < 8; i++) {
        sprintf(out, WS_TMPPREFIX "%08lx", (unsigned long)(ws_now() * 7919UL + g_ws.seq * 31UL + i));
#ifdef AMIAGENT_WS_TEST
        if (WS_HOOK("tmpfix")) strcpy(out, WS_TMPPREFIX "deadbeef");
#endif
        switch (ws_scan(dir, out, NULL, NULL)) {
        case 0:  return 1;
        case -1: return 0;
        }
    }
    return 0;
}

/* Exactly what ws_tmpname() makes: the prefix plus 8 hex digits. */
static int ws_is_tmp(const char *s)
{
    int i, pl = (int)strlen(WS_TMPPREFIX);
    if ((int)strlen(s) != pl + 8 || strncmp(s, WS_TMPPREFIX, pl)) return 0;
    for (i = pl; i < pl + 8; i++)
        if (!((s[i] >= '0' && s[i] <= '9') || (s[i] >= 'a' && s[i] <= 'f'))) return 0;
    return 1;
}

/* Remove what an interrupted copy left behind: only our exact name pattern. */
static int ws_sweep(BPTR dir)
{
    BPTR old = CurrentDir(dir);
    struct FileInfoBlock *fib = (struct FileInfoBlock *)AllocDosObject(DOS_FIB, NULL);
    char list[8][32];
    int n = 0, i;
    if (fib) {
        if (Examine(dir, fib))
            while (n < 8 && ExNext(dir, fib))
                if (fib->fib_DirEntryType < 0 && ws_is_tmp((const char *)fib->fib_FileName))
                    strcpy(list[n++], (const char *)fib->fib_FileName);
        FreeDosObject(DOS_FIB, fib);
    }
    for (i = 0; i < n; i++)
        if (DeleteFile((STRPTR)list[i])) ws_log("SWEEP", list[i]);
    CurrentDir(old);
    return n;
}

/* Prove on this filesystem that Rename() refuses an existing name. */
static const char *ws_probe(BPTR dir)
{
    char a[32], b[32], rb[2];
    BPTR old, fh;
    const char *bad = NULL;
    LONG n;

    g_ws.seq++;
    if (!ws_tmpname(dir, a)) return "cannot pick a probe name";
    old = CurrentDir(dir);
    if (!(fh = Open((STRPTR)a, MODE_NEWFILE))) { CurrentDir(old); return "cannot create a probe file"; }
    Write(fh, "A", 1); Close(fh);
    g_ws.seq++;
    if (!ws_tmpname(dir, b)) { DeleteFile((STRPTR)a); CurrentDir(old); return "cannot pick a probe name"; }
    if (!(fh = Open((STRPTR)b, MODE_NEWFILE))) { DeleteFile((STRPTR)a); CurrentDir(old); return "cannot create a probe file"; }
    Write(fh, "B", 1); Close(fh);

    if (ws_rename(a, b)) bad = "Rename() replaces existing files here";
    else if (IoErr() != ERROR_OBJECT_EXISTS) bad = "Rename() gave an unexpected error";
    if ((fh = Open((STRPTR)b, MODE_OLDFILE))) {
        n = Read(fh, rb, 1);
        Close(fh);
        if (n != 1 || rb[0] != 'B') bad = "Rename() replaces existing files here";
    } else bad = "probe file disappeared";
    DeleteFile((STRPTR)a);
    DeleteFile((STRPTR)b);
    CurrentDir(old);
    return bad;
}

/* Allowed roots may not contain, sit inside or be one of these. */
static const char *ws_guard(BPTR root)
{
    static const char *const both[] = {
        "S:", "C:", "L:", "DEVS:", "LIBS:", "ENVARC:", "SYS:WBStartup", "PROGDIR:", NULL };
    int i;
    BPTR l;
    if ((l = Lock((STRPTR)"SYS:", ACCESS_READ))) {
        int inside = ws_under(l, root);
        UnLock(l);
        if (inside) return "WRITEROOT contains SYS:";
    }
    for (i = 0; both[i]; i++) {
        if ((l = Lock((STRPTR)both[i], ACCESS_READ))) {
            int bad = ws_under(l, root) || ws_under(root, l);
            UnLock(l);
            if (bad) return both[i];
        }
    }
    return NULL;
}

/* Is this lock on a block device? Network and RAM handlers call themselves
 * DOS\x too, but only a mounted disk has a FileSysStartupMsg with a device. */
static int ws_local(BPTR lock)
{
    struct MsgPort *port = ((struct FileLock *)BADDR(lock))->fl_Task;
    struct DosList *dl = LockDosList(LDF_DEVICES | LDF_READ);
    int local = 0;
    while ((dl = NextDosEntry(dl, LDF_DEVICES))) {
        if (dl->dol_Task == port) {
            ULONG st = (ULONG)dl->dol_misc.dol_handler.dol_Startup;
            if (st > 1024 && TypeOfMem(BADDR(st))) {
                struct FileSysStartupMsg *fssm = (struct FileSysStartupMsg *)BADDR(st);
                if (fssm->fssm_Device && TypeOfMem(BADDR(fssm->fssm_Device))) local = 1;
            }
            break;
        }
    }
    UnLockDosList(LDF_DEVICES | LDF_READ);
    return local;
}

/* Info(), waiting out the short ID_VALIDATING of pending FFS buffers. */
static int ws_diskinfo(BPTR lock, struct InfoData *id)
{
    int i;
    for (i = 0; i < 12; i++) {
        if (!Info(lock, id)) return 0;
        if (id->id_DiskState != ID_VALIDATING) break;
        Delay(25);
    }
    return 1;
}

/* Called from main() once, with the command line. NULL = armed. */
static const char *ws_arm(const char *root, const char *src, const char *client,
                          LONG minutes, LONG writes, LONG maxkb, const char *noread)
{
    static struct InfoData id __attribute__((aligned(4)));
    const char *why;
    char *p, list[WS_MAXPATH];
    BPTR up;

    g_ws.configured = 1;
    g_ws.closed = 1;          /* stays closed unless every check below passes */
    crc_init();
    if (!root || !src || !client || !noread) return "WRITEROOT, SRCROOT, CLIENT and NOREAD are all required";
    if (minutes < 1 || minutes > 120) return "WRITEMIN must be 1..120";
    if (writes < 1 || writes > 100) return "WRITEMAX must be 1..100";
    if (maxkb < 1 || maxkb > 4096) return "MAXKB must be 1..4096";
    if (!ws_path_ok(root) || !ws_path_ok(src) || strlen(client) >= sizeof g_ws.client) return "bad path";
    if (strlen(noread) >= sizeof list) return "NOREAD too long";
    strcpy(g_ws.rootname, root);
    strcpy(g_ws.srcroot, src);
    strcpy(g_ws.client, client);

    if (!(g_ws.root = Lock((STRPTR)root, ACCESS_READ))) return "WRITEROOT does not exist";
    if (!ws_isdir(g_ws.root)) return "WRITEROOT is not a directory";
    if (!(up = ParentDir(g_ws.root))) return "WRITEROOT is a volume root";
    UnLock(up);
    if ((why = ws_guard(g_ws.root))) return why;
    if (!ws_local(g_ws.root)) return "WRITEROOT is not on a local disk";
    if (!ws_diskinfo(g_ws.root, &id)) return "Info() failed on WRITEROOT";
    if ((id.id_DiskType & 0xFFFFFF00UL) != WS_ID('D','O','S',0) || (id.id_DiskType & 0xFF) > 7)
        return "WRITEROOT is not on a local OFS/FFS volume";
    if (id.id_DiskState != ID_VALIDATED) return "WRITEROOT volume is write protected or validating";

    /* Folders whose contents GET must not hand out in this build. */
    if ((g_ws.noread[0] = Lock((STRPTR)"PROGDIR:Prefs", ACCESS_READ))) g_ws.nnoread = 1;
    else return "PROGDIR:Prefs is missing";
    strcpy(list, noread);
    for (p = strtok(list, "|"); p && g_ws.nnoread < WS_MAXNOREAD; p = strtok(NULL, "|")) {
        BPTR l = Lock((STRPTR)p, ACCESS_READ);
        if (!l) return "a NOREAD folder does not exist";
        g_ws.noread[g_ws.nnoread++] = l;
    }

    g_ws.start = ws_now();
    if (!ws_log("ARM", root)) return "cannot write " WS_LOG;
    ws_sweep(g_ws.root);
#ifdef AMIAGENT_WS_TEST
    if (!WS_HOOK("noprobe"))
#endif
    if ((why = ws_probe(g_ws.root))) { ws_log("ARMFAIL", why); return why; }

    g_ws.deadline = g_ws.start + minutes * 60L;
    g_ws.writes_left = writes;
    g_ws.maxbytes = (ULONG)maxkb * 1024UL;
    g_ws.closed = 0;
    ws_log("ARMED", client);
    return NULL;
}

static void ws_shutdown(void)
{
    int i;
    if (g_ws.configured && !g_ws.closed) ws_log("DISARM", "agent stopped");
    g_ws.closed = 1;
    if (g_ws.root) { UnLock(g_ws.root); g_ws.root = 0; }
    for (i = 0; i < g_ws.nnoread; i++) UnLock(g_ws.noread[i]);
    g_ws.nnoread = 0;
}

/* Closes for good when the window has passed, also if the clock runs back. */
static int ws_open(void)
{
    LONG now;
    if (!g_ws.configured || g_ws.closed) return 0;
    now = ws_now();
    if (now < g_ws.start || now >= g_ws.deadline || g_ws.writes_left <= 0) {
        g_ws.closed = 1;
        ws_log("EXPIRED", "");
        return 0;
    }
    return 1;
}

static int ws_noread(BPTR lock)
{
    int i;
    for (i = 0; i < g_ws.nnoread; i++)
        if (ws_under(lock, g_ws.noread[i])) return 1;
    return 0;
}

/* Extra INFO lines. */
static int ws_info(struct buf *b)
{
    char line[WS_MAXPATH + 40];
    int ok = 1, open = ws_open();
    sprintf(line, "write=%s\n", open ? "armed" : g_ws.configured ? "closed" : "off"); ok &= buf_str(b, line);
    if (open) {
        sprintf(line, "write_root=%s\n", g_ws.rootname); ok &= buf_str(b, line);
        sprintf(line, "write_seconds_left=%ld\n", (long)(g_ws.deadline - ws_now())); ok &= buf_str(b, line);
        sprintf(line, "write_count_left=%ld\n", (long)g_ws.writes_left); ok &= buf_str(b, line);
        sprintf(line, "write_max_bytes=%lu\n", (unsigned long)g_ws.maxbytes); ok &= buf_str(b, line);
    }
    return ok;
}

/* Blocks a file of size bytes needs, plus a reserve. */
static ULONG ws_blocks(ULONG size, const struct InfoData *id)
{
    ULONG bpb = (ULONG)id->id_BytesPerBlock;
    ULONG data = id->id_DiskType == WS_ID('D','O','S',0) ? bpb - 24 : bpb;
    ULONG n = size / data + 1;
    ULONG perext = bpb / 4 - 56;
    return n + n / perext + 2 + (WS_RESERVEKB * 1024UL) / bpb;
}

static int ws_client_gone(int sock)
{
    char c;
    if (sock_readable(sock, 0) != 1) return 0;
    return recv(sock, &c, 1, 0) <= 0;
}

/* Everything COPYIN holds, so one exit path can release it. */
struct ws_job {
    BPTR src, dstdir, tdir, old;   /* old: saved CurrentDir, valid when entered */
    BPTR in, out;
    int entered;
    char tmp[32];
};

static int ws_err(int sock, struct ws_job *j, const char *code, const char *detail)
{
    char msg[WS_MAXPATH + 60];
    LONG e = IoErr();
    if (j->out) { Close(j->out); j->out = 0; }
    if (j->in)  { Close(j->in);  j->in = 0; }
    if (j->tmp[0]) {
        if (!DeleteFile((STRPTR)j->tmp)) {
            ws_log("TMPLEFT", j->tmp);
            code = "TMPLEFT";
        }
        j->tmp[0] = 0;
    }
    if (j->entered) { CurrentDir(j->old); j->entered = 0; }
    if (j->tdir && j->tdir != j->dstdir) UnLock(j->tdir);
    if (j->src)    UnLock(j->src);
    if (j->dstdir) UnLock(j->dstdir);
    sprintf(msg, "WS:%s %.200s (DOS error %ld)", code, detail, (long)e);
    ws_log("FAIL", msg);
    return send_err(sock, msg);
}

static int do_copyin(int sock, const UBYTE *body, ULONG len, const char *client)
{
    static struct InfoData id __attribute__((aligned(4)));
    struct ws_job j;
    const char *srcname, *dstdir, *name, *end;
    UBYTE flags;
    ULONG size, crc, c, left, need, freeb;
    BPTR srcroot;
    char line[WS_MAXPATH + 100];
    LONG n, sig;
    struct FileInfoBlock *fib;
    int r;

    memset(&j, 0, sizeof j);
    if (len < 12 || body[len - 1] != 0) return send_err(sock, "WS:PROTO malformed COPYIN");
    flags = body[0];
    size = get_be32(body + 1);
    crc = get_be32(body + 5);
    srcname = (const char *)body + 9;
    end = (const char *)body + len;
    dstdir = srcname + strlen(srcname) + 1;
    if (dstdir >= end) return send_err(sock, "WS:PROTO malformed COPYIN");
    name = dstdir + strlen(dstdir) + 1;
    if (name >= end || name + strlen(name) + 1 != end) return send_err(sock, "WS:PROTO malformed COPYIN");

    if (!ws_open()) return send_err(sock, "WS:NOT_ARMED no open write mandate on this Amiga");
    if (strcmp(client, g_ws.client)) {
        ws_log("REFUSED", client);
        return send_err(sock, "WS:CLIENT this client address is not in the mandate");
    }
    if (!ws_name_ok(name) || !ws_name_ok(srcname) || !ws_path_ok(dstdir)) {
        ws_log("REFUSED", "bad name");
        return send_err(sock, "WS:PATH bad file name or folder");
    }
    if (size == 0 || size > g_ws.maxbytes) {
        ws_log("REFUSED", "size");
        return send_err(sock, "WS:SIZE file is empty or above MAXKB");
    }

    /* Destination: by lock, inside the root, a folder. */
    if (!(j.dstdir = Lock((STRPTR)dstdir, ACCESS_READ))) {
        ws_log("REFUSED", dstdir);
        return ws_err(sock, &j, "PATH", dstdir);
    }
    if (!ws_isdir(j.dstdir) || !ws_under(j.dstdir, g_ws.root)) {
        ws_log("REFUSED", dstdir);
        return ws_err(sock, &j, "PATH", "folder is outside WRITEROOT");
    }

    /* Source: a plain name, directly in the share folder, a real file. */
    if (!(srcroot = Lock((STRPTR)g_ws.srcroot, ACCESS_READ)))
        return ws_err(sock, &j, "SOURCE", "share folder not available");
    {
        BPTR old = CurrentDir(srcroot);
        j.src = Lock((STRPTR)srcname, ACCESS_READ);
        CurrentDir(old);
    }
    if (!j.src) { UnLock(srcroot); return ws_err(sock, &j, "SOURCE", srcname); }
    r = ws_under(j.src, srcroot);
    UnLock(srcroot);
    if (!r) return ws_err(sock, &j, "SOURCE", "source is outside SRCROOT");
    if (((struct FileLock *)BADDR(j.src))->fl_Task == ((struct FileLock *)BADDR(g_ws.root))->fl_Task)
        return ws_err(sock, &j, "SOURCE", "source is on the same volume as WRITEROOT");
    if (!(fib = (struct FileInfoBlock *)AllocDosObject(DOS_FIB, NULL)))
        return ws_err(sock, &j, "MEMORY", "");
    if (!Examine(j.src, fib) || fib->fib_DirEntryType >= 0 || (ULONG)fib->fib_Size != size) {
        FreeDosObject(DOS_FIB, fib);
        return ws_err(sock, &j, "SOURCE", "not a file of the announced size");
    }
    FreeDosObject(DOS_FIB, fib);

    /* Not there yet, in any form. */
#ifdef AMIAGENT_WS_TEST
    r = WS_HOOK("noscan") ? 0 : ws_scan(j.dstdir, name, NULL, NULL);
#else
    r = ws_scan(j.dstdir, name, NULL, NULL);
#endif
    if (r) return ws_err(sock, &j, r > 0 ? "EXISTS" : "SCAN", name);

    /* Space. */
    if (!ws_diskinfo(j.dstdir, &id)) return ws_err(sock, &j, "SPACE", "Info() failed");
    if (id.id_DiskState != ID_VALIDATED) return ws_err(sock, &j, "SPACE", "volume is write protected or validating");
    need = ws_blocks(size, &id);
    freeb = (ULONG)id.id_NumBlocks - (ULONG)id.id_NumBlocksUsed;
#ifdef AMIAGENT_WS_TEST
    if (!WS_HOOK("nospace"))
#endif
    if (need > freeb) return ws_err(sock, &j, "SPACE", "not enough free blocks");

    if (flags & WS_F_CHECK) {
        sprintf(line, "check=ok\nfree_blocks=%lu\nneed_blocks=%lu\n", (unsigned long)freeb, (unsigned long)need);
        UnLock(j.src); UnLock(j.dstdir);
        return send_resp(sock, ST_OK, line, (ULONG)strlen(line));
    }

    /* From here on it counts as a write, whatever the outcome. */
    g_ws.seq++;
    g_ws.writes_left--;
    sprintf(line, "%s -> %s/%s size=%lu crc=%08lx", srcname, dstdir, name, (unsigned long)size, (unsigned long)crc);
    if (!ws_log("START", line)) return ws_err(sock, &j, "LOG", "cannot write the log");

    if (!ws_tmpname(j.dstdir, j.tmp)) { j.tmp[0] = 0; return ws_err(sock, &j, "SCAN", "no temporary name"); }
    j.tdir = j.dstdir;
#ifdef AMIAGENT_WS_TEST
    if (WS_HOOK("tmpoutside")) j.tdir = ParentDir(g_ws.root);
#endif
    j.old = CurrentDir(j.tdir);
    j.entered = 1;

    if (!(j.in = OpenFromLock(j.src))) {
        j.tmp[0] = 0;
        return ws_err(sock, &j, "SOURCE", "cannot open source");
    }
    j.src = 0;                 /* now owned by j.in */
    if (!(j.out = Open((STRPTR)j.tmp, MODE_NEWFILE))) {
        char t[32]; strcpy(t, j.tmp); j.tmp[0] = 0;
        return ws_err(sock, &j, "IO", t);
    }
    /* The temporary file must really sit where it should. */
    {
        BPTR pl = ParentOfFH(j.out);
        int inroot = pl && SameLock(pl, j.dstdir) == LOCK_SAME && ws_under(pl, g_ws.root);
        if (pl) UnLock(pl);
        if (!inroot) return ws_err(sock, &j, "TMPPATH", "temporary file is outside the target folder");
    }

    c = 0xFFFFFFFFUL;
    for (left = size; left; left -= (ULONG)n) {
        LONG want = left > IOBUF ? IOBUF : (LONG)left;
        sig = (LONG)SetSignal(0, 0);
        if (sig & SIGBREAKF_CTRL_C) {
            g_ws.closed = 1;
            ws_err(sock, &j, "ABORT", "Ctrl-C");
            return 0;          /* the signal stays set: the main loop stops next */
        }
        if (ws_client_gone(sock)) return ws_err(sock, &j, "ABORT", "client went away");
        n = Read(j.in, g_io, want);
        if (n <= 0) return ws_err(sock, &j, "IOSRC", "share read failed or file got shorter");
        c = crc_add(c, g_io, n);
#ifdef AMIAGENT_WS_TEST
        if (ws_hookval("slow")) Delay(ws_hookval("slow"));
        if (WS_HOOK("badcrc")) g_io[0] ^= 1;
#endif
        if (Write(j.out, g_io, n) != n) return ws_err(sock, &j, "IODST", "write failed (disk full?)");
    }
    if (Read(j.in, g_io, 1) != 0) return ws_err(sock, &j, "IOSRC", "file got longer");
    Close(j.in); j.in = 0;
    {
        LONG ok = Close(j.out);
        j.out = 0;
        if (!ok) return ws_err(sock, &j, "IODST", "close failed (disk full?)");
    }
    if ((c ^ 0xFFFFFFFFUL) != crc) return ws_err(sock, &j, "CRC", "share data differs from the announced CRC");

    /* Read back what is on the local disk. */
    if (!(j.in = Open((STRPTR)j.tmp, MODE_OLDFILE))) return ws_err(sock, &j, "IODST", "cannot reopen temporary file");
    c = 0xFFFFFFFFUL;
    left = 0;
    while ((n = Read(j.in, g_io, IOBUF)) > 0) { c = crc_add(c, g_io, n); left += (ULONG)n; }
    Close(j.in); j.in = 0;
    if (n < 0 || left != size || (c ^ 0xFFFFFFFFUL) != crc)
        return ws_err(sock, &j, "CRC", "read-back differs");

#ifdef AMIAGENT_WS_TEST
    if (ws_hookval("pause")) Delay(ws_hookval("pause"));
    r = WS_HOOK("noscan") ? 0 : ws_scan(j.dstdir, name, NULL, NULL);
#else
    r = ws_scan(j.dstdir, name, NULL, NULL);
#endif
    if (r) return ws_err(sock, &j, r > 0 ? "EXISTS" : "SCAN", name);
    if (!ws_rename(j.tmp, name)) return ws_err(sock, &j, "EXISTS", name);
    j.tmp[0] = 0;

    CurrentDir(j.old); j.entered = 0;
    if (j.tdir != j.dstdir) UnLock(j.tdir);
    UnLock(j.dstdir);
    sprintf(line, "%s/%s size=%lu crc=%08lx", dstdir, name, (unsigned long)size, (unsigned long)crc);
    r = ws_log("OK", line);
    sprintf(line, "result=ok\nsize=%lu\ncrc=%08lx\ncount_left=%ld\nlogged=%d\n",
            (unsigned long)size, (unsigned long)crc, (long)g_ws.writes_left, r);
    return send_resp(sock, ST_OK, line, (ULONG)strlen(line));
}
