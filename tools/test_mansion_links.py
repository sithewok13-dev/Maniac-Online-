#!/usr/bin/env python3
"""What the mansion's things do to other things, through the original scripts.

Needs privately supplied Maniac Mansion DOS V1 data. Opening and closing the
mailbox and the desk show and hide their open pictures; the hall's secret
door has no handle ("There's no handle here!"), the gargoyle pushed or
pulled opens it, and it shuts behind the one going down its stairs; the
garden gate moves as one (opened or pulled on the pool deck, all three of
its sides open, closed or pushed all shut; from the garage or the other
side, that side and the deck's); the bathroom's shower curtain moves as one;
its sink runs without its second picture; its shower's tap has no handle.
The new engine's kManiacSets, kManiacOpenedBy, kManiacTogether,
kManiacShutsBehind follow this (from 0155 the things file records what
every thing does). Not an iPhone test.
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
    print('PASS: the mailbox, the desk, the gate, the gargoyle\'s secret door, the shower curtain, the sink and the tap, as the original scripts')


if __name__ == '__main__':
    main()
