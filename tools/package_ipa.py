#!/usr/bin/env python3
"""Package an actual unsigned iPhoneOS .app for signing by a sideloading tool."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    app = args.app.resolve()
    info = plistlib.loads((app / "Info.plist").read_bytes())
    if info.get("CFBundleSupportedPlatforms") != ["iPhoneOS"]:
        raise SystemExit("Expected a device build, not an iOS simulator app")
    executable = app / info["CFBundleExecutable"]
    subprocess.run(["lipo", str(executable), "-verify_arch", "arm64"], check=True)
    if any(p.suffix.lower() in {".lfl", ".d64"} for p in app.rglob("*")):
        raise SystemExit("Refusing to package proprietary game resource files")
    if not os.access(executable, os.X_OK):
        raise SystemExit("App executable is missing executable permission")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    ipa = output / "SCUMMVERSE-unsigned.ipa"
    with tempfile.TemporaryDirectory(prefix="scummverse-ipa-") as temp:
        payload = Path(temp) / "Payload"
        payload.mkdir()
        subprocess.run(["ditto", str(app), str(payload / app.name)], check=True)
        subprocess.run(["ditto", "-c", "-k", "--keepParent", str(payload), str(ipa)], check=True)
    with zipfile.ZipFile(ipa) as archive:
        if archive.testzip() is not None:
            raise SystemExit("IPA ZIP integrity check failed")
        plistlib.loads(archive.read(f"Payload/{app.name}/Info.plist"))
        if f"Payload/{app.name}/{info['CFBundleExecutable']}" not in archive.namelist():
            raise SystemExit("IPA executable missing")
    metadata = {
        "project_commit": os.environ.get("GITHUB_SHA"),
        "upstream": json.loads((ROOT / "upstream.json").read_text()),
        "bundle_identifier": info["CFBundleIdentifier"],
        "minimum_ios": info.get("MinimumOSVersion"),
        "architecture": "arm64",
        "signed": False,
        "game_data_included": False,
        "sha256": hashlib.sha256(ipa.read_bytes()).hexdigest(),
    }
    (output / "build-info.json").write_text(json.dumps(metadata, indent=2) + "\n")
    shutil.copyfile(ROOT / "COPYING", output / "COPYING")
    shutil.copyfile(ROOT / "docs/ios.md", output / "INSTALL.md")
    print(f"Validated unsigned device IPA: {ipa}")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
