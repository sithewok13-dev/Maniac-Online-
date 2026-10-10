# SCUMMVERSE / Maniac Online

A small, reproducible source fork of **real ScummVM**, starting with the original
Commodore 64 Maniac Mansion. No replacement engine or recreated graphics.

**Current scope:** baseline engine build and standalone direct-launch implementation.
This is not yet a multiplayer client. Exploration overrides, networking, and physical
iPhone validation are later milestones. No proprietary game data is included.

## Source layout

- `upstream.json`: exact upstream source revision (ScummVM 2.9.1).
- `patches/`: reviewable modifications applied to that revision.
- `tools/`: source preparation, native builds, startup tests, and launch helpers.
- `docs/`: source investigation, iOS instructions, and validation record.
- `engine/`: generated full upstream checkout plus fork patches (ignored).
- `build/`: generated binaries and Xcode projects (ignored).

This is a patch-maintained fork: `python3 tools/bootstrap.py` obtains the actual
ScummVM source and applies the changes. It verifies the commit, refuses revision
mismatches, and does not reset your local edits. Upstream history and license files
remain in `engine/`. The GitHub repository is not a GitHub-network fork.

## Desktop development

Install Python 3, Git, Make, a C++11 compiler, and SDL2 development headers.
On Debian/Ubuntu: `apt-get install build-essential python3 git libsdl2-dev`.
On macOS: install Xcode Command Line Tools and SDL2 (`brew install sdl2`).

```sh
python3 tools/build.py --backend sdl
python3 tools/run.py /absolute/path/to/your/maniac-data
```

Use your legally obtained C64 images, named **`maniac1.d64`** and
**`maniac2.d64`**, together in the data directory. Do not add them to Git.
The original game introduction and character selection remain unchanged in this
milestone; direct launch means bypassing ScummVM's game library, not skipping the
game's own scripts. No puzzle or death prevention has been implemented yet.

Launching the binary with no arguments uses `maniac/` beneath the current working
directory. `--path=/path/to/data` overrides that location. Startup always selects
Maniac Mansion/C64. Diagnostic commands such as `--version`, `--list-games`, and
`--detect` remain available. Errors and game exit cannot open the ScummVM launcher.

## Headless verification

```sh
python3 tools/build.py --backend null
python3 tools/test_startup.py build/null/scummvm
```

The null backend compiles the real interpreter but has no graphical output or
audio playback. It is a CI check, **not a headless multiplayer server**.

See [iOS setup](docs/ios.md), [engine investigation](docs/architecture.md), and
[milestones and evidence](docs/status.md) before proceeding to exploration mode.

## License

Project code and patches are GPL-3.0-or-later; see [COPYING](COPYING). ScummVM retains
its copyrights and component-specific licenses in `engine/COPYRIGHT` and
`engine/LICENSES/`. When distributing binaries, provide the corresponding pinned
source, patches, build instructions, and required notices under the applicable
licenses. Game assets remain separate and are not licensed by this project.
