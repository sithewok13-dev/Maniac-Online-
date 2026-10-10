#!/usr/bin/env python3
"""Materialize the pinned ScummVM fork without overwriting local edits."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT, capture=False):
    return subprocess.run(args, cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None).stdout


def main():
    pin = json.loads((ROOT / "upstream.json").read_text())
    source = ROOT / "engine"
    if not source.exists():
        run("git", "clone", "--depth", "1", "--branch", pin["tag"],
            pin["repository"], str(source))
    revision = run("git", "rev-parse", "HEAD", cwd=source, capture=True).strip()
    if revision != pin["commit"]:
        raise SystemExit(f"Refusing to modify engine at {revision}; expected {pin['commit']}")
    patches = sorted((ROOT / "patches").glob("*.patch"))
    if not patches:
        raise SystemExit("No fork patches found")
    for patch in patches:
        applied = subprocess.run(["git", "apply", "--reverse", "--check", str(patch)],
                                 cwd=source, capture_output=True).returncode == 0
        if applied:
            print(f"Already applied: {patch.name}")
            continue
        run("git", "apply", "--check", str(patch), cwd=source)
        run("git", "apply", str(patch), cwd=source)
    print(f"SCUMMVERSE source ready: {source} ({revision} + patches)")


if __name__ == "__main__":
    main()
