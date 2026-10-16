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

## Original Zak reference tooling

- Source-reference native fixture passes with sandbox preference off/on, while
  asserting the original Zak engine remains outside the Maniac sandbox.
- Checks room, walkbox count, actor identity, visibility, position, elevation,
  facing and nonempty rendered bounds. Does not certify seated appearance.
- Requires the verified privately supplied English DOS V1 index; no proprietary
  fixtures are committed. Test-only launcher edits live in temporary archives.
- Source-reference ASan check also passes; normal companion probe and all 11
  standalone startup cases pass after the shared runner change.
- Latest Apple run for 0035: 38724181478, job 116385857974, failed with an empty
  steps list. There is still no compiled iOS artifact for these changes.

## Patch 0036 — six-chair aircraft seating

- Native and AddressSanitizer engine builds pass.
- Portable allocation and source-mask adapter tests pass ASan/UBSan with warnings
  treated as errors: stable reservations, overflow atomicity, invalid/duplicate
  reservation repair, released slots, bounded source-mask reuse.
- Native/ASan seating probe passes: six unique poses, late joining, full-flight
  rejection, NPC waiting, save/load, character switching, getting up and reseating,
  immediate arrival cleanup. Extended ASan probe also checks standing saves, old
  flight migration and seven-rider legacy preservation.
- All 21 available actors render nonempty seated poses; private native previews
  visually reviewed. No proprietary reference images distributed.
- Native joined-flight, companion-presence, flights, full expansion seed 15 and
  eleven startup checks pass. Joined-flight also passes ASan.
- iOS simulator/device testing and true multiplayer remain unverified; no IPA.
- All 36 incremental patch prefixes, idempotence and local-edit preservation pass
  `tools/test_bootstrap.py`.

- Original Zak reference launcher still passes after the cabin mask change.
- Published implementation: fd6082aa130be8a87f390a3e4b007441004e2352.
- Remote native runs 38750078945 / 38750070288 and iOS run 38750070011
  failed before executing steps. iOS job 116473836890 has `steps: []`.
  No remote compilation or artifact acceptance claimed; cause remains unknown.

## Patch 0037 — Mexico chamber setup and source room colors

- Native and ASan engine builds pass.
- `test_chamber.py` passes native/ASan: executes original Zak chamber entries,
  compares all 21 Mexico object states, confirms blocked walkboxes, repairs an
  older raw-state save, returns through the exit, and verifies shared-resource
  isolation. Actor-free Mexico background is byte-identical to the original
  interpreter's PPM fixture. Lighting is explicitly enabled for this visual test.
- `test_temple_reference.py` passes native/ASan: twelve original entry handlers,
  distinct layouts, reachable active doorway graph and exterior/chamber exits.
  Resource 53 MD5 is checked. This is an audit fixture, not a shipped temple fix.
- Native full expansion seed 15, seating regression and eleven startup tests pass.
- All 37 patch prefixes, idempotence and preservation of local/conflicting edits
  pass `test_bootstrap.py`; incremental diff whitespace check clean.
- No iOS simulator/device acceptance or new IPA claimed. Previously observed
  pre-step CI failures remain a separate infrastructure blocker.

## Patch 0038 — Mexico logical temple replacement (2026-10-15)

- Native and ASan engine builds pass. Temple tests pass on both, including an
  actual previous-build save captured before replacing the 0037 ASan build.
- All twelve original entries are executed with reset initial object state.
  Sandbox positions, signed walking anchors, object states, five walkbox flags
  and camera limits match. Leftmost actor-free viewport pixels match for all
  twelve scenes after explicitly updating camera strips and cached object states.
- All 52 original internal doorway destinations, all three exterior entrances,
  distinct variant save/load, offscreen NPC arrival, actor switching and invalid
  destination rejection pass. Save migration preserves two room-88 occupants
  across the 99-to-110 room capacity increase; repeated migration is harmless.
- Corrected chamber fixture passes ASan, including initialized object art,
  restrictions, old-state restoration, return to room 108/logical 166 and isolation
  from the other resource-14 chamber. Previous 0037 direct screenshot fixtures
  lacked state/camera refresh; these corrected comparisons supersede that evidence.
- Native full expansion seed 15 passes: all 54 imported rooms, actual selectable
  walking-hotspot exits, roster, local flights, teleports and bus/save behavior.
  Native seating regression and all eleven startup tests pass.
- All 38 patch prefixes reconstruct; idempotence, local-edit preservation and
  whitespace checks pass. Python test tooling compiles.
- Private evidence: build/temple-{test,asan-test,expansion,bootstrap}.log,
  build/temple-chamber-test.log, build/temple-seating-test.log,
  build/temple-startup-test.log, original/sandbox PPM captures and legacy-temple.s12.
  None of these proprietary fixtures, logs or images are committed.
- No full original torch/darkness/puzzle progression, authoritative multiplayer,
  iPhone/simulator acceptance or new IPA claimed. Apple CI previously failed before
  steps; remote compilation status remains separate from local verification.

## Patch 0039 — Mars logical interiors (2026-10-15)

- Native and AddressSanitizer engine builds pass.
- Mars reference and integration probes pass native/ASan: twenty initialized
  interior scenes match original interpreter pixels at the camera minimum,
  object positions/states/walking anchors, source box flags and camera bounds.
  All sixty interior routes reach their original destinations; distinct scenes
  survive saves. Additional ASan checks verify explicit arrival coordinates and
  restoration of a simulated older machine-room pose on the unused screen half.
- Native full expansion seed 15 passes across all 71 imported rooms, including
  selectable walking-hotspot exits, actor roster and local transport/teleports.
- Mexico regression passes with twelve original pixel comparisons, 52 doorways
  and the actual pre-0038 save fixture. Native seating regression and all eleven
  startup checks pass. Python test tooling compiles.
- All 39 incremental patch prefixes reconstruct. Idempotence, local/conflicting
  edit preservation and incremental whitespace checks pass.
- Private evidence: build/mars-{test,asan-test,expansion,temple-test,seating-test,
  startup-test,bootstrap}.log and source/sandbox PPMs. No source artwork, scripts,
  game data or saves are published.
- This uses an explicit open-door exploration preset, not original puzzle
  progression. Hostel/tram/pyramid branches and complete Mars behavior remain
  open. No iOS compilation, simulator/device acceptance, IPA or real networked
  multiplayer result is implied by these native checks.


## Patch 0040 — conversation reliability (2026-10-16)

- Environment: Linux container, no original game data, no iPhone or simulator,
  Hugging Face blocked (no model weights). Real-model probes were compile-checked
  only, not executed.
- Unit-tested: `tools/test_conversation.cpp` (ASan/UBSan, -Werror): causal order
  with queued sends, backpressure, stale/duplicate completion, departures,
  rotating groups, classic exclusion from model context, bounds, ID monotonicity.
- Runtime-tested: `python3 tools/test_talk_runtime.py` builds pinned llama.cpp
  (CPU) and runs the real iOS dialogue runtime with a scripted provider under
  ASan and TSan: load survival across room change, queued sends, fallback,
  departure, ambient pre-emption, end/off mid-reply. The load-survival case
  fails on the previous logic (verified) and passes with the fix.
- `test_scene_talk.cpp` updated: no-model sends now succeed with classic lines;
  bubble order, sanitization and ASCII conversion of smart quotes/emoji.
- 40 patch prefixes, idempotence, local-edit preservation pass; a fresh
  upstream checkout plus 0001–0040 reproduces the working tree exactly.
  Null build and 11 startup tests pass (talk code is iOS-only).
- NOT verified: UIKit compilation (pending Apple CI), keyboard, layout and
  touch behaviour on a device, model reply quality or latency.

## Patch 0041 — portrait layout v2

- Unit-tested: 500 width/height/keyboard/aspect combinations (ASan/UBSan,
  -Werror): same chat bottom edge, chat never smaller than v1, no reserved
  letterbox band, height-limited and invalid-aspect cases identical to v1;
  exact iPhone 14 / SE figures. Original 49 v1 cases unchanged.
- 41 patch prefixes reconstruct; null build and 11 startup tests pass.
- NOT verified: UIKit/renderer compilation (Apple CI), on-device appearance.

## Apple CI for 0040–0042 (2026-10-16)

- iOS run 38919709518 (0040) and 38920692079 (0040–0042, commit 7f373eb):
  UIKit/renderer compile, arm64 IPA packaged. Artifact 12055045974.
- Native runs 38919709561 and 38920691938: green, including runtime ASan/TSan.
- Compiled is not device-tested: chat, layout and airport labels await iPhone checks.

## Patch 0043 — with original data (2026-10-16)

- Data: user-supplied English DOS V1 Maniac (00.LFL 7f45ddd6...) and Zak
  (00.LFL 7020931d..., all 31 pinned room files match). Not committed.
- `tools/test_all_data.py`: 26 data tests. All pass except the scene audit,
  which fails only on rooms 64/65/97/98 (not in the original; patch 0044).
- Scene audit: 55/71 exact (was 41/71); reference proven deterministic (two
  runs byte-identical). It also caught a regression during development
  (Mexico chamber colors), fixed before commit.
- Pre-existing roaming timeout reproduced on the unmodified 0042 baseline;
  cause was the probe missing the shared prelude (modal desktop dialog).
- Native null build, startup tests and 43 patch prefixes pass.
- NOT verified: iPhone, animation, scrolling frames beyond the camera minimum.

## Patch 0044

- `tools/test_all_data.py`: 26/26 data tests pass (scene audit included: all
  audited rooms exact, retired rooms unreachable). Expansion probe checks every
  pad command lands at its original site, out-of-range commands are ignored,
  retired rooms are refused, and a pre-0044 save made inside a retired room
  (with a second occupant in another) migrates both occupants and the view.
- Perspective and chamber probes updated to non-retired rooms (Seattle chamber
  92 now serves as the shared-resource-14 isolation check).
- 44 patch prefixes, null build and startup pass. iOS panel compile: Apple CI.
- NOT verified: iPhone; ASan run of the data probes for 0043/0044.

## Patch 0045 and sanitizer coverage (2026-10-16)

- 26/26 data tests pass; expansion probe checks The King's name and migration
  of a legacy-named save; dialogue runtime tests pass.
- AddressSanitizer engine build (build/asan, CXXFLAGS -fsanitize=address):
  expansion seed 15, flights, chamber and scene audit pass with 0 ASan errors
  on the 0044 state.
- CI: native and iOS runs 38951831349/38951831639 green for 0043-0044.

## Patch 0046

- 26/26 data tests pass. Expansion probe: carving refuses walkers twice with
  both original lines, feeder traversal lands at (61,51) on the ledge, five-step
  eye/window/valley graph, Peru pad lands in eye chamber 98.
- Scene audit 57/71 exact; 69/97/98 exact against 138/136/137.
- ASan expansion (seed 15) clean. 46 patch prefixes; startup tests pass.

- CI for 0046 (fdd7249): native and iOS run 38955494557 green; IPA artifact 12069933388.

## Patches 0047–0050

- 26/26 data tests pass (`tools/test_all_data.py`), scene audit 64/75 exact
  with no failures; dialogue runtime tests pass; bootstrap reconstructs every
  patch prefix. Expansion probe walks every link (now including logical scenes),
  checks logical-scene save/load and the borrowed resident actor.
- Not device-tested; not multiplayer-tested.

## Patch 0051

- 26/26 data tests pass. Airport probe: 100+ random NPC flights board seated,
  land on their clock and reach every destination; NPC flight never blocks the
  player; player flight never auto-lands. Zak-cast: released guests share one
  NPC flight. Bus probe: an NPC rides the bus alone. Not device-tested.

## Patches 0052–0053

- 27/27 data tests pass (adds test_net_engine). tools/test_net.cpp passes under
  ASan/UBSan and TSan (also in native CI). Talk runtime tests cover chips and
  the nearby composer. Apple CI built the 0052 IPA (UIKit chat compiles).
- Not device-tested; not tested between two devices or two engine processes.

## Patch 0054

- ASan build: expansion, net_engine, airport, worlds, bus, flights, flight_join,
  companions, companion_presence, seating, zak_cast, portraits, walkboxes,
  perspective, chamber, temple, mars and the scene audit run with 0 errors
  (the 0049 overflow was found this way). test_exploration, test_safety,
  test_roaming and test_ai_encounters have no --build option (not ASan-run).
- 27/27 data tests pass on the normal build.
