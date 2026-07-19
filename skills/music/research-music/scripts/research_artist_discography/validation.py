import csv
from typing import Any, Dict, List, TextIO

from .models import MEASUREMENT_TYPES, SOURCE_TIERS


OBSERVATION_COLUMNS = [
    "artist_id", "release_group_id", "edition_id", "release_type", "metric", "value", "unit",
    "measurement_type", "market", "period_start", "period_end", "observed_at", "source_tier",
    "source_name", "source_url", "evidence", "confidence",
]


def validate_dataset(dataset: Dict[str, Any]) -> List[str]:
    errors = []
    if dataset.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    artist = dataset.get("artist", {})
    if not artist.get("id") or not artist.get("name"):
        errors.append("artist id and name are required")
    release_rows = dataset.get("releases", [])
    release_ids = {row.get("release_group_id") for row in release_rows}
    if any(not release_id for release_id in release_ids):
        errors.append("every release requires release_group_id")
    if len(release_ids) != len(release_rows):
        errors.append("release_group_id values must be unique")
    for index, row in enumerate(dataset.get("observations", [])):
        prefix = "observations[%d]" % index
        required = [
            "artist_id", "release_group_id", "release_type", "metric", "value", "unit",
            "measurement_type", "market", "period_start", "period_end", "observed_at",
            "source_tier", "source_name", "source_url", "evidence", "confidence",
        ]
        missing = [key for key in required if key not in row or row[key] is None or row[key] == ""]
        if missing:
            errors.append("%s missing required fields: %s" % (prefix, ", ".join(missing)))
        if row.get("artist_id") != artist.get("id"):
            errors.append("%s references an unknown artist" % prefix)
        if row.get("release_group_id") not in release_ids:
            errors.append("%s references an unknown release" % prefix)
        if row.get("measurement_type") not in MEASUREMENT_TYPES:
            errors.append("%s has unknown measurement_type" % prefix)
        if row.get("source_tier") not in SOURCE_TIERS:
            errors.append("%s has unknown source_tier" % prefix)
        if not str(row.get("source_url", "")).startswith(("http://", "https://")):
            errors.append("%s requires source_url" % prefix)
        if not row.get("period_start") or not row.get("period_end") or not row.get("observed_at"):
            errors.append("%s requires period and observed_at" % prefix)
        confidence = row.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0.0 <= confidence <= 1.0:
            errors.append("%s confidence must be between 0 and 1" % prefix)
    return errors


def write_observations_csv(dataset: Dict[str, Any], destination: TextIO) -> None:
    writer = csv.DictWriter(destination, fieldnames=OBSERVATION_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(dataset.get("observations", []))
