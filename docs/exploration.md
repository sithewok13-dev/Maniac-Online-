# Exploration previews: passage locks and capture/death protection

The first preview lets OPEN work without a key or character prerequisite for seven
confirmed passage objects. Original sounds, paired door states, close actions,
walkboxes and room-transition scripts remain in use. The second preview adds the capture/death protection described below. Other
puzzle barriers and successful endings remain; this is not yet full free exploration.

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

## Preview 2: capture/death protection

Enabled by default for the same audited English DOS V1 edition. The independent
`scummverse_exploration_safety=false` configuration setting restores original
behavior after relaunch. **Start a fresh game to test this build.** A save made
mid-capture or mid-death can contain already-frozen actors, disabled controls or
running destructive scripts; this patch does not reconstruct that prior state.

The adapter chooses existing non-hostile branches through scoped variable reads.
It does not rewrite the stored puzzle variables, edit resource files, change actor
movement, or turn off the script scheduler. The scope includes global-script type
as well as script number, because object scripts can have the same numeric IDs.

| Global script | Scoped read | Result |
| --- | --- | --- |
| 36 | 73 → no target (255) | Edna's monitor loops without stopping patrols or capturing. |
| 91 | 113 → no target (255) | Ed's monitor loops without starting the chase. Monitor greetings are also skipped. |
| 48 | 200 → no target (255) | Purple Tentacle performs the empty-room search and returns without switching the active kid. |
| 116 | 106 → permitted (1) | Ed's normal pickup branch runs before any capture/control changes. |
| 107 | 157: lethal tape (25) → ordinary negative review (0) | Original dialogue and control/camera restoration finish without leaving the room for death. |
| 110 | 101: hostile contracts (1/2) → neutral (0) | Avoids disabling input before the death call. Other contract paths are unchanged. |

The script-start guard suppresses reactor countdowns 7/12, Edna imprisonment 37,
Purple Tentacle chase/imprisonment 49, death 61, game over 62, Ed chase/imprisonment
88/89, lab capture trigger 117, self-destruct countdown 123, and meteor projectile
128. Some surrounding story dialogue can still mention danger. Successful endings
and other puzzle conditions are not disabled.

## Protection verification

Run `python3 tools/test_safety.py /path/to/maniac` after the null-backend build.
The isolated probe compiles a temporary engine translation unit and executes the
original DOS resource scripts. No probe code is part of the shipped IPA.

- Edna and Ed monitors: hostile target decisions differ with protection on/off;
  protected monitors remain running while the player keeps their room and controls.
- Ed's guarded pickup: original object 34 invokes script 116; protected pickup
  succeeds without persisting the permission override or locking the controls.
- Both hostile contracts: original behavior disables input; protected behavior
  leaves it available and preserves the contract variable.
- Purple Tentacle: original search captures the kid when disabled; protected
  search finishes with the kid in the same room and Tentacle back in room 31.
- Bad tape: original behavior removes the kid's costume on death; protected
  dialogue finishes with costume, room and input intact, without changing the tape.
- Edna's hallway-to-bedroom patrol completes with protection enabled.
- All suppressed destructive entries leave player room, costume and controls
  intact; the checks include all six death-reason values.
- Original radioactive microwave, pool-refill and reactor-button handlers complete
  without killing the player or entering game over.
- Existing seven-door scripts, front-door round trip, and 11 startup checks pass.

The probe accelerates script delays and clears dialogue waits; its evidence covers
VM state and original-script completion, not real-time pacing or audiovisual
behavior. The owner already confirmed preview 1 on iPhone; preview 2 needs its
own physical-device check.

## iPhone protection check

Sideload the new IPA and start a fresh game with the same lowercase `maniac` data
folder. Enter Edna's kitchen area, approach Weird Ed, and try taking an item in
his room. Confirm that no kid is imprisoned and that walking, changing kids and
leaving the room still work. Recheck a door transition and normal sound/animation.
Where accessible, test the pool/refill and microwave hazards. Original puzzle
barriers still apply; protection does not provide a teleport or solve every puzzle.

## Kitchen and hallway correction — 2026-10-11

The owner reported that Edna disappeared immediately in the kitchen and Green
Tentacle prevented reaching Weird Ed. Edna's kitchen script 153 waits on chase
flag 126; with capture disabled that flag stays clear, so the script immediately
starts her departure through script 38. The fourth patch makes only that scoped
read report "still waiting" while the current room is the kitchen (7). It leaves
the stored flag clear. Once the player leaves, the original departure resumes.
Edna's normal timed departure before the encounter is not removed.

Green Tentacle's gate script 51 launches pushback script 161, requires food/drink,
and contains Bernard's forced retreat. Both starts are suppressed under the same
edition-gated exploration-safety setting. The original room-entry script still
places Green Tentacle at his resting position, and his food/drink state is not
falsified. He remains visible; normal walkboxes and exit scripts handle passage.

The real-script probe first reproduced the Edna regression before the fix. It now
checks that she stays through the kitchen greeting, keeps controls available and
resumes her normal departure after the player leaves. For both Dave and Bernard,
it runs the original hallway entry, walks to the stairs with no food/drink, checks
Green Tentacle remains present, then executes the original transitions through
room 38 into Weird Ed's room (26). With protection off, the original gate remains.
The earlier capture/death, patrol, door and startup tests still pass. These are
headless VM checks; the corrected IPA needs confirmation on iPhone.

Start a fresh game with the corrected IPA. Check Edna's kitchen greeting, then
walk past Green Tentacle and up to Weird Ed. Old saves may retain already-running
blocking scripts or an Edna departure that began in the previous build.
