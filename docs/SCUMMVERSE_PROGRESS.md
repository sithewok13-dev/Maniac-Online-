# Current development handoff — Purple Meteor

## Scope and baseline

Active milestone: Phase 1; latest patch 0196 (local WiFi play in the other worlds; 0195 the mansion's main power in the new engine: the circuit breakers off, the house dark as its own scripts leave it; 0194 the new engine's last doors: Loom's dragon's lair left by its door, the tour through every door; 0193 every other-world door walkable in Maniac's engine; 0192 the mansion's and Zak's own people among the wanderers; 0191 Fate of Atlantis's labyrinth, rings and travel screens walkable; 0190 Monkey Island 2's jungle and tunnels; 0189 Loom's dark rooms' holes filled; 0187 and 0188: Sam & Max's copy protection answered, its early saves reloading; 0186 Story mode and Explore mode kept apart, Monkey Island 2's copy protection answered; 0185 imported Zak's story; 0184 Maniac's own story, going on at the next start, Save now).
Working branch: claude/gameplay-fixes (from codex/scummverse-c64-baseline fde0674);
PRs target codex/scummverse-c64-baseline. Do not modify main or the Codex branch.
claude/scummverse-dev holds the same commits and is superseded.
Apple CI works since the repository became public: iOS run 38789360948 built the
0039 IPA. Earlier "blocked before steps" notes below are historical.
Delivered for the 2026-10-16/17 requests: NPC transport, chat overhaul and split
screen, local WiFi first increment, bus/tram boarding waits, other-world scenes
(0057) and their characters (0058), ten games (0060), empty rider chairs (0061)
and whole-game worlds with doors and 263 characters (0062). iPhone acceptance
remains open for all.
Previous delivered baseline: patch 0022, project commit
25197b5190fc441d68a503726faacb12de9693ba. User reports gameplay defects against
this lineage. Existing original-data tests validate the sandbox's own mappings;
they do not establish source-game authenticity or real multiplayer correctness.

## Audited defects / next queue

1. Portrait cropping: extraction chose a top square based on body width. Replaced
   with full visible sprite bounds fitted into a padded square. This deliberately
   shows whole character portraits until explicit source face metadata exists.
2. Navigation: Peru carving and Seattle forest now preserve audited box restrictions.
   Other imported rooms still clear box flags. Original
   entry scripts are suppressed. Restore audited scene restrictions through an
   edition adapter, with safe spawn/exit tests; do not merely remove the loop and
   assume rooms whose setup never ran will work. Peru walking actors are now excluded from aerial boxes; bird traversal still
   needs an explicit capability interaction.
3. Room identity: physical Zak resources are reused by different logical rooms.
   Catalog entries map resource files, omitting script-controlled object states,
   scroll regions and costume variants. Audit Mexico, Mars, Peru and Egypt from
   original logical scene setup before correcting room connections or scale.
4. Scaling: patch 0027 uses original 10:46 distant reference proportions in
   pyramid/temple exteriors while preserving visitor identities. Other imported
   costumes still use 6:5 normalization; depth-dependent perspective remains open. Investigate V1 costume variants, not assumptions
   about later SCUMM depth scaling. No arbitrary room-scale constants.
5. Portrait phone UI: current half-window rendering and native panel positioning
   need real rotation, safe-area, keyboard and input-coordinate validation.
6. Transport: patches 0035/0036 enforce companion presence and six local aircraft
   seats. Reservations survive switching and saves; late boarding respects capacity.
   Single active flight remains; no authoritative server or network multiplayer.
   Physical iPhone verification and multiple simultaneous flights remain open.
7. Chat/AI: platform-owned runtime, limited context, no durable messaging contract.
   Preserve the prior Metal buffer ownership crash fix and model integrity checks.
8. Missing NPCs: The King (0045), Guru and Nepal guard (0050) restored from
   original costumes and entry scripts. Sentry/devotee and Guru script remain.

## Roadmap and limits

Phase 1 existing bugs → portable module contracts → game-pack acceptance test →
real authoritative multiplayer/persistence → bounded AI memory/providers →
protected expansions → crafting and validated adventures → external Curator →
atomic discovery history → secure optional testnet ownership → economy prototype
and desktop adapters. Complete vertical slices; do not start all systems together.
Canonical assets remain protected. Player content uses approved physical entrances.
Most objects are ordinary inventory items. No pay-to-win or speculative token work.

## Latest scene repair

Patch 0025 replaces the Mt. Rainier scenery route with original loose-dirt object
267 (sandbox 737), enables its original open artwork, and removes duplicated
Seattle object handlers. Shared connection metadata governs the route. See
SCUMMVERSE_SCENE_AUDIT.md for verified source evidence and remaining limitations.

Patch 0026 adds audited navigation policies for Peru and Seattle, including old
save-state recovery. The full original scene/scale pipeline is not yet restored.

Patch 0028 makes actor picking in distant scenes use renderer top/bottom bounds
instead of the original fixed 80-pixel vertical column. Other scenes retain
legacy picking; current player remains excluded. Horizontal picking still uses
upstream eight-pixel graphics strips, not per-pixel silhouette tests.

## Resolved intermittent regression (patch 0029)

The walkbox failure was in gallery rendering, not navigation: an offscreen
actor's walkbox was looked up in the currently displayed room by
Actor::prepareDrawActorCostume. A cave actor in box 7 and a three-box jungle
reproduce it directly. Expansion seed 15 reproduces it in the London gallery.
Portrait preparation now skips room-mask lookup; real scene rendering retains it.

Expansion probes now accept --seed (default 0) for repeatability. Seed 4 also
exposed a test assumption: switching to an NPC already aboard a bus correctly
blocks immediate airport travel. The test now completes that bus ride first;
separate boarding/takeover checks remain intact.

## Continuation

Read AGENTS.md and SCUMMVERSE_ARCHITECTURE.md. Patch 0024 resolves the renderer
strip assertion; full expansion tests now pass in null and ASan. The next
substantive content slice is a logical
Zak scene identity/setup audit with private reference comparisons and one faithful
scene proving geometry, scale and transitions. Existing private descumm output
under build/zak-analysis can inform analysis; never publish those scripts/assets.
Record verification evidence in SCUMMVERSE_TEST_STATUS.md. No automatic claim of
complete Mars, multiplayer support, device acceptance or future background work.

## Active mobile layout repair (patch 0030)

Portrait chat previously moved upward for the keyboard while the renderer and
buttons stayed at half height. A portable point-based layout now reserves a
44-point toolbar between the game and chat, shrinking the game when typing needs
space. Rendering retains original aspect fitting and uses the resulting rectangle
for mouse conversion. UIKit sends bottom occlusion through the existing event
queue; no cross-thread UIKit reads or AI-runtime layout dependency. Safe-area
layout now assigns the new host frame before placing controls. Portrait toolbar
and chat gestures do not become scene clicks.

Portable layout cases pass with sanitizers. Apple CI compilation and actual
rotation/keyboard/device acceptance remain separate verification stages. Next:
verify Apple build, then audit plane seating/manifest visibility using original
costume data. No claim of networked transportation or complete portrait acceptance.

## Bus visibility repair (patch 0031)

A deterministic takeover test reproduced a passenger briefly appearing outside
an already-moving bus: scene entry/putActor showed the selected actor again,
while transport only hid them on the next tick. Manifest-owned visibility is now
restored immediately after actor switching and save loading, using the same rule
as normal bus updates. Two-passenger takeover/save/load/arrival checks pass under
ASan: both hidden in transit and both visible in the airport. This addresses a
local rendering/state path, not authoritative network synchronization.

Apple build blocker: commit 04f50136 triggered run 38651455882; its IPA job failed
before any steps ran and no log exists (log endpoint returns BlobNotFound).
Native GitHub jobs also failed before steps. Cause is not established from the
available connector data. Local native/ASan testing remains available; no new
installable Apple artifact or device acceptance is claimed. Resume Apple CI once
runner execution is available; do not spend money to unblock it without approval.

## Independent traveller records (patch 0032)

Flight auditing exposed that all actors beyond the original seven shared slot
zero for bookings, mansion return points, arrival origin and party history.
A regression reproduced Annie overwriting Zak's Seattle booking with Miami.
Expanded actors now own six separate saved fields (399 schema marker; 400..501
records), with legacy original-seven indices preserved. Existing save container
size is unchanged. Migration assigns the ambiguous old shared record only to the
active expanded actor; its historical owner cannot be recovered. Other expanded
actors start with empty records. Migration is idempotent.

Plane seating audit: original DOS V1 resource 11, seat object 255 uses position
(63,52), elevation byte 252 (signed -4) and facing command 249; it does not select
a bespoke sitting animation. Only one interactive seat is defined. Do not assign
that same spot to the whole cast or claim group seating finished. Next: inspect
original chair foreground/occlusion and empty-chair options, then implement and
visually verify a seat-capacity policy using original art. Private extraction
stays in build/zak-analysis, never in the repository.

Latest Apple run checked: 38651860666 also failed before any job steps. Apple
compilation remains blocked; no new IPA or device validation is claimed.

The return-trip test also reproduced scene-switch contamination: selecting an
actor already at the airport while viewing another actor in the mansion recorded
the old viewport room as the new actor's departure. Return records now update
only when the departing actor actually occupies the current room. Behavioural
tests exercise separate rooms for Annie and Zak, not just distinct key indices.

## Joining an existing local flight (patch 0033)

Characters boarding from the same origin for the active destination can now join
that flight, including their companions. Route, original owner and prior manifest
are retained. Wrong origins/destinations leave the existing flight and rejected
booking unchanged. Save/load and Arrive preserve the joined party. Arrival history
excludes the currently controlled character from its own companion mask. Existing
single-flight storage remains; this is local character travel, not networking.

Next: NPC booking/boarding consistency and original-art seating/occlusion preview.

## NPC flight bookings (patch 0034)

NPC roaming now respects a valid saved computer booking after control switches
away. A matching active flight receives the NPC in its manifest/cabin rather than
having them teleport directly to the destination. Boarding consumes the booking;
random travel remains the fallback for unbooked NPCs. Initial party selection also
prefers saved bookings over stale autonomous choices. A stale-choice regression
reproduced "NPC ignored selected booking" before the fix.

Original-seat preview remains research only: actor placement/facing/elevation
alone has not yet established correct seated rendering. Do not ship standing
actors through chairs as a completed seating feature. Group seating, native iOS
acceptance and real network multiplayer remain outstanding.

## Latest continuation checkpoint

Patches 0033 and 0034 are published as separate commits. Local native/ASan flight
join checks, full expansion seed 15, patch-prefix checks through 0034 and startup
checks pass. Apple run 38664283970 for 0034 failed before steps (no log available),
so there is still no newly verified IPA.

Private seat preview now checks successful scene/actor setup and renders three
frames. Zak is actor 24, costume 34, facing 90, elevation -4, original seat position
63,52 and walkbox 4. It still appears standing through the chair. Original room
11 has box 4 mask 3 and initial flag 128; original seat script sets flag 160.
Next concrete investigation: compare original-interpreter seat rendering and
foreground object 263/state/mask initialization, then normalize costume rendering
only if that comparison proves a mismatch. Do not replace original chair graphics
or stack the whole party in the one defined interactive seat. The preview code
and screenshots are private build artifacts, not shipped functionality.

## Companion presence and vehicle ownership (patch 0035)

Reproduced companions being recalled from another room during an ordinary update,
including a hidden bus passenger. Following now carries an actor only when they
shared the leader's actual departure scene. Bus manifests own their passengers
until arrival; aircraft and bus boarding require presence at the departure room.
Absent companions keep their relationship but are not teleported or added to the
arrival party. Reuniting in the same scene resumes following.

The focused regression covers a present companion, an absent companion and a
hidden bus rider, including save/load, plane arrival, normal transitions and bus
boarding. The older companion probe used retired airport command 20; it now uses
the current command 40 rather than silently testing a removed interface.

Seating research: a private test-only launcher now permits a Zak source-interpreter
reference without changing the shipped Maniac-only startup. Both reference and
sandbox previews are available under build/seat-*. Original script 5 also applies
costume frames 11 and 13; the earlier position-only preview omitted these. A visual
match and multi-seat capacity policy have NOT been established. Private extracted
scripts/images are not published. Continue this comparison before claiming seating.

## Reproducible original-interpreter reference fixture

`python3 tools/test_source_reference.py game-data/zak-dos` now builds an isolated
reference launcher and executes Zak's own engine path with the audited DOS V1
index. It checks plane room 11, its seven walkboxes, original costume 1 and the
seat's position/elevation/facing after rendering. It runs with the sandbox setting
both off and on and verifies that Zak never enables the Maniac sandbox. A private
launcher is no longer needed for this fixture. No source art or scripts are shipped.

This is an audit tool, not a game-pack implementation or proof that sandbox seating
matches the original. The fixture stops original cinematics and arranges seat state;
it does not test the entire original boarding puzzle. The application still starts
only its supported Maniac sandbox. Reference launcher changes are compiled solely
into temporary copies of the archives.

Current head before this tooling commit: dc427cc3efca5a720323245b50d00cc7c95c3b8e
(companion presence). Full expansion seed 15 also passed for that fix. Next: compare
original/sandbox costume and chair-mask rendering with this reproducible baseline;
retain original-art and capacity requirements. Native iOS build infrastructure is
still unverified since the previous pre-step Actions failures; no new IPA claimed.

Reference-tool validation: native/ASan pass; normal companion probe and 11 startup
cases also pass after the runner change. Apple run 38724181478 for 0035 failed
before any job steps (job 116385857974). Cause remains undiagnosed; do not mistake
this for a compiler failure or spend money/reconfigure billing without approval.

## Patch 0036 — reserved airplane chairs (2026-10-15)

Implemented a portable, atomic seat allocator and a separate DOS V1 cabin adapter.
New flights use six original chairs. Joining retains reservations; rejected parties
keep their booking and location. NPCs wait when that flight is full. Passengers start
seated, can walk into the aisle, and Use the original seat hotspot to return to their
reserved chair. Arrive remains immediate and flights have no timer or takeoff scene.
Reservations and seated/standing state survive save/load and actor selection.
Legacy flights with more than six actors remain intact in the aisle and can arrive.

Original source rendering showed two distinct causes: visitors were enlarged 6:5,
and only the original player's chair had a foreground mask. Imported seated sprites
now render at source size; the adapter extends that original mask to the matching
chairs without shipping artwork. Native Maniac bodies use a two-pixel chair-anchor
alignment. Walking still uses original geometry; transport poses do not unlock boxes.
All 21 available costumes were rendered in isolation and visually inspected in the
native build. This is native visual review, not iPhone or multiplayer acceptance.

Validation: portable allocator/mask contracts under ASan/UBSan; native and ASan
engine builds; seating and joined-flight probes; native companion-presence, flights,
full expansion seed 15 and 11 startup cases. Expanded seating tests cover standing
save/load and pre-seating-save migration, including seven-person legacy flights.
See TEST_STATUS for reconstruction and final publication verification.

Parent commit: 3a93ac9e698e773ac5db80b27a21280bb106c7ee. Patch distribution remains
on codex/scummverse-c64-baseline / draft PR 1. No proprietary images, game data or
extracted scripts are committed. No new IPA or successful Apple build claimed.

Publication verified: fd6082aa130be8a87f390a3e4b007441004e2352 on the existing
branch/PR. Native Actions runs 38750078945 and 38750070288 failed before steps;
iOS run 38750070011 job 116473836890 also failed with an empty steps list. Local
native/ASan results above remain valid. CI cause is undiagnosed, not a demonstrated
compiler error; do not claim an IPA or alter paid infrastructure. Resume from the
Mexico/Mars logical-scene audit, or investigate the pre-step CI failure read-only.

## Patch 0037 — Mexico chamber and logical temple audit

Parent: 57734176df617255ef5eab24949a808427fb60ac. Added room-scoped source object
state rules for chamber 89 / original 130, navigation restrictions and old-save
repair. Separated imported background/object color mapping from native actor colors
using ScummVM's existing Zak tables. The reference-driven chamber test compares all
21 object states and the actor-free background pixel-for-pixel, plus load repair,
exit behavior and isolation from another chamber using the same source resource.

Original-interpreter audit now covers all twelve temple scenes 156–167. Their
source resource is 53; current sandbox corridor 88 incorrectly uses Mars resource
36. Tools produce private snapshots and validate the reachable doorway graph.
The corridor replacement and Mars reconstruction are NOT complete. Next vertical
slice: stable logical scene registry/IDs, entry placements, source object layout,
links, and old room-88 save migration; avoid a shared mutable pseudo-room solution.
No proprietary assets, extracted scripts, generated reference images or runtime
snapshots are committed. Apple/device and multiplayer acceptance remain separate.

0037 validation: native/ASan chamber and temple-reference tests pass; full expansion
seed 15, seating and eleven startup cases pass. All 37 patch prefixes reconstruct
cleanly. See TEST_STATUS for precise coverage and remaining device/CI limits.


## Patch 0038 — distinct Mexico temple rooms

Parent: b8ed04c38aad4f611f1a0f1cdbd2189383e2e874. Room 88 now represents original
logical 156/resource 53. Appended stable rooms 99–109 represent logical 157–167;
other room IDs remain unchanged. Restored original object layouts, signed walking
anchors, camera limits, box flags, 52 internal doorway routes, three exterior
entrances and the crystal-chamber return to logical 166. NPC arrivals use source
anchors without changing the displayed room. Internal room travel does not reuse
UI teleporter command numbers. Shared room-capacity predicates replace stale bounds.

Saved variable 527 marks migration inside the existing 800-variable container.
Actual patch-0037 room-88 save (99-room engine) loads into the new 110-room engine;
two occupants are retained and old geometry is rebuilt. New variants save/load and
actor switching retain distinct locations. No proprietary fixture is committed.

Native/ASan temple comparisons pass for all 12 layouts, states, walking anchors,
box flags and leftmost actor-free viewport; all 52 doorway routes pass. Native
expansion seed 15 exercises all 54 imported rooms and selectable walking exits.
Visual fixture review exposed missing object-state/camera refresh in direct drawing
helpers; chamber and temple reference helpers now perform both before capture.
See TEST_STATUS for remaining validation. Original temple lighting/torch puzzles
remain bypassed in this exploration adapter; full Zak puzzle support is not claimed.

Continuation: build/temple-base.index is the pre-0038 alternate index;
patches/0038-mexico-logical-temple.patch is the distribution change. Private
build/legacy-temple.s12 was captured using the 0037 ASan build before rebuilding it.
The capture recipe is tools/test_temple_legacy.py: use a matching 0037 engine AND
compiled build, then test the resulting private save with the new test_temple.py
--legacy-save option. Never publish saves, original data, snapshots or descumm output.


## Mars interior graph — patch 0039

Twenty interior scenes now use independently audited original logical setup.
Seventeen rooms are appended (110–126); existing corridor 82, Great Chamber 83
and machine room 93 keep their IDs. Sixty interior exits follow original handlers,
with arrival-object anchors or explicit original arrival coordinates. Exterior 79's
Great Chamber entrance now reaches 83 rather than the three-door corridor 82.

The shared `ZakSceneSetup` descriptor replaces the temple-only descriptor and owns
object counts/layout/state, box flags, camera minimum/maximum and source palette.
Mars uses the same import, navigation and restoration code as Mexico. The machine
platform uses the right half of resource 35; the projection room uses the left.
Older saves with a machine-room actor in the unused half are projected into the
correct visible scene during restoration. Existing room capacity grows to 127.
Before adding IDs 128 or higher, account for upstream V1 pseudo-room mapping;
do not blindly append beyond that boundary.

Reference tests execute original entries with an explicit exploration preset:
massive doors and rock tunnels open, source machine defaults, lighting enabled.
They do not reproduce the original puzzle sequence. Full Mars support remains
unfinished: hostel/airlock variants, tram, pyramid branches, NPC behavior and
original special interactions still need source-based repair. No new iPhone build
or real multiplayer acceptance is claimed. Private source evidence stays in build/.


## Patch 0040 — reliable shared conversation

Root causes found by reading the runtime, not by device reproduction:
1. `sendTalk` refused every message without a loaded model, while Classic is
   the default, so Talk never sent on a fresh install.
2. It also refused while an ambient encounter line generated (up to 5 s) and
   while earlier replies were pending (up to 30 s per speaker).
3. A room/player change during an active talk bumped the epoch unconditionally;
   if a model was loading, the finished load was discarded and never retried.
4. iOS smart quotes produced UTF-8 that V1 speech bubbles cannot render.

`common/scummverse_conversation.h` (contract v1) owns the ordered transcript,
stable line IDs, a three-message outbox, rotating two-speaker scheduling,
departure cancellation and model-context selection. No threads, model or UI.
The llama runtime is one reply provider; classic authored lines are the
fallback for no model, filtered output and timeouts, labelled in the UI.
Messages wait in the outbox and join the transcript only after earlier replies,
so answers stay causal. A departing speaker's reply is cancelled; the other
scheduled speaker still answers. Talk pre-empts an ambient line immediately.
The talk bar renders one attributed, colour-coded transcript, keeps Send enabled
while replies are pending, follows new lines only when scrolled to the end,
disables smart quotes and uses a single header row in portrait while typing.

Not done here: conversation persistence across rooms/saves, durable memory,
network delivery, and device keyboard/rotation acceptance.

## Patch 0041 — aspect-fit portrait layout (contract v2)

Portrait reserved the upper half for the game but the picture is width-limited:
on a 390x797-point host the 320x200 scene needs 243.75 points of a 354.5-point
region, leaving letterbox bands between scene and toolbar. Layout v2 accepts the
host width and the renderer's displayed aspect (published as an integer x1000 so
UIKit and the renderer compute identical rectangles) and caps the game region at
the aspect-fit height. Freed space goes to chat (366 -> 475 points there).
Height-limited cases (keyboard visible) are unchanged. "Upper half" cannot be
reached at full width without cropping; the scene stays at maximum width.
Not device-verified: real safe areas, rotation and touch conversion.

## Patch 0042 — airport VoiceOver labels; code audit notes

Row buttons on the destination/teleport panel always announced the first page
(Maniac Mansion..Miami). Names now come from one list shared with drawing,
are relabelled per page, and rows past the end are hidden.

Code audit (2026-10-16, from source, not device): only one flight can exist
(vars 724-727); NPCs without a matching flight are moved to their destination
directly, no plane (roaming.inc ~338). The airport is reached by an edge test
needing exactly x==0 in room 1. The destination panel imitates the Zak screen
with drawn pixel text, not original art. No Elvis-related character, Guru or
Nepal guards exist in code. Peru boxes 6-8 are invisible to walkers; no bird
traversal. Zaire, Mexico and Peru "temple" rooms all use resource 39 (the
Mexico exterior per audit) with no logical setup: verify with original data.
Edge case: residents 8/17-19 are set up under var 764 but gated by var 763.

## Original data needed for scene work (not in the repository)

Place privately in ignored folders; never commit or upload publicly:
- `game-data/mm-dos/`: every `.LFL` from English Maniac Mansion DOS **V1**
  (including `00.LFL`; not the enhanced V2, C64, NES or demo releases).
- `game-data/zak-dos/`: every `.LFL` from English Zak McKracken DOS **V1**
  (index MD5 7020931d5a2be0a49d68e7a1882363e4). Each imported room is
  checked against a pinned per-file MD5; mismatches are rejected.
Needed for: scene/logical-room audits (shared resource 39), walkboxes, scale,
NPC costumes (Guru, Nepal guards, Elvis-related character), Mars rooms, and
tools/test_expansion.py and the reference probes. Optional: device saves that
reproduce bugs, kept in ignored build/ folders.

## Patch 0043 — original airports and scene views (data-verified)

Original data was supplied for this session (English DOS V1 Maniac and Zak;
kept in ignored game-data/). The new scene authenticity audit compares every
imported room against the original interpreter. Seattle, Miami, London and
Mexico City now use the original big-airport resource with each city's
logical setup; regional airports, jungles, crystal chamber 129, village 150,
hostel 180 and Stonehenge 133 use generated original setups
(tools/gen_zak_scene_setup.py). A ZakSceneView table replaces the hard-coded
color switch. Airport gate/terminal handling resolves original object roles,
not import indices. Saves made inside a converted airport are rebuilt on load
(var 528 = scene schema). See SCUMMVERSE_SCENE_AUDIT.md for evidence.

Test runner: `python3 tools/test_all_data.py game-data/mm-dos game-data/zak-dos`
runs every data test in order. It exposed three stale probes (bus/companions
room count, roaming missing the shared prelude, Seattle exit index); all fixed.
Probe captures previously used a private absolute path and silently skipped.

## Patch 0044 — retire invented scenes; original teleport sites

Rooms 64/65 (Zaire temple/crystal chamber) and 97/98 (Peru temple/crystal
chamber) have no original counterpart. Their IDs stay allocated; no link,
pad or travel request reaches them; saved occupants move to the village (63)
or carving (96) on load (var 528 = schema 2). Jungle exits follow the first
original jungle scene. Crystal pads are the five original map sites with
original platform arrivals: Seattle 92, Mexico 89, Peru 98 (0046), Egypt 76 (newly
added) and Mars 125 (was the non-original pad in room 84). The iOS panel lists
five sites. Next scene work: Cairo (71 is a pyramid passage, not Cairo), Mars
pyramid 84, split scenes 151/181/134, Nepal guard station (resource 18).

## Patch 0045 — The King; NPC source findings

Actor 17 wears Zak costume 27, which the original names "The King" (room 10
object 240 script, Bermuda alien craft); the sandbox called it "Alien pilot".
Name, dialogue personality and docs corrected; saved names migrate on load
(var 528 = scene schema 3). The original pilot is costume 10.

Original NPC sources (private descumm, for the next NPC slice):
- Guru: costume 22, room 19 at (60,56), anim 251, script 42 approaches the
  player. The original costume draws him seated cross-legged above his dais;
  restoring that costume yields levitation with original art.
- Nepal guard: costume 26, Kathmandu street 17 at (80,11); policeman name in 17.
- Stonehenge sentry: costume 24 (logical 133); airport devotee: costume 25.
- Zaire villagers: actors 10-12 all costume 21 color 9 (identical to the shaman
  in the original too); actor 10 named "Shaman".
Adding Guru/guard needs new actor slots. Maniac scripts reference 12/15/16 and
also 8/17-19 (already repurposed); audit each reference (likely blocked
cutscenes) before allocating. Not done in this session.

## Patch 0046 — Peru carving interior; bird traversal (navigation item)

Original data shows resource 43 is Peru's carving interior (ledge 138, eye
chambers 136/137), not a Nepal sanctuary. Walkers still cannot cross the
valley: the carving gives the original refusal lines. The bird feeder is an
explicit traversal (ZakTraversal table) to the ledge at the original arrival
point; eyes, windows and valley follow the original graph. Rooms 97/98 reuse
retired IDs for the eye chambers; the Peru pad lands at 137's platform.
Not done: a playable/animated bird (original actor 6 / costume 15; actor slot
6 is Wendy in Maniac), Nepal guard station (resource 18).

## Patches 0047–0049 — device report fixes (portraits, bus ghost, speech)

From the user's device screenshots (2026-10-16):
- 0047: character-gallery portraits drew Zak-side cast headless. V1 frames only
  update masked limbs, so the boot portrait decodes init, stand and talk-stop
  frames. Expansion probe compares boot portraits to later ones.
- 0048: the bus left a frozen image of the boarded player. Root cause: a full
  redraw drew hidden actors (drawActorCostume ignores `_visible`); hidden actors
  are skipped in the sandbox and riders are boarded once. Bus probe checks the
  frame after pickup.
- 0049: NPC speech split words at 28 columns and was dark text on busy scenes.
  `common/scummverse_text.h` wraps on word boundaries (tools/test_text.cpp, CI);
  sandbox speech has a solid backdrop, outline and brightened EGA colors.
Compiled and data-tested on Linux; not device-tested.

## Patch 0050 — logical scenes, original routes, Guru and Nepal guard

Logical scenes ≥128 (`zakLogicalScenes`): Stonehenge 134, Egypt pyramid
passage 135, Zaire shaman's hut 151, Mars hostel bunks 181 mount through the
saved resource mapper on their physical resource. Retired 64/65 now hold
original scenes: 64 = Kathmandu guard station (resource 18), 65 = San Francisco
phone company (resource 4); 71 is the Mars pyramid entrance (183).
Routes follow original object scripts (private descumm): Nepal street door 350
→ guard station, temple door 351 → Guru (arrival 375), yak 352 → airport
(the original $100 ride; free here); SF street → phone company → Caponian HQ;
HQ rope → Zak's apartment (link destination 54 now maps to travel 1);
Cairo → Sphinx → pyramid passage 135 / legs / Sphinx; Mars landing ↔ pyramid
entrance; hostel ↔ bunks; Zaire village ↔ hut; Stonehenge 133 ↔ 134.
Scene audit 64/75 exact, no failures (rest tolerated/unaudited).

Residents: Maniac actors 12 (Dead Cousin Ted), 15 (Meteor Police, scripts
42/43/124) and 16 (Meteor) are all referenced. Actor 15 is borrowed only while
the player views a resident scene and only when the mansion is not using it
(room 0); var 768 = borrowing scene, 769 = Maniac costume to restore.
Costumes 42/43 = Zak 26/22 (`_numCostumes` 44, static, not saved). Nepal guard
at the temple door (80,11 anim 250), Guru seated before the statue (60,56 anim
251), both with original colors; chat addresses them (authored personalities
and offline lines in `zakResidents`). Expansion probe: each resident present,
survives save/load, actor returned on leaving, never taken from the mansion.
Not done: Guru's original approach script 42, Stonehenge sentry (costume 24),
airport devotee (25), SF shops 5/6/7, apartment room 2, pyramid mazes
(resource 23), Mars pyramid 84/188.

## Patch 0051 — NPCs fly on their own

NPC travellers no longer teleport when their boarding timer ends. They board
the shared cabin: join the flight on their route at their gate, or start one
when the cabin is free (var 796 marks an NPC-started flight). A flight whose
riders do not include the controlled actor lands on its own after
kNpcFlightTime (1800 timer units, about 30 s; var 795 is the saved clock);
riders appear at the destination airport. The player is never blocked: boarding
a different route lands an NPC-started flight first. While the player flies,
NPCs on other routes wait at their gate, and the player's flight lands only on
Arrive. NPCs already called and rode the bus on their own (street stop
passage); the bus probe now proves it without the player.
Still a single cabin: concurrent flights remain future work.

## Patch 0052 — streamlined chat

User report: chat was hard to use (Talk → tap a character in the scene → "+"
→ tap again; composer disabled until someone was picked). Now:
- People row: a chip for every character here plus "Everyone"; tap to add or
  remove (runtime `toggleTalk`; removing the last person ends the chat).
- Composer always ready: with nobody chosen, a message goes to everyone nearby
  (runtime `sendNearby`: one person directly, several as a group that follows
  arrivals/departures). Contextual placeholder names the recipients.
- Header is chips + Follow (single person) + close; landscape adds Log/Hide.
  Tapping a character in the scene still works (armPick path unchanged).
Runtime behavior tested (tools/test_scene_talk.cpp, ASan/UBSan, TSan suite).
The UIKit layer is compiled only by Apple CI; not device-tested.

## Patch 0053 — local WiFi play (first increment)

Worlds → "Play together on WiFi": one device hosts (TCP port 47913, shows its
IPv4 addresses), others join by address. Same build and own game files on
each device; each person plays a different cast member. The host validates
protocol/content version, capacity (4 joiners) and character uniqueness, and
relays avatars (room/x/y, ~10/s) and speech. On each device a remote player's
character is an ordinary actor driven by their updates: no NPC roaming,
companion, passenger or AI-chat role while controlled; switching to it is
refused; leaving or disconnecting gives it back. Player chat: lines the
player says are broadcast; with no NPCs nearby the composer still speaks to
players. Info.plist has NSLocalNetworkUsageDescription.
Verified: codec/session tests over loopback (ASan/UBSan, TSan, CI) and an
engine probe where the real engine hosts and a second in-process session
joins. NOT verified: two devices, two engine processes, iPhone networking or
the local-network permission prompt. Not shared: world/NPC state, flights,
bus, inventory, saves — each device still simulates its own world.
Next for multiplayer: two-process test, discovery (Bonjour), shared flights
and an authoritative world model.

## Patch 0054 — bounded text outline (memory-safety fix for 0049)

ASan found heap overflows in `CharsetRendererPC::drawBits1`: 0049 forced the
outline shadow on all sandbox V1 text, and the outline's one-pixel offset
wrote past small surfaces (the 16-row message line, during Maniac script
prints). Upstream never outlined V1 text, so it had no bounds there. The
outline now applies only to sandbox speech on the text surface, and every
outline/glyph write is checked against the destination surface. Found by
running the probes under the ASan build; 22 probes plus the scene audit are
now ASan-clean. Speech capture unchanged. Device builds before 0054 could
corrupt heap memory when such a message printed.

## Patch 0055 — bus boarding wait; operational Mars tram

User request (2026-10-17): the bus waits several seconds for others; the Mars
tram works and waits the same way.
- Bus: boards for kBusBoarding (300 timer units, ~5 s; was 60). Riders walk
  to the door and step in; idle street characters may decide to ride; anyone
  who reaches the stop during the wait rides. Requesting a bus that just left
  says so. Scene schema 4 migrates saves made while the old bus drove.
- Tram (original object 445, button 450, script 51): runs between the landing
  site (185, sandbox 79) and the new logical scene 184 "Mars tram station"
  (same resource 27, original setup). Countdown "Tram leaving in 5 seconds."
  / "All aboard!", riders walk aboard, then a ride (kTramArrival) with riders
  hidden and travel locked; arrival at the original (13,63). The button calls
  it over empty. Mars NPCs ride and call it. Vars 797 phase, 798 riders,
  799 station/empty-call. The ride scene (resource 26, costume 20) is not
  imported: no free physical slot until the dynamic-slot work.
- Original wiring corrected: landing-site door 449 → 181 (Mars door 463);
  181 → landing site; Shuttle Bug door 452 → ship interior (81); pyramid door
  456 is at 184 (was wired from 79). 181 is the hostel entrance, 180 the bunks.
Probes: tools/test_tram.py (new), bus boarding wait + late rider, schema-4
migration. 28/28 data tests pass.

## Patch 0056 — split-screen chat (layout contract v3)

User request: while chat is open, split the screen in half. Portrait: game
on top, chat below. Landscape: chat left, game right, swappable.
`common/scummverse_layout.h` v3 `splitLayout()` (tested: 2,304 cases in
tools/test_mobile_layout.cpp) is shared by UIKit and the renderer. The talk
bar publishes inset and flags (bit 0 open, bit 1 chat on the right) through
kInputChatLayoutChanged; iOSGraphicsManager fits the picture into the game
half and shifts the draw/active rects (touches map to the moved picture).
Landscape gets a ⇄ swap button (remembered in NSUserDefaults); the button
column moves to the game half's edge. Closing chat restores full-screen
landscape; portrait closed keeps v2. Compiled only by Apple CI; not
device-tested (rotation, keyboard and touch mapping need iPhone checks).

## Patch 0057 — other worlds: scenes from the player's other SCUMM games

User request (2026-10-17): add locations and characters from Monkey Island
1/2, Loom, Indiana Jones 3/4, Day of the Tentacle and Sam & Max (user supplied
their own copies; they stay in ignored game-data/). This patch adds locations;
characters are the next slice.
- Design: the original game's own engine renders its scenes. At app start,
  `base/main.cpp` finds catalog folders in Documents (monkey, monkey2, loom,
  indy3, atlantis, tentacle, samnmax), chains each new game once in export
  mode (`scummverse_world_export`, engines/scumm/scummverse_world_export.inc)
  and then starts Maniac with its own settings restored. Export failures only
  log. The cache (Documents/worlds/*.svw: pixels, palette, walk boxes) is
  private, derived from the player's files, never committed.
- `common/scummverse_world_catalog.h`: 41 curated scenes (room numbers for
  the audited editions + descriptive names). `common/scummverse_world.*`:
  portable loader — scales to the 128-line sandbox view (area average snapped
  to the scene's own colors; point sampling for 16-color EGA art), packs
  colors into palette slots 16..255 (unused by V1 art), pads narrow scenes,
  converts walk boxes to V2 trapezoids with a routing table, builds a V1 room
  resource. Unit test tools/test_world.cpp (synthetic, CI).
- Sandbox: logical rooms 200+ (catalog order) backed by one new physical
  room 127 (`kForeignRoom`, `_numRooms` 128; static resources only, saves
  unaffected). GdiV1 draws foreign strips from the scene pixels. Walking off
  a side reaches the neighboring scene of that game when its boxes allow.
  Worlds → "Visit other worlds" (iOS) lists games (disabled until installed)
  and scenes. Saves inside a scene reload it; without the cache the player is
  moved to the airport. Chat context knows the scene names.
- Verified: 41/41 scenes export via the real binary (tools/export_worlds.py)
  and via probes; tools/test_world_visit.py visits all 41 (walks in 38, side
  exits, save/load, missing cache, home palette intact), ASan clean.
- Not done: foreground masks (actors draw in front of everything), original
  doors/objects/scripts in those scenes, characters from those games,
  device testing. Editions other than the audited ones are not exported.

## Patch 0058 — other worlds: characters from those games

Second slice of the 2026-10-17 request. 16 characters, one per scene that has
one: Stan, Guybrush and LeChuck (MI1); Guybrush (MI2); Bobbin (Loom); Indy and
Elsa (Indy3); Sophia and Indy (Indy4); Purple Tentacle, Bernard, Hoagie,
Laverne and Green Tentacle (DOTT); Sam and Max. Costume numbers for the
audited editions were picked from private contact sheets of every costume
(build/foreign, never committed).
- Export: right after a guest's scene, the original engine renders its
  costume (stand, up to 12 walk and 6 talk frames, four facings; two fills
  give exact transparency) into Documents/worlds/<gameid>-c<costume>.svc.
  `<gameid>.svx` marks a finished game; caches from 0057 lack it, so each
  installed game re-exports once to gain its characters.
- `common/scummverse_world.*`: parseSprite/fitSprite scale frames with the
  scene's own factor (nearest pixel, feet anchored) and pack colors into
  slots 224..255 (scenes now use 16..223). Lookup falls back to standing and
  to the nearest facing. Unit tests in tools/test_world.cpp.
- Sandbox: the guest borrows the resident actor 15 (same mechanism and saved
  vars 768/769 as the Guru), so walking, speech, talk chips and AI chat work
  unchanged; `Actor::drawActorCostume` hands that actor to
  `scummverseDrawGuest`, which blits the frame for its facing/state and marks
  it dirty under its own actor bit (normal background restore and depth
  order). Guests greet the player once per visit (newly written lines),
  stroll within the boxes and stop while chatting. The runtime gives them
  their names, personalities and classic lines (test_scene_talk). The iOS
  scene list names who lives where.
- Verified: real export of all 7 games (16/16 characters);
  tools/test_world_visit.py checks every guest is mounted, named, palette
  applied and drawn, plus greeting, talking and walking frames, save/load and
  returning the borrowed actor; ASan clean. Screens inspected by eye.
- Not done: foreground masks, guests' original voices/scripts, more than one
  guest per scene, device testing.

## Patch 0059 — other worlds: a fuller cast (64 characters)

User request (2026-10-17): more characters from the seven games, not just
the leads. A private scanner (build/foreign, never committed) decrypted each
game's scripts and paired actor names with costumes (105 entries, 64 high
confidence); Loom and Sam & Max have no script names, so those were matched
by eye. It also corrected 0058: Day of the Tentacle's Bernard, Laverne and
Hoagie are costumes 302, 303 and 304 (0058 used look-alike variants).
- Up to five characters per scene, 64 in all (catalog `guests[5]`), e.g. the
  SCUMM Bar's important-looking pirates and cook, the Sea Monkey crew,
  Herman, Largo, the Spitmaster, the weaver elders, the shepherd and dragon,
  Henry and Marcus, the Algiers market, Ben Franklin, George Washington, Dr.
  Fred, Sam and Max together, the carnival. Uniformed Nazi characters and the
  Hitler costume are deliberately left out.
- Engine: Maniac now allocates 30 actors; 25..29 are transient guest slots
  (Maniac's own objects start at 30, so object/actor numbering is unchanged).
  Saves still hold only the original 25 actors (loading clears the guests),
  V1 per-actor color tables are bounds-checked, and the boot-time costume
  assignment skips the guest slots. Actor 15 goes back to Zak's residents; a
  0058 save made inside a world returns it.
- Colors: scenes use slots 16..191, all characters of a scene share 192..255
  through `fitSprites` (joint RGB budget; unit-tested). Characters are
  exported right after their own scene, so they use that room's palette.
- Export marker is now versioned (`<gameid>-v2.svx`, kWorldExportVersion),
  so installed games export once more to gain the new cast.
- Chat: the roster and runtime cover actors up to 29; the runtime names guest
  slots from the catalog (test_scene_talk).
- Verified: real export 41 scenes / 64 characters; tools/test_world_visit.py
  checks every character placed, named, in the roster and drawn, plus
  greeting, talking, chatting holds still, walking frames, save/load,
  leaving, and the 0058 migration; ASan clean. Scenes inspected by eye.
- Not done: foreground masks; at most five per scene; characters do not
  interact with each other or with their scenes' objects; device testing.

## Patch 0060 — other worlds: Full Throttle, The Dig, The Curse of Monkey Island

User request (2026-10-17): add The Dig and Full Throttle (files supplied by
the user, split for upload and rejoined; FT.LA0 "Version B", DIG.LA0 and
COMI.LA0 match ScummVM's detection table), then The Curse of Monkey Island.
- Builds now enable ScummVM's `scumm_7_8` sub-engine (tools/build.py,
  tools/generate_ios.py; CI uses both). These editions are only ever run in
  export mode; Full Throttle's bike-fight (INSANE) setup is skipped there,
  so its DATA/*.rip files are not needed.
- Exporter: v7+ cameras need vertical limits (VAR_CAMERA_MIN/MAX_Y) and a
  vertical center; v7+ shadow pixels (AKOS color 13, shadow mode 1) are
  shaded background, so the two-fill capture leaves them out.
- 15 scenes (FT 5, Dig 4, Curse 6) and 16 characters: Ben, Father Torque,
  Maureen, Malcolm Corley, Adrian Ripburger and a biker; Boston Low, Maggie
  Robbins and Ludger Brink (in spacesuits on the asteroid, and on the alien
  world); Guybrush, Haggis McMutton, Lemonhead and the ghost bride. The Dig's
  names come from its scripts; Full Throttle and Curse name few actors, so
  those were matched by eye and by the costumes each scene's scripts set
  (Corley, Ripburger, Maureen and Father Torque are likely, not certain).
- The catalog is limited to 56 scenes (logical rooms 200..255; actor rooms
  are one byte). Existing scenes keep their order; tools/test_world.cpp
  checks the limit. Scenes without characters were trimmed to fit.
- Characters whose game has no walking frames for them no longer stroll.
- Verified: real export (15 scenes, 16 characters, also under ASan);
  test_world_visit visits all 56 scenes with 80 characters (ASan clean);
  Maniac startup tests pass with the larger build. Not device-tested; the
  iOS build with v7/v8 is compiled only by Apple CI.

## Patch 0061 — no painted passenger in a rider's chair

Device report: after standing up from a plane seat, a static character sat
in it. Zak's cabin art paints passengers into chairs 19, 30, 41 and 52 (only
63 and 74 are empty), so a rider assigned one of those chairs overlapped a
painted person, who showed again once the rider stood. Now every chair held
by a rider (seated, or stood up and keeping the seat) or occupied by a seated
player from another device takes chair 74's tiles in the picture, color and
mask maps (`ScummverseZakPlane::emptyChair`, applied from pristine copies on
cabin entry and whenever the held chairs change). Unheld chairs keep their
painted passengers. tools/probes/seating.inc compares the background buffer
of each chair against the empty chair, before and after standing.

## Patch 0062 — other worlds: whole games, doors and every character

User request (2026-10-17): all the characters (e.g. Sam & Max's Conroy
Bumpus, Lee-Harvey, Bruno and Trixie), and every travel-able location, so a
player can walk all over Scabb or Blood Island. Seven research agents worked
on private analysis (build/foreign, never committed): each game's door links
from its object scripts and each character's costume, room and name.
- Places are (game, room) pairs held in eight slot rooms 192..199 (saved
  variables 600..607, layout 608). Saves from 0057..0061 (rooms 200..255)
  migrate through the frozen kWorldLegacyPlaces. Any exported room can be
  visited; the 56 named places stay in the menu.
- Doors: tools/world_maps.py generates scummverse_world_maps.inc (563 rooms,
  1483 doors: door, exit, walk, map, vehicle and time-travel links; pseudo
  rooms folded into their physical room; only rooms the exporter can draw).
  A tap on a door object walks there; on arrival the player goes to the
  room the game's door leads to (map rooms travel at once). A walk that is
  stuck for 60 frames stops. A tap still pending when the player travels
  never opens a door at the new place (the probe caught one in Full
  Throttle).
- Story areas: 54 parts that the games reach only through voyages, rides
  or cutscenes (e.g. the ghost ship, Castle Brunwald, Vulture Rock) get a
  "More:" entry in the game's place menu (newly written names), so every
  exported room is reachable on foot from a menu entry (unit-tested). Menu
  place requests use kWorldPlaceRequest (above scene-bound requests); chat
  context names a story area by its entry name.
- Cast: tools/world_cast.py generates scummverse_world_cast.inc: 263
  characters (Monkey Island 32, Monkey Island 2 39, Loom 24, Last Crusade 15,
  Fate of Atlantis 28, Day of the Tentacle 36, Sam & Max 32, Full Throttle
  12, The Dig 9, Curse 36), up to five per room, with newly written
  personalities and lines. The Dig's bat creature is left out (it draws a
  few pixels). Agents corrected earlier picks (e.g. Monkey
  Island 2's Elaine is costume 10; 79 is Kate Capsize).
- Exporter: every map room and each character's costume (once, right after
  its first room); scenes are gzip "SVW2" with room objects. Full Throttle
  no longer stops in room 45 (animation steps queued sound commands that
  nothing ran; the queue is dropped while capturing). Costumes with no stand
  animation, one facing, or pictures drawn far from the actor (room
  coordinates) are searched for and centered; captures cut by the screen
  edge are re-centered; pictures not standing on the actor's feet stand on
  their own bottom center; Curse's shadow pixels (colors 0..7) are left out
  instead of drawn red; the capture no longer inherits a walk box's depth
  scale (Monkey Island's Carla was tiny). Every distinct costume of the
  cast now exports (ten were blank before, e.g. Curse's Wally, Wharf Rat,
  Elaine, King Andre and Cruff).
- kWorldExportVersion is 3, so installed games export once more.
- Verified (Linux, the user's private copies): export of all ten games, 564
  scenes and 257 character sprites in 34 s (also under ASan: clean, same
  files); tools/test_world.cpp (door maps, reachability, story areas,
  catalog, cast); tools/test_world_visit.py (also under ASan) visits all 56
  named places, mounts every story area, places every one of the 263
  characters in its own room (named, in the talk roster, drawn) and walks
  every door: 1396 lead where the map says, 71 do not (4.8%; the probe fails
  above 5%), 16 are skipped; test_talk_runtime (ASan/TSan) and the startup
  tests pass. Sprites compared by eye before and after the exporter changes.
- Known gaps: Fate of Atlantis rooms with line-segment walk paths (e.g. the
  labyrinth, rooms 50/51 and 85..88) and some doors outside the fitted walk
  boxes fail to walk through; story transitions themselves (voyages, the
  bike ride, cutscenes) are not played; scenes have no foreground masks and
  no room scripts; characters stand where placed and do not use their
  scenes' objects; seated characters have no chair; the iOS menu change is
  compiled only by Apple CI; nothing here is device-tested.

## Patch 0063 — which build is running

Device report (2026-10-17): after installing the 0062 IPA the app seemed to
be the old version. Every IPA had carried ScummVM's own version (2.9.1), so
neither the player nor a sideloading tool could tell builds apart, and a
tool may treat an equal version as already installed. CI's 0062 IPA was
built from commit 650f944 (build-info.json), so the cause on the device is
not established.
- tools/package_ipa.py stamps each IPA `<latest patch>.<CI run>` as
  CFBundleShortVersionString and CFBundleVersion, plus SCUMMVERSEBuild
  ("patch 0063, build N (commit)"), before the sideloading tool signs it;
  build-info.json records both. tools/test_package_ipa.py checks the stamp.
- The in-game menu's Connected worlds message ends with that build line and
  how many supplied games have other worlds exported for this build.
- docs/ios.md (the IPA's INSTALL.md) says how to check the build and what to
  do when an older one still opens. Compiled only by Apple CI; not
  device-tested.

## Patch 0064 — portrait play

User request (2026-10-17): play in portrait with the graphics on top and the
chat on the bottom half. The portrait layouts (contract v2, and v3's split
from 0056) existed but never showed on a phone: patch 0001 set
`orientation_games` and `orientation_menus` to landscape for every session,
so the app never rotated. Both are now `auto` (the app follows the phone).
Starting a game in portrait no longer opens ScummVM's game keyboard (rotation
already skipped it under SCUMMVERSE): the bottom of the screen is the
conversation with its own message field. In portrait the picture is
aspect-fit at the top, the button row below it, and the conversation fills
the rest (exactly half while a conversation is open, above the keyboard
while typing). tools/test_mobile_layout.cpp covers the layout contract;
rotation, the keyboard, safe areas and touch mapping in portrait are
compiled only by Apple CI and not device-tested.

## Patch 0065 — one scale for everyone in other worlds

Device report (2026-10-17, screenshots of The Dig, Monkey Island's map,
jail, Melee town and the ghost ship): Maniac characters were about twice
the size of the scenes' own characters. Scenes are shrunk to the 128-row
V1 room and their characters with them, but V1 costumes were drawn at
their own size, and nobody followed the source games' depth scaling.
- Rule: everyone is as tall as a person standing at that spot of the scene:
  the game's lead character at full scale (WorldGame::heroHeight, measured
  from the audited editions: Monkey Island 1/2 47, Loom and Last Crusade
  45, Atlantis 50, Tentacle 74, Sam & Max 70, Full Throttle 94, The Dig 63,
  Curse 268 source pixels), fitted like the scene, times the scale the game
  gives the walk box there. A Maniac teenager (72 V1 pixels: Dave, Michael,
  Jeff) maps to that height; other Maniac and Zak characters keep their
  proportions.
- Exporter: scenes are "SVW3": per box, the game's own character scale at
  its top and bottom edges (box scale or scale slot from the room's SCAL
  data; slots only scripts would set count as full size, and are reset
  between rooms). Readers keep "SVW1"/"SVW2" (full size). kWorldExportVersion
  is 4 so installed games export again. 331 of 564 rooms scale by depth
  (none in Loom and Last Crusade, whose games never scale).
- Drawing: V1 characters in other worlds are drawn by their own renderer,
  unmasked, into a screen-wide canvas with 64 rows of headroom, then scaled
  around their feet (nearest pixel); within 3% of their size they are drawn
  as before. Guests' frames are scaled by the depth scale the same way.
  Depth never goes below 10% (some far boxes scale to almost nothing).
- Verified: tools/test_world.cpp (SVW3 parse, truncation, kept boxes,
  interpolation, older files, hero heights); tools/test_world_visit.py checks
  the visitor's drawn height at all 56 named places (within 20%; all but one
  within 2 pixels) and all 263 characters drawn (depth-aware minimum), plus
  doors and story areas as before; the probe's screenshots compared by eye.
  Not device-tested.
- Not done: characters do not walk slower when smaller; seated or scripted
  poses keep their own anchors; Maniac rooms are unchanged.

## Patch 0066 — script-built rooms, map figures, guest chat crash

Device report (2026-10-17, screenshot of Last Crusade's catacomb tunnels):
Castle Brunwald is incomplete; the visitor looks wrong on the Venice
catacomb maps; talking to some characters shows "thinking" and a second
message crashes. Also asked: is local multiplayer available (yes, since
0053: Worlds menu, Connected worlds, Play together on WiFi).
- Crash: the dialogue worker remembered each speaker's last line in a
  25-entry table, but other-world characters are actors 25..29, so a model
  reply from one of them wrote past it and the next message crashed. The
  table now covers every talk actor and the line is remembered in the
  worker's shared path, so the scripted test provider exercises it.
  test_talk_provider adds two messages to guest 27 (fails with the old
  table under UBSan, now fatal in test_talk_runtime; passes under ASan/UBSan
  and TSan). Model-backed replies themselves are not tested here (no weights).
- Script-built rooms: Last Crusade (v3) reuses template rooms as "pseudo
  rooms" 128+ (55 instances of 6 templates: Castle Brunwald's corridors,
  rooms and towers, the Venice library's stacks and reading rooms). The game's boot
  script maps them, which the exporter skips, so they failed or drew the
  bare template. Door maps now keep each instance as its own room with its
  template's resource; the exporter maps it and runs the room's entry
  script for a few cycles (sounds stopped, scripts killed, actors hidden,
  the room must not change), which furnishes that instance. v3/v4 rooms
  that render to one color are retried the same way. The "show every
  object" fallback is gone (it crashed Loom 65 and Last Crusade 20 with a
  screen-strip error). Scenes are "SVW4": each object's state after those
  scripts; doors an instance does not show (`switched` links, 118 in Last
  Crusade) are not offered. kWorldExportVersion is 5. Two more story areas
  are named (Monkey Island beach, Castle Brunwald corridor).
- Map figures: on map rooms (e.g. Melee Island's map, the Venice catacomb
  tunnels) the visitor and guests are drawn at 0.3 of a standing
  person (`scummverseWorldDepth`), like the games' own map figures.
- Folder names: a later report (screenshot of the Other worlds menu) showed
  Loom and Sam & Max as "add Documents/loom" although the user had copied
  them: the folders were "loom " and "samnmax " (trailing space, as zipped
  on a Mac; the files match the audited copies). A game's folder is now
  found ignoring case and surrounding spaces, at launch and in the menu.
  The menu tells a missing folder from one that will be set up at the next
  start ("restart the app to set up") and from one whose setup stopped.
- Export robustness: the engine runs with no console input (an engine error
  ends the export instead of waiting). `<game>-v5.try` counts started
  exports; a game that stopped twice without its `.svx` (a crash, or the app
  closed during setup twice) is skipped at later starts (logged) instead of
  crashing every launch, and the Connected worlds message names it.
- Verified (Linux, the user's private copies): export of all ten games, 635
  scenes and 257 character sprites, no problems (also under ASan: clean,
  byte-identical files); tools/test_world.cpp (634 rooms, 1708 doors, 56
  story areas, every room reachable; SVW4 parse, truncation, sandbox, older
  files); tools/test_world_visit.py (also under ASan) visits all 56 named
  places and every story area, checks the visitor's map-figure height on
  25 map rooms, draws all 263 characters, and walks every door: 1550 lead
  where the map says, 66 do not (4.1%), 16 are skipped and 76 are hidden in
  their instance; test_talk_runtime (ASan/UBSan/TSan), test_startup and the
  original-data suite pass; tools/test_world_setup.py (also with the ASan
  binary) finds "loom " and "LOOM" folders and sets them up, skips a game
  whose marker counts two unfinished setups and retries one with one. The
  iOS menu changes are compiled only by Apple CI.
  Screenshots of a castle instance, the Venice library and the catacomb
  maps compared by eye.
- Known gaps: Last Crusade's castle halls 20, 28 and 32 stay dark (their
  doors' scripts build them, which the export does not run); Loom's cave 65
  is dark; Atlantis 20 and Full Throttle 13 (the ride map) are blank;
  nothing here is device-tested.

## Patch 0067 — all of Castle Brunwald on foot

User request (2026-10-17): walk around Castle Brunwald in its entirety, as
in the original. Two things were missing.
- The three floors (rooms 20, 28, 32) are floor plans: overhead maps a small
  Indy walks around. Each section is an untouchable object switched off under
  a dark cover and drawn only while its cover is off (presumably revealed as
  he explores; inferred from the objects, the reveal script was not traced),
  so the scenes exported black. Door maps now
  have a third room kind, the floor plan (tools/world_maps.py FLOOR_PLANS):
  the exporter switches every section on and its cover off (then refreshes
  the room's object states), and everyone there is a small figure who walks
  to the doors (map rooms still travel at once).
- The rooms off the halls are instances of four templates (corridors, two
  kinds of room, tower rooms) whose doors call
  loadRoomWithEgo(object, room) with variables the instance's entry script
  sets (V99..V107; read from the door scripts with descumm). The analysis had
  left them unresolved, so most rooms had no way back and some doors were
  hidden. world_maps.py's TEMPLATE_DOORS now names each template's door
  variables (numbers only) and resolves them per instance from private
  values captured after each entry script (build/foreign/links/
  indy3-vars.json); they replace the analysis's links for those objects. A
  room of 0 means no door, and the tower and guard-room windows count only
  where the outer wall has a window leading back. The same rules join the
  Venice library's stacks and reading rooms.
- 48 castle rooms (floors, entrance and great hall, kitchen, laundry,
  office, guard rooms, bedrooms, corridors, towers) are now reached from the
  entrance hall through doors and lead back to it (unit-tested). The guards'
  corridor (132, a story encounter) keeps its menu entry.
  kWorldExportVersion is 6.
- Verified (Linux, the user's private copies): export of all ten games
  (also ASan: clean, identical files); tools/test_world.cpp (door maps 634
  rooms, 1683 doors, 55 story areas, every room reachable; Castle Brunwald
  both ways); tools/test_world_visit.py (also ASan) walks every door: 1601
  lead where the map says (was 1550), 66 do not (none in the castle), none
  hidden (was 76); the three floor plans draw and their visitor is a small
  figure; screenshots of the floors and several rooms compared by eye;
  original-data suite. Not device-tested.
- Not done: the guards and Vogel are not in the rooms; doors are not
  opened or closed (a tap walks through); the floor plans show everything at
  once instead of revealing as you explore.

## Patch 0068 — Zak: the Sphinx maze and the pyramid corridors

User request (2026-10-17): walk Zak McKracken's mazes, like the one in
Cairo. A research agent read the original data and scripts (private notes
in build/foreign/zak-mazes/): the maze inside the Sphinx is fourteen cells,
logical rooms 207..220, all on the one corridor resource 23 with Egypt's
pyramid corridor 206 and Mars's 187. The resource-23 entry script draws
each cell's doorways and stores, per doorway, the next cell and the doorway
to arrive at. The sandbox had collapsed resource 23 into one bare corridor
(room 74) whose edges led to the wrong rooms; the maze, the second Sphinx
leg, the Mars sarcophagus chamber and the Egypt map room did not exist, and
the Mars pyramid door skipped straight to an invented crystal-room link.
- Scenes (original logical numbers, newly written names): 207..220 and 187
  on slot 74 (now Egypt's 206), 139 on 73 (now 140, the leg with the secret
  entryway), 186 on 75 (155), 152 on 84 (188). Setups are generated from the
  original-interpreter captures (tools/gen_zak_scene_setup.py; cell 207 from
  its entry script, its capture was taken from the wrong resource). The
  views for 74/75/84 are replaced by those setups.
- Doorways follow the original variables 44..55 per cell (42 links in
  resource 23), plus the Sphinx's secret entryway and both legs, the
  pyramid passage, both sarcophagus chambers with their stairs and the map
  room. Exploration presets open what the original opens by puzzle: the
  leg's secret entryway, the Sphinx's entryway (shown), both sets of stairs,
  the Mars sarcophagus; the dark corridors and the dead end are lit. The
  guardian at the dead end (220) runs no script here.
- Saves: rooms 200..255 were other-world places in saves from patches
  0057..0061; those saves (variable 608 unset) are now migrated before the
  Zak restore steps, and every new game sets 608 at boot, so a save made
  in the maze is never mistaken for one. The WiFi content stamp is 68.
- tools/test_scene_authenticity.py read stray byte runs in 05/03/40/54.LFL
  as pseudo-room table entries (207 -> 12, 204 and 252 -> 51); it now takes
  only the boot script's chained table.
- Verified (Linux, the user's private data): scene audit 82 of 94 exact,
  every maze cell, both corridors, the second leg and the map room among
  them; the four preset rooms differ only by the opened passage (tolerances
  with reasons, compared by eye). New tools/test_maze.py (also ASan) taps
  through all fourteen cells and back out, both pyramids and the Mars
  stairs, checking each arrival's camera, walk boxes and doorway states,
  saves and loads in the maze, and loads a legacy-layout save in 207 (it
  leaves for the airport). test_expansion (also ASan) clicks every link and
  save/loads every logical scene. Original-data suite 30/30. Not
  device-tested.
- Not done: the cells are lit (the original needs a flashlight or lighter);
  the Sphinx's other secret entryway variant (when the other leg is locked)
  and the jungle's random walk are not modelled; passages are shown open
  rather than opened by their puzzles, and the Mars pyramid door leads in
  while still drawn closed.

## Patch 0069 — play as anyone from the other worlds

User request (2026-10-17): more playable characters, especially the main
ones: Indy, the Grail Knight, Biff, Guybrush, Meathook, LeChuck, Stan,
Bobbin, Sam and Max, the Bigfoots, Conroy Bumpus and his henchman, the
Voodoo Lady, "and more than those".
- The character you control can play any cast member of the installed
  games (Worlds menu, "Play as someone from another world", then a game,
  then who; "Be yourself again" undoes it). Switch characters to play
  several at once. The choice is saved per character (variables 641..664:
  appearance key game * 1024 + costume + 1, stable across cast
  regeneration).
- They are drawn from that game's exported frames in every room, as tall
  as a person there: a Maniac teenager (72 V1 pixels) in the mansion and
  Zak's places, the scene's lead character in other worlds (times depth).
  Their name replaces the character's (Actor::getActorName), the roster
  shows their portrait (front standing frame), and chat names and plays
  them (scummverseTalkAppearance). A scene's own copy of that character
  steps aside while someone plays them.
- Portable: fitSprites takes one scale per character; the bridge keeps
  mounted characters independently of scenes (mountCharacters; guests are
  that with the scene's scale) and renders sprite portraits.
- Cast: Henry Jones joins (264 characters). The cast generator had read
  "lying down" in the description of one of his variant costumes as his
  own pose; only the main sprite's description is checked now.
  kWorldExportVersion is 7 so installed games export once more.
- Not included: Last Crusade's Biff is a castle guard in a Nazi uniform,
  which this project leaves out; Fate of Atlantis's Biff (the Barnett
  student) is in. The Grail Knight, Guybrush, Meathook, LeChuck, Stan,
  Bobbin, Sam, Max, three Bigfoots, Conroy Bumpus, Lee-Harvey and the
  Voodoo Lady are all playable, among 264.
- Verified (Linux, the user's private copies): tools/test_world.cpp (own
  scales, characters without a scene, portraits); new
  tools/test_appearance.py (also ASan): Dave plays Indiana Jones and
  Bernard Guybrush through the menu request: name, chat identity, saved
  key, roster portrait, frames beside a scene's characters, drawn height in the mansion
  (72), in Last Crusade (45 of 45 expected) and at the SCUMM Bar (35 of
  34), Barnett's own Indy stepping aside and back, save/load, refusal of
  an unknown character, and Dave again; test_talk_runtime (names and
  personalities in chat); test_world_visit draws all 264 characters;
  original-data suite 31/31; screenshots compared by eye. The iOS
  menu is compiled only by Apple CI; nothing is device-tested.
- Not done: a played character keeps the sandbox character's inventory,
  verbs and travel; WiFi partners see the original character; the
  character has no voice of their own in classic (offline) lines.

## Patch 0070 — crystal teleport pads reach other worlds

User request (2026-10-17): Zak's teleport pads should also go to The Dig,
Loom and other otherworldly places. The pad computer (the pixel destination
computer, opened from a pad or the Worlds menu) lists, after Zak's five
crystal-map sites, every named place and story-area entrance of The Dig,
Loom and Fate of Atlantis whose scene is exported here (up to 7, 8 and 14),
paged four at a time. Choosing one sends the existing place request
(scummverseTravelPlace), the same path as the Visit other worlds menu; Zak
sites keep their scene-bound commands 50..54. Compiled only by Apple CI
(iOS UI); the engine path is covered by the existing other-world probes.
Not device-tested. Patch 0071: the 0070 IPA failed to compile (the pad
type was declared after the view interface that used it); fixed.

## Patch 0072 — Sharptooth, Red Skull and a floating Murray

User request (2026-10-17): play as Murray (the talking skull, who should
levitate), Wally, the Monkey Island monkey, the three-headed monkey and all
three headhunters, among others (Doug the Mole Man too).
- Already playable since 0069: Murray, both Wallys (Monkey Island 2 and
  Curse), the monkey and the three-headed monkey (Monkey Island 1), Doug
  the Mole Man (Sam & Max; the game has only his seated pose), Lemonhead.
  "Timmy" is the monkey's name in Escape from Monkey Island, not a SCUMM
  game; the Monkey Island 1 monkey is in the list as "Monkey".
- The other two headhunters share Lemonhead's costume with their own
  animation sets (masks). The catalog's kWorldCostumeVariants names such a
  character by a virtual costume number (906, 911) with the real costume and
  its init/walk/stand/talk frames; the exporter applies them before
  capturing. Named by their masks (newly written personalities and lines):
  Sharptooth (grey, pointed teeth) and Red Skull. They replace the research
  entry that rendered the shared costume as Lemonhead again. 265 characters;
  kWorldExportVersion is 8.
- Floating: kWorldHoverers (Murray) are drawn a quarter of their height
  above their feet with a gentle bob and keep their standing pose while they
  move, as guests or when played.
- Verified (Linux, the user's private copies): MI1 export of the three masks
  compared by eye; tools/test_world.cpp (variants, floating); test_appearance
  plays Murray (floats 4..8 px, bobbing) besides the 0069 checks;
  test_world_visit draws all 265 characters; original-data suite 31/31.
  Not device-tested.

## Patch 0073 — Zak's San Francisco on foot (14th Avenue)

User request (2026-10-17): Zak must reach 14th Avenue, where the pawn shop
and Annie's place are; it could not be reached on foot.
- Original geography (Zak DOS V1 scripts, private research): the 13th
  Avenue street corner object 141 "14th Avenue" leads up the hill to room 5
  (14th Avenue: Lou's Loans, the Society for Ancient Wisdom door and stairs,
  the hair salon); Lou's Loans is room 7; the Society office upstairs is
  room 6, where Annie starts the game (the data has no separate "Annie's
  apartment"); Zak's bedroom and the street stairs both open into his living
  room (room 2), which the sandbox used to skip.
- No free physical room ID existed (56..126 all used, 127 is other worlds).
  The eleven Mexico temple passages that patch 0038 gave their own slots
  (99..109) are folded back into original logical scenes 157..167 on room
  88's resource, like the Sphinx maze (0068); each keeps its own audited
  setup. Slots 99..102 now hold 14th Avenue, Lou's Loans, the Society
  office and Zak's living room; 103..109 are retired IDs.
- Links follow the original exits and arrival points; the Society door is
  shown open (its stairs walkable); original walk boxes kept in 14th Avenue
  (sidewalk facing hints), Lou's (nobody behind the counter) and the living
  room (not inside the television). NPCs walk the same routes (the bedroom
  and stairs passages go through the living room; a new corner passage).
- Leaving the Shuttle Bug now arrives at its door (original 452), not at
  the tram end of the landing site.
- Saves: scene schema 5 (var 528). Anyone saved in old rooms 99..109 stands
  at the same spot in passage room+58; new games start at schema 5. WiFi
  content stamp 73 (room content changed).
- Not done: Lou himself (would need an extra costume slot); the salon and
  the bakery have no interiors in the original.
- New games start Annie in the Society office (original boot script), not
  in Zak's bedroom; Melissa and Leslie still start at Zak's.
- Verified (Linux, the user's private copies): tools/test_san_francisco.py
  taps every door like a player (bedroom, living room, street, corner,
  Lou's, Society office and back), checks the door, stairs and walk boxes,
  saves and loads in the office, sends an NPC up the corner offscreen,
  refuses retired IDs, leaves the Shuttle Bug at its door and loads a
  schema-4 save standing in old rooms 100/101; scene authenticity: rooms
  99..102, 88 and 157..167 match the original pixel for pixel; test_temple
  (twelve passages, 52 routes), chamber, expansion, airport, bus and cast
  probes updated (the bus probe now parks bystanders in their own rooms);
  original-data suite 32/32; startup test. Not device-tested.

## Patch 0074 — The Dig's light bridges all switched on

User request (2026-10-17): every light bridge on, so players reach every
spire.
- Original logic (The Dig's scripts, private research): a bridge is on when
  its beam object (252, 367, 394, 427, 511) lacks class 32; var 430 counts
  them. Each spire (31, 49, 56, 61, 75), the island map (77) and the hub
  (91) runs its own room script that draws its bridges as actors (light
  streams) and opens their walk boxes. The door map already had every
  bridge door; nothing drew them, and the tomb spire's bridge boxes were
  closed (the exporter never ran v7 room scripts).
- The catalog's exploration presets: classes switched off and variables set
  before a game's rooms are exported, room scripts run for the named rooms
  (whose actors stay for the capture), and the tints the two sunset spires'
  entry scripts give the bridges' colors. A light bridge is a stream of
  pulses, so the still keeps every pixel of one animation cycle. Walk boxes
  are written as the scripts leave them (tomb spire 56 boxes 8/9 open; the
  lab cliff's "off" stub 17 closed). Other games' exports are unchanged;
  kWorldExportVersion is 9 (every game exports again once).
- Doors: a door under a tap now beats one only within the 4-pixel slack
  (the island map's tap on the map spire went to the hub).
- Verified (Linux, the user's private copies): tools/test_dig_bridges.py
  exports The Dig with the real binary and checks bridge pixels in all seven
  rooms, the walk boxes and door-map reachability between every spire and
  the hub; renders of 31/49/56/61/75/77/91 compared by eye; all ten games
  re-exported (635 scenes); test_world_visit (1608 doors; the island map's
  door to the map spire now works; Dig's remaining failures are five
  on-foot doors in rooms 30/34/38/41, unrelated to the bridges);
  tools/test_world.cpp preset checks; original-data suite 33/33.
  Not device-tested.

## Patch 0075 — Fishbowls and oxygen tanks on Mars

User request (2026-10-17): humans on Mars where the original would kill them
wear a goldfish bowl and a scuba mask and tank, as in the original; not the
tentacle; Murray (the talking skull), the monkeys, the three-headed monkey
and the headhunters too.
- Original (Zak's global script 9, private research): kids without gear
  suffocate in about 15 seconds on Mars outdoors (landing site, tram
  station, pyramid entrance, outside the Face) and inside the pyramid
  always; in the Face's halls, antechambers and passages while the air
  machine is off, and in the hostel airlock while its light is on (both as
  the game starts). Zak wears a black fishbowl outline and a mask; Melissa
  and Leslie their helmets; there is no tank picture.
- The sandbox draws newly made gear over anyone who breathes in those
  rooms (zakAirlessRooms): a black bowl with a white glint around the head,
  a mask on the face and a yellow tank on the back with its hose, fitted to
  the pixels the character just drew (only its own screen strips), so it
  fits Maniac and Zak costumes and every other-world character alike; a
  figure about as wide as tall (a skull, a monkey) is all head. Not worn:
  the tentacles, the Caponian and The King, and other-world tentacles,
  ghosts and skeletons, the maintenance droid and the Cocytus aliens
  (kWorldAirless). Nobody suffocates; the gear comes off where there is air.
- Verified (Linux, the user's private copies): tools/test_mars_air.py lines
  up Dave, Zak, Melissa, the Green Tentacle, the Caponian and Bernard
  playing Murray in the hostel bunks (air: no gear) and on the landing site
  (gear on the breathers only, by drawn height and the air rule), and back;
  screenshot compared by eye; tools/test_world.cpp air checks; original-data
  suite 34/34; startup test. Not device-tested.

## Patch 0076 — The Dig's tram, called at the ledge

User request (2026-10-17): the Dig's subway should come by itself when you
near the platform's ledge, let you board, wait a few seconds for others to
board, and go.
- Original (The Dig's scripts, private research): five lines, each from a
  station off the Nexus to one at a spire (80-37, 95-29, 81-70, 83-53,
  94-60); a call switch brings the car (an animated costume), its pictures
  show it parked, the ride is a video the user's copy does not have. Today
  the sandbox moved players at once when they tapped the empty track.
- Catalog kWorldTramLines: per station its car (a door to the other end),
  the car's picture objects, the ledge (inside the platform, where it meets
  the boarding boxes), where riders step off, and the tunnel side.
- Export: each station again with its car parked ("<game>-<room>-car.svw";
  the pictures' own and the game's state switched on). The scene bridge
  fits the station in colors chosen from that picture and keeps only what
  differs (World::fitPicture, WorldBridge::mountPicture/showPicture); the
  engine draws the car into the station's background: sliding out of its
  tunnel, or a dissolve where it comes toward the viewer.
- Play (saved vars 609 phase, 610 riders, 611 trip, 612 where each car is
  parked): walking to a ledge (or tapping the car, which walks there) calls
  the car once per approach; it comes in (1.5 s), opens for 5 s ("Doors
  closing!" near the end), then leaves with everyone standing on the ledge
  and the player's companions, but never without the player (it stays
  parked, open); travel is locked during the ride; after 2 s the riders
  arrive with the car at the other end and step off; that car stays parked
  there and opens at once next time. One trip at a time ("The tram is on
  another run"). Lines are newly written. Export version 10.
- Not done: WiFi players cannot be in other worlds yet (relaying places is
  a later milestone); the original ride video is not shown.
- Verified (Linux, the user's private copies): tools/test_dig_tram.py rides
  the map-spire line: the ledge calls the car, it is drawn at the station,
  Dave, his companion and Wendy on the ledge ride (Razor standing back does
  not), travel is refused mid-ride, a save and load mid-ride keeps riders
  hidden, everyone steps off at the spire station, the parked car opens at
  once and does not leave without the player; test_world_visit takes all
  ten tram doors through the ledge (1608 doors; Dig's remaining failures
  are the five on-foot doors in rooms 30/34/38/41); tools/test_world.cpp
  scene pictures and the line table; screenshots of stations 80 and 37
  compared by eye; original-data suite 35/35; startup test. Not
  device-tested.

## Patch 0077 — Melissa and Leslie's van flies

User request (2026-10-17): the modified van should fly anywhere within reason
(outdoor places, not catacombs or castle interiors); one per game, starting at
its own spot and remembered where parked; passengers (NPCs, networked players)
along; the classic takeoff; flying like the plane, looking out through the
windshield endlessly, with Arrive.
- Original (Zak's scripts, private research): the van, the "Shuttle Bug",
  stands painted into the Mars landing site (object 454 is the empty sand
  drawn once it has gone); its door opens into the cockpit (room 30); the
  controls launch it with a countdown, the windshield's stars (494) and the
  flight colors. It never lands anywhere in the original.
- Here: the controls start a countdown (meters blinking, newly written
  lines), then everyone in the cockpit lifts off into the cockpit in flight
  (logical room 221 on the cockpit's resource: stars, flight colors; the
  riders unseen, first person); travel is locked until Arrive, which shows
  the destination computer listing kWorldVanSites (outdoor Zak, mansion and
  other-world places; other worlds only when exported). Landing parks the
  van beside the player (on the roomier side, as tall as people there) and
  the riders step out; the cockpit door leads back to wherever it stands;
  at Mars the original art shows it or the sand. NPCs only take the
  cockpit door where the van is.
- Away from Mars the van is drawn from the original's art: the landing
  site's background with the van less the same with the sand, taken once
  in the landing site and kept as "zak-van.svv" beside the other worlds'
  cache (the user's own derived data), drawn into redrawn strips of the
  background so people walk in front of it.
- Saved vars 613..618 (site, position, phase, riders, scale); WiFi content
  stamp 77.
- Not done: networked players cannot ride yet (their devices move them;
  passengers are this device's characters); no landing animation outside
  (the original has none).
- Verified (Linux, the user's private copies): tools/test_van.py boards at
  Mars with a companion, launches from the controls, checks the countdown
  lock, liftoff into the flight view, the travel lock, a save and load in
  flight, the landing request in San Francisco (van drawn: 90% of its pixels
  on the background, riders out), boarding by tapping it, the cockpit door
  back to San Francisco, the sand at Mars, a flight to Monkey Island's beach
  (drawn, scaled) and home to Mars; screenshots compared by eye;
  tools/test_world.cpp van sites; original-data suite 36/36; startup test. iOS
  destination computer and Arrive button compiled by Apple CI only. Not
  device-tested.

## Patch 0078 — Curse of Monkey Island in proportion; play the Purple Meteor

User report (2026-10-17, four iPhone screenshots): scaling problems in Curse
of Monkey Island and Fate of Atlantis; a Curse jungle scene looked cut off or
in the wrong aspect; requests to play as The Creator (The Dig) and as the
Purple Meteor, levitating like Murray or Zak's Guru.
- Curse's aspect: the phone shows Maniac's 320x200 screen 1.2 times taller
  (aspect correction), as the 320x200 games were drawn for; Curse draws
  square pixels at 640x480, so its scenes came out squeezed (a 4:3 room
  171 px wide). Scenes and Curse characters are now widened 1.2 when fitted
  (`SourceScene::widen`, `SourceSprite::widen`, catalog `worldWiden`;
  pictures, boxes, objects and door points follow); a 4:3 room is 205 px
  wide. It still sits between dark bands: a 4:3 picture cannot fill the wide
  V1 strip without cropping, which this patch does not do.
- Curse's depth: eight rooms (Puerto Pollo, Blood Island's village, the
  Carnival and others) give their walk boxes a scale only through their entry
  script (box scale slots set at run time), so visitors stood at full size
  (Dave 72 px in Puerto Pollo, about twice Guybrush). The exporter now runs
  such a room's entry script for a few cycles (Curse only: some v7 entry
  scripts need data export mode leaves out), keeps the per-box scales it
  leaves, puts back the game state it changed and sets the room up again;
  pixels are unchanged. Dave in Puerto Pollo is now 57 px, beside Guybrush.
  Export version 11.
- Fate of Atlantis: not reproduced. With the same data the Linux build draws
  Dave 40 px tall on the Seaside village dock (the guest beside him 43 px),
  while the screenshots show him at the unscaled 72 px; every scaled path
  checks out in code, so the phone may be running a build from before patch
  0065 (scale). Asked the user for the build number (Connected worlds).
- Narrow scenes: guests are placed on the scene's own picture, clear of the
  dark side bands (the hotel-lobby screenshot had one half outside it).
- The Creator: already in The Dig's cast and exported (costume 321, one
  pose for every direction; 218 is the same pose and 320/322 are cutscene
  effects, checked by a trial export). Playable from Worlds → Play as
  someone else → The Dig; verified through the engine (103 px in the mansion,
  as much taller than a teenager as beside a person in his game).
- The Purple Meteor: Maniac's own actor 16 (costume 16), offered first in
  Play as someone else. A Maniac look (pseudo game kWorldManiacLooks, key
  saved like other looks) dresses the character in that costume, in the
  Meteor's own V1 colors (Maniac colors costumes by actor:
  `scummverseColorActor`), named and chatting as the Purple Meteor (newly
  written personality and lines), hovering with a slow bob (its costume
  already floats), with no fishbowl on Mars; the character's own costume is
  kept in saved vars 666..689 and comes back with "Be yourself again".
- WiFi content stamp 78 (scene geometry changed).
- Verified (Linux, the user's private copies): test_world (widened fit,
  sprites, catalog looks); ten-game export (645 scenes, 260 characters, no
  errors; only Curse's scales differ from 0077, pixels identical);
  tools/test_appearance.py (The Creator's height; the Meteor's costume,
  colors, name, chat identity, hover 2..6 px, save/load, Melee Island, back
  to Dave); world visit: 1607 doors work, 60 fail (0077: 1608/59; two Curse
  doors in rooms whose boxes convert to slivers now fail, one works);
  screenshots of Puerto Pollo, the village, the Carnival and the beach
  checked by eye; original-data suite 36/36; bootstrap; startup test. iOS
  menu entry compiled by Apple CI only. Not device-tested.

## Patch 0079 — Zak's last two pads, the King's quiff, green Murray, the van to scale

User requests (2026-10-17): make Zak's Atlantis and Mars pyramid teleport
platforms work; the King playable in his Elvis look from the Caponians'
ship; Curse of Monkey Island's green Murray (on the plank) playable besides
the other; the van was out of scale with the characters (an Amiga
screenshot of the landing site for comparison).
- Pads: the crystal map (objects 480-486, script 60) also shows "Atlantis"
  (483) and "Mars pyramid" (485), whose scripts are empty in the original
  (Zak has no Atlantis room). Pad commands 55 and 56 now lead to Fate of
  Atlantis's lost city (area 36, when that game is exported; otherwise "isn't
  installed") and to the platform in the Mars pyramid's crystal room
  (sandbox 84, original 327), whose own platform now opens the pad computer.
  Appended, so commands 50..54 keep their meaning; the iOS pad list names
  seven Zak sites before the other worlds.
- The King (sandbox character 17, costume 27 imported as 39): as on the
  ship (original room 10's object script: Color(1), TalkColor(1),
  animateActor 24), in his white suit with the quiff frame (6) drawn over
  his standing and closed-mouth frames (`scummverseOverlayFrame`, decoded in
  startAnimActor; roster portrait too). Saves with the older grey King get
  the look on load.
- Green Murray: costume variants carry a palette room; Curse's Murray
  (costume 49) is exported a second time in room 11's palette (the ship's
  hold, green; the theater's is orange) as costume 949, "Murray (green)",
  with a newly written personality and lines; he floats like the other.
  Export version 12.
- The van: in the original's landing-site panorama (resource 27: landing
  site 79, tram station 184) Melissa and Leslie wear long-shot spacesuit
  costume 7, 27 px tall (costume 3 is 62 px), beside the painted van; the
  sandbox scaled the van against 62 px and drew everyone there full size.
  Now everyone at the landing site and the tram station is drawn at 27/62
  (the long-shot ratio table also holds the 10 px distant rooms' 5/23), and
  a parked van is scaled against those 27 px people: 2.7 times a person's
  height, as far as the room has room above and across.
- WiFi content stamp unchanged (78): no scene geometry changed.
- Verified (Linux, the user's private copies): test_world; ten-game export
  (645 scenes, 261 characters, no errors); tools/test_expansion.py (pad
  computer from the Mars pyramid platform, all seven commands land, Atlantis
  reaches Fate of Atlantis room 36, out-of-range command 57 ignored);
  tools/test_zak_cast.py (the King's costume, white suit, name, quiff frames
  only on him, an older grey King restored); tools/test_appearance.py (green
  Murray's key, name, float); tools/test_mars_air.py (Dave 34 px at the
  landing site, 72 normally); tools/test_van.py; world visit 1607 doors
  work, 60 fail (as 0078); original-data suite 36/36; Curse re-exported
  after the palette is put back (scenes and characters byte-identical);
  bootstrap; startup test. iOS pad list not compiled yet (Apple CI runs on
  push). Not device-tested.

## Patch 0080 — Play the Meteor Police and the man-eating plant

User requests (2026-10-17, with a Maniac Mansion screenshot of the plant and
a picture of the Meteor Police officer in a glass dome): play as the
"Martian police"; play as the man-eating plant, with wheels under its pot so
it just rolls around.
- Both are Maniac's own (private research of the boot and phone scripts):
  the Meteor Police officer is actor/costume 15 (the phone call's "Meteor
  Police"), the plant actor/costume 19 ("Plant"). Offered under Play as
  someone else after the Purple Meteor, as Maniac looks (kWorldManiacCast:
  newly written personalities and lines; talk color 5, as the originals),
  each in its own V1 colors (the officer green, his uniform red).
- The officer wears a glass dome everywhere, as in the user's picture
  (`worldDomed`): the air gear's bowl alone, in light gray, set on his head
  below the beacon on its stalk (the first rows at least half his width).
  Where there is no air (Mars) he breathes like a person: black bowl, tank
  and mask.
- The plant: its costume's directions are growth stages (left and right a
  sprout, away the grown plant), so it is always shown in its direction
  toward the viewer, its everyday size (`worldRoller`,
  `scummverseCostumeFacing` in the classic costume decoder), mirrored as it
  turns. The original paints its pot into the room; here a newly drawn pot
  on two wheels (17 rows under the stem, in the costume's own colors, two-
  pixel cells, scaled with long shots, masked like the costume) is drawn
  after its limbs (`ClassicCostumeRenderer::drawExtra`); the wheels' spokes
  swap at every step it rolls. It needs no air.
- A Maniac look is now recorded before its costume is set, so the costume's
  first animations already follow it.
- Not done: no rolling sound.
- Verified (Linux, the user's private copies): test_world (catalog: keys,
  names, dome, rolling stage, air); tools/test_appearance.py (the officer's
  costume, colors, name, the dome's glint; the plant's costume, colors,
  name, its everyday stage in all four directions, drawn 52..64 px with the
  pot, pot unchanged and wheels turned one step on, save/load, back to
  Dave); screenshots in the mansion, the airport, the hostel, Mars (gear),
  the landing site and Melee Island checked by eye; tools/test_mars_air.py;
  world visit 1607 doors work, 60 fail (as 0079); original-data suite
  36/36; bootstrap; startup test. iOS menu text compiled by Apple CI only (after a push). Not
  device-tested.

## Patch 0081 — CAMERA: photos and selfies

User request (2026-10-17): a CAMERA button beside AI and Talk, photos and
selfies only (no burst, no Action Freeze, no cinematic burst): tap for a
photo (CLEAN, the room alone, the default; or FULL, the whole screen), with
a white flash, the shutter and "1 photo saved"; hold half a second with a
filling ring for a selfie (the game holds still, everyone turns to the
viewer and poses from their own animations, now and then a surprise,
framed on the player and whoever is near, 1/3/5 photos posed afresh, 3 by
default, everything put back exactly afterwards); options (CLEAN/FULL,
SELFIES 1/3/5) on a panel opened by sliding CAMERA down, remembered; Photos
with add-only access (asked once, the game holding still meanwhile), or
Files › SCUMMVERSE › Screenshots when it is off; names like "SCUMMVERSE
2026-10-17 14.05.09 clean.png". The Serious Sam port's iOS photo saving was
the reference (read only); the OpenJKDF2 one was not needed.
- Portable (common/scummverse_camera.{h,cpp}, plain-types face
  scummverse_camera_engine.h): the request slot, the hold flag, notes for
  the player, whole-pixel enlarging (columns 5x, rows 6x: the 1.2 aspect;
  the longer side at least 1600, at most 4096), selfie framing (the player
  and those within three quarters of their height side to side, head room,
  4:5 to 4:3 as shown, inside the view), pose plans (standing 40%,
  mid-step 30%, talking 30%; in about one shot in four someone hasn't
  noticed or everyone stares at the player), names (a second photo within
  the same second gets -2 after the time), and a sink the saver registers.
- Game side (engines/scumm/scummverse_camera.inc, at the top of
  scummLoop): a photo copies the last drawn frame: CLEAN the main virtual
  screen; FULL the room, the line above it and the verbs at their lines
  (not the hidden banner screen), the text overlay (speech) and the V1 DOS
  line colors. A selfie (the sandbox's V1 edition only) keeps everyone's
  pose state (`Actor::PoseState`: facing, frame, animation, costume
  state, extent), the gfx usage bits and the other worlds' animation
  clocks; each shot is posed from that and drawn without scripts or
  walking (guests and characters from other games pose from their own
  frames); the frame is set by the first shot; the last stays 0.9 s; then
  everything is put back and the next step draws it (a photo waits that
  step). No scripts, timers or network polling run meanwhile (up to about
  2.5 s for five). "No selfie here" without the player in the room;
  a selfie nobody can save says so. Requests and notes are cleared when a
  game starts or ends.
- iOS (scummverse_camera_ui.inc, manual reference counting): the button
  (camera symbol, below Worlds in the landscape column, after Worlds in the
  portrait toolbar), its ring, the slide-down options, the flash, the
  shutter (system sound 1108), PNG encoding off the main thread, saving to
  Photos (iOS 14 on; on iOS 13 to Files, since adding there needs full
  library access), the "N photos saved" line once per photo or selfie, the
  game's notes. NSPhotoLibraryAddUsageDescription in Info.plist; Photos
  and ImageIO linked by the IPA workflow.
- Reviews: two independent reviews (iOS side; game and portable side).
  Fixed from them: FULL had the hidden banner screen over the room (a black
  band) and lacked speech; the test's expectations were built the same way,
  so they are now independent (each photo against the screen as drawn);
  iOS 13 would have tried Photos without the right permission; selfies
  restricted to the sandbox's V1 edition; stale requests cleared per game;
  selfie failures reported; the step after a selfie draws before any photo;
  a stuck "saved" line, double asking, the options panel's taps and
  rotation, sliding off the button, VoiceOver actions.
- Verified (Linux, the user's private copies): tools/test_camera.cpp
  (ASan/UBSan: requests, factors, enlarging, framing, poses, names,
  delivery); tools/test_camera_engine.py (new, in the data suite): CLEAN
  is the room as drawn at 1600 by 816, FULL 1600 by 1200 with the room as
  drawn and the verbs, speech on FULL; selfies of three in the mansion (a
  crowd), with Dave alone and on Melee Island (Bernard as Guybrush): no
  variable changes while held, whole pixels, 4:5 to 4:3, the saved state
  byte for byte the same afterwards and, alone, the room pixel for pixel the
  same one step later; the hold; a selfie with nobody to save it; no selfie
  without the player; three runs in a row; screenshots checked by eye;
  test_world; world visit 1607 doors work, 60 fail (as 0080); original-data
  suite 37/37; bootstrap; startup. The iOS
  button, ring, panel, flash, shutter, Photos permission and saving are
  not compiled yet (Apple CI on push) and not device-tested.

## Patch 0082 — Chaos, both Teds, the grown plant; Mars air; game folders one level down

User requests (2026-10-17, with pictures of Loom's Chaos, Day of the
Tentacle's beauty contest (Remastered) and Maniac's upstairs bathroom):
play as Chaos, levitating; play as Day of the Tentacle's Ted dressed for the
beauty contest (spaghetti for hair, the fake lips, roller skates), rolling
on his skates and otherwise still; play as Maniac's Ted with roller skates,
otherwise still; the plant fully grown; no fishbowl for the Meteor Police
on Mars (his dome is his helmet), a fishbowl for the plant there. Also:
Loom and Sam & Max shown greyed out although their files were installed.
- Chaos (Loom costume 130) hovers (`kWorldHoverers`) and needs no air. The
  hover lift is now at most 12 pixels plus the bob, so a tall character
  stays on the screen; his robe hangs below his feet line, so the gap
  under it is smaller than the lift.
- Day of the Tentacle's Ted (costume 235: white suit, sunglasses, roller
  skates, bald; the floppy data has no contest head, which is in the
  Remastered art only) is a glider (`kWorldGliders`): he keeps his standing
  pose while he moves, so he rolls on his own skates. Played, he wears a
  newly drawn dress-up (`scummverseDrawDressUp`): wavy yellow strands over
  his scalp, short over the brow and long at the back, and big red lips
  with white teeth over his mouth, fitted to his frames (they all look
  right). His frames all look right, so facing left he is drawn mirrored,
  dress-up included (`oneWay`), here and as a guest in his own world, where
  he glides without the dress-up. He wears a fishbowl on Mars (the user:
  "Ted should get a fishbowl when he's on mars"; he is dead, so the
  fishbowl is deliberate dark humor).
- Dead Cousin Ted (Maniac costume 12) is a new Maniac look (newly written
  personality and lines). He rolls (`worldRoller` with gear skates, his own
  direction): lifted two V1 rows (four pixels, `kWorldSkateLift`), with
  newly drawn skates filling them: red plates on yellow wheels whose
  spokes turn as he rolls (fixed colors so they show on any floor). He
  wears a fishbowl and tank on Mars, over his own head.
- The plant's direction is now away from the viewer: the grown plant
  (about 70 px, 86 with the pot), still on its pot with wheels. It breathes,
  so Mars gives it a fishbowl and tank; the Meteor Police officer no longer
  does (his dome stays everywhere).
- Where Mars has air (the user: fishbowls only outdoors and in the Great
  Pyramid; "inside the great chamber on mars there's breathable air"):
  `zakAirlessRooms` is now the landing site, the tram station, the Great
  Pyramid's entrance and its corridor, sarcophagus chamber and crystal
  room. The Face from its Great Chamber in (the three massive doors, the
  antechambers, passages and chambers) and the hostel's airlock have air,
  as if the original's air machine and airlock were running.
- Loom and Sam & Max greyed out: the user's files were fine (byte-for-byte
  the tested copies) but sat inside an unzipped archive's folder. The app
  now looks one folder further down too, skipping `__MACOSX` and hidden
  folders (base/main.cpp for setup, the iOS status for the menu), and
  Connected worlds names top-level folders it does not recognize.
- Verified (Linux, the user's private copies): test_world (catalog: the
  officer airless and domed, the plant breathing and grown, Ted's skates,
  the glider and its dress-up, Chaos hovering); tools/test_appearance.py
  (the plant's grown stage in all four directions, 80..96 px with the pot,
  pot unchanged and wheels turned; Maniac Ted lifted, skate plates
  unchanged and wheels turned one step on, back to Dave; Day of the
  Tentacle's Ted in his dress-up and gliding; Chaos 10..14 px over the
  floor and on the screen; DOTT Ted's lips at the front of his face either
  way he faces); tools/test_mars_air.py (air in the hostel's airlock, the
  Great Chamber, the three massive doors and the machine chamber; none
  outside and inside the Great Pyramid and at the landing site; playing
  the officer: no gear, the dome kept; the plant and both Teds: gear;
  Chaos: none); original-data suite 37/37; bootstrap; startup; tools/test_world_setup.py (game folders inside an archive's
  folder, beside a `__MACOSX` decoy); screenshots checked by eye (on the
  dark brick wall outside the Face the bowls' black rims are faint, as
  everyone's are there).
- The user's Loom and Sam & Max showed once they renamed the folders
  without the trailing spaces, on the build before this patch (which
  already ignored spaces at the ends of names here on Linux, so the cause
  on the iPhone is not certain; the nested folder is the likelier one). The iOS folder search and the new status line are not compiled yet
  (Apple CI on push) and not device-tested.

## Patch 0083 — Murray bounces and talks; selfies put every actor back

User requests (2026-10-17): "Murray should bounce to move around. And his
mouth should move when he's talking." (Both of Curse's Murrays, the skull
and the green one of the ship's hold.)
- Murray no longer floats (`kWorldHoverers` keeps the Purple Meteor and
  Chaos). He is a bouncer (`kWorldBouncers`): at rest on the ground; while
  he moves, hops like a ball half his height high (at most 16 pixels, one
  hop every 24 ticks), a hop under way finished when he stops
  (`worldHop`, per character and per scene guest); posing for a selfie, on
  the ground. As a guest in his own world he now hops about too (he did not
  move before, having no walking frames).
- His mouth: the exported talking frames (two, the jaw about a pixel apart
  at this size) barely showed. Talking now draws his standing frame with
  the head above his jaw (54 rows in 100 from the top) lifted two rows
  every other talking step, the gap his frame's darkest color: a mouth
  opening and closing.
- Sprite drawing options are one `ScummverseSpriteStyle` (hover, glide,
  dress-up, one-way, hop, jaw).
- CAMERA fix (patch 0081's selfie): its full redraw marks every actor for
  drawing, those in other rooms too, and clears every actor's background
  reset; only the people in the room were put back, so a character sent
  elsewhere could come out of a selfie marked (the data suite caught it
  once in 37 tests: "The selfie changed the game (alone)"). A selfie now
  keeps both flags for every actor and puts them back.
  tools/probes/camera.inc clears the flag on those it sends away before
  the lone selfie, so the case is tested every run (it failed every run
  without the fix, and passes with it).
- Verified (Linux, the user's private copies): test_world (bouncers, the
  jaw, no longer hovering); tools/test_appearance.py (Murray on the ground
  at rest, 13 px hops with two landings while walking, landed after, his
  mouth open 22 and closed 18 of 40 talking steps; green Murray on the
  ground; the other looks as before); tools/test_camera_engine.py three
  runs in a row; original-data suite 37/37; bootstrap; startup;
  screenshots (closed, open, mid-hop) checked by eye. Not device-tested.

## Patch 0084 — the CAMERA's iOS code compiles

Apple CI run 84 (0081–0083 pushed, the CAMERA's iOS code compiled for the
first time) failed with one error: scummverse_camera_ui.inc used
`scummverseCameraNoPhotos` before defining it. It is now defined above its
first use; nothing else changes. Compiled by Apple CI only after this push;
not device-tested.

## Patch 0085 — TOUR: every location, numbered

User requests (2026-10-18): "an NPC I can spectate who systematically walks
through every single room/location, which I can just sit back and watch
looking for bugs. Each room/location it enters should have a label/
identification number I can make note of to report bugs"; "If there's no
way to traverse a location it should just warp to it. But I want it to get
to every location"; all twelve games.
- The guide is the character the player controls, on autopilot (the camera
  follows it); Stop brings it back to where the tour began. (A separate
  NPC would need the sandbox's travel, which moves the controlled
  character, to move someone else: offered to the user, not built.)
- 773 stops with every game installed: Maniac Mansion's 37 rooms a kid can
  stand in (private research of the original scripts: each is a
  loadRoomWithEgo target; close-ups, title, cutscene and ending rooms
  excluded; the same rooms as mansionPassages), Zak's 102 (apartment,
  airport, street, imported rooms, logical scenes), then the 634 rooms of
  the ten other games' door maps. Stop numbers come from static tables only,
  so they are the same on every device; stops of games not installed are
  passed over.
- Route: per game, from its first room, the nearest room not yet visited by
  doors (breadth-first over mansionPassages, zakLinks or the door map,
  passing back through visited rooms: "on the way through …"), else a warp
  to the next unvisited room; 109 warps (the 12 game starts, rooms no door
  reaches: by plane, bus, tram or cutscene). Doors are used the way a
  player's are (scummversePassage, the zakLinks travel,
  scummverseFollowLink); a door that will not take the guide falls back to
  a warp. All of it as though landing, so no ride (a plane mid-flight, a
  tram) holds the guide; other-world travel now honors that too.
- In each stop: settle, walk across (to 12% and 88% of the room's width
  and back to the middle, each at most 10 s), a last look, then on.
- Label (top left, over the game): "Stop 137 of 773 · Zak 84 · Mars pyramid
  crystal room", "· warped" when warped there; tap it for the controls.
  Controls (Worlds menu › Tour every location): Start / Start at stop N
  (remembered in the configuration, scummverse_tour_stop), Start over,
  Go to stop… (a number), Next, Previous, Stop the tour.
- Verified (Linux, the user's private copies): tools/test_tour.cpp (ASan/
  UBSan and TSan: requests, label, whole-character truncation, two
  threads); tools/test_tour_engine.py (new, in the data suite): stop 1 walked
  across, stop 2 reached through its door by itself; Stop returns home;
  Resume at the remembered stop, Next, Previous; stops 2..12 on their own
  all through doors; every one of the 773 stops entered by number, in the
  room it names; every door of the route taken from the stop before: 1073
  doors, 6 fail (door objects absent from the exported scenes: Monkey
  Island 2 rooms 61 and 82, Atlantis 48, Day of the Tentacle 21; the tour
  warps there); screenshots checked by eye. The iOS label and menu are
  compiled by Apple CI only after a push; not device-tested.

## Patch 0086 — TOUR: one clean pass, continuous walking

User requests (2026-10-18): "There should be no stopping just continuous
walking"; then "I don't like the way he doubles back and goes back and
forth. It should be one clean pass through and only revisit locations to
get to ones he hasn't been to yet".
- One pass through each stop: from where the guide comes in straight on to
  the door out (the next stop's first door). Only where that door's walk
  spot lies within a quarter of the room's width of where it came in (a
  dead end entered and left by the same door, or doors side by side), or
  there is no door out (a warp follows), does it first walk to the
  walkable spot farthest from where it came in (a walk box corner as the
  boxes take it: a room's far end, a winding path's other end), the one
  turn. Rooms are still revisited only on the way to rooms not yet
  visited (the 0085 route, unchanged).
- No pauses: a step that starts no walk (already there, a warp, a door
  taken) is followed by the next in the same update (scummverseTourAdvance,
  at most 8 steps), so the guide stands at most the one frame between two
  walks. Every stop is still shown at least a second for its label to be
  read: where the walk is shorter the guide waits at the door out.
- The label's stop is now kept apart from the stop being walked to
  (_scummverseTourShown): Next, Previous, the remembered stop and the
  menu's "Start at stop N" follow the stop on the label, since the guide
  heads for the next stop's door as soon as it arrives.
- Fixed on the way: in other games' rooms the tour's walks counted as taps,
  so a walk ending near a door (or the side exit of a game without a door
  map, or the mansion's road and airport edges) took the guide off its
  route into another room under the old label. Taps and edge exits are
  ignored while touring (the tour takes its doors itself); a tap pending
  from before the tour is dropped.
- Other worlds (players too): a walk that comes back to a spot it has
  already passed ends there (scummverseWorldDoors). Converted walk boxes
  could send the V1 walker round a loop (Monkey Island room 141: about
  10 s circling) or back and forth; the existing check caught only a
  walker standing still.
- Found, not fixed: in some rooms of the other games the guide cannot walk
  from the spot a door puts it on (the walk ends at once: the box there
  does not lead on); it waits its second and goes on. Part of task #25
  (converted walk boxes).
- Independent review of the first version (read-only) found no blocker;
  applied: the road and airport edge exits are disarmed when the tour ends
  (home may lie at an edge), and walks go nowhere in a room without walk
  boxes (no stop has none today). Left as is: the one frame of standing
  pose where one walk ends and the next begins.
- iOS: the screen stays awake while the tour runs (idleTimerDisabled), so
  it can be watched or screen-recorded without the phone locking; docs/
  ios.md gives each game's first stop for recording a game at a time.
- Verified (Linux, the user's private copies): tools/test_tour_engine.py
  now also walks the mansion's stops 2..12 and the first seven stops of
  Zak's world and of each of the ten other games on their own, requiring
  every stop in turn (none skipped), the guide in the stop's room until
  the next, never more than one step without walking apart from the wait
  at a door (all twelve: 1), at most one turn back in a stop (32 pixels
  or more; the mansion and Zak strictly, other worlds listed: none turned
  more than once), and each stop shown at least 14 steps; the rest as in
  0085 (773 stops entered, 1073 doors, the same 6 failing). The iOS change
  is compiled by Apple CI only after a push. Not device-tested.

## Patch 0087 — TOUR: 2x, 4x and 8x speed

User requests (2026-10-18): "Can you make options to make him walk in 2x
and 4x speed?"; "Can you make an 8X also".
- The tour's controls have Speed: 1x, 2x, 4x, 8x in turn. While touring
  the whole game plays that much faster (waitForTimer waits a half, a
  quarter or an eighth as long between game steps), like a video played
  fast: the
  guide's steps and legs, other characters and animations alike, rather
  than the guide alone sliding faster. Normal speed again whenever the
  tour is not running. The choice is remembered (scummverse_tour_speed).
  Every stop still lasts at least a second of game time, so an eighth of
  a second at 8x; the iOS label now refreshes five times a second (was
  twice) so a quick stop still shows. Played fast, the screen is shown at
  most about 60 times a second (every 16 ms; the steps between are drawn
  but not shown), so a display that waits for the screen's refresh does
  not hold the game back (8x of Maniac Mansion's 9 to 18 steps a second
  would be more than 60).
- Portable: common/scummverse_tour Tour::setSpeed/speed (1, 2, 4 or 8,
  else 1; under the mutex; reset to 1).
- Verified (Linux, the user's private copies): tools/test_tour.cpp (ASan/
  UBSan and TSan: speed values, clamping, reset, two threads);
  tools/test_tour_engine.py: 4x and 8x taken up and remembered, a 500 ms
  wait 549 ms at 1x, 137 ms at 4x, 68 ms at 8x touring, 550 ms at 8x not
  touring; back to 1x; the rest as in 0086. The 60-a-second showing is
  not measured (the test's null screen does not wait). The iOS menu and
  the faster label refresh are compiled by Apple CI only after a push.
  Not device-tested (how fast and smoothly an iPhone plays 8x is not
  known yet).

## Patch 0088 — TOUR: control bar, pause, 16x

User requests (2026-10-18): "It needs 16x"; "Changing the speed requires
going in and out of the menu because it closes every time I change it";
"When in tour mode make a button that I can pause and rewind if possible
in the main interface so I don't have to go into that menu. If I see a bug
I want to be able to quickly pause and hit like a left arrow button which
goes back to each numbered location while it's paused. So I can take
screenshots of bugs to send you"; "I want this on the main screen
somewhere when tour is enabled. Not hidden in options".
- iOS: while touring, a bar on the game's screen under the label:
  previous stop, pause/play, next stop, speed (1x, 2x, 4x, 8x, 16x in
  turn), go to a stop by number (asks the number), stop the tour. Tapping
  changes only that; the tour's menu is not needed (the label still opens
  it). Narrower buttons on a narrow screen, clear of the buttons on the
  right. The pause icon follows what was asked
  until the game says so (scummverseTourAsked).
- Pause: the guide stops where it is (the player may walk it about); the
  label stays. Paused, Previous and Next warp from stop to stop and stay
  paused (only a warp is made while paused: scummverseTourAdvance); Play
  walks again to the walk that was under way (the far end, or the door
  out: _scummverseTourTarget, the door point) from where the guide is. The
  game plays at normal speed while paused.
- 16x: the speed's last step (Tour::setSpeed 16; the screen still shown
  at most every 16 ms). How close an iPhone comes to 16x is not known.
- Requests now wait in order (at most 16; the oldest go), one taken a game
  step, so quick taps all count: two taps on Next go two stops on.
- Verified (Linux, the user's private copies): tools/test_tour.cpp (ASan/
  UBSan, TSan: requests in order and capped, paused, 16x, two threads);
  tools/test_tour_engine.py: a 500 ms wait 34 ms at 16x, 549 ms paused;
  paused 60 steps the guide and label unchanged; Previous then Next twice
  while paused land on the stops before and after, still paused; Play
  walks on; the rest as in 0087. The iOS bar is compiled by Apple CI only
  after a push. Not device-tested.

## Patch 0089 — Lights on in dark rooms; doors opened before going through

User requests (2026-10-18): "if doors were closed, characters would walk
through them without opening ... if they come upon a closed door to open
it automatically"; "I also want the lights to be turned on in dark rooms
by default if there's an in game light available. Like the maniac mansion
basement by the reactor".
- Lights: the original starts six rooms dark (global script 1 sets their
  "light is off" bit, 2816 + room; script 55 lights a room from it): the
  phone hall (5), the basement by the reactor (8), the wall-safe closet
  (9), the crawlspace (15), the medical office (22) and the darkroom (23).
  Each has its own light (switch, lamps, desk lamp, red light) whose Turn on
  clears that bit and nothing else (private research of the scripts,
  confirmed by running each Turn on). The sandbox clears the six bits once
  per game (var 619, kScummverseLightsVar): at its start, and on loading a
  save made before. The switches work as before; a light switched off stays
  off. Zak's rooms and the other games' are already shown lit.
- Doors: Maniac Mansion's walking characters already opened a door as they
  set off to it; the tour guide's opened only as it left the room, unseen.
  The tour now opens the door as the guide sets off to it (both sides).
  Zak: the player, Zak's walking characters and the tour went through
  closed doors; now a door opens as someone goes through it, and the door
  back on arrival, but only Zak's closed doors whose open picture was
  checked by eye (14 of 30) and that are not in a scene set up as the
  original's own (zakSceneSetups, held to the original's states by
  tools/test_maze.py: the Sphinx maze, the pyramids, the jail, the
  hostel...): 8 doors (zakOpenDoors). In the imported rooms other doors'
  open pictures draw garbled (the hut, the hostel corridor), reversed (two),
  or with someone painted in the doorway (the guru's). Opened Zak doors close again when
  the room is entered anew (its states are restored then).
- Not done: the other ten games' rooms are exported pictures with their
  doors drawn in as the room starts; opening them needs each door's open
  picture in the export (a new export version and re-export), proposed.
- Verified (Linux, the user's private copies): tools/test_lights_doors.py
  (new, in the data suite): the six rooms lit in a new sandbox; the
  basement's switch off (dark, and dark again after leaving and coming
  back) and on; an old save lit once; the tour walked through Maniac's
  stops 2..37 and Zak's 38..139: 49 Maniac doors open as the guide set off,
  5 of Zak's clean doors and 8 doors back on arrival, 122 other Zak door
  objects left as drawn; tools/test_maze.py passes; the player's walk through Zak's
  jail door opens the door back (in room 67). Not device-tested.

## Patch 0090 — Picture-pass fixes

User requests (2026-10-18): "When you do the picture pass I want to know all
the errors you find"; "Can we keep making corrections without building yet?"
The picture pass (a private probe: the tour paused, every stop gone to and
its screen saved under build/tour-shots/, then looked over) found broken,
blank and badly placed stops. Fixed here:
- Arrival spot in other worlds (`fitScene`): the middle of the lowest walk
  box at least a quarter the size of the biggest, instead of the biggest
  box's center (that put the guide in the sky, in lava or water, or with
  the head cut off on stops such as 239, 611, 666, 711).
- Characters there (`scummversePlaceGuest`): of the floor spots across the
  scene, a step behind the arrival point, the one with the most room (up to
  48 pixels) from the player, the arrival spot and the others, nearest its
  own side; with no room left (a narrow scene, wide characters) a step
  further back. Whoever arrives is drawn in front of them. They used to pile
  up on and in front of the guide (Curse rooms 21 and 36, the Edison
  grounds).
- Tour spots: Maniac's art studio stop stands clear of the easel; Zak's
  Mars landing site (79) stands at a picked spot, clear of the tram.
- Export (version 13, every game exports again): a v3..v6 room that comes out
  one color is retried with its entry script (was v3/v4 only); one color
  even then is no place and is not exported (Loom 65, Atlantis 20, Full
  Throttle 13: a black or beige backdrop). On the phone an older export's
  scene of such a room is emptied; the tour and the menus (story areas,
  crystal pads, van sites) pass over empty scenes, and doors into them do
  nothing (7 doors: two in Atlantis to its room 20, five in Full
  Throttle to its room 13).
  Loom's pictures have holes (solid black) where animation frames go; where
  a frame's rectangle is a hole in a lit picture, the first of the frames
  there that fills it is drawn (the waterspout, the beach, the glass city,
  the sky, the tents...). Day of the Tentacle's room 11 is cut to its 144
  picture rows (a pink block below them).
- Not fixed (reported): holes in Loom's dark rooms (26, 28, 31, 50: their
  frames cover little of the hole, or the room around is dark too); stops
  whose walk boxes are all near the top (the guide is cut off by the top
  edge: 240, 476, 576, 696); the scale in two Curse rooms (728, 729); a
  light effect drawn as stripes (693); a few stops that are not real
  places (cutscene or map screens: 230, 514, 614, 616, 662, 697); the map
  guide standing in the sea (153, 155, 164); stop 166's label.
- Verified (Linux, the user's private copies): the picture pass again over
  all 773 stops (the blank stops gone, the guide visible at the crowded
  ones, the Loom holes above filled), compared stop by stop with the first
  pass by an independent review (no stop worse; a few unsure ones checked
  at full size); tools/test_world (ASan, UBSan); the data suite, 39 tests
  (world visit with the 0089 build as baseline: the same doors work but
  the 9 into or out of the three dropped rooms, 1589 work, 68 fail; 54
  story areas, the Loom cave dropped). The iPhone menus' changes are not
  compiled here (Apple CI builds them). Not device-tested.

## Patch 0091 — The van's destination chosen aboard; the Mars tram comes by itself; Ted from the side; the TOUR bar off the picture

User requests (2026-10-18): "Make the tram work from the pyramid back to
the great face on mars. It comes after a few seconds."; "Take the controls
off the screen in tour mode. I want to see the tour unobstructed. Put the
controls somewhere else, if possible"; "Give Ted a sideview. He's always
looking forward."
- Tram: its call button stands at the landing site only, so at the tram
  station by the pyramid nobody could call it back. Now whoever waits at a
  station where it is not (and it is idle at the other) brings it over
  after two seconds ("The tram is on its way."), empty, three seconds'
  ride; then boarding and the ride back as before (kTramCallWait); not
  while touring (the tour's pictures keep the tram put).
- Ted: Maniac's costume for him shows him only from the front. Facing left
  or right he is newly drawn from the side (a narrower wrapped figure with
  a nose, in his own colors; the skates seen side-on), the costume's own
  frames left out then (ClassicCostumeRenderer::drawsFigure, catalog
  kWorldProfiles).
- TOUR: the stop's label and the bar move off the game's picture: in
  landscape into the band left of it, where the renderer drew the picture
  (published by the iOS graphics manager, scummverseGameRect; the label up
  to six lines, the buttons in rows of three, or two in a band 88 to 132
  points wide, which is the iPhones'), in portrait to the top of the chat
  area under the toolbar; over the picture's top left only where neither
  has room (a split screen, the smallest phones).
- Van (user, with a picture of the destinations: "This screen should
  appear as soon as you get in the van. You choose a destination and then
  it shows the animation take off. And you can chill in the van until you
  hit arrive"): aboard on the ground the destinations show at once (on the
  iPhone; once a visit to the cockpit, not for the tour; the controls show
  them again); the one chosen is kept (variable 620, kVanDestinationVar)
  and the countdown and liftoff follow; Arrive lands there. Chosen in
  flight (no destination kept, as in a save from before), it lands at
  once, as before. The user's van that always came down at the Shepherds
  Meadow: on the desktop every landing goes where asked (the meadow first,
  then San Francisco, Monkey Island, Barnett College, the mansion and the
  asteroid, each with a save and load in flight); not reproduced.
- Verified (Linux, the user's private copies): tools/test_tram.py (the
  tram coming to whoever waits, both ways, and the ride back from the
  pyramid's station), tools/test_appearance.py (over a plain color: Ted 14
  pixels wide across his middle from the side, 20 from the front, his
  nose ahead of him both ways, facing away his own costume), tools/test_van.py
  (destinations shown aboard, the choice starting the countdown and kept
  through a save and load in flight, Arrive landing there; a choice made
  in flight landing at once); the data suite, 39 tests: 38 passed, the
  camera test once failed (three selfie shots alike on Melee Island) and
  passed on three reruns (intermittent, cause not found). An independent
  review then found the landscape band rule unreachable on iPhones (the
  layout's band is 90 to 120 points there), the side figure tied to the
  skates, the tram sending itself during the tour, the cut-off redraw flag
  lost and a weak test; all fixed, and the van, tram, tour, appearance,
  camera, portrait and Mars air tests passed again. The iPhone code (the
  TOUR bar's place, the published picture rectangle, the destinations
  shown on boarding) is not compiled here (Apple CI builds it). Not
  device-tested.

## Patch 0092 — The tram's platform swept of its sand

User request (2026-10-18, a picture of the Mars landing site): "Clean the
sand off for continuity that the tram works lol".
- The sand drifted over the tram's platform is the original's object 451
  ("sand"); with its state 8 the original draws the platform swept (its
  own picture: grey slabs on legs). At both tram stations (the landing
  site and the tram station, one resource) it is set so from the first
  look (scummverseApplyTramState, every update there; kZakTramSand).
- Verified (Linux, the user's private copies): tools/test_tram.py (the sand
  object swept at the landing site; the rides as before), test_mars,
  test_mars_air, test_van, test_tour_engine, test_scene_authenticity (86
  of 99 rooms match an original scene, as before); a screenshot of the
  landing site shows the platform. Not device-tested.

## Patch 0093 — Ted from the side, redrawn with his glasses

User (2026-10-18): "The ted side view is terrible. What about his glasses?"
- The side view (0091) is drawn again after his front: his skull as wide,
  his glasses' round lens (dark rim, white glass) in front of his face
  with its arm back toward his ear and his nose under it, his arms folded
  at his chest and the dark band at his waist as from the front, the
  wrappings in short bands like his own.
- The appearance test now checks what matters for a side view: his
  glasses and nose ahead of his hips the way he faces (4 pixels, both
  ways), left and right differing from the front and from each other,
  facing away his own costume.
- Verified (Linux): tools/test_appearance.py; a screenshot of him facing
  front, left and right was sent to the user for a look. Not
  device-tested.

## Patch 0094 — The character screen, without the opening

User (2026-10-18): skip Maniac Mansion's opening and go straight to a
character screen of 12 boxes, one per game, each showing its main
character; a tap plays them, a long press lists everyone in that game;
"Play as someone else" in the game comes back to it. "Don't put 'all' in
each box. Just make a note on the screen somewhere which says long press
for all".
- A new sandbox game no longer plays the opening: at the end of the boot
  the boot scripts run on at once (waits and messages cut short, sound
  stopped) until the sandbox is ready, and the character screen opens.
  Loading a saved game is unchanged (it never runs the boot).
- The screen (iPhone, scummverse_cast_ui.inc): "Who do you want to play?",
  the note "Long press a game for everyone in it", Done, and 12 boxes
  (3 across in portrait, 6 in landscape, scrolling when they don't fit):
  Maniac Mansion (Dave), Zak McKracken (Zak), then the ten other games
  with their leads (catalog kWorldLeads: Guybrush in both Monkey Islands
  and in COMI, Bobbin, Indy twice, Bernard, Sam, Ben, Boston Low). The faces are
  drawn from the player's own files, as the roster's are. A game not set
  up is dimmed with "Add Documents/<folder>" and a tap says how.
- A tap plays the lead: Dave or Zak as themselves; someone from another
  game takes their look and goes where they live (Guybrush to Melee
  Island). The long-press list has everyone with frames: Maniac's people
  and its four looks (Purple Meteor, Meteor Police, the man-eating
  plant, Dead Cousin Ted), Zak's people, each game's cast once by name.
- "Play as someone else" in the Worlds menu (command 61) and the game's
  own New Kid button open the screen; the separate "Choose character"
  entry and the old play-as menus are gone. Off the iPhone the roster
  stays.
- Long press opens a scrolling list (some games have over thirty people),
  Cancel closes it; a game not set up says how to add it.
- Tests: two probes that needed Zak missing at the start (worlds,
  airport) now start the game without him, since the boot reaches the
  sandbox before a probe runs. tools/test_cast.py (in the data suite):
  the sandbox ready at the end of the boot, the screen shown once, 12
  boxes, the leads (Dave, Zak, each game's), a face for each game set up,
  Guybrush played on Melee Island, Bernard as himself, "Play as someone
  else" and New Kid showing it again.
- Independent review of the iPhone code (it cannot be compiled here): no
  compile errors found; fixed from it: names that may be missing, frames
  checked for without reading them (73 MB of files read on each opening),
  the long list, the Done button's size, light status bar, pressed tiles,
  labels shrinking to fit, and a retry when an alert is up at the start.
- Verified (Linux, the user's private copies): data suite 40/40 before
  the review fixes (two failed on the first run before their setup fix;
  re-run, passed); after them cast, worlds, airport and appearance again;
  bootstrap, startup. Not compiled for iOS yet (the screen is iOS only);
  not device-tested.

## Patch 0095 — Everyone sits on the plane

User (2026-10-18, playing Dr Fred, a screenshot of a woman standing in the
aisle): "Why is she not sitting when I got on the plane? ... Everyone
should sit on the plane and replace the painting. Even the man eating
plant, Ted, the rat, the parrot, the creator, etc"
- Someone boarding with the player was already seated (reproduced:
  Dr Fred with Annie and Melissa following, all three seated). A rider in
  the cabin without a chair was not: one in by another way, or one the
  player had stood up and then switched away from. They stood and
  wandered the aisle.
- Now anyone in the cabin other than the player walks to their chair (or
  a free one) and sits; the painted passenger in that chair goes, as for
  everyone seated. Only the player stands up, by walking, and sits again
  with the seat as before; no other walk takes a rider out of a chair.
  Six chairs: a seventh still stands.
- Looks: the plant, Ted and the Meteor sat on wheels, skates or in the
  air; now down in the chair. Characters from other games were drawn
  standing in front of the chair; now they sit as Maniac's own do,
  behind the seat's front, in the chair's middle, facing the front of
  the plane. The rat, the parrot and Murray sit up on the cushion, whole;
  the Creator and Chaos shrink to a seat's height.
- Tests: the seating probe (a late rider walks to a free chair and sits;
  another walk does not stand her; played, stood up and left, she sits
  again in her chair; as the plant she stays down in it); the appearance
  probe (the plant, Ted, the Meteor, the rat, Guybrush, the Creator and
  Chaos seated: in the chair, facing front, nothing below the seat's front,
  centred, no taller than a seat). Screenshots of thirteen looks seated
  were checked by eye.
- Independent review: nothing serious; fixed from it: a rider whose way
  to the chair is blocked sits after a while instead of trying forever;
  flights saved over six before seating are left as they were; a chair
  another device's player sits in, or held by someone no longer aboard,
  is not given out; a seated Maniac look shown again stays in the chair;
  no wheels or skates in a seat.
- Verified (Linux, the user's private copies): data suite 40/40 before
  the review fixes and again after them; startup. Not device-tested.

## Patch 0096 — Zak McKracken's missing people

User (2026-10-19): "There's a lot of characters missing from Zak
McCracken. Find and add them please"
- Found from the player's own Zak files (the original scripts' actor
  setups, names and costumes, read in the private analysis; every costume
  drawn to a sheet to identify it). Zak's game names about twenty people;
  the sandbox had Zak, Annie, Melissa, Leslie, a Caponian, The King, the
  Zaire shaman and villager, and (in their rooms only) the Nepal guard and
  the Guru.
- Added where the original scripts put them, in their costumes and
  colours (eight more Zak costumes imported, sandbox costumes 44..51): Lou
  in Lou's Loans, the stewardess on the plane, the bum at the Miami
  airport, the devotee at the San Francisco airport, the policeman at the
  Kathmandu guard station, the sentry at Stonehenge, the Skolarian (the
  projection deep inside Mars) in the projection chamber, and the pilot,
  who waits at the Seattle airport (his own scene, original room 131, is
  not imported). They stand there and can be talked to; personalities and
  lines are newly written.
- The baker, as in the original: the bakery has no inside; push or use
  its doorbell on Zak's street (13th Avenue, original room 3) and he
  comes to the upstairs window (drawn in front of its glass), says the
  bakery is closed, and goes again after about ten seconds; ring again
  and he stays and grumbles. (User: "he's always going to be at the
  window? That doesn't make sense".)
- They can be played: Zak's box on the character screen now lists them
  (with the Nepal guard and the Guru) after Zak's people. The character
  wears their costume in their colour; back as themselves, their own
  costume and colour return (the saved home look now keeps the colour;
  older saves keep working).
- Not added: the bird (seen when Zak flies as it), the Mars and Egypt
  variants of the four friends, and the TV newsreader. The baker (only
  ever seen at his window) is not offered to play.
- Tests: tools/test_zak_cast.py (every resident in their room, drawn; the
  baker away until the doorbell rings, then at his window speaking, kept
  by a second ring, gone after a while;
  every look played in its costume and colour; saved and loaded; Annie
  herself again; without Zak's files a look cannot be chosen and one worn
  is dropped); tools/test_cast.py (the Zak box lists them);
  tools/test_expansion.py (all ten residents, saved and loaded, and the
  actor returned); tools/test_appearance.py (home look encoding).
- Independent review: nothing crashing or corrupting saves on normal
  paths; fixed from it: a saved Zak look without Zak's files (a crash on
  drawing) is dropped, and refused when chosen; a home look captured
  before its tint; an older save's home look gains its colour; Zak's
  costumes failing to mount now say why; rollers, profiles and floating
  looked up by the look's own game; and an older slip: a guest whose
  appearance number began another's (Lemonhead) stepped aside whenever
  someone in the room played Maniac's own. The unused bird costume is
  not imported. (The baker and his doorbell were added after the review.)
- A save made while playing one of Maniac's or Zak's own cannot be loaded
  by builds before 0096 (the saved home look now carries the colour).
- Verified (Linux, the user's private copies): data suite 39/40 before the
  review fixes (the expansion probe expected nobody at the San Francisco
  airport; updated, passed); after them the full suite again; bootstrap,
  startup. Screenshots of each resident in their room and each look
  walking were checked by eye. Not device-tested.

## Patch 0097 — Maniac Mansion and Zak McKracken in Other worlds

User (2026-10-19, a screenshot of the Other worlds menu): "Why are maniac
and Zak still not listed on other worlds?"
- Other worlds listed only the ten games exported from the player's other
  copies; Maniac's rooms and Zak's places were reached through other
  entries (Return to Maniac Mansion, Zak's apartment, the airport, the
  pads, the tour).
- Now the menu starts with Maniac Mansion and Zak McKracken. Each opens a
  scrolling list of that game's places, named as the tour names them
  (Maniac's 37 rooms; Zak's 66 places, a run of numbered places such as a
  maze's cells by its first; not the plane or the van in flight, which are
  rides), and a choice takes the player there (the tour's own way in;
  rides, flights and the van are finished first, as elsewhere; not during
  the tour). Without Zak's files, Zak McKracken says so.
- Tests: tools/test_cast.py (both lists, each name once, the kitchen and
  Lou's Loans reached).
- Independent review of the iPhone part (it cannot be compiled here): no
  compile errors found; fixed from it: not during the tour, a spoken
  reason without Zak's files, the list closes before the trip (so what
  the arrival shows is not hidden; no double taps), no ride cabins in
  the list, Maniac arrivals named.
- Verified (Linux, the user's private copies): data suite 40/40 before the
  review fixes and again after; bootstrap, startup. The iPhone menu is not
  compiled yet; not device-tested.

## Patch 0098 — walks, seats, the plant and ladder, the van, the character screen

User (2026-10-19, thirteen screenshots), in their words:
- "The van likes to go here now when I tell it other places" (a Loom
  forest). Fixed: a reused world slot room kept showing the place mounted
  there before (the mount was skipped when the slot's room number
  matched); the slot now remembers which place it holds
  (_scummverseWorldKey) and is remounted for another.
- "Some characters don't occupy the plane seat right" (the VR dragon, a
  brown quadruped, the camel, the three-headed monkey), "There's a gap i
  circled where you can see the wall of the plane through the seat. Make
  that area black like it is for the painted characters." Seated
  characters from other games are now no wider than a seat (as well as no
  taller than someone seated) and kept against the seat's back; a chair
  someone sits in shows the painted chairs' black under its seat, not the
  wall.
- "Doug the mole man needs a walking character model. And he shouldn't
  be holding that bowl. His other mole friend from the game also needs a
  walking model." Sam & Max only ever draws Doug sitting, holding the bowl
  (the bowl is part of his body picture; no costume shows him standing).
  He now walks in his uncle Shuv-Oohl's stance and walk (the same kind of
  mole man; the game's own frames), with his own head and his own browns
  for the purple robe; no bowl. Shuv-Oohl (his friend in the cast) has a
  real side walk, which the game keeps under one facing; the export now
  walks him in it in every direction (it used his talking gestures before).
- "The camel's legs need to move when it walks." The game has the camel as
  one still picture; walking, its legs now swing from the hips (the near
  pair against the far pair, as a camel paces), eight frames made from
  that picture.
- "The nest monster isn't animated at all when it moves. Research how it
  moves in the dig cutscenes for inspiration." The Dig's own costume for
  it has a twelve-step crawl (its animation 15), which the export had
  missed (it found another picture first); it now crawls in it, turned
  either way, and stands in its first step. The cutscenes themselves
  (video) were not used.
- "The scale is not right here on mars with the balloon man". The landing
  site's long shot (the tram station) draws people at 27/62; characters
  from other games were drawn full size there. Now at the long shot's size.
- "There's supposed to be a ladder in Edna's room": its picture (object
  235) is now on; the way up it already worked.
- "Put the plant back in this room to be able to climb or the room above
  isn't accessible." Zak's Zaire villager had been put in actor 19, which
  is Maniac's man-eating plant, so with Zak's files the plant room's pot
  was empty. The plant has its actor back (older saves too); the villager
  is now a resident of the Zaire village (through the borrowed actor, as
  the other residents) and can be played from Zak's box. The climb is the
  hatch above the plant, as before.
- "In the games character menu, list the game's name, but not the
  character. ... Put "long press to play as another character. Make a
  progress bar for long press. ... Make Dr Fred the icon for maniac
  mansion instead of Dave. Make the purple tentacle the icon for DOTT
  instead of Bernard." Done: each box names its game, the note reads
  "Long press to play as another character", a bar fills while pressing,
  and the leads are Dr Fred and Purple Tentacle.
- The export version is 14: installed games export once more on launch.
- Tests: tools/test_van.py (every landing site, twice: the place shown is
  the one asked for); tools/test_cast.py (Dr Fred leads Maniac);
  tools/test_seating.py (held chairs black under the seat);
  tools/test_world_visit.py (Doug, Shuv-Oohl, the camel and the nest
  monster walk left and right in frames that change); tools/test_mars_air.py
  (someone from another game is drawn at the long shot's size);
  tools/test_zak_cast.py (actor 19 stays the plant with Zak's cast; an
  older save's villager becomes the plant again); tools/test_lights_doors.py
  (Edna's ladder drawn); tools/test_expansion.py (the villager among the
  residents); tools/test_world.cpp (the new catalog lists).
- Seats, second and third rounds (the user, seat sheets): "Guybrush doesn't
  sit in the plane seat right", "Ben from full throttle doesn't look right
  sitting in the plane seat": people from other games now sink to their
  waist in the seat (the seat's front hides their legs) as Maniac's own do.
  "The plant and 3 headed monkey should be facing the front of the plane.
  Create the views if you need to": the plant has a newly drawn side view
  (head, jaws and teeth, stem and leaves); the three-headed monkey a side
  view made from the island's monkey (its stance and walk, repainted) with
  three newly drawn heads ("The side view of the 3 headed monkey is a
  mess. Use the pic I attached for inspiration"), joined by necks; seated
  it is one solid black furry body under them ("Why can you see through
  the three headed monkey? Fix that": the window showed between its heads,
  back and tail). "The creator, nest
  monster, camel and virtual dragon need to be hilariously oversized ...
  conform [to the] general shape of the seats and look like they're
  crammed in them. The camel needs to be in a seated, not standing
  position": crammed between the seat's back and past its armrest, from
  the overhead bins down (kWorldSeatFits); the camel sits back in the seat
  ("a more relaxed pose with its leg on the armrest", "his head in a
  neutral position facing the right of the plane like everyone else"),
  forelegs folded, a hind leg slung over the armrest and drawn in front of
  the seat's front; the dragon's tail curls up the seat's back ("isn't sitting in the seat
  right"), and the nest monster ("reimagined sitting in the seat") lies
  sprawled, legs over the seat's back and armrest: seated frames made from
  their own stance at export (kWorldSeatPoses), as previewed to and
  approved by the user. "Murray from COMI needs to be completely
  redesigned": his white skull (costume 12) in Plunder Island's colours.
  "Doug the moleman is facing the wrong direction": his head is turned to
  face the way his body walks.
- Review fixes: an older save's plant is restored as soon as it loads (it
  waited for the character screen or a trip before), never while the
  player plays the villager, and leaves any ride; the character screen's
  hold bar is full when the list opens and survives a layout pass; its
  labels no longer overlap.
- Tests added: tools/test_world_visit.py (each seated pose: a picture
  facing right, and one the same size over the seat's front if it has
  one); tools/test_appearance.py (the camel, dragon, nest monster and
  three-headed monkey seated inside their chair, nothing below its front
  but the camel's leg over the armrest); tools/test_seating.py (every held chair, not only the reference
  one, black under its seat); tools/test_world.cpp (seated frames parsed,
  found from any facing, standing when not drawn; seat fits, poses and the
  drawn heads in the catalog).
- "Is Timmy the monkey added as a playable character?": Timmy is not in
  any of the twelve games' data (searched every file, plain and in the
  games' XOR encodings); Monkey Island's monkey and Monkey Island 2's Jojo
  are playable.
- Verified (Linux, the user's private copies): all ten games exported
  again (642 scenes, 261 characters); the seat picture matches the poses
  the user approved; data suite 40/40 before the review fixes and again
  after them and the monkey's fill; after the relaxed camel,
  test_appearance, test_world_visit and test_seating again; portable
  tests (world, portrait, mobile layout, seats, conversation, camera,
  tour, net) with sanitizers; bootstrap, startup. Independent review: no
  memory or crash finding; its save, test and iPhone findings fixed (a
  seated, mirrored one-way character pushed out of the seat's back, which
  no character does today, left as is). The iPhone screen is not compiled
  here; not device-tested.

## Patch 0099 — the camel sitting back in its seat

User (2026-10-19, after the 0098 camel picture and two more), in their
words: "that looks terrible. There's a section of him cut out. And he's
not sitting all the way back against the back of the seat"; then "He
should come further forward and make him bigger to fill up the seat. Why
is his leg sticking out like that ... His leg is still up unexplainably
and his back looks cut off against the seat".
- The camel's seated pose is designed against the cabin picture itself
  (with a copy of the exporter's pose code): upright, leaning back a
  little so its hump follows the seat's back from the top of the seat to
  the cushion (no gap, nothing cut off), head level facing the front near
  the overhead bins, filling the seat from its back to its front (the
  user, on a version that left the wall showing in front of its belly:
  "that gap in the seat again where you can see through the character to
  the wall of the plane"), its forelegs down in its lap and its hind legs
  in the seat, behind the seat's front. The gap between
  neck and legs that showed the window ("a section of him cut out") and
  the leg over the armrest (its hoof pointed up) are gone.
- A seat fit says where the picture starts (`back`, pixels right of the
  seat's place), and like everyone seated the big ones show nothing left
  of the seat's back line behind the seat's front. Pictures over the
  seat's front (0098) stay available; no pose uses one now.
- The export version is 15: installed games export once more on launch
  (a phone that ran 0098 would keep its camel otherwise).
- Verified (Linux, the user's private copies): all ten games exported
  again at version 15; the camel in the seat checked row by row against
  the seat's back and front (no wall showing in the seat but a pixel at
  its edge); test_appearance, test_world_visit, test_seating and
  test_world_setup; tools/test_world.cpp with sanitizers; bootstrap,
  startup. The full data suite was last run on 0098 (40/40). Not
  device-tested.

## Patch 0100 — the Creator walks and talks; the hold ring; riders jump into the van

User (2026-10-20, a screen recording and notes), in their words:
- "Creator isn't animated. Just moves around lifelessly and still." The
  Dig never walks its Creator: its costume's walk, stand and talk are one
  still picture (its other animations only gesture, on the spot). It now
  walks on swinging legs made from its own stride (kWorldLegSwings), talks
  with its own head and mouth (animation 13, a costume variant), and turns:
  the game drew it facing right only, so facing left is its mirror
  (kWorldOneFacings). A variant's own animations each start from its
  set-up at export (its talk had left its arm tucked in every later
  picture). In a seat, the big ones without a seated pose keep their
  standing picture's size and place, so talking does not resize them.
- "Please make the long press green and goes around the main characters in
  the first menu. It should take .5 sec." A green ring runs round the box
  while it is held, half a second.
- "Can other characters ride in the van? None of the other npcs jump in
  with me": only those already in its cockpit flew along (a companion who
  followed the player in). Now whoever stands where the van is parked jumps
  in when the player picks a destination (not anyone on the bus, a flight
  or the tram), flies along unseen and steps out beside the player at the
  landing. tools/test_van.py checks someone standing by the van rides
  along and steps out.
- "How big of a deal is it to make the characters in the long press menus
  visual like the first menu?" Answered (a face for each of the about 260
  characters, drawn when a list opens, and a grid like the first screen:
  a patch of its own); not started.
- The export version is 16: installed games export once more on launch
  (the Creator's frames are made at export).
- Verified (Linux, the user's private copies): all ten games exported
  again at version 16; the Creator's walk, talk and turn checked frame by frame
  (a moving preview made for the user); test_world_visit (the Creator now
  among the walkers), test_appearance, test_seating, test_van, test_bus,
  test_flights, test_companions; tools/test_world.cpp with sanitizers;
  bootstrap, startup. The hold ring is iPhone code, not compiled here.
  Not device-tested.

## Patch 0101 — wanderers from the other games; chat for 64; fairer colours

User (2026-10-20), in their words: "I just want more actors roaming outside
their home games. It'll be more interesting to find them in odd places";
"Only 3 per room? I'd like that to be more dynamic"; "No save some slots,
enough to be safe"; "Is it always the same 40 wanderers or do the characters
change"; "I don't need them all on the plans or in the van, following me".
- Wanderers (common/scummverse_wander.*, engines/scumm/scummverse_wander.inc):
  forty of the other games' characters are out at once, over every place
  there is (the mansion's rooms, Zak's, the other games' exported rooms but
  maps and floor plans: 743 places with all ten games here). Off-screen each
  is a saved note, who and where (variables 256..335); now and then one
  moves on through a door of its place, sometimes anywhere at all, sometimes
  to where another is (so a few gather). Every two and a half minutes one
  goes home and someone not out yet sets out from home, so everyone gets a
  turn. A wanderer is not at home meanwhile (never two of anyone). While the
  player watches a place nothing there changes but arrivals.
- In the viewed place they are drawn as visitors, as many as its floor has
  room for (one per 40 pixels, fewer for those already there; 26 slots at
  most): actors of their own outside the game's actor table, since Maniac
  numbers its objects from where the actors end. They stroll a little,
  greet the player once in their own colour, walk in from a side when they
  arrive, wear air gear on Mars, and step aside while someone plays them.
  They do not follow, ride or sit on the plane.
- Chat: anyone visiting can be chatted with (the people row, a tap while
  picking, group talk). Participant lists are 64 bits wide (talk IDs: 1..24
  the sandbox's people, 25..29 a scene's own, 30..55 wanderers). Follow is
  offered only for the mansion's and Zak's people.
- Colours: other games' characters take every palette slot the room leaves:
  240 in the mansion and Zak's rooms (64 before), after the scene's own in
  other worlds, where a scene that expects many characters on arrival keeps
  fewer colours (down to 128). They share them fairly: each in turn keeps
  its own most used colours, passing over near-duplicates (in a test of ten
  characters in 64 colours the worst one's average error fell from 10.2 to
  3.9).
- Tests: tools/test_wander.cpp (ASan/UBSan, TSan); tools/test_wander_engine.py
  (data suite); test_conversation and test_scene_talk past 32 IDs;
  test_world.cpp fair shares; test_appearance and test_world_visit send a
  checked place's residents home first; colour checks use
  WorldBridge::guestFirstSlot. Engine tests keep wanderers home
  (scummverse_wanderers=false in run_probe's config) except test_wander_engine
  and test_world_visit, so their rooms stay as each expects.
- Independent review, fixed: strips the engine draws again (an object's
  state, speech gone) now take visitors there with them (defensive: in this
  build visitors are drawn every frame anyway, so the new check passed
  without it too); a scene's own characters stand clear of visitors; a
  damaged character file is passed over rather than blanking everyone
  there; chat drops visitors once when they are cleared (a load), so a slot
  is never taken for whoever had it; more of the cast set out when games are
  exported later; a crowd is named up to ten in the chat prompt; talk masks
  past the last wanderer are ignored; colour counting by palette index.
  Left as is: a visitor's frames are read and all characters refitted when
  someone arrives (rare; a few frames).
- Verified (Linux, the user's private copies): the full data suite (41/41,
  with test_wander_engine new); tools/test_wander.cpp (ASan/UBSan, TSan);
  test_world.cpp, test_conversation.cpp (sanitizers); test_talk_runtime.py
  (ASan/UBSan, TSan, no weights); bootstrap, startup, package_ipa. The chat
  screen changes (scummverse_talk_ui.inc) are iPhone code, compiled only by
  Apple CI. Not device-tested.

## Patch 0102 — every game an equal share of the wanderers; they come by

User (2026-10-20, on the 0101 IPA): "I'm in maniac mansion and i don't see
wandering characters from other games aside from the ones from Zak". Spread
evenly over 743 places, the mansion's 37 rooms held about two of the forty
between them (a room about one chance in twenty). A first answer weighed
the mansion's and Zak's rooms four times; the user: "I kind of like that
they're random and could be anywhere instead of steering them to maniac
mansion" and "is there a better way to do this to give every game equal
weight?" Now:
- Every game has an equal share (kWanderGameShare): a place weighs one game's
  worth over its game's places, so each of the twelve (the mansion, Zak's
  world, the other ten) holds about three of the forty whatever its size;
  who sets out is chosen the same way (a game's characters share one game's
  worth, Wander::Cast weights), so a big cast does not crowd out a small one.
- One move in twenty heads for a room next to the player's (Rules::toward),
  so they are met wherever the player goes; from there a door may bring
  them in. Those in the player's room stay while watched, so nobody moves
  in once four are there (Rules::crowd; the user: "Should we try 4?").
  Engine probe: set out in all twelve games; ten minutes by the kitchen,
  eight in the mansion and one or two in the kitchen at a time.
- Asked for next (not in this patch): the mansion's and Zak's own characters
  in the wanderer pool too.
- Tests: test_wander.cpp (toward the player, the crowd, weighted places and
  characters; ASan/UBSan, TSan); test_wander_engine.py logs where they set
  out (at least six games) and checks they come by.
- Verified (Linux, the user's private copies): the full data suite (41/41);
  test_wander.cpp (ASan/UBSan, TSan); bootstrap, startup, package_ipa. Not
  device-tested.

## Patch 0103 — everyone out, all over the place; small ones; Zak's broom

User (2026-10-20): "Lets do 2 everyone is out", first leaning toward their
own game, then "I take it back. Make it completely random. I want to see
them all over the place"; "If one of the wandering characters is small, like a parrot or a
rat or a crab, can we make that not count toward the 4?"; "Can we make the
broom from Zak a playable character?"
- Everyone out: every other-game character whose frames are exported (261
  with all ten games) is always somewhere; there is no limit of forty and no
  taking turns. Setting out and going anywhere pick any game, every game an
  equal share (Rules::lean, the chance to stay in the character's own game,
  is 0; one number to change); moves through doors, gatherings and the pull
  toward the player as
  before (with everyone out, about one in a hundred and twenty-five moves
  heads for a room next to the player's). A scene's own characters are out
  too, so its residents are seen as visitors wherever they are (engine probe
  at the start: 30 of 261 in their own game, 25 in the mansion, 27 in Zak's
  places, all twelve games visited; standing ten minutes by the kitchen it is
  at its four most of the time).
- Saved: the cast's signature in variable 256, everyone's place two to a
  variable in 257..398 and 529..599 (room for 426); a save from before 0103,
  a new game or a different cast (games added since) sets everyone out
  afresh.
- Small ones: animals and critters (kWorldSmall: parrots, rats, the crab,
  seagulls, cats, the rabbit, owl, sheep, chicken, ghost pig, critters, both
  Murrays, the monkeys, Jojo; measured at half a person or less against each
  game's lead, people exported sitting left out) never count toward the four
  in the player's room or toward how many a room shows.
- Zak's broom (his costume 33, read from the player's Zak files like the
  0096 cast; sandbox costume 52): playable from Zak's box on the character
  screen, brown, hopping along on its handle (a bouncer like Murray; on the
  ground at rest), needs no air on Mars; newly written personality and lines.
- Asked: the alien with the fake nose and glasses is Zak's Caponian (actor 8,
  costume 38), already playable from Zak's box.
- Tests: test_wander.cpp rewritten (everyone out anywhere, a lean, weights, the
  crowd and small ones, saving two to a value; ASan/UBSan, TSan);
  test_wander_engine.py (everyone out and saved, Monkey Island's residents
  out, four in the living room, half an hour passing, save and load, ten
  minutes by the kitchen); test_zak_cast.py (the broom hops and lands);
  engine tests keep wanderers off (residents at home), so test_world_visit and
  test_appearance are as in 0100.
- Verified (Linux, the user's private copies): the full data suite (41/41,
  run with the lean at three in four; the switch to completely random then
  re-ran test_wander.cpp and test_wander_engine.py, the only tests with
  wanderers on); test_zak_cast five times (the broom); bootstrap, startup,
  package_ipa. Not device-tested.

## Patch 0104 — the new engine (preview): a place at full resolution in full colour

User (2026-10-20): "Let's start this: New engine module (recommended): a new
'game' inside ScummVM, written just for the sandbox. It uses ScummVM's code
to read all twelve games' files but sets its own rules: no character limit,
the iPhone's full resolution, full color. Everyone is equal." and "Can we
make it modular? so if I want to use DOS V1 or V2 maniac mansion, or DOS or
FM towns, fate of Atlantis, they're interchangeable?"
- Step 1 of 5 (see ARCHITECTURE, Sandbox engine): a new ScummVM engine,
  `engines/scummverse` (game id `sandbox`), alongside Maniac. It shows a
  place exported from the player's own games (the worlds cache) on the
  device's own pixels held sideways, in true colour (each scene and each
  character in its own colours, no shared palette), the place's people and
  the game's lead, who walks where the player taps, through the walk boxes,
  at a person's size for where they stand, the camera following in wide
  rooms. No limit on characters.
- iPhone: Worlds > New engine (preview) saves Maniac and opens it; its
  Worlds button has Back to Maniac Mansion, which loads that save. Maniac
  says why when it won't open it (no other game installed yet, a WiFi game,
  the tour, the save failed); a new engine that cannot start goes back to
  Maniac on its own. Tapped during a cutscene, it opens when the cutscene
  ends (as other Worlds requests do). The other buttons (Talk, Camera and so
  on) do nothing useful there yet; if iOS closes the app while it is in the
  new engine, the way back to that Maniac save is not kept yet.
- Not yet: doors between places, everyone out, Maniac Mansion and Zak in
  it, chat, the character screen, camera and tour, rides; editions as
  interchangeable adapters is designed (ARCHITECTURE), not built. Areas a
  game joins only through its own box connections (not exported yet) are
  walked as near as the boxes allow.
- Review fixes: flat walk boxes (lines and points, 42% of the exported
  boxes) no longer join boxes along their whole line (in 128 places
  characters could have walked through walls); a scene is moved, not copied,
  into place (up to 44 MB scaled); the screen is drawn again only while
  someone walks; the iPhone menu asks a flag, not the settings, whether the
  new engine runs.
- Tests: test_stage.cpp (view, boxes, flat boxes, paths, colours, drawing,
  walking, spots; C++11, ASan/UBSan); test_startup (a made-up place shown and walked;
  the sandbox without places refused); test_sandbox_engine.py (the first
  place, every exported place (642) with its people and each lead walking,
  Maniac -> sandbox -> Maniac back in the same room from the same save, and
  the same with a place that cannot be read).

## Patch 0105 — the new engine: walking as the games do, doors, everyone out

User (2026-10-20), on 0104: "New engine feels off is it the walking speed?",
then "Just keep building in the order you think is right."
- Walking as the original games do: a step every six ticks, at most 8
  pixels across and 2 up or down the scene (the SCUMM default walk speed;
  doubled for Curse of Monkey Island's finer pixels), one walk frame a step
  (no more sliding feet), smaller steps far away. The camera stays still
  until the one played comes within a quarter of the screen of an edge, then
  scrolls to centre them.
- Doors in all ten games: tap a door, the one played walks to it and goes
  through to the room beyond, arriving at its door back (the generated door
  maps of 0062 onward; maps go at once). Neighbouring walk boxes the older
  games draw two pixels apart now meet (Loom, Indy 3), and with no door to
  arrive at the player starts where the most doors are in reach. Engine
  test through every door of every place: 1657 tried, 1570 through to their
  room (1461 of the 1475 with a door back standing at it), 23 to a door
  under the tap, 64 stopped short (areas a game joins only through its own
  box connections, which the export does not save yet: Indy 3, Loom, Curse
  of Monkey Island mostly).
- Everyone out, no limit: every installed character from every game is
  somewhere among 606 places (as Maniac's wanderers: equal share per game,
  the pull toward the player, four at most drifting into the player's room,
  small ones aside); a place shows everyone there; those arriving while the
  player watches come in through a door and walk on; those there stroll.
  Where the player is and where everyone is is kept between visits
  (scummverse-sandbox.state in the saves: at each room, every half minute
  and on leaving).
- Review fixes: doors without a walk-to point (all of Day of the Tentacle's,
  Sam & Max's, Full Throttle's, The Dig's and Curse of Monkey Island's) are
  reached and arrived at the bottom middle of the door, as in Maniac's other
  worlds (they put everyone in a corner); the place and the one played are
  checked before the stage changes, and a place that cannot be shown leaves
  the player where they were; a character whose file is damaged is not
  tried again; floor plans are walked; of doors only near a tap the nearest
  wins; the camera keeps up in Curse of Monkey Island; scummverse_place wins
  over the kept state; the iPhone menu lists a game when any named place of
  it is installed.
- iPhone: the new engine's Worlds menu adds "Go to <game>" for each
  installed game (its first named place); Back to Maniac Mansion as before.
- Tests: test_stage.cpp (steps of 8 and 2, legs in step, the edge camera
  both ways and never losing the walker, lookAt, gaps of up to 3 pixels meet
  and 4 do not, groups of boxes, doors under before near and the nearest of
  those near); test_sandbox_engine.py adds every door of every place (at
  least 95 in 100 through, 99 in 100 of those with a door back standing at
  it) and half an hour with everyone out (someone arrives, everyone shown is
  on stage, the state written and read back).

## Patch 0106 — the bigger export: box connections, colour cycles, objects' names and pictures

User (2026-10-20): "Will the original objects eventually be implemented which
you can pick up and interact with or will it remain empty? New engine is
supposed to retain the look and feel of the originals." Step 2b of the plan
(objects and verbs are 2c).
- Export version 17 ("SVW5"): every installed game exports once more on the
  next launch. Each scene adds the game's own box connections, the room's
  colour cycles, and every object's name and pictures (without it, and in
  each of its states). On the desktop all ten games re-exported in 73
  seconds: 642 places (641 pixel for pixel as before, one pixel apart in one
  room drawn by an older build), 8562 objects, 5529 named, 4798 with
  pictures (33 MB of pictures; the cache grows from 95 to 103 MB), colour
  cycles in 143 places, box connections in all.
- The new engine: water, fire and lights move where the room cycles its
  colours (the scene kept as palette indices, a quarter of the memory); the
  games' own box connections join areas they keep apart: doors gone through
  rise to 1608 of 1657 (97 in 100; the 49 left are joined only by the games'
  scripts: stairs, ladders); objects can be shown in any of their pictures
  (used by 2c).
- The old engine reads the new scenes and ignores what it has no use for.
- Tests: test_world.cpp (SVW5: connections, cycles, names, pictures and the
  one shown, truncation, nothing left over, older files); test_stage.cpp
  (connections join boxes apart, touching still meet, a matrix naming the
  file's own box numbers; colour cycles against a port of the games' own
  palette code: up, down, overlapping, to 255, the older sweep, one step a
  update; showing a picture renders as the scene with it, in the middle and
  at the edge, on screens larger and smaller than the scene); the engine's
  all-places test shows every object picture, then the one the scene shows,
  and test_sandbox_engine.py checks names, pictures and moving colours, and
  every exported cycle (at least 4 ticks a step, in range); the door test
  asks 96 in 100.
- Two independent reviews (the stage, the export), fixed before packaging:
  the older games' sweep was exported a step a tick (the frame timer is not
  running at export): now a frame (4 ticks); the others' cycles at least a
  frame, the older games' only those started, none with EGA dithering, none
  left from the last room; overlapping rotations add up (a step an update);
  in rooms their scripts set up (Monkey Island's maps, Indy 3's, the Dig's
  presets) objects' pictures did not match the room as shown: each picture
  is now the scene with what its state changes, and the file says which one
  the scene shows (always exactly the scene; checked in every place); a room
  without a box matrix no longer reaches the engine's assert; heights the
  drawing rounds are put back; objects outside the room's rows, older
  objects without an image and rows under 8 are not drawn; up to 16 states;
  name escapes skip their arguments; an empty picture is refused.
- Measured after the fixes (desktop, Linux): 642 places, pixel for pixel as
  in export 16 but one pixel in one Monkey Island 2 room (the same in every
  run now: drawn by an older build); 4798 objects with pictures, 4280 of
  them changing between pictures (the rest look the same in every state, as
  the game draws them here); colour cycles in 143 places, all at least 4
  ticks a step, moving in 142 within the test's walk.

## Patch 0107 — the games' own verb panels in the new engine (step 2c, first part)

User (2026-10-20): "New engine is supposed to retain the look and feel of
the originals." and "Just keep building in the order you think is right".
- Export version 18: each game with a verb panel (The Secret of Monkey
  Island, Monkey Island 2, Indiana Jones and the Last Crusade, Indiana Jones
  and the Fate of Atlantis, Day of the Tentacle) also exports
  "<game>-ui.svi": its own start (boot script) is run on at once, without
  waits, speech or cutscenes (the music's clock moving with the frames,
  Monkey Island 2's copy protection answered: the engine takes any
  answer), until its verbs are up; then the panel is taken as the game
  draws it, with nothing carried and the sentence line empty, each verb
  also drawn highlighted, the inventory's slots and arrows, the player's
  talk colour, and two letterings (the sentence line's and the talk's)
  drawn letter by letter by the game itself. Under a second for each game
  on the desktop. Loom, Sam & Max and the three later games have other
  interfaces (later). The catalog says which verb is which (by the games'
  own verb numbers) and where the inventory is.
- The new engine shows the panel under the scene, both at one scale, as
  the original's screen has them. A tap on a verb chooses it (lit as the
  game lights it; the sentence line names it; a tap near its letters counts),
  a tap on it again lets it go. A verb then a tap on a thing (named and
  shown here) walks there and does it, by plain rules (the games' scripts do
  not run): look and "what is" name it (said over the head in the game's
  talk lettering), open and turn on show its picture 1 when it shows none,
  close and turn off picture 0, push and pull its next picture, pick up
  takes something small that is shown (not a door) into the inventory (names
  or pictures, as the game has it; arrows when there is more) and the place
  is without it; the rest is said not to work. What was changed and taken
  stays (state file "SVS2"; "SVS1" still read). Without a verb, taps walk and
  go through doors as before. scummverse_verbs=false hides the panel.
- Export fixes on the way: an object state past the one shown that the game
  draws as mostly (80 in 100) one block of a colour found nowhere around it
  (a fill it never shows: Monkey Island 2's doors in magenta, Loom's in its
  primary colours) ends its pictures (40 objects in the ten games, none of
  them showing it; dark doorways keep theirs, their black is around them);
  verb names keep the games' joined letters (Day of the Tentacle's "oo").
- Known: most small things are not in the scenes, as their games' scripts
  put them there at run time (the SCUMM Bar's mugs, Day of the Tentacle's
  battery): little to pick up yet. Next: the export with the games' own
  object states (each room as its entry script leaves it).
- Tests: tools/test_panel.cpp (the file whole or not at all, half-empty
  rectangles refused; layout and taps, a verb's place on screen holding
  exactly its taps at any scale, rows kept on screen; drawing; names cut at
  their slot, pictures fitted, a missing slot left alone; scrolling and
  arrows; on screen at the scene's scale; lettering, wrapping and speech;
  the rules; things carried from a scene); test_sandbox_engine.py "verbs":
  5 panels, 52 verbs each chosen and let go by a tap; in each game's first
  place look (the line said, then gone and the screen drawn again), open,
  close, push, a door refused, and (in 4) out of reach nothing done; pick-ups
  (2 things small and shown among the five first places), not to be used
  again, each looked at by a tap on its slot (a thing carried shows in each
  game's own way: a name, or its picture); all kept through the state file
  and shown gone after a reload. With the panel the scene is drawn
  smaller: the door test's taps land differently (1600 of 1657 through
  against 1608).
- Two independent reviews (the export; the panel and the sandbox), fixed
  before packaging. Export: the start now begins clean (no script slot,
  cutscene or override left from the places' export, no exit script of the
  last room: the engine would stop on a cutscene left open); letters only
  as many as each charset has (Indiana Jones 3's has 226: garbage past it),
  none for two-byte lettering, each drawn after a space (its own offset as
  within a line), "nothing" chosen after the charset's colours are loaded;
  slots and arrows kept on the panel (else none), names ending at an arrow
  (Indiana Jones 3's); Mac Indiana Jones and FM Towns refused (their verbs
  are drawn elsewhere); Monkey Island 2 Mac's boot checked as the engine
  does; the verbs counted again at the end. Panel and sandbox: a slot of
  no size skipped (it crashed in a fuzzed file); a thing taken is no longer
  a thing there (it could be opened back into view and taken twice); a line
  said or gone and a picture shown draw the screen again; what takes a hand
  needs the one played near it ("I can't reach that."); shut doors and other
  things in a game's state 0 are things too; the panel's rows kept on
  screen; push and pull switch two-picture things, else step through those
  showing them; a verb's place on screen matches its taps exactly; a verb
  chosen cancels a door walked to; a door not reached clears the sentence
  line; a thing is carried as it was shown when taken; a panel that cannot
  be read is reported.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0108 — things where the games put them, and what each answers (step 2d)

User (2026-10-20): "Will the original objects eventually be implemented which
you can pick up and interact with or will it remain empty? New engine is
supposed to retain the look and feel of the originals."
- Export version 19: after its verb panel, each of the five verb-panel
  games also exports "<game>-things.svo": from the game's own start, each
  of its places is set up again and its entry script run as on arriving
  (cutscenes skipped as a player skips them, lines not waited for; the
  game's variables and object states put back after each room), and each
  object's picture then is kept, with the verbs its own script answers
  (its own entries in the object's verb table, not the catch-all one;
  also whether it has a catch-all entry, and whether its game has it
  untouchable or carried there). The things pass runs only after its
  panel was captured. The scenes themselves are unchanged, byte for byte
  (all 903 scene and character files against the 0107 export). On the
  desktop: Monkey Island 78 of 81 places set up, Monkey Island 2 69 of 71,
  Indiana Jones 3 99 of 111, Fate of Atlantis 68 of 72, Day of the
  Tentacle 49 of 50 (the rest are left by their own scripts); objects that
  can be touched there and answer some verb: 530, 414, 471, 406, 348;
  answering pick up: 73, 196, 150, 90, 125 (untouchable or carried: 887,
  224, 1035, 546, 258).
- The new engine shows each object as its game has it there (what the
  player opened, closed or took still wins): 412 things in 140 places,
  the SCUMM Bar's pirates at their tables among them. Each verb now also
  needs the thing to answer it in its game (open or close, on or off, push
  or pull, pick up): a mug can be taken, a pirate not. One with only its
  catch-all entry is not known (every verb does as before); one its game
  has untouchable or carried there is not a thing in the sandbox. A door
  its game switches by an object's picture is a door only while shown.
  Without a things file (Loom, Sam & Max, the later games) the plain rules
  are as before. The things file is read whole or not at all (any order,
  a room only once, at most 1024 rooms and 4096 objects a room); one that
  cannot be read is told once and kept as none.
- Running every room's entry script out of its story's order reaches the
  engine's own checks (a script stopped or ending inside a cutscene, the
  cutscene stack, nesting too deep, a script of another room): while
  exporting only, those are told and passed over instead of stopping the
  app (scummverseScriptError; normal play stops as the originals did). The
  scene export now starts each room with no script, cutscene or override
  left (one left made the engine stop at the script's end), the things pass
  keeps the screens the game set itself (the places' layout made a script
  that restores the verbs draw past the room's screen: memory damage), and
  the panel capture starts from the engine's own start screens. Review
  fixes: a script slot taken while exporting keeps no cutscene or override
  of the script stopped there (one skipped later would have run the slot's
  new script from the old one's place, or a dead slot: a crash); a
  cutscene is skipped only where the script that set it still runs; the
  sentence and object-drawing queues and the game's inventory list are put
  back each room; Day of the Tentacle's arrays an earlier room freed read
  as 0; restart, pause and quit from a room's script are passed over; a
  quit or a failed pass writes no things file, and an older export's panel
  or things file the new one lacks is emptied. Mac and FM Towns Indiana
  Jones (no panel captured) get no things file.
- Tests: tools/test_panel.cpp (the things file read whole or not at all,
  in any order, a room once, at most so many, kept per game, one that
  cannot be read kept as none; the rules with what a thing answers, its
  catch-all entry alone not known); test_sandbox_engine.py: the things
  placed (412 in 140 places), the SCUMM Bar's file as its scripts answer
  (a pirate looked at and talked to, not taken; the kitchen door opened
  and closed; no mug out at the start), doors picked as the sandbox has
  them (1602 tried, 1537 through, 13 elsewhere, 52 short, 71 not there or
  shut by their game), and the verbs test picks things by what they
  answer, passes over one out of reach for another, and looks through each
  game's places until that game has pushed, taken and declined one: 5
  pushed, 5 taken (each looked at in its slot), 5 refused because their
  games do not take them, 5 doors refused, 1 out of reach.
- Known: Loom, Sam & Max, Full Throttle, The Dig and Curse of Monkey Island
  have no things file yet (their starts are not run). Not every entry
  script leaves its room as a player finds it (cutscenes skipped). Actors,
  verbs and renamed objects are not put back between rooms (only object
  states are kept, so these do not reach the file). A verb its script
  answers may still be a refusal there (a sign that answers pick up with
  a line): the sandbox then takes what the game would not. At its start
  Monkey Island puts no mug out in the SCUMM Bar (untouchable, unseen), so
  none can be taken there yet.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0109 — the mansion in the new engine (step 2e, first part)

User (2026-10-20): "Only 10 games? There's 12."
- Maniac Mansion's own places now come into the new engine like the other
  ten games': 37 rooms of the mansion (the tour's stops), 73 doors from the
  original engine's own passage table (the rides out left out), and 17
  people (the seven kids, Dr Fred, Sandy, Nurse Edna, Weird Ed, Dead Cousin
  Ted, both tentacles, the Purple Meteor, the Meteor Police, the plant),
  with newly written personalities and lines. Dave is its lead. The menu
  in the new engine lists the mansion with the other games; "Back to the
  original engine" returns to the game itself.
- The export handles the oldest games' differences (SCUMM v1): rooms lit,
  walk boxes and positions in their 8 by 2 pixel units, object pictures by
  the "on" bit (doors, the fridge, the lab's vault open and closed), no
  made-up picture for objects without an image, each person in their own
  colours, and each room drawn from the game's own starting states (the
  garage shut, the shower curtain drawn, no parcel yet at the mailbox).
  Only the edition the original engine's tables are checked against (DOS
  V1 English) is exported, from the folder the game itself starts from. On the desktop: 37 of 37 rooms, 17 of 17 people, 217 of 391
  objects with a second picture. The other ten games' scenes, characters
  and panels are byte-identical to 0108.
- The original engine leaves the mansion out wherever it lists other
  worlds (menus, visits, tour, wanderers, character screen, status), so
  nothing changes there.
- The things pass and the panel capture now give the same result every
  time: what a room's or a start's scripts pick at random is picked the
  same (a seed per room). Two exports compared: every things and panel
  file identical (before, a pirate's pose or an animation frame differed
  run to run: 412 or 418 things placed).
- On the iPhone, the mansion is exported from the game's own folder at the
  next launch (one more game set up).
- Review fixes: the world-visit, character-screen and wanderer tests leave
  the mansion out where the original engine does; a visit to a mansion
  place as "another world" is refused; the mansion's folder is taken from
  the game's own start (command line included), never searched for.
- Known: the new engine's wanderers' saved places reset once (its cast
  grew). In the oldest games an item's "on" picture is the place without
  it (taken): for the mansion's coming verb panel, pick up will need that
  way round. Zak McKracken is not in yet (its doors in the original engine are
  numbered for its rooms as imported into the mansion; next). No verb panel
  for the mansion yet (tap to walk, doors as elsewhere). The plant's
  standing frames show its growth stages by facing.

## Patch 0110 — Zak McKracken in the new engine (step 2e, second part)

- Zak McKracken's own places come into the new engine in Zak's own
  numbers, exported from its own files (the folder named zak, as the
  original engine finds it): 99 places (Zak's apartment and street, the
  airports, Seattle, Zaire, Nepal, Egypt and the Sphinx's maze, Stonehenge,
  Mexico's temple, Peru's carving, the Bermuda craft, Mars and its mazes)
  and 240 doors, translated from the original engine's own Zak tables
  (tools/world_maps.py; the import's object numbers turned back into
  Zak's with the order of each room's objects, private analysis of the
  user's copy in build/foreign/links/zak-objects.json). Sixteen people
  (Zak, Annie, Melissa, Leslie, the Caponian, the King, the shaman, the
  Guru and the residents) in their own colours (kWorldOwnTints), with the
  personalities the original engine's residents already have.
- The places Zak's scripts make of one wide room (its logical rooms: the
  jungle paths, Kinshasa and the hut, the Mars hostel, the mazes' cells)
  are each cut to the part their entry script lets the camera show, the
  walk boxes outside switched off (a room of its own is shown whole). Every
  Zak room is exported with its entry script, so it keeps the colours and
  walk boxes the script sets (the phone company's cyan, the Guru's brown);
  what the script changes in the game is put back after its room. A room
  whose script takes the player on at once (the Seattle airport, the
  Sphinx maze's dead end) is shown as drawn, without it. Four doors whose
  object their place's window leaves out are left out (Mars passages 202
  and 204 back to 193, the shaman's hut, Stonehenge's), counted where
  Zak's places are exported. An edition other than the checked one is
  tried once, not at every launch.
- On the desktop: 99 of 99 places, 16 of 16 people; the sandbox's door test
  walks all 240 of Zak's doors through. The other games' and the
  mansion's files are byte-identical to 0109.
- Known: the airports look alike apart from their signs (as in the game);
  travel between them is by plane, which the new engine does not ride yet
  (each airport is reached from its city's places, or from the menu). The rides (plane, bus,
  tram, the van) come with step 5. The baker, drawn only at his window, is
  left out. The original engine's own fixes to some Zak places (the
  Society's stairs, the Sphinx's secret entry, Seattle's loose dirt) are
  not applied (the game's own states are). On the desktop the export finds
  Zak in a folder named zak where the app starts (on the iPhone,
  Documents/zak, as the original engine does), not scummverse_zak_path.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0111 — the mansion's and Zak's verb panels in the new engine (step 2e, third part)

- The mansion and Zak McKracken now play in the new engine with their own
  verb panel, as the other five games with one do: the mansion's 15 verbs
  (Push, Pull, Give, Open, Close, Read, Walk to, Pick up, What is, Unlock,
  New kid, Use, Turn on, Turn off, Fix) and Zak's 14 (with Put on and Take
  off), in green under the place, the sentence line, the four inventory
  slots with their arrows, and the game's own lettering. Each is captured
  by the game's own SCUMM engine from its start (the mansion's verbs from
  the script that sets them up, Zak's from its boot script; then drawn on
  a cleared verb screen, each verb also lit, the slots, arrows and
  sentence line where the engine itself puts them, each letter drawn by
  the game).
- What the verbs do there: Read names a thing as Look does; Unlock opens
  what opens ("It isn't locked." otherwise); Fix, Put on and Take off
  answer with a plain line ("It doesn't need fixing."); New kid plays the next of the game's people
  (its cast's order, all of them, not only the kids) where the one played
  stands. Pick up follows the oldest games' way round: a thing is there in
  its first picture and gone once taken (its "on" picture), and is carried
  as it looked. Where things are, and what each answers, comes from the
  mansion's and Zak's own scripts, as for the other games (0108).
- On the desktop: the sandbox's verb test goes through 7 panels (the
  mansion's and Zak's included): 81 verbs chosen, things looked at, opened,
  closed, pushed, 7 taken and looked at in their slot, doors and what
  their games do not let be taken refused, out of reach refused, New kid
  played and back. The other ten games' files and the mansion's are
  byte-identical to 0110; of Zak's, its people change (in colour) and two
  places (12 and 19, scripted) change once with a fixed seed for what
  their scripts pick at random.
- Fixed from 0110: Zak's sixteen people came into the new engine all in one
  grey (after a scripted room the export put the game's variables back,
  the lights with them, before drawing its people; the oldest games draw
  everyone grey with the lights off). They are now drawn lit, in the
  colours Zak's scripts give them through its own colour table (Zak in
  green, Annie in magenta). The sandbox test now fails on any of the
  mansion's or Zak's people in that grey alone.
- Review fixes: the panel capture no longer runs the exit script of the
  last place exported when Zak's start changes rooms (no effect on today's
  files, which stay byte-identical); it also needs four verbs up at the
  end, not only at some point, and only verbs shown in full; New kid passes
  over someone who cannot be shown, and says so when no one can. The export
  version stays 19: no phone has had a 19 export yet (0106 to 0110 are not
  pushed), so the first build with 0111 exports every game afresh.
- Known: the arrows are drawn as arrows, not the game's own glyphs. The one
  played before New kid is not left standing there. The mansion's lines are
  shown in white, not each kid's own colour (its panel is captured from the
  script that sets up the verbs, before any kid is chosen). The games' own replies
  are not used (their scripts do not run in the new engine): the lines are
  the new engine's plain ones.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0112 — Sam & Max's own controls in the new engine (step 2f, first part)

User (2026-10-21): "Keep going". Step 2f: the games without a verb panel
(Loom, Sam & Max, Full Throttle, The Dig, The Curse of Monkey Island) each
have controls of their own, drawn by their scripts when the player taps or
holds, not set up at their start. Sam & Max first; The Dig, the verb coin
(Full Throttle, Curse of Monkey Island) and Loom's distaff follow.
- Sam & Max plays in the new engine with its own controls: its box button
  in the corner of the scene; the pointer as the verb (walking, look, use,
  talk, pick up, its own five pointers), a right click (two fingers on the
  iPhone) bringing the next round as the game does; a tap on the button
  opens the box over the scene (the game's own cardboard box, its verb
  icons along the top, what is carried in its cells), an icon there is the
  pointer from then on and shuts it, as do its own box icon, a tap off it
  and a right click (its box icon also gives the walking pointer back); a
  carried thing tapped there is looked at (named) or
  has the pointer's verb used on it. Speech is in the game's lettering, in
  Sam's colour. The verbs do what the other games' do (the plain rules);
  Sam & Max's own replies are not used.
- Captured by the game's own engine from its start ("samnmax-ui.svi",
  "SVI2"): the start run until the button stands in the scene and the
  player has the pointer; each pointer as a right click brings it round
  (checked to come back to the first); the button drawn alone; the box as a
  tap on the button opens it, its objects drawn alone over two fills (its
  picture and icons, what it leaves clear kept, not what the start put in
  it); its cells (6 by 5 of 40 by 24, as the game lays its things out); the
  talk lettering. The verb numbers (walk 7, look 4, use 5, talk 6, pick up
  3) and the icons' objects are in the catalog (kWorldOverlays), read off
  the user's copy.
- On the desktop: the other games' files are byte-identical to 0111 (the
  panels' lettering capture is now one function for both); the new engine's
  verb test goes through 8 panels: Sam & Max's box opened from its button
  and shut by its icon, a tap off it and a right click, its pointer brought
  round all five verbs back to walking, each icon chosen, looking, doors
  refused, out of reach refused, a carried thing looked at in its cell.
- On a phone without a two-finger right click: the box's own box icon
  shuts it and gives the walking pointer back, and the use pointer on a
  door goes through it, as the game's does (look names a door, as before).
- Review fixes: a damaged controls file is refused without writing past
  the pointers it lists (each cut tested); opening the box or a right click
  drops what was being walked to; the box's capture puts the whole screen
  back (each icon was drawn whole over the others).
- Known: Sam & Max's things are not placed where its game puts them yet
  (its rooms' scripts, run out of their story's order, do not end: the
  things pass is left out for it; the plain rules apply, so nothing there
  was taken in the test). The pointer is drawn where the last tap was
  (there is no hovering on a phone). A thing carried cannot yet be used on
  another (the box's way: as the pointer). The box keeps the verb chosen
  only within a place.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0113 — The Dig's own controls in the new engine (step 2f, second part)

- The Dig plays in the new engine with its own controls: its "i" button
  in the corner; one tap does what fits, as its game's single click does
  (a thing that can be taken is picked up, one that is shut opens, else it
  is looked at and named; a door or the ground walks, as before); the
  button opens its grid of things over the scene, the scene showing
  darkened through it as the game's shadow colours darken it, what is
  carried in its cells (a tap there names it); a tap off it shuts it, as
  does a right click. Its pointer, the crosshair, is drawn where the last
  tap was. Speech is in its own lettering, in Boston's colour.
- Captured by its own engine from its start like Sam & Max's: the button,
  the grid as the game draws it (a blast object: drawn alone over three
  fills, what it darkens told from what it leaves clear and what it draws;
  how much it darkens measured on the shadow table it draws through), its
  40 cells (8 by 5 of 32 by 24, as its inventory lays its things out), its
  pointer, the talk lettering (the later games' own glyph renderer, letter
  by letter, as many as the charset has).
- Export version 20: every game exports once more at the next launch (the
  controls file gained what a shaded pixel keeps; The Dig's is new).
- On the desktop: the other games' files are byte-identical to 0112 but
  Sam & Max's controls (one byte more); the verb test goes through 9 panels
  (The Dig's: its button and grid, a tap doing what fits, a door gone to
  with a tap).
- Review fixes: its lettering is taken in its charset's own colours (as
  the game loads them for each line); the grid is drawn over three fills,
  not two, so a darkening that makes two fills one colour is still told
  from what it draws; with no shadow table that does what it shows, half
  the brightness; a tap that only looks needs no reach (one out of reach
  is named, not refused); the verb test asks Sam & Max's icons again.
- Known: The Dig's things are not placed where its game puts them yet (as
  Sam & Max's); its magnifying glass and the way it uses one thing on
  another are not there yet; the grid's darkening is one measure for all
  its colours (the game's table per colour).
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0114 — Full Throttle's own controls in the new engine (step 2f, third part)

- Full Throttle plays in the new engine with its own controls: a tap
  walks (a door goes through, as before); a press held on a thing opens
  its verb coin there, the game's own (the skull's eyes, its teeth, the
  hand, the boot), the thing's name in its banner in the game's lettering;
  moving onto a part lights it as the game does (the eyes glow, the tongue
  comes out, the hand grabs, the boot kicks); let go on a part, Ben walks
  over and does it (the eyes name it; the teeth talk; the hand takes what
  can be taken, opens what is shut, shuts what is open, else "That doesn't
  seem to work."; the boot moves what a push would); let go off the parts,
  nothing. A right click (two fingers on the iPhone) opens its skull of
  things carried in the middle of the screen, four in its mouth; its eyes'
  arrows show when there are more that way, and a tap on an eye goes one
  thing along; a tap on a thing names it, a press held on one opens the
  coin over it; a tap off the skull or another right click shuts it. Its
  pointer, the red crosshair, is drawn where the last tap was.
- On the iPhone a long press is the held press: the coin opens a quarter
  of a second after the phone reports the long press (itself half a
  second), about three quarters of a second in all.
- Captured by its own engine ("ft-ui.svi", "SVI3") without playing the
  story: its start run until the player has the pointer (that pointer, and
  the palette then); the coin and the skull drawn alone from their
  costumes by an actor of the engine's own, in their exact colours as the
  game sets them each time it shows them (its kernel function 14: each
  costume colour remapped into the palette, a free entry taken where none
  matches); each part lit (the coin's animation for it, where it differs
  from the coin's own); the skull's arrows (its animations with the back
  and forward arrows); the name's lettering (charset 1, colour 7, centred
  18 pixels below where the coin is held, as its script prints it) and the
  talk's. The costume and animation numbers, the verb numbers (eyes 8,
  teeth 10, hand 9, boot 5), where the skull opens, its cells and its eyes
  are in the catalog (kWorldCoins), read off the user's copy with the
  engine's own probes (not kept).
- Export version 21: every game exports once more at the next launch
  (Full Throttle's controls are new; the other games' files are
  byte-identical to 0113).
- On the desktop: the verb test goes through 10 panels (Full Throttle's:
  its skull opened by a right click and shut by a tap off it and by a right
  click; the coin not open before the press is held, then open over a
  thing, each of its four parts lit under the pointer, let go off them
  nothing done; a press let go at once walks; looking with the coin's eyes,
  the boot's push and the hand on a thing). Its pictures: verbs-ft.png
  (the pointer), verbs-ft-coin.png (the coin over the bike, its eyes lit),
  verbs-ft-box.png (the skull with things carried, its forward arrow).
- Data suite: 41 of 42 in the full run; test_camera_engine (the old
  engine's camera, a Melee selfie's three shots alike) failed there and
  passed run again on its own: a check that poses may make flaky, not
  touched here. Unit tests with ASan/UBSan pass.
- Review fixes: the coin and the skull are drawn as the game shows them
  (set up, then the coin, then a part lit over it), their colours remapped
  and drawn the same way, on the screen's own rows; the skull's arrows are
  its wherever they are; the name is drawn on the screen (a long one past
  the coin's edges); the coin's size on screen is as its pixels map; a coin
  left open by a lost let-go is shut at the next press, and is lit where
  the pointer is; the verb test taps the skull's arrows, names a carried
  thing with the coin and tries the hand until it takes something. Full
  Throttle's file is byte-identical after them.
- Known: the coin and the skull do not flicker as the game's do (one
  picture each, the first of their animations); Full Throttle's things are
  not placed where its game puts them yet (as Sam & Max's and The Dig's); a
  carried thing cannot yet be used on another (the game's way: as the
  pointer); the coin is for the place's things and the things carried, not
  yet for people.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0115 — Loom's distaff in the new engine (step 2f, fourth part)

User (2026-10-21): "Keep working". The Curse of Monkey Island's coin is
held back: the copy here has only its COMI.LA0 to LA2, not its RESOURCE
folder's fonts (FONT0.NUT to FONT4.NUT), and its start stops on the first
it opens; Loom's distaff, the next, comes first.
- Loom plays in the new engine with its own controls: its distaff under
  the scene as the game draws it once every note is known, the staff below
  it with the notes' letters and coloured notes (the Practice level's). A
  tap on a note lights it in its glow, as the game's does; four notes spin a
  draft: Opening spins open the thing chosen (Bobbin walks over), and the
  same notes backwards (Closing) shut it, as in Loom; another of its drafts
  says "Nothing happens." (not taken up by the plain rules yet); notes that
  spin no draft do nothing. A tap on a thing chooses it: its picture in the
  box at the bottom right, where the game shows its icon, and Bobbin walks
  over; a second tap on it examines it (names it). Doors and the ground walk
  as before.
- Captured by its own engine ("loom-ui.svi", "SVI4"): its start run until
  its choice of how hard, Practice tapped as a player does, then on until
  the first place; every note known and every draft learned (as the
  debugger's "drafts learn" does) and the game's own script draws the
  distaff; the panel as it draws it; each note's verb lit in the fourth
  frame of its glow (its colour bright); the sixteen drafts as that start
  chose their notes (Loom chooses them when a game starts; variables 50 to
  81, read as the debugger's "drafts" reads them); the talk lettering.
- Export version 22: every game exports once more at the next launch
  (Loom's controls are new; the other games' files are byte-identical to
  0114).
- On the desktop: the verb test goes through 11 panels (Loom's: each note
  lit and let go, its sixteen drafts, notes that are no draft doing
  nothing, Sleep saying it does nothing yet; its first place, the tents,
  has nothing named, so a thing in another of its places is chosen, then
  examined by a second tap, opened by Opening and shut by it backwards).
  Its picture: verbs-loom.png (a note lit).
- Data suite 42/42; unit tests with ASan/UBSan pass.
- Review fixes: a thing chosen is examined by a second tap even where it
  has no picture for the box; a note just played no longer takes a tap on a
  door for itself (taps walk); the export refuses a note whose glow drew
  nothing; a thing shown in its first picture (a shut one) is drawn whole
  in the box, and the box follows it when a draft opens or shuts it; the
  verb test waits for the line looked at to go and checks it gets back to
  the first place. Loom's file is byte-identical after them.
- Known: the game's own icons for the things chosen are not used (the
  thing's own picture is shown in their box); only Opening and Closing do
  something; the notes are not heard; a note does not animate through its
  glow; only Loom's floppy edition (EGA) is taken (its CD and Mac editions
  keep their drafts and verbs elsewhere: not exported).
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0116 — chat in the new engine (step 4, first part)

User (2026-10-21): "Push and keep going", "Don't ask me for permission just
keep going". Step 4 brings the iPhone's own features to the new engine;
chat comes first.
- The Talk button works in the new engine as in Maniac: the chat is told
  who is in the place every moment (the one played as the character they
  are, everyone else there by name, up to 26), and the place itself (the
  mansion's rooms by their own names, the other games' by their places').
  Replies are said over the speaker's head in the game's own talk
  lettering, kept within the scene's picture, while their mouth moves (their
  talk frames); the next line waits until the last is gone. Those in the
  conversation stop where they are and face the one played, and do not
  wander off; the one played turns to them as it begins and to whoever
  speaks. When the chat asks whom to talk to, a tap on someone picks them
  (a tap on no one keeps it asking; it is never a walk); a coin game's press
  is then a plain tap. (Corrected in 0117: nothing in the iPhone's chat asks
  whom yet; its people are chosen by their name buttons. The tap is tested
  only against the stand-in, as Maniac's own tap for it is unused too.) Leaving the new engine tells the chat no one is
  there.
- The stage (common/scummverse_stage): standing people turn towards a point
  (as walking there would turn them), play their talk frames in turn, and
  stop where they are.
- Speech over anyone's head (verbs' lines too) now stays within the
  scene's picture instead of running into the black border.
- The Worlds menu in the new engine says Talk chats with anyone there.
- On the desktop (no chat there): a "talk" check puts a stand-in for the
  chat in, in a place of each game with someone besides the one played (12
  places): told who is there, the place, and Maniac's rooms by number;
  someone talked with stops and stays fifteen seconds; their line over them,
  talking; the next only after it; the one played's own; a tap picking
  someone while the chat asks, a tap on no one kept for picking, then a tap
  walking again; the chat cleared on leaving. Its picture: talk.png.
- Stage unit test (ASan/UBSan): facing, talk frames in turn (standing where
  a way has none), stopping.
- Known: everyone's lines are in the one lettering colour (the games give
  each person their own); with the panel turned off (scummverse_verbs) no
  lettering is loaded and lines show only in the chat; people beyond the
  26th in a place cannot be talked with.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0117 — chat in the new engine: review fixes

An independent review of 0116 (pushed before it came back).
- The new engine now tells the iPhone's chat window which place it is in,
  as Maniac does every moment: going through a door clears the old
  conversation from the window (it stayed under "Nobody nearby"), the chat
  no longer reads Maniac's last journey into a new place, and Maniac's
  Arrive button cannot show there.
- Whenever everyone in a place is put on the stage again (playing someone
  else there, a door that could not be shown, a game chosen from the menu),
  the conversation ends, as Maniac's does when the one played changes; it
  could go on with people's places among the chat's names shifted.
- People turning to a conversation are drawn at once, not with the first
  line.
- A line from someone out of view, or in a game whose lettering is not
  loaded (the Curse of Monkey Island's), goes after half a second (the
  chat shows it) instead of holding the next line back for up to fifteen.
- The "talk" check now: someone set walking stops when talked with; asked
  to stroll three hundred times, they never do; the conversation's start is
  drawn; a line from out of view goes at once; the place is checked by its
  numbers as the chat reads them; the chat's window is told the place; the
  same place entered again ends the conversation and tells the chat who is
  there again; the mansion's rooms are required when its files are there.
  Taking out either the conversation's end or the strolling guard makes it
  fail (checked).
- Not taken: nothing in the iPhone's chat asks whom to talk to yet (its
  pick mode is never armed), so the tap that picks someone is tested only
  against the stand-in (0116 corrected).
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0118 — the character screen in the new engine (step 4, second part)

- The new engine's Worlds menu has Play as someone else: the same
  character screen as Maniac's, a box for every game (the mansion first,
  Zak second, then the others) with its lead's face, drawn from the
  player's own exported files (a game not exported shows where to add it).
  A tap on a box plays its lead; a long press lists everyone of that game
  who is installed (the lead first, each once by name). A choice plays that
  character in the new engine, in the place where they live (their place
  in the game's cast, else the game's first place), saved as the one played
  from then on; "You are playing ..." shows briefly. The mansion's box leads
  with Dave here (the new engine's lead for it), where Maniac's own screen
  leads with Dr Fred.
- The chat's own requests (a place's token and a command) can fall within
  the character screen's numbers in the new engine; they are no one's key
  and do nothing.
- On the desktop (no character screen there): a "cast" check puts a
  stand-in in: 12 boxes, every lead's face drawn, 299 people listed (294
  from 0119: those sharing a look once), each
  installed, none twice, the lead first; in every game the lead and the last
  listed are chosen as the screen sends them and are played where they live
  (once on the stage); a chat request in its range does nothing; the one
  played is kept in the state. Its picture: cast.png (the twelve faces).
- Known: the wanderers carry on as they were (whoever is played is passed
  by when people come on the stage; the one played before is not among
  them); where everyone is is not carried over to the next launch when the
  one played changes. (Both changed in 0119.)
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0119 — the character screen in the new engine: review fixes

An independent review of 0118 (pushed before it came back).
- The screen offers only those a choice can play: installed, shown before
  without trouble, and with a place to be; a game's face is the first of
  them (whom a tap on its box plays), so no box shows a face that plays no
  one or someone else. A choice that cannot be played says so ("... can't
  be played here yet.") instead of nothing; a request in the screen's range
  that is no one's (the chat's) stays silent.
- People of a game who share one look (Loom's Flute and Stopper and the
  glassmakers, Day of the Tentacle's) are listed once, under the first
  name, so the name chosen is the one shown and talked to.
- Everyone wanders, the one played among them (passed by wherever people
  come on the stage): the one played before is out again after a choice,
  and where everyone is now stays from one launch to the next whoever is
  played (it was dropped when the one played changed).
- A choice not shown puts the one played before back where they stood.
- The "cast" check now: a face exactly where someone can be played, never
  a face of a few pixels, every face different; nobody listed twice by
  name or by look; the lead first wherever the lead can be played; the lead
  checked in their own room from the leads' table (not the rule the engine
  uses), the last listed in their cast place; a one-person game counted
  once; and with everyone out, someone wandering chosen, sent to the place
  as a wanderer, is shown once over a minute of people coming and on
  entering again, and the one played before is out among them. Taking out
  the pass-by on entering fails it (checked). The sandbox engine test now
  requires every choice played.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0120 — the camera in the new engine (step 4, third part)

- The camera button works in the new engine as in Maniac. A photo is the
  scene alone (clean) or the whole screen with the game's panel (full), at
  the new engine's own full resolution in full colour, enlarged by whole
  pixels only when smaller than 1600 across. A selfie of 1, 3 or 5 shots
  holds the place still (nobody walks, taps wait), poses everyone afresh for
  each shot from their own frames (facing the camera, mid-step or talking;
  now and then someone hasn't noticed, or everyone stares at the one
  played), frames the one played and whoever stands near (4:5 to 4:3), and
  leaves everyone as they were. While iOS asks for access to Photos the
  place holds still. The pictures go to the same saving (the Photos album)
  as Maniac's.
- The camera module (common/scummverse_camera): a true-colour picture
  already shown square is enlarged by one whole factor both ways; a
  selfie's frame can be worked out for square pixels; a plain-types sink
  lets an engine's own check take the pictures.
- The stage: someone can be posed (a way and a frame held, whatever they
  were doing) and let go.
- On the desktop (no Photos there): a "camera" check with a stand-in sink,
  in Monkey Island's first place with someone there: a clean photo the
  scene's size (1918x1036 from a 1280x720 screen: each pixel 2 by 2), its
  corners and middle as drawn; a full one the screen's (2560x1440); a
  selfie of three: everyone posed, three shots of one frame in turn, 4:5 to
  4:3, nobody moving meanwhile, nobody left posed, taking as long as its
  shots are shown; held, the one played does not walk, let go, walks on.
  Pictures: camera-full.png, camera-selfie.png. Camera unit test
  (ASan/UBSan): square factors, enlarging and cutting, the plain sink,
  square framing. Stage unit test: posing.
- Known: the selfie's people are framed from where they are drawn (as
  Maniac's); a photo taken while a line is said keeps the line only in a
  full one.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0121 — the camera in the new engine: review fixes

An independent review of 0120 (pushed before it came back).
- In a place wider than the screen a selfie was framed over the whole
  scene, not the part shown: near the screen's edge its frame ran off it
  and the picture came out cut, narrower than 4:5, the one played at its
  edge. Photos and selfies now take the part of the scene on the screen.
- A check that stands in for the Photos saving puts the iPhone's own back
  when it is done (it ended the saving for the rest of the run).
- Held for a selfie or the Photos question, Full Throttle's coin is shut if
  it was open, and the chat goes on while iOS asks (its replies wait).
- The "camera" check now also: someone is walking when the selfie starts;
  each shot is the posed scene as drawn on its own; the shots are 4:5 to
  4:3 by their own measure; it goes through the run loop's own holding;
  and in a wide place scrolled to its far side (one where a frame over the
  whole scene would run off the screen), a selfie stays within the part
  shown. With the old framing it fails (checked). The camera unit test
  frames a wide group with both near ones in, and the iPhone's saving
  taken back after a check.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0122 — the tour in the new engine (step 4, fourth part)

- The new engine's Worlds menu has Tour every location (watch for bugs),
  with the same controls as Maniac's: the label at the top naming each stop
  ("Stop 12/768 · loom 21 · ...", the mansion's and Zak's as "Maniac 12",
  "Zak 84"), the bar under it (previous, pause or play, next, speed 1x to
  16x), go to a stop by number, stop. The one played goes on autopilot
  through every place installed: the mansion's, Zak's, then every other
  game's, in one pass across each and on through a door where one leads to
  the next stop (through places seen before if need be), warping only where
  none does; a stop that cannot be shown says so and the tour goes on.
  Paused, the one played stands (and can be walked about); Next and
  Previous go from stop to stop and stay paused. Stopped, or at the end, back
  where it began, at the same spot; it resumes at the stop it was at (kept
  between launches). Taps wait while it tours; going to a game, back to
  Maniac or playing someone else ends it there. While touring, where the
  one played was before the tour stays saved.
- On the desktop: a "tour" check through the tour's own requests: 768
  stops, every place installed once (The Dig's subway cars are rides, not
  places), each game begun at its first place, every way on foot a chain of
  doors from the stop before; Go to stop 3 and its label, paused standing,
  Next and Previous staying paused, played walking on, stopped back where it
  began to resume at its stop; then the whole tour at 16 times the speed:
  every stop in turn (628 on foot, 140 warped, none not shown; 422,912 game
  ticks, about two hours at 1x) and back where it began. (Corrected in
  0123: "on foot" counted doors gone through without checking they were
  reached; with that checked, 532, then 604 once walks to a door may last
  longer.)
- Known: the mansion's rooms are named by its map where they have names
  (Maniac's own tour names all 37); rides (the bus, the plane, the van,
  the Dig's subway) are not stops in the new engine yet (step 5).
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0123 — the tour in the new engine: review fixes

An independent review of 0122 (pushed before it came back).
- The iPhone's tour menu is told the stops as the new engine starts: it
  offered "Start the tour" while resuming a saved stop, hid "Start over at
  stop 1", and Go to stop stopped at 1.
- The tour goes through a door only when the one played reached it (as a
  player's tap on a door needs); otherwise it says so in the log and warps
  on, counted apart. A walk to a door may last up to 40 seconds (at 1x;
  the longest places took longer than the 10 a walk across gets, and the
  tour went through from afar).
- Paused on the way through a place between two stops, then played, it
  goes on along the same way (it warped); through only a door of the
  place it is in; a walk of the player's own does not go on into the tour.
- A place passed through between two stops is labelled so ("Stop 12/768 ·
  on the way, through loom 21 · ...") for a bug report to name it.
- Back to the original engine while touring brings the one played home
  first, so where it began is what is saved.
- Where it resumes is kept at each stop (iOS may close the app without a
  word), as the place, not its number (another game installed does not
  move it).
- A tour into another game's room of the same number is drawn at once.
- The "tour" check now also: the start tells the menu where it resumes (a
  place kept as the fifth stop's); a way passed through is labelled so,
  paused there and played it reaches the next stop on foot; every way's
  places are installed; the label's whole stop count; too few places
  skip rather than fail. Whole tour: 768 stops, 604 on foot, 164 warped,
  25 doors not reached (as the doors check's walks that stop short), none
  not shown.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0124 — The Dig's tram in the new engine (step 5, first part)

User (2026-10-21): "Keep going?" Step 5 brings the rides to the new
engine; The Dig's tram comes first (its stations' cars were already
exported).
- In the new engine The Dig's five tram lines run as in Maniac's other
  worlds: walking onto a station's platform ledge calls its car (a tap on
  the car's door walks there instead of going through it); the car comes
  out of its tunnel (or toward the viewer, fading in), "Here comes the
  tram."; its doors open ("The doors open. All aboard!") for five seconds
  ("Doors closing!"), and with the one played on the ledge as they close it
  leaves, the one played out of sight while riding, to the other end, where
  its doors open and they step off; the car stays there. Called where it
  stands, it is waiting, open ("The tram is here. All aboard!"); left
  without the one played, it stays, open. Announcements are drawn at the
  top of the place in the game's lettering.
- The stage: a place can hold a second picture of itself (the same place
  in another state, the car parked: only where it differs, in the place's
  own colours), shown slid by any amount within its own rectangle or as a
  dissolve; someone can be hidden (not drawn).
- On the desktop: a "rides" check takes every line both ways as a player
  does (10 stations): a tap on the car's door walks to the ledge (not
  through), the car is called and drawn, ridden to the other end unseen,
  stepped off there, and there, called again, waiting open and left
  without the one played. Picture: tram.png. Stage unit test (ASan/UBSan):
  the second picture shown, slid, dissolved, its nearest colours, refused
  when not the same size or no different; someone hidden. The doors check
  now counts the 10 car doors as stopped short (they walk to the ledge):
  1829 of 1915 through (1839 before), 73 short.
- Known: where the car is is not kept between launches; the wanderers
  and the tour do not ride it (the tour goes on through its door as
  before); only the one played rides (as the new engine has no
  companions yet).
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0125 — Zak's bus, Mars tram and planes in the new engine (step 5, second part)

- Zak McKracken's rides run in the new engine. A tap on the bus in Zak's
  street walks there; "The bus leaves in 5 seconds."; on board, out of
  sight, to the San Francisco airport, off at its door; that door out is the
  bus back to the street. The Mars tram likewise between the landing site
  and the pyramid ("Tram leaving in 5 seconds."; it stands at both in their
  pictures, so it is not called). A tap on an airport's gate to the planes
  walks there and asks where to (the iPhone's list of places: every other
  airport installed, by city); "Flight to Seattle boarding. Departing in 5
  seconds."; a flight of ten seconds out of sight, then "Welcome to
  Seattle.", off at that airport's gate. Walked off before it leaves, it
  goes without the one played ("The bus left without you."). The rides are
  a table (kWorldRides, kWorldAirports in the catalog) the new engine
  reads; Maniac's own rides are unchanged.
- On the desktop: the "rides" check also boards every Zak ride by a tap as
  a player does (the bus and the tram both ways), misses one by walking off,
  and flies from San Francisco to every other airport in turn and back to
  it (9 flights, each chosen from the list it asks with; one to a place no
  plane goes, or to where it is, does nothing).
- Known: no plane's cabin, bus or tram is shown while riding (their scenes
  are not exported for the new engine: Maniac's plane cabin is its own
  room); no tickets (the CashCard and the reservations terminal are left
  out); only the one played rides; the van and the mansion's scripted
  moments are next.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0126 — The Dig's tram in the new engine: review fixes

An independent review of 0124 (pushed before it came back).
- Put somewhere else while riding (the Worlds menu, the tour, playing
  someone else), the one played is no longer taken back to The Dig's
  station when the car arrives, and taps work again at once. The tour's
  guide is never taken aboard. Once aboard, nothing of the one played's own
  goes on (a door or a verb walked to).
- Put on a ledge (the tour ending there, a launch resuming there) is no
  call: the ledge calls once the one played has been off it (a tap on the
  car's door still calls it, even from on the ledge).
- A tram whose other end is not installed is not called ("This tram's
  other end isn't installed yet.").
- An object shown in another picture where the car stands (its doors) is
  kept under the car and shows as it is when the car goes (the car's slide
  put the place's old look back over it).
- The dissolve (a car coming toward the viewer) is a scatter: it was a
  wipe in vertical stripes, in Maniac's own Dig tram too (common
  scummverse_world).
- Zak's rides (0125) likewise leave nothing of the one played's own going
  once aboard.
- The "rides" check compares the place with and without the car at the
  same moment (the colours cycle; it passed with the car never drawn,
  checked), and checks the car gone from where it left and staying where it
  went. The stage unit test checks a scatter both ways (stripes fail it,
  checked), a car colour that is another of the place's, and an object
  under the car.
- Maniac's Dig tram test passes.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0127 — the Shuttle Bug in the new engine (step 5, third part)

- Melissa and Leslie's Shuttle Bug flies in the new engine. A tap on its
  door at the Mars landing site walks there and asks where to (the
  iPhone's list of places: the van's sites in every game installed, by
  their names, as Maniac's van offers them); "Liftoff in 5 seconds."; a
  flight of ten seconds out of sight, then "The Shuttle Bug touches down."
  where the place puts someone arriving. It stays parked there (kept
  between launches); the Worlds menu's Board the Shuttle Bug takes off
  again from where it stands (elsewhere it says where it is parked). The
  mansion's and Zak's sites are those sure to be the place named (the
  landing site, the Mars pyramid, the mansion's entry road, Zak's street,
  the Seattle forest, the Zaire village, Kathmandu, the Sphinx,
  Stonehenge); the jungles, the Face and Fourteenth Avenue are left out of
  the new engine's list for now.
- On the desktop: the "rides" check boards it at its door on Mars, flies it
  to Melee Island (chosen from the list, which does not offer where it is),
  boards it there from the menu and flies home, and asked for elsewhere it
  names where it is.
- Known: the van is not drawn where it lands (Maniac draws it from the
  picture its own engine takes at the landing site; the new engine does
  not have it yet), and at the landing site it is drawn even when away (it
  is part of that place's picture); no cockpit or starfield while flying.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0128 — the new engine's rides: review fixes

An independent review of 0125 (Zak's rides).
- A tap on a door that overlaps where a ride is boarded goes through the
  door when the door is the smaller (the 14th Avenue door over Zak's bus
  boarded the bus). Doors and rides are now one choice: the one tapped most
  nearly, the smaller where both are.
- Walking off while a ride counts down, by a tap, now says it left without
  you (it was silent, and the countdown's line stayed); a tap near where it
  is boarded keeps it, and a tap on it again walks back to it rather than
  starting the countdown over.
- A plane's or the van's list of where to can be closed: its Cancel (and
  the list not shown at all, something else being over the game) now says
  "No flight booked." or "The Shuttle Bug stays put." and the ride is not
  taken; a choice made after that does nothing. Left unanswered for a
  minute, walked off from, or somewhere else chosen meanwhile (the tour,
  the menu, playing someone else), the list is taken away. On the iPhone it
  can no longer be swiped away unheard (its Cancel closes it).
- The bus and the Mars tram do not count down when their other end is not
  installed ("The bus isn't running: its other stop isn't installed yet.").
  A ride whose arrival cannot be shown puts the one played back where they
  boarded ("That ride couldn't get there.") instead of leaving the game with
  no one to play.
- No ride is boarded while touring (paused too); the menu's Board the
  Shuttle Bug ends the tour first.
- The "rides" check runs Zak's part without The Dig (and The Dig's without
  Zak). It now walks off by a tap, taps a door over the bus's stop, and
  closes a plane's list four ways (Cancel with a late choice after it,
  unanswered, walked off from, another place chosen).
- Not checked: a bus or tram whose other end is missing, and an arrival
  that cannot be shown (every place of Zak is exported here); the iPhone's
  list (its Cancel, being taken away, not swiping) is compiled for the
  desktop only as a stand-in, not built for iOS here.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0129 — the Shuttle Bug drawn where it lands (new engine)

- Where the Shuttle Bug lands in the new engine (Melee Island, the
  mansion's road and the other sites), it now stands there: beside where
  the one played stepped out, on the side with more room, as much taller
  than the people there as in Zak's long shot of it (as Maniac parks it),
  people nearer than it in front of it and those further behind. It is
  there again each time (where it stands is kept between launches). A tap
  on it walks to its door and asks where to, as at its door on Mars; the
  Worlds menu still works too.
- Its picture is the one Maniac takes at the Mars landing site (kept beside
  the other worlds as zak-van.svv once Maniac has been there with the van
  in place). Until then the new engine does not draw it and the menu is the
  way aboard.
- The stage has "props" for this: still pictures in their own colours,
  standing among the people by the row they stand on (unit-tested: colours,
  size and perspective, order with people, rectangle, gone with the place).
- On the desktop: the "rides" check flies it to Melee Island, finds it drawn
  beside the one played and taller than them, boards it by a tap on it and
  flies home (not drawn over the landing site's own picture of it), flies
  back by the menu and finds it drawn where it landed again. Without its
  drawing on landing the check fails (checked).
- Known: at the Mars landing site the van is still part of the picture when
  it is away (the export has no picture of the sand without it); no cockpit
  or starfield while flying; only the one played rides.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0130 — the parked van and the places list: review fixes

An independent review of 0129 and of 0128's iPhone list.
- A tap boards the parked van only where the van is drawn: the sky and
  ground its picture leaves showing around it are the place's again (a door
  behind them works; it took the whole rectangle).
- Its size and room above are worked out in the place's own pixels (Curse
  of Monkey Island's are half the size), it is small on a map as people
  are, and a picture larger than Maniac takes is not read. Where it stands
  is kept together with where it is (it was kept in two writes).
- The iPhone's list of places: taken away while it is still coming up, it
  now closes once up (it stayed, its rows doing nothing); a list asked for
  earlier and still waiting to come up no longer closes or answers for a
  newer one; once a row is chosen its Cancel no longer answers (and after
  Cancel no row), so a choice is not lost to a Cancel just after it.
- Checked against the data: the van's picture uses the landing site's own
  colour numbers (all 6,184 of its pixels are the landing site's there).
- The "rides" check now taps beside the van's picture (a walk) and on it
  (aboard), and checks its size against the people there and its shape
  (each fails with the old behaviour, checked); the stage unit test checks
  where a prop is hit.
- The iPhone list changes are built by the IPA job only; not tested on an
  iPhone. Everything else tested on the desktop build only (Linux).

## Patch 0131 — doors across parts a game joins by script (new engine)

Fixing existing gameplay first: in the new engine some doors could not be
used at all from where the player arrives.
- Many places are in parts the original joins only by a script (stairs
  climbed, a ledge let down from, a cliff path): the walk boxes do not
  meet, and the game's own box table agrees (for example Monkey Island's
  room 48: its ledge and its ground). The new engine runs no scripts, so a
  door in the other part was walked toward and nothing happened. A tapped
  door is now gone through once the player has walked as near to it as the
  walk boxes allow.
- The tour reaches 626 of 768 stops on foot (was 604): 2 doors not reached
  (both in one Atlantis room, a walk longer than the tour waits), 23 gone
  through from as near as the walk allows (was 25 not reached).
- The doors check: 1,868 of 1,905 doors gone through (was 1,829 of 1,915),
  14 to another place, 23 short. The Dig's ten tram car doors are counted
  apart (a tap there calls the tram; the rides check rides them). It now
  taps the part of a door the scene shows (a door reaching past the scene's
  edge was tapped off it) and fails below 98% (was 96%). Without the new
  rule it fails (checked).
- Still short (23): Monkey Island's forest exits placed off the picture (13;
  the forest's own edge exits work), two exits below the picture (Monkey
  Island 2 room 45, Indiana Jones 3 room 47), five Loom doors under a thing
  of the same shape (the tap picks the thing), and three in The Dig (an
  alcove under another object; rooms 61 and 64).
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0132 — the doors check taps where a player's tap finds a door

- The new engine's doors check tapped each door's middle. Where a smaller
  thing sits there (Loom's gate and Cob, a door panel), the tap chose the
  thing and the door counted as unreachable, though a tap beside the thing
  goes through. It now taps the spot of the door nearest its middle that a
  player's tap finds: one no other door takes and, where a walking tap
  takes things first (Loom's distaff, a pointer over the scene), no thing
  over it. Doors with no such spot are counted (41, Monkey Island's forest
  exits outside the picture among them).
- Result: 1,887 of 1,905 doors gone through (was 1,868), 3 to another
  place, 15 short: Monkey Island's 13 forest exits placed outside the
  picture (each a twin of one of the forest's own edge exits, to the same
  place and arrival, which work) and two Loom doors under a thing of the
  same place (the Glassmakers' crystal, the dragon's cave).
  It now fails below 99% (was 98%).
- No change to how the game plays; the check measures what a player can do.
- Tested on the desktop build only (Linux).

## Patch 0133 — doors across parts joined by script: review fixes

An independent review of 0131.
- Where a walk toward a door ends now belongs to that door: a door tapped
  while the tour was paused, then Play, no longer sends the one played
  through that door when the tour's own walk ends (the tour now drops a
  door walk of the player's own when it picks up again).
- Boarding the van from the Worlds menu stops any walk to a door or thing
  the player had started.
- A walk with no way worked out leaves no end to go through from (it could
  not happen today, but it no longer fails open), and a new place starts
  with none.
- The checks: the doors check counts doors gone through only from as near
  as the walk allows (38) and fails if there are none or too many (a tenth
  of all); the tour's count (23) is held to the same.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0134 — the mansion's doors open as you go through (new engine; step 5, the mansion's moments)

User (2026-10-21): "Don't wait for me keep going". The first of the
mansion's scripted moments in the new engine, as Maniac's own engine does
them:
- A shut door of the mansion is seen opening as the one played reaches
  it, for a moment, before they go through; the door they come in by stands
  open. Doors stay as left (kept between launches, as when opened by hand).
  It follows the game's own Open: only where the game's script opens and
  shuts that door and its open picture differs. The tour's way through
  opens them too.
- Zak's doors are left as drawn (as Maniac's own engine leaves most of
  them): some of their open pictures have someone painted in the doorway
  (the guru's), checked by eye against the mansion's, which are all clean.
- On the desktop: the doors check sees 25 mansion doors opening as they are
  gone through, 49 left open, 52 open on arrival; a picture of the front
  door opening was looked at.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0135 — The Dig's tram cars kept where they stand (new engine)

- Where each of The Dig's five tram cars stands is now kept between
  launches (it was forgotten: every car came again when called). A car
  called away is kept where it stood until it stands somewhere again.
- On the desktop: the "rides" check starts with the first line's car left
  at its second station last time and finds it read back so; the rides
  themselves pass as before. The writing of it (only when not testing) was
  not run by a check.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0136 — the mansion's doors: review fixes

An independent review of 0134.
- The doors check could pass without the doors opening (state carried over
  from door to door). It now takes each mansion door from as the game
  leaves it and checks it alone: 49 of 49 doors the game opens are seen
  opening and left open, 50 of 50 doors back are open on arrival, and 24
  of 24 the game does not open (stairs, a ladder, a hole) are left as they
  were. Without the door back opening it fails (checked).
- The tour no longer opens doors on its way (it saved every mansion door
  open); it leaves every place as it finds it, and the tour check says so.
- A second tap on a door as it opens no longer stops the one played going
  through; a door to a place not installed is not opened; only the door
  they came in by stands open (a named arrival that is another door, the
  hall's way into room 6, is left as it was); the door back is kept at
  once (it was opened after the place was saved).
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0137 — the mansion's New kid goes to the kid (new engine; step 5)

- New kid on the mansion's panel now goes to the next of its people where
  they are (among the wanderers; with wanderers off, where they live), as
  the original's New kid goes to the kid chosen, and the one played before
  stays standing where they were (out among the wanderers there, so they
  are there again later). It used to bring the next one to where you stood
  and the one before vanished.
- On the desktop: the "cast" check plays the mansion's first, takes New kid
  among the wanderers, and finds the next played where they were and the
  one before left where they stood (with the old behaviour it fails,
  checked); the verbs check's New kid (wanderers off) passes as before.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0138 — the mansion's and Zak's people speak in their own colours (new engine)

- In the mansion and in Zak's places, each person's lines are now shown in
  their own talk colour (the cast's, in the panel's colours, as the games
  show them: Dave white, Syd and Sandy yellow, Weird Ed and Michael light
  cyan...). They were all in the panel's one colour. Visitors from the
  other games keep the panel's colour, and the other games' places are as
  before (their own colours are not known to the new engine yet).
- On the desktop: the chat check finds a line said in the mansion and one
  in Zak's place in the speaker's own colour (more of the line's pixels in
  it than the place has without the line); in the panel's one colour it
  fails (checked). The panel unit test passes.
- Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0139 — custom characters: Crispy (new engine)

- A new last box on the new engine's character screen, "Custom
  characters", with Crispy first: the user's 8 lb terrier in his red devil
  Halloween costume (hood with two horns, capelet with black trim). Picked,
  he is played right where the player is, standing where the one before
  stood, about a third of a person tall, and he is kept when the app
  restarts. He has walking and talking frames in four directions, and his
  own description and lines for the chat ("Woof! Trick or treat!" and so
  on; the chat with him is not tried on an iPhone).
- His drawing is made by tools/custom_characters.py (pixel art drawn in
  code, from looking at the user's photos; no photo is stored or read by
  the tool) into engine/common/scummverse_custom_cast.inc, so he needs no
  game files and is carried in the app.
- On the desktop: the character check finds the custom box last, titled,
  with a face, Crispy first; plays him from the start place's lead and
  finds him there, where the lead stood, 0.30 of the lead's height, and
  kept in the saved state. A picture of him beside Guybrush outside the
  SCUMM Bar was checked by eye. Unit tests and the startup test pass.
- Not yet: he is not among the wanderers and not in Maniac's own engine's
  character screen (only the new engine's). Tested on the desktop build
  only (Linux). Not tested on an iPhone.

## Patch 0140 — New kid and talk colours: review fixes (new engine)

- An independent review of 0137 and 0138 found the New kid's next kid,
  when already in the same place, stood on the spot the one before was put
  on (both stacked). Now the next kid stays where they stood and the one
  before stays where they were; one coming from elsewhere does not land on
  the one before. New kid also ends a paused tour first, keeps the count
  of people on the stage right, and keeps the wanderers' record of where
  the kid is when they were found nowhere.
- Tests: the character check now also plays New kid with the next kid
  already in the same place and checks both spots, each person on the
  stage once, and the stage in step with the actors (fails without the fix:
  checked). The chat check now fails if no line in the mansion is in its
  speaker's colour. The panel unit test now covers the talk colour bridge
  (a line in a given colour, else the panel's).
- Not fixed (noted): with the wanderers on, most New kid presses move to
  another game (they wander everywhere), and the cast's colours assume the
  DOS editions' palette.
- On the desktop: the cast, chat and verb checks, the panel unit test and
  the startup test pass. Full suite not yet rerun. Tested on the desktop
  build only (Linux). Not tested on an iPhone.

## Patch 0141 — the mansion's lights turn off and on (new engine; step 5)

- In the mansion, Turn off on one of its lights (the lamps, lights, wall
  and desk lamps, the darkroom's red light, the basement's light switch:
  what its own script turns on and off; not a flashlight) makes the place
  dark as the original shows it: black, with everyone in grey. Turn on
  lights it again. A place left dark stays dark when you come back and
  after the app restarts; other places are not affected. As in Maniac's
  own engine, every place starts lit.
- On the desktop: the verbs check turns each of the mansion's 10 lights
  off and on as a player does (the verb, then a tap on it): off, nothing
  of the place drawn but people in grey; another place lit; dark again on
  coming back; kept as written and read back; on, lit. Without the dark
  kept on coming back it fails (checked). A picture of the dark basement
  was looked at. The stage unit test covers the dark drawing. Startup
  test passes. Full suite not yet rerun.
- Also: the custom characters' check now measures each against the height
  it is drawn to have (ready for a second custom character).
- Not yet: a flashlight lighting a dark place; the original's fuse box and
  breakers. Tested on the desktop build only (Linux). Not tested on an
  iPhone.

## Patch 0142 — Suzy, the second custom character (new engine)

User (2026-10-21): "Make another custom character called Suzy." Suzy joins
Crispy in the character screen's "Custom characters" box: long dark hair
streaked with silver in a ponytail, a big smile, a green T-shirt with a
small white bat emblem, light jeans, white sneakers and a black sling bag
(drawn from the user's photos by a helper; the photos are not stored).
She walks and talks in four directions, stands about as tall as the
place's lead, and has her own description and lines for the chat.
- Custom characters are now drawn with square pixels, as drawn (they were
  shown 1.2 times taller than drawn).
- On the desktop: the character check lists both (Crispy first), plays
  each where the player is, and checks each against the height it is drawn
  to have; a picture of Suzy beside Guybrush outside the SCUMM Bar was
  looked at. Full suite not yet rerun. Not tested on an iPhone.

## Patch 0143 — Crispy's face, Suzy as she is (new engine)

User (2026-10-21): "Can you give him more facial features than that? Give
him distinct facial features like the photos" (Crispy), and of Suzy: "her
hair ... is more black than gray, with some gray streaks. Also her butt and
thighs are bigger and she's a little shorter. She's also Asian."
- Crispy's head is redrawn pixel by pixel so his face reads at game size:
  big dark eyes clouded with age, bushy white eyebrows, a big black nose, a
  grey moustache and a scraggly grey-white beard breaking the outline, tan
  folded ears under the hood; his mouth opens in the beard as he talks.
  His body, costume and walk are as before.
- Suzy: mostly black hair with a few grey streaks (strongest at the
  hairline), fuller hips, butt and thighs, three rows shorter (about 0.88
  of a person now), and her face redrawn from the photos (rounder face,
  gently almond eyes that narrow as she smiles, her big smile, her skin
  tone). Drawn by helpers from the user's photos; the photos are not
  stored.
- The full suite passed at 0142 (all 24 checks, including the lights and
  both custom characters).
- On the desktop: the character check plays both, each as tall as drawn;
  pictures of both beside Guybrush were looked at; startup test passes.
  Not tested on an iPhone.

## Patch 0144 — custom characters and lights: review fixes

An independent review of 0139-0142 found no serious bugs; the small ones:
- Maniac's own engine refuses a custom character (new engine only) with a
  line instead of reading past its list of games for its folder.
- Picking a custom character with everyone out: the one played before
  stays beside them, once, out among the wanderers here (they used to be
  left wherever the wanderers last had them).
- The lights are saved only when they change; the check now saves them to
  the settings and reads them back from there, as at launch.
- The chat check needs a line in the mansion itself in its speaker's
  colour (Zak's alone no longer passes it).
- iPhone: the custom characters' box never asks for a game folder to be
  added; the character screen's comment counts its boxes rightly.
- On the desktop: the cast check (with the new wanderers part, which fails
  without the fix: checked), the verbs (lights) and chat checks and the
  startup test pass. The iPhone change is compiled only by the Apple CI.
  Not tested on an iPhone.

## Patch 0145 — the iPhone build fixed after 0144

- 0144's character screen change used property syntax on an untyped
  dictionary value, which Objective-C rejects ("property 'length' not
  found on object of type 'id'"): the Apple CI's IPA build failed in
  ios7_video.mm. It now sends the message instead. Reproduced and checked
  with a small Objective-C++ mock (clang -fsyntax-only, iOS runtime): the
  old line fails, the new one compiles. The IPA build itself is the Apple
  CI's. Not tested on an iPhone.

## Patch 0146 — the mansion's flashlight in the dark (new engine; step 5)

User (2026-10-21): "Keep working". After the lights (0141), the mansion's
flashlight: carried and turned on (Turn on, then a tap on it in the
things carried; Turn off likewise), in a dark place it shows a small
window of the place, as the original does: 48 x 32 of the place's pixels
with rounded corners where the pointer last was (the original's follows
the cursor: on the iPhone, where you last tapped; on the desktop, the
mouse), the rest still dark and everyone in grey. Before any tap in a
place it is round the one played. On or off is kept.
- On the desktop: the verbs check takes the flashlight (or uses it when
  already carried), makes a place dark, turns it on as a player does,
  taps the place and finds the window there and no bigger, then turns it
  off and finds it all dark again; a picture of the beam in the dark
  basement was looked at. The stage unit test covers the window (its
  rectangle, rounding, kept inside the place, off, gone with the place).
  Startup test passes. Full suite not yet rerun.
- Not as the original: the corners are rounded by a simple rule, not the
  original's exact curve; the flashlight needs no batteries here.
  Tested on the desktop build only (Linux). Not tested on an iPhone.

## Patch 0147 — followers in the new engine (the chat's Follow)

User (2026-10-21): "Keep working" (and earlier, option 3: visitors follow
you). In the new engine anyone there can now be asked along from the chat
(its Follow button, shown for the new engine's visitors too; Unfollow to
let them stay). Someone asked along says "I'll come with you.", walks
after the one played (to beside them, not while talking with you), and
comes along wherever the one played arrives (through doors, on the rides,
to places chosen from the menus: every arrival brings them; only the doors
are checked), beside them (among the wanderers too). Asked to stay they say "See you around!" and stay. They
follow the one played: playing someone else lets them go. Kept when the
app restarts.
- On the desktop: a new "follow" check (the chat a stand-in), with the
  wanderers off and on: asked along (said, followed), walking after the
  one played from across the place, through a door and there once beside
  them (and among the wanderers there), the chat told who follows (by
  slot), kept as written and read back from the settings, staying when
  asked (not coming after), and let go when someone else is played. It
  fails without the walking after and without the coming along (both
  checked). The chat's own side (who follows, who can be asked) has a
  unit test in the dialogue runtime tests, which pass. Startup passes.
- The iPhone chat change (the Follow button for the new engine's
  visitors) is compiled by the Apple CI only. Not tested on an iPhone.
- Not yet: followers do not sit in the plane's seats or appear inside the
  van's cockpit view as Maniac's own engine shows them.

## Patch 0148 — the follow check made steady

- The full suite's run of 0147's "follow" check failed once with the
  wanderers on ("came after though asked to stay"): with only two people
  in the place, the one asked to stay strolled at random to a spot near
  the one played. Not a following fault; strolling is now held off while
  the check measures walking after and staying (only following moves
  them then). Five runs in a row pass; the full suite is rerun with it.
- The Apple CI built 0147's IPA (the chat's Follow change compiles).

## Patch 0149 — followers checked on a ride

- The rides check now has someone following when the one played takes
  Zak's bus: they come along and are off beside the one played at the
  other end, there once. (Followers already came along on every arrival;
  this checks it on a ride.) The full suite passed at 0148 (26 checks).
- Not yet: on the plane they do not take seats as Maniac's own engine's
  passengers do. Tested on the desktop build only. Not tested on an
  iPhone.

## Patch 0150 — followers and the flashlight: review fixes

An independent review of 0146-0149 found no serious bugs; fixed:
- Someone following who is in the chat with you (the chat open, as when
  you tap Follow) was held standing where they were; now, left far
  behind, they come after you while talking, and stand to talk once near.
- Followers stand at their own spot beside the one played (left and right
  in turn) and only walk when farther than it; those further out no
  longer set off again and again where they stood.
- On launch, followers are put beside where the one played was saved
  (they were put by the place's starting spot).
- The flashlight is found off when picked up (an old "on" no longer
  carries over), and its beam keeps where it was pointed even at the
  picture's left edge.
- On the desktop: the follow check now also has the follower in the chat
  while the one played walks off (fails with the old behaviour: checked);
  three runs in a row pass. The full suite is rerun with it. Not tested
  on an iPhone.

## Patch 0151 — the water valve drains the pool (new engine; step 5)

User (2026-10-21): "Keep going". The next of the mansion's moments, taken
from the original's own scripts: the basement's water valve. Opening it or
turning it on (in the basement) drains the swimming pool on the pool deck:
the pool shows its empty picture, and its ladder now goes down to the pit
under the pool. Closing it or turning it off fills the pool again, and the
ladder goes nowhere (as in the original, where it cannot be used while the
pool is full). Kept like every picture. The tour still visits the pit.
- How it was found: a probe ran the original DOS V1 valve script through
  Maniac's own engine and listed every object it changed: the valve
  (66) and the pool (139) to their second pictures, the ladder (172) from
  untouchable to usable; closing undoes all three. tools/test_pool_valve.py
  (with tools/probes/pool_valve.inc, in the data suite) checks this against
  the game's scripts (needs the private data): it passes with the
  protection on and off (the probe goes back to the basement before each
  turn: unprotected, a script takes the kid elsewhere after). The full
  suite passed with this patch (27 checks).
- On the desktop: the verbs check opens the valve as a player does, finds
  the pool drained (a picture of it was looked at) and goes down its
  ladder to the pit, then closes it, finds the pool full and the ladder
  going nowhere; without the ladder's rule it fails (checked). The doors
  check drains the pool before trying that ladder, as the game would.
- Not done: the reactor's meltdown timer and the glowing key's script (the
  pit is a place to visit, as the rest of the new engine).
  Tested on the desktop build only. Not tested on an iPhone.

## Patch 0152 — the gargoyle's secret door and other mansion links (new engine)

User (2026-10-21): "Keep going". The pool's probe, run over every thing of
the mansion and every verb its script answers (open, close, turn on and
off, push, pull), listed which other things each changes in the original.
Most are a door and its other side (the new engine already opens the door
back); the rest are now in the new engine:
- The front hall's secret door has no handle: opening or closing it says
  "There's no handle here!" (the original's line), and shut it goes
  nowhere. Pushing or pulling the gargoyle opens it (it stays open), and
  through it is the basement. It is not opened on the way through as the
  other doors are.
- Opening and closing the mailbox and the desk show them open and shut.
- The garden gate opened or pulled shows open from the garage and from the
  other side too; closed, shut from all three.
- Not done: the shower curtains (Dead Cousin Ted's), the TV's picture.
- tools/test_mansion_links.py (tools/probes/mansion_links.inc, in the data
  suite) checks these against the original scripts: passes with the
  protection on and off.
- On the desktop: the verbs check finds the secret door shut, its line,
  going nowhere; the gargoyle pushed opening it and the way through to the
  basement; the mailbox and the desk opened and closed. The doors check
  opens the secret door (as the gargoyle would) before trying it. Tested
  on the desktop build only. Not tested on an iPhone.
- The full suite passed with 0152 (27 checks).

## Patch 0153 — the shower curtain, the gate as one (new engine)

User (2026-10-21): "Keep going". The next of the mansion's
moments, taken again from the original's own scripts by a probe that runs
each verb through Maniac's own engine:
- The bathroom's shower curtain moves as one: opening or pulling any of its
  three parts (or its gathered end) draws it all aside, and the wall behind
  reads "FOR A GOOD TIME CALL EDNA" with her number; closing any part
  draws it all back. Pushed, it won't budge (the original has no script
  for that). The sink there runs without its second picture (it was the
  wrong way round); the shower's tap turned on says "The handle's
  missing." and turned off does nothing, as in the original.
- The garden gate moves as one, as in the original: opened or pulled on
  the pool deck, all three of its sides open; closed or pushed, all shut;
  from the garage or the other side, that side and the deck's. Walking
  through it shut opens it the same way. (Before, push and pull could leave
  its sides disagreeing.)
- The hall's secret door shuts behind whoever goes down its stairs (the
  original closes it); coming back up, it is shut, and the gargoyle opens
  it again. A paused tour no longer lets the player through a door the
  game keeps shut (a review finding on 0151/0152).
- Not done: the TV (turning it on changes only a close-up room that is not
  a place); the circuit breakers (they start a cut-scene).
- Checks: tools/test_mansion_links.py now also runs the curtain, the gate
  from all three sides, the gargoyle pulled, the secret door closed and
  gone through, the sink and the tap through the original scripts (37
  steps; passes with the protection on and off). The verbs check opens the
  curtain by a part and closes it from its end, pushes it, pulls it, runs
  the sink and the tap, opens and pushes the gate from the deck and pulls
  and closes it from the garage, tries the shut secret door with a tour
  paused, sees it kept open, then shut behind on the stairs down; each new
  rule broken on purpose fails it (checked). The kept check now compares
  every kept picture, not only how many. Tested on the desktop build only.
  Not tested on an iPhone.

## Patch 0154 — Extra, the third custom character (new engine)

User (2026-10-21): "Make a new character named "Extra". He's an 8 pound
Chihuahua." (nine photos). Drawn in tools/custom_characters.py from the
photos (the photos are not kept): a glossy black coat with a blue-grey
sheen, big tall pointed ears with pink insides, huge round brown eyes with
a catch-light and a tan rim, a black button nose, the white goatee on his
chin and a white wisp on his chest, a thin tail curled over his back with a
pale tip, and a thin orange collar (from one photo; it also keeps him seen
in dark rooms); the costume's wings in one photo are not drawn. Side,
front and back, walking and talking (his jaw drops, a pink tongue), a
dog's height (0.3 of a person, as Crispy). In the Custom characters box
after Crispy and Suzy, played where the player is; the chat has his own
description and lines.
- Drawing done by a helper from the photos; looked at here enlarged and in
  the engine (beside Guybrush at the Scumm Bar, at his height).
- On the desktop: the cast check plays all three custom characters where
  the player is (3; shot of each). Tested on the desktop build only. Not
  tested on an iPhone.
- The full suite passed with 0154 (27 checks).

## Patch 0155 — every thing of the mansion as its own script answers (new engine)

User (2026-10-21): "Keep going". A probe ran every thing of the mansion
through Maniac's own engine with each verb that changes a picture (open,
close, turn on and off, push, pull), from both of its pictures, and
compared that with the new engine: about two in three answered otherwise
(the original's own lines, "I can't reach it." and the like, and pictures
the wrong way round, such as the kitchen's tap and the circuit breakers).
Rather than copy the game's lines into the project, the export now
records them from the player's own copy:
- When the mansion is set up (on the iPhone at the next launch, once: only
  Maniac is exported again, "maniac-v23"), its things file also records,
  for each thing that is not a door, what its own script does to each of
  those verbs from each picture: the line it says, its picture after, and
  the pictures of the things it sets elsewhere (even as they were: closing
  the valve fills the pool however it was found). 654 of them; the 617 the
  probe also saw are the same.
- The new engine answers so for every thing of the mansion's that is not a
  door (doors still open as you go): the line, the picture, the others.
  A light its script will not let you reach is no longer turned off.
  The handwritten tap line of 0153 is gone (the record has it, and only
  where the original says it).
- On the desktop: every recorded use is done again as a player does it
  (485; 169 are things out of reach, or pictures the game never has them
  in), each with the original's line, picture and others; with the records
  ignored, 289 differ (checked). The verbs check expects the original's
  answer where one is known. tools/test_panel.cpp reads the new things file
  (any order, whole or not at all). Exported with tools/export_worlds.py
  through the app's own launch path. Tested on the desktop build only. Not
  tested on an iPhone (the first launch there exports the mansion again).
- The full suite passed with 0155 (28 checks).

## Patch 0156 — Extra drawn again (new engine)

User (2026-10-22): "Extra looks nothing like the pictures". The first
drawing (made by a helper) had a small head, small ears, long thin legs and
an orange collar from the costume photo. Drawn again here by hand, his head
pixel by pixel from the photos (not kept), side and front at one scale:
- Big, tall, pointed ears set high on an apple dome, dusky pinkish brown
  inside (the far one in shadow from the side); big round dark-brown eyes
  set wide, with a shine and the tan skin under them; a short muzzle with
  grey hairs, a black button nose with its shine; the white goatee under the
  mouth; a few white hairs on his chest; a compact, deep-chested body on
  short legs, the neck rising to the back of his head; the tail curled up
  over his back to a pale tip. No collar.
- From behind: the round back of his head and his ears, his neck, his hips,
  the tail curled on his back.
- On the desktop: the cast check plays all three custom characters (3);
  looked at enlarged on dark, grey and light backgrounds and in the engine
  beside Guybrush at the Scumm Bar. Tested on the desktop build only. Not
  tested on an iPhone.

## Patch 0157 — Extra with his own build (new engine)

User (2026-10-22): "Nope it still sucks. His head is way too big. Make it
look more like the real dog". Looked again at the photo of him standing:
he is a stocky little dog, not a leggy one. Drawn again, row by row:
- A long, round, deep body (a little barrel) on short sturdy legs; a round
  head about a third of his body's length, held at about the height of his
  back on a short thick neck; a short snout; tall, wide-based ears; the tail
  carried up in a curl to its pale tip. His face as before at this size: the
  big dark eye with its shine and the tan under it, the black nose, grey
  about the mouth, the white goatee; white hairs on his chest; his belly a
  little shaggy. Front and back at the same build (broad chest and hips).
- On the desktop: the cast check plays all three custom characters (3);
  looked at enlarged and in the engine beside Guybrush. Tested on the
  desktop build only. Not tested on an iPhone.

## Patch 0158 — Extra slender (new engine)

User (2026-10-22): "He's not chunky at all". 0157 read his build wrongly
from a photo taken from above. From the photo of him held up: slender and
fine-boned, a slim body on thin legs, a round head about as wide as his
body, huge ears angled up and out (about as tall as his head), big eyes, a
short snout. Drawn again row by row so: side, front and back at that build,
his face, ears, white goatee and curled tail as before.
- On the desktop: the cast check plays all three custom characters (3);
  looked at enlarged and in the engine beside Guybrush. Tested on the
  desktop build only. Not tested on an iPhone.

## Patch 0159 — review fixes for 0153-0155 (new engine)

An independent review of 0153-0155 (read only). Fixed:
- The garden gate walked up to shut now opens as one (all its sides), as
  opened with the verb: the door is opened on reaching it, before the way
  through, so 0153's rule in travel() was never reached that way.
- A thing of the mansion's with no second picture keeps the picture its game
  counts it in (its own, and as another's), so its next verb starts from
  there (not exercised by the mansion's records: none of those things
  changes its own).
- What a thing's script sets elsewhere leaves a thing carried as it is.
- The secret door shuts behind also with a tour paused.
- The export: one look per room for what answers which verb (then a run
  only for those), the verb and its objects set as the engine sets them
  for a sentence (no record changed), a line's break kept as a space.
- The verbs check's replay now fails on a record not found again or a
  thing not reached, expects silence where the record says nothing, and
  replays things with no second picture from each picture too: 646 replayed
  (8 out of reach), 0 failed. A check walks up to the shut gate on the
  pool deck: all its sides open (without the fix it fails, checked).
- Left as they are: the mansion's marker is written before its things file
  (an interrupted export keeps the old file: the new engine's own rules
  then); the handwritten tables answer before the records (they agree).
- Tested on the desktop build only. Not tested on an iPhone.
- The full suite passed with 0159 (28 checks).

## Patch 0160 — Extra by an artists' panel, a smaller head (new engine)

User (2026-10-22): "Can you add more agents to work on this. His head is
still oversized" (and ultracode on). Two multi-agent rounds, each drawing
from the user's photos (read only, never copied):
- Round 1: four artists (the current drawing with a smaller head; measured
  from the photo held up; a classic small-dog sprite; a deer-type build),
  three judges (likeness; proportions; reading at game size and pixel
  quality), the winner refined, then a skeptical check. Small heads now, but
  read as a deer or a rabbit (likeness 5.5 of 10); one artist's face, ears
  and tail were the best, its head still big.
- Round 2: three artists put that face, those broad flaring ears, the
  rounded chest and the curled tail on the small head and slim build; four
  judges (one as his owner: "is that Extra?") chose the same one three
  times of four; polished; the check passed it on head size, slenderness,
  ears and legs (likeness 6.5 of 10), better than the drawing in the game and
  than round 1.
- Now: from the side, head and snout 11 px on a 27 px body (about 41%; the
  last drawing about 60%); from the front, the skull 10 px wide over a 12 px
  rounded chest (the last 14 over 12); ears broad triangles flaring out more
  than up; thin legs about as long as his chest is deep, fur in every leg in
  every frame; the neck sloping forward. Drawn 31 rows tall in his 40, made
  as tall in the game as before (0.3 of a person, as Crispy).
- In tools/custom_characters.py with every name of his prefixed (Suzy's
  drawing has a SIDE_HEAD of its own); the generator's frames are the
  panel's pixel for pixel (checked).
- On the desktop: the cast check plays all three custom characters (3);
  looked at in the engine beside Guybrush. Tested on the desktop build only.
  Not tested on an iPhone.
- The full suite passed with 0160 (28 checks).

## Patch 0161 — read, pick up and fix as the mansion's scripts answer (new engine)

Step 5 goes on (the mansion's scripted moments). A survey of the mansion's
own scripts for fix, unlock, use, read and pick up (private analysis, in
build/ only) found 340 answers: every read says something; 37 picks take the
thing, 40 refuse with a line ("It's too heavy!"); fix mostly says why not.
Use and unlock want a second thing; left for later.
- The export (on the device, from the player's own data, as 0155) now also
  records read, pick up and fix: 1040 records (was 654), 90 of them taken.
  The mansion is exported again once (marker maniac-v24); the other games
  are not.
- The new engine: a thing read says the line its script says; picked up,
  it is taken as its script takes it (its line too: "Hmm, they're
  uncanceled.") or refused with its script's line, and what the script
  sets elsewhere is set (the doormat lifted); fixed, its script's line. A
  thing carried, read, says its script's line. One whose script says
  nothing and changes nothing keeps the new engine's own answer.
- Checked: the verbs check replays every record as a player does it: 962
  as the scripts answer (5 out of reach; 44 taken, then put back; 10 of
  those read while carried; 73 left to the plain rules), 0 failed. The
  panel's parser test reads the taken bit and refuses values past 3.
- Tested on the desktop build only. Not tested on an iPhone. An independent
  review is running; its fixes come in a later patch.
- The full suite passed with 0161.

## Patch 0162 — review fixes for 0161 (new engine)

An independent review of 0161 (three reviewers, each finding checked by
another; read only). Fixed:
- Things inside something shut when exported (the fridge's food, the key
  under the mat, the dimes in the piggy bank, the envelope in the safe, the
  tape behind the panel and others) could be picked up with it shut, and
  stayed drawn after: the stage has no picture of the place without them.
  Now refused as before 0161 (the plain rules). Taking them once their
  container is open needs the export to know what each is inside; not done.
- Reading a thing carried from the mansion gave its plain name after a start
  elsewhere (the mansion's things file not read yet): now read when needed.
- Fix is left out: the mansion's fix wants a second thing ("fix ... with"),
  so its one-thing answers were the wrong ones. The mansion exports once
  more (maniac-v25).
- Rejected after checking: the marker written before the things file (as
  0159 left it), old builds and the after byte (each build exports again),
  the replay's checks and the suite's floors.
- Checked: the verbs check replays 901 as the scripts answer (5 out of
  reach; 26 taken then put back, 5 of those read while carried with the
  things file cleared first; 82 left to the plain rules: those taken with no
  picture without them are tried and must not be taken), 0 failed. Without
  the shut-container rule the check fails (four things taken); without the
  load on reading it fails (five lines); both checked.
- Tested on the desktop build only. Not tested on an iPhone.
- The full suite passed with 0162.

## Patch 0163 — Crispy redrawn from the user's model (new engine)

User (2026-10-22): a pixel-art model of Crispy, "Use this model for Crispy"
(ultracode on). The model was read only, never copied into the project.
- An artists' panel: four artists (the side view sampled from the model and
  cleaned up by hand; drawn by hand; sampled at twice the size and reduced by
  hand; the old drawing changed to match), three judges (likeness to the
  model; reading at game size and pixel quality; as his owner). All three
  chose the sampled one; refined with their notes, then a skeptical check:
  likeness 7 of 10, reads in the game, consistent, clean, better than the
  old drawing; the model not read at run time.
- Now: a scruffy tan terrier in a three-quarter side view as the model, the
  red hood with two crescent horns framing his face in a dark rim, dark eyes
  with glints, a big black nose, a cream beard, black ties under his chin
  with the red flap hanging at his chest, the red cape over his back with
  its black edge, the tan rump and the tail up; front and back to match.
  Left as the check found it: the fur cleaner than the model's wiry coat,
  the horns thin at 1x.
- In tools/custom_characters.py (every name of his prefixed; the frames are
  the panel's pixel for pixel, checked). As tall as before (0.3 of a person).
- On the desktop: the cast check plays all three custom characters, 0
  failed; looked at in the engine beside Guybrush. Tested on the desktop
  build only. Not tested on an iPhone.

## Patch 0164 — the Sith Ewok, a fourth custom character (new engine)

User (2026-10-22): a front, side and back model sheet, "Make a new Sith Ewok
character" (ultracode on). The sheet was read only, never copied.
- An artists' panel: four artists (sampled from each view and cleaned up by
  hand; drawn by hand; sampled at twice the size and reduced by hand;
  readability first), three judges (likeness; reading at game size; as the
  user). Scores were close (one judge chose B, two A; B's total was highest);
  B refined with all the notes, then a skeptical check: likeness 7 of 10,
  reads in the game, consistent, clean; the sheet not read at run time.
- Drawn: a short, stout Ewok in a charcoal-purple hooded robe with two round
  ears on the hood, a thick cowl, wide sleeves and furry hands, glowing amber
  eyes under a stern brow, a black nose and a frown; a brown belt with a
  silver buckle and the crossguard hilt at the left hip (the viewer's right
  from the front, the near side from the side, the left from the back); the
  robe lit at its rims so it reads on dark places. 40x48, drawn 46 rows tall,
  about 0.6 of a person. Talking opens the mouth; walking bobs and sways the
  hem. Left as the check found it: the face window squarer and brighter than
  the sheet's, the hood's crown flatter, the robe wider at the hem.
- In the catalog as costume 4 (its description and lines for the chat, the
  talk colour light magenta); in tools/custom_characters.py with every name
  prefixed (the panel's frames pixel for pixel, checked).
- On the desktop: the cast check plays all four custom characters, 0
  failed; looked at in the engine beside Guybrush. Tested on the desktop
  build only. Not tested on an iPhone.

## Patch 0165 — Extra redrawn from the user's model (new engine)

User (2026-10-22): a pixel-art picture of Extra, "Redesign Extra using this
art as closely as possible". The picture was read only, never copied.
- An artists' panel: four artists (sampled from the picture with the head
  turned to the viewer as in it; sampled with the head in profile; sampled at
  twice the size and reduced by hand; readability first), three judges
  (likeness; reading at game size; as his owner). Two chose the sampled
  three-quarter one (A), one the reduced one (C); A refined with all the
  notes, then a skeptical check: likeness 8 of 10, reads in the game,
  consistent, clean, better than the drawing before; the picture not read
  at run time.
- Now as the picture: a glossy black Chihuahua with blue-grey sheen and
  maroon shading, his head turned to the viewer, very big ears with salmon
  insides, big brown eyes with glints, a white chin and a white blaze down
  his chest, a slim deep chest and tucked belly, long thin legs with white
  toe tips, the tail raised and hooking forward. Drawn 38 rows tall in his
  40, kept 0.3 of a person in the game. Left as the check found it: from
  behind his haunches are wider than the picture's slim dog and the tail
  reads faintly; from the front only the front legs show.
- In tools/custom_characters.py (his section replaced; every name prefixed;
  the panel's frames pixel for pixel, checked).
- On the desktop: the cast check plays all four custom characters, 0
  failed; looked at in the engine beside Guybrush. Tested on the desktop
  build only. Not tested on an iPhone.

## Patch 0166 — Suzy 2, a fifth custom character (new engine)

User (2026-10-22): a pixel-art picture, "Make a Suzy 2 as close as possible
to this pic". A new character beside Suzy (hers is unchanged). The picture
was read only, never copied.
- An artists' panel: four artists (sampled from the picture and cleaned up
  by hand; drawn by hand; sampled at twice the size and reduced by hand;
  readability first), three judges (likeness; reading at game size; as the
  user). Two chose the reduced one (C), one the sampled one; C refined with
  all the notes, then a skeptical check: likeness 7 of 10, reads in the
  game, consistent, clean; the picture not read at run time.
- Drawn as the picture: very long dark hair with grey and silver streaks,
  most of it over her left shoulder down to her wrist, a broad white grin,
  a green crew-neck T-shirt with a white oval emblem and a dark green bat,
  a black watch on her left wrist, blue jeans with faded thighs, light grey
  sneakers; her back covered by the hair past the waist; a real stride from
  the side. 32x56, 52 rows tall, 0.95 of a person as Suzy.
- In the catalog as costume 5 (her description and lines for the chat, the
  talk colour light cyan so she is told from Suzy); in
  tools/custom_characters.py with every name prefixed (the panel's frames
  pixel for pixel, checked).
- On the desktop: the cast check plays all five custom characters, 0
  failed; looked at in the engine beside Guybrush. Tested on the desktop
  build only. Not tested on an iPhone.

## Patch 0167 — Suzy's own drawing put back after 0166 (new engine)

Found on reading 0166's diff: Suzy 2's section defined the canvas size
names W and H again (32x56), and Suzy's own frames, built from them, were
drawn 32 wide: shifted, her pictures changed. Suzy 2's are now SUZY2_W and
SUZY2_H; Crispy's, Suzy's, Extra's and the Sith Ewok's data are byte for
byte as 0165 built them (checked), Suzy 2's as the panel's.
- tools/custom_characters.py now refuses a top-level name defined twice
  (with the old line back it stops, naming W; checked).
- On the desktop: the cast check plays all five custom characters, 0 failed.
  Tested on the desktop build only. Not tested on an iPhone; 0166's IPA has
  Suzy drawn wrong.
- The full suite passed with 0167 (five custom characters).

## Patch 0168 — things inside others, shown and taken only when open (new engine)

Step 5 goes on, from 0162's review: the mansion's things inside another
(the fridge's food, the key under the door mat, the dimes in the piggy
bank, the envelope in the safe behind the painting, the tape behind the
loose panel, the tools in the trunk: 49 of them) were drawn as the shut
container, so they could not be taken once it was open, and a tap there
found them before the container.
- The export (the mansion's, on the device): what each thing is inside and
  the picture that one shows it in ("SVO3"); each such thing drawn with what
  it is in opened, so its pictures are the open container with it and
  without it. The mansion exports once more (maniac-v26).
- The new engine: one inside a shut thing is not touched (a tap finds the
  container); opened, it is drawn and can be taken; shut again, the
  container covers it; opened again, what was taken stays gone.
- Checked: the verbs check opens the fridge, takes the cheese, shuts it,
  leaves and comes back, opens it again (the cheese still gone, the lettuce
  there), and lifts the mat and takes the key; the replay opens each
  thing's container before using it: 917 as the scripts answer (5 out of
  reach, 42 taken), 0 failed. Without drawing again after a picture
  changes the fridge check fails (checked). The stage and panel parser
  tests cover the new reading (looksAs; "SVO3": its order, cut short, one
  inside itself, listed twice).
- Tested on the desktop build only. Not tested on an iPhone.
- The full suite passed with 0168.

## Patch 0169 — review fixes for 0168 (new engine)

An independent review of 0168 (three reviewers, each finding checked by
another; read only). Fixed:
- Drawn again in the original's order (from its last object to its first)
  with what overlaps them: 0168's order left a strip of the shower curtain
  shut after it was drawn aside (its rod's picture painted over it), and a
  corner of the envelope in the safe after it was taken.
- A door inside something shut is no way through until it is open: the
  grating behind the bushes, the hole behind the blotch of paint, the door
  behind its padlock (walked through before, and kept open).
- The letters in the mailbox are not there until the mail comes, as the
  original has them (their state says so): opening the mailbox no longer
  shows them to be taken. The mansion exports once more (maniac-v27).
- The mansion's old things file is emptied before its export's marker, so
  an export that stops after its places never pairs them with an older
  file (it has none then: the new engine's own rules).
- Checked: the shower curtain now looks so (pixel for pixel), the envelope
  taken from the safe behind the painting, the grating behind the bushes,
  the mailbox's letters; drawn in 0168's order four checks fail (checked).
  The verbs check: 848 as the scripts answer (74 away: the letters and
  others not yet there), 0 failed.
- Tested on the desktop build only. Not tested on an iPhone.
- The full suite passed with 0169.

## Patch 0170 — two things: Use with, Give to, Unlock with (new engine)

Step 5 goes on. The new engine had no sentence of two things: Use, Give,
Unlock and Fix worked on one thing only.
- With a game's verb panel under the scene (the mansion, Zak, both Monkey
  Islands, both Indys, Day of the Tentacle): Use or Give and a thing
  carried reads "Use the key with" / "Give the key to", the verb staying
  lit; then a thing here (walked to) or another carried completes it:
  "Use the key with the door". Unlock and Fix start from the thing here
  ("Unlock the door with"), then the thing carried. Another verb or a tap
  on the floor lets go. (Sam & Max, The Dig, Full Throttle and Loom keep
  their own controls as before.)
- What two things do: the plain answer for now ("That doesn't seem to
  work."; given: "I don't think they want it."). The mansion's own answers
  come next, recorded from its scripts as the others.
- Checked: in each of seven games the verbs check takes a thing, chooses
  Use, taps it (the sentence ends "with", the verb lit), taps another
  thing here (walked to, the plain answer, the sentence cleared), then
  again and the floor (let go, walking). 0 failed.
- Tested on the desktop build only. Not tested on an iPhone.
- The full suite passed with 0170.

## Patch 0171 — two things as the mansion's own scripts answer (new engine)

0170's two-thing sentences now answer as the mansion's own scripts do.
- The export (on the device, from the player's own data) runs each thing's
  script with each other thing as its second (the ones that can be carried
  owned by the kid), from its place as the kid arrives, and records the
  answer: its line, its picture after, the others it sets, what the kid has
  then, and what is used up. Each thing's usual answer is kept once; only
  the seconds answered otherwise are listed: 234 records, 48 of them a
  thing's own answer to one second (for example the cassette tape put in
  the recorder, dimes in the arcade game, the faucet handle on the shower,
  the paint remover on the blotch, the key in the front door, the lockers'
  key). Use answers by what it is used on, as the mansion's sentences run.
  The mansion exports once more (maniac-v28).
- Checked: the verbs check replays each own answer as a player has it (the
  second carried, then Use, or Unlock and Fix on the one here): 47 as the
  scripts answer (1 not tried: its second has no place), 0 failed; looked
  up the other way round, 21 fail (checked). The panel parser test reads
  the seconds, the used-up bits and the usual answer.
- Tested on the desktop build only. Not tested on an iPhone.
- The full suite passed with 0171.

## Patch 0172 — review fixes for 0170-0171 (new engine)

An independent review of the two-thing sentences (three reviewers, each
finding checked by another; read only). Fixed:
- A sentence half made ("Use the key with") was kept through a change of
  place (the Worlds menu, the character screen, the tour, a ride) and took
  the next tap there, in any game: now let go on entering a place.
- The export filed each answer under the picture its thing was in after
  its script began, not before: 18 of the mansion's own answers could not
  be reached in play (the paint remover on the blotch, the trunk's and the
  coin boxes' keys, the padlocks, the faucet handle). Each run now sets the
  thing's picture first, from each of its pictures; 101 own answers.
- A carried first's own script never ran (it was not in the kid's
  inventory): it is now, as taken. A usual answer that says and changes
  nothing gives the plain line, as for one thing.
- The usual answer never uses anything up (the lab suit's used up whatever
  was used with it); runs that start a cut-scene or take the kid away are
  not recorded, nor the suit's ending (as play refuses it).
- Checked: 97 own answers replayed as the scripts give them (4 not tried:
  no place for their second); the blotch, the trunk and the coin box
  answered from the picture the place shows them in (with the old picture
  reading those three fail, checked); a half made sentence let go on
  entering a place; the mansion exports once more (maniac-v29). 0 failed.
- Tested on the desktop build only. Not tested on an iPhone.
- The full suite passed with 0172 (after a fix to its own script: 0172's
  message line had an unescaped apostrophe, a syntax error; fixed and
  pushed as a tools-only commit).

## Patch 0173 — Give to someone (new engine)

0170's "Give the key to" could only be completed on a thing: tapping a
person let go. Now someone tapped is given it: the one played walks up
beside them and they answer ("No, thanks.", in their own voice: no game's
records say what people take). Checked in the verbs check (Give, the thing
carried, someone on screen: walked up to, their answer, the sentence let
go), where a place has someone on screen. Tested on the desktop build
only. Not tested on an iPhone.
- The full suite passed with 0173.

## Patch 0174 — custom characters kept compressed (new engine)

Ahead of Crispy 2 (drawn at Curse of Monkey Island's detail, 96 rows and up
to 250 colours, several times the data of the 40-row characters): each
custom character in engine/common/scummverse_custom_cast.inc is now its
character file gzip-compressed (mtime 0, the same bytes each time), read
whole by the new engine (as the export's own files are). The generated
file goes from 1.4 MB to 68 KB. On the desktop the cast check plays all
five custom characters as before, as tall, 0 failed. Tested on the desktop
build only. Not tested on an iPhone.

## Patch 0175 — something lit: the L key, its frames and its glow (new engine)

User (2026-10-22), with three sheets of a Sith Ewok 2 (the saber off,
igniting, lit): "The lightsaber should be switched off by default, but there
should be an unused key that ignites it. He grabs the hilt with both hands
while it ignites, but switches to only holding it in his right hand while
he walks around with it ignited." This patch is the engine's part; Sith
Ewok 2 himself (drawn by an artist panel from the sheets) follows.

- Character files ("SVC1") may carry four more poses: lighting up (its
  frames played forwards; backwards, putting it out) and standing, walking
  and talking with it lit (World::GuestKind 4..7). A missing facing of
  those takes the nearest facing's, else the unlit pose.
- A frame's mask may now say 2: its colour is light added to what is
  behind (a blade's red haze over any place), or 3: drawn even in the dark
  (the blade itself where the lights are off); 1 as before.
- The stage: light(actor, on, played): standing, its lighting-up frames in
  turn, 8 ticks each (six: about four fifths of a second), then its lit
  poses; walking ends the frames. Posed for a photo, lit, its lit poses.
- The new engine: the L key (on the iPhone, pinch to bring up the keyboard)
  lights what the one played carries or puts it out; nothing for those
  carrying none. It stays lit through doors and places while the same one
  is played, and starts off (not kept when the app closes).
- tools/custom_characters.py: lit poses' numbers, glow and shine letters per
  character, its height against a person from its first (standing) frame.
- Tests: test_stage (the frames in turn, lit standing and walking, put out
  backwards, at once, walking ends them, nobody else lights; a glow added
  to the place and to the dark, a lit blade in the dark) passes with
  ASan/UBSan. The cast check gains: for one carrying something lit, L
  lights it (its frames, then lit, walking lit, lit in the next place, put
  out, standing as before), for the others L does nothing; with a stand-in
  (the Sith Ewok given lighting frames, not committed) it passed with 1 lit,
  and with the real cast (none carry one yet) 0 failed. Startup test passes.
  Tested on the desktop build only. Not tested on an iPhone.

## Patch 0176 — something lit: review fixes (new engine)

An independent review of 0175 (two reviewers, each finding verified) found:
- The lighting-up frames were not drawn: the new engine draws again only
  while someone walks or talks (StageBridge::busy), and lighting up was not
  counted, so the screen stayed on the first frame (or, putting it out, on
  the last, the blade looking lit). busy() now counts it.
- L pressed again halfway restarted from the other end (the blade jumping
  out full, or gone): it now turns back from the frame shown.
- Talking lit with no frames of its own dropped to the unlit pose (the
  blade gone): now lit standing, as the old engine's frame fallback has it.
- The iPhone's keyboard may send a capital L (keycode 'L'): L is now taken
  in either case (by keycode or by its letter).
- The cast check could not fail for a lighter not lighting: it now counts
  those that can light and fails unless each did, presses the key as the
  iPhone sends it (capital, then small), checks the place is redrawn while
  lighting (busy), and fails when the one played does not walk (it tries
  both ways).
- The bridge's pose numbers' compile-time check no longer warns
  (-Wenum-compare).
Tests: test_stage (-Wall -Werror, ASan/UBSan) adds turning back halfway both
ways, lit talking as lit standing, and the bridge busy while lighting up and
not after; passes. The cast check passes with a stand-in lighter (not
committed: 1 lit) and with the real cast (0 lit, 0 failed); startup test
passes. Tested on the desktop build only. Not tested on an iPhone.

## Patch 0177 — Crispy 2, drawn at Curse of Monkey Island's detail (new engine)

User (2026-10-22), with the picture of Crispy in his devil costume: "make a
Crispy, Crispy 2 or 3, whatever we're up to and use the newest generation of
SCUMM, SCUMM version 8 (v8). Make him look as close to the attached image as
possible". Drawn by an artist panel (four artists, three judges, the winner
refined, a skeptical check; then a second refinement for the check's
findings: see-through cracks, a weak back view, a plain front body, a stiff
walk; checked again: 0 holes, cleaner, likeness 7.5 of 10, v8 quality 7):
104 x 96 from the side, 72 x 96 from the front and back, 240 colours, the
side sampled from the picture, the front's face from it, the back painted
to match. The picture is not kept or read: every frame is baked into
tools/custom_characters.py as palette indices (zlib + base64), the section's
names prefixed crispy2_ (its frames checked equal to the panel's, pixel for
pixel). Costume 6, 0.3 of a person tall (as Crispy), talk colour 8 (orange);
the other five characters' data unchanged. On the desktop the cast check
plays all six where the player is, as tall as drawn, 0 failed; a shot shows
him on Monkey Island's dock beside Guybrush. Tested on the desktop build
only. Not tested on an iPhone.

## Patch 0178 — Extra 2, drawn at Curse of Monkey Island's detail (new engine)

User (2026-10-22), with the picture of Extra: "make a new Extra, Extra 2, and
use the newest generation of SCUMM, SCUMM version 8 (v8). Make him look as
close to the attached image as possible", then with a sheet of his side and
back: "Add these side and back views to Extra 2" (the panel was restarted
with it; the artists kept their front work). Drawn by an artist panel (four
artists, three judges, the winner refined, checked: likeness 8 of 10, v8
quality 7): 104 x 96 from the side, 72 x 96 from the front and back, 236
colours; the side and back from the user's sheet, the front's face from the
first picture. A second refinement for the check's findings (a stiff front
body, a pale talking tongue, a short muzzle, speckle, step 2 of the front and
back walks the same as standing) came out worse (the front a narrow
"penguin", the muzzle a beak: likeness 6) and was set aside; a merge of the
two was stopped when the user, shown the first ("Extra is almost perfect!
But he has too much white"), circled the white on his neck and asked: "take
away the white on the neck between the chin and the chest ... The chin looks
perfect. Also make the white on the chest less. He's only a tiny bit white
there." So the first version, with its front frames (all eight: standing,
walking, talking) edited: the neck's white patch and its warm brown edge
taken away, filled from the coat round it (each pixel the mean of its coat
neighbours, from the edge in, snapped to the coat's own blue-blacks); the
chest's white cut to a tiny patch (about ten pixels round its brightest
point) with a soft edge; the chin kept. The side view keeps the white blaze
from the user's side sheet. The pictures are not kept or read: every frame
is baked into tools/custom_characters.py (the section's names prefixed
extra2_, its frames checked equal to the edited module's). Costume 7, 0.3 of
a person tall (as Extra), talk colour 3 (cyan); the other six characters'
data unchanged. On the desktop the cast check plays all seven where the
player is, as tall as drawn, 0 failed; a shot shows him on Monkey Island's
dock. Known: the front and back walks' step 2 is the standing pose (three
poses in turn). Tested on the desktop build only. Not tested on an iPhone.

## Patch 0179 — Suzy 3, drawn at Curse of Monkey Island's detail (new engine)

User (2026-10-22), with a picture of Suzy with a black sling bag: "make a
Suzy 3, and use the newest generation of SCUMM, SCUMM version 8 (v8). Make
her look as close to the attached image as possible. You can't tell from the
pic but she has wider hips and a bigger butt than that. She's about 5'3" in
height." Drawn by an artist panel (four artists, three judges, the winner
refined, checked: likeness 8, v8 quality 6, the hips as asked): 104 x 200 in
every facing, 236 colours; the front sampled from the picture (the hips,
thighs and seat about a quarter wider), the side and back painted. The check
found the side's arms flat sticks, its face generic, the side and back flatter
than the front, the side seat a bubble pinched behind the knee, thin back
legs; a second refinement (the front's tones on the side and back, shaped
arms, fuller legs) was stopped when the user, shown the first sheet, said:
"Suzy 3's butt sags too much. It's perkier than that. For her eyes, keep in
mind she's Asian." A third pass from the second's work: the seat full and
round but lifted, fullest just under the waistband, tucking into the thigh at
a short fold (the back's two cheeks high and round with the pockets on them);
in profile a narrow almond eye in a smiling squint, a soft low nose bridge, a
round cheek, her tan; a clearer front walk. Checked: likeness 8, v8 quality
7.5, the seat perky, the side's eyes as asked; it noted a dark strip between
her legs on one front walk frame, which, opened to a gap, looked worse (a
ragged slit) and was kept as a shadow. The front's face is the picture's (its
eyes unchanged). The picture is not kept or read: every frame is baked into
tools/custom_characters.py (the section's names prefixed suzy3_, its frames
checked equal to the panel's). Costume 8, 5'3" (0.9 of a person), talk colour
5 (green); the other seven characters' data unchanged. The generated file
grows to 1.2 MB (her painted textures compress less). On the desktop the cast
check plays all eight where the player is, as tall as drawn, 0 failed; a shot
shows her on Monkey Island's dock between two Guybrushes, about nine tenths
of his height. Known: from the back her hips read wider than from the front.
Tested on the desktop build only. Not tested on an iPhone.

## Patch 0180 — Sith Ewok 2 and his lightsaber (new engine)

User (2026-10-22), with three sheets (the saber off; igniting with both
paws; lit, walking): "make a Sith Ewok 2, and use the newest generation of
SCUMM, SCUMM version 8 (v8). Make it look as close to the attached image as
possible. The lightsaber should be switched off by default, but there should
be an unused key that ignites it. He grabs the hilt with both hands while it
ignites, but switches to only holding it in his right hand while he walks
around with it ignited." The engine's part came first (0175, 0176: the L key,
the lighting-up frames, lit poses, a glow's added light). Drawn by an artist
panel (four artists, three judges, the winner refined, checked: likeness 8,
v8 quality 7, both paws on the hilt while it lights, the right paw only lit,
clean): 80 frames, 241 colours. Saber off (121 x 132, as the first sheet:
the deep hood with its ear bumps, the stern face and amber eyes, the cowl,
the belt and buckle, the hilt hanging at it, bare paws): standing, walking,
talking. Lighting up (181 x 240, the body where it stands off): the paws on
the hilt, raised, then the blade at a quarter, half, three quarters, full,
the cross-guard blades growing, a burst of sparks. Lit (as the third sheet):
standing (two crackles, alternating), walking and talking with it in his
right paw, red light on his robe. The blade's core and edges, its sparks and
his amber eyes show in the dark (mask 3); its red haze is added light
(mask 2). Lit frames are trimmed to what is drawn (tools/custom_characters.py
svc(trim=...), for a lit one only: the others' bytes are unchanged). The
sheets are not kept or read: every frame is baked into the generator (lzma
+ base85 in its section; the section's names prefixed sewok2_, its frames
checked equal to the panel's). Costume 9, about 0.6 of a person (as the Sith
Ewok), talk colour 2 (red). The generated file grows to 3.3 MB.
- Tests: the cast check now plays a real lighter: L (as the iPhone sends it,
  capital) lights it (the lighting-up frames while he stands, the place drawn
  meanwhile), then lit; walking lit; lit in the next place; l puts it out;
  standing as before; the others light nothing; 9 custom played, 1 lit, 0
  failed; shots of him off, lighting and lit on Monkey Island's dock beside
  Guybrush. tools/test_sandbox_engine.py now requires at least one lighter.
  Startup test passes. Known (the check's notes): from behind his lit feet
  are flattened; a soft band at the lit robe's hem; a few stray orange pixels
  on two back lighting-up frames; the stance changes from standing to the
  sheet's wide combat stance as it lights and back as he walks (as the
  sheets have it); the hilt moves from his belt to his paws between frames;
  the blade is cleaner than the sheets' crackling one. Tested on the desktop
  build only. Not tested on an iPhone (the L key there: pinch to bring up the
  keyboard).


## Patch 0181 — Story play: the original games, opened from Maniac (first step)

User (2026-10-22): "is it possible to make a story mode where all 12 games
are playable from start to finish, at the same time? Meaning you can
teleport to monkey island and play a some, then go to Indiana jones and play
some. Save, and it saves all your progress?" and later "You don't have to
hold story mode or anything to else. I want you to keep working on
everything." A read-only design pass (four agents: the start-up and chained
targets, the save slots, the iOS menus, then a design) found ScummVM runs one
engine at a time, so "at the same time" is: each game keeps its own place,
saved when it is left and loaded when it is opened again. This is its first
step.
- Maniac's Worlds menu has "Play the original games": each game with a folder
  in Documents, "Start <game>" or "Continue <game>" (it has a story save);
  one without reads "<game> (add Documents/<folder>)". A game opens in its
  own engine as ScummVM runs it (none of the mansion's additions): its own
  start, menus, controls, films and music. Maniac is saved first (slot 100,
  as for the new engine) and comes back exactly there.
- In a game, the Worlds button offers "Go to <another game>" and "Back to
  Maniac Mansion". Leaving saves the game's place to its story save (slot 99,
  "Story", an ordinary save: its own save and load menus list it, and its
  music state is kept), and it starts there next time. Leaving any other way
  (the game's own Quit, ScummVM's menu) saves it on the way out too. It is
  not saved while the game has the controls (its opening, a cutscene, a
  film) or its own menus are up: the leaving waits up to 8 seconds of the
  game's time, then asks: Leave (it starts again where it was last saved)
  or Stay. A game opened again goes on from the newer of its story save and
  its autosave (ScummVM's own, every 5 minutes and when the phone puts the
  app away), so a place left where it could not be saved is not lost.
- Each game has its own target, kept from one launch to the next
  ("scummverse-story-monkey" and so on, its saves "scummverse-story-
  monkey.s99"...), its folder looked up again at each launch (and when it is
  opened, for a folder added while the app runs), its edition found as it
  starts (common/scummverse_story.h, shared by base/main.cpp and the
  engine). The start-up rule is unchanged (the app starts only
  Maniac, or the new engine). A game that quits, or cannot start, comes back
  to Maniac.
- A game is refused, in words, when a file its story cannot go on without is
  missing (the engine would stop, and the app with it): Full Throttle's bike
  fights (its DATA folder: ROADRASH.RIP and the rest), The Curse of Monkey
  Island's lettering (its RESOURCE folder: FONT0.NUT to FONT4.NUT). Their
  places in the new engine need neither.
- Another game's own rooms 192 to 199 are its own: only the mansion reads
  them as other worlds' slots.
- Copy protection: Monkey Island 2's opening asks for the recipe from its
  code wheel (ScummVM takes any number; type one with the keyboard, a pinch
  on the iPhone), and Sam & Max's asks you to dress them as the manual
  shows; both are the games' own, as ScummVM runs them.
- Tests (desktop, null backend): tools/test_story_engine.py (new, in the data
  suite) runs the real engine with a Documents folder of the supplied games;
  the Worlds menu's requests go through the poll the story code reads. Each
  of Monkey Island, Loom, Indiana Jones and the Last Crusade, Fate of
  Atlantis, Day of the Tentacle, The Dig, The Curse of Monkey Island (with
  the fonts the user sent) and Zak McKracken: opened from Maniac (a request
  left from before dropped), started fresh, played past its opening, saved
  by Back to Maniac Mansion and left; Maniac back in the same room with the
  same kid each time. Then each opened again from its story save with every
  variable as saved (bar the two the engine itself sets on loading), going
  on to the next game directly (Go to); the last left as ScummVM's own menu
  does (Return to Launcher), saved on the way out, and opened again from
  there. Full Throttle here (only FT.LA0 and FT.LA1) is refused for its
  missing ROADRASH.RIP, as it must be. Monkey Island 2 and Sam & Max are not
  in the default run: their copy protection waits for the player.
  tools/test_startup.py (14): a saved story target cannot be started from
  the command line.
- Reviewed by two reviewers, each finding checked: fixed, a game left by its
  own Quit or ScummVM's menu was not saved (now saved on quitting, and the
  newer autosave taken when it could not be); a folder added while the app
  runs is set up when opened (it was refused as missing); the story save
  could disturb a save the game itself had waiting (now it waits for it,
  and puts the game's save settings back); the 8 seconds were wall-clock
  time (now the game's own); the test now goes through the requests'
  handling, checks the save as written, a request left from before, and a
  quit's save. Rejected: none of substance.
- Not yet (the design's next steps): Maniac Mansion's own original story
  apart from the hub; saving all the games together as one snapshot; the
  app starting in the game last played; the Talk, AI and camera buttons
  hidden in a game (they do nothing there).

## Patch 0182 — Sith Ewok 2 polished (new engine)

A second pass on the 0180 drawing, of my own initiative (the user had said
most things looked OK), each change checked against the user's sheets by a
separate checker as better with nothing worse:
- From behind, lit: his feet as tall as when the saber is off (they were
  flat slivers), the lit walk with a real stride (the raised foot's sole as
  sheet 3 shows it, the hem swinging); a stray outline under a raised foot
  gone (lit and off).
- Lit, standing: the robe's folds crisp down to the hem (a blurred band
  there before).
- Lighting up: the first frame takes the hilt from his belt with both paws
  (front, side and back), the next raises it; the belt shows no hilt after;
  his stance widens from standing into the sheet's over the first frames;
  stray orange specks on the robe from behind gone; the sleeve across his
  belly shaded with folds.
- The blade crackles more: a ragged red edge with flickering points, more
  sparks near the cross-guard; its two crackles still differ only in sparks
  and haze.
- The saber-off walk is as before (a proposed change to its third step made
  it limp, so it was left out).
- tools/custom_characters.py: his section's frames only (the colours, glow,
  shine and every other frame byte for byte the same; the frames equal the
  checked drawing's); engine/common/scummverse_custom_cast.inc regenerated.
- Tested on the desktop build only (the cast check: he lights, walks lit,
  puts it out). Not tested on an iPhone.

## Patch 0183 — The Curse of Monkey Island's verb coin (new engine)

The user sent FONT0.NUT to FONT4.NUT (kept in the ignored game-data folder,
never committed); with them The Curse starts and its controls can be taken
from the user's own copy, as Full Throttle's were (0114):
- Its coin: hand, skull and parrot over a thing, opened by a held press;
  the part under the finger lit, its verb done when let go. The thing's name
  goes on the line at the bottom of the screen, centred, as the game shows
  it (without the verb before it).
- Its chest: a right click (the two-finger tap) opens it as the game draws
  it; the things carried in a grid of cells (6 across, 4 down, laid out from
  the one thing seen at its start). No arrows: it has none.
- The export taps the plain game on its first menu, skips its films, and
  waits until the player has the pointer. Its lettering is the fonts' plain
  letters. Full Throttle's export is byte for byte the same as before.
- The new engine's panel: a coin's name on a fixed line, and a box with no
  arrows (the verb test no longer asks a coin game for arrows it has none
  of).
- The Curse's places are re-exported once at the next launch (comi-v23).
  On the phone it needs its RESOURCE folder (with FONT0..4.NUT) in
  Documents/comi.
- Tested on the desktop build only: the panel unit test (ASan/UBSan) with a
  new case for the Curse's layout; the sandbox suite; the export from the
  user's copy, its verb test (12 panels, 2 coins) and screenshots of the
  coin and the chest. Not tested on an iPhone.

## Patch 0184 — Maniac Mansion's own story; the app goes on in the story it was in

Story play's next steps (the user's "all 12 games playable start to finish",
"save, and it saves all your progress"):
- Maniac Mansion's original story is one of the games in "Play the original
  games" ("Maniac Mansion (original story)"): the same data the mansion plays
  from, with none of the mansion's additions (no roaming, doors, safety,
  other worlds, visitors, custom characters or camera). Its saves are its own
  ("Story", slot 99), apart from the mansion's; leaving it brings the mansion
  back where it was, and Go to takes it to another game's story and back.
- The app goes on where it was left: put away or stopped in a game's story
  (after it has played a few seconds), the next start opens that game again
  from its newest save (its story save or the autosave); Back to Maniac
  Mansion then brings the mansion back where it was. A game whose folder or
  needed files are gone is not opened; a game that cannot start goes back to
  the mansion. Once the mansion is playing, the next start is the mansion.
- The story menu (Worlds, in a game) has Save now: it saves where you are
  (its "Story" save) and the game goes on.
- In any story game the Talk, AI and Camera buttons, the conversation bar
  and Arrive are hidden (a chat left open shuts; the Worlds button stays, to
  leave); the camera also refuses in the engine.
- A story's target named on the command line is refused, the mansion's own
  story included, however it is spelled (only the mansion and the sandbox
  start the app).
- Fixed after an independent review: the guard's spelling (a target named in
  capitals got past it); a "Go to" refused for missing files left later
  quits unsaved; a save and an autosave in the same minute are now told
  apart by time played; the conversation bar and Arrive stayed over a story.
- Tested on the desktop build only: the startup tests (20; new: the
  mansion's story target set up from the mansion's folder without its
  additions and refused on the command line in any spelling or by its key;
  a stopped story gone on with, then the mansion; one whose folder is gone
  dropped; the mark taken even when the sandbox starts) and the story probe
  with the mansion's own story first (opened, saved, back, reopened exactly,
  game to game; every story started without the additions; then the app
  started again in the last game, where it was, Save now there, and the
  mansion after it): 9 games passed (the mansion's own story, Monkey Island,
  Loom, Indiana Jones and the Last Crusade, Fate of Atlantis, Day of the
  Tentacle, The Dig, The Curse of Monkey Island, Zak McKracken), Full
  Throttle refused here (its DATA files are missing from this copy). After
  the review's fixes, the mansion's own story, Monkey Island and Loom again,
  with the stopped-app test made stricter: the app started in Loom's story,
  Save now, the engine's own mark found on disk, an autosave, the app
  stopped at once; started again with nothing put in, it went on from that
  newer autosave (same minute: told apart by time played), Save now, then
  ScummVM's menu saved it again on the way out (passed).
  The iPhone menus and the hidden buttons are compiled for iOS only by Apple
  CI; not tested on an iPhone.

## Patch 0185 — the original games from the new engine; an imported Zak's story

- The new engine's Worlds menu has "Play the original games" too (the same
  list as the mansion's). Opening one keeps the new engine's place, plays the
  game from its newest save, and leaving it brings the mansion back where it
  was when the new engine was opened.
- On the phone, a Zak brought in with "Import Zak from this app" (kept in the
  app's own storage, not in Documents) can now be played as a story; before,
  only a Documents/zak folder counted. The app adds a drive for its own
  copies of game files, as ScummVM does for the app bundle.
- Tested on the desktop build only: the new engine's suite (all of it, with a
  new switch: the mansion -> the new engine -> Maniac's own story, left by
  ScummVM's menu and saved on the way out -> the mansion where it was), the
  startup tests (20). The imported-Zak path is iPhone-only: syntax-checked
  here with the iPhone setting on; compiled for iOS only by Apple CI; not
  tested on an iPhone.

## Patch 0186 — Story mode and Explore mode kept apart; copy protection answered

The user agreed story play should be separate from exploration ("Story mode
should be separate from exploration/open world mode") and asked to fix the
open issues:
- Two modes. Explore mode is the mansion, the other worlds and the new
  engine; Story mode is the original games, each as it was made. The Worlds
  menu switches: "Story mode (the original games)" from the mansion or the
  new engine (the mansion saves where it is, even on its kids' screen; the
  new engine its place), "Explore mode" from inside a game (saved; the
  mansion comes back where it was). The app reopens in the mode it was left
  in, and in Story mode in the game it was left in.
- Story mode's home is its list: each game found, "Continue" or "Start",
  Maniac Mansion's own story among them, and "Explore mode". Leaving a game
  ("Story list" in its Worlds menu, or its own Quit) goes back to the list,
  never to the mansion. A game whose copy lacks a file it cannot start
  without says so ("Full Throttle (needs ROADRASH.RIP)") and is not opened;
  one that plays on without its films, voices or music says that too
  ("(no films, voices and music)"). Story games show text by default.
- Monkey Island 2's recipe screen (its copy protection, which ScummVM leaves
  to the player and which takes any number) is answered by story play, so it
  starts like the others. Sam & Max's dress-up screen checks a real answer (a
  wrong one makes the game quit; pressing its button passed only sometimes in
  testing), so it is still the player's; decoding it is the next step.
- Found while testing: a Sam & Max story save made the moment Sam reaches his
  office (right after its intro is skipped) loads into a script error (room
  92, object 0) that stops the game; under investigation.
- Fixed after an independent review: a game left for the list stayed marked
  to reopen at the next start; Sam & Max's press could stay held; Story mode
  could be taken while the mansion booted or exported; folders added while
  the app runs were missing from the list; a list withdrawn could still
  appear later; and five tests that could pass with the feature broken.
- Tested on the desktop build only: the startup tests (22: Story mode's list
  first, a story chosen, one needing files not taken, Explore; going on only
  in Story mode), the story probe over 10 games (Maniac's own story, Monkey
  Island 1 and 2, Loom, Indiana Jones and the Last Crusade, Fate of
  Atlantis, Day of the Tentacle, The Dig, The Curse, Zak; Full Throttle
  refused, its DATA missing here; Monkey Island 2's recipe answered), the app
  stopped and gone on (from a newer autosave), Save now, and a Story mode run
  (the list, Story list, Maniac's own story, Explore mode, Story mode from
  the mansion through its menu's request, the list, Explore), and the new
  engine's suite (with Maniac -> new engine -> Story mode -> Explore). The
  iPhone list, menus and hidden buttons are compiled for iOS only by Apple
  CI; not tested on an iPhone.

## Patch 0187 — Sam & Max's copy protection answered; its early saves reload

Following the user's "Let's fix all these issues":
- Sam & Max's dress-up screen (its floppy copies' copy protection) is now
  answered by story play, as Monkey Island 2's is: a press wakes the
  wardrobes; the game names a page of its manual and a doll; the clothes
  that page asks for are read from the game's own table at run time (never
  copied into the project), put on, and its button pressed. Read from its
  scripts: a wrong answer gets one more chance, then the game quits; and its
  check, as compiled, only ever looks at the doll's first item, so a bare
  press is wrong on one page of ten (page 4) and right on the rest. That is
  why pressing alone passed "only sometimes" before.
- The Sam & Max save that would not reload (a script error naming room 92,
  object 0): its after-load script sets the cursor from a variable the game
  has not set yet just after its intro. ScummVM already skips that for room
  93 (its bug 14467); it is now skipped for any room.
- The story test has Sam & Max in its default list again, held to page 4
  (the page a press alone gets wrong); it requires the dolls dressed and
  left with no wrong answer.
- Tested on the desktop build only: the story test with Sam & Max (held to
  page 4, Sam's doll: dressed and right the first time; its office save,
  made just after the intro, reopened three times exactly as saved), the
  startup tests (22), the bootstrap test and the IPA stamp. Not tested on an
  iPhone.

## Patch 0188 — Sam & Max's dolls: the review's fixes

An independent review of 0187 found two real problems, both fixed:
- The press was sent as mouse events, which ScummVM halves in some render
  modes (Sam & Max offers EGA): there it would land on the clothes, not the
  button. It now sets the game's own mouse position and a click for the
  next frame, in the game's screen coordinates, as a tap ends up.
- The test could pass with the press broken: its own clicker (used for
  other games' openings) could press the button itself. It no longer clicks
  on Sam & Max's dolls, records when they were left, and is held to a doll
  as well as a page (Max by default; 0187's run had Sam).
- Also from the review: after a wrong answer (a second would end the game),
  or if the page's clothes are not all found, the screen is left to the
  player.
- Tested on the desktop build only: the Sam & Max story test (page 4,
  Max's doll: dressed and right the first time, with nothing else clicking;
  then its saves as before) and the bootstrap test; and a control run with
  the dressing switched off, which the test failed as it should (the game's
  one more chance taken, then the screen left to the player and the game
  still running). Then the whole story test over 11 games (Sam & Max
  among them, through its dolls to Sam's office; Full Throttle refused
  here, its ROADRASH.RIP missing) passed. Apple CI built the IPAs of 0187
  and 0188. Not tested on an iPhone.

## Patch 0189 — Loom's dark rooms: their holes filled

The last of the older exploration list's picture items ("holes in Loom's
dark rooms 26, 28, 31, 50", reported unfixed since 0089):
- Found by logging the exporter's hole test in those rooms: there a hole is
  covered by several tiles a frame (the dragon's hoard, the cave pool, the
  tower's doorway), the other frames being objects the same size in the
  same places. Each tile alone failed the test, the picture around it being
  dark (a night or cave room) or other tiles. Now a black tile with such
  twins counts as a hole too (not the close-up corner at the top left), and
  is filled, as before, only by a frame that lights at least half of it.
- Changed: the dragon's lair (28: the dragon on its gold), the cave pool
  (31: the water), the Elsewhere path (50: the top of its middle), the
  tower (35: its lit doorway) and Bobbin's tent (6: the hanging cloths and
  the floor); room 26 was already right. Each compared with the previous
  export by eye; the other Loom rooms are unchanged. A little of the lair
  (left of the hoard) and of the Elsewhere path's middle stays dark: every
  frame there is dark too.
- Loom's export is one version ahead (its scenes export once more on the
  phone); tools/test_world_setup.py reads the per-game versions again (its
  pattern had not matched since 0183).
- Tested on the desktop build only: the Loom export and the comparison, the
  world setup test with Loom. Not tested on an iPhone.

## Patch 0190 — Monkey Island 2: Dinky Island's jungle and the tunnels under it

From the older exploration list ("run-time doors in Monkey Island 2 and
Fate of Atlantis"). Those doors lead where the game decides as it runs, so
the door map (which lists a door's room only when the analysis can read it)
had dropped them: the jungle's exits all led to the beach, and the tunnels
under Big Whoop were cut off. Five areas of the two games were decoded from
the games' own scripts by one agent each and checked by another (private
analysis, never committed: build/foreign/dynamic/); this patch takes Monkey
Island 2's two:
- The jungle (rooms 96-98, which the game shows as 13 places): every one of
  its 18 exits now leads somewhere fixed. Where the original's own table
  says (the parrot's route: east, north, east, from the beach to the X
  clearing) it is followed; where the original rolls a random place, one of
  its possible outcomes is chosen so that exits pair by side (out on the
  left, back in on the right).
- Under the X: the tunnel junction (93, which the game shows as eight
  places) is exported as its elevator hall with the ceiling hole above and
  the back door beside the elevator; its left, right and back doors lead to
  the storage, first-aid and maintenance rooms and the elevator to the car
  (88), now exported with its gates open on the tunnel wall (it was a black
  void); the lever takes the car up to the street (89). The hole leads back
  up to the X, and the X down (the original's dynamite, left out). The two
  ends of Phatt Island's tunnel lead to each other.
- How: tools/world_maps.py takes fixed doors from the checked private
  tables (they replace the analysis's links for those doors; doors into a
  room with no exported scene are left out); the exporter can give a room
  one of its run-time looks (catalog: kWorldPresetStates, the objects'
  pictures, and kWorldPresetPlaces, where its scripts draw one elsewhere),
  writing those states in the scene. Monkey Island 2's export is one
  version ahead, so it exports again on the phone. The jungle and storage
  room menu entrances are no longer needed.
- tools/test_ai_encounters.py's stand-in for the phone's runtime (shared by
  the engine probes: the door walk among them) lacked two functions added
  in 0184 and 0186 (Story mode's), so those probes no longer linked; added.
- Tested on the desktop build only: the new export of both rooms compared
  by eye with the old; the walk through every door of every world (passes:
  1,589 doors, 69 failing within its allowance, two of them new ones: the
  car's door and the elevator's, which the same walk over just these rooms
  takes correctly, each door to its room; in the long walk the tunnels'
  rooms share the visit slots with the others). Not tested on an iPhone.

## Patch 0191 — Fate of Atlantis: the labyrinth, the rings and the travel screens

The rest of the older list's "run-time doors in Fate of Atlantis", from the
same checked private tables as 0190:
- Knossos's labyrinth and catacombs: the two template rooms (50, 51; the
  game shows them as 38 cells) are exported each as one cell, furnished by
  the game's own entry script for that cell (cell 161, five doorways; cell
  169, its gate's walk box on with a head on the shelf), with that cell's
  doors only: out to the Crete hillside, the elevator, the catacombs, the
  map room, the hideout, the gold-box rooms.
- Atlantis's rings: the overhead plans' doorways (85-88) lead where one
  game's shuffle of the outer ring puts them (the state the analysis found
  in about one game in five: the machine room, the statue room, the lava
  room in their usual places); the outer ring's chamber (92) shows its
  three doors, one leading on into the middle ring (94, its four doorways
  shown, cut to its 144 rows as the game shows it), the inner ring's
  doorway (93) too; the pit room (14) has its pit open, as after the
  digger.
- The travel screens: the Sahara (20) is exported for the first time, as
  the screen with the dig site, on camels (the desert's camel doors stay
  off until the exporter draws the camels, which are actors: the balloon is
  the way in); the sea (95) shows its islands, the way on
  from the dig site's inflated balloon; the chamber of doors (44) its open
  doorways; the dig site (67) its rope ladder; the world map (75) its dig
  site.
- The exporter can now export a v5 template room as one of its instances
  (catalog kWorldPresetInstances: VAR_ROOM the instance, its variables and
  classes set first, the game's state put back after), switch walk boxes
  for a look (kWorldPresetBoxes, the box matrix rebuilt), clear a class for
  one, and cut a room to a height. Fate of Atlantis's export is one
  version ahead. Five menu entrances are no longer needed (the desert, the
  sea, Atlantis, the pool, the labyrinth elevator): doors reach them.
- The ring's four overhead plans (85-88) are maps here (a tap on a doorway
  goes there): their walk paths are thin lines a visitor could not follow,
  so their hallways failed the door walk before too.
- Left out after testing: a second way from the middle ring into the pit
  room, which lay over the doorway to room 16 (the pit room is reached by
  the ring's left edge, its pit and the digger), and the desert's right
  edge (invented; the walker could not reach it).
- Tested on the desktop build only: the new export of every changed room
  compared by eye with the old (the Sahara new); the walk through every
  door of every world (passes: 1,634 doors, 47 failing, against 69 before
  0190; none of 0190's or 0191's new doors among them: the rest are older
  doors in rooms where the walker cannot get about, Atlantis's hillside,
  chamber and dock among them); the same walk over just the changed
  rooms, each door to its room; the bootstrap, startup and world setup
  tests. Not tested on an iPhone.

## Patch 0192 — the mansion's and Zak's own people among the wanderers

Asked for in 0102 ("the mansion's and Zak's own characters in the wanderer
pool too"):
- The original engine's wanderers now take the mansion's and Zak's people
  too (26 with both games' frames exported: Nurse Edna, Weird Ed, Dr Fred,
  Sandy, Dead Cousin Ted, both tentacles, the plant, the Purple Meteor, the
  Meteor Police; Zak, Annie, Melissa, Leslie, Lou, the King, the Caponian,
  the guards, the Guru and the rest), drawn from their exported frames like
  everyone else's, each game's people one game's share as before.
- Never in their own game's places: this engine plays the mansion and Zak's
  world with their own actors, so the mansion's people roam Zak's places and
  the other games, Zak's people the mansion and the other games (never two
  of anyone in view). Wander::Cast marks them away; setting out, doors,
  joining and the pull toward the player all keep them out of their own
  game (with nowhere else to go they stay home).
- The mansion's seven kids are not among them: they are the party played
  there, taken along to other worlds.
- A visiting one steps aside (not drawn) while their own actor is in the
  room (Nurse Edna when her actor is there) or someone there plays their
  look from the character screen (the Purple Meteor, the Meteor Police, the
  plant, Ted; Zak's people by name).
- Saved games: the cast is new, so everyone sets out afresh once (as when
  games are added).
- Hardening from the review of 0189-0191 (no defects found): a staged room
  puts the game's state back after its export too, like an instance. That
  showed one thing that had leaned on the leak: Fate of Atlantis's pit room
  (14) script reads its pit, and its things (the pit and what is by it)
  were touchable in the things file only because the room's scene, staged
  with the pit open, had left that state behind. A staged room's pictures
  are now set before its scripts run as well as after, so the same file
  comes from its own room whatever ran before. Re-exported: all 217 of
  Fate of Atlantis's and Monkey Island 2's files the same as before, byte
  for byte. The fixed door tables count an emptied scene file (a room
  whose export failed) as not exported (the door map the same).
- Tests: test_wander.cpp (away ones never in their own game: setting out,
  doors, joins, jumps, toward the player; nowhere when there is nowhere else;
  through the game's side; ASan/UBSan, TSan); test_wander_engine.py (287
  out, 26 the mansion's and Zak's, none in their own game's places at the
  start, after half an hour or ten minutes by the kitchen; the kids not out;
  Nurse Edna and Lou drawn visiting Monkey Island; the visiting Purple Meteor
  stepping aside while Dave plays it and back after; Edna stepping aside for
  her own actor). Tested on the desktop build only; not on an iPhone.

## Patch 0193 — every other-world door walkable in Maniac's own engine

The walk through every door of every world (test_world_visit) had 47 doors
failing in Maniac's own engine (Monkey Island 2, Fate of Atlantis, Loom,
Indy 3, Full Throttle, the Dig, Curse and Monkey Island). A probe tracing
the walks (private, not committed) found three causes:
- The routes: a V1 room keeps a one-byte start for each row of its
  next-box table, so in a scene with more than 16 walk boxes (other games'
  rooms, converted, often have 20 to 60) the later rows wrapped round to
  another row's numbers, and the walker went the wrong way round the room
  and gave up (Monkey Island's room 65: round six boxes and back). The
  engine now finds a converted scene's rows by number past that point
  (getNextBox; Maniac's and Zak's own rooms read as before).
- Boxes the conversion leaves a diagonal step apart (Loom's room 10) were
  not joined: the scene file already holds the game's own box connections
  (as the new engine uses), and boxes it connects directly are now joined
  too while they are still close (never to a game's dummy box, a point in a
  corner that many connect to).
- The loop guard stopped a walk the first time it came back to a spot it
  had passed, which a path round the end of one box into the next does
  once (Loom's room 32): now the second time.
- The test taps each door where no other door covers it (as a player taps
  what is shown), nearest its middle; a door wholly under others is tapped
  in its middle as before and, if it then leads elsewhere, counted apart.
- Walk test: 1,680 doors through, 0 failing (47 before); one covered
  (Loom's room 22 shows one doorway in two states, to rooms 17 and 18; 18
  is reached from 16 and 20). More than one in a hundred failing is now a
  regression (was one in twenty).
- An independent review (read only) found no engine defect; from it:
  boxes that cross like a plus sign (no corner inside the other) now count
  as touching; a box that is a single point is never joined through the
  game's table; the loop guard's one step back is forgiven again once the
  walk reaches new spots (two corners in one walk); and the test counts a
  door as covered only when a tap can land on it at all and it then leads
  through one of the doors over it (a tram stop never), else as failed.
- Tests: test_world.cpp (rooms joined by their game's table only when
  close, never a point; crossing boxes; ASan/UBSan), test_world_visit.py,
  and the engine tests that walk
  there: wander, tour, camera, lights and doors, world setup, sandbox engine;
  startup, bootstrap, package_ipa.
  Tested on the desktop build only; not on an iPhone.

## Patch 0194 — the new engine's last doors: out of Loom's dragon's lair

After 0193 the new engine's own walk through every door had 18 doors
"short" (the walker stopped and did not go through). Traced one by one,
none was a walk that failed:
- Loom's dragon's lair (28): its one way out lies wholly under the dragon,
  the gold and the straw, and Loom's distaff takes things before doors, so
  no tap found it: in the new engine the lair could only be left by the
  menu. Now a door wholly under things, with no other door here a tap
  finds leading where it does, is taken before them where it lies (the
  dragon is still chosen above the doorway). Loom's crystal room (18) has
  such a door too, but the bell's doorway leads the same way, so its
  crystal is still the thing chosen there.
- The test now taps as a player does: the engine's own reach for doors
  (four pixels, the test had two), the spot checked where the tap lands
  after the screen and back (a pixel's rounding brought one of Loom's
  things within reach); a door wholly off the picture (the second way out
  of 13 of Monkey Island's forest rooms, beside the first) counted as not
  shown; one inside something shut (the grating behind the mansion's
  bushes, two others) opened first, as a player opens it; one under things
  with another door the same way counted apart.
- An independent review (read only) found three things that today's
  files do not trigger but could: a tap now skips a thing only for the
  door the tap itself takes there, and only one that a tap would find
  without the things (not one under another door, nor inside something
  shut); the test counts a door apart as having another door the same way
  only when such a door is found, and checks a spot under a door by the
  tap's own rule; containers the test opens are shut again after each
  door, and one that cannot be shown open counts the door as not shown.
- Door test: 1,915 tried, 1,914 through, 1 elsewhere, 0 short (18 before);
  more than one in a hundred short is now a failure (test_sandbox_engine).
- The tour: its two doors not reached were in Fate of Atlantis's labyrinth
  chamber (43), nearly three screens wide, whose doors at either end were
  forty seconds' walk apart, the tour's limit for a walk to a door: that
  limit now grows with how many screens wide the place is (0 not reached,
  769 stops).
- Tests: test_sandbox_engine.py (all of it). Tested on the desktop build
  only; not on an iPhone.

## Patch 0195 — the mansion's main power (new engine; step 5)

From 0141's "not yet": the original's fuse box and breakers.
- In the new engine, the circuit breakers in the basement (in the fuse
  box, opened first) turned off make the house dark where the mansion's
  own room scripts leave it dark with the main power off: 27 of its places
  (the basement, the halls, the kitchen, the bedrooms and the rest
  indoors; outside, the garage, the lab's rooms and others stay lit). A
  lamp turned on there stays dark without the power; the flashlight still
  lights its window. Turned on again, every place is lit as before (those
  whose own lights were turned off stay dark). Kept with the rest of the
  mansion's state.
- Which places, from the game itself: the export runs the breakers' own
  turn-off script from the game's start, then arrives in each place as a
  kid does (its entry scripts run) with the power on and with it off, and
  lists those lit with it on and dark with it off (a probe of every room
  1..52 agreed). The mansion's things file is "SVO5": "SVO4" with the main
  power (room, object, its picture off) and those places after. The
  mansion is exported once more (maniac-v30); the other games are not.
- An independent review (read only) found nothing wrong with this data;
  from it: the export writes the main power only when the breakers' own
  script turned them off and some place is dark then, and only where the
  lights are a variable it keeps (not the C64's), all of the game's state
  kept for the arrivals with it off; a file whose main power is none of
  its things, or starts in its picture off, is read with no main power (the
  house is never dark from the start); the check turns a lamp off and on
  (on is then the lamp's own answer) and expects the basement as the list
  has it.
- Tests: test_panel.cpp ("SVO5" read whole or not at all, by game and
  place, a nonsense power dropped; its documented -Wshadow build works again: 0171's own block had
  names shadowing others); test_sandbox_engine.py (the verbs check opens
  the fuse box, turns the breakers off as a player does: every place of
  the list dark on going there, the others lit, a lamp there dark still;
  on again, all lit; the mansion left as found). Re-exported: of the
  mansion's files only the things file differs, by its new end. Tested on
  the desktop build only; not on an iPhone.

## Patch 0196 — local WiFi play in the other worlds

From the PR's known remaining list: "players are not relayed in other
worlds". Each device keeps the other worlds' places in slot rooms of its
own (192..199, filled as places are visited), so a slot number meant
nothing on another device and those rooms were not sent at all: a friend
in Monkey Island vanished from the mansion and was never seen there.
- Now the place is sent (its game and that game's room), and the device
  receiving it puts the character in its own slot for that place (the one
  it is already in, else a free slot), only where that place's scene is
  installed. Both see each other there, walking and talking as in the
  mansion.
- Somewhere a device can't show (a place not installed there): the
  character is away from every place on that device (not seen) and still
  its player's, so nobody there can play it, take it along or chat with
  it. A place found missing is not looked up again until the player moves.
- A friend leaving (or the WiFi dropping) while in another world's place:
  their character goes home to the mansion. Another world's slot is never
  kept by a character nobody plays (before, enough of them used up all
  eight and no new place could open). Characters left by this device's
  own player in another world's place go home too, a while after the
  player has gone (a save loaded with one there as well).
- Devices of different builds do not join (the build identity is 79 now).
- Not yet: someone playing a look from the character screen is seen as the
  cast member they control; riding the tram, van or plane together on two
  devices.
- An independent review found the two problems above in the first
  version (a character not kept for its player in a place not installed;
  released characters stuck in slots); both fixed before commit.
- Positions in another world assume both devices exported the same
  edition of that game (as the build identity assumes the same build).
- Tests: test_net.cpp (a place round trips; rooms between the mansion's
  and those refused when sent and when received; ASan/UBSan, TSan);
  test_net_engine.py (over loopback: a room and a place not shown here,
  away and still the player's; the remote in this device's own slot for
  Monkey Island's dock, the local player gone there sent as the place,
  back to the mansion; released from the dock, home; one left there, home
  after a while). One process on one machine: not two devices, not an
  iPhone network test. The full data suite passed at 0195 (44/44, Story
  mode too).


## Patch 0197 — WiFi play: friends see the look you play

0196 left this open: someone playing a look from the character screen
(Guybrush, Dead Cousin Ted...) was seen on the other devices as the cast
member they control.
- Each player's avatar now carries the look played. Each device shows it
  where it has it (its own catalog, and that game's characters exported
  there); one it hasn't (a custom character, played only in the new
  engine; a game not set up there; one of Zak's people where Zak's files
  aren't there) shows the cast member itself. Shown quietly: no "You are
  playing..." notice, nor a Zak files notice, on someone else's device.
  A burst of look changes is tried once (at most every quarter second).
- Saves keep the characters' own looks, never a friend's: the look is
  taken off for the save and put back after it (a friend's character
  walking then goes on walking: a costume change stops a walk). A save
  loaded during a WiFi game: the friend's look goes back on; loaded as
  the character a friend plays, it is the local player's again (the
  friend's frames ignored, as before). When the friend leaves, the
  character gets back the look it had before they came. (Still as before:
  after a load, friends' characters stand where the save has them until
  their players move.)
- WiFi events not yet handled when a game ends (or another starts) are
  dropped, so none reaches the next game.
- Devices of different builds do not join: protocol 2 (the avatar frame
  is two words longer), build identity 80.
- An independent review found the save, load and Zak files problems
  above in the first version; fixed before commit.
- Tests: test_net.cpp (the look round trips in 32 bits; none above the
  limit sent or received; relayed from one client through the host to
  another; ASan/UBSan, TSan); test_net_engine.py over loopback (Zak
  playing the Meteor Police before his player comes, kept for him; a
  Maniac look, Dead Cousin Ted, shown without a notice, and a Monkey
  Island look where exported (it was here); Crispy, not here, as Zak
  himself; Zak himself again; costumes checked; the local player's look
  sent; a real save while Zak walks: it holds his own look, he walks on;
  loading puts the friend's look back; on leaving, the Meteor Police
  again). One process on one machine: not two devices, not an iPhone
  network test. Not tested: a device without Zak's files.

## Patch 0198 — the new engine: flights seen from the cabin, the van from its cockpit

Step 5 of the new engine (rides), from its "not yet" list: followers did
not sit in the plane's seats or appear in the van's cockpit as Maniac's
own engine shows them; the one played simply vanished for the trip.
- Zak's plane cabin and the Shuttle Bug's cockpit are now exported with
  Zak's places (his export is redone once). They are not places: not in
  the menus, the tour or the checks of every place, never where the game
  resumes (a flight closed midway resumes at the stop it left from).
- A flight: once boarded, the cabin. The one played sits in the seat Zak
  takes in the game, those following in the empty seat behind, then in
  the painted passengers' seats (each given the empty seat's back over its
  passenger); more than six aboard, the rest unseen. Everyone is seen from
  the side, sitting (their seated pose where they have one, as Fate of
  Atlantis' camel does, else as they stand), heads where the painted
  passengers' are; anyone too big for that (the camel) is made smaller
  till they fit. Each seat's front is drawn over them, with the dark under
  the cushion as under a painted passenger (as in Maniac's own engine).
  Nobody gets up, nor for a selfie; ten seconds later, the gate where it
  lands.
- The van: once it lifts off, its cockpit, everyone at the controls unseen,
  then the site where it lands.
- While aboard: a tour begun goes home to the stop the ride left from; a
  character chosen goes where they live (the ride is given up); the chat
  asks no one along nor to stay; the Worlds menu's Board the Shuttle Bug
  does nothing; a custom character can't be chosen (they are played where
  the player is, and the cabin is no place).
- An independent review found, in the first version: the seated poses never
  shown (the stage took only standing, walking and talking poses), short
  people in the painted passengers' seats hidden behind the seat's back,
  heads not lined up for seats off screen, a tour begun aboard (or a
  failed choice of character) going back into the cabin, a selfie undoing
  the seating. All fixed before commit; the check now covers them.
- Still: a big one's legs can show beside the seat's front (the front is
  only as wide as a seat); a seated pose's part over the seat's front (a
  leg over the armrest, in Maniac's own engine) is not drawn.
- Tests: test_stage.cpp (a piece of the place's picture drawn over whoever
  sits behind it, by the row asked; someone seated exactly where asked;
  made smaller; ASan/UBSan); test_sandbox_engine.py (all 9 flights seen
  from the cabin; on the first five following, the camel among them in its
  seated pose, everyone in a seat of their own with their head in line and
  seen (drawn, not covered), a selfie aboard keeping them seated, nobody
  getting up; a tour begun aboard home at the stop; the 3 van flights from
  the cockpit; the tour 769 stops without the two insides; the whole
  sandbox check passed). Pictures looked at on the desktop (cabin.png,
  cockpit.png). Not tested on an iPhone. Seated poses exist only for the
  characters that had them for Maniac's own engine; the others sit as
  they stand, partly hidden by the seat's front.

## Patch 0199 — the new engine's plane: the big ones too big for their seats again

User (2026-10-23), on 0198's cabin, where anyone too tall was made smaller
till they fit: "The camel is supposed to look too big for the seat."
- Everyone aboard now sits as Maniac's own engine seats them (the same
  cabin, the same rows and numbers): the big ones it lists (Fate of
  Atlantis' camel, The Dig's Creator and nest monster, Sam & Max's dragon,
  Monkey Island's three-headed monkey) crammed in from the overhead bins
  down, part of them below the seat's front, at least as wide as the seat,
  hilariously oversized as the user asked for Maniac's own; anyone else no
  taller than a seated teenager nor wider than the seat, sunk to the
  cushion (the small ones) or to their waist.
- The stage can now make someone taller and wider by different amounts.
- Tests: test_stage.cpp (fitted taller and wider; ASan/UBSan);
  test_sandbox_engine.py (the camel crammed from the bins' row, as tall as
  Maniac's own engine makes it; the others sitting in their seats; the
  whole sandbox check passed). A picture of the cabin with the camel was
  looked at on the desktop. Not tested on an iPhone.


## Patch 0200 — Sith Ewok 3, Crispy 2 pees, Suzy 4

User (2026-10-23): a new Sith Ewok whose lightsaber comes to his paw by the
Force (as in the video they sent), who swings it and shoots force lightning,
and who answers anyone who mocks him; Crispy 2 lifting his leg to pee at P,
the puddle drying to a stain; a Suzy 4 looking straight ahead.
- Sith Ewok 3 (a new custom character; Sith Ewok 2 unchanged): Sith Ewok 2
  with moves drawn from the side by an artist panel. Played: L once (after a
  third of a second without a second L) a force grab (his paw out, the hilt
  flying off his belt into it, both paws, the blade out), or with it lit,
  put away by hand; L twice a swing right then left with glowing trails
  (not lit: just taken up); F blue-white force lightning for a second and a
  half, from both paws, or the free one with it lit. Walking, a key stops
  him first (at the first L). Not played (left in a place by playing
  another custom character), now and then (every three to four minutes,
  only standing near the one played, not following or talking) a show: the
  saber taken up, swung once or twice, put away; or lightning into the air.
  After a move, half the time, whoever is nearest heckles him and he
  answers back (now and then in angry Ewokese); text only, no one else
  moves. With the iPhone's model in use the lines are its own, in each
  one's personality (his the user's approved one); without it, while a
  chat is open, or when it is slow (four seconds), written lines. A heckle
  waits for anyone else's line to end, and is let go if they talk on.
- Crispy 2: P lifts his far hind leg (mirrored facing left, so always the
  far one) for three seconds, from the side; walking, he stops first. A
  small puddle where the stream lands, spreading while he pees, drying over
  twenty seconds to a stain; each place keeps its stains (twelve at most,
  the oldest let go), saved with the sandbox's state (SVS3) and so kept
  after quitting. Not played, now and then (every two to four minutes) he
  walks to a door or thing nearby and does the same.
- Suzy 4 (a new custom character; Suzy 3 unchanged): Suzy 3 facing the
  viewer squarely and looking straight ahead, her smile as the user called
  perfect, the chin and neck as the user corrected them, by an artist panel
  from Suzy 3 and her photo (not kept).
- Custom characters left in a place (another custom one played) stay only
  until the place changes; they do not roam as the wanderers do.
- Two independent reviews found, in the first versions: a move or a pee
  turned to the other side by a talker faced mid-move (the puddle left
  under his head), a lit Sith Ewok 3 arriving in a new place turned to the
  right, the first L not stopping a walk at once (a door gone through
  meanwhile), heckles said over others' lines, a walk's sentence left
  shown, a pee cut short still spreading a full puddle, the waits for a
  show or a pee on his own running down while he was played (then at once
  once left), a stain not saved at once, a dog peeing mid-conversation
  after his walk, a fresh puddle shown dry on coming back, and the
  generator not making the include it claims to. All fixed before commit,
  each with a check.
- Tests: test_stage.cpp (the moves and the leg lifted from the side, kept
  to the side last faced, not turned mid-move; art points; marks spreading,
  drying, cut short, under everyone, not in the dark, the oldest let go;
  ASan/UBSan); test_talk_runtime.py (the model's remark job, refused during
  a conversation and while one is out; ASan, TSan); test_sandbox_engine.py
  (a new moves check: the keys, walks stopped, heckles written, the
  stand-in model's and slow, waiting for others, shows near and not far or
  walking; Crispy 2's pee both ways, stains back again, saved and read
  back, at most twelve, on his own, cut short, entered again; 11 custom
  characters on the character screen; the whole sandbox check passed);
  test_custom_characters.py (new: the include is what the generator
  writes); startup, bootstrap, package_ipa. Pictures of each looked at on
  the desktop. The model's own heckles were tested only with a stand-in on
  the desktop (no model weights here). Not tested on an iPhone.

## Patch 0201 — Crispy 2's stream where the user showed it; Crispy 2, Sith Ewok 3 and Suzy 4 roam

User (2026-10-23), with a picture of the first round's frame: "The pee
should come out like this from that direction/location"; and "Make them
roam the worlds like the other characters. Suzy too", then "I want the
newest suzy to roam. Also Extra".
- Crispy 2's stream now comes from under his belly and slants down to the
  floor between his legs, as in the picture, in the shipped frames' gold
  with a dark edge where it meets nothing (seen on any floor); his raised
  leg as shipped. The puddle lands there (the generator's mark: 15 art
  pixels behind his feet).
- Crispy 2, Sith Ewok 3, Suzy 4 (the newest Suzy) and Extra 2 (the newest
  Extra) roam the new engine's places with everyone else
  (kWorldCustomRoamers; the two dogs small, never part of a crowd): met
  anywhere, coming in through doors, asked along, talked with; Sith Ewok 3
  shows off and Crispy 2 pees on his own near the one played, as before.
  Not in Maniac's own engine (it cannot draw them). The other custom
  characters still appear only where the player is.
- Tests: test_sandbox_engine.py (the character screen's check: the four
  roaming, one sent here shown once, Crispy not roaming; the moves check
  with the new stream; the whole sandbox check passed); test_startup.py (a
  made-up place now shows the four roamers too); test_custom_characters.py;
  bootstrap, package_ipa. The new stream looked at on the desktop. Not
  tested on an iPhone.

## Patch 0202 — Gameplay fixes from a bug hunt across the new engine

User (2026-10-23): "Can you add more agents to this to get more done and
faster". Eight hunters read the new engine area by area (doors and travel,
verbs, chat and followers, rides, the custom characters, wanderers, the
mansion's moments, keeping progress and the camera); each finding was
checked by a test that fails without its fix where one could be written.
Fixed:
- Doors and travel. A place its game leaves only by a script (71 door
  arrivals over 17 places: Monkey Island, Monkey Island 2, Indy 3's floor
  plans, Atlantis' map room, Full Throttle, The Dig, Curse) has a way back:
  an arrow drawn at the place's left (a white triangle on a darkened
  square, mid-height), a tap on it back the way they came, told so on
  arrival, kept between launches (let go once elsewhere); other taps, at
  the edges too, walk as before. Monkey Island's and Indy 3's switched
  doors (shown open or shut): gone through open, the door back open too
  (24 pairs); two Indy 3 doors its game only walks through are doors
  always. Two ways out drawn as one (Loom room 22): the one whose walk-to
  point is nearer the tap. An arrival door's point off every box no longer
  lands on a lone box cut off from the floor.
- People. Everyone is placed, and walks about, where the picture is (not
  beside, below or at the very top of it) and in the one played's part of
  the place (116 scenes put someone off the picture before; now 0 of the
  298 people placed over all 779 places; the one played put in another
  part afterwards, as a launch, a tour's end or a switch does, the others
  go with them). Curse of Monkey Island's people
  are no longer drawn too small against the 320-wide games' (the height
  limit 4 -> 8). The Purple Meteor counts as small. Playing someone of the
  game's own who is here keeps the one played before where they stood; a
  custom character left beside who does not roam stays through the next
  switch here.
- Rides. Those following ride out of sight with the one played on Zak's
  bus, the Mars tram and The Dig's tram (not left at the stop walking
  about, not shown at the far station before the car). The Shuttle Bug is
  not boarded on the way on another ride (the player was left invisible);
  parked where is no longer installed, it is back at its own landing site.
  After a failed ride, a tour stopped or a choice refused, those following
  are put beside the one played again.
- Verbs. A verb chosen on the way to a door or a thing no longer drops
  the walk's goal (the kid stopped at the door); the flashlight left on
  stays on after a launch. More carried than a box's cells (Sam & Max's,
  The Dig's, the Curse's chest): its last cell turns the page (a white
  arrow; past the last page, the first again). Monkey Island 2's and Day of
  the Tentacle's panels draw their arrows (in the sentence's colour) where
  there is more.
- Chat (iPhone only). The name chips are rebuilt when who is here changes,
  not only how many (a door to as many others showed the last place's);
  with a hardware keyboard, the game's keys come back once the message
  field lets go (L, F and P did nothing until a pinch).
- Keeping progress. A save whose place or character has gone (exported
  again) keeps what was carried, changed and stained (it was wiped); kept
  while touring (where the tour began, with a stain or a thing taken while
  paused); Story mode chosen during a tour saves where it began; kept when
  iOS puts the app in the background.
- Custom characters. A pee cut short by the place changing leaves a puddle
  as big as it got (none before the leg is up); a heckle or Sith Ewok 3's
  answer waits for the line being said, his own too.
- The mansion's padlocked door (room 4): probed in the original (new
  tools/test_mansion_locks.py, in the data suite), the door stays locked
  until both its padlocks are unlocked with the key from the pit, the
  second unlocking it; then Open opens it. The things file has each
  padlock alone, so the door never opened; kManiacPadlocks now opens and
  shuts it once both show unlocked, and its doorway leads to room 31.
- Not fixed yet (found, real): the mansion's wall safe (room 9) cannot be
  opened by a player (its combination is not modelled); two garage things
  (room 16) cannot be picked up
  (their exported pictures are identical); a thing carried whose own place
  is no longer installed is let go on reading the save.
- An independent review of the first draft found the edge taking every
  tap near it (now the arrow), the others left behind when the one played
  is moved after entering, followers left hidden after a failed tram
  arrival, the way back kept after leaving and written during tours, a
  Loom note shown as the sentence, the rescue from a lone box skipped
  (it counted the door come in by), and a walk-only door back given its
  second picture: all fixed.
- Tests: test_stage.cpp (spots in the picture, with room, in a group;
  doors drawn as one); test_panel.cpp (a box's pages; picture panels'
  arrows); test_sandbox_engine.py (every place's people in the
  picture beside the one played, and with them when they are moved; every
  door, the arrow back from each place with no way on (drawn, a tap at the
  other edge a walk), the switched doors back open; a verb chosen on the way to
  a door; the padlocked door opened as a player does it; the flashlight
  kept on; the rides with someone following, the
  van not boarded on the way, called home; switching here; a save with its
  place gone, kept when paused; the tour's save and Story mode; the pee cut
  short by a place change; heckles waiting for his own line). The chat's
  two fixes are iPhone code, not compiled here. Not tested on an iPhone.

## Patch 0203 — things carried kept when their place is gone; the garage's things taken

Two more from the first bug hunt's list.
- A thing carried whose own place is no longer installed (a game taken
  away or exported again) was let go on reading the save. It is kept
  (_carriedAway: saved again with the rest, not shown) for when the place
  is back.
- The mansion's garage (room 16): the tools in the trunk and the water
  faucet handle, which its own script gives to the kid, were refused
  ("I can't pick that up.") because their exported pictures are the same
  with and without them (the garage's export has no picture of its own for
  any of its things). They are taken as the game gives them; the place
  looks as it did. (0162 refused such things so a taken thing would not
  stay drawn; for these two, needed for the mansion's puzzles, taking them
  matters more.)
- The wall safe (room 9), probed in the original: Open or Use takes the
  kid to a keypad (room 43, twelve keys); the combination is a clue found
  elsewhere. Not modelled yet.
- Tests: test_sandbox_engine.py's verbs check (a thing carried from a
  place gone kept through a save and a load; the mansion's things as their
  scripts answer, the garage's two taken: 849 records, 0 failed), the cast
  check, test_startup, bootstrap. Not tested on an iPhone.

## Patch 0204 — ways back from dead ends of any depth; small state fixes in the new engine

From the second bug hunt (a second pass over the new engine).
- The arrow back (0202) was drawn only in a place with no door at all. A
  place whose doors lead only further in, never back to where the player
  came from, left them stuck there. Now the arrow is drawn wherever the
  game's doors (installed ones, those it keeps shut too) cannot lead back
  to the place come from, nor to a ride, a tram stop or the parked van:
  reaches(), a search over the game's door map. Deeper in, the arrow still
  goes back through the door first come through. Leaving the region (a
  ride, another game) lets it go. The message is now "No way back from
  here".
- A tour begun in such a place keeps its way back: the tour's own moves
  no longer drop it or its saved copy, and the tour's end home brings the
  arrow back. If the way back cannot be shown (its place gone), the arrow
  goes and the player stays where they stood, told so.
- A long press while a door walk was starting cleared the door but not
  the walk's goal or a door seen opening.
- Play on a paused tour lets go of a sentence half made while paused.
- The insides of rides are not places among the wanderers (place() is 0
  there): nobody is sent to a plane's cabin to stay.
- Leaving mid-pee (Back, Story mode, the app closing) saves the puddle as
  big as it got, not full-size.
- A message told at the place before is gone on entering the next.
- "Fly the Shuttle Bug" during a tour ends the tour only where the van is;
  elsewhere the tour goes on with the van's whereabouts told.
- The tour's speed is remembered (scummverse_tour_speed, as the mansion's
  tour).
- Tests: the doors check (every dead-end arrival back by the arrow, every
  other one from a place further in first; a tap at the other edge may go
  through a door there, a walk); the tour check (a tour begun past a door
  with no way back, the arrow back after; a half sentence let go on Play;
  the van asked for elsewhere, the tour on); the suite's floors raised
  nearer what the data gives (the mansion's things, pairs, the main power,
  the chat in every game, no door leading elsewhere).

## Patch 0205 — iPhone: the keyboard, the tour's label, the screen kept awake

From the second bug hunt (the iPhone's own controls). Not built here: the
iPhone build (CI) compiles it; not tested on an iPhone yet.
- The chat hidden (turned to landscape with a message half typed and the
  chat not opened) lets the keyboard go; it no longer stays over the game
  with no field to see.
- The tour's label and bar stay in the game's half of the screen, as the
  picture is laid out with the chat open or not, on either side: never over
  the chat or the toolbar.
- The tour no longer puts its label and bar on top five times a second
  (each reorder laid the view out again); only when something else is.
- After a tour the screen stays awake while a game runs, as it does
  without a tour (it was let sleep).
- The on-phone model is loaded again only on coming back from the
  background, which unloaded it; Control Center, a banner or the Photos
  prompt no longer reload it and end the conversation.
- The Worlds menu reads Story mode or Explore mode from a flag the game's
  thread sets, not from the settings file the game may be writing.
- With a hardware keyboard, the game takes its keys back only when no other
  field (the tour's "Go to stop", the WiFi address) is typing and nothing is
  shown over the game.
- One finding left: a menu step said to run only after a dismissal; not
  shown wrong by the code, so left as it is.

## Patch 0206 — the chat: whom a chip talks to, where a sentence ends, what bubbles can show

From the second bug hunt (conversations).
- In Everyone mode a person's chip starts a talk with them alone (it
  added or dropped them from a group of everyone). A group down to one is a
  talk with that one: their chip shown chosen, Follow offered.
- A reply is cut at the end of its first sentence, not at "Dr.", "3.5",
  "...", "U.S." or "Wait... what"; while a reply is still arriving, a
  sentence counts only once what follows shows it ended.
- Maniac's and Zak's speech font draws some characters as other signs
  (=, \, _, |, ~, `, %): those are put as what they mean before a line is
  drawn; the transcript keeps them as typed.
- A character's last line, which a reply avoids repeating, is kept with
  who said it: another place's guests, renumbered wanderers and new parts
  that take the same number no longer get it.
- Someone played as another game's character speaks that character's
  classic lines.
- With the one replying taken out of a group, the next answers at once.
- Zak's residents' shared part is not offered Follow (the game refuses it).
- A message with nothing a bubble can show says so and starts nothing.
- Tests: test_text, test_scene_talk, test_talk_provider (ASan/UBSan, TSan)
  through test_talk_runtime.py; each fix undone one at a time is caught. The
  real model's replies are not run here; the iPhone's chat bar is not built
  here (CI builds it).

## Patch 0207 — the new engine's controls: Loom's notes, people in front, coins, What is

From the second bug hunt (the games' own controls in the new engine).
- Loom: a note played long after the last (2.5 seconds) begins a draft
  again, and a tap on the scene lets the notes go. One stray note no longer
  leaves every later draft a note out until the next place.
- Someone standing in front of a thing or a door: a verb on them is on
  them, not on what is behind. Looking names them; talking (The Dig's tap
  too) walks up beside them, who answer; the rest does nothing. Taps find
  them by a pixel of theirs, not their rectangle (giving too). A walk's tap
  goes where it went before.
- Full Throttle's and the Curse's coins: a press on someone names the coin
  for them. Pushed down to stay on screen, a coin may open with a part under
  the finger: nothing is lit or done until the finger moves.
- The mansion's two garage things (0203), carried into another game, were
  drawn as nothing (their two pictures are the same): drawn whole.
- When a walk ends (a pair done, a door not reached, a walk halted), the
  sentence line shows the verb chosen on the way, as it is still lit, not
  "Walk to".
- What is (the mansion, Zak, Indy 3): names a thing where it is, without
  walking there.
- Tests: test_panel (a thing whose pictures are the same drawn whole), the
  verbs check (a coin let go unmoved, nothing done; a part lit only once
  moved; a draft after a stray note spun; someone in front looked at).

## Patch 0208 — the mansion's engine: playing someone in another world, followers left there, rides

From the second bug hunt (travel in Maniac's own engine, the classic one).
- Someone standing in another game's place (followers brought to Monkey
  Island, say) can be played from the character screen: the place is
  mounted first and gone to as the Worlds menu goes (it did nothing).
- Followers of someone nobody plays any more, left in another game's
  place, go home with them (to the airport, 53) instead of staying there for
  good and keeping a world slot taken.
- No switching while flying the Shuttle Bug (nobody would land it): the
  character screen says "Let's finish this van ride first.", as for the bus.
- "Return to Maniac Mansion" leaves a room whose light was turned off dark
  (it lit it); Zak's places are lit as before.
- The Shuttle Bug launched at Mars no longer takes people aboard the Mars
  tram (its station is the van's landing site).
- Nobody roams, and the tour does not climb, down the pool's ladder while
  the pool is full (the game keeps it untouchable till drained); the tour
  goes to the pit's stop directly then.
- The Dig's tram: the player's followers still on their way to the ledge
  when the doors close ride along, hidden, instead of standing at the far
  station before the car comes.
- Tapping the Mars tram while it runs says where it is going.
- Arrive from a flight takes only those still aboard, not a WiFi friend's
  character or someone who left the cabin.
- Tests: the data suite's roaming, airport, flights, flight join,
  companions, companion presence, seating, Zak cast, portraits, Mars, Dig
  tram, van, appearance, expansion, tram, world visit, tour, lights and
  doors, pool valve (19 of 19), test_startup. No test switches to someone in
  another world yet (that path read and compiled, not run). Not tested on
  an iPhone.

## Patch 0209 — WiFi play: lost links noticed, a taken character refused, places after a load

From the second bug hunt (local WiFi play).
- A quiet link sends a ping every 3 seconds; one silent for 15 seconds is
  gone (the host tells the others; a client says "The host stopped
  answering."). The protocol is 3: devices of the build before and after
  refuse each other with "The host runs a different game version."
  A device that stops for 15 seconds (the ScummVM menu or the app in the
  background) is dropped and must join again.
- A device asking for a character someone else controls is refused and
  closed; the character it had is let go for everyone.
- After a load each friend stands where they really are (put there, not
  walked), not following or riding as the save had them.
- Lines wait their turn (the latest one each, up to 5 seconds) instead of
  being dropped while another shows.
- A broken listener is opened again on the same port, else hosting stops
  with the reason told.
- A join while every place is still held (a leaver removed later in the
  same moment) is refused as full; closing the game always says WiFi play
  is off.
- Tests: test_net (ASan/UBSan, TSan: ping codec, an old protocol refused,
  a taken character refused and closed, a join while full, a broken
  listener reopened, liveness on a moved clock), the WiFi engine probe
  (tools/probes/net.inc: a taken character refused, lines queued, places
  and companions after a load), flights, companions, seating, startup.
  Not run on two devices or an iPhone.

## Patch 0210 — the stage: the person in front, no one on the side bars, a lit saber's crackle

From the second bug hunt (the new engine's stage).
- A tap on people finds the one drawn in front there, in the order they
  are drawn (Scene::actorAt; a prop in front, the van, takes the tap); the
  chat's pick does the same, by a pixel of theirs, not their rectangle.
  0207's pixel test counted only some of the masks that are drawn solid;
  it now counts them all, as drawing does.
- People and props are drawn only within the place: none on the bars
  beside or above a narrower or shorter place (a kid at a left exit was
  drawn half on the bar); taps find them only there too.
- A lit saber standing still crackles (its two lit frames in turn): the
  stage counts as busy while someone is lit, so the screen is drawn again.
- A walk box that is a single point off the picture (Atlantis 75's at
  -1,-1, linked by the game's table) is no box: a tap no longer walks the
  player off the picture's corner.
- Left for later (a fix agent is on it): walks that take a long way round
  or start backwards (the box search ignores distance), and boxes the game
  joins only by its table crossed through what is not floor.
- Tests: test_stage (the front one found under a point, none on the bars
  beside a narrower place, the point box dropped; a lit one busy), the
  moves and talk checks, the full sandbox suite.

## Patch 0211 — Story mode: progress kept when the phone puts the app away

From the second bug hunt (Story mode).
- Put away (the home screen, a call), a story's autosave was only asked
  for: written on the next frame, which never came while the app was
  suspended, so a story stopped by iOS in the background went on from an
  older save. An autosave asked for while the game is held still (no save
  or load pending, no script running, saving allowed) is now written at
  once (ScummEngine::scummverseSaveNow), as the main loop writes one.
- The story's own save runs a v6 game's scripts before and after it, as
  every other save does (Sam & Max keeps its cursor so; the cause of
  0186's "room 92, object 0" error, which 0187 only silenced; that guard
  stays for older saves). The Curse's save gets its own picture and its
  "game loaded" cleared, as its own saves do.
- The game's own menu (F5 in Maniac, Zak, Indy 3 and Loom; F1 or F5 in
  The Curse), where it cannot be saved and where its own Quit is: the story
  is saved quietly as the key opens it, so quitting there goes on from
  there. A menu reached another way is not saved first (nothing is
  overwritten on quitting there).
- Which save a story goes on from (its story save or its autosave): each
  is numbered as it is written (scummverse_story_order0/99 in its target),
  so a load from the game's own menu, or the clock changing, no longer
  makes the older one win; saves from before go by the old rule.
- Left as it is: The Day of the Tentacle's computer still cannot start
  Maniac's own story (doing it safely needs Tentacle's place kept partway
  through its computer script; planned, not done).
- Tests: test_story_engine.py (every game folder: opened, saved, back,
  reopened exactly as saved, quit-saved, the app stopped and gone on; its
  resume run now asks for the autosave with the game held still and fails
  if a frame was needed to write it, the autosave winning by its number),
  test_startup. The save as the game's menu opens is compiled and read, not
  run by a test. Not tested on an iPhone (the suspend itself is iOS's).

## Patch 0212 — the new engine's rides: the van off the doors, everyone seen in the cabin

From the second bug hunt (rides and seats in the new engine).
- The Shuttle Bug parked beside where the player landed could stand over
  a door (at 10 of its 46 sites a door was all but covered: the Ball of
  Twine's museum door, the Carnival's, Puerto Pollo's, Mount Rushmore's...),
  and a tap there walked to the van. It now stands at the nearest spot
  along the place covering the least of any door or ride's boarding place.
- In the plane's cabin the camera was on the one played's seat, and the
  4th and 5th followers sat off screen all flight. It is on everyone
  seated; when they are more than the screen shows, it pans across them,
  there and back in a flight's ten seconds.
- Asked along or told to stay in the chat while riding out of sight (The
  Dig's tram arriving, its doors not yet open), someone stayed hidden at the
  far station; the chat's Follow and Stay now wait until the ride is over,
  as they already did aboard.
  (Where no spot along the place leaves every door's middle clear, as in
  the 320-wide places the van nearly fills, it is drawn smaller, down to
  half.)
- Tests: the rides check (each of 41 van sites installed: no door's or
  boarding place's middle under the van; a flight with five following:
  everyone seated seen whole during it), the full sandbox suite. Not tested
  on an iPhone.

## Patch 0213 — the mansion's engine: the tour's saves, its way back and its end; wanderers out of the flying van

From the second bug hunt (the classic engine's wanderers, tour and camera).
- Wanderers from other games could be shown inside the flying Shuttle Bug
  (the van in flight, 221, where everyone aboard is hidden): it is no place
  of theirs (wanderZakRoom refuses a place that is the cockpit, 81). One
  there from an older save moves on at its next turn.
- No saving during the mansion's tour ("Not during the tour. Stop the tour
  to save."): a save mid-tour kept the room the tour was at and lost where
  it began. ScummVM's autosave tries again later. On the iPhone the
  background autosave is skipped mid-tour too, so an app iOS stops mid-tour
  starts the mansion afresh, as after a force-quit.
- The tour keeps the kid's way back to the mansion (it passed through the
  gate approach, 52, and left that as the way back); it is put back when
  the tour ends.
- At the tour's natural end the guide goes home (where it began, at the
  spot they stood, in another world or Zak's too), and the next tour
  starts at stop 1 (it stayed at the last stop, and "Start at stop N" ended
  at once).
- A selfie aboard the plane leaves those seated in their seats as they
  sit.
- Tests: the data suite's tour (saving refused while touring, the way back
  unchanged after Stop, a tour run to its end home and resuming at stop 1),
  wanderers (221 no place), camera, seating, van, flights, roaming, lights
  and doors, world visit and Story mode probes. The selfie aboard the plane
  is read and compiled, not run by a test. Not tested on an iPhone.

## Patch 0214 — the exporter: what is drawn over things, shared door pictures, containers in every game

From the second bug hunt (the world export). Export version 23: every game
is exported again (markers: maniac-v31; comi, loom, monkey2, atlantis and
zak v24; the rest v23).
- Pictures were taken with what the game draws over a thing still drawn
  (the mansion garage's door slats over the trunk and its tools, the
  shower curtain over the bathroom's things, the wall safe under its
  opened painting): both of a thing's pictures came out alike. While a
  thing's pictures are taken, everything drawn over it is put away a
  moment. Identical pictures under a shown thing: the mansion 12 to 0,
  Loom 57 to 0, Zak 52 to 2, Indy 3 44 to 27, Monkey Island 69 to 49 (those
  left draw nothing of their own: path hotspots).
- The new engine lays things as the games draw them (Scene::layObjects):
  the place without them, then each in its picture now, from the one under
  all up; the oldest games' things whole, the others where they differ.
  The garage: door opened, trunk opened, tools taken, door shut and opened
  again, all drawn right; the drained pool no longer keeps a patch of water;
  Monkey Island 2's people in room 47 are drawn in the right order.
- Version 1 rooms where things share one picture pointer: the one it
  belongs to (whose tiles end just where the next begin) keeps it. The
  mansion's doors 10/454, 12/456, 21/465, 23/459 and 38/460 now open, and
  46 of Zak's (doors and the containers holding things) have pictures.
- Things inside closed containers, in every game: Zak, Monkey Island, Indy
  3, Atlantis, Tentacle and Monkey Island 2 now say what each is inside
  (things files "SVO3" with no effects), so they are hidden and untouched
  while shut.
- Door maps leave out places the export cannot make (Loom 65, Full
  Throttle 13) and doors with nothing to tap (Monkey Island 2's 0x0 ones,
  three of Atlantis', one of Tentacle's, three of Full Throttle's); two
  Monkey Island 2 places get names ("Up the great tree", "Sea map").
- The things pass says so when it fails, and retries without the room's
  entry script in every game: 22 rooms that had none now have things.
- Known limit: in the later games a thing whose colour matched what was
  under it at export can show a few stray pixels of a changed thing under
  it (needs per-picture opacity: a new format).
- Tests: exported again here (all 12 games, the mansion's and Zak's too);
  the full sandbox suite on it (objects with pictures 5860 to 5976; things
  where their games put them 397 in 137 places to 418 in 146; doors 1923 of
  1923 through; 134 arrivals with no way back, 32 from further in; the
  garage's things whose pictures were alike: none now), test_stage (the
  places without their things, laid in order), test_panel (a things file
  with parents and no effects), test_world, the data suite's world visit,
  tour, lights and doors, camera, wanderers, cast, mansion links and locks,
  and world setup. Not tested on an iPhone (it exports on the phone the
  same way, once, at launch).

## Patch 0215 — the new engine's walks: no long way round, not through walls

From the second bug hunt (the stage's walks).
- A walk kept the first chain of boxes with the fewest boxes in the order
  the file lists them, however far it walked: Zak 12's 36-pixel walk took
  129, a 110-pixel walk in The Dig's 4 took 589 round the room's edge,
  some started backwards. Of the fewest-box chains it now takes the one
  walked least (distance to each way in, plus the straight line on), and
  enters each box where the line to the goal crosses it, carrying on from
  where they stand when already inside it.
- Boxes the game joins only by its own table, apart from each other, were
  crossed straight from wherever the walker stood (the mansion's 8: a
  467-pixel diagonal up to 20 pixels off the floor). The walk now goes
  along the floor to the gate first, then across, as ScummVM's own walk
  does.
- Over the 781 places' sample walks: detours 5814 to 1248, walks starting
  backwards 1956 to 175, places with detours 85 to 41, walks straying more
  than 10 pixels off the floor 1324 to 148 (what is left are real gaps the
  games join by script). Every walk still ends where it did.
- Worse: a one-step turn (facing changed for a step and back) shows more
  often, mostly where a walk goes to the gate and then a step across
  (Maniac's 8-pixel gaps, as its own engine walks them).
- Left: The Dig's 4 to 7 still go round where boxes only touch at a corner
  (the box links, not the walk); Full Throttle's 99 unchanged.
- Tests: test_stage (the box listed first not taken over a shorter chain;
  two overlapping boxes not walked back first; no sidestep along a shared
  edge; a table-linked gap not crossed on a slant), the full sandbox suite.

## Patch 0216 — iPhone: game keys after the character screen, buttons off ScummVM's menu, WiFi addresses

From the second bug hunt (the iPhone's menus and screens). The iPhone code
is compiled by CI's iPhone build only; not tested on an iPhone.
- With a hardware keyboard, the game's keys came back only after a pinch
  once the character screen (or the roster) had been up: it took the focus
  from the hidden field that passes keys to the game. It now ends editing
  only on the chat bar and gives the keys back as it closes
  (scummverseGameKeysBack: a keyboard connected, nothing shown over the
  game, no other field typing).
- In portrait, AI, Talk, Worlds and Camera floated over ScummVM's own menu
  and dialogs (a tap there opened the Worlds menu instead): they are hidden
  while it is up, and the touch-mode and menu buttons go back to their own
  corner meanwhile.
- Story mode's list: a game that needs a file says so when tapped (copy it
  into its folder in Documents) and the list stays; no Cancel that only
  brought the list back.
- WiFi play lists the addresses friends can reach: interfaces up and
  running, WiFi first, then a hotspot, no loopback, cellular or VPN, and
  "192.168.1.2" no longer hidden by "192.168.1.20" (Net::reachableAddresses).
- WiFi play says what happened: Join with no address asks again with a
  hint; hosting, joining, players coming and going and a lost host are shown
  a moment on screen and told to VoiceOver.
- VoiceOver can close the camera options (the escape gesture; the panel is
  modal for VoiceOver).
- The hardware keyboard's fn-bar setting is read from a flag the game's
  thread sets, not from the settings file it may be writing.
- Tests: test_net (ASan/UBSan, TSan; the address filter: a phone-like list,
  interfaces down, duplicates; three mutations caught), the WiFi engine
  probe, the Story test (its list), test_startup, the desktop build.

## Patch 0217 — the on-phone model: no crash going to the home screen mid-reply, phones it fits, downloads kept

From the second bug hunt (the on-phone model's own path, which the
scripted tests do not take). The iPhone code and the llama.cpp fix are
compiled by CI's iPhone build only; not tested on an iPhone.
- Going to the home screen (or locking the phone) while the model was
  writing a greeting or a remark on the GPU could stop the app: iOS
  refuses GPU work from the background and llama.cpp aborted on the failed
  copy. Losing the screen now stops any job in flight and waits (at most
  300 ms) until the worker is out of llama.cpp; nothing new starts until
  the app is active again (a cut-off chat reply is written again then; a
  greeting falls back to the game's own line). Going to the background
  waits up to a second before the model is put away. A second llama.cpp
  fix (tools/runtime-patches/0002) makes that failed copy an error, not an
  abort.
- Phones report a little less memory than they are sold with, so "6 GB"
  phones never got the larger model or the GPU, and "3 GB" ones not even
  the small one: memory is rounded up to whole GB first, and a model a phone
  can never run says "Needs a phone with more memory".
- Control Center, a banner or the Photos prompt no longer ends the chat
  (only the keyboard is put away); going to the background still closes it.
- A download put away during its check is installed when it passes (only
  not made current if another was chosen meanwhile); staged files get
  unique names and leftovers are cleared at launch; the storage check comes
  before the current model is turned off; a download may take 6 hours.
- The runtime shuts down before the app or a desktop probe exits (a job in
  flight at exit used freed memory).
- Tests: test_talk_runtime (two new sections: losing the screen stops a
  reply within the bound, nothing starts while held, the reply written
  again, a greeting dropped, a load kept; shutdown prompt and repeatable;
  each part undone caught), test_metal_ownership on the patched llama.cpp,
  the real llama.cpp path on the CPU with small random models under
  ASan/TSan (the wait under 15 ms; exit with a job in flight clean).

## Patch 0218 — iPhone: the AI settings screen steady, settings read off the game's thread, WiFi addresses looked up less

Leftovers from the second bug hunt. The iPhone code is compiled by CI's
iPhone build only; not tested on an iPhone.
- The AI settings screen rebuilt its whole table every second (VoiceOver
  lost its place; a model's row flipped between available and not as free
  memory hovered at its limit). Rows are worked out as the screen appears and
  updated in place only when the status really changes.
- Closing the AI settings screen gives a hardware keyboard's keys back to
  the game, as the character screen does (0216).
- The touch-mode setting (onscreen_control) is read from a flag the game's
  thread sets, not from the settings file, on rotation, suspend and pinch.
- While hosting WiFi play, the device's addresses are looked up as hosting
  starts and then at most every 5 seconds, not on every engine update.
- Tests: test_net (ASan/UBSan, TSan; the address cache: one lookup, none
  for 2.5 seconds, one after 5, again on hosting again; three mutations
  caught), the WiFi engine probe, test_startup, the desktop build.


## Patch 0219 — the mansion's engine without Zak, Zak's twins, the tour taking the controls

Leftovers from the earlier bug hunts (the classic engine).
- Without Zak installed, someone sent "home" from another game's place went
  to San Francisco's airport (53), which exists only with Zak: switching to
  them stopped the engine ("Room 53: data not found"). Home is the airport
  with Zak, else the mansion's front lawn (room 1, where Return to Maniac
  Mansion arrives): roaming, a WiFi friend's character let go, a world
  restored at launch, and the character screen all use it; switching
  mounts Zak's rooms first and, where one cannot be mounted, plays them
  from the front lawn.
- Zak's twins: someone visiting stepped aside only for a look of the same
  name, so the Zaire villager look and the visiting shaman (one costume,
  two names) were both shown, and Zak's own actors without a look (Zak,
  Annie, Melissa, Leslie, the Caponian, the King, the shaman) each stood
  beside a wandering copy of themselves. People are now told apart by the
  costume they wear (Zak's through kZakCastOriginal).
- The mansion's tour takes the controls: while it runs (not paused) the
  player's taps, verbs and keys are ignored (ScummEngine_v2::runInputScript),
  its own controls and the iPhone's menus still work; paused, the player
  has them back. A load ends the tour, and so does switching kids.
- Tested: the full data suite with Maniac's and Zak's data (46 of 46,
  among them the tour, wanderers, worlds, WiFi, camera, Story mode and the
  sandbox suite), test_startup and the desktop build. Not tested on an
  iPhone.

## Patch 0220 — Story mode: Day of the Tentacle's computer opens Maniac Mansion's own story

0211 left this undone. In Story mode, Tentacle's computer now opens
Maniac Mansion's own story (the mansion's data, as Story mode's list
opens it), not a Maniac copy inside Tentacle's folder.
- ScummVM's own way is kept: Tentacle waits in its temporary save (slot
  100) and comes back from it when Maniac's story ends. That same moment
  is also written as Tentacle's story save, so leaving Maniac any other way
  (its Worlds menu: another game, the Story list, Explore mode), or the app
  stopping in it, keeps Tentacle's progress; it goes on from the computer
  next time.
- Maniac's story, opened so, goes on from its own newest story save and
  keeps its place there; Save now works (it was ignored while Tentacle
  waited); its own Quit or ScummVM's menu saves it and goes back to
  Tentacle. Its Worlds menu's ways go where they say, the way back to
  Tentacle dropped (put back if a Go to is refused). If Tentacle's story
  save could not be written, every way out goes back to Tentacle first.
- Without Maniac's own story files, the computer says where they go
  (Documents/maniac on the phone) and Tentacle plays on.
- Explore mode and exports keep ScummVM's original behaviour.
- Not covered: Tentacle's real computer script (the test calls the
  computer's opening where Tentacle can be saved); an autosave asked for in
  the frame between the computer and its temporary save (ScummVM has the
  same window). If the app is stopped inside Maniac's story, the next start
  goes on in Maniac's story (no longer opened by Tentacle); Tentacle's
  Continue resumes at the computer.
- Tests: test_story_engine.py with a new run (Tentacle's computer three
  times: Maniac's story opened, Save now, ScummVM's menu saving it and
  Tentacle back from its temporary save exactly; its Story list going to
  the list and Tentacle from its hand-over save exactly; the app stopped in
  it and started again), test_startup, then the full data suite. Not tested
  on an iPhone.

## Patch 0221 — WiFi play: a paused game stays in; the host's listener kept

From an independent review of 0209.
- A device was dropped once its game loop stood still for 15 seconds (the
  session was polled only from the loop): ScummVM's menu, the pause
  banner, typing a save's name, and on the iPhone Control Center or a call
  banner. A paused host dropped everyone. Now a small thread owned by the
  session (the keeper) polls in the engine's stead once the engine has not
  for 1 second: it answers and sends pings, relays between players, and
  holds what it hears for the engine (each player's last place and last
  line, who left), so a long pause holds little. While the engine polls,
  the keeper only sleeps. If no thread can be made, play goes on as before.
  0209's note above now holds only for the background: once the phone
  suspends the app nothing runs, and a device gone for 15 seconds (killed,
  WiFi off, suspended) is still dropped; a closed connection at once.
- Any error from accepting a new connection closed and reopened the
  host's listener, resetting everyone waiting to join (and ending hosting
  if it could not reopen). Out of descriptors or memory, the host stops
  accepting for a moment; one connection's error skips that connection;
  only a dead listener (or more failures in a row than its backlog) is
  reopened.
- tools/test_talk_provider.cpp waits for the worker's real status instead
  of a 50 ms sleep (it failed now and then under TSan and load).
- Tests: test_net (ASan/UBSan and TSan; new: the engine away for 30 s
  while others walk and talk, every device away at once, leaving and
  joining while away, out of descriptors, a listener shut down, liveness
  on raw silent sockets), the WiFi engine probe (new: the engine paused 18
  s while Zak's player walks on, nobody dropped; the device away 30 s),
  test_talk_runtime, test_startup, the full data suite. Not tested on two
  phones or an iPhone.

## Patch 0222 — the mansion's tour and the menus; a place to go on from

Leftovers from the earlier bug hunts and an independent review (classic engine).
- Somewhere else chosen mid-tour, paused or not (another game's place,
  Return to Maniac Mansion, the mansion's or Zak's places, a teleport pad,
  someone from another game on the character screen, Arrive in the cabin
  mid-flight), ends the tour where it is and goes there. Before, the tour
  pulled the guide back to its own way, and choices from the menus were
  dropped once the tour had changed rooms. The way back to the mansion is
  as the tour began, or the stop the player left from. The mansion's and
  Zak's place lists are offered mid-tour.
- Paused, other games' doors are walked through as tapped (Play forgets a
  tap); a ride boarded while paused (a flight, the van, a tram, the bus)
  ends the tour, and Next or Play then say to finish the ride first.
- The autosave is written as the tour begins and kept while touring
  (autosaves asked for meanwhile, ScummVM's or the phone's as it puts the
  app away, succeed by keeping it), so a phone that stops the app mid-tour
  goes on from where the tour began. Before, it started the mansion afresh.
  Manual saves are still refused mid-tour; play during a paused tour is not
  saved.
- Left as is: the road edges stay off while paused; Story mode and the new
  engine are still refused mid-tour in this engine.
- Tests: the tour probe (new: a place chosen mid-tour, Return to Maniac
  Mansion, the mansion's places, a pad with an old menu token, someone from
  another game, a paused door tap, a flight and the van's flight boarded
  while paused, the tour's autosave kept and loaded), cast and worlds
  probes, the full data suite. Not tested on an iPhone.

## Patch 0223 — visitors in the dark; no greeting for a rider out of sight

From the third bug hunt (wanderers, classic engine).
- A mansion room's own people are drawn grey with black lines with the
  light off, as the original draws them; a visiting character, or someone
  played as another game's character, kept all its colours. They are now
  shaded the same way in the dark (Ted's dress-up too).
- A visitor near Zak's bus stop greeted the empty stop while the player
  rode out of sight; a hidden player is not greeted.
- Tests: test_wander (two schedulers on two threads, ASan/UBSan and TSan),
  the wander probe (new: Guybrush grey in the dark basement and in colour
  with the light back; no greeting during a bus ride), the full data
  suite. The played look and Ted's dress-up in the dark were compiled and
  read, not run. Not tested on an iPhone.

## Patch 0224 — the export's pictures as the scene; the van on the floor (export version 24)

From an independent review of 0214 (new engine and exporter).
- Things hidden inside a shut container (the cabinet in room 3, the coin
  boxes in room 18) left marks where the place was drawn without them: the
  stage now leaves out what the scene file shows hidden when it lays the
  place bare, and a place entered with nothing shown is drawn exactly as
  the game drew it.
- A thing's showing picture differed from the scene in 17 places (laid
  again with nothing changed, 37,075 pixels moved): the exporter takes the
  covers-off picture only where the covers really draw, and the scene
  everywhere else. 20 scene files change (The Dig 49 and 56; Indy3 134,
  136-139, 153, 162, 168, 178; Monkey Island 132; Zak 130, 135, 141, 143,
  145, 160, 184, 192); the garage's sequence is pixel for pixel as 0214.
- The plane's cabin swings by time (600 ticks), not by frames drawn.
- A lit actor standing still is busy only when its next frame is due.
- The van no longer lands with its door off the floor (Atlantis 19: 126
  pixels; Loom 5, Sam & Max 27 and 9): spots on the floor come first.
- Known: Zak 141/143/145's plant shows its first picture as before 0214;
  in some rooms the exporter's own redraw differs from the scene it saves
  (under investigation).
- Tests: a fresh export of all 12 games (version 24), test_stage
  (ASan/UBSan; new: a hidden thing inside a shut container leaves no mark;
  lit frames), the rides self-test (41 of 41 van sites with the door on the
  floor), the full sandbox suite and the full data suite. Not tested on an
  iPhone.

## Patch 0225 — the new engine's character screen; a selfie aboard

From the third bug hunt (new engine).
- Picking whoever is played, in their home place, changed nothing but the
  place was entered again (everyone moved, the chat or a ride dropped):
  now only "You are playing ..." is said.
- Someone else picked in the same place (New kid too): everyone else stays
  where they stood (they were spread to the arrival spots).
- A custom character left in the place and picked again plays from where
  he stood (he took the previous one's spot).
- Someone picked aboard a ride (the plane, the Shuttle Bug): the one left
  stays at the stop it was boarded at (they turned up wherever their
  wanderer record had drifted).
- A selfie in the plane's cabin with the camera panned away (4:3 screens,
  four or five seated) is taken, the camera put on the player first.
- Tests: the cast self-test (four new counts), the camera self-test (also
  at 1920x1440), moves, follow, verbs, talk, tour, rides, walk and back,
  the full sandbox suite and data suite. Not tested on an iPhone or iPad.

## Patch 0226 — the custom characters on a ride out of sight

From the third bug hunt (new engine).
- Crispy 2's pee, or Sith Ewok 3's moves, went on after the bus or a tram
  left with him hidden (the puddle spread at the empty stop and was saved
  full size; a heckle was still said). The ride now ends the move where he
  got on, the puddle as big as it got.
- Sith Ewok 2's L lit the saber unseen in a plane seat (he stepped off
  lit); it does nothing while hidden or seated, as Sith Ewok 3's.
- The moves self-test no longer fails now and then (a show running in the
  Crispy 2 section).
- Tests: the moves self-test (new: out of sight on a ride, 3 of 3, each
  fix mutation-checked), rides, cast, the full sandbox suite and data
  suite. Not tested on an iPhone.

## Patch 0227 — walks: boxes touching only at a corner

From the second bug hunt (new engine's walks).
- Two walk boxes touching only at a corner counted as joined, so walks cut
  round the corner and doubled back (The Dig 4-7: 146 detours each, up to
  257 pixels). Such a corner is now left out where a third box joins both
  along their sides (as the games' own tables and ScummVM do); corners the
  game joins, lines, points and slivers are kept. Which boxes reach which
  is unchanged in all 781 scenes.
- Over all scenes: detours 1248 to 686; walks longer than the game's own
  route 571 to 30; The Dig 4-7 146 to 18 each; Full Throttle 99 83 to 30.
  A few scenes have more small detours (Atlantis 71, COMI 10, FT 43 and
  62), none longer than the game's route.
- Tests: test_stage (ASan/UBSan; new: The Dig 4's layout), 210,400 walks
  with no end point changed, a path fuzzer (200,000 rounds), the full
  sandbox suite and data suite. Not tested on an iPhone.

## Patch 0228 — the custom characters: maps, stains, the saber put away

From the third bug hunt (new engine).
- On a map or floor plan, Crispy 2 no longer pees (it left a stain on the
  map) and Sith Ewok 3 no longer shows off: "Not here."
- At a place's 12 stains, a pee cut short no longer drops the oldest.
- A stain is saved as the pee ends, at the size it reached (it was saved
  full size as it began, so the app stopped mid-pee kept a full one; one
  that ran to its end was not saved).
- Sith Ewok 3's L then a tap: the walk wins over the delayed grab.
- Switching away from a lit Sith Ewok 2 or 3 in the place: he puts the
  saber away beside you.
- The one played is never the heckler of a Sith Ewok 3 show.
- Tests: the moves self-test (new section, each fix mutation-checked),
  test_stage (ASan/UBSan, the 12-mark limit), the full sandbox suite and
  data suite. Not tested on an iPhone.
