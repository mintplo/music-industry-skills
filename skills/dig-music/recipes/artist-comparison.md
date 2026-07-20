# Artist or Release Comparison

## Use this branch

Use for artist or release comparisons, including performance comparisons across
markets, periods, or platforms. Combine it with other branches only for the
facts necessary to make the requested comparison interpretable.

## Questions to resolve

Before collection, define the entities, market, relative period, metric, unit,
and measurement definition. Identify which observations can share a comparison
key and which must remain separate.

## Source stack

Use [MusicBrainz](../providers/musicbrainz.md) and, when needed,
[Wikidata](../providers/wikidata.md) to resolve comparable artists and releases.
Select only the performance cards that match the requested evidence:
[Circle Chart](../providers/circle-chart.md) for Korean chart evidence,
[Oricon](../providers/oricon.md) for Japanese public rankings, or
[YouTube](../providers/youtube.md) for current public video observations.
Use [Web search](../providers/web-search.md) to discover direct official,
operator-published, or attributable sources for the defined comparison.

## Evidence checks

Read `../references/metric-compatibility.md` before comparing numbers. Retain
market, metric, unit, measurement type, period basis, window length, source,
and observation date for every entity and observation. Define relative windows
such as `first week` with exact dates when they affect comparability.
Show incompatible evidence separately and never create an overall synthetic
score.

Never award a winner from unmatched evidence, such as an artist-specific
release with no corresponding release for the other artist. Keep that evidence
separate and call the comparison unavailable, including in the conclusion.
Treat raw sales as volume, not conversion, unless a relevant denominator makes
conversion measurable. Attribute qualitative demand or reaction claims and
state their sampling and interpretation limits.

## Completion criterion

Answer the requested comparison only where the defined observations are
compatible; otherwise present the evidence as non-comparable, unavailable, or
access-dependent. Choose a table, prose, or another format only if it helps the
user's requested comparison.
