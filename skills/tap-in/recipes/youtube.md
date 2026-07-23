# YouTube recipe

Use the official YouTube Data API as the **mandatory first path**. Public read operations do not require control of the artist's channel. Use a browser fallback only after the user explicitly declines YouTube API use.

Follow the five-post total budget in `SKILL.md`; **do not reset** it to five YouTube posts.

## API-first routing

1. If the user already explicitly declined YouTube API use, skip credential checks and follow `Browser fallback`.
2. Otherwise run `youtube_api.py check`. When it succeeds, collect through the API.
3. When credentials are missing, explain that the API provides stable public counters and paginated comments, then ask to connect with `configure --gui`. Missing credentials, urgency, a request to avoid delays or questions, and public browser availability are not API refusal; do not start browser collection.
4. When an API request fails because of quota or another access condition, report the condition and ask whether to use the browser fallback. Do not switch paths without explicit user authorization.
5. Use `Browser fallback` only after the user explicitly declines the API or explicitly authorizes fallback after an API failure.

## API path

Use the bundled dependency-free helper from this skill's installed directory:

```bash
python3 <skill-directory>/scripts/youtube_api.py check
python3 <skill-directory>/scripts/youtube_api.py configure --gui
python3 <skill-directory>/scripts/youtube_api.py collect \
  --video-id VIDEO_ID \
  --subject "Artist or campaign" \
  --output OUTPUT_DIRECTORY
python3 <skill-directory>/scripts/validate_dataset.py OUTPUT_DIRECTORY
```

Run `check` first. Run `configure --gui` only when no credential is available and the user agrees to connect; it verifies the key before saving it to macOS Keychain. On non-macOS systems, provide `YOUTUBE_API_KEY` through the process environment. Never request or echo the key in chat, files, logs, or command arguments.

The macOS Keychain helper uses `xcrun swift`; if Command Line Tools are unavailable, ask the user to run `xcode-select --install`. When a native dialog cannot appear, have the user run `youtube_api.py configure` in their own Terminal so the key is entered through a hidden terminal prompt.

Repeat `--video-id` for up to five videos. The default collects all accessible top-level comments and replies. Use `--max-comments 100` only for an explicitly bounded sample, or `--top-level-only` only when replies are out of scope. Existing output artifacts are protected unless `--overwrite` is explicitly supplied.

The helper performs this protocol:

1. Resolve the canonical video ID and URL. Retrieve public post metadata and counters with `videos.list`; store the exact response observation time.
2. Call `commentThreads.list` with `part=snippet`, `videoId`, `maxResults=100`, `textFormat=plainText`, and `order=time`.
3. Follow every `nextPageToken` to enumerate published top-level comments. Mark `sampling_method: youtube_api_full_pagination` only after exhausting the token chain.
4. When replies are in scope, call `comments.list` with each top-level comment's `parentId`, `maxResults=100`, and every `nextPageToken`. Treat a fetched count below `totalReplyCount` as partial coverage.
5. Preserve already collected comments when a later page fails. Record `commentsDisabled`, permission errors, quota exhaustion, deleted videos, and transient failures as explicit status and stop reasons. A comment counter is not proof that all comments are retrievable.

API output is a collection bundle, not a finished sentiment analysis. Each comment initially has `coding_status: pending`, provisional `unclear`/low-confidence labels, and `reaction-summary.json` excludes those comments from the usable sentiment denominator. Apply `references/comment-coding.md`, replace the provisional labels, regenerate the summary, and validate again before downstream sentiment analysis.

For a very large video, estimate remaining pages, quota, storage, and run time before a long enumeration. If the bounded run stops early, use `coverage: partial`; do not call it all comments.

## Browser fallback

Capture only publicly rendered values. Expand comments until 100 unique comments, an access gate appears, or repeated attempts add no comments. Label the result `sampling_method: youtube_public_visible_order`, `coverage: partial`, and a **convenience sample**. Record `observed_at` for metrics and `missing_reason` for hidden or unavailable values.

## Caveats

- API pagination is a time-bounded observation; comments can be added, edited, hidden, or deleted during collection.
- Top-level comments and replies are different frames. Report both counts.
- Relevance order, time order, and browser-visible order are not interchangeable.
