import json
import time
from typing import Any, Dict, List
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import ReleaseCandidate


USER_AGENT = "research-artist-discography/0.1 (local Codex skill)"


def _get_json(url: str, timeout: int = 15) -> Dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_musicbrainz_artists(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [{
        "id": row["id"],
        "name": row["name"],
        "country": row.get("country"),
        "score": int(row.get("score", 0)),
        "disambiguation": row.get("disambiguation", ""),
    } for row in payload.get("artists", [])]


def parse_musicbrainz_release_groups(
    artist_name: str, payload: Dict[str, Any]
) -> List[ReleaseCandidate]:
    rows = []
    for row in payload.get("release-groups", []):
        mbid = row["id"]
        rows.append(ReleaseCandidate(
            source="MusicBrainz",
            source_id=mbid,
            artist_name=artist_name,
            title=row["title"],
            first_release_date=row.get("first-release-date", ""),
            primary_type=row.get("primary-type", "Other"),
            secondary_types=tuple(row.get("secondary-types", [])),
            mbid=mbid,
            source_url="https://musicbrainz.org/release-group/%s" % mbid,
        ))
    return rows


def parse_itunes_albums(artist_name: str, payload: Dict[str, Any]) -> List[ReleaseCandidate]:
    rows = []
    for row in payload.get("results", []):
        if row.get("wrapperType") != "collection" or row.get("collectionType") != "Album":
            continue
        if row.get("artistName", "").casefold() != artist_name.casefold():
            continue
        track_count = row.get("trackCount")
        rows.append(ReleaseCandidate(
            source="Apple iTunes Search",
            source_id=str(row["collectionId"]),
            artist_name=row.get("artistName", artist_name),
            title=row["collectionName"],
            first_release_date=row.get("releaseDate", "")[:10],
            primary_type="Single" if track_count is not None and track_count <= 3 else "Album",
            source_url=row.get("collectionViewUrl", "https://music.apple.com/"),
            track_count=track_count,
        ))
    return rows


def search_musicbrainz_artist(artist_name: str) -> List[Dict[str, Any]]:
    query = urlencode({"query": 'artist:"%s"' % artist_name, "fmt": "json", "limit": 10})
    return parse_musicbrainz_artists(
        _get_json("https://musicbrainz.org/ws/2/artist/?%s" % query)
    )


def fetch_musicbrainz_release_groups(
    artist_name: str, artist_mbid: str
) -> List[ReleaseCandidate]:
    rows = []
    offset = 0
    while True:
        time.sleep(1.1)
        query = urlencode({
            "artist": artist_mbid,
            "fmt": "json",
            "limit": 100,
            "offset": offset,
        })
        payload = _get_json("https://musicbrainz.org/ws/2/release-group?%s" % query)
        page = payload.get("release-groups", [])
        rows.extend(parse_musicbrainz_release_groups(artist_name, payload))
        offset += len(page)
        total = int(payload.get("release-group-count", offset))
        if not page or offset >= total:
            return rows


def fetch_itunes_albums(artist_name: str, country: str = "KR") -> List[ReleaseCandidate]:
    query = urlencode({
        "term": artist_name,
        "country": country,
        "media": "music",
        "entity": "album",
        "limit": 200,
    })
    return parse_itunes_albums(
        artist_name, _get_json("https://itunes.apple.com/search?%s" % query)
    )
