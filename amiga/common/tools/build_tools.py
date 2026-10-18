#!/usr/bin/env python3
"""build_tools.py - assemble the small 68000 helper tools with asm68k.py.

    python3 build_tools.py OUTDIR [NAME...]      (default: WiFiVraag Geladen VrijKB)

Each NAME.s in this directory becomes OUTDIR/NAME, an AmigaOS hunk executable
(one CODE hunk, no relocations). A source may contain a line with only PAD:
it is assembled once with nothing there and, if its variable block ("vars")
is then not longword aligned, once more with one padding word. This is the
same rule the original build kits used.

The SHA-256 of every result is checked against tools.sha256 next to this file;
a mismatch is an error. Requires Python 3.8+ only.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asm68k  # noqa: E402


def assemble(name):
    src = open(os.path.join(HERE, name + ".s"), encoding="latin-1").read()
    for pad in ("", "        dc.w    0"):
        a = asm68k.Asm(src.replace("\nPAD\n", "\n" + pad + "\n"))
        code = a.assemble()
        if "\nPAD\n" not in src or "vars" not in a.sym or a.sym["vars"] % 4 == 0:
            break
    else:
        raise SystemExit(f"{name}: vars not longword aligned")
    return asm68k.hunk_exe(code)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    out = sys.argv[1]
    names = sys.argv[2:] or ["WiFiVraag", "Geladen", "VrijKB"]
    want = {}
    for line in open(os.path.join(HERE, "tools.sha256"), encoding="ascii"):
        if line.strip() and not line.startswith("#"):
            h, n = line.split()
            want[n] = h
    os.makedirs(out, exist_ok=True)
    bad = 0
    for n in names:
        exe = assemble(n)
        h = hashlib.sha256(exe).hexdigest()
        with open(os.path.join(out, n), "wb") as f:
            f.write(exe)
        ok = want.get(n) == h
        bad += not ok
        print(f"{'OK  ' if ok else 'FOUT'} {n:10} {len(exe):5} bytes  {h}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
