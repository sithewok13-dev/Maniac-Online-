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
