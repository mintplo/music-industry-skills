import html
import re
from typing import Any, Dict, Iterable, List

from .models import ChartEntry


def _integer(value: Any) -> int:
    return int(str(value).replace(",", "").strip())


def _circle_rows(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    rows = payload.get("List", [])
    if isinstance(rows, dict):
        return [rows[key] for key in sorted(rows, key=lambda value: int(value))]
    return rows


def parse_circle_album(
    payload: Dict[str, Any], source_url: str, period_start: str, period_end: str
) -> List[ChartEntry]:
    output = []
    for row in _circle_rows(payload):
        common = dict(
            artist_name=row["ARTIST_NAME"],
            title=row["ALBUM_NAME"],
            market="KR",
            period_start=period_start,
            period_end=period_end,
            source_name="Circle Album Chart",
            source_url=source_url,
        )
        output.append(
            ChartEntry(
                metric="chart_rank",
                value=_integer(row["SERVICE_RANKING"]),
                unit="rank",
                measurement_type="chart_rank",
                evidence="SERVICE_RANKING=%s" % row["SERVICE_RANKING"],
                **common,
            )
        )
        if str(row.get("CntYN", "N")).casefold() == "y" and str(
            row.get("Album_CNT", "")
        ).strip():
            output.append(
                ChartEntry(
                    metric="album_units",
                    value=_integer(row["Album_CNT"]),
                    unit="copies",
                    measurement_type="shipment_net_returns",
                    evidence="Album_CNT=%s; distributor=%s"
                    % (row["Album_CNT"], row.get("de_nm", "")),
                    **common,
                )
            )
    return output


def parse_oricon_album(
    html_text: str, source_url: str, period_start: str, period_end: str
) -> List[ChartEntry]:
    sections = re.findall(
        r'<section class="box-rank-entry".*?</section>', html_text, flags=re.DOTALL
    )
    output = []
    for section in sections:
        rank = re.search(r'<p class="num[^\"]*">\s*([0-9]+)\s*</p>', section)
        title = re.search(r'<h2 class="title"[^>]*>(.*?)</h2>', section, flags=re.DOTALL)
        artist = re.search(r'<p class="name">(.*?)</p>', section, flags=re.DOTALL)
        if not (rank and title and artist):
            continue
        clean = lambda value: html.unescape(re.sub(r"<[^>]+>", "", value)).strip()
        output.append(
            ChartEntry(
                artist_name=clean(artist.group(1)),
                title=clean(title.group(1)),
                metric="chart_rank",
                value=int(rank.group(1)),
                unit="rank",
                measurement_type="chart_rank",
                market="JP",
                period_start=period_start,
                period_end=period_end,
                source_name="Oricon Weekly Album Ranking",
                source_url=source_url,
                evidence="public weekly rank=%s" % rank.group(1),
            )
        )
    return output
