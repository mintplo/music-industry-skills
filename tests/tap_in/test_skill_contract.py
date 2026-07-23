import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "tap-in"
VALIDATOR = SKILL / "scripts" / "validate_dataset.py"


class SocialReactionSkillContractTests(unittest.TestCase):
    def test_skill_is_model_invoked_and_reusable(self):
        self.assertTrue((SKILL / "SKILL.md").is_file())
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]

        self.assertTrue(text.startswith("---\nname: tap-in\n"))
        self.assertIn("Use when", frontmatter)
        self.assertIn("YouTube", frontmatter)
        self.assertIn("Instagram", frontmatter)
        self.assertIn("TikTok", frontmatter)
        self.assertNotIn("disable-model-invocation", text)
        self.assertLessEqual(len(text.splitlines()), 180)

    def test_openai_metadata_uses_tap_in_display_name(self):
        metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn('display_name: "Tap In"', metadata)

    def test_skill_defines_stable_four_file_contract(self):
        self.assertTrue((SKILL / "SKILL.md").is_file())
        self.assertTrue((SKILL / "references" / "data-contract.md").is_file())
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        contract = (SKILL / "references" / "data-contract.md").read_text(
            encoding="utf-8"
        )

        for filename in (
            "collection-manifest.json",
            "posts.jsonl",
            "comments.jsonl",
            "reaction-summary.json",
        ):
            self.assertIn(filename, text)
            self.assertIn(filename, contract)
        self.assertIn("tap-in/v1", contract)
        self.assertIn('"hate":0', contract)
        self.assertIn('"other":0', contract)
        self.assertIn("supported", contract)
        self.assertIn("access-dependent", contract)
        self.assertIn("unavailable", contract)
        self.assertIn("partial", contract)
        self.assertIn("coding_status", contract)

    def test_platform_recipes_and_model_coding_contract_exist(self):
        required = [
            SKILL / "agents" / "openai.yaml",
            SKILL / "recipes" / "youtube.md",
            SKILL / "recipes" / "instagram.md",
            SKILL / "recipes" / "tiktok.md",
            SKILL / "references" / "comment-coding.md",
        ]
        self.assertEqual([], [str(path) for path in required if not path.is_file()])

        coding = required[-1].read_text(encoding="utf-8")
        for label in (
            "substantive",
            "affect_only",
            "off_topic",
            "duplicate",
            "promotional_spam",
            "suspected_automation",
            "positive",
            "negative",
            "mixed",
            "neutral",
            "unclear",
        ):
            self.assertIn(label, coding)
        self.assertIn("negative substantive", coding.casefold())
        self.assertIn("emoji", coding.casefold())

    def test_sampling_contract_is_per_post_and_carries_limitations(self):
        self.assertTrue((SKILL / "SKILL.md").is_file())
        for name in ("youtube.md", "instagram.md", "tiktok.md"):
            self.assertTrue((SKILL / "recipes" / name).is_file())
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        combined = "\n".join(
            (SKILL / "recipes" / name).read_text(encoding="utf-8")
            for name in ("youtube.md", "instagram.md", "tiktok.md")
        )

        self.assertIn("100 comments per post", text.casefold())
        self.assertIn("5 posts total", text.casefold())
        self.assertIn("30", text)
        self.assertIn(
            "<skill-directory>/scripts/validate_dataset.py",
            text,
        )
        self.assertIn("convenience sample", combined.casefold())
        self.assertIn("do not reset", combined.casefold())
        self.assertIn("observed_at", combined)
        self.assertIn("missing_reason", combined)

    def test_youtube_api_is_first_path_and_fallback_requires_explicit_consent(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8").casefold()
        recipe = (SKILL / "recipes" / "youtube.md").read_text(
            encoding="utf-8"
        ).casefold()
        provider = (
            ROOT / "skills" / "dig-music" / "providers" / "youtube.md"
        ).read_text(encoding="utf-8").casefold()

        for text in (skill, recipe, provider):
            self.assertIn("mandatory first path", text)
            self.assertIn("only after the user explicitly declines", text)
            self.assertRegex(
                text,
                r"explicitly authorizes fallback (after|following) an api failure",
            )
            self.assertIn("missing credentials", text)
            self.assertIn("urgency", text)
        self.assertLess(
            recipe.index("## api-first routing"),
            recipe.index("## browser fallback"),
        )

    def test_dig_music_declares_required_subskill(self):
        text = (ROOT / "skills" / "dig-music" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("**REQUIRED SUB-SKILL:**", text)
        self.assertIn("tap-in", text)

    def test_readme_installs_and_documents_both_skills(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "--skill dig-music --skill tap-in -g",
            readme,
        )
        self.assertIn("$tap-in", readme)
        self.assertIn("tap-in/", readme)


class DatasetValidatorTests(unittest.TestCase):
    def write_valid_bundle(self, root):
        manifest = {
            "contract_version": "tap-in/v1",
            "run_id": "run-1",
            "subject": {"name": "Example Artist"},
            "status": "supported",
            "coverage": "partial",
            "started_at": "2026-07-21T00:00:00Z",
            "completed_at": "2026-07-21T00:01:00Z",
            "platforms": [
                {
                    "platform": "instagram",
                    "status": "supported",
                    "coverage": "partial",
                    "collection_method": "public_browser",
                    "limitations": ["Visible comments only"],
                }
            ],
            "collection_frames": [
                {
                    "frame_id": "instagram:post-1",
                    "platform": "instagram",
                    "post_id": "post-1",
                    "requested_url": "https://www.instagram.com/p/example/",
                    "status": "supported",
                    "coverage": "partial",
                    "sampling_method": "platform_default_visible_order",
                    "target_comments": 100,
                    "achieved_top_level_comments": 1,
                    "achieved_reply_comments": 0,
                    "stop_reason": "fixture_cap",
                    "observed_at": "2026-07-21T00:00:40Z",
                }
            ],
            "limitations": ["Convenience sample"],
        }
        post = {
            "contract_version": "tap-in/v1",
            "run_id": "run-1",
            "platform": "instagram",
            "post_id": "post-1",
            "canonical_url": "https://www.instagram.com/p/example/",
            "published_at": None,
            "observed_at": "2026-07-21T00:00:30Z",
            "collection_method": "public_browser",
            "content_type": "reel",
            "text": "Example caption",
            "metrics": {
                "views": {
                    "value": None,
                    "display_value": None,
                    "is_exact": None,
                    "observed_at": "2026-07-21T00:00:30Z",
                    "availability": "unavailable",
                    "source_url": "https://www.instagram.com/p/example/",
                    "missing_reason": "not_publicly_displayed",
                }
            },
        }
        comment = {
            "contract_version": "tap-in/v1",
            "run_id": "run-1",
            "platform": "instagram",
            "post_id": "post-1",
            "comment_id": "comment-1",
            "parent_comment_id": None,
            "text": "I love this song",
            "published_at": None,
            "observed_at": "2026-07-21T00:00:40Z",
            "sample_rank": 1,
            "sampling_method": "platform_default_visible_order",
            "source_url": "https://www.instagram.com/p/example/",
            "coding_status": "complete",
            "labels": {
                "analysis_value": "affect_only",
                "sentiment": "positive",
                "toxicity": [],
                "confidence": "high",
            },
        }
        summary = {
            "contract_version": "tap-in/v1",
            "run_id": "run-1",
            "counts": {"collected": 1, "usable": 1, "excluded": 0},
            "sentiment": {
                "positive": 1,
                "negative": 0,
                "mixed": 0,
                "neutral": 0,
                "unclear": 0,
            },
            "analysis_value": {
                "substantive": 0,
                "affect_only": 1,
                "off_topic": 0,
                "duplicate": 0,
                "promotional_spam": 0,
                "suspected_automation": 0,
                "unclear": 0,
            },
            "toxicity": {
                "abuse": 0,
                "hate": 0,
                "threat": 0,
                "sexual_harassment": 0,
                "privacy_exposure": 0,
                "self_harm": 0,
                "other": 0,
            },
            "limitations": ["Convenience sample"],
        }
        (root / "collection-manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        (root / "posts.jsonl").write_text(
            json.dumps(post) + "\n", encoding="utf-8"
        )
        (root / "comments.jsonl").write_text(
            json.dumps(comment) + "\n", encoding="utf-8"
        )
        (root / "reaction-summary.json").write_text(
            json.dumps(summary), encoding="utf-8"
        )

    def run_validator(self, root):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(root)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

    def test_validator_accepts_valid_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_bundle(root)

            result = self.run_validator(root)

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("valid", result.stdout.casefold())

    def test_validator_rejects_ambiguous_missing_metric(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_bundle(root)
            post_path = root / "posts.jsonl"
            post = json.loads(post_path.read_text(encoding="utf-8"))
            del post["metrics"]["views"]["missing_reason"]
            post_path.write_text(json.dumps(post) + "\n", encoding="utf-8")

            result = self.run_validator(root)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("missing_reason", result.stderr)

    def test_validator_reconciles_all_summary_breakdowns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_bundle(root)
            path = root / "reaction-summary.json"
            summary = json.loads(path.read_text(encoding="utf-8"))
            summary["sentiment"]["positive"] = 999
            path.write_text(json.dumps(summary), encoding="utf-8")

            result = self.run_validator(root)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("sentiment.positive", result.stderr)

    def test_validator_requires_and_reconciles_per_post_frames(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_bundle(root)
            path = root / "collection-manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["collection_frames"][0]["achieved_top_level_comments"] = 2
            path.write_text(json.dumps(manifest), encoding="utf-8")

            result = self.run_validator(root)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("achieved_top_level_comments", result.stderr)

    def test_validator_rejects_missing_collection_frames(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_bundle(root)
            path = root / "collection-manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            del manifest["collection_frames"]
            path.write_text(json.dumps(manifest), encoding="utf-8")

            result = self.run_validator(root)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("collection_frames", result.stderr)

    def test_validator_rejects_empty_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_bundle(root)
            post_path = root / "posts.jsonl"
            post = json.loads(post_path.read_text(encoding="utf-8"))
            post["metrics"] = {}
            post_path.write_text(json.dumps(post) + "\n", encoding="utf-8")

            result = self.run_validator(root)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("at least one metric", result.stderr)

    def test_validator_rejects_supported_status_without_observations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_bundle(root)
            (root / "posts.jsonl").write_text("", encoding="utf-8")
            (root / "comments.jsonl").write_text("", encoding="utf-8")
            manifest_path = root / "collection-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            frame = manifest["collection_frames"][0]
            frame["post_id"] = None
            frame["status"] = "access-dependent"
            frame["achieved_top_level_comments"] = 0
            frame["stop_reason"] = "login_required"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            summary_path = root / "reaction-summary.json"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            summary["counts"] = {"collected": 0, "usable": 0, "excluded": 0}
            summary["sentiment"] = {name: 0 for name in summary["sentiment"]}
            summary["analysis_value"] = {
                name: 0 for name in summary["analysis_value"]
            }
            summary["toxicity"] = {name: 0 for name in summary["toxicity"]}
            summary_path.write_text(json.dumps(summary), encoding="utf-8")

            result = self.run_validator(root)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("supported", result.stderr)
            self.assertIn("observation", result.stderr)

    def test_validator_reports_malformed_labels_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_bundle(root)
            path = root / "comments.jsonl"
            comment = json.loads(path.read_text(encoding="utf-8"))
            comment["labels"] = "malformed"
            path.write_text(json.dumps(comment) + "\n", encoding="utf-8")

            result = self.run_validator(root)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("labels must be an object", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_validator_reports_nested_malformed_labels_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_bundle(root)
            path = root / "comments.jsonl"
            comment = json.loads(path.read_text(encoding="utf-8"))
            comment["labels"]["analysis_value"] = {}
            comment["labels"]["toxicity"] = [{}]
            path.write_text(json.dumps(comment) + "\n", encoding="utf-8")

            result = self.run_validator(root)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("invalid analysis_value", result.stderr)
            self.assertIn("invalid toxicity", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_validator_reports_nested_malformed_sentiment_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_bundle(root)
            path = root / "comments.jsonl"
            comment = json.loads(path.read_text(encoding="utf-8"))
            comment["labels"]["sentiment"] = {}
            path.write_text(json.dumps(comment) + "\n", encoding="utf-8")

            result = self.run_validator(root)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("invalid sentiment", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_validator_rejects_pending_comment_with_usable_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_bundle(root)
            path = root / "comments.jsonl"
            comment = json.loads(path.read_text(encoding="utf-8"))
            comment["coding_status"] = "pending"
            path.write_text(json.dumps(comment) + "\n", encoding="utf-8")

            result = self.run_validator(root)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("pending comment requires provisional labels", result.stderr)

    def test_validator_rejects_raw_commenter_identity_fields(self):
        prohibited = {
            "authorDisplayName": "Example User",
            "authorChannelId": "channel-1",
            "authorProfileImageUrl": "https://example.com/avatar.jpg",
            "profile_url": "https://example.com/user",
        }
        for field, value in prohibited.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.write_valid_bundle(root)
                path = root / "comments.jsonl"
                comment = json.loads(path.read_text(encoding="utf-8"))
                comment[field] = value
                path.write_text(json.dumps(comment) + "\n", encoding="utf-8")

                result = self.run_validator(root)

                self.assertNotEqual(0, result.returncode)
                self.assertIn("raw commenter identity/profile field", result.stderr)

    def test_validator_enforces_metric_exactness_states(self):
        cases = (
            (
                {"value": None, "display_value": "1.2M", "is_exact": None, "availability": "available", "missing_reason": "exact_value_not_public"},
                "display-only metric requires is_exact false",
            ),
            (
                {"value": 1200, "display_value": "1,200", "is_exact": False, "availability": "available"},
                "numeric value requires is_exact true",
            ),
            (
                {"value": None, "display_value": None, "is_exact": False, "availability": "unavailable", "missing_reason": "not_publicly_displayed"},
                "unavailable metric requires is_exact null",
            ),
        )
        for updates, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.write_valid_bundle(root)
                post_path = root / "posts.jsonl"
                post = json.loads(post_path.read_text(encoding="utf-8"))
                metric = post["metrics"]["views"]
                metric.clear()
                metric.update(
                    {
                        "observed_at": "2026-07-21T00:00:30Z",
                        "source_url": "https://www.instagram.com/p/example/",
                        **updates,
                    }
                )
                post_path.write_text(json.dumps(post) + "\n", encoding="utf-8")

                result = self.run_validator(root)

                self.assertNotEqual(0, result.returncode)
                self.assertIn(message, result.stderr)

    def test_validator_enforces_utc_metric_provenance_and_availability(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_bundle(root)
            post_path = root / "posts.jsonl"
            post = json.loads(post_path.read_text(encoding="utf-8"))
            metric = post["metrics"]["views"]
            metric["observed_at"] = "2026-07-21T09:00:30+09:00"
            metric["availability"] = "mystery"
            del metric["source_url"]
            post_path.write_text(json.dumps(post) + "\n", encoding="utf-8")

            result = self.run_validator(root)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("UTC", result.stderr)
            self.assertIn("availability", result.stderr)
            self.assertIn("source_url", result.stderr)


if __name__ == "__main__":
    unittest.main()
