#!/usr/bin/env python3
"""Other worlds in the sandbox: visit every exported scene through the engine.

Needs an export cache (build/worlds, see tools/export_worlds.py) made from
privately supplied games. Checks mounting, palette slots, walking, side
exits, save/load, a missing cache, and every scene's characters (placement,
names, talk roster, drawing, greeting, walking, save/load, leaving). Not an
iPhone test.
"""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds')
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    if not list(a.worlds.glob('*.svw')):
        print(f'SKIP: no other-worlds cache in {a.worlds} (run tools/export_worlds.py)')
        raise SystemExit(0)
    run_probe(a.data.resolve(), (ROOT/'tools/probes/world_visit.inc').read_text(), 'scummverse_roaming',
              'SCUMMVERSE_WORLD_VISIT_PASS', 'world-visit', PRELUDE, a.build, timeout=300,
              extra_config=f'scummverse_worlds_path={a.worlds.resolve()}\n')
