#!/usr/bin/env python3
"""Materialize the pinned ScummVM fork without overwriting local edits."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT, capture=False):
    return subprocess.run(args, cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None).stdout


def applied_prefix(source, patches):
    """Recognize dependent patches by reversing them in a disposable copy.

    Checking each patch against the final tree fails when a later patch changes
    its context. Never reverse patches in the user's working checkout.
    """
    paths = set()
    for patch in patches:
        for line in run("git", "apply", "--numstat", str(patch),
                        cwd=source, capture=True).splitlines():
            path = Path(line.split("\t", 2)[2])
            if path.is_absolute() or ".." in path.parts:
                raise SystemExit(f"Unsafe patch path: {path}")
            paths.add(path)
    for count in range(len(patches), 0, -1):
        with tempfile.TemporaryDirectory(prefix="scummverse-patch-check-") as tmp:
            shadow = Path(tmp)
            for path in paths:
                if (source / path).exists():
                    (shadow / path).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source / path, shadow / path)
            for patch in reversed(patches[:count]):
                result = subprocess.run(["git", "apply", "--reverse", str(patch)],
                                        cwd=shadow, capture_output=True)
                if result.returncode:
                    break
            else:
                return count
    return 0


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
    count = applied_prefix(source, patches)
    for patch in patches[:count]:
        print(f"Already applied: {patch.name}")
    for patch in patches[count:]:
        run("git", "apply", "--check", str(patch), cwd=source)
        run("git", "apply", str(patch), cwd=source)
    print(f"SCUMMVERSE source ready: {source} ({revision} + patches)")


if __name__ == "__main__":
    main()
