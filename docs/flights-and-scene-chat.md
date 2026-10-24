# Scene conversations and flights

This preview uses the original English DOS V1 Maniac Mansion and Zak McKracken
files already imported into SCUMMVERSE. It includes the previous Qwen Metal
ownership fix. No game images, scripts, or model weights are bundled.

## Conversation controls

Tap **Talk**, then click a character in the game scene. A small message bar opens
with that recipient selected. In landscape, sending hides the keyboard and collapses the bar;
tap the recipient to write again. Portrait keeps the lower-half chat and composer available. Player and NPC lines appear in the scene.
**+** selects another character to join the same conversation. These explicit
groups share history; unrelated bystanders do not automatically join. **History**
expands recent messages. **Follow / Unfollow** stays in the conversation.
**Close** ends it. A room change, player change, or app backgrounding ends the
session. At most two NPCs reply to each message, with rotating leads.
Sending never requires a model: without one (Classic, the default) or when a
reply fails or times out, the character answers with an authored line marked
**(classic)**. You can keep typing while replies are pending; up to three
messages wait in order and enter the transcript only after earlier replies, so
answers always follow the message they answer. A rejected send keeps the draft.

## Destinations and flights

Use the airport reservations computer, select a destination, and walk to the gate.
The paged destination list now has ten entries; see [expanded worlds](expanded-worlds.md). Seattle includes
the original regional airport, forest, and Mt. Rainier cave. Miami currently has
its regional airport only; more surrounding rooms are not part of this preview.
The original game reuses the regional-airport artwork between cities.

The gate takes you directly into the original plane cabin, already in flight.
There is no takeoff sequence. **Arrive** is immediately available on the right.
Until it is pressed, the flight stays open for walking and talking. Companions
board together. Non-companions join only if they are at that airport's gate,
waiting for the same destination when the player boards. Passengers and the
route survive save/load and arrive together. Only one player-held flight can be
active at once; switch back to the travelling character and finish it before starting
another. Worlds shortcuts cannot silently strand a cabin's passengers.

In Seattle, walk outside the airport to the forest, then to Mt. Rainier to enter
the cave. The cave exit and forest airport exit return along the same route.
Use either regional airport computer for another flight. All fares remain free.

## Bus

The San Francisco bus now waits with its driver asleep until a player or NPC
requests a ride. Tap the original bus. Boarding is free, the driver wakes, and
the front-facing original bus art moves down toward the foreground. The original
bus-absent object supplies the uncovered pavement. The driver moves with the cab.


## Implementation and validation

Patch 0017 adds rooms 56–60; 56 is the cabin, 57 Seattle airport, 58 forest,
59 cave, and 60 Miami airport. These sightseeing rooms reuse the scratch object
IDs 732–764 and restore their own states on entry; foreign puzzle scripts never
run. Original files 09, 11, 12, and 13 are checked against the supported edition's
hashes before use. Existing object-table and variable capacities are unchanged.
Variables 724–727 persist the active flight route, passenger mask, origin, and
original player. The bus phase is saved; NPC route planning is transient after loading.

`tools/test_flights.py` checks private original-data loading, manifests,
indefinite flights, save/load, connected exits, and requested bus boarding.
`tools/test_scene_talk.cpp` checks scene selection, explicit groups, stale picks,
and no-model failures. The real-model group test checks player speech followed by
attributed, serial NPC replies. Native compilation and address-sanitizer probes
do not replace touch/keyboard testing on an iPhone.
