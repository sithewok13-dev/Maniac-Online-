#!/usr/bin/env python3
"""Export other-world scenes and characters from privately supplied games, like the iOS app.

Builds a temporary Documents folder with maniac/ and one folder per game
(named as in common/scummverse_world_catalog.h), runs the real binary, which
exports each new game once before starting Maniac, and copies the resulting
worlds/ cache to build/worlds. Game data and the cache stay in ignored folders.

Usage: tools/export_worlds.py game-data/mm-dos monkey2=game-data/monkey2-vga ...
"""
import argparse
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('maniac', type=Path)
    p.add_argument('games', nargs='+', help='folder=path pairs, e.g. monkey2=game-data/monkey2-vga')
    p.add_argument('--binary', type=Path, default=ROOT/'build/null/scummvm')
    p.add_argument('--out', type=Path, default=ROOT/'build/worlds')
    p.add_argument('--timeout', type=int, default=3600, help='seconds before giving up')
    a = p.parse_args()
    with tempfile.TemporaryDirectory(prefix='scummverse-documents-', dir=ROOT/'build') as tmp:
        docs = Path(tmp)
        (docs/'maniac').symlink_to(a.maniac.resolve())
        for pair in a.games:
            folder, path = pair.split('=', 1)
            (docs/folder).symlink_to(Path(path).resolve())
        (docs/'scummvm.ini').write_text('[scummvm]\n')
        # No console: an engine error ends the run instead of waiting for input.
        proc = subprocess.Popen([str(a.binary.resolve()), '--config=scummvm.ini'], cwd=docs,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        # Exports finish, then Maniac starts and runs until stopped.
        lines = []
        started = time.time()
        deadline = started + a.timeout
        for line in proc.stdout:
            lines.append(line)
            if "target 'maniac'" in line or time.time() > deadline:
                break
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log = ''.join(lines)
        (ROOT/'build/export-worlds.log').write_text(log)
        cache = docs/'worlds'
        exported = sorted(f.name for f in cache.glob('*.svw')) if cache.exists() else []
        guests = sorted(f.name for f in cache.glob('*.svc')) if cache.exists() else []
        markers = sorted(f.name for f in cache.glob('*.svx')) if cache.exists() else []
        panels = sorted(f.name for f in cache.glob('*.svi')) if cache.exists() else []
        things = sorted(f.name for f in cache.glob('*.svo')) if cache.exists() else []
        fights = sorted(f.name for f in cache.glob('*.svd')) if cache.exists() else []  # (from 0298: kWorldDuels)
        a.out.mkdir(parents=True, exist_ok=True)
        for name in exported + guests + markers + panels + things + fights:
            shutil.copy2(docs/'worlds'/name, a.out/name)
        for line in log.splitlines():
            if 'SCUMMVERSE_WORLD_EXPORT ' in line or 'SCUMMVERSE_WORLD_GUEST' in line or 'SCUMMVERSE_WORLD_PRESET' in line or 'SCUMMVERSE_WORLD_PANEL' in line or 'SCUMMVERSE_WORLD_THINGS' in line or 'SCUMMVERSE_WORLD_DUEL' in line or 'world export' in line:
                print(line.strip())
        print(f'{len(exported)} scenes, {len(guests)} characters, {len(panels)} verb panels exported to {a.out} in {time.time() - started:.0f}s')
        # (From 0250: a timed event's first wait (kWorldTimed) not as the
        # script that waits it counts, or not checked, told by the export.)
        timed = [line.strip() for line in log.splitlines() if line.startswith('WARNING') and 'world things' in line and 'timed event' in line]
        if timed:
            print('\n'.join(timed) + '\nFAIL: a timed event not as its script waits it (common/scummverse_world_catalog.h, kWorldTimed)')
            return 1
        # (From 0298: a fight's numbers (kWorldDuels) not as its scripts have
        # them, told by the export.)
        duels = [line.strip() for line in log.splitlines() if line.startswith('WARNING') and 'world duel' in line and 'not as its script' in line]
        if duels:
            print('\n'.join(duels) + '\nFAIL: insult sword fighting not as its scripts have it (common/scummverse_world_catalog.h, kWorldDuels)')
            return 1
        return 0 if exported else 1


if __name__ == '__main__':
    raise SystemExit(main())
