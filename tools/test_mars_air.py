#!/usr/bin/env python3
"""Fishbowls and oxygen tanks on Mars, through the real engine.

Needs privately supplied Maniac Mansion and Zak DOS V1 data; with an export
cache holding Curse of Monkey Island's characters (tools/export_worlds.py)
Bernard also plays Murray. Lines characters up in the hostel bunks (air) and
on the landing site (none): the gear is drawn on those who breathe and only
there, never on the tentacle or the Caponian. Not an iPhone test.
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
