#!/usr/bin/env python3
"""The CAMERA through the real engine (Linux; not the iPhone's button,
flash, shutter or saving).

A photo of the room (CLEAN) is the room as drawn, each pixel 5 by 6, 1600
wide; one of the whole screen (FULL) is 1600 by 1200 with the verbs and
inventory. A selfie of three holds the game still (no variable changes),
poses everyone afresh for each shot, frames the player (whole pixels, 4:5 to
4:3, the player whole: the frame found in the screen it was cut from), and
leaves the game's saved state byte for byte as it was; also in another world
(Melee Island) when exported. A row of the kids too wide for the room's
height at 4:3 gets a narrower frame of the room's whole height, 4:3 at most,
Dave and those beside him whole. The game holds still while iOS asks for
Photos access; no selfie without the player in the room.
"""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE

CAMERA = r'''
#include "common/scummverse_camera.h"
#include "common/memstream.h"
#include "common/serializer.h"
#include <string>
#include <vector>
namespace FakeCamera {
std::vector<Scummverse::Camera::Picture> pictures;
std::vector<int> kinds, shot, shots;
void sink(const Scummverse::Camera::Picture &p, int kind, int s, int n, void *) {
 if (pictures.empty()) { kinds.clear(); shot.clear(); shots.clear(); }
 pictures.push_back(p); kinds.push_back(kind); shot.push_back(s); shots.push_back(n);
}
struct Install { Install() { Scummverse::Camera::setSink(sink, nullptr); } } install;
}
'''

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds')
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    run_probe(a.data.resolve(), (ROOT/'tools/probes/camera.inc').read_text(), 'scummverse_roaming',
              'SCUMMVERSE_CAMERA_PASS', 'camera', CAMERA + PRELUDE, a.build, timeout=600,
              extra_config=f'scummverse_worlds_path={a.worlds.resolve()}\n')
