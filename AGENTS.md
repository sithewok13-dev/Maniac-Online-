# Scummverse / Purple Meteor Initiative

Read docs/SCUMMVERSE_PROGRESS.md first, then docs/SCUMMVERSE_ARCHITECTURE.md.
The user authorizes incremental implementation, tests and focused commits. Fix
existing gameplay before advancing creator, multiplayer or ownership milestones.
Preserve the ScummVM foundation, original artwork and working sideload workflow.

## Repository mechanics

The project root is a patch distribution, not a Git checkout. `engine/` is the
pinned upstream checkout; its working changes materialize patches/0001 onward.
Never commit the engine working tree as though it were the distribution repository.
Run `python3 tools/bootstrap.py` to prepare source. Do not reset user changes.
Capture an alternate Git index of the current engine before editing; generate a
new incremental patch against it. New files must appear in that patch. Verify
`python3 tools/test_bootstrap.py` before publishing. Root changes and patches must
be committed together to the project repository on a non-main branch.

## Validation

Build: `make -C build/null -j3`. Startup: `python3 tools/test_startup.py build/null/scummvm`.
Portable contracts: compile tools/test_{portrait,mobile_layout,seats,conversation}.cpp
with -Iengine and sanitizers, then run. CAMERA: tools/test_camera.cpp with
engine/common/scummverse_camera.cpp (sanitizers); through the engine,
`python3 tools/test_camera_engine.py game-data/mm-dos` (in the data suite). TOUR: tools/test_tour.cpp
with engine/common/scummverse_tour.cpp (ASan, TSan); through the engine,
`python3 tools/test_tour_engine.py game-data/mm-dos` (in the data suite; enters every stop).
WANDERERS: tools/test_wander.cpp with engine/common/scummverse_wander.cpp (ASan, TSan);
through the engine, `python3 tools/test_wander_engine.py game-data/mm-dos` (in the data suite). LIGHTS
and DOORS: `python3 tools/test_lights_doors.py game-data/mm-dos` (in the data suite). WiFi sessions: compile tools/test_net.cpp with engine/common/scummverse_net.cpp
(ASan, TSan). Dialogue runtime without weights (ASan/TSan):
`python3 tools/test_talk_runtime.py`. Apple CI (macos-15) builds the IPA on pushes
to main, codex/** and claude/**; it is not blocked. Each IPA is stamped
`<patch>.<run>` (tools/package_ipa.py, `python3 tools/test_package_ipa.py`). Hugging Face may be blocked in
cloud sessions, so real-model probes may only be compile-checked there.
With privately supplied assets: `python3 tools/test_expansion.py game-data/mm-dos`.
Other worlds: `python3 tools/export_worlds.py game-data/mm-dos monkey2=game-data/<dir> ...`
(folders: monkey monkey2 loom indy3 atlantis tentacle samnmax ft dig comi)
then `python3 tools/test_world_visit.py game-data/mm-dos` (cache in build/worlds;
scenes .svw, characters .svc; walks every door, a few minutes). Launch-time
setup: `python3 tools/test_world_setup.py game-data/mm-dos loom=game-data/loom-ega`.
Door maps and casts are generated: `python3 tools/world_maps.py` and
`python3 tools/world_cast.py` read private analysis in build/foreign/ and
rewrite engine/common/scummverse_world_{maps,cast}.inc (commit those, never
build/foreign/).
Probe runner temporarily instruments scumm.cpp; do not run probes concurrently
with builds or other probes. It restores source and binaries. Native compilation
is not iOS device acceptance. Local NPC tests are not multiplayer tests.

## Boundaries and safety

Prefer portable, narrow modules and edition-specific adapters to scattered room
exceptions. AI proposes; deterministic systems validate. No public proprietary
assets, extracted scripts, model weights, private paths, keys or credentials.
Keep private reference images and supplied game data in ignored directories.
No paid services, mainnet activity, real minting, token issuance, irreversible
transfers or destructive user-data changes without explicit authorization.
Do not create a replacement app or abandon ScummVM. Keep continuity records
honest: proposed, implemented, compiled, tested and device-tested are distinct.
