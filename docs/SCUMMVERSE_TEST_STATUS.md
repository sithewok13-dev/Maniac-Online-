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
