# Instagram recipe

Use public rendered post pages in an available browser when authorization to the target account is unavailable. Do not use reverse-engineered private endpoints or bypass a login wall.

Follow the five-post total budget in `SKILL.md`; **do not reset** it to five Instagram posts.

## Collection path

1. Start from canonical official-account or post URLs. If no posts were supplied, use Instagram's allocation from the cross-platform budget, matching the requested campaign, content type, and period; record the rule and whether a pinned post affected discovery.
2. Open each post and capture caption, content type, publication display, canonical URL, and only the counters rendered to the current session.
3. Preserve abbreviated counters such as `1.2M` in `display_value`. Set exact numeric values only when the page exposes them; otherwise use `null`, `is_exact: false`, and `missing_reason`.
4. Expand or scroll comments in the platform's default visible order. Deduplicate observed comment IDs. Stop at 100 unique comments per post, a login/access gate, a rate limit, or three consecutive expansions with no new unique comments.
5. Record `sampling_method: instagram_default_visible_order`, achieved count, session state (`logged_out` or `existing_user_session` without identifiers), `observed_at`, and the stop reason.

## Interpretation

This is a ranked, visible-order **convenience sample**, not random sampling. The platform may rank, collapse, hide, translate, or remove comments, and the public comment counter may include replies or comments that are not rendered. Use `coverage: partial` unless an explicitly bounded visible frame was exhausted. Every hidden metric needs `missing_reason`; never replace it with zero.
