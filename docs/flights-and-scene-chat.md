# Scene conversations and flights

This preview uses the original English DOS V1 Maniac Mansion and Zak McKracken
files already imported into SCUMMVERSE. It includes the previous Qwen Metal
ownership fix. No game images, scripts, or model weights are bundled.

## Conversation controls

Tap **Talk**, then click a character in the game scene. A small message bar opens
with that recipient selected. Sending hides the keyboard and collapses the bar;
tap the recipient to write again. Player and NPC lines appear in the scene.
**+** selects another character to join the same conversation. These explicit
groups share history; unrelated bystanders do not automatically join. **History**
expands recent messages. **Follow / Unfollow** stays in the conversation.
**Close** ends it. A room change, player change, or app backgrounding ends the
session. Failed sends keep the draft and show an error. A downloaded, ready model
is required to generate replies. At most two NPCs reply to each message.

## Destinations and flights

Use the airport reservations computer, select a destination, and walk to the gate.
Destinations: Maniac Mansion, San Francisco, Seattle, and Miami. Seattle includes
the original regional airport, forest, and Mt. Rainier cave. Miami currently has
its regional airport only; more surrounding rooms are not part of this preview.
The original game reuses the regional-airport artwork between cities.

The gate takes you directly into the original plane cabin, already in flight.
There is no takeoff sequence. **Arrive** is immediately available on the right.
Until it is pressed, the flight stays open for walking and talking. Companions
board together. Non-companions join only if they are at that airport's gate,
waiting for the same destination when the player boards. Passengers and the
route survive save/load and arrive together. Only one player-held flight can be
active at once; switch back to the travelling kid and finish it before starting
another. Worlds shortcuts cannot silently strand a cabin's passengers.

In Seattle, walk outside the airport to the forest, then to Mt. Rainier to enter
the cave. The cave exit and forest airport exit return along the same route.
Use either regional airport computer for another flight. All fares remain free.

## Bus

The San Francisco street bus follows a ten-second game-time cycle: one second
arriving, two seconds stopped, one departing, six away. Walk into the stop area,
or use the original bus / reader hotspot, to wait. Walk away to cancel. Waiting
players and their companions transfer at departure; NPC routes also wait for the
bus stop window. Opening a game menu can pause game time.

The bus body is part of the original background. The adapter repositions its
original tiles and uses the game's bus-absent object for the uncovered pavement.
The driver overlays move with it. No replacement vehicle artwork is generated.

## Implementation and validation

Patch 0017 adds rooms 56–60; 56 is the cabin, 57 Seattle airport, 58 forest,
59 cave, and 60 Miami airport. These sightseeing rooms reuse the scratch object
IDs 732–764 and restore their own states on entry; foreign puzzle scripts never
run. Original files 09, 11, 12, and 13 are checked against the supported edition's
hashes before use. Existing object-table and variable capacities are unchanged.
Variables 724–727 persist the active flight route, passenger mask, origin, and
original player. Bus and NPC departure timers are transient after loading.

`tools/test_flights.py` checks private original-data loading, manifests,
indefinite flights, save/load, connected exits, and bus waiting/cancellation.
`tools/test_scene_talk.cpp` checks scene selection, explicit groups, stale picks,
and no-model failures. The real-model group test checks player speech followed by
attributed, serial NPC replies. Native compilation and address-sanitizer probes
do not replace touch/keyboard testing on an iPhone.

The bus carries the original awake driver from Zak’s DOS street graphics. His cab
image and mask move with the bus during arrival and departure, and disappear
with it offscreen. The original sleeping and talking overlays stay disabled so
they cannot leave a second driver behind. The driver is scenery, not a roaming
conversation participant.
