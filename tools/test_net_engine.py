#!/usr/bin/env python3
"""Local WiFi play through the real engine over loopback TCP.

The engine hosts; a second session joins as another device controlling Zak.
Checks remote avatars, walking, room changes, speech both ways, validation and
release on departure. One process on one machine: not a two-device or iPhone
network test.
"""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    # (From 0196 a place in another world too, where one is exported.)
    worlds = ROOT/'build/worlds'
    run_probe(a.data.resolve(), (ROOT/'tools/probes/net.inc').read_text(), 'scummverse_roaming',
              'SCUMMVERSE_NET_PASS', 'net',
              '#include "common/scummverse_net.h"\n#include "common/scummverse_net_engine.h"\n' + PRELUDE, a.build,
              extra_config=f'scummverse_worlds_path={worlds.resolve()}\n' if (worlds/'monkey-33.svw').exists() else '')
