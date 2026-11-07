#!/usr/bin/env python3
"""The basement's water valve through the original scripts.

Needs privately supplied Maniac Mansion DOS V1 data. Opening or turning on
the valve (object 66, room 29) shows its second picture and the pool's
(139, the pool deck, room 6: drained) and makes the pool's ladder (172) usable;
closing or turning it off undoes all three. The new engine's
kManiacFollows and kManiacDoorNeeds follow this. Not an iPhone test.
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
    run_probe(data, (ROOT/'tools/probes/pool_valve.inc').read_text(),
              'scummverse_exploration_safety', 'SCUMMVERSE_POOL_VALVE_PASS', 'pool-valve', timeout=300)
    print('PASS: the water valve drains and fills the pool, its ladder usable only drained')


if __name__ == '__main__':
    main()
