#!/usr/bin/env python3
"""Exercise the real null-backend executable, without copyrighted fixtures."""
from pathlib import Path
import gzip
import re
import struct
import subprocess
import sys
import tempfile
import unittest


def export_version(gameid):
    """A game's export version, as worldExportVersion in
    common/scummverse_world_catalog.h gives it: the base, plus the lead of
    the first of its choices that names the game (the mansion's own; from
    0254 Monkey Island 2's; from 0258 one for several games at once), else
    nothing."""
    catalog = (Path(__file__).resolve().parent.parent / "engine/common/scummverse_world_catalog.h").read_text()
    base = int(re.search(r"kWorldExportVersion = (\d+);", catalog).group(1))
    body = re.search(r"inline int worldExportVersion\(const char \*gameid\) \{(.*?)\n\}", catalog, re.S).group(1)
    for names, lead in re.findall(r'((?:same\(gameid, "[^"]+"\)\s*(?:\|\|\s*)?)+)\?\s*(\d+)\s*:', body):
        if f'same(gameid, "{gameid}")' in names:
            return base + int(lead)
    return base

BINARY = Path(sys.argv.pop(1) if len(sys.argv) > 1 else "build/null/scummvm").resolve()


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="scummverse test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "scummvm.ini"
        self.config.write_text("[scummvm]\n")

    def run_game(self, *args):
        return subprocess.run([str(BINARY), f"--config={self.config}", *args],
                              cwd=self.root, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=15)

    def assert_data_failure(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("SCUMMVERSE: could not start Maniac Mansion (original DOS V1)", result.stdout)
        self.assertIn("game ID 'maniac'", result.stdout)

    def test_version_remains_available(self):
        result = self.run_game("--version")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("ScummVM 2.9.1", result.stdout)

    def test_game_detection_remains_available(self):
        result = self.run_game("--list-games")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Maniac Mansion", result.stdout)

    def test_no_arguments_selects_maniac_and_exits_without_data(self):
        self.assert_data_failure(self.run_game())

    def test_empty_default_data_directory(self):
        (self.root / "maniac").mkdir()
        self.assert_data_failure(self.run_game())

    def test_explicit_path_with_spaces(self):
        data = self.root / "my original disks"
        data.mkdir()
        self.assert_data_failure(self.run_game(f"--path={data}", "scumm:maniac"))

    def test_other_game_is_rejected(self):
        result = self.run_game("scumm:monkey")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("only Maniac Mansion (original DOS V1) and the sandbox are supported", result.stdout)

    def test_saved_launcher_preference_does_not_open_launcher(self):
        self.config.write_text("[scummvm]\ngui_return_to_launcher_at_exit=true\n")
        self.assert_data_failure(self.run_game())

    def test_saved_unrelated_target_is_rejected(self):
        self.config.write_text("[scummvm]\n\n[other]\nengineid=scumm\ngameid=monkey\npath=.\n")
        result = self.run_game("other")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("only Maniac Mansion (original DOS V1) and the sandbox are supported", result.stdout)

    def test_saved_story_target_is_rejected(self):
        # Story play's own targets (one per game, kept in the configuration)
        # are opened from Maniac's Worlds menu only, never at the start.
        self.config.write_text("[scummvm]\n\n[scummverse-story-monkey]\nengineid=scumm\ngameid=monkey\npath=.\nscummverse_story=true\n")
        result = self.run_game("scummverse-story-monkey")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("only Maniac Mansion (original DOS V1) and the sandbox are supported", result.stdout)

    def test_saved_maniac_story_target_is_rejected(self):
        # The mansion's own story is Maniac Mansion too, but it is opened from
        # the mansion only: never the one the app starts as.
        self.config.write_text("[scummvm]\n\n[scummverse-story-maniac]\nengineid=scumm\ngameid=maniac\npath=.\nplatform=dos\nscummverse_story=true\nscummverse_roaming=false\n")
        for name in ("scummverse-story-maniac", "SCUMMVERSE-STORY-MANIAC"):
            result = self.run_game(name)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("only Maniac Mansion (original DOS V1) and the sandbox are supported", result.stdout)

    def test_any_story_marked_target_is_rejected(self):
        # (Known by its key, whatever it is named.)
        self.config.write_text("[scummvm]\n\n[mine]\nengineid=scumm\ngameid=maniac\npath=.\nplatform=dos\nscummverse_story=true\n")
        result = self.run_game("mine")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("only Maniac Mansion (original DOS V1) and the sandbox are supported", result.stdout)

    def test_maniac_story_target_follows_the_mansion(self):
        # Set up from the mansion's own folder at each start, with none of
        # the mansion's additions (even when its data is missing).
        data = self.root / "my original disks"
        data.mkdir()
        self.assert_data_failure(self.run_game(f"--path={data}", "scumm:maniac"))
        config = self.config.read_text()
        self.assertIn("[scummverse-story-maniac]", config)
        story = config.split("[scummverse-story-maniac]")[1].split("\n[")[0]
        for line in ("gameid=maniac", "platform=dos", "scummverse_story=true", "scummverse_roaming=false",
                     "scummverse_exploration_doors=false", "scummverse_exploration_safety=false", f"path={data}"):
            self.assertIn(line + "\n", story + "\n", story)

    def test_story_playing_goes_on_then_the_list(self):
        # Stopped in a story in Story mode: the next start goes on in it (here
        # it cannot start: no data), then Story mode's list (here nothing is
        # chosen: Explore mode, the mansion); the story to go on in is taken.
        (self.root / "monkey").mkdir()
        # (Already set up for the worlds: no export first, so the story is the
        # first run itself.)
        (self.root / "worlds").mkdir()
        (self.root / "worlds" / f"monkey-v{export_version('monkey')}.svx").write_bytes(b"")
        self.config.write_text("[scummvm]\nscummverse_mode=story\nscummverse_story_playing=scummverse-story-monkey\n\n"
                               "[scummverse-story-monkey]\nengineid=scumm\ngameid=monkey\ndescription=The Secret of Monkey Island\n"
                               f"path={self.root / 'monkey'}\nscummverse_story=true\n")
        result = self.run_game()
        self.assertIn("SCUMMVERSE: going on with scummverse-story-monkey", result.stdout)
        self.assertNotIn("world export", result.stdout)
        self.assertIn("SCUMMVERSE: could not start The Secret of Monkey Island", result.stdout)
        self.assertIn("SCUMMVERSE: Explore mode", result.stdout)
        self.assert_data_failure(result)
        config = self.config.read_text()
        self.assertNotIn("scummverse_story_playing", config)
        self.assertIn("scummverse_mode=explore", config)

    def test_story_playing_is_ignored_in_explore_mode(self):
        # (Explore mode is the mansion: a story left marked is not gone on with.)
        (self.root / "monkey").mkdir()
        self.config.write_text("[scummvm]\nscummverse_story_playing=scummverse-story-monkey\n\n"
                               "[scummverse-story-monkey]\nengineid=scumm\ngameid=monkey\n"
                               f"path={self.root / 'monkey'}\nscummverse_story=true\n")
        result = self.run_game()
        self.assertNotIn("going on with", result.stdout)
        self.assert_data_failure(result)
        self.assertNotIn("scummverse_story_playing", self.config.read_text())

    def test_story_mode_list(self):
        # Story mode with nothing to go on in: its list first. A story chosen
        # (here it cannot start: no data), the list again; a game whose story
        # needs files it lacks is not taken; then Explore mode, the mansion.
        (self.root / "monkey").mkdir()
        (self.root / "ft").mkdir()
        # (Both already set up for the worlds: the list is the first thing.)
        (self.root / "worlds").mkdir()
        for name in ("monkey", "ft"):
            (self.root / "worlds" / f"{name}-v{export_version(name)}.svx").write_bytes(b"")
        self.config.write_text("[scummvm]\nscummverse_mode=story\nscummverse_story_choices=monkey,ft\n")
        result = self.run_game()
        self.assertNotIn("world export", result.stdout)
        self.assertIn("SCUMMVERSE: Story mode: scummverse-story-monkey", result.stdout)
        self.assertIn("SCUMMVERSE: could not start The Secret of Monkey Island", result.stdout)
        self.assertNotIn("Story mode: scummverse-story-ft", result.stdout)
        self.assertIn("SCUMMVERSE: Explore mode", result.stdout)
        self.assert_data_failure(result)
        self.assertIn("scummverse_mode=explore", self.config.read_text())

    def test_story_playing_is_taken_at_any_start(self):
        # (The sandbox started instead: the mark is taken all the same, so a
        # game that stops the app is not opened at every start.)
        self.config.write_text("[scummvm]\nscummverse_story_playing=scummverse-story-monkey\n")
        result = self.run_game("scummverse:sandbox")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("scummverse_story_playing", self.config.read_text())

    def test_story_playing_without_its_folder_is_dropped(self):
        self.config.write_text("[scummvm]\nscummverse_mode=story\nscummverse_story_playing=scummverse-story-monkey\n\n"
                               "[scummverse-story-monkey]\nengineid=scumm\ngameid=monkey\npath=gone\nscummverse_story=true\n")
        result = self.run_game()
        self.assertNotIn("going on with", result.stdout)
        self.assert_data_failure(result)
        self.assertNotIn("scummverse_story_playing", self.config.read_text())

    # The phone's restore point (common/scummverse_restore.h): the file the
    # iPhone's backend writes as the app is put away, naming the target and
    # the autosave slot it saved; ScummVM's launcher would take it, Explore
    # mode's mansion takes it itself (here the test's own file, named by
    # scummverse_restore_point: the desktop has none). Taken once, as the app
    # starts: the file is let go (emptied) whatever it says.
    def restore_point(self, text, saves=(), extra=""):
        point = self.root / "scummvm.state"
        point.write_bytes(text if isinstance(text, bytes) else text.encode())
        (self.root / "saves").mkdir(exist_ok=True)
        for name in saves:
            (self.root / "saves" / name).write_bytes(b"not a real save")
        self.config.write_text(f"[scummvm]\nscummverse_restore_point={point}\n{extra}")
        return point

    def run_saved(self, *args):
        return self.run_game(f"--savepath={self.root / 'saves'}", *args)

    def test_restore_point_names_the_mansion(self):
        point = self.restore_point("[state]\nrestore_target=maniac\nrestore_slot=0\n", ("maniac.s00",))
        result = self.run_saved()
        self.assertIn("SCUMMVERSE: the mansion where it was when the app was put away (its slot 0)", result.stdout)
        self.assert_data_failure(result)
        self.assertEqual(point.read_bytes(), b"")
        # (Taken once: the next start is afresh.)
        again = self.run_saved()
        self.assertNotIn("restore point", again.stdout)
        self.assertNotIn("when the app was put away", again.stdout)
        self.assert_data_failure(again)

    def test_restore_point_needs_its_save(self):
        point = self.restore_point("[state]\nrestore_target=maniac\nrestore_slot=3\n", ("maniac.s00",))
        result = self.run_saved()
        self.assertIn("SCUMMVERSE: the phone's restore point names slot 3, not saved there", result.stdout)
        self.assertNotIn("when the app was put away", result.stdout)
        self.assert_data_failure(result)
        self.assertEqual(point.read_bytes(), b"")

    def test_restore_point_of_a_story_is_not_the_mansions(self):
        # (The app put away in a story: it goes on from its own newest save,
        # by its own rule; the mansion starts as it would.)
        point = self.restore_point("[state]\nrestore_target=scummverse-story-monkey\nrestore_slot=0\n",
                                   ("maniac.s00", "scummverse-story-monkey.s00"))
        result = self.run_saved()
        self.assertIn("SCUMMVERSE: the phone's restore point is scummverse-story-monkey's, not the mansion's", result.stdout)
        self.assertNotIn("when the app was put away", result.stdout)
        self.assert_data_failure(result)
        self.assertEqual(point.read_bytes(), b"")

    def test_restore_point_after_the_new_engine(self):
        # The app stopped while the new engine was open (0239's mark, and the
        # mansion's save for it): that save is newer than any restore point
        # naming the mansion (the backend writes none for the new engine).
        point = self.restore_point("[state]\nrestore_target=maniac\nrestore_slot=0\n", ("maniac.s00", "maniac.c100"),
                                   "scummverse_sandbox_open=true\n")
        result = self.run_saved()
        self.assertIn("SCUMMVERSE: the mansion where it was when the new engine was opened", result.stdout)
        self.assertIn("SCUMMVERSE: the phone's restore point set aside: the mansion goes on from a later save", result.stdout)
        self.assertNotIn("when the app was put away", result.stdout)
        self.assert_data_failure(result)
        self.assertEqual(point.read_bytes(), b"")
        self.assertNotIn("scummverse_sandbox_open", self.config.read_text())

    def test_restore_point_after_a_story_the_mansion_opened(self):
        # The app put away and stopped in a story the mansion opened (the
        # same mark, naming the story; the mansion's save for it): started
        # again, the mansion from that save; the story's point set aside.
        point = self.restore_point("[state]\nrestore_target=scummverse-story-monkey\nrestore_slot=0\n",
                                   ("maniac.s00", "maniac.c100", "scummverse-story-monkey.s00"),
                                   "scummverse_sandbox_open=scummverse-story-monkey\n")
        result = self.run_saved()
        self.assertIn("SCUMMVERSE: the mansion where it was when scummverse-story-monkey was opened", result.stdout)
        self.assertIn("SCUMMVERSE: the phone's restore point set aside: the mansion goes on from a later save", result.stdout)
        self.assertNotIn("the new engine was opened", result.stdout)
        self.assert_data_failure(result)
        self.assertEqual(point.read_bytes(), b"")
        self.assertNotIn("scummverse_sandbox_open", self.config.read_text())

    # The point taken at a start that stopped before the mansion started (its
    # exports, a story gone on in, Story mode's list): kept on disk, as that
    # start left it, until the mansion's first start decides on it (tried
    # once), then let go.
    def kept_point(self, target, slot, saves=(), file="", extra=""):
        return self.restore_point(file, saves, f"scummverse_restore_taken={target}\nscummverse_restore_taken_slot={slot}\n{extra}")

    def test_restore_point_kept_from_a_start_that_stopped(self):
        point = self.kept_point("maniac", "0", ("maniac.s00",))
        result = self.run_saved()
        self.assertIn("SCUMMVERSE: the phone's restore point, kept from a start that stopped first: maniac, slot 0", result.stdout)
        self.assertIn("SCUMMVERSE: the mansion where it was when the app was put away (its slot 0)", result.stdout)
        self.assert_data_failure(result)
        self.assertNotIn("scummverse_restore_taken", self.config.read_text())
        # (Tried once: the next start is afresh, even though that one failed.)
        again = self.run_saved()
        self.assertNotIn("restore point", again.stdout)
        self.assert_data_failure(again)
        self.assertEqual(point.read_bytes(), b"")

    def test_restore_point_kept_over_another_games(self):
        # (The mansion's kept point and one another game left since, the
        # mansion not played: the mansion's stands.)
        point = self.kept_point("maniac", "0", ("maniac.s00", "scummverse-story-monkey.s00"),
                                "[state]\nrestore_target=scummverse-story-monkey\nrestore_slot=0\n")
        result = self.run_saved()
        self.assertIn("SCUMMVERSE: the phone's restore point is scummverse-story-monkey's; the mansion's kept from before stands", result.stdout)
        self.assertIn("SCUMMVERSE: the mansion where it was when the app was put away (its slot 0)", result.stdout)
        self.assert_data_failure(result)
        self.assertEqual(point.read_bytes(), b"")
        self.assertNotIn("scummverse_restore_taken", self.config.read_text())

    def test_restore_point_kept_replaced_by_a_newer(self):
        point = self.kept_point("scummverse-story-monkey", "0", ("maniac.s00", "maniac.s01"),
                                "[state]\nrestore_target=maniac\nrestore_slot=1\n")
        result = self.run_saved()
        self.assertIn("SCUMMVERSE: the mansion where it was when the app was put away (its slot 1)", result.stdout)
        self.assert_data_failure(result)
        self.assertEqual(point.read_bytes(), b"")
        self.assertNotIn("scummverse_restore_taken", self.config.read_text())

    def test_restore_point_kept_after_the_mark(self):
        # (The mansion's save for a game it opened is newer: both let go.)
        self.kept_point("maniac", "0", ("maniac.s00", "maniac.c100"), extra="scummverse_sandbox_open=scummverse-story-monkey\n")
        result = self.run_saved()
        self.assertIn("SCUMMVERSE: the mansion where it was when scummverse-story-monkey was opened", result.stdout)
        self.assertIn("SCUMMVERSE: the phone's restore point set aside: the mansion goes on from a later save", result.stdout)
        self.assert_data_failure(result)
        self.assertNotIn("scummverse_restore_taken", self.config.read_text())
        self.assertNotIn("scummverse_sandbox_open", self.config.read_text())

    def test_damaged_kept_restore_point(self):
        for target, slot in (("maniac", "x"), ("man iac", "0"), ("maniac", "1000"), ("", "0")):
            with self.subTest(target=target, slot=slot):
                self.kept_point(target, slot, ("maniac.s00", "maniac.s01"))
                result = self.run_saved()
                self.assertIn("SCUMMVERSE: the phone's restore point kept from before is damaged; not used", result.stdout)
                self.assertNotIn("when the app was put away", result.stdout)
                self.assert_data_failure(result)
                self.assertNotIn("scummverse_restore_taken", self.config.read_text())

    def test_damaged_restore_point(self):
        # Cut short as it was written, a slot that is no number, a key outside
        # its section (ScummVM's own INI reader stops the app at that), a NUL
        # byte, far too long: not used, let go, the start as it would be.
        for text in (b"[state]\nrestore_target=maniac\nrestore_slot=1", b"[state]\nrestore_target=maniac\nrestore_slot=0x\n",
                     b"restore_target=maniac\n[state]\nrestore_target=maniac\nrestore_slot=0\n", b"[sta",
                     b"[state]\nrestore_target=man\0iac\nrestore_slot=0\n",
                     b"[state]\nrestore_target=maniac\nrestore_slot=0\n" + b"#" * 100000 + b"\n"):
            with self.subTest(text=text[:60]):
                point = self.restore_point(text, ("maniac.s00", "maniac.s01"))
                result = self.run_saved()
                self.assertIn("SCUMMVERSE: the phone's restore point is damaged; not used", result.stdout)
                self.assertNotIn("when the app was put away", result.stdout)
                self.assert_data_failure(result)
                self.assertEqual(point.read_bytes(), b"")
        # (A folder where the file would be: not read, left as it is.)
        point.unlink()
        point.mkdir()
        result = self.run_saved()
        self.assertNotIn("restore point", result.stdout)
        self.assert_data_failure(result)
        self.assertTrue(point.is_dir())

    def test_restore_point_is_the_mansions_only(self):
        # (The new engine started on its own: never taken there.)
        point = self.restore_point("[state]\nrestore_target=maniac\nrestore_slot=0\n", ("maniac.s00",))
        (self.root / "worlds").mkdir()
        result = self.run_saved("scummverse:sandbox")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("restore point", result.stdout)
        self.assertEqual(point.read_text(), "[state]\nrestore_target=maniac\nrestore_slot=0\n")

    def test_sandbox_without_places(self):
        (self.root / "worlds").mkdir()
        result = self.run_game("scummverse:sandbox")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("SCUMMVERSE: could not start the sandbox", result.stdout)

    def make_synthetic_place(self):
        worlds = self.root / "worlds"
        worlds.mkdir()
        w, h = 320, 144
        scene = b"SVW3" + struct.pack("<HHHBB", 33, w, h, 2, 0)
        scene += bytes(c for i in range(256) for c in (i, 255 - i, i // 2))
        scene += bytes((x // 8 + y // 8) % 200 + 20 for y in range(h) for x in range(w))
        for l, t, r, b in ((10, 100, 160, 140), (160, 100, 310, 140)):
            scene += struct.pack("<8h", l, t, r, t, r, b, l, b) + bytes(2)
        scene += struct.pack("<H", 0) + bytes((128, 255, 255, 255))
        (worlds / "monkey-33.svw").write_bytes(gzip.compress(scene))
        lead = b"SVC1" + struct.pack("<HH", 1, 2)
        lead += bytes(c for i in range(256) for c in (i, i, 255 - i))
        for direction, kind in ((2, 0), (1, 1)):
            lead += bytes((direction, kind, 0, 0)) + struct.pack("<hhHH", -10, -40, 20, 40)
            lead += bytes([30]) * 800 + bytes([0] * 20 + [1] * 780)
        (worlds / "monkey-c1.svc").write_bytes(lead)

    def assert_synthetic_walk(self, result):
        self.assertEqual(result.returncode, 0, result.stdout)
        # (The lead and, from 0201, the four custom characters who roam: in a
        # world of one place, all of them there.)
        self.assertIn("1 shown, 5 people, 1 walked across, 0 as near as they go, 0 skipped, 0 failed", result.stdout)
        self.assertIn("screen 1280x720", result.stdout)
        self.assertIn("SCUMMVERSE sandbox selftest PASS", result.stdout)

    def test_sandbox_synthetic_place(self):
        # A made-up place and lead (no game data): the sandbox shows it at
        # 1280x720 in true colour and the lead walks across.
        self.make_synthetic_place()
        self.config.write_text("[scummvm]\nscummverse_selftest=walk\nscummverse_screen=1280x720\n")
        self.assert_synthetic_walk(self.run_game("scummverse:sandbox"))

    def test_sandbox_damaged_settings(self):
        # Its settings as a file cut short as the app was stopped writing it
        # leaves them (not true or false, not a number, or a number out of
        # range): read as not kept, the defaults (wanderers out), and it
        # starts all the same. (ConfMan's own getBool and getInt end the app.)
        self.make_synthetic_place()
        self.config.write_text("[scummvm]\nscummverse_selftest=walk\nscummverse_screen=1280x720\n"
                               "scummverse_wanderers=fal\nscummverse_verbs=tr\nscummverse_tour_speed=fast\n"
                               "scummverse_sandbox_tour_place=\nscummverse_sandbox_van_place=99999999999\n"
                               "scummverse_sandbox_flashlight=of\nscummverse_sandbox_tram_parked=x7\n"
                               "scummverse_sandbox_van_x=-\nscummverse_sandbox_van_y=1e\n")
        self.assert_synthetic_walk(self.run_game("scummverse:sandbox"))

    def assert_edition_rejected(self, filename, header):
        # Synthetic detector signatures only, never copyrighted game fixtures.
        data = self.root / "maniac"
        data.mkdir()
        (data / filename).write_bytes(header + bytes(30))
        result = self.run_game()
        self.assert_data_failure(result)
        self.assertIn("requires one full original DOS V1 edition", result.stdout)

    def test_enhanced_v2_is_rejected(self):
        self.assert_edition_rejected("00.LFL", bytes([0xff, 0xfe]))

    def test_nes_v1_is_rejected(self):
        self.assert_edition_rejected("00.LFL", bytes([0xbc, 0xb9]))

    def test_dos_v1_demo_is_rejected(self):
        self.assert_edition_rejected("00.MAN", bytes([0xce, 0xf5]))


if __name__ == "__main__":
    if not BINARY.is_file():
        raise SystemExit(f"Build the null backend first; missing {BINARY}")
    unittest.main(verbosity=2)
