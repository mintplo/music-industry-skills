#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile

from research_artist_discography.charts import parse_circle_album, parse_oricon_album
from research_artist_discography.matching import (
    filter_release_records,
    find_release,
    group_release_candidates,
)
from research_artist_discography.models import observation_from_chart_entry, to_dict
from research_artist_discography.providers import (
    fetch_itunes_albums,
    fetch_musicbrainz_release_groups,
    parse_itunes_albums,
    parse_musicbrainz_artists,
    parse_musicbrainz_release_groups,
    search_musicbrainz_artist,
)
from research_artist_discography.validation import validate_dataset, write_observations_csv


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def select_artist(candidates, artist_mbid, warnings):
    if not candidates:
        raise RuntimeError("MusicBrainz returned no artist candidates")
    if artist_mbid:
        selected = next((row for row in candidates if row["id"] == artist_mbid), None)
        if selected is None:
            raise RuntimeError("--artist-mbid was not present in MusicBrainz candidates")
        return selected
    if len(candidates) > 1:
        warnings.append("MusicBrainz top artist candidate selected; verify same-name ambiguity")
    return candidates[0]


def load_catalog(artist_name, fixture_dir, artist_mbid, country):
    warnings = []
    if fixture_dir:
        artist_rows = parse_musicbrainz_artists(
            read_json(fixture_dir / "musicbrainz_artist.json")
        )
        selected = select_artist(artist_rows, artist_mbid, warnings)
        musicbrainz = parse_musicbrainz_release_groups(
            artist_name, read_json(fixture_dir / "musicbrainz_release_groups.json")
        )
        itunes = parse_itunes_albums(
            artist_name, read_json(fixture_dir / "itunes_albums.json")
        )
        return selected["id"], musicbrainz + itunes, warnings

    candidates = search_musicbrainz_artist(artist_name)
    selected = select_artist(candidates, artist_mbid, warnings)
    musicbrainz = fetch_musicbrainz_release_groups(artist_name, selected["id"])
    itunes = fetch_itunes_albums(artist_name, country)
    return selected["id"], musicbrainz + itunes, warnings


def attach_chart_entries(entries, records, artist_id, observed_at, warnings):
    observations = []
    for entry in entries:
        release = find_release(records, entry.artist_name, entry.title)
        if release is None:
            warnings.append("unmatched chart entry: %s — %s" % (entry.artist_name, entry.title))
            continue
        observations.append(observation_from_chart_entry(
            entry,
            artist_id=artist_id,
            release_group_id=release.release_group_id,
            release_type=release.release_type,
            observed_at=observed_at,
        ))
    return observations


def parse_args():
    parser = argparse.ArgumentParser(description="Collect and normalize an artist discography")
    parser.add_argument("artist")
    parser.add_argument("--artist-mbid")
    parser.add_argument("--country", default="KR")
    parser.add_argument("--fixture-dir", type=Path)
    parser.add_argument("--include-non-default", action="store_true")
    parser.add_argument("--circle-json", type=Path)
    parser.add_argument("--oricon-html", type=Path)
    parser.add_argument("--period-start", default="")
    parser.add_argument("--period-end", default="")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--csv", type=Path)
    return parser.parse_args()


def _preflight_parent(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.parent.is_dir():
        raise RuntimeError("output parent is not a directory: %s" % path.parent)


def _stage_text(path, content=None, dataset=None):
    staged_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=str(path.parent),
            prefix=".%s." % path.name,
            suffix=".tmp",
            delete=False,
        ) as handle:
            staged_path = Path(handle.name)
            if dataset is None:
                handle.write(content)
            else:
                write_observations_csv(dataset, handle)
        return staged_path
    except OSError:
        if staged_path:
            staged_path.unlink(missing_ok=True)
        raise


def write_outputs(payload, output_path, csv_path):
    paths = [output_path] + ([csv_path] if csv_path else [])
    staged_paths = []
    try:
        for path in paths:
            _preflight_parent(path)
        staged_paths.append(_stage_text(
            output_path,
            content=json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        ))
        if csv_path:
            staged_paths.append(_stage_text(csv_path, dataset=payload))
        for path, staged_path in zip(paths, staged_paths):
            os.replace(staged_path, path)
    except OSError as error:
        raise RuntimeError("could not write outputs: %s" % error) from error
    finally:
        for staged_path in staged_paths:
            if staged_path.exists():
                staged_path.unlink()


def main():
    try:
        args = parse_args()
        artist_id, candidates, warnings = load_catalog(
            args.artist, args.fixture_dir, args.artist_mbid, args.country
        )
        all_records = group_release_candidates(candidates)
        analysis_records = filter_release_records(
            all_records, include_non_default=args.include_non_default
        )
        observed_at = datetime.now(timezone.utc).isoformat()
        chart_entries = []
        if args.circle_json:
            chart_entries.extend(parse_circle_album(
                read_json(args.circle_json),
                "https://circlechart.kr/page_chart/album.circle",
                args.period_start,
                args.period_end,
            ))
        if args.oricon_html:
            chart_entries.extend(parse_oricon_album(
                args.oricon_html.read_text(encoding="utf-8"),
                "https://www.oricon.co.jp/rank/ja/w/",
                args.period_start,
                args.period_end,
            ))
        observations = attach_chart_entries(
            chart_entries, analysis_records, artist_id, observed_at, warnings
        )
        payload = {
            "schema_version": "1.0",
            "artist": {"id": artist_id, "name": args.artist},
            "releases": [to_dict(record) for record in all_records],
            "analysis_release_group_ids": [
                record.release_group_id for record in analysis_records
            ],
            "observations": [to_dict(row) for row in observations],
            "warnings": warnings,
            "collected_at": observed_at,
        }
        errors = validate_dataset(payload)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 2
        write_outputs(payload, args.output, args.csv)
        return 0
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
