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
panel (Monkey Island 1 and 2, Indiana Jones 3 and 4, Day of the Tentacle,
the mansion, Zak McKracken; Sam & Max's box over the scene, opened from its
button, its pointer brought round by right clicks; The Dig's grid from its
button, its one tap doing what fits; Full Throttle's coin, held over a thing
and let go on a part, and its skull of things from a right click; Loom's
distaff, its notes lit, its Opening draft spun forwards and backwards)
is shown under its first place, every verb chosen and used on the things
there (and on their other places' for pushing and picking up, by what each
thing's own script answers), what was taken kept; the things are where
their games put them; the mansion's and Zak's people are in their colours;
the iPhone's chat (a stand-in for it) is told who is there, those in a
conversation stand facing the one played, each line is said over its
speaker's head, and a tap picks someone when the chat asks whom; someone
asked along by it follows the one played, through doors too, until asked
to stay or someone else is played; its character screen (a stand-in) gets a box per game with its lead's face and
people, and each game's lead and another are played where they live, and a
last box of custom characters (Crispy first, played where the player is); its
camera takes a photo of the scene and of the screen and a selfie of three
(everyone posed, nobody moving), and holds still while asked; its tour
visits every place installed, most on foot through doors, its controls
working, and ends back where it began; The Dig's tram is called from
each ledge, comes, and is ridden to the other end, where it waits; Zak's
bus and Mars tram are boarded and ridden both ways, a plane flies to every
airport chosen from the list it asks with, and a ride walked off is missed;
then from Maniac the
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
			static int scummverseSwitchFrames = 0, scummverseStoryFrames = 0;
			if (_scummverseStory) {
				// (Maniac's own story, opened from the sandbox: a while, then
				// ScummVM's menu's way out, home to the mansion.)
				if (++scummverseStoryFrames == 120) {
					warning("SCUMMVERSE_SWITCH_STORY %s additions=%d room=%d", _targetName.c_str(),
						_scummverseRoaming + _scummverseExplorationDoors + _scummverseExplorationSafety + _scummverseAuditedManiac, _currentRoom);
					Common::Event event;
					event.type = Common::EVENT_RETURN_TO_LAUNCHER;
					_system->getEventManager()->pushEvent(event);
				}
			} else if (ConfMan.hasKey("save_slot") && ConfMan.getInt("save_slot") == 100) {
				warning("SCUMMVERSE_SWITCH_BACK room=%d ego=%d", _currentRoom, VAR(VAR_EGO));
				quitGame();
			} else if (++scummverseSwitchFrames == ConfMan.getInt("scummverse_switch_probe")) {
				warning("SCUMMVERSE_SWITCH_OPEN room=%d ego=%d", _currentRoom, VAR(VAR_EGO));
				scummverseOpenSandbox();
			}
		}
'''
LOOP = '\twhile (!shouldQuit()) {\n\t\t// Determine how long to wait before the next loop iteration should start\n'


def sandbox(exe, worlds, mode, shots, cwd, timeout=900, wanderers=False, extra=''):
    # (Wanderers off: each place's own people, the same every run.)
    config = Path(cwd)/f'sandbox-{mode}.ini'
    config.write_text(f'[scummvm]\nscummverse_selftest={mode}\nscummverse_shots={shots}\nscummverse_screen=1280x720\n'
                      f'scummverse_wanderers={str(wanderers).lower()}\n{extra}')
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
    """A things file: {room: {object: (picture, answers)}} ("SVO1"; from
    export version 23 "SVO3" with no effects, then what each is inside)."""
    data = path.read_bytes()
    if data[:2] == b'\x1f\x8b':
        data = gzip.decompress(data)
    if data[:4] not in (b'SVO1', b'SVO3'):
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
    if data[:4] == b'SVO3':
        effects, parents = struct.unpack_from('<HH', data, p)
        if effects:
            raise SystemExit(f'FAIL: {path.name}: what its things do, outside the mansion')
        p += 4 + parents * 7
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


def colours_of(path):
    """A character file's colours drawn (palette indices), over all its frames."""
    data = path.read_bytes()
    if data[:4] != b'SVC1':
        raise SystemExit(f'FAIL: {path.name}: not a character file')
    frames, p, used = struct.unpack_from('<H', data, 6)[0], 8 + 768, set()
    for _ in range(frames):
        width, height = struct.unpack_from('<HH', data, p + 8)
        p += 12
        pixels, mask = data[p:p + width * height], data[p + width * height:p + 2 * width * height]
        used.update(c for c, m in zip(pixels, mask) if m)
        p += 2 * width * height
    return used


def check_lit_people(worlds):
    # The oldest games draw everyone in one grey (8, and black) while the
    # lights say not to colour them: none of their people exported so.
    people = 0
    for game in ('maniac', 'zak'):
        for path in sorted(worlds.glob(f'{game}-c*.svc')):
            people += 1
            if colours_of(path) <= {0, 8}:
                raise SystemExit(f'FAIL: {path.name}: in grey only (as with the lights off)')
    return people


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


def switch(data, worlds, frames, broken=False, story=False):
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
                          f'scummverse_switch_probe={frames}\nscummverse_worlds_path={worlds}\nscummverse_selftest={"story" if story else "back"}\n'
                          # (Story mode's list: Maniac's own story, then nothing chosen: Explore.)
                          + ('scummverse_story_choices=maniac\n' if story else ''))
        result = subprocess.run([str(exe), f'--config={config}', f'--path={data}', f'--savepath={work}', '--debuglevel=1'],
                                cwd=work, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=600)
        output = result.stdout + result.stderr
        (ROOT/'build/sandbox-switch.log').write_text(output)
        lines = output.splitlines()
        opened = [l for l in lines if 'SCUMMVERSE_SWITCH_OPEN' in l]
        back = [l for l in lines if 'SCUMMVERSE_SWITCH_BACK' in l]
        # A sandbox that works leaves by the menu's way back; one that cannot
        # start goes back to Maniac on its own.
        sandbox_line = 'SCUMMVERSE: could not start the sandbox' if broken else 'SCUMMVERSE sandbox story: leaving' if story else 'SCUMMVERSE sandbox back: leaving'
        ran = [l for l in lines if sandbox_line in l]
        if result.returncode or len(opened) != 1 or len(back) != 1 or len(ran) != 1:
            raise SystemExit('FAIL: switch\n' + output[-6000:])
        if story:
            # The sandbox's Story mode: its list (Maniac's own story chosen;
            # none of the mansion's additions), left by ScummVM's menu, saved
            # on the way out; the list again (nothing chosen: Explore mode),
            # the mansion where it was.
            told = [l for l in lines if 'SCUMMVERSE_SWITCH_STORY' in l]
            if len(told) != 1 or 'scummverse-story-maniac additions=0 ' not in told[0] or \
                    not any('scummverse-story-maniac saved on quitting' in l for l in lines) or \
                    not any('SCUMMVERSE: Story mode: scummverse-story-maniac' in l for l in lines) or \
                    not any('SCUMMVERSE: Explore mode' in l for l in lines):
                raise SystemExit('FAIL: switch: the sandbox did not open Maniac\'s own story\n' + output[-6000:])
            where = opened[0].split('SCUMMVERSE_SWITCH_OPEN ')[1].rstrip('!')
            again = back[0].split('SCUMMVERSE_SWITCH_BACK ')[1].rstrip('!')
            if where != again:
                raise SystemExit(f'FAIL: switch: left Maniac at {where}, came back at {again}')
            print(f'PASS: Maniac -> new engine -> Story mode (its list: Maniac\'s own story) -> Explore mode: Maniac, back where it was ({where})')
            return
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
        lit = check_lit_people(worlds)
        if lit:
            print(f"PASS: the mansion's and Zak's {lit} people in their colours (not the lights-off grey)")
        # (A door in a part of the place the game joins by a script is gone
        # through from as near as the walk boxes allow; The Dig's tram cars are
        # called, not gone through: the rides check.)
        output = sandbox(exe, worlds, 'doors', shots, tmp)
        d = re.search(r'selftest doors: (\d+) tried, (\d+) through .*?(\d+) elsewhere, (\d+) short.*?(\d+) with no spot a tap finds them, (\d+) from as near', output)
        # (Some doors only from as near as the walk allows, not most; from 0194
        # every door a tap finds walked to: one in a hundred short at most.)
        # (From 0204 none elsewhere: each door to its own place.)
        if not d or (int(d.group(2)) + int(d.group(3))) * 100 < int(d.group(1)) * 99 or not 0 < int(d.group(6)) * 10 < int(d.group(1)) \
                or int(d.group(4)) * 100 > int(d.group(1)) or d.group(3) != '0':
            raise SystemExit('FAIL: doors\n' + output[-2000:])
        # (The mansion's doors open as one goes through, where its game opens
        # them; the door back stands open.)
        o = re.search(r'selftest doors opening: (\d+) of (\d+) seen opening, (\d+) of (\d+) left open behind, (\d+) of (\d+) doors back open on arrival, (\d+) of (\d+) the game', output)
        if (worlds/'maniac-1.svw').exists() and (not o or int(o.group(2)) == 0 or int(o.group(6)) == 0 or o.group(1) != o.group(2) or o.group(3) != o.group(4)
                                                 or o.group(5) != o.group(6) or o.group(7) != o.group(8)):
            raise SystemExit('FAIL: doors opening\n' + output[-2000:])
        if o:
            print(f'PASS: the mansion\'s doors, each from as the game leaves it: {o.group(1)} seen opening as gone through and left open, '
                  f'{o.group(5)} doors back open on arrival, {o.group(7)} the game does not open left as they were')
        print(f'PASS: through the doors of every place (tapped where a tap finds them, walked to, gone through): {d.group(2)} of {d.group(1)} through, '
              f'{d.group(3)} elsewhere, {d.group(4)} short ({d.group(6)} from as near as the walk boxes allow); {d.group(5)} with no spot of their own')
        # (From 0202) A place with no way on (its game leaves it by a script):
        # a tap at its edge back the way they came, every time. (From 0204 any
        # place with no way back to where they came from, however far in: from
        # a place further in too, back to the door first come through.)
        b = re.search(r'doors with no way on: (\d+) arrived at, (\d+) back by a tap on the arrow at the left \((\d+) of (\d+) from a place further in\)', output)
        if not b or b.group(1) != b.group(2) or b.group(3) != b.group(4) or (int(b.group(1)) > 8 and b.group(4) == '0'):
            raise SystemExit('FAIL: no way back from a place with no way on\n' + output[-2000:])
        print(f'PASS: {b.group(1)} arrivals at places with no way back, each back the way they came by a tap on the arrow drawn at the left (a tap at the other edge walks); {b.group(3)} of them from a place further in')
        # (From 0202) The other games' switched doors (Monkey Island's, Indy 3's):
        # gone through open, the door back open too.
        sw = re.search(r'doors switched: (\d+) gone through open, (\d+) with the door back open', output)
        if not sw or sw.group(1) != sw.group(2) or ((worlds/'monkey-25.svw').exists() and sw.group(1) == '0'):
            raise SystemExit('FAIL: switched doors back\n' + output[-2000:])
        print(f'PASS: {sw.group(1)} switched doors gone through open, the door back open too')
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
        # (From 0202) The mansion's: a verb chosen on the way to a door, the walk goes on through it.
        w = re.search(r'(\d+) doors gone through with a verb chosen on the way', output)
        if (worlds/'maniac-ui.svi').exists() and (not w or w.group(1) != '1'):
            raise SystemExit('FAIL: a verb chosen on the way to a door\n' + output[-2000:])
        # (From 0203) The mansion's padlocked door: both padlocks unlocked with
        # the key from the pit, opened, gone through (tools/test_mansion_locks.py
        # checks the original does so).
        pl = re.search(r'(\d+) padlocked doors opened', output)
        if (worlds/'maniac-4.svw').exists() and (worlds/'maniac-31.svw').exists() and (not pl or pl.group(1) != '1'):
            raise SystemExit('FAIL: the padlocked door\n' + output[-2000:])
        # (Full Throttle's coin: each a file of its own kind, each held, lit and let go.)
        coins = len([f for f in worlds.glob('*-ui.svi') if f.stat().st_size and gzip.decompress(f.read_bytes())[:4] == b'SVI3'])
        held = int(re.search(r'(\d+) coins', output).group(1))
        if held != coins:
            raise SystemExit(f'FAIL: {held} coins held of {coins} exported')
        if coins:
            print(f'PASS: {coins} coin held over a thing, each part lit, let go off them; its box from a right click')
        # (Loom's distaff: each its own kind of file, its drafts spun.)
        distaffs = len([f for f in worlds.glob('*-ui.svi') if f.stat().st_size and gzip.decompress(f.read_bytes())[:4] == b'SVI4'])
        spun = int(re.search(r'(\d+) distaffs', output).group(1))
        if spun != distaffs:
            raise SystemExit(f'FAIL: {spun} distaffs played of {distaffs} exported')
        if distaffs:
            print(f'PASS: {distaffs} distaff: each note lit; its drafts spun (Opening forwards and backwards); notes that are no draft do nothing')
        # (The mansion's lights: each off, the place dark, kept; on again.)
        lights = re.search(r'(\d+) lights off and (\d+) on again \((\d+) flashlight, (\d+) pool, (\d+) links\)', output)
        if (worlds/'maniac-1.svw').exists() and (not lights or int(lights.group(1)) < 5 or lights.group(1) != lights.group(2) or lights.group(3) != '1' or lights.group(4) != '1' or lights.group(5) != '4'):
            raise SystemExit('FAIL: the mansion\'s lights\n' + output[-2000:])
        # (From 0195: the circuit breakers off, where the mansion's own room
        # scripts leave it dark then, dark; on again, lit.)
        power = re.search(r'the main power off in (\d+) places and on again', output)
        if (worlds/'maniac-1.svw').exists() and (not power or int(power.group(1)) < 25):
            raise SystemExit('FAIL: the mansion\'s main power\n' + output[-2000:])
        if power and int(power.group(1)):
            print(f'PASS: the mansion\'s main power: the fuse box opened, the circuit breakers off, {power.group(1)} places dark as its own scripts leave them (a lamp turned on there dark still), the rest lit; on again, all lit')
        if lights and int(lights.group(1)):
            print(f'PASS: the mansion\'s lights: {lights.group(1)} turned off (the place dark, everyone in grey; again so on coming back, only there; kept) and on again; the flashlight lighting a window where the tap was; the water valve draining and filling the pool, its ladder down only when drained; the gargoyle opening the hall\'s secret door (no handle; shut, going nowhere, nor with a tour paused; shut behind on the stairs down); the mailbox and the desk opened and closed; the shower curtain drawn aside and back as one (pushed, it won\'t budge), the sink and the tap as the game; the garden gate moving as one')
        # (From 0170: Use, a thing carried, a thing here: two things, in each
        # game with the panel under the scene.)
        pairs = re.search(r'selftest pairs: (\d+) games used a thing carried with a thing here; (\d+) of the mansion\'s own as its scripts answer \((\d+) not tried; (\d+) as found\); (\d+) gave one to someone', output)
        if not pairs or int(pairs.group(1)) < 5 or ((worlds/'maniac-1.svw').exists() and (int(pairs.group(2)) < 95 or pairs.group(4) != '3')) or int(pairs.group(5)) < 1:
            raise SystemExit('FAIL: two things (Use, a thing carried, a thing here; the mansion\'s own)\n' + output[-2000:])
        # (From 0207) Someone in front of what is behind them: looked at, them;
        # a coin let go where it opened, unmoved, nothing done; Loom's draft
        # after a stray note spun still.
        lp = re.search(r'gave one to someone \((\d+) looked at them, not what is behind\)', output)
        ui = re.search(r'selftest interface: (\d+) coins let go unmoved where they opened, nothing done; (\d+) drafts spun after a stray note', output)
        if not lp or lp.group(1) != pairs.group(5) or not ui or ui.group(1) != str(coins) or ui.group(2) != str(distaffs):
            raise SystemExit('FAIL: someone in front, a coin let go unmoved, a draft after a stray note\n' + output[-2000:])
        print(f'PASS: someone in front looked at, them ({lp.group(1)}); {ui.group(1)} coins let go unmoved where they opened, nothing done (a part lit only once the finger moves); {ui.group(2)} Loom drafts spun after a stray note')
        print(f'PASS: two things: in {pairs.group(1)} games Use, a thing carried ("Use it with", the verb still lit), then a thing here (walked to, the plain answer); a tap on the floor lets go; {pairs.group(2)} of the mansion\'s own answers (Use, Unlock, Fix with a thing carried) as its scripts give them ({pairs.group(3)} not tried); as found, from the picture the place shows: the paint remover on the blotch, the trunk\'s key, the coin box\'s key ({pairs.group(4)}); given to someone here, walked up to, they answer ({pairs.group(5)} games)')
        # (From 0155: the mansion's things as their own scripts answer, from
        # its things file: every use replayed as a player does it; from 0161
        # read, picked up and fixed too, some taken.)
        effects = re.search(r"selftest effects: (\d+) as the mansion's own scripts answer \((\d+) away, (\d+) taken, (\d+) read carried, (\d+) left to the plain rules; (\d+) inside others; (\d+) taken whose pictures are the same\)", output)
        # (From 0203 the garage's two (room 16, their export's pictures the
        # same) are taken as their game gives them; from export version 23
        # their pictures leave out the garage door over them: none the same.)
        # (From 0204 nearer what the mansion gives: 849 answered, 74 away, 63
        # to the plain rules when pinned.)
        if (worlds/'maniac-1.svw').exists() and (not effects or int(effects.group(1)) < 840 or int(effects.group(2)) > 80 or int(effects.group(3)) < 35 or int(effects.group(4)) < 3
                                                 or int(effects.group(5)) > 70 or effects.group(6) != '4'
                                                 or ((worlds/'maniac-16.svw').exists() and effects.group(7) != '0')):
            raise SystemExit('FAIL: the mansion\'s things as their own scripts answer (export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
        if effects:
            print(f"PASS: {effects.group(1)} uses of the mansion's things as their own scripts answer them (the line, the picture after, the others it sets; {effects.group(3)} of them taken, {effects.group(4)} of those read as carried; {effects.group(2)} out of reach or in a picture the game never has, {effects.group(5)} left to the plain rules: silent, or taken where not there or with no picture of its own; {effects.group(7)} taken whose pictures are the same); the fridge's food and the key under the mat inside them: untouched while shut, taken once open, gone when opened again")
        # The iPhone's chat (a stand-in for it: the desktop has none), in a
        # place of each game with someone there.
        output = sandbox(exe, worlds, 'talk', shots, tmp)
        places = int(re.search(r'selftest talk: (\d+) places', output).group(1))
        games = {f.name.split('-')[0] for f in worlds.glob('*.svw')}
        if places < 2 or places < len(games):
            raise SystemExit(f'FAIL: chat tried in {places} places ({len(games)} games)')
        # (The mansion's rooms go to the chat by their own numbers.)
        if any(worlds.glob('maniac-*.svw')) and "Maniac's rooms seen" not in output:
            raise SystemExit('FAIL: chat not tried in the mansion')
        # (The mansion's and Zak's people speak in their own colours.)
        c = re.search(r'(\d+) in their speakers\' own colours', output)
        if any(worlds.glob('maniac-*.svw')) and (not c or int(c.group(1)) == 0):
            raise SystemExit('FAIL: lines not in their speakers\' own colours\n' + output[-2000:])
        print(f'PASS: chat in {places} places: told who is here; those talking stand and face; lines over their speakers; a tap picks someone')
        # Followers (the chat's Follow, a stand-in): asked along, walking after
        # the one played, through a door beside them, the chat told, kept,
        # staying when asked, let go when someone else is played; with the
        # wanderers off and on.
        output = sandbox(exe, worlds, 'follow', shots, tmp)
        m = re.search(r'selftest follow: (\d+) asked along, (\d+) walked after \((\d+) while talking\), (\d+) through a door, (\d+) told the chat, (\d+) kept, (\d+) stayed, (\d+) let go, (\d+) failed', output)
        if not m or m.group(9) != '0' or any(m.group(i) != '2' for i in (1, 4, 5, 6, 7, 8)) or m.group(2) == '0' or m.group(3) == '0':
            raise SystemExit('FAIL: followers\n' + output[-2000:])
        print(f'PASS: followers (the chat\'s Follow): asked along, walking after the one played (talking too), through a door beside them, the chat told, kept, staying when asked, let go when someone else is played; wanderers off and on')
        # The character screen (a stand-in for the iPhone's): a box per game,
        # its people; each game's lead and another played where they live.
        output = sandbox(exe, worlds, 'cast', shots, tmp)
        m = re.search(r'selftest cast: (\d+) boxes \((\d+) faces\), (\d+) people listed, (\d+) of (\d+) played', output)
        if not m:
            raise SystemExit('FAIL: character screen: no summary\n' + output[-2000:])
        # (The mansion's New kid: the next played where they are, the one
        # played before left where they stood.)
        k = re.search(r'(\d+) new kids where they are \((\d+) here already\)', output)
        if (worlds/'maniac-1.svw').exists() and (not k or int(k.group(1)) != 1 or int(k.group(2)) != 1):
            raise SystemExit('FAIL: New kid\n' + output[-2000:])
        if k and int(k.group(1)):
            print('PASS: the mansion\'s New kid: the next played where they are (here already: where they stood), the one before left where they stood')
        boxes, faces, people, played, expected = (int(m.group(i)) for i in range(1, 6))
        if faces < 2 or played != expected or played < 2 * faces - 2:
            raise SystemExit(f'FAIL: character screen: {faces} faces, {played} of {expected} played')
        print(f'PASS: character screen: {boxes} games, {faces} faces, {people} people; {played} played where they live')
        # (The custom characters' box last, Crispy first: played where the
        # player is, about a third of a person tall; Sith Ewok 2 lights his
        # saber at L.)
        c = re.search(r'(\d+) custom played where the player is \(([\d.]+) of a person tall; (\d+) among the wanderers; (\d+) lit what they carry\)', output)
        if not c or int(c.group(1)) < 1 or not 0.2 <= float(c.group(2)) <= 0.45 or c.group(3) != '1' or int(c.group(4)) < 1:
            raise SystemExit('FAIL: custom characters\n' + output[-2000:])
        print(f'PASS: custom characters: {c.group(1)} in their own box (Crispy first), played where the player is, {c.group(2)} of a person tall; among the wanderers, the one before left beside them; {c.group(4)} lit what they carry at L (the others nothing)')
        # (From 0202) Among the wanderers: one left here who does not roam
        # stays through the next switch here; someone of the game's own who
        # lives here played, the one before stays where they stood.
        h = re.search(r'(\d+) left here kept\), (\d+) of the game\'s own here played', output)
        if not h or h.group(1) != '1' or h.group(2) != '1':
            raise SystemExit('FAIL: those left here at a switch\n' + output[-2000:])
        print('PASS: switching here: a custom one left who does not roam stays; someone of the game\'s own played, the one before stays where they stood')
        # Sith Ewok 3's moves (0200): L once a force grab (after the wait for
        # a second), L twice a swing, F force lightning, L once put away (a
        # walk stopped first); heckled and answered (written lines, a stand-in
        # model's, written when it is slow); not played, a show near the one
        # played now and then, none far away or walking. Crispy 2's pee: P
        # (a walk stopped), a puddle behind him either way he faces, dried to
        # a stain, kept (back again, saved and read back, 12 a place at most);
        # not played, on his own.
        output = sandbox(exe, worlds, 'moves', shots, tmp)
        m = re.search(r"selftest moves: (\d+) keys, (\d+) walks stopped, (\d+) heckled in written lines \((\d+) answered, (\d+) in Ewokese\), "
                      r"(\d+) with the model's lines, (\d+) written when it is slow, 1 waiting for others, (\d+) shows \((\d+) saber, (\d+) lightning\), (\d+) held far away or walking; "
                      r"Crispy 2: (\d+) pees .*?, (\d+) stains kept .*?, (\d+) on his own, 6 cut short.*?, 0 failed", output)
        if not m or int(m.group(1)) != 6 or int(m.group(3)) < 1 or int(m.group(4)) < 1 or int(m.group(6)) < 1 or int(m.group(7)) < 1 or int(m.group(9)) < 1 or int(m.group(10)) < 1 \
                or int(m.group(12)) != 2 or int(m.group(13)) != 3 or int(m.group(14)) != 1:
            raise SystemExit('FAIL: moves\n' + output[-2000:])
        print(f'PASS: Sith Ewok 3: {m.group(1)} keys (force grab, swing, lightning lit and not, put away by hand; {m.group(2)} walks stopped first); '
              f'heckled and answered (written, the model\'s, written when it is slow); {m.group(8)} shows not played ({m.group(9)} saber, {m.group(10)} lightning), held far away or walking; '
              f'Crispy 2: P (a walk stopped, a puddle behind him either way, dried to a stain), stains kept (back again, saved and read back, 12 at most), on his own; '
              f'cut short (as big as it got; none before his leg was up), drying on when entered again, his while begun again when played')
        # The camera (a stand-in for the iPhone's Photos): photos of the scene
        # and of the screen, a selfie of three, held still while asked.
        output = sandbox(exe, worlds, 'camera', shots, tmp)
        m = re.search(r'selftest camera: clean (\d+)x(\d+), full (\d+)x(\d+), selfie (\d+) shots (\d+)x(\d+)', output)
        if not m or int(m.group(5)) != 3:
            raise SystemExit('FAIL: camera\n' + output[-2000:])
        print(f'PASS: camera: a photo of the scene ({m.group(1)}x{m.group(2)}), of the screen ({m.group(3)}x{m.group(4)}), a selfie of three ({m.group(6)}x{m.group(7)}), held still')
        # The tour: every place installed a stop, the whole of it at 16x.
        output = sandbox(exe, worlds, 'tour', shots, tmp)
        m = re.search(r'selftest tour: (\d+) stops \((\d+) on foot, (\d+) warped, (\d+) not shown\)', output)
        if not m:
            raise SystemExit('FAIL: tour\n' + output[-2000:])
        stops, foot, warped, refused = (int(m.group(i)) for i in range(1, 5))
        # (Not The Dig's subway cars, nor the insides of rides, from 0198:
        # kWorldRideScenes, Zak's plane cabin and van cockpit.)
        insides = {'zak-11.svw', 'zak-30.svw'}
        svw = len([f for f in worlds.glob('*.svw') if f.stat().st_size and re.fullmatch(r'[a-z0-9]+-\d+\.svw', f.name) and f.name not in insides])
        if stops != svw or foot * 2 < stops:
            raise SystemExit(f'FAIL: tour: {stops} stops of {svw} places, {foot} on foot')
        unreached = int(re.search(r'(\d+) doors not reached', output).group(1))
        across = int(re.search(r'(\d+) gone through from as near as the walk boxes allow', output).group(1))
        if unreached * 100 > foot or not 0 < across * 10 < foot:
            raise SystemExit(f'FAIL: tour: {unreached} doors not reached, {across} from as near as the walk allows, for {foot} on foot')
        print(f'PASS: tour: {stops} stops ({foot} on foot, {warped} warped, {refused} not shown, {unreached} doors not reached, '
              f'{across} through from as near as the walk boxes allow); its controls; back where it began')
        # (From 0204) Begun past a door with no way back: the arrow back again
        # once it ends; a sentence half made while paused let go on Play; the
        # van asked for where it isn't, the tour on.
        wk = re.search(r'tour way back: (\d+) kept through a tour \((\d+) a half sentence let go on Play, (\d+) the van asked for elsewhere and the tour on\)', output)
        if not wk or (int(b.group(1)) and wk.group(1) != '1') or (wk.group(1) == '1' and (wk.group(2) != '1' or wk.group(3) != '1')):
            raise SystemExit('FAIL: tour: the way back, Play, the van\n' + output[-2000:])
        if wk.group(1) == '1':
            print('PASS: tour begun past a door with no way back: the arrow back there again once it ends; a half sentence let go on Play; the van asked for where it isn\'t, the tour going on')
        # The rides: The Dig's tram, every line both ways (when The Dig is
        # there); Zak's (when Zak is), each part on its own.
        cars = len(list(worlds.glob('dig-*-car.svw')))
        if cars or (worlds/'zak-3.svw').exists():
            # (The first line's car left at its second station last time: read
            # back so at launch.)
            output = sandbox(exe, worlds, 'rides', shots, tmp, extra='scummverse_sandbox_tram_parked=2\n')
            m = re.search(r'selftest rides: (\d+) tram stations, (\d+) rides, (\d+) waited', output)
            if not m or 'selftest PASS' not in output:
                raise SystemExit('FAIL: rides\n' + output[-2000:])
            if 'tram cars kept as left: 2' not in output:
                raise SystemExit('FAIL: where the tram cars stood not read back\n' + output[-2000:])
            if cars:
                if int(m.group(1)) != cars or int(m.group(2)) * 2 != cars or int(m.group(3)) * 2 != cars:
                    raise SystemExit('FAIL: The Dig\'s tram\n' + output[-2000:])
                print(f'PASS: The Dig\'s tram: {m.group(1)} stations, called from the ledge, ridden {m.group(2)} times, waiting {m.group(3)} times')
                # (Someone following rides along, out of sight with the one played.)
                t = re.search(r'(\d+) trams with someone following', output)
                if not t or t.group(1) != m.group(2):
                    raise SystemExit('FAIL: someone following not along on The Dig\'s tram\n' + output[-2000:])
                print('PASS: someone following rides The Dig\'s tram along, out of sight with the one played')
            # Zak's rides: the bus and the Mars tram both ways, a plane to every
            # airport, one missed by walking off (a tap away), a door over the
            # bus's stop tapped (the door), a plane's list closed, left
            # unanswered, walked off from and gone elsewhere from.
            z = re.search(r'(\d+) bus and tram rides, (\d+) flights, (\d+) missed, (\d+) door taps beside rides, (\d+) lists closed', output)
            airports = len([r for r in range(141, 150) if (worlds/f'zak-{r}.svw').exists()])
            if (worlds/'zak-3.svw').exists():
                if not z or int(z.group(1)) != 4 or int(z.group(2)) != airports or int(z.group(3)) != 1 or int(z.group(4)) < 1 or int(z.group(5)) != 4:
                    raise SystemExit('FAIL: Zak\'s rides\n' + output[-2000:])
                print(f'PASS: Zak\'s rides: the bus and the Mars tram both ways, {z.group(2)} flights (each airport, chosen from the list), one missed, '
                      f'{z.group(4)} doors over where rides are boarded, 4 lists closed or withdrawn')
                # (Someone following rides the bus along, off beside the one played.)
                f = re.search(r'(\d+) ridden with someone following', output)
                if not f or f.group(1) != '1':
                    raise SystemExit('FAIL: someone following not along on the bus\n' + output[-2000:])
                print('PASS: someone following rides the bus along (out of sight with the one played, not walking about the stop) and gets off beside the one played')
                # (From 0198) Each flight seen from Zak's plane cabin where it is
                # exported: the one played seated, on the first those following
                # (up to five) seated too, each seen with their head where the
                # painted passengers' are, Fate of Atlantis' camel (where
                # exported) in its seated pose, a selfie aboard keeping them
                # seated, nobody getting up; a tour begun aboard going home to
                # the stop.
                c = re.search(r'(\d+) flights seen from the cabin \((\d+) following seated, (\d+) in their seated pose, (\d+) crammed in\), (\d+) tours begun aboard home at the stop', output)
                if (worlds/'zak-11.svw').exists():
                    camel = (worlds/'atlantis-c93.svc').exists()
                    if not c or c.group(1) != z.group(2) or int(c.group(2)) < 2 or (camel and (c.group(3) != '1' or c.group(4) != '1')) or c.group(5) != '1':
                        raise SystemExit('FAIL: flights seen from the cabin\n' + output[-2000:])
                    print(f'PASS: {c.group(1)} flights seen from the cabin, the one played seated; {c.group(2)} following seated on the first as Maniac\'s own engine seats them, seen'
                          + (', the camel in its seated pose, crammed in too big for the seat' if camel else '') + '; a selfie aboard; a tour begun aboard home at the stop')
            # The Shuttle Bug: Mars to Melee Island and back, and there again
            # (when both are there); drawn there and boarded by a tap on it
            # when Maniac has taken its picture (zak-van.svv).
            v = re.search(r'(\d+) van flights, (\d+) by a tap on it', output)
            if (worlds/'zak-185.svw').exists() and (worlds/'monkey-33.svw').exists():
                drawn = (worlds/'zak-van.svv').exists()
                if not v or int(v.group(1)) != 3 or int(v.group(2)) != int(drawn):
                    raise SystemExit('FAIL: the Shuttle Bug\n' + output[-2000:])
                print('PASS: the Shuttle Bug: from its door on Mars to Melee Island, ' + ('drawn there beside the one played, boarded by a tap on it' if drawn else 'from the menu there (no picture of it taken yet)')
                      + ', back to Mars (not drawn over its own picture), to Melee again (drawn where it landed); not where it is not')
                k = re.search(r'(\d+) van flights from the cockpit', output)
                if (worlds/'zak-30.svw').exists():
                    if not k or k.group(1) != '3':
                        raise SystemExit('FAIL: van flights from the cockpit\n' + output[-2000:])
                    print('PASS: every van flight seen from its cockpit, the one played at the controls unseen')
                # (Asked for on the way on the Mars tram: not now; parked where
                # is no longer installed: back at its own site.)
                r = re.search(r'(\d+) van checks', output)
                if not r or r.group(1) != '2':
                    raise SystemExit('FAIL: the Shuttle Bug asked for on the way, or parked where is not installed\n' + output[-2000:])
                print('PASS: the Shuttle Bug not boarded on the way on the Mars tram; called home from a place no longer installed')
                # (From 0212) Parked at each of its sites, no door's middle under
                # it; in the plane's cabin everyone seated seen whole in the flight.
                # Standing on the floor too: the walk to its door ends at it (not,
                # as at Atlantis's Azores before, 126 pixels away).
                sv = re.search(r'rides seen: (\d+) flights with everyone seated seen whole, (\d+) of (\d+) van sites with no door\'s middle under the van, (\d+) with it on the floor', output)
                if not sv or sv.group(2) != sv.group(3) or sv.group(4) != sv.group(3) or ((worlds/'zak-11.svw').exists() and sv.group(1) == '0'):
                    raise SystemExit('FAIL: the van over doors or off the floor, or someone seated aboard never seen\n' + output[-2000:])
                print(f'PASS: the Shuttle Bug at each of its {sv.group(3)} sites off the doors\' middles (smaller where it must be), on the floor; {sv.group(1)} flights with everyone seated seen whole (the camera across them)')
    switch(a.data.resolve(), worlds, a.frames)
    # A cache whose place cannot be read: back to Maniac all the same.
    with tempfile.TemporaryDirectory(prefix='scummverse-broken-', dir=ROOT/'build') as broken:
        (Path(broken)/'monkey-33.svw').write_bytes(b'SVW3 not a scene')
        switch(a.data.resolve(), Path(broken), a.frames, broken=True)
    switch(a.data.resolve(), worlds, a.frames, story=True)
    print('PASS: sandbox engine')
