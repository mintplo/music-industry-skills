from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "music" / "research-music"


class ResearchMusicSkillContractTests(unittest.TestCase):
    def test_core_skill_is_model_invoked_and_document_first(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: research-music\n"))
        self.assertIn("source stack", text.casefold())
        self.assertIn("providers/CATALOG.md", text)
        self.assertIn("references/evidence-policy.md", text)
        self.assertIn("references/entity-resolution.md", text)
        self.assertIn("references/metric-compatibility.md", text)
        self.assertNotIn("disable-model-invocation", text)
        self.assertNotIn("Provider Registry", text)
        self.assertNotIn("complete discography", text.casefold())
        self.assertLessEqual(len(text.splitlines()), 180)

    def test_metadata_and_minimum_provider_cards_exist(self):
        required = [
            SKILL / "agents" / "openai.yaml",
            SKILL / "providers" / "CATALOG.md",
            SKILL / "providers" / "musicbrainz.md",
            SKILL / "providers" / "web-search.md",
        ]
        self.assertEqual([], [str(path) for path in required if not path.is_file()])
        metadata = required[0].read_text(encoding="utf-8")
        self.assertIn('$research-music', metadata)
        self.assertNotIn("allow_implicit_invocation: false", metadata)

    def test_common_steps_end_on_question_requirements_not_a_template(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Every requested branch", text)
        self.assertIn("supported, unavailable, or access-dependent", text)
        self.assertIn("Do not add sections the user did not ask for", text)


if __name__ == "__main__":
    unittest.main()
