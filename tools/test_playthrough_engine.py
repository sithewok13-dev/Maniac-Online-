#!/usr/bin/env python3
"""Maniac Mansion played through to one of its endings, by the player's taps,
in the real engine (Linux, the null backend; not an iPhone test).

The probe (tools/probes/playthrough.inc, written into a temporary copy of
scumm.cpp as the other engine probes are) plays the original game as a player
does: each verb tapped on the screen, each thing tapped where a tap finds it
(the kid walking towards it until it shows), the things carried tapped in the
inventory, the kids changed with New Kid; the game's own scripts walk the kid
there and do it. Every step checks what the game did (an object's state, who
carries what, the room, a variable the game sets) and a failure names the
step. The route is in the probe, by room, object and actor number.
- Story mode (set as the app keeps it; Maniac Mansion's own story chosen from
  Story mode's list, as the desktop's builds choose, scummverse_story_choices):
  the kid screen (kids 2 and 5 with 3), the opening, and the ending where
  actor 15 takes actor 16 away (script 43) and the game is won (script 63):
  three kids, 18 steps. None of the mansion's additions may show (roaming,
  free doors, safety, visitors).
- Explore mode (the mansion as it starts: scummverse_roaming, the wanderers on,
  other games' visitors from the export cache): one kid takes the same things
  in the same rooms. What the sandbox replaces by design (docs/roaming.md: no
  opening, doors without keys or codes, lights on, no captures, countdowns or
  arcade game) is checked as it promises, and the ending is not reached; other
  games' visitors must be met in at least --visitor-rooms rooms (when the
  cache holds other games).
The two codes the game picks at random are read from its variables, where the
player reads them on the screen; --seed is the game's random seed (the route
holds for any). Game data, saves and the probe stay in a temporary folder
under build/; each mode's log is build/playthrough-<mode>.log.
"""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from test_exploration import ROOT, command_for
from test_ai_encounters import PRELUDE

BOUNDARY = '\n}\n\n#ifdef ENABLE_HE\nvoid ScummEngine_v90he::runBootscript()'
MANIAC_V1 = '7f45ddd6dbfbf8f80c0c0efea4c295bc'  # 00.LFL of the audited English DOS V1


def probe_binary(work, build_name):
    build = ROOT/'build'/build_name
    source = ROOT/'engine/engines/scumm/scumm.cpp'
    code = '#include "common/tokenizer.h"\n' + PRELUDE + source.read_text()
    if code.count(BOUNDARY) != 1:
        raise RuntimeError('Pinned runBootscript boundary changed')
    probe = work/'scumm.cpp'
    probe.write_text(code.replace(BOUNDARY, '\n' + (ROOT/'tools/probes/playthrough.inc').read_text() + BOUNDARY))
    cmd = command_for(build, source, 'engines/scumm/scumm.o')
    cmd[cmd.index(str(source))] = str(probe)
    cmd[cmd.index('-o')+1] = str(work/'scumm.o')
    cmd[cmd.index('-MF')+1] = str(work/'scumm.d')
    built = subprocess.run(cmd, cwd=build, capture_output=True, text=True)
    if built.returncode:
        raise SystemExit('FAIL: the playthrough probe does not compile\n' + built.stderr[-6000:])
    archive = work/'libscumm.a'
    shutil.copy2(build/'engines/scumm/libscumm.a', archive)
    subprocess.run(['ar', 'r', str(archive), str(work/'scumm.o')], check=True)
    cmd = command_for(build, 'engines/scumm/libscumm.a', 'scummvm')
    cmd[cmd.index('engines/scumm/libscumm.a')] = str(archive)
    exe = work/'scummvm-probe'
    cmd[cmd.index('-o')+1] = str(exe)
    subprocess.run(cmd, cwd=build, check=True)
    return exe


def play(exe, work, mode, a, visitor_rooms):
    run = work/mode
    (run/'worlds').mkdir(parents=True)
    # (Every game already set up: no export at the start.)
    for marker in a.worlds.glob('*.svx'):
        shutil.copy2(marker, run/'worlds'/marker.name)
    lines = ['[scummvm]', f'scummverse_playthrough={mode}', f'random_seed={a.seed}',
             f'scummverse_worlds_path={a.worlds.resolve()}']
    if mode == 'story':
        lines += ['scummverse_mode=story', 'scummverse_story_choices=maniac']
    else:
        lines += ['scummverse_roaming=true', 'scummverse_wanderers=true',
                  f'scummverse_playthrough_visitor_rooms={visitor_rooms}']
    if a.trace:
        lines.append('scummverse_playthrough_trace=1')
    config = run/'probe.ini'
    config.write_text('\n'.join(lines) + '\n')
    began = time.time()
    result = subprocess.run([str(exe), f'--config={config}', f'--path={a.data.resolve()}', f'--savepath={run}', '--debuglevel=1'],
                            cwd=run, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=a.timeout)
    took = time.time() - began
    output = result.stdout + result.stderr
    (ROOT/f'build/playthrough-{mode}.log').write_text(output)
    passed = [l for l in output.splitlines() if 'SCUMMVERSE_PLAYTHROUGH_PASS' in l]
    failed = [l for l in output.splitlines() if 'SCUMMVERSE_PLAYTHROUGH_FAIL' in l]
    # (Story mode: the app went back to the mansion afterwards, and stopped.)
    home = mode != 'story' or 'SCUMMVERSE_PLAYTHROUGH_HOME' in output
    if result.returncode or failed or not passed or not home:
        raise SystemExit(f'FAIL: playthrough ({mode}): ' + (failed[0] if failed else output[-6000:]))
    print(f'PASS: playthrough, {mode} mode, {took:.1f} s: ' + passed[0].split('SCUMMVERSE_PLAYTHROUGH_PASS ', 1)[1].rstrip('!'))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('data', type=Path, help='the audited Maniac Mansion DOS V1 folder')
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds', help='the export cache (other games\' visitors)')
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--visitor-rooms', type=int, default=5, help='rooms where Explore mode must meet visitors')
    p.add_argument('--modes', nargs='*', choices=('story', 'explore'), default=['story', 'explore'])
    p.add_argument('--timeout', type=int, default=900, help='seconds per mode')
    p.add_argument('--trace', action='store_true', help='log every script, room and tap (build/playthrough-*.log)')
    p.add_argument('--build', choices=('null', 'asan'), default='null')
    a = p.parse_args()
    if hashlib.md5((a.data/'00.LFL').read_bytes()).hexdigest() != MANIAC_V1:
        p.error('the route is the audited English DOS V1 edition\'s')
    # (Visitors come from other games' exports; Maniac's and Zak's people are
    # not visitors in the mansion.)
    others = [m for m in a.worlds.glob('*.svx') if not m.name.startswith(('maniac-', 'zak-'))]
    visitor_rooms = a.visitor_rooms if others else 0
    if not others:
        print(f'NOTE: no other games in {a.worlds}: Explore mode is played without visitors')
    with tempfile.TemporaryDirectory(prefix='scummverse-playthrough-', dir=ROOT/'build') as tmp:
        work = Path(tmp)
        exe = probe_binary(work, a.build)
        for mode in a.modes:
            play(exe, work, mode, a, visitor_rooms)
    print('PASS: playthrough (normal source, executable, game data and saves unchanged)')


if __name__ == '__main__':
    main()
