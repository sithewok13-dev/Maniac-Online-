# Expanded Zak world and character gallery

This round keeps the original English DOS V1 data supplied by the player. No game
art or model weights are bundled. It expands the sandbox, not the original Zak
puzzle campaign. Kathmandu is the Nepal destination.

## Playing

- A fresh game opens a face gallery after boot initialization. Choose any of the
  21 available characters: the seven mansion kids, Fred, Edna, Ed, the two
  tentacles, Sandy, Zak, Annie, Melissa, Leslie, a Caponian, The King, the Zaire shaman,
  and a villager. Portraits are rendered from original costumes at runtime.
- During play, **New kid** or **Worlds → Choose character** opens the same gallery.
  Switching moves your view to that character's current location. The previous
  player stays in the world and resumes independent roaming. Zak characters
  appear only when their original resources are installed.
- Rotate the phone upright for game graphics above and persistent chat below.
  The message field, selected participants, transcript and Follow controls stay
  together. In portrait, sending keeps the keyboard available; landscape keeps
  the compact collapsing bar. Failed sends keep your draft.
- Use an airport computer, select a destination, then **OK** and the gate.
  **Prev / Next** pages through ten free destinations. A flight starts directly
  in the original cabin and continues until **Arrive**. Companions and nearby
  passengers boarding the same route travel together.
- The San Francisco bus remains parked with its original sleeping driver.
  Tap the bus to request a free ride. NPCs can request it too. The driver wakes,
  passengers board, and the front-on bus moves toward the foreground. There is
  no scheduled ten-second cycle. The original driver remains scenery rather
  than a separate conversation character.
- Original platform hotspots open the crystal destination panel. **Worlds →
  Crystal teleport pads** provides the same unlocked sandbox travel. All playable
  characters can use it, without crystal inventory or training requirements.
  Companions come along. The sites are the original crystal-map destinations:
  Seattle, Mexico, Peru (inside the giant carving), Egypt and Mars (the face's
  crystal chamber), plus the map's two spots the original left inert: Mars
  pyramid (the pyramid's crystal room, whose platform is a pad too) and
  Atlantis (Fate of Atlantis's lost city, when that game is installed). Mars is
  reached through this panel, not a commercial airport flight.

## Areas

The airport serves Maniac Mansion, San Francisco, Seattle, Miami, Kinshasa/Zaire,
Kathmandu/Nepal, Cairo, London, Mexico City and Lima/Peru. Seattle, Miami, London
and Mexico City use the original big terminal; the others the regional one, each
with its original signs. Miami remains an airport stop (closed for repairs, as in
the original). The other added areas include Zaire's jungle and village, Kathmandu's
street and sanctuary, Cairo and its pyramid rooms, Stonehenge, Mexico's jungle and
temple passages, Peru's jungle, carving and the carving's ledge and eye chambers
(reached on the bird from the feeder; walkers cannot cross the valley), Caponian headquarters and spacecraft,
and Mars's landing site, hostel, shuttle, face, Great Chamber, pyramid and machine
room. Original resources reused by Zak are also reused here; this is not newly
invented city artwork. Local exits bypass original puzzle script prerequisites.

## Compatibility and verification

Patch 0020 keeps the 25-actor, 800-variable save layout. Four unused actor slots
become the added Zak residents; a separate initialization flag migrates existing
saves. Imported rooms occupy 53–98 and costumes 34–41. Scratch objects 732–764 are
restored on entry. Non-kid players use a shared return-point slot while current
locations remain per actor. Bus phase and manifest use saved variables 765–767.

`tools/test_expansion.py` checks fresh boot without the old picker, all imported
rooms, actual walking input for all playable characters, flights, portraits,
clickable exits, teleport controls, bus requests and save/load. Private screenshots
are generated only under ignored `build/`. Existing bus, flight and old-save
probes cover regression paths. AddressSanitizer checks engine memory behavior.
The Apple build checks UIKit compilation; physical rotation, keyboard feel and
animation timing still need testing on an iPhone.
