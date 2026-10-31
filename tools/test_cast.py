#!/usr/bin/env python3
"""The character screen, through the real engine.

Needs privately supplied Maniac Mansion and Zak DOS V1 data and the other
worlds' export cache (tools/export_worlds.py). A new sandbox game starts
without Maniac Mansion's opening and shows the character screen: a box per
game (12) with its lead first (Dave, Zak, each other game's lead), its
face for every game here; choosing a lead from another game plays them
where they live; choosing Bernard plays him as himself; "Play as someone
else" shows the screen again. The iPhone screen itself is not tested here.
"""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds')
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    run_probe(a.data.resolve(), (ROOT/'tools/probes/cast.inc').read_text(),
              'scummverse_roaming', 'SCUMMVERSE_CAST_PASS', 'cast', PRELUDE, a.build, timeout=600,
              extra_config=f'scummverse_worlds_path={a.worlds.resolve()}\n')
    print('PASS: character screen')
