#!/usr/bin/env python3
"""Fishbowls and oxygen tanks on Mars, through the real engine.

Needs privately supplied Maniac Mansion and Zak DOS V1 data; with an export
cache holding Curse of Monkey Island's characters (tools/export_worlds.py)
Bernard also plays Murray. Lines characters up where there is air (the
hostel's airlock and bunks, the Face's Great Chamber, its three massive doors
and machine chamber) and where there is none (outside the Great Pyramid,
inside it, the landing site): the gear is drawn on those who breathe and only
there, never on the tentacle or the Caponian. Then the player plays the
Meteor Police (his dome is his helmet: no gear), the plant and both Teds
(gear) and Chaos (none) outside on Mars. Not an iPhone test.
"""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds')
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    murray = (a.worlds/'comi-c49.svc').exists()
    run_probe(a.data.resolve(), (ROOT/'tools/probes/mars_air.inc').read_text().replace('@MURRAY@', 'true' if murray else 'false'),
              'scummverse_roaming', 'SCUMMVERSE_MARS_AIR_PASS', 'mars-air',
              PRELUDE.replace('void scummverseRosterFace(int,const unsigned char *) {}',
                              'void scummverseRosterFace(int,const unsigned char *) {}'),
              a.build, timeout=600, extra_config=f'scummverse_worlds_path={a.worlds.resolve()}\n')
    print('PASS: Mars air gear' + (' (Murray included)' if murray else ' (no Curse of Monkey Island export: Murray skipped)'))
