# Current development handoff — Purple Meteor

## Scope and baseline

Active milestone: Phase 1; source-derived distant scale added for pyramid/temple exteriors.
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

## Continuation

Read AGENTS.md and SCUMMVERSE_ARCHITECTURE.md. Patch 0024 resolves the renderer
strip assertion; full expansion tests now pass in null and ASan. The next
substantive content slice is a logical
Zak scene identity/setup audit with private reference comparisons and one faithful
scene proving geometry, scale and transitions. Existing private descumm output
under build/zak-analysis can inform analysis; never publish those scripts/assets.
Record verification evidence in SCUMMVERSE_TEST_STATUS.md. No automatic claim of
complete Mars, multiplayer support, device acceptance or future background work.
