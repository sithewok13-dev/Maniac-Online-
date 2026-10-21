#!/usr/bin/env python3
"""What the mansion's things do to other things, through the original scripts.

Needs privately supplied Maniac Mansion DOS V1 data. Opening and closing the
mailbox and the desk show and hide their open pictures; the gate shows open
from the garage and from the other side; the hall's secret door has no
handle ("There's no handle here!") and the gargoyle pushed opens it. The
new engine's kManiacSets and kManiacOpenedBy follow this. Not an iPhone test.
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
    run_probe(data, (ROOT/'tools/probes/mansion_links.inc').read_text(),
              'scummverse_exploration_safety', 'SCUMMVERSE_MANSION_LINKS_PASS', 'mansion-links', timeout=300)
    print('PASS: the mailbox, the desk, the gate and the gargoyle\'s secret door, as the original scripts')


if __name__ == '__main__':
    main()
