#!/usr/bin/env python3
"""Generate ScummVM's native Xcode project; does not claim to compile/sign iOS."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.run([sys.executable, str(ROOT / "tools/bootstrap.py")], check=True)
    output = ROOT / "build/ios"
    output.mkdir(parents=True, exist_ok=True)
    tool = ROOT / "build/tools/create_project"
    tool.parent.mkdir(parents=True, exist_ok=True)
    source = ROOT / "engine/devtools/create_project"
    files = ["cmake.cpp", "create_project.cpp", "codeblocks.cpp", "msvc.cpp",
             "msbuild.cpp", "xcode.cpp"]
    subprocess.run([os.environ.get("CXX", "c++"), "-std=c++11", "-O2", "-DPOSIX",
                    *[str(source / name) for name in files], "-o", str(tool)], check=True)
    subprocess.run([str(tool), str(ROOT / "engine"), "--xcode", "--use-xcframework",
                    "--output-dir", str(output),
                    "--disable-all-engines", "--enable-engine=scumm,scumm_7_8,scummverse",
                    "--disable-nasm", "--disable-taskbar", "--disable-tts"],
                   cwd=output, check=True)
    project = (output / "scummvm.xcodeproj/project.pbxproj").read_text()
    if 'path = "/frameworks/' in project:
        raise SystemExit("Generator produced invalid root-relative framework paths")
    print(f"Generated {output / 'scummvm.xcodeproj'}")
    print("Next: place upstream iOS frameworks in build/ios/frameworks and follow docs/ios.md")


if __name__ == "__main__":
    main()
