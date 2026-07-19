# Wikidata

## Capabilities

Resolve entity IDs, aliases, structured dates, external identifiers, and linked
official or reference pages.

## Use when

Disambiguate artists, releases, labels, countries, or dates; discover structured
links after an entity has been identified.

## Do not use for

Claiming complete discographies, release performance, current availability, or
an official statement merely because a URL appears in an item.

## Access

Use the public Wikidata Query Service for narrowly scoped SPARQL queries or the
MediaWiki Action API for small entity lookups; neither path requires an API key.
Follow the documented User-Agent, robot, concurrency, and retry guidance in
[Wikidata data access](https://www.wikidata.org/wiki/Wikidata:Data_access).

## Inputs and outputs

Start with labels, aliases, or a known QID. Retain the QID, labels and aliases,
statements and qualifiers used, external IDs, links, and retrieval date.

## Evidence

Authority tier: community-maintained structured reference data. Cite the item or
query result for entity-resolution support, then cite the linked official source
for material release or campaign claims.

## Limits and terms

Wikidata data can be incomplete, disputed, or changed by contributors. Do not
infer that a missing statement means the fact does not exist, and do not treat
structured links as proof of current platform availability.

## Fallbacks

Use [MusicBrainz](musicbrainz.md) for music-specific identity and official
artist, label, or retailer pages for material facts. Report unresolved identity
when sources do not converge.

## Verification

Confirm the QID against the artist's market, role, and dates; cross-check a
decision-critical fact with MusicBrainz or a direct official page.

Last verified: 2026-07-19
