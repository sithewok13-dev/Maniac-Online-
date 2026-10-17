# Native iPhone setup

Use the existing ScummVM iOS backend, not SDL on iOS. The pinned upstream guide is
`engine/doc/docportal/other_platforms/ios_build.rst`. This repository does not
include a signed app or claim physical-device validation.

## Download an IPA without owning a Mac

The **iOS unsigned IPA** GitHub Actions workflow uses a hosted `macos-15` runner.
It runs on relevant pushes to the development branch and main. After it reaches
green, open the run's **Artifacts** section and download **SCUMMVERSE-unsigned-IPA**.
Unzip that artifact to get `SCUMMVERSE-unsigned.ipa`. The separate corresponding
source artifact contains the patched engine and build instructions.

Import the IPA into your sideloading/signing tool, such as AltStore or SideStore,
and follow that tool's signing steps. The IPA is unsigned: tapping it in Files
will not install it. No Apple credentials or provisioning profiles are stored in
this repository. Sideloading tools may require initial setup on a computer.

The build targets arm64 iPhones/iPads running iOS 13 or later. It contains the
original DOS V1 direct-launch prototype, with no multiplayer and no game files.
After first launch, use the iPhone **Files** app, **On My iPhone > SCUMMVERSE**, to
create `maniac` and copy all your original `.LFL` files there. Force-close and
reopen SCUMMVERSE. Finder file sharing on a Mac or Apple Devices file sharing on
Windows is another way to populate the same Documents directory.

Each IPA carries its own version, `<patch>.<build>` (for example `63.69`), so
the sideloading tool installs it as an update over the previous one; your game
files and saves in Documents stay. To check which build is running, open the
in-game menu's **Connected worlds**: its message ends with "Build: patch 0063,
build 69 (…)" and how many of your other games are exported for that build.
Other games are set up once, at launch, before Maniac Mansion starts; keep the
app open until then. Folder names ignore case and spaces around them, but
must otherwise match (`loom`, `samnmax`, …). A game folder is found at the
top of Files › SCUMMVERSE or one folder further down (unzipping an archive
of several game folders in the Files app puts them inside a folder named
after the archive; a Mac's `__MACOSX` folder is ignored). Connected worlds
names any top-level folder it doesn't recognize. Once a game is set up, the
Worlds menu's "Play as someone else" lets the character you control
become anyone from it (Indy, Guybrush, Sam and Max, The Creator, …); the
Purple Meteor from Maniac Mansion itself is always offered first, and floats,
followed by the Meteor Police officer (in a glass dome, his helmet, so no
fishbowl on Mars), the man-eating plant (fully grown, rolling on a pot with
wheels; a fishbowl on Mars) and Dead Cousin Ted (on roller skates, a
fishbowl on Mars too);
Loom offers Chaos, who floats; Day of the Tentacle offers Ted dressed up
for the beauty contest (spaghetti hair, big lips), who glides on his skates;
Curse of Monkey Island offers Murray twice (the skull as in the theater, and
green as in the ship's hold). A game whose setup stopped twice is listed as "Could not
set up" and skipped; to retry it, delete its `.try` file in the `worlds`
folder with the Files app. If it still shows an older build, the old app is the one being opened: look for
a second SCUMMVERSE icon (two sideloading tools can install two copies), and
force-close the app before reopening it. Deleting an app also deletes its
Documents folder, so copy your game files out first.

The workflow checks that the app targets iPhoneOS and contains arm64 code, then
checks IPA ZIP integrity. Those checks do not establish successful installation
or gameplay on your device. The build log is available as a diagnostic artifact.
Artifacts expire after 14 days; rerun the workflow when another build is needed.

## Generate and build on a Mac

Requirements: Xcode with iOS SDK, Python 3, Git, a C++ compiler, an Apple signing
team and a connected iPhone. Obtain the upstream v3 iOS XCFramework libraries:
<https://downloads.scummvm.org/frs/build/scummvm-ios7-libs-v3.zip>.

```sh
python3 tools/generate_ios.py
```

Place the extracted **frameworks** directory at `build/ios/frameworks`. Open
`build/ios/scummvm.xcodeproj`. Select the **ScummVM-iOS** target and your physical
iPhone, select your signing team, and set a unique bundle identifier. Build/run
with Xcode. Keep the generated project out of Git; regenerate from pinned source.
Generation on Linux verifies the generator and project structure only, not the
Apple toolchain, SDK, linking, signing, or app runtime.

The fork changes both `dists/ios7/Info.plist` and its `.in` template to display
SCUMMVERSE and declare portrait and landscape orientations. It uses existing
backend settings `orientation_games=auto`, `orientation_menus=auto` (the app
follows the phone's rotation), `touch_mode_2d_games=direct`, and
`filtering=false`. Hold the phone upright (rotation lock may stay on) for the
picture on top and the conversation below; turn it sideways to play full width,
with the conversation beside the picture while it is open.

## Supply the authentic original DOS V1 data

Install the app, then use Finder file sharing or Xcode's device container tools
to place your original DOS V1 resource files here:

```text
Documents/
  maniac/
    00.LFL
    01.LFL
    ... (all .LFL files from the release)
```

The existing iOS entry point changes the working directory to Documents, and its
filesystem is rooted there. No absolute desktop path is embedded into the app.
The files must contain the actual original game data; renaming unrelated files
will not make them compatible. Include files from every disk, preserving names.
Enhanced DOS V2 and demo data are rejected; use an unmixed V1 directory. Relaunch
after transferring data.

Without valid data, a minimal error dialog explains the required location.
Dismiss it and relaunch after correcting the files. The ScummVM game library
does not appear. iOS does not terminate itself on exit; the upstream `quit()` is
a no-op, so the game thread ends and the app must be relaunched. A native import /
retry screen is a future UX improvement, not an implemented feature.

The directory name must be lowercase **`maniac`**, not `Maniac`. On iPhone, use
Files → On My iPhone → SCUMMVERSE → maniac. The owner resolved the initial
"Path does not exist" error by correcting this capitalization.

## Device acceptance checklist

The owner confirmed baseline gameplay works on iPhone after the data-path fix.
The owner also confirmed the door preview; capture/death protection checks remain pending; see [exploration.md](exploration.md).

- Fresh install with no data: clear error, never the ScummVM launcher.
- Valid original DOS V1 files: authentic title, audio, rooms and animations.
- Original game selection completes and touch movement works in landscape.
- Pixel filtering remains off; inspect aspect and device-safe-area scaling.
- Background/foreground, phone interruptions and rotation behave correctly.
- End/return-to-launcher never opens the game-selection frontend.
- Invalid/missing resource files fails visibly, without a silent fallback.

Two-device networking, independent actors and reconnection are not implemented.
The exploration preview removes documented locks and protects audited capture/death
paths. Start a fresh game when testing the new protection: it does not repair an
older save taken midway through capture or death. Other progression barriers
remain, so this is not yet full free exploration.

## Optional on-device dialogue

The **AI** button opens model settings. Start with **Small** (491 MB), downloaded
over Wi-Fi. **Larger** (1.12 GB) is available when memory/temperature checks allow
it. Both run offline afterward; **Classic** requires no model. Stay in the app
while downloading. See [local dialogue](local-ai.md) for limits and fallbacks.
The hosted build includes the runtime, not model weights. Manual builds must also
run `python3 tools/build_local_ai.py` and use the local-AI compiler/linker flags
from `.github/workflows/ios-ipa.yml`.

## Connected worlds and free airport travel

Create a separate lowercase `zak` folder beside `maniac` and copy all original
English Zak DOS V1 `.LFL` files directly inside, including **08.LFL**. Walk beyond
the outer mansion grounds to reach the airport. Walk to the gate or Use the
reservations terminal to choose a free destination. NPCs, including Zak, choose
random destinations and pause travel while talking. **Worlds → Go to airport**
is also available as a testing shortcut.

Keep both data folders when loading saves. See [worlds.md](worlds.md) (packaged as
WORLDS.md) for the exact walking routes and current airport/street/apartment scope.

Leave Zak's apartment through his living room and walk right to the bus for a
free airport ride. The airport's right-hand door takes the return bus. Keep 03.LFL
in the `zak` folder for the street scene. The street stairs return to the apartment;
the corner up the street leads to 14th Avenue (Lou's Loans, the Society office).

Melissa and Leslie's van stands at the Mars landing site. Walk in through its
door and tap the controls: after a countdown it lifts off with everyone in the
cockpit, and you look out at the stars until you tap **Arrive** and pick an
outdoor place (Zak's, the mansion's, or an installed other world's). It stays
parked there, drawn beside you; tap it to board again.

The **CAMERA** button (camera symbol, below Worlds; in portrait after it)
takes pictures of the game:
- Tap: a photo, with a white flash, the shutter sound and "1 photo saved".
  CLEAN (the default) is the room alone; FULL is the whole screen with the
  verbs and inventory. Both are enlarged with sharp pixels (the whole screen
  is 1600 by 1200, in the proportions the phone shows).
- Hold half a second, while the ring around it fills: a selfie. The game
  holds still, everyone in the room turns to the camera and poses (now and
  then someone hasn't noticed, or they all stare at your character), and the
  picture is framed on your character and whoever is near. It takes 1, 3 or
  5 photos (3 unless you change it), posed afresh for each; afterwards
  everything is exactly as it was.
- Slide it down: the options (CLEAN or FULL, SELFIES 1, 3 or 5), remembered.
  Tap anywhere else to close them.
Photos go to the Photos app (it asks once, for adding photos only; the game
holds still while it asks). With that access off they go to Files ›
SCUMMVERSE › Screenshots. Names look like "SCUMMVERSE 2026-10-17 14.05.09
clean.png" ("full", "selfie"; a second one within the same second gets -2,
-3 after the time). On iOS 13 they always go to Files (adding to Photos
needs iOS 14 there).

Zak's crystal teleport panel lists seven sites: Seattle, Mexico, Peru, Egypt,
Mars face, Mars pyramid and Atlantis (Fate of Atlantis's lost city, when that
game is set up).

In The Dig, walk to a tram station's platform edge: the car comes, waits a few
seconds for everyone on the edge, and takes you to the other end of the line.
