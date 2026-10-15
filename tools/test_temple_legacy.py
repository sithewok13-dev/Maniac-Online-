#!/usr/bin/env python3
"""Capture a private pre-replacement temple save using the patch-0037 engine.
Run with engine source AND build at patch 0037; refuses the expanded room count.
Then pass build/legacy-temple.s12 to test_temple.py --legacy-save on the new build.
Never commit the fixture: it contains user-supplied game data and saved state.
"""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('data',type=Path)
p.add_argument('--build',choices=('null','asan'),default='null')
a=p.parse_args()
run_probe(a.data.resolve(),(ROOT/'tools/probes/temple_legacy.inc').read_text(),
 'scummverse_roaming','SCUMMVERSE_LEGACY_TEMPLE_PASS','legacy-temple',PRELUDE,a.build)
