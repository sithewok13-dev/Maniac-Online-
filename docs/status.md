# Milestone status and verification

Initial work targets the **original DOS V1** edition, as selected by the
project owner. The baseline now works on iPhone; the first exploration preview
adds seven passage-lock overrides and audited capture/death protection. Multiplayer is not implemented.

## Milestone 0 — baseline: device-confirmed

- Actual official ScummVM v2.9.1 source downloaded and inspected.
- Exact upstream commit: `9d9b9e93108a276c551aeffa390169ccc5148e15`.
- Pristine Linux x86_64 build with GCC 14 and the null backend succeeded.
- Pristine executable `--version` and `--list-engines` succeeded, reporting SCUMM
  v0–v6 support. V1 contains the original DOS Maniac Mansion implementation.
- Repeatable source preparation, desktop build tools and iOS project generation
  are included. No game assets are tracked.
- Apple arm64 iPhoneOS build passed in GitHub Actions; the owner installed the
  unsigned IPA via sideloading and confirmed baseline gameplay works.

## Milestone 1 — direct launch: device-confirmed

The source patch selects Maniac Mansion/original DOS V1 using the existing startup machinery.
No normal launch, engine-identification failure or return path opens the standard
ScummVM launcher. Errors retain a nonzero return code. Diagnostic CLI commands
are retained. The game itself still runs its original scripts and introduction.

iOS uses Documents/maniac, landscape metadata, and the existing direct-touch and
filtering controls. Xcode signing and bundle identifiers remain developer choices.
The upstream iOS quit method does not terminate the app; relaunch is required
after an error. There is no asset import/retry UI in this milestone.

## Milestone 2 — first exploration preview

Seven audited passage locks are bypassed by the second source patch; the owner
confirmed this door preview works on iPhone. The third patch protects audited
capture/death paths, with real-script tests both enabled and disabled. See
[exploration.md](exploration.md) for scope and verification. Protection still
needs iPhone validation; remaining progression barriers are active.

## Milestones 3–6 — not implemented

- Authoritative server, independent players and authentic remote avatar rendering.
- Independent room membership, movement synchronization and shared NPC state.
- Two-iPhone tests, interruption/reconnection behavior.
- Private internet hosting.

These require further engine work and exploration validation.
The null backend is not a network server and no multiplayer success is claimed.

## Validation limits

Local checks use Linux and the null backend with the owner's privately supplied
DOS resources. Apple builds run on hosted macOS GitHub Actions. Device validation
is reported by the owner, not performed remotely by the assistant. Headless tests
do not prove visual behavior, audio playback or networking. Historical results
below describe the state at the time of each earlier milestone.

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

## Capture/death protection — 2026-10-11

The real DOS script probe checks Edna and Ed's hostile target decisions, Ed's
guarded pickup, both lethal contract variants, Purple Tentacle's complete search,
the fatal tape interaction, and Edna's completed hallway-to-bedroom patrol.
With protection disabled the original capture, death and disabled-input outcomes
are observed; with protection enabled the player keeps their room/costume/controls.
The guarded destructive entries are checked for absence of side effects, including
all six death-reason values. Door and startup regression checks also pass.

No new iPhone gameplay success is claimed until the owner tests this build. The
probe advances script delays and dialogue waits to test VM outcomes; it does not
measure real-time pacing, rendering, sound or touch input. Original data remains
local and is not included in source or binary artifacts.

Source preparation now recognizes a dependent patch stack by reversing it in a
disposable copy, rather than trying to reverse each old patch against the final
tree. Tests cover pristine source, every applied prefix, a complete stack,
unrelated local edits and conflicting edits; the real checkout is never reversed.

## Kitchen disappearance and hallway gate — 2026-10-11

The owner's iPhone test found two gaps in the protection preview. The fourth
patch keeps Edna's kitchen scene waiting while the player remains there and
suppresses Green Tentacle's gate/pushback/Bernard retreat. Both Dave and Bernard
now reach Weird Ed through the original hallway/stairs/door scripts in headless
tests, with Green Tentacle still present. Edna's original departure resumes after
leaving the kitchen. Physical-device confirmation of this correction is pending.
