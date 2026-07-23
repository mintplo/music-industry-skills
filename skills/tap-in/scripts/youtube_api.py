#!/usr/bin/env python3
"""Secure YouTube Data API access and public reaction collection."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Mapping, NamedTuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import uuid


API_BASE = "https://www.googleapis.com/youtube/v3"
KEYCHAIN_SERVICE = "music-industry-skills.youtube-data-api"
KEYCHAIN_STORE_HELPER = Path(__file__).with_name("keychain_store.swift")
GUI_TITLE = "Music Industry Skills — YouTube Data API"
CONTRACT_VERSION = "tap-in/v1"
OUTPUT_FILES = (
    "collection-manifest.json",
    "posts.jsonl",
    "comments.jsonl",
    "reaction-summary.json",
)
GUI_DIALOG = f'''set response to display dialog "Enter your YouTube Data API v3 key. The key will be verified and stored in macOS Keychain." default answer "" buttons {{"Cancel", "Connect"}} default button "Connect" with title "{GUI_TITLE}" with hidden answer
return text returned of response'''


class CredentialError(RuntimeError):
    """Raised when the YouTube API key is absent or unusable."""


class OutputExistsError(RuntimeError):
    """Raised when collection would replace an existing contract artifact."""


class YouTubeApiError(RuntimeError):
    """A redacted YouTube Data API failure."""

    def __init__(self, status: int | None, reason: str, message: str) -> None:
        self.status = status
        self.reason = reason or "unknown_error"
        self.message = message or "YouTube Data API request failed"
        status_text = "HTTP {}".format(status) if status is not None else "network error"
        super().__init__("{}: {} ({})".format(status_text, self.message, self.reason))


Runner = Callable[..., subprocess.CompletedProcess]
Transport = Callable[[str, Mapping[str, Any]], dict[str, Any]]


class CommentCollection(NamedTuple):
    comments: list[dict[str, Any]]
    top_level_count: int
    reply_count: int
    coverage: str
    stop_reason: str | None
    error: YouTubeApiError | None


def _validate_api_key(api_key: str) -> str:
    api_key = api_key.strip()
    if len(api_key) < 20 or any(character.isspace() for character in api_key):
        raise CredentialError("A valid YouTube Data API key is required.")
    return api_key


def load_api_key(
    *,
    environ: Mapping[str, str] | None = None,
    platform_name: str | None = None,
    runner: Runner = subprocess.run,
    account: str | None = None,
) -> str:
    """Load YOUTUBE_API_KEY first, then the macOS login Keychain."""

    environ = os.environ if environ is None else environ
    platform_name = sys.platform if platform_name is None else platform_name
    environment_key = environ.get("YOUTUBE_API_KEY", "").strip()
    if environment_key:
        return _validate_api_key(environment_key)
    if platform_name != "darwin":
        raise CredentialError(
            "No YouTube API key found. Set YOUTUBE_API_KEY. On macOS, run "
            "`youtube_api.py configure --gui`."
        )

    account = account or getpass.getuser()
    command = [
        "xcrun",
        "swift",
        str(KEYCHAIN_STORE_HELPER),
        "read",
        KEYCHAIN_SERVICE,
        account,
    ]
    try:
        result = runner(command, text=True, capture_output=True, check=True)
        return _validate_api_key(result.stdout)
    except FileNotFoundError:
        raise CredentialError(
            "macOS Command Line Tools are required for Keychain access. Run "
            "`xcode-select --install`, then try again."
        ) from None
    except (subprocess.CalledProcessError, CredentialError):
        raise CredentialError(
            "YouTube API key is not configured. Run `youtube_api.py configure --gui`."
        ) from None


def store_api_key(
    api_key: str,
    *,
    platform_name: str | None = None,
    runner: Runner = subprocess.run,
    account: str | None = None,
) -> dict[str, str]:
    """Store the key in macOS Keychain without returning it."""

    api_key = _validate_api_key(api_key)
    platform_name = sys.platform if platform_name is None else platform_name
    if platform_name != "darwin":
        raise CredentialError(
            "Secure automatic storage is available on macOS only. Set YOUTUBE_API_KEY."
        )
    account = account or getpass.getuser()
    command = [
        "xcrun",
        "swift",
        str(KEYCHAIN_STORE_HELPER),
        "write",
        KEYCHAIN_SERVICE,
        account,
    ]
    try:
        runner(
            command,
            input=api_key,
            text=True,
            capture_output=True,
            check=True,
        )
    except FileNotFoundError:
        raise CredentialError(
            "macOS Command Line Tools are required for Keychain access. Run "
            "`xcode-select --install`, then try again."
        ) from None
    except (OSError, subprocess.CalledProcessError):
        raise CredentialError("Could not save the YouTube API key to macOS Keychain.") from None
    return {"storage": "macos-keychain", "service": KEYCHAIN_SERVICE}


def _native_dialog(script: str, runner: Runner = subprocess.run) -> str:
    try:
        result = runner(
            ["osascript", "-e", script],
            text=True,
            capture_output=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise CredentialError(
            "YouTube configuration was cancelled or the native dialog is unavailable."
        ) from None
    return result.stdout.strip()


def prompt_gui_api_key(
    *,
    platform_name: str | None = None,
    runner: Runner = subprocess.run,
) -> str:
    platform_name = sys.platform if platform_name is None else platform_name
    if platform_name != "darwin":
        raise CredentialError("YouTube GUI configuration is available on macOS only.")
    return _validate_api_key(_native_dialog(GUI_DIALOG, runner))


def _parse_api_error(raw: bytes, status: int, api_key: str) -> YouTubeApiError:
    reason = "http_error"
    message = "YouTube Data API request failed"
    try:
        payload = json.loads(raw.decode("utf-8"))
        error = payload.get("error") or {}
        message = str(error.get("message") or message)
        details = error.get("errors") or []
        if details and isinstance(details[0], dict):
            reason = str(details[0].get("reason") or reason)
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        pass
    return YouTubeApiError(
        status,
        reason.replace(api_key, "[REDACTED]"),
        message.replace(api_key, "[REDACTED]"),
    )


def _default_transport(api_key: str, resource: str, params: Mapping[str, Any]) -> dict[str, Any]:
    query = dict(params)
    query["key"] = api_key
    request = Request(
        "{}/{}?{}".format(API_BASE, resource, urlencode(query)),
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise _parse_api_error(error.read(), error.code, api_key) from None
    except URLError as error:
        reason = str(error.reason).replace(api_key, "[REDACTED]")
        raise YouTubeApiError(None, "network_error", reason) from None
    except json.JSONDecodeError:
        raise YouTubeApiError(None, "invalid_json", "YouTube returned invalid JSON") from None


class YouTubeApi:
    """Dependency-free client for public YouTube Data API reads."""

    def __init__(
        self,
        api_key: str,
        *,
        transport: Transport | None = None,
        now: Callable[[], datetime] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = _validate_api_key(api_key)
        self.transport = transport or (
            lambda resource, params: _default_transport(self.api_key, resource, params)
        )
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.sleep = sleep

    def observed_at(self) -> str:
        value = self.now().astimezone(timezone.utc).replace(microsecond=0)
        return value.isoformat().replace("+00:00", "Z")

    def request(self, resource: str, params: Mapping[str, Any]) -> dict[str, Any]:
        transient_statuses = {429, 500, 502, 503, 504}
        transient_reasons = {"rateLimitExceeded", "userRateLimitExceeded", "backendError"}
        for attempt in range(4):
            try:
                payload = self.transport(resource, params)
                if not isinstance(payload, dict):
                    raise YouTubeApiError(None, "invalid_json", "YouTube returned a non-object response")
                return payload
            except YouTubeApiError as error:
                transient = error.status in transient_statuses or error.reason in transient_reasons
                if not transient or attempt == 3:
                    raise
                self.sleep(min(2**attempt, 8))
        raise AssertionError("unreachable")

    def check(self) -> dict[str, Any]:
        payload = self.request("i18nRegions", {"part": "snippet", "hl": "en"})
        return {
            "ok": True,
            "provider": "youtube-data-api-v3",
            "auth": "api_key",
            "public_read": True,
            "regions_returned": len(payload.get("items") or []),
            "observed_at": self.observed_at(),
        }

    def get_video(self, video_id: str) -> dict[str, Any] | None:
        payload = self.request(
            "videos",
            {"part": "snippet,statistics", "id": video_id},
        )
        items = payload.get("items") or []
        return items[0] if items else None


def _metric(
    statistics: Mapping[str, Any],
    key: str,
    source_url: str,
    observed_at: str,
) -> dict[str, Any]:
    raw = statistics.get(key)
    if raw is None:
        return {
            "value": None,
            "display_value": None,
            "is_exact": None,
            "observed_at": observed_at,
            "availability": "unavailable",
            "source_url": source_url,
            "missing_reason": "not_returned_by_api",
        }
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return {
            "value": None,
            "display_value": str(raw),
            "is_exact": False,
            "observed_at": observed_at,
            "availability": "available",
            "source_url": source_url,
            "missing_reason": "invalid_numeric_value",
        }
    return {
        "value": value,
        "display_value": str(raw),
        "is_exact": True,
        "observed_at": observed_at,
        "availability": "available",
        "source_url": source_url,
    }


def _post_record(
    item: Mapping[str, Any],
    run_id: str,
    observed_at: str,
) -> dict[str, Any]:
    video_id = str(item.get("id"))
    url = "https://www.youtube.com/watch?v={}".format(video_id)
    snippet = item.get("snippet") or {}
    statistics = item.get("statistics") or {}
    return {
        "contract_version": CONTRACT_VERSION,
        "run_id": run_id,
        "platform": "youtube",
        "post_id": video_id,
        "canonical_url": url,
        "published_at": snippet.get("publishedAt"),
        "observed_at": observed_at,
        "collection_method": "youtube_data_api_v3",
        "content_type": "video",
        "title": snippet.get("title"),
        "text": str(snippet.get("description") or ""),
        "channel_id": snippet.get("channelId"),
        "channel_title": snippet.get("channelTitle"),
        "metrics": {
            "views": _metric(statistics, "viewCount", url, observed_at),
            "likes": _metric(statistics, "likeCount", url, observed_at),
            "comments": _metric(statistics, "commentCount", url, observed_at),
        },
    }


def _comment_record(
    item: Mapping[str, Any],
    *,
    run_id: str,
    video_id: str,
    parent_comment_id: str | None,
    rank: int,
    observed_at: str,
) -> dict[str, Any]:
    snippet = item.get("snippet") or {}
    return {
        "contract_version": CONTRACT_VERSION,
        "run_id": run_id,
        "platform": "youtube",
        "post_id": video_id,
        "comment_id": str(item.get("id")),
        "parent_comment_id": parent_comment_id,
        "text": str(snippet.get("textOriginal") or snippet.get("textDisplay") or ""),
        "published_at": snippet.get("publishedAt"),
        "updated_at": snippet.get("updatedAt"),
        "observed_at": observed_at,
        "sample_rank": rank,
        "sampling_method": "youtube_api_full_pagination",
        "source_url": "https://www.youtube.com/watch?v={}".format(video_id),
        "like_count": snippet.get("likeCount"),
        "reply_depth": 1 if parent_comment_id else 0,
        "coding_status": "pending",
        "labels": {
            "analysis_value": "unclear",
            "sentiment": "unclear",
            "toxicity": [],
            "confidence": "low",
        },
    }


def _collect_replies(
    client: YouTubeApi,
    *,
    video_id: str,
    parent_id: str,
    run_id: str,
    observed_at: str,
    comments: list[dict[str, Any]],
    max_comments: int | None,
) -> tuple[int, bool]:
    reply_count = 0
    page_token = None
    while True:
        params: dict[str, Any] = {
            "part": "snippet",
            "parentId": parent_id,
            "maxResults": 100,
            "textFormat": "plainText",
        }
        if page_token:
            params["pageToken"] = page_token
        payload = client.request("comments", params)
        for reply in payload.get("items") or []:
            if max_comments is not None and len(comments) >= max_comments:
                return reply_count, True
            comments.append(
                _comment_record(
                    reply,
                    run_id=run_id,
                    video_id=video_id,
                    parent_comment_id=parent_id,
                    rank=len(comments) + 1,
                    observed_at=observed_at,
                )
            )
            reply_count += 1
        page_token = payload.get("nextPageToken")
        if not page_token:
            return reply_count, False


def _collect_comments(
    client: YouTubeApi,
    *,
    video_id: str,
    run_id: str,
    observed_at: str,
    include_replies: bool,
    max_comments: int | None,
) -> CommentCollection:
    comments: list[dict[str, Any]] = []
    reply_targets: list[tuple[str, int]] = []
    page_token = None

    def result(
        coverage: str,
        stop_reason: str | None = None,
        error: YouTubeApiError | None = None,
    ) -> CommentCollection:
        actual_top = sum(item["parent_comment_id"] is None for item in comments)
        actual_replies = len(comments) - actual_top
        return CommentCollection(
            comments,
            actual_top,
            actual_replies,
            coverage,
            stop_reason,
            error,
        )

    while True:
        params: dict[str, Any] = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,
            "textFormat": "plainText",
            "order": "time",
        }
        if page_token:
            params["pageToken"] = page_token
        try:
            payload = client.request("commentThreads", params)
        except YouTubeApiError as error:
            return result("partial", error=error)
        threads = payload.get("items") or []
        for index, thread in enumerate(threads):
            if max_comments is not None and len(comments) >= max_comments:
                return result("partial", "user_comment_cap")
            snippet = thread.get("snippet") or {}
            top_level = snippet.get("topLevelComment") or {}
            top_level_id = str(top_level.get("id"))
            comments.append(
                _comment_record(
                    top_level,
                    run_id=run_id,
                    video_id=video_id,
                    parent_comment_id=None,
                    rank=len(comments) + 1,
                    observed_at=observed_at,
                )
            )
            total_replies = int(snippet.get("totalReplyCount") or 0)
            reply_targets.append((top_level_id, total_replies))
            if max_comments is not None and len(comments) >= max_comments:
                more_exist = (
                    (
                        include_replies
                        and any(reply_total > 0 for _, reply_total in reply_targets)
                    )
                    or index < len(threads) - 1
                    or bool(payload.get("nextPageToken"))
                )
                if more_exist:
                    return result("partial", "user_comment_cap")
        page_token = payload.get("nextPageToken")
        if not page_token:
            break

    if not include_replies:
        return result("complete")

    first_error: YouTubeApiError | None = None
    partial_reason: str | None = None
    for parent_id, total_replies in reply_targets:
        if not total_replies:
            continue
        if max_comments is not None and len(comments) >= max_comments:
            return result("partial", "user_comment_cap", first_error)
        try:
            added, capped = _collect_replies(
                client,
                video_id=video_id,
                parent_id=parent_id,
                run_id=run_id,
                observed_at=observed_at,
                comments=comments,
                max_comments=max_comments,
            )
        except YouTubeApiError as error:
            if first_error is None:
                first_error = error
            continue
        if capped:
            return result("partial", "user_comment_cap", first_error)
        if added < total_replies:
            partial_reason = partial_reason or "reply_count_mismatch"

    if first_error is not None:
        return result("partial", partial_reason, first_error)
    if partial_reason is not None:
        return result("partial", partial_reason)
    return result("complete")


def _stop_reason(error: YouTubeApiError) -> tuple[str, str]:
    mappings = {
        "commentsDisabled": ("unavailable", "comments_disabled"),
        "videoNotFound": ("unavailable", "video_not_found"),
        "quotaExceeded": ("access-dependent", "quota_exhausted"),
        "dailyLimitExceeded": ("access-dependent", "quota_exhausted"),
        "rateLimitExceeded": ("access-dependent", "rate_limited"),
        "userRateLimitExceeded": ("access-dependent", "rate_limited"),
    }
    if error.reason in mappings:
        return mappings[error.reason]
    safe_reason = re.sub(r"[^a-z0-9]+", "_", error.reason.casefold()).strip("_")
    return "access-dependent", "api_{}".format(safe_reason or "failure")


def _frame(
    *,
    video_id: str,
    post_id: str | None,
    status: str,
    coverage: str,
    sampling_method: str,
    target_comments: int | None,
    top_level_count: int,
    reply_count: int,
    stop_reason: str | None,
    observed_at: str,
) -> dict[str, Any]:
    return {
        "frame_id": "youtube:{}".format(video_id),
        "platform": "youtube",
        "post_id": post_id,
        "requested_url": "https://www.youtube.com/watch?v={}".format(video_id),
        "status": status,
        "coverage": coverage,
        "sampling_method": sampling_method,
        "target_comments": target_comments,
        "achieved_top_level_comments": top_level_count,
        "achieved_reply_comments": reply_count,
        "stop_reason": stop_reason,
        "observed_at": observed_at,
    }


def _empty_summary(run_id: str, comments: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(comments)
    return {
        "contract_version": CONTRACT_VERSION,
        "run_id": run_id,
        "counts": {"collected": count, "usable": 0, "excluded": count},
        "sentiment": {
            "positive": 0,
            "negative": 0,
            "mixed": 0,
            "neutral": 0,
            "unclear": 0,
        },
        "analysis_value": {
            "substantive": 0,
            "affect_only": 0,
            "off_topic": 0,
            "duplicate": 0,
            "promotional_spam": 0,
            "suspected_automation": 0,
            "unclear": count,
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
        "limitations": [
            "Comment coding is pending; provisional labels are unclear with low confidence."
        ],
    }


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=".{}-".format(path.name),
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_bundle(
    output: Path,
    manifest: Mapping[str, Any],
    posts: list[dict[str, Any]],
    comments: list[dict[str, Any]],
    summary: Mapping[str, Any],
) -> None:
    documents = {
        "collection-manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        "posts.jsonl": "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in posts),
        "comments.jsonl": "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in comments),
        "reaction-summary.json": json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
    }
    for filename, text in documents.items():
        _write_atomic(output / filename, text)


def collect_to_directory(
    client: YouTubeApi,
    video_ids: list[str],
    output: Path,
    *,
    subject: str,
    include_replies: bool = True,
    max_comments: int | None = None,
    overwrite: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    video_ids = [value.strip() for value in video_ids if value.strip()]
    if not video_ids:
        raise ValueError("At least one YouTube video ID is required.")
    if len(video_ids) > 5:
        raise ValueError("A collection run supports at most five YouTube videos.")
    if len(video_ids) != len(set(video_ids)):
        raise ValueError("Duplicate YouTube video IDs are not allowed.")
    if max_comments is not None and max_comments < 1:
        raise ValueError("max_comments must be a positive integer.")
    if not subject.strip():
        raise ValueError("subject must not be empty.")
    output = Path(output)
    existing = [output / name for name in OUTPUT_FILES if (output / name).exists()]
    if existing and not overwrite:
        raise OutputExistsError(
            "Refusing to replace existing artifact: {}".format(existing[0].name)
        )

    run_id = run_id or "youtube-{}".format(uuid.uuid4())
    started_at = client.observed_at()
    posts: list[dict[str, Any]] = []
    comments: list[dict[str, Any]] = []
    frames: list[dict[str, Any]] = []
    for video_id in video_ids:
        observed_at = client.observed_at()
        try:
            video = client.get_video(video_id)
        except YouTubeApiError as error:
            status, reason = _stop_reason(error)
            frames.append(
                _frame(
                    video_id=video_id,
                    post_id=None,
                    status=status,
                    coverage="partial",
                    sampling_method="youtube_api_not_started",
                    target_comments=max_comments,
                    top_level_count=0,
                    reply_count=0,
                    stop_reason=reason,
                    observed_at=observed_at,
                )
            )
            continue
        if video is None:
            frames.append(
                _frame(
                    video_id=video_id,
                    post_id=None,
                    status="unavailable",
                    coverage="partial",
                    sampling_method="youtube_api_not_started",
                    target_comments=max_comments,
                    top_level_count=0,
                    reply_count=0,
                    stop_reason="video_not_found",
                    observed_at=observed_at,
                )
            )
            continue

        posts.append(_post_record(video, run_id, observed_at))
        collection = _collect_comments(
            client,
            video_id=video_id,
            run_id=run_id,
            observed_at=observed_at,
            include_replies=include_replies,
            max_comments=max_comments,
        )
        if collection.error is not None:
            frame_status, frame_reason = _stop_reason(collection.error)
        else:
            frame_status = "supported"
            frame_reason = collection.stop_reason
        if collection.coverage == "complete":
            sampling_method = "youtube_api_full_pagination"
        elif collection.stop_reason == "user_comment_cap":
            sampling_method = "youtube_api_bounded_pagination"
        else:
            sampling_method = "youtube_api_partial_pagination"
        for comment in collection.comments:
            comment["sampling_method"] = sampling_method
        comments.extend(collection.comments)
        frames.append(
            _frame(
                video_id=video_id,
                post_id=video_id,
                status=frame_status,
                coverage=collection.coverage,
                sampling_method=sampling_method,
                target_comments=max_comments,
                top_level_count=collection.top_level_count,
                reply_count=collection.reply_count,
                stop_reason=frame_reason,
                observed_at=observed_at,
            )
        )

    status = (
        "supported"
        if posts
        else "access-dependent"
        if any(frame["status"] == "access-dependent" for frame in frames)
        else "unavailable"
    )
    coverage = "complete" if frames and all(frame["coverage"] == "complete" for frame in frames) else "partial"
    limitations = [
        "Public counters and comments are observations at collection time.",
        "Comments can be added, edited, hidden, or deleted during pagination.",
        "Comment coding is pending after API collection.",
    ]
    if not include_replies:
        limitations.append("Replies were excluded by request.")
    if max_comments is not None:
        limitations.append("A user comment cap may truncate a video's comment frame.")
    completed_at = client.observed_at()
    manifest = {
        "contract_version": CONTRACT_VERSION,
        "run_id": run_id,
        "subject": {
            "name": subject.strip(),
            "seed_urls": [
                "https://www.youtube.com/watch?v={}".format(video_id)
                for video_id in video_ids
            ],
        },
        "status": status,
        "coverage": coverage,
        "started_at": started_at,
        "completed_at": completed_at,
        "platforms": [
            {
                "platform": "youtube",
                "status": status,
                "coverage": coverage,
                "collection_method": "youtube_data_api_v3",
                "limitations": list(limitations),
            }
        ],
        "collection_frames": frames,
        "limitations": limitations,
    }
    summary = _empty_summary(run_id, comments)
    _write_bundle(output, manifest, posts, comments, summary)
    return {
        "contract_version": CONTRACT_VERSION,
        "run_id": run_id,
        "status": status,
        "coverage": coverage,
        "posts": len(posts),
        "comments": len(comments),
        "output": str(output.resolve()),
        "artifacts": [str((output / name).resolve()) for name in OUTPUT_FILES],
    }


def _configure(*, gui: bool = False) -> dict[str, Any]:
    if sys.platform != "darwin":
        raise CredentialError(
            "`configure` stores the key in macOS Keychain. Set YOUTUBE_API_KEY on this platform."
        )
    api_key = prompt_gui_api_key() if gui else _validate_api_key(
        getpass.getpass("YouTube Data API key (hidden): ")
    )
    check = YouTubeApi(api_key).check()
    storage = store_api_key(api_key)
    return {"configured": True, **storage, "check": check}


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Secure YouTube Data API access for tap-in."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    configure = commands.add_parser(
        "configure",
        help="Verify and store an API key in macOS Keychain.",
    )
    configure.add_argument(
        "--gui",
        action="store_true",
        help="Use a hidden native macOS input dialog.",
    )
    commands.add_parser("check", help="Verify public YouTube Data API access.")
    collect = commands.add_parser(
        "collect",
        help="Collect public video counters and comments into the v1 bundle.",
    )
    collect.add_argument(
        "--video-id",
        action="append",
        required=True,
        help="YouTube video ID; repeat for up to five videos.",
    )
    collect.add_argument("--output", type=Path, required=True)
    collect.add_argument("--subject", default="YouTube collection")
    collect.add_argument(
        "--top-level-only",
        action="store_true",
        help="Exclude replies; the default retrieves every accessible reply.",
    )
    collect.add_argument(
        "--max-comments",
        type=_positive_int,
        help="Optional total comment cap per video; default is full pagination.",
    )
    collect.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing contract artifacts in the output directory.",
    )
    return parser


def _print_json(payload: Mapping[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "configure":
            result = _configure(gui=args.gui)
        else:
            client = YouTubeApi(load_api_key())
            if args.command == "check":
                result = client.check()
            else:
                result = collect_to_directory(
                    client,
                    args.video_id,
                    args.output,
                    subject=args.subject,
                    include_replies=not args.top_level_only,
                    max_comments=args.max_comments,
                    overwrite=args.overwrite,
                )
        _print_json(result)
        return 0
    except (CredentialError, OutputExistsError, YouTubeApiError, ValueError) as error:
        print("error: {}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
