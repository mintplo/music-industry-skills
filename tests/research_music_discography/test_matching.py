import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(
    0,
    os.fspath(ROOT / "skills" / "dig-music" / "scripts"),
)

from research_artist_discography.matching import (
    classify_release_type,
    filter_release_records,
    group_release_candidates,
)
from research_artist_discography.models import ReleaseCandidate


def candidate(source, source_id, title, date, primary, secondary=(), mbid=None, tracks=None, barcode=None):
    return ReleaseCandidate(
        source=source,
        source_id=source_id,
        artist_name="Example Artist",
        title=title,
        first_release_date=date,
        primary_type=primary,
        secondary_types=secondary,
        barcode=barcode,
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

    def test_year_month_musicbrainz_date_matches_an_exact_date_in_the_same_month(self):
        records = group_release_candidates([
            candidate("MusicBrainz", "rg-1", "First EP", "2025-01", "EP", mbid="rg-1"),
            candidate("iTunes", "99", "First EP", "2025-01-24", "Album", tracks=6),
        ])
        self.assertEqual(1, len(records))

    def test_unidentified_candidate_cannot_bridge_conflicting_mbid_groups(self):
        records = group_release_candidates([
            candidate("MusicBrainz", "rg-1", "First EP", "2025-01-02", "EP", mbid="rg-1"),
            candidate("iTunes", "99", "First EP", "2025-01-02", "EP"),
            candidate("MusicBrainz", "rg-2", "First EP", "2025-01-02", "EP", mbid="rg-2"),
        ])
        self.assertEqual(2, len(records))
        self.assertEqual({"rg:rg-1", "rg:rg-2"}, {record.release_group_id for record in records})

    def test_missing_date_does_not_merge_a_repeated_title(self):
        records = group_release_candidates([
            candidate("one", "1", "Same Title", "", "Album"),
            candidate("two", "2", "Same Title", "2025-01-01", "Album"),
        ])
        self.assertEqual(2, len(records))

    def test_year_only_date_does_not_merge_a_repeated_title(self):
        records = group_release_candidates([
            candidate("one", "1", "Same Title", "2025", "Album"),
            candidate("two", "2", "Same Title", "2025-01-01", "Album"),
        ])
        self.assertEqual(2, len(records))

    def test_equal_barcode_is_a_positive_identifier_match(self):
        records = group_release_candidates([
            candidate("one", "1", "Same Title", "", "Album", barcode="8801234567890"),
            candidate("two", "2", "Same Title (Japan Edition)", "2025", "Album", barcode="8801234567890"),
        ])
        self.assertEqual(1, len(records))

    def test_classifies_member_solo_from_raw_secondary_type(self):
        release = candidate("mb", "solo", "Solo", "2025-01-01", "Album", ("Member Solo",))
        self.assertEqual("member_solo", classify_release_type(release))

    def test_feature_records_are_excluded_by_the_default_filter(self):
        records = group_release_candidates([
            candidate("mb", "feature", "Feature", "2025-01-01", "Feature"),
        ])
        self.assertEqual("feature", records[0].release_type)
        self.assertEqual([], filter_release_records(records))

    def test_member_solo_edition_excludes_a_generic_canonical_album(self):
        records = group_release_candidates([
            candidate("MusicBrainz", "rg-1", "Solo", "2025-01-01", "Album", mbid="rg-1"),
            candidate("store", "1", "Solo", "2025-01-01", "Album", ("Member Solo",)),
        ])
        self.assertEqual("member_solo", records[0].release_type)
        self.assertFalse(records[0].default_included)

    def test_feature_edition_excludes_a_generic_canonical_album(self):
        records = group_release_candidates([
            candidate("MusicBrainz", "rg-1", "Feature", "2025-01-01", "Album", mbid="rg-1"),
            candidate("store", "1", "Feature", "2025-01-01", "Album", ("Feature",)),
        ])
        self.assertEqual("feature", records[0].release_type)
        self.assertFalse(records[0].default_included)

    def test_ambiguous_anonymous_candidate_remains_its_own_group(self):
        records = group_release_candidates([
            candidate("MusicBrainz", "rg-1", "Same Title", "2025-01-01", "Album", mbid="rg-1"),
            candidate("MusicBrainz", "rg-2", "Same Title", "2025-01-01", "Album", mbid="rg-2"),
            candidate("store", "1", "Same Title", "2025-01-01", "Album"),
        ])
        self.assertEqual(3, len(records))
        self.assertEqual(1, sum(len(record.editions) == 1 and record.release_group_id.startswith("local:") for record in records))

    def test_default_filter_keeps_singles_and_excludes_compilations(self):
        records = group_release_candidates([
            candidate("mb", "1", "Digital", "2025-01-01", "Single", tracks=1),
            candidate("mb", "2", "Best", "2025-02-01", "Album", ("Compilation",)),
        ])
        self.assertEqual(["digital_single"], [record.release_type for record in filter_release_records(records)])


if __name__ == "__main__":
    unittest.main()
