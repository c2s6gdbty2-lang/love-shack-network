#!/usr/bin/env python3
"""build-adf.py - build out/AmiAgent-Installatie.adf (volume AmiAgent-Installatie).

Sources, all inside this repository (paths relative to this file):
  - ../out/agent/amiagent (READONLY build) and ../out/agent/amimon from build-agent.sh;
  - WiFiVraag, Geladen, VrijKB: assembled from amiga/common/tools/*.s by
    build_tools.py (SHA-256 checked there);
  - CRCLijst: the binary in amiga/a600/A600AirPrint/C (source in its Docs/);
  - the scripts and LeesMij next to this directory, the icons in ../icons;
  - the drawer icon is this project's own A600AirPrint drawer (Hulp/Lade.info);
    the disk icon uses the A600AirPrint Disk.info only as a structure template
    (type, window, default tool) with its own image from amiagent_icons.py;
    both get the window size of the tested disk;
  - ../patches and the upstream licence as documentation;
  - NOTICE-runtime-newlib.txt (the newlib notices for the linked C runtime) at the disk root.

There is NO token and NO address on the disk: Installeer asks for the token.
amiagent-rw-test is never put on the disk.

Needs Python 3.8+ and xdftool (pip install amitools); set XDFTOOL=/path/to/xdftool
if it is not on PATH. After writing, every file is read back from the ADF and
compared byte for byte.
"""
import hashlib
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # .../AmiAgent
REPO = os.path.abspath(os.path.join(K, "..", "..", ".."))
TOOLS = os.path.join(REPO, "amiga", "common", "tools")
A600 = os.path.join(REPO, "amiga", "a600", "A600AirPrint")
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(K, "build"))
import icon  # noqa: E402
import amiagent_icons  # noqa: E402

CRCLIJST_SHA = "e142b87623452902eb5fe821371b9551b4d687f4e863df364ea02174b49d53ef"
VOL = "AmiAgent-Installatie"
OUT = os.path.join(K, "out")
XDF = os.environ.get("XDFTOOL") or shutil.which("xdftool")
sha = lambda b: hashlib.sha256(b).hexdigest()
rd = lambda p: open(p, "rb").read()


def text(p):
    b = rd(p)
    assert all(c in (9, 10) or 32 <= c < 127 for c in b), "non-ASCII character in " + p
    return b


def drawer_icon(template, left, top, width, height, image=None):
    """Same as the original kit: template icon, new window box, scroll offset 0, no fixed position.
    With image=, the template's picture is replaced (and its selected image dropped)."""
    d = icon.parse(rd(template))
    if image is not None:
        d["image1"], d["image2"] = image, None
        d["gadget"] = dict(d["gadget"], w=image["w"], h=image["h"] + 1, flags=4)
    dd = bytearray(d["drawer"])
    struct.pack_into(">hhhh", dd, 0, left, top, width, height)
    struct.pack_into(">ii", dd, 48, 0, 0)
    d["drawer"] = bytes(dd)
    d["x"], d["y"] = icon.NO_ICON_POSITION, icon.NO_ICON_POSITION
    return icon.build(d)


def xdf(*args, **kw):
    return subprocess.run([XDF] + list(args), check=True, **kw)


def main():
    if not XDF:
        sys.exit("xdftool not found: pip install amitools, or set XDFTOOL")
    agent = rd(os.path.join(OUT, "agent", "amiagent"))
    assert b"lsn1 READONLY" in agent, "amiagent is not the READONLY build"
    tools = os.path.join(OUT, "tools")
    subprocess.run([sys.executable, "-I", "-B", os.path.join(TOOLS, "build_tools.py"), tools], check=True)
    crc = rd(os.path.join(A600, "C", "CRCLijst"))
    assert sha(crc) == CRCLIJST_SHA, "unexpected CRCLijst"

    p = os.path.join(OUT, VOL)
    shutil.rmtree(p, ignore_errors=True)
    for d in ("C", "S", "AmiAgent/C", "AmiAgent/Docs"):
        os.makedirs(os.path.join(p, d))
    w = lambda rel, b: open(os.path.join(p, rel), "wb").write(b)
    for f in ("Installeer", "Verwijderen", "LeesMij"):
        w(f, text(os.path.join(K, f)))
    # Notices for the C runtime linked into amiagent/amimon (BSD-style terms require them in the
    # documentation of a binary distribution). At the disk root, so the installer and its CRC list
    # stay exactly as tested.
    w("NOTICE-runtime-newlib", text(os.path.join(K, "NOTICE-runtime-newlib.txt")))
    w("AmiAgent/LeesMij", text(os.path.join(K, "LeesMij")))
    for f in ("AmiAgent Start", "AmiAgent Stop"):
        w("AmiAgent/" + f, text(os.path.join(K, f)))
    w("AmiAgent/amiagent", agent)
    w("AmiAgent/AmiAgent Status", rd(os.path.join(OUT, "agent", "amimon")))
    w("AmiAgent/C/Geladen", rd(os.path.join(tools, "Geladen")))
    for f in ("VrijKB", "WiFiVraag"):
        w("C/" + f, rd(os.path.join(tools, f)))
    w("C/CRCLijst", crc)
    # Apache-2.0 4(a) and 4(d): the licence text and upstream NOTICE travel with the agent.
    for f, up in (("LICENSE-amimcp", "LICENSE"), ("NOTICE-amimcp", "NOTICE")):
        b = rd(os.path.join(K, f))
        assert b == rd(os.path.join(K, "upstream", up)), f + " differs from the pinned upstream " + up
        w("AmiAgent/Docs/" + f, b)
    for f in sorted(os.listdir(os.path.join(K, "patches"))):
        w("AmiAgent/Docs/" + f, rd(os.path.join(K, "patches", f)))

    ic = os.path.join(K, "icons")
    for s, dd in (("AmiAgent Start.info", "AmiAgent/AmiAgent Start.info"),
                  ("AmiAgent Stop.info", "AmiAgent/AmiAgent Stop.info"),
                  ("amimon.info", "AmiAgent/AmiAgent Status.info"),
                  ("AmiAgent-LeesMij.info", "AmiAgent/LeesMij.info"),
                  ("LeesMij.info", "LeesMij.info"),
                  ("Installeer.info", "Installeer.info"),
                  ("Verwijderen.info", "Verwijderen.info")):
        w(dd, rd(os.path.join(ic, s)))
    w("AmiAgent.info", drawer_icon(os.path.join(A600, "Hulp", "Lade.info"), 40, 30, 440, 90))
    w("Disk.info", drawer_icon(os.path.join(A600, "Disk.info"), 40, 30, 320, 80,
                               image=icon.image_from_art(amiagent_icons.disk_art())))

    lst = ["# CRCLijst 1.0: crc32 grootte pad"]
    for root, _, files in sorted(os.walk(os.path.join(p, "AmiAgent"))):
        for f in sorted(files):
            fp = os.path.join(root, f); b = rd(fp)
            rel = os.path.relpath(fp, os.path.join(p, "AmiAgent"))
            lst.append("%08x %d Work:AmiAgent/%s" % (zlib.crc32(b), len(b), rel))
    w("S/Bestanden.crc", ("\n".join(lst) + "\n").encode())

    adf = os.path.join(OUT, "AmiAgent-Installatie.adf")
    if os.path.exists(adf):
        os.remove(adf)
    xdf(adf, "create", "+", "format", VOL, "ffs", stdout=subprocess.DEVNULL)
    files = []
    for root, dirs, fs in sorted(os.walk(p)):
        rel = os.path.relpath(root, p)
        for d in sorted(dirs):
            xdf(adf, "makedir", os.path.normpath(os.path.join(rel, d)))
        for f in sorted(fs):
            files.append(os.path.normpath(os.path.join(rel, f)))
            xdf(adf, "write", os.path.join(root, f), files[-1])
    for f in ("Installeer", "Verwijderen", "AmiAgent/AmiAgent Start", "AmiAgent/AmiAgent Stop"):
        xdf(adf, "protect", f, "srwed")

    # Read every file back from the image.
    with tempfile.TemporaryDirectory() as t:
        for f in files:
            dst = os.path.join(t, f.replace("/", "_"))
            xdf(adf, "read", f, dst, stdout=subprocess.DEVNULL)
            assert rd(dst) == rd(os.path.join(p, f)), "read-back differs: " + f
    man = ["AmiAgent 1.0 (amiagent 0.13.2-lsn1 READONLY) - installatiedisk (volume %s)" % VOL,
           "ADF sha256 %s (not byte-reproducible: xdftool stores the build time)" % sha(rd(adf)), ""]
    for f in sorted(files):
        fp = os.path.join(p, f)
        man.append("%s  %7d  %s" % (sha(rd(fp)), os.path.getsize(fp), f))
    open(os.path.join(OUT, "MANIFEST.txt"), "w").write("\n".join(man) + "\n")
    print("\n".join(man))
    print("read-back: %d files identical" % len(files))


if __name__ == "__main__":
    main()
