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

    def test_output_recipe_requires_one_itemized_master_inventory_and_recent_ledger(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        report = (SKILL / "references" / "report-format.md").read_text(encoding="utf-8")
        self.assertIn("Create one complete master inventory before analysis.", skill)
        self.assertIn(
            "Use exactly one canonical row per discovered release group, including excluded "
            "and uncertain releases.",
            skill,
        )
        self.assertIn(
            "Every master-inventory row must include first-release date, normalized type, "
            "role/status, and selection eligibility.",
            report,
        )
        self.assertIn(
            "A category summary cannot replace individually itemized excluded or uncertain rows, "
            "and those rows must not be labeled default-eligible.",
            report,
        )
        self.assertIn(
            "For a latest-N or recent-N selection request, show a recent-N candidate ledger "
            "after applying the documented filters.",
            skill,
        )
        self.assertIn(
            "Recent-N candidate ledger only for a latest-N or recent-N selection request",
            report,
        )
        self.assertIn(
            "After building the master inventory, apply explicit role, type, period, and "
            "album filters. Sort the remaining considered releases by normalized first-release "
            "date descending, with unknown dates last. Then mark every considered release "
            "`eligible`, `excluded`, or `uncertain` with its reason and select exactly the "
            "first N eligible rows.",
            report,
        )
        self.assertIn(
            "An official standalone `digital_single` remains eligible unless the "
            "documented default-type or role rules exclude it.",
            report,
        )
        self.assertIn("Never substitute a lower candidate because data is unavailable.", report)

    def test_output_recipe_requires_evidence_ids_and_metric_visualization_decisions(self):
        report = (SKILL / "references" / "report-format.md").read_text(encoding="utf-8")
        self.assertIn("Create a timeline for release history.", report)
        self.assertIn(
            "Assign a stable evidence ID to every complete numeric evidence row.", report
        )
        self.assertIn(
            "Cite that evidence ID whenever later prose or a table repeats a performance "
            "number; otherwise keep the later claim qualitative.",
            report,
        )
        self.assertIn(
            "Use the evidence ID instead of duplicating the complete provenance fields when "
            "the later claim maps to that row.",
            report,
        )
        self.assertIn(
            "For every metric family used in comparison, create its comparable chart when "
            "comparable numeric observations exist.",
            report,
        )
        self.assertIn(
            "When omitting a chart, state its concrete insufficiency or omission rationale "
            "adjacent to that metric family.",
            report,
        )
        self.assertIn("A prose comparison is not a substitute for a required chart.", report)

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

    def test_skill_requires_a_pre_final_audit_of_every_performance_number(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        report = (SKILL / "references" / "report-format.md").read_text(encoding="utf-8")
        self.assertIn("Before finalizing, run a mandatory numeric audit.", skill)
        self.assertIn(
            "Treat quantified certification labels as performance numbers in the mandatory "
            "audit.",
            skill,
        )
        self.assertIn(
            "Scan every performance number and quantified performance claim in prose and "
            "tables, including a number cited only to dismiss it.",
            report,
        )
        self.assertIn(
            "Treat quantified certifications and numeric labels—including multipliers, levels, "
            "and thresholds such as `3× Platinum`, ranks, percentages, and K/M abbreviations—as "
            "performance numbers.",
            report,
        )
        self.assertIn(
            "Require every such mention, including one in limitation or reference-only prose, "
            "to cite a complete evidence row by its evidence ID.",
            report,
        )
        self.assertIn(
            "If a quantified certification multiplier, level, threshold, or numeric label lacks "
            "a complete evidence ID, remove the entire quantified certification or numeric label. "
            "To retain the underlying claim, use a genuinely qualitative statement such as "
            "`a certification is reported` with a normal adjacent source citation.",
            report,
        )
        self.assertIn(
            "Map each later performance claim by evidence ID to one complete evidence row.",
            report,
        )
        self.assertIn(
            "If no complete mapping exists, remove the number or state the claim "
            "qualitatively without it.",
            report,
        )
        self.assertIn(
            "Release dates and catalog track counts may follow catalog citation rules; "
            "this exception never applies to performance claims.",
            report,
        )

    def test_excluded_roles_take_precedence_over_default_release_forms(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        source_policy = (SKILL / "references" / "source-policy.md").read_text(encoding="utf-8")
        precedence = (
            "When a release has both a default form and an excluded role, apply excluded-role "
            "precedence in this order: `member_solo`, `feature`, `ost`, `live_album`, "
            "`compilation`, `remix_album`."
        )
        self.assertIn(precedence, skill)
        self.assertIn(precedence, source_policy)
        self.assertIn(
            "Exclude it from default recent-N analysis and preserve it separately.", skill
        )
        self.assertIn(
            "If sources do not resolve the classification, mark it `uncertain` and do not "
            "place it in direct recent-N comparison until clarified.",
            skill,
        )

    def test_concept_and_promotion_facts_require_adjacent_direct_citations(self):
        report = (SKILL / "references" / "report-format.md").read_text(encoding="utf-8")
        source_policy = (SKILL / "references" / "source-policy.md").read_text(encoding="utf-8")
        required_rule = (
            "Give every factual concept or promotion claim an adjacent direct citation in "
            "the same bullet or table cell."
        )
        self.assertIn(required_rule, report)
        self.assertIn(required_rule, source_policy)
        self.assertIn(
            "A bibliography or links later in the report do not satisfy this requirement.",
            report,
        )
        self.assertIn(
            "Apply this rule to factual premises in interpretation, change, and "
            "marketing-implications sections.",
            report,
        )
        self.assertIn(
            "The `interpretation` label exempts only the analytical inference, not embedded "
            "factual premises.",
            report,
        )
        self.assertIn(
            "Repeat the direct citation beside each factual premise, or state the inference "
            "without restating unlinked facts.",
            report,
        )
        self.assertIn("Keep interpretations separately labeled.", report)


if __name__ == "__main__":
    unittest.main()
