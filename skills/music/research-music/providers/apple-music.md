# Apple Music and iTunes Search

## Capabilities

Cross-check artist, album, track, and music-video catalog records through the
no-key iTunes Search API; use Apple Music catalog records when an appropriate
Apple Music developer token is available.

## Use when

Find or confirm an iTunes Store catalog record, map a known iTunes identifier,
or check Apple Music catalog metadata in a requested storefront.

## Do not use for

Sales, chart performance, a historical performance series, or assuming a
catalog field establishes availability in every storefront.

## Access

Use the public iTunes Search or Lookup URL described in Apple's
[Search API documentation](https://performance-partners.apple.com/search-api)
without a MusicKit token. Apple Music API requests require the appropriate
developer token described in the [Apple Music API documentation](https://developer.apple.com/documentation/applemusicapi);
do not attempt tokenless access to protected endpoints.

## Inputs and outputs

Search by term or use lookup identifiers and record the storefront, collection
or track ID, artist ID, entity kind, name, artist name, release date, explicit
flag, preview or URL when returned, and observation date.

## Evidence

Authority tier: provider-managed catalog metadata, primary for the returned
Apple/iTunes record at the observation time. Cite the direct storefront URL or
recorded API response and retain the storefront.

## Limits and terms

The Search API documentation lists an approximate request limit that can change;
use it at low volume and follow Apple's terms. Catalog identity and availability
vary by storefront and time, and catalog fields are not sales or performance
evidence.

## Fallbacks

Use [MusicBrainz](musicbrainz.md) for release identity and
[Spotify](spotify.md) for a separate platform catalog check. Use official artist
or label pages when access to Apple Music is unavailable.

## Verification

Check entity type, edition, storefront, release-date precision, and credited
artist. Do not compare an Apple catalog observation to a platform metric as if
they measured the same thing.

Last verified: 2026-07-19
