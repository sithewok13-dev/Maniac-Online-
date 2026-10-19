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
Everyone rides seated (0095): only the player (or another device's) stands
up, by walking (scummverseKeepsSeat refuses other walks for a seated rider);
anyone else in the cabin without a chair, or left standing, walks to theirs
or a free one and sits (scummverseTakeSeat, from the roaming update). Seated,
Maniac's own looks sit in the chair (no wheels, skates or floating), and
characters drawn from other games' frames sit as Maniac's own do: clipped
at the seat front's line and the chair's mask, centred in it, the small
ones on its cushion, the big ones crammed in (`kWorldSeatFits`, seated
poses where they have one).
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

Physical IDs are scarce (56..126), so a scene sharing another's resource is a
logical scene, not a slot: 0073 folded the Mexico temple passages 157..167
(slots 99..109 since 0038) onto room 88's resource and reused slots 99..102
for San Francisco (14th Avenue, Lou's Loans, the Society office, Zak's living
room). Retired IDs (103..109) are refused for travel; scene schema 5 (var 528)
moves anyone saved there to room+58, and new games start at schema 5.


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
are scaled the same way (`scummverseDrawWorldActor`). Curse of Monkey Island
rooms that set their box scales only in the entry script are exported after
a dry run of it (state restored, pixels unchanged). Aspect: Maniac's screen
is shown 1.2 times taller than drawn, like the 320x200 games; Curse (square
pixels) is widened 1.2 when fitted (`worldWiden`), scenes and characters
alike. Maniac's own characters can be played too (`kWorldManiacLooks`:
the costume itself, in its actor's V1 colors). Room kinds: scene,
map (small figures, 0.3 of that height; hotspots travel at once) and floor
plan (small figures that walk to the doors; the exporter reveals every
section) (`scummverseWorldDepth`, `kWorldFloorPlan`). Doors of v3 template
instances are resolved at generation time from each template's door
variables and the values its entry script sets (tools/world_maps.py).
Script-built rooms: a v3/v4 pseudo room is exported by mapping it to its
template (the boot script, which normally does this, is skipped) and running
the room's entry script for a few cycles; one-color v3..v6 renders are retried
that way, and a room still one color is no place (export version 13: not
exported; an older export's scene of it is emptied, and the tour skips empty
scenes). Loom objects that draw as solid black frames (an animation's later
steps) show the room without objects instead; Day of the Tentacle's room 11
is cut to its 144 picture rows. Arrival spot (`fitScene`): the middle of the
lowest walk box at least a quarter the size of the biggest. Scenes are "SVW4" (object states after those scripts); a door link
marked `switched` is offered only where that object is shown. Exploration
presets (0074, catalog: classes switched off, variables, room scripts and
their tints) put a game in an explored state before its rooms are drawn;
named room scripts run with their actors kept for the capture, accumulated
over one animation cycle (The Dig's light bridges and their walk boxes).
The van (0077, scummverse_van.inc): a parked sprite taken from Zak's own
landing-site art is drawn into redrawn background strips of any room (V1 or
other-world scene) at its saved spot; flight is a logical scene on the
cockpit's resource; landing sites are a catalog list. Long shots (0079):
rooms where the original draws people small list their ratio
(`zakDistantCostumeRooms`); V1 characters there are drawn at it, and the
van is scaled against the long shot's people; so are characters drawn from
other games' frames (0098). Overlay frames
(`scummverseOverlayFrame`) add a costume frame over chosen ones (the King's
quiff). A costume variant may name the room whose palette it is exported
in (Curse's green Murray), or keep its own costume with other animations
(the Dig's nest monster crawls; a stand it names is the only one tried).
Walks the game never drew both ways are made by the exporter from the
game's own frames (0098), each a catalog list: `kWorldSideWalks` (a walk
kept under one facing serves every direction, mirrored for the other;
a remote one-facing picture is stood on its feet, then turned both ways),
`kWorldCostumeGrafts` (a guest the game only drew sitting: their own head
limbs on a relative's stance and walk, the relative's clothes repainted
by palette index and its head cut off below where the clothes start;
Doug the Mole Man in his uncle Shuv-Oohl's) and `kWorldLegSwings` (a
standing four-legged guest: each leg traced up from its foot, the brighter
near pair swung against the far pair from the hip; the camel). Guests
drawn only from the front get side views (`kWorldSideViews`: a relative's
stance and walk, repainted, its head found by its face colour and replaced
by a newly drawn one, repeated behind it; the three-headed monkey). Some
get a seated frame (GuestKind `kGuestSeated`, `kWorldSeatPoses`: parts of
the stance facing right, each turned about a pivot and set from the
origin or on another part, those marked front in a second picture drawn
over the seat's front; the camel sitting back with a leg over the armrest,
the dragon's tail up the seat's back, the nest monster sprawled, the
three-headed monkey filled solid). In a plane seat the big ones
(`kWorldSeatFits`) are crammed between the seat's back and past its
armrest, from the overhead bins down and partly below the seat's front,
in their seated frame when they have one. Maniac looks may wear a dome (`worldDomed`, the
air gear's bowl alone) or roll (`worldRoller`: a fixed costume direction
or their own, decoded through `scummverseCostumeFacing`, and newly drawn
gear after the limbs by `ClassicCostumeRenderer::drawExtra`: a pot on
wheels under the feet, or skates in the rows the feet are lifted by,
`kWorldSkateLift`; V1 elevation counts two-pixel rows). Characters from
other games may hover (`worldHovers`, a lift capped for tall ones), bounce
(`worldBouncer`: hops while moving, a hop under way finished on stopping,
and a jaw: talking, the head above it lifts off it every other step), or glide
(`worldGlider`: the standing pose while moving, optionally with a newly
drawn dress-up over the sprite's head, `scummverseDrawDressUp`, and drawn
mirrored facing left when every frame looks right, `oneWay`). Native
game folders are found at the top of Documents or one folder down
(base/main.cpp and the iOS status alike).
TOUR (0085): common/scummverse_tour.{h,cpp} is portable (the interface's
request slot and the game's published label, both under a mutex);
engines/scumm/scummverse_tour.inc is the game's side, stepped from
scummverseUpdateRoaming: an ordered stop list built once from static
tables (so stop numbers are the same everywhere): per game, from its first
room, the nearest room not yet visited by doors (a breadth-first search
over mansionPassages, zakLinks or the game's door map; visited rooms are
passed through), else the next unvisited room of the list (a warp). Each
stop: the doors walked to and used the way a player uses them
(scummversePassage, the zakLinks travel, scummverseFollowLink), else a warp
(mansion rooms by startScene, Zak and other worlds by the sandbox's travel),
all as though landing so no ride holds the guide; one pass through each
stop without pauses (0086): straight on to the door out, or first to the
walkable spot farthest from the way in where that door is near it (a dead
end) or none leads on; any step that starts no walk is followed at once in
the same update (scummverseTourAdvance); each stop shown at least a second;
the label's stop (_scummverseTourShown) is kept apart from the stop walked
to; the door the guide sets off to opens first (scummverseTourOpenDoor:
Maniac's passages, Zak's clean doors, zakOpenDoors); the tour's walks are not taps on doors or side exits; the interface's
speed (Tour::setSpeed: 1, 2, 4, 8 or 16; 0087, 0088) shortens
waitForTimer's wait while touring and not paused, so the whole game plays
faster (scummverse_tour_speed), the screen then shown at most every 16 ms;
requests wait in a queue, one taken a game step; paused (0088, Tour::
publishPaused) only warps by number, Next or Previous are made, and Play
walks again to the walk under way (_scummverseTourTarget); stops of games not installed are passed over; the next stop is kept in the configuration
(scummverse_tour_stop). The iOS side (scummverse_tour_ui.inc) shows the
label and the control bar off the game's picture (0091: the band left of
it in landscape, under the toolbar in portrait, by the layout contract;
over its top left only without room) and the controls (Worlds menu, or a
tap on the label). Characters drawn only from the front in their costume
are newly drawn from the side when facing left or right (0091, catalog
kWorldProfiles; the renderer's drawsFigure leaves the costume's limbs out).
CAMERA (0081): three parts. common/scummverse_camera.{h,cpp} is portable
(the request slot the interface fills and the game takes, the hold flag,
whole-pixel enlarging with rows 6/5 of columns, selfie framing, pose plans
with their surprises, names, and a sink the saver registers);
scummverse_camera_engine.h is its plain-types face for the engine.
engines/scumm/scummverse_camera.inc is the game's side, run at the top of
each scummLoop: a photo copies the last drawn frame, the main virtual
screen (CLEAN) or the main, text and verb screens by their lines with the
text overlay and the V1 DOS line colors (FULL; never the banner screen); a
selfie (sandbox V1 only) keeps everyone's pose state
(`Actor::getPoseState`), the gfx usage bits and the other worlds'
animation clocks, poses and draws each shot without running scripts,
frames the first and keeps that frame, and puts everything back; the next
step draws it before any photo (the saved state is byte for byte the same:
tools/test_camera_engine.py). The iOS side
(scummverse_camera_ui.inc) is the button, options, flash, shutter and
saving (Photos add-only, else Documents/Screenshots).
Scene pictures (0076): the same room exported in another state (a Dig tram
car parked) is fitted with the scene, in colors chosen from it, keeping only
the pixels that differ; the engine draws it into the scene's background
(sliding or dissolving) and redraws. The exporter counts started exports in `<game>-v<N>.try` and writes `.svx` when one
finishes; after `kWorldExportAttempts` (2) unfinished ones the game is
skipped at start rather than crashing every launch.
Playing someone from another game (0069): a sandbox character (1..24) has an
optional saved appearance (a cast member's key). The engine mounts, whenever
the set changes, the frames everyone in the viewed room needs (the scene's
guests at the scene's scale, appearances at a person's height there) into
the shared character slots 192..255, draws them through the same actor hook,
and overrides only the name lookup; inventory, verbs, travel and saves stay
the sandbox character's. Maniac's own (kWorldManiacLooks) and Zak's own
(kWorldZakLooks, 0096: the scene residents) are native looks: the sandbox
costume itself, Zak's in its colour (kWorldZakTints, actor palette slot 1);
the saved home look (kScummverseHomeCostumeVar + id) is the costume, with
the colour plus one above it (0 in older saves). Zak's imported costumes are
sandbox 35..51 (kScummverseFirstZakCostume, kScummverseZakCostumes;
scummverseMountZakCast); residents stand in their scenes
through the borrowed actor 15 (zakResidents). Zak's people who walk about
borrow Maniac's unnamed actors 8, 17 and 18 (and 20..22, 24); actor 19 is
Maniac's man-eating plant (kManiacPlantActor), which the study's entry
script places, so Zak's Zaire villager is a resident (0098; older saves'
villager in actor 19 is the plant again).
The character screen (0094) replaces the roster as the way to choose who to
play: scummverseCastOffer sends one box per game (Maniac, Zak, then
kWorldGames) with its lead's face drawn from the player's files (the
roster's portrait for Maniac and Zak, WorldBridge::spritePortrait of the
exported frames for the rest; leads in catalog kWorldLeads) and its people,
each as a request: kWorldCastActorRequest + actor (switch, own look) or
kWorldCastRequest + appearance key (take the look, go where they live).
The iOS screen (scummverse_cast_ui.inc) only shows them and sends the
choice back. A new sandbox game skips the opening: runBootscript runs the
boot scripts (pauses and messages cut short) until the sandbox is ready,
and the screen opens; "Play as someone else" (command 61) and the game's
New Kid button open it again. Without SCUMMVERSE_LOCAL_AI it falls back to
the roster.
v7/v8 editions are compiled in solely so the player's copies can be exported.
