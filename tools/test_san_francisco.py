#!/usr/bin/env python3
"""Zak's San Francisco walked on foot through the real engine.

Needs privately supplied Maniac Mansion and Zak DOS V1 data. Taps doors like
a player from Zak's bedroom through his living room to 13th Avenue, up the
corner to 14th Avenue, into Lou's Loans and the Society office (saved and
loaded there) and home again; checks the Society door and walk boxes, an
NPC taking the corner offscreen, retired room IDs, the Shuttle Bug's door,
and a pre-0073 save standing in old temple rooms. Not an iPhone test.
"""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    run_probe(a.data.resolve(), (ROOT/'tools/probes/san_francisco.inc').read_text(), 'scummverse_roaming',
              'SCUMMVERSE_SF_PASS', 'san-francisco',
              PRELUDE + '\nnamespace ProbeCatalog {\n#include "scumm/scummverse_places.inc"\n}\n', a.build, timeout=600)
