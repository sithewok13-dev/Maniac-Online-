#!/usr/bin/env python3
"""Compare every imported sandbox room with original Zak logical scenes.

Requires privately supplied English DOS V1 Maniac Mansion and Zak data. The
original interpreter runs each candidate scene's own entry handler; the
sandbox renders each imported room. Both actor-free viewports at the camera
minimum are compared pixel for pixel. Captures, reports and contact sheets stay
in ignored build/scene-audit. This verifies initialized background artwork,
object state and colors, not animation, scrolling or puzzle progression.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE

OUT = ROOT/'build/scene-audit'
ZAK_INDEX_MD5 = '7020931d5a2be0a49d68e7a1882363e4'
# Region values of original variable 222+ego that select jungle colors.
REGIONS = {'zaire': 150, 'peru': 42, 'default': 0}

# Sandbox room -> expected original logical scene (room, region), or None when
# the original game has no such scene. Evidence: pseudo-room table, airport
# ticket mapping (scripts 58/120), crystal-map teleports (map objects 480-487),
# jungle entry colors. Rooms absent here are reported but not asserted.
EXPECTED = {
    56: (11, 0), 58: (12, 0), 59: (13, 0),
    57: (144, 0), 60: (143, 0), 77: (141, 0), 85: (142, 0),   # big airports
    61: (147, 0), 66: (148, 0), 70: (146, 0), 94: (149, 0),   # regional airports
    62: (170, 150), 95: (175, 42), 86: (168, 0),               # first jungle scene by region
    78: (133, 0), 72: (20, 0), 67: (17, 0),                    # airport exits
    63: (150, 0), 96: (42, 0), 87: (39, 0),
    64: None, 65: None, 97: None, 98: None,                    # not in original
    89: (130, 0), 92: (129, 0), 93: (194, 0),
    63: (150, 0), 80: (180, 0), 68: (19, 0), 74: (23, 0), 75: (155, 0),
    79: (185, 0), 81: (30, 0),
}
# Explained, bounded differences. Anything larger, or any camera difference,
# still fails. Keep reasons specific; remove entries once the cause is fixed.
TOLERANCE = {
    58: (0.03, 'loose-dirt cave opening shown dug: sandbox route into the cave'),
    93: (0.002, 'machine display defaults; covered by tools/test_mars_reference.py'),
}


def pseudo_rooms(zak):
    """Original logical->physical mapping, read from the supplied data."""
    mapping = {}
    for path in sorted(zak.glob('*.LFL')):
        data = bytes(b ^ 0xFF for b in path.read_bytes())
        for i in range(len(data) - 3):
            if data[i] == 0xCC and 1 <= data[i+1] <= 60:
                j, logical = i + 2, []
                while j < len(data) and data[j] >= 0x80:
                    logical.append(data[j]); j += 1
                if logical and j < len(data) and data[j] == 0 and len(logical) <= 16:
                    for room in logical:
                        mapping.setdefault(room, data[i+1])
    return mapping


def ppm(path):
    data = path.read_bytes()
    header, rest = data.split(b'\n', 1)
    size, rest = rest.split(b'\n', 1)
    _, pixels = rest.split(b'\n', 1)
    width, height = map(int, size.split())
    return width, height, pixels


def difference(a, b):
    wa, ha, pa = ppm(a)
    wb, hb, pb = ppm(b)
    if (wa, ha) != (wb, hb):
        return 1.0
    differing = sum(1 for i in range(0, len(pa), 3) if pa[i:i+3] != pb[i:i+3])
    return differing / (wa * ha)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('maniac', type=Path)
    p.add_argument('zak', type=Path)
    p.add_argument('--build', choices=('null', 'asan'), default='null')
    p.add_argument('--batch', type=int, default=18)
    a = p.parse_args()
    zak = a.zak.resolve()
    if hashlib.md5((zak/'00.LFL').read_bytes()).hexdigest() != ZAK_INDEX_MD5:
        p.error('Requires the audited English DOS V1 Zak edition')
    OUT.mkdir(parents=True, exist_ok=True)

    run_probe(a.maniac.resolve(), (ROOT/'tools/probes/scene_audit_sandbox.inc').read_text(),
              'scummverse_roaming', 'SCUMMVERSE_SCENE_SANDBOX_PASS', 'scene-sandbox',
              PRELUDE + '\nnamespace ProbeCatalog {\n#include "scumm/scummverse_places.inc"\n}\n', a.build)
    sandbox = {r['room']: r for r in json.loads((OUT/'sandbox.json').read_text())['rooms']}

    mapping = pseudo_rooms(zak)
    resources = {r['resource'] for r in sandbox.values() if r['resource']} | {8, 9}
    candidates = set()
    for resource in resources:
        candidates.add((resource, resource, 0))
        candidates.update((logical, resource, 0) for logical, phys in mapping.items() if phys == resource)
    jungle = [logical for logical, phys in mapping.items() if phys == 37]
    candidates.update((logical, 37, region) for logical in jungle for region in REGIONS.values())
    for expected in EXPECTED.values():
        if expected:
            room, region = expected
            candidates.add((room, mapping.get(room, room), region))
    candidates = sorted(candidates)
    reference = {}
    for start in range(0, len(candidates), a.batch):
        chunk = candidates[start:start+a.batch]
        code = (ROOT/'tools/probes/scene_audit_reference.inc').read_text().replace(
            '@CANDIDATES@', ','.join('{%d,%d,%d}' % c for c in chunk))
        run_probe(zak, code, 'scummverse_roaming', 'SCUMMVERSE_SCENE_REFERENCE_PASS',
                  'scene-reference', PRELUDE, a.build, reference_game='zak')
        for scene in json.loads((OUT/'reference.json').read_text())['scenes']:
            reference[(scene['logical_room'], scene['region'])] = scene

    (OUT/'reference-all.json').write_text(json.dumps(sorted(reference.values(), key=lambda s: (s['logical_room'], s['region']))))
    results, failures = [], []
    for room, info in sorted(sandbox.items()):
        shot = OUT/f'sbx-{room}.ppm'
        same_resource = [key for key, scene in reference.items() if scene['resource'] == info['resource']]
        scored = sorted((difference(shot, OUT/f'ref-{key[0]}-{key[1]}.ppm'), key) for key in same_resource)
        best = scored[0] if scored else (1.0, None)
        expected = EXPECTED.get(room, 'unaudited')
        entry = {'room': room, 'resource': info['resource'], 'best_logical': best[1],
                 'best_difference': round(best[0], 4), 'expected': expected}
        if expected is None:
            entry['verdict'] = 'not in original game'
        elif expected == 'unaudited':
            entry['verdict'] = 'exact' if best[0] == 0 else 'unaudited'
        else:
            key = tuple(expected)
            path = OUT/f'ref-{key[0]}-{key[1]}.ppm'
            diff = difference(shot, path) if path.exists() else 1.0
            entry['expected_difference'] = round(diff, 4)
            original = reference.get(key, {})
            entry['camera'] = info['camera']
            entry['original_camera'] = original.get('camera')
            limit, reason = TOLERANCE.get(room, (0, ''))
            if original.get('camera') != info['camera']:
                entry['verdict'] = 'camera mismatch'
            elif diff == 0:
                entry['verdict'] = 'exact'
            elif diff <= limit:
                entry['verdict'], entry['reason'] = 'explained difference', reason
            else:
                entry['verdict'] = 'mismatch'
        if entry['verdict'] in ('mismatch', 'camera mismatch', 'not in original game'):
            failures.append(entry)
        results.append(entry)
    (OUT/'report.json').write_text(json.dumps({'rooms': results}, indent=1))
    exact = sum(1 for r in results if r['verdict'] == 'exact')
    print(f'{exact}/{len(results)} imported rooms match an original scene exactly')
    for entry in failures:
        print(f"  room {entry['room']}: {entry['verdict']} (expected {entry['expected']}, "
              f"best {entry['best_logical']} diff {entry['best_difference']}, "
              f"camera {entry.get('camera')} vs original {entry.get('original_camera')})")
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
