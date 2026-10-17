#!/usr/bin/env python3
"""icon.py - lezen en schrijven van klassieke AmigaOS DiskObject-iconen (.info).

Alleen het OS 1.x/2.x/3.1-formaat (planaire Image-structuren, geen NewIcons of
ColorIcons). parse() en build() zijn elkaars inverse; build(parse(x)) == x wordt
getest op de WB 3.1-iconen.
"""
import struct

WBDISK, WBDRAWER, WBTOOL, WBPROJECT, WBGARBAGE = 1, 2, 3, 4, 5
NO_ICON_POSITION = 0x80000000


def _img_size(w, h, d):
    return ((w + 15) // 16) * 2 * h * d


def _read_image(b, o):
    le, te, w, h, d, data_ptr, pick, onoff, nxt = struct.unpack_from(">hhhhhIBBI", b, o)
    o += 20
    n = _img_size(w, h, d)
    img = dict(left=le, top=te, w=w, h=h, depth=d, pick=pick, onoff=onoff, data=b[o:o + n])
    return img, o + n


def _write_image(img):
    return struct.pack(">hhhhhIBBI", img["left"], img["top"], img["w"], img["h"], img["depth"],
                       1, img["pick"], img["onoff"], 0) + img["data"]


def _read_str(b, o):
    n, = struct.unpack_from(">I", b, o)
    s = b[o + 4:o + 4 + n]
    return s.rstrip(b"\0").decode("latin-1"), o + 4 + n


def _write_str(s):
    raw = s.encode("latin-1") + b"\0"
    return struct.pack(">I", len(raw)) + raw


def parse(b):
    magic, ver = struct.unpack_from(">HH", b, 0)
    if magic != 0xE310 or ver != 1:
        raise ValueError("geen DiskObject")
    g = struct.unpack_from(">IhhhhHHHIIIIIHI", b, 4)
    (g_next, g_left, g_top, g_w, g_h, g_flags, g_act, g_type, g_render, g_select,
     g_text, g_mutex, g_special, g_id, g_user) = g
    typ, pad, deftool, tooltypes, cx, cy, drawer, toolwin, stack = struct.unpack_from(">BBIIIIIII", b, 48)
    o = 78
    d = dict(gadget=dict(left=g_left, top=g_top, w=g_w, h=g_h, flags=g_flags, act=g_act,
                         gtype=g_type, user=g_user),
             type=typ, x=cx, y=cy, stack=stack, drawer=None, drawer2=None,
             image1=None, image2=None, deftool=None, tooltypes=None, toolwin=None)
    if drawer:
        d["drawer"] = b[o:o + 56]
        o += 56
    if g_render:
        d["image1"], o = _read_image(b, o)
    if g_select:
        d["image2"], o = _read_image(b, o)
    if deftool:
        d["deftool"], o = _read_str(b, o)
    if tooltypes:
        n, = struct.unpack_from(">I", b, o)
        o += 4
        tt = []
        for _ in range(n // 4 - 1):
            s, o = _read_str(b, o)
            tt.append(s)
        d["tooltypes"] = tt
    if toolwin:
        d["toolwin"], o = _read_str(b, o)
    if drawer and g_user == 1:
        d["drawer2"] = b[o:o + 6]
        o += 6
    d["rest"] = b[o:]
    return d


def build(d):
    g = d["gadget"]
    out = struct.pack(">HH", 0xE310, 1)
    out += struct.pack(">IhhhhHHHIIIIIHI", 0, g["left"], g["top"], g["w"], g["h"], g["flags"],
                       g["act"], g["gtype"], 1 if d["image1"] else 0, 1 if d["image2"] else 0,
                       0, 0, 0, 0, g["user"])
    out += struct.pack(">BBIIIIIII", d["type"], 0, 1 if d["deftool"] is not None else 0,
                       1 if d["tooltypes"] is not None else 0, d["x"], d["y"],
                       1 if d["drawer"] else 0, 1 if d["toolwin"] is not None else 0, d["stack"])
    if d["drawer"]:
        out += d["drawer"]
    if d["image1"]:
        out += _write_image(d["image1"])
    if d["image2"]:
        out += _write_image(d["image2"])
    if d["deftool"] is not None:
        out += _write_str(d["deftool"])
    if d["tooltypes"] is not None:
        out += struct.pack(">I", (len(d["tooltypes"]) + 1) * 4)
        for s in d["tooltypes"]:
            out += _write_str(s)
    if d["toolwin"] is not None:
        out += _write_str(d["toolwin"])
    if d["drawer"] and g["user"] == 1:
        out += d["drawer2"] or b"\0" * 6
    out += d.get("rest", b"")
    return out


def image_from_art(rows, depth=2):
    """rows: lijst met even lange strings; '.'=0 grijs '#'=1 zwart 'o'=2 wit '+'=3 blauw."""
    pen = {".": 0, "#": 1, "o": 2, "+": 3}
    h, w = len(rows), len(rows[0])
    assert all(len(r) == w for r in rows), "ongelijke rijen"
    bpr = ((w + 15) // 16) * 2
    planes = []
    for p in range(depth):
        pl = bytearray()
        for r in rows:
            row = bytearray(bpr)
            for x, ch in enumerate(r):
                if (pen[ch] >> p) & 1:
                    row[x // 8] |= 0x80 >> (x % 8)
            pl += row
        planes.append(bytes(pl))
    return dict(left=0, top=0, w=w, h=h, depth=depth, pick=(1 << depth) - 1, onoff=0, data=b"".join(planes))


def image_pixels(img):
    """Geeft een lijst rijen met pennummers terug (voor previews)."""
    w, h, d = img["w"], img["h"], img["depth"]
    bpr = ((w + 15) // 16) * 2
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            v = 0
            for p in range(d):
                byte = img["data"][p * bpr * h + y * bpr + x // 8]
                if byte & (0x80 >> (x % 8)):
                    v |= 1 << p
            row.append(v)
        rows.append(row)
    return rows


def project_icon(image1, image2, deftool, tooltypes, x=NO_ICON_POSITION, y=NO_ICON_POSITION, stack=8192):
    w, h = image1["w"], image1["h"]
    return dict(gadget=dict(left=0, top=0, w=w, h=h + 1, flags=6 if image2 else 4, act=3, gtype=1, user=1),
                type=WBPROJECT, x=x, y=y, stack=stack, drawer=None, drawer2=None,
                image1=image1, image2=image2, deftool=deftool, tooltypes=tooltypes, toolwin=None, rest=b"")


if __name__ == "__main__":
    import sys
    for f in sys.argv[1:]:
        raw = open(f, "rb").read()
        d = parse(raw)
        ok = build(d) == raw
        print(f"{'OK ' if ok else 'VERSCHIL'} type={d['type']} {d['image1']['w']}x{d['image1']['h']}x{d['image1']['depth']} "
              f"tool={d['deftool']!r} tt={d['tooltypes']} drawer={'ja' if d['drawer'] else 'nee'} {f.rsplit('/', 1)[-1]}")
