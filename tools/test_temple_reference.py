#!/usr/bin/env python3
"""Audit original logical temple scenes through Zak entry scripts.
Requires the privately supplied English DOS V1 edition. This verifies isolated
scene setup, not original puzzle progression or sandbox seating correctness.
"""
import argparse
import hashlib
import json
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('data', type=Path)
p.add_argument('--build', choices=('null', 'asan'), default='null')
a = p.parse_args()
data = a.data.resolve()
if hashlib.md5((data/'00.LFL').read_bytes()).hexdigest() != '7020931d5a2be0a49d68e7a1882363e4':
    p.error('Requires the audited English DOS V1 Zak edition')
if hashlib.md5((data/'53.LFL').read_bytes()).hexdigest() != 'c7260003f7c70b810560c1def0d04678':
    p.error('Unexpected temple resource version')
run_probe(data, (ROOT/'tools/probes/temple_reference.inc').read_text(),
          'scummverse_roaming', 'SCUMMVERSE_TEMPLE_REFERENCE_PASS',
          'temple-reference', PRELUDE, a.build, reference_game='zak')

scenes=json.loads((ROOT/'build/temple-reference.json').read_text())['scenes']
assert [s['logical_room'] for s in scenes]==list(range(156,168))
assert len({tuple((o['id'],o['x'],o['y'],o['state']) for o in s['objects']) for s in scenes})>=3
# Only active, touchable original exit objects contribute traversal edges.
exit_pairs={741:2,742:3,743:4,744:0,745:1,746:1,747:5}
graph={s['logical_room']:{s['transition_pairs'][exit_pairs[o['id']]][1]
 for o in s['objects'] if o['id'] in exit_pairs and o['state']&8 and not o['state']&2}
 for s in scenes}
seen={156}
while True:
 expanded=seen | {v for n in seen for v in graph.get(n,set())}
 if expanded==seen:break
 seen=expanded
assert set(range(156,168)) <= seen and 130 in seen and 39 in seen
print('PASS: twelve original temple scenes form a reachable graph with exterior and crystal-chamber exits')
