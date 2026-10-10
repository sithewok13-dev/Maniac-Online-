#!/usr/bin/env python3
"""Launch the SDL build using user-owned data, without configuring a game library."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path, help="Directory containing original game files")
    args = parser.parse_args()
    data = args.data.expanduser().resolve()
    if not data.is_dir():
        parser.error(f"Game data directory does not exist: {data}")
    binary = ROOT / "build/sdl/scummvm"
    if not binary.is_file():
        parser.error("Build first: python3 tools/build.py --backend sdl")
    raise SystemExit(subprocess.run([str(binary), f"--path={data}", "scumm:maniac"],
                                    cwd=ROOT).returncode)


if __name__ == "__main__":
    main()
