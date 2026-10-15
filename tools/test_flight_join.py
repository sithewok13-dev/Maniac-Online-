#!/usr/bin/env python3
"""Verify same-route boarding, rejection isolation and joined-flight persistence."""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('data',type=Path)
p.add_argument('--build',choices=('null','asan'),default='null')
a=p.parse_args()
run_probe(a.data.resolve(),(ROOT/'tools/probes/flight_join.inc').read_text(),
 'scummverse_roaming','SCUMMVERSE_FLIGHT_JOIN_PASS','flight-join',
 PRELUDE+'\nnamespace ProbeCatalog {\n#include "scumm/scummverse_places.inc"\n}\n',a.build)
