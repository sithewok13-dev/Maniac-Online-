#!/usr/bin/env python3
"""The Dig's light bridges, all switched on, exported through the real engine.

Needs a privately supplied copy of The Dig (default game-data/dig). Exports
it into a temporary cache with the real binary and checks that each spire,
the island map and the hub draw their bridges (the game's own room scripts,
preset by the exporter), that the bridges' walk boxes are open as the game
leaves them, and that every spire reaches every other one and the hub
through the door map. Not an iPhone test.
"""
import argparse
import gzip
import re
import struct
import subprocess
import sys
import tempfile
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPIRES = (31, 49, 56, 61, 75)
# Room: (walk boxes the bridge opens, walk boxes it closes).
BOXES = {31: ((9, 10, 12), ()), 49: ((7,), ()), 56: ((8, 9), ()), 61: ((12,), ()),
         75: ((15, 16), (17,)), 77: ((1, 2, 3, 4, 5), ())}


def box_flags(path):
    data = gzip.open(path).read()
    if data[:4] != b'SVW4':
        raise SystemExit(f'{path.name}: not an SVW4 scene')
    _, width, height, count = struct.unpack('<HHHB', data[4:11])
    offset = 12 + 768 + width * height
    return [data[offset + 18 * b + 16] for b in range(count)]


def dig_links():
    text = (ROOT/'engine/common/scummverse_world_maps.inc').read_text()
    body = text[text.index('kWorldMap_digLinks[] = {'):]
    body = body[:body.index('};')]
    graph = defaultdict(set)
    for room, _, target, _, _ in re.findall(r'\{(\d+), (\d+), (\d+), (\d+), (\d+)\}', body):
        graph[int(room)].add(int(target))
    return graph


def reachable(graph, start):
    seen, todo = {start}, deque([start])
    while todo:
        for nxt in graph[todo.popleft()]:
            if nxt not in seen:
                seen.add(nxt); todo.append(nxt)
    return seen


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('maniac', type=Path)
    p.add_argument('--dig', type=Path, default=ROOT/'game-data/dig')
    a = p.parse_args()
    graph = dig_links()
    for spire in SPIRES + (91,):
        missing = {s for s in SPIRES + (91,) if s not in reachable(graph, spire)}
        if missing:
            raise SystemExit(f'FAIL: from {spire} the door map cannot reach {sorted(missing)}')
    if not a.dig.exists():
        print(f'SKIP: no Dig data in {a.dig} (door map checked)')
        return 0
    with tempfile.TemporaryDirectory(prefix='dig-bridges-', dir=ROOT/'build') as tmp:
        out = Path(tmp)
        result = subprocess.run([sys.executable, str(ROOT/'tools/export_worlds.py'), str(a.maniac),
                                 f'dig={a.dig}', '--out', str(out)], capture_output=True, text=True)
        if result.returncode:
            raise SystemExit(f'FAIL: export\n{result.stdout[-3000:]}{result.stderr[-3000:]}')
        drawn = {int(room): int(pixels) for room, pixels in
                 re.findall(r'SCUMMVERSE_WORLD_PRESET dig (\d+) (\d+)', result.stdout)}
        for room in SPIRES + (77, 91):
            if drawn.get(room, 0) < 300:
                raise SystemExit(f'FAIL: room {room} drew {drawn.get(room, 0)} bridge pixels')
        for room, (opened, closed) in BOXES.items():
            flags = box_flags(out/f'dig-{room}.svw')
            for b in opened:
                if flags[b] & 0x80:
                    raise SystemExit(f'FAIL: room {room} box {b} closed ({flags[b]})')
            for b in closed:
                if not flags[b] & 0x80:
                    raise SystemExit(f'FAIL: room {room} box {b} open')
    print(f'PASS: Dig light bridges drawn ({", ".join(f"{r}:{n}" for r, n in sorted(drawn.items()))} pixels), '
          f'walk boxes open, every spire and the hub reachable')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
