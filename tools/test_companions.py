#!/usr/bin/env python3
"""Exercise computer selection, companions, saves and imported sprite clipping with real private resources."""
import argparse, json, tempfile
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('maniac',type=Path)
p.add_argument('--build',choices=('null','asan'),default='null')
a=p.parse_args()
with tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
    code=(ROOT/'tools/probes/bus.inc').read_text().replace('"@BAD_ZAK@"',json.dumps(temp)).replace('"@SNAPSHOT@"','""')
    extra=(ROOT/'tools/probes/companions.inc').read_text().replace('@COMPARE@',str(ROOT/'build/connected-scale.ppm'))
    code=code.replace('warning("SCUMMVERSE_BUS_PASS enabled=1");',extra+'\nwarning("SCUMMVERSE_BUS_PASS enabled=1");')
    run_probe(a.maniac.resolve(),code,'scummverse_roaming','SCUMMVERSE_BUS_PASS','companions',PRELUDE,a.build)
