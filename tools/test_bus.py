#!/usr/bin/env python3
"""Exercise free bus travel with private original English DOS V1 resources."""
import argparse
import json
from pathlib import Path
import tempfile
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('maniac', type=Path)
    parser.add_argument('--build', choices=('null', 'asan'), default='null')
    parser.add_argument('--snapshot', type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='bus-invalid-', dir=ROOT/'build') as tmp:
        code = (ROOT/'tools/probes/bus.inc').read_text()
        code = code.replace('"@BAD_ZAK@"', json.dumps(tmp))
        code = code.replace('"@SNAPSHOT@"', json.dumps(str(args.snapshot.resolve()) if args.snapshot else ''))
        run_probe(args.maniac.resolve(), code, 'scummverse_roaming', 'SCUMMVERSE_BUS_PASS', 'bus', PRELUDE, args.build)
