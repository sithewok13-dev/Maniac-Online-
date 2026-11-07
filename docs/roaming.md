# Roaming sandbox preview

This replaces the story-driven NPC patrols with autonomous exploration in the
verified English original DOS V1 edition (index MD5
`7f45ddd6dbfbf8f80c0c0efea4c295bc`). Start a **new game** when upgrading from a
story/safety preview. Existing mid-cutscene or capture saves are not repaired.

The original character picker remains. The introduction and story cinematics are
disabled, including timed interruptions and endings. The radiation suit ending
handoff is also disabled so it cannot remove the team or lock character switching. This is an exploration
sandbox, not a completable original campaign.

## Behavior

- All seven kids, Fred, Edna, Weird Ed, Purple Tentacle, Green Tentacle, and Sandy
  roam; the currently controlled kid never roams autonomously. New Kid still
  selects members of the original chosen team.
- The 36 navigable mansion/grounds rooms form a connected graph, with 73 directed
  passage records including an exit from the alternate garage backdrop. Title,
  character-selection, TV, telescope and ending-only scenes are not destinations.
- Visible actors use the real V1 walking/pathfinding and original costumes. They
  walk to an exit, open both sides of a door, then enter the adjoining room.
  Offscreen movement uses timed room transitions without loading scenes or moving
  the player's camera. Dead ends allow backtracking; other rooms prefer a new exit.
- Player Walk to can open/traverse the same passages without keys, combinations,
  tentacle food, or story prerequisites. The sealed lab exit also works in reverse.
  Entering the pool area drains it and reveals the ladder; entering the plant room
  grows and pacifies the plant so its attic route is usable.
- 52 newly authored, character-specific offline lines are selected at encounters,
  with repeat avoidance and 20–40 second per-character cooldowns. These are random
  lines, **not live AI generation**. No server, API key, or network is required.
- Dead Cousin Ted, the meteor, plants, vehicles and cinematic-only actors are not
  given walking routines. No replacement sprites are introduced.
- Normal saves retain actor rooms/positions. Transient routes are replanned on
  load; selecting a roaming kid cancels that kid's autonomous walk.

## Implementation and checks

`0005-roaming-sandbox.patch` adds a DOS-specific adapter, compiled through the
existing SCUMM translation unit on desktop and iOS. It reads door coordinates
from user-supplied resources; the repository contains topology identifiers and
new dialogue, not game assets or decompiled scripts.

The adapter blocks audited cinematic/controller scripts before their camera and
input effects. Actor opcode guards prevent room entry/exit scripts from resetting
NPC positions. Passage handling is limited to the verified topology. Legacy
exploration/safety behavior remains available with `scummverse_roaming=false`.

Local verification uses `python3 tools/test_roaming.py /path/to/dos-v1-data` with a
temporary, instrumented real interpreter. It covers original boot cleanup,
cutscene rejection, every passage, visible NPC traversal, all roaming costumes,
player/camera isolation, kid switching, dialogue cooldowns and save/reload.
Timers are accelerated in these probes. They do not verify physical iPhone
rendering, sound, or touch; those still require device testing.

For device validation: start fresh, select your team, visit the kitchen and upper
hallway, watch characters leave and enter, follow one through a door, switch kids,
and save/relaunch/load. Check that dialogue never steals control and no story
cutscene interrupts exploration. Multiplayer is local WiFi play only (from patch
0053; docs/SCUMMVERSE_ARCHITECTURE.md, Local WiFi play); riding together on two
devices is not done yet.
