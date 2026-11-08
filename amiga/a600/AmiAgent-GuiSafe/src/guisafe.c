/* guisafe.c - LSN 0005: GUI-SAFE (The Love Shack Network). PROTOTYPE, emulator only.
 *
 * Included by amiagent.c, only in the AMIAGENT_GUISAFE build (always together with
 * AMIAGENT_READONLY). Everything the READONLY build refuses stays refused, except:
 *   - LAUNCH (0x41): start the ONE program of this session. Program, folder and name
 *     come from a local allowlist file read once at start; the client sends nothing
 *     but the code. The agent itself does LoadSeg + CreateNewProc: no shell, no
 *     Execute, no client text in any command line.
 *   - INPUT (0x08): keyboard, text and mouse, but every single event passes gs_gate()
 *     right before it is posted to input.device (see there).
 *   - GSEND (0x42): the client ends the session.
 * PUT, AREXX, UIACT, BREAK and free EXEC stay refused.
 *
 * The mandate is local and single-use, exactly like WRITE-SAFE: it exists only as
 * arguments of this process, given by a script somebody started at the machine,
 * lives in RAM, cannot be extended over the network, and once closed it stays closed.
 *
 * Write isolation (preventive): at arming time every local volume named in PROTECT
 * is write-protected through its own filesystem (ACTION_WRITE_PROTECT, random key),
 * and a probe proves that creating a file there now fails. Every mounted volume must
 * be in PROTECT or in EXEMPT, otherwise the mandate is refused (fail closed). Exempt
 * volumes (RAM Disk, the network share) must be isolated elsewhere (share: server-side
 * permissions). The protection is lifted only when the session is over AND the
 * program has exited, or when the user stops the agent locally (Ctrl-C).
 *
 * Detection only (not prevention): NOTIFY tripwire on named folders.
 */
#include <dos/notify.h>
#include <graphics/clip.h>
#include <graphics/layers.h>
#include <proto/layers.h>

#define CMD_LAUNCH  0x41
#define CMD_GSEND   0x42
#define GS_MAXPATH  200
#define GS_MAXVOL   8
#define GS_MAXNOTE  6
#define GS_RAMLOG   "RAM:AmiAgent-gs.log"
#define GS_LOG      "PROGDIR:Log/gui.log"

static int gs_ieq(const char *a, const char *b)
{
    for (;; a++, b++) {
        char x = *a, y = *b;
        if (x >= 'a' && x <= 'z') x -= 32;
        if (y >= 'a' && y <= 'z') y -= 32;
        if (x != y) return 0;
        if (!x) return 1;
    }
}

struct Library *LayersBase = NULL;

static struct {
    int armed, closed;
    char why[64];
    char app[32], prog[GS_MAXPATH], dir[GS_MAXPATH], testdir[GS_MAXPATH], client[32];
    LONG start, deadline, idle_until, idlesec;
    LONG actions_left, launches_left;
    struct Task *self;
    struct Process *proc;          /* the session program, NULL when not running */
    volatile LONG app_running;
    int app_had_window, focus_bad;
    int in_text, refused;
    char refusemsg[96];
    struct { struct MsgPort *port; char name[32]; LONG key; int on; } vol[GS_MAXVOL];
    int nvol;
    struct NotifyRequest nr[GS_MAXNOTE];
    char nname[GS_MAXNOTE][GS_MAXPATH];
    int nnote;
    BYTE nsig;
} g_gs;

static LONG gs_now(void)
{
    struct DateStamp ds;
    DateStamp(&ds);
    return (ds.ds_Days * 1440L + ds.ds_Minute) * 60L + ds.ds_Tick / TICKS_PER_SECOND;
}

/* Log lines go to RAM while volumes are protected; at shutdown they are appended
 * to PROGDIR:Log/gui.log once that volume is writable again. */
static void gs_log(const char *what, const char *detail)
{
    char line[GS_MAXPATH + 120], ts[24];
    BPTR fh;
    ts_now(ts, sizeof ts);
    sprintf(line, "%s %s %.150s\n", ts, what, detail ? detail : "");
    fh = Open((STRPTR)GS_RAMLOG, MODE_READWRITE);
    if (!fh) return;
    Seek(fh, 0, OFFSET_END);
    Write(fh, line, (LONG)strlen(line));
    Close(fh);
}

static void gs_close(const char *why)
{
    if (g_gs.closed) return;
    g_gs.closed = 1;
    strncpy(g_gs.why, why, sizeof g_gs.why - 1);
    gs_log("SESSIE-DICHT", why);
    note("amiagent-gs: session closed: %s\n", why);
}

/* ---- allowlist: lines "WORD|program|current folder"; '#' comments ---- */
static int gs_allow(const char *file, const char *word)
{
    BPTR fh = Open((STRPTR)file, MODE_OLDFILE);
    char line[2 * GS_MAXPATH + 40];
    int found = 0;
    if (!fh) return 0;
    while (FGets(fh, line, sizeof line - 1)) {
        char *a, *b, *nl;
        if (line[0] == '#' || line[0] == '\n') continue;
        if ((nl = strchr(line, '\n'))) *nl = 0;
        a = strchr(line, '|'); if (!a) continue; *a++ = 0;
        b = strchr(a, '|');    if (!b) continue; *b++ = 0;
        if (!gs_ieq(line, word)) continue;
        if (strlen(a) >= GS_MAXPATH || strlen(b) >= GS_MAXPATH) break;
        strcpy(g_gs.prog, a); strcpy(g_gs.dir, b);
        found = 1; break;
    }
    Close(fh);
    return found;
}

/* ---- write isolation ---- */
static int gs_listed(const char *list, const char *name)
{
    char buf[GS_MAXPATH], *t, *s;
    if (!list) return 0;
    strncpy(buf, list, sizeof buf - 1); buf[sizeof buf - 1] = 0;
    for (s = buf; s; s = t) {
        if ((t = strchr(s, ','))) *t++ = 0;
        if (*s && gs_ieq(s, name)) return 1;
    }
    return 0;
}

/* Every mounted volume must be named in PROTECT or EXEMPT. */
static const char *gs_volcheck(const char *protect, const char *exempt, char *bad)
{
    struct DosList *dl = LockDosList(LDF_VOLUMES | LDF_READ);
    const char *why = NULL;
    while ((dl = NextDosEntry(dl, LDF_VOLUMES))) {
        UBYTE *b = (UBYTE *)BADDR(dl->dol_Name);
        char name[32];
        int n = b ? b[0] : 0;
        if (n > 30) n = 30;
        if (b) memcpy(name, b + 1, n);
        name[n] = 0;
        if (!gs_listed(protect, name) && !gs_listed(exempt, name)) {
            strcpy(bad, name); why = "a mounted volume is neither in PROTECT nor in EXEMPT"; break;
        }
    }
    UnLockDosList(LDF_VOLUMES | LDF_READ);
    return why;
}

static const char *gs_protect(const char *protect)
{
    char buf[GS_MAXPATH], *t, *s, path[40];
    strncpy(buf, protect, sizeof buf - 1); buf[sizeof buf - 1] = 0;
    for (s = buf; s && *s; s = t) {
        struct DevProc *dp;
        BPTR fh;
        LONG key;
        if ((t = strchr(s, ','))) *t++ = 0;
        if (g_gs.nvol >= GS_MAXVOL || strlen(s) > 28) return "too many or too long PROTECT entries";
        sprintf(path, "%s:", s);
        dp = GetDeviceProc((STRPTR)path, NULL);
        if (!dp) return "a PROTECT volume is not mounted";
        g_gs.vol[g_gs.nvol].port = dp->dvp_Port;
        FreeDeviceProc(dp);
        key = (LONG)((gs_now() * 2654435761UL) ^ (ULONG)FindTask(NULL) ^ ((ULONG)g_gs.nvol << 24) ^ 0x5A17C0DEUL);
        if (!key) key = 0x1234567;
        strcpy(g_gs.vol[g_gs.nvol].name, s);
        g_gs.vol[g_gs.nvol].key = key;
        if (!DoPkt(g_gs.vol[g_gs.nvol].port, ACTION_WRITE_PROTECT, DOSTRUE, key, 0, 0, 0))
            return "filesystem refused ACTION_WRITE_PROTECT";
        g_gs.vol[g_gs.nvol].on = 1;
        g_gs.nvol++;
        /* live probe: creating a file must now fail */
        sprintf(path, "%s:.gs-probe", s);
        fh = Open((STRPTR)path, MODE_NEWFILE);
        if (fh) { Close(fh); DeleteFile((STRPTR)path); return "probe could still write after write-protect"; }
        gs_log("BESCHERMD", s);
    }
    return NULL;
}

static void gs_unprotect(void)
{
    int i;
    for (i = 0; i < g_gs.nvol; i++) if (g_gs.vol[i].on) {
        if (DoPkt(g_gs.vol[i].port, ACTION_WRITE_PROTECT, DOSFALSE, g_gs.vol[i].key, 0, 0, 0)) {
            g_gs.vol[i].on = 0;
            gs_log("VRIJGEGEVEN", g_gs.vol[i].name);
        } else gs_log("VRIJGEVEN-MISLUKT", g_gs.vol[i].name);
    }
}

/* ---- tripwire (detection only) ---- */
static void gs_notify(const char *list)
{
    char buf[GS_MAXPATH * 2], *t, *s;
    if (!list) return;
    g_gs.nsig = AllocSignal(-1);
    if (g_gs.nsig < 0) { gs_log("TRIPWIRE", "geen signaal vrij"); return; }
    strncpy(buf, list, sizeof buf - 1); buf[sizeof buf - 1] = 0;
    for (s = buf; s && *s && g_gs.nnote < GS_MAXNOTE; s = t) {
        struct NotifyRequest *nr = &g_gs.nr[g_gs.nnote];
        if ((t = strchr(s, ','))) *t++ = 0;
        strncpy(g_gs.nname[g_gs.nnote], s, GS_MAXPATH - 1);
        memset(nr, 0, sizeof *nr);
        nr->nr_Name = (STRPTR)g_gs.nname[g_gs.nnote];
        nr->nr_Flags = NRF_SEND_SIGNAL;
        nr->nr_stuff.nr_Signal.nr_Task = g_gs.self;
        nr->nr_stuff.nr_Signal.nr_SignalNum = g_gs.nsig;
        if (StartNotify(nr)) { g_gs.nnote++; gs_log("TRIPWIRE-AAN", s); }
        else gs_log("TRIPWIRE-NIET-MOGELIJK", s);
    }
}

/* ---- mandate file: KEY=VALUE lines (local, protection r); command-line values win ---- */
static char g_mf[10][GS_MAXPATH];
static const char *g_mkeys[10] = { "ALLOW", "TESTDIR", "CLIENT", "GUIMIN", "GUIMAX", "IDLESEC",
                                   "PROTECT", "EXEMPT", "NOTIFY", "APP" };
static int gs_mandate_file(const char *file)
{
    BPTR fh = Open((STRPTR)file, MODE_OLDFILE);
    char line[GS_MAXPATH + 20];
    if (!fh) return 0;
    while (FGets(fh, line, sizeof line - 1)) {
        char *eq, *nl; int i;
        if (line[0] == '#' || line[0] == '\n') continue;
        if ((nl = strchr(line, '\n'))) *nl = 0;
        if (!(eq = strchr(line, '='))) continue;
        *eq++ = 0;
        for (i = 0; i < 10; i++)
            if (gs_ieq(line, g_mkeys[i]) && strlen(eq) < GS_MAXPATH) strcpy(g_mf[i], eq);
    }
    Close(fh);
    return 1;
}
static const char *gs_mv(const char *cmdline, int i) { return cmdline ? cmdline : (g_mf[i][0] ? g_mf[i] : NULL); }
static LONG gs_mn(LONG *cmdline, int i, LONG dflt) { return cmdline ? *cmdline : (g_mf[i][0] ? atol(g_mf[i]) : dflt); }

/* ---- arming ---- */
static const char *gs_arm(const char *app, const char *allow, const char *testdir, const char *client,
                          LONG minutes, LONG actions, LONG idlesec, const char *protect,
                          const char *exempt, const char *notify)
{
    static char bad[40], whybuf[120];
    const char *why;
    g_gs.closed = 1;                      /* stays closed unless every check passes */
    g_gs.self = FindTask(NULL);
    g_gs.nsig = -1;
    DeleteFile((STRPTR)GS_RAMLOG);
    if (!app || !allow || !testdir || !client || !protect) return "APP, ALLOW, TESTDIR, CLIENT and PROTECT are required";
    if (minutes < 1 || minutes > 30) return "GUIMIN must be 1..30";
    if (actions < 1 || actions > 500) return "GUIMAX must be 1..500";
    if (idlesec < 10 || idlesec > 600) return "IDLESEC must be 10..600";
    if (strlen(app) >= sizeof g_gs.app || strlen(testdir) >= GS_MAXPATH || strlen(client) >= sizeof g_gs.client)
        return "argument too long";
    if (!strchr(testdir, ':') || strstr(testdir, "//")) return "TESTDIR must be an absolute path";
    if (!gs_allow(allow, app)) return "APP is not in the local allowlist";
    {   /* the allowlist file itself must not be writable by a later request: it is read once, here */
        BPTR l = Lock((STRPTR)g_gs.prog, ACCESS_READ);
        if (!l) return "program from the allowlist not found";
        UnLock(l);
        l = Lock((STRPTR)testdir, ACCESS_READ);
        if (!l) return "TESTDIR not found";
        UnLock(l);
    }
    LayersBase = OpenLibrary((STRPTR)"layers.library", 37);
    if (!LayersBase) return "layers.library";
    if ((why = gs_volcheck(protect, exempt, bad))) { sprintf(whybuf, "%s: %s", why, bad); return whybuf; }
    strcpy(g_gs.app, app); strcpy(g_gs.testdir, testdir); strcpy(g_gs.client, client);
    gs_log("MANDAAT", app);
    gs_log("ALLOW", g_gs.prog);
    gs_log("TESTDIR", testdir);
    if ((why = gs_protect(protect))) { gs_unprotect(); return why; }
    gs_notify(notify);
    g_gs.start = gs_now();
    g_gs.deadline = g_gs.start + minutes * 60L;
    g_gs.idlesec = idlesec;
    g_gs.idle_until = g_gs.start + idlesec;
    g_gs.actions_left = actions;
    g_gs.launches_left = 3;
    g_gs.armed = 1;
    g_gs.closed = 0;
    note("amiagent-gs: GUI-SAFE open: %s, %ld min, %ld actions, client %s\n", app, minutes, actions, client);
    return NULL;
}

static int gs_app_running(void) { return g_gs.proc && g_gs.app_running; }

static void gs_shutdown(void)
{
    int i;
    for (i = 0; i < g_gs.nnote; i++) EndNotify(&g_gs.nr[i]);
    g_gs.nnote = 0;
    if (g_gs.nsig >= 0) { FreeSignal(g_gs.nsig); g_gs.nsig = -1; }
    gs_close("agent stopt");
    gs_unprotect();
    {   /* RAM log -> persistent log, now that volumes are writable again */
        BPTR in = Open((STRPTR)GS_RAMLOG, MODE_OLDFILE), out;
        if (in) {
            out = Open((STRPTR)GS_LOG, MODE_READWRITE);
            if (out) {
                char b[256]; LONG n;
                Seek(out, 0, OFFSET_END);
                while ((n = Read(in, b, sizeof b)) > 0) Write(out, b, n);
                Close(out);
            }
            Close(in);
        }
    }
    if (LayersBase) { CloseLibrary(LayersBase); LayersBase = NULL; }
}

/* ---- the session program ---- */
static void gs_exitcode(void)
{
    /* runs in the child's context just before it is gone */
    g_gs.app_running = 0;
    Signal(g_gs.self, SIGBREAKF_CTRL_F);
}

static int do_launch(int sock)
{
    BPTR seg, dir, home, in, out;
    struct Process *p;
    char msg[80];
    if (g_gs.closed) return send_err(sock, "GUI-SAFE: session closed");
    if (gs_app_running()) return send_err(sock, "GUI-SAFE: the program is already running (one per session)");
    if (g_gs.launches_left <= 0) return send_err(sock, "GUI-SAFE: launch limit reached");
    if (--g_gs.actions_left < 0) { gs_close("actielimiet"); return send_err(sock, "GUI-SAFE: action limit"); }
    seg = LoadSeg((STRPTR)g_gs.prog);
    if (!seg) return send_err(sock, "GUI-SAFE: LoadSeg failed");
    dir = Lock((STRPTR)g_gs.dir, ACCESS_READ);
    home = dir ? DupLock(dir) : 0;
    in = Open((STRPTR)"NIL:", MODE_OLDFILE);
    out = Open((STRPTR)"NIL:", MODE_NEWFILE);
    if (!dir || !home || !in || !out) {
        if (dir) UnLock(dir); if (home) UnLock(home); if (in) Close(in); if (out) Close(out);
        UnLoadSeg(seg);
        return send_err(sock, "GUI-SAFE: cannot prepare the process");
    }
    g_gs.app_running = 1; g_gs.app_had_window = 0; g_gs.focus_bad = 0;
    p = CreateNewProcTags(NP_Seglist, (ULONG)seg, NP_FreeSeglist, TRUE,
                          NP_Name, (ULONG)g_gs.app, NP_CommandName, (ULONG)g_gs.app,
                          NP_CurrentDir, (ULONG)dir, NP_HomeDir, (ULONG)home,
                          NP_Input, (ULONG)in, NP_Output, (ULONG)out,
                          NP_CloseInput, TRUE, NP_CloseOutput, TRUE,
                          NP_Cli, TRUE, NP_Arguments, (ULONG)"\n",
                          NP_StackSize, 16384, NP_ExitCode, (ULONG)gs_exitcode,
                          TAG_DONE);
    if (!p) {
        g_gs.app_running = 0;
        UnLock(dir); UnLock(home); Close(in); Close(out); UnLoadSeg(seg);
        return send_err(sock, "GUI-SAFE: CreateNewProc failed");
    }
    g_gs.proc = p;
    g_gs.launches_left--;
    gs_log("LAUNCH", g_gs.prog);
    sprintf(msg, "launched %.30s", g_gs.app);
    return send_resp(sock, ST_OK, msg, (ULONG)strlen(msg));
}

/* ---- the gate: one decision per input event, right before it is posted ---- */
static int gs_win_ok(struct Window *w)
{
    return w && w->UserPort && g_gs.proc && w->UserPort->mp_SigTask == (struct Task *)g_gs.proc;
}

static void input_post(struct InputEvent *ie);
static void gs_release_all(void)
{
    static const UWORD codes[] = { IECODE_LBUTTON, IECODE_RBUTTON, IECODE_MBUTTON };
    struct InputEvent ie;
    int i;
    for (i = 0; i < 3; i++) {
        memset(&ie, 0, sizeof ie);
        ie.ie_Class = IECLASS_RAWMOUSE;
        ie.ie_Code = codes[i] | IECODE_UP_PREFIX;
        input_post(&ie);
    }
}

static void gs_refuse(const char *why)
{
    int first = !g_gs.refused;
    g_gs.refused = 1;
    strncpy(g_gs.refusemsg, why, sizeof g_gs.refusemsg - 1);
    gs_log("GEWEIGERD", why);
    gs_close(why);                         /* every violation ends the session (fail safe) */
    if (first && g_inreq) gs_release_all(); /* a refused SCRIPT may have pressed a button */
}

/* returns 1 = do NOT post this event */
static int gs_gate(struct InputEvent *ie)
{
    UWORD code = ie->ie_Code, q = ie->ie_Qualifier;
    int ok;
    /* releases and plain motion are always allowed, so nothing is ever left held down */
    if (ie->ie_Class == IECLASS_POINTERPOS) return 0;
    if (ie->ie_Class == IECLASS_RAWMOUSE && (code == IECODE_NOBUTTON || (code & IECODE_UP_PREFIX))) return 0;
    if (ie->ie_Class == IECLASS_RAWKEY && (code & IECODE_UP_PREFIX)) return 0;
    if (g_gs.refused) return 1;            /* the rest of this request is dropped */
    if (g_gs.closed || !gs_app_running()) {
        gs_refuse(g_gs.closed ? "session closed" : "program not running");
        return 1;
    }
    switch (ie->ie_Class) {
    case IECLASS_POINTERPOS:
        return 0;
    case IECLASS_RAWMOUSE:
        if (code == IECODE_NOBUTTON || (code & IECODE_UP_PREFIX)) return 0;
        Forbid();
        if (code == IECODE_RBUTTON) {
            ok = gs_win_ok(IntuitionBase->ActiveWindow);       /* menus of the active window */
        } else {
            struct Screen *s = IntuitionBase->FirstScreen;
            struct Layer *l = s ? WhichLayer(&s->LayerInfo, s->MouseX, s->MouseY) : NULL;
            ok = l && gs_win_ok(l->Window);                    /* window under the pointer */
        }
        Permit();
        if (!ok) { gs_refuse(code == IECODE_RBUTTON ? "menu: active window is not the program"
                                                    : "click: not on a window of the program"); return 1; }
        return 0;
    case IECLASS_RAWKEY:
        if (code & IECODE_UP_PREFIX) return 0;
        if ((q & IEQUALIFIER_LCOMMAND) && (q & IEQUALIFIER_RCOMMAND)) { gs_refuse("key: both Amiga keys"); return 1; }
        if ((q & IEQUALIFIER_LCOMMAND) && code != 0x34 && code != 0x35) { gs_refuse("key: left-Amiga combination"); return 1; }
        if (code == 0x66) { gs_refuse("key: left-Amiga key"); return 1; }
        if (!g_gs.in_text && code < 0x40 && !(q & IEQUALIFIER_RCOMMAND) && !(q & IEQUALIFIER_LCOMMAND)) {
            gs_refuse("key: printable keys only through TEXT"); return 1;
        }
        Forbid();
        ok = gs_win_ok(IntuitionBase->ActiveWindow);
        Permit();
        if (!ok) { gs_refuse("key: active window is not the program"); return 1; }
        return 0;
    default:
        gs_refuse("input class not allowed");
        return 1;
    }
}

/* TEXT may name a path only inside TESTDIR (prevents typing other volumes or parents
 * into a file requester; mouse navigation in a requester is not covered here: that is
 * what the volume write-protect is for). */
static int gs_text_ok(const UBYTE *p, ULONG len)
{
    ULONG i, colon = 0, slash = 0, tl = (ULONG)strlen(g_gs.testdir);
    for (i = 0; i < len; i++) { if (p[i] == ':') colon++; if (p[i] == '/') slash++; }
    if (!colon && !slash) return 1;
    if (colon != 1 || len < tl) return 0;
    for (i = 0; i < tl; i++) {
        UBYTE a = p[i], b = (UBYTE)g_gs.testdir[i];
        if (a >= 'a' && a <= 'z') a -= 32;
        if (b >= 'a' && b <= 'z') b -= 32;
        if (a != b) return 0;
    }
    for (i = 0; i + 1 < len; i++) if (p[i] == '/' && p[i + 1] == '/') return 0;
    if (len > tl && g_gs.testdir[tl - 1] != '/' && g_gs.testdir[tl - 1] != ':' && p[tl] != '/') return 0;
    return 1;
}

/* called for every authenticated request: keeps the idle timer alive and decides
 * whether INPUT may pass the READONLY wall at all */
static void gs_touch(void) { if (!g_gs.closed) g_gs.idle_until = gs_now() + g_gs.idlesec; }

static int gs_input_ok(void)
{
    if (g_gs.closed || !gs_app_running()) return 0;
    if (--g_gs.actions_left < 0) { gs_close("actielimiet"); return 0; }
    return 1;
}

static int gs_scan_windows(void)
{
    struct Screen *s; struct Window *w; int seen = 0;
    Forbid();
    for (s = IntuitionBase->FirstScreen; s; s = s->NextScreen)
        for (w = s->FirstWindow; w; w = w->NextWindow) if (gs_win_ok(w)) seen = 1;
    Permit();
    return seen;
}

/* main loop, every ~2 s. Returns 1 when the agent must exit. */
static int gs_tick(void)
{
    LONG now = gs_now();
    ULONG sigs = SetSignal(0, (g_gs.nsig >= 0 ? (1UL << g_gs.nsig) : 0) | SIGBREAKF_CTRL_F);
    if (!g_gs.armed) return 0;
    if (g_gs.proc && !g_gs.app_running) { gs_log("PROGRAMMA-AFGESLOTEN", g_gs.app); g_gs.proc = NULL; }
    if (!g_gs.closed) {
        if (g_gs.nsig >= 0 && (sigs & (1UL << g_gs.nsig))) gs_close("struikeldraad: wijziging in bewaakte map");
        else if (now >= g_gs.deadline) gs_close("tijd op");
        else if (now >= g_gs.idle_until) gs_close("geen verbinding (idle)");
        else if (g_gs.actions_left <= 0) gs_close("actielimiet");
        else if (gs_app_running()) {
            if (gs_scan_windows()) g_gs.app_had_window = 1;
            if (g_gs.app_had_window) {
                int ok;
                Forbid(); ok = gs_win_ok(IntuitionBase->ActiveWindow); Permit();
                g_gs.focus_bad = ok ? 0 : g_gs.focus_bad + 1;
                if (g_gs.focus_bad >= 2) gs_close("focusverlies");
            }
        }
    }
    /* closed: the agent ends once the program is gone; volumes stay protected until then */
    return g_gs.closed && !gs_app_running();
}

static int gs_info(struct buf *b)
{
    char line[GS_MAXPATH + 40]; int ok = 1;
    sprintf(line, "gui_session=%s\n", !g_gs.armed ? "none" : g_gs.closed ? "closed" : "open"); ok &= buf_str(b, line);
    if (g_gs.armed) {
        sprintf(line, "gui_app=%s\n", g_gs.app); ok &= buf_str(b, line);
        sprintf(line, "gui_app_running=%ld\n", (long)gs_app_running()); ok &= buf_str(b, line);
        sprintf(line, "gui_testdir=%s\n", g_gs.testdir); ok &= buf_str(b, line);
        sprintf(line, "gui_seconds_left=%ld\n", (long)(g_gs.deadline - gs_now())); ok &= buf_str(b, line);
        sprintf(line, "gui_actions_left=%ld\n", (long)g_gs.actions_left); ok &= buf_str(b, line);
        sprintf(line, "gui_protected=%ld\n", (long)g_gs.nvol); ok &= buf_str(b, line);
        if (g_gs.closed) { sprintf(line, "gui_closed_why=%s\n", g_gs.why); ok &= buf_str(b, line); }
    }
    return ok;
}
