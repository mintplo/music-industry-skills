import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).with_name("fixtures")
sys.path.insert(0, os.fspath(ROOT / "skills" / "research-artist-discography" / "scripts"))

from research_artist_discography.providers import (
    parse_itunes_albums,
    parse_musicbrainz_artists,
    parse_musicbrainz_release_groups,
)
import research_artist_discography.providers as providers


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class ProviderTests(unittest.TestCase):
    def setUp(self):
        providers._last_musicbrainz_request_at = None

    def test_musicbrainz_artist_candidates_preserve_disambiguation(self):
        rows = parse_musicbrainz_artists(load("musicbrainz_artist.json"))
        self.assertEqual("artist-mbid-1", rows[0]["id"])
        self.assertEqual("K-pop group", rows[0]["disambiguation"])

    def test_musicbrainz_release_groups_become_candidates(self):
        rows = parse_musicbrainz_release_groups("Example Artist", load("musicbrainz_release_groups.json"))
        self.assertEqual(["rg-1", "rg-2"], [row.mbid for row in rows])
        self.assertEqual("EP", rows[0].primary_type)

    def test_itunes_results_become_catalog_cross_checks(self):
        rows = parse_itunes_albums("Example Artist", load("itunes_albums.json"))
        self.assertEqual(2, len(rows))
        self.assertEqual(6, rows[0].track_count)
        self.assertEqual("2025-01-02", rows[0].first_release_date)

    def test_musicbrainz_search_then_fetch_and_search_are_throttled(self):
        clock = FakeClock()
        artist_payload = load("musicbrainz_artist.json")
        release_payload = {"release-groups": [], "release-group-count": 0}
        with patch.object(
            providers, "_get_json", side_effect=[artist_payload, release_payload, artist_payload]
        ) as get_json, patch.object(providers.time, "monotonic", clock.monotonic), patch.object(
            providers.time, "sleep", clock.sleep
        ):
            providers.search_musicbrainz_artist("Example Artist")
            providers.fetch_musicbrainz_release_groups("Example Artist", "artist-mbid-1")
            providers.search_musicbrainz_artist("Example Artist")

        self.assertEqual([1.1, 1.1], clock.sleeps)
        self.assertEqual(3, get_json.call_count)

    def test_musicbrainz_release_group_pages_are_throttled_after_first_page(self):
        clock = FakeClock()
        first_page = {
            "release-groups": [{"id": "rg-1", "title": "First EP", "primary-type": "EP"}],
            "release-group-count": 2,
        }
        second_page = {
            "release-groups": [{"id": "rg-2", "title": "First Album", "primary-type": "Album"}],
            "release-group-count": 2,
        }
        with patch.object(providers, "_get_json", side_effect=[first_page, second_page]) as get_json, patch.object(
            providers.time, "monotonic", clock.monotonic
        ), patch.object(providers.time, "sleep", clock.sleep):
            rows = providers.fetch_musicbrainz_release_groups("Example Artist", "artist-mbid-1")

        self.assertEqual(["rg-1", "rg-2"], [row.mbid for row in rows])
        self.assertEqual([1.1], clock.sleeps)
        self.assertEqual(2, get_json.call_count)


if __name__ == "__main__":
    unittest.main()
