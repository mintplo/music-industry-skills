#!/usr/bin/env python3
"""Validate a tap-in/v1 dataset bundle."""

import argparse
from collections import Counter
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import sys


VERSION = "tap-in/v1"
FILES = (
    "collection-manifest.json",
    "posts.jsonl",
    "comments.jsonl",
    "reaction-summary.json",
)
ACCESS_STATUSES = {"supported", "access-dependent", "unavailable"}
COVERAGE_STATUSES = {"complete", "partial"}
METRIC_AVAILABILITIES = {"available", "access-dependent", "unavailable"}
ANALYSIS_VALUES = {
    "substantive",
    "affect_only",
    "off_topic",
    "duplicate",
    "promotional_spam",
    "suspected_automation",
    "unclear",
}
SENTIMENTS = {"positive", "negative", "mixed", "neutral", "unclear"}
CONFIDENCES = {"high", "medium", "low"}
CODING_STATUSES = {"pending", "complete"}
TOXICITY_FLAGS = {
    "abuse",
    "hate",
    "threat",
    "sexual_harassment",
    "privacy_exposure",
    "self_harm",
    "other",
}


def is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def is_nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def load_json(path, errors):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append("{}: {}".format(path.name, exc))
        return None
    if not isinstance(value, dict):
        errors.append("{}: root must be an object".format(path.name))
        return None
    return value


def load_jsonl(path, errors):
    records = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        errors.append("{}: {}".format(path.name, exc))
        return records
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append("{}:{}: {}".format(path.name, number, exc))
            continue
        if not isinstance(value, dict):
            errors.append("{}:{}: line must be an object".format(path.name, number))
            continue
        records.append((number, value))
    return records


def require_fields(record, fields, location, errors):
    for field in fields:
        if field not in record:
            errors.append("{}: missing {}".format(location, field))


def require_nonempty(record, fields, location, errors):
    for field in fields:
        if field in record and not is_nonempty_string(record[field]):
            errors.append("{}: {} must be a non-empty string".format(location, field))


def check_timestamp(value, location, errors, nullable=False):
    if value is None and nullable:
        return
    if not isinstance(value, str):
        errors.append("{}: must be an RFC 3339 UTC timestamp".format(location))
        return
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        errors.append("{}: must be an RFC 3339 UTC timestamp".format(location))
        return
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        errors.append("{}: timestamp must be UTC".format(location))


def check_common(record, location, run_id, errors):
    require_fields(record, ("contract_version", "run_id"), location, errors)
    if record.get("contract_version") != VERSION:
        errors.append("{}: contract_version must be {}".format(location, VERSION))
    if not is_nonempty_string(record.get("run_id")):
        errors.append("{}: run_id must be a non-empty string".format(location))
    if run_id is not None and record.get("run_id") != run_id:
        errors.append("{}: run_id does not match manifest".format(location))


def validate_manifest(manifest, errors):
    location = "collection-manifest.json"
    require_fields(
        manifest,
        (
            "contract_version",
            "run_id",
            "subject",
            "status",
            "coverage",
            "started_at",
            "completed_at",
            "platforms",
            "collection_frames",
            "limitations",
        ),
        location,
        errors,
    )
    check_common(manifest, location, None, errors)
    if manifest.get("status") not in ACCESS_STATUSES:
        errors.append("{}: invalid status".format(location))
    if manifest.get("coverage") not in COVERAGE_STATUSES:
        errors.append("{}: invalid coverage".format(location))
    if not isinstance(manifest.get("subject"), dict):
        errors.append("{}: subject must be an object".format(location))
    if not isinstance(manifest.get("limitations"), list):
        errors.append("{}: limitations must be an array".format(location))
    check_timestamp(manifest.get("started_at"), location + ":started_at", errors)
    check_timestamp(manifest.get("completed_at"), location + ":completed_at", errors)

    platforms = manifest.get("platforms")
    if not isinstance(platforms, list) or not platforms:
        errors.append("{}: platforms must be a non-empty array".format(location))
    else:
        seen = set()
        for index, platform in enumerate(platforms):
            item_location = "{}:platforms[{}]".format(location, index)
            if not isinstance(platform, dict):
                errors.append("{}: must be an object".format(item_location))
                continue
            require_fields(
                platform,
                ("platform", "status", "coverage", "collection_method", "limitations"),
                item_location,
                errors,
            )
            require_nonempty(platform, ("platform", "collection_method"), item_location, errors)
            name = platform.get("platform")
            if name in seen:
                errors.append("{}: duplicate platform".format(item_location))
            seen.add(name)
            if platform.get("status") not in ACCESS_STATUSES:
                errors.append("{}: invalid status".format(item_location))
            if platform.get("coverage") not in COVERAGE_STATUSES:
                errors.append("{}: invalid coverage".format(item_location))
            if not isinstance(platform.get("limitations"), list):
                errors.append("{}: limitations must be an array".format(item_location))

    frames = manifest.get("collection_frames")
    if not isinstance(frames, list) or not frames:
        errors.append("{}: collection_frames must be a non-empty array".format(location))


def validate_posts(records, run_id, errors):
    post_ids = set()
    required = (
        "contract_version",
        "run_id",
        "platform",
        "post_id",
        "canonical_url",
        "published_at",
        "observed_at",
        "collection_method",
        "content_type",
        "text",
        "metrics",
    )
    for number, post in records:
        location = "posts.jsonl:{}".format(number)
        require_fields(post, required, location, errors)
        check_common(post, location, run_id, errors)
        require_nonempty(
            post,
            ("platform", "post_id", "canonical_url", "collection_method", "content_type"),
            location,
            errors,
        )
        if "text" in post and not isinstance(post["text"], str):
            errors.append("{}: text must be a string".format(location))
        check_timestamp(post.get("published_at"), location + ":published_at", errors, nullable=True)
        check_timestamp(post.get("observed_at"), location + ":observed_at", errors)
        key = (post.get("platform"), post.get("post_id"))
        if all(is_nonempty_string(value) for value in key):
            if key in post_ids:
                errors.append("{}: duplicate platform/post_id".format(location))
            post_ids.add(key)
        metrics = post.get("metrics")
        if not isinstance(metrics, dict):
            errors.append("{}: metrics must be an object".format(location))
            continue
        if not metrics:
            errors.append("{}: metrics must contain at least one metric attempt".format(location))
        for name, metric in metrics.items():
            metric_location = "{}:metrics.{}".format(location, name)
            if not is_nonempty_string(name):
                errors.append("{}: metric name must be non-empty".format(metric_location))
            if not isinstance(metric, dict):
                errors.append("{}: must be an object".format(metric_location))
                continue
            require_fields(
                metric,
                (
                    "value",
                    "display_value",
                    "is_exact",
                    "observed_at",
                    "availability",
                    "source_url",
                ),
                metric_location,
                errors,
            )
            check_timestamp(metric.get("observed_at"), metric_location + ":observed_at", errors)
            if not is_nonempty_string(metric.get("source_url")):
                errors.append("{}: source_url must be a non-empty string".format(metric_location))
            availability = metric.get("availability")
            if availability not in METRIC_AVAILABILITIES:
                errors.append("{}: invalid availability".format(metric_location))
            value = metric.get("value")
            display_value = metric.get("display_value")
            is_exact = metric.get("is_exact")
            if value is not None and not is_count(value):
                errors.append("{}: value must be a non-negative integer or null".format(metric_location))
            if display_value is not None and not isinstance(display_value, str):
                errors.append("{}: display_value must be a string or null".format(metric_location))
            if is_exact is not None and not isinstance(is_exact, bool):
                errors.append("{}: is_exact must be a boolean or null".format(metric_location))
            if value is None and not is_nonempty_string(metric.get("missing_reason")):
                errors.append("{}: missing_reason is required when value is null".format(metric_location))
            if value is not None and is_exact is not True:
                errors.append("{}: numeric value requires is_exact true".format(metric_location))
            if value is None and availability == "available" and display_value and is_exact is not False:
                errors.append("{}: display-only metric requires is_exact false".format(metric_location))
            if value is None and availability in {"access-dependent", "unavailable"} and is_exact is not None:
                errors.append("{}: unavailable metric requires is_exact null".format(metric_location))
            if availability == "available" and value is None and not display_value:
                errors.append("{}: available metric requires value or display_value".format(metric_location))
            if availability in {"access-dependent", "unavailable"} and value is not None:
                errors.append("{}: unavailable metric value must be null".format(metric_location))
    return post_ids


def validate_comments(records, run_id, post_ids, errors):
    required = (
        "contract_version",
        "run_id",
        "platform",
        "post_id",
        "comment_id",
        "parent_comment_id",
        "text",
        "published_at",
        "observed_at",
        "sample_rank",
        "sampling_method",
        "source_url",
        "coding_status",
        "labels",
    )
    comment_ids = set()
    for number, comment in records:
        location = "comments.jsonl:{}".format(number)
        require_fields(comment, required, location, errors)
        check_common(comment, location, run_id, errors)
        for path in prohibited_commenter_identity_paths(comment):
            errors.append(
                "{}:{}: raw commenter identity/profile field is prohibited".format(
                    location,
                    path,
                )
            )
        require_nonempty(
            comment,
            ("platform", "post_id", "comment_id", "text", "sampling_method", "source_url"),
            location,
            errors,
        )
        check_timestamp(comment.get("published_at"), location + ":published_at", errors, nullable=True)
        check_timestamp(comment.get("observed_at"), location + ":observed_at", errors)
        post_key = (comment.get("platform"), comment.get("post_id"))
        if post_key not in post_ids:
            errors.append("{}: references an unknown post".format(location))
        comment_key = (comment.get("platform"), comment.get("comment_id"))
        if all(is_nonempty_string(value) for value in comment_key):
            if comment_key in comment_ids:
                errors.append("{}: duplicate platform/comment_id".format(location))
            comment_ids.add(comment_key)
        if not isinstance(comment.get("sample_rank"), int) or isinstance(comment.get("sample_rank"), bool) or comment.get("sample_rank", 0) < 1:
            errors.append("{}: sample_rank must be a positive integer".format(location))
        coding_status = comment.get("coding_status")
        if coding_status not in CODING_STATUSES:
            errors.append("{}: invalid coding_status".format(location))
        labels = comment.get("labels")
        if not isinstance(labels, dict):
            errors.append("{}: labels must be an object".format(location))
            continue
        require_fields(
            labels,
            ("analysis_value", "sentiment", "toxicity", "confidence"),
            location + ":labels",
            errors,
        )
        analysis_value = labels.get("analysis_value")
        sentiment = labels.get("sentiment")
        confidence = labels.get("confidence")
        if not isinstance(analysis_value, str) or analysis_value not in ANALYSIS_VALUES:
            errors.append("{}: invalid analysis_value".format(location))
        if not isinstance(sentiment, str) or sentiment not in SENTIMENTS:
            errors.append("{}: invalid sentiment".format(location))
        if not isinstance(confidence, str) or confidence not in CONFIDENCES:
            errors.append("{}: invalid confidence".format(location))
        toxicity = labels.get("toxicity")
        if not isinstance(toxicity, list) or any(
            not isinstance(flag, str) or flag not in TOXICITY_FLAGS
            for flag in toxicity
        ):
            errors.append("{}: invalid toxicity flags".format(location))
        elif len(toxicity) != len(set(toxicity)):
            errors.append("{}: toxicity flags must be unique".format(location))
        if coding_status == "pending" and (
            analysis_value != "unclear"
            or sentiment != "unclear"
            or confidence != "low"
            or toxicity != []
        ):
            errors.append("{}: pending comment requires provisional labels".format(location))


def prohibited_commenter_identity_paths(value, prefix=""):
    if isinstance(value, dict):
        for field, nested in value.items():
            path = "{}.{}".format(prefix, field) if prefix else field
            normalized = re.sub(r"[^a-z0-9]+", "", field.casefold())
            identity_field = (
                normalized.startswith("author")
                or "profile" in normalized
                or normalized
                in {
                    "username",
                    "userdisplayname",
                    "userhandle",
                    "handle",
                    "avatar",
                    "avatarurl",
                }
            )
            if identity_field and "hash" not in normalized:
                yield path
            else:
                yield from prohibited_commenter_identity_paths(nested, path)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            path = "{}[{}]".format(prefix, index)
            yield from prohibited_commenter_identity_paths(nested, path)


def valid_labels(comment):
    labels = comment.get("labels")
    return labels if isinstance(labels, dict) else {}


def validate_collection_frames(manifest, post_ids, comments, errors):
    frames = manifest.get("collection_frames")
    platforms = manifest.get("platforms")
    if not isinstance(frames, list) or not isinstance(platforms, list):
        return
    declared_platforms = {
        item.get("platform")
        for item in platforms
        if isinstance(item, dict) and is_nonempty_string(item.get("platform"))
    }
    comment_counts = Counter()
    for _, comment in comments:
        key = (comment.get("platform"), comment.get("post_id"))
        level = "reply" if comment.get("parent_comment_id") is not None else "top"
        comment_counts[(key, level)] += 1

    frame_ids = set()
    framed_posts = set()
    frame_platforms = set()
    required = (
        "frame_id",
        "platform",
        "post_id",
        "requested_url",
        "status",
        "coverage",
        "sampling_method",
        "target_comments",
        "achieved_top_level_comments",
        "achieved_reply_comments",
        "stop_reason",
        "observed_at",
    )
    for index, frame in enumerate(frames):
        location = "collection-manifest.json:collection_frames[{}]".format(index)
        if not isinstance(frame, dict):
            errors.append("{}: must be an object".format(location))
            continue
        require_fields(frame, required, location, errors)
        require_nonempty(frame, ("frame_id", "platform", "requested_url", "sampling_method"), location, errors)
        frame_id = frame.get("frame_id")
        if frame_id in frame_ids:
            errors.append("{}: duplicate frame_id".format(location))
        frame_ids.add(frame_id)
        platform = frame.get("platform")
        frame_platforms.add(platform)
        if platform not in declared_platforms:
            errors.append("{}: platform is not declared".format(location))
        status = frame.get("status")
        coverage = frame.get("coverage")
        if status not in ACCESS_STATUSES:
            errors.append("{}: invalid status".format(location))
        if coverage not in COVERAGE_STATUSES:
            errors.append("{}: invalid coverage".format(location))
        if status in {"access-dependent", "unavailable"} and coverage == "complete":
            errors.append("{}: non-supported frame coverage must be partial".format(location))
        target = frame.get("target_comments")
        if target is not None and not is_count(target):
            errors.append("{}: target_comments must be a non-negative integer or null".format(location))
        for field in ("achieved_top_level_comments", "achieved_reply_comments"):
            if not is_count(frame.get(field)):
                errors.append("{}: {} must be a non-negative integer".format(location, field))
        if coverage == "partial" and not is_nonempty_string(frame.get("stop_reason")):
            errors.append("{}: partial coverage requires stop_reason".format(location))
        if frame.get("stop_reason") is not None and not isinstance(frame.get("stop_reason"), str):
            errors.append("{}: stop_reason must be a string or null".format(location))
        check_timestamp(frame.get("observed_at"), location + ":observed_at", errors)

        post_id = frame.get("post_id")
        if post_id is not None and not is_nonempty_string(post_id):
            errors.append("{}: post_id must be a non-empty string or null".format(location))
            continue
        top = frame.get("achieved_top_level_comments")
        replies = frame.get("achieved_reply_comments")
        if post_id is None:
            if (is_count(top) and top) or (is_count(replies) and replies):
                errors.append("{}: frame without post_id cannot have achieved comments".format(location))
            continue
        post_key = (platform, post_id)
        if post_key in framed_posts:
            errors.append("{}: duplicate platform/post_id frame".format(location))
        framed_posts.add(post_key)
        if post_key not in post_ids:
            errors.append("{}: post_id has no posts.jsonl observation".format(location))
        if is_count(top) and top != comment_counts[(post_key, "top")]:
            errors.append("{}: achieved_top_level_comments must equal {}".format(location, comment_counts[(post_key, "top")]))
        if is_count(replies) and replies != comment_counts[(post_key, "reply")]:
            errors.append("{}: achieved_reply_comments must equal {}".format(location, comment_counts[(post_key, "reply")]))

    for post_key in post_ids - framed_posts:
        errors.append("collection-manifest.json: collection_frames missing post {}:{}".format(*post_key))
    for platform in declared_platforms - frame_platforms:
        errors.append("collection-manifest.json: collection_frames missing platform {}".format(platform))


def validate_status_semantics(manifest, post_ids, errors):
    observed_platforms = {platform for platform, _ in post_ids}
    status = manifest.get("status")
    if status == "supported" and not post_ids:
        errors.append("collection-manifest.json: supported status requires at least one post observation")
    if status in {"access-dependent", "unavailable"} and post_ids:
        errors.append("collection-manifest.json: observed posts require supported status")

    platforms = manifest.get("platforms")
    frames = manifest.get("collection_frames")
    if not isinstance(platforms, list) or not isinstance(frames, list):
        return
    for index, platform in enumerate(platforms):
        if not isinstance(platform, dict):
            continue
        name = platform.get("platform")
        item_location = "collection-manifest.json:platforms[{}]".format(index)
        has_observation = name in observed_platforms
        if platform.get("status") == "supported" and not has_observation:
            errors.append("{}: supported status requires a post observation".format(item_location))
        if platform.get("status") in {"access-dependent", "unavailable"} and has_observation:
            errors.append("{}: observed posts require supported status".format(item_location))
        platform_frames = [frame for frame in frames if isinstance(frame, dict) and frame.get("platform") == name]
        any_partial = any(frame.get("coverage") == "partial" for frame in platform_frames)
        if platform.get("coverage") == "complete" and any_partial:
            errors.append("{}: complete coverage conflicts with partial frame".format(item_location))
        if platform.get("coverage") == "partial" and platform_frames and not any_partial:
            errors.append("{}: partial coverage requires a partial frame".format(item_location))
    any_partial = any(isinstance(frame, dict) and frame.get("coverage") == "partial" for frame in frames)
    if manifest.get("coverage") == "complete" and any_partial:
        errors.append("collection-manifest.json: complete coverage conflicts with partial frame")
    if manifest.get("coverage") == "partial" and frames and not any_partial:
        errors.append("collection-manifest.json: partial coverage requires a partial frame")


def validate_count_map(actual, allowed, expected, location, errors):
    if not isinstance(actual, dict):
        errors.append("{}: must be an object".format(location))
        return
    unknown = set(actual) - set(allowed)
    for name in sorted(unknown):
        errors.append("{}: unknown label {}".format(location, name))
    for name in sorted(allowed):
        if name not in actual:
            errors.append("{}: missing {}".format(location, name))
            continue
        if not is_count(actual[name]):
            errors.append("{}.{}: must be a non-negative integer".format(location, name))
            continue
        if actual[name] != expected.get(name, 0):
            errors.append("{}.{} must equal {}".format(location, name, expected.get(name, 0)))


def validate_summary(summary, run_id, comments, errors):
    location = "reaction-summary.json"
    require_fields(
        summary,
        ("contract_version", "run_id", "counts", "sentiment", "analysis_value", "toxicity", "limitations"),
        location,
        errors,
    )
    check_common(summary, location, run_id, errors)
    if not isinstance(summary.get("limitations"), list):
        errors.append("{}: limitations must be an array".format(location))

    analysis = Counter()
    sentiment = Counter()
    toxicity = Counter()
    usable = 0
    for _, comment in comments:
        labels = valid_labels(comment)
        analysis_value = labels.get("analysis_value")
        if isinstance(analysis_value, str) and analysis_value in ANALYSIS_VALUES:
            analysis[analysis_value] += 1
        coding_complete = comment.get("coding_status") == "complete"
        if coding_complete and isinstance(analysis_value, str) and analysis_value in {"substantive", "affect_only"}:
            usable += 1
            sentiment_value = labels.get("sentiment")
            if isinstance(sentiment_value, str) and sentiment_value in SENTIMENTS:
                sentiment[sentiment_value] += 1
        flags = labels.get("toxicity") if coding_complete else []
        if isinstance(flags, list):
            for flag in flags:
                if isinstance(flag, str) and flag in TOXICITY_FLAGS:
                    toxicity[flag] += 1

    expected_counts = {
        "collected": len(comments),
        "usable": usable,
        "excluded": len(comments) - usable,
    }
    validate_count_map(summary.get("counts"), expected_counts, expected_counts, location + ":counts", errors)
    validate_count_map(summary.get("sentiment"), SENTIMENTS, sentiment, location + ":sentiment", errors)
    validate_count_map(summary.get("analysis_value"), ANALYSIS_VALUES, analysis, location + ":analysis_value", errors)
    validate_count_map(summary.get("toxicity"), TOXICITY_FLAGS, toxicity, location + ":toxicity", errors)


def validate_dataset(root):
    errors = []
    for filename in FILES:
        if not (root / filename).is_file():
            errors.append("{}: required file is missing".format(filename))
    if errors:
        return errors, 0, 0
    manifest = load_json(root / FILES[0], errors)
    posts = load_jsonl(root / FILES[1], errors)
    comments = load_jsonl(root / FILES[2], errors)
    summary = load_json(root / FILES[3], errors)
    if manifest is None or summary is None:
        return errors, len(posts), len(comments)
    validate_manifest(manifest, errors)
    run_id = manifest.get("run_id")
    post_ids = validate_posts(posts, run_id, errors)
    validate_comments(comments, run_id, post_ids, errors)
    validate_collection_frames(manifest, post_ids, comments, errors)
    validate_status_semantics(manifest, post_ids, errors)
    validate_summary(summary, run_id, comments, errors)
    return errors, len(posts), len(comments)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="directory containing the four contract files")
    args = parser.parse_args()
    errors, post_count, comment_count = validate_dataset(args.dataset)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("valid: {} posts, {} comments".format(post_count, comment_count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
