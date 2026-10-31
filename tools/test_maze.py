#!/usr/bin/env python3
"""Zak's pyramids and the Sphinx maze in the sandbox, walked through the real engine.

Needs privately supplied Maniac Mansion and Zak DOS V1 data. Taps doorways
like a player through every maze cell, the Egypt and Mars pyramid corridors,
sarcophagus chambers and stairs, checking each arrival's original camera,
walk boxes and doorway states; saves and loads inside the maze; and loads a
pre-0062 save standing in room 207 (then an other-world place). Not an
iPhone test.
"""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    run_probe(a.data.resolve(), (ROOT/'tools/probes/maze.inc').read_text(), 'scummverse_roaming',
              'SCUMMVERSE_MAZE_PASS', 'maze',
              PRELUDE + '\nnamespace ProbeCatalog {\n#include "scumm/scummverse_places.inc"\n}\n', a.build, timeout=600)
