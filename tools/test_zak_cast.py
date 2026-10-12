#!/usr/bin/env python3
"""Verify original-data Zak cast rendering, roaming, companions and save/load."""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('data',type=Path); p.add_argument('--build',choices=('null','asan'),default='null'); a=p.parse_args()
    run_probe(a.data.resolve(),(ROOT/'tools/probes/zak_cast.inc').read_text(),'scummverse_roaming','SCUMMVERSE_ZAK_CAST_PASS','zak-cast',PRELUDE,a.build)
