import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, os.fspath(ROOT / "skills" / "research-artist-discography" / "scripts"))

from research_artist_discography.matching import (
    classify_release_type,
    filter_release_records,
    group_release_candidates,
)
from research_artist_discography.models import ReleaseCandidate


def candidate(source, source_id, title, date, primary, secondary=(), mbid=None, tracks=None):
    return ReleaseCandidate(
        source=source,
        source_id=source_id,
        artist_name="Example Artist",
        title=title,
        first_release_date=date,
        primary_type=primary,
        secondary_types=secondary,
        mbid=mbid,
        source_url="https://example.com/%s" % source_id,
        track_count=tracks,
    )


class MatchingTests(unittest.TestCase):
    def test_classifies_default_and_non_default_types(self):
        self.assertEqual("studio_album", classify_release_type(candidate("mb", "1", "One", "2025-01-01", "Album")))
        self.assertEqual("ep", classify_release_type(candidate("mb", "2", "Two", "2025-02-01", "EP")))
        self.assertEqual("repackage", classify_release_type(candidate("mb", "3", "Three Repackage", "2025-03-01", "Album", ("Reissue",))))
        self.assertEqual("compilation", classify_release_type(candidate("mb", "4", "Best", "2025-04-01", "Album", ("Compilation",))))

    def test_groups_same_release_across_sources_but_keeps_editions(self):
        records = group_release_candidates([
            candidate("MusicBrainz", "rg-1", "First EP", "2025-01-02", "EP", mbid="rg-1"),
            candidate("iTunes", "99", "First EP", "2025-01-02", "EP", tracks=6),
        ])
        self.assertEqual(1, len(records))
        self.assertEqual(2, len(records[0].editions))
        self.assertEqual("rg:rg-1", records[0].release_group_id)

    def test_groups_country_editions_with_nearby_dates(self):
        records = group_release_candidates([
            candidate("MusicBrainz", "rg-1", "First EP", "2025-01-02", "EP", mbid="rg-1"),
            candidate("iTunes", "99", "First EP", "2025-01-24", "Album", tracks=6),
        ])
        self.assertEqual(1, len(records))

    def test_partial_musicbrainz_dates_do_not_crash_grouping(self):
        records = group_release_candidates([
            candidate("MusicBrainz", "rg-1", "First EP", "2025-01", "EP", mbid="rg-1"),
            candidate("iTunes", "99", "First EP", "2025-01-24", "Album", tracks=6),
        ])
        self.assertEqual(1, len(records))

    def test_default_filter_keeps_singles_and_excludes_compilations(self):
        records = group_release_candidates([
            candidate("mb", "1", "Digital", "2025-01-01", "Single", tracks=1),
            candidate("mb", "2", "Best", "2025-02-01", "Album", ("Compilation",)),
        ])
        self.assertEqual(["digital_single"], [record.release_type for record in filter_release_records(records)])


if __name__ == "__main__":
    unittest.main()
