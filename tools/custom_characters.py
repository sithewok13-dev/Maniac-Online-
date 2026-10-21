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
"""
import argparse
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


# The custom characters (their number, name, the art, its colours, and how
# tall they stand against a person: Crispy is a little dog).
CUSTOM = [(1, 'Crispy', crispy, CRISPY_COLOURS, 0.3)]


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
