#!/usr/bin/env python3
"""Render a source-interpreter Zak plane fixture without changing shipped startup.
Requires the privately supplied English DOS V1 edition. This verifies isolated
scene setup, not original puzzle progression or sandbox seating correctness.
"""
import argparse
import hashlib
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
run_probe(data, (ROOT/'tools/probes/source_reference.inc').read_text(),
          'scummverse_roaming', 'SCUMMVERSE_SOURCE_REFERENCE_PASS',
          'source-reference', PRELUDE, a.build, reference_game='zak')
