# Spotify

## Capabilities

Retrieve Spotify's credentialed artist, album, and track catalog metadata and
Spotify identifiers.

## Use when

Check a Spotify artist, album, or track record, search the Spotify catalog, or
collect platform-specific IDs and metadata after credentials are available.

## Do not use for

Sales, historical performance, universal availability, or comparisons that
assume Spotify catalog fields match another platform's catalog fields.

## Access

Create a Spotify app and obtain an access token through the documented
[Web API](https://developer.spotify.com/documentation/web-api) authorization
flow. Use client credentials for eligible app-only endpoints and user
authorization only when an endpoint requires a user's data or scopes; do not
ask for credentials when a fallback can close the request.

## Inputs and outputs

Search by artist, album, track, or Spotify URI/ID. Retain the returned Spotify
ID or URI, entity type, name, credited artists, release date and precision,
markets when supplied, and observation date.

## Evidence

Authority tier: provider-managed catalog metadata, primary for what Spotify
returns at the observation time. Cite the direct Spotify URL or recorded API
response and identify the market and observation date.

## Limits and terms

Catalog availability and returned fields can vary by market, authorization, and
time. Follow Spotify's documented scopes, rate limits, and developer terms; a
catalog record is not sales evidence or a historical popularity series.

## Fallbacks

Use [Apple Music](apple-music.md) for a platform cross-check and
[MusicBrainz](musicbrainz.md) for music-specific identity. Use an official
artist or label page for release facts.

## Verification

Verify that artist, edition, market, and release-date precision match the
question. Preserve platform provenance and keep Spotify-only observations
separate from incompatible metrics.

Last verified: 2026-07-19
