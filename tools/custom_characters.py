#!/usr/bin/env python3
"""Custom characters for the new engine (engines/scummverse), drawn here.

Each is newly drawn pixel art (not taken from any game), made into the
engine's character format ("SVC1": palette, then frames by facing, pose and
step, each with its mask) and written as engine/common/scummverse_custom_cast.inc,
which the engine carries (no files to install). Run it again after changing a
drawing; --preview DIR also writes each frame enlarged as PNG (needs Pillow).

Crispy: the user's eight-pound terrier in his red devil costume for
Halloween (hood with two horns, cape trimmed in black, its black ties), drawn
from the user's description and photos (the photos themselves are not kept);
his face pixel by pixel so it reads at game size: big dark eyes clouded with
age, bushy white eyebrows, a big black nose, a grey moustache and a scraggly
grey-white beard, tan folded ears under the hood.

Suzy: smiling, long black hair with a few grey streaks pulled back into a
ponytail, her face as in the user's photos; a heather-green T-shirt with a
small white oval and a green bat on it, light-wash jeans over full hips and
thighs, white sneakers, a black cross-body sling bag and a black
smartwatch; a little shorter than the people of a place. Drawn the same way
from the user's photos and corrections (the photos are not kept).

Extra: the user's eight-pound black Chihuahua, drawn by hand from the user's
photos (the photos are not kept), his build as in them: slender and
fine-boned, a slim body on thin legs; a round head about as wide as his body,
held up on his neck, a short snout; huge ears angled up and out, dusky
pinkish brown inside; big round dark eyes with a shine and the tan under
them; a black nose, grey about the mouth, his white goatee; a few white
hairs on his chest; the tail carried up in a curl to a pale tip. His glossy
black a step above the outline, with a blue-grey sheen, so he reads in a
dark room. No collar (that photo was his costume).
"""
import argparse
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Facings and poses as the engine numbers them (World::SourceFrame).
LEFT, RIGHT, FRONT, BACK = 0, 1, 2, 3
STAND, WALK, TALK = 0, 1, 2

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


# Crispy's colours: letter -> RGB (' ' is never drawn).
CRISPY_COLOURS = {
    'K': (0x22, 0x18, 0x18),  # outline
    'R': (0xDD, 0x26, 0x20),  # costume red
    'r': (0x9C, 0x14, 0x16),  # costume red, shaded
    'h': (0xFF, 0x62, 0x50),  # costume red, lit
    'T': (0x12, 0x10, 0x12),  # black trim and ties
    't': (0x48, 0x40, 0x44),  # trim, lit
    'W': (0xF4, 0xE8, 0xCC),  # fur, pale cream
    'F': (0xDC, 0xC3, 0x96),  # fur, biscuit
    'f': (0xB0, 0x8E, 0x5E),  # fur, shaded (ears)
    'w': (0xFF, 0xFC, 0xF2),  # white wisps: eyebrows, whisker tips
    'g': (0xC4, 0xBE, 0xB2),  # grey whiskers and beard
    'm': (0x96, 0x8E, 0x86),  # beard, shaded grey
    'G': (0x5C, 0x54, 0x52),  # dark grey: lips, muzzle pigment, eye rims
    'N': (0x16, 0x14, 0x16),  # nose
    'n': (0x6A, 0x66, 0x70),  # nose, lit
    'E': (0x26, 0x24, 0x2C),  # eye
    'e': (0x8A, 0x9C, 0xB0),  # eye, clouded
    'c': (0xD8, 0xE6, 0xF2),  # eye, cloud's glint
    'M': (0x58, 0x16, 0x1C),  # mouth, inside
    'P': (0xE6, 0x86, 0x92),  # tongue
}


def crispy_stamp(c, x, y, rows):
    """Letters onto `c` from (x, y); '.' leaves what is there."""
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != '.':
                c.put(x + dx, y + dy, ch)


def crispy_mirror_rows(half, centre=True):
    """Rows from their left half: mirrored about the last column (centre)."""
    return [h + (h[-2::-1] if centre else h[::-1]) for h in half]


# ---------------------------------------------------------------- side ----

# The face in profile, facing right: x 35..47, from y 3 (b adds the bob).
CRISPY_SIDE_FACE = [
    # 3333344444444
    # 5678901234567
    "...TFFFK.....",  # 3  the forehead, biscuit, under the hood
    "...TFFFFK....",  # 4
    "..TFFwFwFK...",  # 5  eyebrow hairs up
    "..TFwwwwwgK..",  # 6  the bushy white eyebrow, jutting
    "..TFGEEEmFKK.",  # 7  the eye under it; the stop, the muzzle's top
    "..TFFEceWggnN",  # 8  the clouded eye; the grey muzzle, the nose
    "..TFFGEEFWNNN",  # 9  biscuit round the eye, the muzzle cream
    ".TFFFWWgWWNNN",  # 10
    ".TFWWgWWggGN.",  # 11 the moustache, the lip
    ".TWWgWggmGGK.",  # 12 the mouth
    ".TWgWgmggwgK.",  # 13 the beard
    "TWgwgmgwgwgw.",  # 14
    "TWgwmgwgwgK..",  # 15
    "TgwgmgwgwK...",  # 16
    ".KwmgwKgK....",  # 17
    "..KgKw.K.....",  # 18
    "...K.K.......",  # 19
]
CRISPY_SIDE_TALK = [  # the jaw dropped: rows 11..14 replaced
    ".TFWWgWWggGN.",  # 11
    ".TWWgWggGMMK.",  # 12
    ".TWgWgmgGPMK.",  # 13
    "TWgwgmgwgGGw.",  # 14
]
# The ear: a tan flap folded down out of the hood, behind the cheek.
CRISPY_SIDE_EAR = [
    ".KK..",   # y 9, from x 34
    "KfFK.",
    "KffFK",
    "KfffK",
    ".KffK",
    "..KfK",
    "...K.",
]


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
    # The head under the hood (its face is drawn after the outline).
    c.ellipse(29, 3 + b, 40, 18 + b, 'F')
    # The capelet over the shoulders and back, its hem trimmed in black.
    c.polygon([(35, 15 + b), (25, 16 + b), (14, 19 + b), (10, 23 + b), (14, 25 + b), (24, 24 + b), (32, 24 + b), (37, 21 + b)], 'R')
    c.shade('R', 'r', 22 + b)
    c.line([(10, 23 + b), (14, 25 + b), (24, 24 + b), (32, 24 + b), (37, 21 + b)], 'T')
    # The hood over the head's top and back, down to the brow.
    c.polygon([(26, 11 + b), (28, 5 + b), (32, 2 + b), (37, 1 + b), (40, 2 + b), (39, 4 + b),
               (38, 7 + b), (37, 11 + b), (36, 15 + b), (35, 18 + b), (35, 21 + b), (30, 21 + b), (26, 16 + b)], 'R')
    c.line([(31, 4 + b), (36, 3 + b)], 'h')
    # The horns, the far one shaded.
    c.polygon([(29, 6 + b), (32, 4 + b), (30, 0 + b), (28, 0 + b)], 'r')
    c.polygon([(35, 3 + b), (39, 3 + b), (40, 0 + b), (38, 0 + b), (36, 1 + b)], 'R')
    c.put(38, 1 + b, 'h'); c.put(37, 2 + b, 'h')
    # The ties.
    c.line([(37, 21 + b), (36, 29 + b)], 'T')
    c.line([(38, 21 + b), (39, 28 + b)], 'T')
    c.outline()
    # The face: brow, clouded eye, nose, moustache, beard; the ear.
    crispy_stamp(c, 35, 3 + b, CRISPY_SIDE_FACE)
    if talking:
        crispy_stamp(c, 35, 11 + b, CRISPY_SIDE_TALK)
    crispy_stamp(c, 34, 9 + b, CRISPY_SIDE_EAR)
    return c


# --------------------------------------------------------------- front ----

# The face from the front: x 5..29 (centre column x 17), from y 7.
CRISPY_FRONT_FACE_HALF = [
    # x 5..17 (the centre last)
    ".......FFFFFF",  # 8  the crown, biscuit
    ".....FFFFFFFF",  # 9
    "....FFFFFFFFF",  # 10
    "....wFwFFFFFF",  # 11 eyebrow hairs up
    "...FFwwwwgFFF",  # 12 the eyebrows
    "...FFGEEGFFWW",  # 13 the eyes, dark-rimmed
    "...FFEceEFWWW",  # 14 (clouded)
    "...WWEeEEWWWg",  # 15
    "...WWGEEGWWWg",  # 16
]
CRISPY_FRONT_FACE_LOW = [
    # x 5..29: 5   10   15   20   25
    "...WWWggWWWWWWWWWggWWW...",  # 17 grey under the eyes
    "...WWWWWWWWNNNWWWWWWWW...",  # 18 the nose
    "...WWgWWWWNNNNNWWWWgWW...",  # 19
    "...WgmgWWWNNNNNWWggmgW...",  # 20 the moustache
    "...WgmggWWWNNNWWWggmgW...",  # 21
    "..gWWgmggWWWGWWWggmgWWg..",  # 22 (cheek hair over the rim)
    "..wWWgmggWGGGGGWggmgWWw..",  # 23 the lips
    "...WWwgmgmwmmmwmgmgwWW...",  # 24 the chin
    "....WgwWgwWgmgWwgWwgW....",  # 25 the beard
    "....WgwWgWwgmgwWgWwgW....",  # 26
    ".....gwWgwWgmgWwgWwg.....",  # 27
    ".....KwWgwWmgmWgwWwK.....",  # 28
    "......KgwKWgmgWKgwK......",  # 29
    ".......KK.KwgwK.KK.......",  # 30
    "...........KwK...........",  # 31
]
CRISPY_FRONT_FACE = crispy_mirror_rows(CRISPY_FRONT_FACE_HALF) + CRISPY_FRONT_FACE_LOW
CRISPY_FRONT_TALK = [  # the mouth open in the beard, rows 23..25, x 14..20
    "GGMMMGG",
    "gGMPMGg",
    "wgGMGgw",
]
# The ears: tan flaps folded down out of the hood at the cheeks.
CRISPY_FRONT_EAR = [
    "..KK.",   # y 14, from x 4 (mirrored for the right)
    ".KFfK",
    "KfFff",
    "KfffK",
    "KfffK",
    ".KffK",
    "..KK.",
]


def _crispy_front_face(c, talking):
    crispy_stamp(c, 5, 8, CRISPY_FRONT_FACE)
    # (Not quite symmetrical: one glint of light on the nose.)
    c.put(16, 19, 'n'); c.put(18, 19, 'N')
    if talking:
        crispy_stamp(c, 14, 23, CRISPY_FRONT_TALK)
    crispy_stamp(c, 4, 14, CRISPY_FRONT_EAR)
    crispy_stamp(c, 26, 14, [r[::-1] for r in CRISPY_FRONT_EAR])


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
    c.polygon([(9, 8), (12, 5), (8, 0), (6, 1)], 'R')
    c.polygon([(25, 8), (22, 5), (26, 0), (28, 1)], 'R')
    c.put(8, 2, 'h'); c.put(9, 3, 'h'); c.put(25, 2, 'h'); c.put(24, 3, 'h')
    c.ellipse(4, 3, 30, 27, 'R')
    c.line([(9, 5), (17, 4), (25, 5)], 'h')
    c.ellipse(7, 7, 27, 31, 'T')
    # The face's silhouette (its features come after the outline).
    c.ellipse(8, 8, 26, 31, 'W')
    # The ties.
    c.line([(15, 31), (14, 37)], 'T')
    c.line([(19, 31), (20, 37)], 'T')
    c.outline()
    _crispy_front_face(c, talking)
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
    # The hood's back (as big as the front's), shaded below, its seam;
    # both horns.
    c.polygon([(9, 8), (12, 5), (8, 0), (6, 1)], 'R')
    c.polygon([(25, 8), (22, 5), (26, 0), (28, 1)], 'R')
    c.put(8, 2, 'h'); c.put(9, 3, 'h'); c.put(25, 2, 'h'); c.put(24, 3, 'h')
    c.ellipse(5, 3, 29, 22, 'r')
    c.ellipse(6, 3, 28, 19, 'R')
    c.line([(9, 5), (17, 4), (25, 5)], 'h')
    c.line([(8, 7), (7, 12)], 'h')
    c.line([(17, 6), (17, 20)], 'r')
    c.outline()
    # The ears folded down below the hood's sides; wisps of whisker.
    crispy_stamp(c, 3, 16, ["..KK", ".KfK", "KffK", "KffK", ".KK."])
    crispy_stamp(c, 27, 16, ["KK..", "KfK.", "KffK", "KffK", ".KK."])
    for x, y, ch in ((3, 21, 'w'), (30, 21, 'w')):
        c.put(x, y, ch)
    return c


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


# ------------------------------------------------------------- preview ----


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


# Suzy's frames: W x H, the body on the middle column.
W, H = 29, 56
MID = W // 2  # (the body's axis; the engine puts her feet here)
TOP = 4       # her head's first row (she is 52 rows tall)

SUZY_COLOURS = {
    'K': (0x24, 0x1C, 0x22),  # outline
    'S': (0xDC, 0x9E, 0x7C),  # skin
    's': (0xB6, 0x7C, 0x60),  # skin, shaded
    'c': (0xE4, 0x8A, 0x76),  # cheeks, lip
    'h': (0x2A, 0x26, 0x2E),  # hair, black
    'd': (0x4C, 0x48, 0x54),  # hair, its sheen
    'H': (0x8A, 0x88, 0x92),  # hair, grey streaks
    'L': (0xC4, 0xC4, 0xCC),  # hair, silver streaks
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
}

# Her hair: mostly black, a few grey and silver strands; greyer at the hairline.
DARK = 'hdhhHhhdhhLh'
GREY = 'hLhHdL'


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


def comb(c, cx, cy, width, region, strands=DARK, hairline=GREY):
    """Her hair in `region` combed into strands along lines through cx, cy
    (where it is pulled back to), coloured in turn; beside her face (the
    hairline) from the greyer strands."""
    face = [[c.cells[y][x] in 'Ssc' for x in range(c.width)] for y in range(c.height)]
    for y in range(c.height):
        for x in range(c.width):
            if c.cells[y][x] in 'hdHL' and region(x, y):
                a = int(math.floor(math.atan2(x - cx, cy - y) / width))
                near = any(face[yy][xx] for yy in range(max(0, y - 1), min(c.height, y + 2))
                           for xx in range(max(0, x - 1), min(c.width, x + 2)))
                seq = hairline if near else strands
                c.cells[y][x] = seq[a % len(seq)]


def streak_down(c, centre, region, strands, phase=0):
    """A tail of hair streaked along its length (`centre(y)` is its middle)."""
    for y in range(c.height):
        for x in range(c.width):
            if c.cells[y][x] == 'h' and region(x, y):
                k = int(math.floor(x - centre(y) + 0.5)) + phase
                c.cells[y][x] = strands[k % len(strands)]


# Facing the viewer (and away): the head and the shirt are drawn pixel by
# pixel; the legs walk.

FRONT_HEAD = [  # x 7..21 (the middle at the 8th letter), y TOP..TOP+13
    '.....KKKKK.....',
    '...KKhhhhhKK...',
    '..KhhhhhhhhhK..',
    '.KhhhSSSSShhhK.',
    '.KhhSSSSSSShhK.',
    '.KhSddSSSddShK.',
    '.KhSSSSSSSSShK.',
    'KsSsKKSSSKKsSsK',
    'KsSSSSSsSSSSSsK',
    '.KScsSSSSSscSK.',
    '.KSSSWWWWWSSSK.',
    '..KSSScccSSSK..',
    '...KsSSSSSsK...',
    '....KKsssKK....',
]
FRONT_TALK = {  # (rows replaced, talking: counted from TOP)
    10: '.KSSSKWWWKSSSK.',
    11: '..KSScMMMcSSK..',
}

FRONT_BODY = [  # x 4..24 (the middle at the 11th letter), y 18..36
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
    '.KSsKggGGGGGGGggKsSK.',
    '.KSsKKgGGGGGGGgKKsSK.',
    '.KSsKKgGGGGGGGgKKsSK.',
    'KSsK.KgGGGGGGGgK.KsSK',
    'KSsKKgggggggggggKKsSK',
    'KSsKKKKKKKKKKKKKKKsSK',
    'KSSK.............KSSK',
    'KSSK.............KSSK',
    '.KK...............KK.',
]

BACK_HEAD = [  # x 7..21, y TOP..TOP+13
    '.....KKKKK.....',
    '...KKhhhhhKK...',
    '..KhhhhhhhhhK..',
    '.KhhhhhhhhhhhK.',
    '.KhhhhhhhhhhhK.',
    '.KhhhhhhhhhhhK.',
    '.KhhhhhhhhhhhK.',
    'KshhhhhhhhhhhsK',
    'KshhhhTTThhhhsK',
    '.KhhhhhhhhhhhK.',
    '..KhhhhhhhhhK..',
    '..KhhhhhhhhhK..',
    '...KSShhhSSK...',
    '....KSSSSSK....',
]

BACK_BODY = [  # x 4..24, y 18..36
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
    '.KSsKggGGGGGGGggKsSK.',
    '.KSsKKgGGGGGGGgKKsSK.',
    '.KSsKKgGGGGGGGgKKsSK.',
    'KSsK.KgGGGGGGGgK.KsSK',
    'KSsKKgggggggggggKKsSK',
    'KSsKKKKKKKKKKKKKKKsSK',
    'KSSK.............KSSK',
    'KSSK.............KSSK',
    '.KK...............KK.',
]

HIPS = [(8, 20), (7, 21), (6, 22), (6, 22), (6, 22), (6, 22)]  # y 32..37 (full hips)
CROTCH = 38


def front_legs(c, lift, b, back=False):
    """Hips, both legs in jeans (full thighs, touching at the top), the
    sneakers; `lift` > 0 raises her right foot (the viewer's left; from
    behind, the viewer's right), < 0 the other."""
    rows(c, 32 + b, HIPS, 'J')
    for mirror in (False, True):
        up = max(0, lift) if mirror == back else max(0, -lift)
        X = (lambda x: 2 * MID - x) if mirror else (lambda x: x)
        top, bottom = CROTCH + b, 51 - up
        for y in range(top, bottom + 1):
            f = (y - top) / (bottom - top)
            x0 = 6 if f < 0.2 else 7 if f < 0.42 else 8 if f < 0.62 else 9
            span(c, y, X(x0), X(14 if y < top + 2 else 13), 'J')
        rows(c, bottom + 1, [(X(9), X(13))] + [(X(8), X(13))] * 3, 'W')


def jeans_shading(c, b, back=False):
    recolour(c, 'J', 'j', lambda x, y: y == 34 + b or abs(x - MID) >= 7 or (abs(x - MID) == 2 and y >= CROTCH + 2 + b))
    if not back:
        recolour(c, 'J', 'i', lambda x, y: CROTCH + 1 + b <= y <= 44 and abs(x - MID) in (4, 5))
        recolour(c, 'J', 'i', lambda x, y: y in (46, 47) and abs(x - MID) == 4)


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
    # Her long hair, behind her neck and shoulders.
    behind = Canvas(W, H)
    rows(behind, 13 + b, [(8, 20)] * 7, 'h')
    for x in (10, 18):
        span(behind, 16 + b, x, x, 'd'); span(behind, 17 + b, x, x, 'd')
    paste(c, behind)
    stamp(c, 4, 18 + b, FRONT_BODY)
    # The sling bag at her left hip (the viewer's right), on its strap from
    # her right shoulder, down under the emblem.
    bag = Canvas(W, H)
    rows(bag, 30 + b, [(16, 20)] * 4 + [(17, 19)], 'T')
    paste(c, bag)
    span(c, 31 + b, 17, 19, 't')
    c.put(18, 32 + b, 't')
    c.line([(10, 19 + b), (10, 25 + b), (16, 30 + b)], 'T')
    # The watch on her left wrist.
    c.put(22, 33 + b, 'T'); c.put(23, 33 + b, 'T')
    head = FRONT_HEAD[:]
    if talking:
        for y, line in FRONT_TALK.items():
            head[y] = line
    stamp(c, 7, TOP + b, head)
    # (Combed back from her forehead; the brows left alone.)
    comb(c, MID, TOP + 10 + b, 0.3, lambda x, y: y <= TOP + 9 + b and (y <= TOP + 4 + b or abs(x - MID) >= 5))
    # A loose grey strand by each temple.
    c.put(9, TOP + 6 + b, 'H'); c.put(19, TOP + 6 + b, 'L')
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
    for x0 in (8, 17):
        span(c, 35 + b, x0, x0 + 3, 'j')
        c.put(x0, 36 + b, 'j'); c.put(x0 + 3, 36 + b, 'j')
    stamp(c, 4, 18 + b, BACK_BODY)
    # The strap across her back, from her right shoulder to her left hip.
    c.line([(18, 19 + b), (10, 31 + b)], 'T')
    c.put(5, 33 + b, 'T'); c.put(6, 33 + b, 'T')  # the watch
    stamp(c, 7, TOP + b, BACK_HEAD)
    comb(c, MID, TOP + 11 + b, 0.17, lambda x, y: y <= TOP + 13 + b, strands='hdhhHhhdhhhLhhdh', hairline='hdhhHhhdhhhLhhdh')
    # The ponytail down her back from its tie, swaying a little as she walks.
    top, end = TOP + 9 + b, TOP + 26 + b
    sway = (0, 0.5, 0, -0.5)[step]
    def centre(y):
        t = (y - top) / (end - top)
        return MID + 0.7 * math.sin(t * math.pi * 1.2) + sway * t
    p = Canvas(W, H)
    for y in range(top, end + 1):
        t = (y - top) / (end - top)
        half = 1.6 + 1.3 * t / 0.15 if t < 0.15 else 2.9 - 2.4 * (t - 0.15) / 0.85
        span(p, y, int(round(centre(y) - half)), int(round(centre(y) + half)), 'h')
    paste(c, p)
    streak_down(c, centre, lambda x, y: top <= y, 'hdhHhhdh', phase=2)
    return c


# Facing right.

SIDE_HEAD = [  # x 5..21, y TOP..TOP+13
    '......KKKKK......',
    '....KKhhhhhKK....',
    '...KhhhhhhhhhK...',
    '..KhhhhhhhhhSK...',
    '..KhhhhhhhhSSSK..',
    '..KhhhhhhhSSddK..',
    '..KhhhhhSSSSSSK..',
    '..KhhhhSsSsKKSK..',
    '..KhhhhSsSSSSSSK.',
    '...KhhhSSSScsSK..',
    '...KhhSSSSSSSWK..',
    '....KhSSSSSScK...',
    '.....KSSSSSSK....',
    '........KKKKK....',
]
SIDE_TALK = {
    10: '...KhhSSSSSSSWM..',
    11: '....KhSSSSSMMK...',
}

POSES = {  # near foot x, far foot x, near up, far up, near knee x, far knee x
    0: (15, 13, 0, 0, 15, 13),
    1: (19, 9, 0, 1, 17, 11),
    2: (14, 16, 0, 2, 14, 17),
    3: (9, 19, 1, 0, 11, 17),
}


def side_leg(c, fx, kx, up, b, jeans, shoe):
    """A full thigh down to the knee, the calf, the sneaker."""
    top, ky, ankle = 35 + b, 45, 51 - up
    c.polygon([(9, top), (19, top), (kx + 3.2, ky), (fx + 2.5, ankle + 1), (fx - 2, ankle + 1), (kx - 2.8, ky)], jeans)
    rows(c, ankle + 1, [(fx - 2, fx + 1), (fx - 2, fx + 3), (fx - 3, fx + 4), (fx - 3, fx + 4)], shoe)


def side_arm(b, dx, skin, sleeve):
    a = Canvas(W, H)
    a.polygon([(12.5, 24 + b), (16, 24 + b), (16 + dx, 33 + b), (12.5 + dx, 33 + b)], skin)
    a.ellipse(12 + dx, 32 + b, 15 + dx, 35 + b, skin)
    lean = dx / 4
    a.polygon([(12.5, 19 + b), (15.5, 19 + b), (17, 21 + b), (16.5 + lean, 26.5 + b), (11.5 + lean, 26.5 + b), (11.5, 21 + b)], sleeve)
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
    # The hips (round behind), the near leg.
    low = Canvas(W, H)
    rows(low, 32 + b, [(10, 18), (9, 18), (8, 18), (8, 18), (8, 18), (8, 19), (9, 19)], 'J')
    side_leg(low, nfx, nkx, nup, b, 'J', 'W')
    paste(c, low)
    recolour(c, 'J', 'j', lambda x, y: y == 33 + b or x <= 9)
    recolour(c, 'J', 'i', lambda x, y: 37 + b <= y <= 43 and x >= 15 and c.get(x + 1, y) == 'J')
    recolour(c, 'J', 'i', lambda x, y: y in (34 + b, 35 + b) and x == 11)
    shoe_shading(c)
    # The shirt and the neck.
    top = Canvas(W, H)
    rows(top, 15 + b, [(12, 16)] * 5, 'S')
    rows(top, 19 + b, [(11, 17), (10, 18)] + [(10, 19)] * 5 + [(10, 18)] * 2 + [(11, 18)] * 3 + [(10, 18)] * 2, 'G')
    paste(c, top)
    recolour(c, 'G', 'g', lambda x, y: y >= 31 + b or x <= 11 or (y == 26 + b and x >= 17))
    recolour(c, 'S', 's', lambda x, y: y <= 18 + b)
    # The bag at her left hip, on its strap from her right shoulder.
    bag = Canvas(W, H)
    rows(bag, 29 + b, [(16, 20)] * 4 + [(17, 19)], 'T')
    paste(c, bag)
    span(c, 30 + b, 17, 19, 't')
    c.line([(11, 20 + b), (16, 29 + b)], 'T')
    # The ponytail down her back.
    p = Canvas(W, H)
    p.polygon([(5, 9 + b), (8, 9 + b), (8.5, 13 + b), (9.5, 18 + b), (10.5, 23 + b), (10, 27 + b), (8.5, 30 + b), (7, 27 + b), (6, 21 + b), (5, 15 + b)], 'h')
    paste(c, p)
    streak_down(c, lambda y: 6.5 + max(0, y - 9 - b) * 0.12, lambda x, y: x <= 10 and y >= 9 + b, 'hdhHhhdh', phase=3)
    # The head.
    head = SIDE_HEAD[:]
    if talking:
        for y, line in SIDE_TALK.items():
            head[y] = line
    stamp(c, 5, TOP + b, head)
    comb(c, 7, TOP + 6 + b, 0.3, lambda x, y: y <= TOP + 13 + b and 8 <= x <= 16)
    c.put(7, TOP + 5 + b, 'T'); c.put(7, TOP + 6 + b, 'T')  # the hair tie
    # The near arm, its watch.
    paste(c, side_arm(b, swing, 'S', 'G'))
    recolour(c, 'G', 'g', lambda x, y: y == 26 + b)
    c.put(13 + swing, 32 + b, 'T'); c.put(14 + swing, 32 + b, 'T')
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


# ---------------------------------------------------------------- Extra ----

# Extra's colours: letter -> RGB (' ' is never drawn). His glossy black coat
# a step above the outline, with a blue-grey sheen, so his shape and his face
# still read in a dark room.
EXTRA_COLOURS = {
    'K': (0x09, 0x08, 0x0C),  # outline
    'B': (0x26, 0x25, 0x2E),  # fur, black
    'b': (0x17, 0x16, 0x1D),  # fur, in shadow
    'L': (0x4A, 0x50, 0x66),  # fur, its gloss
    'l': (0x86, 0x90, 0xAE),  # fur, gloss at its brightest
    'P': (0xB4, 0x7C, 0x6A),  # inside the ears, a dusky pinkish brown
    'p': (0x7A, 0x48, 0x3E),  # inside the ears, deeper
    'r': (0xA0, 0x6A, 0x4A),  # the tan skin under the eyes
    'E': (0x62, 0x36, 0x20),  # eye, dark brown
    'D': (0x14, 0x0A, 0x08),  # eye, the pupil
    'w': (0xFF, 0xFF, 0xFF),  # the eyes' shine
    'N': (0x0C, 0x0B, 0x10),  # nose
    'n': (0x76, 0x74, 0x82),  # nose, lit
    'W': (0xF2, 0xF0, 0xEA),  # the white chin, white hairs, the tail's tip
    'g': (0xAC, 0xAC, 0xB4),  # grey hairs
    'G': (0x6A, 0x6A, 0x76),  # grey hairs, darker
    'M': (0x5E, 0x1A, 0x22),  # mouth, inside
    'T': (0xEC, 0x88, 0x98),  # tongue
}
EXTRA_FUR = 'BbLl'


def extra_over(c, draw, only=EXTRA_FUR):
    """What `draw` paints on a blank canvas laid on `c`, only over `only`."""
    t = Canvas(c.width, c.height)
    draw(t)
    for y in range(c.height):
        for x in range(c.width):
            if t.cells[y][x] != ' ' and c.cells[y][x] in only:
                c.cells[y][x] = t.cells[y][x]


def extra_outline(c, letters='BbLlPpg'):
    """His silhouette's edge (fur, ear or grey beside nothing) in 'K'; the
    face drawn into it keeps its own lines."""
    edge = [(x, y) for y in range(c.height) for x in range(c.width)
            if c.cells[y][x] in letters and any(c.get(x + dx, y + dy) == ' ' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        c.cells[y][x] = 'K'


def extra_spans(c, rows, colour='B', dy=0):
    """Rows of him (y -> [(x0, x1), ...], inclusive) filled in `colour`."""
    for y, segments in rows.items():
        for x0, x1 in segments:
            for x in range(x0, x1 + 1):
                c.put(x, y + dy, colour)


def extra_paint(c, pixels, dy=0):
    """Single pixels ((x, y) -> letter)."""
    for (x, y), colour in pixels.items():
        c.put(x, y + dy, colour)


# His build, as in the user's photos: slender and fine-boned, a slim body on
# thin legs; a round head about as wide as his body, held up on his neck, a
# short snout; huge ears angled up and out; the tail carried up in a curl.
# Drawn row by row (y -> spans), the outline after.
EXTRA_SIDE_BODY = {  # facing right
    # the ears: the near one, the far one ahead of it
    0: [(32, 33)], 1: [(32, 34), (37, 38)], 2: [(32, 34), (37, 38)], 3: [(32, 35), (37, 39)], 4: [(32, 35), (37, 39)],
    5: [(32, 36), (37, 40)], 6: [(32, 40)],
    # the round head, the short snout
    7: [(32, 39)], 8: [(32, 40)], 9: [(31, 41)], 10: [(31, 41)], 11: [(31, 42)], 12: [(31, 44)], 13: [(30, 45)],
    14: [(30, 45)], 15: [(30, 44)], 16: [(30, 42)],
    # the neck, the back, the slim body, the belly tucked
    17: [(29, 37)], 18: [(28, 37)], 19: [(15, 37)], 20: [(13, 37)], 21: [(12, 37)], 22: [(12, 37)], 23: [(12, 37)],
    24: [(12, 37)], 25: [(13, 36)], 26: [(13, 19), (25, 36)], 27: [(14, 18), (28, 35)], 28: [(29, 34)],
}
EXTRA_SIDE_TAIL = {18: [(13, 14)], 17: [(12, 13)], 16: [(12, 13)], 15: [(12, 13)], 14: [(13, 14)], 13: [(14, 17)]}
# The near ear's dusky pink inside, the far ear in shadow.
EXTRA_SIDE_EARS = {
    (32, 1): 'P', (33, 2): 'P', (33, 3): 'P', (34, 3): 'P', (33, 4): 'p', (34, 4): 'P', (33, 5): 'p', (34, 5): 'P', (35, 5): 'P',
    (34, 6): 'p', (35, 6): 'P', (38, 2): 'b', (38, 3): 'p', (38, 4): 'p', (38, 5): 'p', (39, 5): 'b', (39, 4): 'b',
}
# His face: the big round eye with its shine and the tan under it; the black
# nose at the snout's end; grey about the mouth; the white chin under it.
EXTRA_SIDE_FACE = {
    (37, 9): 'D', (38, 9): 'w', (37, 10): 'E', (38, 10): 'D', (36, 9): 'K', (36, 10): 'K', (37, 8): 'K', (38, 8): 'K',
    (37, 11): 'r', (38, 11): 'r',
    (44, 12): 'N', (44, 13): 'N', (45, 13): 'n', (45, 14): 'N', (43, 12): 'K',
    (41, 13): 'G', (42, 14): 'g',
    (40, 15): 'K', (41, 15): 'K', (42, 15): 'K', (43, 15): 'K',
    (39, 16): 'g', (40, 16): 'W', (41, 16): 'W', (42, 16): 'g',
}
EXTRA_SIDE_TALK = {  # the jaw dropped, the tongue
    (41, 15): 'M', (42, 15): 'M', (43, 15): 'M', (41, 16): 'T', (42, 16): 'W', (40, 16): 'W', (40, 17): 'W', (41, 17): 'g',
}
EXTRA_FRONT_BODY = {  # facing the viewer: the ears, the head, the neck, the chest
    0: [(6, 7), (26, 27)], 1: [(6, 8), (25, 27)], 2: [(7, 9), (24, 26)], 3: [(7, 10), (23, 26)], 4: [(8, 11), (22, 25)],
    5: [(8, 12), (13, 20), (21, 25)], 6: [(9, 24)], 7: [(10, 23)], 8: [(10, 23)], 9: [(10, 23)], 10: [(10, 23)],
    11: [(11, 22)], 12: [(11, 22)], 13: [(12, 21)], 14: [(13, 20)], 15: [(13, 20)], 16: [(14, 19)],
    17: [(13, 20)], 18: [(12, 21)], 19: [(11, 22)], 20: [(11, 22)], 21: [(11, 22)], 22: [(11, 22)], 23: [(11, 22)],
    24: [(11, 22)], 25: [(11, 22)], 26: [(12, 21)], 27: [(13, 20)],
}
EXTRA_FRONT_FACE = {  # the eyes set wide, the nose, grey, the mouth, the white chin
    (12, 8): 'K', (13, 8): 'K', (20, 8): 'K', (21, 8): 'K',
    (11, 9): 'K', (12, 9): 'D', (13, 9): 'w', (20, 9): 'w', (21, 9): 'D', (22, 9): 'K',
    (11, 10): 'K', (12, 10): 'E', (13, 10): 'D', (20, 10): 'D', (21, 10): 'E', (22, 10): 'K',
    (12, 11): 'r', (13, 11): 'r', (20, 11): 'r', (21, 11): 'r',
    (16, 11): 'N', (17, 11): 'N', (15, 12): 'N', (16, 12): 'n', (17, 12): 'N', (18, 12): 'N',
    (14, 13): 'G', (19, 13): 'G', (16, 13): 'K', (17, 13): 'K',
    (15, 14): 'K', (16, 14): 'K', (17, 14): 'K', (18, 14): 'K',
    (15, 15): 'g', (16, 15): 'W', (17, 15): 'W', (18, 15): 'g', (16, 16): 'W', (17, 16): 'g',
}
EXTRA_FRONT_TALK = {(16, 14): 'M', (17, 14): 'M', (16, 15): 'T', (17, 15): 'T', (16, 16): 'W', (17, 16): 'W'}
EXTRA_FRONT_EARS = {}
for _x, _y in ((7, 1), (7, 2), (8, 2), (8, 3), (9, 3), (9, 4), (10, 4), (9, 5), (10, 5), (11, 5)):
    EXTRA_FRONT_EARS[(_x, _y)] = EXTRA_FRONT_EARS[(33 - _x, _y)] = 'P'
for _x, _y in ((8, 4), (10, 6), (11, 6)):
    EXTRA_FRONT_EARS[(_x, _y)] = EXTRA_FRONT_EARS[(33 - _x, _y)] = 'p'


def extra_gloss(c, points, dy=0):
    """His sheen, only on his black fur."""
    for x, y, colour in points:
        if c.get(x, y + dy) == 'B':
            c.put(x, y + dy, colour)


def extra_side(step=0, talking=False):
    """Facing right: 48 x 40, feet on row 38. `step` 0..3 walks."""
    c = Canvas(48, 40)
    b = 1 if step in (1, 3) else 0  # (a bob as the legs pass)
    swing = [0, 2, 0, -2][step]

    def leg(lean, x0, top, colour, hind):
        # Thin, to a small paw; a hind leg angled back at the hock.
        for y in range(top, 38):
            x = x0 + round(lean * (y - top) / (38 - top)) - (1 if hind and y >= 32 else 0)
            extra_spans(c, {y: [(x, x + 1)]}, colour)
        x = x0 + lean - (1 if hind else 0)
        extra_spans(c, {38: [(x - 1, x + 2)]}, colour)
    # The far legs, in shadow, swinging opposite the near ones.
    leg(swing, 17, 26, 'b', True)
    leg(-swing, 34, 28, 'b', False)
    extra_spans(c, EXTRA_SIDE_BODY, 'B', b)
    extra_spans(c, EXTRA_SIDE_TAIL, 'B', b)
    leg(-swing, 15, 26, 'B', True)
    leg(swing, 32, 28, 'B', False)
    extra_outline(c)
    extra_paint(c, EXTRA_SIDE_EARS, b)
    extra_paint(c, EXTRA_SIDE_FACE, b)
    if talking:
        extra_paint(c, EXTRA_SIDE_TALK, b)
    # His gloss: the dome, the neck, along the back, the haunch, the tail.
    extra_gloss(c, ((34, 7, 'L'), (35, 7, 'l'), (36, 7, 'L'), (31, 12, 'L'), (31, 14, 'L'), (17, 20, 'L'), (18, 20, 'L'),
                    (19, 20, 'l'), (20, 20, 'L'), (21, 20, 'L'), (22, 20, 'L'), (13, 22, 'L'), (13, 23, 'L'), (12, 15, 'L')), b)
    # The tail's pale tip; white hairs on his chest.
    extra_paint(c, {(17, 14): 'g', (36, 21): 'g', (36, 22): 'W'}, b)
    return c


def extra_legs(c, top, step):
    """Both legs from the front or behind, thin, one lifted a little in step."""
    lift = (0, 1, 0, -1)[step]
    for x0, dy in ((13, max(0, lift)), (19, max(0, -lift))):
        extra_spans(c, {y: [(x0, x0 + 1)] for y in range(top, 38 - dy)})
        extra_spans(c, {38 - dy: [(x0 - 1, x0 + 2)]})


def extra_front(step=0, talking=False):
    """Facing the viewer: 34 x 40, feet on row 38."""
    c = Canvas(34, 40)
    extra_legs(c, 27, step)
    extra_spans(c, EXTRA_FRONT_BODY)
    extra_outline(c)
    extra_paint(c, EXTRA_FRONT_EARS)
    extra_paint(c, EXTRA_FRONT_FACE)
    if talking:
        extra_paint(c, EXTRA_FRONT_TALK)
    # (Not mirrored: the gloss on his dome and his chest.)
    extra_gloss(c, ((14, 6, 'L'), (15, 6, 'L'), (16, 6, 'l'), (17, 6, 'L'), (12, 21, 'L'), (12, 22, 'L')))
    extra_paint(c, {(16, 19): 'g', (16, 20): 'W'})
    return c


def extra_back(step=0):
    """Facing away: 34 x 40, feet on row 38."""
    c = Canvas(34, 40)
    extra_legs(c, 27, step)
    rows = dict(EXTRA_FRONT_BODY)
    for y in range(21, 27):
        rows[y] = [(10, 23)]  # (his hips)
    extra_spans(c, rows)
    extra_outline(c)
    # The ears' backs lit; his gloss; the skull's edge over his neck.
    extra_gloss(c, ((7, 1, 'L'), (8, 2, 'L'), (26, 1, 'L'), (25, 2, 'L'), (14, 6, 'L'), (15, 6, 'L'), (16, 6, 'l'), (17, 6, 'L'),
                    (12, 23, 'L'), (21, 23, 'L'), (14, 15, 'b'), (15, 16, 'b'), (18, 16, 'b'), (19, 15, 'b')))
    # The tail curled up on his back, its pale tip.
    crispy_stamp(c, 14, 17, ["..KKK.", ".KBLBK", "KBKKWK", "KBK.K.", ".KBK..", ".KBK..", "..KBK."])
    return c


def extra():
    frames = []
    side = [extra_side(s) for s in range(4)]
    for d, flip in ((RIGHT, False), (LEFT, True)):
        pick = (lambda f: f.mirrored()) if flip else (lambda f: f)
        frames.append((d, STAND, 0, pick(side[0])))
        frames += [(d, WALK, i, pick(side[i])) for i in range(4)]
        frames += [(d, TALK, 0, pick(side[0])), (d, TALK, 1, pick(extra_side(0, True)))]
    frames.append((FRONT, STAND, 0, extra_front()))
    frames += [(FRONT, WALK, i, extra_front(i)) for i in range(4)]
    frames += [(FRONT, TALK, 0, extra_front()), (FRONT, TALK, 1, extra_front(0, True))]
    frames.append((BACK, STAND, 0, extra_back()))
    frames += [(BACK, WALK, i, extra_back(i)) for i in range(4)]
    return frames


for _name, _pixels in (('EXTRA_SIDE_EARS', EXTRA_SIDE_EARS), ('EXTRA_SIDE_FACE', EXTRA_SIDE_FACE),
                       ('EXTRA_SIDE_TALK', EXTRA_SIDE_TALK), ('EXTRA_FRONT_FACE', EXTRA_FRONT_FACE),
                       ('EXTRA_FRONT_TALK', EXTRA_FRONT_TALK), ('EXTRA_FRONT_EARS', EXTRA_FRONT_EARS)):
    assert set(_pixels.values()) <= set(EXTRA_COLOURS), _name


# The custom characters (their number, name, the art, its colours, and how
# tall they stand against a person: Crispy and Extra are little dogs).
CUSTOM = [(1, 'Crispy', crispy, CRISPY_COLOURS, 0.3), (2, 'Suzy', suzy, SUZY_COLOURS, 0.95),
          (3, 'Extra', extra, EXTRA_COLOURS, 0.3)]


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
