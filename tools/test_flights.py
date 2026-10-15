#!/usr/bin/env python3
"""Verify original-data flights, manifest save/load, sightseeing exits and bus timing."""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('data',type=Path); p.add_argument('--build',choices=('null','asan'),default='null'); a=p.parse_args()
    run_probe(a.data.resolve(),(ROOT/'tools/probes/flights.inc').read_text(),'scummverse_roaming','SCUMMVERSE_FLIGHTS_PASS','flights',PRELUDE+'\nnamespace ProbeCatalog {\n#include \"scumm/scummverse_places.inc\"\n}\n',a.build)
