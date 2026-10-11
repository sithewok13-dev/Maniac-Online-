# Connected worlds: first Zak visit

This preview connects the original English DOS V1 Maniac Mansion sandbox to
Zak McKracken's apartment. The selected Maniac kid keeps their appearance,
identity and inventory. Zak walks around his apartment and appears in **Talk**.
Return through **Worlds** to the room and position where that kid left.

## iPhone setup

Keep Maniac's files in `Documents/maniac`. Create a separate lowercase **zak**
folder in Files → On My iPhone → SCUMMVERSE. Extract the Zak ZIP and copy its
original `.LFL` files directly into that folder, with `00.LFL` and `01.LFL` at
the top level. Copy all 59 files, `00.LFL` through `58.LFL`; omit `__MACOSX`.
Do not mix the two games' files or put the ZIP itself in the folder.

```text
SCUMMVERSE/
  maniac/
    00.LFL
    ...
  zak/
    00.LFL
    01.LFL
    ...
    58.LFL
```

After selecting your kids, tap **Worlds → Visit Zak's apartment**. To return,
tap **Worlds → Return to Maniac Mansion**. Missing or incompatible Zak data
leaves you in your current room. Correct the files, then retry Worlds.

Travel and wandering require no model. Typed conversation uses the existing
downloaded model through **AI**, then **Talk → Zak McKracken**. Qwen3 4B remains
available on devices passing its memory checks. Group Talk includes Zak and
any other visiting kid present. No model upgrade or second model is required.

Keep both data folders installed when loading saves from this preview,
including saves made inside Zak's apartment. Older builds do not know how to
load the added world; keep earlier saves if you intend to downgrade.

## Deliberate first-milestone limits

Only the apartment is connected. Its original art, walkboxes, object images
and Zak costume come from your files. Zak's puzzle scripts, room animations,
cutscenes and exits are disabled: interacting with a foreign object does not
run a Maniac script with the same number. Use Worlds to leave.

Zak currently stays in his apartment. Autonomous cross-game journeys, the rest
of Zak's locations, shared puzzles/items, and importing other games are future
work. This is a bounded adapter, not a general multi-game virtual machine.

## Implementation and validation

The adapter accepts the English V1 index MD5
`7020931d5a2be0a49d68e7a1882363e4` and apartment file MD5
`2e30571757edc1cd0f2a450ba5c89153`. It verifies user files before decoding or
changing the current scene. Hashes identify an edition; no assets are embedded.

Audited unused Maniac slots represent `zak:apartment` (room 54), `zak:zak`
(actor 24, costume 34), and apartment objects 650–682. Variables 703–723 keep
per-kid return coordinates; variable 760 records initialization. The existing
serializer retains those slots without changing save-array sizes. Imported
resources are recreated from the user's files on resource eviction or reload.
The scene switches between Maniac's 136-pixel height and Zak's 128-pixel height.

With private, locally supplied data in sibling `maniac`/`zak` directories:

```sh
python3 tools/test_worlds.py /path/to/maniac
```

The probe exercises missing-data rejection, separate actor/object resources,
walking, native input, Talk integration, inventory ownership, return position,
and save/reload. `--build asan` uses an existing AddressSanitizer null build.
These checks and a hosted Apple build do not replace physical iPhone testing.
