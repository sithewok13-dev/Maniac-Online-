#!/usr/bin/env python3
"""Wanderers through the real engine: other games' characters out of their homes.

Needs privately supplied Maniac Mansion data and an export cache (build/worlds,
see tools/export_worlds.py) holding at least Monkey Island. Forty are out,
each once; Guybrush is not at home in Monkey Island while he wanders; three
in the living room are drawn there from their own frames, another walks in
from a side; the others move on while the living room's stay; Guybrush
greets once in his colour; one moved away leaves no trace; save and load
keep them; none on the plane or in the van's cockpit; in time others take
their turn; in the dark basement one is a grey shape as Dave is, in its
colours lit again; nobody greets the player out of sight on Zak's bus. Not
an iPhone test.
"""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds')
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    # (Forty out and others taking turns need a cast of fifty or more.)
    if not (a.worlds/'monkey-33.svw').exists() or not (a.worlds/'monkey-c1.svc').exists() or len(list(a.worlds.glob('*.svc'))) < 50:
        print(f'SKIP: not enough exported characters in {a.worlds} (run tools/export_worlds.py with several games)')
        raise SystemExit(0)
    run_probe(a.data.resolve(), (ROOT/'tools/probes/wander.inc').read_text(), 'scummverse_roaming',
              'SCUMMVERSE_WANDER_PASS', 'wander', PRELUDE, a.build, timeout=600,
              extra_config=f'scummverse_worlds_path={a.worlds.resolve()}\nscummverse_wanderers=true\n')
    print('PASS: wanderers')
