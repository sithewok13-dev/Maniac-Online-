#!/usr/bin/env python3
"""The mansion's padlocked door through the original scripts.

Needs privately supplied Maniac Mansion DOS V1 data. In room 4 the door
(160) stays locked until both its padlocks (161, 162) are unlocked with the
key from the pit; the second unlocks the door, and then Open opens it. The
new engine's kManiacPadlocks follows this (from 0203). Not an iPhone test.
"""
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
    run_probe(data, (ROOT/'tools/probes/mansion_locks.inc').read_text(),
              'scummverse_exploration_safety', 'SCUMMVERSE_MANSION_LOCKS_PASS', 'mansion-locks', timeout=300)
    print('PASS: the padlocked door locked until both padlocks are unlocked with the key, then opened, as the original scripts')


if __name__ == '__main__':
    main()
