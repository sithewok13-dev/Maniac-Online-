#!/usr/bin/env python3
"""The Dig's tram, ridden through the real engine.

Needs an export cache (build/worlds, see tools/export_worlds.py) holding a
privately supplied copy of The Dig. At the Nexus station of the map-spire
line the ledge calls the car; Dave, his companion and someone on the ledge
board during the wait (not someone standing back), travel is locked during
the ride (saved and loaded halfway), everyone steps off at the spire
station, and the parked car there opens at once but never leaves without
the player. A damaged save's phase for that trip (before its start, past
its end) is dropped first: the ledge's call goes through. Not an iPhone test.
"""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds')
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    if not (a.worlds/'dig-80-car.svw').exists():
        print(f'SKIP: no Dig tram export in {a.worlds} (run tools/export_worlds.py with dig=...)')
        raise SystemExit(0)
    run_probe(a.data.resolve(), (ROOT/'tools/probes/dig_tram.inc').read_text(), 'scummverse_roaming',
              'SCUMMVERSE_DIG_TRAM_PASS', 'dig-tram', PRELUDE, a.build, timeout=600,
              extra_config=f'scummverse_worlds_path={a.worlds.resolve()}\n')
