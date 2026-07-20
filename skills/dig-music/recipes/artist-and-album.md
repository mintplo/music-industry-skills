# Artist and Album

## Use this branch

Use for multi-part or branch-specific research about an artist, release, album,
song, track list, or discography.
Do not load this recipe for a simple or single-fact request.
Combine this branch with another relevant branch when the request also asks
about a campaign, comparison, or market pattern.

## Questions to resolve

Identify the primary artist and the release group before deciding whether a
specific edition, recording, or track is in scope. Determine whether the
question asks for catalog facts, an official concept statement, or performance
evidence. When the request uses a relative response window such as initial or
early, define its exact start and end before collection. Identify later momentum
as outside that window rather than using it to close the early-response branch.
A single-album question never requires the full discography.

## Source stack

Start with [MusicBrainz](../providers/musicbrainz.md) and, when useful,
[Wikidata](../providers/wikidata.md) to resolve identity and release groups.
Add [Apple Music](../providers/apple-music.md) or
[Spotify](../providers/spotify.md) only for relevant catalog cross-checks.
Only when the request actually requires a complete release inventory, optionally
use `skills/dig-music/scripts/collect_discography_data.py` for
deterministic catalog normalization; do not run it for ordinary artist or
single-release questions.
Use [Web search](../providers/web-search.md) to find official artist, label,
distributor, or press pages for concept and release claims; use
[Web crawling](../providers/web-crawling.md) only for an allowed direct-page
review. Add [Circle Chart](../providers/circle-chart.md),
[Oricon](../providers/oricon.md), or [YouTube](../providers/youtube.md) only
when the user asks for the corresponding performance or public-video evidence.

## Evidence checks

Keep the primary artist's role distinct from featured or guest roles. Preserve
the release group and edition distinction, market, and date precision. Treat
official pages or attributable press as evidence for concepts, and retain the
market, period, measurement, observation date, and official status for every
requested performance observation.

## Completion criterion

Close only the requested artist or release branches with direct evidence,
qualified uncertainty, or an access-dependent result. Shape the answer to the
request rather than expanding it into an inventory or report the user did not
ask for.
