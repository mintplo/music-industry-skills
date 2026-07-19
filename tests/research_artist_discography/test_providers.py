import json
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).with_name("fixtures")
sys.path.insert(0, os.fspath(ROOT / "skills" / "research-artist-discography" / "scripts"))

from research_artist_discography.providers import (
    parse_itunes_albums,
    parse_musicbrainz_artists,
    parse_musicbrainz_release_groups,
)


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ProviderTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
