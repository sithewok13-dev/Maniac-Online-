#!/usr/bin/env python3
"""Verify audited original walkbox restrictions for the walking cast."""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('data',type=Path); p.add_argument('--build',choices=('null','asan'),default='null'); a=p.parse_args()
    run_probe(a.data.resolve(),(ROOT/'tools/probes/walkboxes.inc').read_text(),'scummverse_roaming','SCUMMVERSE_WALKBOX_PASS','walkboxes',PRELUDE,a.build)
