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
                self.assertRegex(text, r"Last verified: 20\d{2}-\d{2}-\d{2}")
                self.assertRegex(text, r"https://")
                self.assertNotRegex(text, r"\b(T[B]D|T[O]DO|FIX[M]E)\b")

    def test_spotify_access_records_the_documented_premium_prerequisite(self):
        text = (PROVIDERS / "spotify.md").read_text(encoding="utf-8")
        self.assertIn("Spotify Premium account", text)
        self.assertIn("access token", text)

    def test_youtube_access_requires_api_key_or_oauth_for_public_data(self):
        text = (PROVIDERS / "youtube.md").read_text(encoding="utf-8")
        self.assertIn(
            "Every Data API request requires an API key or OAuth 2.0 token.",
            text,
        )
        self.assertIn("API-key access is limited to public data.", text)
        self.assertNotIn("unauthenticated-public access", text)


if __name__ == "__main__":
    unittest.main()
