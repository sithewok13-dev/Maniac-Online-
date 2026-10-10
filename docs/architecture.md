# Engine investigation and boundaries

Inspected revision: `9d9b9e93108a276c551aeffa390169ccc5148e15` (v2.9.1).
Paths below are relative to the materialized `engine/` checkout. These are actual
upstream symbols, not proposed APIs. Initial content target: **original DOS V1**.

| Responsibility | Existing implementation | Consequence |
| --- | --- | --- |
| Game identity | `engines/scumm/detection_tables.h`: `maniac`, `GID_MANIAC`, DOS, version 1 | Validate the detected full V1 edition before any platform override; reject V2 and demos. |
| DOS resource access | `engines/scumm/resource.cpp`, `resource_v2.cpp`, `file.cpp`: `ScummFile` | Load original numbered `.LFL` resources; keep upstream decoding and artwork. |
| Startup | `base/main.cpp`: `scummvm_main`, `identifyGame`, `runGame`; `base/commandLine.cpp`: `processSettings` | Use normal `scumm:maniac` temporary target and DOS platform setting. |
| iOS entry | `backends/platform/ios7/ios7_osys_main.cpp`: `iOS7_main` | Already changes directory to Documents before `scummvm_main`; defaults can be shared. |
| Actors | `engines/scumm/actor.h`, `actor.cpp`: `Actor_v2`, `startWalkActor`, `walkActors` | Actor IDs belong to original scripts; do not assign network player IDs to them. |
| Drawing | `actor.cpp`: `ScummEngine::processActors`, `costume.cpp`, `gfx.cpp` | Only actors in `_currentRoom` are drawn and depth-sorted; remote avatars need compatible masking, costume and sorting behavior. |
| Room changes | `room.cpp`: `ScummEngine::startScene` | Runs exit/entry scripts and unloads room resources. A peer changing rooms must not call this for the local player. |
| Walkability | `boxes.cpp`, `Actor::adjustXYToBeInBox`, versioned movement code | Walkbox/path validation must be adapted to V1 and measured with actual DOS data. |
| Input/scripts | `input.cpp`, `verbs.cpp`, `script_v2.cpp`, `script.cpp` | Single-player ego and script scheduling cannot be treated as an authoritative shared simulation. |

## Implemented boundary

Startup, a narrow edition check at engine creation, and iOS application metadata change. The first exploration patch
also clears seven audited passage locks immediately before their original OPEN handlers.
Rendering, audio, actors and resource loaders remain upstream code. The startup patch
selects Maniac Mansion/original DOS V1 when launched normally, validates the selected game,
sets direct touch and landscape defaults, and terminates the game loop on exit or
failure. The launcher entry is replaced by a diagnostic guard. Diagnostics still
use the normal upstream CLI. Missing/incorrect data is never replaced with a mock.

V1 uses `ScummEngine_v2` and `Actor_v2` in this upstream revision: the class names
cover both V1 and V2; they do not imply the enhanced V2 edition was selected.
The edition check requires unambiguous detection of a single full Maniac Mansion
candidate with version 1 and DOS platform before the upstream platform override. It never
forces V2 resources through the V1 interpreter. This improves reuse potential
for later DOS worlds but does not eliminate per-game adapters or script analysis.

## Exploration investigation

The supplied English DOS V1 index has MD5 `7f45ddd6dbfbf8f80c0c0efea4c295bc`.
Its 176 indexed global scripts and room object/entry/exit handlers were inspected
locally with upstream `descumm -1u`; game scripts and resources are not published.
The first adapter is documented in [exploration.md](exploration.md). Capture and
death overrides remain pending: caller cleanup must be verified before suppression.

1. Detect the supplied DOS resource revision and record hashes locally, not the assets.
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
actor slots can safely be reused. The V1 `Actor_v2` behavior must be tested, not
inferred from later SCUMM versions. Account for foreground masks and depth order.

Do not serialize VM memory or synchronize unrelated single-player scripts.
Server movement validation needs a trustworthy, edition-specific room/walkbox
model; raw client coordinates are not authority. Plan sequence numbers, bounded
messages, reconnect identity, and room-scoped snapshots for the network milestone.
Implement only after the original game and exploration adapter are verified.

No protocol, placeholder server, AI service, additional world, or fake second
player is included in this milestone.
