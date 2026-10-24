#!/usr/bin/env python3
"""What a damaged settings file, export or save leaves, through the real engine.

The mansion started with settings as a file cut short while the app was
stopped writing it leaves them (not true or false, not a number, out of
range): it starts, each read as its default or as not kept (ConfMan's own
getBool and getInt end the app there); a scene an export stopped partway
left, in a scratch worlds folder, its size saying gigabytes, is not read
and said so at once; the van's scale and the Dig tram's trip and phase as a
damaged save holds them are kept within reason (no step held up, no trip no
line has). Not an iPhone test.
"""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE

# (Each cut short: 'tr' for true, 'fal' for false; a number that is not one,
# and one out of range.)
SETTINGS = ('scummverse_roaming=tr\nscummverse_wanderers=fal\nscummverse_exploration_safety=ye\n'
            'scummverse_tour_stop=abc\nscummverse_tour_speed=99999999999\n')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds')
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    # (Exploration doors, set right, both ways: read as they are.)
    run_probe(a.data.resolve(), (ROOT/'tools/probes/damaged.inc').read_text(), 'scummverse_exploration_doors',
              'SCUMMVERSE_DAMAGED_PASS', 'damaged', PRELUDE, a.build, timeout=600,
              extra_config=f'scummverse_worlds_path={a.worlds.resolve()}\n' + SETTINGS)
    print('PASS: damaged settings, scene, van and tram')
