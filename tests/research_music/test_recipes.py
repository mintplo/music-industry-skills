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


if __name__ == "__main__":
    unittest.main()
