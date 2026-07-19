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

    def test_skill_preserves_metric_and_access_boundaries(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        source_policy = (SKILL / "references" / "source-policy.md").read_text(encoding="utf-8")
        schema = (SKILL / "references" / "data-schema.md").read_text(encoding="utf-8")
        report = (SKILL / "references" / "report-format.md").read_text(encoding="utf-8")
        self.assertIn("Never estimate a missing number", skill)
        self.assertIn("Never bypass Cloudflare", source_policy)
        self.assertIn("shipment_net_returns", schema)
        self.assertIn("retail_sale", schema)
        self.assertIn("estimated_sale", schema)
        self.assertIn("Do not place unlike units on one axis", report)

    def test_recent_filters_preserve_inventory_and_type_semantics(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "`앨범` or `recent albums` means chronological `studio_album`, `ep`, "
            "`single_album`, and `repackage` release groups.",
            skill,
        )
        self.assertIn(
            "`발매작` or `releases` means every default release type, including "
            "`digital_single`.",
            skill,
        )
        self.assertIn(
            "Never omit a qualifying release merely to improve metric comparability; "
            "retain it and show `데이터 없음` or `비교 불가`.",
            skill,
        )

    def test_numeric_tables_keep_provenance_and_unofficial_labels(self):
        report = (SKILL / "references" / "report-format.md").read_text(encoding="utf-8")
        source_policy = (SKILL / "references" / "source-policy.md").read_text(encoding="utf-8")
        self.assertIn(
            "Every numeric evidence row or table cell must expose source tier, source URL, "
            "market, period/window, `observed_at`, measurement type/unit, and confidence.",
            report,
        )
        self.assertIn("A separate paragraph does not satisfy this requirement.", report)
        self.assertIn("Kworb", source_policy)
        self.assertIn("source tier `C`", source_policy)
        self.assertIn("non-official", source_policy)
        self.assertIn("never present it as YouTube Analytics", source_policy)

    def test_track_and_promotional_content_require_a_separate_release_group(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        source_policy = (SKILL / "references" / "source-policy.md").read_text(encoding="utf-8")
        required_rule = (
            "Do not classify album tracks, track videos, or pre-release promotional content "
            "as standalone singles unless an official catalog or source shows a separate release group."
        )
        self.assertIn(required_rule, skill)
        self.assertIn(required_rule, source_policy)
        self.assertIn("Preserve uncertain classification as a warning.", skill)


if __name__ == "__main__":
    unittest.main()
