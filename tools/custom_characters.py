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


def extra_gloss(c, points, dy=0):
    """His sheen, only on his black fur."""
    for x, y, colour in points:
        if c.get(x, y + dy) == 'B':
            c.put(x, y + dy, colour)


# His build, as in the user's photos, drawn again by a panel of artists and
# judges (2026-10-22: "His head is still oversized"): slender and fine-boned,
# a small head (from the side, head and snout about 41% of his body; from the
# front, the skull no wider than his chest), big ears flaring out more than up,
# legs about as long as his chest is deep.
# Proportions (from the photo of him held up facing the camera):
#   side: head and snout 11 px (x 35..45) against a body 27 px from chest to
#         rump (x 14..40), about 41%; the skull 8 rows (12..19);
#   front: the skull 10 px wide (12..21) over a 12 px chest; the ear tips
#         3 rows above the skull's top and 20 px apart (about 2x the skull);
#   legs: 9 rows below the chest (30..38) under a chest 10 rows deep (20..29).
# Silhouettes are filled in fur (row -> spans), outlined, then the face and
# the sheen are placed pixel by pixel.

# ---------------------------------------------------------------- side ----
EXTRA_SIDE_HEAD = {
    # the near ear (behind, its pink inside to us), the far ear ahead of it
    8: [(34, 34)], 9: [(33, 35), (40, 40)], 10: [(32, 37), (39, 41)], 11: [(32, 42)],
    # the round skull, the stop, the short snout, the jaw
    12: [(33, 42)], 13: [(35, 43)], 14: [(35, 45)], 15: [(35, 45)], 16: [(34, 44)],
    17: [(34, 43)], 18: [(32, 41)],
}
EXTRA_SIDE_BODY = {  # the neck sloping down to the withers, the rounded chest, the tucked belly
    19: [(30, 41)], 20: [(18, 40)], 21: [(16, 40)], 22: [(15, 40)], 23: [(15, 40)], 24: [(15, 40)],
    25: [(15, 39)], 26: [(16, 24), (28, 39)], 27: [(16, 22), (30, 38)], 28: [(17, 21), (30, 37)], 29: [(31, 36)],
}
# the tail: up from the rump, back, over and forward, its pale tip at the end
EXTRA_SIDE_TAIL = ["..KKKK.",
             ".KBLLBK",
             "KBKKKWK",
             "KBK..K.",
             ".KBK...",
             "..KBK..",
             "...KB..",
             "...KB.."]
EXTRA_SIDE_FACE = {
    # the far ear in shadow; the seam between the ears
    (40, 10): 'b', (40, 11): 'b', (39, 11): 'K',
    # the big round eye, its shine, the tan rim under it
    (40, 13): 'K', (41, 13): 'K', (39, 14): 'K', (39, 15): 'K',
    (40, 14): 'D', (41, 14): 'w', (40, 15): 'E', (41, 15): 'D', (41, 16): 'r',
    # the black nose at the end of the snout, lit
    (44, 14): 'N', (45, 14): 'N', (45, 15): 'N', (44, 15): 'n',
    # grey about the mouth, the mouth's line, the small white patch under the jaw
    (43, 15): 'G', (42, 16): 'g', (43, 16): 'K',
    (40, 17): 'g', (41, 17): 'W', (40, 18): 'W',
}
EXTRA_SIDE_JAW = {17: [(34, 44)], 18: [(33, 43)]}  # the jaw dropped a row
EXTRA_SIDE_TALK = {(42, 16): 'K', (43, 16): 'M', (42, 17): 'M', (43, 17): 'T', (41, 17): 'g', (40, 17): 'g',
             (41, 18): 'W', (40, 18): 'W'}


def extra_fur_only(c, pixels, dy=0):
    """Single pixels, only where his fur is (never over the outline)."""
    for (x, y), ch in pixels.items():
        if c.get(x, y + dy) in 'Bb':
            c.put(x, y + dy, ch)


def extra_leg_path(x0, top, swing, hind):
    """A thin leg's left column per row, from row `top` down to its paw (rows
    37..38). A hind leg is set a pixel forward above the hock (row 33)."""
    cols = {}
    for y in range(top, 39):
        t = min(1.0, (y - top) / (37 - top))
        x = x0 + round(swing * t)
        if hind and y < 33:  # the thigh forward, the hock angled back
            x += 2 if y < 32 else 1
        if y - 1 in cols:  # never more than a pixel's step from the row above
            x = max(cols[y - 1] - 1, min(cols[y - 1] + 1, x))
        cols[y] = x
    return cols


def extra_leg_fill(c, cols, colour):
    for y, x in cols.items():
        extra_spans(c, {y: [(x, x + (3 if y >= 37 else 2))]}, colour)


def extra_leg_stamp(c, cols, colour, below):
    """The leg drawn over whatever is there, its own outline round its fur
    (rows from `below` down): K fur K, the paw K fur fur K over KKKK."""
    for y, x in cols.items():
        if y < below:
            continue
        if y == 38:
            crispy_stamp(c, x, y, ["KKKK"])
        elif y == 37:
            crispy_stamp(c, x, y, ["K" + colour * 2 + "K"])
        else:
            crispy_stamp(c, x, y, ["K" + colour + "K"])


def extra_side(step=0, talking=False):
    """Facing right: 48 x 40, feet on row 38. `step` 0..3 walks."""
    c = Canvas(48, 40)
    b = 1 if step in (1, 3) else 0  # a bob as the legs pass
    # near hind and far fore move together, far hind and near fore together.
    # On step 1 the legs spread (the far ones swing less, so they never
    # hide); on step 3 they pass, and each near paw lands squarely over its
    # far one, so the feet never merge into one wide blob.
    near, far = [(0, 0), (2, 1), (0, 0), (-3, -2)][step]
    legs = [  # far ones first; (path, colour, first row below the body)
        (extra_leg_path(22, 26 + b, far, True), 'b', 29 + b),
        (extra_leg_path(29, 28 + b, -far, False), 'b', 30 + b),
        (extra_leg_path(17, 26 + b, -near, True), 'B', 29 + b),
        (extra_leg_path(34, 28 + b, near, False), 'B', 30 + b),
    ]
    for cols, colour, _ in legs:
        extra_leg_fill(c, cols, colour)
    for rows in (EXTRA_SIDE_HEAD, EXTRA_SIDE_BODY) + ((EXTRA_SIDE_JAW,) if talking else ()):
        extra_spans(c, rows, 'B', b)
    extra_outline(c)
    crispy_stamp(c, 13, 14 + b, EXTRA_SIDE_TAIL)
    for cols, colour, below in legs:
        extra_leg_stamp(c, cols, colour, below)
    # the near ear's dusky pink inside, deeper at its base
    # (pink only in its front half; its back edge stays black fur)
    extra_fur_only(c, {(34, 9): 'P', (34, 10): 'P', (35, 10): 'P', (36, 10): 'P', (35, 11): 'P', (36, 11): 'P',
                 (37, 11): 'p', (36, 12): 'p', (37, 12): 'p'}, b)
    extra_paint(c, EXTRA_SIDE_FACE, b)
    if talking:
        extra_paint(c, EXTRA_SIDE_TALK, b)
    extra_gloss(c, ((39, 12, 'L'), (33, 11, 'L'),
                    (22, 21, 'L'), (23, 21, 'L'), (24, 21, 'l'), (25, 21, 'L'), (26, 21, 'L'), (27, 21, 'L'),
                    (34, 19, 'L'), (33, 20, 'L'), (16, 23, 'L'), (16, 24, 'L')), b)
    # the tail's ridge and its pale tip; white hairs on the chest
    extra_paint(c, {(39, 22): 'g', (39, 23): 'W', (38, 24): 'g'}, b)
    return c


# --------------------------------------------------------------- front ----
def extra_mirror(half):
    """Spans drawn for the left half (x <= 16), mirrored about the 16|17 seam."""
    rows = {}
    for y, segs in half.items():
        out = []
        for x0, x1 in segs:
            if x1 >= 16:
                out.append((x0, 33 - x0))
            else:
                out += [(x0, x1), (33 - x1, 33 - x0)]
        rows[y] = out
    return rows


def extra_sym(pixels):
    out = {}
    for (x, y), ch in pixels.items():
        out[(x, y)] = out[(33 - x, y)] = ch
    return out


EXTRA_HEAD_HALF = {
    # the left ear, flared out more than up, broad at its base
    8: [(7, 7)], 9: [(7, 9)], 10: [(7, 11)], 11: [(7, 12), (14, 16)],
    # the skull, no wider than the chest; the cheeks, the muzzle, the chin
    12: [(8, 16)], 13: [(9, 16)], 14: [(10, 16)], 15: [(12, 16)], 16: [(12, 16)],
    17: [(13, 16)], 18: [(13, 16)], 19: [(13, 16)],
}
EXTRA_FRONT_HALF = dict(EXTRA_HEAD_HALF)
EXTRA_FRONT_HALF.update({  # the neck, the rounded chest
    20: [(13, 16)], 21: [(12, 16)], 22: [(11, 16)], 23: [(11, 16)], 24: [(11, 16)], 25: [(11, 16)],
    26: [(11, 16)], 27: [(11, 16)], 28: [(12, 16)], 29: [(13, 16)],
})
EXTRA_BACK_HALF = dict(EXTRA_FRONT_HALF)
EXTRA_BACK_HALF.update({22: [(11, 16)], 23: [(10, 16)], 24: [(10, 16)], 25: [(10, 16)], 26: [(10, 16)],
                  27: [(10, 16)], 28: [(11, 16)], 29: [(12, 16)]})
EXTRA_EAR_INSIDE = extra_sym({(8, 10): 'P', (9, 10): 'P', (8, 11): 'P', (9, 11): 'P', (10, 11): 'P',
                  (11, 11): 'p', (9, 12): 'P', (10, 12): 'p', (11, 12): 'p', (10, 13): 'p', (11, 13): 'p'})

EXTRA_FRONT_FACE = extra_sym({
    # the eyes' lids; the tan under them
    (13, 13): 'K', (14, 13): 'K', (13, 16): 'r',
    # grey about the muzzle; the mouth; the white goatee
    (15, 17): 'g', (15, 18): 'G', (16, 18): 'K',
    (16, 19): 'W',
})
# the eyes, big and dark, the shine on the same side in both (light from the left)
EXTRA_FRONT_FACE.update({(13, 14): 'w', (14, 14): 'D', (13, 15): 'E', (14, 15): 'D',
                   (19, 14): 'w', (20, 14): 'D', (19, 15): 'E', (20, 15): 'D',
                   (16, 16): 'n', (17, 16): 'N', (16, 17): 'N', (17, 17): 'N'})
EXTRA_FRONT_TALK = {(16, 18): 'M', (17, 18): 'M', (16, 19): 'T', (17, 19): 'T', (15, 19): 'K', (18, 19): 'K',
              (16, 20): 'W', (17, 20): 'W'}  # the goatee pushed down under the open mouth


def extra_front_legs(c, step, b=0):
    lift = (0, 1, 0, -1)[step]
    for x0, dy in ((13, max(0, lift)), (18, max(0, -lift))):
        extra_spans(c, {y: [(x0, x0 + 2)] for y in range(27 + b, 38 - dy)})
        extra_spans(c, {38 - dy: [(x0 - 1, x0 + 2)] if x0 < 16 else [(x0, x0 + 3)]})


def extra_front(step=0, talking=False):
    """Facing the viewer: 34 x 40, feet on row 38. Walking bobs a row on
    steps 1 and 3, like the side."""
    c = Canvas(34, 40)
    b = 1 if step in (1, 3) else 0
    extra_front_legs(c, step, b)
    extra_spans(c, extra_mirror(EXTRA_FRONT_HALF), 'B', b)
    extra_outline(c)
    extra_paint(c, EXTRA_EAR_INSIDE, b)
    extra_paint(c, EXTRA_FRONT_FACE, b)
    if talking:
        extra_paint(c, EXTRA_FRONT_TALK, b)
    extra_gloss(c, ((15, 12, 'L'), (16, 12, 'l'), (17, 12, 'L'), (14, 12, 'L'),
                    (12, 23, 'L'), (12, 24, 'L'), (14, 32, 'L'), (14, 33, 'L')), b)
    extra_paint(c, {(16, 22): 'W', (17, 23): 'g'}, b)
    return c


# the tail seen from behind: up from the top of his rump, curled over to his
# right, its pale tip at the end, fur all round it
EXTRA_BACK_TAIL = [".KKK.",
             "KBLBK",
             "KBKWK",
             "KBK.K",
             ".KBK.",
             ".KBK.",
             "..B.."]


def extra_back(step=0):
    """Facing away: 34 x 40, feet on row 38."""
    c = Canvas(34, 40)
    b = 1 if step in (1, 3) else 0
    extra_front_legs(c, step, b)
    extra_spans(c, extra_mirror(EXTRA_BACK_HALF), 'B', b)
    extra_outline(c)
    extra_gloss(c, ((8, 9, 'L'), (9, 10, 'L'), (25, 9, 'L'), (24, 10, 'L'),
                    (15, 12, 'L'), (16, 12, 'l'), (17, 12, 'L'), (14, 12, 'L'),
                    (11, 24, 'L'), (11, 25, 'L'), (22, 24, 'L'), (22, 25, 'L')), b)
    # the nape, a short dark line; the tail curled up on the rump
    extra_paint(c, {(16, 19): 'b', (17, 19): 'b'}, b)
    for dy, row in enumerate(EXTRA_BACK_TAIL):
        for dx, ch in enumerate(row):
            if ch != '.':
                c.put(16 + dx, 21 + b + dy, ch)
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


for _name, _pixels in (('EXTRA_SIDE_FACE', EXTRA_SIDE_FACE), ('EXTRA_SIDE_TALK', EXTRA_SIDE_TALK),
                       ('EXTRA_EAR_INSIDE', EXTRA_EAR_INSIDE), ('EXTRA_FRONT_FACE', EXTRA_FRONT_FACE),
                       ('EXTRA_FRONT_TALK', EXTRA_FRONT_TALK)):
    assert set(_pixels.values()) <= set(EXTRA_COLOURS), _name
assert all(set(''.join(_rows)) <= set(EXTRA_COLOURS) | {'.'} for _rows in (EXTRA_SIDE_TAIL, EXTRA_BACK_TAIL))


# The custom characters (their number, name, the art, its colours, and how
# tall they stand against a person: Crispy and Extra are little dogs).
CUSTOM = [(1, 'Crispy', crispy, CRISPY_COLOURS, 0.3), (2, 'Suzy', suzy, SUZY_COLOURS, 0.95),
          (3, 'Extra', extra, EXTRA_COLOURS, 0.3 * 40 / 31),  # (drawn 31 rows tall in his 40: 0.3 of a person, as Crispy)
          (4, 'Sith Ewok', ewok, EWOK_COLOURS, 0.6 * 48 / 46)]  # (drawn 46 rows tall in 48: about 0.6 of a person, as an Ewok)


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
