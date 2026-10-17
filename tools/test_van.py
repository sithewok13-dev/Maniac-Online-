#!/usr/bin/env python3
"""Melissa and Leslie's van, flown through the real engine.

Needs privately supplied Maniac Mansion and Zak DOS V1 data; with an export
cache holding Monkey Island (tools/export_worlds.py) the van also lands
there. Boards at the Mars landing site with a companion, launches from the
controls, flies with travel locked (saved and loaded in flight), lands in
San Francisco where it is drawn and boarded again, and flies home to Mars.
Not an iPhone test.
"""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds')
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    monkey = (a.worlds/'monkey-20.svw').exists()
    run_probe(a.data.resolve(), (ROOT/'tools/probes/van.inc').read_text().replace('@MONKEY@', 'true' if monkey else 'false'),
              'scummverse_roaming', 'SCUMMVERSE_VAN_PASS', 'van', PRELUDE, a.build, timeout=600,
              extra_config=f'scummverse_worlds_path={a.worlds.resolve()}\n')
    print('PASS: van' + (' (Monkey Island included)' if monkey else ' (no Monkey Island export)'))
