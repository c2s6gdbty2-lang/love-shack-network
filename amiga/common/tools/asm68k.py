#!/usr/bin/env python3
"""
asm68k.py - small two-pass Motorola 68000 assembler that writes an AmigaOS
hunk executable (one CODE hunk, no relocations).

Supports exactly the 68000 subset used by A600NetStart.s (Motorola syntax):
  move/movea/moveq/movem/lea/pea/clr/tst/neg/swap/ext, add/sub/and/or/cmp,
  addi/subi/andi/ori/cmpi, addq/subq, divu/divs/mulu/muls (.w),
  lsl/lsr/asl/asr (#imm and Dn counts), bra/bsr/bcc (.w), dbra/dbcc,
  jsr/jmp, rts, nop; directives equ, dc.b/dc.w/dc.l, ds.b, even, end.
Every addressing mode is range checked; nothing outside the 68000 ISA can be
emitted.  Usage: asm68k.py source.s output [--list listing.txt]
"""
import re
import struct
import sys

CC = {"t": 0, "ra": 0, "f": 1, "sr": 1, "hi": 2, "ls": 3, "cc": 4, "hs": 4, "cs": 5, "lo": 5,
      "ne": 6, "eq": 7, "vc": 8, "vs": 9, "pl": 10, "mi": 11, "ge": 12, "lt": 13, "gt": 14, "le": 15}
SZ = {"b": 0, "w": 1, "l": 2}


class AsmError(Exception):
    pass


def split_ops(s):
    out, cur, depth, q = [], "", 0, None
    for ch in s:
        if q:
            cur += ch
            if ch == q:
                q = None
            continue
        if ch in "\"'":
            q = ch; cur += ch; continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip()); cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


class Asm:
    def __init__(self, text):
        self.lines = text.splitlines()
        self.sym = {}
        self.listing = []

    # -------------------------------------------------------------- expressions
    def ev(self, e, final):
        e = e.strip()
        def num(m):
            t = m.group(0)
            if t.startswith("$"):
                return str(int(t[1:], 16))
            if t.startswith("%"):
                return str(int(t[1:], 2))
            return t
        e2 = re.sub(r"\$[0-9A-Fa-f]+|%[01]+", num, e)
        def symr(m):
            n = m.group(0)
            if re.fullmatch(r"0[xX][0-9a-fA-F]+|\d+", n):
                return n
            if n in self.sym:
                return str(self.sym[n])
            if final:
                raise AsmError("undefined symbol " + n)
            return "0"
        e3 = re.sub(r"[A-Za-z_.][A-Za-z0-9_.]*|0[xX][0-9a-fA-F]+|\d+", symr, e2)
        if not re.fullmatch(r"[0-9xXa-fA-F+\-*/()<> |&~ ]*", e3):
            raise AsmError("bad expression " + e)
        return int(eval(e3.replace("/", "//")))

    # -------------------------------------------------------------- EA parsing
    def ea(self, op, size, pc_ext, final):
        """Return (mode, reg, extbytes).  pc_ext = address of the extension word."""
        o = op.strip()
        lo = o.lower()
        r = re.fullmatch(r"([da])([0-7])|sp", lo)
        if r:
            if lo == "sp":
                return 1, 7, b""
            return (0 if r.group(1) == "d" else 1), int(r.group(2)), b""
        m = re.fullmatch(r"\((a[0-7]|sp)\)(\+?)", lo)
        if m:
            reg = 7 if m.group(1) == "sp" else int(m.group(1)[1])
            return (3 if m.group(2) else 2), reg, b""
        m = re.fullmatch(r"-\((a[0-7]|sp)\)", lo)
        if m:
            reg = 7 if m.group(1) == "sp" else int(m.group(1)[1])
            return 4, reg, b""
        m = re.fullmatch(r"(.+)\((a[0-7]|sp|pc)\)", o, re.I)
        if m:
            d = self.ev(m.group(1), final)
            base = m.group(2).lower()
            if base == "pc":
                disp = d - pc_ext
                if final and not -32768 <= disp <= 32767:
                    raise AsmError("pc displacement out of range")
                return 7, 2, struct.pack(">h", disp if final else 0)
            if final and not -32768 <= d <= 32767:
                raise AsmError("d16 out of range")
            reg = 7 if base == "sp" else int(base[1])
            return 5, reg, struct.pack(">h", d)
        if o.startswith("#"):
            v = self.ev(o[1:], final)
            if size == 2:
                return 7, 4, struct.pack(">I", v & 0xFFFFFFFF)
            if size == 1:
                return 7, 4, struct.pack(">H", v & 0xFFFF)
            return 7, 4, struct.pack(">H", v & 0xFF)
        m = re.fullmatch(r"(.+)\.w", o, re.I)
        if m:
            return 7, 0, struct.pack(">h", self.ev(m.group(1), final))
        m = re.fullmatch(r"(.+?)(\.l)?", o, re.I)
        return 7, 1, struct.pack(">I", self.ev(m.group(1), final) & 0xFFFFFFFF)

    @staticmethod
    def dreg(op):
        m = re.fullmatch(r"d([0-7])", op.strip().lower())
        if not m:
            raise AsmError("data register expected: " + op)
        return int(m.group(1))

    @staticmethod
    def areg(op):
        lo = op.strip().lower()
        if lo == "sp":
            return 7
        m = re.fullmatch(r"a([0-7])", lo)
        if not m:
            raise AsmError("address register expected: " + op)
        return int(m.group(1))

    @staticmethod
    def reglist(s):
        mask = 0
        for part in s.lower().split("/"):
            if "-" in part:
                a, b = part.split("-")
                ia = (0 if a[0] == "d" else 8) + int(a[1]); ib = (0 if b[0] == "d" else 8) + int(b[1])
                for i in range(ia, ib + 1):
                    mask |= 1 << i
            else:
                mask |= 1 << ((0 if part[0] == "d" else 8) + int(part[1]))
        return mask

    # -------------------------------------------------------------- instructions
    def encode(self, mn, ops, pc, final):
        base, _, sfx = mn.lower().partition(".")
        size = SZ.get(sfx, 1 if base not in ("moveq", "lea", "pea", "jsr", "jmp", "swap") else 2)
        o = split_ops(ops) if ops else []
        W = lambda *ws: b"".join(struct.pack(">H", w & 0xFFFF) for w in ws)

        def branch_disp(target):
            disp = self.ev(target, final) - (pc + 2)
            if final and not -32768 <= disp <= 32767:
                raise AsmError("branch out of range")
            return disp if final else 0

        if base in ("rts", "nop"):
            return W(0x4E75 if base == "rts" else 0x4E71)
        if base == "moveq":
            v = self.ev(o[0].lstrip("#"), final)
            if final and not -128 <= v <= 127:
                raise AsmError("moveq out of range")
            return W(0x7000 | self.dreg(o[1]) << 9 | (v & 0xFF))
        if base in ("bra", "bsr") or (base[0] == "b" and base[1:] in CC and base not in ("btst",)):
            cc = 0 if base == "bra" else 1 if base == "bsr" else CC[base[1:]]
            if sfx not in ("w", ""):
                raise AsmError("only .w branches are supported")
            return W(0x6000 | cc << 8, branch_disp(o[0]))
        if base in ("dbra", "dbf") or (base.startswith("db") and base[2:] in CC):
            cc = 1 if base in ("dbra", "dbf") else CC[base[2:]]
            return W(0x50C8 | cc << 8 | self.dreg(o[0]), branch_disp(o[1]))
        if base in ("jsr", "jmp", "pea"):
            m, r, x = self.ea(o[0], 2, pc + 2, final)
            if m in (0, 1, 3, 4) or (m == 7 and r == 4):
                raise AsmError("illegal EA for " + base)
            return W({"jsr": 0x4E80, "jmp": 0x4EC0, "pea": 0x4840}[base] | m << 3 | r) + x
        if base == "lea":
            m, r, x = self.ea(o[0], 2, pc + 2, final)
            if m in (0, 1, 3, 4) or (m == 7 and r == 4):
                raise AsmError("illegal EA for lea")
            return W(0x41C0 | self.areg(o[1]) << 9 | m << 3 | r) + x
        if base == "movem":
            if sfx not in ("w", "l"):
                raise AsmError("movem needs .w/.l")
            szb = 0x40 if sfx == "l" else 0
            if re.fullmatch(r"-\((sp|a7)\)", o[1].lower()):
                mask = self.reglist(o[0])
                rev = int("{:016b}".format(mask)[::-1], 2)
                return W(0x4880 | szb | 0x27, rev)
            if re.fullmatch(r"\((sp|a7)\)\+", o[0].lower()):
                return W(0x4C80 | szb | 0x1F, self.reglist(o[1]))
            raise AsmError("unsupported movem form")
        if base in ("move", "movea"):
            szcode = {0: 1, 1: 3, 2: 2}[size]
            m1, r1, x1 = self.ea(o[0], size, pc + 2, final)
            m2, r2, x2 = self.ea(o[1], size, pc + 2 + len(x1), final)
            if (m2 == 7 and r2 >= 2) or (m2 == 1 and size == 0) or (m1 == 1 and size == 0):
                raise AsmError("illegal move destination/size")
            return W(szcode << 12 | r2 << 9 | m2 << 6 | m1 << 3 | r1) + x1 + x2
        if base in ("clr", "tst", "neg", "not"):
            m, r, x = self.ea(o[0], size, pc + 2, final)
            if m == 1 or (m == 7 and r >= 2 and base != "tst") or (base == "tst" and m == 7 and r >= 2):
                raise AsmError("illegal EA for " + base + " on 68000")
            op = {"clr": 0x4200, "tst": 0x4A00, "neg": 0x4400, "not": 0x4600}[base]
            return W(op | size << 6 | m << 3 | r) + x
        if base == "swap":
            return W(0x4840 | self.dreg(o[0]))
        if base == "ext":
            return W((0x4880 if size == 1 else 0x48C0) | self.dreg(o[0]))
        if base in ("addi", "subi", "andi", "ori", "cmpi", "eori"):
            imm_m, _, imm = self.ea(o[0], size, pc + 2, final)
            m, r, x = self.ea(o[1], size, pc + 2 + len(imm), final)
            if m == 1 or (m == 7 and r >= 2):
                raise AsmError("illegal destination for " + base)
            op = {"ori": 0x0000, "andi": 0x0200, "subi": 0x0400, "addi": 0x0600, "eori": 0x0A00, "cmpi": 0x0C00}[base]
            return W(op | size << 6 | m << 3 | r) + imm + x
        if base in ("addq", "subq"):
            v = self.ev(o[0].lstrip("#"), final)
            if final and not 1 <= v <= 8:
                raise AsmError("addq/subq range 1..8")
            m, r, x = self.ea(o[1], size, pc + 2, final)
            if m == 1 and size == 0:
                raise AsmError("byte addq to An")
            return W(0x5000 | (0x100 if base == "subq" else 0) | (v & 7) << 9 | size << 6 | m << 3 | r) + x
        if base in ("add", "sub", "and", "or", "cmp"):
            dst = o[1].strip().lower()
            opbase = {"add": 0xD000, "sub": 0x9000, "and": 0xC000, "or": 0x8000, "cmp": 0xB000}[base]
            if re.fullmatch(r"d[0-7]", dst):
                m, r, x = self.ea(o[0], size, pc + 2, final)
                if m == 1 and base in ("and", "or"):
                    raise AsmError("An source illegal for and/or")
                return W(opbase | self.dreg(dst) << 9 | size << 6 | m << 3 | r) + x
            raise AsmError("only <ea>,Dn forms supported for " + base)
        if base in ("divu", "divs", "mulu", "muls"):
            if sfx not in ("w", ""):
                raise AsmError("68000 only has 16-bit mul/div")
            m, r, x = self.ea(o[0], 1, pc + 2, final)
            op = {"divu": 0x80C0, "divs": 0x81C0, "mulu": 0xC0C0, "muls": 0xC1C0}[base]
            return W(op | self.dreg(o[1]) << 9 | m << 3 | r) + x
        if base in ("lsl", "lsr", "asl", "asr"):
            kind = {"as": 0, "ls": 1}[base[:2]]
            left = 1 if base[2] == "l" else 0
            if o[0].startswith("#"):
                v = self.ev(o[0][1:], final)
                if final and not 1 <= v <= 8:
                    raise AsmError("shift count 1..8")
                return W(0xE000 | (v & 7) << 9 | left << 8 | size << 6 | kind << 3 | self.dreg(o[1]))
            return W(0xE000 | self.dreg(o[0]) << 9 | left << 8 | size << 6 | 0x20 | kind << 3 | self.dreg(o[1]))
        raise AsmError("unsupported instruction " + mn)

    # -------------------------------------------------------------- passes
    def data(self, directive, args, final):
        d = directive.lower()
        if d == "dc.b":
            out = b""
            for a in split_ops(args):
                if a[0] in "\"'":
                    out += a[1:-1].encode("latin-1")
                else:
                    out += bytes([self.ev(a, final) & 0xFF])
            return out
        if d == "dc.w":
            return b"".join(struct.pack(">H", self.ev(a, final) & 0xFFFF) for a in split_ops(args))
        if d == "dc.l":
            return b"".join(struct.pack(">I", self.ev(a, final) & 0xFFFFFFFF) for a in split_ops(args))
        if d == "ds.b":
            return bytes(self.ev(args, final))
        raise AsmError("unknown directive " + directive)

    def run(self, final):
        pc = 0
        out = bytearray()
        for ln, raw in enumerate(self.lines, 1):
            line = raw
            # strip comments (outside strings)
            q = None
            for i, ch in enumerate(line):
                if q:
                    if ch == q:
                        q = None
                elif ch in "\"'":
                    q = ch
                elif ch == ";":
                    line = line[:i]; break
            if not line.strip():
                continue
            try:
                m = re.match(r"^([A-Za-z_.][A-Za-z0-9_.]*):?\s+(equ)\s+(.*)$", line.strip(), re.I)
                if m and not line[0].isspace():
                    self.sym[m.group(1)] = self.ev(m.group(3), final)
                    continue
                label = None
                if not line[0].isspace():
                    first = line.split()[0]
                    if first.endswith(":"):
                        label = first[:-1]
                        line = line[line.index(":") + 1:]
                    else:
                        label = first
                        line = line[len(first):]
                    if label:
                        if label in self._labels_seen:
                            raise AsmError("duplicate label " + label)
                        self.sym[label] = pc
                        self._labels_seen.add(label)
                parts = line.strip().split(None, 1)
                if not parts:
                    continue
                mn = parts[0]
                args = parts[1] if len(parts) > 1 else ""
                low = mn.lower()
                if low == "end":
                    break
                if low == "even":
                    if pc & 1:
                        out += b"\0"; pc += 1
                    continue
                if low in ("dc.b", "dc.w", "dc.l", "ds.b"):
                    if low != "dc.b" and low != "ds.b" and pc & 1:
                        raise AsmError("odd address for " + low)
                    b = self.data(low, args, final)
                else:
                    if pc & 1:
                        raise AsmError("instruction at odd address")
                    b = self.encode(mn, args, pc, final)
                    if final:
                        self.listing.append((pc, b, mn, args, ln))
                out += b
                pc += len(b)
            except AsmError as e:
                raise AsmError("line %d: %s  [%s]" % (ln, e, raw.strip()))
        return bytes(out)

    def assemble(self):
        self._labels_seen = set()
        self.run(False)
        self._labels_seen = set()
        first = self.run(False)            # labels now stable (all branches fixed .w)
        self._labels_seen = set()
        code = self.run(True)
        if len(code) != len(first):
            raise AsmError("size changed between passes")
        return code


def hunk_exe(code):
    code = code + b"\0" * (-len(code) % 4)
    n = len(code) // 4
    return struct.pack(">IIIIII", 0x3F3, 0, 1, 0, 0, n) + struct.pack(">II", 0x3E9, n) + code + struct.pack(">I", 0x3F2)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    a = Asm(open(src, encoding="latin-1").read())
    code = a.assemble()
    open(dst, "wb").write(hunk_exe(code))
    if "--list" in sys.argv:
        with open(sys.argv[sys.argv.index("--list") + 1], "w") as f:
            for pc, b, mn, args, ln in a.listing:
                f.write("%06x  %-24s %-8s %s\n" % (pc, b.hex(), mn, args))
    print("%s: %d bytes code, %d bytes file" % (dst, len(code), len(hunk_exe(code))))
