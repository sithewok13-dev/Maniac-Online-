# Original-scene audit: English Zak DOS V1

Source index full MD5: 7020931d5a2be0a49d68e7a1882363e4. Original data,
decompiled scripts and comparison images remain private under ignored directories.
This is an evidence ledger, not a claim of full game compatibility.

| Scene | Source evidence | Implementation / remaining work |
| --- | --- | --- |
| Seattle forest / cave | 12.LFL local object 5, original ID 267 is loose dirt; state bit 8 displays the opening. Its Walk handler enters resource 13 through original cave exit 272. Local object 6 / ID 271 is Mt. Rainier scenery. | Patch 0025 routes sandbox 58/object 737 to 59, not scenery 738. Original open artwork enabled by source-ID scene-state metadata. Cave exit returns to forest. Sandbox deliberately bypasses digging puzzle. |
| Seattle tree access | Forest entry sets box 4 flag 64 while original branch object 52 is not in state 8. | Not repaired. Global imported-box unlock remains; audit walking and bird/tree interaction before changing. |
| Temple exterior | 39.LFL entry changes the first two protagonists to costume variants via original variables indexed from 171 plus actor ID plus 8. | Confirms missing original costume selection, not generic later-engine scale metadata. Mexico/Zaire/Peru still require per-logical-room verification. |
| Peru carving | 42.LFL entry initializes bird actor 6 and several state-dependent environmental animations. | Traversal capability and bird control not implemented. Do not treat missing source setup as permission for unrestricted walking. |

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
