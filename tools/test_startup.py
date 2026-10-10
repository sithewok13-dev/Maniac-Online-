#!/usr/bin/env python3
"""Exercise the real null-backend executable, without copyrighted fixtures."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

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
        self.assertIn("SCUMMVERSE: could not start Maniac Mansion (C64)", result.stdout)
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
        self.assertIn("only Maniac Mansion (C64) is supported", result.stdout)

    def test_saved_launcher_preference_does_not_open_launcher(self):
        self.config.write_text("[scummvm]\ngui_return_to_launcher_at_exit=true\n")
        self.assert_data_failure(self.run_game())

    def test_saved_unrelated_target_is_rejected(self):
        self.config.write_text("[scummvm]\n\n[other]\nengineid=scumm\ngameid=monkey\npath=.\n")
        result = self.run_game("other")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("only Maniac Mansion (C64) is supported", result.stdout)


if __name__ == "__main__":
    if not BINARY.is_file():
        raise SystemExit(f"Build the null backend first; missing {BINARY}")
    unittest.main(verbosity=2)
