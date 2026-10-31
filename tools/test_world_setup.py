#!/usr/bin/env python3
"""Other worlds at launch: which supplied games the app sets up, like on iOS.

Runs the real binary on a temporary Documents folder (maniac/ plus one other
game) and checks that the game's folder is found despite stray spaces or
case ("loom " from a zip made on a Mac) and one folder further down (the
Files app unzips a zip of several folders into a folder named after it,
next to a Mac's __MACOSX, which is never taken for the game), that a game
whose setup stopped twice is skipped and logged, and that one which stopped
once is retried. From 0273 also that a game set up with a debug level
(--debuglevel=1, as the tests start the app) writes the same files, byte
for byte, as one set up without: its scripts read their debug mode (with
monkey=game-data/monkey1-vga, Monkey Island's room 14 object 176's Turn on).
From 0284 also that one set up with its export's runs played in the
opposite order (scummverse_export_order=reversed: every run starts from the
game put back whole) records the same: every other file byte for byte, its
things file answer for answer (the answers may be written in another order).
Needs privately supplied games; nothing is copied out of build/.

Usage: tools/test_world_setup.py game-data/mm-dos loom=game-data/loom-ega
"""
import argparse
import gzip
import re
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = (ROOT/'engine/common/scummverse_world_catalog.h').read_text()
VERSION = int(re.search(r'kWorldExportVersion = (\d+);', CATALOG).group(1))
# worldExportVersion's games ahead of the rest: ("maniac",) -> 7, ...
AHEAD = [(re.findall(r'same\(gameid, "(\w+)"\)', games), int(n)) for games, n in
         re.findall(r'((?:same\(gameid, "\w+"\)(?: \|\| )?)+) \? (\d+)',
                    re.search(r'return kWorldExportVersion \+ \((.*?)\);', CATALOG, re.S).group(1))]


def version(game):
    """A game's export marker version (worldExportVersion: some games ahead)."""
    return VERSION + next((n for games, n in AHEAD if game in games), 0)


def answers_of(data):
    """A things file (.svo) as (its bytes before its answers, its answers each
    as its bytes, sorted, its bytes after): see common/scummverse_panel.h."""
    raw = gzip.decompress(data) if data[:2] == b'\x1f\x8b' else data
    magic, at = raw[:4], 4
    # (From 0284 "SVOB" too: SVOA's answers, its valued ones after them;
    # from 0286 "SVOC" likewise, its later steps lines too.)
    ninth = magic in (b'SVO9', b'SVOA', b'SVOB', b'SVOC')
    pairs = ninth or magic in (b'SVO4', b'SVO5', b'SVO6', b'SVO7', b'SVO8')
    if not (pairs or magic in (b'SVO2', b'SVO3')):
        return raw, [], b''

    def u8():
        nonlocal at
        at += 1
        return raw[at - 1]

    def u16():
        nonlocal at
        at += 2
        return raw[at - 2] | raw[at - 1] << 8
    for _ in range(u16()):
        u16()
        things = u16()
        at += 5 * things
    head, answers = raw[:at], []
    for _ in range(u16()):
        start = at
        at += 6 + (2 if pairs else 0)
        # (Each read before it is skipped: `at += u8()` would add to the
        # `at` before the read.)
        if ninth:
            at += 2
            parts = u8()
            at += 6 * parts
            for _ in range(u8()):
                speaker = u8()
                at += (2 if speaker not in (0, 255) else 0) + (1 if speaker else 0)
                length = u8()
                at += length
        else:
            at += 1
            parts = u8()
            at += 5 * parts
            length = u8()
            at += length
        answers.append(raw[start:at])
    return head, sorted(answers), raw[at:]


def launch(binary, maniac, game, data, folder_name, attempts=None, timeout=300, extra=(), files=None, settings=''):
    """Start the app once; returns (log, finished marker written, attempt count).
    (From 0273 `extra` more arguments, and `files` filled with what it wrote;
    from 0284 `settings` more lines of its scummvm.ini.)"""
    with tempfile.TemporaryDirectory(prefix='scummverse-setup-', dir=ROOT/'build') as tmp:
        docs = Path(tmp)
        (docs/'maniac').symlink_to(maniac.resolve())
        (docs/folder_name).parent.mkdir(parents=True, exist_ok=True)
        (docs/folder_name).symlink_to(data.resolve())
        if '/' in folder_name:
            # A Mac's leftovers beside it: an empty folder of the same name.
            (docs/'__MACOSX'/Path(folder_name).name).mkdir(parents=True)
        worlds = docs/'worlds'
        worlds.mkdir()
        attempt = worlds/f'{game}-v{version(game)}.try'
        if attempts is not None:
            attempt.write_bytes(b'SVT1' + bytes([attempts]))
        (docs/'scummvm.ini').write_text('[scummvm]\n' + settings)
        proc = subprocess.Popen([str(binary), '--config=scummvm.ini', *extra], cwd=docs, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        lines, deadline = [], time.time() + timeout
        for line in proc.stdout:
            lines.append(line)
            # Setup finishes before Maniac starts.
            if "target 'maniac'" in line or time.time() > deadline:
                break
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        count = attempt.read_bytes()[4] if attempt.exists() and attempt.stat().st_size > 4 else None
        if files is not None:
            files.update((f.name, f.read_bytes()) for f in worlds.iterdir() if f.is_file() and f.suffix != '.try')
        return ''.join(lines), (worlds/f'{game}-v{version(game)}.svx').exists(), count


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('maniac', type=Path)
    p.add_argument('game', help='catalog folder=path, e.g. loom=game-data/loom-ega')
    p.add_argument('--binary', type=Path, default=ROOT/'build/null/scummvm')
    a = p.parse_args()
    folder, path = a.game.split('=', 1)
    data = Path(path)
    gameid = folder  # Every catalog game's folder is its game id.
    binary = a.binary.resolve()
    for name in (folder + ' ', folder.upper(), f'{folder}__samnmax_test/{folder} '):
        log, done, count = launch(binary, a.maniac, gameid, data, name)
        assert done and count == 1, (name, done, count, log[-3000:])
        print(f'PASS: folder named {name!r} is found and set up')
    log, done, count = launch(binary, a.maniac, gameid, data, folder, attempts=2)
    assert 'stopped twice' in log and not done and count == 2, (done, count, log[-3000:])
    print('PASS: a setup that stopped twice is skipped and logged')
    log, done, count = launch(binary, a.maniac, gameid, data, folder, attempts=1)
    assert 'stopped twice' not in log and done and count == 2, (done, count, log[-3000:])
    print('PASS: a setup that stopped once is retried and finishes')
    log, done, count = launch(binary, a.maniac, gameid, data, 'not-' + folder)
    assert not done and count is None and "target 'maniac'" in log, (done, count, log[-3000:])
    print('PASS: no matching folder, nothing set up; Maniac starts')
    # (From 0273: the same files with a debug level as without.)
    plain, debugged = {}, {}
    log, done, count = launch(binary, a.maniac, gameid, data, folder, files=plain)
    assert done, log[-3000:]
    log, done, count = launch(binary, a.maniac, gameid, data, folder, extra=('--debuglevel=1',), files=debugged)
    assert done, log[-3000:]
    differ = sorted(name for name in set(plain) | set(debugged) if plain.get(name) != debugged.get(name))
    assert not differ, f'set up otherwise with a debug level: {differ}'
    print(f'PASS: set up with a debug level, the same {len(plain)} files byte for byte')
    # (From 0284: its runs in the opposite order, the same records.)
    reversed_ = {}
    log, done, count = launch(binary, a.maniac, gameid, data, folder, files=reversed_, settings='scummverse_export_order=reversed\n')
    assert done, log[-3000:]
    differ = sorted(name for name in set(plain) | set(reversed_) if plain.get(name) != reversed_.get(name) and not name.endswith('-things.svo'))
    assert not differ, f'set up otherwise with its runs in the opposite order: {differ}'
    things = sorted(name for name in set(plain) | set(reversed_) if name.endswith('-things.svo'))
    for name in things:
        before, after = answers_of(plain.get(name, b'')), answers_of(reversed_.get(name, b''))
        lost = [r for r in before[1] if r not in after[1]]
        gained = [r for r in after[1] if r not in before[1]]
        assert before == after, (f'{name}: its runs in the opposite order record otherwise ({len(lost)} answers only forwards, {len(gained)} only backwards, '
                                 f'rest {"same" if before[0] == after[0] and before[2] == after[2] else "differs"}; '
                                 f'first answers only forwards, by room and thing: {[(r[0] | r[1] << 8, r[2] | r[3] << 8) for r in lost[:8]]})')
    print(f'PASS: set up with its runs in the opposite order, the same {len(plain)} files, {len(things)} things file answer for answer')


if __name__ == '__main__':
    main()
