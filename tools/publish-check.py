#!/usr/bin/env python3
"""publish-check.py - pre-publication scanner for The Love Shack Network.

Scans files (and the contents of .zip/.tgz archives and raw ADF/HDF images)
for material that must not be published:

  SECRET    literal secrets listed in a private file outside the repository
            (one per line; default ~/.lsn-secrets). Values are never printed.
  CRED      password/psk assignments that are not placeholders
  IP        private IPv4 addresses (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
  MAC       hardware (MAC) addresses
  EMAIL     e-mail addresses
  NAME      private words listed in the secrets file with a "name:" prefix
            (for example an SSID or a family name)
  ROM       Amiga Kickstart ROM images (by size and header)
  WB        files that look like Commodore/Hyperion Workbench components

Usage:
  publish-check.py [--secrets FILE] [--allow FILE] [--strict-ip] PATH...

An allow file lists justified exceptions, one per line:
  KIND<TAB>path suffix<TAB>reason
Allowed findings are printed as "allow" and do not block.

Exit code 0 when nothing blocking was found, 1 otherwise. IP findings are
reported but only block when --strict-ip is given.
"""
import argparse
import io
import os
import re
import sys
import tarfile
import zipfile

PLACEHOLDER = re.compile(rb"^(@@|\$|\{|<|\*|x+$|your|changeme|wachtwoord|password|example|voorbeeld|0123456789|\(|\\S)", re.I)
CRED = re.compile(rb"(?i)\b(password|passwd|psk|secret|token|apikey)\s*[=:]\s*\"?([^\s\"']{4,})")
IP = re.compile(rb"\b(192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b")
MAC = re.compile(rb"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b")
EMAIL = re.compile(rb"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
WB_NAMES = {b"loadwb", b"setpatch", b"iprefs", b"workbench.library", b"icon.library",
            b"printer.device", b"parallel.device", b"serial.device", b"multiview",
            b"conclip", b"addbuffers", b"assign", b"execute", b"installer"}
BROADCAST_OK = {b"ff:ff:ff:ff:ff:ff", b"00:00:00:00:00:00"}


def load_secrets(path):
    lits, names = [], []
    if path and os.path.exists(path):
        for line in open(path, "rb").read().splitlines():
            line = line.strip()
            if not line or line.startswith(b"#"):
                continue
            if line.startswith(b"name:"):
                names.append(line[5:].strip().lower())
            else:
                lits.append(line)
    return lits, names


class Scanner:
    def __init__(self, secrets, names, strict_ip):
        self.secrets, self.names, self.strict_ip = secrets, names, strict_ip
        self.findings = []

    def add(self, kind, where, detail, blocking=True):
        self.findings.append((kind, where, detail, blocking))

    def scan_bytes(self, where, data, depth=0):
        base = os.path.basename(where.split("!")[-1]).lower().encode()
        for s in self.secrets:
            if s in data:
                self.add("SECRET", where, "%d occurrence(s), value hidden" % data.count(s))
        low = data.lower()
        for n in self.names:
            if n in low:
                self.add("NAME", where, "private word #%d present" % (self.names.index(n) + 1))
        for m in CRED.finditer(data):
            val = m.group(2)
            if not PLACEHOLDER.match(val):
                self.add("CRED", where, "%s=<%d chars hidden>" % (m.group(1).decode(errors="replace"), len(val)))
        ips = sorted(set(IP.findall(data)))
        if ips:
            self.add("IP", where, " ".join(i.decode() for i in ips[:8]) + (" ..." if len(ips) > 8 else ""),
                     blocking=self.strict_ip)
        macs = sorted(set(m.lower() for m in MAC.findall(data)) - BROADCAST_OK)
        if macs:
            self.add("MAC", where, " ".join(m.decode() for m in macs[:6]))
        mails = sorted(set(EMAIL.findall(data)))
        if mails:
            self.add("EMAIL", where, "%d address(es)" % len(mails), blocking=False)
        if len(data) in (262144, 524288) and data[:4] in (b"\x11\x11\x4e\xf9", b"\x11\x14\x4e\xf9"):
            self.add("ROM", where, "Kickstart ROM image")
        if base in WB_NAMES:
            self.add("WB", where, "name matches a Workbench component")
        if base.endswith((b".adf", b".hdf")):
            hits = [n.decode() for n in WB_NAMES if re.search(rb"(?i)\b" + re.escape(n) + rb"\b", data[:2_000_000])]
            if len(hits) >= 3:
                self.add("WB", where, "image contains Workbench file names: " + ", ".join(sorted(hits)[:6]))
        if depth < 3:
            self.scan_archive(where, data, depth)

    def scan_archive(self, where, data, depth):
        try:
            if data[:2] == b"PK":
                z = zipfile.ZipFile(io.BytesIO(data))
                for i in z.infolist():
                    if not i.is_dir():
                        self.scan_bytes(where + "!" + i.filename, z.read(i), depth + 1)
            elif data[:2] == b"\x1f\x8b" or data[257:262] == b"ustar":
                t = tarfile.open(fileobj=io.BytesIO(data))
                for m in t.getmembers():
                    if m.isfile():
                        self.scan_bytes(where + "!" + m.name, t.extractfile(m).read(), depth + 1)
        except Exception:
            pass

    def scan_path(self, path):
        if os.path.isdir(path):
            for dp, dn, fn in os.walk(path):
                dn[:] = [d for d in dn if d != ".git"]
                for f in sorted(fn):
                    self.scan_path(os.path.join(dp, f))
            return
        try:
            with open(path, "rb") as fh:
                self.scan_bytes(path, fh.read())
        except OSError as e:
            self.add("ERROR", path, str(e))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secrets", default=os.path.expanduser("~/.lsn-secrets"))
    ap.add_argument("--strict-ip", action="store_true")
    ap.add_argument("--allow", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "publish-check.allow"))
    ap.add_argument("paths", nargs="+")
    a = ap.parse_args()
    lits, names = load_secrets(a.secrets)
    sc = Scanner(lits, names, a.strict_ip)
    for p in a.paths:
        sc.scan_path(p)
    allow = []
    if a.allow and os.path.exists(a.allow):
        for line in open(a.allow, encoding="utf-8"):
            if line.strip() and not line.startswith("#"):
                k, suffix, reason = line.rstrip("\n").split("\t", 2)
                allow.append((k, suffix))
    blocking = 0
    for kind, where, detail, block in sc.findings:
        allowed = any(kind == k and where.endswith(sfx) for k, sfx in allow)
        state = "allow" if (block and allowed) else ("BLOCK" if block else "note")
        blocking += state == "BLOCK"
        print("%s\t%s\t%s\t%s" % (state, kind, where, detail))
    print("# secrets loaded: %d literal, %d private words; findings: %d (%d blocking)"
          % (len(lits), len(names), len(sc.findings), blocking), file=sys.stderr)
    sys.exit(1 if blocking else 0)


if __name__ == "__main__":
    main()
