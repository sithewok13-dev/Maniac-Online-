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
