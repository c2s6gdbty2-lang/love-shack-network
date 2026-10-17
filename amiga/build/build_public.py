#!/usr/bin/env python3
"""build_public.py - build the public A600AirPrint / AirPrintPS floppy images.

The package trees in this repository are the files that were tested on real
hardware. The only difference is that network details are written as tokens:

    @@PRINTER_NAME@@  @@PRINTER_HOST@@  @@PRINTER_PORT@@  @@PRINTER_PATH@@

This script fills the tokens from an INI file. For A600AirPrint it also
regenerates the checksum lists that Installeer uses to verify its copy
(Hulp/Doel-31.lst, Hulp/Doel-32.lst), using the same algorithm as the original
build. Finally it writes an FFS ADF and reads every file back from it.

Requires Python 3.8+ and amitools (`pip install amitools`, which provides xdftool).

    python3 build_public.py --package a600 --config network.ini --out out/
    python3 build_public.py --package airprintps --config network.ini --out out/
"""
import argparse
import configparser
import hashlib
import os
import re
import shutil
import subprocess
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
AMIGA = os.path.dirname(HERE)

PACKAGES = {
    "a600": dict(tree=os.path.join(AMIGA, "a600", "A600AirPrint"), volume="A600AirPrint",
                 adf="A600AirPrint-public.adf",
                 scripts=["Controle", "Installeer", "Verwijderen", "ControleerPrinter", "TestTekst", "TestGrafiek",
                          "Hulp/Zoekwoord", "Hulp/Poortcheck", "Hulp/Poortmelding"]),
    "airprintps": dict(tree=os.path.join(AMIGA, "a500-pistorm", "AirPrintPS"), volume="AirPrintPS",
                       adf="AirPrintPS-public.adf",
                       scripts=["Inventaris", "Installeer", "Verwijderen", "ControleerPrinter", "TestTekst",
                                "TestGrafiek"]),
}
TOKEN_RE = re.compile(rb"@@PRINTER_(NAME|HOST|PORT|PATH)@@")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load_config(path):
    cp = configparser.ConfigParser()
    if not cp.read(path, encoding="utf-8"):
        sys.exit("ERROR: cannot read %s" % path)
    p = cp["printer"]
    v = {"NAME": p.get("name", "printer").strip(), "HOST": p["host"].strip(),
         "PORT": p.get("port", "631").strip(), "PATH": p.get("path", "/ipp/print").strip()}
    if not re.fullmatch(r"[A-Za-z0-9 ._-]{1,30}", v["NAME"]):
        sys.exit("ERROR: printer name: 1-30 characters, letters/digits/space/._-")
    ip = re.fullmatch(r"(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})", v["HOST"])
    if ip:
        for part in ip.groups():
            # AmiTCP reads a leading zero as octal, so 192.168.001.050 would be wrong
            if int(part) > 255 or (len(part) > 1 and part[0] == "0"):
                sys.exit("ERROR: printer host %r is not a valid IPv4 address" % v["HOST"])
    elif not re.fullmatch(r"[A-Za-z0-9.-]{1,63}", v["HOST"]):
        sys.exit("ERROR: printer host must be an IPv4 address or a host name")
    if not v["PORT"].isdigit() or not 1 <= int(v["PORT"]) <= 65535:
        sys.exit("ERROR: printer port must be 1-65535")
    if not re.fullmatch(r"/[A-Za-z0-9/._-]{0,62}", v["PATH"]):
        sys.exit("ERROR: printer path must start with / (for example /ipp/print)")
    return {k: s.encode("latin-1") for k, s in v.items()}


def fill_tree(src, dst, values):
    shutil.rmtree(dst, ignore_errors=True)
    for root, _, files in os.walk(src):
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(root, f), src)
            data = open(os.path.join(root, f), "rb").read()
            data = TOKEN_RE.sub(lambda m: values[m.group(1).decode()], data)
            out = os.path.join(dst, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, "wb").write(data)
    left = [os.path.relpath(os.path.join(r, f), dst) for r, _, fs in os.walk(dst) for f in fs
            if TOKEN_RE.search(open(os.path.join(r, f), "rb").read())]
    if left:
        sys.exit("ERROR: unfilled tokens in %s" % left)


def crc_line(data, path):
    return "%08x %d %s" % (zlib.crc32(data) & 0xFFFFFFFF, len(data), path)


def a600_lists(tree):
    """Same content and order as the original A600AirPrint build (Installeer step [4])."""
    rd = lambda rel: open(os.path.join(tree, rel), "rb").read()
    hulp = ["Zoekwoord", "Poortcheck", "Poortmelding"]
    work = ["Controle", "Controle.info", "ControleerPrinter", "ControleerPrinter.info", "TestTekst", "TestTekst.info",
            "TestGrafiek", "TestGrafiek.info", "Verwijderen", "Verwijderen.info", "LeesMij", "LeesMij.info",
            "TestBeeld.iff", "C/AirPrintProbe", "C/CRCLijst"] + ["Hulp/" + f for f in hulp] + \
           ["Docs/" + f for f in ("AmiAirPrint.readme", "AmiAirPrint-LICENSE", "AmiAirPrint-1.2-ps1.diff", "crclijst.c")]
    for variant, prefs in (("31", "AmiAirPrintPrefsClassic"), ("32", "AmiAirPrintPrefs")):
        lines = ["# A600AirPrint: verwachte inhoud na Installeer (Workbench %s)" % variant,
                 crc_line(rd("Bestanden/airprint.device"), "DEVS:airprint.device"),
                 crc_line(rd("Bestanden/AirPrint"), "DEVS:Printers/AirPrint"),
                 crc_line(rd("Bestanden/" + prefs), "SYS:Prefs/AmiAirPrint"),
                 crc_line(rd("Bestanden/AmiAirPrint.info"), "SYS:Prefs/AmiAirPrint.info"),
                 crc_line(rd("Bestanden/AirPrint.prefs"), "ENVARC:AirPrint.prefs"),
                 crc_line(rd("Hulp/Lade.info"), "Work:A600AirPrint.info")]
        lines += [crc_line(rd(f), "Work:A600AirPrint/" + f) for f in work]
        open(os.path.join(tree, "Hulp", "Doel-%s.lst" % variant), "wb").write(("\n".join(lines) + "\n").encode())


def sha_list(tree):
    lines = []
    for root, _, files in os.walk(tree):
        for f in sorted(files):
            p = os.path.join(root, f)
            lines.append("%s  %s" % (sha(p), os.path.relpath(p, tree).replace(os.sep, "/")))
    open(os.path.join(tree, "Docs", "SHA256.txt"), "wb").write(
        ("\n".join(sorted(lines, key=lambda l: l[66:])) + "\n").encode())


def xdftool():
    for cand in (os.environ.get("XDFTOOL"), shutil.which("xdftool"),
                 os.path.expanduser("~/.amitools-venv/bin/xdftool")):
        if cand and os.path.exists(cand):
            return cand
    sys.exit("ERROR: xdftool not found (pip install amitools, or set XDFTOOL)")


def make_adf(xdf, tree, adf, volume, scripts):
    if os.path.exists(adf):
        os.remove(adf)
    run = lambda *a: subprocess.run([xdf, adf, *a], check=True, capture_output=True, text=True)
    run("create")
    run("format", volume, "ffs")
    for root, dirs, files in os.walk(tree):
        dirs.sort()
        rel = os.path.relpath(root, tree)
        if rel != ".":
            run("makedir", rel.replace(os.sep, "/"))
        for f in sorted(files):
            run("write", os.path.join(root, f), f if rel == "." else rel.replace(os.sep, "/") + "/" + f)
    for s in scripts:
        run("protect", s, "srwed")   # the s bit lets IconX/Execute run the script


def verify_adf(xdf, tree, adf, volume, work):
    back = os.path.join(work, "readback")
    shutil.rmtree(back, ignore_errors=True)
    os.makedirs(back)
    subprocess.run([xdf, adf, "unpack", back], check=True, capture_output=True)
    n, bad = 0, []
    for root, _, files in os.walk(tree):
        for f in files:
            a = os.path.join(root, f)
            b = os.path.join(back, volume, os.path.relpath(a, tree))
            n += 1
            if not os.path.exists(b) or sha(a) != sha(b):
                bad.append(os.path.relpath(a, tree))
    shutil.rmtree(back)
    if bad:
        sys.exit("ERROR: ADF differs from tree: %s" % bad)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--package", choices=sorted(PACKAGES), required=True)
    ap.add_argument("--config", required=True, help="INI file with a [printer] section")
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    a = ap.parse_args()
    pk = PACKAGES[a.package]
    values = load_config(a.config)
    os.makedirs(a.out, exist_ok=True)
    tree = os.path.join(a.out, pk["volume"])
    fill_tree(pk["tree"], tree, values)
    if a.package == "a600":
        a600_lists(tree)
    sha_list(tree)
    xdf = xdftool()
    adf = os.path.join(a.out, pk["adf"])
    make_adf(xdf, tree, adf, pk["volume"], pk["scripts"])
    n = verify_adf(xdf, tree, adf, pk["volume"], a.out)
    print("OK: %d files read back identical from %s\nADF SHA-256 %s" % (n, adf, sha(adf)))


if __name__ == "__main__":
    main()
