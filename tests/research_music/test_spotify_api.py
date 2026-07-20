import base64
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "skills"
    / "dig-music"
    / "scripts"
    / "spotify_api.py"
)


def load_module():
    if not SCRIPT.is_file():
        raise AssertionError(f"missing Spotify adapter: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("spotify_api", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecordingRunner:
    def __init__(self, stdout=""):
        self.stdout = stdout
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, stdout=self.stdout, stderr="")


class SequencedRunner:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        output = next(self.outputs)
        if isinstance(output, Exception):
            raise output
        return subprocess.CompletedProcess(args, 0, stdout=output, stderr="")


class FakeSpotifyTransport:
    def __init__(self):
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        if request.full_url == "https://accounts.spotify.com/api/token":
            return {"access_token": "token-value", "expires_in": 3600}, {}

        parsed = urlparse(request.full_url)
        if parsed.path == "/v1/search":
            query = parse_qs(parsed.query)
            kind = query["type"][0]
            return {
                f"{kind}s": {
                    "items": [
                        {
                            "id": "artist-id",
                            "uri": "spotify:artist:artist-id",
                            "name": "CORTIS",
                            "type": "artist",
                            "external_urls": {
                                "spotify": "https://open.spotify.com/artist/artist-id"
                            },
                            "genres": ["k-pop"],
                        }
                    ]
                }
            }, {}
        raise AssertionError(f"unexpected request: {request.full_url}")


class SpotifyCredentialTests(unittest.TestCase):
    def test_cli_exposes_configure_check_and_search_commands(self):
        load_module()

        result = subprocess.run(
            [os.fspath(SCRIPT), "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertIn("configure", result.stdout)
        self.assertIn("check", result.stdout)
        self.assertIn("search", result.stdout)

    def test_configure_help_exposes_native_gui_mode(self):
        load_module()

        result = subprocess.run(
            [os.fspath(SCRIPT), "configure", "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertIn("--gui", result.stdout)

    def test_gui_prompt_uses_hidden_native_secret_dialog(self):
        spotify = load_module()
        runner = SequencedRunner(["gui-id\n", "gui-secret\n"])

        credentials = spotify.prompt_gui_credentials(
            platform_name="darwin",
            runner=runner,
        )

        self.assertEqual(spotify.Credentials("gui-id", "gui-secret"), credentials)
        self.assertEqual(2, len(runner.calls))
        client_id_call, secret_call = runner.calls
        self.assertEqual("osascript", client_id_call[0][0])
        self.assertIn("Client ID", client_id_call[0][-1])
        self.assertIn("Client Secret", secret_call[0][-1])
        self.assertIn("with hidden answer", secret_call[0][-1])
        self.assertTrue(client_id_call[1]["capture_output"])
        self.assertTrue(secret_call[1]["capture_output"])
        self.assertNotIn("gui-secret", json.dumps(runner.calls))

    def test_gui_prompt_treats_dialog_cancellation_as_a_safe_error(self):
        spotify = load_module()
        cancelled = subprocess.CalledProcessError(1, ["osascript"])

        with self.assertRaisesRegex(spotify.CredentialError, "cancelled"):
            spotify.prompt_gui_credentials(
                platform_name="darwin",
                runner=SequencedRunner([cancelled]),
            )

    def test_gui_prompt_is_macos_only(self):
        spotify = load_module()

        with self.assertRaisesRegex(spotify.CredentialError, "macOS only"):
            spotify.prompt_gui_credentials(
                platform_name="linux",
                runner=SequencedRunner([]),
            )

    def test_environment_credentials_take_precedence(self):
        spotify = load_module()
        runner = RecordingRunner()

        credentials = spotify.load_credentials(
            environ={
                "SPOTIFY_CLIENT_ID": "environment-id",
                "SPOTIFY_CLIENT_SECRET": "environment-secret",
            },
            platform_name="darwin",
            runner=runner,
        )

        self.assertEqual("environment-id", credentials.client_id)
        self.assertEqual("environment-secret", credentials.client_secret)
        self.assertEqual([], runner.calls)

    def test_partial_environment_credentials_fail_closed(self):
        spotify = load_module()

        with self.assertRaisesRegex(
            spotify.CredentialError,
            "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET",
        ):
            spotify.load_credentials(
                environ={"SPOTIFY_CLIENT_ID": "only-an-id"},
                platform_name="darwin",
                runner=RecordingRunner(),
            )

    def test_macos_keychain_credentials_are_loaded_without_printing_secrets(self):
        spotify = load_module()
        payload = json.dumps(
            {"client_id": "keychain-id", "client_secret": "keychain-secret"}
        )
        runner = RecordingRunner(stdout=f"{payload}\n")

        credentials = spotify.load_credentials(
            environ={},
            platform_name="darwin",
            runner=runner,
            account="test-user",
        )

        self.assertEqual("keychain-id", credentials.client_id)
        self.assertEqual("keychain-secret", credentials.client_secret)
        args, kwargs = runner.calls[0]
        self.assertEqual(
            [
                "security",
                "find-generic-password",
                "-a",
                "test-user",
                "-s",
                spotify.KEYCHAIN_SERVICE,
                "-w",
            ],
            args,
        )
        self.assertTrue(kwargs["capture_output"])

    def test_macos_keychain_storage_updates_one_service_item(self):
        spotify = load_module()
        runner = RecordingRunner()

        result = spotify.store_credentials(
            spotify.Credentials("stored-id", "stored-secret"),
            platform_name="darwin",
            runner=runner,
            account="test-user",
        )

        self.assertEqual(
            {"storage": "macos-keychain", "service": spotify.KEYCHAIN_SERVICE},
            result,
        )
        args, kwargs = runner.calls[0]
        self.assertEqual("security", args[0])
        self.assertIn("add-generic-password", args)
        self.assertIn("-U", args)
        self.assertIn("test-user", args)
        payload = json.loads(args[args.index("-w") + 1])
        self.assertEqual(
            {"client_id": "stored-id", "client_secret": "stored-secret"},
            payload,
        )
        self.assertTrue(kwargs["capture_output"])

    def test_non_macos_without_environment_credentials_has_actionable_error(self):
        spotify = load_module()

        with self.assertRaisesRegex(spotify.CredentialError, "spotify_api.py configure"):
            spotify.load_credentials(environ={}, platform_name="linux")


class SpotifyApiTests(unittest.TestCase):
    def setUp(self):
        self.spotify = load_module()
        self.transport = FakeSpotifyTransport()
        self.client = self.spotify.SpotifyApi(
            self.spotify.Credentials("client-id", "client-secret"),
            transport=self.transport,
            now=lambda: datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc),
        )

    def test_check_verifies_token_and_catalog_without_returning_token(self):
        result = self.client.check()

        self.assertEqual(
            {
                "ok": True,
                "provider": "spotify",
                "auth": "client_credentials",
                "catalog_search": True,
                "expires_in": 3600,
                "observed_at": "2026-07-20T12:00:00Z",
            },
            result,
        )
        self.assertNotIn("token-value", json.dumps(result))

        token_request = self.transport.requests[0]
        authorization = token_request.get_header("Authorization")
        encoded = authorization.removeprefix("Basic ")
        self.assertEqual(
            "client-id:client-secret",
            base64.b64decode(encoded).decode("utf-8"),
        )
        self.assertEqual(
            {"grant_type": ["client_credentials"]},
            parse_qs(token_request.data.decode("utf-8")),
        )

    def test_search_returns_normalized_source_backed_artist_records(self):
        result = self.client.search("artist", "CORTIS", limit=5, market="KR")

        self.assertEqual("spotify", result["provider"])
        self.assertEqual("2026-07-20T12:00:00Z", result["observed_at"])
        self.assertEqual(
            {"type": "artist", "query": "CORTIS", "limit": 5, "market": "KR"},
            result["request"],
        )
        self.assertEqual(
            {
                "spotify_id": "artist-id",
                "spotify_uri": "spotify:artist:artist-id",
                "type": "artist",
                "name": "CORTIS",
                "spotify_url": "https://open.spotify.com/artist/artist-id",
                "genres": ["k-pop"],
            },
            result["items"][0],
        )

        search_request = self.transport.requests[-1]
        query = parse_qs(urlparse(search_request.full_url).query)
        self.assertEqual(["CORTIS"], query["q"])
        self.assertEqual(["artist"], query["type"])
        self.assertEqual(["5"], query["limit"])
        self.assertEqual(["KR"], query["market"])
        self.assertEqual("Bearer token-value", search_request.get_header("Authorization"))

    def test_search_rejects_limits_outside_development_mode_maximum(self):
        for limit in (0, 11):
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(ValueError, "between 1 and 10"):
                    self.client.search("album", "test", limit=limit)

    def test_album_records_preserve_release_identity_fields(self):
        result = self.spotify.normalize_item(
            "album",
            {
                "id": "album-id",
                "uri": "spotify:album:album-id",
                "name": "COLOR OUTSIDE THE LINES",
                "type": "album",
                "album_type": "album",
                "release_date": "2026-07-20",
                "release_date_precision": "day",
                "total_tracks": 5,
                "external_urls": {
                    "spotify": "https://open.spotify.com/album/album-id"
                },
                "artists": [{"id": "artist-id", "name": "CORTIS"}],
                "external_ids": {"upc": "123456789012"},
            },
        )

        self.assertEqual(
            {
                "spotify_id": "album-id",
                "spotify_uri": "spotify:album:album-id",
                "type": "album",
                "name": "COLOR OUTSIDE THE LINES",
                "spotify_url": "https://open.spotify.com/album/album-id",
                "artists": [{"spotify_id": "artist-id", "name": "CORTIS"}],
                "album_type": "album",
                "release_date": "2026-07-20",
                "release_date_precision": "day",
                "total_tracks": 5,
                "external_ids": {"upc": "123456789012"},
            },
            result,
        )

    def test_track_records_preserve_album_and_recording_identity(self):
        result = self.spotify.normalize_item(
            "track",
            {
                "id": "track-id",
                "uri": "spotify:track:track-id",
                "name": "GO!",
                "type": "track",
                "duration_ms": 173000,
                "explicit": False,
                "external_urls": {
                    "spotify": "https://open.spotify.com/track/track-id"
                },
                "artists": [{"id": "artist-id", "name": "CORTIS"}],
                "external_ids": {"isrc": "KRA012600001"},
                "album": {
                    "id": "album-id",
                    "name": "COLOR OUTSIDE THE LINES",
                    "release_date": "2026-07-20",
                    "release_date_precision": "day",
                },
            },
        )

        self.assertEqual(
            {
                "spotify_id": "track-id",
                "spotify_uri": "spotify:track:track-id",
                "type": "track",
                "name": "GO!",
                "spotify_url": "https://open.spotify.com/track/track-id",
                "artists": [{"spotify_id": "artist-id", "name": "CORTIS"}],
                "duration_ms": 173000,
                "explicit": False,
                "external_ids": {"isrc": "KRA012600001"},
                "album": {
                    "spotify_id": "album-id",
                    "name": "COLOR OUTSIDE THE LINES",
                    "release_date": "2026-07-20",
                    "release_date_precision": "day",
                },
            },
            result,
        )


class SpotifyDocumentationTests(unittest.TestCase):
    def test_provider_and_readme_explain_secure_setup_and_commands(self):
        provider = (
            ROOT
            / "skills"
            / "dig-music"
            / "providers"
            / "spotify.md"
        ).read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for expected in (
            "spotify_api.py configure",
            "spotify_api.py check",
            "spotify_api.py search",
            "macOS Keychain",
            "SPOTIFY_CLIENT_ID",
            "SPOTIFY_CLIENT_SECRET",
            "popularity",
        ):
            self.assertIn(expected, provider)
        self.assertIn("spotify_api.py configure", readme)

if __name__ == "__main__":
    unittest.main()
