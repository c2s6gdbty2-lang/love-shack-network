"""amiagent_icons.py - the AmiAgent disk icon image, drawn in code (original work, MIT).

A diskette whose label shows a magnifying glass: the agent only looks, it never
writes. 48x24 pixels, the four Workbench pens: 0 grey, 1 black, 2 white, 3 blue.
Uses icon.image_from_art() from amiga/common/tools/icon.py.
"""


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.p = [[0] * w for _ in range(h)]

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)

    def frame(self, x0, y0, x1, y1, c):
        for x in range(x0, x1 + 1):
            self.px(x, y0, c); self.px(x, y1, c)
        for y in range(y0, y1 + 1):
            self.px(x0, y, c); self.px(x1, y, c)

    def line(self, x0, y0, x1, y1, c):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.px(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)

    def ellipse(self, cx, cy, rx, ry, c, fill=False):
        """Ellipse; rx is wider than ry because Workbench pixels are about twice as tall as wide."""
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if (fill and d <= 1.0) or (not fill and 0.55 <= d <= 1.0):
                    self.px(x, y, c)

    def art(self):
        return ["".join(".#o+"[v] for v in row) for row in self.p]


def disk_art():
    c = Canvas(48, 24)
    c.rect(2, 0, 45, 23, 1)                      # diskette body
    c.rect(11, 0, 34, 7, 2); c.rect(27, 1, 31, 6, 1)   # metal shutter with its window
    c.rect(6, 10, 41, 22, 2)                     # label
    c.line(9, 13, 18, 13, 3); c.line(9, 16, 16, 16, 3); c.line(9, 19, 17, 19, 3)   # text lines
    c.ellipse(28, 15, 6, 4, 3, fill=True)        # lens (blue glass)
    c.rect(27, 13, 28, 13, 2)                    # highlight
    c.ellipse(28, 15, 6, 4, 1)                   # rim
    c.line(33, 18, 38, 21, 1); c.line(34, 18, 39, 21, 1)   # handle
    return c.art()


if __name__ == "__main__":
    print("\n".join(disk_art()))
