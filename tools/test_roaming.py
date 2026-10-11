#!/usr/bin/env python3
"""Probe sandbox behavior with user-supplied DOS V1 resources (never bundled)."""
import argparse
import hashlib
from test_exploration import ROOT, run_probe

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=__import__('pathlib').Path)
    data = parser.parse_args().data.resolve()
    if hashlib.md5((data/'00.LFL').read_bytes()).hexdigest() != '7f45ddd6dbfbf8f80c0c0efea4c295bc':
        parser.error('Requires audited original English DOS V1')
    run_probe(data, (ROOT/'tools/probes/roaming.inc').read_text(),
              'scummverse_roaming', 'SCUMMVERSE_ROAMING_PROBE_PASS', 'roaming')
