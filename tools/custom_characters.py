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

Extra: the user's eight-pound black Chihuahua, drawn from the user's photos
(the photos are not kept) by a panel of artists and judges after the user's
corrections: slender and fine-boned, a small head (from the side, head and
snout about 41% of his body; from the front, the skull no wider than his
rounded chest) on a neck sloping forward; big ears flaring out more than up,
dusky pinkish brown inside; big round dark eyes with a shine and the tan under
them; a short snout, a black nose, grey about the mouth, his white goatee; a
few white hairs on his chest; thin legs about as long as his chest is deep;
the tail carried up in a curl to a pale tip. His glossy black a step above
the outline, with a blue-grey sheen, so he reads in a dark room. No collar
(that photo was his costume).

Crispy 2: Crispy again at Curse of Monkey Island's detail (SCUMM v8: 96 rows,
240 colours, smooth shading), as close as the panel could draw him to the
user's picture of him in his devil costume.

Extra 2: Extra at the same detail (96 rows, 236 colours), from the user's
picture and SIDE/BACK sheet; only a tiny bit of white on his chest.
"""
import argparse
import base64
import gzip
import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Facings and poses as the engine numbers them (World::SourceFrame); one
# carrying something lit (Sith Ewok 2's saber) lights it up (played
# backwards, puts it out) and stands, walks and talks with it lit.
LEFT, RIGHT, FRONT, BACK = 0, 1, 2, 3
STAND, WALK, TALK = 0, 1, 2
IGNITE, LIT_STAND, LIT_WALK, LIT_TALK = 4, 5, 6, 7

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


def crispy_stamp(c, x, y, rows):
    """Letters onto `c` from (x, y); '.' leaves what is there."""
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != '.':
                c.put(x + dx, y + dy, ch)


# Crispy, the user's eight-pound terrier, in his red devil costume.
#
# Drawn from the user's model picture: a scruffy tan terrier, a red hood with
# two curved horns framing his face in a dark rim, a red cape over his back
# tied under his chin with black ties (one red flap hanging at his chest), his
# tail up.  Every pixel is baked into the letter tables below.

CRISPY_COLOURS = {
    'K': (0x1A, 0x10, 0x10),  # outline, hood rim, cape trim, ties
    'h': (0xF2, 0x44, 0x34),  # costume red, lit
    'R': (0xCE, 0x16, 0x14),  # costume red
    'r': (0x96, 0x08, 0x10),  # costume red, shaded
    'q': (0x5A, 0x0C, 0x12),  # costume red, deep shadow
    'w': (0xFA, 0xEC, 0xD4),  # whisker and beard wisps
    'W': (0xF0, 0xCC, 0x9C),  # fur, cream
    'F': (0xDC, 0xAA, 0x74),  # fur, tan
    'f': (0xBC, 0x88, 0x56),  # fur, shaded
    'd': (0x82, 0x5A, 0x3C),  # fur, dark (eye rims, far legs)
    'E': (0x1E, 0x12, 0x0E),  # eye
    'e': (0xF4, 0xF0, 0xE8),  # eye glint
    'N': (0x16, 0x12, 0x12),  # nose
    'n': (0x80, 0x78, 0x7A),  # nose, lit
    'M': (0x5A, 0x14, 0x1A),  # mouth, inside
    'P': (0xEC, 0x80, 0x90),  # tongue
}


def crispy_table(c, x0, y0, rows):
    """A letter table onto `c` from (x0, y0); '.' is nothing."""
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != '.':
                c.put(x0 + x, y0 + y, ch)


def crispy_ring(c):
    """A 1-pixel 'K' line round the outside of everything drawn."""
    edge = [(x, y) for y in range(c.height) for x in range(c.width)
            if c.cells[y][x] == ' ' and any(c.get(x + dx, y + dy) not in (' ', 'K')
                                            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        c.cells[y][x] = 'K'


def crispy_column(c, x, top, foot, leg, paw):
    """A straight leg: `leg` letters on rows top..foot-1 from x, `paw` on foot."""
    for y in range(top, foot):
        crispy_table(c, x, y, [leg])
    crispy_table(c, x, foot, [paw])


# ---------------------------------------------------------------- side ----

def crispy_leg(c, top, x_top, x_foot, foot, cols, thigh=0, behind=None):
    """A side leg from row `top` (at x_top) to its paw on row `foot` (at
    x_foot): three pixels wide (`cols` back, middle, front), the paw one
    longer forward; `thigh` widens its first rows backwards.  Where it
    passes over the pixels in `behind` (a far leg) it gets a 'K' edge.
    Returns the pixels it drew."""
    back, mid, front = cols
    n = max(1, foot - top)
    got = {}
    for y in range(top, foot):
        x = int(round(x_top + (x_foot - x_top) * (y - top) / n))
        w0 = x - (thigh if y - top < 3 else 0)
        for xx in range(w0, x + 3):
            got[(xx, y)] = back if xx == w0 else (front if xx == x + 2 else mid)
    for xx in range(x_foot, x_foot + 4):
        got[(xx, foot)] = back if xx == x_foot else mid
    if behind:
        for (x, y) in got:
            for dx, dy in ((1, 0), (-1, 0), (0, 1)):
                p = (x + dx, y + dy)
                if p not in got and p in behind and c.get(*p) == behind[p]:
                    c.put(p[0], p[1], 'K')
    for (x, y), ch in got.items():
        c.put(x, y, ch)
    return got


def crispy_part(c, near, far, top):
    """Where a near leg passes two pixels from a far leg the outline would run
    double (a dark patch under the belly): the outline pixel next to the far
    leg joins the far leg instead, so one 'K' parts the two legs.  The same
    between a far leg and the chest flap, where the flap takes the pixel."""
    for y in range(top, c.height):
        for x in range(1, c.width - 2):
            a, k1, k2, z = (c.get(x + i, y) for i in range(-1, 3))
            if k1 != 'K' or k2 != 'K' or a in (' ', 'K') or z in (' ', 'K'):
                continue
            if far.get((x + 2, y)) == z and near.get((x - 1, y)) == a:
                c.put(x + 1, y, CRISPY_FAR[0])
                c.put(x + 2, y, CRISPY_FAR[1])
            elif far.get((x - 1, y)) == a and near.get((x + 2, y)) == z:
                c.put(x, y, CRISPY_FAR[0])
                c.put(x - 1, y, CRISPY_FAR[1])
            elif far.get((x - 1, y)) == a and z in 'rR' and ' ' not in (
                    c.get(x + 1, y - 1), c.get(x + 1, y + 1)):
                c.put(x + 1, y, 'r')  # the chest flap, likewise


CRISPY_X0 = 5  # CRISPY_SIDE_BODY's column 0 on the 48-wide canvas
CRISPY_SIDE_BODY = [
    "...........................................",  # 0
    ".....................R.........R...........",  # 1
    "....................hR.........Rh..........",  # 2
    "...................hRr.........rRh.........",  # 3
    "..................hRr.RhhhhhhRR.rRh........",  # 4
    "..................hRRqRhhhhRRRqrRRh........",  # 5
    "..................hRRrqRrKKKKKKrRRh........",  # 6
    "....F.............rRRRRKFFWWWFFFKRr........",  # 7
    "...FF.............rRRRKFFWWWWFFWFFr........",  # 8
    "..FF..............rRRKfFFWWWWFFWWFr........",  # 9
    ".FF..............rRRKfdFFfffFFFFfFw........",  # 10
    ".FF..............rRRKFfFFEEeFFFfEeF........",  # 11
    ".Ff....f........rrRRKFfFFEEEFWFFEEFWw......",  # 12
    ".FfF..fFFFRhhhhhRRrRKfFFFEEEFWWWWWFW.......",  # 13
    ".fFFFFFFFKRhhhRRRRrRKdFdFFFFWWWNnnNW.......",  # 14
    "..fFFFFFFKRRRRRRRRrRKdfFFFFWWWWNNNNWw......",  # 15
    "..fFWFFFFKRRRRRrRRRrRKFFfWWWWdWWNNWW.......",  # 16
    "..fFWFFFFRRRRRrRRRRrrKKFfWWWWfWWdWW........",  # 17
    ".ffFFFFfFRRRRRrRRRRrrrKFfWWWWdKKKdWw.......",  # 18
    "..fFFFFfFRRRRRrRRRRRrrrKfWWwWWWWWwW........",  # 19
    "..fFFFfFFRRRRRrRRRRRRrrKwWKKWwWWWWw........",  # 20
    "..fFFFfFFRRRRRRrRRRRRrKWwWKKWwRRR..........",  # 21
    "..fWFFFFFRRRRRRrRRRRrrKWFKWwKWRhR..........",  # 22
    "..fWFFFFFRrRRRRrRRRrrrKWWKWFKWRhR..........",  # 23
    ".ffFFFFFFKrrRRRrRRrrrKWWFKWFKWRhR..........",  # 24
    "..fFFfFFFKrrrRRrRrrrKFWWFKWFWWrRR..........",  # 25
    "..fFFFFFFFKrrrrrrrrKFFWWFKFFWWrRR..........",  # 26
    "..fFFFFFFFFKKKKKKKKFFFWWFKFFFWrRR..........",  # 27
    "...fFFFF..f.........FFWWFFFFFFrRR..........",  # 28
    "..............................rRR..........",  # 29
    "...............................rR..........",  # 30
    "...............................rR..........",  # 31
    "................................R..........",  # 32
]
CRISPY_NEAR = ('f', 'F', 'W')
CRISPY_FAR = ('d', 'f', 'f')
CRISPY_SIDE_TALK = ["dMMMd", ".MPM."]  # the jaw dropped a little, from (29, 18)


def crispy_side(step=0, talking=False):
    """Facing right (three-quarter, as in the model): 48 x 40, feet on row 38."""
    c = Canvas(48, 40)
    b = 1 if step in (1, 3) else 0
    sw = (0, 2, 0, -2)[step]
    far = crispy_leg(c, 27 + b, CRISPY_X0 + 10, CRISPY_X0 + 11 - sw, 36, CRISPY_FAR)
    far.update(crispy_leg(c, 28 + b, CRISPY_X0 + 27, CRISPY_X0 + 27 + sw, 36, CRISPY_FAR))
    crispy_table(c, CRISPY_X0, b, CRISPY_SIDE_BODY)
    near = crispy_leg(c, 27 + b, CRISPY_X0 + 4, CRISPY_X0 + 4 + sw, 37, CRISPY_NEAR, thigh=1, behind=far)
    near.update(crispy_leg(c, 27 + b, CRISPY_X0 + 20, CRISPY_X0 + 20 - sw, 37, CRISPY_NEAR, behind=far))
    if talking:
        crispy_table(c, CRISPY_X0 + 29, 18 + b, CRISPY_SIDE_TALK)
    crispy_ring(c)
    crispy_part(c, near, far, 29 + b)
    return c


# --------------------------------------------------------------- front ----

CRISPY_FRONT_BODY = [
    "..................................",  # 0
    ".........R..............R.........",  # 1
    "........hR..............Rh........",  # 2
    ".......hRr..............rRh.......",  # 3
    "......hRr.RhhhhhhhhhhhhR.rRh......",  # 4
    "......hRRqRRRhhhhhhhhRRRqRRh......",  # 5
    ".....rhRRrqRRRRRRRRRRRRqrRRhr.....",  # 6
    "....rRRRRRRKKKKKKKKKKKKRRRRRRr....",  # 7
    "....rRRRRKKFFFFFWWFFFFFKKRRRRr....",  # 8
    "....rRRRKFFFFFFWWWWFFFFFFKRRRr....",  # 9
    "....rRRKfFFFFFFFWWFFFFFFFfKRRr....",  # 10
    "....rRRKFfFEEeFFWWFFEEeFfFKRRr....",  # 11
    "....rRRKFfFEEEFFWWFFEEEFfFKRRr....",  # 12
    "....rRRKfFFEEEFWWWWFEEEFFfKRRr....",  # 13
    "....rRRKdFFFFFWNnnNWFFFFFdKRRr....",  # 14
    "....rRRKFFFFWWWNNNNWWWFFFFKRRr....",  # 15
    "....rRRKFFWWfWWWNNWWWfWWFFKRRr....",  # 16
    "....rRRRKFWWWWWWddWWWWWWFKRRRr....",  # 17
    "....rRRRKFWWWWWdKKdWWWWWFKRRRr....",  # 18
    ".....rRRRKWWWwWWWWWWwWWWKRRRr.....",  # 19
    "......rRRRKWwWWwWWwWWwWKRRRr......",  # 20
    ".....rRRRRRKwWfwKKwfWwKRRRRRr.....",  # 21
    "....rRRRRRRKFwFKwWKFKhRRRRRRRr....",  # 22
    "...rRRRRRRRKFWFKWWKWKhRRRRRRRRr...",  # 23
    "...rRRRRRRrKFWWKWWWWKhRrRRRRRRr...",  # 24
    "..rrRRRRRRrKFWWKWWWWKRRrRRRRRRrr..",  # 25
    "..rrRRRRRrrKFWWWWWWFKRrrrRRRRRrr..",  # 26
    "..rrrRRRRrrKFFWWWWWWKRrrrRRRRrrr..",  # 27
    "..rrrrrrrrrKFFWWWWWWKRrrrrrrrrrr..",  # 28
    "...........fFFFWWWWFFRr...........",  # 29
    ".....................r............",  # 30
]
CRISPY_FRONT_TALK = ["dMMMMd", ".dMPd."]  # the mouth open, from (14, 18)


def crispy_front(step=0, talking=False):
    """Facing the viewer: 34 x 40, feet on row 38."""
    c = Canvas(34, 40)
    b = 1 if step in (1, 3) else 0
    lift_l = 2 if step == 1 else 0
    lift_r = 2 if step == 3 else 0
    # the hind legs, behind
    crispy_column(c, 6, 30 + b, 36 - lift_r // 2, ".dff", "dfff")
    crispy_column(c, 24, 30 + b, 36 - lift_l // 2, "ffd", "fffd")
    crispy_table(c, 0, b, CRISPY_FRONT_BODY)
    crispy_column(c, 10, 30 + b, 37 - lift_l, ".fFWW", "fFWWW")
    crispy_column(c, 19, 30 + b, 37 - lift_r, "WWFf", "WWWFf")
    if talking:
        crispy_table(c, 14, 18 + b, CRISPY_FRONT_TALK)
    crispy_ring(c)
    return c


# ---------------------------------------------------------------- back ----

CRISPY_BACK_BODY = [
    "..................................",  # 0
    ".........R..............R.........",  # 1
    "........hR..............Rh........",  # 2
    ".......hRr..............rRh.......",  # 3
    "......hRr.RhhhhhhhhhhhhR.rRh......",  # 4
    "......hRRqRRhhhhhRRRRRRRqRRR......",  # 5
    ".....rhRRrqRRRRRRRRRRRRqrRRRr.....",  # 6
    "....rRRRRRRRRRRRRRRRRRRRRrrrrr....",  # 7
    "....rRhhRRRRRRRRRRRRRRRRRrrrrr....",  # 8
    "....rRhRRRRRRKKRRRRRRRRRRrrrrr....",  # 9
    "....rRRRRRRRKWFKRRRRRRRRRrrrrr....",  # 10
    "....rRRRRRRRKFWFKRRRRRRRRrrrrr....",  # 11
    ".....rRRRRRRRKFFFKRRRRRRRrrrr.....",  # 12
    "......rrRRRRRRKWFfKRRRRRRrrr......",  # 13
    "....RRqqrrrrrrKWFfKrrrrrrrqqRR....",  # 14
    "...rRhRRqqqqqqKWFfKqqqqqqqrrrrr...",  # 15
    "...rRhRRRRRRRRKWFFfKRRRRRRrrrrr...",  # 16
    "...rRhRRRRRRRKFWFFfKKRRRRRrrrrr...",  # 17
    "...rRRRRrRRKKfFWFFfFFKKRRrrrrrr...",  # 18
    "...rRRRRrRKFFFFWFFfFFFFKRrrrrrr...",  # 19
    "...rRRRRrKFFFFFFFFFFFFFfKrrrrrr...",  # 20
    "...rRRRrRKFFFFFFFFFFFFFfKRrrrrr...",  # 21
    "...KrRRrKfFFFFFFFFFFFFFffKrrrrK...",  # 22
    "...FKKrrKfFFFFFFFFFFFFFffKrrKKF...",  # 23
    "...fFFKKKfFFFFFFFFFFFFFffKKKfff...",  # 24
    "...fFFFFffFFFFFFFFFFFFFffffffff...",  # 25
    "...fFFFFfFFFFFFFFFFFFFFffffffff...",  # 26
    "...fFFFFfFFFFFFFFFFFFFFffffffff...",  # 27
    "...fFFFFFfFFFFFFFFFFFFFffffffff...",  # 28
    "..FfFFFFFfFFFFFFFFFFFFFffffffffF..",  # 29
    "....fFFFFFfFFFFFffFFFFFfffffff....",  # 30
    "......fFFFFfFf......fFffffff......",  # 31
    ".......fFFFF..........FFFFf.......",  # 32
]


def crispy_back(step=0):
    """Facing away: 34 x 40, feet on row 38."""
    c = Canvas(34, 40)
    b = 1 if step in (1, 3) else 0
    lift_l = 2 if step == 1 else 0
    lift_r = 2 if step == 3 else 0
    # the front legs, further off
    crispy_column(c, 5, 30 + b, 36 - lift_r // 2, "df", "ddf")
    crispy_column(c, 27, 30 + b, 36 - lift_l // 2, "fd", "fdd")
    crispy_table(c, 0, b, CRISPY_BACK_BODY)
    crispy_column(c, 8, 31 + b, 37 - lift_l, "fFWF", "fFWFF")
    crispy_column(c, 22, 31 + b, 37 - lift_r, "FFFf", "FFFFf")
    crispy_ring(c)
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


# ----------------------------------------------------------- Sith Ewok ----

# The Sith Ewok: a short, stocky Ewok in a very dark charcoal-purple hooded
# robe (two round bear ears on the hood, a thick cowl round the neck, wide
# sleeves), brown fur, small glowing amber eyes under a stern brow, a black
# nose and a frown; a brown belt with a little square silver buckle and a
# black and silver crossguard hilt hanging at the left hip (the viewer's right
# from the front). 40 x 48, the soles on row 46 (row 47 empty). The robe is
# lit at its rims and folds in a muted purple-grey and outlined in near-black,
# so it reads on dark backgrounds too.
#
# Walking bobs the figure down a row on steps 1 and 3: the finished body is squashed
# by one row in the robe below the hands (so its shading does not shimmer),
# then the hilt (hanging from the belt) and the feet are drawn.
EWOK_COLOURS = {
    'K': (0x0C, 0x08, 0x0C),  # outline, near-black
    'k': (0x1C, 0x14, 0x1C),  # inside the hood; deep folds
    'r': (0x2C, 0x22, 0x2C),  # robe, shaded
    'R': (0x3C, 0x30, 0x3C),  # robe
    'h': (0x5A, 0x4A, 0x58),  # robe, lit folds
    'H': (0x80, 0x6E, 0x7C),  # robe, its brightest rim
    'P': (0x3E, 0x1E, 0x10),  # the dark brown inner panel
    'm': (0x4A, 0x22, 0x0E),  # fur, deepest
    'f': (0x7A, 0x3A, 0x14),  # fur, shaded
    'F': (0xA6, 0x56, 0x22),  # fur
    'L': (0xCC, 0x80, 0x44),  # fur, lit; the muzzle
    'N': (0x10, 0x08, 0x08),  # nose, mouth
    'M': (0x6C, 0x14, 0x14),  # mouth, open
    'Y': (0xFF, 0xD8, 0x8C),  # eye, its glow
    'O': (0xE8, 0x7C, 0x1C),  # eye, amber
    'B': (0x70, 0x3A, 0x1C),  # belt
    'b': (0x46, 0x22, 0x12),  # belt, shaded
    'S': (0xDC, 0xD4, 0xCC),  # silver, lit
    's': (0x8C, 0x84, 0x80),  # silver
    'G': (0x26, 0x26, 0x2C),  # the hilt's black grip
    'g': (0x5E, 0x5A, 0x60),  # the grip's steel edge
    'C': (0xC8, 0x70, 0x38),  # the hilt's copper ring
}
EWOK_ROBE = 'rRhH'
EWOK_FUR = 'mfFL'
EWOK_CUT = 34   # the robe row taken out on a bob


def ewok_over(c, x, y, colour, only=EWOK_ROBE):
    """`colour` at (x, y) only where `only` is."""
    if c.get(x, y) in only:
        c.put(x, y, colour)


def ewok_over_line(c, points, colour, only=EWOK_ROBE):
    t = Canvas(c.width, c.height)
    t.line(points, colour)
    for y in range(c.height):
        for x in range(c.width):
            if t.cells[y][x] != ' ':
                ewok_over(c, x, y, colour, only)


def ewok_mirror_rows(half):
    """Rows from their left half, mirrored about the last column."""
    return [h + h[-2::-1] for h in half]


def ewok_bob(c):
    """Down a row: the robe row CUT taken out, everything above it lowered."""
    del c.cells[EWOK_CUT]
    c.cells.insert(0, [' '] * c.width)


# ------------------------------------------------------------- the hilt ----
# A black grip with a silver edge and catches, one copper ring in its lower
# third; the crossguard's short silver quillons near the bottom (row 39), the
# emitter under them, all centred on the grip.
EWOK_HILT = [
    "KKKK",   # 24
    "KSSK",   # 25 the pommel
    "KssK",
    "KgGK",   # the black grip
    "KgGK",
    "KgGK",
    "KSsK",   # 30 a silver band
    "KgGK",
    "KgGK",
    "KgGK",
    "KCCK",   # 34 the copper ring
    "KgGK",
    "KgGK",
    "KssK",   # 37 the collar over the guard
]
EWOK_GUARD = [
    "KKKKKKKK",   # 38
    "KSsSSsSK",   # 39 the quillons
    "KKKgGKKK",
    "..KSsK..",   # 41 the emitter
    "..KKKK..",
]


def ewok_hilt(c, x, y):
    """The hilt's grip at x+1..x+2 from row y (its top outline)."""
    crispy_stamp(c, x, y, EWOK_HILT)
    crispy_stamp(c, x - 2, y + len(EWOK_HILT), EWOK_GUARD)


# -------------------------------------------------------------- the feet ----
EWOK_FOOT_FRONT = [
    ".KKKKKK.",
    "KfFLLFfK",
    "KFLLLLFK",
    "KFfFfFfK",   # the toes
    "KKKKKKKK",   # the soles (row 46)
]
EWOK_FOOT_BACK = [   # heels
    ".KKKKKK.",
    "KfffffmK",
    "KFFFFfmK",
    "KFLLFfmK",
    "KKKKKKKK",
]
EWOK_FOOT_SIDE = [   # facing right, the near foot
    "..KKKKK..",
    ".KfFFFLK.",
    "KfFFFLLLK",
    "KfFFfFfFK",
    "KKKKKKKKK",
]
EWOK_FOOT_FAR = [    # the far foot, in shadow
    "..KKKKK..",
    ".KmffFfK.",
    "KmffFFfFK",
    "KmfmfmfmK",
    "KKKKKKKKK",
]


def ewok_hem_line(c):
    """A dark line where the robe's hem lies on a foot."""
    for y in range(38, 46):
        for x in range(c.width):
            if c.get(x, y) in EWOK_ROBE + 'kP' and c.get(x, y + 1) in EWOK_FUR:
                c.put(x, y, 'K')


def ewok_foot(c, x, lift, rows, hem):
    """A foot from (x, 42 - lift); a lifted foot shows only below the hem."""
    for dy, row in enumerate(rows):
        y = 42 - lift + dy
        if lift and y < hem:
            continue
        for dx, ch in enumerate(row):
            if ch != '.':
                c.put(x + dx, y, ch)


# ------------------------------------------------------------- the front ----
# The face in the hood's opening, x 14..26 (axis x 20), from y 7.
EWOK_FRONT_FACE = ewok_mirror_rows([
    "kkkkkkk",   # 7  the hood's shadow over the brow
    "kkkkmmm",   # 8
    "kmmmfff",   # 9
    "fmmmFFF",   # 10 the stern brow, its inner ends lower
    "fOYmmFF",   # 11 the glowing eyes
    "fFFFFFL",   # 12
    "fFFFLNN",   # 13 the nose
    "fFFLLLN",   # 14
    "kfFLLLL",   # 15
    "kfFLLNN",   # 16 the frown
    "kffLNLL",   # 17
    ".kffLLL",   # 18
])
EWOK_FRONT_TALK = ewok_mirror_rows([  # rows 16..18: the mouth open a little
    "kfFLLNN",
    "kffLNMM",
    ".kffLNM",
])
EWOK_EAR = [".KKKK.",   # the round ear on the hood, from its top
       "KhHHhK",
       "KhrkrK",
       "KRkkrR"]


def ewok_robe_body(c, sway):
    """The robe from the shoulders to the hem (front and back alike)."""
    c.polygon([(10, 19), (31, 19), (36 + sway, 45), (5 + sway, 45)], 'R')
    # the wide sleeves
    c.polygon([(12, 19), (7, 21), (3, 26), (3, 29), (12, 29), (13, 24)], 'R')
    c.polygon([(29, 19), (34, 21), (38, 26), (38, 29), (29, 29), (28, 24)], 'R')


def ewok_shade_robe(c, sway):
    """The robe's sides in shadow toward the hem."""
    for y in range(24, 46):
        for x in range(40):
            if c.get(x, y) == 'R':
                t = (y - 24) // 5
                if x < 9 + sway + t or x > 31 + sway - t:
                    c.put(x, y, 'r')


EWOK_HAND = [  # the viewer's left hand, hanging out of the sleeve, from x 5, y 28
    "KFLLFK",
    "KFLLFK",
    "KFFFfK",
    "KfmfmK",   # the fingers
    ".KKKK.",
]
EWOK_HAND_BACK = [  # seen from behind: the back of the paw, darker
    "KffFfK",
    "KfFFfK",
    "KffFmK",
    "KmfmmK",
    ".KKKK.",
]


def ewok_hands(c, rows=EWOK_HAND):
    for x in list(range(5, 12)) + list(range(29, 36)):
        ewok_over(c, x, 27, 'k')   # the sleeves' openings, dark
    crispy_stamp(c, 5, 28, rows)
    crispy_stamp(c, 30, 28, [r[::-1] for r in rows])


def ewok_cowl(c):
    c.ellipse(7, 15, 33, 24, 'R')


def ewok_hood(c, back=False):
    c.ellipse(9, 1, 15, 7, 'R')
    c.ellipse(25, 1, 31, 7, 'R')
    if back:
        c.polygon([(10, 11), (30, 11), (28, 19), (20, 22), (12, 19)], 'R')
    c.ellipse(8, 3, 32, 20, 'R')


def ewok_sleeve_folds(c):
    ewok_over_line(c, [(7, 22), (4, 26)], 'H')
    ewok_over_line(c, [(9, 23), (8, 26)], 'k')
    ewok_over_line(c, [(33, 22), (36, 26)], 'h')
    ewok_over_line(c, [(31, 23), (32, 26)], 'k')


def ewok_cowl_folds(c):
    ewok_over_line(c, [(9, 17), (14, 20), (20, 21), (26, 20), (31, 17)], 'h')
    ewok_over_line(c, [(8, 20), (14, 23), (20, 24), (26, 23), (32, 20)], 'k')
    ewok_over_line(c, [(11, 22), (20, 23), (29, 22)], 'r')
    ewok_over_line(c, [(8, 17), (8, 20)], 'h')
    ewok_over_line(c, [(32, 17), (32, 20)], 'r')


def ewok_hood_lights(c):
    ewok_over_line(c, [(12, 5), (16, 4), (24, 4), (28, 5)], 'H')
    ewok_over_line(c, [(11, 6), (9, 10), (9, 13)], 'h')
    ewok_over_line(c, [(31, 8), (31, 13)], 'r')
    for x0 in (9, 26):
        crispy_stamp(c, x0, 1, EWOK_EAR if x0 < 20 else [r[::-1] for r in EWOK_EAR])


def ewok_belt(c, y, x0=12, x1=29):
    for x in range(x0, x1):
        if c.get(x, y) not in ' K':
            c.put(x, y, 'B')
        if c.get(x, y + 1) not in ' K':
            c.put(x, y + 1, 'b')


def ewok_front(step=0, talking=False):
    c = Canvas(40, 48)
    sway = (0, 1, 0, -1)[step]
    ewok_robe_body(c, sway)
    ewok_cowl(c)
    ewok_hood(c)
    c.outline()
    ewok_shade_robe(c, sway)
    # the inner panel down the front, between the buckle and the hilt
    for y in range(28, 44):
        s = sway if y > 40 else 0
        for x in range(19, 22):
            c.put(x + s, y, 'P')
        ewok_over(c, 18 + s, y, 'h')
        ewok_over(c, 22 + s, y, 'k')
    # robe folds
    ewok_over_line(c, [(14, 28), (12 + sway, 44)], 'k')
    ewok_over_line(c, [(15, 28), (14 + sway, 43)], 'h')
    ewok_over_line(c, [(28, 29), (29 + sway, 44)], 'k')
    ewok_over_line(c, [(9, 30), (8 + sway, 43)], 'h', 'r')
    ewok_sleeve_folds(c)
    ewok_hands(c)
    ewok_cowl_folds(c)
    ewok_hood_lights(c)
    # the face, in the hood's opening, its edge lit
    crispy_stamp(c, 14, 7, EWOK_FRONT_FACE)
    if talking:
        crispy_stamp(c, 14, 16, EWOK_FRONT_TALK)
    ewok_over_line(c, [(13, 8), (12, 12), (13, 17)], 'h')
    ewok_over_line(c, [(27, 8), (28, 12), (27, 17)], 'r')
    ewok_over_line(c, [(15, 6), (25, 6)], 'h')
    # the belt, its buckle
    ewok_belt(c, 26)
    crispy_stamp(c, 19, 25, ["sSs", "sKs", "sss"])
    b = 1 if step in (1, 3) else 0
    if b:
        ewok_bob(c)
    # the hilt at the left hip (the viewer's right)
    ewok_hilt(c, 24, 24 + b)
    lift = (0, 1, 0, -1)[step]
    ewok_foot(c, 9 + sway, max(0, lift), EWOK_FOOT_FRONT, 43)
    ewok_foot(c, 24 + sway, max(0, -lift), EWOK_FOOT_FRONT, 43)
    ewok_hem_line(c)
    return c


# -------------------------------------------------------------- the back ----

def ewok_back(step=0):
    c = Canvas(40, 48)
    sway = (0, 1, 0, -1)[step]
    ewok_robe_body(c, sway)
    ewok_cowl(c)
    ewok_hood(c, back=True)
    c.outline()
    ewok_shade_robe(c, sway)
    # the robe's folds down the back
    for x0, x1, colour in ((16, 15, 'h'), (20, 20, 'k'), (24, 25, 'h'), (13, 11, 'k'), (27, 29, 'k'),
                           (11, 9, 'h'), (29, 31, 'r')):
        ewok_over_line(c, [(x0, 28), (x1 + sway, 44)], colour)
    ewok_over_line(c, [(21, 30), (21 + sway, 43)], 'r')
    ewok_sleeve_folds(c)
    ewok_hands(c, EWOK_HAND_BACK)
    # the cowl round the shoulders, under the hood's long back
    ewok_over_line(c, [(8, 18), (10, 22), (14, 24)], 'h')
    ewok_over_line(c, [(32, 18), (30, 22), (26, 24)], 'r')
    ewok_over_line(c, [(9, 16), (12, 19)], 'k')
    ewok_over_line(c, [(31, 16), (28, 19)], 'k')
    # the hood's back: lit crown, soft folds, its shadowed tip
    ewok_hood_lights(c)
    ewok_over_line(c, [(14, 7), (13, 11), (13, 16)], 'h')
    ewok_over_line(c, [(21, 8), (21, 15), (20, 19)], 'r')
    ewok_over_line(c, [(26, 7), (27, 11), (27, 16)], 'r')
    ewok_over_line(c, [(13, 19), (20, 22), (27, 19)], 'k')
    ewok_over_line(c, [(12, 18), (20, 21), (28, 18)], 'r')
    ewok_belt(c, 26)
    b = 1 if step in (1, 3) else 0
    if b:
        ewok_bob(c)
    # the hilt at the left side (the viewer's left)
    ewok_hilt(c, 12, 24 + b)
    lift = (0, 1, 0, -1)[step]
    ewok_foot(c, 9 + sway, max(0, -lift), EWOK_FOOT_BACK, 43)
    ewok_foot(c, 24 + sway, max(0, lift), EWOK_FOOT_BACK, 43)
    ewok_hem_line(c)
    return c


# -------------------------------------------------------------- the side ----
# Facing right. The face in profile under the hood's brim, x 22..31, from y 8.
EWOK_SIDE_FACE = [
    # x 22..31
    "kkkkkkkK..",   # 8  the brim's shadow
    "kkkkkkkkK.",   # 9  the forehead, deep in the hood
    "kkfmmmmmK.",   # 10 the brow, jutting
    "kfFFmOYFK.",   # 11 the eye under it, glowing
    "kfFFFFFLNK",   # 12 the blunt snout, the black nose at its tip
    "kmfFFFLLNK",   # 13
    "kmfFFLLLLK",   # 14
    "kmfFFLNNK.",   # 15 the frown
    "kkmfFLLK..",   # 16 the chin
    "kkmfffK...",   # 17
    "kkkmfK....",   # 18
]
EWOK_SIDE_TALK = [  # rows 15..16
    "kmfFFNMNK.",
    "kkmfFMNK..",
]
EWOK_SIDE_HAND = [  # the hanging hand, out of the sleeve
    "KFLLFK",
    "KFFLFK",
    "KFFFfK",
    "KfmfmK",   # the fingers
    ".KKKK.",
]


def ewok_side(step=0, talking=False):
    c = Canvas(40, 48)
    sway = (0, 1, 0, -1)[step]
    stride = (0, 2, 0, -2)[step]
    # the far foot, behind
    ewok_foot(c, 12 - stride, 0, EWOK_FOOT_FAR, 44)
    # the robe: the back flaring out to the hem, the front falling straight
    c.polygon([(12, 18), (28, 18), (29, 28), (31 + sway, 45), (7 + sway, 45), (9, 30), (10, 22)], 'R')
    # the cowl
    c.ellipse(9, 15, 29, 24, 'R')
    # the hood: tall, its crown toward the back, its brim forward over the
    # face, its back draping down to the shoulders
    c.polygon([(9, 21), (9, 12), (11, 7), (14, 3), (18, 1), (24, 1), (28, 3),
               (31, 6), (31, 8), (23, 8), (23, 19), (14, 22)], 'R')
    # the face's silhouette under the brim
    for dy, row in enumerate(EWOK_SIDE_FACE):
        for dx, ch in enumerate(row):
            if ch != '.':
                c.put(22 + dx, 8 + dy, 'F')
    # the hanging sleeve
    arm = (0, 1, 0, -1)[step]
    c.polygon([(15, 18), (21, 18), (23 + arm, 24), (23 + arm, 29), (14 + arm, 29), (13, 24)], 'R')
    c.outline()
    # the face recessed under the brim
    crispy_stamp(c, 22, 8, EWOK_SIDE_FACE)
    if talking:
        crispy_stamp(c, 22, 15, EWOK_SIDE_TALK)
    ewok_over_line(c, [(21, 9), (20, 13), (21, 18)], 'h')
    ewok_over_line(c, [(24, 3), (28, 4), (30, 7)], 'H')
    ewok_over_line(c, [(23, 7), (30, 7)], 'h')
    # the hood's crown and back lit, its lower back in shadow
    ewok_over_line(c, [(10, 10), (12, 6), (15, 3)], 'H')
    ewok_over_line(c, [(16, 2), (23, 2)], 'H')
    ewok_over_line(c, [(10, 12), (10, 17)], 'h')
    ewok_over_line(c, [(13, 8), (13, 17)], 'r')
    ewok_over_line(c, [(17, 6), (17, 14), (16, 18)], 'r')
    # the cowl's folds
    ewok_over_line(c, [(10, 18), (16, 20), (23, 20), (28, 18)], 'h')
    ewok_over_line(c, [(10, 21), (17, 23), (24, 23), (28, 21)], 'k')
    # the robe: shaded at the back, lit down the front, its folds
    for y in range(24, 46):
        for x in range(40):
            if c.get(x, y) == 'R' and x < 11 + sway + (y - 24) // 6:
                c.put(x, y, 'r')
    ewok_over_line(c, [(28, 24), (30 + sway, 43)], 'H')
    ewok_over_line(c, [(11, 31), (9 + sway, 44)], 'k')
    ewok_over_line(c, [(14, 32), (13 + sway, 44)], 'h')
    ewok_over_line(c, [(19, 33), (19 + sway, 44)], 'k')
    ewok_over_line(c, [(26, 29), (27 + sway, 44)], 'k')
    ewok_over_line(c, [(10, 23), (9, 30)], 'h')
    # the sleeve: its lit front edge, the dark opening over the wrist, the hand
    ewok_over_line(c, [(20, 19), (22 + arm, 25)], 'H')
    ewok_over_line(c, [(15, 21), (14 + arm, 26)], 'k')
    ewok_over_line(c, [(17, 22), (17 + arm, 26)], 'h')
    for x in range(15, 23):
        ewok_over(c, x + arm, 27, 'k')
    crispy_stamp(c, 15 + arm, 28, EWOK_SIDE_HAND)
    # the belt from the arm to the front
    ewok_belt(c, 26, 21, 31)
    b = 1 if step in (1, 3) else 0
    if b:
        ewok_bob(c)
    # the hilt in front of the hip
    ewok_hilt(c, 23, 24 + b)
    ewok_foot(c, 21 + stride, 0, EWOK_FOOT_SIDE, 44)
    ewok_hem_line(c)
    return c


def ewok():
    frames = []
    side = [ewok_side(s) for s in range(4)]
    for d, flip in ((RIGHT, False), (LEFT, True)):
        pick = (lambda f: f.mirrored()) if flip else (lambda f: f)
        frames.append((d, STAND, 0, pick(side[0])))
        frames += [(d, WALK, i, pick(side[i])) for i in range(4)]
        frames += [(d, TALK, 0, pick(side[0])), (d, TALK, 1, pick(ewok_side(0, True)))]
    frames.append((FRONT, STAND, 0, ewok_front()))
    frames += [(FRONT, WALK, i, ewok_front(i)) for i in range(4)]
    frames += [(FRONT, TALK, 0, ewok_front()), (FRONT, TALK, 1, ewok_front(0, True))]
    frames.append((BACK, STAND, 0, ewok_back()))
    frames += [(BACK, WALK, i, ewok_back(i)) for i in range(4)]
    return frames


# ------------------------------------------------------------- preview ----


def svc(frames, colours, costume, glow=(), shine=()):
    """The engine's character file: frames (dir, kind, index, canvas).
    Letters in `glow` are light added to what is behind them (mask 2), in
    `shine` drawn even in the dark (mask 3): a lit blade and its haze."""
    letters = list(colours)
    number = {letter: i + 1 for i, letter in enumerate(letters)}
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
                    pixels[y * w + x] = number[ch]
                    mask[y * w + x] = 2 if ch in glow else 3 if ch in shine else 1
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

# Extra, redrawn from the user's pixel-art model: a glossy black coat with
# blue-grey sheen and maroon-brown shading, two very big upright ears with
# salmon insides, big round brown eyes, white chin and chest blaze, a slim
# deep-chested body on long thin legs with white toe tips, the tail up and
# curling forward over the back.
EXTRA_COLOURS = {
    'K': (0x08, 0x06, 0x0A),  # outline
    'b': (0x12, 0x10, 0x18),  # fur, deep shadow
    'B': (0x1F, 0x1D, 0x2B),  # fur, glossy black
    'g': (0x3C, 0x3A, 0x4A),  # muzzle, dark grey
    'L': (0x3A, 0x46, 0x6C),  # fur, blue-grey sheen
    'l': (0x66, 0x7A, 0xA8),  # fur, sheen at its brightest
    'm': (0x48, 0x20, 0x2A),  # fur, maroon shading
    'r': (0x78, 0x40, 0x4C),  # fur, maroon lit
    'q': (0x7C, 0x30, 0x2C),  # ear inside, deepest
    'p': (0xB8, 0x5A, 0x4A),  # ear inside
    'P': (0xEA, 0x8A, 0x70),  # ear inside, salmon
    'W': (0xF8, 0xE4, 0xD6),  # white chin, blaze, toes
    'c': (0xB8, 0x96, 0x8C),  # white, shaded
    'E': (0x48, 0x22, 0x14),  # eye, dark brown
    'e': (0x80, 0x46, 0x26),  # eye, brown lit (lower rim)
    'D': (0x0C, 0x06, 0x06),  # pupil
    'w': (0xFF, 0xF8, 0xF0),  # glint
    'N': (0x04, 0x03, 0x06),  # nose
    'n': (0x6C, 0x6C, 0x80),  # nose, lit
    'M': (0x60, 0x14, 0x20),  # mouth, inside
    'T': (0xEC, 0x7C, 0x88),  # tongue
}


def extra_spans(c, rows, colour='B', dx=0, dy=0):
    for y, segs in rows.items():
        for x0, x1 in segs:
            for x in range(x0, x1 + 1):
                c.put(x + dx, y + dy, colour)


def extra_outline(c, letters='BbLlmrqpP'):
    edge = [(x, y) for y in range(c.height) for x in range(c.width)
            if c.cells[y][x] in letters and any(c.get(x + ex, y + ey) == ' ' for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        c.cells[y][x] = 'K'


def extra_paint(c, pixels, dx=0, dy=0, only=None):
    for (x, y), ch in pixels.items():
        if only is None or c.get(x + dx, y + dy) in only:
            c.put(x + dx, y + dy, ch)


def extra_rows(c, x, y, rows, only=None):
    """Letter rows onto `c` from (x, y); '.' leaves what is there."""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != '.' and (only is None or c.get(x + i, y + j) in only):
                c.put(x + i, y + j, ch)


# ---------------------------------------------------------------- side ----
# Facing right (the model mirrored). Head turned toward the viewer as in the
# model: the near ear on the right, standing tall; the far ear behind it on
# the left, leaning well out like the model's.
EXTRA_SIDE_HEAD = [  # x 18..39, rows 1..16
    "....................KK",  # 1  the near ear's tip
    "...................KqK",  # 2
    "..KK..............KPqK",  # 3  the far ear's tip, leaning out
    "..KPKK...........KPPqK",  # 4
    "..KPPqKK........KpPPqK",  # 5
    "...KPPPqKK.....KbpPPqK",  # 6
    "...KpPPPqbKKKKKbbpPPqK",  # 7  the skull's top between the ears
    "....KpPPqbbbBLlBBbbqbK",  # 8  the forehead's gloss
    ".....KqpqbbBBbBBBBBbLK",  # 9
    "......KqbBBBbbBBBwEBK.",  # 10 the near eye, its glint
    ".......KbbbwEBbBbEDbK.",  # 11 the far eye
    "........KKbEDbbbbeDbK.",  # 12
    "..........KbbNnNbbbLK.",  # 13 the nose, lit on top
    "...........KgNNNgbbbK.",  # 14
    "...........KbKgKKbbK..",  # 15 the mouth line
    "...........KbcWWcbK...",  # 16 the white chin
]


def extra_head_spans(rows, y0, x0):
    spans = {}
    for j, row in enumerate(rows):
        segs, start = [], None
        for i, ch in enumerate(row + '.'):
            if ch != '.' and start is None:
                start = i
            elif ch == '.' and start is not None:
                segs.append((x0 + start, x0 + i - 1))
                start = None
        spans[y0 + j] = segs
    return spans


EXTRA_SIDE_SIL = dict(extra_head_spans(EXTRA_SIDE_HEAD, 1, 18))
EXTRA_SIDE_SIL.update({
    17: [(27, 37)],
    18: [(17, 37)], 19: [(15, 37)], 20: [(14, 37)], 21: [(13, 37)], 22: [(13, 37)],
    23: [(13, 37)], 24: [(13, 20), (25, 36)], 25: [(13, 19), (26, 36)], 26: [(14, 19), (28, 34)],
    27: [(15, 18)],
})
EXTRA_SIDE_FACE = {
    # the white blaze down the chest: a tuft, then a triangle pointing down
    (33, 18): 'c', (34, 18): 'W', (34, 19): 'c',
    (32, 21): 'c', (33, 21): 'W', (34, 21): 'W', (35, 21): 'c', (32, 22): 'c', (33, 22): 'W', (34, 22): 'W',
    (33, 23): 'W', (34, 23): 'c', (33, 24): 'c',
}
EXTRA_SIDE_SHEEN = {
    # the neck
    (28, 17): 'L', (29, 17): 'L', (28, 18): 'L',
    # the back, the rump
    (18, 19): 'L', (19, 19): 'L', (20, 19): 'l', (21, 19): 'L', (22, 19): 'L', (23, 19): 'L', (24, 19): 'L',
    (25, 19): 'L', (16, 19): 'L', (15, 20): 'l', (14, 21): 'L', (14, 22): 'L', (14, 23): 'L',
    # the shoulder and the chest's side, maroon down its front
    (29, 20): 'L', (30, 21): 'L', (36, 19): 'm', (36, 20): 'm', (36, 21): 'r', (36, 22): 'r', (36, 23): 'm', (35, 24): 'm',
    (35, 25): 'm',
}
# the tail: up from the rump, leaning back, its tip hooked forward
EXTRA_SIDE_TAIL = ["..KKK.",
             ".KLlBK",
             "KBlKKK",
             "KBLK..",
             "KBLK..",
             "KBmK..",
             ".KBmK.",
             ".KKBmK"]


def extra_belly(c, x0, x1, b):
    """One clean maroon band along the belly's underline: the lowest fur
    pixel above the bottom outline, from the thigh to the chest."""
    for x in range(x0, x1 + 1):
        for y in range(27 + b, 15, -1):
            if c.get(x, y) == 'K' and c.get(x, y - 1) == 'B':
                c.put(x, y - 1, 'm')
                break


def extra_leg(c, cols, fill):
    """A thin leg: rows y -> left x; K fill K; the paw (its last two rows) a
    pixel longer forward, white toe tips under it."""
    last = max(cols)
    for y, x in sorted(cols.items()):
        if y == last:
            extra_rows(c, x, y, ["KWKWK"])
        elif y == last - 1:
            extra_rows(c, x, y, ["K" + fill[0] + fill[0] + fill[1] + "K"])
        else:
            extra_rows(c, x, y, ["K" + fill + "K"])


def extra_path(points):
    """Left columns, row by row, straight between (row, x) points."""
    cols = {}
    for (y0, x0), (y1, x1) in zip(points, points[1:]):
        for y in range(y0, y1 + 1):
            cols[y] = round(x0 + (x1 - x0) * (y - y0) / max(1, y1 - y0))
    return cols


# talking: the mouth opens under the nose, the pink tongue on the lower jaw,
# the white chin pushed a little down
EXTRA_SIDE_TALK = {(31, 15): 'K', (32, 15): 'M', (33, 15): 'M', (34, 15): 'M', (35, 15): 'K',
             (31, 16): 'K', (32, 16): 'T', (33, 16): 'M', (34, 16): 'K',
             (31, 17): 'c', (32, 17): 'W'}


def extra_side(step=0, talking=False):
    """Facing right: 48 x 40, feet on row 38. `step` 0..3 walks: on 1 the
    hind legs spread while the fore legs pass, on 3 the other way round
    (the body a row lower on both); on 2 the swinging pair is lifted."""
    c = Canvas(48, 40)
    b = 1 if step in (1, 3) else 0
    s = (0, -2, 0, 2)[step]          # near hind and far fore: s; the others: -s
    up = 1 if step == 2 else 0       # near hind and far fore swing through on 2
    far_hind = extra_path([(24 + b, 20), (31, 20 - s), (37, 19 - s)])
    far_fore = extra_path([(25 + b, 32), (37 - up, 32 + s)])
    near_hind = extra_path([(25 + b, 15), (29 + b, 16 + min(0, s)), (33 - up, 13 + s), (38 - up, 13 + s)])
    near_fore = extra_path([(26 + b, 27), (38, 27 - s)])
    extra_leg(c, far_hind, 'bm')
    extra_leg(c, far_fore, 'bm')
    extra_spans(c, EXTRA_SIDE_SIL, 'B', 0, b)
    extra_outline(c)
    extra_belly(c, 20, 33, b)
    extra_rows(c, 11, 12 + b, EXTRA_SIDE_TAIL)
    extra_rows(c, 18, 1 + b, EXTRA_SIDE_HEAD)
    extra_paint(c, EXTRA_SIDE_SHEEN, 0, b, only='B')
    extra_paint(c, EXTRA_SIDE_FACE, 0, b)
    extra_leg(c, {y: x for y, x in near_hind.items() if y >= 27 + b}, 'Lm')
    extra_leg(c, {y: x for y, x in near_fore.items() if y >= 27 + b}, 'Bm')
    if talking:
        extra_paint(c, EXTRA_SIDE_TALK, 0, b)
    return c


# --------------------------------------------------------------- front ----
def extra_mirror(half):
    """Rows of the left half (x 0..16), mirrored about the 16|17 seam."""
    return [h + h[::-1] for h in half]


EXTRA_FRONT_HALF = [  # x 0..16, rows 1..28
    "......KK.........",  # 1  the ears' tips: big, upright, salmon inside
    "......KqK........",  # 2
    "......KqPK.......",  # 3
    "......KqPPK......",  # 4
    "......KqPPpK.....",  # 5
    "......KqPPPpK....",  # 6
    "......KbqPPpbKKKK",  # 7  the skull's top between the ears
    ".......KbqPpbBBLl",  # 8  the forehead's gloss
    "........KbqbBBBBB",  # 9
    "........KBbBBBbBb",  # 10 the eyes (painted)
    "........KbBbBBbbB",  # 11
    ".........KBBbbbbg",  # 12 the muzzle's bridge
    "..........KBbbgNN",  # 13 the nose
    "...........KbbgNN",  # 14
    "............KbKgK",  # 15 the mouth line
    ".............KbcW",  # 16 the white chin
    "............KBbbb",  # 17 the throat
    "............KBBbb",  # 18 the chest, deep
    "...........KLBBBb",  # 19 the shoulders
    "...........KLBBBB",  # 20
    "...........KBBBBB",  # 21
    "............KBBBB",  # 22 narrowing to the elbows
    "............KmBBB",  # 23
    "............KmBBB",  # 24
    "............KmBbB",  # 25
    "............KmBKB",  # 26 the elbows, the brisket between them
    "............KLmKb",  # 27
    "............KLmKK",  # 28 the brisket's bottom
]
EXTRA_FRONT_FACE = {
    # the eyes, the glint on the same side in both, a lit lower rim
    (12, 10): 'w', (13, 10): 'E', (12, 11): 'E', (13, 11): 'D', (12, 12): 'e', (13, 12): 'D',
    (20, 10): 'w', (21, 10): 'E', (20, 11): 'E', (21, 11): 'D', (20, 12): 'e', (21, 12): 'D',
    (16, 13): 'n', (17, 13): 'N',
    # the white blaze: a tuft, then a long triangle
    (16, 19): 'c', (17, 19): 'W', (17, 20): 'c', (15, 22): 'c', (16, 22): 'W', (17, 22): 'W', (18, 22): 'c',
    (16, 23): 'W', (17, 23): 'W', (16, 24): 'W', (17, 24): 'c', (16, 25): 'c',
}
EXTRA_FRONT_TALK = {  # the mouth open under the nose, a pink tongue, the chin dropped a row
    (15, 15): 'K', (16, 15): 'M', (17, 15): 'M', (18, 15): 'K', (15, 16): 'K', (16, 16): 'T', (17, 16): 'M', (18, 16): 'K',
    (15, 17): 'c', (16, 17): 'W', (17, 17): 'W', (18, 17): 'c'}


def extra_front_legs(c, step, b, toes=True, fill=('Lm', 'mL')):
    lift = (0, 2, 0, 2)[step]
    for i, (x, f) in enumerate(((12, fill[0]), (18, fill[1]))):
        up = lift if (i == 0) == (step == 1) else 0
        cols = {y: x for y in range(26 + b, 39 - up)}
        last = 38 - up
        for y in sorted(cols):
            if y == last:
                extra_rows(c, x - (1 if i == 0 else 0), y, ["KWKWK" if toes else "KKKKK"])
            elif y == last - 1:
                extra_rows(c, x - (1 if i == 0 else 0), y, [("KBB" + f[1] + "K") if i == 0 else ("K" + f[0] + "BBK")])
            else:
                extra_rows(c, x, y, ["K" + f + "K"])


def extra_front(step=0, talking=False):
    """Facing the viewer: 34 x 40, feet on row 38; walking lifts a paw and
    bobs a row on steps 1 and 3."""
    c = Canvas(34, 40)
    b = 1 if step in (1, 3) else 0
    extra_front_legs(c, step, b)
    extra_rows(c, 0, 1 + b, extra_mirror(EXTRA_FRONT_HALF))
    extra_paint(c, EXTRA_FRONT_FACE, 0, b)
    if talking:
        extra_paint(c, EXTRA_FRONT_TALK, 0, b)
    return c


# ---------------------------------------------------------------- back ----
EXTRA_BACK_HALF = [  # x 0..16, rows 1..28: the ears' backs, the head, the back
    "......KK.........",  # 1
    "......KLK........",  # 2
    "......KLBK.......",  # 3
    "......KLBbK......",  # 4
    "......KLBBbK.....",  # 5
    "......KLBBbbK....",  # 6
    "......KBLBBbbKKKK",  # 7
    ".......KBLBbBBLLl",  # 8
    "........KBBbBBBBB",  # 9
    "........KLBBBBBBL",  # 10
    "........KLBBBBBBB",  # 11
    ".........KLBBBBBB",  # 12
    "..........KBBBBBb",  # 13
    "...........KBBBbb",  # 14 the nape
    "...........KLBBbb",  # 15
    "..........KLLBBbb",  # 16 the shoulders
    "..........KLBBBBb",  # 17
    "..........KBLBBBB",  # 18 the back
    "..........KLBBBBB",  # 19
    ".........KLLBBBBB",  # 20 the haunches
    ".........KLBBBBBB",  # 21
    ".........KLBBBBBB",  # 22
    ".........KLBBBBBB",  # 23
    ".........KBLBBBBb",  # 24 the haunches part
    "..........KBBBBBb",  # 25
    "..........KmBBBbK",  # 26
    "...........KmBbK.",  # 27
    "............KmbK.",  # 28
]
# the tail from behind: up from the top of the rump, over the back, its
# tip curling over to his right past the nape (blue-lit on its outer edge)
EXTRA_BACK_TAIL = [  # x 15..27, rows 11..22
    ".......KKK...",  # 11
    "......KlLBK..",  # 12
    ".....KLKKLBK.",  # 13
    "....KLK..KlK.",  # 14
    "...KLBK...KK.",  # 15
    "..KLBK.......",  # 16
    "..KLBK.......",  # 17
    ".KLBK........",  # 18
    ".KLBK........",  # 19
    ".KlBK........",  # 20
    ".KBBK........",  # 21
    ".KbBK........",  # 22
]


def extra_back(step=0):
    """Facing away: 34 x 40, feet on row 38."""
    c = Canvas(34, 40)
    b = 1 if step in (1, 3) else 0
    extra_front_legs(c, step, b, toes=False, fill=('Lb', 'bL'))
    extra_rows(c, 0, 1 + b, extra_mirror(EXTRA_BACK_HALF))
    extra_rows(c, 15, 11 + b, EXTRA_BACK_TAIL)
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


# --------------------------------------------------------------- Suzy 2 ----

# Suzy 2: drawn as close as the size allows to the user's picture: very long
# dark hair with grey streaks falling mostly over her left shoulder, a broad
# smile, a green T-shirt with a white oval and a dark green bat, slim faded blue
# jeans flared a little at the ankle, light grey sneakers with white soles, a
# black smartwatch on her left wrist.  Every pixel is in the tables below (the
# picture itself is not read).

SUZY2_W, SUZY2_H = 32, 56
SUZY2_TOP = 4  # the top of her hair; the soles' outline on row 55

SUZY2_COLOURS = {
    'K': (0x22, 0x18, 0x1A),  # outline
    'h': (0x30, 0x22, 0x20),  # hair, dark brown-black
    'd': (0x52, 0x40, 0x3A),  # hair, its sheen
    'H': (0x84, 0x78, 0x74),  # hair, grey streaks
    'L': (0xB8, 0xB2, 0xAE),  # hair, silver streaks
    'S': (0xEC, 0x9A, 0x62),  # skin, warm tan
    's': (0xB8, 0x68, 0x3E),  # skin, shaded
    'l': (0xF8, 0xB8, 0x84),  # skin, lit
    'c': (0xD8, 0x6E, 0x4E),  # cheeks
    'r': (0xC0, 0x4C, 0x40),  # lip
    'M': (0x6E, 0x1E, 0x22),  # mouth, open
    'W': (0xF8, 0xF2, 0xE2),  # teeth, the emblem, soles
    'G': (0x4A, 0xA2, 0x56),  # shirt, green
    'q': (0x72, 0xC6, 0x6E),  # shirt, lit
    'g': (0x2E, 0x70, 0x3A),  # shirt, shaded
    'b': (0x0C, 0x4E, 0x16),  # the bat
    'J': (0x4C, 0x68, 0x9E),  # jeans
    'i': (0x7E, 0x94, 0xC0),  # jeans, faded
    'j': (0x2C, 0x40, 0x72),  # jeans, dark
    'n': (0xC8, 0xC4, 0xCE),  # sneakers, light grey
    'm': (0x8E, 0x88, 0x98),  # sneakers, shaded, laces
    'T': (0x0E, 0x0C, 0x10),  # watch strap
    'u': (0x5E, 0x62, 0x6E),  # watch face
}


def suzy2_blank():
    return Canvas(SUZY2_W, SUZY2_H)


def suzy2_rows_at(c, table, dy=0, dx=0):
    """{row: (x0, letters)}; '.' leaves what is there."""
    for y, (x0, s) in table.items():
        crispy_stamp(c, x0 + dx, y + dy, [s])


def suzy2_shift_region(c, x0, x1, y0, y1, dy):
    """Columns x0..x1, rows y0..y1, moved dy rows (what they leave is empty)."""
    cols = {x: [c.get(x, y) for y in range(y0, y1 + 1)] for x in range(x0, x1 + 1)}
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            c.cells[y][x] = ' '
    for x in range(x0, x1 + 1):
        for i, ch in enumerate(cols[x]):
            if ch != ' ':
                c.put(x, y0 + i + dy, ch)


def suzy2_final_outline(c):
    """Any drawn pixel left at the silhouette's edge becomes the outline."""
    c.outline('K')


# ---------------------------------------------------------------- front --

SUZY2_FRONT_UPPER = {  # rows 4..37: head, shirt, arms, hips ('h' hair is streaked after)
    4:  (13, 'KKKKKK'),
    5:  (11, 'KKhhhhhhhKK'),
    6:  (10, 'KhhhhhhhhhhK'),
    7:  (10, 'KhhhSSSShhhhK'),
    8:  (10, 'KhhSSSSSShhhK'),
    9:  (10, 'KhSKKSSKKShhK'),
    10: (10, 'KhScSSsScShhK'),
    11: (10, 'KhSKWWWWKShhhK'),
    12: (10, 'KhhsSrrSSSshhK'),
    13: (10, 'KhhKsSSSSsKhhhK'),
    14: (10, 'KhhhKssKhhhhhhK'),
    15: (8, 'KGGhdgSSSSghhhhhK'),
    16: (7, 'KqqGhGGggggGhhhhhGK'),
    17: (7, 'KqGgGWWWWWWGhhhhhGK'),
    18: (7, 'KqGgWbWbbWbWhhhhhGK'),
    19: (7, 'KqGgWbbbbbbWhhhhhgKK'),
    20: (7, 'KgggGWWbbWWGhhhhhgKhK'),
    21: (7, 'KSsKqGGGGGGGhhhhsSKhK'),
    22: (7, 'KSsKqGGGGGGGhhhhsSKhhK'),
    23: (7, 'KSsKGGGGGGGghhhhsSKhhK'),
    24: (7, 'KSsKGGGGGGGghhhhsSKhhK'),
    25: (7, 'KSsKGGGGGGGghhhhsSKhhK'),
    26: (7, 'KSsKGGGGGGgghhhhsSKhhK'),
    27: (7, 'KSsKGGGGGGGghhhhsSKhhK'),
    28: (7, 'KSsKgGGGGGGghhhhsSKhK'),
    29: (7, 'KSsKggggggghhghKsSKhK'),
    30: (7, 'KSsKjJJJJiJJhJhKsSKhK'),
    31: (7, 'KSsKJjJJJjJJjJKTuTKK'),
    32: (6, 'KSSsKJJjJJjJjJJKsSSK'),
    33: (6, 'KSSsKJJiiJjJiiJKSSsK'),
    34: (6, 'KSSsKJJiiJjJiiJKSSsK'),
    35: (6, 'KsSsKjJiiJjJiiJKsSsK'),
    36: (6, 'KKKKKjjiiJjJiijKKKKK'),
    37: (11, 'KjiiJjJiijK'),
}

# Her hair's strands: (x, first row, last row, letter) over the 'h' hair.
SUZY2_FRONT_STRANDS = [
    # the crown, parted near the middle; grey at her right temple
    (14, 5, 5, 'd'), (16, 5, 6, 'd'), (18, 5, 6, 'd'), (12, 5, 5, 'H'), (13, 5, 5, 'L'),
    (11, 8, 12, 'H'), (12, 6, 6, 'L'), (13, 6, 6, 'H'), (11, 6, 7, 'd'),
    (19, 6, 7, 'd'), (20, 9, 12, 'd'), (21, 7, 8, 'H'),
    # the left side's strands to her shoulder
    (11, 14, 14, 'H'), (12, 14, 15, 'd'),
    # the long fall over her left shoulder
    (20, 13, 15, 'H'), (20, 16, 17, 'L'), (22, 15, 18, 'd'), (21, 18, 21, 'd'),
    (19, 19, 22, 'd'), (20, 22, 24, 'H'), (21, 25, 28, 'd'), (19, 26, 27, 'H'),
    (22, 13, 14, 'L'), (22, 20, 23, 'L'), (21, 14, 15, 'd'), (20, 27, 28, 'H'),
    # the strands hanging outside her left arm
    (26, 21, 22, 'H'), (27, 22, 25, 'd'), (26, 25, 25, 'H'), (27, 27, 27, 'H'),
    (26, 29, 29, 'H'),
]


def suzy2_strands(c, spec, dy=0, dx=0, flip=False):
    for x, y0, y1, ch in spec:
        if flip:
            x = SUZY2_W - 1 - x
        for y in range(y0, y1 + 1):
            if c.get(x + dx, y + dy) in 'hdHL':
                c.put(x + dx, y + dy, ch)


# Her legs from the crotch (row 38) to the hem (row 51): the viewer's left leg
# (x0, letters); the other is its mirror round column 16 (her axis), sharing
# the seam's outline down to row 41, then parted.
SUZY2_MID = 16
SUZY2_LEG_LEFT = [
    (11, 'KjiiJK'),   # 38 the crotch: one seam between the thighs
    (11, 'KjiiJK'),
    (11, 'KjiiJK'),
    (11, 'KjiiJK'),
    (11, 'KjiJK'),    # 42 parted above the knee
    (11, 'KjiJK'),
    (11, 'KjiJK'),
    (11, 'KjJJK'),    # 45 shins, darker
    (11, 'KjJJK'),
    (11, 'KjJJK'),
    (11, 'KjJJK'),
    (11, 'KjJJK'),
    (10, 'KjJJJK'),   # 50 flare
    (10, 'KjjjjK'),   # 51 hem
]
SUZY2_SHOE_LEFT = [
    (9, 'KnmnmnK'),   # laces
    (8, 'KnnnnnnK'),
    (8, 'KWWWWWWK'),
    (8, 'KKKKKKKK'),
]
SUZY2_KNEE = 5  # the row taken out first when a leg bends


def suzy2_mirror_x(x0, s, axis=SUZY2_MID):
    return (2 * axis - (x0 + len(s) - 1), s[::-1])


def suzy2_front_legs(c, lift_left, lift_right, b, leg=None, shoe=None):
    leg, shoe = leg or SUZY2_LEG_LEFT, shoe or SUZY2_SHOE_LEFT
    for lift, flip in ((lift_left, False), (lift_right, True)):
        legs = list(leg)
        drop = b + lift
        # Bending: rows taken out round the knee.
        for _ in range(drop):
            del legs[SUZY2_KNEE]
        y = 38 + b
        for x0, s in legs:
            if flip:
                x0, s = suzy2_mirror_x(x0, s)
            crispy_stamp(c, x0, y, [s])
            y += 1
        for x0, s in shoe:
            if flip:
                x0, s = suzy2_mirror_x(x0, s)
            crispy_stamp(c, x0, y, [s])
            y += 1


SUZY2_FRONT_TALK = {12: (10, 'KhhsMMMMSSshhK'), 13: (10, 'KhhKsrrSSsKhhhK')}


def suzy2_front(step=0, talking=False):
    c = suzy2_blank()
    b = 1 if step in (1, 3) else 0
    lift = (0, 2, 0, 2)[step]
    suzy2_front_legs(c, lift if step == 1 else 0, lift if step == 3 else 0, b)
    up = dict(SUZY2_FRONT_UPPER)
    if talking:
        up.update(SUZY2_FRONT_TALK)
    suzy2_rows_at(c, up, dy=b)
    suzy2_strands(c, SUZY2_FRONT_STRANDS, dy=b)
    # Arms swing a little: the arm forward (with the other leg) a row shorter.
    if step == 1:
        suzy2_shift_region(c, 22, 31, 27 + b, 37 + b, -1)
    elif step == 3:
        suzy2_shift_region(c, 0, 9, 27 + b, 37 + b, -1)
    suzy2_final_outline(c)
    return c


# ----------------------------------------------------------------- side --

def suzy2_layer():
    return Canvas(SUZY2_W, SUZY2_H)


def suzy2_lay(dst, src, outline=True):
    """A part drawn on its own, outlined round, laid over what is there."""
    if outline:
        src.outline('K')
    for y in range(SUZY2_H):
        for x in range(SUZY2_W):
            if src.cells[y][x] != ' ':
                dst.cells[y][x] = src.cells[y][x]


def suzy2_spans(c, table, dy=0, dx=0):
    """{row: (x0, x1, letter)} filled."""
    for y, (x0, x1, ch) in table.items():
        for x in range(x0, x1 + 1):
            c.put(x + dx, y + dy, ch)


SUZY2_SIDE_HEAD = {  # facing right
    4:  (12, 'KKKKK'),
    5:  (10, 'KKhhhhhKK'),
    6:  (9, 'KhhhhhhhhhK'),
    7:  (9, 'KhhhhhhhhhSK'),
    8:  (9, 'KhhhhhhhhSSSK'),
    9:  (9, 'KhhhhhhhSSKSK'),
    10: (9, 'KhhhhhhhScSSSK'),
    11: (9, 'KhhhhhhhSSKWK'),
    12: (9, 'KhhhhhhhSSSrK'),
    13: (9, 'KhhhhhhSSSSK'),
    14: (9, 'KhhhhhsssKK'),
}
SUZY2_SIDE_TALK = {12: (9, 'KhhhhhhhSSSMK'), 13: (9, 'KhhhhhhSSSrK')}
SUZY2_SIDE_HEAD_STRANDS = [(12, 5, 5, 'H'), (13, 5, 5, 'L'), (15, 5, 6, 'd'), (11, 6, 7, 'H'), (12, 6, 6, 'L'),
                     (17, 6, 7, 'd'), (14, 7, 9, 'd'), (16, 8, 12, 'H'), (12, 8, 13, 'd'), (10, 9, 13, 'd')]

SUZY2_SIDE_TORSO = {  # facing right, rows 15..38 (x0, letters)
    15: (13, 'KGGssGK'),
    16: (11, 'KggGGGGGGK'),
    17: (11, 'KggGGGGGqqK'),
    18: (11, 'KggGGGGGGqK'),
    19: (11, 'KggGGGGGGWK'),
    20: (11, 'KggGGGGGGWK'),
    21: (11, 'KggGGGGGGGK'),
    22: (11, 'KggGGGGGGK'),
    23: (11, 'KggGGGGGGK'),
    24: (11, 'KggGGGGGGK'),
    25: (11, 'KggGGGGGGK'),
    26: (11, 'KggGGGGGGK'),
    27: (11, 'KggGGGGGGK'),
    28: (11, 'KggGGGGGGK'),
    29: (11, 'KggggggggK'),
    30: (11, 'KjjJJJJJJK'),
    31: (10, 'KjjJJJJJJJK'),
    32: (10, 'KjjJJJJJjJK'),
    33: (10, 'KjjJJJJjJJK'),
    34: (10, 'KjjJJJJJJJK'),
    35: (10, 'KjjJJJJJJJK'),
    36: (10, 'KjjJJJJJJJK'),
    37: (11, 'KjJJJJJJJK'),
    38: (11, 'KjJJJJJJK'),
}

# The long hair down her back (rows 15..33): (x0, letters), swaying `sway`
# columns from row 26 down.
SUZY2_SIDE_HAIR = {
    15: (9, 'KhHdh'), 16: (9, 'KhHdh'), 17: (9, 'KhHdh'), 18: (9, 'KhHhd'), 19: (9, 'KhLhd'),
    20: (9, 'KhLhh'), 21: (9, 'KdLhh'), 22: (9, 'KdHhh'), 23: (9, 'KdhHh'), 24: (9, 'KhhHh'),
    25: (9, 'KhhHd'), 26: (9, 'KhdHK'), 27: (9, 'KhdhK'), 28: (9, 'KhdLK'), 29: (9, 'KhdLK'),
    30: (9, 'KhhLK'), 31: (9, 'KdhK'), 32: (9, 'KhK'), 33: (10, 'K'),
}

# Walk cycle (facing right): near foot x, far foot x, near up, far up,
# near knee x, far knee x, the near hand's swing (columns forward).
SUZY2_SIDE_POSES = {
    0: (16, 14, 0, 0, 16, 14, 0),
    1: (21, 10, 0, 1, 18, 12, -4),
    2: (15, 16, 0, 2, 15, 18, 0),
    3: (10, 21, 1, 0, 12, 18, 4),
}

SUZY2_SIDE_SHOE = [  # facing right, the ankle at the 4th letter
    '.KnnmK..',
    'KnnnnmnK',
    'KWWWWWWK',
    'KKKKKKKK',
]


def suzy2_side_leg(c, fx, kx, up, b, near):
    """Hip to knee to ankle in slim jeans (faded in front), the sneaker."""
    leg = suzy2_layer()
    hip, knee, ankle = 37 + b, 46, 51 - up
    for y in range(hip, ankle + 1):
        if y <= knee:
            t = (y - hip) / (knee - hip)
            cx = 15.5 + (kx - 15.5) * t
            half = 3.5 - 1.0 * t
        else:
            t = (y - knee) / max(1, ankle - knee)
            cx = kx + (fx - kx) * t
            half = 2.5 + 0.5 * t * t
        x0, x1 = int(round(cx - half)), int(round(cx + half)) - 1
        for x in range(x0, x1 + 1):
            leg.put(x, y, 'J' if near else 'j')
        if near:
            leg.put(x1, y, 'i' if hip + 1 <= y <= knee + 1 else 'J')
            leg.put(x1 - 1, y, 'i' if hip + 2 <= y <= knee - 2 else 'J')
            leg.put(x0, y, 'j')
    inside = [leg.cells[ankle][:]]
    leg.outline('K')
    for x in range(1, SUZY2_W - 1):  # the hem's row: outlined at its ends only
        if inside[0][x] != ' ' and inside[0][x - 1] != ' ' and inside[0][x + 1] != ' ':
            leg.cells[ankle][x] = 'j'
    for y in range(hip, hip + 3):  # no outline across her hips (the torso's there)
        for x in range(SUZY2_W):
            if leg.cells[y][x] == 'K' and c.get(x, y) not in ' K':
                leg.cells[y][x] = ' '
    suzy2_lay(c, leg, outline=False)
    shoe = SUZY2_SIDE_SHOE if near else [r.replace('n', 'm').replace('W', 'n') for r in SUZY2_SIDE_SHOE]
    crispy_stamp(c, fx - 3, ankle + 1, shoe)


def suzy2_side_arm(c, b, dx, near):
    """Her arm from the shoulder (the sleeve), swung dx columns at the hand."""
    sk, sk2, sh, hem = ('S', 's', 'G', 'g') if near else ('s', 's', 'g', 'g')
    sleeve = {17: (13, 'KGGGGK'), 18: (13, 'KGGGGK'), 19: (13, 'KGGGGK'), 20: (13, 'KggggK')}
    if dx > 0:
        sleeve = {17: (13, 'KGGGGK'), 18: (13, 'KGGGGK'), 19: (14, 'KGGGGK'), 20: (14, 'KggggK')}
    elif dx < 0:
        sleeve = {17: (13, 'KGGGGK'), 18: (12, 'KGGGGK'), 19: (12, 'KGGGGK'), 20: (12, 'KggggK')}
    for y in range(21, 35):
        o = int(round(dx * (y - 19) / 15))
        if y <= 30:
            crispy_stamp(c, 14 + o, y + b, ['K' + sk + sk2 + 'K'])
        elif y == 31:
            crispy_stamp(c, 14 + o, y + b, ['KTuK' if near else 'KssK'])
        else:
            crispy_stamp(c, 14 + o, y + b, ['K' + sk + sk + sk2 + 'K'] if y < 34 else ['KsSsK'])
    o = int(round(dx * 16 / 15))
    crispy_stamp(c, 15 + o, 35 + b, ['KKK'])
    for y, (x0, s) in sleeve.items():
        s = s.replace('G', sh).replace('g', hem)
        crispy_stamp(c, x0, y + b, [s])


def suzy2_side(step=0, talking=False):
    c = suzy2_blank()
    b = 1 if step in (1, 3) else 0
    nfx, ffx, nup, fup, nkx, fkx, swing = SUZY2_SIDE_POSES[step]
    if swing:
        suzy2_side_arm(c, b, -swing * 3 // 2, near=False)
    suzy2_side_leg(c, ffx, fkx, fup, b, near=False)
    suzy2_rows_at(c, SUZY2_SIDE_TORSO, dy=b)
    suzy2_side_leg(c, nfx, nkx, nup, b, near=True)
    suzy2_rows_at(c, SUZY2_SIDE_HAIR, dy=b)
    head = dict(SUZY2_SIDE_HEAD)
    if talking:
        head.update(SUZY2_SIDE_TALK)
    suzy2_rows_at(c, head, dy=b)
    suzy2_strands(c, SUZY2_SIDE_HEAD_STRANDS, dy=b)
    suzy2_side_arm(c, b, swing, near=True)
    suzy2_final_outline(c)
    # A far leg hidden but for its outline: no doubled outline beside the near one.
    for y in range(38, SUZY2_H - 4):
        for x in range(1, SUZY2_W - 2):
            if (c.cells[y][x] == 'K' and c.get(x - 1, y) == ' ' and c.get(x + 1, y) == 'K'
                    and c.get(x + 2, y) not in ' K'):
                c.cells[y][x] = ' '
    return c


# ----------------------------------------------------------------- back --

SUZY2_BACK_UPPER = {  # rows 4..40: her hair over most of her back, the shirt, arms, hips
    4:  (13, 'KKKKKK'),
    5:  (11, 'KKhhhhhhhKK'),
    6:  (10, 'KhhhhhhhhhhK'),
    7:  (9, 'KhhhhhhhhhhhK'),
    8:  (9, 'KhhhhhhhhhhhK'),
    9:  (9, 'KhhhhhhhhhhhK'),
    10: (9, 'KhhhhhhhhhhhK'),
    11: (8, 'KhhhhhhhhhhhhK'),
    12: (8, 'KhhhhhhhhhhhhK'),
    13: (8, 'KhhhhhhhhhhhhhK'),
    14: (8, 'KhhhhhhhhhhhhKK'),
    15: (8, 'KhhhhhhhhhhhhGGK'),
    16: (7, 'KGGhhhhhhhhhhhGGGK'),
    17: (7, 'KGgGhhhhhhhhhhgGGK'),
    18: (7, 'KGgGhhhhhhhhhhgGGK'),
    19: (7, 'KGgGhhhhhhhhhhgGGK'),
    20: (7, 'KgggGhhhhhhhhGgggK'),
    21: (7, 'KsSKhhhhhhhhhhKSsK'),
    22: (7, 'KsSKGhhhhhhhhhKSsK'),
    23: (7, 'KsSKGhhhhhhhhGKSsK'),
    24: (7, 'KsSKGhhhhhhhhGKSsK'),
    25: (7, 'KsSKGhhhhhhhhGKSsK'),
    26: (7, 'KsSKGhhhhhhhhGKSsK'),
    27: (7, 'KsSKGhhhhhhhhGKSsK'),
    28: (7, 'KsSKgGhhhhhhhgKSsK'),
    29: (7, 'KsSKgghhhhhhggKSsK'),
    30: (7, 'KsSKjjhhhhhhjjKSsK'),
    31: (7, 'KTuKjJhhhhhhJjKSsK'),
    32: (6, 'KsSSKJJhJhhJhJJKSSsK'),
    33: (6, 'KsSSKJJjjJjJjjJKsSSK'),
    34: (6, 'KsSSKJJjjJjJjjJKsSSK'),
    35: (6, 'KsSsKJJJJJjJJJJKsSsK'),
    36: (6, 'KKKKKjJJJJjJJJjKKKKK'),
    37: (11, 'KjJJJjJJJjK'),
}
SUZY2_BACK_STRANDS = [
    (12, 5, 6, 'H'), (13, 5, 5, 'L'), (15, 5, 9, 'd'), (11, 8, 11, 'H'), (14, 9, 14, 'd'),
    (10, 10, 16, 'd'), (19, 8, 11, 'H'), (17, 7, 13, 'd'), (13, 13, 19, 'H'), (16, 15, 20, 'd'),
    (12, 18, 24, 'd'), (18, 18, 23, 'H'), (15, 21, 26, 'L'), (17, 25, 29, 'd'), (14, 27, 30, 'H'),
    (19, 12, 17, 'd'), (9, 16, 18, 'd'),
]
SUZY2_BACK_LEG = [
    (11, 'KjJJJK'),   # 38 the seat's seam
    (11, 'KjJJJK'),
    (11, 'KjJJJK'),
    (11, 'KjJJJK'),
    (11, 'KjJJK'),    # 42 parted
    (11, 'KjjjK'),    # 43 the knee's crease
    (11, 'KjJJK'),
    (11, 'KjJJK'),    # 45
    (11, 'KjJJK'),
    (11, 'KjJJK'),
    (11, 'KjJJK'),
    (11, 'KjJJK'),
    (10, 'KjJJJK'),   # 50
    (10, 'KjjjjK'),   # 51
]
SUZY2_BACK_SHOE = [
    (9, 'KnmmmnK'),   # the heel tab
    (8, 'KnnnnnnK'),
    (8, 'KWWWWWWK'),
    (8, 'KKKKKKKK'),
]


def suzy2_back(step=0):
    c = suzy2_blank()
    b = 1 if step in (1, 3) else 0
    # (from behind her right foot is on the viewer's right)
    suzy2_front_legs(c, 2 if step == 3 else 0, 2 if step == 1 else 0, b, SUZY2_BACK_LEG, SUZY2_BACK_SHOE)
    suzy2_rows_at(c, SUZY2_BACK_UPPER, dy=b)
    suzy2_strands(c, SUZY2_BACK_STRANDS, dy=b)
    if step == 1:
        suzy2_shift_region(c, 0, 9, 27 + b, 37 + b, -1)
    elif step == 3:
        suzy2_shift_region(c, 22, 31, 27 + b, 37 + b, -1)
    suzy2_final_outline(c)
    return c


def suzy2():
    frames = []
    side = [suzy2_side(s) for s in range(4)]
    for d, flip in ((RIGHT, False), (LEFT, True)):
        pick = (lambda f: f.mirrored()) if flip else (lambda f: f)
        frames.append((d, STAND, 0, pick(side[0])))
        frames += [(d, WALK, i, pick(side[i])) for i in range(4)]
        frames += [(d, TALK, 0, pick(side[0])), (d, TALK, 1, pick(suzy2_side(0, True)))]
    frames.append((FRONT, STAND, 0, suzy2_front()))
    frames += [(FRONT, WALK, i, suzy2_front(i)) for i in range(4)]
    frames += [(FRONT, TALK, 0, suzy2_front()), (FRONT, TALK, 1, suzy2_front(0, True))]
    frames.append((BACK, STAND, 0, suzy2_back()))
    frames += [(BACK, WALK, i, suzy2_back(i)) for i in range(4)]
    return frames


# ------------------------------------------------------------- Crispy 2 ----

# Crispy 2: the user's dog Crispy as a devil (red hood with two horns, red
# cape tied with black ties, a red flap at his chest), drawn in the SCUMM v8
# manner (Curse of Monkey Island): high resolution, many colours, smooth
# shading, a clean dark outline; by an artist panel from the user's picture
# (the side sampled from it, the front's face from it, the back painted to
# match), the picture itself not kept or read here.
#
# Side 104 x 96 (facing right, three-quarter), front and back 72 x 96; the
# feet's lowest row is 94 (row 95 empty), the horn tips' outline on row 1.
# Every frame is baked here as palette indices (zlib + base64, 0 =
# transparent) and decoded when drawn.

CRISPY2_KEYS = [chr(0x100 + i) for i in range(240)]
CRISPY2_RGB = [(246, 211, 163), (241, 201, 152), (241, 198, 147), (238, 198, 149), (240, 194, 142), (237, 194, 143), (236, 193, 143), (234, 193, 142), (237, 190, 138), (234, 190, 139), (235, 186, 132), (229, 186, 135), (228, 181, 129), (226, 180, 128), (228, 177, 122), (226, 176, 122), (226, 173, 118), (223, 174, 123), (224, 170, 114), (224, 168, 110), (220, 168, 114), (222, 165, 108), (220, 164, 108), (218, 172, 122), (211, 172, 126), (218, 167, 112), (211, 167, 119), (218, 165, 109), (218, 163, 106), (212, 164, 114), (220, 161, 104), (216, 161, 106), (216, 159, 102), (216, 156, 101), (210, 159, 107), (204, 159, 113), (207, 156, 103), (211, 153, 98), (208, 152, 98), (204, 152, 100), (205, 150, 96), (206, 147, 94), (203, 146, 92), (201, 145, 92), (197, 153, 108), (198, 145, 94), (192, 149, 105), (183, 148, 112), (197, 142, 90), (197, 140, 87), (188, 141, 96), (196, 138, 84), (191, 138, 87), (193, 135, 82), (188, 137, 88), (187, 134, 85), (176, 136, 98), (194, 131, 80), (189, 131, 79), (184, 132, 83), (184, 127, 76), (179, 130, 84), (178, 127, 80), (177, 122, 74), (171, 127, 85), (161, 128, 95), (172, 122, 78), (162, 122, 83), (170, 119, 74), (169, 116, 70), (159, 117, 78), (172, 112, 73), (162, 111, 67), (155, 112, 73), (156, 110, 68), (206, 82, 59), (247, 57, 43), (155, 104, 63), (248, 52, 39), (244, 47, 34), (243, 41, 31), (244, 36, 28), (235, 40, 29), (233, 35, 27), (226, 39, 31), (187, 40, 33), (144, 115, 87), (146, 109, 74), (143, 106, 72), (144, 103, 65), (136, 102, 71), (147, 97, 61), (139, 98, 62), (133, 96, 63), (124, 96, 72), (136, 91, 59), (125, 90, 60), (130, 84, 56), (121, 82, 56), (115, 87, 64), (113, 82, 57), (114, 79, 55), (104, 77, 54), (105, 73, 51), (102, 69, 47), (92, 70, 54), (91, 65, 47), (96, 59, 44), (87, 58, 43), (81, 58, 45), (80, 50, 42), (70, 55, 49), (68, 49, 44), (67, 45, 36), (55, 42, 40), (55, 37, 30), (51, 36, 29), (48, 35, 34), (240, 30, 25), (233, 29, 24), (226, 31, 23), (227, 25, 21), (220, 28, 22), (218, 26, 20), (216, 23, 20), (217, 20, 18), (209, 26, 21), (210, 23, 19), (207, 21, 18), (206, 19, 17), (201, 18, 16), (204, 17, 16), (201, 17, 16), (200, 16, 16), (204, 13, 15), (190, 25, 21), (193, 18, 17), (195, 17, 16), (194, 16, 15), (194, 14, 15), (190, 14, 15), (187, 13, 14), (182, 14, 14), (194, 11, 13), (188, 11, 13), (183, 11, 14), (181, 11, 13), (191, 7, 15), (183, 7, 15), (176, 18, 17), (160, 20, 21), (168, 14, 14), (173, 12, 13), (156, 12, 14), (176, 9, 13), (176, 8, 13), (171, 8, 13), (164, 8, 13), (151, 8, 13), (175, 5, 14), (171, 5, 13), (168, 5, 13), (165, 5, 14), (162, 5, 14), (160, 6, 13), (157, 5, 14), (152, 5, 14), (145, 5, 13), (171, 3, 14), (165, 4, 14), (160, 3, 14), (155, 3, 15), (151, 3, 13), (150, 2, 15), (151, 1, 14), (146, 3, 14), (146, 1, 14), (133, 13, 19), (112, 15, 20), (128, 7, 12), (136, 5, 13), (129, 5, 14), (122, 5, 13), (110, 5, 14), (140, 3, 13), (140, 1, 14), (133, 3, 13), (129, 3, 13), (125, 3, 12), (118, 3, 12), (112, 2, 13), (105, 2, 12), (85, 17, 24), (55, 17, 18), (48, 32, 26), (50, 14, 15), (45, 31, 27), (45, 29, 22), (45, 18, 16), (46, 10, 12), (94, 6, 12), (95, 2, 12), (79, 6, 10), (79, 2, 11), (65, 4, 12), (50, 6, 12), (44, 8, 12), (40, 30, 33), (40, 27, 23), (40, 26, 21), (38, 25, 21), (37, 22, 21), (33, 23, 24), (31, 19, 21), (28, 19, 22), (19, 17, 26), (41, 11, 13), (40, 9, 12), (34, 11, 14), (34, 9, 12), (23, 13, 17), (20, 9, 11), (18, 9, 12), (14, 11, 19), (40, 8, 12), (36, 8, 12), (30, 8, 12), (30, 8, 10), (37, 3, 14), (26, 8, 10), (24, 5, 9), (11, 4, 8), (9, 1, 5), (3, 2, 9), (1, 2, 8), (1, 0, 4), (30, 9, 12), (16, 4, 6), (236, 112, 136), (196, 74, 100)]
CRISPY2_COLOURS = dict(zip(CRISPY2_KEYS, CRISPY2_RGB))

CRISPY2_DATA = {
    ('side', 0, False): (104, 96, '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'),
    ('front', 0, False): (72, 96, 'eNrN2f9XUnn+B3DRxbOIQn47HxVXnUJQJ0ByGGCHIC8KCx41rQBRQcIvoCsaWhJNdrZpdaZSdBVELUUkxfxSKo6j+XWnOuVqkl8aaiePObanRXb+hs/F6uyu20DuD5/zeR+P58099zx4vl/3/X7fe7geHv/f2yOduzN0jz6G+fq8u1POf+0eeq7PbHnu5pSWTL2bUzxetNWo7rv7rvuqmrYXrpmxm2rVn905f1apb465hB61G9Un3ec5qTa2uyzR87bJyxmX3ED3L2Vcnmx77sZpOH7KnXPqeIMbZ7nDdL3q7cC2Hn2gbb0dVtV1U8eyS8d4o6E6HZweWy++1TQ1NWnqNZr29vZWDdhxfhx/sQVOsPTqhhtG106Xtrkhver+lqWjKz0zswpsGSc7O09mOHuZmemGDsvW/ar0hmZtl5s8jY3XqzL1Mw2qS/3q6nRnOw623U61uv+SqmFGn1l1vbHRTZ6e4cZGVeaFjoamRpVaPbKwsDA33tExPgd2RtRqVWNTQ8eFTFVj43CPS8ejd7Kp8Upm5re1V1QqneW1Y8fhcLx5A/7bcby26FSqK7XfZmZeaWya7HUzx16BV+WPmln1lyOj9h0Fh83hiEpKRBywo9ixj458qZ7V/BE85ZX7Bb/cXj82oR617TyUfxGJDAwK+uSToKBAZOQX8oc7tlH1xFh9+/JH7BuvhrrNE40tP9iUnCNYf5gPHInBIOE+MH/sEY7S9kNL44S5e+gj4mzNLk7V6GwOOYf4SRgc5uUJ8/ODeXrB4GGfEDlyh01XM7U4u+WemVpYqL8wbys9/dvwwGAk9ADcCw7+HYAigwPDf3u61DZ/oX5hYWrL/bCGbzbOb8qPkg76e0GhMK9YL7DFesGgUC//g6Sj8s35xpvDbgf2YmDoRjNv085K9g2KwiKhEAgywNMzAAmBQJHYqCDfZJZ9k9d8Y2jghZvduamj+sK6TZ6MiUF7QWAo1K98wpHIcJ9foVAwiBc6BpMst61fqO5ocrNDP7pendFiWzl97MjREAgE4hka7xl44ECgZ3yoJ/gx5OiRY6dXbC0Z1dddO8s97dUnKjeVOV98FgjxiS+v4AOHwrDYsEMAv6I83gcS+NkXOcrNyhPV7a7Xxau7wxcvrf98ujAuCgJHF6/9dZ2fgMdi8Qn89b+uFaPhkKi4wtM/r1+6OHz3lWtn8mKL7U1aWaCnZ2R+xZp4bT2JHh1NT1oHuxX5kZ6egWVpb2wtFyfdOHeGtaOO0hxlEJrFsp4pUzheZjEwGEbWS4ei7IyVxUIHKXNKHaPa4TuvXO8/d/pGN3/PVGLScjDSl7JNR1HO0aioozlFjk3ZSykmJw2jZP5+c7Tvjrv9Z6hr9Iw8spKRx4KTix0ORQ4e7+2Nx+coHI5iMpyVx6iMlJ8Z7RqY+dF1nsHeeWXOwcq8Y3GUWEZxsSgNDl5vyIE0UXExI5YSdyyv8mCOcr530E0e49DgUgULWXkaHwA9zGGBBcmWlKARXrg0FotzGBqAP12JZFUsDQ65cUyDd5eUcZTnHCzc6zAjLycGJy6328p/DUhy8hiHveBYznNKnHLp7qDJpfPC3NW/lEUqUxLhMJhfNCkaKbaeE8cDxQhYDCnaDwaDE5VlpKyl/i6zywX244yxa1Eq3cjBe/t4Q+F+If4V9vLieMAuhgX7waHgQXzOhlS62GV0XWePrTHDdOXqGuc3wSFe3lC/Q0EKu9Vhq3DEw6P9oN5eIcG/4aytVk4bxtxsQH9b6ja8diiPxWHDfb3hQcnFwPo566bNAeGnBMG9fcOxcceUjteG7qW/uXZ+erykHXd8z/k8OgyBFCiB+ITyCqt1Uwzx4SsFSERY9Oec7x3j2qXHP7nZyH5aXOxbdMjT0vJoBMAzXoGiissriiAQIN4TINDy0tLkDvCERXeMx8aTpek7S8rSPFZasDeiBEKgAkWOYoQvvAThHZzGyitVLt2ZXnqy4fbutfFkeWLgjSyPCQtFFfsjfs335QM+2b4I/2JUKIyZJ3szMLH8ZMP9HWzjyZOturn86AAEkBCOChWjCsrLC1DiUFR4AoAIiM6fq9t68uQn98zy+PLrRV0oKpoQj45IAEKpZC6XTA0FEiLQ8YRoVKhu8fXy3D1394sfX88YpgsLePlUAZoQASTi8GhUQAAKjcclAhEEtICazysofD037Ppx1eNRq6Wuboz7WVIeXxyQeCiJQCXGONd7DJFKSDqUGCDmA0mfccf1+rbOFy4ZTd3Vmm8sZGwUIR5RTk3k4xLwBBSKgE/A8ROp5X6ERDSeMpNradW3uVpgoHPt6tU6jSUqKgKFW38gEMckURMTEhKpSTFiwYN13O/IMeiZGcm4a+eRHozz1bV6C95SjCdkA1KhmE1PepPIBkSAQJY/O0Jt4VFn9PqZVh0I/WKJHulv/ulqs9agabVY6ACVyj/Mzk/M3mCzd3aIQPbfi2aAluOpj3P0bW0D/bf1t8yWX1ir/9iNAw5Lo9NY5In8Q8L8JAFbvOPYsQvEgp8lxfL6ixcvft3W1qHXg4E6Lf/48MzZHq+rufzVVfCRWaMpzC1E4+OAMAxg++GM3X5YRKJxeafq06uqLoF59K06TWvb4+2NDzsWp3PNGUdWmMtF02E0OAxjI1KsdgaNQkm+lPHlydTU805HDzr6uQ86YJz6mstXauqccWT1KckIYlgUBm5bP8wAHSKJwrxVfxJ0UnVOBwyk/2Cgje3vdNcuX74Cluf27W6DhMpAEJn+mGD7QZptx24jRjPZJpP2RGpq+jfmid2BafTmD0Ab2wvDA4a+24Zu0y2TUS5io8jJn5IwyDcv1+12my2ClkAwGru06ampp8xjExN3J4eHp2aX/sPZ2J67rW1uBq+60dRjKjFoE0HnMAkDI9p3duwUGyIiAd1lNJrq0tNBZ8zc22My3Rq6t7gXAh3jrtNlugXmMWQlojjRjCgY5lOM3e5Nsj2LJqNHuhoaTNr0dNCZMPeauk29Y3sdkBkwvI/TbfxTdg2VwCSHQw9gMEfs9tgQ2w6KQWAbq9W1tedTB98F6u4xz+yB/ul0998dGtDV8akMdAzMHwM+s+w6dgSTzjTWVlWp1RkXpsbHJgZ7bpkGJsb/vUJgkXv7tNpvbg8MmHp0Og3vkojNJiD8wjEHAn9wOChR1ooKCpPZXauqUl85cb6t7d7YvamxjqGJqcU9ztxAN4/X19ev0em/5vF4klPClBBSGBZzwA90GMHnQIeeMNpQq1LVXlS1tHR2tt2bnOS1fLvXWRjgabXNp0CC53R4WiED4cfEYvz+x263M3zPWc9RkumJHQ1VVZedDth4vP5ec8teZ5RnaGlp1vaZBnp7e24btCIAHRrNJGKDaXY7nUS0Wq2ENDa3s6Eqs7ZaNTY1PX3v7lDPyMjI/N5x9YBfYTD09Q/0Dpj6DNpmLRDKIlJiYxng7CHTn1rPJaSwhSM3qk9UX1FP3AOdyaG7oPOXvddrewY82jnS09NzswtkmgEhg0nBf8oM3nHgic48dCGXC4w2/iHjuGrQbLFMjzrbwvb2nnkISo9ByTw4eKvbOSFFQgadhMIzffB/p5FIaNu5c8lciaho5A8Z6SrzvZmZ2cffjf5l+0MLFZTmJkYnzIOt9devXqvTCGi4aMqhECKRSSJTbNYzbKFUrp/XfZmu6pyenZ2fdSof3oBACQzVqdfU19VpcgfNoSySL51OYpAptE2rUEiVgwtdWZd+wTz+HYj8gvJWclLbM0ZwRQ6aARyHhEYk0ylltBSrNSVJMCOeGBzsrFFv7yKuHxU23lnb2+xtSQqZjCAzaXQ66LCpbw9vt9b86A55114q5KUKpUKRxURTKGTaNp2BK7Oyk8pWSkuVisrRlo/+yW6NC4ik+cVekpQEAoGZksxEs7lCaZmSKyoUyZ59/E9/T4VskVRWhCTK2QQmN4XLTMZxS+RCqVJYKN2Xw+U6nUhaskxUuiZZeZqbK0+hAmV5Sft1ckXZYB6aXCQWrqyuSgolNBqOLVIC+3UkUn5+gSeNWYITPPXwePg5hojCiZQpQGG2vPTZfpxCfkE+lMHkJDidswcxxFCcRFaWVMiX7yuPUCYuISAZyUzqeweHy1UquNKs/eURZhcpspAMGpP6wHngbGRsREJuaQlXKinaVx5RdoEiy5+CfudURsbGMHcd2X6cFa5QUlRCgBNDmEn/dISgI5EVffy4ViVcgUQGOlgE01meXSeCKZCUgNNqH3UGHbZEpsiCQ0P+1XHmyRWVlO2jzlQBv0QhgENj3jvId/VJkpTsg+HHs7PlCjQUSn5fH2Qsedeh7sfxeEAFJHKFJA5JZgLv6/zWAfblrAhBR5lCCft3R1EqFEpk+5iHK0Jwu5F+T4l975w9CHZFCkGuVCpe//g8qyKJorDyISWWyX1bn7NxoCNRChWFSvHqPt5hFCoLlCsplFiWULKy61Bi6UyJorK4oDJ/Xy9DXq49DYqk4Vkpuc4LXxlEwdLQyTjB6trL/b5WOYuJlVO4pZLcFWefIWGi5fG5K//F+5mzJLaMXSaVOPukFJmwIBd4+l+96Pn+4bOHz9beTc1nK+urD/4P3i79LzMkcTE='),
    ('side', 0, True): (104, 96, 'eNrNmYtb0um2x1EJBQVFRRRBIQRFvMRFUogiK2YYj2hexsYoTUpTEzVFzabMVCpLUzvVTGYK2uWo4W262UWNpPbs2TsvqIh1puO+lEbN/hPO+9Psso9iPs08z1kP4qM/eD+/71rrXe963x8M9v/ZJh9ZuPho6nfDXDgYt+TF0oM9k78X5nBMz1I3Pf1T5aHzvwvI1HjmcMzSjpusL4794XcAPbt15vDhmIdL30b7qbjoR1/OeXLmPy1zrteWRZ178uVuq+86VBy19A2b7nRWH4h79OVuq++qLY48t+RApt7O6vjIc18aoaeXLt0BnLiHFvSA60Xd018ano4ztcVFse/0TD/5YAtyOmsORxZeM30hp1ZbW3OsMPI4GPbZpOmn02fOnDl9urr69OnTTybfwGD/o9W2A05M4+/BqTkcVfho+tmtC5fqYgsLC4uKCosKY2JKLgw8M914x/liPWe0NbW1pWDUWw/qTxadqPu++EjU1q3R0Vu3xsTENTbe0mr/q6YY6PnCRHjaoG2vqyuPiYn5oaG2rrr2cHHRoQuN3d3d1y7Uq1RFhfG9vbU1RTGFPy4zg0aWLW6dvfW1tYcLC+Pu1dSeKi4uuXDBYJ6zFw8H6k/HxpXdqy6KiTltiaPT6WXrl8vr+t7O2trao0Wnb9UUxR08N/Dc/DYrPT0zK2vGbJ4x9jSWljSWFMYMvLGACWKzcSkGy3oaz2i72qvr6k703fle1T00MWPev5bNoNPpNFoQb33yW7N5oORS4UEL4VEGkZ2cCIPLOk7bCUJ0pvGni0d6ACZ7g4RHcbTHYp1o/jwmXZzy1nz8wHELcpRBLlgn5/xlM2H6594ube+Da83VPRMvdLJQAcnJEYmytlnlSCaT8CQyZ2j8YPGkBac5YbH4z8DcvNd/95df7jaVdI+9ei6ThlLIRDQSucrGBm1PQtu7YKl0RU/xcd2SGBrGCRuoXJ7T2Xmj7/a9+oPnhybSU6VcPNYJ64REYrE2CHu0tbO1syOdvW6dt7O7p89iGFYA1smJtjzmzZ86tFrt9Yb682NjWbLQtavxSMgQCJqDjY2DtYMDGgn8h+coFx9qROqCxfp7Kj+jXje0a9V1dcfHJsZkkhAMgUAk2iOtrazsaYCDtUFjEXArKytnInXRsXQsZycnhvIz6sGVhvrrFcdKBsYm0qVMP6oX2tra2cfDwRpFdcSsoqzCEhEAY2XtyXH3XIwT4uzk+Blugz1paDipij3QPfRrVoqUGRriBY1q5ePhYYUm2q9ikYOICOc1Vlb0YLs8GGYxjouz02dztsYXDM3skwmFDF9rK8yahIQ1HuE+GAKdTiCHIG3DMl5ZW/9TbgeDefz7t310AibWye8zwqNWdzao4s4Pvdq3TyJkMKyt3T12m2dmEsIDab6+XBwhhOqVu2Zixho1iFvk6zSGiOHk5Ls85wngdFbG9Rhn9kmy/fysrYl+Gf9UKHJmkjZv9vWl4YghfrsVxvyXaWnjsEXik4/zYzhjPyMPnjSptZ0njw+8+BXiIKyoQTkFaebdmeZfv9vm60vFoYgh2fKJly/T0xfnEBhBAS6Mz/Jbh7b19IR5nzxiP5MqkUgVv+7Ozn5lzt2ZyPB1t8GsImxUmM2527YNL17cGGI29uM8YLGUsLki9HS+yZh+Ns/RqNXXO6qM+n1yho4llUppkpy3aS/MEzsSxf64VRgHa2ubYPPLhKSksUU5eomE9WnCsWj57ri5/Kqvv3jx4r2+6WnAetYHAnS92pi1b8vqx5uk0g041s4cs7lgj3RtEJioNjZw8GMdiAlcooKBpSfIb4Gzdl1+fj6RjsN55k/+UF1dXQWs7s69+/dvT0+bNJrOzkbjvhQRzZAiFjKCglg7MzLSJBKqzbyhgoGkJTnKoCAxWKyokKt0ylAcgYh3c8PnT3arak6dqppD1dTU9N69a7oCODeM+5KpRINcTMWhKRKJWAy8QSZiMDY2gV9t2/Yd+O2AWzw+o8kiCQARcPn5ShaegCMQCHg8UWm6HBkZeQSCnKo6VXOqq+/uzSuarmuAI14tfZiyDmePCmBJkpO3UINYOGe4NSZ4e9KQMS8vwXZNzu7FC2mERMJl4HyJRFc3vBuRwGQyA4JHbnY2nS2Niy0tB2JO1d/p7e3o/eWqpuvmRARtXfbD9VQXJBJH3SQSeVG9vJyB09Zvy8jNgWwNBqMsWBQ0LJVIQhn+eLwbnsTn4d0IOJxyqlN7Xdv5Y3VkdHx0VHTdld6+jq6/XGtS3xzbJNv3UiJ2QNjaIZFUKoGAc4fD4TY+YTlGY064ldWaF5vhm9csChpPBxyBkI0nsdh4yAjuwwPXIevqBXap7kxdR/+dzq7+n9XqGwP7Us3ZYoaXLQYBFh9bdz+Go7Mz3DMhwfwiJ8eYl5PzosAG89hjUdDoN2DWSUP86UQCjkQSCARK07XWlpbWVvDW0qaFYD83NLX3vnqg6bjx32azXESjUQkIhK29L8PPzw8Lt4FjEtJeGEEnl/MCVFKP8ALF4p77TioR8X2JbgQ2l8hmh+hMN1pb61Sqk5UqVSUAavv6Vaq2ztt/vdnQ+TezOVnEpdNwaDtnZ9+1uUkoDzBzMMEJuQU5Q8Yh8zBYWpesLsNiERFPYjB5XFcCO4Clm26srKhQqSogU6mqevu6VBWV2t7+f9xQP5gxZ0WIWDQaDkfNVSRgwnNzrEEeIDi7M4aG8mZzwCTCLNk7jacz8QEkXz7elcBis3Vv/qQ+qYIw0AtI6u1rL1dVtvXe+/npna7+GbAAybZI13ltd8b4JCUhbKzB/LTxDE8AGTcWBsRtd1hKj34DM4DC5bq54rnsUJbOBDILYMrAC+KoTjzoAH9Wtvf29f/1xp0Hf8/KTpZt2ULFYHz2eIFkW+MBYhIWFp6Q9CIvAYN2GLTzXIKzIZTJFrHJrm5cLlfA0k1WlKtUtSdaWqrm9KhUXV2Qsqq23v6f/wIUze5NlW1yd3cPzgj0coB7eK5CwN+8s4xgDxQMFrhkr8gMELBIFD6dzhaEGnqOloNhK6EsAK4rr1B19JapKttVpzr6+v72j3PaP2eL/Nydw8IC/WgYzG6Mu0/Om/eGyQ/zWJKjF4lEDCKBTcTzmULdoxPlZVAGzL1VVJdVlGv6tRWq9q6q6nv3+17ePnfNxx0X6BMWGIhzX5Nk99X6zbsB4LfffoM4PsrFupAFOUIhiUBgk7k8b6FQN9k4zyiD3utaNUfLyzoftB5p0N7V/vig7/bbP/9H+Ffuazk+Pp7BGxNQQZ5BHE7w27eA89vbt+5eyv/bhLzHcPkUEolLwfHAJBXo3gyUAasoKysvL6trbmlRlZWfbGkrvXixAxSIGzdY7PMDPhlJPmE+wds5gSEhHA+o8sDf/utfAGOp4RzcCByG53rj8fMcw2TpiWoQ+PJyqCC0tFy+XFZa2VZaWnv27NUbx3m82w84gznhPomBIZzghEBOCALOCQ7mcMLCnEETxLGwy2KTiaDgQFWUx+WyNw1OP+jvv99w415LM1AD3lrPHik9euTQkSOnqr79trsnXeiu25zmUxCeFJ4UGMQJ4oR5BXpSwZLiGeiZH7Y0Zy2DjieRQLs8zxHrn93u6++7devq5Tk5La01hwDjyJGS5pbOTm1H+8GSb/Wc9YHGX1+FKaisbZyEtaHn/SOp5PhbaR6WODAlhcL1JhGJvmD6cMVi/RtTSyukowWAmlurqg7N25HSWFWLtrrm1LnHerGfdGp2dva1j2L9TM7GdVcuf+seH/lgs+W+SUem8L1JeCKRx/XmCyR6w1MAAS6DXqAAzUGioqKiK1VgVp1obe02jciAzb5+PRuYt/ZtUoSh9QdqfHTkfZnFTfvgBiEfD/oCvDd3tYDPl0j0ps42KDItTVWqeUx0dPzZpga1prVV09py1TQiBZixidzZ2cCUTbu+2zLe6EWtBh87bvFUTAcGJxF5YIWjCIUCrkQyMmnSQpi7nadL4+K3xkaX1Dc0AHB19cFK9bwa6QaZUSQbmpWKRSJxRnhDZHx1VGFhiWVO6F6eNx/UUTyXLPAVCAVyg+nOD313W0pLo6FjldpqTTOUEur4uLiDl66aHo9IhXyecUyUDDgiUcCWUUNPydbv4yIjD1jkcLKyuEwBkccDuY3H03mA8+jbvvtlZXHRkKnmkxtgYmNj666YpkekIr5AMJv4jfH1rJHh68vRTZkuV8cBTqTlY8vh1RQWUARlNxmPF0iAnmvtQEns1vi2do2meT5WAHNU0zwwNaoXCfg8wavnY7OzRqOvL5aufPO0peVsbGRk1AmLgpR0ARfPp0MpBwcNwtcphqnuK21t7e1Xr7a3Awyw9isH4uJi6wBmBMLw+VwplG5+Rhesi0u+/qlGoz4bFRkZ/9BigEL4FG8+CcwgogPWni6WZ46b2tsgA/7SQNZyDcTmeP2VgSm9XuLP4/OZq/1Zs7M0mnEccAj5T9XgM1VRUZY5YTou25tC55NJJEd7e3uIM9WjUbe11WmaWxrUp9Stl+PBOJdvATW6dVg2k0RZvZqCn53FMIyvUfZYsm66W11T03I2Kuqh5d2NjkckirgkF6y9A8rua8U4DDZ1S6OpbVKrz6orK6J745taNZruKYARuiFRWBIZi0WFz85ifY2ztnA4WTZi0hwuPnbsQORyHAGFJHL1wwI1CEJKwXPoXPWS5mJT01mwslbEX2/VqDUDU4/1Op6/PdLFHk20tbObMJuxyKG8PDjCW6h7qjlWWFhcvPWg5UQIEgSI+Hg02hmFQKxOBXJyIc81gaUBWFkDWBuuTYIMEIJWBYVE2c0Z4DihCgDHjiLQPW0+VlRYXB57wKKg9aEb+QJ/bzQaBYc7sKGNRV7G+PSFWpXqWIX6YlPz5e6eqccgnykQAjX3srMDZRRtXzBUYIfyplBHemqOFRUdO1T0cJn4sIVADtoJDiexdDDY87zMjPGBBijV1GrNhYGpqccjyV/726MwoIFH2aFQ1nCP2VkPNHpoaMjOjuhFA26uKSw8uhwHptsgIjii0QgEgrx5EHAKshUTU40Qp7nHNDll0I9IpXxXe1fgVxAaFBJwXs+iHR2Hhwps3aDjB1NjTWHMscPLcoT+aFc0Gg5H8qBzRcMehSJnYrK7uXvyKfRgyQAafbFY7O/q5miLtbWztbMherw2OzpCehyYW/SA033xcOzh8uJHy+lhgm8Bjh0kBza+SzEHejp/6F2QnSIUCby96S4o2zkOJtgd5zMDvpBmLChg5kH5mddTW7o1ejk9oFPEznHI0HnghCJNAdn4u4uKfOkWIcnbGyQ1EgVcF8hxx+EIOHs0bqdxKFe2a+4Ed6q7dGvUshylv78jGmmLC4KW3ons7L0KRWrq3gUQzLBfiOfh6SgstLtC7g7DubvjCGi0TPZiSD6Pgb0ZOPd91Gfo8Xe0tfUmza3w45mKVIVcnvr+pDl1/4hYwObRcQiQA0j3nakbCeE+gT77E6VjQ6kLH3uzvyrq4HLPmXQSppMLghAyf4w6vkeuyJLvHP2wRrEoYM2hOzqAtHbITpeHhSUF+uTmSgFHvmfhdqYaVcvlgZIhk3h7kwjvGpYJhTxLkZo8+tF9BG/hubi4QJMUNZo9uiYtkJP794gI6f4hufy97MkfVcuFJ0AmAAlFWtiJjWekKvbs2GX4uATyXN1c7ZF2CLu8Cdjg9uC0/F2JKRJJuuSDe2E955dzGytZwPMmk983YOOKzL2yxJGPMEKRcLUrSGwEPA9ag5XjudkKwJFEjK7gqYteJBPwKJSPOJmZe+WJH4bYlSkX+XNdsLagIOTN/ed5gUI+xxleAWdwA/Ab+yMOBJLL0z64xLBTKGBhnWydUah5Duy5QrFiDkwvEwhXO5I+2ilDoB17PijS8wg4JtbWEbnAAdNMLpVI1ulWwhlNFoG+6hNOVmbqDtmO0Q81nU/HuoCKgMn/mLNunX5Fz8VGxFzSR3kwl3PpKbIdewzj70Fgd+Rqj8AqP3AkQqEwcWRFjhNzyd6UTzjp6enJO3bszDQsPCIQiF1dHHEY7oKnxlMgTsSKBOkjRAEUyicnGbmZc7bjne8GN2YJBBQymfz+CYJhVwTgiDYOrggkCcBiCZ+AQCpk5mamL0x4nVAiDviYAxuVSrgsKk2pXBGHTXGkKT+5t4m89PS8jD0LAVrHE7LJlNX098OOJEpDqF5efn6DK+GIxY4u/hs/mQ7Px8efj3+0MZcIQYtI130QDBKbSuWJkg2fzRmOEAmlLuIgucHCzlzI59P59G+G36dkRoRUyhNlb5J/Nmj4G+GGbDwjMTRtfGkQ2FVBm2XdB8emyqUbN+Wmpn2+44a37cqVCfWsNEu+5QaAvTKN8x703GAYGdQ/N6wk44YNu3dtgFkqI8OJTJaYzSa7rl9ZEfh3Myx3X4NMpkTuLdzhmzgM+yNNv0W0I5stzApJHv1DObDh5OS87RsMewywP9hGR5+P6mB/OGal9r+OI/ei'),
    ('front', 0, True): (72, 96, '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'),
    ('back', 0, False): (72, 96, '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'),
    ('side', 1, False): (104, 96, 'eNrtmftf0tnWx1EJBQVFRRRBIQRFvAQiKUSRFTOMj2hexsYoLUxTEzVFzabMVCpLU3uqmcwUtMujhrexi13MSOrMmXPygogY1eM5Z0qj/oZnf3VmzjxzFO0089tZL/r66gXf/f6utT577bX3Fwb7j8Fg00+sfPlk5nfDXDqcuOyXFYf7p38vzNH4/uUeeva7miMXfxeQqeXc0fjlAzfdVJbwze8AenH73NGj8Y+Xf4yuM4lxTz6d8+zcf1vn3GyojL3w7NPD1tR7pCx2+Qc23e2pO5T45NPD1tTbUBZzYdmBTIM9dUkxFz41Q8+vXLkLOImPrfgDvi/tm/3U9HSfaygrTfjJn9ln/7Sf3empPxpTcsP0iZwGTUP9iZKYk2DYF9Om786eO3fu7Nm6urNnzz6bfg+D/a9G0wU48S2/B6f+aGzJk9kXty9daUwoKSkpLS0pLYmPL780/MI08BPnk/05p6lvaKgAo95+2HS69FTj12XHYrdvj4vbvj0+PrGl5bZG8z/1ZcCfTxTC82ZNV2NjVXx8/DfNDY11DUfLSo9caunr67txqUmpLC1JGhxsqC+NL/l2hRk0vmJx6xlsamg4WlKSeL++4UxZWfmlS3rLgr1+PNx0NiGx8n5daXz8WWscrVYn3biSrpsGexoaGo6Xnr1dX5p4+MKw2fIhNysrJzd3zmKZM/a3VJS3lJfED7+3gglhs3F79db9aTmn6e2qa2w8NXT3a2Xf6NSc5eB6NoNOp9NoIdyNaR8sluHyKyWHraRHEUJ2cSGMrBg4TQ9I0bmW7y4f6weYvE1iLsXZEYt1oQVymXTR3g+Wk4dOWnFHEeKGdXEtWlEJs98P9moGH95oq+ufeq2VRvBJLs5IlK3dGmcymYQnkcNGDYfLpq0EzQWLxa8Cc+v+o3s//HCvtbxv8q1ZKomgkIloJHKNnR3akYR2dMNS6fL+spPaZTE0jAs2WLEyp6dnYOjO/abDF0ensjIkHDzWBeuCRGKxdghHtK2rrasznb1hg6+rp7ffUhhWENbFhbYy5v2fujUazc3mpouTk7nSiPVr8UjIEAiak52dk62TExoJ4ocPUyw91LjEDYsN9Fasol43d2lUjY0nJ6cmpeJwDIFAJDoibW1sHGmAg7VDYxFwGxsbVyJ1ybG0LFcXF4ZiFfXgWnPTzeoT5cOTU1kSZgDVB21r6+rn5WSLojpj1lDWYIkIgLGx9Q7z9F6KE+7q4ryKsMGeNTefViYc6ht9lbtXwowI94FGtfHz8rJBEx3XsMghRITrOhsbeqhDIQyzFMfN1WXVnO1JxaNzB6QCAcPf1gazLjl5nVeUH4ZApxPI4Uj7yOy3trY/yhxgMK/f3u2n5TOxLgGrSI9K1dOsTLw4+vbAAbGAwbC19fRKt8zNJUcF0/z9OThCONWnYN3UnC1qBLfE7TSGkOHi4r8y5xng9NQk9hvnDojzAgJsbYkB2T/K5flzqVu3+vvTcMTwgHS5sehNZqYBtkR+inABDFfsKnTwrFWl6Tl9cvj1K4iDsKGG5BdnWtJzLK++2uHvT8WhiOF5sqk3b7KyluYQGCFBboxVxa1b03F2ynJAFn2QSRWLJfJX6Xl5by0Fu1MY/p52mDWEzXKLpWDHjrGlixtDxMb+WgcslgK2UISeLzYZsy8WOWqV6mZ3rVF3QMbQsiQSCU2c/yHztWVqV4ooELcG42RraxdqeZOcmjq5JEcnFrP+v+BYtCJP3IK+mpouX758f2h2FrBeDIEE3awz5h7YtvbpFolkE461O99iKd4nWR8CJqqdHRz8sw3GBC9TwcDSExLwM2f9hqKiIiIdh/Mumv6mrq6uFljj3fsPHtyZnTWp1T09LcYDe4U0/V6RgBESwtqdnZ0pFlPtFg0VClxalqMICRGBxYoKhUqriMARiHgPD3zRdJ+y/syZ2gVUfX394L17pmuAM2A8kEYl6mUiKg5NEYtFIhANMhGDsbML/mzHjq/AXyfc0vmZSBOKAYiAKypSsPAEHIFAwOOJCtPVmJiYYxDkTO2Z+jO9Q/duXVP33gAc0VrJ470bcI6oIJY4LW0bNYSFc4XbYkJ3po4aCwuT7dflpy9dSKPFYg4D508kunvgPYgEJpMZFDp+q6f1fEViQkUVcOZM093Bwe7BH66re29NRdM25D3eSHVDInHULUKhD9XHxxUEbeOO7IJ8yNZhMIriJUFjErE4ghGIx3vgSTwu3oOAwylmejQ3NT3f1sXEJcXFxjVeGxzq7v3LjVbVrckt0gNvxCInhL0DEkmlEgg4TzgcbucXmW805kfZ2Kx7vRW+dd2SIEMW4PAFbDyJxcZDRvAcG74JWe8gsCuN5xq7H93t6X30vUo1MHwgw5InYvjYYxBg8bH3DGA4u7rCvZOTLa/z842F+fmvi+0wT72WBE18AWadJDyQTiTgSCQ+n68w3ehob+/oAJf2Tg0E+765tWvw7UN198BLi0UmpNGoBATC3tGfERAQgIXbwTHJma+NoJPLfw0qqVdUsXzpyH0lEQt5/kQPAptDZLPDtaaBjo5GpfJ0jVJZA4CaoUdKZWfPnb/eau75m8WSJuTQaTi0g6ur//qCVJQXmDmY0OSC4vxR46hlDCyty1aXMZGQiCcxmFyOO4EdxNLOttRUVyuV1ZAplbWDQ73K6hrN4KN/DKgezllyo4UsGg2HoxbIkzFRBfm2QAeIsPTs0dHC+XwwiTDL9k6GLCY+iOTPw7sTWGy29v2fVKeVEAb6AJcGh7qqlDWdg/e/f36399EcWICk2yQbfHa6YvxSUxF2tmB+2nlHJQPFTUYC53Y6LeePbhMziMLheLjjOewIltYElAUwleADcZSnHnaD/9Z0DQ49+uvA3Yd/z81Lk27bRsVg/Pb5ALGt8wI5iYyMSk59XZiMQTuNOHgvw9kUwWQL2WR3Dw6Hw2dpp6urlMqGU+3ttQv+KJW9vZBntZ2Dj77/C/Bofn+GdIunp2dodrCPE9zLew0CnhyZujPd+O5tdqgXCgYLXrZXZAbxWSQKj05n8yP0/cerwLA1kApA6Kqqld2DlcqaLuWZ7qGhv/3jgubPecIAT9fIyOAAGgaTjvH0y0//ca4YmqWbt2KKIr2W5eiEQiGDSGAT8TymQPvkVFUlpICFS3VdZXWV+pGmWtnVW1t3/8HQmzsXbvh54oL9IoODcZ7rUh0+27g1fV12fmF6ampkJMJPsVQX8rM7AgGJQGCTOVxfgUA73bLIqISujR3q41WVPQ87jjVr7mm+fTh058Of/yvqM8/1YX5+3qGbk1Eh3iFhYaGhYWGRka6gafBR/GsT8guGw6OQSBwKjgsmKV/7frgSWHVlZVVVZWNbe7uysup0e2fF5cvdoEAMDLDYF4f9slP9Iv1Cd4YFh4eHeUGVBw6tPwhPaw3nyGYQMDzHF49f5OinK07VgcRXVUEFob396tXKiprOioqG8+evD5zkcu88DBvJj/JLCQ4PC00ODgtHQBxwsUMS/XaGWdllsclEUHCgKsrlcNhbRmYfPnr0oHngfnsb8AZcOs4fqzh+7MixY2dqv/yyrz9L4KndmulXHJUalRocEhYSFukT7E0FS4p3sPdI5PKc9Qw6nkQC7fIiR6R7cWfo0dDt29evLrjT3lF/BDCOHStva+/p0XR3HS7/Uhe2Mdj46m2knMraEZa8PuJiYAyVnHQ706vICgemoFA4viQi0R9MH45IpHtvau+A/GgHoLaO2toji3asIkHZrqmrP3PhqU4UIJmZn59/5yffOJe/ecO1q196JsU83Gq9b9KSKTxfEp5I5HJ8eXyxTv8cQEDIoA8oQAuQ2NjYuBolmFWnOjr6TONSYPPv3s0HF67/kBqt7/iGmhQX80BqddM+sknAw4O+AO/LWcvn8cRinamnE8pMe2utchETF5d0vrVZpe7oUHe0XzeNSwBmcqpgfj5475Y9X20ztPhQ68DPTlo9FdOCwUlELljhKAIBnyMWj0+bNBDmXs/ZisSk7Qlx5U3NzQBcV3e4RrXojWST1CiUjs5LREKhKDuqOSapLrakpNw6J2I/15cH6iieQ+b78wV8md5095uhe+0VFXHQsUpDnboNkoQqKTHx8JXrpqfjEgGPa5wUpgGOUBi0bULfX77968SYmENWOWG5uRwmn8jlAm3j8XQu4Dz5cuhBZWViHGTKRXEDTEJCQuM10+y4RMjj8+dTvjC+mzcy/P3DtDOmq3WJgBNj/dhybC2FBTyC1E3G4/li4M+NLuBJwvakzi61um0xVwBzXN02PDOhE/J5XP5b8+T8vNHo74+lK94/b28/nxATE3vKqkMKOp+D59EhycFBg/D5Xv1M37XOzq6u69e7ugAGWNe1Q4mJCY0AMw5heDyOBJJbgNEN6+ZWpHuuVqvOx8bEJD22mqBwHsWXRwIziOiEdaSLZDkGU1cnZCBeasjab4DcnGy6Njyj04kDuTwec20ga36eRjMaAIdQ9FwFflMbG2udE6nlsH0pdB6ZRHJ2dHSEODP9alVnZ6O6rb1ZdUbVcTUJjHP1NvBGuwHLZpIoa9dS8PPzGIbxHcoRS9bO9qnq69vPx8Y+tr670XKJRCGH5IZ1dEI5fC43wGAzt9XqhlaV6ryqpjpuMKm1Q63umwEYgQcShSWRsVhU1Pw81t84bw+Hk6XjJvXRshMnDsWsxOFTSEL3ACzwBkHYW2yGzlWvqC+3tp4HK2t10s0OtUo9PPNUp+UGOiLdHNFEeweHKYsFixwtLIQjfAXa5+oTJSVlZdsPWxdCCD9IyMOj0a4oBGJtBnCnAIpcK1gagFU2g7XhxjRQgAC0KigkymHBAMcFVQw4DhS+9nnbidKSsqqEQ1Yd2hixmccP9EWjUXC4ExvaWBRmG2YvNSiVJ6pVl1vbrvb1zzwFeqZACNTCx8EBlFG0Y/FosQPKl0Id768/UVp64kjp4xXywxYAd9AucDiJpYXBzIU52YbhZkhqKpX60vDMzNPxtM8DHVEY0MCjHFAoW7jX/LwXGj06OurgQPShgTDXl5QcX5GzSUhwRqMRCAR568LBlrk4T/64BeK09ZumZ55qxyUSnrujO4grSA0KCTjv5tHOzmOjxfYe0PGDqaW+JP7E0ZU4gkC0OxoNhyO5Px0rGvbI5fK+tr7p5zMv3rwsAo2+SCQKdPdwtsfaO9g72BG93lmcnSF/nJjbdIDTd/lowtGqsicr+MMENwGOw9ZFzpQ8Uw6ZYfrHNx8+mPV7BUK+ry/dDWW/wMGEeuL85sAdmcbiYmYhpM/C/oaK7XGlKwmbiV3gkH86DpzKy9svl2dk7De8/PD2lXlcsk1A8vUFokaiQOiCwzxxOALOEY3bbRwtkO5ZOMGd6avYHrsSRxEY6IxG2uNCfmntc+QZcpksQ29+CfzR6g8K8Fw8HYWFdlfI9EicpyeOgEZLpa9HZYsY2PvhC1+vxNEyA53t7X1Jv9pQGPbJ5Lmy3RPacfOrVy/NZq2Iz+bScQggAqTn7ozNhGC/gymSydGMjJ/Po98frI09vEJ+xEwXNwQh/NeHqHp9Rsa+fXv2HDS/ApHTsihg0aE7OwFdO+VlySIj/QoKJIAj2/fLufdMi9K6DhQMqdjXl0T4TbtikOfsl6aMm1++emso0oZu47q5uUGzFDWRN7EurODv0dGSg6My2T/P16e/VVrPTpCUD+RE+u0+LCdnvyxlwjBhfvXSoNDyue4e7o5IB4RD4VRh6M6De1L2isVZ4oxfneP3X7QeNlYan+tLJv9L+2XIyZHJMvUTL18atFq+QChY6w6kjYAXjhQZCvLkgCOOnlj1K5eRTcAdNoW8RJcHgXbtmxg3m4v25MiEgRw3rD0oCYUGc7FctoAZ+4h3OzopX7DWmbTU9jU3J2OXdNe4Xj8xpt8t4LOwLvauKBTgmOXyj+ZMpAlBs7MkB2bIztor3bXPMD6h03EJOCbW3hmJKpwwm6fyZBLxhg26j3lZNS7ikMjkpbvjgpwF27Vr4iCXR8e6gZqAKZLrXgGOWCAQpIx/TOBEHLIvZZku3ACSlFOQkwUErJPwRe5uzjgMJwfUPAjzcfmJFgZRKMs3+1OFWVmF2fugLVkun08hk8lUhUG/JxpwhJtHPgYkDsJiCcu/mzEbDGbD4gIiFgUtciYmJGIOi0pTKD6Gw6Y40xQrP5p2A1fAJlPW0hUG83iKJJzq4xMQMPIRHJHI2S1w88rB1nLEAtC90RUHdYYciVhMpXKFaaueqmPRQoHETRQi068M2izg8eg8+heG7OxoiYQrzNuyirt+wnwh2JSHZ6REZBpWUT3AjgfayGqnCjNkks1bCjIyVx23sR17CqQCHStzVTHmBIF9LC1Ma9brx0d0Zv1HCG5Mn75nE0y7qt+mMFkiNpvsvlEL+zdMv/rHUjCZYpmvYJd/CuwPNd024a48tiA3fPVC+/dsLC2tcOcm/T497A+2iQnzhBb2h2M+wv4P3UH9BQ=='),
    ('front', 1, False): (72, 96, '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'),
    ('side', 1, True): (104, 96, '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'),
    ('front', 1, True): (72, 96, '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'),
    ('back', 1, False): (72, 96, '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'),
    ('side', 2, False): (104, 96, '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'),
    ('front', 2, False): (72, 96, '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'),
    ('side', 2, True): (104, 96, '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'),
    ('front', 2, True): (72, 96, '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'),
    ('back', 2, False): (72, 96, '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'),
    ('side', 3, False): (104, 96, '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'),
    ('front', 3, False): (72, 96, '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'),
    ('side', 3, True): (104, 96, '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'),
    ('front', 3, True): (72, 96, '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'),
    ('back', 3, False): (72, 96, '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'),
}

def crispy2_canvas(key):
    w, h, s = CRISPY2_DATA[key]
    raw = zlib.decompress(base64.b64decode(s))
    c = Canvas(w, h)
    for y in range(h):
        row = c.cells[y]
        for x in range(w):
            v = raw[y * w + x]
            if v:
                row[x] = CRISPY2_KEYS[v - 1]
    return c

def crispy2_side(step=0, talking=False):
    return crispy2_canvas(('side', step % 4, bool(talking)))

def crispy2_front(step=0, talking=False):
    return crispy2_canvas(('front', step % 4, bool(talking)))

def crispy2_back(step=0):
    return crispy2_canvas(('back', step % 4, False))

def crispy2():
    frames = []
    side = [crispy2_side(s) for s in range(4)]
    for d, flip in ((RIGHT, False), (LEFT, True)):
        pick = (lambda f: f.mirrored()) if flip else (lambda f: f)
        frames.append((d, STAND, 0, pick(side[0])))
        frames += [(d, WALK, i, pick(side[i])) for i in range(4)]
        frames += [(d, TALK, 0, pick(side[0])), (d, TALK, 1, pick(crispy2_side(0, True)))]
    frames.append((FRONT, STAND, 0, crispy2_front()))
    frames += [(FRONT, WALK, i, crispy2_front(i)) for i in range(4)]
    frames += [(FRONT, TALK, 0, crispy2_front()), (FRONT, TALK, 1, crispy2_front(0, True))]
    frames.append((BACK, STAND, 0, crispy2_back()))
    frames += [(BACK, WALK, i, crispy2_back(i)) for i in range(4)]
    return frames


# -------------------------------------------------------------- Extra 2 ----

# Extra 2: the user's black Chihuahua at Curse of Monkey Island's detail
# (SCUMM v8: 96 rows, 236 colours, glossy shading, a dark outline with a
# blue-grey and maroon-brown rim so he reads on dark and light places); by an
# artist panel, the side and back from the user's SIDE/BACK sheet, the front
# from the user's first picture, the white on his neck taken away and his
# chest's made a tiny patch at the user's word (the pictures not kept or read
# here). Side 104 x 96 (facing right), front and back 72 x 96; ear tips on
# row 1, the feet's lowest row 94. Every frame is baked as palette indices
# (zlib + base64, 255 = transparent) and decoded when drawn.

EXTRA2_PALETTE = [
    (1, 1, 1), (2, 0, 0), (3, 1, 0), (3, 1, 2), (5, 1, 1), (5, 3, 5),
    (6, 2, 2), (7, 2, 2), (8, 3, 4), (8, 5, 7), (8, 8, 12), (9, 3, 2),
    (9, 3, 3), (9, 4, 3), (9, 10, 17), (10, 4, 3), (10, 4, 4), (10, 6, 8),
    (11, 5, 6), (11, 7, 10), (11, 13, 22), (12, 4, 4), (12, 8, 13), (13, 11, 17),
    (13, 15, 27), (14, 4, 4), (14, 5, 5), (14, 7, 8), (14, 8, 11), (14, 13, 22),
    (15, 9, 13), (15, 19, 32), (16, 10, 20), (16, 11, 16), (16, 23, 39), (17, 6, 6),
    (17, 13, 20), (17, 15, 24), (17, 17, 28), (18, 13, 20), (19, 7, 8), (19, 8, 11),
    (19, 11, 14), (19, 19, 34), (19, 29, 48), (20, 12, 17), (21, 15, 20), (21, 15, 24),
    (21, 15, 30), (22, 19, 27), (22, 22, 39), (22, 24, 44), (23, 7, 7), (23, 9, 10),
    (23, 36, 62), (24, 11, 14), (24, 17, 22), (24, 31, 54), (25, 15, 17), (25, 22, 33),
    (25, 27, 48), (26, 19, 41), (26, 26, 40), (26, 45, 73), (27, 20, 27), (28, 10, 9),
    (28, 17, 23), (28, 31, 53), (28, 31, 60), (28, 38, 68), (29, 10, 11), (29, 11, 14),
    (29, 13, 22), (29, 26, 36), (29, 35, 63), (30, 14, 16), (30, 24, 53), (30, 54, 86),
    (31, 16, 19), (31, 23, 31), (32, 28, 44), (32, 43, 74), (33, 8, 6), (33, 33, 57),
    (33, 48, 82), (34, 19, 30), (34, 62, 97), (35, 13, 14), (35, 18, 23), (35, 22, 36),
    (35, 28, 37), (35, 33, 49), (36, 32, 43), (36, 38, 60), (36, 71, 110), (37, 15, 18),
    (39, 23, 25), (39, 51, 88), (39, 58, 94), (40, 25, 32), (40, 37, 54), (40, 43, 64),
    (40, 65, 103), (41, 9, 16), (42, 16, 16), (42, 30, 49), (42, 46, 76), (43, 19, 29),
    (43, 19, 57), (43, 31, 37), (43, 72, 112), (44, 18, 20), (44, 25, 40), (44, 31, 70),
    (44, 81, 123), (45, 38, 46), (46, 42, 55), (46, 67, 104), (46, 87, 132), (47, 62, 94),
    (48, 13, 10), (48, 47, 65), (48, 74, 118), (50, 23, 33), (50, 29, 30), (51, 21, 25),
    (51, 60, 91), (52, 34, 40), (52, 36, 47), (52, 92, 143), (53, 51, 71), (53, 55, 82),
    (53, 103, 153), (54, 20, 20), (54, 38, 63), (54, 80, 130), (55, 29, 43), (55, 62, 92),
    (56, 16, 15), (57, 25, 31), (57, 41, 43), (57, 59, 87), (59, 27, 37), (59, 40, 54),
    (59, 55, 78), (60, 23, 25), (60, 48, 65), (62, 34, 33), (62, 57, 83), (63, 45, 60),
    (64, 34, 41), (64, 45, 46), (64, 51, 72), (64, 68, 92), (64, 76, 108), (65, 22, 16),
    (65, 42, 53), (66, 25, 27), (66, 37, 49), (67, 38, 45), (68, 28, 32), (69, 32, 35),
    (69, 52, 51), (73, 31, 21), (73, 50, 66), (73, 59, 78), (74, 34, 44), (74, 39, 33),
    (74, 58, 60), (79, 34, 38), (80, 42, 43), (81, 29, 29), (81, 41, 56), (82, 56, 49),
    (82, 73, 86), (83, 37, 51), (84, 69, 69), (85, 45, 51), (86, 32, 23), (86, 37, 45),
    (89, 42, 25), (89, 61, 82), (90, 34, 34), (90, 86, 105), (91, 25, 21), (91, 44, 62),
    (94, 61, 57), (95, 48, 69), (98, 42, 44), (98, 46, 26), (98, 49, 52), (98, 80, 81),
    (100, 34, 26), (105, 38, 34), (105, 93, 95), (106, 70, 66), (107, 50, 70), (113, 43, 40),
    (115, 55, 83), (116, 79, 74), (117, 96, 89), (123, 111, 113), (126, 44, 34), (130, 52, 48),
    (132, 91, 83), (133, 67, 59), (138, 127, 129), (139, 48, 37), (142, 85, 72), (144, 101, 91),
    (153, 55, 43), (160, 114, 103), (161, 64, 51), (166, 141, 134), (167, 79, 64), (174, 125, 110),
    (181, 70, 55), (186, 139, 125), (189, 90, 72), (189, 170, 168), (205, 86, 66), (205, 153, 135),
    (205, 161, 146), (214, 100, 76), (215, 181, 167), (216, 109, 85), (218, 173, 154), (226, 119, 94),
    (235, 127, 98), (235, 191, 170), (235, 202, 188), (243, 116, 87), (249, 231, 217), (250, 212, 194),
    (253, 224, 206), (253, 249, 242),
]

EXTRA2_FRAMES = {
    ('side', 0, False): (104, 96,
        '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'
    ),
    ('side', 0, True): (104, 96,
        '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'
        'fwA9wFYO'
    ),
    ('front', 0, False): (72, 96,
        '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'
        'oyMS'
    ),
    ('front', 0, True): (72, 96,
        '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'
        '5Q=='
    ),
    ('back', 0, False): (72, 96,
        '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'
    ),
    ('side', 1, False): (104, 96,
        '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'
        'Pp//o9Ov6dx9P/4HesZoOQ=='
    ),
    ('side', 1, True): (104, 96,
        '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'
        'Pp//o9Ov6dx9P/4HesZoOQ=='
    ),
    ('front', 1, False): (72, 96,
        'eNrV2e9PG+cdAPAXme27jRfcuYWNc1y5xTy6q3zWdUE4NkIWSIksJJ+zKIrxD2HJRIJOJ15wVWel'
        'w5atoLrhZNf4UrM42K5xC5uFmiYuQoWmIKHEMEJEmRe5UiMGikr6R3RnCJ26dZvvcfZij5DwC99H'
        '3+f53vP9Pnr8/ff/FwMA8EIYISm8CAgkP3s/+QIgkFpev5ZsfG4g9UVFghqemxRPpbp+bbBRCKQ+'
        'q+xVVof/0xqBOnIKUuuV/b3N/Ll/CwEppcn6nIPqxnujP/3dmvL+n8Q6nOXdvYOD6pfnLv3EEgGQ'
        'FK6tbt6px/miUjnYr356pv9fAwLJ5OVbm5XN4n9PAhC3qtX93d38r14z/VNAUjDn3lvdrVY3Z+px'
        '7u892X68fVOl1DrGwY+DOXNzvbK3X61jWtLXb1d3NnbypELLWB0COMmxFMxvz/xup7onJXO+nncL'
        'FLd2djeGdbTVxYf56elp4QgTBE3bL1ar+1IKspm6HGl9Hn/qZFhPfFoIxMOSI/0JFhr52W82pGiq'
        '9YUjOVtP1m+ZbLwQCXi9Q+4rgek/hAXBqsZP3dzeOdh7NJOpz0nfGtZRjDsyfUVivNIYiseFsJsl'
        '277c3q4+eVSsc+eBYrvW6HCHpwPeoRGHw+GWQnIPjfSqVfmd7cr+Vr01BaSNlCUgBNyS0WOxMJYe'
        'b8AxYNS1v7bx+HFlGdS/40lgC4Q9NrdFylM7MFrcgYDDSNHEanVPjsNldP65h3en9IxaAwyaViNj'
        'CYRdJKW+Wals1V+WQKIJ6//6u/srPjNmtFg1eouRC7IemtB25nJyCi4QiKlHD50rH09Jb2LA5nxn'
        '7ds/5316lJYYea1nyHn3bn7lHWZoKMAHgn/863cPVkZ70Zy86g+ifJK+nM+P2vh4gmcNvVN3Px5e'
        'GcZzMis2EPgAg9EePiymM2lxzMVNrazk2zJyCz9IsLzLE59LFSZtARs7lvD4z58jWmdkOyJpNPD8'
        'WOETbvGhx2ZMcFZUqbeJshsRyOGkkY3z9yYXy60/1y6M0YyeuSG/n4EZfVcXHV6490GLNHwLY6ZL'
        'uhxMpwYz5GWKX7zH+U0+p1jgAZWB6q5gxjxIcosFzu+76l8ohCitCNelgWjv/TB4//ZH153cAm9A'
        'e+OQTpQm5756evj0q2++eeDrpbrgHBA9hWpV5rXDw8Onf5uz40gTpCMoXlYhFGH+8BOOOIV3dSoh'
        'nTiKNb2soO39lKGLpFCkGdKJOCzMab2NMZn8jP600eKIQMYz4WD07Qxjskr/9B2OCdh4JkYGWtv1'
        'DMMYjaZWdmQCMp6Id2RSisRoMgVNVn/QcxHSEbzdjkmLlabpXh3NTv4a1ol6+ywej8tgoA26dhPT'
        'c3Ec2ol5XCylk4bJz8I5AIx7vd0D7JyJ0mqDOt1VtqfPOy6/boDxN6/09XQYfAbKjOl0dp3+jW7v'
        'm+MwzkT3G/oWez95/ry9395y+vWeCSjnAm+ztKvtSpwyaJR2dStj4y/IdQCIDhSL7/pbMQSXHLoZ'
        'QVv877qLA1G5XfDViwMzRdqJ+XBCq5skfJjdxFoHLr4alefEz154yb+kRVEUI8oatRpDtSbTpZcu'
        'nI3LdPreDhl0QQzFsPJhGcMwjYYyGEJv98l0EmffSvcTTpzAys+ePSvjGKHVEP3pt84m5Dmi//Pi'
        'VQIhj5xvyziO2zUEWfzcL7NngMxS8aMuBHHiD54ePisTeDOOdJHFJbktDMws3Z7/PYI0DyIPymUN'
        'STQjCE7cXpJ7TgDp7HzNQVRKH0EQpFn6iDTPZ9Oyzxu53HJWpZKepvBmQoqn9nkwB3FOmF/ONqlq'
        'TytxQiM5TSpDDqYAgcyssjYbRIVTGmliSqsLro6lBkfPq44knKAoYnQwBeckybZjRhpmaa1JyLpa'
        '6L9zvQYdrTZy/Q45BnW9AFL++Wxn27HT1pmdN4XgnLDL3JkdlPIlLfdgtpMIhSAbqsiRNSeXqzmX'
        'uJA7DJkwESW6EOlwmWvu5UJiCPZcV5hFFYrazgS51z2xUijViHMUBIj9ki2F4tAOplAcFS6QoLlS'
        'LAztaJHn8cRb/KVZyMspkAxx6HHhApFXqFIK1klxs5rjHIGEWluCvQgEibGS+nhtgahQQzvS0yXs'
        'eY5ABhPj0E64ZD5xRCwN70SC3IkTR2MReIeLCSeOJgTvhNnZE0fgCg3E0+E3Hx8wgBArwTuBCOo8'
        'WiAQ7fA3kK/xIK5MH++LU4QVPh6hpM09fw8JswvWAdHZH27BQCY0G4c6PgMgWKzmkxIIxEIBYl+A'
        'BSEpqFmr4uTYBIRCDKJbgHJ5RFyb5XInFwgg6jIwEKdnsHbjg7UbP9wfgPFXFFa2OwqgFugfZ2UQ'
        'jaBcrGMi2uh9feIvY66v+YXFRp3cXObGw7QoNvxDBPjxRP9n4+9RSDNU'
    ),
    ('front', 1, True): (72, 96,
        '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'
    ),
    ('back', 1, False): (72, 96,
        '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'
        '739vifWHU75j/Q+X6izk'
    ),
    ('side', 2, False): (104, 96,
        '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'
    ),
    ('side', 2, True): (104, 96,
        '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'
    ),
    ('front', 2, False): (72, 96,
        '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'
        'oyMS'
    ),
    ('front', 2, True): (72, 96,
        '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'
        'oyMS'
    ),
    ('back', 2, False): (72, 96,
        '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'
    ),
    ('side', 3, False): (104, 96,
        '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'
        'bhzb1c1C6PtfPf0eDF7jP76MvLE='
    ),
    ('side', 3, True): (104, 96,
        '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'
        'bhzb1c1C6PtfPf0eDF7jP76MvLE='
    ),
    ('front', 3, False): (72, 96,
        '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'
    ),
    ('front', 3, True): (72, 96,
        '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'
    ),
    ('back', 3, False): (72, 96,
        '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'
        'sc+/+U3xZ3Pkp/LTr57JP5dzjEr8T8Z/ALnyHn0='
    ),
}

EXTRA2_COLOURS = {chr(0x100 + _i): _c for _i, _c in enumerate(EXTRA2_PALETTE)}
EXTRA2_CACHE = {}

def extra2_canvas(key):
    if key not in EXTRA2_CACHE:
        w, h, blob = EXTRA2_FRAMES[key]
        raw = zlib.decompress(base64.b64decode(blob))
        EXTRA2_CACHE[key] = (w, h, raw)
    w, h, raw = EXTRA2_CACHE[key]
    c = Canvas(w, h)
    for y in range(h):
        row = c.cells[y]
        for x in range(w):
            v = raw[y * w + x]
            if v != 255:
                row[x] = chr(0x100 + v)
    return c


def extra2_side(step=0, talking=False):
    """Facing right, 104 x 96; feet on row 94. Steps 0..3 trot (diagonal pairs
    alternate, the body a row lower on 1 and 3); talking opens the mouth."""
    return extra2_canvas(('side', step % 4, bool(talking)))


def extra2_front(step=0, talking=False):
    """Facing the viewer, 72 x 96; steps 0..3 lift one fore paw then the other."""
    return extra2_canvas(('front', step % 4, bool(talking)))


def extra2_back(step=0):
    """Facing away, 72 x 96: ear backs, glossy back, tail up, hind legs."""
    return extra2_canvas(('back', step % 4, False))


def extra2():
    frames = []
    side = [extra2_side(s) for s in range(4)]
    for d, flip in ((RIGHT, False), (LEFT, True)):
        pick = (lambda f: f.mirrored()) if flip else (lambda f: f)
        frames.append((d, STAND, 0, pick(side[0])))
        frames += [(d, WALK, i, pick(side[i])) for i in range(4)]
        frames += [(d, TALK, 0, pick(side[0])), (d, TALK, 1, pick(extra2_side(0, True)))]
    frames.append((FRONT, STAND, 0, extra2_front()))
    frames += [(FRONT, WALK, i, extra2_front(i)) for i in range(4)]
    frames += [(FRONT, TALK, 0, extra2_front()), (FRONT, TALK, 1, extra2_front(0, True))]
    frames.append((BACK, STAND, 0, extra2_back()))
    frames += [(BACK, WALK, i, extra2_back(i)) for i in range(4)]
    return frames


def _each_name_once():
    """Each character's section keeps its own names: one defined twice at the
    top level would change an earlier character's drawing (0166's Suzy 2 had
    redefined Suzy's W and H)."""
    import ast
    seen = set()
    for node in ast.parse(Path(__file__).read_text()).body:
        names = [node.name] if isinstance(node, (ast.FunctionDef, ast.ClassDef)) else \
            [x.id for t in node.targets for x in ast.walk(t) if isinstance(x, ast.Name)] if isinstance(node, ast.Assign) else []
        for name in names:
            assert name not in seen, f'{name} defined twice in tools/custom_characters.py'
            seen.add(name)


_each_name_once()


CUSTOM = [(1, 'Crispy', crispy, CRISPY_COLOURS, 0.3), (2, 'Suzy', suzy, SUZY_COLOURS, 0.95),
          (3, 'Extra', extra, EXTRA_COLOURS, 0.3 * 40 / 38),  # (drawn 38 rows tall in his 40: 0.3 of a person, as Crispy)
          (4, 'Sith Ewok', ewok, EWOK_COLOURS, 0.6 * 48 / 46),  # (drawn 46 rows tall in 48: about 0.6 of a person, as an Ewok)
          (5, 'Suzy 2', suzy2, SUZY2_COLOURS, 0.95),  # (52 rows tall in 56, as Suzy)
          (6, 'Crispy 2', crispy2, CRISPY2_COLOURS, 0.3 * 96 / 94),  # (drawn 94 rows tall in his 96: 0.3 of a person, as Crispy)
          (7, 'Extra 2', extra2, EXTRA2_COLOURS, 0.3 * 96 / 94)]  # (drawn 94 rows tall in his 96: 0.3 of a person, as Extra)


def write_inc(path):
    lines = ['// SPDX-License-Identifier: GPL-3.0-or-later',
             '// Generated by tools/custom_characters.py: the new engine\'s custom',
             '// characters, newly drawn there (not taken from any game). Do not edit.',
             '']
    table = []
    for costume, name, art, colours, height, *light in CUSTOM:
        # (Gzip-compressed from 0174, as the export's files; the engine reads
        # it whole. mtime 0: the same bytes each time. Its height against a
        # person by its first frame, standing, as the engine checks it: a
        # lit blade's frames are taller.)
        frames = art()
        data = gzip.compress(svc(frames, colours, costume, *light), compresslevel=9, mtime=0)
        tallest = frames[0][3].height
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
    for costume, name, art, colours, *_ in CUSTOM:
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
