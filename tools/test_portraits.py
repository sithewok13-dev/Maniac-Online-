#!/usr/bin/env python3
"""Verify all character portraits retain transparent padding with original costumes."""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('data',type=Path); p.add_argument('--build',choices=('null','asan'),default='null'); a=p.parse_args()
    run_probe(a.data.resolve(),(ROOT/'tools/probes/portraits.inc').read_text(),'scummverse_roaming','SCUMMVERSE_PORTRAITS_PASS','portraits',PRELUDE.replace('void scummverseRosterFace(int,const unsigned char *) {}', 'namespace FakeFaces { unsigned char pixels[25][64*64*4]={}; unsigned mask=0; }\nvoid scummverseRosterFace(int id,const unsigned char *data) { memcpy(FakeFaces::pixels[id],data,64*64*4); FakeFaces::mask |= 1u<<id; }') + '\nnamespace ProbeCatalog {\n#include "scumm/scummverse_places.inc"\n}\n',a.build)
