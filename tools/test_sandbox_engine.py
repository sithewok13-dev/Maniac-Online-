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
distaff, its notes lit, its Opening draft spun forwards and backwards, or,
with its things file's own answers, every record played through it: a tap
on a thing, a second, each draft spun on it both ways)
is shown under its first place, every verb chosen and used on the things
there (and on their other places' for pushing and picking up, by what each
thing's own script answers), what was taken kept; the things are where
their games put them; the mansion's and Zak's people are in their colours;
the iPhone's chat (a stand-in for it) is told who is there, those in a
conversation stand facing the one played, each line is said over its
speaker's head, and a tap picks someone when the chat asks whom; someone
asked along by it follows the one played, through doors too, until asked
to stay or someone else is played (the same person of another game where
they arrive steps aside); its character screen (a stand-in) gets a box per game with its lead's face and
people, and each game's lead and another are played where they live (the
same person as the one played chosen there: the one before goes home), and a
last box of custom characters (Crispy first, played where the player is); its
camera takes a photo of the scene and of the screen and a selfie of three
(everyone posed, nobody moving), and holds still while asked; its tour
visits every place installed, most on foot through doors, its controls
working, and ends back where it began; The Dig's tram is called from
each ledge, comes, and is ridden to the other end, where it waits; Zak's
bus and Mars tram are boarded and ridden both ways, a plane flies to every
airport chosen from the list it asks with, and a ride walked off is missed;
launched as the phone launches it (its own target, its settings on disk),
left past a door with no way back, someone asked along, the tour paused,
put away and stopped as iOS stops the app, it starts again there with all
of it; with the one played's file damaged, there as someone else; with that
place gone from the cache, or it and the one played damaged, elsewhere (no
way back from there); then from Maniac the
Worlds menu's New engine (preview) opens the sandbox and its Back to Maniac
Mansion returns to the same room, from the saved game (and with the app
stopped in the sandbox instead, the next start finds Maniac there); put
away as the phone puts it away and stopped, Maniac starts again from the
phone's restore point, where it was (one naming a story's target, or older
than the save for the sandbox, not taken; stopped again during its own
export at the next start, the point taken: from it all the same at the
start after); put away and stopped in a story it opened, Maniac starts
again where it was when it opened it. In every check each frame drawn in
parts (only where it changed) is the frame drawn whole, and the screen as
sent the frame converted whole.
Pictures go to build/sandbox-shots. Not an iPhone test.
"""
import argparse
import gzip
from pathlib import Path
import re
import resource
import shutil
import struct
import subprocess
import sys
import tempfile
from test_exploration import ROOT, command_for

# Test-only: at the top of Maniac's main loop. Once the game has run a while,
# the menu's New engine (preview), or with scummverse_switch_probe_story its
# story (Maniac Mansion's own, as the Worlds menu opens one); back from the
# sandbox (loaded from the temporary save), where Maniac is, then stop.
SWITCH = r'''
		if (ConfMan.hasKey("scummverse_switch_probe")) {
			static int scummverseSwitchFrames = 0, scummverseStoryFrames = 0;
			if (_scummverseStory) {
				// (Maniac's own story, opened from the sandbox: a while, then
				// ScummVM's menu's way out, home to the mansion. Opened from
				// the mansion: left to the restore probe, which stops the app.)
				if (!ConfMan.hasKey("scummverse_switch_probe_story") && ++scummverseStoryFrames == 120) {
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
				if (!ConfMan.hasKey("scummverse_switch_probe_story")) scummverseOpenSandbox();
				else for (int g = 0; g < ::Scummverse::WorldCatalog::worldGameCount(); ++g)
					if (::Scummverse::WorldCatalog::sameId(::Scummverse::WorldCatalog::kWorldGames[g].gameid, "maniac")) scummverseOpenStory(g);
			}
		}
'''
# Test-only, beside it: the phone's restore point (common/scummverse_restore.h).
# Once the mansion has run a while, put away as the iPhone's backend puts the
# app away (ios7_osys_main.cpp, saveState: the game held still, its autosave
# unless a player's save is in that slot, then the restore point naming the
# target and slot, written to scummverse_restore_point; the target named may
# be set instead, a story's), then stopped (or played on); with
# scummverse_restore_probe_story, the story playing put away instead (the
# mansion's own frames not counted) and the app stopped at once, as iOS
# stops it (a story's own quitting goes home to the mansion); started with
# 0, where it is at its first frame (the time played: a save's own once
# loaded, about none afresh), then stop.
RESTORE = r'''
		if (ConfMan.hasKey("scummverse_restore_probe") && _scummverseStory == ConfMan.hasKey("scummverse_restore_probe_story")) {
			static int scummverseRestoreFrames = 0;
			const int at = ConfMan.getInt("scummverse_restore_probe");
			if (at == 0 && scummverseRestoreFrames++ == 0) {
				warning("SCUMMVERSE_RESTORE_START slot=%d room=%d ego=%d played=%u", ConfMan.hasKey("save_slot") ? ConfMan.getInt("save_slot") : -1,
					_currentRoom, VAR(VAR_EGO), getTotalPlayTime() / 1000);
				quitGame();
			} else if (at > 0 && ++scummverseRestoreFrames == at) {
				PauseToken held = pauseEngine();
				const Common::String target = ConfMan.getActiveDomainName();
				const int slot = getAutosaveSlot();
				bool written = false;
				if (hasFeature(kSupportsSavingDuringRuntime) && canSaveAutosaveCurrently() &&
						getMetaEngine()->hasFeature(MetaEngine::kSupportsLoadingDuringStartup) && slot != -1) {
					const SaveStateDescriptor desc = getMetaEngine()->querySaveMetaInfos(target.c_str(), slot);
					if ((desc.getSaveSlot() == -1 || desc.isAutosave()) && saveGameState(slot, "Autosave", true).getCode() == Common::kNoError) {
						Common::DumpFile point;
						if (point.open(ConfMan.getPath("scummverse_restore_point"))) {
							point.writeString("[state]\nrestore_target=" + (ConfMan.hasKey("scummverse_restore_probe_names") ? ConfMan.get("scummverse_restore_probe_names") : target) +
								Common::String::format("\nrestore_slot=%d\n", slot));
							written = point.flush() && !point.err();
							point.close();
						}
					}
				}
				held.clear();
				warning("SCUMMVERSE_RESTORE_AWAY room=%d ego=%d played=%u written=%d", _currentRoom, VAR(VAR_EGO), getTotalPlayTime() / 1000, written);
				if (ConfMan.getBool("scummverse_restore_probe_stop")) {
					if (_scummverseStory) _system->quit(); // (the null backend's: the process ends here)
					quitGame();
				}
			}
		}
'''
LOOP = '\twhile (!shouldQuit()) {\n\t\t// Determine how long to wait before the next loop iteration should start\n'


def frames_drawn_whole(output, what):
    # (From 0243 the screen is drawn in parts; scummverse_check_frames draws
    # each frame whole too: every one the same, and the screen as sent.)
    m = re.search(r'sandbox frames: (\d+) checked, (\d+) drawn in parts not as drawn whole', output)
    if not m or int(m.group(2)):
        raise SystemExit(f'FAIL: sandbox {what}: frames drawn in parts not as drawn whole\n' + output[-4000:])
    return int(m.group(1))


def sandbox(exe, worlds, mode, shots, cwd, timeout=900, wanderers=False, extra=''):
    # (Wanderers off: each place's own people, the same every run. From 0267
    # a fixed random_seed: where they stroll the same every run too.)
    config = Path(cwd)/f'sandbox-{mode}.ini'
    config.write_text(f'[scummvm]\nscummverse_selftest={mode}\nscummverse_shots={shots}\nscummverse_screen=1280x720\n'
                      f'scummverse_wanderers={str(wanderers).lower()}\nscummverse_check_frames=true\nrandom_seed=4242\n{extra}')
    result = subprocess.run([str(exe), f'--config={config}', f'--path={worlds}', f'--savepath={cwd}', 'scummverse:sandbox'], cwd=cwd,
                            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
    output = result.stdout + result.stderr
    (ROOT/f'build/sandbox-{mode}.log').write_text(output)
    summary = [line for line in output.splitlines() if 'sandbox selftest' in line or 'sandbox walk' in line or 'sandbox verbs' in line or 'sandbox frames' in line]
    if result.returncode or 'SCUMMVERSE sandbox selftest PASS' not in output:
        raise SystemExit(f'FAIL: sandbox {mode}\n' + output[-4000:])
    frames_drawn_whole(output, mode)
    for line in summary:
        print('  ' + line.replace('WARNING: ', '').rstrip('!'))
    return output


def relaunch(exe, worlds, tmp):
    """The app stopped and started again: the sandbox's own target as Maniac
    makes it (scummverse-sandbox, its settings written to disk as on the
    phone). "keep" leaves it as in play, then put away as iOS puts the app
    away and gone without the run's own save at its end, as iOS stops it;
    "resume" starts as a launch starts and finds it all so. Then again with
    that place gone from the cache, with the one played's file damaged (as
    an export stopped partway leaves one): there as someone else, and with
    both damaged: started elsewhere."""
    work = Path(tmp)/'relaunch'
    work.mkdir()
    config, state = work/'sandbox.ini', work/'scummverse-sandbox.state'
    config.write_text('[scummvm]\nscummverse_selftest=keep\nscummverse_screen=1280x720\nscummverse_wanderers=false\n'
                      f'[scummverse-sandbox]\nengineid=scummverse\ngameid=sandbox\ndescription=Scummverse sandbox\npath={worlds}\n')

    def launch(mode, path, cache=''):
        # (The settings as the run before left them, the check and the cache changed.)
        text = re.sub(r'(?m)^scummverse_selftest=.*$', f'scummverse_selftest={mode}', config.read_text())
        text = re.sub(r'(?m)^scummverse_selftest_cache=.*\n', '', re.sub(r'(?m)^path=.*$', f'path={path}', text))
        config.write_text(text.replace('[scummvm]\n', f'[scummvm]\nscummverse_selftest_cache={cache}\n' if cache else '[scummvm]\n', 1))
        result = subprocess.run([str(exe), f'--config={config}', f'--savepath={work}', 'scummverse-sandbox'], cwd=work,
                                stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=900)
        output = result.stdout + result.stderr
        (ROOT/f'build/sandbox-{mode}{"-" + cache if cache else ""}.log').write_text(output)
        if result.returncode or 'SCUMMVERSE sandbox selftest PASS' not in output:
            raise SystemExit(f'FAIL: sandbox {mode} {cache}\n' + output[-4000:])
        for line in output.splitlines():
            if 'sandbox selftest' in line and 'PASS' not in line:
                print('  ' + line.replace('WARNING: ', '').rstrip('!'))

    def cache(name, damage):
        folder = work/name
        folder.mkdir()
        for f in worlds.iterdir():
            (folder/f.name).symlink_to(f)
        for f, size in damage:
            (folder/f).unlink()
            if size:
                # (A compressed one cut where its last four bytes, the size
                # it is read at, say gigabytes, as one cut short may say.)
                data = (worlds/f).read_bytes()
                while data[:2] == b'\x1f\x8b' and size < len(data) - 4 and struct.unpack('<I', data[size - 4:size])[0] < 7 << 29:
                    size += 1
                (folder/f).write_bytes(data[:size])
        return folder

    launch('keep', worlds)
    launch('resume', worlds)
    print('PASS: stopped as iOS stops the app and started again: where it was left, the one played, those asked along, the way back, the tour\'s stop')
    kept = config.read_text(), state.read_bytes()
    scene, look = (work/'scummverse-selftest.expect').read_text().splitlines()[1].split()
    for name, damage in (('gone', [(scene, 0)]), ('look', [(look, 40)]), ('damaged', [(scene, 3000), (look, 40)])):
        config.write_text(kept[0])
        state.write_bytes(kept[1])
        launch('resume', cache(name, damage), name)
    # (Never read at the size a damaged one says: on the phone, the app gone.
    # ru_maxrss is in kilobytes on Linux, bytes on macOS.)
    if resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss > (3 << 30 if sys.platform == 'darwin' else 3 << 20):
        raise SystemExit('FAIL: a damaged scene file read at the size it says (gigabytes)')
    print('PASS: started again with that place gone, or it and the one played damaged: elsewhere (no way back from there); the one played damaged: '
          'there as someone else; what was changed kept')


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
    export version 23 "SVO3" with no effects, then what each is inside;
    from 0254 a game's own answers after the same table, "SVO7" and on,
    read by test_panel: only the table here; from 0267 "SVOA" too)."""
    data = path.read_bytes()
    if data[:2] == b'\x1f\x8b':
        data = gzip.decompress(data)
    if data[:3] != b'SVO' or data[3:4] not in b'13456789A':
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
    if data[:4] not in (b'SVO1', b'SVO3'):
        return found
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


def answer_keys(path):
    """From 0285, a things file's answers ("SVO9" and on, see
    common/scummverse_panel.h) as a set of (room, object, verb kind, the
    picture played from, the thing with it), read as
    tools/test_world_setup.py reads them; none from an older file."""
    data = path.read_bytes() if path.exists() else b''
    if data[:2] == b'\x1f\x8b':
        data = gzip.decompress(data)
    # (From 0286 "SVOC" too: its answers as SVOB's, its later steps lines
    # too, after them.)
    if data[:4] not in (b'SVO9', b'SVOA', b'SVOB', b'SVOC'):
        return set()
    p = 6
    for _ in range(struct.unpack_from('<H', data, 4)[0]):
        p += 4 + 5 * struct.unpack_from('<H', data, p + 2)[0]
    count, p, keys = struct.unpack_from('<H', data, p)[0], p + 2, set()
    for _ in range(count):
        keys.add(struct.unpack_from('<HHBBH', data, p))
        p += 10  # (room, object, kind, from, with, its picture after, flags)
        p += 1 + 6 * data[p]  # (its others)
        lines, p = data[p], p + 1
        for _ in range(lines):
            speaker, p = data[p], p + 1
            p += (2 if speaker not in (0, 255) else 0) + (1 if speaker else 0)
            p += 1 + data[p]
    return keys


PUSH = 6


def check_arrivals(worlds):
    # (From 0285) Where a place's own scripts read the one played as it
    # starts, its export has them there, standing at the thing used, as a
    # player stands: Monkey Island 2's room 60 (a walk box read each frame:
    # at the foot of its tree, a plank pushed answers as its game answers,
    # not as a climb), places whose scripts have the camera follow them
    # (Monkey Island 2's 50, the Last Crusade's 7, Day of the Tentacle's 30:
    # before, no answers at all), the SCUMM Bar's important-looking pirates
    # talked to (their pan done) and, where their scripts take them away
    # standing there, a thing still answered as before (Zak's room 4, 152;
    # Monkey Island's room 3, 44). Each wherever its game's export is of
    # 0285's version (its marker). (From 0290) A place whose entry starts a
    # cut-scene that shows another room first, the first time, answered
    # past it, as a player skips it (Zak's living room, room 2: its cabinet
    # opened, the box of crayons in it picked up; before, no answers at all).
    cases = (('monkey2', 35, (60, 670, PUSH, 0, 0)), ('monkey2', 35, (50, 574, LOOK, 0, 0)), ('indy3', 30, (7, 148, LOOK, 0, 0)),
             ('tentacle', 34, (30, 248, LOOK, 0, 0)), ('monkey', 34, (28, 332, TALK, 0, 0)), ('monkey', 34, (3, 44, LOOK, 0, 0)),
             ('zak', 32, (4, 152, OPEN, 0, 0)), ('zak', 33, (2, 121, OPEN, 0, 0)), ('zak', 33, (2, 25, PICK_UP, 0, 0)))
    checked = 0
    for game, version, key in cases:
        if not (worlds/f'{game}-v{version}.svx').exists() or not (worlds/f'{game}-{key[0]}.svw').exists():
            continue
        if key not in answer_keys(worlds/f'{game}-things.svo'):
            raise SystemExit(f'FAIL: {game} room {key[0]}: object {key[1]} not answered (verb {key[2]} from {key[3]}) with the one played there as it starts '
                             f'(export {game} again: tools/export_worlds.py)')
        checked += 1
    return checked


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


def stopped_switch(exe, data, worlds, work, frames, log):
    """Maniac -> the new engine, the app stopped there: the new engine's run
    ends without Back to Maniac Mansion (as iOS stops the app, which leaves
    the mansion no restore point of its own); started again, the mansion is
    where it was saved for the new engine (its slot 100), not afresh, and the
    mark that says so is let go once it plays."""
    config = work/'stopped.ini'
    config.write_text('[scummvm]\nscummverse_roaming=false\nscummverse_wanderers=false\n'
                      f'scummverse_switch_probe={frames}\nscummverse_worlds_path={worlds}\nscummverse_selftest=walk\n')
    outputs, marks = [], []
    for _ in range(2):
        result = subprocess.run([str(exe), f'--config={config}', f'--path={data}', f'--savepath={work}', '--debuglevel=1'],
                                cwd=work, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=600)
        outputs.append(result.stdout + result.stderr)
        marks.append('scummverse_sandbox_open' in config.read_text())
        if result.returncode:
            break
    Path(log).write_text('\n'.join(outputs))
    def said(output, text):
        return [l.split(text + ' ')[1].rstrip('!') for l in output.splitlines() if text in l]
    if len(outputs) != 2 or len(said(outputs[0], 'SCUMMVERSE_SWITCH_OPEN')) != 1 or said(outputs[0], 'SCUMMVERSE_SWITCH_BACK') or \
            'SCUMMVERSE sandbox selftest PASS' not in outputs[0] or not marks[0]:
        raise SystemExit('FAIL: switch, the app stopped in the new engine: the first run\n' + outputs[-1][-6000:])
    where, again = said(outputs[0], 'SCUMMVERSE_SWITCH_OPEN')[0], said(outputs[1], 'SCUMMVERSE_SWITCH_BACK')
    loaded = [l for l in outputs[1].splitlines() if 'State loaded from' in l and ".c100'" in l]
    if again != [where] or len(loaded) != 1 or 'the mansion where it was when the new engine was opened' not in outputs[1]:
        raise SystemExit(f'FAIL: switch, the app stopped in the new engine: left Maniac at {where}, started again at {again or "its start"}\n' + outputs[1][-6000:])
    if marks[1]:
        raise SystemExit('FAIL: switch, the app stopped in the new engine: the mark kept once the mansion played')
    print(f'PASS: Maniac -> new engine, the app stopped there; started again, Maniac where it was ({where}), the mark let go')


def restored_switch(exe, data, worlds, work, frames, log):
    """The phone's restore point (the mansion has no launcher to take it):
    put away while the mansion plays (its autosave, the point naming it) and
    stopped there, started again from it, where it was, the point let go (a
    third start afresh); a point naming a story's target leaves the mansion
    to start as it would; the mansion's own story opened from it (its Worlds
    menu's way), put away and stopped there: started again (Explore mode, no
    story gone on in), the mansion from its save for the story (the mark the
    opening left), the story's point set aside; put away and played on, then
    the new engine opened and the app stopped there, the mansion's save for
    the new engine wins (0239's mark), the point (older) set aside; put away
    and stopped, then stopped again during the mansion's own export at the
    next start (as after an update that changes it), the point taken: the
    start after that, the export done, from the autosave all the same."""
    point = work/'scummvm.state'
    config = work/'restored.ini'
    base = ('[scummvm]\nscummverse_roaming=false\nscummverse_wanderers=false\n'
            f'scummverse_restore_point={point}\nscummverse_worlds_path={worlds}\n')
    logs = []

    def run(name, extra, fresh=False, stop_at=None):
        # (The settings as the run before left them, the probe's own changed.)
        kept = base if fresh else re.sub(r'(?m)^scummverse_(restore_probe\w*|switch_probe\w*|selftest)=.*\n', '', config.read_text())
        config.write_text(kept.replace('[scummvm]\n', '[scummvm]\n' + extra, 1))
        command = [str(exe), f'--config={config}', f'--path={data}', f'--savepath={saves}', '--debuglevel=1']
        if stop_at:
            # (Stopped as iOS stops the app once stop_at is said: nothing more
            # saved or written.)
            with subprocess.Popen(command, cwd=work, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
                lines = []
                for line in proc.stdout:
                    lines.append(line)
                    if stop_at in line:
                        proc.kill()
                        break
                proc.wait(timeout=600)
            output = ''.join(lines)
            logs.append(f'==== {name}\n' + output)
            Path(log).write_text('\n'.join(logs))
            if stop_at not in output:
                raise SystemExit(f'FAIL: restore point, {name}: never said {stop_at!r}\n' + output[-6000:])
            return output
        result = subprocess.run(command, cwd=work, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=600)
        output = result.stdout + result.stderr
        logs.append(f'==== {name}\n' + output)
        Path(log).write_text('\n'.join(logs))
        if result.returncode:
            raise SystemExit(f'FAIL: restore point, {name}: exit {result.returncode}\n' + output[-6000:])
        return output

    def said(output, text):
        return [l.split(text + ' ')[1].rstrip('!') for l in output.splitlines() if text in l]

    def loaded(output):
        return [l.split("'")[1].rsplit('/', 1)[-1] for l in output.splitlines() if 'State loaded from' in l]

    def fields(line):
        return dict(f.split('=') for f in line.split())

    def started(output):
        start = said(output, 'SCUMMVERSE_RESTORE_START')
        return fields(start[0]) if len(start) == 1 else {}

    def put_away(output):
        away = said(output, 'SCUMMVERSE_RESTORE_AWAY')
        return fields(away[0]) if len(away) == 1 and away[0].endswith(' written=1') else {}

    # Put away and stopped in the mansion; started again, from its autosave
    # (where it was, its time played the save's own); once more, afresh.
    saves = work/'restored'
    saves.mkdir()
    away = run('put away', f'scummverse_restore_probe={frames}\nscummverse_restore_probe_stop=true\n', fresh=True)
    gone = put_away(away)
    if not gone or int(gone['played']) < 2 or point.read_text() != '[state]\nrestore_target=maniac\nrestore_slot=0\n' or \
            not (saves/'maniac.s00').is_file():
        raise SystemExit('FAIL: restore point: not put away as the phone puts it away\n' + away[-6000:])
    where = f"room={gone['room']} ego={gone['ego']}"
    back = run('started again', 'scummverse_restore_probe=0\n')
    again = started(back)
    if not again or again['slot'] != '0' or f"room={again['room']} ego={again['ego']}" != where or \
            not int(gone['played']) <= int(again['played']) <= int(gone['played']) + 2 or loaded(back) != ['maniac.s00'] or \
            'the mansion where it was when the app was put away (its slot 0)' not in back or point.read_bytes():
        raise SystemExit(f'FAIL: restore point: put away at {gone}, started again at {again} (loaded {loaded(back)})\n' + back[-6000:])
    fresh = run('started once more', 'scummverse_restore_probe=0\n')
    once = started(fresh)
    if not once or once['slot'] != '-1' or int(once['played']) >= int(gone['played']) or loaded(fresh):
        raise SystemExit(f'FAIL: restore point: taken twice ({once})\n' + fresh[-6000:])
    print(f"PASS: Maniac put away as the phone puts it away and stopped; started again, where it was ({where}, {gone['played']} s played, "
          'its autosave), the restore point taken once')

    # The point naming a story's target (the app put away in a story): the
    # mansion starts as it would (here afresh), its own autosave not taken.
    saves = work/'restored-story'
    saves.mkdir()
    away = run('put away in a story', f'scummverse_restore_probe={frames}\nscummverse_restore_probe_stop=true\n'
                                      'scummverse_restore_probe_names=scummverse-story-maniac\n', fresh=True)
    gone = put_away(away)
    if not gone or 'restore_target=scummverse-story-maniac\n' not in point.read_text() or not (saves/'maniac.s00').is_file():
        raise SystemExit('FAIL: restore point: a story\'s not written\n' + away[-6000:])
    back = run('started again after a story', 'scummverse_restore_probe=0\n')
    again = started(back)
    if not again or again['slot'] != '-1' or int(again['played']) >= int(gone['played']) or loaded(back) or \
            "the phone's restore point is scummverse-story-maniac's, not the mansion's" not in back or point.read_bytes():
        raise SystemExit(f'FAIL: restore point: a story\'s taken by the mansion ({again})\n' + back[-6000:])
    print('PASS: a restore point naming a story leaves the mansion to start as it would (its own autosave not taken)')

    # A story the mansion opened (Maniac Mansion's own, as its Worlds menu
    # opens one: the mansion saved in its slot 100), put away there (its own
    # autosave, the point naming it) and stopped: started again in Explore
    # mode, where a story is not gone on in, the mansion from its save for
    # the story (the mark the opening left, let go), the point set aside.
    saves = work/'restored-opened'
    saves.mkdir()
    story = 'scummverse-story-maniac'
    away = run('put away in a story the mansion opened', f'scummverse_restore_probe={frames}\nscummverse_restore_probe_stop=true\n'
                                                         f'scummverse_restore_probe_story=true\nscummverse_switch_probe={frames}\n'
                                                         'scummverse_switch_probe_story=true\n', fresh=True)
    gone, opened = put_away(away), said(away, 'SCUMMVERSE_SWITCH_OPEN')
    marked = f'scummverse_sandbox_open={story}\n' in config.read_text()
    if not gone or len(opened) != 1 or point.read_text() != f'[state]\nrestore_target={story}\nrestore_slot=0\n' or \
            not (saves/'maniac.c100').is_file() or not (saves/f'{story}.s00').is_file():
        raise SystemExit('FAIL: restore point: put away in a story the mansion opened\n' + away[-6000:])
    back = run('started again after a story the mansion opened', 'scummverse_restore_probe=0\n')
    again = started(back)
    # (Afresh it is in the same room at its first frame: the slot, the save
    # loaded and the time played tell them apart.)
    if not again or again['slot'] != '100' or f"room={again['room']} ego={again['ego']}" != opened[0] or loaded(back) != ['maniac.c100'] or \
            int(again['played']) < 2 or not marked or f'the mansion where it was when {story} was opened' not in back or "the phone's restore point set aside" not in back or \
            point.read_bytes() or 'scummverse_sandbox_open' in config.read_text():
        raise SystemExit(f'FAIL: restore point: the mansion left for its own story at {opened[0]} (marked so: {marked}), put away and '
                         f'stopped there, started again at {again} (loaded {loaded(back)})\n' + back[-6000:])
    print(f"PASS: the mansion's own story opened from it ({opened[0]}), put away and stopped there: started again, the mansion "
          'where it was (its save for the story), the story\'s restore point set aside, the mark let go')

    # Put away and played on (the point left, as on the phone until the next
    # start), then the new engine opened and the app stopped there: the
    # mansion from its save for the new engine (later than the autosave),
    # the point set aside.
    saves = work/'restored-sandbox'
    saves.mkdir()
    away = run('put away, played on, the new engine', f'scummverse_restore_probe={max(frames // 2, 1)}\nscummverse_restore_probe_stop=false\n'
                                                       f'scummverse_switch_probe={frames}\nscummverse_selftest=walk\n', fresh=True)
    gone, opened = put_away(away), said(away, 'SCUMMVERSE_SWITCH_OPEN')
    if not gone or len(opened) != 1 or 'SCUMMVERSE sandbox selftest PASS' not in away or \
            'scummverse_sandbox_open' not in config.read_text() or not point.read_bytes():
        raise SystemExit('FAIL: restore point: put away, played on, the new engine opened\n' + away[-6000:])
    back = run('started again after the new engine', 'scummverse_restore_probe=0\n')
    again = started(back)
    if not again or again['slot'] != '100' or f"room={again['room']} ego={again['ego']}" != opened[0] or \
            int(again['played']) <= int(gone['played']) or loaded(back) != ['maniac.c100'] or \
            'the mansion where it was when the new engine was opened' not in back or \
            "the phone's restore point set aside" not in back or point.read_bytes():
        raise SystemExit(f'FAIL: restore point: put away at {gone}, the new engine opened at {opened[0]}, started again at {again} (loaded {loaded(back)})\n' + back[-6000:])
    print(f"PASS: put away, played on, the new engine opened and the app stopped there: Maniac from its save for the new engine "
          f"({opened[0]}, {again['played']} s played), the older restore point ({gone['played']} s) set aside")

    # Put away and stopped in the mansion; at the next start the mansion's
    # own export runs first (as after an update that changes it: here its
    # marker removed) and the app is stopped during it, the point taken (the
    # file let go); the start after that, the export done, the mansion from
    # its autosave all the same: the point kept on disk until the mansion's
    # start decides on it, then let go.
    saves = work/'restored-export'
    saves.mkdir()
    away = run('put away before an export', f'scummverse_restore_probe={frames}\nscummverse_restore_probe_stop=true\n', fresh=True)
    gone = put_away(away)
    if not gone or point.read_text() != '[state]\nrestore_target=maniac\nrestore_slot=0\n':
        raise SystemExit('FAIL: restore point: not put away before an export\n' + away[-6000:])
    where = f"room={gone['room']} ego={gone['ego']}"
    for marker in list((work/'worlds').glob('maniac-v*.svx')) + list((work/'worlds').glob('maniac-v*.try')):
        marker.unlink()
    stopped = run('stopped during the export', 'scummverse_restore_probe=0\n', stop_at="User picked target 'scummverse-export-maniac'")
    kept = 'scummverse_restore_taken=maniac\n' in config.read_text()
    if point.read_bytes() or any((work/'worlds').glob('maniac-v*.svx')):
        raise SystemExit('FAIL: restore point: the point not taken, or the export not stopped\n' + stopped[-6000:])
    back = run('started again after the export stopped', 'scummverse_restore_probe=0\n')
    again = started(back)
    if not again or again['slot'] != '0' or f"room={again['room']} ego={again['ego']}" != where or \
            not int(gone['played']) <= int(again['played']) <= int(gone['played']) + 2 or loaded(back) != ['maniac.s00'] or \
            'SCUMMVERSE_WORLD_EXPORT maniac ' not in back or 'the mansion where it was when the app was put away (its slot 0)' not in back or \
            not kept or 'scummverse_restore_taken' in config.read_text():
        raise SystemExit(f'FAIL: restore point: put away at {gone}, stopped during the export (kept on disk: {kept}), started again at {again} '
                         f'(loaded {loaded(back)})\n' + back[-6000:])
    print(f"PASS: put away and stopped, then stopped again during the mansion's own export (the point taken): the next start, "
          f"the export done, where it was ({where}, its autosave), the kept point let go")


def switch(data, worlds, frames, broken=False, story=False, stopped=False, restored=False):
    build = ROOT/'build/null'
    source = ROOT/'engine/engines/scumm/scumm.cpp'
    with tempfile.TemporaryDirectory(prefix='scummverse-switch-', dir=ROOT/'build') as tmp:
        work = Path(tmp)
        code = source.read_text()
        if code.count(LOOP) != 1:
            raise RuntimeError('Pinned main loop boundary changed')
        probe = work/'scumm.cpp'
        probe.write_text(code.replace(LOOP, LOOP.split('\n')[0] + '\n' + RESTORE + SWITCH + '\n'.join(LOOP.split('\n')[1:])))
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
        if stopped:
            stopped_switch(exe, data, worlds, work, frames, ROOT/'build/sandbox-stopped.log')
            return
        if restored:
            restored_switch(exe, data, worlds, work, frames, ROOT/'build/sandbox-restored.log')
            return
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
    # (Two games with people of one name in both, as Monkey Island's and
    # Monkey Island 2's Guybrush, the mansion's and Day of the Tentacle's
    # tentacles: the checks that nobody is shown twice have someone to try.)
    monkeys = any(worlds.glob('monkey-*.svw')) and any(worlds.glob('monkey2-*.svw'))
    twins = monkeys or (any(worlds.glob('maniac-*.svw')) and any(worlds.glob('tentacle-*.svw')))
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
        arrived = check_arrivals(worlds)
        if arrived:
            print(f'PASS: {arrived} answers of places whose scripts read the one played as they start, recorded with them there (from 0285)')
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
        # (From 0272) Each door an answer makes untouchable or touchable, before
        # and after it: made untouchable no door (a tap there no tap on it, no
        # way through it), kept so; a door again once another answer makes it
        # touchable; those whose games make them so only in a state the new
        # engine does not play, doors all the same.
        td = re.search(r'selftest doors touched: (\d+) records of (\d+) doors .*?; (\d+) made untouchable no door then .*?(\d+) of them kept so .*?, (\d+) made touchable again .*?; '
                       r'(\d+) made touchable a door then; (\d+) whose games .*?; (\d+) failed', output)
        if not td or td.group(8) != '0' or ((worlds/'zak-25.svw').exists() and (td.group(3) == '0' or td.group(4) == '0' or td.group(5) == '0')):
            raise SystemExit('FAIL: doors answers make untouchable or touchable\n' + output[-2000:])
        print(f'PASS: {td.group(1)} records of {td.group(2)} doors answers make untouchable or touchable: {td.group(3)} made untouchable no door then (no tap on it, '
              f'no way through it; {td.group(4)} kept so through a save and a load), {td.group(5)} a door again once another answer made it touchable; {td.group(6)} made touchable '
              f'a door then; {td.group(7)} a door all the same (their games make them so only in a state the new engine does not play)')
        # (From 0280) Each door its game starts untouchable until an answer
        # there opens it: no door at the start (a tap there no tap on it, no
        # way through it), a door once that answer is given, kept so; those
        # whose games open them otherwise (by the way one arrives, or on their
        # own), those only answers elsewhere open and those their games start
        # touchable, doors from the start.
        ts = re.search(r'selftest doors start shut: (\d+) doors .*?; (\d+) a door once that answer is given \((\d+) kept so .*?\); (\d+) set aside .*? and (\d+) opened only by answers '
                       r'elsewhere, doors from the start, as are (\d+) an answer makes touchable', output)
        if not ts or ts.group(1) != ts.group(2) or ts.group(2) != ts.group(3) or ((worlds/'zak-25.svw').exists() and ts.group(1) == '0'):
            raise SystemExit('FAIL: doors their games start untouchable\n' + output[-2000:])
        print(f'PASS: {ts.group(1)} doors their games start untouchable until an answer there: no door at the start (no tap on it, no way through it), a door once it is '
              f'given ({ts.group(3)} kept so through a save and a load); {ts.group(4)} set aside (their games open them otherwise), {ts.group(5)} opened only from elsewhere '
              f'and {ts.group(6)} started touchable, doors from the start')
        output = sandbox(exe, worlds, 'wander', shots, tmp, wanderers=True)
        print('PASS: everyone out; those coming in shown; where everyone is kept')
        # (From 0230) Never two of anyone (by name: another game's of the
        # same name), in no place nor on the stage; with two games of the
        # same people here, two of one person sent here shown once (and not
        # beside one of them played); Monkey Island's lead played, the others
        # of his name kept out.
        t = re.search(r"never two of anyone: (\d+) places checked with nobody twice \((\d+) twice\), (\d+) on the stage twice, (\d+) of the one played's name came in "
                      r"\((\d+) of (\d+) kept out\); (.+?) of games (-?\d+) and (-?\d+) sent here: (\d+) of 2 stepped aside", output)
        if not t or int(t.group(1)) == 0 or any(t.group(i) != '0' for i in (2, 3, 4)) or t.group(5) != t.group(6) \
                or (twins and (t.group(7) == 'nobody' or t.group(10) != '2')) or (monkeys and t.group(6) == '0'):
            raise SystemExit('FAIL: wanderers: two of one person\n' + output[-2000:])
        print(f'PASS: never two of anyone: {t.group(1)} places with nobody twice, nobody twice on the stage; {t.group(7)} of two games sent here, '
              f'{t.group(10)} of 2 stepped aside; {t.group(6)} of the one played\'s name kept out')
        # Each game's own verb panel (exported from its start): every verb
        # chosen, used on the things there, kept.
        output = sandbox(exe, worlds, 'verbs', shots, tmp)
        panels = int(re.search(r'selftest verbs: (\d+) panels', output).group(1))
        exported = len([f for f in worlds.glob('*-ui.svi') if f.stat().st_size])  # (an emptied one is none)
        if panels != exported:
            raise SystemExit(f'FAIL: {panels} verb panels shown of {exported} exported')
        print(f'PASS: {panels} games\' own verb panels: each verb chosen; look, open, close, push, pick up; kept')
        # (From 0272) With a verb chosen, a door an answer made untouchable is
        # no tap on it either: the verb not used on it, not gone through.
        tv = re.search(r'selftest doors touched: .*?; (\d+) made untouchable no door then \(a tap there not on its way through it, (\d+) with a verb chosen not used on it either.*?(\d+) failed', output)
        if not tv or tv.group(3) != '0' or ((worlds/'zak-25.svw').exists() and tv.group(2) == '0'):
            raise SystemExit('FAIL: a verb on a door an answer made untouchable\n' + output[-2000:])
        print(f'PASS: {tv.group(2)} taps with a verb chosen on doors answers made untouchable: the verb not used on them, not gone through, as their games leave them')
        # (From 0280) So too a door its game starts untouchable until an answer there.
        tz = re.search(r'selftest doors start shut: (\d+) doors .*?, (\d+) with a verb chosen not used on it either', output)
        if not tz or ((worlds/'zak-25.svw').exists() and tz.group(2) == '0'):
            raise SystemExit('FAIL: a verb on a door its game starts untouchable\n' + output[-2000:])
        print(f'PASS: {tz.group(2)} taps with a verb chosen on doors their games start untouchable: the verb not used on them, not gone through')
        # (From 0276) A thing given back that an answer of two there uses up
        # (Fate of Atlantis's ladder: on room 48's broken stairway, in room
        # 18's hole): taken, used up (no thing where it lay: not taken
        # twice), given back, used up again, each kept through a save and a
        # load. Room 18's once its things file has the hole's ladder's
        # answers (atlantis-v30).
        gb = re.search(r'selftest given back: (\d+) of (\d+) answers .*?; (\d+) not tried .*?, (\d+) no loop .*?; (\d+) failed', output)
        if not gb or gb.group(5) != '0' or int(gb.group(1)) + int(gb.group(3)) + int(gb.group(4)) != int(gb.group(2)) or ((worlds/'atlantis-48.svw').exists() and gb.group(1) == '0') or \
                ((worlds/'atlantis-v30.svx').exists() and int(gb.group(1)) < 3):
            raise SystemExit('FAIL: a thing given back that an answer uses up\n' + output[-2000:])
        print(f'PASS: {gb.group(1)} of {gb.group(2)} answers giving back a thing an answer of two uses up, played in turn: given back, used up again, '
              f'never a second one where it lay; kept through a save and a load')
        # (From 0290) A thing a later game's answer takes or gives that its
        # place has no picture of (Day of the Tentacle's hamster, room 42;
        # Monkey Island's bananas, room 25): carried by its name, drawn in its
        # slot, kept through a save and a load (before, refused). Zak's
        # CashCard (room 1), given by an answer of two that leaves it a
        # picture of its own where it lay: so once given, entered again and
        # read back (before, drawn there again, carried); and its living room
        # (room 2) answered past its first cut-scene, where its export is
        # 0290's (zak-v33).
        nm = re.search(r'selftest named: (\d+) of (\d+) things .*?, (\d+) kept through a save and a load; (\d+) failed', output)
        if not nm or nm.group(4) != '0' or nm.group(1) != nm.group(2) or nm.group(3) != nm.group(1) or ((worlds/'tentacle-42.svw').exists() and nm.group(1) == '0'):
            raise SystemExit('FAIL: things with no picture of their own carried by their names\n' + output[-2000:])
        print(f'PASS: {nm.group(1)} things later games\' answers take or give with no picture of their own carried by their names, drawn in their slots, kept')
        zp = re.search(r'selftest Zak McKracken given and placed: (\d+) of (\d+) answers .*?; (\d+) living room', output)
        zak33 = (worlds/'zak-v33.svx').exists()
        if not zp or zp.group(1) != zp.group(2) or (zak33 and (worlds/'zak-1.svw').exists() and zp.group(1) == '0') or \
                (zak33 and (worlds/'zak-2.svw').exists() and zp.group(3) != '1'):
            raise SystemExit('FAIL: Zak\'s CashCard\'s place once given, or its living room\'s answers (export Zak again: tools/export_worlds.py)\n' + output[-2000:])
        print(f'PASS: {zp.group(1)} of Zak\'s answers of two giving a thing they leave a picture of its own where it lay, so when entered again and read back; '
              f'{zp.group(3)} living room answered past its first cut-scene')
        # (From 0281) A thing its game starts untouchable that an answer makes
        # touchable (one thing, or a thing carried used on one): the answer
        # played as a player plays it, then each answer of the thing from the
        # picture it is left in, as recorded; those its export plays from 0281
        # (Monkey Island's room 41, 378; Monkey Island 2's room 12, 106; The
        # Curse of Monkey Island's room 69, 1164; ...) with answers wherever
        # their game's export is of this version. And a thing an answer
        # gives: carried, its place as its game leaves it (the answer's own
        # picture for it, else as its own pick up leaves it), not drawn where
        # it lay (Monkey Island 2's map piece, room 48; Fate of Atlantis's
        # tube, room 73).
        rv = re.search(r'selftest revealed: (\d+) things .*?\((\d+) with answers .*?, (\d+) with none.*?then (\d+) of (\d+) of their answers as recorded '
                       r'\((\d+) not playable here, (\d+) inside another shut\); (\d+) of (\d+) its exports play from 0281 so; (\d+) failed', output)
        ga = re.search(r'selftest given away: (\d+) answers .*?\((\d+) setting its picture.*?played so: (\d+) carried.*?; (\d+) not playable.*?; (\d+) failed', output)
        if not rv or rv.group(10) != '0' or rv.group(4) != rv.group(5) or rv.group(8) != rv.group(9) or \
                ((worlds/'monkey-v32.svx').exists() and (worlds/'monkey-41.svw').exists() and int(rv.group(8)) == 0):
            raise SystemExit('FAIL: things an answer reveals\n' + output[-2000:])
        if not ga or ga.group(5) != '0' or int(ga.group(3)) + int(ga.group(4)) != int(ga.group(1)) or \
                ((worlds/'monkey2-48.svw').exists() and (worlds/'monkey2-v33.svx').exists() and int(ga.group(3)) == 0):
            raise SystemExit('FAIL: things an answer gives, drawn where they lay\n' + output[-2000:])
        print(f'PASS: {rv.group(1)} things their games start untouchable made touchable by an answer, the answer played: {rv.group(4)} of {rv.group(5)} of their '
              f'answers as recorded ({rv.group(3)} with none of their own); {rv.group(8)} of {rv.group(9)} its exports play from 0281 so; '
              f'{ga.group(3)} of {ga.group(1)} answers giving a thing: carried, its place as its game leaves it ({ga.group(4)} not playable here)')
        # (From 0283) An answer that takes the one played to another place of
        # its game, as its export records it (Day of the Tentacle's room 23,
        # its open door 164 used: room 21), played as a player plays it: its
        # first line said where it began, then there once its lines are said,
        # standing where its game leaves them, the one following brought
        # along, the arrow back where no door leads back; kept through a save
        # and a load; let go by another way taken first. Each one whose places
        # are installed; Day of the Tentacle's once its export is of this
        # version (tentacle-v32).
        gs = re.search(r'selftest goes: (\d+) of (\d+) answers .*?, (\d+) let go by another way taken first; (\d+) of (\d+) its export records from 0283 so; '
                       r'(\d+) not playable here; (\d+) failed', output)
        if not gs or gs.group(7) != '0' or int(gs.group(1)) + int(gs.group(6)) != int(gs.group(2)) or gs.group(3) != gs.group(1) or gs.group(4) != gs.group(5) or \
                ((worlds/'tentacle-v32.svx').exists() and (worlds/'tentacle-23.svw').exists() and (worlds/'tentacle-21.svw').exists() and (gs.group(1) == '0' or gs.group(5) == '0')):
            raise SystemExit('FAIL: an answer taking the one played to another place\n' + output[-2000:])
        print(f'PASS: {gs.group(1)} of {gs.group(2)} answers taking the one played to another place of their game: there once said, where their game leaves them, '
              f'those following along, kept through a save and a load, let go by another way taken first ({gs.group(6)} not playable here)')
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
        # (From 0271 Loom's things as its game's scripts answer its controls:
        # every record through the distaff, the self-test's own checks.)
        lr = re.search(r'selftest Loom: (\d+) of (\d+) records of (\d+) things .*?(\d+) taps, (\d+) second taps, (\d+) drafts \((\d+) backwards\) through its distaff', output)
        if lr and int(lr.group(2)):
            print(f'PASS: Loom: {lr.group(1)} of {lr.group(2)} records of {lr.group(3)} things through its own controls ({lr.group(4)} taps, {lr.group(5)} second taps, '
                  f'{lr.group(6)} drafts, {lr.group(7)} of them backwards)')
        # (From 0271 a draft spun on the way to a thing just tapped spins
        # nothing there; its tap's answer is given on arriving, not lost.)
        kept = re.search(r'selftest Loom: .*?; (\d+) drafts spun on the way to a thing tapped', output)
        if kept and int(kept.group(1)):
            print(f'PASS: Loom: {kept.group(1)} draft spun on the way to a thing tapped, its tap\'s answer kept')
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
        # to the plain rules when pinned. From 0274, its export version 42,
        # 16 of those silent picked up give a thing: away now, as their things
        # start hidden (the quarters of room 18, the demo tape, the hamster);
        # each played by the given check below. From 0278, its export version
        # 43, those that hand a verb on to another thing (a thing lying there
        # picked up first among them) are the hand-off check's, below: counted
        # with these.)
        handed = re.search(r"selftest handed: (\d+) of (\d+) records of one thing of the mansion's handing a verb on to another as its sentence script runs it next, as those verbs "
                           r"used there by a player \((\d+) away, (\d+) doing nothing there either; (\d+) of the effects' records\); the tape in (\d+) of 3 decks turning it on and off, "
                           r"its line the deck's with the tape in \((\d+) from across the place\), (\d+) of 2 refused taken out while on; the Victrola (\d+) played and stopped by its record, refused taken off while it plays; "
                           r"the radio (\d+) picked up and its batteries given opened where it lies, not again; the package (\d+) picked up and its stamps given pulled at the front door, "
                           r"refused pulled or opened again carried, (\d+) its stamps picked off first; (\d+) of 2 carried answered as their scripts", output)
        handedEffects = int(handed.group(5)) if handed else 0
        if (worlds/'maniac-1.svw').exists() and (not effects or int(effects.group(1)) + handedEffects < 840 or int(effects.group(2)) > 96 or int(effects.group(3)) < 35 or int(effects.group(4)) < 3
                                                 or int(effects.group(5)) > 70 or effects.group(6) != '4'
                                                 or ((worlds/'maniac-16.svw').exists() and effects.group(7) != '0')):
            raise SystemExit('FAIL: the mansion\'s things as their own scripts answer (export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
        # (From 0240) The wall safe behind the painting (room 9): Open on it
        # shows its keypad (room 43, a close-up, exported with the mansion's
        # places, no place itself); the code its own start chose, tapped key by
        # key, opens it, the envelope inside taken; a wrong code closes the
        # keypad with its line, the safe shut (its records not tried as plain
        # answers: shown as the close-up).
        safe = re.search(r'selftest close-ups: (\d+) records shown as close-ups; the wall safe: (\d+) opened with its code key by key on its keypad, '
                         r'the envelope inside taken, shut again; (\d+) not opened with a wrong code, the keypad closed, its line said; '
                         r"(\d+) left by a menu's choice, unanswered", output)
        # (From 0248 the TV's Turn on (room 17) shows its film: a record too.)
        film = (worlds/'maniac-40.svw').exists() and (worlds/'maniac-40.svw').stat().st_size > 0
        # (From 0263 the lab's switch too, from the mansion's export version
        # 39: three more records shown as its films.)
        mansion = max([int(f.stem.split('-v')[1]) for f in worlds.glob('maniac-v*.svx')] or [0])
        closeups = (2 if film else 1) + (3 if mansion >= 39 else 0)
        if (worlds/'maniac-9.svw').exists() and (worlds/'maniac-43.svw').exists() and (worlds/'maniac-43.svw').stat().st_size and \
                (not safe or safe.group(1) != str(closeups) or safe.group(2) != '1' or safe.group(3) != '1' or safe.group(4) != '1'):
            raise SystemExit('FAIL: the wall safe and its keypad (export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
        if safe and safe.group(2) == '1':
            print('PASS: the wall safe behind the painting: Open shows its keypad (the close-up, nobody there, kept as the room it was opened from); '
                  'the code its own start chose, tapped key by key, opens it back where they stood, the envelope inside taken; Use and a wrong code: '
                  'the keypad closes, its line said, the safe still shut; a menu\'s choice there leaves it unanswered')
        # (From 0252) The safe's room not shown again as the code's last key
        # is pressed (the one played's file not read then): over once all the
        # same, the safe open, somewhere else as a launch starts (not tried
        # again at each key tapped).
        safe_fell = re.search(r"left by a menu's choice, unanswered; (\d+) over once where the place it was shown from could not be shown again \(elsewhere, open\)", output)
        if safe and safe.group(2) == '1' and (not safe_fell or safe_fell.group(1) != '1'):
            raise SystemExit('FAIL: the wall safe\'s keypad not over once where its room could not be shown again\n' + output[-2000:])
        if safe_fell and safe_fell.group(1) == '1':
            print('PASS: the wall safe\'s keypad over once where its room cannot be shown again as the last key is pressed: elsewhere, the safe open')
        # (From 0242) The telescope (room 28): Use shows its view (room 34, or
        # 35 at its left end; a close-up, no place), what it is turned to as
        # the export recorded each turn both ways the painting can be, for the
        # game's own time; its buttons turn it a coin at a time (none paid:
        # its own line), and turned to where the painting moved shows the
        # code's part, its things as the start that chose the safe's code
        # marked them; a tap leaves it, everyone back where they stood. A
        # custom character chosen, or the Shuttle Bug boarded from the Worlds
        # menu, while it is shown: left first.
        scope = re.search(r'selftest telescope: (\d+) of (\d+) views shown as recorded \(nobody there, kept as where it was used from, gone after their time, everyone back\); '
                          r'(\d+) pressed unpaid as its own script answers, (\d+) turned towards the code\'s view a coin at a time \((\d+) coins used up\), (\d+) at its end; '
                          r"(\d+) showed the code's part with its things as recorded \((\d+) marked\), left by a tap, everyone back \((\d+) following\); "
                          r'left for (\d+) custom character chosen there, (\d+) Shuttle Bug boarded from the Worlds menu', output)
        if (worlds/'maniac-28.svw').exists() and (worlds/'maniac-34.svw').exists() and (worlds/'maniac-34.svw').stat().st_size and \
                (not scope or scope.group(1) != scope.group(2) or int(scope.group(2)) < 6 or scope.group(3) != '1' or int(scope.group(4)) < 1
                 or int(scope.group(5)) < int(scope.group(4)) or scope.group(7) != '1' or scope.group(9) != '1' or scope.group(10) != '1' or scope.group(11) != '1'):
            raise SystemExit('FAIL: the telescope and its view (export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
        if scope and scope.group(7) == '1':
            print(f'PASS: the telescope: Use shows its view (a close-up, nobody there, kept as the room it was used from), {scope.group(1)} turns and paintings '
                  f'as the export recorded them, for the game\'s own time, everyone back; its buttons turned it {scope.group(4)} steps a coin at a time '
                  f'(unpaid, its own line), to the code\'s part with the painting moved, its things as that start marked them ({scope.group(8)} drawn); '
                  'a tap leaves it; a custom character chosen and the Shuttle Bug boarded from the Worlds menu there leave it first')
        # (From 0252) Its room not shown again as a tap or its time ends the
        # view (the one played's file not read then): over once all the same,
        # somewhere else as a launch starts.
        scope_fell = re.search(r'Shuttle Bug boarded from the Worlds menu; (\d+) over once where the place it was shown from could not be shown again \(elsewhere\)', output)
        if scope and scope.group(7) == '1' and (not scope_fell or scope_fell.group(1) != '2'):
            raise SystemExit('FAIL: the telescope\'s view not over once where its room could not be shown again\n' + output[-2000:])
        if scope_fell and scope_fell.group(1) == '2':
            print('PASS: the telescope\'s view over once where its room cannot be shown again, by a tap and by its time: elsewhere')
        # (From 0248) The TV (room 17) and the typewriter (room 27): with the
        # main power off, Turn on says its line, no film; Turn off as its
        # script answers; with it on, its film (room 40, a close-up: the TV on
        # in the place first, then the one there in their place and colour,
        # nobody else in view, every line and picture on its tick as the
        # export recorded them), back where they stood, the TV off, the mark
        # left for the one played only; a menu's choice leaves it unwatched, a
        # tap skips to its end, marked. The typewriter with the envelope:
        # refused unwatched, typed once watched (then already so), refused
        # for another unwatched; the mailbox shut as before, open and the
        # envelope read as they answer without and with the address; the
        # marks kept through a save and reload, an older state (none) read.
        tv = re.search(r"selftest TV: (\d+) said its line with the main power off \(no film\), (\d+) turned off as its own script answers; (\d+) played its film as recorded "
                       r"\((\d+) of (\d+) events on their ticks, (\d+) lines said, the one there in their place and colour, nobody else in view, kept as where it was turned on from, back where they stood\), "
                       r"(\d+) marked for the one played only; (\d+) left unwatched by a menu's choice, (\d+) skipped by a tap and marked; the typewriter: (\d+) refused unwatched, (\d+) typed the address "
                       r"once watched \((\d+) already addressed, (\d+) for another who watched\); the mailbox: (\d+) shut as before, open (\d+) without the address, (\d+) with it; the envelope read: (\d+) blank, (\d+) addressed; "
                       r"(\d+) marks kept through a save and reload \((\d+) older states read with none\)", output)
        if film and all((worlds/f'maniac-{r}.svw').exists() for r in (1, 9, 17, 27)) and \
                (not tv or tv.group(1, 2, 3) != ('1', '1', '1') or int(tv.group(5)) < 4 or tv.group(4) != tv.group(5) or int(tv.group(6)) < 2 or tv.group(7) != '1'
                 or tv.group(8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18) != ('1',) * 11 or tv.group(19) != '3' or tv.group(20) != '1'):
            raise SystemExit('FAIL: the TV, its film and the typewriter (export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
        if tv and tv.group(3) == '1':
            print(f'PASS: the TV: with the main power off its line, no film; Turn off as its script answers; with it on, its film (a close-up: the TV on first, '
                  f'then the one there in their place and colour, {tv.group(4)} lines and pictures each on its tick as recorded, {tv.group(6)} lines), back where they stood, the mark '
                  'left for the one who watched only; a menu\'s choice leaves it unwatched, a tap skips it, marked; the typewriter with the envelope refuses '
                  'until the kid watched, then types the address once; the mailbox and the envelope answer without and with it; the marks kept through a '
                  'save and reload, an older state read')
        # (From 0250) The rest of the envelope's way to the mailbox, from
        # afresh: each answer refusing before what its script wants, as
        # recorded (the empty jar in the microwave, the tap off, the contents
        # unopened, the stamps unsteamed, the mailbox with nothing in the
        # envelope); the jar filled at the running tap, it and the envelope in
        # the microwave (touchable only open), steamed open turned on (not
        # with the envelope alone), both taken out again; opened carried (the
        # quarter given, not torn), the manuscript put in, addressed after the
        # TV; the package at the front door its time after the stairs (not a
        # tick before, never twice), its stamps given opened, stamped; posted
        # (read addressed; taken back before its time: nothing then), not due
        # with the flag down, the mailbox open or a mark missing, due on
        # leaving it shut with the flag up, kept through a save and reload,
        # collected its time after leaving (waiting while at the front door),
        # nothing after it; torn open, refused by the contents, the stamps and
        # the microwave; an older state (marks, no timed events) read, damaged
        # timed events let go; a film whose place cannot be shown again as it
        # ends over once, elsewhere, marked (from a review of 0248).
        mail = re.search(r"selftest mail: (\d+) refused before what their scripts want, as recorded \(the empty jar, the tap off, the contents unopened, the stamps unsteamed, "
                         r"the mailbox with nothing in the envelope\); the kitchen: (\d+) jar filled at the running tap, (\d+) put in the microwave with the envelope, (\d+) steamed open \((\d+) not with "
                         r"the envelope alone\), (\d+) taken out again; (\d+) opened carried \(the quarter given, not torn\), (\d+) manuscript put in, (\d+) addressed after the TV; (\d+) package at the front "
                         r"door (\d+) ticks after the stairs \(not before; (\d+) stamps given by it\), (\d+) stamped; (\d+) posted \((\d+) read addressed, (\d+) taken back with no pickup\), (\d+) not due with the "
                         r"flag down, the mailbox open or a mark missing, (\d+) due on leaving the mailbox shut with its flag up; (\d+) kept through a save and reload, (\d+) collected (\d+) ticks after leaving \((\d+) "
                         r"waited while at the front door\), (\d+) nothing after it; (\d+) torn open \(the contents, the stamps and the microwave refusing it\); (\d+) older states read \(marks, no "
                         r"timed events\), (\d+) with damaged timed events read without them; (\d+) film over once where its place could not be shown again \(elsewhere, marked\)", output)
        if film and all((worlds/f'maniac-{r}.svw').exists() for r in (1, 2, 7, 9, 12, 17, 22, 27, 36, 38)) and \
                (not mail or mail.group(1) != '5' or mail.group(3) != '2' or mail.group(11) != '18300' or mail.group(21) != '7200'
                 or any(mail.group(k) != '1' for k in (2, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26, 27))):
            raise SystemExit('FAIL: the envelope\'s way to the mailbox and its pickup (export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
        if mail and mail.group(14) == '1':
            print('PASS: the envelope\'s way to the mailbox: each answer refusing before what its script wants, then as recorded: the jar filled at the running tap, '
                  'it and the envelope put in the microwave and steamed open (not with the envelope alone), taken out again; opened carried (the quarter given, not '
                  'torn), the manuscript put in, addressed after the TV; the package at the front door its time after the stairs, its stamps, stamped; posted (read '
                  'addressed; taken back, no pickup; not due with the flag down, the mailbox open or a mark missing), due on leaving, kept through a save and reload, collected '
                  f'{mail.group(21)} ticks after leaving (waiting while at the front door), nothing after it; torn open, refused; older and damaged states read; '
                  'a film whose place cannot be shown again over once, elsewhere')
        # (From 0257) The radio in the hidden room and the Meteor Police, from
        # afresh: the old radio opened, its tube refused to another kid (as
        # recorded) and taken by Bernard; the socket refusing another kid and
        # taking the tube from Bernard (in its place, touchable); the radio
        # refusing to turn on without the tube (as recorded), nothing with the
        # main power off, on, off (its lines off and used off); the wanted
        # poster read with the number its keypad wants; on, Use: the keypad, a
        # wrong number calling nothing, the right one calling the Meteor
        # Police: their film (room 32) as recorded, back where they stood; at
        # their time (as the export measured it) with the dungeon shut nothing,
        # called again (the film skipped by a tap), kept through a save and
        # reload; with its doors open the badge left there (taken), never
        # called again after (from 0263 used on, its line, no keypad, as its
        # script answers once they took the meteor); the tube taken out again
        # (the radio off). As the wall safe's keypad (0252): where it was used
        # from not shown again as the last key is pressed, over once, someone
        # else played, called.
        radio = re.search(r"selftest radio: the tube (\d+) refused to another kid, (\d+) taken by Bernard; the socket (\d+) refused to another kid, (\d+) the tube put in by Bernard; "
                          r"the radio (\d+) refused on without the tube, (\d+) nothing with the main power off, (\d+) on, (\d+) off \(its lines off and used off\); (\d+) poster read with the "
                          r"keypad's number; (\d+) keypad shown on, (\d+) wrong number calling nothing, (\d+) right number calling the Meteor Police \((\d+) film played as recorded, (\d+) "
                          r"events, back where they stood\); their time (\d+) ticks: (\d+) with the dungeon shut \(nothing, called again\), (\d+) kept through a save and reload, (\d+) with its "
                          r"doors open \(the badge left, taken\), (\d+) not called again after \(its line, no keypad\); (\d+) tube taken out again \(the radio off\); (\d+) keypad over once where its place "
                          r"could not be shown again \(someone else played, called\)", output)
        if all((worlds/f'maniac-{r}.svw').exists() and (worlds/f'maniac-{r}.svw').stat().st_size > 0 for r in (3, 4, 21, 32, 43)) and \
                (not radio or any(radio.group(k) != '1' for k in list(range(1, 14)) + list(range(16, 22))) or int(radio.group(14)) < 1 or int(radio.group(15)) < 18000):
            raise SystemExit('FAIL: the radio and the Meteor Police (export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
        if radio and radio.group(12) == '1':
            print('PASS: the radio: its tube taken from the old radio and put in its socket only by Bernard (refused to another kid as recorded); on only with the tube in '
                  'and the main power on, off, its lines; the wanted poster\'s number the keypad\'s; on, its keypad: a wrong number calls nothing, the right one the Meteor '
                  f'Police: their film as recorded ({radio.group(14)} events), back where they stood; {radio.group(15)} ticks later with the dungeon shut nothing, called again, '
                  'kept through a save and reload; with its doors open the badge left there, taken; not called again after (its line, no keypad); the tube taken out again, the radio off; '
                  'where it was used from not shown again, the keypad over once, called all the same')
        # (From 0263) The Meteor Police taking the meteor and the ending it
        # opens, from afresh: before (no call, or their time with the dungeon
        # shut) the Purple Meteor in the lab (room 51) and its thing there, the
        # radio's keypad its answer used on, the lab's switch turned off as its
        # own script answers; at their time with both doors open the meteor
        # taken (kept through a save and reload): the lab without the Purple
        # Meteor (nobody bringing it in, but played), its thing untouchable,
        # the radio's line instead of its keypad, Dr Fred's lab (room 30) and
        # the front door (room 1) places still; then the switch turned off:
        # Dr Fred's film (his lab), then the ending's (the front door) at once,
        # each as recorded, back where they stood, not again; each skipped by a
        # tap; Dr Fred's film's place not shown again as it ends, over once.
        # (From 0264) The ending's film left before its end (another played,
        # the app stopped meanwhile): the switch still on, both films again.
        # (From 0266) Before, the switch Dr Fred's other film (the meteor still
        # there), nothing following; turned off first (kept through a save and
        # reload); the ending seen once for good, kept (the state's "SVS7"):
        # never again, from off or on; an older state (SVS6) read with none
        # seen. (From 0268) The switch's script runs only from on, as the
        # original's: from off nothing, before they took the meteor or after
        # (turned off first, the ending's way through it gone); on again, its
        # film again.
        ending = re.search(r"selftest ending: (\d+) before the Meteor Police took the meteor \(the Purple Meteor in the lab, its thing there, the radio's keypad its answer, the switch "
                           r"Dr Fred's other film \((\d+) events\), back where they stood, nothing following, nothing from off, again from on\); (\d+) turned off first, kept through a "
                           r"save and reload, then once they took the meteor nothing from off, on again Dr Fred's film and the ending's, seen kept through a save and reload, never again; "
                           r"(\d+) taken at their time with the "
                           r"dungeon's doors open \(not with them shut\), kept through a save and reload; (\d+) lab without the Purple Meteor after \(its thing untouchable, the radio's line "
                           r"instead of its keypad, Dr Fred's lab and the front door places still\); the switch: (\d+) played Dr Fred's film \((\d+) events\) then the ending's at once "
                           r"\((\d+) events\), back where they stood, not again \(from off or on, through a save and reload\); (\d+) an older state \(SVS6\) read with none seen, damaged "
                           r"ones let go; (\d+) skipped by a tap, the ending following; (\d+) over once where the place it was shown from could not be shown again; (\d+) the ending's left "
                           r"before its end, the switch still on \(Dr Fred's film again\)", output)
        if all((worlds/f'maniac-{r}.svw').exists() and (worlds/f'maniac-{r}.svw').stat().st_size > 0 for r in (1, 4, 21, 30, 51)) and \
                (not ending or any(ending.group(k) != '1' for k in (1, 3, 4, 5, 6, 9, 10, 11, 12)) or any(int(ending.group(k)) < 1 for k in (2, 7, 8))):
            raise SystemExit('FAIL: the Meteor Police taking the meteor, and the ending through the lab\'s switch (export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
        if ending and ending.group(6) == '1':
            print('PASS: the Meteor Police take the meteor only with both dungeon doors open at their time, kept through a save and reload: the lab without the Purple Meteor '
                  '(nobody bringing it in), its thing untouchable, the radio\'s line instead of its keypad; then the lab\'s switch plays Dr Fred\'s film '
                  f'({ending.group(7)} events) and the ending\'s at once ({ending.group(8)} events), back where they stood, never again (seen once, kept); each skipped by a tap; '
                  'Dr Fred\'s film over once where the place it was shown from could not be shown again; the ending\'s left before its end, the switch still on, '
                  f'both films again; before, the switch Dr Fred\'s other film ({ending.group(2)} events), nothing from off (as the original\'s script); turned off first, '
                  'nothing from off once they took the meteor; an older state read with none seen')
        # (From 0274) What one thing's answer gives the kid, as the mansion's
        # own scripts give it (its export version 42 records it): each such
        # record played, the thing given carried; the cassette taken back out
        # of each of the three decks (not lost), the record taken off the
        # Victrola the one put on, the package's stamps pulled off, the radio's
        # batteries given once it is picked up and opened carried. Each verb
        # of a pair a thing does not answer while it answers the other
        # (open and close, on and off, push and pull): nothing changed, as its
        # game; the lab's switch turned on, from on and off: nothing.
        given = re.search(r"selftest given: (\d+) of (\d+) records of one thing of the mansion's giving another as its own scripts give it, each carried \((\d+) in a picture its game "
                          r"never has it touchable in\); the cassette taken back out of (\d+) of 3 decks, not lost; the record taken off the Victrola (\d+) of 2 as the one put on; "
                          r"the package's stamps (\d+) pulled off; the radio's batteries (\d+) given opened carried; (\d+) of (\d+) verbs a thing does not answer of its pair "
                          r"\((\d+) things away\) as its game, nothing changed; "
                          r"the lab's switch turned on (\d+), from on and off, nothing", output)
        if mansion >= 42 and (worlds/'maniac-1.svw').exists():
            exported = lambda *rooms: all((worlds/f'maniac-{r}.svw').exists() and (worlds/f'maniac-{r}.svw').stat().st_size > 0 for r in rooms)
            if not given or int(given.group(2)) < 20 or int(given.group(1)) + int(given.group(3)) != int(given.group(2)) or \
                    (exported(3, 5, 17, 20) and given.group(4) != '3') or (exported(17, 20) and given.group(5) != '2') or (exported(1) and given.group(6) != '1') or \
                    (exported(2) and given.group(7) != '1') or int(given.group(9)) < 20 or int(given.group(8)) + int(given.group(10)) != int(given.group(9)) or \
                    (exported(30, 51) and given.group(11) != '1'):
                raise SystemExit('FAIL: what one thing\'s answer gives as the mansion\'s own scripts give it, or a verb a thing does not answer (export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
            print(f"PASS: {given.group(1)} of {given.group(2)} answers of one mansion thing giving another, each carried ({given.group(3)} in a picture never touchable); the cassette back out of "
                  f"{given.group(4)} decks, not lost; the record off the Victrola the one put on ({given.group(5)} of 2); the package's stamps pulled off; the radio's batteries opened "
                  f"carried; {given.group(8)} of {given.group(9)} verbs a thing does not answer of its pair nothing changed ({given.group(10)} away); the lab's switch turned on: nothing")
        # (From 0278) What an answer hands on to another thing, as the
        # mansion's sentence script runs it next (its export version 43
        # records it): every such record played as those verbs used there by
        # a player; the tape in each deck turning it on and off (its line the
        # deck's with the tape in), taken out refused while on (but room
        # 20's); the record on the Victrola playing and stopped, refused taken
        # off while it plays; the radio opened where it lies picked up, its
        # batteries given, not again; the package pulled at the front door
        # picked up, its stamps given, refused again, and with them picked off
        # first; the film and the chainsaw carried answered as their scripts.
        if mansion >= 43 and (worlds/'maniac-1.svw').exists():
            there = lambda *rooms: all((worlds/f'maniac-{r}.svw').exists() and (worlds/f'maniac-{r}.svw').stat().st_size > 0 for r in rooms)
            if not handed or int(handed.group(2)) < 40 or int(handed.group(1)) + int(handed.group(3)) != int(handed.group(2)) or int(handed.group(4)) > 4 or \
                    int(handed.group(5)) < int(handed.group(1)) or (there(3, 5, 17, 20) and (handed.group(6) != '3' or handed.group(7) != '1' or handed.group(8) != '2')) or \
                    (there(17, 20) and handed.group(9) != '1') or (there(1, 2) and (handed.group(10) != '1' or handed.group(11) != '1' or handed.group(12) != '1')) or \
                    (there(1, 2, 7) and handed.group(13) != '2'):
                raise SystemExit('FAIL: what an answer hands on to another thing, or what the mansion\'s scripts read of what was done (export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
            print(f"PASS: {handed.group(1)} of {handed.group(2)} answers of the mansion's handing a verb on to another as its sentence script runs it, as those verbs used there ({handed.group(3)} away, "
                  f"{handed.group(4)} doing nothing there either); the tape in {handed.group(6)} decks turning it on and off (from across the place too), {handed.group(8)} refused taken out while on; the Victrola played and "
                  f"stopped by its record, its record refused while it plays; the radio picked up opened where it lies, its batteries not given again; the package picked up pulled, its stamps "
                  f"not given again ({handed.group(12)} picked off first); {handed.group(13)} carried answered as their scripts")
            # (From 0278) What the package and the radio keep inside them:
            # opened again where they gave it, not given again; a state kept
            # before 0278 (the stamps and the batteries shown taken out by
            # the pick-up then, neither given) read back: given once; with
            # the envelope stamped, the package refusing still.
            inside = re.search(r"selftest inside: (\d+) of 2 opened again where they gave what they keep inside \(the radio nothing, the package its refusal\); a state kept before 0278: "
                               r"(\d+) the package's stamps and the radio's batteries given once, (\d+) the package refusing with the envelope stamped", output)
            if there(1, 2) and (not inside or inside.group(1) != '2' or inside.group(2) != '1' or inside.group(3) != '1'):
                raise SystemExit('FAIL: what the package or the radio keeps inside it given again, or not given from a state kept before 0278\n' + output[-2000:])
            if inside:
                print(f"PASS: the radio and the package opened again where they gave what they keep inside, nothing given again ({inside.group(1)} of 2); a state kept before 0278 "
                      f"read back: the stamps and the batteries given once ({inside.group(2)}), the package refusing with the envelope stamped ({inside.group(3)})")
        # (From 0282) What the mansion's cassette records and which record is
        # on the Victrola, kept (its export version 44's things file, "SVOB",
        # records the answers that read or leave them and what the scripts
        # they start do later): record 32 recorded in either order and played
        # in the living room, the vase, the windows and the chandelier broken
        # in their time, the key in it picked up and unlocking the dungeon's
        # door, the deck and the Victrola stopping on their own; the old record
        # breaking nothing and never stopping itself; a blank cassette's line;
        # turned off in time, nothing broken; on again, from the start; the
        # main power off; room 9's light pulled as its place's lights are; a
        # state kept before 0282 with its record on read so. Saved and loaded
        # between steps.
        if mansion >= 44 and (worlds/'maniac-1.svw').exists():
            there = lambda *rooms: all((worlds/f'maniac-{r}.svw').exists() and (worlds/f'maniac-{r}.svw').stat().st_size > 0 for r in rooms)
            recorded = re.search(r"selftest recorded: (\d+) of 2 chains of record 32 recorded .*?\((\d+) of 2 unlocking the dungeon's door\).*?; (\d+) the old record recorded and played.*?; "
                                 r"(\d+) a blank cassette's line in two decks; (\d+) turned off in time, nothing broken, (\d+) turned on again from the start; (\d+) the main power off.*?; "
                                 r"(\d+) of 2 room 9's light pulled off and on as it is; (\d+) a state kept before 0282 read with its record on", output)
            if there(3, 4, 5, 8, 9, 17, 20) and (not recorded or recorded.groups() != ('2', '2', '1', '1', '1', '1', '1', '2', '1')):
                raise SystemExit('FAIL: what the mansion\'s cassette recorded, the record on the Victrola, or what playing them breaks, not as its scripts (export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
            if recorded:
                print(f"PASS: record 32 recorded on the cassette ({recorded.group(1)} of 2 orders) and played: the vase, the living room's windows and chandelier broken in their time, the key "
                      f"in it picked up unlocking the dungeon's door ({recorded.group(2)}), the deck and the Victrola stopping on their own; the old record breaking nothing, never stopping; "
                      f"a blank cassette's line; turned off in time, nothing broken; on again from the start; the main power off; room 9's light pulled as its lights are "
                      f"({recorded.group(8)} of 2); a state kept before 0282 read with its record on; saved and loaded between steps")
        # (From 0282) The tape played again once the old rusty key is
        # carried: the key not drawn under the chandelier again; a record put
        # on the Victrola while one is on refused, as its script refuses it
        # (the mansion's export version 45 records the refusal), the first
        # given back taken off.
        if mansion >= 44 and (worlds/'maniac-1.svw').exists():
            there = lambda *rooms: all((worlds/f'maniac-{r}.svw').exists() and (worlds/f'maniac-{r}.svw').stat().st_size > 0 for r in rooms)
            again = re.search(r"selftest recorded again: (\d+) the tape played again once the old rusty key is carried, the key not drawn where it lay; (\d+) of (\d+) a record put on "
                              r"the Victrola while one is on refused, the first given back taken off", output)
            if there(3, 4, 5, 8, 9, 17, 20) and (not again or again.group(1) != '1' or again.group(2) != again.group(3) or (mansion >= 45 and again.group(3) != '1')):
                raise SystemExit('FAIL: the key drawn again once carried, or a second record put on the Victrola not refused (export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
            if again:
                print(f"PASS: the tape played again once the key is carried, the key not drawn where it lay ({again.group(1)}); a second record put on the Victrola refused, "
                      f"the first given back ({again.group(2)} of {again.group(3)})")
        # (From 0286) The mansion's music, as a player has it (its export
        # version 47's things file, "SVOC"): the piano answering anyone but Syd
        # or Razor with their line, recorded by each of them with the recorder
        # on, with the Victrola on turning it off first; the Green Tentacle
        # hearing its tape on his stereo (his lines, his demo tape shown, the
        # cassette kept), the demo tape given back as the cassette, refused by
        # the recorder and by him; three tapes given to him; the stereo with
        # him away only playing; a tape put in the stereo while on played; the
        # demo tape mailed, its reply due, waiting at the front door, a contract
        # for him read and given to him; the piano's tape's reply read and given
        # to the Purple Meteor (no ending); a blank tape's reply nothing; the
        # chandelier falling with the one played under it and away. Saved and
        # loaded between steps.
        if mansion >= 47 and (worlds/'maniac-1.svw').exists():
            there = lambda *rooms: all((worlds/f'maniac-{r}.svw').exists() and (worlds/f'maniac-{r}.svw').stat().st_size > 0 for r in rooms)
            music = re.search(r"selftest music: the piano (\d+) answered with their line for someone not Syd or Razor, (\d+) of 2 recorded by Syd and Razor \(157 at 50\) and kept, (\d+) with "
                              r"the Victrola on turned off first; the Green Tentacle (\d+) hearing its tape on his stereo .*?, (\d+) refused by the recorder and by him; (\d+) of 3 tapes given "
                              r"to him .*?; (\d+) the stereo with him away only playing; (\d+) a tape put in the stereo while on played .*?; the demo tape (\d+) put in the envelope, .*?, (\d+) a "
                              r"contract for him read and given to him; (\d+) the piano's tape's reply .*?; (\d+) a blank tape's reply nothing; (\d+) of 2 the chandelier falling", output)
            if there(1, 2, 3, 4, 5, 8, 9, 17, 20, 51) and (not music or music.groups() != ('1', '2', '1', '1', '1', '3', '1', '1', '1', '1', '1', '1', '2')):
                raise SystemExit('FAIL: the mansion\'s music not as its scripts (the piano, the Green Tentacle, his demo tape, the cassette mailed and its reply, the chandelier\'s line; '
                                 'export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
            if music:
                print("PASS: the mansion's music as its scripts: the piano (anyone else's line; recorded by Syd and by Razor; the Victrola turned off first), the Green Tentacle hearing "
                      "its tape (his lines, his demo tape, the cassette kept), three tapes given to him, the stereo with him away, a tape put in the stereo while on played, "
                      "the demo tape mailed (its reply, a contract for him read and given), the piano's tape's reply given to the Purple Meteor (no ending), a blank tape's "
                      "reply nothing, the chandelier's line under it and not away; saved and loaded between steps")
        # (From 0286) The original's endings (its script 63), each its main way
        # as a player has it from afresh, as far as this engine plays it: the
        # Meteor Police's reached (the radio's tube by Bernard, the radio on, its
        # call, the key down the drained pool and the dungeon's outer door; from
        # 0287 the arcade's wires fixed in the dark, Dr Fred's high score seen,
        # the inner door's code; the meteor taken; from 0287 the badge given to
        # the Purple Tentacle and the lab's door by its card key, walked through;
        # the switch's films, the ending seen); the book contract's as far as
        # its reply (the manuscript retyped by Wendy not kept: none posted
        # back); the Edsel's as far as the meteor in the lab (from 0287 walked
        # up: the Green Tentacle's friend saved from the Purple Tentacle, the
        # code, the card key; refused: Dr Fred's cut-scene's value not kept).
        # From 0288 (the mansion's export version 50) the other two end to end
        # too, saved and loaded between steps: the book contract's (the
        # manuscript retyped by Bernard then Wendy and read, posted, the
        # publisher's reply a book contract read and taken, the way up with the
        # contract sending the Purple Tentacle away, given to the Purple Meteor:
        # cut short and kept, then his film and the ending's seen, the contract
        # used up, not again) and the Edsel's (the way up as from 0287, the
        # meteor refused, Dr Fred's other film, the meteor picked up, the yellow
        # key and the trunk, the launch's films and the ending seen, not again).
        if mansion >= 50 and (worlds/'maniac-1.svw').exists():
            there = lambda *rooms: all((worlds/f'maniac-{r}.svw').exists() and (worlds/f'maniac-{r}.svw').stat().st_size > 0 for r in rooms)
            endings = re.search(r"selftest endings: the Meteor Police's (\d+) reached \((\d+) of 11 steps.*?; the book contract's (\d+) reached \((\d+) of 7 steps.*?; "
                                r"the Edsel's (\d+) reached \((\d+) of 11 steps", output)
            if there(1, 2, 3, 4, 6, 7, 8, 9, 15, 16, 18, 20, 21, 22, 26, 27, 29, 30, 31, 39, 42, 46, 48, 51) and (not endings or endings.groups() != ('1', '11', '1', '7', '1', '11')):
                raise SystemExit('FAIL: the endings not reached as a player plays them (the Meteor Police\'s, the book contract\'s and the Edsel\'s, each up through the inner '
                                 'door\'s code, past the Purple Tentacle and the lab\'s door; export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
            if endings and endings.groups() == ('1', '11', '1', '7', '1', '11'):
                print("PASS: the endings as a player plays them from afresh, saved and loaded between steps: the Meteor Police's (the radio's tube, its call, the pool's key, the "
                      "dungeon's doors, the wires, the high score, the inner door's code, the meteor taken, the badge to the Purple Tentacle, the card key, the switch's films, "
                      "the ending seen); the book contract's (the manuscript retyped by Wendy, posted, the publisher's reply read and taken, the Purple Tentacle sent away by it, "
                      "given to the Purple Meteor: his film and the ending's, the contract used up); the Edsel's (the way up, Dr Fred's other film, the meteor picked up, the key "
                      "and the trunk, the launch's films and the ending); none again once seen")
        # (From 0287) The way up to the lab, as the original's scripts keep it
        # (its export version 48): the dungeon's inner door locked (its keypad,
        # its code none before Dr Fred has played Meteor Mess), the arcade's
        # wires fixed only in the dark with the flashlight on, Dr Fred's time
        # (waiting with the power off or the one played in the arcade), his
        # high score seen with the quarter, the keypad right and wrong (both
        # sides, shut again, opened from room 31), the Purple Tentacle guarding
        # his door (barred; the badge or a book contract sending him off for
        # good; the Green Tentacle's friend saved), the lab's door by its card
        # key only, the garage's slab only from the lab. Saved and loaded
        # between steps.
        if mansion >= 48 and (worlds/'maniac-1.svw').exists():
            there = lambda *rooms: all((worlds/f'maniac-{r}.svw').exists() and (worlds/f'maniac-{r}.svw').stat().st_size > 0 for r in rooms)
            lab = re.search(r"selftest lab: (\d+) the dungeon's inner door .*?; (\d+) the arcade's wires .*?; (\d+) his time .*?; (\d+) his high score .*?; (\d+) the inner door's keypad "
                            r".*?; (\d+) the Purple Tentacle guarding .*?; (\d+) the badge .*?; (\d+) a book contract likewise; (\d+) the Green Tentacle's friend .*?; (\d+) the lab's door "
                            r".*?; (\d+) the garage's cement slab", output)
            if there(4, 7, 8, 9, 15, 16, 18, 20, 26, 30, 31, 39, 51) and (not lab or lab.groups() != ('1',) * 11):
                raise SystemExit('FAIL: the way up to the lab not as its scripts keep it (the inner door\'s keypad and code, the wires, Dr Fred\'s time and high score, the Purple '
                                 'Tentacle, the lab\'s door, the slab; export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
            if lab:
                print("PASS: the way up to the lab as its scripts keep it: the inner door locked (its keypad, no code before Dr Fred has played), the wires fixed in the dark, "
                      "his time and his high score, the keypad right and wrong (both sides, shut again, opened from room 31), the Purple Tentacle guarding (the badge, a book "
                      "contract, the Green Tentacle's friend), the lab's door by its card key, the garage's slab from the lab only; saved and loaded between steps")
        # (From 0287) The same with everyone out (its export version 49): the
        # Purple Tentacle at his post though the wanderers sent him away, one of
        # his name they have there (Day of the Tentacle's, where installed)
        # stepping aside for him, the badge given there, no guard for that one
        # played; no guard where he cannot be shown (his door not barred for
        # good); the Green Tentacle met away from his room given his contract
        # (his friend made, then saved); the arcade's wires fixed with the tools
        # used on them in the dark, as with Fix.
        if mansion >= 49 and (worlds/'maniac-1.svw').exists():
            there = lambda *rooms: all((worlds/f'maniac-{r}.svw').exists() and (worlds/f'maniac-{r}.svw').stat().st_size > 0 for r in rooms)
            more = re.search(r"selftest lab more: (\d+) the Purple Tentacle at his post .*?; (\d+) no guard where he cannot be shown .*?; (\d+) the Green Tentacle given his contract "
                             r".*?; (\d+) the arcade's wires fixed with the tools", output)
            if there(4, 7, 8, 9, 12, 13, 15, 16, 18, 20, 26, 30, 31, 39, 51) and (not more or more.groups() != ('1',) * 4):
                raise SystemExit('FAIL: the way up to the lab not as its scripts keep it with everyone out (the Purple Tentacle at his post, one of his name standing aside; no guard '
                                 'not to be shown; the Green Tentacle away from his room; the wires by Use; export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
            if more:
                print("PASS: the way up to the lab with everyone out: the Purple Tentacle at his post (one of his name the wanderers had there stepping aside), the badge given "
                      "there; no guard where he cannot be shown; the Green Tentacle given his contract away from his room, his friend saved; the wires fixed by Use as by Fix")
        # (From 0289) The dungeon's inner door's Unlock shows its keypad as its
        # Open does, with any thing, shut (its export version 51: before, "That
        # doesn't seem to work."), and the quarter in Meteor Mess before Dr Fred
        # has played shows its score screen with none of its high scores (before,
        # nothing), only with the arcade's wires fixed, its line with the power
        # off, as their scripts.
        if mansion >= 51 and (worlds/'maniac-1.svw').exists():
            there = lambda *rooms: all((worlds/f'maniac-{r}.svw').exists() and (worlds/f'maniac-{r}.svw').stat().st_size > 0 for r in rooms)
            score = re.search(r"selftest lab keypad and score: (\d+) Unlock on the dungeon's inner door .*?; (\d+) the quarter in Meteor Mess before he has played", output)
            if there(4, 7, 8, 9, 15, 16, 18, 20, 26, 30, 31, 39, 51) and (not score or score.groups() != ('1', '1')):
                raise SystemExit('FAIL: the inner door\'s Unlock not showing its keypad as its Open does, or Meteor Mess before Dr Fred has played not showing its score screen '
                                 'with no high score (export the mansion again: tools/export_worlds.py)\n' + output[-2000:])
            if score:
                print("PASS: Unlock on the dungeon's inner door shows its keypad as Open does (with any thing, shut; wrong before Dr Fred has played, right after); the quarter "
                      "in Meteor Mess before he has played shows its score screen with no high score, only with the arcade's wires fixed, its line with the power off")
        # (From 0277) A verb Zak's or a later game's thing does not answer, as
        # a player chooses it: from a picture its export played it from (a
        # record of another verb from there), each verb with no record from
        # there whose plain rules would change it (its game said nothing and
        # changed nothing then, or took the one played elsewhere): nothing
        # changed, a line said; where they change nothing, their own line. From
        # the picture its place shows it in or one an answer leaves it in, one
        # never played there (Zak's room 2; Fate of Atlantis's room 17, 183 to
        # 185 past their second picture): the plain rules, but a verb of a pair
        # its script has no entry for while it answers the other in a game
        # whose own sentence changes nothing so (as 0274's mansion; its records
        # counted again: none changing it), nothing changed; not Day of the
        # Tentacle's, whose own sentence opens, closes and pulls so (recorded),
        # by the plain rules. Full Throttle's door in room 56, answered with
        # nothing at all, kicked: nothing.
        unanswered = {m.group(1): [int(x) for x in m.groups()[1:]] for m in re.finditer(
            r"selftest unanswered (.+?): (\d+) of (\d+) verbs a thing has no answer to from a picture it was played from \((\d+) away\) as its game, nothing changed, a line said; "
            r"(\d+) of (\d+) of them whose plain rules change nothing, their line; from the picture its place shows it in or an answer leaves it in, never played there: (\d+) of (\d+) by the plain rules "
            r"\((\d+) a verb of a pair its script has no entry for\), (\d+) of (\d+) a verb of a pair its script has no entry for, nothing changed; (\d+) of (\d+) records of a verb "
            r"of a pair its script has no entry for changing it", output)}
        nothing = re.search(r"selftest unanswered: (\d+) of (\d+) things answered with nothing at all kicked from their pictures 0 and 1, nothing changed", output)
        # (Each game: its title; at least so many verbs it has no answer to from
        # a picture played (with this export); whether its own sentence changes
        # nothing for a verb of a pair its script has no entry for; at least so
        # many such never played from where its place shows them, so many by
        # the plain rules never played there, and so many whose plain rules
        # change nothing. From 0285 fewer of those never played: the export
        # has the one played in the place as it starts, and answers there
        # what it did not (Zak's, Monkey Island 2's, the Last Crusade's, Day of
        # the Tentacle's); a verb of a pair Day of the Tentacle's script has
        # no entry for, by the plain rules, only in an export before 0285's.
        # From 0290 none of Zak's: its room 2, the last never played, is
        # arrived at past its cut-scene and answered.)
        later = (('zak', 'Zak McKracken', 16, True, 0, 0, 1), ('monkey', 'The Secret of Monkey Island', 15, True, 0, 0, 1), ('monkey2', 'Monkey Island 2', 5, True, 0, 0, 1),
                 ('indy3', 'Indiana Jones and the Last Crusade', 30, True, 0, 0, 1), ('atlantis', 'Indiana Jones and the Fate of Atlantis', 3, True, 0, 1, 1),
                 ('tentacle', 'Day of the Tentacle', 5, False, 0, 0, 1), ('samnmax', 'Sam & Max Hit the Road', 8, False, 0, 0, 1), ('ft', 'Full Throttle', 2, False, 0, 1, 1),
                 ('dig', 'The Dig', 0, False, 0, 0, 0), ('comi', 'The Curse of Monkey Island', 0, False, 0, 0, 1), ('loom', 'Loom', 0, False, 0, 0, 0))
        for gameid, title, least, quiet, least_quiet, least_plain, least_lines in later:
            answers = worlds/f'{gameid}-things.svo'
            if not answers.exists() or not answers.stat().st_size:
                continue
            u = unanswered.get(title)
            if not u or u[0] + u[2] != u[1] or u[3] != u[4] or u[5] != u[6] or u[8] != u[9] or u[1] < least or u[9] < least_quiet or u[6] < least_plain or u[4] < least_lines or \
                    (quiet and u[10]) or (not quiet and u[9]) or (gameid == 'tentacle' and (not u[10] or (not u[7] and not (worlds/'tentacle-v34.svx').exists()))):
                raise SystemExit(f'FAIL: {title}: a verb its thing does not answer, as its game (export {title} again: tools/export_worlds.py)\n' + output[-2000:])
            if u[1] or u[4] or u[6] or u[9]:
                print(f"PASS: {title}: {u[0]} of {u[1]} verbs a thing has no answer to from a picture it was played from nothing changed, a line said ({u[2]} away); {u[3]} whose plain "
                      f"rules change nothing their line; never played from where its place or an answer shows it: {u[5]} by the plain rules ({u[7]} a verb of a pair it has no entry "
                      f"for), {u[8]} a verb of a pair it has no entry for nothing changed; {u[10]} of {u[11]} records of such a verb changing it")
        if (worlds/'ft-56.svw').exists() and (worlds/'ft-things.svo').exists() and (not nothing or nothing.group(1) != '2' or nothing.group(2) != '2'):
            raise SystemExit('FAIL: Full Throttle\'s door in room 56, answered with nothing at all, changed when kicked\n' + output[-2000:])
        if nothing and int(nothing.group(2)):
            print(f"PASS: Full Throttle's door in room 56, answered with nothing at all: kicked from its pictures 0 and 1 ({nothing.group(1)} of {nothing.group(2)}), nothing changed")
        if effects:
            print(f"PASS: {effects.group(1)} uses of the mansion's things as their own scripts answer them (the line, the picture after, the others it sets; {effects.group(3)} of them taken, {effects.group(4)} of those read as carried; {effects.group(2)} out of reach or in a picture the game never has, {effects.group(5)} left to the plain rules: silent, or taken where not there or with no picture of its own; {effects.group(7)} taken whose pictures are the same); the fridge's food and the key under the mat inside them: untouched while shut, taken once open, gone when opened again")
        # (From 0247) Sam & Max's things as its own sentences answer (its
        # things file, from its own start): every record replayed as a player
        # uses that verb there (the line, the picture after, taken, the others
        # it sets and gives); one taken with its pointer chosen in its box.
        # From 0258 (its things file "SVO9"): taken, gone as a thing, the place
        # as its game leaves it, its box picture its own; its answers whole:
        # pictures past the second, every line in turn by who says it in their
        # colour (Max's by Max following), the things given carried by their
        # own inventory pictures (one kept through a save and a load). (From
        # 0270 a line of someone not here, Max where he is not, told over the
        # place in their colour, not said by the one played.)
        own = re.search(r"selftest Sam & Max: (\d+) of (\d+) records of (\d+) things as its own sentences answer \((\d+) away; (\d+) lines, (\d+) pictures changed, "
                        r"(\d+) taken, (\d+) given, (\d+) of them with no picture to carry\), (\d+) taken with its pointer from the box", output)
        whole = re.search(r"selftest Sam & Max whole: (\d+) taken gone as things, the place as its game leaves it, their box pictures their own; (\d+) of (\d+) answers from or to a picture past the second \((\d+) in a picture their places have not\), (\d+) of (\d+) of several lines said in turn, "
                          r"(\d+) of (\d+) lines by someone else \((\d+) by the one here its cast knows so, (\d+) told over the place, (\d+) told over the place in their colour as they are not here\), "
                          r"(\d+) of (\d+) things given carried by their own inventory pictures \((\d+) kept through a save and a load; (\d+) with none, not carried\); (\d+) lines drawn in their speakers' colours; "
                          r"(\d+) of Max's lines said by him as he follows, over him in his colour, (\d+) answer of several lines played through as time passes "
                          r"\((\d+) let go by a line said meanwhile and by another place\)", output)
        snm = worlds/'samnmax-things.svo'
        snmBytes = snm.read_bytes() if snm.exists() else b''
        snmNinth = (gzip.decompress(snmBytes) if snmBytes[:2] == b'\x1f\x8b' else snmBytes)[:4] in (b'SVO9', b'SVOA')  # (from 0267 "SVOA": SVO9 and more)
        # (Its export from 0258, version 27, writes "SVO9": one exported so
        # that is not, is not whole.)
        if any((worlds/f'samnmax-v{v}.svx').exists() for v in (27, 28, 29)) and snm.exists() and not snmNinth:
            raise SystemExit('FAIL: Sam & Max\'s things file not "SVO9" though exported as version 27 (export Sam & Max again: tools/export_worlds.py)')
        if snm.exists() and snm.stat().st_size and (not own or int(own.group(2)) < 1000 or int(own.group(1)) + int(own.group(4)) != int(own.group(2))
                                                    or int(own.group(7)) < 20 or own.group(10) != '1'):
            raise SystemExit('FAIL: Sam & Max\'s things as its own sentences answer (export Sam & Max again: tools/export_worlds.py)\n' + output[-2000:])
        if snmNinth and (not whole or not own or whole.group(1) != own.group(7) or int(whole.group(3)) < 10 or int(whole.group(2)) + int(whole.group(4)) != int(whole.group(3))
                         or int(whole.group(6)) < 50 or whole.group(5) != whole.group(6) or int(whole.group(8)) < 100 or whole.group(7) != whole.group(8) or whole.group(9) == '0'
                         or whole.group(10) == '0' or whole.group(11) == '0' or int(whole.group(13)) < 2 or whole.group(12) != whole.group(13) or whole.group(14) != '1' or whole.group(15) != '0'
                         or int(whole.group(16)) < 1000 or whole.group(17) != '1' or whole.group(18) != '1' or whole.group(19) != '1'):
            raise SystemExit('FAIL: Sam & Max\'s answers whole: pictures past the second, its lines by who says them, things given by their own pictures (export Sam & Max again: tools/export_worlds.py)\n' + output[-2000:])
        if own and int(own.group(2)):
            print(f"PASS: {own.group(1)} of {own.group(2)} answers of Sam & Max's {own.group(3)} things as its own sentences give them ({own.group(5)} lines, {own.group(6)} pictures changed, "
                  f"{own.group(7)} taken, {own.group(8)} giving another, {own.group(9)} of those with no picture to carry; {own.group(4)} away); one taken with its pointer from its box")
        if whole and snmNinth:
            print(f"PASS: Sam & Max's answers whole: {whole.group(1)} taken gone as things, the place as its game leaves it, their box pictures their own; {whole.group(2)} from or to a picture "
                  f"past the second; {whole.group(5)} of several lines said in turn; {whole.group(7)} lines by someone else ({whole.group(9)} by the one here its cast knows so, {whole.group(10)} told "
                  f"over the place, {whole.group(11)} told over the place in their colour as they are not here), {whole.group(16)} drawn in their speakers' colours; {whole.group(12)} things given carried by their "
                  "own inventory pictures, kept through a save and a load; Max's line said by Max following, over him in his colour; an answer of several lines played through as time passes, "
                  "the rest let go by a line said meanwhile or another place")
        # (From 0256) Zak's likewise (its things file): every record of one
        # thing replayed as a player uses that verb there (its panel's verbs
        # but What is and Give), its place entered again after each one
        # taken; one taken with its panel's verb, seen in its slots; each of
        # two (Use: a thing carried first, then one here or carried too) as
        # its own sentence answers, used up as it uses up.
        zak = re.search(r"selftest Zak McKracken: (\d+) of (\d+) records of one thing of (\d+) things as its own sentences answer \((\d+) away; (\d+) lines, (\d+) pictures changed, "
                        r"(\d+) taken \((\d+) places entered again as left\), (\d+) given, (\d+) of them with no picture to carry\), (\d+) taken with its panel, in its slots; "
                        r"(\d+) of (\d+) of two things \(Use\) as its own sentence answers \((\d+) not tried; (\d+) a usual answer, (\d+) using up, (\d+) with both carried\)", output)
        answers = worlds/'zak-things.svo'
        if answers.exists() and answers.stat().st_size and gzip.decompress(answers.read_bytes())[:4] != b'SVO3' and \
                (not zak or int(zak.group(2)) < 4000 or int(zak.group(1)) + int(zak.group(4)) != int(zak.group(2)) or int(zak.group(7)) < 20
                 or zak.group(8) != zak.group(7) or zak.group(11) != '1' or int(zak.group(13)) < 1000 or int(zak.group(12)) + int(zak.group(14)) != int(zak.group(13))
                 or int(zak.group(16)) < 1 or int(zak.group(17)) < 1):
            raise SystemExit('FAIL: Zak\'s things as its own sentences answer (export Zak again: tools/export_worlds.py)\n' + output[-2000:])
        if zak and int(zak.group(2)):
            print(f"PASS: {zak.group(1)} of {zak.group(2)} answers of Zak's {zak.group(3)} things as its own sentences give them ({zak.group(5)} lines, {zak.group(6)} pictures changed, "
                  f"{zak.group(7)} taken, each place entered again as left; {zak.group(4)} away); one taken with its panel's verb, in its slots; "
                  f"{zak.group(12)} of {zak.group(13)} Use of two as its sentences give them ({zak.group(15)} usual answers, {zak.group(16)} using up, {zak.group(17)} both carried; {zak.group(14)} not tried)")
        # (From 0270) Who says a line, whatever the things files hold, in a
        # place of a later game with someone of its own there: the one played
        # their own, someone here over them, someone hidden, of a costume nobody
        # here wears or of none told over the place in their colour, never by
        # the one played; each drawn so.
        ruled = re.search(r"selftest speakers: (\d+) places where who says a line is as its record has it", output)
        later = any(not f.name.startswith(('maniac-', 'zak-')) for f in worlds.glob('*.svw'))
        if later and (not ruled or ruled.group(1) == '0'):
            raise SystemExit('FAIL: who says a line here (the one played, someone here, else told over the place in their colour)\n' + output[-2000:])
        if ruled:
            print(f"PASS: who says a line in {ruled.group(1)} place: someone not here, hidden or unknown told over the place in their colour, not by the one played")
        # (From 0251) The Dig's and Full Throttle's likewise (their things
        # files): every record replayed as a player uses that verb there (The
        # Dig's tap; Full Throttle's coin: eyes, teeth, hand, boot); one taken
        # through the game's own controls (the tap; the coin's hand) and seen
        # in its box; The Dig's way down kept untouchable under its hatch until
        # the hatch's answer shows it, then gone through with a tap. (From
        # 0253) Day of the Tentacle's likewise, each of its verb panel's verbs
        # but giving, each answer as the kid of that place's time gives it;
        # one taken with its verb chosen on the panel, seen among its things.
        # (From 0254) Monkey Island's and Monkey Island 2's so too, each of
        # their panels' verbs but giving (Monkey Island 2's drinks at its bar,
        # taken by its game with no picture of their own, refused).
        # (From 0255) What another's answer shows that the game keeps
        # untouchable all the same is no thing then: Full Throttle's room 131,
        # 573.
        # (From 0261) Fate of Atlantis's and the Last Crusade's so too, each of
        # their panels' verbs on a thing alone (not giving, using one their
        # games want a second thing for, the Last Crusade's talking or what
        # is), their answers whole. (From 0262) The Curse of Monkey Island's
        # likewise, its coin's hand, skull and parrot; one taken with its coin's
        # hand, seen in its chest; four things its answers show kept
        # untouchable, as its game keeps them.
        for title, gameid, most, least_taken in (('The Dig', 'dig', 150, 10), ('Full Throttle', 'ft', 800, 2), ('Day of the Tentacle', 'tentacle', 3000, 40),
                                                 ('The Secret of Monkey Island', 'monkey', 6000, 40), ('Monkey Island 2', 'monkey2', 5000, 40),
                                                 ('Indiana Jones and the Fate of Atlantis', 'atlantis', 3000, 40), ('Indiana Jones and the Last Crusade', 'indy3', 3500, 30),
                                                 ('The Curse of Monkey Island', 'comi', 2000, 20)):
            own = re.search(re.escape(f"selftest {title}: ") + r"(\d+) of (\d+) records of (\d+) things as its own sentences answer \((\d+) away; (\d+) lines, (\d+) pictures changed, "
                            r"(\d+) taken, (\d+) given, (\d+) of them with no picture to carry; ([^)]*)\), (\d+) taken with its own controls, in its box; "
                            r"(\d+) of (\d+) doors its game keeps untouchable shown by another's answer, then gone through; (\d+) of (\d+) things it keeps untouchable all the same shown so, not things; "
                            r"whole: (\d+) of several lines said in turn, (\d+) lines by someone else, (\d+) from or to a picture past the second \((\d+) in a picture their places have not\)", output)
            # (From 0258, its things file "SVO9" where its answers need it: its
            # lines in turn by who says them, pictures past the second (The
            # Dig's and Day of the Tentacle's, each also from the picture it
            # is found in and those answers leave it in).)
            least_past = {'dig': 8, 'tentacle': 40}
            # (The Monkey Islands' one line, with who says it: not the place's
            # own talk after it.)
            least_several = most_several = {'monkey': 0, 'monkey2': 0}
            answers = worlds/f'{gameid}-things.svo'
            answerBytes = answers.read_bytes() if answers.exists() else b''
            ninth = (gzip.decompress(answerBytes) if answerBytes[:2] == b'\x1f\x8b' else answerBytes)[:4] in (b'SVO9', b'SVOA')  # (from 0267 "SVOA": SVO9 and more)
            ninthVersion = {'monkey2': 28, 'indy3': 26}.get(gameid, 27)
            if (worlds/f'{gameid}-v{ninthVersion}.svx').exists() and answers.exists() and not ninth:
                raise SystemExit(f'FAIL: {title}\'s things file not "SVO9" though exported as version {ninthVersion} (export {title} again: tools/export_worlds.py)')
            if answers.exists() and answers.stat().st_size and (not own or int(own.group(2)) < most or int(own.group(1)) + int(own.group(4)) + int(own.group(19)) != int(own.group(2))
                                                              or int(own.group(7)) < least_taken or own.group(11) != '1' or own.group(12) != own.group(13)
                                                              or (gameid == 'dig' and own.group(13) == '0') or own.group(14) != own.group(15)
                                                              or (gameid == 'ft' and (worlds/'ft-131.svw').exists() and own.group(15) == '0')
                                                              or (gameid == 'comi' and (worlds/'comi-65.svw').exists() and own.group(15) == '0')
                                                              or (ninth and (int(own.group(16)) < least_several.get(gameid, 1) or int(own.group(16)) > most_several.get(gameid, int(own.group(16))) or own.group(17) == '0' or int(own.group(18)) < least_past.get(gameid, 0)))):
                raise SystemExit(f'FAIL: {title}\'s things as its own sentences answer (export {title} again: tools/export_worlds.py)\n' + output[-2000:])
            # (From 0267, its things file "SVOA" (its export from 0267's
            # version on writes it): what its answers make touchable or
            # untouchable, as its game's scripts set or clear their classes,
            # kept so, each a thing then or not (the thing itself too).)
            touches = re.search(re.escape(f"selftest {title} touches: ") + r"(\d+) of (\d+) made touchable or untouchable by its answers kept so; (\d+) of (\d+) made touchable things then, "
                                r"(\d+) of (\d+) made untouchable not things then; (\d+) records of things it starts untouchable answered once made touchable", output)
            tenth = (gzip.decompress(answerBytes) if answerBytes[:2] == b'\x1f\x8b' else answerBytes)[:4] == b'SVOA'
            tenthVersion = {'monkey': 30, 'monkey2': 31, 'tentacle': 29, 'indy3': 27}.get(gameid, 28)
            if (worlds/f'{gameid}-v{tenthVersion}.svx').exists() and answers.exists() and not tenth:
                raise SystemExit(f'FAIL: {title}\'s things file not "SVOA" though exported as version {tenthVersion} (export {title} again: tools/export_worlds.py)')
            if tenth and (not touches or touches.group(1) != touches.group(2) or touches.group(2) == '0' or touches.group(3) != touches.group(4) or touches.group(5) != touches.group(6)):
                raise SystemExit(f'FAIL: what {title}\'s answers make touchable or untouchable (export {title} again: tools/export_worlds.py)\n' + output[-2000:])
            if touches:
                print(f"PASS: what {title}'s answers make touchable or untouchable as its scripts leave it: {touches.group(1)} kept so; {touches.group(3)} made touchable things then, "
                      f"{touches.group(5)} made untouchable not things then; {touches.group(7)} answers of things it starts untouchable once made touchable")
            # (From 0270 who says them: someone else's over them where they are
            # here, else told over the place in their colour, never by the one
            # played (Full Throttle's bartender in room 54, Day of the Tentacle's,
            # The Dig's and The Curse's people its cast knows by another costume
            # or places elsewhere); its two things' first lines likewise, by who
            # says them as recorded (Day of the Tentacle's told over the place,
            # Monkey Island 2's people given to answering over them, where its
            # export is 0270's or later).)
            speakers = re.search(re.escape(f"selftest {title} speakers: ") + r"(\d+) lines of one thing by someone else said over them here, (\d+) by someone not here told over the place in their colour, "
                                 r"not by the one played; two things: (\d+) first lines by someone else as recorded \((\d+) over them here, (\d+) told over the place in their colour\)", output)
            least_off = {'ft': 100, 'tentacle': 50, 'dig': 10, 'comi': 50}
            spokenSince = {'tentacle': 30, 'monkey2': 32, 'atlantis': 29}
            exported = [int(m.group(1)) for m in (re.fullmatch(re.escape(gameid) + r'-v(\d+)\.svx', f.name) for f in worlds.glob(f'{gameid}-v*.svx')) if m]
            if own and int(own.group(2)) and (not speakers or (ninth and int(speakers.group(2)) < least_off.get(gameid, 0)) or int(speakers.group(3)) != int(speakers.group(4)) + int(speakers.group(5))
                                              or (gameid in spokenSince and exported and max(exported) >= spokenSince[gameid] and speakers.group(3) == '0')):
                raise SystemExit(f'FAIL: who says {title}\'s lines: someone not here told over the place in their colour, not by the one played; its two things\' by who says them '
                                 f'(export {title} again: tools/export_worlds.py)\n' + output[-2000:])
            if speakers:
                print(f"PASS: who says {title}'s lines: {speakers.group(1)} of someone else over them, {speakers.group(2)} of someone not here told over the place in their colour, not by the one played; "
                      f"two things: {speakers.group(3)} first lines by someone else as recorded ({speakers.group(4)} over them, {speakers.group(5)} over the place)")
            if own and int(own.group(2)):
                print(f"PASS: {own.group(1)} of {own.group(2)} answers of {title}'s {own.group(3)} things as its own sentences give them ({own.group(5)} lines, {own.group(6)} pictures changed, "
                      f"{own.group(7)} taken, {own.group(8)} giving another; {own.group(10)}; {own.group(4)} away); one taken with its own controls, in its box; "
                      f"{own.group(12)} door kept untouchable until another's answer shows it, then gone through; {own.group(14)} shown by another's answer, kept untouchable; "
                      f"whole: {own.group(16)} answers of several lines said in turn, {own.group(17)} lines by someone else, {own.group(18)} from or to a picture past the second ({own.group(19)} in a picture their places have not)")
        # (From 0267) Sam & Max's, Zak's and the mansion's answers that make
        # things touchable or untouchable (their things files "SVOA"), each
        # as the new engine plays it, kept so, each a thing then or not; and
        # the cases the reviews of 0251 to 0262 found, each played as a player
        # uses that verb there, its thing a thing (or not) then as the
        # original's scripts leave it: The Dig's ten made untouchable, Full
        # Throttle's four and its 573 kept untouchable though shown, Fate of
        # Atlantis's 22 and Sam & Max's 267 and 268 made touchable with no or
        # a picture change.
        t = re.search(r"selftest touches: (\d+) of (\d+) records of one thing of Sam & Max, Zak and the mansion making things touchable or untouchable as the new engine plays them "
                      r"\((\d+) away, (\d+) left to the plain rules\); (\d+) of (\d+) cases the reviews found as the original's scripts leave them", output)
        def svoa(gameid):
            f = worlds/f'{gameid}-things.svo'
            data = f.read_bytes() if f.exists() else b''
            # (From 0282 "SVOB" too: SVOA and more, the mansion's from 0282; from
            # 0286 "SVOC", the mansion's from then.)
            return (gzip.decompress(data) if data[:2] == b'\x1f\x8b' else data)[:4] in (b'SVOA', b'SVOB', b'SVOC')
        known = [g for g, room in (('dig', 19), ('dig', 20), ('dig', 31), ('dig', 34), ('dig', 49), ('dig', 56), ('dig', 61), ('dig', 65), ('dig', 68), ('dig', 75),
                                   ('ft', 50), ('ft', 54), ('ft', 54), ('ft', 115), ('ft', 131), ('atlantis', 1), ('samnmax', 25), ('samnmax', 25))
                 if svoa(g) and (worlds/f'{g}-{room}.svw').exists()]
        if not t or int(t.group(1)) + int(t.group(3)) + int(t.group(4)) != int(t.group(2)) or t.group(5) != t.group(6) or int(t.group(6)) != len(known) or \
                any(svoa(g) and t.group(2) == '0' for g in ('samnmax', 'zak', 'maniac')):
            raise SystemExit(f'FAIL: what answers make touchable or untouchable ({len(known)} cases the reviews found here)\n' + output[-2000:])
        print(f"PASS: {t.group(1)} of {t.group(2)} answers of Sam & Max, Zak and the mansion making things touchable or untouchable as the new engine plays them ({t.group(3)} away, "
              f"{t.group(4)} left to the plain rules); {t.group(5)} of {t.group(6)} cases the reviews found as the original's scripts leave them")
        # (From 0260) Day of the Tentacle's and both Monkey Islands' two
        # things as their own sentences answer: each record of a thing carried
        # used with what it is used on (here, or carried too) and of one given
        # to someone here, as a player has it (most tried: not one whose first
        # has no picture to carry, one away there or someone not there), where
        # its export is 0260's or later (its marker's version from then). (From
        # 0261) Fate of Atlantis's and the Last Crusade's too (the Last
        # Crusade's fewer: fewer firsts its verb script asks "with" for).
        for title, gameid, since, least in (('Day of the Tentacle', 'tentacle', 28, 1000), ('The Secret of Monkey Island', 'monkey', 29, 1000), ('Monkey Island 2', 'monkey2', 30, 1000),
                                            ('Indiana Jones and the Fate of Atlantis', 'atlantis', 27, 1000), ('Indiana Jones and the Last Crusade', 'indy3', 26, 400)):
            exported = [int(m.group(1)) for m in (re.fullmatch(re.escape(gameid) + r'-v(\d+)\.svx', f.name) for f in worlds.glob(f'{gameid}-v*.svx')) if m]
            two = re.search(re.escape(f"selftest {title} two things: ") + r"(\d+) of (\d+) records of two things as its own sentences answer \((\d+) not tried: (\d+) with one carried that has no picture to carry, "
                            r"(\d+) away there, (\d+) nobody there; (\d+) a usual answer, (\d+) given to someone, (\d+) using up, (\d+) with both carried, (\d+) giving one with no picture to carry\)", output)
            if exported and max(exported) >= since and (worlds/f'{gameid}-things.svo').exists() and (
                    not two or int(two.group(2)) < least or int(two.group(1)) + int(two.group(3)) != int(two.group(2)) or 4 * int(two.group(1)) < 3 * int(two.group(2))
                    or two.group(7) == '0' or two.group(8) == '0'):
                raise SystemExit(f'FAIL: {title}\'s two things as its own sentences answer (export {title} again: tools/export_worlds.py)\n' + output[-2000:])
            # (From 0265: of them, given to someone where the cast puts them
            # though filed where their game has them, and setting another to a
            # picture past the second, as the new engine now reads them.)
            more = re.search(re.escape(f"selftest {title} two things: ") + r".*?\); (\d+) given to someone where the cast puts them, filed where their game has them; (\d+) setting another to a picture past the second", output)
            if two and int(two.group(2)):
                print(f"PASS: {two.group(1)} of {two.group(2)} answers of {title}'s two things as its own sentences give them (Use with what it is used on, Give to someone: "
                      f"{two.group(7)} usual answers, {two.group(8)} given to someone, {two.group(9)} using up, {two.group(10)} with both carried; not tried: {two.group(4)} with a thing carried that has no picture to carry, "
                      f"{two.group(5)} away there, {two.group(6)} with nobody there)" + (f"; {more.group(1)} given where the cast puts them, {more.group(2)} setting another past its second picture" if more else ""))
        # (From 0269) the two things of the games whose box's things are held
        # as the pointer (Sam & Max's box, The Dig's grid, Full Throttle's
        # skull, The Curse of Monkey Island's chest): each record of a thing
        # held used on a thing here or given to someone, through its own
        # controls as a player makes it (held from its box, the pointer its
        # picture, then a tap on what it is used on, walked to), where its
        # export is 0269's or later; the thing held let go by a right click,
        # the floor, the box and another place. (Full Throttle's few: its
        # things held answer alike whatever they are used on, each its usual
        # answer once; none given to someone says anything.)
        for title, gameid, since, least, given in (('Sam & Max Hit the Road', 'samnmax', 29, 400, True), ('The Dig', 'dig', 29, 400, True), ('Full Throttle', 'ft', 29, 10, False),
                                                   ('The Curse of Monkey Island', 'comi', 29, 400, True)):
            exported = [int(m.group(1)) for m in (re.fullmatch(re.escape(gameid) + r'-v(\d+)\.svx', f.name) for f in worlds.glob(f'{gameid}-v*.svx')) if m]
            held = re.search(re.escape(f"selftest {title} two things: ") + r"(\d+) of (\d+) records of two things through its own controls as its own sentences answer \((\d+) not tried: "
                             r"(\d+) with one carried that has no picture to carry, (\d+) away there, (\d+) where no tap finds it, (\d+) nobody there; (\d+) a usual answer, (\d+) given to someone, "
                             r"(\d+) using up, (\d+) of several lines, (\d+) lines by someone else, (\d+) giving one, (\d+) of them with no picture to carry\); (\d+) held drawn as the pointer, "
                             r"(\d+) let go by a right click, the floor, the box and another place", output)
            if exported and max(exported) >= since and (worlds/f'{gameid}-things.svo').exists() and (
                    not held or int(held.group(2)) < least or int(held.group(1)) + int(held.group(3)) != int(held.group(2)) or 10 * int(held.group(1)) < 9 * int(held.group(2))
                    or held.group(8) == '0' or (given and held.group(9) == '0') or int(held.group(15)) != int(held.group(1)) + int(held.group(6)) or held.group(16) != '1'):
                raise SystemExit(f'FAIL: {title}\'s two things through its own controls (export {title} again: tools/export_worlds.py)\n' + output[-2000:])
            # (From 0270 who says their lines: someone else's over them where
            # they are here, else told over the place in their colour, not by
            # the one played.)
            heldSpeakers = re.search(re.escape(f"selftest {title} two things held speakers: ") + r"(\d+) lines by someone else said over them here, (\d+) by someone not here told over the place in their colour, "
                                     r"not by the one played", output)
            if held and int(held.group(2)) and (not heldSpeakers or int(heldSpeakers.group(1)) + int(heldSpeakers.group(2)) > int(held.group(12))
                                                or (given and exported and max(exported) >= since and heldSpeakers.group(1) == '0')):
                raise SystemExit(f'FAIL: who says {title}\'s two things\' lines through its own controls\n' + output[-2000:])
            if heldSpeakers and held and int(held.group(2)):
                print(f"PASS: who says {title}'s two things' lines: {heldSpeakers.group(1)} of someone else over them, {heldSpeakers.group(2)} of someone not here told over the place in their colour")
            if held and int(held.group(2)):
                print(f"PASS: {held.group(1)} of {held.group(2)} answers of {title}'s two things through its own controls as its own sentences give them (a thing from its box held as "
                      f"the pointer, drawn as it, then a tap on a thing or someone: {held.group(8)} usual answers, {held.group(9)} given to someone, {held.group(10)} using up, {held.group(11)} "
                      f"of several lines; not tried: {held.group(5)} away there, {held.group(6)} where no tap finds it, {held.group(7)} with nobody there); let go by a right click, the floor, "
                      "the box and another place")
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
        m = re.search(r'selftest follow: (\d+) asked along, (\d+) walked after \((\d+) while talking\), (\d+) through a door, (\d+) told the chat, (\d+) kept, (\d+) stayed, (\d+) let go, '
                      r'(\d+) of (\d+) following where the same person lives or wanders shown once \(the other stepping aside\), (\d+) failed', output)
        if not m or m.group(11) != '0' or any(m.group(i) != '2' for i in (1, 4, 5, 6, 7, 8)) or m.group(2) == '0' or m.group(3) == '0' \
                or m.group(9) != m.group(10) or (twins and m.group(10) != '2'):
            raise SystemExit('FAIL: followers\n' + output[-2000:])
        print(f'PASS: followers (the chat\'s Follow): asked along, walking after the one played (talking too), through a door beside them, the chat told, kept, staying when asked, let go when someone else is played; wanderers off and on; '
              f'{m.group(9)} of {m.group(10)} into where the same person (another game\'s) lives or wanders, shown once, the other stepping aside')
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
        # Choosing on the screen: the one played chosen again where they live
        # changes nothing; someone here played, everyone else stays where they
        # stood; a custom one left here chosen again plays from where he
        # stood; someone chosen aboard the plane leaves the one before at the
        # airport it was boarded at (where the cabin is exported).
        chosen = re.search(r'(\d+) chosen again where they live as they were, (\d+) played here with everyone else where they stood, (\d+) custom chosen again where he stood, (\d+) of (\d+) chosen aboard left at the stop', output)
        if not chosen or chosen.group(1) != '1' or chosen.group(2) != '1' or chosen.group(3) != '1' or chosen.group(4) != chosen.group(5):
            raise SystemExit('FAIL: choosing on the character screen\n' + output[-2000:])
        print(f'PASS: choosing on the character screen: the one played chosen again where they live, as they were; someone here played, everyone else where they stood; a custom one left here chosen again, from where he stood; {chosen.group(4)} chosen aboard, the one before left at the stop')
        # (The same person as the one played, another game's of the same
        # name, chosen where they live with the one played there: the one
        # before not left beside them, but gone home among the wanderers.)
        twin = re.search(r'(\d+) of (\d+) the same person as the one played chosen there \(the one before gone home, not beside them\)', output)
        if not twin or twin.group(1) != twin.group(2) or (twins and twin.group(2) != '1'):
            raise SystemExit('FAIL: the same person as the one played chosen\n' + output[-2000:])
        print(f'PASS: {twin.group(1)} of {twin.group(2)} the same person as the one played (another game\'s) chosen there: played, the one before gone home, not beside them')
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
        # On a map or a floor plan (no floor there) no pee, no moves and
        # nothing lit (Sith Ewok 2's either; lit already, put away there by
        # him and Sith Ewok 3), the one played told so, none by those left
        # there; at a place's limit a pee let go before the leg is up lets no
        # stain go; a save during a pee (the app put away, then closed) holds
        # none of it, its stain saved as it ends; a walk asked for after L once goes on; Sith Ewok 2 and 3
        # switched from lit put it away beside the one played (the mansion's
        # New kid too); a show heckled by someone else, never the one played.
        left = re.search(r"(\d+) of (\d+) maps and floor plans \(no pee, no moves, nothing lit, said so; put away there; none by those left there\), (\d+) at a place's limit .*?, "
                         r"(\d+) saved during a pee \(none of it\) and as it ended, (\d+) walks asked for after L once gone on, (\d+) of 2 put away beside when switched from lit, "
                         r"(\d+) of (\d+) at the mansion's New kid, (\d+) shows heckled by someone else only, 0 failed", output)
        if not left or left.group(1) != left.group(2) or any(left.group(i) != '1' for i in (3, 4, 5, 9)) or left.group(6) != '2' \
                or left.group(7) != left.group(8) or ((worlds/'maniac-1.svw').exists() and left.group(7) != '2'):
            raise SystemExit('FAIL: moves (maps, the stains\' limit, a save during a pee, a walk after L once, switched from lit, the heckler)\n' + output[-2000:])
        print(f'PASS: on {left.group(1)} maps and floor plans no pee, no moves and nothing lit (said so; put away there; none by those left there); no stain let go at a place\'s limit for a pee let go before the leg is up; '
              f'a save during a pee holds none of it, its stain saved as it ends; a walk asked for after L once goes on; Sith Ewok 2 and 3 switched from lit put it away beside ({left.group(7)} at New kid); '
              f'a show heckled by someone else, never the one played')
        # The camera (a stand-in for the iPhone's Photos): photos of the scene
        # and of the screen, a selfie of three, held still while asked.
        output = sandbox(exe, worlds, 'camera', shots, tmp)
        m = re.search(r'selftest camera: clean (\d+)x(\d+), full (\d+)x(\d+), selfie (\d+) shots (\d+)x(\d+)', output)
        if not m or int(m.group(5)) != 3:
            raise SystemExit('FAIL: camera\n' + output[-2000:])
        print(f'PASS: camera: a photo of the scene ({m.group(1)}x{m.group(2)}), of the screen ({m.group(3)}x{m.group(4)}), a selfie of three ({m.group(6)}x{m.group(7)}), held still')
        # (Aboard the plane, the camera panned away from the one played: a
        # selfie all the same, they seated again after.)
        aboard = re.search(r'(\d+) of (\d+) aboard with the camera panned away', output)
        if not aboard or aboard.group(1) != aboard.group(2):
            raise SystemExit('FAIL: camera aboard\n' + output[-2000:])
        if aboard.group(2) != '0':
            print('PASS: camera aboard the plane, panned away from the one played: a selfie all the same, seated again after')
        # The tour: every place installed a stop, the whole of it at 16x.
        output = sandbox(exe, worlds, 'tour', shots, tmp)
        m = re.search(r'selftest tour: (\d+) stops \((\d+) on foot, (\d+) warped, (\d+) not shown\)', output)
        if not m:
            raise SystemExit('FAIL: tour\n' + output[-2000:])
        stops, foot, warped, refused = (int(m.group(i)) for i in range(1, 5))
        # (Not The Dig's subway cars, nor the insides of rides, from 0198:
        # kWorldRideScenes, Zak's plane cabin and van cockpit; nor, from 0240,
        # the close-ups, kWorldCloseUps: the mansion's wall safe's keypad, from
        # 0242 its telescope's views, from 0248 its TV's film, from 0257 the
        # police headquarters' film after the radio's call, from 0287 Dr
        # Fred's high score on Meteor Mess, from 0288 the talk show's and the
        # Edsel's flight and space films.)
        insides = {'zak-11.svw', 'zak-30.svw', 'maniac-43.svw', 'maniac-34.svw', 'maniac-35.svw', 'maniac-40.svw', 'maniac-32.svw', 'maniac-39.svw',
                   'maniac-42.svw', 'maniac-46.svw', 'maniac-48.svw'}
        svw = len([f for f in worlds.glob('*.svw') if f.stat().st_size and re.fullmatch(r'[a-z0-9]+-\d+\.svw', f.name) and f.name not in insides])
        if stops != svw or foot * 2 < stops:
            raise SystemExit(f'FAIL: tour: {stops} stops of {svw} places, {foot} on foot')
        unreached = int(re.search(r'(\d+) doors not reached', output).group(1))
        across = int(re.search(r'(\d+) gone through from as near as the walk boxes allow', output).group(1))
        if unreached * 100 > foot or not 0 < across * 10 < foot:
            raise SystemExit(f'FAIL: tour: {unreached} doors not reached, {across} from as near as the walk allows, for {foot} on foot')
        print(f'PASS: tour: {stops} stops ({foot} on foot, {warped} warped, {refused} not shown, {unreached} doors not reached, '
              f'{across} through from as near as the walk boxes allow); its controls; back where it began')
        # (From 0252) Begun upstairs in the mansion (room 38) and stopped at
        # its hall (room 12): the way home starts no timed event (the package).
        if all((worlds/f'maniac-{r}.svw').exists() for r in (12, 38)):
            if "stopped at the mansion's hall, begun upstairs: home, no timed event started" not in output:
                raise SystemExit('FAIL: tour: a timed event started by the way home\n' + output[-2000:])
            print('PASS: tour stopped at the mansion\'s hall, begun upstairs: home, no timed event started')
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
        relaunch(exe, worlds, tmp)
    switch(a.data.resolve(), worlds, a.frames)
    # A cache whose place cannot be read: back to Maniac all the same.
    with tempfile.TemporaryDirectory(prefix='scummverse-broken-', dir=ROOT/'build') as broken:
        (Path(broken)/'monkey-33.svw').write_bytes(b'SVW3 not a scene')
        switch(a.data.resolve(), Path(broken), a.frames, broken=True)
    switch(a.data.resolve(), worlds, a.frames, story=True)
    switch(a.data.resolve(), worlds, a.frames, stopped=True)
    switch(a.data.resolve(), worlds, a.frames, restored=True)
    print('PASS: sandbox engine')
