# Web Search

## Capabilities

Discover official artist, label, platform, chart, press-release, and reputable reporting pages relevant to a question.

## Use when

Find primary sources, current reporting, publication dates, campaign material, or a direct page for a cited claim.

## Do not use for

Treating search snippets, result rankings, or an unsourced aggregator as final evidence.

## Access

Use the active runtime's web tool when available; otherwise state that discovery
is access-dependent and use supplied links. When the runtime is OpenAI-based,
consult the current [web-search guidance](https://developers.openai.com/api/docs/guides/tools-web-search),
but do not assume that every runtime exposes the same interface.

## Inputs and outputs

Query with the entity, market, date range, and claim type; retain the direct page URL, publisher, publication date, and access date.

## Evidence

Authority tier: discovery only; authority belongs to the direct source found.
Prefer primary and official pages, check dates before relying on current claims,
and cite the direct supporting link rather than a search-results page.

## Limits and terms

Respect the active tool's access limits and site terms. Web search is a discovery path, not a vendor API contract.

## Fallbacks

Search official domains directly, use corroborated press when no primary page exists, or mark the claim unavailable.

## Verification

Open the direct source, verify that it supports the stated claim, and preserve any market, period, and observation-date qualifiers.

Last verified: 2026-07-19
