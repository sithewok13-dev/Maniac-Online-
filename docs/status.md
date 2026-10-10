# Milestone status and verification

Initial work targets the **original DOS V1** edition, as selected by the
project owner. Work deliberately stops before exploration and multiplayer code.

## Milestone 0 — baseline: partial

- Actual official ScummVM v2.9.1 source downloaded and inspected.
- Exact upstream commit: `9d9b9e93108a276c551aeffa390169ccc5148e15`.
- Pristine Linux x86_64 build with GCC 14 and the null backend succeeded.
- Pristine executable `--version` and `--list-engines` succeeded, reporting SCUMM
  v0–v6 support. V1 contains the original DOS Maniac Mansion implementation.
- Repeatable source preparation, desktop build tools and iOS project generation
  are included. No game assets are tracked.
- Still required: run the original DOS V1 game, verify audio/graphics and compile /
  deploy the iOS target with Apple's toolchain.

## Milestone 1 — direct launch: implemented, gameplay validation pending

The source patch selects Maniac Mansion/original DOS V1 using the existing startup machinery.
No normal launch, engine-identification failure or return path opens the standard
ScummVM launcher. Errors retain a nonzero return code. Diagnostic CLI commands
are retained. The game itself still runs its original scripts and introduction.

iOS uses Documents/maniac, landscape metadata, and the existing direct-touch and
filtering controls. Xcode signing and bundle identifiers remain developer choices.
The upstream iOS quit method does not terminate the app; relaunch is required
after an error. There is no asset import/retry UI in this milestone.

## Milestones 2–6 — not implemented

- Free exploration and edition-specific progression overrides.
- Authoritative server, independent players and authentic remote avatar rendering.
- Independent room membership, movement synchronization and shared NPC state.
- Two-iPhone tests, interruption/reconnection behavior.
- Private internet hosting.

These require the original DOS V1 data and the preceding milestone validations.
The null backend is not a network server and no multiplayer success is claimed.

## Validation limits

This workspace is Linux without Xcode, iPhone hardware, SDL2 development headers
or proprietary DOS resource files. Headless compilation and startup checks cannot prove
gameplay, screen scaling, sound, iOS execution, or networking. The GitHub workflow
also includes an SDL build for an environment with SDL2 installed; adding that
workflow is not evidence that its remote run has passed.

See the validation results recorded below and the device checklist in [ios.md](ios.md).

## Baseline results — 2026-10-10 (before DOS switch)

| Check | Result |
| --- | --- |
| Pristine upstream configure / full null-backend SCUMM build | Passed |
| Patched configure / full null-backend SCUMM build | Passed |
| Rebuild after consolidating missing-data error handling | Passed |
| Executable startup tests | 8 passed: version, game listing, missing data, empty directory, path with spaces, unrelated game, saved launcher preference, unrelated saved target |
| Native upstream Xcode project generator compiled on Linux | Passed |
| Xcode project generation and iOS source references | Passed; not an iOS build |
| Both iOS plists parse and declare landscape / SCUMMVERSE | Passed |
| Bootstrap repeated on already-patched source | Passed, no duplicate application |
| Python syntax and patch whitespace checks | Passed |

The full build emitted existing upstream warnings in `scumm/sound.cpp` and
`graphics/managed_surface.cpp`; neither prevented compilation. No authentic game
frames, audio, room transitions, successful game exit, or connected clients have
been tested. Startup tests use only empty directories and configuration files.

## DOS V1 switch — 2026-10-10

- Rebuilt the actual SCUMM engine and startup code successfully with DOS selected.
- Edition validation runs before upstream platform overrides and requires one
  unambiguous, full original DOS V1 match. Enhanced V2, other platforms, demos and
  ambiguous fallback candidates are rejected rather than reinterpreted as V1.
- All **11 executable startup tests passed**, including synthetic V2, NES and V1
  demo detector signatures. These minimal synthetic headers contain no game
  artwork or scripts and do not establish successful authentic game execution.
- The consolidated DOS patch applied to clean pinned source and exactly reproduced
  all four changed source files. Bootstrap idempotence, Python syntax and patch
  whitespace checks passed.
- Updated desktop/iOS data instructions to require all original DOS `.LFL` files,
  including `00.LFL`; documented migration for existing C64 engine checkouts.
- Original DOS gameplay, graphics/audio and physical iOS validation remain pending.
  Earlier Xcode-generation checks still concern project structure only.
