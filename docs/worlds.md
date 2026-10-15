# Connected worlds and the free airport

Zak's original San Francisco airport connects the Maniac Mansion grounds and
Zak's street, free airport bus and apartment, Seattle forest/cave, Miami airport and the original plane cabin. Travel is free: no tickets, cash, purchases or puzzle checks.
The selected character keeps their appearance, identity and inventory. NPCs, including
Zak, Annie, Melissa and Leslie, choose destinations randomly and can wander between the connected worlds.

## Zak companions

Annie Larris, Melissa China and Leslie Bennett start in Zak's apartment on their
first initialization, then roam the connected world. They use their original DOS
walking costumes, normalized to the same 120% scale as Zak. Tap **Talk**, select
a character, and use **+** to include others. **Follow** brings them through doors,
on the bus and onto your flight; **Unfollow** lets them explore independently.
They have individual local-AI personalities and newly written offline greetings.
They are also selectable players in the new character gallery. See [expanded worlds](expanded-worlds.md) for the complete available roster and travel map.

Existing saves gain the three visitors without resetting Zak or the mansion cast.
Keep the full original Zak file set installed: their sprites require **06.LFL**
and **28.LFL**. Missing/unsupported optional sprite files leave the existing worlds
usable and produce a diagnostic; installation is retried periodically.

## iPhone setup

Keep Maniac's files in `Documents/maniac`. Create a separate lowercase **zak**
folder in Files → On My iPhone → SCUMMVERSE. Extract the Zak ZIP and copy all 59
original `.LFL` files, `00.LFL` through `58.LFL`, directly into that folder.
The bus street needs **03.LFL**, and the airport needs **08.LFL**, in addition
to the apartment's 00.LFL/01.LFL.
Omit `__MACOSX`; do not mix the games or leave the resources inside the ZIP.

```text
SCUMMVERSE/
  maniac/
    00.LFL
    ...
  zak/
    00.LFL
    01.LFL
    ...
    08.LFL
    ...
    58.LFL
```

## Walking and choosing destinations

- Walk all the way left on the mansion's front grounds, or all the way right
  on the driveway/opening exterior, to reach the airport. The existing path
  between those two exterior screens remains intact.
- **Use** the airport reservations computer to open the purple pixel destination
  panel. Select **Maniac Mansion** or **San Francisco**, then **OK**. Selection
  does not move the player: walk to the **gate to planes** to enter the plane; **Arrive** lands at your destination. **Cancel**
  leaves the previous selection intact. The right-hand door still takes the free bus.
- Leave the apartment through its door, walk right along the street, then
  tap the **bus** to wake the driver and request a ride. No CashCard is needed.
- On the street, **Walk to** the **stairs** to enter Zak's apartment.
- Arrivals are placed inside the destination, away from automatic exits. Use the computer again to change the selected destination.
- **Worlds** remains a shortcut for testing. Its **Return to Maniac Mansion**
  option retains the selected kid's saved departure point; the airport's mansion
  destination always arrives safely on the front grounds.

Travel requires no model. Use **Talk** with an already downloaded model for
individual or shared group conversations with anyone in the current room.

## NPC travel

Inactive kids and mansion NPCs use the same routes as Zak. They walk to exits
while visible; offscreen trips use elapsed travel time without switching your
camera. At the airport any available flight destination may be selected, including
where the NPC just came from. NPCs linger before choosing another route and
pause departures during individual/group conversations or their pending speech.
The active player is never assigned a random destination.

This adds the **airport, street/bus, apartment, plane, Seattle forest/cave and Miami airport**.
It does not run the original Zak campaign. See [flight and bus instructions](flights-and-scene-chat.md). Original Zak room
animations, puzzles, ticket/fare logic and cutscenes remain disabled. No game
assets, multiplayer or model-controlled movement are included.

Keep both game-data folders installed when loading connected-world saves.
Earlier builds cannot load airport saves; keep older saves if downgrading.
Existing apartment saves migrate without resetting Zak's saved position.
Street saves require this bus build or newer. Keep a backup before downgrading.

## Implementation and validation

The importer verifies original English DOS V1 files before decoding:

| File | MD5 | Used for |
| --- | --- | --- |
| 00.LFL | `7020931d5a2be0a49d68e7a1882363e4` | Resource directory |
| 01.LFL | `2e30571757edc1cd0f2a450ba5c89153` | Apartment and Zak costume |
| 03.LFL | `25a9e059a9df572554ee8ceffc08cb9f` | San Francisco street and bus |
| 08.LFL | `5337090e7a6ebdbfb698ebda3750d926` | San Francisco airport |

Audited unused Maniac slots represent airport room 53, apartment room 54, Zak
actor 24/costume 34, Annie/Melissa/Leslie in reserved ending-actor slots 20–22 with added costumes 35–37, and imported objects 650–731. Room 55 is added for the
street; native directory reads retain their original room count. Variables
703–723 retain per-kid return points; 760–762 record world initialization.
The existing indexed resource save format supports the additional room. Transient routes are replanned on load; original actor locations are
preserved. Imported resources can be recreated after eviction or reload. Scene
height switches between Maniac's 136 pixels and Zak's 128 pixels.

With private original resources in sibling `maniac`/`zak` directories:

```sh
python3 tools/test_worlds.py /path/to/maniac
python3 tools/test_airport.py /path/to/maniac
python3 tools/test_bus.py /path/to/maniac
```

The airport probe covers incompatible-data rejection before transfer, isolated
object IDs/scripts, native floor input, both outer walking exits, arrival
protection, free destination selection, stale passenger rejection, every NPC's
visible routes, random offscreen destinations, conversation pauses, inventory,
and save/reload. `--build asan` uses an existing AddressSanitizer null build.
`--old-save /path/to/maniac.s02` also tests a save made by the apartment-only
build. An optional `--snapshot /private/path/airport.ppm` captures a local frame;
do not publish original game assets with source or build artifacts.

These checks and the hosted Apple build do not establish physical iPhone touch
layout, model performance, or uninterrupted device gameplay.

The bus probe checks every playable kid, missing street data without moving
the player, free CashCard-reader interactions, return buses, imported object
isolation, inventory preservation and street save/reload. The airport probe
also checks every roaming NPC on both street connections. Bus travel changes
rooms after boarding; it does not play the original driving cutscene.

## Zak file lookup troubleshooting

On iPhone the app now looks directly in its own `Documents/zak`, independently
of the saved Maniac game path. Leading/trailing folder whitespace, a capitalized `Zak` folder and lowercase `.lfl`
filenames are accepted too. Desktop sibling-folder discovery supports both
absolute paths and a bare relative `maniac` path; `scummverse_zak_path` remains
an explicit override.

A failed import reports whether the folder is unavailable, a named file is
missing/unreadable, or its contents do not match the supported English DOS V1
edition. Open **Worlds** again after a failed trip to read that status. The log
includes the game path and resolved Zak folder when available, and suppresses
repeated identical warnings. All edition checks remain enabled.

## Choose the Zak folder on iPhone

Open **Worlds → Choose Zak folder...**. In the iPhone Files picker, navigate to
and select the extracted `zak` folder containing `00.LFL` directly. Choose the
folder, not the ZIP or its parent. The app checks 00.LFL, 01.LFL, 03.LFL and
08.LFL against the supported original English DOS V1 edition, then imports
available 00.LFL–58.LFL files. After the import succeeds, open **Worlds → Go to
airport**. Files stored in iCloud may need to download during import.

The original folder and previous imports are preserved. A cancelled or failed
import never changes the active import. A complete, verified copy is stored
inside this app's Application Support directory, and its relative location is
saved so app-container UUID changes do not leave a stale absolute path. The
engine reads this native location directly without adding another Documents
prefix. You do not need to edit Preferences or move the source folder.

When no folder has been imported, native Documents/zak discovery remains the
fallback. The desktop path override does not override an iPhone folder selection.
Repeated successful imports keep prior private copies; there is no removal UI
for those copies yet. The picker and file-provider behavior need device testing.

## Connected-world controls

Worlds shows verified installation status for Maniac and the supported Zak resources.
Use **Import Zak from this app** for the local folder; it tolerates surrounding
spaces and case differences. Exact `zak` wins when both spellings exist.

Choose an individual character in **Talk**, then **Follow**. No model is
required for this button. The companion follows the selected kid through rooms,
free buses and airport departures. **Unfollow** releases them to roaming.
Multiple characters can accompany one kid. Switching kids does not reassign their
companions: they wait for their original leader. Companion assignments and each
kid's selected destination are saved. Followers enter rooms at the player's
arrival, then walk behind them. Airport departures enter the original plane cabin
until **Arrive** is pressed. Waiting companions ride the timed street bus together.

Zak's imported sprite renders at 120% around his feet in every room, with nearest
neighbour pixels, existing palettes and room masks. Other characters retain their
individual proportions. A private comparison measured Dave at 72 pixels tall and
normalized Zak close to that height. Fractional scaling produces unequal pixel
widths; it does not replace or redraw the supplied artwork.

`tools/test_companions.py` checks selection versus boarding, stale menus, joining,
dismissing, bus/world/door following, selected-kid isolation, saved assignments,
arrival facts and sprite clipping. It passes null and AddressSanitizer probes.
`tools/test_travel_context.cpp` checks scene-specific AI arrival facts without a
model. Native/chroot folder tests cover leading and trailing spaces. UIKit touch,
keyboard and visual acceptance still require a physical iPhone.
