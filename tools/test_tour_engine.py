#!/usr/bin/env python3
"""The TOUR through the real engine (Linux; not the iPhone's label or menu).

Asked as the Worlds menu does, the player's character visits stop 1 (a
mansion room), walks across it and goes on to stop 2 by itself; Stop brings
it back where it began; Resume (the remembered stop), Next and Previous;
then every stop is gone to by number and must be entered, in the room its
label names. Then what interrupts it: a load, playing someone else, a
place, a pad or someone chosen from the menus (the tour ends there), a ride
boarded while paused, the road's end walked off while paused (the guide
put there by the tour going nowhere), the van's flight chosen as it plays
on; a door of another game's tapped while paused (no tap kept after Stop
or a load); the autosave written as it begins and kept while touring (as
the phone asks for one); not touring, a save waiting for its frame (Tentacle's computer's)
never taken over by an autosave (the phone's, the game held still: the one
there kept as its restore point; with none, or in a story, refused;
ScummVM's own as the game runs refused, to try again soon). Zak's stops need his files; other worlds'
stops need their export cache (build/worlds), else they are passed over
(without Monkey Island's, so are its place and doors tried mid-tour; with
it, they must be tried). Not an iPhone test.
"""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('data', type=Path)
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds')
    p.add_argument('--build', choices=('null', 'asan'), default='null'); a = p.parse_args()
    run_probe(a.data.resolve(), (ROOT/'tools/probes/tour.inc').read_text(), 'scummverse_roaming',
              'SCUMMVERSE_TOUR_PASS', 'tour', PRELUDE, a.build, timeout=2400,
              extra_config=f'scummverse_worlds_path={a.worlds.resolve()}\n')
    # (With Monkey Island's places exported, what needs them is tried: a
    # place of another game chosen mid-tour, a door of one tapped while
    # paused, no tap kept after Stop or a load.)
    log = (ROOT/'build/tour-probe-True.log').read_text()
    if any(a.worlds.resolve().glob('monkey-*.svw')) and ('TOUR no monkey export' in log or 'TOUR a place chosen mid-tour' not in log
                                                         or 'none kept after Stop or a load' not in log):
        raise SystemExit('FAIL: tour: Monkey Island exported, its place and doors not tried mid-tour')
    print('PASS: tour')
