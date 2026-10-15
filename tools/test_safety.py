#!/usr/bin/env python3
"""Exercise original DOS V1 capture/death scripts with protection on and off."""
import argparse
import hashlib
from pathlib import Path
from test_exploration import ROOT, run_probe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=Path)
    args = parser.parse_args()
    data = args.data.resolve()
    if hashlib.md5((data/'00.LFL').read_bytes()).hexdigest() != '7f45ddd6dbfbf8f80c0c0efea4c295bc':
        parser.error('Requires the audited English DOS V1 edition')
    run_probe(data, (ROOT/'tools/probes/safety.inc').read_text(),
              'scummverse_exploration_safety', 'SCUMMVERSE_SAFETY_PROBE_PASS', 'safety')


if __name__ == '__main__':
    main()
