# TikTok recipe

Use public rendered video pages in an available browser when no suitable authorized API is configured. Do not use undocumented private endpoints, evade access controls, or claim complete comment coverage from the rendered list.

Follow the five-post total budget in `SKILL.md`; **do not reset** it to five TikTok posts.

## Collection path

1. Resolve canonical official-account or video URLs. If videos were not supplied, use TikTok's allocation from the cross-platform budget and match the requested campaign and period; document discovery and selection.
2. Capture caption, video URL and ID, publication display, content type, and rendered view, like, comment, share, or save counters. Keep platform-specific metric names.
3. Store the displayed counter and exactness separately. Every metric observation requires `observed_at`; every unavailable value requires `missing_reason`.
4. Open the comments panel and collect unique comments in the default visible order. Stop at 100 unique comments per post, an access gate, a rate limit, or three consecutive expansions with no new unique comments.
5. Record `sampling_method: tiktok_default_visible_order`, achieved count, session state without identifiers, and the stop reason. Record replies only when requested and keep their parent IDs.

## Interpretation

The rendered list is a ranked **convenience sample** affected by session, locale, moderation, deletion, and platform ranking. A displayed comment count does not prove that the same number is retrievable. Use `coverage: partial` whenever the population is unknown or collection stops at the cap. Do not compare TikTok views or plays directly with another platform without a separate metric-compatibility rule.
