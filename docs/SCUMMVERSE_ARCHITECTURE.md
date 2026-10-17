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

## Mobile presentation contract v1 (v2 since 0041: optional width and game aspect cap the game region at its aspect-fit height)

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

## Seat allocation contract and DOS V1 cabin adapter

`common/scummverse_seats.h` owns no world state. It consumes a passenger bitset and
signed reservations, preserving unique valid assignments and allocating free slots.
Over-capacity/invalid requests leave caller state unchanged. Negative reservations
retain a standing passenger's place. `tools/test_seats.cpp` tests the contract with
synthetic data; replacement allocators must preserve stable and atomic results.

The engine owns bookings, manifests and saved variables 502..525 (actor 1..24);
526 is the migration marker. No save-container change. Existing six-or-fewer flights
acquire seats on restoration. Larger legacy flights keep all riders without seating
or allowing new boarding. Landing clears reservations and elevation.

`scummverse_plane.h` is the edition adapter: six chair coordinates and reuse of the
source chair's foreground mask for identical repeated chairs. Rendering does not
allocate seats. Imported seated costumes use source size; the source Maniac anchor
is aligned by one two-pixel cell. A bounded actor pose method bypasses projection
only for assigned seated riders; walking immediately restores aisle navigation.
This is local transport integration, not a server, network protocol or game-pack
acceptance demonstration. Separate concurrent flights remain future work.

## Logical scene setup and source-art color boundary

`ZakSceneObjectState` now scopes rules by sandbox room as well as source resource
and original object identity. Room zero retains resource-wide behavior (Seattle's
opening); Mexico chamber 89 uses its own logical-130 state. Ordered masks are
applied during import before object IDs are remapped. Imported puzzle interactions
remain disabled, so restoring this room's immutable setup on load preserves the
intended sightseeing state; it does not overwrite native game progression.

GdiV1 receives both the host color table and an imported-room table from ScummVM's
existing palette definitions. Only imported room/object rasterization selects the
latter. Actor color mapping is unchanged. This separates source artwork colors
from character identity without changing the host game ID or duplicating palettes.

The next content step needs stable IDs for each logical temple room (156–167),
not twelve variants behind a shared live room ID. Current room 88 remains the old
wrong mapping until that graph and existing-save migration can be delivered together.


## Logical temple adapter and append-only room identities (0038)

`scummverse_content.h` centralizes imported/foreign room capacity predicates.
A compile-time check binds the catalog length to allocated capacity. Existing IDs
remain stable; 99–109 append variants while 88 replaces the erroneous Mars resource
with its intended Mexico logical scene. The catalog's logical-scene descriptors
own source object placement/state, box flags and camera limits. Door links carry
original destination-object IDs, resolved through the importer's source-ID mapping.
This keeps foreign script execution disabled while preserving initialized geometry.

The same source arrival resolver serves offscreen NPC travel; it consumes cached
resource metadata and the destination variant, never the displayed room's objects.
Object displacement preserves the original signed walking-anchor behavior. Applying
layout to saved objects is idempotent. Save marker 527 repairs the previous room-88
geometry and occupants; upstream's indexed resource serialization supports appended
room capacity without shifting saved records. Reverse loading a new save into the
old build is not supported or promised. Original game files are never modified.

This is an edition-specific adapter increment, not a complete game-pack registration
API or the additional-game acceptance demonstration. Future adapters must still
separate engine versions and validate their original initialization semantics.


## Shared logical scene setup (0039)

`ZakSceneSetup` generalizes the Mexico descriptor for Mars: bounded object/box
arrays with explicit counts, both camera bounds, source colors and logical identity.
Rendering and navigation consume the initialized scene through existing engine
paths; adding these variants did not require a new renderer or navigation system.
Source exit metadata supports original explicit arrival coordinates in addition to
destination object anchors, with the same data used for player and local NPC travel.

This remains an audited English DOS V1 adapter, not an untrusted pack loader or a
new-game acceptance demonstration. Its tests independently execute source entries
and compare pixels, object state/anchors, walkbox flags, saves and room graph.
The exploration preset intentionally opens original puzzle doors. Current room
count is 127; upstream V1 treats IDs >=128 as pseudo rooms. Further expansion needs
an explicit ID/mapping design before increasing that bound.

Since 0050 that design is the original's own: a logical scene keeps its original
room number (128+) and resolves to an imported physical slot through the saved
`_resourceMapper`, with its own `ZakSceneSetup` (0068: the fourteen Sphinx maze
cells 207..220 and the Mars corridor 187 all on slot 74, resource 23). Rooms
200..255 were other-world places in saves from patches 0057..0061; such saves
(layout variable 608 unset) are migrated before any Zak restore step reads the
room, and every new game sets 608 at boot.


## Conversation contract v1 (0040)

`common/scummverse_conversation.h` implements the first slice of the
Communication row: ordered lines with monotonic IDs, idempotent ticketed
completion, a bounded outbox and departure handling. Providers (local model,
classic lines, a future server) are outside it; the iOS runtime serializes
access with its mutex. UI and engine bubbles read the same transcript. Not yet:
persistence, network delivery acknowledgments or multi-conversation rooms.

## Local WiFi play (patch 0053)

`common/scummverse_net.{h,cpp}`: portable codec, non-blocking POSIX TCP
`Session` (host relays; clients talk only to the host) and a mutex-protected
request/status channel for the UI thread. Frames are length-prefixed and
strictly validated (actor 1..24, room 1..255, printable ASCII speech ≤160);
malformed input drops only that connection. `common/scummverse_net_engine.h`
is a std-free bridge so engine code never includes standard headers after
ScummVM's forbidden-symbol macros. `engines/scumm/scummverse_net.inc` maps
peers to cast members and validates rooms against this build
(`kScummverseNetContent` = room count and patch level). AI proposes;
deterministic systems validate: remote input never reaches the conversation
model and never controls the local player's character.

## Other worlds (patches 0057..0069)

Scenes and characters from other SCUMM games are never shipped: the player's
own copy is run once in export mode, and its own engine renders a private
cache (scenes `.svw`, characters `.svc`, finished marker
`<game>-v<kWorldExportVersion>.svx`). Portable code (`common/scummverse_world.*`,
std-free bridge `scummverse_world_engine.h`) fits them to the V1 sandbox on one
physical room, with palette slots 16..191 for the scene and 192..255 shared by
its characters. Characters use transient guest actors (Maniac 25..29, never
saved; Maniac objects start at 30), so the sandbox's walking, speech and chat
rules apply; only drawing is replaced.

A place is (catalog game, that game's room). Eight logical rooms 192..199
hold the places in use; saved variables 600..607 name each slot's place and
608 marks the layout (older saves' rooms 200..255 migrate through the frozen
`kWorldLegacyPlaces`). Places are reached three ways: the scene menu's named
landmarks (`scummverse_world_catalog.h`, newly authored names and lines), a
landmark's neighbours by walking off a side, and doors. A door is a room
object the player taps; when the player arrives at it, `scummverseWorldDoors`
follows the game's own link to the target room (map rooms travel at once).

Two committed tables are generated from private analysis of the player's
games (the generators read `build/foreign/`, which is never committed):
`scummverse_world_maps.inc` (tools/world_maps.py: every exportable room and
its door, exit, walk, map, vehicle and time-travel links, pseudo rooms folded
into their physical room except v3/v4 instances 128+, which keep their own
number and name their template's resource) and `scummverse_world_cast.inc` (tools/world_cast.py:
each character's costume, room, name, newly written personality and lines;
at most five per room). Besides that new text they hold only numbers and names.
Scale: everyone in another world is as tall as that game's lead character
(`WorldGame::heroHeight`) fitted like the scene, times the game's own scale for
the walk box there (exported per box, "SVW3"). V1 characters are rendered by
their own renderer into a canvas and scaled around their feet; guests' frames
are scaled the same way (`scummverseDrawWorldActor`). Room kinds: scene,
map (small figures, 0.3 of that height; hotspots travel at once) and floor
plan (small figures that walk to the doors; the exporter reveals every
section) (`scummverseWorldDepth`, `kWorldFloorPlan`). Doors of v3 template
instances are resolved at generation time from each template's door
variables and the values its entry script sets (tools/world_maps.py).
Script-built rooms: a v3/v4 pseudo room is exported by mapping it to its
template (the boot script, which normally does this, is skipped) and running
the room's entry script for a few cycles; one-color v3/v4 renders are retried
that way. Scenes are "SVW4" (object states after those scripts); a door link
marked `switched` is offered only where that object is shown. The exporter
counts started exports in `<game>-v<N>.try` and writes `.svx` when one
finishes; after `kWorldExportAttempts` (2) unfinished ones the game is
skipped at start rather than crashing every launch.
Playing someone from another game (0069): a sandbox character (1..24) has an
optional saved appearance (a cast member's key). The engine mounts, whenever
the set changes, the frames everyone in the viewed room needs (the scene's
guests at the scene's scale, appearances at a person's height there) into
the shared character slots 192..255, draws them through the same actor hook,
and overrides only the name lookup; inventory, verbs, travel and saves stay
the sandbox character's.
v7/v8 editions are compiled in solely so the player's copies can be exported.
