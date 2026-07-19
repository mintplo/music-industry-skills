# Source Policy

## Priority

1. Official APIs, official charts, labels, distributors, and artist channels
2. Reliable press or two independent agreeing sources
3. Wikis and community-maintained pages as reference-only evidence

## Required evidence

For every number preserve source name, URL, market, period, observation time, measurement type, source tier, and a short evidence note. Report unavailable data as unavailable.

## Provider roles

- MusicBrainz: identifiers and release groups; respect one request per second and review commercial terms before company-scale use.
- Wikidata: CC0 identity and date cross-check; verify missing or mistyped K-pop records.
- Apple iTunes Search: no-key catalog cross-check; do not treat catalog fields as performance.
- Spotify: catalog and track-list support when credentials exist; do not rely on removed development-mode popularity fields.
- Circle Album Chart: shipments net of returns; keep separate from Circle Retail Album point-of-sale data. Treat the page's internal JSON route as undocumented and low-frequency only.
- Oricon: label public page values with exactly what the page exposes. Never infer sales from rank.
- YouTube Data API: public video/channel observations when a key exists; preserve collection time and quota limits.
- Instagram, TikTok, and X: do not make competitor data a credential-free requirement. Use official authenticated interfaces only when later authorized.
- NamuWiki and other wikis: reference-only, short evidence, original link, no bulk commercial corpus, no access-control bypass.

## Access rules

Honor robots directives, rate limits, `Retry-After`, login boundaries, and site terms. Prefer static HTML or official interfaces. Use browser rendering only when necessary. Never bypass Cloudflare or reuse a person's authenticated session.
