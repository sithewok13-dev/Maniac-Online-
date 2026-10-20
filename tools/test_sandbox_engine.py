#!/usr/bin/env python3
"""The sandbox engine (engines/scummverse) through the real executable.

Needs an export cache (build/worlds, see tools/export_worlds.py) and, for the
switch, privately supplied Maniac Mansion data. The first place is shown at
1280x720 in true colour and its lead walks across by taps; every place
installed is shown with its people, each lead walking as far as the walk
boxes go; every door of every place is tapped, walked to and gone through
(at least 95 in 100 reach their place: the rest need the games' own box
connections, not exported yet); everyone is out for half an hour, those
coming in are shown, and where everyone is is kept; each game's own verb
panel (Monkey Island 1 and 2, Indiana Jones 3 and 4, Day of the Tentacle)
is shown under its first place, every verb chosen and used on the things
there (and on their other places' for pushing and picking up, by what each
thing's own script answers), what was taken kept; the things are where
their games put them; then from Maniac the
Worlds menu's New engine (preview) opens the sandbox and its Back to Maniac
Mansion returns to the same room, from the saved game. Pictures go to
build/sandbox-shots. Not an iPhone test.
"""
import argparse
import gzip
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
from test_exploration import ROOT, command_for

# Test-only: at the top of Maniac's main loop. Once the game has run a while,
# the menu's New engine (preview); back from the sandbox (loaded from the
# temporary save), where Maniac is, then stop.
SWITCH = r'''
		if (ConfMan.hasKey("scummverse_switch_probe")) {
			static int scummverseSwitchFrames = 0;
			if (ConfMan.hasKey("save_slot") && ConfMan.getInt("save_slot") == 100) {
				warning("SCUMMVERSE_SWITCH_BACK room=%d ego=%d", _currentRoom, VAR(VAR_EGO));
				quitGame();
			} else if (++scummverseSwitchFrames == ConfMan.getInt("scummverse_switch_probe")) {
				warning("SCUMMVERSE_SWITCH_OPEN room=%d ego=%d", _currentRoom, VAR(VAR_EGO));
				scummverseOpenSandbox();
			}
		}
'''
LOOP = '\twhile (!shouldQuit()) {\n\t\t// Determine how long to wait before the next loop iteration should start\n'


def sandbox(exe, worlds, mode, shots, cwd, timeout=900, wanderers=False):
    # (Wanderers off: each place's own people, the same every run.)
    config = Path(cwd)/f'sandbox-{mode}.ini'
    config.write_text(f'[scummvm]\nscummverse_selftest={mode}\nscummverse_shots={shots}\nscummverse_screen=1280x720\n'
                      f'scummverse_wanderers={str(wanderers).lower()}\n')
    result = subprocess.run([str(exe), f'--config={config}', f'--path={worlds}', f'--savepath={cwd}', 'scummverse:sandbox'], cwd=cwd,
                            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
    output = result.stdout + result.stderr
    (ROOT/f'build/sandbox-{mode}.log').write_text(output)
    summary = [line for line in output.splitlines() if 'sandbox selftest' in line or 'sandbox walk' in line or 'sandbox verbs' in line]
    if result.returncode or 'SCUMMVERSE sandbox selftest PASS' not in output:
        raise SystemExit(f'FAIL: sandbox {mode}\n' + output[-4000:])
    for line in summary:
        print('  ' + line.replace('WARNING: ', '').rstrip('!'))
    return output


def cycles_of(path):
    """A scene file's colour cycles (delay, first, last, mode); None before SVW5."""
    data = path.read_bytes()
    if data[:2] == b'\x1f\x8b':  # (the cache keeps them compressed)
        data = gzip.decompress(data)
    if data[:4] != b'SVW5':
        return None
    width, height, boxes = struct.unpack_from('<HH', data, 6) + (data[10],)
    p = 12 + 768 + width * height + boxes * 18
    objects = struct.unpack_from('<H', data, p)[0]
    p += 2 + objects * 16 + boxes * 2 + boxes * boxes
    return [struct.unpack_from('<HBBB', data, p + 1 + i * 5) for i in range(data[p])]


def things_of(path):
    """A things file: {room: {object: (picture, answers)}}."""
    data = path.read_bytes()
    if data[:2] == b'\x1f\x8b':
        data = gzip.decompress(data)
    if data[:4] != b'SVO1':
        raise SystemExit(f'FAIL: {path.name}: not a things file')
    rooms, p, found = struct.unpack_from('<H', data, 4)[0], 6, {}
    for _ in range(rooms):
        room, count = struct.unpack_from('<HH', data, p)
        p += 4
        found[room] = {}
        for _ in range(count):
            obj, picture, answers = struct.unpack_from('<HBH', data, p)
            found[room][obj] = (picture, answers)
            p += 5
    if p != len(data):
        raise SystemExit(f'FAIL: {path.name}: {len(data) - p} bytes left over')
    return found


# What a verb is in a things file's answers (WorldVerbKind), and its two
# other bits: a catch-all entry, untouchable or carried there.
LOOK, PICK_UP, OPEN, CLOSE, TALK = 2, 3, 4, 5, 10
ANY, AWAY = 1 << 14, 1 << 15


def check_things(worlds):
    # As the SCUMM Bar's own scripts answer (Monkey Island, room 28): a
    # pirate is talked to, not taken; the kitchen door opens; a mug is taken
    # once its game puts one out (at its start none is: untouchable, unseen).
    path = worlds/'monkey-things.svo'
    if not path.exists():
        return None
    bar = things_of(path).get(28, {})
    expect = {341: ([LOOK, TALK], [PICK_UP], False), 322: ([OPEN, CLOSE], [PICK_UP], False), 373: ([PICK_UP], [], True)}
    for obj, (has, lacks, away) in expect.items():
        if obj not in bar:
            raise SystemExit(f'FAIL: monkey room 28: object {obj} not listed')
        answers = bar[obj][1]
        if any(not answers & 1 << k for k in has) or any(answers & 1 << k for k in lacks) or bool(answers & AWAY) != away:
            raise SystemExit(f'FAIL: monkey room 28: object {obj} answers {answers:#06x}')
    return len(bar)


def check_cycles(worlds):
    # As exported: at least a frame (4 ticks) a step, in range, a known mode.
    places = cycling = 0
    for path in sorted(worlds.glob('*.svw')):
        found = cycles_of(path)
        if found is None:
            continue
        places += 1
        cycling += bool(found)
        for delay, first, last, mode in found:
            if delay < 4 or first >= last or mode > 2:
                raise SystemExit(f'FAIL: {path.name}: colour cycle delay {delay}, {first}..{last}, mode {mode}')
    return places, cycling


def switch(data, worlds, frames, broken=False):
    build = ROOT/'build/null'
    source = ROOT/'engine/engines/scumm/scumm.cpp'
    with tempfile.TemporaryDirectory(prefix='scummverse-switch-', dir=ROOT/'build') as tmp:
        work = Path(tmp)
        code = source.read_text()
        if code.count(LOOP) != 1:
            raise RuntimeError('Pinned main loop boundary changed')
        probe = work/'scumm.cpp'
        probe.write_text(code.replace(LOOP, LOOP.split('\n')[0] + '\n' + SWITCH + '\n'.join(LOOP.split('\n')[1:])))
        cmd = command_for(build, source, 'engines/scumm/scumm.o')
        cmd[cmd.index(str(source))] = str(probe)
        cmd[cmd.index('-o')+1] = str(work/'scumm.o')
        cmd[cmd.index('-MF')+1] = str(work/'scumm.d')
        subprocess.run(cmd, cwd=build, check=True)
        archive = work/'libscumm.a'
        shutil.copy2(build/'engines/scumm/libscumm.a', archive)
        subprocess.run(['ar', 'r', str(archive), str(work/'scumm.o')], check=True)
        cmd = command_for(build, 'engines/scumm/libscumm.a', 'scummvm')
        cmd[cmd.index('engines/scumm/libscumm.a')] = str(archive)
        exe = work/'scummvm-probe'
        cmd[cmd.index('-o')+1] = str(exe)
        subprocess.run(cmd, cwd=build, check=True)
        config = work/'switch.ini'
        # (Roaming off: no character offer waiting for a tap at the start.)
        config.write_text('[scummvm]\nscummverse_roaming=false\nscummverse_wanderers=false\n'
                          f'scummverse_switch_probe={frames}\nscummverse_worlds_path={worlds}\nscummverse_selftest=back\n')
        result = subprocess.run([str(exe), f'--config={config}', f'--path={data}', f'--savepath={work}', '--debuglevel=1'],
                                cwd=work, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=600)
        output = result.stdout + result.stderr
        (ROOT/'build/sandbox-switch.log').write_text(output)
        lines = output.splitlines()
        opened = [l for l in lines if 'SCUMMVERSE_SWITCH_OPEN' in l]
        back = [l for l in lines if 'SCUMMVERSE_SWITCH_BACK' in l]
        # A sandbox that works leaves by the menu's way back; one that cannot
        # start goes back to Maniac on its own.
        sandbox_line = 'SCUMMVERSE: could not start the sandbox' if broken else 'SCUMMVERSE sandbox back: leaving'
        ran = [l for l in lines if sandbox_line in l]
        if result.returncode or len(opened) != 1 or len(back) != 1 or len(ran) != 1:
            raise SystemExit('FAIL: switch\n' + output[-6000:])
        # In order (the log's two streams each in order: ScummVM's own lines,
        # then the warnings): opened, the sandbox ran and left, back in
        # Maniac; Maniac saved, the sandbox started, the same save loaded.
        def first(text):
            return next((i for i, l in enumerate(lines) if text in l), -1)
        said = [first('SCUMMVERSE_SWITCH_OPEN'), first(sandbox_line), first('SCUMMVERSE_SWITCH_BACK')]
        logged = [first('State saved as'), first('Running Scummverse sandbox'), first('State loaded from')]
        saved = lines[logged[0]].split("'")[1] if logged[0] >= 0 else None
        loaded = lines[logged[2]].split("'")[1] if logged[2] >= 0 else None
        if -1 in said + logged or said != sorted(said) or logged != sorted(logged) or saved != loaded:
            raise SystemExit(f'FAIL: switch out of order {said} {logged} (saved {saved}, loaded {loaded})\n' + output[-6000:])
        where = opened[0].split('SCUMMVERSE_SWITCH_OPEN ')[1].rstrip('!')
        again = back[0].split('SCUMMVERSE_SWITCH_BACK ')[1].rstrip('!')
        if where != again:
            raise SystemExit(f'FAIL: switch: left Maniac at {where}, came back at {again}')
        print(f'PASS: Maniac -> new engine{" (broken)" if broken else ""} -> Maniac, back where it was ({where}, from {saved})')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('data', type=Path)
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds')
    p.add_argument('--frames', type=int, default=600, help="Maniac's frames before the switch")
    a = p.parse_args()
    worlds = a.worlds.resolve()
    if not list(worlds.glob('*.svw')):
        print(f'SKIP: no exported places in {worlds} (run tools/export_worlds.py)')
        raise SystemExit(0)
    exe = ROOT/'build/null/scummvm'
    shots = ROOT/'build/sandbox-shots'
    shots.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='scummverse-sandbox-', dir=ROOT/'build') as tmp:
        sandbox(exe, worlds, 'walk', shots, tmp)
        print('PASS: the first place at 1280x720 in true colour; its lead walks across')
        output = sandbox(exe, worlds, 'all', shots, tmp)
        print('PASS: every place installed, its people shown, each lead walking')
        # Objects named and pictured, colours moving where the files have them.
        objects, named, pictured, moving = map(int, re.search(
            r'all objects: (\d+), (\d+) named, (\d+) with pictures; (\d+) places with colours moving', output).groups())
        places, cycling = check_cycles(worlds)
        if places and (not named or not pictured or (cycling and not moving) or moving > cycling):
            raise SystemExit(f'FAIL: objects {objects}, {named} named, {pictured} pictured; {moving} places moving of {cycling} with cycles')
        print(f'PASS: {named} of {objects} objects named, {pictured} with pictures; colours moving in {moving} of {cycling} places with cycles')
        # Things where their games put them (from each game's own start and
        # each room's entry script), where those were exported.
        placed, placedPlaces = map(int, re.search(r'all things: (\d+) where their games put them, in (\d+) places', output).groups())
        if [f for f in worlds.glob('*-things.svo') if f.stat().st_size] and not placed:
            raise SystemExit('FAIL: no things where their games put them')
        print(f'PASS: {placed} things where their games put them, in {placedPlaces} places')
        bar = check_things(worlds)
        if bar is not None:
            print(f'PASS: the SCUMM Bar as its scripts answer ({bar} objects: a pirate talked to, not taken; a door opened; no mug out yet)')
        sandbox(exe, worlds, 'doors', shots, tmp)
        print('PASS: through the doors of every place (tapped, walked to, gone through)')
        sandbox(exe, worlds, 'wander', shots, tmp, wanderers=True)
        print('PASS: everyone out; those coming in shown; where everyone is kept')
        # Each game's own verb panel (exported from its start): every verb
        # chosen, used on the things there, kept.
        output = sandbox(exe, worlds, 'verbs', shots, tmp)
        panels = int(re.search(r'selftest verbs: (\d+) panels', output).group(1))
        exported = len([f for f in worlds.glob('*-ui.svi') if f.stat().st_size])  # (an emptied one is none)
        if panels != exported:
            raise SystemExit(f'FAIL: {panels} verb panels shown of {exported} exported')
        print(f'PASS: {panels} games\' own verb panels: each verb chosen; look, open, close, push, pick up; kept')
    switch(a.data.resolve(), worlds, a.frames)
    # A cache whose place cannot be read: back to Maniac all the same.
    with tempfile.TemporaryDirectory(prefix='scummverse-broken-', dir=ROOT/'build') as broken:
        (Path(broken)/'monkey-33.svw').write_bytes(b'SVW3 not a scene')
        switch(a.data.resolve(), Path(broken), a.frames, broken=True)
    print('PASS: sandbox engine')
