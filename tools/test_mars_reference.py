#!/usr/bin/env python3
"""Audit original Mars logical scene setup using privately supplied DOS V1 data."""
import argparse
import hashlib
import json
from pathlib import Path
from test_exploration import ROOT,run_probe
from test_ai_encounters import PRELUDE
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('data',type=Path)
p.add_argument('--build',choices=('null','asan'),default='null')
a=p.parse_args()
if hashlib.md5((a.data/'00.LFL').read_bytes()).hexdigest()!='7020931d5a2be0a49d68e7a1882363e4':
 p.error('Requires audited English DOS V1 edition')
run_probe(a.data.resolve(),(ROOT/'tools/probes/mars_reference.inc').read_text(),
 'scummverse_roaming','SCUMMVERSE_MARS_REFERENCE_PASS','mars-reference',PRELUDE,a.build,reference_game='zak')
report=json.loads((ROOT/'build/mars-reference.json').read_text())
scenes={s['logical_room']:s for s in report['scenes']}
assert set(range(188,206))<=scenes.keys()
assert all(scenes[n]['resource']==36 for n in range(196,206))
assert all(scenes[n]['camera']==[480,480] for n in (188,189,190,191,194))
assert scenes[195]['camera']==[160,160]
print('PASS: original Mars logical resources, split-room cameras and maze variants')
