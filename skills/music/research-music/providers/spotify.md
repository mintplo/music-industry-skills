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

Spotify currently requires the app owner to have an active Spotify Premium account
in development mode. Create an app in the
[Spotify developer dashboard](https://developer.spotify.com/dashboard), then
use Client Credentials to obtain a short-lived access token for public catalog
research. User authorization is not needed for the artist, album, and track
searches supported here.

From this skill directory, configure the included standard-library adapter:

```bash
python3 scripts/spotify_api.py configure
python3 scripts/spotify_api.py check
python3 scripts/spotify_api.py search artist "CORTIS" --market KR
python3 scripts/spotify_api.py search album "CORTIS" --market KR --limit 10
```

`spotify_api.py configure` prompts for the app Client ID and a hidden Client
Secret, stores both in **macOS Keychain**, and immediately verifies token and
catalog access. Never paste the secret into a research prompt or commit it to
the repository. Environment variables take precedence when automation needs
them:

```bash
export SPOTIFY_CLIENT_ID="..."
export SPOTIFY_CLIENT_SECRET="..."
python3 scripts/spotify_api.py check
```

On non-macOS systems, provide both environment variables. Providing only one
fails closed rather than falling back to another credential source.

## Inputs and outputs

Search by artist, album, track, or Spotify URI/ID. Retain the returned Spotify
ID or URI, entity type, name, credited artists, release date and precision,
external IDs when supplied, the requested market, and observation date. The
adapter emits normalized JSON suitable for use as one input to a wider source
stack; it does not turn catalog metadata into performance evidence.

## Evidence

Authority tier: provider-managed catalog metadata, primary for what Spotify
returns at the observation time. Cite the direct Spotify URL or recorded API
response and identify the market and observation date.

## Limits and terms

Catalog availability and returned fields can vary by market, authorization, and
time. Follow Spotify's documented scopes, rate limits, and developer terms; a
catalog record is not sales evidence or a historical popularity series.

For apps created under Spotify's February 2026 development-mode rules, Search
accepts at most 10 results per request (default 5). Artist followers and
`popularity`, album and track `popularity`, and `available_markets` are not
available as general research fields. New Releases and Artist Top Tracks are
also unavailable in this mode. Do not reconstruct, scrape, or label these as
Spotify-provided facts. See Spotify's
[February 2026 migration guide](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide)
and [quota modes](https://developer.spotify.com/documentation/web-api/concepts/quota-modes).

## Fallbacks

Use [Apple Music](apple-music.md) for a platform cross-check and
[MusicBrainz](musicbrainz.md) for music-specific identity. Use an official
artist or label page for release facts.

## Verification

Verify that artist, edition, market, and release-date precision match the
question. Preserve platform provenance and keep Spotify-only observations
separate from incompatible metrics.

Last verified: 2026-07-20
