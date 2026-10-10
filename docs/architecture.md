# Engine investigation and boundaries

Inspected revision: `9d9b9e93108a276c551aeffa390169ccc5148e15` (v2.9.1).
Paths below are relative to the materialized `engine/` checkout. These are actual
upstream symbols, not proposed APIs. Initial content target: **C64 original**.

| Responsibility | Existing implementation | Consequence |
| --- | --- | --- |
| Game identity | `engines/scumm/detection_tables.h`: `maniac`, `GID_MANIAC`, C64, version 0 | Preserve disk detection; DOS V1 is not the chosen initial adapter. |
| C64 resource access | `engines/scumm/file.cpp`: `ScummDiskImage` | Keep original disk decoding and resources; do not extract/recreate artwork. |
| Startup | `base/main.cpp`: `scummvm_main`, `identifyGame`, `runGame`; `base/commandLine.cpp`: `processSettings` | Use normal `scumm:maniac` temporary target and C64 platform setting. |
| iOS entry | `backends/platform/ios7/ios7_osys_main.cpp`: `iOS7_main` | Already changes directory to Documents before `scummvm_main`; defaults can be shared. |
| Actors | `engines/scumm/actor.h`, `actor.cpp`: `Actor_v0`, `Actor_v2`, `startWalkActor`, `walkActors` | Actor IDs belong to original scripts; do not assign network player IDs to them. |
| Drawing | `actor.cpp`: `ScummEngine::processActors`, `costume.cpp`, `gfx.cpp` | Only actors in `_currentRoom` are drawn and depth-sorted; remote avatars need compatible masking, costume and sorting behavior. |
| Room changes | `room.cpp`: `ScummEngine::startScene` | Runs exit/entry scripts and unloads room resources. A peer changing rooms must not call this for the local player. |
| Walkability | `boxes.cpp`, `Actor::adjustXYToBeInBox`, versioned movement code | Walkbox/path validation must be adapted to V0 and measured with actual C64 data. |
| Input/scripts | `input.cpp`, `verbs.cpp`, `script_v0.cpp`, `script.cpp` | Single-player ego and script scheduling cannot be treated as an authoritative shared simulation. |

## Implemented boundary

Only startup and iOS application metadata change. The interpreter, rendering,
audio, scripts, actors, and resource loaders remain upstream code. The patch
selects Maniac Mansion/C64 when launched normally, validates the selected game,
sets direct touch and landscape defaults, and terminates the game loop on exit or
failure. The launcher entry is replaced by a diagnostic guard. Diagnostics still
use the normal upstream CLI. Missing/incorrect data is never replaced with a mock.

## Next investigation: exploration (not implemented)

1. Detect the supplied disk-image revision and record hashes locally, not the assets.
2. Run with `--debugflags=SCRIPTS,ACTORS,RESOURCE` on desktop; trace startup,
   character selection, room exits, door prerequisites, capture/death and cutscenes.
3. Record room relationships and walkboxes from that edition. Identify exact
   progression dependencies before adding edition-specific overrides.
4. Add an explicit exploration adapter with narrow hooks; retain harmless ambient
   and NPC scripts. Do not globally disable all scripts or invent room/script IDs.
5. Verify original visuals, depth ordering, exits and no-loss behavior with the data.

## Multiplayer direction (design only)

Use a headless server that owns membership, session-scoped player IDs, room IDs,
validated movement, and eventually NPC state. Each client retains one ScummVM
current room and its own local input/camera. A peer entering another room updates
the peer's network record and visibility, not the local engine's room.

Keep transport/session management independent from the world adapter. Player IDs
and NPC IDs must be distinct from SCUMM actor slots. Prototype authentic costume
rendering through a separate avatar layer before deciding whether any reserved
actor slots can safely be reused. The V0 `Actor_v0` behavior must be tested, not
inferred from later SCUMM versions. Account for foreground masks and depth order.

Do not serialize VM memory or synchronize unrelated single-player scripts.
Server movement validation needs a trustworthy, edition-specific room/walkbox
model; raw client coordinates are not authority. Plan sequence numbers, bounded
messages, reconnect identity, and room-scoped snapshots for the network milestone.
Implement only after the original game and exploration adapter are verified.

No protocol, placeholder server, AI service, additional world, or fake second
player is included in this milestone.
