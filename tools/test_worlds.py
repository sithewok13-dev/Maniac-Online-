#!/usr/bin/env python3
"""Exercise a real Zak apartment visit using locally supplied original DOS resources."""
from pathlib import Path
import argparse
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('maniac', type=Path)
    parser.add_argument("--build", choices=("null", "asan"), default="null")
    args = parser.parse_args()
    # The default sibling 'zak' directory is also the iPhone layout. The game
    # starts without it (the boot reaches the sandbox before the probe runs)
    # and the probe then removes the missing path.
    run_probe(args.maniac.resolve(), (ROOT/'tools/probes/worlds.inc').read_text(),
              'scummverse_roaming', 'SCUMMVERSE_WORLDS_PASS', 'worlds', PRELUDE, args.build,
              extra_config='scummverse_zak_path=/nonexistent/zak\n')
