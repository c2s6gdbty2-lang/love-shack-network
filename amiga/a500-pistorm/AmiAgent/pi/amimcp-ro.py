#!/usr/bin/env python3
"""amimcp-ro.py - READONLY client filter for amimcp (The Love Shack Network).

The second safety layer, in front of the upstream MCP server. Claude Code
starts this file as its MCP server; this file starts upstream amimcp.py as a
child and passes JSON-RPC through, but:

  * tools/list only shows the tools on ALLOW (an unknown or new upstream tool
    stays hidden and blocked: allowlist, not denylist);
  * tools/call for any other tool is answered here and never reaches the agent;
  * amiga_shell only accepts exactly Avail, Version or ShowConfig, nothing else;
  * amiga_screenshot is always forced to method=native (the SGrab fallback
    would run a program on the Amiga);
  * amiga_read_file / amiga_list_dir refuse device handlers (CON:, SER:, ...);
  * AMIGA_HOST must be in LSN_ALLOWED_HOSTS;
  * every call is written to an audit log (never the token);
  * at most one tool call is in flight, with at least LSN_MIN_INTERVAL seconds
    (default 0.5) between calls; the filter never retries (upstream does not either).

The first layer is the READONLY agent build itself: even a client that skips
this filter cannot write. Standard library only.
"""
import json, os, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
UPSTREAM = os.environ.get("LSN_UPSTREAM", os.path.join(HERE, "..", "upstream", "server", "amimcp.py"))
AUDIT = os.environ.get("LSN_AUDIT_LOG", os.path.join(HERE, "..", "log", "audit.log"))
ALLOWED_HOSTS = [h for h in os.environ.get("LSN_ALLOWED_HOSTS", "").split(",") if h]
MIN_INTERVAL = float(os.environ.get("LSN_MIN_INTERVAL", "0.5"))

ALLOW = {
    "amiga_shell", "amiga_system_info", "amiga_list_dir", "amiga_read_file",
    "amiga_screenshot", "amiga_screens", "amiga_pointer", "amiga_region_changed",
    "amiga_ui_tree", "amiga_menus", "amiga_rexx_ports",
}
SHELL_ALLOW = {"Avail", "Version", "ShowConfig"}
DEVICES = {"CON", "RAW", "SER", "PAR", "PRT", "PIPE", "AUX", "NIL", "TCP", "SPEAK", "KCON", "KRAW"}


def audit(event, **kw):
    try:
        os.makedirs(os.path.dirname(AUDIT), exist_ok=True)
        with open(AUDIT, "a") as f:
            f.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **kw}) + "\n")
    except OSError:
        pass


def refuse(why):
    return {"content": [{"type": "text", "text": "READONLY-filter: " + why}], "isError": True}


def check_call(name, args):
    """Return (args, None) to forward, or (None, reason) to refuse."""
    if name not in ALLOW:
        return None, f"{name} is not allowed in read-only mode"
    args = dict(args or {})
    if name == "amiga_shell":
        cmd = args.get("command")
        if cmd not in SHELL_ALLOW:
            return None, "amiga_shell only accepts exactly: " + ", ".join(sorted(SHELL_ALLOW))
        extra = set(args) - {"command", "timeout"}
        if extra:
            return None, "amiga_shell: unexpected arguments " + ", ".join(sorted(extra))
        args["timeout"] = min(int(args.get("timeout", 60) or 60), 60)
    if name == "amiga_screenshot":
        args["method"] = "native"
    if name in ("amiga_read_file", "amiga_list_dir"):
        path = str(args.get("path", ""))
        dev = path.split(":", 1)[0].upper() if ":" in path else ""
        if dev in DEVICES or "\n" in path or "\r" in path:
            return None, f"{name}: device handlers and control characters are refused"
    return args, None


def main():
    host = os.environ.get("AMIGA_HOST", "")
    if host not in ALLOWED_HOSTS:
        sys.stderr.write("amimcp-ro: AMIGA_HOST %r is not in LSN_ALLOWED_HOSTS\n" % host)
        sys.exit(2)
    child = subprocess.Popen([sys.executable, "-I", UPSTREAM], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, text=True, bufsize=1)
    out_lock = threading.Lock()
    list_ids = set()
    pending = {}                 # id -> Event, for the one tool call in flight
    last = [0.0]

    def emit(msg):
        with out_lock:
            sys.stdout.write(json.dumps(msg) + "\n"); sys.stdout.flush()

    def from_child():
        for line in child.stdout:
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            ev = pending.pop(msg.get("id"), None)
            if ev:
                ev.set()
            if msg.get("id") in list_ids and "result" in msg:
                list_ids.discard(msg["id"])
                tools = msg["result"].get("tools", [])
                msg["result"]["tools"] = [t for t in tools if t.get("name") in ALLOW]
            emit(msg)
    threading.Thread(target=from_child, daemon=True).start()

    for line in sys.stdin:
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if msg.get("method") == "tools/list":
            list_ids.add(msg.get("id"))
        if msg.get("method") == "tools/call":
            p = msg.get("params") or {}
            name = p.get("name", "")
            args, why = check_call(name, p.get("arguments"))
            if why:
                audit("refused", tool=name, reason=why)
                emit({"jsonrpc": "2.0", "id": msg.get("id"), "result": refuse(why)})
                continue
            audit("forwarded", tool=name, args=args)
            msg["params"]["arguments"] = args
            wait = last[0] + MIN_INTERVAL - time.time()
            if wait > 0:
                time.sleep(wait)
            ev = threading.Event(); pending[msg.get("id")] = ev
            child.stdin.write(json.dumps(msg) + "\n"); child.stdin.flush()
            ev.wait(timeout=180)  # one call at a time; no retry when it times out
            last[0] = time.time()
            continue
        child.stdin.write(json.dumps(msg) + "\n"); child.stdin.flush()
    child.stdin.close()
    child.wait(timeout=10)


if __name__ == "__main__":
    main()
