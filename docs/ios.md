# Native iPhone setup

Use the existing ScummVM iOS backend, not SDL on iOS. The pinned upstream guide is
`engine/doc/docportal/other_platforms/ios_build.rst`. This repository does not
include a signed app or claim physical-device validation.

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
SCUMMVERSE and declare landscape orientations. It uses existing backend settings
`orientation_games=landscape`, `orientation_menus=landscape`,
`touch_mode_2d_games=direct`, and `filtering=false`.

## Supply the authentic C64 data

Install the app, then use Finder file sharing or Xcode's device container tools
to place your original disk images here:

```text
Documents/
  maniac/
    maniac1.d64
    maniac2.d64
```

The existing iOS entry point changes the working directory to Documents, and its
filesystem is rooted there. No absolute desktop path is embedded into the app.
The files must contain the actual original game data; renaming unrelated images
will not make them compatible. Relaunch after transferring data.

Without valid data, a minimal error dialog explains the required location.
Dismiss it and relaunch after correcting the files. The ScummVM game library
does not appear. iOS does not terminate itself on exit; the upstream `quit()` is
a no-op, so the game thread ends and the app must be relaunched. A native import /
retry screen is a future UX improvement, not an implemented feature.

## Device acceptance checklist (not yet executed)

- Fresh install with no data: clear error, never the ScummVM launcher.
- Valid original C64 disks: authentic title, audio, rooms and animations.
- Original game selection completes and touch movement works in landscape.
- Pixel filtering remains off; inspect aspect and device-safe-area scaling.
- Background/foreground, phone interruptions and rotation behave correctly.
- End/return-to-launcher never opens the game-selection frontend.
- Invalid/missing second disk fails visibly, without a silent fallback.

Only after these checks pass should exploration overrides be enabled. Two-device
networking, independent actors, free exploration and reconnection are not part
of this direct-launch milestone and cannot yet be acceptance-tested.
