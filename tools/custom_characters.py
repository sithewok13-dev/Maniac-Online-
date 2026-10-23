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

From 0200: Crispy 2 lifts his far hind leg to pee (P); Suzy 4, Suzy 3
looking straight ahead; Sith Ewok 3, Sith Ewok 2 with moves drawn from the
side (a force grab of his saber, putting it away by hand, a swing, force
lightning).
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
# (From 0200, seen from the side: Sith Ewok 3's taking it up and putting it
# away, his moves; Crispy 2's leg lifted.)
GRAB, STOW, SWING, ZAP, LIT_ZAP, PEE = 8, 9, 10, 11, 12, 13

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

# (0200) Crispy 2's pee, by an artist panel from his own side frame: P lifts
# his FAR hind leg (away from the camera; mirrored facing left), the thigh
# kicked up and back about 45 degrees behind the haunch (frame 0 half way
# up), a stream outlined in gold-brown so it shows on any floor, flickering
# (frames 1..3), droplets where it lands. His body, head, cape and tail as
# side 0; his standing far hind leg taken away. 104 x 96 as his side frames;
# five new colours. The engine draws the puddle where the stream lands
# (CUSTOM_MARKS: art pixels from his feet, facing right, and its width).
CRISPY2_PEE_COLOURS = {
    chr(0x300): (138, 92, 20),
    chr(0x301): (238, 206, 84),
    chr(0x302): (255, 240, 150),
    chr(0x303): (196, 150, 40),
    chr(0x304): (112, 72, 68),
}
CRISPY2_PEE_DATA = [
    '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',
]
CRISPY2_PEE_KEYS = sorted(CRISPY2_PEE_COLOURS)
CRISPY2_PEE_LANDING, CRISPY2_PEE_WIDTH = (11, 94), 22
CRISPY2_ALL_COLOURS = dict(CRISPY2_COLOURS, **CRISPY2_PEE_COLOURS)


def crispy2_pee(i):
    """His far hind leg up: 0 half way, 1..3 up, peeing; facing right."""
    raw = zlib.decompress(base64.b64decode(CRISPY2_PEE_DATA[max(0, min(3, i))]))
    keys = [' '] + CRISPY2_KEYS + CRISPY2_PEE_KEYS
    c = Canvas(104, 96)
    for y in range(96):
        c.cells[y] = [keys[v] for v in raw[y * 104:(y + 1) * 104]]
    return c


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
    # (0200) His far hind leg up to pee, from the side.
    for d, flip in ((RIGHT, False), (LEFT, True)):
        pick = (lambda f: f.mirrored()) if flip else (lambda f: f)
        frames += [(d, PEE, i, pick(crispy2_pee(i))) for i in range(4)]
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
    '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'
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
    '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'
    '7f/Y+l/NhUsF'),
  ('S', 0, 1): (
    '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'),
  ('S', 1, 1): (
    'eNrtm/1PU/mex7EFKQ/DSUhB0qLGnkyJyeHBg0PVnoVhZpx2cG57eTAc04W5JITSpjhrt4xlsgsuBs/Fh6kSMwz3WkauFqnbKpEM'
    'OwfjMlJbEAIJFdzGaaa3RI83Q/+I/XxPQZ3Zn5Qvv+03CGhiX3l/Pu/Pw/cUUlL+/2zv0brRoWn0efsgWndU9fpsF0irUvn9FMcJ'
    'BEH4w/KwnHZvS8TCfj9HqAQiajIZohrTqEO3DZK0fpU/DDI4nVMucBSzqtGphG3guP3+MBXlwqNnnRx8XlXooiq/QLixy/FHBQWh'
    'c6xmUJwiY1Ql93OUQS5oMWPClFwwCApdxirl12Q4qGg4atA4/Vz/Ct6ofR8m5Jw86jwbDjscTDiqk5uc1IsPT2ZlrWB1NBXmomG5'
    '6awuyjhMBrki6nBSsnj9yaxxnCA3F6blnMlwVhNVaHQmuUnucHKdA/n5E/knJvFxtBSnojidYXU1rDMpGIPOZNBQXfOJ/ImTE1mT'
    'J7CBtJyKCAvM6KpcYXAoQIxKo+mbnU+cjFfX50/g5PjdfoNz1SGP6hhH2GTQaYQ54FQnEvH4yXyMHIpya5yrKrmccRjkDsrhFKYH'
    'quMIk6jGxtEKHEdxGaOmqCrsZCjGGNb486ZT51MTia6/l/7TVXwcivYrGJATjo7Kww6/QcN1Tc/Ozv8iu3dyAl9+tJygDY9qHFxU'
    'btCEFSbB5BQ6Z1MH5hP1E5f27s3GxyEE3WiGgQrDRKAcUUozSvRfnf/lJJRP6oPSVHxxI8IGR4ZfFQ5rDCoHFdZoLnXOzg7EJyYm'
    'xk+Pj2PkyHUaJ9UWVmWEDQwR1VD3iqdTE/UnssZPn846fXoFF4eWmzQmSq6KOsMmnWDQCDOd06nxiSxgjOPkENCddZw8rHOEGQNM'
    'VJGTQFGDc+IEpsiBr6O6jD8L8qiJUWmgn44KXWdmgZN1WgSNn8bGMehWo4Qclg+VRsUxo3TX9DQ0hIkTk+PjiINnNmiFHVHFapSG'
    'Mcf4NW2cc9Td1Tk9PTuQiJ+YnIhPxGf/GxOHizKrMIHkTgWlCQOH7p8GY8/+CUj1ifr6Vmz9TcdkAMfg0AkaA+LMzck6i8EL1dWP'
    'qjsfzeDjOEaBo2DkSY77xqPp2enOq6mp8wN5f/nqK2x9FDh+Ws4wYQ78Bnq6HhV3nrk6mwpd7sdvv/0WU3vj/AYGOAYHo/Kj/GTQ'
    'M12ds1fBCqnz1dU//ngD03ZAqRSmDL876nC84siKr87Op6KZWv1vf/lXXFNbpYC4uQ2Mw9+mUQkQN6RnFoI2UJ0YGHj0J0zpUanE'
    'uOkYxg89FHHyuuamf4EBNJAKlsPW3lTJ/DAKhoIeSkHc8m6A2QaqqxPVP8fxjQUVZ0Ich0kj6EyCypmhzeuSoepJDMyDJmxl2kYw'
    'plE/xygcgkIhRJ1O7XczXcXTneA3cPY8Nk6YZkwZ1JIJ1jaTgTM4Ndq8vBlQNDsLbW46FRsnqlUoMihYRjWcQ84pnA5tV15eHtRq'
    'cfGZM8Wt2PITdQOH0/kVGpXDL3JkIGim60ZXV19fH7ZtVKAIpEdHKRxRhwAchVYmmwHOo2JskOTYJhSm0bAcOAaHG8acgZDJ5vof'
    '9ePluBGHgUWUMjE6BS3A9nYPOHP928CBfq2ggKOIEpQG2tuNLhmg7r3oxxs4P6xvCoJ6wjDrS5WaDLesX9bVJXshcDN4OW06p1NH'
    'UAxzqxdOT89nubm9dbIZwch17cXIIcI65yhEjLm11tx89Oidg7v+AKf3w1YhlzvVhlFPWOHM8AsU07OWBO06uAtO785/CLljHW0Y'
    'OSZnBiFwzp5a4AAIJB3cdedO78Gx9dy6Pyzh8wHjGKU5LuNWWW3zWvNHIgn+9B5tHjNyvbuW8HE0DrfA1XWMdO9EippFVc3NvXcW'
    'B41jy5hAsFcxjMLNUbfud5Qt71xbW/tog9V79GidMbdu18E6TI2Hceho4OSAoFoEakaq1pp7m492DBq58oN36rBwaBMjJ5KcquXa'
    'nYgknl4I3wXw3J07OEAiJ0pzRpHTjUBAgk89ovvqjFwDxA8LByYCzf1wV+RkiqCdtbXLPWL8usEKzUc/qsPhAx0Tptdv3c1BoLLl'
    '2tpjx2qXAYMy1dz8vsAdxyEI3bM0KuKHQ3eTIKSodjmzu2fDEWVIUHNzHY5+7fD33rp+CJE6OkbKurszu7t7Mjetd3wl+z4WDtx8'
    '/FfS0q4D6X6SVFVV1bN8bGcSdDH78z+O4ODoDE7heVp7u4gCTfcBNdKTuWHxUyuf/+3z7A4MHNiohCvt7Yvt7Q/T0n69ngzfLXC4'
    'CCoXOXe3ziEUcodQ93zx4cNTi4uiKiDdBw5yHlRS+co/r6StbZnjBo6GoLkrR45cPLII56FIupW5vIwi17y29mLF37yGJ24ELbTK'
    'fm54eKS8XNR0/VCSg2r2ozHj2BoOjilqomkhuxMuIz9fOHJRBN3qyMw8tgEijGM7d2LgMFGFm27NhgsPXKwGEj9f+OHWrZxMOKKi'
    '2kXBWFe7/HzrDYHx62i6dToRr6/PjycSiZeHMjfOMjrlAveP7m4cHEJB0w+uiZyJyYn6l92Zr093WYPAvV9VhYFjGjPRRPZ8dbw+'
    'HziTpajxbFKOdZcdF4SGkZGtc9ymsIlD6RHlAKdqE9Pd3V1VVVZnFMo7OrbOoRUqBfdgNrEpZ0TkQMfurhoZ6ejIeW4czMGAAY5f'
    '53+QisImRg043QhT1ZFz99Ch69dhLtzFgEkhDJTujxC2Dc6iyIG85BxKO/Vw8WID2DrtCgaOIBcMK8jVIqavHKYCBK4q53r7kYsX'
    'Gy68Pyi8jwMDgRMMyfQgE9BpI4jTPXK3vbyh4UJDw3MjrrcDae5NDhpzoGfk7sOLFxouXLgwaBQw3bnd3J+zkQ0mJrNKP6A73ohb'
    '+ZFy4HDxVkyc/0LVk484DOhBnGUAgQ/aF48PGl9gesjjplbOJMOWVaojknGDvtY9Asa+C92gM45HkJt7INptMiurVD4Iu0Fyt4Lt'
    'arm7CmwAMcUC0ia7gZgeoifJOSZOHjhjxsHUBB6QlkI2SKaH6EVxK8vcWLPXrkOVoueXWDgvoFkn06OhT23Gbae4G0B6rlydnk/g'
    'EKRdQXZDzeADDZEjcrrFuK11Hx8zCs8/fITeftw6SNvaKaZnstRpGkzuo0lBa3Vcbu5gz4dd/Qi0ZXO7kd0gbKX/ruHeb7+eU1aG'
    'SgjuDGmcMTd3rOfDe139sxhS5Aa7ofSU/lnDHU9rL188lXboUNrD9vbjAnBy665cutf16NrWQW6wGwrbS5WJaIBNPicHps7djrKc'
    'MSPi5LpTLuV19adu2Qt09kC8HuS8dCuIC7DzIhKkCRaQJIdISbl0T1Y8n5gd1G6Nk0wPoVUIDXA5QSgEq1tffw3KkxV3cl9/vZWf'
    'TNk7nYCwlf5dcOuEBriboIsQog0CZpMDoBnAfH21de/ed41e37VqFLYXAgF6Ftt/TUsTYQ3E+hPmSe4rkAAYGdTRQHZr6zuh+gZQ'
    '2F4SFK0QdlRunCMX6yrX19dzHZoNTor2669nBhIi6Jd3etehNRGHsL0kwhA3s8dj9pjNZk9lJSDFBDkBRIuLeN7cGdTq4tmd7/Ju'
    'gBi2rFI3IacVRNBuj+2OwYc9Nog4IshoRBzk7rnOJCg78fagvvlqGD2ltBAlGPrLYAwQu4PB4G6iMinI6MhNcsQymhZDl5r9Dpxr'
    'AxA3CBtFOIlgLBhsbAwGLbsbkxwkiDG+At0AUDxefS3x1k9O+2ZFV5e6DYSfqpG4rC6JxEqqXcFXHKNmkwP1eqMYbi6d79CD+lJR'
    'esZLqTAtF0Iej2fB7LLyZnMN0bYJevLkFee7G7PXpvvn34XzC7gaOP9C0QxhNktcEnXIKpW49ERbm8gBUMaTDU7Kpf452Uz/HNz9'
    'Wt/e1fmT41mlL+mwMGy1sqQkRHqDPDssckTQ+u3VTQ4o+m5GViy7Otv69ukRN51S6KISCckDRe21sKEYcDZBH5+lX3cpcJ1sbqar'
    '7+3TMyFyDEKhklfyJBkK8S1DfCPiIBCQzt6m3/gvl9B527cEVtAtLisLDPcBTbokVrU65LWGGskQSSwttbWduv8rkJxn6S3O0tb4'
    '5OQ4nPzSrNJYiIWgSUhWzbd4vdampaWlSthLPwPQVjEpfbKB+snx06dL87NKSZZlQ4Cx8koLGWIP0AD6DPS0bZ2zI3uueLoaVsSX'
    'E6Ue0hvykiFwNUk2smo1P7gkHsjSln/uckf2mYF4an1+PXBcXquXZ3lSzYckFn6I9A4TtMghtn7P2pHdPx9PRbtB6YJLwqpdaggY'
    '6PofJUuqrfbzgzRNjBU2bZ3T+GC6OnWidMHjsfLqodBQiPVaWSXfqCZ5PuRyhdRTXpdrx5Y5TbFW2C/qgeMyS9QkVI8EHOclLawU'
    'ypUdUsNnlxUDx7XyQCZ7ueAxS7xeXskqlVNT3iHwG3zvhXq1quHr1sOW0kQ21mS/9IAc9ZALmg7Pq9Ve1moNWqFa/+qFmElwyElp'
    'kgaDMAo8ZujSLjVI4JVeidprbeTZUMjKqq2AUePg2KU+lBpr6FxoSO2VuNhzIS/P2xulyikldDqWP8eGMMRtf9BuqXBZ0QANqa1e'
    'qRIKiFWHpDdDLAuGG7LCoJBi4QRjjQGldIokIfOs1xsipVPnzsXsXvUQr4YBobaSQxg4IijmCypBSAiNBF5KkkppLHbOq5aEvGqS'
    '9A5NYeLY7fbdMRe8IsuSvJef8sIXO/IDCSLhnzHYAIFaWtBSaFfy/Dm1l/RC3HglGbSyVkkISlRJqpvwcGpq0i2ACYWmSIl3yhti'
    'pbzXGpRIYP2FHQtH09kApae3NLYA6RwP7QBmEESLtVihcjweWOXU2DgBX2C4xRK7KUW7AQldjmT5oBrkQPmCpCZMnBRbSWFhJL0l'
    'aJcqWTTorLwUPmBfhAOtApceuHCc/7QkMmwBzrmh0F+talgSXHYRs7BnwYyPY3v8uBBCFwMQD4XK8kqrxG5e2LNnD0Jh49gCvgMH'
    'CpEeu5Kdgv4JLRX2X8RBJIx6Skp+CrS0AEiqDJFWkvWC1XjE+eSTPQv4EvRFYWHh4/OFw40xKTpKfgjchvR8gjg4BR0YTm9JD6SD'
    '5aT8EIxs0upZGEJq9gAIHyfli5J0qFZoC3bwQgiaKnQD68In6OzBCzqAQEGUIlY5xcO8hjoVA4dZ0IESCB1Y4aZUOqUMWb3AUS4k'
    'E7QHI2cDtBtat5SHOxA42yNx4XdCyhefPi5EKbLElPwUGZKYXeYFNikIa+BEQS3IC+BsWK4kVtdrQTg52k8PlOjBDF/CzLMrlWo0'
    'gPiFpBNwclK+gG4KkygYBElTPMlKzGa1eTsEnT9QEhDLaDeEbkgCghamNpoCXkGfPi7xDaejKS5FdSRxmbclcNrz5z99XJPe2II2'
    'IGhzU6TLcy6pB7OgAwcO+NKRILACbCMQOem2BO4xgArRVhIUZx4v8XjUyRr6PgUr6KfHJSUVw2jRugnthw25UPNBTRsvBykqKdRD'
    'o2tEZoC1d4h0Jecq1sCBFSB0AEq3NAbRiGBdZnsyQzswCzr/WDR3Y4vlJrhBSUpg8cFuOBD0E7QfXwR5YTds+ErS5VUjQdsAOl9S'
    'CF5AZRQDN8CqvbCAP0FohEPc9HoYRhYAwRSPmT1Y17jXIFh/UOdutEDkpKx9ymzeDk6KrbDEp9fXNFqQoJiUtahDEpxr9muQLzIM'
    'J70lJrXHghb9lxal2rwtHH1NYDi9ZiNDFuipXit2js1WMRyJoAS1gBiLMiSN2W8qsXPg2hUZjtQM6wPpqPnYd1ta0oOgqAmzmkgg'
    'UgOMdORsuPNPhUhXTMJLpzBz9kcC+pphkKMPVKBKZa1Wl93Ksl68cbNVVIDXWob1w8MVEUtQyg5JXK4YesrUhDk7+poI6gbpel9F'
    'EOqUh6uQFL3BtQOvnIAeWS0SqPH59FClwDF77OjijZcT0OsrEEnvg95jgb2e95oXbqLnczswd4JIBAUNbF0RgfKR8laXeQq3HlsE'
    '1EBriwQCARAEWz0Mb4mZh7uQpAlzepAJAhUB6Nkl+y27Y0qJZwFWejNWX9t8ICeij0SQmhJbyn7Ye4bMHhe54MGaHxvEKwBdJ1BS'
    '6PPZ0MM56KNeq0S94MGZn/2Biv+I6APDkB8RIz4ElLJm1zm8PrBVRPTQ2yoqKnyFto2njbDzSKysB6semy8ActKHfSg3SQ6scUrr'
    'EL+As37AbZEKH5ROYUXFJseyG/SoQ1jrFFxQoR8Gu72Sg0AxacjrXcD4lAc1nQhqBBGf7bU1LEG7mpXifNwHLohUiLVj+81j55s8'
    'yWP0AUyeimFYDCoCtt94HRYrVorP1zbff8KEA7sFfscJSr3nprBxbD5fbN24rvxNcjaNILW78HBstkLfem5BQUGuMbD/900CcWB6'
    'Y9FjK1m/XFBwGf7k/h/OTfvNmNoqwRO3JsOzZ89uP9u3bx/xew7cvoMwVfFw6Ge3b38MqGf7Ln//e04w2AhjFQ9nad+zj28jzuXL'
    'S7/nWBpbpuCS34QFs+/ZPpAEnIKC3/7G3H4PXE+VUiWWBa5tn3hu3769r6Bg35uRsxkZOE9yP9Hr929dTlHRN5dFEuSn4DeK6KKi'
    'p+jkGj0YOG1FRUWHv0Ggy8jcbyiqLEqCDhcxNI4EIVLR4YJNUtsbmMNJRU+/qaxc2vpvO36fREH8LqOPjResPHy46JuiDU1PiwqK'
    'KitxiDq8IepNzmGRI56nhw8/fYoBtCkKXnyD0wYY+FvRGwcLKCXF3yaiXnMKDm8eMXrvvYeHI8av7ZtXcfumQHz9r97bPF9h46AA'
    'bn6z/t6bZ11e2baUsg2n7avkq1dWoh+CakvZtlMZ3s5Xf7fzv5mKrWs='),
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


# --------------------------------------------------------------- Suzy 4 ----

# Suzy 4: Suzy 3 facing the viewer squarely and looking straight ahead (the
# user: Suzy 3's front was at a weird angle), her own face from her photo set
# upright and centred, the smile the user called perfect, narrower happy
# eyes, a round, broad, even chin and a shorter neck (the user's corrections);
# wide hips into straight jeans; a front walk with alternating steps and arm
# swing. By an artist panel; the photo is not kept or read here: every frame
# is baked as palette indices (zlib + base64, 0 = nothing), 104 x 200, hair
# from row 2, soles on row 198. Her side and back as Suzy 3's, the side's
# jaw and collar matched.

SUZY4_COLOURS = {
    'Ā': (32, 29, 38),
    'ā': (92, 118, 167),
    'Ă': (58, 88, 141),
    'ă': (212, 115, 58),
    'Ą': (43, 113, 59),
    'ą': (89, 185, 97),
    'Ć': (45, 71, 122),
    'ć': (165, 83, 42),
    'Ĉ': (110, 100, 101),
    'ĉ': (74, 166, 86),
    'Ċ': (254, 158, 83),
    'ċ': (67, 38, 24),
    'Č': (248, 248, 248),
    'č': (56, 138, 73),
    'Ď': (29, 20, 21),
    'ď': (7, 3, 5),
    'Đ': (162, 133, 124),
    'đ': (64, 62, 65),
    'Ē': (3, 77, 4),
    'ē': (59, 47, 47),
    'Ĕ': (128, 53, 25),
    'ĕ': (246, 143, 73),
    'Ė': (150, 211, 150),
    'ė': (192, 190, 202),
    'Ę': (7, 10, 25),
    'ę': (73, 61, 61),
    'Ě': (60, 91, 145),
    'ě': (27, 45, 87),
    'Ĝ': (54, 78, 126),
    'ĝ': (119, 138, 177),
    'Ğ': (28, 14, 14),
    'ğ': (16, 15, 15),
    'Ġ': (174, 172, 184),
    'ġ': (47, 36, 35),
    'Ģ': (70, 101, 154),
    'ģ': (187, 224, 185),
    'Ĥ': (21, 58, 31),
    'ĥ': (83, 111, 162),
    'Ħ': (221, 220, 228),
    'Ĩ': (24, 21, 30),
    'ĩ': (98, 35, 20),
    'Ī': (124, 100, 93),
    'ī': (38, 29, 30),
    'Ĭ': (187, 93, 48),
    'ĭ': (24, 40, 80),
    'Į': (84, 51, 32),
    'į': (80, 143, 80),
    'İ': (21, 36, 72),
    'ı': (26, 18, 19),
    'Ĳ': (22, 102, 24),
    'ĳ': (137, 208, 132),
    'Ĵ': (112, 88, 81),
    'ĵ': (33, 54, 100),
    'Ķ': (92, 81, 81),
    'ķ': (50, 126, 67),
    'ĸ': (211, 210, 219),
    'Ĺ': (30, 91, 48),
    'ĺ': (20, 13, 15),
    'Ļ': (82, 71, 71),
    'ļ': (122, 75, 52),
    'Ľ': (48, 45, 48),
    'ľ': (67, 156, 82),
    'Ŀ': (181, 100, 52),
    'ŀ': (234, 128, 66),
    'Ł': (131, 172, 127),
    'ł': (136, 133, 144),
    'Ń': (125, 142, 179),
    'ń': (109, 199, 108),
    'Ņ': (15, 26, 57),
    'ņ': (68, 56, 56),
    'Ň': (41, 65, 114),
    'ň': (50, 81, 52),
    'ŉ': (46, 69, 114),
    'Ŋ': (101, 155, 100),
    'ŋ': (171, 119, 66),
    'Ō': (169, 217, 168),
    'ō': (63, 52, 52),
    'Ŏ': (58, 57, 59),
    'ŏ': (57, 39, 37),
    'Ő': (84, 179, 93),
    'ő': (33, 39, 28),
    'Œ': (242, 139, 71),
    'œ': (16, 89, 17),
    'Ŕ': (25, 71, 36),
    'ŕ': (201, 224, 194),
    'Ŗ': (48, 74, 124),
    'ŗ': (66, 97, 152),
    'Ř': (253, 152, 77),
    'ř': (3, 106, 3),
    'Ś': (78, 66, 65),
    'ś': (143, 93, 50),
    'Ŝ': (27, 24, 34),
    'ŝ': (100, 195, 103),
    'Ş': (20, 16, 20),
    'ş': (210, 107, 73),
    'Š': (46, 73, 127),
    'š': (15, 29, 17),
    'Ţ': (27, 6, 4),
    'ţ': (51, 27, 21),
    'Ť': (95, 98, 54),
    'ť': (45, 40, 42),
    'Ŧ': (102, 126, 171),
    'ŧ': (40, 106, 57),
    'Ũ': (49, 76, 129),
    'ũ': (87, 115, 165),
    'Ū': (159, 183, 154),
    'ū': (22, 18, 26),
    'Ŭ': (59, 144, 76),
    'ŭ': (248, 132, 73),
    'Ů': (50, 81, 139),
    'ů': (90, 67, 62),
    'Ű': (50, 99, 52),
    'ű': (55, 85, 139),
    'Ų': (185, 156, 145),
    'ų': (89, 76, 75),
    'Ŵ': (194, 98, 50),
    'ŵ': (245, 240, 231),
    'Ŷ': (255, 170, 97),
    'ŷ': (97, 87, 86),
    'Ÿ': (151, 73, 37),
    'Ź': (23, 21, 21),
    'ź': (15, 4, 4),
    'Ż': (201, 197, 178),
    'ż': (107, 69, 42),
    'Ž': (70, 161, 84),
    'ž': (33, 56, 35),
    'ſ': (201, 93, 51),
    'ƀ': (45, 64, 104),
    'Ɓ': (40, 66, 40),
    'Ƃ': (127, 122, 123),
    'ƃ': (56, 21, 9),
    'Ƅ': (42, 23, 18),
    'ƅ': (72, 97, 144),
    'Ɔ': (35, 26, 26),
    'Ƈ': (67, 48, 45),
    'ƈ': (175, 90, 45),
    'Ɖ': (13, 22, 47),
    'Ɗ': (29, 82, 42),
    'Ƌ': (38, 90, 47),
    'ƌ': (35, 18, 16),
    'ƍ': (202, 200, 210),
    'Ǝ': (96, 122, 170),
    'Ə': (184, 182, 193),
    'Ɛ': (24, 26, 20),
    'Ƒ': (221, 121, 62),
    'ƒ': (14, 9, 11),
    'Ɠ': (195, 107, 54),
    'Ɣ': (122, 134, 77),
    'ƕ': (45, 9, 5),
    'Ɩ': (27, 25, 26),
    'Ɨ': (106, 48, 24),
    'Ƙ': (78, 103, 151),
    'ƙ': (222, 210, 194),
    'ƚ': (90, 110, 153),
    'ƛ': (218, 106, 57),
    'Ɯ': (23, 16, 17),
    'Ɲ': (43, 68, 119),
    'ƞ': (36, 33, 35),
    'Ɵ': (46, 120, 64),
    'Ơ': (63, 150, 79),
    'ơ': (203, 159, 99),
    'Ƣ': (162, 67, 38),
    'ƣ': (62, 83, 128),
    'Ƥ': (107, 129, 173),
    'ƥ': (104, 93, 93),
    'Ʀ': (28, 47, 30),
    'Ƨ': (32, 29, 30),
    'ƨ': (78, 108, 160),
    'Ʃ': (151, 149, 158),
    'ƪ': (38, 51, 74),
    'ƫ': (31, 50, 94),
    'Ƭ': (43, 32, 33),
    'ƭ': (124, 203, 118),
    'Ʈ': (52, 132, 70),
    'Ư': (255, 163, 87),
    'ư': (72, 89, 128),
    'Ʊ': (124, 59, 31),
    'Ʋ': (250, 147, 76),
    'Ƴ': (5, 8, 13),
    'ƴ': (16, 42, 22),
    'Ƶ': (250, 153, 81),
    'ƶ': (77, 56, 53),
    'Ʒ': (77, 26, 13),
    'Ƹ': (64, 94, 148),
    'ƹ': (65, 90, 139),
    'ƺ': (66, 127, 69),
    'ƻ': (10, 6, 8),
    'Ƽ': (60, 30, 20),
    'ƽ': (84, 40, 21),
    'ƾ': (204, 102, 53),
    'ƿ': (10, 16, 38),
    'ǀ': (31, 106, 34),
    'ǁ': (139, 65, 32),
    'ǂ': (36, 58, 105),
    'ǃ': (187, 85, 47),
    'Ǆ': (51, 79, 132),
    'ǅ': (74, 104, 158),
    'ǆ': (207, 109, 55),
    'Ǉ': (176, 80, 42),
    'ǈ': (19, 31, 63),
    'ǉ': (221, 115, 60),
    'Ǌ': (113, 134, 175),
    'ǋ': (144, 118, 109),
    'ǌ': (36, 99, 53),
    'Ǎ': (41, 37, 39),
    'ǎ': (66, 75, 36),
    'Ǐ': (3, 92, 3),
    'ǐ': (77, 172, 89),
    'Ǒ': (51, 40, 40),
    'ǒ': (71, 70, 73),
    'Ǔ': (55, 33, 24),
    'ǔ': (117, 108, 109),
    'Ǖ': (229, 228, 232),
    'ǖ': (56, 73, 113),
    'Ǘ': (38, 61, 111),
    'ǘ': (72, 105, 69),
    'Ǚ': (163, 161, 171),
    'ǚ': (218, 135, 73),
    'Ǜ': (55, 43, 43),
    'ǜ': (3, 1, 3),
    'ǝ': (233, 117, 63),
    'Ǟ': (54, 82, 134),
    'ǟ': (98, 59, 38),
    'Ǡ': (237, 134, 69),
    'ǡ': (93, 193, 99),
    'Ǣ': (53, 52, 31),
    'ǣ': (27, 34, 24),
    'Ǥ': (44, 29, 28),
    'ǥ': (32, 23, 24),
    'Ǧ': (77, 45, 30),
    'ǧ': (14, 73, 17),
    'Ǩ': (18, 11, 13),
    'ǩ': (58, 113, 62),
    'Ǫ': (53, 51, 52),
    'ǫ': (228, 124, 64),
}

SUZY4_KEYS = 'ĀāĂăĄąĆćĈĉĊċČčĎďĐđĒēĔĕĖėĘęĚěĜĝĞğĠġĢģĤĥĦĨĩĪīĬĭĮįİıĲĳĴĵĶķĸĹĺĻļĽľĿŀŁłŃńŅņŇňŉŊŋŌōŎŏŐőŒœŔŕŖŗŘřŚśŜŝŞşŠšŢţŤťŦŧŨũŪūŬŭŮůŰűŲųŴŵŶŷŸŹźŻżŽžſƀƁƂƃƄƅƆƇƈƉƊƋƌƍƎƏƐƑƒƓƔƕƖƗƘƙƚƛƜƝƞƟƠơƢƣƤƥƦƧƨƩƪƫƬƭƮƯưƱƲƳƴƵƶƷƸƹƺƻƼƽƾƿǀǁǂǃǄǅǆǇǈǉǊǋǌǍǎǏǐǑǒǓǔǕǖǗǘǙǚǛǜǝǞǟǠǡǢǣǤǥǦǧǨǩǪǫ'
SUZY4_W, SUZY4_H = 104, 200
SUZY4_DATA = {
    ('F', 0, 0): (
        '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'
        '2db64ouN/3btnxd3y/nB+p8uRvwfWv8FXJ6CmA=='
    ),
    ('F', 1, 0): (
        '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'
        'ZsGncdb+lwMfWfCpcP6JBf8vnP8GLydshg=='
    ),
    ('F', 2, 0): (
        'eNrlmoFXWme29h0U9aMpkraxtQfNqVTuxIYGpjKO3oaYRoc6KxOMdTzt19EPk4qQT7F0mlTMJZpJ1GgtjThFqqIsZQkNkSiI'
        'wZxEK4IxRqvTtJKmaDXFlib/xN0v6tz0zr1rRT1d665132igp1nnd5797v3s/aIREf/rF46TJIn/whBS3fl86u2d76XqyF8U'
        'k3q7cud7O3empqWm4b8ciax8LxW0pKXeHn5mOG2YZP1CmOHK29/ebkgDPamVDQ3Dab/MLpEvVf69crhhODU17S+3d8L71Pc6'
        'f4HY4X9M3ZlWmVb53Q/Hm+N+n7qzsjLt9nu/gCL17bTnK19tPdBatWvPueZnbu9Mrby9s556TOrvk4+PZ+W7lrMm3+/ZU/1H'
        'SLq01PfUlGMqBediH145dcqRn/VwtOpqJ6R2ZSXlgtSpz++uWoy/cuqKI94Rn9UxfrUhLQ1y7jZONef/Xh/Nj3e4HPHxDodj'
        'cWLXJ8OVEklyKrWBw79KvbwDOBsrf3HiqmQ4ub6+cidObbI9s7vtFugBOUhPfEXNruPf1gskEmozQZ+2uvtmRbzryhMobk9c'
        'cTkqbn7yd4Gg/nLqbQprFb/9vODGZNV3331XVQEr/Gb03OW4TMFlSgOnTqvUtU3eO3VgcLCjo6NmsKrF8bBml0BArgafuV2p'
        'o47z+8u697OunBodranp6Lg5MTp6Kn6xRyfQCVaDaRSmNv7SH8/lOzquNzdf76mouIle36+4ufsyGcoMUllCZGpalSvr+vvH'
        'j++quVIxcfP48cHrNTVXVwMhQVCSOkxZJpDvpV5wnTpVUVOzWHGqYnGxZqKmIn5xTxwZigvGDadSxcH/kjp4q2Ix3uVyORyn'
        'HJBx4AsVi4OCTJ0gbrWeqn6Hf/CVpCerosLlAilXQE9Hxakr8HdV80u61TjB6rcUgfDblbsn8uMrKhZreirgxdUxAZIWO3qu'
        'rpL1q5mCuGGKBKmDzRNZaFt6eiYmJnrQyyKsm3viBIKgINRcX0kJyPL3+s7xxVs1NT03a3rG9+4d75no6ViEet3VeVkXDApW'
        'BZKnqKjV1frkzhujWUhJR0VHTQcSNjFxs6amSiAJBRs644LBI1RwcOgz9d9VdEz0VA2ur6qbExM1E20CSZxgWJDZ0PwtFYEj'
        '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'
        'QcT/nPXvqOmV9A=='
    ),
    ('F', 3, 0): (
        'eNrNmo1XU3eax2mAQNNOiLbSZhLglpTsyBhNtmQZmDXgCJPi6TRIGa7dFjZqCYkDwXRbh9CJoauAIE3lMg2p5O1A1qSkRiCA'
        'ideX8hJUXiodp6bdBgptsCn+E/v8EpzZnZ09x8D1nP2Jgke9n3yf5/u8/IIJCf9vD4aRJIk9ZgipNf80d27b27kE+VgxuXON'
        '297eti03LzcPe3wksvHtXNCSlzs3/ux43jjJekyY8ca5b+ba80BPbmN7+3je48kS+fPGLxrH28dzc/P+bW4bfJ37tvkxxA77'
        'Te62vMa8xm/vH+1K+3XutsbGvLm3H4Mi7VzeTxv/uaeop2nHzlNdz85ty22c29ZGPSb319lHJ4orxlaKZ97p39n8GzBdXu7b'
        'WsoxjaJTqQ8unTgxUlH84HrTZTNYu7GRckHa3J9mNS2lXzpxaSR9JL24b+Jye14eeG4Oo5rzL1evV6SPjI2kp4+MjCxN7fho'
        'vFEmy86lNnDYn3M/fRo4D0/F0tRl2Xh2W1vjNoxasz2b1Xsb9IAcpCe9Qb/j6DdtIpmMWicY89aybjakj116CsXtqUtjIw03'
        'P/pCJGr7NHeOwlrF5n4qujbT9O233zY1wIl+cf3Up2mFok8pDZw2r5HonfnPE0XDw319ffrhpu6RB/odIhG5Fn52rpGgjvPr'
        'T4l3ii+duH5dr+/ruzl1/fqJ9KV+QkSI1sJ5FFob+/lvTlWM9F3t6rra39BwE31+p+Fm1qdkpDBMZQmRuXlNY8VX3zl6dIf+'
        'UsPUzaNHh6/q9ZfXQhFRWJY7TpkTyLdzz4ydONGg1y81nGhYWtJP6RvSl3amkZG0cNp4LlUc7N9yh283LKWPjY2NjJwYAcdB'
        'X2hYGhYVEqK0tTaq5h32+z/L+osbGsbGQMol0NPXcOIS/NrU9XNiLU209g1FIGyuMWuqIr2hYUnf3wCfxvqmQNJSX//lNbJt'
        'rVCUNk6RIG24a6oYpaW/f2pqqh99WoJzc2eaSBQWRbraGikBOb9oM08s3dbr+2/q+yd27Zron+rvW4J63WH+lAiHRWsi2XYq'
        'anWtLdt87XoxUtLX0KfvQ8Kmpm7q9U0iWSTcbk4Lh1+lgoPBnGn7tqFvqr9peOM03Zya0k/1imRponFRYXvXN1QEjmzPlhVe'
        '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'
        'emznvwC/ul7r'
    ),
    ('F', 0, 1): (
        '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'
        'HeaVMnPCDu3xQwVYEdGrSkarNp47dOd0eH3wwdbL2d+jl5/q9QnNGQnHzKKVWB2+Q8X5D5bF6kRmetq7Ky8ePHT6f1pH9dps'
        'Sa3gG4duZaNsdHNnnPL8fBpUmL7WxbKnrv4WbfuzB/v/bPvHqtceC44HB9+l6WLLzgX9O+vU+flFNB29Nas6/6nfOmDXk4c+'
        'OA1aAK+dPAt/OX36S+CkQiVNe1MX5uwsQFgR1E+Ro7WqLB9Ah06fXV5+5c7y1dOnz/5i+SoI4tDpz/X6tGMhSXDQIaLFlr0p'
        'MO3IceVlsTQ6nU6l5+eXDT116Lcnl5eXX3tt+ezZ71577TUQ9smzS3p967Hs4OYlkXmlqOxg6N6OOKP5sSs6R4koH62yp07e'
        'WX7lu1dee+1QFuI98d13h162arWZ5wSbQdAbFPWroeYdOc4vAk7f6NDQEGDKyoaOPHfwk1deW37iu1988skn1Wd/f+ScXv8N'
        '9ZygLeEYXUSjxa7gO8vU20nF67OnXk/The1B68hzz/3+6veHwqW0TARJqi/RnU/Ys15cXLx+PyY3l/HkTkC34WRwv+NPiBOm'
        'oMad/xSUT3i3YX7jBUyr1zp0558Pc4rXOzrf8Qd3yHHe77g7SivbxmyEe0P4j9i7td9eOIEN0mhZqXs61ouTEOcakb0Dzu2x'
        'V1913o85l7bxYPey/LKyB1377vU9I9e/fkFEq9rMnl3fsud6KLSDkoA4SfdjPm2lFYW3ptFWYsOBgvcHv36p6/UXLnx7XWTO'
        'yu49Feasd47g2Xjk563bTuDkdXS+DmMUZHtZrKjaAWNOmPPm9W+vj0yNvPOpqDqrKftUTDhAMRrGpgDfGWe9IyYXBin4osXG'
        'FkFRra4W6WJjF7+9Vldx7YUX+uh9reVE/Ow2p07QvDMOeD3mDZjXwgv8BglVTTeLRIsCHHtnz567jsyqViw0MruehAIUXxdq'
        'zo44Vd8ZGxtbh+i+bjabq9Eym3UrK1BZReYqK2bFe6+VLGZSF1tD2V2zYcd1dFaEJE3+HXCS1tdjLn7qcMA0Ta+mZ/ZlOhxm'
        'sIb6DWSOtry1r69qcbEEz77eue24CzCdSiI16MTYGGR5p+aFTAcQ+qqr6fBKpVL7qMf0eutxbQm8o2aVjGb3AicGOa7zY4Yg'
        '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'
    ),
    ('S', 0, 0): (
        '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'
        'eLA='
    ),
    ('S', 1, 0): (
        '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'
    ),
    ('S', 2, 0): (
        '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'
    ),
    ('S', 3, 0): (
        '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'
    ),
    ('S', 0, 1): (
        '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'
    ),
    ('B', 0, 0): (
        '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'
        '7jhXCec/jv1iz56tZMEKjT4iCkEqpd2ZDjJbWyk9ufWfBQUXGBQ4KGFXj+KNR/ZMH/vFxAo4t+6+/U7q/Fx7JBqNFotvwA7t'
        'TiBpuh5khoJMPpmi437+SAxHSqAZTwhMTq/15fP56T3Tb+yfWAHnQ6Tb8fNzuXY0X7Sv63QQZFKzgq7TmaSmN/JT9EI+7zLg'
        'pHB2ycyayqmsX4xeymTOh/HtloN0y7zRauXy+Wh0CgEKdDptZjJuZljQk8WpYCGfw/yAg6uJGRKeqbbtN/1aY+CNU518XV4f'
        'nP3fG9/f+A7SYCBv25YcKQzThDP8knsnw2WSSX1u8npwpFp0pzGcZjQJE1JQmCsVqk1Knjx8jHC27VpeyJ/9+G/+9m8//p9P'
        'PvmLQr1en+/fvXt3OwPH0buDOxk6c7KYEubb2kh9xC/qgp7R3IxuCrvDNT/fP/+Ljzr1ZNl+euqPHxPOqcO8PFnpcPqJ4zK7'
        'L2Xu0JlonaYLjZlSob47QjimkMkEdviu+fl6oV5Awh0K1d8ynDc//O3/eufjj79JsHKkjh3u7u/vD1I0nfFbwf+gM/l+LVMa'
        'qlRwZ3BSGZOG38h7duNKf6FSqU9s2xbWreVU4h8e34a3/THftn9HHEecMZgJUpkp8OC3+elMrhGZn9+9u0CqHRfcEUzY0h+a'
        'VE9QlYnHycFYTiCAgzB++e7Gm3yCL/qWb8F5CfQgPejvb+iZUn87iMThz/7+nI4D5aXu0O3+/vlCRHYSTmG+Dgw56MtNWoQT'
        'iviblRI+BXuwxyZ8o+vz85Su1/sdYb5BMKCmdBSFTOA71UqdXEGI+jucXctzwvR/+52J+UipUqi34y07Mg9rMhnfyevTkXpd'
        'mx+BNwuTU8Qel9a1/nrByjWi4aaWOMslAhnq8a6n35noNxyA5pojjXhy+PrU9amcUzFwJyPPD1F+qY7f/JFGYzg5l4w3hvLy'
        'IF6r13cvcd7ugoMo/utEf6KUcBJzzVIlUooUCkbfSKsRj8dhSv0k+SMeTzaGapSDHKvAx/W5QiHkXOvovy7sIW3qXyYmeDkR'
        'qQyybLHPVv1RthSpVAqVuXq9kIiXKvP1Ofy1ECmVeNaymlbCSIaciSXOcvb85jePb7v12NMbJyaoqpMoJVU571OqVeUti6Ko'
        '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'
    ),
    ('B', 1, 0): (
        'eNrtm/9v1Ha679tx6TRdXSwhHxbZk1S11dkcuSMyrGaAGZVDS+NRqmOWArJXvlBFqhg8Aq3WGnTTSi2nPWrchtKhvZXY0dYD'
        'aJMchh0vqyIhOZXOcnaupyeNEgmXvTvqWuuCqG9p+Sfu++MJ+VKdm4Rk+tt12SXVJH75eZ7353nej6M+8sj/v378y4qudHT9'
        'mBDe89m8PzJZlliJptPWj0DJWTwo5cm/ZPPZyaxXzvOyJHWflLOBYfKTf5ksj5Qnyx4zWeZ9VpKsrmM8YEYm/6JpPfjH99hJ'
        'TZa7DcrZtuf52exIT77MTEo9ct728yOIp8sgy/ZkXx4ZyfbweXlS7vGyJu9n86KmsZKc62rWfD8LTtln5Ul/0s+GyOOkL+a1'
        'LgaUM23e96SeEa3HlmVm0h9hyqLt2WzW9rOaJHcLlMNNfUi6rGVNzWcm+aykeTZv21mJl7LdCwgcnpcmy/IkY0ue32OXURWR'
        '522WlRi2LDG5LqWNcLQeKE30ZHDMvOZrpj0n8tq7ksTm5a5xeJ4p97DZfCj7vNcTankvH9q8aefDvCSXu5Q4Eo/PZieZSYaW'
        'vTlw2DJfpkVPtFneL8tSviucXCiKNlPO5rURnpZ4Eg+b97K0iHh8htc0v+znusJBPHK2zGZZnmZtwpHyfsRBQLZfZjS5Sxyb'
        '1/Ij7AhDODY4cp4ph4QjarbMahLbLY5X1srSJM+nWfubpRxesyU5L+W7xfFHtLzUY/Jp6UE8eZFwPE2UZSi7Wxw5n2elSZMP'
        'OxxUJG+LvCh6Es/ITL5rHE3Ls/KIyZsy4dDgaDzh8JInE47VHQ6fZxEPZoHIoNX1mExe1jxwTFH2JHC0LnE83Dev5U3e9m1b'
        'nsSM63BEkfFJ3thuccoMAgLnmBdx3tVk1hdtxBNxtG7F45c9Nq9pJmZbxGEecOyIw3aLw2R5tgyOHXFGbCbPEI5tfiMzHsNI'
        '+XR3ODLh5CW0Odvm2SUcW0ZAjFzuFmcEnLKEsuPUaCM4Tks43zNMlziiROIpy6JJ4gFHyjMYqGQA/YLxfMbvEseWyl6+nGXE'
        'UF7gsIz4DRkMMg9Onu4Kh5cwP/Mj/Dwny5N4mCgeX8IM8rWucEyPcDDl7FAybVvLegucbyTCYSRt4w0uR5s+OGVtcinH73BE'
        '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'
        'OA=='
    ),
    ('B', 2, 0): (
        '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'
    ),
    ('B', 3, 0): (
        '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'
        'LHi1hQ=='
    ),
}
SUZY4_CACHE = {}


def suzy4_frame(view, step, talking):
    key = (view, step % 4, 1 if talking else 0)
    if key not in SUZY4_DATA:
        key = (view, step % 4, 0)
    if key not in SUZY4_CACHE:
        raw = zlib.decompress(base64.b64decode(''.join(SUZY4_DATA[key])))
        SUZY4_CACHE[key] = [[(SUZY4_KEYS[v - 1] if v else ' ') for v in raw[y * SUZY4_W:(y + 1) * SUZY4_W]] for y in range(SUZY4_H)]
    c = Canvas(SUZY4_W, SUZY4_H)
    c.cells = [row[:] for row in SUZY4_CACHE[key]]
    return c


def suzy4_front(step=0, talking=False):
    """Facing the viewer squarely: 104 x 200, hair from row 2, soles on row 198."""
    return suzy4_frame('F', step, talking)


def suzy4_side(step=0, talking=False):
    """Facing right: 104 x 200; `step` 0..3 walks."""
    return suzy4_frame('S', step, talking)


def suzy4_back(step=0):
    """Facing away: 104 x 200; `step` 0..3 walks."""
    return suzy4_frame('B', step, False)


def suzy4():
    frames = []
    side = [suzy4_side(s) for s in range(4)]
    for d, flip in ((RIGHT, False), (LEFT, True)):
        pick = (lambda f: f.mirrored()) if flip else (lambda f: f)
        frames.append((d, STAND, 0, pick(side[0])))
        frames += [(d, WALK, i, pick(side[i])) for i in range(4)]
        frames += [(d, TALK, 0, pick(side[0])), (d, TALK, 1, pick(suzy4_side(0, True)))]
    frames.append((FRONT, STAND, 0, suzy4_front()))
    frames += [(FRONT, WALK, i, suzy4_front(i)) for i in range(4)]
    frames += [(FRONT, TALK, 0, suzy4_front()), (FRONT, TALK, 1, suzy4_front(0, True))]
    frames.append((BACK, STAND, 0, suzy4_back()))
    frames += [(BACK, WALK, i, suzy4_back(i)) for i in range(4)]
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
    (('ign', 'front', 0, 0), 181, 240, 43, 111, 93, 128),
    (('ign', 'front', 1, 0), 181, 240, 38, 116, 90, 123),
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
    (('lit', 'front', 3, 0), 181, 240, 7, 37, 135, 202),
    (('lit', 'front', 3, 1), 181, 240, 6, 37, 136, 202),
    (('off', 'side', 0, 'talk'), 121, 132, 27, 3, 66, 128),
    (('off', 'side', 0, 0), 121, 132, 27, 3, 66, 128),
    (('off', 'side', 1, 0), 121, 132, 20, 3, 79, 128),
    (('off', 'side', 2, 0), 121, 132, 30, 2, 61, 129),
    (('off', 'side', 3, 0), 121, 132, 21, 3, 78, 128),
    (('ign', 'side', 0, 0), 181, 240, 57, 111, 66, 128),
    (('ign', 'side', 1, 0), 181, 240, 59, 119, 76, 120),
    (('ign', 'side', 2, 0), 181, 240, 48, 119, 99, 120),
    (('ign', 'side', 3, 0), 181, 240, 48, 87, 103, 152),
    (('ign', 'side', 4, 0), 181, 240, 48, 56, 107, 183),
    (('ign', 'side', 5, 0), 181, 240, 48, 24, 113, 215),
    (('lit', 'side', 0, 0), 181, 240, 49, 37, 122, 202),
    (('lit', 'side', 0, 1), 181, 240, 49, 37, 122, 202),
    (('lit', 'side', 0, 'talk'), 181, 240, 49, 37, 122, 202),
    (('lit', 'side', 1, 0), 181, 240, 47, 37, 124, 202),
    (('lit', 'side', 1, 1), 181, 240, 47, 37, 125, 202),
    (('lit', 'side', 2, 0), 181, 240, 49, 36, 122, 203),
    (('lit', 'side', 2, 1), 181, 240, 49, 36, 122, 203),
    (('lit', 'side', 3, 0), 181, 240, 47, 37, 123, 202),
    (('lit', 'side', 3, 1), 181, 240, 47, 37, 123, 202),
    (('off', 'back', 0, 0), 121, 132, 14, 3, 93, 128),
    (('off', 'back', 1, 0), 121, 132, 14, 2, 93, 129),
    (('off', 'back', 2, 0), 121, 132, 14, 3, 93, 128),
    (('off', 'back', 3, 0), 121, 132, 14, 2, 93, 129),
    (('ign', 'back', 0, 0), 181, 240, 44, 111, 93, 128),
    (('ign', 'back', 1, 0), 181, 240, 52, 118, 101, 121),
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
    '{Wp48S^xk9=GL@E0stWa8~^|S5YJf5=8p33{#^h7ZZ1g|(;G%=@x{UiU7Ox=xq#q*yS*<xnr7Jz`>N=4W`!1cAhmLA6#EusUjZqd'
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
    '7*V~@i#qgYeo74i(t%qQ0)0XOj-DUucH<0jy}$q&Fq|OW?I!-11}czso;A(8ylhOE8ivw3imwZF0<wj(qLRiK<=GBXgXyNd2U2W7'
    '?_{xB(`!$#%zaK)j8SkqCa^p9@L*&^;)dMIp(<RsjKa|U3jqb;o7DWvZ5zK(O>K!c;Q_)0>EB+iI%Z0S?mqF^@iM97qn1SJLUTNv'
    'RyfY-RdDA5aDp>sKHr-nvJZs0C7}&4ko#L;JFlbpeZ1A8lGtzIR>ecd?Ka{K`~&(%w`?7y>0tsRoJRTXU#XYQqEXgZ;*xAm4=xn5'
    'BLIND)?qMTp7$P837eK-G8xeYIN;qOUoUIwv<8JsRR5+$&;-kMq|E_nw$COB?SMXYroKaX+M25&XIwd|S`?YF*BTd5u0|r9VV5uC'
    ')DgvFz)gJ_*j^>SFy8)-Ax6q-JdE46k@-LSVSoRUy-wJwx01kNQR6D}+W1LW{k4of)1M&1S~j33|JpV0IkHO%2f#y|_30j?t^%mo'
    'wCSbHto6(ADsC2E<jf;L8WY=1TF@vVbHdiY02>8UN8%rSzNWN`hB&m$R9k0J!EV|ka;6n8;cueB#(zhn?rEGSk{CfP?m&MMHFm=M'
    'M+oiZf{TWqdE3QZW>}eN77g$HA&j*ib{){+tf&0@x{=!B4NCM-%vxKRH3T<B$dCVC269s_=SZ%c+g$*KaURB%D%ELoprT1zYbbB`'
    'I<-7K{MehD<ZrLm?D$1t-2mY8Pg3LdxOX-N)j<SQO%ouFDXfw-_1@(P494^p?owvJ54fs4|G}XGm%gvf>H<x=N%RpX+x$aU$*GPA'
    '#Za$-<s58zNel5r=?N~g$K<ZmayY!#+3|_f+p~X`{@GKI9f@#jAWz&XE&?rH<m+^AG_u}hv0>F#9^nqJ^-q_#9)rqX^i`-D2?*A|'
    'IW}yzg{`j?<2A{_$lVk>eZ$N%wka_8-Ew-yq7d$Hj24S+f*rPth~(is`u2UZ%XuIG4)qd74!4joo6M_2{_L(ybUMpARHmD$bfdNF'
    '_<SxVnHY)=2B_h-u$jfFN8@p$e16SZpEDwzCOfQz?+ndDP&L<^o9FdD97RRs53iRGQspuFGw_72SvQbh7cF&p^?hiWUDQM{iMi-k'
    'iQ_wF5g3nEBVxJeboSaCz#I=FiXi@mK4MWOH6`(dgI1fVPnMt^PZb>)oRv44F}@oIW#5oMp;XGbNIB2ZC8M-cL;<!hmsx{9A6aqn'
    '7%mln2bI|T>7Kcq{Susb?@DCn|9wOuv$;Wj^Q0#dSShKyw|9~DI9HAd^V0!KZ8vHv>OzwM<BmL92JlH=EDwkW+I^lVI39-6Qurb$'
    't;k8gFppgCOhnD-_!T9s;BXZcNE^(Pr$8M==9Y3GK%Z7tH?)GV)r`4#3q^p@2NxFmT|!t&-fyd{F^AKCRgsyC_5Qhq207R2UBYO&'
    '!Oo^x21f5_1a8aON4NtC_ijh+DAh@3sI`g?R{6`h1Vyq8VJ%~QFql6Sru>tu^vGT$0AGA;;MNh&A?p<iz7cl!0k8jP(XUPaFwvdy'
    'W7rOkpMbKg+x!u>a*rjc`hqU|IPQ=xj{o$>a9l^E4M-Yqhb^nBkwwaj^}>()5A=aPW@3&;bv?eDv8qhlqicx!>8E9eHYX$x_ltIh'
    ')|3Hm_b@i8NQe<FR>A3!M!m7^Z&8Gu@i8^BRKX3HAkDB&e~cPp#*0eoS2V6D^8^q&y&}N82_YV>lt-ukL=sZ4RxH7k=w<_hiwg}5'
    '*qtNv1LN%*xr2|l_5XhlNcPV$&NzItGNOHhhEZt2N^)bY?4k>{bI^Mgg0#{vC?`ZaB|ZGOPIs_z*a`~?glfTCs?n&px^4exLZdQD'
    '$`F&?ZD=}>dN1tg;2?H5lLn)}MRM|bx_*sdiK7bRA+<R7BbH)R3ocmdJg9{q|APh0pD1wFCf$fEvAB2hnF^rw8RfP2TFbg2VLB+{'
    '0{>!gjHP&!2<iwO>+iSQqO;fqc_wGNe6J%a-BTNE9m;2(IUEKznL5t>pv<1VF^)F$^E}5qyKVnk39ai?lln7Zb+e8DGF~<9^Tc;k'
    'B0yhC@iG(DrGFk59Rk(Ygn#$o$f0P_=pIsq32GqV<X=F^z)qR)Nl#c&FPauP3?v{9f_j`IOA@lUUQjd`F;^_d)*XQ|5+|X#qzx?i'
    '5z(Kqt7RkZmv-71^-X<J+dQ*uC0b6BZ3Rf<@SDTBj>!|f+QyiP>ocnN#mnnV*o()5ucahcxCKo%ya0$MP10REQm2L}QC`UOpq#Q<'
    '@zf_PDgu96(&!+AEwoyO)|vm3V}|O4Q?KxdEMXsr;o~wBajdK$V^up$!B>ma=_5_*qgUj7H7sp*2@X)&-s+L##s!h+afYR8QaEd-'
    '7PpMIPH0j|DgN{CbS&mlISuJ@ga0i);_q)31|~FzrfS33xUZBFi-J-iM0{&bW0#ds%V%jn$3_H&Q#Bwfa4TNGovLv0w}XY88w4Kd'
    '!hB_mq>#&qgAu;}%r_)~6N%#>Gvf{vpm7DUFlS>3bnz1vg%iKiaK!qq!pQ<(a~Va;JAquTUWMO<<8P0)%REKWhpgM6?rfPwJ~e%T'
    '2@*sV(lmFx)LRfR5|(TQrqPkbdCSZp`SW2YpX@obhr>50j}0!8K3GaA2KOPoD{Rlvl0n3Nd5)Ab`kPnyIT2n}&%Yvw7)I#_!&vdp'
    '-dd+)19c-YKd}u5-%VsK0Rm)NO?N~A80qf7QLB!FqZ2`3?4pX8O!mHuE1@k!_a<>7<rOsDjnVH<M%(4TM{w}ayyC;<=bsh)Lq9TQ'
    'l!dYB@}0okj<7XL8ngN#cH!QB?n5d=Wo*d%jWl;GtqQ79sLS91{K;i>?-y$OkmvmrW(db-lxkwmE31@}`=MtE7!DE9m-{uSpeScW'
    '3CSr6KqaWQ`=OGE5PWk0NRG6=LPQZdcp-P0JRACe1`D0{b%dx~%6b2X+EDS?Ra<R;f+S7^b1Fj|<@~kY?P&i5slYoRcBS$Q7fo%$'
    'xv^$vhfeyem~uP=c7z@9u*OD1On5>ZD%n?43#fa>i1JH^fl#DkF6)C7h2Cq}6BTqKUSi<yLa)$GR)>-8aR}B6U(*A`kO)fTia%8q'
    '(TqeA;3?}oY42S^o8MXxFlU*k{>V?wI|o-L@1rSW2-?!Q(lYz`eZyOWUu&G^rXKF^LHw&8iKJ)iUPJKo1gzPqlL!YBo$`xPV96OG'
    'm@9qza&L?P6f4I)#xEPP@{Or_EW3dPqIDQ6L$r)c+Jo8d4Te2qDA~<A!7@6<ypxQeEKc!LxQQ)?h1B2_Ky*80i+5tav10<nu|W@<'
    'o1RcOWwa}nFVdmy@!lw-GxXRP>ItfK<)KEns=%dzQ3Yp`eg)Gqloh=}H)>LOG+Uh9ZO2mELalVYflD|9;sU3!AtK4!eNl7ox5DCl'
    'Q5oL(<GFD;mmYH^%;(omFzw~tWw@ksm}9%qF>}^-e)jmB)=P9_YRsyP<(JiE%ERN_Sl$(bwsT`4OYuUpE!6=|<$6!*<I;FQfbenl'
    '^S#JR9OFhAtDXm@Lq?mhvJ?tL2c7;+iRD1zx8#Tht#G$YWHX_tb%QJ95&Vi^_Q%E%{FIvhk11N9r^1Lw=114Bui4Cqw|T-m7y5Z1'
    'bS152Dg+*kf>tennld=JxMvc~K1<|?q03*VQ&8~h&Id3-CPz%zX`oaZ2#FM*2qiB<b^QXz-ZmH}zj{c8eBW|gIsy0i3)uP%{z6gu'
    'aBCu=d2tyd-#p4l7|CEpQy)IJFAZtIeg$x!`oiNwcZ_UY5H|Y*>u8y=Wa!3n_1F4zHhnlyR7PRT-a#oY-Uz~ddJeu8KqS;RyIg_<'
    'akKZ#2w_m_@*5)sm;zXzb)2~j<G_D?Cy2D{G|DK-&ELhh@e(KD?K*H<+iPB(V}0O&Pv--!?<Z2lyYV`&0LeADI4Fe%jB!|j@`<`&'
    '7aiz^y!<mPkYi8vv=PifBwxd5!yxjWq6D-#I^D9ZRQA3$i%HET%(Ll1<vDv}vS#$LqU8uz(Dqm_(n+CZ?YjB+CTy@vop-E#OZ^-T'
    '<B-0$>4QL?ryIx^$yBm#F<yW)SmGO+7C~88M6zaSoNF05dZ-+YO5Y(O{M@(@-VH0i=BpIKKd&pUhR`*xVl?llNc4}m+OWx&_|9zb'
    '+BP8)_DLE0VV|+}<0hi7Kbel2H`El^7L}66#HA^EhlBh5HK;+d9nzhaWK>Npz&Nqa?^8~<(?1PnK=x_NgAG6^WsH^M!Ix?p&MpnO'
    '&wEsVb(T!bc`CJ~|E~rofS=3bVPz8uc}ZQ!SFS}Gn>=U-ae1b+Nbz98_>z)_jm$CiQqFGYW+E24$j%by72{2j?65?8IaffOPKj{t'
    'E+X4m5%L`ww~Q`3Fw-j=zvhb*zURz$e|5&_`y#gJmc=C#!xOv~59xFhP$YhNMF+EQ1qd#O^tKp;@(M}RK`oir`Ph95sa6ERKU;#)'
    'k+YKo>xNXJMAhYm9S6^U&d4OYMeAR||E+@=c(+MTpKd;y8n<>uxpu#vDQh~-0=hJ&6%Wb?rhe_Iu<713>@C*;n!E-Fn+3q#n5ZZ*'
    '`a=5r64)Vp?Ga0_q1Y%+RSQSY!b3xx+19JvmIv97({bsMo}AsN4|=`@i&|4=`umRxvNXPHe2V?)bpjjB=!UaimpS%WPEsk_Oj?Fj'
    '9zUm;TGobs;`vMka!^(jImo(|T$nef&Mb9-%4=*jbrM&8p(l>{T>8Y*-zntyzmQ?YGS-{Hq8bD>;+4}Fe?27E?Wy0d1mtHqoKn<Q'
    '*Zyek9Yw|35ox7?N5|L$0C;qGh4FV8a2}{cKgsry&kR}))hXoTN@KIcase7|4s3e&^0{Hc@*g%~eRkz<W=LWS^IH2Ur$ug8ID`^D'
    't7J0&vc&~=w5M%>paMSV8(?*BY-9K;>Yi77*P^_c>W<R*MGqPLEwuFLesIGa^NSz{YHn-oXKSk9@Wf+yn@L1Uw%u4`e%_H7meih3'
    'h8%8GYs0V5zs}3F|0FB=okA`@N<QTEDhViVILm~vjP&XdB4aK6Qq^ONw+XJ6PDri!%aCg6gHT?ti?hcM6+RU68H&u2ZT|(+P_!$3'
    'ehjb1u1^p*)Hx%>U3%%*F_*A6;32vO<fa}D>k1QVt^W57*4N>?t*LIzbJKbskD+tFLz|{z&+n9YwDAkkA($x<5&#y+w~G@e@QseP'
    'vtS1=U<I2PdV7T5ysPXF&?jVVbTzR#D@e_5tyWFnqZ7jOLitg#sAPXd%#<vO!CQcBJc(@JG)S+9Sz&-U!?(F6U(Y#t5R&A?sm1Uc'
    'vgn3E%symUVd&Km!V4zakGH#|>)CG?cQW<1Fj|EytNtNG^%_2=s+cYfMK$8d-{A$pc|P-PU564{N2M|)<?ik}E46Jl(k?#~enP|6'
    'Oi=F7am-Nq7_P*KFzu!5ligKqt7-=YW>7}04ASQ0j;1(5y>m4;6nJAk<|Vo@N$ZY6K9KbL$9SQ7=!^_dP}ZA`be!v99>`J7Mv3XN'
    'Ot3?3X#exhr>3tT4Q5p#xYQm^as#~$qdaVrk<$}f_{og;W-5&oh3!|>3bxpWWlzhTu7)%;_TSIspeV@suLW~Fx2_b(UdAg6vj=XL'
    ')o|d`$x43lPcX|Z@uuXu6@=LIahJXoq{vFF*HFcS_5m?|lv~)hg#HSo#HdNWH^%%dn>;@2&6z28@d}r$RNDB1kcIT(<}jVKF-|%u'
    'n8NycxcBnSLLKl`A~UIawMY13fWVtEG$GcbOKm9*wPNe4gwOeR<k9CncfoU>aVd--J;>GbX4TN!yIpF`qQu7{s6ReF2!+~k5(rW;'
    'NdVcc1u8J<YpoFeM#;kfdLPL{aWRT`^furK!+YQYc?+61EgtG@C>KHyzo-i_jXHY6V|U-4KH3gWXYZ;9c(hI*#t$#Es@6c2=;XD{'
    'X_W$ASVVOE_BvZbq+viRCL<yDK{BxdYY~Yp<CP5gFNW%1hWIh9Av)iYwAtv43)seWe^w;JK&fPD4R~@zVC|!?fFwHGk3;-ccp#Az'
    'l3*|fhl}qTwa@2CC`;Lfs_9<hirX51;&Vw4E-lGdrNc%%+v`wy@`>4rJO;hy_)%S|7md@8|4A<L`U<q1I-0>{a6-{ED2wQhncsed'
    'h~48{M9wWG*)HYrpsP#{%uE8x{5S9yHo6&knc$IS{T%U87MhXP%Ij&RjnDNK@m^!*`w`Xs%uMJT00uLFNX9;*=sk2e6fA>?uxH-{'
    'o$$cUt(GCnN+6R?NbB38%zNGujbUc+P1gGwl7h?e<1V+6r!=qLaQ>sFD}m^F+C)V3bfCI1V`*4>c><p*F)Ho^KgC#r7+c<+(R)7}'
    '@xr4e8_YlLV{rG_t3Qe>nIC0V@ILnnSQ{zx*&f4TDZ)4&btuv)EYeXSzxJzM7E*J1fsu0BYfS!V8_*-?*<OOmxsS7c(4k#+z7Wf0'
    'ZHoFL#qmfD9*m1WIXCLq_Fsll>`N&v=@6`>h<IEb!BplCdK@-va0!s!e?BB~3;W6%na-sb{tVzeu1NW3<p?F>LCrM5ann3xSln?N'
    'Ts?D&86L<;t2<IKmH?H9<cu67LJtLr!6-BUp9u|ityX^$pFqlgkKh28<<pgts`t+?-~eZFZx|9@t_}a71RJ!45V#O$3gupUMma5F'
    'pcqXC66Q3-msBc3sC8<QPLS;@;HYalTTrJ>=bVTwR#<d7RCj=byI&fgI|%HbjWEthvv0Femuqr$rxiW8-{??6Pg>SRz-0{2DG%*l'
    '(k5uC%LdMAu!17IXN>ZL=TSA1=F01EZ<+KpfHCI}zYa;=WcDj>Dl+o&i^HE9*+M9KI&mIP(juu%#)K~=;sdoa18LmZfwCO#grZdJ'
    '=}}8o*$)8PaEAIHb>@(&XaT;@<`|zEFW-A$ixtnrbcOT{sMX*u*uY)!8z{0gsT<JaSBe{(#J%2csp!>XgMzfoYTm^fu&Zqyoej?X'
    'EY;7ST%z6)B|`(U9Rl`q5&*hkKL4jQ<!mD;cjkOOa#RS9gWA>yW;u(-eHOLF;Q;Mh$gCmBBFUooq|I<UK?^>B;6d}~*}xvmowUYk'
    'ePT;=4r)jyuJvJ@Z?WYU=;ihB-R_hCj9I{Rhj(b_Qzg(jLe(p>g$U$<iQ&n3M0BDbfr#3w0C(LzSRdg4Q@JY?2kS9if(=lQ`P3p!'
    '+A-W>N;tD(^RjWh`U)h@tNOe7kc&{gHsZKBVMcc#LDII?|69FDk%CyWg~N2NhW0(Zrb6CYQ=uJU(mI1Q9Xz}gtFE-;ilIb;_Jtil'
    'vM=w+s@!baZEQXP7wX@_8juI0{niS+F)$~;`lhM^O<@khH^os#<Ce`^+u;%~Hr92~@99DLzrPSRdpJ-dH82c@_Zjx#cwwt%e$KD~'
    'rb`A4JlF6SP<tfRj*k-8n~YqpvKvtxUtP0>Q2xZm@)Xig@ES=022vniYKNMoGh}T!8W6ek9~~nWpXKp<=}S(#i`TtKE@`CB^g_T&'
    'xstJqoa^#w0j#~<{Z!<IfCL&PVesfGG;h%WCbLyt@Lm}_l)jFK_34l3j5YUv+0k^Am4-@k7w}?NMpy7an1)tQ`u*+5Du|$TITHu*'
    '0gNZ0Od08hGhg&1sI|ivV&KlNh=@B^HH8`fm|$GM8|aNC;0bn+B|yz*{J7Wu<=55y*bValCK;-N3Bub*Q<n8AWo2GoiEGka;SJ9e'
    '5P=UU{)i}mzhzi9cvpPku1)nH#7NZkGc!yr<1=kNaMsPBf|juj3E8#tO7^4Ta5a{7<Zfgc`Qum|T|x&G_@)k0qkemMNHWq+Cc(qS'
    'qXV2&mZ?Ycv%QFS!SiP<mjm;Fv!NgqW<dX_b05hgto=BAVX4Fp4_aD&?UtDST~gSF=f8TkZ8T%>#<jXROx9WfJv2jzrT`T4QdZJr'
    '>C0IU`Hq2ZA-6?)&B;!>o^Qi_IbRrc+w(^8=ujD`rBZ!a1+!&~Ad%uJnWB^I5%}Zmr2K+lNEQ0!s2^UIa<wWLe2D39*!lle220I>'
    'gfni^)}2ijNJeUdnBEX<9A)dB_RN%IZ8^AX8RRIE(el=iS8*c}U<NlLwiB_c7-;1roN~f9<MS?!3RrUs0IYo}^h(20@NaMPb|crO'
    '_gEXR@nW-mzzF{T-zeNjcHiW73_A9kAcdFbxrt9UXa(v!6GNq=$cm!VLAemh_}-EcFXz2y=j|AHyxq^X4t(ty&Oikb5w0{Q`iO9^'
    'Y7BbhAC>F#B=!Fl10Q?zeW!R=*lLzmTppc~yu^BZ-6g>^rg08c+2sN5!2Kg&JFn4}n_oc`eqkHTpN~nDSlCNBqaHS4`Hj-L1t4r)'
    'VlkN+FnPgIA(9%qC{N;yY$MSmfykEx!2ik9qvYmFz^q>JqX~Krk1Xu&;c8TVb6IFI*!;`;=Q@I1U$R%M(=}99)s{Ah$%v)FpmFrZ'
    '2<GQvqd9u+2Oq_VS*n(4MAU;IiO!Soa-K~M34;3XOcFc|0s@Pt|2Zg*;w6K(;`xV}-C4@dJfM3)J12uIN7wt=uGlc?6ET<x$Petj'
    'z3If_)?U6iW1NVdrur{MuF8~WWu||P80fu8kFm1%fZ$-_=p}yBf3*+`tQ~eQRksR4<6jq>zLtv~Zn^V5C9%uy@%YG2Yv>%Zoz6G*'
    '`Yu0UokH|+DC^fGtA>VS(+oV-euDV+F0S13oCx}Q9{TPg)3`{Ct+#LY9i><NCGd%)TP?EtES8%Y_NRku=YJIfl{Wzx8dEpe`QEo)'
    '{8&wQ=pxSOu)S1<#3bb*2X|#7X{o=S;Tw)NE5f-QI9#n6k9XBH6YLkbN}kie29{E=9j_HZtMf{2PzASytYfY9R*XxDGvJ#ke%t(j'
    'KJ78~F`{3?n8Zmy;M*m{T{lg}^787~Yl$39VZ<5izpJAc6<Wa>H_)_ILem}IEW_NG5{q-`A79Y3Ht5$_GsYobz<b%7?ZsHrV}8|P'
    'KAS)^F(EhNL%JJ3yf;C6_9pJ4Vr~zIKBm;dZm%<(owbMnm{-<|@sW3o3k-%8hf&&O-Ukis1|$N`_MbSubK3TlsGLd1tujv+su@dI'
    'e~PN!&QYHz?nyk6p0VSPX5GCV7|=v6&0D@|zmYMU4!+}GxE7>O!qJ3N!rz>lenc6Pf-xxy^5}xZaTlQAIJ&V42Dwq8IAMRO&l*60'
    'Kz8dwRKNO64%ODbj*J~}-;6~gG$3R>Z6n`pa<l!#rE%rE=pB#Y1YwJu)bk#%=h|)#Da$5%=WnUS`!ADXm)|7c<9!Xrw8Jb72_7&{'
    'UiLUYPtE0>z?p!Vrm~KmoB&L7EL-g>1$FT9BhTPiF#s)-_Pg?fv@-JDt2p}4RS`%gV1dmkBCVP8p1N$`Gp=sF0?di*tH}HZX_t5P'
    '`Xt+}dwT$Csu$jDLGy~$TEIV#-Id|FrD8r2cIC*qzYasIYt{tCV?~FVOy?Pz>S;m)bV35`V2wxd2P)Ltv(3UeprDfYaloDoGyWW='
    'SEsvR;SYSQmm9;EB@C{=-6>9b;Pz(1EO^M)*c+*OGT83z;LZGx$wdgCvPWdp%3}{UAB+Tf2=04gK&ZA*nU~H_nuNcE2*hU?@n8jC'
    'dP|%zbFT}Nc;H1b>aXLY-^3~0&*#k}e52cAp`cc|_XQ!hlH|%+;C?{2CGpu@=L=IUS8BGakObM7SfU~7A+Mh=%iKSpT_pQ1yf!5^'
    'pswiowhDFaFKhtJFK?Y<R(=A%L0sLmvAh^lD~z1~pMUB?GA715E1<MDM_Vr1|9Sr;r(=!{qB(4e1f_1~5XgUit(>URXT@^Q*5TV^'
    'R>=ju*VmWcK;mNmd~rOsJI68o@>-=C?j<PsC`p`90dYUm+bGMax7|!L3RahF_X1X%Bh8oDNUIQVjHBjy4nM28_`^Vd5f&y`A4x`2'
    'M^PHdR~~A#|B}}4F9w=ZymXPz%~`6eSd7WwZc-4;hj9bPeg2U`eWb>T$qb3)<49en2QJsOiL3)!h(#1&fKpqAx{k+IuKFNH2}>Pm'
    'hS%#I{SO1zIuwnZ)k|gn=Hi!qv50gRwhD|uDCy<p0MP?}h}+l>ZVJ)y3)T_1b7F_RaJ7?pGTg2?N>@S{g5va63luh0D)69%Jl^Sn'
    'P|CQ_iDYCRIeHrCwujEE-GqM#no*vsr)K@RWLFg`i%z!!9JJzcF*M9AFRBqxD~7!-W5#fMqQ=@5Ye#jPu+nqIFRnv0p`#~NoNq(0'
    'zc6b((YmI!2S1jU^qGdF@L<1gj4?RzwCa(!5)c*nqcC9t(@W!;?}tv-Hwu#NUjl-}YRe_<Z>eTKK(=RJwwdx}2#e4R7JBHMp+j$7'
    'N|}b&&ABtB0wH6(23n5$LjdE?xcUR}tRM4daa^r7p|D^N<`NZtU|lx4Ebq~v?;tpTyWRvbo_gwW`Y>ZO>INe&$(P|F*Mj(obRHK6'
    'k_*4>)3l=SMHq>9#M+e@rbo|PUUX-{Vl;5M=d%C=K1k!{sAG39*^p`s4|q{u3&|2OyA@(KMOp>@mR$HFi-Eq#B1NW>XEjkUB8-Ze'
    'fK<&TEr22pdgh<$2rgJQ;`ecyCdp#i07FXr{&LUyYZEM!%ZJueu#c0T-?u02?6XST1bf&n!d^p}NqHzf6((9tT8#E**YU<2QSS9('
    '(~}UORja}+@MW0*p!mHV<)t<2ZBlzoMIHV8x;_1cx(2lL*1R4LY#_D+OS7;Q#=Goa{p5G3XKD^+vJ|RZSW*B9_et^rxc^SI{w3bZ'
    'Y@7pF65zPG?&y$N5!)_W#h+7a$td~4wxKknk9|~ENRPnJw%UMNabnNp39aIbPPf*A^_$EL)hs|Wp5jJ!IG!nD+$Ia@IM^0pkCmcX'
    'N1l|LQ#XaBMpFTa=FQtMVBpO#+A<*7-KnKSXWS%e8-?3Xv=bp%t{M6A(1y}ktsN)O9$^2c<)Pu3V6+6Ir=$c5EE|E3xwu+m15T+l'
    '`oEqF9&1H^-Uz$?HB3n0+qhFrX1iO2akttu<~HY&_U=xgPY#&p#LOFg<<Op(=Hby9Umc{vTTf`be}UoYO-v?_COi2j*LxBj79!g<'
    'Cj~BcQ>W6g$%BOc)7&*8Qyq_p%b2}ZpW}Ocw0G5}#ib)dnXYDM`|0Jh{y&jL1nWC<d_M)hfkfxiMnPdp%C68Y`IMI-Wg@`uZ$RUL'
    'i^F%CgUy13FX*ESj#zU=pj^;xeULV{C#Fdj?`M$L8HI~VC--M(Q>_E|JJ3@x#=w&`sj{*|J~LI7EPJqSnHvhO0$Pm|BYbm6*MIHI'
    'YMkl0i<<He(L*h)kW+%6K}S$ae5|(n%3x^@rzv~izTNG*)0itU10*L>3L)vKW7yj3cFQ=`k&O{ezM6OKvZdNGwHny42YKrDxnkNS'
    'cR^NfO<_g^%Hg}45cr`U)mwRyh_3(^HBTW_J<P><pPEyR{)5>p7s$`v^d{umfl0axoH~%f60|EWVW+E;i(qf@rt!_fK%LR2jI;%q'
    'N75VVL@VL=ED!2>>VAZ+maEUT8pZWBdE`;<w?wD5_8F`HnI?gW>vi55jBE_Uuh3~`0|HW4R?2ckL5T>-DGe4`euizM7b?Fy2oy@|'
    '2}w)p6pb2b#4DxLR)%g7{uRRQ)Xm;COa`_4W}#m$K!0}NPL%)hgqA7NPR&*<w$ZT#?aZS*u<I$2Qo(&uDXx|_XBmP4DVHJ)K{CUK'
    '_E+_fl+OYxlYr_esHR-cip_P<&hZT|Cf1tl2nxm=Qpp2_0IuV6?ISPi<@6Da<AUkoHCTRQjssLG_zpnh;=%h^;CVy-i`LuAJfKN^'
    '>a%pjez}MIkGhe>vAvFa2T^qmMTQ6}AeM!g+2djr`J8Ar*-eO2-VDNL5tS6rPE18DDG0tEFfBo{S<%90Qa5VR4xbJ|4mCFlIZl!0'
    'V!zUQm5H*YFs}3cXR+^igdmJ#>js2l94fvEs3}79#GD3+L1RlGUhtEE$9Nqsf7dfT_+ZK36?jZ|oOst>``H3Ls7%dFP`&n_8E}HC'
    '3#W&@d|)hxQ7igE-&AG=)sv)nYIM{~ehva?%+}q2=)kwr*i_jUpAU^pmxzLUQgZY@djzJffR1qa_>yjEPS;~Vo-&W;+>77GE5b92'
    'cUjbkg6)0I?w<3~QzwI~B}rAma%%)@w8mIsR1;CMYtF}JLrh@UKUrHJ`)@vlY>#Ugb|3l#cfpVDu#I86eP#ZBiMm_prYnZ}IHRfK'
    'rg+uR<r+KP8p01wtgC2q)=+Ec`x8#d+2CFCJcitvWW6^oLB9OH)e?atJ40CLfk3AC@jBuaAGbL7%HN8r^?z^=Q~Z`wif$;-8>n=l'
    'l`U%y+;GhI@sSH;6N2Um@RptfWBiF+&6Kq!S7J4UX$I4jH_M?et!-DI0COf3Uwt2NV!Xc;N?FoWBPz5HWLQ^tb08`Pv$fKu15b+j'
    '!d%pc+97wvc6``9^V{G;eKh!0*DQYrq?EMEy$t^8I^_rHK-tu0L<B`KU#Y1~rJC~wo2Qv44iK*Vad`IW2=Bf-3S3Z=p6ID!)Ym}G'
    'sKn!EY@>&4djc&|49=MuWk;IQv!R&>=haoi#buuYpnXseSzb(Lq!-qiE@{hDBemO*+<b|Dssl*wirN9$U%_TYe^AiUeJoJ$gTR9}'
    'MYt)_3b0S&n4mD*E6TXFUL&Y2+vM|b0ISOx@spm_QEk!Fvkp5v=`_W}5#3=A&NMVG-UFwS&SrXlf~%0O5VvDYjg|P-0$zhKmkNS;'
    '5o^!t<O4?n(`%YUXsZ_W>X8aaH?w^e!5K1F2Te!=u5c1uz&$&^)WD)76M{hn@<r`my_}k{Aa)R3JW=2H(46if`7D+^JRBv=IbDje'
    '*BN&TO$ti{5!#tY-Vv^Tei2%E$c5Fy)XcrOUqHZ-LCevs!cU^^p=s}cDCvrbnzy2;>{ojYgR(Im429;pyIF1yY1g(%Cr+vzmy{oK'
    'Gd!oTe51?|i!ZmrZccxaRhrg$&bQoX<?J155^Mu8Fxq^=uK(3^sbH!EQahOFvZ+4RXPq_mKvhl-{&@)e=p*z`zqVEH-x&bTL~rU}'
    '(uu0T;_$vTF!i4+IG1lbDt{1_<sc~XnwTfK{`||>x~@qN<R0w?<@0`Y5>R$F<K9mV>fl?m5K7@?t*{tzRP>FGtKuz$BoC|+PoMuq'
    'PHI|+lIURIqe@T=nxd5xI~qFyVx9M`B4as_LT8`}oaU`1+tFM;_Ls@JENUW^$qS0hq(ZsOSt%nCQi#3PqzzH$H8)TdQ)_1qx=5;W'
    'fZ8$B=^Y9JS9WeQB!f;P*dSxcLLXmA&dI<HxV9?rE{2)@_OHpSzrfC68oVr}G_z*6&;UW4n(;YZx1gykM*)K+tNqxXb_Sc}5y^07'
    'enq@Yh0#0jF~tZfE=0|OS1IAm)lg#768t%xu(e@*K1JW^LoXJOfBbxj?#JG=djZT;0Li%VCq9{v_b?W9f<&%#Ox$shi>VQ;7x8u1'
    'hd9PW8!;WC7Tb|yE76GO?;np<9UZp`0P5bAT+6I_HC8NqUc|`?=|DBo{D@S=g7aU5S7$!T&H0@T(%z4ACEvs#o!T(^Qu5U6S6}3e'
    'pF-U=i+|;PDZ-_57z!sSJlh)xI7V7zwt@bfq#JwTOHznEW!2gIS@<b*bLK>r)OU$cM#aM8$us+Tpb{n-O5Ysgoi)Go^$`%Tb;1?6'
    'AsvQsl{{3Dv{WUOj91X31g3kopv2_n^e1jW6J;fSGc!r9zVmoy+@d|9Qd^IFIL#J#0FYn-VE)qjN}L?6g7n);5%g^I@1+ZXb@9?W'
    '{St#+AAuO@?u|RtxNfkQ1GWi*GPgEW6^Hsa8@AQL9Rzp$hlGGMe~cJg_T};-2Lil_W;PTM$<X1rzICGA9qE%0;?Q4FBi4ApHg}<c'
    '(J10O|E+m1gI^Xp{3!4dL%$al6@ZqjrBs|V{Z5qUW$!4`h`J_=s%6Mg29y<T<zj=}D^^trE*I2~|4CY$7seFmh4R%Q9O)(6PI*P('
    'A^1A^xQrfo+NUw^=ob9&8ie;Hg(ag;O$@?sUu3$51NO?nz9?wO(bl>kX67&LpyBfbl2UAf=dqsBfhOzL0#u6FThA{WN34Qz2<GZw'
    'u=UE?DNX-4tXY}o#!U=S%1{r=PqZ=b(`X-Lo^-Bz#14*CFUf!n6#I5{y?KgI#QMO0Rt(~i&O$J|kQ9hSA~!!6b9(uj)*?USU(zC='
    ')~4^o!7BlKL^bAnf!nN0G?tEjYHgOt?gvRYb4vx#<kO9JTY%iyp3(*=<4{f@e$QjO*aJg%7o1IuSXH~U05F{~4Xt3mFY_NKH|w~g'
    'iJ4V?yp)*uQOVA44f3M5r_|>0Q*S167at-q#h5<bk_yaBO5Sne^{|H_2oujtP^WviPS|GPx$S8vuYczchd&?VxF^50yDd=HtLGDS'
    'w$)FwAZ_3+PGfZ{wo?YB^%oe&P)v^49pP~2OD1Y<jQWd-f<5ZXA8+bD@)S-^^m9qt{L}|5YGo=(OIY@1*+S=MN!ht^=AM}|gtT?_'
    'SKqj>mbA83?pjtE%e1cfCpMe9C&cg^NQt-dmjGbI97JR=SPW9de4zFt$gW0LFRhBLcVuBHOQlgpm=)%`-9Y6${<VV)z=c!%_6~}b'
    'CrL*e%cWU8Z^LyNU7xAku;5a+G}j%{cfW@z9!gL{pW1%mtZ4`zzN%dCX(2|{9GL3zZ(|U4oqZjO*r{1;4}TUYzG>JARK@{${6Npc'
    '@*gbvQAU8DjqDAZc7QU2%RjpLd&`Q0n`qNrGV=r|&-Z4G9AIHP?xcA$U7LU3pq_F>8?&Gvslhl91Ac;|;8hM!hJ<PW?^y=ks};_k'
    'VvLor6IUG}-*Ds{;)IanJ+SxOy?|(~0y=exN0JwD+A$p%(Py;>N3{MvoG0=%M9>X)dTgm|W=XG&i4_W{0jl4$X|<R;Lb*%g$}GK8'
    '#Mwr_d9br&Mx=&_v-}~mUO<+Ar!TZ@8D|x61Q|oSx`g2Q=j#Hbb%KTJMyyvadfFW~l&25t-h}KIq!d$$bH8gLNN%YMDGuK<U-4`c'
    '6Hnr=;mrKU#@g{bBf+0_;A^_(wFZ_hqZgrSnL+nZVqM>*4Ct1FX7aJ#3q|niNSo9~54;P5`~SoFmk<9MPJJQ{lTMGk0()T-s?@IF'
    'XDSO&t7B(Lb0h-jWT&>J&Cgn~(t3WSWkP33Ibl>Yr(qWGpKKBIf_gXemhLdQIHHHm3GeSZleOCI0#?Sa+z`z<XtT<M#vV?;Z>2DQ'
    'LExjXvP19#Fe5#|J-msm6lt_YZte<eeaS0RP-5(i*iOu36GDf<MmwE`iJVttX*ZikFvQvz^kR!v!SMnHL+`ax0A?=WIPGzrV4;@b'
    '8yn<R{#1|dn9%SI#!UhtY@+Mf_5geZ-O4VyGP-F^hv>3Oz0vo)T|ubN&0l$Qaa6%q*JMO#Xivn(uQ2?htMX_sU@9V5{9*dhTk`Ob'
    'BkjFb(&&D~B`+5MXBV9OFs#+2UAWXc-<y`@=I&LW*hk)tU}PVWlWuuz6^G)0?__{!!<^Rz(H~{sWqbORgT@1wI0gIamx>C~tWQ1w'
    '0a3hX9!TSTo+_BefB>|BKz^BXoODZBVbCmF!!u(g2`5JqX;6jif~-N;T;Sj9<sB(SaqF7T7t9)V^4uQNeqkzC^zdpqazB4})&&qn'
    'Y>V=231}FoJ5ozEuDRH%atPpXp@qF;joDSKx(($$a?y3C)>R&MlO8&a6pPx5$nmvyga0}>r@hk3Rd4}5MI9NZe9o{u_=^gdmQFQc'
    'mKh>76qM<`w31R4-%ep=;N4G4ng607|CBL4t%wA%0DB+gXsO^U+uUcr1tIf7=C?=)=%9D-J)J-iDwvw9^h-52D6Qw*Diwjhx&oPi'
    't)}hF7w`NK;S`84KZcO4Dx-Q(e?)t=M!Xkyn#l5_uy6%mqxl-3fsgj_>zDHfo&z^YV_G&eww~@ZWn89S&22ZMAI*2l<w0Q5qv(G5'
    '&GY2MhqeZxk2fO;Zo%Jt_7SzCz(AI-fEx<gP0Jb&Ay27e{PdTgWu>yhUrF<_28=@B=J{c>L$C?%nRwLJE5N}{#P;-9s?x*(^#lR('
    '^F1aFpqBYK*VsgymrD20aS3LUt_oXG0Je+1Fg8(;))Qz^r<Hcx$i8mmeq=*P{G<j~gLnExvyda9DWm#z2L|;_HUsIm#BF48B&xkg'
    'wG_^l`WiBbPm^hYh6!iJlqWQ%PozKq<^kec0*SVx+i2?8TruKIsj^;?cm{-5N!$v}g&EbVbF=%@IJLdc%%RcGu|`&~B5Kbm;n9?j'
    'oFTWpzJnxAvbAdIsw!JSnHUJ6j`2hePFSY>hO9zv2{7&wu&^bpB}u2x3sN~kOg-CdOk(w9c!Ql4)Qiyv`8K({zMNtL&^c7SrQskF'
    'ht~*8W{Pk%)~bMAadj~ni#qG`Rs1w$Ld4$fi6qt6%w+^k5HbO`ntNLWgtTeGSlssBL0g+huGrdKUpsnN%XUrgp6U<Xo)b9W{<OIw'
    'o-q%K{t=$Hl*{fh)=7I53f<Gu&~jAxV#s)6-9%diF-Xc`mNkpLBaoqO&0JzGSjB94f!5%W#RuO*zadmxB(H$Dsv#Xs+i)FINmMC{'
    '=O#GG%8KZuJuI;39(Gw=eZ;PTgIdL1$Rq!8!@|0$yUZ#&O6{jyAys2IjFamJ4IRIyQ-A%c=v!wO2=S{dZ=U&%VgO!^yZ2txlO;dD'
    '+U5T(HS6nV#8sY2sjlPj;eW>S97gbppdCQ1+)!z?2}po>rGu3ch+?<l6CJzRYPsifETNr^5v=VfbMRxAsDDEnpRj2u5Q_j8dfa)}'
    'Rnv3hO=8BrEIS>#&4f$YP#$JQ3wAH7Kw6BP=4L84=ImZ2v&A(P_U|-dVY=LESN3)X;Uv=(R_-ixl<rOcEMM(Z(PSTZmU(sKWLvab'
    'nwSRa3TW)n9H>Vm$XkSd^TLD*PONQHyy+0mm(MA2;V3LdJhv{#<jeT&XGe$0+g?tr$xN|(ST>!=RKs2bqKwy=2tp>QHK4G=l6=it'
    '>|X~G<)Q(6TN_po$L~X1L_fv%^@nW_nCfurH`6d0469^KY}9-Ae98Oxdhk+8%7jJ!jowav8TYU9dGGcxltQ+%s2+kBH&>t=`FS+D'
    'IMQlph5c{GaG(grs`D7XLbY04JCYtj9r8OC&o8#-KP=0AQnt<~L8+OYBJK`{Xs?=T)KYH!>!%mJ)8F3$w2xK%d{s7rzY$<|F;W$t'
    'j_QeVnLD9Pkm+Od7OqH{TXA$MAQgW`jqn4j3QUjAueK^|oMDyu6e8C~7%zJZGa`D_@Ln~AKZrJzG4;*cWe51r{@k4%5&VHTF+7gB'
    '02&<Z{OA&yQo|rIX~Df^7Dk#VEU#_Sk`c%3xl5^a@{AsYL@sYkgI%v!-MKZg4b5xzw#)BDuL)~ql;Lr8TAp3G!3KMMev<s<Q1b$L'
    'eEJAi-!qe1@tvgODW`745x+m|W1ae`d|mSSRo{X(6VIb5vK0o+JUGNkV!R>Sbp;z}bfo1YgOosF;WMl1^(Z(qi7Zn!|Bf1v0tFDk'
    'nfuy8&0tFY>RaH`jS@2a5zMA7u)6(AuLg(=e2;Mb!DG^%c|=mbbFEJ4`A$3)(D$(12sot{9B%=CJU)p368JXt&Pnb7v}R7Lv4t^b'
    'K?hW&X>x>-&@<at>C4qqN7L??fZV40JIc~PvSH2*IF5wy`h?@<4h>W|m8O`*M-+&ZNSA@8uD!jRB|dEYY~_|LmjuH|A1P}(FQi1e'
    'lE^Yt(?GKeT;L2<RfOz@4dL%l{7RDK82ABGH{)n|2<S{cq>v>ZT6x=Q=~c0vYa@b5-ZiXJ?5p7|Gzl9ICh7piZpfY)tx9>bfQ@Rk'
    '17{Cj_uD$-3&7~6p=jGvo70fSGh>?g&p8zMs?F9(NSV%pt*I&^7*;a@E!PEss(l~709tVJl}xT{EY0bQ60%Z!OGP{l3cEI<b`aJY'
    '&2j^I@k=IqFI1@uh;xV)TZrALAa%XClQCAI!GrO{h1#-Krum)4-k?99j}vwm{J4uU=+@k?W~g~)qMtoBQ&+6mh_-xNLOAXEp&~NV'
    'K%@!G=^TuixtWkutSEhZ))^hm*)b+i3dSoM%Jmvn2(aWL@nBQ4yPiY!8<ZKb00OISD>KITo8N6cMA|rxn)r-~qO8i<-1j3?r#@`>'
    'KQ2@iSiATx0XPXDmPWwzh?j3G#|Fe=v{;___>~a2p0g&(DFwWhu*d1Lx?!P~q6W4O@SZEjjxDf1!So`b8@<f8_RwY;mta=?`iu5M'
    'u&UE<#I1RvU0(j1R$KG*6MH`0<xytP{d1klAL3&4{|JM;sql2{CzfwBVGPLyw|KK?LrDQQ8j-83$DqX*xXk<5{_}D_p?Sy$Frns2'
    'zedZxi!8|CN8c!vf{Da-!ai_})c7Nfo3mV)CM}10cuk&aXr^fnNsLK9vc2cZN9rX5rhzj+;k~~fnE>&uScGKa(EZT+P1-CFU7tr8'
    'ow@X&J(80#cp*vEtS$E(U)96jR0j;8*h_-+VqvB&$bu8E`km2e$baP8KYQ%N3#lt{$8b=!N*&h;&_`T--;_CKT9FZ3gcD|H$|-r^'
    '1g!pvcPQdja71}}4j+Y5^pFsEx?)n8aOtW7F>vhkKv{H;%hxHlUg?$_+4|r2kw7<Vs!4G)e37jIxL5t}2Mbi-#YL&&mwD<moqEjd'
    'N9u)1s|&A9T)Y+s2@1CmjCs*7Wnz+oHWru^|D<X^$dIb#w%jZgF=H_+Yz3KyI~@qbsBOX&_zTwAV`_@Q&$G%1=4$@eV~pMUq1xHI'
    'f0Z-j+bkWVFDme-ikH8qkT#i+&XUf1LZX%Qx*i)>^hcp3;!|D=Y}4-93tZPh0~99ALjH&4K)0v5g=$X!lv$1HE$f_@Pr(V%ohopf'
    '<)-Z{=OnWW;b7jY38(j~r@L4wzxdXQYPTOxZ=80oZiKh_FJ9&m^ETsC<@AgKa`4plLft-e%>U#;4nEiu!SP0I6lH^X`2hLFhdP-D'
    'Fy@R6H*DDsbvg^{h}5w+JUeNRB$Lv|#^G5RSGM@b3U+Q(tLAlK4RJkNNg5ET3(6d@iXp4Cv}~GS3p7>nDVqOj{2lF+lNNk_(S}K)'
    'M)O~AJW>NLemee*w%812F~>?oJGik%*jViNU6`blj5Q;K7aJ>ESM3zLnz|GgNGHZv=5k7N^((H%YIP&dyN?$K|CNFz64VahBT@$W'
    '|5xL8IU44n)JIj%`twZIS3aKwL7CfWTGOQ^Yw%)z%WZI0{~PoI8(E}ln<xj}R-@VF%jVzQX9jHW!C*}cp!jgYhR{@&An<_L5CMwR'
    'F>&MD%;%=lZy&^&2>_!OtmB9}1%zxMz;O8>?3Dc^)!u<Z>-D=&g!03VnfQ~egDo(6W878j3+b-#?vW`83--AdA9gJ+>3na(%Mb~#'
    '&J+tq;X}F@%*4YY4`*|$tztS67@!jg+pD_&y6_%>g<}^iL#5Dz)&X1NI$+Q4It5dMJ=#kZ-W)A+=Z=*sp_@Nf;OTs++x9jE$2>o_'
    'fm4&4$4@i*kDf837LSuTjxF!#+rQ4_*y$PQ<TsCHi$n(ZBj)4L!|n>9i8*HW*tYYoak+Tn`vDLsy4qS7)7Kb_KIlNkX&|_qvlFZ?'
    'vW8_|5fy@}McfpQB{0$q<cPdqm%*S2Qn{w*tH&1(r`8>cYKaLu6|)t(;^~sNy*2C$_ZOio#D`X2TdsIY;fJfoRyx>Cv5(l&Y`w5q'
    '?70mbWCOZ~!7D~9J<O1%XAqQOuTGKXJMyPGL7TGvH>i{~y+o&=t8p~PizA#i^0RK_VkraO8E2}UI~=M+k<XFmnfrbkp*9uLrzG#O'
    'b$ye(l4m!nu5yXZ#ccKh3kc}C-2NS)$~A(SJnZVnM2mNBx$Ek(I1LtBeYrGNjvPqN_^_zx@cY+Nv+7vBAJt?YR@Hrohz;RHBP9*z'
    'L_g!6g(PL{7(=!UB{R0d=ft)jEQ%jIar0?9X4cVCedpgcst^%0r!+vhCnp7W+FRgCgr8hq>^odydRk7xJSo2>gC5U@SjhZ!1G@p1'
    'F`x+DF*XaM#836^CHZ6^47@&~oNZfk{cfM^;9*2isq0xYQ(tO^{YC+#-!WI{Z@*b629&eY-N-&@n+)vUDJFMd<3;2Iu5`;>8+muf'
    'gDsA)>`#p2aZ_undd{ZO83^dHWB%ztb9499TrXh2B)Z@m08jxe#+GIA#O&b9@{yqKhomVj0eN9YdJ~IUot{`}^Zx=da7&Ft#c%Ix'
    'i4?eeD{xR(I>6&m{KhYi-yfx-^w>Ls`AQaL&+7rsOP=<uOOLyYc!e>AjgiKkM0U>1%I<@)ywQ+2^35TB$y=%-=G1}1o(QZ!Jm%R{'
    '5)sTsRpW<Z@0gykVa78KpA;h`G-}n!ZWI!7itsc1m-jS<<~Al*3$7h{sW_QD(1V8GExD1iKHQlu$33KDHm3h*<F+^wv1<E_-z^Jm'
    'iJVWeJ|$48%nAq?-3NdSQ8K<h6Mq{ZY%y*3jw@F*=d06L&2ea|$4FE)oreUc#4YoTrWn-4ns~tLB&}5l*477d=&Hzkt;A~y4uoq%'
    '(I5i7B&!45atF)paK1kqKeC%|g|EDn5EIYhryjeTC}$Gpcwt=v4P~OX7!vejy*H_@>n{2JTVCApZigBoPsoG){W@9xCuejK)odYR'
    'u$+3$WshSRLQRlox_%>kHnce(y3hRv6~ui&PJ2Ta^Bs$bHs`mGnp(aILby^h<at|E&Q~v0Kycyf_T+hV9kc=@6ossxm?Tj${{A(t'
    'AO%6px@!0`wzR#<`OA8b@FTxlA-7;2QZ|t#1T6KipoL!mmc>VeJBF$^qDlvrH*vD-4b(mfyyH9gT~fK;n?;=>2ji-)@3p)?^~uO{'
    'x;)<m7QaKr;)VfF#vQ~~h}q~>E^28Ew|y0ZbI}{7O`$mp2X1$7JGpoajxV-1<8^1@1ceWwkAbMIH<@~mfgs4cG57e{lCg2FG{~~i'
    'L|14{tIYyRdnbA7WmMpY7YQe`lH4-h$Nx-JeTl!ISdg_;+0zAcAef=IW^e?R;lQ6k3doP^Fa~Vek{elK@EGR()ThE6n&-NCFTy9V'
    'MKrI~c2|l#oPoS8K9h=E)kI+LgKmqAM9r*osW9nLlQ!T8a=r(W_R4#M|MT&pqH@o$P+@rPkNGT$CBfHzKU>q%VO@r8mNySwV^6qT'
    'DF{(bDp(k$HMZ%3CX4Q}oVS5)>H+>cU+QJv)o(1>DsZ<uh(k1he67{vLuub+<lL=OJN&Yt=<F%aJ69=PrTE<7tjfYl<BgdU2Df|W'
    'fHMm1p0(2#cgzf?!4y}-+fVjbhKKbQH(u?46w2`)1c~zB@|KN~SBbl8dlr)hTYD8CdGB<NtVkmA$X?C^hn4+|j2R4BZt(_2$_WlT'
    'P?~;r$U&<76!E9c!-!V6W6L;1s=m0F2x+u$dJj!+MTtK)f(7RM_bEP5iVZs9J*}%y_hFSXTDcu7Z2S<PosIMlk~JB(G(>!pE}~OE'
    '1%*R*ssMvY3j{l4P{DaSgGeGPsOePAhRJny6i#RJh1n9|`QCs7e;0O~Ood1)Fm+asV3Jh#22_CVm$T|(g0#OKaCyyp!D#?(kbUPQ'
    'kH(%3E}p+gVpFeCCwsT2I!w&^8`skXTAN_BR}u$zzGnZVB6lZyq==Dt^F!kWC;lw5z6Nug1AR`?3<Bdno~@~X<d{oWv29zQrvLsr'
    'CGmn_1C})AG=Lj4hejAmGZ7h(mk$WBF6n8W7+-P}0|La?6BJXk>~E(<IY3?UH}KGx@b$IKxGH3v)u1kJ)=%<aV-U+A+4B=i?&{Iq'
    'MZur?*Gz=%59QGeJ;PaJ*m}`Tee!cLLD25b{<0+j&2-a)(Yn)G#h-%W$9X92f36+IY@~-51?_|Vgl}{StlU7WVGu|l=364<cx+;G'
    'l}m@J&KQigzt%W`_2iU!Xr3YvuwV&2JC+ucRMT2%d4e38tG45<`MusqkGF|fHu$S|+R3dH-=NC<7$XvPS+#a;#D&L|?DoJ8Hb3k_'
    '=Vf|-u}rxDyT7QEU$<8*oLOL|gtwR*AQTCiMtnL()^~Rnn*$o7v|M{EW<4rwGeVeF{}`G{R%VZI-f89-=n(N|T`$B%4GW1osqNym'
    '(k9ZfX8%u5j^>apofRwarmE!qNEM9w5ILwnRv^&PXpg$njs9~f+^C3x-fIyiDmc@1Z^F*mRI`^m;Gp`8u>i$*FmZZ#5jZ5Uq5c*_'
    ')+%;BdMSk-;O$8n1hxL^O{0F3pScbIVbPk_$pZC_4=GIm|G*a#yL|5A3xV4w%KS=ok$uHzPXMd<QFW)V(#g*Txs8WGZ8{Y}0Oo7C'
    'r^z#k@O2XQz-3{?#>oy!XA`FJN~}59Z^GdAuD_syFUZAAKw5HmLf<FQMRGqJLRaV-9j0JM41e@NtxWDlCOO(k24$6Z`2D#)uyU$N'
    'itMo49N4}D-+p&Q7QBX?YQU&(Ym6dS4bDt^OvxYAu>#_X6&ep&%8vMe4N`t(&RqN!f$w3q6OM?sfp#^onB+@PfgH~w*_ZJmz=V^l'
    'IYQE~vA$w$DG(_(@G-&2xg|u+Zw1w5eQEmGuZ(~+j`g`7)pJsfS}o+!f((k+X42@i?Ou7X>NtOZn7bpHpTQjr+XNCr<pVA%?78Ap'
    '+BOlg^rLw&Ccw0oYncuH*)Qvf=^VZcy_xMer^OuxL=SacM~%4{*>e6Y14NwcR;?<?z}4(N(TLvG;)z~Uvqo0sk|Vzghu;M&GycOh'
    '4*syn5!!fg;;tS;W2;vu^LCrVne_AE7-3Mu7vOCRfUI6gNJS~S(ljU`;)u&d>*^`IjOCQ0XaTzMnzXL}XM2vT=Pd?JH<16sOBBA5'
    'BUC4m#*3PHHW&L0S-3FF9@cv}pFILJO9^eUc28DMpw}RMj-Z0&!+5zh{SMk<pL|D6hO5)(+Eot7RI9vUGILZeKO_z5#onhTt%pcP'
    '?@*g+Ylnv+Laey(226usUCI5dXNXb$!_-0RML|Fcn%tII0_roC=it`*ph4B)c9fFE{arI^L=%>#&)~0y&MBV54M-KZRg4<0Ub6)x'
    'O9BSeGoO1Xcddz$lD00j2>sjC)h*=b;EED4Ok1oNf&5x7mQ}huT8>(xkjOwHN+uS_Qv=x;9+CPQDvcqbzOIeZ!we(AZ{zJ`?#>&5'
    '&^H4TV&Y#lfQ>}*<B(glUxU*zK&Ug;=*{6ro0}r5iA#G*z*FGL^86y-QN=I2e}o&cSDbQ7^;JwKAr-e`p_0&+ZbeG*^Kac3VGnS2'
    ')O4s~>^*Jun!EE}V+*VhijTcgTcJDt5kh(wlvo+En_kyi{opa-`JQ1K9L)^WgVrSmbgg+$*>>rqqT)JL_WWU}dBKM#M@p<PF!w&g'
    'B}P->(S{OJp1$<O0znVQfi&ch3tp~gf9#MmYx!aSE!-@yxqx$9<3;Ew9T04w2Yf-R8vLN9hYbYnrPNT@rLii$@L$)xVs?s_CF03b'
    '+6#BrKn&})XFHr_dJtViwDIBHyVQ=b*c;SeSA8rAW?UwhI0bfp2EyM2+T`-bV!M_T$5AyZ7LUNFN^*uOrvJ}@hDcVNUy@jBi?fDj'
    'v<{ZY8{6Ck{$$pvzg|gFD;Ny^i00|4#sk3710m3Ugf39LFoBFvXYObja7yWipS4yJllNftTS$TMXqP)RKw7vJOj~~4+o?H^FARc;'
    '`9{Vq$m@_VqKGRuo4*{Wa+5!QgjaS<%E#3hi+lf`&(8VpN87%QP%JNVsff%?yPTtwIRtO(UK5Vr@q!6wxCtM`t=xRA<xxsa?ma%P'
    ')Y6KtyTSZ|R_DQ2Sba8r0rBUyQ!MVGbyUm^S@>KZ0o1QW8_Fo%5Sz3J(a$d>*p_BqxD1Zq>42J~0?w&CZ~<{#X-*AjkyER6%P%WH'
    'T3L#ZG|&kd&T$qdw(!`W$%Ic&se@nObhqZQP9}up9h$=}wfM^t{qKObgsJngyIY~~V-y)wTtEj_yKWJ|JB;OsGeX&y9~B1y9YOh5'
    'LH)+<FVbdr^g-MeV_Xi1<mxnPBgGjn5Nozc>!e3(7qc&Zqf_*ZhHijn*yD;8CB}5bIi$7KdjR1ndA>&Oeu>f=-w;YpPz0TdIqv2H'
    '^GNCWq8J+j^M+K6&L6HBA$0AsrrP7^-S&oL<=IRT`T%@+5RAn6H=P7iPk)8X%m!mhW|=<Gof9PFnIS=#`!(!UeTs%Nx^d`%PB}-G'
    'AH6;H$|d;R@|5v5mX#lU&a1*2{Q%o)$RxRAfgf=&+csd!H{Th_SCgOplJDI!h>Ctlp<~sZ{Dc<brKYz}fW+E={<j4ONrvRusrYPr'
    'O5>e9n1A`yUdaCg@dqc7_;QhSi*2p5mnfp2r@h78A<tAQ_CjmL3^r4OS6DLT&fKK%Lb9VaQm`0*bp8E8FDyz-i=!Xd!Oi5G=w$tQ'
    'xx~8Gl4&#Qiv39D(ws?E^t;k^$`D1VQh`X=-`x|y6Vn!LL^ZvYjT_kzGnV&x^~w*)rO9lKhzy6=nJE}?05}MfE&7g0+=;TTZi-Mz'
    '`ytk|{v9b{0={M{M344D!ejZ;O<}dm`iw;P8-0|M{?+&G&r~&#4+vO((3MVmYq_2c?il`J726rAe;u}~8=nH7FqFeSwQ*e`aohn<'
    'N}%627Vl-hA(BdjLrL?c@l=wN3n4r?JZVR$vr+-LDw+|-7$LQirX&AvF83Y~t@}dvh@4!LiyddOtODHK6t;BS6=3%_GCn#~I$<;u'
    'cNdLyMZQ`IOCdvj3hr>jPUzyoKM<fV%fMQUo3yZzVPb=&>|ouuU@;T^(hXw=q@Xd1zFWgVo5fP=BEa8+s95*3Fdm#<JO1b|7(Y)!'
    'M=CiEO~G0rN94hF+-=fJzIw4$g8kwoTj(5kFTFz6Eq|*%SyiuLD0&K#9=!DkhX{PnM4;q)3@^myp-;m$yAk;c|3INc$}G#V94-Yp'
    '7S``geWs$r@;Ds#poJ$Eqc~rq*50k-?CLT&l+QJQ@qL|D$5G5--GmgzzV68C4I#maDsF!phTQzU5HxHql}l#z)W*dOP7XHx$hV}w'
    '%8>)`KdT(?o@9U2Zp4<c*OJkl-ZJ*p2WZGh>ZL?vsG3U54!_+TzN@HoUPwtFOmpe|#U0nHn+QDAAc4@a#wd26bf<t-GUmNnNpo8H'
    '5#O~%ZG^1)CfFvS@a6zej2S|bcHz|~B17PWkbYjKL~jj+9etAm4TRznTd*92yofkQHWpJ=GmT2ri?E4(&p1s9G0VofM#%XDC+;OP'
    'A{X|_@v^}<w`1z5{r>HTICT!=uXL8FI>>A8@1dBI;ZqyzA}&oVO%R4r=D3Zc>Ae0o2dQ>PS#^2C$D0LgvUyjqJ|>8?u>lnF{pYW>'
    '6KdRW;F0UuZ>4g@7(b(iJO`#gSY%v{;^<QfiK~m6sGxCiT@*HG)i`YG3EA6k5Fi()K;Rs7!Mw$$IlulB^iCi0hQteThm!FE=G{2R'
    'P-~eS<-)pd1Z%}73SzT|a2hs_8al03Xbxwrbt;K(f4q8u{6XG`qWWtLa?Ja^1J}n6S~~4mU>Cr<s}-wx<M^W1bsT-TN~?GypnbgF'
    'm@;bgQFWcRWv;P_<Dj79Q+K|SaN*Z#d|tzLWrJ;psW<Fl?_rEBj5`^GzRV4U1DE(cc6cY~n)y&x<PcEpQ26#sG;|+H#g=HG_?9g('
    'x<aSwotn&kZ`T&+C5=H^9!JAmJD!F$UL3YX7B}*CQA#4k58^Xw--zR}a66{?e~CIXXJibN>C-_tk*%~?m6=aPa4gTyqq^!ZmsATd'
    'lziBPs$)qwGazLk==Kq&A*eagp+d~dj4N#U=t0s>32Ll>t>{(wKYd%X6ogJ{vNH~2VvGacA%<B)Ua2q-ld0_}O=ss-)8^|&XM<wN'
    'a#~7ZI@bkrjK`aDzJp(~i<}_pvRaQCSmTXw=uUVgB+HA%n}O&f!MU|P7X>FJohpo56;drXBt~y6Ks^tmo#N-~VkvGLqOY+%Y63j`'
    'Ge%={4YxsM1bS7PRm9B=bE~u;3BB3oy=E3ufl{J2YjWM8C}ImV+(Ubq|JdL*Hq5gB7s->5alYZTAnMBP1pk*l6OeAssd`R%i{8T!'
    '=<|pxpTysH1ip=O?ch>uRD#odi^3=&eQ5<z(|R?p+?=_4O=5GSYG=s4J`s1JkjXsdi6lg<%RoyY3|yVWrTHHn^q1?u13=<lZ-C|n'
    'M;{?L$_dTVuAM$WF3f4_wFJ7Eiv=w^l5|grRYbv+8#IKONIbj{n~UrG@Do!-Z_CYG5QWjfgDtk4Vkr3rn~*4@G@g)T)hU4tl)>vC'
    '=+f60ZE@`8Z9yC?p*kOP$!o83N8Sva36x`#H?L9HMSNnAAc=zBRjAhWdW}ciF^<T)=A7C~5;$FsCyIXs>VG)4rmJ4tAW2O(30>)V'
    'Ev3xg`lq;f2Tz}ua?!ITsxv$x%EWq0@s3y{h)2x9=tACJv+sgk>lpyK%g{;5r_iM<L(qELWp<OkX<t*VUw|J$Y)EZr4NYQ}*CrK$'
    'v;7pMe2QQssDQlK!U-nF`>8Dy9fYigV_=(Bs|#+V{n^o#;iRJK4}O+7EL|mqFw4eVPQ{$Q6!k4tIUDmP8L%$bk_O0XzG@?E9-1%v'
    '?Wkuki0>jnCC3)I1DEOD10~sBKolzOeH?|MhP{BZh{7z;obSFAks+>pZ;k^TRl(y5e_e$NHbSz*1Qon)V6AnHa6i2}_i&_&9}QGq'
    'L$Cd~84zz}c@r95Ay=#@k=Euc1BL^suc#XV6JY>r5mXQBhGxt24yZi+SBZXc5dt2nm#>R*!ND*s^BnMQ%Fy6o&?9vrF%o2|TQ`{#'
    'a6seT=PUM{X`;IYmJNiRnl3v^KQgChXHv-Ix_oO>h6c~?Aee)<+XtISzAm2atm`)tZSz-Gn=-r{HK6sa-V_INdjZY>+xKoEec&gm'
    'zWT@l-`LJCS8-DV{v6jQ)(%;^9H|R~2Ft6tZU7%G89^E<+Ufpz*0@4dV;0~o3xT^DYg3O5g}Q<B7>y@~YC`tN!wC_8adL$~oyH~x'
    'xwI`7%&~NQjVgwM8?dN3@g;3t_p}BQYP8h`VaG+;prPR>ghgd>-#|tW%S<CzT{U3F6~Y|G@wz5x#yL8;n`#^53KmQ~T=W%-03e=='
    '5+Hhv_5I9C0aWmiDj<sk?MRJQH|s3L7BktCsBjVpXtt+=vgv{0Y2l4%8~xZzvJjuj1o94%@hhW7VTX{SEHRTCrm|Z8Hgm{y9}}rl'
    'ioxgP>Vb&eVmM{^0py&4z)`F4tn|FrGcEPr9Ok8kX<8>_)GCx@8^C&7h^|2$HeufTR1pV!hy}!y{zn8V4^Ty?<<|79r^uMcna~>4'
    '=cn1YNM#28;2~i=v6Dbl!SpDf3d_lD^}$GFx?!#*S0~!xy)jtnUnPpHYRCkgV${OKKy#uipj7??5WG{~C_+|AWe+y7Wu1OjWBNIo'
    '6c>>FTquDW{q#ELXdkhrwlN5kqP~G&Y(B-jn<Iu^XkK1?57E>C@X?YYylUs8$8C_DyMK}O^m);*>rE~Tf=or4J|LwK!oZJ(9|8eV'
    'r}1J~ES#PyWeZXSqRpSnfkW*fe-_SAF~Qi<Vp`Xp%_h!_#O5e>pk%)cbkBPYyp6`39c6W_7f7xxtoxE6J_cW#;N;<J5Fr6bv2wXF'
    'p<Uz{r~mfkF4hbkiJ~#uuj%q!N!#)>;(liMpkHr8)t0dSGUC+Q&Mx-ivz*tlyK14ZCSgou1Y7Sv>7f)uMx8X6WUJmByUref@8E91'
    'pw~nfM?~xFSMdZq2X%}(){4R-Mue%1)=yb+hbpOvm)9Yr-5cyOkD#8529fDS5aL#X9eG?+jgR(g)4=QvY`HRI03cI*$Zo|Plh-0B'
    '!sDvu%k^aoYn_La%*4vD8#DgXq4o^(%Qz9I8=vU_M5SPkw-OD;LD+ta&2>zfHWL8<B-w}6i9v?~9P#k)_Wu<-3r`OXIlM74->2=g'
    'k5u$_tZU(Hkl)XP?@`bPiPD3;vF@J+%N@?((TG$z8~}}aaKOdCd-ggToaf}rs%9V?@b=X!A>o$|jz}IPI8J)<*DFmID7y;JHY_h7'
    'DEDsYc=1!VH$iIYN4a@ejAWrbMJvj}5@K)PMU+rK_d+$Bv<mjUBj^7dQtTC2+$HtZJlIX#ypGEizSi&}*)4*(l;{0BAyh^hrcCsA'
    'P<+5G-ADcD&kez~_iUwFQ+MvaC`zSSPsisqr=harWej4V9*r-~TMDC6{`}n~64Y2cclM2|)7NkW2EgCoof$@q(LSAsI8TryEJ>z|'
    '^XC;N3@3Bg)2hf!sa*mj0YBLQ#E_0MsB`J6fLSr#%ebrMXrpR8Uo9PgZyNKaybEm5CMs$fWZq=6myKiyEpshF1}4{{C9L~f4iOQ*'
    '<1^cieJq$3<Li&F%{@S3;{R>~07F6O#8ZA{PVG~ctFGd{o6A2TiS&}v>frxL5(oNqNngq#r-<DK!|WOfe?X^S5Uf9I*jka#V-L~Y'
    '`cXtky-U)SLg|x}(gM@#hFokqIoe%6IH;}Z(6|Jln`?@ivek)Zy^{1QPRAyAVIJgJs~%$dPHGhF6EO&Sx68Jif(as^;<PG|24Lxq'
    'F5`ec>=_(2mK?s8Vi9G&5H@e4za(9s3!{<(NNsaDTP_DX{I0Bw;u~%$$QG8{B44KyLgBY&N=Zkdm8pET2WPf4UMf|ccV&g{eDl@k'
    'b?;$p&Y{90H2+|><z2vqB~qFhd<P^#&i22pLPK{+1K<(YHnFAd`BCvjrvIexa~8@$)3foLz6%$RH2znJ<rQ)zJmg#USvY_LTIbv3'
    '(aGaP@e3L8tCE)u6tCB>GGs61jthQD@ahX}%&;;DJx3Hi-l&Q3eNyU-B#Ty{{6o1Zh8qm|;0l0(6YdbK_nF!>F6T8|w9TyA>#8)i'
    'G*p08Go`9V2<#!weY6>)^Odoau3L2y>Bb&@uMR6g;c$c9oW^)up1}DmsB;4;#m9Fc0fPIfK7>gi0?#KCy+8RWS=)oL$45D6{e}lm'
    'dONX`f4D=h1KUM(491|MHmtltPuwb3JB79cVGo$4v)2H1&HzXV^YYIUR48q4K&QO=8`Be{fbEn9)R2Z6DOdvEzpOjX&7Uq~ygao-'
    'gE4Zg;BXCTfjFr>I}M+`zec5alU}as*#gV@ks^4(*P-PzQX*#hw#+FuAIncnXF}qLz#RiGQMR@oC&qqv$XAz?$L2o6_2m9R*oy-l'
    'Cm14CF{Y$Y{Rpf`@y43VF|_8Q=ab6*@VDGOsufmb|ESUqhI}8I6&luOM&>)>)u_NxXPk_Ls^iXxW~=RL5IB{9yq|W~X<y323f0Dt'
    'oIU3<adVyv2K+&bf{Pw}U#HtL7Ggu{mR^eC6pHh@Kgu4G?zFmkr_>r;*xj?81iF}`{8ju66M1_UBF6Q^Kx7ia!?0{imec($`vd}8'
    'zMWqaX+gegUzB{g(}66rrYGA*Tb@H~L$<~Y2;1YQVnyEsTFi}wsEObIKEos1se#dF5W1QUhmdXGQ+S3$TV4@`n{b*z+LjYDc7nZ!'
    '@v5Sg7}i1LOw%Yv!R3av`6f4r7{{5=()U81Ws9-u9+^22V{uehRZD+^8wUA>A)J5-*39`#-=+>&L;(hV)xwqNh}INq<ZRxFBpY-H'
    'g=wi^TsG~Z;Z>N$`?}wn05+K3cP*m`Y$)*H^Dm#wg8xfDOkV_2^J!l@$vS*ImX;@dFyzQK(@4kJvO{#(S@^pLm?b=jbT%)vz_F>|'
    '7RXleguL^-h3rhey`ds?lq4GW3wM_%XvcFliJr*iGUZO?0`c=y-1JkzggY6hhMGx+S_ydxaWx_E>6dE5wXdf0(*pnIq)F{P7|Jb7'
    '<Oj^4YnD35R(91V>zx#?gL&VRO-rXa;%m{d2X#!dPcAo$QQ#R`2f~Cg6DGK6ED3-Mv|nD_M)1K~e>~zff#Fwy<KiDGak!VF!sIPu'
    'Kr01H|32pgVu}e79C%{%rp$x8u(%ozh|jpNdO6arrEI0ojjpX2cZM0CR5;xCP^~I?a82~UZXuybER}cV>E!xhsj3k6o_%0r=9v=+'
    '6AwoEH0FJr!`szNLT&fp#M6Us%>iC?69iyudjP!G4acz4s5i{*7Vt<M1}#Tg_@nLjT4O%cll|;#>Uu$sgpM8l>_i2{-CnOD=ffP*'
    'Kh~lM{J2UzNGNuFuf$TUALrT3c*-ijqApY5KRqL)U5`A?h!L@XV`$Ld*8SZVvHg4!QX9u$hXzrAixXw+;lu9jk9VC0<(6E(lX!Y^'
    'YxQY>XT5dRot#n{<YG<8?4P2&@5i`YD1cJus@v6;Vvx?>Q@HrBHex)r_7hs10n0z;N*|)zrJ(erstfp@K})_7EJ_6KU_wd3IWK=)'
    'HUa%=&#jCcrOeNF5Z}?O*44?g1~M&4xY(iZQ?P3q)My(j6Wf~gESf^;dKv82PSSq`%m^PtT9q4krQX8C)l&Uvh)@{LKI|-{w|qHM'
    'fbZ#HKZ0j<HVSHN(avsk43yh0+s;5{3Q4XDYFaA<77FNb)42gS6)l~dUg<=-E&+T;fJ4bb6TD<o+|YfX0a^mRJfY=zS}+7wfMS^?'
    '?dJqiVk(29m(kF{d(<YysGj!fL+;ERQQS4FtZ(YTx?Z^eA|$1h<m{%}9$u}LGIoIN@fs_V*Lt2A33VdF<&htcen7j&3cSX?Q#KWq'
    '+~<2qGU=uIhSJg9{cB0+)0~P!t2G6)pz#1_M7G9@oj6hH-15E&7=!0j1|Jp@KmlYN-U<P{y;%`&S^HqoFU3ONW-eK`<>&YLQxC>9'
    'buEu9#dSSUw*e_8{L^Zi)v%<H&zOLOc%Z<tZD7Uwf?Wt1JHizt+xAWmjmkp+v7;3Y`wUk3E#(%5E8Rzpf%Xs!2Snh_LudM;Xu6Da'
    '$Jyl}PXdXGJhjokiI<O9rLM{7<#}0`ngY0<#QZc(SB~Tgq9r9qltf$CTE!T^0PId5Q<f0|>*`(6TqJE@x1)8s?fJ*6kg{2Z{56ZR'
    'E}sAQR%3sX3aLXNrF(<>iQgsQN<#&AMWq^vx5$)Z)JC+-+Z|L)Ns+%j&@)yal&EoB7;n0typs$Oiu;{!Hy1UiK)laq10Gb;o!4Iv'
    'Nbv62Lkz-J!TX1IQH(CIz4vvk{_Wt9OFs@tBr@A{3Wzxco_~VnT$U9-8Z-j;vJ(>t8UD+qlB2|Qq9*QeD)YfL;=R31UFUIp_-j-i'
    'zL!bUU~SQ>t1{3*U#O|Y^^HL}H!QMgFc&xO&M#B{a40c%dc9|0>gL$s08e?2KdJI|2evrpyOGsFxef2LQp|CfAq{4JLyAO+QGy_Y'
    'KNz~vV0kXnCwaq@+RgaU-d+_xKdJY^si59_e6+^BX)}U}+4O_2vZ4TPxm+}&Pq*JYg%>}ZnjW`VE-ndCvT<<sRJwPQ2}X>{w&ZZF'
    '?0u$nQlqhH7;Mu(LzqQ>xrUq8$x0iF*A1meAojUnmDz(PKMHf9C9hNswK@vSoYP@h7f5OK5;5U*)VmCr`(6P?zI`isEZo5IW=EPA'
    'HeevAv21}_%rjS}1tLP;DBUzv?%8BiZ>1zO5l(8ZhR!fx)uXcP>N!ZSFVs%fT7)W-DymD?Yiz-?w=HdGVHsF!q~P@9Q6^*xpP03E'
    'C}bSq7a>3=VP|yP5UXTihiiXKl-h=(PfZ4yf%RaQ@1&Su=cT|W*P;O?CzGLDQ1xb(^PR7TdyZft1eD8D3i9ZmfmPW)4FN;zW7E_9'
    '<gK{6Mrn`jhvMOouMfDQFF#fadWVZd^t&TJ^=4{ocm8!^VxmtG2;1F&^Wuhn?X!=cGqr3?Js(dqIsJmQuE;&ys)1NZ%h8VgC0QGs'
    's~K<qCDyU_0r!STgeDWY23?2^4To*xC*O;kk9gg%D3Pu(e+vBxQ5$vE^DNuT%+W5YfIr@Y45S~3-Vjm*&8G}|<O1r##`3dxM?&;o'
    '`j9(TZTS}yuoJAEEVRgeK|hJ}1V1N5LzyF`;F$8l*wqs2p2M2)cyzQwF(ZE2c7HE~=@2vF^ciZ?CaWV52jKX(04EllU%8JFHpzlb'
    'O~o8a_{{StZO|g!AZ@Umc+9-rWw_}k+YRy)yrIFa5v-H1{RwL(&7~UqMbosZ$fKsFrQ*w{>Axq@c3#nsdtip)Ke7$nan+imNCwqi'
    'YkiEmE69OeGNKKsYh66)!6hn}KB&Xlg|~+M$g};SSU1RZ@JJXt?6_LQ$JeTml#uoph~XpTkEOxb`q2K04FjJ%h|u*!T*bi-e4KY+'
    'IO_d3IuL^GzJ%tTV^W!&M2m8CPMSHO&?BHT81Z?FKp#$ra3wwf0->mB4|26OFCm9oO5{2R25lQI^GcT4g*-rspg6k;Ev?&6ZyDs~'
    '=_Putv;yR+uGoToTk<pe5;50&&SrC5RUP{Gb&>H_RQdasT<XTK7LCEz@UqOfvBYKM&;Co-dZWn3a1bnx{C6jvASGr{4YBDEQ-x|~'
    'k2qe;O;Sd+Y!_3uW~3xF^}?aI>KkTMe}u>phJ4;w-#P9h%+${Ma1~*K3bgeb&uTQfnv=&xbT%tF+@_RofABzFn0=a)`j#_XSx5@I'
    'QqfEV=?OVivmf&IRBOaSBd>{Z*U1F4tAUD3NXNrHN5_c@4_SWKJ5LLM+))=xAvHDS^G;wUs!*P<$nUa8Uf$iYJ*PbhgcjgL;r50@'
    'abf&9XmpvC$|E^%UtLbaD2*BkDi2ObBo}98y5vXAny9@-n{tB>$LkLTwjq!Yx1RTPCNS@u&h)xjIpK*9{I#1)i@_=CXPgQ-XyftU'
    '+gKWF(gw@4wyvVY>5(#Y$ltJCm2uMqXcHr5PKFP#7107u(?L?JQX!)y5G3%EP8R3TpgAvwU$Dg3M6Nfv>hO&p`<I*LOVc&U(09$x'
    'f3p}`TUWU|Whe{xs2govAuEZSRc#J{(}9*Iu*Qy~8)yOkHlV0Nu18n_G<^@#J|LJ&Eaw@Ngns|bNhNdfGLgJ&gh9~}H55=HmAjY1'
    'yoZfZaS0C52WTiJWx?IK=Wx$)jmy*{CpMQ?Wu}(*d(qY~RLOqpM1Y=?OM!CHqkqCq@DS+AMPyT9OV^BNOiuS&hi<`+5R9M#r+c=3'
    'h9jar#O1Z|2}2Yv{<2oojL1g>>=kz0gO(Lf*ndZB<So`QKYW=Kv8-*zGma1c5m3SG1r+h~)&ORpVD;sBoH&MydjR9HVFufey|;a8'
    'P@BCd1o#vGw6MG$7<FgEz<|_s>mJ}p>99{LPk{uWIeme4gQ#1!7WLB{xnKUK;xWe_1f-ZBF9xL#zBU#a@?;55Jy}+mBJ_3tyvh7('
    'NaX}hu~~LaGjFDtTf55XQAIy(HKYMm%(?1}=#Ps@#uR~cIF~umuK<k!k>8vUL|A@tqX_;wmOC5FJ?`J{Yl3;*AlIy}8?i7CPaN*B'
    '&r7{?l`X3~0_Qvi`RDst^QB?@vYJ(HK)sZ2S&*uB3q2>1N`PxEXy#h9clgf>cMXl%4$8ZB8U9BkJ0=$7nSSGl0R2``x-oI4L=%|H'
    '<yCF1aV*_nAv3SG2*G)vGHm60D*58h`))M<(p_Zy&e--0JIYaf8VK=4ZO}`HOSz&0!>zryjXi?Kp57_4S05~BPg<@JNp+W*b5R;v'
    '_1ItrF?=G@c(yG71?6`+oz6K-*RZL@MWEd1jyRkekG3QhqUoaV>*~mRqZCw`LpU+~%z&dg(R+({Nu_$mvI<A^TwnuR$W74soUd}='
    '+9eigqaH4C!A78bMEVfmL#s}RQ?I9waZ+o|)mhJPK7l86%~0EJq;(cfewLmIv9UylRM`9cejuRO%qB<6P5sT|_&Dq-IU3O98bss}'
    'pHF5BaCuK1msVsSIRt8YE9mt|)o>w>QA2BtJI+Dh)mx<d7O9RlmF`2~xJU}^R%>6+&-hRmL-826Un+@mv>J^{BQu?qyK3-3a0$+A'
    'Tn(x%4wDL&eQT0s`brQCX_KD6^s*6_fAqxNk2Z@DzkE}Hog{3&GZ}mAdHGXI4V(v4u+H-3u3H-oGdU>8k2GCsW(R_aRX#*QbF5&?'
    'Y?(`Dp2BON)yp!=_oi!9XO>o|(%Ime7MoOgM%DQJP0@}mX;(2<aodOpr`w0n@4{Ttv;^vMbVW|5Wlh~di(GQ_%895TN&jS;XC=L%'
    '_|!p-{4feOD=z?NQos(p9B!&4SMp5Jdz&8YFk<((fcjp3DX0Z3mV)=0txe-N5cj%;hcL$0J5rCQ0lJq`@%AkvGfpO%=9g_j0|sM0'
    'cSi?ur(H4C(RaJ|sAdW{)!F3mEZ#B=wf<WmIs4$49K{cBtJv1{UK>60sb%7=AqsaQj7A^pnd;ScFeGIFwZ=Rw53-G3_@f_>N2$Dt'
    '!fS3n2joduv~|Ql9B0h9R(#T=SpumvdtCe`I|-M|PEYF-hEbpMiJDSzpQh$Hp)SUq9&RRGl&9eXk4(@5TmBL)k8m}yu~1~3eAto!'
    'hbY2{F1IfZIMu^oT<va2%NCHL_C}iLQ-0Gij@Y7{Ei@0VM6QZPBI;|K9*wC0x{jQBgq#(gyCaQ4pJu-tO<|og;23HC&(ocfRc(|G'
    'zpDrQdm%QtkND-rfR(0l>@t1ieGS@%7;a^jszBNnxPFRC&KrOH<vJT)<K4`Di&gS(RH!#eiRbC?enL#4Qzs|0mJ^l#v(t2jy&QR)'
    'u_=SrXcE(6>XKA4;8qx2Ku&0^_2|)r2?69qDKlFvApHx6A@;|jH(1k-uW5(d;V67wqAHh6Vo4$4oM5z7=x#e*3=9$C&SH%;w%uGN'
    'vpm$`^4T2-v{9&++p_~%wLfMJ-<)4EgK{J#Kt-wF*i>g8uYbl4Gih12Is_Xg5KAW3M`ujx#-cwh6obEw53D?_L0(k_*X!Op7zBI2'
    'Z2N*6B%rUPU?D43%m>SwO!F&BxTt{uk;f-#jj|j$G)oAo{p`~XjHlj0aicN9b-Ho3dka&)fatXuYS8|i{{7uS>p4U}Wry4zbhVQM'
    '+aF->XVxoIITz`jr{i+dA%{8`e-=={Kms&$TnI%yxVgo-NByp2$h!?^qKVzEtO`XOb`}_npn3$C_*wE2e{OPbt42r-OEZcK_YTi)'
    '{S*m!vetmAKos&B9LkGq)#Y2+_nrCmd%+%~<3as$iNmHBs8ww&W=*$rZ#7^{9&*s7xD7;nK^T?&v?w<5<=-k9Z9C+q40lw-lMAkx'
    'x#)Wlqi^N}9+@`<@`pP2F6#{#uM3~Lg>*(fy++|KQ&VAVFQRTDW$u;CY$91CH<qT)S+7#^MB>RynHNlEREd(CRMq~az?=7bgvV|m'
    '6}Lra`|hDfuTjL*X8#BNR?!HJmd^0fnzz8E;4RBrp5XUf{z@GTu&1Z12x|_rqo$S}{RfluaXnD&C6-ubt4VA-W6KXS4qQBpBlJW*'
    'Q}%&p>`gKYgYH(#1J#jeUWu`%UhBlUfV(v-WGFRQ$Au1`LzAF$ITk5=&-%lE_%DbzuiB#JU92yqXuPlSTg}oh;f*4}e=i0CShj(Q'
    'nr*sErZ^Lf9t;@<^4EjE&x=O!1>X@T6#2W_IphA0*5Q@to?TkN9@%<IxdU`;c$<Q<slKSArg-O9&jGQb#=&?#%E)LLrBA*$Hf2<W'
    'rBTREdw9fEZP^E>z5-6(NCeI;Z}TfuXIqV>5rrN_K^q5zfa5ErA)Uaxi4UCLV-E<&TxPeJ4^{h)bwF<W!kw-cr{6fN!uHm-d~~qc'
    'i;5mZ%jD(u*GoguWDnE8QA*h4_#(bP0*y9u?A1!V^9WY&VJJLv>^7$3gN`kq=_T)~K24vlg|VQOnq8xRmDNHsxvQfzPk-c9I!`pi'
    'X!Jy>e41fB7;VAYoW^ibOf8d@9W)a*cL{HRWfD2qP3c38GfeQgWy~oQkw~=|=$aoB0~14v9i?9dz~RyE&1<#kaE!@a#Z~J;hN^;$'
    'uc$~`2l|B9mv+7F&T#y>GBy{LFhYeBHiV~m3i(8Znkz$*KzqBHSCDhznM5pi^!mh%R8dWEyymrhF^-X+7k(O^th$5b3dXaZ(0_y#'
    ')bVKmW^E|b864^1^o!0t&Ssd&Lc<X|>E+94dRKhWGt{QOI+y!HFc9d%BvjS^d*3)dnBR)xdcOidMJlGL^Sloc0{%5Xp;15uUPBf7'
    'FiY2)Nz<!e1Bgum!@#hsd5xhqbwqcZii4S*{t}4QVthr6*gs5J#zfTHw;T1|GldR!9?{n`tfK*-6qj#!7eq&LyVD^pfxo9rIhtM3'
    'pe2^q=1vss9bmC*4m-ER!IU0!{`V}s<+qW_yD|OuC37IyoPPdyU<FoXc!kch+xjR)XQGQs&mFRe7w~A(<lO9O^968~$CB=hSy|h-'
    'K?Y2trT#SUN7pFt5;+-l*vX5Y>VE`iJYo<^y@S#IaMVuL<H2)g4|o6NU7f~D_6aW#(pb>2CbEpg7QWUvfh8li?z>W1MZkmivZXKl'
    'LhQyvuv7m`Ra~%h;L$jKr{T;%Bb=&OGZ_Fd7O){Ab0xBg;?0p#gxF<&=*1A$kubiIfG~}jrUBBG-{jb5Fx8s(!G(2e2dVC@z7qTs'
    '2s2w7?kYH%9a;_&w4<|lo#}S#M=A{uir<{-#`*f1806%}XSwY2wgeBo?>r9i5cXBzp$q}zevQmYb|kM*F4WvM5Z`N8=~5#-Zlo_D'
    '!x>*~y%ov?Pw^l>Nolcqj?@w)W&X?!Mlo%8^Lk&#j}$Fhr&gad8vkj8P%CwC56q5N1Io-*G|Ze-eF$#<qUC77UAFoL9!ucyR%)7L'
    'wy`&n4KhS+zURI?R8&t?IViA!=ughxe?#@VP-48*fR!{$1#nK<wU5&qvOr0b5TZr(#4*Iv<CQJEXR3=Kcev)Q0EN^`EJ>f^Gt@1j'
    'S2B+uh&xo+acsTQJL#6obIc9=Z>vcK=K_NCOLmf6mFduHidRAg@4&Q(T;Ag7YVIij7riebg~EB!-J4}E;KuWO=?<x=*22Y%_m3h%'
    '2gCLcxBj@k)=zy?TyXsBZnS_=6g)yX;#QyD3g9g_mbW!M2lLK9w9q<s0?O9D-{08;dY^5=4jLE6CU4Vj>fV+=9mHxTiw{WsANgn7'
    'd6MAUlvhZ`2R%x8v2oU-0eYx+h?QTK;57|mYjOGu^nse7@<gR5_B+Y<t%gMkm6YHjTUXVBQx*+e$x6uR)yDPm-FyXK<EQ>XyrMP6'
    '(%f;HW=R0HahanVP=U<NL7zts7<;4)t`6fd`aEa7i{d!>_T3#x40QwVN1L$?h(0s{xP1@|C^?@%R;j=OD#jmRA)+IJLI{<=t8bFi'
    'E0#p}Mj*(4Q~tsLF+)tFT(SrG3+vYA*<3Jepjz%AlcW}Go8Mst0SBtB2b11~l9hBpRT{{W0)?>rP)8o6tfhzqzv+EIb$?;{Co86f'
    'Dz~<q7`i;QL~%+KD6t>VG52nK5=%PtxN|&jr%k`4sx+ULl^y=$Ua~<F&ja&o$bCrT-rl+0_Mu`VwvdXg0msBn4LPo>uEMVV|As7j'
    'zd5EPn3&+6=`IgY@uh+yb)gCyCo%cOTiZvZ9cCN5#_+XZNK1WJrOU;GCpg34#RjNV3n6M+g25`io<24=2wm=gc`_1uVzvg&oC>`j'
    '#U8wxF<VSlZ3ew4BV8!RnRf0+V!1u$ZZ$r=X|ICC!zNl3RMuT8!r$71IQwQfv<r_2DSW_Cbz8eI0_Ar((l5x<$ITJu>(G<BCr+kK'
    '{14RE5<-CmU}v^pA9oyY8Wp^4-n!r%kkLwiR=D2yLSzR7Dmz6mXIv*6&UEKF;!z)QH~6Z|%ehs!@$lk{GQ7@C&-!@R4#K`87b#~g'
    'FQ62Vi#LVlj+cC2(UGu$IP>@9YS%jc)s`1OaBhc#FNpLvfUTh41ds-6vXiLg$H3!}(%$FoNltfa>@6w>T7_xlN+V+VT~{N~sV22T'
    'M{GV%7>-sd9|?6q)u=S%HsFb4rXUkwN`;kn>b)<!Rd9`$VO5ID)cyH`vzkgsN%NdB>utXcRlqZk*?0bHerx`eii5w!HE}6l!;HKm'
    '1(}4LBHnpdUyu8s{K3i|Cg7>~Rko{!EODvt`A%$tBbhlJ4qad5!nUG5)0%xs0PS52-qf1~@oN((3S+hH_IqPP6sUbU{JL)-su)^M'
    'X>C{en&tQP6P3(QuZi+<GDBr(-g8u{w3SHnlIKoo-Yf+2?g?ZvWu<-TE@}*HgwADqpL`0&Xuba3_Ay5uY-mjW!j#pjAg5`!J?(RB'
    'k9B=lCg_mnr<@ScaYDAu0%*<@o8`6aSrurGfamiMbj5pc1J_*A{+J+1!Q^x3>efo;%zEM%J*8SA3C;SWxtyv$vBkMD>>)3<$+`(A'
    'o)xq%ljUfPH%n$U)F?0u&QAUgvx4hL!FsB#%ilWl?^lXjBbopR-y_KDB|PIyu>(Y`=E>xd?nt_}6vhC1WpoX##oxf(9SOqkx`w+Q'
    'HIdxZ$tEa#o{|CyA|>;?o(x``CB%Fx(5EIGTy9eYPgqs7;SP=6H^!;lQIe*=VR&6-)Rq-7O?5P)QBO!_Yw8`>NBk^lwO@M5BpRB6'
    'nb0FnfT|r3!EP`hYxrxmRIQU0y#6Kr%c`Z9Kx$ua<XAFT`t%S01mPN1_aM`K;SPw*adB4*mxq5Gwb2|8W0=YcS!b|Q9(_UxGj7;z'
    'yZ<9d1GQNccgMN^o3r?Iz%Z&1@7ZlB2t&9oj`T0ltPkoc<?N+hG;ytF;MftBOjyH_ylqbPJ6v~=yvw~yFOolc8hY`|IOwVjD#M|R'
    '_)p1{qP&{=iEva`a+sI+isorEhQkNvP{L#Q33lQDjT2o$6##Q6h_X3>71}2ZqrxUoQF@4Hp!>)EHrZjyU|tI_3<)2$dSTIzQ(+xQ'
    '@v_z*(>8q6RyBXF-X=xi`)3G|2bX13=lOPhPSSW=*KKjdqX@5O4{h)w`96n>STZ~+K>K@QT>aX=oM1~z$LJ5^S#Z@QzE$8*sp~C~'
    'InB0*?$ZAr`g^r_sdv2w1T=qK)$LL^-w@x?t-@E42hx^zF0us;X~CM{ksQj}&%eLFgo3rNN_zzvtL!`K^vKVJMFsB36Wo!I@=jfU'
    'VX#`W8A|Ja(0ZQLob6I;RYt2hh+Y)w5cUG_{;iK3BqvMxZZH?Vo^g;EHD;Jr3O+Zh7(P&n2GJDBWWR$=iOd$*uUJV=o%g(RarUb@'
    'h74a=_(ugP3W?v=YN-(*Fp!ll!_4ngXV+M%$IW6P=NZFEkD?SKD=Xy-RN|u#9O8EY%_MOzV|br$-w3&k2BX<&W%H6xg!kPD5XEzk'
    '#Bmx6`^g`Y4o#jdoM*($=0CC&oE5&Ke8>(5N`lzqE<wMH1R$|Ww#J!nh3@u9_}?hhBt|%XgWcWOfrflbZHkax!Q|h8+?_EA8<xzg'
    'U@@jUhHB1ylzp<A+8=!gM)u>d={t@Ty*I3Y9LzMk`G5G|0Rq_nb|#l@#57pZF)v+TfLWhr8onUvn};S&IhA^&G3)WzQ*{G=A^*IL'
    'Y4l}GbQ-2K6E71h{;(=;`=Pm2<go~~wc9^6sZXWv!F5JB49jKM(Rt9`@J2$D(6PrrOhf(&EHElD&Cg86(>0toQRzxua@QYXeX;aw'
    '3C18a#0-OJ_4R`Rga3tcH=}AUB2xGD2EDfH774r|vj#W!C)-Gt^J|bRDnF#%23bdatzrUv(?7gj;QO3qVI75NFc6E>s5U5kJ|Ip='
    'PTbnih{LSVzkIv-&jVWxZP9zzZIBmMvrZLvHDV!oQHm<DaYmxKOp8yh%qs+L%0m%<YWqMtYfK~~VKbX>@4SXNq1mt4Nx(A-oU^y*'
    '02q7kt!HS+`95+uB(23IpOwSYVFM4(yX=gY30V-|h&ppVMMl8+MKXr~TwsF%R@U*lj)n#>qk4K3(8}(7Y;TvB)L8I+4AL?JTdC*_'
    'G_Bd~11O6ow-~AqY}hYVV4-Epa!FJ~*muY2DcU&vjX#P0h`W_7SM-jMah-Gcc($OTD?TJT!C3Fe84C+@W_ez46*)frlbS*DEu|V9'
    'yAA(MkN<x)PY9sAYn*m`SP`QJ<XSVe;ZIgO|J^P&jgfxbJ9)`}!9DDCFOPr6T9K4}xSO>)cx+&6Hp!}LH$gS#C#&wrzfIBars37l'
    'h7v4`uI+D{{-!_6=I`J4VNOYyaE7h&0xqVTFu{J1yN_U&s(w;Ke5TIt_-r)7Y&PaOFKuf5ffR9Y!w9p962_KSME>c20_7+?r1&Uk'
    'wZBe49wh(KzFs7FTk!LYr4TV77pzKzO#`TdN2P_xL4M*fNui7jc!jmt;}MF|=NVBH`Y|;A*uf*|8A23n?N%iFu@6(3=qLfP%~~+U'
    '80BI3<x=lyva{PUl<+~>+;|j>T+Mw@SitNz7|Zeji-Wd#P%Ti)ap@>=du)s-<LTbY_$W<BPLxAz6=g6*#ybRx=?!=hN3=gAjUBsH'
    '#_UoZ<@(#<BT~HjnSDIzm>8MD<DxKA62M*DQD7h11oxI>D+kNXhpz6*g3eCjBd<?rKj{LOyAvKA-gv|hEbCM$PbrT=m@$Y?5$D1@'
    'ufzKC_r&>y&kh?NxHd2GHD_D{5+42U`2AaAXg<_BM4x-&E8$C{9u^g?f_rIz8|*e4pM#D!;j1!Db)Yw2j7)cDm!y|A+>36@g#sqL'
    'CFPFrpT~Vq3@&!S#;Dvngpd`!h+w;n-#I2pSjj1@^Rg;KI2~B=vfOc9=cm>F*4=x4;w3~?=Z=D&GL0Q}iKva236_>_Dyj?bTI)^~'
    'F6I1Uj@;ORZooGpb|`^sj2wl?yy(21H~lVSRTDs(WPR>Zuw0S2eTG;l0Rg1QX*iFMmF@9sVpQ9_Dxf}2XJfddIRB;KLNEP2Dhr}0'
    'gn_Ll&JCftsRX<|+K&f%taqPe@WxvLO=mTFm2{fQyp=_DKA=<`)*iD?+R5g**IfIRa>bhYf}wvuZ&lqdaYY2Q^2Z9zx@UWL(^|wm'
    'Fx~-k^IAZ8;_`mTaWcrLzq@6{HijW>i<3@D><aR3olR|}!Dx6R(=Vx^=;mO4y3b9kQ$705@^pL2{<&Vir*FZI)z9MECq0MVowSf<'
    '|1I5svleRwWg+{&CZSdkkXqhwm{sytvK%4ooES)_9m>U;GFp<1^0^yIPFWWprst)l7)-;EfWf2z)*E1+6L`+UflOym#Rz<jICTwy'
    '^!ZOLS=2H=`GutjP%Gfx+KMfqq6kmQ{+`)(COJ6k*Z5iCZ=YDXvUr&$6w`4RNW(_Wa=VseTGVvZvVxx1ndk*c6J8rkJWYySkku(f'
    'pvb++P<EO&(y(3tRKGwuFm+!=kLcPQ)dXNMVu?#4*XvDxW9SdQAUDEV@cs~EU~xJ-2KUQVJF}3TK^h5m-HnJ7^DU||H*`K$<VqeE'
    '-mp6=xyE)%@(WSGXgg5<FYAlbmbMpqq0?p8OypCxtuyIa-{daJQ@6}y5y)ztM)pEY{8I;4xMDqnDHdoy6&~BX*6Lqaa+~uom?qk='
    'is$7W>Z@sgye=^~U&m^9cnUTQ63-D3EIoA&FId{M5k|TfI12Vk1EX5E%&BD?k8Af6=eL#k#f*9R$#<C=$*R^*3wP;w2jkTZDlR>j'
    '6LrTfOG9%?qr{h3xb<*gFnRb*j`{z%LyFV-0`6YTx&e9rz?3<|<?Tr3{|t+rH|-_Wcu$cU&+s8KQ6ShlA+fLLFD~_3Ok>YDvEA>V'
    '_S-^eFIIPwu7Y7gH7tMDAm`PEfb0MGI8Be`$G*uG--E$una>)MfA1M81<K5di5v*YEo+)J#}hgtKcl@`(`M!{{`VV53|vqtquC|$'
    '20chT-{U}l`6*kohrSccJ!@FrV0=o`&p~uNd$w$E8R}d5ILLLKeSYnPxxcjMW7`traFFNwP={92;c%fE<e%iFyvrJ8^Wn$mjiVCv'
    'n<pc{8hQH$(%`a%!6eE5T&8v*CY+E3qn=p{(nTPAzg_@K6bOIVAA36LAWEqQk)V{s{jv82*&LGDL7a@rGmQVk-6a0`E7xMK=Z77}'
    '()Aj8?WZkzgF|T97BrzDvX{<G9)2rCUJn9>WQICsVGvg121=74PTK&7E-!<I<775WeYaMh1=;39=wUtKc>4A1!A?qQCC48hYNv+7'
    '&tU@)XJL1~&;a`xB#*T$4qu>so~*hH)(-OF&80?<xjWp<F{Y_Qe1FrWzvpn&cWMGWLO@pQw@@1uzo2G|rJWt#{n3-`B+9A-nlTrO'
    '(v|PGF~z20r^MVU{#ss4iiI+H+Tc?VU&9Y6CI~<#TN2&}pxH9Gcf-B7eCG%N0%{df6fq&K=gQeEctYrp+}V3^<D3N6Kq<z#S~e~X'
    'pGkpt*ACZ=nE7PD%*~)H&^&ZdmObpI*C)J$#n|fOOy*+;PIEFrn+=){)QAZOs@(}O%aQe8h{uXjd@j%4)0Y4T5)Sh)y4nDSSp+0B'
    'B(9>rPn{t)cKvZbH>|JJRh#!T+$ogWj|M^nGZjadJ5m$5vH6atQE_(rZn{jp{b4mBMAz($%{lxH<6ZjB2I&*?9Bt+xNQy#W<PI+)'
    'G0tvW6v`2kI9}s<@o~`05yLQK&~}F~HPhv*&lC_UOUcHPAgVG}ZO0n-U7X=vX{%FbX=+Z8a0Jxt9<rc2IY5nUF0CId^y?;^%)s*@'
    '`b}N_OQR(Ly~N9pjv6e;PkTjCfBz@lz#4O>4?~L2<Z|lz<46!ehE?y6Agtzx2E5{_D*Wk+9BMgZqsZaB>^2vhwY1$Qd0NoF6thm~'
    'X^O2EDq5ht-%#)b@b#qzXv}e!cd|-$2Rdl6!R>q}M61%Y{3=xtMd%|Q4?Nx4rIh50?iqnh#@q3sT&T8rvhae{NQv0$hoOJ*3T9Ge'
    '0(@<fR5EN8PbU=WCtpxplR77Z&EIf8eG#Jf1V92zapYuh_qSGQ3SC-n(?PeE;2HHhuwHUd%|=d*Mi@l0Z+~*HAyGi(|I72pSn}#r'
    '-XJVh6hA*t;2p_@^5OkM0-7ImyY@;R^K(}O0Xq?DF2pZMG)_1GCWzBb>ba<r4>o|Giwv_3SC<R>^=NYN3=U^H9lY)8SbHK)6gkzu'
    '$o;@A$h_<Cz|h2*eN(JpnwF)95(Zs3U)=Gg2$=ey_O`Enx_Ead98f*pb#>*NXK-gTG+Su$xj<ZdvLiF1^hOt8iCH01=@3!SbWDRp'
    'MQkWF9l5$o-_b-TB_FY4V;XRvW%V-F`n&GWjzvNkjQ~=Okup3aiT<$A6-iaP{z5~O>m#)0g!@8TTP{Cf5RPUhN=88IFL+hiiP+Ui'
    'lKOAk<xlP1A7sp6j6aQjozez6cj{#`k21oI7AY5_x8G+gIP~B$5rxHs5YXE)<Mk=`AF>s@W!+<#eHA52IKE%iK~+N5*vIr}^Ez?<'
    'FquAJ#}jGTW^N>}a0R3XNXl3*opp4B<()uoRLLYh@U^IvI{+Amf^7Z~{an|DMba%bQ-jlB7$(;UfIeC^UnoW}`T&ze$`T`fX-3Db'
    '%RpF=cFWQu!Eo?Jot1Sq&vvlkPfPIMI&7gpqvf=CdAnEF+PHT4K=3L6K$M6hpKUX1{ucnuyXo7lA#_^JfeXFukU_70#42BUXBn9?'
    '0QmeBf!+86H;H@+7T6k<H#Fs4$6dCOs&i^E8+MIkJ2~a}MIl77k~k_6Zb~m9#Srd^xUEIA^zA3E;Dq3p7>wv<NwrJZ6K*J#m_lRV'
    '1fN|EPK`*hTZB&Ra}+?Axy5Sk*{j<_PvM<<S5kh%ZiKFqYXOJ;*TT?Tt4721E2|ihF8P`wPLX_Y`*9UA4xP-m-8P9Y8BHV%zTsF}'
    '9Ym?560Xj;nj1;yyFdC@v9;YfhTS+)gblxv2aC;uI2!4sPj2hXq?gnWzSWH*W>Yc{w}<vh*VfzycDZ0h_za?nl~OcO$1W8oH`8Er'
    ';GcQ*vwZ8uW->u2EnMx5`IyXY>_d>RslZ$)gpnq?4M)yqs})1_GBb1ocGl7+kT!-CvM?Ou+aiyGl1HsJyDIj+9fwYaj{$*nTz>FR'
    '&HRiHWcfy{HJ;fnB7GxtaMNHguX8dQakD0phDc5XY%{j{?W(pMmXaCAMn;MpQk01$O#96v8MJjM-d(<0Myg&wF7w?au}yCSrB>B2'
    'm&w0G(EJEs^twU}=SA4j#??4C1B^U6MSaxui8+Vk;WN-AM-L9c^nI&4p2%G)r~$~a1Tyfy>=RVR68qZ=h1$m5ePha%kT;HhDtLU4'
    '+7WpZF{tZfWhT+J?3d)ge`c`-(VSUxh_Z?KpT^7Co1Rbn)EZ`=0Ql@V{)Et^^ZLFN={4}MfbmvgcZe)W(of$_vx*D(x@L>mUo-S@'
    'bBH~PD18IcHJ)Zm(y(IiE3-MPMsQ!F5Pt>kw!m6ji<o6Y%<cjM4Ww8$UJg-gvfIiO;HUYE?l#VWxmOMg*bM^_J+HZFJkL@w|8?v>'
    '>h3$)=oVf1b?pVMRzjNRDTqFccyhM!<1B`ed08x(a_!!9$9=dymK8_qv$LH_H<=z4yVYCn7#I8=@Mas(X=?NiuE?<zdBhORNI;(-'
    'pqIc_tLE7_z>W<Ns(_QgnH31=UI^Q~idYMs)fD`+hJV6v8k7^(E+94qPCi5?f1i44x`AFH%j?jkUCqD`t~x^<qWRM9QJu9m325$G'
    'Oy40Xwgt<r0{asY{87N(>syONh}*j9ye{6(q#`(DmAQ<quI0F{Nyq{1S*||oJ-v2wx~nY`2cwJdSS^+A1b`Fz+tSSr{(u-TH3|iB'
    'YDvV?*jSKPO_d}E1re0mDS?q{sdl%kakBZTS)sALuoe}N@-HIZ7gz;64L;g88rA6mlf#C*LfthL>e-0z++_sqoFpHmA)e1rqC>c%'
    '69QwZJI=L)&_PhFLFAf#&^6XC7W8YIfKNmB7)kaeK&3y6Z9Y32yzo~{-mb2ABo(8rHZ7bMQfs!=gz5muwfcZpwDEBaqAGjRpAt0#'
    'fbWmUi$nRL6_`zw@W3tJ)|2S$(^L2z9CSFZQ_IlSFMS?3>{P=U`;Mu~4^vH!6Bl>ceM@ttz(xk7!7+q6fD26iz9KWoTpaA8|Fbf>'
    '<$?sC_Eqs^d4l}oe;Nj<wJV^YXVXRo*@%iRU>^hMil<+z*@ne5qq7spT`s#ypmIkBq0<>;pC<SRPng;gSFo0m*V5no&Rr<yKHJ0*'
    'VJBVM3*{<Z0Gig=@VG(#%D%4FyZQ-~A1AN67j(}>afnI|6~}k3m)8^hpN$C(>hvObNlUiU4|cD7UV=qlhUSl_hDh<3@HH$~%-18E'
    'JOjl~8Z)emh5d#?6FN%`EH3UP_iU3C&jFs4^T_%)1&m4XAQ}}H04Dm5OMY1jC{0hkT+4w&qsp#IXa@OKzp~rwC(OoOES<4N$SDrl'
    'd|2E1Qkv-Tp>oSxj8d*#v>Hk5Z|`Zgiy}OoR)a|L(s_Hh&Cg~D`>T9zLB_aE(K3$+C<s5V{o3?ttQtLjh~2_UfDSKP(U(X&3dL{a'
    'v^j0{AcvT>u|PuR_V5ui!d5y<4A8*L)bvC{eAWpo+YOyyBIr^JnnSg@np^4}2mb}`q(6#*(4*{2H|Fn$);ZYHNrB*Mh*?xJLiNLx'
    'w1uCc6pa_GD`RRsc)#Gz%StIfUYfADp#17GTyYz=5o^HW!oxg~jveap)Dn_`(SMA*!MqmH(arLZZ?@)WWjzn-ee~F!X@S}y@}a<V'
    'ePq|`z}KagOsM<xJs<?RNe{~q^I`$oTdet7Z`Y}2*8SyXOl-c+Nk>$EYn?3S4B4PPnND6xY3K(Zs)gv-i_XOp6}Rn*oCICmp#3b_'
    'DR_<;gDqpgI|3<(;oh|Ov|!8-b<W2|7MkIVC>cK&Sy?`4<Ggx43siPD6`O=w-}bfgm%6*%fD&tq4G;&B7Px)~N^t}JO6knWOH1x-'
    ';tz(7up5ZBOH#kNP=g9?s0hE)tOmzI(L)(kVUl9>z-^W=$)P;_ObX!t7VEtD$2UM_NMSK_-4qVoSFgMj%0K-!Y<*VZU5r^<um0f4'
    'oo!-D9{S;4V!uEU78V!l1e9V)3_?m)!sU@3d3A<aMkl1B+E*A-2+v&TVp>!$gJ$Lxb#<qC6iLI{LMDwfA!CxC^UipNT>u5%uG!!`'
    'o=UX{2?O!dlCb0GOh6l3%zuoD#n}5=ArSI|g;IIxM&pJM0)=OF+z(mc&u^(he7roku#X1Es2u4hmCtvV;kh_;+)xS5Q$0f8{|0Je'
    '*L`?cqyGo5{Dm{w4}X#MAc%aDP@up$WwH+QIv;PiM7R2rY{Okp0tZF1UZ4;X?dZ0)GffP5dN{n72rqI60MbVxA?4ap;socJs<G#}'
    '=-6J);1=zj(uB=Rq@=%Cl^dDRWwq-^vXCgyx49w5KqjBlk7OzgvmEMHrhL8`YW$yjM+(e3!$X)Y>H+p49lOhfML;dDSH&3KgAU(f'
    'Gg9eu1xp~+sDTWD*aSMSyuQhEB1(N67ddz=pLO9HFUL0GS7U#BpB}?_uO2QHihEb}$E|$}${zJR!T*>=&B4e+V6jQlxaothr3O|@'
    '5-h~Y?gXDTz-qB-+3q?CFMwzE^F`<CQ^p==e>i)lB5jok@d63Pjj%RUP7O2l2|<$Q>oA%;5fl@z`EtH5tz@`d@biWs2EY2nhuoZb'
    '|2+tzgX_>l{4p+qx9UK;H=t8FCQ+lyra;)kTNW%t?~?8og}urG-;wc*e6OcvZ>y`i5UemZ`(sjCn-BW~CKUnu^^i{2-Ivjqt@vhD'
    'MYae&_Fn>5qyLS{au{mzJEzg5gX%7wJr>YrTDe|^R;1!iSs-CE?xo7G>6b`nA6-O(t^pf}qCqwIGLg?g7PP9j3L>H3n|1UCRqL14'
    ')fqiQDCL03;-H#?j!wH06YNP7FY>*Ya}BeZ9Cn5!^jmLxA>u;LxOgI+e_6n}B044pSj8huR5J``A-yiIYBTLMR>xL;ew}A`2c$xF'
    'Q$x??3{!gRUbPL{ix6Y~+TLa<<(VzOMmrB3i6*vVZ69cQcjzd<D;~rpyZ)TK0H1OEhZT^DB({g9U5R0wcNUIE|Me~8=#yigc%=`!'
    '3v>&Dd#p~_TfrY0;SECbMUaDIlk_39JhKlSK_D`ahWI2kA})<0-!Y46bw2}<2=8<}Ummh#{-=#}GJ`87ojbn(pq45ZkfO-8`u2ws'
    'RWF9{f+hQKS0{g#k?O)alz$9x`|UVN4jdu<+`(*}L?Lz6|CtAv(5=~suN@Egil*K;C*ypyI>GMTUQVyx|G1fQ%+c56(Cga5b#S|D'
    'YGUWu-i7M5C<MQ@dk8zLrvamdLQ#Mu^fXqJ5$Ql|n2vE{VW5`Jm`^ap9O6s`2(^k_1ctVSL|ia*t{|VB&mmhXh6UvL+7A<<fT@3E'
    '!}8gM_=Yg=qVE?Pz9t)$Q12V9T6#h%^Tx90<oDkHRDEP?*I7Ek2A!JgDdwiZr&%>UQo&;+)gl}^EmgO+%15d>(~}_|afq$>AcxV?'
    'd#u8SwsloRiT9-V=cLv~FTc7|pGH4I6$YK7jr{4eXR%K?G0VRvxYD-Bs0g3`E`RR>eXK0{BKr`s2JA!Pr3;Qcjbm5_Wuzcq-2m9?'
    '4PnF4ch?Hp^VI6Xcz@ebJR?DXqJJG7+S5$dTbynjR&O;`?dJ;3M@@V7b7lMQB>qQygKKNwIh{q;_Y5f|pu<E+DT|EqSkct1P#AtU'
    'Bzv@Sx)7CO)HngAQ8%I^giei~MEI~jpv)u6n^Iq%x)tMkR*R@H=j(v0Sxp4PkL0p5%T)zE5R&PlzS0Tsz&k75KAY#VMHwZK_3EpO'
    '!a6pP>gN-%_2a_ns42>3U0fZ$Wn8MzLj(D9Uk0!RNsrOZf_Nh@-R9YXD@$!OWu@wrwfKy`sR9TNG;vJ?f^s4-W*aN53*!-2p|?)x'
    'oSj8T&-z9s5Y5O*p92aj&Y$5qPyJJP0Mdi1&LS#lG`=nS&tDp=uK%TQplaz)hU>q~fOlDqBh0e6E(|ZOsGc9Qty&a8gMbnn^n2w8'
    '$C2*V|G<ij?b?D2B@e0(d>CG}|JslZfC89aLU`PFy`j<!NoOjJU(kuX6&cF^kjw%AlYrFwpkp!c0{$~~6SAZWPQo(bD0#e#wfD9!'
    'B?ZV@+a25)Il=JuBM!BVsd)SLFn6Al+4+B4>C*iQ_%a<YIcEb+rhRTxgT}ds_{Hk@D4qpZ^1AtrzGo%w-<RxZls5f3%@2-d5=91i'
    'G%vbt{duW5!k4B1tTTXcFinp1S9KMWeFsCp`3?eKv4Azb_VlhS1YVK?a29CF(?i(!fJO7hUn2#Xdu`6FMcYfHnR5xqQAkKn-GbO%'
    'Zh`k4+uYt%#obk~bwoI7sJM_lUs_QP9n}5^ELDm<G+@dREL#m{TH0DLoBW{YecJY~VlV{k4@dF+QOmh}{3ep%eFUi|ZZmBVl8<m4'
    'B#BJ*IS*WfcI6E3WDo!n4(oyEFC8=rU?AFyGgkvt2;_JkS{4)=n?`L9%_Q5b10~3j!t%ilhbs;4*cEmJ)tNvCCS?IU3quJQ<YC1e'
    'U-6g{#)sxrnMW!6=RAQw5_<ddA{WvHs5%HY-PFyckjuy#!O9nM&!%PqkPAk7m!F7PAE&}zchy!QoL3T!XgL2r&u?u&;oYtBFg(p?'
    'E_;W#J#=R4K={SziEXCXNAgIoE4xZDe#vP(oq`!ooQ~1sMJm^_Nh*Wh9&bJ-#MK0~x(uz=epJu~1A)53foK6#`TGFdnhx3X|D5W}'
    'uD|8f)qHZ|0G3NYW3h}dES>Q(t%^pXgiZSWiIFLp+UsvUz86nUQV0r!c?niPWsRk3UGF;r>By>%$$doQ!5O2F6Cku1;tTwb=-Mk>'
    'to3eiE+*2Ps+nr*v1TOmTj1UnpS<eyRA22KA(Br-lY7v3!Zm7ea9fmYR7d~FGpj(I_&)?<5E;nr^aYY^5?s%#nf0rh$*OoMmgd}_'
    'WCPu)=U*U5k|*lK3q#_+nfez*^31{<0d&7$4{+@`(qy<cn4!qwcv3k6>^9K%Lk9ryr60fYAyp^{t;XKpA!IGe<ykJic%_SAoX#Z!'
    '3l0Ad?%5Ju^JLTU^$HhKLk2}D{W^d)+}DxR5Q8(SXO1X{#*3H_49#Ra0<l2D%RF$klXL95NZ>9=T$D->9|oqImqFtbJER2K)DJ|5'
    'Z4zq*YezEw5bDw9*kHX5fTD7R)%3Aa1p%URpYmBiS&MDlx~J(RACUv3i#8C2E##RKNmy{%JQEU<f6gE9YDu^}5uk#nmV`g9yYLo9'
    'tiKc9f-RHOUpA{4zMDFRwuK|SedTYU5HPF5{!byB6|!3y+UjODB(|G}8*xp26`&22<hp)BN<lB0V{g;==wjU~QSDTDG!(U<B#UGc'
    '-KZ1FOAUVAs$a$R{S)lfr!%uzSXnTwt<lrFTf6kgTp0?yXXidr$j7bSvqB~w!?U+6MmTJ0JpPzGeQTH^vmZvZThzc`T)h`WF@T}~'
    'nf(;fkRhhU*0heX^tab@lU&cguaxwFK=l?l8{jt#kK0$*2IT^j(Lx@TzZq{VXO{Fa%RLx85OFBJ>~V3d7ZX=SZPFELUq6n;OwvbK'
    'e01+y%k0iK?<hLw5;TwRpDeN^EvE*GXP+C6awmPdr;ls@5|#^Xpb%jduyQTaCW;zoaUbumUpPtY11ZW*5F$R{lio*rSk>YrWlyO{'
    'KNV(>w8Zp^EpKfi$B*gJ2L$oMjQiI$frUDDTlnhtUjtMk7*9_Tsa@gVpi@v&t6dp~hTbYHc2>4riC}&+*29)d+AY!cesP#%V5W79'
    'E3?AlB9^H=V&^6z7aP|*jn&I|jzfK>xtWDGCqkqM$%v3<Xbd$=D7(3so&2~6n8d!f!daHMA~^z6LPFXg&?2<t5^DS`WA9q;S^j5D'
    '(3z96-$3Ik&TE>Ed7&T51_jDLbohrCDIsPg70+yNc<i`$fgx3L^`f12Fpr9@()&MXp0kG~eb<v|O`*MNKbr0bNHA+1eLQy5ELkgc'
    '-A|nadtQTE+<JjpWw1TXM)}pTag9X2!Mqa8Zz_>?IIi}Dd8kjJCs_D(m03+%h~mXByTmx|b~YnTXo(3~O8&GIqq^tJ1U_{x{h5s3'
    'et4dG7{x*^A*lcX*EYlN_ssSF!PskHT>Ot|rjU!{VYQm2IEa7x&-HW@gpAA#gBY7XSZzaJ+fGs^f6Z-h<eCqwxsUI%m5Iy<bvNf7'
    'lb@-KD0?gHaMAhSXn>?C0R}yL$u40a&M8t8Fh|RC7sfPS-pAqrlK~Rd46^0Q@N^zbG(i{enj65?%SYd~;7mKuyP!lOZ#C2Q&F^!6'
    '(~_L?%q+-Gv+T<(gTrHb@Fkd~C-{7^>OuiH8jDZrx7Y|RZ#;XJ%2DjXNsGUeWBP!{9eA?fK2bB-0Z3>xo26$g@ec3_vW=dPj@Tla'
    'nLq>TA?qj4B=B(9)NV6Q2Tk(cVY`h338CEpf1Nl9Pe4}<fiM+$4Y)Y@C+?Iw5{Sfwa^hOdPv>8#Y~I~oydvV9vtfUbOnoXIhKj65'
    'CxjI0l4}j7ct1?LJh5uXdU+&Cc*S$E)UR|3+<<PBIUm>86ndr8GgaZ$y`_&sGfa!y!mKPTg1qS2j0ck`xMs=outf@^u=IcgM{#O)'
    'C>h-lEII2_FV&Fz9fXhKbDH5<b78W+fiu}#IqDZT8zXW}f2$oejiZ_YFJEkWmzDQh{YzHpho-@S5pKfF3Bl}?mH)VTkRUF!Wrub{'
    'c4I;i>nq22<q$vB-v>}!FtS|i@B62Po@2AfmfL=FulS0i!J6tGR~UXIRx_Hd-q4$8nMN_G1k_^p7Z%PLEOKX3t7q?ck8R5>GfG`-'
    'j{+KG1R<ACCc7-g*d%B92gV0?bao~$L-s0%xwW0<g3zDbCVDBYZjQ=4t($|243(Mycumvc7;8wuKkF^mj}7$8%z#Y7l#qcnu7RnZ'
    'G1fY8dB?W=mUf|}ggDyY)Mk8}mExl^;^_<%D-q1n^k|MGDGKeg$Pbu(QVET)7A_U2Th{ETEd>LNuU$l`F&f^;s#=~(Ug@Y^<4D++'
    '8<g)r5(fX@1$x){!!;+3ugK}dXJ42|H%Hg*om1fEG1CKYnr@89?O|nkK;$IQsZ)|b+=p#3-zl8cGr?luWg4SEIlhW@&McIvbr@;>'
    'V^VHZujfG2vJtm~wVu=|Z_f1aNpVb_<wSFwQUV9*sP=NbTUJTfww2caslb{-18G+!kW%KK=h?d+7oAvaY`~H_V%{GI?z*4`on_tT'
    ';#J$U<jNEap^y&eZ^<+5PM*v$=eK@d7o0ff_hz4`jl`6x@XZ^wImrbQ@|=S+bbi^NSQJu)jlM@!G}N^f=s5d8c;7zN)l+AGx%32('
    'Azu#^Znr?w#&?R9g3dYvdZtLD&auSc8PC0GYJQcrv-*{ibaSJh`;#+dkq78SOb@Y@_Vr!^dxnUtY4JwBpBCsZQ4TQpD$LTf6iGSu'
    'Mhz!$YK93l);W*<mJGed(R$oUweUmBs@CJTr>#{(+=k*HhyCKRlH_uvrRM}GJfr;Szr7ri7+NPR-`jx*nRHM!`+4jPriXd!G4@Mf'
    '^IH}0zw!dS;UrxO@mVQ#@Rz&#H{76egF89jlcF)+Nv{}w>9X|Bph+Y~)0OlVfGvv!0k<IPr#Fn4N`q}SOTbIPEaQ!5!d8Jhqsq6g'
    'xUf$2nh(#sy7=yMRf}bH0Y;}FTqMuT!<mPvbu;nc>VLp9gIMig(7lgWW^u~XVd_B*$1P?r+qn4Lq@;0X$X&F&$)7~+i^+Omn2gD~'
    '{_3%Y{#GlbpZq%=c%bor=l)(ZsZ_ZcqstXmS@_f%dQ0WCB?#1ZF&wb8h7l~@1z8doJH&Y8K^FaHmYi8C<Jcg_dR-<Dtu5V{BYux*'
    'L#QMx=F`{2D{QJ-b{M%1<<}&(5=zSXCBVx@THBFZVTkety6lQbv=g`gvQf!|omljOFK)y{(O!j!m~pDfzW?#Ib{2hjfMwc7#C5<4'
    'l0?2Wh`kU{HLtav1UZTb)&47&Ipc`Fsy^ACiJ*-v9a|k)K_)urdp2$M{Mh_H6Cq3ge7CG_p69qoyd#)tYEmj98LB#_N{z?4;W(mO'
    '%sN>6mF(>K!_<m;h_4$_A1R_d+hSG4+h=V?ICNT0!tcepzXxJ0>Z|JRhU9*ZJ^gfel}^_CE=<#%j!5{9w~2+yh}zAn^`BS!Bt8Ic'
    '8WE43uAuvk3?xOsdLKycAMP;cW;FPsM4VNazo#v;If&~E^u-K~I{k+RclnW}u5_rGRM`>?-5|nI#hzabLZeK(<i|pe&(y4u4-2fc'
    '?P_s}+mE*&5Bhl2lVJc!%&a0CKMBiGFdPFm<yoH=UrJx_$nBn(!0yGQwz-~Mx`$yVbcc|)9#UL^6-)kL&x6<@+zic7&!n)tv?RZ7'
    '0;GzWc0%_9*PV(~xtw-kv92VcBr>7T_;RQ~AAcW|kQ^*W@*AL+lXgkp>+WL)0W<ffz+)r9X+f<ec)j|k)--%fYQ6r%$o!~DG;$K{'
    ';fm0Lee@TWTi2?ASFeORrL832<Kw*&dT^sglTbl6Q8|?oWI%~#ALIRm;jP%vN^gFMX5P)`UTV~qXV}mdu>2}Di6*W8?Y)FI7MhkZ'
    'Jk$wV@S$ijj#txo0MgE)$+svwIh}~mc-ws>+!{HTG&ibM>Kjio!=O!y!jcw)_Z(rB#}Jnu0y&eKq5|G}<1y<x*&B9_(K%7*M=FJh'
    '4%Z5|bcwK}^Yfrne#1<3__K;J7HYZ{rj>~h<-jTZ^6h98ra$Zgtx|KimYP;v@(>4rAIY!|5~k!|PsIB~$oP=IGO@l&t2K0P27I@O'
    'kd6=TnVtxeVO5yT7*pUzr!G_c@sPEjGKyWkmT)c1a`&rV^4QYU2s?AQq<kQ#eD(Ep)iE0bt@)D%#C_$H|NrylI)P;pMYT5r2x(h4'
    '+r?e`MkGqKRP=ggX`zZ;4#Wh<N_^!X2)2wR{_3bXADH~FR0>(TQ~-9I{`nmcZLIO&Mz#$DCBGI<BOAz)9uos4?-+YJ#m`U`cyhzk'
    'Rg(doN_B!<-t0DtCGlqPad?rU6Hon~F%^z{^im4}nl(5mM<fGEx;-fegj*&A<~?**$O-i@n<(VyhV}6n66vB)T0?Og_h}b%l0e|;'
    '<~#pf>COM^8ULR#lGg=(FKU*B2{Iec)b~A|6#oWvOAK^arJE!ejR{;V=VG;}q;eK&#c<S&{UyF77QUoiZK|J$Kac@O+q%M1)DG6f'
    '(N7ljkbxM_Aukxh>R_&2&A5|Wl5^IUjji|*45QEl2sS6GsWM}+Yq~Ii#_vG<^(9%=%13W?>NmQd(VIw>NVOUaTbPd@y<)$aZC(En'
    '^e><-jpdsLpFA{`*=@Ip1mBD-4Ey-lZ9}$bgfKbIT%aWQJRxZKmfWo`5z*;rb_I6y>p)9|MX{_MCeVucK1|6cN?nW64g<rgGm`HF'
    'sB6k*Z5bz?XFXD(3fVc}<L@|k$bfG!uJXT`QaBj_LiH=zFicZmJQWI!JKk!QkwVk3S!?;CU!H-z5*kPU-T6QdJR7^_f%zhtQDUM!'
    'X~3_=v$n5dnPONsk&s<`6tPrx^?D~?27ltj!~}qHT`Fi-PYV_OAjgNWsz$35=qp&jhup+t6Tu~{{hMCPP^w9A1~Hi35tovI51mj!'
    'bIL~bKPu=06w3`z_=PTi&0hm{1hLG}Mi%~Zsh7^#T(A_~MWS%hO(r=2*46I(g>T6y&UL@(7lIgM5tL+yAD;@H!mi#gZ3^FYm7~$B'
    '!9{5*ax2kAtf@iDqfe7x2moj^Ue?l`>~SRjW(M(z-z91Im-bCLRW$aeP@Svn7`BeI`}TT~m_)=2=_(bd?oHaw0oR4QXjmcJjvztN'
    '+scv%YQm7}p**f3MStC?6fk^{;?IOF6H}Y3`)S!EsZfnUsG*KUJ(!BFYz7&O&w>{pgE8X*emd>2nWs^g-RYR><kHJf2@Ll`$A3tK'
    'Kphv|UNmo#=2H4>>)(i*NteptiDf{j<_JYvX>%zzXXQoQfy^=Tv9J)El`+$aCo}A=mS$Rk(q{4P6^i+p=C;&-uCG+&V`z{8xI&vx'
    'YE{a!4r7D6*boA8Q~oHq%uxL{XgX?~JfydEgEl)Hp-;O<7xw<Bd~g0<6o!j+du8$_Y_en`t+)axFz>LUgegV)yv^eE`q`AI#LWu8'
    ')QOan`e$V^k1CT&+%ocP)TX4IF%#hSn4A?p(MU+7rKY~Cl-6HbJu-NghvNpwz3d6A_38H0%0iryU3Uv&nvasioz?mH+BN}C^$~h|'
    'pc}dGTkegZ(wIh7-B`R&Y`d2PGlumJI)I=REK4P~S+>>$r*!G-Rw}&(I8jV^+8Ku2m-g2=KYm4D*VZQoAshzyG%d-F$#3Ns!CjNr'
    'AcTl<cp3(1u%e)fFZXa8<{x6ScFG_At4&7bg2)#_!H$-`cKuV2re^K306uwuyEhu*PD`^^C@KtpH9vXSci(IB82LBVs(<L+VdTZ8'
    'kWuam06%Qpv_l#MEFNU0F)*Yqk&B-L#lsHs6{*<2dRQ65@u9kCDJC$~dcLS><(a1O!|Ep;>6%rC_b(%|)^D4DhZ8egmd6fJgq15q'
    '-&{_4TgO1KEvP3xPxm_Bvkd8wnso!t&rlTZ?njB=tlQUfF?(EFe0k#2$dN^_;|pqFii;ZKiT+E-G4k8<@JK+$)-B&}-<3w8Sy|LT'
    'M2j*q7|eP+o3uzdy{3<mJ6b)88mk{W=fSy`!Nn48EvOxoXInIIc`Gsj1`%H9o>LHaGXxQ2quJj@eWDZ2KjO3*sh9H?!rr55m%^R?'
    'Z$_~{b{WVj55%O<2NO1l-hjfed3Da`e}A%!sEavPT+}E^fWy5ScmF|k@=SNjWZg}L@4~oXG4{}AorO@$VW8{G1=?PWM}G~2JXo*d'
    '{K5JQpLy^r_bCk4j0TY-Vdzc*GRA+HYEmf`$M;kmy&}E7+Woke14BXnX(4nE|6B9o=^0S&%XD23U%!@idwcmMg-KC$R`}DCcXZhr'
    '!=CCcNXz>Y1@U+lVt2kVcYlvJ)IyA9dy%NHe%F6Vk7vNtReS^qJD~xtP>EoWGS-U$d!Ng@4>=TrqoYIWyKogpxCYdh{v2gsb&McD'
    '0HlIii|T3QL&6uI2VZ)p-L5AHe%j3UHc;9y)7KHA<fr}C=2RZ!{lQJQPCxJ*Xhgo2+#w$X5uuFKsaTb?A3=q<JG=nNlsDK&77^g6'
    'DREi^^DcF_=}k4}&XKZ2z?;Hu_Gd+GIhTIv;X8EV5t+SxgAD>(rsCT1QY7DGNl&ZTn=BSC(Q9RC%>Sd|==FyOC%F!9>9*RFovliW'
    '&Oz}vEMPa(>#q!Bxh_6`8E@wg8t1^7!7>)YZ;R*{0zdSGokF#=t(D)|l}?dXcXOI&xGXxL{u$kNs-z8VN2op^8$hZl3<FBGzAA;I'
    'huiZC$@lI-RD&Bsad##ZziGes^lUkazRiEsm3Rkvix+BY2UC0gAAtWoudY#CS1{F=k}&lfd2*K(;$&Wzk8gRSY>RAV;4=R>I5Vl^'
    'gZ+-KQO~22zzzIj4UcSV5iq{u1RyVWpZSC!=8Ke0t{-dzF)`6xy$aSFm=fSsytI~0+BImkkp*=@{wBvf<0&Q)oCe@^E={@Mix{>%'
    'zNLdLa5RiN0$mr4BXl28is$u``u$}`O24S7V+KuYVk07+DzT~^@2_>e_H6kq*f%W*vPBS0zIWSMK%ERm$fp!WzIe(=3#=kNAT`|o'
    'a?}rCd8-HgauD{UfD4(9^0}SkXX$f6(xb{+ANlH<lkqNCoLJ)={~K(nLjdF$X2k#XoxstpJfz`XjbFET?<z)L)iFT^cT{_nuw>_x'
    'IA$I;o-L$iZ<jiDQ*m351WWlcDfe!6XvYc#>pXD&Lj(+6Zw#%g54z0q629B@M}Tqibz$4UpCUl3_IqXIgHN(x(nu$V`7NEJ9OZu7'
    '(IwW-TrctoR2H>oL?(-)rXmhc&E@XEH8fy)d=8rG26;@jtv<TzhjcHA2MqXQgL&WVmJi@l-V#Mxl4Eh3rkcV!;>C2_qc|(piSSLm'
    'SXU+y^d<+cN=ETvxW|M#d=4uZ?X1p3;Dt+ytL1xs)NrrejnUesm-?rjv_m=yNiKOMQjvUsyRT3o#brTD?<V?oOD6#>`><Z!uqlev'
    'iA5NWXzpdp)<7#?TUV9za5+|#b!Y`WZ|P<cron?p!BT-*JxoVRmTvoYYq$KFf`I9)o0U$z?o>#DPZy1O5gK6#Y$6Q|HJiE(vCY2u'
    'KqmD<G#JZY&T76Z9=Kz>2xExzbR<Fyi|e`M^~JL%|LS$8TSfbv<=;B67gn;i3*ZiZ^$w?JAT*~z1O6nZ6f1P+x{rsmt>GHKoUNRs'
    'nO0pd-cF!j!eq!(G9q5+TB8*=6%Qg((IK4WyRo(}>@K1mMQ|55@KJYalQlm)=Sp?c@9|fiP}~Yt3gkT{`AHszp&HsH7ci;j+MJ^^'
    'u1sg7YgcU~0jIEK;X@4Am6Q{xxQ*&rhfponJ={wZ?~ylQC+pph9+YPQ5p<+NS`ze)C->LM(uY}>!6S?RFhV99E23qTpi!IV?>PL#'
    '1H}^qBmKT5OHIKLo&XCDc#|Bx;yo!6SXNk8)54=6nYbe3^qjAd(mVdp2G>8n;JbE9Gv3wwf=brk`~8C*?7Vl`qYe`y@yU;F*YUL$'
    'Cq&w3X8Q1chrbGUN8YYTAr|vGHiAITrq{kB&nR*mky6@9)sAj^$wXIfd5jFG(&Z&?P;g4zJD_6zqj&hw{|)RL*!L@MtLfES6X6eE'
    'WizT%kJ`K_5kLITZf3-c)S=`TEo8C;%O3&{oUE;CKd;WwN6FQ)y_3Z<Ui}QoUP+9`&$j<|;nrdA!4Cx+iUO4_Qkas=So;GNB5sh+'
    '4jWiebmZEtA?+{nRyR5?V2M`&1^E)@9Jdq#tRKHsKk1n+%e`>xym2_LpAjZV^Qw2M4KRv8^O?k#0zan#Jh&&$i*nW$G7*i>Yqoi@'
    'mIsmQ4lqB4$Bb^Z4XMPkeLArlM();=iC$4A8tSRq+PQfOyc`InlR}2lB92TAu)#7tvlvTaLo4VnLPpU72I$wA3>DDE#m>HVnoS#J'
    'zw!TKX$bMb*G#b|*zdNwijnF51ArMkxW{{o&Wu^#^Jd?!F$d}Y)_<`oAP!?n$r4Zh-hAp3S(#8EiH!zJURm7<Bf7q)?bb`Ac#9rW'
    'zY4kl3FI)AX>!ga)Bhx2^0~Bup1y`y9N4PkablEf(IuT?WQXQ%Mk7y(YU{<MZAUqe7|*l=1B0}dSE?pfQ(f~m8Y8;4<E*&iHm4FC'
    '5oS50$Wi}JLTaj+@HsQPE+L&3O%?tQIF#g`Dj%(Vcq`aRf>OI$>6c8dtLq_fe0f!EcOiv7O*!)!%oi{c88Xx%Wx@2`N!&r@DxZ=4'
    'BR;qN$y4$^D?y|bz(M$HR~k<w#ssmRz)KI=x%4f`_EXW8&cplu7R6M-w`ld}jFCxfi4n!U+A9NBcM}cmZmE;t%UyT~zR}!CEr=JU'
    'h)%SMKb<2rfN(z7m1q+s#qSE}iLzS=^Awf|%oV<qPX40fA);{Ve;ndG?_U%vS9wg^OJZLtB4*7g(OJg@Vw5$${N?xEmHg4;4jrlX'
    '88`S_YZ#`{*>E?~Uo<xg-DIQak^sm+8a51cLj2}dR9d@tP?qrC1Aj_X6%AwV7eWm~y=5|W7f?<YY~yi~rbEpgy2lWRAkSUzJ%9Po'
    'DdTZT1Ovv&-)ITyY1(R4!V4*rN#RVKW%zf+_9mVM<cR6Hw7@||-Xgsd?0AZIHA=wey0Sr(wJ7v4Z7rGi&Qj|De=7U6O4*<TvNYrk'
    'kt@oYq8Qm(&q+0yhb@XocRw|gJn)Euy|O6zBQL-Dgq`(ne0?F?-SPEAZz0~)iHwz9<psY|7{re?kVq?>#Oz#G28H7HJ-fD$uJrzm'
    'ienJE%)3jxPHe7>sDhR1xk!1>G7%E=qj$mCW!T2?u=5jzK4gH(eh$p^NWJ=uh-4(|JRTHX-K=4@^hMYJ$zKQ*Hy#Lbem5z!8}5dP'
    'VAWPZP*gV*1=6GQa}vzHFk7pj<|C80()(gKq>Lqmxe|O1ws`!wyxDtY$_;(B^Z3i?9Wr}IrFhPR#Go|k+W$S-z6Yj=_PI@!L8X%g'
    'E(vBF*n2iJ50DKQ@w2VDyQJ@pDC#YsvH1@UU0OOOW&QQNrO}XER7VK}R4K0+E0;Piv|cDm_>JgQw8wH}CyHW1ub!B>L^#t=gAfPC'
    '$R)!iNuksDdr}qC*}@`84(jfqcc+YkMy}dXH<om+lER4mM37r`&EMK|E^AKxa`*^Qd?)+e)iJ_#DP=9U5v|p>^gWsc(PR7uMP(@{'
    '6A9|qH_(OxsY8|ENQG90tdD?CiL8^E<UxRES(SeI44WYh0QH~Ytzom~?80{~uzW-8(eU57QRZW9NfYW0=gMKJO3Ka=KVHHHvAe10'
    '>>vY*1yu{lqhFBQYLsZw4gfm7{4)$g`dEl{#WRa|R_u)JCcsVVRJI@>lj0%kSeNxX3~huwwPIZy7X-+j$-JvRxv9c16iM4V0{;o;'
    'Q)N-rg904Pt@$iDE+0gmrt8d-Z(>lg8?S(9_NnAw(HPGlzn5dNjvaxRdrCPwn%sbeoM3j52V*88N>R+eW+QtA;ju4%djT9e?cqlw'
    'l+gkA>r8c<kvOypvyL$CHu{chK3tw^L_FS)K6T1Ej!=szcTl`=ZHrqO67=1_9`fPS7|qI-+WH2QB%t!J=BV_12+TLfdr<M)vUN|9'
    'yl}s?s$lxhe_WaHzB#mYJDlOBe1KfB13={XRgGx%lHZae5e=RRNfwb{38i|`n~D;(*-#G5zN9C@mRbxpn?^W1Qq6QCL6LaPN~5c~'
    '_$P8Chp&B&=3t<-cbbw+KgfSg#}&_Xs|24HL*uhA*e?{E=4HoU<=F`K=L(-S!D!?agK>(rs0mrYLJTV@sVLa|2LOBkI1Ec(<qm-E'
    'lWW_bX4`2&om)swcX}EFHQp~pDyqzX3VyY5G02k4Gk#W<Tmm3ZmmrNUp;f=ERQXFmLfZo9U8uHrmH;k4&(@BXXwO`1Ojc^sR-I0Y'
    'Hu@1xZ?R%K?P|TvjV^=(R!ld5Z&|Z9$&<&2OS5JinY<oJYxhY$psOJ38u`A}Ksh0u(81VujBqF6(5Z9y1(<t(PU9*UfSB07N3NUW'
    'I>0(|;=*mnm3H_84XFyh2oLW14XBx{Jby`MUyp&x)4!%_{<d->2T6l-k`OX;q7aDuAEPs!swU><j`xyqbb}|I`5w7*m_sK{4-JwQ'
    'BJpBtP!gr`UMMcdDPps+rW&caF*p>po8`0~VU!)<g7oZVTgxCuG3ik^^bL6D%>C(yx$PqEfm7BV=>Mi=+}9<}hx|~glP*;+F8(|K'
    'hbwUTZ|XK8nolvfs5&5!(5k*Xl}IlYX0xB=^AT)OVZQ>ijKCk~_*gZkyEAS4LqJM1{;)MmgiL(#sYe`wPJ-jt^s@}`gkyF#E}0$u'
    'Caf=kQ|Y?Gp*2mO2L!;yB!&>Nh0PUmYnuJxHGJ>@5%*3G5$}3);y6FhR9WI63WXx?xQu*uT#(WdsJGQ*VLjEm=x1f-mLh=O$TBsP'
    'Io69XOQ^8vA+CF{FDP`?8f{25LDX}&c(6a293nDV<<KJ97-IPe$Nh5(=s2yvoD<s8Qx0@3e8AeP4J^se>@y8N4lxF-S>&8&RvFq2'
    '9|+c)n)SLnQVE{rJZq!A&MF7AQB&loQu{8S0LuZ#NvJShFTPX}(73Xmawj?2!H<huz4;08PpE}&%><zish-BZwb>I|i+I=B)CmwW'
    '=1P@f39Wug0qAgGyT(;cpMi=->SpQ*0LMAbuDvm_&-gLioon6>x5C)N^69vpFt>xJJ|T*O+uIQL(qXgF5$Qfts29`2>66K)V;c&!'
    ')|nz-__6DQH|Gfo{c_&=f@}85n7`<wl!+~>9QQWqldE6CCKuidH|fqW@nV)>cqtSAFSe+Xm8mfxj3#b5Sy6J$&^7cj*}E_HJv_Ml'
    'kkFED_m%xDe}7t(cI5K_P^2mHF4<^(@0Q>Y!?3%p*X8DN<<hHbAyfclQLPNKh&)w^!cJ#<-6Z37nnVh2)%*$T0e_%^yZ;!Fx9RTL'
    'E=d<2>?LX{-9`~hmAgyt&9G!|oCcGQ!3)b?KgjVK$F){>x8bW6f^se{Kz<B29;%1(r5bm%T38E7m!SDp(`kE0p61g|FZ8EreFTL4'
    '{cl336YD*Tp@r((Mk)O?t4W`oR}7r~V0ld_(1NS@_&+RREcT9U1xtCBsLs^j+A3}5rOIq`#*i<Y1f>+CgNsep{27K8m8<TB|0i$2'
    '%D&B)!%FX!ZfS{LGb@|t_{%N*Ap46ZzIZ6kvS2TU>RrN4W?mF61+wFDw=`sMelv7Pdgv9y@W!b|dgmexsvU7`_UyUEwDY$wdljR8'
    '&4P0ryp&CUU_i^lO^l|}!y!Jm$A+q*X=YIabbnz)Xx}y%LW|gs@e((G7TmyG@k{6^>>a*z$ar!^ZwaqtE+`1yx>GB->SO;&R4j+='
    '4$bGu&Pe%n5Zgh~%AM*GWueE-!i=_PwU-;!&z=74H}DoraR<{lpy(vifeo7!Q1K_%20~#_HuM+Y_rkq?^qBqzOV%oJn#=KPqTC-Z'
    'j_@?Ag%c$twii|gJi7EpB(lD<t7)coH0nrE-0RE)?;W(o$A0la67ow@@5xyV>(o$}$!qmyGEDD3CCjIs48YdjAy%OO3H8qFq+wfn'
    'cn6EX6(H{~DF-e#H}UOB!Q5Zf2Km_VI;@O{w0haqjg8m3#}XXAZ0+b^_gn#rt0lasAa$bi|3c{NI~*u4!SJIhjANYRC?F{zYb}$C'
    'iex(hBanPP2mMJ9iqQ_XXMs`q5tfJp&}z$Q3KDOCI5D3dwJJ=<58su`>c5@?8E@$$FAZCSArAJ(444MU9QK@#Zv`K$G90XQAalp+'
    'EXmBgvhRO!xpeCZ3|L)gAs+<%Qr(_)OTjJEMcdnz_}ZYMHdjMz_5!ug0~vhQM>Of=zft12<(T7b!l4wmqfm6gvZK;;$iECZrUXi^'
    'ov8*|9?b*j#Jcbd-G>V$_ldf)3Va5{<!n1a8ZAiYYz)LQp&DMcgs{)fV{FLb)<Qy){3_TviL9~0eZ?Ihba<@SvFTKh65$6FqO{=#'
    'RaMam{^2k9XJZ=bB;*V#wX%%)NSbXshDy><7h>H80c(kQSicm`v<!1O>95J6)qX7beOR3gw_eilNu=@T&wuFS1Pq8FApCDDsFBCB'
    'Jj!mgichs$g(U&~UEREoKU?^H-7M6*8bMf^yjX@dgVJxw#8f4zB|?yhebRDz;NTK`0n1z46W4m)3-`|==+Xx6KzU)~%AS$(dOt(F'
    'N@UYdcs+is8%{2#NfdHMn~@KezLj&P)#$UWQ)mGBZMx1@ZsMw+_UOudfNT|Wtbg@{AV$fF)<C8!h-^;1%Dmr$_(){C{8wlIBr1Em'
    'b(fJx_k#j0ulA@UN(-@iTeE<9+V$Mg&gcOLtuq)D=`thGmY~tlEyoRVsnp)=*Z^kkiP(CzVCmG(;TISpo)>PV`o;l#;G^73<goq3'
    'r09Bb6`44!6-Bds;`{CbM?=hXr6Q>)VzboBJOQ<6LuRrb?E&_Ols!`n2m}}S?bNTG=w*u~A&$tWMLxwYKx)HN&ABGK%%+LJh+$o?'
    'yFsrZ5b*^Kl{1t%k#QDw>_;}}XT*NrSYVaZ98dI4#&J@88cHz^HKc{XZFuRCvy|=JPSh#FnKG_2VjgEvTkA-ZwIah?zk7()0u0se'
    'RqRAwXnxaV0mBgsrKWgJf?-4>v9;rKgVzkzD{`v{c*!c0*)C(8O6yt*Ch|%qN%wSZP=i99M&C&Axd<qtdttag_flLpF6MeCro`SJ'
    '4hfP7t>wl>$st_Yx&w8z5>QHpb*nK}qd<U{tS)Tn1`Oc+>$Zn`apG708Yul)D*B8}W{bi`V2QgMc%ITkL=`jLD4Xjt;@~mE%Amnn'
    'H*3Vd9qG<HB0im3;eJ77>zP?%h0FaSGvz#SlLFkF!kd;!?NboN81%YQEM^VWnTC6qDw90*awNh2YT^BNFG;N+OxCTKy9dpui3%t{'
    '>_QgNuadRLJCBRAdcBVkJaWFL;zGAkI5n3h`Y;T6QYqVi%n2iFA@8+Ibsg=F2JSw~6T+NsZ)yl#DRlvOgG8u#w;UU#@2kiDR2OQl'
    'G)OrdMp?SH4a}=G*$7J}FXa`EddE&bAN9Vs2lu5(gQVYKOxS~?7h{zEp}?faS;oe`bf1!c30-~?!&j>Tza)iz8BXYRjUKJBJV$@<'
    'qQV?-&m^Td^$r^>HiCQxm5Tigl4><5&vp__n>=Ie@$~Gu-gyy@&lAew^ZJ;FL5;4^>$@5~Y4n2-&;C4ZhONdS;IPF1j`nu4m_RA?'
    ';N>4HMLX7FM^E;v5F}Q=p<$ux(%DDjaS6gnsv_hwq^;%vw+qZbQM%$i_CH08q~}dyPnpCLv)M}13cT@b0ZNlL`n3P@yl?<eBSmmV'
    ')9e^y$Hz{%C}3ycVU`%D>Mv^Hj1$c8N$c!LXjd-6c*Q2c%IA2?EUA=e-~C!v{BbyGkGbo3Ro3;)ysjm%=IpLAe?FvCV6nYs(RBMx'
    '@MPnE#`0vO+s;DF0ahaI%9#Ry5?A|89}EG}GO58Oo<ks+C|jRAoU&5M9{%ho9U`E3;)Kk8V50a<@@(&ag`~>EoJ@=Ss-`!ltiRi6'
    'rdeu&j>o)b3%W}Z6><B52Gn%#kWm&aM-eUaIPu<&LZFt%r<fJ3?XsQ2A+Wy=tv!J`RD%g_UCh?LKaTS%cZdMaOK=3gWx@c#`U8`1'
    ')JpK#66uoT&W1aVvp_$TDxy@&_5b4Ea@L}zTEZD^VuHt)O%iK^y)3c5i;W*1TdhG0TBEz7rL&L}u5}J@AD723#8K`5d{bz*Kh(kO'
    'Hi)7|ljCEH8Prof_%a{n!nGTpLeG#@Yj)`q3F-v?!!5UMQj4+)IqfI4ww;V-+T-9h4e;!tJqEI~0zmwjhp1rEIMs|%l5$+hfZ3OM'
    'zKKR^{F%ZI&bRTZ(nH~DHk3H#9R1#zqcdyG5+o_)(@GzlF<C)L0TQvxp4ko3Hc9<@L7K<150PO(>tmgM9sUBs0$VobWZEfO<Nmc2'
    'EvgjrAa*@7GOE>Z4q7ZHKHtzXMGE@{mPp|*w^R}<cH{q5X!u!DWo`oeI~%TATJ}E08S9)gE_=x2xDYE}w~^MZXxB)x?0pQ2+pK35'
    'Ih6Nt6ZlXU&x(+NTXnQZ-frNSu;kGzWuN0$s|FQ<y@fgJ1K#iR&vr|z(jh8SaQ0j`YbJH89d(H3RuHK%)c+6#Ud0AkYkiBEwf|mf'
    'g#w;HF>b_*)09sAvmXP5q@7v}6!V5`>7o6}5DP2%q9bHqbF@2<qBe6Zf}l8tu{}DxqD2vw_p(+@D!3}V<MaYsd39e-M6)1ADsfS`'
    'MGIPvZCG=I;`b3RoicYXXop5#*?*ty=I{YWgeReho+}g+R{ikT$6ayHfy>Ra_a(X6*Y}ZGdrdB<A{7+_$9;I6AD6KYoQ^i9yIAGC'
    '#}61vCQoSrcC+;YKFnS2_B$t;S-(~I<d`Oyt<F8~gQ8g^z;hy$l6ZUg<S%a^N*rktVrI5U#ss!PO`*l=fi?Kf-V<Ek>mS;B*e0T1'
    '(V=jC&0-T~Pms+{6ZC<&c?bj{nG5W9GTm612!E$KWFt$4d)WABS5R;esf%zd+BF8{$LZN>T#;@pNQt1#u|)TG4$*xjb*Pt}-FN=L'
    'HzAMEA~1>fWrStvt5~0x)BHA@^evv>x}V21f5fZ&8u$L2(TyC{WO3w*Uu2et!!|?UDkoR+j#@1po%FZ1IZ4%3pN7dbX2(i2uMdE|'
    'HBjfvG<8D?BwwLJ(o@KwLsHQWhHO_xbq6P!P2x3LC%S8Q)Km7q@$j}QFiUWvtSa1yXU^*fLJ>~{_$>iESJwDgsJ>Jx+&^QtIa;%}'
    '9A*zzAWK9<1<jIVW+=g;yNq_y4)2`+9@ZD!!RPmzR?6lQ?;@>LQCj0e4_OXXgM2Hfe+Q>w02c;w>z#dFYj)6Kcu&<YBQ(P&NA&_y'
    'sOP_>C6iZZm_`TJg$UKhHc0jGSvYE8nMJ&0-3c6`3G<1PIxShaYEDVyBm3QgJlA$gQT{zL?9ZG65a$XEplYBh!y#bvpDFlADG%hA'
    'IEj1Z^TwaGtL}o11+sx)<aclJI}eLMTcx;-x|D`dQ82G$U8}Iy4akLou`pHp*VsUknwN?v;p~bl3B!o?Iw`|r1Eh3wed%s0aEpjU'
    '7+B@Q;h_>t!)xEyAhaFq{lEauOcw2>&o$94KMNq|9n-6BOCssEs`}>*zl<Y#8MG+bm{Vmy<c!wSPPh#H2oE3|T=3XTn6&eOk_~25'
    'wXtdaN4bR_MDE0fVw-(_k5}qq8}e%cd$L>=Qp{$xE2P>bC22qCZR}_|cO5r!!*_-);ho2bvEVdjfbtog5`qXpKg0h#$nq7fO~yN%'
    '0JfM{M-Rbq@^j>E@T1s6_|mF#iu55HOung-Bq|d+dR{<x6=Qh{W{Haq8k}0g$wCpk?5!xnn1LeZDwDL$9ET>>8Mm1~K8+hO%~d5k'
    'Un>uOq9`ApbKTD$*2(YZ!f&^YmdbCF=Ch?60<CBN|HF7!oM^-+*qp!4+MzsCD_&ng>8Ek9R=XIyYR;uG;rfm>XL{8NR=lg!sxOsN'
    'C$edtI*I}xhahqZa4~&S6*N>G9tt{>Xb66O!-88p7@x;+Y-R*sUKj11b;tR(Ra)CM5m}RP>btf=oCNq+>QZKnm%|ki1DnmJZCleu'
    'G4OKOb|-+63?^v97)wQS(6|md`Jx<C4Wzl%HwD~L>hNNY%qWVN$->+wGv7@sPzl3>PLVfG#-&FDsr8S2pyz-a$4HtDhs{(^=+d;4'
    'WW++UJE71P%b9bf<p3(IF6?16nPI84bw=@5Sa(~nvMi_sCD3xtD_RS*=oo`eWoi6hwkmSK?-Cc~1-Nj_MI<VeTEKsU>|;jGhobF9'
    'vi*S$|2~_6^dU#V2!sptzBLI)PQpAsKT>bf5&6e<O!#x!wY|51{zkLv>@h!(pD*81GH@>;Ay6hS10e^_0j)Oml=AM$<C{a4RldzV'
    'oe;AdSyvgn!pw>MyBuhgBG9u?B4jCdNQpnnkv2^?aNeZlQ7FQ}p*e0AJ;Em#8btz&lLl%|W<q!yjR8enAPUk>v{MnVi;Bkw^~NCB'
    'd{$Nm4UGp$Hm>>W+Leu?UGwAJ#ww(AX%nuQnv6+;<*TgpkJj(U)L>Iy@K4{nJQT5$<irNQuKcI6BFiA%#H&Ro)zvzo2rPhB{bGWA'
    'Cnl1OB;uJV0dqNuk5=3)CPZ-Ipp!51r>|NhAVny)xczTEKG>7cP#-vbZsYt-AZ@0f+z(rTdEW2>%;z0jzYKJQmlU)(vb*snY!uH4'
    'bW5O{I&GC8*9YD*y)f22#oQ^wCxK4Z&J%=wS!@N(%FFs;nG;jb?ZNn#`~ku+)7Bu%npW(-6UE%_L2<hV+@4m%T$gcs<PMipLH?;y'
    'M$>BvV>TceV&xK}v<}uJpVL<D&%{9KUC(t~3O@r3<KHlxe)@UgVm`j8cNJjeLMR8*YW@)_v^^O>BC4^N%;u&QWAB<Nxry-@qUFA&'
    'JdU{rTPW}JGWIZ|wtFe7GZQ+6I{#K7CiuvPXeVQN93NO`pHQI!#ktEe^I4-wn(^lU8!6fwVh-sRA4M3DR4yzCknZ!@|CLciz08w8'
    'nHoUn2mY)aUn?p3l&B7jzilehidh;bUw-+9cJaHlt=%lE^g(4A181uQkMmQNx|Epu3|H3z)CID_yHUO7;pT$lZNc-AsLZkjzJvG3'
    'yOk!t;hi~);Zh0xvETpr(&V;P{n<91JJ?o1|2rbyCRuM1ijD7jnjt`wV;FnC-UTA9eF?6c*M$m&t#(4$&a)C7(=&g)%L7JaBJY&q'
    'HbhI%;LgT0Q%JX1vjBVY#hRS4LSttMl~@f1*9hnsBr}~XvoZNWBo-&>vck4DgSlE4e!g3s6B^HRSQ(f$z(9roA}^+IGzK0?#n<>y'
    's~(QWc?Vzr^zh9FPIH_Bb3e{Wmdm&Tc_}cc=!kmesZXV+)sH1vHFt;g%B{D6%HTt*P5R;fjMN@&-jY3Ai6{AGuD&BXn*X`o-i&pr'
    'FZjgyju`9-EmlwZpYRsBpFHTk+wCyJI#Z^@i?oZ{hM{*fhNvfo%qGu01Vh{N<cBFox-G1VYCgX>M_6{bc*DL0Dt83iD%e=TNxTh='
    'b+EBp5g$6#Us4CGMp#_0+JpHADbyVePCQh&ZOYgEngUA-KtPzrYq%iuc58nrv!U?J>xPjUx_-HNPU(@csIPHdhMi-^nHf#La+zFm'
    '^{za{AA>KhZVC{RQ!2eg0UgkKKSs2(lYbXH%XE*SAzg6Hbu$wKVgS?Zf&t&k!-lecNJyF#EfMe)sQ1Wu+Yg8Esi#YrcsF%yuh7CF'
    'sD-x8&uZog<n=bw76%j9`2l=w28Js#``_QSU#l-t7-1Q)4Nyiq7lctRu6g}k`{7ohS|>Q?(oPkbZ33K(j`ikC^(DNjw|&X4z}60a'
    'j{G)REiol$S+D{ZexWc%DuE2)YNk5g`EGKuQiS(?OXdujx_s$d`S7yKhsuvXie<S_fUisPYjosDkEZ&)dbW<zZyh#Qyp5X{$IoRj'
    'cMkZpNk00iRr?ouuH?iRo^Rfgix_`B;XbKQq8{6gxK%mcv;B*Q^G2$O<088R{Sg4=={s&>JO!<vE;_FntCrIxZe9QfcC75(^Tgh5'
    '3QjSdXIrm|Bs1FWM?>9!dAR3A#DgfKc+4<TX4o1KBb$30ggOw9Sph7XQ(DTRwA@_|-w?bUpfAoUU<RL%diAw|^R0ohs_2A@vxfXm'
    'RsLkgW~TDO?ya_shrkO)d%T9tL;eL1P&r3!GAPD+UmJBU(`!;s>HMsJUMgQ%aN}$%bTcRQkACxFgSkC&2yc>U*T=PGK9xHF2oLm_'
    'yJ%-IDU&n05GX|_u7ewuhyr^T&-(*gu8kq&o!BULXJ|Y?V02Zf%DP~O^znjO$DQsw=h+0^GJ(QVYY0ASfO&&;OkNsmj7s&MIA{{d'
    'uThe*o&wp$xC;WBtTyo>)sft_h}=;R)k%wgSe;yGgnPGciu3Gbw%MPsXI}_)@3$;x8&FEL!e-|2k??6<IV-V(Ow=lnCGe_mxm!?J'
    'qS)!<rB<NGM<v{1O81DNOJ~}pZEF|~D~DqOL9UndvFuyDm9~eoMPgd8DBz=EgEz{>4gFW5Z*Yk90-4c`jPUgB$Nod6m4cB^Tim4M'
    '&lJ@QwtxhM&Qbq2(uiGut;B%zVG}FXVEA1e;_%JZRKZ(QLfHY4psBfqL!kp;IK+~j_pJ<L>GOG(USv>4j$%SH&ZHSp{x@;0FOs5P'
    '?OoiCpH<$?Y~z_{9VRZy(N-FqB4HIfBWsT3q2Df(ri}~~T`aMHr(Ck>ok6JxTF3XF%Z%1H3g*7=bHF@R*@lTZuu=iVm2R>hCp$<t'
    '<{+tzP8|*9A}th&EUGTnd4-Oo%o;3KHTFMuJ}*T?l4G1%L~{(-57A+Bf`A$*Ae&`G2*_jYz+#|W5DuK7(L;geLLBJqPPe2est3L+'
    'CR2EOVsn^98O+&NwGi_)CFEtt5xHUcux#mBHlZ<VrIPoX`GH>TCDOmcUtT3HmO7);V^yw`<}w-1P3&#ot=f%?XGH@Y^_?)nXp#U@'
    'TU>ala7Zs1BP{v`I^pvMAh&MX?1D`;N>bLuar$Xl*<xw^H6Q~x+|%e=6KZjqpzJrReoiP0T_{D;(6&vEm--ltFZVV~f<I8s@9>=S'
    'TNTOB&~8sgSSdD(5f{k9X#k{bNt#6t1k+j&0t;rz!DU|r9oW#)n$9OjdDk2Dop3J%*f=_b!<}Vd*3tm&uI99`tj_l%80hfis)<}`'
    'n(Le^ANUAZ{3+MDkT_{VWsfewJ0}OH;0sA&Pr^bhtTyjQGNgKq*=|LXSK+lv-<55a2JOqolQhGa*0$<cY<Zo#ySTzuD&37wjt=H>'
    'Au80l@OsvWS#{<y0imr*qi$1TltS;Kq58h6iVt%LJylJ;M|gcP%7)C`>2i>TY|5Hu^M9Y}Hx!=Z`u)WgM4iIi3iA~XR6cl1V_X~M'
    'Nmp4I8!sI_Qtno<Ww=m+1x6U(H73c?oDJ~s0)|pV@BRP?|7;)@wppG5qAwYTnGzN-(Oi}3ujQs|YBa@|E!=-ai0GsS3}%KyRA>P)'
    '00L8D-XWfU?8qQ>xl$dUKvx`?lgdz3@XdEnY3fKyL<#9HsE!x`z%aGshPrBOwCJZ!Gj~bt>%TNx2G#+Gq6)<rXsRAdo&$Ifu!bi6'
    'rJ<0o6q&}dP9|7jx3tXC9xBBp%sJN>l+Q|so%=<P+p=2CQk(9`gvKQGEB{noa@;hnN45HT=IVB^dLw2MQmX(AUl>i7Fg7hwpJxc~'
    '$1sP`znFpXs4qPv-F9Diw;_>_n_k)Ws>RkkSTkkR-ja#TJT*AFi+K^bdCvRVl=S3!DUdVWn~SBM-a)}NI9Fcd7|rSoK2}nbG7yR!'
    '-@T_If=0)!$paj(9H8ZbtO6Gr=|W9Nd+^x&yb5IaQjkqT6GJ7H!g-SXNEA7{)9PUK86l$cIZ@%)bsJ`e`}WI-qOD^h>~tNbPle0d'
    's5yT`)4Y}ut&upL;zE*Ze$Mwtk%fDHR0yG}k(VF<Vn?Y2;!trIJZ861yra*~hacv7%7?q0{;vuS%)nbXtzB*{<pJ3p$P-a5A_u?3'
    'JgOA<>n6mur^~vB-@BmZ|Ciiwe|xpgY2xGJ*)ax9E^8izigLO%sc6cJe!iw(wGoJjGgWa(CuO}+Y)d(tMwddwM{J}Egaj<2$|^ll'
    'df+d1#emvi?q)(A`HNOIOVXLtSmHbAjlPi;;mP&cyd4%!kHHY|GEnNjw^g`lZDUBap7}$E%7t{3<6Tz>yNd~ns(aO|{jY%GEkGEn'
    'Opt}I2iDSzAu#M&>4;uJ%>%BBnh3VQ`_R1vF{A4pb=8N2{+cb9mTcBkIBU)92Zavz?*rOF3HSC=#Un?B7)2FVkh5w=XK8LmxT~yx'
    'SwHVyH*)?3ol2t@muLwAlg1~zl#En0!}o;otg5@D%>yIGq5$2n8kP={r_WOse@N<3wCXRvoSil{GSt}u|4DVZp2!6ku``$wI1SSu'
    'TZV@;*D_%QL5F{pziA({E4k|Y=Nb`pys&<MS7vh&nP@`Gs<kcxS>X1_xsqnK7xSg4Xzp-aTLq5U`PBFQdNTXdq;`DBtRcmkR8=H_'
    '(RLOPtyv^}B)F6VV!XhL7rfFvnZ|vQx<8h+9fjhbjZ>!t*H>)`tkr!B@--Nyg1;f9jZ=*eL_9PIU8ov)If9iZ{12RVG>yEu3sUjS'
    'Qu!6gD~=o*7OgGOTvxP+1Wvti>G)3A+(kx{pp#PR2{#9K&JJN1=T>D;@tu&+Na`mm+K1u-9mTfmM|d0kaH9q}`B~8{AyoR_gx@(G'
    'DmvFNx@-z2hFj}F=pzd4LQJ@Xf;=pkC5qNI!D6#1T*TJN$0;b=*`qD6j7byKoh@+j7J7^ez?#;O5Rh^DRuPU-3n!9Eloyx;?sFms'
    'W9Sqzp)Rs@zaeO;+WjOPYtzXDWujpY0n2ce7}iBXW7{*97RC;uA6~$01;|`ihyFW2(TtC)^nn1EQw~INLzTNb&HgNlbZ6E#O!iMe'
    '^wLP5Zi_>hL$}>Melml(+`gK~`%1=0N;c4L^)Mp^qK_5eE)wB1UeVh<C;%G3-O+&Xg3V?q=)H-_?w~z&OKOD}d}${8*yowvP{heG'
    'Ng|Cj9i$X0o7?LY(~~igW{-3_=C=${|5b@dx20-DA|MpyhA}1)K(Ab;^vujv(yYL>wDGy?&e_M42au)qCqn0!p#0|zv5@ocBXlqr'
    'nb+X&$vYsr|MD5^Cc0InZ>WJ2D;_wXE$%-u>bUA{V8;4H2RCw+5&w^!NZ?)-VH<OxlCQ9bLD4Oa4e9$*`_0~eu)4(e>6Gp8Hly{B'
    'ZtrOTxF&_sb#3tqRj>{h_^fEw&*;a@nKw_9GG7&bcL1yeGFTw%{nosWj%uHuJz8y#8ptSA4s4Lbz<(jZJyFDzdoVghVN<nv#~rmz'
    'wlcfV(^76c{y^i7&XUV&b_5kXR^x{VOQ+L5oy4T^fC!kV@>&rY!EpLv)zM9#e};cSWFecR-3u;7VS0~2H9i|NBe3qL1>S%Kt^2Tc'
    'VRY!u!w!N1muN7%#!<v9QQTZJ{_QgR+_^U5^XbR`wmVU%U48)M_OPlK&)%xy1|6HkvMEV{r_?EpX(>et@-M$U5wYXjmn1inVX*iU'
    'KDmf52Xb7Yx*y`{v4dao2rw?ysh*X>fn=Au%{3Trh};IocP~=h5f`mVagDL{f<zRiVu4H_w1z}HXPcVc&hO7n=~KZtfx6Bfhul$p'
    'FfHI+x^57ey&nnv+uA*$w;juE2J&F7%BsDNiBFB$(RX~KzhU5|xH683LemPrNg*Jiad=42vn!J~D1I`hj{Y3e{^k0f1ZP@K7o&9b'
    '=EI<&&Hq(arCQG~Y$p*V&LdsG9GKn3VG(hx{Y-GQeX5`gO0+{fzX+Zbsb4RLW@DVk$D$s0Gh3%0^yL5kcSWR91V}yHy-0WCwWFZh'
    'z@{unj;!<J(R*k%UrT=+rCBl>VaL4y_`mt`$@a6kme<gwI+6NHjT*tJ6zH0JLfpeu+M$5%so8_HFEp83`NlxZ6^NA8*dvziM88WD'
    '0%QyWzEHF3p{znjcvbeE=9;|YomP>6LdqkEvhDHGUm|Cf+;th8*NV9nuu9DW#VMF}V(xtfC<Zg&SS;?0ayGa2%PkC8DQ@ay@5MRs'
    'L4GR3H4VrEzj`9GJ(3>dHmOFtF0AJH)+`gowhIjvy}@+kWi<Qv6O3uG7C0heP(B0EfyNba^bG>(T@v{jQ0I46*4Qr^T@H?SP#mlK'
    '!CsU<J7~-cXGsO<quUsb$iLk3Jbv0swE~|)BiJ5;@@}b$5lJWP@fvQ{L$XF1h!xf$%#V8Zf_B0nSzGfd89Nk_AfoBC>edF;;GMyA'
    'YXxt>#%g1#cs#-xDZsc|RH7oZ5<0$UkptSaU_BgO&aZ_B@MP1>5g=N?k6=hrN7}v)`~Ak{M>+t`>y8+@xeYs|&afBjarjy=u9`h_'
    '84s+}4(Bdca2Weo3X0#22~v8otX6j@Nl!d?W$n!Cfkyo<t8f|oZ;iV^+oMO8!>KZB`ZYclXIk9n5d}+>6jiFntqa{GfM!jpT@6%K'
    'w52HH?v{9WoDmUk*gv5+0FO<n4f1a~`xo0pI@=52$^jR0V;z$aP$f}hULiT1Ufa73AG{cm^L%9hUH|c}!2X6$e8L3VA?~a%_z6a^'
    'ZCKLZPTlGJ?`d6ew6xCT{s>Dk{_$$IzVMp>Rwz=rGC&kW+tj>!%~nC_Obbd+zXju==mE%gDFrw~(mRDVRDE!RL8u?tjX1H?I*-#m'
    '0&cBkOmdc04gJfDNefgwxE$8~xV(;xPPzY=nPvg$S0TCBh5l1kj*@$kA?zB$3NHFu99)ICGWlNCFN$RYYTW>aFs>_BB#l4#wUx0l'
    'Tc<htVvBu$jZnqn^}N^4>X4B5cQ*bk*ZS7Ia)I8OtNK2k`6>WiO@Muti~_ThY(jvj(r+qFM7bF_J6Jk0Bx{;yL9yWc<d_OupL(gs'
    '3^19<6okmUfYNK8iol7l-;y{jPH1s3e;0f~RLrie%oaw-MYk@XwFos>&#p$Py(pUWh_Q6%2hnLirlZowA_QzGKsmlhLhNj!#>le{'
    '848<9C+YLAC|z_I(+=x6aRs7%sokO|_`PoU0e}0J8n)R?+e=Vwt*#Mt-mJ*m=Nt`<)$KPcrB^18O|+RA4X&Ygo+oRdb6MF~8vld>'
    'w1Il@4I)6PVeOi6a`2<#vUEoX=?c@PbJC&m-|We8aPxGgr+iiJ&!K|c4VZmYRd{Pb@3vVoV}b3zIl+axukmq((>87!a?;yv6N(eO'
    '4BW3uCsXsy+i?~;WS$6nQ#C$H4t=3j+)a;)3@e@IU}u{?b`I3fb&>0^LF>|s!a5QpE_f_Ixd$oto2<wJe+or}F{?jEC__!NpkrwS'
    'j7%Usm|#ysSTyaeG=(jeK$iY;bw3aK>-AcJAqV<6lV^o`e<_QXD-y=Al)7&0AXu*Aw`%l;aINv~l(b8E9*8rL7FymuATyT<8mfHn'
    '$+$z-g0F2Epy*(Dym`%Ki1Hc~Dzx_FgCh7kbCJz~C@+#ZaI(5#7$r`ljCng-IHWk7e32NT>mkOF3#+x^9wJc8t5gXT8(6uO?gGk@'
    'n~}q^eiKxY3BCaC1(tltsn>Z0F7*dd8@kafC_lTfl|a}&_T(D)^c@e-_b&J?v5+z~W!7cW*MB^|XQK2f&ic!<^4%yv6{U1{_|i0E'
    'GYz^+w*m}~$J{tyo#&3ZBQ?r8ZIGb(4_@LC#hM(ql1{)!LvNHCYfOYyZum~$U?_x~a${)Vp=XN+5b<GO)!-Wu_cG(~`?-t70BoNy'
    'eu#F%RnZ;1LXFoN#;;1OyN82jnU9O6_eBR;MhhPa7_r?yTV5a5?0i5(JweoZ_hV#3d|tf&v8#C<)JbS{v>d<ld}#<qX70vxY?1Rt'
    '@epyI)--5@nPrO@?W3llA!@!xYNuC+qDX}$6DrO<Z%kX9^sRq2m#)|5wG?X2cSlY>WeK}ModJrL$p^o-10uS7irG+guukzOow?g5'
    'R<K0;EOCHGwkBgGP4;|clO=uaQq|oW{w<1^SKH;szp>(9D{KZmTTV6@Z2GR3Xle+ImWy*ldzoY8wKyg`@9Zk^DC%B)(JL}hj)B0('
    '8x0QeAD3S41iOS$$gnNRN0?fCVX2_y@TNKou-#V`z8>3DVtfd4gl<BX<UBCV<uKzL{@AK873iXKJar%29Op)XVh8oSX1=*|2m5zQ'
    'hvQ_F$Wn!dZ*}-HnERcc5u@;4C*P@-7%a<8>iGM;>XOHWU-2e`Ba}-Qe@PrkMSE31Vr3&O{k5t&u6NeJhZ97|{U3TS((ND^cnWsI'
    '?mX(q8%3`q6ar$rkP-iDks}cCf3on1r*!TG*Tyhj`%$m}u(J|mLd%?+Mv%ttE4~Q3<dqJ>d>;V6S_i#v(x%@V()M=7J{amwvtiOM'
    'M#8R#c^(>dmpA-`$SDAYX2)q#XT(YUXYAe=hu-@_&9^zn@f~%sTv^EpvRU(R(Ca!)iE&7wEB7)L%%l`sOXlL3voQy7k1b@$+GnBh'
    '^M92VhypfECYHdc`dE19SxlgSQCUTmBJ3?lPvKhT3F>w-c&gwMXG0-xXVGB|e7&hvjR|Ux^=Z~AjT$Wxo1RX{#5rE+d@0<Q>m#Lo'
    '|D;82Y|mg)5{Wm$*kdMtdJLyfa25o{t{%-?9J3nYPQ|!OBumUB)@ISR-=MHLPeloFAEbpAUocu4x5KjCi-Ezx!aO!ht3+G>!g@#`'
    '+>tf_C0*B1v(;IDiH-GoDjlx$ul~-l+hx8$FLjxRT@fC1B#NI*4n;-BbL=C)CRP}8$7`=dZSFo4#d$XU50wd0NNI65SgpQ1(F^mQ'
    '8WmwBJ)^oWVnI}*4xZRT)N|}W+krraRRYJ$75+}Lo99$C;LH)q|E>Yyr*ZY8s+iU*7Ph$E9Zm=SXuNF_t~ixu9ER$_P3jU@W^<FV'
    'HnB73iX@ZsN0{h2Ru*oOi0}K2)mo!v>htP(HgjM8qsjoGrdrNX70>|s+DX2_rZ(6O?*O%M51JEgp~Q}2S)^dSP^QA3PBX_5A1Qm>'
    'ib{*OU7zlIoo!g|mVp#=0~)#zvCRY;o}c<qLp=7&$*kZvvGn*$>vcQI{ozKL_W~@`8vwf>kBvEfM8o{ob}r>R&TX$jChg%^AI18|'
    'CDNXyx>OG6l`!(pDT5Jl#uz0LiJAQpQ!jI3cmv)JXLP#u_yG_?HRZMuW9*&-r}N>8noNH?a}Wp&3xWSNeLnI-1azcNxMTf5AGX|o'
    'jNW_Dxd)BZbqY_D`kEC#TQ{=2ix^YMifdk<2gRjqs2K<w-ZGi761?CM>TtG(Fes2#1`DtT?xR6KeGK!B)Qklst`2$Lod>$s0FzfJ'
    'S32&w#k_qzr>%?e`MZu?yxD(MI^K@AMb3!*1inkTp6#yrD-11Os@a?XlK7=NjkA@Jl-()i_I2uhFx;|(0ZUr;3)s<k&JQQEiQa)*'
    'gN0dcWFn0+XT#vYhy?8HCuA}ZoOUv(1F$Z%DBo_MFU<0q4WsWf#CeuO0tC;2VY_4+gVbvDX{SuLD!Jk%cCcFi7mUH%t`_u{70##q'
    'C~kmFWU*s1!r+{IO8H;cyu*3E2E;=?_Z!unXCsKpJ4(+L*O=oxr@;1-vc;3@YMmt@u{&=HJhRLy2>_z;BS#_DMYrP}>V9h5RlLsQ'
    'fdY!?QRgtgKFFavaR;h(SK7p?xeB>3C426dry<v|Yq;h1ySy+%6Gh{SM=YkGVKUl!%Bwa!{Hr<s6t(g>0O$k#B)m%B#IjMqvQGwe'
    'xQj;EUB?jL_m~WRb=<^b7{x`jl;u}>u5P;&Ml6jy1}rRyeV9nBC8Qe8YiU(X@`9O-vdj}z?{^@1>(dMXa8}($Qj>HLt=Q)jcqz7L'
    'g+U0u3k|If@UOqNy~NuTs~3#S6a8Z)jNg@DG5<B0R8>A**pkFXdX!a&n3i%iLH4=&JSTlzv~UU|e5L{~#@Xa;@5g)UnMHczC7^iF'
    '6hN;&hyH)Z4j7iB%>v$Vit#b7p~+>;8(IITSYjJwj7$>&;z9)h3z4bEK!awt|MPVNRHiq7<1a2YIQ&Zc{R&PVp9k`_a<J5?mj5w}'
    '?H#|cE@`~cgru!72j;1ZeE$`{t)>OA>cL7!bm`S4NpzY7lye4W7!35*3SOlD-DNSQ#iqXC0#Vjo3Sa#yMB{O&l~4n;XQJ_)sC1P0'
    'i+Ge`a4`LWg+4qef}n9ynFv&?;}8&VC)|rX=_`InIuM$D<K%~7O+PT#azQm{?BlGZg=7?u9xg}V0dnaQv3-gB+deikuk8*tH$m;0'
    '$Ym+XscROXW0^wH8#A)s{7@<MjLpx8uOHnHvs@o@dIS=5VmS26u}!`q2B99V1#w=^k(yF8AZ@0LP>J&0$bpSY`|D_R2y#TlDtO_c'
    'Li;bRsmW+f?x<Ekr8sBXRA?(l^gJ2$j%I2vv&zEG#)E-g_Hgw%gyZ=L<IshS7Rc!buVZm>+JlQ1iT#^5finoXEn4J9qFGaIf$tvr'
    'KLGmen0O)206gC?3((>dtz+CrIV<Z3+9Emyo(y(d{t80vWq6G)Vl*s#oN2k+(dfkcexn#w`J!f%e57nwQn(g<fqK;u;(zMiOXLkF'
    'pohi|Ng(*-g9jzPD}W{w^J|@swmTh?Elv->*IW+HK9;Q<f?dtOL#8B~APU1IT7|#cLpP>r{B0)9={{)QS`Ib-d}t?~@Uo9u{KWR{'
    'evVK!El~5~?WN&dU0g`>p}}G+iqL^~S#ysHiVqjz#py@RU!g$=Oy!`c<uTG-QX-ul=M3Ck-qE0Q1Ur)Ir#S6}^FlC6{$f;R`+-5&'
    't!!D#TUd2&m#2fVIG<)lz{h5|9hDuMKXb^)Bm;TZRelU@R1fX9b?#gM+w#xDasH$(D!}UkXSTNCL#+J6#U_GaWOTA6J<q9mO;X~1'
    'HMZjEmqYD2vGLuhd1<QN;F8a5!bU*Q5<`cD+{RDr2z!b`7pw*1dJ$8(4ovgOyM3~@At2Ol#6rRuU~FaU58jU*WS?+s)tnAHG)n``'
    '>!|&o+{J_+?`=~o_zR9+o60C}>wM_*udqU}CzMjgJep|&sxs!sTZO{mS;B~{%Pk#WiH3erR`+WYUH~P*-|~v_qD~%Rrd27p+`7vn'
    'Wc*#KnAfi}vL<R=oY(p1;BELg`B%2XDHnl<CMEH`6FIzo484mFngj34xsI&wR_up8R2&3P*W^26rbtIW=BD3?U#b#6%6apyq&_O$'
    'IBYa<@I7cju{2#4D1xlVwsEd;fb++J$<I3_v#me9Us5Km{JUWwZr73koXfj+X+dw^dZHt)U&-ZV*5(C8v+72e5O1MY9VzMuvlW}8'
    '^S+Q}H(!X?i+RAU5|}3nh33%;|7vUQJM|BF<TZ>Fem&s)1Y5WeN}K^Oxb6H&Nd^>N@(M@VU0P&>`q?J4KwbaqLp9~s5&N8=P%ZuV'
    ';TXr$evR?-6JrJCxFqI!QW_(d)aALc%bB%!&AR!om-Kf904CeB!sn0o$P;^*h`WSm;-xLe!(Y7i8^zEA2-f;X`#rC9Sui|%3VvKg'
    '>e^LdPUjMFWK=JZy0kwAW;qSB3VAB{O*8M9S-6&`m4^3F@SStSmQdL4^!~cRj}{G*)9QZ)8M()@8WJk-2P`$9E)J3ozFZU<FMJOO'
    '&IsPUW1yop?aA~d(GJ0-OKT1@2C{n#d?U(qo2K$Smq%;gAB3`@343+FRCGcc-kY@uA1Qd6R7=J_#osHq=xT|wuXjqH{{t<NcJ<Rl'
    'H!ha3k->3>wN-ptArFw;KtU7KXMA_Te|LN*xZi)x(YVQ_>i8^{^;+Uy^A4fy$YT#_O{Tt|s>|IJ0quj~f`*a0Ui{ZqboaODjdg))'
    'tnNm`8bw^TY~_1OHV`HS&#>6BV(*oXU63}=Glr_uIMU&ZxoRU)BD3kLDzDEX)16vJ?{*&%Cw~&Aw3$A<h6U3UV=o1!BRh)6acFgB'
    '`Gl#u5?$Y)O4fPkDDg-ORNgqh+OFSviRo49c5NIgNV2dknh%ROTLyx5gGXi4r2^fI_!l&0JE@B&sQLJg%|`F=2l}|EH1~gWVZr2L'
    'dcY&yg4P97r<7H6?;S<VLd}hO;{0C)ebkYpL!XZErrZ8xg0+%&8F2<WD}vcHfXp3E4pnSH-uPA$M@O_IAADEm_S%ymQ30mW`?Ww}'
    'p_d^%gHv>s1H>=IkJJ3o?LGq?J51zb+FnG}?@jIcV@8&P`Oq#2=&E?pGCWUW(jd{*x(CblX4Ase`!TROCb1m>0Hy^bvTJlJ%Yj3^'
    '<6hKW4M88nlZBNz>+qv^ArEIc2U1B(q1dI)Xw1|v_Cw;XE_Zhv1tJr}Jf5tK-<Nk*TqS7At}lOt<p?+94NRdpE+86D@(0tdo&*sb'
    'x~n@FORx#Sq45cLXqA$lsm&)+|C{KeX5X6&=UMCiE32N<f}5dq@ww_w7TO#ld@TQ)!VuXYznuGw!U^rz_V3W6<-4UCn&@?zwy0Mx'
    ';d0gN2gNC+)8<3%C}$(R1oW-h(3BZU6SEgQeQj!l&a)EMLwTvEhN)*iWoYwwx~uq6RMnw&*w)LnX~VH6)>Xo?#XmUk3)$)t@zS||'
    '`6-k9Rp9_71bXkWeissK#;&|9qlFoQ6bWqwum(88Buba0z%{4&a&{DF)2a2El6AO;!t>=r#6YQHPT;L^86JvAgugNQ!G54<Uyk1R'
    'F%uR=`aPd)hBFc3x25@O7v?{OKvI9$x22eyK<m6H*e$wg=o+WG_R_-MqNKKa(+}D+=W^I76y{<Lm7%=qy-HBien;iG`NHm?Jz&U#'
    'NnuGDNGR$u2>gyf=w{bABq$F<s8<jG_dA9|Ioi(w_j`H&82UhRTjLQkog}h3Kb~n^EmPt8ynwFL7o@8@WWcvZ26VG?b%wZ4=W$gI'
    'h^H83#YW2qx)SbdoA5Z<KzPG7h1}sZOKEq0sBTGX8gKl4rg*G4-kO##_{~k(V=N@J0=lnVB396*SQr`APJ{OC@+3w`0p#aKgohFC'
    'YJD4CHjZl0E)78R_-I@InSEk}>*8}Zgu;(3Uhecv7040$yriFE99fN{d?*21qPOiOV}wm3z)6(|>Lpmar#xxZbXBGeQ$(_t-T2T{'
    'ivYU1q8wfFz2{KoT*{}$8fVcN(rORl;ckv<F>T#9Wkf6EGSERvphuEeQ@lcwFKy=1aa%TO6JO%BWQ8xGZr7nDo!o54t8*n2$k<dv'
    '<sRE%d>hG~{WfT07%{Y8`2t;<m#@s?d=&#CdPKg6F2jkLw^j7zXcW6v9=BCXhTxmma4E@EZH6=DWwkD?B!x=CV<+m}kYhQRr@3tA'
    'Bu#L3opO+k8u;bE<grC5ykONBe_P4doQ7M8kzH~2spZiGJlon2xXM&rk)(ReL*g^sz_T<6KcmJ$8M~<lpmt55y_R{<!947SQr(^w'
    '#8I`V+B2;$>dG*5BiawM#!e0j5khxo=gB<)!8Df7uX}qwB(ySNf`rgT=?_qpnZlset?M5l;%VEWaqIbt-gscN3i97Oi)0EWkwB*='
    '_+?OpKw744VqDokaBLbbSHZ}2f`gslLQuWfM4CK4t^IK^i`{FHVCU8Alz~v`%}-;yW>-2kShDdn9yLcrs7TeglTGYo^rous3XhkO'
    '<#>HMHaDxP1st$$;Wm4by)hMegzbaE12+qmL_KuVpNl;L;MTwQnBJI%Aoz(OSAu|=Ui-qmh*I$q>xe0oAiJY3<DFW#oF$z9)Q91S'
    'O$aSAGh{m_`QxstiMsRBkJ$F%!KU*Pv}B*tXDU)`FZf=a3iRA4@k)Dj&x_<#Zmevp+GOVZD6M*_fzy|$1$*JRL0zO*{Y-IgW!YhF'
    ';p<z7i#8SIY+J4W{z$Ra3#MA#_SO6aBOyXr#n&MoC%*)rbD7TMpW{jl5z1QCF#)P2p5!`-cZv)v8=~?oJPHyf$*#z}B1m>*7H>Wx'
    'NKLHYnY-SE#bv1O%9EN>93y)Q=hLauL`auEQ71X%!6Ph<7o!r~Z+^LD?Y!{Cq-sKd+V)ygm8kiTGv*o$$_-mTk%Xx;QXogJe8ANy'
    'f=>n1Oe_^7EQ1EHzx{SSuj}rH_ez&ig>f;)@A{=aZXm$byVz<Y!h}-DS2^Mj7bFoZBGdOB^wbCeeqOb`Bp*|CMDrH*{4JrAt|%O?'
    '9IP`X7!(cbTPLTzP1TlSC3Pa|<hbIQu&|Xpi-={{FvxNaf7sxRvc`K7(xzvHlj_Jte)BgT4+pRqq;ZBE6T3a2z#rE^7H+Pu-=F|_'
    'Z58iP>l_M5&0*-MQdy5p2<jj7Blz5uh&0w9T-8M`M;t(13uS1PujOy_87t&ZC7I%)Jn%ht64UyPdY@o622v3Z^H`4W0^yJ=X9NZ6'
    'VvsJpNrK<$>w{lP2cZp-^C~ion&scU=6|%v^I<%F)|kEC<B$Tw{Al2$u3~lo9L2e?x)C=h2bMM`SWgKJrh9)5gnqDOJ1dT&ek6nh'
    'DP2VF3}CGmpBetYJlZ>=^(;i|=4v_r{bxtpcE%>wk_X&49E}wA?i7ZH+m)DhfNs5%aU3Uf7#}AowI7mjrYD~y4Ki6dxz9mO6YxW#'
    'n<8McL29&OGsIiPGPt}4b4)9-lm*&x?d3pvzf-&~_tD^;+M34z`DJd^+=ot#V@ImYa`M^h(0RqEll_Ok8DrG024X)UeGUTvw8mao'
    '1vUjDF~bWLR>xJ#Wzx+U#Lo@-G@!$1&`+iltUuoEih+N>Zdvsw5(fjIOtnqi?Ahu{1(5e5vWCJNB}@1{F}5uHRS?}{O!JJ9OpFBD'
    'I=mZ(pnl;|j8??1FK_X65nfPC({%q7foaw4nm+f_W29a9(K>D_6~5&u`dDb#p?B<WLQ;WiU;<9|2M>^`nt3gR+KkeC$f?z!+Y{o}'
    '$KR7+K|i5_4LSGM*va-U=GJzB_OH)o@{beQzmlM>T=*hdS%$CDW?veY5(Fj2+xO*P=4;DLD(Eh=4=)mTCB~xXimB{}qYuFJ_9Y@I'
    'YxB4EaK`0h@srS2o#cCGXUVNp<6m8YB4sodzAAp!3h3d)!<Z2jwVQYyUZeJBht}yvAYY!>cW*DAWChT)+IB%4xV$~7vE%4(PM1p}'
    'AHwCUT$4|YzUkDzy<e1f0vJnO7*TT2o!!-Vt(P#04{;S-IyG(0)2vj4UF#`lBGdJ_rtCtpRI=6C3;Z%hs`PWRR<bLYMlEz|80`fU'
    'u$s#9$!}|p`R(d;rab$NT0X(Y^gcueM^v;Q<`62=lv0|2>mcxg-KI$?CSBTZUyaOm>?*{zIAzMl2tJF;wuVom!%<Zs9+p0mFiVwZ'
    '9H+I9!9CqwhcogXFS`kgRoBXVZ0Cx0%JBwBL=WdK+6r}QorY&Cfm+?1`_^t9YABM@&Ec)28+_KLlP&fpc>LjRTEPd>`)jZ)eCS)-'
    'BjNCkW>tG68dt9)j%5j7wWA58O*<vm(DU_>ebjipOd7Bo;XfBNrl!1S=^z11Js79`)BaxjC}2hB`P&gjhJM;hpdoJju*P<5UH64R'
    '#t;(`>cdC;?W%LgCO42m@X_&YsK=_IS*coC{5y~)RP_++rB4b^F^<ra&nJf;LqgJCMD!nf<TqrfexW#;vE%NKe-<WV{s<A<`>;jz'
    'x?}!N7oT}Nt$cwIiUGmBoo1VGy9!oK@O2S>7U9bP%}og9^|*OxcS#6n@*!#>aCrll8+}9GI4d1FOaz8BcXL>u8@-5!=RCfK^;rD$'
    'Xk0y%LVf^f<!rbuj|+WOgwuL^{N=hED?`d9a>`R#wRq6A+7fte<<>e_3wYQx3diwt?ZhPoD!rv?qe@o`(;&RPQu(=>rM%3Avn~(S'
    'J24lk%3W=6RN(<0z4!|lCRp55Wvs4R%}2ps-@C<k<ajM9rx78S06|c5#xebK5d9fhN7bhc=7iB@vrk5BvOaR~Y}=HTP&u5NeHITM'
    '_ekn>uI6mGxq<k0MhZEMO8AkFf`1f$SAM#*?Q72ML6`-op<sU!?7NtBGN@HHf9%g9e65ZUO{3)ny7Lfbr%4a%O4Z>0r^mwVvuxp#'
    'hb5;Yd;YmcG>Mn~Gf@k<W{#yJGnb?S6-+((@|)+}Lh0}{Q2Us1N3SJV3V<i?RWumd{+Uy^-SQ|Q@$cLfP4WR*q_p_>oV@B1cNxJ>'
    'QU$TCUC4`zDu8;KJGBhDN-DA<f@pyZ!7?6>G``VUfy1GNKUKrf-b9CYk_=)LAA^{+E|a2+m47%?DQaD603D8<lc0Q-CFojryt59L'
    '-4Mh$Tso8r`16^M+TGZCagIEaS{#qdDCI_eopLutqW<qs^}}oiScJ;0+((xm6CYDesGryUyNml)`?GOv+cHurP7#!VO3slhILsuV'
    '$EwD{?J%;+LuuVm3dE}pdeX``Bnj>g=<VRTCbUPeW4|`4|5(g2ORc#nN3IwB{{El;bQr2GlPiYy1F=R6$ooS9lL|NzKuEqM<4QrS'
    't*JVdTkC+mP$6{6Fd&?u(6v-~4}TqqFxoR!b)PH0ga0S0eL<gsniO}qZ&xezt4wtp*W#}+p|e~>r1$uLdo+57I9Ml+yN$KkkFZ{$'
    'whBzEDBX3>oiunt1#=&3D+sA%l?QU4U3^4bYK>iq&lj_}5c2GwUm{|o&nak(U^z!15(SqM=E9ePeyWD7JZQC7i)6PsuM2h2wg9_Z'
    '_HQd>PB?-4lM*}L6De~)MoZRyss4TlbMOn*#E1^i|L`S$9hBHL?~ZQgVC^2WiyQ((|D#a{fyLi}J*+r7$tY-9Q$ZuswWf0%7dr@}'
    's0`l!3|zi6kwqn^@<T_Lf0cL4ph+D|JQ)jf`8%>jSn>WXP3UDv)~;wTO>{x~U@4s<gZ|hj^pjKYSUm`exP4wJRB1|;e!s|o==u5O'
    'tJ;9L1<=L4#D3tth(etUAR}}KJ4orqS&7aK6$!zR#eKYnn8;yiFPyp%n(LBv<?{}$X-?5aTs<?lsp~?(6R7$gZ;9x;LDo*GZkefC'
    '`7rRdO}CuM{TkS~5lO`<UJRuH0q?vKGPdA8bx=y;4!3<qd&0nTnQ$o}C&b?{vJ3C;>cI!f?atCNtUS4t{+c`#j&4t|kw&&>jmn@='
    'LQdJU>(g1jH9t{<_?cUZ?E}b6foBG)7)<7A1d}#sc~^35OzC@YeU4n6pWcb6T=jATNaX<#dr~O4KZ0h`@_tNyk6kBg-TzL2p>5wS'
    '1IS%b4imB9Ew3;pi%{m_9*Qq}j<fF;nwy5&26{sjUS(!Ep?QM3MR=L%cpd0h0LpECa?JC4p64kBgU&?;R>EY!g^K)>R}<3Uug>sE'
    '?T;K?Pn&cJVH#BlHc;GH&~hEYZ1R_<CRjik)*Usqa`)mIQqmajo8qW9zb7=lHNV+UM$TX%H4^hGyIc<{S^bbW={fIkCl|chgzEY-'
    'f^#1_)@(QQwmQmIK11H_0sTm=wE`)9H)2s(N(S2LEDf_#2l5-Jm!SQvI@go__(@BRXK-|_+!!%3T{Z;LCajE3kZ4k~AMCQN-_PXF'
    'kMdkYU_LC7;qS)jU}aSd!Ku}pVE0unpFP&UzF4j;KjmH8RhTK>`Mn?9mny74p-z^(`5bih#02(CMC-4pKINee4H7j%EM}sTr{h@R'
    '%N0{gx``J5gx1^YCp+=%%45!E-mC1_$aOo3tHiwvoUS8#Yx6SD`d^{*=DJgY>F_o-NCzC;5BnyWm>~V#!-+Ta-j{wl2QX%?QbDSY'
    'h1bO~0erP@d^>LT=QwBgt4~f$Fwhtp%iMJ)8UG@Fh)JG;UxHtP2U+j8vHZe%$ss(sy$TOVssVV7<3@;tg&I7Wu|vv2cJGEw2NW&Q'
    '4Z1^E-gj;-1OM+x`+pSeN(<^#6=+uQ{Hm8J|4I;Wso=5ZC!<Oht8dYA)CGaYdr<h=kWC?*)+(Uc@L4s?Oh&*wpM<+(0*XmBV;F_b'
    'mf(7!mw!(zV;51uh@gNt_&WT@d|#+Y*Eq-4I$iZ^iX~yi(0UgQbFQUzUN_--2Sn_<02HzrrN<t|q0(8cv>|+af@jnl-g_QT|IQF~'
    '1Zc%6Pp7lR_e1J>dsO?8I-JqSJ%P93|0e@`gkG|k?tc6u{*HSbAqLm#;ADEI+t<fGSv{+_W+)a!NrjdbN=B7&HeXF6?3$K{Gxw2y'
    'a%$Z2fu#OgWdwG9)|`>uphdhJd|%_AzAX2Q3L$)#xY)WvL`~DYud>&jQ(;Pfiw1vPtb@63-i~kR^%Bz|nKwyg4i$l9Z%gO#_>6Y@'
    '$#UmADn@GOAuoC*Fc(l;_7TqD``7J}AaKgq1-HKk7U61u;R4;FZT^L=IIxd>weX~0G0R$cFWWr?f<tzk0I9iq9!e%qjy6N{G3(;A'
    'YyRe^h)Mr|eOvGenadB-{C?-(B1W6Y!!=t<<JiZNq804^I8g%Ev{mh)Oefq(dV=+6EfElP?C-69IjtLbm^|iYl*iP=T2{$emqqMl'
    'nd+PWTO}y|d#ptd_+QbfS!Z<Wza=fN=`*@*HGIk)Ns5EvfKrFwpv>&)P*@=d1?>G_Ek9qi7E<3C_;DTep?8jX8EDcFw{y)ko$J9|'
    '-zoN8L;VPD9^j#H!o!Je$VT@z?ifz!ad-uViAN!%E#(x#J*KISOKDV>c*vM0v>rC_oMi8sGB(PY-%X|Ex_H7oWF@RrK#^OTF<xQC'
    'el#B62Y|~`V~&KB(Wm4QoXTwzbS0<dP-p$!q1$?z7Aq))nV>-X)AF4(N|t^}CVd3k35r`^vr<S!T7M#^XpdXymPQC8vqX7b?_N5K'
    '4mKHkgU=h2uvJ5vwqvEvA}S$Xk>1jSe<2o2YWsf!S<HH%d(KJ-`OwB@(+%YV?|!}eguKc-^{+Tv)a<<mSp-kXDq0<4<8URJ?g{YN'
    '(7{`^dToFWG2hs2LQd<RJ=XnUU|h4l?5~znamEVo#c(lbR20=B!zk6J$C@+gi{!@`Qg{A#a}(rXL2rTBUi0H;`m{J@39jsm`zi`{'
    '7tNFpG6LVyr!c7pkq0*ZeVTk@jR-?z+|}i|;J?^?6WDGJI$mo<aL5+Od@R+qf6MoR*<<zIFMc!^U=057zjw9xUK@NZ*OwkX-&m)1'
    '1FuQGLDJw&osWXN3mG5!__OqHC^r;$jrIMN%ieA6EJ3%U3jj!DJdm)OfGJ3>&ZK6MRhzHL1!Ca;tKmEG6R)D3FkVS#f-s%bXbsL;'
    'YZZlN6|A<sfRCR@XxHph;Z@)x|B1O*f!|?DE!_<gErik56`4%l#WQfhBs6MZ9N1D0fVWLQ)Y)cgJeso+Q*o$ZCnT=Fl$ya=j9B(n'
    'F=0%&UI)n1Ql(lk_?=4FJ=V=UuQSg+KmX$sJA1Ih7n5@~9c@|Xs<<W9x2fZwgiR8`=3eh?8JUA6lRcH&EfWQQ+T7<RU(^!Ideswl'
    'EYRojL^?1CQVNqr;K*?GAh^<cc;YbzzIE8Rzz&S1ZB^HX+H59g{7FB{s$ciR<(MoI#7Dq1lgE(lHEMt}Zg2&D^34ZTvSb2w;p11c'
    'JAnDmzhBsSSF)C!Ko_1Q&Rtil&`{HJID2TH6Qk(gpM<2}x8JqQJ+J`Ar=KAv@XIY*nuL=x#3_Ys;*u0jrYM}teK)%jE|b%T@1=1J'
    'wiaL9>PspbBB;pk2(1sWLRN+itv(=vanETFhJNR*)Ypv`!wyl8eKxgGVS}Gbh&$AV{7IftyES;fv%SOY-+4qfW>%?-Gq4tXeq52l'
    'S)RUUVSPv5UrHP(&j}t^!`knkox7FMMVUmW1!v@;+0rs`Q2U6-&5-25d`^6<#iD~wHtYBXx1i#wdC3H_Y9F?Jei0Q$>l5+7P#7yq'
    '_j!*B3}n@?TH{WG;*1kFttP&<!HaeCYd}CDaR_|Is?|KY*;6w*4mu^_nU9;=U)XQ2iH+~CiPU07yqPuabrDiX0?%12K`D;++2rv-'
    'yJLjSNesXh^EDpYp8tKHIwaYwGF)&E<U@l@PMJ&`WWF26L>x<%&Kci-7j1gCHR>V{e%lG(eW9e|WXwV{>3Q?g5)+JnJ@3#d9Wu=g'
    '={eY%cZ}VGzs}J@HfD!0XF~dHUp`PrnxxpjjJ^v;A%Qn>7AxjJ?OcS>eOvV)*gL6w3Gd-ef+|S!+d2Vtjicnj3^LhSV^>^5P!;HH'
    '{k{uU->jkuB<_STj*Cy-iF1DH9@yvDLE4^_lFg^e-&$n_IxK9rYdd13mzO1$v#Q5dorC5LoR?XYaVdd(6c76)%&S>uuzxi3Lm)|6'
    '<p5H04M2BW6uPZbDUI<YF#*}X?Hm@7u2@;1&i`DY^sX#%1N;H47SYawx*0dEs1Gg&;wH?T<DxNL!E%lU>Z0V*K-)&@A&hhqAf?IY'
    'Z6c5)%_DKAGkMmi!5Z}3Ukp_kK$7yD6G;g*=oGWND@$2}r>TvVjnH)0TlB53Eg+F7a|n^FcXY6sfte$fcg>pg36xttxnTtfS--pS'
    '>>*)IT7*QEDw&pj2pkmhsL+uT;Te<78KuL!1Ixj)5@QkkyO@(Z`(gY!x+yBU7j-in(h%3sjK1y}X}tXH9p@I*KOD3<QQwe=3`1FD'
    'hNv#AL|=rV(XhuRu7P>hS>^|7IYG4Wi|;vCEHkg=^4Q8C<H|f9chMtQc)k-rV{(g-KtrDLI;Cjw7Ra7-*d&kS5fp6gb0TRkRfL%f'
    '@x0YLoN|ixVran`;!C&bfK2Cux+MFDh=>+R1ReksRggZ*(v^2BSd`;N7{Y}8i}#+!S6EFDSAXMcP)&)e<lW&cVY#K6TB3fi4qkUD'
    'Z)I3l;^L1k2$NGcM)z=0tiF_1`d?Su)4ZHR0}i)^7>M4QJ4eF^ykEjCOG84@ggVG(Vl1JLsd8KR<X;1`s=#LcK%h|HKl<5xt^l;7'
    'cUD<9bp5muL-e{vSi-v9{4^rDa<O;!%$vObL>_Yv+AZKzuGH8AKbL^#!}8$EC5pPCe-i)`TN*HJ!$WNghTmh2@;&zO2m9?07;yPj'
    'o<~eINI)CS*f0L4@mM?*cVJo{y_l*H`n1#evV^S}2<!xaPY)ojbNA0U2zuP8x8jT#A&2?Xjl@&fk&ZR{brMfz&1L-$jYzxmoSbeh'
    '3btOi64i8mEv<$X;eJd=-1}+hLCT13Xaory+RcyxMMb!>Z($EU`p(7()jJxGGN|^h;&^$vwm4x^%?J<;lLQ&=fo32l>h*3-<xH|?'
    '!|_SG6O0hGR(3eHZg~tIf%R8jzZi1b_jAFzebp(fo0out!n*>zx*T45cy1ZAW9l42;A!*J4~~i&?vuOW4zk8UlHXP;qv;9WI}c|1'
    'DMB#cLmw8;*_OYjbYZfqp6yq}SMmUk;d-?xf!lBwQRuUw5^f2;k~rGe(yP{>-etKF;j`)X)1vC^P^LZ@OnMQ_U_ILE5*t~>LiYJC'
    'VL!zU_)HkE5vBLqLU{6cIENJDT{u+$X4!4bY)ORgfvVlAp*2|nwYzsmorRPe8Rq;pVG^N_Pa@4n;=sJ=e13s{=)&kSFf2|Wt}FaF'
    'p-fuc(5xXem&mGGnVxn9gz)08Kj02ewNy&?MaPbT`D#C~Ih~<gd_Mg?Zl^zN>MF99-(M_TB-Oly6D8p#N}5XHID;|{N`}B5tJ&Dr'
    '`MG{fGM(mpz|vC<2x3sjhQv;!N^OXL^Twsme=HR!2TzqwWT9^fquki3anI0*+Hld7uyJCtS;X6`ukHY)0ADrUvZX%W?~;-ag9E%Q'
    '|3SFSm)9-pDe?vWH>05g2;$}Dj#CzD#iX8dleD&BGc%Du4WWi4%XxikXaWN~$o<Nicn|#gL{GR{qj2j4YRD*hyXbCPC^=C;?}AcU'
    '!KzoxRbdx=!%Z=7Zh)^Z8L;bAS9W4rro}3eUIhSAdwHB!G2m)0JgA~i#!Sg4NA;nBcv}Dl$#dEQ1%#*S9gLoymJn_H@mzy?)B@Sb'
    'P(o%!m*d}?Hd&v!su9TN0PlqEvSBrVtT%X^@?)+GZ=@=)UbGuW-k@|A6v;bP{+fq&;=9}lp6qF9Ip~#rE!VVp-K9L&ZJjrwPpGQP'
    ')*1~TJ{U`qEttS$su|C8f1AvdzY1CF0U-?3cH2?w?QavAnd%S4YO)FmquP>D^X2<fD#()$xoN^OS~-ETKj8l-6zYETr&DE@0M`OB'
    '0@f^}%IGN(5fAfDmEJo&mc}GXMm%o+h+s9cv6I?XmEW<50F<CyJ8r}42i52)@>HNr1R!D;Xj(j*I&6%`m_Sx2KTg(c+tqO)pc=JN'
    '(o--b{W&Ka93A7FFC>zo?Ah2l)8xN<WF-&o4oc*fU`nRmMAXFw&Zjc%rc7RY&hFu=#a|79BZ#&C;x8n$S(>$sG6Y+TsRd|yI$n*G'
    'yMbVVa)&B6XRkonlPcyOC|S0{3pf*x1wi_y1P*+;$ayL5=G4+JQRrwf84NyzQS&aT<J-5Ds=i`VyOk)!R8h#<Y4p*VRN>&o{_rZT'
    'FsRuFEUg4_h*!DtW&4(~2Ai?+f`Bh7uQz;Gb~bJ<5bUSSOqR4zIGp*B7vk;c!o(myL8Sb+;Y(ZYlB6TvV867<=Pg1l`@1l0LEwZu'
    'q&D`EyeDjPMHs{0R+7e|&qa3}xt^uyP*df$+`Z<vI`08S5@$7c1k5f>cc=rUJ;(Z2;S2C@_ZL7BsLK8#@KLC8V=aC}3yNeQD3A$X'
    '0h#k~4txqSMi>pSYUZETptY+m4x}qi&tk2NXi#zC*MG4zJue=(8~*{mI{1>$BzPKHIDnqUd<X)HbnomSWYDmHv^(Zn+Jp(3M$>g8'
    '?`|7VE<L6T5jLYimm7UIT)k|{F2lPn@3Q=?s(Hxnj|XyNI^~sEw_$00_`9y8GJHdUJN8&6*19z;7a!zKpXqVU^|KJ1ULNx%#+ec}'
    'B%vFDE{WipBLn@=GDYbs6NbNt6X)DlAT>fY$Vb^Be4kfHn<8L86USpL@`P4wHduDEcVQvL3#RE<A0gKgz<SB~cl*7;Q|QE;NsHSC'
    '93JXAiSzkiUg5d6y+`MB{{@hR0Tm{3wxqImf<@&UMV*LMJLR|dDLfzFWWf}diGqvqL|y_jKG>fWXqj2wDvanL-DI$~GH4?^C$9iY'
    '!|<x9yPaUan*e!-WncfBD=-0=ldt<hv64KgmwCJMyAWGts`9L>#n6QFRlqZV$zVoTU`%P)ZtH@PPYQDW|EBM>ZN5P-IMzc$f7k^s'
    'K8tLkLMf?dna2faY-^6`#z39(QDiZ3j<?1BS{a_gKXk*Hf|zOl`vSZa8<0e9B-LV40VvROYwx{b-YT7YkU+i|6w$Ve`yBKQWQ|O3'
    'WpuikRLQss8+(oOQH1h6le)S5qNH=Zb~hep%lWhYksG1eXoRiu7BFK_Bn%y!ppAYQzs5wU*4{eR-{g`eG4d9Un@#ipIsIqv1|%&#'
    'A)z)C-kQtQ(o7aJGoNpOLP_MEg27hLsg;%a#fj8nLzaPUt}b1kH3f{7x=3GDeGSrnwhop;UvrJ_BmCCW!4f94SmJ8OiBY>X_w?R$'
    'IQ3-0w{I;)i`0q_TWM<av&mdM1=fjb0-=*?;j>gwaEln!Q))AA?LUSfyoI}O3+F2^?no9q{5!6LH<J>GG2G2~x*$mPyYv{WzSFzL'
    'i|zNBO9k64D7YMe_n6ws310#2mnG4|9{jCeCY#raoKyXPI`l@q!Pt3V4x+Z0{8L{rnflXqe$V;gxLE00l-*S66tGYNysFnx1vP@H'
    'q<U)sX`+y>oQv-vW>k%TV1YmWi4o?Bq5k9Lx>FEpEaKWv5VL5ro#KXu3MP4G2Fe9h-EM_1nvJ9=-V4kln}Ifm3!C}d`8BrjC#rmS'
    'nP=cEN>MlYE8=GqiGpZn4Eg2FzAUNbzhWVWax+L7e_#Ea4y-4ecQW@4gQOj3n$V?oL8G510bAU2R%M!QTx}{mD-!@zC4)ypp&k)G'
    'P=JkGZFF4?Q^rwc1D_mNR1MtalTadOti-?o%*%h>ZuJX8&?y6W+f==u4i0B4KXa`M;?#?p7RmK|A8Sd^OO4Ab)k~g<*A)|QwG$`Z'
    'gMGh*AVWZFM`8Ol+Hyya=ROnA9_h(U>B2Kb1qM#6$<^jXH3wk-FIlnUMmogVbo|q6Xb(N{q+h_V6Z$-6fCpD$oc4?3EnFo&V4p7t'
    '@`yXV|BS+bgqc@pOBekHcJfP-*DWffn?}rpC%uFYJxH{hPi(hHn1jd;-Wz1~Xw*ktc=Z{xnfBfEO|h}=4y6||IBmmvZt6!(jo;W^'
    'OSOOo7|vaO%PI~u_|?n0hI42^3hJS5dmOE>i%|z7D#kc!FQ9|{pgXtFBrF4Z4XL~*x)HBeX5K2E@6S-Y+%K&8RzMhUJxtG+Ff@Ot'
    '>G%`t8&H-2kPxH8q@y{w+^nzu=DlnIOsX?-qgg4ffIzN-R!VJ@<(G=ohdJs;u_nzi-7U!P5lqcRUoaN0HUGNv)3NNv{EobQi@Lnd'
    '0o|fos-b+;v<4Boh8ZS?uC1Zwq|Qz>E{tz%^V3HvLqMS%!j<`v_Oy(_gvMNAL3i-Z=`03vTaGaNo=`^(I=87EqU=lY#H*+YYGiQ*'
    'o9T=$I8wo9uIg`AwZ%r>u7Cs$blF2s=vJpJ*48Qns;{X3xZ1eXZ;!X(xNLzlP*WiQ8Zde^!VyPQyjnOnc!Vt}a^e=`W|r$?UiC$a'
    '$HeC2SB{CV*C^c$Pk(SsSQv6j_&Kh7BHs${Nc;k;W56{+UjCZ|dS!HiFZE)GgzFCt+xo3<O<b<|{awkpgsio<XB?T9H(Of%iU7vM'
    'lmO2QZd`#FTKw<1dY0uJtQ-Y+L>Qf3Bx^yo>fL6MV*p#jv`MuU?#6mS$vxjT7vzT95S$bkG)Ai|#2QxV;`<`re%Y;Ah;mD)u1FK3'
    'A&m^tdCF=*1r@s&JQ5GixEDRTbX<3~Mh`?Vaj4XcSb&%gAdD3G>gE)&2zAq(UW<IcGZ}Py1NlHp#p#g?M5E~TNhouV=|n|Nae?Fh'
    'GeRz3Vd>re)MJtqL84{+22=czq8mW8NaMsQ8JF@d#5+Ipg8uR9J|ixYlAlS$a98r0=B#sJXz9M!JIj`w;d?R_;t$tB!un6I_bITr'
    '%~LIdG<A{r_8?Czy+|~zT|nFWnJNYQiwEcCtXd4Pt}G3k@@6BG&P8_%(`6xN^SQNKbD@lWT$+0JaJczS+AyU!D1zIa<7C;MA%VW9'
    '=6oZVw&`{8Z#?lUZ>S^9%G_dy8QA%bzQVMTHNq<&@w%mE8O_M)(;!_S$X;A^qDiSn;>OuKnF`X=2nHBoT=Z>1L}%P5KW!;aS5-m3'
    '>Q>@bh0P6SHIieq<R*p{e4`<b!{73mBdoZE55295!0XBo5o53ycFf#b>GtjnG%yyDBxQimjw?;4*wubsX6TB`)|-pm@uSipvlt=#'
    '(r@@j1%{Ul^O1gbS;5LS;Xh*`g3;-&kv5q3EOdkY{DAha?<S*=Ad%S>8fqs7?+KK9`Jr@;wJVXrpjrG5Gfv<dc%!ZN0lzQ}>rq=<'
    '?Ej98AdX>?<-j@QCOqlGO@KDk#-LsBc+T^K!4^`1hR=p~3l)e}Ea2H(_1mGsaPH=HVUQ|+dXS&bsS9iB3JNzlU~4uT7jU|YP0Ru9'
    'd7}dbi<BeO-j(5&1$7cFltPK{D=qyUA>h~~pazKA`Xss3)Jc$p6H>^Q!++)UVrLb(xpdH;VD#?+U;IFmpbKq!@s=G9?$nG!M_eXs'
    'X)O9_Wg{+&gCi7qwBFCjiTsZFIQ*o5Tr*C0XilUi!DG7tu0nHVccx+0B+w*L?*WUXnqmJmquQD|<V*dQ5bA)vs~@I_gQZ*4ZPiyN'
    'Dnu%2bAsb4kR62sI<xT6JF?u;kDY#&<tSxKEpPiFp0N%|GZzUY(~i_>n*|B{=zby&ZQ=m}|G2}!uY~L|%4M8{OtYk6s^~+?;mLem'
    '<k=E)Goh;foS|{OSLWP!HJn755~bE$>i>wh+(u@J4VEH8lMD%~R$cKtJK-!nkB+n~HQzpN!(qK0Dzpgk66Z87z5wJ{9gBDl&lQ0H'
    'BGFO|1EV8Qu>)(LO(c|(WN({1*oUcM`{Jxn*cZNh-gV^xgr9Pc&n`GX&y34>ee(p;#OMOrnE;-|VzMX|c|#%ODSA4Nt>vc`i<ELr'
    'C~T5djN|x{m619xeY#U*<9%m<P|K*#c9*jz9itpG-*^@)u>q__4&`hYvP`8^ITl_OyqU+w+GrRnVzSmx@}prltjf^8bspp4M75cj'
    '%ND`8Mec^Jn0zO;G~RXzLtz(uX_A{7Y5dd0$FgdU@|Gj?h0xw2s|@dB-mgFcPC$46J+X*WeRo)$Sb+Ge6!gd)`a#r&4v?=fVD{;H'
    '>N#pxj&V^=IL^NWna!F1*Er0!P|SB7&i`n-BnmH&ZocLRQfVk%_0B6CFKuEsErx~<Ti7gJw-+L%*OUIG(LuDu5(eZ9t~Chvqq{N('
    '#c(ipShX6jgXY|cm%szG4zP9=Tz5!dfK)pP<am)4j$LO;p_<8)fl3J^@SZZ??x?4nZr#V$xVnNgnePS^II1GuzePM6GEu+=o1viT'
    'MTl!j>aHs!j__L@2)EXdTTq&WuNGbx3gi`qw^<d)^ReMnd{of3=1j<s*wvhH-?0YfUhQj8<pF8EJ*7s98K=F}t<ZURUx^O=+Z7>4'
    '9U%R-y`kGei923%Ngzi=%P0;d%`z;N!B2=_Dt4F7E7EqQcd`Eh69B{t7B^Xuv7U^kBh=wMojNYH>D1Ao+fC8Yf1YF62~Rw+c?J>g'
    '_lIi{cke5tD$kz69MA6pH|%29raq+@w%^{XoKnvHp&#Il9pQ2aPbE@V6_%b&hZ0bhH&|(Aj*LY-4wRQ(;@VzrOH+^Uey<is@OGGc'
    'e~oi*sfv|Hg2F0<Gx^-&VtX-_o7@EG2WulHN=@IQ<-(-eSS?<Cq~d}_JVkManYX&9xsTq<*JFgt2JdAm{G>G$HP<{;ev;do%LpEo'
    'ASFy*cGFDsay~~!!duit16qaf%0^zlKdYk}@Q&ytnu4cg*D*frzc!c|LYGzVRKxyTf?2w?N^k`q#_?oofN-O8FU0_doLw(&R%%;w'
    '{{{_7-CPD-c>{*cdc#u}cF=L20r&II+M>rTq=}i@9_=qg5wZH_;KuuJbxe;Io=%8U`W!G*#^swu;?}~?O)^qXk77DlZ&`MRm^%2F'
    'FI~bf8?#6?ZLY&PapHN2t=J2G&94fKCz(TWg@+ly-NfzIj)GdS4u?R9lcg-@uNB9s(5;8JtRWPhdP5cejoaxKi$kA?Pgm&%?$A#*'
    'e<jKxoNBX++}=QKgb>H+zLfoWQfMl1h#bo@?2DLS;oCy%x-5{Q+u%uUNy1m{*(A?yk2c7VQZgP!qcmo%b`*?4)8=U2u!#}jxUE&H'
    'Hv(Kw6$@+YiL`2$qMq@>ZY1&;HB|9D(SJFTt~5Q3>a3F?DN9s0Ll5kbJ%_~2?g5c_sJLSaHY0_*bVz_<qfY;dv-q0qo&)>9dUTC&'
    '9QZcic>?)9fi+<q`_!+IfF>Zpo{M!vQ7;d!bo29u;dLR9`W*5BTXMn@#;XP^!5G?e6X?*r5bP@>RZga;AB=_8R5yo6SF!<_@gN>q'
    'b^R+<Qk}YWH*Zx>sz{F)+mTUg=E`)Bb-^lWSfA+V<Wu-0G3(}J7xe2&m{9x(1o*3E(12dT6BE4g-IqgY+?zrRY*_|jRz2X3Y&qJ$'
    'Q5@bs51fAat6@M=wgcJE-8)TpWnkdQ<=V;cf`WiuwS(P@h#vv+-RU4&%?M)PU`H^cjM*2Fhd#!mmBRIdWidL|hfb;nga!7>`#sjW'
    '(E;YQ7A@B8F@tEz^>1s0sD!$>><W#q?4kGwo!otSx5%C~ubhxNLRmf2hKRM5)YK4@@5&G4oUoAc=$Y)J6b6|c<ltqsnudsn=(v6K'
    'bgo)SSIU$E1mvU1)@EwchQCeS-`A5dViHxq^LhJeCa)xW!BZ4`o<DE6q6(oh+F1JJt<Qb;-TZ-2rSVBiLy77!0-Y%AX|=a4J6bnb'
    '{vvCkrmp=JbVL{7cM78}q}=t!Gpkv|zt2!gsgL5@7xv!uQyNM5Ysm#-6xd$4xdFOA@2~*Ec`N0F5fx5=Lc~kqed+1#r-!Y|!mo*>'
    'l(_MLEH^^lKRk(@vaxJsv>SA!F3XfnW^bVx9AZgFl`BYN*S_|*DPDO()zmBmwuX7m!=PF2Xg&&U*o4R=M9q?t4XwEl<ONup+|9$J'
    'qK=I7p!9p8UY*E>ru9fo>w`FG8ewXWboNE!kq1_KvT-7iu8+sQuuH{_=ghKMk@KdwS;WNu`MIjbn+{1ArJ9sR6qgYqZ%GOyO2T8?'
    '{tn17AV0mVBbzdQxTZN>Lq0}dQ&$)Y%Lf;tL{mYTwHd8wvTLkq?xInQkZVM)dLSi@_DX8M37<xZP#}TBdkza`LD0Wv#JLeqWDk&3'
    'kqV|8nbOEP7r9FPfyKK9vtm9w9;SFqXOJxKBLEvoe{Wa_yR{<wF*7agy&0hz(Q>G&hx=N!uIfgnbF>eBJ(^cemR?z>89!xAr*OOQ'
    '6x);(;8bS{gcKv_oE@M=WU#gfFy3eO*5E{P=(G&c?}7%oubQg<>2q4l2P!glO<(y#CbV<aEAi5-5I}(J!gANXq(7<N6H@Cc<X6os'
    'uJWgmCdz%cczpT}xK!rcRI04*M{x#oS76Uq@xKr(wJUsJ5IB&O+I_|zjkAQ1EPU@jPA}y*xLdsqvl0O8TD<`ixfOg~gpqc+vOl8B'
    'B~1SOX2C-6lizJjBYKIb+l(DT(AGVHpb9Gh3l=<<dI3y-%&(n`pj`rpt|N)5){oMXP>7k4dB#bZH%ADWh4EsI!*$aJ>W{QJ?|)JA'
    '(8;u<<s(UMOKH0yBu~E799ilYAf=h8|NeYB4he6ILB&A+_?3GM`?EELZ=8JaL^CdMupA!}3Va{B_XhC0Ji$}#!hy-;PzZgtj48^I'
    '3_cYUW>NbDTzHYp$CckJ2>?$J1cH^m$qC!eYPp>#@b1KcruHx81i*)Z)S&}YIsn`&0iF9Zb3m-QVbiYcfj_gG#`_x+>ohuLJ#x5P'
    '*USx@e`>r^6w_ikJeri>J$BK7J(Pn^z^yYc$s<ipfE))8s`D4)7;(v^B2~?Lq@d4~xn4#mXK2l!d(=BgfFZs@C(CUp35uue(4uz7'
    'eLB_5LWslu$KSf-7G}w(w}Un(9`l*F@~6gHIn2TZFrA}E2VU3=Y|wtb=tJx9WwrBd-)=G<*^OfutVuJ&9O^T3RuFOvDAsfYyV{YF'
    'FL&}efd3ZE`e(Ad%02h_{gDV?jqcCgt9LsJxJtv#dqq7{{L2Nx4=tH&`EXT$K-Kx(=l*G0!+gV}N2SrypUs{h;_6zda)X&O6ev&M'
    'zd;gGeqd^~=P5U?i^dsb8vyzr0e9xmI=H0aJRlY!|4V;Ay|T3XG-I#~A~J(OXh2nQ(ZN<*1HHsMJF-YzZ2LU4fF;8pC$%K76MWJ!'
    '>fJTSq;LW(l-_)+FZGAG{nYEY$UC<K)ppan&VX!^D>r<2KHgWXT5~e=k>rP&BHjF}(OO4H`ngVmju{!)<(6-d>}#{33p^>?k56K1'
    'J}GPck>pWnUtugBIKTEUz`dwq+I?r&i?srmjiTPz6Iz`VN~u`hO~opR-`<MBxF%|-a=E?+o#l+-F|Yoq;1cXZXc^t6z*Q1W%L6f-'
    'ZGv)9F{0KXO;1pNV5iew$FFfsuLx%8-23HR`QQsYVt^%qO67xX_cbolsv3(IJI~d$z9BV*p`QcNsN_RgjsW7m#ou-RB%us`V{x8{'
    '>k?XP%UkBo>})AXekm^$*B*R*LBKj-utX&|iL~6O8{86u-)2Dsj3OGl3Z<?<fl@a81Y#&#^HO!5{b~BD%gkjR28i#{^JkG{nZ0u%'
    'kyn3Q!UnKs<x9f8<-8xAA*3Txhe;`q@+E;42u_mBfRi$6%y^5jN|nZFt`-n5IEJ8Q5Wsf&Rp-sn>0ii4apy&_meReak>B4a0)b!s'
    'eXWwVBQSDU`vqDDXKmm~7K3xrZjiaR_zXZ#HoZn@qaa=a7R5(Kug6UmOP0haXoqzmPg8+w8_bLQV$j-NC&mhXx$<=i#k&)eRb`Db'
    'j72?zr_XMBlF<DqpLr9bV?k6IIz-72-tauC$rF(I=KvywH#|WU1Jc8+w1Wc&SE64BwVJZ+XH7H@%Y5qk;Y=l9X61yC<U*z8_c);M'
    '@ET<oCRL~kLZ-MT%PWKJGVYzrlF-$+Qa4NMt?u<{y)e04swT*3Q2G2|wTPZxdA4&Vf__}qE=Fe5DWXPN;m&SXh@dSk%K^h6BN!LM'
    'WuwO4&@38Er#a!T=O3rTkKK1P-T#2p4NH^HCi|=r-$a@6w?K94AT2?zlSA2UF0T5;GEi1r4j{WvSJ+ALZ$}Wr6-w|@%{8`DCtg1z'
    '<a|jSuO=#F18dpJkZgY-=!w*#xlBMtxZIEPoRxY>+|!4E(w)-?t$s5M(t&Hm;xGb$<1bzMDSSyI{gq)K!NKB|%<-y%C)-CIR~Dci'
    '1VyQxXo0T_&p0m*ZrcvB!@UL`=U{we2xwr1oQ|U%PRfu`;G4}jAu78_K_N--M%*I189>Dtd-!-ay_bfI>(Z~e4}9fUhASFPg6I-A'
    'zimx&IPg5~7qX1UA@n_&j*g<}>ln4y%+<?cF$!?eA4;zKZ#$?NwKRV$efgnDZgqgVPkp}dq)w6!Opv_@)@sCnGPnV=EPPYFBmdP-'
    'Hxv?s%3@U$AVo1&AQLqtXgf6+tt>YFZA(_>+taXe7SPZVabf^QzLY<HXLPF_`V%1eHKju~1E+6}hujmI3q)80@7~vhvIKLf52oOV'
    'i1Z;6%oYw~ZKuaokeaHkXLk5uUwhIYA!;4r#1PBZO+TisCjglmmZ)!VZ`eb(otN1>*l=-5IqC5H2f;W#y@|k?S9kB1T#wd1-Qb(%'
    '-Y;VcY0r8_0vw<uNtmuIZ&Y*r=^;%~q&@DZbhD|0x(D5Sl#{&RB$1P_fDv}z3HgR^L>)Pi-E&(2!@&&4fDw{EE_u?W#uSe_a<ZJw'
    'g)9V_3dS&(cEG}ZfXMrjEd(w(08Lz~;dZe+5qLW!pJ&=9DCAie@v}>?1j4g&Y2|gkb{Z0UY}6QZ0h}7STsrJ0S|6`%N5sDQOsh;_'
    '7{;zBtD*#}IeJpEjKn_zi~de^#Hy6)=0#)YAvA^aI;9}$>k-kEu(it$J%;UFm;sF4(CI50E+?HL@ci{0sVyb(9V{&^zcPBYrp;Z$'
    'eGEnCAxJ?hKiuPz>mt6SDYs$D8tdoxpc~B-<YEvP$8-B%ri6f=%2JZl+~WIGm70*w3M!asA=_U!?7;}Q9?HGjwz%+`_ty@KkNmSj'
    'iLTkpC6l=}2R8T_g+XQ>SL|trAZG27Cg>k0JXef}&p5<vzFJ+?!nA$C4ZX~*!kziWX$)y>1ed@f4qrkY8AM|^P;l-}BS0U9#QtA*'
    'D=p6K916=KYgEfYFCg`m4U8j4$h+y7%$qE8_}8wA$z!R9kL#5<f71*+s76|@%++7J2Wu-lyf*C!oE5z8uk_IG3Cw@gt<4xDzGZka'
    '!S#<;@loBU!Vq0WnItE@h@;*MD>s7x9TJp~ks3WYMsI(LT2P@o!eO%ME0O4GQu*EjLf8Vr{<g*C+~Yxs&#k(vt%#AeC#Qj`d;}Va'
    'f*{dtzM{*kQadTv$#!n7UVT2oT=iKYejwhM{@<o`dlJYR_J7Vrf_y3S<JKwKwsLHR<--xy%C$AAIMG|qj8J2Z-|_X(UDVrjz=gou'
    'gz?~R9xg_TV=CwH9q<?ngJrOU3R*<0eoOp56T8`mmt?=^<SrGBUHGLNsvL{a`49kWK-8|R$T26w6CcwG){^zEACr(itr$`%st5<K'
    '+<`|1%Fp?5<GL#F2?l6nsIlx!DsHmpr1?yZ;~!=?8e7@8CsuF2Ff(5@TzC!arAE!u&kS$KvcQg%(8*ZczXE*;-<2&vw0o3E^4VKK'
    'S_1cJ{gPSN77&}1Dyvg8?&9>Cav+RPMKOsHNUq1^QN+;J5Rc^LCR<;qeXO#=_qXm32}s%?E8l`U*7A?ktOHPkI<2<$1(yK5r*`Y_'
    'V?4yjn;HS4t+xeX+Jg&{<+sEGYwGa06iCa&cSw2p&(oRUD_tPkVI1{?c>mc11Va)1jYmh;8gszjln3S%j(UNPPm7H0%Y9x!+it>M'
    '&tPMkn|H;alFbnnn-?*au3f$yeeFgu%X9o*8;OO3<nK6FprPkFW?1256yn`^Y@b5!`;0H&3~chDaog~EmCz1B7eL6m<!7*>GT#+3'
    'fK~z5C4t-r{sZHcoeHZq`7)(%h5>osK<ihUiM!H4W0b=w0gwtM_S_maPn61gMJ*yveBWYHf!^aM=CgWO8ZS*yY@PSZk`<5gma*Yg'
    '@)fW7N~^hSNeX7gyMi>*Q-B+*i8(x6wC#hAglx^-u!{LxJ8we;A0*7@>wP-*?y!nZdZdW(i9g$Wgm(xJ93KmT8tWK&dGFqH*`LQ='
    'dvo1FDn79x@o0=07S1R#vmti9pRNFcZ=?}~^$z8ro8IYsQ08Q0d-JH$&Z&a(xXv3-0F`;fss6g3p}E0Zkg@RwJ*5ms-U!na>)6Xj'
    'n%ZK`ry@UrKGm{APr;Q(cNS%KRFH$Fh+m4TD*TSLsMwh~Ie$QO5u?a)Eec9U$e~nOO6Tmezexu5WV?D^LEFCRwtJE_z_HS*SCo$+'
    'B@98`jUqSE;&17jtGz+m(msSX@;wW8koLaZ>1J@3=Lq8MVCkNFwcUkEzu(+(LlT^aG<Vk4CsM3njD`;^n$B7c0hT=g0+~u~9F1q-'
    'zuO@m$0G#7d$fy7%SN=8dYo0MFgh!L_q$sh6epPB(v+e}Eq31ThemMfBCDnLtrr}ax5l3IXri`Y_C0h1tkESUDHyj6ZRG+ci1Lle'
    '((Qm+D;`|EGDwW=2h9i6vBQt)OaK=Szw7nIL_brNh9{>yi?K`UFlEa?9xl!sy%;GUPPd~Emj_eBDpOE0P#2MiFILOgwbt1t2A^}W'
    '4~W8nCq*Pns>PRR;7Dy5i1)cesSc#Dtv3NQnM=m~EqDQ*7#^+z^;0zs1@%cnNqOi-T*yqG&6K>ePjnbkA9zvxftw=FG7Rk0{S5SH'
    '4^)rnLTss0Mr?Q<HYd%}194SiO>uy*N!jrX);v_bQ>IBxIus}(tl`uX!#ofON>wUrs#hkz#Y^F!Ei%;OCs<n+t?!LBM~g+rHig~a'
    'wY`FeFB1F>XCe6pC!!`ev!$N*A_|*^Zl*>_TQhQs$O(*o$0olNXmbPwW{}TcQs@YoArB|9l6XH%qN{kuV6}P=c>4f3<B4f{6E0k3'
    'MvKW7LJO|uU6!+&OU~eTYi;OUr1fIR*g&)<U-c6BAfq9AKR86ON~m7a2>^*0x}P~{CHD|BPJ)YLeocMbuo^y*alnQs#9vV84?NNg'
    'j3z<P+H-InEB=Qrl~&bSHCkmb7Oavar7YY}zK7+TD^XU@#s{aR4xx^_Sz-fgATv_5&0KkB)ARj2uz^&wKf7wyN_6D89aFyyH?E@R'
    'q}m0hfZH-)5+oN4Xk7t1Y)p_V$eHKgB2L#Wxs@Kif-w{pY3mm8Flz+k1VJStd{hY*pvk=wcnu+Cn$UxjE=6<lG1PoAZwI>zGtSwc'
    'X&mKn(}wMh+`uQRT^)N*vmWt{qZ2-cVyyVJxJLTPdJiaUvR^?3H7!x*DpRv7dJA5+KM`4JbkFn9eDU{zxgM|vF}rM!=&tYYw6LKP'
    'k&y6t>k*c8jZe}C$6abGu-qVeMaCnRhjKO*5x`JP1K*te4}`F9?IRRJSU<3`(o5Q-X#XX318VIpM$P9e1{Lm5?m0vL*i=PKx>n)a'
    'F#NjQl!^{ylBJM+jpua>DveT$@(ZS;G6gobLE&xse#p$yiwtvlj=UtGfWqQ8Zvz`-G4MD>?;MMKgIxv^J;NHC&IsvXS*5#91;ZN|'
    'KqMGY3q|`=6FX&5Z0>D&J4+1m5_>zjb1x9@9yq&d-UY@$<-0sian3QXrw#gb3387%e#7|Sj;ilXF9}&y*f_E^UlPy5dv#oVxvWtk'
    '-sFcwZkYETSx=tvon4J%T`I=iC1s$6Nx?^euSE<vV~9;ioy&{Scbn;-(^&C_Vc@9dUXH=l>!a#c$j=5nJoJ@7j(wG-JT~<;YHpXe'
    'R^6_o++@$-YeaX}?+}c`=?rgKsGgRHV+Laz&mFv;Y^i+oh_?x>paWY{<``I)v;nCQ;LsM=FWpOXc=}kb_l{G?vVz)STt-=iTZG#D'
    'S``3oIvWY3B6~Q4dnvfj;^rxxwvF44&{zTJ{>uP}4YZG8y@QF0y7$+RCSCu7Cto5Dyty&CDum9U-oI$^By2TN=vUf@lBnWT#3DWT'
    '*q*v|WH=PyoX!z@nkYtM-J?>s&wiSmf=rU}3r>yKI2liG^5T||sEq_{F*eK<$%*l0BY0DRi2#pcexs3j$=G`lsxydh?Q(dQRNy)H'
    'T*vC1Wbd?Q8r)r_KlLcCYKkT4L%Bx-#o~PDx|bW7E$jt!rhdF9*XrT&K2Z%l#zv)h)7O;J;xSu|W7LOf{So#*Y7}C(<_yR~Eo=A{'
    ';2tJy&eS#T=X_%Eqw}_cnQl>M)o*=54b3)BRiccwDs?=so-2M_EfK+tNJ0?MqRP2*JX^fz8&hE4na=QYFvh(g!0SbxQ9e1K9pMuY'
    '6QlQX90sfb9$zQaQI#PO0M#yXI=>^iEUAto?!a-qCNec9Ac%jzT4+vIv+~Z(NhM5Ho%I7gR{F9OI$jW%dAUkSJi2fpTqiCSnHuUQ'
    'odQ-FszLZ(bqZa3fy{OH@dEEjzm-eJ-FOefp{_(5UOTtM)smM%=7R}L;3KuJ2x)_^j7y&ToW*Uc1_=#De8>!_q-mAe0hYj__=Ms9'
    'XG(1i+<hN{vyXx`*((J5lorv3V#=PqPqGklS76kdwwESb_P!27U^zOOYiaYKnIX%`@>kYJRM5!6+9P6UVtrN@ew`J<y}05e-`%f='
    'Y(x7O%Z0;%sc_NVM_3?0v>%!+S>VJprDx#}pVXy<7&&ItQ>facinlW+Tqj6bxdLG%MP=&y>1@2D>p9g6DGn#I1nm3l5X5n!k5|U3'
    '*DwdoXr)A}xS^L3kN-o`Zq`+ZfIrI2v?ISZaxsB*>e9~S-Pav)dw%h#eQVzl!uc5rdjb;hN@1qDxhIm8DX<#}Q3Gq5G%6AuAIQCd'
    'g`Ng8ZiK69Ff7JT?g6@?KucD*a$G-|4MWxO6+1qANQ4s8Qw2+A?)i}TC%4sSAK)2LMQ^h8zm$V`=Te9E^)^2sRknG%7Vqy{Ua$(X'
    'gC>W<4TBDk@kual8YAK*&jctN3MHgNNP%|s@~iMbJv*r2kZoVCvElWY4AMn+|K-#^FfSj6Ap5fE6!aXGWnbf#?nDbO36&I&dgG<j'
    '(VR}H1q=)pAN@d!3=U$@2^a0z%ki{|)c_;2$}s04tWsXbrtzr=2SY*&O8}X?(~3$oKXH;4NfgoK6a|J@#_wKJ4dIzC6`NfiTY)A$'
    '(;Z-;b2m60*wPOFlz+|zzYKm!N4J`BI1xgnYq{ik;ib-KMdb<o;1zbHQE<;j(oq5HXZaT04$z6<eP_G;ioDg_ak{@Jg3)5I8jZh1'
    '!=1t}kBkc#lU5F#MpVWqMbV#)r+K!gP;<EBJ7F0{=&N=Py`*xY2;!wd5n=5obz~m-%asz-7muW^(Q#~xt@nSymN=yI^E@^?o5~V_'
    'Xnv35GEe|q1uFwx!n#adMOZsGXZkn_9VWv$!Oa^GDK2d-eaTW{8Us{}J$juuqM$L@oPasl4VNw>_!#+457VrpzUId&)q?N|j>6<y'
    'V+O5}@4X|Uw#p6LaM`O<;1yiU>BzP&si_sdz*<>?%RKC_D4Z|#`X}O!fm`p=I=r11Z&^QRwN0ZnqdX)!Eio7T(E0)8@^Sq$Q2=p-'
    'm{Vd)>R{?Zln*m3M3!p>)ON>(HP0JyBXu*>KYISGyhr03fL>ur1T3zes<hdYIYBu~Ruh&^wW>??*2xGe5owa+;g}&J9}nyF%IWD>'
    '9<`qMpmv_eS5C(12CpX{h&uzF#qD8HjnI~pvrsFkPet_aA~*y?m$OM!_AiN5pqNiG7Fg(fr&?<{*4`+qQ5a&J6=|>Vrsre8=cSVj'
    'y)V1%FK6iBx!3+B{%m81Ar0q#OcJ&vo7y6m+$CxjbGr1;QF8XcFvtaeMp-fYkz)iU$x_gEk{<9RX?2=6*`Mct%D~J#j*n>*h>Gql'
    'lrRgNidI@6E=2M3K>z<7_@QS3ZI=2Q=}8pOW>g?G?M|B1*6>S3C-HCH9l*5iUvv(be&Vp7uy|WMEo=K6_$<G2xwXWk(wL2Z9T06+'
    'qS<38LOyqRaQt9Q*I#}BP64dwUNY}Y_}W-b+>RtCHT-=2G3b=#V;S(s`>Ua0K5?7^I%flmzFC6)@NBnnAHic${%9(*E(r-`2C6Vz'
    '?H+?4_;`&>z37nH>VsADA(UmEzh=;lqL=LEqm3_$n*Z>s#zPW2f=GIohz<huG_D?;|MnrA9WB*6uti;zQG#~E0NYxB?VN7{<5wAi'
    '>S2a7@9KQndZU}mL4jSU=2(D*txfd?v=JkXfFKXkTaPa4IJK!Iv!Zm(-V`55<h8Qp`qjK+c(Wk#rH6}iBRFT;qwtG1!~iuJSe2a<'
    't~#hWGUaxZFwPH{z{Tfh?Xk4AgetGzmU`NdEXrDtPo2INF?A(>-6NCz;XV%0RTg{8t9thB`(s;`WKutO^R;*x`!(dXDo#bVuPpKn'
    '$3geCpR$tCBZ(m0c4!M2qgnJ(hlg3M=Hjwa6fTebx{M05DL*=mifsWJ&Y3UjSyJ5YwQOEaB}GGH;8dgvNc6AfYC?{GKsRQVj$$VI'
    'bi~672iCW+c&o2O{^S?1B41d^h1`i0CffQ4h&eX&f?(9FTKT)owFuAdKv+_AU&OULy$1dYc9SyLU-}|pMDjcbaW_uoYxj(dM4!vQ'
    'ire-Sbi*x}nrNs?r5I^#?i`|?PRb1IO+x$4RGg>_`<xJNw0SWb@?TxxCGu)Uj&Mm$gu{)WQ|NQK7SuZG40k{1<w*Npf!CqHlD1_4'
    '%eW`B>kAPsQMYfepluBsDpC;JZN71=C4d-oR80{<`u~L5@2x12H%V`8&DnMeO)t|Oo;9TXCWDl)i^uPPcqYF0;4Z(0#}Jrax-GN@'
    'R*d=k=9z6@3MoH2Uz(t-D~O>q8Sg3O-&3I$E8Wcnc^#=RFu)Jrgh^;#o~7RnB5Zk${SKwPHiU<>Wt9Dbu`Ti(`A26NN@xn@a50FV'
    '0AN6782sXH80FJE=>zrS&l^}BLQ9&}w|^yi+(nQ_>Soh`hxvo%@#Sz+MFa2)htuwFR``7*Thy)wbi!aBo1B0$%xWf%AN@|Chj&2R'
    'LtD_WKn4EcZa9+aJCi~*ZbAp#b??k8>{&motP|U?3SsMhEG7g_-ge0invBTez)ZE(&Ckz2)GCX&70sp_7;k90+&`J~zd!@An5q0z'
    'k^$16mV0e+RNW4{SSTH0FD#%G{SxI!!R@Va=~5&PHH22B65KIJD#%JA@0^I<UI{-kt^aSQr1lz*z+^)M)Q?8tiO(U&9;2(d0}*W%'
    'qWWm~F-C*j1ukeme^WvfFKdRZATd|VP+~psL}|_139gwUr1h=8|8p!G7@aOnUWnuTKqm<JDopmTjZtQ<hDf~2M_{TeeN+JIS=|D$'
    'tYQbyB@83P9cI2Q;r3iJ$ixBw>5RkGK~^F^HxHPETP@E#LPi5Dvv8N;W$>4!xp-V<)p^=@ZBq%ZhbO~pw77!`)SLf5pv&Litc+T;'
    '!w6SUMttc12EX<YY-s9|971|G4Q$wZLoWjxBe3lPc_`Rrj<)96{;F0rccJQiqQF`iCgV=dWHtyu+jHkW;vi&Zd5S@(0@;HtkI{I7'
    'kYOD8(E%9%;jJI4{Eb3~H9&0DJI%kwVLv#($IL18E-jexC2A+2Evb7%lQrzJ9ws*DHMRU?u5>?rdgp^%r?tg|J5GLMP*v~|FKaTd'
    'Hy0~dCm-nXW;AbD<~*5QlO2)ABW|&bZ`-Di;@m`QzCv-bh$0Yi?VV^%3tE%1wjp-$UxZpYFIwC>L1s!;B*Jn$%J&jwx)71A?}F=u'
    '2jIxMPkQ7mnzFnaYv}q{FXfJ>fsv}+vcT<vCyhrs4j!T}l@J{D!K&cs#3X5km68XgAj$49lb9$4VEdLzm#=P7j!Ty_k|a05DZh#C'
    'LtyBc1@!A&1L{S~Vfw6sm9x=CO9Su|Ta?IMH<C2`{jFOf<>l@0@LROrVNuG2w&vVZQpY_?1PF=o3|#2w*v)wN(#05B=mxyLF=F{K'
    ';ZADrrh&Qt=eW=!jLbEliY`g_*`}^otb~LUi)aEr#9f93JeCXD&{OYn9anNgq58)$GWhyfhi%V&S=9QJLPF<dw8(P-XSO<wtle;i'
    'Z11?pJO*yWwz;glM#nG#;z~Z|f|t4|QgW(9k^*GgVr?u1`(6mHbesl<23~9240di$fOvzg(E>VAx3NnnAGE)Z;SiX*SONnWz22{Z'
    'sCa{w_baYSsa_-njjJndtDJxBNG4CBbeDGT^5yK@Rm|IYRGVwB4KBBf&l;Mxem>1s&{4zSy#ZOt9TZu-Tn`bc#Uci;4?gfbKbe*#'
    'OeobcZ80Ht5L4oPb*s5~*-qjd-I+R%Z66Wv?J#f#iKb*0c&p|6rQ$r0gMOO~EKzv2xtrI`zwqD+AvQTXlz9>!|9wUBYd^Y+b3{h='
    '-Z*-kYd$T6t0k?ab0-;Ip)|BavyZlk&ecWj0ClFj*AH2ZNIVx5qvg#VHgVn(cPiVq_XUX0hO--=bGMu%L41zbE^=>bInu!j(e7!}'
    'E?owACN^?6RFqns{{~NtNY$hYY}^sindWKUV%-M~#|!Qf4|Q9bd?((*{$q(ltTKm!@*$l`*I%=jjNCKnwV63;H%hXM$up*+=fZV!'
    '@w5-v`&poa4wDdhx<tSv@NeUOh(Z`$e|VZ3n{f_e``I$>;$c_`Eixrwz@H25DWOydlXjM6TI3n>>_AzOSqb&@Vk|Q1i;n7|x<L)d'
    '^!w{Nn*hE?wp-;=Ul9ie#P*U%2YkxPxNgkPWii)7?5Y#9N|)(w!z$|Kd(f6N=J&~Va4RRvbPvg$4<~cO6_o|>PJ<K{b*Eq1+Fr%j'
    'kNSh3_Uj$AWj<>AjXeM|_!^_4j3JMuGn{8~LVb<dT$S-RwXrdo9*h^g6ak7+@RhiRo*K)~pB@P`6mkak4U@ZFg7f0EARpSqy1~n2'
    'hoKtg&=~l6HW46(mm!8*q{H%AhYn-2<E1lL+Pfm$aP5&($eS#q08WMc5RfwX+mNa@SqU$LRhyw5QXu<&FmNlcw~bUFe^nLh!_^2D'
    'nxl(kB#sM%RmySb7pfmF4^q(iW)T}}VG4*nEUXFDh8kBru>ATF-XAev+_9osI?mLM)8ubmiBz$`Bn(c)q)U`cQ4+Ln{52Z(z2TLe'
    'J@rn3uu=Xo97jUsYm%6&Edqo!ort!l@9C^&^se<dr8AE6PqQfq279DX_6la>z8}S28PY&Km@QTGbRM_50s<zI-1X^YoXk_{Z()dH'
    '{Bg>6$^_~-4ss@Ve|yJ)e)ATQ(ete&R%PfA{IGb%fh>>;ThWzr+g;SkOsnh5!}9iPS3jxFyIIsZ+Exric6sJbK=4+2e%B+#AY?t-'
    '6&?}l5C%_P{)HT4wA}ho1CQ9zFe?!vDvI%zaOa>{AuQDsl`KjK?fA!hop0Rf?kl^sDY=K6Pfs|-pBeV2>CPByhBH*Y$c+>$DvMXO'
    ')J;X{rGj#FXRVsd3$IiZjJ?yQz(SQ^n=V?2^;C)(Koz$)*f`Z_hj!_5a|qtDlwBypJbR+*zmZKiQ)JKCPyA@giQA=eyG9EfRxsJ5'
    'h8YV+NJ;*uF?_Iz<~$es%BT7pEdOpKGlrTHpOuGuWNW980d7CE;pHN}MpU<=0Q}mz^;PYZMy174QFq=d=U1Xqf2Ru;G^&0PA6LIE'
    '_hhh>K4wnRfB@zU`3EVvky3RTx1g93JTQ-fiFOj@Y9Elzic8BNW(s<|FGkv3t}(;_em(V*%h4#@89ioAO6P4s?Kh(HN0<wu^9-K+'
    'f33F|e<&9Zg%?#aG46!wHkMM%YyP+;HnDtu9-?dt_)alwqmUMtWR*$`L9nTwJS&SUce|qswc#rga_UD?YbEP|Q@bX?<{}4B&`|FP'
    'BChzgH>+M<F-6oVzVmch^Xesz%H<z8BQPh{thZc-aU4|BNFZLets(h6X?TLZhtft4J##3cqi*&3w;l4}F5~=Zg!3=U&W=s4*crE!'
    '*p|yIDC}Xz0IC716>==zNAt*^KscPh_<20QDK4wDHIxD7#V`Q9PVNlLERH|#IMGOjT;K#(gU1Q8Tg0jd32X*K)k83yH>(?lp#)C_'
    '<u7_;(;^h|1(My}cIhkdR8GAB_nHS$cd)oZo51w^JMMbPgX=1pOfh*OQgEFbSMd3A5?l0qmxl*lpb^J?CWIU_xRQA=`;i>Z>abFx'
    'zl!EGt?|{KfA)mS-$R$BD(|I?v{|yqylsjCNOYX)^&I3ktpm?D?>Cp)Sp2=x7;){8-1*qC_po)*pU{uk8FQ<EE=l-iKBsm35tICC'
    'Hh&k~ZG&#;Wo_;mRb^nMm@kp9NkFY~uxFNwcn8v8+tXl?_(az;EC1Dlj0}p8TDpeaJ}8Q)+5@AV-EfMd=jy}V%3C%yp0PnKP0z|E'
    'Dd&g9{?UujD4yFH6fuAi6B+o(F$l|Q6Jcmdvrd|oB1wiWQ8)iqaC&ug)pLUt9cGcxVMwWD-Ygkpr=YZ+(M|ag<b=RqD=6B`p#8VR'
    '=zZ+fg9J=XCV2D7<r1!!R^<wc5p*Xx@=PJQq@T6NIz3$R8y_CgPF}7(%K?mkjdKrf#QEgGD2+cF>28_NL$y1~D=ZxmiGBBJ0^u6K'
    's9X|!T43q8IfH_LEuB=Y0@!}or-whz8;X(>po@dukm)j!twUi*swRv?vV|+g;D95=3P;k+U(_i}H?T~8GB~he@(Rl1(0*8Wg}zy$'
    '!oN9K2!)HOgVe*o45cP&Z3SqaC2d$YxhC(3gTO5Ji&)6AYdFPoS_D(dx~a$gDG?FXvERdCA6~z8iL@zIAN_7EqPhSruz4$)`J&h#'
    '4wN^$FT3oH5ZT01Z##?fi>#F8OP&GL9zx=9uUyj-Flh4g=CbE)8Tgw_zN}LI%qUMOcD35G<&$ykqhhs`{eLlw|5M?bvBMk8TNM#9'
    'IMD6trSJKoiHQ_7S<7Hn6Jpvb(<it}@GRZ*nVUp2S{UxkwEg*CHr0-DX>m^tJ^Wot%c!dU5e9v^D<@)o<%##Xva?#rf4PK?t=@^S'
    'wH0_qE%risBs4`u(DC&JDQ$6oQV6;UW0y8Ynlet&hCs4e_;1)F3OK%TUoZvbCZXZD(iFeco&u`Vc~1_8obb`NH#5`UAX;nSX`QZ$'
    'XImEQ__1uYyi)2XE%ka-QM@p((YW-_Jbbkcz>Jk7s!}<Wi>e?_6V$EbI*JHaWjSk}I^GwEjR9Cge<{`fU1r^275%TMY*>Py+HwsB'
    '(f;BdybCusUDRV_62x1>5SkLRJ_P7E0|R!*hN)F~vl5?L3econm*+N)<a|9~m0{OCzWmw2J4n$f90%Il;-Wv7Fxb0HmwqLW2S!TR'
    'L*iS@Nu1=mCbpU&zJgS$dd%`Cr8#rK<B<BM-~+(hckmla8kCq8bDWiR9n|tx0n`{y|C0W{4CGx@BCEO<P7X{!C(v}JVab6J&o#F;'
    'wI{1_u6r0d<>*EVAr8NKkw#jJ$+`TxkM4m1<JdJW6C0OcU|qIxyL|=fX`v?b&TuRtr}LAMfc8e`!00>gOQTo@1IipnB?*jN;y;=i'
    'u|34Ibe!~(0!RO|h`x-fr?n$*nU?kd+8?JVoCcLpk?<s&*o>CZ{l-<rAW7g_LkR$bb{p#%XeFhF`$?u_|GJ^04&5NZ1}V|!`<~m*'
    '>ew#2K`7>_o;`)`z{&v_{b#g`LODk@N6S%+O2t+dv%(`&huDv?%#GKObmIxdKl`_9o`MCN>P_b~znaOym`rhF_*$!v95g8Uj)Zhd'
    'Vd3b3{(4+d(c*kyoM~l)ob<@Gp5~~CioGwn%hcb|0dA#1-4U~`q}5+Eg__g7m?W@hFIAn-VrB8F_}I{@DEIqjutX2X&_uZ2;{JJ4'
    's2=BcpK;^2m?VK${m2r>n9{P|XK-D}Ahn|`R(tC#bhX8e)YdHoERz(6JjVv8z;e2jY54S)^ypq^4{68+IAvD;k2Bph{tKf&-j=bl'
    'E{;ke_FtPbh)i+w=d4Xzfo1ruNv0k%Ra};!+tp{KW;Hy9)=g{oA!7`I>*w39jVd9J?%gOoptVjnLX_N@xRuVBl32tK19_S4N3DF@'
    'Y>adrCzD%{h?;~nk@IRm{R~c`E0zY1dr>0glkyiiqdOfdE*P=t0GgUV<-X;pkwRRSnk*R=QOty-XqrE&l}9H#$8Zd0|G{M#um|pT'
    '&e7%`uT11)_3HQgJ(?V2#{HLU{<kO@tocBpQk{-=<&&T6dY24je>R&-@M{yjLuxFLY!lQn6%*kgATrYoM2g(kNI$!nk<|d|XF*=F'
    '7dkDzkJC<79%&f;I;U>`W`PT+z{;sZ%#1s%gYZOO<Ox27l!SL0=KP2?+YG;9a82VC?;N&<<ayw(yzMZ1UV=ekVg1HbMVOjWY{71-'
    'J~>I#1eqP&^RPzLL-N732G(%BfZF>WXvNf6E^w_f9Mlund*SACK$60z>duHx01=`SdhuTBel&08vYmv@#)+u4Rvl^Q|8v&iW{(=c'
    'XT0gN8CF>vW&daX?|LS_!ry+jc%of%6|@vGCu%(u=P5txix#k!cy&DO*~_3!;U2h(ROf`v5Q@bi+bJwW3!I;7#qHm)JUSfIE@03+'
    'MTh2a8?oTgbAiq}85yLQ0IjE>Ckhhgj%x;g9c!9ldUNZ#lvHGYNCXRUZmFn-(W%Drb=lvkLd%_u92cDTk%_#3>*wx5u?&>aGfQ5S'
    'HWX$<<e*`8O0gtP#qr+fQ$`$(>KQ2(@a+d6>prOEGjuW-c9<c^Kn#dfho6@A*L~E*n{<a*q0RahdIn^Xks;9|;c%J4bx0Z#Ag0MH'
    'Xe@X16YoYa0lc-xJB3W-aa3g}eLr2kq7gUP8*6b&7W(Zb@|8f)h!wKBhI!#Ds1iZ9Y}X*_;b+h!g=qXFD@Cb*<{JiiFjyHHQPBUR'
    'KadqnfUBz|g}O?t+<($tiH>@fOI0_963JpUVoU9}#+22`3&$D%yCI}5#Q^-I*X}PkR_FT53Y!ZYeEX;tjinD&$`1Ry(rTk>FAn-d'
    'spK+;)#S9Qn~YI<rvQLOXB@Xe;$79d>t5+%4{8A}4fJWKA{PjMT$t##*xe>d)0#6ju!@$^35^hSa9j-20ZSLSUIae}kvU%y=7!7K'
    'ttoCT&U+bcOgL)^;ge1<(EN&VWYGYj`$cms0VSF%m|@coLW)6-gbsN0{2dZIgsQk_6f(aR#7tE{8|H3bl8>b!4YD*IGPC295{Th@'
    '8F{~suKJR+-q^gTY)t260&PmYLdKb^KZJ3)U_4YP_HwUSn0A9@i)5O4hvN=^9!G>|lxbu<j8%@Zgw+CMp^RqA{25xAtn*M46*;BA'
    '5(-^ig}>zY9?dG)j-v%yL@(8hzQQ<ZDbf;KrDf_=CoE6*v3cveIt}zC^z4Kq@~(e(RDQ3YroDWWLezP<29%-ZCzKmu*zDwMfx6SW'
    'DJxrzzMUm6HVkMH|1{de#!MzY<-fRD!vIk0yk-KGWE;j$MQ3k8@@aL)XO|E{*>^m({%)3Vzd{tTvCi@lBxG&XKrAkUOSy&o0vXT!'
    'R39<HDnlknvcw(VO*H)Z{TnlvZ0h3m=UO-k4LgF)QRS?Iki-B5ro{A6d9c0c<Z5O{KXzC(@@xN@#&%M_?tL8U?sf>?feN%nZz@G^'
    '`C@GGmbYM7a+K_)iK$ba9z;Ar%3>`>c6hlM3hxTJFtbyv@6tfd6XSPKQOrY@J&58}9!(@s?F^MwWXdJ{grkezz^r|Lxm^<-tRhO@'
    'im_nfukrn4<QYK@a~K*EKEeWKC$&|@+J~jO_!I5&rSU}u@YcLQ0@)cLw5>}^z+^=N9gOsuF4s8Cf2#l(k;W!N%fL%tD@~K-uKyuD'
    '&3e0^d;f!~BcP0^J2I<t<B_KOk8f)D`A40;JEH59DFqE;2g+Xk@3ei>yK0*IJs2i%3b}xnJmEM``hIvI%HV-nR7Z?0zl>@5UL7{Q'
    'JhAY38edVd;lt4u(u-~7fS<D^;TY}S*?6B+VdgJYJnXb<<m@>;L!b~_@uex6_UdJNlxb)<f(mqVVw}GoDQW9#R=F@K;eBi(*$j0}'
    'd5^5{vVzW~sbs?YMfR`3PxYGA=CjRRBfHX%Gd#5~L=Y`*B2qLpbl@XV1?I(dCGC09=8da^8jz&5Uc8&WBk-+Dr6bJxLN(_oQEC{A'
    'F2Z%Dxu2fDobo*4x@Z&B`Y}YJbB_sYi?a(4MP>RDjOedanvaw2-o~koP2T4N^@WN}*@rYSDA3Rr5YZ$JaT>;AWp*Ie?J}G8*>hB%'
    'YNMEFWwCez*Z$ntf~d2jQ-<Awa_TY6jcbf)HK}?Z>@>(L?Q`C@-X-jDWMs4tQ8_(|r1H-dOquNm)IIRQI;u!26L^e73+ioSj=2>F'
    'dJbecb%^yXyry-+>*y#*QJ6$Zbf5bm!Tx=596ynrzIBqeyP_oNU=kW+A4xC;bya-Cyzz=sC9>^L?>Zqhc({c$Pm&Ihn|UF}ON2V<'
    'P&vv~fatM8U{=PtW32wL7S!EyHdo(KzjQQ#L=p2#CxvwyU?gzlC~N7XqhuoQ^LvHFEyAS70C2wG*Cy?cmOKt!R$#85wSEFzu+kiZ'
    'tx)AISa4_%?3c5oU{`N0(K+fd!;{8^bPEWYvC3m=Iy#g(2=O~01HCP|5?${pjAoqq&>VDQ*Oyf{AM_da=Q?46%+J*t?mn0qU;!vd'
    '9grK05n0}Ea)ov;eq#sUlvZ(bU@~O$mqvBr<<%iduO&0)6r%vAPfIQd(X1D6^%uYjh9NXiP;7yrd%ClaEGNBWY+OYeH?xNbB<BjP'
    '$cnB9tjt^09~BiwPN{)M(8}5y3X+a1Jm1%Lp3T3oPuaGB4(nJB3UgfBqVhre?&fewk7F&|T;fPRA*GkLf`8Zo4SF%j(K06Xu^^fG'
    'lbeA)xpP$K{P@tZ3<b)Nli6ycc(;a=q6j<f!k9Mj9ok;5EL=K#HpVB!&@G*s0C&TtnXt(D92>(s>Cw6KUW5f0H2MrB4I{X`(^o8E'
    '=DL+@4D}`=+$UhWX8Iv(cI#%IrUX3CHK`^KId>;X-(ZoJ(M6D#vfiWwW#J_G*4z8SCH_wV0NeVS!UFo9<Isc2;Q;a`ru+_(`w)%6'
    'U)?+flyzY@p)b?;FDi}@jd*3MIY8G^NCPM{!pCgd=kI@GvR<ERDnI)mkv``o)vUQwpablT>#@X;AkRSOO|0#YymJ9gKUIIjH*$3B'
    'jTW-`hqJoWPbI{-;wicG1iX(?%=({cBgtHB<=HDb5c-LuQ#xcqBlwNI><GJIG!|>nNxWkL>tFz)1RH*Dj25;TNUSW;ms~bo$D0)e'
    'bowqFheg{lV9#Pi-Q@M-?KM1aNUmQX^<rz%Tj8K!(sCLcT=rwx1|z10IciUN$j0Pa3NepXNmYimmxe(kF+lkkI&{tvc{Iez<FZZl'
    '%%q9i)i$Gno_5XVX$pE-E;6KPW7%1mF?9o$cJDO=&V`Vu5}?j1kfscJhFN3?&=InHUldd0U8Rl|(@Ll8NTU4(04F=|frg7rk9}Ep'
    'YB8%i_xzVI?}(!Y)V?+xq51g~FW3O2{`4_!jE9d*(8)6-;_yGoFK;0m4YpYRYF7cqa&?w#8&%AmsOR9$=&pea;2Cp_2A|&Z0IV&{'
    'JDU!WdPgB7zP+_)$`Fb_Lr>K)mJJYmzYb~|QZCWv9ktt+H_UygkN!8L4MfkLw;MaHCgWJm+6ekg#`D7!%rG+Y6Ql_*|4_%jG156}'
    '`c}J5vjSnAu_t$~G-aUSyAn82`*+7{M;?(LO!0-|49=^_onn5+yeN9|KIvl3ear*Rg-J<tg%p|INb_*!-Y_6q`IzU{;84XZH5Dc6'
    'POwk~(DBgE%pz(`fy%jj+xTLVX4yGRSsnP=W}YV=K4c%BPp~?{-X3zA5i}9%tI_g34DQmdI8h(Lw{iGjL+viKoyZj>ZZPm1t<mkp'
    'M;qL>$#e}%tS^^&ZYy%nexCZdfGDu8R^IpS+S1uoZ61#gag>h;*MHxLLsaFu*I{Q|FX+RSLi=^q3Y?sA+X_(zknD1CmBN|{)7*VY'
    '8L|!Q#+2qW--i2mtnANsML-=q?a%3CX|Gw20j=A5KQI&aB)vvB&znG{R~oSUJDd<RmI}pwp70TG3zT3Nxz~Q|RkFn4E7Mgl`3kS@'
    '9dvxx+XL0J;OEH0y%n$Y2-r>aGTaH~@-}Bm%qc0M^}WunFzevvt1)_civ`R3!S;V=NEJ?X`rONDusk`zz_aEgy$rK^;u8??6m@h^'
    '&x&J=&Y6rkl7q*@Z>=>r?;YA6bC(Q6loV7baA-{U+a#SzbuDu*Xx9%>bhIm70`#S?-fmWdvPN5m1tO%Bqc4R(w)SU8(1~z*=$VC5'
    '2AO!_E|G2rlUH~`FE;F3GZiV(ym!aLf+YoW-jEkkQN|c|lJHv>e*oj|%{+(AdEgUoL6k2edb{k?GC4w0R+5E4vUCvrEsRt!V)yNv'
    'ext<q0;S(&%io@)CXklRz4oUP<j@-nJ$TeOsIHctAFBK2a4whjF&^u;q*Eocj2p-_Q8!t)s}@AOBTi#3ziexQA@i;@sj{@-rBSPe'
    '9l&AD1gu>R;L)(X(_IZmh;)GrVN=}Pw?&=^HAy;B^KMUDgc3j{(EKv=5kxNlV8fjg(P-&Xak>GV5jS%hZQT^Fh=ptIuXlnr6!M*l'
    'I_|Z%;anFCU<zBV$kT{QUphQQrXKhJzI&Inj|_kRAY8?zX9)hx%Wj)oypvvFMWxVF>w3wCur=D@*%c{HGBoagnMEaewLi&2ls_aO'
    'GF#=@lP1^QcR1nzKDp7lkH(?xRHLR_uTE<?SJoqhk9q81DfFZAYo<Tt4W^p}EFSIaou+Ju-N%t(rVGDvL+K)ln4Y7}UKSR^YMAT>'
    '6Wl=F3waBq+iZH?L5zpqVCHyutMzCyqU8Sy5z>5`Wcw6Vwe*>q=|mz9*XA*bNW30bG?TH&24Do)YcFJW1wR!2J_0zC6$mr;uTTO`'
    'F4(^kXzT03;sLl%|DsDOgesUMI~22nqqqf^O~U=<%qA6PvgMMG%LvRLRauD1@J+}CXWQb$e1QVQ{(HKB6~q=9ATLHl`yc>8!@Z0>'
    'p$RLHLiRu)%~u`4{@>o1=`TnCjT$UlqP94=i%v>^r2|zam$wlwd&(}<+~C2Squ8ra_AeiR%Pv$E`wUnO-g0xuI3#9m&xFA=061vK'
    'lQoWZo|#<IOd$%KKj7@A%A&gUFNu~1&gF4^7#RpEPWMu}PD|kS%Sz9lp4+H_Kc0(V)m%-$&_X*2840STYH532vHSDE`008+jr?uL'
    '5DU!Jzs|K`=JD^kTx7o$;5DJEYrjs@Z2dV7Z4ppW2rgjP{@5jdoZMK18F@&JjsKY#rj~?TCrjcBZmTVXJXLbfka9Dtp2UdJ=)As='
    '8Pu)J@PuU9*>fxo*a&-(IP8`8mbP1}{gOPU8#Bl1@vSzu{N0=L-^P&=ms@B(iUMC6yKAP9FrPq2ci8g6lb1!oQ4<~(XS9Af!b8#d'
    'ZKO8hKB4zKD{WNOGpi%z;QR8ej8b-I_cWE~18264>$U!W552T6mOsFhW-SMcg9qTtgQo4&sMhd&_n+vpvx!9`4WmQanaMIRdjnQ~'
    'I{*rCC^seJ_YLLA@VhG^N+Q~fBYDaR1-8$oMP(u_4dC*5SC~pD`iW!Ps@mO31a@t3qKO|cdtv2uaGa}^*TyyLFoJlC`nJgKwm*M`'
    '{(;;R!K|Q0&uD~w!`AqGoSR^MUy4p(c%;PXtanD#de?a0LX<MYSm6X0>p{r^>sia$r6J`NBIvz+d8?xjDQ}?=D<HS9)9C*2?Jx|M'
    'T=XeHaD8g1$E5kJ^;{29EBnWTnVnUJUlqUd%+)4lMEl9zazP+YfEEE{xnIj5Xc%s^&|^%#;ukcppeIiDwsOGOE}sx=fOJH(OW_Y-'
    '7Os`Iw_}OkOyagFw=gD8s_1ywW-4}(ay;+*zivBmbfOk^pfQb3f&je=v)?AV>hT1Kp4E1m_MJw!+-ux4^dau%)>%KfHo<X={D>Oi'
    'sWhF^z&LS4$%>g9L*`B`<$~m;OHK_A`DYQt6yQHiHG9%CbrT%=+gdtbm%FpElg=zpSVj&X9gQmYy(ScPWyhS=gL}agK&liiOf8Dk'
    'FWW!laFZc+A^K{`NDOIY2}Q<=?|s2oXXT9X6QT1|c+7QvFAFKqN|s%Fp>dn~2(lA)DQWyg3^{%8!xyNKBAIF%QEPlm*3v|+Xi~O>'
    'pv0!31R!C4^Td{MCDK8ZU%^H$^%U=p>2D>P>H*f=h7gy_(VnpvkO)AR)OgIbO9?O74K;b;W9MQ)-Aim~RLdTxNX;Y`|3qJE2K`Vw'
    '%=Rmo3X}s`+$Mf851pMxDv1-#l~m}RiFRNr07z{{6LsR^f^YuJeo(wXOhoqyX*}qxBuNClo_8+>m7e6u8iUp^`mW>UK#>*4HUmIH'
    'IU4NYZCy0y#@~P&0>el+f4Zz((gCXy9#`~meysD*_H=u)G`3@P(N|XuwViYOkaPnfVc}rX#;0?CZ02($zAKps>8~kTaPX2GoDLgb'
    'KhQkX8HH6B0d6wBhm2^wKfRK%hn{k2F8-^*xh*-m_<IKfHB-AQPS@g4VmPb}U3N8dcza8i&1^_yCtBK`2%)7;NJ|YNC<T0O;~y7R'
    'Cck~V36=zPP2{Mll>kPR0_GEwB=}mS`t`!_O}35@kH|fT*V`maEciYO-L7Lf>S>p#r7~&1JMbgo-pimQ`R?twGnwbQrTQ)lC^eq='
    ';bS%gqy*gyz7Tpn<V*)h*6I~51xkj00@)MW1<H*@GMuX{&(`+{p<@^8qC+hczmZ|I2cZ09xr=rKC1LEH==7YR2E8fc^&c|b?*Gw4'
    '{$>Bh8n#3<Rn0R1anfQ*&o;vbH{+KL%sBB_o0XssA@FSL74zRpUE%372tSBFELk}u@$NXja?^^1Q{6I-_pp4<M2rLDSwJ~?Rb5?V'
    'conj~hR)AxG7;jUCd0Kug#&E!p2f5C9)d=$Srixbvd)NT<8673f$OsVBY`A}qg9Zu(b~e(w&Qq>Klh`|*X^9Hr>R>8q;n<><QRl('
    'UEciWAi<GS0|=mp2wR)LE!qV?x1g=01Cy@4%cvByB5vGi5EslVa@}RqN=j=T>PPkmz?tEm$^?uUM6Rd;H$nsft#SfTi3y52k;E9r'
    '?<nqNc&gixVXC$7^}=^5X*Vz{fi7zhW!v>a>FI3qwnT3Wv)Y=Un$RQZ5JLqWvE&Jh0c6$W2Pi)pvv2zU_q686C$A)8nK_<?682!t'
    'l&&2y%EQu)(&k8x?9=5_kco|%Tyb)?gj#&4vv`=pgBAD>E8ve$E_%iQL^a0ONfC!h_LkehU_dI(U~=MdwO4#rNdjlgNaFPJxb$NH'
    '_}4HX(Vs{=ybKlM&NXkQFrE+zDloM5L9x9AG~}{w)kkBq$WYoj%96Amh&asKT=G#JqU9Pv2HfA}Sm1^>k$-x7vXB=MwY1C4&<<gi'
    'q#1{)!N**PBq>b{_y%b6##tq;KXggsnb(wvHGCOcgFWV2xUcSJuf(AD3%JU=f9xtH?5_5<e}Gfsm>Z>)#4CI5x0<N#yNI?JG;?yw'
    '&_e0@S^jjC1{(<g0LFz_=RxDq0XQR}Ln?7qZP7*W%0WP5rzzAt?EWIUk&+xlW4xjnf&fk0V`vbtT#CB<=f36|c@Wbi8W~Etdpm8K'
    ';YR~{@GZ->s)XpZAHiyWpwK*uVP*p_h;|g*o%3Zvh1AO4wkG7Qk06Mf6%x{~Bog%bB8ZUCf;adX`yYjDn{=7kn+X9-Sp=5?$Zb}&'
    'T-vLXK0JH@mXt8EU-p;#hkj@*l^JT}_3C_gkqu1ERyXo~W6Z+csVAFFEjg0P09UYaffBCpU~3N};<^nd5{90!gJjQ{+Q4nfMJWT&'
    'cAhNK{_gByIlY{G2JG7@h<<j5(lB3*A6nRqbXQd9)2*O&ew!MHoo!=*2-$oGx=K642icRA@;`}ZTvEm_dFcCk_e7kOQ7FkXp{=|8'
    'bya4^O;Ep8K1{}_f{^{G4y{<_JK+SBiwnh0fjc(AR_sLSqjCuI9=aU?>dG4&f7stxMc4?S?~`2e_-U9gn`zdV<c+P!%?73KDL`w='
    '+jaAK#S&up4LB@MB7e0hcT!M%UwI=nqL!=hYf7p-8Q!S#?n}`eL0?dS<h~{B!&<4gL}xIrS`4>2ViTMx45aSNlakN?Bj4qei^SSi'
    'sJz*~1ZXH^WqUalr8(Rl!)eR^vIH1dgntE6ZwovlFPBu2M!(&@0e4OcFu7fHv??byxS35m7$hgu+SBz3tAS%V+3T#c$aIM_K8ayd'
    'kw0YJO!neBT#=n+ry=NQn(Z%L=1y8L(wpUjJG#la>1jhvC)_7%SblioISu?HeG>atIg?-9qS#bb4#f7<VZ-EJgNi+`ndVcN2lrV_'
    'k;zC?=x8Do>&Y8*5SPnL{|n7*3<sjC8*~kS)u{)`En?tin$*6vL$im9t5WZqG#KB6%Tw%!p?xN)=2}Eo<yP`wUJpF-F-$Yph~e*Q'
    'j~T!aA;5&3gGAx8^1mdlx5W_~t68Mr>A}P9qPAT4HK!mhX8n!AZOwmzaOf&HWgefo-DCbN=*LF<cn;s?Qg43e=e|JP_D3$<pZ%YW'
    '{v+6Xn73R~y)I=7>)=(TP!U*jw3}F4okt>kF5;F>9tjjAxt|xO!MyJ-<MlTCth1JR&V8W1jN!+kI)|#y4Mvry5ziFgG+5|4++QDH'
    'U=&Gc$23Ek?HJuLD1*WY_u~d+12_Pny?+ibj<v60{C(yrnySQB(h#090FJCnt<<;%vWM`!YGcrwWe#4CxVfOff3UP@CJ*lk2<tvz'
    'QK<irvXclb;(UCt(~SHQjgOJ~m<oylE8P+HHy@56u8F>ggtV!4_<qF!I6WvpP!wm9M)+cm3GAj`P(i_vJO($!5j8n@^njT~06iWc'
    'o^Ev{xo1cTLc`%N!`&tc)Xi%ghG5!o-#Gjk{FP0X+~KvD>&WZ2d}i=E@fo0Fvt6x38&D*UFTaFgW9dEjANq5q@*zQXrFWmPftskq'
    '_B~rB<F%~6lE)*O*<8H`ch-wab(8}CJ{Dd0zkXn17AjU4BOK|B0PE&}!@v3&S6z1EtJtk<f271%D~cQ^jC(%glC?vBfsx1fM@d%0'
    '*3M|^mmY8Wt5X9B2)#X2rs9Q!3pMJ>iF-NJ<e_bK_4IaG$sLB;%GuK`&PF%bw=zE=g(u!@qZMQ<&y+o>yAZ{(VJ)sWW0=O<k`s>j'
    'IdGB7aAskqFuS%k({$ok_|G(2)s#6I!Yw(Z<pE8<eCv^Q&lY({7Y9%hNB{dZ!w~3;*;ShfG?%_u&C9~FCxy5TFqjE0d&<2j%59}8'
    'lA%Y<DDK#V9hU3fp7s*1N&zJ?BU({O<T)Q&#{HY*==xzy(EXjQki_HpqxNN}woSqYUa8J#wCq@#9HEU3j6p;Wjwc(w9mrLK)7_0U'
    'Zqo4L@oqo#n*zo@WL`NUYQ@JsOrw>6pX|r`RKt5#S+XEZ&%~GTQg<r0UqtK^L&r`YAJw@{=l*KMxRdh#S`oF2Sw_qx8a!aG4+t<V'
    'W8dRx<Lk_~@!$72V`!#$HFaWboUcP^F3wrlqe+|IwhpwFwP5&a^HFb|TY8g+BW-Ze3Vcy~fGP`3n~N_@pQi^Eb=I+VauaHZwW<I0'
    '5)>Zo-#MB)(~AVW`F+*6(8%RIRfCin5x9_-W9YF4xNdzlv-zSvHp5(mVySG!vz#8aq6RI!&I1cLf^r4<ie1M=3BM`LUDYabA1(Lr'
    '-L3tuk3y@RocD~4kW-RZy=E8_!2KZE8b8qs)O(tMbzQD06|5+qZB3!9BxP?GK>^VY_IMa#hcsom09-cs6e<Dtb1808s5J0buEV07'
    '3mmHCbOO^W1Zto?HI(Ru-4FEhSK|I4;D0#O8C8g_IR1S-uL=Ut>Dr3akQ8$k-4wF^Z)tG%;XqaG=PP(v`0PD`*KdqPu|`#&0jh)9'
    'lS;DqC2gAL4JA|~G8w_p(5@Pjv%%+<6ppig&#hr-S_$s_!gzDL3;Ac_b#RS_A07S~IszK#C`dthzNttuKr1Z+;{9;tDA03n)diX2'
    'EZ0ZuAS_9lUA`(x{JiR{;qnI1fC$j(_c`zPwa#JM0DI)}rq)^;JHg}tI{ZvQQ7z72L9_U_Y*E25R=tWuB6ZlN2;90tciJ-YugQlg'
    'JJ2VPAsoRJ_PASUtT0*WcLgfiIuUSSYJQFN^w2afMQ8f_{v-mqrg-n><cl#*(&?+CH}-5M@)WVoK2K-D`mPCu6~tm^)G8%a;(0JW'
    '!X$Q2_i_v`q?X;0l@T{0h)PZ{%_aQh43{kCfWWO1a2QWwL=KxEarY*K0Cq^Hg`tpqo^biX?{|}r`#k+0NSN5mnvv-+-E<lSqWDn?'
    'UurcLAXaRtqu|08l|z~giGf4unq^Am(D57k?p`9Dcrhv$^k58(1e=jJvBhl^GWI#T&GRFF(CQ?kW@CmwSEu|={+>u&?uWP#dMEUg'
    'cghk9;L;~mgK^?#JF|DS{#_T|bB8YifE+Ko*n+rMonFO9G%07m8(`^j1mNYMzcpvS-a~0f#V1R?Kw46Q5cCInncZ^A0d)rwpoeG4'
    'h3!93DV~#vP34#21?rdByj*iby<*<|JO3W}Q4BwyUfeqd<31o5M8R7Fu@D@_6VsDuHzm<O$UZG=@g+(L4)E6EIG7_7UK&#H)5K)M'
    '8gC|<Xg9hv2TEAHrsEhh&{p)L<;qcbdsY|_-mv_!B$7oD`uNhVcmxf02(#BC9QQ9l%9xNPaDfZi!nu?pwmwLJt(TJvboiJLs29zB'
    'v1uW&?jqi!xopbORRX#_sl9%)!9hq2^3h;0mNvj`D-|i@Y_(t}ovx8RjxDDK-jrvVFGY{Eym=gU1IDBM0(FjvAhl@?!G9QU%ornJ'
    '{ZD7uV6oeeB<2t@9>P2-1a%hy(Jy#0$Hgtm%B7hqCs)MPl#;?AxzepJAfxOpkXa2@PF<188eotYFJWlQ?LQZg9F8~0SB|}UCpC0g'
    'o}H^~Mw^IMJ2=h;4oQr^_$vD~Rj`u?hYd=jx%{9}{o9WecuL3l&D2bU<Zq&*yNAAd(E$|)H~-IM(n<XE&_?fsI$d67LEqNMhae5m'
    'VqpLAERC<){aXo{3FHTF*2GFVNUrWqXjV0szMDEKngZnJa#)+|jA##Q+$?H$tmley*r3)*8=5}Ss-SzK2YUC?52u5@8-D~{m>IRn'
    'Qs^SUcg0tNF0ybCYtSLnTh(`_W=|`L8IpBcxmk0X<Fw&;-O6n#XO*hJfWRC@oBwvyD$+L|gDfFbc)(+lYhx9jkaGy72_x8m=|}l}'
    'bu!Y!g-o6AQwFn%8g`&_jNWcVgv%#(Y$vGFASxG7bH-kQyr^zOhC!wpMLYQ9MRU{Ew89K|y8Ye{Mrg9s^rQJb6N|~gDVoaK_C~J@'
    'a6$3hbOTtLuxtrOu|Q~T#S`Ke)RfxjeZE*Kh8o(D__L2f1jHL;xjMdPw^3%z?ixg}qD*oN+rYTsaWg75G%z|G1*?!&n{1{&^D+*?'
    'UC9KK+5w~z^p7y*o}sleRiSMNf{Y83S+y6A1iOt+HFqz_|AF27c!a;Qkw9ad6|J`~BpSR(vW37WzshS)Rs-R_^T*mw60g^n+Xi_2'
    '7wsK^`XNcDZYRe*FKSMAYLZp8{VR-9^8ut-)`j|G6RowH(c(oeF=9>S4SXs<JEu*c`fKOnnY}v)#-B-%Bd&j)H#Y=%6P|@b0P)$G'
    '+8c4GRa+y+&9C_zmjf}7LQ77c6*9VQJCIDkdq4{Ow1IpQCvy6fDNm{?6a1bgSePhv$m+Wev#*+|NMx)2W)SS4<c#-@kOuWr(nN2q'
    '7wd8wxViXE7N-IRU77ikGn>Oz!BL~Q35zSjvyEs9KxUHLtW4nDFsoY{D%jqVVqGA@{I%?sRUL&V%0NY)ue~^dZNhz|>l|R{PxlK{'
    'h5Ufee?L5dhDB#Or25f1NnOny>lUlTCyNFj9(BnHP0DWVIBxgI^bbc`67UyeXhXfID|b;xD_Ei&onNpEH+{|Wy46`5c@1D0*j=eH'
    '`SSGXPM!}JbIm#jBUrn?+@A`_dW~)@`zsrBENN+}Im)PG%M~ZoW{Qs3Vm(>t2<5nTll^0SOVw!2=?dHYyCO8zxRPn}Lk>k>0UmpC'
    'jT5<~m?ph4a3Lqc$5OKd*E3o5oWgE}M?-^#=*DXq(d+I{M)=wY<xO>kQO;e?SG4xYIvKn+m>*QR`GRQneqdrY04)~yDo=rU5|}PN'
    'pgE9`A!dOaU6oc82Bsdkn`VQv=z%P}nuq&#c<Cg1B{CyLoGSmUuuDL|$*e!5)6(PG7SbbEOkT40RE@zC%@uOZ`iE-1LYVt(1s&<q'
    '<tHaGEP;-io{qNRL+fhN?<3nGLv9P{b0$!}AuuI3Wh?t$AX;E!r!Yr5+TD6`FwMk@yXP|Ch<vcv5taq;Gn!AB^2gT(>*k5CO?Mzl'
    'GBEZUEWX$2nO;fux)DoAco8^7>vw2%wNFEggyri%pTFwwp9i>*QJ>aU0^&=DtJlo2jLtRdAXtLaIGmIiJ|ddX7S<A#P}L;}ZfGqv'
    ')W`1~Mfk(?z}TunLxfBKTFx!N$&ijd2>mvqQ%tdoL`2)Veh8qp@h@kyTb%o;R|?HjX*KhD2vN);D)*@E;;$-zcliJ=n%y47wbao@'
    'B5@Q}r&Oa_BlLNW+)9DP@%%bF@>bn?_$8)=aM4Ab1-!wh4>Fi<Q{H==BE{0EpbAiyL*IJQ#L~O|=qFw*h>T441f@f}H4F2e2>RLv'
    'BvA(zCDmnBx5GAO#kEkQ9n^&p|Kc6G`L#G3$2G(jY$=xY9(k+I*?j|Ak}g<xfn$ls<M&UF!ItIZ#nmYowqy4OZ)7MyLbN(e@}N)i'
    'kx(==L~#m$TvD5FAgzBMr{f~P?2@rTRqvQU4R-&|!^Iaq8L3%e&4hj`rbrEWSYUq+mRo^>1@MW&EV~Wg(e_F{s{+lqpgzT)rvlwB'
    '3yhPEP^faSdatOjxQ+S<pZN*EMd?i*=S}6AGe~6vd%@0+3X}nFjL(-VnxhTchtTbq7F=h5y2BXhMp_1%63fxKwmmrN5q(aKBkDKL'
    'Apr6D@#(R`IilOEKTbjDA(%7`Un{-^J(eu@-P@_!rt&r<&~ACuz31PR7uIJs1skA(jcvN;Y*ZOGC=|{xNxl{?3iT%IgP02853NA!'
    'j#@@Ar16oGv%(j7i5ldse@8|34J1$FNf{g(Gi^ay>bT=y7cz$5ULD9gw<+9aK)&FpMu*TxS_*z^G@aa&=SDNRmyrK6y;1$h`sDhP'
    'O)7-a4L>YWHA`=frinmt>KFpKwMM|$#oUKG3vf_elWQdx3zf5I2W%%<9V!RU7y)t^j7)z+v1)MVQOwKogOc6Hv-a2y!95fDF%tTn'
    '8j$LuKt53Xi9pk$ah%ALps!`L5)|4*vs~!tjtD?+TiCLB$)-_8Cyc{Re1d_giQ;XpeGJEqgE@q~mfc_nh$yKKN&0-=nc!iIl^gs&'
    'O9#hR<Z|BA{&zU6ML|+w8=|#BR+(#0OUy25phJ$2br2U95maxc*w;oj>lcXJuTXV+rR(jfSLPEFC2oZrB4LN3lD^p({8Ul2u^x-h'
    'GubJvNOU@L_L`PJk~gcMsZ($?-)z|eIshahgf^@u(s<m<+pV~OP}4Itr#^09*OVP`@gAn<kzeRiF&w|fk#*D=B;9Ss!)lAjG4A(3'
    'c1d|_XmWTSUzbj4>^5TQaH4q=CIR!0cM1U2i?qLWx>511HAzCYu@l1`UEovgUY9uRtIIJ!l$k%8Yg5~KfF$EfCL^JP@vq&Og>b`B'
    '?k6QWJ;_a(a1Av>$P~aAcr~@$nsz7G0+?7HM~cvv%7?F4DNAyNL!c^;Xu-VM2P?utghlOUCMvmwfD`b#@}%+%AtP~5!i;8~io->-'
    '>wV88eNLfy&fsQ0Lgi1BD}wZ;JAH5#1P=KwQX~1~tlmCRC3f{TL$}8Dr3rAh&#gZMd+jsgD&j&2$BX>QN1GYuf!+jn4e=P@S@|$>'
    'st0O(?eub9m*1%quuhwA#)7lkk9n<b<coXa;T2NHSyI$e=}Sxy(V{F3R(ojA`IM(TgPM_rL!-G)S1_!W;%$)KQCG^r6}bK4=@4^&'
    'JKJM4#1mZf1y{6+2Ydv>Yh|5%aXYN1v{Bfikm~t%@-gq+`dnKra0<)(q<@!ygc31aca08jC`s>gh{d4n&6I%@Io|8f<9iaHr6j&('
    '6RSv5ZRE#%vEJ}ZzYAnInJ68wL}T8WS^7pvSPDd}Z(snHv57RUGz9*QP;RgzIcp%5kHoNg*E;5gWU_KxNMVO=BKt1^1P1TVDTg7I'
    '^*oSlP#Ak2rMHYVP)4|(s@1oraw#uGN(aqIUu%5>XGw9iXilubXkwkE%HM}XWEi?m;{ci$of}Y@uA8qMs^iHrnT6+c_B(g$HQ!_F'
    'Rf4z?4cGWyn2`*Dd<%T+P>O0_(~DWNeG9^PWE&?6QBI>3<POyRLipGDO{#$%fO$}*+Hlcpfih$qYcr%@VY&TO47%{+_`0%(!^$>W'
    'kOuun$G#nIu6l@RjlppY|LTHo3lipfICJ7m)hih1s6}|M7jzi*hU`TWcsb~-|DLWqNN6Sijpd{c&VE#@#HYy*C<8+TKXYL2IKv(P'
    '9ggJZ{EK+QWSDe1u6b54ih3g!(be(%9@9!X)L*tSJK~i_Y2T)O>qmbP0`wPSxA}kGVT0Vs&h>dr_sUS|E-!1Z8%pRjmo3uR!c7{i'
    'c#<0*$1St3Je4f~lEBwsrEs9;>^R?BwgyxV@j(=e4H?Kf^J`IZ!oe~X*J8%>#4q7%-Kl`hk2~sQez5UZe`?m?n(41s0OvCZ7(-rV'
    'QN>2cM`8qxEFk8<c&AoLfiz2^A)ttfOwpEF=5a9qLs&eO!2PqoI7PD6c!?xmd3#vSRAy-7vjZa?_nE6&%}Bu)(R=>i2m5djzs%0a'
    'X?c5!)gO0~myVaxTHG?6_})sg%(|c8|DzC>;rYk652)4^Men#Sl@;e4`jX~<I=j#)q^E;>1CDMRfUAu;2iL4h)Lk!;5guu$jB_e2'
    'kovHOqit<hSHDS++T?cMcXi_c(ynP6W7AbxXih47s(Jbbd*UU?kcWdeZNo!dBc?EU4@ckxa8Up%fb8hoUM8b$Kv+{Fw}v+jn0?Az'
    'TsC?lt)z^Rn&g3aSku5MAq(F$>+f$x26XG!*F6{1@mO#`!9Z@2+`JsI=qB9_!Ck411T{iASxZw!vRqSo5B=aQ&``)Etga!FPN@S('
    'hEq?j9dY<jpas;m4rn09-BmcV<$oBxprs11EbVeo3*qvLQ+hlP#9r8sKoK51^-^n{PaHP4MB^PS{p4*#&{~DKf~uX}FHI4MPt*LS'
    '!5hRs0JJ=^)^2|JZx?1zUzvSv=>|j;Q>rEL=|<bG+Aj(<c20gTi!$@zTS=r8%1PfkzHYRVAqGvosxgqEwB34vUYsqoGw6_IAYcfw'
    'M+Y)>9Eta>UinMuVSrK`9szEkFKV2PnMDcjo%+f5rwBY?a^P60LgLW8NK@|HZiNaVblCTyhGwaDrgy&pz6SLIo?oO9-z#Wsyx#Bk'
    'lrTMwn@$e=I`<tSQ^i1vfzck2(G-%r@jYmXiyape(*<~G*L~nd|8(L!ti;86w;ZOhUGMzo%)AX*Y9ZP}Z~(@7eevkEe|88u2qyk+'
    'Vqrlb^d)<KbpBLlofBXz?>XS%^nc|311-jh(!PW=qLJJu<*w0+20+AAXeA;1IyCD1uh?MKNkL=-vi~eN3f-0Bbt~yqbY%nc?4@M*'
    'lJlS|LdzwkKtiz+8W~5L+y(V2F{ubgL0)#*QWOs~xr}F)FwDBbB6-qJN_!<Ih02p@ts@Mweo%Dmv}Ke7>o5L$VH^J_1KA2CPlbuX'
    'F`tn%PNeg1OW%aNrHKh=PRq3%jYE*4g7b<9|4WrZf8Xg@RfQMF4R=nOx8*71UGYd>d_AIPeUR)##bs_Ny4N&HBSX+AY#T)dh#^L;'
    'DJ=MN<AzTw@GuCl+fcsXbzSdRX!f@cI9RsQ@=bD+r;)o<Z_-f>(cw4#=#(=0l;e6c<iYtvc~bqBikntUjoXT~X@3kF>MiINhv}Z5'
    ';<_0Viz%7i64rotw>N_C1@G)B#YkIw^-EPr0tKE7J=sUax8?ruXv!>V2RY-W+MSn*Fq;ajrq!cwX)H%nkiO^fcLCw33J=TvNd^;F'
    'kN7v87He2EI2&NX*mdoByY`u*@wS2Dd%ayaK&X8`h+I(mkwYa)cXVn>$L7{siuMTiZAL-L$l3AjTCuAaQ*9(VA&yyVWJo_#0sVF^'
    'RQ*InLE4L=t6c9etGG=!1pb5xfRc@f8;k`U<<BZy9-F{Oqx)A<AUC>I%myE^+5}f&&7sR&zEu1N<7>XL$;h-#*I^eJM0svAeZC)U'
    '=7_(RFuU0TpmGfDblKe2*_8q_4{TIsZ4V)HxQ}UoWPwX+6VwWjF!<5wXUv;$c-5JK(X1ugLajZ-0&?>J0kV&Yh8R{^u0PxjI0$~t'
    's}OWPhq^lZ(b!t_pznnk35+={3eDo>KcF7P`;1&yFf-!*S*cN^);nG4%4ENko2D&%(_#(U)=qPhM?3OQjp8Oh>pw<PRd~N`zHa-}'
    '%d&1Dru?zM6{h&jQS~IW%~}A(2=w@ikMOR2A^4Bk{V8rir~3R)X#UY)&bE?oLZgGap=gZzYVq4AVExMR$RfDGamSO{IETiz<lbJE'
    '^(m4cyYS_X(yqE%!y;!N0~4BEws|bO9=qe(DNYe1j)>-f4gPZ9;rhF^DyRWxkyroW6zf>U{`&iG@Ala`oac2Xl>%3;A!o6xa$Eno'
    'iB4AH(2qUC6+|M&Z>K+X1%E;i11$qgS9H(_G+EPa5+*nON3}7t5#R0EVj4ggiq0!4`<WN`#a<xhb);YEBUa%wGoqdkD~e_V^#_Yt'
    'KPo6L@wpkuJLs;U`1Vj=blgucBmRpn90$@e0=k&oL>zDf;<J*T@~vNqy8*kbgmXixi+xR-1l;4#)`tiW>4<m?EEBLABtJYbCCn^I'
    '25nk4lkvV*u(k1%{TjDpzpR>Cy=$nT+}FOMdVA_hNElrIMkxvBZ<b(DAW;LJ9RO;#Xiy1va5dWgDfFGG7~^A|3ttFC6S5T^9zR6`'
    '{<Smd?smOQ(x?}Un~?z}V%1JaA=VICRvMJoC0Eev^{xua#a<*A3I+TV%s+=@Z#%Oqx_R#14;=J3F0Q2CY<m#cHfu>$xTlBL4u?w`'
    '5!uO1+<u+3xFFrD5;7haGw426>M2a){8lI<xxWfz`hxeHPWtD4CE|ROlS5u^qC7bgSlL@&I!9`+DTY#fUcR7oKhO!ZV_f5A(8-zs'
    'ctC$U4BIR49xM)sCsq>UckrG`-O^S{ZTr^ITj%+hNG@UcbdrLjbh+9l0n3FCKS9#H=L;g97{ztZ;QaGvxgb*HSzMx%)|c3g;1d~|'
    'G^2N%IyrdQM6Ux}Mz4sVv)D8&aI2*nzZ!6y;+dwy(EF(^E63CK1=dz^e?@pLwA=du+!&w18&_?pw@DC}2VBTZw&W>1H!cOzpU8bu'
    '+c+kXQ3V-rl@hPtg)3>=?}JN-!s-F*HZ^u+?@-d;e_=zu<Qmo`;IUvdFlgr8&m|T)t%+&-PcnKX1)5WO4pBN91{%S=M-$xmdP$~q'
    'v&tGZ(l1~mQU8_8%?B<_RJQ<?CLi~%SSeg|la5^3KDkgx6FD<~!sVCLo*!-5%rKZ9EcKDUH{c1@f9i4e^5b72#`tykapfrzQb@PH'
    '=m-HD{gJIqol&=850n<mM}QoAvXwtZy$&ia;cPs%OZG3pRdVU8Nq|lG95S$c@Im4^XE0Ty8pX88NmIUXZZ+Fk3SbSO;lO2X7SOBn'
    'u_o_65Rq0TT4j{G{?0l|GZMOucC<ut0Oy?ju9Q65gQpSAHH>G_(_IZ$hZ-cHaZgB#t~lBu(tZ4K1b$^+UKPejCTTu-gYUL)`foTt'
    'P1|Iea~D<OP^q_bDvGuXw96od1PLl518^2E0+Op^I5_J5{)ejaC^mJF!JykPyC}H_6E;*}Un?Mk`Gs2btY;8}7VM2<*~O%$V#<=q'
    '?MydX0U31Fga>62vGHd*8e3$({MTC}MyIRPLmMijrNaHEdo*BEyEr-h&3nL_^3K5N<F7&nc1!<I5YJCflzk2nDe^%2W<kx87}E&S'
    'H0dODY=o9Zj45e@?8W@|q3_UMe(V>6N)lhEw!}hfowM?PYNn^!uG1)@qGZTPFafhriBhg5+=5y{u6z3S4+k0KcZ))}b3@zQ6XShp'
    '+7&c8YIDA-n49szdKiDncmjjb8d~aAZ7z<#1K~``14FK^5x5H2L8#U)8FUlsPIDOzWL0E$9JT{-%d&jhmFv-tMma;vYo{x(2Cfpz'
    '++etog-3RZ<m^b<fE1-8s5qDQ74?Lm^WpEoAk94btXx0-K=7=Eg+>l;Z#|Fu?8trNp1*=m<kOb%tAI~g@K;g=d1zF_8V_rk=GJ~>'
    'VSyK5C7Phu>bGNvQTdHUUyYB_xdfxiD15e%AnyiB$q{FgnA8;&T0l~0!7l@Y3<yMZ#6MbM%V-%&>ig<|UXp$idT*rpS2LtfX8h<A'
    'n#BhpsAi{vJtQTzQ3KdaX~-{i&GaVlBB1?=?o}j3@;Ym(0q%$^DLl*|_?TF5cQrNg%4l$3W&tW{FqLuUl~kKK0~eYUfY#$G^CB;j'
    'mwl6SXvM2lVBfa1IqNsk*&^aoQIC?d=mEDlM3Xd-<U}_lX;K5Wntup?^hRQDd@J~|JcxayjBAktQA_}}?uTol@b8W@p+X@H+%w0g'
    '?9qh(Zz%3km{;Yk!Z5a~uC>1vM5CXva^>&RM21&oyy^=!Htba%4)&H<cBOoDmYgXWWP`*CUu$V9UbuF6R70B=l~#?AG=@#+&oYCF'
    'e+1{3b%2=Dzb6P4`SwSJ<#*oUcAx}a4{FP)<@}3eKINp6tm;zG3`D08Ycrd|!#o1tpVV0H4ew`S%D40D<{8)?l#5_BqTl=*y<zbQ'
    '_P@Du_(R=laOqf2@dW-YYU4_jQ0FAqU+1WxkhA)fQ51y*sG))%;-Yzp4&HfLZ^HY=cgBf&ZUm3S2cHWqU+y)*t!wMo-b9X_9SEtG'
    '0LL&atXww~IdMzg$nz|P`V!gOu7Vn-8f4SX{AEJ`L`0r9z~vg%HSK2@zP3`+tHirsfeu_KSiwk<d1~E(i5(KHeZ`a1*A}*`sA2qb'
    'DdZMa0Ny~FFO9Fe)0cJ=eHkLK<-8P?c7?N5XfU#%EI&%TKf!Ud?t{tsWLgqT@#xQ`$HHdX^AmFuEHEXHQd<0rw>0EQt;Mgi#xFpI'
    '&f8%$WRw<o1&-Vf4VBIsiv2nd#Px1~1*}D7{%unPv)6q)Ucj8zx6Xw<$N|{Zz?h{+z1pooByp%G(Y2%vYGc}-oC6Q6uz=vkdM1hv'
    'wH)uaM+b6dR_!fBijRJ~ZBKQ^CNHpz;82D)!*d(U6FV>qxWS584F^xM#NKU&ClkPJk=c4@LtH(c^*0+0MPhh>3KIMbkpZpy^{b7K'
    '^FR+X;t`zT_b!7Y_yY5Ay#Sg<+LZ~^E`M*Gr4%);<>a?A!{jHFN#<Jqlg{U3BiX~JveE^f2#Cfkrp!7$eNy{Qan4sqXWpShV{6$='
    'Db0x@QY$r|d-WZ;J#Tm^GuKXK&ONmz-6^2_o}-GEBqy-SJY8>4d#@(M5IHSK9c0U{4rYzF;uaus%l**(iG~uT*?lebR?PajDLe7-'
    '=N*BnOH0bpH&HgsT60fQWx0ZxxXduhLK7jUiEa8x9i%qNLZC-LObi(KSLNGR7}2mXKP#MsmZIkM$Qohs45>^WHBzCfnHQ8-p#7_|'
    'yMRA9Ia0eK=;q3r?wjcZzY^Ln>cpMsE$vIvp^0jg50<Y=YdN$uYK`1B3I4N*Kw#0<0ObEVa^|((a70^PiFviJ#<9%9M#wN%C`}{w'
    '+BgVId8<H*vHSU>*w@mnqKiNB`3{Rf>!KNBRm?-yw|tS%;^gd)kHG@bLM2+O9My3$;(`XXxxIG%(o4bq`5oPSZNKc}kQEm}l3xch'
    'X<Or)n`Qc`zH;H6PlRV7#{ei<0oA#@)!Kt<4VxGgkacr-JM$3WI=c;_2I`9gxZA1(g%a_F10&@Ef^df}FZP~~G=a&$=U$rzy{3G`'
    '(-rMe!vm{7LP1GFCXCqFE~)UCRPwlITT7L)$iwIHGu|=e;MX?jVHY3oT!R@zS;YCMTJ_=9FzR@f9^wQK83hFD*NeC@fSev4<JB?q'
    'ra$p;S$Q(nXjavOTy`=PbTCM!k@PCDG0>V!Ysu1XqmUF}gT-4sM72y+;MdSf)b6+7dR7=vlvVCM=m4i`l6p*^Lych5e+ao|Azu>i'
    '8*c#C@FxK@dxx1+z=Q06U1!%dfuGj5;NqiBXu2E$`!GEw8%TpJM#h<nK$oL7s!?httV&mD1$!IeqT^)WXGQ(-({0!1T9=2()llm|'
    'CSg(bj~=92Ld7?~&!o%%u<y7)ZJCj16R7MW$H~Jgs>70dIPU`JW~BQI+PgT}PS3`7bv9Z!A}D4h$t(13*Ikp9Q8D$V;+wk>2?{R^'
    '(QQS0Lgjv15le%Lb2do2FnLJtY5zsoQ1Yc1Q~IH+P_2?8zaRhu+9x_vE4XnAHC~^BEMMdos~x1Nm^>J|&5NT_FV0cazE!uGAu;!}'
    'S(cVRbqb@6<<0(@=r<o*mP?nB7oh?0qgLZKrAqOzHeJ||C^qeq8Nw_I(ck31PL*uc@9nWC^hvcO8ewpV=a>OlupU=(L$_x%n17nR'
    'P<6-VmxYhdWwj*XaCc~;eT!;Da1~yCO#homlzq_(jIMKkBrU=T*FiW|Q!6E$=Da!ux%?VjR9z@)@m>6IW~RZH+wPvAg?NhRh=6iM'
    'y8(mH?gYaI_IR4hw^6wR46Dxi$(vRM`CzZwNVohk6{OnH0zv4UOs(aTI>k2KtNH+E5;J9_WrXJDc}z;^L{n->NkWaI$<iC&KQ}d?'
    'BfnJ5z^pI-gx)^~8gmPe6PPdDyI!yAGsA>))bsyYD*>d7^bKm$1Q1*@ZhRN8u1B&9>f!C!w?`=nfsL+`k-ywBP~JYax7nyJOEnr}'
    '4#qK#Tx>UWf}-LVP#<DTY}oF4fbTGJ3ZnlzAf!+__af21HoK3+w>V14V=6&IeJ3~LABO87beeO!=X-8%Oh{EqH5CIF63_E$W-nPE'
    'yU5Fx&dq(9sJbZm@)SF-D4XH3eaN|pz_pZ^km5)W2-~72qr8Bn(uk#!0?4hK&qJf5t83@~)?oNLVg0d*W4orFfzFUS4sE$VP1KKW'
    'on^0S^bjepO*o(;<C#&txIHQlDYoK#4n=2@7^4pU3_!_Z%s^D(`b>tw?(i1Li!@pRmWB)3`Do5BZw1z)^RfDU>@P?Jwx<WNC82c@'
    '8^>G263=C9E8F&*K>-=ciL6Rf2p^(TxatG9n*fddPl@-z$j0eY&?xhiweW^3n}zFAlB4$_mED!4pIIS5k|W97y&D5tBjld(u+O)Q'
    '61fJrn(LN+;9<*d^;{m7R#SJ1&4h1ek6Kp{<yfDM$}H@w@L;ylIl|ov6kf8WW#&N}GTlTXXMn}Mm(G5j??t72mmtNK${UrVvhnBz'
    'nE&GZy|6^kk_)Cw%O3bA)DA4#M{Nb6p!-&SX>c#<BHr`Y%sXz<2gQFyZ~{+5IkG%7#tP};C9nsvGm=xW?)pnba*gI-@9jaLf}xbV'
    'g3hC2Ci$p48$%}5bic^r<ihoE))38_ntuu1S4(+flB6`QIb9u}x<>Y~m-U{0rjs!Z?SfYF=TujClo{IK@xU?xCBrawk3vUc2!N;%'
    '^a-QjWa4m;Mb$JPXVgL5eo;C3*uQ4=LOmz>Xb9l}!tx5JGJ4!MpKDo(#2&p0RQN+XEYmi&ocZGu6VwlWcbX)K248+-+)dkut-0Rl'
    '7t4$6O6JJ)fhJ~<j|b<$HCJw@O6H52I)1S!UqnBgmt_Esy)Zt|X{fOL<cKOV_AE5$8t>6Bi%c5m@y@H5hH-`i9aFK%rk}uP69+br'
    '0g8QCn9L=u-q!=~IlIY%)M_z6{a22DrsvQb(w`hc-#h_=I#Ho5U|n&fL82LtWp2@?E5_KxwkVC@C&#4zaw>gJ14$|~HgB@F{FynH'
    'V6LdE$se`aW|fFrEA7NiAncRw4S-pHIj&S@%j9!qH0t;tKW}MkAM69=PiO6j`c?4$T97#<C^KrJNOr{ZnjJmB^?&!rO>P)>gxlYO'
    'TzHs@@<lV=<ey6zmrptp;PNA=vZhfEf!!R~ZE`8SP?#3JmC9Io$K}bv{;uflw(l@0X@cppCJ49IBi|??-!}C@QUoNuWcrf>=Hr07'
    '=b7vNT*^8t{ytTVo!MV(-B>6T@y?!qdg#F@xsQF(u4<OUme}p?=&Mf4)0h{HJ2qD(R|HElcB>IFg3_E6kzu4$4Wwlp{Z6H9i>*nj'
    'D*=24-Fxe^t-Qv+3bi*=4rs`d$81hal$@BbF981<>KbDp9m(=3L94d9o(msG(x?H}nGSemVoVBl*j7T|y-5C$>Gut?>t0e+?p3;c'
    'w15bLqT>-v+%ebA!m9kba&MpN&{aeiY0LMd%*6-Q@fp%eG)L3wXo3w6ecZO1Fz#ka02F~r<B23T&1LCaQd#h=v*vD&2Y-eOrBH^3'
    ';Pk1!>xkD1Qg^Z7v5rg+Cvn2`zW=sQ-*Qu41ENQ=%2zf50J2F>x$u8xks7T`2o)}`#UC9f5qp!&sTZvF?D1;p>=L3Cb@e1}mrfou'
    '@0xGlBx90UY!U3~?|4v+B7a&V%Eu4q5X-j2&Yz}TGE`V%hSqEa(sDJ0&+)(oG9zoi?Cb>I!E|<H`tYZ`o8?)x)>+j|@DQwAC=XTm'
    '8?G27J4Wmk2rNl8kGt$lsP<|>TLXk#SJZiDdTts@JM@R8<keO!pb9hESLn5v4&f4_R;@r}>FLskBhu8>y@PE?tATe^>S$L1z{vzw'
    'M}<IQ#Wk`2yb2XE&4RP3!lBsK5_by2y{eIJ1@-zY!|dal$FJ2VW}U%3@{1V_^_jN4T2&KdS7Pa%hvw2TA~&Th*#V~B$;Iv*<F_fD'
    '(#khUX^2(6f6!$F!aEgJ-JZP~pC5`}KCmhC#lqEON`;lyGNGuX_L4HS*_c>aV~SS54+mt8HOm3;7J&2Cb~&RQ1yMLk|B6o&_?B3O'
    'T?iwt1AO#<<*&&ZlK*eKnC$&F-F*|S4wsbc61Ab&5;FoGR~$N_%vusdTAj<Z$!ec@p9>LwE&m3{xavN(B`<Guge=XPpgxbbVQPBU'
    '&kX;_FR+&A+h|V{-L^S8f~=6r)8Y(tIXVs}=FZ);X%6%m#!jKpH4BPkPw;uOSi(+HqTVZdc(NxbQaa-7vKkpR6JUl>(qGpkN@**c'
    'fJ!vgaL<|-NZ5hB5{hN}PrvQt#DfBSRXO;@6}Yvx?hB`Bqf#P(Cj6`R2zE7E@NX--L{M&h=|7?mxrZs==-0PBOT<ZZLgrySH^++0'
    '+6I3lCbYXk*NEhQQz+k-<V_J5x4t*gm~&@$T3i-Ej|Y>PSvGTR<i<S!id&S0Zy^S9QXSN8=#}4+t@ukvrsHw<6XkmxMx*wT4(_~G'
    'x1)m@=m}Qu9XQVrHNbF3jsP{XH6`YU`7H`NWA0<TZNa4cN;jJMFgwo+5wRDiZ?+v0j+e6IjHr2Ae^}k4e^mDQDmteIcTfKfC!LQw'
    '3{a>$P171v-U4l5;#oQR%a41i@&Oe+$>&&~KjHW7zca62GY4&1Fot@D`mPB7@6@k&o&}WkoOh|$D*XA3sr;HIWlKLr04_AQK5JZ%'
    'FM;+0IVnoTxL0xpOM65%2rKu4&PQN|>|LyFE*!LZ+wrq<ygx+^?Dm)STjMAHApNba490_rU-K7Pn||`4M6VC#UT)VLsDwPskpjP1'
    'Ao6*K?^nlu*>}`_nwrH%$kOC`BaYl3PdOjuO1xeH59+ieyv4Y$g0_5GQuc9Kl#PclUyi9>3ybZSCl(2cP2u@QrIXg}<TU2ZyL2J^'
    '!=hNzyOz-TTB5{MN$Sc47cH)K7?AiNe?jLgqiwL`sriDex7YI&#8S}CTAUw4E9dmwTS2A?fT~Td+<O;LDMdY_@~0ccT0$>@+t=VQ'
    '_0m^OEo{^}VkTxPaIy~KYY~%)&O%r`U~!_aR0&b`^=`g6wpQZ=emwY0tc1K;r6Zu`>`k|lE|>B#CMD0n;IGH+N`m3hosa63=!Oie'
    'fv+7WkIDX;QAR8o$NawLBYcYi1dK@MHH^qHh-460cpU~Jw9uzV$L5T2sRRir+r8-)Ai4%6mI>f%3bUE5LzR=gHl3R9PXnis?$Gby'
    'NgS#n-jT6}zW`~eX=71m9)pGU#cuzBFpo#=Q@_8Nzc*Gr{t|Z@RI95S)smT^XQCK7_5y05Dy}vNWeUtg^=!5kCi|kWwdw#!z&yeN'
    'KIq-EOXG&^!tLwx!|LF_rFjjOnqu+3h(#sB@jW^p(7H%tVKTk^504QqeTc|<jVZ;W4I&HFAj@w`QueSicB9WkHk99HF#F2yZNG1u'
    'LL|?9Wyw*g^Mqo~V5mjk2$dMMlYp+dTG0h+6BFhtz(ZV<mBu>h6j@>x?%^z5_+EKl+$iCDFv}!QVmXaFe)(nwi~g~#D$C*S&c6hh'
    '6(qySayu$oG}?>S!i=BL>93>Cs8VW#J4^mZrvX}Bdo9#WO3b=3{9YUC_UubqBnFxMwFJA$4Y|P7Sqk3Lp$?iW;ZLY3I2<{Os7my7'
    'rM~UvKgLz8r4dmqAk~7{;Z@wkaTSXd0}2q9dLmb^FQLW`eFW3=gj)r*3scKlT0eK@BlK3XOiAjt%CkD>_E!;1lre=rz4XpAG{7NB'
    '&VQC(i8KHFVR%>4NAykdVX`X8eePL01t5a0E40q|#R#2d*dJ@MScZ>KYlsMXAUnbmk=BN@nm%@&`_Iwhdp0KN!|a#l9BFj{ge|8|'
    'umX+i3Mj{$#)ro+6w<`pIY04ki+`{!btC*R3K<q}teBkW!7D%OvgZN@39Ln9!+clI_xR9VmX;YL_@`S>@8d_zwp5^*A;<|5bFP_7'
    'Z;TAO_h1)0$Pob_kMN61Z*E{0atuG&ox-^D=k1bIervH6osdw{x}-fy`BU7#dnbpoV1`)ud!N=U61Qye6U#&xT*47>>n7{B=w9Uh'
    'K&>%)*m+k<jI*pUm2Cs++H?-JHd-!jK2KQEReO3m_SB8TCMW=f%{vu2+0pt$5$+)AZ@;$Yes$evb+Vdu=#T3qCLin=gd@@G6sb6g'
    '+r6Xs5fP}*M+D=ufZD7JuM-Q{)dsucVk-iBmAOaj{+3vQ2`bxoQ<%SpGusbXpv-gI{#nh0Usl<sb#><ejb4ubpL48LF8n+$X9H*2'
    'z3!(0rp{YPmd+CNEsD_%Mj%u^(fBNMiu`8*(ZA0cOwh%3C;Q{v?#R*vCCs0G2G0s0C0pZjw*Ja58Bo9y{Ev*vx;{LjtJ|amX5owf'
    '6v{*7dFA3vi)oa)KZk#0&2SEW<drN#PYq2ddThoLt@c@DrY?i)|LFk4|6#H}sv|AId*dQ8on(YuT$}N{;>Q8`rTmetcVv<`NkXy|'
    'HFh**iQJ<VtlXbV<O#;{H~^rE{Wm6n07N|UZ1QU+qNfic;@Qfn4zsv-J4=;J=RBF(R_4_<O20irzFK926Xz7~h<s)vB!dzvFi$cC'
    'hH*W6ltsjXZA7bo+`jRs$CO?>qr+57qf>qQ1sbyt^$m@Q*5NeqAxcuLDGb(Y*Bw?Xl6F$X+eG|zhtWLmioWg-7V*>Ko|{yIk@s&P'
    ')vzI|S5JZ^UI-F1k|+|eioZ3s&2jEZ6ant&@Ke~lk60Rg9YsF6YkFw%(IzrUG^RVm;|6-<p7c7@vAOY}n<bodIDno~X^*OF9oC_k'
    'b2Z~uyk8p1v|caiZqxz$q(BCsWLccotFKFKr!P;@%loiqa$-+j9mL`c?I7j8<6*pbTq}?g!gM5;J3)yx|KJRU%spV=FkH!|m~sYG'
    'oJ8Nza!_*u{`tYZsa3htZFf41N7{$t`j=2~Uqp8oevtM2Az^i&F$Eo_ei=n8-U3&Nuc0M0U^D`AYj|!l7vrqgTefz5&mStKWh@gO'
    '|ASIg;;^9)4%Kp?g^KK4wF;|5r<%t{5RqWw^*@#1*F)*pOk~&mAx3+Zy43-KAJo!%`ym-pSBnYJ`73;Vt<)09{Z7-a{sF7-MTyuv'
    'd2r;rsjTFXY||hL^8#FY<^RoPwK-Nq(CB30v7wySRQbYHH43^0o6$cZ>DD%a;pJ?j6VoN1wMHZ+x(fnW5L}c3L}>=avb<v$rc?p1'
    'awxbUj^i!9={H*H4d|>c`|#67zvB8wCNw*QRW|rSAAinIhpdaJx%Z%PL&0EZ3c48ANr(<GB6BJMgkO`G#uO7OOIUQ|?67`Z5N87('
    '$tLPSYO8cjGPg*z0lE3G;_ET5;WYDCvAXy{ujre3sGw!@$V!kdLBXCP4pBCV+JlwcO9fV@!oNpw;0mv*a$4u->u;5}a6CP?Uy8CN'
    'WVOE+uMszLlsk(Uq$_TeOg!~b!c<ipTnA7o@fg3!tJw%_m`aaJNn4Z-{0?}yzObZNDDpx@jA8QW6;!T0DIwT&&3OiVbO~uwDS-f|'
    'Arl&1?$*?5fObh+!}Bp+#IBMnr)hhyO4)1R#KFqKmD@5ua}Y1-d^hGzK5)dYCbPCkA*lnr8Uu!BT}zj`W%A(&ZXHD?47$GkS+=c7'
    '(J$dR@a|iD8v{rPu+u@ett^Hpxe7{LZ8#{`E%iE~RY~>HilNwozd=#b-#^Q;_9gg~bppgHa!VcYR)@teA&*|v?tsjYqtQtm_U2cw'
    'T~QD+a{89Bqx2rfKK#2}ef$`}Z2!JH>;ISJrb9=T92h|Qy`4ilx2Hbc_hF*`4k#`7o2KD2W{6w76XC2pj=U!UK-WDpUr}v|g&I*z'
    'v`9nysQ|wDgUzapn2oCWUsAA}{fr?PFPp7lH3oGb#Q?cAA4_HMJdGBH0?;2xbd)_eyr{G83{3LAEaj$(5y@=H!C<=z`ZL*&IQ+dY'
    '<1zqR`d%`a(CC&lv@~>v$IAkl@+yKVL06-&L;EB$%UEf+bbMtcJM$q$6`A~dIL0b|Tpr8~HV|~=%YN)=%nO}sFD@iqI~D*r1HjmK'
    '_Fw59uIQgb$Z`|~NmPI}s4ma^h256kqYtY1at*q}z=|Xxc_oJzI)m3NuJY@b>D}c4Iz(<GGWyz-aO5ufCu%}%6_V`&bV-07-Le%='
    'afx72sh*2Dze)STyg|n_xhTi~MQbyx0vAX(yp|JNfxJK}NuJ5$m{C!TCUmGdE^QYQMM?C-Y!aWj%@aofgZHe}u0Y5GIDb-W$p4=c'
    'qF)z=ookM`F|QFwx$f&qHs=>9h~`Rc*(g6>4P1=BoeZp?!SohF$zIc8o``NtQ^y+^zOi2l?3;vkJ0Nz{8bH}l%1>&Pr4tG-Ct%mG'
    '(QdslJmb0fn7MZkx-pI(`e8oO-|VKCnx%Wb&-Q2-{3Vn*Z=9}veNG(QrqT6Ry?rRqVZ5gwl3*wy7h<BlLe270@6X<7+DFXQ?!>3='
    'hO#yV8NTjv9i-AD1Q?9q(8)VqRx$(h7NVnPsLi2WADQ8*Ai0j%C~=qFgsTCA9#PVo-kAa#E98OCwyX@nWA5jP8Vv^4<@&i4w*f6r'
    '<ENC{POwBIa0qkmb)zfv_vD<>ALgfoLwe0%h5-8?s7BP`4L?f+ak^sf*VuE;d!lHOxDUF<Fth%7eQF=m`b169p7o+{0sub;I9*H6'
    '4!Qv;F~#CS=?7iFzZiVz)PoB#EE%!G;%CL68s-)Wq5k7+2s2SeA}XJ1!N+D4je8Ts%HCxA@(B5dzQe1NvLE=<lz1%Q;D|@az99gP'
    'HNsYS+Br!CofxV>Y9p5E27RPJoq;9o7RaRGF)*+}8>VpGK}W1;(BPO3_`>sE|0*Gds|aIK#Vg|1{Qi_MS)a%V!csk{Xz**9m25mA'
    'qnqxm#iQP%cb={5^&}w?64}SqFe_8r6$p(YU15e>ng`<al#f^ei`)2iq^oKnNe*e1q7G|A>N1rIT@m_@ccLESF9^?%t7z_s3h<Qj'
    '+u|P?#0WcpLnRAPx7(}?4{g?fKPDu*46@T8&0;lCCj1J7Rb8xl56?D~VI5<xi<(*-RZr~aHy{WQFq`)*&<y&G#eHBUir_rLGX_@3'
    'Py%x8PJQiwJgbUt6f8wM@t}Y;{0E5JsTWzb*CSeCed%vXF8tomkDPN=D$V$n+NTPod5uIOz6quz&38k{=Xwcm6b<gB-m&R>xncur'
    'tzDMln>b9g%vIgGY#!(yqRlFI59mPUpPOO^Nl&4_=+aB6+R5NS_xU-M&N}lu{N+c&*LT72+}Vn13-tOSodxP3+IP%x>a7yMbFuI>'
    'T0pyG_rDPkL4BuOWlmxH+YIL8!J+}4iXO~+Owc2~!!SOf<$(BrVM+<dZ6B0kK^T6CYELRW`PH^XJ*12Ua_8SqsaRW+svijHL;ue!'
    'Z*MWG0309Zb;=MQn21~}8N&@04ruWlbYH2_()9xqA>#kBz=~8jk0^}#UV!b%dM$^7&h!pNj8<2jJ!Pfg<$jDE%-<j&L!c?K`cjm;'
    'Y62u-gY|z6m{~Rvi;OXQ;osLn6>cDl6vW9SA7S#nobj*K1a|B#qv$yIgykW}xH@~vEiu-~<^HFmhsyU43s_x>c;+HemZ)(Z*Uy-5'
    'M4tN`#T}aA8)0ioxJBPFJFOesO@I#l)N}_V6uk~7*OIvZt?Zz&pbVky`_*SZH}zR7D0ITB4I2oiJ%4>il`3p1<u##G^pgLl1eiN5'
    'Fl>ulw%=&27X#d-7%j+AeX0Q>TI(djNHY^CQn}U05aPIACuNWF1hz6J$MNwe<Q%HJtJcnK2Nr56-eQ&#JofaGNO0Pq+y#OJ5I80b'
    'zv?Qwi!&O12_#$YzvD4XBg$N0VPR%Z7`0Wk?n+@pGz3!tnI1#qS#xd9FYg_=mCEzG??8S=TDARLh`g<eL8q&X%m^V8@t%VG*3-86'
    'CmUhsp4sO{MH7is-IHa|v4oR$0hk%Q1?utnaUa!{QrZF>pimXmv~CV1fF{Cj`j|1JbrrK8KUhiqF=dyKfe#4|5wS&IXg9K|W!7|W'
    'QIov_b@WjGJ&&dR0s{Viu$+LtSWtMA&s0x4`4I>Je&$>Z6a~*U-Mk|ob%_EjT=;F){7nZKy&NrXHT&P9@!#lF0<kQZj1kY#=-a-l'
    '#Z+bUB~v?B_jAmvdhKvyaL_*WsPifc!X2L^X#@^UCPghLcNF5MDb|nbm0*M}CnoqgSU+PXJT~o9s{1aFJ-4OCtsV$Ry;svOT9LLL'
    'a5WL&?ZcLiJfi%AQ80?3a=itbr*v+WZUbh<|1clXTS|2SoLywy`Pxb&NTh(3$mhX62%)_5dkvGhrOyCgJS}u?P#-F)a_YR7RMNoT'
    'y95u;=|DCtHHy)Qzr;OU@GTMfuz@INwe(;^V(miOoL-b_IFC2C^;Fpv>0*~p8BQq+XkylVMRw&d`~f+#vu!2Xeb)tHz&r4mP7IHw'
    'ga60Jd~5x?ki2B+rA}Y<sEM&d`zQ0KgP=*VQtUnmKpTIZjAZyNA|A~3Nng^kH{;h1rnwXcx1Z0FwsEXqi*{E+7ukTJ^sycoW{F+^'
    'AulLJ)*^0xKV8GkkrHS0d;1=kq?3vLG50wF2GLss1My)XKo5{p2-wB8AUestUbAe$&QUREA_#R}b1q~}GOT&)t{Y*aROknEJKk`-'
    'Zl?H}`I>wIHRK`^Z`MW6^cQ7|xW4?T$~8ElU9bN38|T5c3{4<W`#E?pgAu^#({vf(;se|C#ve(q9XSHiOig;;0>n!4&Y?>`5-d3T'
    'jRwioNJy^Gy{aoB8zW0dAZKiF-`fY&@pN7VaP%65RJImeR`6zQvJZCL#EQW*((Ku#AC|{v(15c^?>Ja`%uJ$E@gJa#-N|k^>_T+('
    'Yj^IFjs)lGs>(iftaI9tHowNr_bZV~ASZRtW`T5uh&28tJk~}-v}glRM_e($R()r*5M-PB4dr@dqe41w(xd&`ZnKTz%<kjC=sMhk'
    'nQ1QKI#}W1z?aA51t3Nsa4zzxgzQ}67TsHVCA(V9mAn42=8JPW5f3qwYW)*kufvN`!C}Da`#>g>x6E}bYMB&<hfPwKaK5<HE5Iar'
    'k`tZ@F#h#DH<QrRbLe?8%onPT>R7e&W#?2P;uX7Zok!N!!f1g)f800(lr+&{{buVGT4~6I^$QtXg6u5--k-*Zf)2NKAqM%Nkih#O'
    'CK)15hR~WL`<+=c2|u;G;dXZV$&{G~eP~9nM!(x;0?)xc<oe}iMvJe$Gm@5#TVYhlaK0AXoRkXs$&AwF*V%Fidv&}9!E9{dB6C6Q'
    'J$B&y0T}sw!KSFVaFZ~x&Mp@>EP~8!`ieDZ32g|ZD$Zs`+0cT^ss?qkNQ?ULX@dSXI1V=v5kdUBa#Ws=NK;#K3Gccv$%-sy0=lN_'
    'G$D$it^##g|1xHQlqXShB0qbzK2lwI`G|a*%Gv{Lrd*XD4KPUyAF@+boxh!zOO2^aI9EdV>~Sbdv9j~Q2ajSuORuB_&M(gB&1GM6'
    'zk3FP<&+@VLP9oPp-jx(<qeebrW+C!>I?8sx4fK_ecUWTlcNU<*23hD33t&24tY?g*?Qeg4Di+xWKI9KXOzX$1J5f`o~EB;pzF40'
    'oln|cd7OpXlEW|+GEap4AxHx#$RU*(-!(GW<@I1{uf)-FA_q4mO<)oUHKrC&|J^e;?H^!+1OPs!S!Qr#-JCTYB9%DG61EUUwUl>q'
    'XAR6mQwtg7pkNyO?Ev<E8Yrh-k}a(tb7KgrfM0OF#)`}zVSf(W{#jZ0o{Ri=F3aH)>IFh3+CD*pifNPr`$`kawRJ@#DjMYU=Hp3p'
    'MpA_=1HxA4qw}FY{w)|PSi3z{^*dIe;LM}xGfC%4+L}hx4^!x?hJJRNR9&mBrz~Q&^kVESf?rrrpmM8#G_`$*aLOwG>7dGQ6DkXg'
    'I>Q@GZsiV8zj~DCN{>Q+Y5IYRLG`4fxA-*aKBwVeKaKsU%4j!`(?3EVJ3-k!p)ov&X&5kseCY4KF&Fq8Vrp=ml=Vd)z}I(X1929Z'
    'wVAP>bkFu6-d-+xalLdJcb`7HS-oh^Y)J6;<xxHVQYEl|C)wKVhxd7PvP7R(H%SiIly%zHI2B5cNrxO5*FR)nj2%k#jkjbhJUA6S'
    '|B|hQWS|gfZ(Bpybiu$vJ!^7@AC=PC6<8b>&f&*}%BH}*<xj-5)iaEGDOiyIVv9W?!g?f$y$E{a$<bbiq?&tqp$vI*n`nt}hUuI5'
    ';0qiZ1EQQ4g?esdfya;API66rKhC#%4{0@}f`)l6c}_~Kh#FrQh&x_RfS-Q9lZSAeDLr_X!K{1F{s*sByWml(oq=kVJQZO2XO%d5'
    'IwYom<PQHvsD~*cXT_}*U^s@}lxtbDtJ?5+E%U%Fgq~2;BHjC`O#3BjW$}8NIuR}@3^3P4f{3wCEQ2l?^jjmlalgH&nfbTtRu#iG'
    'Yv~zTgw1#P#w#XAm`WP8I6znY!VT~3f$HLRQXqMy7{WndoZZ6)=GV7X##Ti01?l|j<QxNS=Q_O0jd6Xs!2{!ln`>5k!h;14iT#rJ'
    '+CV+lQbmPJ3`tvwzgFhtCdqe2N<7EGp(`II;YoMW07}phrc;_us|{Dq_TF#NHLO<w9n=GFt2NY-?V3k@N0TMyvenP3wsn8FIic^w'
    'dHsy}PPtRos~Py?o%BqJf7oodtb}ovc|IfRtmcRmrGmq9(&ON;+I7|yX)rRq<_MoTXfFT5ZdBA=c*?=`O`lH76KL04>N`8A*%Zg;'
    'CW7H02bm+8+06gdB0JKF{aAJmYO9GhMC~i%AcdMoGC5T*&-qj*D{hU;X;HEqd*ZJklqx97H;x#Og$hWLUPvGw>#1iQW-~Li->(9<'
    '$OF?6be~Xn0$Mg~@03%}!_OveRmx*RxHi&jdD=FMfO&ag*-C+P!MQz*0t1*Ak@P=w3;$3xRZP&H!POma3%=g{pPpEt;3EH51MLJA'
    'zs4<o1$$y*vD)mNINMx-@Y==5&Dj*8eti#2275@TO$H-tL#UU=DZZPs)Gf_bqsC5b-n7E+lF@W0EOFf?r(0kUs65w(@C>o0LD>F;'
    'F6e6sh>D<RB8J0l)L%l(X1VlHRrS?It*l6mFj~97da#z_hMK4GHnCamj7Z9#)NGA@;Li-2)uh46ZZO-Un1-b>1BNyHkP^|OE{xkI'
    '0(%Yos8YQ}ly@7R&0U633$Z;%h8<(aSs{E1E{U(=X?3Fo6MnTz-Wa%gW;bONi+v=!acOsYJ1&b9Q<Q3fx#m*v2X$RJbO-X9;wa$b'
    'nD3Rc;A)=?nMTTRRDA}VX=Hi;QXsNB19OGJT6S>0c}H0M7^;$JB-t(+KOrk<m4f+XEgupy!G`5er7a!IaWxdTG#|d-B^k&Kn=mxo'
    'Far3P;VnSqWVc9Q1&c$iD|I`Kwa7OLbRQ_2IGDqkZZgN4u85N|wI+VI26`Xw<-I+VDW?pPD#cn@{vlIWNG_%~H+R>3WMi9d9LO*!'
    'qr;C^&5p&AnDso?9c;HBX}Ox^(51}2-ez>~e41?X^V1nto4Z)EXs|7r6dpn3d~TwU_O<IEFzBNWJ-DAfMdWm3Aaj5itRd0VycfLX'
    'x3?2BG`@mmcz!$8s<H~ukFGTFOOhxaOu~-XU7N@T=euA`Q_!uovX}90Ss&qHpBB$c9Yk6mi%Eo;jGP=|7Aec>(PY{{drmj=sawm#'
    'QOGTh|4F#6H{2+yQ?XcO$<(ks^iRR_FfOP_P!d=LMxwxlg$4*B;Nnu7alD@}#_sHMhzvyFmj-?%FLLxotu(CM06Z@!=ds>x2m?ya'
    'oRBDiKD@RR5@V6e<V$HlT;m`NmvTxyMcGY^O;1rQ<OK^bft2}<cgzwD?KR$~{-z+8@Z10Ro3sjbG@KRAk~nd!I#}0J<__j~cz{pS'
    '71y|zysa>+gz-gvor7kcg!Ym?`Z@xypk(UOKUdeB3K8zwOoVv@=ihPgO2*Py!;84GaCxy}&qLr42&_!LQKi!X*gcu{`|QPVrKuVo'
    '<u^H5@w|Kr(Hi_vPbBSG{H3}E_61MhI$wmFG!>gj4nXMHQ#)<kbjiZmfc51b7jFTJy|iZI3{Ou;1%es34D@%0T$XM^uUZ0Uz{c&4'
    '#<$4cip!%Va<d&E%FN$wDZiu8S&R)cgzBQECZ>js&!s87)y~(r9P^1isvvyYpyVP52Ri)iFj_|)^p}O>Bz?LLk3!&J+z}D09L3;L'
    'M$1~+a0+kAOI`iM-wz~}X-Vj6fjg0oOoC1&haV;mSJ0FxB+`kgi8wK#6~GCs4bimMf}kwcR=8F{7c*=+w1=rHLZ$8>;VlTsWe2dy'
    '_J8^**Ao#6Prat$rL35f1f_&is)UQ52;C6}-J)XRlM%-GiDnchPR)mV0^v*hIwh-1SdG|;^{TkeY2JF8prl>_727HW9j0AfezJ!1'
    't(R43yf3b0Yn5URdJDQ_QgduzO~*{L)16;vOdB1U4g6r$jiCL97<8l}6;gFw{FGkYQ!4<Dkq(M}jve?*XoM(#7rAqYgxJ&@j{M5G'
    'tYN>c5?Q1HWw`jleVPnm^{E(adU+;-205adW8^v7#YbT8iTxpsAJ&?Hr6JaGx?@lAleuyW@gdX7to9sKyy+v*R>xIre5}OMfw4s<'
    'Lu+qWS6@rwgySH+y+*V^vi|8(Qslw?NgsmFQRt8Q;>hmz_U4rvfl1Ayg^n8zhyf??cKc5yE=<)8VI=AC2W}ZekQIEdR5`-NtH>X='
    '3?Aimn>qIP*DIZ5zmX59#|tv|)M{y6Q+li<VeE4bwl+E`pKiZhm}fwR@dM>{h0@|uepoJiv8;G^=Nrdv8)!+ab1@~jaIf}AX|4i-'
    '(iy#;SY<@DUY>cK<PZO~5$Tyaekn=HuD*V%ok=_G<fW?lxW~4dvN$(Ak2fCq=XmE|jeV*Rnby(_jl6MSISnvj>8@LJ9(-VT@j%@x'
    'nj1w~Yd{oH$v_L)@yNn{np!*-`Ru3RlvOv@6#>6}Z+GhtY*16O9i-sul*Ojb?64kA78jrM89zqy{tMVKRC6%kHjA*Kl6J$$h#a#A'
    '?c3UD=7o!UP$fj>Q=ES@oIWf4YFzKMkNqJ)sTpM6>1HjKQzm{>nvS8y{0F{c)WZGSI5RvP5qHkYB`(!GkXRa)Wj-0xx}4_lV-j@='
    'yt?!7kKNZWZ0jtP&r1pX|MK_n*!Eh>d1NysR9#hT#E38l3fF-2Od)hW8hln>a&ktw&c%n2p-D_w?;~5_D^dFObxsCiyCj>lKNr7C'
    'VF4{SE3tKt>XIAjdlrmSApZ%d-PJ6!N(bTQ<AuAwK+J$9`crZ}^52()4%f3hSm&-yX)|n1_xY$t2&SeqLg20deCX0!>rF7k+@~br'
    'G2U<R#6b_&ja4LnR^Roy4qxWC$J^-|cb%tuTmi=aoORT%&b}{#bLfT`vd<YV(^*Fn1VKGfDoiMpMqArfaoh>!1ASOs?o#3a(&+8Z'
    'GJay@7!mbEeDIz1KFhVBh({#b4(f(|?p*2u$c1DO3Ymr^D&ytuS6x^VxZqFkGpY`pDgpX69aNzJ`Jdtmbsni>J@&*waiFH^)}f+S'
    '^z6%_j5UdB)#uhcbwZl15plFhy}#XBIV$rfLj`p1niff!=UxT|;h0A8JoGOY#N#GmI^Lv}c6=uDBw;1f<)ImU`p!DLdW;vdTAe+2'
    'k?&D1%3GO}Jm7B3TjXONaA^;>F!2b<FNn54q3(=$2BLOaYzzL7cZ(+H2@<41oz&EII)M)Qa;wfKjg-l^5R=`XG8%dcy=D%%)$vun'
    'ZXs_aynCkkvOlH?-^t_ts3?_c-z;1?`&h)d>@`9*F4;MI+n27>{AOHqW~?BHxmM6z7qjrt9;{pGav*`c71SGLDDoNXVEWs0YEv*6'
    'pn-(rp$Un#%g8USOC3x2sa|%x6}}AE%zbd+;5VI^A|alB#z-*kdhD#2HpXXVf{z|ogqE#NMCD9L={28gX~fT~TDuE@h2cp-e8H%='
    '*ziv06xQem@Ef3ZB`>dJtEUK3axUPYDY}rCu>4h~lq+^s!mg;YtK!y<9JW)Nb7U3+_i0)hdl?7<5tMU?obI#!zkU<YdC8>4)9f{`'
    'TIkYIX73|x9>I&@*wNNxTd~{AZXoUlP~==K#IXV%EB<<2y%$&<h@v+VC3$0e;UXQH4w1~Ak4ed_`!8D%^GDJN)JO4oB{9sKJ6FI<'
    'z%Qjjs%xqsxkFju$Jc)i#b5F4WVKHJGaLe$V)!pn8d1qC2e$UFY7h97YV^UoIWiS@23Rg2hbt>}Hz!>L(H`O#gn9~<8|V5*2M~aG'
    '3uSS(rHVlI`k5g+!5!!|6LD~iUoDQydPC|$_w(DdHq2sZ^kQnm;W!33(Atjg_PKq7y?OB>l_wd71-$-SL<`eEUC_15_yH~oHx)y('
    '*P=@u0!o|^rLxr`-zOmvY}b<)5^s>6-H^lsPdCRvzl%gH;kUHPnBT=%1(S*PkmGYe7T>+0-UhskT8}c;lS|qGxaiCQuAgw<n#`eA'
    '(xPCu8Q|#rknURt0MLHFshn$EEOvaaFO8U|!nDkLJ;bzysz4M4V;bj_dsnJbFzDdFVPrC^fmdX`nmFHz`v^BY|3>{|Sr>~$BDOd+'
    'pessX4r4PpuZU*$`75D?YxN!^Wew<Wkms2W0|sj4$sulKMyPlliT!P-b(J;K*Y=v3Ca9xaVOAW@0+@ic%$$a}xDD3Uweu%{_dzE>'
    'g#@2A<2c0hVP>XV6S&Y}lB8JFkzF4fOyte){gR;Bs~(;zaW=F};v7Xav|~g>Fuer$uF1%8+m*@Z*L^>IFjoeyz%Bc>RQ$ULKbK75'
    '+w(~e3N^3id5C<^%6=4wXP)|X{r(-KBBY*Q>eaC<+rJF3|KG$vtc!+|(7WP!0GYU$_npodF3Y}bR3fqD&WN7Hce`>9_W`e^2+9pX'
    'Zxa9z`N_T1yh$2Gjf46P?ib2;X9gc*L4v435x+L4%`QbWy3WH=+y0S(d7JTIA4aG|&%ow1%WOFYH`lTPywA!G{-62vKws0t3W{ho'
    'q8-Y=VXJ>~1v^s_^@7fK9-r#MZ!&o?@hKlP2e>%r8C`s<f}-c;k=zRw?AuS8pN73(Z)N+1u@;PL{?&7V#?$JThH(=UARQtHm-3z0'
    'vh(+4ha1hr7khmY0vs5_URyO;QDKjz)S?9L2<CG?`K>4yA05vnD{nzu7hEb+2?x-cEv1shBVZ7lrCTkevMh|U$e#YJQPmR$@5!?1'
    'Z3;Z5_Du}pn_$jQHIadQncxU~qzNp!K#;vWVj|={?wK@U|NpJ8sC2K5eV;Z;!}>m1?I@5m8d7{W19YZ2!*2`^KKRNuK3IfEw(BkD'
    'EWi`d#A*mPU0hPLd-~bW<9+jG?#wY)?2t?Y!>#ILMa(aHGMZa|oqigw_^;STqBtNX(!Fc!I+<X<eN^WG4c6^Q|Kgu;0@hcF9C%38'
    'so%H4LFQ=%ARRlNS6X}<>ZBHJI1R2cYzK1Oxvjd~I09&ZnBS2Gie7Vx%=}hCHzB-j>4en6z3;=e{AizHg$Qp5)mi&g-b7An+Y%Pr'
    ')q%wTg(6Lm6zF~Nj#e!vq87zi=D8!HD7fR-G*3=d1%!IP6Gu<nF(S4qXD&Uf8yT<FRFEjghfM7Y0B9a*t*MxTNFwR!y+O6cu@|F~'
    'M55;H_snn_DCR7E93>FK;({!s2T1#BZygUuds=D^BV!|7l=ecpJk*-;cJF_Lcn|n-2?~axk^uj$!tx@HWbVY6EPh24_@+5t?6h7-'
    'p_m#%7JXeUX{fS#IU%~VbN#Qj4$4}5OnoNuGSobnTjq!t^q(u&EWId@_Zx*Eb@d1of(E3e#NjQ1YZK({KMU*}bfcp>De)irLXA_&'
    '?YdBD`0OZAIviiJxHquzr16<QTfO>|racl@WBg~qDb0U&4v$n1i$v_UziNGW-vPV37B(LuBj4rS6;*~{kDm7WRgX|Tcb-f{Ali5k'
    'U+c0)^U(xf=kjh@49;HuRwEyBQ{zWdN^YuKny>^a3B1h;J?v~auDKP1XAmEaTg0(9^$Qleq>!;~2K_klSsRC<+A$+D3A-M8iTEdR'
    'dzEp*a^VmeerITl)fkbZ^(;Ja3IN9Fy_v4aMT>$5TX5v-&fxqv#r~C%uBPm(ygn+j(^Od%*XW`-$4KRMWG3JyYf65m&eEd?O0&$u'
    'O}|@IPw65+SHdYx2%kVBULUUaww2kQ&Rw=c?0>B9K3wW80}MD=@=X~bb#)y#eEC1*on}Ih;*2S439g{&S!}R>&i)F;<4I_bY>Ap0'
    'pxb%KEBnAE=4qp{em~_O^4)1>*bJD2o)c4MHDZv6867m~Oyu^JcX3@^jyo$e%vVSm?1f!28i^|MmuhT1b!2be0GH<u!x?&Xl2wI!'
    'cSb>ov*8gO3TQHz(BI*72Xnv3?tPuyJzGnD-P^kJ0#<4>FZ%|bT)XH(fWnT&(UcUhPf65y={*XiPI^SlU+Z_aaQWKsbh8YDw!E%M'
    '=M*#7x7a?KDo2$@ZD_$$f4Y!qle)PT%JW<?Q)T8jBO^<)P_!|ARxib~;w*k=#Wt{3M1I?`?FFfmb4-;VY(vQ`6<Ubo68T$;<_(ys'
    'JRw`4-C?91(}W#1xa*jUsexM8<p^sQvD&?zjhi@K1wG+}Os_ThN`|M3YIUlck~}e(-|3!^0@S2Q3SVlI0x&igz4Ks~-*CKKhkBAo'
    '_~Xf*cuZ6XRQ-IcZm=+UbCIK12zjMUMc*IPzE)MTX|4m+_mfk3g3=4fd-Njb!6`lWLQgAnIO*5Umtg3CSIaEN{3i5)7KJQC+iRz1'
    '@SSY(e4LUhAm}BC3Qb90T_?{pKoHX?Q`{G*eOI8#_t^+8E2`FJm_$g^>j&iw)Ey9?Fkd=lwPSW%lgu{%vI@=dVl(GUCyE=x7lbT{'
    'E&}WS2LDN?>j4^-cKcnMk_<BMMi{sxS&X^wHm@-TBwX8wL}n8w8%y*aYrlAg$4+&~H=6$4@VtP|9+3w5P1J=@olRp1nWkSBU;^?i'
    'JsCh6xZ9#czfKl|g9A>Ma>6wsT6Nw#m4ii6X@tBb|7TtB!KU|%ctiCBXNs7JZ!LG>>qWO>IN5rW5{_~j;Kniu)e0`c{4C1nPTfg}'
    '`MaGrqLd3&bL@oTeuf6#VWiSl?I^~WGI|HW*T*CS<Iu9Er71Hs4j|YXBkLUhDXCBX@Jp$jZsod{rvX+8HE44}T&b1_KZ07$YP5uq'
    'ERUUNhR;n%DkT>iV)VGkA!86GwgYbD@IFR6Sr7zu6c<4q^8w6qDTz1KJ$j}%#+m9*2~%9k5Aa1Th)upGDU16$Dc*`gJ~p{r;4%Fe'
    '2SV}=Ntmzfvy|XjYO}I-r^+_127P|?T{tUY`0YT|6W>u~NWQPj-^MxB`>AY!Wyv6^yx_e#A&*Xp8oUdyx011BVqFRQD80ZU?}`@q'
    'hjV;I$cN&W$l8rS;tx!al;m+zMDAhSY*(e51qoR`3ZyJ*`fYm!x<Sfl%V%aUM?)g+X?`;qi~~|>)K^5defin({d-GgS=b-SmkWkr'
    '(it-B?w@AOH@Q0^gB~22kul45WaDTXYT^Beq;kW2H$NVK^fo)4`YB;T(03ozm}G*^xRhXXX`PnJSVWkTEv?g^*N`|<p~9?ppD-rc'
    'i$A`4CWJ4Q1*M_xE}e#JrkgHlC+{dAaHLDZ9K9~V-Kq7!xxn24aZO}cZ`Jz|>_l?5J1YTEXj|Zr*w`P8pJ4K^T5!x=R;1ep+?EWb'
    '9hg45>U>>530hb<e#p?1L1#hUFH}TE0vLK=;)*c&!oMTsv5a5`pxyMos#e&RdXDhw*gQ45lj93Q#G+}QvbGH-*aJJOF1rxq2nyP!'
    'kBoBKFRoY8PTBS}&9@iR)YmiU>s39@;Wz5eYc~}H%BIOr88jw|y=gTaCv^A0i_E5%Ww?Y<ZWd$q37bu|JeVyGF(1*^R7LaQEsbr1'
    'mu7T3tD$n9N|l4{&Ou`Ltn}K0%zXgF_ZnQ($qQd|e$@AF)PXD4FljuU8r^wt0*0wl=EOqLj6aXZYnP1g#({oA;k)UW4?^XcX!9SM'
    'P%(OSX37hFmC7c$qxk17n`D0HX;-g&h(*67MaQIOsV#{m*l&>H7yB)nrjOpVn+OBarEOF6568aT2K%!mY7w~ica}4nQbc-A4R4N3'
    'yEhd733fn(vCl6AYAVY-&1xkog=TICdNg0U?%PTor2~~FC&9oz;>L1wrUIBOKvYY2hF>BNxg9IKaVrW~$H;L8@OxwZjJLXAK!_&$'
    '@woy3X`7!iiU&k$Nvz$GTlu!l6-;qfRIJ0756y)Nbf*rm_=8ta7VD9Fhp$tYCJ-cITLQesL5(G^-mQqBF7YIIf@!t!pe~1M9sMTA'
    'YR>1l;tD>@Rqt8^2Bx8!s#707xq>z0N~Sy6|Ab?R5xf{G-lA~RRf2X4g6|4OFUp!IwQX%not+X)uZ5|lJ6U%TkWjg-v&ynus;Owb'
    'idLH{1cD`nzVS_s09Mm<nWny8TQRajc;mV{H5QXg`3(0cthi*}V5&I#Nh{qr{_1S_a)XQtV*hwb1F$A68S!pd8}cLa%`i$%Tpsy8'
    'Oag7KHl`q{njjIwQ=TsgsTWjol|PzAbth&r=IXVK4s2%L&ls5{W|-l+kMr7PJT?}OOV?;V(XrZfO-S$6qQ?K!XhFaAm{V{s6b;_O'
    '@AEN!<NO0iMkcr^m>k;=Gdm3kanSF$KSPKp!vFTctrJN&<OwU(%7!wy4*+vs6Su1Di>Z=N6D@X>F}OZ9q16GwF;J!;SPvM2X??c-'
    'dB8cb{JT;#kMK6Hqbxp8DlzeL=7%4e?8@KB#g7)G6z!pdfBKqqkxN8iV<SmY!?SWUYXvSV_}gqY)Y#j3sbDMX_hAFb9|kH%9s-j('
    'NymKaGmMo2p_&l+oy5jDl<5wruN4l{=1#A`u`-`lKU}rxq%|2g8dyRxeT+c&X-4(Ezf`SZS_?O}K<unc6yh8CSZ0$4E>iqEnVB^r'
    'nK1&bir5C?7Bk>z?f?ZHE8i&m440hJM1U^B;Zd6TTW+ZMPkmnJgkq${PCemEdn&}49u<grO`4Nao#l*pY%q~tNS~&(fKe|KM?qgY'
    '?)D^RBNh<VH;BoKI|Rk=bGVCy!ZhMJS%c&0hb#0M6yYp_UFLS1ioo?N<i^jSH2PGtu})7LMPN};hY}DVNgR(#_<CCm8MK4sOHjka'
    'oi!L;8>m4PVDV|obtvhs`xP9@t@NzS`jbNJw2;R|5Z1UpFQ3Cq@V^H=Td27y?&U&(5!_095m|vT{*(k<f71UfbnsZ>KItH1z;Ha7'
    '=dMxWmmqQwLIm@1%Ft0;GpJdDDA0#8$j)0>0rR1?zDc7CFL}CPNBV697l(gDsDdp3^B9{q`qJO>IHy^>+6zmwtk`I$gmDzc$UByB'
    'VgDu+BLjkF)@&Y>04gD=Wi6Y+xbI?8m*NGNLK*623`<aA>zy!a3n%EpZh#Lwt`b%PGOgUU=n_(+N_6V-ek#z-Hmyz<mV2s)TU)W4'
    'E$Y;Pm63A+u~XWbiZ3;3_A?3Ln~DXo5t_F0*IHs48&0SFK<{ZKaQ9j!jv^A2uT(HQ&W$eAWtl+6R`|2$=N+kJPsuD1BqL_lagI}g'
    'kQO-6%-j+)bfh63sOolvHxA%ZieI5-v0O^`d<>f(Y)swUMx66xQKwZgp#T<;bTuy6vT)Ul@Q#TJX#D4WX%FT!2@+teb_^gy@v*RP'
    'OM(*DigrodYhWa$FD(ic<ohrszL8lV!|K)AJ^8$?p!Zeg@8Ou)Kwz3W35v<y^II({$oExd=~RkMl_XDEyeqE}tT9N~SX6}GhiZVh'
    'f6JD@mfcfa9yZxEIz6b8(G_C!k*KY(@J_Z2iak#S$0X!&^wG%aaU)_p<j1u@f4!)@T51h~S4dZLaBJo5rW{TyKBS?on?U@Ukp~3K'
    'c!%w*Lwoa~u*kHDJ$Xqaw>pf&;Y%25*&(I*Nxq+lt<|mCKwvP6gqUsKY-q$g-z{<H&g3K?k^*$K^V!CqsV4p7!E1##wf^ZwlKH}f'
    '51n~g%r+614RezQyCFoX3LFO0o|Gs?DyoG`fMCQDKYoPgfW+(}lcdQDYcMtZim`On%{7+5EJXMesPpL52>FU>gthI&vu^*fcB7EN'
    '39aa45y<l?5%G*_mmsBu0p&4^i*`vz(mDIMq<M!Rsf4Pjd2Ikch7fn8IKbu)KnHWgYViL?5tjHuK@A<g$DSCj4zvjI&by8x3<_xa'
    'xXyY+665WdiRLO!JzZkkkHpb@$Lzn+f==o%5_PlHO?&jCK8P>w9s24zR#wt|8}(BjqA|qTdtAaxeBCXb8#G%ekLFn!s*WcYzk3jR'
    'K*JaWcD|skle9*cON^SQBJik|e2vU<U%2u=rV)dj92L^Qr2u9vrrx2nOZ+7xNOTa|>}_J#J>a2`_0S=HHE9U5KOXH&Jee`}eL6ow'
    'WD&Elc(0k-hz4kK<0i`o0k3XrjfU7!g`>*Sx@^D6i;w7m0{P!K?a1W?N`s}{@6=G@LIjQF26RDlN9I6*4khA7D0_>$y&$Du#+d6f'
    'Vf$%7lb$#%F#4N^qy1m=#A+z7NSGDIMkF2W)#MJ_*&xq%^`|RdA2N2)g<=ilB<B<?@Tk^8?Z-?{-<OP{r#lm$xqoK>l5#UvM2CzB'
    'y$vb!E2XYXy1;K{c&GGIDDsHLM2M2q@D@G4a<T!H$HY2U?9_z}wv<t(oLlW0=E=(2KACL}e@u@_aF1=rs#}I;<lFL+r8VG*oq=?G'
    '3aalYg!jQFSK~b2R$^n=d!LLJi$RWUc!9qn+UB=S9MR5?zpl-^y^A1IX!1gha76HMJRKo1Ei*OAaE>N<&$i#pmD75(wM_3BcCs^>'
    'GB^<)z|CrgJMw|aPP4{G)MkZY_f;sm1IgEGo}C^4+J4y^o)_#{9x9|_kF_D>RTR(`<*NLk<WL7wykj|h93Z^IjH=aY6ykvP@*svc'
    '%z>{mPE#h7>`h`+0lJNew_{tR5_SC(F?1;{|MF^+CAVfZ9__EG_5E12vMVqc;?WBqIc(*LOURZXq2Eh^yKvEcehHQu72xe6B^drj'
    'qCpF%=T;MT6$0Ao9m>0v$b<7qz?vvr7&SdhGJ{ckvRiM)xj>CU$lM91B)U(*`%M9BR^>-kqRm9b==jP!S(>RTZjv5%OpG|U<->rN'
    '-^D^iK_~-b)3DdQG;{mooV){cR!j1k4Q@OiSgZ@1SHCq6`xNRC@YII{$}Tv?=-dR`MfD#$`r-&iN?ia@mt2dT|4*?k<`_cv!YB8A'
    '4YwnK6YPaf1L_Pzew8M~0aO+fh-6zH1D-CeDOmzNR<=N9Nip^Vj+B)}^rA4C9ZzWo*J?i6S&DQ{a8($JVa6S;U@%g=*kjfWX{#Ex'
    '1(n`5O=~7eBVD?DeKp~xg6k{e8b=~jtvuB3Ne(Frv8cMZ3}dTSI;^OB)sIZpliRy6<+Gx3$3f`v%Ph<Q=XP7YP(0~~Tc0Oye;qLR'
    '4vikTeT+lj&x-^b`n5c(geEG%iLlJI{}r7N0bU7k>v^)C9q%NYMYb$|g#3w?5LHjPM6IXCf{C9NGIM(NuKx-_W88RwroXEs258ex'
    'm@aa4)eN(y+%*6;g_Zph6)mY18B%7BQczfYR??G5-#KV)uFh?$yzSxF4+f~8UxPKw8EUIVq3xtlz}8(XM-_7F`MxRL=9k{b%~7ui'
    '0Z)pWni!$P3C#(sokc6kE)l=MbG?qf^iJ+laB4uK3|4i3l|XryGZu!1TFUbY<<rWi#$h)X3wN8U9Eu-@@q6%yAlQpvpK7BSSt!v0'
    '>+>&ZQSSQFH-B#%`U$Ly*rafLug-T6Pbc5Xhb$iKy9qzPxhSpxJ00ToJx9YZW7iifR;aF$GF?LqonXi+xW~~vDSKr48Z<50Iypb>'
    '{4DkwZMWm$1N99^ZSHBQWfH-3oPJ+z8Pbm-VUSB54wfqIH2ImG>N+~&jgYf+hI+O#?V%f?2SxZNN*5F%wP~`t-=m;tG8d5!I4@8G'
    '!ApBtSbyOPm-Ft0P_xfOW4g_5eqwk1O{km>1{g7(V=r%-fM**WVu)rj@Ip$T4pDz&Z+=yQjh;B+f{}&vyopWHU9E{cg*ad+Fx5_g'
    'L}LJi`3AQ{s0uSa9n^y?1w$GG0xY-yud;0FVE@=E5oEpRVuo3%*xc_co252aCoBL)k<03UL|@c7ktY9zz<vBGMD8dnV%(m_hU!|5'
    'j*O%`_UIPgSHdkH1*@9vBW)xaXVDQR{bvp-IjZ6xV+HrjH&02Dkza*AiUYSn5lOlTt45}f=(I6Xy~wVm<Rja#au+6lWb|&HK~{fA'
    's_K9*;92c&q~<|uV0_Whq49pT^X$NBTLO2t=0b5_mb>wWHx=0?K`DEgAH+&h-LQpMNm>jcv%j4)NW%=gq;%hy{DmA4c$b2#t9k8v'
    'rZ{U^kJBCuzYFhL&ENxd*iF<>UDV{&r+UzjDDnI1MuYicH<Lk-*Mzb5B?z+#4gKmy_seI3=0zRDJy-Xq$qt%)Qt@pw?GM8tez|Mi'
    'Vxi!kyjwZ`zN@_f$pDgzkzQ0twd<h9r5?CyotgCO)}Wx>xDg5#y>ciY_*?%!zZcK7sz<2z>a8S!Sd^JVeBo3QyVew#%+2tcY9Cv_'
    'XYfNn`1=*fw%M#UCw)?0E1$5G+nXxkwpSrR1||rZgZN1^BT5;v2+YH|N=pZAQA<)+tFa7M=3|Xx(MG#dUp>_bMfx86byuiqnuPp2'
    'Cyr5Nydt#?!xgT)wm->MA<GeFoc{l_*{|r4AX)pPPe+zC&d@59MJrNjxgC`xbAf3Fyt3v%?%C7w3921j#do{>a}6at$KZws$#0|~'
    '633QjFSE$-tnO1`lcG7&z5SbSl8(@R+<_+b)(47O1<xdkO@#*+OqGZKI+@iI;A%+q%Laz(O~+_yaL|62BPpF!f1#cl0hg?^v0f>b'
    'SN6DI2K9ozdd8id$Klcs9!};o@iA!JJqUE;r{32$$=4KsI@*ueWXozQ%TOk&9TbZT@tdoD{{P<_pTq-2PTyFiu-A<HSEhclj&~7O'
    'L8TJ}#y`&o3y}}yz9;gaOQe_=XF?L84L#4=CT`+rxuGfRxQr{pAeX*36c?95^m)YbrGQO%e9@0MA`0h8UZH!y!upF=?blp=KUV8S'
    'm?obu1E157AEf068I%za<QBb|1#QQxT=Dt1@D;s;gVVvp!Q_;1Zj9IeUl=P1^5?|Y&gbfyC)TdOR)!y2CRtoQup^Ok8N$dx?Gyio'
    '5REf03p0t2D?;#5@~G!&*y@k{O2y=znLC15AHq8(NO9ywkTrj_{{(_#9<O3`Z%@<UhLd;fHQ$*h8scRm_mCaDSqw}jB!AWE90&;)'
    'uNbD>9|i3;R1TWWIrk-%H-w!s^3d|NobjptwcS2YUa2v5gk-VnibyJAMhDb$5hQ(r_yL~3qgh2e$XZ<Z$^V6JyVFV9Udx8x=1k^='
    '=%}c`CFR*iqmaF)4A=XL(*VCRkF6>ylY;pvu6jEcbD$wAK#=A}3Hw2U#CT)?-fp}@c#{psXMOp`L%Woq4YaJ?BRJVxN=ED)ZeIvN'
    '5_d|Om2$DIW0k>q^rqa<&M?toAk7ff+w9Z%lw;|Sa&%u_*mDku2_~=~;e7`#?-~{JC6O<fg|M%yxw-ws+VN_Vdm_O~kti@LZ<>fg'
    '9&GvbX3xk2u*s8S&|qnMWhNHHEe#x0%R!F_0W%g(%Y;<WLqB8cR`Xd?6wqc!FvHl$)<ugb!md#f%K`=_XpL#C1^_t#1=;xfmjv>@'
    'ftRMenF~+W=cWRQ@eogQaeu7Vkvb~L;j-1At@P=g;_gIlv@|eVLZM_IuO90Mgat!{dfIfKBCKWCaOk9!<#D!+qRf6ki14W*0aTde'
    'T@7<jzk*tuLtqhx<IPmLOW(deO^+)YzQ~L~tF92MmAYzL)%5^1H=Q2$l!X<#NeJ!YV(1RZ+*sJ9C^NnY@~YDwRrc}Fbv*@O0MTUa'
    'BrT|uFqQ^ol1A(vGare+5b$?_ohJGb$S-(oXlhICt5V{ajZ%Q>9NPv5x`K8UA!2gNY0BgtmwP33IdYtA&J!9C0xCu(in5qQ(Tg(B'
    'f+l^mg-mmF%8sq;NQ?0pMw15A15Y72hqRJK8XL?MKbj`7F_5xFGsg-4aYIaZTR@I{rny5{3vE)=fpr7*i~~CFYTm+Fsa{s<6wdwC'
    'geA3F765jd3L>epP#pc~>QC(E=V`oSD-L=oeT+(xwN=s4*-F+sgSRM0s@L7)+DB15kUzpSZmZIet7C#!X+%lBx!MRBZorS07u>;@'
    'uiDak4s{+xG#@)?diaCo|76;I9JuNUipbN}cN)+HG9per#mGWfbntb%O4|Vqz@$ls$>v}gwvChcy&!?vutb2yP2s<({6+A@BR!-E'
    'H1~mSnM=w3+thOE|5(1}-=t3YTbz;kq-JVd+cqC<oR+wFgRvM8CT(mIzn>x>O3Z~HFxQL-CE*5AZ=AexW76Y5vWD8pA$5~TLH)L;'
    '`2y%dTYmr1c6x+{?w$!HLq<u%6jdcS86?f)NEU6M`;H{EEWW&#s-trojgF+B;IEX%1MH-TIjI^S(n1?S1Ehr}(8=|CR2-<Cl_LM9'
    'Ht3D#3jPC1SyJ*D=9E-*tR(OG%THy$X$^;`%e$=)c1m>hQ8_V%Ok7eRVm^D(wzQeqLC=JJ%ST`ddMKMp4M*5CZm_IyJWYP|yuva{'
    '9Bg@8FO<4Z!=~mg)gYK8oR%=O5H{7v?3_lztV5gXC2V1?l&Yr_>c*^6<ud^FDHFBBT-4<1<s3wkj!XE$a|6_V3=Gj(B&&Q)Viz0Y'
    '6#Q$KvfJX)2i3Gygr#0+#mZyGQ_;z%0RP$(AQlWjR2-@ByxASi@EH$ukQIVn%E)=LA|HN<mn+hjJ-AF$-ho4s1j7BI-olr&-3IA|'
    'yl!ynkq{7h=`hQb1zY<rG%Y5n&zo@w1BO;xEL@7uuFq+zdRU~y)ZQ>yRVm`UlTEvUFt5+DWz=HAPde^-CYj&p+Ne$cfd{?8mhm_b'
    '<qzx_33)=0Mwi-rx~}JNhEsgy^n)KJ%iCqtiM`*^c}U+yjtZsj1*TQr@TI)%77!&au2032>IgD@c~f_e<j>QciMKJ;;nlzIG#(nT'
    'QE2vV3+0aieAQYoV0DUU7rh+4u5~<f@kGAV!d`B}9sxk~3EM4!M>2QGYJ(QOR|~e5`cDNk2`CKLv07r4H=739C8P191FveXf?B<_'
    '9;a7_i)n8T!S}4J*R>wtg!8}a7^<~0^P7tDBQe{YUP+Pt`5eJ|o!k}fkB(dxc{toMR*xqdfcDq)&JN%#ZZ4O#P=r|j)BDmGP-+JF'
    'c1tIT6ascev2tlR<yS*qJ#WW{F&*xPO^<p%oF=zip<nllTEF_bTd7AVggkeX&oyqy4EAWLHz{R^{MxDjh+R}wU41>ZR0#kdc=|s`'
    'ZJ&gB6(8ll2g1{>{i$Gb7`5&tPYi{hqu~nG3Y|}OP~i=Ih^&m2Fe_}>%cKYSgk?kIBWS(#Or%2YRv`UPFRI@$Y~6ATgfJ8vM`ia4'
    '=I|Inw*SyxG^(otzEV*jN;w#td}W9hEQVpUkg0$02!A{;yQGdT5+f3jj0?B^VyZDy+bu|_4UiueH3xhcebSKqdVr%TT4#?6i<6u('
    'q)$d}y{`gqUdrzjn~IpNRQzPcu40e-NJ`>YY;xmWHL^>R_OkTxkd9`-LA;XZBSz8${ZTpP%Rnzu{rP(}fdIPm@p<#)DTH`iN#i1X'
    'DVp({M@Cgo1t{DwcHtO|ezqj6Zo%|R_u0)gh-@uvYL^>n?=g5By-Io*a{IOcDEV1VBomHwd42??Bn4jmq~=Dz6~Wf>))T^&lZ!zb'
    'pa1BXrECucD(`03qa0wyRkJhwq6-IkH+M4ju~kYtD!x>bR!*ao(C<}M1h92wo|sQSwvSeO-Ad+&%{8<7yyo%kBXlUjgUq#BV^vHm'
    'VT1U3iQ-94i~Tt-=E^vm*zyx##DC*~g!z61lS@jIk32(Np<s*_0(hT}JrgI7Iu6Jwh^xza!TZCzQq~xH7%ivb;<#smUo~hB2E`VY'
    '20)TE=y#<tQflo!-=u$dg+$*hHV>ln=!SU}SWZPiN;WA4nTP2--GvRHO;3zL(IL+!LC3u4vRJ5G6@T^BRaS^Hshf@Zk*foyJ7Pj7'
    'yH{1v_lAq(*(#%1k>xQ|=6&0L9G5W+owd#7BF`#^D>y!7lP`rivvv+LYE@(v6+m!&d=iC5J!0fauLWiOb5J_yK2B*K=!sRBg4W!I'
    '=#xRR;Tk65|7rhr2$3<;;3hb)8Yn@xIb<>Nx4FCUP~RApERqKeWS0iIF=C>^8j$E87599-5+eQ0&RP!Qy>AGKEvCIdc`Jyz6D{^-'
    '%Z*QKj?0SqwRpRO{r-?UO6BRyGe@!;IsrW3tjP?l@~<E@7O#15yos&iZ-_)gtD;QU;@#%nZ?R#~KEK;;JqwXMW4|EvM0pjh#l_}e'
    'M_`3uFkir-U)$D+W_(-d78-8Am$xDJ(TRT?+uOP#qymh#v8C@`Bv))w6yqR(e!rrzP^u*=<TX}As_P#*)gr}SeUq4lEEA~0nt%{J'
    '5s4N`G!ysyrH&iYM|C0xxXK7hj?UzyW#oB@s`MuJBb_8g)2QOJSRJDA)VNdM_g5ZI<zEl))Qs_1F{}P4*p7F{BlHaIfb;MF?j+0O'
    'C>(!hIK%csqx&M*lz8-M%f8WVQ>b)Za#XdSANqW)<AA+}q?u?}-uS!Te#5*_E>gQDaY-BW@H<*RIce|;jpMGN8Am|#qHaEKiaC*}'
    'iV-5~U#(mh-MLw5XPxMoX7+XxC<CnDj0v)>*RCcG+L@9tePD)`__9AIa^pc?@TQQVv*u;J*&Ht$-fbOP_Q2PLiU8xkiu8P6*&peW'
    'S1LW5m8taB%X!%W@;1Uii0UnipZV=l8-(w+IZF>k!A^@|d3+Y!QA!DpfV=YRXf3dQm-o(8t7+=qskEo1{iJwJ9f_AH1MBqC`A5w='
    'h7g-8f@j`NGCX=~Mc=4BvFB7XQJ}(RZ3#qApH%%*w;+oBVz$2s=?&GxQvE8X{|!K(IlLCNc2QcRsjMoUHv#Vq_5xOpNemMe9dGEr'
    'OztI;!j-;q*C2H~ox1mF+7A_MU&J3Q*?-eg&!?q$O0_x#gqn|O2(gWKyXP7+kEK=xspH|pwPCL|)6fC)37DaN5tmhy^^L8rE*rkA'
    '?!;8!0j(4h){TcK4vIxuZ+}0g|7*+P&6PebSMayRu3xHNA5w;UR6c*TN(ejf^W3v7M#}~ag?blGlIy8vUOD?zcF3}lOWr^dH0U){'
    '?*ONL^Ks~n9(>>`(3?VupsaY1lq6s}4{o(hS$@W?1l$%!ny^v6-tsA&D3nk-%zSjAjg1+vlwzV;*m)V^p~fL@so`{})wzNSa+Ib{'
    'O!uF3642}+G?lr2bz0bo!~kr6tSvET5$Y<!b!P$(S}C&Rl+NAWPJf6;UAif0r{-H14S=6`-V&%q;@hp#;8V`{(F*=|z1Vp*vZH`2'
    'Iq1{upVQ~i$OaO<G&9bLjcGF`+=1)#n2!vweXXTcVv!5cgJ0A}&tAqKa>9Z<IarFW^;H#&n26P}bveCC`#~SJt{l0$JMlmWWw`X{'
    'o%93--h6Q$i~E$WNwzQS09p?(4JM=xBdD%e<$l{F2~B4az*R7_1J<e$8$mz#x%+}<_D(9?Yrjg^p|0Wr2)1OEizDZnu<{538<}o>'
    'uydvN?(Imu-WyN`F45Vz#6>|#&Uk3AH6DiXee{zvm=9n*b_z~}3^`qg1&?r$@Nji=cqt+HKGB+9js+<O#%%IgGx_01?vZ3Qco+h-'
    'w=Vunb=cGVaWz9g&TYAQgaVA&vuvE7w_YrdJ6HZ*-5yLq?E9pPW4KJJ?VHdx<MpyX0gYSv9a3G<nh6W)8kA~erBuDMr9TmAA}hl~'
    '9OXb5ljKby*tfmD-biB|2wds)Yo6kCFFO|#z?ahE82XDS7ZbNhHQ53Hy$CMKDuTD}Qfv~<AbhOr$RTGh)GvoIX@2y9zbfbVW!l7*'
    'G2wm-{?bw%xAk-H356BK$Oa_5HjFQKcp`=B)L&b?0X{cZOhkw>u@_z0p|%oPfQd~8FQYd`pOs_N{coxc?l3i|fqM$PN}20l#3;$z'
    'NEP7e675adPIR<^lV1eVx0JT8J`Z123tTmAF%o0n#e>C_Ke!e=ie3m>?jRb`ON;lY6t@OIFe6>_opm6m?FwFbaHy{$KPmzY`<*X0'
    'Jlk-Hu1knKX}14w>%{+(_bU0)<NbR&Mk0Q8QPa=70U?H(oFb#GJ`XEny&iS)8Siq8p^Lhe_q7(SV1x%Zc!o6hl<Jo2X`-E`SbC*<'
    'Q)4<8%S>r_)|3q1h~4Fms9-OSq(;r1pOb$1^f~xJGn89nyJcAsT6>!x@e<WO6yS6UBJG`|u}9i;@IJ84FJ`n-T@Cfsxp(~n2i6gF'
    '3`Bzfqj^vVZf*&31I<-+4Q;E7ckkM*W&?khyR@)Zx@qQ6tlieU93zbgVd>swQbxui$I0Iab6fyPzNM=(?*%qs#I*uBzLRi$PeCw~'
    'Y(^T5rB-z^iSi-waJ9`XXyL2J_)>cq1BQ!FV8&Tw!@99K_h^<058LVD+US)OGOb|pmzl+2R2;j*F3Ev=M=K$~Atb<J`kZV9b}atF'
    '-DHw4OvLu_G+mKCeTV3GtzmDb6hJ=Udd#q=;M=g(a=_2)OJdcLZhPiXDobBjrE)k;-X;S@12VP*<IU$e>?=RjwaEu7WZ{F?k;?fp'
    '!hXh7090|&)mOSwA=kPQ@(_Rd28@9{0|N9BcN|@BvFZ?X6=_8gK~k6p=Pim_cEOY04&W;S`+tbXqy?&Hut`}i7|p6A=i|;O0`Z+q'
    'tN)PF$3y+MFwSC3lhUWztqH17ikS#O$$6Q$2ZxBG5I-pz7g(FvK}W-btWvFhxnrIPKqA0d`5fN{XW>p^-EGgrZvzS~GnPE!(Qoz^'
    'F%hj34o34#Z7_L#F`uOs&M~U*$!QJ24499GN8Wkqa^&mxHm|(LOL3(mEckUB&e1Ui60|e>L>)!Z_jC1$0Epw2D_VVTy=o>7Bd(kj'
    'D%a=8T!3&ASt<qjsQHE1StU~MK(+EepTGiVrFl{p`28YtHVw3uZkN~zDw+#nqFUn|1L52!UNiONgdDb#Bku6;SNUqGy`QZPv1_1G'
    'WNqih<LhD<9l)LsLh6z_!VCWt!%Ik|@>~7DgQLzBi;{;~+e<ETF#c~PGe>29Dn*LsWwuC!8{ImbCu=%%*swPI7#P|=SAjU)M=EKQ'
    'qt5?pY8WeK=&cYnlEg@vcwOe+^Z6_y!whQ(>x(FrM>Esv+0BF#f<go-?l)VIOkq6Z<6p1Mw~$THk|LK<^Nv%B32>l>B0_e5mITw_'
    '<x&uEuZDzGlWCUJs~?MlaObh?4QBNV;s|OM>;C;X<WFkOSt``^E$q12Xsm9}ZoB$X-QKFdTEN^*`_7Qi5RVK7P%p&y-%ym`+;V`1'
    'wS<!)zS@S_KJMb>X{3C%on;%~I~az4{I0{w6-DoiFKk18Pv(*nHVxbRemrdSX-*vBxEh_{TX;DhL2x`2*>Tq^w1B#t4c-7B{ixR0'
    '5|B=~3C(C;YY1a3lM9%#k0)vf3Rw@sL<GdJowp++3D2NUdM(wd@dJ-~ozX!(k9Q1x>jPDbPl=A_hjs=BpT|daK1;-=Vgfn~TMXit'
    'efmNI%CV6_at9q;QN5!x=n%;ybf@wt*nL+I6}XyDz`NmZR8fJ3<R<n46^FhYht<T`MDg`_6?B<LWX{HOM5?SV$DSG&ADzzRl`B{T'
    'C{EI;mJA%}D8Z}WM6URl^It7s?qrU%B%9x`ha9wo5O;^IcxG%@lz@14^p?dLA0u-64WNVt#E3oE5RvmMQv+azt4kj%hT{s~gQr=r'
    'HCp*>SmVujA5ZlWVapJT;NcKG-Pliag$L9W^9w^{ODi{;YiAsxKUJh36t~84U{)2GY5X_`i)78->7}&O0v5JD0F1fM(j!Ea!U7mX'
    'se%VJgTlNslyp6)_y74nbl$SW6zPqm_N={Hpv0!qY!un#e+F=N%xTkv>+eO`s*D;=Jzc!1D^zRb$AnywChzH?(>vx5VR}enL>`st'
    'gj3(W^*pAm0Oyw9t5IEu2^LW$?BpFSadAAJBD$PGxz_5>3;vrhfE<(*qm4XnJwY4k&_LYbh}PA2v!rvTVPwkHaL7^G$Il!tjUJ@)'
    'Eo+;g@~V5p3H7DZ_OBQ<o%NmK8&~kqB=cNLka%N#0rnj4p=hXiT`4Dkp8gL1Rb~#NCX!w+?&_IuW`Y%4jrt^1RnixcTTntg!_y4t'
    '(yfy<M>sK$Jl{DX<mOyZXdaWaV+mf_y%6xGkGXpxX=wQYIS!(}Bfqed8s!i^IPn;7^Zl!v>DEiUKD}UoSr0_{8-2~!(pKH3Zokp~'
    'K;_`QYEYf@5_2OVncNtOJ-`0P)R5%2Ve&=R3O@ad9iLC_LHt&vZX1S)X$58AIuxNTf4e;Zu6$awuOmiTTj?8aMu<-*El=2zQ}c@h'
    'TmtcJyCAC)d?7S|w){Ln$h5o37wT2j$BV-dzYxkc61P=+%>hNPyd}g=!5MyW5elq%54HoUQj0A?*R=GhbaD;{A;CRD`~(O{Bth^X'
    '749g=f=SG3isLdWQtgngJ|#|%GI5ehdJ{u<%7@yIm9i>;dg9Ubw&smTbKBTq0WLO%60WEy=l_1q(j}%T!tfoTw7pyd2OiRTqmQ_j'
    '&cM8O<{^#yyb;@5d!gT4Yi0(->GhRzLexNRzSaV~=m($2|8HXM4KmB38wV-B&KH2}JPCe|`GXnp{f#B^uUYhcuOWLgan}--yJ-NQ'
    'Cg@%HiG|y9humZlLGIVqRtU-*B=6PJ#4~`74LTzc0JuPM%Uh!#Vgd!Sqmo(Bk@6MTOb6%w&6BdW;vOylI9ktViA3l=+d|CLlEt%x'
    'L~$dL&=f(X&twA=$RxlOlOb3-uEHNfLUm?@X{*!gU9S_+2*_b4UB``D%jq=7_UCxhd#6`lTmS@G2*p_@?T!o-@(^j)hD1x?emH5g'
    'kEG+lq}vlP{*-pBnIWNYAt^LQTx^4O&1~bJ8F0fp-TWC~Q*Uye92*0FRzh9t%Xx*RYi5VE2}gpfQu^(!Hva|QEvFmVr0S`rwRfot'
    'aK*96GeE?&MaCZ9Ix~w_U+&RAlUQ^o6*jfDvb%2)8}uULeooauojKr~TqxK7-RqCd(IYuj&p@Q(s(K^kc^i`<)OA^rbUR&!>QQwE'
    'IgnDukT<>_u91ia)gQ$#F%<ARyykg)<w%bptVs^EsptM}LbF)t1CDKAyyo1lrq<1`1D;QBbq7{5n87{n974XK2dyzW%8A1RLS6X3'
    '!e!IAqNbIs1i~;LK=SwMM)s^>H1`%zZGmuiRR%9&1S{#q%mg&JM9y44BHh&1x8F7L+?^dY-l)0g$Lgr}TppmH<$7+iITQ1VqWi!k'
    '{#`Mo<&)WcLEi1bNnP6^_$%}9PpE4CMvCcUQJqWdEaLTXj<T&z4zWd#`g!^&W(-k;AVImI+1bU{;+Gbr!60wj;=fSEB*k{ZmW(pO'
    'N8FU;G$%kqMbio%-)$Qz7wE2_qYxIhilQ)VkW6OI5RH(>xF1Gp+>CcLOsm@=zFKlN?b<GW?7Yb<(-f2{pY{*E;&8xN5+?B_CkD~&'
    's!V$Pr*&1|H`hfogYij}Cy)V^>Z53a8P@DniacC_G!Y>?!f?l#+gX}=I}6I!#UU{W4zqELvOW%%*jB<5epAi!RT(DnTIlHw#7s2-'
    'DC}_dZyM`GuvhpgJllbPn)=#w|FKbm7WR*;L*(%<Cu(vQ?wUt(FGlbc`lWlr(^r)T;@!aVtz7-+P2bY>%E=sNQr;tddZ0+?x>+|t'
    'bB`wvY>wABco02tCu8ml?sDklw?#oN*^|6vdMa3cDP0howD(%vs-l2@s~C#?pHWJRhOY&7C5E^{<)O0J60FJzb79H-ING7OZ7!TJ'
    'LIbhU+wUrerem^@!`8=wNHK`C@pAmcE!pBxc>I=YUE2&bdr>$DK#tuWii^e<FHR)qhiwnkk~JCD^!^W+KA!0GLzFKZ?!yu*8gj%E'
    'OFm#aB>xxjq&ckDOB|<q;Gd(kJ4O~zj=0<n&j`|vW&Us*&sV7+RJo{T(;4k&D4n5pUS+s#1G>5|7a%fGva`H63)ey=9b3x_8#Nlj'
    'wDmBE&`vb#m(?*N5cSu>_992zOU2v;Az+}6FF#EgcJOX*q_KZjolO4OSLcTHF;cp1t}QIHZ|b_BFWTfqmrq?zN4RmJz<4uRPqTnp'
    'P-TvyQq%fH1AjIX8pueUkD#C`FF;{i(&~)ezXTZHmjnN^Z=!t`GRQtlG}3T9!o1xlsO3bB=R&L&wp%d#p=2Y08fA7Wa5n!6*AB%2'
    'cNxJ+(-mb#J1+FFtcK9@frg~l^qT8@jWlkAs*yzyM4eP1qO=Ek29W^3no-w1@2UqX65XH-CG@{T#`{Duvf+5#{o%Uu=L&w6+4JL|'
    '_`F0ew?8|-SK+`)EGb|1QaB*MoZ1pgrBoIaHin?ew=C^Bvn(Iu71RV!uZ1rFkCuu^F#bdYv{MbqtInCXl}J67O+`e3oY~E1k?qb<'
    'sMW-!w>+89o}ndPBL8Xw3AL~qCcW74ioLIvCMC<BMoAV+?*a;{N|wlOhnhMr@FTK#hDGGc_IvbBo#Uf19etBzt4R2<oF`()Kc*1E'
    'G_W+F6e_@G-T!UzG<ZwX$k7jQoD^hdVy0<Q9l?y@4KAF!Cg@wl|Bn)qZ`;G%TntnEh!ZgSwi5TKyE7d#$A~ix%^tw00S5#DB~`cD'
    'c~?K8;+W(^+?4je0p6vScTZg1a?OV4J-cOK=;<3I7BxfY>E|#J6dMdZ$bWjxNi|}z6MKFUWQCn_*6kRojKf)+ik_Wpm&}pQP%7!H'
    '3GE26Ak0<ZI(?D)$A5VSoD7cp>2-%WaP|$flLF0LNVt?=Extd5HDXe#_!-gudc|lobP2P^it^cT!N)!o7cG-tDmrnL)uk#YRBh3o'
    '!<3C4KHx4ci#=(DQh2Ltm2e;_2-kC2GGrXE$@)lmzq{lNU7mb`{9}zvz%RWq^zh{U3a%w%0aPqrw2Yv5tI_)~VI`!D%!6H?Ku+jb'
    'e&jZ3XSa7vm2kk0dUNUFLZQQcNgR3m);KxkfhDThxXwQ|SLERP)5{vniNLGC{&7ZAu`E=TNx0fEL{`IO^-=bQK&v>12}Re6Dr={M'
    '-|L*LW=OK9pk1syvVC#K7&6A=GxG~N(b(1d5-T~R7~NEUpg(l2C^TY*wxx&tCo)JbwE9yM;&S&!KB%O+l+Qbb<eNz#xEx<1?egl2'
    'ql#k<U^?Yli9=5aDG^SC2$r(d&Rv6Jbbkgp4~MKn6_acCG>SJ#8CTl!d}_Dj)TwQynbgktEl2weLfcQc$8lioh;7S^<Wx!>0?uAz'
    ';L{45_}{FT_-YarMogG%Na&12GLZJL-`RaD*SWQ)eYBLPgu{ffhIYPzQiZ_@k}4@ym21#cfsQdfd{QMYQ4mHmOg?DgZ^m`#1j=k('
    'C%!g%d@|8fZ?wu?<Jz`Od*B#o{gTd?(wQJAmNW+ARLpgW-LFrKO<_{g8W#@%7XREDb{7Me?h?&?8z6BBhrGEe_6X~R*tCy5ieoHs'
    'pfkPTKO?A66+=Yv>$!#Xw`R_TjBA!!4$oX8FeuTR5#C}CA!&>ZU_PJ%v}@c~I5)==deEov%3LY?pS)OhASPOUc%L-koXdBjLoJe9'
    '226GA)tx+;be62mxzVQ^R=L<b<7W`PZF!4w+&%5yqL4%`kya)kyw!bU?IOBAzNAp-w5g2f;Qd%JPqq{Rr5@1kTA^XIjtGb&5@Vj&'
    '(o!{D^W@=O@$0^!#d<RePaRu(Y2wG_uM(`PkW9u#L3fjW*;r`rJd_|@x`zEv=XZu&7+68419>(=_OFF0UVZ`c@rX*6h;F}$z63c='
    'N51_*@16O4_#EKhYF|X!eQ(T_#d{RmPunY4qyDfRo%h7;Gt@QL-U8s>+neKco$!0k$NYF_XzV_c*Joqq?({dufv2}PJwM-8D&G@_'
    'yCz0n+Xe>lG%dZZ!!U$ti+(qzlq$N%o;zUG2jtzMBTp3pR|*2D->Eg;j$k8Z;Pq}M;TW_-;?yARmwb2~hb-@B;}|%QP92SkY+#v-'
    'Cxp4@)WGq~VR$s#Gos8|I+daU_F}OA&;loTDF9A>nTFt&cAm5pMBm7GX6YbGk`eNFX@{ON72Clp=uMi5z6=#EVp(=t^IkBn-xcx0'
    'k3Yafy>}kEASfgEP)wHR2b=m3t!?Cren2;owq<<KRa7C)DNs}sN$A|hB{gdBT#1I%lAbV$+9Bmx?EI!I1J~I2VAcPJiG^Fl97(D%'
    'xihS^n;1eHmV{`%)MkP*e10QEFAJTU_g9ajZLf?PzymSAILks%<Yj6JMr9?sMqj>Eq*>rSXU|Kz#bpK2q2A?J6>&stlq{j?X(Q-2'
    'Z(mB&I0Yc3`CF<3JS&X8`xgD7o?~6k!QdZiR>DH@C{RLn7)pGv<|LoAX(GvKP)}#{>3;2L{rt<4;5G=c!t<^r43}p`T8!JiT($DV'
    'Yy7~U-bYgnCT#jiY_BoZ@TsOf%RhdL0EgJfEq{$n;&i6j{=1sX6W|AUKH0B<$^LB8P{yd`pnwwgH!+yHUpwCwQBF`c4e*1OaAQA3'
    'xI6n}cOoyQrz(%ta`LKO?EglGsIn95OO=qpNT8a>ZxEhk*;{bOT<UCT9k~sp&&oRQEd1(~ggXxRSy%oT`*%ck?cO&LgAu5VsZ?yh'
    'zdiH`dlM@Rf43&Z)}D^8G6uF6b*=h(g@RwwH5v>NS@G7XNBEDEQ<MBjQKAn1WpqK67~kQ4z+a5>_$O;zkmRCeVL8$5fl08T0r&2Z'
    'aH^Tb@RHtQ`pbJY8bE0*V=j)lKaOK%%!@F6`b;x>2Ne2|LwgeIMEANYoPrjfmN%##%olorn_ZN)h{+9zIZ%ASk`g@!Wv|hejcG$9'
    '>=RuZyVt)9AMfdFty(6(Ctz3eTLhzb)fFrGOMO)IPBI%}V$LQXO#Y8Kyi%=s>@v)2HM)u98;3M;eS&>5K?Q5JL685T#6`(|Cz<#m'
    '&dInWLwUe!>Z)<73LpDd@;$@A);#u*K?6HjA<q@ul~)GqY)`fLWao7<QPwaCs@#CuMN3>*Y(_n^Fxn*wjeoe8(_7N7E3fYS*y9zd'
    '{GDwtKzqZ=9cA6|t{vKoolM=9v%skguC{HEv-vm2&)u%JH3QQLRbU&n!c1w^{5jtx?CGe=KGZ1in=RQ`>HR0yD>GvEfho^qcn4U3'
    'q=Fi(cwCr@R`wb}G*q{*#uenGqhm~PFZF9^owoJc5r5ahBI{iR6pP*Xf+wSpl>T|+Y*F>D777R6@jtX!fHk1{{rA&=XOf>$F;Hnm'
    'I$MNqK&h-doY;tvZ>reo8z)^vG*PBn_<H<5*O*ynxq>O6$if{8k)eBPldFE!P;|g2c+v^Mg$e+tqxZ>ckqQuQ8dN}x_eobcYj%Yg'
    'UF_z6r3NzTIf<wrKE;NyX&&J{vnTOKGUB>=Q`U|xd~lMf$H-h~{f*Yz1Q5TuBewRIz6*w+Ve8ru9)9Lt`+^JIn(u=AxHSF{uUMEF'
    '=HOfJyio*tm<c`TyFBgPZ!sQ3P;VNkiT9CSfQq#LKZRwT$}g+93`m-gIT?vI0jqmw(2!Q#y;C$73DkO$oLAIHR1S`1$XG3cWd4V&'
    'P?(KhAFHs45*`UMj?$=!eR-Lp20u3@c0-9!(3}MRUmx%jY~2w$vvTb_ma^-cx)F$?p}i)}htTdRMSTPlV=Wq!TsOAE_O!de2brz!'
    'GpXCKf&L1)#9XRZ6da<(T~G#hU`nz|e$ctGH|4%>yrY4Kq-FgzLsT?`*Yx0>o3N9pAH5Xvea=Net!YQ1@~M@0z#W7%Q<u}Ub;c@g'
    'L6des`)_4$#2ncnmqC#CO6*=-)eJY%=QrgaQydJ%x?C6EIVqVY$?e6Ho%g@sV9XoCv!K&Rc<piOG&%tg9m?}J__Iut9`^JL)JWP1'
    '5plbUf)lgfs<I+BP)mS^_)N8B&KiMHHkGx29Q9)<M=O^obQ!nViJy`-A=urOH>PMtLr;eP<+!RB_%B&CvL%3~bL@`-AQwf0EJ?H5'
    'txCNP<(+Z9itTeAq*0>0P8c?!^edK2)oYEc`lXiJx+2i<aNPG@bO2JWmEl}?ADDP-zK4Qa{-Z>`GxBF6tiTCvU*B3tYr#4(#zP$G'
    '_W9sBA0N%SL^k6`5_Jf7_D?9Tq`s+`re&^r4$fog!l}5IzT!byX>|X!Tk+LWCt+qCAxloqr0`Bi`3T(*(TVo=dTkzG4^)T0`I#el'
    '{>_Fi#uo*Nvbf(Ene`zxgsaK#{Of%uD<)o|#&E7do@yg=_)WC+B)mT!PVn!b$C!O;k>dr|C?Ec!eQVA+d-1rK(yDM;M?tnqhJQ(U'
    'eIZDkJOuXZk~C;`-TMdw8!6(c3gpe=*zH{ZKIRpwMzL)&mhG8-Cg~yIf|MEB{AmPwy~Gxxq0dt1iQc+X#7A)vT}e@q1KPy^)0d_r'
    '42XWkyek%1<&ZsbjGoY#czMVay>GicaBxr7U-&MK>%lU0W6W+Q2mE$nhGwKoyD#4&lDsDUzPB1RVNx9a1GjC#sX37OC2VtY_vFUu'
    '5dbDKGIwO2v6jV&a+Cd}T9rKi+ri%Qpd+3cBF`g87ALuUyO)?~G3>>@DrzuvxGe5Md61OwZmgIP@MeidIFPou{vs2|2i(#hVMSR('
    'o)HA!h9j8MXA*KWuPNl2xp)Znu(T{l?bA>1f2l*N9>ksz1x<|<-I4gF8nxjUIOR&r&UWHz(18kL#kM!XkJ%X4iQ6s-s(z`Qg)eVT'
    '(<KO5N2@UP5`fp^&gFXj`2BDbit!ySa4%eiPgtV%HT<p=jCl^<_F484+`ENYPkt!)3-aq}abzk9{2zx^<m)qod3+@76;Q<BY>*kp'
    '2yCUK38fxhJr4r<AL3bImvKzTs&*|p&(b@xBu1E*{S!+!gKnZL3#MIXR#6+B6Q#gmE&95Vg`D<E!`_@8wL$~$FZ@VSiyfZqO0{gb'
    'F~KuB%%B;!&tfCtk_<I2iYXY-dr!kxn&rN@CzIIU{Uc4oa}A7LZ$x8jsd1&8b&{6g+(O)l323MLue$>EY$evG9U}OR>nW<_+JrQp'
    'G1qcUY7Pyj1A$S$cuk-RfMyObZLf$7*SOuO^nJHwX{p<-HgMwe$FW;_@AwRE9XSXrwi-50q0~l7($UP5SI6rZ3cLCSSg4s)L`G+`'
    '+x&83I-V9kL!x=*ZMQIKtnRLR@!8TRPJK1Zp9pxxSzEvV%glXrD@GI}qqs!|n|5X+I1N~OOVX0AR%k&gj@g9yVAmFLqf0Dd-64$+'
    '8OUn6P;-B`l`Kt!hM>P@$fS?5;8>FPt;4C(tY}WJ<}TtqL;7o9v7$2nVcRBVt$UD0x1s*^yaBHeCUpV2$jQJYgQROfp;~|23f~fZ'
    '>KmaN15z9xg`ZueFVcoQ8=7q(#J~cICC;JZPcF+}dDrIhhHt=(0$`6}#I?-LPC8I-UxN14PefLPAqboDKUvy)fV#u-=TL}0wq~lG'
    'Fz(DS3ZX72lebOQyOCn3f={~mUJPuVE-~_WZV#jnv^c7|CnDxjhY~3D6anvvfOs$bEeh(5J&l^s&)3^w>biJ=IE0v_Kp>Okwjm$E'
    'VBZ_VWi87}XsEQj_#J`XeE%J$O&z`(;0cq!L#(utcPaXSb`DOSY?c6u;;52MBSTpa^Pw5j0rRYJf28Y76@e6)>CvSGv2Nh?_&|qE'
    '%egvns#haK93;l%e_ms;1g8(c7Q;4!&)shGAMW-9WPwru#gZwj@_7-)P=_fF6Vbz3C3q&ZGsp1w0uk-#`wljuESni2w3H?@4Jr*d'
    'X(Oy%Up2krTg5h2x!h&LQNX~vdxohEbXWK;nEzue=3z;*p_8;c$8Y%g)ir|s6zTzvTx3x6r5#;gWm_@HLZAG9_{nKyWV;$mHD;IY'
    '>uSoG8Mk@^B(7`)F{YU58GxA0VkM`$V|m}Ibc%OqH<@b(ZLuuz3tqy=1VT_=KOtQtHc)y@-GEfI%S#fzKh@W)5-xdia-#=k24o~7'
    'j3lF7luIg<%5rar^;@=1H(U~6Yb@~W5Yvo(FqY~RG-UO*z@I7xHCiQeUNZVGTqs;Rf(jBf3V<$3Ynz$3^bseD%EbQMHBSBcupsHK'
    '0nr^4tGz1IADnj%W)Qqr0n-+ev_G26ps43)4f9qV5+EfWdV)EycK^loJhHY`ceSD`@20%C?{ge`SARQcc&*}Oj^jmtXoW_#aMrVG'
    '99dmwg~L4u!rr`QC%BZgna&d+jcY~#WP((DbzC4h@Rl!afES&noIx-l!2^s$gU!i5mB_JoPgi$G^<oju_=CLGE3y>_QfVz4FQTct'
    '0jMZ{^eIe21>XDz`Wm?>K}OM&F?V2podCGra9*ECQcpls&wemdfg(6HOut|T_gb~fJb@M~4P6@Vl>yftC~(14)sSYCoLh%Wb|z=%'
    'XOJC3@~RJW=<QT`iZJa~#&a(iFT;Iu9nCzH9oFO!PEKI9m9hF%?MOF@34cll>XsAt`+f%<GBb+AES63{<jPZ!`cp38-7wZsTqO{Q'
    'oRylxzlrz0a{oCP;Oyl^8m*Vhdj)AiR-IizdORzX<aUwXbXKU=naOwUMaj7K6gp{P=7<t+J4AUugQ5&z-Gufa4Npi9_1=}lk?uer'
    'wgliht%isLvS1Q~c$TYV&v+-On^nW#>_ii(w4J;Fy4s8LsYzcC{5vE|sTBV7r0i@{+;G|l^P+0=oCw@$xVe>9RY(tg(IX9i{qVmt'
    '<*QrY)yVu2^qxhyEO*5wE$UY~pa~Vxk)zrT9)5XPc0z!ADg-joKnQ503$tWQ<kSJsciF2;f1MzPe=9m9#oP&m)|R0i-&hEyT7+D9'
    '?OM4yr-VISULAook!~QpMW@4;oGv&7*i+5&5dsqD)24NP-w{iyCGMBw1KJ0xt>yF1t)S)ATy2`DYM?uK0T&+EhhvcI-cqXMdU@B1'
    'j_@OS&GwId|E7COt7pT|LZ;HnuYsbY^vlCi5UH;VUY_dkh1)p!5{hZ+QpCZv$c%OA4v;79LuDK-NVcZtDXEM3bKDTf!^SBb+B@90'
    '25B1<>(a`%QTJ*2iqD6pO$gHSFn%2{x4fX5zlV$WSgVh0ds|?@De~W)%m9kVAd9laLip9D5hcb<J_jU0$;7Xxb)0kHYX%w1yK>^E'
    'B)5koBZMF|$>EICBH5t49h%k{ylJr{QI7x?pn{jPR|AbQD+YfsdFN#?@Pe@m%>5w25d966d>$arh3JFdlN2RwK;91D3ctUH=)*4J'
    'QSdM>6#|wb5cOs?4CW<K|4do`6}ta@yn%bayNW!3JwhPs@Ba-7!pQ3nnEHGF7Z1EUDvQM8>{~REh(EGVZvgTV7(wwdvG=AB$m50h'
    '(jUV6YwT}2AW9QO?j^Cau5IKi774^z%jzMacZqo~i*#O>pYwc5xW}ROJ$w6v5UbCdMYhw1&Kj1s&$Qr^*3yqIw5Ddqg8B7fU#dQq'
    'T4AAXg?so2J20lNb)R3zJxf3dt!8(}MWE%Iwz~l?Z_0J1u@&oWZ;P4UvFtF<tJzMhOaALHH&fozgs&|nP<6jUlU{N^E~AJew$ITv'
    'fz8s#+B*724BP`e6$ySsPEa0uB+*%m0>ercMb3V?<Lq{;i=C(@)VYXpLm6)0&0$8iGG*<D^71%5KCa#bPVGusAwVR!2;Vmt(qJwP'
    'KY6TTBEG#srO0ed#FQ<G>9-!~+TF+esUj(O^k%6vdx<~PC1V!x!!2%dn45ad20;`58=I*9np9Oh7(<Cvn{^P)8z8GcA7duB)K<eE'
    '?apS2VtCi=`dTMNqa-);KVygw^dn~pAyXt|p$gcCLh03O5qYl3{fOz`4ca!o7aPg1u+MO*Xo(#}BKNsVNEoq{)NkvU)O^NRae&tK'
    'rL`kE6H8m8SlZqVptjI}b1gAp!4pN`jOEU1e2iYe9&uPo!v_-=^M)V$+vDX<ffR{D#5iZflVclH5Spr(gZBPt(;D{qRh_Kh>Dj<l'
    'gQCs;rg_~wD}+RKH>7MWx~w9w%-v?Ny&ql#7h}M2m)yTUnuViBv$7<_Kx3+yAqhVncttso0E-SCvVXRO?>1{Bp+v}03Em%!+^lvG'
    'kDDpoixo46_hEwf(>IuJU$TnWh4u8W-HtlG93~0k8wcg|RNdq4MXB$=Ffpdxn<idwi7yd})G6NU@MoCU1l$C6wrN|K7i{16ao?9Y'
    '3Vh9bzM3bkExqT->P@)*Y~%A5I>l}-M-d!iy1%9^XJP$_HrKG$jlty0Y?f=L;8p4RZ0>C6^4%t{{YL-9e&7EC3b2YXcX}*3k{a9m'
    '88_mEw`cFcnW@f6wQXl0vt7)ZcW*>gFr9wefUH*=Y<M-JVLU#CIWt&EW<r!oz6UoG^5n4lGY{m}>;<R_znlo!k}Zz!t=fZ<04`s?'
    'Bxq)eg!eR|57rhAw;%c=yDbf9*yG1-<yaBjdie5rz`LqNj(xXV3UJFnH=mu+{?N$z6_>h>TG4%ql+pMbd+C~NF`N-*=b>D;O7tNs'
    'wOM-9`->Us@;R%^z6MVNHNIobqH1F!?0E0JCPA5_n8~9LA5P}a8^$Upz=R;GLd4qnp0E8DEF{_?lr>%^Ap>semI9$iZoD%0gtPr*'
    'rrMS~P54!vi?x(*XP}~*^G+GE(}ouFrf+UD!U$u4O}6B40VG8@7codhaHnn2)cVzvqp4I1fA%337L2-Lu9E643ybN(r*6St&(L*M'
    '(usrtvkKlx12)`umV!)h3ioo@)g5k4XATdso^{kSv!hajqnac+*SdEWXL<wOj?&`OFUDyD7~zI?@eKk7rD@D|EiT4_MwmP8Xa?^H'
    'kIUZELt*E@xM}{oL#F~{Jh?!Wr&ckm1<CD694`NL0i8=<8%C7%pq870`xbVMUaENxoVOPH?xF&jPVNPROS5U?`XTQS9W$XYL2erZ'
    'uwWb&1q!H2SpT%<SIkINS8}*>+SBv!5SO=AM{LhtE-=y$QO@0Gvk6nX5zNo{@8WKI=!rlGX15A|tvXE^C0I<w(YYgtCuz|7L^nSl'
    'P}a+xn?nqp{9jn8nrO2k^Y#>!`I7@rVt$}I*Q2!pGw1Y;Rqvpap4~R*f~lSdp%yRr?h+6|q{M?-u*&Td&ghaT0|fVD!oWJ{aR~F&'
    'y^>C6l6K$KvJ0F~OA$bvNd`$36cj?&15v=B1yu#GELvfAk^6WX8=^j27+VFB8snuo2eFO1fT}y{&hX>9ZG(b}yjE{W_j4#GD3#kC'
    'LW78hrd-A?Bm07cu^5tLUFoJGQf8%g6V248@JwF%DSrupgEdNVwM-8a1<yRxTHHrzfv3$pv$c8&)N-zoJr8ExFv8FyFi)EslEr_D'
    'ttXnLfBpklQ^NE_Q#=aB#g{5)xxnyQ7bcg4B-0a5Bd(E-be$8%T4#__3Cbf#H{|#cb7g0b&WUDxC&i_Zu_RQ5@RR;EQS0Z-#uUXD'
    '6gF{$`4U9)SJtSq8wS@`k!4{MMroTf=stC5i`1yaqV)STuSza(eUFFBkn^ooj-=sPZ!ps_$g3!?@<fl2kT%~iC#z0jm6Q=DU%|D+'
    '97J%?IC92y$79F=YH&=6B45?*4T3NGvdV(-`v(WHr`5Sfb-R6bzUzbvNGTc!URO4=K?(G4`m2X8aUypzf*YUw+BP7uyd_%DfsoKj'
    'pxBFIe7W>tCi{GGO1ReZ6s~e|j(%?;0W&b2Q-KY({+i`-n!jcyR#*2Kts4MZ4#swDjcZ=inSb|^CH}xC&j>By4|h{fdD6v+i6oq$'
    'F_e8faXMI70BshrG1J&ET@okA5tp|yWnIL9N`Q-~9rrr7V|7mLM{UvKGR8!t&SGXD9IF2$gNf7_#AbS+Ykm+bbW$9l>i7ISgvG8e'
    'ZBU%rvCln?+v?qGHLNuM7d~l_A3|dLgD}OB#-jiW|D`w{s<#H8xt*Dy+#~ft?}tXOCs!}={feOar)}*uT}OsIEa#n)WPW}!ZKsxo'
    '^n6iPy60ChiiD_#_NV?NSec{H^qnryAertKML#85YPRNvM6n@>2r0|)%!M1-d*6}g*5q^7{M3u>c#`ijQ0xI`{YotYXALHVL@!PA'
    'xMk!X$iYMj4vB)wGkT73_<|625JyH?B=-^>8QFe}tfJWbqtX=bk|qj@-vm(_LS7S+mOl7t2OmEQbcNFZ2$}2U50&PSNLJHDVOOBT'
    '?Q9hu{zKi~u;38Fng$t!6Mnt#RTF7?V=R{f!$6;)81mb114bZdW4djs{T|HH0tX_Uqed^Zp8>)yQMbSH_a@An+Ybny!Ay86mV^kZ'
    'tC4)Dc)x=gU$1R-S@aKmAFmIJ(ux!?FZJX2sd<jMAJ<l}Bz_yp9ux$$qOAPA6|8M5xu<wQmDep(mLY#DGtlqAHkKbrG*(}d5`{UY'
    '`4>o?s5{uxxMwz+GQ#jaxZejFdqwwj@rVSUh|K>oLWRd4!Ec%#Qqy2)3a+z=A~T#<q*Dd^(WGy!{)MGskS=3+h;G<K7069qaxr-B'
    '6dO;7#IcUw3vy9{B2AdgIS<vU(r_{RtE_$=DtjdA@x+q!n_m%-o0j4CT-UxQRe#e4wwMYnJHP>~A$VuwdpFAX#es~GarpeUisQ!g'
    'j^q9z=cF$B3jIZGQS~AgZ0MtfT-21#N)?%DM!KMX9x&fN+(Qv~I|~t(5Fyo09r~C%c>;Ex&1MUgBIzhk6%uvGjExGzEmh}C5sh<h'
    '9fEs*(&W_l^z1|y8P_Rw09{{MXBCCFJGkW*dTu;0)QNz^fP|RXeVy67xO1kdxuzKzD=`bNJFk5f&A$<jht25fo}wKxJSgxD&wzX@'
    'eEyjvh5Qwq$H(j{lUEfLU4x1wDQId)QO-jW>?}r*<)aTdCBkIB#{f954E%XHgS9s_P{iYWs^Q+D$p>8pc4POn=HbV^CWEmxd-N2q'
    '*X5tV#=~Fmcs@ZNpP6X`WI&TXs|s^Go3+14#TUUX3&+myV#k)v?jZL@-Ae7k-1cnmlokR0nvEznRpkG1?$COULcNT(E?q&rk>$lN'
    'eS#V@KacGy0<^);KTN#@L<Ki5(QnB{9`vcRU&J9QuYKsF&lx@cXaX7Sr;J4*&r^B%pW&YM!KYhoFaXLwmHV<knc{l(g$97XR8T5U'
    'Md)dR&LunV3|%{`F5=Uc#7Z^Hq)@$b=&OBFWG~scaoeikj^i#<-987gQqOxZS9IQr0-vGoC~t3z<7>wl_RRHM_A_5G2@GT;^4Q=T'
    'F^xU#v8^cXIlv1=5-Gapjsj+@JhihID2hCOm@o4ng76{k?c`d-<cBlQVo~GzvX~RU&BXSP)ZK&ZmcZy<27t7g?~VYY-P_sPuphcA'
    'otKD(hR|)=fuWr)cpa=e@(A(aY!wchBgOQ%79phR#9mG5cYM@?UJnpG`LyFZ5<ZkDd5l)rZ?S8{puf7YhZ}iUHVEGM`p^RPDL@&I'
    ';8la{43X@S&B9dEleflg^N3XPd!JSo3Wl)v#SdYEeHxqOVb(lGrJN`bP2P#1$M!;z{<Ah`0qWk|Iv02yiaWk<0esYQ|Aw%%D3Z)M'
    'u)PgH5KUlNm)$s*)rAYY;M>{<b;a(HgBU-Ifa-HCvghAPn#a*(KNnc!8wf{iHpIm~Tmx)8yL?cLdf4~Z)&qr~-;SNMC&vi^R}a>H'
    'lLXmCYp9Feb!|Iy;wfwsBu;NxnrSw37y_qY-+twgB`8u$Dj_S}Kq`pl=e}Q4w-wS_LnktuQq#RiIesZ8mP^Tu_gaGcBAavKX5&Xv'
    'D+05OCtcmvHaoXZ*Z{So&ga<oLLnbD6BzVfH}vb@wt>~I`P5o>onksy^s>^-4ceUcR)dT>0Sx{yDxs90_D5pn)xl%g6W;`+b%?C@'
    'B?EW3_G?ZJ)Yg99)pZ9w<mn&Q`}tz5S^wq4%ABh~F?J((RpG!;S`t5y!ow_bR*<>mW7*U89a+I9#$>geQn1!Wk;2Ru9L%k9P2ooc'
    'WxfXCm>DNpN-*^YCl?s<vq<~(fG}F(JFwqMSbyRL24MZfr$Dnu;uqz6O5PUn(%XgWsm`G;^3gE_mQkZw#oG)ak-A_&gGrW|=#6Nt'
    'ze|P45IgO=QiM4wp?nanj`xtcfN;SM&Y|YLm-eva)wK61_o~o>w9515DfGJRDAs+aK%~&#F}UYjrU*^`)A?XV%fA=ShZ_9G-@p5`'
    'oe9N+jdM}uGfu`r?;xR$IoFabd!&6diH`u^zgoy}xUF0hO+4Oxk}-wFpih(iYnHN81?UH)`htwe*$xwEOebG*vZ)k=S`pi~<2%o='
    '4>T``>UZEt$#~T&34Q&tPAl?jPLELoaI<O?O_wBj1jcnQ>2m$Mit%3)^coB++LC;4fyL(e-qyWpqD}@Ve!N_$rsM{c^Rv8Ait&LG'
    '6xavc9j2dh$-1F&AX+QIY+d+F)Q1A4B1;!p>JtFUNqTl(RN&GxSfPL`9e!Xi@weNPn%!FqLU~dxwL^cO%;)_5Q9DqDR)R2fh4BS4'
    'mQ5@vuh0K)%GDW-r07*CwOeaoS#7!OaPKyJU{b+f0ljwBWfL@HCM(z+^(QHQRhnd=I|z!A<-VRX&82kEusVhuHje{L^S*)ZjTcpA'
    'xHTz~W6YWfN1hHj<-|wiNLKUd0U^j{t4}kWN3!z7_v3>9YR|73bl;dF6%%7GTti#j4U9XvnN7%j)*z>>ty1PE!J#=J)mu<-H_H~h'
    'NzI2B(Ov@zQK~p$8PeP(7+~eFd1*I{PXbi=*aWK{ki9ox;zuz@Ed?ByJ>z^DPLO_FhCI1|x3p}e8gIwhVn&JZ^Mh_z<ga6iu?dSa'
    'DX64hYXrC@C^9)PiWK4MbgkQI2-GQcY2A%u4iQ4xkyQuKB*PYkB$3gxZ7)8DH@pVcEgwqnoxF~CtD^T|2iU;|p{2xaY!T&I=yzDO'
    'x$JLCOupP+*4}*iR&(gX40v&dot|%<S}^W+x2T#yxJ<Nry~K`6NLj=<Z8M7Lt#-e-fWtwrkm+|(+Zg!oV62z8X@JK6Gf`bt-ZGp1'
    '!Nmk`Sma1kH$1p$vtwEM9>h>F&yl6p8#nSp<<f9T+>a%GWY}K21#P_1CPj=YWQKf9&}BR~N|3dpMOLR|K5|Jb;<d$r?^psQ23n@x'
    'Xz7(-|JwX7Yh(kCG5}P?T@=!1><&u;Z3hT8kso~M!RM};^Ypw!v`dNNY8{)0vReIV$y7?hdR#QJ6a}CuU?a=!K_r{+-j26lv9DL-'
    'wIkW5uQb2d`<Sf_-s-3VOUog<^BbV#g6=G+TnV;r)LPp&%&_TVUvCTvtC=#i4d6sxPm1#^(_`DkfC3*s@gSZbVJd-Df~x^YSu1E&'
    '0-Zgk#(Ji&3yxak3sZ;GePC+)op*Dx^q7)ZYdC7^mu4Q#ft^4JU6DAKrldNBP%)2qyP7q(yS5z-@ea25C0E$%_AOYU$#3IDmrP5$'
    '|FNv&t3l2)vdsa=hfW<EO2q9x$|sQ_R!iqj2v}TaN0HGGx`4p!sl^We0NpH3EaEZ8Cv4;Fu;yh=c2c`XAx}<U!CaEhp@94L`gcP-'
    'p*lzDa~Le!&T*Ie&f3qhd>3^kubK<ftX5yU+gEkzh~C{Un762j;}WhtS5G|V13FV@#7H+}BhbFRh&ObH9C|tKaYi<ubq8+<YfBG6'
    'l0~8UD`8sHEDY+cYh1VC0(Y&=bst7+-E6U$@fn;9To5Kd#cyV3{LwRVwTb%;Cy<eQITK&`NIKI1Zu_;r3zSDybHqYCzUSzE`2Had'
    'D=eQox<^DAnnOtUV1ZHDKot54<jbVT?}Cy*wi{}!0)eL<##8A1^CU*;*Dp0u>uSd~-fAfbklwTaFO7c=0KAnnqQ)8>-jrQFMlsL#'
    '&Lqx@Zr_|`Jlw|_4y`9B>hbaQVS`Jqv6wdib>6?;$&nq!Es+o>x2myDXK?@q;xu;nS?Vo>*jWX!*xon4Vq--DzKw}2n2=#4r;a-x'
    'v(pRyaFe(-_HaQ-f`$k~%-J#nVk<A>4Cp3k<zebCC*JkQY&LJVvc>z44e11ao<UAhuR;k8?}Kudf`b2KPWp877(vmH`(}&R*Mubb'
    'W*GQAPJDrf*K`$)N_KFCh`Nx9NsUoCk_z3y3Yg&(7&qHUjc1x4mj*+jWH_aNW`BzhPF<>VMQZ`E(cgVPR;f^OQM|X-?;2pY+<W#3'
    'o}t#1zxNp^@&XDq;sxt-JcRe+rsbO2*xQ*KTBrkJ-ZNkZW$#=xQ(XvC7zx4CV4OZ}E(?@F<@jK=l_?ALc741>^g7(~d)vcqd632O'
    'HPV7#zU;`41>Nyk)Y7%gSvf9JQq)K6*+X58E|vY8&6y>$DEC)BK4cbED^R_7;@jeqz+rpm;Jw1)BoPcAY9Zt0r=0PJEF?Y%4AM6Q'
    'p3xQvYh+E<Cb(4!A{*cjD9nv<qP7xw=Sc@h;#FXwPgz{6sgyx*`0TA~0@Y!IcNalIw~RoaN#HX~$iz%(dR}Cji9^@#^FF<v2^e&Z'
    'oR?4L?VR|y`{2padUU#Ma6M*Y^sKn{xY)T<9IN?~t_%VH{v(xBHc%9VD@gy-V}CcM84L=CuRySMP>J(RUWGYnLvm|*%|(DoE@t{D'
    'W4FRJ1pkO9f1N$-#W$Laxor;JtSlpppK;Ml`xVq&iYfBe?vWHyF?2@i>#<xEF|#Ey2r4XHB`6L_IH;DwF+g<}@zJ<aO-1$@Q5F9I'
    '?~697#+DcO(_LqS|C9QoPVGG$*>%r#JpbIvp|Pn4C#<oXezx7+iG3)9#4TbvF8kjrz|q<}8486bG|ENZof*oQP0`ta3)J1LJi?`F'
    '>@ttKR~qR@!A_b~)3`k}ChksHM`)KApXx!+waqv}S6)o`(XmM)`({bq=fSz4t0vU3pve6bV-^9-s>${MIBt7zdWkCOd8AZ>1HS5u'
    '4v-UN{Avokt}+&STtClV&Mlv%eGSriJ(m!_1_qo_-L1|^*%G0jM=`EzfjP7S#-hu(+vE3j6)j4^D#(S;X;lONok)q@6_#VR=0M(%'
    '&Vb=tPELAtXtmP&9Ms;>mhie5AkVc+nVweuRD-So7B49nB};;g!reDdGG9>?n;wfFb}m}&KR<4!+u9U7v2<>0+-<5ZTY;X}N2_lT'
    '%P}jfoIs$VA-=JL?J;S@XBz)F{Tw7lyit2PB8Gz5Gg-AInPb`ca?&+RZDm!Am|h&?mVo@8Cz@}nZdDCxd3TDkpc}Gb>)|==k$){M'
    'b3(S9(M`kEAH8~75_v?t(|B9n)J$%#)}msj+2nXQbAqZX5+BoKk=v>pNo-&D-fdW|j3`qQR%7*y8nEnO(GnvKbD)ZqQ0QGlk*9S!'
    'wXPI<q?lRap;9>_uWi&_R4^pimorI@l}~=PsGh|JCUT_f7-O!bzDt$m_BBh_d1LkG)AR%qf;z&(KCYE3XK7|PFyS@qlf~1<^)?$m'
    '$LS%5Q~(yDSofr;N-);x#9@_;>Q2^zaj$Gu5)5D2IFuMDj|g;}?$_Dj?Fqgipj~Rh_EPwuAdIuUg0*aV9*;gua5Bdu7X~-9tQ213'
    's=PYainmlkN<N)AELJw>f|@JidAi+}Ry&eWEPj{qvWHDDS2`tBWBx~2f6e}i1+;-WF>CvsD)V7aXUvzHKl(ZH76yRrql=2&+Gf;j'
    'b^N^g9hj)I7J=)(n}=d7@O!gUCsGUq)lqpX6PJ*D-3n#7#A@nGyu=^XxKX?IE{Vc$R_D)dwO~>31N3nt09{CCdfyM*aft<dk?7d?'
    'S(m4uDX+hG&O_Q;YLni)#J#pMc$ioW&HL*HI8D`3A=AYz2NXH#W$KYFSJ`mT4Vm3<O=d8i^S#TJB~Pyw)c8+BcY>hS_%&kVAT?Uy'
    '-qu1wOL;wIlgZCnZ5o?AKmI<F`xIl+?EWSEMm+}fwZPc>@Xw@Ha7VQ_a)4H#&=!E^zPOd3k6o8Bz9;N#Mr8{4A6%PRR}}C$c`jug'
    'E-9~d<pTUqDKj-rWC)f8^~?xIQY#~=#J=)Wq>UgJycx^QgoQF?Z;xWf=F19K9W-&IvZJ4pJ^eYor+oLU@j(hTh8JBYuS<9kiSCJ?'
    'O#A`VgedlfQ3;CZR0#*BOR=<LCzb7~K9ODzJdh`a8d^0oAI7y>3qk~t0p}(&wX3<%Q7e^|qgYx(9qsebRU&w#PX3Lq2_jWDKk?ka'
    ';K}*(c-PG(5xBp)-kjL>rQhzf6l5Rg4m?~0CUnh~v2Hi`TRSHLTShTUC|-c)iQ^P*i@LfNnKBqCqhYUrPypmDGxhA7Pewdl$u0_|'
    'dIQo}4=9@B-oU;+;n2*%v80I3%9Er5&wIr|C%8a6ZEzu=DVABN4BWTYlO)cOr<mJV($R9jl&%(O@N0AC>>UZvWl7f9H}r;%B2FkU'
    'fZ1RB(8fCQDkpEsi>F=S(^0N5v>wkx8%C#7)OQ_8o0umR=*UcMh!Tp-)&EN5Dg)o&!q?^{VOnw-?Q;3XhFjo_r05g9hV6Ek%kV#k'
    'g%M2A><xk<mucPE!Wmg}yuO5RZ-TDzABuS-uR3<N4(a0-0n_vu*Ir;Dkd2C*`#56@HMEuyZU4olkf#-UKMCE2ub*jUJJm)G?VQiT'
    'Zm6i8i>TmZ+7eY;*W$=Rvq)1$!yiO~a5w=O$GWIS<<qn!NGQG(7TU+cj^~R&Sxq4-8&bQ;VGCyS<6A=qd$a>=Xg5Z=!LO?ww=8$;'
    ')ZOZ)xwH*q@zK~HlTS-q!k>-%g@`a~saTy(9c*5eE}jC?F<AaHS0=qt$c>di;Ash3uJoQka>zyWPgZgVeGW$Dqbi?^#WMhdX(~V`'
    '6=eFDO@`s0T@7&UfJ$L)K`k?~)Y~q3cu63s*Wh$YyIJP`H0xHQ`d0cAFs5ISC9Rbo%I+(`)5RSmldl$zszQ!|T^G<5F-u10C9c<l'
    '&XYYDkB%Aa%viXmZ2{lG1pqHBv<RYo(f3woVm6Hdx-j#%ynA^#s^$0Op3Ox}UXUU>&1@pS?rBioy+ScO`%R4Huo_7XPnVwYp=P%Q'
    'rQU@U7tIa=jEG9d|L-sSz5gUH=EX?bxJvGxW}CnleR9Ho@0sGqyUhXrY~pJ?8|6pgyw^~b@Ji74+#zN6=_j3faM#AJ0#qp4oV=OG'
    'wsJMVUK`a|kXTo?X`H=BV?Z<Im+sWg6bxA3GX$j*_MJdWJh{`c)X2BF2%g)x5Q_Mu2+r850n;mFF^$4VHHCVtXt2-lALC3zHvEZm'
    '1z|KgrC!j~faE%=U34RMz~&i2Y_Yj<n#5a06d1E};Bw7BjJ#>4%{F6)t<iYFI=s)_8oCN{wpx?t^?z0@GA!K=sv9Q0-1MAyfL;7m'
    'A^m*V&+xIex^Ig~Bd=3-g=9xM#rH%wkSib=<3a7t44Yz_=<(^H(X)^cg8yypNZ>5xCg%wDISgHxA1pqQ5>1=RCd*I4Voah8)hO~t'
    'Z!%{Vd%8vJ+rzSV9*78{obs*Pm`@u|6%(8t(OaSOhuM``S*v5EFdQLenrqyywAGjGrGD!~QydlH98z+_T8*5k#Tr`0&Gw>rd)WMu'
    '7YVE=`Frxn`f{r7r3BnoF<MxN!y=SycLll~p3Qkt2x`cQ;xR~{LRK+9O1rsn^`HX1X(lDejeV%C%1+`i1(g(ux4!j<a)`&YRe07%'
    'uU;vWyA9k22v~1hp|X}gZ+kC0P4?gDV5)7C3rzo^**g|hu}95-bLIm&2oYY14redld_A8pxXtgd5@eDTw>(k+IxWIqbwyCB>3h%T'
    'N@NJPojOq6#DsK3z+GaeE%$`oUh(2MGB4`;(5@Q015NMtdW{$L#AXbkh))sqj_l!;e()Cw)oW`L647vKr5z+slKHu9zHWe*@kKyb'
    '7^27}s-`=d#_IejS>0)>+Bh<MO4w9a#u&ZJ>mmWthq_B<756$E(SaHh7C__x%HG@0ov!q)soB=0L?eRpgCTp8TXz$7EPm6xaSsV)'
    '6g9xPJF8a4SVh2P(LGTDginr1d%F<9sTsw;*$er}1&xryVp9@IJ8*<{Uz{UJ|IXbV%kyT!diQ7=<|3iPHlQw54)kc35rA)wxtV8g'
    'ZDE%1*ADJRH_uSYQg&1x&A}eq2EtOzB2ydE<X*ZC5&t|pQ;)Pp0pNPy#7@9Wvo$w86*!fIMk`tq6y(i%-?IegnIX3sm;s#&q6xEg'
    'SM<C!DF+QUJA!;v>D|bB$}8VOVRT4B4cn>Gs#wQgqES~1GANB)T7f(>U)ePqp5V3R7EZ?wrY$RZ75F|}P;mGz&W5CS*<A^Le6a|Q'
    'i<~1mYQqY`Q1a}Gi5GD*fwMT+qTcf(D#UqTbnGJ+q+<xF_^z@(8@o<Wr!311E%=!{F*fDCeq7GE;s3fm1%~7@YYCrX)@KRTy>Vd!'
    'Jr~E$`JB#~e0q3IrY|OkxaNV^J9QbgC{&hB&;EU)yEN-$=`a;sJls!8lBI1ihy@v%_Xp@y6yghr>FmcZ#nJ$~zxjP->03|Dswye$'
    '+nTWzKuYP|%hX%TxqBYpqVk`ov>`D9?~IOEvOuk@KqY<UCl*Km6r!03&-A-uch>D0kY^B>awZNrnFnUJN{Y%nN#X*1fj9|TcJO$r'
    'pPeEKAq#s1Qd&lS1Zy|QEG_m#pB)}XkRnDW-<?dB0cosZ5|ZzD%SE7^996~w^<0E1GnB|cT{7n>;DvdBmFa-Gn?4n`&l`JL6;786'
    '`%uHB6VhWY1AQ}6auPf9#458Ise=016z8yTdpcCm#Wna9U9&s@-%eZiLU=(&ts4dHcJt%|3AZ#Ea^qz=c0GeF(60|fUQzl}dC%2e'
    '116&&)Y63t5}0I(?dOwH>mF3R<Ub1(lwUdzySP^nLB)KJrANp&ilCs^33FlXc8nA7pPUQ|(lNd1KfSTIJ&Qpju(;$HnDl&b^i9zX'
    'UaApKk&bev^1L1=^DkDU0jqBxNxvg08yHk_n@!0|C+HjaOi<7g0jLN&^E=?$9>QQGPzrs6HW&XP4jnX_cX}fJr3pcX$M7k`hu8@y'
    'uDdVK8rF1i|4lOJC6>EXFArJ(2B@o@6({gU4(^d~Qt}bMgbtd~9+dqw5MvPMv(n~X%rq2dQ2ux{1knU@LNf@-x1f`UK272f`H&2v'
    'hf>ctn<UJAyq#7(e@oA7?n*yZlJAhk3F@2ndUJO!o}tnRLR7nA#*HL7AiFP9<W$Q(OL?<z-`E1Qh~=brbX{9c$S*h~I-#YkI*9?Y'
    'e02wC{0NtW9^Vbu13~sT-c;JlWVVQ}nKkW_^UE5fs-!srZfY+ts7A&T)m>7057y4sZTMV3;t*w>BasD`z&FCvJRSX7G4A-F44jzx'
    '9R69*Szs|7t%;x6VFd>K4(|6@ZM~W{f-_EK(1MUSDZ95uQq3;dO)a#mWr~t_zGK{>LAAHyv!M0TO-N8M+<AaJ`4*;L3e!Qdlkm}('
    'N1B+yWb;t7c-T2(gtOVAQVS%T+p%T<WE{qxaZByVIA26>*Q1YBJykE$l{akHht}3EVD><}S+s-8QMMZJc>ZTnC$S9YY#u*_lYVI|'
    'tq#PWuw1N+X!`{(K1V{vr>x_>BPHn5qt!?c@lqE?*#ZmC%_cNm<UU^23Nwg&L}NMlzu_zI4}(wU1iENkzZ+M{szX;;fU`u=)4&Ig'
    '*Nw+{;Foqjg5;t>o@)1nY||g8kyy`-n$Vw!dnN+M%{G2#4vEovum-ITr+|>%mS-&!718#naUaaQ;HCNlrASrRY#J0N_!_KQR8*Jd'
    ')G=f1c%#QGVMg+;ft}1CUOW+5HuJB-a5#+xmgsg?;p{koAM@l2lGy#C`7hqeTL~&GFI7QU41jgoXHSJTlH_|Iv^<pN3VPQq_aOX#'
    '-%oaneFsbFJ6fG-KDNCu`@0$&a#A;82yLXo3O$XhyQVK9a+vGfp&<ix21!8ewxE^#ZA0jR<-7|Q<nkQ(AD_J(`}rNyogz4!VR!6R'
    '#G_ow{DPc9XfjD3-96QvuRog1k54%8NJKsJYOmElVKD`-?BdTdx}sESK>*ZgeSFzKC<umhZz6TN6abwq5HdlR|4%!R_am$n-ngf7'
    'q-PqAh_<wyxT6Q-JQ-DkyX;@jb@_%;^w|m-z0b{%+AX*Us)HmyW~W~m5oU42ZNwn*#7=8>Z6vV9^M!$fUII8fm1RtAue(J1JA<r~'
    '7Yt6LoK@qSkx1<LcD@YMakdQk(mKlAl>L=C<rFsBRO<BtZfGk+l>b3DzLFzm6n%0l*~1M}s6Z0{TZ1?IVS{$ha$}?TyN5#(4w#vy'
    'Xx9PuGZpt@Mq#p7y_1rT%4uT>xqajmolDq+8T<T16QnbX##vM!kWAYynNOlV7X5DTGVb?;mUs8B*ggeE^>{|K?A6cDSELQvgwo3L'
    'Cc>7k@1yz?aGZhtX{|j#&iZA&M!ERA07)FzYad)L!=FjeI=M5=XiZ(!Q&~OZV4LU`wv{Y$Ul_j{P%LGc**Fjni@2{xt-EZu+Wcp0'
    ')x<H@iB^9!+#g$w{a*jfY4z?CXEF2J@cEIa!r`c)uc1izslPcVtvrDS8-XoA!xY7htF7e)qYVDXZrth}k7;dXOy{LpC9l^arp>Ms'
    '`q-FlQR+Md_jr7$od^8CyPN>L$A|q5A4P)ocN*@AhFK0pl3sNl{dO^By@R6Xbe>@Tmfk0avOFdfsF2mhKQ>hs#SOFJ=*ha-BdIQf'
    'kU`!?%@?MB!kFLzuX!&r(!d82P%m0q=5g7`A@SE|zBfZMD49>{UIIyXX1J~$ofUcHGWLUL(94u?V{&Sa!xYR7aQL{8|7)8tH0maN'
    'aXf|TKL1X*d}<S19+;}Lx-6S+X^AmMWKP%Skw?FiEV$(zzsLh&r{~&X#lVEkYondwEdpVL;1Mc=?jtZv^373q51&-Ll%~(?Xc+gv'
    'gabFblipvCqnK~U82iJ;?ZgXcwvHVjw^RwnP&D5|8fh*EXUR~}XW#h!DbP&0Q?3>!8#ymo-&uM@{1bZ4<5{Cc<S^DcN>Akj-ahWF'
    '5e*qIa%YlAFc_5a!pTWEMHpbN0)cIcNXv^8bNObaNw828eP*2aJg!MBKCk4ohx3_IUJfi%7kl)oF6XF)iIN=TdP5nS*k^Z30J`k<'
    'w(W^QK2kdnX0GIIp<kY<Of9Vvc6$~O`ziDP-O#)rBYXfz*v;r$tuf%^bD!fD)~jK%?tyloh)=ob5D@t+)FcJeZ?&l1O@oR|gaw;M'
    '7Z)ai7p;i0UP?WDex7$$B;-ql7}>Wm(#s#}%yf&pQ?H&;L>QqP&95PFIQ^m`X3AyMr(?G#Frj46fs8>{Yp`&35MsouO}5|P&BIog'
    'HTPw)2sN9UxOP4S980-2?|;p%?|=&X4iBmIqxJ70)ycKBK^xJmg!z$wAzrF`gPf;wHsRPvS(KEEjG`@q@;_!l=RqQH)_*PzjcoKI'
    'W-Y%Amiwm(pJ#pBP~PNGnSv?JrThaA<h<;b%2V_<c<|^==MGcA<INH%&`0a@)-sU3Q;l!c1BpK7^)Gy$z$_qmP+_jAdBc&(DbXk^'
    '(57tO$3BEqB9Z00Wk~2l4DUiBXLoP!gm}8F%gIg1bCU0bXZSA)4rE}cHKB8IBJdvU8bhB|jJq$_*#%CmCZep0Jm(y1ZzJFro(q)6'
    'QEnoH0+G=_l<;-eXESH>n(k+$3PpnEL~`ccK^~RvBzh1|`B#2Kq}0-4Wp+6>Gjeh9b;UX2)Rl0yy1l!XqUYE%-b}EY1W#z?a6E#j'
    'Maj|3GhH<j5{M*@(Iobu8o#Gi^OZC^xPfj<%v^aQxlzdL0x$cYp07N>MEIFy>qiohCN-H151@A;eM8X7+Dgn;INoY(uKg$4@sM=G'
    '(dd1MbyM-(-qihTBqS(en-gUA?+Ev0qc{+?9T#uAUhTb-VPm3C{h7(A9tpy_x0!(B&+P20MSYK8sRlwTmu-}y34b>tj!aBl0X4-H'
    'D7FBS+E!_I?gwZ(;DIpvoKG3@S_HJu$d+V}Ec<L#UoB1Lr1ZCG{z5;tIiDS%h94R;SJknkf&fi^2R}}T#hwO%#g)R9laSZ9K@Q{x'
    '90=A0t>D1<fK^1ii`C$;Yg)!f(rnm{U;XlMt+f@R@R037aIt}I-w85jIak~$r3y6JZzsbL+pTg??4tu^+1boGH>dVDI*6_en{5Or'
    '6|Zi$1)s?HU~_O5d~O(88Hj%`$U=Q>Bv@>9K`FCY&L{*V6!AI$zhP{8ImrEbH;gkFh#TR6xXa0@d6LGfu<nQoxTY!ALGf!b^Zj3r'
    '849iSG_R;zY1)4XjIAh2?mYm#8Tik*j67YPZNQUL>BU#tP`5WFN^194>*v-u-R~Q2(kRk&Gc!$$FXWK%yA;Uxy)&{YYnCAUw}EBy'
    'hgwK?tCdq|-KyseI4r9G?@lT6dlDqQ&#`Dv`G}IdjphL|E)VOE*@btY0fPhtudTeiQN>@8_zVB>dKNq2yg#;mI<LF+fxk;bH404Y'
    '?$7%a^BI549FZ_SE)Ia6d-R}jr4n{Wt8AIo8dn=FF5RSeTda69P%p$4vZN$~woqm=yiNSb4vx@H7;U12(CDa-ALluNZ&SG4h1+%k'
    '^Y5-AO4nG#qecDm0SEU-sU<{97C)kDjg%Rs+OJuMMMt7fR_)Gj9XIl%vkDbA<*t0GXEo$IE_XmDm#N^^F#*O{3CMrZ=Xh6><De7|'
    'q?SW=)uv(xH%RyQa3@!y2vx3YJigv&QL)|*$4?4B{sr|VowdnyA^C+;a{0d)j>qXn8^{|%Nc0=#+chA;dzl0*kBn>>t5Nd5d9D#F'
    'AcQOzx%EWEuyD~j$KRWs-L_-kjr|;&PfLCRnc}gzXy38F8+n<+e_L`T3o@CNRToAz^q@aOPIpKHi_OeanuXgm6$PYu#xDH^S47*d'
    '2YcgLB}Kl*!LQ<)dRv}Z;g_znkZQzuc27Tt@?YR5?YL}64cndD7>?EAU0$_x4`&IX<p%oGlOa9P87{_+0lk^=?M!V%u8{kUVJnjL'
    '!-%CSolJEF^0jT|Aygi^f89oE6{4fD)-2#R-!<_x_yN|nhqkFA*tTPCJ4V+MOI#%r?kfh|-Fm$WE6^~+=PE0Vb$jDR5Bw&?rlFF7'
    '@7CYO09SNqE3(=D!vv|>!&}MLvx!@+4cc=2*4R|w;?$y+LQ!JCcW2CqE0H2!vRU^w)UjrQ3KE%9vhT$+`B%EA;)krVO?hjI^bBO2'
    'opY2q)5XcCxO^$l_=nBe%!|2t7q<OF2P)-}?e&2k&>~dKifp`F&!47P)?+S8%iYKjfv>odyDEv|(w;{p-;w+cIR~@AGcPcV)1oZa'
    'p&#9q{pUbbB}iYl{e1m5n+Cp*v4z}B3OYR08=wiCsc3nS4(&*0F0f`iv-U3SnMeqhr;L!944nkW2oQ%6kYnkzsh$GyYOdgK5s#=g'
    'Pyb`OJ^>e%siGYiM8B$Ssnn392!&7{cd|`wrG_0`SL$j`N#ZwZ_Q*C7ozc^6QS}DcZ>#L@%OG0#4MHG-6v?%LF&PqIrUt16*!Z`D'
    'GasRFF1wNNn$4JzZj<Bw$%r10g{(K^?(W5G4FqIQ67m)bPA(gxBLk;=AAy}*A(cN;A&y)Dm@}jHs>r<fNdhf81)<fhgQ4j$s<Nli'
    'n(IUp@d(^BR=j`&G4Dlo4m-k@!LHr%i@1))!QYu1>?H9W%aO|lu^xP5@~bZYj>SpBUK+P`<^8Jaz8Q+z{>T@8R7(I-fm{Fg%l$o_'
    '`mL8Gycw8ekcuJt$6L`dzLdtf(Z;6R8zf>*gcV<XpgiOy<jADIQ|5(+t2Dh-KEczyql!TLgR4+*+fO2X6=z><r0e({3M9m(VoXnh'
    '?Y?%6j==|LIea6$*v~bZY{pyx${Tcp<d(?w6Wb%=r3W24C|<J48rwyKH$auH&Z0J&J~%0FYL+j?*BWDl-XR?u=?~<Txzg}HfuQjP'
    'do5oy=e_Xw&$UE8t+{W`8@1M~q5tx4&-$BZn}`vNQzeGn@I`bEsr%J;;@;-D|2Rv3?=^F8IpQxV;?ft#RT?1_UhRHd5qJGBZZcYX'
    'K0a=*2`#jz?nT>Vl9oP5WTQo>`@VoAXU2HXf`o))PiSQR!TFSlbb^hD)ElkxZr^G%;1dH9i~)j!OPY;eBeGk`90N>MF%>wr+}5+7'
    'c)eeMWx;Q5Bu@T$AoX9Erl34e6+WO8KA(yGR2+W$%~E_-p}rGFbSyxUrfshgAV~8W38xO6B<cxq+^u!p(5vWP4IaNjTiU;4Dy2gK'
    'X@s!~<jJ;D?J%GpdI)-fDlc#VO_sW>o^W7MdculM!Gr-4n$rQdI@{A?1?_i=`|nS0OYF67A>h^_g@6K*q(IS?up#x(^Q_87TAunI'
    '`=S#{U>YZZPe5*e>BVmpuj7%BCASwBrKYdh@Ip20Ek?Jx&oBo~&#2Y?4~SC*@9I}y9<{k?IlpxX`b>rPul`1|kVSxH3&Q5!dTUV('
    '8M(ysfz^8^^|@I|?u#2#xaGgs+yLCb9e<lrW*bTIN#FP~d=++o5U)3p&b3ZxV4?*kOef-OuNBXy?D17#^8XS^x`P+hlaLqbA-`HI'
    '4}F@tS<3S*XsdD}ljWP$$jr+ZM8l}S&f3RlzE6w_?Scu1QV$-|x%t69Gqt?@=C7{@3*M|htp!nytl%Deh?yq!|5~3Y-L;m*=0MT6'
    'exoaI;U&{*5<5?cA2td4<MGKLDv$y4P{zew08&)cr-zSK6@$El5m1XNW`JojpbV)Nk2v*&Q&gCsT(i)*Pgtc!3E>{R-H*6?%4F82'
    'bh13$aGbpee+tny-Zle}QemD^9-H7i<Fp-brddq=iuz)9b{oEt)VumzhQZZurvUceyq!WjFB<AUrpzJ9`M(CPpA;XAcKDvB`#~4h'
    'iT{Hspw+%WbK(tCIq<YPaj{mGAB#oo+lMfnYG^}1tc*n!&Z;UO8zOCS$GL{c-uiO4!uZ-mb?R@XJ>j-=g9tR>v)O>hOwUQ?-OxMR'
    '=7>P=&-<FbWtVvnz&kP_MM*hDB)KT9Bq}-yYKxeM{wy78ia{ttHhZXsT{OaZC=Gr9eq5ZGTm(yYrbpLWONlKvivcUM;9OWRm^7HF'
    'Kg4J+^yUv>d9pV6gwJfCu?g2f_v0_r_(y@`iQ(|$Q*;f+m)@xMO(tz<IDo99OQtLXTWZ~fkNPg_Mv;~kyo2#>D0^z>xZ=PqRje^v'
    '{-41AKNbr&Om5eI6s}Q*RprN{$;#yhF#k+Q?^YDQ7w&rj@R5om3AKOOCWTB1`t05&ecrQ@!ZmW3Gx|^YCm$j(1S^hxD`pKh7vSA1'
    ';rrO6&S{2%Ho<|DzxM9ppLw%dlA}9cLG3%_VyMN3&PrWOV;&xK&o##!<Ks-+%iZ9iT*)Wo=`$3>#g=~M39)l|06vdn1j3-b4|E~@'
    'lTb+n&Z@{n^DQZ84ks+>;tBTkhWU|2+ZQY&gSlWOej)|UdR8fFX*@#(D&E_fj!v_cml0r64sd&+-S=xV5`)2v&2XU!6*n}QlBym&'
    'k)tXzqJ1pB>5`!)kW^)ciidthTHQP##MuKuM$|+=<2^6OP$28c&gx>_NWZ6tdNCce#pnhlOkAC})sZnNhufhGk3f8VtDad!7Kvca'
    'sVBl5n{jb5_4^>-^V)otjhm?E5)80;^6tN~VMlOxvX;-GT9RF>N{J4Kbll#*I*UbkLef_0xZJ`2yG0%%nEFKKKrp#^-W?q$KcS!`'
    'xIKLygOHsHOZm8X&<3JI=aS$XgL?LRB>bv7qt8h5U@hQLUUn_PuYrR-;i`Ee2=?*QFzYrLJ7}SV7js&wAvE79Hy|IQsXj!#UUP+k'
    '^LF0dt^syF?FfxucG(~|T<h6bR%eYJR<>gh8Lto6WqlLP*%OaEQkc#C*o7kSZ}II&m?ICv+frbAq5{{*{hQrEEk!(@od^wuz9=Xz'
    '0?|ko+(G9&%(#szy0qT-SQ&`kzU!aPR}}hVBASFMXN`ei0W9uT!$!9LTd>%XUsCy-O=WEij;O9+Fo1&2ljrp0;|$m12z4UEvSAKZ'
    'v`9F2SXPuqoVM*zSv`4~44o8MJ&vFm-c<C<8N(t3x?n!}d8iL`V(~0L@Kv5O&QB{U5MC!6M$mc?Q#KZzX?xLo&_HnN^H)6*RLaCx'
    'CtQCFWAsU9GjvE3Ys=d>jb39O3}G<4N(OG`J#q1b^Lk=7yiOL3m0Ugwk+<{bQ~+=4SpFwWC_da;n<OCa4bgj|f^2$9J~h6!SSbA|'
    'kY@#|d)bWlpGEc_1I9rdpCcNm;t0esiG(LF-M*!qF$8RGjGw{_kYfmZy`{)V%o>KcE+l%4b^D$Enwgw9WBa5z+AieKdNp_)m4R=h'
    'N_Wh(z&-@#P{zzACsQMRvilR3J|byHu~=Vx9pjlB1i%wn4pbEyFaH_Tdxs+inEeg5z<N9W9?#yPbpl&WCaizz-8Sn2)McC{iwJE4'
    'P551XuFIH{qv!NFlLKJWDx(4lKT__DOj3HBNEBcZi_Kf>WnN97cq&4xO&Y?=WUY}No*H3l9s@WV|HkJ~2nr&HJu@bD3iCIIsv00Y'
    '7~TzdL^#pk3zlzCisy(};w-Ep1J4lceg{NAER4iN95{PFeD}ce%q8BirPHZ+W*J?%A$2%k0R!)2K68YC1;Afv!q!Y_g5=UOX&~ym'
    'G)`;&k;WeEz{@6UBYc?gZrwvd;bYN!nIHRo=CV)tM8GCnc7x_tK>Os__Cu4J@34PMy_IofE172qO?ORy-@2Cl%0T#`u~VpR4KK$z'
    '3CAR99V54EMU+ZcnQ3PR(ZRQ2_X`L)S4)fF6CN0sRV!r_9qv@2*ZQDVw%t8Ar8l&Av@oEG1b}+~-DX)a<#b+lKe}eBJI4LDA11`)'
    '@%V6alZuKz)iv2T1))4I$)mMowbfhy>yX<sCkr0Uu2V(4DinNeCD$t;HjLlVl%%^y&D0&Zx@MP|U}R48eLXsa&5r>HX{2}7MP{DX'
    'TawXV<9|&iogC-TQIL<GgG4h0A=R!T`vHk{K`$O(q5ST;rEd+qz410)usdAE_(K#UXQN7Z_tb>8on*cCw#U|f*uUie5hlo!IHV}f'
    't~o%HortHEqPJruAviL$)UK_?@t4ekxGtK{J!(Gx4#yvLW7P(<K7bDiCe<fI$}#C;!*=6?A3M~EeeH+_9j>u?b-D=pCV72nZTXPF'
    '>w2^#r-!Xv#%=Xb!Iu-5-z=%eA-|7#FD%11%1;4tfz3T74j@F{qJ=Z%*?eZ*`sfh{VvQ8Z?+es`{N(wey(@|f5VHUg&LU%z=>wBn'
    '?W#?58>Kc@ba=8go_%{bND<u<5LzX4qzf{?U*{&ZR&3lIOGdF+IgdCq`}8DsX%e6pI-^+{F@3Sk+95ud*#k&?L`#G?{~E|2<cWo)'
    'S<!k>dWo1akk4lU#sjoxzSOLk9Y&EA_k}6dEa5v;*k?(>OXHIPAuDA=fYZkH6pi=B+J<wpsjoduZP|j9qV}l22DR<q^KgoAfipCA'
    '(Dzsj;?Lb$j6=Qrba2ihbC7L%>UMBC;jNQNQ_KlLKh#gsYs^`C(5v)&Jdd!G8Q;{?e&R>L#x|O%RH+SWSPT5xu(TmRNtUWESm|?p'
    'P~QV2lR5vCOTET(N=%tT%7hxcyA{J-9~@iAac|rjdW46@lhwO#iU?Cx$zePvaIpQ?_mTwk`)>_pXmt}_e(xz-kUD`g^3tsA>?7B!'
    ';RIgvWn*>y;YKSU$`12_Dod{zgSxmv5MA44^u`E@wSg%-)9m>n<~)=SMgb7Ca_{p1j^mVq54)E9KEPsd?KVt#b_p-@L04!0FzeKz'
    'VLs-Qk4Ocr79P-eH2MNoX34)i+I%OlEewI^fZCAJmHOQ??K7zpx$=(4FIMBX;=>b_Dq`-!$qONv4E)G2tv9oT=HF>*pu#V^HYHf!'
    'E;Dz30s@h1yG^-7!Ti<ht86(X4W7HvdrMmRj5fgf6O_l1bOoj5M|w1-zBNk(q!fY?K`|j=VSa^4o5xVj&#qUpN_7cv1|3CviEOL#'
    '<GblDOPmNVjl_|p9Yu5r+=#JVuq((WKkh(34VJ3f7@8*#-XKzb3{po}`VMEK;`hWNAn<w~6CyvQ_8j`K_Xu}bds8$xp!Y1!M!IE='
    '0y*?nT_b|we)oulZ16^c+>98uq`M|-BQ&C}%I6hP;4~xO%-u;;Yh2b;R*w=T!#~UL{CdxVQyFLaU=1xG2LpcRj;)2TZGjb2<B}iP'
    '*<eiUG2wiw(_L`(|6QdjrI)N(Un~J9VAYAnIO_<1D_?fgoJ>_{5Q!uWIrryd+EA)!*vCba;?hqF8L0EW%2rO$rle{)B_@GgsbtUr'
    'tyn6ttGu}&OQLK0$}Ca<^*>(3Co>Z$7e2z_FP0t#z<PnOY&)U&MMU4HjUS4c(84$HCBA3uSwwUebJ<Y$ekNP!Rl%qqyawsnjy^U~'
    '<C+<^_GA3SflH)7rH+;^k(ei@#XDv;3@(i^j{BY&?L6LnvxPa1+OE!cCJ=!znddyyJ`$8nedfQp6*$c?^=gwJZM_vIH$RPK2l#zT'
    'bf>5r8xpfCEMyB^XHB<%eid%z7*iwc1ZbhNc7+420fo|_e3eg|A|vpZa*qg-s4C^eF?xtR9ZxDCbe`~=hsQC>@w52U90e*?fK?7*'
    '3^1WR00000786}_hyaTU00EJ+3F4PV!_e6@vBYQl0ssI200dcD'
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


# ---------------------------------------------------------- Sith Ewok 3 ----

# Sith Ewok 3: Sith Ewok 2 (the same frames, the same size) with moves drawn
# from the side, facing right (mirrored facing left), by an artist panel:
# GRAB 0..5, the Force grab (his paw out, the hilt flying off his belt into
# it, both paws on it, settling into his lighting-up frame 1, where the ignite
# frames go on from their second); STOW 0..2, put away by hand after the
# blade has gone in (the hilt tipped down to the belt, clipped on, standing);
# SWING 0..5, one swing right then left with glowing trails, lit; ZAP 0..3,
# blue-white force lightning from both paws (a wind-up, then a loop); LIT_ZAP
# 0..3, from his free paw with the saber lit. GRAB and STOW 181 x 240, SWING
# 301 x 240, ZAP and LIT_ZAP 421 x 240, his body as Sith Ewok 2's frames place
# it on the middle column, feet on row 238. Ten new colours: the bolts' white
# cores and blue to violet edges (drawn even in the dark) and their haze
# (light added). Baked as palette indices (lzma + base85), decoded at import.

SEWOK3_NEW_COLOURS = {
    'Ȁ': (236, 246, 255),
    'ȁ': (150, 206, 255),
    'Ȃ': (64, 128, 255),
    'ȃ': (124, 88, 238),
    'Ȅ': (72, 46, 172),
    'ȅ': (40, 72, 176),
    'Ȇ': (20, 38, 108),
    'ȇ': (10, 18, 58),
    'Ȉ': (5, 8, 30),
    'ȋ': (34, 6, 44),
}
SEWOK3_NEW_GLOW = {'ȅ', 'ȇ', 'Ȉ', 'ȋ', 'Ȇ'}
SEWOK3_NEW_SHINE = {'Ȁ', 'ȃ', 'Ȅ', 'ȁ', 'Ȃ'}
SEWOK3_KEYS = ' ĀāĂăĄąĆćĈĉĊċČčĎďĐđĒēĔĕĖėĘęĚěĜĝĞğĠġĢģĤĥĦħĨĩĪīĬĭĮįİıĲĳĴĵĶķĸĹĺĻļĽľĿŀŁłŃńŅņŇňŉŊŋŌōŎŏŐőŒœŔŕŖŗŘřŚśŜŝŞşŠšŢţŤťŦŧŨũŪūŬŭŮůŰűŲųŴŵŶŷŸŹźŻżŽžſƀƁƂƃƄƅƆƇƈƉƊƋƌƍƎƏƐƑƒƓƔƕƖƗƘƙƚƛƜƝƞƟƠơƢƣƤƥƦƧƨƩƪƫƬƭƮƯưƱƲƳƴƵƶƷƸƹƺƻƼƽƾƿǀǁǂǃǄǅǆǇǈǉǊǋǌǍǎǏǐǑǒǓǔǕǖǗǘǙǚǛǜǝǞǟǠǡǢǣǤǥǦǧǨǩǪǫǬǭǮǯǰȀȁȂȃȄȅȆȇȈȋ'
SEWOK3_INDEX = [
    ('grab', 0, 181, 240, 57, 111, 80, 128),
    ('grab', 1, 181, 240, 57, 111, 94, 128),
    ('grab', 2, 181, 240, 57, 111, 94, 128),
    ('grab', 3, 181, 240, 57, 111, 102, 128),
    ('grab', 4, 181, 240, 57, 111, 89, 128),
    ('grab', 5, 181, 240, 59, 119, 79, 120),
    ('stow', 0, 181, 240, 59, 119, 87, 120),
    ('stow', 1, 181, 240, 57, 111, 66, 128),
    ('stow', 2, 181, 240, 57, 111, 66, 128),
    ('swing', 0, 301, 240, 29, 79, 157, 160),
    ('swing', 1, 301, 240, 80, 15, 157, 224),
    ('swing', 2, 301, 240, 109, 48, 186, 191),
    ('swing', 3, 301, 240, 109, 7, 158, 232),
    ('swing', 4, 301, 240, 7, 70, 179, 169),
    ('swing', 5, 301, 240, 107, 16, 112, 223),
    ('zap', 0, 421, 240, 177, 111, 83, 128),
    ('zap', 1, 421, 240, 177, 111, 199, 128),
    ('zap', 2, 421, 240, 177, 111, 208, 128),
    ('zap', 3, 421, 240, 177, 111, 211, 128),
    ('litzap', 0, 421, 240, 68, 116, 192, 123),
    ('litzap', 1, 421, 240, 67, 116, 311, 123),
    ('litzap', 2, 421, 240, 67, 116, 315, 123),
    ('litzap', 3, 421, 240, 66, 116, 315, 123),
]
SEWOK3_DATA = (
    '{Wp48S^xk9=GL@E0stWa8~^|S5YJf5=h0u^d|dzlZWc*$;W&Z8)q~p;*3pD>5isr6#vq-BnSa@8|4Ump|39=V1>#F_)}dVr3+Ilg'
    'XF72rc`5fyYWhx|^$Uj1Uu5x&>aR+;0k}e}j|qIV;sBH)(b)Ym&t+0JXti|gypbIl%bBo382e`dgE*zH0YZY}tjD&nGwI+Q>g@UP'
    'Pqrzpm`Dw#&USF+OXCJMHN%nBTbdo20vp<^cN7hjD@Je;=I_+hx^<bff|KRtVjF%w9%!Y~M%btzu5x=NFmfex-SK|1o;zL>J))(j'
    '^`?gPW?w^yFd4Iv9#vu#@$x-M&aGlBB)SBL_1xMDmq!-L6w@6!{00efh1u{RU)i;}E&k-JgmE}qEqsw?W(Rhk@aR=XLW^*Qx5~1Z'
    'CUqA`zI<peY2cvlqsnDd>`(7M9I3*K5{QCjoCj0x2%ILQD{F{IiV`#4`o~FCh054@Sx1v)*K6N6r{rSR$}T&c!>)1V-acLBmjbO*'
    'd{Tbb``vROTY$mPp<t9@CO;g0T==&^v@h~?-)XhX3Og-4s*7AIQmp`f_xxn-hn)Oo6xktd1+gxML%%0}Ky22@?F$XRyyxHDcuJWz'
    'EDqBd5V6eflqLhmiH^$gNt;nan3*s{;M*3f?|vH_=FoXdPA3>p+c_Zr{Cex(ZyeRa&^^3RYt&^I*1Et^h2cqQ?K<xF8tBjgKYM;y'
    'RzYFTIm5nTtt}c9YqHr@$d^2=-_r!>QoLncvj&myIyHmBNp;NI6W2>qH?Y__iPKrAu`u-tHSVGs|K3qE(dhYtfAIuv9tf5BkhDGY'
    'FD_4D?5Mng=E!ub7t>@pVOY5sHPjNomZ`9-DOTP~c8^+H5C?}Skw@A14-2HK^YGCw7>sz)07_8+sGfdqd2hJQI%%KRZ(EQl1956q'
    '?@HZug9QKE(<q`x&%TEgo;G!vQFl0n0%a0N7wRUuJb|=LaSl;A_|(mbHnR}KimwY{Mxc?N;m%g`4cr6jHpr&^($}BIxwGnc$V&pq'
    'G4g=z+h6~FZY22@6ee!teNNl9aCsB<CY)1wAA6$v-_S-sWnVWFF(O%OhTGEaG9R4eNn|06jh%Q%9*b-x6<B%I@XeYzyHBlwy!99|'
    ';fFwCF;wPHq-ODra#Yv5&o3KGAeTf=((AN`r8;;WaSp*#WS-mkfl^KqHNJRc3w^wmiC_UNNNjj4TKjRj3mY^s2P`WHvipO8aBT8Q'
    'J*dF;X(aM;eC(hoyiX@mXqV@Bq!ccbA}=jQ*Cv$g;jS|nvlXn`k$TmMCsAYLC~o24+UcHB4>)i$x-CiIs5&yxkU(J4q}syO>nZ{7'
    'qPa~Sn{?KYlFII&J30~4o>CHA&&||^oG!tPWq}4`;M7f9?=zl+hT63-B;bEZz*6<__LIS47Zj1ui3>sR7Vi`yoZAW^+jy<{emA@~'
    'FI&||`qrR>-r%4sFaW3QXb+Dvmq(i_?=>3@yy+~*It3EF$keDbFgn5Y4GR&Aji9W4{k>=DhpUiGv^6I7r9R3$CBR7`gLiIokry!*'
    'e;5|q*Z4H$ICC1YUtZLCeBn0Q45%5TDoDYG)-)#QnTJ=_BfrlXLz$95+RK@63NZ5?P9_$Br1?laX39R{YTKXg7ZHJ4A;W$;P@0MK'
    '%gu3sH4nvpp5pxtA#koLp3~-w%~_RQ3>`xWEKfjn36}6QaUS0+wWLigoH0;Eu6zf|`7Zs?DUFczp{Dselo8`=%o45=Uh1)o!4BgA'
    '76Nol6|wy1A;R4@c4ZkWPkm(@_hWe-$}`V1Ll-m;X+m$5)Iwe>2p9p~cWg3ujJWS!@sf5e1*ZQo=V6Ii3Tk|s&XVw&Z<R`EhR~04'
    '4$N1@MEFSX*r>y0OgTa2@D~clJjSmJ6I%g=p*eeJd-ESV96L+APXtkPPu5=lRbrEKE;{QGV~4?om@5rW{S^NjM7|rrFB9k<Ru|gY'
    'f}BA{!;4t=6L?Ck)IR|#fGnxjd<fZyi+bbos%G+A%eKwO0DJ!umF9d~Y)%wpGleOJ>-xqS>~CW>4nN=kL_ClUB~vpL_expW4&|0K'
    'GDZ-*`@r(0N##>rBHEy{oPXBLRhp>_;yz=S^`Q`<s0C~4<I+l05{KFeS7dMD&eFte=?cq;s3j&G;u!^veVDj|Bt7;fC8lPKl_{}X'
    'T!;*hiAm%6WD)!vXEc}3;3z)1s}Q2wr<`v&omQPqLk#>m5u-0*Nmg{coxFH1R#QRP=~%XvA+EMIVLWqvjUo@zq%nm*nyE}icw}t5'
    '!Pgv8pX8HM)61{*nWkY!btCQn&Xu_YX{r+fRs(+baozdmdDqlveRQ0XMyQZvQI$R6u$JmLZ(<3z!^toyH8U>REB5cGkC!!$=8<<}'
    'H@$7001>x2hcZYMC!kmY$Py`ls_L%VZ?Yz~UYr@E7wai+w=jtNn0~1(C~^c@t`||#F=msnm+XTOGlvuMM<$B#11t{R9=z!uE%ven'
    'KI%L#K~$ResGOJ$y>Z}$)st6Ze^_?dO}#cb!}&3}Y1Wc8VO*qM%;AI1_rW%Nw5Sy<NIP2wtD2Tt7WEVlI2g_XFjqkAOH<BRSJz_Y'
    'ff=@y?_N1JTYgA1TO=L<XV|%Sg4j3v!cV@80j`hl!K3KPrA3<LzBGrIpg)9q7eR#j@V|oO-tkd9{~CoFSvy<&S-2vgp6{EZwi>=t'
    'zq5IS#=E<s5_#Z|R@Or%qv_krPgGml_aq~OUgQPmw9pDHr8}!QM20!;{lD<P5tgKz$|6$PNKnJUt~MrqQAz=EPb<sE9lc1h-Y8#}'
    'iyQx_eGmxR&51z9l3Pahjt@)r%kJ#+pbvU*KgH1?-u1#(+3q-|4b45<fE#_&YG(Q{Y4*Ivtr6jgH-a=yR|qAsKaFo)#Z7%Jv9n2W'
    'yfiHA0d&|<;FvOjWbA}1k!&D_3@!q7W96jJ*?g%m9UzZ)>b1O3OIB_pc-(oT+7Bww4>sN6#RCo*w*qsJ-td`ff87auSY@A(Iw|F!'
    '-2eEp0UQ=*WdX$+4b2wUozK?xX(GowR5*dP3#c%ZWk!|MXOM5mq{XK7mymn1@cJfFvzk5)CLa2?V-&$aB@OZzCtil+mNVw2*+eQY'
    'W!h0fu;K*KbnF=KSgCz;7A}kX@f~-ibCbEnx*6g>6<I@o?E)f%Y0Jb6m?TC7GTWe-$~-6%sX+)_F&u$OvJ#uq%3Z2%nU{Ne%DzAy'
    '|7+8!KK>4MP<1AZKcm8k?F&iS4myoERt_OHaqT%mt07N{uqGVfs;AjSm0sNR1IUPNaX_m(l#y`d0aNbDF^R)h1!T%i^updP%d+;z'
    '$4b_`&d)0rW;-rfj7CSJPx48|l0f!Wv-Fhc`H5W_*-7o)m!IN8b{HWyFv4_(Qz$o5W-L2$MO>HFpN<``D0!O$Z%3xz-<@VzXCR*F'
    'nG!J*P-7#s>Se9xkQz?6A@>6|1+u*!1hsPeK94%%llnw>clE>n7{t%m$<-)lm3%S)W)Y37%jBn;XvQ3yfXk*FJ$;_F;i5J}`9v*r'
    '8MN06O&7f=0U5$Ls%gsg?ykp<x9;x-37PK`DYj>KN=<H+Lx3;pVvwzGVXQh-B}ak=ZfG!~U^tOmL(AHCu7-%IrAOy$n1k|0><FzG'
    '$RavA88aY|zpN*Z&0zQurd&$;?wXl&L)plC?7;v=P?=Q`(!lf;1A+Azp<VoAg6iX1fyitw=%8}gZc*CRx&46mFAe1?)l(g8LBM~g'
    'UGDkgP_Ms7!y0C#xLs6Xy11D9t<3n{G7dzb&gNV2T!Nw}*M|%u0mWy7{h@WB8g*$;c<W|h#;W13ii$!(+1MR}^0vj)lde4Y@G6#o'
    'h~9`{yyl~_$+SyA1o}pk3G38D&IMV7A%{YX)mi3|-RUGTG?a!t<ymLjkd%CjqezSbNHGGc=xE9iGOJQxv3AkF9kdEC)#UOt-~z$%'
    'fzAPtF$FX{@gu1AWsQ04b~7LvPFZAsqXgy@m02>T!N3%Ojh*mUl~0AX$GEUhT8*%z{H?R@Q!Ga%YH3_+xfJEmR@i2c0QyX2C<|(*'
    'NyvE{Jzv^1zeCn!qFHa<ReE%^q2HO|riI?A_duriPfl!dE*|jVhJbuFPk1{V>AfG|sm{O!JAZ+JLWxQIsq*I^qv;eYEH%D4<b~=u'
    'c$_rOzqZP2g-<IK^ih`oJ&Qwn4*?*Tk+jXt#M<s3luxTfBBr#%gdbLX86J}05CDtOqyGqzY-7!i1GTNJZ1>gxGfkjKRu>c*ZNPxR'
    '4OXS6-=D#Fz)`|)8E?J$^r7C3Qkq4J^6l~85@X~0tYk?g;~~LbPbi35<HM+GR#dtsViN1fI;KXioV*(#d457mKyQD!JB`5?QES2v'
    '#5AYf21TPtQgVaY43yH3#y*;LnmRMglzyz@sT3>xaJG+}th8VEr!L(uvWh2epHt)L`r+Mru^Ay9{k%j}Cr6}YeDlvDI%=jKgpYEJ'
    'ufTNGLMVCG0}T}HXAAj|Jx0wY76ju(<U&Vk)s62;UDvK6)eEei`DZ*a?-2fa*d8_0DD$thAclql)Xwnn>{PIvSaH+e3Z&K$sa=}P'
    '+NKSO2u3;5(;~YTjadqS*Cg<x^nDk_nD`5Wg43;^HIkn*RnLk<+qU2PGR*^1O>69Pzo9A(V>+Rt+sOBvEY2L?&Vl$<bT%`BhIn{Q'
    ')~`}_R#Y!&26j#+mzlT}9zj^p2U8S5YFO_gWz2JsS1$6xhF82v!6eGX5kWoBQvkoROS#rmh7)DX^a~2QVzCNGCzWi=rq$|=e(5xR'
    'ENMF3fO(Xnn}4tRChG=J*;iwxt`MtNkq4jiZL@?{Cbp}4B(GN{k-Cds1dOgvI<w}w4W#8W8i^>?+I7<vP?@Gs%a;Z<&Co8-g3il^'
    'jg3~Ufo2G4;5)~l)N{tvND?~HbF*v**vvnNqUh4<RgN;*bUMht+nB=o+lvdGXGvjX6i>;&A0kz72V#FnybeO~gO~es5q+)-!!c~Y'
    'kielo2Y7^QgL6)M8+@MgWv1+R0H7{!91042wrH2OZxq(`)n{ONCw6M)zn#&>31qii>dHjm+k{9azt@RLp!;`k=JG-SdHeDTMgrE5'
    'b%sLN-Dho5u>-`K%tg7n=Ve?m<&R0Ge_^?Hz{la@L}9}jAVTlzF419v97K=nE1dF{SBu}Sa(1qaL(?4J0THA+zZ!Ezv%0{V$sZAT'
    'UAUv_H|ugs%SpxCStH+11ICs1`h^(WT7B0DUI7D?K>tqclAU3~BiKLhCwOpaBaCa`q|31(YQ#z8%He6rUAh~t6P_E<IqUx$`_MkI'
    'PIM>yu)8{~X#*h2j}Fz=#@+a@vic@sMegoK|9+mnnkvO<NC&NCUDiFXS4!!-g05US<vK=DyG#2!uLE9+eQERhuE_aK@ngw+<P4Nz'
    'FcaotrJ<mVTSX>kynqj&1Mqz|2|Nr04O@Ugu|+VjuP(q09KCPlAroDZr<T*~R>1Wdyd<Nuw4)WiX{@ds2L$I2O^#pmEAV_Ln#X$*'
    'ph*=ESUZ1(gdmp4+(UUUT);ozXS<DiAix-OKxfpGN^_#sb{Z6Pg|#}QDv!CGB_3G@X%i+}#$0wm&)sF=r#u&)QXk}ML8$8JwLc3<'
    'qt`K{xuDl^jc5bTAofM;{FdVO2cylB<Jr&@S!6L)+j7I6d<)O`)bpAr1A~?VcKvJ*|I(-lxal3kEY9z2@l|Z2B&x-Dyi<`~UqXN<'
    'zN&~_^(Hz4s_60|%eO@bVsLqw1qNO-a+FQEfT59B_GXMc{VX^Noy)?}g+yGK8TDke2AK*rlx+?Y|8~AqKRQuA7uLj&o`?U7c%@V&'
    '+ty1}{O>3E4yX`7!J3&|ZK!0)2Jgq;bwLd`Q+BZxZ_$ftXyjii?0Lq2q--O;DfB8Q&5tTHAwPMI{MEgFA|&&(b>|%&@D`#Gl?!g$'
    '6(slxj)7Q>1K2!-qP$m10c|K*<H1efk+?Uf{mK@UDA3efnN`jdSHkY#COQVN%|IO*L;$6h60LNeS_ldFCc~!7McBsbu^cz9*ogPB'
    'r>K_^mo$(FUnTZGg;o(bo^3N@GKhM<{DsEt2m%h3o+iTn<tSN`T1{QC^f>)ur>TR1e3X@k->l##+)bi*U#4lm?Y_?ZW%fy4`s?V_'
    'Y4Kj~PLt2iJ;w)*;ASc3V)y~kB|+u6UlEFN<z{g%fDygq<UQZvgGV*ma}Y>IZ%axBE^)`BKBMB~%}0sy2Hb6ejOt8Q?E0PpbFlg>'
    '6}(0VjHW3r0JvL*TBzwDG@9ZQp+3Xmg6__9)Wy!A8<Jm7%?>tVtibC}$(=q^9SavZ8NcGEzh}YFzqpA)2dvpP9#WfsL+qtRJSUky'
    '297J@p(>^|rx*vNnMvcz<Zx7<%{8~e8Lx|<tie_PXXh_J@;EW{eitQMw7lm`19S{}a(R=%Q*_MwBrSglYy!Y7ZKtRd--N9)g=^b^'
    'tz4F6LR+qqv``Wj8~j$c&{Sg&Py4d(=qtm<&b&vS$^V!Q<C|w6#>^qUrlZ8)3ul{hU{}5Bjmg3LD(uxUyB%T7?)zV<nfvrbv*2^q'
    '04$I4la3lV2D~3Xr|7Djb8roIvxFyZBuIsFf?U%Bnti36-gR#;Ll6poak=%U@@!a1U6;+Mdv6WcVXwE@8=vRsHMtv;c;J&dH%U3q'
    'l3=4t&^R-CPBt0zmr`qXu=W*4OWs3LSF!9WiQ05x;r#FZP@VbZV!C#`e8_T%pEios&u!Ijccok<c&zlv#LMVbeVFO7pzx1;*5zy$'
    '$d4|iU$ju=&)sMM*WJrzxITRFpY#S-&IxFGKL9L<t;BqX5#cnDe}v(Lp^{L={mRB!{GNAntoSTz6l-nyDOc7i4Nyqtr^Qv_FZxO&'
    '^x+ErtOCz#&I6I%)!N_xw^Giamy?W4^YN@4TU6RriJoZ-%8NRZQiL4CfbvWHG{qxRdY&)_r+YlaNK@+eDX0FKnz1f&Y<!E;eUk$%'
    '7=JKuB|%^#GljdZNk++XTpFnyOja~;w)vCSL0PqI^S8??Gg*EPMXQ$Q<hq9`uhIYlmLr*^W0PvG5EYbq3ENK8)mViKriRD)wSEHw'
    '@($;d7jSSZ0>0~Vt{j11;_MM-!_5-TWHdFW>Lassbj*X?_Twe~l$^JSNfQnG?*8S}g7B7-Lik=`W{~#}F*u9OFrk_DEm0o`_c3Fl'
    'Dj)l){ve?T$QxXw!U2~q7zq`G@cJ#DGd!)Rwv*zJ2uZ(HqYY`=GXqcck{10IjuNn>j;o3oTnIc|sb->~ZzTXk+eLTT#~a&i2Miha'
    '*5rUJ7~t@X!Fan}l_j#OWQL5ZKHcI{12vY2ygR+?3>Id8_t4Q}*(?UzC*M2XlknbV3EmezfZl2`jE*>sgv(W%&{8Mu9L&VfYNgIY'
    'OMqz-M+$vH;Z@@`086Cd>FBH9-e%1$<kxytS7P|QR68hBBc8ld38%YMz})o}gSan+I?W~!OYfpCaslq>xy;N=^*0)Z215r#bAjJi'
    'ha_91m4;;?yF!j3n6Nfy@UfemfLU=oQGm?F_lFhAmQ7wk42na99?t_c^w8dz*<TH5t!5uZK)=x)=%SK7?VyTQh2U;0k1`iF#yNAN'
    'w_?`-Rqb9_HYzp8Ji_z7P|~7b6&UFz(AQfLwh0tq@cE{izL>f#yJdceNuNy%K)QyfufE@L-c;(bCdI`lsz^DDRCa1f4W;)nPro{T'
    'eljJD8ALNT5j<Pidyv*TP9Nw~cvD22?t?pCR-8!j3!=a|fJ(;~PCT}eIg0+NQHep=K`Pj=_KdlDKEikg?Pf}Y3dK6hox};P`AUE8'
    'Hsj;{(x+v=ALw}Df-=q|i`X%(u>;td+i`cQT=xCj=<*s|OwddrU;6gfmHI)?KDzavawC@6n?Qh~5WK=?D(^u);kf=ST=HsC%J!;i'
    'X-~>)m2}y7va0VgoqiNIBwYIk-g=LJJ3ne1AL@afdY9ky*hOH9L}9vjy8|<<LE^vk-=cj^kWPdN^k_NVyCw2*ChEsZ2-Ae9(#bd3'
    '!142Bsct{quRoHfnuamo^C2b1v%;y)-x|_1S`_={VAQG2h^7uqcfqIn=`*`+#Yl<<piDyJbDHp;HTSWwOk59xDJ5|wUjSh65Mg1E'
    'b@y;wRS-!+m3l)K53sm*nS8<4fntZaxCSqO4A2Ao1?P(5aC)|Ge1qJT`dODP=zDyt9d9*gwZnJ;XSbJ-y4E+SUw<1UDE1b<J$D@w'
    '#kq+SQ~Nw4_hfcPz~<@aXX}v1J?ih7`bMbT4QfJd)}OV)%B1_=u-*5E+A>ZR4t4N(hzUxCZiUvr4Uy=bv%>oL(xLYn)Zl+39?rfP'
    '@<&{aukCFcDCZ3`a#KK7$(ovPa!-85Uf}J#Q#)N_xL!cmoUp_Dr)H&2m4s54Dt&?PF$#G5D6e`g8KJ)CPLp119fPe%`s`S==j}PM'
    'OETV2Ler2ppJ2U{wp?H0xHg8?FDT&X{I*y^9ekh1a9U8XEpncZZUMZWMQmc<i~6*&9-~?dG<4A&HEp(C_D3!{G&Px0*+BlAg=MET'
    'x(A^~v~>GNlOCmvb8{m*<|tB=3_aeEQL)t>L9hjV$1(+RjB%>-do6gNsEPUxrI5Z!sa5EqXeAn(1G3C9mrfLp=e*XozB%e%e1vWm'
    'gwZLTWoXUR^1dV$3w<*&EVjY^lp+d1L0g(Ix25@=Pb3$@15v^{uJ%3$zhC&|J!160qw3QsI`>^U=9`y463Qgv9dvx|LbOLlZd0JI'
    'J&7;!<|GA2f8D@wYOhI&h|@~r^}45*bm5qY_2Kuf`@2ppt}e=r$!y<aB~~u=9eL*v2L7Mbt2p1vk0di(qC1fvl0xtdXpTw*s)ncy'
    '`3FNwRKK<-yZosP%)o{P(iP^$)e2zWZ7eoQ*|(kY>^9|eRd}~yooCoe<O_80Y%_P@X@7HcekIpGXVNC@Y`KB09bX03?>qs6d{#tD'
    '805vy|MTk#LeoA;mDPkY#TWnsb53$peV0O~!g&QEaG&h@a8$T%?evNpGS~oC5_PL$T1qP;R?`L`2%5go0Bty?b=CwtTdiavwYHG~'
    '=V%%4YDO)7K=fn@^2e9IV$OYhfakM5`1;!L6CynwWJ|1n)+Mfg9lT^YIN)wUqwkwxR%!nbSGp?2BGo<<@@enksjN4i@npy1Lnlei'
    '`m-uA%m9tydfHadC3~j%t3O4LT_>6m^zY>XoNkh=@#-_1_4N;I(!yE7{tr3aIlSfF10Z_SU!ke{tiU=_<g5+PD4%y4jw^bD99UBA'
    'R`d60Q%`E5#1fv;`tpreuLD0)LU0$DS#|b$(v<YUT^o{i7*cZ?dxX<X5K>UdKE2Hl9@mK8RT?-40DT8bhY#0iv(ufP>^GF}w<}wC'
    '3X0^PunglHaW(bA%pi;M+ZA|B_?^EZ*0pr=AGW0kdA^+lA6+oWx_ABpq;v$WYrcZl2F@fSbCUvxZoeWb_K&rNm;Sfc1-+3YKUNjz'
    'h_Ubpt%PZ`m7ge!x#pK3_Jt~BC+qrOdCHc{kgCa_MbxV4!WK!p<a0;#m5kK#J|11x-J%6WonTate~MIPlxK_m3OJ%HaM!uS)=hYX'
    'Mxq{4f)@jAV3j$X4OA~p_aZYt1nP7U2=M9W{~JI%Pr;=C^y^S^+5YGy!3*WcCo?3L)8JKONlaFRkqAL2*MP?0oQ)s6SHGJcquc8B'
    '%kQSFL(n(op5?J4^&IF}!6ow>Z?vh7Azux^N0Ux3oj1~DTSX`-O);M{W4ESQ3^M-f6I?2I>J~j-$j<sM=!=8k=ZY<jQ{W*NTOk}w'
    'vpfCzpYDJ|=`WRta@~qd*&|$AG&BlkoPUP?vq_e3E*0m!w*j*(K&uF(7=JMXl##N?4dP#RCUgjPL5mhzfk*1PTM=!5()oic2W~~A'
    'V|EACScmuuZGa3{huMme1h;l4O2vF&I(^tUl|n2d8{atOcJZBTb{1P+CJQU&)Swx@*8UeH(TdV3qMyet!Q9;zE6<RTy(zi9m0d2t'
    'R5_lg<;phP*IOa<NNwPJ_o;kqcdQ++$Nzmeo((}hAXI3`3V$qmduk1$tsHnDeYoa;CRHOLFsHcf&>1A+zstY@iJ$#&c5Bv%E89}0'
    'hAyA(8d)#@l`itaUUNi3LXbHaQ7*`clJ}b@YBR$7PSSmh%hSQRXRQ{r0?CLTF9)+zDu@)Kep9zE`ue29{!v_o<4N}9$&KN)PtMl!'
    'HGxtposA|*<fS#Gr^VQ0Z59d+=oXZQTaf#iTCNeiN0A3?1Z@L%in5X*eO++|-U$$;Mv@!ag78Ulz<<9=MyyY27T--rEHtRM;SpLP'
    'Yj*cR0~l(gO?5I<VGPG?c7>*inzh(BkJf$!5`I-fJdbD?`FcV2o&Ps-X{A1KSE~18)&7gZZuW%?{JpRamVLd?&;H4?^wJ|dJe(6H'
    '?g~*T+9lv9-s|I`YoSZUgz57})ZpurI5j7P8bBPt8|~Q6dYJTVN|@b;SGr7UZZm=^^z92a4|-3$osY#uwIO>=@Se;`%cz*DUAR-<'
    'Gf~cV;Yp}tOTl6^`FONUa;dYO)<tU6&j+;1Ptb+&Mf~eTbga)!2tT+QgG^V|HHO;*im$w_Whlbd?sp@Bc-W$NhNv7VO$&d8YrO)q'
    'isfY<FkeU0(3_{E;M1$<Olq0{@7;gD#<3;2$iWEI;3T5*MU(r;;n31NmH|)>W>fQgne>*BY1QlIie?Llam!5_W)Gp-v*Qp=rJ0!f'
    'fj!74moGU8&XIV0q=-M&FtW@%rt!3EeTzF_fT+tl)$SIz`ZyXcS)BAC0QizF<&374K>cdFt1U&P4ic&dP5Lqx0Uz!@hhK5pqup0$'
    '2N-lVs>X__pU{5y%~X}TcgEQ|as7RTn&E)}GyeKpQ_jXCtStU1kSrY!ug%7oCbgR<o;?dd6eYKRHVAsg8l$ax@1laO7y8b$_@M?z'
    '(kx7OTpnCT@+MK~F~`DnVK4n^Rxt2Tu?rJx;};ND)$86OW*tW-jMO@<sZ|X=90#HzUud*#uATfE)Fs%WT=;ROsiR1JYx~o*TueuS'
    'VX5I4yxqoO+(JhyJ51s$P-u{`@yi%>E(3cpZM_VsH``0mTLH4`u_+fsBT%Y`8fma*;Lo}nDv{g|?0)VBhEkj#^4~M9fSy=JW(9Or'
    'SDMu<!Y$gWk5sn?bYzIvD1>Fg#GQJpncwCA`mE9M{HOg|-WnCXgRgeoIKhOFfkfCFu{!8j_Q?r2&tYhAzdbQ_Ee;7nC~|$T7oaWS'
    'OYWxoh+ie$IFfTE&-8)%yVe6U;3s7^tRM{$@!Mv86X2%Wm{6z^<`=u}Q$7i}&?_HUN%N(jt5=>P5?}|{<v;4yf<~oZ+}Pr~%GdEP'
    'kREl40^(dK8)0Q%K~q9j8QpXaMu&yLgcIGVY3AMb*yIIFg~RT3uN3%A_ePq-eqS;F>Dpf8$8ppgZPuNe^hM(2*v+tOOaWHk*h2aj'
    'Uw3S(T#IGSut2##VZ^Z*JzVP;-OXY5)iB_hBz-)zZbtWaKM;WXScMM$90~W$yToIl>%e=h^7TqM*rSe=HoSX#b1fc9Bj<C<Rqh#5'
    '^SSt58*llE!Pbs{zLYV-A+ocN{>~ckPUG(W_cR?_hX0C$<iJ|P{@vfnhgM2DqBRZyFcswGD$pPbZ`akjSHAe@jLJFrJDSD%(r{fz'
    '<Kv@?*X8g7Z;<o*-4H}6+zNnQDS6YPo@?JEIln(!5#;<h-GBPWFJ6x%+|Ia8BJjhBjeX3o`|~5flE<}Xpd}raA`o#@3|spMR{2@9'
    '(uxwqJ!dc1r)lk1PmIDF82C|Zm*)VCUv|hvfpdJzVjl(a=3*WHPXZ#<zRdj39a*l*8i<b;)Q4Ra6)JN+s4G<9kbsujikGST_^q)^'
    '2-GA9dm0fZw_}ZXqt?jZwd|Io{%HH3BmlK9ywXt8qzM$$BEkO((1q|OitIu%HsW2bBVy|-*#w&sXDD@q#yQMXEkL6+|0l-tKDNl~'
    'k{d>{)Q?_rop=j7!YjtD&3S`ezMC?7RjMP4d-2}by%IPINL4L`+7k?F*~m(%5b<%FbMmwsg!^xvb@SV=q5>2;ZqyQA2GBQHwIre*'
    '{HOqhIy8noL_qvtiXW2Y5Pn;?%DY&=`*J@$tC+M|wCHT5?{=ceP1Nv0r3oes45zGbm&F1KROeWSurU6++jJo%%icgkS7%)4mRJw$'
    '8)fieC#9?R&JNY2e}FbZU^P3kGz-l=?+(bvm~YHSkre#yxDbn+h%KEsk|ca?e#0x^S3okB1hJil@B+9}XM<s=5OAzryq@V@2)9WZ'
    'zrM{Sx;qOci8UL;0j$6V{~Igos0Fu?F<%~;Mv&{jS(4}?>#r}X`xmOARgt@8p=qrWip=MtSR6g6@IhPfq1ze3kED*%*u3T3HkDtx'
    '^Z1hwyH+I(89mlJ9YZ!KlML{I+fJh-n+lQ=N_;u5`oVBxM$Z=3y;r{s#F%Y5GRdVmn*CRHqdEq+dZ?{`WQE}!e1$`4q$kDi*@dW!'
    'Ad)mEPRZqDlT;?@htP7=s=-wV$33hKT-5>^(}t39oQWg{p!3m!#|ot4UiDnN_k38*Wc9|0jRbrzL~hW))IO-huJifRq62MkT|M*A'
    'kIIlsUAX7bu%FVi5D}w-KNUlulq{o9M!}20?8WfiC0{kq^Q>(<eKfr4bH->qBlhgzwTJhg(hvX{fhRd29Yi1wN2u3?Z=gA~oz<ag'
    '$=hSri~JQ&+LpUp*$Ah`JT{?1v~$qLBOT2;vinqr;9<LLFg@85P>+g7STu^7^=SnlfQyu!PiTsmGpAEdR@)(Wn`;Cuk!5QnA<{-D'
    '6KS7qpLylr^A-yt5b8JLSiQ&!u@^|UZxbnuv_y6{smm!+Bi$Bx`Zb%BJiHC`B&5Odi_P$e-KXm!#@<oXgQs_-RH}kubl`|hX!tzL'
    'O?`x4d9cwC;b8!zVyJ9qD4`3Y;MJP`%G}Dis4~xIW=HEQX%VCTNSd-;!$R|z#UeuTpthvVN$blvKSGnjum!Z)tif1jBSMj6y8N9W'
    '1m8siZ)I9<=OevO#tr#zx7&JwF0w(xCkrKh&IASGa~>|?gO%|}q5gxOBTd}MsWD@#1f>n5Hb%a}oZVtCJ~U+gElH$n{z!098Em>F'
    '34U%O`l>4uMRlu%8YlPLY!|H6!PHq#O!#&OkL`=okvrMdries@wDaR^nw?bTb@Sb@YnzExbxWT!t>=Nrew_mqB{EuX`xIers%c6S'
    '2VyX8NhRHwG5b~ohB|P{=ND^8W^w3w!qT&i)kYf&_ajOA$V@s*;I*GvIvcC{;Jg1fri>w8ulT+_&N~d&4D%%Hdu@EIrb!J?E$HMK'
    '(kQ*sd0)sWG@Zw$xG^9UiT0J-f&>U)qD}o&KWRMm;Tb{tDy5#C0g(}wDBk*43bRAOX~`{^69$Z}R;Vd)dSc_C6P@I&-f-OIR5P3t'
    '0w?|>eqIQ=Df<O|LSFG`)4u=rke~xxT`;IHZb%k1<fyaRJ!6Z8=If!^3T~$6_ge}+ZEJSy=$uK;{2elLZWr!gWDv;MU@P$?*IA6r'
    '=bRHA^z1tGiEx5yIZTZXLll`ny#bG^=YZ_9-&^kxgI6#{D5=rA5JfiF-gKBGkG|r3SOsjqdu3vKw}BIjn}o|ls+a*}t!*-(Afd4%'
    '_ykmMy<h#UaU+%S(KCv#8&IIz^P&n^XL486%9O!dAzK+sM9rT&V3&Yz*tok&e?*e_hJvyXayG<?rwfIB#is09J7X=R%iD>SV?1)D'
    ';6oC(hvj$0jIU(TvvH(pY60*RxV3k4`|0#jOGjf#Yo5Nl5g#+f_MqKtZ1!+3E3+8GsDGy;YPs;la8rWZA`{Baa8LHWV>g>+YA)Pc'
    '0)+^#^J4!-SF1pGo6dv^L6-9rX4I;Ur4OBTa;f^0njvCyWH+u7xU7cOzbrl{N5{6u%;3cVov+m-u{G9KkbQhUSI5}TV|MbIxZKm~'
    'u9D&g%ArB-`X?wggdMDa+xQM26M}Kg@cR__PptM(pIXcpCGp~q`vFKj36Auu@HFb&N91_K=?;r@Pj-7{cSe%0x7p5Pqq$to^Hnu`'
    'JMM=oO}SDt`oWssU;@MV2A<7>F{~<-Ul^*bP2~0SflK(+ccseOaz?|rI7FFCya^!CxqQiAt~9v5qkTx|>4O>df%wkJ(lmuTEc#jx'
    'L#ZfOHRjXMO*4zo*@vTXGoD(;Ek;&zMcy<TiS(caV(35Vt>_k#;ao8U@1dVj7Y*sYrVb@D|0WP^?i2FpAhx)3=k5wMD-BSA`9K~U'
    'Ko*85C^)PrU1lBF6v>SKE2lgVG?+4kyjo$6*PZSm=QX`%K_3U~-7^*{T2s;66vTViGO_N6(rld^I)R?K=HQJ75%XiCQyE)in4@gw'
    'J{!k6g7PoUmES#a#u+4X9{CwOrgAv--ceI)TFoq?2nsy=#mN~tbh=<J1QBf1nH+3c%V1i1Zq4HKCd_j&H6&R*T$=mx+xcB^8mxRr'
    'k}NTl%U9^rvN}8jo(TF?%(fg4$5;>E2Hz({y4%wmw)ud{DZZ^|6pcMmEW1{1uYksf%5$a<0N255?Sj4*N@<_HX+7(S8D(LPepA{f'
    'Di=GUG&$mt(Ua_BVQcr~{(4+ssq%%0A7+iLs*A24mrTK!2cha>%s%9|J^K~zyK6*kBTxVKy-)~{*7$0}5CR)%Qfze@7%Sad)JZ{{'
    'P91hsh$Dc-K`}~YFI80_QNO}X5Z4c8&X5n(u~q9nxlG~S!x6AIUG=Ujlp*T}ZQ`m`JC&rnNM8ce9@gPgFUi59DL<_mRhY>{etz_%'
    'HHnMHQ!h`>X*}fpO^U*L(g82}bf|6cYthIjdea|gVkk!1&sB)-OGEJTZpQH>_gm1usqVH6#N6@)6-5MBh5;G*>;q##68zE;g#i2<'
    'U*>O6%aAvm8<_LUNISg1KPKZ?Cj%5xNbmoB)h*!n8f2{wGDbW=WtAwZzd{QzmDfyprq{!u>?|YdtsBKa+6Z@7(gs8!<|Mw>a1^{8'
    'z>Yh(0na&s5Zxp_CRzj88Rb9#lp717n=F(1dxR;@qi{xwYhmgGk?=}x`%!M&z5mMYRC8WSUIxe0*lTXezx)%}gSwMtM3K(M)6k~a'
    'F)$PtW&UmOD-lCwqZX;DCaHkLBCV|ys{WDLeBl}sQUQIsi;NLdYKZ=@hbW!s0K4bvlj-7`wz<y+dkMkFj2<AmaS`w3a!P9hlkbz_'
    'i_?E&;Y!bRkdTXmif7FmFe+zNjPpSP6Ccd_{_liTPLRBQ=;mBc9uiF3ujjxC&`|pjE0q#l4s@ZDdW>aEX=}tiej~&^t96P6PHI4>'
    'a7W>`?0k@T-~?gtFd&enyHQ&rDbV!+bwU(*>U-@aVuGYTJHc^D`x%9@29{;j{6aZ$1-&G@vf&Dt>NmgY&^^%;6fJ;qw<N)aeaC{m'
    'R@(gbsA5HQd3=@J)A}^^`mpy-7hW*c7pkM;DY)_&LUw1z1;x{w<7@tQBs6cmNd(ptlu*N(%shL29%h37Py!u(7yVynKDI03i~DkL'
    '&7QTDN{m+=+NXuzaWqTk_!daNkx0i|jM)})nm1=aGk;yl=9n^o2L#-g#9_v449<}(?OW(dxxRbufDHB;C^Fx3k5|+g)LUNRf|~5%'
    'O%GH1m0EvS5fVlB7<(2=K1Y?XtowcU-u`@El@orsGts@R1;M`8(Y(6JqnE6{RR1q<33sL>5=DC$I3HWbVK@Vz6I+N%Qj8}ep$^j#'
    'exR#OVPW?XuN4Z4{QNZuXMi{@2`}HdqL+8SC_2R_sx^EV;cPq%_}0S<dfiLx$V#%BRzinhIzwN6!ImZUlqGb{@606`mTV)<@Bs<U'
    'D1su!2qyFs<&Z0e5B`pW@Z@#biav(_pQ0n55z!OKP4O~qEW5_n4?ynX6vq!fbGljVyQrAKG4Z3H*z}rt`5SOQy8hnW9sh((3*W*F'
    'o%}ww>*}bzd07@edP_+`mYy^YqJdRh!r*O0)t3aofKt0keT&^d$R+*3ept<1Bd8X0cwnSzvkr9?=bm@kOWlKl$wZ9FzJZXNwwUQF'
    'sOe0-$k_?D6(g&kPbWUt+&ZRUl`ICvJK&PTbdP!qPbp&0L_gD%T05j!yc4a=54+e-7(fDVK8y9oPuD9!$>*f2!ShZx3ky1FB;vF7'
    ')%6kX3^%fZnrzix0m8PY0E(G5fv(4v^p6G~HFi1!>^GB%Y&hT?xI-iiG<uZG6Tf}qGO~Nu;gdY?EIJ_f0iN_voj&#Mv8<*$4?M#y'
    'ck<rs&2-)#d?>3<YTa6^e_-M|W|{I#E^vplXCnK*BIu#}WwKD|0<e~!C$=xi1#!(@>(aYdqp{580Md=LMgu#fs~&)WJxTkHKC^i^'
    'dAYU;h>&KVl#Zu5Q#5q~?~HWXpX1XBP!7gaDx2SCeo`3Emn7poyPPBnwlm}Xm82!)kbl21)#eP3h|R0zbI@uj&$&B$st_nxwXs8q'
    'uT=YC*twPGJh^bcpJ~3H?`s)WW5Mc}9rSlY<X=pW+XbbJp%Vz_(tC<elu^&YE_Pua%HTyq--2Jz_bG<45yD4e=$+`v@C?piI@Brp'
    '@w8BUQSr0mnu5(}T`$SXIOr-(Z<m9|_1Kl(Wb+P&+~u?FehdKl%$CPeSSGkvsCb~{dDQDVmkXRTL3aiFwKv5tbE1af@Fx#3DM2F}'
    'YkkVk;VFJGP7j%sg2)~q7*IZ^c_$^1vz_6`%+OAaoUTYaRgps$)NsgG4dka))+lB;%aP!Gw}ujE3DC(I_wf`q7OjYAmjmz7&eB~G'
    'woEmDMt2oa>kfRQ5#4q{Sc4HV@wcomN$OWUn2W6G$!kJG=fAu+$YQ;bpiiN93l}c)WdDmGC8_OsVOs7iYv2nxvj#PlzgbDop@XIf'
    'c|s_qEkV8;lRR~=nRdwO10Zm)tUA{U&00$dTEpKv_yAi_n7};8=E~*bdK&l!B$?g|z)h_HB;watVUZWnYDC8=5qXjvWcx!5k=n14'
    'NQDcWBu0;^JX+2{kWB2Wp>4i~nOA2mG^ctK@F__l(b+&+*<@L9=9RYkGLWV`6tnsx9>m0S90iB#^XzLMg;vMw%%uf8>@55JVy77W'
    'SB^vlnf0qT#zywSe!zZUx1!rNwNkn8y7`cMfx){NJJ_HZwn_d1HY<tuZD9)BnK-`u6{G6ooeKLhyed?iI9CjxaE%gJ+AcR7uY+`i'
    '8oc*$kn-z3>O`2_-RN>4<2yCwwt=+Q-i7#CW0TnMQhyUC*hp2<!-VxTsza-LT#!vH-cWhlQ(KZA{hKQqYLKWD6Ib~6C8927eLznP'
    'CHI<!4@-Ff^BlLp<O06Pj<;+;eRYBpJ6(&pOERIm{kQKTBxlGWLGDR>_plfqP4D|2YgP~A7U)Jo1noivJS|XKBk7VFZXD(*OAzds'
    'u8NWlSG=)s?5fPdUnd_csn;PJO^Fb2Z*Ey$)p{JmooJ~nWs9=DvqJT611&{=M6s8(JI6!umwQR-VG!{nCRgVpiZ!e886Vtfq~JI('
    'Xz;CcB~JS0G?!8_VLCTw*D>xR)d#N1c7ElS-NeQ%UJhsa)6ZH@J@<4A#X8fbHPlMHYb0t$p{#_CVaz-_F%*YNIJ~?OXUofq1kj38'
    '*Id8o?`(#RbJ=6jDgcdI{Pw`__v%;X)6n;XONH)%_4qQHHmducF*}SH&?>nv8Pq`-rI-`+cAwwT&?+;eBH(a%O#**EW{a@{ZJ4Ks'
    '?2JF+(<^K=U>%eVlm;%f!JAg;0#lcW9i5$7Ln#Lpp!-<8Q_lEdX|{=xxB^CcZ6#o5=I+jPu@41AWvR4&*Uk3pp)Oyiccj^Dg?<qz'
    'p+{{s2rw<gtMH#B-D7)2mg{Yu;2EOGBZ31`88zF50MoNJ&V8|9l*ygvb*nk|JuhtS#7rd{ls@Kd$UcN08reuxEe1vS(|JObWSBvM'
    'lF->nA}m-_WiO9#%sNbFo3^#m$u57<!2V$~xR+)sEB*AFn}gP*DL#$X<1D*)j$GcbEznt{jFKpib%&&}tWAP;H+80Wd;ahU9uR>u'
    '`bu6q><MrWKs6<yIOTj&Vdf$c|FD>Rix2zpz=pu#f47A@$qThzPwgEa*&%48^RvepYif^-HxeWHuEH&m!65en1-n{RSNi$yGcw*>'
    'XW@;}uZR0pPT&y|1iugW`SB*${(&w+A(^oI)c5~xH$|B^BSx>{8P^Y6ZHrO0n&IOosrh98Fdf(z1~+Yd;6NS5c&y`ZEfK1cNZ#?~'
    '#&vtK5`sD=k-ruLIZ>_~z8!}e6jFwUcdsX<-PYbsQ520m%&{?X*;a%iFu~6hosX4M7gS~YGw9dM3x<`)EL~)lKs)3%c1lJ~E2%(K'
    '0-8s|J1Ym`Y$c@-%fBG@*JB6Kzij*+LVY&(#0U?hPb~3q^!*McnaF&|2d|j&BGv=PdcN-563rIH1^A<<2TftAxsxh_w-!uIjlnbw'
    'Y`u4NzZ$NY7_--mbI`J;3gAPnsFSHUb_F+A^#l-+6rt{gJFI2oQWCH72z#U1EEXC>ClA!I$^2z)+B+9&X9TAoarQTLs166wa)!PO'
    ')X<A~;lDqPrYkEJ+hM*ivIu#4^41>`Z_(AFFu(~$o*j@~{LeQ-2g3m=lr{Nd`NXZrC<~9I1`E_#2*Ki4m(f;K&~`!G-(SgW+CCyy'
    'bZi{S)_lS3VLsK6m?`Qo8O_S=sFfifI$ijKuB()vc{czq>pbuQmfG@0U6Bq>`%zapS&=9gUGyN6E8wQt?m2mA6SW8rBNBogS|}e!'
    '@rZy^D>BS8xxB2hkGXbWx#2H-Dcxr|*Ji|&QVLv)RV+-AyJGvza*+!-9Vhg*30HreEy5MdFYXHq`9|h;%*+$C*ib)^wmniWRw)Ih'
    '23SckvC~cTi7i@puh%_BB__G5Mx1x>pi}Va!$Z5uJvNOK2x3q0QsjO`+NU^^?kF0bn}6!R4?B^2N{Ljb?Ixvl6eX*Z%<y6MGgIxv'
    'dx9dZ%rXExq@Pr)VoWIKalGMS2ooLoqbk^lO!iV30$?)zPdO<_l1gDxv8^SSDws4aHK?5ADvPj5x^br8d*vxRlDA$|-ybB?YhbN}'
    'dU9{ey!pz0ow<jdJHLZio(icX7|Em9srh38TG$mL=wAGFHgwcqRYzrXF9Dr|=jK|;z#98@RglQw#*9KmSV9hx(d&gqpNECGcuW9l'
    'nQ)&BO~Wr&HPqcih_VuSqLvvo;mIEW0zsrtx>#s4&ae8UKdn974U1l7L$sIfBwu~HsoWWTqdL#Ut=sU}r%fBTs1WGFUXo*;&+z-@'
    'wcm)!Yg4dk<z50$?p;3jY&g~p)71EYR(mBP;#*kBT*}-$VY9fYTkBb-*JV?z^$Onl+d>~r2?ytaFrh;rS#ji6im+Q-Wm-vsu*?iv'
    'EJT`}oOnGHF4V5^+i^QFrUQGaERX-mZNXqGKZX3EE<WX-(iycnhIX$CY|-geCcfYn?@MH>VvY@%Pt?*gS$dhOz&nRR-H-z;XI069'
    'KJMT}Y3Z1>LNb!Ie0%FAP4c^i6=QQzFtR+4I-ib$^Cz=z+M3?=q#k@W)3z;3-yu9bT?0q#O~}=9IjZCKqUQ-yQ^vyn6~Im#i83p|'
    '3o%kFf3YmLUjPfITlfN5LCo6YI(jD)#j=jbv+;3$CZy-A<mzs0u^4$vB`89OkX~x!0ouyJ*^4V=A`SGMqbMH80~0BXkFM-*e9Q7|'
    '{v#6$@BQZcTEN5f7G=v8$@EQBb0FU@q}Yp=^v5m)cPZ~P`b`pkyy!nq2j_)~`XX@JCw%%Wz+^c#c~2Bu<HDVJh8=!0)MmY$8hT!^'
    'dLgY)Fv9flh;9k#RYpb{4I4tsOIXrs7vEES8|@nMWD2P@VNYh!${_B_yuy6@t!(}=L-U2XQ4zCBX|q*fwYCdHbaV%3<J&VsYujrp'
    '_X<k#j=fUAg5#E2JLSrIw5gAlgvV=8)aWrO+J8w~9bbig4#_Q<>&FH4%-)r)=>U^mifwuHW@q-(y5;aocjQ0FirFUZCfO-SEaSp9'
    'ev1*>LAIK%lW;StJ9qN=)4c^FqTL}h{ZtWsfaV%NIOO59D9{@#R1}Zg6mM&2V6eoq&#QRK{1@Q7KptvBUJekvC`&`Ljh@iXFo9WS'
    'cVl55@#aU1TLCb<(0?77pj%GCfwPl#c2INU-&#3Gfh4h_rA-xEg`o1su67#eK>b(eW1cvDFXXJtLK-qQZ8;6oPY4OCQ!gRkg6vQf'
    'I2HO7qI>MV8MD4|jWu$Jc6+T;8V>ANfQF6kY3KFNPH=(mF%u^2(9*h;Fs6E!H2=wXm2sbBNyz&i)RUE?Mg21Ft@?cf-LCO1-`Imr'
    '3B0?|d|p@4raIR-luVo$<=Wp`AS%2?QM=e^^B{&am&=>*aLF1&00^v?U9n76unuK@UwZ9M+KY6JQdn5gAHFVDaxA<iY4Z93w1$CW'
    'rrUt`U1e8YE-vs6l(*h=FW(b<J53LVe<(WL?{ya<|Gn*Q%t}Y^^vYO<qukX8Pw$}#4l*0%Athl)(NzAMG=uJ&tFMONRoh0)W<a=K'
    'uLfLkzBuzijA)(SHT)J0l{`|NuBfx74jowUkXap0J~pTa)doI+^!F7x%fSC&FfuYr-kg#cMz^R9ff`&xf_}b2mXNSMtTvYj>MvoX'
    'n^;{bNZ&*sTE6uANdR^o9nr(=b8Rb^HwGRN&>tbxr4e%BIUzi|v^FlnP8nqr6JrRyza-^i@8ClqIUmXm%fW}ep^&e2bH@L|*^%uV'
    '*4b+RQyAWLSD&mKnMqey#3#s(p=;D;Ga@RXfH#Q@0aepovN;ygdmi$M?!hZ`d|~!MdMazSEx30U$2>ZE?c_?FAJOP9(mjB&Vs+Sb'
    'k!Gcyh4lh;NdyN<A(OiJna}>MGzR5!Iej~c@jV$tUvH|EVRugKjx0(f^>SYFAPDDE&(+A<z2+YS%lm)}Oscs(9|YKK*>(1OD(>S7'
    '8r1nj)ljeUYa)pIY<Pbf32@v}G66{#loW-db4fhWWE`tF$njz!dW3!CzT^f&Z0lRJx(hA^Yx%f-z;j=k;MD&z6mlF;Z<8!L(xWdz'
    '+Io|J&G8Je8j<XM`t&^9g|0zPt#JO{)m6t|ezdX<pEKS~1Jl~KET5WcF`@_&SdGCeRL@BFUo}OHO^kCUnR{m;@DbSqESPj9ph7p$'
    'X2U#)n~ln&AoZ0$3)T>g*d~LTUP~LkP06q8{<(@grK5qD^<f^+p?@kfEs2#?VrIZVXBo>o^eo`x_(Zz_tv<bt)7<`ht;{g#{$b1)'
    'aV1&{3w<wrZ8kgjIbMXl7P0~_k|$gt!qIi1Q6C)*vWo_dte<@Q`gF>(#H3L*G@P_J+z}xg{}TaAI0+0cK@A+58tq>vd9f`k2EYCW'
    'QgC|})nm5hepZhk>?Hq`#R}N*Ly9u^!tP`JE2`w+B97(MlB4#L53X7@cla2MtWPx{3kOWYC-@c+#&x7ixFgJMg+sS-#<Qqko^u2V'
    'Fr~R!sU?vjSS(k?Ns{BH?H1%A*o@>SR<~BIUM1&>@3{;j4JElF55QnFlT)xM8z(ty{dl$hJqfZ=xu|F6#MR%$MzIAOki>Bh2OFo)'
    'DBJUMnxba*->`t#>F#WGFq6&0O^pI=E1_91rTA>(^WrbZ^@Mz9IVCgSD`DrROfN3bd+kK_F&7i#12Vs7YIM%bh=_x)Vd>l1sJ{}9'
    '{WfuF)Ne|ER+hCrVr6nhSONuX|L6!0L0CTVTx_~S?FjKDg_wt_7Pid>$nZ31k1C3n{7b4EyH8GR`j$n_k0ukokCCreUB{rh7-tx;'
    'Ky~{_gZnosY$wd5E{)|+<(j1H{$N4{K6=&V#!Wb_($b={gBFZpUk(+^0r#+n(?+o2agRQ96+6MB4Rbuzzskw6(!;Np^n^Mg-<<#%'
    '5Voh4<`cn1ndcyP&}bY3%v-DL)Zu+H&Ue!9FqHhTCybQ9Pr~&ZnqvU5GqlLqj@|AUyV;HGu>W3aob3uC0i~#GAJ$3pe}ccI4_J%e'
    'xXUR!#PMC|*2YJmU1xv*Z#o!szZ;m!rTvU4PyKLlkAWU+b+_GJxtde-Zmtxg2#t0D2YOB>a!)6VCvO6NL4>(nd>PqB#hjV`cX(rY'
    'r(QZj;Do-4f1;-J*rK*$nG!23Di+$CekhI<GfA_mD>8V<eCq?c+Dzmyw{2#1b1Kv*hq<!H8Ue-nhzHggQ79WrB~Wb5rJ`#wTexHU'
    'zK~tIRIB=wv-#q#9tLZPn6VppELkmtAZjSiNTTn*Y94wjtO(J2+P!mz4THKtqKae(uD>JudTTBW%TuWp`1D+iNHe%Q7$pFuiF+n='
    'FtxYt<P1{eZ1ksZ&9nN5qd!O4=x{>DK`}8ea6?-fGi$)o#bco|0peCEi};hT2_9h+W6V~C|7sWV_{;Z2x-45WjjD%H)%?fw|EW3|'
    'RglcgsRBRb;Kq!&tm>@I9Rpq!L!1r+(pS^+RtF@F7+BEl<mzqGqI&=w!^v~~pCFuR1n-le2=5PzlUR-moPH5Twvz%Q$mV#kJmEas'
    '%1xBdUmqk*?LH{oeX-e%D8P16SXy55OC%pLQhOXIB_V_#QTyMEJ9jIf9gxhkkBAtPeyT`_$YzF;<Cx&vBj;a{v)kDA0;Nx*Lm2#C'
    '?n<8}G7ny?0ta1B+g;8G8XxQ*b%KJ%ae86|IYk|~JjlTE8d@b95S9>QL#d;Rswf>?iH|@rIFrWF-!`+h`A7aEwn2k@usW>(=1nKZ'
    '#gUiFDAjn>L)@<bWszg3-avcCw9z*&VWDibWbC>pw8`*U$JrK0$yS_u1bz}k7B|dzu}5rOk!xMAqjWu4(&c|D7NKVXd}O`q=Vv$0'
    ')6_PoTXp>uX9rR*FK&i*<C;W@)J*7x<c)wiYWU3E`%gW=7hTx=$up*k8Iklu^mei%K3EK)9g>MtD+Cx*y#lFoPR6WW7<cidqn!WA'
    'd!TGfCRj7Jq9+mdYc;;6q%M8}RCeuwRWy6foOC?rPR;fwkpKUCI1Dl^3N@dpB>=o>L>)e#CaBL;q&n)OKsC}r0nF^Vwp4hf8|7q@'
    'PB?zt?h5$jpPUWv=Rqdtj+eVNxi}p=wU95G)ZmqiV{0fwUw(J_!Ta5Q>0=hZqVt(f7@%9)PvV>8QeQgYo>SPpU5Mo^`xV`-8p)sX'
    '6AQJ2y&!Y(GeIuw=A#LgOf)fX8pC|K69U23cd%3ZHxb%d%sEv48p-TQ%7)ujlW<$gO2G0+4f$yy{_Bw~B#9OfxMD!4(CIoT=k%1t'
    'r4+cK?nq`SV1orYIEAnidsu9I@%)zPY$(82FtZxmgL_`oQ?Yf%>Jk&l=+~2_`yvzj8lE`^O`Hj(3Qe7DxVL9-%W{Ca7yQ%I&`+?D'
    'fdZRnQ(V48&VDo`9nn5>pIDg>0H3VMhlboS$l^KMG6HRYJ^-@=?v)w>=h!-_@DKg9=sX|Ggat42J&^mjl$uh+F@D-wSW-+Y-XVQb'
    'C>>+cYi=c#MH%yhW=i=D!G})wx6_b=e;T0?(;sbR!*cxmX6o~*f@~>e-KwK}fH1P;XXec(5m)zZr7+uV<)m<_&VQ;3Z)kjsb{_pB'
    'A%W4D2RFus%Rt*zryN8{&?P9MsmTDM#Qfv^muvzhX2|slw-0p1hHs3vfB^=DX=Y}RJ2&aRMW;LZ+M!HsN-z*gfAUISd1AXXa{xE7'
    'Fl=F$mi%_jp@$A*vM-PXN4bN;68fs#?Bw&;{MN&~PYEDRu&!rPW35RLfE{RR0I6&#GD*(T2-f4mpWPC;5r{E93YC1A21HKo4dQfk'
    'U{aIK+q$^MN5bW5lYw>zH?80VfC&sA!l3Q=Tsu)_(!<c&8Z(2kWLUkX^oPcL(hcnBeDIm7($fz%KvG4qx=glg68yikKv<Qz*%sfr'
    'MPg;tP;d;ESScz@3l71h&2wc|D^rQX(LvlsVREA3mOw0&UT0xjoedpIHF{$pPQG9Y6g+|t^X-HRvn*No37)ZYyy@5U8dA0-`631z'
    '3o3F`_*RK{Iz5?7(iXWRN4pf5iDJQ0cuj?w>knhBdHOMxPUU1q5YTmFD`<FxFo9}7FI`rSjrx1Ip2Z$A5#UCtyQVGz**MYTR1T4N'
    'xig%6u+g>EZHC>`e8oSS7?lbAb~ZwKB=iHGsur`Apd5l?fsLDrmB>6zS9eXG$!v;GI#sCPn}HN<9PmixKsdrFA9~L;+^p3<|L|$('
    '{?hPSO#9R73*lFt0@Cm_QIu}2*iRZqQeaP9#aG#nnkEk=MB~O2>($YfUIWp#3T4c8yO>hq7X=Y;r#aGK;4Z<u6H1YVSSR5JPya=T'
    '{jJ=8=TvXqhXV!%H#MtonN|(yXQS4&3eEIJAc0aH=kdzpBu;;^IH+a-#SKqP!13lH5~z|2oIuv8a1&zLsgj0czfa^N0Wc+8hUWYF'
    'iH9)MszmtR^HwBHO&E<@lv1XeXfmj*G9NWUCRz$Du|MR6J1yXamp>O_Y;ZcGbQn9PjHHAo0<Vbk6XZ`3@p4;7+9jSR#x33d_db^K'
    'd!ZWIS@sgL#f7W#lC$)K>m1<WTN@PFNL$B@^fdbPO7fAsjZV!{%=A5ogMPsfMV<cQ_(8ZzY#iVHVf4->$w+a7?-w)&TU}t7<k>rp'
    '!ur3YIh(STLmhy3MRiCYA6nnL@U4@sJ}U2Z+Fh<s>%p`$h@dkE?`u31>afSL$$e;l;esWz-ADvMg<yM6Ev&azIhmdUmN+Z5w`tI>'
    'q(B*kZEA`qZFNj<56xU}(*SzU+en4QgKQ-wqgd^iWp@LnYe*VgzxE&tf|nbjb+r&vJG*`sY4xf~5T!!{IadUQkrB;D-FQB+ZN+g-'
    'ywDiuw?~@rK>(Y%3KlxJ&@};qy=ZgM8f_MTtRWG1MVFBu@Z9S}4B~JG@iRs|t^tOU1HcR`j)keUzVmKbfGO>jy@Qivu>qvhwNcR)'
    'Iplgq^t<*bKXxW&z;`@<K3&T986z)n=pHc*d0CwKNZ<Z?9`@?kn>snG9wKf7a(<dW>(kwJ<o`<W-X3E87VwF9ZMssmjKRe?FAy}Z'
    ';!SVuf{(UpZt!R+RS8kILC>GT3?mqg1^}gh@$=ud5%7+ugtPbnyIFU);65djaxsUzgS83RWc{HyWk}h}wX?Nxe)&0G?RJ%V0_igV'
    'UbSufo*qh1I4V+NdTjj&cl(@dr?L#gXNkGkF-98TtycOg>+DII3_Va0+;Upg@^pVfUaLpnEdSsoF<7+0{MKMkW+gPSe!23eRIJ=N'
    'r|%@IDjME1RNPyv3veitXOk+Ba7+Pkua~KgNslQ$0e01F!}jQBOr@y<3|8?_=(cK2cJcD&k~#*R$9uP6J-SAA$XniFENbX-<!Yg<'
    'OVTBU-cAzYYdPc+0trYGp^~&(r7GO_y8+rL?IrHEJZzm~%oKpc2@@ekBwU<q`=m~!xZli8G6kO9>9D7+fC`)WVuF@AJJq~X-rQ_z'
    'e*;S&j5-KJY!5r`K*9Nn{tesziveUWy}(qoniX$K^SQhiyJs|#la%BKKg83NR6}$)Q1HD<NNeVM)4R9yj$&$7GwhU1$bO>aOpyU`'
    'e*$bbd|NPy?5ddxvH|lkyLeP#HYP)b1B4^Y=I;_$an`wY4&|r!dAPPdjLnuKOZur`WKCY;VuFLqmGMdt^4}R3=3*|!gT<CRA}3iF'
    '05dArFGuy3VSMfjuiV^Jvj`=WSM!5{&=SZCcB2FyoI-0s)OL3mG2|cIp^p$_Hqjxb(x%Hc)s1^IK=n#P;rf8q!DC|M2U8#A#HxP$'
    'AEjh<%ff+3dZQZh%(;9N15zYw4B-GLM(GGO{?njwx%JS1aL~g6XS8($G!#J%Tf-B%^VZEN3wC06+B#+>W}j4X6FosQLGVK<cF3)('
    'tP%L7jpSJ{Ay^#46~TYwC+~N-hmPq|E?eMffLbGH7+0THm6_9mRRp5J#p4&6!x}>;ym!7YE6+Ldgmb90aQJGtypwH8`+%V8<v)*1'
    '!!DAjC`bC0(a8fjJb=B~0(e}K=qZ`%dzct7p!t(pYG3~tPcR2@=5WrUx(CbV_JHE^?p3j%Rs7>*$a1hiqDbjPz~tGKcU?5#zkGhS'
    'v})p5(H;2G{zTtEz+A?ph#KfJJpi5l*TtHDQ^#c*Wo(#|c+V!0o{NhXbqs+dALLId0Wu*v{()<aLi#~}CIEXeXqk&VhRl2t`~Aj='
    '0Y4BphUL-hdgYY6jlo(dIyOHVG2Ee=W#NI|)?Ia%@U5|9_8VQ43BTJNR{9e&^TpBvB1|XAT5iIFZY5Sivp;NZ8hb{VOcVt<cy7o!'
    'F5j-j9P*K03S=T61aMYYrGZq)9fd6H(dVY?V`m(scE15j4ST%MxdA{Gee2FO=9n2fH1zYws1_^WeQPm{u9rs|&nrAn>$k1|-AWPb'
    'najZODT(lg>?udz_}Htg{_!(Zi(zQenc@P3sXU30uGFHnbir7D7!%RweR)orT3<1~6vEw`wf9!)Ugs)ZgBrgKN`+b5jJ1w-+vB`m'
    'QHMo>=dGX%eVa5lk^oEUd5#N^c(a2izWF3J$tkYR3AzPEWiRZK@i64f4f{=A+tT1jBQ9jT#)ka9J9luR56jR?7eEaO82g6}xQVLa'
    'YcLR(L(x@Z*xgMS-?{ZEh}{oW6vw@--hAB@br{jGD`F^_@g#p<9=*L$U7qXT^!<<W{n#M7yfvaNdXI=p&Mq{>Z6dJI9Cisv55^Xz'
    'ih4d>6Kmx4fzP`^aR&yDC<%CpyVbTAf)<=%EEB#R-82|@K_*fs|6$m_{xD+Awb*S0{$-%NrC{l{9tk8T7+Xi>C#Z6KW;2Zj|9MK$'
    'dVPmH5sr!G8Pj4h*=8&39;E;Bw8JCve~x<go^qJTZj}+9hH4<UJB!LZJ^1ZjVieME7~AT56N@>*f;4P?z$m@h;n;?&npga^xr(Fw'
    'y;Sppv^5!UNrS=Q*t&UX<*|*dpqFvUkZ^pQEY(k-A$p(judXTnk3)Z;<HqKDxeD@3^A5(v<=C*Yz=#lY8wVdRTo-c6>Ml<PJy%5@'
    'iyH(D$|IK3-i)?1mM||u@1_+*^<Jv%5g0lj0W=+{CDX%pPjqD)BE}13x}r~B);2xh-ToZXFx+8VvAsdB22TwbMwhnIzcukKQ_)of'
    'JUHA5FRC>P$8)3o&xbY94>f8K`BSING7s)HY5>PCk>Cj25AkAfkANzk*3dFl)Hc4r)?CRJ^skG+`4-*$N@5O3>Mxq0H3>QjYv$qJ'
    'Qh~;m*0_9saZfczx=!2znO3>ikLJEa9>a8j+h(CK74-ZU-P)qL!F^N8&!#!un#sKRH~)e&P8h}Tq{vc1**CuTWnhT#V4)Z_i~OoM'
    'TVp`H@6Gf~<JigZ=kKc-UAyC060l_fR9f|ZuC6+ddEJosI6zmQS!!zbX7L~<^tezZP`WB&l|5S}b@fIoPTP6Tv?FL_++j50ne4e?'
    'R7mdAmjD)=s6xVUD_}Fl^)8DnUaGMalKZM^oTMcvZldDiGHTKaVJ#^};7DtuIFB%MA?PswVMeF>u);ZelE!8Z`YPV_!9Wj$dSkS4'
    '3!qq@<2jdn6-$*~OXm;S{Vn^xb{m`hd;U`3wvAp*bfo=?*WuGP>{B0F^l24>bg#$OfNB(bN9R<OW8%v^wJkiF$Y6ks0=Rd6HKDD>'
    'ISZ#GW92Td+1M!Q$$SK&i$4}GAGMoB@@}Ogn^43ee%cb^<sBVV*g9M6RlRJ@hN)?YbMF(DYXu#tkJm-kCL7vS6U_aDx?T<5+X1GO'
    'e7kkmGa1Q;+IC`$I{-Q2mjA$RUe^vhPhEE`eK3iA*IKgo8a?CE*D$UObEBs{y~~bNw<fBRiUKtsSGON$2(0T`PW$CfE`OvY=HoTH'
    'f_YN<<(baC`%=#Mll2-rZh94_1A2fR&-|!BKjMiYp&5!x<0Ss7wgc8a&%0}s^Ssw0MqNgNOj%<BDYMjZ!Pvl@oDqU!;7>!<)cZM2'
    '2zg)8LmmlEvNb9(da0G}FftL2;ntU|@;Jm>Dl6(zv*dVdeO(?C86s2EnhUPte$dyq>qKbSRV_VAYyEu*1@s`%PTKnxdOk5NuEDAd'
    'c3Q5$y4iOZi*g>Pv~_zQ*MPIZLvWz{*Gm}NP!eyWuq$fu6H8IZ*4Rq&;N_r%<egmt>S%=T&&H?L0#t<M$Yxi<#ENwB)bbfA@Wpx6'
    'T`j+y2haV64w5LM3yE;)m~<WFwrAU<d?GbEx+)*;at9xUfM2to6Aq)IjIx>-#`6)7B<$APJVhSblAk(?xQ~O#y1x~R8_@t5)0}88'
    'Mg(~azquyb6SF?!#$+F<&T2JgLg*|^ndKjQz$H14l3C^PZ4hy?n%XEaQeT{*rb*ba_Pfl@7wO80{c=4<5zF(rF4Z7$awa^Og412T'
    '{jsyvEzmGm{fOt|h)BRoU*5PxNya!(?rv|b#XYkkWKY7jQI=;@tC=^~C*#FG)0423OR_NSIqM`5@m1VI4BC2*3KlFyPaWF!z1(MP'
    'h-|=FsMr}Y6D^e8YN{1C4rXm_U}K@YGL{kk5Ck~1orL&t)%=&GcJSpT28AfyHfS2$5STCDBW$St0`f8vEG%e*;*$Z6=3i0)^7k_$'
    'yb$=+mh2}ioFL1iyfU{TcbGONV|zkZmakrQDMME7GFK?x*}Y)#YG{(JI0(x{(U@*QA<!RmCmhJnQ9I}_b3^rGSSZDwq*gSq&g`Ia'
    'zzVyL<H>_5DT&~Dk`X%cD6_Dok5=*jNDM4(GYW@~hx6g{=EGk+O=;GIle^UaCErCv+&vhkJj64J`Dt&QAjpQ`vw9X3#dpYyB~98E'
    '@Sy<$aRW`zDdO%zO%*!o(ihazfWV_PccS3eP057O>~ZhZa`E@!t@<f+)I-wXz}Rzdy11saHRFu4{LYsPdyZZaqyg~cod<9HlS&-F'
    'TjI@;Flcy<+~(UBij0etW*yA9dewi=wCwSPC3}6@70wr*FsA$oBkzU;Uh|3>MF1qsj!8CgOPmBm(ZRiDEkgZ%df~|F1}Zn`&rcz9'
    'Cwak7qXk=2e9J^!bJLpO3D^FYHZ3?dQLjXP%+@=34FwA4iL)SX;*U?ykCE>izj${})*p}G24S6&IOj5n@u*P=QAR%yUa16eApW$z'
    '!*x`AweGjO2i%|u#$%(LKfA(m$?=%lTnF|M<F!`!>ox)=Bdi6w<kh(kFY^BS)<Ik_E2K@rD`hYYorZ$M3(NSe&vSu%+<(q(tDnKl'
    '1p7R%`%kdx$Hdlj_vrCuf;KIh?deWb^nLvvoLXC|#-Opz)#nRo3`elLV_g5+iz{`7V8jNY`u9C|JJt)u)8NkSOH!NOdVpwiQ+yu0'
    'bIb2=gQk;N<|^ndmcJ+3J3Hq4uX`hhQYh(o-cFDFj=>n2?`&#FqL{_4DhMH5+8swp9#!)5yUTdL>GWhW^EQaV#c43BmZJ*Huc%jX'
    'Pxud}q>&1my+$dcA)1y`0Z&fLR~6W1n)bFD7?N)zHSen5LWzf-n)a6uHA9s~4byf?(rzpKNjDqqN$35-pYr^i2ADSWw@xd)Nok&('
    'B0<#}1i4VK-rJLnnKS)%Ml}6d#VUD{Futg|OKYy&J10S}VIKqv2Jlx;e7p4glcQI!TS(y)0Y2cz?05Jy1eDgNpBvN(a3k5^q2?PL'
    'od?31_)bxUUBr3>2y1a^q$Juq<>_H6s+g~8l2#qCMNdlem_FPqOQ-v&7h0W*M=3FWu5q(WCf5r$@9oT*RdwPRMajp%axehHF!+YY'
    '7?(kHH_m0who268I4PbPz<Ix*KGEZ8;bE_P1e7ZI&2$!MMRK4JAa)^F?8tRP^f&2j29Wd8dL+RXgbGNybBeS!b=@X3jnpvZk!kZJ'
    'N{FSuX&KeZkx}&-fo6fB^H;F80t?_#V}G><;YbVv^$n~8OJc1g8K7|F2YS7C`R|_u44>^tS{l;JNDVkC=oGDFCa)|$C;}{Qzi)FN'
    '?{0wSdE&+{AkhByvexTI153gjyZ@CNS5!>?C2)Voe0_Mm0apFsOW8}I+Mufk_!i#}Z}O(J@2vQNBtX0owvmQ>jWW{1E^GVAP+mg#'
    '5OmrVQS{wXwQeCZqY)F3PzCzL+47|Wb6o)-Om<C)ZO-u+;2+vwR#<5;6xsl#FX{Ha9EHvZ-5f&`idhH7QZ?1&IeVy#Kj+IHpe+or'
    '%#XBmGkj+->JRpSE3CFgG4Mn1yhUvjxPe6tqA_`RJ)1je=xVhj+kdk69qNTopF_w5H*$KA4$>26k8=dnIf7P0n6)*9P(6HrD}5V5'
    'wYU@71AHFOFLLG)y)=?6kWQ-WBt_!8QKx3fdMbKtL1YAkql-Ih15LMNIg8Yvdsl^IQS{W2I*EF&@jsnI`+u@7Q`R+2k?BfG1kX`o'
    '3mCC+!^O{>#kHIR8%AOz;H3IdNcrszB){GQZKV8ENv@<Q8l8G%%==EVL&YE@aiq+-oco^Iukz^uX)W%3Kkn%z6ytsK;v2>NN^2EA'
    'eaF)Qx`)%-ra|etKt<udp}E4HStMOLF^+`D65q>P6YhBTpJ3y@Do`Y^8g3!TMGRWnhcma&*L7GrncS5GFAdU**-h`ty9Me6YXunG'
    'c9OdcOBqX9$((m-M@lW*F05`Gp(FnwuIQ$n(%;X}V?is)n)!WVn*%VIsz0s|U-Lu2y>5_m90JzQTOT64j3@w<8W`|n;SHaJaSF4`'
    'a5}^R@f3870!65U3L(rk7)5f${!#TCYrJ*6y_s7?nkFd+)!U-lwF)+v5e;xM%`>uI-m@i7GRI6US2y8nFtb{58k^{~m+|vhk?mYY'
    '@3V0z5a8z?(Ko(%(xnidi&Pm{$L)@A#^kM=nUgMX>G|})9fB8x9IOc(Ij3}tM|eeZReR|QQoA_&DEo3IWXlAAbb_%{vJ_P&9LLLw'
    'm@V}t#o3wXm#OGs?Dsz6Zy$pZ`46!rl99$0RBt0GMJaVE&YtRa{jSfv7bQJ52R|Rl=)mbQQhSWG?%YzqPNw+ZofX|>#Nsfd^cXA6'
    '%DW>;-9A84Bh;InfvBYE>aixhd0jUwlT83D<iu3igaW;ZnT$k;izM4!MA}?V+4?5#i`#PY!mMYGW`zfCwbiI?lyF7Wu>8xEpj)E7'
    '_fv8dt@NyR<U>mlyo2?It>dHp;!t)4w>Gx<LKP+8u`8alZ35Qg00)`!gKV0cYs7xH?t-8RlLz-ZoY}}4NxlE)O~?;r=B8RvG3OjD'
    '#*8XP|INWKaRNF+CBddYA;)s1U%a)ToRZ!Ie!kM!V9{@pZnYC#Rozi$>(~~t(QbsTZrX>zcYq95@SYRw>MWCGf2x3rd8M;T*_VZT'
    '9&i$fP2``xOu}H0DvHZ)?pAU4(FDojUnRAArLaNHu>F_7N&7#n&3oKXUPE$Rvka9Uk}{qktXVoZ^QS{3kJN-&f{A}X)-(9EasVid'
    'f8fq2oKR*4o8dC*kw<#H09q^zL}&U&@ZpnPY_2`>ir!!znYd8wh=B$4v;KsvG2Cz6pH3`|5M5@>6M=9}aEl(a9aHEoDD(=H*4zl|'
    'h34jJAWEw6XAg<p*#CN<%9Nk)_}AE4MqgSnn$EQETk)mXt*;1y;5I=Bb*7>lAvj)|*M@ZLhlYi}woKIt(1Q2BASsAGf-6(Z)%2^M'
    'jX`%*)<liw9WR*#w$hY{=8jfm&W2JmcX}u5M%?=kbbpf$j>d_OBnsK_Yjqmsw@v{(0ynqxtC)1m(ACeief`3nZU$Bn2_f3R=znuD'
    'S=BiN2&cV?ugSddp-ey-2lMT7$s0JFxHEL~!xIOOoj8LRrNpjSl_qvR1Kun=kix4iE`tY+DhEeog$cKz5M>*$QbC<o$=M>&k+wMx'
    'sI-`in23_}y;4h!vZhpe8)^6mch`F(py$^elK%81(;mSMr0n6=zy|Mb;1MUL<r|vXy{NvzU8Yt}xII!#3UAk!+%k|69-T+>l%66V'
    'LDoR0BWb@svR^r_L)$IIh3VzyS9w}7Oy*{G>?>JlUrUnR_(Nw+i2Zf6=_p@Fn%ya}8XxP6_p_`miLT&4ox<W8+J{af9JESf7gxwu'
    '1~+uY?#9%W=YGei5xqy6d+iPvbFY^ai_0J|X0?+p694E&<!%=YFFEhBnTnt^6z~U8p!?g)Q4I48>t5GNm<sO>w7{%IiIU78HaFVk'
    'ICz}bj~Go0@y-5CY38;h$&dPt>27>PS$fQl(gJ+t6aKI%Xo+w*hI9W=<=IPqoI6_S!g?DrhqNfVC{|<pcGP<Z0w?MnMTyYuGs}Qz'
    'c=M%p)5mEuvAgGuFicJhSc-G@hMlopshx8@(9M`b4{=0gTv&(#;4VjzOX*mLIO>2+uJ2o2Blv+T5Cv8}&#oYXA+gAES9<-I#@$&2'
    '<t9QPj9itr`1$?e`z?By5?zU(yOCrOMe>#~Ec?H?Gi<IGJ)t&`Jb7;o5bgU_!Po{{B6LCUrsV*b{F*5z5|lg=8iV-^e}omL^O`I)'
    'XBed_iVqOO^=o>6DlZgW{6-CsFdKKxftYdln66!(cqe>P_fPJ5qiH@u{t;B=-zFOyTs(|lQca4OT&ov4FQT%n!R)N#+edeDi#Nw%'
    'ByoR&K)06P4#36C2&t%ZaQw+CcM6H%03Sj73$SM)n+YqSTZx~OapM71&PC+c0`WoyZ*M$V_T%9t<sAM%G(IIcf&GBd)2=Zl{EJ>J'
    '2LIJ+7g~rgd_AHVo;y?T3o|d^GZ^1n({w*}NefJ4fmg+T_7bt-QiEFkNJf?WvSU&mg*!8v1yOg(>=oqpNy?#_J0ApwygZnKd;bjM'
    '@3n2hKko<|kRn6=Q=4_z%iUOd6gOJv(EKkUn0J`Irp#Uv90S!T_Z$I)?2zyoaa)!tM+`Ml)q&?}`J&7}Z&J`kh;rX9oK*FZfA>)J'
    'I-sxjeSdc*bF$rHjh%g=;a<!JaZP#`_YpYfXccl!y4$>;G`JpQSo<2-3f7cphw+xhr900vo4y@$j95fGUpcFsXsE2c->e6&-nq6)'
    '+l$$$|5W~&tKK>FF{2!F{`PkL7$GPRc{XnD{ILc|HD16C6)-f$%$?jSl{;LP@eXsLyve%RFI!3?sH;mE<hyzQ`02)ENybsy!_T#`'
    'on!xT9~SF|BFgC_*Dv~us48bZl=J1jB`nDl8EkI;!i*H&yg-O9G?}5xv`8qT73d04=9hRS3B!2nucna|Ks&w)>(0PBab6$4XC<)T'
    'HBW{=Y#G`LD$~Xv+39&*On>N8HC6Mi;;%6lk+CXI2;Rsl7cu}dClrLIp8cVdS2A3!gKa*lIAyxSuy1_quOIzFrcO(*!ZUNzONJ4U'
    'GQ>w363E?M-_-W7+~*_r>s$Hevb$@awr_u>#6!Wn$Hdt!#ZBewrQ)9&&iS!Z)`cWMLp7F<=`plCnz^zRlkVDkFxQL|@DZ3%23_*K'
    'k$lBdOqb6_QM4G;0)qI}ekJ@wl0qZIVEcq$U*g)%AwM|lSLv;w!7M+LY3Y_{lXn#Lp?o&bpN09pv2AC7i0!Y{<h-}#q`-lww>%l%'
    'WNMKaia4OKzGT2Im<YB!3?epWxW3GTFI>on)i*5Wu}h^?6R*A9AfRNkp<?uT<}9mAuN<Y(fmv>`MS-(cC;y?Z#B&w)qnVN)UnzsG'
    '*%)zG1(rab=4E3iF=hF;{v)$(D?MAi^PhMTWIz(Eu2SX7!PI<mu1KlH*+lFW0UL-#E)fWM?GEo{imx;@mbw8gzRxz7-l@r!{|N_V'
    'iKs^JK4WW3@_4<DMaaLjzNwIUSeM__d@{WF@+lCJMa)4P_c~>X{;p+Zu?p-T%sSVG<hMb{wt~0p|J|X>{lE+>u&OfStG0FnEQ>8!'
    '%XOBI3Vu1G>MJt?N%h}&3LF?Q>1XC(HE(FDD<>9)bLg<&6Rgjd2Xks3r{CHy7`wLQnJwF}F0Gd$kD3V=%=|_^qAQ0WPKI~Jo#ucp'
    ')nSvPLhiH%d`0Ut7U8K3i3*FX{@)5*CPGBsrR``_uI*5PX!)Nnr$FXpH*pss-{5?EI2`csBQg=P6p!VwZRnl^ZDV{_oC&8)2LO5C'
    'L?6%Bo>_;;`LMAwS4r*MD04xZ(!$2t43K$A?z122^8QP5+e$Gvg68ZVZ~ZfWJ9EVE!}t+S=Ip1d^T+q)Ljfm>?h16I+=*t6MtW`x'
    'vjQmMK;X353mWptrlG;!#~~s??--U182AR7XVs3>ncCUmt_;EIvI5!YzsWoz9@+Uuo>Z0>Vl<l!%8wa3v9c#D^YUhal}H_qt4eTq'
    '_^Vw2M=?SkRcdg%ezJ>9c{gjAPS+F2M@RI-O1QIVs+n=tafVo^lV#U~QonxiW8_jIb8RGd#S@o79B$$`8iM<Vg!f}nr6LGK{LES!'
    'Z#3Q&IFDB~8ZI<1s*P<I2rp_eDe3*Q{~qjP)psiVN;zv+J9)4wEpH?)QKq{FmkGT4@3vuIu-qlH&TZQz0N2!yB+l>Huj&mRfG}0h'
    'NWzP{zxU2BF;uKmE(z~hH1WVd?2LXnri8}~YNu=0_q)hc1aO<iz`6@(?#0|)Lr#AO^yOY~i$GHBbB}askqA0&0NFWZ6wJwf_>3#p'
    '#;~ogRkc9PV)^an(EO?oJ97+HTwvQ09)PS3gvp#;8>gWx`pMEkxN8*cFgFwa*Be#khOi%X?l0!FnM~QliiCpeay}>`p;t~2m;yR%'
    'kza4v_)M<HVWi^F(N=L7_R|?WP-PZQVz^P^zQY_cv_~lkcg5;e|4+I3WxJi@R7?HH;qYYG64MLPcXl-{RvZp^7Ar9k_Z52mH^muc'
    'kf9&cD6*$i`hn9nt)T}wX?n#P(b!*>x&nBNP;w=dzcfI+H)a6U6^TKz-Ev|QE))znH0UaJm^A5d`f8rDWG=3@sO;1oegpj7S;05D'
    'Q2E%@cLM#o!((JCJ#BvT6dbt-zIV5i+nN9S2}`hkFv#$p%g{Ak?}x*4!$seCPoT&Tc}jSF&re4WjFs3H;`rA)v~ByGgW%y!PjF?X'
    '9wOfj?3CLTE$QYjG3L6WCm~?UcT0M|%v>El=zqA2R!?fwEb+QfYt7myU&oL|L3L;<YjNV!zYqK>n85Gdl-+}j=8iM%7OO?f3Gk$e'
    'P*L)&w=5J$g@zw-VL%S8G{80bYdVe0ah90Eq&YaYVMvl#L1A5{r5xJqQO(I`kJ<g33zoA)DVHribwk!wVRb%=Ey;M04YL0=aBgO?'
    'JI_`Cp~ks{E*od~7WXti{AOK=HoISVXOue$VOda#kIojNjn&oO!nK?TRS@!VheG!)sp5_+&yzA<>0ey@j8_IElM$#B)}b|=DKFPY'
    '(`Y?d(PE4cynMcb3`Jc(KgZ_?y&f|B|IJkugl%`HL=38F)lLw_Ir;jUzo!7kR-pcRzZKAfn#8amP+(jTgo)7fv5EGE#>#S8Jh?*E'
    'zxFZ5n&wxdOobHA<TP3Cw1L#pg=tA+VyQP1Ti}d(hy#20wD$y8iMbctREpKyh7QyQRn;&;z4W1IKICUPr>o5Oj*^Cwmv0s{Dd%Q{'
    'GL+gqWaTdN)4BJic$)gD4K6h-C;Ftj{HK|L^YqD|>ngp@OKxj5fK=t#gae#BmbwKDvdn;%iXFB>3j?p6G!jC5VW!joh<TuEED#Fn'
    'OzLLsS=pn~rS0tDP|3hliA0JfAc@4#fWMk>`S2OS-w`|ek%8bJ+Y}IPhsvDBY!>8=@R!PoQWW_O02~kp%OywIo??UZ5@Tbl9Xeb#'
    'W!fRKJ3=e)t|dVEm1nLKOh<jI?1AJ=mDizTG(=(&jl9WBcl-dQev30)4`%2qP;t$m1-0H^p0v){tQ)WPF<HlJ{w==oU(>wwLSO08'
    '`x$M%=`oN;fQ>jcA5}}!v=nrQQim+5i)}o{k(EokTIQ9UWAV&UihdRNU(N+aU@>G>S8?JDfcP7g<yE?Sa=Ws{Fm1IXDC_q}!3I=&'
    'aNC$NSf3Dz`AaZYuZdLUwCASw^hdRqvdcn2obgBL<?aE{IXm3~RSA{P#|Zy2khl!J^N}bZgk@xSG$|$Kj&^gj@ylwMj_FZ*j#AwJ'
    '6|t^?0<ujEuc2wd$umv~5lcM-@lgBYG+Z%gf&@Xv=GQv!^fg-uzk^$~<$ZK(NbJ?#L2Np*oOS~Sl@Jl8%noe{JF^6NRbf60p5elF'
    'Z4@~)&}HBH<#XP?1@#k~Z%dYZ^3c5lrA(Ajf8ln63V@gPX)Ax#0~7m^M3R5$bQhdXF6Jc)kvokzy)#}?k}4RC&n#^>fqBfG&(C`u'
    'iIvAZ#UbIB?|D7OY4tgq!j_g`6>G~Klg6T51_{rJOt-%wu6-d4NG7KCxN`RrGHgcIBsGo1j-UR}H23m%mR5WrY&A?D+p0<^eco`1'
    'tfeCW2ICb;gpkuUXz&*5e`<LCXJ2Nao5i=&@O{~oKSD}u)e9(U)>_B=H7MA=IB;U1`h<u2pvD<`YLRTza{I^ageF3g$HBY-v1~*~'
    '0q3y7(91UsR`4lph5pY_VVuz{arDSd?S}pkmZ}jA!uDTi?;&g6{pr|0U`2@1Je+(%s-<qehC(}^Tk;GXG4G~_->_-rkIRBpt5F}G'
    ';Q*@uLOCJ;kIgeOL`psjKmHO}7Kp5tKOU1L(ep6wkOfsINS;Kx7}}8Fd3A!5kB`^=JXq_xS_`cRLNyutSy|bcsv2KJm(vffJ32rq'
    '3WV}rPW16-dY!<`r#H)$U@Hj(jAlZ<D2A~|c%pv;GhpjQL<)XdQfGWJyEX-rk%m1#wyZ?QIj6c%H1aSBoS-zk`+BE$L@elmZnl=X'
    'QBFze9y3N3=)pISYDo#3I?_hETN?{=J83Lc@9$846*|wC+o0MN!)u}-C%|E?;3h)lAKz!m^S&^!LE%)2)!g=dYF(^lNz?R=6K}}6'
    'ZcHdawzPW*@m=D)vWZbHFs0JObfbCf3gDok#Mw}0d%gQv{nz>$jEz#P4SaKr!{6B~wsEr*@!&^`;IusO5t5>^-gnE*&-94dCA2@Q'
    'uHVlhfRLv8?e2ncI?Cwrc>!tuq{}|l*VK%3h?$^vcq>^)&A0)*V0=$BmJ7uX@zoZvBO*)8+1ADRgW2~bXolvjq|;EZh_LN<{4tHm'
    'Q}=I8hn+ZTI4oj)A$cDmSlJZ}!g0nXmIa@hG9)tJkXC6og@7|ug!RZ-;`d0uC$(%MkymeQDB7a|(wKhdatiZkJ?LhxV|tI8MMo*0'
    '+Vek;P8ueh<hE<OvF)(q0!~&$C?NIhN^9tE7YZ<qhL%OZ-OWR6hDD*PPE>TZF$hf+A`hsT{;^BuI**|999MxpJbr~ana8<N1o7M^'
    '=U-J!Q!0e&CgJ(Kb76+f+N<Z9QR?juV1=(mP!t(mv&7^_LIWHPHwDeANeDRDDPo3Od#hFD$QZ-+fOmyAf6=jjFMEAI7zK7O94`H$'
    'Ow9xZ>1vpk>RhmlgJW!lQ@sYu;u@x|MGj@1rW<l5I9_EVFoS3pMD;lHG^~%>A{NlK>>E%P>5^xv=zmL;Yp6NEI(Q623|csDDp+YJ'
    '@5ZipWxuO_FG|()ZAXB5&L2Cc?ZudzfDCYh_X6~=+F2gS@(uPR)JnH&RH?%Bgj9|@$xjV*F~YT^?@|X|;A)VJf}9M^6m+~^jJ+Na'
    'nXm{he)AW#4M{uNIj`dVQh?F0JSiaeDF{%KxWX#V0gb3aWh=bftf7{$s==+qTWGrmOrW{tO^VU|kKk+&+EZ+848W{n9P;zEii(;H'
    'D~aX&a2Vgrd<6`^I_d@wTx!7_HUf;5%MQybxl=ZB4q~wN_|V~ec<j`@?~*OodgXmZ{=IeLMi+eJHzu`feYF{H+uNHkOCk8T&&23*'
    '#}YF1Q8w2K_5NyDA}3Xn@wHNQ*9Dy~qQ6Aoq0$KD4gT=)Y`#tcF!Spd+*>DW?9#YhwvWZai*u#CwO0$-GY@i48VkAR^>Vbi{T9lw'
    'r6>}+f5@o<Rl0G1R@*T2JP?a1SXJaDWWwe~qZ0u5&i)CjZaXQ?m-SBxmPyk|5J})@3oK*zYxxJY69ym4v7gkg3B>0Jy($RH(CKIg'
    'BQY(`4TTkuODA3Oe%5JTr}Mf7Sv}^)CKFG~kI@EpL)6I_J<%*e-M=)(gmMsaw9@1I`B-(y_jy_w=9Ackhs3{t?m9}|s}w0Mq<x3q'
    '^Qt1kdcPZ3knJx?!aUx`(h8j1bJ9m5f1tB}dje;*M24n|@c1=jzB~})<;XjsZvuxkqOZNB{(lyK-iDSWQfr-oO)Xt7x;ts>rm8^4'
    'NLYh&=;J(R3m)WTU^R(wXkY;ZkM-tW&AZT2m+7wP!!##7ji8AF<&)ky^16B~>gR3P;G0?d3A6cKHId`6Jyj4DU{b_P1FR*Tmkm_i'
    '8&VG32zbT4=Ub7xvA@+X)&1zUNW@GWeXW6Q6I1-+jRvq|xzPbN=J+<F8#6kz&&2x>YWlnYU+U;=*e?foag-PS@KrK)wLM*~G1qjc'
    '$>1hwtOU6_39BN{!OU0-LeHiw3r<J`8!MF1Op?KP`UMb#ku}`TTbR3%X<6d-hAqm7)Vvxe{E2e4v62eZ^_tyzO<g-%)!5A{9`U(i'
    '_3U225kL;w=GkMG|H}uQ2Km^UEsO~}5?qk_V0FdXUDXggmqYFQkuRL>6bn3@xz~b!MWg4VUyZd-4Z8-1zSkthYkfIbZcPOI<#8Lp'
    'vMP8Yz~Wvdw+U><Z{*F!8<jAl8=bdNBn=&RNVx{h-se(mFv~VQSv2f(zI3v+>6r)L8D%{5mEmnVFGyZNzHebw*gPJPbtXLjh@j?F'
    '@3kLwhW)RE#uD1bl3#dR^MWR{8rwhMfA?(N+FXF|1`=BnJ~pcV`nO&?U=0E*bS2`#fyct{4d|O$qHJyq-8U$`MVV~-aBe;&woub8'
    'w3=QCwZ5dCs^mUPML<Y4MGFDl@*wI>T*eE(HC)lmZBoy7$Q0Rdy>qnwC^t$-5WU0|SM6tKY4vC)Ud1BawjyFaZD$bklw`<sD+$^s'
    '6LEx@J=@$1@e*|l-On{R0dUGOLxZ~-5WjYGorL{dKX<{m8!rDeSNf3+e5gK}wb+JH(*>_dMt*wNrtQ*$g$@-jtS98HAf0ITH%J}-'
    ')OO2eYtdQ*#r|$7gzV=h=SIxzZ@6>yQsBohBG=Q+UQ0vTTjg*cg;m<_$u<-g3CF&^f{{^Rsbb16P`3_f1|2chSYai~O~}$gVM5gP'
    '1{sn#bu}Gmo)7$`OM0eklQe*8AG8|4OXCcl6!q|_N5T;^x~!8?8O)T#`Kx#(Scx-3EOcO_wBkodzd2t9z2Iogc12t=VxzH|)Eo^v'
    '=f+E-L7BK!y@=r9Y#&zd%55Y3sR-eC`CZiD%BtOyXZde}Bb{p2&iPH4n*6$LgRG$Zcbha&p|R<5rP`^~v+V3DL(X^feNMkJ-WOUN'
    'vtWT0CMTcsUfI7}bczT)!20n+M4|B)k6B;{0FZHgJ=3*rdhE6CnZgruyIMgtJ$BTXnAkI1r|k3>Ft0W7lTt<`_aL`AJ+E%RH8ac0'
    'tnYQn)(6P85&x%~A=##S<Qs+L8f6>jdxE9dodpBWY^+b)1-(MGnO3x1PWL=-^^VWKORrN`9-@yGYun%Uhqu&uP<pFoAi^eh(A>yJ'
    '6n3eW2B6z#R=z{Emw~R@HK}6q{+vc<S;oos_vuh8KG)6SUc%Hm6eOd=L74bEh_LF@$|i-Idz-n_6H>2+I_<a(;QkgBxqMgLOoY)v'
    'b{4rZ`9He<-@xq6k>}P-XhAVKSqP?P;V<?7=I5YCht@d@g0#J*TYY$q^0pD0)#Hk{iC)9*K@$F|g`r!gj$ooI&erS97Q{~056Wu_'
    'b``Ba#3_<SobclIG3<UK3&KtXqK-U>WAY_fkb>PH`!0#@fe-t%#GF9lScWCtdFo0aXn`;7X&|~F(@<`DL_ko9(@s`KfpNeh-o)h)'
    'ITI+u#vh>*C}*!NGcM-Hc|AiyLP)DbM#K1bHXy;niLsy?UJO@Cj1zk_eijVWU~G8ld}<h2A=M<mpTfh|8d%Wc7T>R1DdDMP+%%W_'
    '#6GYqF-ATWQ*~5vUM}W`=Y~hZ0f7j>_%OBjHoXypIklJAtbWO8>C^la)!T<yL2K}wns?4{+<-|hnIy&ZN%x&kLWexN6I!u+@SiDG'
    '>WVG=AlvHWpo&Vw?weW5t&eCDhQ0-7W-eZ@jB9_|AM`%oqw>9~&1N6$ynNJ|5UOoi0<5)XKTo<_y?Zo`vq{DMxN&G>kIHTq1kuef'
    'nB8C*HiJS*%C(KP<Bf{|$U$}VcAiUn{grIx=o8Vz432iCkV%mAegLOymx<>@cp?Y?$;n_0qTOv>$!BmD_&^A!pWwEtyQX_a)SM$Y'
    'S7QObny76+09s*89~-Gvfc;Luc=-_o)J*l&5lTD+Am=fY6A;H9^}yhWxx?S&{qH)~C8DIZxcq6|HDUaH^@l_487APLnn;h0oi5kA'
    'P#vIZ9uZf5mjEelW|QomU9uLF^`-org|Zjn?<}+D3HXm6{a^E>?EE4n)+ZA*&4p`g*?1{MRmiT>8s*kugU)gn3}e>(B}4G*SUS4G'
    'Asx%8e;Sr78_Ufv0KDC}Ki#$Z^x_G;HZIwuEIEXyov_dc$DAB4y-V!%t9|eq9L9{<oQYr!{K3MVmLWX)m^4_}7o#3Q(*%3o8SzbD'
    'rGyV~kt4IrQ_ba}u~qoB@cx8%<n9kwb)4OjJQ2T<U4}YdSJ!Q#kL&GOZlO4m^L){NcJ+OE+S_{>@9NCWJHg_sI__%S_<u;!Wk2~l'
    '#J*Z;Z&rckjwY8@`A;#)m9Zu}t5~pMhkOd)*%1uG-tzVFIv6MZ^X^g;RI#jm`zM$OO2XM=tT-R|ocd~%OcP5cOLHlEb%x!Nn}4ao'
    ')nKB6=-kbX;#u4S%{#@h;t5}Wz=0A1&0?FKj@}dWVy;04K(S`q6GSAgbv-#+wl6-Q<xa5MyB00S74?=Af~zOL|Kl~HR@&?M{N#T1'
    'ttFU?i$6x~OGJ;G0f06~iS_XS4)Lv-_Ze-`*-L=i|9=w`paXb=_r=EwuJD~Z|H+`JRVACJQ+MVqY3VAkEI{_$DMp<W0T!^6ClUV|'
    'ZVs_uk86zyAWbL?@ShyJ)WRUv#MuXL$>~0W)o^vjmrn#%jIRpK#tcXbX@3=<Jn(T;w7V_o8g4VB*P;*OAib{GOdGq+WGv%-@R+hc'
    '190pQ00V*Idq-`*mrFA~F~(|FJgivJA$`E1XG{W8LgEM}fa08kmW2N?r=U`^6UK4z8K6>woD{XkE`xrh>2X&QSm)em6Q;I-s{)Q6'
    'a~H&biR~E1VfmtCe0((qXetD^InKIB>3i^LVa)I<q;fqePrb<fc;#JSbl9veyt#ltPsQBTKg-I{_cf)p*L%oM_(P@g@~o;r<}z`V'
    '))NEjuRFI$i^FrY{Q4*G6Qx0NbW)(j9eG0i7BHGymUuIS_GzNOQD!M(eA$vkvVED+iz=c}jWxgD7H(o97>v#mKpM~ThL*lofPkBO'
    'Ny}U);02}7y$%F2up{P>G2jT)3C<Jw9mjF@o(IKeEKE$W4KCylQbQEvDE_jn^Hqcr@ZoeQmGZaszUro{-2ZvDc%d1`Th3wRoB|iz'
    '7IMORW+$c&Kva_*HB{%->r~R0l!3);1fU2koC8#Hxs-)#*s^bhJ=LC?9i~C1XzJ>yPl;vd{gt=%+m&?J^{Z`R?3J4EiW9HDV~5?r'
    '-$^%TA3dmZbSI=APWDOnU-qejzsMJMfBA!Q{iA$ZWh$ljfAG=36I9iB6r8*l*og>rva&7o1mnZs<tlOk1Zcu$T8Em4dU!h&MI)`c'
    '#X-T(stA~kMOn;z>TY@GV@>-X+SgJ|=6mV-KVt^?W?>5GrdmfV`_tk0k_;u>pL4V+vRkurGC67<W@g3b?{zS}0>od-Hm^8!h{`=@'
    '+WC^R+iG?l1AF(Q^?LbcmqpIyXv67-5v>=SPmiAJyoZvF1ew`MW=!+5ksSa-7rtrcgeU;pDXpvq1g`K|D%S0-bgUyre;#3WuyPgK'
    'beg~3cZncSfzj!{-VRe93Q2EjA2NRp+Q!I_u*baf@}OtBBT%^9za2%@Mlf};<&Do>aD`Ol<gDoQlCBoal9Fq`riAwjeD%~`vQ^t`'
    'MUfASn*3qDc3KIWCphPvqE0$ElF!*HP0r)%6asKXQ%_0u^=Dwxp!7=T9IOrjN82PJ@!0nb7D9!rj!)F28lzXYMN3B(WVs)9<skCo'
    'J5P3Vc1V{-&t>g@Xw4n-J4p!|W~~G3R!?#9eI7<A0zR(k@c0XyE{tkp+5J-cSAAxDS9UD+%;Gl^A@u0QNO;I`;`(@^c8%3D06FSD'
    '`!Anhzw&-UYNB*J#b5Yle@Q5^=8?{9%1?my0PwWO3w-T!u^!@TGKRcs$;^{zzK^n6v6_OQ{qJorK>J^WO1q#sK=&B#;c=++{Q6W#'
    's175kW^Uzo-fA|vf6;4@8tBNqPcyC_CoQ>VjvOjM^+7>RzG;uVDmVl}!+q}A;{twZ8=5*1#+p6xeAvw~>DKu=E}u?}U#6DhKEJ)8'
    'v534HE0n<XRZigouzcpgT)ZMyek|qsf{)2)Vh@7HU_oi>t#@BiCRi>aP4_Uamb}o&`TxnR1KY?O*<`<m?1K|b3sD$qTQU=r22nza'
    '-V9Tsp?e@I6!juaBAu0O0o>we2f~Ez&0eL@7m!;_+};racX|)FpeUyV4a&`(VK?kIzHal(#$1w=|7b+y@A^2T_b9I0yAwUI-++|N'
    'M@c`_ILFnG(<He!H;~37Y)q_?L+Y*rco<VYVEfp5YiBcqWY17~f<ji>cBa^Lf$s>?0%3)q56a=Rof69$;q<atN&0mG!+e_?G~Yj2'
    'IJZ`suIQ<wtk^2ZlgYf-YBx8|ES&(VZz{-gS9t0(eG)zFK2=`LPVX>2U75k<^$T%hMDeo#eDA7CS3~(xpCpRyuE~lv`a*j-^;SVB'
    'TOKKvpEn@)G^}hedTa)AbGC<C4R;bShSenv=fK^`<)F|S;)JqirWR`@@?@Z|B$G%Il>YBvjjnV0w6OfJHJ@1#D;+R&Cd(Q+<0PoJ'
    'C|K}zZPGgVQ;8fgjmw|R2a1m8zEeH0I)&DKTuiTFMZ~qD|FRQqY~a`wk@LD)Qetj`WLL3n2l@?g`e+H>lbe5N;P3SC@wG^$@a`s1'
    '<Kl=-&Q*Q?uSN)d3u9U5dki8q1}LQi_9e=^4Ywk@U<WE?{NGI`sFsgwsUu${OMCUrvC|UZ6eqZ9Z}(;fIB=2&Kv7)aFB{*VG|dWA'
    'q78XOR4bR%HK|uRWQGh0BZzq_v@@_*ADBs^)-Uzi8ztM~IN)#|CXQ%}F|z;VXV%lGk$md?XupQRt~t6GGv9}k5#gAlVVWU{8ZxIo'
    '>)!o(YkK41^u)Jxb|iRmBAaC&nmUC#a=6+aB<6zf98hv{d=(_;O95cYhy+;jR~GFt^3Ze|1kvj4$rMPoH`!UFbIy4hJ>V7=W7E~F'
    '>a-IL5(=SaqsA!f9dmtNXCum_QnT^v)8$VI;Vf0|mxSJ2>mM>Twt;P|!Px_<C(*AiHHN&8%;jOv{HB*vbFqK*Ddlzp^O=y{vIV{~'
    'pI2}c6fY`M&N4oIOBs|^(5G0hb7B!Y_JQ2OC^2X;GnX20A;0N`R5nG`tb5++LDs%RzN=KRb>Jv?$5(%0#G^5aJ0V$SeN50WSuuB7'
    'lRT3lk_}rfHh1tlPk4pU>)6l=sl!L?bz`_u<R-Ksw5GhFM2Rx8+ua<+FS*%@x+M*{ivhsxgyM@Y@4Ga-w_{)YE0}!7=nM}0a3zIS'
    'Cm+eif+KA}{bHDEQ@RhR`zBn&;lmkZs}n8_o@Sg}e0>O_AN8Z%>(YB?Y;<HJk8-nQfB4j<-t%whi+b-~h@I{ofVqMDBy1{8JU+<4'
    '8#2O~t>kXqq3_Xjrt}xqM12N&&@>t-+}nf!(gjDgXxNP(y2GTj=7<CNjUw*cO5;X>T-GD_+*4Zh3bKHm2XtrgCH<uZ^e%cl&hK!D'
    'F5~EG4F}aPX5ybfEAZ;?)x-BgQ#y8!1V+nNMDD72edT2$gD~IcFs5ey%k*|heTCi*_r+*OI@qRv)HMDt)$qOX`-V}XG|h&a1gKUi'
    'EoP)-6ACVzABKdY@Q~S<+Pf+<PJ{J&%J3quk_NN@j9})bxt|m=`g!v`@v2V#EU}(flwjxo&eq)-Ad1&zZZ=|_Doe3BGzM99M_&Wv'
    'I$1hKgHJjoVX*KvqDk@RLr0s@o26$h)Tw6HibpI%*r^~CCRuXWxBQoae|S%z9Ahs`u#w5lQRrP>A4Ve{4ae=(@ZfK4=d+^YDt;@7'
    'BmM1rqkjSLDn|2of;vpuR$zD56auGhYO1OSK{dF=J<_-%d8e-$;srayT!8O{{$3QDf_L&nDMcFMG^m7%lOa5{mI`v^FAXqRJ5hO$'
    'j0px;B)(Xrn{zlazVG4SaPjs`%a=i`38_w^5HR=T%|)Ns?TjIxr?JTitp)tCej3n_PHX^=CA8g)U_d+OziG10r=#GJVFDV!n7})z'
    'm%ZUR4bX*1`06U%TIx%KQME1~bi4VyXJ+7<ET(%ovNQN+7FI8{Fa27BoP5?3O^<C=(VPxAN2HevzlzuqKktrxjgFQ8fF3g1w7a!3'
    'gk~ef)V!dz!p=|Bzpw60<Vla1&PpHXYX&)A<=wPv`m<7J;HEEwS2y%q;b9Or2?)xhAJq}m-46H--I&#>d^fDrQ+x?e%6aE~Sp$i('
    'O<&|MJ>nZ5e`qe3`05?pj46F2b=(}!P;bb!-4RDV==?U8uy=NTBA`SuKXtXw?Ypdri|2EIJ#f-AU5u~ft!UJ4F+Tb<;&3vL`&_fw'
    'A$K8E##ZwBwPDmU^b`XgM<rZziz>M-orck`4mQ@%ZG>jp9jh@~9ZHD|XJ?@%tkr8Qf=k7yujV`8FM`0arNRD+(b7M$6hvrdaes@X'
    'UINo7yn&%@D}z@K8$*D{etRvMOcTo5UiFU3gil+!L2d5xDDzxXF6Px50A${aFu%(zXL{J7G26TdoAf8a25jr*b*U2=3|7qi^dGU2'
    '<d2J%(U~-14ExQqk!kZetM~b)&Zy^JD<Rmi)X(9KPRku1HM44{@QpO2(E)^D*0r($#hTeGx)FkR<x=S{cNIH@7jq%mwAe+4`v|^B'
    'Un8FD3}e`dIaQcK=C}L8420~>DFH+@{x@lt|2YR;V%pF)k4pCO64Q(NbW>YbC(ForED(@tPY*CvgcSTvzteQo`LDb*%R50Nz{e(s'
    'AQp(6gudga{$UXaG|zNCppjy0W*%EmGZBE#GWss?#S6z=E-0OWQ6LzR>E-WqBW=3Vi%j8i57+OOr)fJBnyMN#Q!e3Q<_;k_)eKDa'
    'XC(~H-(haam@<On+l@f-i5?iWWQpcJ3B$@%;`^642K<H;FgH_3>m{0~j2F;#m(`NDARx<+2nU**czV%plANvh`ScgqRR(xFp1@S?'
    '^)$rxxR-Xf7~3m85fiN<Y7)Wx{&tgZpOMES-M;W3>ii_kM*b0>>`&R*E5mfip5aFDMvNYRonwO`EZ1n=I%0gA7q&?i=L1!|sr_~0'
    'Vf5%dU`3+n4A=KItfqMkV`@8TRgw<7eg~^U6C!f9YRoaoFYn+2_h}pYH55l1RJb0{iwJ#TyakYK)L5pVG1o$Txhvg9h?LsCv4fnR'
    '1v^^iv8a3)?5iln*F$5mJiAVUok|bQ9+8zULj^WkO@2&**3BQj;J<14J<f>^lcgyfXdmID=)B74TrGY-NYvp1yJw(p$GSFut+l7|'
    ')C_6|7`;oM<Yj1<k61TSd(m7cU7Ob46e%|RxWgACrrywI=QH-N>=6W{;){X@j9hY1=U7MdK7TlNXpL1AQr{+VcIGvZWvD1Y)&O?1'
    'LfOy418vI$MA+&h%aE&=$Gec`GG;hUN`{66uU;kGJwaj;(sw1V(Fs~b*JWByzvLFZ1cotf_Yxt7dcSM2ZmE$^-vU&gly=N;6I@Z~'
    'fk-uFVeQ5jArZi*&Yolvo_icXK}DGKth$-riS63ck6qwz34+t5{U!Ch7c$ifLU7r&%Xm?|!nk#=19Q_P`hUnLUZN^-5Q9n0o<){8'
    'PD+DKy=v5$MOchc^G1)P8y?9F<+9hJ#~3yS#q1Pj5OVYyosz(ab}3&HCYxIq#jYcldkxvd6rzkb#scu%V;;z`u)gRtGK^VLOaI(Q'
    'c8ab7s|q+Nxa=u{zUlMPSh=r!1d)l?A^nPAL9_bw+bjoJz8d=yX2y%U$I4?8E{ev;@Kys5?XgMELoX3`<Xz9v9MR}TxAN>lKeFtQ'
    'c-&bJ_8vaS6E)<|`zC!{#F=cVX8UGe6w$i;u}F7=s+s6;kfo4JC|X-Bs5ps}0W1u5xY4+@DMtB&HvEh&k53Jphw~MqPl#J<(G{OW'
    '=r%n-#l&0aH055`s`R7UuB-dNGtG1G?*>faR$Jo-0jc)VHDG(f+@~GTOk)VtZ#@R^R4s(D+tTe=CI!_3)~D-0OUVg}T!(DWs%1lY'
    '?|nY}paHmuLp|wP6>w&Jq3nBzwuYfHOvmn7(LO9ehkkxb2q}tFppiedFjMHuSB61z(&ZBSlls%*Gws&6B7S*Q`jwJ^+{$afFJi|t'
    'LZfLPlS*BA4y)`pAk1gsEY6IitWYmgQ5g7kl~v0xuIsBK=31m$%vQ~*4Tyu$_R4RkrBFB`Yzj`~+b>}{2Nb`Dcs7S<yG0y{{_GUm'
    'A!i4F1RjGjX^|7GrL&+cwq#{+p#ZnbKdH4{vHY$RQJ{{8eup^Pr%$pjkh<fy5Zz32hQVRCOV!`dHPX|J>sn8~4fr3*U)SC#<kgk#'
    '&+6}<)4UC&cPn3jS2L0i81ET+eR&-d&0a%(&M@<5RlIMs2_S2u!NZXML%`iD%{*71t7*Nk)P)Ni=EP9IL-<hnT12ox{Ro3F*!{JY'
    '9=?QQ4wMO^U3%<A9z@r5^NQvN_c2khtH={vMl_#v@*x)7De24Mh*AOT;bYAPC+W=O82d3$&p;$u7TLr-X3-bH#L|<#fH-mhOqU1_'
    'B+n$Cwbd94f>b}gp<f|{QRTMU7!MIJ=9!HUQuGwZU4=t;kc2Cm5vd{VmmJ<o;WSIq;cftMe62(dzxp@YDY|ZS^g!lbDgSWVJEszw'
    '-==ki|NUPUJgGs6T2mqZ(~updgy`C`3tPVdMV*BKvfPFUz}F*_t%2l*oU58~9_hmqcGXwBXE~4Ed)Egk)|17ShU6g+Hq=2u6eT$y'
    'JU3Jg?P-<v_40Yma#NE$mMwuU$a~q;>2Zay+r`hqu9SU35~z+JSy_zB(4rc@@fE5N;yN82;SRoz{#WGafBU}~f~%UH0Mt43UZl4k'
    '?3ds*Z!rt&EGAfNMr88u4f?m>Ibuts985}=yhWto0g-$$f5^fl^?IIRBIL$$1q!M?d2uT)aJ~PEUN$_*q;fHWoi%RaROZ(sn@KsT'
    '>K8xF5h>p1diF7jf7kFOOM^l#ty_G|Wgxh}aUDvl`wlA~j_Kv_O2*!*!zP4@_Uk!3z=&V*olX6=y=vr$UG&%xz)IpomMeX$T5gaX'
    'X>UooeZWxV$@mlNc&{D;Qjey>=fu7o0`ggY^;(^CsFS|P^9V<a>ELCoqv0)mizT+qmH&mwGlDluBAUx2_;h{88y&?;zk!qB%yF|~'
    ';|uGwwnQA}K8oC*N79oO@UAnDnv%nAvt>0A*NQ=W+=tatG`N3A3lDFQ8HCS0suo8J!vNM@pas>_CZ-x#Atjp2Xk;Z3A>RC{gkJms'
    'fBr@ByZMtJ@N!$c!}BZo=Bq%Vn7ZRIcl78xHUZu{5B5Uq*V3Tk7W63ED*0z53inzYl7CV(uQLy<5QzsjwEtdtO1SqcBT$y?$xl;T'
    '%?8tC7CayTvz`a{UJd0>qVE!+Hmf;Y<g})BR$9OcN8Md^`j(gW2Bl$hp%Z8+UkQ3Ot{WKWa4keM@C=XuVvWpt>FCr5@|6V0ys(O)'
    'gh6No#oG&k53<oLMfC&xayyz}NmZ+@3%2Vlyu&w%Vg()~mMu?YkpA`6-_*LaOzVhpX^a)Pq<6$8%o<5<Bcs$(wA9!JuU^^17~lt1'
    '|J4LI4H1J+wfHJ%-a6%rFHMtN<_?eUs?I<@R7cbL3mRQ1qNv6_i{!LXR%T$h7!&>k+TBe`bUw%u-_gaUqq)`0Svr7jxVR=o%iguJ'
    'u<IhAdC6EsA_2KMC`Iq>nF;sOz%uDuOnN70XN1In0{awNb!X*5pG`nONTyO1Jh|10HQgQg6Yg4J%*mRcLt0yU$q{|;q`0NWOlqBm'
    '{E3#`&aUp9t26a|%2BO|vG(LpP6@wMyWH7zI9;*0b4z(CCm%;EqIGW)-&T^JP!7tcVNh2oWy_~5(9~`(2K$=RJGEQO%m*)1n-%rL'
    'M+$F){JPF{VK0rmeA*>-mx#S@<k2H1ew1E~h!$-6LDam&5y=m4rs=p!EIcF2L%i_mzI7OwK5m~YwY~I+;evGhnveEd73l;<n-dsN'
    'x`uPWaz>>3Mij!hS8Fv?Q*bdN(AHo*xul$+<Fkp$Hp&**Bv0)bRWgAuYSp)-DE5=2ffNQ_^}yF8tz}z*>vIvhJ*nxd2bjC0twq0@'
    '{+r9l#72YX#%@jBMFxD?&i}}E-%22vW~q6X<i%e=8TXF1mW?{bpn%E)R0SR@=8VBBG~0G^eJz7rw}Ty{YED5fpptj*tU$p@*ue`?'
    '8|2V!_3F9}RS|uhbOpn+W6f_*c(rs@bo|g8tbUW$8Ag`eOr9_mZ1PwpmtI&Ix@bN1$1*R&iTYzsNI^(_e9F_)xvbJH#H31I<3#<9'
    'YrCc!X(*sENyA^|TaimR(lcaOnSLKt#bW{V<8fD@sT<W6lmlXGW0za<QGC}^H4Oshi?ii~(R&Ghz%7syta&hP?N#Z=gLiKyi7-g9'
    '3?FTF+nT{ZT5LEyx^S%%P$&v-pU1y<c`!nqJD6LY_k_Uy(V&h|KLmewni<JmXoS{+tRwc+j;mx_I0B$xFC;9<+6DEtit(D1OXi$4'
    'AxmyayaEdXW7PaYbPwr5>c;7@uQ7>Xk_2&54y*ti&#2BPy;-=6c43hDh7+aop3`q^GtJ}CBf762Nw9wn<RU^OHd+4Cw|Qd`ImW{m'
    'B*$1edAvFXJngI3*=D}v1nE8p;43*AS+D&ARxP_{7+B>iee5*q-pZ<tW5(l0gUOR`ZdsS9?B|-_8i~6^I}u!HVN(%_RyV2SO8^wf'
    'f#{aeGkV@gO!ep8mhDdhWoSGL4_1#9`iQ|WSK0%K*Q{%gDVoC2Qs($apSPJmT#=BuhKoPJrypn2_oL1AYnQAlbJ9z?EmTcQieU<?'
    'ad_R2Dn|ct)@sdTAS=zHk_l+%|KiH@;PR^>_hTmTyhJLO+tcw+W5AFWPeD64lrCD~+UU*z;I%yw6Y1qmeGXc`Svr5eJLyW^FfO-W'
    'V%<`4iZ&maJ3efbKCPY+iKVe1A<v?+#F{4&Y~rll={;xpPQp#x6h@%~u&`=VpNhGa)<LKQUKcHHhM%(GoV>%G!TLiRJ6kV5j*QJu'
    '$c|%bYe(AXBBFB%7HQD<x7?S9)nC>c`sq$Ua&^(+<FF4+=hP6YSy2kgCqED61f8!1SXn_Cj3d(u;xlv5C3ivC`rcABb$bjZmrN<?'
    'HRDFhCwv<_Q4B6X@>+d)V<d>$d32nu@BYh<!Kx#lr77OrMhp}I?@fmZ!O1lyXV|{bKrFv6%iLuAL@1%^{rT9x8vBFuU9<(t@eX;z'
    '4(l+!1AQn4%2+y;d7tr`+P9%}O6+B11J>gc`bO0VPW?m!E`+R}2$h?gw(RRCM07x^#kj%3-9pL00o548nB4!cM6}t^Ln}$<yThnd'
    'mQ5wX&b??%i2&)SnzfatZ0!tN(GNN#Zz+Z;1BI9)QgUz}-&e8uLxXG_6)haB+;Rvl;_9CIJKOps)=>bL3obfI`0@DR?gc@!CI`nl'
    'xK(nhnl?%mt|#;zm<PlP+V4e1q*lXn4PP2P$A90$p_><Ue>oOK%eBPi;-P$F!@$cFcsD?KM*B3L>&gRk9j1{lAM_BN=2u-Ad1}oo'
    '5@l7{!K4R|4mgVhKk4a_C9ne488UT!AjduBSd|@i3(d@`Mp+X}xLwkUhy%b{CcQqe?8Mjx%j;a6yXl<q)(mn_!RRy@q1;k<N<0%K'
    '=)@Bz+&;$P@|I?mp^|~@e5PgTIF)aE4uLZRqn66MC>>7Za03`4Mei!yjJwIAeJtxU?*a<N8exN=HE{~()64#W2Cag`ot_F37a~vV'
    '(Fq(hmX2QP@-=V}1ICOSa{bySWZ-GVz48jnVkkVmah9(EagWlC9IS^SUu&(SSbNy<tn&Z{a?j0$usd(ac5J@(rytTsj?Q4PURB0`'
    'Itb0s?)Do_m@~8U%DO)YU#J!e<~24-2D&14+j#{Xr6)j2=2|p-AIR#FJrE|$Rjbu|PmP*6;-u7G+wdG5(k$gnX2;GQ*gvOg2T^?('
    'O20)pE3f?I={RJLY#%GC?RSx`mD8T!tJQ^?b7UVvH>IvlkL5DzCh>X*P3CCUx))p#cfI}L=Gx6U`y{X{s*caiNG7POLju;^!QOQ#'
    'B&4-w=sfB^wUQkZP<8g<G8T-LOk|hn%usQM>2<A~)jDeSOQm5T6(vsJ%^a+hx<DJXuI#mtkEHCUcWl}M&rW>GS}@M`yvjYHGTYv~'
    'p`9rY6N3)-hK)ee5y>6~d*`i|2F8W%Hyy&LJZ<)p27q!Rto$oYG2NN6d_VeBc&xzXa)wW-NC>_EkX^Dz$KIQOlmqc=2sddtHGHMN'
    'UtljR0^23F{<0@eW)~CMYuG&Z=K!z(ozgPdF`BXbfYhF9G5Y8R#PRBV_gH$2MAh8;`^q8!5ua=$WC=$H;Ra$gZV4-s;`}S_BfUFS'
    '=%e*pgs;t6F_i(ejzsegoCSyALd$y|DKM2%5~FHbt!KGW%cVznJ`%`H92jsRz@7c!p^1)nPj%7ZaK;yalp>LFs9#hPg;@8>zM=7;'
    '+CQPK+CbiJcS3t5^I+qzFl*QDO3YmHHH~msT9Z;5j_D6CReXRbfR=Je07vueRwjPBf7BTzXNcp;Gfsq5Vun;J<=)e)gLC+^Az-Ts'
    '6CoUX^_J(G9MS+Ubv`M|8@Gd>aGy`VnvZX@K!e@Qz-yE5ot0zNEiZ;o!&GZMnU?k2Ut8eXsh8zwylFqA1R`rPgtjzEuIE@WKW^85'
    '(ZabrUmu#qeIVWI_%?`nfA+f{C(-GcivRb8(2pirH(<F)T(jza22dLl;Q;91W<}>ZYpLldurVAZ>_r4c7vCYnD0R=~7*Y#Zj~2vW'
    'rnk$ts!hdL>rm)H+8#XM?e>TbU=(7YDt^CCeLE)<nR23=!!{XR$m@-rPl0`~{j@U?bHgqfEGrJ-d@h+YY?~_h(5#;S0S~FVL{V5-'
    '+kz`W)_e{-G74Q)WZ(~5%WtaEosT9v^rlpCdvsN%ZK~*wZ6(<{28HJR)h`dTyW~UIp!XGfv80moQl)Z77qrTg6($5|Lsz0NR{MLb'
    'Pr*K6F06^om>Ri}hNKCE3%uP3ljrx#%M$7YTHFw~C5<TvFC@3v4`Q*^{cv<j#|tvAL8DqwpmHD*3ElYqr(W5XMy+mw$5+yzAQaUe'
    '>v|33adFv<*8LZ=%Ed%6d8QNqW_=h{VoT&Z;u-XY@6b<8&<botsU)=XSA6rns86et7-K#nrU<xp7%T{wO_lTv;IMiObOf{tMXiEF'
    'MH1136R18hw@ZWrbux)YK|UV-IoJS`46+D#@ljWi>6TJ%XF`tl{J}iN2O9cdX+WgAE<Q+OofIvUH{!LrQyQ65yJo2m2DR&qp~z&^'
    'ZRHU$HO~qwPZY#Z;F_u_qUId2RDgQ4x{Y|5r#P;mLTL4iPfis=Yp~yKs&z~BmGCbkiki8pXYmSHu#UXRD)_gafKY=>tBHy@_fP<2'
    'S`)^?RX8vaoQS!wS|<mk_*wFQT%CVhddZ`3c6A8rqnd8%`;yDd)092hNIZ!5CQL8U%gu@y{G$L^6L#@!xHle|6*q-N*3Kexb=Z9B'
    'h}g(l933~%$$vxH$(1M8T_8$=qyuCC{EspA?#5gg(3{!axe`U^E_4OA+G!y()|Fc#QyfB*9EZEAjPl_K{g!>tHbw6Q2WCwqbLc;x'
    'V<Cp$zq52-dl#~5tIf6D+4Wmm7b*qUZsE`|i6-N|gKCJ3EeiRboq)%F%fTHIp(%eQ9Yr`S;6&j_EE4Yd`hKbU(S_0$Dne&%1fbt#'
    'COFJNg|DCi!b89YSoE}{c-cN4U`c5f8pl8R*HZB^1-5S@R=w27(zYK@u?}%F#oo{lC2rnG;HHjpPcp3Ky<)u$Luy^Ej-M4;Elp3t'
    'gFBW6@Adob6>>K?GhbQCx1XiFWXqayyowt3;yQ7$d@;lCg*vN4%uz_O$@7}Qb=YOVB#p19G0+_sgVojq5e{5X`mwx*d)e}~Da5_7'
    '0l?6c%tPGQK!l~Bz6xo%HTS*gRyKwXkG=ea>Wync06>)E7nB|lS&Z}dl)u#(?Y47d)kjQJ^U{^4tu`fADaa#Z7Kbn7mv^N!9F^C8'
    '-~%A@7juHAHNSmpyn<=~eJ=tHEXMy@_>S&)lxWxH(HdXzP(N2BxxCGq`Ec?^7et!^kg4feAi>5FpRh%wO-V}jrkaF+1>sNBMUPXR'
    'o9p`j5uHwC950mWi3nv%g89I)vP6aJmDsB@R;0xL)@T(WwyqqI2H>x)rJ((CRZ!{VJbPdUN;8tF)%-@xPLshI%SEpg*9m>yccS}n'
    '+-4hOkVfKSv!N4bW_5b75yWOEJgkbmO7Rk=4UPdjK$`fOm-0BUD<pVqUcHeNL&{~jd{ZOG-#pMI++rE>r)~z5E7>57VC+{1gbJo;'
    'Vqge#H=0lWiqsXIs6R7u2!YzG^UkoASej2YXJwa(HhlL(>F?B;|JFT!fyPa!`?YB}5nn{C#i_Cy9`^-wS>9z)qVS)J_tU@H*eZ{_'
    'T@PBZXN$HJ5iMV*e81607ue$z3XXoA1F0;18jWlioz?~$;VV<BOuU*N(5Y}yn5B{CK$Jf#*-yfKNLEn_+o}P90OA>~6&$jed{x@T'
    'SJ~lW2}|hrR(O9`5oZHZ1jVN<a(;><Q{Q(M>QD>rd)*iGT<;kL!}8w?y=%OZ79;a{{AF{(@gvK-(maogj%@E6I8pfJR=r|Fl6@M6'
    '@<+Bh;5@UjHDroWPU>`O3;%f0q<bf?y<D)9Vb1UXIB_=+r#-KzFyxIk3d9^-`rm`Jups<DP<7ZNA<;5m))?(e`AWtN(zCQ7I+Wh$'
    'WErqcpucZ#RY?V*H<@K!4Ek?T7ZC^PJc~une%Uo(zeN6;+r~h_80)&!sbWiV96f@7-kEH*p>*9v!-}82@raa(oZDo)jm0+?=(lbz'
    '(~BJ&4=OjG2bK^OuW@=B_i}L9R=Bb$u9#)Ecr}G3@C47T=YI@fQb{VI!eUlrn59?kbo;>yX^}P$XIXVN^*{y5p1oIP$C);h7YVC)'
    'GY}EO=7LiOR5obAcfS#J_;GjLxELsuuU92)PVkr<^P0BkDj*ayTdPb(*jfS+qLAizZZ~cgB({HMl?G`*+a2s%IX?~elub#)tv>_~'
    'Go?xFS9{*|z5q{OfrZOQ^Pu=&M#B#EA&qWp!ngaYA?TeUC*x=ANsR+{L47Peh*DT|kA+F6Z&-?j*g|`Bc3rR@%gnSCg_{t$^IdFL'
    '1)}a9>+sKr&qxX{tcl$Oe{KiY2`cwR@|`^D7Z<6NRcy?yOo9~Yr&Yqcg>Dx8#_)#Z7VoPSf*5ua`CsQTjTf935~pw$eN4`~;$Z{g'
    'H!*3(bLx0iK)4|OgxZp{CGN$Q`ZPrTGPir7&A$V=CadX>J{+w1HkAzV^)OVm)caBL=lO(ExzPNz;CR4HqcqC9+EK7pKJrIZn8??<'
    'iD3y2z9{nrc?<7;a~Q1DjTqtAy<6N(CS4yU+!NU;d5sh7)x83<Gu;)7acbsxI2tj!ue%!*gtrIWxPcVt2qCFI#{PZVZNu?z<~j~`'
    '0HoVwy1gfZ<7-uGX5^VzCRgXJ4#aUt^pX<`hKY8;Z3rH;ppzq+X^E^J--#!{ysu>RY;G-HbCFRxp2o4~i7K{OqIx-4q>J19`fdsR'
    '>zVr4H#)lcdv<>%c8%Gk9=W@Hs;;SJHxa9Gv%=^7+}ww-R{b#|!Abr)@lt83wS*%LIXP<;w>xpvx4^rm5|C=KGI~mpCXS>b8ub73'
    'a5nuw$qGs~HmYf#NAHJa{5T<GD2Z{a#dPcnf|d|>kA?Jo#XO^wbmTccQP~032csT|o8W__$3(X9VYXI0A8C167s4G*wWb-68W>vX'
    'aF9_}JzL+0T%ntSDL+B!`%p2D+mO|n#L-czoFj3}0%MMqPWTfe#F!lSkq8zB)Zfm#$V{bmKdM=c$*@2wRYou~!8fO4sw0503H1?u'
    'edHH}{qdss%kp9c%0C>&KhUt&PS6U-50%7<jOepMHLFCPBO|~CBn%esAAi`W6pbXbrG1jw!*b(}nq(xCV>IH+T`H?**6Gky9@~X#'
    'lLl~*Sn-FkfCG%w?%_tm+|u19&JhjSW7Vlebz9MXYYzR!jLKLF*E9a(g3gLnTHQ9;F%G)Q@x#HX4P=dqM~YSqH~txY@4{IGI?pJ^'
    '*WM@0x7=~#mog3h*cfiroYeq>0164isj}pIbf3)eTeqJ$F;+~$rO!Dv>sdh<5@rvgj+O$2nsiOnF^hX+o#`Ds_!){bNS{!bl-G1@'
    '?T;byQfFU<xpWTnBSrH4KMnwPf{P%Adj&$!M{>*dgQ8YDX^iTGxNhL4rK?8KnlFs-i6A3*n}{DhXgCl5c26ODzcI9i`Uug9yHo1|'
    '5v>To25$C4Blgn!M5Wd#)&W&kkvU2Sr;%%V9zc-KQ-zcLS~YbfUMe@}8A_YiVNRivTdMzcQUsLx6l|%w5Rybbngd0WZVT)+VwbDo'
    'Ph_#Ju6VZo4R~7ND*mp|u+h<MU*bB6yg8AVvALD8a5++KP7^27yz{OzX^%OQ@QKfx7t49DGzBEf0_trY*}87<1*B(dG&r)lX!K+d'
    '%p=$*^+a{}hyq?GwmKeh9{ee0Yn5Ym5f*lc|FvTmGHhxp+VZBk`_|7br!!cIu>WUqOR(yddVJD~n!bzp$ER2_eeFp!@fD*Xn&%$k'
    'H`aMj@pmvjL85#KGN*p43znpXY#eFQ#K(k>4Vc9IFAFnP=gzFhm)3D%C-W&y5Z-fZVZfQyiZ_?vSG0CeU2N7IUoMkQ!KC6WS(~M@'
    'NIlnOE3(ftg!w)fj6$cY`_(fNl@qC6fEV~Lm4_Uq+R);qcs5omYT|7pu3kXX9q}25$QNzjIh^c6=kLex7?9gOd!{JBZpfQuS}>}='
    'hJS%b=7fKQsfGVwoyWLRFkRwbne75@xEM|S_q)3+t<v!-HqpUG=|u4YLMwXf{92TV=bHfg><SgJ?CiYjgDxH)Pb{U!U;JALR2<R^'
    '?P?j|pUCBkRX7tl=n_9v%I9!6J}m!Bk^D%0PbmoesKsVK)bCF-3<sXyBX=!078?&Uhzsx`3I%9!j3j?jq}qDtUze7w5LLWdP6&8C'
    'v=O(F-yc@e^H7FO4;N_}WDAsvh&Lrk2>lQxEe&2`c-q-8;MHG663{3&`Q-QNMqj6^9S~W$=);`SiO2E-DXK}Lfun4DEXVCA(#dg%'
    '_FS^guCkPEDO}(q&O)>K;OtJyFxEwgu7VcPz*@BqkE5ft>uf94zYY{^aV;#u^=%!tHlF|JhYYg{{DT?gXEiE$wgGkUl*N&X?Bs~E'
    'UmZB<oP%EXI!Bha8UVR{DD=ICu#EddLiP%caywhu6ddq;OL8l<wE`UR4*o(MElRlp7N%+KP?<-2es%BN#bl&Y@hV{4I`H9PS|WuO'
    'kY|T1s+=Wl!(C7mKa@{Q_~=()nA{D`Iw=ql(ZbHIw<kMfc-|iAmYA7fgZV$jCgslkof6gM0G1W7i#{g+C1!1^(EkJ4fklm8=V2vX'
    '!nC(C?H<@t2`O7u$vH*CSqa{J1)!&pj0G{;oP^gkco-q}!U1-0O#M&oIdNQ&2&VUo&7Z4dghU*WV~s0aVLy&-$kk6^C%Ckcx5~Z$'
    'Qv#COoqdDajPmXpJEU~|>KkAQR!NVC>ClyCGI=RynLyFM7fbC$jiBTZ#Nf?2DYF?0==B%N4orpD6PHIGQ&_UkznbNy9LOO6QZ{hE'
    'gg=(CowuGNIYLvi8*IT2BPQxJ<M3fuB8{xS`KTp>%Z*+wEKr*Qh@k_nDaA(zscPb`kCu7FTjM<zne_W$u(MW550s-`ljX4(WbKqU'
    'hQ_>w4T?{QGUk{q(BULD533}G*@0c!vG}o!WeoJzC|$jlHeRWF0n={*Qj=3ztt6+{L=Xd-3{|8Nd!Bqdmk4JH4*`c()N3J#W;@%)'
    'c6J9LiyQ?0lS0z1Q=osSk*yV<jmCbyfBq>wd~Ir(H2(5nMU<#F<lLDBW<iP<yJ|cDUa7_R%U#~Oo$~%gIPP6VBBLvex{kVpDvG-#'
    'KOs@u#0VmWVyvvCk)#?gI1#q6^i|%!Z4N$ofI8T<TEKnHTHTk46ae}xM&q5#GZ0o=*dHH?P+KB=(Xp)APFuF2U~J0te73{YEJZ_)'
    'k6T^FfKs~9Px2{sDfWQ3f#QA*R&nRai#k`jo1yCgF<wPz_y<9MNZK?N4J7IPIu;dkZ%MxYt*{yq&Wk2Rv3*U<NrB?qi6*18wYqLd'
    'JDX(taan6L=R;6B8!z=(lp*J;VNY7f$c4?UlJ6%)H|*(^`{ZgL<iZP&&ewdNOE3Z;|04+!?#_kgWXWJ-!wNU<D=znpgtc@Go{<~w'
    'P7z2iY1a7tmJ?-U1}s*i4mTZkS1KW3`J!pi(2nDpjVlRM;uaRwD^zO!uF3Z|oR*I5{o$z{_x#HaIc8M73H>D_hio?UoacW*?I;eu'
    '2Hxwv>t3=oA^JaI_00HGRCh7FohGI6M!;h)AgtU}<|iJoGT4cu_hA-q)5nYy6qkT=J{A&bFmYqZBg3S4UZIlA1I>oh+~nb)`80OH'
    '1C~LyH51m|vk61*u~m03>l7c()|A|Kg72xthRvo3|CQoA9eFNZRPxgMk11IpI6Evxso*y{Hk!hjsPRcA`O`zxs-R=P-jHTOAsIPW'
    '@DI(GP}y-$2IG?>@pu6qgsS8i^(5P-ORky5Q?I6Bb407a1WdPIf)+RSLVJelR?Y%-?eGB$A_}v*^6BOhu%`A%q+%1qiQ+fVHEG=$'
    ';t$EmxFctUW<3yJx4b1kqea{vRk>g7iwz7ijX;o2U8hU3Sfp{#4vrn!<?@Et9uVlz=0U|YY*wG?5*kw5CYPYN25TN@i^E#R>#Fme'
    'D!Wv^p;;7(hl#$Wri#}7CflyaI}mq+kwy5Rs*J7tD6{(p-)Nx{jdxb&P&m^=G@wxr|I0KRFfqotZr@izDk1`9^r0Sn9TOG-tZ2f4'
    '=q+^E*L=6f&!b&0%ND4yaxD5wSZnISxRJ;l-g!hKvP<$dZ)pLoR&7@}gw_Ss&$W5RK|fn#saYF*8Dpe0Krh#j>XP5>Uw@e>z{3b5'
    'WZBZhcX{teFeX!=hI&Hb$pA(|Vh&=Eq_6I-{m^Z$(TJ^66S|Uk)*rh?jY+y%%P%;%MD3Gh@^l2g9k8S_800cN^YJ5vNmo(C(1@JF'
    '|Esv2+~u^dZOEV6wlfQKXs`fWC8q=4v@EL{S(s7Lm(Zh&NkyjfMKVwqP-_;!HRp4WLxFbv$sNc{?pjh|8uu3`-Tl1|GqAS*3tIT0'
    'eMARP@J5t(2GbIEXeUVfVvQ?PT2{5Za+46$r1&KX;;QASx%1KMr$J-3LIB}miKz6|xX}IcsH46sY?Yd-adMk4-JPksjMri{$ig$Q'
    'tx39=W-PP*hfU?^29~p^HGNs<5Ww)GG4m9FR;vYUYJq)33utU7$+r|Fl1s+~xRK<Wb5W^;P>fI+B1MM~ocB91h1KuRVK_ao`T5(0'
    '>$H~mX@bsY>tD)OnNgeU2w|zDF79du<<E>*s-FRIeRX33L4aG{srgBJX<0UyGFkr>12hntHQN$2SAJ^3L@CPKjiqwqzZ)nG00_RN'
    '9PhZ7Nw=_1`Z!H3CcMvBVfti0WB#ecTZp`3tVp&dNaGnPs$<qq;sk$uDt}LfRT+2OwsY`|N@|>XY~LF#kzQH4mCe=`ZxH;?S-y<w'
    'V&F=BZEUiT4MLqt123`ufA26eK6sJ>(sGzZPzB$AT?hDRqTQN*5fGW|h`2GR_X`Y=U50k_lpW6xO6XD+AKHO{7=frg3X!L@5|!|?'
    '3napvPVPgeQXxUw${Tr_{x%{(5FNjdDNfT%`A%chX#7zL5CAJ&?})oSy6y3JJ;j7s?J^<9T?Z<uwKXve34%bGS;CL1Ehz`(amo-{'
    'CVXcHDI3aJ?YKs-G9$)UDEMhsR%(`Uy~Et`IqNw%fREV@VRjq}zy^<hq1}+Hl^2h=)@jt9&5UENCCLp3Y5l+eJFH->Pe^!X!H`Tl'
    '&k+V|lYwPvPB2#-I8B}u_f|BGg<Wys$nStnsOoNOD8qtQeK-cuzT|<w+xoFR#-@y(`PA&;+-@1rfs^iX*!!B=hZamWQAA{XiL9+2'
    'bA$I|Y8z)xPllU^YXoj*)nlKiF0JeK9*fJ7a${az=gxd5DRCCQ$S;JI&rc$4e?V&Yu?N>RrR>2hHg7C}lwM%qK}k}r7c%y^S4>Hg'
    'Wtu!qFS-$qq>D}1pKUe>Nu^{3R6gYF$YNTUNjAcXdK(7Zg{AeXY!JyZ3MCwZG}H>^myG<M`v2iXQ{v7q*)q}rzaMXii>ilCBe|W8'
    'M%M}mdj#g;Ur(9P>4F`lkcF<K3}>Qcy3~T80cf`JBbhn#9@n*kYb2b1($vM1k38R5p;QDa*?0o!i;)}t5BV5v_#{5U>kb<_`NDX#'
    'nChOx3fdMLu#+-p%9@o{<2Xlf@##jS?E&ant+mMh!qnUSl~akA*9%Iu*hiHmUD^iyFlJTX`9QYfEzzZ{^^ITp08yk8s$Wy>=Dgi{'
    'ts$aMgy@BoN!3WzCM*>B`gZksqtFcnM$M^G{BRDP5Uj009mho{lb1azb>D!4WxRmbZn$JbPcF$mH>_FpcFa|N$@VtYZ3C6knjP_)'
    '-c(-=j-<(t^8tLt^WlM@+JAT!pz)n+NrU9uxC6&)YI&Gpd7xbS*)wR{{5CR!d<bJ}urEA(Xs`7i{wpltor+%o7bIT)lfb-l9x6EP'
    'a5w^X!t{qO3Zf~E*R-yd&}SZd3P^Jvd!uCpTrM@>kuDiB^c6>@p>JveZ)$GY9B94C1s1tbJaM>2o*cnCk4*yoV05jL-(I}YFr7Z{'
    '!B6nm3R<(|+Dh@LUmsX!+8B&~lUQ6qJYt)7<SFt^r(L0Wd*42+!&(c6Wa7mRf?eL6Cw3_+^U0DMQMO{pOB@Pt^dZW?IZWNc2|^z;'
    'j6)|%gZLDEDXR&>a78=43CF`MPU5z}fUf`oA|IW7<!bdaw&&g7!8I_xjA5NVZ~%52KUz!jpA%y=fIM_aJo9<|a!Jv;%N^MpbsU8C'
    'sP1e}N!Mur5|Kaw;t@k98kJ$H%xl&jyLKTw4Do>$I;}IC@0R(qhn5KR#!I(1jPiorYe;GTvYJho`b9W_rH+j6)&^pP0nMaP*1}hS'
    ';f=+OhRqenX~{D+Tus_~PyngV2a9ZUgJ}8MTiAfS+&qLZSac8ucF#GP`G+GLg;B~oTQG;c+!T1aEsh4rOFUKxKeaH7|GY+F4gA%T'
    'w9$)v54SNgwva<S$5O*HtomY8kgKvjRDBEByF%U3M3zHU2UGW#h2f+#yhPJQnm_AKb+Y!7pJ;_Kxaf|;0zwX3kFw59#EkNW8v9_9'
    'h=@rmoWIF|LP%~<BJzR{w%SonAenp$b97UdPi-8d8SISge{TB?(|Swh;4*2lP(gH{?UeHn9bG?3@t5+X-}589ze4_N{BNfjgc$`s'
    '<$o2xh4H2-TXn~=;@w^JHJS3fipnB{ig$fNyjAu})(uz*s(8s1=P2aqsi*i2c_+JVa0LcGbA$48yoc<l5a43M&l5bxU&?FeGt2t6'
    'VfJ^Ec6?`p4(e!=sMqnI2T!ezv|efd_f$FD;t%*!R@f@?8}(}Qo?w{xeUBZTR3aXYx)~E7<`ke}rZAq|G}m<P6@qKPs^7MdVnT@s'
    'dFjb7qYumtrjb!Xv6D3fQRlmqzf1Mi9XMvf3nzPuJ=s*2@U)k|z|yLXbo0IFyffL55-9;|LGr>BY6fyKYN`ksEA;I6Uc6#$f;$bH'
    'eYa%(iAI?S7aT2t6w?xLg6TmZ$Nzfo5N-XV!E{i_F*Jd$vb=eS#DZ1}UsgY#{ecU8o|%$K!&SH*5lcQ$8D4R=k(%}bh0TVRh#HGp'
    'I_yyuhw$c4!?UqE>O?G7CB<lKq-q3sdT{j4$)?CQpJEfWy}q4R-mp@ovqZ?ctgbLOkEaf_%nx~YY#X^aw8P%bIDtF4@I(!@4?*p$'
    'R|pq71J&_`3TCs^8ffP`U>T?BleRKGs#x3pP{L;^x->?<HSBDz!j!U<?k<`JMm+N~&}Ec&Hk~j?LN)j{`K}=0GN1KDq^uQN+HqfC'
    '^>qfU*00faY5KsoTEA-t!gkv`wFhkw<c8-hfo>f3u}LD_8m^YC`H*bo^d@Q0%OHUSZa2hFO|1^`5n>VSD!Ve^QrG7(Ig>gPrVSHj'
    'RHrCX3JX{xmq@4uro0dWFp+%eU^OTSVq=Y^FigQSzrQqxd;2V0JsFI`?G^XAY^65HW?uc?rF2)X$zO5(tGVh1=Kd(YZqpIjk-GCi'
    'tMQtVG3UTa4SRo5S!%l_e~!E*nvzlAs++PMkuXW)Jqu|)?!CR?4?;&AVd+W#5Z*S?SGe;vU1?M2@20NXyRo5>GEIj{XI64OxZx5Z'
    '4A{sTn-iRT{jB3gyz+Z+Y+L(n(}$OE%{)IU5l5Lc-Cv660&S^9B_0QO*HrhEa?|IQ=)|)L>nXNv8EMy(>V*vfB10YoZg#P|nc(EF'
    '0>Zu>`wkfbMi&Wc^$r7G_}d6XJ(^$^Ik-UJ4|w?OrP7g7I|n1;{H2LO4J$C=Caf@?;2QG+-jhlW7H+frgKy8yTv?n$;odx3ByT>V'
    '1HVN$yr;no%gmci9I@ODLI1PzG`tBWaBXIZa6BBm=jFJvf5~;*Pitznn>o=Nu^Ap@FysQiQSH*}P%ctbjYNh0z%-DiWGC)~N?0%$'
    '^ooeOi2i0!OPINQfLy!yEq^boLleGi-0K}h!}ZwnkZVNnag(Y^X!5@jMyFMKdI|2|s<@iLuO&QIS&sv#qm2RuSP->6Jy;H|{$FhB'
    '!HDRM`1I^#I~_8+iTQ<?#f@x&%M$(h#A&K@b8eX+Z#90vg3ZaAZJn*UR1<=j?O=iHS~y9C*2{ZhvjtUMES*?y91eJj+o`SGD;Qp%'
    '^u<(q{*KObotfo_wslrTZ|yA(p&!*fx5_K|B9*N)A})?Fm}+)LJFmVYFcQT_4Z>S=@Wugwf^k@>gOPctrh;U5_#IuG0rs(7T4}L&'
    '=|em)6(b=f>Z>P}MAazoIOiC_Hg;iMkw?)iQk!et=wCd&=eTCGccKN#cS;mE-%fM?yR!!4LL1YJeXLNo=T17*{tsrEoOe!~6a&T0'
    'moy<EbS&vo#;6_Vlzm-q*CGhOASSeX5Xx=ahDahG3e`Vn5094FFA?Xc{bF$Wz-u8=kMvH1Ag)U+pTbRw!FEwwQ|saf1KN2Q9yz`X'
    '@Lu^&I2^SU6}zQ|N$nim4ckD?hFjKZq$Fwa-v8ZqkyyKUx)sg)z9G+U%hI8))mJpiBcMAO{y7E-jE~2dIKC*dhGU~Lse^E|#d0Vx'
    'W7HMOT8NaJTa^F@Rs$1l<?^hPN#y$)i1l7>IfO*q_c-kH-|z3_Gd|l_Ca=HHBzKGROp+A=<V#(r3OcgR(5rlq;L0%0?M;dx-Q)T9'
    '@h*^2e6U&per|ReQ9ZF`zKRmuTw2N;6l6KNeMNMw{4`{)^g+4_^rUzrw&S{BupRVSB5Tf-Sm^MgjI~VtQFT{@-(zDT<*lqL?)Db&'
    't45ddwnr=6k*{}9&Wn#RpFq_Cd{Dq>X1=fr(dBpG0WABE*kQ_|PRe<){qWPfRR#+Q<lZtBeU~<8Ws4{+?k=!xM*_oUz!S}Ao%HsI'
    'y>h%VL=R10`)DD@lCuX$HE3}##0y`rK&FOEVeC$`X@i?D^gf8hdLjX6g}c%6R0)2V!E39GL^thpIH9dGh~;Ti#=R-V2;z1}I#WmH'
    'P8Z`Op3z7A`KYit2|pDrFbe39>-1w@Axccl@LgO%d2RtO)#hEg?<{1tGy)M@b$Bz!Gk(2Qrq8z|VID5F_N;RadJl}JUx%S(L+;V@'
    'tjS5>3Wc(R95W<=-6^TRQ$76AHA*$zM1ULl#`8|{W;$-}YqyJIFP<LKSD0McfuktI`f^|_h&!8vllr7vA55;N2#$=pKyJbJ$c0$d'
    '*-I*`bk8kXNlI2pYrj*(s?MdMh5u}D<miOD>Vakz3BEBb#+K}PSP&A2#P=8I#`qBiv6)umjE~yN1_k+HE5BEAG+i+wE;^sDqcbEO'
    'ZcX}n#XN!vse7QpnjbN26#JXk&1h8rI736%@Rl&0yJZ%~m7nL+GU$961TwRHgHQT#y-e`JA`SXPD)idnp7gqw>>A&`96UI|GWps6'
    'Bc|ki$dPM?D4T_*z|8onPH5?6G^vXN@SZXNFR~A|X@dU(ksdLrT#DGWi<tx=!}MANYcYM-)k)B+w+vp-iY9<%$78cl0(I1Ceaq&F'
    '^wT)Ge_dAh!D-U+`R@0XO0s0;n70wgX6v2V?IB6sOQ%Ok=xIQE@&=Szc2nkB3G@4rqro&2<6n>rCX0C$B_N8afk=V1OW09bH5$z8'
    'E*iqcN|AKUgE^b9WnL^bxqLwo`JQ3;u`kqMYM@rSSl)<);8dXvM2{IP0O3~%>TY|OmD}RUs5<G9MwEGSPNdytKJ7~skq+2RR!5ka'
    '!9?e1iTA^1fYcL=<&gV5_^*?bt0_S!iYXT(XjS-#c@Uh_O=Z{zK`1zo?MA0x7`6y*KL>0mR7jutjvR9b1aYwbohtYJg;egFSi{|^'
    '{)?X)!J(C3R{-KgD9b%?=-A9dBKUv%2m~@ODTRWOAp<D2w58vm(K$_4HeBH$@Z|}GpbOH4<-tSs{)nW~IpwA<oj?;B7acrM1jwBX'
    'Hq9b_$Q$6lLYX$()jid&o0B6nb`}54h^Qnjnl!N$bDj+}c4EF=yTEb9&SOxxOgt+PSd$fc{Wv>O6!1?#YGb}P`vP^9dA7l}`wz#V'
    '&vBrrsvnsAwMKQ4YxSEbo0pN8r}G5!n!LT|IwLuX&t(9_2S@oddR-e;>6o9@g94XR9J4VtaS7Z@PuX0%zinjNU=5(mR3xb*7||pa'
    '<b6we#9A_q>a<?A-uEh5FmW4Qe4h8=FgQ;+-g9F_;qvs{ioP;<RW<NqLk?&YwkhTA(q28Y&HC`Ocqem*v{u~M_0uFf^(wx6IqW@y'
    '_dCPi2RRkVrCM!kGMSk(!8`e4@pt%wh=)uVr?WnN=s&gn|9`jy{C<`qnB8f-7@ZPx`{U-#k{H3L1~(=;ZurS3QOMx>f-LF@0N6yO'
    '!tNzs7*a*SW6iR<MKZW#tts-xECQS;55IC-ZL$*RrS+)f5w%)Ul_Ob}$0b`=D2%s~kWjn=_uRV%x9_eZxShWUf6di})(QMaj99ZK'
    'Zpk*8#iXH=Q};yCNs9SZ`+t^tg@nY{cZC5xY0DV@B_@nyIF*G?G}gZ0f#q~xZ)kkt$t=plSyRI_Rs-reElDBSe6cO*pI{~zAD~pb'
    '<7PXi+q~z%&FYdKA!K7)aE>ji`+8)!GBGhMAfo==hYDJ3P+a8<C|G9}J1vCZ^xa{rJjL7Y%{g@wd|l&;E4Zf;(#;S<kbul+THu$r'
    '&18yJv61X07vaI&04Vx;3JmUh#Zw|LL<#^*25hEUK)T3UeJc2_tuA_{{F-04;PI3Fu#zSuj6=li5O=zap{KYKuDM}9<kfTb8K4Sn'
    'HAcbSLR~LNw2M4nB-<8r4YG&+M|lF3{L+fIh37J?BLR{$d{UW>F#!qr;+r8KbdPGy7*ecVUL*i8p5=0XBsGtll0~c0Neo~pILyAR'
    '0?X6O-78D-4)E7rUzQVZb|0K~QFTlHk{gVg+ExS%wpokf_r)#>I^&SQa&nl?(B{)OI|`HOJa#%Xn43isXp&Di=nqmj2+XSk*xL1|'
    '(cgnhR~m=5Yp*vBX{LG@E4+LAN7(McWuAz7w@~fv&)&Icvi$u}cavDIRVyF}j#3MYtGS;T_|~Z()zOEBqVi%@32Kopd@0iCc?Zbn'
    'Ja@K+K)0Q2C7b8fTVtx2pR$f=z=pSQP9fhz<J~QMZV@8p-tBuFT%CR=SS@O@K2?inRvi>xf)3e%2a3yc&CoJI%vOOu!e$`Jy*`S5'
    'qtG9t@~rtV53RgyUOjndnWtF~*ON53&mw`?H&jHe#a|6!l{Hqz-<P-S2ZA0GQcH|i7Cbbeenyzn<pY;OM}S_7id02HuN?Eftu|)g'
    'G{c!3x6(1L>p`xJtj5y>OpBkbY4|T&d$$97jvIW=Pb7FafpbLnRcqa3iqL1t7LZh`SjzVgne5~g8xDEFE;U%<u>a1+70X=@w^jYf'
    'rWEj(z~rM7APW6T@I^fNA|$v6@&!8eu~x!&teoe&G^9&ayI20saJB@K<_WK}DecHOC^lA_M;_+-8b=HiNARrni)&5a2=x~f<rj;Q'
    '{<Q;eq=g|RmG!jT$%Mw8RD#>fQnJ(ixt5!$T$}XFhV~g8^eAlCU#(dmS08BTj>j8A^s_9=1bph~UX=FGiZYk0K#M}8+cbCs3BYY)'
    'x54kcuVdKV)B3ZX=G5l++>Aqd>Yj1Ajzo|%=zGfJ>rT+QnlRhhR%4{3pesfde^SLi&-0t~7b<}c9dMA}S;G)qyq7u`)+ps^o**bu'
    'wb$BRKH+?9$>`9@L}V-!oU$=C>#scBf)9N|@;*{xKg9j2iHh%HkOTJmRYJoAQj~+L587S%^kK}MpAFS$>1ZH_WwtznaCvCog)9TO'
    'UE0QAUc%p1mG}J*21I$2;p2R4ka0iP_b}owvFGiSSJ8C<a6e&w8MaA>iyrtLNlSJ32>vx1X($NnUSr_#(N?2N81dSIt`$4asXzwb'
    '`pqs<W;w-Vt9B6#q(<9N)Y`i>J!Xub1^{lpUgo+p)hd`=IN!SawKLF#)f)_I1L=2DfWWp(vivDe^MN6cW2c1UO`S_7om7yYKyTt%'
    '5-$xAieOm?GO>I-omxUU3$eCnW7m;yI3e~~$d?DN-6!Y(K-*l%8M#GXq_WT2o3rzz$d9FlBSTJSB*@_!emr_9>-)X?N2~)02T;32'
    'jm~5P!3D+iPUK=BN5bgGYYBz(mRiRY7=$#@jj#ub7aJapiJTHDBlzGMbEPPWsQ1MzxMNU8mgifHTF-;Gpio9OQvrV?3MVR42z{1s'
    '9|Oh1S4icN%zt(iQ?s|y^Oq4OKj7)7keY~jPCKa{*^V3yxkWJXOQxsoGGI_;KMM%A_7`q!B^)(tten1fdozF>#p|nRO2LAIW}KuW'
    '*V4p1zKnA)X4akN-|8&Ll}{ssjQ@k*Tsb~DLf{KsMCQE6Hj_D~;QAoa0)*rh>PaeUOk8oq>^nZh^5f8~aAU_eheFSQmxO!+SE_^_'
    '7GAl*No$Oke)w(uE2{QcluWr&Xd5kE8{SCQ_tW9>E7tzSn2^g-zY)Wq*p#aE1`Su}{PO)aBwa`Hb<A|l=Nb;4C3!^oJ)J5+U80cy'
    '_c`>$i2#()NTj6szwIA6K5w;~XHF)0Xyk<W)oGP00a)<@DB}^wO)v<X6uZs9$M-LNUI-Vlsh9gQRD;V_2xL87r>#S|?V(brbcX>)'
    'vHudS>JFuWjSEsjJ&LpAc5g_GT|$NHGs=3_N|1Q=FWZAi4VQNTcSE$su|uL%*1%q(`#Fpq;dct3JDLgNgUZBCC0*SZa?swxcO3sq'
    'mNK9>A#Z^aB#_Em0<XnYt1nmNW{jMykai8&q0g~~2F*j$1tj__(+qCvBPcrti+Z26GN$&w%BQuP?EnFJAr4>1yHGn%S>FF)FO)EV'
    '2@Y@~>(owPjnjGr%$pNd(X~}6BrGj8M#N>+QZ9hXW=SCmQYgCuc*saL)wJmG^T4<FlvUs8k(p9LJTc@q0M|Mb<O>Ab$-6CV;m<m`'
    '!!kKZa5zt}dRaW?gC%L6!c{(7PK}dUKg>6+u$7V_1RTwkpwm?iDI77I$~4WZ>WcZ*H+~H(4&RS)lrdeTLWIAlTqb=4&wGh<{B?Q#'
    'NhFpmCP}!B+&l4><Hcdj=apTtUMnxS$x0!C{OMs(`(?Q~s~0_>EHH7d8D0ymcy4Gz<tDl?xkKhiE#44D(d|qHaM_T2$X4AuT><F>'
    'Gt1TDpuylw5gT!IdfT}NNP2yjiqNK%G)*^`w4NzH!*|1omhZ<LfNTc+hXX`^8#Y4Uqf{>&00@%HS%cfP5=c@5jZ{nc#(|qt_hHH*'
    '%aVd|+%*)Q?5IY1q#Eq+Hd4}Mluxou&Da`gtfG@BkH%aQfH`Yj%vC%(h<;8=aIH|3a(tj5(CAs@1?!DD8bwxQfLp;Jn2^<%C5g}I'
    'KY7t|4!k^=oX>g}^SdH-MPzopC^lht;U42-lnRNXY8FCcTF8h-x`!=x6Ka3PpD4H-bZD>crJ3mhCVDHmMyi4Mt<-Eu4+r=Np+NV$'
    '{=7M}1WebippYoaD4a)^SyyGVw#cbS5ggZqd#{Yro!GD{OZ2h%>TiZ+8ElGV9x#_7>b01;&QgLXDSo`eXrc%2kU;$_u>YK?GPXX!'
    ')-pD_+bYYONjM|ACy1L^fe^(YuXz3gRjf`jNdFxi8ZW3pL##~NzW_N7J-qDIhXMY)ddMWgqlKtD=cum0mg!M2Bc~c!6jau9;yMa)'
    '+1|Tju2h-8p~Hf{4^CRV%O>lvcAUDC`PxeEJR5=>0+*k4K&2`$BeS5#A#+y{i@9=WSOff%7kS*!vETU4ULyDZpyv})J<}?WG!aPL'
    ')lCp3CLTx=E^g3Urk=dW9|!_3?{N3};Bg0)kEOtuQnfDQaZktUUB~gxHtV@?ZhO?MaM@XuRiW04^^@F&riQIRWtp#tt~k|!hS8TR'
    '<egv37dNKOpst&3C|#S^F)#4`{(9{?`TvJUksjy=8`%ZvFP8QSd|Y{Hut+O=GbYFlks!5_$;T;PcVch-(vQkwcR_+kW~Q02fAxDn'
    'rel~?Y+uExDs>Ya>@dNHfN{ZGqbAHv_cVGp!d{c$(UIGa>8+oVF%W3`X+G3}!wH_Ij;C>uwRmz28ffrPztwr_Mww13sJWOxc?NM4'
    'rg%O}0vvQ!72)zBT66P|CMKVOy|Lq9Z;}!T``;zo3EH!?fnu)py%!~>b^<F(rOXHzsT^)Q<|=UR^=Fen4rZg((?xokOK%1MIt0{;'
    'bS0Ttn${~p++GzM=?Dv2o<F6aMYzM%>++msM`kwCBYq>%0d8Aw2HffQDJGvoW(JPPMXWDRj=9;)?A&%3hr`hSyS<cLqq+9!m&e3Z'
    'D;|Ov2X&!ikyqU*pCxAhfyTfZR#Eb%r$$x%(^3`|^EpnBhyH9k-|jz(Mi1jLoDlKexU0wxSxVOP9sPdQqoAx*YMpR}2*8qlqk)N~'
    '7Dw#=z{PlOiAfd`w*4~1n4e3>omArwbBiR@mxX2CrWSBp<~={wJV{wro5uj3V4lwcMFJ;Y?irYu6-=|-Uic`{SW6gtNtAXiSMFQ&'
    '=w@`fqP~{{osn6*zu4VJ^k!iE*}CXNw~S61G5t*+Wy&?a@B(kOELwz=;7DhrvL>=&@h+MDfZ^e!{+jei3QYrDsv|W{Fx?U-gZ8Bg'
    '2xvn|U+ZVXQR(@%igY{>&z_x6ymgGz$Xs;-=}K%2JTcezFsqdTh5~1hiY4*JzZ2&u>#A_SE`!fkx2^21&eMz!={nT%3`b~_fO#Ey'
    '8#k(`9Q2DGCxVFO<rr*NgJxa)?Amny5#nf&Knjb%=8D}(K81gn&<r{r9%c1W7E#sDJP8~uWEFd*VK%Vb0$(aN2b&Ll*b}|{HH`>A'
    'gbss&nq~|g%d%ZGeTI>gFxd}vi?-mVLsnD~<m4Mk8&N=OB8a73gw|AfAQ=5}xtXTV7HMX(3lv036e<kwg<|s&-E;d4S7pO1LuR22'
    'NNH7mr7UMr%zrB45`?YfQG&i1b`!*qcbw{eA({YJr!j)s4qYl$;9wZktW5E-#?xf4Z`w3RO=%JAo?X|rdnjuUJ=%`-hOLPCCEjj`'
    'L9UDOxrs*@&tSdh#EX*J<3E!Oh<5H07j7&jBXCvd$3^BPo^SXn*KM`!Jczwrc)sumPb)(1*6+OtK&KzqJzYHc?>QN7Lc=OKk;>ph'
    'n%a}JH60wK*8q^BDS%T<LC2E8Jq`#fD{+koVWq2@RpaEFOox9ivH@kE2FM#=0Ph-8R786yNqsj>cOG)dWj`$tZ`cWw0ZcPB(FAN@'
    '8s2t*T*~pA1vkuXwp{v$jK&dKJaum%h)eGoTDkhWYMLy4Cl{c8XtpO(Xfveu8?jS24LI0t4K+uGg5ynrnwM`&D$EQ#r+7MCY*-n@'
    'qs4HV)lUlDjhLH|OjtPNxma<c=qdH<>^~{qM~kear$w2JH}t-1D9Fmx_n269i4T0VyQ(@d_&Ko-SJ!3J&=ENx1zI8;@&>Q3&>sJ8'
    'b+rNu4wlgGAJFH!NPkDj3Vmf{7-d>DhVHtTo}owsk0|r{)g}}Q!DHlIA)LOqB#QYLkuQmWqQRbjzdgo$;a!Tqr=MsVhbgTC@nogq'
    'uc98HVBP?Tw~l)dM2C$~1DYq*z{}ti07u&r{KEPnQkcNmcCtf!*v2r2wDL2VZ(~sCdTK2KQ8fVbAm4J`+akS<OY!EWd2lb3fQHSJ'
    'Tv6&xnj-kC=bB&sP$qFg=V#F0TN9>6XBdGl^0E%Qir5=n!zY=$OzS+3%1(;%sBdn*Ny`2vfz^gDxQT#)@jJI04jYx?Lzp^9IQ-oq'
    'J4GP3h&v?pLM%#38}~wA&%L*0H0yRLJ>d}WOP+EjTIDbxT702+1h^){3B{C%4H(JXyK>%8l4F$lV7K>iXM2{&W{R0S!0kQ+G${s1'
    'jla&0_Y<zN6*1Qc=sDJ(sm1)ARYho;-lIk`9N&0QN`e5~xWd*h!6m}b9BKV@aQo9c9mA0%h~Ogot+kicmQ!L~R6jsV=5bs5M|mSS'
    '{igplZ$=7cf^nx483Pl3aD72A?iavWZlG6aj8dDg)IZ?=r7Q{mxI)OdK-6LICgExhc}uP4t-Oo=NQ2am3?NU14d}0IXZeC!;xLTO'
    ')MCAfsQAyIELD9E%ym&X6ZRMr;NmeT%!yobTqL$A&XSIn>%C+$VBhbS)yvo)O!D6QF?gn}`JxuR-vp4tg64M<Q*d#x&b(DR6Q>yN'
    'i4*}|!?0>>kn1=||0_jK#Ym}1+2)*Ry~+3vVdmaO!v=85(caFiRLRHvL4Ng5&Ct-yV@V0^S8-SNQ%Ax(UvD(8#dzj~5-b(Q5g8x;'
    '=1uaBu@)WEGGc<8#CT=}5n(a`)}!SEMf^7JUG8OdvQJNwJKMvX-pnwsHy9CMm*Z)qeED3X()1O`TQhrk_uF%ZHbxlxEUzd2-$1?r'
    'E0~Rkpd&0W0ck=t7=RJCd~9dvk<QJe#Fj~!Mq66_$Z42_c5b#<V6c+pg22yVL;9ZAsB$a*|3^2jypi7h5|7(9Y^SC={rIa}n5L6?'
    'Wdm?O&^Z??-siMO8|JE`M4u-Kc#+eYN|yRID5e?vXQn_CNx7v_>b}%6*~blAXv!tj^~4}tM-OnYJ14c4>fO$Vi|djgpZJ`)pHNU*'
    'R(nH?{i?g}Kt)U=LgG_87iUDDbk*JH230xmmr~<)HT=pq$G<;Dj}zd7rAB`uk7)ADGlxh%<|#a9JICte%&mOa(QT=ui=~F~`PlXv'
    'sI?EqPeeEp(wLBK)I^ih)R$<<U<8ZUT9(#g^mM(_4#0l1we&iN@JTpez>>Oy^VqRASjgiBKyX-F+V0^fa8)TwHd=KOn0v~i4O~(Q'
    'V#se-K75MKL7n(7>f@{(BSleN3D`zWvT^Kdp3my(VD2+IL3u_`7Mz5#Xtg0^JdI-;yJ1?q7VM=K@Z}Rda&>2pp_};)>7LW#?a-zr'
    'iE@!nh+6q}KL$I@1RP!dc0ulFf2X!Ps(BBSX?woB_niP^CES5Xr|iHOoHRJ{0`R}V&7_zrat+k(6uC`9sxJiz3h4K`PG82|V(i&n'
    '1N~q};gMsjv*2<f!>>zx|K7uw7VWt1MI?6&<qNky2(}KoipW0My-2@Hq8Lw7c`6KS{799x(e6d)&>Ov)E$C#P*q^S?i)ulm?P!PN'
    '=L%pmb=Wxo(zH?9bqDZ((T_g?Y#D&#8n^F>iMM~x+lG4^?Q`RxX*Wi@YqksKZ%E|la)O#pUVkX#D?gEB+<hwH$cz(29c}Vy-V!)H'
    'y8bq;+?<K0A~00!{avMfw2mMZkX7NRGosE{(6nY#AG3LLn1i;K;oDXoOxdVcE--okd*pr9fb^&!hX%X7eB8-xr$95f3_vNjgZr#p'
    '*{nU@&0e`V2l>Gt>9xY_k9=>S1eg{XoG@FADjMS8CzrCsWv<qrQ?>Z@Ct+k}F=Oych^zUTcJJBb;mF*iE;*Wtx@P@c9s#;bB9myy'
    '4QMDB`xw2REm%oG5>+|JX`%etcIDr9+nA2P4H-JvmDz>t=GmQ)=b-NIJ&wEsG&_gktn-w_848)*au6mR$I`GVclNEQ&R(N5eT4Xm'
    '{ZEgGqLQ~ew}%mHFD(2D0(Gduo~mUkty<X?c4muDP3-x?6Mk(TIJ;CvtkGzE++oP~pXr}GZ3WbX2uk#uy!)LL2f3(9oZ*G}jJLyD'
    'b!!pR2{%JvG6X9uVUu*9W4k>k_qjEam3GEHA@Y6uM7t3|(1bi6kC1bWR$P?44d)>Y_PUt=*)$qvnHP|y5G7sf{DBuV@=y}+;-_w4'
    'aq1raG)~II+|Z`L$j-!GnPzi7Qr@Y}h^cm<<v#^<{TpE9$UfmcVo#<HB5a=;#HjCGD7<Ke*pe7l4L2Wqx45Dneb9;A>O}g`DO<Nm'
    'eLN8|K*+ROL>uu>Tm0-V?Nh|Ew9g_Y9y}uh6L69NLcph*sfcBFj-otW=yX)zM_GQoTnyYIFLw~UEkxG5NWma)6D3DgbbS~s&qzmF'
    'dQqeguj1t@0=a<Kwn|u+K3x{Hre;1)WFPa&+Lmdk+FhwqurpBk;#)r9>=D4d86T2GfZ|Sa{4`&VDR$#~f%caKvv6NuKYwlBIwAw)'
    '8=5m0<{+C~$~FL!VQgl7e=;I73p-)1`b>a!aY9m7Q7}GIon)cn6`$tgS1^tn@XnghS}xAcX;4?3E~^dliHtS)?}!mE!lm<^F3-``'
    '3S&S*F7+fGM@39V^!NrhLgeGx*QWc!xy9S&N2>mK8}DKJClfHT&7O#<Mjxjam)_Z%i%-ZVN63vzE<}_IP#&4?X^;an<RHgpi_`*_'
    ';p9#Dz<)=zMP^|U1T>N(!SgMoK-)JCg)UJ6g8q|(=b`8akcjD07)KkTeuu+9{d^Cd=*|3+OY-NM5jfYOxSxa?IjJ7f=q$A+GEz^V'
    'oB>DrzM|XswbPoij!4ot$2LB7;|2`B$k8paY*z}IPppg>yRje$=IGtCRi9K(b|3P8IC<&G{|tXk?(WIGGGVvmp`|{0QJ5b53DDWI'
    '1~jM#-p3T^$?XQhyT(mZcG-1NShzkPtGSiU#8I%4qJ>bSK{p`N%-7d7nIj@NHW+LoTxaGFQ=TQRfmWgb6e2djxCwb7N_*JMS0p|t'
    '9M*EMcUWA3N<L)CvEf!#C#u2LGp9NyE=Jv>nr_>fj~~E$sS6wNcGg%XHfoQo5zcK`b!8tr^PB+*793h)$i$cPxQ?i!nkhb-i3`tU'
    'mzDZ}FOC@h2zlk_MDTJnAD1s4;A_}bYGO>^z%XX(Njlqoig3cP1uo=@aYp|_8TEXEgs!QW%XLp0gdwa#gKk}X=-v?EBEkQTjCVZM'
    'e}@Ep(bmL$NxKnGKl|pI5E&Z*X_j)bfkT&6oMk{RPz}R)($z1$vqy#IGr*a+G}<08Rh+Djxp{WKN|X5ffk(gbQQ{x45!5OD+%EO|'
    'YxPEaxv6^OsVb7~*0v0{y|u6x;fb6p%9VL*-`dLqHApv04CKiZka#wfKp@*Cb&b@5Fd7U0lLU~SjyyWBX%gEBEk#og_JYrdu{X6k'
    '#s!KNNgR@n6%lS9K@ea>Oq8H|4do&R^apnl?tGGS=ybn%#Wex6%ph=#G6@l3b(vu*a7ZDEppBro;Mp8JsuLVO=~|uTFQsS>Q8jYP'
    'UzE03@hw>7<z4DIi#D8eEoFSx^JD2>rHD6{B!B#=sczzLE8fVL0iC~S>vT%zI7yY1bqbNtL&1f`W7rQ@0*`c%?ChM-SO0l8C#jn>'
    'b0n0hp6jaXf8uz2Y*brO_2zTD%-_??a&k-$woaXTIjzEQ%a#ty$N8k7_<1yCMboQb@tkZ^srpIJ5L$V#Cce2Y0m!@y2LEDGgbu&G'
    '@sjC36lQ$T41}vW&zmTT*};7q9%7gGmy6AOx+rF@14^D5M49_ktE>2!a8-TvZqyqGM4-u!h1L%<8*#b?7FLx(7&i9+(>Bj1J+H_u'
    'U<EVU*`G6Dn(QYg)-eq$j=c%LJPp7FkL~89zldZBLDz!$H?=KF_=p)ag6eAzd7mUNK!!^8=Ezo&(G!UTu7?LQ&}$Ver4eqG1Rp6B'
    'UkEJ@Y0Z;*-<E1nRle$i{boCdy>Bndd%&|(8Y(-qB7F*>LG@cPVv~mV`g7#V+im3ST;a+;u1OwI{258N0+hKUg>*!M`sfQSTLkmW'
    'XPIUAW$*hK!ss(F)+j5A6?mT2qA_mmWVv~xxB-}ro1|W({YHtgqPZu=61=a-k2MtDx*>a>NdN<sQfr&0IJzw)m}<5q8SjFfd5-2}'
    'j*i5ra4#}g2SE)5^x*yEgQgsYI*r@Q37Yxx;w5>$!=SPq{wqp4i2}N2u{A?bg{0DsHYt-8YmOrLj3hgrS-;7>DL)8ksDi75cT87;'
    '^M7;Gw)V>OfL|eu<*R<QnEIWsT^NqtHE2(8e>&zTF46LdE2Q~OmX9bDA(|FF8F!x{K+tUg;}Q_O9&gQ`M3pofc_obUg1)N%b)w#i'
    '>~-3J2ZXTk13Tg0<a}r=e}xNG=)k^MCortZclZ5uk&&0g;S#J=huCjX4WkGN(^4j(NbHgce?~}64Rn}Q9vLpge5b10M#LA#y7=R<'
    'Gr<`dp?o4d+9VwYL;L0R%f0Uh@ibRjL?TjpU<YMF+Re30ukP8d>5i%7&+>slCe*>B(T94WXIw}Sm(GlELn1P`Ka#0fZysU8$ut$}'
    'iaCAQbABFLn2fGBtsbCgY4B9rTDRuWU+#$IObb4c_wCBVe*4h=&tFYZeq*RVqxLCNZRryrwMrcqlfRiWP+U*57&CdZBj5?PsDbkU'
    'qXa-mSTAN#eJ@AWSW_IJxda~#@vh2a6Z|PC!NU+>k;Rwon)Y<{oe2tT`P7c@3A8+gwm4TgSY3~Rw+a6ew(1=ibU#l)>2{B@%)52c'
    'mPbg|`_u+->tQoC<9-FMikY3y2|WN{$=N7SX1~&oPcn~OIZ*&08dd0drVGwa)2@$3z5|KORa0!UvDcZ=5n!n`_=(>dPMdiGT~8)5'
    'U)Zp4uWvTbUoY8W9m}R<+(}(CSrof2`|BjCsVk>Rr!nuvo;kp^dT9n5z%mAfmW-DW!l)cVzv|G;eGcdvN5YaRDXt6LDB<BG?xibu'
    'BI<cav6f{Rm2IZG205!~_7QVW+@mi8cn;n0CR+hy;mG3P;fW(908bUE{-5`H_0yl_vL79N<1BA{)BO|Ak{|Ib0CoP*#G1)*;RbJj'
    '#X*fOXDv9oTpw2|S!s#ERidFL1;BJq+f&bO&l|P@5u{9P0fymy3_@A?-V`ucZO*)*4?>_?W_W|s1m7TLdEu+170PRxHdIxUYijqW'
    'Fd;pFGT{<&eDf$2LPO99p<8V<{cz*|<Psh_6n6ekAI;GYuRDBmfE}4MUwip8$#tJJVh`=hCt2At+9Qf!qfVJO&m4dBa)%V$k%|nl'
    'hEx_j__PK&m2eIsKfBD5d5&NFkbW_oC{X~5*VJ{Pc-n(BYlISXK$=!RPmUp6c|&fUa+O_c0qzIq_c`J6cDd8oH<6xoJ=hWgZ9B=|'
    'db$kRDD?Xj%pjj`=7S*AlFT)dXJ03}A`it~!|XP}zAcR)&AM}Zr&md!k{sV26{UJM;N0fMg^CWV!q3f9fnwOV<Se|ty`Y*1ws~Ks'
    '77OmyN4OAYD|)_1xd_G31TL^dyxHFx&SN<p+|hXBC-d=+k{?GJHh@Pm{TfO0r1G!V3;um72*Qe9GPg@0Ji!y8#ae82<cHUiS%mq@'
    '2`(bR1mphk%|U0vLj^QaeZQ%Z)p^}luop#S@-Kj!>)t4$77?(|I1rZ82`V|2^k;nt(E70q*=B}ZV?^sp$SnxV*Yqm1_7VVRHym)T'
    'gMd{qyi37*J(WR_YbCNdL7Voe9+GHcw5EGwqckO?H-|HPvH;$ao2#egaae4V%L6MseC^R8q%XRW09-wp1x9#|-~U(rE(f+ReEp9H'
    '3<`u>Bz^g~6?P>+AYywv75$R_xSakmbc!ya?d7nr0l*HGJQvtBjuZd@=*6bavbuoo00Ef41K^?`=5v_}vBYQl0ssI200dcD'
)

SEWOK3_COLOURS = dict(SEWOK2_COLOURS, **SEWOK3_NEW_COLOURS)
SEWOK3_GLOW = SEWOK2_GLOW | SEWOK3_NEW_GLOW
SEWOK3_SHINE = SEWOK2_SHINE | SEWOK3_NEW_SHINE


def sewok3_decode():
    raw = lzma.decompress(base64.b85decode(''.join(SEWOK3_DATA)))
    frames = {}
    p = 0
    for name, i, width, height, x0, y0, w, h in SEWOK3_INDEX:
        rows = []
        for y in range(h):
            rows.append(''.join(SEWOK3_KEYS[b] for b in raw[p:p + w]))
            p += w
        frames[(name, i)] = (width, height, x0, y0, rows)
    return frames


SEWOK3_FRAMES = sewok3_decode()


def sewok3_canvas(name, i, n):
    width, height, x0, y0, rows = SEWOK3_FRAMES[(name, max(0, min(n - 1, int(i))))]
    c = Canvas(width, height)
    for y, row in enumerate(rows):
        cells = c.cells[y0 + y]
        for x, k in enumerate(row):
            if k != ' ':
                cells[x0 + x] = k
    return c


def sewok3():
    frames = sewok2()
    moves = ((GRAB, 'grab', 6), (STOW, 'stow', 3), (SWING, 'swing', 6), (ZAP, 'zap', 4), (LIT_ZAP, 'litzap', 4))
    for d, flip in ((RIGHT, False), (LEFT, True)):
        pick = (lambda f: f.mirrored()) if flip else (lambda f: f)
        for kind, name, n in moves:
            frames += [(d, kind, i, pick(sewok3_canvas(name, i, n))) for i in range(n)]
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
          (6, 'Crispy 2', crispy2, CRISPY2_ALL_COLOURS, 0.3 * 96 / 94),  # (drawn 94 rows tall in his 96: 0.3 of a person, as Crispy)
          (7, 'Extra 2', extra2, EXTRA2_COLOURS, 0.3 * 96 / 94),  # (drawn 94 rows tall in his 96: 0.3 of a person, as Extra)
          (8, 'Suzy 3', suzy3, SUZY3_COLOURS, 0.9 * 200 / 197),  # (drawn 197 rows tall in her 200: 5'3", 0.9 of a person)
          # (Standing 129 rows tall in his 132, about 0.6 of a person as the
          # Sith Ewok; his saber's haze and blade lit.)
          (9, 'Sith Ewok 2', sewok2, SEWOK2_COLOURS, 0.6 * 132 / 129, SEWOK2_GLOW, SEWOK2_SHINE),
          (10, 'Suzy 4', suzy4, SUZY4_COLOURS, 0.9 * 200 / 197),  # (as Suzy 3: 5'3")
          (11, 'Sith Ewok 3', sewok3, SEWOK3_COLOURS, 0.6 * 132 / 129, SEWOK3_GLOW, SEWOK3_SHINE)]  # (as Sith Ewok 2)


# (0200) Where a move leaves a mark on the floor, by costume: art pixels from
# the feet, facing right, and the mark's width (Crispy 2's puddle, where his
# stream lands).
CUSTOM_MARKS = {6: (CRISPY2_PEE_LANDING[0] - 104 // 2, CRISPY2_PEE_WIDTH)}


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
        mark_x, mark_width = CUSTOM_MARKS.get(costume, (0, 0))
        table.append(f'\t{{{costume}, {ident}, sizeof({ident}), {height} / {tallest}, {mark_x}, {mark_width}}},')
    lines += ['// (Its number, its file, and a person\'s height per row of its art: as',
              '// tall against the people of a place as it is drawn to stand; where a',
              '// move leaves a mark on the floor, art pixels from its feet facing right,',
              '// and its width: 0, none.)',
              'struct WorldCustomArt { int costume; const unsigned char *data; unsigned size; double personPerRow; int markX, markWidth; };',
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
