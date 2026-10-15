# Current development handoff — Purple Meteor

## Scope and baseline

Active milestone: Phase 1; distant scale and matching vertical selection bounds implemented.
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
6. Transport: local manifests, standing plane actors, single active flight; no
   authoritative server. Reproduce reported bus ghosts with visibility/state
   transitions before introducing shared vehicle instances/seats.
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
