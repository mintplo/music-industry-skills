# Data Schema

## Release record

Required fields: `release_group_id`, `artist_name`, `title`, `first_release_date`, `release_type`, and `editions`.

`editions[]` is the canonical source container. Do not add a duplicate top-level `sources` field.

Allowed default release types: `studio_album`, `ep`, `single_album`, `digital_single`, and `repackage`.

Preserved non-default types: `member_solo`, `feature`, `ost`, `live_album`, `compilation`, `remix_album`, and `other`.

## Observation

```json
{
  "artist_id": "canonical-artist-id",
  "release_group_id": "canonical-release-group-id",
  "edition_id": null,
  "release_type": "studio_album",
  "metric": "album_units",
  "value": 1250000,
  "unit": "copies",
  "measurement_type": "shipment_net_returns",
  "market": "KR",
  "period_start": "2026-01-01",
  "period_end": "2026-01-31",
  "observed_at": "2026-07-19T12:00:00+09:00",
  "source_tier": "A",
  "source_name": "Circle Chart",
  "source_url": "https://example.com/source",
  "evidence": "The source field and period that support the value.",
  "confidence": 0.98
}
```

Allowed measurement types: `shipment_net_returns`, `retail_sale`, `estimated_sale`, `album_equivalent_unit`, `chart_rank`, and `certification_threshold`.

Never sum observations with different measurement types, markets, units, or periods. A comparison may show unlike values side by side only when the difference is labeled.

Source tiers: `A` official, `B` reliable corroborated, `C` wiki/community/single unofficial source, and `unverified` for unresolved evidence.
