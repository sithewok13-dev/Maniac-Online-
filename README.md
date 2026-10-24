# SCUMMVERSE / Maniac Online

A small, reproducible source fork of **real ScummVM**, starting with the original
DOS V1 Maniac Mansion. No replacement engine or recreated graphics.

**Current scope:** standalone DOS V1 iPhone exploration sandbox. Characters roam
between rooms, open doors, and speak randomized offline encounter lines. Story
cutscenes are disabled; the original character picker remains. Start a new game
when upgrading. See [roaming behavior and validation](docs/roaming.md).
An optional on-device dialogue preview adds separately downloaded Small/Larger
models through the iPhone **AI** button; Classic remains the default. See
[local dialogue setup and limits](docs/local-ai.md). Movement remains engine-driven.
The outer mansion grounds now connect to Zak's original DOS V1 airport. Travel
is free; you choose a destination while NPCs choose randomly. Zak and the mansion
cast can visit the mansion, San Francisco, Seattle and Miami airport, with shared
plane cabins and a timed free bus. See
[connected worlds](docs/worlds.md) for setup and current destinations.
Multiplayer remains unimplemented. No proprietary game data or model weights are included.

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

Copy **all `.LFL` files** from your legally obtained original DOS V1 release,
including **`00.LFL`**, into one data directory. Keep filenames intact and include
files from every disk. Do not add them to Git. The enhanced DOS V2 release, C64
release, NES release and demos are not supported by this first world. The engine
checks detected version/platform/demo status before applying platform overrides;
setting DOS alone does not establish that the files are V1.
The character picker remains, followed by immediate exploration with the intro
and story cutscenes disabled. [Roaming sandbox](docs/roaming.md) describes the new
default; [earlier exploration changes](docs/exploration.md) records the prior
seven-door and capture-protection milestones.

Launching the binary with no arguments uses `maniac/` beneath the current working
directory. `--path=/path/to/data` overrides that location. Startup always selects
Maniac Mansion/original DOS V1. Diagnostic commands such as `--version`, `--list-games`, and
`--detect` remain available. Errors and game exit cannot open the ScummVM launcher.
Two modes, kept apart: Explore mode (the mansion, other worlds, the new
engine) and Story mode (the original games, each from its folder in
Documents in its own engine as ScummVM runs it, Maniac Mansion's own story
among them). The Worlds menu switches between them; Story mode's list starts
or continues each game, and leaving a game saves its place (slot 99,
"Story"). The app reopens in the mode, and the game, it was left in.

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

## Updating an existing C64 checkout

Before pulling this change, reverse the old patch without discarding local edits:

```sh
git -C engine apply --reverse ../patches/0001-standalone-maniac-c64.patch
git pull --ff-only
python3 tools/bootstrap.py
```

If you already pulled, recover the old patch with
`git show 0085605d508df8a256d2f861ecf4b9da5a3f0c3d:patches/0001-standalone-maniac-c64.patch > /tmp/scummverse-c64.patch`,
then use `git -C engine apply --reverse /tmp/scummverse-c64.patch` before bootstrap.
If reverse application reports conflicts, preserve and reconcile your local engine
edits first; do not reset the checkout. Replace C64 disk images with the original
DOS `.LFL` files. A fresh checkout needs only the normal build command.

The **Talk preview** uses in-scene character selection and a small message bar.
Qwen3 4B is an optional 2,497 MB download for high-memory phones; Small/Larger
remain available. See [local dialogue](docs/local-ai.md) for limits and instructions.

**Group Talk:** tap **Talk**, then a character. Use **+** and tap another character
to share the conversation. Send collapses the bar; tap the recipient to write again.
See [scene chat, destinations, flights and bus](docs/flights-and-scene-chat.md).

**Expanded Zak cast:** Annie, Melissa and Leslie start at Zak's apartment and join
roaming, group conversations and companion travel. Their original sprites come
from your installed Zak files; existing saves migrate automatically.

The latest sandbox expansion adds a playable face gallery, portrait game/chat layout, on-request sleeping-driver bus, and more original Zak locations. See [controls and scope](docs/expanded-worlds.md).
