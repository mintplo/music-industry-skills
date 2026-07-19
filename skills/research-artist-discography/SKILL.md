---
name: research-artist-discography
description: Research an artist's full discography, release metadata, concepts, promotion, sales and chart evidence, and public social/video signals. Use when Codex is asked to investigate an artist's albums or comeback history, compare releases, build a sourced album timeline, or drill into one release within the artist's catalog.
---

# Research Artist Discography

Start from the artist name (아티스트 이름). Treat an album name as an optional filter or drill-down target, while preserving the 전체 디스코그래피.

## Workflow

1. Resolve the artist before collecting releases. Ask only when same-name candidates remain genuinely ambiguous.
2. Build the complete release inventory from at least two catalog sources when possible.
3. Include studio albums, EPs/mini albums, single albums, digital singles, and repackages by default.
4. Preserve member solos, features, OST tracks, live albums, compilations, and remix albums separately; exclude them from default comparisons unless requested.
5. Group country and format editions under a release group without deleting edition identifiers.
6. Collect current performance evidence from official sources first. Never estimate a missing number.
7. Collect release concepts and promotion from official introductions, press releases, artist channels, and attributable interviews; attach a source to every claim.
8. Collect YouTube and other accessible public signals with their observation time; report authenticated SNS data as unavailable when credentials are absent.
9. Apply period, release-type, latest-N, and album-name filters only after preserving the entire release inventory.
10. Keep facts, missing data, conflicts, and interpretation visibly separate.
11. Return the entire release inventory before reducing detail for a long discography.

Read `references/source-policy.md` before selecting or crawling sources. Read `references/data-schema.md` before combining observations or exporting JSON/CSV. Read `references/report-format.md` before composing the final brief or visualization.

Use `scripts/collect_discography_data.py` when deterministic catalog normalization is useful. Web research remains necessary for current chart evidence, concepts, promotion, and sources not implemented by the script.
