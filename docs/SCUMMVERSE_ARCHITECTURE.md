# Purple Meteor architecture — current audit, 2026-10-12

Mission: preserve classic SCUMM worlds while enabling an expanding adventure
universe built by players and intelligent inhabitants. iOS first, portable core;
modular monolith first. The Purple Meteor belongs in this universe.

## Actual baseline

Pinned ScummVM 2.9.1 plus distribution patches 0001–0022 supports a local
Maniac Mansion DOS V1 sandbox importing selected Zak DOS V1 resources. Engine
hooks, room catalog, roaming and transport are coupled through ScummEngine and
included .inc files. Native iOS UI communicates through common/scummverse_ai.h.
Local model runtime and conversation state live under the iOS backend. There is
no authoritative multiplayer server, creator system, Curator or wallet.
Older architecture.md and status.md describe historical milestones; they are
not evidence that later modifications still preserve those boundaries.

## Incremental module boundaries

| Boundary | Owns / consumes / emits | Replacement and failure contract |
| --- | --- | --- |
| Presentation | Sprite bounds and viewport → placement; no world state | Portable contain-layout function v1; synthetic aspect tests; invalid input yields empty placement |
| Content adapters (next) | Edition identity, logical scene setup, source references → validated scene descriptors | Register versioned adapter; reject unknown editions before mutation; test logical-room variants, not just physical files |
| Geometry/navigation | Walkboxes, restrictions, traversal capabilities → validated paths | Use version-specific engine adapter; never globally unlock boxes; invalid movement preserves position |
| World/transport | Stable entities, room membership, manifests, seats → transition events | Eventually authoritative atomic transitions and reconnect snapshots; transport must not own rendering |
| Communication | Conversation IDs, ordered messages, acknowledgments → delivery events | Replace transport/UI independently; idempotent IDs, bounded retries, persistence; retain failed drafts |
| NPC intelligence | Personality, bounded memory, world snapshot → dialogue/action proposals | Provider-independent request/cancel/result; validate actions separately; classic dialogue fallback |
| Platform | Files, secure storage, lifecycle, input, viewport | OS adapters; shared game logic has no UIKit dependency |
| Persistence/inventory | Versioned entity/item state and transactions | Migrations, atomic updates, idempotency; preserve previous valid state on failure |
| Creation/Curator/discovery (later) | Validated content proposals, publication and claim records | Untrusted declarative content, bounded jobs; canonical worlds protected; atomic limited claims |
| Ownership (later) | Optional settlement and secure signing | No inventory dependency on a chain; testnet first, explicit transfer authorization |

Only presentation's small contract is implemented in this milestone. Other rows
are target boundaries, not APIs that already exist. Extract contracts when their
first real vertical slice requires them; avoid empty service scaffolding.

## First major architecture acceptance test

A second adapter registered through a documented game-pack interface must load
an authentic scene and its actor/navigation data without edits to rendering,
networking, inventory or navigation implementation. Current Zak integration does
NOT meet this test. Do not claim another game supported by showing backgrounds.
Packs need stable game/edition/logical-room IDs, versioned compatibility metadata,
source resource references, scene initialization, geometry, costume variants,
object states and validated transitions. Original SCUMM versions differ; preserve
version-specific behavior behind adapters. Start with Maniac and Zak, then choose
another edition only after inspecting its actual format and licensing.

## Mobile presentation contract v1

`common/scummverse_layout.h` owns portrait vertical-region allocation in host-view
points. It consumes host height and bottom occlusion, emitting disjoint game,
toolbar and chat regions. It owns no mutable state. UIKit and the iOS renderer
consume it; `kInputChatLayoutChanged` delivers integer millipoint occlusion through
the platform event queue, without rebuilding the graphics surface. The engine
retains aspect fitting and input conversion. Tests use synthetic device geometry;
UIKit/device acceptance remains necessary. This is a small portable module, not
an additional service. Landscape and engine GUI overlays retain their layouts.

## Travel persistence adapter v1

The traveller key helpers in scummverse_places.inc isolate the legacy variable
layout from gameplay calls. Original seven actor records keep their existing
indices; expanded actor records occupy six fields each in 400..501, with schema
marker 399. These are sandbox-reserved variables within the existing save size;
original direct DOS V1 script variable operands are byte-sized. Existing expanded
actors' shared legacy slot is inherently ambiguous; migration preserves it only
for the active expanded actor. No file rewriting or save-container version change.
A future persistence adapter must preserve the tested independent bookings,
return locations, migration and idempotence contracts.

## Companion presence invariant

A follow relationship records intent, not omnipresent membership. Scene transition
code may carry a companion only from the leader's recorded departure scene.
Vehicle manifests temporarily own riders; following must not reveal, relocate or
board them into another vehicle. Boarding requires departure-room presence. These
rules are exercised by tools/test_companion_presence.py with private source data;
future world/transport replacements must retain them, including across save/load.
