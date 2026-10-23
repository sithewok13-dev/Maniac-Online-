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
Since 0101 participants are 64-bit (`uint64_t`, IDs 1..63): sandbox characters
1..24, a scene's own characters 25..29, wanderers visiting 30..55
(`kScummverseTalkVisitor` + slot; `scummverseTalkVisitor` tells the runtime who
each is). Only 1..24 can follow.

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
physical room, with palette slots from 16 for the scene and every slot after
its colours shared by its characters (0101: 176 for the scene, fewer down to
128 when many characters are expected on arrival; in the mansion and Zak's
rooms characters get 16..255). Characters share them fairly: each in turn
keeps its own most used colours, passing over near-duplicates. Characters use transient guest actors (Maniac 25..29, never
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
lowest walk box at least a quarter the size of the biggest. Scenes are "SVW5"
(export version 17; "SVW4" added object states after those scripts): the
game's own box connections (getNextBox for every pair of boxes; none in a
room without a matrix), the room's colour cycles as cyclePalette runs them
(the older games' sweep a step a frame, only those started; the others'
rotation a step each delay, at most one a frame; none with EGA dithering; a
frame taken as 4 ticks), and per object its name (printable, without the
later games' "/id/" keys and escape codes) and pictures: its rectangle
without it, then in each of its states, and which one the scene shows
(exactly the scene's rectangle). Each picture is the scene with what that
state changes: the rectangle drawn in the state against drawn as it is, so
what the rooms' scripts and presets drew there stays (scripted rooms bring
the room's object states up to date first, as the game does every frame).
A state is drawn only when every strip of its image is where the game's
drawing reads it and the object is within the room's rows; drawing takes
the image from the global state table, so both it and the room's copy are
set, then put back with the heights drawing rounds. The old engine reads
them and ignores what it has no use for; a door link
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
near pair swung against the far pair from the hip; the camel, the Dig's
Creator) and `kWorldOneFacings` (drawn facing one way only: the other
facing is its mirror). Guests
drawn only from the front get side views (`kWorldSideViews`: a relative's
stance and walk, repainted, its head found by its face colour and replaced
by a newly drawn one, repeated behind it; the three-headed monkey). Some
get a seated frame (GuestKind `kGuestSeated`, `kWorldSeatPoses`: parts of
the stance facing right, each turned about a pivot and set from the
origin or on another part, those marked front in a second picture drawn
over the seat's front (no pose uses one now); the camel sitting back,
the dragon's tail up the seat's back, the nest monster sprawled, the
three-headed monkey filled solid). In a plane seat the big ones
(`kWorldSeatFits`) are fitted from a set place by the seat's back to past
its armrest, from a set row down and partly below the seat's front, in
their seated frame when they have one, nothing left of the seat's back
line behind the seat's front. Maniac looks may wear a dome (`worldDomed`, the
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
the shared character slots (WorldBridge::guestFirstSlot onwards), draws them through the same actor hook,
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
v7/v8 editions are compiled in so the player's copies can be exported, and
for story play.

## Story play (0181)

The original games, each in its own engine as ScummVM runs it, opened from
Maniac's Worlds menu ("Play the original games"). Each game found in
Documents has a persistent target, `scummverse-story-<id>` (engineid scumm,
its folder, `scummverse_story=true`, no platform: its edition is detected as
it starts), set up at each launch by base/main.cpp and, for a folder added
while the app runs, when it is opened (`common/scummverse_story.h`, which
also holds the Documents folder lookup the exports use); the start guard is
unchanged (only Maniac or the sandbox from the command line). A game whose
story needs a file its folder lacks (`kWorldStoryNeeds`: Full Throttle's
DATA, The Curse's RESOURCE fonts; its engine would stop the app) is refused
in words. The hub
Maniac's `scummverseOpenStory` (a sibling of `scummverseOpenSandbox`: not
during WiFi or the tour) saves Maniac to slot 100 and chains the game's
target at its story save, slot 99 (`kWorldStorySlot`, an ordinary save named
"Story", so iMUSE state is kept), when it has one. In a story the engine
carries none of the mansion's additions (`_scummverseStory`; the roaming,
doors and safety gates are the audited Maniac's, and other worlds' rooms
192-199 are read only in the audited Maniac); `scummverseUpdateStory`
answers the Worlds menu: Back to Maniac Mansion (`kWorldStoryHomeRequest`)
or another game's story (`kWorldStoryRequest + game`), each after saving to
slot 99 (not while the game has the controls, `_userPut <= 0`, nor while its
own save or load waits; retried for 8 seconds of game time, then the player
chooses Leave or Stay). Any other way out (the game's Quit, ScummVM's menu)
saves it in `go()` on quitting (`scummverseStoryQuit`). A story is opened
from the newer of slot 99 and its autosave (slot 0). The home rule is
main.cpp's: a story run
that ends with nothing queued (Back, the game's own Quit or Return to
Launcher, or a game that cannot start) chains Maniac at its slot 100. The
codes sit above the sandbox's games (a static_assert keeps them apart), so
the sandbox ignores them. iOS: `scummverseStoryPlaying()` (the catalog index
of the story playing, -1 none) switches the Worlds button to the story's
menu (Go to <game> for each folder found, Back to Maniac Mansion).
`tools/test_story_engine.py` walks it through the real engine.

Maniac Mansion's own story (0184) is `scummverse-story-maniac`: the folder
the mansion itself plays from (main.cpp's `maniacPath`, refreshed at each
launch; `addStoryTarget(game, maniacPath)`), platform dos, and
`scummverse_roaming`, `scummverse_exploration_doors` and
`scummverse_exploration_safety` false; in the engine a story is never the
audited Maniac (`auditedManiac` requires `!_scummverseStory`), so every
addition behind those gates and the other worlds' rooms are off whatever the
keys say, and the camera refuses ("No camera in this game"). Its saves are
its own (`scummverse-story-maniac.sNN`), apart from the mansion's
`maniac.*`. The start guard also refuses any story target named on the
command line (gameid maniac included; known by its prefix in any case, or by
its `scummverse_story` key). On the phone the Talk, AI and Camera buttons,
the conversation bar and Arrive hide while any story plays (a chat left open
shuts; the Worlds button stays), and the menus call it "Maniac Mansion
(original story)". The story menu's Save now (`kWorldStorySaveRequest`,
below the home code) writes the story save and the game goes on; a leave
whose chain is refused clears `_scummverseStorySaved`, so quitting saves
again. Of a story save and an autosave made in the same minute, the one
with more time played is the newer.

Going on at the next start (0184): a story that has played five seconds of
its own time writes `scummverse_story_playing=<target>` to the application
domain (flushed); the mansion clears it whenever it starts. At launch
main.cpp takes it (`Scummverse::storyToResume()`: a story domain whose
folder is there and whose `kWorldStoryNeeds` files are all present; the key
is removed and flushed before anything starts, so a game that stops the app
as it starts is not opened at every launch) and starts that target after any
exports (`scummverseQueueWorldExports(then, ...)`) or at once, Maniac's
command-line settings set aside. A story started with no save named goes on
from its newest (`scummverseStorySlotOf`, kept in `_scummverseStoryFrom`).
The home rule then brings the mansion back at its slot 100; a story that
cannot start goes home too, even when it was the first run. The
kWorldStoryNeeds check lives in `common/scummverse_story.h`
(`storyMissing`) for both.

From the new engine (0185): its Worlds menu also has "Play the original
games" (the same list). `SandboxEngine::openStory` checks the story's target
and files as the mansion does, saves the sandbox, drops its own way back
(the mansion at slot 100, queued when the sandbox was opened: a story goes on
only with nothing queued after it) and chains the story with no slot, so it
starts from its newest save; the home rule brings the mansion back at its
slot 100, saved when the sandbox was opened. The sandbox's `story` selftest
and `test_sandbox_engine.py`'s third switch walk Maniac -> sandbox ->
Maniac's own story -> Maniac.

Story mode and Explore mode (0186), kept apart: `scummverse_mode` in the
application domain ("story" or "explore"; Explore when unset;
`common/scummverse_story.h` storyMode/setStoryMode). Explore mode is the
mansion, the other worlds and the new engine; their Worlds menus offer
"Story mode" (`kWorldStoryModeRequest`): the mansion saves its slot 100 (the
request taken whatever it is doing, `scummverseWorldPeek`, even on its kids'
screen), the new engine saves its place and drops its way back; each sets
Story mode and returns to the launcher with nothing queued. Story mode's home
is its list (base/main.cpp `scummverseStoryList`): each story found, Continue
(a story save or autosave) or Start, "(needs FILE)" when kWorldStoryNeeds
are missing (not taken), "(no films, voices and music)" from
kWorldStoryWants; and "Explore mode". On the phone it is the native list
(`scummversePlaces*`, its Cancel showing it again) over no game
(`scummverseStoryPlaying(kWorldStoryListShowing)` hides the game's buttons
and Worlds); the desktop builds take `scummverse_story_choices` in turn
(tests), else Explore. It comes up at launch in Story mode with nothing to
go on in (after the backend, or once any exports are done: they then chain
nothing after them), and whenever a run ends with nothing queued in Story
mode (a story's Story list, `kWorldStoryHomeRequest`; its own Quit; a story
that cannot start). A story's "Explore mode" (`kWorldStoryExploreRequest`)
saves it, sets Explore and goes home: the mansion at its slot 100. Going on
at the next start is Story mode's only. Stories default to text on
(`subtitles`, unless set).

Copy protection in story play (0186): `scummverseStoryPassGuard` answers
Monkey Island 2's recipe screen, which ScummVM leaves to the player with
copy_protection off (room 108; any number is taken, ScummVM reading the
answer for the number asked: "1", then Return, every 1.5 s of game time, at
most 20 tries; then the player's). Sam & Max's floppy dolls screen (room 71;
0187, `scummverseStoryDressDolls`): any press wakes the wardrobes (var 151);
the game then picks a page of its manual (var 152, 1-10) and a doll (var
153: 0 Sam, clothes objects 715-744; 1 Max, 745-770), and lights its button
(object 771, state 1). Its button checks the clothes the page asks for,
three letters a doll in its own table (array 304, read at run time through
`scummverseArrayAt`, never copied: object = first + letter - 'A'), by their
state; a wrong answer has one more chance (var 154), then the game quits.
Story play puts on (state 1) any of the three that is off, then presses the
button at its centre (mouse events through the event manager), every 1.5 s,
at most 20 presses. (As compiled, its check stops at the doll's first item
when that item is not asked for, so only the page whose answer includes it,
page 4, ever refuses a bare press; the test holds the dolls to that page.)

Sam & Max saves made before the game first sets its cursor (just after its
intro, as a story's first save can be) reload with its after-load script
setting the cursor from object 0 in room 92, which would stop the game;
upstream's fix for bug 14467 skipped only room 93, and 0187 skips object 0 in
any room (`script_v6.cpp`, SO_CURSOR_IMAGE).

Zak imported from the Files app (0185, iOS): the importer keeps its copy in
Application Support (`ConnectedWorlds/zak-<uuid>`, outside the Documents
chroot). The backend adds a `connectedworlds:` virtual drive for that folder
(as upstream's `appbundle:`), and `addStoryTarget` gives Zak's story target
the path `connectedworlds:/zak-<uuid>` (from `iOS7_getZakDirectory()`) when
Documents has no zak folder; the menus count such a Zak as found.

## Wanderers (0101, everyone out since 0103)

Other games' characters roam outside their home rooms
(`common/scummverse_wander.{h,cpp}`, plain C++, `tools/test_wander.cpp`;
std-free bridge `scummverse_wander_engine.h`). Places are one code each
(kind Maniac/Zak/world, game, room, below 65536) and belong to a game;
doors come from mansionPassages, zakLinks and the generated door maps (a
door into a map or floor plan leads on to where its doors go). Every
exported character is out (Wander::Cast, with its game, weight and whether it
is small); the cast's signature is saved in variable 256 and everyone's place
two to a variable in 257..398 and 529..599. Off-screen a character is only
that note: it moves on through a door now and then, sometimes anywhere (by
place weight: every game an equal share, split over its places; Rules::lean
could keep some in their own game, 0 now), sometimes to another one, sometimes to a room
next to the player's (never into it once four are there, small ones aside,
since those there stay while watched). A scene's residents are out too (the
scene leaves them out at home; they are visitors wherever they are).
`engines/scumm/scummverse_wander.inc` shows those in the viewed place as
visitors, as many as its floor has room for (`Wander::capacity`: one per 40
pixels of floor, fewer for the characters already there; small ones always
fit; at most 26 slots): Actor_v2 instances outside `_actors` with number 0
(MM V1 numbers objects from 30, so more numbered actors would collide).
processActors sorts them with the actors, walkActors walks them,
resetActorBgs restores what they covered (they have no strip bits; anyone
sharing a restored strip is drawn again). They speak as the narrator in their
own colour, stand where their key and the floor put them (the same after a
load), and walk in from a side when they arrive while the player watches.
Engine tests run with `scummverse_wanderers=false` (residents at home) unless
they ask for them.

## Sandbox engine (0104, preview)

A game of its own inside ScummVM, made for the sandbox (`engines/scummverse`,
engine id `scummverse`, game id `sandbox`; the user: "a new game inside
ScummVM, written just for the sandbox ... no character limit, the iPhone's
full resolution, full color. Everyone is equal"). It plays from the worlds
cache (`.svw` scenes, `.svc` characters, exported from the player's own games
by their own SCUMM engines, see Other worlds), never from game files itself,
so its rules are its own and no game's limits (MM V1's numbering, 16 colours,
one palette) apply.

- `common/scummverse_stage.{h,cpp}` (plain C++, `tools/test_stage.cpp`; the
  engine reaches it through the plain-types `scummverse_stage_engine.h`): a
  place on a screen of any size. View::fit makes the scene as tall as the
  screen allows and no wider than its own game's screen at that size (art
  drawn for 320x200 has pixels 1.2 times taller than wide, Curse of Monkey
  Island's 640x480 square ones); wider rooms scroll after the one followed:
  the camera centres on them, then scrolls only when they come within a
  quarter of the screen of an edge. Walk boxes (switched-off boxes and the
  games' placeholder at -32000 dropped; flat ones, lines and points, hold
  only themselves) meet within 3 pixels (kBoxGap: the older games draw
  neighbours two apart); which meet, and the groups reachable from one
  another, are worked out once per scene (Links). Paths go breadth first
  through meeting boxes, crossing where best on the way, and end as near
  the destination as the boxes reached allow. Where the export has the
  game's own connections, boxes also meet where either is the other's next
  box on the way (areas a game joins though apart); touching boxes still
  meet (a game may route between them through a box switched off here).
  The scaled scene keeps palette indices, its colours a 256-entry table that
  the room's colour cycles move (up, down or the older games' sweep), drawn
  again when they do; an object can be shown in any of its pictures
  (showObject), the scene and its scaled copy updated in its rectangle. Characters are drawn in true
  colour from their own palettes, as tall as the scene's people (their
  game's lead against the scene's, heroHeight) at the box's own scale, a
  third on map rooms, nearer ones in front. They walk as the games do: a
  step every six ticks, at most 8 across and 2 up or down the scene (twice
  that in Curse of Monkey Island's finer pixels), smaller far away (never
  below a quarter), one walk frame a step, facing the way they go. Nothing
  is limited to a palette or to a number of characters. The screen is drawn
  again only while someone walks.
- `common/scummverse_panel.{h,cpp}` (plain C++, `tools/test_panel.cpp`; the
  engine reaches it through `scummverse_panel_engine.h`, step 2c, 0107): a
  game's own verb panel ("<game>-ui.svi", "SVI1"), exported by its SCUMM
  engine from the game's own start (scummverseExportPanel, after its places
  and their marker: its boot script run on at once with scummLoop, scripts
  never waiting, cutscenes left, messages gone, the music's clock moving
  with the frames through _scummverseMusicTimer, a typed answer where the
  catalog's WorldPanel names a room that waits for one; then nothing
  carried, the sentence line and names emptied, every verb in its usual
  colour; the verb screen as drawn, each verb drawn highlighted, the slots
  and arrows, and each letter 32..255 drawn by the game on the sentence line
  in the sentence's own charset and the talk's). The catalog's kWorldVerbs
  names each verb's use by its game's own number (WorldVerbKind). The panel
  is laid out under the scene at the scene's scale (as the original's
  screen: the stage's height is what is left above it), its columns
  centred; taps hit verbs (or the nearest within 6 panel pixels), slots and
  arrows; it is composed at its own size (a chosen verb lit, the sentence
  line in the game's lettering, things carried as names cut at their slot
  or pictures fitted to theirs, the names lists' arrows only when there is
  more) and scaled; speech is drawn in the talk lettering at the scene's
  scale over the one played. `Panel::decide` holds the plain rules (the
  games' scripts do not run): look names, open/turn on picture 1 from none,
  close/turn off picture 0, push/pull the next picture, pick up takes small
  shown things that are not doors (into the inventory; the place then shows
  picture 0; what takes a hand needs the one played near it); push and pull
  switch two-picture things, else step through the pictures showing them;
  the rest is said not to work. Things carried keep only the
  pixels where they differ from the place without them, in their scene's
  colours, and go with the one played from panel to panel. Where a game
  puts things ("<game>-things.svo", "SVO1", 0108, scummverseExportThings:
  from the game's own start, after its panel, each place set up again with
  its entry script run, cutscenes skipped, the game's variables and object
  states put back after each room; per object its picture and the verbs its
  own verb table answers, the catch-all entry aside; bit 14 that it has a
  catch-all entry, bit 15 that it is untouchable or carried there; only
  after its panel was captured): the sandbox shows each object so unless
  the player changed it, leaves out those away, and `decide` also needs the
  thing to answer the verb there (one with only a catch-all entry is not
  known). While exporting, the engine's own script checks
  (cutscenes left open, the cutscene stack, nesting, a script of another
  room) are told and passed over (scummverseScriptError); in play they stop
  it as the originals did.
- The mansion in the new engine (0109): kWorldGames ends with the games the
  original engine plays itself (`worldHome`, version 1-2: Maniac Mansion,
  index 10). Its places export like the others' from the game's own folder
  (base/main.cpp takes the Maniac target's path; export targets run with
  `scummverse_roaming` off), with the oldest games' differences handled in
  the exporter: rooms lit (VAR_CURRENT_LIGHTS), boxes and actor positions in
  their 8 by 2 pixel units, object states as bits (a picture shown while the
  "on" bit is set; objects without an image of their own share one image
  pointer and get none), people coloured by their actor (the same number as
  the costume). Its door map is generated from the original engine's own
  tables (tools/world_maps.py reads scummverse_tour.inc's rooms and
  scummverse_roaming.inc's passages, the rides left out) and its cast is
  newly written in tools/world_cast.py (HOME). The original engine's menus,
  visits, tour, wanderers, character screen and status skip home games; the
  new engine's game menu lists the mansion with the rest. Zak McKracken
  (0110, index 11) follows the same way from its own folder: its map is
  the original engine's Zak tables turned back into Zak's own numbers
  (logical rooms 128+ as pseudo rooms of their resource, objects by their
  place in their room, build/foreign/links/zak-objects.json), its cast is
  coloured by kWorldOwnTints; every Zak room is exported with its entry
  script (room colours and boxes it sets kept, what it changes in the game
  put back after the room), a logical room is cut to the camera window
  its script sets (boxes outside switched off), a room whose script leaves
  at once is exported without it, and doors whose object a window leaves
  out are dropped when the map is generated (from build/worlds).
  Their verb panels (0111) come from ScummEngine_v2::scummverseExportPanelOld:
  the verb screen set up as the edition's (initScreens 16,152 for the
  mansion, 16,144 for Zak), the game's verbs killed, then WorldPanel's start
  script (the mansion's 164) or the boot script run until at least four
  verbs stand unchanged for 30 frames; the verb screen cleared and the
  verbs drawn plain and each lit; the sentence line, the four slots and the
  arrows taken from the engine's own `_mouseOverBoxesV2`; letters 32..127
  drawn by drawString in charset 2. It writes the same "SVI1" as the later
  games' panel (scummverseWriteUi). The oldest games' verbs add WorldVerbKind
  Read, Unlock, Fix, New kid, Put on and Take off; worldVerbAnswerKind maps
  each to the verb whose answer bit it uses in the things file (Read as
  look, Unlock as open, the rest as use; New kid none). `Panel::Thing`'s
  `takenShown` is their pick-up way round (there in picture 0, taken in 1),
  and PanelBridge::addItem's `without` the picture of the place without it.
  The oldest games' people are exported with VAR_CURRENT_LIGHTS lit (actor
  colours on) and the variable put back after: their costumes draw everyone
  in one grey otherwise, and a scripted room's put-back variables may not
  be lit.
- Controls over the scene (0112, step 2f; `WorldOverlay`, "SVI2"): a game
  without a verb panel has its controls drawn by its scripts when the
  player taps (Sam & Max: the pointer is the verb, a right click the next;
  a box of things opens from a button). ScummEngine::scummverseExportOverlay
  runs the game's start until its button actor stands in the scene, takes
  each pointer from `_grabbedCursor` as right clicks bring it round (it must
  come back to the first), the button with scummverseCaptureActor, then
  opens the box with a click on the button and draws its objects alone with
  scummverseCaptureObjects (front and back buffers filled three times, each
  object drawn with drawObject; what keeps the fills is clear, the screen
  put back after); the icons are the box's verbs (lit: their next
  image, where they have one), the catalog's cells its slots; the talk
  lettering is drawn by a verb slot it borrows (scummverseCaptureLetters,
  the panels' too). "SVI2" is "SVI1" with the panel's mask after its
  pixels and, after the letterings, each verb's pointer, the button and the
  box's shutting icon (see scummverseWriteUi). In common/scummverse_panel
  `Source::over` makes the panel a box laid over the scene's view: shut,
  only its button is hit and drawn (renderControls, with the pointer at its
  hot spot); open, every tap is the box's (`close` off it), drawn only
  where its mask is. The sandbox keeps the whole screen for the scene, a
  right click (EVENT_RBUTTONDOWN) brings the next verb or shuts the box,
  and the pointer stays the verb chosen. The Dig (0113): its box is a blast
  object (`WorldOverlay::blast`; v6 on ScummEngine_v6::scummverseBlast and
  scummverseDrawBlast find and draw it alone), its mask 2 where it darkens
  the scene (a pixel that is neither the same over three fills nor the
  fills themselves: drawn through a shadow table, the one that turns the
  fills into what was seen, whose average darkening is the file's shade
  byte), its
  only verb kWorldVerbAct (Panel::decide: pick up, else open, else look;
  doors walked through), its lettering drawn by drawCharV7
  (scummverseCaptureLettersV7, v7).
- A coin held over a thing (0114, step 2f; `WorldCoin`, "SVI3"): Full
  Throttle's verbs are the parts of a coin a held press opens.
  ScummEngine::scummverseExportCoin runs its start only until the player
  has the pointer, then draws the coin and the skull of things alone with
  scummverseCaptureActor: an actor of the engine's own (the last) wearing
  their costumes in the catalog's animations, its palette remapped as the
  game's kernel function 14 does (Actor::remapActorPalette, threshold 0:
  free entries take the costumes' exact colours, so the file's palette is
  taken last). Each verb's part is where its lit animation differs from
  the coin's own, lit through a mask (the scene shows where the lit picture
  is clear); the skull's arrows are the skull in its arrow animations over
  the catalog's eye rectangles. "SVI3" is "SVI2" without a button (a right
  click opens the box), the verbs' rectangles on the coin, and after the
  shade the coin (its anchor the hot spot), the name's centre and colour,
  each verb's lit mask and the arrows' pictures. In
  common/scummverse_panel `Source::coin`: Panel::openCoin places the coin's
  anchor at the press, the coin kept on screen; coinVerb picks the
  smallest part under a point (the eyes lie in the skull); renderCoin
  draws it, the part lit and the name in fonts[0]; the open box's hit gives
  its arrows (code 4) and scroll goes a thing at a time; kHand is
  Panel::decide's hand (pick up, open, close, else it doesn't work). The
  sandbox keeps a press (EVENT_LBUTTONDOWN), opens the coin once it is held
  kCoinHold (250 ms; the iPhone's long press already waits half a second),
  lights the part under the pointer (EVENT_MOUSEMOVE) and does its verb when
  let go (EVENT_LBUTTONUP); a press let go before the coin opens is a tap
  where it began.
  The Curse of Monkey Island's coin (0183, its entry in kWorldCoins, v8):
  hand, skull and parrot (verbs 7, 6, 8); its start (`start`, the plain
  game's object on the first menu) tapped once the pointer shows, from
  variables as a fresh start has them (the places' export leaves them as
  its main menu's), until the player has the pointer in another room; its
  films skipped while exporting (smush_player.cpp). Its costumes keep the
  room's colours (no remapping); its lettering is FONT0..4.NUT's plain
  letters (CharsetRendererNut). The name goes on the line the game keeps
  for it (the sentence fields, centred at `nameAtX`, `nameAtY`), not under
  the coin. Its chest (`boxBlast`, the blast object the game draws it as)
  is opened with a right click and drawn alone, its things left out; its
  cells a grid (`rows` of `columns`, `stepY` apart) and no arrows (zero
  rectangles; Panel::arrows() false, the sandbox's check skipped).
- Loom's distaff (0115, step 2f; `WorldDistaff`, "SVI4"): a panel under
  the scene whose verbs are notes (kWorldVerbNote, their ids 0 c to 7 high
  C). ScummEngine::scummverseExportDistaff runs Loom's start, taps its
  choice of how hard (the catalog's object), runs on to the first place,
  marks every draft learned and every note known (the debugger's variables:
  drafts from 50, two each, the notes three bits each; 122 the notes known)
  and runs the script that draws the distaff (18); the verb screen as it is
  then is the panel (the staff's letters and notes are drawn by the script,
  not as verbs), each note's verb (1 to 8) lit by drawing its glow's verb
  over it (from the catalog's, every fifth), the drafts read from those
  variables. "SVI4" is "SVI1" with, after the letterings, the box where the
  thing chosen is shown and the drafts (name, notes). In
  common/scummverse_panel `Source::distaff`: Panel::play records a note (lit
  as the selected verb) and at the fourth returns the draft it spins (16
  more backwards); `choose` keeps the thing chosen, drawn fitted in the
  box (Panel::fit, the slots' too); the sentence line is not drawn. The
  sandbox (chooseVerb, spin, chooseThing) plays a tapped note, unlit after
  half a second, and spins Opening as kWorldVerbOpen on the thing chosen
  (backwards kWorldVerbClose) through the plain rules; a thing tapped
  (not a door) is chosen, its picture from its place's file, and tapped
  again is looked at.
- Chat in the sandbox (0116, step 4): SandboxEngine::talkScene tells the
  iPhone's chat (common/scummverse_ai.h, the same calls Maniac makes) who
  is here every step: the one played as talk ID 1 with its appearance key
  (scummverseTalkAppearance, so the chat names and plays them as that cast
  member), everyone else on the stage as a visitor (scummverseTalkVisitor,
  talk ID 30 + their slot, slots in stage order without the one played, at
  most 26), the place as Maniac tells it (the mansion's rooms by their own
  numbers, the other games' by worldPlaceKey). A line comes back only while
  none is shown (canSpeak); it is said over its speaker's head (sayAs, the
  game's talk lettering, kept within the scene's picture) while their talk
  frames play (Stage `Actor::talking`, a frame each kTalkTicks), for as
  long as a verb's line, at most 15 seconds. Those in the conversation stop
  (Scene::stop), face the one played (Scene::face) and do not stroll; the
  one played turns to them as it begins and to whoever speaks. While the
  chat asks whom to talk to, a tap on the scene goes to scummverseTalkPick
  with whoever is drawn in front there (talkIdAt; 0 for no one, which the
  chat keeps asking), never a walk; a coin game's press is then a plain
  tap. On leaving, the chat is told no one is here (talkEnd). The calls go
  through `SandboxEngine::Talk` so the "talk" self-test can put in a
  stand-in (the desktop has no chat). Each step also tells the chat's window
  the place (scummverseTravelScene, as Maniac's companions code does; its
  token resets the window's transcript); `enter` ends any conversation
  (talkEnd), since the stage's slots are given out again. A line whose
  speaker is out of view, or with no lettering loaded, is kept only
  kUnseenLine ticks. The chat's pick mode is never armed by its window yet
  (Runtime::armPick has no caller), so the picking tap is reached only from
  the self-test's stand-in.
- The character screen in the sandbox (0118, step 4): the Worlds menu's
  Play as someone else sends kWorldSandboxCastRequest; castOffer gives the
  iPhone's screen (scummverseCastGame/Member/Show, as Maniac's
  scummverseCastOffer) a box per game, slot 0 the mansion (the screen
  starts afresh at slot 0), 1 Zak, 2 + n the others, each with its lead's
  face (kWorldLeads; WorldBridge::spritePortrait of its .svc) and its
  installed people (kWorldCast, the lead first, once by name), each as
  kWorldCastRequest + appearance key (the mansion's and Zak's people too:
  here they are keys like everyone's, not Maniac's actors). Every polled
  request now goes to `request`, which takes the back, cast and game
  requests and the screen's choices (castChoose: hasCharacter and
  worldAppearance, then the cast's place if installed and walkable, else
  the game's first; on failure the one played and the place before). The
  chat's sceneToken | command can fall in the screen's range (place keys of
  10000 and up); those are no key and do nothing. The calls go through
  `SandboxEngine::Phone` (the chat's too) for the "cast" self-test's
  stand-in. castHome is the one rule for both the screen and a choice
  (installed, not `_broken`, in the cast, a place to be); the people are
  listed once by name and once by key; a box's face is its first person's.
  buildWanderers takes everyone, the one played too; `enter` and
  `arrivals` pass the one played by, so a choice never shows them twice and
  the wanderers' signature does not change with who is played.
- The camera in the sandbox (0120, step 4): the run loop asks cameraStep
  first; while it holds (Camera::held, the iOS Photos prompt, or a selfie)
  nothing else runs (events drained, a press let go, time not carried
  over). Requests are Maniac's (Camera::takeRequest): a clean photo renders
  the stage alone into the frame and crops its view; a full one presents
  and takes the frame whole; both through Camera::shootTrue (square pixels,
  one whole factor, Camera::squareFactor). A selfie (selfieBegin, Pose,
  Shoot, End) poses every actor with Camera::planShot's choices through
  Stage::pose (a way and a frame held; -1 their own), shows the stage, and
  takes kSelfieSettle, kSelfieNext and kSelfieShow as Maniac's; its frame
  (Camera::frameSelfie with rowAspect 1: the stage's pixels are square)
  from the drawn rectangles, fixed at the first shot, within `shown` (the
  part of the scene on the screen: View::width less the camera, cut at the
  screen, as Scene::render draws it; the clean photo's crop too).
  Camera::setPlainSink is for the "camera" self-test's stand-in; it holds
  the sink set before (the iOS one) and puts it back when let go.
  cameraHold is the run loop's holding (events drained, a press and a coin
  let go, the chat pumped while iOS asks for Photos).
- The tour in the sandbox (0122, step 4; common/scummverse_tour.h, the
  iPhone's label, bar and menu unchanged): tourBuild orders each game's
  installed places (the mansion, Zak, then catalog order) as Maniac's
  scummverseTourSegment does: from the game's first place, breadth first
  over its map's links to the nearest not visited (TourStop::legs, the
  links in turn; places seen before passed through), else the next not
  visited (a warp). The run loop takes Tour::takeRequest into tourCommand;
  step runs tourStep (kTourAcross: to the far end, or straight to the door
  out when it is more than a quarter of the place away; kTourToDoor: then
  `travel` through each leg; kTourRefusedStop: kTourRefused ticks), each
  stop shown at least kTourGlimpse ticks, each walk at most kTourWalk; the
  run loop's ticks are multiplied by Tour::speed while touring. Taps wait
  while touring unpaused; requests that change the place end it
  (tourEnd(false)); saveState does nothing while touring (where it began
  stays saved; tourStart saves it); the stop to resume at is ConfMan's
  scummverse_sandbox_tour_place (game * 1024 + room, written and flushed at
  each stop by tourKeep). From 0123: run() calls tourReady (build and
  publish) once the first place is shown; kTourToDoor goes through only a
  link of the place it is in that the one played reached (tourReached:
  within kDoorReach of the door's walkable point; maps a tap away), else
  warps on (Touring::unreached); a walk to a door gets kTourDoorWalk ticks;
  `leg` is the way's position (tourPlan keeps it: a pause on the way goes
  on); a place passed through publishes its own label; a request back to
  Maniac ends the tour home.
- The Dig's tram in the sandbox (0124, step 5; kWorldTramLines): `enter`
  mounts the station's car ("<game>-<room>-car.svw") as the stage's second
  picture (Stage::mountPicture: the scene in another state, only where it
  differs, remapped to the scene's colours; showPicture(dx, amount) slides
  it within its rectangle or dissolves it, rescaling that rectangle; the
  scene's object pictures are applied after it), before the place's
  things. SandboxEngine::Tram is Maniac's phase machine (kTramOpen 90,
  kTramClose 390, kTramGone 480, kTramThere 600, kTramDone 690 ticks;
  `parked` two bits a line) without Maniac's variables: tramStep calls the
  car when the one played stands still on the ledge (within 3 source
  pixels a 320-wide unit, re-armed beyond 6; not while touring), hides them
  (Stage::hide) when the doors close on them, enters the other end at
  kTramThere, and shows them walking to the exit at kTramDone; tramShow
  puts the car in view from the state (tunnel: slid; 0: dissolved). A tap
  on a car's door walks to the ledge; taps wait while riding. `announce`
  draws a line at the top of the place. From 0126: Stage::showObject keeps
  the second picture's `clean` copy as the place is now and shows the
  picture again over it (as last shown: Picture::applied, dx, amount); the
  dissolve's scatter mixes x and y (scattered(); Maniac's
  WorldBridge::showPicture likewise); `armed` starts false at each station
  (a tap on the car's door arms it); a ride whose player is seen again
  (another `enter`) is no longer theirs.
- Rides between a game's places in the sandbox (0125, step 5; the
  catalog's kWorldRides {game, room, object, target, arrival, kind} and
  kWorldAirports {game, room, gate, city}): a tap (walking) on a ride's
  object (worldRideAt) walks to its walk-to point (SandboxEngine::Riding,
  kRideWalking); there a plane asks where to through the Phone's places
  list (scummversePlacesBegin/Item/Show, each other installed airport as
  worldPlaceRequest; the choice comes back to `request` in the place range
  and rideChosen takes it only while asking, from where it is), the others
  count down at once; kRideBoarded ticks after, the one played is hidden,
  and after kRideTrip of its kind `enter`s the target at its arrival
  object. Walking off before then cancels it with a line; taps wait while
  riding; `enter` lets any pending ride go. The van (0127,
  kWorldRideVan): its sites are kWorldVanSites through worldVanPlace (the
  other games' rooms as listed; the mansion's and Zak's by
  kWorldVanPlaces, the sandbox's numbering), offered as kWorldVanRequest +
  site and taken by rideSite; boarded at its door only where it is parked
  (`_vanPlace`, ConfMan scummverse_sandbox_van_place), or anywhere it is
  parked by kWorldSandboxVanRequest (the Worlds menu's Board the Shuttle
  Bug); Riding keeps where it was boarded and where it goes (another game
  for the van). From 0128: doors and ride objects are one candidate list in
  `tap` (objectAt's nearest, smaller first); a list of where to carries a
  cancel request (scummversePlacesCancel, kWorldSandboxStayRequest: closed
  unchosen or not shown, taken by rideStay) and is withdrawn by
  scummversePlacesHide (rideOff: from `enter`, walking off, kRideAsk
  ticks unanswered, the engine closing); a countdown is kept through taps
  and ends by walking out of reach in rideStep; bus and tram check their
  target installed; a failed arrival re-enters where it was boarded;
  rideBoard refuses while touring. From 0129 the parked van is a stage prop
  (Scene::addProp: palette indices, `none` transparent, own colours,
  standing on its bottom centre, `rows` tall at full scale times depthAt,
  sorted with the actors by row, props behind actors on the same row;
  propRect; cleared by load): SandboxEngine::vanShow reads zak-van.svv
  (Maniac's capture) in zak-185's palette (StageBridge::paletteOf) and
  places it beside the landing point (`_vanX/_vanY`, ConfMan
  scummverse_sandbox_van_x/_y, kept by vanPark) sized as Maniac does
  (kVanKidHeight against the place's heroHeight, capped by the room above
  and across); a tap in its rectangle walks to its door (kVanDoorAcross)
  as a kRideWalking van ride (vanWalk). From 0130 the tap tests the
  prop's drawn pixels (Scene::propHit, as render picks them), vanShow's
  margins are in the place's pixels (unit = screenWidthOf/320) and its
  depth takes the map factor; the iPhone places list numbers each list
  and each withdrawal (scummversePlacesGeneration): a Present for an
  earlier one does nothing, and one withdrawn while being presented is
  dismissed by its presentation's completion.
- Doors in the sandbox (0131): walkToDoor keeps where the walk toward a
  door ends (Scene heading: as near as the walk boxes allow); reachDoor
  goes through when the player stands by the door's point, the tap, or
  that end (a part of the place the game joins to the door's only by a
  script); the tour's tourReached returns 1 at the door, 2 at that end
  (counted as `across`), 0 when the walk was cut off. From 0133 the end
  is kept with its link (`_doorGoalLink`, set by walkToDoor only when a way
  was worked out, cleared by `enter`) and counts only for that door.
- The mansion's moments (0134, step 5): SandboxEngine::openDoor shows a
  mansion door open by PanelBridge::decide(kWorldVerbOpen) (the game's
  answers, a differing open picture) through showPicture (kept in
  `_pictures`); reachDoor opens a shut door and waits kDoorOpening ticks
  (`_opening`, counted down in step) before travel; travel opens the door
  gone through and, after `enter`, the door back. From 0136: doorOpens
  (index, picture, shut) says whether and to which picture; travel opens
  only the arrival that is the link back to where they came from, never on
  the tour's way, and saves after; a second tap on the door opening keeps
  `_opening`.
- The tram's parked bits (0135) are kept in ConfMan
  scummverse_sandbox_tram_parked (tramKeep, when a car comes to stand) and
  read at launch.
- The mansion's lights (0141): Scene::setDark (StageBridge::setDark) draws
  no place and no props, everyone in kDarkColor (the games' dark grey),
  until another place loads. SandboxEngine::isLight: in "maniac", a thing
  whose game answers both Turn on and Turn off and whose name has "lamp"
  or "light" (not "flash"); act() turns it before the plain rules
  (lights(on), the game's picture if it differs). `_dark` (game * 1024 +
  room) is applied by `enter` and kept in ConfMan scummverse_sandbox_dark
  (lightsKept/lightsRead: numbers between commas), read at launch. The
  flashlight (0146): Scene::setFlashlight(on, at, 48, 32) shows the place
  only inside that source rectangle (left & ~7, top & ~1, kept inside,
  corners rounded within 4 pixels) while dark; the sandbox's useItem turns
  it on or off for the carried "flashlight" of "maniac" (ConfMan
  scummverse_sandbox_flashlight), and present's aimFlashlight points it at
  the last tap or mouse move over the place (`_beamX/_beamY`, reset by
  `enter`), else at the one played.
- Things changing others, doors kept shut (0151): kManiacFollows (a
  thing whose picture, once changed by act(), is copied to another, here
  or elsewhere: setPicture writes `_pictures`) and kManiacDoorNeeds (a door
  travel refuses until another thing shows a picture; not on the tour's
  way; the doors check meets it first: meetDoorNeed). Taken from the
  original's scripts by tools/test_pool_valve.py's probe: the water valve
  (29/66) drains the pool (6/139), whose ladder (6/172) needs it drained.
  From 0152, kManiacSets (a verb on one thing shows a picture of another:
  the mailbox and desk hotspots, the gate's other views, the gargoyle 10/351
  opening the secret door 10/69) and kManiacOpenedBy (a door only another
  thing opens: its own line to Open/Close, never opened by doorOpens), from
  tools/test_mansion_links.py's probe over every thing and verb.
  From 0153, kManiacTogether (rows: one thing and a verb mask that sets
  each of its parts, anywhere, to picture 0 or 1; itself among them, act()
  returns whatever the panel's rules would say: the shower curtain 24/115..117
  and its end 279, the inverted sink 24/253, the gate 6/138 with 16/143 and
  52/108; push or pull on such a thing whose script answers only the other
  won't budge), kManiacLines (a verb's own line, or "" for nothing: the
  shower tap 24/118; removed in 0155) and kManiacShutsBehind (travel
  leaves the door shut: 10/69). travel() applies a door's Open rows when it opens one on the way
  through; doorAllowed gates the player whenever a tour is off or paused.
  From 0155, the mansion's things file is "SVO2" (Panel::ThingEffect):
  scummverseExportThings, for Maniac V1 only, runs each non-door thing's
  open/close/on/off/push/pull script (its own entry or the catch-all) from
  each picture, arriving as the probes do (startScene, scripts stopped, kid
  3 alone), until it ends; putState records what a script sets while
  `_scummverseStatesSet` points somewhere (only then). act() asks
  PanelBridge::thingEffect after the handwritten tables and the lights
  (isLight and its branch defer to an effect that only refuses), for
  non-doors only. worldExportVersion() puts the mansion one ahead
  ("maniac-v23"), so only it exports again; main.cpp, the iOS worlds UI,
  world_visit.inc and test_world_setup.py use it.
  From 0159: thingBit() is a thing's picture as its game counts (the stage's,
  else `_pictures`, else the things file's); setPicture and effectOf keep
  it in `_pictures` for one the stage has no second picture for; pictureOf
  reads the stage only for one it has; reachDoor applies a door's Open rows
  when it opens it.
  From 0161 the records also cover read, pick up and fix (not use or
  unlock: those want a second thing), and bit 1 of the after byte says the
  kid took it (ThingEffect::taken; values past 3 are a bad effect).
  effectOf carries a thing taken (carry, then picture 1) and says its line;
  plainAnswer leaves to the plain rules a read, pick up or fix that says
  nothing and changes nothing, and a take from picture 1 (the mansion's
  picture without it). useItem reads a carried thing by its record (from 1,
  else 0). The mansion's marker is now maniac-v24 (worldExportVersion: the
  mansion 2 ahead; tools/test_world_setup.py reads the lead from the header).
  From 0162 not fix (the mansion's wants a second thing: "with"); marker
  maniac-v25. A take is the plain rules' too where the stage has no picture
  without the thing (one inside a thing shut when exported: the stage has
  no parents), and useItem loads the carried thing's game's things file
  (loadThings, as enter does) if it was not entered since the start.
  From 0168 the mansion's things file is "SVO3": after the effects, each
  thing inside another (its game's parent and parent state, as a picture;
  Panel::ThingParent, PanelBridge::thingParent). The mansion's export
  draws such a thing's pictures with each it is in opened (put back after;
  the fill filter looks round it at that render). insideShut: not a thing
  while any it is in shows another picture; layInside (after enter's
  placing and after every showPicture) draws, from the outside in, each
  thing something is inside and each inside one not shut in, so a shut
  one covers what is in it and what was taken stays gone when it opens.
  StageBridge::looksAs tells whether the scene where an object is looks
  as one of its pictures. Marker maniac-v26.
  From 0169 layInside draws as the original's drawRoomObjects: the family
  (things inside others and what holds them) and every object overlapping
  it, from the last stage index to the first (the first on top), one
  inside one shut left out; nothing in a room without parents. A door
  inside one shut is no door for doorAllowed, doorOpens, a tap's walk and
  the wanderers' arrivals. The things pass marks away a V1-2 thing whose
  state has the untouchable bit (as findObject). The mansion's old things
  file is emptied before its marker. Marker maniac-v27.
- Two things (0170): with a panel under the scene (twoThings: not over the
  scene, a coin or the distaff), Give and Use on a thing carried, and
  Unlock and Fix on one here, hold the first (_holding, its verb kept lit,
  the sentence "<verb> <it> with/to"); the second, carried or here,
  completes it (pairWith: walked to the one here, if any, then act ->
  pairUp; _pairing carries the other to the arrival). Another verb or a
  tap on the floor lets go. pairUp answers by the plain rules where
  pairOwn finds nothing.
  From 0171 the mansion's things file is "SVO4": effects have a second
  (u16 with: 0 none, 0xFFFF any other) and after bits 2-3 (the first or
  second used up); an other's picture 2 is a thing the kid has then. The
  export runs, from each place as arrived (its state kept and put back
  between runs, re-entered if a script leaves), Use on every thing with a
  Use entry with each that can be carried (and the carried ones' own Use
  with every thing), Unlock and Fix on every thing with one, the carried
  ones owned by the kid; per first, the most common answer is kept once
  (with 0xFFFF) and only seconds answered otherwise are listed; answers
  that leave the place are not. pairOwn looks up the one here's script
  first (as the mansion's own sentences run: "Use X in Y" answers by Y's),
  then the first's (PanelBridge::pairEffect: that second's own, else the
  usual); it says the line, sets the one here's picture after and the
  others, carries what is had, and drops what is used up. Marker maniac-v28.
  From 0172 each pair run sets the first's picture before it runs (from 0
  and 1 for one here; a carried first is put in the kid's inventory, as
  taken, and looked up from 0); a run that starts a cut-scene or takes the
  kid away is not recorded, nor the lab suit's ending; the usual answer
  uses nothing up and gives nothing. pairOwn looks up only the picture the
  thing is in, lets the usual answer use nothing up, and passes a usual
  one that says and changes nothing on (to the plain rules). enter() lets
  go of a half made sentence. Marker maniac-v29.
  From 0173, holding Give with a thing carried, someone tapped (personAt:
  the front-most drawn under the tap) is given it: giveTo walks up beside
  them (Pair::person), act() on arrival with target -1, pairUp has them
  answer "No, thanks." (sayAs): no game's records say what people take.
- Followers (0147): the chat sends its place's token and 64 or 96 plus
  the talk ID (kTalkVisitor + slot: 94..119 along, 126..151 stay), taken
  first by `request` (before the character screen's range, which tokens
  can fall in) into chatCommand. `_followers` (keys) follow `_leader`
  (the one played; another played lets them go); followStep walks a far
  one to beside the one played every 20 ticks (not while chatting; stroll
  skips them); `enter` calls bringFollowers (WanderBridge::send to the
  place, addPerson if not shown, placed beside). talkScene tells the chat
  who follows by slot bits through `travel`; the iPhone runtime's
  follows/canFollow read those bits while scummverseSandboxActive.
  ConfMan scummverse_sandbox_followers: "leader:key,key".
- Custom characters (0139): drawn by `tools/custom_characters.py` (plain
  Python, no images read; `--preview DIR` writes PNGs) into
  `common/scummverse_custom_cast.inc` (generated, committed): each an SVC1
  file carried in the binary (kWorldCustomArt: costume, bytes, scene rows of
  a person per art row) under the pseudo-game kWorldCustomLooks (1002, as
  kWorldManiacLooks and kWorldZakLooks), named and voiced by
  kWorldCustomCast in the catalog. The sandbox's scan marks them installed;
  readCharacter gives their carried bytes where others read
  `<game>-c<costume>.svc`; addPerson draws them a fixed part of the place's
  lead (personPerRow) in square pixels (from 0142). castOffer adds a last
  box, slot 2 + worldGameCount(), "Custom characters", its face the first's;
  castHome is the player's place and castChoose plays them there, where the
  one before stood. They are not wanderers and not in Maniac's own engine.
  One may carry something lit (0175): poses 4..7 (World::GuestKind: lighting
  up, played backwards to put it out; standing, walking, talking lit) and
  mask 2 (light added to what is behind) and 3 (drawn in the dark). The
  stage's light(actor, on, played) shows the lighting-up frames while it
  stands, then the lit poses; the sandbox's L key (lightKey) toggles it for
  the one played, kept through places by _litKey while the same one plays.
- `engines/scummverse/sandbox.cpp`: the screen is the device's own pixels
  held sideways (at most 1440 rows; 1280x720 where the backend reports fewer
  than 720; `scummverse_screen` overrides), in the stage's own 32-bit format
  or the richest the backend offers (converted with crossBlit). It starts
  where the player was (`scummverse-sandbox.state` in the saves, written at
  each room, every half minute, on leaving and after each verb; "SVS2" adds
  the objects shown in another picture and the things carried, "SVS1" is
  still read; `scummverse_place` wins),
  else in `scummverse_place` or the first named
  place installed, playing that game's lead (kWorldLeads) in every game. A
  tap walks there (with the game's panel: a verb chosen first is used on the
  thing tapped once there, see the panel above); a tap on a door (a room object with a WorldLink from the
  generated door maps; switched doors only while shown) walks to its walk-to
  point (else to the tap: screen-edge exits) and, once there (within 12
  pixels of its point or of the tap), goes through to its room, arriving at
  the named object or the door back; a door without a walk-to point (the
  later games keep it in scripts) is reached at the bottom middle of its
  rectangle, as in Maniac's other worlds; on maps a tap goes at once (floor
  plans are walked). With no door to arrive at, the
  player starts in the group of boxes with the most doors. Everyone is out
  (WanderBridge, as Maniac's other-world wanderers; each engine builds it
  afresh when it starts: every installed place but maps, the games' doors,
  every installed character but the one played, each game an equal share,
  four at most drifting into the player's place, small ones aside): a place
  shows everyone there, without a limit; those the wanderers bring in while
  the player watches come through a door and walk on; those there stroll now
  and then. Its Worlds menu offers each installed game's first named place
  (kWorldSandboxGameRequest + game) and Back to Maniac Mansion.
  `scummverse_selftest` (walk, all, back, doors, wander) checks without
  anyone at the screen; `scummverse_wanderers=false` shows each place's own
  people instead.
- Detection: a folder holding `.svw` files is the sandbox (AdvancedDetector
  fallback); no game file names its own.
- Opening it: the Worlds menu's New engine (preview) asks Maniac
  (kWorldSandboxRequest) to save to the temporary slot and chain the
  sandbox target (`scummverse-sandbox`, path the worlds cache) then itself at
  that slot, as Day of the Tentacle's Maniac Mansion easter egg does; the
  sandbox's Worlds menu (shown while scummverseSandboxActive) has Back to
  Maniac Mansion (kWorldSandboxRequest + 1). Maniac saves at once and
  refuses (said by the player's character) without another game's places,
  in a WiFi game, on the tour, or when the save fails. base/main.cpp
  continues along such chains (also when the chained sandbox cannot start),
  gives Maniac its own settings back (and the slot), and gives the sandbox
  the phone's touch and orientation settings.

Proposed (not built): editions as adapters. The sandbox only reads the cache,
so any edition its own SCUMM engine can export is interchangeable: Maniac
Mansion DOS V1 or V2 (enhanced), Zak, Fate of Atlantis DOS or FM Towns, and
so on. An adapter names an edition (its detection entry), exports its scenes
and characters under the game's id with the edition's own pixel shape,
lead height, cast and door map, and the player picks which edition of a game
the sandbox uses. Maniac Mansion and Zak would then be exported like the other
ten games, everyone equal.
