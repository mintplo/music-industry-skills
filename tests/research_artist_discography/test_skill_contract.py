from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "research-artist-discography"


class SkillContractTests(unittest.TestCase):
    def test_required_files_and_frontmatter_exist(self):
        required = [
            SKILL / "SKILL.md",
            SKILL / "agents" / "openai.yaml",
            SKILL / "references" / "source-policy.md",
            SKILL / "references" / "data-schema.md",
            SKILL / "references" / "report-format.md",
        ]
        self.assertEqual([], [str(path) for path in required if not path.is_file()])

        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: research-artist-discography\n"))
        self.assertIn("아티스트 이름", text)
        self.assertIn("전체 디스코그래피", text)
        self.assertIn("references/source-policy.md", text)
        self.assertIn("references/data-schema.md", text)
        self.assertIn("references/report-format.md", text)
        self.assertIn(
            "If `scripts/collect_discography_data.py` exists, use it", text
        )
        self.assertNotIn(
            "Use `scripts/collect_discography_data.py` when", text
        )
        self.assertNotRegex(text, r"\b(T[B]D|T[O]DO|FIX[M]E)\b")
        self.assertLessEqual(len(text.splitlines()), 500)

    def test_ui_prompt_names_the_skill(self):
        text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('$research-artist-discography', text)


if __name__ == "__main__":
    unittest.main()
