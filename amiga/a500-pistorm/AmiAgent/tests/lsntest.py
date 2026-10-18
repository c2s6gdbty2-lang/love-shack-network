#!/usr/bin/env python3
"""lsntest.py - emulatortests E1..E10 voor AmiAgent LSN. Draai IN de namespace:

    tests/ns.sh run python3 -I tests/lsntest.py basis      (boot + E1 E2 E4 E5 E6 E7 E9 E10)
    tests/ns.sh run python3 -I tests/lsntest.py e3         (twee boots met inet.access)
    tests/ns.sh run python3 -I tests/lsntest.py e8         (boot + test-smbd in de namespace)

Elke controle wordt vastgelegd als OK/FOUT in tests/resultaten/<fase>.txt en .json.
Alleen de scratch-emulator ($LSN_EMU) wordt aangeraakt.
"""
import json, os, socket, struct, subprocess, sys, time, zlib, hashlib

K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Your own Amiberry harness (not part of this repository; it needs your own Kickstart/Workbench):
#   LSN_HARNESS = directory with emu-boot.sh, emu-stop.sh, mkconf.py, maakhdf.sh, tools/aux.py
#   LSN_EMU     = scratch directory of that harness (work/, adf/); only this is touched
H = os.environ.get("LSN_HARNESS") or sys.exit("set LSN_HARNESS (see docs/TESTS.md)")
EMU = os.environ.get("LSN_EMU") or sys.exit("set LSN_EMU (see docs/TESTS.md)")
sys.path.insert(0, os.path.join(K, "upstream", "server"))
from amiga import Amiga, AmigaError, AmigaUnreachable  # noqa: E402

_tf = os.path.join(K, "tests", "testtoken")          # test-only token, made on first run, git-ignored
if not os.path.exists(_tf):
    import secrets
    with open(os.open(_tf, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as _f:
        _f.write("".join(secrets.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(24)) + "\n")
TOKEN = open(_tf).read().strip()
RES = os.path.join(K, "tests", "resultaten"); os.makedirs(RES, exist_ok=True)
fase = sys.argv[1]
log, checks = [], []


def say(s):
    print(s, flush=True); log.append(s)


def check(test, what, ok, detail=""):
    checks.append(dict(test=test, check=what, ok=bool(ok), detail=str(detail)[:400]))
    say(("  OK   " if ok else "  FOUT ") + f"{test}: {what}" + (f"  [{str(detail)[:160]}]" if detail else ""))


def aux(name, tmo, cmd, knoppen="", invoer=""):
    a = [sys.executable, "-I", os.path.join(H, "tools", "aux.py"), name, str(tmo), cmd, knoppen]
    if invoer:
        a.append(invoer)
    return subprocess.run(a, capture_output=True, text=True).stdout.replace(TOKEN, "<token>")


def ami(port=17846, token=TOKEN, timeout=20):
    return Amiga("127.0.0.1", port, token, timeout=timeout)


def try_(f):
    try:
        return "OK", f()
    except (AmigaError, AmigaUnreachable, OSError) as e:
        return type(e).__name__, str(e)


def boot(inet=""):
    env = dict(os.environ)
    if inet:
        env["INETACCESS"] = inet
    r = subprocess.run([os.path.join(K, "tests", "emu-aa.sh")], capture_output=True, text=True, env=env)
    say("boot: " + (r.stdout.strip().splitlines() or ["?"])[-1])


def install():
    out = aux("inst", 150, 'Execute "AmiAgent-Installatie:Installeer"', "V,V,V",
              f"Token (leeg~~{TOKEN}|controle:~~{TOKEN}")
    return out


def network():
    aux("n", 10, "Set PNstil 1")
    out = aux("net", 150, 'Execute "Work:PlipNet/Plipbox Start"')
    return "[3] OK" in out


def start():
    return aux("start", 40, 'Execute "Work:AmiAgent/AmiAgent Start"', "V")


def stop():
    return aux("stop", 40, 'Execute "Work:AmiAgent/AmiAgent Stop"', "V")


def mcp(server, calls, env_extra):
    """Start een MCP-server (lijst argv), voer tools/list + calls uit, geef resultaten terug."""
    env = dict(os.environ, AMIGA_HOST="127.0.0.1", AMIGA_PORT="17846", AMIGA_TOKEN=TOKEN, **env_extra)
    p = subprocess.Popen(server, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, env=env)
    n = [0]

    def call(method, params=None):
        n[0] += 1
        p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": n[0], "method": method, "params": params or {}}) + "\n")
        p.stdin.flush()
        while True:
            line = p.stdout.readline()
            if not line:
                return None
            m = json.loads(line)
            if m.get("id") == n[0]:
                return m
    call("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "lsntest", "version": "1"}})
    p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"); p.stdin.flush()
    tools = [t["name"] for t in call("tools/list")["result"]["tools"]]
    out = []
    for name, args in calls:
        r = call("tools/call", {"name": name, "arguments": args})
        res = r.get("result") or {}
        text = " ".join(c.get("text", "[%s]" % c.get("type")) for c in res.get("content", []))
        if "error" in r:
            text = "JSON-RPC error: " + json.dumps(r["error"])
        out.append((name, args, bool(res.get("isError")) or "error" in r, text))
    p.stdin.close(); p.wait(timeout=20)
    return tools, out


def work_digest():
    """sha256 over alle bestanden in de host-map achter Work: (excl. .uaem-metadata)."""
    h = hashlib.sha256()
    for root, dirs, files in sorted(os.walk(os.path.join(EMU, "work"))):
        dirs.sort()
        for f in sorted(files):
            fp = os.path.join(root, f)
            h.update(os.path.relpath(fp, EMU).encode()); h.update(open(fp, "rb").read())
    return h.hexdigest()


# ---------------------------------------------------------------------------
def fase_basis():
    boot()
    # E1 - starten en stoppen
    out = aux("e1a", 40, 'Execute "AmiAgent-Installatie:AmiAgent/AmiAgent Start"', "V")
    check("E1", "Start zonder installatie geweigerd", "ontbreekt" in out, out.splitlines()[-2:] if out else "")
    out = install()
    check("E1", "installatie, CRC-controle 15/15", "15 ongewijzigd, 0 afwijkend" in out and "Installatie klaar" in out)
    tok = open(os.path.join(EMU, "work", "AmiAgent", "Prefs", "Token"), "rb").read()
    check("E1", "token opgeslagen, niet op de ADF", tok == TOKEN.encode() and TOKEN.encode() not in
          open(os.path.join(K, "out", "AmiAgent-Installatie.adf"), "rb").read())
    out = start()
    check("E1", "Start zonder netwerk geweigerd", "nog geen netwerk" in out)
    check("E1", "netwerk (AmiTCP 3.0b2) gestart", network())
    out = start()
    check("E1", "Start: luistert op 7846", "luistert op poort 7846" in out)
    st, v = try_(lambda: ami().ping())
    check("E1", "PING met juist token, meldt READONLY", st == "OK" and "READONLY" in v, v)
    out = start()
    check("E1", "tweede Start: 'draait al', geen tweede agent", "draait al" in out)
    out = aux("st", 10, "Status")
    check("E1", "precies een amiagent-proces", out.count("Work:AmiAgent/amiagent") == 1)
    out = stop()
    check("E1", "Stop", "is gestopt" in out)
    st, v = try_(lambda: ami(timeout=5).ping())
    check("E1", "na Stop geen verbinding meer", st != "OK", st)
    out = stop()
    check("E1", "Stop als hij niet draait: nette melding", "draaide niet" in out)
    out = start()
    st, v = try_(lambda: ami().ping())
    check("E1", "opnieuw Start werkt", "luistert" in out and st == "OK")

    # E2 - token
    st, v = try_(lambda: ami(token="fout-token-123456").ping())
    check("E2", "fout token geweigerd", st != "OK" and "bad token" in v, v)
    st, v = try_(lambda: ami(token="").ping())
    check("E2", "zonder token geweigerd", st != "OK", v)
    st, v = try_(lambda: ami(token=TOKEN[:-1]).ping())
    check("E2", "token met 1 teken te weinig geweigerd", st != "OK", v)
    st, v = try_(lambda: ami().ping())
    check("E2", "agent draait door na foute pogingen", st == "OK")
    out = aux("e2tf", 20, "Work:AmiAgent/amiagent TOKENFILE=RAM:bestaat-niet PORT=7850")
    check("E2", "start met ontbrekend TOKENFILE geweigerd", "TOKENFILE is missing" in out, out.splitlines()[-1:])
    out = aux("e2nt", 20, "Work:AmiAgent/amiagent PORT=7851")
    check("E2", "READONLY-build start niet zonder token", "refusing to start without a token" in out)
    out = aux("e2st", 10, "Status")
    check("E2", "token niet zichtbaar in Status", TOKEN not in out and "<token>" not in out)

    # E4 - clientfilter
    ro = [sys.executable, "-I", os.path.join(K, "pi", "amimcp-ro.py")]
    env = dict(LSN_ALLOWED_HOSTS="127.0.0.1", LSN_AUDIT_LOG=os.path.join(RES, "audit-e4.log"))
    calls = [("amiga_shell", {"command": "Avail"}), ("amiga_shell", {"command": "Version"}),
             ("amiga_shell", {"command": "ShowConfig"}), ("amiga_system_info", {}),
             ("amiga_list_dir", {"path": "SYS:S"}), ("amiga_read_file", {"path": "S:Startup-Sequence"}),
             ("amiga_shell", {"command": "Delete RAM:x"}), ("amiga_shell", {"command": "Avail FLUSH"}),
             ("amiga_shell", {"command": "Avail >RAM:x"}), ("amiga_write_file", {"path": "RAM:x", "content": "x"}),
             ("amiga_arexx", {"source": "say 1"}), ("amiga_type", {"text": "x"}), ("amiga_click", {"x": 1, "y": 1}),
             ("amiga_break", {}), ("amiga_menu_select", {"item": "Quit"}), ("amiga_ui_click", {"gadget": "OK"}),
             ("amiga_read_file", {"path": "CON:0/0/100/50/x"})]
    tools, res = mcp(ro, calls, env)
    check("E4", "filter toont alleen 11 leestools", sorted(tools) == sorted([
        "amiga_shell", "amiga_system_info", "amiga_list_dir", "amiga_read_file", "amiga_screenshot", "amiga_screens",
        "amiga_pointer", "amiga_region_changed", "amiga_ui_tree", "amiga_menus", "amiga_rexx_ports"]), tools)
    for (name, args, err, text) in res:
        allowed = (name, json.dumps(args)) in [("amiga_shell", json.dumps({"command": c})) for c in ("Avail", "Version", "ShowConfig")] \
            or name in ("amiga_system_info", "amiga_list_dir") or (name == "amiga_read_file" and args["path"].startswith("S:"))
        if allowed:
            check("E4", f"toegestaan: {name} {json.dumps(args)}", not err, text[:120])
        else:
            check("E4", f"geweigerd door filter: {name} {json.dumps(args)}", err and "READONLY-filter" in text, text[:120])
    sc = [t for (n, a, e, t) in res if a.get("command") == "ShowConfig"]
    check("E4", "ShowConfig geeft geheugenindeling", sc and "RAM" in sc[0].upper(), sc[0][:200] if sc else "")
    env_bad = dict(env, LSN_ALLOWED_HOSTS="192.0.2.70")
    r = subprocess.run(ro, input="", capture_output=True, text=True,
                       env=dict(os.environ, AMIGA_HOST="127.0.0.1", **env_bad))
    check("E4", "filter weigert een host buiten LSN_ALLOWED_HOSTS", r.returncode == 2, r.stderr.strip())

    # E7 - schermafdruk en GUI-boom (via de filter)
    tools, res = mcp(ro, [("amiga_screenshot", {}), ("amiga_screens", {}), ("amiga_ui_tree", {}),
                          ("amiga_menus", {}), ("amiga_pointer", {}), ("amiga_region_changed", {"x": 0, "y": 0, "w": 64, "h": 16})], env)
    for (name, args, err, text) in res:
        check("E7", f"{name} werkt", not err, text[:100])

    # E5 - netwerk weg en terug, client breekt af
    before = ami().system_info()
    aux("e5d", 20, "Work:PlipNet/AmiTCP/bin/ifconfig plip0 down")
    st, v = try_(lambda: ami(timeout=6).ping())
    check("E5", "interface down: geen antwoord (time-out)", st != "OK", st)
    aux("e5u", 20, "Work:PlipNet/AmiTCP/bin/ifconfig plip0 up")
    ok = False
    for _ in range(10):
        st, v = try_(lambda: ami(timeout=6).ping())
        if st == "OK":
            ok = True; break
        time.sleep(2)
    check("E5", "interface up: agent weer bereikbaar zonder herstart", ok, st)
    s = socket.create_connection(("127.0.0.1", 17846), timeout=5)
    s.sendall(struct.pack(">4sBBHI", b"AMI0", 0x10, 0, 0, len(TOKEN)) + TOKEN.encode())
    s.close()
    st, v = try_(lambda: ami().ping())
    check("E5", "client verbreekt midden in een verzoek: agent draait door", st == "OK")
    s = socket.create_connection(("127.0.0.1", 17846), timeout=5)
    s.sendall(b"rommel" * 10); time.sleep(1); s.close()
    st, v = try_(lambda: ami().ping())
    check("E5", "ongeldig frame: agent draait door", st == "OK")

    # E6 - vastgelopen opdracht (rw-testbuild op poort 7847) en READONLY-gedrag
    aux("e6s", 20, f"Run >NIL: Work:Test/amiagent-rw-test PORT=7847 TOKEN={TOKEN}")
    time.sleep(3)
    rw = ami(port=17847, timeout=30)
    st, v = try_(lambda: rw.exec_command("Wait 30", timeout=3))
    check("E6", "rw-test: 'Wait 30' met limiet 3 s -> 'still running'", st != "OK" and "still running" in v, v[:120])
    st, v = try_(lambda: rw.ping())
    check("E6", "rw-test: agent blijft bereikbaar tijdens vastgelopen opdracht", st == "OK")
    st, v = try_(lambda: rw.break_command())
    check("E6", "rw-test: BREAK stuurt Ctrl-C", st == "OK" and "Ctrl-C" in v, v[:120])
    time.sleep(2)
    st, v = try_(lambda: rw.exec_command("Echo na-break", timeout=10))
    check("E6", "rw-test: na BREAK werkt een nieuwe opdracht", st == "OK" and "na-break" in v[1], v)
    aux("e6q", 20, "Status")
    st, v = try_(lambda: ami().break_command())
    check("E6", "READONLY: BREAK geweigerd", st != "OK" and "READONLY" in v, v)
    st, v = try_(lambda: ami().exec_command("Wait 30", timeout=3))
    check("E6", "READONLY: 'Wait 30' geweigerd (kan niet vastlopen)", st != "OK" and "READONLY" in v, v)
    # rw-test weer stoppen
    nr = aux("e6n", 10, "Status COMMAND=Work:Test/amiagent-rw-test").strip().splitlines()
    nr = [x for x in nr if x.strip().isdigit()]
    if nr:
        aux("e6b", 10, f"Break {nr[-1].strip()} C")
    time.sleep(2)
    st, v = try_(lambda: ami(port=17847, timeout=5).ping())
    check("E6", "rw-test-agent weer gestopt (niet meer bereikbaar)", st != "OK")

    # E10 - omzeilpogingen: zonder filter, rechtstreeks op het protocol, lokale ARexx
    d0 = work_digest()
    ram0 = aux("e10r0", 20, "List RAM: ALL QUICK NOHEAD")
    up = [sys.executable, "-I", os.path.join(K, "upstream", "server", "amimcp.py")]
    tools, res = mcp(up, [("amiga_write_file", {"path": "RAM:omzeil.txt", "content": "x"}),
                          ("amiga_write_file", {"path": "Work:omzeil.txt", "content": "x"}),
                          ("amiga_shell", {"command": "Delete Work:AmiAgent/LeesMij"}),
                          ("amiga_shell", {"command": "Avail >RAM:omzeil"}),
                          ("amiga_arexx", {"source": "address command 'Delete Work:AmiAgent/LeesMij'"}),
                          ("amiga_type", {"text": "Delete Work:AmiAgent/LeesMij\n"}),
                          ("amiga_click", {"x": 100, "y": 100}), ("amiga_key", {"key": "return"}),
                          ("amiga_menu_select", {"item": "Quit"}), ("amiga_ui_click", {"gadget": "OK"}),
                          ("amiga_break", {}),
                          ("amiga_screenshot", {"method": "sgrab"})], {})
    for (name, args, err, text) in res:
        check("E10", f"zonder filter geweigerd door agent: {name} {json.dumps(args)[:60]}", err and "READONLY" in text, text[:110])
    raw = ami()
    attempts = [
        ("EXEC 'Avail FLUSH'", lambda: raw.exec_command("Avail FLUSH")),
        ("EXEC 'Avail >RAM:x'", lambda: raw.exec_command("Avail >RAM:x")),
        ("EXEC 'Avail' + newline + Delete", lambda: raw.exec_command("Avail\nDelete Work:AmiAgent/LeesMij")),
        ("EXEC ' Avail' (spatie)", lambda: raw.exec_command(" Avail")),
        ("EXEC 'C:Avail'", lambda: raw.exec_command("C:Avail")),
        ("EXEC 'Avail;x'", lambda: raw.exec_command("Avail;x")),
        ("EXEC 'Version Work:AmiAgent/amiagent'", lambda: raw.exec_command("Version Work:AmiAgent/amiagent")),
        ("PUT RAM:x", lambda: raw.write_file("RAM:x", b"x")),
        ("AREXX", lambda: raw.arexx("say 1")),
        ("INPUT tekst", lambda: raw.input_text("x")),
        ("INPUT klik", lambda: raw.input_click(10, 10)),
        ("UIACT", lambda: raw.ui_click("OK")),
        ("BREAK", lambda: raw.break_command()),
        ("GET CON:", lambda: raw.read_file("CON:0/0/200/50/omzeil")),
        ("GET RAW:", lambda: raw.read_file("RAW:0/0/200/50/omzeil")),
        ("GET SER:", lambda: raw.read_file("SER:")),
        ("GET PIPE:", lambda: raw.read_file("PIPE:omzeil")),
        ("GET map Work:AmiAgent", lambda: raw.read_file("Work:AmiAgent")),
        ("GETRANGE CON:", lambda: raw.read_range("CON:0/0/200/50/omzeil", 0, 10)),
    ]
    for what, f in attempts:
        st, v = try_(f)
        check("E10", f"protocol rechtstreeks geweigerd: {what}", st != "OK", str(v)[:110])
    for code in (0x04, 0x08, 0x09, 0x0E, 0x12, 0x7F):
        s = socket.create_connection(("127.0.0.1", 17846), timeout=10)
        frame = lambda c, p: struct.pack(">4sBBHI", b"AMI0", c, 0, 0, len(p)) + p
        s.sendall(frame(0x10, TOKEN.encode())); s.recv(64)
        s.sendall(frame(code, b"RAM:x\x00\x00\x00\x01x"))
        r = b""
        try:
            while True:
                d = s.recv(256)
                if not d:
                    break
                r += d
        except (socket.timeout, ConnectionResetError):
            pass
        s.close()
        check("E10", f"ruw frame 0x{code:02X} geweigerd", b"READONLY" in r or b"unknown command" in r, r[12:90])
    for what, f in [("EXEC Avail", lambda: raw.exec_command("Avail")), ("EXEC avail (kleine letters)", lambda: raw.exec_command("avail")),
                    ("GET S:Startup-Sequence", lambda: raw.read_file("S:Startup-Sequence")),
                    ("GETRANGE S:Startup-Sequence", lambda: raw.read_range("S:Startup-Sequence", 0, 16))]:
        st, v = try_(f)
        check("E10", f"leesactie nog steeds toegestaan: {what}", st == "OK")
    # lokale ARexx-poort AMIAGENT (vanaf de Amiga zelf)
    aux("rx0", 30, "Run >NIL: SYS:System/RexxMast")
    time.sleep(3)
    for c, want in [("ENTERTEXT Delete", "20"), ("KEY return", "20"), ("TASKPRI amiagent 5", "20"),
                    ("ACTIVATEWINDOW Workbench", "20"), ("VERSION", "0"), ("TASKLIST", "0")]:
        out = aux("rx", 30, f"SYS:Rexxc/RX \"address AMIAGENT; '{c}'; say 'RC=' rc\"")
        got = [l for l in out.splitlines() if "RC=" in l]
        check("E10", f"lokale ARexx {c.split()[0]} -> rc {want}", got and got[-1].replace(" ", "").endswith("RC=" + want), got[-1:] if got else out[-120:])
    d1 = work_digest()
    ram1 = aux("e10r1", 20, "List RAM: ALL QUICK NOHEAD")
    check("E10", "Work: byte-identiek na alle pogingen", d0 == d1, d0[:16] + " / " + d1[:16])
    check("E10", "RAM: ongewijzigd na alle pogingen", ram0.split("\n", 1)[1:] == ram1.split("\n", 1)[1:])
    pr = aux("e10ok", 15, "Echo \"Work:AmiAgent/LeesMij:\" NOLINE")
    check("E10", "Work:AmiAgent/LeesMij bestaat nog", os.path.exists(os.path.join(EMU, "work", "AmiAgent", "LeesMij")))

    # E9 - herhaalde verbindingen: 3 reeksen van 300 (elke 10e met Avail), tempo ~10/s.
    # Criterium: geen GROEI meer tussen reeks 2 en 3 (AmiTCP-bufferpool groeit eerst en blijft dan gelijk).
    a = ami()
    def vrij():
        time.sleep(2); i = a.system_info(); return int(i["chipram_free"]), int(i["fastram_free"])
    pts = [vrij()]; fails = 0; t0 = time.time()
    for b in range(3):
        for i in range(300):
            st, v = try_(lambda: a.exec_command("Avail") if i % 10 == 0 else a.ping())
            fails += st != "OK"; time.sleep(0.1)
        pts.append(vrij())
    dt = time.time() - t0
    for n, (c, f) in enumerate(pts):
        say(f"  E9 meting {n}: chip {c} fast {f}")
    check("E9", f"900 verbindingen (90x Avail) in {dt:.0f} s, tempo ~10/s, zonder fout", fails == 0, f"{fails} fouten")
    check("E9", "Chip RAM: geen groei tussen reeks 2 en 3", abs(pts[2][0] - pts[3][0]) <= 4096, pts[2][0] - pts[3][0])
    check("E9", "Fast RAM: geen groei tussen reeks 2 en 3 (<= 16 KB)", pts[2][1] - pts[3][1] <= 16384, pts[2][1] - pts[3][1])
    stop()


def fase_e3():
    for label, rules, expect_ok in [
        ("productieregels (alleen Pi en Mac, voorbeeldadressen)",
         "7846\t192.0.2.145\tallow\tLOG\n7846\t192.0.2.30\tallow\tLOG\n7846\t*.*.*.*\tdeny\tLOG\n", False),
        ("testregels (10.0.2.2 speelt de Pi)",
         "7846\t10.0.2.2\tallow\tLOG\n7846\t*.*.*.*\tdeny\tLOG\n", True)]:
        say(f"-- E3: {label}")
        boot(rules)
        install(); network(); start()
        st, v = try_(lambda: ami(timeout=8).ping())
        check("E3", f"{label}: verbinding {'toegestaan' if expect_ok else 'geweigerd'}", (st == "OK") == expect_ok, st)
        lg = aux("e3log", 15, "Search T:AmiTCP.log \"port 7846\"")
        check("E3", f"{label}: AmiTCP-log meldt de beslissing",
              ("allowed" if expect_ok else "denied") in lg, [l for l in lg.splitlines() if "7846" in l][-1:])
        stop()


def fase_e8():
    # test-smbd wordt vooraf buiten deze driver gestart: tests/e8-smbd.sh start
    T = os.path.join(K, "tests", "smbd"); share = os.path.join(T, "share"); pw = "e8-testwachtwoord"
    try:
        socket.create_connection((os.environ.get("E8_SMB", "10.99.0.1"), 4450), timeout=3).close(); up = True
    except OSError:
        up = False
    check("E8", f"test-smbd bereikbaar ({os.environ.get('E8_SMB', '10.99.0.1')}:4450)", up)
    payload = os.urandom(200000); open(os.path.join(share, "groot.bin"), "wb").write(payload)
    crc = "%08X" % (zlib.crc32(payload) & 0xFFFFFFFF)
    boot()
    install(); network(); start()
    out = aux("e8m", 60, f"Run >NIL: Work:Test/smbfs SHARE=//{os.environ.get("E8_SMB", "10.99.0.1")}:4450/LSNTest USER={os.environ.get("USER", "lsntest")} PASSWORD={pw} VOLUME=LSNTest DEVICE=LSNSMB PROTOCOL=nt1 SETENV")
    time.sleep(6)
    out = aux("e8l", 30, "List LSNTest:")
    check("E8", "smbfs koppelt LSNTest: naast amiagent (zelfde AmiTCP)", "groot.bin" in out, out.splitlines()[-2:])
    a = ami()
    st, v = try_(lambda: a.ping())
    check("E8", "amiagent bereikbaar terwijl smbfs gekoppeld is", st == "OK")
    import threading
    res = {}
    def kopieer():
        res["out"] = aux("e8c", 120, "Copy LSNTest:groot.bin RAM:groot.bin")
    th = threading.Thread(target=kopieer); th.start()
    pings = []
    for _ in range(10):
        pings.append(try_(lambda: a.ping())[0]); time.sleep(0.5)
    th.join()
    check("E8", "amiagent antwoordt tijdens SMB-kopie (10/10)", pings.count("OK") == 10, pings)
    st, v = try_(lambda: a.read_file("RAM:groot.bin"))
    check("E8", "kopie via smbfs byte-identiek (gelezen via amiagent)", st == "OK" and zlib.crc32(v) & 0xFFFFFFFF == int(crc, 16), crc)
    st, v = try_(lambda: a.list_dir("LSNTest:"))
    check("E8", "amiagent kan LSNTest: alleen lezen (LIST)", st == "OK")
    st, v = try_(lambda: a.write_file("LSNTest:schrijf.txt", b"x"))
    check("E8", "amiagent kan NIET naar de share schrijven", st != "OK" and not os.path.exists(os.path.join(share, "schrijf.txt")), v)
    stop()
    out = aux("e8l2", 30, "List LSNTest:")
    check("E8", "na AmiAgent Stop blijft LSNTest: gekoppeld", "groot.bin" in out)


{"basis": fase_basis, "e3": fase_e3, "e8": fase_e8}[fase]()
subprocess.run([os.path.join(H, "emu-stop.sh")])
okn = sum(c["ok"] for c in checks)
say(f"== {fase}: {okn}/{len(checks)} controles OK")
open(os.path.join(RES, fase + ".txt"), "w").write("\n".join(log) + "\n")
json.dump(checks, open(os.path.join(RES, fase + ".json"), "w"), indent=1)
