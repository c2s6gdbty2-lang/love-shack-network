#!/usr/bin/env python3
"""test_filter.py - offline test of the READONLY client filter (pi/amimcp-ro.py).

No Amiga, no emulator, no network: the filter is started with LSN_UPSTREAM set to
a small fake upstream that answers tools/list with every upstream tool name and
echoes each tools/call it receives. The test checks what reaches the "agent".

    python3 tests/test_filter.py        (exit 0 = all checks passed)
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FILTER = os.path.join(HERE, "..", "pi", "amimcp-ro.py")
MARK = "TOKEN-MARKER-must-not-appear-in-the-audit-log"

FAKE = r'''
import json, sys
TOOLS = ["amiga_shell", "amiga_system_info", "amiga_list_dir", "amiga_read_file", "amiga_write_file",
         "amiga_screenshot", "amiga_screens", "amiga_pointer", "amiga_region_changed", "amiga_ui_tree",
         "amiga_menus", "amiga_rexx_ports", "amiga_arexx", "amiga_type", "amiga_key", "amiga_click",
         "amiga_drag", "amiga_button", "amiga_move_mouse", "amiga_break", "amiga_ui_click",
         "amiga_menu_select", "amiga_some_future_tool"]
for line in sys.stdin:
    m = json.loads(line)
    if "id" not in m:
        continue
    if m.get("method") == "tools/list":
        r = {"tools": [{"name": t} for t in TOOLS]}
    elif m.get("method") == "tools/call":
        r = {"content": [{"type": "text", "text": "UPSTREAM " + json.dumps(m["params"], sort_keys=True)}]}
    else:
        r = {}
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": m["id"], "result": r}) + "\n"); sys.stdout.flush()
'''

results = []


def check(what, ok, detail=""):
    results.append(ok)
    print(("  OK   " if ok else "  FOUT ") + what + (f"  [{detail}]" if detail and not ok else ""))


def run_session(env, calls):
    p = subprocess.Popen([sys.executable, "-I", FILTER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, env=env)
    msgs = [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}]
    for i, (name, args) in enumerate(calls, 2):
        msgs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                     "params": {"name": name, "arguments": args}})
    out, err = p.communicate("".join(json.dumps(m) + "\n" for m in msgs), timeout=60)
    by_id = {}
    for line in out.splitlines():
        m = json.loads(line)
        by_id[m["id"]] = m["result"]
    return p.returncode, by_id, err


def main():
    with tempfile.TemporaryDirectory() as t:
        fake = os.path.join(t, "fake_upstream.py")
        open(fake, "w").write(FAKE)
        audit = os.path.join(t, "audit.log")
        env = dict(os.environ, LSN_UPSTREAM=fake, LSN_AUDIT_LOG=audit, LSN_MIN_INTERVAL="0",
                   AMIGA_HOST="192.0.2.70", LSN_ALLOWED_HOSTS="192.0.2.70", AMIGA_TOKEN=MARK)

        allowed = [("amiga_shell", {"command": "Avail"}), ("amiga_shell", {"command": "Version"}),
                   ("amiga_shell", {"command": "ShowConfig", "timeout": 600}),
                   ("amiga_system_info", {}), ("amiga_list_dir", {"path": "SYS:S"}),
                   ("amiga_read_file", {"path": "S:Startup-Sequence"}),
                   ("amiga_screenshot", {"method": "sgrab"}), ("amiga_screens", {})]
        refused = [("amiga_write_file", {"path": "RAM:x", "content": "x"}),
                   ("amiga_arexx", {"source": "say 1"}), ("amiga_type", {"text": "x"}),
                   ("amiga_key", {"key": "return"}), ("amiga_click", {"x": 1, "y": 1}),
                   ("amiga_break", {}), ("amiga_menu_select", {"item": "Quit"}),
                   ("amiga_ui_click", {"gadget": "OK"}), ("amiga_some_future_tool", {}),
                   ("amiga_shell", {"command": "Dir"}), ("amiga_shell", {"command": "Avail FLUSH"}),
                   ("amiga_shell", {"command": "Avail\nDelete RAM:x"}), ("amiga_shell", {"command": "avail"}),
                   ("amiga_shell", {"command": "Avail", "extra": 1}),
                   ("amiga_read_file", {"path": "CON:0/0/100/50/x"}), ("amiga_list_dir", {"path": "ser:"}),
                   ("amiga_read_file", {"path": "S:x\nDelete"})]
        rc, res, err = run_session(env, allowed + refused)

        names = sorted(t["name"] for t in res[1]["tools"])
        check("tools/list shows exactly the 11 read tools", len(names) == 11 and "amiga_write_file" not in names
              and "amiga_some_future_tool" not in names, names)
        for i, (n, a) in enumerate(allowed, 2):
            text = res[i]["content"][0]["text"]
            check(f"forwarded: {n} {json.dumps(a)}", text.startswith("UPSTREAM ") and not res[i].get("isError"), text)
        sc = json.loads(res[2 + 2]["content"][0]["text"][9:])
        check("shell timeout is capped at 60 s", sc["arguments"]["timeout"] == 60, sc)
        shot = json.loads(res[2 + 6]["content"][0]["text"][9:])
        check("screenshot is forced to method=native", shot["arguments"]["method"] == "native", shot)
        for j, (n, a) in enumerate(refused, 2 + len(allowed)):
            text = res[j]["content"][0]["text"]
            check(f"refused by the filter: {n} {json.dumps(a)}",
                  res[j].get("isError") and text.startswith("READONLY-filter") and "UPSTREAM" not in text, text)
        log = open(audit).read()
        check("audit log written", log.count('"forwarded"') == len(allowed) and log.count('"refused"') == len(refused))
        check("token never in the audit log", MARK not in log)

        bad = dict(env, AMIGA_HOST="192.0.2.99")
        rc, res, err = run_session(bad, [])
        check("filter refuses to start for a host outside LSN_ALLOWED_HOSTS", rc == 2 and not res, err.strip())
        rc, res, err = run_session(dict(env, LSN_ALLOWED_HOSTS=""), [])
        check("filter refuses to start with an empty LSN_ALLOWED_HOSTS", rc == 2 and not res, err.strip())

    print(f"{sum(results)}/{len(results)} OK")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
