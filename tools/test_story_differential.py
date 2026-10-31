#!/usr/bin/env python3
"""Story mode against stock ScummVM 2.9.1: the original games, frame by frame.

Story mode is meant to run each original game as it was made, as ScummVM
runs it, apart from deliberate, documented differences (docs/
SCUMMVERSE_ARCHITECTURE.md, Story play). This drives our build in Story mode
(as its list starts a game: scummverse_mode=story, the game chosen there)
and a stock ScummVM 2.9.1 build (the pinned upstream commit, configured as
build/null for the SCUMM engines) the same way, and compares every frame.

Both binaries are linked from their own build's objects with the same probes
(temporary copies; never the source or the builds):
- tools/probes/story_differential_backend.inc in the null backend: a clock
  that moves only when something waits (a run is the same on any machine,
  and nothing sleeps), the sound mixed as that clock passes, a screen that
  keeps what is drawn, a fixed date;
- tools/probes/story_differential.inc at the top of the SCUMM main loop:
  each frame's screen (pixels, palette, cursor, shake), sound, variables,
  bit variables, objects, actors, script slots and pending save or load, as
  hashes; full dumps at fixed frames; and the same inputs at the same
  frames (Escape, the talk-skip key, a click every 8 frames on a verb, a
  thing or anywhere, right clicks, the game's own menu key, ScummVM's save
  and then load of slot 7 every 1000 frames), from the probe's own numbers;
  in the oldest games (V1-V3, a file a room), a room tour: every --tour
  frames the player's character is taken to the next room, as ScummVM's
  debugger's room command does, so play goes on in every room (not Indy3:
  TOUR_SKIP).
Both runs use the same random seed (random_seed), text on (as Story mode
sets it), ScummVM's autosave and a fresh save folder. The saves both wrote
must be the same byte for byte; then both go on from the last one, as Story
mode's Continue does (ours from its story save, stock told to load it).

Deliberate differences, documented, are told apart and not failed:
- Story play answers Monkey Island 2's and Sam & Max's copy protection: the
  stock build is given the same answers at the same point of the same
  frames (tools/probes/story_differential_guard.inc), so those games are
  compared past them (--no-guard shows where that difference begins).
- A story whose folder lacks a file its engine needs (kWorldStoryNeeds) is
  refused in words by Story mode's list; stock ScummVM stops on it.
- ScummVM's autosave due in the frame the game itself asked for a save or
  load: stock puts the autosave in the game's request's place, ours lets
  the game's go first (saveload.cpp saveGameState). Seen by moving the
  autosaves 7 seconds and running again: that frame must then be the same.
- Maniac Mansion V1 has 5 actor slots more for other worlds' guests, never
  used in a story; its own 25 are compared.
A game away from its main loop for a minute of game time (a film, a
question nobody answers) is pressed Escape, N and Return, as a player
would. A game that hangs (30 s of real time with no wait), is stuck (20
minutes of game time with no frame), crashes or stops on an error in both
builds after the same frames is noted, not failed (stock does it too).
Any other difference fails: the first frame that differs is looked at
closely (both run again, the frames around it written out): what differs
(variables by number, objects, actors, script slots, pixels, palette
entries). Screens are written as PNG files in --out only.

Usage: tools/test_story_differential.py game-data/mm-dos [monkey=game-data/monkey1-vga ...]
  --stock DIR: a built stock ScummVM 2.9.1 null-backend build (default
  build/stock-2.9.1; with --make-stock it is made there when missing:
  git archive of engine/'s pinned HEAD, configured with build/null's options
  without our engine, nice make -j2; skipped, with a note, when absent).
With no games given: Maniac Mansion's own story and every game folder under
game-data/ the catalog names. All of them at the defaults (3000 frames each,
then 2000 from the last save) take about 2 minutes; runs are the same
whatever else the machine is doing (the probe's clock).
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import shutil
import struct
import subprocess
import tempfile
import time
import zlib

ROOT = Path(__file__).resolve().parents[1]
PROBES = Path(__file__).resolve().parent/'probes'

# The catalog's games (common/scummverse_world_catalog.h) and their usual
# folders under game-data/.
DEFAULT = {'monkey': 'monkey1-vga', 'monkey2': 'monkey2-vga', 'loom': 'loom-ega', 'indy3': 'indy3-vga', 'atlantis': 'atlantis-mac',
           'tentacle': 'tentacle-floppy', 'samnmax': 'samnmax-floppy', 'ft': 'ft', 'dig': 'dig', 'comi': 'comi', 'zak': 'zak-dos'}
ORDER = ['maniac', 'zak', 'monkey', 'monkey2', 'loom', 'indy3', 'atlantis', 'tentacle', 'samnmax', 'ft', 'dig', 'comi']
FIELDS = ('t', 'spun', 'room', 'ego', 'cam', 'screen', 'palette', 'cursor', 'shake', 'audio', 'vars', 'bits', 'objects', 'actors', 'slots', 'pending', 'event')

LOOP = '\twhile (!shouldQuit()) {\n\t\t// Determine how long to wait before the next loop iteration should start\n'
NAMESPACE = '\nnamespace Scumm {\n\n// Use g_scumm from error() ONLY\n'
GUARD_AT = '\tif (_currentRoom == 0) {\n\t\tif (_game.version > 3)\n\t\t\tdisplayDialog();\n'
OURS_GUARD = '\tscummverseUpdateStory(delta);\n'
DECLARATIONS = '''
// SCUMMVERSE story differential (test only): the probe backend's side.
bool scummverseDiffScreen(const byte *&pixels, int &w, int &h, int &pitch, int &bpp, const byte *&palette, uint32 &cursor, int &shake, bool &cursorShown);
uint32 scummverseDiffAudio();
uint32 scummverseDiffNow();
uint32 scummverseDiffSpun();
void scummverseDiffFrame();
'''
BACKEND_AT = '#include "gui/debugger.h"\n#endif\n'
GRAPHICS = '_graphicsManager = new NullGraphicsManager();'
MIXER = '((NullMixerManager *)_mixerManager)->update(1);'
CLOCK = {
    'uint32 OSystem_NULL::getMillis(bool skipRecord) {':
        '\tif (++g_diffSpins >= 100000) {\n\t\tg_diffSpins = 0;\n\t\t++g_diffNow;\n\t\t++g_diffSpun;\n\t}\n\treturn g_diffNow;\n',
    'void OSystem_NULL::delayMillis(uint msecs) {':
        '\tg_diffSpins = 0;\n\tg_diffNow += msecs ? msecs : 1;\n\tdiffAlive();\n',
    'void OSystem_NULL::getTimeAndDate(TimeDate &td, bool skipRecord) const {':
        '\tconst uint32 t = 12 * 3600 + g_diffNow / 1000;\n\ttd.tm_sec = t % 60;\n\ttd.tm_min = t / 60 % 60;\n\ttd.tm_hour = t / 3600 % 24;\n'
        '\ttd.tm_mday = 1 + t / 86400 % 28;\n\ttd.tm_mon = 0;\n\ttd.tm_year = 101;\n\ttd.tm_wday = 1;\n',
}

# Differences known to be deliberate (docs/SCUMMVERSE_ARCHITECTURE.md), by
# what they touch. Anything else found is unexpected.
KNOWN_HEAD = {
    # Maniac Mansion V1: 5 actor slots more, for other worlds' guests (never
    # saved, no costume, never used in a story; scumm.cpp setupScumm). The
    # probe compares the game's own 25.
    ('maniac', 'actors'): 'Maniac Mansion V1 keeps 5 more actor slots for other worlds\' guests (scumm.cpp setupScumm; never used in a story); its own 25 are compared',
}

# Games the room tour (--tour) leaves out: stock ScummVM 2.9.1 itself writes
# past a mask buffer (Gdi::decodeMask) a while after Indy is put in room 9
# that way (as by ScummVM's debugger's room command), and a heap so damaged
# need not fail the same way in both builds.
TOUR_SKIP = {'indy3'}


def once(code, mark, where):
    if code.count(mark) != 1:
        raise SystemExit(f'FAIL: pinned boundary changed in {where}: {mark!r}')


def source_dir(build):
    m = re.search(r'^srcdir = (.*)$', (build/'Makefile').read_text(), re.M)
    if not m:
        raise SystemExit(f'FAIL: {build} is not a configured ScummVM build')
    return m.group(1).strip()


def command_for(build, source, target):
    """The build's own compiler (or linker) argv for target, source as make names it."""
    output = subprocess.check_output(['make', '-n', '-W', source, target], cwd=build, text=True, stderr=subprocess.DEVNULL)
    for line in output.splitlines():
        if ';' in line and (' LINK ' if target == 'scummvm' else ' C++ ') in line:
            return shlex.split(line.split(';', 1)[1])
    raise SystemExit(f'FAIL: no command for {target} in {build}')


def make_stock(stock, ours):
    """Stock ScummVM 2.9.1 for the null backend: the pinned upstream commit, our build's configure options, SCUMM only."""
    engine = Path(source_dir(ours))
    engine = engine if engine.is_absolute() else (ours/engine).resolve()
    # (engine/'s HEAD is the pinned upstream commit, upstream.json beside it;
    # its working tree holds our patches and is not read.)
    pin = subprocess.check_output(['git', '-C', str(engine), 'rev-parse', 'HEAD'], text=True).strip()
    pinned = engine.parent/'upstream.json'
    if pinned.exists() and json.loads(pinned.read_text())['commit'] != pin:
        raise SystemExit(f'FAIL: {engine} is at {pin}, not the commit {pinned} pins')
    flags = shlex.split(re.search(r'^SAVED_CONFIGFLAGS\s*:=\s*(.*)$', (ours/'config.mk').read_text(), re.M).group(1))
    # (Our own engine is not in the stock source.)
    flags = [','.join(e for e in f.split(',') if e != 'scummverse') if f.startswith('--enable-engine=') else f for f in flags]
    source = stock/'source'
    shutil.rmtree(source, ignore_errors=True)
    source.mkdir(parents=True)
    archive = subprocess.Popen(['git', '-C', str(engine), 'archive', pin], stdout=subprocess.PIPE)
    subprocess.run(['tar', '-x', '-C', str(source)], stdin=archive.stdout, check=True)
    if archive.wait():
        raise SystemExit('FAIL: git archive of the pinned commit')
    print(f'making stock ScummVM 2.9.1 in {stock} ({" ".join(flags)})', flush=True)
    for cmd in (['nice', str(source/'configure')] + flags, ['nice', 'make', '-j2']):
        done = subprocess.run(cmd, cwd=stock, capture_output=True, text=True)
        if done.returncode:
            raise SystemExit(f'FAIL: {" ".join(cmd)}\n' + (done.stdout + done.stderr)[-4000:])


def probe_binary(build, work, stock):
    """build's scummvm with the probes: its own objects, scumm.o and null.o rebuilt from probe copies."""
    srcdir = source_dir(build)
    src = Path(srcdir) if Path(srcdir).is_absolute() else (build/srcdir).resolve()
    scumm = (src/'engines/scumm/scumm.cpp').read_text()
    null = (src/'backends/platform/null/null.cpp').read_text()
    for mark in (LOOP, NAMESPACE, GUARD_AT):
        once(scumm, mark, f'{src}/engines/scumm/scumm.cpp')
    if stock and OURS_GUARD in scumm:
        raise SystemExit(f'FAIL: {build} is not a stock build (its scumm.cpp has story play)')
    if not stock:
        # (Ours: story play's own answers, where the stock build is given them.)
        once(scumm, OURS_GUARD + GUARD_AT, f'{src}/engines/scumm/scumm.cpp')
    scumm = scumm.replace(NAMESPACE, DECLARATIONS + NAMESPACE)
    scumm = scumm.replace(LOOP, LOOP.split('\n')[0] + '\n' + (PROBES/'story_differential.inc').read_text() + '\n'.join(LOOP.split('\n')[1:]))
    if stock:
        scumm = scumm.replace(GUARD_AT, (PROBES/'story_differential_guard.inc').read_text() + GUARD_AT)
    for mark in [BACKEND_AT, GRAPHICS, MIXER] + list(CLOCK):
        once(null, mark, f'{src}/backends/platform/null/null.cpp')
    null = null.replace(BACKEND_AT, BACKEND_AT + (PROBES/'story_differential_backend.inc').read_text())
    null = null.replace(GRAPHICS, '_graphicsManager = g_diffScreen = new DiffGraphicsManager();')
    null = null.replace(MIXER, 'scummverseDiffMix(_mixerManager);\n\tif (scummverseDiffNudge(event))\n\t\treturn true;')
    for head, body in CLOCK.items():
        start = null.index(head) + len(head) + 1
        end = null.index('\n}\n', start) + 1
        null = null[:start] + body + null[end:]
    objects = {}
    for rel, code in (('engines/scumm/scumm.cpp', scumm), ('backends/platform/null/null.cpp', null)):
        probe = work/Path(rel).name
        probe.write_text(code)
        target = rel.replace('.cpp', '.o')
        named = f'{srcdir}/{rel}'
        cmd = command_for(build, named, target)
        cmd[cmd.index(named)] = str(probe)
        obj = work/Path(target).name
        cmd[cmd.index('-o') + 1] = str(obj)
        if '-MF' in cmd:
            cmd[cmd.index('-MF') + 1] = str(work/(Path(target).stem + '.d'))
        built = subprocess.run(['nice'] + cmd, cwd=build, capture_output=True, text=True)
        if built.returncode:
            raise SystemExit(f'FAIL: the probe copy of {rel} does not compile in {build}\n' + built.stderr[-6000:])
        objects[target] = obj
    archive = work/'libscumm.a'
    shutil.copy2(build/'engines/scumm/libscumm.a', archive)
    subprocess.run(['ar', 'r', str(archive), str(objects['engines/scumm/scumm.o'])], check=True)
    cmd = command_for(build, 'engines/scumm/libscumm.a', 'scummvm')
    cmd[cmd.index('engines/scumm/libscumm.a')] = str(archive)
    cmd[cmd.index('backends/platform/null/null.o')] = str(objects['backends/platform/null/null.o'])
    exe = work/'scummvm'
    cmd[cmd.index('-o') + 1] = str(exe)
    subprocess.run(['nice'] + cmd, cwd=build, check=True, capture_output=True)
    for o in list(objects.values()) + [archive]:
        o.unlink()
    return exe


def run(exe, stock, game, path, maniac, out, a, autosave, window=(-1, -1), start=None, frames=None):
    """One game in one build: its frames.txt (and dumps) in out; the seconds it took, or None when it did not start.

    start: a save to go on from (as Story mode's Continue: its story save,
    slot 99, the newest it has; the stock build told to load that slot)."""
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    saves = out/'saves'
    saves.mkdir()
    target = game if stock else f'scummverse-story-{game}'
    if start:
        shutil.copy2(start, saves/f'{target}.s99')
    keys = (f'random_seed={a.seed}\nautosave_period={autosave}\nscummverse_diff_out={out}\nscummverse_diff_target={target}\nscummverse_diff_frames={frames or a.frames}\nscummverse_diff_every={a.every}\n'
            f'scummverse_diff_from={window[0]}\nscummverse_diff_to={window[1]}\nscummverse_diff_seed={a.seed}\n'
            f'scummverse_diff_tour={0 if game in TOUR_SKIP else a.tour}\n')
    config = out/'run.ini'
    if stock:
        # The game's target as Story mode makes it (common/scummverse_story.h
        # addStoryTarget): its id and folder, text on; the mansion's platform.
        guard = '' if a.no_guard else 'scummverse_diff_guard=1\n'
        config.write_text(f'[scummvm]\n{keys}{guard}\n[{target}]\ngameid={game}\nengineid=scumm\ndescription={game}\n'
                          f'path={path}\nsubtitles=true\n' + ('platform=dos\n' if game == 'maniac' else '') + ('save_slot=99\n' if start else ''))
        cmd, cwd = [str(exe), f'--config={config}', f'--savepath={saves}', target], out
    else:
        # Story mode, the game chosen from its list (Documents: the game's
        # folder; the worlds cache's markers, so nothing is set up first).
        docs = out/'documents'
        docs.mkdir()
        if game != 'maniac':
            (docs/game).symlink_to(path)
        (docs/'worlds').mkdir()
        for marker in Path(a.worlds).glob('*.svx'):
            shutil.copy2(marker, docs/'worlds'/marker.name)
        config.write_text(f'[scummvm]\n{keys}scummverse_mode=story\nscummverse_story_choices={game}\n'
                          'scummverse_roaming=false\nscummverse_wanderers=false\n')
        cmd, cwd = [str(exe), f'--config={config}', f'--path={maniac}', f'--savepath={saves}'], docs
    # (Neither build is given a debug level, as a phone has none: stock
    # ScummVM would make it the game's own debug mode, which its scripts
    # read; ours, from 0275, keeps that off whatever the level.)
    assert not any(c.startswith(('-d', '--debuglevel')) for c in cmd), cmd
    started = time.time()
    result = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=a.timeout)
    (out/'output.log').write_text(result.stdout + result.stderr)
    (out/'exit.txt').write_text(str(result.returncode))
    # (Stopped before its last frame, by an error or hung: its frames so far,
    # each written as it came, as ScummVM left them.)
    if not (out/'frames.txt').exists() and (out/'frames.txt.tmp').exists():
        (out/'frames.txt.tmp').rename(out/'frames.txt')
    return time.time() - started if (out/'frames.txt').exists() else None


def stop_reason(out):
    """Why a run stopped before its last frame (hung, crashed, or ScummVM's error), else None."""
    log = (out/'output.log').read_text()
    if 'SCUMMVERSE_DIFF_DONE' in log:
        return None
    if 'SCUMMVERSE_DIFF_HUNG' in log:
        return 'hung'
    if 'SCUMMVERSE_DIFF_STUCK' in log:
        return 'stuck (no frame for 20 minutes of game time)'
    code = int((out/'exit.txt').read_text())
    if code < 0:
        return f'crashed (signal {-code})'  # (as the heap fell: its words differ from one build to another)
    said = [l for l in log.splitlines() if l.strip() and not l.startswith('debug>') and 'Debugger' not in l]
    return 'error: ' + (said[-1][:200] if said else '?')


def first_difference(rs, ro):
    """The first frame that differs (and in what), or (None, [])."""
    n = min(len(rs), len(ro))
    for i in range(n):
        fields = [f for f in FIELDS if rs[i].get(f) != ro[i].get(f)]
        if fields:
            return rs[i]['frame'], fields
    return (n, ['frames']) if len(rs) != len(ro) else (None, [])


def story_needs(ours, game, path):
    """The first file the game's story needs (kWorldStoryNeeds, in our catalog) that its folder lacks, else None."""
    srcdir = source_dir(ours)
    src = Path(srcdir) if Path(srcdir).is_absolute() else (ours/srcdir).resolve()
    catalog = (src/'common/scummverse_world_catalog.h').read_text()
    m = re.search(r'\{"' + re.escape(game) + r'", \{([^}]*)\}\}', catalog)
    if not m:
        return None
    here = {f.name.lower() for d in [path] + [d for d in path.iterdir() if d.is_dir() and d.name.lower() in ('data', 'video', 'resource')]
            for f in d.iterdir()}
    for name in re.findall(r'"([^"]+)"', m.group(1)):
        if name.lower() not in here:
            return name.upper()
    return None


def frames_of(out):
    lines = (out/'frames.txt').read_text().splitlines()
    head = dict(zip(lines[0].split()[0::2], lines[0].split()[1::2])) if lines else {}
    rows = []
    for line in lines[1:]:
        parts = line.split()
        if not parts or not parts[0].isdigit():
            continue
        if len(parts) == 3 and parts[1] in ('save', 'load', 'tour') and rows:
            # (ScummVM's save or load asked for in that frame, and whether it
            # was taken; the room the tour took the player's character to.)
            rows[-1]['event'] = rows[-1].get('event', '') + f'{parts[1]}={parts[2]} '
            continue
        row = {'frame': int(parts[0])}
        for p in parts[1:]:
            k, _, v = p.partition('=')
            row[k] = v
        rows.append(row)
    return head, rows


def state_of(path):
    """A state dump: {kind: {key: value}}."""
    got = {'var': {}, 'bit': {}, 'object': {}, 'actor': {}, 'slot': {}, 'head': {}}
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        p = line.split()
        if p[0] == 'frame':
            got['head'] = dict(zip(p[0::2], p[1::2]))
        elif p[0] == 'var':
            got['var'][int(p[1])] = int(p[2])
        elif p[0] == 'bit':
            got['bit'][int(p[1])] = 1
        elif p[0] in ('object', 'actor', 'slot'):
            got[p[0]][int(p[1])] = ' '.join(p[2:])
    return got


def shot_of(path):
    if not path.exists():
        return None
    data = path.read_bytes()
    head, rest = data.split(b'\n', 1)
    _, w, h, bpp = head.split()
    w, h, bpp = int(w), int(h), int(bpp)
    return w, h, bpp, rest[:768], rest[768:768 + w * h * bpp]


def png(path, shot):
    """An indexed screen as an RGB PNG (written in --out only)."""
    w, h, bpp, palette, pixels = shot
    rows = bytearray()
    for y in range(h):
        rows.append(0)
        line = pixels[y * w * bpp:(y + 1) * w * bpp]
        if bpp == 1:
            for c in line:
                rows += palette[3 * c:3 * c + 3]
        else:
            for x in range(w):
                v = line[2 * x] | line[2 * x + 1] << 8
                rows += bytes(((v >> 11) << 3 & 255, (v >> 5 & 63) << 2, (v & 31) << 3))

    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) +
                     chunk(b'IDAT', zlib.compress(bytes(rows), 6)) + chunk(b'IEND', b''))


def compare_states(a_state, b_state):
    """What differs between two dumps, in words (numbers only)."""
    said = []
    for kind in ('var', 'bit', 'object', 'actor', 'slot'):
        x, y = a_state[kind], b_state[kind]
        keys = sorted(set(x) | set(y))
        diff = [k for k in keys if x.get(k, 0 if kind == 'var' else None) != y.get(k, 0 if kind == 'var' else None)]
        if diff:
            shown = ', '.join(f'{k}: {x.get(k, 0 if kind == "var" else "-")} / {y.get(k, 0 if kind == "var" else "-")}' for k in diff[:12])
            said.append(f'{len(diff)} {kind}{"s" if len(diff) > 1 else ""} differ (stock / ours): {shown}{" ..." if len(diff) > 12 else ""}')
    for k in ('room', 'ego', 'cam', 'userput', 'cursorstate'):
        if a_state['head'].get(k) != b_state['head'].get(k):
            said.append(f'{k}: {a_state["head"].get(k)} / {b_state["head"].get(k)}')
    return said


def compare_shots(a_shot, b_shot):
    if not a_shot or not b_shot:
        return ['no screen in one of them']
    if a_shot[:3] != b_shot[:3]:
        return [f'screen size {a_shot[:3]} / {b_shot[:3]}']
    said = []
    w, h, bpp = a_shot[:3]
    pal = [i for i in range(256) if a_shot[3][3 * i:3 * i + 3] != b_shot[3][3 * i:3 * i + 3]]
    if pal:
        said.append(f'{len(pal)} palette entries differ (first {pal[:8]})')
    pa, pb = a_shot[4], b_shot[4]
    if pa != pb:
        xs, ys, n = [], [], 0
        for y in range(h):
            ra, rb = pa[y * w * bpp:(y + 1) * w * bpp], pb[y * w * bpp:(y + 1) * w * bpp]
            if ra != rb:
                cols = [x for x in range(w) if ra[x * bpp:(x + 1) * bpp] != rb[x * bpp:(x + 1) * bpp]]
                n += len(cols)
                ys.append(y)
                xs += [cols[0], cols[-1]]
        said.append(f'{n} pixels differ, within x {min(xs)}-{max(xs)}, y {min(ys)}-{max(ys)}')
    return said


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('maniac', type=Path, help="the mansion's folder (Maniac Mansion's own story)")
    p.add_argument('games', nargs='*', help='folder=path pairs, e.g. monkey=game-data/monkey1-vga')
    p.add_argument('--stock', type=Path, default=ROOT/'build/stock-2.9.1', help='a built stock ScummVM 2.9.1 null-backend build '
                   '(default build/stock-2.9.1; see --make-stock)')
    p.add_argument('--make-stock', action='store_true', help='make the stock build first if it is not there: the pinned upstream '
                   "source (engine/'s git HEAD, through git archive: its working tree and git state untouched) in STOCK/source, "
                   "configured with build/null's options for the SCUMM engines, built with nice make -j2")
    p.add_argument('--ours', type=Path, default=ROOT/'build/null', help='our null-backend build (default build/null)')
    p.add_argument('--worlds', type=Path, default=ROOT/'build/worlds', help="the worlds cache (its markers: nothing set up first)")
    p.add_argument('--frames', type=int, default=3000)
    p.add_argument('--every', type=int, default=500, help='full dumps and screens every this many frames')
    p.add_argument('--seed', type=int, default=20250101)
    p.add_argument('--no-maniac', action='store_true')
    p.add_argument('--out', type=Path, help='keep the runs here (screens as PNG); default a temporary folder')
    p.add_argument('--timeout', type=int, default=1800)
    p.add_argument('--autosave', type=int, default=300, help="ScummVM's autosave period, seconds (its default 300)")
    p.add_argument('--tour', type=int, default=500, help="the oldest games (V1-V3, a file a room): every this many frames the player's "
                   "character is taken to the next room, as ScummVM's debugger does, so play goes on in every room (0: not)")
    p.add_argument('--continue-frames', type=int, default=2000, help='frames played again from the last save, as Story mode goes on from it (0: not)')
    p.add_argument('--no-guard', action='store_true', help="the stock build not given story play's copy-protection answers "
                   '(shows where that deliberate difference begins; the test then fails there)')
    a = p.parse_args()
    pairs = [g.split('=', 1) for g in a.games] if a.games else [(k, str(ROOT/'game-data'/v)) for k, v in DEFAULT.items() if (ROOT/'game-data'/v).is_dir()]
    games = [(k, Path(v).resolve()) for k, v in pairs]
    for k, _ in games:
        if k not in ORDER or k == 'maniac':
            raise SystemExit(f'not a story game: {k}')
    if not a.no_maniac:
        games.insert(0, ('maniac', a.maniac.resolve()))
    games.sort(key=lambda g: ORDER.index(g[0]))
    if a.make_stock and not (a.stock/'scummvm').exists():
        make_stock(a.stock.resolve(), a.ours.resolve())
    if not (a.stock/'scummvm').exists():
        print(f'SKIP: story differential: no stock ScummVM 2.9.1 build in {a.stock} (--make-stock makes one, a few minutes)')
        return
    for build in (a.stock, a.ours):
        if not (build/'Makefile').exists() or not (build/'scummvm').exists():
            raise SystemExit(f'FAIL: {build} is not a built ScummVM build')
    with tempfile.TemporaryDirectory(prefix='scummverse-story-differential-', dir=ROOT/'build' if (ROOT/'build').is_dir() else None) as tmp:
        work = Path(a.out).resolve() if a.out else Path(tmp)
        work.mkdir(parents=True, exist_ok=True)
        bins = {}
        for name, build, stock in (('stock', a.stock.resolve(), True), ('ours', a.ours.resolve(), False)):
            (work/name).mkdir(exist_ok=True)
            bins[name] = probe_binary(build, work/name, stock)
        results, unexpected = [], []
        for game, path in games:
            runs = {name: work/'runs'/game/name for name in ('stock', 'ours')}
            shown = len(results)
            notes, period = [], a.autosave
            while True:
                took = {name: run(bins[name], name == 'stock', game, path, a.maniac.resolve(), runs[name], a, period) for name in runs}
                if took['ours'] is None or took['stock'] is None:
                    break
                (hs, rs), (ho, ro) = frames_of(runs['stock']), frames_of(runs['ours'])
                first, fields = first_difference(rs, ro)
                # ScummVM's autosave due in the frame the game itself asked
                # for a save or load (its own, for the next frame): stock
                # ScummVM 2.9.1 puts the autosave in its place (the game's
                # request lost), ours lets the game's go first (deliberate:
                # saveload.cpp saveGameState, "never over a save or load
                # already asked for"; docs/SCUMMVERSE_PROGRESS.md, "A save or
                # load already waiting"). Seen by moving the autosaves: run
                # again with them 7 seconds further apart, that frame must
                # then be the same.
                if first and fields != ['frames'] and rs[first - 1].get('pending', '0/0/0') != '0/0/0' and len(notes) < 4:
                    was = (first, period, rs[first - 1]['pending'])
                    period += 7
                    notes.append(was)
                    continue
                break
            if took['ours'] is None or took['stock'] is None:
                # A story that needs a file its folder lacks is refused in
                # words by Story mode's list (kWorldStoryNeeds: its engine
                # would stop the app); stock ScummVM stops with an error.
                logs = {n: (runs[n]/'output.log').read_text() for n in runs}
                lacking = story_needs(a.ours.resolve(), game, path)
                refused = 'SCUMMVERSE: Explore mode' in logs['ours'] or 'SCUMMVERSE_DIFF_OTHER' in logs['ours']
                stopped = re.findall(r'Cannot open file [^\n]*|could not start[^\n]*', logs['stock'])
                if lacking and took['ours'] is None and refused:
                    results.append(f'{game}: not compared: its folder lacks {lacking}; Story mode refuses it in words (deliberate, kWorldStoryNeeds), '
                                   f'stock ScummVM ' + (f'stops: {stopped[0]}' if took['stock'] is None else 'starts'))
                else:
                    unexpected.append(f'{game}: did not start in the {"Story mode" if took["ours"] is None else "stock"} build\n' +
                                      logs['ours' if took['ours'] is None else 'stock'][-2000:])
                    results.append(f'{game}: did not start')
                print(results[-1], flush=True)
                continue
            said_notes = []
            for at, every, pending in notes:
                kind = {'1': 'save', '2': 'load'}.get(pending.split('/')[0], '?')
                moved = first is None or first > at
                text = (f'{game}: with autosaves every {every} s, ScummVM\'s autosave fell in frame {at - 1}, where the game had asked for a {kind} '
                        f'(slot {pending.split("/")[1]}{", temporary" if pending.endswith("/1") else ""}): stock puts the autosave in its place, ours '
                        'lets the game\'s go first (deliberate: saveload.cpp saveGameState; docs/SCUMMVERSE_PROGRESS.md "A save or load already waiting")')
                if moved:
                    said_notes.append(text + f'; with them every {every + 7} s that frame is the same')
                else:
                    unexpected.append(text + f', but with them every {every + 7} s it still differs at frame {first}')
            for k in sorted(set(hs) | set(ho)):
                if hs.get(k) != ho.get(k):
                    known = KNOWN_HEAD.get((game, k))
                    (said_notes if known else unexpected).append(f'{game}: {k} {hs.get(k)} / {ho.get(k)}' + (f' (deliberate: {known})' if known else ''))
            nudged = [(runs[name]/'output.log').read_text().count('SCUMMVERSE_DIFF_NUDGE') for name in ('stock', 'ours')]
            if any(nudged):
                said_notes.append(f'{game}: its main loop away for a minute of game time {nudged[0]} / {nudged[1]} times: Escape, N and Return pressed')
            guarded = [l for l in (runs['stock']/'output.log').read_text().splitlines() if 'SCUMMVERSE_DIFF_GUARD' in l]
            answered = [l for l in (runs['ours']/'output.log').read_text().splitlines() if 'copy protection answered' in l or 'copy protection left' in l]
            if guarded or answered:
                said_notes.append(f'{game}: copy protection answered {len(answered)} times by story play, {len(guarded)} times in the stock build '
                                  '(deliberate: story play answers it; the stock build given the same answers)')
            n = min(len(rs), len(ro))
            why = {name: stop_reason(runs[name]) for name in runs}
            if first is None and (why['stock'] or why['ours']):
                # (Both stopped at the same frame, as stock ScummVM does there.)
                (said_notes if why['stock'] == why['ours'] else unexpected).append(
                    f'{game}: both stopped after frame {n - 1}: {why["stock"]} / {why["ours"]}')
            line = f'{game}: {n} frames, {took["stock"]:.0f} s / {took["ours"]:.0f} s, autosaves every {period} s'
            rooms = sorted({int(r['room']) for r in rs[:n]})
            if first is None:
                results.append(f'{line}: identical (rooms {rooms})')
            else:
                # Both again, every part of the frames around it written out.
                window = (max(0, first - 2), first + 2)
                for name in runs:
                    run(bins[name], name == 'stock', game, path, a.maniac.resolve(), runs[name], a, period, window)
                said = [f'first differs at frame {first} (room {rs[first]["room"] if first < len(rs) else "?"} / {ro[first]["room"] if first < len(ro) else "?"}): {", ".join(fields)}']
                (_, ws), (_, wo) = frames_of(runs['stock']), frames_of(runs['ours'])
                for f in range(window[0], window[1] + 1):
                    sa, so = state_of(runs['stock']/f'state-{f:05d}.txt'), state_of(runs['ours']/f'state-{f:05d}.txt')
                    what = [f'{k} {ws[f].get(k)} / {wo[f].get(k)}' for k in FIELDS if f < min(len(ws), len(wo)) and ws[f].get(k) != wo[f].get(k)
                            and k in ('t', 'spun', 'room', 'ego', 'cam', 'cursor', 'shake', 'audio', 'pending', 'event')]
                    if sa and so:
                        what += compare_states(sa, so) + compare_shots(shot_of(runs['stock']/f'shot-{f:05d}.raw'), shot_of(runs['ours']/f'shot-{f:05d}.raw'))
                    if what:
                        said.append(f'  frame {f}: ' + '; '.join(what))
                unexpected.append(f'{line}:\n    ' + '\n    '.join(said))
                results.append(f'{line}: differs from frame {first}')
            if first is None:
                # The saves both wrote (ScummVM's, the game's own; not story
                # play's own story saves), byte for byte.
                for f in sorted((runs['stock']/'saves').iterdir()):
                    mine = runs['ours']/'saves'/f.name.replace(game + '.', f'scummverse-story-{game}.', 1)
                    if not mine.exists():
                        unexpected.append(f'{game}: {f.suffix} written by stock only')
                    elif mine.read_bytes() != f.read_bytes():
                        x, y = f.read_bytes(), mine.read_bytes()
                        at = next((i for i in range(min(len(x), len(y))) if x[i] != y[i]), min(len(x), len(y)))
                        unexpected.append(f'{game}: its {f.suffix} save differs ({len(x)} / {len(y)} bytes, first at byte {at})')
                saved = runs['stock']/'saves'/f'{game}.s07'
                if a.continue_frames and saved.exists():
                    # Story mode's Continue: both go on from that save (ours
                    # as its story save, slot 99; stock told to load it).
                    kept = work/'runs'/game/'continue.s07'
                    shutil.copy2(saved, kept)
                    cont = {name: work/'runs'/game/f'{name}-continue' for name in runs}
                    gone = {name: run(bins[name], name == 'stock', game, path, a.maniac.resolve(), cont[name], a, period, start=kept,
                                      frames=a.continue_frames) for name in cont}
                    if None in gone.values():
                        unexpected.append(f'{game}: did not go on from its save in the {"Story mode" if gone["ours"] is None else "stock"} build')
                    else:
                        (_, cs), (_, co) = frames_of(cont['stock']), frames_of(cont['ours'])
                        again, what = first_difference(cs, co)
                        if again is None:
                            results.append(f'  {game}: gone on from its save (room {cs[0]["room"]}) for {len(cs)} frames: identical')
                        else:
                            unexpected.append(f'{game}: gone on from its save, first differs at frame {again}: {", ".join(what)}')
                            results.append(f'  {game}: gone on from its save: differs from frame {again}')
                    for name in cont:
                        for raw in cont[name].glob('shot-*.raw'):
                            raw.unlink()
                        shutil.rmtree(cont[name]/'documents', ignore_errors=True)
            results += ['  ' + x for x in said_notes]
            # Screens as PNG (in --out only), and the raw dumps dropped.
            for name in runs:
                for raw in sorted(runs[name].glob('shot-*.raw')):
                    if a.out:
                        png(raw.with_suffix('.png'), shot_of(raw))
                    raw.unlink()
                shutil.rmtree(runs[name]/'documents', ignore_errors=True)
            print('\n'.join(results[shown:]), flush=True)
        if unexpected:
            raise SystemExit('FAIL: story differential:\n  ' + '\n  '.join(results) + '\nunexpected:\n  ' + '\n  '.join(unexpected))
        print('PASS: story differential: every game in Story mode as in stock ScummVM 2.9.1, frame by frame (screen, palette, sound, '
              'variables, objects, actors, scripts), the same inputs and seed:\n  ' + '\n  '.join(results))


if __name__ == '__main__':
    main()
