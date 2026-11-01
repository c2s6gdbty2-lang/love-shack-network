#!/usr/bin/env python3
"""amimcp-ws.py - WRITE-SAFE MCP server (The Love Shack Network).

A separate MCP server, next to the READONLY filter amimcp-ro.py, which it does
not touch. It only speaks the COPYIN command: a file from the Pi outbox is
staged on AmigaShare and then fetched by amiagent-ws on the Amiga.

This is NOT a security boundary. Whoever can run things as this user can read
the token and talk to the agent directly. Every rule that matters is enforced
on the Amiga, under a mandate given at the machine. This file gives correct
staging, a clear error and an audit trail; it adds no authority.

Standard library plus upstream amiga.py (the framing).
"""
import hashlib, json, os, re, subprocess, sys, time, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get("LSN_UPSTREAM_DIR", os.path.join(HERE, "..", "upstream", "server")))
from amiga import Amiga, AmigaError, AmigaUnreachable  # noqa: E402

MACHINE = os.environ.get("LSN_MACHINE", "a600")
AUDIT = os.environ.get("LSN_AUDIT_LOG", os.path.join(HERE, "..", "log", f"audit-ws-{MACHINE}.log"))
OUTBOX = os.path.realpath(os.environ.get("LSN_WS_OUTBOX", os.path.join(HERE, "..", "outbox")))
STAGE = os.environ.get("LSN_WS_STAGE", os.path.join(HERE, "..", "share", MACHINE))
SUDO_USER = os.environ.get("LSN_WS_SUDO", "amiga")     # empty: write directly (tests)
ALLOWED_HOSTS = [h for h in os.environ.get("LSN_ALLOWED_HOSTS", "").split(",") if h]
MAX_BYTES = int(os.environ.get("LSN_WS_MAXBYTES", str(1024 * 1024)))
CMD_COPYIN = 0x40
NAME = re.compile(r"^[A-Za-z0-9_+\-][A-Za-z0-9._+\- ]{0,29}$")

ARGS = {
    "type": "object",
    "properties": {
        "local_path": {"type": "string", "description": "File on the Pi, inside the WRITE-SAFE outbox."},
        "dest_dir": {"type": "string", "description": "Folder on the Amiga, inside the mandate's WRITEROOT."},
        "name": {"type": "string", "description": "New file name, without any path."},
    },
    "required": ["local_path", "dest_dir", "name"],
}
TOOLS = [
    {"name": "amiga_ws_status", "description": "Show whether this Amiga has an open write mandate.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "amiga_ws_check", "description": "Dry run of amiga_ws_put: all checks on the Amiga, nothing written, no write counted.",
     "inputSchema": ARGS},
    {"name": "amiga_ws_put", "description": "Place one NEW file on the Amiga. Never overwrites. Needs a mandate given at the Amiga.",
     "inputSchema": ARGS},
]


def audit(event, **kw):
    try:
        os.makedirs(os.path.dirname(AUDIT), exist_ok=True)
        with open(AUDIT, "a") as f:
            f.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "machine": MACHINE, "event": event, **kw}) + "\n")
    except OSError:
        pass


def stage_write(path, data):
    if SUDO_USER:
        subprocess.run(["sudo", "-n", "-u", SUDO_USER, "tee", path], input=data, stdout=subprocess.DEVNULL,
                       stderr=subprocess.PIPE, check=True)
    else:
        with open(path, "wb") as f:
            f.write(data)


def stage_remove(path):
    if SUDO_USER:
        subprocess.run(["sudo", "-n", "-u", SUDO_USER, "rm", "-f", path], check=False)
    else:
        try:
            os.remove(path)
        except OSError:
            pass


def copyin(ami, flags, size, crc, src, dest_dir, name, timeout):
    body = bytes([flags]) + size.to_bytes(4, "big") + crc.to_bytes(4, "big")
    body += src.encode("latin-1") + b"\0" + dest_dir.encode("latin-1") + b"\0" + name.encode("latin-1") + b"\0"
    return ami._request(CMD_COPYIN, body, timeout=timeout).decode("latin-1", "replace")


def tool_status(ami, args):
    info = ami._request(0x06).decode("latin-1", "replace")
    keep = [l for l in info.splitlines() if l.startswith(("agent=", "build=", "write"))]
    return "\n".join(keep)


def tool_copy(ami, args, check):
    path = os.path.realpath(str(args.get("local_path", "")))
    dest_dir, name = str(args.get("dest_dir", "")), str(args.get("name", ""))
    if not path.startswith(OUTBOX + os.sep) or not os.path.isfile(path):
        raise ValueError(f"local_path must be a file inside {OUTBOX}")
    if not NAME.match(name) or name.lower().endswith(".info") or name.endswith((".", " ")):
        raise ValueError("name is not a plain Amiga file name")
    with open(path, "rb") as f:
        data = f.read()
    if not 0 < len(data) <= MAX_BYTES:
        raise ValueError(f"file must be 1..{MAX_BYTES} bytes")
    crc = zlib.crc32(data) & 0xFFFFFFFF
    sha = hashlib.sha256(data).hexdigest()
    src = f"ws-{crc:08x}-{os.getpid() & 0xFFFF:04x}"
    full = os.path.join(STAGE, src)
    meta = dict(file=os.path.basename(path), size=len(data), crc=f"{crc:08x}", sha256=sha, dest=f"{dest_dir}/{name}")
    audit("start", tool="check" if check else "put", **meta)
    stage_write(full, data)
    try:
        out = copyin(ami, 1 if check else 0, len(data), crc, src, dest_dir, name, 60 + len(data) // 2048)
    except (AmigaError, AmigaUnreachable) as e:
        audit("error", tool="check" if check else "put", error=str(e)[:200], **meta)
        raise
    finally:
        stage_remove(full)
    audit("ok", tool="check" if check else "put", **meta)
    return out.strip()


def main():
    host = os.environ.get("AMIGA_HOST", "")
    if host not in ALLOWED_HOSTS:
        sys.stderr.write(f"amimcp-ws: AMIGA_HOST {host!r} is not in LSN_ALLOWED_HOSTS\n")
        sys.exit(2)
    ami = Amiga(host, int(os.environ.get("AMIGA_PORT", "7846")), os.environ.get("AMIGA_TOKEN", ""), timeout=30)
    calls = {"amiga_ws_status": tool_status,
             "amiga_ws_check": lambda a, x: tool_copy(a, x, True),
             "amiga_ws_put": lambda a, x: tool_copy(a, x, False)}
    for line in sys.stdin:
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        mid, method = msg.get("id"), msg.get("method")
        if method == "initialize":
            result = {"protocolVersion": msg.get("params", {}).get("protocolVersion", "2024-11-05"),
                      "capabilities": {"tools": {}}, "serverInfo": {"name": "amimcp-ws", "version": "1.0"}}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            p = msg.get("params") or {}
            fn = calls.get(p.get("name"))
            try:
                if not fn:
                    raise ValueError("unknown tool")
                result = {"content": [{"type": "text", "text": fn(ami, p.get("arguments") or {})}]}
            except (AmigaError, AmigaUnreachable, ValueError, OSError, subprocess.CalledProcessError) as e:
                result = {"content": [{"type": "text", "text": str(e)}], "isError": True}
        elif mid is None:
            continue
        else:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "unknown method"}}) + "\n")
            sys.stdout.flush()
            continue
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid, "result": result}) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
