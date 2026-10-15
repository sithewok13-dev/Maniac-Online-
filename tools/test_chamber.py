#!/usr/bin/env python3
"""Compare Mexico chamber setup with independently executed original Zak scripts.
Private snapshots stay in build/. Source game data is never modified or shipped.
"""
import argparse
import hashlib
import json
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('data',type=Path,help='Maniac DOS data; Zak is in sibling zak-dos')
p.add_argument('--build',choices=('null','asan'),default='null')
a=p.parse_args()
zak=a.data.resolve().parent/'zak-dos'
if hashlib.md5((zak/'00.LFL').read_bytes()).hexdigest()!='7020931d5a2be0a49d68e7a1882363e4':
 p.error('Requires original English Zak DOS V1')
run_probe(zak,(ROOT/'tools/probes/chamber_reference.inc').read_text(),
 'scummverse_roaming','SCUMMVERSE_CHAMBER_REFERENCE_PASS','chamber-reference',PRELUDE,a.build,reference_game='zak')
report=json.loads((ROOT/'build/chamber-reference.json').read_text())
scene=next(s for s in report['scenes'] if s['logical_room']==130)
assert scene['resource']==14 and len(scene['objects'])==21
checks='\n'.join(f'if(getState({732+i})!={o["state"]}) error("Source object {o["id"]} state mismatch: %d",getState({732+i}));' for i,o in enumerate(scene['objects']))
probe=(ROOT/'tools/probes/chamber.inc').read_text().replace('@REFERENCE_CHECKS@',checks)
run_probe(a.data.resolve(),probe,'scummverse_roaming','SCUMMVERSE_CHAMBER_PASS','chamber',PRELUDE,a.build)
original=(ROOT/'build/chamber-reference-130.ppm').read_bytes()
actual=(ROOT/'build/chamber-sandbox.ppm').read_bytes()
if original!=actual:
 raise AssertionError('Source/sandbox Mexico chamber background pixels differ; inspect private build images')
print('PASS: Mexico chamber background exactly matches the original interpreter fixture')
