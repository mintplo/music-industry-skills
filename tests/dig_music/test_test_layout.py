from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests"


class TestLayoutTests(unittest.TestCase):
    def test_active_skill_tests_use_current_skill_names(self):
        packages = {
            path.name
            for path in TESTS.iterdir()
            if path.is_dir() and (path / "__init__.py").is_file()
        }

        self.assertEqual({"dig_music", "tap_in"}, packages)
        self.assertFalse((TESTS / "research_music_discography").exists())
