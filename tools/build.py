#!/usr/bin/env python3
"""Build actual ScummVM with SCUMM v0-v8 (v7/v8 only for other-world exports) and the sandbox engine; null is CI-only, SDL is playable."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("sdl", "null"), default="sdl")
    parser.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1))
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    subprocess.run([sys.executable, str(ROOT / "tools/bootstrap.py")], check=True)
    output = ROOT / "build" / args.backend
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(ROOT / "engine/configure"), f"--backend={args.backend}",
                    "--disable-all-engines", "--enable-engine=scumm,scumm_7_8,scummverse",
                    "--disable-detection-full", "--disable-cloud", "--disable-debug"],
                   cwd=output, check=True)
    subprocess.run(["make", f"-j{args.jobs}"], cwd=output, check=True)
    print(f"Built: {output / 'scummvm'}")


if __name__ == "__main__":
    main()
