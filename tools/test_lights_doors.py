#!/usr/bin/env python3
"""Lights and doors, through the real engine.

Needs privately supplied Maniac Mansion and Zak DOS V1 data. Maniac
Mansion's six rooms the original starts dark are lit in a new sandbox, the
basement's switch still turns its light off (and off stays off) and on, a
save from before is lit once; the tour opens each door the guide sets off
to before it goes through (Maniac's, and Zak's whose open picture was
checked, plus the door back on arrival) and leaves Zak's others as drawn;
the player's walk through a Zak door opens the door back. Door tables come
from the source. Not an iPhone test.
"""
import argparse, re
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE

def table(path, name):
    src = (ROOT/path).read_text()
    start = src.index(name); end = src.index('};', start)
    return src[start:end]

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds')
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    passages = re.findall(r'\{(\d+), (\d+), \d+, \d+, (true|false)', table('engine/engines/scumm/scummverse_roaming.inc', 'mansionPassages[] = {'))
    links = re.findall(r'\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', table('engine/engines/scumm/scummverse_places.inc', 'zakLinks[] = {'))
    clean = re.findall(r'\{(\d+), (\d+)\}', table('engine/engines/scumm/scummverse_places.inc', 'zakOpenDoors[][2] = {'))
    probe = (ROOT/'tools/probes/lights_doors.inc').read_text()
    probe = probe.replace('@PASSAGES@', ','.join('{%s,%s,%s}' % r for r in passages))
    probe = probe.replace('@ZAKLINKS@', ','.join('{%s,%s,%s}' % r for r in links))
    probe = probe.replace('@ZAKOPEN@', ','.join('{%s,%s}' % r for r in clean))
    run_probe(a.data.resolve(), probe, 'scummverse_roaming', 'SCUMMVERSE_LIGHTS_DOORS_PASS', 'lights-doors', PRELUDE,
              a.build, timeout=1200, extra_config=f'scummverse_worlds_path={a.worlds.resolve()}\n')
    print('PASS: lights and doors')
