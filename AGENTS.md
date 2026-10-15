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
Portable portrait contract: compile tools/test_portrait.cpp with -Iengine and run.
With privately supplied assets: `python3 tools/test_expansion.py game-data/mm-dos`.
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
