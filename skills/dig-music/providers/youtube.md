# YouTube

## Capabilities

Resolve YouTube video and channel identity and observe current public video or
channel metadata and statistics.

## Use when

Verify an official video or channel, record its current public counters, or
collect published time, title, channel ID, video ID, and public statistics.

## Do not use for

Historical first-day or first-week metrics inferred from a current counter, or
YouTube Analytics data without the channel owner's authorized access.

## Access

Use the [YouTube Data API reference](https://developers.google.com/youtube/v3/docs)
with a Google project and API credentials. Every Data API request requires an API key or OAuth 2.0 token.
API-key access is limited to public data. Use OAuth for methods requiring user
authorization. Budget requests using the official [quota-cost guidance](https://developers.google.com/youtube/v3/determine_quota_cost).

For reusable public counters and comments, use the installed
`tap-in` helper with the official YouTube Data API as the
**mandatory first path**. Check access with
`python3 <tap-in-skill-directory>/scripts/youtube_api.py check`.
When credentials are missing, ask to connect with
`python3 <tap-in-skill-directory>/scripts/youtube_api.py configure --gui`.
Missing credentials, urgency, or an available browser do not authorize a
fallback. Use browser collection only after the user explicitly declines the
API or explicitly authorizes fallback following an API failure. Never ask the
user to paste the key into chat.

## Inputs and outputs

Search by official channel or video URL, channel ID, video ID, or title. Retain
the video/channel ID, canonical URL, title, channel, published time, requested
resource parts, public counters, and observation time.

## Evidence

Authority tier: provider-managed public observations, primary for the returned
public resource at the observation time. Cite the video/channel URL or recorded
API response and label counters as current observations.

## Limits and terms

Public counters change and do not reconstruct an earlier window. API requests
consume quota, including invalid requests; follow API policies and do not claim
owner-only analytics from public Data API fields.

## Fallbacks

Use an official video or channel page for supplementary, non-official context,
or for the bounded fallback only after the user explicitly declines the API or
authorizes fallback after an API failure. Mark unavailable historical metrics
as unavailable.

## Verification

Confirm the channel's official relationship, the exact video, and the time zone
and observation time. Keep video views, subscribers, and other distinct metrics
separate from chart, sales, or streaming measures.

Last verified: 2026-07-21
