#!/usr/bin/env python3
"""Story play through the real engine: the original games opened from Maniac.

Builds a probe binary (temporary copies of scumm.cpp, with
engines/scumm/scummverse_story.inc written into it, and of the film player;
as test_sandbox_engine.py's switch does) and runs Maniac with a Documents
folder holding the supplied games. The Worlds menu's requests reach the
story code through the poll it reads (in place of the phone's), so its own
handling of them is what runs.
- First pass: Maniac opens each game's story (a request left over from
  before is sent as it opens: the game must drop it); the game starts fresh,
  runs a while, and once it can be saved asks to go back to Maniac (the
  menu's Back to Maniac Mansion): it saves its story save and leaves, and
  Maniac comes back where it was. A game whose story needs a file its folder
  lacks is refused (that file must really be missing).
- Second pass: Maniac opens the first game again; each starts from its story
  save exactly as saved (every variable), then goes on to the next game's
  story directly (Go to <game>); the last leaves as ScummVM's own menu does
  (Return to Launcher, no request), which must save it on the way out.
- Third: Maniac opens that last game again: it starts from the save made on
  the way out, exactly as it was, and goes back.
- Then the app starts again as if it had been stopped in the last game's
  story (the mansion clears the mark, so it is put in): it goes on in that
  game from its newest save, where it was; Save now saves it and it goes on;
  once it has played a few seconds the engine marks it on disk; ScummVM's
  autosave; the app is stopped at once (as the phone stops it). Started
  again with nothing put in: it goes on from that newer autosave, Save now,
  then ScummVM's menu (Return to Launcher) saves it again on the way out,
  and the mansion comes back where it was.
Maniac Mansion's own story (its data, with none of the mansion's additions)
is the first game unless --no-maniac. Every story starts with none of them.
Films are cut short; a start that asks something is clicked through.
Monkey Island 2's and Sam & Max's openings are their copy protection (a
recipe from the code wheel; a doll dressed as a page of the manual shows):
story play answers them for the player (scummverseStoryPassGuard), so they
are in the default list. Sam & Max is held to the page a press alone gets
wrong (--dolls-page), and must leave with no wrong answer.
Game data and saves stay in a temporary folder under build/.

Usage: tools/test_story_engine.py game-data/mm-dos monkey=game-data/monkey1-vga ...
(with no games given, every game folder under game-data/ the catalog names)
"""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from test_exploration import ROOT, command_for

# The catalog's games in its order (common/scummverse_world_catalog.h).
CATALOG = ['monkey', 'monkey2', 'loom', 'indy3', 'atlantis', 'tentacle', 'samnmax', 'ft', 'dig', 'comi', 'maniac', 'zak']
DEFAULT = {'monkey': 'monkey1-vga', 'monkey2': 'monkey2-vga', 'loom': 'loom-ega', 'indy3': 'indy3-vga', 'atlantis': 'atlantis-mac',
           'tentacle': 'tentacle-floppy', 'samnmax': 'samnmax-floppy', 'ft': 'ft', 'dig': 'dig', 'comi': 'comi', 'zak': 'zak-dos'}

# Test-only, at file scope: the request the story code polls (the phone's
# Worlds menu on the device), engines made, and what each story save held.
GLOBALS = r'''
static int g_probeRequest = 0, g_probeEngines = 0, g_probeFrames = 0;
static int probePoll() { const int request = g_probeRequest; g_probeRequest = 0; return request; }
static int probePeek() { return g_probeRequest; }
static Common::HashMap<Common::String, Common::Array<int32> > g_probeVars;
'''
# Test-only, where the story save is written: what it held.
SAVED = r'''
	warning("SCUMMVERSE_STORY_SAVED %s room=%d ego=%d frames=%d", _targetName.c_str(), _currentRoom, VAR_EGO != 0xFF ? VAR(VAR_EGO) : -1, g_probeFrames);
	g_probeVars[_targetName] = Common::Array<int32>(_scummVars, _numVariables);
'''
# Test-only: at the top of the main loop (Maniac and each game's story).
PROBE = r'''
		if (ConfMan.hasKey("scummverse_story_probe")) {
			using namespace ::Scummverse::WorldCatalog;
			static int probeSeen = 0, probePass = 0, probeAt = 0, probeLast = -1, probeFirstRoom = 0;
			static bool probeAsked = false, probeSavedNow = false, probeAutosaving = false, probeEntered = false;
			static Common::Array<bool> probeRefused;
			Common::Array<int> games;
			for (const Common::String &g : Common::StringTokenizer(ConfMan.get("scummverse_story_probe_games"), ",").split()) games.push_back(atoi(g.c_str()));
			const int count = games.size();
			probeRefused.resize(count);
			auto nextOk = [&](int i) { while (i < count && probeRefused[i]) ++i; return i; };
			const int frames = ConfMan.getInt("scummverse_story_probe");
			const int ego = VAR_EGO != 0xFF ? VAR(VAR_EGO) : -1;
			const bool fresh = probeSeen != g_probeEngines;
			// (The app started again in a story: only Back, then done.)
			if (probePass == 0 && ConfMan.hasKey("scummverse_story_probe_resume")) probePass = 5;
			// (Story mode: its list's choices, the configuration's in turn.)
			if (probePass == 0 && ConfMan.hasKey("scummverse_story_probe_mode")) probePass = 6;
			if (fresh) { probeSeen = g_probeEngines; g_probeFrames = 0; probeAsked = false; probeFirstRoom = 0; }
			if (!probeFirstRoom) probeFirstRoom = _currentRoom;
			++g_probeFrames;
			if (!_scummverseStory) {
				if (fresh && ConfMan.hasKey("save_slot") && ConfMan.getInt("save_slot") == 100)
					warning("SCUMMVERSE_STORY_HOME room=%d ego=%d", _currentRoom, ego);
				// (Each time it has run a while with nothing on its way: after a
				// game refused for its files, the next a while later.)
				if (probePass == 6 && g_probeFrames % frames == 0 && ChainedGamesMan.empty()) {
					// (The mansion's Worlds menu: Story mode; the second time, done.)
					// (Through the menu's request, as the phone sends it.)
					if (!probeEntered) { probeEntered = true; warning("SCUMMVERSE_STORY_ENTER room=%d ego=%d", _currentRoom, ego); g_probeRequest = kWorldStoryModeRequest; }
					else { warning("SCUMMVERSE_STORY_DONE"); quitGame(); }
				} else if (g_probeFrames % frames == 0 && ChainedGamesMan.empty()) {
					if (probePass == 0 && probeAt == count) { probePass = 1; probeAt = nextOk(0); if (probeAt >= count) probePass = 4; }
					const int game = probePass == 2 ? probeLast : probePass < 2 && probeAt < count ? games[probeAt] : -1;
					if (probePass == 4 || game < 0) { warning("SCUMMVERSE_STORY_DONE"); quitGame(); }
					else {
						warning("SCUMMVERSE_STORY_OPEN game=%d pass=%d room=%d ego=%d", game, probePass, _currentRoom, ego);
						// (A request left from before: the game must drop it.)
						g_probeRequest = kWorldStoryHomeRequest;
						scummverseOpenStory(game);
						if (ChainedGamesMan.empty()) {
							g_probeRequest = 0;
							warning("SCUMMVERSE_STORY_NOT_OPENED game=%d", game);
							if (probePass == 0) probeRefused[probeAt] = true; else quitGame();
						}
						if (probePass == 0) ++probeAt;
						if (probePass == 2) probePass = 3;
					}
				}
			} else {
				// (Sam & Max's dolls: held to the page given, and on leaving
				// them, how many wrong answers they had.)
				static int probeDollsRoom = 0;
				if (_game.id == GID_SAMNMAX && ConfMan.hasKey("scummverse_story_probe_page")) {
					const int page = ConfMan.getInt("scummverse_story_probe_page");
					if (_currentRoom == 71 && readVar(152) >= 1 && readVar(152) != page) writeVar(152, page);
					if (probeDollsRoom == 71 && _currentRoom != 71)
						warning("SCUMMVERSE_STORY_DOLLS %s page=%d doll=%d wrong=%d", _targetName.c_str(), readVar(152), readVar(153), readVar(154));
					probeDollsRoom = _currentRoom;
				}
				if (fresh) {
					const int slot = ConfMan.hasKey("save_slot") ? ConfMan.getInt("save_slot") : -1;
					// (None of the mansion's additions in any story.)
					const int additions = _scummverseRoaming + _scummverseExplorationDoors + _scummverseExplorationSafety + _scummverseAuditedManiac;
					warning("SCUMMVERSE_STORY_START %s v%d additions=%d room=%d ego=%d from=%d slot=%d", _targetName.c_str(), _game.version, additions, _currentRoom, ego, _scummverseStoryFrom, slot);
					if (probePass >= 1) {
						int differ = 0, firstDiff = -1;
						const Common::Array<int32> &kept = g_probeVars[_targetName];
						for (int i = 0; i < _numVariables; ++i) {
							// (Two the engine itself sets on every load: the room
							// flag, and the voices as the settings have them.)
							if ((VAR_ROOM_FLAG != 0xFF && i == VAR_ROOM_FLAG) || (VAR_VOICE_MODE != 0xFF && i == VAR_VOICE_MODE)) continue;
							if (i >= (int)kept.size() || kept[i] != _scummVars[i]) { if (firstDiff < 0) firstDiff = i; ++differ; }
						}
						warning("SCUMMVERSE_STORY_LOADED %s room=%d ego=%d vars=%d differ=%d first=%d", _targetName.c_str(), _currentRoom, ego, (int)kept.size(), differ, firstDiff);
					}
				}
				// (Where the story save can be made: the player has the controls.)
				const bool can = canSaveGameStateCurrently() && _userPut > 0 && !_saveLoadFlag;
				if (probePass == 0 && !probeAsked && g_probeFrames >= frames) {
					// (Past its opening screen, where the game waits for a click.)
					if (can && _currentRoom != probeFirstRoom) {
						// (The menu's Back to Maniac Mansion.)
						probeAsked = true;
						warning("SCUMMVERSE_STORY_BACK %s room=%d ego=%d", _targetName.c_str(), _currentRoom, ego);
						g_probeRequest = kWorldStoryHomeRequest;
					} else if (g_probeFrames > frames + 2400) {
						probeAsked = true;
						warning("SCUMMVERSE_STORY_REFUSED %s room=%d", _targetName.c_str(), _currentRoom);
						quitGame();
					} else {
						// (A start that asks something, as Monkey Island 2's how
						// hard: a click in the middle now and then.)
						scummverseSkipCutscene();
						if (VAR_HAVE_MSG != 0xFF) VAR(VAR_HAVE_MSG) = 0;
						_talkDelay = 0;
						// (Each of its verbs and things on the screen in turn, then
						// the middle: wherever the question's answers are.)
						if ((g_probeFrames - frames) % 120 == 60) {
							Common::Array<Common::Point> spots;
							for (int i = 1; i < _numVerbs; ++i)
								if (_verbs[i].verbid && _verbs[i].curmode == 1 && !_verbs[i].curRect.isEmpty())
									spots.push_back(Common::Point((_verbs[i].curRect.left + _verbs[i].curRect.right) / 2, (_verbs[i].curRect.top + _verbs[i].curRect.bottom) / 2));
							const VirtScreen &vs = _virtscr[kMainVirtScreen];
							for (int i = 1; i < _numLocalObjects; ++i)
								if (_objs[i].obj_nr && _objs[i].width > 0 && _objs[i].height > 0)
									spots.push_back(Common::Point(_objs[i].x_pos + _objs[i].width / 2 - vs.xstart, _objs[i].y_pos + _objs[i].height / 2 + vs.topline));
							spots.push_back(Common::Point(_screenWidth / 2, _screenHeight / 2));
							const Common::Point at = spots[((g_probeFrames - frames) / 120) % spots.size()];
							_mouse.x = at.x; _mouse.y = at.y;
							_leftBtnPressed = 3; // (clicked and down)
						} else if ((g_probeFrames - frames) % 120 == 61) _leftBtnPressed = 0;
					}
				}
				// (Only once it can be saved: a leaving it cannot save asks the
				// player, and nobody answers here.)
				if (probePass == 1 && !probeAsked && g_probeFrames >= frames / 4 && can) {
					probeAsked = true;
					probeAt = nextOk(probeAt + 1);
					if (probeAt < count) {
						// (The menu's Go to <game>.)
						warning("SCUMMVERSE_STORY_GO %s to=%d room=%d ego=%d", _targetName.c_str(), games[probeAt], _currentRoom, ego);
						g_probeRequest = kWorldStoryRequest + games[probeAt];
					} else {
						// (ScummVM's own menu, Return to Launcher: no request.)
						for (int g = 0; g < count; ++g)
							if (_targetName == Common::String(kWorldStoryPrefix) + kWorldGames[games[g]].gameid) probeLast = games[g];
						probePass = 2;
						warning("SCUMMVERSE_STORY_QUIT %s room=%d ego=%d", _targetName.c_str(), _currentRoom, ego);
						Common::Event event;
						event.type = Common::EVENT_RETURN_TO_LAUNCHER;
						_system->getEventManager()->pushEvent(event);
					}
				}
				// (Gone on with at the start: the menu's Save now first, the
				// game going on. The first time, once it is marked to go on in
				// at the next start, ScummVM's autosave, then the app stopped
				// at once, as the phone stops it; the second time, ScummVM's
				// own menu, Return to Launcher, which must save it again.)
				if (probePass == 5 && !probeSavedNow && g_probeFrames >= frames / 8 && can) {
					probeSavedNow = true;
					warning("SCUMMVERSE_STORY_SAVE_NOW %s room=%d ego=%d", _targetName.c_str(), _currentRoom, ego);
					g_probeRequest = kWorldStorySaveRequest;
				}
				if (probePass == 5 && probeSavedNow && !probeAsked && g_probeFrames >= frames / 4 && can) {
					if (ConfMan.getInt("scummverse_story_probe_resume") == 1) {
						if (_scummverseStoryPlayed < 0) {
							probeAsked = probeAutosaving = true;
							saveGameState(getAutosaveSlot(), "Autosave", true);
						}
					} else {
						probeAsked = true;
						probePass = 4;
						warning("SCUMMVERSE_STORY_QUIT %s room=%d ego=%d", _targetName.c_str(), _currentRoom, ego);
						Common::Event event;
						event.type = Common::EVENT_RETURN_TO_LAUNCHER;
						_system->getEventManager()->pushEvent(event);
					}
				}
				if (probeAutosaving && !_saveLoadFlag) {
					warning("SCUMMVERSE_STORY_AUTOSAVED %s room=%d ego=%d", _targetName.c_str(), _currentRoom, ego);
					// (The null backend's quit: the process ends here, nothing
					// more saved or written.)
					_system->quit();
				}
				// (Story mode: its Story list; Maniac's own story, Explore mode.)
				if (probePass == 6 && !probeAsked && g_probeFrames >= frames / 4 && can) {
					probeAsked = true;
					const bool mansion = _targetName == Common::String(kWorldStoryPrefix) + "maniac";
					warning("SCUMMVERSE_STORY_MODE_LEAVE %s %s room=%d ego=%d", _targetName.c_str(), mansion ? "explore" : "list", _currentRoom, ego);
					g_probeRequest = mansion ? kWorldStoryExploreRequest : kWorldStoryHomeRequest;
				}
				if (probePass == 3 && !probeAsked && g_probeFrames >= frames / 4 && can) {
					probeAsked = true;
					probePass = 4;
					warning("SCUMMVERSE_STORY_BACK %s room=%d ego=%d", _targetName.c_str(), _currentRoom, ego);
					g_probeRequest = kWorldStoryHomeRequest;
				}
				if (g_probeFrames == frames * 6 + (probePass == 0 ? 2400 : 0)) { warning("SCUMMVERSE_STORY_STUCK %s room=%d", _targetName.c_str(), _currentRoom); probePass = 4; quitGame(); }
			}
		}
'''
LOOP = '\twhile (!shouldQuit()) {\n\t\t// Determine how long to wait before the next loop iteration should start\n'
INCLUDE = '#include "scumm/scummverse_story.inc"\n'
ROAMING = '#include "scumm/scummverse_roaming.inc"\n'
AFTER_INCLUDES = '#include "common/scummverse_story.h"\n'
SAVE_DONE = '\t_scummverseStorySaved = true;\n\treturn true;\n'
MADE = '\t_scummverseStory = ConfMan.hasKey("scummverse_story")'
# Test-only: films end at once.
FILM = '\t\tif (_vm->shouldQuit() || _vm->_saveLoadFlag || _vm->_smushVideoShouldFinish) {\n'
FILM_PROBE = '\t\tif (ConfMan.hasKey("scummverse_story_probe")) _vm->_smushVideoShouldFinish = true;\n'


def once(code, mark, where):
    if code.count(mark) != 1:
        raise RuntimeError(f'Pinned boundary changed in {where}: {mark!r}')


def scumm_probe():
    code = (ROOT/'engine/engines/scumm/scumm.cpp').read_text()
    story = (ROOT/'engine/engines/scumm/scummverse_story.inc').read_text()
    for mark in (LOOP, INCLUDE, AFTER_INCLUDES, MADE, ROAMING):
        once(code, mark, 'scumm.cpp')
    roaming = (ROOT/'engine/engines/scumm/scummverse_roaming.inc').read_text()
    once(roaming, 'scummverseWorldPeek()', 'scummverse_roaming.inc')
    once(story, SAVE_DONE, 'scummverse_story.inc')
    if 'scummverseWorldPoll()' not in story or code.count('scummverseWorldPoll()') != 1:
        raise RuntimeError('the story code no longer polls the Worlds menu where expected')
    story = story.replace('scummverseWorldPoll()', 'probePoll()').replace(SAVE_DONE, SAVED + SAVE_DONE)
    code = code.replace(INCLUDE, story)
    # (The mansion's Story mode request, through the probe's in place of the phone's.)
    code = code.replace(ROAMING, roaming.replace('scummverseWorldPeek()', 'probePeek()').replace('scummverseWorldPoll()', 'probePoll()'))
    code = code.replace('scummverseWorldPoll()', 'probePoll()')  # (the constructor's drop of a request left over)
    code = code.replace(MADE, '\t++g_probeEngines;\n' + MADE)
    code = code.replace(AFTER_INCLUDES, AFTER_INCLUDES + '#include "common/tokenizer.h"\n' + GLOBALS)
    return code.replace(LOOP, LOOP.split('\n')[0] + '\n' + PROBE + '\n'.join(LOOP.split('\n')[1:]))


def probe_binary(work):
    build = ROOT/'build/null'
    objects = []
    film = (ROOT/'engine/engines/scumm/smush/smush_player.cpp').read_text()
    once(film, FILM, 'smush_player.cpp')
    for rel, code in (('engines/scumm/scumm.cpp', scumm_probe()), ('engines/scumm/smush/smush_player.cpp', film.replace(FILM, FILM_PROBE + FILM))):
        source = ROOT/'engine'/rel
        probe = work/Path(rel).name
        probe.write_text(code)
        target = rel.replace('.cpp', '.o')
        cmd = command_for(build, source, target)
        cmd[cmd.index(str(source))] = str(probe)
        obj = work/Path(target).name
        cmd[cmd.index('-o')+1] = str(obj)
        cmd[cmd.index('-MF')+1] = str(work/(Path(target).stem + '.d'))
        built = subprocess.run(cmd, cwd=build, capture_output=True, text=True)
        if built.returncode:
            raise SystemExit(f'FAIL: probe for {rel} does not compile\n' + built.stderr[-6000:])
        objects.append(obj)
    archive = work/'libscumm.a'
    shutil.copy2(build/'engines/scumm/libscumm.a', archive)
    subprocess.run(['ar', 'r', str(archive)] + [str(o) for o in objects], check=True)
    cmd = command_for(build, 'engines/scumm/libscumm.a', 'scummvm')
    cmd[cmd.index('engines/scumm/libscumm.a')] = str(archive)
    exe = work/'scummvm-probe'
    cmd[cmd.index('-o')+1] = str(exe)
    subprocess.run(cmd, cwd=build, check=True, capture_output=True)
    return exe


def missing(path, name):
    places = [path] + [d for d in path.iterdir() if d.is_dir() and d.name.lower() in ('data', 'video', 'resource')]
    return not any(f.name.lower() == name.lower() for d in places for f in d.iterdir())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('maniac', type=Path)
    p.add_argument('games', nargs='*', help='folder=path pairs, e.g. monkey=game-data/monkey1-vga')
    p.add_argument('--frames', type=int, default=240, help='frames before each leaves (and Maniac before it opens one)')
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds')
    p.add_argument('--no-maniac', action='store_true', help="leave out Maniac Mansion's own story")
    p.add_argument('--dolls-page', type=int, default=4, help="Sam & Max's copy protection held to this page of the manual (4: the one where a press alone is wrong)")
    a = p.parse_args()
    pairs = [g.split('=', 1) for g in a.games] if a.games else [(k, str(ROOT/'game-data'/v)) for k, v in DEFAULT.items() if (ROOT/'game-data'/v).is_dir()]
    games = [(k, Path(v).resolve()) for k, v in pairs]
    for k, _ in games:
        if k not in CATALOG or k == 'maniac':
            raise SystemExit(f'not a story game: {k} (Maniac Mansion\'s own story is the mansion\'s data)')
    # (The mansion's own story: from the folder the mansion plays from.)
    if not a.no_maniac:
        games.insert(0, ('maniac', a.maniac.resolve()))
    if not games:
        print('SKIP: story play: no games supplied')
        return
    order = [CATALOG.index(k) for k, _ in games]
    with tempfile.TemporaryDirectory(prefix='scummverse-story-', dir=ROOT/'build') as tmp:
        work = Path(tmp)
        exe = probe_binary(work)
        docs = work/'documents'
        docs.mkdir()
        for k, path in games:
            if k != 'maniac':
                (docs/k).symlink_to(path)
        # (Every game already set up: no exports at the start.)
        (docs/'worlds').mkdir()
        for marker in Path(a.worlds).glob('*.svx'):
            shutil.copy2(marker, docs/'worlds'/marker.name)
        saves = work/'saves'
        saves.mkdir()
        config = work/'story.ini'
        config.write_text('[scummvm]\nscummverse_roaming=false\nscummverse_wanderers=false\n'
                          f'scummverse_story_probe={a.frames}\nscummverse_story_probe_games={",".join(map(str, order))}\n'
                          f'scummverse_worlds_path={a.worlds.resolve()}\nscummverse_story_probe_page={a.dolls_page}\n')
        result = subprocess.run([str(exe), f'--config={config}', f'--path={a.maniac.resolve()}', f'--savepath={saves}', '--debuglevel=1'],
                                cwd=docs, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=5400)
        output = result.stdout + result.stderr
        (ROOT/'build/story-engine.log').write_text(output)
        lines = [l for l in output.splitlines() if 'SCUMMVERSE_STORY_' in l or 'SCUMMVERSE story' in l or 'could not start' in l]
        fail = []

        def tagged(tag):
            return [l.split(tag + ' ', 1)[1].rstrip('!') for l in lines if tag + ' ' in l]
        opened, homes = tagged('SCUMMVERSE_STORY_OPEN'), tagged('SCUMMVERSE_STORY_HOME')
        starts, saved, loaded = tagged('SCUMMVERSE_STORY_START'), tagged('SCUMMVERSE_STORY_SAVED'), tagged('SCUMMVERSE_STORY_LOADED')
        went, quits = tagged('SCUMMVERSE_STORY_GO'), tagged('SCUMMVERSE_STORY_QUIT')
        # Games refused for a file their story needs (as the engine says it):
        # that file must really be missing from the game's folder.
        refused = {}
        for l in lines:
            m = re.search(r'SCUMMVERSE story: (\w+) not opened \((.*)\)', l)
            if m:
                refused[m.group(1)] = m.group(2)
        for k, path in games:
            if k in refused:
                m = re.search(r'Documents/\w+: (\S+) is missing', refused[k])
                if not m or not missing(path, m.group(1)):
                    fail.append(f'{k}: refused ({refused[k]})')
        ok = [k for k, _ in games if k not in refused]
        n = len(games)
        if result.returncode or not any('SCUMMVERSE_STORY_DONE' in l for l in lines):
            fail.append(f'did not finish (exit {result.returncode})')
        for tag in ('SCUMMVERSE_STORY_STUCK', 'SCUMMVERSE_STORY_REFUSED', 'could not start'):
            fail += [f'{tag}: {l}' for l in lines if tag in l]
        if ok:
            if len(opened) != n + 2 or len(homes) != len(ok) + 2:
                fail.append(f'Maniac opened {len(opened)} and came back {len(homes)} times, expected {n + 2} and {len(ok) + 2}')
            # Maniac back where it was each time (the same room and kid).
            for o, h in zip([o for o in opened if not any(f'game={CATALOG.index(k)} ' in o for k in refused)], homes):
                if re.sub(r'game=\d+ pass=\d+ ', '', o) != h:
                    fail.append(f'Maniac left at {o}, came back at {h}')
        report = [f'{k} refused ({refused[k]})' for k in refused]
        last = ok[-1] if ok else None
        for k in ok:
            target = f'scummverse-story-{k}'
            begun = [s for s in starts if s.startswith(target + ' ')]
            kept = [s for s in saved if s.startswith(target + ' ')]
            back = [s for s in loaded if s.startswith(target + ' ')]
            want = 3 if k == last else 2
            if len(begun) != want:
                fail.append(f'{k}: started {len(begun)} times, expected {want}')
                continue
            if not begun[0].endswith('slot=-1'):
                fail.append(f'{k}: first start not fresh ({begun[0]})')
            fail += [f'{k}: started with the mansion\'s additions ({b})' for b in begun if ' additions=0 ' not in b]
            for b in begun[1:]:
                if not b.endswith('slot=99'):
                    fail.append(f'{k}: not started from its story save ({b})')
            if len(kept) != want:
                fail.append(f'{k}: saved {len(kept)} times, expected {want}')
                continue
            # The leftover request dropped: it ran a while before it saved.
            frames0 = int(re.search(r'frames=(\d+)', kept[0]).group(1))
            if frames0 < a.frames:
                fail.append(f'{k}: left after {frames0} frames (a request from before it started was not dropped)')
            # Each start from a save exactly as that save held it.
            for i, b in enumerate(back):
                where = re.search(r'room=(\d+) ego=(-?\d+) vars=(\d+) differ=(\d+)', b)
                was = re.search(r'room=(\d+) ego=(-?\d+)', kept[i]).groups()
                if not where or where.groups()[:2] != was:
                    fail.append(f'{k}: saved at {was}, started at {where.groups()[:2] if where else None}')
                elif where.group(4) != '0':
                    fail.append(f'{k}: {where.group(4)} of {where.group(3)} variables not as saved ({b})')
            if not (saves/f'{target}.s99').exists():
                fail.append(f'{k}: no {target}.s99')
            # (A copy-protection screen answered by story play, and left.)
            guard = {'monkey2': '108', 'samnmax': '71'}.get(k)
            if guard and (not any(f'{target} copy protection answered' in l for l in lines) or
                          re.search(r'room=(-?[0-9]+)', kept[0]).group(1) == guard):
                fail.append(f'{k}: its copy protection not answered and left')
            # (The dolls dressed as the page asks, right the first time.)
            if k == 'samnmax':
                dolls = [l for l in lines if f'SCUMMVERSE_STORY_DOLLS {target} ' in l]
                if not any(f'{target} copy protection answered (the dolls dressed)' in l for l in lines):
                    fail.append(f'{k}: its dolls not dressed')
                if len(dolls) != 1 or f'page={a.dolls_page} ' not in dolls[0] or not dolls[0].rstrip('!').endswith(' wrong=0'):
                    fail.append(f'{k}: its dolls left {dolls}, expected once, page {a.dolls_page}, no wrong answer')
            report.append(f'{k} (room {re.search(r"room=(-?[0-9]+)", kept[0]).group(1)})')
        if ok:
            if len(went) != len(ok) - 1 or len(quits) != 1 or not quits[0].startswith(f'scummverse-story-{last} '):
                fail.append(f'went on {len(went)} times and quit {len(quits)}, expected {len(ok) - 1} and 1 ({last})')
            if not any(f'scummverse-story-{last} saved on quitting' in l for l in lines):
                fail.append(f'{last}: not saved on quitting')
        # (Maniac's own autosave, slot 0, is ScummVM's: not story play's.)
        stray = sorted(f.name for f in saves.iterdir() if f.name.startswith('maniac.s') and f.name != 'maniac.s00')
        if stray:
            fail.append(f'Maniac saves written by story play: {stray}')
        # The app started again, stopped in the last game's story: it goes on
        # there from its newest save (the one made as it went back, where it
        # was); Save now saves it there and it goes on; once it has played a
        # few seconds it is marked (on disk) to go on in; ScummVM's autosave;
        # then the app stopped at once, as the phone stops it. Started again:
        # it goes on from that autosave (newer, in the same minute or later),
        # Save now, then ScummVM's menu (Return to Launcher) saves it again on
        # the way out, and the mansion comes back after it, where it was.
        marked = [l for l in lines if 'goes on at the next start' in l]
        if ok and not marked:
            fail.append('no story marked to go on in at the next start')
        if ok and not fail:
            ini = config.read_text()
            if 'scummverse_story_playing' in ini:
                fail.append('the mansion did not clear the story to go on in')
            target = f'scummverse-story-{last}'

            def start(mode, inject):
                # (Going on at the next start is Story mode's. The engine's own
                # mark kept when nothing is put in.)
                keys = 'scummverse_story_probe_resume|scummverse_mode|scummverse_story_choices' + ('|scummverse_story_playing' if inject else '')
                text = re.sub(r'^(' + keys + r')=.*\n', '', config.read_text(), flags=re.M)
                head = f'[scummvm]\nscummverse_mode=story\nscummverse_story_probe_resume={mode}\n' + (f'scummverse_story_playing={target}\n' if inject else '')
                config.write_text(text.replace('[scummvm]\n', head, 1))
                run = subprocess.run([str(exe), f'--config={config}', f'--path={a.maniac.resolve()}', f'--savepath={saves}', '--debuglevel=1'],
                                     cwd=docs, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=1800)
                out = run.stdout + run.stderr
                (ROOT/f'build/story-engine-resume{mode}.log').write_text(out)
                keep = [l for l in out.splitlines() if 'SCUMMVERSE_STORY_' in l or 'SCUMMVERSE story' in l or 'could not start' in l or 'going on with' in l]
                return run, out, keep, [l.split('SCUMMVERSE_STORY_START ', 1)[1] for l in keep if 'SCUMMVERSE_STORY_START ' in l]

            def where(text):
                m = re.search(r'room=(\d+) ego=(-?\d+)', text)
                return m.groups() if m else None
            # (Stopped in it: the key put in, as the first run's mansion cleared it.)
            first, more, relines, restart = start(1, True)
            last_saved = [s for s in saved if s.startswith(target + ' ')][-1]
            autosaved = [l.split('SCUMMVERSE_STORY_AUTOSAVED ', 1)[1] for l in relines if 'SCUMMVERSE_STORY_AUTOSAVED ' in l]
            if first.returncode or not autosaved:
                fail.append(f'started again: not autosaved and stopped (exit {first.returncode})')
            elif len(restart) != 1 or not restart[0].startswith(target + ' ') or not re.search(r' from=(99|0) slot=-1', restart[0]):
                fail.append(f'started again: did not go on in {last} from its save: {restart}')
            elif where(restart[0]) != where(last_saved) and ' from=99 ' in restart[0]:
                fail.append(f'{last} went on at {restart[0]}, saved at {where(last_saved)}')
            elif not any(f'{target} saved now' in l for l in relines):
                fail.append(f'{last}: Save now did not save it')
            elif f'scummverse_story_playing={target}' not in config.read_text():
                fail.append(f'{last}: not marked on disk to go on in at the next start')
            lines += relines
            output += more
            if not fail:
                # (Stopped again: the engine's own mark, nothing put in.)
                second, more, relines, restart = start(2, False)
                if second.returncode or not any('SCUMMVERSE_STORY_DONE' in l for l in relines):
                    fail.append(f'second start did not finish (exit {second.returncode})')
                elif len(restart) != 1 or not restart[0].startswith(target + ' ') or ' from=0 slot=-1' not in restart[0]:
                    fail.append(f'second start did not go on in {last} from its newer autosave: {restart}')
                elif where(restart[0]) != where(autosaved[0]):
                    fail.append(f'{last} went on at {restart[0]}, autosaved at {autosaved[0]}')
                elif not any(f'{target} saved now' in l for l in relines) or not any(f'{target} saved on quitting' in l for l in relines):
                    fail.append(f'{last}: Save now, then ScummVM\'s menu, did not save it both times')
                elif not any('SCUMMVERSE_STORY_HOME' in l for l in relines):
                    fail.append('the mansion did not come back after the story gone on in')
                elif 'scummverse_story_playing' in config.read_text():
                    fail.append('the story to go on in was not cleared')
                else:
                    report.append(f'the app stopped in {last} went on there from its story save, Save now, marked on disk, autosaved and '
                                  f'stopped; started again from that newer autosave, Save now, saved again leaving by ScummVM\'s menu, then the mansion')
                lines += relines
                output += more
            # (A game of the list's other than the mansion's own story.)
            chosen = next((k for k in reversed(ok) if k != 'maniac'), None)
            if not fail and not chosen:
                report.append('Story mode not walked (no game but the mansion\'s own story)')
            if not fail and chosen:
                target = f'scummverse-story-{chosen}'
                # Story mode: its list at the start (the last game, then
                # Maniac's own story), Story list from the one, Explore mode
                # from the other (the mansion where it was), Story mode again
                # from the mansion's menu, its list, Explore.
                text = re.sub(r'^(scummverse_story_probe_resume|scummverse_mode|scummverse_story_choices|scummverse_story_playing)=.*\n', '',
                              config.read_text(), flags=re.M)
                config.write_text(text.replace('[scummvm]\n', f'[scummvm]\nscummverse_story_probe_mode=1\nscummverse_mode=story\n'
                                               f'scummverse_story_choices={chosen},maniac,explore\n', 1))
                third = subprocess.run([str(exe), f'--config={config}', f'--path={a.maniac.resolve()}', f'--savepath={saves}', '--debuglevel=1'],
                                       cwd=docs, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=1800)
                more = third.stdout + third.stderr
                (ROOT/'build/story-engine-mode.log').write_text(more)
                relines = [l for l in more.splitlines() if 'SCUMMVERSE_STORY_' in l or 'SCUMMVERSE story' in l or 'Story mode' in l or 'Explore mode' in l or 'could not start' in l]
                order = ['SCUMMVERSE: Story mode: ' + target, 'SCUMMVERSE_STORY_START ' + target, 'SCUMMVERSE_STORY_MODE_LEAVE ' + target + ' list',
                         'SCUMMVERSE: Story mode: scummverse-story-maniac', 'SCUMMVERSE_STORY_START scummverse-story-maniac',
                         'SCUMMVERSE_STORY_MODE_LEAVE scummverse-story-maniac explore', 'SCUMMVERSE_STORY_HOME', 'SCUMMVERSE_STORY_ENTER',
                         'SCUMMVERSE story: Story mode', 'SCUMMVERSE: Explore mode', 'SCUMMVERSE_STORY_HOME', 'SCUMMVERSE_STORY_DONE']
                at, absent = 0, None
                for want in order:
                    while at < len(relines) and want not in relines[at]:
                        at += 1
                    if at == len(relines):
                        absent = want
                        break
                    at += 1
                if third.returncode or absent:
                    fail.append(f'Story mode: {absent or "exit " + str(third.returncode)} not as expected')
                elif sum('SCUMMVERSE: Explore mode' in l for l in relines) != 1 or sum('SCUMMVERSE: Story mode: ' in l for l in relines) != 2:
                    # (Explore from the mansion's own story's menu, not by the list: chosen there once only.)
                    fail.append('Story mode: the list chose Explore or a story more often than asked')
                elif 'scummverse_mode=explore' not in config.read_text():
                    fail.append('Story mode: Explore mode not kept')
                elif any('additions=' in l and ' additions=0 ' not in l for l in relines):
                    fail.append('Story mode: a story with the mansion\'s additions')
                else:
                    report.append(f'Story mode: its list ({chosen}), Story list, Maniac\'s own story, Explore mode (the mansion where it was), '
                                  'Story mode from the mansion\'s menu, its list, Explore')
                lines += relines
                output += more
        if fail:
            raise SystemExit('FAIL: story play\n  ' + '\n  '.join(fail) + '\n' + '\n'.join(lines[-60:]) + '\n' + output[-3000:])
        print(f'PASS: story play: Maniac opens each of {len(ok)} games (a request from before dropped), each saves and goes back, '
              f'Maniac where it was; each again from its story save exactly as saved, on to the next; the last quit as '
              f'ScummVM\'s menu does, saved on the way out and started again from there; the app started again in a story: {"; ".join(report)}')


if __name__ == '__main__':
    main()
