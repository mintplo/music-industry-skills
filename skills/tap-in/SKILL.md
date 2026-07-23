---
name: tap-in
description: Use when a task or another skill needs reusable public post metadata, engagement counters, comments, sentiment, noise or spam, suspected automation, or toxicity signals from YouTube, Instagram, or TikTok.
---

# Tap In

Create a source-backed observation dataset for downstream analysis. Keep collection, comment coding, and interpretation separable; this skill returns data and coverage limits rather than a polished research report.

## Required brief

Establish these values from the request or existing research context:

- subject and canonical account or post URLs
- requested platforms, market or language, and time window
- post-selection rule and whether replies are in scope
- output directory

Resolve ambiguous identities before collection. Reuse a caller's resolved entities instead of resolving them again.

## Default sampling

- When the user supplies post URLs, collect those posts.
- Otherwise select up to **5 posts total across all requested platforms** that directly match the event, campaign, or period. Include at least one per requested platform when available, then allocate the remainder by relevance; record the selection rule.
- For Instagram and TikTok, target **100 comments per post** in the platform's visible default order.
- For YouTube, use the official YouTube Data API as the **mandatory first path** and enumerate all accessible published top-level comments and requested replies. Missing credentials, urgency, or public browser access does not authorize fallback. Use a clearly labeled public-browser convenience sample of up to **100 comments per post** only after the user explicitly declines YouTube API use or explicitly authorizes fallback following an API failure.
- Treat fewer than 30 accessible comments per comparison cell as qualitative-only. Treat 30–49 as a weak directional read, 50–99 as exploratory, and 100 as a useful descriptive sample—not a representative population estimate.

Do not redistribute one post's shortfall to imply balanced coverage elsewhere. Report achieved counts by platform and post.

## Workflow

1. Read [`references/data-contract.md`](references/data-contract.md) and create a `tap-in/v1` run manifest before collecting.
2. Read only the requested platform recipes: [`recipes/youtube.md`](recipes/youtube.md), [`recipes/instagram.md`](recipes/instagram.md), or [`recipes/tiktok.md`](recipes/tiktok.md). For YouTube, follow its API-first routing. Unless the user already explicitly declined the API, run `python3 <skill-directory>/scripts/youtube_api.py check`; if credentials are missing, explain the benefit and ask to connect with `python3 <skill-directory>/scripts/youtube_api.py configure --gui`. Do not silently switch to a browser. Never ask for the key in chat.
3. Capture post text, public counters, source URLs, and observation timestamps. For YouTube, use `python3 <skill-directory>/scripts/youtube_api.py collect ...` as specified in its recipe. Preserve abbreviated display values. Store an unavailable value as `null` with `missing_reason`, never as zero.
4. Capture comments using the recipe's explicit sampling method and stop reason. Never describe a ranked or visible-first sample as random.
5. Read [`references/comment-coding.md`](references/comment-coding.md), then code analysis value, sentiment, and toxicity on independent axes. YouTube API output starts with provisional `coding_status: pending`; replace provisional labels and regenerate the summary before treating the bundle as analyzed.
6. Produce the four contract files and run `python3 <skill-directory>/scripts/validate_dataset.py <output-directory>` using this skill's installed directory. Fix every validation error before returning the bundle.

## Access rules

- Prefer official APIs when they expose the requested public data. For YouTube, the official API is the mandatory first path; use browser fallback only after the user explicitly declines it or explicitly authorizes fallback following an API failure. For other platforms, use an available browser for public rendered pages when authentication to the target account is unavailable.
- Do not request the user to paste secrets. Use configured credentials only after checking availability non-interactively.
- Do not bypass login walls, CAPTCHAs, robots controls, rate limits, private accounts, or platform access controls. Do not use undocumented private endpoints.
- Stop repeated browser expansion after the platform blocks access or no new unique comments appear. Record the exact stop reason.
- Collect only fields needed for the analysis. Do not collect profile photos, bios, follower graphs, or other commenter profile data. Hash a public author key only when deduplication requires it.

## Output contract

Return these four required reusable artifacts:

- `collection-manifest.json` — request, methods, coverage, access status, and limitations
- `posts.jsonl` — one normalized post observation per line
- `comments.jsonl` — one normalized comment and its independent labels per line
- `reaction-summary.json` — descriptive counts and denominators derived from the JSONL files

Use `supported`, `access-dependent`, or `unavailable` for access status and `complete` or `partial` for coverage. A login wall with a visible comment counter is partial/access-dependent, not zero comments.

## Completion criteria

- Every requested platform and post is represented by observations or an explicit coverage gap.
- Every counter has a source URL and `observed_at`; every missing counter has `missing_reason`.
- Every comment records its sampling method and rank.
- Negative substantive criticism and lightweight fan reactions remain in the usable denominator; spam, off-topic content, duplicates, and suspected automation remain in raw exposure counts but are excluded from primary sentiment.
- The handoff states that public visible comments are a convenience sample and does not generalize percentages to the platform population.

When invoked by another skill, return the four artifact paths, contract version, run status, achieved sample counts, and limitations so the caller can continue without depending on this skill's internal files.
