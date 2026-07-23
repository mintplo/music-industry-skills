import csv
import io
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(
    0,
    os.fspath(ROOT / "skills" / "dig-music" / "scripts"),
)

from research_artist_discography.validation import validate_dataset, write_observations_csv


def dataset(measurement_type="chart_rank"):
    return {
        "schema_version": "1.0",
        "artist": {"id": "artist-1", "name": "Example Artist"},
        "releases": [{"release_group_id": "release-1", "release_type": "ep"}],
        "observations": [{
            "artist_id": "artist-1",
            "release_group_id": "release-1",
            "release_type": "ep",
            "metric": "chart_rank",
            "value": 1,
            "unit": "rank",
            "measurement_type": measurement_type,
            "market": "KR",
            "period_start": "2025-01-01",
            "period_end": "2025-01-07",
            "observed_at": "2025-01-08T00:00:00+09:00",
            "source_tier": "A",
            "source_name": "Circle Chart",
            "source_url": "https://circlechart.kr/example",
            "evidence": "SERVICE_RANKING=1",
            "confidence": 1.0,
        }],
        "warnings": [],
    }


class ValidationTests(unittest.TestCase):
    def test_valid_dataset_has_no_errors(self):
        self.assertEqual([], validate_dataset(dataset()))

    def test_unknown_measurement_type_is_rejected(self):
        errors = validate_dataset(dataset("sales"))
        self.assertTrue(any("measurement_type" in error for error in errors))

    def test_unknown_source_tier_is_rejected(self):
        payload = dataset()
        payload["observations"][0]["source_tier"] = "D"
        self.assertTrue(any("source_tier" in error for error in validate_dataset(payload)))

    def test_duplicate_release_ids_are_rejected(self):
        payload = dataset()
        payload["releases"].append({"release_group_id": "release-1", "release_type": "album"})
        self.assertTrue(any("unique" in error for error in validate_dataset(payload)))

    def test_empty_release_id_is_rejected(self):
        payload = dataset()
        payload["releases"][0]["release_group_id"] = ""
        self.assertTrue(any("requires release_group_id" in error for error in validate_dataset(payload)))

    def test_unknown_artist_or_release_ids_are_rejected(self):
        payload = dataset()
        payload["observations"][0]["artist_id"] = "artist-2"
        payload["observations"][0]["release_group_id"] = "release-2"
        errors = validate_dataset(payload)
        self.assertTrue(any("unknown artist" in error for error in errors))
        self.assertTrue(any("unknown release" in error for error in errors))

    def test_missing_provenance_period_or_evidence_is_rejected(self):
        payload = dataset()
        observation = payload["observations"][0]
        observation["source_url"] = ""
        observation["period_start"] = ""
        observation["observed_at"] = ""
        observation["evidence"] = ""
        errors = validate_dataset(payload)
        self.assertTrue(any("source_url" in error for error in errors))
        self.assertTrue(any("period_start" in error for error in errors))
        self.assertTrue(any("observed_at" in error for error in errors))
        self.assertTrue(any("evidence" in error for error in errors))

    def test_invalid_confidence_is_rejected_but_zero_is_allowed(self):
        payload = dataset()
        payload["observations"][0]["confidence"] = 0
        self.assertEqual([], validate_dataset(payload))
        payload["observations"][0]["confidence"] = 1.1
        self.assertTrue(any("confidence" in error for error in validate_dataset(payload)))

    def test_csv_preserves_measurement_type_column(self):
        output = io.StringIO()
        write_observations_csv(dataset(), output)
        output.seek(0)
        row = next(csv.DictReader(output))
        self.assertEqual("chart_rank", row["measurement_type"])
        self.assertEqual("rank", row["unit"])


if __name__ == "__main__":
    unittest.main()
