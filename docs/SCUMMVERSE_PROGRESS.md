# Current development handoff — Purple Meteor

## Scope and baseline

Active milestone: Phase 1; latest patch 0072 (Sharptooth, Red Skull and a floating Murray).
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

