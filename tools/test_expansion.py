#!/usr/bin/env python3
"""Exercise supplied-data rooms, expanded playable roster, flights and on-demand bus."""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('data',type=Path); p.add_argument('--seed',type=int,default=0); p.add_argument('--build',choices=('null','asan'),default='null'); a=p.parse_args()
    run_probe(a.data.resolve(),('_rnd.setSeed(%du);\n' % a.seed)+(ROOT/'tools/probes/expansion.inc').read_text(),'scummverse_roaming','SCUMMVERSE_EXPANSION_PASS','expansion',PRELUDE.replace('void scummverseRosterFace(int,const unsigned char *) {}', 'namespace FakeFaces { unsigned char pixels[25][64*64*4]={}; unsigned mask=0; }\nvoid scummverseRosterFace(int id,const unsigned char *data) { memcpy(FakeFaces::pixels[id],data,64*64*4); FakeFaces::mask |= 1u<<id; }') + '\nnamespace ProbeCatalog {\n#include "scumm/scummverse_places.inc"\n}\n',a.build)
