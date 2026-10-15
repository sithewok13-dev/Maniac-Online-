# Verification status — 2026-10-12

- Baseline: 11 startup tests passed; engine diff whitespace check clean.
- New portable portrait contract: 144 dimension/target combinations, invalid
  inputs, centering, padding and aspect bounds pass ASan/UBSan, C++11 with warnings
  treated as errors. No proprietary fixtures or platform dependencies.
- Native null and AddressSanitizer engine builds passed.
- Original-costume roster probe passed with override disabled/enabled: all 21
  characters produce nonempty portraits with at least two pixels of frame padding.
- All 23 patch prefixes, idempotence and preservation of local edits passed.
- Patch 0024 resolves the expansion assertion: the test clicked x=-8 for actor
  8 at x=2; the chat picking hook indexed graphics strips without validating
  scene coordinates. Scene input now rejects points outside the room before
  any actor/object lookup or script execution. Valid near-edge walking is tested
  separately from rejection of five invalid boundary points for every character.
- Full expansion probe now passes in null and AddressSanitizer builds, override
  disabled/enabled: 43 imported rooms, 21 actors, local flights, links, teleports,
  bus travel and save/load. This tests sandbox behavior, not canonical accuracy
  or network multiplayer. Logs: build/input-bounds-expansion.log and
  build/input-bounds-asan.log.
- All 24 patch prefixes and 11 startup tests pass; whitespace checks pass.
- iOS simulator and physical iPhone verification: not performed this milestone.
- Multiplayer, new-game adapter acceptance, persistent AI memory, creators,
  Curator and testnet ownership: not implemented or demonstrated.

## Patch 0025 — Seattle cave

- Null and ASan engine builds pass; flight probes pass disabled/enabled on both.
- Native cave-opening clicks and round trip pass; mountain scenery and walking
  to the forest edge do not enter the cave. Original opening state is asserted.
- Full expansion probe passes on null; all 25 patch prefixes reconstruct cleanly.
- No iOS or visual-reference acceptance claimed. Scene audit records unresolved
  walkbox restrictions, perspective, source puzzle differences and arrival placement.

## Patch 0026 — audited walkboxes and save recovery (2026-10-13)

- Null and ASan builds pass. New walkbox probe passes disabled/enabled on both:
  ground preserved, all 21 walking actors excluded from three Peru aerial regions,
  actual player walking constrained, jungle exit retained, Seattle restriction
  and cave round trip retained, simulated legacy aerial save repaired on load.
- Full expansion probe passes on null. Flight probe passes on ASan.
- 11 startup tests, 26 patch-prefix reconstruction and whitespace checks pass.
- Original bird-control traversal, other scenes' navigation and perspective scale
  are still pending. No simulator or device acceptance claimed.

## Patch 0027 — distant exterior scale (2026-10-14)

- Source reference test confirms standing costume spans of 46px and 10px from
  supplied DOS V1 resources. This validates the 5:23 scale reference.
- Null and ASan builds and perspective probes pass: 21 characters, four facings,
  nonempty reduced sprites, feet anchoring, four intended exterior policies,
  unrelated-room exclusions and portrait exclusion. No source assets distributed.
- Null full expansion and portrait probes pass; 27 patch prefixes reconstruct
  cleanly; engine whitespace check passes.
- This is uniform scene scale using each character's art, not the original
  generic distant costume or depth interpolation. Physical iPhone appearance,
  on-device hit testing and simulator testing remain unverified.

## Patch 0028 — distant actor selection

- Native and ASan perspective probes pass, including rendered-bound selection
  and rejection just above/below the sprite bounds for all selectable cast members
  in four facings. Current player remains excluded by design.
- 28 patch prefixes and 11 startup tests pass; builds and whitespace checks pass.
- Full expansion regression is INTERMITTENT: build/hitbox-expansion.log failed
  with `box 4 is out of bounds (0,2)`; diagnostic rerun in build/hitbox-diag.log
  passed. Do not characterize overall travel as consistently green. Root cause
  remains unresolved; investigate seeded roaming and cross-room actor walkbox state.
- Native device touch interaction remains unverified. Horizontal selection still
  uses original graphics strips; this fix corrects vertical extent only.

## Patch 0029 — portrait/room isolation

- Deterministic pre-fix failures: offscreen cave actor box 7 with jungle's three
  boxes; full expansion seed 15 (London gallery, box 5). Stack identifies
  getMaskFromBox → prepareDrawActorCostume → scummverseRosterOffer.
- Portrait preparation now uses no room mask, preventing cross-room walkbox reads.
  Temporary Linux backtrace instrumentation was removed; no platform dependency
  was added to shipped code.
- Targeted reproduction and expansion seeds 15 and 4 pass on null. Seed 4's
  already-boarded NPC test now finishes its bus ride before testing airport travel.
- Native and ASan builds pass. Targeted portraits and seed 15 expansion pass
  on ASan; 29 patch prefixes, all 11 startup tests and whitespace checks pass.
- This closes the reproduced intermittent gallery crash. Device verification
  and broader original-scene authenticity work remain pending.

## Patch 0030 — coordinated mobile layout

- ASan/UBSan portable layout contract: 49 screen/keyboard combinations, 1x/2x/3x
  point-to-pixel alignment, keyboard dismissal and invalid dimensions pass.
- Patch-prefix/idempotence/local-edit preservation tests pass through 0030.
- Native build is current; native compilation does not compile UIKit sources.
- Apple arm64 CI build pending; physical portrait/landscape, keyboard animation,
  safe-area and touch acceptance are not yet verified.

## Patch 0031 — bus actor visibility

- Reproduced before fix: expansion seed 15 failed with "Bus rider visible
  immediately after takeover" (build/bus-visibility-repro.log).
- Fixed native takeover/save/load test passes. Expanded two-passenger test passes
  ASan with seed 15, sandbox override disabled/enabled. It checks immediate
  visibility, saved phase/manifest, and visible airport arrival for both actors.
- Native and ASan engine builds pass. Full patch-prefix and startup checks run
  for this patch; see build/bus-visibility-bootstrap.log and startup.log.
- Apple CI run 38651455882 for patch 0030 failed before executing build steps;
  no job logs are available. This is a build-execution blocker, not evidence of
  a compiler failure. UIKit compilation and device validation remain outstanding.

## Patch 0032 — independent character travel records

- Before fix, flight probe failed: Annie's Miami selection overwrote Zak's Seattle
  booking. Return-trip probe separately exposed scene-switch contamination.
- Native and ASan builds and flight probes pass with override disabled/enabled:
  independent bookings through save/load, independent mansion return rooms,
  migration from the legacy shared slot, idempotence, preservation of original
  kid fields, and nonoverlapping record keys for all 24 actor IDs.
- All 32 patch prefixes, idempotence and local-edit preservation pass.
- Startup: 11 checks pass. Logs: build/travel-records-{fixed,asan,bootstrap,startup}.log.
- Seating source audit is research only; group seating is not implemented.
- Apple CI still fails before job steps (latest checked run 38651860666);
  no new Apple build or device acceptance is claimed.
- Full expansion probe seed 15 passes after switching the test from direct legacy
  slot writes to real airport-computer commands. Covers all 21 selectable actors,
  imported rooms, flights, bus takeover/save/load, links and teleports. This is
  local sandbox testing, not network multiplayer or full source-game authenticity.

## Patch 0033 — matching-flight join

- Reproduced rejection of a matching late passenger before the fix.
- Native and ASan join probes pass: wrong destination/origin rejection isolation,
  original-owner/route preservation, companion joining, repeated boarding,
  save/load, and united arrival without moving the rejected passenger.
- Existing native flight regression passes (including independent bookings,
  migration, separate return points and bus timing).
- All 33 patch prefixes/idempotence/local-edit-preservation checks pass.
- Logs: build/flight-join-{repro,fixed,asan,flights,bootstrap}.log.
- This is not real multiplayer validation. Seating and physical-device acceptance
  remain outstanding; Apple CI execution remains an external blocker.

## Patch 0034 — NPC bookings and shared flight

- Native and ASan focused tests pass: a saved booking supersedes a stale NPC
  destination, an NPC outside the gate is not boarded with the initial party,
  the NPC later joins the matching active flight, its booking is consumed, and
  it arrives with that flight. Existing rejection/save-load join cases also pass.
- Full expansion seed 15 passes with sandbox override disabled/enabled.
- All 34 patch prefixes/idempotence/local-edit checks pass; engine whitespace
  checks pass. Logs: build/npc-booking-{repro,fixed,asan,expansion,bootstrap}.log.
- Private original-seat preview is not a shipped feature or acceptance result.
- Final startup run for 0034: all 11 tests pass (build/npc-booking-startup.log).
- Latest Apple run 38664283970 fails before job steps, with no logs; no device IPA
  validation is claimed for this commit.

## Companion presence (0035)

- Reproduced remote/bus companion recall before the fix.
- Native and AddressSanitizer focused checks pass, including save/load and bus/plane
  boarding. Present companions continue following ordinary transitions.
- Existing companion and shared-flight probes pass. Updated the companion probe's
  retired airport-selection command to the current protocol.
- Startup: 11 cases pass. Patch preparation through 0035 passes, including prefixes,
  idempotence and preservation of local edits.
- These are local actors; no network multiplayer or iOS device acceptance claimed.
