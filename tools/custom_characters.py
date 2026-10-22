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

Suzy 3: Suzy at that detail (200 rows, 236 colours), from the user's picture
with her black sling bag; wider hips and a fuller, perky seat; 5'3".

Sith Ewok 2: the Sith Ewok at that detail from the user's three sheets, his
crossguard saber off until the L key lights it (both paws on the hilt as it
springs out, then carried lit in his right paw).
"""
import argparse
import base64
import gzip
import lzma
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


def svc(frames, colours, costume, glow=(), shine=(), trim=False):
    """The engine's character file: frames (dir, kind, index, canvas).
    Letters in `glow` are light added to what is behind them (mask 2), in
    `shine` drawn even in the dark (mask 3): a lit blade and its haze.
    Trimmed, each frame only as big as what is drawn in it (its feet where
    they were)."""
    letters = list(colours)
    number = {letter: i + 1 for i, letter in enumerate(letters)}
    palette = bytearray(768)
    for i, letter in enumerate(letters):
        palette[(i + 1) * 3:(i + 1) * 3 + 3] = bytes(colours[letter])
    out = bytearray(b'SVC1') + struct.pack('<HH', costume, len(frames)) + palette
    for d, kind, index, canvas in frames:
        w, h = canvas.width, canvas.height
        x0, y0 = 0, 0
        if trim:
            rows = [y for y in range(h) if any(ch != ' ' for ch in canvas.cells[y])]
            cols = [x for x in range(w) if any(canvas.cells[y][x] != ' ' for y in rows)]
            x0, y0, w, h = cols[0], rows[0], cols[-1] - cols[0] + 1, rows[-1] - rows[0] + 1
        pixels = bytearray(w * h)
        mask = bytearray(w * h)
        for y in range(h):
            for x in range(w):
                ch = canvas.cells[y + y0][x + x0]
                if ch != ' ':
                    pixels[y * w + x] = number[ch]
                    mask[y * w + x] = 2 if ch in glow else 3 if ch in shine else 1
        # (The feet at the canvas's bottom row's middle.)
        out += struct.pack('<BBBBhhHH', d, kind, index, 0, x0 - canvas.width // 2, y0 - (canvas.height - 1), w, h) + pixels + mask
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
    ('front', 0, False): (72, 96, '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'),
    ('side', 0, True): (104, 96, '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'),
    ('front', 0, True): (72, 96, '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'),
    ('back', 0, False): (72, 96, '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'),
    ('side', 1, False): (104, 96, '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'),
    ('front', 1, False): (72, 96, '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'),
    ('side', 1, True): (104, 96, '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'),
    ('front', 1, True): (72, 96, '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'),
    ('back', 1, False): (72, 96, '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'),
    ('side', 2, False): (104, 96, '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'),
    ('front', 2, False): (72, 96, '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'),
    ('side', 2, True): (104, 96, 'eNrNmYtb0tnWx1EJFQVFRRRBQQRFvMRFUogiK2YYX9G8jI1RmpSmJmpes0kzlcrU1E41k5mCdnnV8DZ2sYsaSZ05c46mqIj1Tq/nUho1509490+zPOdVrKfpec56EB+F3/78vmutvfba+weD/Sfb9CMTHz6a+d0wF4/ErPph6ZHe6d8LUxzVu9pNz/5UefTC7wIyNJ0tjlrdcdMNRdE//A6gZ7fOFhdHPVz9NjqqYiIffT7nydk/mObcqCuLOP/k893W0H20KGL1Gzbc6ao5HPPo893W0F1XFH5+1YEM/V01seHnPzdCI5cv3wGcmIcm9IDPC3tmPzc8nWfrigqj3+mZffLBluR01RaHF1w3fCanTl1Xe6Ig/CQY9tm04aczZ8+ePXOmpubMmTNPpt/AYP+rVncATlTT78GpLY4oeDT77NbFy/XRBQUFhYUFhQVRUSUXh54Z+t5xPlvPWXVtXV0pGPXWg4bThafqvy86FrFjR2Tkjh1RUTFNTbfU6v+uLQJ6PjMRRhrVHfX15VFRUT801tXX1BUXFR692NTT03P9YoNCUVgQ299fV1sYVfDjGjNobM3i1tXfUFdXXFAQc6+2rqqoqOTiRZ1xwV48HGo4Ex1Tdq+mMCrqjCmORqOVblorrxv6u+rq6o4XnrlVWxhz5PzQc+PbjNTU9IyMOaNxTt/bVFrSVFIQNfTGBCaAxcIm6UzraTqr7u6oqa8/NXDne0XP6NSc8dAGFp1Go1GpAdxNiW+NxqGSywVHTIQnL4Bkb48fXtNx6i4QorNNP1061gswmZvFXLKdDQZjT/XlMmiipLfGk4dPmpCTF+CIsXfIXTMTZn/u71b3P7jeUtM79UIjDeYT7e2skeYW6+xIJCKOSGKPTh4pmjbhNHsMBvcRmJv3Bu/+8svd5pKeiVfPpZJgMomAsrZeZ2GBsiGibBwxFJq8t+ikZlUMFW2P8c9bm9PV1Tdw+17DkQujU6nJEg4OY4+xt7bGYCwQNihzB3MHOxpr40YPBxc3r5UwTD+MvT11bcybP3aq1eobjQ0XJiYypMEbPHHWkCEQVFsLC1tzW1uUNfAfjp238lBjEkcMxtct7yPqdWOHWllff3JiakIqDkLj8QSCjbW5mZkNFXAwFigMAm5mZuZAoKw4lobpYG9Pz/uIenC1seFGxYmSoYmpVAnDh+KOMjd38HK1NUdS7NDryOswBATAmJm7sV3cVuIEOdjbfYTbYE8aG08rog/3jP6akSRhBAe5Q6Oaebm6mqEINuuYpAACwmG9mRkt0CoHhl6J4+hg/9GcHbH5o3MHpQIB3dvcDL0+Lm69a6gXGk+j4UlB1pYhaa/Mzf8hs4LBXP/9ai8Nn4Gx9/mI8CiVXY2KmAujrw4eFAvodHNzF9d9xrm5uFB/qrc3B4sPorhnr5+aM0cOY1e4nEoX0u3tvdfmPAGcrsqYXv3cQXGmj4+5OcEn7R9yedZcwrZt3t5ULCHIZ59cn/syJWUStkJ8crE+dAfMR+TBk2aluuv0yaEXv0IchBklICs/xbgv3fjrdzu9vSlYJCEoUzb18mVq6socPD3Az5H+UX7rVLedmTIelIUdYlDEYon8132Zma+M2Xvi6d4uFuh1+C1yozF7586nKxc3uoiFWZ4HTGYebKEIjSw2GbPPFjkqpfJGZ7Vee1BG1zAlEglVnPU25YVxane8yBe7Dm1rbm4RaHwZl5AwsSJHKxYz/zXhmNRcF+xCfjU0XLp06d7A7CxgPRsAAbpRo884uN3z8VaJZDOWuSfLaMzfL9kQACaqhQUc/Jj7o/1XqWBg6QnwWeJs2Jibm0ugYbFuudM/1NTUVAOrv3Pv/v3bs7MGlaqrq0l/MElI1SWJBPSAAOaetLQUsZhisWjIQCBpVU5eQIAILFYUyFWavGAsnoBzdsblTvcoaquqqhdQtbW1/XfvGq4CTp/+YCKFoJOJKFgUWSwWiYA3SAQ02sLC/6udO78Dv22xK8dnPFEoBiA8Njc3j4nDY/F4PA5HyDNcCQ8PPwZBqqqraqu6B+7evKrqvg44Ik/Jw6SNWBukH1OcmLidEsDEOsDN0YG7Ekb1OTlxluuz9q1cSMPEYg4d600gODnjnAl4BoPhFzh2s6v5XGlMdGk5EFPVcKe/v7P/l2uq7ptTYdSNmQ83URytrbGUrUKhO8Xd3QE4bdPOtOwsyNaj0Xn5K4KeSsTiYLovDueMI/K4OGc8Fps306W+oe76sSY8MjYyIrL+av9AZ/efrzcrb05slR58KRbZIiytrK0pFDwe6wKHwy28QrL0+qxQM7P1L7bBt61fETSZCjh8AQtHZLJwkOFdng7dgKy7H9jl+rP1nYN3uroHf1Yq+4YOJhszRXR3SzQCLD6WLj50OwcHuFtcnPFFVpY+JyvrRb4F+rHriqDxb8CskwT50gh4LJHI5/PzDNfbWlvb2sBba7sagv3c2NzR/+qBqrPvf4xGmZBKpeARCEsbb7qPjw8GbgFHx6W80INOLusFqKSuofnylT33nUQs5HkTnPEsDoHFCtIY+tra6hWK05UKRSUAqgcGFYr2rtt/udnY9VejMVHIoVGxKCsHB+8N2QlIVzBz0IFx2flZo/pR41OwtK5aXZ6KhAQckc7gcpzwLD+mZrapsqJCoaiATKGo7h/oVlRUqvsH/96nfDBnzAgTMqlULJaSLY9Dh2ZnmYM8QLD3pY2O5sxngUmEXrV3mkxl4PyI3jycE57JYmne/FF5WgFhoBeQ1D/QUa6obO+/9/PIne7BObAASbdLNrrvckB7JSQgLMzB/LRwC40DGTcRAsTtsl1Nj3Yzw4/M4Tg74TisYKbGADILYMrAC+IoTj3oBH9WdvQPDP6l786Dv2VkJkq3b6eg0V773UGyrXcFMQkJCY1LeJETh0bZDlu5rcLZHMxgCVkkJ2cOh8NnaqYryhWKulOtrdULehSK7m5IWXV7/+DPfwaK5g8kS7e6uLgEpvm728Jd3dYh4G/eWVqgKxIG81+1V2T48ZlEMo9GY/GDdb3Hy8GwlVAWANeVVyg6+8sUlR2Kqs6Bgb/+/bz6T5lCHxeHkBB/HyoavQ/t4pX15r2hc0NcV+VohUIhnYBnEXA8hkDz6FR5GZQBC28VNWUV5apBdYWio7u65t79gZe3z1/3csH6e4X4+2Nd1idYfbVp2z4A+O233yCOV95KXciSHIGAiMezSByuh0CgmW5aZJRB7/VtquPlZV0P2o41qu+qf3wwcPvtn/4r9CuXDWwvL7fALXHIALcANjvw7VvA+e3tWxf3vP/fhLzHcHhkIpFDxnLBJOVr3gyVAasoKysvL6tvaW1VlJWfbm0vvXSpExSIvj4m68KQV1qCV4hX4C62f1AQ2xWqPPC3//wnwJhqOIe3AIfhOB443CJHN116qgYEvrwcKgitrVeulJVWtpeW1p07d63vJJd7+wF7OCvUK94/iB0Y588OQsDZgYFsdkiIA2iC2CZ2WSwSARQcqIpyORzW1uHZB4OD9xv77rW2ADXgre3csdLjx44eO1ZV/e23Pb2pAhfNthSv/NCE0AT/AHYAO8Td340ClhQ3f7fckNU5G+g0HJEI2uVFjkj77PbA4MCtW9euLMhpbas9ChjHjpW0tHZ1qTs7jpR8q2Vv8tf/+ipETmHuZMdtCL7gG04hxd5KcTXFgeWRyRwPIoHgDaYPRyTSvjG0tkE6WgGopa26+uiiHSuNVrSqa2qrzj/WinwkM/Pz86+95JvmsrZsvHrlW5fY8AfbTPdNGhKZ50HEEQhcjgePL9bqRgAEuAx6gQK0AImIiIisVIBZdaqtrccwJgU2//r1vH/OhrcJYbq2HyixkeH3pSY37cObBTwc6AtwHhxPPo8nFmsNXe1QZFqbqxWLmMjI2HPNjUpVW5uqrfWaYUwCMBNT2fPz/klb9363fbLJnVIDvnbS5KmYBgxOJHDBCkcWCPgcsXhs2qCGMHe7zpTGxO6IjixpaGwE4JqaI5XKRTWSzVK9UDo6LxEJhaK00Mbw2JqIgoIS05zgA1wPHqijOA6J780X8GU6w50fBu62lpZGQscqdTWqFigllLExMUcuXzM8HpMIeFz9hDARcIRCv+3jut6SHd/HhIcfNslhZ2RwGHwClwtyG4ejcQHn0bcD98vKYiIhUywmN8BER0fXXzXMjkmEPD5/Pv4b/et5Pd3bm62ZMVypiQGccNPHlk89yUygCMpuEg7HFwM91zuAkugdse0dKlXLYqwA5riqZWhmXCvk87j8V88n5uf1em9vDC3vzUhr67no8PCIUyYF5dH4HByPBqUcHDQIXyfpZnqutrd3dFy71tEBMMA6rh6OiYmuB5gxCMPjcSRQuvnoHTGOjrnaEZVKeS4iPDz2ockABfHIHjwimEEEW4wNTSRLnzR0tEMG/KWCrPU6iM3JhqtDM1qt2JfL4zE8fZnz81SqfhJw8LkjSvCd6ogI05wQDYflQabxSESinY2NDcSZ6VUp29vrVS2tjcoqZduVWDDOlVtAjWYjhsUgkj09ybj5eTRd/xppgyFpZnuUtbWt5yIiHpre3Wi4BIKQQ3TE2Ngirb6WT8JgM7dUqrpmpfKcsrIisj+2uU2l6pkBGIGzNRJDJGEwyND5eYy3ft4SDidJxwyq4qITJw6Hr8Xhk4lCJx8MUIPAJ+U/h85VL6suNTefAytrReyNNpVSNTTzWKvh+tpYO9qgCJZWVlNGI8Z6NCcHjvAQaEZUJwoKiop2HDGdCAF8PyEPh0I5IBEIz2QgJxvyXDNYGoCVNYK14fo0yAABaFWQ1kirBQMce2Q+4FiR+ZqRlhOFBUXl0YdNCtoUvIXH9/VAoZBwuC0L2ljkpE3OXqxTKE5UKC81t1zp6Z15DPKZDCGQCy8rK1BGUTb5o/lWSA8yZay39kRh4YmjhQ/XiA9LAOSg7OFwIlMDgz3PSU+bHGqEUk2pVF0cmpl5PJb4ta8NEg0aeKQVEmkOd52fd0WhRkdHrawI7lTg5tqCguNrcWCazUK8HQqFQCBI24YBJz9TPjXTBHFaeg3TMzrtmETCc7JxAn4FoUFaA87reZSd3dPRfEtn6PjB0FRbEHWieG0Oww5w4HArCAPT7ZfLs6ame1p6pkegB0s60OiLRCJfJ2c7S4yllaWVBcH1tRFcAfTYMrZrAafnUnF0cXnRWs8xNAzMAoe0cE43uVe+ABpZPPTOz0wSCPkeHjRHpOUCBx3ogvWaAxek6PPzGTlQfub01pXuiFxLDyzP19cOZW2JDYCWxCl5ihyyyXcfynMl2wVEDw+Q1NZI4Dp/tgsWi8faoLB79KPZ0r0LJ7gzPaU7ItbkaBi+dpaWHsSFlXcqM/OAXJ6cfGAJBNMdEuC4OBoSA+2urPeFYF1csHgUSip9MSpbxMDeDJ3//iM4Yoa9IwIftOi2dHmyXCZLfn/SnHxoTMRncWlYBMgBa5c9yVvwCf5e2dkSycSobP+7r705VB1xZI345NGlYg8PIv5dIzG5XybPkO0Z/7BGMclgzaHZ2YK0ts1MlYHmmp39t7AwyaFRmWzpdmaaFGvlQZ6flA8CTXy3Q5qSyzLkyYnjy/QGbuc6OjpCkxQ5njm+fn9gSu7e+CSxOFX8Qfb0j4q13MZM5HM9SKQlPWnJ8v279+r+pQRynZydbKytEFY5U7DhXcOT2ZlywBGHLbub3gtrnUdpNgNBLPJ7kDz9gDR+bDlGIBR4OoHERsBzoDUYzGW5bIHz9JOeu2ilfIGn3ZLjJtPTD8jil93p3nSZ0JfjiLEEBSFn8V/P5Yt6tJ/EGU8UgkZkiQOBZLKUZY7T7RHwmRh7Swck8h0HNjWVKZOIN278NNCYiEN8H6BF0O79yxRpuXgsA2NpZ/2eA+aZTCwQCOLHPslxIg7Jg/yBk5GevFu6e3xZTefRMI6gIqA/bNsnkyDOp3lOGyb0I5OXjZGWmiTdvV/3viZood2RjQ0G8+E7ur1hgCPcMvxJILEfBoPP/XCokJqauHv3nnTd0hMCvsjJ0Q6L5ix7JDIuEXOYFGpe3idxWGQ7qga2FPzs9AXb/c53w1sy+HwyiURa/gBhLF4SRHF39/HRfDznaZhQIHEUBbyvIyAV0rPTU5f+1gjEIr9/40ympYVJJFxh5lbZx3O+EWzOxNHjg1OWQjKVk5qak7Z/KRE2cgUsEtmTttxJUznJMsmWrdnJKZ8gaOfebKlAy/xwyfPJyeeTy/blYgHoEGn/4qPnOt3YsPb5J02hp7p9ezfDNKtvzAU8Ho1H++bTKs1KpjP5cHMYbKqgvbIG9mVNK+b4ga0ylf2FQU/jGUwRi0Vy2qT9sqBhBkMs8xDs9o5/+mUdt124O5MlyAhavtR+Ec8lJubs2qzbr/vCmQAbH38+/qE0/efY/wFA4+Kz'),
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
        'eNrtmv1XE1caxzklzgzOhRmCERpeBKPc8CJKQgKRLERIQkMgYAWCWU8CZsvCYYFuLMEFyVnqQYw2'
        'lbSgrgo4Si2UttBulxXpadUqCnRri7baFovrWavt/hHuTYIKgjRJSX/aGw55O9zPfJ+3+9y5PHz4'
        '/7HIgPA34tjgb6EBWnzHgbYnc/uU02GwzUqC1rSjvuMcPbvbJQlatlX2+pAzcWF3nAMEraoDPuT0'
        'Tt24cCAe2c6yfeOHn/iSM33j/IFUm7UwKnziki85M9NT53e/sCEmnDcx6TvOyNTM/empsy9uDyDx'
        '8zd85iCk59/3Z25NHE95GWOdn/JlvM3cdwoyJvnt9qHdeiemHaBrL8YVBPinWH1mt86Pv/sP4pzf'
        'jUepsl96CQW4T1DwxOSt+zNTt64dwInkZMQ5dszqExL8+P70rYmpqS14aWq4zKgr/Ivt2N+gLwz3'
        'zcy1qVtTx0GZMUu2o7AwKSP9JR+AYO/pb27cOnsthZtUIEoqbjIm0RHJhcsPgh9Mfjc9fXY3nqST'
        'xae9UFocgbPik9KXfSWC3efvz0wf5xCywg1UafFmPo6DmFdUwcsPYlovTCixrB0yUZKqIIKkk38P'
        'RZvZy7+0wp6yPVSwThefpFIhTGF6RHw4K7h9+TmdcaV1m3XJlCxdlcZOTt5z7nRdqswHetpZvDKj'
        'Lo2ISVYlJRXU3fnve8ftpT7hYKkFMpLGSQokxR+//r16y+my5GWvQNCKs3hpqg2Ay6PZLKL1o9Nb'
        'Kk+XEeE2mwO1fCxoI3G6dEfBhrLmPaqo4PDjH314WpOWnC6TFXTYbP/8BRJ091pgQzaJ+/NVu3Qy'
        '5uMaGcUi+PyIHWnJG0prDh1R615ZMvBQ+1JfX+9W5YX1uZGUP6+gRpdax+hU8WwMD0nWbWCzNTWv'
        'vd9XdgIufZElFbU7/9zuFkcSw2Fxsow6DUdZui5GptMZCwKixsdrdvW9//4eZkk5jWZzXnQ045ae'
        'xvJ0DovFN8rSSJLEKZnGaKwZT01OQ3qG+vqXxFhbyv9EY4w7/oEWsyR9HemH8dQ5IpwkRfGlbx55'
        '7ciRU0NDFy9e7FkSY6kt/10IzrgXBhZ9kSCVQiAO32DIMRjLyvYMvXbk1Km+oaFPr/6Cc0x50W5i'
        'kHvEEkEcoIGfH87j8g0FBk3aF19//f2dHx88eLCk3WGFvmgl6HET02BWrBDIaDYNMMyfJxLliFK4'
        '43B2LP2ntfq8AKLTXTlmsWS9rEsUiEiAQ5EYj++uJRpKqtmg3U3v1OqDBMIXtNoUQNNsEB7OFbmJ'
        'eQj3Joq4VLt7wWYy1wrY26qoSgOgaDpHbWx2F4M4Ei2udaMjR0Wj0ZyfqeBEZxtwPjIbHq757EqP'
        '25xXt9lZlW/BxQreHO9C2GApNxVlS8NA8MaDlTyHewxXbp5zu0DDTmEVpX2aAy0WS4PFOVy0hgbx'
        'pnpz0coAAAB7e7OSpnjKum9vu895CA+JiRx7B5ynxFLbaDKZ2tCP2WK1WiyNphJhUL5JHoYDQABK'
        'qwWk4eCVO/f6POI08/knO1wWQoi2tjZzkUScm5cgzJXnKSrQW5M+d9OKfIXUtFXAoZHJaPRbGXfv'
        'p6udHnBOJBQCjrbJZnXap76ipaI8XxIbuTFBIIhNyNXvLDftLC/aFIXlhq3Sl1dtF/GAc6g/uHvv'
        'M0/WT3hYvJ7AtcUJVmShRmSrIqEwlANCYqWCdYn5+q1FenleBBsQQolEUdtQZddyAQikQdPg1bs9'
        'Hq3TkBEGIVsQgMhuaWmUB2+KpdDbtbEgSpIrX7FSLo/mUDRByEv0RNi+sS57K4mylBPHKrvqYTsA'
        'GQYZAiN2tpgzE+XChBj0jg5mh8SGRpAbhfIYNpo3MFKxVYGHFneP/t1eh0zHAaJzpzzlQMjgGEvS'
        '1pIbHbpNGktRdKCjsNBU8Dq5VOBQR68WZCYGBEmEKSMj/XYtHwDewc+96EIhwwJtbZI1YkVVuGNa'
        'Cj0QKVQgWEdRDrcn5IqDcEkChueMjF2yGzhA+cldb7pd2F3RsnOVeFtVMZsIpJGfKYckBAR0IEWR'
        'kRKxYHWwNDQUI3mi10fPiJo//+HnKx1eCNrbZtqpyH25DqmhaEeZRCKQAZ0xTIGNYjEAIVJpFc0B'
        'wPDuB2++c/3eg6/e8oLTYC7KzP1jBJo1MBBBnBxnTjp9FZIgQa+JzPp9dh5O4qdu3rz980/3rnjM'
        'gZaKFoV0kyvbkbGAwykOXU516ClqE/ogWFLecbIyRwnKzt1GK/VNz2+8wEaTPjuWmLUSILl8Dnqm'
        'KKcJgePhkBckLTo2eNJu5/AM13948POVTk850NpYIQ9xUgKdFlPaeY4wcMwfOGtAx5NAkT822IUS'
        'lTR8/eD2255zGs0VayWxpGMuZCnS0Nwl4qAXBHJWIJgdJEGsXps/NjZi59H49bs/vs14brY2U4k8'
        'lu2aj5vS1TUwPGxXupIIaXGGOIG+xoV7xy4Najn489/e/ZbnBQct/JLQ2ctOqbxweXJy8vKAkuNK'
        'IWdsAHYkqoHZtrHBVgrHK2/fPMd4EdW1LYqNnNAQFMMgZWByspXjh9kvXx62k6TTTShvsdwEkk7c'
        'd6lLSRL+mq9uvtfjTTVoaKkNC5DH0uB55fDlgUruc8+x+Eqmv79VySNdweYnFtOBf9h3Rsmj8Jx3'
        'rr9n6PZCjnVVm2lN2Ho2wLVdwwNbnmOhXGQxjvrKaEnAQzUArCjJXBGw71BdChfQb3/5JZvs9IJz'
        'gjGX5MnXk4A/MMxlZofzfjgi2e1KpYgVlr8mUny4GrMzTP+X/5r92uPjCUt9rUIRC0StAwwzv6Vy'
        'kJgc4L9KuFUhyVHW9UO3+ulnBkKbPCEc1HUNQ6gmcDQyHk/kMJ9fokJSLUjA7f1QxRXRLJDh3dYa'
        'ldGtkWiV7EGTZoXQiKOC85anTGmCP2lAGJju54fhXJ2XnPqiMEdcdTsMkh2KOJp5E8E3ghOz7V3v'
        'OL5W4xhqRlXegKBVLw4DKFnQhhlKs+JwgpU1n/Pqqm37Bk86cgZqcJxvqPZKEFoW1qBi7dzWQUkq'
        'F2ep4dPbCtnopS5nLCNB3Lr9Rq84e/PDCAI4MRnb2RimXtBwS+mxEdd+Ggkimg96ZzdTfiztUiNd'
        'u1CNg6M+ODY4W2oQ6PXDXgUcrBUSLkzGqrXYQgzihL4+dubRJiULqz7jjR5Ynzm75YaSxDB8EUy7'
        'cMXg2KPKCWW4xhuOI9pI1yQwOwzTwMVOMLCR0Sd7F0344MtecOr1bOAqv1AXh8kW43RyRt59wsnS'
        'Ht7vzeqjB8BVfmEBF09fjGNVDj4p0FBmaK7xpnczYY9CSYZji3NK5x7HwWavOK/mr+58xAHYIhEL'
        'raRhZC7HeEbreSDANzKT3ngUS6WcxTg2PjO3KYQ6A9+LBIKd1Ucfc/iLCIIdB0eOztOTw/WG09t7'
        '6HFu5LAXzACthnfH5u5CYLGWKyr03HC25sd3uh1lP+Op1RJacs6MzO0HUEXg1TV57CHYoH18pgc1'
        'GFpMq+ZdLDyK85vn9R1QDZq6mzI8W7+hRRxgnZMcMcV7Vg/tmnv57VrDU+0aVIuamsIzMqr+usv9'
        'ey+WKtEcjlpTfa7MCOdxmNGnbxmjNoKoNoY09bq/64Z7i3ks6+P+ZmE3Ay3/GO1dwMHi9u+/vnnz'
        'px5wglh+xR3PPnaFltGRBXtRqFYbqvvK1B74pyIzen9W7zh8Zj0XNNUt3It63MbBhi9W3rmYdudZ'
        '+3RoCfN/nvr1p8zw0BcB348zh5+pp6E+dH/3Mhxawdlm91nlL2t8KGI06q1ff7qztJUhM3SK+fHT'
        'Pp//o9Ov6dx9P/4HesZoOQ=='
    ),
    ('front', 1, False): (72, 96,
        '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'
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


# --------------------------------------------------------------- Suzy 3 ----

# Suzy 3: Suzy at Curse of Monkey Island's detail (SCUMM v8: 200 rows, 236
# colours), by an artist panel from the user's picture: the front sampled from
# it (the hips, thighs and seat widened as the user asked, "she has wider hips
# and a bigger butt than that"); the side and back painted to match in its
# tones, then redrawn at the user's word ("Suzy 3's butt sags too much. It's
# perkier than that. For her eyes, keep in mind she's Asian"): a full, round,
# lifted seat, fullest just under the waistband; in profile a narrow almond
# eye in a smiling squint, a soft low nose bridge, a round cheek. Long dark
# hair with grey streaks, the green bat T-shirt, the black sling bag on its
# strap, faded jeans, grey sneakers. About 5'3" (0.9 of a person). The
# picture is not kept or read here: every frame is baked as palette indices
# (zlib + base64, 0 = transparent) and decoded when drawn. 104 x 200, the hair
# from row 2, the soles' lowest row 198.

SUZY3_W3, SUZY3_H3 = 104, 200

SUZY3_COLOURS = {
    chr(0x100): (32, 29, 38),
    chr(0x101): (92, 118, 167),
    chr(0x102): (58, 88, 141),
    chr(0x103): (212, 115, 58),
    chr(0x104): (43, 113, 59),
    chr(0x105): (89, 185, 97),
    chr(0x106): (45, 71, 122),
    chr(0x107): (165, 83, 42),
    chr(0x108): (110, 100, 101),
    chr(0x109): (74, 166, 86),
    chr(0x10a): (254, 158, 83),
    chr(0x10b): (67, 38, 24),
    chr(0x10c): (248, 248, 248),
    chr(0x10d): (56, 138, 73),
    chr(0x10e): (29, 20, 21),
    chr(0x10f): (7, 3, 5),
    chr(0x110): (162, 133, 124),
    chr(0x111): (64, 62, 65),
    chr(0x112): (3, 77, 4),
    chr(0x113): (59, 47, 47),
    chr(0x114): (128, 53, 25),
    chr(0x115): (246, 143, 73),
    chr(0x116): (150, 211, 150),
    chr(0x117): (192, 190, 202),
    chr(0x118): (7, 10, 25),
    chr(0x119): (73, 61, 61),
    chr(0x11a): (60, 91, 145),
    chr(0x11b): (27, 45, 87),
    chr(0x11c): (54, 78, 126),
    chr(0x11d): (119, 138, 177),
    chr(0x11e): (28, 14, 14),
    chr(0x11f): (16, 15, 15),
    chr(0x120): (174, 172, 184),
    chr(0x121): (47, 36, 35),
    chr(0x122): (70, 101, 154),
    chr(0x123): (187, 224, 185),
    chr(0x124): (21, 58, 31),
    chr(0x125): (83, 111, 162),
    chr(0x126): (221, 220, 228),
    chr(0x127): (187, 132, 96),
    chr(0x128): (24, 21, 30),
    chr(0x129): (98, 35, 20),
    chr(0x12a): (124, 100, 93),
    chr(0x12b): (38, 29, 30),
    chr(0x12c): (187, 93, 48),
    chr(0x12d): (24, 40, 80),
    chr(0x12e): (84, 51, 32),
    chr(0x12f): (80, 143, 80),
    chr(0x130): (21, 36, 72),
    chr(0x131): (26, 18, 19),
    chr(0x132): (22, 102, 24),
    chr(0x133): (137, 208, 132),
    chr(0x134): (112, 88, 81),
    chr(0x135): (33, 54, 100),
    chr(0x136): (92, 81, 81),
    chr(0x137): (50, 126, 67),
    chr(0x138): (211, 210, 219),
    chr(0x139): (30, 91, 48),
    chr(0x13a): (20, 13, 15),
    chr(0x13b): (82, 71, 71),
    chr(0x13c): (122, 75, 52),
    chr(0x13d): (48, 45, 48),
    chr(0x13e): (67, 156, 82),
    chr(0x13f): (181, 100, 52),
    chr(0x140): (234, 128, 66),
    chr(0x141): (131, 172, 127),
    chr(0x142): (136, 133, 144),
    chr(0x143): (125, 142, 179),
    chr(0x144): (109, 199, 108),
    chr(0x145): (15, 26, 57),
    chr(0x146): (68, 56, 56),
    chr(0x147): (41, 65, 114),
    chr(0x148): (50, 81, 52),
    chr(0x149): (46, 69, 114),
    chr(0x14a): (101, 155, 100),
    chr(0x14b): (171, 119, 66),
    chr(0x14c): (169, 217, 168),
    chr(0x14d): (63, 52, 52),
    chr(0x14e): (58, 57, 59),
    chr(0x14f): (57, 39, 37),
    chr(0x150): (84, 179, 93),
    chr(0x151): (33, 39, 28),
    chr(0x152): (242, 139, 71),
    chr(0x153): (16, 89, 17),
    chr(0x154): (25, 71, 36),
    chr(0x155): (201, 224, 194),
    chr(0x156): (48, 74, 124),
    chr(0x157): (66, 97, 152),
    chr(0x158): (253, 152, 77),
    chr(0x159): (3, 106, 3),
    chr(0x15a): (78, 66, 65),
    chr(0x15b): (143, 93, 50),
    chr(0x15c): (27, 24, 34),
    chr(0x15d): (100, 195, 103),
    chr(0x15e): (20, 16, 20),
    chr(0x15f): (210, 107, 73),
    chr(0x160): (46, 73, 127),
    chr(0x161): (15, 29, 17),
    chr(0x162): (27, 6, 4),
    chr(0x163): (51, 27, 21),
    chr(0x164): (95, 98, 54),
    chr(0x165): (45, 40, 42),
    chr(0x166): (102, 126, 171),
    chr(0x167): (40, 106, 57),
    chr(0x168): (49, 76, 129),
    chr(0x169): (87, 115, 165),
    chr(0x16a): (159, 183, 154),
    chr(0x16b): (22, 18, 26),
    chr(0x16c): (59, 144, 76),
    chr(0x16d): (248, 132, 73),
    chr(0x16e): (50, 81, 139),
    chr(0x16f): (90, 67, 62),
    chr(0x170): (50, 99, 52),
    chr(0x171): (55, 85, 139),
    chr(0x172): (185, 156, 145),
    chr(0x173): (89, 76, 75),
    chr(0x174): (194, 98, 50),
    chr(0x175): (245, 240, 231),
    chr(0x176): (255, 170, 97),
    chr(0x177): (97, 87, 86),
    chr(0x178): (151, 73, 37),
    chr(0x179): (23, 21, 21),
    chr(0x17a): (15, 4, 4),
    chr(0x17b): (201, 197, 178),
    chr(0x17c): (107, 69, 42),
    chr(0x17d): (70, 161, 84),
    chr(0x17e): (33, 56, 35),
    chr(0x17f): (201, 93, 51),
    chr(0x180): (45, 64, 104),
    chr(0x181): (40, 66, 40),
    chr(0x182): (127, 122, 123),
    chr(0x183): (56, 21, 9),
    chr(0x184): (42, 23, 18),
    chr(0x185): (72, 97, 144),
    chr(0x186): (35, 26, 26),
    chr(0x187): (67, 48, 45),
    chr(0x188): (175, 90, 45),
    chr(0x189): (13, 22, 47),
    chr(0x18a): (29, 82, 42),
    chr(0x18b): (38, 90, 47),
    chr(0x18c): (35, 18, 16),
    chr(0x18d): (202, 200, 210),
    chr(0x18e): (96, 122, 170),
    chr(0x18f): (184, 182, 193),
    chr(0x190): (24, 26, 20),
    chr(0x191): (221, 121, 62),
    chr(0x192): (14, 9, 11),
    chr(0x193): (195, 107, 54),
    chr(0x194): (122, 134, 77),
    chr(0x195): (45, 9, 5),
    chr(0x196): (27, 25, 26),
    chr(0x197): (106, 48, 24),
    chr(0x198): (78, 103, 151),
    chr(0x199): (222, 210, 194),
    chr(0x19a): (90, 110, 153),
    chr(0x19b): (218, 106, 57),
    chr(0x19c): (23, 16, 17),
    chr(0x19d): (43, 68, 119),
    chr(0x19e): (36, 33, 35),
    chr(0x19f): (46, 120, 64),
    chr(0x1a0): (63, 150, 79),
    chr(0x1a1): (203, 159, 99),
    chr(0x1a2): (162, 67, 38),
    chr(0x1a3): (62, 83, 128),
    chr(0x1a4): (107, 129, 173),
    chr(0x1a5): (104, 93, 93),
    chr(0x1a6): (28, 47, 30),
    chr(0x1a7): (32, 29, 30),
    chr(0x1a8): (78, 108, 160),
    chr(0x1a9): (151, 149, 158),
    chr(0x1aa): (38, 51, 74),
    chr(0x1ab): (31, 50, 94),
    chr(0x1ac): (43, 32, 33),
    chr(0x1ad): (124, 203, 118),
    chr(0x1ae): (52, 132, 70),
    chr(0x1af): (255, 163, 87),
    chr(0x1b0): (72, 89, 128),
    chr(0x1b1): (124, 59, 31),
    chr(0x1b2): (250, 147, 76),
    chr(0x1b3): (5, 8, 13),
    chr(0x1b4): (16, 42, 22),
    chr(0x1b5): (250, 153, 81),
    chr(0x1b6): (77, 56, 53),
    chr(0x1b7): (77, 26, 13),
    chr(0x1b8): (64, 94, 148),
    chr(0x1b9): (65, 90, 139),
    chr(0x1ba): (66, 127, 69),
    chr(0x1bb): (10, 6, 8),
    chr(0x1bc): (60, 30, 20),
    chr(0x1bd): (84, 40, 21),
    chr(0x1be): (204, 102, 53),
    chr(0x1bf): (10, 16, 38),
    chr(0x1c0): (31, 106, 34),
    chr(0x1c1): (139, 65, 32),
    chr(0x1c2): (36, 58, 105),
    chr(0x1c3): (187, 85, 47),
    chr(0x1c4): (51, 79, 132),
    chr(0x1c5): (74, 104, 158),
    chr(0x1c6): (207, 109, 55),
    chr(0x1c7): (176, 80, 42),
    chr(0x1c8): (19, 31, 63),
    chr(0x1c9): (221, 115, 60),
    chr(0x1ca): (113, 134, 175),
    chr(0x1cb): (144, 118, 109),
    chr(0x1cc): (36, 99, 53),
    chr(0x1cd): (41, 37, 39),
    chr(0x1ce): (66, 75, 36),
    chr(0x1cf): (3, 92, 3),
    chr(0x1d0): (77, 172, 89),
    chr(0x1d1): (51, 40, 40),
    chr(0x1d2): (71, 70, 73),
    chr(0x1d3): (55, 33, 24),
    chr(0x1d4): (117, 108, 109),
    chr(0x1d5): (229, 228, 232),
    chr(0x1d6): (56, 73, 113),
    chr(0x1d7): (38, 61, 111),
    chr(0x1d8): (72, 105, 69),
    chr(0x1d9): (163, 161, 171),
    chr(0x1da): (218, 135, 73),
    chr(0x1db): (55, 43, 43),
    chr(0x1dc): (3, 1, 3),
    chr(0x1dd): (233, 117, 63),
    chr(0x1de): (54, 82, 134),
    chr(0x1df): (98, 59, 38),
    chr(0x1e0): (237, 134, 69),
    chr(0x1e1): (93, 193, 99),
    chr(0x1e2): (53, 52, 31),
    chr(0x1e3): (27, 34, 24),
    chr(0x1e4): (44, 29, 28),
    chr(0x1e5): (32, 23, 24),
    chr(0x1e6): (77, 45, 30),
    chr(0x1e7): (14, 73, 17),
    chr(0x1e8): (18, 11, 13),
    chr(0x1e9): (58, 113, 62),
    chr(0x1ea): (53, 51, 52),
    chr(0x1eb): (228, 124, 64),
}

SUZY3_DATA = {
  ('F', 0, 0): (
    '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'),
  ('F', 1, 0): (
    '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'
    '2sFOeqaUBcf/Bv1bjZk='),
  ('F', 2, 0): (
    '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'),
  ('F', 3, 0): (
    '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'),
  ('F', 0, 1): (
    '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'),
  ('F', 1, 1): (
    'eNrtnP9f0vf+9z2g0rCEalENDZLJrmWyYJOZ70200rE6O+FcE/dFDraJkN/GKo+4kTYDzIzy7UJXoNymExalaabYu+xIYGq6rO3E'
    'KmW6wT7v8o+4nm/sbNf1uX1ut+MXun66nnNmeYM7zy+vx/PxYq6wsP8f/0+CJoB45pSAIOH26s8TaM8WRdvat/rz1bcTDkIIzM8M'
    'Y759O+GLhKSEpIN9hr6yMtozIplfWP3G7aSy26shoz5JX8LqpGcCQiCHDw/6ExKS+l5fvTqp7+DtzwPPJB1D2d2kst/LrtXgWz9M'
    'uJ2UlHD7c1roMYKE1QlJ/6sxLa1i3ZZ+Vt/t1QBa/XnIx452+/Xn/RUzVxiM9NHBii3734KEypI+14eao0+68En3XHl5eW5Pdvpg'
    'xfVjZUllBsPrq82hxnxIWxeeC5yo3Nzc7OGhLT+WlRni4hK2hpiT8LdPErN7uroITG5Pw6F19X1lcQH/wdWhHYVAQtn1UUYPwYBg'
    'ZIffqpEY9GaJZHVIZ5v2XFKgO53ByO2ZZ2WPHlp3LI4m0OuTQtqhwO3nrx1KZ0R15TJ6enKJJmXfrPHrERqtL6QJ6RP0K8Nnrjx8'
    'ODOTnv7l779/+feH0KGtGE2/NSkhhGdIf3DrKw1vfvn7yrTp0cHaWkZ518zgrfqtqNms7wvlJAReuND0sLy8Z/rQ8OhwbdUrr4TP'
    'zAzW+HEU0cclhVBOaY9oKxhRv1+7fiuxJ7yiicViNY0ONgXMmFnv70sKXeEEb11o7Ak+fWLX3K3Ev6fNDYZP38IDmJnm1yeFrnDm'
    '22+GZ6czGqrOpZdPj1bdunUut6dkENVjiICmfyt0CdE+f7Ohqzx9cLqEUV5SUpJ+5UrJ9PRgzQV6IIDoA2Wh4tDeSOoeLem5ciWK'
    'cQWGYbTkSk/J9LnE/gBG24oggr5QHSHBT8+vGwa9Kamai7pScuXczdHpkvTpqiYWDffTEFC5EE0cLeFRdzij5NytofSqm98mfvvt'
    't1Xnzp0bHGJdQCV+JEBbE5rCCf7x+tZrow3nbg7dXLelacu6b6u+/fbmzcRDK+oluN6Ab43Th6ZwtJ/69PWHhm8CYPrczapR+DS0'
    '7lZiYgXLEDAb9DSJ4ENBaDiP4gQV4beGtvwZKxITE9dVGvxInEQgoe0NDee7uOfjXhlNrOrv/uYwEd90bzl0KHFFPyYxCJA+iV8S'
    'dy8UlaOtiTNIWLWHBm/1n5mP/pvnEhOHKvFAnx6RlOkl/oJQJEQreGQwmK8lDg+O9vfDsPX3n6saTLzVT0eQPkOAZuijGe6uCYH4'
    'BO4eNBj0aNOh8Oy/z8f0aG1t95kpASaR9NECZWX6uBdCkJD5hTceSfz41PVDM1d6onpAd0ZXVDRtqaHTpmh9WyXmCwfLLsSZQsEp'
    'K5PEIRi96RAD1G16+lzFUHdTN3DoaB+YnoAh6aAhBCMneAs81AUzSp+qWdEweGgwsaK7u3tFRQ09gGJ+g8B/IdB3uyxu2Q0yH+yL'
    'k/jNOE6fqlxXUfHRR0ND3UO1g7X9+xEBRr/QJ/AHBEm3+/YuFyR4I84QR0NQJMgZguiuaBwdXtFUg/nRKfPzBtyP9yUk3dUs897z'
    '4Yctj2g0BEOn6OymQ7W1QxW1ww0NjSuGajA9QsdoEkmAJkm6bdgbWCbnbwUBBIo2dbk3vmluNC3t0HDDXHhj7QoWDhsVQAYDghjA'
    '1i+zcMjdOByls/N76yJ+qEjPDh8eDp+ba2wc/hI6JghgU3QiI4EhyXB3eSBcoImP3zfeMZ5c/OloOiM9PLxhrmG48aPP2FA1P4Jh'
    'GB6Q0ARlfY+Ww8HNHUc7qZGix29rraJtD8Fcz2SnN4SnfRoRkY+jGM2Psk73oqg54DcYlnGEkG2vvXbxYsbk1be1s1ki7ba/duXm'
    'Rj3866fJna0n9OhWjK43sHDNibpeDKPFLf0MmS8SlLxJ7WPqbN5s1iRVu+3rr7/eFt2ZnFx8ZB/7AjqF+A1x/iOfUbMe5yNL5pjz'
    'XruYEQnPvy0rLy9vNi9LRNWKRCJrcbRVFN1ReFogAE5A0iehZly8SD1qMyzNkODbLl6MnI2MnKQSmLxZCG0QpJ2cpFqPjpsQP8yA'
    '3/xI8nNGZMbFvI4lvkVi3pORJ8qKzBJlPaU8jcgs+MOsiCMyNA7DaRK/PvC8KDLv4sWr+UtL6LeLWbPRWVnF2j8hf34VGf2bBo1D'
    'cP2jvriCd7dFQkJZHX5kSWXLE80mR1qt80/+2jsvvvj++y++8876ed5Vk0lD0+P+C4Y4w6/bqJEZGRlHzUvhnM7I64wspLbCc2a8'
    'tv7Ajj3/vPN47X/9/M+IHTveWZ8xe1TG1uBxAYNEIjF89pg6CQll9OqXADqdl9WaVVgoms1bv+Pnx3se31k7/q89O3bcubN2z6vb'
    '3sk7bdKg0Jy+Pknf6Yi3tTArGRkd+I+L79DpWWqhdbwwK2/9th1fHH5/7QdrD4Cp2rP2zp0dq7ZF/wxlw+L8kjKDvw8/8lgrmpzN'
    'y3jMliw6IU1WJLV1PD5r9sCeF/91+PAX771KYA7vee+9bf86/M3VIzaTRhaIA6GmSfRHYdipkdC1/MUX7nRepKgz/sjs+49XwdOv'
    'Ij5WHf4jvrCZTCaZ2f98UpmZ1nHCWqylUiPzMupQiXnRHKo1usO6PiL47Kv+278/AcaEgrEq6xMgHUejrVRqVmRe3iQWQBYrbZHa'
    '4tb4vHdOEKmsOvw0mX9z1gBG06H36/tgqXf0PqZSRSCBeXnYYo+QOSOSWnw0OuOdV98/fHjH1QMvbSPa8w183rHt/cMPiLLlvysR'
    '4IbnJdi+jqtarXYS8olcLAe5Ghkpij4ym5HxzrbDJ2GWf77zz8OHD7z6wT9//uDOnsPPEenEH/lVgBr8frz3aFD0iEH4DD1vXlw6'
    'eaLozgg4ExffuXrgvTtrP/jgzoEv1t754IO1d9774gDRHdn4CbYe9ev1ASRCZIUDBAllbKP/bXGcyNlJ65G8ixkZeRdf3PPq2rVr'
    'P7jz+L/uENH72Y57gLF1dBZ2XEDhwu1HCotFRN0isya12OIGDn93m7a4I4Pg5OW99uKOPXv2vLd27R4iXnxx/RENlK2uc/zd32io'
    '3qynjUdbrUThYIvEm9csqkOstE9PPM4ggtg9F9evf/HAjgPvr4fI0P6gMcE/ydrkjvwLqB6h/XYiWlQcbBCVGo99uKiE6nMbf4h8'
    'SglGxmuvvUb8bnZb2SuoRmOKt2qL69hwFQZDdKJYC3ogunr1y98vY4ZF5VMfNfND5L8Zs/OLbv7rH375vaYfv3YiS2uNYEvMAgFi'
    'iigWFX/26Udp4TMVGLq4rVof1fMLUfCn++2PzGapn12/fr3p919+tGpFyR2CALTHFnH0h7QZ4p1TRlqlAFvUVq3v6vkS/A2saNid'
    'VC2hKhnz6Xz5y1BS//VX+qO10cnxuN7sR+t/qW2YCb5HyxiuFKBxi+R8RNUSkQXzClJXDFaBGKhfV66sub6u/1hdtLWzdd/pABrA'
    'rtU2zGUH33EGDs2PLY6T+/BTEeFuREQycDKKi4ut4HROXNuPHbv2+8rO4s7W8bpeFBMgKxPTs3v+zUEMKLI4DuNLkVVkJYJAgc0R'
    'FcPXJ9hsNut6zbutnRGFKWBEEcTMqp0j3ggm3nEersQlLYvkZH9ZTDyxtTgYItHkpJZqTbahNjZWs288OTmicLyuAzVjKLZiric3'
    'yJkZrjQbLiyWE/5DZ2c0fBRHd7a2JifDF9boIzaZjc3eF9HaOg6Rko/S6CxWbfhMMJ/c7GE6LrlrWwToGHAamt7uBEJra2d0NIGK'
    'KIyoa9G0aEzsFPiyNSJlXzwbPCnrk6Hw9CAmNzuRjvr9T/CFpzMMnLkV/RGthRARyZ1QwuLOiJQJk61FY+sdh5IVQkp1+YIfMaxp'
    'ZcMcI8hhrJvC/JK9yCKOaVduenjt0K/RhcnBfGAWRJ0n8k2aFpvMtC85urOwri4lYjyf5cfx7qYGKBzcWHJ7+qcwwd0CZBFli2LM'
    'DddW9HemaIujCfdeLDrR0WKDPWrTaOLHk0XazpT4ffE4rDn0WndjsHBRuTM1GIq/ZV7MGDDS09LSVtSMj09GR0/C1ae1w2bT2Fom'
    'JjSa/H0pKRFWrbW1sFcjoaEoa0VjOICioqKGz2A4ugjdqX/YFdWwoqKxdujd6Mnk4tnJycctLRqZpgViYiK+NboQSCJrZ3wvDe6n'
    'rNrGtMaG7K6uqIr+KXzKvwhOV3l5VENabW1Fx2RWtBbEU2OSaSCdIKi3k0rtLNyX0tp6JF6AYji9Ka02baa8vCs3fIiOo4EFc+rn'
    '4EGMnuzG2oofs4qLIyePgvk0yUzzmJb8wmIq1doJchAfzxZgaCVwGOWQTs8McAQLL1x9FDwqu6cnvHFF/2SndfKozcQ2aTTzmAlT'
    'b2FrcrEItKEwJT8fr6ejTYfSo7qCnG6462NmwYLLBsEgOLX9nVbtEZtGJnuKaZmwmXrBDmip4IcKU37rxVgYfX8ioyvIyc4+gwVo'
    'pgXmw8omHjRDcNb92inqaDGx2RqZbcJmC6Zjg5Wt1YoI4Uk5kp+PsiqbGEQ6XaDXDWfoiF+furCEWFHwsKjsHkZ4Y7816zeNho2i'
    'bA2cHYIDshOfDGe3lShe8r7f4lG8cl1PsGy5DMboGRAE2t6FJcTKhUf1ZOfONKbVWDtaNGzTmjVr7hXYwE1B2dim+M5oa3RnNCQV'
    'XZdf14vvryDyiSI4g2cqp44de2JeoNch2pMLnC+PdUzAnJlACFLv7S0AaWuxoZreTpHWaoX7Ued4vGbfPrRyiJELhzQK/MGhM5U4'
    'ol9gPvVQtyhGbk9D469sm41NHJsCyGXiXmqqxqbBNfvAf05mRVph/dSd6IinV1YAB/KBMVgB/cHi1iw0H3hUdi605xiMgAlrKQBR'
    'K7DZbE/uTbBlpvzkyTxwxSkpdXWt1uTTdZcrh2ZyiZcGnKEzdBp6wRy2cM7D3LlDQ3pTyxONLfUfrz+BghW02Ez3NKgtn5olio5I'
    'SWntnKRGpPzWkT9V05BLNIiRnd50pjKg1yyKw2hovGYr+Ol1U8GEqeXeQfg0McEumID2RLSOF0ZbtVlULcz2vrpC+v5aGDgYg+y5'
    'dfsr/QteC/Oc7PDaY6aW17+zFTxJnWixrVmjmWgxafaiaPx4NHGpmixO7myFu8uJQijcH5zKSv+jhcrOMaIID9MbhzSy758rKJhI'
    'nSiAQZh4Aw4QcNh14FMjqaLkwmRrFtwtT6AYvX9unhO+n07X351AFsyJym1sOFRvYz/4ik1QWmxPUm2mNRqbLBXPj6BqrZ1wUom1'
    'VFwMu5t9eap/vj8zZ+h0PG6he/sTQkLShrsF7Jbn7hWYUomUCqBopntsWQGeDxYETJAVLnBWMItgfvPZU2ca5jlbcAy7ew9ZoOzA'
    'iIanpf2oIWY61ZSamvokFSgtsgIbm87ubU2GWzwV3BwwRCAM472X6fQmQkYZ2RU4C9u6sJsWaw5EZ6427bpJxiYYBewnRDI2IE60'
    'YBiWAmpA1UI+Iiq4x+LWuuOZN+hTZ0Cxc2fA96I4LljwUpgZHuqmyTS2idSW1BYbu+BJywSkJAtywJVoReC24RJRfOJo5sh5h7c6'
    'c+P+jx4+fPO5uysFWIFswelEDa+4/gnbNFEAIzAxQYBeKJiYsGEmDYr1poDX0UK93n776HmH0ik8K3ZXu/jsvWuePPmKPjXF3lpg'
    'XqCIRqWvqKFDzQBTQGjbRIsMBTFgo7IpGbovmkpNPtJx/rwwh+whkezknDYhr+08OpG6d+I2NjUlE7QU4Asa6tye8P4pWeoEFA04'
    'pmBGJpS+5qANpePYxhvHR85fOm6Rcux2j91DLvXed8R4+fSVDQ21ZakyWIgX9v5nDutYT3nXTG2lpiC1BcpG9N9mg5JBxVK/u0dH'
    'sRuZPIr7UvN5npiS45Zy3HIXj39W6I3B34Ryz3X7JXdR2gI4UDWwOsOojagYCBvYT1ABk0nDZqNfvQ4Wii8Ui72Oe2cVmSOZwmpH'
    'jKOt+dJPPKHj2JWgPxgdraHRFuDjjwGmvDwdMxFJgMMldjX8AsOKFTz4CsMy+Q4XRMy9+2fHdm3atWvs7KW2N/rOikfCg5ubMZN9'
    '3Rx4gizAUEF0hVeyg89vCqYiY+MyGZtu+8c97IYjR8r1SJ1StVcovD9wSXfJ7fQ4R3SxH3XNGytG9jDtP6+F+nCC0pVbux/VaMAZ'
    'mjRxcWbCUgEG1BLdmOnYHUuxiCmlSrWTY1fZORwPh6xWCi/9tauE+PGrqOyZ7E/+YzasRqI5wGmis1GwUhr211/v+PpXGWSDT8ng'
    'fnicJ3RRfE4uCcLYriCpPB6yVC0vdaR3RVWNdpV39YAVQRZiQ8t70ru6GlgbM28ASCa7/fVnj79GZTKULsMwdKNDKeVygcKVMsnq'
    '2NgcsdvD5UAhq7vKS5pqo7qulHTNpP/ndK5ANjercnvqWfiInH8Zk2locZ9+amDL2BgIAXY5xlXKdO8W7obeiH0clcJIUqhUdqlb'
    'fje3pKqyNqqk6tx0FWsBs9bVlb7uVtc0C8FdZItl5AZc4dlE1TA2jqGXR2J4fD4vhkK2q4ztY2MKFddjZ5bmkH1kQ3bJt+yHXXM3'
    'SwbP/ed0Rku6cquQ2q4qFiKrJjPVaiBtRFEMJWaAfvkvI7wYr5vpsZOamzlSJ8ep03FVRhKXpOImXUm8gTF6qqbTb9UvQNmqoq7U'
    's46lf8tCEBeHZHdScoQxMfzMGxCZx4/f2HjDIaaId+fspribSaT2sU2bdkFSHKfScn9N9fHakqp100OshSj1rStd00hayU2Yf0Sn'
    'UJCkTrnQERMjdDgcvMzMkRtTlzN5DopabVe0tyuMmxRjRmKy7TATvuru6Ztb6usXdKFnDWVHTX/SFNUIHPyswtjeriJxOWqlF9TF'
    'JRTGZN64LGR6SEZjO7RHAb+qSCqVwmO0qzy7r587hiz4ls0aLJlet/Uvfwly2hWK9k1Gksru8cBhVFtcQv7IRqGS7OHAn6lIpLH2'
    'Xbt2bRqD16KyO8mOhb81EezQ9Ll1K4/BC8PbVO1jxFDBS1ZJOVKyW+yK4W/0Mp1MDid4SqE9Y2NjmxQqeBkeTtHi3oVnESegiWim'
    'rBkom4j6kEgcu1SttIgdMZerOXBgVEaCsov4gDYpiJwXywljsY4dC44m3tZOvNyxdphcJygnWW4ROoDDNRqB3g4g4GwiQsH1MJWL'
    '5fz5Bvb9dqIuIGIkFQd0Ri2HtXO5WsqBQWgnUiW2wq5d7QoPvAwPc8mcMFlbuxE61G6EusArLlVSLI6NLqaUYzQqIBniA44PMXQe'
    'O4fpQnAcXxqoiHjVULigLkudPqVFeNxB9tihIwooWztRtV2b2o0Ku91Z6th4eYmYsCIFgYE2c1XAYardFLH3eLUnOAbwjU3Byo3N'
    'c9xeXiay1MKRiC4TIDiMTrJbrvS6CA4MtZHY2e2bguen3Wj3MH1Kd4xsqR0qGgsGnHwSh8N0yy1iIcGBwikgl/lxg0kBDgdEd+mT'
    'UESc1E1jhLxwPWQlwRmJcRIc4pDOBzGRHg5HnRO7DE7bJgLUDtuMBIWTy8UO3o3dHo5CQZyfXTBvhPIoQEw9nIE24ZLrFoYEB27M'
    'aAc5bW5WU+QxMTeqPVIj9IeY6l3EN+EEcVV2srjNxcOXzCEGC/RUpeJynANMCkUIWqrzkBQw2UH3RoxJ+xiXa3f6muUxS+fcnz9A'
    '7SrCeJApchdIwoAd1o/RGKwZHB/FpjG7qpk8wJUvPR+YBELkQOLsdh1Z6bbIXfzLTpUHFhBxtiChdiIhlcqp1NmVS+9PWBFIGeiB'
    'wsgFxfa5LWIX77jL7lHAamonpmA+XTvIEkldiiydI7uvCGqpEVyAkwwC53UJoXCw0tuDKrprF3xfJbXb3WdL1UsvG4DAQUEzFCQP'
    'LDi52OKNEU5xQOKgP8GBAyUdI3k4zt2qUvGyOEHL0U44UCfTbaG4eLsvc6BwRtWmYEabNpHauVyOu63ZHbMcDgHapCAp7EY7GBIY'
    'bP79zI0DXFU7YQ6AROwGGHryWaZbFrY8Diyhdq6KQx5g+uQUrzD2+EadiquCSSAgMAdGrlSqJrkpy0onDK8Gy2mEA9TMAYWTe3nV'
    'Ixt1do6RODjEwIGBcJKVwgGvcHmcsCJoukrVrmpuHpADJ6YtZqOO6zEGmxMEKcBV6VRq3jI5+HkuTJyqmUlWesXA0fEyL7fNG3n4'
    'IBkVcDFxNzuXc3qedkgKo63wkH0Wr1hM4V0CDpOr4u6alz7YtnZpzlm1GF8uBxFy4Gal4urUFEuOi9cm5N/gD5DAqxJ7Gwyrnazk'
    'L0dE/4iX7SCkzVIdWe4Cmx0j5mdujCWB+yZWN1hEqdMpNUpfDlt+FDlJ7UYumSIWi5XyzEsj/I05XFI7YRXhygBy4LRwHUUh4IR9'
    'rGseGIh1MqVSpVDYxudvdHGIVRfc2nafSzjSLA5FPmEvK4ycs3CLd7qF/Mz7MTKZUg27m7CQXCnFEqu+b+SEJJ+wj7kgpTq43Qkd'
    'vIEiGVJU6oGbSbtKoWrWcUhcX7MvNPlwmG2X7rscXgvF67gvQ2RFcrcORg52HLgqn9BxycIMSUIvg+X0UXxkstJSfX8EbuBFljY7'
    'l6QAGXcLY1yUZo46NJwcXbPd45RKLY6RamERcCgUn665WRdLEVf7pFKvTv1xSPrD2V0dK5XmOHh8XlsMcGQvO2N1Z3UDA7CMOHIh'
    'r50ZmgaBmDb7XLwY2NuXhC6YBETsA5+tMDa3gRiRmTpOSEAfk5UDTg4HFFPsBfEBjswrrt7dfJbc1qbzOJlgd6SyUOQjhSubW04B'
    'KXWcvyT0ymTIy0qXsDq2bWBArVZzOG1GTmgKByDiamIBazXg9ULdZHIpyd5WncMkgXuQKrncUHBwMVnKAYy7VC7e3ez1OhAEKbLE'
    '6mB9w21CypS6L5GkoZjsIjWZrC5VKpVgSXVeigU4cH0Qit0+34DUAz4xh8RBQsEpLVWTS0tL4RLk0lHkFhzyUap9OQM6jwcmWyp1'
    'k6R4KDiUUrW6VC53gyc9G+SA9ijdZKcU7nfgE6VMDzkUnGBCpe7SUrHYcclFmedQ5GqykyN1epjgin2hkWxZsGilcrfcq/OKLThO'
    'SA/FXaoGP+xkMpm+Zk4oDlAYQmDkpTDZwvtCJQWHsEAZ5aVkJhFkty4kBzUMtxBVcyvFXrkvh+LFcWLgKBSL3AeTyCQzfdUhmTdI'
    'SE0hKF4xM6fZJQSMTGmxUCwUpY9Ih6l0teGh4QSvJWKLk5kzEIMQASDISK2EG6WP6dOFRHeAQ4F7icXHlMpjHDxCd8AlwCRQ5HK1'
    '2s1kKpsdoalbmIwsVaulTFdmLN8VTAhGEEYbhqGU7PS5neLQ1C0M51Ng0/H5MXyv3AUYHFdChiBFcjWTTKHEhoiDZ/K9Th+f5xDC'
    'RnU5oHKI2E1WiuU+MlNNyfHqikKUjhBOEJlZKhbyqnPkpcRKLRKrmWoLWQpi5KPYZSHCyL0OHs8FLS+l6DgWmQzHYapLiSNKsYg5'
    'TGdoyiYTe10ur3CEJy5VW+5fCg5CaamXQlYrlXCP8DhjQ8JB5BQ73AzccFSFfLgL83nEplNb1EwYOYtPyowVh6JuMgqsGU5sW/OA'
    'MGYk8zzPEePg47iQyRS74Kj6PE5htTAEHCTuhQ/f+lu1V1xq0bVVV1e3uVwxIzheBNsAsiGDT+TFyIXLLxxt9TfffPHF5x9OOLyl'
    'Xm9Ote6+sKgIOBRwOlIpnN0YIW9AHoIG6bdvP3ny5OYHO78bGbGIxfwRQmNwl9CrBi/sFvJcYu+l5V8dBRe2n9xw8uQpiAc7d358'
    '/MZPO4n/QwqBI8tzqDnkHKHLIs+xW5bHMes3bDi5ffupUxuAs/nBg+8hNn+PB2fdxc8UgkWQSj3O3b5lNSgQ9xLEhs0bALN58/c7'
    'HwAMavggyPHy+A6KkwLmiskE6VnGxAVOvhSMk5DMg+8fQPVObiA+bYX2yLwur5scC3cI/gjfZamOXfok6InGbIc4eerBg83BFm3Y'
    'sOEUQvwnMkTOlHrIwuPH+UK5BVgxwuVwtr8EKKIzG7Zv3/C9XkAYkPmnk1mYPgqheLqzKpJ9wCW8v/SBo23/d0CtTv3fP6+JCL1C'
    'r4WjI/w1bAYyeRlzjdBotFPzmFO0//7TMjhPrBywMz1SQiIcYLyXOddP43+wWgOxPt/58/zvvtq588E9fmgW0P+kruDpzv+0gajp'
    'S5t3Pru/Agp3OW7sPLWdmMiTp3biYc8O9Pz3p04RlJPbT21+dn/RVBjyPagEUF7aDpP/DP/qLMGqBxuCB+sU6MU/8GfI2QxnmNAh'
    '4Gx+dhzkMOjEUwV86eSzbBCI3lPM9g2Hn11C+KoN8/MGGrgq7hkO9qr/I/TPsG6H/8QcDoQ9S9AfIUCeIScMD17tYCc9U8qC438D'
    'zE+LRA=='),
  ('F', 2, 1): (
    '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'),
  ('F', 3, 1): (
    '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'),
  ('S', 0, 0): (
    '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'),
  ('S', 1, 0): (
    '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'
    'ykr0Q1BtKdsWleHtfPX3i/8FVyOpqw=='),
  ('S', 2, 0): (
    'eNrl2vFPFHmWAHDoRhqQsRJSoqlGJ1TdtOFSgJYbSqdrYbhVuwdnqldw0j2pVZYNoe2Ozt50mrXZ3KGL0TpmXNvhTDzupgmc0NIT'
    'aiSS41IYljmhC4FAYgEu63Sml4mW68Afce9b4N4m+9vxrfvlvlF/mF8+8973fd97Jebk/H897gQ6HIf+tBLJ0P9zrJLcNK0orCwb'
    'BEEs6aROkglLgskoimzQhpGRJA/JS8moh8YPuRVd0QklI1Mx0ZBfCqu8p03W8TsJRdFZUtYLryVlOZNcpTwkrRhGAns4CilTBMWv'
    'FrIytZqkRYVVRNFwY2Z0NmOIBuVZXWUVvjCqkJmMLxZT5PdW8GaNzRCiLGZi13Q9ygs66SGXY+zL9vXxsRW8WdNlUhelax5SiEoi'
    'KWWiMbZ7vXQczgrOcHSClCXPNZ6keI9ESiIw7T2flI6Nf4wxIDcr08OyBy4n45EoQaQkkWc75r+rX/+k6ZMmfJBbpgndEApXSUqM'
    'UhIZpXn++lTe5jqcpvHdGB2Fo8XYapTMeJajuiB6eKNgtme9qb6+frO0FKPDsolYbJUmSYEXyagS5Y07efM9PZub9Zub2PLmNmRW'
    'kQuTQkbPxARW8PyUVx62583P1/f87B//+OM7+ByWUyhhVYfHmRT1qCLyRsfUlz31693/Apn7ZAVfuSX0JB8dJkmR1ynBkGJG5dRs'
    '/dj6J6W/ffvtYmyOTBieZKHIZkhJUqIiyyeJmbzZO5tQ13nF1bMYHd0TK1RouB5R5xWd539b2d5TD09n9+XLo6MYHajkGKtn9MKM'
    'KBAZnt0LedssHd8NDkgruOqAEKWY9JKkyZgueQwxZjy8OvvzzbHRyyaD0SGlQs8wqXvQI4WJajyeypuvH9u9BV2+vILJySWpVdEg'
    'M4JA89BPk0ZH+2zeZunHlzE7LPRQkiAzvETzbbKQJDrap/J61qFb7949OgrXtILJgXgyHAndgOZ1cLiOyvdmZ3tQIYzv/rh+9neY'
    'nGESugFHkjFKAQeeT8fM1anZ+XloCaX4BgPKm1QIjof3ICdWSHR0T00haLPnScfMzD18jpAERxLILYe7dxU5X87O583/7a/eegvT'
    '1DZYUUjSnCgIusJnkPP4ydQskn7+XU/9Pzz7V1yOsuVEozRyoknucXdlZfvUbN785nzPzMwMprwRNEUV0gmS5984e7uRkgcOTNTf'
    '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'
    'qn3rr8//kWNJ3tr+6ixZ+Ir+F+e/AWc4idU='),
  ('S', 3, 0): (
    'eNrt2+FvE9eWAHDHEzBJKCNFQ1p5klSdUR1lNQkwrTK0ng1Nl9YutJMlAdnIL7CRqrgeQVe1JsV5WqXdIDICmppmI7HZh11YsImr'
    'TKmIijRBvLQxdiAWkTIkbLa16heWTlXIH7HnjhMo/VZyLe2HvULtt/npnHvuuWfs2Gb7/1Xa5Y6hxfPov6VD3DGKebJKBbkZRmM4'
    'TjVJktQMyqD4WEkylgfFZEwzHwh4KCGQVDwlCMmtGZpBannVE6FMlRMXBY+hlsCJzWkGR6lGxfGkquaTi04PxWiqGcMejkapTtKj'
    'LFZwqnMxyUgap0mU6cbMQCymZDo9i4ucJlQoGpXPeyIRTW1awJs1Lk9KqpSPHDcMRRANykMFItzPTdcOTixgrWjNUClDChz35EUl'
    'IFHOvBLhNtVMVB28VrWAMxyDp9SA57iQdwrOABWglIg6tdI5AdBBfI6bUxlO9UiLi3lPwClKzoAkcH3lw20fTkzUTODLnFudIw1T'
    'TC5STkmBcBRGEE7M/NTW1vnhxMGJToyOxjNSZFGh8h5RMQKSRzCbhofbflxpG175sAajw3ExIbLIUJSoSJSiKRGzd2bmp+XOth8/'
    'vIYtb25THdPUimQgz+QjIid6DEGbnpqZnR1e+dPf/vb3I+9jczhec4qL0KLzSclQNElQ+yCelZWTVz9c7sSWNyi3mJEUFJWiJMFw'
    'Bsy7EfPTqXPls21ty0MvvrgZm6OapidZIXF5uBF+VvKckCSnpmbKV5YnJso3bxvB55CGR6nQGMMQIG2cIQhDTeUrw8sTVVXfHPum'
    'CqMDlRzhjDxTkZdEMi9wV6dmVtomDgKD1gKuOuClgBDQKCg3I+AxJcG8itLWWXXsGF6HpAJJzxgF2TNESXVGzOkmcGqQgyL6ZgFX'
    'Xec9FZRJ5QMiI0A/TZp9n07NDndWwf6AU4XPkTyLFEnlhQAjMKqYJPuaAFrpvAYbVFV1EFMrRfE4F/M8Bd1AEww1UhHb1NQ7MlPe'
    'BoV97ZuDbTN/xeZAN+ApKuIsOnxfU+9U+RRq2R/WdLa9j62/ecQKcDyCxxQk5Fw82TsyNTMCredW382bF/E5ShKcgEitOtM3ewGa'
    'HS4fLv+7j597DlsfBYfhJVE0VKg35Gxq+rR3prx8eLa881/u/QemdqBqkuUoCrO6P1v7bkKHmymfhVN08+ZNTCMixzgDFUyMEh47'
    '0xdv9cINVD47/OPK8l9xtTeGcUI8MUlUGAPOD4rnYu8bEA/cdMtt+K45hpFEyJtHFBnooZYz3QcdbhjimV1ZXsDneJAjOkUOeqhm'
    'OTd7oSEMD6+srOA7PgwXEJMarwQE0xMwjUiFe+vWvltNM7MzU/80PDyLzTFIMVChqaJTMANOMx+JuKe3Tl/snRqZmhqZeR/f/hg8'
    'OBwTgLEtANN8RHBP923t6+ubmuo9cQLf1GtSbqezgoNhVEDH1BlR3NO3+qYB2oRPQU6eB0f1ME4BJjfLuXXr5M0mWHgdjYRzynk4'
    'p5JXTNWZdLo3bboFbQC3Q4KTNCRwJCUG15xEgnPyJEA4nRhyFBhEobo9Tl6F6W0rOJtuglQCx8mBE6BIzmpvfQDduvrzTbyJm3MK'
    'kQCJHMacQ9f2pk0g/ayq03gdw5mMeEhOdCqcSkUufzKAVnV19Rfq9ItYHU8kSZmcGFBINTBw6NCht75+9fn33nv+1QfqRz1Y44lU'
    'aOCIivt/Prl/HxyAXn3v+ecHqsd29WB0ApEK0uQURem4vG8jgpAEa+C/qzvem8N3AYlKBa+qghi5vKvyCfTWW29+0a7uf34OW0MQ'
    'BTiglnN0e//8xkOWBNRbDx61j80/34FrrhIVOKBcUvx2y5ajFwBCIVnUQEd7dcfXX3dgajyiUs1z4EQuXwGomDsreQPbz7arr3/9'
    'agcWhw8o0Ai4pEd48HDnFQTtXYUODZw2q8cggR14HDFPckxSUt65fP7KdUjd44gGDnVAKWByoL/lec6IUAr37fmdkLpd/fOPocqz'
    '7WOH3jrUgcHhPKIBTlIT1S82PNy5pRgQQG8euj9w/2VTPXAIjyMJzKojPtjw8PrRYkBvAnT//kA/CggDBOfHo2j8mBHhLOf8Ttih'
    'Xf2VIKGYBu5/srD5OhaHksDh8hFTVJVvN2xAO3Thwq5d/UVr4LPN7/7jLhyOR4qYliOokSQK6Aqc16NHt1tY5YWFd//z3c27MDgw'
    'UYFDKUXnAyiFK7C2bEHahV0PLOcoFkcxeVUSTUFDzgcbNpw/f34nrOtXtlz+ZN9nC39aeHh/3U7MdFIRkledAVNglMiD7+988BFQ'
    'aJ3fefkKFMPPC9r9jXjyRvKmE96CGTH54M73dz66c+cDWBs++7HtF6iEsfaxjTicu1SA50lwRA05q+v0j+XDyzXb9u3bR7aP7duH'
    'wREpZ4wnAxI4gaT04MGD/acPjIzAa33ntapth+bvmO0d8/MP1t8QRM0D8cBbvUg6I+pn/ZWb/3361sjwcueE5bxuqp9UVuJwzjp5'
    'nhfza87eLSf6RlbaljtrDlZte7Nyv6m+3N+PwQlwsD+cYpgB0hNRX+mvrBy48ekwclBAlQdM88D2Xet3YgEjwPFkxOA8yHkdnAs3'
    'Tp5DASGnv6Pd/GwXBod3MuDwEUOTTA/KG0D7b/RaAYGz90H72e0X1s+Ao3kYnkwyectBeaucv3FyZqXN2qBDcC9cx8DYSIlDjsBR'
    'eXg7NV+B3lk5f6AYEErco/aO8zgckzIlDepNlRh4aySLzoXVgK5VVf2ivvwFlgmONyXOcjQ1kOTPWw7aodliQFXb/oxnIoVe3UNy'
    'TlVS4a2R3150ji7cmlrN3Dc8plc6TsrHNCdEZUYiPLqzK/fO95++0VQOtY3OEKZPfGNcXo0xkplntIhYdObn5/s3b+otR1s0gevL'
    'wJjG/OrOU6aRZyIec82Zv3JjFbp2DU9AMZX7lZQM80uGilBnL1gDyPz8vn3fL2zqnS0WHRbIrWpuFRyecSrkgSfOvi0LxYgwbRE4'
    'v5JODmYEUSRPrzrAbNy4ffNjCJMTAydmKgJ/3hqmVp2NlZtR6qC6cQQEb46rjiD8+ajl7EUQMAfGTtzqPbeyDI1u/ZCbZNwxkTdJ'
    'TQicPVqcRCvn9wLUoVZXn0DnaLkGQ+ZiqkauOurLG3YCtFraD9X26uqx/TeaZlaWMWxRTOsxeJHnSEZQPzm/4ZU7H5y/cuXhhg0f'
    'vGyCU91x4MWmczigmCYxvGiqZE+A3I8m66Nbdu7csqv/wlg7cqpjthMny1egFtYJxTQK3uk0k4w5yf3FGf4oemM4bRYd0gbQubZ1'
    'Q7GePPqjHeSY+2GCv76laHU8evQYGjpZ3tZ5bX3fdscMioPdMc2Yx9wP0/vOncXXhbPArDm2oaZZ6EA1VQs8/6yWOy9qHMSjmk7z'
    '9B30svAQvS28Tj66K96tXoNOoF6Hrr2aXxYWFp7R4Ug3b3K80yxrXV2vv9LR+ujRo2pFWHVsJ27OWB0IoJprzwK5jYDm/tVNGpC3'
    'RNAehJVItLYCaW1QBCB0ow5NjwwXoW1tz/ItPrQDjxYDh+KdpK/O5wtlMvCf0FnkWFB7u3VzD92a+mkV+uUZID7GcGO/Qt4oUiRD'
    'PmvB/0JkazGgdqW66EDRzVg99dgx2KM/7AyBQ7pjpKGREXIPMhwOX3fIUXRQQGL7Ywj11GPHqjon/vBsMnQ1po2Z/0bGJFLjWuwu'
    'ORqNyvZg9InTLqw5thNN55avVU20PcNNDg5DSTGTy/OUmbJqIOhiE4kWsmcNunt3zRm6OFxTs1ze+Qy9bugN0uwxDD7P8SKZkqNy'
    '1B5lMy47OD2WA1DF3bU0vb/cVt40fA5mkz8KDbXybv5XmH15Q21xueSU3ZXSfXKq6FjQo68WH2/H+9NXR1ZWRpaX/+AXUENziRh5'
    'm9eMPHTRQd0VzcqubDZO6w5w1qB/OP5k24dONM0MD5984w867lyO/67OdFMkZe4gBtkwwWZdrFcvOggC6fhXvy2vE7D+8PdpZfU5'
    'MpHTank3x4ddLlbXsyzNOmgiTM7N9fR8dP0hSJHj6x2xy3L1mcTuXCLnaHaE7C6dpsMpXdd90RTbNTc31wq39zsArXuSh3D8u+tz'
    'CSjmlD+lh8Hwp/zh+CTL7uABegfi6Vm/A+EUdu+uByhot2fDBEH7w/BPz6TCWf3snLVgl9b9d5dliVwYGBRQ1A4FjfbmL6lJ1jHp'
    'H/S3kLzlkOv/s8syyNfueitxQXtK1v1+v0yzWX1PVp+kRzOnzvI8OdbchcHx5epzOStvMjvIFlhXVh+VXf+V1QdTUSiGSZqVU+t3'
    'uoLx+py1PYlo1M7Kdp120VlWd7hkgtDtUVc2anfZy9bv2L2goKzJKf+g7NdTo7I8mZJ9/myKIPwpO2xadv3h2Br1eDABpycIdwFs'
    'iw6FzcqyP+xwAcmysisF1V6GwSlkQpCzhF3OwkOzcGpSMq0TBS9BE0TWFdUJKEIc8WQu1SZkWXa5/K6oH84M4Wf9NG33+XU2xY5m'
    '/ZA/GofjCznGo7LMQhdIpeDRrE7rfh3yltJpIO1RXWfxOBnHeDY1Ce0zCpWA9j7rt6d8k4VJP/RtPTuo6xgcW2N3KBSq9UHDYekw'
    'TdMsyw6OsrRDTg3qLKo5OTWJxYl7HTDb+LJ6KhzWs7TuYolCONsNVQBb47LLdBgHY7MdWYqHQpkCQYTDhF8fHJVZNjsK54fQZbsf'
    '5S6LyUnH93R3110qhHUoZb/MEnSKzTrguLrgjMpYqq2YuaWWJUcoVChcYrPwcH/2Ujhr98nRUTt0IjhXuJwjzbXj6SWvLxPWXfLo'
    '4CDL+l32Ag2Toh1JuBiAapuba1viAIV1OKM6PclmM9loMAd9Lxgtw+bYDp/a0TyejmcKl2iC1tlRqGe6DnU9BGF0bO63IXd7QkSW'
    'puH6ycr2aLAAitXJcTpHbtdC4kL/TKSgAbhkaAjBArr+0AWI1/kOOWHYIGhykLtUAjnW3IDRObKjufnUqdqWpQyBmqjfJQcT9kT9'
    'bliY46ltTi+lxx0ZNJC6WDoVDSbkerR21+N0Dh/eMZ5Od8NZDcPN4KdZVzA3mqu3BjucDkjN8T3x7gK0gknCqrdgOIfythuzYzs8'
    'nvY66uCoQt7ghcGeYItOPW6n1gH3gy8EUy961QoG5URutzWpNmKG0t447BB0BFYPh10wmtTXWwWH2bEdbtmDILhZiUF/Npggigx+'
    'J77k6M6EoRb0LBR2kM4VoS7Mju2IN+4L1WUK4QJcd8GEa9XRcQdka0zDhVcoTNJhGOJheNyNTlBushF/QKjmCmE2lc3aEzlXMZ4s'
    'dsfW6PU6QhmYFdlUNLFWCDJ+50iLoxsGR4Km4QQl2Horby5HCQKCOQGmLJgUoPXIOdQSclFfCQKCodFXhw6RX04ErQsoF+zG70BA'
    'Dl8Ghiwia0cFhxpPsAR5QxAauMMwVqGCQwEFvd4SQEe8sEMZdINHE3oOvYlHS+LAYL8H5W0yZU8MWvWWiC8dKYkDZzVTyLLRxGQ9'
    '2p+EtySOrdGxB/JWcKErFbanPleavAEU8mUugQOzlfUJRnop3lgaJwMDCWuPZhIJ9NFCvCVdooAydRlaTqW6UXHngnu8jtI4tq4C'
    'zCP+sHcU3hqCUV+8RIXQmCnQIZ8vjgZHPeVfWloqRTxddCFMQIcbhW3KQOUR6ZZSOF0FaG46ESJSe8IhuCUKGe9SCTp2Fz1J++FV'
    'WC/40g5vd6iuEF9aKkG9NRK6KwW3j10O0eFCyNcdH1+K4z+ojWFiEl5M0FcmhWCWqAv50mmHA39dN9YRug7v91F7yA5vQuGMN93S'
    'UoJz2hUO+wcha0FX5i/B0ULBC6/88aX0v2KGGgsQTRDOZjATlF1EoRuC8XrTaS/mg9pFENEo+qYpE47K4UJ37ThALUtezAcIwomi'
    'aKKpUBReiDO1teO14+NQcJidLn82FYy6ovJSNqXThdod6COZdAuMw5idSRllLerTs0SmrvZ2c3MzvObFvV68F1CZPDiKvg2uy7j0'
    'QqFxx+1TtyEgGLoxH9Qy2Bn0kYuDvlTINNoOv33qbbQ9LVBwWOutzG4PRrOEg6WJTKP1+RL63Gfcu+TFO5KWQbuxZ5cKhE5Yz4WA'
    'UCWgM4TT6YpGXTrhDROZTOPaB2a3m8db4J7D6pTJ9pR/D3TpwtpTD0MdQOLSWBtcl901SkM0BfrJQw/veHtHbYsX54DQ5R8NE164'
    'Pp+EgwKyjmpLGt8B6iL8hMNXKBTqfvvII82o4lqwHdTGxkKiurp9d/i30RQDgoJLx/c04lEyddXivXv3xOrw7x5YhHBNPI3d1Q0N'
    '9+Dfvbtlv//AbEdtLdyomArhy7sNDQ2fQ0T3yN85wKDabsEDkYhpQM5rT/8c6/CpHdYOYXJaX3vthQaUt3sNPb/fnx2otseP4GJe'
    'a2goSq1Pv7D6oil6KQ0nqBGLg1YReipz7tZ2tB5lTn23/m+5e5577uOGNajhqYj4r36wVmsrhg9Ke1qfg3XvcUifP4noS3BeeunM'
    'C2fOVH9pwyVZQVnSWkRzZ86ceemF4nqpp+fL9f82cG41qAaA4N8qNAexvHTmzKr0wg9nejD8rnLOeM6iPn/KAclaVkgQG44fcK4G'
    '9fHHHz9xfngsFdfneH4puko97RQXxPQ5xIrtF6k9ra1P8gblVnx+sehh8/D9xBae//gEN/x2tbZCzZXiHX/utdWn91h/YmMr2UKA'
    '7f/Y+l/NhUsF'),
  ('S', 0, 1): (
    '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'),
  ('S', 1, 1): (
    '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'),
  ('S', 2, 1): (
    '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'),
  ('S', 3, 1): (
    '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'),
  ('B', 0, 0): (
    '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'
    'e32V66f/9vD6aZnrq3bbI2v5F/7frv8EAt51xg=='),
  ('B', 1, 0): (
    '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'
    'Og=='),
  ('B', 2, 0): (
    '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'
    '7PVVrp/+24Prp2Wur9ptD63lX/h/u/4DpGV4EQ=='),
  ('B', 3, 0): (
    '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'
    'j7O9VoOiYo1IAZRQMVShluVgF//j2wucqqqqLdueHFQVFQYFNilUaTJeCRnqcG6yUIsramuqNFWirMZULmxF4yEEqlgsVpTlOBt+'
    'eX3zifl2MTYUzpH7UydnmlZVLXmtVktF4/cmI7WC0J5o24VQ3LJKXs5rIHw5tWXk4oVKrKjYgu0ty9nwy0WjaayZq7ar0ShFDVZt'
    'Vf33FqZlS62qihepVLjmcJMrFOI5rtWK5kpTUVwkdzIcFzi7WLSsij2w4j9AHWtXw5mMSuW4+JDRCmerOS+KgalS2aGY4dWvDamh'
    'Sj1DwY4c/KnmRsKNZt2ilGJscpLzVsF5L1xtt8Phk1ykXsJUrWYzVdVTc0pzqGLk6hN11QjVm3YukwljXHutkYxVr4eKFmdZJxut'
    'VXDq4ZFqJouci8xMcepIuFqFIglni0PZilGNTERyQqxZL45ApSBHsmHVVuJ1wzJsSrEbpdX6LaeGRzLDw/WTXDhcRaIrk5mJ9kkh'
    'M3gt3rQK0eG2oETVXLZaVZTIxHALeWFZCrJiFZwhuKqVy4SjJSo8cy0+NZXlhGh8YqY1aXnN4WuDWSVmTMUnBnMWl7UaaHFAqCNR'
    'pKgtqCvnIOHCOTVHSLkRrxW/Fvdw46FGLGYXlfbgtZkhSyg1BHtoYjgSHbwWQTJQJaphFEOGpawCA8chHBSHfPZKltei6hNxdHBL'
    'iBUND5zBoRLnTSlFm8vFJyKlUtSj0D7smFKyQ8aqONVMtep5VIP0FG4KOIs6qXglThBKTXCaFGfbHNXgWkh4yj7pcYptCQJ6r9dY'
    'FSeTGalGOXRq1aNKLbVE4UkUKIKgDA1fm2lShi1wQtGw4C+OankN2ypxHGfELGt1nHa7jah69u8EQ0EmtQSDMFAjuaEZ2OMhg4WG'
    'ZSEwrZIFhchZnI3xAJmwKk5zqNrKqdGWqticUhIUjlMmFcVGHpTiGK6R3GQMXHQzQ4iFALOLoUkBaa1QU6viDA2hhKKehd6vGPXh'
    'IRX2YPRZXH14YvjaxPBEvUWVpiyIIgrtLmYYRdJDT8L03Ko4kWYml8vmGgpHIcCloZnBSL1ej88M18OkH7RV/A5+K1IfnIlUJ42K'
    'XYwJtk3BoPZqOHBcO9MeaXiUEbMVhFfxMkPNdo6yKGoqN5PxUI9Uq90cyiiY1JPFYkwxFK5FRb3SKjl4KmZdVIjFBIUon5hh24Ji'
    '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'
    '6cXTkw=='),
}

SUZY3_KEYS = sorted(SUZY3_COLOURS)
SUZY3_CACHE = {}


def suzy3_frame(view, step, talking):
    key = (view, step, 1 if talking else 0)
    if key not in SUZY3_DATA:
        key = (view, step, 0)
    if key not in SUZY3_CACHE:
        raw = zlib.decompress(base64.b64decode(''.join(SUZY3_DATA[key])))
        assert len(raw) == SUZY3_W3 * SUZY3_H3
        SUZY3_CACHE[key] = [[(SUZY3_KEYS[v - 1] if v else ' ') for v in raw[y * SUZY3_W3:(y + 1) * SUZY3_W3]] for y in range(SUZY3_H3)]
    c = Canvas(SUZY3_W3, SUZY3_H3)
    c.cells = [row[:] for row in SUZY3_CACHE[key]]
    return c


def suzy3_front(step=0, talking=False):
    """Facing the viewer: 104 x 200, hair from row 2, soles on row 198."""
    return suzy3_frame('F', step % 4, talking)


def suzy3_side(step=0, talking=False):
    """Facing right: 104 x 200; `step` 0..3 walks (a real stride)."""
    return suzy3_frame('S', step % 4, talking)


def suzy3_back(step=0):
    """Facing away: 104 x 200; `step` 0..3 walks."""
    return suzy3_frame('B', step % 4, False)


def suzy3():
    frames = []
    side = [suzy3_side(s) for s in range(4)]
    for d, flip in ((RIGHT, False), (LEFT, True)):
        pick = (lambda f: f.mirrored()) if flip else (lambda f: f)
        frames.append((d, STAND, 0, pick(side[0])))
        frames += [(d, WALK, i, pick(side[i])) for i in range(4)]
        frames += [(d, TALK, 0, pick(side[0])), (d, TALK, 1, pick(suzy3_side(0, True)))]
    frames.append((FRONT, STAND, 0, suzy3_front()))
    frames += [(FRONT, WALK, i, suzy3_front(i)) for i in range(4)]
    frames += [(FRONT, TALK, 0, suzy3_front()), (FRONT, TALK, 1, suzy3_front(0, True))]
    frames.append((BACK, STAND, 0, suzy3_back()))
    frames += [(BACK, WALK, i, suzy3_back(i)) for i in range(4)]
    return frames


# ---------------------------------------------------------- Sith Ewok 2 ----

# Sith Ewok 2: a hooded Ewok with a crossguard lightsaber at Curse of Monkey
# Island's detail (SCUMM v8: 128 rows, 241 colours), by an artist panel from
# the user's three sheets (the saber off, igniting, lit): the saber off at
# first; lit by a key, he takes the hilt in both paws as the blade springs
# out (IGNITE 0..5, played backwards to put it out), then carries it lit in
# his right paw (LIT_STAND with two crackles, LIT_WALK, LIT_TALK). OFF frames
# 121 x 132 (axis column 60, feet on row 130); IGNITE and LIT frames 181 x 240
# with the body at the same place (+30, +108), the blade above. SEWOK2_GLOW
# letters are light added to what is behind (the blade's red haze), and
# SEWOK2_SHINE drawn even in the dark (the blade, its sparks, his amber eyes).
# The sheets are not kept or read here: every frame is baked as palette
# indices (lzma + base85) and decoded at import.

SEWOK2_COLOURS = {
    'Ā': (1, 0, 0),
    'ā': (70, 53, 59),
    'Ă': (214, 83, 24),
    'ă': (77, 28, 5),
    'Ą': (128, 62, 21),
    'ą': (48, 36, 38),
    'Ć': (133, 42, 7),
    'ć': (56, 5, 4),
    'Ĉ': (57, 19, 6),
    'ĉ': (41, 28, 30),
    'Ċ': (230, 168, 119),
    'ċ': (26, 17, 19),
    'Č': (82, 33, 34),
    'č': (75, 20, 2),
    'Ď': (251, 37, 13),
    'ď': (188, 88, 33),
    'Đ': (164, 20, 20),
    'đ': (93, 26, 3),
    'Ē': (164, 149, 140),
    'ē': (31, 22, 24),
    'Ĕ': (175, 73, 24),
    'ĕ': (84, 50, 52),
    'Ė': (64, 28, 20),
    'ė': (73, 62, 56),
    'Ę': (248, 226, 205),
    'ę': (122, 10, 8),
    'Ě': (41, 6, 4),
    'ě': (111, 52, 16),
    'Ĝ': (13, 3, 2),
    'ĝ': (95, 20, 20),
    'Ğ': (142, 26, 26),
    'ğ': (33, 5, 3),
    'Ġ': (35, 23, 26),
    'ġ': (58, 14, 2),
    'Ģ': (111, 45, 45),
    'ģ': (14, 21, 20),
    'Ĥ': (81, 84, 105),
    'ĥ': (246, 67, 11),
    'Ħ': (19, 17, 17),
    'ħ': (86, 21, 22),
    'Ĩ': (203, 92, 33),
    'ĩ': (90, 84, 84),
    'Ī': (89, 62, 65),
    'ī': (131, 94, 79),
    'Ĭ': (143, 56, 15),
    'ĭ': (244, 182, 182),
    'Į': (226, 207, 219),
    'į': (35, 32, 31),
    'İ': (81, 28, 17),
    'ı': (56, 39, 42),
    'Ĳ': (38, 26, 29),
    'ĳ': (66, 47, 50),
    'Ĵ': (143, 72, 67),
    'ĵ': (142, 133, 130),
    'Ķ': (47, 35, 43),
    'ķ': (82, 42, 43),
    'ĸ': (22, 16, 20),
    'Ĺ': (1, 1, 5),
    'ĺ': (19, 4, 2),
    'Ļ': (108, 30, 3),
    'ļ': (154, 27, 26),
    'Ľ': (186, 56, 11),
    'ľ': (90, 31, 32),
    'Ŀ': (25, 8, 5),
    'ŀ': (40, 30, 37),
    'Ł': (75, 56, 63),
    'ł': (58, 54, 53),
    'Ń': (94, 9, 8),
    'ń': (76, 54, 56),
    'Ņ': (5, 1, 1),
    'ņ': (54, 41, 48),
    'Ň': (114, 38, 7),
    'ň': (198, 103, 43),
    'ŉ': (250, 165, 141),
    'Ŋ': (237, 95, 30),
    'ŋ': (58, 61, 70),
    'Ō': (50, 35, 39),
    'ō': (74, 11, 10),
    'Ŏ': (109, 31, 31),
    'ŏ': (108, 103, 120),
    'Ő': (62, 22, 4),
    'ő': (158, 63, 18),
    'Œ': (17, 10, 11),
    'œ': (33, 10, 4),
    'Ŕ': (21, 13, 14),
    'ŕ': (9, 5, 6),
    'Ŗ': (249, 85, 21),
    'ŗ': (51, 24, 25),
    'Ř': (149, 11, 9),
    'ř': (207, 142, 139),
    'Ś': (89, 41, 12),
    'ś': (199, 28, 13),
    'Ŝ': (83, 58, 61),
    'ŝ': (162, 76, 28),
    'Ş': (4, 8, 9),
    'ş': (13, 12, 11),
    'Š': (224, 113, 47),
    'š': (76, 51, 53),
    'Ţ': (128, 56, 18),
    'ţ': (32, 21, 23),
    'Ť': (120, 21, 21),
    'ť': (5, 3, 3),
    'Ŧ': (93, 36, 8),
    'ŧ': (68, 23, 25),
    'Ũ': (167, 82, 70),
    'ũ': (93, 33, 20),
    'Ū': (64, 48, 56),
    'ū': (119, 51, 15),
    'Ŭ': (112, 103, 100),
    'ŭ': (123, 42, 41),
    'Ů': (69, 24, 15),
    'ů': (47, 28, 29),
    'Ű': (50, 38, 45),
    'ű': (183, 97, 41),
    'Ų': (138, 61, 20),
    'ų': (75, 32, 6),
    'Ŵ': (53, 36, 39),
    'ŵ': (209, 108, 100),
    'Ŷ': (45, 33, 35),
    'ŷ': (106, 21, 21),
    'Ÿ': (39, 23, 19),
    'Ź': (70, 49, 52),
    'ź': (199, 77, 22),
    'Ż': (161, 119, 91),
    'ż': (59, 44, 52),
    'Ž': (100, 31, 32),
    'ž': (122, 36, 5),
    'ſ': (29, 19, 21),
    'ƀ': (126, 46, 10),
    'Ɓ': (66, 16, 2),
    'Ƃ': (101, 92, 88),
    'ƃ': (63, 44, 47),
    'Ƅ': (13, 8, 9),
    'ƅ': (59, 24, 25),
    'Ɔ': (60, 42, 45),
    'Ƈ': (72, 56, 59),
    'ƈ': (56, 34, 36),
    'Ɖ': (125, 116, 114),
    'Ɗ': (88, 76, 69),
    'Ƌ': (137, 14, 11),
    'ƌ': (32, 24, 30),
    'ƍ': (70, 25, 4),
    'Ǝ': (59, 15, 15),
    'Ə': (30, 14, 13),
    'Ɛ': (170, 15, 12),
    'Ƒ': (82, 9, 7),
    'ƒ': (47, 4, 4),
    'Ɠ': (78, 72, 70),
    'Ɣ': (217, 198, 185),
    'ƕ': (61, 31, 33),
    'Ɩ': (84, 33, 7),
    'Ɨ': (67, 63, 61),
    'Ƙ': (51, 15, 4),
    'ƙ': (151, 69, 24),
    'ƚ': (86, 58, 47),
    'ƛ': (36, 27, 34),
    'Ɯ': (40, 15, 9),
    'Ɲ': (140, 42, 41),
    'ƞ': (109, 44, 12),
    'Ɵ': (46, 32, 36),
    'Ơ': (44, 31, 33),
    'ơ': (158, 53, 11),
    'Ƣ': (71, 32, 34),
    'ƣ': (24, 15, 17),
    'Ƥ': (43, 29, 33),
    'ƥ': (186, 172, 163),
    'Ʀ': (80, 56, 58),
    'Ƨ': (95, 49, 50),
    'ƨ': (107, 10, 8),
    'Ʃ': (168, 45, 7),
    'ƪ': (49, 10, 2),
    'ƫ': (175, 84, 32),
    'Ƭ': (139, 120, 107),
    'ƭ': (28, 21, 27),
    'Ʈ': (49, 45, 44),
    'Ư': (48, 33, 36),
    'ư': (96, 41, 42),
    'Ʊ': (29, 27, 26),
    'Ʋ': (53, 38, 41),
    'Ƴ': (41, 38, 37),
    'ƴ': (51, 29, 24),
    'Ƶ': (65, 4, 4),
    'ƶ': (182, 58, 53),
    'Ʒ': (50, 14, 15),
    'Ƹ': (68, 40, 41),
    'ƹ': (68, 46, 49),
    'ƺ': (80, 61, 67),
    'ƻ': (117, 99, 87),
    'Ƽ': (43, 16, 17),
    'ƽ': (145, 73, 27),
    'ƾ': (186, 71, 20),
    'ƿ': (61, 46, 39),
    'ǀ': (102, 32, 5),
    'ǁ': (25, 19, 24),
    'ǂ': (48, 19, 11),
    'ǃ': (204, 63, 14),
    'Ǆ': (183, 22, 15),
    'ǅ': (25, 22, 21),
    'ǆ': (116, 84, 85),
    'Ǉ': (149, 38, 5),
    'ǈ': (56, 24, 16),
    'ǉ': (222, 34, 12),
    'Ǌ': (37, 8, 3),
    'ǋ': (101, 42, 11),
    'ǌ': (43, 11, 3),
    'Ǎ': (171, 61, 14),
    'ǎ': (109, 73, 64),
    'Ǐ': (66, 14, 14),
    'ǐ': (162, 84, 33),
    'Ǒ': (119, 30, 30),
    'ǒ': (84, 24, 3),
    'Ǔ': (145, 48, 9),
    'ǔ': (44, 33, 40),
    'Ǖ': (160, 114, 116),
    'ǖ': (131, 28, 28),
    'Ǘ': (17, 12, 16),
    'ǘ': (78, 24, 25),
    'Ǚ': (38, 19, 20),
    'ǚ': (37, 26, 28),
    'Ǜ': (73, 52, 54),
    'ǜ': (28, 5, 2),
    'ǝ': (75, 33, 22),
    'Ǟ': (224, 70, 17),
    'ǟ': (41, 30, 32),
    'Ǡ': (255, 222, 128),
    'ǡ': (236, 138, 34),
    'Ǣ': (70, 30, 18),
    'ǣ': (40, 10, 12),
    'Ǥ': (132, 46, 42),
    'ǥ': (255, 255, 255),
    'Ǧ': (255, 214, 206),
    'ǧ': (255, 128, 116),
    'Ǩ': (250, 30, 24),
    'ǩ': (178, 6, 14),
    'Ǫ': (255, 226, 196),
    'ǫ': (255, 70, 48),
    'Ǭ': (140, 10, 10),
    'ǭ': (96, 2, 2),
    'Ǯ': (62, 0, 0),
    'ǯ': (34, 0, 0),
    'ǰ': (18, 0, 0),
}
SEWOK2_GLOW = {'Ǭ', 'ǭ', 'Ǯ', 'ǯ', 'ǰ'}
SEWOK2_SHINE = {'Ǡ', 'ǡ', 'ǥ', 'Ǧ', 'ǧ', 'Ǩ', 'ǩ', 'Ǫ', 'ǫ'}
SEWOK2_KEYS = 'ĀāĂăĄąĆćĈĉĊċČčĎďĐđĒēĔĕĖėĘęĚěĜĝĞğĠġĢģĤĥĦħĨĩĪīĬĭĮįİıĲĳĴĵĶķĸĹĺĻļĽľĿŀŁłŃńŅņŇňŉŊŋŌōŎŏŐőŒœŔŕŖŗŘřŚśŜŝŞşŠšŢţŤťŦŧŨũŪūŬŭŮůŰűŲųŴŵŶŷŸŹźŻżŽžſƀƁƂƃƄƅƆƇƈƉƊƋƌƍƎƏƐƑƒƓƔƕƖƗƘƙƚƛƜƝƞƟƠơƢƣƤƥƦƧƨƩƪƫƬƭƮƯưƱƲƳƴƵƶƷƸƹƺƻƼƽƾƿǀǁǂǃǄǅǆǇǈǉǊǋǌǍǎǏǐǑǒǓǔǕǖǗǘǙǚǛǜǝǞǟǠǡǢǣǤǥǦǧǨǩǪǫǬǭǮǯǰ'
SEWOK2_INDEX = [
    (('off', 'front', 0, 'talk'), 121, 132, 13, 3, 93, 128),
    (('off', 'front', 0, 0), 121, 132, 13, 3, 93, 128),
    (('off', 'front', 1, 0), 121, 132, 13, 2, 93, 129),
    (('off', 'front', 2, 0), 121, 132, 13, 3, 93, 128),
    (('off', 'front', 3, 0), 121, 132, 13, 2, 93, 129),
    (('ign', 'front', 0, 0), 181, 240, 33, 116, 99, 123),
    (('ign', 'front', 1, 0), 181, 240, 28, 116, 108, 123),
    (('ign', 'front', 2, 0), 181, 240, 28, 116, 108, 123),
    (('ign', 'front', 3, 0), 181, 240, 27, 88, 109, 151),
    (('ign', 'front', 4, 0), 181, 240, 21, 56, 115, 183),
    (('ign', 'front', 5, 0), 181, 240, 18, 24, 118, 215),
    (('lit', 'front', 0, 0), 181, 240, 7, 37, 135, 202),
    (('lit', 'front', 0, 1), 181, 240, 7, 37, 135, 202),
    (('lit', 'front', 0, 'talk'), 181, 240, 7, 37, 135, 202),
    (('lit', 'front', 1, 0), 181, 240, 8, 37, 134, 202),
    (('lit', 'front', 1, 1), 181, 240, 8, 37, 134, 202),
    (('lit', 'front', 2, 0), 181, 240, 7, 36, 135, 203),
    (('lit', 'front', 2, 1), 181, 240, 7, 36, 135, 203),
    (('lit', 'front', 3, 0), 181, 240, 6, 37, 136, 202),
    (('lit', 'front', 3, 1), 181, 240, 6, 37, 136, 202),
    (('off', 'side', 0, 'talk'), 121, 132, 27, 3, 66, 128),
    (('off', 'side', 0, 0), 121, 132, 27, 3, 66, 128),
    (('off', 'side', 1, 0), 121, 132, 20, 3, 79, 128),
    (('off', 'side', 2, 0), 121, 132, 30, 2, 61, 129),
    (('off', 'side', 3, 0), 121, 132, 21, 3, 78, 128),
    (('ign', 'side', 0, 0), 181, 240, 52, 119, 89, 120),
    (('ign', 'side', 1, 0), 181, 240, 48, 119, 99, 120),
    (('ign', 'side', 2, 0), 181, 240, 48, 119, 99, 120),
    (('ign', 'side', 3, 0), 181, 240, 48, 87, 102, 152),
    (('ign', 'side', 4, 0), 181, 240, 48, 56, 107, 183),
    (('ign', 'side', 5, 0), 181, 240, 48, 24, 113, 215),
    (('lit', 'side', 0, 0), 181, 240, 49, 37, 122, 202),
    (('lit', 'side', 0, 1), 181, 240, 49, 37, 122, 202),
    (('lit', 'side', 0, 'talk'), 181, 240, 49, 37, 122, 202),
    (('lit', 'side', 1, 0), 181, 240, 47, 37, 124, 202),
    (('lit', 'side', 1, 1), 181, 240, 47, 37, 124, 202),
    (('lit', 'side', 2, 0), 181, 240, 49, 36, 122, 203),
    (('lit', 'side', 2, 1), 181, 240, 49, 36, 122, 203),
    (('lit', 'side', 3, 0), 181, 240, 47, 37, 123, 202),
    (('lit', 'side', 3, 1), 181, 240, 47, 37, 123, 202),
    (('off', 'back', 0, 0), 121, 132, 14, 3, 93, 128),
    (('off', 'back', 1, 0), 121, 132, 14, 2, 93, 129),
    (('off', 'back', 2, 0), 121, 132, 14, 3, 93, 128),
    (('off', 'back', 3, 0), 121, 132, 14, 2, 93, 129),
    (('ign', 'back', 0, 0), 181, 240, 48, 118, 105, 121),
    (('ign', 'back', 1, 0), 181, 240, 44, 118, 109, 121),
    (('ign', 'back', 2, 0), 181, 240, 44, 118, 118, 121),
    (('ign', 'back', 3, 0), 181, 240, 44, 88, 126, 151),
    (('ign', 'back', 4, 0), 181, 240, 44, 56, 133, 183),
    (('ign', 'back', 5, 0), 181, 240, 44, 24, 137, 215),
    (('lit', 'back', 0, 0), 181, 240, 40, 36, 141, 203),
    (('lit', 'back', 0, 1), 181, 240, 40, 36, 141, 203),
    (('lit', 'back', 1, 0), 181, 240, 40, 36, 141, 203),
    (('lit', 'back', 1, 1), 181, 240, 40, 36, 141, 203),
    (('lit', 'back', 2, 0), 181, 240, 40, 35, 141, 204),
    (('lit', 'back', 2, 1), 181, 240, 40, 35, 141, 204),
    (('lit', 'back', 3, 0), 181, 240, 40, 36, 141, 203),
    (('lit', 'back', 3, 1), 181, 240, 40, 36, 141, 203),
]
SEWOK2_DATA = (
    '{Wp48S^xk9=GL@E0stWa8~^|S5YJf5=B<J6|6Kq8ZZ1g|(;G%=@x{UiU7Ox=xq#q*yS*<xnr7Jz`>N=4W`!1cAhmLA6#EusUjZqd'
    '|J^9;Rn?jjw6=W-EF%i}2WEIL$u~ex=1V}+7&MjY47JkE0k+r04tdf(?byR(X}+_|G?Wmj(;mGOW!{7nM&5)dA&dSw(QPlTd<cbC'
    'fKCdoQxvyqC|*6$x8?I5GBfWkxt5!~JcBXTv7eU3HcOmHYWqA5&cv5H3JC6?%`Y{)<B?rs%q`0|HxFTi%_1O6$5sJ;7#vvhtRM($'
    'F;pr6e<59?dzQE?&S`unbPjJi!>=&(8u6=D+Yoska2LM`eHuYra9ZYNIv(iN<Rq?xkMDB8R-(;M1o)MueATj)3~^lQBuK0ix}5z<'
    'pF%al{M-zu_ljGVpK6(xP8id#sY{E3&Ea1L;@SH?1aeSy(R>0VUAY#Tso=#oV<yLSy5%0zjvdT9dsaF~%4c&}(4ZG5U{{IXgpoN5'
    'byROgxBd-Pb}RbeWH;X~vzBb5<vr^#j#-OTkl7d#heMjFfUIdgGY>DPY<~fo^oK8YX73R%G%8RS$*YvJDt^Cu913eNP16H!v+de*'
    '(qAI<EOB{<uPfNQUz@%l#*9$}3EV9{`y+KC5*di3z}xj)k0xU%OwJv=h?cUXO~L2gu))S?zGAqk#UD1*QKN)v5sEYSz7?~pe57g('
    '$2Q7X%5G;ItNx)3=pK-XP|8=%T4uX16zlo#?QmMLmq`5Xxe!@y&*id1XrZ4oyji^k5h?p@(cb==Vs25#g3`;ELUhtVpR`~VN$1@&'
    'z^qb)C@ftQN6I-<I2vD<5!6ZrF8y6?{#oyt_`BZFVfTN*#E)}+fyvzA=FXr-|7NG0{1@Fw>53gp60Clml<nWR+2ly`7(s1N=lXR3'
    'PU<08#LNFF&nxnpT*YqdCSpKbHcPQg9{i+P@AeN`4swn-C^1GF#uRu)_aL(&WFFAUi=W6WQp6`V%j%7P#1l|uW+klLi=6WO^wf+2'
    'WJ8IzR&+hb&nUAtxpjOhXF!*HK`lP;Hh*)f-na4fWBXfQVMxEdWYU=KR&ZfOemN~i<Np64OXC^Zg)<^CV<DR8;1xBr&7X}jdy)%u'
    'Iqit_n`zS=`k&z(MlMKw=5kytjTp1D5>$LZ756_p-x18_0;`}|fy<QWzq{0*ZjA@ZOb*~fiPVP-s=M{En{i*wwp0JR!PrR{b4E0?'
    'p!?%`p%gx(mzK<V)j44+Z9oC|9%>PpTDAD9n$Hd*$+Qu(Ms{y_HUG@q6KAX$)fx-X_*AwONaFC=|MVA*3f(xxQpbxSk27cNa(o$v'
    '8SW{Nn@#@_<Vaik2)tQ<e|<&aN#o#X9*^`+T;=@ZB3wtz*TC?YIMP-8LA}VHv;3|Jc-p|kxr}|+;Rk`q7U4g4k&X9G{UJF|F3D_p'
    '@m?ql;yC<B?87^hne~yI5~PR>qX#mY7G7KmWIirDc?}^jer$3~L2R_lYCA^W=OD|tOD2w^XuaksFiiVmBBUqW%e+HUPugfUS&ko}'
    '6fd;@(LFpCzvx0)-$o^;zMI2}2F)mGXjwaa^KkSnlnQ_KL++VF(C0h5?y)sSR8b>_1D-t6IYR_n&R{|3_874j8);u`_w<TDj|VkV'
    'C{&CA7Yxe~p+LhFxSQy9IJANWXiYr?Y+9h{S7P)jfT=CH41bc)u;Bw4ydNj2F)mtL$Q01zWI#;6ahZaEOzJ!&V8A3I2fd{vWW2qx'
    'ilAbxvW4q$yd%6?-!QWg{c5=Lmx_Xn-L_}yte{tyj>t>}AKUhA;rEqaHq+6O@52|<7MCG`%mC9fh`{+*y$x!|kT*T#6%@MaR|!A9'
    '`8P!rl!07xWc8-}k^W%>&va1iBsFpZJ6u1{M?n9x`mZEAd%0POa6Qb6^|@_0cO8^UP(Q@CW<>}>r^8Tp1Md8s-=licC{_z!>zI27'
    '-Atq+W-nSpRVhe18JKU_^uDPCQMG)=Qr7=bmfAe4Rk9EN9;dUIsbwsE7#;Mp{)jU$cBDEsD$=04{@$IS?=w$!j>d3!GlNC-`}-G+'
    'm&#LxseX7C^c0?e4MaHKv%Wi}Fr$l>K+Rd%vCh|5vtt3$b`Vv7t2V*SidwC7=2_{=7TV!5LLHEu`yW(SCJDR2s5+M<fEV(&6t;Cb'
    '$ZT4K>;QYT@cytVC!XO5tZb`9aL5Z$=kz3dq$1-*lILQLQ+8}Rc^yD73mWnLS~ci3!n7pBa@=E}i$J0BbhUi>3VqFOiSNe6Ko-5R'
    'O*vQB;+#laqV?SDTg9HD_o#$PVr53+KmT47QMPG}7g7a$8<=*q0k+YJun+bbBm3%5Imd4g*t_cUv@Wz8v{9`=8nk-mQ3iJ#^XZz&'
    'jyW249jSi(LZ7$MRr>>T60*s=wK;aI3}Q>#JjbYit<aui(mOHcGHcgZ$0aKlcSvU?P;|@PY$V(c4Gwvefkr3OxTywP(9uP5;RP0R'
    '8D9t&ld?cB-m|m!RFF8~eK(eyM|>={;?3K0$~bpE7EoRR9L3efu8x06ZQ_HEeG@W9{<?SOH^l+bpkQnXEZmFql?HAwzD}XXLcuMQ'
    'N<v>xZPSq@^ymSHrs;(F=0b0uYhj(8OL0mgd~{tjPsWQy`o-uHDL6wNWG9I!y4D=FLncp!j_fbgA-cUI+83}hYxPe`dwm;0=J<y%'
    '-CCe!i>@JDpxA2~wvJpbOoa$G;h4YnOzkJKMJ+<iwV?YLks)_5w|*~i8b|pq5mi|!MlG!<xd1T?C^e5}-zsSG)b#kb!*l7BL^AW='
    'r%An;IysX$pQmXU8+#Nk4WTSO;HIf>a20OXp%~YBPrB;9oTO|{CBPKBnsg%fI_NunSznX<`0P6TQ?135_z*gx5@05kBZf$AANL|q'
    'a5ie!&Hh<Ypc_X#lHAPmZ?@R33B0)LwPXPyRBtJrkROK!_3)96LVOxca+NqeO&fWdiXq4lg9$I8ok`M}4DDjqZ;UFQYOa!h@g#Rf'
    '4mY>G%}f7{(1xxZ2yL4(lLnjs@ijhntDPiUWtPjXl{)3Fh$I!ECRvAmoYzDAYlfmSG}vxaRW)xY-~zNVyrq1?aJMt#y{7X{cML;&'
    'DO!P9@l02LwDjw#N>n|*Ssq*aGUXSN5KsS%6!pv1d>tduJtY1jLA9AATw#M7Gy?`W9`c&ORR7Z$AMC7Kc_^Pi+sj9msKij?ELz<o'
    '&557j|N16~W^@Orszb7SX>4bPB{^rb%+0);2bAsYgS^j!a_m!$?O8svH<cRUK!|+%W1B6R#7WXy%!?WoxABu$CsO>02X0SsG9bX}'
    's!#<Ccfc{o@7r;^W8h~$J0p3gEX;-hL&lfMD8H!|C?*zeUKH?_05Di*<layGSpY8^T~;21g(8h@MdvZKEj>i}C%Ju<e!AZ5J-fA`'
    'J$*IL+_EojRuxsdoMNXlhw<y$*k_atoI8>MNa(FY0J7F=TPICbJ2@a@TpNZtc>K5CUG4KEln2yR^Nmm6{Joo)0}3*km<~I?n}pRT'
    '`tq#`slzNS`DB0346vvY>kR4QZaYI81N{hsyG~`B?Z?KI#(u43JB|UiuC5fa(@s8(o!e^FD2NJQhLGJRG$l+w_%ug)Hn?G0g?du3'
    'Y!d9kk)}Z=9)XkC*}2Mb-)hVcOI%@A1AlvmUPB^Ocngp&_g?vg<ZzZ`-HbW~vAYS>K4w?cq?~Iba1zAhyRGFl-q#7p0z9!IY>!rm'
    '9cbx`j@4MxGG`Asdn{id74@Yzz~XO(>4EcvwB|9*!hK)KwKXd3n^5C!YV|o@@Qm(-`o$|Rw!boOJELzLMqxb9tT?~^Xh%f&P5Xto'
    'W<~Ahw4A}!5!z1`FWw_>!xp(DVAl9aEVfO|5WxO%NU!^Rl@>gWQNxspzw%$sGQ^p=?nl|l{W!O-c~<KxVk;a$1wYtOBTSq42ODmT'
    '<o`lq3snbK$0=2*NShB1l7<mQU(ueeWBqFRmAQE_K$<7Fr{9vIr=s@REOpju3&j!Z0p!Ml4OvsI0;(vzu#(X}USK8lclswL+DX%^'
    '-f!;?1w*;cgl_2+W{RSU!$3=<?-8G6uMD>*nH;;p(p>{yTq84!m+w7}3@sSL?Y3nmM^mjPRALO#8N2aXWrkn7jDbPx7+?+zrkS+t'
    'm>edZqQm)32&C)&p#@JL;9*A2J>E<C2qVBM0kWM+>t;GlA_a8SX>@V^(lBrCi$^hKy2$Vz<bwgR4n1wnRw^6Nefh;WOEdGb3=p_#'
    'zL8VozBGFMlhHIjuCYJmk3488tl_;R6&Ri#AhWFaB2X@?J%O&2jCpL`a07eOZdII5l5}cqZPe$E;UXw5IA6KgQ+{S$=Od2=4$|2~'
    '8VdN;()0mwUp?VfXu+%pAL`-cc@bfu8<EJJPDb0ZsdD(QOvU13i}6XC^s>PRbI-yHevEmAotcCe#x1_--cxncP6RGIemFd#HTpWC'
    'g7v@#+`fd_6}KOUE+IV_UhMbNv&w8}W!y+TkyvMZ_c9Q_dO~-BFMuBWA)qb{J`F2c^vYPr7ZxOeUhjn(w3!x4I>=OOGGC-jd>@%>'
    'i1btiXt3*4H5;jdi$g%R_Z-a{%*Fiy@V$)9th&rD=m0y}e&ELkOIsJVXmtIhu4gHjJ0Pn)S;Wqw8uD_1bFN_kbK#msqMfX>UKH)z'
    'q8f#+ySKY6)iYd5wV)G@XfKXLg+fONe3vq;->9?0o#;I65Pp*e5r&3a5%YIzv_-_(z4i{!ZbQ}x!r|5~q1rp9PQ9Ze4qYaf7PkM-'
    '=z(B14u~6Gu`8~%FR>LJ8_jp5fq-_`AA-~eY^+*~D6AIWE6VC?4UvVHRS##1beP>gK)6W1PXp^@q}&OMS1GlwgLf(R^`;-291@e}'
    'l^6{`b(Drs1$DY*R|4VXqDIS7^r?LB<A05+Jy$mu)FfCd;xxl5b))flJu@?~w$;R^EZ{ec+WK9?IcUL)nw{etc5wtln1L8cTPkTN'
    ')DzmwsSBJ4nNkK#ylrp7S48HFQ|0*TLEgSFYkK97&JK{kCuymM_xe6nx~DSL=1DHg*fne=xmocAj2wi7rei$1pNo+t%0y^QQJD>#'
    '*m|;_TI(D9!GMIWwweFcl<~NH3Vs-8X;&)fpe`j8{P@POH!-;|&C2HAx@JDUp|+V$m^n9|4K6yl{ir>yS(u7K1J$v`xQZEbmzs0Q'
    '?cKc#)$~D<cR<d^+bj#wd{?-u)8Or-T@E8PYA}&^_&(h`QI?UceoxwJs$n{u*S|GigY=s<+h@9}p(B*(0W~E-nFn0>5dp8?Ij`92'
    '@NLo6!7b(ZTMd~u)Q7$O>ekjd<7~=qqXJBS;dvaA_^t0lHBT_%)F(fQlFZO4JZ%FJhr~umClF21jQpNDQ%(iBea?jn#!1D5-K%rz'
    '1-Yz}C|k&h8C5&c&;JcahD5B8I5y2Rl6E^bj64uade!mirHWD#)El*>E$f&+*qL6z04t|?3OLd_Z%aTunES1rzO3N&=z9{Lx=ybL'
    'oh6Xoy#860vk*CvWfFKQ|AOyB94QhNxmOTch}P{+_h+oEgfiyp@4(8%0=Dr<3Hox%h*lai`}22{YS}WGfD{}|J88qVW)Dnej9vt<'
    'jQaA$L@A2C&F+6I0q0>bUCVYDX;&T2X;>qwI_Y;&6`0p{rA9;=W0D7SgGNe<$!iwG#@WhaTu&xBNJO7@<R0L_yLb3QnUNasb*tKA'
    '0P)nOR^Mwk9p(Fm1-Q27tPz3upEg$0u7D#J7wZ{3$D|%v2SNR<iU#!S`l8=T_jnP0o9f8YTQ7$4nvXJ+UdRh!t5-5vNh{c1`jXJ+'
    '8Z4RFaPg=x!$a243m=jcE8^$IxtYdn>e=rp+S-!)LhrBXYsoUnNJYkyzR8H|g2?)In1$DzyeH@;;YMe@nR;!YT&0o*Q`uuxUd$2g'
    '=Ig+0fNlY<n*NW9MGrqv?UzTKwlQ?CTk(dH?OlDXI&C~2-G!bqbfW%W*WB|<YcsoEc#=-O3lDmN{Xk){q<s4VHtQ<pVqepwbhDMl'
    'z<^zN5}u6*+i9luK02VPgSGaHPY+Z|wYJ-gVR;<nL^@<q2GJU_+0M^<`$^BpedtY-(;0vC%|<ylMFl!bc}>}2nX@ix;P}&h%qP0d'
    '$k&iST+#e>qpGV*vJBn|A!wenpoqq}a!OSCk9<)9doB%0Wm}&>--M*hcxhy>33OA661FpvbVbwhA&2~pTIg9o9E&iwgq8c2Zf?Wm'
    'Hrnevijsr|SrzB-1`ln|QE#JH1uv`o!E!d4g`RPIN8oV3-@BwF%+C;CQTT!$D2KBWGnd`H8p?jIvH2DDcgMFxV_1u>i=OH7DV{OM'
    'F05%%xl()e9m@I)SwoYBz&YR*UgcOGESgq;jqP)yBWeIA$^{hoO(67(5k}Ym+rvc-GF@eWVa5mqEED!-qJN|I|21vCDuR>yNz#`P'
    'E*39v;!mGT4*g`Ll)Zv`ZKSYmfXk+{-iE#Jf<+v@fXg7?4R8~al=cC7GByE@S3zX^sz!8d*-$|=F_7)VuZSc68u-7UoE$oZfd$d_'
    'FB%0t%~hlei)w)>kV!NkzlW3R?G*d4mU*3E8f3Zu^`JQ~4rxn=aS$mnKw3LS2;0|U%SS&%qnBB|{_39wx?DKj4m6a~>4EQ`RyYR>'
    'r2Jy(uglGg8*|Vzd|8u=Lg>L6krzwmfLcE^$oe<qsYBuSmzZ#>>0j%iFoih(eSy4%NS&;<<<HGbRf$Zie8AMT6uW+ZHQ2^ziwRh*'
    '>J-ximITT|k`7xzX^YlhJO8i*%nH9+e1<u8nK$u)#!!K^h$UFNC&3Nrw<jI+&K=;aii$K2@1Tag)=vRVez-p7-rVhov}Nn!(tH^#'
    'mNUR6{e=q#ox}hgfXi=9O*%fF_S(a{wJ5#aQg3glZFuJ`4UY8sSVuLhpm8vwR)`mz_qE&bJ<{8n^9%beCbyFlHZ0<8f};o#*u{z&'
    'p_c(t50}aE>&FA9ePG1Q6zA`Wq6{MX(Virc3<J>TO#u6&po0LfrMm1oeEx92bbMk(gTrs+bz4M`OVyRx8ZA=iOR>+~0DNPf#ok;='
    '-wo(Il)z~|J^f%#7TD3p!XB%9OMrN=r^@W?-Tpy+j)LePSeMhD*K_j$T2VYll<R{rSSZ;<X@<N}jXib5=?LytNnjs@ldcu7R;!lT'
    ';L@U@mGv%MHuAnS%qj8hW#xpQ^;=WmO`VPm!hxcXr~rHqZEmTJc9Q7Mt;H`Y4sPJ(gr*d1QcA+a2NSgwT%Fa<l>kV=n5p{33QwVv'
    '*y(bl8>gmWnUAsQuM{P)nd0ez>j3$WGtZ%UxsLU8k6P6Xph?~wFG{cUuF<9#D{#3IQQ7!06v=txP`1x^W)9Zq)QgSx@6LJYvWl{V'
    'ayyB;?XRU$K&mD+ay8&e<gh~3X0HfqT(yUmVT0{|WrC2~ToHr27G;q7437p2!llCU0?sJ}3Pe9QCM|s|*9KY8_yS=i?EsvRm@!j='
    'h>@aMu<(cMhGzo_w;hVhEl$j_y|ETT=hcbVL6os$QWm1=)1>P96I!d~$G*~_ev+pWnUC>2@*<Lu-B~pB6~Mk=uSgxnzK=g`49DH@'
    'ZiCTw|B;2XMtO<XQx4z0o0jBJ$5ph|w7)I`zKsf)dAzmd7i_m{K^8_-Oo^sRR!+{>Wi+6BB-A5HsSLgB^t)Zb=X$rY+jEE$?Rkl6'
    '`P}Ga&pnKIVwgF*dQ#RLFSMH~=PtGpK%I^ZhczD62vP0DJT?nK)d;lOr$U9!UR1jl7sWZQO0s(a1ItR?l(3{H8>I?c3io|^50VMG'
    '${is}xhpxU&ByA!<VQKuH5hWELIOanP2DeC0QpgvF?FyDj|-9=zOcfWjE7vpvb`P}l-q{f-lqCUe&U^LC-qTs_-<_d)7=yO>y}&#'
    'PB6Z7kY=<Of;}V3$KXsX-x!gZmt(9-J<oy0nNUAVStFQXFf3jWuQHQaU`HH5I&$(jfOrN#N7+c`9QU76>&Wq8K>+}}9I9jGbMSZG'
    'y<AA(03YKqxfzsF6g~9D#YY(DR)C9^mFfqH6?jwTgR<1`?kUb(_a1=|>H@uR+ZL37hm95n2nO~KY@PMIL71T-rTC(idUZC~x3K-C'
    'W0zVOV`9sW<GOY@;1H+(36lJf35CdU-+j^q*RPU=&y0|*0)tgL(YN5okpPOh(U*_Je!e^)WRziDuW?g?>b+sDRzvj8?l_l;O7%V-'
    'Ti9s#=(<9zX&AU|>YYJw07o%uGT_tC`*X<<sDN!+C)YS+Hh6C9yJnL`N#js4UN`zRDM9p9Pqzmhvn-X>hLh)-5DD}Pxq7~v5wiw9'
    'fO1~nvRb0u(x?c7CKvva4(2w`7B?lT@<C_69J4%Gu&v!l?dY?<-k(5x{D#07p+$2R+8lmzTdb9xU94)IFH?zB!j(BNtUn9kZ!@Zx'
    'F{yN^n@oCPMB7)=?7LpdWc}+b12_>D9yzRpN`n+mVD&7MB0-tCm5h68O-2XGdAFYu$#k*h*qj((CHh{pVU*N?bOSoBpKDnei^{vt'
    'K~;2}aR7%f-*9H;#eTy`F)nL5FV|rwcOmhnHMVY4qitp>P#)Iqvu4sr=+@Kzyu3UQ>d<ci{y_u85o@%p16WEw(o)~-eNK;HH<*HM'
    'n3GwTr;@Q8UjkoQm0k(LJl9t00c)p}n<}%cS12;}%vZWSfxV%!rN{g24FT9Y#kmu_IPrNqw_R_seX2eF8`QVdkBJo2L6`e{{NZ$X'
    'ns>3{UGETqLG)g=kQh<*P$Orhacfg~IGHLaxv(F4XDJyHsqo(Xy&Q@gX9w(dJXXV=PJa2O*{4|3=g3D8;{|;f)h=J!_+&;4t^-&4'
    'sn&_RQ%10H_;DHFWruyHijz&|#s}9#l5!mUyQ)&jNZ&eXk9Lv|-Nn=LRDPpMW!5GeD5*wveo?!=7eJEqKTakBaWX?{<yd-%7&;L1'
    'ldBAFo&gv^Mch3NN0#exmoIIpMSTEg22h>*G-Ji!&T#G#@)I8Ch-j4RlNmUvgu(=aaIF5;XFjq|x>;(Tx`9Uta*D<VGWUYW)|4Yk'
    '^|>CUb|AX*F`F_c#{j3_LLaEIjv>~ZH-Mv~tRX<^g>k5Rg8=UN2*QeyS8eBb1A7=i!MfEOAeYeJmSyFWrYI-@BhEnEQO874rN<S$'
    'HDFEu6>*8BkCfSa7lBK4)NdspW`JuW>aE5^(JUHv=o8)GFTC#*h|%SQyKJixQa?7HaxKCf?UP(uo?=i>ZLL}j&`OICTwQgv--?-B'
    '+A5~qe61I{@6&3@??uEBwbkF`iJ)mMS5P?>`Dqf_1pZu!MrwJu$L)QhI)I49j)p-Cf_y074u)JebXLhTT1}0;r1800#ZwJ{t%jMh'
    '`zEGOnU`a8(j2LAKAk36>2Rg+82ajsU+ST|DM*YefFEtB9+iPT3cc$|j}Vyi=$JYF_*SrrEE(IQ!JD4#O3WBcNpaE;UuFSWHEJ!q'
    'R=+p7gTzXPRrL7BBW&mk3EO$yiiXYPymK{t5-<^#gcJovVwVnKc!c@dH9c1Z9HF#<WX^fg_`IUTzMXQW_iaC~v;q7;(nXeA08tV$'
    '!<fX2{HdP}1*sa{c|*o?Rd}sXxJP)PaQU?m=q=uE%yM^xnY1R!Vg?&!vvIsXCDtz;<f_7ho2^TXNk^C8M^S3z!`;7;fsbH{LF%kv'
    'T$pH^i<M>hD{jk_Zy-wl5qvqZ9{^yn1|~NAzq}(;PxTptJgUYQ$Tfzz(zbhJ9QYbt7%{MeHhJ?sjeL|mB7}>80Rz|Caj*9}t^G?%'
    'RLH~;i`0FniiJJ0Yyv<P#Jcl0-+gR}={_Z7Ko5*hRC_3<#+l}b(pIP(?$=T>RuJBme|`_8Yr!b8cswg6a`=`Ev#JRrjH#XnbBVR^'
    'U`=l3PhNb-b*nHvR0`1f1$0_$q$>U4=ZU;hgdF^9b;BBo_2=(;AZnA(=}P<K9cxJncwV?nzX4U403QnvUwm2{S|isfX~poR_rV*^'
    'Ef30^iFX?oXe#!QIzwUxyD#vcAk)dt)&2@(6WgA&enbB>?pM29%;t-5^w-`vHWnzl93tcw)X4t5uB^R_s081r*M1^_Z$ws7JAbA`'
    'YR$1b9O4fhh8KCs$+!Vh9o@^WnM?XCEf^Srl&*Wr1pq|!m(focEThY3#TjDIMnA*bRJEzC5FHB{$41Iz3dtacl-Ydd@QD116`F#l'
    ')$!Ou!a}aTe~i#W%MURlPp&L$HBP`;U@IO65i<4-N}VOQyw#n=7BOqBkpJydMyIZsJ+G}YSW!i5wMUtF9>;JXY6wF+y@8Ic3G~qB'
    '5Clk;*QcB>S}sCqiWB1bLI8vH0p~_~pvf}NA~7?!5+KwX@*<j5tH5N)O@^j|(Nrj-pUXY4XR?!WumsT2%}&&T?dP)#YNLKlpWJ#8'
    '280JBy7{fI9};wyBtb%e>Q&fy)yIVV>;(}QmXVvqmkLm9uQ~pDU>!E|V4F$^H5NF*j$9D0hM?&XR8mzEW6kpAhU#c42T!*g5|KO~'
    'Q-pKZ0m&z{MNY}qJS$%+3;)(m)aeeNJBv-bIouzcA~l%&CdlUv(eCtO8V{=h2nL)zoAO&+R9#WS7@*3u$*L@Z(2xqM_%B4%dnIQ{'
    'S<j4Eg_D&)iG?seEh!xbFkP*u_7gN%jE|pZl@;@pu9aG-9Q6|;FEU2$T(IWgy?1tBcq6lec8(buaH%03?yq3{ej8Dn{j-niRe(?M'
    's|kBH{CJT=Zn6h?M?WVUmMEIXdI?ZYjY`bn589(@*^1#9&7k80#fVMkP_2FGe{$z`%^1xGjuA&@U7>nPRvIj&6L%sEtZx0V(2MG`'
    '%$?lDA6%wAM1Irn*-sKdcPGfToH_*x?p=Go1@33v<yb7{SFl>lpXWwL^mT)gy#9}Gx7#xW(aetFKd;?0!72VS?X%KYSi$A`%u3b+'
    '=W=Cc@xxXUJQkC=lxAGEddtH#m3=BRqw44Si!K5OjbKJY#bH3^1x{qx0pq;()+mMH7sz+h$NJ08$dWdX#l2=-m_cxO?^!XZFRQ1-'
    'eA1I$o`DL|0E?1jn2ILZfn5CRi{}hxPxse-pY_y*tm^s!6VgUV3A>I78+;dAy<{}Tf0H)dbhg9U$XmEWa6EY3Tly>XG0_PyGMi3y'
    '2+?_fEBBEAG~35`)!gw<3AI4=x@&KWqSO@k{qm0`fH^a8NKd8QaA@?9R)aB@7lw5uDTYupDNR31u;V`9M02f|)4t!9c(M%N9G4r!'
    'q+IbW;DNwE2l4Xhf<q_*`EOh^XTZZGMvytfA!RD052eFsc#GFi<6<{R>X)8djizFMD$rgoJVi3vD$C+LvMgatP-g~A4qHx?Wh8+Y'
    '=BkNUar?q>PcilLPkTN0Cm$pR45Vc$%KzY71xs`=Ode>vAq2OZkEFa06J$@IkE6nk4p8)=(G~o{pzCSiDSQ<m2IBqgki4^~S=l@N'
    'rQ88$eGR^w>+7w&&F3U&8<wmCT`4nxCmWh#HI1YUXOINLDu?@C_?nO!wuWUARSd*K^+~6-HI$N)+N0+AQ~u3PbQ_HG2Ly<NjEj{B'
    '_i8s-6@mt;+}8;|kb^<%uM8BG^uEM{Fia8Cnv&Fj^DwA-RL+nzVHBBrs<X@^Qz$omU?PIgUrM&n-JV1uGvhBhh#+%HMbpMi3UNhQ'
    'dBs)1!uf>FErL+Tpr?`6X%RNLhYG@p?52v5_FB`42c?$tEtU~fnW>1u(Z!emOl_C<Cv|XzyA3K=o#R2s*Sy&MDP{&XW?xghu?=7t'
    'Y+s6|oZm7s#C$Wc_6!Igu$*v<N;KgvRjI1bjL3*~KHJ4p$q}yqIIz9YiNa<0g2O8l-22^DBLikH$~DzSJoNP2s^e?OA(gQqm?se6'
    '3@_l6dr_JFpNzkYc@oj|9x}R74!!0O2HXXH*BZlFdm(5OE5#i1(4a-`3k$;FtxZly))W>9!WQe4hLzksf$fz318Y{Y18#HdY%JGN'
    'QeYugWWa8AVtS~Qq(gSgW=)_&^j<*(!E<lbS#g-Qrp0`6=S*|mMqRI*M=L7TUw9xZ?F1DCA{N(eDv5o8({6ALn$v!gv0V9zH4t3V'
    '7*V~@i#qgYeo74i(t%qQ0)0XOj-DUucH<0jy}$q&Fq|OW?I!-11}czso;A(8ylhOE8ivw3imwZF0<wj(qLRiK<=G6RW^*~FUbmMI'
    'p&b7=-_wZ1c>m*_l~FM#+J7re(h|m#o`+CBH*8pS*p$@=kz(-o>hGE$tni*yfY6lNYF}CqR@&Lz0m-kcBc7qQOiHu>w~sO_<O{(0'
    'bOabeQT3(o+&Yl@L(`lj&|A=VOg;=dA4GkJY&#xPWc{HVTl(P~v60rFeXvv*;H~26o5;C+O-V*oD3E+blg~{^(z1eIX3v3(us@&;'
    'eC}W^scwcls+~k-2w;Z!u~Va%g<wI&L$MyZh9gIE2_8kuz?@lVa1*OH-A4V2V8cZe9)Qf+KIYTxh)(DBc2DTK{jM$}6xg)yY?@FJ'
    'qwFgUHOk3Nn91#}XZL_wF3rX<g3QnrfH<zBE%PAKYyJ7DMW)<901vs~Dd%<O!?2s-?RA%nPQC@a1xuTDE+Fvu&wXyn%n>yS_5d0w'
    'zRDhkWj{jIIgFFAIn_s31$LuW%rl)o4SwxWf9pJjHEci%I6*R6TnAaoaKZOrmWyR;z>qh`D-R;65Frap0o;6H@?Qcc#rmj{)DD%n'
    '3<w;}$E8^Cp=9@v{}INNcid;s0>=edRK-3pgfchv5;`AsYxAX0w>RiV?nY<)9MHO_+plXG!>PSPQZfREl~mQKKc7-m8?4E8dBBg&'
    'GfcF(ns*D78-qw}_vraGHOGz=S|!X$lS&+KaOp<{AzPC{w*Ii06ca?wS9WZ&1y;lx2{nlCIVB9)B3vP<`+6HTRRrX4S+5=$Ta#D;'
    '5iI6DG|4<*(#OwSUM8t9S7B2?u05P}`S|hX4A3LlRPLmbjuGo0(I9--4vJm*=O&x4W3cM}!mBRQ4Fku2*h*V@uq8vNL&$A-dds4`'
    '$k?5NRO`7j<`@{xKo%mxTyZ3EaH0jdQsb)fP+Tvn4=uZvws<B+&0Do<)71~6@>@oLNnc72SmvxrNP_O{veJL1gK|R}MYb*kCQ2xv'
    'y4w`fzqXga<@5$l@9&B`DRg$jD)0pLfWOm`S_nr}3()WOZycyt!U|q7Yl`XP;O)rVVRqs^B(%TL2;3{ygR(g}#vmo}JiKH1tjl$A'
    'W8ZXB6oY4P6>5q}snt62;N+@TB?e0X$qw#c)6pnO&s<`fXe%vroAI$babbWU@N%ONhKQ=tv5@X8smBjPoXG!Z-8Kd|6u&1jxI*-j'
    'z+`O^1_<l0r%YA8XC|~a%P%MmiWqiOBjF1GXRZ$kEn;W=ZxO|2b@ae2LK;LqJ=EF0@&+M>AZRK1|2Cy2LbBz}TqZNl?gNCsDu5OD'
    '({`C_zX?TLDPzq1@Om!MvDx7{&3GKCLfjze=)9F`a8}f(6q_XxjNDYq2y7|wD*Cobxmql5`o<Dk!+zoC4(%{pi^apIxB6wjZS-Xe'
    'dLzT5z(_XRJBR9a!DD|9+W~F{UexNdT4A}#1BImibBv}W_Birztr8?sEgJban;Mq@GC;#QK);byQzR!RyyPl**{UedcUHB-z<VBS'
    'Fr0tPeC_i!&SL9z#^bAVwSWCXQl)GNZgRxED@)@Myc+jX>}OOM(D(m)jml5)#U9oZE#kaiJl0|h?zuImXl=SIdYw<O2&Qs!Jk8I{'
    '1~C$1NfZvRHUaF9U~k4P8Rl9fp(JgH?lJ(II|V@kQ@(YhHtJ?#<Fb&mQclL|W76FMvr}jze}C2aAv1u2lJAd)uBY_XrrJ(=ig#oV'
    'd)Mh91RM52d%a_K8@LBPQ^G_HKEsTya4D<-)p}9#!gIpPj}^OVB`ot==-qOIcY5jD*BlNOS&{=D)%(+egPy&WB?&*q2M$w5hwH&`'
    'dB5@;GYw!I4!;W9HMTZ85ZF+g(eLXs@LhRfQ?30UQhK!nV`OMNq@}duo!^#)5pZS^-YdAAnSj=z3M0qn-6A>9*yJMk--=W|OFEf('
    'sG5Vsk=|R`JXWsV)^G_{fNloRbW%h!WOI0s67|fy6=H1LT+f^7p!E`2HO_<qs>tk^;74P`_;?Vm6-LWW)7^<Ad@da7>t~uy-T$N?'
    'ZDl8Gv;Dq&HrtgDQ16t3M(5+8a4@I>Zt-H1LXJzmNDdVlteEfQ2xRj`Y09A++z%<wsIh-GBfIyMLaE(OZXbT;6nz*Pidnno7ZS6>'
    '^|gf&%Z`f61i|FlU8|eW9L^+-Z&hnU_x}9(p9i=ju`8-W7qI6=GL^$glr=e{58>cM2q&1+_B}UPqFh(4j~XCq!>l-u6;qiOOfZEh'
    'Bx(~sgc*2LZ@#Te7o4tybc<t{PK1$y4weHIG&X1PJP&@CxHh>!!oNgS+7EE#I+<~AoI1@XL%MP}W1niPP>_fNoDQG_Rh6WIw11DH'
    'xt)E!T1RTsK?=%52WEKaK2p;z+qf+T>Jzs_=9(p)1sc=ZxnN2v@_AF8c9%+Gd^a}Vfy@1L4=!(#{7Py&l<sejWPF3Y7g{q=neMjx'
    'ujATDKTPo3)HaaOSkEONM3OhQelh(-%12oVz+77cd_Ta?JiSvT!X%?UUCTd+>amsy|AE$@C`{Wx7b9enwwDO=vX^jJF|`9kx8ldN'
    'kfqB`TguQLGMODc$zuYgzQCU`B_mwbfmCMZY9XL1RD=KRDFIF+mAuqtkBauRxyA!vH1f(GPI#L4o%9|K_5A#*B7t)mY$fvl`NE~-'
    'Z8x!&=w_MBQu{wKAaqI_M$uP6{OTuhdj@4KfrEV~W!w+r>-lt8r7@mh7$b*wHv0I?VEkx6(jWbC`_L6PH;Mx+>#+)#6S-J#-xH^8'
    'ANqa?L{N}784ZY(fOm_K7kB@Y!z-OiOML4|1}R(jbRGXSIt=cATzxi)S_$qYWm;tjD$aa?gKn$>B4TAN8P18nJY4I59HE`QkB^4('
    'N%}AtmaIUkk@)5^Vn#@qYqG-MF;gZq`9Z?G+KNuzDQEhqlk?=JSu)HU@z$VAZL|<jzFsprIRM2Dh{i@*_DQh8u4<2WC8$PAx^|1-'
    'n?)z0W-Ehn*IHn))Amy7oi69E+VJ$%OQHuq(}}Uj)`GJxsScrNDgNcnxLY(J;4}!W`**X9tp(GawtvVLd-ik$vYqrB)r@MbGuB+n'
    'drO1F{j%ta>1Tl_$_AkFWT+kp(SK-1bLmq~<ig130<D2`wErQj9>X$e=sp=T#Ynw@kD~t-{J0zwB34Nj4x7%Br6b0f{psKQkTtN2'
    'AK}~RFA3H&De7EKo?@RQ?syNrAj&r)lKQis=64QrA>PZybz#?!pp?(0yC#*sCieH{p2hRbWaF7{d!~X@a@`S1#D!hN`YsQj-V26h'
    '!Dsr47jTLqO)_6xlr~50g-)b43LtOuv<}NWe-tV8?uul(My#6Q$~=ZWT=&+^80hducUVC*oz~j@kY@VTn;@@5qhs~xq?XM4G_%>_'
    'Ir2Uo@3mxdJtvbEJ$tUQ8Ya;y%UW!i*r~k(gFV|Qz?UofD?OiAkABLC2?DeY*CQ|?p1lgfP>6+Ux_Ma8B2%3$dN^1LI~}yVu|y@o'
    'd<n+et6sc7L-d{fI})B1YY+JkadS`hU+Lu^iVn}{Eyzh<iNY*^y4(XZP`xH+U~R;l4C^7f*1+P&)2d*RwCw9H$ts>LyGwx6sv!b;'
    'uA<)7;*jDGy#D&BPT+(V_frG7(k}}n!ZPp2bS<VWa_0A3x!CzfqLiDI0P_2;xx@XD5upsN`$LjO(E=b#N0d!F(#-Wr-69LA@IYW~'
    'NIJJ_nTZ`4JP}b`D)DPRh#SZUXkyTw#(L~&qQ!+@Opn$`bBOMK4V`L!_Vy+(l3A?Ra;m`Ts);<5d638c&`};3ry%k+<5*LJTp-0;'
    'dPZtnn}}hr_6XHi!ca^pL)`E}-1AViR+4^*E^~7A&+V?(TYQfv7uWqYn>dGRWm)R!0VubEY1-_q^}&6S=VCo0VY`-d8*FCfRu}v>'
    '^H$2<TJNYLJ$F@`f9KC#G)}P~Afu4XP=nBpd>u=RPwSZ`NLwB_%AZjxTGPK~!h~+sE<x7=FW;5goz-KVLg?t61p0||{dbav40e~;'
    'e(_gVS_l#}7~y@^a^vO*;=!fb#oMjNFmu=&riBH5xBg(fF>H9ekdw3L4Cg;Ekkhy%UGZ+bn4=!q)VFrjq67q1PFx;|Wjl(c1bD(-'
    '5~5Mlz&-sOSHl80dI}SLD<WqWiZ!E09R*kH50PM>)-A28()(KI+fz6?YPd+%I?gz~PdCD^LZ?M!3*+(2Kb-<Hd`S{bG?~WJaas&M'
    'YGlxe`HFtcb_lJ+Y7-6x=03%>uJ5<!4ZnhScLQ4ObWYIY^wi7u32yvU;$sk9U&>?-_^GyNcn)jB*~^65ma1uhjyP~SNdfEbh`pnM'
    'L$twYpN96A>&qSV52;)iP$G`hcjGVm`TQWYW{Ie7n$&VtD^07&j=&nqCy&DdNviC}G_pD3eAo5Yai>s|0`V@~P7-mMuB85|8QFt('
    'qYXUeoG?c@5V?fGUFkh{EOLI+Egxw!#Um~{lzG%PGIvxK3=V*{f>fzQPOHuBoD1uBr5=5AsfP=@&>HbJ&6)1!;iP?6{D;AVsw|^!'
    'Hm&4yc00aJX~-Ok{<lq192qS^z6>}BSU&7}xi97TavP8fApPB<a2!s^%huj!_Q24Lxki%ZpH5C^ph>HxqBUQP-snQ-^BkM2Htg$w'
    'cda26QNz%9qs5rd1HvIJ&Ka}MQ0@pVvq@Lf8J@QL$amVX0s<o9aZSa7u!<F*-A|NA4}A8z89bgopkn($iU6XoNSkPs&5ynWud>X^'
    'J>gI&0>;6qkU_JD6!gb=+4Zr78!qUYFv*;n4%#FACdqoVxSDc1t`XtJxqxV5xA**hiu&6uJ5k?n)uSKklvoG0WlG<6rR@U3*qZma'
    'cgN--g-+^I$!b+&mfZ-m0)u2o)s99|J??p!W($CagygR#zvd1p;5k*FkLv16$4p8ZKph78ZD;9|OJKWPJ4uJ3R<UQkU=FAzX}rYU'
    'iS-4&lwwnRsR{f0Oh2g8FkuKephq=vLAMS?P!oZrUXxO#U8}y&i{|F)tLS(2ZQ2%i0%t$uDl&b9e0oLKkD3l}VGyB$W@7I{wS>uE'
    '7fZE$x5THc_Kbyk+0N7%MYOoRn}w@8hG}8_iB&@3rAlyIR})S*L}0i&RY^OsuRkqcD2u&;JCQ*lNVTvg%J6enDB+sbY!F1#QA0k!'
    'J4^DWJ<R+6>H(ZVj-lP|$?<4hJ8w;YaG=h(AjUH7qE8_|ns2AkXp%tIIS-zf4LJT9NW3SOTqI;2H%Yg%0Jel-&@g4k*9+F&DlNFt'
    'fn%n<6LT2T(2&jXhZby>i24&yD3UvM**gx|qYhS(5d|ieO(z{oF2KUQ+%t}C?(AX!5%^XepeZ`T&d5#phZ)i$B@G_C{2)i6Mx)wL'
    'NH);7)P+@J6=f=>25T03hA@pwGBgcy<m2-ZE8j4=O7*_o7x;dp3=BJMzp=MY(b&(AJKaq-6`_~5$p~z@uL}z_1+cA(<K~`G4P2qp'
    '*WGzrb8XEIC_Zhz`4!dVO<M3fbPZuHDl7w;PMGsCM$1)nn+y)nB%v1`SpY_-iu;$g9tB_|g3zo{kkGtdtCYhROqg%-uJDGmzXu8r'
    'zqAD<6WPj<>F9C;laK1Al{nV{f{`MvZJo~gAQ+L_Wg>8vs5)v(pbLo&LKuxzU|Q*EL=)VQ=b?qM8^9gIA`>e@araWLCytQsMlh%('
    '<oIF+2cizfVk%3(ndYG-&d?@ZvKith4M|wHt+Mc~>6z3$o2%8RYb1D?&4KkZUmQ!n7t2N7X1v?0{?#N{@mPK{k}3`rr+l<5&JN@%'
    '#-qArE)eT30BacUj;BRK_Qfl7f)a9gge@4LGJ4D{13rcaR`*R6!TExtM~saV;}p_zQs~%@YNfjH4@x}70>Tt`ga6E;Lvq(qx)(~h'
    'IRpm6P5fWjE0*fmfqF@)Zq8?AdL&!ga|DC5xczG%jS!At^kC0K7l1q9_&A}6G;2N@dC5#wruZA`JFcXU3L6$0nm~Ot27>o}0Gdh<'
    't$XqF#wc?c9Q!zvry5(e4z9cjBS<SpG@Eu*Jg2rE2!^GewuzRs8aW=G4S`>zAA>0_g~gy^Gf4nv0FO#xr1q5WS167A55PL4u*pya'
    'er;M{sbea!cd%&o_d7LZ0rdd_w$|MnibfwV0I@cLUW_^qnXAyf!in`02SN*XmQJiF3@U6ec8`PhAlU{EUu4_~GzR_`;ZS18SbXa%'
    'SoDoY4=pzkOzrg}aX9O^m67euf&TFFGy;kYb|7(KVp4FNgfqZ^Qeuy;f&MU%(`V^0v$3%OrGX5OvF<T)=ZXUvi=bSJF_Gccx7jlK'
    '^**+#$p33I+-egKlAOmk7r6^QIj}%TMkZ->S=B#AzKer_l#c<&f7{F-QN!LVX2+8`iKYV3O!Y7A@-{eRtL~ykCpJ$lPBP?@1^OPf'
    'bow?=aRpk8Lue&6H<N6Cn;#x0I7q$`jPdgU<YGKf*x?C$R~T5R!iVB%nGN_eWfifGbupPm)=e7+tFA5i{25ushm@6^1XcADkGem?'
    '`m~keh;0~)0ZLuWW3F8nG+j%9XU!L{08Cd4@(}xFO4<g;shT@*c2)bOBoR;^8G@42kF;<W@lvjPtlHkgxQ$HjFfqPB>Ydpj+J?9S'
    '!u4)w2?$nwPVTwcu_%-(oLOq`rnp%P7^RxV6CfRN<lBmEw5|JNczyyjaXX)o1i;Ij8@S4`djI?^efYEJ%)!Ty)rf4=`e|*cNl&S2'
    'v*v73CvZe9v&AxVx0@P@<1WAtiE2-zqPr~_fi^en*9+?afz0qcFLni3DvLBrRyWs*zs{Ewn&~8xK*kBhDvo!;<d0Mf3>+;^jWMoo'
    'v2E<~Pg`3ojA=d)QPuLQckDI$zylr2RJvNC^i75n5`SzE=T9nax9;;7aZBX*5>RV=FU`hb@F12#I(t9x#36uXIB$$?1qXkICj$|U'
    'f2jjQNZQdfyaa^R)0iMh{S@rSS@x=nXeq+;7Y}Y<u`t|k^>`bIj7{#H1F`Hzi11Z|q!u-fhS`oM@hukI^CE3uiWyN$^DFcgIeqt`'
    '<p9<Xv|xJddZG*-ht%8*>NND-N!K16hs{IQi_SIohVl2POL*PS%U(mN=s(2ad_EcMV!>%8A}<sf6R3}m9NiO_5XbDRhbCe95ob0w'
    '!BX93Ljb7`Oac=2q9r1>H1ixxIxX$zGX9T^{t?WH=NbClq{MVJ&7$6?rid3RzirD+D9b!t)G{7u+5WV2(WH#R59qxKk+n=}5`L<<'
    '{EAuqRkA(FxoD`)vxuY+0upy8=lXe3^ezG6rQJBn+;o_<55r%eUExjh4^Ti!Q<fEDWfB`Xh$jE`Da{sbfu?OAJPaxKui)v%7iEH?'
    'LqKe)AIysdCd54#B;B(NRl`onNt!sIFZasyxwz1X@BHTmx2$vWdH6v@2Q0iqlCVHg9N>t*A2?n@1sTic2kFt%>K>^Da^-|QOh41Y'
    'hbE#F6+!%0{(%|}KuDy00t|iac3%(Y<&e2&NR?RMs*$D8ja5hHJE9Vmy^r`y8RpjJO9)WI)>G@w%Wz(0V|e4M=AcP`__qttsjcBE'
    'as!S%7TlDnHq_zp9HTn46vwA>PZdFxpjJ*8XHPD+q5&&fS^A3LX%iti&ml9*OMWHYu|o(AG*p`|C)Q+J?pI-4KXpb6tbgNq`Pg_8'
    'M+$lLQRMF$;JxIDz1$Hl2a{oXC7@&t3r?0*7Isd&&cZHR3dwJwu0%u4c=bSZp<&w-GQPH!EeM(UqRR15(~Petp%#{~9(b048e@{f'
    'fn_Y+Iy+tyKES%Dowus}@{L5Q4L|A@@MRMH*$OpLeBtv)PX!KoT|SD+yYMExxeM#qg6E)079>}tfqUNh-WE5tVuNtfjaTo|4qXI5'
    '#ldd>C5L;*8hwxt5v~{1JlUB!no4~d@HZ|RW?AvaVw#K0Qr6qTK?K^y-<#11cB-!!xdBttydfZR)DX94nqW9szkk~6<>RbtU6H<x'
    'Y+LwQ74K%`_z?5z!hCKZ%i#IYIul!*f#%wM#VV*D3gi;HXaC?%kqt2Lp|v3Hy;fHrW^Z*SMm%eG?6N79!<Lv#m0;T=SrGzEfT@Y#'
    'bD4z<`;1|hk%+t8DKrNp{fcZOiJ{h#&tqwAzB#`QI1=JxW|zx68|IF|GuOa`rAS@A)_3izVnuss?b>{6TobIRPdP^x7mM+g!<M4N'
    'M9HO>z#>>G;0-6fPFV|#952?Coh<TqjE~)%LXEsbzSjH7p@7F-){yPYHekom7&0*m9pE18>5i+$yvm0NIa&Pu&1`>wg94gUvvC20'
    '`3k_pn75|DYI=lBCAKR-4zd*k>@_?6xw`$N%VH)F*@<Wr6jyNPpp|GbC3Wd59nBrE^`NcA!#Z>Q9VYQ+=8TT}1EB6)OL(lo+~dh3'
    '-2xHBbTcF`p+Cy0_UOEtFV7P#04TfZmn)yTYAmA0yN&$|;RNi?K$Rg;-^CsFo|(xMb3xjh@@@FrTT7;eA>i_3OPM1Zw~$VLnb^P('
    '^LK7WD7i|V{Z4FCW5CZ&e16f$#!wHKE_>v6dC`z--fTTMXC!qaQZi@}f!>fUD&K{%u!=O^SLhGgymS$<socSuqZxnqY(p+Hx#Z4p'
    'j?!<}jiR_6S4S8QG73ZNxOb9v{o7i8<;USI;>pi+Mc8tHxD6ilx`B%M@<pY&BF2KWiSJASr|q~Qz~`{j8S4jJr5trktKM$)%n(Aa'
    'l6@s`JR&2FU{?Pu8O$mGQTp<|S8WZST<ZYriqP&_l6$n44sk6Ka&<CPN5Qtpho}(mfG$mc#OvbEh?TN1+U?zj(*U_!%i1UZI0F(l'
    '=_=MWZ`_DBA>Fd|S$_WVFAsE{s{h5*j~&X|qD(!Iltz<I_odF^c$B}Wq<A*L1L49sHbAO3OqyR<xv5MqEQsqB&*)#kjP{j~<>yKz'
    '1Vh!2zgXJRM#ph|l(?YtLOL{<5#i?&-C+H5*lqe=lKK(-8!qt#9C*PTGUKI4qfwsXgT92@%fWf!svB9x$$A}{bra?&r+(vkO^!=0'
    'JA@!)ufSlla@e>O2WQW^Qx#8;B=b>p%RO3ZBK-hY`P$!1=&(bFU(hLb{$hqK9Z}&Gcp5gA&+y}X<d1YDIfnPod1tt~5;S}^=gpYd'
    '-5bRL(#e3Lojnz1=`UFg1JrZ0ko)XEdtU4++Xvcu^#oJ-p&JZ}A(hp_-h3We32)Lk0_{dChUPkPBX?aGLOV%H0hg0n-HV8q$=)tB'
    'y-V}Dr1BL@L67>?>T@}Ukz}34XE8RS;#nH5WtogvT~GLr0=E+;sox!C#gL0Y$BmTE8YBj1y~D%hoRZ#kZhua<iQ###6XU3Xq&JXO'
    'UWCoukG>GS#@9wI8KdOObV`Y7trfBC@5eho*7i&vaJEUg=ga)X#@y{>o?t&=h*3vIP-~Tywhr^9xlpr|*PrlG=bWa2*DE8z<pw1W'
    'n?QKDOWqhxiuWCmLq_$F&>)eqUiGkDULI&|#i!W#4ynLil7DJ5tE1UAec_|RtQ5T+cDN6yh7ia`F47{wmVTsPHCB9kPs2>e?*#Ka'
    'Y9+MhZ4P5s22p7qw`{i|e6eVoJm}P<vJ08SbtS67tYke+fa99P_G#1AqZPj8Y>^36h~R-2(Fj|h%pb5p;MkKh)%*gp1jIm}cgdxm'
    '4};}!=Zri>e7L6Yq_r*eY~ssR`9pnIT?%(xB5V~72U|2+w9yAkO`h_U4aUu<^Eq5QnOf%6+{=O|xVB6&@e3)m`>RE<QEui{y;tX!'
    'S&pc%3plIUn&`G|1xt5ungmR((CQ*_<j=#!`k1t7{y=QH-AS!#AGFBmxilWB+olG6<$uF7wsDb>#(jO%z62pHBP>4&-XH>8+lCFY'
    'q8Fk<5gIPX4Cx^{I;M>caZy^DC&@l*pXTCYDy9-w!lo+Dq6@;50`F`besZ|@luZ#3HmvP)RACr|pJfVsip9c9%eumi(w|?hxa|Ko'
    '7&l_8ba7=a4$kf=VBE){a>xp7&~mo5vSOPCvXt7XHdMRR%p%pn=7!fx@gynQS3n&2U?J|8z-+}aq6>lePHs@Z3Js;G*@V0hvZfnM'
    '9e)n@jZaYX-BA^2dxE*CQcOg;8vp~cIpf^4fsl@`@8M|o)Px&R50C`T@JKqYm*>Iy5X>dUaHU}9K>nSh&E~?sht9wrsSnUBeXHOL'
    'mLB)mWpcGceGw-o<68(VPTwW+pROD&^~<paR3o)sTho=*Q$#-jZr|?bbIjyh$&j3h*7xsbt0H3Ek<olG1m-NlwZmxX1Iq_HL<j)Y'
    'i?w7FfCk%87(rU`ham0+v<cV807&ONl{CjQ0RSDba=9D^I`%3m&gay>cyy^i9Q5$jKqLsX{xK7YWaDFZ>>UQ$9+I676ar$zw(jZg'
    'pXJ7IR(ylH)LpbNmO%=qST;A(I|AfF92?52OX(I}^n{b0%hc7@E293m6Z(O;G{{D=?d{9@Wpz<ss^EHgfi(_bm4ERtfZtAE2|ZkN'
    '1_NJ{dgBe9D+JhrIzb%C;`cTi*2`l}3CR8^6U3#@Re7f=VZbMu#9#+@S`ectEQPM_#F0Yx5enede`1e01_&3apo@H;ghUGIP;Jc<'
    '`n>m~{ym;V*T?KJ3i*K_Qxjhe*Eu{vi;%6#Utk13Fdu5?-MU?L8eS6Uk~^WVf=NI-)2IrY1-S8hOj2d{N68AIwWJ($-J9hg^g8bD'
    'G^>(#Vl5Ym)VG?rFxEU;rl`yM3i`V-EDNFvkF)N^?foQBH%rJ+u4&$<ZV{g!S)h19f3S-rn2U%$Ly(*@Ll~8c>eo<EA$B^M$<<!a'
    'dP7sK@_Asg_N@(MH6IQJvMZ$VQaR(Cu|<_Nuq}S;lpp}(Eb4y-ZkdyeU>NSkw5?lgy>hc^ygc-NfshzEF}v6U>u&$)JYoiCk?iWA'
    'b1C8v{K8btA|HBONyER2c{nPLfniZ=VYLC=g_&LV#}wh}`o`&ny4|=+icxH<wvUzjL9z(z_d`><gj0O=o&7a(fMsj{hIqwe*TQT9'
    'Gch3NLCKdb*!;1iDF^>j*$L3H-+^HfG+vNw4ru|{juCa9(|qQLb$|rQwQ`>CHuCmlF{>07H%W%mFJ_QH(-4Z$%z7_9Y}!;X8uyoA'
    '!hPrqg?3eX(^=O|7g}`U@4NB<Y-O*_h9$*3v<}@&dceRDGPAJYMn(-H2-&l8xLeDQXkh@`){iqXY(5;1bt{Oo@l_OaOICabGW>Zg'
    'hE?s{jK10jo13cx#F?i$7YPv2d=xarL#Go5y!RA$JtVuzBwY`fULHH3mtNmfXH{q7A|fgke;^+bfz((|8e{qx<E^bs5)tDh=lfZ|'
    'eI37FqaV2-Kn-yoGbh`J>U9!FTBf3wxkvB$O%I6BYD6#2U(&b?qU*rmHQic;rU4hbXQ?q7qVVNLypM>uA`5^iJQL3)F+ry`D3WBo'
    'qgQ@H37PL2XeQ!QnnhTxz~S~y7)ng9wJg}ecdir8$ZXUE%y2ghKP)qlDXe7)d!x%+S6{S>qG3cAwp5p-juC5A1oOWs`oXl#48xV*'
    '6jb;88mE@~EO(#{_41t`ui^IEM!g-^a~#t(mi7a4NWGRB^KY7x#A>%sS?pA+C4+t-<Smo!%IAyi5JWu;-olQo;i?%`{ntMX6#o}g'
    'f&g+9Qhfw(ZtX|p!<BV4bMT-|nfQZ;eB9!*pZ1s+Q-NA_C$ptN`9Rs2-t0ejLnX`Bw~4Xw4!%|9F`uDPM-mmn3t>WVY?!uFDa_S_'
    '^*A>rOh$;fw}*waqNd#3NERw%y4s)>PdCg4#*G(#nlF0cgDsE0_8(4eP(V$ui)oCy|N57qiEM09p1~y9m5QacGI32sr)?{H)>vIZ'
    'raxG2PiI&D$-^ip1hRp#T=N+8n}=F`?n>Z6W%ZMcx|1z&OnG~mn#8hUxN$#HXnb5JmQXZMy~<vtMo0FUVer=9V`+YbqWVgPEpqZh'
    'Mh*A~O+mz=^=p_IU*SRCU$NF`pfPUoqxM9jU8;k1=)QV77vV=TVpyVIa}xKg8-QWrgywtyFpw&{w1GYs1uHSyfn#1|gu@ihAWGlG'
    '?rPP6qX-eNy_YIe_F~YKdz6HQ@ntS7GywaEbTGLv*<7imCW3tEc&maWgi(^A_(=$F$(lU2i*LmS@>e2$>Q6J@08k?TQ%ceZ<1ni*'
    'cE3pulIQJBqJ=l-owy0Qz<D3osC%_8GMdFv`JgK9aW4=G#f*mpEFmi|I}|&WBQOm_nzNfjBI(18L^FFgYdV+<&?ykR+VcFXZvGNY'
    '7xF)wwYAr_WxT*r*twPA_SUadNt~DvuSVgztf2M6!ZB3S3Tc3DA@Hu5h__heEKOvbg1%wGu`Z+b8yltxB4fS8$L?W52I)Vs)hey^'
    'L;$8LMR6>eqQ`^W6c+UHFq!Rc;ht6$TvkRXJ4L=z`JfHafq(yU)66C!KqBL@bEjXHUlY7v!u-x*XtTUAwb4B*T<CrjbA&tfJlXaH'
    'H>NUx0R8Mxc!B{W*NSb@r?Ftb@CyxE#m8u&8=o1j>;|QJkvdjZ$knKSclT{0AvqISNc$r+@qNZS>=$$dPFFQ9uE|``>_`%U#iODB'
    'x@76<g)pP#M+p!@i|X5X^>72yOp}8VT1X!S)rSxtv>Ru6j)^hYd+CIyExtqH&0_0i_8tS3W<XsW&26Qt6$qj-&(iig-PT7lVJ`ob'
    'q8So9F@CUS^4M`$><)-TuRB&K$S1b#L)pFmIV0?z<d?Iwr9w*|89G}E-CdI@FPJjX>5nIym_FQ;8cEn{IeV2F>feM&LG&9;k8Sn-'
    '>zy1yNT}yp=PJ98d#O0W5xu<6a(2_qa!p(ZZLVI?S$4<gO~ryyx|#|#U5K=1KhmEMY6;}TwIaQkNyOqh5;1%PtP#>7!p*>1ek~WN'
    'aMG_m60%R?LV1*HiiogWO1chbl(*rnt^lXPLFRj0rS4k0-n;6n`r-$W0X_BDh4Q|i*;q@3B`NZ)!BA*W9?IofV^$4HcITFx{<Pg>'
    'Ot5-Ra8VWMt5Mq%b#ft-U{K~zkBU+NyH4g&<poSkCWj2pB)?*pao-aebxAM4MAk!Qi;^iX&Rs;&BlBO}ld;KwVnSQj?SM?0vNM3}'
    'D20K*NGV9DPCvd{PA5ntmnjm|)8ii~=)04lJmo%sJhi<Ead>9r8jH5w!<Ph=w)d&PQ8?F9^$0E&s<j@KGV1zath|EMG#;z2W}9@}'
    'b!WM{oDb7YAY?ovXvd;wf``LKDpL3XfNweTkS;k?f)=>fEmBKFR^cm!+qtD?@U`(nRq17UlNDf)i1UtXd{V9I&+E&nOF_(jEmmN`'
    'cYCOj2LjT|n$(>%a6rx^03VNUNtpx|&&H~CVAS|wbV=}OdUtRx)tOn1zi4zisvrcq<v2~debUa_TL4jYkpNuV{&*({_VpiG=w0-E'
    '%?*s<Fk-4mr>dYoM9*S-kaE`z{-hKEShWxKS|{oNnM=f1n)$%+F78(2{C_X0t6v>?KqmCv;6a80?FQH1sapQJSu)KBlDLuL5$TZv'
    'P8P?uc`p_1a#bt0;gjZ7LbbtfO#_Z|0uGkuc05@slH%E>7VL2D4l4LkJzu8UfmUKtNl-I00G8D?f4=JMm$y03Wq=iUnje-7;%%3T'
    'IKOVb675mzB>;=E9J3BCGq4z~m>eB$Tb1TF7hw@gtbU!Cdq21lal8l#Xj#uOX4R&v{4@RBj`iw1ercAiBD-;zn(x?pcB0Tg6Esm_'
    'Qx_^`O&TErR&H^M?&KWir(?D37SLx&?;ES+8r+Paoc~<-+H>w@KT`Z67W-Qj^Ii7Hr#>b7$eAxI<nTVGn7^P{skYf%3ta~U>h|D%'
    '>R?TAIu{#Z8oyX64`g+=GMK#I{ZZt1*no#BG<?nsot9TW%0TY;4iTq^sir*h1qCC{OH?_qZ4;AM>@tYa{^=}8!K7zXkGYWhD>J1%'
    'LDT-yae?>h5FN-7MWhUq^sfl%yL!#kQZAdU!SP#*=cb~Y{1|pyDRfh6Vg=n@jK-6<mt3g-$fVF`#m!ZQu+uqPv}N7u!hg`g60qqx'
    'hhpaZ1-<@(7Z>YnP_fXU#VHRK#zS5Al-3!Un*QTw-tS25H?6*kuG_Fo(kT(0sYkmS@OVc4Ak23HIx%(p)>d${ww^xQQH!Rxipn^h'
    'xp+1+&0Q1AYHMojDrcb4qb;>Zq#mg`rzST>ki4842g=+&=si2y(7Z<M&1dJ10Qhm8FH-{+YU2=~SdizI^genwY%}ROO+f%xixYI5'
    'q2rQ%CHLc8Eqk;QfAP2r;3_XLyX1j<p{ISt(m)*`1N=Jvo!-;Yk7pM8L`UT*rYjG2@#hai?+`12^kWtuYxe@iuRhb-1{jIL=p2K%'
    '?}0jol?heMYJr{Wkr+U7@oWA&kDrw4m{SmYlsQ(bSFRJE?2&<p-3hN-P38g3S<!>-iNS|Dk#fb(GgMjNH}5apOND{-zb<acOH}OY'
    'pte&%SlAP%gFZpg14ONfhfcv)yGM@gV!C#RDCTG~4-(u9XXcpo2Em{FTfV41WC)!r@R;)0v1^gGxmj6NC?El<qv1mvLF;4epbdA$'
    'RCdGf8NH*RG-J9&28gZkpdON!!<;yJC1bV>#wxl6ZqX&JuJpJIYY<dX^Dx$PnCmB!YYMUlNgRPiM7V$%jzGB7D!JrXk$gjt;YTQg'
    ')T~)FY6dua!(Nld#(l%dI-^{wHCGj(P*D__WpEpz%dt+62-A8HN8ndkl_-Z?*s)GTQ2L#b-gknQq{{9=uSsK)YOZVCyTPa~1ExSc'
    '*LG(;cTOCGbDp@2qnZRlbDd6DaU3J%bbI<E=$QI%wCDZ><W4~XI+_=)b>T9D(n^q<jEES>egq^CywFJOlcxr#e@v)E9x%iGEe>rP'
    'fOb+jD|S5>nB;TP3SP-9;mt<*AQVsiSyyBROB_G}5D8%u0_^WPy;1y5UK_3C3N2ny5V^xLckQVKQDcU0>P&*QeIZa%G&7G1`mH)J'
    'O1id#Uy-9<GQ0n_FdH%nB3~1@iz+pxEA?JC+6Pe_tn#ASoDKV{3b{(6sO#!u#4N#&yN*{7#s%yU?Kc@|)U^)-|HTj+VvAxN3j39~'
    'RMrq!65E{Bn-fa$NFY$i#!s*uY3&hW8S_7<LK`9m+9dod+!)M@PenzbNp003+sv4uu+bK|5~q$8afk%CM17U}?JUE2xF0xD1k8pM'
    'g|#`ZQ%Ol?NuwfP4t|eZgqmug5ONx>0`&57o2q9{#fb82?gLOwD+#iMNU_Kwh2Yeq0H;PiY!0qkfWxIkp0nOF;<dhwDV=U;>x2Mp'
    'GbVVTVW-foe0cFM_lnSfHi~h@6Y^BD{wIZ=MD6G7`|;9Z5?H36y(EH7+>r$n?sWu#tvnH!Ud&E__?z12Eu>^q>-=hbi`9tH&0iyx'
    'd)q%3>0WL@-f>LdSOt>rfzg6jzWD7aJZ#wrF9QE7TMlNoS0FUrFP%qr);D;I9$dhVrG1x61EvjgtX0=_I{TCi>m|5~U{9^-gQmnD'
    'T<t1=>kIzwQg|X7%#P-h_<0;PQL*mr!GTcQ;-ysL^QfW&S8c0Lh+cSNnJuy(bVFs_ot73#pVyY^wJ|b0t0x3<^~l?55Ux!j)^U8Y'
    ';3}OpKwDyvYHaIQ3$5`mp=Np)*D>Ic2fBg2-l{o;%_r)v71GgBcB6=Nep9J2Z9)Ckj?mJaMLZjlobeB6c@<zsk7UK-!;>_^jF`r{'
    'Hf9LtMB-{0@uXYP*{XoSD$o&RDAmO6a4s{M#i2w?XMKQ`pUui9rwB#6Nz6J34PvlVP%e{B%MtuT;O|D2w@E~FL*igo*N-k__VQHa'
    'XD~rp2+WM#@paFt2F7d6y`H9D#yU^KzEv48wKR#XgWt_uS-I~?NUHr?c$uiW9D{P|%if%qIQ5{giCR`v;>;YehpfF8S<(G02;^uc'
    'Z$UFQZV(28L^npu*#H5qu3S-_tj@X>y>5F2q-&c0+)$p*_t%w0uT#dAOwGcOC=W{o73J*klEUS(82-EnuCZ4$2p*TVc>CNSZZN6='
    'sD|b$wpCvq!%Y*><K++zbx7dD1kqToq`sPqQ0P#EOUA{278~xvUkv_xn)`BA2^Go^C>(tT=Qtw4A9V<L+f7Cd>ncoOUzwPyq+%Oh'
    'aQ+yrjHO{s4X`DJB7}?ghiNNbD7)sQz}p%na~`-&Fd|HD(aq=tvWd)vBY8?ylYV-{c(&aT84~o5mr!>_y2gCGyEvrK2pZf-SCzln'
    'VVfhh0!ms*7#b-J4k3yA^oN)AS1GachHxula7$u3;=sq#*G$wqv(LdH82UU|TagMTk+@&gn8<LN6o$+q%H1;q;e`ew#WYMPj{L4j'
    'JPLM;JQO5$g?OliY;G&46Ha8J%?gaeh&>8Kg|g(z2TtTzOu}NS6f?BU!yMT11_RM>eZk~(5@Vtt9jmR$lhxi|LWAB^?hRxz#G+SY'
    'E-Kmg-VGcFkQhcDAg7Uy=N;?PI?eM`06RoTKOS=B_1=0GDx$X?6Z`5*$U{<E{^tLwp;_g0u`g=fl1wj^`}rrxt`NH<k&TC&dElfq'
    'pgt+BGW3`gj=aeoh9w2)%|({5i!_{yQ$S|%eO@yEy{HEwkPHds{v8S)-mwoKYamzxhNW-K5HPV`9eOq8J`bQy8pf=&^xisBHT;n@'
    '`NpzIHm?{7A;kL!8|c^<GH7L5rl%VIHcgf=#{6O)Q1aq*8&FMdznlLohk^&_ULrTE$*tVuqmw-_<^cdJ#q;G@oh-Bo^d*C=z{^|~'
    'M%85e0B(gO<gC&_(HTmplgZa~2Utx9+O@ltlNx=T4I3z#p<HEse?C7%KMR(q6HeIa8S?myBs)HT?zX}Mi@U#TEFu~_w_u#IwsY)l'
    '`JA1Rb+pFkOxCf@<14JFM+}OrS-mrQcHW;2jEX-=AOQU5tVnmDjwBiE?du0ruSS&fO*tGdmvkz_uH%ZrcGELhlTaU0>h_E@Ql7hu'
    'nZ<bj>ZBI>yxw;xYzZ(==KA;?qSo@NvFoBuM{xaJta`}-7<D?9nF$8U<R`dD7v<m=KhOQC|1qh<6Ah6J>b@s$P#3ad6wg!--PeV?'
    'Q{IZF)nn6+{@U&t(~O0-KI8Ln@Kgu?POlF)pIg$E4vrift;rmF8hY~(|AOLGf1){pK>K|eXjL$b0ucL?L=HvPIBA41p-ie(0NN+4'
    '0xo<VNRZV|@DnJFRpvmQKSgubLSaz4b_@-JtU22#qFG*RR&&=$!)SA_%jt7r!-n-Jna^bg5rZiV*FEgqY2B`V>=%8u(E6#wL;}HM'
    'i=QdJI4ru)d55U8$0+Fo3pT<&y^hjVU41YMG|9M#YPS{++%0BCnmV~xzWNJy47+DTK`$7yDo?rV&1He?L`P*mW~is3%@3aWM(Cy^'
    'u$|#(9!do>RxxIry-wI2EX;Bhsr!#3nO8%*iTUatb}qIV#yC~(xz4IwaoM|S&80m8u|z^Rz{*9NK?4S+e%#{Bu-$&Fb%IsBc0N-1'
    'Zj%XVU_hjgkjXq!#gV4o$()}ro^E}We3qsWigv4z0}B18<TrJg57;!Az5mj8PKkJgpIUe4A*>NVa@@_Xy2cV*{D#8MaIa0F#H62i'
    '&zqZ&88K1HoRQi{{=g0t_Wo)>j-Xpr0w(;f3UG~SGE*t_Xf?6^0k3_|Fz2z3BWl>$_HgG?rf7Lr(OD{xHdu~n-nma)y@pGU7&SUX'
    'M`0u>x=YUT0I|!kAXv?6&CT(^`RU6WbAE>X(>u~Q@m!17$zpU{Vv-%yV>AD?4(Jz&FP`8)aY!`$+WBRCWj(Imh2~VXbOa*Fvecq`'
    '`I@bq<J|CfcKv)zElG=yX#li6FW2k`bDBe`l7Zu|auqQQ03QAViv7bvi3f<tEH8&gSn}pD<3t|$0STmMJk?P-ZR)oZ1mlq-B<o&o'
    'w!r>N`>xEX1iIzZ-2PG@1Pp(xom1NkI!o~J07~{dK6CHlu90MYe!F!=@Q61T|JRuS_Y3(L%5N}jl{@rf6RseqEiu_;r_|?4fMN$U'
    '#r4@^1qbIF+_fX?I4OnEQ;xs}<81r`k)vTKw6E4E9`7WPP8j>DGJ?C`OIC})oCUC$d^cxj+@yQlDbslhhUtl107;)${A&8W5uyfE'
    'hgPY@xFCA?9@9(6>zcBiwf*CaTaE{F5J0j-QI9ToGhG9+<oO7Gu@Xkxg7%=aG|?&*SFvE>e-z=YOAwf8do@yG^=gHcu#st|$>Q$#'
    'f6%va*i3gfz#c$Ff&2Yf=D*SSHtYneG%`-vLvyjHfwuxHErEX$?3^hRE7AsN848C5k_mOd&_)wuHg0$5IOEA9dEmQ~3?+(rVl#r?'
    '6f*B|!M%wxNVf##QT{`_gLrEbh;V_Jcib?I4C>7Ye{`9qdE|n-A6wxJFE;=lo|7S;w$x7U>hez^u>yVcVvY7S2PLIT016nSvDLDY'
    'G}`%!^SSo6sRgKh{BlqB$V7K>f&kdf7F61xrkK}8+-Ksqt5o+stuF_ZK^Z@)Gxh`~*5ixoO+!QC0j(dw68z734sOHFpSk}D_>Jwo'
    'Ldq1Ls;tUx!d7qZcZhb_2mv8=dh=>O6L^D4G$vwLD=?5gv5I5<g)D_&>?TKxFts;izQC+Z60JOy)Pm%T;>&NEoTivd@w7I&2Z3}4'
    'f-HrRo5`c2=`)TDaZ}x|0_o@M#+r^GzsMkXuIZ=P+QJKQVSiOoK))s@qGUN<t2m*8ARw0_%&sJ8Lw-7yF?%`uTaG^T%=-l>2Ep4r'
    '>(c5A3?Y=o$Y^E%S<UDq>rX&h5NGGm$yZ}GcVg8FIEeWp!QG@R&vpj8C&?sRCyGyGtTqhwyUuT5f{WPDEdjX0u6=a)y?3MFvhjMO'
    'R6cv*f>Q|HppN@TXSLskgvhWpG~5gU-2yEj%hLV`OmYT{Ds$uMN}xrb7mlR3P(rsW74%k+Ei<LhZjl{v{v1vxMq+0N=lqAWHpyW_'
    'bdMs_m!feEf2dI<?J=+7h~Mo15Z8R!GrD@<oFfBxk6MT#=Z8m3obQ#IKakVD@3R-om#X~W#pGIPMxD^FFi@rd(F}D0n*KmZYhQbJ'
    '#!hbD^4*MNA%?q5Uc%6jJfqL+bEw*pa$iH;oWXn4sRDTTl?0S6a?IkZ)MClQnXGJ=N0YDE(9kT62JPGwXx#@=h7<Tu(E$Qr79A2R'
    '?*85h0yJf%jYq$&Nt)~1s~&=L?6W{2qcHmV1b|DRW)8$J(=#9rl>6*4ybRyX>-#}GN2(Iu0b(_7(RQDZ{H>#_Me`*nR<zJ&BGs+R'
    'vLnKfF~<{4wBR2<;7$V>WR4jHf}4plAO^H|_+8Q-uE4a)V#Nd@S9`3{TKC1yLT9?=t%-x0iu@`O4Coq7oDgV0^!wmUO`cIloZko)'
    'e*J`k*NO^ZL2KBuz5hv|i#fMHgRFsW+0|@|0Zt<5v^HX(pni~?DTrI@o%NNYI@EMbkGu+<+p4vmycZ<j#AJOw`@>fv?$^`6{d@;z'
    'jTx~-1%Kj4bB!u#adjgfg@Wu-v8HjH{XoL(Lb_~`-A0KJ=U$=&!NBDpE5GMcC;nJ3^26sLJg3XW9$WAPSAFpo<~f)Qg7B)z#;B}T'
    ';WH49CSgS)?!DU%=<`w?&dkr;@}~v!z>o9UQEE1!gjn`fXLJ^}UmMyaQLeS<NfDJ~1BQI*1Yv#ikPr9oA64<bF#fjs>UX@%a0|+J'
    '^S>ai_H5WcI*xY0BnMtkYoLbl$w5vddzvSJVirI<5nVUT@xr(rs^FbNG47^C=6_)pjYA0=x-0Q34YxatrVg5%NsG<1CtI2ZCkys{'
    '@7$?3hE*;xCb;4C$Y^p>T9ORJR~{!xN~FM1(7qLn)szl~gE@7)1uj(<6cMo5%RJpCOOOy<Q)o{pUXy*7!Eqf#JJe%}ssmFcgY-EU'
    '*EaBA-mp6|eetW%#)Kssd~R)xmf+t?5%pGFC&eH;V!AMysoB9aQkIzE;?J(pr}vWOiWmJ(sZ_P}Tw~jHr#sO*cJ@d;y0EUI^e^St'
    'gy`?^RPLtz>p6tZZ0jdc{>hC~B~d5VJVty)R|$Z{B%4g9HTmF3oSXM7r0#J0F`AXVK$&T8#yiQFfAc-V6yY4S^K$jH;6|%jv<^K3'
    '^sslia>W34XB%d|`BkA2oKZ|Ca7t^HP+TE@A8|&HM#Gu&5#5)lp<y{PAFPj&7`QfyTzuJ4g~Cwst;<6*x^KMB%s;d!H#;U-@qW-$'
    '^zDOtuw1MKmB-<{U=a3Pb2{)0pyC^K!Na5s=#j(dqk-+djF0>wIk4#57uzj5Oro$7yV?&OZT&mE{w$=17;<ln*;>4mQ_~~m-D9Uv'
    ')a9jg-j$XTp;%yonnnZg8X#({{S3e^$#fPn{s{%Jw1JS_1=ZPCTz2~wD?z<2X5;cB+T!6AU4XW6?GzY;ne7w7e%I`%?qLG<oS&x$'
    '@v+zo3!j_I-xGvo5&)y1Lq!ZMsD0{}J8b~$`u0FmIIRkgYr<%$1Tr9pvHrOo?9+w>X+4czH5tIA({JHwkaPZ59d?`L2dCf(OnpfJ'
    'b8eCldkIRmOjuFcy$g!`?dHtL=s%ki?2vg)*>5gIe~}c|d5bCUtnP-+psV{$ya{|*_#R$=h<e$DZ$`w+4oclA!iQT%2@AR|sN6DB'
    '(mN@FI^PN>)@!Kx1pI)5aC1-Cmak8^;tyb9_2C&*{`Be}J&;wS)u(+wYDygSn<4x8Q%FaVPB<bREQ-8P^|?^42c4#=^ai)a8#DwA'
    'un9<`ZG9K#1Mn063wU&Q_$0WVZe0K1<;XA~qNgLsg#iN8DHLE}puX(Cyi#nL7F~$Q@paI{BcJN%Fdt0KeG!Ao1dpS<uQ#fd=Y><u'
    'kPvWr*W6#qabD2K=Au369a}e{j$Lq{U(1uFD2pun;YlsLmc~rqPC|giGI;Y)Y$zZ*^_B;C7q_VOeE;AKXOni<8t>G+PrX5jDLfOV'
    '?U``yR6Z2$^ci0MX$V74Z5Csop<XrwiZmASv0G~U-1?VZJaVZfzwel>jn4ic>-)Dv{>0p1*n1r^sOwn{f_+!>Y?e)Poa7LA_15Ve'
    'Ntp16SXt$O*D!t8d1`FZC5(FDW(a$*IF#WDt-vd^N6+;k4`xm)Mq0-fXrayV;8&-exj+j6s}A)|X_5smQ~+O2MJ_xdbx(_BxMz8G'
    '+l5ALob`hbJ|>%C+(Emo>ubRnO-@|ZvT$uE^qVs(I7FbCZTre!iN9S@%4#iY+X2>FPw(jv<&57MW;HKlf8<2=0-yJI?p-bCisep8'
    'h|1(GE+!UxfO1?#>ioD^Z^vrgc>pegv5xFUCe_jr<#}$#H$kX+E_t8X*x@#>|D~}r%G#6ti_C#K<T~HiK80n9;d~TB<-IwEiCpy*'
    'slvW?88fwjnlm?rPQ-|?lCie+B{$sZ>&rSFv-yeI-^zF)Bnn9b0uyl<h->3DheGeIPQ>~(*eVM`?@m66{D&FA@cI$LmPhD}<Q`N!'
    'S~<n8Z)w8Y0sXrdmxbRoYxJWx$9~YC>c%W%&hWNI?-SqSLaCa3TpKIb8)}&FMJ&02OOr=ifwIyu({UN^`m#;puI)B##s^;g-9B(#'
    'P^Na54?7izt#s17#Tw$4Isa-l2ilc5MeZikYSaT6p^K~lMzrt^V*g!Ui*>}LQ;6|-zaWKUrvtPR{^Rmi(DFo|YHx=Ddi%8M9%M8@'
    '*3m2EXr}U<DXuBHrw`=o*lokhC^LA-Pc5T&x+*jesW&y35%fzI;6z@(^Y-IDKxZ2GKuMx*XE_{FtA<o^Zu%g)W0xqPufHI*Ff9mS'
    '2TbnCLv>q}v)Md1i=C<RU4u0los1xhirc#T8TJo5a$j8(r9ysp1^*USrhjZHZVFs<u$j@5$96fc;v56z$Rb)VIcN9xdn}%cqCOfY'
    'a={1f0I4mel33Cb=nZTu?0O{_*Csh|TXa>3IAapQFFkXVO*w!jvuzRD0;`IDZsW+pQ|6rs+ZghDi~B;!7^gd0(&G9{>(yaw=*l2b'
    '#sjc0(dtOwaO2-~bt3Phx}&otL?Gf)yGL*NVS^qSg5mJ}zc^nESj8_wv{oWyRx})Wo3r*&R|L~e6qU`qya$>PMMi1j`ht~DVcL1?'
    '<C2a5f`wJ;M_W2)0JHQpQ%RejX?s7;##-2QV%qKu$?D@8D9yn>hhmPt8d}%xnr>#oI6~qW*Y|3DV<F54e?~eMirLPA2AY>D-x)K>'
    '7Ig~hkD{eIp>>LGVs#b5-E!DPDd!l;0PlGA%_~LI$6u1GlwvY$CQ&XdAIExZkWA5zvzq#}hZW`uzHARuZY32A^2^4GT^#$IrbRsp'
    ')R9^Cf<+xQV7!SOVKI5c2DV&csmm9q(K<-}ddq+#kjwJM&pSd%XbQVXa!nY?Csg9`)@PkgFCt6TkcsxMrH<2rXdf;r>YK%;EmzLv'
    '=4Ux3P_R5N;+?IiW*Rm`dy3>Noja^;V;|^jwJZr_y;o_oP>k@85(qYYcG2Nt#;cpHl1esrQ=&~20=YQ;LybCW`6pP!41Ej>DGD8)'
    'v=B*6&3ZfB|Jf58ZlYIuobQ`6V{Zc6)MU@%O@xkcxc}^c_X!Z0@vsNSpfSuif~9ihHDZ2*`8JmI8RF&?FmMs)dEajww-X7JlHHDN'
    ';6Dk5{_^Ypd;J(}@w^IcE3Ucru$f>T){L7kAcxaL?0hSj7sBbSk<X{xLo#dB9$Y&eP;YID9jfwvcOkfxo*(ZL9VUNCF1>jZf~plD'
    'QOs$dAE||dwynE_+$6#)&KzddM1lFSD(dkHq{Aw@oR2GVw|X%;31d@C<^&UH%04-RBefNWV9A5Z9taVn8Yl*z46~WCVM{`l=G?6W'
    '1Po~#N#i`Jz<QP>Gwf%LAWnZ;$L6J~O@gq{Yzb*+Yg7OI^^df=1b22U>nWs?tk+k4i4M<xa#1>y<5?^D?AsK@24DCJ*9}EA`5<p9'
    'x*GwhwhN)Mt7A3$)M5)Re)lSCU(Szh7Y}AB)>jgO%+T4oZx+}g3t@aoD>rIgP;B|_WP~?(5=LgaML^dCDSzIf$+(ll3?k~C1=Jo$'
    'ljwRzUaj!@^xDRHM4=%V2K@)DI6s#O(bTTa!%uuI(;lX~-<GU0y`n_7blGRK7m(d;#Vl)Lo3AsDNH<i(*$6oCRJ`}~oyLMH?QG2i'
    '`?81{)!t%B2!NB?i7JX$lUnM0D1llAxmH^|T8mxh4q-1ZJe&ZC_u-5wCD6;$*%%Tzl;vBm?91U7|BwGL(SJ<f<88bWq^-|vKz1vh'
    'P({kv;Hh`p2M&$dqiTR;54*YuarBmF4g5hGlMX7G$z{5kx70c7Idh5rA<8{bC5{2@rvjCT-sT4;WNXBd8_AP4P~IJ9hgQK0Ryps%'
    'Zr)=-2N%0n&)Q1DZ@dzT@nNK3iD5IqdMg{+M)?#^|Km0*pr|L1-!XSm^Ttyb%<5hoT68D^@JAHjA5Y|)A1qVEyqFhTK(OM_9Aa6y'
    '`4sv2e2&qOW&#1mgkH54FQgooXWXsyT6GpMXIQz{51<XV*hemO{O}T#l9Qb2{*l|+{l-Sj?`B_WnrgSQlt^?i!}NW{0}1Ytfr_Fp'
    '_rB~j7_Qgs6qwtk?Q>Buz}mAJ){9crGLD=%bI%RJZF<K(QBcTGN##rgd11!Q`o~)&yY`RuyCVaeRDSd+iyUchqY7gz6PBmz^9`*='
    '+e-Ox!~g|~AbHaor={?{&Inv~@lzSfcE;;6{Vpo6B!+UpC?-)SLDGvMo=qSAl09V7pz*O*%lqgR@?|{xiyO_)ew1dCVtVtXT0x_f'
    '36JKid+kN4O>%}zB2MpJnyPvVrqVN8#uqvHSg5r?H-~x{eNv;~e1L<@qEtY07jU6)Ql7GhLq^of{aVM<tf-kPYG2%cseT72f6K*>'
    'Kqok#OH4?0aF)_D1jmuMvdjLvF49C^-1#}a8!`e27YaTEXCWDPy(pU7qABNoZ`46nzN_jHaqRZ9CIwz{clMD`rr`l?4`4=R3{N=q'
    '5gH7j)JV5U=ww6-?#`r;isl+P8Nt+(JV>#kMjrXSP#V<px672Xd|I=_-M^ZIMnxo=G?uiiEK<F(PR)z!G7n11)SmE5F4+ccL}wd!'
    'n$&UmcohYPS69m%zccWceb!8Y&%T}UrD+H}IH-IT{c-L)I=3Y!4gW`|p*naA1s)ty78VO1Q;!M<q#|zOBO5~9n2EF*6l%(R1~ZM;'
    'd#*$k9$b!VbyV+1pS)dP*(PU7>6n2$Rsqg!qS)-DKeJ3LaiG?Hrr}ltY`@5mdglQ;fDCyWqfWWW)#5I^G#Wr0=)y-z=ta~)p+LgZ'
    'Mhx<SuL@L%tv(m$SXn<ZornmNl;X97auF_ZMQY+XH3BE>E-~y34KdQU$5na6=R@j5VrwnO<Fc!Y^N2qRViD{f2vl>GR03YOI34w!'
    'DCj*_0h^EPJAG{={>T`x6iOKp+6B1mU9T<**y&(P<I*dx0}S%2u6rxY4zX2zeRa^;mt=D|c5M9gUrlhdCj?9KcaAFeQ~1yoxpWtC'
    '9-|h{l)ovU06MD|07e<kL#cK!(NkU{{$FJRIM5Nojq=!Q{Q)ikn~PxAN{G7AIy%dL0$HHPKaQ%L{A6W;RQo6EE_QVG?w3bp7n-CJ'
    'oz?Lm2CPC~ioia(9XIJDsd{B!7CW6lB03ykBN!sfo6f;c9)Ji2L`VZ|XW!(|$b9cPXHoU}qKSn}QjF9iP(?+NVy&u8to0A6i_ruh'
    'lOMg9pL;f6#NbM8x>M`FEcpNekaq2rnKFnXVuF!!C;uDxzA8!e<2tAmPkE`qBhTb1TPuWWZ-$!!9Jrgm&$mwelN;fEye^hFJB$M('
    '4d*V+7N66bq$NJldh6_S9J*nLmj<r)#TEo7Fr7!$$gQf460S}m%s>470G}A$Kw!QuErp?m%_GArojn><$HHxW{?9bceLZrC<8P=Z'
    'cgH`4#*i7#O3SQa#)c#}%S0k8Q5Zrgnk9T3+zZg!R4#Yn8v8|SBv^uS{ShLk98CA9%Cf}n9Hgsbd`}^FQT{POjs8&b0gk5_P8}-~'
    'qo1NK2_2)MZzh9UCabXsvOx?WM5Wn7KV}&#`LHych};f1xE=+|E$_)vNG{lX*|eTN19xG&*00D$T`L(%PC|KGANE%$aA63ai5{G2'
    'M8vFS8ii5xIIoa2S~UVS%sDRB+K@w^J+2<9|E&>WBHI!aq{JZIHO2N2zoT`I+I3%~udF)`Uwsd32J{evUeFa@Md8Y!(9drVE^oWu'
    '%G7j{0V)I7e~+$%8sY$=ay@~>1h>GZrQDL{FjaNQASfMt_Gc@QwNT-Avo<oh(h+Y`p*tm(reCTJ)&ilr+bhVo6eUumLHqdOd@4ar'
    '0{)rA!RcR`I;kSnZ3j==Ia@yloU84uoed8g;w_ES_Gh7my1uMyN<~*eN96`|B^*P;fH==4rhD~7s>WqId>V{5pAmw54&1IubhnVh'
    'e{rl0I8c)PSwB^rktIz(r-N>6a?m^^XgA<Hk44QW1XGb!TB{=uBm|c!fNxUzqy61q435MD<RqtjBEPigF2_{dgQW<HsoU15DSnj3'
    '4XdFFa7{3}3$Broycnx&h<DJJS6)h&w7+=kfZbZIf;DBKviX&+lLJI4>htV19b9|$oWTySK}kw{8esJ&fh#-s*AS+;=@PZkEtrh&'
    'z?l0=G2Czg#DD09?HFs_I?m^IX|}9Y*><DK6RO!I-(P{MLm2^GMDEgymG{sQS4T9uvw_*5o!fEX2pV2Acdkx~b$CC8+zFbP4-CBf'
    '240A)%6q*-jD4KbCUY|Ve2#TNCCn*((>P#a2`-NZNJlU<3b5`Jx{*ubvX3C}2s}v^A4S}(pGCRGo?Sp();{<$$)0c?qk{3N7;Mp3'
    '@_4*|thM?q<#_u#W~6&I6fc|$fY<K!=oFMV%uGwc#2gduf@nwu_`3)o`Le--b5aAV&Ay7HV4b;nF(k3<AVczUSh92hz0r+Z1gs=*'
    'v<}Imuc6vVJ{(xb?5X}NjC4$g6;!Ac61$CscZ8BE?7Y@&x|v7`2R@rmCvYqkihZ%ua5}rVWI(7XU(G>tZsNV!Py;*vxP;w47B)xd'
    'j)R{4KLO$biGjQZJ^{6<HO)savOHnAH9X4wk2=GbR?-SCn`(A}uK&6K_R2m*8>l)0Vhnl1wy!teOXrlg2|F6QE3Py1Ek0|LABw=W'
    'l)$Mf<99;OO@x(6Cz@KW2MQ(itQHVHHI~8Wup8yO2!A-Ja{Di0AC8-c3Tq?5#9n0+?53g9JT{F^v%?AMc|h$}<wo(I;TAH67CXvB'
    '8>3;l2}HlKyf~od`K-}-`nWy}<(Z&91mND_Jz+0F0#D%iwQGCvLwB)DF+H7+*z=Z=u9mH%dBC#|n+^DFLyVnYkcxi6W+eZrh?8(0'
    'n4-fKNGaP7u<SnONINClNuGu3Bitn!0ioL4;O%fR0cWOs)+l`fJ!yl0QJJ{oeAct1l1U6yusKsYq)T>;hS-qxw>cT#{^VsfXQmu%'
    'EUyT3UDDKM33(fODG25$p<sDL^gu$l!%4f|u*j<)&okPz)Wu?P1e%#_f5?0hX;Xf(8sAulZX)t4LITLN>2)kjJ_0*?P*@HB+TRmg'
    '+DfQY1e9`>v+GQ*JAtuR`$tT}=ZNMWZ)$~ca~IgwVfY)!w=$DyQ-@)}DDsin9`3rSD_dQRDfjYba&+<4z|v*jyHZ<zr;?(f3V}WD'
    'h*%!Qp;^zUM88z~(RLi17(3&*72zW}f>>(gURtQ{S2fY>&~i0*<B#GSA<hr}pRKTG%as&gXe)hMG~D<e{PKZA{N&*>3MJ$ONcIjN'
    'lLotZ=W|iH_KC`___yOt`27_}TRVGyE%<?PVz=13^QC}LHv6*6+mYx5TaU5lA3xl_z)1K$tX6s!%#eXC&b3z-f_$4A2xpjlr|<)P'
    '(E&r0R;b17mW+<o#yEDb-9+b%RRF;c0@+7<AO3N}jRMJE<J4w}qs6FgWDaxvy&S|xC1w9kHCI1qYIZ1T*3JM%I@Fbzc-NgS9!~X@'
    '(cD}<6Ivb6csygn&n^6*In6_r8Ff<)U;tg~^?B<WJ13WDk5rxqSHrPTPMyCE2Sp|=W`cax%L!%xI_=+o)dYA0g9~T#2U*r2={-D;'
    'c%<ryAzOo-T3^xZreSFoRtL5pmH~2}+6h1R7DP-K+2qSX)=24YlmD?;EQWXiT`Z*`_G10B1{H?;m$otIg_kle-ThyjgR|lh?-u|%'
    'aWXK0AK;t3wgStXSIoWP!x9`8){M(^ow|YyN+K&chr6_*SSwgXI`ED?aD%fz`!vOma_u-kLU2HK05jxa=}c#_7R&l$=F^!AU1!l_'
    'c;FTtqUC%P#NkeNb_bGlJTBSlDTJK0x29YU5iw(Ds2|OA@_`JmF#ty{X7Fog`Lu1W*2RRc^l<=kc9*eal(7|lXZbYeNeR`;abppr'
    '@dazsDt{?5elx`!gI8Do)_}>URK@!_97Qpns0ukA&AMnOrdx}Lywh&#(>?HX6EG%t22oQ4p57-lv>fvN-9|RfJS<i=c4Ic2i2n?-'
    '?3~;iCH=QgpNy$X`Vn9^s}+vBPI%dsf7lD3KAgHjVRv6atP0j3DA3Dsk*ZjCV$&Ob)ldu}ub-;LInVC0IAunBPL_@OGajV?iXO1+'
    'mvr-m%vUyQY~L??Af`wiR;Os3cQM5k%{_V=3>s4b@utYxu=*-T+0My{tRLw&Q4n*=@7@2#Dkknu?sz@;{pFlq-iE85ZsKU$x0HHh'
    'M}<2Tqu8LaR61uP6zs){xT8VDY82K7B5Z6fPo{<fyX9f!V$}SNA9Mu$cehtqx*;jca)kygkrq>o_4j|FK>4@L1dH?fzSfPG*T$g)'
    '!OdN*7pN?hvkF-`m<-u?v8Et{@$x^WwRvx~92LT!D<N<EPa!l!HA@==T0HU0#zzI8{$jhFyR#PG&AXb7<a}?QS(~FHG)Ak)q%f7>'
    'D5@m~K&>62G3dA^xL^}oR3X@RP<>CRO+xg<&UgVn!?YUFi8FI#rSq-XQw?@S4F<%Kl~630-bir$W*tW@b5xZ~L&khKEqK@o>(2OA'
    'r*#PA0?Yur5WRYt>1hm|H#>o5anfs(#l-M*dF$Uf+HP)lW0_|i0|LU|){#Fna^!l~$LY_dymh&tQ|yRu<`&TB@@o+Bm|0vUBEWf*'
    '<h5pwFi{x(?JL#K?JqP7o_^Z-B4yF0oOjDRMzfId%zW>2ozJxz^!Qe(wpDrQ%q<q!CEXZ4$r$k_=jgq%D&TuN9gHI?Tw2uV(qR8Z'
    'YN1dHqXot2IoohorM-5ydCB$DS{78ccNDmIUtAjc?XI|TPD`C<3r1zCnrt!n#?`?f6_bu6Pyc}iaI;iq_4*`RPLrjG7mvYs?I{m!'
    'c&Ohnps*$_M+3XfdC{Rl{$|tJ4yV|jq}5+A_SXYR*c>}#Pp++R8xQ_xNLOGN*_%9t=|Rv=_VvjN{l>CSCw+5yJey?vX*=j00^4NO'
    'rxO8a@XigIc9v0QmjW3SbzleZe;ho)4^|FBtnfg$0tw;t2krj?Jg9{{npfvm!AtGi6hL9mz6pE?5`GCKpJG;uPcb`tnKg|yC&>MQ'
    'y6aXAJMsl<n0!`|kuRp;){cS9$;V(9TJYG$aG+F|luM0F9`R;IO;v$bVX4=#^}3uLCbQ6L-i*k<0Djh(Ao=-PFXw>ZH{=orF5YtF'
    'Q`zpX3nU|OAG}^I0!JdV*H2QxqIWyjvxrOh(NkLe<RRqvlHQj}I*dPXmJ$b97o@}F6(%Cb=h=~4K1YCeI+y@y_lR!uxU|%e*J2cm'
    'D|shgf;~(cH=F>zU|&zgX72SMtZA*nkjE})XY(JnJ!QHu*(k|ZRhzLlz=RAoAku2)<H0fRGH7CBETa&Lg;C4f?Gf~~cY!TtK83gj'
    'L24&P9k#4yr|c25BX#SSW_WRNp!PC_Zmx1?PKA5JAB}h(by|{^MPacW;?klUvHdF?Tj7MU#ZowOPXZ<dz+so7FzvV3(fSnR9mIQ7'
    'KiqZm0IfvLovx6+s<Dn!&fd2d%oT&EGAdV@Q8(O7D<<@ICZZ4dOB0WObZ%*>SSBg{gR*b94X<e*u|X!F#dnb+uQR!lb`I08-$Lk-'
    'q=!@<$=Q7!kia{0px4l8Eqqb--JF!*!H4(yZDnr+riT<oM9ZzCDG4GyzZ^i2Jy~8{L~X3gmUY7kka+|t_}H1mtE@&Q*&BeP^>_=i'
    'MdFR$W?RJ|2uac!xUnJ5LhJMfM;H)e87Lg2`;(G-Ain&5DTaE=v*>BO*Y6|bu@+gBDsgA?n~;O}xP%I<acUu@)a`0`*Lx!{>b7XB'
    '4o6=NopGVD$dN-3uns08kY<k2=BquBXy-$;&;cz~6t9q-P4+R<bunZ7$f?-+Yppd%DsmEpVR-jT_9vwWv1v^WeJ5-C<>(?xPF=KP'
    'h+e$GOgu5$AG<431LwAj#YyVa$cb2eh0Uo=h6e}&nRQXqqpT1qy_`+eo#&tRqn!KG>A;@ZCDJ()f3#Au55liWu%>`noGVl9W^6g2'
    'Z)}5Lv-xLbmI+7cf(I#oV+j9X`aITR|G5Pnv_Jt~<}vH;S1i{4s4qv+{hUTQefZT-CkNW3caRySn!CYYp=RQDb^F#bnyx!lWrmU4'
    'VgkhHsLf6!T)EUrQ)6`j&5c5<Ro}a*m-ME~IJyN!N&tdI!ov_R)A5UF-bqIv$)3%Rb(7ibS9r4(c^J4&&X|YQmS)Ro{iQj;MSZ?7'
    'e4})}zZ$)M=>xAyTpH5qYHg98EiSShV8NkT+6DdNP3G)2elE!bHQU{hl2SyAIeR&@H&{CxID;ks;?jfK#_v9j@xQxLerKjWlSCb-'
    'T~e5nDNpa@AGQnlyma<<r1ky$+KL%WN3+d$<-}xWcXRc$ha_z;h-y5jon#EpqD{YWfTlKT0+4=;^spzr?fA146kZY}#nGaOkf{@;'
    'V-?!bH&ONlU`&Ib?TcNrfshTMrL$*m<vGm*1-7vNOU|v7oB3Z`eSxBW+tj5D893Z?zzsHn*#x!(NvzV^DoAhY*S(t#Am~TM94y~='
    '!7&)9+_PE*ZZLo*M~+{fv6zsAns|5_B_7CF1<eEn)Z6_MqaD*w!I~~R@*?ooQ!<qbm#+>7t>6TU>{lDA#rV$^*+04AM7dc{5=a^q'
    'epUqB-)^_Yc;q=Qj#a1ZJWN_NCOSCGun8-4#0*PA0=Nc)<XXh*jBGP8;E6hNAF>eAflUL_fu=A&1*pPd3C+BQKp=uNrBrH;)B96S'
    '&)gcK<K&FcE%47os#q5FJ+>h=q&t&yF*|J3*&+yiA=;s3<y_i9t}$C>r(=%UxXA|>rtUTA<m?lKutHsMfAZp9tRA0eyX9?*cfDK%'
    'ngE#_=99hA_rjHS)*&A8+vemp*h7w*dP3};aC>XA))<#p!!+-DKkLu1MJ7d3{t)t-t#a}I#Fb_|mReqAo;-z4D>ee~R(_Gkn{2qb'
    'I$`8>kvGvW0&42wnip26^&d1x+bFDVvt`hTe_z|eywPA-KwgD@qE}AJOyjV9ITt*jYgL{g*@0Y|1$=tnFqB6-_sr@=rk}P4hcB@7'
    'xo@6=C4&s^{r`)-shPF>tG>qAty{eUp6MCIBW1pQBLsbV1Ahu~nN7{XD&tKwC`pBs_8qZ;o9Dc`b1P#JtHpI_fn4gyhF0^ad56!b'
    'b?}BV2HyKSX?t6Hw7&KA;Lug9b^FKRG9o<gG!ozIW*9V*JNvSZvq>=%)*2{352*C5cR2EW^R2T!zXPsn0ifJMVUUYvWhzhbQb%iN'
    '*gkh$qd3p29bf0K{i9~pw@ft*K85B}T5e>}YtWZn0;huSEVZw2QFc|zSra9*7k1xulUe=*F42k1@|=f3r_epw_|R`+M|U~e>wg5i'
    '&}QCswYAm<w(i?fJ2(qaAoS|t#-mj3im8EIw`T?nvqx6)CXOiBhW)?tb&e(``6Br2*rE&3vV(;BYQKIJ9|xkYYV(<&zqqff9R|g#'
    'wy}Sa{wxoJ#Isv<uD?YR1~S%Hu>S{D>G)r)kEmIHaq@2=Y?DeSg->7Rxv4e3m@6!ro3`^=2f>PYthBff2GUx9*?@Y`NUT1SYn-~N'
    '*b!Q9vblc~DKdUqc*D5`TIR!S%trE;G+cJQg-PF79ca|dY5U?M>k)!SsM`L%%H_du9M`&Yo$du5cb0wZN3a<!CZ2{;(R(8|1zu5('
    '&Jmthdzs8Lgc_4Th76(#stE8Ww7;0yWxr{YKtejtvy(dm&Imp-v-Zt3uA*0pw5i<qHbLtPO67W0$matI9XX&Y9x0DIbi=yNzmOM>'
    'ThjUViF7kh#0=Gol%r<BWQ$L|RaG`ao;0QPlH#=9U-}SxDlnWtX{#ZZ!I?X1UhN3L<r;@SPx2e+3MX#4X<T5yC?W39$;TqQXW3uq'
    '&53$lblmy#Fm(}_(g?zWeo{{$Sv(?q@H+)4lNQrMa`KaZ(nYiZK8-#eebvCbF3Ou}%{G7Koa8odU&!)|ie(;>ywG}jhy#9+yg;h9'
    'N9Gr~66sDWJXd47dfQ{Th~>el=oBNR8z$sEF0&`ghfRA-)b^&o_kB!TK2B|6bYGyNh4R!eYxj!(JQQ1FvhObS3a+!X4BawuOj>@#'
    'm-tHau7zRRsWJ<(_YQXSEKkI68cS;pl!_V|FD`5*wr6R$+5!yw<4gF9y?>8T-WU-_2MSo1wwGcRcLQR}Lxgi5yjtQ`2y<vP0!5i}'
    'Jl4r!y!N>5wdpC1f^?!B2nS!Ll_%94%D_vga<T1Xy6EsNFJsQN>5gP6iFEw_>33$Nah}WgJrjWkx=0E2Fl)4-`2&%QE7hN4jtX<S'
    '$|^Q06A2RChWE-kmakdAZB9bo5D<1=p$vD9^$ei&2L&9}P$-=^t<8g*L5#$csik;PjLXL%{uZN)IpiM}_RbyRG0N&~+!0XP&3ZjX'
    '9j$W}>ESCnLJXWV!QJZzDXTW<Sv1wF4ONba-S>WO=<Kmsl8)X0N+>3bHE&nGaHVdWkbwHf3hD)aJ`FXU)zQC%x(BB(l5~X88>k1G'
    'tJ4K7Ar-PF(~f0!=Lr5)bGibHcL3+%Pja4Ivv^Q%!-Y*LW7;fv)b5*WRV2qoOChz2u`t6(xJ1#$pCOy}Vd__vCiF6iZtw+-)wb_`'
    'Sx2cLOKwfb{>{7?TNMA)*osWrFt+MeugljP+a0$r8GN-)i;*19L@0P%-Ak36E>o1DWRm!{M6T3e;eWHspU5dee_`hJbvrR6SQj0e'
    'W)U`G?IB>H+V$L&Hh`9AR9DwbE_Q^+HI+*ay&oosz{zFu7U9TG!L_i~R;bjmf<{VHnA7nG57ce#|Ju)H-!(MPi;G<x=oy(3Z%K&~'
    'Gwbu4{9xJA1nj!&I!y>-uX0)Q59SmmYn*l`Oi}S$DxhqctNp30R9iTy(3-SZS%I-==U&hv{Z|?Sb^!Id^XyJ)r;%9Ya>#}b{~N~<'
    'c6T<$E({_jMkW(P<qXA+xI$|I#Vkz1YRxZp1)ePIz^h%WgZ4iePVhwK8cN0xxBi8^L}n^&S_2oTpgNjy<G{Okr(FJn#6z<P!{!0d'
    'YFsvDB*V&sP@V5Mr@3A)D~UUXqR8}i%`w<&Y4$iV$}GT1i~z+B(3L{Y83G17xY6-Q5q}$Fy0w9RwNB8a4NU6PBd2Rd<er*_m0+0V'
    'ju-*J<XBbwY|tnVFngGzN9^~5(+7dO3ruWtLp1S%yU3h=I;N%5dR~<Hg<9?AFpmsZT^dHTFBq?X0>NwPSoG(Fz6q`4!ZWaF-LKhF'
    'p)$%M!A$HrZfEsr{9?Vbjp7r`UG>|})S?%0=BuZ87tV0jfb?CosO+a*Z#<*Oz$^jm!sj03jmGo=@zxv=`d}A8D0!frgtLH#5`%t9'
    'I(a2DbjO|3{rF?jmq|fiy@;^*868iBz{#z-_I$JUvhin}u>Rk(BBeiNMr9=!I+ef&8n&yaa{gtD_laE3$F%e&USnT!QMPh`Dx#2d'
    ';NL)yPO?c!*Rkr;gWu&Pm;=^8Md_uGhOi9x0B--cmyY4VGqzP6a288Ki@i*~3*spo<TmGHpW_+6<f=mpiV)_-{VXq(e^3IQhWN4{'
    'ki4Jrg(CE<D36svS2o}x`pYxSIJh`K9Rxr+_#7iydslchDgWOI)w}=aG|#k+*UCwON4faX9`?e4nBkVrHd?5!fQstI$e1I6cQ;Xr'
    '6M9mxMjf-R!mngX!H|w|TW3Yv5UCa+8^XJMy<^_JgFuT5$7~)mo?$R!I!z(y3yUO(D-2PRI)y^0(RWe%=mW8o+{@PcAvXOexYV|u'
    'KS)aP`h<L}7`0!oFhw1efS*uXkhYzAme^0ht!(*_$3=XdFEJp(xM&trI?)Y?)O$-9Y%CX|FBTr#+ts+x$D|mCp(!_a!-D=0PZM$8'
    'XSgKR-t6SVGm?8)958!MKG}U9M*>$T-9w=I)3{Sy%T1MR_QEy#f#pRzQ5e5wMNFTZqVU<H&o%QDz3p$2Ooy`_RazU`3#E?=Y(S8m'
    '--vjgjbUXL(I-Zjwj&7!M^C%pS+g%n(1;oRfSuC={AT1m1ah9%6^DCeTK1sVXnA#jiy53@(qwC__DAf4`^~`qeAFbyQW(1k4SEoW'
    'I2>$i-4T!YC>>7dbP^4rKA>&{l_C=y5x;r<^cw+}@|}Zd+Z_Ch42Xv5nw}2$rXhU0Kf*Ss0z(Rt+q}=nERVF9;FnUub;oV5?g-w^'
    'xx*Q4Y|7}AGe{fbEZ)uwTk5B5Nb1lw6cW*}@*;TapD9caWbcdX)0b7|(b@$aWlGOR@{1x4+&?WL7^{R!!a0voU0&ac?zBFrlq+l^'
    '<#1GI1n(&zPzXwOBIG<Ry2}gEl;`k-2p6KU=rI84^Po4hCLRU9mG&e0pg1tCn1R`Xj*lJi=`)}#F0fwk+CWTiDu{lUgO%ZhEn~QX'
    'F7eA(rzTH$I5tiTcJRBU3M(OvBYZ4)u&nq~*S*DUpa*IRG5(Gk9ttaj=d|xL?H18kr7b=a)oYHsXvrOAQlFT(8JYa9z}%VZAUmoV'
    'g8x>dLS`2<Mypn<TYmUk9)-L4so){>YCydYajczvz=?PM>*86X7N}R08~_(fMxhmDh1MgTn`Jquw(G!Vu0p>F96Hujsn|%Y2)DwT'
    'vuvjH`;MvPrKqKFgi7N5!;uo@wFOEK9Vi}ErlSG@L$4>#skV?Ct8-+L8&2=$aR-g*fL^zfKyaS!)YkIwfYY<aI%P`XFE6|~xyVF|'
    'NYh&#%tLXZ30le+H~Ncu_JaF*y7iMOwVLwa$y1whrRX?;5KZ*+s>k{m!Uq<iT8*W2MB($A#+k(b)zO?;R)+0dfjO1BhN;COw*xjg'
    '8|cnn9$iPACnLg6=@Ss?26YuySXzdOfq(L{ANt~@C1l!DmQwxRI$t!0&YLd$%5&&xn(E&O!57&`^cqCo<*;BDA`JT@!O3%$c2e!6'
    'i;U_3%D7O-LKi29d0QdQO8MbP5Dk>M;#m4`1Ui+pmz}n1KW{*p0zIx)WFCkg!;F2G$?YBJ{d2T;LiO5sc=2RjC9jQF$1crVK67{^'
    'iNeUiVbjK0hn+NE4VcP-9w{dl8&3VjS~$D^FTZAvi?O}tuDQfdBzxaYwh}G1V6O#dYF*UH%+#k#M`lCrLZJEn77==!U8*l?njCxC'
    'hh;2{k#Sm;{f{YKpc$7o2gG}0B|&$iVi?O4$`>(1;Nl=h+gJS|VSEZsp9-lx<n1{9l(CS&t1$ay-c(t+wS`|18NKEYPAPY1xv?_J'
    'qZFF@*m6gPsA{YWn>$j5AMK`M6O8X6H##aAvhrVBgO-^@7lp_QH$krfj4!4w?84B-G>~NJ9Jz{Jdz%!ZvX1_f5wCKwc=cUKU>@Ga'
    '2ooZ|g_XfEsUYNbPj)4CwmUQk>ipGZmwyp{JDztZ_9I;D+m~cuXVx7>WL$EfktUI=n&?{=7o$FifdW<z{vAz_@Pk8CXQhWx-1eDu'
    'CvfB$@vAsRv6C}`;!RR#iZFA@099YP_;!VV)c>te?m#Da-({=xh{^muU(5nND16T>*UGE#coRwUV<%!xjl<t@R@IpOQi;=jQ}^@`'
    '1j^5ja;HBD5?omI6KO3v9M!+RqFtde^At#Jd~Fkdn@Ag1ej3JAB!X(;nv3V96=j1eP{LBtM0(@fx6ULs!Ik2|3rigjJyhi0HKaz9'
    '8lFc9+F&}i#<xu16<Cj<Wl1I2BRC8Dw(iGth3*9dE*`**4Hcszk34(c3XRwJTV3k-IB*=+D;c2!(fZ1zg6;p(u*Qintd=d<WkfW{'
    'dIEeq4#^L!a;T3B32`wG@FTNLZ#5%x4w}5~=qDEK=wBXL@daxs?W$x$7+JHYJP*<1!*Wr(YK?ER>fY`v&f%S*X)`{f;WWl5t=-?B'
    '2u=X@PJ4OC9P@RD7w>z$GKBr~mi|d@1w*oj`&bdLG2$So4+F=->mqg^S!#Lz%7j`4TNy@;gfHgZX~*k6ao2O2B*}T-DbqhK)eRoL'
    '(k+_omW`EbRN{xMq1FYcDO&>oAc;q)2F1!()ISm8!&6?|=wfKi2(7yb52#aa87Qt)*>yc)-;A#SFb5*<gtcN^_!&hB9}l7-M3b>h'
    'Z$AWwVC|zJ8&e7CNK1bb``u#~UlCNBNKn>w3hGlP7zrOz0x_=c1A|4&(-q#6Vh#l|axbmk;?IAR#O_U#@Pw-N{=rKaP*OHt{FUjy'
    '`2VUa1@Anj+1xGi4{K}kpXV+oq`dN6RI;o<`(b5y5+>}6c=;$B%;UfJQw3})?#9SjH>ig?J>?58qRibs)6Z6#7VG3QgbR<_Snk*S'
    '*V|-sHdePPJLIDLA9NVpJt;$65t`gg=<<Ak{u5Lw*=aX(Ge5<`BhxuDYiEApupE*a8icsVu?<c;vLO;!3NSkV7JzQ4e<9W<?hyzo'
    'wK-f?+p^>>ak|Eu*BgoEn>9+OE{}1!+~ZUBXN6%2t?htSoclMiU%4(n{`ttim1^?Z+?mADJB*2|Dud^675xEoCY%@V$VOY}%y^CE'
    'ysoX4hr>fH780G){}jB8Xk=LR-(wAjg^|rLJ%J`@m(>VEQ}5o!vU`&uSjx{}zoxWg$tnQWfwQxb6@vqZaZ#&Rp?O8C>X2RGc=5^b'
    'J8Z1gxLC3ERElZBhzKV0d#yAxq3IU<!eS?}=u0$5OK;O@+Op>6EPwWcddUNcNE{3W7=Y(5d7b8!uV}y{;t&gZw6IPZ{>s_qx34eR'
    'd_kwCOA_-@c=$GS8xQ;Sm>rQ7X0cfo*G;z-m`+tn5&(E!OziX*es(WB=-tde!-4(Nt|%M-g8@)irz>(0bYI`UM~&BlID7ptSd`FK'
    't(gh&jwvROv{7EnU)HgRTc`}F#dG^`8zbV5?EqYY&4k25;D0SzG~K3kAyYJ)xW**27oHPB1M`miQR)bps7`HMUA>Q|iXfe~<5&gu'
    '?~Swm0U}N&LyqpNM|6ALO(-iOq|WPZ#3KVbdIXZRf{-}eOzwMM%E9hnUNnk6Rk#zeGr8jkUfaxk0NF>JF-JjWZWi<cP5cL|b3g(9'
    'f0w|Kd<@2I!lJ<L>_CY$!k?NeckQ+*(bR4WX}a`{v9KH<ISG)yNfd{48hK@_LPhFv3nTQxlO%F5G#<!fON1V~mBuU6-Y~xlKiD4e'
    '4HF951Q#ax0kw!RXA?Ny@_1QY-YPp}P-jonpw0h;sBXqRW!gO{qD@&?`XLfUuN1(`z?posoW`SyZUMH2zlL&uJi>#fgA-T!#vOO<'
    'kK-u<u)5^ic?B|{OU>TQm)?Re#PApbgZ9AuM|>aw`Otc#zJL7`ep4_tQc+L|b$ui&+fCj92K9+C%k321%df;bclBQYeXO)N)|m^O'
    'u0|7W%S!v06=Rg)+PznMD?zszUBc%5**Y--SgqmSr5Il|2@*&Up0Z^E%-JGWI-(9^2Q405N|%&kt~u{3EfO%~Olha<n5sqD<HyCu'
    '?`4scx?j<!nrg@${@4Ain#cnd6XcgP_#h_XW<xS`%?a%)y)s6u=sHcG=6xnUFLDuO4hEP)e6(f0d@5@%6Y9`r^2Hx;@?(r{^{r%A'
    'zd@tF;+fp4j}%x#>+QDuk2b2slmLVU3Y!+9yUJ*0fY3<wsUR?Z*C#|d$?J;?3okU5=YMQ6tH9`GfD#(^H@06Tj!iQ|DZCu*%Gj{b'
    'Fh5SMJ&SEmWQQ)xxdSbSPA`T|;@s{}#%jst-0F@{Lzc1+TB)G<0?>gBN>FvF2>~@il;6lKWd(S>5UL0YNvwckIutCs*|{auu=5~B'
    'Z1pd*6ykh>ytA<MmG|v5mSV}D=^N?e1us{-k;jV6u?@$=n=qP*1(SMh^rpXY8C>AhOYjElXYiizI6z(ya5Vk7vF9PJDH1_A1-NKs'
    '+Os0lnIEa8#sWML!Q0uVzAwQ^XEReaqBdr%jDg8}ulP%D>;2PA{*AgXUSI5gz94eiKjhs8Vw3e0RHQzUwQ~E5Sov>pAKEP}62TKl'
    'K)|Ns;pJK5Q@J<tkIIa?0JZ8WE;$nY<)TkELn_5se;=sE!Td}@_nSSz@NYnteLw$n48~X17-|V9Sjv0FZ{>G@_#$TzKA$#@j0pzR'
    '5UU17?-1;i=g0kSCoj4@89scDo*-5imqg@S8tD@bf84S_td5iW8~5HCGx@*=?m_-I0>z93Jhd3eT3%A(n^E8S5)4mu?q^dO-!6<s'
    '3xJax)j@@*=Tn=mv#^BlLhgB>xu;6e{&r)^ES}xL@T60X-IEY&$C;eEbScP3jQ&l+EZlAXrn$L2#7?E%NfZybKta(FCD~0B;?mrL'
    'BOYkXD)_8~<65eAh3*p7&W>!pTqA@WqP-#-$LbQcui#mu;2WFsA;Fe!CYa4L@Z=g6(n`(XHfkrffXDROUP!)vU3M&wId-5y=9}SO'
    '9Y)U$KxyJfQ%g7xVIu>UYS~udBoY7TKlJa;$NodCh=2YRa9_(hLHQ(OkeLdb>wBh>Kt#~dFc#Qwm;nVTmRj}W4H{af@=Yg$F0m3V'
    '0q!UzdRMPF*_wcd_1xK=H@B>!&;K$Y7}<8y$r&ENw%9~7e(#2^l55T-)+(0AR6|MgQC4bU_0O+*A{gkPw|;X#!QY#=-=muulcyHN'
    'Ur%AHasm_4u00Iy%Znbfv?RpLMy7NkZ6F)~fl*V?h#ScAQnqXeAf!JO|6n%1`+KS4Ilqf4*DB|&p1xpx8abiD`4Rtl-2nTD3bNfc'
    'XT2~+mfXBZ;yJUV!<J;9nbDoEYDrs0jKS8|Me)EkRRY-4&Ba*U=>HlyZk0YWz+-zqB?5{{ru`dp2x0!nwckSj>(rOr?@?`rz58qt'
    'HlM3|sO?VaPG{NM;3hGmW}8+P2=v|JI}|%9Co6Zq9WNE}+`=}b(RXCuhEfRZtIyA`atM0*=qvo#eWhjm8|$%i--*NSWbDETTX}tT'
    'Z6_JAQt0l?`#f)x&t=EwYb<r1OW&Iv694Eau}PEhK+=?^bc+PnIj-5|d5E(U)XviqMf9^V*Nk3ykl6=lp37f?66uu|E;<S^7_Mar'
    '3BBSaCvT9oHGOVns`<FTTOru2vV9}p)T~MEv)Y7e#cK$uAbI6;Zlz((*y_FFjQQO&&k>gONA?HAi<!%0pJh=G)P|+TE6DHqd#dLG'
    'ZzAP=DB=AS+q|bJZG@3w$>G6st5ao}Vq?c+*7_QBHYS0OBdzVfWA)3H$G=jiPf$|AJ23&|Dam&wN@Q5tzb#ivA;y%FH7t-|A}i7<'
    'fRv6zwX<(}OfV^cL0R~`r+KBJ!oQ0HII)(CkRz=>2tjX-+f?^FKDHvMlHSkRtE>p>H*pN;@Vl|p(uqEcgckofW|)KZ<%0bjwqkke'
    'AgH&NjjdJ1mK*u)EEAgO0(@1*20uFv*3_EZN_~FCQJxwo0*B=p&ySt=x=B{fj&P@XtHhf~ESmdwbpHfu+Ea8s8+WK<*lvVR5nGM4'
    '+MXN{Cf3YF?bl++biHx^NMWVNML8%Onnv>QG1`5EaUyf>=>{Z7|7*MzFrq{2*dMn7L|O4qQd>=Vdb}N?s9Kt=cafFvocu)&VvWn)'
    'B`?({BeQNnGC$sFXrcdc@G+tO8VEWC=PhC7HZ<9i&R}+rXp0Th&+Z)?h%RvwBqO`Om=UzOR3vmBY1t$jOi9aJynJ+IsZje~8G<GN'
    'xG-Ds49L3Tj!nR=0J{-{zfM~}mDJOTNK~v0o;Nf%8UrU>$Tr!>PCr>C^Eu49H$<gP-PLw@1`WAat06e45%fN`<>NZFqtMbv4sWi+'
    '|4<>v&FfL0RkVp|>-02TBK;R`^l~D`!`RNTdm~K1F+s7$CaF`)jVI#c*8$%jy+*eA7Pj32OZGkE<q#4C9SQ&iPPUDS`Sw|%bUy=1'
    '%y3|5&aqMZzzrLQtm(fP!L_)BG$pof)1VkZ*Gb<JXo+m4<XbAY#h22x;rjD$4N{hmGVdP7&ZMZ39OA!mheo5omq+7;^>1qY!i4l;'
    '(evJPs&1*svdB`*43o0Ul|wF&T!I}}Q{r;XpyQ~a9QXP!*&ez-`l>Pc41A)ZWfjK~?KqZ(2`!R`srU$@&)G4m%BOO^5UEu&Jq(Z!'
    'NvE!p5jCwL#827|`!i6DA0b;ZOPJ*IOd!vaDA`2cG9wZ~E6W=Nj}cDwb-@)Z&zHuWnXrnPpSAA$s{P#LSgthnrwDez`v}-X`Kd3G'
    'ht<ogYk-HGaDYtK0pTka2@ww1BLy?kw@mgf>e4dQ^6}SXCTB`{m9kUwp9*htl9CQQec}Ns%di+^?=4Adc%$v_OiW9nGzXKh^ASpA'
    'i2gG*!y&Ifzh#zUv$6)(^3Qx<qFLV7iUTG$)w`nZ!Nwg=_9zV`Bi}}RUrFb4Xqol$u;0*a&5rL3TYw0JsJ3WrQNK3>_#grAiMtz<'
    '&rZFwIHVq6vdz8s7+a7ExS@rYuAGVpacm)i1e6_>K%K7o4l9V4=E7`~`6x)F1Qy1lh)&A;S*xF<FTPs|aU%|vg4)U8aa6AQk7kvJ'
    '_seWA__|w@JE<)6niqCwQl9HL8xJQ-)kQZ>$_F9(Z`_*BgGEyIkB;EG?E6@e4NFkq(o}TvD#2uX0~Ca(H@<u2XqBqBN62s;jM9kQ'
    '`2Ml+vqc4>r`fhTuy)!bPjy4AKOihu^lQZ(?~cWdTcmc)Xt||j7<2<m#r)O1=bZ_shx^6kv?eJusW%zU<KIPpBmJZ!+^8LLX#!Np'
    'Z+PU{vb)y~^LwbtxjmkgttK~+@>n#KNPaW}9Ij7|I=^%%)XwFd5u)?Gu@4UgKa69mjqYBP|3wH9gXzNjsGmQEP~^ha2c_+qxZ_Mm'
    '%||=RL;KvbkIv)x?*70>zPPG*H5#Ulc^WiQsBGBu7+EVB-c;ox!Q-$cgZLzLTOF{*y!DDHsqp}Y(ER}263wW1QN4|LeaDk`_x`t#'
    'xa_?IsFEq_uDar@E>g8F=lUThx^P=DK(Ae9f#+nd)hlsGx0rQvR0~MzNp~aVP<x$OelUiQ=9R9=Y@_X2SERy>*k};b;uO3&cdO~E'
    '$^}=h=(CD`Eg!+>z+NdqZA#5yy7iAr2SHcR<dk`1J!7TN_*@_3lv%F<F>o{~9F^^|_e2W?T<y3!dKc1XMD3h}^pzuF+hm4%geAk&'
    'X-NwmcWWT*R*B;@Ms>6XK8Rm<&&&}i+c18wB#VWFNu1s`Ikzf9k08{}t<xfITsT2+hMizvKdaspL}PXAKsoqEr3(s0!bAtrKYg*;'
    '#AQ6sd7>`yppRlRbsgx*74z4Gn|h&>qo3}<r^#M%S@aT(b?Qv!s6u?>cm1&ih%q>Ny{q-vS44gGRGD)Jue&5h*`uUaUnl;F>6T4E'
    'UWE>Y@vDY4uU-<~iB1TxrL5Kr3BPZKvhm^$9xnq|B(%@euOHw74QMN?UbBL{<l2r4BYD>}*J}=Cq)OE0%!M+uQk)dkaki%mppK4z'
    'E(xBn=U?}ve}WOt1x}bbWNsn`Q6mAfz-Mo9NH!*nwfFd$qKz?@T_A*}(F;~BX>87io{nAq+a-6qj1ipvUx*o3Eh}evarog0x~$Cc'
    'i;aVV$GI(Zwi*ys(VC;=>=;nHuNX!0;Q=!0S`uc7OPHwe=IUxZ|Ne5$bHoZ>=6xc7E8P^ZqR{h!sFcr-*S3Xj+`QWNsLjRBSnAL0'
    'RD**xMvf59)|A~~$1%!{$FK#PII5>QC67~Oo3bn~F%iAOI);U#i~kHqSJ4p;5Y2gV`bxm$GPE;Ad4J%tMM5SGNl9}duD<)L%{woA'
    'tPjalaZT&7QblYpO6b_m_|gziTpQ`2VEx5C_EoAx<dKkEGoObb&coQgWF+NJBq?9OC1nR#vb0Cb5g$vyQ)#Fo8e*oRN@Gyxeh57*'
    'JT3H3Vf*|{ScgT`2{W<8Vgb+@?iA8}Vu0gLMWfx5r;@*wMW?=24qK+rTOLpZxmKF314u~zTq!005Lm~WPy;c0rkNT#j{>Sz#637O'
    'R7ut~l7%RyH4Q@t!i0btm%ue*x2QB(B@aa<fNYko`1n=AO#iJIpb6TTAAPSeQu(v=FjGvXzviHex^LtAE+m<S!7fkvW1rK0P@CeC'
    'r7SA#q2ifx5JSRE)%hBrcP^2S5^jS12kN!pVkj-u!(^WYl{g`PhV1I>!O@}@900IXmB=sawiRLV$!3eD4Euk@O#B$Yg-yYH@5AWi'
    '111&z9pG4T)e9DM47AwrhsNV(n7H-IXF*%T9h={9?xQs_xG30RXF7f3DU7LuXPh}IC!dD*gC4#5Sz-!AL50#Vf<Km4AzwRXN~rdn'
    'z;8i+r0F%-eJHXsC!;a`!fj6)7J&OqKj4%=#`={1D<{Y-JJb2x&M=C^*D30ewPq2cU5$<`0}6UeEjUNGPLb#zuvR2jqhjIFYUL+9'
    'tU$6W%b+~)?Nx}uO}n^Xd9+{tN0=rY2bab1#fLJp0NotVlZgu>j3+*f2ou3Oqxv?KJ$UY|`PPRx-LTp^j`j?j>LA9Ykjfa4geN|5'
    '2B-Z9gn!FiXPa|dh>yd$ST@jB-E;rb^9ytpdidl%$xlvs^6bt4IEeVOycCZ9oaon>QyOC1X6V6yIL%q3dpVG&+a$NS(t+8E8G3B+'
    'Z))t*{jR~I*?rROwj3xH%^dq|a|cM@_%4WxVAub6!4^--CnA6#lOPSiJNl%z-*qQ`7ta9X>J9t1tKf$o)4tD?Oaj259;?>pt6CK9'
    'PiYzC)LJjKTz-dun|V%+tXtH}?C<+?+2+L0B<24kWFC(ZKUB@H0EGy9&C0b!Gd!la!M@v-)DYjCAZ@#8L}PU^xNu!?Sdm_P3XY+{'
    '8HWmiPl(8gDTd=YON%(}?xs(wZJX$fYXYza<J`kfN!u^z1#<Oiij}-B!3>!mUJG$(YUQtUPSq)K#c*ly;EKN_Js(J_fj%@F9HL;$'
    'R~sO3e`G%=7Pcfl^nU6g8wuwP6uVRz%`BuqV#`ks+cilM@2%%|975-M+AcqE9VmUf4{)6mD<Z|!J|~X{V~!}~H6m8L=Eeu(KCnx6'
    '>p6kY@2am`iqXDaQ+TX0StzxndtpOkLDJzg!lO`B+GR9BK|n-h;(t_F<*Fe%>?(d5epf1@rQYC{ibeqFgH=Vh72D-yiTemP4Ai6Z'
    'K*u&J4~A+B{byq?vkWem((X_Orrd9r@=Sti#6}UouwF=fYI=TLx}Fv1_O{Uz|DmZ)u#s%lBx8MX2LJQ`Q<oJb_qYPB6Xy62KtE+&'
    '$<{+lAygDJ`d<bA6Rq<QSEsriaYLKHbvAXAa4EaH?5&)CE}s`U5d-MF#v3MM=2H!l+>{Rhdj@&lXXskx1btUo(6ggZ0a&@rL*%9F'
    '$oB5^?;Z)nDcqQQN)lPSvAR#<NT4trf7d0dSgB8t-a%2gGbMkzc?3~;S9=w#S4_o0_z%l=7)*1FX)x@i&^npVd`h}^h<QIYrxu6;'
    '-TZQs+WbqzsA?)`>eQ>16zT?q!$6?#)+0Sl;{z#DAKh}z8s#u#nnT&?ZzRI*m8JIR?bd+B_zm{m9kn`a-fvQB&7@@c+Xg$j@G3=3'
    'pboYC*=0=IW)dr1{4y4pP5dsz`c0EI$qUu!C~|Y$D{8I*-R{_5msijKJPrU<>}$lidv|QsG5AU7?lE`<9DkyUIBkBFzC6npnHz-='
    'kRGqj4omk-8tI9+cat6Q{fo{)zKx-xw1iE2lwTuMSpk{i%JEoyy+|#Jk)s5d9DZ!$$5`o#6USBM1So~if}W>!9lavf)w(yyHP$-X'
    '>hmIW$KO#a82E`nVKQ;6u$rH&#hPe~L@>cDU}i!m`%Tw?D#WA8d2=FaFmt;_R)UK8=t~-upo5+dXy&NZ3Z=z7U`PQUn_oZeS@<>C'
    'v#%&CY!7@7Ur#9lJr+R&fw(~$>`7)Ro;<sC8!90nvs<JYP1Cn#4Ir;ebCuEXzn0>VABXjTe&{#CnPC=`B`Jw0_*KizTv}bf1y@R('
    ';lO{29Fpr<`+FpVo&T5V<GQilFMPKG05R9wbAYyI6P0*3Tjv!IU14*<bCSLZZTnsXb+I{~F_gDj9HzpsZ3WD-SW!Vj!`ZcPpY?C*'
    'QgIBivhcAB$zh5n{55?WZRl-2^92fh-Fjqx(|DhR7-$*=!Wb&uE=YlTFCBH;X<R{&i$v0olhc5zLS9%<-OK}CFs6E1nZ=0Qsd<=o'
    '<1+jPeAUwP8Y8imUi3_n)mNa~h#(Gq$a<GyeT!1CO3=5D&-z55B+&92mfN{2i&3OTDt`hnB?X~NmcFP@twqS)94~29>9C&N2ak82'
    '!vVH_80^6MEeo0mZYet5IZlH_OkcO*A>g2Hh8Y!!TB)n%j(sDi{S(v&wJNcnk}4qP!$vO2@;AA?ROW<b^}*smZ+DSc=?f{=`+#mZ'
    '`Ccz&XO5N)o7TIJQ=!INM443Z-}@$0vRvpA!|B<w{--UpFPEH{^ykIZ^dw^E=^47bPSPl}ZM520P$5EN5sum>Z`|2ylysJ$T{9of'
    'v#H!7k{z~efc1&&I89J%i|oJlaWp)bBXTBd3jP;rz&BYs>;!uIt5Vv;Z?m}b_ovSD#JZ8ptUh()aau>)qnaO%o>{Sfs7lJso+!ge'
    'p!kCdc4x#mDI}Oz6+>LH%b0wx>M%FuUb}L|JpL%qKv!IZ=F&9?RSi4(?Gx253pm>c7+=FcGd1m0@HtLT^?;mp66?mJ0vE%vdMW2L'
    'M$umO)CEU)@0Ib&U{Vtp_cb1!>gw9zY3ePpQz5PmQgf{rC<M8@!1fc!^kN<})A+}*lY><d?k*?#4B2mUh3K*mK+1`eKKR%Y>UM5b'
    ')NzH;q7$)`m3*#hrF79ks43RD@jHpup=p|MAD^$c=f|Sct~a47vC;=8Wjtxn`QQWkJFh9TX6o7p@*c^frdBa2UG$!LbpVcE!db|l'
    '+-DDWmFtf9r(K;&=`5Jxw93e%QvM5myPc>f-s&gO)wYW=b~JRsV6~m4pArrcxtd!^<H*5&^$%Ik(!@F_I1pjywoy#N(8yp8lHMzx'
    'UL46L+WK5oET&nMeS*wo3!>0*e7n)oDdFic`L|1pYP+j5!o|);OY|tP#$VfE&Y8{ZKM0AVCG^P>aNvw&f)-37MS7xjV4j^s^e4n-'
    '(N#OFhlk%hmN@k;%91JGIOqgWU%f>Urc#-`&l54eU~|$d)HNC6n_xb9*VM14GE%xi^E3eet0C-ZC}U-Z+`dI9cR<K^m|pzA5ef~2'
    'd>z$*I`t9Q!S?MGk&P$3Qjh=I*x6ixq7S-J6fqqS$~B4jiAo110nk$=M$_bBd|_r03N6_5qh4?*09)w#()nzK*O;aD@g%Q@?()i5'
    'O{$#k7Fz)eZNY00DuJ&NmeqT33xrFGq(ihe_>LC8WFqLNPlO|If!K~-1-6t@Fk`#N2<QUDXyL@;Ehw=g>%m*?pM-g4iNE#C^Cj?|'
    'P5**|E4zUHU%~bOlcXF4pDO(?k}Z%=;rZ?&sp({wfBxVQCvH%<glGLb_Kp8gfA)Mldb^}%S`n`>M`D)UIu6#v+VSqB$s}Vs87&ch'
    'p*>3bJvdAYw`Vdbk+MN2?$sB|R+Z@Aj|e8GmiR$%SHJB|KGf)k#vE}F>b3LK8LJh|O0&Iz*3mc03t#}T@AA~mn^pth%iz3#B&9|s'
    'IkCO2%@MQP6FLNh7VNmUY@9VS+P{%DsUMjpZ&ZmKPIXUP>!>I=WozZqBtPk@u-Vj9E^sasghn#sR(_>=E6&o{WXo>L>m&24-ru0L'
    'iz^Au>*IIH^@eLwvU(ht(V|f|#q-@w58x-5`KV_fP}m&uWx@yzoT8bN1iHQ3z`{UfaiQ^o8;y~aF-~mTVyo6Y+W^?73pxk9*R3A^'
    '5o`+-AzZ$u(au3XMd54lqO5{*hG{(=WQ8|N;+*6uthbBQ;t?M*l4LDp2Q|u8yqR)>!ArME1Kp1(z5l6QNNx<UA6xLHECa!fG2h+p'
    'k@b-0OV%wKO@CXyofwLnOh=A9LlqR%Ql@Ot<1XOp0*MER*3;7k3bJJ8z#`KcCAQn9y5ldh5?%|+Tp9hyd&~uKK|7h=7*x8XmXc*B'
    'XveHk`UTx6zB&3*&Un4X=f!07DoOSj??$Js-~{*qC{eGa!HC<}{fl?=o`8bcNG&m`V`Vp^A}VL|Ei#O^91AO(6wG5M{~#!xi++Tj'
    '*)C<p-J4bnY?=xoWR)AqLA(hEFVpD#U{q6hA|az_I$qQHA?6;4)gff6Shq@-v9*D%)#sSbcZPV1fZYhI68ych0J#+T&U}^g$Ct1H'
    '#%~sApv#^^4zJZd9Z6kCL|v8FirlV{`PKsvcX5zR0TdAOYi8ok#y2Sl#vsbRm;#&;Zt;pPek#Zp6Gde)D$xTZLOKD}LhO%b7B5hk'
    'd{1#m#5y0kWs^!L^&(rk+ot#}F1my5PfcvNsM}?n^};o%CJ!u{rO#*G4PBT^652xQt4QfgT3*>6t6$xQdUb2`pkGT5{=)Xz)`DN1'
    'Y2}l7;s=~N6#k}_IdOoBY(Cqmb|=5)8(T)|evOcjiPYeqQq0O6e(eAtcBVkWO`Q&dp5KMl%G8;CA>Zq7hJ>(Jfk9@yonBEWZ~oQZ'
    'wk4dD1j)b})>36eeIw+XD<RaES#}4wE(Z6;lRg+BIQO2z0GJh!{-Z<a-i8aIhCIMv)g+8kx~<nmni!F8)x@pj5zK=cxT^kk2@6f1'
    '-{j0awmG{9<bQx1b4yMb=Ms=#z3E@8q?XqX5Vg(6@hf4os3_+6Pu7D}u{;PdJt)QoZ}uts_~_Yg5Ism%y|dBq3rbX+rBH<@X=R>N'
    '@a(c})N{tT{%6ex5`s~Nij(F28JE6*lwSzWqE5a_rei_Dr5#AiN-nT)y6hDaOf;7g>|xnSt*)iaKFSZ{xC}^qu0D8I84tQ$D~}19'
    '{R&cL7CX^qUh3uxNwlbo35T$xS*2cqgM%KY^NdRi&l{?$>1Ve)ePK1j^rq7=lT^9SG$#t~ezn+ECT!pyU^b|POZ3{KZ0t2X+oFwo'
    'EK2X6qnW}?-V;u^7?CE*PLpfS;<s%)03%k^e~P@nYf^Ai)x;YAwKLo<7yrnBCf>nnMtbyJx`(-8Rx1RMwQ=aGEpx@vY1EmMpKp!Y'
    'b(P@GD%Y|{V8)XdJ{L~j%~{Fg(Z7VMJQ4BSs4XX0>s2IlY>FW6IiqV7zeKO|H-E73$etHA#>7|BQqop{{?$bO3&iWfY0)eZa>8&8'
    'w9%i6BVU=R0p|G~FXiJtzAb7a4!U2Z%BZFVaNr_Oqq*f%9huCE%)EX)>WoWM^_>K-QEcFj){{}u`b8;37nCI*Za$+y2P0*}<L$8B'
    'oT^5;9)-bA*(pcx6Q~pp>ZiML5Gzi)PRDJ}x&@v2PPn@0na|o>@4Fq{aPM5M@pIVjG#e07$OA@?d;_RvQoGDXTD6um^~qj`E{0z('
    'L=sTKK`j~fP^SJ-E+)hNy$h-dFD}?9z$cEjCzn!UBM@{ly`Xf_knTqx`R{7;l_YC`0OgQLrh6sDr7Eq+88m3U-nbMR@j9^BMfH5*'
    'TCIWn{d0=@`ho7nkXyW3&>3)+*`!Ca#hx|4RfXM?UM=8EBKc<dY^Vj)t-|9VR8NMfMvu;grVYXj7BG_TjW~*d|3Ha^7R>+`yth)F'
    '1JlB|mmtJVp$a~8-Gs3AC<mmiNzNco&-RNgc6)jJd-}iLFoh*`DXw%ttrk50?~4)c&5nH(tV*^DY*AzHHBC)WXgbWvI*%}!{k`yF'
    'ky9x+ARH~(_A)!cJSrY!i@c*!;Ju-VO4k{c$9}mLrKKz`8p`WaBc~a+pT~Idj&qNJ;uLC0`I0A$S@{u!1Yz`?+?&YzF(bL8?u<p~'
    'W}Xa6CSx}A8lS=JFL!btrB1rQQTdH-x&QX?lnPwU^2Z>@$V~a+69|~J1=~fUx{+J0h)6<@Di2?g??`-8{VL&1Yts<PQY>}V|1%x?'
    '-5d6(P|;i0w1q~Kkf}qvZ&pyo;1K6lgu5lf_aD+P+1htJ^3^{=9FcSG!b9m9BYRESX15T(gm_y~gSRsX2fTe;ptmvlEh2TzTs%PV'
    '*adrG@Xa<iwe54993d?G!O6O(z;xBs%i7*GxKm(jt1nO(NDbOMC&H8<B;ZFW&oLczkZh+&eo4xpgMNwf%qkh{L<o#}vH=nhaHUrx'
    '0=u%Qx8ZQ=36qSJhFGg8dvboWtDnA&GPS<X=2L&#6-@nck^??ykbv(#@2Z+hEY*Klj4&Q6m+eNDH^eY{@V=bM0F>x}yT*>C@Me(%'
    'H$~;{d~Wn-{92AL*$z7&aR{NVM@$oOc(>=By4F`A!KVBAwd8Nm6A^FOst|-Oo|_ON<V%Et5W?g`MUv2AgElf!>lj+WDHn(3$3$QO'
    'b#*4t@`lFAeqeJ~P8|>clUx__phfJT*Ii+5`dV)XaOnZ4H$`fYdIPC@BggY}#@<d=)6`#vjJri2bobX+YKADrh58%i(aM@Fdy?{S'
    'IwG;o9~gQtd*|`_ufSOExASAA*FhMdEve`cf%404ts?+_(U<+)g(Fw0&yd_skHTK(GLbA4z?ev%2Q`25B!oS`_D48$Tj3>5iWj$E'
    'xOF-aB&-mo3CA>N%rTu=jnB;=f)*1zN$UIDvV^`ywu#u<?5O)pn%i6_te0n;PXeehR5dQ_uZMO&#Bffc69NrxGYhcaxhnApmzh|-'
    'llP^(nJ;sK#M^e)%%^`gi|vxaSZO)Cu4Sb(Z1TdG^>~{O%tT~>i1nJG-D#6ql32QUp;r_Hr@It(HswS)mz_SSKSVn^H0;8M3BLCb'
    'pYM7t0~S9cz}CfRw4>ZQ@U`qSm=UFnlx4lXx6do93IpWqT6+T(%~p0ml7!9a&>Kq54`P#?iF;HWFaCE<N*-Z_p=CLoeOg`xZN@4b'
    'pFHO?KOcmlL>FJOc>-0hQ%aARI?JK4qd3N18`GcQ`0BfD)38krms&|u``Nts0Yh^iFk)aV5J^-QD;lfw#L_%KG-whdvQ@+!x*JlT'
    '=g7N^>OpQi=tMEAX8uPMHIu#}s=RTrqiKQy;jhtPadrBjg*_rfWO90?jYub8x2#JuW=a<Y_uxN8EL_DHPN%JO6TuQ(X-00xnaw&W'
    'AS+-kib@gQs~WKj^H7d7kG$N2=V}7iY<KHwV`Kj^P#2t9s4|5wbAa5FPG%aroNc9K)z@JV;5LSl-sq!Ij$KMw52I0sju;VuC}I$Z'
    'pY6^f)SQ^G0=lK7DDMH-(ddX*^xZHbo;0A6cBB$L_yVYa*?iR<ofUxFmxDXiI$R+uM!hH6R4oKkYXdNzoo`F3K(_?R=0do)PURYQ'
    'Du4s^8bsaJHN@C3bzndQKOflGniK0t%*%2q>}7R{W5Il}hAfW6oE1d38eg3|V6o19co^Fa?2e@c5Dx5?dh;T#Z$f~(DYy=v=wjG)'
    'uWL9?a#gJIAngDKWn?UUz<rI_#!VHvlDQwpJE1sWdg@f^X~?Rn9cv}4UxI<8Nrc?Fh<Ses^^sT&jtr3dm+?BgT*r;v<EkOm<`HVQ'
    'fI&@l53ne94u<`8v;cN2=hg*Ggi~sA0!YZ_)0p_C_8)&8A1!+8vK%~}B9AWWeBe%c3O)%b98(<>u8;QEbNFVTL@Q(wtilEMAU+7{'
    'X-0|t5V?4z!4w60K|Iq?p$jnFtZm|J4solmH)v?XY+6Y$keb5(6eawJ%XVWGy&9h>0Ssn;E@CRC>Q+bbB(8Y|mkXA&c5p$I?{g&6'
    'wagrjJsoU!DfrQ_u`zk+2)@wyJYBla@Rspp*tQM?SUS1|{c|-JO|>O9d)gVg!y83(QlYk6ogEo^`<MmO`jQ~ksByxML<Kf46si>M'
    'Jmz}~VdqI_+p`YvXN;r0OQrNuT)G$1D5dIY%JI<{%_?Bf4IF20FX=GS06$WkWT=fZb@w!(pX@+mj<YQA3G3%KDLhFq&9id_#y)+z'
    '!rYSMastyd%D@W-yO^L+4`6=^m@do~qZ5lOu1rsq^QxOo_VjJqpFQ+3ew;g?tqRcR-~hWsehLJ#h(b;W?i>9kMrGSA38TY;Y`>fd'
    'k6bm*L)oG#-;w;jlI>68+|43GV+Kc-KgBXstI#O#nq>ngh@`o<1TJad^iNjg#d8+vDl}QX8sH&U{4yZTOj=guz<H<^uqMf(0ach#'
    's``-B{OdcpcFrEV{}z*w1|>gUYVy4t<KBf|k*a8+C~a^0VQ&VJcY*6~DXS?Pvf@y~cjW#mSU7yLo{6hXS5Wql{*eS#Stn}@lt3y_'
    '5alNoLM;p8RsVL{mzj}Dbyr;LsT%x;HF9KX)~+d*$Ww5pqi8No`G~!WZZ(tksu?#$5kB4Toj${6(ho`FvE(<-LnA|224w_mUF%R-'
    'bU~ZtK56zm?CuLh$r%1h3fWGNOgu%<^0@MNFU{>O9I~e3JV)oOh<1p~wl?FKnyJ;H96@$4)JN9Fl3aLnc0@{`5pVz|8DnmwU?zk5'
    't>eRd%~*%W5}L4oUt|j}E;$%;6XR8b0p5f+N+?3<cJg^TRO0N}XK31A!U|Id84m=|qVsK-mM|oRzRdQsXBF5A?g&wFj{*V6s+gSx'
    'k4nJPy8&4jH7uQ(G3Nay>N<c~csAraS63x@^ei~4Ln2eKZy+0jH1BeaeIzb`@7mZ1h;!??Q=O^0ahs3oh~O8&uTFPW%JfMvIZvLN'
    '$nfM@)AQ>H)ksLTA}qS8<_5f;Ku|`Y!iKO^sNd1Xl|20;nv*uoXwz7+gykNZz3|R|@k_Z``XJ|S_mLN2A#xP5N+~#>2xiyA6dI8U'
    '?6_|0H<UoUXW;)XLq?0vbT#;8380vYT(dpxb`{FrotppM&fySu&67#Y8)6p$7`DHlX11X8Gx2+CcPv-Moszi!Y&gJHOq9wOpgvoY'
    'N%E*Qek8IGe*TV=7O(r%M;gP?Zj`GeJW#9Zt(_8@<uz(cG7JS(20mon$Z@i;FlZ#y!BtMkA`*Y5a^BP6{Aah@E5Kfu*8Q+aXZOSE'
    'bFD>b7<ImiDv%@7dx|DXq3OC$13D>>S5ji>l5U*|se?T9d2P|ya9Dy#w}Jjvgozul+c6;1(I0=#XZ)TZH?~NVLS(?F$o>`zZF3YS'
    '-n?$vg{y;?9Su}B@(bZsG5#-fP7N#TU1^`scPivMF9q|QSej{m+ON5NB|*w^>ZioYI(*{eIZ!q;r)4TTH}9}k+?*VbKvLRaSD{!Z'
    '85Oc!`&MTILYrCxm}Ql(qXhugpi+u*=6r9d5JL13c#hk$q;+4c5^+E(3EO<;9X#TZ*Sll8O(?mQP(5dViQk@6I%@Iuj;0^JZn`N+'
    'VbJhyn6DX=Tx&CVX15L(Wl7odjbDB{b=DGfs#_IM6O(R}c#3Q?Bjjt_fQ&rltydJ-2P=T$vx?rYdeGs!#(HV^%z}Eq%|BfbmeH-$'
    'uNjSqTYb$pLyEJ6bWA)q@6hWmAAY62j!G!y0_wBsf@fh15(y}Evv`PY98k{X-#Vvk)}ZdYDj$NoR!qz{nAFnl!BY~+%aS|me%n(>'
    'Z~W{5%>%;ADYF`#kV}VF!|0*=`NZiPD`xUiWjd<wpBW~=lHov&Axg-1YP91b8gntkal#7rJhr`c_Ae=$<bBQ&P=(;9;F7l@`dp>q'
    'PY5r?gsHp=ZcaNO7fhCjAM+I!tHGR7QsSJ(6j_<mcxVk=b!;)DPfFOW{%d<uSiz(7p0e{cLM;iC!&|9Hj|a|?f$SoTEtis^DkTv<'
    'z=L=(CH_n^AS|#j3C~odP>|bo+SNP24xtnJHcs%m7?u|fX}6()A0sZO{)qy5lS6}tS@O{>6E+F-Jw=-|X;ib12#<KN!V0c7Mk6nQ'
    'bM6<NM;aLR_^c@B3N<dRJ$>8asZm-6j`X5ik2(@drVV#UvY4$piO@o#L+=AZZ4Z!rwd`8$W4)mK2H{pfy!0e;P#ts(VxQ(FgTfzC'
    ')z&8^oVK!-oQl@hxaA>`iyT$n9YwF}_NKjq>#qF42oVxKxmFUBzJY>nWT2W#Q(!J|Qbnx)=4YEkIs^1OMZDdph!B*S<Vw*CWpch}'
    'q#|-Em~v%`R%N!lH5<&OPZxX72`NSE_!ES?gn}#)c0-md3tJ?I;oWQyw6T3^t7`z;|9SDSMXAZx2W9@`4lMZdC8U2SZy*Sa#4-Kx'
    'KHy{iIkB(X?9$7;uD$NNhIs_E!NUA#wc?&XaHPm!M$I`|BvJr<^_ijl=!|#C$At4G*Q64OCT!QV<zksKjtZbbp@mttjT`^_?+t(h'
    '@IxX!{UfgPLSBiPz(I$UB&YM&8i{Z4HV>Ta-A-8V?BCI}(qB}GlE}e`I}|?o-##;GIXqk1w(|thMG$An5mU|VQ@i-a>~O;peh%nA'
    'vF4Zsjj!O#cvWcSXX|-v1J|@PS#aWAspwle;BPIMKH1^oBM|N=OL5N-2`fqdpgSI;*~e9<u}IDXdxsqAmEcPQ#p&ux7j_s5O(gtA'
    'B281RLuPmx9mIn->_l`*w@9mc^@8TZXEfg2eD@a^lO%&>)^5!G<0t9%;w9(fCYg(87Gpp~VRzeA837k-P-bkk7BRHFiFxN5va!If'
    'Pc4xD#gF9>!Ln8f;!#MGRUeMWnmVPDh)xs9tM)(s!1?P#J8Q;y_c&(5_Os9Su5CT~h{JqO^oY<DJ`koCJ~3S^UYg&AxU$_>R4{)Z'
    'yCo7ZYgSvP*MnC?hUz}%MdWu$)c3KR2N1BMU>@<4bN9oLbmWjNz&#Ds5%HX?nC1;d@)<q2+~5e*m^u0tx;i|G8PcsF%5{_t-05ed'
    'gPP{O4quj`=96*aG$sX)^0l_X^1xJm>i4($yFvW~JYYTFURhNZ9>yHB=SL59uX?P%jBsYIgXDaq({5HMo3<S8KEKTUsAmXf3;JAA'
    'YR-jH5Zt(R&jjhqJu=M<4Ya4Gp9~Qrs6t6Ql!PQWYx|r9D*IaRMRje#f`_cJrM%VwE%U7Mp$<^&!{)fC*j9gKNN(6*<~dp&;d-`#'
    '2%n_5{9N2lNf>`8l|AO|9)<~Dz#RnEx@0kyUUvQcvG_a*`Kvhe1eX$I_gReB>&<=SA-a%J^o`X{bnKh9f$(ME_9v;=lHp+2-;$}_'
    'C9OgRXf52}X9*0AvK;yA&i>VA@C|}zY6xTRv<}B&3B_%Wuv*N(#-o2<b1%Y!{2Cf9t+vds@;;uCH<F$F=eJ`5)#D7KfoxH^VNJS6'
    '(FW&G)Hp%dTeKrz$q%O3y1T)0MYz^a8axTggMpZ2goENtD5d1T9d0~c;hE51#hVak5zjakHIUar1AsvxOqn0ng?}=sH&z60`$+b~'
    'm?VL8e}n<GI78Mh)ttZd>l`I^bsjwtRARPCNevco=neVlJwdc?aH0C;>i=LCbFafSbsXZSnVeY|;SsBw%Jc?quqEJ%AM#I`>%AY+'
    'ioUx^YL8}6Hyz}WrBX3fT{d{rKFR}wBRF2E@x3H@C1h*i@0e$`2pr&x>;?DBB|0Q0u`XB5x2{%Ip;;6~zACPI74b8n+efBy7Z5{x'
    'dT#ql2^Wv5Ccc;Sni#R+L_(X4ht1x1Wap1G^j>iH+m5kak~4df|H#?0;tyO$i?T-g_x9dXDvnb=_;v?C=rSC%?QW+gLXIz-kh3e%'
    'B*aNUaSZNh^~DXvP}U1zD)fFI;6XmEs?Q|%y)YN`nB0B7*hiUn-Y-#7)=_$6_3p@<?n)%q)(bL3F?M6?+{LV9u^noXT2QLO+8hU4'
    '(nfEmhMAZ~I%@J7;rz5`#{dAV0hou{zp*O3Zf>X-m|KslpAkci6k`Vx5kq$MS8>Bb@kT8@$0(Z&HOxcd+Q|U_#}#Y49Ok7Zy*rHb'
    'OobfP`nYH1?#dR|%|PnE9r1jaTQMs6^-Y+~hb$FI`rDqtS9QpKLA>^3-sv+gNf>RTTR`DRy%Z>~`}Iw^fQ@JbfCvmuseufo6i<(J'
    '59e6$6FX8x3h@XeoHDg}2vd9MLtwZ<k`}PUI_TURw^w<N&&B(C4s|oWhloMgv5gD>%=QU}OVQ;)m`SM-PDI(0S<K-#VU?O6+N)uC'
    '+$@U7a{zzsrzrY!^^VU~LQq?MeB-PbQUu>?Of3n#!W{9w&@C}~Zs7bkbr9`XiINo&wgN|^#Vz!P%;t2XBsgM<spcUoQC}}rdabsg'
    'PL08T(7QLxi2o0VrJS~oIYPrjA270qZupM<{4+woPcEMcxoukvC^vGaZ(a#SnCjtYLLgE!qRWuV^(F4%dO_~Wy2qA){ngVZ>sg`-'
    's+C{zr|$^w6mDWWE*8uLeW6mF3l7h_$ht;JSy8UEbF)Im>%uID9Ngj(&5GdLxVXT<EMwi!R-`?7j#=j~XUCu`6(n?*(Yd{!q%rz*'
    'zH8J<iZ0!T?#dJC)#_$DGZ^wa46Bp7=Cg}b%b(7ctijNwt+mn4#tSkw>lTL0oGz1vehL_ZOw6A!2E`>LG`GL~+bsuhj7uX(H5LRl'
    'Nw7kW)gKw;mIXg!6lQM2q3#^|YV3T2(3`#`0Pb%aZe}b$4N!wTl6GE=qTxdNOCl)MRtgzQG=iM7uw79`Xt>7*nrECNMXm6Q`qXeC'
    'Y31#kqJkdR{e$!9Kml*RLrDaOc9|Y9^1jgMeF`G>HMy}k6=DF_#u&#u%jlu~JVuFe?nM^-d=ZNo!tbQ27>}gcvKD#>qt3wy^g_v4'
    'k+^_mxgwL%8bba|Kr?Yg8vqBx8vjmU(tJ=5afJ||+<~`!T^l3cGvIUG3OQ;x)yd$mx=%;}Ag%%&%uAuYiLmy<E$6h~YB$8{ikD?t'
    'w|eE9BU%G5=H_sStR@3#T^y||Cf=XC<xfwPbm`^v%miN!ULHPB>0}lak1M2BY@lS{fI)Ekt$&(lv!AjL7^#mZ%U1srbnzn<sLwIa'
    'me>`Qi_NxjW#YgSZZhH80Kp|;TT@7eIz_t!fN>zZB<aj-X)a|m4GKN^Mh^mFgd4&Xj#L0-q3JhTHf{BtOOyXvbGvR?2>DW4Ch)q!'
    '`~VzmvoheMIIs=F%W`M<Ohr+Y+bkKP-y@+I<u(n$t*+}|POzIsjfJQ^pm;jnlE_RlH@74Vuleu>WoI%I#Lv8LL$8Wk*nqocvBi^f'
    'sYB>+$_RH@s9x24g+^n+-Bauz(<;x^+9kn~f|=GMV3U_ab=Beni^eUPT(8Z_JFpW`g0pK}ngb`0<EXQx1?ms9*}F*ZHjh_z-rcF`'
    '?7h@`$`|Mo*;=Us_j$YasJGDmC{dI3VaeeJ{JBfOz$lfuKru*Nol=MqZbPduM_fSfLiQ8F`Eq@nG7JVj+h_kGG`c7i13&?AU-y}0'
    'P-vQjrX}asVVJVH9(%M}IRePFHVH*9Lh*$&a%nz6Lz14sl-WVCJyVGal&>M04~)Z1d%35sj=&ipoEIq;zRD5@56%5hxb_u&xifwU'
    '6Ot#q8G+UA7?20>qA5^o&V>(sac*brQ5>s4Z*n4J(;^4S=FNb*cw70W4N6gj7X<wy*=}WZ3m2ttTP%vY<ITw4(owP~gsb^O5v^CM'
    'oo%SK3|n>%#dK082!_#RFK;{~a&3<h)>gJz_B8KHG3Q)EYZSs`RB-8!S;)F0w!k)ptk+hZ_lO2k0(x4337v`0Q;bOo_s?PmHVqrk'
    'wFJZ(372=`TCeRU!8E?rXrDm&CKHrt0WybTFnT4~3^m)#U?sNI3@>TGbQVVFJ-bhV(dyV)#s#6uk(<NN;9|U)YQ6hpCr1YjRIS>g'
    'Zr9+)AO9DFy;Q#acuGWbQY@TN8y5G`;aWMyvnS2A<nT_mVIjMuapQ!Ah^EZ}AyjZ_opsgOWXbPT-Zdm!)3$^Pk}~ssOx9RV5ur#H'
    '%KP|j<VSUT7NX*28irU0nK3Q_^q6R~QMMkyGg2~?-Z1g%1+y0STrUcgI;ir7mWDtgI%6u0T|&OHtv;2qjmd<WH@|qLGU0BpDOPkQ'
    '`aY;IGQ^=G?C9&eD(#Z#loly|So<!;6stqphY6PVhW){(Vms|Fbne$W<PX5$Z9mPFAEp@g`u3rHIz@2IiNWCnVEKr<zFyGv<5I(F'
    '8USI5HTDZC%aJLSk3EEXH%ii&{yp52VQ}6Wh}-nm4dx<m2AL_&udRgzW;tL!52+XS@nXGx#MuM6B!m}dNq^pW&vuwF4xM>DF?SWC'
    'uyToDIn6HCTH{4I9sKNNY=G%Ds|@c+>6yv@7agd14*Aa=L*pi)R*jZQ!N^eK5icxDL=9F_dM3OEY*Kt?RqBWx8pZk53S++{G2QHs'
    'E4GJ^HM^@lYbQ&ldj$`b#yn8bbH@$=k4t$5BxaCvN{=|ArrUDk8y!vdyLLq!?(Bppq9MVlR4<LuM-si3>%LTR7aJm31BhVdVp5GH'
    'J_u(J=ixEQ<;t4YWST6nd%zX|_1(}cdGs&MZqvHQd#Q&eOk*!ZbdW>#W`!pav~dJ9KvW$=`~8p8EXsqbB)2JAvKyi|(ov8ga;$5d'
    'h`A~0;o&A(*F{TGnU|F>uEd9<C9&)IzEVW;VIK7v*jh^)NM_8P$^7$g_cqkDp8@ZluW>Eu^2rP(S!DyP72e+8O^HXV45Z>dM>+Qs'
    '9lFmVhYUn$X|+GE>yeK@j=QIKEvRN8fN>5cE13V5nK?5u0lr|;m<mlpf*~@lFDy&cAv2xnG#b^xum3hD1g!=+_K}bu@oa@^(;{c8'
    'dls=cz>vHhz2UF^3~O~2@23!}(&r{N2hB#K7!e{+9T8&&!E8Md>f`(?qVu1|pv*F``c+mY$R9J(j0zO0P=v#ojF1jU1ln_mn7EV^'
    '6d-TL{!^y|F*I&Roj?7!ErD~K3EYTIBfz_e^G4YC^~_?&GeDJ#S?HR=h4fPPli6J|P5fKX93a)XRlrwRP;y(~CWTFofNSkmJ3K?}'
    'NID4C%Xs6bAWr0X72F$M9LO(rBmG*{!(!3e-%<ozZk=^aFq7O5c$Gy(pemF$;LH_crIrpR`^HusOS8b!&P?btuBU+FxBI-40VqQ8'
    'Lm?Yv%LwROgyy>ili2c?3mRFHpFW>A+$eMTeOVWa6-W38t-!!}JFR>bb$Oqbtwh?}MZLlkb#SAO4!zJ!-4eS_7|{e})DQ$V`&>i)'
    '{_XL>B%PY<;=GU~TOyPbPvo@~ZZD4u+CkLBoyB53RL8ls7RLjO9JJiyCgW5ha>_>-tGKEHfw`qE<|Vd|sMxzf+5pOQ^LKKzGY&~x'
    '%wGvQJg#|r0QnF<Sr)+s&)zV9y)l5SyL6l1fA5--=(q^1vq=>@x<7IX*entv*QnBK>y1<|Z<Bv)LeEJU7UPdGN<5H$m>y#|o#uow'
    '8^udkjmVQIJ$v<Az#|ZNgJj7x3R@?sGnskWltX4F%lE*R-f+(4yA+XOfLFpJehm;o2D#JZ8vW+|=fy%9#7ibWO<TUm!t<pVga*~{'
    '+pN23rw)4hu_iEH7VrP~0lAT1Y|3szJfgfm<fquhxO~Xymja4+tf58rNAv9B;OgChO{5=8@lAiU%q_X&XK9asFhB>JpSR!;m*E%<'
    'SDlp^cZ>V?hmtmN5Ja0WXYAbFBIR|QC0brc1SHWzDOBkxL1}z_i{mex2t<Omw=?G-7z@_m-+?k%L9yT|WnW3NLJnPIU&wGZEr(pO'
    '+cfur|80Tcs2`;X_Qu0s!P0O=7$_>$v;w>`A|S>Me7?jr;oSy(`MwYVJF&|qi+CzS#psOwvf0?fnKUYH?7af*vxPxW%ld|p2w>8e'
    '`HT74hg?evd{rSG`!F}Kq&7f?a$b=6o;!QxQ|#0j9@j*R6=GLTApJf1C%V@+@ZfW33r9du1-vE&GYDBlNQtMd=GsJW%|xljuVUyW'
    'e4RF7r3XO>|M~N8=PE}7AxlX>q<AI=5z-~NYJi5(jH9QK@k#T`_cK2gUYJT+MBkcm3R~1G6E-&>Tg&7hRxmAQ_=A#a#KC2}&?^Wf'
    'dBQ$`Iv5K70kpJt7{VTP2IZ1GOySbtQHKHY0m7HypA=^=8{m9*lCFX0Q2@u-p{v*ez>km1H$yc>i&#s*`qAY2Q4a7bD_^)C!W!IA'
    '1JX0m-|=-qXeB>;4Y~ihZmp`8Q9VMWR6|D{yqOfyW0Ei3XbN7ON}yj87Db-B2%KHWF4#Ht)|=TY=Kz9Q0Tt~nzilFgOZ_-WXpvTg'
    'FX?9%`XMUkg_YR!EI-<8#1NJa$gLl!)vzSMUe`~<zAI}gbu!Zds6Z<m7mE-`y{`<OnS~%=WX?g`gRTteIXS7ioU-K$Cfo<E3ntjU'
    '>IJw9F1vd5Y}rZ&2zCoOw+x+pQ*HLAJ=`CiUem#=ZqRe>O=HY<#i<Qs?+g7O>VU=Id7ODvCJFbcEr|Lx2DEx>X~wJ#ICum+$fY+e'
    'Gfg>_`EF;gRNVXj2-N}mNEQ6hgu`clogl+X_3`oyMKRaJuzS<tb3(@fM~?o&DL|@UFtTPYe>nl&hb0;Fw1R2L{g8L)!ACW?n@vku'
    'D2Zh|=qwpXxf;*umWln!cj<SgMj%98DptiPz?6-#Hi_eNHtS2#3|EAly^JaPmDTb?Ql->tdLN#y2RG$?2F2D5m)x_1+*2{Uc3j60'
    'rtmhL0E5|G^h1hS?gl?n)c7(WZQ19=(ul+eysjr$`3M;ypWpGkqL3Iqyb!6xmZ{WZyoO_uG89fb9=o}66)}We@)O5!?HKhW;JC~J'
    'K#O?Y*pI%juZDAJ&B+YXQk)MByzTSwAyR)^V&lGsXk;)WI8gsdPkTQ{+!)4ZwBSNZ*qWnattn}so?52Z2n=a*8uaM%C&wSS9XMxV'
    '^|e&XMN6}|)6XN$e+5LVd8qg0nC~bHA&$@#mme9W{}xiSNH3Gp3P6+cF$aJ{4zsusX+&Aw<ce42xy49~A}q$InDxw=os<x<?h(k{'
    'x1^I9A@;?X5JYzdz&sev;(GXmm_kn18;hLuD8m?d?xq+5_&P#AKPAUMVd!2cStIs#q(`%9_bTJW>Mf*2#@wkSBbyuDWy)zb9xU7w'
    '?Yu%RP(~^GVzt|Bx2&wLfR^7Q1EqVHirqL|E@VirT8D(dDh8v!`dcbzr|2(Isx?CeRMmSN7H-f*gDEH>*m1K(9M-Tu5FE3)4aoO@'
    'Lyl2Xj!X{VBq%4cY?r!vT5Qpw^;ouKX{`s(3p0OPdRAl=bWTu0{94pT1_rX}l0BHmN9V^QBxLYvJT_6j;{qcHSXk}%Fs;-_7r;IZ'
    'ZP(fQ!JyLIPfL#!JCiJX1R#p6o(8N#%8=On-yD(DURU<!vnn+SC|~$%P104SW0KKNM1d&CkhT2yU{cG}+_$EKE7N~%by1vjRl}3>'
    'Y4np^u4KRLW!TN<3cm0D(vxr(<nzCgb^=aCRNQ2vAtCUYqF54eLtWL)D+UT4Nyo&MSW?#9VK8J`cUiA1W!j~`NokFJ!^c~549or`'
    '4?%S9>V3|@aM*6P026{|BOT6&WKEssU>m_3pkcAfM14rB?u?*fK2%!W$G0^bJCen1kl1}^BOw{CSVgt`jZKtU=pcnRzc%Qe3noW%'
    'xb_j{HC)-{i(LPxBF!NcICiC^9N3s#{#{Bd?;~oI7R|T$n@AZ>8n14w3SW%{vqMyTpqzmpGL7mHDU1UcMadF>Mm`Rul&iB!b$7fJ'
    'H10YH^r!g;Rr)FR%0Bg&r2F^YAAbibncI=r^eN|BI(zi;7T3^u%`osDs9do2?NJB{RdNUn9B-x8NUf-FT8vYSboLtBElfU}?rHhu'
    'B}Oa}61~Pr`&e5~J7gx&Od>+1+m3<1yI=FO3v6;szHl{TDYaVd&-wJ#adKt!MOBORvnWjLY|wy2kfQo*h1D7vsj`_Lgq;HhS}(eP'
    'G$59e=SPNBK2Ott1-T->B2J?(^9&>LQS6UaUe!3o?NiJo|40<d?L|8Y90KB2KhOg_L-p0-No~;Bf#y=7p{?3S>@N=a?;bgIIV`VI'
    'z|f=@&XGL5D*s^4iGVo^3BjGaXjzSdZ9d9RT){ce6L;B|4Mh33DS`tw^Glaz_d;3c(?}uSeM#U0WA5Jl1g1os3s0HTzgB&oJ7zOc'
    '#{uf%1328dZ`)64mXW+yqN~|M{L%g#WEX>D`;iiZ9DYq9DKzh-Fh_F7Z5`;qozY|i@+`1RaobooSBgwXcbGkq9ik*2c-qLkQkUR7'
    'HHn$In`lpZKqi6a^3qWOeyo^zlCm%$jTa&JV<pBDL=_||s^O}M0}@5cD~&r%*a*%HmwU$tiVLlq(DatGl(Xh2!P*^eD-a3vW3Y>Q'
    ';_$?rt_Eh%^BZw90lg^5tgU>N=KFjhCiS;!CP1*gJ}q4?ntYdqiu2z6i*eY8jU5Yc{n^Lhw@vmkzFUOU89!566oH_%O)=9feJH3v'
    'jC_%ZD?S+{fMpRb{djyo7qed|K8V^<r{(n`ak}85S?f(bDGMS%5sZ_(VTTVFDhHEiWz3-pjuOk7^DSxezjTwSmmJ^x6At((<LK<U'
    '?fcpjp04<Hz{AH>w|#CLh=?992J8c8GFm6sk-yx6r*I!8P4`>dvqy7^yleAome`fE2}i5Hb}FBMKr9{vT4$8d!|pjYi;bLyhw_i5'
    'Rti41%VYx?Mplps9}oG}J79+EG_5yHVR;`qvVQQ8B?8|(;c84}-`My9yV)Ppq=9E`OoN^CzQq^h7Js(BIs^Rdq+|Rik(F*KA>gTo'
    'BD-we^|FV-7J3_OhmLSTXSD1G9THy8@iWxh04!HccnkIDMg9{809*E9qqg%uwIIk!9H$O^L8#56&~ejRF!Eo}zc9A#kSK#qN{OCx'
    'Pg3)hTdrwcX0*}JJbM>;OD6SBJTuB_tgJ*$3XDQmbN7rksXJ@0|7qJya_;!&A!ynCiz0$I#&8HhY|o(z;szHa?fx<^=<i{FfEzes'
    '!BYMmMdbSQ6-RN$Ost3Sc~U6Bks+93@vGe-9J28+0_M}st_%nX@4D!{Gk0O&Ct~#VudkO<acQaf57~qscSkBBdRTWce2<~9b7WpY'
    ';i_>rM>6@y;84UUlF(O~^WcD!2lr}0rH>nR>|GASU+}Tgo5W>(reTyu6T$CJWWdb<|3)nxKv=cPB#eE2Bw}n)+$;}j+d|SifzZ|{'
    'nptWYFG}wYT+3?g>TU!TJ%%r<0L@%aC(t<Pq1}4%-gHx?&*zLN%ItEimh3ZU3g0XEXV^Bdu9-}0Lutt}E$>W0#|@1LC<auBG+AHi'
    'NE`YBp-WJ1tV%%j&Cnh`CFGcXs_|-J6~iH?oDI@`HvM2CWC+x@<vQj6GLY$}Iv~2+(3!56(W%!=#q9eqs}_sbYV{$^9m04`L|fne'
    '(6!KhK0sLSPXVEZhYe0mfdX{xpC9pIP)N+xFP60vdJ*-K%Q*XW+fs(x*q-5X^BO)QIMBL?3{2nzr_8;4njX_3%w1A#7;_RaZLb<S'
    '_Sp%ki5Jn;(oxcjbG;>uYNkejq+3b7+Yu)<%0-O=@d{0F(Yp~8`y$d$n|I)qos%i4*&|i^09Pq6N@{|Qo9ecm33!b?Z^$-R$%xua'
    'h3$PCe@EU()x=}?q%jV3;z2lAnP#mKqgqVLi52b}74uE8kfWSsi2tPWacpseN=&C6eDdwS24*bI&YR~L12~VEuAJ>kG<Fz2V^}4U'
    'i@;O$NUU6{m#YYM?lfV-*~%2M2Qnw6wg`POuys+aU6e5|d8wQ%J`bsH0Z1URfaajzo;{Dib}jhC65&vCtOb;r)a4%Tq{(y7>RUWu'
    '^w|WDg!`0c$<?6ipUP6`_#7_aJl(ybw0RhxR9>;n3ANaf;^7BaB=N6TZ<C)At~8&qkyvDd<q6w7jX_jE3kvJmPe;s4W9)chT~c(x'
    'HIcxl0TSFdP)6+o0~&CWh3RG!Ky_hM9p~q(<$VRAV6Sv6w}K?~V*$n4V(%-iR8SeZVNd253IRBft-mc#eu`o&n_|Y~x7XL2p~G!g'
    'q#8&ejMI{?#-w$}p^`OcP^7THe8Z!bg=*FeL~1GuXU|_n+<|l?fv=EB>Q@~KwW}oXMme$sD<CjhF`JnOhkTQ6(5WPzoBLjR5L~41'
    'J2r-C!&c2`=tZa@Kv?IZqeQzY_1BQia1eV`?6-}?4Rl@GfewiGdRG#*)!l4`^T}YD;)15;k%Ql9oHiGP<^5g(mxu-#AL#y;kaKf)'
    'R<#5lpSeDo-d&1yx)0l5QOc`});E<kGH0P1yl!tdA&>Z)Rw4O(LHg5{EJq7_F<3R)ozjgBvVgLHt|Ql)w&b%<g<)h=&wpHIF7TG^'
    'bEzW33{5fth$(drU0hVbD!VkKFIR>d!)I(HHk6de-azt*Qrh-`!;P6M0=cttp~7txzCoJHFd}{%kH?E~Iee|*OsN4X`PWlKs5H2O'
    'N`73RwHxIF-M9BH>FA&XZBW^C7;E)`<}!~9UYV$X8;>LAKDpt-8?+N!WrKNr24k~c;1VDWU3g<%$UU|T4J&Lg3gb>EYVtz?u%Bux'
    '*pl0-;d%kIHk`SGVSL9P@YN?M0j)xCM(r<~%O%^%w_;e|2u%l7gOT#Pww#=`N|2m^9AEZ_JpN@MV;q;g`6b9!dE2pJ(N%*Yj<_CY'
    'E~u+a`nByFDg1<uw^{73Q9^BY#Pwd~BCrc1oiG7MEzMkFkvXs!mdr1TjQidH#UB0&9+<xzE<h*ZJ>8iz(trX9y=A9e*H;M1;mIP6'
    '){sS@r6AW>&q^$gs<R?sr?s|WWdC*NtZrp-JPMT1;hz$;iNb$U_#QId=$QQs)XcDc6{Hiq5Cn?p<NVU0zXK5r60XpnyU_elKOb0d'
    'e*ySw8PaBvHdpTHAML&R9#Cm&t#Kv5h3-BeVy~;P`|2%?k{)o*<Ps(^uqJLd3T;Rwn<abS5EpU!BZl5D60QLl<F~87-nPu`Md}PA'
    'l05i+nkl)p7RL0K$qq29H!x^|64?0X!^7s*=Fz6xEOldX<v-kli7p{YxT=Q?*nAjuMT=1Wozd{H0$d2g=qg-G>6Jz9uRW_Rd$u(_'
    'I~Ug9<Pi<fUCHAGmL`<y$jw>+*PXyTg1Bz=(PFUbPP_pLdq>HR1?(+F*2sMLnZA0^bnHNc)%kx3YU*X2X6%BdZz~Alp>eFAV39lU'
    'jj!Tzeye196VdhpBL13L#a{L3{<3bGT=_^qwyr*iI{!G~AqN!<ejONrVoe7r>o*;XYW_EBFte5eq-oC%gDy9q+OPfAP<oIU8#$5E'
    '6dX4jHMVYYvD+(zBUys7bhGux4*(`dxt%iyHktWtL-<iD;_>pm)l(VMi@%{Nm>M@~xZsUUjf^~8^-td(KUUib-@ccirl{<&z8x~e'
    '!>LJ`RIcdhiGUlL_GHO->3MxHg?h*_PF*3>8+>=w)=cF^KnBY%ruXCk0T;ifXP?w_w4^B!?8zFN;c42UWM6OpMC*?M2EKc>#rclL'
    '2xk8L664sPO+jHpS1qZ_+v+5(9Q3W;eM_tM!(xH=1^OuJe0z7gjE|UCs2+yJm!NhOfR<KQNXpDQd4q>tR#T@G8GS!+8TTW=7j9Md'
    '7e2|5n%XHhG&`NJLbs_})}Qq#dl6m3teJS4HU)Kqxt)j1LfVp=^kH{~8p)W4KSt60NcM~;ysm4F9{5|eieD4K`UL@e_ZX5qWQaJj'
    'ozo|DblyGeK=j|Z5h(`+_}93Z&xI3h@8C-DqpWjB)4FZj|2EJ;iu1Ulqr_SeA7}+)p1zrjolG)%A<(hEs4#W%lY(^@Is)`+V(MG@'
    'JLj=KTN?N0D<>Ps?@x10Rn3UdwQi2jw$|?Rut(7JSiDkbzM?2XataWLtb72i+`rZ7kME5q(Yk}*#Re>!^3S@fT_0mSu~QtMd=t%V'
    'p{_TL0vn-V-{OF4W*=l~%|)YX19j?b-$o^x#W`^CIsL;6j>KU<QG!D^c2Y_3n+^w;`O?8A)5h7^ub29NV{l`R6j8s(r1eUd)rsGS'
    '^3bSl7va3p`Q06Z6NsVAX%<<T=#MRkZ!chE50De|A|Kqv#10&R(u347sq{-(R5#_2j?#zNQ>3EoeKgP<m89s>Gze4-N%6A1i!lvb'
    '0tjeX<OgNAEYV<YX(1s?*a@&}Aaww!DcZyp9~^nP)W-ebz6qPT7mGCe{vzZ^)GKI&EITe=y+I_%ycayCiowA_T9BX0ofUMZm{A0x'
    'xVbm9+w@R$VX!jxxO2bnPgLm1>E|FjXFQ!J&|mx(-FrK$>+67G%eXNq4Q5(CuTZzkkaQmc@}g=>`8@$omfe2a!lRr(_hECZi6Z#8'
    'PTeLUr(+W9!u+Xm#QrP&6*vZ53&0xg))s}OwGqeH1O@md=mfA_N+{|uH-OD1PVc=*=9uw1EWsZWxTK&1l(0*_vgC!S6Z6gJdy-9w'
    'LxRS}r%IayYx_L=#Y4H~%Y;pbm&nBHW&}Mh--3%D9#iM~VcJ)RAICqqU8=6kq_?<KuOrdMbHpy8cL>HJZ0nk8gjmYDjcbbiCMi`J'
    '7v?n}el%jr5~Xb{Fosp?4b_c=){AKA3=?mV!S{o7xQXHcjN4OQ1<?f**04p?2H$8!+%9*^3UG8%d*WD0-Pne(M6G)`Rt4HHSeDWk'
    'JD$3|_T*$F!a`6uqhs+myi76-6G6(a9@cMOF4;whizpt7?p7LaSj;b4rHQkX4O3*f5}j2kNP-H(0y=f+JiK(Q(=?$Zin4DrBBeU('
    'pB_yp;i_!l6GAImR!oZVp7eLtej`@Pq?g|$n=WCjk08zVk%*e|3Un+h8EZVQe|jaUS28K0I4ar?M*aml@->m?i?a)1zTax{!uIcm'
    '_K_Jhh+vj}PhaV-kvp4|4;Bz^9@!T=9Cs792u_@qcTk<$0|MZclyiMPqSaGRFnbpU7GD@4m$hbf^WILZ+WdCp0stg>T5JLNarWw2'
    'j1HL?`=m`h4yZ@3i*#ADA-+)b5p_N%u#%rCFE!e8@WP9^E9Mz!2*rBg%yw**LC{s<j+x9N0N0x7a~D|xdIw61&^%=%{D}U1b4$O1'
    'O320Rhz8~~K*iX$Gwesj+7DPrxIHg8Jywr#+~39i;W!A~^KY3`)5L9+C5o^?wgKaP&Ki6r3KHQp_%kAzZ2au(Y<6Q&OLI~gBTUWC'
    ')T)P)IqM9mN}e8A-U&wWa%OMY3;@s@!$+S<SyD?3e}@Rv$JH7<&S^uk1U^jJKtP!_QzpFp`cJwzQ_C8g2K^-svHG&iZS?2Dl*e(F'
    'rSK4+e}#+0E_m6L{`U+wg~ZYBT0^{ag@>noAS=F{sO7`=<Zl5_RX>0uDJeQLkP;!v`mGHHGbkQ59C$yV4oO@U4e?>GA%oPb7P=FD'
    '+QT$DseW6ZEqTEBXNU=LTKkA$^mN!=t2DG3y8Yn$G~2v_%{-P-E%>9TFodzv)P>5t4<f)rg)G+nKfF@68P(0&?hlY9siul#KN`<R'
    'Q2iy87p-mwU8-;7IG5>bPE6EsaydScAJ^_U=m~*8pyC%;02d(KS1zNyg%4b?VJk+@t(QJb%*$}xz0#ZQ^X-E|q4g@8LS2Nm!mrzP'
    'y^!k~mG?oUF&n4afU_QAQVfGKPZq1mmEk-An;KPC&j<huq6m+=Mz3pLwj_45c0iHOn@lSO@$gaLKvED2_&@&+_srosLaxdN{u-S!'
    '4|ReK?lDxFo=5mE4(~7=i+0_ZzO5`Y^Vr*)@53AStLW~T3827N$&1Hwy^?l2y+;N3ZBxLip#UkD8I`@y(w{_Hhm=xE%Xd3R#ZacZ'
    'a3rXX)pPt$#J!%BTxD?NaK5)_@45k6^63cL<hCH9Z{U6mwUaWc%PXLn5#xM@PTn&ez-6nb9Mz_WV2Cmk0y{}w2~q8b=@!ufh@^r#'
    ')iLcMhur<T?x4b13d^E$a`XvFp%n=+KhQ#0yM@w?_Re}(4j<3{HnUQ6(CXz?2!Tef0Yz1;_rg?@l;jmlWWKAM+ArIAhZf*Z<gwK<'
    '9#ZZy<*84RHJRqh;cc&KbHC2JCBiuk7V>O61K7ow>hc?&gs&w-v(gzF;|nT^lQ*{KL$!J6jiKm!sY11BB0gdvH!2(gEN=!ELbMHy'
    '9)R9hQ39<snFSRm9MAY75|n-8sw&NA-CA96`KM+zVh;M1jXR9xYq>F(BKs{VKrvo~=9+W|cy#}`1;H#Tt+trxPpqhJgtKU(yC%)R'
    'FdooWs+U&}{1+a7z6XkfcfUzl-7Qj?+Tk#&Gx?@92A790yz7^v0SDT8ew2qKQ+C)zF8sMV!rit6pC@4glm7pVdLNEw<q)`yG`2ys'
    'nwVKLFL-N?z|dWV%AEc6RMpBAh!@<A6<`V!2kuK<00VZ}tcsfX@j!gj#(jAk(^9oyGFR3zsc;QyyQ>T^3lLPo_3a*M*-uAIH<9l0'
    'PKX;T5te!E5%0B9xUT^T$j52mdqE}3tP}r7!nBZA&)dk3bsfzsrk=#5Eug|SgeGn^7MmaTz}QStyxLz(W3(|3e&b(DG!9Sj5KX@@'
    'e42fbEtHVBnjwH@O(=(pK>Wc`$k_>orKE(YrQ1|a+oV#cW4>;UB$VLq9Lf0s>p-+jY1&MXgJvMo!oRriJ7AgcjPB_5z@Wiptc=Zr'
    'hHNOfja+F`XNYzyBU%4{%9ouXBkYGvp(98*%n7*TsrlIQrgrfUN4akJ3BxF|>1DWmZ&WIs@y*ie=INY$@={{r`mj0eBt8^B!~McZ'
    'eGp!mUz9Ay{Im_Tyf}fERab5ELE(h5SH>_CiZZPyL?x%O><2iSS$Vbw^#*2^uOih2S&li_+HK~W_^T=ngMLFR76G3=o%^}p0By@d'
    'SAB_APczlI{)A7B(MQ`cwXt<q{iEV6LLOok#(;`HQX;I?UJwdHzM`wbvch^I;&~)9U50jjP%G6a6e?zX*s+I0^JFkb-H{k}fja|5'
    '_vnDj!7jJN;{G<SyfO(K?gZ#lTx|Yb(xd>!wA=kw1>e}z9A(c}*H=|GYZ#L_4=}O=RvicMgjuA~6X%X=mOR76q|6pNr4JxEbozD4'
    ';22%UZ!Vk;6)f{oDx^K1q1#^o16Yw21y&n`)~QT0A#LkbNiVz8lD>I3i#=|IqPQly0z#s&2$%ksp!8&Ie(0-+C}f?Gm?@>I-xC~l'
    '-jH%nzqx`Ub?kP7g2_bMZF6HS^4(MPm1crLj@nB8)hG78i=~nI5eW82KpmrtMTBjg8E?$Oe_@6@v-4WUaV?0Ct78aB<{k`CHK`VO'
    'A{~HqDf$M7-7rOYxyX9R!u!5ua9W1|2PngVMR1!jW1$3{==X{P)%s80IO%8EL8uXw!Vu*}C@#mFLfMeBSZBsm)|bCcuCJD*_*L*x'
    '0a8DXUuzL$M6^#9Vr8vidCtT23E5>@WWEm^Wb9Paz&{<kI#YZ=e2Q+F9UNP@)Y+UThR-c<vcN3Py_JBPO)Tw;*H?{)&J1fxejA{?'
    'CXAzhL|l0YY2#JZlk97YiB#nWBflWqA6@R9YhMpOdDs58S(V5qYsZ6hk0xLzJh<JDC&GG)HEkvpeP8KVoGNM+jPRe0{TXZQjKR2y'
    'n-nCJg3P#LkxlBf8Ozj5@Z|Z%J2Cy^#*{V|%qT*MiVxcTO;&vz5u-vkn?xmRrpiXrFEr!Z(57NVJqP3k5oYEx$N=g>Me7g)tUR4y'
    '#DAPs>$>X8?&5N#+vZp0PvW3YnAC6EZ)7-Bn*JeL=iV&=G?S5b+z=q%UG}d*2#i5K0QP_~n4qf=cf-Q6PVgagtb=Y>MZ_SA%PPai'
    'lT`zxho?U&!V!<$h#R3+#xhldBE_0W?a;Rh3Mfh<znNxI-JmW0z}|ULWiu+u$Ys_OV2rS8aPL5Iuz{DMH}w#CpcY*MX(O<#zBJ|f'
    'gd%;H`1I>J$FQ>lW~WT+#;+vE?uUVLO-owgbWptzGN6+X0J0z?4mA?=c;CgK8wV5${x=J-X>!*T*8`U(D8+68o&6#yzEZvzIhP&-'
    'sv~>^pOqS^VTE`?rGtq<c+JRfv=R=T?l)mRGc_X4*pL^#uo$r~$0LYYwhEC9F8o&Dzx`+Dki#vW(1)ZG=L>{Do?f0B!$8)Fwrzzw'
    '?TM-4j;xydGE_gcA>w?+vZECdcWnV6Jiw>EkrFooo5XivgN0;tRHsPuj^i1?#q3zL>XY#{hAF5my<YC?MQbDy^z+Cuuvax$LOI<N'
    '&6G7Q);v(A@-$odG%frr>|*GYL9>UTE;b4+9(9+(SzC2ebZ76uPU)oNubNn}X6bP9xYUGa%}ZcevHLDs{_G7_QtGCSo?9VNQpT{q'
    ')&We4qCqve4;A=~Nq3WV*rk_iQkE+LgfpTFv@ON>+Rosji&f7vP+IK9!8KL!NV&T6V)CtBmrb@85~C{Z0V#YPtsCyHB1~y@eMwLz'
    'M$4pOJb?^?K6~HXwk&C^nkvE_{CbT|&y`O)%B4(b_h@63Zk>jtd%=vZVq)_A0;oILL?Sn%y0_CzF@+!i!5${03{+61Y5^M;PZ?c#'
    'j+uPJc5#Iaf6#r8h%B$gUQ-eQ{9=(#Q1|?y55Kq0;)PLcST1DyUj&j1tSp)Ap(f!6T9~%2snZGL&EH{bZJDRVA0N)|U2H{7ZCAiB'
    '1<lV9mAgZNcdSV=E?Otx&P6*wAFyBL6zgC3%nI^<Qc!c}FT7}(IaNY&4|jnfd1#SAl923R){+Rv-}d2bdHB8T7?;~j?bs*`po2w?'
    'fz3Mn1sVw!iO$Y9091u!s@$#yoTSqf@!L;YGK1Z79dnSNT(}ARv&()<cA0SGk`n&j;=D}-i6I5EKCA0!rM4s6aBDN=;pN=+j68?~'
    'e7r;5gPOHG!t}Q?{s-xA_q84b{z`?ib#D-#tQdx2nD74pf3RVz<nec-xh7&m`qE_Ja6~4}fI31Os&2<jh?aJc#exVXO3U(WCWa!s'
    '6j@&A`M9tBQHn|#6!TeTKD?w;5LcCNct_;ji=_;zkh;u}uAmaGc*ho|-JaEft5;7-jIEb~k-XOSvvF8o3L@&GSDU-=Aosyw<qWLw'
    'QQwYds`18Y^xM`dLKXqF2l%npHQdDB)EOpS@$VT&9%8Qv3e63q$5`>)?;TI|TLFjZy~rb&feyI(v3Lk1@utZ^_6O+v)k3lO*-~1}'
    '9Cx5BM_DKJU(ZG0W~I-ZGhJ975Hi$<;9*3gn>{sN@kssqBYeZeZCjZ{ti_a+Kge~1y}gk|V$kHGM&aU0pW@4Ham4vM09&hhSTG9Q'
    'tuE?xeDyW8CwZ#p&l|{-zwdipMfdCYj;{T=YBD9>rx33Oyu|!^x^r23ArvBRf2)9^6Zaff*4-W5pEe!1phUoSxAg(gXd5dA;zNXU'
    '6Ymtuk&k)kx$skhX)KHDrz!|_3yK~x5<i-Q@RW!+)gcnWVIsi)=^vya6AoFE_R_@_ecQR(ASy`*_u+(gLp4xE0c3s61eDWrs<XD@'
    '2zifn7!aHEgcf0nWzmUNqBegV?=R0q0F{vl?o)ZlS~elS;9Ti8<-Eo}j27xm4z5*~;~ozzHX1<Nlw~73dIP)Gu%AhxV%^kbV+5lg'
    'TrIbJmX!4+^Jq{m&C#ESG@wl*SfeAWi}g^QiZI8I>S0fW7YrBlvdJ#X1Y!vzE{t&mW08{U1@`}6Vr5rbAekyUqEaXgO8w%a2?leX'
    'K^DWwaI?l;SQ+S!f0iDLTi1$}N06CWJE$ZV&D&+zg(O{7_9KGK{=lCOIF-&j*e0MzPhueDkJHfi_O<A}o$>kWQ_#Q?0IRkkC%GY}'
    '25K+?nEJB22g~y^7xB%U|5}x8H6p<bs1{gSay$+b>UPGNgO=lCdK_cMEldDHZRAVU)tSaNIIkeViI9$eFMZErx0NQ|Q3$Vo9D9$M'
    'pUy^@CI8jVxj2p{V7v$>3%e){t4Ri`Ps3W<+S+9zb0+qY<JSmnQ=5B6lzYw~k!T)}EWMN($)4_lCUUgLF03dG#w#gE^WCAQ*CBCP'
    'a5TMQc<LemszSswUC26WV$zns<41uVJXbQEVG$^&YaKlgJs;Z(j!(EXRd}3I9Wt%zD<E#pBrIpmH1%vR7_uNFm)VYP+WF?jKvXdv'
    '&oIK`j+H|+xbKoA<NXB`y#-?3+<wesf87o>$f|-%nx|kBy1F5fwB`g<v;;NvW+H5U1<bD?B_kRjU=z1ZfY0nH!o$>IcDceXCeRbh'
    'Fux}VbBPl(H+WLAQD?MC_RdPIv1PnXTzBtgnmIC^UUAl1ITqo<Rb9mL(EV-xymv`bZHEDRX!|o5j1!caPJoIYM$O15)*~nT{DI2^'
    '(sQ6&HV!F`Q&3hHUbcX7?k3mM@~K#Ue4v$*Pr<h21^R)pQ3d;1CL0ay`ZQxD|M6tqoHFUL)X*n_tV{2DB|MA>CCnY1>JPY)*E#6+'
    '1O~&=;<Mixvqyhj`_#3>hW!J9@Fcq}*Pwmg!kwkIVGUE``B``WNAlnQ+$>k7`JbT*A<RMq6?I2}TE!z3kCO;~Pc3eNVK)gR0$_|g'
    'jIjU2z0b2+xc71Qm-@32{s+tJ>w|^9s_Emfq~{Z--Lz+8jaspXcvJVDSqa7R^v$uX=7vs8Bz7valKL;3F`w^b0f&F!#fw5HL-@Ce'
    'IFGjfhpT%m_w+ZPW%SOnF$y?>C}X1_FebJL!y)OyTSJ4B`2m5ih$Ts$>KyOySpTZZ7||&|ans@rxw)*+sF|R?4m&u^N^n}*=sY9A'
    '_8K~%S+Ik)vk-}SN>@$J^U8x9&h>O^Wft$|wnN|-mPd3vijr{&_R{Rl2o1%%T6t=Al7pQjiQ)=rh$ON91<NfHxu2nobiOK38#mPj'
    'wa@CRu+HCKPq2PKCvuEij$VP@DBB0f3|KyeiqZ!JlMr*xqbiDu{i&PO57TFXmA!GKrUT1hFDwo<e!gT+8=1b&dL?WeR_!;~@+$F3'
    'x4}L1Z?bJbD69tmm0=YRm})=G=hN(|qfT2?IpqCw2<ar%V#{?SDR_3f&>|8I-F1}snCO}LK0K<xdZYF+><Z15$`K0ZYxA@b)*X6L'
    '^TRRP{a9-o)$8*h-=`X?sm~Ypo+W4eZbvPluxuJm<<j@ZMrx#eQH6pmH7vi2-E_2VlEn@Mj?m8vQx4o}4&8nPo^(1>59bfDm419x'
    'L&VSVA4wO)`Td@@!{Cs`<?Eld@oS2eT%0Gy&bPS!m^x*!_cGi|6r^vlQjNPX{t!%M7V--O?q<#jCgOWx{I1MM=yLqoHxHD%%VgZl'
    '+h8)~yWje5t9z8<GtB0|b31JKkKjU-xj(h1>T-pNUQ;8R2RV<KS-qD`!ZS}}0vI8~=*YatK^-H3_$@(ms~+xpC?HXp-m8qtB&UsZ'
    'sNVvXNSG6;Px!LSXrOW>q=rGKN2$Rfkuo}ARWSG|nS{R_qEE4~J)?(J&0R!uugwg}2#9q_TWNkhJs7HdFV36(_ix==IY5U~#eC)t'
    'v(Df88H9|P+yEE?jHXwz{UF_Vhe-YIRjH+`b%P0a7GsVq2h*%kR%TJKnJMn&GB5rG(Z^zzlg~$OU(`V+L<716nn4wx=4^zgCv^1w'
    'muRnOO3DUDp$wuYmyXiF<Q?Wz-aCG+%Na|kLG~RGvKi&+S&?Nw;m356VS=o}?E&(oEd@b-(i|+ZjZABujSvl1tiG})sA)TQV#S9y'
    'b|@2hWLApkZtaM&#*<3yrW&dsq<@KMP0g^S|FN)(+QQKvwJ8I&Z@WUMKupf4ra5@y`QngRHmPi?_&^INHap^kUMM1{mifd%PYS-?'
    'ISfHXAyk@`$w6kZ<siwM1>MK^CTxt`4l1uXZpqo7LetlCE(xf$O>w523D?|8juP4U!-;RNbaztDjKenM+wci3$v-QW!h->=B7#mu'
    'Fo;6qLJkl}CHnSx5wUS%LXU@~S+%os3WpQ4z*^UhAs9DX^sb3Il5eW}BjEMWeCw5RjK^wbTe%q`-@~f?5~DJ5dT%TwbSf7b7|Y0S'
    ')`!jR;DgjZ$XEHgi5&PZR$!Q6{4H@^&Ox0kPm>QShrMr%q6aEn*yu(oV-hQ9{bC6d@%jH+<MD6)Wa``bb=%(9gv36Q7+9Y2i`BWm'
    'FuEwmf1Cxb?WM2(jnuG$*$xXO7Xaj+yV6SXv%$5M>WR__OdeX?$EHol4Z#*mORUW^SEMUrrRP*Orp?LU6nE2t5s!kO-v7w8d0iF;'
    'V!qSdg!Ws;3~zbEPrwvKQTfYyKXE-lw;uE7k##6D4W4S<N~0ZeQQ6%fg(8)LBp_9;{-FLGNZvwBl5TTce5MKo83Z*UWs<DH(ou#e'
    'oKgK2zQ}b&-4NM%;Sgh$L(5+=$K@Y>bt|r|N!=uuR3(xF$5sEf6mtD&DM)HLdO>~-in7UL<~;diOc;Sxt5Cj|wlrQxNf?k)aiu9N'
    '%sRC6`#I$DDv7{H#38c{pm-eB!W<r7a$$z89DN}j8~`k@hsgET_L$V)xZ{LpP;_vEH3nSPtO4+O&HH3<z2S<73Z*2vbE3w)EX^W%'
    '@GRLSV7(z+w?)hEI+zV2s|84+Eu-s>y*qU~xUuf!!iDpH^<z+8m_TK&+N~#gKNQj&u9SrKfLuaoBeIh!m{uZVd<dCTg;5%kleAwn'
    'oexz-W~D<UGQArlX)5O6e$?n_e)*Fv2zSXZdx}2p=$lEtqUs7Ud9*8Ehq)(a#bzH$;zewgX>yu(q)13G4B|a7;f4aqFk&t86m11?'
    'Al2zhDM<De{O~Sn^kjdnYZKW9E@wB#@QQKKx^T_7EFovbAt+8;j??SCprI4hj`6CGN{}pG%r;Yg$1`$c!vvo@;yuh!?Nv^piJB?k'
    'Q9nCs;4LPEUx9`(`RpC=exstsu{8!uY*Br{+qyNZt7qfQ9#{#2(gdm^m3sJo1ha1d?BYWLaR38UzqXssLYTQALl9BfbEAr)yyl|;'
    'N|Ib_N!LPGW~#`V?VRE*Z$VTf@HNoDF78wM3*8;9U=7iLCoRqyEDZt*9T|*ilc4W#!P})_EY3JG<i5XRsJYS}(!1fSZ(JkY1htLB'
    ')0mSgTgUYP6C9}sb(If_2SDUD++l2(KEHw45_lIX1sDFkNSf6M7sW>JlNDq_rnZ#j0b}w)DcA_GhAJCg%_QJ>0xHedxCR)IqBB_l'
    '`S#Js6)a-;F{7CCt5b-(^kq6stcE)<Ln25Gh=%Ax5<N<agoUP^I^X{j>YsVfwRa7a^xdAaJ60yBw-T9vm<6}tpTs3ay6%7y&f<CI'
    'm~OOM=FNWgn3LaVqZRx6Ls8N85udn>6r|j3-h%Z)ja-V%muiw^6Uv&|g8qCF4vnMr9IC&1_TZpg<KDAYSUa5E-0AQ`xXUev?;p}|'
    'vKvC?%|YSl=L>o3(5-GY=l=u|rZDZ71m4&gwqf?+x{VX;zY{0K9ctMW1?Lrvbfv+jY3-l<gu=z{qn)=ZlYgwYBHBXl3vaMVx_u`s'
    'PCjjWxrRCPP&WqHhOd-Pn&JUw<j_Fk@_R3${bE%B^o8<HGU%k-Q1GK`Ekd146<4!rYdVGC1ZtY@HNKVr5gl8tR2JHj@%j2EiYgNz'
    '`}z_1t1Ci7n?QT1JRww%xl!Zc*FCWz1Zp;)qv=&P>H+Ymbr_{KaS?l2XrruE`7e$%hlTdUCWcIi0#%~xR*!~DYjmK$>`Yn5zu`Qk'
    '`9fw~3ZyPd^~w5#1Ro%>y}x*vZ<-XlI>BGz&7@~pL=zymIz<8H3{o~Ml^i8491;#n)(aFUz5WAR8z`JAkPb0!IYib5kje~cMH!=?'
    '^puwW<Wy67y0!C7Ht*_V`@j0`y3Uc1N8`cXlx5^_l=|?v3=r`S{;jy5&j$)}13oyX8`#LY+lPjr5N6M1lb|`?(JS6O7`(Ffk%4+>'
    '^)QKYxV7d3X&`%|2xV)8`f@EBQ@H3=ZF*Up4*=9p!YQiQ$pc%c7x5`<r91w>d;JZr92$*5+$)Pp8I`voXJwY2N|F6h<&7to*#AM)'
    'xQwv}L3a!p#-J(WhD)hctN)2bB;nibvmwZZ7APl*iu`vOPbT;<8<#qJ_@Gg)YizD>93NrbF9Q};Q3qWsx!9H__J!-3WcKsz*_1T_'
    'npWRz@%9~&8ALikNn8SNlPs5YdlY`C5d0q%+0_?ae<Q@afS&1&p)Y6S)usaQo^;vO)KbEKQvp@g?Wje=(z2C*Z3tr(`TPX}y+YKc'
    '?%Ep#<H{y9Lch3()efD));85pA}RKC`-4OaLz+WEhGceP;LSWsgRqY1)~E&OXIR{CTKm?MNzin1P4Jl4=YCg~S(V4y=(R{hshaX2'
    'djbI5e?CytPhlbBIBI8g$wTbiQnu?c#}b;wOHqj)g{)YdQsdfJO(acr`IQIeVGv^0-g)~;P8~OXq`I#=u~hUv12x909h?e63G$5d'
    'i8J=%Q#YpQKb%NK5Z{WrQ#90+0P8KM>NwUkKAKX9^*{RF84S}+FzKcfQ@zYKXt(m(a|Av1!NkK`cjit^9(}FNe&<F452KOl*s)qq'
    'GO@3{@1;?8#DE+Z5tUgogD>Dls8Xxy3Pq7He5!DL+KNz4sGng>pqZGs8X95Y!u4zSEk<~MO?==<l}WH(`$q;5s;A9qXVC~l6q`){'
    '#usd)eBlH)n;*KREk!Jx-Uk!|a(|~Og&3<Mv7>hNiMd^tI}8(Mib6np3wu;$D$KxBb&4dF$88caxKBrbOO^!00)jJ*%|v7Svhy<n'
    'k6LiT9}UmEa+nk!y@~?vHTLhJVQbLdUy!G?HI`I-IB)QK2Y13Gh4?8BUB<Dmll<E(j8qrm03p+514P-b!-;^-I-p~AE%N=Z)J`l4'
    'l~^I5v(q(4r%%R$9MS!E5@g<LvJC=a2Xn@{XFp|Q@P_y!Me`@iXrCE!ALTkIkI;6BGJgx7l`>+|JXTH@Ef=<M1n{lYdx*(8Q0>5v'
    'h*9sI1NgVxm1=umFM3y^UFrTp=5ckHU={oas>P{JmL%W7btEI+bytRk630c`$==C>X42yw;c*LpBPTnedw3EoDKHYgujDX==@J5|'
    'IpF5mqz8A(T6}eh3QcuX+Xz;I8ATXsR@zMGD+#9+HYhH1nN*EP!YYVDp+Zl(HngIK5xA@GKL_H-laqlDiwVV&DUl-xPsfp*TIUyr'
    '()D|2VanE~_c$8{j>Pw^6phV}bQ!3_>?66+qMM)x4n3WAJ&qU)f<@FdliZkss?;7SyqZ>J!ywSjkh)Mtt}7K3m)660O@uy)8oZtF'
    '3t_0n4&eM7fD6(EI{8B4I?@I1goD;AOx1gC7atY9-}R>BTJT>WixNZ=)PV0QFE&%BNjn&4#FE?<v5Nvfo{1u7QN^Pb2!7zuDFBSg'
    'x+bCS;kWFqdwfcfg!%@O0>rkrzr!UNRlHn&{Giq-?$78ixXG1zQ$24iCD{I;s7!8l4r|{h$pHkld8-vy#02N<g$-F2TPb_o6)1YW'
    'T!|B_)5`tP10DZicun~UfoYa!_T9`c5i~X{A(E+L$}!Hy!_TZ=dHZI05bE+g^?t+rxZb;1<lW7<Fp|ov%gwNc?Kd&t2^E?rT6VnR'
    'f8*(hQ$BN<e?WdqB6-i0|5KEry3J%s-!EhBzJOYe3=hysR}6+Z8rb^Ai+mN<0cc3NY3tw$noKkIk^XOI(+4sCz*V}EvByKu)nU8)'
    '^7aRyoW?x~L`g%vV)+~{$c()^qwYo&KysnM=iYOHj9*%9r%=SvT_kb1ngKZ*VS3}`Mfsbn$ZKJUDfis+jfDC7hnA5@3^;Sb*xREA'
    '8)QBEU}5p}&8`DfW2Yu6X@QQ`?{H5eO$rBPfs_Fe-+43Hv?<gxRce3DxxIe&*ML1*yI27#Yt#qx#RV>pt6F-}SM0(HduSl<n9yRo'
    '@QIU*=d((GQI$zgNa3)8C-IAW!}rc7Oh<wdeoU79>GFN_YP}N(Sdz1>qymLc1C-R;`$G4x;7ccqvyK2%gY!TNbLqet9MxctgIxrH'
    'b1w-H7aWvBi(*)_wb+sb?&tpW5><8I3JfDOF8~=qq;TSpTfDWV`GvlTwKMu#F9-bTB1J`C{aTbo{`XO63dAnE(vIm94VHECOqS94'
    'y6h}RaYJ}a9s+EIPNEW;)77#q$mp>xK_QC%hbry<aYACbdzfgsJ8ra&tqQEcq4UA&*Yv-DVV_V;)DV6o>L*7_x?vjAz&F2vRqf4g'
    '@i2&_AT#+1HeIe*yZ^MuH4p*rTDXWl#@Wqn8fDeOZ<ueYic*WqWUg6-Fryip#q(7@X&bK$Pl!0;H24`^3PFAo%G}fb!CcQ;f969@'
    'Dz&|cB_vl229kd<+gt>;KO#uCSKw0xa{mHous1{rPDEBbu`4f?En8LBv(nSZ;^N=QxJS=BA8#KZ4WHO{`n##BqSRE==4xKIe({s!'
    'kY%VPSaJ)IQ;i-oEqa->Ic2zGq<fzbX{aQX4>Mk?0-)sSikc3Q#;k{rFB77sAPBrqLhzksoZqULP!-D_m`)(}C^uECMZJUe%nZZJ'
    'N=%-!CfwRS%-tWHU1(pGm4xTopl@nLd9Mg-!0zFRC@aVC!s300fW9{Ho7YPnxxZSJ5GEB{4EqB3{?ks6khnP2MrYyDKyAoRgHGaw'
    'Zx9y8<b@#SCe1uf><SZtL5s;O9BFmoBzwD3)Blcn9VJDFV|};ok7(=5=54$|^}RyKsMfD)p($Yy7J*_h#cjs?`o*ab(u#?@)8v6p'
    'k#}dS=zaKCLebGt2Ue%RzlUG^rC%}78zWPFeqp@G@)T&09|(6o&2d<9tO-C|c+@?_3&-)FyeJITqy=FIc*m<rq`DWt<f4c`VBbit'
    '0}8!%>#3!(F$O2dvS^Ly45}<stWt47i7of7y@;MNt`+^&v=Z2~NI*Cm3ae?dcW%-)lec-k(%mmq)aXAN1Bh>*)R#T+#z?1w#sWv8'
    '&-^9=FE-+dVhq;#c<Z*>YM(Na*da>`A+M?gZIV42anlOoDmWckN3eQbY13?m*n#9qy!ARSU&Ytn8KW>DJ^s?^Iz5}Ww#MFly_v57'
    '>_nGaAM#9Lc?|SQ&{i;ZtKYj&wi4X6%pt0}l8ZF3Mk`lO%a*9Xmep!f4W8homeoIz`(;4Y?TkC9mPOu1W8)tOs{@TW*P4~O7@Y6w'
    ')=3)KgM}r*E4`sfXMokxOYp(nqorQ*?5UQm_l?2E(I{$t(eTZqmp6}(FLyBBVu&VTB<|22b~(EQh6Xoh_J~M@HjibG84k)gM^Xvh'
    '6^=_pDMk2^$5Bc6x{-ieUw-sePILqM!&Kr@c@+0T@REV?#rBrIR4WdP+X41E=jl||+ZcIq0E-)ld-p>_7b)D53V1`&Wm>(u7&CG='
    'Tz>qCk~wj|Arlw5B+);#r+DPOYUO-v#>5PhUtIH?Uniw2oIeA5qlyOdN|N|nmY6t9y_ZjSXW@;iBu54+7?T=pP+(?(TeJOtU`e$-'
    '^JHt>HVZTWZv~6l9wXP$#T$EKRKG;Jf~`PRKfbK}qm>1vcK=Cs-6p@^N_~{m-~a3F3XkQwzp;o~F|=By4o!~0mB^U1xZg%k(R41%'
    'd^Re7KxOU0*iUgkT@p3U7HcTx>8Z?xS`aHdU~Qr>;Oo0W5KJAPn()v2!ImqazJBUY`_sb*2$Mc=_riArs3TgO<lPsG3V|J14%mCd'
    '`mx!M7Mm8!NU>lhU_ZsU7t^qZ5D(U2>Y|4<lKn9HO1x>9tB^zQw7)v39a?7gX1%>J3&D(7%mB?m@4CL|dkqPcSY!m;7NG~e9b2c!'
    'r9d{Hv~Mc@bB34)3l6GlloLcJl0d!_n-xg`csjW<?PN3i3+i@wS0DeE=?yWn669OLo;Cvi_vCC;c*Pv%(|j!@MP|&g=LCd`Zv$WS'
    'r09tma;<iFXqXN{5t}P1K-ya;!$x8uYjXWt;IIo?j`FBOMScJ`*+zUwv|KtvTe<N*W}v&!-t%o4K4Fil!8PZ$`=0$3dj3Ew9Nz5m'
    '{M+TVv9i4c#E-zBJ03%cBA(KnBgi*BPN9j0MQRwLs!Ts)-G&x7f#7KmdV|{vvI~OVGHDS-ED=}9SQ{!vm)s2DBvYV5jsdyUkXw6@'
    'mWrjXXb1Kv^mYes{oU8CS&MGmZxTrt#!VutJ;E6%Ru%x*5~{C-I2}rS>c66wG~S0Zta)|5+t<GoJUG-fB3lFTvwN+*Ev8)gS>x!!'
    '%NyFIsNh_E;?kW7YYdnmngAFSx~5(=&_ZE@09f^`Ie?F;GSy~@=M?%UIwy?&0pxe3y4LiZjZvQl3r6h@2bHGe0c2{8Ck&oq0q_$>'
    'VSs6G)}&gOm_IDdQZ?Ra*wwO$dzndJGwAH+h06$BEt-n~28%UtXqZh+9|<@O#0_yJr$c~sh>${~YJcUq{rCpZZSqz}pgpP_&b&zu'
    'IOHEXMKTJvJe@#y=Z1rcG&hrBG>v>ne84bG$OZ2cXE8wAvC!rqt`BW9@H3IJVy+f1s=A%+aGUGERkvqH$KuK+GpY!>aEMceL3S=u'
    'cn?Y$>veaS=8>-r`?o1{bS;3ukxZ0CU4lKP*s>rg4`(p(M6^!|mr%aoUin@D`xa^=$;-qnF?-pL?77DOmy41i4k?aGYy!PGFf@$M'
    '`1R#M*W{tfG5#?sC=Mdoe3qxYt*gnT9pSOovbL%BRxtPQgy87-l*pX3s4*Wq%?aU|+u;k$;_*&wE^IXzE4AXp<)C*EaQWEO|CP_c'
    '<lS%5``Ox9NfvQ;EUh9FU{!;%<8&ZNt5TW$c8nS^>~OwHjzN*W&7W0lN3ew1>EJwwYKz+W?|9R2H$4pns)V<y-ClqAE)MYyEV)d5'
    '*DRa2s*l(tASu`I890r?m$8yw5xht%gokmAEoe0{Sy;y=3@LYS2JLI|MK00J+(WaSv7AhCDOFCk_ph}q7lN>iuq&rlEdw6S&naj~'
    '?(7w(7Txs8;(f#;t8wR&XJUjK#Qpqj1lf7FmX+K_1(mD{7@Z9%@WY^f_wm-^2hg0)j<W>AxL9;3=H-Qc6coVRxeAxz&9Q7fj@(wm'
    '1r@n-9_#=p^0^J}@O;f~$BQ(oZv2sc{2^99f7rb`gIs=57TA+icw}rSL)9(v65b%-5^p85P}R;q_DwU;+J|;oHY*Pn1aNbP@WwYG'
    'fSN4fSes1{+EMD<N#>tX8q9BNKkr6?+O4t;fuLE2^^P1m>33`&J1vHNZ2-V7Ko<tLMSXeXCdb90-99*-#E4vKZJ-(h1^Iq5+~XxM'
    '3+vjIt-?iStv~*07YGLr3+hLdj>W_Sg*5C?Iw&eVL{(&A7-UPJ0BeD<br>spnXD{ND157oh^0X|#7qAgLst{aVS53S&>QYKD6G`x'
    'L;03*tA>dEKV|!6pR*i^rip8NHv9{Q;Bp`PxZQ>Ng94<=Sd7syw)Slvv}Rj71a<+Gun>(Ph)g)?XnMXV**<VJckW#qV<AAMoydp!'
    'i0H-Hm7o*%vynCEK`)AFD9xXw8#mZ^+Oq-k0;$L#DK6c*R}=@M0<%`F_D;lbZdw0-a^ud>YhX_R1X1RFY@~SuDKnyJyve20AqW*U'
    'F3l`{Nx~<DN=wFf2j^Q1MmunmdX`v*6D?2Xak(Xd3Es#)E#!Ajd<T2p)kO@u^b;_ty3zx(9@0iQxgLVeVTh`I(f5Y+Dlp?%n5yea'
    'B21cRGA%xd^S}GfJQAuTHHE<}NT}ZHc+mKQUotD_xmKaN;@vR@IPUeVN`!%pSG=W)EaX#(zjt9ViQVbixn(Jo1H{IR*?9*vD}fs!'
    '@An$Gh6TiMX@O`GFy>F(@MG@yy1hGbziis}rBazEo3!)W<uJ>{8>DDEC+ElH0NXQ-$H+ZGY-@l6JejCXYgG3f!d*ojnCmm(mS(tK'
    'ts$$%%<iZWv89t+xLV}!B0g2Y_H`MruYi1Q1rxp&cP3n!Uprl}1eGD*R)U4aXBueu=c5L>ezl=p$~%{D7(y#pBK)6#i^Tn@P9>V^'
    'WDo_O23J6eWE;%pY69%Kxfd`>@r^{x!6VsQi&6UwIlan*9b<i~8k#zcQ4UdLX)Uqq*uF?U$MOdF8+pT41V{~M4;5oPCjS2%8eqNe'
    '_O0LHp2mUno3Il|vXJRk*b4P6t*CnqgvjoT0Rl4P=FtyG94?V#DU^V04EJ!(xA|<%Pk2e16!Z7UjX2&3jZ3h*WLSv<36)eeJpuXa'
    ')G7OHu-;&lAfza6;pG9+lxV(Y=*NVYi%aJIy$%x?wb&bU&6)p^&rG_^%zK6+ls#fEg`Go^9mY(c!*JB%@=cm;CDb0vJ=Q2w>hrA@'
    'G^11V@9ZHvSN4Dsgd!W*zo!Br4hPTp?D^wZ-JYUPLN1cU7CPBIKd>`p=NbuD(?gwMzj&GjeZoIL(P0KFp(2TeWkao_A>@tSrzi!e'
    'P02yRf1_*Irda9=O_ABNM|9DItL{5K&IKv=2-+~C(D*hkK;4NFo369Tt6=U|bndcO7bI7ssllhZzOpGCz=`emkjWro1Uk9|z+!QL'
    '`@cA4x!M&^)Ft;sPaq71a~avGW7IY|phU~q!QQ7Ca(3f=<{ga)ps<ncN~Q*kZlT#Y{-eW~1Ga#G+aqt9!9H8N^%YGFD-WOKz(Tm#'
    'c){tA%o@kBMMIvms?*+UWB3e5+|Wj<W?(OpKtb)lqCE1YIbagRGxGkYlZzWkJV4Lv2i@ga<1S+F>$8_zhl5#!(`)p%Bw_{bA)3_R'
    'uol@BzcEjX|9_+H&zQh*6^@ies;=h*i_RF`LjxDll-ughfQAZ-0qU20GHqsi*pl|mA`MXrNP`<#o+wH0C9!>`FTWrk*N!6}39b=1'
    'AnoQw3DwI}J691HFKI!OeCy315;i7r)cD2h8iRDbc%NWjHmB0#c71@Zq}t#D-|A7U<=vHEGGR{P0e(k3_?V;W&|*9|2!nW@%=1Ma'
    'tYo&)8mz@>07!=aU+lF}`uD{KK!HdwBV2x5m?vIa`G*G=iGlUGv~#Y!N_>8D=IW<4ISuTG*QlV($5+_(x@@u2pH1wqY>DV{nT4$3'
    'h_12wUB&DUg3oz^Dk(FyNMZDYPOHOwTAGt4jErab4ucE=`v|CyO`iaX9h$l%FF@!jU**Mh_8&1kpK`(BO9_Z}3v<RhjG&AkE17h0'
    '$wq|Nq{ld0XdUz?^@R!IJafyofTOTecyrpT&{~A7cpgIWqiS}EjNC6LZFsP7m(pZL1Z55sU}b$RB|4cQW)p&oqV&v2WCrn2#I|@{'
    '7H`~<C}6zzh}zhWw&lUt=8Q6EF#PUxz#^bwE<DfX0CG|zc2E7?ylU2*j=&@<Sj^bay?(j0P}+5eQFMwo>^aXLwRP$tYHjV|P+bVT'
    'T?ia$;IHm@cQsgmaaG8k|Ak&QbZ4jH*g$^)y(B><DG-6*hTyFOv#&rke6~=f+-ln*^>q?2ulU&0?sHbD2X-&<!!Muz`Y(6EwV1t5'
    '?k|OTA#(3n)sARHIPo1)0Qi6x#Sgk7!Ak1^$rmc~ONQ{7C)~G@X<4)tHr_NlY9BY|<jk2X^yWivhe$GM5N<L$3=C9x3DDXf!YzA#'
    'Z7X`U?6x8zM`Pl|mo1EfxKh6B5!etzNhELS!)>F3b5cOC9Hk$8WHf9N)oYBu=jwOJWKDGAv{%2|KmJ|WqWlq1h#{cBR{j}e5LNLa'
    'GMxw!-YgmzYqea;{G{#z+{CA&OeM&H6X)CEa`y#R=_#M~gbI%TpW|cKR4}tWURmcR%>ttwB@Sk>gaLzLL_T!=t~(jVU5KFhycb;('
    '6Bc{0mO*i67c2^x$OvTYh<(Vg-?{sl>@;JJiIQlnmTth#3#OPv=Mncib`<{XJf7{DfErX&NQT07B?RJMJd%rH;-E^XtW>lksi*62'
    'JC@iU7cH~C3mcl|C1_cRJH^4TKP<eT%UwBxw}@XL!>(s*H93-<Jr!voxv-ll_gMpE>%K<AY}Z`Z8HHui+}y$@mLYmU@3YNgQr=4&'
    'JMIJTxWN>qpA9vgNhbR`LT$~Zc&}R^qSIzwLngLarD0M1up)<u+)^N0+!WA>IcT9eawZefIXZB{7ei8tOepm~%?4-XaU0c`fq0lJ'
    'F@|apdlr(?dRPvTS}X~pMC4PI1W2685&&St)lHlxbM3q{KF8?fLx=ng(lI$D!F&Lzz5&XHkC^=8P`0D^tpMZYi7-&NHahtnr=~KK'
    'N$g*?Sth}6xI-T5kEhW5Y~Mf^3%K%;Kv9QNoxy!E;=oO>$hDGLVHq*l##C5ZIs=5xKr71|8#;r1HV4I$ZQH>QNI6LLjmg5D?mO1>'
    'hfTiEBF+rcvuJOa%^}&~^mVZcG`U8-+T#q*9Q+Xpf3u!T%ns3-1_<c%?0H9yazGOlrrQCnT&D)S-~)MI@NPX4kKsIi9#qJZMNG<*'
    'T*&Bn{gN6q><ed!*do^F;>N|eW;uB;5Cg8f7)Coji2DUY-_+0kF2GG^>k%E$crd`%0%=uP8-Rl7Pw<3^!f5ChX1%sxNrZNZFM$-X'
    'kDG{3-+#T}Xc#Jsp_{<0W37i-mdbU6;+nA$3*#A{>xU^G<CvT_#h8OcV;b6eDCAh>Ki+y|+?IdU#ZCc(w(mkLt!2jY$eEqk>4~A-'
    '<=Gr+CpsI|oV5B)2~MVTLmszT#UVZehqPT}{3Pt5he&p1Bp<FKHEf_PdYU4O1fJVoh8>Oc0(l`yg!fAhg4VT7YFk-1Z~Jfgo2mrH'
    'm4&@Zq(6TwZDdxlT|B=*=ha2Eo19`$-ctoFM83N`Dq&GZ&6l4cnLJd}1Ie9a)EAFbdIuOVdP-C}%fL6bHNNS4;Qq9lyY~A~l4-ss'
    'i1`<nJ!?T^e2P>0n7J;~06dD3Wb{i`Kz6-kED?$Gw<5ixHd@c+iifYD%R7buD2O8}rfrxR9lw1ZPwIm0ql$a}6F9iIU^m1?n({A='
    '$j{9z@I_&vIL77o-di}AY^Ai5r+yd79osn_U-t>DgyiX5M{;7E6*ySlPLrMzHpZG{`m{a<u5)sHtx87v)*3q*Sh(C^KBNR9j_?XR'
    'S|Wxl@^<k_GU0jW{(+*oze7xR9%Ayn*@}u{hu4T1Qh^*s192xm%ul7nqXGXJV#?Zi-4!M4GDyG`U*5X^){%q`o|>QmaBGfCZ*GwF'
    'bzFn>fWqLeBDZZb&bo(-LZ^d~NvC_?NCep5Y;lX!We_zV%JOE{5STJ6a8W-5$hJ3^jQxYsxBjYCp1R`bx#B9cVkc5Q&hZ3WwB~In'
    'B1{r$#dG@RMFWZQg(6m99=?Ke5QNCUYzbk9c5$uB%5#vvtPj`i@mCTXftcs&b@j|a;FD2(vsS!dKq7jA4;=_Y%bx<{2;bl5f}{Z0'
    'tHTm&)0VW6j5+nn#PE3$J3*98c(f7(CSC@d02<J0WC}e?e3Sp~G$Mba??<VJRu81e@>QzUH<!TKmSEZQ%*x90?rv6Gp7K?WhfQR~'
    '!1;emC;oU->@#njeG;etNwUO5$EMgibyw2fGe(@R%}k>&H{kcy{jxQl{%0%&Y>{XY!oHaoz}s@Yq)SQ<JX9TbfdqMocfuQkDZL%@'
    'vL&;GI9!kDL~k=UTxLxc7qy3&?yrkQ<*n~9io1X&$o0z0>TLU|a!96EvsfO%ib?w~o2;bud4+3f&~wRADWenp&`5tVMxJb(rlIN>'
    ')pN~pZ|Jaz+btMS&jg+NZAPbP7XOlRgAg%j|Iiy8VME1rp_#)feax_1YIHUcUj<*2I*?3VItB;U^pe>qr}|J&IFeVFhzCT&<zqiN'
    '$x&y996ZpBG*|oW7F|ZVPFg5A=p~`%ht2LjHneT-!`8DrghP|n;G)b|+pj2yT4pFrNIl_xeDaE)6`r`tERSq0DLw9nXCR*j`dRAm'
    '<yo>$k*NtX*)*NQ3u~WyWm+(_=$=`>1R(Q%BU$a+o>Ut`mT(ZkA40qEHk(L$iY)J3-W9MzTQYZB;Swyyh``|vINq}!YI;+u;hYdJ'
    '|9^A0Z2UIErqp2NKAc9B=p<lE9e}yuOcXpRNSe_gewE|(ube2G=JTByC9<oRqP7M~t$XANZO1WTJgzpzw(s0qegBTaR2`tLVnrRd'
    '7;GkofwVz(mzgaIo<t*~?b!(B2q06TNKGhJ-O2MkSm+r};D+8pyk2CaN11nzO2d&)&xdM6kt;Vq7#*nrI4Bk;=BlRq%LHM4j<6l8'
    'mS{sK;%Irl`QU#R43y<|UK&NMiu%SQ#~q}$IcX?tP>!o`co~`I=M|jfe6gFJdRCE9qkaxVsG{t<M?ZQws@cYzE2m#*Yb{L#7y*rm'
    '2*Iqus*n?=?@&TAR%;{k(eR6BAVZ9TaM>4a)F;9JbstNOQ&c)ZsSV5M7$KuyL`v=+)CddF@Ocdpdc$Fz-fQ~|K3F2dGAE+)$YR0g'
    'xlo4vR`&-5Uc6X<3>K21+({o0ca;xPwa-S9ehLDBz|ucqu4#8r1!Gwj2qHwCdO3Kvk=|Z}Xpx2mO=$E$y{_ihqy>i`To`RFf^adx'
    'S26J(wqI)dE2%Nfpt5IvNMbyHFuphRsy{Fa3SWu--KM2Lv+$=@{b#1IJ!@g{Mv`b*EIDrFb-Z_IgB&dmo2X}|7z=fX8+6S*N$Qpz'
    'aVG7{7xnWNiYPl8m=$jdQO=jq>u74F1Xw6U-RxcBDPMY0pTi9`>Sh7SvNxZ`Nie}+QsxF^;hD{Xy*Qb}Zv}o9D;e>1GMrQ0D&UK7'
    'GlN+yI1&80A@5eV=i=~t;+Uv8`>|>}_$Tw5=L8=Gl#H~6faC*frpWN{{vFOtOKTg1q2#)LvvXEhp&4rU76*t7a&mqt)be-pSW$d4'
    '12zR4G4E@Tl8IsCG&vs9VYTliPpLVtOO7X%cs8HNOB6vv=W>Q>F>P-ezU9($rIm8q`o)ty5j1RC(3NPdoe6rcAC#lRZoZ0^vEAnJ'
    'q2|8c<|zAG-~CTa?N+#!VOX|XYO}DwfM7R?Df2<vaUiFEA6IY)dz?=0XGvk`E`2~i!i?en-|)$IUYeQktm(9fYoz;f7xP~XMQ4x_'
    'cOlX5Y!6_|$^A1}DvM|K@Ua3Ix;R{j7Z*ywsbibm4Baqib3^v__0)3IQ<itq!dVD1l0KeqN_!z-gu~#lW@&8fTfu&#?_M+3@~Rep'
    '`Eaz@;yFdo6{N16j^$RR3LACb=%B#El*l4YVO|Q1jRn0Jm8fS#vJY0USAs@98pzAP2EF*4vccR+PQ?M#v;)c*+SVsHN{i<nv*wbn'
    'mv6h^mm~k2Z}LPnKt%Z9Q&qv59+s|_lIUVh>$-E2_a9X1x4Mh9TvTz~r_aoUVEro&10s)nJv{(NXrT8@{3{~V&}1y+-tzv0JiZ59'
    'o#tF=84`6qz+f71;zA8$l<MIc12);&tDZfa#1hDr`v}B;1S{M;B5HN%$1=q9zr;3tA{*kS%07Osi~RmAMo!ERRSfagfNDvTFBJjA'
    '0-(%KG3G!b|C&x^4g8Eb8ad?ue_BWP5+@FofYulxWI?R%ga0@ebK<GeeSq0oHZZds$D^&ULyr%!1+Sd&GlL5W(>}lT;Ga(*_tcs2'
    'J!3liQ#WdNbn(tC6n^+zh2^x4xwW5s5_%Q5;Wg_3vtg{WPRFxdU4__QOGq35YPEs9UxCfCs>9~)AXj38l6up)?GLquU&-mEX{`{v'
    'g1Z=+VVEy`NmzyBU%y#yBRi|VKHLG-M_kjRCP;?z*^L<^axHsV4%ag6IkBrthSh^|N!0h3i(+tPj^WUaB~)I)v=y`i9=O%){H4XV'
    'yZdLwV8}^2FSE;EksaNC;2b__Um!^}D4&qu3!R~ZvFnec1$?3@Ak`Y6Zpnveq4L5~3nvcS7Ty(0-8hQqNxlq=A0KI8Ws?scfBo}r'
    'CxP)Bs@Nq>v61Aka;;;t-G@D<b?wyQewRpuIEq3RnU1RqV$%H2n`@3OyG4npv1O1LM9|m@egdZ#x}ERgpqW#j>aF~OV$>@fX(TU<'
    'y?d8*A{q2RZP^~6%zSVIi7q0E{;5(~KXx=ZDNyYZfpFLNt3@VA{Ez@57K&|+Q7Y1URfa(pLbo2R4m!iq8wJsHYgD3d@$|H-{N=@k'
    'cq#`iD<}v~6Jqx0&AnQ9=SrGZxa)N^_q?0I%R)v!mRiYhBm57>VK=%yAS9jB!BIi|r_z0o9$(-lJiewW;&>+Bu-;A`#KaZblov_Y'
    'Gu;pELXlW!&DZirz+=OI=1rp$#@l&&or$*+?I+y%s9cnG)o(}@lLVHa1}|4I*3G*?vHLhlP)FXQ$mBu1`StO|5!5VW565IPY5~RQ'
    '<IDrYz+KE>9hVn!SE;sd0RBO5fw__=*N;JWkm1Fu&b>h-13aFg3%#(~c;ft3W9+ivb@O*564U~Z`r{Pg8NQY<t+qJ-fU4+NX8d&9'
    'TzpuOSDF^7zN;BI5>p!~VpB2GK4xQHphK17zljA`2Yfdg|K#eFWxrxEq+-t)=S!GguXa1GENA;aK)XdJB#^B3F<hBek@ng?V!q5&'
    'IzEV#^5GD2XBabG_$#*TFXw(~s6+pW$>)-+9JiNzioa%5AC@`}GyMPukk<jWEqgf^bjM$I@`B0q;DpJpwQ+@tKR42%#^~FEa(+uO'
    '#6c1it0qn-3NP`M=6n!3_SK);k41jH_$OLX62tMnKv+YPo6d+Bdm0Scy{X`5c=sy9Kz-m`nDcSJoCKMt&cg6h`J}x;GVwMbY*Me^'
    'AAa^0&NU+-xt5(y&?NHCNIP}_eP@r8ZFu~^6>sUmLCW52pClmW8UaJV87_167!Evbb_WO#?~Ww)UvxRpuE3!~xbQ%vv3H*!(kYJ9'
    '|2aog=87vbiGW|BKVw4gAtF`LYbLaB=iVqzY)4j`)88z7>47BZ9Uo%OJ)E|`{xK~e@kjAfV}%l`Rttjztmd&6aeaLf1ADnQ-%JL<'
    '9BadjRqosJ3_kBg-|W>i<!k&qhPJl;(sQUUBvx2fyh}(lz0FNF>wz|0YC2cgZPaxk+<?0c%X<y4U|sk_2Y_6)%aDTKQ)?OM&vt6<'
    'cF_BiaerJk8|F)~`@%5ChjbuaoX4<IIO=Lpp}*@|*K2ajDaB02D)CmIPEqEqlL@eY-wiIKc1D-FiWN04(^%}XQb_ZeHts#|HHr0p'
    'rOO3a3}6*2`ZeR9@%k<XXA49={6;HwR6Av`wWN9FZIxzoyNXZ7b6S1h5P7EwGIq0w{r>+<O9qaXY~B5$s@s6&0Z50Sl4q%N%3NZx'
    '_&1147fbMPX*#E{qi?+<q$$o4vw3RoQNJOa<#)c8aKFA$0O3Hgh)EiH2MkDjExEE6B;|)IN&3J;6XoWuaHBT2)eLj0B4c)%5iyJ|'
    'vCRuNC!H1JhHx-_=o|VycF$U5B&Of|NnuaUIY5&?zXAuRAMY)C#<S<9p-9S?goMm&rY9H@<D~8Tn$rvd1zz`ORr`7Z0*L6asw}*A'
    'D1C*J%ZE_~n6qH)Xhi9@hGDi478MlD>b5h6UUqL#*Y`*gyhDj#cz&~eS>S2(o7D2@Imv_zWstPT6ELD-vSSPyJFXHn4%<-!t3t<#'
    '$dST31S{~64|d<@gnB+~haug)EJcW~D<S0s7S3I>IFv!^bj*+N9Dgo4IlVw}hFy80%&;4mx&!ZSx^?b3AW_!`&15+~(fJ<h`5|A('
    '(nGWiBl!kaNbb6NZd<YPT8Bl3E$`)N0^-p!`kSF?oJ#MJsClvT)du`xz5C<DI^3^;?w0QU3%k*5Dp&o<f1VezI0Y$sl*%#=!S_l$'
    'g?~w39P4ZvT~_X)**jRqW0_4%dD&kw9M2j1X18|qt}5sHpWga@PTp{dM0-pDp%u491U;cuUE$G#UB=C`@}5^jwmc8|SvPJkTxnJP'
    'VXAJ9{Jh4}jOIYT{M!t)O;Rz9Poo{Qts8g5_9XMNf)i=444GB`+dVW#adWf8VZ6Sy*s4a?p~%zeud%Xs^}{2RnaeSMM7kSom6|M4'
    '*b8I^!eA}DF|8qAwTiMcS_m|B);R%sukWM^0bnX+1i7HNlsn|KtO<fp#+o}Xdf3*Q_|r0GMi<VlnCKU5S>DMLq-F~!w(vRKC%Hpz'
    '4bShTsY5Cx9kti67|y-E+toJi^nIw_89R#m5P@0yn5e+iz!}f)2S39S#?xrOm5czRJM2cTo4487Vwt}{tX{?Gyc##4GZb3>I@USB'
    '@jEPB=-)<s^fu)&UvI&n6e6Qm-w{xEm@)^py$Cevncwq_INY|HQPlf@UULoxp5Q9y#7WqD0d)M!PNLB3%t9$sCdZ#mW#Zyl&oCo2'
    'nsX|i(!&Bz!mnDoWRNLJgm0tlr14<H9Qphn0%Bwzh6bA!&JEhJWp^WY{B!wOcw|*)AX5VTE>F=ZAjeUO$%)Ik(t}S@1SG8s?lh2v'
    'dP@*6k2HBWex6NoV&NkwDvW4Q&C_)(#!}tgh5JHKUeJ~VD65skHi;0=uu{%O>UcCX7BY$BdEA;UdE^tE<xCCYq~W}&%a+;WmPkwi'
    'm}WCzuWHshv%$qJm3`Oah^qY55TQyLDO=i}sfwD-7;K7ed^)Fh`bGx?2*Udu01}nNqBI_dWZ$4z<RARJfNg=BAfy}Q@oh=qkiVd_'
    'Ou?e!mm31<d(rmO#kW5u`-b2RLmW!c)%wn8Pt%m3r~8J<RE>}@K^Q%!42yE8uhmB*hmQN~To3a0g2yD}r)DMyYx`__;Pw7Iv0qNh'
    'oE2;>&CON~+dcipAL(Z-lo1e&NC5gL85BLe=c@~BZOWsSH^EL?&qz1ek++oNwY%KL>k4w)v;?rfMJKP?go)?f#5xQES5S<=Ooxnq'
    'XPKaAHUXi}`bhH6D6cbW7LITEVQs4sNRsDbDBLO;FWIBh-p#alZAH3U4I%d0NeS~T3!y$}4MNwk=D6WYV#Ac#%}LuJf#>c6<Uvi^'
    'Y2*DE*jSkSOT`m`5Z4}0->SL-ufny@7=+o1j-~O7#;_f5r`LAp4@_0&P6;>zY?|$wp@$+!886nd%xlf+^HFwmi<fFO_p*LAP93{D'
    'HRM{(xji%q7W(uyL)+#|_9@_P^q)m%7c#J1U@%TC#C*eWMkdk@F1{|YJ_#tV{^q;8nr4LW?;h_t?2ZSH@E&6P8OQv?F*;w^P*mC{'
    'gf9*tXK}KCi{7VW@2zb92H5==syd>(y#Z7{mruuabpTUAtcodONBRoSe6#cMxTrt)ZHI?R1VPKJFjO&0)~ps3Cq=5`ypRw0SnQFZ'
    '+4`KB#cJH}snU*j3!^BLY(|WkS{eoTF3-SmnlFwe=UWV%<_wFr@^U2`2{lB>LG6Z&zoUp~>#PUx|Icyk5G|wAOi&Xd-BKg63X6)i'
    '+^Y9PNvjRnQgne__?~Y^T*D}gDg$w#Ec#5ws$i43-3hY<JM?}vVs!AFpm-A+F~HvDQUX@0IC^YlT!sUj5u+Fi09s?8kvQ^BM|7id'
    '<0@%CGj+=Gqhhjy>HPb++<x*1)((j1Jr3_)7QmLSSt`wF=@R1e(?$0E<$8<+s{Rt1+DM>*D)&lQk}qVIq6h5f2yD^GkW!HqvdCFg'
    'Y}|}iOT6O3oQo)yPd0Ewrf45qC%zgPlrp%jylL<hFx5JBy=#@nM>za{za99yU}4;i9DNgHjivZkYlR=wB@b6Hn;4nuX#k=^8s-Ln'
    'Yz%KYKcB2dCbKWfQgy(@T_wZAnqEt(`>SV>D6R4>`ZS(fn}aiWR5pXJ^%Ry$#5K`&9gBH$*@jU`s{98hZ_mgXqDXLsUJMhe9AbJY'
    '7cYyST~UR4A|~eit2Y#9_??%Onnj^uoz1w3fr}=F4(FF#1Hc7UJ};p!3yuTxD%OE%@~{wrG;^@6yzHo!ffn%-fUG*03HkU3B6LJw'
    '-iI6sCW=dYarXXmzS3~~-Pmrc8Jbw~yyHmxh9<A7<9zmx$>3GB7ixYdO8G^E6k2U75a`aeYbG73K5c=88mZ6z)JUrk;p{m);Q)w?'
    'w;kzJt!bP5MInAXDp<LJ31HiTHI4r_4~p*y;j+IWzF$+7M0+M=L4T=06;tX4$xP8?9v8=TEzkFMX`Phr*4TUxx(Ztj;;<-84h%vg'
    'hY`%h26@HK3;ftUw{(J3P-Rz9ntnH_$&5qr3qjTqh!z9*>QVfWAX7yIauY2bE5}E~%c;&VJ=Lf+%{-2$wDHjA65;cJ`Zb?VJTH1_'
    'W?J$r!L9s^cp&^`-58R}XGjWOUaH$}-SRcJ!VQxk`Uh9KR~k^6!L0Sm0@ZBcx%n`>wd^<!!Pk-k+>r+5%Fu{i^k#yP{U3t6^rVS`'
    's=zI%`}S`<@KAY!72UM@Z3N+yjcMW^`3I2Go%IbMNm;odph#dZPxwsCV%#2N;81;8<5?A^aY=eQn?L||xkNdv{RP!j@|IjZ&E3rR'
    'Ht_)}&lzRdX=u9NUN`V=r0X7VAgBmC<>LfK{$t^N<J$8{!?<o-f|bB}7G#;xx}qXV%&a!#fU!skZcTth6bUCVadi_PI+m?odF3lc'
    '76pmU<jWHVQ9IK<_mSH{&WuFtMp(Qy30?0p`8hf(26bp!-E?x3w)_;>+Hud5j?eoq6_j)bm9j7}tWfWozL0>6Go0zbiNo@w&tI+W'
    '(=w8ql-_~oO8nzkSFs0@lIa*bkd89d;n-au^z`smQ)i7GoPp9u=bv=W$x{gh+b%wp_rVF9+|C+1JQ+9aV!Q#3=*0P)xskr=Z#0Hj'
    'J!TohY|k^2MX0P^4fa-*#bksGqJ5=ZX_Oq9`g@I(=g=G!Pexh|C^4FtA3{LlY3HRss&=n9D%3fzB*FwQO+a~*ikH{=t!~q&_SK_w'
    '$X@SCedjClCWwc&HJlFIkc5C*%ldDMYO)>UPz;KvQy_3N5Iv$9L9TOpJJ63f6l)Nd5>GG(AJg(RbM^~$b1s(jlHBM8sdrh5Gvz1|'
    'bCI#cT^kb_#wkSaVer@Lh{_QaaiE*kVaDo_-$E%2#oE`yYYgP;M4JRd4o60CTo@Vab^6pDIfQJOKWafX-7Ts=3rSPRI<nOi)gE-@'
    'ZD9T21g=x!D%o<#jX76yu>}-~ol&nTkH$y$b8p6qb{>%vk=D>H=j$O0A_u$j2bild9M=Z5k*XJMC(0dVjBJ{$s86f7ztssWgTvv>'
    'n>hW<;p`G~7bO0dlU9bLsYs;g=yj+_*}fEMl%KxV#gFQ+6u~UXF%>k^xXSZ>3=>y;SLdyl#ANQmzI3u}m8M$P7yExtwgwMZXjjzQ'
    '3?oHFoh-DPFpp1Z0CL_kte*Pc6ynqLr(=A9h@D5rM98kk(AV9=pSL4pB2JmcG}XN!W##iyK$DS!nzy$b8R0KNL?Y>)Iku5eM}4=('
    'YPLbW{nSXXa|!~uvkKCtZU4=hj~&kOtb}oU{bJsRpFs$%mo55`?V@;I$|d`FbLT`zeu%E<!4rXj%a7q7;mFfbTQ4A^=_z=bh4)FN'
    ')~G_jbJKCKe(<C_-lD*MqeBdoVo9X6ju<XQw757<(bZS;yu7%XDIvqmhpj20fC@Gsu>c9%q{ZFa&-zlm;Ym{IW&WX2Rag<BCS;mb'
    '(`10In+N8noiY*IaQG^rJo)8iKoL*oNWPO+PO3S!i5yG(79UW`_mj@?r$04d*~P}TnK>!+6&%nuK0X#%zJErYeqjv6X=JK-^YnR;'
    'UDVlZo~O*$WSC2WzRJZ@rJv!JjyPuvQpr%y-951N?`bOoByD)YS6X;#ao%FTt}f-u6Wr&z!wu=yH1j5<EILATWJql;f|?YBJsWH&'
    'J18_ka_nR=Hs?w8LECroc%Gppie6c+H6*dweWmC@6sg?z2arY+Y3P|jo7ufGbB{ZG*v!@!Qk(GQEtqpGus&>Q8>ArbVREL_1AS0o'
    '6{t{gzCx4Y37JBQzvIPB>ZN6IKSTX1QHCKs#Mqd7eBa=pYZ}gue)2LA8tU;=wNd@#CW@DpXGB_h%H&Bbgm*RKF-GCA)w#`QPkarA'
    'G_<}8lu;DHX3*cHbWFbUyixIEEtKcg9lEG0o-tq#?6@8x9sg7>SJGz2>ZNwK%q34$<{}4(gbgWJ@TJYI`5_03FK_gAvvzaUN|2pX'
    'QwI%Q{$i5d_lb6frMnOxp)$QfcC3HcrbX3e^p#avYdPLsm6aXUq||IPE1>ovl|{4-r~nJ5c=+JCB{%`NL!X?@xZ|*%#M=e68ZL5t'
    '>T+>Lz7S1}i!U18mgfZ@uAzO87}^JQIiG3Fcd1lW1CvszIDM+4DAKoSzqkS=7(3c<b&3o^l@M;@wkpsYzhqKu<~?euMpl@pNfPP~'
    '9N16ZpZ-#f<%<n}q<WOIgYS&`kF*FNFY04_kpEuGoU@E;QC>UQ9N6QO4jhJH-y{Rw3Zewpm1*sJc%C!0a}{#pB_*pd%3*L{plTA;'
    '3bW1Y+(9{!8+i%*r6LNTwlg#0GTbu-(>42Z;pW!H?ICeh8tGIqiRaY@gvKD+q%qe!S0<vF+xu8w(O8){W?4pN^ynT>b9bSGS|=W;'
    'Br~sE#yNL6;m;<+9e(kLQnCL)wGBfb6l_=x-P|)i(TqGsg0g%4-(D-;B3&cOl1VMpwknjO>${n9Yy=7tva5uZ{HtUTEv~F1=%f?E'
    'GVF4ajbO}u+8N^Gjz#Z03%U-x90Mhjg~x=79<QF4{$I0ehr{H<{#x<kzEVc?3$QNX0Nc7HARmR#4t^NK_?@#$0>^amu6`4FK>NPX'
    'SbGXf(VI^2^TI~Ld2KwpB7H7`<>(Qz^z#gTF!&pJR14kVRpZ4=VVw(U#vnFX28vj%%Ze|g9xNlnc{nbH2oV;Xz?ei$1sl6P?&h7o'
    'ACJ@qzh8RlBD4P`*dh&k=7^C?1ZP<oId<*s@(X3btAY(vGIVtLWO|-y(y2)@eyMy0yuLK%@`q1Qz}+;F#Qf3++itB>w92a>8zf#j'
    'j!nby+tL7_DZGs@G+kQL=b^^aZS!PNl#TiS6`F$an%YOhHeOpabMQhldJ5C?q83>Z>jSn&tdfS$+@m3ZF%SUm(R5k!5S=;5*-a!Q'
    'zQ@3XSpYADS0^DQa0_8`Kn>BTh`S#i^n42B+giU8Hm!aD+^f%Ti6ZJ~6rtt(;K2q@w2rBjwJXHZag#_2&IR`jrpLN%4Blh#B(dAL'
    'fnsqvxC}<)ShnZ?@mJkycAaAzo*_|x)RRTXUT!GCTwY*q1)2nEpRPfB;Hk=6Z?;*=LEWgBFn^3ZhB95X;ACP{FhaHA=5wEmD08(M'
    '4;2s-g5!jFkt{gUSRAJqZcTRWwmY-`0ZLdjVY|?JE4GP|r`o3`1PB*dQSXK6EHEbZ{OwOJ$91A%$;s|E^;i6%%~(a?12+CAF6WbS'
    'G)f-zPzFtIs4wk%d8&bK(qBbTNS=?mbDA1&X{oaqmD!lxi#T0s(bAw$!0t(UcwK5Y)dC)$X~B}W8=i`gb@O|g7?9kQoSzlb^O=ML'
    'SxhyJ5GFkvh11hGA*ynK(jX2z-8wd%DLT`J97Cre^m^lZ(a-o0BzeaE|3TOGyuf*XBXW{3YDj~EJW_NtHvQPWK%Bm_Q%vXKG5K&i'
    'NlYEFT8*wer3LomP5n1Ta2<F=LNERvh0yjG=~`fDA~z5pXe1s{+m(4}HVec+OAH5md}l10{;Phyuu{)FavLM~^D1U0$7qtujq<$&'
    'pohjhBDyUFy>>y@olt9pyCKUmNKN-&=K=QF&Y>pt&&OUG5OdOAiG%Qm@L1<bl3@)!l|6u|pH(~O<RY8>Dd-r@d1w&|v&G|eF-II{'
    'qx;G~Xsf}3DWFP~C&39}Z&>^(OIK2LE;l*PbNC;;G5K9p)9Py>gDAOdNaEiK8(P~0Z4IQ!eSp`-EK=(<xDm2)P2fg;b)_YcM@~^!'
    'vZ#3z)0gXj;nb3D4bzq8BBpTrjsXE#34Ls%<Prqxek9K<dx5(wm=Qhn@D^(xM8T$HKw;J%s|SQ<U=-k`bdHEd6YdbC)iT2=lvPux'
    'A~gS;eUQ!ntOCeO*@w9^A4P!z=5(Bm-#z)aWxRIdCtD>*DAr3X*f_WDnzQ&89=C>*HenW+<huVu?#9PQFbUu;=e8t6NeQo_Tjh>T'
    'aZ9wH%-{ToRwrXzU(H*0>7CLYmj)0!UF0TlAPbWt4KoyK)%e!M6(3(fdG1QubrPk+bU<mNSZ-}gZv_%+AE16EstUv{i_^>dL(eqv'
    'wFON^me!|asjdj#Xo#w?@We$NN+$N0v|e4@y`6?3o<pv^F~6W$uc|!zTNfST6!)7|b`#fn*Z4(G7nnet0N9ZG0Pw#-s^_iJ<7nK~'
    'y@f-f0zJT8E~a{Iy+o=lH2uW~xlE-0XHfqK7i8-ly%8Xd$)c|J;vnHK*jK_u{_E2c2LmG_sFB|`Ex63+8PFO$boX`V0?)9}yu~p6'
    'g`mDPXiu>5`SLGKKx4yhBAr4?sJ%0NmLp+fkOyLpa6C_3V$smzA0y990pHKEC>*_+;~TM7{{{5UW!otyq~(a%<&!?M-H)s{4NJXd'
    'rF+4<4tChW0kpkl%J(%3L(nF&jyRc<pAn{Mpc;@q2zk>{Lnw+pmM~o&e@y28IPi=n{#>QFC~a9hxWfru=vFnVT{Qv*ZJ+_AU(E?x'
    'EGHKFa!2W$i%I&&D!mK#%@o~8`qmdN-#|obq0Jq8NeDUj0T}E;;yYmYDYbt4DQtrBAO{dY1MeHk{99-b%8o$}ayGg?&Od1t8+Bt}'
    'lT49fhH7{3BjCTP@%imv|0l0kMv4bW;1*3tD-QKsKSO)zTchjtCL#*J;)9v{=JJ_Yx-_cUCDF9kpZ$bNLe=%_)*t4f;UQ0jneGIZ'
    'gWv&$q|@?e1qUa1a&XvlAkJ@>%+HEg_W4Sc2ff!NC4ELs&KGy=*6zK%UPZ#hv0j$Te=?-Td*!<457Fc%Ema^5&O+|J-EU~URu*o-'
    'ixtqhXyZNqr%Yq!{qc7!Jf&?>8S~Og5Rm)&Imz>%H*f=Dwwcg?Phy%&C5gwZ1CKd;p8mrU@8$C#GXP&JkGEWjG?+(3GFhB>22{Kf'
    'jW_u3fbYi!$0Q*e04YwUjyh7IYHAg%ihPFWdU5s3{cd3to+WE9Pips}58uU9vXypuE2Se+esK8b=bovp^+=-bvP4>GPM$Yqg{$Y&'
    'e)NoNmS>}NGi$`ngKJ94TN67|D-H_c4~0uDf?&6})To7kq}J?_koa8upcYfKhlk0#=`RWpPNtc6;uhhpOvx~?ia?RW<Yi_e{RT^Z'
    'H!d;HQr~9zKdfY;??;y!L^D)|U^yW*3apWPPAvoeyttMRP1inMdjEl~a)JmqRmYY-FFPOMXk~U_uOT{mL2(m;LC9{0WGdCima2so'
    '>52iktI18zM$8bxY%9h_%57;F+}nzS+p$v@<e`H<7dthV$?mP!pi`)JJm++&Lx}*CLYBpXtGI+TZSA3F*UX#b2nf{!Ap1nHHU~Se'
    ')7(R`d6bm<KL+ZJ;}&fvxMXEM&d_v&$Q8mXEB>?RJY~^&m)+PdlDjY$5ac(e13S&0H6J-)b_HNcR1XGwtMq0%)RWYMWdIYk47-!k'
    '$q~n)z--Qgk)g}hELpNyW&9HUuZ3ORpT=7qdM7iUf4?3UeLUN<FJT2vY{Tw7e*3p3c-xkvGcX-q?x}~?&%_sJ{N=#AnI^))Jpke<'
    'qT(~Ar^HK0{w^O6m_Z0)^-*m^GRtOC^-a9Qz+zj^vB%Z5A7?%5fY?l_vd=nx;N~`sB14-^ggVY+y@gB-V!=I0$(qHx33go{Gnt@W'
    '$Kjnc(dBy$go%A-7|kTqh(}~@J2ixMSKqiJX$<`d6P?BoP}<3I<J>X&jXp#llN>}7i?!x9+2Ayl_X1os14V6(#-ogDE--Sb(XBLq'
    '+eV1Xhy(fnH#!7;5@Y|d(C|0C#94FF1tixi9K0evo1j~_9u4(XHSn#+A(t*9pBg!oS}Hl7hoWc_FOj%y0=j{s3ZvvKVLf$WH5Vjt'
    '_!sY4lTXL?@LJOv2ckN-tF?Kp?kg4k^ZY^Y4&lDP#`FmcIfW^o{xhhiG8m~jJb=E1566flS$xc*ilk_i2-!ftV#Yr-uD5>7{%VKf'
    '0Xzl=^QQ_}TD77>Gqle(3%-ZIre@@u6=;rjvxFU8&V#b}K2;nW7h#d|zGb8dk*bcdKbgbCHq$#ZY@g4zPpcf3w)YEKSVTa$66Bcf'
    '%qML?fWC5zyi8wEkix>oZ}%k%!E6co6O_2C{LGPh5S`6#C4$dSqV$$^Hcaq~aOg1v*GIxmC_tk2PoW&AXkC9~?>(AS^IQxE#r|g0'
    'XiM!3t%V*LYT{zgX)>z;vCeK)+xZnm<Q)-ZQ1dTbHE=M{dgUh0&7k}!wqvp0G>hvJBj>2M!>h!SyHd1!M^i0Luw3OQ9S?~$Wla92'
    'e(;YV)H84HP$#p@lbE6o;bNe(d+W4dR{h&|TCkapo@wSM_nw*k{M+R#4M7~l_vk$13iz80esKr{4b7qmxyr@;lfh=oGxAbCPo;Pp'
    '`B;a6hAIgEnvzgpwBdqa#a?AWF7wyy?G5(5Xbz%(Z6<FUDZ!iv3_M4;vBPkC?eg_vm*|%SbZ=x0q-;a<0JiInF;#N{aZ=5U*zg;K'
    's?T1^vz!SsUtNXQbS`4AAlRCu{Deqsm|5a*foFyw5Wfy9M`eY7Ho!XehEttLMCraKD?kl#G<wVC-X&*%FP{~NmLc2aV`#lOCz-T2'
    'sCB;BC}K*mfvcd=B%K0$h5ryc-Cvil!X$hefjt5)(QTZh2FY6UDPo^I4Vhn4SWBvB1X7h5F~F{d1m{fdz_DGrK}bWv!PCsDe}TRo'
    '?M6ax=LzD9&O7i;0<MxgeK=rs((6A;GaoJ%Bvf|PJ$`eWoCX@E+tA1Fjj051^gP|x0HD=Z^F3a<*8^H^h28F2eQMg35P+swY;CKb'
    'fr~xcTvg~lvh+k%#q{$SM#S_e(#MxHu>hCs-O0tw_dd9QHp`4^PqdT9W&nJrespr({7Ugfp`=;^ixnTw<BJm8iBHoR%R*JEeW;2D'
    '_+Z6UnM5rILA=be)b(?<`!ijg$F$rncc>L~L`_&u$ysRZ_^{9yZvu(B&l$ss6kcAE8I(a6AZmMKXbT`Sh+e`IFIWUkzV>4NTJ5`t'
    '&yNOCPQNq&q~a6|&U;M%?J-x}BDc$$7CF~75T0`xmusP8m1`s`Xk9?|1hLHi)YTZjI{YE1ht;ucChy8jm6&3xIo#yz$s!Yg@D@6~'
    'yRTP|?bQ(VI-I_zzN{O79X}(iz0X12F1p@>!vDC@(<Pldh+8qCgeab&vhRQ9bG(~S*1v~^oFND}*#m>}q2LgaFmz_$?p6cMtiTdw'
    'YRnMz?uh(v4NYDx5?Da97%=CFf>ndHMhY;k+EPdCF4Z>=ITneg`B8Ts2-p$M?o;ChBG;f84uheiD@`CcM?N4EPojaSZuhsLWcl)='
    'hd;YW`|n@=7xIM5`j8~PH9Hfzgk3S=`^Urc{g$Q()Ir?UGq~IgR1nBPS%d3@Q~5E%o*&v>D&CEZ7?<zjl`5i_jcW0QC7_tA``)vg'
    '|FTASrEyYR$?+?O!3sP%Nf}IdhU&2dtk=A|MVJNB{(_T6G|J(|mt;BdU`&{TD!n-_0JM(3mm={coYh*%CY-e=<I2J+F{;-hNDxKY'
    'mWx=hBXE+LkDN%O?~Sc)Tlq@x8%{$&tx~O*HLVICXZ|+dK=QmB-2S!aH#Hks5L;{D)rn<FlCWK0AHo>~8W?sh9B9u+3l9v2;N>x3'
    'sD*53#6yi<p*M?Q1i(jNj}&`P=}2?{hriP9h$|QBlyGXf<{fuM9gHGjGnxdUzTb{_@Povzc!XYTK*$f6v%d=nn{#^RyaOQd095i%'
    'lVEvz!XyKD?yd77WS<hqt>1UAnne3u!i+9yf+|o;iO?@M{>S_@Dl?DksuGikV&|5~Jri~$YX$=Gt;#%`=`!CkSw~@_ddN#Os`oC$'
    '_@&2Ym-Wrr|4<crLD(-h5|LlkhP9A)T)$LoOwR|n&A*iqrB-2x&Jg6-l7RJ~3vp>~a{KJqjol+dG^=-j?o-i^-yx|Twz29?2ewxd'
    'zZSKNY@Y(k4|ewEhsB(Ie5`ykxsv8EZMH_ctDHl~ULw4(KtT8YUVWx0E++z|@*S4cvmjpmeTy-=EP@Ywu+@IhXQOB~bqT(o>t|WO'
    'S4-+=tlS~)pXKl!Jf!}|b6ShSim|aIJ@dhKg(NrK(`A8@tE!-j(u~+|R=bjMY-%EPE$v201FIxHV&Lw@7m?M#9G-t;|9MKlNsoWN'
    '7)IpldXSQWq`0Z&UY=gr-tT!-^)?as`Qpz|&N0;Vv8_rn=KWCA2t3$t+vNbZJkU)}s<I3PzmjXK!!d|=Y?&&S!c=T}R7>NPW;_`w'
    '8jo*#(Xhi2cPx~Z3xQtGEVqGjRvm=emJGm~6QP_T?_^ENVbm&p4rb4uf-BcxPi<X}yhC$OfqQAO+XnR!l0im8L(>iDkD(r1^3}}4'
    'oG=#om?yhCTi?ST+q}Pxbt(7tk@#0UA%MN-ea7_ym2fEiZrcZajM=&>qHL+*<-6smx`yV2XgzR0q@x^zZM+_A>eC0EfAG5u{|K5_'
    ')87at9T-WoE;O}YgGWaSs%w_uE(aJ5W(a%02oN6hseH6e@vZ(Vdo?oJh?G|aq%*KKBKU<H>w7gx5NBb7p`=y|_#_c>sYgxJ=6Tb?'
    'PDJ2Zu&1L5(k#*4zmN(7dVYOCKj2O_LE;C^Zf{6Xm*u^I-tw`PB6Q(#8(PZ-3WlFx4j-vi+ImHQaG<AFun5j_<${3aawx|vV6yW)'
    'v>u^PBONRFQBo_*&Zyl}Fx6OQ2E1}YGPe&jxT$@havY9A29|+@p97EUtJzs0+iuBM^tdMhOUsqAYrUB^h9*FbKry5~f-;4it1&c}'
    'P9}4##M{aE17x!5<{1Hj*WTde$EeM-4g!hW#{+}m$4G#~y-Ucj7UOL!1Hx`N4-$i^m597$(s@14KM}Ll1p;|QYR_pOTY~UKD~*OG'
    'p03;n<M1_8{Gr4<^;l}dLUKM6zi&BRcar^1Y{k(x3U<*$R(4$Or8;f2U9p;m6EttwzSz8$qny2X1dX+t5iuyMaR-5uI$QVrh@?Iv'
    'EOQ4|jW4fs)m7vhi1qz;X^|D`M#ec56#}QbXi1zM`+}vkQw<Iayl#J6pfzM6sxWmX@~S|j?CEWdEMEPghlXkcIFvu2&2I2!jA|P7'
    'jT+VUzCZmA%BjeXe_~)HpNQ2FCjpq*e)FwB;Ol|tnESsx<txw@Xu6jXyWY4fSk`9zvBO71dg(Ss8A-skO2vnknKW{3bE5c-;yoB@'
    'ul9#Ty(Erm#fy7@w1MTR1q;j9oEwK7=yV3U5JJPjK0<_O_GEu|*6WPU@y<>pcq|5NiE#`@Z53%QDsvZ`O*eQTRMHG5!6alDYEh-O'
    'DtiygOR!rsWuH1=Q>uZ_WQW=etlDf2gsP5)?TXIE=wao}+94aycwMt8jEX{(J2BE+9bPo8s@Rb^{CB_2S^zJlKrS?Mq|_G+EA(Xj'
    'J7=91;Jw{<c1Ht9@VWJ0@k+{d?+%~(2q0h90!x9se>llKX%~`>iEi^0Uz9{WSFERM5g@{UF>G&(M|EL9sJUVTJ?M*P&g?PmrqaQq'
    '_`f-_>N_S2&n>WgOM8VhWdY<U+!T(7pt3@E(28?ToVDID*K@r_V$}V7$%|$RB?Bz-zENWXF*7OI8xrcIHniXBT2SmINk$YyWf^7P'
    'uRl#2wpiy16C14>iZgoqL-LfU=l!3?YjRpDvXBk6-U~5-FE!TwmKBzSBhDq)PaCzLvb#`vo6ES)JHSkZZF`}w%0~=<KyzF*#tXFw'
    'FK~iar<?0n);+>s?H0)b0mx2xk=TmQs0NUY+EU5G|Kw3Z5iZ&Ac$De;LH3r9_*i;bO$Oas;w#rXrRgIHJDPqu#){PY(69vdoo(xq'
    '^*If3A*H0OqEsh@N>I~@tiu!1`c<mohMKNg*umaPSa);nTS|9<mDg_2<~Sx~II3#%C|7$Q>MeB1Klk7<ZrN0C(vPOB)qvO2Pqk-E'
    '{}rqaH{Qc&A5Zmza-#Ko9?=&_W<Jmq8*1Mi#6~EU4IbkCm!EL_BN4s#_VlnS(!vg}w)PU!AEBzeZvZ}+6g#}j8-8%aCT2}$AIBq`'
    'jN#Lv?@P;|uQTio9HAF~JLN>$DzzkD{wPMmNil`5SJZoKL}Yu20@OwPhj4a4ttOeGbqXqQbVtU>p@VNE!S!dn<hXQ1r4dey?6kr5'
    '{HYT&JC3WgG3=e&${8>#HM$DLU`$)nri?k`Q(Pe?A~Xqn8AQGM>Dr)$wQ(OZ;cpD0;LeB=!89`(!En^pEjD)&D59rOvoLlFx;ikD'
    'K|nTrE9}48r|&{&HG6OknfI}sMsLR$zCk*bmBQR@!u`3DUApr=jp21t;MmodzADo#VJS*|Fha7j(}PU%ZI^iVw^C10j3+zgZ592P'
    'I>;x#d7DF?lkJ-9SipNK{WV$~f{uF?Cw7Nci3>s>?0}EHUK_TlhE3H_mtfMCr2?eG?kO(AGT$ljX}gbVbPhGG3y*E^L4lOhfXFK-'
    'AtW3YAAETa!{RvfZm2PR@^q38GoZXvY7jFsj`5cuA;e*mw0P+QYAm`3gk&D3X#t^z1QdSjOiEh_6;(^8Q<l#MLYpGxy!EPhqJrG-'
    '0!FbE;+=KC`=(@dAw5q*xaH5lqEdy8n;vOnEa-!Z!T7N_1=X<K%ltXXM-;1C1Ct;iUO3DMtNVb1<4c>J({<`(Es{(_<%M|9F~HAn'
    'l=gZYEe(Qt@6j=Hl<y(*EwC3LS#%Yktl5};gU%wxFf5?{hAeEilr5Ov&q?!!bf)<d;tQ{NoJ#UDRr23*iN5Br*l^NBNnNbssn{X}'
    'fZH9EML7ueC$3$eTSCX}{P2Cmb@ES=U|+HR)wWq;U&a1+HsAp3O+GZAD<j_quDJ;RJ{^LDKXC_wyJu~EqHf8dqX9Ru)ZD)-bW93a'
    '+DW#TJ2j0Ga53;A-pFsP0}`{{G<px$gOqnBGRB&uiW~+8&vuP=X@$3#`(bs|4K*L!yZRW*zm=BLwP$lhZ?l*%1X5V9%om%LvglU0'
    'jZ(GqHv|o4zRR2E*bRwzT|oz7srC_n1roM2C3s^d>84*M6a#r{S^Ww(G8o4R(i_Hz4!4rBQaH0^{ar#_Xk}*_SQgS@^l_{n;Jl0W'
    'ffLFb{GC=%EQ$+BtM?i+i+ZvuN2-)4jMmg&<DOpFS$Tz8I#DEabJ4^^IOi2R@=Mp6RTg>{qaEhlPzdm&x3@q{tw7{8rhWwP16=AM'
    'j@5Pk=nnzI-%F~o9(zWH3Vh@Z)n7l=Vua*GdWU37V_drlyr}2NL6tKHh1e*)V(g0*Vo(F?J6Gbns(;5ne+!Y6i6Q<jA7v2vK#+AS'
    '=2fTqHNMsO69GS|gjGa4=HB<GDkHE`pi-?2z6eSZh?urxW4L)a_4SDaXdg4-<xL~*iR@{Vv}lXgl^=X&N->osl89E1Nq|m2<fbA;'
    '({44e_1BACt=XLClm$hmVFPGL(Uv1RVWk&l*7)u;ys-EgSSKs>55*iE7_2-Kcwk3-hRLxoxE9xnTm2QNq>fdidQ_8`TOAccec=dj'
    'cE1qN$2mgpd*ar&JpcG)Q>dAf1FGSaZzQ|c@AUJ??sn_4bG?qfk60uL)YOX~_7gLpgH(8rdR&#5|3e)xw3~EVCj9~LFTbVf;GA~v'
    'tCoy+UO9su^XGEk@>%OS6&1Qu@W60pN!uQ_Ru*>$O#u;Yc0lxyuul&YwpGy^{9Yo>c8V1XY_Kc>I06<Yw?9*}v`7Duq^n+c*u~Y2'
    'D$a^_CLM5&Ut~uD0M+*49?E+7FS9gG8m|}@97Q-OkDbp-)oGtcHkpZQdyDu+9a7vFEHV`9o=w!2Nqtan;Q1hgOf)aXVOC&4_p9)d'
    'qV)|ZoGrf|_V9dA3A#c%L@1?pNQrCL18?;bFFsJA>K8{pXfixz9Wugj^ujN|#o$5$Vpf@wMRzBG5+&C+S)vY1kE?@${rq$6qP}{g'
    'UUC6QttQ1|_8y)Z$=yI8S+#SGf2TMpE~FwkxUJcejt5MU5?n}mMFs}p#JXaagTIAWjNhug49M*l6$v49uA=5+ccu^~VXfjM4q@}S'
    'v4qi#|MEIxYLGica%XX^`(PGlUW@R8z^>EXvm1j%^swFlB^H>??>PmdW7OyjLcv6ZDfy@&y8mkxo?T84A6}j{VLT{2>nnLt>=SKA'
    'a{AV+aY;es2zmC&uxp(~4<D3~0K8--+hyD-;&9j^J7AY3mfAp53-5?!3u^6~DH$!o-b8w&{ug{Do)!f3C}Z6y392HFmN-jw=%+EE'
    'T<*`se;N7BIIIo|C*roX#(ING-D26ty?o=m-h%Y-`H({$4B-butm0zeFf<BxohcH8lY>M0d}Lq0vgIHaI}akrsIX*TL+fC?S|#rA'
    'f8q`9w+m<hRuqacj0`X45IjNIpY7Gz7_H02Y1Jp6d%x^&+O)knmjJ}QLJFAO(hQ;?c`C@u@8FlzcMC^LAue>Gkxs-e4o(b6(+dW3'
    'W~>kN`;^}7YVBf~i0flL`7Ao?Wfcg#Rp;02U@yIRNB}u+gO0TUx~(}dd+gUtC25E><ymYqEh>MQ)j+rZxwB*(_u=whBnKG8{*bHk'
    'K51R%yoF;D@%1&n_J<(4EyxU<Ax-}_if6U}8XqK0c0;)kzn<i1+)N%o5yGpY+*=u6vZk#hv^g@#KnF#zHtm1WJ@LGEL{Vzt-!l_}'
    '=N?~a2tphhS;?t4t#!o_$eDwfiLgQJLY;+v9V=HHwa?t<?9(?P1C$MUh;Oz?o6#h~v6_!)ab=Boso&}cLe4!QjWdHpI%q6FtC(qQ'
    'AoOXF+qLpNbou#9pLz87GpY1Rag>J_LO8I08jbn|e?@px{S|)*o!T6_7)@^$H*X~T>?HDbNNh5jmW~dRhA!;hPzW0QamOMe<Mg`Q'
    '$2*Pp0<JJGTIbaZWf*1h@3e<EeN9fB1L3!cRIKHS+!tVHvIxVO&;~q859ER<@x_co1?^Gw0q$~CM6E$cx?bG^gXY6@mn>V$N2Gcv'
    'pT9PWfFMB(dhI%v_gVrA$S|af|Dt`ugk-s5gB*n@`?t}JM2q(GxVbEteA(w2fm*Y!e_2QA_UG;3C6IH;jSTfJRR6inp5Yv|BBF>1'
    'nQT#s<#eZ7I&k0OcGB(8pV+}ZQaz|$Ds1W!rho?%J107PPZxAXX1>tM5fv)hLJt#RK1q!;f#qqR&+Cz?9_TXuXMPa4VNZA4ld&`y'
    'R<3vyh&tc8uMIV0a}$vzrZ`hGo0aP;QIHQE!}I!(yp9?r0<FGhzTW>WB=(z8>DNuKpxW7ft^+zT$2@^p1)aW&9s^3yDVz+`DTLT&'
    'b-qXlXcehXBYaH1=PZL`$&!&zE`U}AaGO874O~m`7?<s|Vy>+f?e0$Nlf)~y6p>%v*63=7C>;}qy$d5Xq4Yr7Xh+jc92$>EjkD_H'
    'TZi1a5+bjPNQEs$E8-I^DI5^5p(LT*s!ANc6WDIQEnrgth1GT}sJcbB$Ht4hmC)h1UJJEI)Js#Aois1N;5dRHE{G{*jVVQgc%x)P'
    'RoUsd0t&?m@|_KYCqb{JQ7lPDA5_Vy&o@ed$K#2sFg440`b5OkZ3dLqALh)O%n>>Pm0+$|+~VBv3k+VGKP%uXNYC?H&<(59HJ3Ii'
    'zgj&H1l|y6o^CPi@rnFUCMF@(RpI_-4JcF<cg|Eh0*EGL`_w>KO7DM*1uodegy7?uY0aIAQ^bMN<M8<<ysWgSidN*1`qMg^;{-^4'
    'KbsIp_%Ii+%Gy77BmsGG`kO$G+fImRnAm`9sBuX?TBWf<3R*r}mT8+>2IZ%-`)<5!BokZ7+O{<h;WD(6VF_Z<rM(vLRp?(u-Sjj%'
    '3zTsgnS`rOE1GP(P~QY<40|shguG?sm<+%!M9fqky{+~;!r<;aHgN{_HK}p<iWJD1tT1|QJ_VvyfZ#?&Z+EKDNG>XO!M3A%_E4=8'
    '`nY;Ar-{$^r{r5#=GL~*u+Mih*;CmUmINxv#&i?`sZfxpP+<7k+hcudCV{zfu>i$q`5zm>**Li&0W%q&Gr-iz%_uoiOj1r=SI7|v'
    '`EbeYK*<Oc;lrJF4bENm(fy$hLme%icw?~l2G4a+?im*5L{JK$yOb}*kj^@9>f9oiIN4RLncJG13GVfY{07@vRnaMLHr&s`>4MX`'
    '&pHQkTjxY{0V6Q(yz)JOH3K#&_9G)ek%lM4@{U>~0m~Uy#Y@MdlfYWO7g8v_OT~ce1HC_xO5JCwFK|QQJr*H(D>6L@)Yus~!VOdQ'
    '^r%YnBD#F`T~RXc(o9WU5{zE-Cl^WD1<K&KUq6Kh6_^ECb{(3yG7%+sJMx&CfFu<y_$Sz4kM;B48%ESy)q&ld??zi-+gjv#S1874'
    ';}>E7n0}MU=i*i6wxWc*y4nAhoE&?so}szfLzW8pXY{d15fj091%IA~cMY8=%SG3y&KM&>ppeyHwP8h-nL%aY23nPqq}2jH@<=$#'
    '(@4$K(*mNM2`PJ3s;?E&otAte7>hE%7SRtyi}1r<R%dD09N~rngWOH^=ZKtF{YREwNlsKy3q>SeeW|%=dPf|9+IwQ?bzIbCSy-kE'
    'ceu=FEOdFAJ84@@6niQ6d}vmNqp#$<=~6q=zfV8jr!WM&ce4K3{~T5T@m94z=QjvckOk3<@DHFCYX@h5d3ioI`CSg*Uf(Ikpu;5<'
    '(*PP{;u5lc^a-jj5Tf@KsFCGoYh1q1qXyt48T3WSio!>*s?xh}q1>_Qn9I2P^S5=>yyBx5eZOet*<7Th&S~a<UD*DCtXF=0>8mM>'
    'm)!GS3Ck^R)YG{X4AyeW#`-zJNxN4sN2BSwvJnCH`Bg?r?H)nT5*9M|LphV51)Psu;Ef<@(?E(Ge%klGoizdEDxq}$B%utH_eM+G'
    '077fQVJTm)yrqB2?}JkZ`VI^nY4_GmE`qSlwI*_yRYj3y$909-m0i+O7mD51=Ugw4b+YbIrw7aMcL9tGBVw1`({b!I`MMX|XgEa#'
    'L-G#nqICQi(CETl5j#$wM;i%M(d{{AwjfA)?0k))7@j#H4)Q%c^;vF`Bukzy%=?==Fmp7c-E1{XhN6f<TEX%OVF#K*R}ll&`yaJm'
    '0}$Wa>xCP5hh!q%XN4r(T>AZGE-InXH4wlSO;){&N~G?(J#bfD%p}B?0`>h)mV)QW3hb#U80T74T}WD&Q?0IpovL3;YgDB!%zfmm'
    'ToDO9%1(y6>H8yX<s4Y=>9kBln^G;jg4myW9Y(5v3qu;>_5C--o7dHdfJbB$N<Fx!uOMKdLJ%;ASy2+S12^9Y7G<O3MF_rBmLGLR'
    'cq}e;9YtpFsgAMh47rS4&R&JeXRovc_%ia4gtDEF)Q5K9o@csf?4wj8Fu1IBY|tWcd$Olq-^~*^u#I!BlhBv(f-tR2ylp8O3}~lJ'
    'Wch)hLjHm`|A9^>f>jzE7d9nrR@S(jzE#jm0Ql>Gjh=6h)^Xq}4vSMm<r18u_+PhW1MI($xD7(+`Pp&w6}o>Of|VW!e^Ffmr{up#'
    'C|4+SB?qW}H7>vUJ|-9x+!c#%EZ7gD`31RKgB#8~YMHf(UJ<Y`exDXnrn;B5v=4vf(`1z@OSX}fpl@YN-uRVpAB;l`+0KFa)<l)l'
    '2fK}NRa0QRq7UzO$RjPTgBTwGGL4HoF;2rFTdK@dj}O#5)N=_O5U>`yUWce^jZOV}agnDt)u#dnXDTMNd?b+tZ&Co5n>Ky71t;ie'
    '9zGj_4;@T22=??QkNGO-LzEOkf$_2eEOm2P87@pCg7uMl6r^n+4mt2XkGb-sEak&N&?!2UdTDpHJ@L%Rq;(?AMA`@0k#gV?I0uud'
    'f_?kRu>zy3kkOR<+Pg@)@#T)PlmwdDS3bN^AlI({WQW65tRE?vL?NB5jkpii&tdrmq84Eh{hAvGmr4#Qn!z0mx5d-)(-sz8f|7is'
    ')C#WD(mt-CMIKB%?wVcuPu~ez){VDs#*$<QCl}yv_ZkCFZa~jfm8p$z{+i$aT3fw9zR3y`j~Lv6%4#w+!311WYtz@Fo@!FGbW8`f'
    '52(#wuKl&LfRs#yv{edUGta5@Kw*P_BW~fi(>86ZJV^}4Lj$s|&wLot4?Ayx_0hSw0ra^km60>qpY2{PiJg%+V#P$l_SDztx$Pky'
    '*}8yTM)9QN<GJIxQmK9I8NJuyB5#O}jjLbv!{^zD1_hlYo?|HxDwmH6*<M=5y3Lad3f?%eS1%jPdyqR-MyjCK9hWr$4ZB~(efl5Y'
    '`ov}IFYNG)Rx)cGlaxk0H)n1pA~GSbXMx4C)BMD688g#;cNHQ<GgW<owGDau6epL5L{d|3hadr0CvGjGMrnuN82}N<z%UPCi7$43'
    '>z7FrWYb1*<SYY3FpBos8`myZsr}070rf7)c&MJEss<A=H(>oR=!=H$@Ys8+XMgxX^FfS$M?)7~F-{M=ZYmG8q*SeegJ0b&%&HY5'
    'c`1lRmnymKj@NXfy?cz$n}?>+)TOtu?AaK-SBa2|Xh~VqTzGyL%<BgHN^11>2*P8Dc($fPmT2blN_9Li?6(!dm@3t!XY$GbReG+Z'
    '$d>@MyOM%5IFXN~w9pAo7t2qG7dp&+4}>zXLX{(a{4kmvK?KV9<t`7#+Jj>CH5Pmi)!C?faeyY%sB2Yi*=@xA->Ff1qblIqhC^C6'
    '3ckRNA@WLO72kWMe*O_)*c)n)Rgvj^7gbmcl^-x1cTAg_6mV>pec3SwdNdkqDze+hHVtL|r>>>!ZaSl5%F(-rE88q^^T6vnc32yo'
    '_`l)=i3hZq6UT-gz&W0b@u4^f5R~;eXYzx%z&!WNgAh7VL#~ArCI|G<P&a`&GPnVlNMx^!>&ZVlh_Wq_1-TAq%QOEM(9rLt^AD{f'
    'Os8+Ae`6Up2qmQ$g(E)g=})=fdCh2T_<FZ=2SK}>GlQvg7$OEg+$H2O7qCPX9F@6w6jJHJ0H;2=qFSFT)QBrpMRP2-Y=MySE4nn7'
    '3#>1LQx_X)R^l4O@_^GTYQ0KEsLdU|kTA6nXayX_@i5E@KX;Q1b@x`<lxL7I*m_E5P)un(pyz{Hh%|r;pS4-@tDR>Ke`8I5237J0'
    'T8j%m_NVAbUN2>-KU$Y9ZbfIY;Ld#yWOloz;lC5zm3Lh0t<_cIdGTc2*tV{d8LA-da9!Ksi-yjdtM`G8dMGDSP6@)EJKWB!GmifF'
    '!k+|Gvd=aZb{8kT1ZfMrx^cXB>=C$Mq%Xejt$XHXC5zmjm_p}=r#Q3vHS-Z3wH1T^5Fs8e%q6gK8+0?NqcxgM)t9A%F;4KzK*<e3'
    'lsD3M9Q(TY1jH!6@T?MR*)%?6$v|GI9og=&>7Umo8ifqf3dybG^}gP|rmir&5tf>rSlgWb=4UUQq!Qpat;xuCy~HK>(-cPMBoVI6'
    'S@z$~PE4r5bOuqT##DP{UR+<?Fmkr@eyPKa+3F_+m<ab`R7W%OfB)4e<kt2Sv<Ln-HUU^_B4hk@U)IzM{Q-QY)AljIMu#>rU=-$7'
    '5rb%L3l{@-Hxjcbjd1=BFg%V}^`}hGUY}#G6>{9cm)s(n^+}w$GWz+0XNfmKJV&C22#+psb1QXCc>iyObH1%%yxNY1ILTL)0is2I'
    'D4&wgB%Nqi*SS>d?2f07mXg8-MWu-RCYWJwyes%xWZvJ72*TOiJ`oN08{gOyX))yqn(ICNd<qIc77K6Cw;u(YoEWhC7+?)=%feo`'
    'U`hfLMl8%i=DtCZqbUSnEFs<0{E$3Yd5){vnsdWYzN~XD{-r#^BYp%L2|2oAd`ojKA6Df;26CHp3(heGHKxoX&do4|E_I<4?x9bn'
    '&f1PWJEQ;FLl<T5%u%xCljT5mc7J5^4-KJkwqYf%3<)T94}*gVH6c|xK`(RUpS=apaIR0Cv^lJb#u2D;y;o9CLYZ=&Z|^cF57}F`'
    'V?+jiOIfP7_qnYdy_y=eB=>1)Q^W8(18?IHIb5vSYx16_`yT;C%M)Gns?{yF$6p-?)wJk2aVf~ZeH5w087lyTI4`qi9qae$iliYs'
    'lj=gh4TB0B5eQ=RzD4<B)_eTwVl&$mqa4W6t!*9WzGwc5871N%&YmGR>o2ugt>h7M8w@*gMTMzp`7TDGo_R|{(wT&Kq516;#8JGt'
    '<(uWPezf%pqUNnH2-jpFkHjG)4d8E7oZ&%Mk~5SvLOxol=F7rw&L9%gq_<@8Y7_T;{kQr38W_9CgvKl>Q0A4tKaEY&LC8|?uwCy{'
    '-*sacXG63!Oon!Dq@*V8#3!qUK~ctm1lbD<y<v1SU4;I)qL*zkbHtSJa@gEqy2!Y3dkn22U6bnJMfjvXkYv1Ws&-Z;0B9U~sbg7)'
    '#%Z|Wl0fd90&KB3jXz({l|+JqnUmFHDt;jgVO{#t5&Xq9zh_4mNaj16fmICNvVb;Aj%3|iQ83WSR=u}ShiWN0JKT}$FKT%H6B}VL'
    '`4n9zLlY)0M>6slsomQzju`j1qAMwImDn1mQo>>}omR$Gm%1jWK8vun05%IvSSv+}B3?$EO0MZ251KlQATb1YtMU=2FE)NYgK(~v'
    '|4UhBmd6dAei?PU-L1-}#6Xy2kL<kN!@;vznvXmKD__nYR;&lv{7Dg~TzjKGIW__nt*?&y_B<#(_P8R~Z2lBi(_5B6M?}6?v2mM|'
    'k^Xa7c)^#|juldN5{{4Wm^R8wEXccYj1GFu<)9GgZ%3zQ(Fz$(eTIkWB}_cQ*m>&^_ZA_LsQ%2(SjhL*@aJn6J^05ypDk4NlHUv9'
    'Df?9E2M~kINJ%M)r-8o>siJ+XcHsXS12x6f*_4*!tyA%7F?sMwoePqIZnX<do*T{Q0^?w#vjBTD>$K|g?7vyxVhxFtPaYpn3oYj8'
    'YdDcq-33+m7yLEi1Tr$|pD*Stjd(%w{Ujl3!`mh@Inhtm>YWm_>b&p>6vC0xL~{!Hy?YtNALeH@g~}T?RfBP)C!)C!qal0tOuA4A'
    'Ho{jPNY-{9BRl7(tX&eY0LOGtV3Fx$c)X<(oE)zN>42#|X>`LPU4Z!`%_M7ACL6Ja58Q5*J3*ql(VJ#BGR<$BQ~*s})hHFk3INsB'
    'H{M!Bu=clw%?(9qaX+snRT_V8OIzCfX;8@86ac`_Yz_e2%CVO1re*|$gHF;y6$Wizh6Mv!r@wiTO@F|$qEF9v%B-z1&?YtPf#L`J'
    '(!ri)CE}WaYrV69Chyw!Z#PVqDL9M=RkshfKcH6ATxx0?NN1U`PxUGyz)zL>x-a;8q~%2}bLQ1Qegu25<<QbYki<!yw%8t5fXzyv'
    ')W8e#`!3SVbi$g`9_6@LXScPUjYwYf^JPC=K*I-P?0}U!fp$7yx9xqJVxR@_T7~DEU3RK$ftu{|MB`@Y-S>&8I;rX%(XTdYNZ~Mo'
    '-~HN!VKLNxBt}Y>PbbDS@ltoZ46}0RC8Yl;eQ0r3cX>hzBrM1tCpEi;0>jf;4np_s3_Nw-eF4$b4J%WEp|C&GeyWshmxt>@)0TCo'
    '#tB#0lz(KbR}lx^3}CMHt?>f5HDJAmfbDo@52A)JVK-_4V+AemVj)xe#Z@GM{BdoE@HR)XS!ch;3z*d=cQ4I09StS4co^q!f_mZ!'
    'QBFojoKIGO;@m*N6rI>SMP76qx1}OSArYxGBH&N&>t=A+jVm^b0jjlra^1fZpUl<kDR)(9ig9iU)cAiyDGfBRd7g5o64Xk0SMKja'
    'qOPC`olOI6g5bc#%w%al5}L&Y0Ordo0LHu9@;it?ivR!XlijVa3E>k*{dG0yj2jixf@TW;ho@tA%v8PM{bDdr6^uX-Nhn1+n_Xfy'
    'z5oKHmY*`oRj=T^#N5Jqo!Fi<m!W6<g2i)z=F+jz*tAk5NxXDYS0dpi&+(M5r-y6j#ow#gwzV#l-WM>Cl9PC~6di1?jr5+sB0HoY'
    '!L!gGOtD^B<Li0v$&gpvhSmi$mHhEX<;w06n3+TNb@2@im+6^zPj_{g)-?G9Ys11+%(_XM0fTHNQ<Y?KL7138$o6g3)~c2m`cOih'
    '(SI=~>xun^03FgL&P`ZMz><S{1X|4@S1i6uxx`>!!qPfkMx|_oUS(lp%`%9{<68qBCf85f%p!Zt`IsPP(ubUT5^C{^iExLCF_uVR'
    '5{=0>!k%AG^Rpn@MkaLQ?0t&vt*C|hcFz6a9Psk?et+LItLwwg?I<^V_rMHFy$-n0)Qj<%Jt$%?7Ejxe*zM_q1|QMlXxmKk&(R3y'
    'hCb+4K*09URU<gyh=R3j-w(QqDRP)wtm2L7Jb}@%3ALv7>8V+MNH=t8R`PorV?F@^&cxXAIqi^=P^)-sbu&(-aqY(56gH!A-nzOe'
    ';^Bhn_sDr2d<m~}Y5zy1{E=EGbC>?V`<@%%V7dd`=oh0ss3c=a9`Oqa@LDfDS4fWIfqH%HWYq7SA06hz4Hwc&IWb)65NPE9(#-v>'
    'GUmullDF1454^Zo71b#I!>$79%)Xbp9X`p(EI+f$fZ4+Z^m;Fm=~+K69gv-%#;<`dCkxhryQ@MUc^I>UW%R-)+W7@~v&-M3LIydo'
    'z*s7K-5!-NWBz@9Li68QO2|<L&fS)`T7%{c|As<W;$Ds_f%N09&HfAQ)C>W36URTce4?22w-FeJyBn2}308?4jKv(Da=3z_ex6We'
    '_!)EZAvhmUwROPl7r|PFn=_ZwXXx*=A^Zu}oTobIz)-!KU_+MtRK0Dzd)rS2Sy8O=;%e2CF9sa|pZm`4Ay`%<Vt&UksX(EiFwe{`'
    '@AybX6df6({AYp))I^zMcATm5Od!**N;;g$7Cw@>QN~!UR+yS<G2dgDQ>K5Lml-Gm*aSiOL(kCxzBa0}U&&^xjOlrb0+&sR$)~cD'
    'e{Hn|$i5JWtolHy%0W18VW`x8^|?A}lCd66($m^kO=}J--V|wI`sHM#M^pbjzuMF=N(J?Kx9DS;k78(cbBb`E09jfk=%MCqa4+A='
    'd(gJuRrn1yv+u}nF6F%2T*F4wNMOC3V0u^p!3dj#8jF}>PUAylY?B*yY}8$+DoY5`Zq|YWD4@hJ7s}B`wX0x2xK8_ktu2$Nm3p}5'
    'dax&zPK{wIARCvh^3_ESQ>#&DKuz2rswIpNIU9Fz0(+%gc)tywY@oO@8pc3K{v|(&!aNqX<2H){)gU98cBAdH<{L9&{D%=xD0{GV'
    '!fbrWJ2dDt)MV0G&$JOB7Zr9+gI2O<3RT+a`-aP&nfb!XCDWCBb^mGrKoZ9+j+DS3yIg?Lh(zUM`y@RL|L9J85XnHk{hS#6Tletw'
    'q24I^;2|-F*ZD*`>maj14Fe;*#y=wh-tWXy2GxOf({ZqbBlY{GNjjmcWcoYqg5Mr@q#3pG!eTjb2O?+|k0>~u>FRl`!5u?w+cP8<'
    'u3+C65rju256cOtJNd{-?8psA0x{7b%%bH|O85Am-k_;6NL$=YQG`rlswuIvVqbbIj5!O_<SPNrvR7NV*R$HT-shL*)<ZvLs+7te'
    'Bo?9|X?R&zApqNTC2RSV>5H%y=CSqfC2+|2rWu_RZ-2FXB7YT`66^H-V;1F6{P+R%a`tH)!C|T3=%vDawf(aO9m4Gd(^n;ciCV{j'
    'KMN!C;MYAOzu1LPCzv5HYAK1;CA`lIEEwR~W)&O}EBHvS_^Z)yT?Hj5zUr}1wIN}u5;%`{8o&AZXXAG#gSLsmcIu24NL}*$T4b4J'
    '&43IURJpmicETd!4mCC?-7(qDi48F`7HKU*<Q-~)90pJCRSCr~yz*6caBg{p%}v1<TkhdW$ArzMVrMjq)n(#PE+EMLV+)^Cg3j;z'
    '(lb4`|KVZL@;bbZ=tXopT=<_sLV1y22a$+?=(Btk0euakPvs#<tBSyk?p?AX0%R-)G!vdO{K@HGr%l%tADVnMif<8Tmn(p9Nc5VH'
    'peEn4JqvKlVQ%orl%NyXXuPvVOo<jQLZZ{NJ>6#<2PYglmj7?H+xmON*E=YYPkQ5KT+-^QyvihFH`!WH2)?S3>_l+FTYy$>7NDLh'
    't*EiRL}#YM^n6w~4zZwtpfoXr3fk*zo^pw<^-pW1YBiE8mJ5aEcm7SO>e=$eM14H9@kgCjqir@2RpT;HxdJu*Fyc+IHf0zikcZ2&'
    '%bY<U9=MzEO<V1b-9j5sBr`5~h_BO+@_KfX4l`-qQ@9{O$iavf-VmQqu)+N@vbPHs$U5=k|Hp-ic!uqtAw<h192rSx7j9mztX^d$'
    '>1%N%nmR38|Lp{j*;&1B94a*A_^AViZ?vR+V}WFKcgb4_(~Ra|z4?YX<{m)-xFx`{a~uEYz@R~}`AC2s0VXn;>tX9@7iSWHjoE^Q'
    'IXQV&ktl3}t(H!lS6}geG(2OJH$$dmR|Qjrurr@C62By}C<mHtLPkZwN6%9Crd36fuqYgSsyV4~?#R$#M629y7`s^%8Gv8g(0-Lg'
    '`O&6;(lmY-0{-whi#@>CS_K}tAC=K^>r^cBUxvsT7kQtPEFq6+V%eIrmRco}ty5aY*Ycx<4;TffA(j(q#v+X(#+IqR&=RPi{`#5U'
    'ME^@~{HVl?zpA{c657kNr>!rAi2s1>162_rA1v*%KkJ6-(O<#7|AS6>(U*h@p=Y*$xwWy2OBnXkQkLa?&C&Tzwad&^so&n4)Q3+*'
    'pIr~>Ns@_(#M0*5X#gAwbu~Db29ZFcLkPh8eg(Xa{-o1O4XX8VwA8#8v}J=SFzojb+oY%b!(Pb~d-0VRM!n87shLG7g>pHSAW_tV'
    'gz+;Jfl$^ztOC%WeyBS`ib2X}+NM08+IZtRKgSehh*C;VHAcRTxAr5#JeqWJhM7hq=VI~0tpzNpLN;g4`5N=zy_8fWP)+>bM?sh#'
    '6b`L;K{L*rz<8INOyHeW3<B_4#6f&O_08*3+QD_S6X<i|YL@e4{WrenE$VPe6?QHkeIAfVdRKmpUeLXqpgyVI+n7b50Nsklu5kj('
    'qmxr9XT(&?-i;&W5dtd5SF^IHEi^|;yy?nJ0z(X#&=KfiY`vV>9~$`H56gD)*Fdz0jDYF@MTEOqm0Qe@4}^c=Y@RNa5g(AR;CqKy'
    '3)b+kahPJNzzpdI{%67WHJFg^P6crEPDHlCd>(uGY7NYxCV=@E?Gb7ne{+(F?}bx-q@@lRc>YMCn=aDq%H4fgXSe!L*h1<RYqqFF'
    'EPe|4X%YI!r4~o=;OMHTp1zCVIc`-z@hHfDTrpq?qL7dsP@nu0P$1Z>c4pC*A;Ju!aQ=;6nW54f=zVx!LduYHv4@x8vt*Y2US8ZP'
    'i<gc_JE)1LfcyXEk^$q!&ro8v#0Vy@T(gj}1eyHC<|r%fX`W1=fBgB=KC`evAeWBgQ$bJKbCMaUR|Si#MNnKv)Rgj*v0^NSi5w-V'
    'G#b%BSnzE*k_&TdcHWT}fmQhU4#27(qGYupbj58{c!8`25V18nW2yFIr|-j-U1+TEl$^g}!LJ2!a#EXNab2PTsnx$iYFn<pX;O%&'
    ';%)lUwJCt>Ho`(**T*!p_Z6VIO0jNoItByE5%$G@UgB90@vuBk&^sNr0~#<_kGiNzVLk7j6IitsXQk1_&k@f^=eSumcQlEwzJkGG'
    'eORXvpqNbOfi-J1UnhO0z5k9zB+0xr@W`m$+dS91#iNWR#273U1xNkgoOk^G#!qhL3CB6hX=*-@s(}CYIgh|Tm)bTCIIn~PK6B&J'
    '0Q(n@RVH$#bL10rl)1tfVVmPW4m4=kLTox05cKs`aQ~TQRa6}fXc_4y`WGJQESo>(p-7^GeO40B^@wLw$|A}7EIKzGzJ8a+!7j6D'
    'i<DL_SpDUL6v_L#Li0Te`mEf=e^nj~*HB_4k#)dj;KM=N`ql~w9MP8z_SYKt5BtJ!7Q`dmuM=6@V25Y(GK)&RVn2`l?QP0YFi{2D'
    'dd<OiNKLY{si&<cictGQL{>Ynw@cpGA<yEVcc|3#VWW#~uXgo^Lz)HvCgASEH{NReJw%Oe*<WfSilJoHiYU+@%vIQURlXicuMg2^'
    'v|gtW;REiWYJRh$9of*BLh}pwo|PD&*8T-v74ogcPOIppR)YOTKYdbCM;L|l)IQqE0TUwfyU6|}mduIQ!KCNeq%*J#U0B@5p2F1S'
    '4DsWVN~mY16oh7|uNsJqpvT47#11y-K(chDSjS3z_d}J`YL{R`y$9UCQmfbb6xnw%e*!`-zuJ|;&rID~kiopCp)ubQoAaRP2)c|&'
    'Z4$=Fkodx)Pg^Qi%}9<(jMi6|3M_|VKvcFTP4$hX^1KxIq3q+pnzD>Q{QkP4LXxxx58}7wDM_SW9i3jDy?0L-Fl_-oky1_|l%ZLS'
    'C2Ks*sd!vusOMt7YOXr@MW<ZMy0G!@PF)(QG=*4p@dZ|!Ju%-mphx3c0wHFj{p9R=ZC_ZQW^#m=wXy{%6|r=lj#>b`i|tOoO-6OZ'
    'EA*pOq;BdGZvc2tz25{_^gC_Z0l1GkQD#^n#PUC(n5MVxzH4aYxOoiU8n%*TS7?CWho0dN4ln0M3Y=MkEsSi)6uJ-H^4HI3cd90W'
    '*q^~RMAi|HC?NAT4ESFU79OJiHyy+0fFMx==60s>6bU@GhUlT5X?$bKK{eyy1p0G(9E5_$v!a``qHXwRX8&?DhtV+lH4KXu7Kg5U'
    '_bhkq0IYqXcEcVL+;dNgN0V52ZW5Y&$X^oO6y}b*wBvA9-ruii(!#9g_hRLu`&RpUlQ%BW)Z))+UN_ewGwYxIQqo9NVr{x=z$Bg_'
    ')@>s;>A@WbR(AJpRAJkaqt34WPD3?ZyZL?(X8Yjkt-PROFY($$0eJL)A+?n+Bb+MtaQHIuOJ_T8IaHxsGl)yCVW>Cx|NrH;8Cg(Y'
    '+9yBx+&glq56k18IG?SmB$2K}rb0qKqzaFzgi=6Tzsorvpn-dS_1prf*-qox)I=jGTJl~ulR%1w(vtv_UoB)w%7wYgG`+d=t&gEP'
    'p?ab8@T95P5`Mf{Uj+)n7?=F1Lz&3d1>IZF2PUE=0D&v=5I0ylwU1gB$Q-Q7K&~vkJKkw#C;{q=R<~~#hDb^g#fM>HxJPP9mVo*9'
    '>xI{}dx^uvGDT23ELH+q@L$_?za`$=rD>d4S}`KBM;^0A+Qz<h^8JY61<Kb$oqAl3ThesZt<X}#LIm+(c)HUpVPrEC!Pxe5*Y`lB'
    '8Md}nz&*BKA@v|xO6h!I&_016h_!7Mtzwft%aAw>MZZI2^z^4x$ePcyCVdsvey-BWeA3i{&Fnbm1vKOAZWqMrP19-lK}mEb2#bzd'
    '&mQDx&M6lf32E|qyba)dfIK3{O(}{TJ2lHOlvES@nm~3-2@kQBF{d-dj@|%6prbI<a~%V7glBW8fp%WvAzwE-a<=Gl&-`AjQCeDC'
    '%5&@Xagr%oXJ60Xp%x)74%A|1i^I2!0mRm_cO!S7vkbI&dOli0y|rVCS6ywx2;^^caFytUhR?Qz9h&kTgdiI%^4SpiZhCWacGiHH'
    ')R}iurc5KQdt1E-$J#E<L-Z2L`0Ih+J4EtMJUo~fm1)2)K^%iJZSa_T)Yeg6b?{j%^hG!0Jfg!^5Nhm0+5FNcC+C+_&Kg8U)zPbd'
    'VCbu%yYroI4H^rNFZ+^gQFnuap=m5zkWG*irdu^gecP|@*ubQb!M;kUJJ!Ca!_o_g_DzuV^0)@8=>jRUofSb+vdzHxvoMK!{Q7g^'
    'f9Md;XxZn?NDQvw4TAV8B;oM@tsW|Y1XK>zdM=XTIgc|d;5f-+sOf==92XF7@{H2|zdOEz$m{`2R4b!$t{8luc}kZSEGoTfs7*4K'
    'Z+z%{;hv_Y9mDM)^**bWIYEPe2NLg*RvnaPasKK3MtgkHh`c1+Qw~7bg>973&I~XDx$nWXE4oX%Ot>nwv|@XOqRj!kM+nN?^rX(g'
    'hK|*5Jnux<62j8|EV?W*|E9(_5sc-}|0sv~F(2CVho-kdH>C1FtQrL6_|_~btZ8WtJPG+EDTM3L@X29Hx3rGKH#-HP0wQEE;m>Bu'
    '4z5=Tg9rvJkr0~{=|t#u`?iR;M-=;nLqIF^0oTmfm9DO5yG1EZy+`9pRpmFU`Keofrc_+NpB<Ush1M@g%lHMn3{7Q1=8iHp_2m^V'
    '7>66Wpd6>GhW*xYOA=1h(UH70AfH@!x!C1o<ZA%$yb#=Hqev+?be@oJ4&z=G|3Q4cP6)-`9DU2cP#6;-7d)=;84paLL;kT{vEp(v'
    '5he-q<F&Fiuwf<762g^fqV(MOVJyHXlY||ZO|pKAa<iwj7U1{v7I^#NNv6=JihI{xB{wEpYph)C-e^Novl+eaOD;Zkph^C}rj#A}'
    ';QmUa!Cql+tUN`>m4(;~XT__d%X!I?;L^l2(5ZinT)h=bfM!i>Eunfh2Lw<hIaOpS3&+7gwA0pthIrc5B?4tSvp`k_{JoIORwQ^D'
    'Hi+OwdW2kSbe$6Ojn7M&Ab+}qaV5O?VdxNFvi|R4KXqX4jUy_=RhsX^2P>F#=X{kwl4?7RE0h<)?V}&4{98JihmSbEW`KYiffG@5'
    '&4W4NdY&@m&QzkUH@chR*(xfQmqV}AaA7Ifnq8Y;QJO?N<V-R;=XoGJ!XOp35nN7_@2<>JLu{xl=U=yVE~0=<UYrc+<Z^v4us7pE'
    '@3jA<D0kE2p|nraku`smXEXp>Px=$bkq8OY6R4@{K}fV$x(X8^n7PNC#b!RjRUYSaa28K*)#utli^qv_3s(1c$C!LrarR0uA#&B='
    'k7Krl+w~|%I^zElRR~~}5k(dCXU%yuB(W@WeNBDF(HR!Qj`_5nI#@^MeHqL2sHH(1@44hp6{YRv^M~|51ewj!<gg<uBM+vg{SBtX'
    'z;y532893VN=#Susz#rJvscRt@6IU{LK$UoRVv0aKhzEpxK>&IIRCOpgr+)sdTnP{Nb&)E$3Vl((ub&c3*Th<S(^geqg$gltyPRP'
    'OS8{^U@{L40J$bP?Jy@O8ExB?{EvlgjA~foDJ$JqhvwW6NyA-6tX%=fiGMT-+ib%ScB$VRZAo)+U~DIEw6vTO1Ix_+Ezq{Mhgvj+'
    'T4ZdPGk8Z|sJRPpzvV3DP{5*sc78kcUq8aTyjWjbx_n7d%!#z6Me4qjE@cEF#b~UV)vRjSBVyVDWWj(dQlKOw)`j|MqVaN?{^J+<'
    'VWtxJGZa*Cj8_#$>RU5MdBwOeRQxqr$i>c{Q-ZNdJaq;lrQT;4pJ5nP>vAWzN9-@nQqD{#iHHJJU^*3?>}OCgt$OL%Ax3&_B@3Ai'
    'LEC`R8}s`qkNnjKR$%>tBABbKQpA(P#XSc7zl0N%FPz2{TZYagiyB%;hgongbUtzu&@PDYW%M7TZ_#R;3FYgK75g9E5fOvBA@?1H'
    'Y<I^t-ryw@*pWa_reDp{M(7eZV%-LTxW79J+JV+1YF)aE6XVPDrGZk2sxUF8oM5>C7|8tYJOoyC#KNms0mDC5UaUDa7VHt|V?D{#'
    '?=%3kMg?CxkXNFiUK9IugV59&hkN%W;L~zKh!T{kc&*`JG|T|6DupVDlM@3Yd1V4>%@i_KTDVub@fXsQPUD`!5I^cC2LZGCL>C%p'
    'jfDc+s>9*4HNk1UKNW|n>A{r_cQ4?h%Uw<pwn4>OGH>f^+&#G?ZZLP1Q**NScxnM2gkm~g!&$9zHH?#WYprWU-kiCjt<!+bRSQH^'
    'zR@dfvqbj8h5;{}svVG*$M8HEoHlok`D1E-Ti_8QB$qPK8Xt2Ai(`R%JiC{#<8qyqsbv(9@5d;HN1q`~+7fs5;j?m9Q6!f-^wp(K'
    'Sg^9d<KrX2i@vz03cYY5qVWQq`O*!S=R@RuTq!m#Z&KLeMZ}h^2&&SlJcgfDqn`=uhd@1si<&jH2XKiWD|qjpsDj2a`Q(0-ouy5p'
    'uKDj{RLu<w!M+FNOT+j*hQ5#A^5SUAYN#`~K|a=GZ4H;prs={QlW@nb4c9FjpVqE27_M9*bkP;QXe1FyGBh<11B0Q!E2~Fgd}!8}'
    'Gk$jE8J*p3lf3eA1-*WXdRY8Y_a`DSwDYcHKaHhj7Q#S8P2U8>@42q@a{?a2M0pxBE^_?Yok<o7&cO*lFlwNKL1g(V+je><@uKQK'
    '!V^7FYIP&0$XVZf2=|tP@?^!mZbN)^>2gDeNi<cNmLM;?>&>qaRutvFJUN9g??1qOenZ`LBn6}6B7jNT8sE+JJ|}lY|0Em~ChCqx'
    '@Dhqe2CA5#7Y!7L^&iTCyJ&xj!0b|`j%;rrNQML?C8<UsuRZ*}U%5L*>YJ-vr?KqTG3FP1d0Dc*hz6@5q;l^-urt-xghUEesP(y1'
    'j>ok?pc1Wdloez90^h!rjl)a+Hl*7bsW1a%>dce4wZejDR0p`3OY>xV!SvueWoXyK<&=AwF9dr$#3M{=@I*AC4e{+2Y0H7wm4t8P'
    '2h6eTR4Jshj0cYGkHthI_<J_>6=FG;<t@>=6UyChX#hKApwZ;b>4ZLQXCd%_7C*Xhgcy)B$T<P<sN2l^`JXspsH@&^f50F@9H+J('
    'Cp7pR`TAi1>8NIvL=$ol4U&Moo^%Q}K9x;qC-)}ALJa7*-=NJy3b16Pb4d&FJGFtr3U=<BW-On0B0&0GQ%jZYB@;1#xGUxR<*qd{'
    '#W?zSdpY4O$fic(Am)Mr@z^~t<Ol`nL_jDI0|`5qlzha;{0GO-c2b`rN}+O1lXxmI{7oeed3qA{SXcoeNj}q@^hkJDZId{a;WEW('
    '?{U3b&8=}!ebM96dbNO7yCzI{EDb#K%r7^Kl2*Cm)OgxY+1~$DpLVB2G*x^w*?NeEsQ@*_UREY%J{W$;7>b~*>IGG)&=dnM2frEe'
    'ik7!0Si$;<<UP<w){`)^O2`N=*ag`FjqhaIMc_tt`=a~PJZ^H#Sc@U-miz<?Q5S}dfgdOJ{~sUF2?qvG_XX;bpPf_^7-DW|($5Os'
    's|2(UEODdZYIIsqkbuLDaqB`@BT^)979p9wq@{R>r`8Bh>WOFxBLY*LmqD%dodok84ew4JV$lW!H*yd(Q-2V*ImV{)?MN3MT|iG-'
    'r2nk#^Jo*=FJWI*j1{$WRM(B{bAkp9@qnBfpJ+d@Bj<BOk(|<oausrbXpABzD-zeIfR*dK0vy)}pjt>=M9jmq?cWX_g2En~(~DoF'
    '?cK>72dtTlVfk=XsLPBUzQGUEw%GQxaG)DNmHVK^?vGP=-~gROARWS<<Y@>+5!Dy;tct)xZjKb?1j-NqKF7jmkjI8cRF+O2*L#%+'
    'T)?%Bpbk7|xs2xpQ+S*WzO1?sWta;VSCnIX6f)-brStilUoF&E)V=T+Ov3Io2I~K^&NoNR&zHo*lCW*%x=0(b(PKj+IZ)_?dG~BL'
    '<fUBrEQT%@cEwKC`8U(~F<RU=rWOcx<~UJ$lingJM@9%<iyU19-3iG)->3rZ(1_kTkboULdnoBa)^7j|;N7auBCZc+=aKZDQXL8u'
    'mC6?DccA$&?%m3Z=_+aORrq<!{T*TuV+Fw*Mt20~2_+QxO)d}{#Yk-VF};m>GPzY|TH)TG1)&7habD4`-PjG*#t##LA+pm3ljAj}'
    'r~BGpn%!;$B<2|wcw_iUq?sC*>#mX4z_2gKeUBK3Oj(#cqLF%xO3zLj17u^5P0#@KkU>H{0;nA=1O$(H$1k7tKE(SZkd5yfSXVLc'
    'i<&1~^*4J62jv}yiiOncB46=UOPrMDykt&*rA%~3cOu6ETprf8kwh(kdjDs8a6IV>AwJv%xg#)q!v2)X7<83w*lnJMkWuxHVxUMz'
    'x)j>)t#B-buk+eV&R^Y_f`d}4gb*g4H2u~+WRkJEm4`N)UDkfVY6mn-oqe|M$+LEELiI^S_!hATryUW|MTNI)T!y$@Kj$`GZ%a@{'
    'UGIbvsj$8>Kq+^h?fyJMt?XoTl}DmK4fbE77^*NjC@noE07g>QdniKxwkce0&0jJ)&6<S?(|(~xu}j;ycUUr1jZb5dc|FYuC8HWl'
    'O#Oxgf;aY*2QN9YVTZIo*Xx{`VG%DRllqd43Oupf3@*^t*{MAq+dJkc-hM{RVLucym$Rt#dQQ)<br+k6WuS@D`i3v5e^LNl-+E^2'
    'hzYa>&DN!$)S7|aG8Zv_U3cFV*{c3l4FAS$njd|v1`m5mK~2H)go+63^R<vqvV8VPc4kt^P9er%Hbi}I7_!~2Ft@(duUS$UnBdsF'
    'X%T?I6k`+hS2ZQflkd0jKYn<0uPfV+ifLm_-$URiKTo(;anaw96g+8a4u-U^j~PQJX-^h%OM`t}ml}ay9J+}SLXbN(Xd7sc05!Qn'
    ')+7vo8Q*0xx3_nQoStjjff9}`qx=|?9U#t?hHD@DwcHIbijhnJuScvZlYP~a&e7OtrholF1Dm@Xg5*{I{lJlSvpDHV65M$8|Mgl#'
    'x_zO75YetM5SOQ9&g-1;ZMbo@p5zphL17O^jzf~IgD08C|C{}drvXSfn34WNh-o@>&s9dEK@VAB_VLE2c>9U9*K?BE#UhM}Jtx_Z'
    'jiu<9%Bv_O!OJRQq6ZyZw0x7)8v7>qQ+3$yhl3l^8oAHCmFuC_(0FzO#11y0;y-gQmUupVg>RDBwn|X7NW)OVZ$S)!$Gxl9dsi_s'
    'E!U@MEmY7@zps?h=UCCB^zvpMZWm_#X|<inW;@E!?Z2;M(a`_lQ>*vQP|nX6C)qaL79l*&x+8c4=iM2>Re;E~<Ri(|R&$;yPdY&N'
    '-qJnYTnJ_)n~~J0Y7ZcwtpK;~nEbNNCf>h4>P{tL8%R?TdK3axf+xC{Wkk)F6Q3uZJ@m^T8KVSiF!AXU7XlrsKOV@_3$Xo#J_t{B'
    'k_X_jjjC%}blBxY)BAskUEh1}v_b8S#XZW~!Y$|YABIRfTORkONJG0TAfK$zQRt6%2qNg6zyp>0`F~SpJT_u@qIYAMV%P`G4Ab<V'
    'hKfzCzrWL=l|n}2`zdJ_)&%Xmm0CJVWr`a!z?+=BT!0j{BQ5B%0CB?^4B_~L<4?<0Y8RmWlxQrP^0#Flu&6Q5`mr{km-$e5`QxU7'
    'TdCjOY@UMrxzY(ikFUC2sHf-ArATI9f=FE?JqT-eSEcYEXAAb!9tlpHSoVi?jF_@6ATxucM$+c9M-E+RTsnB%873jA7Q|NfL^K^J'
    '1}KHsN0=sS45~As6`cYH6H=`UAXgx(T8bAM7hl54x!0RGz;6;Qvnm20KsWePyXY4*d=5P%g{TwqyjEMDd&sKU#PKzrMZWU(zVUQM'
    'TTqfADWK>w{Ay-t-)R_#J=QcWz@4XjA3~Z`%eO4PqFeR6p(LtiBlvvAfy8}ip5bu-{vD$AB5f1~reX9uo9vzr`A<DnXBq5FS{i78'
    'QmVMN(ICo{@6e_r5()~}Bd`nMhKX1yg~ca-;i85Ah=`ZcM6U&WQz;ISDLh|B^g>PCSoRIVujHp`-;Zs8REv<OBRQ*?d(SH^ZieDH'
    'jY)n){roIYkGXu010)y<G+OP9Z+3Lz)OjkU%GC?oLVj_rtHZq4xXg<PsUHZsqD$ID<b@F4SDfX=3V;s1)6q5mQ_s5u0dW>|0s5YV'
    'Sx@|Z>rV0KRL?vh+EWIv-T>AGlOQ5OW86>n+C(4>!zgf4>`%&q)CEF-`=iI%p1$Hj?c+Xj0A+i@QDuu(PMzbO6-hLCB}8FwNM3nx'
    '>7^YFnR@TPbvR&b&w}u*l0&L%J-j>25u853X5V%z;aE`gg!?orHOW87nWITZP;{<3#Z{E&+nww2ph`Rg)o$T*fp%bu?AO*9#$r*f'
    'X0n>RVc}NQ9n_VAm%juOi&;4gABa^&K~wh!0?^QQ*g-4hSmFhlq8^PPk4?^sj$^h-QJ-p<s`@ktqOiBdXxU29FevZ`_t5QtyGmue'
    'H!?}B@tB%{2q?a)XvC+Pgm{;uJH$vvymd{5NjuKbB+v}XT%S@}eYfcnuz`Xo#a9`(9tLGf&C-N|Qid3K>i5zJ9l#^k0imUTSd=q#'
    'QHj<iI+^x1nJl;$4$!vCPpL5Dn9=iQlK`eyQp(<CWkgy$UY1m7RB6N)K1&Fu%s33x$DpkDkAZ!;{T-!1WBRHz*U&DS@O9sVxNEsb'
    '6v$->L!DT$%!B>*W_q25?7MPWCm^1TmiE#POwIoEd2vEp<n_)4<Kqw=KxS7=XF%{=vi`#h4eZ};Jh=p7=e3SM<IKlzc%<)|U+dFW'
    'R3$)RSkY}1`|;6_JcBC6po#iUXotuH4~GCiNvlvO<fQ4FPy3|toquaOi$_9!?Znxhx5s<u?EkJDrJUEa_rlIJ;sfDMe?9EbO?{6J'
    'L4hKC-c`zVdoTMEvNVv@L&?KWgYN^EJt6gHp1lig3REd0r5h-lw6EmvpArTA!-|Q!q^!8PG|M~DB+xDpOGBbE`o{rd1Mf=UorqA7'
    'Ub&6}=ye6Rt#`I9-_x=BVri=xp-X%KtzX|QyhZ8Kcl2%+$K-@iRG|!B-ha?Hu`UuWA`zqV<w_<?aRVp(UE8g2fk3tF0*yzafygj^'
    'C*NGt-B(Jh(A06lleORw3YcP>5D1bEMdCWWiAbP!1ltbTe)ANjdd4p3I)5a?hG{6hNaEPyQMml_H^jc`50f!~bwhWPfQKsO=Ho|t'
    'JdN36)_}VX1~AM9%Xz}_k3sVceaMC7GJN^VLj93sr<9NcJ#giWfA@1Ej&4UEjMs|5`4r_|t73<MgdJ7#H{<i<`bGgwhIpqyFiS38'
    'gmEHA3W}QzrCa2IqcgP}Bl{XfDfiWX^U$sn+?qIY6Qb&YQ*d_DdNL#K`Ltft-DEo2Rt(}NI&)XPZ2ZpVrvP_)a|D78rkOE<>x~qM'
    'u422uwUxkrM02HYc)+bTa}54SkaT4#jthNRE@wi^m8lAuRepr=%gD&*g2a&E#sf-V^+Ynl^CQ6Er0>Fzh=yzNQXThfaWv8gk$K>P'
    '^h2XqUIO*DU@rZ!Ww6Qhv9q0F3!s|*QN6uEIjir1Gq|V;%*N&b<LZu9r<OuRoe>7v&rATAX?Npzc_%sPEz_5IB=B2$WFyCm3*9h2'
    'Zk6N(5<_HwzmgWB-WoSqAA<ukwGHSFLX+NtgZh9agl9A6TZ-<X$-6s7r=d|XEQ!8f%N9xc(0~$K*<~u=Yq=3ESI1)DP90VK9<lxu'
    'p~B!X+S_ZMuv(a0Y4T8euKQiRqqTiCO~>6*(;E+|guohZ8Pg?+x*E-NE`1^O{`MvBX{=}$Pd83gKL$9T-0AAdxNgFm*O>-bb+>@`'
    '=ZvE1bAs-@qVNVM%I)}5o{=lrov5hW-2$^y{IarZljtnPK;&3^<G2}jbj+VEa|?(mMr(up1qbMJnXas{I((#SiH|u46!h0hYjJ#8'
    'OR3GNP$_9cJI8{;B^Hc}z6Oj&)jA5V@}{C-APx=!{6#XCDH@$pWifVdxE?4lD)uCSSF?OARvI0FxH@V8*MDm_>9YL?Dc2M7vi8&3'
    '>bTdVAB>d}z?6bWSppU9-eV8rAS;4RRG4kDZaS_Qlelx&<55Fk%VvhG0c9@8=q51z1g4r?Oaj>C8)QFsS~_|5zijrXhqow@D8V&&'
    '7*%?rAGO90B~6+U9qyB>RP<`YN09pG(}L*FFFZZ67jaAJ0XfP)R(4m7(f<9&Hc92PjvB=ALp=rI=^210&-i^-mG#0d1lU_DL$q3)'
    'mn^SCLk|Aw7}ZNrhX{|*?p*o(3aP{?p!h;lL}l^)5^}>JSZ2e^wJe7ka{*ldn-ca!{-?kkTsfL><9nDptfLQW``-Dk*q(+J2{MhE'
    'tIBl=UwGD=u^)qnUUC=JF2)rTu&vfKo4=Oh>#Q5Z@^+;}?#_ZrWAwO~O`S~C9z%<TzBhyp?&6ODVo#(<COlzsSmHPrtEPt*D)Mo~'
    '5dwqRs!ULH1PVT?AW={|w94EO(sEEvuzY7ob^c`HKKa_DZO`cNc-du*<BH2Bs6?45U*i_7CNpeJ0LbN5hqGM6T`Ym1eU9!7Oz2lB'
    '<N(<s1jBi$)NykX>P9a=STEh&9pxJ&O&=RDmO)^lqW<miH%8^=p7pR=8@8%sf-6(ORDdVt68!~%yoc{Pc1qSgLJ*v~BE8`kiBqOo'
    'r}xAW-lokvyFFMz%t7~2x|#;fcXypSOq;eO)O@Jt)r=4e&kZj@Ks;sDSKiJ^dCWt24TUfr&qp_~!2^6#*#;a34C{E|wL%wXq~esj'
    'w;*+3HLzgR%d-e&j?LS>zBSC<Tk%nsI78@3MZvy@*Hr=U|K43CX7^*lIU%;O*1Ce0{z)_uJz_X)mVH0!Bb(n0+EIRfjy&p+>W?e+'
    'Q=DeYBX?J(7UGX3xp|5&dikJK*I}S!IifkOpVv?M+b1kR+l+D)LxZWKJT({+)S;_~!iQr{pXTV?Rg&R`s!2IJO*%nFPQbDVgu4TQ'
    'l}axG3n~MRKqZ>jYg<SoIQN5Ug6xu%+8eMmbm9Nr7MfuwWk%23@_4*vQ+n|K$Tya(haYiPRll=ce9FQiD;A=nOxaF0>NX3VAHVvC'
    '0Wq<hxUJb?(}T>aj+f^jcxJ5ETa*guv^V4}Y3`7fA4I<Ov4X1qAzaJL3(6XmT?$yY5#CS~Jvs@PW=#ZIYspAkyoi7nHgog@R07{k'
    '6`^&{8W}FncbUaCbznxb3OtcdeZWz83r+$p8duTgRsBA^hp6h)4Z9A%t}0B;G1Fj!4Q|8j#@XZvg*r$?W`6+-B!L==7a(T$a~cAj'
    'ioSq3Alva3zccF=M{*XiICF_*ov^2s#Lp4k*>xJ!O51wYW8JQU1I&&&TGis+^lPI0H70CtC!Pi!y^XNDY16&2HNl_klEP1Y2Lw)A'
    'tLvUpvWo3~Mja*Q2V1lTDcpP=>BO;I+zLg(GhfKo_j1<u0nPSFda1_Y7jl-g%H%O5YS7gJvlqQ4R_PT9JuWqBW^H%UgjJLWAQFV>'
    '4a(+Rm%wN=9K{vy#y`su(r@3;!oRV$t|L?UD&5%vJb||XU39K*eO0bRPJ8%W;0&VTbhCz;<;i=+s}-z*a9P|^(-@W=R%`;RNYi@6'
    'MRCJ%=ZZOr5+~|SxFb5LRn0lE3!Z|Gv-Vjk6_*5z0DvR{qr2LA3*<yG*KALd+xqO^1f;(h#j29w3go9xdTr?Iv37o(7_~=+nD5vY'
    '---VQamR9^?R6cNn%-39sOFCUd{u%VR?^=x5|d#3K0y?q^U~l2R={M$g#5UqgQGF%`ZC``e6ZUhKa`izShK;#7r4O4&r#{RW;B9f'
    'Hjp~`Z<z};4qE$i>Leim@dX_)aqKTs2xP@*P$j=ZqTcYkRET2|EpZFsXfZN}Fxm?R+-L1rQM)*R?~(?`nT^IJG3nSnGqv&54A6<d'
    ';xtB19_BTkD%@QGWF%bfI4p;05OC=pPX3*AE3&Bd6vD<CB$X7dP@FEo_)9gKKVQSX>+uOS2Ap2;cewnHAsc%v;&uJowF~OuZq$3z'
    'U6X%wWLy<#Du&)7Pw-3xm;B)%-__j13h{h21QI59lrvs<pi37=-~4N+V94dJz*t8yz|t2%qShH`h*2)C-I-MzBbZRB-yFnF2D#QB'
    ';n^$Sp}hv?25EimsN#sW)T42MnbCFu|697t##!rYZ$uI-=Cg7%ft~(?n-f8~T1jSaUcgBo`E+a65OCM-bhpWk*F+Sh8{_(O?Kn=P'
    'LS(i8U=Q&{R^{^a_|#5Cj$&rL3NR@IE(1VQ?qR-(P0PVlqHfSkt!m1-Y_O<tlbU(?|AYx@w)Vd>p@HF}6#f{CS{n89nZOD-wI(|T'
    'n$fRI61?s|yR@z-3g0l^5%uJ#kDg;|-*i22$kZIL`d>C85|XSGIJ0AVu?>lD&8F!kM@`TBD`@sour@V{`W|Q54|rhN9U1<~Bd4iZ'
    'iW}DRm-sBOjxLrENgtw40V);?P4JS)F}8~bBvL2GZTSL~3m(+}%Bs3PLdHj-t_Oy!pE~o*PB2xZ=hzb=EyhmTjGX%fQX;5ubj@yi'
    'dyXzfyU17w3W~=*Y9!60Am4jLKYUf@YMbX5Y4rhP=rQFRLnFWn37Uub+%8?S45mUW*|18fC`9tZOQ-*Zc)P+SfUQOf`pNN59i|Iz'
    '_%FA((JYa3Ol<|46gVkik!DdI`~aD?7ox6mVqTPe{oa=J@AdXLPaJc;*jg|@!9^aiko}26C^HjvXWLVC#13XthJNEfRmvP!B~-7Y'
    'L$X&i+*_~ostvL!zr3MY$F-r%Tr4425O7Q875jc%f4Q`jP=KSxwW8OIa4i{CgqoaA_(L<#q)NXeR+x-O^Tk&ky!l4WSsHqv7i$-='
    'p?L1A9(jwhvru+!oC5VH{1Q^tg@?|CY@aFZX<`>Uxg@87EDi*V;iIIR<^L^fWc!n2g*kqBlT<@GpGhf@5|Bl8a^H0?xIzD4?VH+P'
    'o}!ay{9f$0E0U-Bf~yew;_UV;4vF3>uuSIf+9%MQx6wu6-imz}^Kv~E`yMTkgcK^f*%K`MZHQ1)sBj1>`WF|_Vz6^)PYvh~9vOf)'
    'Em;eg+#feZt^^WXFQjVB{s`uZiI+#bBT6gs1&E0+F%TDv6oWT?FncP8j%Uz}MpSCaTi|-?0(~D3E^gIIH-)~BO%L+WQC%+o-Ohnr'
    '-J)s6;0-c(d^~%u%mIvoxOvUj)KVm1;tqo0vWi_OE`#{56gT)8*F1Wcn+uoX^mEZC$IYgd;7ppW*p#k!LOwzJ2~W>Bc(y7r&T@A2'
    'fwP9m*RCj~<B?4Oa7w5Dgx{EtRkKf6&Ec|oOT$vBZ6C}Idn`XtYngW*9q$pX9{REkNPTDA72rsi8ml*(;sR{3Yf`e9w%F0kY?hhQ'
    '0pZDEwgbzMy_BPEYCZpS>Fk{8wO@Nn#ZB3<J`J98-5l5%eDk9pqndO7S8=gK))0QNx(9%V#XyHkx%c4qVPg5t8JK10Ui51gsMyB2'
    '5fN0RD{P`}5kKf*dOn8YLb+v}H-!1M3u_V{w!g-^zPxKCX?|Uk*P~euZ1VPLxo%uIMtYJ(e|!LcAX|F(0x=~*`+%VfOQ=n$QGd-D'
    '%N>|)iC`g|+ICon9lv7eJ@KJNOp37B+T{WHd$z_{v1$Kuo)%a}q6f*WX;>*UdAqB1uDhP8DWya_9|{71<{K@COqLGLG3N~?8jry3'
    '%N&GiTm_vFD<<`DF{?{z>U9`H9fyyl_j0oFi?inISGX693h3@>w3lo<*cpaP);_cY$Q^SN*W-)D_uOWA!3f%di8<)OI#WtH-7<??'
    'n5B4%voijwx)Z}|dE+id)I!S0m`+DQIej+k(72k^Npa#?9p@dj84!tsq~DX7m!^$Agn(=_@pR;035wc`%xG$?qW?QJ5m}PL>w>bV'
    'Clwhd!*5bYrPt2{TD#!PAmRysO!_Viuz4NQim<I(5RGr#St?)BZEi)Th{Bo;40W!Ge;6Iz(0FtjsIH+TY$IIk<n_0NEPWYHn~)zA'
    'pJ8^`Y6+#-z7r#A(JVIBlBSZ@g&t(898$*&O^PajuCV=F3v^8!m)GJt4l)F((5%hyO5DD_njxP($W-;`$EY_$nb}>}CW$C!2RlpL'
    '8rfQblfg~W_j_69jqHoA<Mxl&F^>*dRl}=9cCifNH@affti4rO$WY9g!b<2l;(qfiF2udmZ?38?o%5##vsSh$bB_dmw<l*E-op!Y'
    'gd6lgt%|QC9s?SD?@VsF+z=Tpr)W%zFQ|aDvwdQ<%)9@57>wgF;ndPlwS`rrJrhC49Vn!xjz8xR&AB8qGJ5fBJXvw3uUkE|>?#p!'
    'wv2Cn*{wL){kK289W7H`63B>xkKq>ETrhHsfhI~x?P2AyibO#A-6#~9F!VBSjvIs`z48Y>yMF5KUm!7XmC5`IY2;?(pJ=uy5bq8s'
    '=SrI6bq!^t?q^#S8~F;Qe<iy-Jzk(O2y>@&HYchgBBhN2uyP2e%%+7Q_WP~WMzr+DPC+U|b^GmY7tyZb%9BT#O@Aq)XV7+3g#D-E'
    '=k<oeHy<^TX>LJ%z0_eB^iFR)<D$1d+Fy2GCgb#gN0&XH4i5%t`Ct6qdev!8rL%G(Iy)U3lJb7$nLOezD!`5QRs|)ndwh<dXKPa4'
    'dRPRk>p6&P`xSujz`r!4CI~0YY69K-@Zy;8!E;y*l}TM1@l@15u$2X2<d-y;WsS49dTk^_cFbVj3^1lQ@=~RbVFk1K4$P)wvksPA'
    '0~tzsIm5iC9*lfdOK0&pL>#%*QY?UV6&(S(!*?!E$xM^CX7KGI|0Xllon`^dFb9@6Ss<VpBgA#dQ)64!JOk!yugn%DTv*y--Z)+_'
    '&FA4%gH!e-nA{2Qmmu}3o-prhauX=_Y;c}F@YWuACt>LBS-|LReW5=Tz>-~LAMG#=<Zsoq&X;TB4ZTBjgljfP3G{Z;!@zLo{VW&n'
    '<-_d1Ql!s>?2gNp<a9!pR08p%y4+3J64{};i;A$D;pU*XaO3a!kYxD^K~d6cChlYavKH&djWu*{#>SU%>~RN@)ZQXpS2%UJg=*AQ'
    's;mu#;oM)h5f1LITX?upd-23)gqFZTf3hU}c}+8QvzGDuyaB@JuBnd9lYHb-?cDZ_79R?fg!onml&6Jg$}LBE%1->8bo!NkCf@rY'
    'tIRF3g}~lypS>QP!S&x)|JPf#aVUyxx;tBWh)|oHG=_}8=$c+P(elIr4QufENV~cCUaPdplC_u$f#$7|j~ly^-#dY$SM*9z(fv|Q'
    'js6LG8aoXymD!e@n^7}Ju-F+a5BtoW588#wkPfimabkc4U!z~IfR7$P_S@fwFd`eHi@rDy1}?*o%X&bi&QhT1?Mdd-a`;}C@7{Jk'
    'NLQBsZW5RVY(DCs%&?guk|HcKJy)UaQ}2?*$r{QWrW(EbZubLp*!!=?;`7_qZklMr5Ke;_#iF#-+lmtyA{Xs?6w>6a@Yj^YM3$X%'
    'v|`v>P+v$R{gKg{{zA929ze#zTeb&GzK8dycH}v!RLny+ZKC|%A4T$nl21T6JrCYM{9RhM(0BjKt#N@HBZ5N6r=cH)PK^L6ep9tl'
    'mwUDgK=BKPuaVB41;*sY?Xve~?zycJPy6bkuoWt^9w%fP!3(l0qUiM{(C0II0iF*o{Ru=pR&3`0HU?1UA?@jPRAcy*St)Y-tc&Kq'
    'tggL^9h6ntk~;6M<4tj%L&eLLV=Eie9h|*awgQ^{C4maz=zgW!OK~<bM58k&Z$25zkFJUV(t1?(XObI#pYO<zD@QnaVGI>enhL}+'
    'l%!fmna@lMSPXYp)Se?++_#Hk5{uL(287l8*PKs8$ND~;$1ON7<-{-lpXpRRNS{9DsgS4Gij+0W)fNXyIs*1S2V9NfHc6%A;4RZ)'
    'a@>|)$}3Ni#WAxg+VEG#x#}*Un#VXkvv5-c{S0wC)OK97bzvDS+$Yz{uXW2r`<5ad61CuT4d$C5^byjjOnSn}{8?mT4YY=A=4aLc'
    '6s`r>-;rwpM)E3JIc!RnJwDtrxBY;%kW2D0-`Z1PhaPzl+-8?H^#-mW#9uF!g7eY(0SVn8i{k>^iKD@pE^}J|3nlfHexK+Q+VsUO'
    'gUje9)smV$mh7ouS{S$fV@9=R{d52ZtHY&&H^>(r-(+tBTA8mgN+AJBf5NNYA52CNhtAErD2DQE1)0i!k~aYb3!XL2;EAW5z`n_e'
    'dlJR+gw`E6z=OtmgD`=<Ya+i~wLG%8M_eIipcZGQb1R3h^D7YLqUAO|NwKdh%;3bDnxcOT=x}CM9b=wbAfA1Nf$TfIfC_;{#e8d}'
    '#hwObbE}YNf#m#=_|R><I~}_j?nq>|Ugtk>y5q=qIvW#>(^IgJ*uR4o#`;UOi?8Yep%yh!7kvvo%yrAWi7G~WDp}zNFv;Hh7aIZb'
    'CK-It9j{s5;Pox=#BADrwTsyV;M)UWnZP}yHhYuO9PLw3;TH7R6s8kUfeb7W_QUL-1R_cE9MXjDxT^Twwt#VM>3L-dHPyA)mtH!b'
    '4UVXd`Z7ZWa$r<g>U-i@n)fa2P4S255rKMzGuJ!=4n7s`wM!mlqb;<)?#7?^&vIX4DHcp28d!ep8ZSXl=3Do0gjq+A^gcervY=Op'
    'D5WSJEXI3i1;NU7X65}O<z_~~78x}R<GRUB$^dpa$A#22Us~zm9z6o*+`)mgC4M0m(`M-xui=6gQMhcF+*kdIbA)efyjP79ydn9='
    '?#4+tk*)ZFNH3gM<26fO!E@J=yhJRUCLI%hh8Q|Bv8>ug42ER$22^Mu(f8F;I+!Dy*pR_l1saT`*|P(yhvA}=8d^{_Z*q*@vKzyq'
    'S5piaRq48vcr8o2zCAy|$+{NM%Jl7JHN!Rjb6aI&@2V$)DGwe8hZ9*jh9RJJ-n=8egM0s}S=u?6<bnMhw{9Zkv&(Y0Aj5{^yWcc>'
    '5roexE?bDzTpfH0=xtR}?9>1t+kVQXD5@L!82csutP>3PKtM_!Yy}gElDwtp$v>@<H8`A8w!>@kyn8r*kn4SQ^uyPeX+9w&`$@jU'
    '3S}X)(}V_(?r}%gG3aa*olw>MW_YI@0zyk<KQFjzK~(clu|Ye4OcezFSAKF4nyzVNglNk6XRg~TTMQ&-qH7ih&m}bU3uq-`r#D&M'
    '91##Pt}jVP0#<F$!R-X!YX1z*aZy547@+kxg7j885YiWZuhS2Q_RovIdC6lM6ZLh^eEjQ}nw&?c_t2a8QXdmv*S@Oi=dCe9l1-<P'
    '23kJ#q7K$E4%MNT%=xJ&iBm(jxKTW7cD&p9;m>8;yo$m`G`%yf@|t0(%%-JvzNm6d8xSK?oF(7dsEqdBZo@?**CgT7+SWl9OA{Q)'
    'S@y-4dR#1T#*Ji8f6CYs{Ee_t-bH-6g}JYlYWu0xEIXUr-z`7lx$Rc-<d;c`8mOUJYcf1`tw+n6(0cwUpgdl0S&ZqTkpN=3Q`QL}'
    'W&&6@zPj-ON!3lTxmW5hyon>vEnfxj{W%x`7p?a=t&Kk7s4<POEVpG3?Eo;;mxQfoS*}sqZw+ORv2=F&y4PzO8lHYKD89Hlr1Z9{'
    'WGa?#f=ZwaZ14tJCW6Fl9jNNU15cLAPocd#-kMMDRn);i$^E!9xd1zn>lk`w^re90GcnCo<VP*7Dv>A!Z!IG6VLo(g+5si|k~*g%'
    '&%A|f^plNbjX&btwDL?bM`Z_tJRBr;;poaMsfMXgTz-KawoIf9yka}zC!;DcedrQw-I4xq30~*-Mnrdn534b#Fd|kj<C#m~3m&@J'
    'Unog1=BKt>)2rDDMAEHUGVmr$vYZxK=YRI<xSUay#1DQO8=sT}EJ)A1t6fU{fycp<#T@sr<Pl`mIx)~%7$;2VeF}co;<67)!iAGW'
    'Xe2Er%|G8p+M$*Vk2>4Me+U>Xlj5!u1}+(3+$<!yx><LJ(T8pkz{YTbfp?~L7>l=+7+n(N{sDkUm!6$3T>W@RMm{Gk7|k5p@8=7`'
    'V1llua^cNPd=hbo3N}jc@G0)m^3P(2Ruu&X`uM2Jp#uO1(QqMF;jJ02)qI*w?7dv<bcX*V!Oc*k05ZGtQ}=K`t@u)_OI--kD_F9G'
    '79w2xnlg67#_=yXjN!qFeNTf1PhT1sjIvYi{-*AerU{zrgh4L=8Qnia@|G5~FfWE6v(FjZN2R4Xmk2JyY;H344x=1Oy~DHXQ>(ZO'
    'hNEf&|1udZ1ikTj5qxm84D@PmEBIvM@#E&1-ZGA=gi(W6BV$oekdk+pVSQ(h$M3Ic#m=kgK;j0xM(xv(g_87|0gnYs_10dU^7cyy'
    '96V+=KRyy5p^~244#&CBf^9)7g>6ArEBm`Kbb4E9=5?K^Io0393F;(qA=#-1DSZ28(WN{GD`1AF&+oV#0EhMj8)OH!;0jLx;8qSC'
    'BSET27~@oPB&Yy9`r3CKY;|Wz&7e3)AbaWG6J0w5Nnkg4$p0vzdb^QL`V1vBLQ=s^53L`qX%*9>N203xN8fveE)$mxlBUb}=~>&n'
    ';51U)L=$jCw5wtfa*H2Ko*DnzdNlVtxI4WDFt7Q1>OqE?{U|R1eV@?c{TgY19i;|Mm<$m1^OYud&$WwMm74A5j*~sQ_wO&^wtU3F'
    'E<|hyzSp*_#M}6KW$N6eKrFXj)NVB3_nUh)cy{G{6|8)}NYr!$oi<bJg1@&G2HgIs8+t~aRRg8^(j+9j{@>k;lSC~m^OEQ$PD6E|'
    'UklBe8htOMJGzGBN7V5DM<Q*;dy85$M9Szyu8-lNv}PHf&^q87GB__{5E~<gYmw!01ahzcrH(249Jrx3na3mFvU_ZlQE}@MsZDIo'
    'NvMw80zJE(Xn4&cw2VrsZ^iEGaeMPo6R(?Lp}CO{)7Ol4r5*72kOxRGlx0et`vWp|T$+sl7r4pcQfBB2+Ve{h+2WnzT=qVj{zsnv'
    'U=)j8C;237(vjz@63F)KRJAcn<I@=fadtJ^l${f|$eIwfY(D4vL=NM$whwS05O@e@la^Yjs%BMK1Aa|zN!3h4>5Nsqk<0c%>+)%m'
    '5?PBVUESV_wwgQDj4s_{$VnHdfdetJN_EN3qF?@Zx^sHS=-2Dj2GqrSSA$(HtExX@>dquJ3M^0$aoPm5oDJIeFB6>D>T4`Xec30{'
    'V-w5VSRy$PW%NCfD&4E}%ZVdg{X_fiH^PoFbUuO3WVpKVOm3x#goevMZ4by3gv$4aF0vTXV7U#fv%Q<9J#9-2UD4Da90k2Dw1>h9'
    'p>2M%#={wP8I4qs9-=*li(`UX{If_}R`yM0_S`qWSO_W>+1Z+@Pn||{=g?!<8OXgMmC!~-<^5sUuvHqUgBO=(>%C`!1*;Y*p$SWc'
    '`v5p<gu+PaXrq1@LT=R2Jl+Q%Qg+6uqt4=QNM_FH`vr*~XW4}p^eJRPT-lCmn;0U1GBMi@?gwFWq#BbEe?rekXj8n12Y<%^(tnI<'
    '+HAs4US8%k&ux^V_>$<tQwe2hD{L58iWs_wjI00XC$jYZMXgfR1VIaO`fLA-ch8|UbW^f<f?S{OqgVh)QfH#gU~0evu%y3EIEKMV'
    ';k;O2#5x>|7#7k3KpbN3M=SBJVwH$;XK4g-qabNB5L6Yv+cLBZF{AmQO{PI9<|o`83e?B<5S02vNwTD<Th_F>BoNvvNQY)CJOsYk'
    'HCm!bg3t%ZX8SU|D#y_gfX1~hn0f@_@EfiGM^280Lf%xErO9^)STAJ?0R|>puANvB(XBOsv9I}8fz8)p^!ek9-!!cKphKiWU_rR8'
    'Tj%3AYAE_j>b!?%XTBSt0ZifNvkGm=SO;yOqYQM9WF(u^znf<|mvjHb(>T;ATzCJ0tTA8+v4G<r#P%;7wk<-^dvK;e%*HnO=X2Y#'
    'S(6=!?Z>#Dw`w>Qu0AQ?9>R?(3V6NUxI(kI=(54C=+C1Bew{j*d(Z%26XI%HedavdN+yD<0DxM}t7Ew-NnGus(djh$L3(3xw7Tl}'
    'W;vY6%BxTczd&nVzhtGr23cVyTT6zDQV+(sh3s!YhN4)!a-h=goXd@e%ZScE=@{F5#Q<s2smm#u$QC(o3TZSCK#6DIZVi4jS;eXH'
    'CrG^|xtDWnBCIy^@)~4j@S+K9S_$6GmacKghEEn5{@WQne=FPT8m4&Xcmd@9s(Z<<OyJrv09N@<LoeZpp$OR!f&e4ASEGzQ!?XHV'
    '*#=p<jL-rI6F(3D<ek~oT6F{(I^UIOfRvY^GXJZqRq2~kWPUR~yawY(+Hm@J`v6rx|3n;MxT*2Kpz>yLOSwassK-@X8qvg+7xPxf'
    '_WsS{wu3qTRJEdfvDyK@jSO7*p5uk_40A%7&%CZe-S~b#asG$6Y>t)Y7Wkf!_XrmHLoxmP7b!WsbsP9MP_(F-Sb-H*0?)uQ5o&=%'
    'nXJsv{MK-wg#}T4N0K61z<j18c!l%H!l&f0OjCsNnC8!+y<vuyo+JFlnk_egdugU*oR6}f@%^p9r2vHX{Cu8e&Y_^vHT$yD-Q>zr'
    'sTTwl50UDT(F*P)rh+4WXw1^FMk?t>K+$*<iFe~)%DD)w?ct5*pX+F~C5(W;piCx?jN!Bs?xM7r9n|Q|;!RuJ4<bIS{K(2|?*@(2'
    'J&Zq6svxBE1z9Cf@L@`#t=I&?ME8v&<MS^FhLMJL9S`xuIuBl$(8;b_UIrOd=$IwAgXwp8j{|eY2bFo64-#KW?2MoiFNk<xCi_v7'
    '?!yjFXkQK;!2ECV?>+fADo*DlzgNz|!M7+=g6*9G|IQK?vTfU;692n{Bv{>e`B50H1VY+6ZBsykOOR+W>&`i$zglSrj`5CZz0B%+'
    '%@uTW7g>y_az#Cty4X-1vF&ocszNLiswY{@90nTrpyln(f$n*R`8&x_!aYFN>f;eF<rxH|dquCR+d)sVQTpom1y1IvwX)MyPi)vb'
    '&hd;LC<h(=sFFJE2U4_P3M5fI5>pC6TnS=Kw^tyE9(tMg?U$@L;|zi`<-1w<D7uDrqo2=s%T?A=GzKa+CHL_I?gabSX1kR*U;p*j'
    '13K&aeC6~RRejD#2qRG3nc)s-et>@GP=@JwUM-CKfGnJQY%WPuJhSQ9y#@Qz>@EGB=~n-U21&zjfSky8jO#&*Rd1=7gQJ)h-<$>z'
    'Lo4ivzGL@NLOW+MMr)sbU^t^4|5%xgeCfODN!;&gc8@MnrhAn2-JH@Xi0l9VdO@P3+o3pg3GyKZr(II(;Vr@Zl()(kN6>EOrCHzw'
    '1GllZ*kUazr;Ic<2Zw?%Qlha9re*hOWix1(=tjhzll&3NXuJm#Ln-WQJCU*!E?eOl4^b+!xR>93oq7&@p`!F=QEK@U2#h`slowp5'
    '0woAQE~g}<zq$S7<`uJ`sGVpORaDLcEd<d^LKZjw4Fpf*eD0j(^1cLtLGP53e3V1x=!k*C>%ANW*$$_QT$g43#ngb*WJNO)&4_9|'
    '^`&-RNwuu+(7*IDU4#WUnm1t`--AdT^<~kqhv+RZE_&Y^ErTz4Z8(Qbi_SzR^B*uV&<c3DHucI@Su~5-#t%sceO`&_lWLBPW0(eI'
    'hRz_xu=F)<Ed=b0la~zm-jw>jUu^(Jm>LA6RbUZi&OH@Uy1^iYUZ+|q6=1%*VNDt>PAnciiQ)qi+mB8ex@(<YVV6@Kd@QMu;fHOT'
    '8*-uWSxh9nKpmIpA&ifS34LRkVKsm>bts$RivO+A{KxwLD=4F}fc?DPCUKS_jBPIh-oo1X8V~2Eip}fz9IaGSGJo3$-I*CmcF#+z'
    'g|8m+CgjBD4Ny?ls40Q;gb``wlaceAy(QQ;tcWE`HId>@bQVE>n2>-);`PVjYYycA4DjS#cocfR4Rp5=1Z<*Mm`r!mi{obOHzY2J'
    'HBdv2z}Z`%%*A!CwU-`{5dZV50f@lj6FIl@V*SVVp-Q6JpcKmy#Qz!-TK96*h4aG9v>g!_+d`OL6qVZ0@CNZft|8{Z&lJcKbg86R'
    'n?8}d?ayP^NYJR0a=z`_q6HqDg(VJSRf4zMjVUP7-JGZ!BB{iieBZ$DFv3_#?Yio5KW0I<*rtLx+wpSg@LXoS0tc+4M9{nKz7C7='
    'WVbcQ>#Wvmf~Q&okBTY_xNH@D^G8N)&>w84A?S~8f$E%VKjQ8J7n^$Mo31UNuzHzw#{yBvnrdL2t7+-{N@YGUO|wP&SR#w1ajL~Z'
    'Hk7Erpd0RKEBooaVXb0ponz(qz3h5+7qd+(kK6vPvD)SzXW-Ng^=RyH!^4Tq>GIQ3gd;3_-BxQ*DUxxIe1NeR_2C&v7X(&C+NT%i'
    'cxf-8PmfkR{=wf*0&jq$ly&)MUW5R#QCY%{z*^n84-%kAoL$UAJeBc!q0(p{W1Hc{{%+NYOt0yU9}AF9`_Gi>cB=Jpbf_EjBEoGF'
    't<fjQ6}xXa7zb`iJP>QSs)(Vw^Ntgor=FM^u_e5kJcrp>hMZ{o*CllaO&uwwiB47)XC}q#2D^wQkvZ=8I<4teFxxmRJy?LB!MY6f'
    'GSC&9u}!e6dR>zznO&I(ck_HiE*uk@3rSrJ>+7nns&uSxAAlLgGlEN^b*L86#g9B{QPu^~xA@rr)~zUGQqtOyhR?H`WqlOcwdP3V'
    '!_pV9X*Kg~hEf7lYqZxrIke)&Nk}CM#zjN4`-S*!*5_(iZhXR^r0&7`GB`DOrAU0d+{E^*#SxK~7;bY`tqr2%b7+IF;jCOz@P-r7'
    'NTZrr0Rlh}NTU;=x4fLIPAz^IrPwElFV0<3Q85_Kn0FvE`%zK!X0oOCc5l`_KS7S0%>pV*{ssjow-$eM$}UNJJ)&yl`mq2ln-KT='
    'XenEn8dN3^ty*f=P5Jf#A1d1V?Fbnys%w^K4gVRb3Ml3IUZ9ULIIY&0^RH4-3*KRZqIL{n<4n<0apx{%s<dqPHuJzzZ40U4lQ8&i'
    'C5KV_o^e|EvsguZs&ct*%+c2W`x}3>2XKsz<lz_Z4Kb2FJ9*J-_)V*tX_I4@ys)&|WXWy$NvmE@lSFCmc&UDV-s$^LK23a;C}=sV'
    ')&EfsCFSuT-X*GtHzJ2mb+??;i$ZsL-R6?D5KmOdodQq1P7S*B7qb2FLx-3`CIY_LSnOf>`m@*x0o)EWu(fDhT}f?fV;ZeXD?($B'
    'Zk!sDY%;8xkA2hnKX~-|LcVgPt}f)a9I}dlb7hKOL4*FHm^R0+wkW$GTGfOrvJcx4^L2IP;B62_L&ddDz{dAZZYT+GW55#&AQUI9'
    'uTxsnCi_2SA!s7^wab0H3jPim-eJF7Gy&{*LUMV~Je84Lxn9;#kw^@e?^&rdUcTU%>HSJWbYSLPAxD`2!VkglTGaE$ud$cugqa>%'
    '2!ORm6fmM#1~AEG$MUAZC$D&$jF$1`a-$(L1kpVUeA4vr-j1H>mZ*dVvyd!AV?qC+pN$DJ#F5_p?yrHa0K*tddXvCGX9l@8P^w$5'
    'Jlq{!|9_@CIxZz(qZwh?R@vjEWUq^XEsZ}WimM`;pRTRni#^gt>N~6yLQt|OQ%UnsQOD7S8>8ve@#SHa&PCoI-Ct~8f9qNU1S!%{'
    '7hb(FJvA61(q1-xUAQy4VO-F{lX$=x{q+vxCwRpZ7wB~t+87ZQ_dUc*@hfog$ax0My99tVsD?FcF}CezT66|YT{;4O;}({bo$08B'
    'w5Vw#n0t|*xohc)M><Lwh&;w@QU7|@H3G%2yw)ACfG#!wZP>iHlAZ4VEqIRs)P4WjiN`}-@TfNzm|whhi&e}?VT?J3aa-R4qD@#f'
    '8(A(k<vZ*!Y+15*MaIM<Q#FWzqNnJxhfd17gs=VM;F^Y&3Oa#QO8OUA4DyNP>p3&`v7;zD$T|Ni;THr)rYUyrSmLtq(>==moVg|_'
    'y5@IRrQp|L6Jcv2*qmc{c~uuI7FhFvn4m2ZUgT2#M#Vd-nu+jB0+k2djVT=}6i+sova-M_3#NP;`j+ZB`A->2P?%!T(k;~)P|U?E'
    'd7p^6`!Btf5=Kqps4B=@oD^9QKw`I0G<a=r-z!roC1EiSw6Ca6bZg)Q+Ou&PO2f10Cldq*0Qk=}>DSkOJ@NI_+G$Bkv@goxyl>(U'
    'OQ8iALSA>!%Ow4*J@t77h!3fdsM~g=Pozm>w2>ZE6QlIW(#s3RZl;(mkVj~Aok4gSn0nc=dx4}m)i}<9uLJ_%B`(6z8VapJ{5+e}'
    'n!)K-7DojD^~k2n8q@^W6szOZaYc!!!R9KWmQ(c|>?m0<Tf3B^Q%^0FnTKq10wX^kAcBN!w75oIA2H3UiD8E{Yw-MahZ^)*N#gAU'
    'GwAo3bFNj!Qxy&o(CIU(b3yoz!3)2ADSo@E(cd29LW$Ga?F?NZ!FpaFg%JM~@68DHMiRxTc=`Ev6Ya{-qwsLYz?q@Y>&LYuIg~4)'
    'zgbhre_j7tT@u~BLc__JGM+}Do+6Kt(4y;K%o+qr@@(Rq8#XWaHme0CXefe<Ag>UTAVX%v)UpLoFQ9y0L9+d`DLr~2y&o%LIJQ>G'
    '4+!=I$jY%`g=mIB6*N2Y?(RY9^rP#0hsV2s9L6k!vH#<~urmxfszz(5iB%TMJK^=XDFV|sWcmc(cggv|`hn`UQ_kKpXss|p{x0(7'
    '|5UrEhScP0h1tU7DY5<smVYOhwioSh;U34~s(rmr?dq$0GZjz<O5gTq4j4i~j3~_{YS^vqBQ`_-P!e@GT(}abD#*gMm`nH3jI*)$'
    '4w58OkVyANmwySYdjx~H+Lx}`;(qYEJ<#rRcIXQntmR=2q`KuH*-o|sVo^>fUOfevH;ObKZvw)_5R5)D1RoFdd-N7$8nJ_?A_pXs'
    'H}CJ*U@d}6d5ev*s|iQJ@8Que()KeHt{=EZaOjEBU#+lz3hSiFZt#PVK5o9BaGS3$p%XpB7=s&J#tXzw`vgVDN-so9pLGM!08}8O'
    'b2kL&LOYnDl3Y!oG8=?t@`Q>BbJIrtfOIAcNc@x+OCD_gl+@7P`<wlt#p0y#Qk4<t&=WAm2|>Qlslw<a_<%*%M9CSPP%1tkXrR?M'
    'Ls?dlxh$)CO!C+s->#q#nHb`g$%5SQrUqGE*+Vi*K`DqZk-9h%S3+$9MNc$J=azRzea&V9D6J20o3xVgL7D9|lcGd=8ClUwHUu|&'
    'vf6zoZuYkWIDV>G<Jb;A18VutSvKmuQ!{j(Ch$sub^r6;=1)F9f?oQ#zqZ^XM}4%haL^RB9H>=|d|Sz2!&^5&8u2mBbNV|Cw+*%~'
    'g%u-{_YUNkFLXH&bj3`oQKNtZTA>u^Vp5_HXLJP%Yx(#aE@s)RQ0C_DU)}~M%5<R-%k<#wMZeQ>M&Cvy1CnR)9s^R^?0+c7APjrv'
    'JVA;v;#quWrRy{KnRbUcPF<fmci|ZniDQOOHtflINI+l<l;s+V4_=khW^It$+zl1sm2DJ59s+Rv_t?CJ!KW&1Js?s_(o$_HPZ>k2'
    'o9x`-JxW~@r?vZ*c;H<iO1DWpBF#U32L|ejX<z@ZBVY{&oA>Rt2@>7EllL8>j5p}ZY=S4H#ysmfgARZNvS$HHl%tphmdywld@<Br'
    '`O9vK!qV|M&%C2vPT-NgV^()J(&GHW55w-nTrVv6(ex(UJZnsdD%&fyT9wK&i@;j8vpXLC_U<p#&Zc_%s1%5BlcB}!DJz6;fxB%&'
    'h6xRYf#B&jFPza5PV%1B6~yr{8h`rJy3}!DUmnllxQ79v;TJE+>6x{%)Uuh#YA#sNOtPy?^$bKb{-C;zbTqQ@uI75lInn+>v^ZHF'
    'l(YEh?^v}kf5e9ML4xDA(-Xx0m==wDWq};8W&T~Mh$yXq(USl6%6nZq5B25-B+VVkegE8h84b-kwR069nO>4Vq;qFAAA8NR0AbO)'
    'Rs>`I9t2rN$g6H7BIWKO!Ud6vWPV(`?%J+?;PfKsa~?AWJljk&A0VyzLHz9vLWrIc$qvb8JRYeSAchz_;8lQkT4SP)nEC<oqi+)I'
    'kdTnq@G2b(u2Ka^d<$4IRB{Z2GX14(uU%y>wM=)ckxw=s6x`)7GuG&)A;=%j4i57$v=rkM$}?i)DapkeO@~uD6<Xlnoy5AzQ%3@C'
    'v2f*$06*+TH0O&j+&xhtQ$Q8~2<;Fr<_r;77byC(%#F<*Jralpj-X<PV4gpT&&pl|$Pm{XSshk+dNwi1@p5K^e8TGY&=JZ3dRq$#'
    'D6tNvv2n7wbwt@6Zn9udYwrk>c;p;a#ZfwRczuG`X`I*=mH9WK0W2V5inxyWDhyGevduZ_Y8kHiqojUZyp#T_Otc_YvN4584R{5p'
    'o3BE@$L+`3Yk_cC7^TGYa)ketEAZGT@ApDdT!y+n1@ANJMl)K0Q?yF5hMjo9R(C7Ofh+&?rExyCyF4|V*O`a}(D53xM&<97MV>ci'
    '+{x#`D*-_6aGa9zFDI9W`J0AyGZec+3H+l<H}tc}5CD1poa>u=RDK5^Fy9*mDn4;E8I7$cY9F5vmU&-7YL%5(+_v?!lCDtuzfRPP'
    '^dSu_Qm|nO;y@{8H1D@MTe=wVQ{-&SD4$IE`;B)z5M&o7wk(CDDDa{4@BczLY^NgD@n017tAXEhzN=RaRIN+1bqv<T#|{-aTm;JE'
    '%vWM_DgQXUxvntpc=`-2Cxm?<Hbe+3I=8dfYJjLl*XP1!e;LT6uj4^yl`zF_uCkN`60hqd3no=F<Z(h72@{y)X;#h?eAd`8@?RcM'
    '!sd+VTQyxfw(({|^hx${G5Ma&gn?6Dq0lKA1(_lLH&v%Y%^ZV31!j2iX(`urddlFb><lH$4VFKIX9i2d#P>>r6GH=H!?VrxCPZ^L'
    '2OK<Q+zE*49Kk~TS(0~4>KTyc(nv{bYG*})*4EFuAA!n=POWIrE#;hpy3|NGVsZf4!NkbsKk(5zGq?{~f1uO$$0wL~G{Hy234L<Z'
    'G?Ce9#bK7GO!%1FTF*a*{90pH!fBPzwN*je;?^kp?M$|V-fz8t0+BFQW9U&bUEl6vvaZ4bw{kaBZrjinc*h3yB%FK7{XKyrgl9^c'
    '1<eZ3nkAIzb#D{=Cii8Wv65H(3Lc_R`<2Ci?MkdNilz9|3VJtOF$CANSG%9f2ZH{h4=Ku98~o!6jjr(wuHSB6yEAcCIOGctXUG*}'
    'U^QFADO&9<`pSptfZ`0y&j6lu2KBQ<|Ci2vt#$DL+k1AH=0D(=ax-O%iclh7z->{Y$*jX{Y>6Xk#t*wc>T$~ImQT`>6<Xe_-Mx9)'
    'd+795b>_dZtf*cImSd$B$Yb^<{~3v@T6#y6jm?gua;?*vdE)v_99-n3*>R|7a7M$3h>;wbhsDwcW$vNO&<GyYN)d7tT+muAniYD6'
    'CB=N^(om%i!pSf47?)S;1^GWSfmPKuFP1Co7zdrC^4=JfUYOW2z9FA`ae`xO1|!-f`x&D5$<Qd-=lcPbR(Kd2`Clxn9aJAO-{glj'
    'iO*}fpfk?iS)y1UbkSfkO!fdVNC|8zeI!j*r1vD4%p=X?U>v&s1_!N5?MG*hJDHBAEUe{}+U35>HmdD?djpw&lk7N9u=|swVLPHT'
    'H{BeO4uqi21JKfupT2SDhOa#IZP;XCIPtBjZ2V}tauQ-isyyB%veD)~>Am{gs^@z=))vnNtJYI!Vds?W^DEM)=%AU}kdR?XH{_nC'
    'Saks*#f_F(ni!QEa%cGJ1cDs4gMXA3dO2_&#C>sY9qcupFVd4E>*%r^ad=927PdAZm7#r4jEP1U_*H&w5|1`gZ;B>oe~4OE)i}jw'
    '6+D-dekcJFHMC4dabPVeiH0}Yb)5gk6wsO}cBvtCdpP5|KAM)inAJ$5t!OLcZHqw*&{X(1wrv7aoZFo846#rC2H$78-`4Ae0p*)b'
    'Og)ZAh-Do;nSQM+g242thkhr^U642r=5=))5U&5>TB0XAr@Y2X@-{yTK)QTuyauOLB}PsPM@e8f$omA}WkFPIQNOuM7b=X$9MkCF'
    'iIQf`;dM0-%NeL*a!A!;DTTXS$YK2%VG);;1637<xn8r;2(A(O;FnuQsXB<g&A7G0=**+b?Z8u`l`QrlVyi|!DC<RnEIVcDGZ0~u'
    '&Wm(NfaJ!-Fcm?3_kV=t(=!Xr7ST--Jda8(Bg~{Jd-|D|e~R+;7^Y@O+OfqIc?_NSvij(Ehv+}6x#c8R{Aw5jbECvB*OIi(WcNUe'
    '1SqginEb|zQC)twdYr8+Pi1Bp%$;%cJVA5yG|r)2RBc{6li9yYe~uGeps)@3Yf$Ap<Bvf)z5VTIXw9PYbq|#IRpt>Q1a8uA?T}F9'
    'RXDgD{-r5f&9$=8;rQa&#MV7n9dH5G7Z@0~g%yFq%3rX$b1A}m1FrVo{mAuE5b>Ku2WKe)<TM@1!wWC?X#%sZ-AZXKi7+2@5N7*k'
    '#Mp&>k#=hv!YT;GbOlaQ6@0lVe%(xqw59QjL+NLGnf;{3W#C`_WVX~?G(}$ZDI!3e7-%x#ji|UJC;YHYM)i+FB*<1f{Ynk7s1;3@'
    '<uB7xQm$==9p9QA)#NJ*dmB<Whp3SHzN<EM<t5t}A~|p!GIrSho3mf!N!qBRU6=X1_p7O(nO)bkXM#YS<1khF%Wn<!Ca*cG?hS}1'
    'gTyOw>>qqV3i*aqy>gU62t#{T{V>cRmti<i)Y*g;4Gr4uxPSA%W^VgU=umpO%%%#0cfQ>2Buj^Ey*yE17+Xn@{-_OKWsvFX+x`%C'
    'Bi>d;tf{@^saF+!x_QFa)G<dvI+@vuj2Z~>o_qBPhrbF*9V`GUY<~wdb$+J{otRqk=MU<e#0S3=4TNHeb=p}J*s;jshRfC)w!f(}'
    'BSs<TGF!Db*uEBYvX^IR8jg5rm-hzQ1F%Mgpb!t|+q`x2QrVRr-W|0)F?(#!@zzDZ;?q}F^4i-Li_TjAtFpF2&!NRb5ropBQJv@Z'
    'RaLFOt1rRFU_do82rSt6BL0<T;a0;o9^vfQ$L0Zqujkmj484y5veU|~Eh+mxCTZ6{WQk_#=52cuQmALS)d=WPwu#h!rNJ~&XBw`d'
    'EulbiG0VBsP(>*|r2I)R)}1cp%&2z!l8RknuJAh7m3$TtW!XW3ZlNk*Ng1@W_AK^*d$v=@Xu<(*Y6wG&?3&p>+3@eX?+pPHJ(RMJ'
    'n-7h~GTG~`{v8l4)T>AJ+0sMg`JJ;Q+#@)00?ll^E*0#Ct%JjKJVN>9SgpzGX<uH8U*^$6__X&3P=|DZ3O=&1I9v35Y?K}fs={%^'
    'mWTmskRJj@B#Xh6<L)6xjk{m@aWH-E%TFqIR&9huDgn9U@yXI=M<);Nk4P6%8YqcLbNh01Hxi2u8P6A@F&Pbo;Mx8tDi*vPN`ry1'
    '_aaNpWIZ{&Ss{_`0m+>N+y=NBs(>@(du-0le{I})sGyu_cYvv`##6rq8iqH^Je{6hy3y_3_I?XrQz|1&VBVxK<utByqd>A&Lavul'
    '?zP2LpDAp{R)SAS4E3mB-&}v35M&*}1S(~+^H$XmtIIHIm3_tGT*ZxPbb86XLXu`Fr}R_dI{s1sWWrS|wny0aoX3uDVt6>I^yx>0'
    'N3uMD`|WK`)^gmy&ro`1uu5xV07;-)ssszQAOpy+<uiOw>Ugi_n3^Sm>ttiNoftr~@A?KoZRObnoFQ2I4R&7_a_?O;>=nl~F$b1p'
    'ry)#@9|$fP#|z}#0OWI*MS{yV(*5Qp@k=ipPP_>Xa2NIl5CWlDm24m(+vEaAxOfcS+R5B#4Vf#LxhSh>A4XvPlMpivn{RoUpIGO-'
    '5VrFkquLM-4-y^9nP7QS?W_djv@6h&iX!(l_#?!FVgrQA6SY%isp6$6vTs*doWaJvw2@On%IuZwD|Np2t!BFVs6A<iiS2MUVBa6%'
    '!*)JdK?0=K>jBZSz$1}b8+>gel^eThsEZrMfjl2ubq4|;Zd|Cg8UhbWv#lR5&bin2A?O?p!vI%dOMAg99WL`2AGCHNvG}E{(U<R7'
    'mWMHog*<QjaH(+6`q2iV&~blI9-*dl7zh<e1JS|F6HIJBM!5L>{CitRGFzDL*5whXFC9>d!q>t{yVf05`X81fB*7AIf|}@HIQNu1'
    't$=TheIC9%K>aTMAJ@C5x7dwKQbl?#?{UoGBqXs}ZxVnF@6AZ_l<ADBD-4gN#_p4UFj2-S(?6PoQW2A-%$ZprM|%Z@n&k`c9x8?#'
    '!SzOaOuxFoW0KL+)|S2E3)$d|WF>xE*@Do+u<z}?%`ih}L^x2|$`>(e*SAsmy10}U<d)8gztdJ}Hs|R`@t&2RBV#MuMm(^#bjluf'
    'r`{xRqrUn9IjAIkOuy!4HQo)4;y08a7T^A!@yEU#3j{xHYwf@DkF~(5Rh70qJrNHTz-6`+?s$<8qVw|=6Yo^tn7Od)-h<d_vG45L'
    'f}XF?O+L((tL%SV`t~07JSAh_8yZe*0X!DPa(^Nstg7RcU=&D62OFdMBUolEbXzguRI|vz*zvqh_Yuz0!KG@$LuMfm0-h?*;K<8~'
    'YgVlLtP9^H$M^MMcH<eyU{txk^N<!ElUrrvVhaKilfB*nhdTamR2F_V#fm2W&=Qe^m>SLc?N=jRA~1v4u1(857BVKeP&{mtL*=}u'
    'r=dR4s_gC%PvnLI??qx2>gUxH=6CgbTT<ZzX$;wxJe9`cW&~Wq>-HUN7{7R9cE{_dT56>r^PNo<G$1H-EDv&+`{-Uvd^!Z!JSn<O'
    '-C!RZgdJ#8f3|F=KiM`{=4QiCb@=OxsmP<|u7i?3Z+u6gfa>d!?xS13w?bhFM4_HTP4@{t(k?4WP617d(rz~Ix)O_aZq~Xn2vy#3'
    'm8o1Mnq?0w$6rL}6<H%sqo<)@2;011T=wiE_)A<i`rMXQN?6U?(X`B5MEzx#A)pR0x}OyAsLhg~7>agO+CLnF{PC{00l$c@WAg!<'
    'pLutWBILIKI02)aTDZN8s#uQrq+~c&pYFI=zclf!*2FQCe-UYt6<Z$!`lr!ymnDN2i3?pi`ACev6KjhfdoH4Gir`+c5<ICYxQ%?n'
    '^0w)MhBvHqWgoR?0zgy0QiFdQt;!8e#Wi#f@?U84U>3Eufm{!=u^x1E>S=fM)8AE}<`8Rj0Q~IEZ`Tl0nKwTFRErOS%w#BOexJtP'
    'x!%X`+bRIs>O_=*D=@xkDxFu@<w9B=xtl66x|8BCJ`@z+ePDa20P@aHqw*JBK;GQnrLA_AbyqI+t@;P(gzg)y>l4haVC!DXU!)&B'
    '^noPiV*zo%d1iM)@|k*?iOcVzvQni#hi|<ptlU}GO5YguptWnKi=I_h$ANm?<reFAr=Zm~O}<3kC27ltZelehS`|~G(uo5FFk7>5'
    'M#81Hy{xaJHer=DOO#n!627R6DyVta(Yp<D_ve~pd7xOoNOvcPF^kKd@dERUT>aHo$cjQ&^ono^dvD=Z6X#HQwjXt0bglt%G+Ta6'
    '!{@;9dSM9k7>-jBMMC%sMDb~{?~V?t`+{x_nIJIc$h^US-R|{E*}mm-xm$B|*ELl&2x|<!ii`=UuI#ZC8EWBDy9YU&kgV9u@^su+'
    'Br*PH?i=WD;p}ObL+dCzfb&cxY}z_qf24E1W{2;2fKIM0JUPO@%X96qS?X<}aOvwAbgt2BK7k=~K*zoRHp5qxpsJDV1@OlrnT3CA'
    't*_nz=51yRtc$W}#QandphxPQM#ba-2LA#`NrWW-mi;9q%8?<T3T64f9oopc!`7c)Uch`8--JPWRl)#|ifJeyR!5Y!wtTfm9^s=3'
    ';q4%ajx<)sU0m-g4$PvF9q=)j$`BS*`+AwYT}k-$p&7i{dXs`AMvkvy!*$wZgex({+aDzz8&7JV(%Y6+M0bAj1kE9hNg`*ySdCo&'
    'j$%&NDz2X2J6cEVT@~YX*Z{*x5JyqH>xI0CQOB!&xW0AciOk&sjxd++7^s7r^KumVYjqm$*yuPPIMH^DGo-%C>4yas4QH{4E|xAr'
    '1B3egCWZj`Z&WAR8m@MzcQQ6s-6M&kfBW&Jvgh<VC#TE2M=(cVEWB6g5lA1iBD46#-erJE&h(F>=KctM$r<p^9Qn>5Ak*OR6K~#y'
    'IE`IQ@@88G@E;r=sV4wfx5+sFq2DL#guWjaQ8}g|;=mSKpR1c<E1cQ?{G5thXLkN1sHGygl)$}e{RpwS$oOeN*QTXXPzuhd!c|ae'
    '0SQ0P;-m&@b_pC$+sg6IXCi86=6Hn{Z#&OLLn^aO6Ftrh2J74iWlNA*@cAD3)tIz9t5R)G-Fz*<mZ0Z`V!hAnLZrZ_I?27)6>QDC'
    'EDG`z>1H39_DD)}?$PN)f=5K<1#<Z3CH>Ws1fJ7g6n@tZn4LkbeE|lR<mim2PEcZ57CY&{RS^4mFr3_$#n#DIFq{d#J+*`?9690a'
    '6<#P{-p8<WSad*w-nd+aO>RnJqBeobKB;e&KCC3S;~HkyrxQY{D*^#E3IoA7$`atO2GQ#b&680)*zTdUM4LHAlM0DWz}CP$g}Oul'
    '3N+STkCi))dObm<Xn@Pb^0Ggs=PlR}Nt0G;WZ#3+^H8PERuJ*rw<I0=+%{V*f*dZL|LUIPI`;5?xi2LW15y3l)WAo3Jn00}VF>K#'
    'ayB3-HQuo4p@q1rEs-#3qp<#YDS_S_DM#nA|HdaTge&D!AFl_<b$OyGROKe7JK}CE(68Ld2A~j8=!Xf2Ss>FsEX1g_5C85>G<iAu'
    'qub5aCof@`;=nbH)C+BpSZ=PLmCpyez=9?7TxBQBtyHi7D<fK~C-+^{*MU<Te=>sHAF%l&T%gtt-<`3;1@Nf?wa>MPNj7{$*K`RF'
    'q|Yd@<x|2HR)yq19igs~neq>C88X9Z7>5+1yuerN<|ZV9yXvLTo|ymm0>E5A+d}I%((aUxyi15M7e1sCg#6IP5urf#Bi2Q{nUo<T'
    '@Mi-pp<zo=b!lx|%@Da~A>nyN_QYQQ<eR-XIsAS-99<WRxZfda0GSi`<JHUrK|gM{g?yhdm5moe1mg9}B=cFNqWxT?MLc7NE<Eer'
    'DmzgBuN_MTHqmBh9P;6&ufxfnfGf3ju5L<pu&L2b_tl3sq%l!P(K2=S!-Vdcaw9dqsnYCFg(<F%<b-uE!vShK-y;`aaEM4(wz@ak'
    'lQ<fUpgLM2KGB7)%^~ioTf3TZj;6<}4A&FCYIW+esWR;WebxvPiCK2u_1YiY^I*>gR1=Sd5$plEeg03)OA6j%<XHRnINNX$QhV$#'
    '!C%-z<dq=&LZ?zuL*Rx0*$dF`F(EgFHYWr-p)|d{e}6=K!b&)a)yUne*S%Y@`{mQTYZ2$Ii<H@npVg0=NR6{~xS!p^!&Rr9fFY1R'
    'ka&_SlmwoP9^>O{3l9@~`Xy}6fNlkI5|0JYJu;=)!^xnGtLI7)IdfBuyrk}Vo@X+KgbSO;_TAn91qa&nNWKIX9U{C$64e&8m$6Qz'
    'L*kHF9e}0ko1Y2xvdwRb3#vi@aL^Fz+DUdU48tuwVX64k?#STlGK_QETL^DxZS`iGNNP%D#3gl{fLq!v(6rmRIGjLlF^nhD`uGUH'
    'T9YdHxQT1=8EbTSR(?r3&{E{p$IQTFv(R+}9VO4_L)prY;B)y4IW3ywAgVKD4IRV3GX$$3IIhE!YN3`R!5kB^e}NOYUCA)1l82#3'
    'BtB?pUE?&2dpjmVNufdK+MFoVb_YQ)A})tZX9wy3*MDLiDTag+D<2g*Gn#iivixBlRAzT75Sm_RVqoQjtR>9x8O4{kKC&uYZfoL-'
    'Gi5mRW!m-<CcND9day3ePxm6;-37Mz`q;%-A$KgCK+#dF>#Om<nX}yf>AV@M<8Y@spI8is?ltf(1oKH_(G6E;jvhqQO3XlejSMkO'
    'Rs<>Ex<db!;>428*%te`0CGUg^)DQp`+M4=cxj2GOhI4MOHwZ@QMxrX;ip;G^m~rWTm`vvYg$*yRNGR=Y)UeE3tF8??2Nj6Y2adQ'
    'T>)WHLcO|65bxl*<ilLpUYwn0pUl#VyUwmtISA8RL4bqGupQP32oWRi^l&q{a=I{MgCh7gv0Q9#_;6ZDxh5XXj?_l`#stxg{BgHz'
    '7RQ7ZNx37EgkT*=Jw~ecz);(*Bpv|3VR>E!6c()mXIpwF1*1Z-CR*Oc26{}04oZjr4T3~|w-~nupGk|*+z@>`loF7}CI7KqQd-+e'
    '*?dE&$;DM`9UwkEkV0!S7}1$>65}gBz83Ff2IT9Qnl-8dC0lK>Hkh5&Qg;Rr>T;y^6yX9rpoYE81)<K8wid7)jN>zfD01Z^d+eS{'
    'Xt`ho2cXJFwvGe9eDY3biMI37#Alhhh}lq%EybIf$Elx%52CWj6ID<bw#zldUZ>kaZH$EYjUJGLgY@fi{(v)&n#-OSX)f4komw(v'
    'C%TT7VfFp%Df<kR<by?_OX*&AaC;-~^}erj02Il)*?UsT8mxI7cro<tS#<1dbOfhZro*a~<Ai~fEx&hevo+ZxZS7`C=jzqexmjlk'
    '6c`t%E#0Y`DLi=?qt2mpY!gJyhHbi&#11@E($Y5|Cmg*HBas~SUkA)9*IzVeL)2}FAn<h1<mRx($6Bt|-K-m6m;NTD6r92YO8%eF'
    '%z~?Mmpp&{Zg59Fi<~epG!arm&KEw+un;|kV9qK^<z4Y)^L_(34?v{%2nG5KKKDD9=~^4;uBK){Us$Ru>3X*n^!3sKaFt|v)oqDd'
    'F5tvsEmr@O$(P(Jp?+F_ZZ|GlkvYI2{YrBo(u5JU=rcjD-|||`&rOo<6*F<%Y#z=@&+2>oC?dUjkk%w_3pC23Yc4VfcfBPM(fndB'
    '8(eUfWU#T+&Z4XW$Dj^4dB)Aoh@XrzzvBF7xpz?h0LhuVan0V_*RQmvTo-ufQ;c(_6QAb6=JlNU)qlt$7JKXYB?aMl=GQ9`B8{j1'
    'qoUDqn-rt}G^YXyh=Nyrv=5Rfcbw=LP`I07+It_RQ?gnlWkY^&aMiBJ;}cnzW=qXuBa!f?JLwL_8^3fm5}Vd@U7~_J?ydtr=-O&q'
    '>C8f=E}q5lZ2Se3mERlZ<18$WNdOhB3f--1V_Ljf{_Q6+#u1@po{s)Q8--F6r}rB~)c`SkQAjEG@orJ_sKFM9tFrji(=X_*Omg7y'
    'v=<Ek_?_9R&gNG)8_b4tD^<e)%{9S|{(cr(8x-Yq8=?K8Ut+nU#RS!g#vdv5?m4&?rU3w?+q5+_&j9tJ+JcO21Ic}*?-;N$6AKk6'
    'P-Jk!*yG!ZHf&qUZzI<B7Z1;ml{p61ih#M3r2;WLhzg!)Quqoc(|<5KCX(5i;?3=3^(rJ~d8BeX*i1PoJ)QDi<U>YFZ(;&#ahlwo'
    'OKe4>YiAqx{*KLjDBN;=yIpDxMa4d@^=Mf3D6cCo1nb7BUUHJ63Q(!5q+K04KXm(05FayPT#ky{^~DE(vVLNQT(~QY?xc=i?-|t1'
    'Lscxc(eQrgF>2Jki}#Ude2_{<k_Ei@gzuK+){TY3x6L)7KwC{oOc@)Piau)_WJi@c?>_a_7ytoZIknaL>$?+V2k3o2r#Rkqd894m'
    '#j-&3aRn>#AeEhZ33pD#Bn}NmciVufb80rwDZTi}fxM3<6n^q!4<P*cqo2jQT;_e3mnjSdcZrM3sIl<}2s^!w>IFV{w<agH9xTM%'
    '`A5~n5#KZIJd69`?)aP|k6G;>>4QDMM}0W)%YmUCqLueEEB@f;L(T}Mx2MEI5RmD_<m|d7bd9CX-VY^(Z>W0N1sLL<b{)kmhI^3('
    '^SGX@c9|~O@1#L057_Vt6^HkX;w&s?a!wF;;JU2LK1?xB{vWZ%J>|iL7$|}*m1{JQ=e`HBuP<n=-VVFoL!_;zAsZ3%VAcJml@+xk'
    '9yYi#$Rb7MNlV#V%oDRrly$3fBYUYet|Yv-7mNI^Q!Sb#c4@#p{xw&D+ftq=<8kqfXSFk-g);hE)MwyB%<rFde9<0Z3mT@v4d(0w'
    'o2tj_he#6+k!Fqn)lyrcWI?c_jkPiZA?<p6B`)x0@tzcfpiXhG08!+cCwP2k`3R1k2&&U0#JjImMba}OYqNU`*@k_C<~kg94PLlm'
    'F#tV^^{R3Yx_WhD>If`4+S5KL0RgOZo^3t^eFzwVm|u8J=3nc`L-@Q<gDlmJCZhutW{A?!0Tr-Vu+KSK>UBYLB*F5_kFRnwZ5gHN'
    'cmgOH+M`dIOh1}na|&fbX={{i3E8M{ZMf`O!b8E0#aB1~o2#!W!3s&9L87G^tLvxGdr+`z<-Ry5Zs~)2AO*fRvbl!03-E7Oa!u!3'
    '3Zti;KbVdSFraL|=KjqAck0y#dQ{D>J3uG#JOp=1%Ek6lgSAEeQ7H?D)Iqo=n<1OM+=4<5FnJA&SD0+JAbtZNyrv}6ofQ{mA<c7e'
    'h(&McfsxlD1DHkW<7V(W<syg!UK3MfJ6B9KA2{Nk$vuO2+!K$vYw;ng(u%9-(OH`vg<O)np1m9xoRc?>czCQl6ppIxfGFvZTZd`o'
    '^_N`65^)9hBfRTg$sx;p>Myg#ZnP$>Fh4`HwDNnVkLRrwWEH+-+Hh~ujv-<FH)8VO1hQU6Z^vF2U5r{onJ3S*rPfVF1aO#ZhjYib'
    'fkIGl12=!VHi}O}uYXSt^|!n9dbH$XCE*s|QWcL^;;b@ASS!Kjsc|yMBsQE={D-0eKPAf5-uz$Q>V(-CT;-JX0EEU!%BZ?0EEh#!'
    '*LnWgz+)}Jzr%p6PrZYqihWexU8yr38iD1vRW=^t24?Ta#Q7z2R^>RTx;dKJ$o1^YDOaM5?EcYeW<4f7O@~JwcBr+q;)m7YxkVE}'
    'kac!lH+j6=F|_BAY?T^bOQ3{;)5Q6z;V6OgGWndMgPJQ!!zsJA_!!F#2KS{X2&}0)+*m6x&fyI!2XR-Qj}rnt#VHDJ`~n;IeQ#EA'
    ';94aos|9k0Ta@ce!p2@foTMXL1Rkd)Ax61Ui1y7>XrblH{GonO@o<JZ7!$5hqm~dlZZ*?wV1Um0NU#c)Pi89QNj-NsGpZvQ-nspN'
    'FFkG?NlX=iJnV5fuzoWSI#M;xuu6U+7%yx8jj)cqN5F5feP34d-1hU9vks;ypnAMZG4=IKq{PRG!#1d*OE+EVGD(^Jj<Fu?S}@N`'
    'VYJmx*499m@1!-t2Qra~io~*r54)68fM3wl&AxQ@n3jlZZVOraNFsT5P9}3Q>(-v=Suip%w3JWJPqYFl<%tbD%wedng{iIg$Z0`@'
    'd~1sX)`wLkfKTPFH-t?5pH&jhI>Wd3t%S%3K_Z0es64pcXkEVK#HFzhF1g!$Z$pWDsau`ygvpm8)|xwlBEREiZbC*oMxC0HQaYEx'
    'IBldrb}b8A8pL)G2hRq^a#=Of27gY;b-#FU4>epx9&t_ytIW`TRXUFc$=IVsbQMFybZ0tA@(24QrS@~hKABOfw}@Lp#AELtu`WGO'
    '>A4AfFmIjHYUF1+5DD+Y-*~R}IKk|XKWFWBJ>3!>Tesioo@cak5s4}xHF&Kh|H3SZQn{<1C}lPQrG?bp;g>OKmF8reUaI*QTef>G'
    ';zpYMqvU4s98l7-4UZrL=~TS&iGCtgA|Z14bYEhb<Q{PWBf#NUP$-lXwBX(UjyGevzX<}l&NYr<D0Z1umeRT1gQ$yy;LO6L1fT??'
    'UU(x@{~L^Yh2$LRv$9EM3lCFgVCa&;>LyP3kav(diyUXt4LtVN!1RkXJrz6R9x48tx=b0J0BbE2V5A<(WmQzHYjTBYusq|}$(e9|'
    'p;_G!F%(l{iQl(yLQsms<o;KH4p6v08~nc(Y1)8Vs7xf=pL^F-jm>!9c>A+i7ssVY9r$no9asrEQpT$>pgaH4I`uwV=6FUDC!eUl'
    'eb-DK{{8e-(<lu$1h4rPKy1g_!%5c!ljk&;3_h&vFzlb`{A@THsi9dz9t(q3g;Oo0Tj{-B%K%G2#uHoBh%TDelIjpz!<U}q0yKg('
    '(K+#}K8Qt+JNshV{2oo|qSE+ijvSbVFJ46^0_GmOpGV6x1J6Cg-0T2U{6RZKX_;WY2<(G^JZAIExe5Zc{7d)i61mM32E0Lo${=u)'
    'Co9Nsn`~C<JfPbq6aJC>lmZ%skm}SyqgChrM!KiQw*Nkjzw6X}1Y8+g4RPs`b@OL|3j%VO(I`<>zgE={VxVqfEWixoL}{?8Svmrq'
    'OdoO4w{&XW9K<rR8Us**&n3!R0`n%onDk7VQC4kcq%A~=jb|Z}PS0zj7_bnliJr+yBzt}K98$rl74tJJ2O1SB%n|?^qpIJ>K2d3w'
    '!C%)UV_jWzsV>C@NR)Ups{Fmc#D|~A40?rwq}&OjHr|rX)NpQ<v0{D`tIK#k%G;8h6>Ij*T+_P6(%Vu71uhDB%=4kjc{B3o-AR1U'
    '!1yxF?c#=TTC4)JS(#Vx1ARW3xQflhM`N)yxpQx<5uKaqFcr-I=$z~8F}C7xvHip{Y!|gtBo+%#Z>sQyrs%vB9o3%P2Lj56w$w1I'
    'nQ2K+3doCM4Lo#0yDS3CE#|hv=|$Qp3;6&K!S~#~b>(}AD966!&DIM1!{OAo=ujdv{>k8SnpKPP?{uHrf-J>Fhx_QT;|@`f@j<KA'
    '^q$idCH$oNI4x`(*ZLsBvF%H--Lsi6Yi+SQHBx75Vly|?Ydsq3DMs;6vWV9(w<~H{@fTx=(gsv!Ye5<j0Hjvq&R)d-4!Jg-gD9TU'
    'URu6}Zy5yrYmlyjm$@M#<yc7yb3;XLrm#EweRx)~HVgib(sSHNl<}-ijh=+fOwdj84h_j&=tXb9UrV{gRII3>Uf|UL68d?S<swdJ'
    'YOl$!Jy0N-<X4Y7$GVT|Ivh3`pL*7?u^l5bzF^dT7$H`FdI{@FNC-T8=699u)8CLDiMpKB_D(uq4}icY!{>oqv*B=BVs$q(GaB#e'
    '?h-s-tCUS^3w=-^dpb(tty?oQfofeD?ktU~$NIug7)jB1+Ck#>vnkdE<TZf?jieFyu?vN|Q;2!v6DcZ?8HNj5@#D48J&<X_^=l01'
    '{N+%J(Y<MQ&nNY(EZ<nTjhFW~bu890Ff)bSb1bybx1osWHhPl&qp!2#Dt(IX(*nNAw@mIOH+qM4XT}H9P#dXAONr^DKEd{>1^C$n'
    'Pn~%05Bwe;mC|R@OF&o%59dsGa=LJ9IH^>|3*q?-XeZZj+B%(R<&1dbCIpkZ+#fC;7j32S-$?=q!0T>qyLq<r+2D0J_N<ooLk<CK'
    '>=yMU)ay_G$Qo&j_scRK{WtQt@ky%Ge>S0AE4At~Y-HAYe_n^M^S^4&$g~+4+*o6rS!iE1bJ8>iV7b=uw9G>><neCi?BilQh}e{E'
    '%gSKW92@((9FuP68+^&>M8U1dPODXm*<Vj}i|eC5;p^6__T$JU(Kp}xT_ec#(KiX)C9;`>{U)2bq_Ei(zsULSJN$jUPJt4Iu>_XU'
    'eO3gEH3x7ay13Xj#?&IKeFJ+8#hcSOE~AluM`wA{^=Dc(Z=EADhSqPRUm9x-kI`MeL0ww$&h&~r#Hubu=`V6~qWL>KqNt8d9?Vj*'
    '+Bv%hX03?Vp3K9ss=>Pj4%^n98aeur;Gx<o6x!ANDqt`N{B4m(iZd0dBOnw0Z%qnv!$!Mc=5{AD5V7==wpk*a&9cx=Kh5Uq;TAZ)'
    '&o1D9oP4~(<|Kz&=n4zLlmr(a0UuEVgd<vyeRbmXzp=i=S;oKSbG-bhX5Z*t@S%Yviz0-ucUqp(mI`DeJgJ=|kjdtyR#M{wi_`z6'
    '*p-hD3DP>xKw0)+LW_N=YVr);H?<$_9h%SytSta1rD7nc6`4v_PxWm-SC^9&W;o_5j_<bqa*BmM2sYX~Oy);gh2nsFl7R8kWj@AP'
    'jMi;Kk0A`SVph~mDe$WPrv^ArbYkl56P_oY*vB;rFuRGjmP90pGgdmpD#&K~JdstIaM?xS#*w~{5Sk*>ob;WCraGkH+w-ACOR8T%'
    'A8_FT>oM4$erdI%Ip>1%I7F_ucLEG-EM5%SWzx{;(}7()^*v*)kFkq$>(K;1F|?Gpja69`^>QJcFgMa?XfRg}SI)V1|3kX8*QetP'
    'a&`=$XJVdGt*K6$q$%-KNcL41^18SJ&wpttsl+T7?%tzJw+gSZ5ImhmyR|qpPE!7>rl^%$n6rs|U7NX*d=@oG)KmQq7WJTAhx6O8'
    '5_#)NdP`xfSt0mqIcz^LoUdx5iC$+~=|T4?>7HM=w_V{8gcRI8UwtsxJw(m*Woq9f!+~J)f)Sbk5$zqzL>sn)O0gZo*Nx_}V2?uV'
    'f!(g<wo|No+DupjuDZ#OoM(MsND?_0gpe9{wrW-R<nmg0skl!ZMcs&%gj)5wTd?YP*jV*C|KBb|qwr7RQt^=!1p-wH=&{MmJZYF-'
    'RzfHA{n6%Engy2va^II~pk}F8y#I}omW31pvFu`<!rd&JLiS)X7p1>x*hJh%5pRm<M~&nDKk*UA&-Sw;mgZW1&KR>84xM@+#U-UP'
    'kO-cCCTBEO*k{wyK3&6q6Kou$Am{xr?_aDOL9caVC>}kod9&4&Vu}orPu6k#XcU4qqvCX}jW%dLQ|<rMJi8^;^rtG}Tfs(6VOGec'
    'nm)Wo59XnAl-h-}F_xFIY_Y{yNmnEW722%V5*U{l*c=aYG5Q<^vH*!C{`KDJY%q@|{5IG*50xMI=rwap{fjsp1ff)$$}GMlmt(db'
    'DTDYMmu-z$iQvpfeiBy0hf;xsorA;RIXoqkrLs1XmxZ9NyT~j4lYFVsSN=Z@XtF(L0`PJeBE}`(NiA=UH~s>jr5?@>Ikiqsm<Qmc'
    '6Nc2Au+|+;J?fk3t8wUnmre9gQfMiBy>Y&<eC36M(ul#j%?S>L2SbkjPt?SFV?&XDm&<fBl+5{kxrbq<H4Q`b3@nOhHp6gu_h$`('
    'W<Nf<QcE#Qe1r3Ts-I0@3}l-k%P&I^9XRCMobO1Pg}nLic8d0VHgAR{DA0+F+}HNtt7mSwy!12O!k0nSp&%RU#^&JfNYP!C=t?pP'
    '-o{~D0jV6CCg}bzM^(%@cP+c-19wrXxfYQx2&f-k;T5H3A^)aKJ=Ndy-IgY-Ggo$WbOT~e<Plwip3P7KYJX}YBrqQ+tx80}5<1eh'
    'JtB0ZT$E!$e3LxiG@e2}eY+d}_2Gs%62=6_gc3gB8;vPj87Wb_8%ZGBplH@~YT4j7S=JV_h4y3iK-G1!Eof2lv_nR^q+9p8T2nGH'
    'o~}w_wsHbM6pmxc`yG(nXTtCSmZ-`K#@f@hMlm>7Kt5QiQ15K)jz0pSObj4SP?~8Ln*}d=BB9X;1BOAsv(2@JuU{@ePLJ@xN(vR*'
    'UIur(n_T)MMA+3^S!Y)uwbRy>4!gQh`RRp#Dp3ak7Nj=phVLsHmxQxfj+>!9id{_za8h&q=CpBlQ}Gihalc8h28lR~I>7Yr3qo{T'
    '`k=NFcg~43;;@R+(->73H#9rT0q|3+_<%0xAWw3R`MLiJq58V9&5*C~0N#zu?hU3!ZGz1wdHYICO)3=J?$|{CCwfJ=JQ~AV%!!IW'
    'Qi)yyJAzAHrjSr!2ao@%R&(m5|L^o22{#Fx>g?Bd1BB@{52xZ}0cC68g-xg#ZURQ!=B>sh@v`F?6!ZB)sxgI=fjXfobC%r_a25|#'
    '<Z%FY|FTgXVyPElRDaT+SzOBQs_3r{=ygz^gC8)V>38265!0*!ADBA7k&T^}&!pgOoR$}otMwb`QM4y)X1_+PtV8@}w5+C($!kmX'
    'UG)414y4q!N0oV>!6<Ec4C*uo8J9opINTVtW~q%G{)w;vuH!$sQACqm^aZN|G4GE<^&=&mXf+o<_hH*<4p`d<tac`r{rT(Z4$_-<'
    'RB%)R0Sqr>)T8VW8Ql}1jc+{TNw%mGhsbrjTRQ7(8}VXDBs}Vm;oZl(Tk7HX3~3|s>p(b<{48N^z(!GjtMx;5t;At<vX&kFbBEG^'
    'yCzY^21%&J*B0!@cF=89Hfxe{W;5+F>oVW!;L>7%U6EjQZ4vkxs2TAjsj$a;b4r4U&dURIb>yU6TbiM2EmmvX)^OfYOHt`+h1uB('
    '3vyldJs<5MC6BIUtrtbJK3G0CIQF=tl$Ev|UZ*oaB#<yt7sxRE!Uj;k<wa{I@R?At5r#}9!mZ%UuvT@<3h{E1Us|-IxbKVG{}no$'
    '<Wg+h>RN^Aun$ud<t$It8X$OV-Z__Cb;(~8cY$i>TrpD+8V)`5Efh(b^8yDpr*sUyMg`}$6Wmy}!DvoaUphL#-*%*mai}y$Gxuwp'
    'me%tZ7Pq(GLJQ{;c%lnsBp%`_YsYQ*noxW)C||arfq1ru+^blpvP~alnlb7x)huomKQeY1*x0tXZRCaB5Eehc{CI02(+bV9)dN1r'
    'cYZ13>A`9(KAwHrA0;m=`fWl5Z_m%+9AtDuC#-wpB!M*l@3S`?>OCU#bdv~r(aoZ<O_t2y88x&fgaf*q*x=sOpbjY9n1F0d>7oAs'
    '+qKU=jVbxKn<z`f{~NJ!Yn8kAHyN1szwl{)o8$DGG;n#vd`}Q*J`{h!J0223%2Op6MvzcnVkyl(jsJ)xKLr?rcBixGy()(rA7XD+'
    'c1BMQ&4juiW{5P!_NTbNhVT;aBb%9=7S*m}KR~*fSagZNI7k$zy_=}3R+wAtO-_3XTA$O~Mb-m@asZ8rwS^w_6|GkYD(azd1jsPw'
    'q=DB@Vre8dC(G-U9$2~tz<0e76;VO3#Lmpm)JP^Flx4+Z{@zsM&LhnReZFT(AT{R%#uSd%8YLfVM2)TYRbuT0{qBV}V9lc!0DfGm'
    '4oevRglo#kbNlM1kP>lqQwWRAvlm^CA?Dd>W{W@6{9DKiuLw+dOizdVlBr=%aG2`v@i<-v6(}eQ7ouecVAk=)TH#L~+%@%axY&{2'
    'y>*aGRpr<BxVcNE8}?XKpTfFFauKh>un=#&6O59ZN?#d2h#*k#t8DGF^4%nruCAvonOE1p%_7&2k?ZZ<YD{nYT%7ZxEo8_avqmnX'
    '(ddS<hKzYO?N{?V=TN`wgPPY-CyPxMM(MU_C7&Hormcuu!A(8$4$CADx{IfY56vg}bcXU94zJMMQR5T=5pi__hLbLf*vd<C`oGWg'
    '5A?vSh)cI`P5PHO$lTA+LST3|&6<Y+{eup5LQLR3?U-t*U(X2pKbuS1>W%Z4;Vpvyf}4cR)66`eJT&HGTf{>cUr=@rtfOLH`oG>Y'
    'd?kh1_kMcG5XegnHoe}uWSOg`#uw(cJL!v3t`mni5Be9b-EPx}NWWnNj^GlZ7_##an<N%SWY1XAJi@MDcy{X)XQTg6O(CO3=iu=v'
    '#C-mkT_%}J`FpPHTrC=%X)LHXl}85m9`)OHI+1UVWs~U7Qn;8Y5TWZ6C2Ie|UVxcS5%7LkU7r2*!|VOq=>bF-JqC-w;@vS$b`Y=)'
    'SX<(bJ7w2ckP+m><uplFsRQ~HQoUxEEjdVIwJ$&v?SG7z>Kk$&&$tGoiyd6)?Kg+Kc^gWadmVz6678kms=O|E&ICm515wH1qV6uo'
    'x-g;bz&aH&Q`r9%AiCAURwTzRNHSNj>ZWIWk$um7EFo`Q1s%=KjiRxQjL{fAjW8i9E2$#rK4UY?aZIInrB@_!2IVc}ZWar;vc+H`'
    '>7aM6u3+`$%`X(liey!|N+psGeaOiN!_!*!umg?j#`&T9t9r}^RM^?7kiJVh>_&3j9C~|GqbPQ>3sPuc`ZJfeGc^lp`>@w81+lqB'
    'n7Z4j%IB8-q<#nb{G|#;gNT$OH<5;32l2SPntY_9&)izra3eZT-EUMPeG{`Z>NcTixQ;<d9P&g!qb4QoSme+a9rE%X<|2voIeV#U'
    'S@L{pFU4We<$WNf{jt6G$78;;GA8Y{pBb;{(=@TZ=p(caTWvE`6g3dRs80<*6m1G)L?Mls68jY~jG!qbo68Mzy3hIa?fV@Ymom8H'
    '^nnJa<H~dhSFD~XK97JR#_5sjv;TM1=#%atF9%@xr!FaKpllE6g_+nF8YUG~O`nDyYFFf^tFdwqThiA+Pki6+oYLt>EB;}wtp-p6'
    'Rx`uLcXykNOZ8n|@;V|~|IK$I;zD25_jaHjlO)>1NcCWf9}Mg`eg9A?WvNf!Kd_n^=30HDwDa%;is^_8XB6j=X<}-FX_XXNr2<wF'
    'sNVagkRIIgDn4G_%I%|kK)7ifZ3a6UeciE|-%1na)FCup-UM%NTtGv&ypI+qrXl$gJ;nZw&hD%46ud2S@*|$;%j*`UA_X6A`H_!Q'
    'zoLgpZ+7aDpRH3ctr`8r4G#KT0&_^XP5;{_%R*!8U{2SaFFvX6K~^f!D(3bTafiO%f5<7}fB?R2`Jnt(`HJDUY9uNhrR;{{(4Mci'
    '-x4Q0uLLn**pUSC`B`*$_cU=WD<BjLHI^1i48L3?7TjsY@T1wgpzxkjA2y@7Eqsa{>6xfQ<Sw4wx!Latbe}(RWJfV@B^9BP(Brsv'
    'Gmq6sq`EdLnfgA9!<Z<KMx=l&XXCtE<!8b3;sP2$e)}2rQhsRDi-|D2-R=pq={MZdHM{r+x_vIbZP%@ryMP<Fcq6CB6=<)B<J?xj'
    'm21><5{wQHb8p~sR`f69G=$E{IE1!(3T@U{&2w!qoXI9yHKJZ#%;!Z$HX~j>fKAZJM+Nf7$qh!ITejEK)rJiMaVH(~k#-&DkmwA^'
    'G~XUg-%LuPy8)ZuYK~--xTFQXNb~KnP=FrVXNg*wsg(6@Pa#yYOfl4~1}=8C+9!c0Dqc4w0wo=p|L6;xTE?Uu-%7jFC|jb0T9R*h'
    '0`yt_nxL*?i~nJscwqRCrz~ygMUD8+SNxLq^zxAW+<4O9dN$x>^|vsgrfo-0nznV+*UAFLLG8VI`z;`Lxde`4NX)BL|0jD!Pg4;a'
    '6UGC$PK!C}G*fr60ftna9l@611f(uiF9Wtymg91!;;!O7sc+sA&NHJ?&scXwy>(mGAE`1|_>|2Wa(de4fohMCnSzpx9;>*e1ugY`'
    '(2)~sO%v5vA_lUpnHKctpA;MjfTCt<J?d`6cz)|ts~pObsCfVWW+KRo&G8<9q^_5uD(2D?TJ&X-ZjiB&8N3xpg~bS0_;~`muys&o'
    '%h>J$*LMWRpu^Vm%w>WnUL?(EuF4{MgS~nA0icY-tnVeK`V{$}lh%})nN6X%=H&yt?u#yUtNu%nUl;)f|6Vgw7!!!uPQA~DEqQ-2'
    'L4wTP(Ti#LmiQ;*!OBCPV5WGfjOr7O5duK^O$WXJQ&~dFZH{wKwd(g~rQV?q+WnZ*p*VWJ7Yhympga8WZ*Zq8JT!2~h6s}c_fD12'
    'PHY0RvY>@_k(uq^`<stmG6L*p3m8RyV0mY1h-i6kb@!IQ$5im<5hHI$*)$V?$Cv69;t{LQTrjVv?dHr_ifieCn|!dpIk)i}sUH!y'
    'ri3~Io}tuiQ+VxLC=}fAWRap6)Cmj_T6nDzZf?Wm<NQwq*WrDNqfU3E$(5>VwFAq*h9ni^KcKChoMe5kKy}7*G_LO=DR1`?9Do}b'
    'W2i}|DtdI17pE!W=_?x|D*lkYd$8RT(w`DzFh;$$51?`ME0;T4?o=j}z6NJzI?sV8aKkrb27RMpUiiP|O~}%JS%ueg+%H~*^|#_*'
    'y3t1UMgx*QLGjH1dNv?Ce#~B-A}c`rBc^8Z+<6|7<^%Cjkb9#3oVT=5i4Lyylc+_Wm{W`)QlyBr2NY;$z3g%I)D76!(9q(jt#xPZ'
    'yB#Np(Nu$nH9!|VaRk%%@a9iAL0wTf!afmVRL|x?Fia^bGofX4M<6KbgU7r?Qvb1)7Jk~3mR3T8T))QYlZHfEiQV_DzH(ktk&F#J'
    '%Tyt&-qOf6#zlQ54jRwe>|Etzh$*BFi5^Pc$6x>U6_K`Wr*Z1d7t8N5-$l<_jcuHGzDGv1c+=;`NjUpPm;ysvOI19)5N>r;x-`=Q'
    'W2If*7Horq2aT3#L-B}{iNZFC(8j85`WnXj7=zO_u>+Ivd15gr`~5~HFX`cE9*q6ezw_N%?5$hCCrzVs1$HK_eASbyRyTiJEBBR#'
    'QxbhxDSi0WZ`4^pze^PDVC0`6oag%F8KH+W54wKzXI{ruHE`2-AF~=?NeTX0rjYsyI7nj=$T2gV8dL|d>ZJ;HQ>{8H;XR2e=p`Cx'
    '2KfExX{LyTkMmY+GkjFT*Bl|4qVbaP1JIHF1!HRPg#+PwnR6Mt_O!T_5)84}0QB}y;0nU7Mo-RsXa=w?#O4@7SYLwTNsJq7uC<Sm'
    '=*=W+JQzRc+MCH*qnq@>no)dKqo{cljlL|Pu^@0=<DY#!c!af2MVs_j$s^=60$}Wl9hpi7tAXmKc*H{g-k}Z1TWI0BVcRjk*9)eK'
    'pNEZrWBW)J!!(7HxVkH}v_zDFzW8ZEY#YsnCUA=q{5!?V*jea!>-4qxSs~R~?cCi$+eeeD0;X>DrOL=XDy4@;`hsm`EQ8<%n84~O'
    '=fDzVN56}bPCS1+YO^FO#~BH*1qF!uCl)E%db>b~K8{wtadGd7*iZ5{Y=J`HFX~@26E+rW2W!@Ak#87J**~PPk<a!6Mv=Sl=2|~s'
    'g?Px+_sgy0UeGj}Z`b#X0>Lc=8lmAqP~NEUICnI(ec9O4P-IE~?ZxBSkZ_ifv&@poSv?$2uueHds>5kHp)Rnjeiq|yCa=0)B_v7`'
    'g&U+VepC5fa45GO$%ADj{%ueRfMz>t!gu-=|5TJepk2z7@~)LShCg;@HCtC|`t-!g)IZMOtUeLgt(Eq<jRuZtAom!@)S%++F^mjr'
    'lL1~^q9*KgRhOObB)q<5Va_s@j-pkJVOy33ZpHm4Z)pUl;3G*hrz`Y%%?_c}OC%f=sYv8GHu^Km=gv-I`936T4je@a@Qr<JSc`sE'
    'A$tX(1bs%L3ofqpHYa(@211cA88f!z%pH3Hd|)(slp`qB+ZV;+gQW(R*9RrPxK`$lQL}z09bBIp&oOwJUasxo@^dCe>P0dX=6cp='
    'O0$W=PHnd`rO$bI-=m8VfgUJNHmmpooVgEd;S}%}VC~5hcGfD}%q=R5`57;vP7m2t$gKy<U-Knvzu0G8kCb`KY7*5uEXxUw8Pl<i'
    'jsj7<n%m7CR0P$|j-LMYF1Bx&Fzb0EINPlEjpQ2$*4+k=ukk++bl-=#0pyGsl_%z}@61+~IOA4lGDt{`R|m^gf0GWx_~+iYXcO#9'
    'Zg!KW^)GTXa(Y<K;G5p&;c4sM$9$VC!9iOoSK|b|6r@2D2`t$WI3D6fF2AT^@k9EAvCnVhw~haN&8mIzUMjy-QvWOS7AT&A=2GGd'
    'D{(<{#$|@hSQ1SMay1w-F>3})(sNb&!hDpbzlJr_*Z6+{k1mUlzDvSqQX4Cii9pLLJY-0PkNZ+ql2*cy1!|4LBi=nmGMrMc=-enN'
    'kWE`yn{XYYH~V9Y{xgBoPsOX?Zk5g$N>~%nfYj`MRT3c>1#%`rc&Fvv*n5Vwi~EBvT5fU`od$vF6%$@mOY;VNXKb^Y<eB&g&7OJ='
    'XUXfK14OA?YoO>YwlwP~s#Co6`>p)_gj>Ht@`;$%aDMpGg$lCk5wn>!u;1(mY~GLc{!0YiYD){YGL+`|7~%vgrK%#}=~5RI_80d#'
    '5}45tg+)?Ev}(6<3Nt3_Y5FJxnn`@%p_M<RANU*$*r#+`|ER|xx%}4+s#9kvj<-f6`%2y*tI-CAh3;`wjX@D*4P`}zt)Nb(U<D=n'
    'Z3xzfoA@a}5K*rur?}mR8DfY}%0@GI^j?lEF{#xXm>qH$J*nWRU@hd%!W3GN)~VzAO`Mp$OtXjo5GwUm8iw2qfxboH4ad3dCk9Pt'
    '5gh#T=C@UeA4V~-$Itr@I<_Kp@d+(A-*WhYqG$i>EI_)<sA<#$3lR#EM^eg6M4+r_buXeE(4eL3MpzW1nhYho1Fc`k&1ZCHRY$l3'
    '^IT^caVKOxODN$isn1{g;^Mm&FL1zAW9&{tm~N_x-2N&~u)?Mnc02bD(n+ZEZ8^t1e5P}Vla7z>miW>_R#$D|%lj^^EE~hTinf1#'
    'TQR_9M@MEokT+Lk@W;?(JmvQ#te2{}DEH7t=sTLG01#$!MZjtVmiLWHxUG!C>zSI-rv8@#&!M3~eBxN9D=(RbJFBUtT@RWzlkD8y'
    't7D!7L}?Fy@r@~Cd{|Rkn`BUdL!)ZjaeNBp%dZ7SriG9>Z42LF)FH|CO!X6(!L38~i7{zAjoS?Y(`j1uw`iXB5)&RH<Kp8VP#o^u'
    'Wc*;hLRL5175Y>!8T=qaBs~{Q0AxLET6W9Ut0`;L^Vit*KfsZDs9+0Fe`*x?hjhrrw*@N$=!b*mux0K_bA|(o`mgajcxN~_qw3uS'
    'gdbQ1QR8m-G)9Vo5$)@jDd;yttN3rV-g4qgY28@{pKzF{ROHJn=z}xhPl~}aG<7Z%Jv2|~%G#E`){28o_YeVm(50(!&1|7zSFs#`'
    'RG3Rf&o0G$d$`R9LSAuNza-Hw*z66RL5}hi!8SG;ssOG^`?}0ogl4==^x;svieO`F!V-Y)5{+EHpCr-r6gp+{qlit+T(9AKOnQ#?'
    '`$Ob%x+8+$Dy<TL5F-MGO}s;=96oxI<E9WeA4l>MXy)L<SrFAz3*D#vw?Ggc$!<z;mA(56tMwXa^XKSq8}bnx{e)JX0jPea)5b}3'
    'N~5gavGS~zpV1ELR3|YHN=UUxaCg&A_5<L@QB4-&n5aEB@bD*j+<t9Z2aJ|8<!=X!?tqDBAa3<&N&gwCJ{{0tkOzV-h`OQd&xkn?'
    'yzMewPUSfob*hG~d&H{v7yPSaj0#$XZO$8c6=Bx?iH%0>ZdlQQ%y5Nk(zUjJoo(Yl+_nkKRsnQQV|?_q$y}}tpA<8TGn@votomh<'
    'gRJ6W32+-7oO^2Q6ve4r#GL6=Pgj{93)LZ(3#dM29e^~Kh5R~3zmFM(XC@B<#b7ky$wD}(yIjvzpmKp_BgF_}ph%%T(+xC|$Tn~U'
    'Q>^-*wux^mKs_gVoLcl`;Cs9_{OOCVuaz5D@w$(1y?P8x^i3q~uF7@nar3~`oKtmHb+UjL5PADJH7%d7gyqMCe~u#U)#lX%AXCpf'
    '1ruKd6iNjqjNy84t!3L$uhxf=dDmg((98>GCq2@pvjC*9w=Z21!rp~nP<7GFz52@ma|R9YV7VCIwyf=-FiseL>3GaRYL$iTPek0a'
    'UAGZ)q&XjhteB4%z4jqQW1_Z*-H(~-2Vce>&$a#>=g7}a`y;CJ)ww4SjKDO*Z$(@pQtn8o80HqR)vYDgRJx6J!=#6Z*z>#DPCwd<'
    'T4I1OkzSFM9NQ&iO^5S4bR1dGUCsxMr8QWlm<$A)oyJ{J9CSoVJ6|-A78{GQHBNrK20;wyHtGBJ)3Ajh&%XQOrYhZ<TNU%Te7*Yw'
    'TuY6jApm7aeaK*mA}<kszi7l_7TfZ~un>)E+%AU;ve>x?%$jDGd3zTtVBW+_AgKfuW>*@T9Ar~PyHhIqlwifPQc>e8H_Knb%vYsF'
    'L)wVrU$qm3%lS2N#YBy?R`XvIVMIz(<V+aVl20~0j3-PZ|5*G2YI$m9DF>?Sew!orCt&?hxmlSWF0gAV-0-L)0M6Byrel{Nb)64F'
    'b(Elo{o9BTUnUI+TC^j8kR!B0ODU$co=<^bq`f+ty>1$b;F?^E42gLDS|>VQ8oOF64bnt{jrAi+3s&CnS+cw@i)-dgbZ5Ux#0YL&'
    'H{0by;1Wp*!g)XX;An~W)n2oD%aSZKxZaTRKnLB5JjMptrh2JMH{)EZLVfs|iedpBN^q&qVf0arIaefQ-{h`<g<ca0U8D4Z;j`IM'
    'K?Gc<*8Lj331o$Z5$O#1<=dAnIRRE>V1B)Z{yY;&=dRLy#G>o#jxv2eiTkecOcayogTmfPdiyLJ(Mp1LWZvhxf4E$fcOi&X$rz}L'
    'GV#zktpwTpD!RgnD?nL;0yUEtOU_x!;YO`Kj^cNOIVo65_CF(cXC<`3&dH6tz%99nHVU<`*5IM?iaoQOReaObJ`x_ZSMu89P!ii2'
    '?-kx<HR}B))t5?Rlhn?WKEgTBxF(b*^+IGPmL*yv3Z4lH+JGVm*ZdYBu^cl#(r>Pb>aXK^qwFyqnjWRx%y-f*%2u-5Z*a#L1qc_<'
    'DQW;Y6m0a+zwt?cyEuE$cs~~b-_mqjD1SWYKCFE6teKMu6H5-Mu>7mWX0}1+0Fml%LawlguQkhn$fb{s6yWs5<{2%jON9c|Uc{=l'
    'pLTsSw44vmi1MOjIZ>i=qQzsNLQyDqP;MoHgg$R&tI&*oryfi~l90Bqa~B5||3?mnO}d1zWrlR)dPHSKW{v%)%#JUdGP#&RXhe49'
    '4kcpB>PIZ<l?+=Cf`WjZpONcPFmq@e26-rg^j$US;y4Ee?R?B0E?vG}Fp3<d3_6Ubx>f7F&``^q<eHhxHrS(XxPD4mjWOBvg{t75'
    'gGX7Yf4fTVsB}UH++f8Lp1zRnv5zh*dj=YMCcwqQ)jD@)=>Az^c5cptvVc|*(9;iBR*t_$#yusWS;O0o30MPX#iql;jvXeCf39<R'
    'Bb;qA8ElH(I6z0K^>OZqeG1aJTfHcSnNYrzS)kF1R=;q&k~T?RZ@^y8+6D_w{~^EGX`Fl9IIr2QT-<NXU)BX$H@kGs^*Iinvs_Yh'
    '*<{e$uPk$|ZYu+T+r|XYeYpQlf$3lEt*|i?QR8gOB8H6qJ?iuwz2dcIpXBr4<=vu|q0i(vWwgB9-Dp+v`w7?oHpF>X?eN93z8jU8'
    '8HRuG|BPP(8(5EbI?1Ktz1D$!y4Y~f>$%%QR)=D~GK-nuIdDH66S2DnNF=c-bfj<qGSQ&;EiV!}j;X#~kuQAavb5A|5DSocw*$D9'
    '^qdXF^9DRmz|YcsFB((rJdI<((KNliV*$n+eszT-Ux|`GUtF*sm^?+5phqnP*$|&JM#;R-R3OcGhQjpt5JzQ$zZX>7+tL^2<=*ku'
    'n~3>)ZriTVit1;5JIk!_LobopfonSjmu85i^WNfn(jE_MSFK~-<q{xbz4yqYBtUKUpG;}ZVkE~|aac7N5pK!gYBgc8to_#@)bYHL'
    '$V(8|vaV9i=PrMxqVK4Rtq8g0X-audO_pbb@7GSsSDx%M3qm-(97KkDd*@S<e^TH{1$kwE2jU7290mHS(88RdV==QhQiIb)Eufcq'
    's)f6O#i|xtQ)JilDvJnT1sw~BBVlHnnPHokf85B&k|yv(<^k;E$&}!{OIlp9$e=YlK|4;a9Vs8jsGJzzDTWnziv8MRn+v544E`r@'
    'YV_4R)Di^gv2LTHixlWpD<Bjt^N9aWGYspHvME_`dA4$W=y^iouR!Q?#2qGFkBR57*j<bqY<R?AaTn*k&a1Ln&Y@)0)g}m;;LduO'
    'ZrW$S!$kCpaAud)|07PJI9)~MLyK`1J%^HH<0QvnKC5uCJ2+h=Zu44Vjk>>ph-d+*E!!Q5DlB-S7ET*R)ImG9NtppNp^^YzG8PzI'
    '(XALrH+gT&f$nOmSNd_<x9^tJ@vC=w*1NUcjFMe_b(k(Y(I)Y$h@U=<f6)lThC{3zl%`$+-o#DqdND3S090;K*mL<e;hD@EN&=}X'
    'lh<UlHVSZz!XQ9pLjmLx2ayf8z8-|PGeOQ?(f!p#s+MI0%bx|@sG|(BWNpCc(U<kKclA^P+BZPZ)TF^<%ng;%vE*;PxxhO{iW}!b'
    'l>=d-1!+0E;(P_qg4}^^Au-Rq)Zmy+Y_pxk@qE#7J(0-sAYM`j(jdlUy7mVrtC<qb^dt6{MwA=jw}0P6@aoDwlp%PAGY4Z8CW@RQ'
    '5=k|y@hxs{h`~4~)nJ~XP)r}+S#*AQeV$TrAt7)at32>-_~j@(;Y7|X<)#e(bOl8$fJyV!tQ@1F3{{EFG+flA`tmCZG@a@lf1Gz7'
    'y#M7A5mep<ILN&cbYma4^$<z;4v*l5$1V@B=;jTt7E1C65tW2nU%J3{J-l)fkcWsigmyc?*mq?#m_?zt?n^puCxRf}3T!CF66T`8'
    '(1dSCG*L_{k^_>h*G9{daO#jbnW|WHrb_o99hNtY=xOXIh0Hwi$XK18f_>s+tIG~v8o47S<Ae|aTEyP111J;R%^Bj^gnRyF5IQXE'
    'P3-@>#Rty<b%Eveq_xHPF=QN130JjvG9$F@QGJ<NvHsHt5|bzt6*<G0fd6v)ITx9LDtuz|oLL5tuA2_yV64{he4Ck=eU8VcaJtjF'
    'nqVzukIz_~-Qauk%07R-VbDk&0`AwIzXWFsr|A?h%|h!5!;Q>Z;_S+5qi`c#sBG}sT-(GjJ4(|em(2=Kx>PYj+b^Wf;EY4U039w?'
    'Z-+CpjfoAh8Rq~%NzYYtqUTUu-DPT7;<GrEZVo=ygA)NcQ1+$}Sj`ulK7J=cx~wV-M_mGKeQTItgoA!U%SrS!!{&FCM%0L<idF$p'
    'MHH}b_aW?y9vReM8AK71Jnxk|v>;tZ9CK^VI9w5o;C$c!2$?MKk~3d!?ttYFlcY~q!UHL$kdL-eGJ>%G7f!_@!VC!d09i!0IBdIQ'
    'xBW@%GZbI3yO3JMrwLN%3h<9|PtFM(X5r%%I%_@LdJW6XJZmuhhk34Gn`18b4t(j~p!oZ*tK%QuNA4wsn&0TtG`6EG8go8pyOby}'
    '(O};n1<ShyP?S4Jp-RGZ_P03hBQ}kXIk6={VIhCs(4V43cngE*oWgz$+f>9xQF}hZt6R(@<q09O#V#Qa(qyI8W%`?-NVF1n@pHZ@'
    't(9oKY}t?%|2fOqt(IO0&A`9o`V_2!11sg?TUF_D3D-R5neu`rujTPO1wJ}J;np6TRKKm3fm>WEp@C!l^f?82=c|@S?w)<2jw=O4'
    '1|%Udl}s{S&w_Gc<W`AIW3Tm_%%M9|V*ECm(r9d#L@vj&saQ8)%B+J`4lg2=W!6UFrnp{ok=dF+GMXc_ZBLrGPjHYC;W};dau8@K'
    'jRylj8=3PTyk*}5?NV}fMS62!nSCp;R3>*(mFG|dE8WtUV7`YM4NgXnu`vIv&uQ`Vg#s&n<3KNTN*j1|BazR@qOu5LklSr<VG}wD'
    'pC(gn55|}Xc3h>W0`YXf)}WlI2+0S<8E4lf(Qa$JMeS1I2L3IT<DIKzD0tzoH7TZuO=Jw=U32ago=fN#Be05TZ5|XR&kdi(NrOt#'
    'Ij?ns{`j=p3hHRy&hD{g%zdgtKa1H@u@WiT0GnYMq4C$pr;DrWx*CDlv;xc@=PBj_oeD!)_&0S<%vg27VQt+rR_S_<HZ0DkGl!5C'
    'pkUJS-N(9^W#L<%Z5-l-X9HN7_0s)h^agMdNhiHK9oN<M$c2Xvp4*_%B{R*&<ruyjB<SxFKLv!75nP*yw9ysl;37EsI&d)PqdCj&'
    '=YV<be{e}jdXy+=wN0f~xf!OPn{GJO9cYjt7Yk3i(77wL#-C0t@H%ORk2j?z(PVLYhy3{1$@EW^SzD8{e>!Byi=dN+Z<Ow`a?u*c'
    '{}+Tjoc7Dx&L{HaTUyC+qz6&Iu77YY8xSsi)*dIyW|5X|x<DvkJhcN_R5l*y48zi&RY3zOHfX`TcNS7Sn2dwM%zu@A#RmoNj`4J7'
    'z+O2^3soA|TvFI!U5Cl7)mQdS8OeJFkfFZeRz$;oHDcnI_=|73xcjYFO!3l-RV0asj=OXLDS=g2hDIeTl52S$0zyD@?gg;M)Jny;'
    'tb*urO=hGoL9vbPocZP+{~V;txt#~64y`;6^er%`tT7>lB0n^;YQ8kL9rk#Nu{8z84W+jGsPLP*;)%tRSINs`f)X_6@uGsKisiG7'
    'Ffu}hsX}9+Xxpz9Iib(nC#{d;2FY4;WO>q;Lc}tI2JQkRM}6&AfjL3!1x!A#d787hU-_T%8|#jiCgJRkX^cdEx!tCZl56V%sc26i'
    '0(*_Q-Iz%DgG%-SdiT_+ZT#(y>qdyh8Au-Ji83;dv<ch}nbI1_R7-@9k!!GtoyfKcun@_}oLHfGN}{v@SyK{2h6a$lbO1IAMSSIU'
    'rEExE^7i7uHp#|e08#$hVr~sJf7|syTRLQ0gr;N{@?ZUYvUisKP&(6zPcky&sKfaJ7_Bs%$cxDcBjo%UKQ?CM$2Ipe6QZH8QL=^_'
    '^=)Xr=9s5pJn*t??t<6;sQc>1P5L<ACv3;L1=y~F`X8S-G$peC^9#5tCcDbjue9Lr5Q2aaXR4Ft0neZ|>Yl-<YyO*f>~FrNxROUU'
    '0T8L<(-y@aB3Y?jGBx)Fo#>P8?(eYE+R43}RV-xkzwOT^D7*Dc$ZEuFZ79j0WAHhfpyLPLRPVT&EhBiyF1m-TDB+>u$Z;>mnCG2u'
    'JiKuuJil4#y3RkJM-cnZ6M7kyim=wj@<>`BM^;AyE+*}LrU|_Gzoa7snSvH<r1xj;>^cm%S6$Zm&NvqKU<Ybj#lc3YdKE@W@U5Xr'
    'g@3Z=ryS|@mQT>c%P1mI3T80Q#pmU*C1Ty~vC6o5&hu^CgmC-R-Jg*p@duWEt)_Ft^wtFz?3?Zp4`r;tletek`U!86<FD4i0ie8~'
    'veie4P!FQ;WAy${$9IC<K-x0>d825yIP+V9o!_c8prhF$27b054=`#sny|O^dpL>3jGXvn3)3wl4$^&aUnMVb2|&w<oT;Nb%$&qF'
    'gqnzsfc7_y=L6?mb4VS=Z}!9~FP)n@XSYCYMP)EXrLCPE?BY;~20Mu@W~05{gQgH?(R^|)E9C9%M{Ctl@frY$%^RsZes;`Cfs})h'
    '(P7CavanxauazT}eg|0m5Tjc2*w|Q)o?dcaukwWEw+_R+$MWr}5aykb&`6RxdwHz6BIgxo6ROv+gTZK8AU2vPM-(BRe5HI7btYGN'
    '{t%rOza}@$<{kb26Tf}$Q)yS@4F1Imamp>(-5Em-dvQA{tSXEWv!tESHP1Pt(QT_Gn7-;p?sf!Pr*5849ZE2V)h4UKIEKLy301iz'
    'qS%U|Gws!p3rnh27MefzE${vU<zA&!TL<o`xc$h$MQkpFpZCy!4|xsgoWOZipfdvnA``ui-B@2F(9C6uGj95wU9?f`mQ)@2$tF9d'
    'rbr2m_A`(*Ugnt;B2qCHGv7@l1tb8WhZ|$N&Min1E2|a25SiG|M3v76lTQyiOq<+Zd}xCrL4*B05#T7YV^K@Xk35H>SEleKaX!&7'
    'Iw%gL2P0{caz79oP+uxw;tSVnhr)K;iyJN-AenuO!*1NvqjPk+8SgWR+jNUGQMn^VuXRxOhjERbv*9;Bvl-Fc#OV+;-u9Xn+3(GI'
    'B66lsToS!PtXfphVx?Br@BPRp<IB2k|27++=-4|k{imv+>V7Qp{gHBWN&bS{jG=pBh#HAN8NHFMng0SOrkK{bN}kxpm?4#STJ7}L'
    'LN%D8-E9wJT~J?cem*&yixe(!tw_XnlPP>$hH_++LG&{_>RL{9jpwR%b`9HEOu>WEhJvY{utRn-u_>cfj0rT>nfJvUasyWkO3Y6c'
    'GMDtwCL#`88FPS*O47ZQGPv*`|C@IK#CnM`i5SX_p!VPVp4LAsYdq3~?qFcC+S`Xcs!f6b;K_;?2F~Ffp9FxnNq2Z{|DibY5@mpV'
    '!C+bJW4$b@p6~1XfRfq^uVS8R!9pgGOc@n;R!5{6p1!%QBHSBWpHy2Ni7*>DubJ1&QrWJzXT|FPKp|jqz}5}9F=d47$6WjZxg4}c'
    'TyNNK#sCQLpcc02p5Xe*!D&IHJeY!0*tG@tg8}f2aG=B@>9HfNTaVU3>2Xa=y`pRdM<G=kwY72(giL?Zh)@8{MttRm?P2htg1J^3'
    'ucDMif`3+gRAxH!^*BW;e420Yj@MkuyB9X3Gj$vTtb=pi9pt#&wB&tUfPnG5_&DoYDk(U2TT?ZUpF}5Yi(t@UKnI}Lr2GoCeh2Ai'
    'iecz_N<(#(bqVy3U8`M@ls+fxWkVzz&}El}H9}`+uz^!e@H8{@O)nz1K=)w5L!SZBMZW{@IKOu^xQ;4|m=Z6PzhYjkNz07a^9fS?'
    'ARqA*pP(nLTzxJgvT@!K<ZC5-qo*R|@94Y|a%v&~JI8}Wmjk$`{fF+7jn*GN@JQMjaGy9+ritWdjQy&Na#v&BmOk=XsBRVF!poHS'
    'exm+3lo6fF4#hxE$3xYc;J0^Cn|?ODvvde0jgz78PFH!u`bA*5(tQs-GO%F5BKAwi+;L=(6Bz1)n2F~Y&-ZMJ1LvOr-mXkm*zqnX'
    'InmEBk4y^jvzrw`$uAf)++-Vm9KH=>Q1Ll(J1&{`ak-D(9aE$HPZ8DvIW$)_Cs0P*+s^ZhRp=C51;p63ejz_#wo%RsMRpuose`SG'
    'z_)XP&Q5IRV(`5`U2vZRYL`2RrqYCA-&(p*YF6&zN?rfSt|(lBRlOP*e1~Klo>~v1lU)FDk2{$MM6pDrJ!+4V$GbsdO1hJMk|2>^'
    'zd~;`G0EaXjtm(A_sa?HV;T(1E5BQVsq;;!Dx*_Q+f){x{oAr0j9oTa!q+<htN2a@!`1+3f2NAj0NNAlq%GJ`&C5k?62qWMa1;q|'
    '=`!3wv5|d{TF`C^W0sFy5R}Y6p1i2rGiSQH{?_nl={8oDC`J&+xM?X0=(OYN7I<8W7~b-(tt4k-)a~i6;k{A(>W2|aX(Q!MJ<<(t'
    'S_0vZ%<~B~3L1LEgI85m>lh7dEWaPbdj7a5227-`08BgaTV)DWUYgJ-`YV1-_ewP{PahPAu0A@XW^rI*X1WRHmA@=-lCW#9*H)fY'
    'nylDC3K1RQFVQomc(NrbqZTA1YLI&a57<xdo2&5-%s(TMY8jQ!&>YcACR#Fxu;7NF#7)mt%o17BGTK=f2LKVOA}lro#y1a$_CGQ_'
    ')V?13h!Z6_s}<pVC##7!oAqMgd{CZiZEO0pUU?Vn6*9ci5riP#1tnIn1azjG#D?*RpzWH<7I45?BDT2S%TwCr^t-SfN42{tVACSR'
    'YWa8uUfHhQE%)0KwmRa|=`@`j1n;&8yDAm<-nyP}%;CGH!w_@ZH0X<{+gavAwBrPemo-ho@mg%&P;}}t)IrVd25=_FiIp9~WG>0w'
    '{YkZbj7+u>fN|X&j0l_j%%O7_f&#;-0s=QI$I&1kwjaEKw!^#aMD+{vVR?Hh{g%)lBU|xGa0`Aw78-LSFD4`z^;u2Yw8aqwe}+Hi'
    '{Lza{Sn6tYT~gSwuf)Sj6Utnd9In!v5!QoLx$Zl_T&z2M5DYuON(aNC!|TB1mUuAa7o)JPAPG_1ySq$$r49fWv{d2xf_=l|G`3vg'
    '90V=niv$dl>-Psj$IFno7I@PGW!;8X6&pD{fif8Xn~Au>ubhI5!xiE8f$CvxZ-6dU2e)?P1v9`u&AD-yO#8QCh)NT{R*1)q3-;$s'
    'D6Rtfws3)}z8oI0kzYQC+u40_-_7?Vm7Z&(U(C^Hy)QJcQtsI~;dSGTI?u2m=nCA?4sSzMi}F3bmh_u&5b~jT*hQBOextZ-du&kO'
    'yy_-RKOHk26^VqO`*|r}HCF!bhW1+?$Y;1JJj;LYy%y@qI`X7tS(zu|OFzE|0Hh+&7cU*OO}AZorIL`SNjH+96m6Sz{%$+>9xY`t'
    'RPT!J(Lnf}3mfDqk}Y>J!HKM8ZBS2vGgdE2b%62Euj|Yxl^0*6y(-BaRXTri*NAetK)h*FRH-|1tGA6iBV3gu(f$&`tea#wVUtDC'
    'I5e})R3`%}h^bA1x|te~F9=}W4n6?o3U7qpYmD-i|C(j9c}!x+xJG<2e)Vnupky|_Aj?LV=Ht{;eVcs((TR?p=hHqF>F+Fr5P<}g'
    '2&z+BFwbSwSY^dVEn%XOLYCAZ$qoA&*%6oChSbgAS%7+Yoys3_@uBO7O5yr|$`atLo1Au*kv^3;!{+l(3CP43L?qi%9O_*r+BM@L'
    'oSK^*snDD`Vs2gkB~ZU9<H6b9l;P`D1*4n!Y{2`1n7Lk{c6S9eMb%+syQP{-rA2njm2afcM?&a$QllyXu3m)YkFdi3q-~IjH=PsD'
    'O|X|2;3U-S(9=wn!MH|H_iRLoX;YmM*=KU-8-6TO)m?9sD13;k%x;Nu>;3&gPG$|hDU@HNbXG9l!zI;Twb0e4ul{Dnvb@m>bicAF'
    'aeQcG#OR&6)f5sIN_x<ug%FyHs<QaFzKM?RNOD7FzNx4YWXnbJ*wnZF@8&1N63QGF3rV2i_=Xw@xv==%9S}4j7N4hT1#B>XQ*4Uy'
    'P$}I0eBzVdk;F5=5*;ef9*{j4znqd&#Ds#3&h9?lYmF6zR~6iEjmT`ob}W+AH+Z~pu)F9H$VCLST{Z%&DDU;skKkx7)9K^noI1`i'
    '_zQ{<Ji5+}>&0PsX^4SY?fu}~5C%wf&>U^Uj8nL&|Ku_aXYutLji%cqc%xX~du=NPER9d(pyn4E(aNh&d^#4;D0p1@(+F;=ioto6'
    'AaVvRSBYsmi*xOQ?GVVAL@%mZEc2MlU#aJxaO&L8K-k9NS==zEOjk9Ezx*Uxep0}pK;7~JTHvJ?DtOzxkk1ejuzrpr;I6YZ1<}>0'
    'StUhfdhJX|T^`>xepEdmvuCnfvz?XQIw+_xKeqJKwE#HYRj0}Fuavh54E^7Rq}Gt`b>h?=c0O9>4yk9vi!Z}z<M;;qhgT;4L_$+j'
    'BA`Aw_o}oipWI$OlQR$scS!3d{m7pIZQQ8b02v(0m3hCA&)_Mt7kQ!0kq`2zGPRyY9%3yYvO0pbG>P>{+VDoN{py7>zc(h-!4`FL'
    '4o<fdx(N)3>64OJV4=WRql>c33M8Q~G8*;#vHR2f@dbmWvyWXeY5gF-eirTYf!j{*8$K0xJ}GH<gvI>)oW-_8Pb)gti5wBHea3Z&'
    '=m@q6OrCzoCgvq@DVc_;r?#Zlo<Sm;7XEMSNs-2=S%{3I4rbDqJCA}w#w;!!RoN6CGvl3`L*==Di8FhWX7r{i#_Z&SvkZ3+_}@?7'
    'v?EANS!lBeHOTLu-y1TXfgzwoJrX&&B=iE*fzvm=p%ZYoDD&Dhf>EoIO)#*u?<;x@cb3ha6@D<eQNnBk30S0G7%9@W>++H(E1$X*'
    '038`f7oa1DQTS2dGV|@0xgJdS<5!mt@8Yo~LHAzjHodf=U~{w4z)40nfb%Xt%98JnsrwS5f;|aQp=|}>q+?*FIx9e0qg3f0b&Sww'
    'drbC=RLb)ieif}41Bu4^Kp`k?{zq$<-8}cScey3y?mQF%p$<V>%si;c?MIy2m`p>vjkioacIp#8Zb~zwECjerdimL${`QZc3o$9A'
    '!|AoJk?9JC@UP`qteXD&eG6JvK2h?PSHXJ6>vJDSO{?hyNSRhcWe1rEh+85l$Dx*7S+;d#w$P7u)8GwLr;k3h1H1?S=;r0gKdHI~'
    'Tp%Ny8Pik}&rDvSFP5Xk-rq6&_Rn|7ez+w51bJ7i$v{m;=Nxl5Ju7=w>xhSnDL}6#jdI`0<u>-oYr3~)UESJHO*KJT;EI5v#_jP{'
    'JQO-&>@Nn(GE|ncZOLPin>ZP=L`IAk+lVe8tQ=9MuL>!Ob2_4RiWrJ-3=4W`zH{WleO&QWdVP#%<RyRco2!<Wb)rIsvjTHie=8hV'
    'K+YDR`UOrnQbwRO3^S9#sOa<Lp-JK9JP4WT=crO%-M(H|`{sr)5PLcuY7?n58BCCn@T-rokJEzU3*wuzh3}2<Mlpw?$z!(WJUBY`'
    '8Q21zfqISF>M}1LCr(&tA{oth{f`+Qs%K~ZJJPD{h^Q4Rme?&BhkxGBytUFzzEq+Z5psUA-#9I2h0KC4Ar&L%G&2E%u{_yVxMYd0'
    'G<-5%yBFzDryG_g4Rm4D#iJ!|q}j^#mF(-_c}erjhOq#f15&vP7X~XOI~;Nn=DSc|61Bybn{CS--&*LaK8ai&DlTyIAKW;2I$FcZ'
    'I{9LZ!wMHI>qo=jM2(`lJTpQGU!6Koee1DPJWNr!(Q~D3JA4!#Mq=1mWp`FeSG+1{!gl~z*2YKb@w+r&*l>)#UV|UJ#OAgpF|kUD'
    'c37s^vVSy^WRg?4#I41Y@U6wP&MD%XgYWQr;snpkQ9<Fz8J0IozD9D6cN51gp`aBQo-)fK<>d>=;!gn3tY3S=yP<($+oB_A&-de7'
    '6uKkN1t!Ajdsioj9Ibmr&}!Ez%n4rqW==A#kG!GPOAt7C>x1~(p2Lk4jWxd_eM)!x|L5kFi*WUnZXp6t(715I&7Y)0;kc~+>06BP'
    'dCv&+|D+$ipKAM$wQI4yGXAMKA8dL^FINJaHkyOb&~_3ZKGLwJWJg&m;pd(vA>{(wge8?K+d3rDXFklVN4a>P6T)B+(REha=iJT;'
    'EPXVQ1aopLBi4B<_2`u(?M%N8sWc?mIy2rTzo7JeI{sRDA$5dK%TDK-48c^Rb>l0$&<Jb;E%?h-e_=DPT(8uGUm>x<`<HPj7IX`)'
    '5))8v*V*qV#dBXNko`zu#KoxZ2H2^<xBs^2?T~cI0|v$w@X3-ecA{QeZx4|0or)Xa65)Hcu5P#<e+Th)oNiDU!nuo$sc_RHVjzt7'
    'Ok3(iw>Er}!Dib~c84IJaO59Y{NoY7{=d5|SL@>Af13;$o)N+gL>uG#2DZYXU=QkVv*6tY3`~~%chp>r8B~gLzr8$vo6WW5E$Hf3'
    's1<1In?FBcFrGk?<|Y;a-xDK5SuO1eY;waz-(qW@fG?NZaGBMmx#fuuanQaqo12M>Ef^_L5-yLI34I@+(VWx9WlBQgkQ)yPS<HL='
    'AX8p%G11VK5Z(h(J<9yw$y7FoUTKdqLMX8E!$0aIePgNOTJw{TW^a-NSFQ(Pfm@>(OfV4oviejVAFWq6hZvAKSI7k-NW0woFF5v('
    'QN3bjt;r;#V{_uX4Y~QN`(&(*no03o<7xrFY?8X4b8+*QW16rjakx4<a+Us4E-Y7l&oOl(usM!^$qf8Q*5pt>#@@L=8UNbcc}2&~'
    'z}EV2E=b$@QRcewbeDzd>Fu=PF>#>KLe3WN3L911tf+@!<BPlLHmxW8u9-$U;(hXE;|&lD@h1Ri9%2R38E4LG^V!SI9%B^3Z?##f'
    'ixWjh(?e#L3Mx$CyVrZ3mB6X&Zp_)syMvc+*x(m;E`Iv^f&bgECoz8@UAM}hj6L`+mS_}z#l7^%0(G5jrk2Nlr16Ic@N!9{Rh$cH'
    'H$ogRwsJJo%x`@kSJC5_{r>z_r35b{&}|WAh}zNAyN@-XrnuJiSSnb{${{$ag)AnIGLVks%B?^yRRT#?i;{~cUZpx!sM77%%MU>k'
    'Hk>2U7fUfDXUFdW;8G<<zLblX2*Jt_+{>C3*?V>N<e~1KG&6JGdp_m71IS;IBv<8XD=2=e9mZ2tPfaFYd0V+o2(q%nm@iDW3RBWc'
    '<fUj{wXyrdJL{8v6zOdzK~OGVj3zD+TUTGPT@91D1i(G0=b^cO&mmnc6WE9}bz^eGjq))-rCWrwJuDrGKYH3bWa4tp>%FhkF3whz'
    'A+eQk_VI%9o<OAinEN0;ZPrVMeB{OPaq3=(&cS@w4y^WHl9TpM0;8HOQ`g9M=rcQP;BR#I&NJ9k;XC{Ifg^SWy=N9B!67ZvOo&fa'
    '9&7$);iVT3fOe7&28caTkLu@sIWP$X+k=4j!%Vv=BEbu0AoguD_c4lERqIrJ(O*Ax)n9|Hh_+1t45_^k-W#q>^Ka8Jr@R$eoFN%8'
    'C-8w75<fnY>{z1(i|@3IvHp>$qs^d>mMx1o5QUENFK8Cp=Z5P@_M+k@pG^vG?>GSQw_JyummIaoH}80&9@nx)gFjX0PTD4fN8D^U'
    'EKtm>F^qDbze}lzD9Be{-rD?c2ieVrL5gu`b)r?;BP&M-7bk(DzZ5oZenS$_f#}kB6*vfsDnC*h@*}S<)lHQ!;#|Z-vq-N%jkR5d'
    'wGM@aL!iNg<qqrqm}4b;3Qx3p|Fk&a%)aiRNtG7MCKW-h)BeuB_Y+GW)e#P354omsx+q|uT%+8z0qIoH#7vFe=V$`Q+XgL%SEj6h'
    'uFq+6#XyxA#>6D93;Y6TF)@Xe<A?VK$VpXt+~q8AlXm&M6pS7#H+Re276u2+mgiR}`Pe7FbDNB&Nz3y|Z{Ih+NPN(3E%p1db`iOt'
    'b<EJ+63={h@LhNW(dXYJkBlb4+xmpeHTT=vEk;reku6thP^e1s<jA)t_^?R>ev<$nSI+|)CGlfm7+Hcg%Ay^&x?&wXtIptExY;k6'
    '9wC?VO;Hvd^~Dh+*@QqtvIKLtM%ie-UVF)(&$ei&Y-eldK6kt2M829b+xeJ9gadnY{bU~%Zroecqw7G(-EgWF#k_e*iJc^QbA&80'
    'Atz&*3j-|SMWI!O2EH6^&i6(2C6U`O{l{wHXcnbH03wbC%$aSVhi2#6dAuxuFMM1k%Jap-m-k3nNHVh(39GUkX?5o#*RQD<wY^6R'
    'FrM0;k!0SbTJy5S7qN+IhWJk3K0`I<O}W90?rNLJxCIi0ZDcZ{VChzcjI+TeFw)@g^VBNR4p2|ZQ&c06qQVZn+FsS2gTe-@o@3#W'
    'tn%G>=UUN;2D9Ib&ZJjW(M~~qg1lxZDC|{xaAA1GB&a?S)G+joUnr*<7}~$jf=9<TsOE8N2dCGf6Lv@Fk>H*A-i*a4l-VYfY9+^N'
    '^xX%Ta;K#P&k`4Eqfjj*O&%sR42RH<+TaP{Ah}T_p}CrU&&6i2-o*gqFP_dt)r`a88a_dqdK$RidL@k^jyXz)=9YENe&<1VRklS^'
    'T0-;ZuU+r_V;I1(JcqsK0plX~?Yb(Y$QBv3XjwcH&G;Yf^f9c@4`(+h1A(9n7376@<bgy(4oH4^%ac`NG<0-Qs_%5$AAyN!Xam1$'
    'E>)`hyVqUvg*0lOdg_+=$4xLaQVfzGq&B>Hu;&B36!Vo-7(HZ7(4*GC<{0N)n&@&&u%MdF;5twyDp+YBo}1T;s3?g`71}EX)rFdi'
    'sS6>iw;uIsjDRF(vN6Y`Rn-mBAFaZ}7D17|ZF#`6FJX`*(H893<K$T0C1YV$hl)hKA(k+TQ&R<Its))@?hY)q$Jwwp#d4#tI5BE%'
    '*^2`5=IW~Op4#>%4a-j48)&aIy3g$jXc_WBKvZ6Q>JV8owC>>t2T^RoW^J94V%M}Q-X;}X3cUtHD)82~&_sBQta{PJDGZ3t&g>*m'
    '1g-qWY1o6j4|SIJaX*k<i<A)+*zfCv$6jyO;3Sf2Qs-~E>eVK~br$8IPZ*bECi>5szNRd9BSGkUD+zsbp6~a<Yb`MU`BdEl`CuYc'
    'M^g%t)Igmy?6vGN4B!KdU<Z5!^V-|b;ng^g17hTq;(4n?wj%qWCnzsr*pk=$f#Fks$xoOLJ%#l4Tk9+7Aq=c0yKvhdw@8yaW)qs;'
    'AYB$#!vO^jvowTC(u@17iN}@F67s9Dvef*&gvKA`t@J1oiGCP9VPA@XCUu5i0ByL&ls@k>p-kf59i0-&H+9mfCu2ZNhprq84-+T5'
    '1%~(ym5peQ8-io{F(i$WvzIWcS37j1^M#BA3!dEXyNg%Ujkv)w(<pf1-b1>=`!9LQKSRnc@Zj0&>8`0x!FGxw`Fv#MKtKy3K}C21'
    '1tnVOn^hW0tkznGnY=jr1O0Pog1i9Eg@AFA{?v&V00#F2NL)~1()hO(pp8GzhdbjXV)Str3%_9?;A!CP4u$)+{pXT1Yb&~OQ}c%v'
    'LwE>2Spbe)gre$0SVR8tIN@D%WWP6ATTU&CXDOjOZrU&PU|1A1@cN6=^SN-8R0B!z$cQT#O4h$Y-SJEe>FIK_&~U%8RZej+f>Cg{'
    '=w)=e6^~WYsLQB2r^p_`uo}qy8c<<MQLAaFjdG7}&2#1tvzF_E=%*saD?!S+azV9`>J*!*k0$n8>3-aV5B(7U{xIuiayG!?Vd=bt'
    ';M%{A#kE3G`>~~ngIP<g3|DcxTgHE_`im($JYn4@3zXjkwBeO)%&Mk6O`9q=(xzr}VHUv0ujg~wDR5WRN1iI)XlG<4cT(|2lzKi2'
    '8r1YgxFA#|f+5)}o)pdRr8PfUFkO)u7H%!!MZkL+Rh$e|pEWzy&CnEj2v;Yfn3~c$3_J-*^H^?Da~9-nHQEWkY|)CVB2sxDwj@xO'
    'M2h&#=t4kmdz?}&z&??Ad_@Qk(w!BcF5-p6Bjjvil#`VgDd?-Q8>_w|_xi6mfs3FB`YkIBEs<+?kwNyw4<1J)hta*$19Z722iAiR'
    '@ZWkp)&L8Ym2CVSOeUqdhtL4Ybr?dP=ca)ffD8M1r{>)PJ60@<E??ptS>f?_>ZfjUHAfIlYXXe9JHg9ASm;%SLZJ2XV3W^^q!!cO'
    'emD$$G;8y2N8NmbQ;V2U4qq<@5ynHkN#yeL!e-k2o7JIpn*T}X&fe$_b1*=o5K6=(vy3dJ(NtVl$YPa$IotSTc?t50{Z6{!6y_m9'
    'iNpyi)<sMqb#Aqn&(h6I&vGT-JCP`R<&m)&Bv81&mXwbArk9o_0q;pE=g18z!lb0OHm!zeQ}ah32K_G<4GcY7Q8ltH^T0iRLvb$u'
    'm13$bH(j{lS7Kx<*9Wbc#-c%FY3Ti>RxyJ|lVWSYT(Wu7AGOg0ZkvFD=gZR=7x0;+jrROktt<eYcqpw6qir9~S-QQ@?2uV{qhnZo'
    'u>pm@*(+)ng_<D*>oc5uE%ZT7QCR0h3+?}ZQ1;U$Y@Hs)G<ts@Q<&mz*=Q~M95JQ6+%RNcZQrUJmG|PZU>aI_Z0Y*ou2?@Izbeq`'
    'fZJW@@jZF4(|VL&j$bD?S)-Sp@lHNmOxqyT0B-ifPwQ**uE4{=k{jK<{7OYt&)XbZh*SF71-hG9@tq{@3+;(0xY$!cfX=}$q_#ha'
    'I^3lDc0Gtab+xEL6T&&XUl4XAkEKXEq{M?v^O)`RB|w+370RErn_JkIV;zugLctZr>|u|Yp|J<=xIRyN#)U$?<iOOU(WGwv$k@qC'
    'Ppn6vAUb_S-Z16gjA0^h!*S-ggKuG5wWms{pTM>$pTE?3hAHb1J?ap-{55{hm@@vCyMu;q5(*98!{Di=^q^Ua7Z?{@8-lEH`KeFc'
    '3_!J_F$n$}MRoP|9%U)ob1a=>{h7EVxE{^|nczScXq6=k&XL2}&L-Vu<Q5vz?v^!8-92nZ-7<F&JNWahW;hHo9t-FlnMY6{NQh9S'
    ')`p$j-?YOsf1&?Aydjm>;E|>S;UU-4VgeL&;1Di<4hjq6$^RzMOZJ^Wg-_LLz7N$$q|-JuO0n&yud1~GInaRXBsx4G(HUE^E{iU$'
    'X|63aBztV-Ocr^YtWoDS-J3k9G|SvJZHVwlQ;DAaNb!Wzy6--i-;%2NI0IB--l7@Ne{Z1RNQ6pg@kUQb-9`_5S~9;QWQ5!1L`kn|'
    '7kN!{L>RH&{9c8#I;CEbUuwKhz6tnnNXD>-1)HLYJ5x__q@C|-@Vi@anWoWK+8bp*RQu|ymAeerb($NFw`x2^GMR>m-t8e0Q(T9+'
    'lDdk@(+3NwedCc__aLl|i58CL5jI1u7Z)f}*_V@8F-Z<Jvvw);fHO4olsY27p<GQYSWSp$7`pEi(z5U1i`O8`h&k(e+cRN1_p^%x'
    't0qTgrCODrT>`HyY9Pof9wE<_;1FpH2@7#LXJv>YHC!8=qq`dz04J8@awSQvl8hFYYKKRmrDDba!5})LnNoZ=k`gWvfG+Tv592+}'
    'aYp;AQ33>&aewc{_gPX)wUW0ul)=`kQq2_-%t*NDffr|EjrCf;q+FqJl|Y9%6Xvb#99K9@cHb{M$y9yTx)N9Sg3pEr$qMS$53)hx'
    '9g45U4&$zH&1CQP<wsGVRmfJfA>Y5%+@<QcP0ZpfXYxlc%^tfpZjPkcAK$L=ANqB6D0d9X^hcN6J*N`AZ4;lY%LA{jiG(k<Cm>~='
    'Qs<e~BZVq>PgR_rZmUL}B(yB-D#6kWhR|2-1V?ypK2|^07$C7dS-UB0!1fbXZL^e9W;AWUw6?Bw-t3&{nx<EK>Fb)awtyI|K<P}T'
    's5KSWDfxsm)i`ksiq!;nAH4L<{H$GBd=<3w*V2#c=u&mbwV6*&^kBFg%WK!&WQP?!X2}gbhaKh7ErED++zJQAW<<{kNlp|pe(hCa'
    '`}8~d&14Osa-jAs{zu5-)MiLo_IPWm*(oC~$-rpp^#XHb2w;LLn8VYrq&+EOs~Br0{ye~<{Axl6V}&YXhKMSI7z@JJS9Sf}r*L4f'
    'zWKn!@L+IGrt{(w*w6m&?B-Uf<R0H^R}xgY1WvRUXZ-SGfQdV5Enm~#Z1JEJyn%djpt^GM!zJJ_xj<j@)O|J4#!urH&anx4n$#NM'
    '^v*m$Yyz*AlB+If?rLA<AAQNw`FCoJSPrag<duqR#P^Qrp9frLMGNd4^(c@*RT=SXp%j-}ZI6GM5+xGGEnhZS9d1M4bv6fQNLg4v'
    ';r*kKTP<zEWmyFQ;0^$nw$FCcb}+{Lt=U?pMWm7_R28r)*yZD*D^(Mnv<hF4vm%$bOU81qEMRw2#_lcZ2rrrC9YmmYz7wHqcceK@'
    'wD3hxgyqd19fI)vV@IU_=4e`90FGsIvc4?%G}uC&f)3S#5(Szf6j5>H8Bd>=doh{Q$ADxerPD`FR0jgNUc=782*p0rj!u3TPC$Wb'
    ';rJuf%m((Q-*(NJs@E0k0FT54x4HREsN!EEE2QXf?Q0Rp^u4-<KN6L1$W$hK@H;A`)gO?A&X;ZRbZ#6*v{Q(mXZqR$hbNw8^p4uN'
    'eDWyAO{>M*VRS#LE;@ULR)o^t2uhJf5rk$IukpE#EgyyrFi-U5GvxmA86Zq)0v~;&!4WzcRUtezeX5)KWa#@ItYYQ|P}33UNQhGs'
    '_qPoh$=!A|8f5W5+fs?qYkFY(zXB!m1ysiqZ*9j#tlM;LQ>QI~i@4xTZee8_#4iiwUF#8w!3ZF8l(1-pq#oy8RCxy|;-mK0xW`kt'
    '{&8Pa`sE}qWn|cLof<N$t~#S?J#qN6%WL0kU0!!sN}bI{)@*Dx)OcHB4<1$Y@->hP|8;s+ldry;eH78Mun|0`)&uZraUl906MHpG'
    ')%OTnHpBUlrR~mowpRTx9}SV!m@cYp{P|I^vr;EcZRd-<?5<!;WT8Es3$-x;A7CpN+jEcsT*!$t=NP4(W5HqVRcRU8TPbw;KGi3!'
    'OA1@u&AG;2c&?zHvub`?jOJbL&n>8isKKCtSB(os%}QQY5;I1qm>Rf2X<C<5GcVn5KK6B?elr?|B6dB$lcFMQJEDeICU0>H5yP2n'
    ')Y_k$_hs%qeFV}mn)KZhKe?asgwM4hw8h&If9L+Gom9fWge<$0SbNcVXNMDX*mGHDUny;1_iLC$%qgn3q}kaQXOB+qj?3kdw4rqG'
    'S1S<T^G@h)^ojWilt`ZPh}ooxQpn&IeudAHqHJY$w-CNnLBNr`dCgjY2xqrPYAadMHJG#SDMX6xX}0`+G^cwL%5(+ITXfF5<kk6-'
    'OF5t2X9~xPJ`x(PS;3_%B0x<iCnL3I&s<Kv7nA*3)P)bHCZ4AiZuW=Ah1GiHke!A?XlPPb4dKTY$P>9meHVfAKZAft?m3f5yThlU'
    '!uOO*$bzXp=Bo#nl5nPvmpaC0^(V>Z5-X}ptzJWkVEG7EdiBN}j<RjyE1t-T$a%+yF%5ozyqg^|Dk!Ts24~|}iE1Ku=hW3l(R+w_'
    'z6c>KAo!$B*23Q#NUlqDa!SLeNTKsVJ(Wz95ZKL={yrz>n8}PvQiwCp-j>*j3gNFGy=vZv!tqU*KA;Fin4DB&E@SX46Me9S#Re_d'
    'KfaIirQ4EkC1;o5qa7dvwv}@^QAwSAmS9}4X{mwGnrPjCu4arQvU1d0L+Hb0^LXt9X}!j$!y1KQa|`Uo(&*9w;wG;N0}WWWgwJ)y'
    '(kLRw4VFsBGyc6*_9q8%unuG7xAqzo8O?Un9b%0+p>|dT4M(+OxB+pWJnF@T8*+YH#&Q3q5l47757;b8H+__i5l0hh-+iXf+@ud5'
    '4ratb>T`*!Z?*2W#R>-uqpLsMR^nT#inm!O#3-@a7kJvn#oVXO5GpeDf!g6sd)EqHF3wH7m6>=bZ$A)LX?{_W)O^npzdUes%D#he'
    'Kr%tEKkJdXJ;#0m#HWZn6%stgWg~OKL-T~ZN<b&PqeiT^Tgr|BqB>g6#v!<RRzf1c+pH6*F2s50p?oR`Jimkyp+HZZ-lnbK7VS%o'
    '8V&lGD~8vPpUL+^uV9ayFK<-~JJs5i?lCfPRU0f{aeBTY9HE(<&T%bs&!~LciJgFEqy=9G@OdrzDYf>1T^59w@U!YhU;%G@S&gb+'
    '&_<*~_<*ATk&`m=uI&;44ZS;K@jTC#-)WWZIZ#tdhGXmGXM8m;{@$a-Hd`nTtg0n51E04tDL8G7UglW*94hy}bA1QM?FNv^y_G=g'
    'V__D=s=QA_tiix-k_XO1E4)QmTK`r~-U)KGV9bC#%k&R|UIE35(0NwAJQu=mg`0(GDirl1XbtCSj4FStIXn!E(-u($15OZrH;Rh6'
    '%y4*Hs-_64{+v`{y{J`CKK;focbf!}jx=aX%g(GTZgKMc2;j2jLl?Z-7N=9Z8aW&DK|wc}+*)|A@(w8_?OB!H)o)W>aXr0q*AIs<'
    'BU(vZ;<MJ<2O0{EKK-g@lz93EEAu}lBknHuYanPfIEnzb?Fq<}MO~7rCI(aGy6Hk*+bJxnAl3q${TSw6>PINm#8t>+&0gp^Z;KWS'
    '8-OV#R83>y_Ra2kr?O%UE<!LN(k}K+!~)}@pj;jnTz9&!n+iUG%B1mNx5=JzMcL%0BwWm3fD68D&YZHDbisPjt79h>h#mO>$2aP)'
    '#{HbL8fFg*s>f@)9k3~5iLj=AJ7bGVAk;R5DQuzBAoObe7YgbouHe06|4aw{2*n?dikE~O;uAcw-rUM3%LI7(17ifbz=P7Ol6`(='
    'Jl6o5&&*z;U1kpfLCShQh4`EMF?gd?7D2!RQmaTLKnm<;!Elxo5JHmXO5EUpG|REGuxAon)I6$shjdmWmY09%b{*~e3N)NQ2xjcn'
    'qAauDu8?;t_NsL85E%bPc`qKS&UviV6-Q+vaMb;Cy~<()n^PK8fRsgfssVxyxYmZfn0v)!x~??zd_83K0UfMDI)-Tin>Yjuu#QQ)'
    '2ZF(hR75L(g=Mxcte^Y%yShKuAVVpZpq)g=?GSOhfWBSlB0@hJ=x+vf7d7nxSoK-JehY_F%4-6J>6f_HalS+sEo1?DRu%gvm+4U!'
    'L}P;$&PlRQR%9^dwvL<_4DQMaQuFm5bxxQ_v`URYY@8N*Xe$TN65OER!@C^eh%eg8T#4h6P99I0DZCk2I3|7+7LWp&Ds&SRCz0j)'
    '-@T+a0(`^>foRsu1&guKo6BOa482)}HT9$xWGKLoi=v&xRqg`YbFV1VQ9AX}9m>gcjv^p%F~~Cq4fDKcXf;|b@v=j!uhT-L_wL|k'
    'U-e}kQB$Wp)pki3BGe&l2UUWn+m~XF6&j}%|7mu38f7QJ&>&Jw7KLq$=Yf|w_E>t@TG&(}_IP)-0q?RtyN%$yVfTc9DCS4Zc$C~)'
    'Lo39aQ~^7$lLfuB|FzB6b5~HA*}BBG%ky0HzcqH>s0Q+3sK+|4QeIlRNyp#v(`vx8&}_@F>z}Q@EmwcLoViNG;Go?YOrI>Slvy4B'
    '-w0PIj7p5Kq62q=$-B>M0i#p1pdy(t{B907Io+FE^(P|vpuK$SB3DY1pkQAF`*Ee53XyVFBPP`;U&TE4@sS!O=U<~+%Dqsf&)9;_'
    'KTEet>8Y+-(&EtqRaF6RL_!}JANWgG6$F8}#QN0Hl9*_FnnEACE?B+U&ru)wXp#`a3a>+edZdCbe-n$5&39zq>Cv=PA2EKP(tL7?'
    ';Z^8YG2VBGIW9C<E0wpb4RzJWmVn=@MrUCas_KAvE-_wALR0s33~g{U)ux>o%6**EFb%>x=?zGWGtS9Ne;~(zK>(LyHnD<Rt%nh0'
    'OhPa`J0$=AhPo?o0l4Jx?mYLpvn0yTcaM1&6N={;i-~#2V;CsJv9pNm*bYIXvO5{OwNzGrZ||xcF;E-zLad4@eH{0a^(!mZ(}QE('
    'pMXUXkVDvtV<V*0Nm`nElx4RoP}Pj)oO%G%-=C8&_5TVu5E)mcj5P4Yf>Mei&rLHvz2wC5m*zR=f2a95g~{d6Vg>7)kNfGrQPJ^*'
    'gO%aEIy}+E(c>_!T3gD7OxWvqxd<_AiBG|z0PPN<4;=^K*0?N11L}*1NN@k-(2FL89X@7PoVW%~1G$1iPP7fLE^Kw*W)s+RAUVe$'
    'pCdRw!L$W-H5vbXz<|+u(^;>sG_+==xArmid^c2LiRpsORiAa0@&9xB6q`BaQ4I?H<xlVY-psz<)7<KV6qo(*3-%la28tYh#@9En'
    'Ewiinv(kc$+ji*~bnvR3-2O#;yb=!o`?OV_%`b47IlR(HpXgKiBzPBy@Rt+~=&b8@yB!894Mm}+pM>LXd`8bC8zt9G7~2;VF`LCR'
    'pn;0kSd%75$$mVIf$~BERGoM}V}rSXsh`CN&qx!C>SGw|9V{Wo3gzmahfH>vqGpL^A6d7y*bpZELj2$x+3C4R5Da{&dyc6$(}YHU'
    'G49Kg%^>;wHfN!SUA>8!P1KRPF@u@)3zeE=7+Hl`lME3%EAt%7g5KRn07G(Ka~3+|&K%O_V(Vb>nnt*5_Q`cCr*2B|NUsaNmxW*g'
    '@2QAV@*q;Z?>TsdWLIxGt9!BZqDKYbdT#7D*vpyEjJG{1`+%pYE9skR|G!Np56QK-9JlA#a9S0>J%S#BFWz~|zfV~>c5ndN#;g4#'
    'sMD)89hNdm3kcT=(^tHtWlbxekw}8k+K3CWYR8XAqV2+CubqyYCHq4wAnGYz3z2Y2jtURgzs{=EN-U_2;lO8}nbpMvOd|;BT%Z6`'
    'MuRiU(GJB@p{v3b8+wX@xxtb6W!-t!P{fa<+4@qKmdPjeAt&nW^M<?(HwR;Qd}_+w*RD_oKa)7gOaz_1k5lCHUG9>MSYOMuv34h-'
    'Z7v58@tW56s6&2&@n1UeXbP`N$Kn6oZmiLI1L4%f&Q|73CU_$rD`h6F<d^chxR?DO%pd*{Y7+8kVDmZp4a8|%8TWQt^`OPSc#Ede'
    'n3B|LwRj51N6?o?6J@@819JP)g}6TZ;jD1{n)dyPzi0{e{$-AzUgoUctw)efa#j%e)muaSBPt$Lo(d<ht%P9WX5i=cU}a8J^CR2P'
    '&VGtIcuWcV1HyTAOFBk1vQTm?^(=H}ts!hh)~O0WVI<3}hOcQTruMM61>19<rf*t4i}ZUlz^|ul(;;OuNuU(noU~(+Q&Ru?Y698O'
    'zOGq~d&}CKY8##d{kW2-Dfrb*tKsZ>Yk&$a)M-Vmj9CG|pNBp8czm5EP>k+#2$)`~x~BF(yJ?H;H(?G<=gnc=miW2}abX4-3*63('
    'w*lOozB4-#@!7ErIyyFiw(px7XFHk(CPgw5EfFqqEM6Y4Ngzy31-4CvsSq7%0g+~8@|**<Bovz~Rlf#KpZbCDTzTWk4uB2fRN286'
    'uy4Tu672lB%O_tko&MWRJt!XDOA3FzYSd1Lr!^I_NAByLX=VCe_ZL;Ql~I=ofLO!tPxW<4&_TZYxhuqht82}BU)u%Hd%QtMEJSlh'
    'y4Cy9llI<DY1Yncf9IEOu1~ZlU)Wdt*@bIe80?RCI+@ZN5pR0n8J{XnEuc)uztnqx7KZt3OTOP;3~hF0Ry_$rPR*)B0QDfWm<YXJ'
    '?46c;TW9O^le9@ARCXODzL<LWSMAd@aSUI%pz{~dlm2mJeATx0NsiI4U4MS^M{{IdM>!D1Ad+5Mxr<jY%Y?wLt(OF)`{A_SjS19='
    '4F2$Le-%r@(5v9Pd?qA)G<+Nu=O`5XF6(a20co!S#aQ!DKyCfjG@`-;f$?9TdDfy0-E{L&C#pVa5d*N)@$<hL1rC(2UB}t3f{=oQ'
    'JB())Tgfr^s6BBsoDoO@h(=XXai^w5XL)^p5VV67=(cCMu8?6JGc!7yK7&MJ3hyzXx*&aW8zoS34o*#5@TVq#myg(F;3Fbq*8=Bi'
    '`L3lbdZ34qWFqLGkL&$$?GUh)lnaYB;P$&~rosT8w$^;IOx^kF+VvFY6f*JJm~(ft!j@x+O3vVS=Bf>|r9hrr^naSdueHD4Tp*5g'
    'x~QIjdp&@nX9oi#L!H<i;qC#qZKYsimQbnoISJ$lIJ6vZX!TwIIB-B8MIDnXNQud*>+Q7JZekfTUZZaq?2y5IW<7s$DL|Kl#`KE+'
    'l-OW6W;~jav>k6JAjVYXf?}J8V8t+562cE_=ZT(oefa&~`BKKu{Y&Fi>qV`X{rvk2?@BxRaW4M3m)ooTkTsRNf}6OJN5hTQXVQDc'
    'G(3OFM(bjK^hy9(@~W(otWB%orTzSypV3vY@W$L9y|RM%*UnMM(su)MyP|&B{F#uMzS(ZZbcd=<gGReqM500_4|TGxj`fAXQEJPZ'
    'Du^mD+ZRB#HG}M53AHvjeNHh3VcNlLL(Fpl)5|rmtEg{f+0H95rxShrs(;`}G&Kkcrh!b%eixGz52$j>yTi8@iu{-sHm=--6wEIM'
    'U|0L5>c__G5qunA>?TD%oqD)0$Ex<!vrpt6cjaTvXj%|1Y2ty;%+V@O+LZRNu^nWm$fm*!fj}*Tr%<aAGN005Kcy^ADOx}lNYv}m'
    '0sYNy6d@~!(N8ZM*;p$y{HuT+A4Ng$A%3)NqTpyuM%O12#1yO~nY{=^_A%|6HP>Znz&WN5&V>XSg(FxF<%cJolClD70P5hFN!nYm'
    'cgEsEmReL2nEtPF=U#|H9&-ScZ*K3RfynERw%b7)Z|ot=EttELT{@$WX`U?dh&JUzu$jjs20%IAq$u_rs;e{MV$Y3wR>%qi{L|MO'
    '&zk?I<Rp!@48tB!;eL?xPYR_Rz+Y&b4`TtpUTPUipU%oFm|P0#L4&~Ax4f0J%*H%y5dt#SCB!v`HDXSg(QiOpFCS&foyCTQ*;QLv'
    '>>wm2OFnLZ_g!aB_lf7%*P=GrP8k|~HoPzcY+TMP=802#G9plUl*fwPk(*?wR~3~DeRvBoV_?*m^zJCGV3{0$mQZInSw!V>5H!)*'
    'Th(fT3L#Q1Is5YJM|X7E4#-%t_`+OeRi-qYBUZGb2(ykRBR?ydeN#w+d?D_MDP(Hwo*Ym2O@V|oZF(5f$v`gPHWvCkr2&N9-Dg1d'
    '*PuQJ%^>UgL_QfvpR1ApqzQ`Y?I8DF!Ym?OA-K|AKbz|{9Vl&tirx7vZ;_6H8MVA^FnKnQyyt{jw3?Vpq9}$wpveR}B}+A$-Qz=U'
    'UJqe{Bi)_)f6CWaloDLEZh?PMK<>~RXgiba#TLK!DE;2v;M{416)(dq@n3{pU;i0{jWmnG6dlsKGm!>c65Iu+O?o7@4PKFm^+XH*'
    'T3>>RYp2Rnom^TK7gMU+zW=O*os#6GSNR9x<YIWSxM%~%zt`nprI&`I6jhcMYk8Hb9J-^121HLJ+yq#rO!&Rih)29ZPQz{Gfpw1a'
    'Lt9H-J~{UQ*|_4uxPnx@syIFT`%#;qHQ-53s9Te&W*Y{>P7O2hxbjE;+yyU0V97RI^Sx>!s$E&nDq+Ig?W2K(eyu$^qJ8i8ba4c}'
    '7U9cNoJONgw7;SKC6$>dzt!1ONg@^@?Gd3Y5XURgB2&;#VAWbgcP4MwqNX)E`3_+P3m)Chu{tGk<lW8ca#ipt$ulGvZqNo<)lsk6'
    'E~!Z@ml_e4s%kSOQzR*46(X;<Dy+i8g7;3ll8j`p^$Xg}v~7%$mxmx{3<%R2-fTT|41cdF2Oc98Qd{E5FB3n?O^AfbEZ)vOd`W&Z'
    'mIW1wyM32zK80IS;UPsU*3w<}ml)^=W7e6Cb-+_&_n`mdJ1@VewZw;EV0Rb-jzuWJH@BBx$w9Mya23I;7fsd5U9trF4ei@z?8Ht4'
    'o`W6Dt*$}qfh9NBY2h%^9U%dMI|qDgyDf#>>xdzb_D@Sv?>XNHR_RB(^iwh?Od*KLp555|o|%Shmc{(^h+@!!G-(~PLQwZZJ5{%;'
    'ic7&0wF3fUHjUR5rR!#;<2}&#9F4RCa=$_{Pb0}A#NnsSm01*aOE;hiIOCEma*a564P=J^Wpdc~p?w$a#@yJi?anJeAJIalbSXV{'
    'AE|$wRZ9{j1*)b`A8F+~;0R%95VWdi00000QkP_{V&?+e00Gsb3F_WP&#GAOvBYQl0ssI200dcD'
)


def sewok2_decode():
    raw = lzma.decompress(base64.b85decode(''.join(SEWOK2_DATA)))
    table = {}
    pos = 0
    keys = ' ' + SEWOK2_KEYS
    for key, width, height, x0, y0, w, h in SEWOK2_INDEX:
        rows = []
        for y in range(h):
            rows.append(''.join(keys[b] for b in raw[pos + y * w:pos + (y + 1) * w]))
        pos += w * h
        table[key] = (width, height, x0, y0, rows)
    return table


SEWOK2_FRAMES = sewok2_decode()


def sewok2_canvas(key):
    width, height, x0, y0, rows = SEWOK2_FRAMES[key]
    c = Canvas(width, height)
    for dy, row in enumerate(rows):
        line = c.cells[y0 + dy]
        for dx, ch in enumerate(row):
            if ch != ' ':
                line[x0 + dx] = ch
    return c


def sewok2_front(step=0, talking=False):
    """Saber off, facing us: step 0 standing, 1..3 walking; talking opens the muzzle."""
    if talking:
        return sewok2_canvas(('off', 'front', 0, 'talk'))
    return sewok2_canvas(('off', 'front', step % 4, 0))


def sewok2_side(step=0, talking=False):
    """Saber off, facing right."""
    if talking:
        return sewok2_canvas(('off', 'side', 0, 'talk'))
    return sewok2_canvas(('off', 'side', step % 4, 0))


def sewok2_back(step=0):
    """Saber off, from behind."""
    return sewok2_canvas(('off', 'back', step % 4, 0))


def sewok2_ignite_front(i):
    """Ignition 0..5: paws take the hilt, raise it, the blade springs out."""
    return sewok2_canvas(('ign', 'front', max(0, min(5, i)), 0))


def sewok2_ignite_side(i):
    return sewok2_canvas(('ign', 'side', max(0, min(5, i)), 0))


def sewok2_ignite_back(i):
    return sewok2_canvas(('ign', 'back', max(0, min(5, i)), 0))


def sewok2_lit_front(step=0, talking=False, spark=0):
    """Saber lit in his right paw; spark 0/1 are two crackles of the blade."""
    if talking:
        return sewok2_canvas(('lit', 'front', 0, 'talk'))
    return sewok2_canvas(('lit', 'front', step % 4, spark % 2))


def sewok2_lit_side(step=0, talking=False, spark=0):
    if talking:
        return sewok2_canvas(('lit', 'side', 0, 'talk'))
    return sewok2_canvas(('lit', 'side', step % 4, spark % 2))


def sewok2_lit_back(step=0, spark=0):
    return sewok2_canvas(('lit', 'back', step % 4, spark % 2))


def sewok2():
    frames = []
    for d, flip in ((RIGHT, False), (LEFT, True)):
        pick = (lambda f: f.mirrored()) if flip else (lambda f: f)
        frames.append((d, STAND, 0, pick(sewok2_side())))
        frames += [(d, WALK, i, pick(sewok2_side(i))) for i in range(4)]
        frames += [(d, TALK, 0, pick(sewok2_side())), (d, TALK, 1, pick(sewok2_side(0, True)))]
        frames += [(d, IGNITE, i, pick(sewok2_ignite_side(i))) for i in range(6)]
        frames += [(d, LIT_STAND, i, pick(sewok2_lit_side(0, False, i))) for i in range(2)]
        frames += [(d, LIT_WALK, i, pick(sewok2_lit_side(i, False, i % 2))) for i in range(4)]
        frames += [(d, LIT_TALK, 0, pick(sewok2_lit_side())), (d, LIT_TALK, 1, pick(sewok2_lit_side(0, True)))]
    frames.append((FRONT, STAND, 0, sewok2_front()))
    frames += [(FRONT, WALK, i, sewok2_front(i)) for i in range(4)]
    frames += [(FRONT, TALK, 0, sewok2_front()), (FRONT, TALK, 1, sewok2_front(0, True))]
    frames += [(FRONT, IGNITE, i, sewok2_ignite_front(i)) for i in range(6)]
    frames += [(FRONT, LIT_STAND, i, sewok2_lit_front(0, False, i)) for i in range(2)]
    frames += [(FRONT, LIT_WALK, i, sewok2_lit_front(i, False, i % 2)) for i in range(4)]
    frames += [(FRONT, LIT_TALK, 0, sewok2_lit_front()), (FRONT, LIT_TALK, 1, sewok2_lit_front(0, True))]
    frames.append((BACK, STAND, 0, sewok2_back()))
    frames += [(BACK, WALK, i, sewok2_back(i)) for i in range(4)]
    frames += [(BACK, IGNITE, i, sewok2_ignite_back(i)) for i in range(6)]
    frames += [(BACK, LIT_STAND, i, sewok2_lit_back(0, i)) for i in range(2)]
    frames += [(BACK, LIT_WALK, i, sewok2_lit_back(i, i % 2)) for i in range(4)]
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
          (7, 'Extra 2', extra2, EXTRA2_COLOURS, 0.3 * 96 / 94),  # (drawn 94 rows tall in his 96: 0.3 of a person, as Extra)
          (8, 'Suzy 3', suzy3, SUZY3_COLOURS, 0.9 * 200 / 197),  # (drawn 197 rows tall in her 200: 5'3", 0.9 of a person)
          # (Standing 129 rows tall in his 132, about 0.6 of a person as the
          # Sith Ewok; his saber's haze and blade lit.)
          (9, 'Sith Ewok 2', sewok2, SEWOK2_COLOURS, 0.6 * 132 / 129, SEWOK2_GLOW, SEWOK2_SHINE)]


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
        # (One carrying something lit: its frames trimmed, the blade's room
        # above it mostly empty.)
        frames = art()
        data = gzip.compress(svc(frames, colours, costume, *light, trim=bool(light)), compresslevel=9, mtime=0)
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
