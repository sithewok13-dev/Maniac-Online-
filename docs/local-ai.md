# Optional local dialogue preview

Tap **AI** in the upper-right controls. The default is **Classic**, which needs
no model and keeps the existing randomized lines. Choose Small or Larger for lower memory use, or **Qwen3 4B** for the experimental
conversation preview on phones with sufficient memory.

- **Small:** Qwen2.5-0.5B-Instruct Q4_K_M, 491,400,032 download bytes.
- **Larger:** Qwen2.5-1.5B-Instruct Q4_K_M, 1,117,320,736 download bytes.
- **Qwen3 4B:** Q4_K_M, 2,497,280,256 download bytes (2,497 MB). Thinking is disabled.
- First download requires Wi-Fi. Keep the app in the foreground until it finishes;
  backgrounding cancels the download, and retry starts over (there is no resume;
  a download may take up to six hours). A download that had already finished and
  passes its check is kept: choose the model again to use it. Tap AI to see progress.
- Downloads are optional and are not included in each IPA. After downloading,
  dialogue runs offline. No API key, external inference service or chat upload.
- Classic/cancel stops generation/downloads. Delete downloaded models also frees
  disk storage. Switching models loads only one at a time.

The inference worker receives a character identity/personality, the current room,
the selected player identity, and at most one prior generated line for ambient encounters.
Explicit conversations also include the last six attributed messages,
held only in memory until the conversation closes. The prompt also receives the
player's latest arrival origin and the characters recorded as arriving with them.
These are engine facts; no additional journeys or relationships are inferred.
It has no movement, door, inventory, script-execution or network capability.
**NPC movement still uses the roaming engine.** Model-driven intentions are not
part of this first dialogue integration.

## Talk preview

Tap **Talk**, then a character directly in the scene. Type in the small message
bar and use Send or the keyboard Send key. Sending dismisses the keyboard and
collapses the bar; tap the recipient to write again. Failed sends retain the draft
and show an error. Player and NPC lines appear in the scene. **History** expands
recent messages; **Close** ends the conversation. Keyboard dictation uses iOS.

Use **+**, then tap another character to add them to the same conversation.
Participants pause their wandering; the rest of the room continues. Bystanders
are not added automatically. Up to two characters reply per message, sequentially,
with a rotating first speaker. The second sees the first speaker's successful
reply. Departed characters cannot deliver late replies. Room/player changes end
the conversation. See [scene chat and travel](flights-and-scene-chat.md).

Only one model is loaded. Two replies can take up to 30 seconds each. The panel
labels every reply with its actual speaker. The game speech renderer waits for an
existing line to finish before presenting the next queued line. There is no
unbounded NPC-to-NPC chatter after a player message. Shared history is capped at
six recent messages, with older entries dropped if needed to fit the token budget. A room or player change,
loading a save, entering the background, or disabling the model ends the conversation.
There is no voice synthesis, persistent relationship memory, or model-controlled action.

Messages are limited to 160 characters / 512 UTF-8 bytes. Only one request can be
active. A failed/slow reply is explicitly reported; no fabricated answer is inserted.
The model's replies can be inaccurate or out of character. A larger model is not a
guarantee of reasoning or reliable game knowledge.

The AI settings screen now scrolls in landscape and updates download progress while
open. Failures distinguish network error codes, HTTP errors, storage failures and
size/hash mismatches. A download still requires Wi-Fi and restarts after cancellation.

## Compatibility and fallback

The app's iOS 13 arm64 baseline remains. Model availability is checked against
actual physical/free memory and temperature, not an assumed phone model name.
Physical memory is taken as the size the phone is sold with (rounded up to whole
GiB: iOS reports a little less, some 5.5 GiB on a 6 GB phone). Small initially
requires a 3 GB phone and 800 MiB available; Larger requires 6 GB and 1,600 MiB
available. Qwen3 4B requires at least 10 GB and 3,500 MiB available. A tier the
phone can never meet says "Needs a phone with more memory". This targets high-memory phones
such as the 17 Pro; actual on-device compatibility remains unverified. These conservative gates are not
claims of tested device compatibility or protection against every OS memory kill.

Lower-memory phones use CPU inference with two threads. Phones of 6 GB and more
use Metal. The app does not use Apple Intelligence or require
a Neural Engine API. All phones can keep using Classic without loading weights.
Any loss of focus (Control Center, a banner, a call, the Photos prompt) stops what
the model is writing, waiting up to 300 ms for the worker to be out of llama (iOS
refuses GPU work from the background), and starts nothing until the app is active
again: a reply cut off is then written again; a greeting is left to the game's own
line; the conversation and the model stay. Memory warnings, serious/critical
thermal conditions, or entering the background (after up to a further second for a
decode still running) cancel inference and unload the model asynchronously. Returning to the foreground
attempts to reload the selected downloaded model; after a pressure warning, select
a model again to retry while remaining in the foreground.

A shared worker accepts one request at a time. It uses a 1,024-token context, 64-token
prompt batches, at most 80 output tokens, and a five-second ambient inference deadline.
An explicit chat reply gets up to 30 seconds; short ASCII sentences are still required.
CPU decoding checks cancellation internally; GPU work is checked between decode
batches, so a running Metal command cannot be interrupted instantaneously. The
worker counts as out of llama only once the GPU has finished what it was sent.
On iOS's will-terminate (and before the desktop probes return) the worker is
stopped and the model unloaded while llama's own statics still exist.
The greeting NPC pauses briefly while it waits; other actors and player controls
continue. The encounter falls back after six seconds of game time.
Responses for departed characters, another room, or a different selected player
are discarded. Existing speech is not interrupted. Unsafe renderer control bytes,
role prefixes, tags, incomplete sentences and overly long/non-ASCII output are
rejected. This is a text-format safeguard, not a guarantee of dialogue quality.

## Reproducibility and validation

`local-ai.json` pins llama.cpp b6500 to an exact commit and pins all three model
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

Individual Talk headers also offer **Follow** / **Unfollow**.
These explicit buttons command the game engine; dialogue itself still cannot
move characters. Group conversations retain their shared, attributed transcript.

## Metal model-unload repair

The pinned runtime's mapped-buffer cleanup previously used the owned shared-buffer
destructor. On iOS that calls `free()` on a borrowed mmap pointer. A physical-device
crash report identified `POINTER_BEING_FREED_WAS_NOT_ALLOCATED` in this exact path
while unloading Qwen3. This is distinct from an iOS Jetsam memory termination.

`tools/runtime-patches/0001-metal-mapped-ownership.patch` assigns mapped buffers
a destructor that releases Metal/residency objects and their wrapper without
freeing the borrowed model storage. Owned shared allocations retain their original
destructor. The builder applies this patch idempotently to the pinned revision
and rejects conflicts. Corresponding source includes both the patch and the
modified runtime. Model weights and inference settings are unchanged.

`tools/test_metal_ownership.py build/llama-src` executes the actual cleanup bodies
with mocked Metal-object releases and real malloc/mmap storage under AddressSanitizer.
It checks 100 borrowed/owned cleanup cycles and destructor dispatch. It does not
exercise a physical GPU; on-device Qwen3 activation/unloading still needs retesting.

## Metal background-failure repair

iOS refuses GPU work from an app in the background; the pinned runtime aborted the
app (`GGML_ABORT` in `ggml_backend_metal_synchronize`) when a tensor copy's command
buffer failed. `tools/runtime-patches/0002-metal-failed-copy-no-abort.patch` logs
the failure, releases the buffer and makes the next graph compute report
`GGML_STATUS_FAILED` (a failed decode) instead. The dialogue runtime's focus wait
is meant to keep the worker from reaching this; the patch covers a decode that
outlasts the wait. Compiled only by the iOS build; not exercised on a GPU here.
