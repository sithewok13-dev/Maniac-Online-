#!/usr/bin/env python3
"""Verify companion presence across ordinary transitions and vehicle boarding."""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('data',type=Path)
p.add_argument('--build',choices=('null','asan'),default='null')
a=p.parse_args()
run_probe(a.data.resolve(),(ROOT/'tools/probes/companion_presence.inc').read_text(),
 'scummverse_roaming','SCUMMVERSE_COMPANION_PRESENCE_PASS','companion-presence',
 PRELUDE+'\nnamespace ProbeCatalog {\n#include "scumm/scummverse_places.inc"\n}\n',a.build)
