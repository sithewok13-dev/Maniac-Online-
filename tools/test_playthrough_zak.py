#!/usr/bin/env python3
"""Zak McKracken played through to its ending, by the player's taps, in the
real engine with all of SCUMMVERSE's changes (Linux, the null backend; not an
iPhone test).

The probe (tools/probes/playthrough_zak.inc, written into a temporary copy of
scumm.cpp as the other engine probes are) plays as a player does: each verb
tapped on the screen, each thing tapped where a tap finds it (the one played
walking towards it until it shows), carried things tapped in the inventory,
the one played changed with the game's own switch; the game's own scripts
walk there and do it. Every step checks what the game did (an object's state,
who carries what, the room, a variable the game sets) and a failure names the
step. The route is in the probe, by room, object, actor and script number,
worked out from the game's own data.
- Story mode (set as the app keeps it; Zak's own story chosen from Story
  mode's list, scummverse_story_choices, its folder beside the app's
  documents as the story test supplies it): the whole game, 59 steps, with
  all four played (actors 1 to 4), the flights booked and flown, the money,
  the capture and the way out, Mars and its air, to the ending (scripts 65,
  66 and 149). None of the mansion's additions may show (roaming, free doors,
  safety, visitors), and afterwards the app goes back to the mansion.
- Explore mode (the mansion as it starts: scummverse_roaming, the wanderers
  on, other games' visitors from the export cache): Zak chosen on the
  character screen, 17 steps through his places as the sandbox joins them
  (the bus, every flight it offers, seated aboard, the maze, the pads, Mars's
  rooms with and without air, the tram). What the sandbox replaces by design
  (docs/roaming.md: no fares, puzzles or endings) is not played; other games'
  visitors must be met in at least --visitor-rooms rooms (when the cache holds
  other games).
The orders the game picks at random are read from its variables, where the
player reads them on the screen; --seed is the game's random seed (the route
holds for any). Saves and the probe stay in a temporary folder under build/;
each mode's log is build/playthrough-zak-<mode>.log.
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
ZAK_V1 = '7020931d5a2be0a49d68e7a1882363e4'  # 00.LFL of the audited English DOS V1


def probe_binary(work, build_name):
    build = ROOT/'build'/build_name
    source = ROOT/'engine/engines/scumm/scumm.cpp'
    code = '#include "common/tokenizer.h"\n' + PRELUDE + source.read_text()
    if code.count(BOUNDARY) != 1:
        raise RuntimeError('Pinned runBootscript boundary changed')
    probe = work/'scumm.cpp'
    probe.write_text(code.replace(BOUNDARY, '\n' + (ROOT/'tools/probes/playthrough_zak.inc').read_text() + BOUNDARY))
    cmd = command_for(build, source, 'engines/scumm/scumm.o')
    cmd[cmd.index(str(source))] = str(probe)
    cmd[cmd.index('-o')+1] = str(work/'scumm.o')
    cmd[cmd.index('-MF')+1] = str(work/'scumm.d')
    built = subprocess.run(cmd, cwd=build, capture_output=True, text=True)
    if built.returncode:
        raise SystemExit('FAIL: the Zak playthrough probe does not compile\n' + built.stderr[-6000:])
    archive = work/'libscumm.a'
    shutil.copy2(build/'engines/scumm/libscumm.a', archive)
    subprocess.run(['ar', 'r', str(archive), str(work/'scumm.o')], check=True)
    cmd = command_for(build, 'engines/scumm/libscumm.a', 'scummvm')
    cmd[cmd.index('engines/scumm/libscumm.a')] = str(archive)
    exe = work/'scummvm-probe'
    cmd[cmd.index('-o')+1] = str(exe)
    subprocess.run(cmd, cwd=build, check=True)
    return exe


def fingerprint(folder):
    return {p.name: hashlib.md5(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir()) if p.is_file()}


def play(exe, work, mode, a, visitor_rooms):
    run = work/mode
    (run/'worlds').mkdir(parents=True)
    # (Every game already set up: no export at the start.)
    for marker in a.worlds.glob('*.svx'):
        shutil.copy2(marker, run/'worlds'/marker.name)
    # (Zak's folder where the app finds the games beside the mansion.)
    (run/'zak').symlink_to(a.zak.resolve())
    lines = ['[scummvm]', f'scummverse_playthrough_zak={mode}', f'random_seed={a.seed}',
             f'scummverse_worlds_path={a.worlds.resolve()}']
    if mode == 'story':
        lines += ['scummverse_mode=story', 'scummverse_story_choices=zak']
    else:
        lines += ['scummverse_roaming=true', 'scummverse_wanderers=true',
                  f'scummverse_playthrough_zak_visitor_rooms={visitor_rooms}']
    if a.trace:
        lines.append('scummverse_playthrough_zak_trace=1')
    config = run/'probe.ini'
    config.write_text('\n'.join(lines) + '\n')
    began = time.time()
    result = subprocess.run([str(exe), f'--config={config}', f'--path={a.data.resolve()}', f'--savepath={run}', '--debuglevel=1'],
                            cwd=run, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=a.timeout)
    took = time.time() - began
    output = result.stdout + result.stderr
    (ROOT/f'build/playthrough-zak-{mode}.log').write_text(output)
    passed = [l for l in output.splitlines() if 'SCUMMVERSE_PLAYTHROUGH_ZAK_PASS' in l]
    failed = [l for l in output.splitlines() if 'SCUMMVERSE_PLAYTHROUGH_ZAK_FAIL' in l]
    # (Story mode: the app went back to the mansion afterwards, and stopped.)
    home = mode != 'story' or 'SCUMMVERSE_PLAYTHROUGH_ZAK_HOME' in output
    if result.returncode or failed or not passed or not home:
        raise SystemExit(f'FAIL: Zak playthrough ({mode}): ' + (failed[0] if failed else output[-6000:]))
    print(f'PASS: Zak playthrough, {mode} mode, {took:.1f} s: ' + passed[0].split('SCUMMVERSE_PLAYTHROUGH_ZAK_PASS ', 1)[1].rstrip('!'))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('data', type=Path, help='the audited Maniac Mansion DOS V1 folder (the app\'s mansion)')
    p.add_argument('zak', type=Path, nargs='?', default=ROOT/'game-data/zak-dos', help='the audited Zak McKracken DOS V1 folder')
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds', help='the export cache (other games\' visitors)')
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--visitor-rooms', type=int, default=5, help='rooms where Explore mode must meet visitors')
    p.add_argument('--modes', nargs='*', choices=('story', 'explore'), default=['story', 'explore'])
    p.add_argument('--timeout', type=int, default=900, help='seconds per mode')
    p.add_argument('--trace', action='store_true', help='log every script, room and tap (build/playthrough-zak-*.log)')
    p.add_argument('--build', choices=('null', 'asan'), default='null')
    a = p.parse_args()
    if hashlib.md5((a.data/'00.LFL').read_bytes()).hexdigest() != MANIAC_V1:
        p.error('the mansion must be the audited English DOS V1 edition')
    if not (a.zak/'00.LFL').is_file():
        print(f'SKIP: Zak playthrough: no Zak McKracken data in {a.zak}')
        return
    if hashlib.md5((a.zak/'00.LFL').read_bytes()).hexdigest() != ZAK_V1:
        p.error('the route is the audited English DOS V1 edition\'s of Zak McKracken')
    # (Visitors come from other games' exports; Maniac's and Zak's people are
    # not visitors in the mansion.)
    others = [m for m in a.worlds.glob('*.svx') if not m.name.startswith(('maniac-', 'zak-'))]
    visitor_rooms = a.visitor_rooms if others else 0
    if not others:
        print(f'NOTE: no other games in {a.worlds}: Explore mode is played without visitors')
    before = fingerprint(a.zak), fingerprint(a.data)
    with tempfile.TemporaryDirectory(prefix='scummverse-playthrough-zak-', dir=ROOT/'build') as tmp:
        work = Path(tmp)
        exe = probe_binary(work, a.build)
        for mode in a.modes:
            play(exe, work, mode, a, visitor_rooms)
    if (fingerprint(a.zak), fingerprint(a.data)) != before:
        raise SystemExit('FAIL: Zak playthrough: the game data changed')
    print('PASS: Zak playthrough (normal source, executable, game data and saves unchanged)')


if __name__ == '__main__':
    main()
