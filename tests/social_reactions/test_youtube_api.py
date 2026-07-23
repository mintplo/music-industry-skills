import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "tap-in"
SCRIPT = SKILL / "scripts" / "youtube_api.py"
VALIDATOR = SKILL / "scripts" / "validate_dataset.py"
README = ROOT / "README.md"
YOUTUBE_RECIPE = SKILL / "recipes" / "youtube.md"
DIG_MUSIC_YOUTUBE = ROOT / "skills" / "dig-music" / "providers" / "youtube.md"
TEST_KEY = "AIza-test-key-that-is-long-enough-for-tests"


class ScriptedTransport:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, resource, params):
        self.calls.append((resource, dict(params)))
        key = (resource, params.get("pageToken"), params.get("parentId"))
        response = self.responses[key]
        if isinstance(response, Exception):
            raise response
        return copy.deepcopy(response)


class YouTubeApiTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), "youtube_api.py must exist")
        spec = importlib.util.spec_from_file_location("youtube_api", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixed_now(self):
        return datetime(2026, 7, 21, 3, 0, 0, tzinfo=timezone.utc)

    def video_response(self):
        return {
            "items": [
                {
                    "id": "video-1",
                    "snippet": {
                        "title": "Example MV",
                        "description": "Example description",
                        "publishedAt": "2026-07-20T00:00:00Z",
                        "channelId": "channel-1",
                        "channelTitle": "Example Artist",
                    },
                    "statistics": {
                        "viewCount": "1234",
                        "likeCount": "120",
                        "commentCount": "4",
                    },
                }
            ]
        }

    def top_comment(self, comment_id, text, reply_count=0):
        return {
            "id": "thread-{}".format(comment_id),
            "snippet": {
                "totalReplyCount": reply_count,
                "topLevelComment": {
                    "id": comment_id,
                    "snippet": {
                        "textOriginal": text,
                        "publishedAt": "2026-07-20T01:00:00Z",
                        "updatedAt": "2026-07-20T01:00:00Z",
                        "likeCount": 3,
                        "authorDisplayName": "must-not-be-stored",
                        "authorProfileImageUrl": "https://example.com/private.jpg",
                    },
                },
            },
        }

    def reply(self, comment_id, parent_id, text):
        return {
            "id": comment_id,
            "snippet": {
                "parentId": parent_id,
                "textOriginal": text,
                "publishedAt": "2026-07-20T02:00:00Z",
                "updatedAt": "2026-07-20T02:00:00Z",
                "likeCount": 1,
                "authorDisplayName": "must-not-be-stored",
            },
        }

    def full_responses(self):
        return {
            ("videos", None, None): self.video_response(),
            ("commentThreads", None, None): {
                "items": [self.top_comment("top-1", "Great chorus", reply_count=2)],
                "nextPageToken": "thread-page-2",
            },
            ("comments", None, "top-1"): {
                "items": [self.reply("reply-1", "top-1", "Same")],
                "nextPageToken": "reply-page-2",
            },
            ("comments", "reply-page-2", "top-1"): {
                "items": [self.reply("reply-2", "top-1", "Agreed")],
            },
            ("commentThreads", "thread-page-2", None): {
                "items": [self.top_comment("top-2", "Mix is muddy")],
            },
        }

    def collect(self, module, root, responses=None, **kwargs):
        transport = ScriptedTransport(responses or self.full_responses())
        client = module.YouTubeApi(
            TEST_KEY,
            transport=transport,
            now=self.fixed_now,
        )
        result = module.collect_to_directory(
            client,
            ["video-1"],
            root,
            subject="Example Artist",
            run_id="youtube-run-1",
            **kwargs
        )
        return result, transport

    def validate_bundle(self, root):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(root)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

    def test_cli_exposes_secure_workflow_and_collection_options(self):
        self.load_module()
        top = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            text=True,
            capture_output=True,
        )
        configure = subprocess.run(
            [sys.executable, str(SCRIPT), "configure", "--help"],
            text=True,
            capture_output=True,
        )
        collect = subprocess.run(
            [sys.executable, str(SCRIPT), "collect", "--help"],
            text=True,
            capture_output=True,
        )

        self.assertEqual(0, top.returncode, top.stderr)
        for command in ("configure", "check", "collect"):
            self.assertIn(command, top.stdout)
        self.assertIn("--gui", configure.stdout)
        for option in (
            "--video-id",
            "--output",
            "--subject",
            "--top-level-only",
            "--max-comments",
            "--overwrite",
        ):
            self.assertIn(option, collect.stdout)

    def test_skill_documents_the_executable_youtube_workflow(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        recipe = YOUTUBE_RECIPE.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")
        provider = DIG_MUSIC_YOUTUBE.read_text(encoding="utf-8")

        for text in (skill, recipe, readme, provider):
            self.assertIn("youtube_api.py", text)
            self.assertIn("configure --gui", text)
            self.assertIn("check", text)
        self.assertIn("youtube_api.py collect", recipe)
        self.assertIn("coding_status", recipe)
        self.assertIn("YOUTUBE_API_KEY", readme)
        self.assertIn("Command Line Tools", readme)
        self.assertIn("xcrun", recipe)

    def test_credentials_prefer_environment_and_keychain_payload_is_not_returned(self):
        module = self.load_module()
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0, stdout=TEST_KEY, stderr="")

        from_environment = module.load_api_key(
            environ={"YOUTUBE_API_KEY": TEST_KEY},
            platform_name="linux",
            runner=runner,
        )
        from_keychain = module.load_api_key(
            environ={},
            platform_name="darwin",
            runner=runner,
            account="tester",
        )
        stored = module.store_api_key(
            TEST_KEY,
            platform_name="darwin",
            runner=runner,
            account="tester",
        )

        self.assertEqual(TEST_KEY, from_environment)
        self.assertEqual(TEST_KEY, from_keychain)
        self.assertNotIn(TEST_KEY, json.dumps(stored))
        self.assertEqual("macos-keychain", stored["storage"])
        read_command, _ = next(
            (command, kwargs)
            for command, kwargs in calls
            if any(part.endswith("keychain_store.swift") for part in command)
            and "read" in command
        )
        store_command, store_kwargs = next(
            (command, kwargs)
            for command, kwargs in calls
            if any(part.endswith("keychain_store.swift") for part in command)
            and "write" in command
        )
        self.assertEqual(["xcrun", "swift"], read_command[:2])
        self.assertNotIn(TEST_KEY, store_command)
        self.assertEqual(["xcrun", "swift"], store_command[:2])
        self.assertEqual("tester", store_command[-1])
        self.assertEqual(TEST_KEY, store_kwargs["input"])

    def test_macos_keychain_access_explains_missing_command_line_tools(self):
        module = self.load_module()

        def unavailable_runner(command, **kwargs):
            raise FileNotFoundError(command[0])

        with self.assertRaisesRegex(module.CredentialError, "Command Line Tools"):
            module.load_api_key(
                environ={},
                platform_name="darwin",
                runner=unavailable_runner,
                account="tester",
            )
        with self.assertRaisesRegex(module.CredentialError, "Command Line Tools"):
            module.store_api_key(
                TEST_KEY,
                platform_name="darwin",
                runner=unavailable_runner,
                account="tester",
            )

    def test_check_uses_public_api_without_oauth(self):
        module = self.load_module()
        transport = ScriptedTransport(
            {
                ("i18nRegions", None, None): {
                    "items": [{"id": "KR", "snippet": {"name": "South Korea"}}]
                }
            }
        )
        client = module.YouTubeApi(TEST_KEY, transport=transport, now=self.fixed_now)

        result = client.check()

        self.assertTrue(result["ok"])
        self.assertEqual("api_key", result["auth"])
        self.assertNotIn(TEST_KEY, json.dumps(result))
        self.assertEqual("i18nRegions", transport.calls[0][0])

    def test_collect_paginates_top_level_comments_and_all_replies(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result, transport = self.collect(module, root)

            validation = self.validate_bundle(root)
            manifest = json.loads((root / "collection-manifest.json").read_text())
            posts = [json.loads(line) for line in (root / "posts.jsonl").read_text().splitlines()]
            comments = [json.loads(line) for line in (root / "comments.jsonl").read_text().splitlines()]
            summary = json.loads((root / "reaction-summary.json").read_text())

        self.assertEqual(0, validation.returncode, validation.stderr)
        self.assertEqual("supported", result["status"])
        self.assertEqual("complete", result["coverage"])
        self.assertEqual(1, len(posts))
        self.assertEqual(1234, posts[0]["metrics"]["views"]["value"])
        self.assertEqual(["top-1", "top-2", "reply-1", "reply-2"], [item["comment_id"] for item in comments])
        self.assertFalse(any("author" in json.dumps(item).casefold() for item in comments))
        frame = manifest["collection_frames"][0]
        self.assertEqual(2, frame["achieved_top_level_comments"])
        self.assertEqual(2, frame["achieved_reply_comments"])
        self.assertEqual("youtube_api_full_pagination", frame["sampling_method"])
        self.assertEqual(4, summary["counts"]["collected"])
        self.assertEqual(4, summary["analysis_value"]["unclear"])
        self.assertEqual(0, summary["counts"]["usable"])
        calls = [(resource, params.get("pageToken"), params.get("parentId")) for resource, params in transport.calls]
        self.assertIn(("commentThreads", "thread-page-2", None), calls)
        self.assertIn(("comments", "reply-page-2", "top-1"), calls)
        thread_call = next(params for resource, params in transport.calls if resource == "commentThreads")
        self.assertEqual("snippet", thread_call["part"])

    def test_comment_cap_marks_partial_and_stops_before_replies(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, transport = self.collect(module, root, max_comments=1)
            manifest = json.loads((root / "collection-manifest.json").read_text())
            comments = [
                json.loads(line)
                for line in (root / "comments.jsonl").read_text().splitlines()
            ]
            validation = self.validate_bundle(root)

        frame = manifest["collection_frames"][0]
        self.assertEqual(0, validation.returncode, validation.stderr)
        self.assertEqual(1, len(comments))
        self.assertEqual("partial", frame["coverage"])
        self.assertEqual("user_comment_cap", frame["stop_reason"])
        self.assertEqual("youtube_api_bounded_pagination", frame["sampling_method"])
        self.assertEqual(
            "youtube_api_bounded_pagination",
            comments[0]["sampling_method"],
        )
        self.assertFalse(any(resource == "comments" for resource, _ in transport.calls))

    def test_comments_disabled_is_a_valid_partial_bundle(self):
        module = self.load_module()
        responses = {
            ("videos", None, None): self.video_response(),
            ("commentThreads", None, None): module.YouTubeApiError(
                403,
                "commentsDisabled",
                "Comments are disabled",
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result, _ = self.collect(module, root, responses=responses)
            manifest = json.loads((root / "collection-manifest.json").read_text())
            validation = self.validate_bundle(root)

        frame = manifest["collection_frames"][0]
        self.assertEqual(0, validation.returncode, validation.stderr)
        self.assertEqual("supported", result["status"])
        self.assertEqual("partial", result["coverage"])
        self.assertEqual("unavailable", frame["status"])
        self.assertEqual("comments_disabled", frame["stop_reason"])

    def test_top_level_only_ignores_replies_when_deciding_coverage(self):
        module = self.load_module()
        responses = {
            ("videos", None, None): self.video_response(),
            ("commentThreads", None, None): {
                "items": [self.top_comment("top-1", "Parent", reply_count=3)],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, transport = self.collect(
                module,
                root,
                responses=responses,
                include_replies=False,
                max_comments=1,
            )
            manifest = json.loads((root / "collection-manifest.json").read_text())
            validation = self.validate_bundle(root)

        frame = manifest["collection_frames"][0]
        self.assertEqual(0, validation.returncode, validation.stderr)
        self.assertEqual("complete", frame["coverage"])
        self.assertEqual("youtube_api_full_pagination", frame["sampling_method"])
        self.assertFalse(any(resource == "comments" for resource, _ in transport.calls))

    def test_mid_pagination_quota_error_preserves_collected_comments(self):
        module = self.load_module()
        responses = {
            ("videos", None, None): self.video_response(),
            ("commentThreads", None, None): {
                "items": [self.top_comment("top-1", "Already collected")],
                "nextPageToken": "thread-page-2",
            },
            ("commentThreads", "thread-page-2", None): module.YouTubeApiError(
                403,
                "quotaExceeded",
                "Daily quota exhausted",
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _ = self.collect(module, root, responses=responses)
            manifest = json.loads((root / "collection-manifest.json").read_text())
            comments = [
                json.loads(line)
                for line in (root / "comments.jsonl").read_text().splitlines()
            ]
            validation = self.validate_bundle(root)

        frame = manifest["collection_frames"][0]
        self.assertEqual(0, validation.returncode, validation.stderr)
        self.assertEqual(["top-1"], [item["comment_id"] for item in comments])
        self.assertEqual(1, frame["achieved_top_level_comments"])
        self.assertEqual("access-dependent", frame["status"])
        self.assertEqual("quota_exhausted", frame["stop_reason"])
        self.assertEqual(
            "youtube_api_partial_pagination",
            comments[0]["sampling_method"],
        )

    def test_reply_count_mismatch_is_not_labeled_full_enumeration(self):
        module = self.load_module()
        responses = {
            ("videos", None, None): self.video_response(),
            ("commentThreads", None, None): {
                "items": [self.top_comment("top-1", "Parent", reply_count=2)],
            },
            ("comments", None, "top-1"): {
                "items": [self.reply("reply-1", "top-1", "Only visible reply")],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _ = self.collect(module, root, responses=responses)
            manifest = json.loads((root / "collection-manifest.json").read_text())
            validation = self.validate_bundle(root)

        frame = manifest["collection_frames"][0]
        self.assertEqual(0, validation.returncode, validation.stderr)
        self.assertEqual("supported", frame["status"])
        self.assertEqual("partial", frame["coverage"])
        self.assertEqual("reply_count_mismatch", frame["stop_reason"])
        self.assertEqual("youtube_api_partial_pagination", frame["sampling_method"])
        self.assertEqual(1, frame["achieved_reply_comments"])

    def test_reply_failure_does_not_skip_other_threads_or_replies(self):
        module = self.load_module()
        responses = {
            ("videos", None, None): self.video_response(),
            ("commentThreads", None, None): {
                "items": [
                    self.top_comment("top-1", "First", reply_count=1),
                    self.top_comment("top-2", "Second", reply_count=1),
                ],
            },
            ("comments", None, "top-1"): module.YouTubeApiError(
                403,
                "forbidden",
                "Reply unavailable",
            ),
            ("comments", None, "top-2"): {
                "items": [self.reply("reply-2", "top-2", "Still accessible")],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, transport = self.collect(module, root, responses=responses)
            manifest = json.loads((root / "collection-manifest.json").read_text())
            comments = [
                json.loads(line)
                for line in (root / "comments.jsonl").read_text().splitlines()
            ]
            validation = self.validate_bundle(root)

        frame = manifest["collection_frames"][0]
        self.assertEqual(0, validation.returncode, validation.stderr)
        self.assertEqual(
            ["top-1", "top-2", "reply-2"],
            [item["comment_id"] for item in comments],
        )
        self.assertEqual(2, frame["achieved_top_level_comments"])
        self.assertEqual(1, frame["achieved_reply_comments"])
        self.assertEqual("partial", frame["coverage"])
        self.assertEqual("api_forbidden", frame["stop_reason"])
        self.assertIn(
            ("comments", None, "top-2"),
            [
                (resource, params.get("pageToken"), params.get("parentId"))
                for resource, params in transport.calls
            ],
        )

    def test_missing_video_produces_explicit_unavailable_frame(self):
        module = self.load_module()
        responses = {("videos", None, None): {"items": []}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result, _ = self.collect(module, root, responses=responses)
            manifest = json.loads((root / "collection-manifest.json").read_text())
            validation = self.validate_bundle(root)

        frame = manifest["collection_frames"][0]
        self.assertEqual(0, validation.returncode, validation.stderr)
        self.assertEqual("unavailable", result["status"])
        self.assertIsNone(frame["post_id"])
        self.assertEqual("video_not_found", frame["stop_reason"])

    def test_collection_refuses_more_than_five_videos_and_existing_outputs(self):
        module = self.load_module()
        transport = ScriptedTransport({})
        client = module.YouTubeApi(TEST_KEY, transport=transport, now=self.fixed_now)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                module.collect_to_directory(
                    client,
                    ["v1", "v2", "v3", "v4", "v5", "v6"],
                    root,
                    subject="Example",
                )
            (root / "posts.jsonl").write_text("user-owned", encoding="utf-8")
            with self.assertRaises(module.OutputExistsError):
                module.collect_to_directory(
                    client,
                    ["video-1"],
                    root,
                    subject="Example",
                )


if __name__ == "__main__":
    unittest.main()
