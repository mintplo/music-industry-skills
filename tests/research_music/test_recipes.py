from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "music" / "research-music"
RECIPES = {
    "artist-and-album.md": "artist, release, album, song, track-list, or discography",
    "release-campaign.md": "rollout, teaser, promotion, media, or comeback-campaign",
    "artist-comparison.md": "artist or release comparisons",
    "market-trend.md": "genre, platform, country, audience, or market-pattern",
}


class RecipeContractTests(unittest.TestCase):
    def test_every_branch_has_a_context_pointer_and_recipe(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for name, trigger in RECIPES.items():
            self.assertTrue((SKILL / "recipes" / name).is_file())
            self.assertIn(trigger, skill)
            self.assertIn(f"recipes/{name}", skill)

    def test_recipes_compose_source_stacks_without_fixed_outputs(self):
        for name in RECIPES:
            text = (SKILL / "recipes" / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertIn("## Source stack", text)
                self.assertIn("## Completion criterion", text)
                self.assertNotIn("must always return", text.casefold())
                self.assertNotIn("Provider Registry", text)

    def test_simple_single_fact_requests_use_common_steps_without_a_recipe(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        artist_and_album = (SKILL / "recipes" / "artist-and-album.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "For a simple or single-fact request, use the common steps directly; do not load a recipe.",
            skill,
        )
        self.assertIn(
            "Do not load this recipe for a simple or single-fact request.",
            artist_and_album,
        )

    def test_recipes_keep_evidence_guards_without_mechanical_output_protocols(self):
        comparison = (SKILL / "recipes" / "artist-comparison.md").read_text(
            encoding="utf-8"
        )
        campaign = (SKILL / "recipes" / "release-campaign.md").read_text(
            encoding="utf-8"
        )
        trend = (SKILL / "recipes" / "market-trend.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Never award a winner from unmatched evidence", comparison)
        self.assertIn("denominator", comparison)
        self.assertNotIn("full adjacent field set", comparison)
        self.assertIn("claim-specific", campaign)
        self.assertNotIn("sweep every retained dated timeline asset", campaign)
        self.assertNotIn("genuinely distinct replacement", campaign)
        self.assertIn("bounded", trend)
        self.assertIn("sampling limits", trend)
        self.assertNotIn("`Candidate pattern:`", trend)
        self.assertNotIn("compound candidate", trend)
        self.assertNotIn("name both provider families and their roles", trend)


if __name__ == "__main__":
    unittest.main()
