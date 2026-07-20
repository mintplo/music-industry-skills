# MusicBrainz

## Capabilities

Identify artists, recordings, release groups, releases, labels, and stable MusicBrainz IDs.

## Use when

Resolve an artist or release and distinguish a release group from a particular edition.

## Do not use for

Current chart, sales, campaign, social, or editorial claims.

## Access

Use the public [MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API) through an available tool or HTTP client. Identify the client with a meaningful User-Agent.

For complete, deterministic catalog normalization, the optional collector at
`skills/dig-music/scripts/collect_discography_data.py` can normalize
MusicBrainz release groups with catalog cross-checks. It is not required for
ordinary research.

## Inputs and outputs

Search names, titles, dates, and existing MBIDs; retain returned artist, release-group, release, and recording MBIDs with title, date, country, and type fields.

## Evidence

Authority tier: community-maintained reference metadata. Cite the relevant
MusicBrainz entity page or API result for identification, and corroborate
material release facts with an official source when possible.

## Limits and terms

Follow the documented [rate limits](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting), including the public-service request guidance; do not treat community metadata as an official performance source.

## Fallbacks

Use official artist, label, distributor, or retailer pages; if identity remains ambiguous, report it as unresolved.

## Verification

Cross-check names, dates, and editions against the requested market and an official source when the distinction affects the answer.

Last verified: 2026-07-19
