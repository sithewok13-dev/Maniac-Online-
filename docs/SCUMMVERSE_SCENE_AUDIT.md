# Original-scene audit: English Zak DOS V1

Source index full MD5: 7020931d5a2be0a49d68e7a1882363e4. Original data,
decompiled scripts and comparison images remain private under ignored directories.
This is an evidence ledger, not a claim of full game compatibility.

| Scene | Source evidence | Implementation / remaining work |
| --- | --- | --- |
| Seattle forest / cave | 12.LFL local object 5, original ID 267 is loose dirt; state bit 8 displays the opening. Its Walk handler enters resource 13 through original cave exit 272. Local object 6 / ID 271 is Mt. Rainier scenery. | Patch 0025 routes sandbox 58/object 737 to 59, not scenery 738. Original open artwork enabled by source-ID scene-state metadata. Cave exit returns to forest. Sandbox deliberately bypasses digging puzzle. |
| Seattle tree access | Forest entry sets box 4 flag 64 while original branch object 52 is not in state 8. | Patch 0026 preserves original forest flags, including locked box 4. Cave entry/return remains tested. Branch puzzle interaction is not implemented. |
| Temple exterior | 39.LFL entry changes the first two protagonists to costume variants via original variables indexed from 171 plus actor ID plus 8. | Confirms missing original costume selection, not generic later-engine scale metadata. Mexico/Zaire/Peru still require per-logical-room verification. |
| Peru carving | 42.LFL entry initializes bird actor 6 and several state-dependent environmental animations. | Patch 0026 preserves ground flags and blocks aerial boxes 6–8 for all walking actors. Source flags 0xA0 exempted original NPCs; sandbox uses 0x80 because its cast is walk-only. Bird control remains unimplemented. |

## Scene-state boundary (small initial extraction)

`ZakSceneObjectState` lives beside the Zak adapter catalog, keyed by source file
and original object ID. Resource import applies declarative set/clear state masks
before remapping to scratch object IDs. The engine does not interpret foreign
scripts or embed the Seattle object ID in general rendering/navigation code.
Only Seattle's uncovered opening is currently represented. This is not yet the
versioned game-pack contract: shared resources require logical scene identity,
not just file identity, before adding variant-specific rules for other locations.

## Acceptance and next evidence

Seattle automated checks exercise native hotspot clicks, explicit scenery rejection,
edge non-transition, return path and state restoration on entry. Existing flight
and expansion checks continue to cover local NPC travel. Original puzzle progression,
precise doorway arrival placement, authentic forest walkbox restrictions and physical
phone interaction remain separate work. Scaling and Mars/Mexico audits remain open.

## Audited navigation policy and saves

Only rooms 58 (Seattle forest) and 96 (Peru carving) currently use restored
source walkbox flags. The remaining imported rooms retain legacy behavior pending
individual audits. Overrides are data beside the Zak catalog; the engine applies
them before computing exit points and actor spawn positions. Source box geometry
and adjacency remain unchanged.

Loading saves reapplies audited flags from the verified room resource and projects
present walking actors to valid boxes, stopping stale walks. A test writes a
legacy-shaped save with unlocked Peru air boxes and a player at (65,10), then
loads it and checks restored restrictions and ground placement. This is a simulated
legacy state, not a historical on-device save fixture. Scene rendering must run
before the test saves, as required by the engine's thumbnail/screen state.

## Distant exterior scale (patch 0027)

Original room resource 20 explicitly chooses costume 9 for the two original
protagonists. Resource 39 chooses it indirectly through variables initialized by
script 108: indices 180/181 both contain 9. The decoded standing frame 6 spans
46 vertical pixels for normal Zak costume 1 and 10 for costume 9. The reference
measurement is reproducible with tools/test_perspective_reference.py and private
DOS V1 data. No extracted artwork or scripts are distributed.

Sandbox rooms 64, 72, 87 and 97 now use a 5:23 uniform reduction around actor feet.
This preserves each visiting character's own costume and palette instead of
replacing everyone with the original generic distant silhouette. Imported Zak
normalization (6:5) is bypassed in these scenes. Larger species retain relative
size differences. This is an adaptation based on original scene scale, not an
exact reproduction of the original distant sprite, nor depth interpolation.

The policy is catalog data queried by the renderer. It does not mutate saved
costumes, actor positions, walkboxes, room connections, or inventory. Portraits
explicitly ignore the policy. Other rooms retain their previous rendering.

## Distant actor selection (patch 0028)

Original V1 selection substitutes a fixed 40*V12_Y_MULTIPLIER vertical span,
ignoring renderer bounds. In the audited distant scenes it now uses actual
half-open draw bounds. This avoids picking a small character by clicking far
above its head. It preserves current-player exclusion and upstream horizontal
strip-based selection. It does not change touch-to-room coordinate conversion.

## Plane cabin seating

Source room 11 / sandbox 56 has six matching chair positions. The source player
uses actor position (63,52), elevation -4, facing right, behind the foreground
chair mask. Only that chair has the usable source mask; simply placing additional
actors at other chairs leaves standing legs visible. Patch 0036 reuses the mask
map references at matching chairs through an edition-specific adapter. It changes
no source image data and does not use foreign scripts. Imported visitors sit at
original 1:1 size; normal scene normalization remains 6:5. Native Maniac chair
anchors are aligned by one two-pixel cell. Private previews cover all 21 costumes.
The original-interpreter fixture remains a reference, not proof of full puzzle
or source-game support. Nonhuman passengers retain their original silhouettes.

## Logical temple audit and Mexico chamber repair — patch 0037

Verified the original initialization mapper and entry handlers. Mexico's temple
corridors are logical rooms 156–167 backed by **53.LFL**, not 36.LFL. Resource 36
backs logical rooms 196–205 in the Mars maze. Current sandbox room 88 still uses
36.LFL incorrectly; replacing it requires stable IDs for twelve distinct scenes,
scene-specific object placement, camera limits, links and save migration. Do not
silently collapse these into one mutable room shared by unrelated actors.

`tools/test_temple_reference.py` executes all twelve original entry handlers in
an isolated original-Zak engine. It records private layout/state/box/transition
snapshots and verifies the active doorway graph is reachable from 156, including
exits to exterior 39 and crystal chamber 130. This is one controlled initial-state
fixture with lighting enabled for inspection, not full original puzzle progression.
Source PseudoRoom mappings and door handlers were cross-checked against the runtime.
No extracted scripts or source assets are distributed.

Sandbox 89 is original logical chamber 130, resource 14. Patch 0037 adds
room-specific object state rules, keeps boxes 12/13 blocked, and repairs this
immutable imported scene's setup when loading older saves. Other resource-14
chambers keep their prior setup; their own variant audits remain open.

Pixel comparison also exposed a shared color-table mismatch: Maniac's DOS V1
mapping maps source color 15 to dark gray while Zak maps it to light gray. Imported
backgrounds and objects now use the existing Zak table from ScummVM, separately
from actor colors. No palette or source art is copied into project fixtures.
The fixed Mexico chamber's actor-free background exactly matches the original
interpreter fixture. This does not validate every imported room's scene setup.


## Mexico temple replacement — patch 0038

The preceding 0037 corridor limitation is resolved for the exploration adapter.
Sandbox 88 = logical 156; sandbox 99–109 = logical 157–167, all using resource 53.
Catalog metadata records initialized scene facts, not copied scripts or artwork.
Camera maxima are 800, 448 or 184 pixels for the three corridor sizes. Source
box restrictions remain intact. Each room owns its persisted identity independently.

Source exterior objects 594/596/597 enter logical 156/157/158 at object 745.
All 52 active internal doorways use the original destination room and arrival
object. Logical 166 leads to crystal chamber 130, which returns to 166. Offscreen
NPC arrivals use the same variant anchors; they do not spawn in a generic corner.

Reference captures now refresh camera strips and cached object states before the
actor-free drawing pass. Earlier 0037 direct captures omitted these steps, so its
pixel-equality result alone was insufficient evidence for initialized object art.
The corrected fixtures and state/anchor comparisons are the acceptance evidence.
The test resets initial object states between original scene entries to avoid
cross-room contamination. Background comparisons cover the leftmost viewport;
full walking-hotspot regression covers all registered exits across scrolling rooms.
Original darkness, torch interactions and puzzle progression remain outside scope.


## Mars interior reconstruction — patch 0039

Original logical identities are not interchangeable physical resources:

| Original logical scene | Sandbox | Source resource |
| --- | --- | --- |
| Three massive doors (32) | 82 | 32 |
| Great Chamber (182) | 83 | 33 |
| Machine platform (194) | 93 | 35, right viewport |
| Antechambers (189–191) | 110–112 | 33, right viewport |
| Projection room (195) | 113 | 35, left viewport |
| Maze passages (196–205) | 114–123 | 36 |
| Yellow crystal / rock chambers (192–193) | 124–125 | 14 |
| Burial chamber (34) | 126 | 34 |

Original entry execution supplies each layout, object state, walkbox restriction,
camera bound and palette. The exploration reference opens massive doors and rock
tunnels using original object state bits; it sets original machine defaults and
illuminates the scene. This is not a claim that the source puzzles are implemented.
Sixty interior transitions are checked against original door handlers and the maze
entry scripts' transition pairs. Exterior object 444 leads to Great Chamber 182;
that chamber leads to the three-door corridor, not directly to a generic maze.

All twenty initial actor-free viewports are compared byte-for-byte with original
interpreter captures. This verifies initialized artwork at the camera minimum,
not every animation, puzzle state or scrolling frame. Scene metadata contains no
copied proprietary scripts or artwork. Native walking-hotspot tests additionally
exercise the registered exits. Hostel rooms 180/181, exterior/tram 184/185 and the
pyramid branch remain separate pending repairs; existing shortcuts there must not
be treated as canonical geography.


## Scene authenticity audit and original airports — patch 0043 (2026-10-16)

`tools/test_scene_authenticity.py` renders every imported sandbox room and the
candidate original logical scenes (through Zak's own entry handlers, with a
fixed random seed) and compares the actor-free viewport at the camera minimum
pixel for pixel, plus camera bounds. Candidates come from the original pseudo-
room table, read from the supplied data at run time (49.LFL `0xCC` records).
Captures and reports stay in ignored build/scene-audit.

Source evidence (private descumm of the user's English DOS V1 files):
- Tickets 659-667 (script 58 names, script 120 targets): London 141, Mexico City
  142, Miami 143, Seattle 144, San Francisco 145 use big-airport resource 8;
  Cairo 146, Kinshasa 147, Katmandu 148, Lima 149 use regional resource 9.
- Airport exits: London -> Stonehenge 133, Mexico City -> jungle 168, Seattle ->
  forest 12, Cairo -> Sphinx 20, Katmandu -> street 17, Kinshasa -> jungle 170
  (then village 150 after five scenes), Lima -> jungle 175 (then carving 42).
  Miami has no exit ("closed for repairs").
- Jungle resource 37 backs logical 168-175, a random maze; colors depend on
  region (Zaire 9/7, Peru 9/3, elsewhere 9/13).
- Crystal map (room 29, objects 480-486, script 60) teleports only to Seattle
  129, Mexico 130, Nepal 137, Egypt 25 and Mars 193. No Zaire/Peru chamber.
- Resource 39 (temple exterior) has no pseudo-rooms: it is Mexico's only.
- Split scenes: village 150/151, hostel 180/181, Stonehenge 133/134.

Results: before 41/71 rooms exact; after 55/71. Audited rooms all match:
airports (now original resource and logical setup, incl. SEA-TAC/MIA signs),
jungles 170/168/175, Seattle chamber 129, village 150, hostel 180, Stonehenge
133, cabin colors/camera, shuttle colors, and Mexico chamber colors. Explained
differences: Seattle forest (cave opening shown dug, by design) and machine
room defaults (covered by the Mars reference test).
Open (64/65/97/98 retired in patch 0044): sandbox "Cairo"
(71) is a pyramid-interior passage that matches no original scene; "Mars
pyramid" (84) shows the left half of resource 15 (original 188 uses the right
half); village 151, hostel 181 and Stonehenge 134 are not yet imported.
