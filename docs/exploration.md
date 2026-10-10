# Exploration preview 1: passage locks

This preview lets OPEN work without a key or character prerequisite for seven
confirmed passage objects. Original sounds, paired door states, close actions,
walkboxes and room-transition scripts remain in use. It does not yet provide full
free exploration: NPC capture, death, other puzzle barriers and endings still run.

The adapter is enabled by default only for the full English DOS V1 edition whose
`00.LFL` MD5 is `7f45ddd6dbfbf8f80c0c0efea4c295bc`. Other accepted DOS V1 revisions
keep their original behavior. The index identifies the revision; it is not an
integrity check of every supplied resource file.

| Room | Object | Passage | Paired object |
| --- | --- | --- | --- |
| 1 | 61 | Front door | 67 |
| 1 | 53 | Rusted grating | 234 |
| 6 | 137 | Pool / garage door | 125 |
| 36 | 125 | Reverse side of that door | 137 |
| 16 | 143 | Gate | 138 |
| 30 | 255 | Outer laboratory door | 267 |
| 52 | 108 | Gate in alternate room | 138 |

The hook in `ScummEngine::runObjectScript` checks the room, object and verb before
clearing only `kObjectStateLocked`. OPEN is verb 1; PULL (10) is also supported
for the two gate objects whose original verb tables share the OPEN handler.
State 04 means different things on other objects, so there is no global unlock.
The constructor caches the edition/configuration guard. No new save format,
networking or game-resource modifications are introduced.

To compare with original behavior, set `scummverse_exploration_doors=false` in
the `[scummvm]` section of the configuration and relaunch. An object already
unlocked in a saved game stays unlocked; use a fresh game for comparisons.

## Verification

- Patched null-backend engine compiles; all 11 existing startup tests pass.
- `python3 tools/test_exploration.py /path/to/maniac` compiles a temporary probe
  from the actual engine and uses the privately supplied original resources.
  It does not edit engine source, the normal binary, game data or existing saves.
- With the override disabled, all seven original OPEN handlers keep their locks.
- With it enabled, all seven original OPEN/CLOSE handlers update both sides.
- Original front-door `loadRoomWithEgo` scripts move the active actor from room 1
  to room 10 and back. No replacement transition implementation is used.
- These are headless VM tests, not a visual or physical-iPhone acceptance test.
  Proprietary resources and disassembled scripts are kept out of the repository.

## iPhone check

Install the new IPA through the same sideloader. Keep the existing lowercase
`Documents/maniac` data directory. Start a fresh game, choose the characters,
then OPEN the front door without picking up the key. Walk inside, close/reopen
the door, and return outside. Check the original animation, sound and touch input.
The grate should also open without a strong character or the rust remover.

## Remaining exploration work

Local script inspection confirmed Edna's capture monitor (36) and transfer (37),
Weird Ed's monitor (91), chase (88) and transfer (89), and Purple Tentacle's
chase/transfer (49). Some callers stop patrol scripts, change input state, or
freeze characters before the transfer. Suppressing only the transfer is unsafe.
The death routine (61) and game-over sequence (62) also have callers that change
rooms or controls first. None of these routines is suppressed in this preview.

Next work needs caller-aware capture/death handling, remaining puzzle passages,
and room-by-room verification before describing the mode as free exploration.
