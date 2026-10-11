# Optional local dialogue preview

Tap **AI** in the upper-right controls. The default is **Classic**, which needs
no model and keeps the existing randomized lines. Choose **Small** first; choose
**Larger** only if it is enabled and Small is comfortable on your phone.

- **Small:** Qwen2.5-0.5B-Instruct Q4_K_M, 491,400,032 download bytes.
- **Larger:** Qwen2.5-1.5B-Instruct Q4_K_M, 1,117,320,736 download bytes.
- First download requires Wi-Fi. Keep the app in the foreground until it finishes;
  backgrounding cancels the download, and retry starts over. Tap AI to see progress.
- Downloads are optional and are not included in each IPA. After downloading,
  dialogue runs offline. No API key, external inference service or chat upload.
- Classic/cancel stops generation/downloads. Delete downloaded models also frees
  disk storage. Switching models loads only one at a time.

The inference worker receives a character identity/personality, the current room,
the selected player identity, and at most one prior generated line for that actor.
It has no movement, door, inventory, script-execution or network capability.
**NPC movement still uses the roaming engine.** Model-driven intentions are not
part of this first dialogue integration.

## Compatibility and fallback

The app's iOS 13 arm64 baseline remains. Model availability is checked against
actual physical/free memory and temperature, not an assumed phone model name.
Small initially requires 3 GiB physical memory and 800 MiB available; Larger
requires 6 GiB physical and 1,600 MiB available. These conservative gates are not
claims of tested device compatibility or protection against every OS memory kill.

Lower-memory phones use CPU inference with two threads. Phones reporting at least
6 GiB physical memory use Metal. The app does not use Apple Intelligence or require
a Neural Engine API. All phones can keep using Classic without loading weights.
Memory warnings, serious/critical thermal conditions, or entering the background
cancel inference and unload the model asynchronously. Returning to the foreground
attempts to reload the selected downloaded model; after a pressure warning, select
a model again to retry while remaining in the foreground.

A shared worker accepts one request at a time. It uses a 512-token context, 64-token
prompt batches, at most 48 output tokens, and a five-second inference deadline.
CPU decoding checks cancellation internally; GPU work is checked between decode
batches, so a running Metal command cannot be interrupted instantaneously.
The greeting NPC pauses briefly while it waits; other actors and player controls
continue. The encounter falls back after six seconds of game time.
Responses for departed characters, another room, or a different selected player
are discarded. Existing speech is not interrupted. Unsafe renderer control bytes,
role prefixes, tags, incomplete sentences and overly long/non-ASCII output are
rejected. This is a text-format safeguard, not a guarantee of dialogue quality.

## Reproducibility and validation

`local-ai.json` pins llama.cpp b6500 to an exact commit and pins both model
revisions, byte counts, and SHA-256 hashes. Downloads are verified before being
moved into the model directory or loaded. Interrupted downloads never become the
active model. Models live in Application Support, excluded from iCloud backup.

`tools/build_local_ai.py` builds static CPU/Metal libraries on hosted macOS,
embedding Metal shader source and targeting baseline arm64 instructions for older
phones. The iOS workflow links these into the existing ScummVM app. Plain desktop
builds retain a no-model bridge and do not require llama.cpp. Source artifacts
include the pinned runtime; model weights and original game files stay excluded.
Runtime/model notices are in `LOCAL_AI_LICENSES.txt` inside the IPA and its ZIP.

Local checks include real CPU generation with both pinned models, output
filtering, bounded queueing, cancellation, missing-model/off fallback, plus a real
DOS VM probe with controlled asynchronous responses for display, timeout, camera/
control isolation and stale-room/player cancellation. The existing roaming probe
continues to pass, including passages, the cast, and save/reload.

Device generation speed, GPU behavior, temperatures and download UI still need
physical-device testing. Linux CPU timings are not iPhone benchmarks. Small-model
lines can be bland or occasionally unsuitable; Classic remains one tap away.

For source builds, follow `docs/ios.md` and the exact linker flags in the iOS
workflow. `python3 tools/build_local_ai.py` requires macOS/Xcode. The portable
runtime test is `tools/test_local_ai.cpp`; link it to the pinned llama/ggml static
libraries and pass a verified GGUF path. The game integration probe is:

```
python3 tools/test_ai_encounters.py /path/to/original-dos-v1
```
