import hashlib
import re
import unicodedata
from datetime import date
from typing import Iterable, List, Optional

from .models import ReleaseCandidate, ReleaseRecord


DEFAULT_TYPES = {"studio_album", "ep", "single_album", "digital_single", "repackage"}


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[^0-9a-z가-힣]+", "", value)


def classify_release_type(candidate: ReleaseCandidate) -> str:
    primary = candidate.primary_type.casefold().strip()
    secondary = {value.casefold().strip() for value in candidate.secondary_types}
    title = candidate.title.casefold()
    if "compilation" in secondary:
        return "compilation"
    if "live" in secondary:
        return "live_album"
    if "remix" in secondary:
        return "remix_album"
    if "soundtrack" in secondary:
        return "ost"
    if "reissue" in secondary or "repackage" in title or "re-pack" in title:
        return "repackage"
    if primary in {"ep", "mini album", "mini-album"}:
        return "ep"
    if primary in {"single album", "single-album"}:
        return "single_album"
    if primary == "single":
        return "digital_single" if candidate.track_count in {None, 1, 2, 3} else "single_album"
    if primary == "album":
        return "studio_album"
    return "other"


def _same_group(left: ReleaseCandidate, right: ReleaseCandidate) -> bool:
    if left.mbid and right.mbid:
        return left.mbid == right.mbid
    if normalize_text(left.artist_name) != normalize_text(right.artist_name):
        return False
    if normalize_text(left.title) != normalize_text(right.title):
        return False
    if not left.first_release_date or not right.first_release_date:
        return True
    if len(left.first_release_date) < 10 or len(right.first_release_date) < 10:
        length = min(len(left.first_release_date), len(right.first_release_date))
        return left.first_release_date[:length] == right.first_release_date[:length]
    left_date = date.fromisoformat(left.first_release_date[:10])
    right_date = date.fromisoformat(right.first_release_date[:10])
    return abs((left_date - right_date).days) <= 45


def _record_id(candidates: List[ReleaseCandidate]) -> str:
    mbid = next((item.mbid for item in candidates if item.mbid), None)
    if mbid:
        return "rg:%s" % mbid
    first = candidates[0]
    raw = "|".join((normalize_text(first.artist_name), normalize_text(first.title), first.first_release_date[:10]))
    return "local:%s" % hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def group_release_candidates(candidates: Iterable[ReleaseCandidate]) -> List[ReleaseRecord]:
    groups: List[List[ReleaseCandidate]] = []
    for candidate in candidates:
        group = next((items for items in groups if any(_same_group(candidate, existing) for existing in items)), None)
        if group is None:
            groups.append([candidate])
        else:
            group.append(candidate)

    records = []
    for items in groups:
        items.sort(key=lambda item: (item.source, item.source_id))
        canonical = next((item for item in items if item.mbid), items[0])
        release_type = classify_release_type(canonical)
        if release_type == "other":
            release_type = next((classify_release_type(item) for item in items if classify_release_type(item) != "other"), "other")
        records.append(ReleaseRecord(
            release_group_id=_record_id(items),
            artist_name=canonical.artist_name,
            title=canonical.title,
            first_release_date=min((item.first_release_date for item in items if item.first_release_date), default=""),
            release_type=release_type,
            editions=tuple(items),
            default_included=release_type in DEFAULT_TYPES,
        ))
    return sorted(records, key=lambda item: (item.first_release_date, normalize_text(item.title)))


def filter_release_records(records: Iterable[ReleaseRecord], include_non_default: bool = False) -> List[ReleaseRecord]:
    return [record for record in records if include_non_default or record.default_included]


def find_release(records: Iterable[ReleaseRecord], artist_name: str, title: str) -> Optional[ReleaseRecord]:
    artist_key = normalize_text(artist_name)
    title_key = normalize_text(title)
    return next((record for record in records if normalize_text(record.artist_name) == artist_key and normalize_text(record.title) == title_key), None)
