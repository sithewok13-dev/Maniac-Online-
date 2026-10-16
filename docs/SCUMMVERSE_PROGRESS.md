# Current development handoff — Purple Meteor

## Scope and baseline

Active milestone: Phase 1; patch 0040 makes scene chat reliable through a portable conversation core.
Working branch: claude/scummverse-dev (from codex/scummverse-c64-baseline fde0674).
Apple CI works since the repository became public: iOS run 38789360948 built the
0039 IPA. Earlier "blocked before steps" notes below are historical.
Next: user-reported device defects (screenshots pending), portrait layout v2,
then Mars hostel/airlock, tram and pyramid. iPhone acceptance remains open.
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
8. Missing NPCs: verify Elvis-related content, Guru levitation and Nepal guards
   using supplied resources; do not invent identity or animation mappings.

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
