from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "dig-music"


class SpotifyHandshakeTests(unittest.TestCase):
    def test_skill_offers_spotify_only_when_useful_and_keeps_fallbacks_open(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        provider = (SKILL / "providers" / "spotify.md").read_text(encoding="utf-8")
        combined = f"{skill}\n{provider}"

        for expected in (
            "only when it materially helps",
            "spotify_api.py check",
            "ask whether the user wants to connect",
            "spotify_api.py configure --gui",
            "Never ask the user to paste",
            "continue with the documented fallbacks",
        ):
            self.assertIn(expected, combined)


if __name__ == "__main__":
    unittest.main()
