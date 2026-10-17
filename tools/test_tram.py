#!/usr/bin/env python3
"""Mars tram: boarding wait, countdown, ride, call button, NPC riders, save/load."""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    run_probe(a.data.resolve(), (ROOT/'tools/probes/tram.inc').read_text(), 'scummverse_roaming',
              'SCUMMVERSE_TRAM_PASS', 'tram', PRELUDE, a.build)
