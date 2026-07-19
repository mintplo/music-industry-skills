from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Dict, Optional, Tuple, Union


Number = Union[int, float]
MEASUREMENT_TYPES = {
    "shipment_net_returns",
    "retail_sale",
    "estimated_sale",
    "album_equivalent_unit",
    "chart_rank",
    "certification_threshold",
}
SOURCE_TIERS = {"A", "B", "C", "unverified"}


@dataclass(frozen=True)
class ReleaseCandidate:
    source: str
    source_id: str
    artist_name: str
    title: str
    first_release_date: str
    primary_type: str
    secondary_types: Tuple[str, ...] = ()
    country: Optional[str] = None
    barcode: Optional[str] = None
    mbid: Optional[str] = None
    source_url: str = ""
    track_count: Optional[int] = None


@dataclass(frozen=True)
class ReleaseRecord:
    release_group_id: str
    artist_name: str
    title: str
    first_release_date: str
    release_type: str
    editions: Tuple[ReleaseCandidate, ...]
    default_included: bool


@dataclass(frozen=True)
class ChartEntry:
    artist_name: str
    title: str
    metric: str
    value: Number
    unit: str
    measurement_type: str
    market: str
    period_start: str
    period_end: str
    source_name: str
    source_url: str
    evidence: str
    source_tier: str = "A"
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if self.measurement_type not in MEASUREMENT_TYPES:
            raise ValueError("unknown measurement_type: %s" % self.measurement_type)


@dataclass(frozen=True)
class Observation:
    artist_id: str
    release_group_id: str
    edition_id: Optional[str]
    release_type: str
    metric: str
    value: Number
    unit: str
    measurement_type: str
    market: str
    period_start: str
    period_end: str
    observed_at: str
    source_tier: str
    source_name: str
    source_url: str
    evidence: str
    confidence: float

    def __post_init__(self) -> None:
        if self.measurement_type not in MEASUREMENT_TYPES:
            raise ValueError("unknown measurement_type: %s" % self.measurement_type)
        if self.source_tier not in SOURCE_TIERS:
            raise ValueError("unknown source_tier: %s" % self.source_tier)
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.source_url.startswith(("http://", "https://")):
            raise ValueError("source_url must be HTTP(S)")


def to_dict(value: Any) -> Dict[str, Any]:
    if not is_dataclass(value):
        raise TypeError("to_dict expects a dataclass instance")
    return _serialize(asdict(value))


def _serialize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value


def observation_from_chart_entry(
    entry: ChartEntry,
    artist_id: str,
    release_group_id: str,
    release_type: str,
    observed_at: str,
) -> Observation:
    return Observation(
        artist_id=artist_id,
        release_group_id=release_group_id,
        edition_id=None,
        release_type=release_type,
        metric=entry.metric,
        value=entry.value,
        unit=entry.unit,
        measurement_type=entry.measurement_type,
        market=entry.market,
        period_start=entry.period_start,
        period_end=entry.period_end,
        observed_at=observed_at,
        source_tier=entry.source_tier,
        source_name=entry.source_name,
        source_url=entry.source_url,
        evidence=entry.evidence,
        confidence=entry.confidence,
    )
