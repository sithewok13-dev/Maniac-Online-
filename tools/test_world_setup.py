#!/usr/bin/env python3
"""Other worlds at launch: which supplied games the app sets up, like on iOS.

Runs the real binary on a temporary Documents folder (maniac/ plus one other
game) and checks that the game's folder is found despite stray spaces or
case ("loom " from a zip made on a Mac) and one folder further down (the
Files app unzips a zip of several folders into a folder named after it,
next to a Mac's __MACOSX, which is never taken for the game), that a game
whose setup stopped twice is skipped and logged, and that one which stopped
once is retried.
Needs privately supplied games; nothing is copied out of build/.

Usage: tools/test_world_setup.py game-data/mm-dos loom=game-data/loom-ega
"""
import argparse
import re
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = int(re.search(r'kWorldExportVersion = (\d+);',
                        (ROOT/'engine/common/scummverse_world_catalog.h').read_text()).group(1))


def launch(binary, maniac, game, data, folder_name, attempts=None, timeout=300):
    """Start the app once; returns (log, finished marker written, attempt count)."""
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
        attempt = worlds/f'{game}-v{VERSION}.try'
        if attempts is not None:
            attempt.write_bytes(b'SVT1' + bytes([attempts]))
        (docs/'scummvm.ini').write_text('[scummvm]\n')
        proc = subprocess.Popen([str(binary), '--config=scummvm.ini'], cwd=docs, stdin=subprocess.DEVNULL,
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
        return ''.join(lines), (worlds/f'{game}-v{VERSION}.svx').exists(), count


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


if __name__ == '__main__':
    main()
