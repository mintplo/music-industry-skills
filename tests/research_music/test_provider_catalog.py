from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PROVIDERS = ROOT / "skills" / "music" / "research-music" / "providers"
EXPECTED = {
    "musicbrainz.md", "wikidata.md", "spotify.md", "apple-music.md",
    "youtube.md", "circle-chart.md", "oricon.md", "web-search.md",
    "web-crawling.md",
}
HEADINGS = {
    "## Capabilities", "## Use when", "## Do not use for", "## Access",
    "## Inputs and outputs", "## Evidence", "## Limits and terms",
    "## Fallbacks", "## Verification",
}


class ProviderCatalogTests(unittest.TestCase):
    def test_all_initial_provider_cards_exist_and_are_reachable(self):
        catalog = (PROVIDERS / "CATALOG.md").read_text(encoding="utf-8")
        actual = {path.name for path in PROVIDERS.glob("*.md")} - {"CATALOG.md"}
        self.assertEqual(EXPECTED, actual)
        for name in EXPECTED:
            self.assertIn(f"({name})", catalog)

    def test_every_card_uses_the_same_information_hierarchy(self):
        for name in EXPECTED:
            text = (PROVIDERS / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertTrue(text.startswith("# "))
                self.assertTrue(HEADINGS.issubset(set(text.splitlines())))
                self.assertIn("Last verified: 2026-07-19", text)
                self.assertRegex(text, r"https://")
                self.assertNotRegex(text, r"\b(T[B]D|T[O]DO|FIX[M]E)\b")


if __name__ == "__main__":
    unittest.main()
