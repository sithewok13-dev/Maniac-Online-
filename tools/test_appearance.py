#!/usr/bin/env python3
"""Playing someone from another game, through the real engine.

Needs an export cache (build/worlds, see tools/export_worlds.py) made from
privately supplied games, at least Last Crusade and Monkey Island. Dave
plays Indiana Jones and Bernard Guybrush: names, chat identity, frames
mounted beside a scene's own characters, drawn height in the mansion and
in two other worlds, save/load, refusal of unknown characters, and back to
Dave. Not an iPhone test.
"""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds')
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    if not list(a.worlds.glob('indy3-*.svc')) or not list(a.worlds.glob('monkey-*.svc')):
        print(f'SKIP: no Last Crusade and Monkey Island characters in {a.worlds} (run tools/export_worlds.py)')
        raise SystemExit(0)
    run_probe(a.data.resolve(), (ROOT/'tools/probes/appearance.inc').read_text(), 'scummverse_roaming',
              'SCUMMVERSE_APPEARANCE_PASS', 'appearance',
              PRELUDE.replace('void scummverseRosterFace(int,const unsigned char *) {}',
                              'namespace FakeFaces { unsigned char pixels[25][64*64*4]={}; }\n'
                              'void scummverseRosterFace(int id,const unsigned char *data) { memcpy(FakeFaces::pixels[id],data,64*64*4); }'),
              a.build, timeout=600,
              extra_config=f'scummverse_worlds_path={a.worlds.resolve()}\n')
