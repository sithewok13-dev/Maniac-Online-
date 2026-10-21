#!/usr/bin/env python3
"""Custom characters for the new engine (engines/scummverse), drawn here.

Each is newly drawn pixel art (not taken from any game), made into the
engine's character format ("SVC1": palette, then frames by facing, pose and
step, each with its mask) and written as engine/common/scummverse_custom_cast.inc,
which the engine carries (no files to install). Run it again after changing a
drawing; --preview DIR also writes each frame enlarged as PNG (needs Pillow).

Crispy: the user's eight-pound terrier in his red devil costume for
Halloween (hood with two horns, cape trimmed in black, its black ties), drawn
from the user's description and photos (the photos themselves are not kept).

Suzy: smiling, long dark hair streaked with silver pulled back into a
ponytail; a heather-green T-shirt with a small white oval and a green bat on
it, light-wash jeans, white sneakers, a black cross-body sling bag and a
black smartwatch; drawn the same way from the user's photos (not kept).
"""
import argparse
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Facings and poses as the engine numbers them (World::SourceFrame).
LEFT, RIGHT, FRONT, BACK = 0, 1, 2, 3
STAND, WALK, TALK = 0, 1, 2

# Crispy's colours: index -> RGB (0 is never drawn: the mask leaves it out).
CRISPY_COLOURS = {
    'K': (0x22, 0x18, 0x18),  # outline
    'R': (0xDD, 0x26, 0x20),  # costume red
    'r': (0x9C, 0x14, 0x16),  # costume red, shaded
    'h': (0xFF, 0x62, 0x50),  # costume red, lit
    'T': (0x12, 0x10, 0x12),  # black trim and ties
    't': (0x48, 0x40, 0x44),  # trim, lit
    'W': (0xF4, 0xE8, 0xCC),  # fur, pale
    'F': (0xDC, 0xC3, 0x96),  # fur
    'f': (0xB0, 0x8E, 0x5E),  # fur, shaded
    'g': (0xC4, 0xBE, 0xB2),  # grey whiskers and beard
    'N': (0x16, 0x14, 0x16),  # nose
    'E': (0x26, 0x24, 0x2C),  # eye
    'e': (0xA8, 0xB4, 0xC0),  # eye, clouded
    'P': (0xE6, 0x86, 0x92),  # tongue
}


class Canvas:
    """A small picture of letters (' ' is nothing), drawn with simple shapes."""

    def __init__(self, width, height):
        self.width, self.height = width, height
        self.cells = [[' '] * width for _ in range(height)]

    def put(self, x, y, c):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.cells[y][x] = c

    def get(self, x, y):
        return self.cells[y][x] if 0 <= x < self.width and 0 <= y < self.height else ' '

    def ellipse(self, x0, y0, x1, y1, c):
        cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 + 0.5, (y1 - y0) / 2 + 0.5
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.put(x, y, c)

    def polygon(self, points, c):
        ys = [p[1] for p in points]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            yc = y + 0.5
            xs = []
            for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
                if (ay <= yc < by) or (by <= yc < ay):
                    xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(round(a)), int(round(b))):
                    self.put(x, y, c)

    def line(self, points, c, width=1):
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            steps = max(abs(bx - ax), abs(by - ay), 1) * 2
            for i in range(int(steps) + 1):
                x, y = ax + (bx - ax) * i / steps, ay + (by - ay) * i / steps
                for dx in range(width):
                    for dy in range(width):
                        self.put(int(round(x - (width - 1) / 2 + dx)), int(round(y - (width - 1) / 2 + dy)), c)

    def outline(self, c='K'):
        """The silhouette's edge (drawn pixels beside nothing) in `c`."""
        edge = []
        for y in range(self.height):
            for x in range(self.width):
                if self.cells[y][x] != ' ' and any(self.get(x + dx, y + dy) == ' ' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    edge.append((x, y))
        for x, y in edge:
            self.cells[y][x] = c

    def shade(self, region, into, below):
        """The `region` letter's lowest rows (from y `below`) in `into`."""
        for y in range(below, self.height):
            for x in range(self.width):
                if self.cells[y][x] == region:
                    self.cells[y][x] = into

    def mirrored(self):
        m = Canvas(self.width, self.height)
        m.cells = [row[::-1] for row in self.cells]
        return m


def crispy_side(step=0, talking=False):
    """Facing right: 48 x 40, feet on the bottom row. `step` 0..3 walks."""
    c = Canvas(48, 40)
    b = 1 if step in (1, 3) else 0  # (a bob as the legs pass)
    swing = (0, 3, 0, -3)[step]
    def leg(top, hip, foot, colour, paw):
        c.polygon([(hip - 1, top), (hip + 3, top), (foot + 2, 37), (foot - 1, 37)], colour)
        c.line([(foot - 1, 37), (foot + 3, 37)], paw)
        c.line([(foot - 1, 38), (foot + 3, 38)], paw)
    # The far legs, shaded, swinging opposite the near ones.
    leg(27 + b, 10, 10 - swing, 'f', 'f')
    leg(27 + b, 27, 27 + swing, 'f', 'f')
    # The tail, wiry and up.
    c.line([(11, 24 + b), (8, 18 + b), (7, 13 + b), (9, 10 + b)], 'F', 3)
    # The body, its pale belly; the chest.
    c.ellipse(8, 19 + b, 34, 31 + b, 'F')
    c.ellipse(11, 26 + b, 31, 32 + b, 'W')
    c.ellipse(27, 15 + b, 38, 30 + b, 'W')
    # The near legs.
    leg(27 + b, 13, 13 + swing, 'F', 'W')
    leg(27 + b, 30, 30 - swing, 'W', 'W')
    # The head, its snout, the beard under it.
    c.ellipse(29, 6 + b, 42, 19 + b, 'F')
    c.ellipse(37, 10 + b, 46, 18 + b, 'W')
    c.polygon([(36, 16 + b), (45, 16 + b), (43, 21 + b), (37, 21 + b)], 'W')
    # The capelet over the shoulders and back, its hem trimmed in black.
    c.polygon([(35, 15 + b), (25, 16 + b), (14, 19 + b), (10, 23 + b), (14, 25 + b), (24, 24 + b), (32, 24 + b), (37, 21 + b)], 'R')
    c.shade('R', 'r', 22 + b)
    c.line([(10, 23 + b), (14, 25 + b), (24, 24 + b), (32, 24 + b), (37, 21 + b)], 'T')
    # The hood over the head's top and back, its rim black round the face.
    c.polygon([(27, 10 + b), (30, 5 + b), (37, 3 + b), (41, 6 + b), (39, 9 + b), (36, 14 + b), (35, 19 + b), (30, 19 + b), (27, 15 + b)], 'R')
    c.line([(41, 6 + b), (39, 9 + b), (36, 14 + b), (35, 19 + b)], 'T')
    c.line([(31, 5 + b), (36, 4 + b)], 'h')
    # The horns, the far one shaded.
    c.polygon([(30, 6 + b), (33, 5 + b), (31, 1 + b), (29, 0 + b)], 'r')
    c.polygon([(35, 5 + b), (39, 5 + b), (39, 1 + b), (38, 0 + b), (36, 2 + b)], 'R')
    c.put(37, 2 + b, 'h'); c.put(37, 3 + b, 'h')
    # The ear, peeking out at the rim.
    c.polygon([(35, 13 + b), (38, 12 + b), (38, 17 + b), (36, 18 + b)], 'f')
    # The ties.
    c.line([(37, 20 + b), (36, 29 + b)], 'T')
    c.line([(38, 20 + b), (39, 28 + b)], 'T')
    c.outline()
    # A clouded eye, the nose, whiskers; talking, the jaw open.
    c.put(39, 10 + b, 'E'); c.put(40, 10 + b, 'E'); c.put(39, 11 + b, 'E'); c.put(40, 11 + b, 'e')
    c.put(45, 11 + b, 'N'); c.put(45, 12 + b, 'N'); c.put(44, 11 + b, 'N')
    # (The wiry beard: grey hairs among the pale.)
    for x, y in ((38, 19), (40, 20), (42, 19), (39, 21), (41, 18), (43, 17), (37, 18)):
        if c.get(x, y + b) == 'W':
            c.put(x, y + b, 'g')
    c.put(42, 15 + b, 'g'); c.put(43, 16 + b, 'g'); c.put(41, 16 + b, 'g')
    if talking:
        for x in range(40, 46):
            c.put(x, 17 + b, 'K')
        c.put(42, 18 + b, 'P'); c.put(43, 18 + b, 'P'); c.put(44, 18 + b, 'K')
    return c


def crispy_front(step=0, talking=False):
    """Facing the viewer: 34 x 40, feet on the bottom row."""
    c = Canvas(34, 40)
    lift = (0, 1, 0, -1)[step]
    # Front legs and paws (one lifted a little in step).
    for x0, dy in ((11, max(0, lift)), (19, max(0, -lift))):
        c.polygon([(x0, 31), (x0 + 4, 31), (x0 + 4, 38 - dy), (x0, 38 - dy)], 'W')
        c.line([(x0 - 1, 38 - dy), (x0 + 4, 38 - dy)], 'W')
    # The cape over the shoulders, its black trim and ties.
    c.polygon([(6, 22), (28, 22), (32, 31), (30, 34), (4, 34), (2, 31)], 'R')
    c.shade('R', 'r', 30)
    c.line([(2, 31), (4, 34), (30, 34), (32, 31)], 'T')
    # The chest between the cape's fronts.
    c.polygon([(12, 22), (22, 22), (21, 33), (13, 33)], 'W')
    # The hood: two horns, the rim black round the face.
    c.polygon([(9, 9), (12, 6), (8, 0), (6, 1)], 'R')
    c.polygon([(25, 9), (22, 6), (26, 0), (28, 1)], 'R')
    c.put(8, 2, 'h'); c.put(9, 3, 'h'); c.put(25, 2, 'h'); c.put(24, 3, 'h')
    c.ellipse(5, 4, 29, 28, 'R')
    c.line([(9, 6), (16, 4), (24, 6)], 'h')
    c.ellipse(8, 9, 26, 29, 'T')
    # The face and its ears, the beard.
    c.ellipse(9, 10, 25, 29, 'F')
    c.polygon([(9, 15), (12, 14), (12, 21), (9, 20)], 'f')
    c.polygon([(25, 15), (22, 14), (22, 21), (25, 20)], 'f')
    c.ellipse(12, 17, 22, 30, 'W')
    c.polygon([(12, 25), (22, 25), (20, 31), (14, 31)], 'g' if not talking else 'W')
    # The ties.
    c.line([(15, 29), (14, 37)], 'T')
    c.line([(19, 29), (20, 37)], 'T')
    c.outline()
    # Eyes (clouded), the nose, whiskers; talking, the mouth open.
    for x in (13, 20):
        c.put(x, 17, 'E'); c.put(x + 1, 17, 'E'); c.put(x, 18, 'E'); c.put(x + 1, 18, 'e')
    for x in (16, 17, 18):
        c.put(x, 22, 'N'); c.put(x, 23, 'N')
    c.put(17, 21, 'N')
    c.put(14, 24, 'g'); c.put(20, 24, 'g'); c.put(13, 25, 'g'); c.put(21, 25, 'g')
    if talking:
        c.put(16, 26, 'K'); c.put(17, 26, 'K'); c.put(18, 26, 'K')
        c.put(16, 27, 'P'); c.put(17, 27, 'P'); c.put(18, 27, 'K')
    return c


def crispy_back(step=0):
    """Facing away: 34 x 40, feet on the bottom row."""
    c = Canvas(34, 40)
    lift = (0, 1, 0, -1)[step]
    # The hind legs and the rear, the tail up from it.
    for x0, dy in ((10, max(0, lift)), (20, max(0, -lift))):
        c.polygon([(x0, 30), (x0 + 4, 30), (x0 + 4, 38 - dy), (x0, 38 - dy)], 'F')
        c.line([(x0 - 1, 38 - dy), (x0 + 4, 38 - dy)], 'F')
    c.ellipse(8, 20, 26, 34, 'F')
    # The capelet over the shoulders, trimmed in black.
    c.polygon([(7, 15), (27, 15), (30, 24), (25, 27), (17, 28), (9, 27), (4, 24)], 'R')
    c.shade('R', 'r', 23)
    c.line([(4, 24), (9, 27), (17, 28), (25, 27), (30, 24)], 'T')
    c.line([(17, 34), (17, 30), (18, 28)], 'F', 3)
    # The hood's back and both horns.
    c.polygon([(9, 9), (12, 6), (8, 0), (6, 1)], 'R')
    c.polygon([(25, 9), (22, 6), (26, 0), (28, 1)], 'R')
    c.ellipse(7, 3, 27, 19, 'R')
    c.line([(10, 6), (17, 4), (24, 6)], 'h')
    c.outline()
    return c


def svc(frames, colours, costume):
    """The engine's character file: frames (dir, kind, index, canvas)."""
    letters = list(colours)
    palette = bytearray(768)
    for i, letter in enumerate(letters):
        palette[(i + 1) * 3:(i + 1) * 3 + 3] = bytes(colours[letter])
    out = bytearray(b'SVC1') + struct.pack('<HH', costume, len(frames)) + palette
    for d, kind, index, canvas in frames:
        w, h = canvas.width, canvas.height
        pixels = bytearray(w * h)
        mask = bytearray(w * h)
        for y in range(h):
            for x in range(w):
                ch = canvas.cells[y][x]
                if ch != ' ':
                    pixels[y * w + x] = letters.index(ch) + 1
                    mask[y * w + x] = 1
        # (The feet at the bottom row's middle.)
        out += struct.pack('<BBBBhhHH', d, kind, index, 0, -(w // 2), -(h - 1), w, h) + pixels + mask
    return bytes(out)


def crispy():
    frames = []
    side = [crispy_side(s) for s in range(4)]
    for d, flip in ((RIGHT, False), (LEFT, True)):
        pick = (lambda f: f.mirrored()) if flip else (lambda f: f)
        frames.append((d, STAND, 0, pick(side[0])))
        frames += [(d, WALK, i, pick(side[i])) for i in range(4)]
        frames += [(d, TALK, 0, pick(side[0])), (d, TALK, 1, pick(crispy_side(0, True)))]
    frames.append((FRONT, STAND, 0, crispy_front()))
    frames += [(FRONT, WALK, i, crispy_front(i)) for i in range(4)]
    frames += [(FRONT, TALK, 0, crispy_front()), (FRONT, TALK, 1, crispy_front(0, True))]
    frames.append((BACK, STAND, 0, crispy_back()))
    frames += [(BACK, WALK, i, crispy_back(i)) for i in range(4)]
    return frames


# Suzy's frames: W x H, the body on the middle column.
W, H = 29, 56
MID = W // 2  # (the body's axis; the engine puts her feet here)

SUZY_COLOURS = {
    'K': (0x24, 0x1C, 0x22),  # outline
    'S': (0xDC, 0xA4, 0x7C),  # skin
    's': (0xB4, 0x7A, 0x5A),  # skin, shaded
    'c': (0xE6, 0x8E, 0x78),  # cheeks
    'H': (0x9C, 0x9A, 0xA2),  # hair, grey
    'h': (0x3C, 0x34, 0x38),  # hair, dark
    'L': (0xD4, 0xD4, 0xD8),  # hair, silver
    'W': (0xF6, 0xF2, 0xEA),  # teeth, emblem, sneakers
    'M': (0x86, 0x2A, 0x2E),  # mouth, open
    'G': (0x6C, 0xB6, 0x5E),  # shirt, heather green
    'g': (0x4A, 0x8A, 0x46),  # shirt, shaded
    'q': (0x92, 0xCC, 0x7E),  # shirt, lit
    'b': (0x1E, 0x86, 0x32),  # the bat on the emblem
    'J': (0x7C, 0xA2, 0xCE),  # jeans, light wash
    'j': (0x58, 0x7A, 0xAA),  # jeans, shaded
    'i': (0xA8, 0xC4, 0xE2),  # jeans, faded
    'n': (0xB4, 0xB4, 0xBE),  # sneakers, shaded
    'T': (0x18, 0x16, 0x1C),  # bag, strap, watch, hair tie
    't': (0x4C, 0x4A, 0x56),  # bag, lit
    'O': (0x8C, 0x5C, 0x34),  # the little bow on the strap
}


# Drawing helpers on top of Canvas: spans of rows, little pictures, layers.

def span(c, y, x0, x1, colour):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        c.put(x, y, colour)


def rows(c, y0, spans, colour):
    for i, (x0, x1) in enumerate(spans):
        span(c, y0 + i, x0, x1, colour)


def stamp(c, x0, y0, picture):
    """A little picture of letters ('.' is nothing) with its top left at x0, y0."""
    for dy, line in enumerate(picture):
        for dx, ch in enumerate(line):
            if ch != '.':
                c.put(x0 + dx, y0 + dy, ch)


def recolour(c, letter, into, where):
    for y in range(c.height):
        for x in range(c.width):
            if c.cells[y][x] == letter and where(x, y):
                c.cells[y][x] = into


def paste(dst, src, outline=True):
    """A part drawn on its own (outlined round, so it stands out) laid on."""
    if outline:
        src.outline()
    for y in range(src.height):
        for x in range(src.width):
            if src.cells[y][x] != ' ':
                dst.cells[y][x] = src.cells[y][x]


def streak_radial(c, cx, cy, width, strands, region, near=None, reach=0):
    """Her hair (dark, grey, silver) in `region` combed into strands along
    lines through cx, cy (where it is pulled back to), coloured in turn
    (within `reach` of that point from `near` instead: darker behind)."""
    for y in range(c.height):
        for x in range(c.width):
            if c.cells[y][x] in 'HhL' and region(x, y):
                a = math.atan2(x - cx, cy - y)
                seq = near if near and math.hypot(x - cx, y - cy) <= reach else strands
                c.cells[y][x] = seq[int(math.floor(a / width)) % len(seq)]


def streak_down(c, centre, region, phase=0, strands='hHLHhH'):
    """A tail of hair streaked along its length (`centre(y)` is its middle)."""
    for y in range(c.height):
        for x in range(c.width):
            if c.cells[y][x] == 'H' and region(x, y):
                k = int(math.floor(x - centre(y) + 0.5)) + phase
                c.cells[y][x] = strands[k % len(strands)]


# Facing the viewer (and away): the head and the shirt are drawn pixel by
# pixel; the legs walk.

FRONT_HEAD = [  # x 7..21 (the middle at the 8th letter), y 1..14
    '.....KKKKK.....',
    '...KKHLLLHKK...',
    '..KHHLLLLLHHK..',
    '.KHhLSSSSSLhHK.',
    '.KHHSSSSSSSHHK.',
    '.KHShhSSShhSHK.',
    '.KhSSSSSSSSShK.',
    'KShSKKSSSKKShSK',
    'KShSShSsShSShSK',
    '.KLcsSSSSSscLK.',
    '..KSSWWWWWSSK..',
    '..KSSScccSSSK..',
    '...KsSSSSSsK...',
    '....KKsssKK....',
]
FRONT_TALK = {  # (rows replaced, talking)
    11: '..KSSKWWWKSSK..',
    12: '..KSScMMMcSSK..',
}

FRONT_BODY = [  # x 4..24 (the middle at the 11th letter), y 15..34
    '.......KsSSSsK.......',
    '.....KKgSSSSSgKK.....',
    '...KKGGGgSSSgGGGKK...',
    '.KKqqGGGGgggGGGGqqKK.',
    'KqGGgGGGGGGGGGGGgGGqK',
    'KGGGgGGGWWWWWGGGgGGGK',
    'KGGGgGGbbWbWbbGGgGGGK',
    'KgggggGWbbbbbWGgggggK',
    'KKKKKgGGWWWWWGGgKKKKK',
    '.KSsKgGGGGGGGGGgKsSK.',
    '.KSsKgGGGGGGGGGgKsSK.',
    '.KSsKggGGGGGGGggKsSK.',
    '.KSsKKgGGGGGGGgKKsSK.',
    '.KSsKKgGGGGGGGgKKsSK.',
    '.KSsKgGGGGGGGGGgKsSK.',
    '.KSsKgggggggggggKsSK.',
    '.KSSKKKKKKKKKKKKKSSK.',
    '.KSSK...........KSSK.',
    '.KSSK...........KSSK.',
    '..KK.............KK..',
]

BACK_HEAD = [  # x 7..21, y 1..14
    '.....KKKKK.....',
    '...KKHLLLHKK...',
    '..KHHLLLLLHHK..',
    '.KHhHLLLLLHhHK.',
    '.KHhHHLLLHHhHK.',
    '.KHHhHHLHHhHHK.',
    '.KhHhHHhHHhHhK.',
    'KSHhHHhHhHHhHSK',
    'KSHHhHTTTHhHHSK',
    '.KhHHhHHHhHHhK.',
    '..KhHHHHHHHhK..',
    '..KHhHHHHHhHK..',
    '...KSSHHHSSK...',
    '....KSSSSSK....',
]

BACK_BODY = [  # x 4..24, y 15..34
    '.......KsSSSsK.......',
    '.....KKgGGGGGgKK.....',
    '...KKGGGGGGGGGGGKK...',
    '.KKqqGGGGGGGGGGGqqKK.',
    'KqGGgGGGGGGGGGGGgGGqK',
    'KGGGgGGGGGGGGGGGgGGGK',
    'KGGGgGgGGGGGGGgGgGGGK',
    'KgggggGgGGGGGgGgggggK',
    'KKKKKgGGGGGGGGGgKKKKK',
    '.KSsKgGGGGGGGGGgKsSK.',
    '.KSsKgGGGGGGGGGgKsSK.',
    '.KSsKggGGGGGGGggKsSK.',
    '.KSsKKgGGGGGGGgKKsSK.',
    '.KSsKKgGGGGGGGgKKsSK.',
    '.KSsKgGGGGGGGGGgKsSK.',
    '.KSsKgggggggggggKsSK.',
    '.KSSKKKKKKKKKKKKKSSK.',
    '.KSSK...........KSSK.',
    '.KSSK...........KSSK.',
    '..KK.............KK..',
]


def front_legs(c, lift, b, back=False):
    """Hips, both legs in jeans, the sneakers; `lift` > 0 raises her right foot
    (the viewer's left; from behind, the viewer's right), < 0 the other."""
    for y in range(30 + b, 36 + b):
        span(c, y, 7, 2 * MID - 7, 'J')
    for mirror in (False, True):
        up = max(0, lift) if mirror == back else max(0, -lift)
        X = (lambda x: 2 * MID - x) if mirror else (lambda x: x)
        bottom = 51 - up
        for y in range(36 + b, bottom + 1):
            x0 = 7 if y < 41 - up // 2 else 8 if y < 46 - up else 9
            span(c, y, X(x0), X(13), 'J')
        rows(c, bottom + 1, [(X(9), X(13))] + [(X(8), X(13))] * 3, 'W')


def jeans_shading(c, b, back=False):
    recolour(c, 'J', 'j', lambda x, y: y == 32 + b or abs(x - MID) == 2 or abs(x - MID) >= 6)
    if not back:
        recolour(c, 'J', 'i', lambda x, y: 37 + b <= y <= 42 and abs(x - MID) in (3, 4))
        recolour(c, 'J', 'i', lambda x, y: y in (45, 46) and abs(x - MID) == 3)


def shoe_shading(c, back=False):
    """The sneakers' lowest white row (from behind: the heels) shaded."""
    for x in range(W):
        ys = [y for y in range(44, H) if c.cells[y][x] == 'W']
        if ys:
            c.cells[max(ys)][x] = 'n'
            if back and len(ys) > 1:
                c.cells[max(ys) - 1][x] = 'n'


def suzy_front(step=0, talking=False):
    """Facing the viewer: W x H, feet on the bottom row."""
    c = Canvas(W, H)
    b = 1 if step in (1, 3) else 0
    lift = (0, 2, 0, -2)[step]
    low = Canvas(W, H)
    front_legs(low, lift, b)
    paste(c, low)
    jeans_shading(c, b)
    shoe_shading(c)
    behind = Canvas(W, H)
    rows(behind, 10 + b, [(8, 20)] * 7, 'h')
    for x in (9, 12, 16, 19):
        span(behind, 13 + b, x, x, 'H'); span(behind, 14 + b, x, x, 'H')
    paste(c, behind)
    stamp(c, 4, 15 + b, FRONT_BODY)
    # The sling bag at her left hip (the viewer's right), on its strap from
    # her right shoulder, down under the emblem.
    bag = Canvas(W, H)
    rows(bag, 28 + b, [(16, 20)] * 4 + [(17, 19)], 'T')
    paste(c, bag)
    span(c, 29 + b, 17, 19, 't')
    c.put(18, 30 + b, 't')
    c.line([(10, 16 + b), (10, 22 + b), (16, 28 + b)], 'T')
    c.put(10, 18 + b, 'O')
    # The watch on her left wrist.
    c.put(21, 31 + b, 'T'); c.put(22, 31 + b, 'T')
    head = FRONT_HEAD[:]
    if talking:
        for y, line in FRONT_TALK.items():
            head[y - 1] = line
    stamp(c, 7, 1 + b, head)
    # (Combed back from her forehead; the brows and eyes left alone.)
    streak_radial(c, MID, 11 + b, 0.28, 'HhLhHL', lambda x, y: y <= 5 + b or abs(x - MID) >= 5)
    # A few loose strands by her face.
    for x, y in ((8, 11), (8, 12), (9, 13), (20, 11), (20, 12)):
        c.put(x, y + b, 'L' if y < 12 else 'H')
    return c


def suzy_back(step=0):
    """Facing away: W x H, feet on the bottom row."""
    c = Canvas(W, H)
    b = 1 if step in (1, 3) else 0
    lift = (0, 2, 0, -2)[step]
    low = Canvas(W, H)
    front_legs(low, lift, b, back=True)
    paste(c, low)
    jeans_shading(c, b, back=True)
    shoe_shading(c, back=True)
    # Back pockets.
    for x0 in (9, 16):
        span(c, 33 + b, x0, x0 + 3, 'j')
        c.put(x0, 34 + b, 'j'); c.put(x0 + 3, 34 + b, 'j')
    stamp(c, 4, 15 + b, BACK_BODY)
    # The strap across her back, from her right shoulder to her left hip.
    c.line([(18, 16 + b), (10, 29 + b)], 'T')
    c.put(6, 31 + b, 'T'); c.put(7, 31 + b, 'T')  # the watch
    stamp(c, 7, 1 + b, BACK_HEAD)
    streak_radial(c, MID, 12 + b, 0.22, 'hHLHhHhL', lambda x, y: y <= 13 + b)
    span(c, 9 + b, 13, 15, 'T')  # the hair tie
    # The ponytail down her back from its tie, swaying a little as she walks.
    top, end = 10 + b, 27 + b
    sway = (0, 0.5, 0, -0.5)[step]
    def centre(y):
        t = (y - top) / (end - top)
        return MID + 0.7 * math.sin(t * math.pi * 1.2) + sway * t
    p = Canvas(W, H)
    for y in range(top, end + 1):
        t = (y - top) / (end - top)
        half = 1.6 + 1.3 * t / 0.15 if t < 0.15 else 2.9 - 2.4 * (t - 0.15) / 0.85
        span(p, y, int(round(centre(y) - half)), int(round(centre(y) + half)), 'H')
    paste(c, p)
    streak_down(c, centre, lambda x, y: top <= y, phase=1, strands='hhHhLh')
    return c


# Facing right.

SIDE_HEAD = [  # x 5..21, y 1..14
    '......KKKKK......',
    '....KKHLLLHKK....',
    '...KHHLLLLHHHK...',
    '..KHhhHLLHHHSK...',
    '..KhHHhhHHHSSSK..',
    '..KHhHHHHhSShhK..',
    '..KhLhhHSSSSSSK..',
    '..KHhLhSsSSSKSSK.',
    '..KhHhHSsSSSSSSK.',
    '...KhhHSSSScsSK..',
    '...KhHSSSSSSSWK..',
    '....KhSSSSSSsK...',
    '.....KSSSSSSK....',
    '........KKKKK....',
]
SIDE_TALK = {
    11: '...KhHSSSSSSSWM..',
    12: '....KHSSSSSMMK...',
}

POSES = {  # near foot x, far foot x, near up, far up, near knee x, far knee x
    0: (15, 13, 0, 0, 15, 13),
    1: (19, 9, 0, 1, 17, 11),
    2: (14, 16, 0, 2, 14, 17),
    3: (9, 19, 1, 0, 11, 17),
}


def side_leg(c, fx, kx, up, b, jeans, shoe):
    top, ky, ankle = 33 + b, 44, 51 - up
    c.polygon([(10, top), (18, top), (kx + 3, ky), (fx + 2.5, ankle + 1), (fx - 2, ankle + 1), (kx - 2.5, ky)], jeans)
    rows(c, ankle + 1, [(fx - 2, fx + 1), (fx - 2, fx + 3), (fx - 3, fx + 4), (fx - 3, fx + 4)], shoe)


def side_arm(b, dx, skin, sleeve):
    a = Canvas(W, H)
    a.polygon([(12.5, 21 + b), (16, 21 + b), (16 + dx, 31 + b), (12.5 + dx, 31 + b)], skin)
    a.ellipse(12 + dx, 30 + b, 15 + dx, 33 + b, skin)
    lean = dx / 4
    a.polygon([(12.5, 16 + b), (15.5, 16 + b), (17, 18 + b), (16.5 + lean, 23.5 + b), (11.5 + lean, 23.5 + b), (11.5, 18 + b)], sleeve)
    return a


def suzy_side(step=0, talking=False):
    """Facing right: W x H, feet on the bottom row. `step` 0..3 walks."""
    c = Canvas(W, H)
    b = 1 if step in (1, 3) else 0
    nfx, ffx, nup, fup, nkx, fkx = POSES[step]
    swing = (0, -4, 0, 4)[step]
    # The far arm and leg, shaded.
    paste(c, side_arm(b, -swing, 's', 'g'))
    far = Canvas(W, H)
    side_leg(far, ffx, fkx, fup, b, 'j', 'n')
    paste(c, far)
    # The hips, the near leg.
    low = Canvas(W, H)
    rows(low, 30 + b, [(10, 18), (10, 18), (9, 18), (9, 18), (9, 18), (9, 18), (10, 18)], 'J')
    side_leg(low, nfx, nkx, nup, b, 'J', 'W')
    paste(c, low)
    recolour(c, 'J', 'j', lambda x, y: y == 32 + b or x <= 10)
    recolour(c, 'J', 'i', lambda x, y: 35 + b <= y <= 41 and x >= 15 and c.get(x + 1, y) == 'J')
    shoe_shading(c)
    # The shirt and the neck.
    top = Canvas(W, H)
    rows(top, 12 + b, [(12, 16)] * 5, 'S')
    rows(top, 16 + b, [(11, 17), (10, 18), (10, 19), (10, 19), (10, 19), (10, 19), (10, 19), (10, 18),
                       (10, 18), (11, 18), (11, 18), (11, 18), (11, 18), (10, 18), (10, 18)], 'G')
    paste(c, top)
    recolour(c, 'G', 'g', lambda x, y: y >= 29 + b or x <= 11 or (y == 23 + b and x >= 17))
    recolour(c, 'S', 's', lambda x, y: y <= 15 + b)
    # The bag at her left hip, on its strap from her right shoulder.
    bag = Canvas(W, H)
    rows(bag, 27 + b, [(16, 20)] * 4 + [(17, 19)], 'T')
    paste(c, bag)
    span(c, 28 + b, 17, 19, 't')
    c.line([(11, 17 + b), (16, 27 + b)], 'T')
    # The ponytail down her back.
    p = Canvas(W, H)
    p.polygon([(5, 6 + b), (8, 6 + b), (8.5, 10 + b), (9.5, 15 + b), (10.5, 20 + b), (10, 24 + b), (8.5, 27 + b), (7, 24 + b), (6, 18 + b), (5, 12 + b)], 'H')
    paste(c, p)
    streak_down(c, lambda y: 6.5 + max(0, y - 6 - b) * 0.12, lambda x, y: x <= 10 and y >= 6 + b, phase=2, strands='hhHhLh')
    # The head.
    head = SIDE_HEAD[:]
    if talking:
        for y, line in SIDE_TALK.items():
            head[y - 1] = line
    stamp(c, 5, 1 + b, head)
    streak_radial(c, 7, 7 + b, 0.28, 'HLhHLh', lambda x, y: y <= 13 + b and 8 <= x <= 16, near='hHhhLh', reach=6)
    c.put(7, 6 + b, 'T'); c.put(7, 7 + b, 'T')  # the hair tie
    # The near arm, its watch.
    paste(c, side_arm(b, swing, 'S', 'G'))
    recolour(c, 'G', 'g', lambda x, y: y == 23 + b)
    c.put(13 + swing, 30 + b, 'T'); c.put(14 + swing, 30 + b, 'T')
    return c


def suzy():
    frames = []
    side = [suzy_side(s) for s in range(4)]
    for d, flip in ((RIGHT, False), (LEFT, True)):
        pick = (lambda f: f.mirrored()) if flip else (lambda f: f)
        frames.append((d, STAND, 0, pick(side[0])))
        frames += [(d, WALK, i, pick(side[i])) for i in range(4)]
        frames += [(d, TALK, 0, pick(side[0])), (d, TALK, 1, pick(suzy_side(0, True)))]
    frames.append((FRONT, STAND, 0, suzy_front()))
    frames += [(FRONT, WALK, i, suzy_front(i)) for i in range(4)]
    frames += [(FRONT, TALK, 0, suzy_front()), (FRONT, TALK, 1, suzy_front(0, True))]
    frames.append((BACK, STAND, 0, suzy_back()))
    frames += [(BACK, WALK, i, suzy_back(i)) for i in range(4)]
    return frames


for _name, _pic in (('FRONT_HEAD', FRONT_HEAD), ('FRONT_BODY', FRONT_BODY), ('BACK_HEAD', BACK_HEAD),
                    ('BACK_BODY', BACK_BODY), ('SIDE_HEAD', SIDE_HEAD)):
    assert len({len(line) for line in _pic}) == 1, _name


# The custom characters (their number, name, the art, its colours, and how
# tall they stand against a person: Crispy is a little dog).
CUSTOM = [(1, 'Crispy', crispy, CRISPY_COLOURS, 0.3), (2, 'Suzy', suzy, SUZY_COLOURS, 0.95)]


def write_inc(path):
    lines = ['// SPDX-License-Identifier: GPL-3.0-or-later',
             '// Generated by tools/custom_characters.py: the new engine\'s custom',
             '// characters, newly drawn there (not taken from any game). Do not edit.',
             '']
    table = []
    for costume, name, art, colours, height in CUSTOM:
        data = svc(art(), colours, costume)
        tallest = max(f[3].height for f in art())
        ident = 'kWorldCustom' + name.replace(' ', '')
        lines.append(f'static const unsigned char {ident}[] = {{')
        for i in range(0, len(data), 24):
            lines.append('\t' + ', '.join(str(b) for b in data[i:i + 24]) + ',')
        lines.append('};')
        table.append(f'\t{{{costume}, {ident}, sizeof({ident}), {height} / {tallest}}},')
    lines += ['// (Its number, its file, and a person\'s height per row of its art: as',
              '// tall against the people of a place as it is drawn to stand.)',
              'struct WorldCustomArt { int costume; const unsigned char *data; unsigned size; double personPerRow; };',
              'static const WorldCustomArt kWorldCustomArt[] = {'] + table + ['};', '']
    path.write_text('\n'.join(lines))


def preview(directory):
    from PIL import Image
    directory.mkdir(parents=True, exist_ok=True)
    for costume, name, art, colours, _ in CUSTOM:
        frames = art()
        scale = 8
        width = sum(f[3].width for f in frames) * scale + 4 * len(frames)
        sheet = Image.new('RGB', (width, max(f[3].height for f in frames) * scale), (90, 70, 110))
        x = 0
        for d, kind, index, canvas in frames:
            for cy in range(canvas.height):
                for cx in range(canvas.width):
                    ch = canvas.cells[cy][cx]
                    if ch != ' ':
                        for py in range(scale):
                            for px in range(scale):
                                sheet.putpixel((x + cx * scale + px, cy * scale + py), colours[ch])
            x += canvas.width * scale + 4
        sheet.save(directory/f'{name.lower()}.png')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--preview', type=Path, help='also write each character\'s frames enlarged here (PNG)')
    a = p.parse_args()
    write_inc(ROOT/'engine/common/scummverse_custom_cast.inc')
    if a.preview:
        preview(a.preview)
    print('wrote engine/common/scummverse_custom_cast.inc')
