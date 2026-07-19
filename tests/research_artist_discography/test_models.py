import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, os.fspath(ROOT / "skills" / "research-artist-discography" / "scripts"))

from research_artist_discography.models import (
    ChartEntry,
    Observation,
    ReleaseCandidate,
    observation_from_chart_entry,
    to_dict,
)


class ModelTests(unittest.TestCase):
    def test_release_candidate_serializes_tuples_as_lists(self):
        candidate = ReleaseCandidate(
            source="MusicBrainz",
            source_id="rg-1",
            artist_name="Example",
            title="First EP",
            first_release_date="2025-01-02",
            primary_type="EP",
            secondary_types=("Mixtape/Street",),
            mbid="rg-1",
            source_url="https://musicbrainz.org/release-group/rg-1",
        )
        self.assertEqual(["Mixtape/Street"], to_dict(candidate)["secondary_types"])

    def test_chart_entry_keeps_rank_separate_from_quantity(self):
        rank = ChartEntry(
            artist_name="Example",
            title="First EP",
            metric="chart_rank",
            value=1,
            unit="rank",
            measurement_type="chart_rank",
            market="KR",
            period_start="2025-01-01",
            period_end="2025-01-07",
            source_name="Circle Chart",
            source_url="https://circlechart.kr/example",
            evidence="SERVICE_RANKING=1",
        )
        observation = observation_from_chart_entry(
            rank,
            artist_id="artist-1",
            release_group_id="release-1",
            release_type="ep",
            observed_at="2025-01-08T00:00:00+09:00",
        )
        self.assertEqual("chart_rank", observation.measurement_type)
        self.assertEqual("rank", observation.unit)

    def test_observation_rejects_unknown_measurement_type(self):
        with self.assertRaisesRegex(ValueError, "measurement_type"):
            Observation(
                artist_id="artist-1",
                release_group_id="release-1",
                edition_id=None,
                release_type="ep",
                metric="album_units",
                value=10,
                unit="copies",
                measurement_type="sales",
                market="KR",
                period_start="2025-01-01",
                period_end="2025-01-07",
                observed_at="2025-01-08T00:00:00+09:00",
                source_tier="A",
                source_name="Example",
                source_url="https://example.com",
                evidence="value=10",
                confidence=1.0,
            )


if __name__ == "__main__":
    unittest.main()
