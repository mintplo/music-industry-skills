# Data contract: `tap-in/v1`

Write UTF-8 JSON with RFC 3339 UTC timestamps. Keep `contract_version` and `run_id` identical across every record. Preserve source-platform identifiers as strings.

## `collection-manifest.json`

Required top-level fields:

| Field | Shape | Meaning |
|---|---|---|
| `contract_version` | string | Always `tap-in/v1` |
| `run_id` | string | Unique collection run identifier |
| `subject` | object | Canonical name, aliases, and seed URLs |
| `status` | enum | `supported`, `access-dependent`, or `unavailable` |
| `coverage` | enum | `complete` or `partial` |
| `started_at`, `completed_at` | timestamp | Run boundaries |
| `platforms` | array | Per-platform method, status, coverage, and limitations |
| `collection_frames` | array | One result for every requested or selected post |
| `limitations` | array | Run-level sampling and access limitations |

Each platform entry contains `platform`, `status`, `coverage`, `collection_method`, and `limitations`. Add requested scope, post-selection rule, locale, browser session state, and API quota facts when applicable. Never store tokens, cookies, or session identifiers.

Each `collection_frames` entry requires `frame_id`, `platform`, nullable `post_id`, `requested_url`, `status`, `coverage`, `sampling_method`, nullable `target_comments`, `achieved_top_level_comments`, `achieved_reply_comments`, nullable `stop_reason`, and `observed_at`. Use one frame per requested or selected post, including posts blocked before an observation could be written. Partial frames require a stop reason. Achieved counts must match `comments.jsonl`.

## `posts.jsonl`

One object per observed post:

```json
{"contract_version":"tap-in/v1","run_id":"run-1","platform":"instagram","post_id":"abc","canonical_url":"https://www.instagram.com/p/abc/","published_at":null,"observed_at":"2026-07-21T00:00:00Z","collection_method":"public_browser","content_type":"reel","text":"caption","metrics":{"views":{"value":null,"display_value":null,"is_exact":null,"observed_at":"2026-07-21T00:00:00Z","availability":"unavailable","source_url":"https://www.instagram.com/p/abc/","missing_reason":"not_publicly_displayed"}}}
```

Required fields are those shown, and `metrics` must contain at least one attempted counter. A metric object contains `value`, `display_value`, `is_exact`, `observed_at`, `availability`, and `source_url`. `availability` is `available`, `access-dependent`, or `unavailable`. A numeric value is an exact non-negative integer and requires `is_exact: true`. When `value` is `null`, require `missing_reason`. Preserve `1.2M` in `display_value`, set `is_exact: false`, and use `missing_reason: exact_value_not_public`; do not silently treat it as an exact integer. A fully unavailable or access-dependent metric uses `value: null` and `is_exact: null`. Keep platform-specific measurements such as views, plays, likes, shares, saves, and comments separate.

## `comments.jsonl`

One object per observed top-level comment or reply:

```json
{"contract_version":"tap-in/v1","run_id":"run-1","platform":"youtube","post_id":"video-1","comment_id":"comment-1","parent_comment_id":null,"text":"The chorus is great","published_at":"2026-07-20T10:00:00Z","observed_at":"2026-07-21T00:00:00Z","sample_rank":1,"sampling_method":"youtube_api_full_pagination","source_url":"https://www.youtube.com/watch?v=video-1","coding_status":"complete","labels":{"analysis_value":"substantive","sentiment":"positive","toxicity":[],"confidence":"high"}}
```

Required fields are those shown. `sample_rank` is one-based within the post and sampling frame. `coding_status` is `pending` or `complete`. A pending record must retain provisional `unclear` analysis and sentiment, no toxicity flags, and low confidence; it is excluded from the usable sentiment denominator. If the platform exposes no stable comment ID, derive a deterministic digest without publishing the raw author handle. Do not store raw author names, handles, channel IDs, profile URLs, avatars, or profile objects; only a one-way `author_key_hash` is allowed when deduplication requires it. Add `like_count`, `language`, `reply_depth`, or coding provenance when observed or needed.

## `reaction-summary.json`

Required fields:

```json
{"contract_version":"tap-in/v1","run_id":"run-1","counts":{"collected":100,"usable":81,"excluded":19},"sentiment":{"positive":60,"negative":10,"mixed":4,"neutral":5,"unclear":2},"analysis_value":{"substantive":30,"affect_only":51,"off_topic":4,"duplicate":3,"promotional_spam":8,"suspected_automation":2,"unclear":2},"toxicity":{"abuse":1,"hate":0,"threat":0,"sexual_harassment":0,"privacy_exposure":0,"self_harm":0,"other":0},"limitations":["Visible-order convenience sample"]}
```

Include every defined sentiment, analysis-value, and toxicity key, using zero when absent. Compute sentiment only across usable comments. Compute `usable` from `substantive + affect_only`; compute `excluded` as `collected - usable`. The validator reconciles all breakdowns with `comments.jsonl`. Report raw count and denominator next to any rate. Provide results per platform and post in optional nested breakdowns rather than pooling unlike sampling frames without disclosure.

## Status semantics

- `supported`: at least one requested observation was collected through an allowed path.
- `access-dependent`: requested observations require unavailable credentials or a platform gate.
- `unavailable`: the content does not exist, is private/deleted, comments are disabled, or no allowed path exists.
- `complete`: the explicitly bounded requested frame was exhausted.
- `partial`: a cap, gate, rate limit, rendering failure, or unknown population prevented exhaustion.

An overall run may be `supported` and `partial`. Record gaps rather than converting missing observations to zero.
