#!/usr/bin/env python3
"""Print ZakSceneSetup entries from a private original-interpreter reference.

Run tools/test_scene_authenticity.py first; it writes
build/scene-audit/reference-all.json from the supplied DOS V1 data. Arguments
are sandbox:logical[:region] triples, e.g. 57:144 62:170:150. The output holds
initialized scene facts (object positions/states, box flags, camera bounds and
room colors), not source artwork or scripts.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    scenes = {(s['logical_room'], s['region']): s
              for s in json.loads((ROOT/'build/scene-audit/reference-all.json').read_text())}
    for spec in sys.argv[1:]:
        parts = [int(v) for v in spec.split(':')]
        room, logical, region = parts[0], parts[1], parts[2] if len(parts) > 2 else 0
        s = scenes[(logical, region)]
        if len(s['objects']) > 33 or len(s['box_flags']) > 16:
            raise SystemExit(f'{spec}: exceeds descriptor capacity')
        boxes = ','.join(str(f) for f in s['box_flags']) or '0'
        print(f" {{{room},{logical},{s['camera'][0]},{s['camera'][1]},{len(s['box_flags'])},{len(s['objects'])},"
              f"{{{','.join(str(c) for c in s['palette'])}}},{{{boxes}}},{{")
        print(',\n'.join(f"  {{{o['id']},{o['x']},{o['y']},{o['state']}}}" for o in s['objects']))
        print(' }},')


if __name__ == '__main__':
    main()
