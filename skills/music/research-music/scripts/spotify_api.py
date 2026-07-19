#!/usr/bin/env python3
"""Small, dependency-free Spotify catalog adapter for research-music."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timedelta, timezone
import getpass
import json
import os
import subprocess
import sys
from typing import Any, Callable, Mapping, NamedTuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"
KEYCHAIN_SERVICE = "music-industry-skills.spotify"
SEARCH_TYPES = ("artist", "album", "track")
GUI_TITLE = "Music Industry Skills — Spotify"
CLIENT_ID_DIALOG = f'''set response to display dialog "Enter your Spotify app Client ID." default answer "" buttons {{"Cancel", "Continue"}} default button "Continue" with title "{GUI_TITLE}"
return text returned of response'''
CLIENT_SECRET_DIALOG = f'''set response to display dialog "Enter your Spotify app Client Secret." default answer "" buttons {{"Cancel", "Connect"}} default button "Connect" with title "{GUI_TITLE}" with hidden answer
return text returned of response'''


class Credentials(NamedTuple):
    client_id: str
    client_secret: str


class CredentialError(RuntimeError):
    """Raised when Spotify credentials are absent or unusable."""


class SpotifyApiError(RuntimeError):
    """Raised when Spotify rejects a request or returns invalid data."""


Runner = Callable[..., subprocess.CompletedProcess]
Transport = Callable[[Request], tuple[dict[str, Any], Mapping[str, str]]]


def _validate_credentials(client_id: str, client_secret: str) -> Credentials:
    client_id = client_id.strip()
    client_secret = client_secret.strip()
    if not client_id or not client_secret:
        raise CredentialError("Spotify Client ID and Client Secret are both required.")
    return Credentials(client_id, client_secret)


def load_credentials(
    *,
    environ: Mapping[str, str] | None = None,
    platform_name: str | None = None,
    runner: Runner = subprocess.run,
    account: str | None = None,
) -> Credentials:
    """Load credentials from environment first, then the macOS Keychain."""

    environ = os.environ if environ is None else environ
    platform_name = sys.platform if platform_name is None else platform_name
    client_id = environ.get("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = environ.get("SPOTIFY_CLIENT_SECRET", "").strip()

    if bool(client_id) != bool(client_secret):
        raise CredentialError(
            "Set both SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET, or unset both."
        )
    if client_id and client_secret:
        return Credentials(client_id, client_secret)

    if platform_name != "darwin":
        raise CredentialError(
            "No Spotify credentials found. Set SPOTIFY_CLIENT_ID and "
            "SPOTIFY_CLIENT_SECRET. On macOS, run `spotify_api.py configure`."
        )

    account = account or getpass.getuser()
    command = [
        "security",
        "find-generic-password",
        "-a",
        account,
        "-s",
        KEYCHAIN_SERVICE,
        "-w",
    ]
    try:
        result = runner(command, text=True, capture_output=True, check=True)
        payload = json.loads(result.stdout)
        return _validate_credentials(
            str(payload.get("client_id", "")),
            str(payload.get("client_secret", "")),
        )
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError):
        raise CredentialError(
            "Spotify credentials are not configured. Run `spotify_api.py configure`."
        ) from None


def store_credentials(
    credentials: Credentials,
    *,
    platform_name: str | None = None,
    runner: Runner = subprocess.run,
    account: str | None = None,
) -> dict[str, str]:
    """Store one Spotify credential bundle in the macOS login Keychain."""

    platform_name = sys.platform if platform_name is None else platform_name
    if platform_name != "darwin":
        raise CredentialError(
            "Secure automatic storage is currently available on macOS only. "
            "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET instead."
        )

    credentials = _validate_credentials(*credentials)
    account = account or getpass.getuser()
    payload = json.dumps(
        {
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
        },
        separators=(",", ":"),
    )
    command = [
        "security",
        "add-generic-password",
        "-U",
        "-a",
        account,
        "-s",
        KEYCHAIN_SERVICE,
        "-w",
        payload,
    ]
    try:
        runner(command, text=True, capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise CredentialError("Could not save Spotify credentials to macOS Keychain.") from None
    return {"storage": "macos-keychain", "service": KEYCHAIN_SERVICE}


def _native_dialog(script: str, runner: Runner) -> str:
    try:
        result = runner(
            ["osascript", "-e", script],
            text=True,
            capture_output=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise CredentialError(
            "Spotify configuration was cancelled or the native dialog is unavailable."
        ) from None
    return result.stdout.strip()


def prompt_gui_credentials(
    *,
    platform_name: str | None = None,
    runner: Runner = subprocess.run,
) -> Credentials:
    """Collect app credentials through native macOS dialogs without echoing them."""

    platform_name = sys.platform if platform_name is None else platform_name
    if platform_name != "darwin":
        raise CredentialError("Spotify GUI configuration is available on macOS only.")
    client_id = _native_dialog(CLIENT_ID_DIALOG, runner)
    client_secret = _native_dialog(CLIENT_SECRET_DIALOG, runner)
    return _validate_credentials(client_id, client_secret)


def _default_transport(request: Request) -> tuple[dict[str, Any], Mapping[str, str]]:
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw)
            return payload, dict(response.headers.items())
    except HTTPError as error:
        raise SpotifyApiError(
            f"Spotify API request failed with HTTP {error.code}."
        ) from None
    except URLError as error:
        raise SpotifyApiError(f"Could not reach Spotify API: {error.reason}") from None
    except json.JSONDecodeError:
        raise SpotifyApiError("Spotify returned an invalid JSON response.") from None


def _artist_reference(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "spotify_id": item.get("id"),
        "name": item.get("name"),
    }


def normalize_item(kind: str, item: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize stable identity metadata without inventing removed API fields."""

    if kind not in SEARCH_TYPES:
        raise ValueError(f"Spotify search type must be one of: {', '.join(SEARCH_TYPES)}")

    normalized: dict[str, Any] = {
        "spotify_id": item.get("id"),
        "spotify_uri": item.get("uri"),
        "type": item.get("type", kind),
        "name": item.get("name"),
        "spotify_url": item.get("external_urls", {}).get("spotify"),
    }
    if kind == "artist":
        normalized["genres"] = list(item.get("genres") or [])
        return normalized

    normalized["artists"] = [
        _artist_reference(artist) for artist in item.get("artists") or []
    ]
    if kind == "album":
        normalized.update(
            {
                "album_type": item.get("album_type"),
                "release_date": item.get("release_date"),
                "release_date_precision": item.get("release_date_precision"),
                "total_tracks": item.get("total_tracks"),
                "external_ids": dict(item.get("external_ids") or {}),
            }
        )
        return normalized

    album = item.get("album") or {}
    normalized.update(
        {
            "duration_ms": item.get("duration_ms"),
            "explicit": item.get("explicit"),
            "external_ids": dict(item.get("external_ids") or {}),
            "album": {
                "spotify_id": album.get("id"),
                "name": album.get("name"),
                "release_date": album.get("release_date"),
                "release_date_precision": album.get("release_date_precision"),
            },
        }
    )
    return normalized


class SpotifyApi:
    """Client Credentials client for public Spotify catalog searches."""

    def __init__(
        self,
        credentials: Credentials,
        *,
        transport: Transport | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.credentials = _validate_credentials(*credentials)
        self.transport = transport or _default_transport
        self.now = now or (lambda: datetime.now(timezone.utc))
        self._access_token: str | None = None
        self._expires_at: datetime | None = None
        self._expires_in: int | None = None

    def _observed_at(self) -> str:
        observed = self.now().astimezone(timezone.utc).replace(microsecond=0)
        return observed.isoformat().replace("+00:00", "Z")

    def _ensure_token(self) -> str:
        now = self.now().astimezone(timezone.utc)
        if (
            self._access_token
            and self._expires_at
            and now < self._expires_at - timedelta(seconds=30)
        ):
            return self._access_token

        raw_credentials = (
            f"{self.credentials.client_id}:{self.credentials.client_secret}".encode("utf-8")
        )
        authorization = base64.b64encode(raw_credentials).decode("ascii")
        request = Request(
            TOKEN_URL,
            data=urlencode({"grant_type": "client_credentials"}).encode("utf-8"),
            headers={
                "Authorization": f"Basic {authorization}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        payload, _ = self.transport(request)
        access_token = payload.get("access_token")
        try:
            expires_in = int(payload.get("expires_in", 3600))
        except (TypeError, ValueError):
            raise SpotifyApiError("Spotify returned an invalid token lifetime.") from None
        if not isinstance(access_token, str) or not access_token:
            raise SpotifyApiError("Spotify did not return an access token.")

        self._access_token = access_token
        self._expires_in = expires_in
        self._expires_at = now + timedelta(seconds=expires_in)
        return access_token

    def _catalog_request(self, params: Mapping[str, Any]) -> dict[str, Any]:
        token = self._ensure_token()
        request = Request(
            f"{API_BASE}/search?{urlencode(params)}",
            headers={"Authorization": f"Bearer {token}"},
            method="GET",
        )
        payload, _ = self.transport(request)
        return payload

    def check(self) -> dict[str, Any]:
        self._ensure_token()
        self._catalog_request({"q": "Spotify", "type": "artist", "limit": 1})
        return {
            "ok": True,
            "provider": "spotify",
            "auth": "client_credentials",
            "catalog_search": True,
            "expires_in": self._expires_in,
            "observed_at": self._observed_at(),
        }

    def search(
        self,
        kind: str,
        query: str,
        *,
        limit: int = 5,
        market: str | None = None,
    ) -> dict[str, Any]:
        if kind not in SEARCH_TYPES:
            raise ValueError(f"Spotify search type must be one of: {', '.join(SEARCH_TYPES)}")
        if not 1 <= limit <= 10:
            raise ValueError("Spotify development-mode search limit must be between 1 and 10.")
        if not query.strip():
            raise ValueError("Spotify search query must not be empty.")

        request_record: dict[str, Any] = {
            "type": kind,
            "query": query,
            "limit": limit,
            "market": market,
        }
        params: dict[str, Any] = {"q": query, "type": kind, "limit": limit}
        if market:
            params["market"] = market
        payload = self._catalog_request(params)
        container = payload.get(f"{kind}s") or {}
        items = container.get("items") or []
        return {
            "provider": "spotify",
            "observed_at": self._observed_at(),
            "request": request_record,
            "items": [normalize_item(kind, item) for item in items],
        }


def _print_json(payload: Mapping[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _configure(*, gui: bool = False) -> dict[str, Any]:
    if sys.platform != "darwin":
        raise CredentialError(
            "`configure` currently stores credentials in macOS Keychain. "
            "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET on this platform."
        )
    if gui:
        credentials = prompt_gui_credentials()
    else:
        client_id = input("Spotify Client ID: ").strip()
        client_secret = getpass.getpass("Spotify Client Secret (hidden): ").strip()
        credentials = _validate_credentials(client_id, client_secret)
    storage = store_credentials(credentials)
    check = SpotifyApi(credentials).check()
    return {"configured": True, **storage, "check": check}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Secure Spotify catalog access for the research-music skill."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    configure = commands.add_parser(
        "configure",
        help="Store app credentials in macOS Keychain and verify the connection.",
    )
    configure.add_argument(
        "--gui",
        action="store_true",
        help="Collect credentials in native macOS dialogs for agent-driven setup.",
    )
    commands.add_parser("check", help="Verify authentication and catalog search.")
    search = commands.add_parser("search", help="Search Spotify catalog metadata.")
    search.add_argument("type", choices=SEARCH_TYPES)
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=5)
    search.add_argument("--market", help="ISO 3166-1 alpha-2 market, such as KR.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "configure":
            result = _configure(gui=args.gui)
        else:
            client = SpotifyApi(load_credentials())
            if args.command == "check":
                result = client.check()
            else:
                result = client.search(
                    args.type,
                    args.query,
                    limit=args.limit,
                    market=args.market,
                )
        _print_json(result)
        return 0
    except (CredentialError, SpotifyApiError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
