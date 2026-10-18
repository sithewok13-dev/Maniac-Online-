#!/usr/bin/env python3
"""Run every test that needs privately supplied original data, in order.

Usage: python3 tools/test_all_data.py game-data/mm-dos game-data/zak-dos
Original-interpreter reference tests run first because several sandbox tests
compare against their private outputs. Probes run one at a time (they share the
build tree). test_temple_legacy is excluded: it needs a patch-0037 engine and
build. Logs go to build/data-tests/. Native probes are not iPhone acceptance.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ['test_mars_reference', 'test_temple_reference', 'test_source_reference',
             'test_perspective_reference']
SANDBOX = ['test_exploration', 'test_safety', 'test_roaming', 'test_ai_encounters', 'test_worlds',
           'test_airport', 'test_bus', 'test_flights', 'test_flight_join', 'test_companions',
           'test_companion_presence', 'test_seating', 'test_zak_paths', 'test_zak_cast',
           'test_portraits', 'test_walkboxes', 'test_perspective', 'test_chamber', 'test_temple',
           'test_mars', 'test_maze', 'test_san_francisco', 'test_dig_bridges', 'test_dig_tram', 'test_van', 'test_mars_air', 'test_appearance', 'test_camera_engine', 'test_expansion', 'test_net_engine', 'test_tram', 'test_world_visit', 'test_tour_engine']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('maniac', type=Path)
    p.add_argument('zak', type=Path)
    p.add_argument('--only', nargs='*', help='run only these test names')
    a = p.parse_args()
    logs = ROOT/'build/data-tests'
    logs.mkdir(parents=True, exist_ok=True)
    plan = [(t, a.zak) for t in REFERENCE] + [(t, a.maniac) for t in SANDBOX]
    plan.append(('test_scene_authenticity', None))
    results = []
    for name, data in plan:
        if a.only and name not in a.only:
            continue
        args = [sys.executable, str(ROOT/'tools'/f'{name}.py')]
        args += [str(a.maniac.resolve()), str(a.zak.resolve())] if data is None else [str(data.resolve())]
        start = time.time()
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
        (logs/f'{name}.log').write_text(result.stdout + result.stderr)
        status = 'PASS' if result.returncode == 0 else 'FAIL'
        results.append((name, status))
        print(f'{status} {name} ({time.time()-start:.0f}s)', flush=True)
    failed = [n for n, s in results if s != 'PASS']
    print(f'{len(results)-len(failed)}/{len(results)} data tests passed' + (f'; failed: {failed}' if failed else ''))
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
