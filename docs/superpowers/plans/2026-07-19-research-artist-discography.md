# Research Artist Discography Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an installable `research-artist-discography` Codex skill that starts from an artist name, constructs the artist's release catalog, preserves metric definitions and evidence, and returns a sourced discography brief with comparisons and optional visualizations.

**Architecture:** Keep the user-facing workflow in a concise `SKILL.md`, move source rules, the normalized schema, and report conventions into three references, and use small Python standard-library modules for deterministic catalog parsing, release matching, chart evidence parsing, validation, and JSON/CSV export. The skill source lives in this repository and is linked into `~/.codex/skills` only after deterministic tests and the official skill validator pass.

**Tech Stack:** Codex skills, Markdown/YAML, Python 3.9+ standard library, `unittest`, MusicBrainz Web Service, Apple iTunes Search API, optional Circle/Oricon saved responses, optional YouTube Data API through the agent's normal web/API tools.

## Global Constraints

- Name the skill folder exactly `research-artist-discography`.
- Treat an artist name as the default input; an album name is an optional filter or drill-down target.
- Include studio albums, EPs/mini albums, single albums, digital singles, and repackages by default.
- Preserve but exclude member solos, features, OST tracks, live albums, compilations, and remix albums from default performance comparisons unless requested.
- Prefer free public sources and require no credentials for the minimum workflow.
- Never bypass access controls, automate login sessions, or treat an undocumented endpoint as a guaranteed production API.
- Never combine shipments net of returns, retail sales, estimated sales, album-equivalent units, ranks, or certification thresholds.
- Attach source URL, source tier, market, period, observation time, measurement type, and confidence to every numeric observation.
- Keep official values separate from article/wiki reference values.
- Keep `SKILL.md` under 500 lines and load the three reference files only when their subject is needed.
- Do not add a README, installation guide, changelog, web app, scheduler, or plugin packaging in this plan.
- Use the Python standard library in shipped scripts; use ephemeral PyYAML only to run the official skill validator.

## File Map

```text
skills/research-artist-discography/
├── SKILL.md                              # Trigger description and agent workflow
├── agents/openai.yaml                    # Codex UI metadata
├── references/
│   ├── source-policy.md                  # Source tiers, access rules, provider caveats
│   ├── data-schema.md                    # Release and observation schema
│   └── report-format.md                  # Brief, comparison, and visualization contract
└── scripts/
    ├── collect_discography_data.py       # CLI orchestration and JSON/CSV output
    └── research_artist_discography/
        ├── __init__.py                   # Public deterministic module exports
        ├── models.py                     # Release, chart, and observation dataclasses
        ├── matching.py                   # Type classification, grouping, filtering
        ├── providers.py                  # MusicBrainz/iTunes parsers and HTTP clients
        ├── charts.py                     # Circle JSON and Oricon HTML parsers
        └── validation.py                 # Dataset invariants and CSV projection

tests/research_artist_discography/
├── test_skill_contract.py                # Skill metadata and instruction contract
├── test_models.py                        # Serialization and metric semantics
├── test_matching.py                      # Classification, grouping, exclusions
├── test_providers.py                     # Catalog response parsing
├── test_charts.py                        # Chart evidence parsing
├── test_validation.py                    # Dataset integrity and non-combination rules
├── test_cli.py                           # Fixture-mode end-to-end collector
└── fixtures/
    ├── musicbrainz_artist.json
    ├── musicbrainz_release_groups.json
    ├── itunes_albums.json
    ├── circle_album_week.json
    └── oricon_album_week.html
```

---

### Task 1: Scaffold the installable skill and lock its written contract

**Files:**
- Create: `skills/research-artist-discography/SKILL.md`
- Create: `skills/research-artist-discography/agents/openai.yaml`
- Create: `skills/research-artist-discography/references/source-policy.md`
- Create: `skills/research-artist-discography/references/data-schema.md`
- Create: `skills/research-artist-discography/references/report-format.md`
- Create: `tests/research_artist_discography/test_skill_contract.py`

**Interfaces:**
- Consumes: approved design in `docs/superpowers/specs/2026-07-19-music-industry-research-skill-design.md`.
- Produces: a valid Codex skill directory whose references and default scope are stable inputs for every later task.

- [ ] **Step 1: Write the failing skill contract test**

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "research-artist-discography"


class SkillContractTests(unittest.TestCase):
    def test_required_files_and_frontmatter_exist(self):
        required = [
            SKILL / "SKILL.md",
            SKILL / "agents" / "openai.yaml",
            SKILL / "references" / "source-policy.md",
            SKILL / "references" / "data-schema.md",
            SKILL / "references" / "report-format.md",
        ]
        self.assertEqual([], [str(path) for path in required if not path.is_file()])

        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: research-artist-discography\n"))
        self.assertIn("아티스트 이름", text)
        self.assertIn("전체 디스코그래피", text)
        self.assertIn("references/source-policy.md", text)
        self.assertIn("references/data-schema.md", text)
        self.assertIn("references/report-format.md", text)
        self.assertNotRegex(text, r"\b(T[B]D|T[O]DO|FIX[M]E)\b")
        self.assertLessEqual(len(text.splitlines()), 500)

    def test_ui_prompt_names_the_skill(self):
        text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('$research-artist-discography', text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and confirm the skill does not exist yet**

Run:

```bash
python3 -m unittest tests.research_artist_discography.test_skill_contract -v
```

Expected: `FAIL` because `skills/research-artist-discography/SKILL.md` does not exist.

- [ ] **Step 3: Initialize the official skill scaffold**

Run:

```bash
python3 /Users/mintplo/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  research-artist-discography \
  --path skills \
  --resources scripts,references \
  --interface 'display_name=Artist Discography Research' \
  --interface 'short_description=아티스트의 전체 발매작과 성과를 출처 기반으로 조사' \
  --interface 'default_prompt=Use $research-artist-discography to research an artist’s full discography and compare release performance.'
```

Expected: the scaffold creates `SKILL.md`, `agents/openai.yaml`, `scripts/`, and `references/` without an `assets/` directory.

- [ ] **Step 4: Replace the generated scaffold text with the first complete skill workflow**

Write `skills/research-artist-discography/SKILL.md` as:

```markdown
---
name: research-artist-discography
description: Research an artist's full discography, release metadata, concepts, promotion, sales and chart evidence, and public social/video signals. Use when Codex is asked to investigate an artist's albums or comeback history, compare releases, build a sourced album timeline, or drill into one release within the artist's catalog.
---

# Research Artist Discography

Start from the artist name. Treat an album name as an optional filter or drill-down target.

## Workflow

1. Resolve the artist before collecting releases. Ask only when same-name candidates remain genuinely ambiguous.
2. Build the complete release inventory from at least two catalog sources when possible.
3. Include studio albums, EPs/mini albums, single albums, digital singles, and repackages by default.
4. Preserve member solos, features, OST tracks, live albums, compilations, and remix albums separately; exclude them from default comparisons unless requested.
5. Group country and format editions under a release group without deleting edition identifiers.
6. Collect current performance evidence from official sources first. Never estimate a missing number.
7. Collect release concepts and promotion from official introductions, press releases, artist channels, and attributable interviews; attach a source to every claim.
8. Collect YouTube and other accessible public signals with their observation time; report authenticated SNS data as unavailable when credentials are absent.
9. Apply period, release-type, latest-N, and album-name filters only after preserving the entire release inventory.
10. Keep facts, missing data, conflicts, and interpretation visibly separate.
11. Return the entire release inventory before reducing detail for a long discography.

Read `references/source-policy.md` before selecting or crawling sources. Read `references/data-schema.md` before combining observations or exporting JSON/CSV. Read `references/report-format.md` before composing the final brief or visualization.

Use `scripts/collect_discography_data.py` when deterministic catalog normalization is useful. Web research remains necessary for current chart evidence, concepts, promotion, and sources not implemented by the script.
```

Keep the generated `agents/openai.yaml`; verify it contains only quoted interface strings and no invented MCP dependency.

- [ ] **Step 5: Write the three reference contracts**

Write `references/source-policy.md` with these exact sections and rules:

```markdown
# Source Policy

## Priority

1. Official APIs, official charts, labels, distributors, and artist channels
2. Reliable press or two independent agreeing sources
3. Wikis and community-maintained pages as reference-only evidence

## Required evidence

For every number preserve source name, URL, market, period, observation time, measurement type, source tier, and a short evidence note. Report unavailable data as unavailable.

## Provider roles

- MusicBrainz: identifiers and release groups; respect one request per second and review commercial terms before company-scale use.
- Wikidata: CC0 identity and date cross-check; verify missing or mistyped K-pop records.
- Apple iTunes Search: no-key catalog cross-check; do not treat catalog fields as performance.
- Spotify: catalog and track-list support when credentials exist; do not rely on removed development-mode popularity fields.
- Circle Album Chart: shipments net of returns; keep separate from Circle Retail Album point-of-sale data. Treat the page's internal JSON route as undocumented and low-frequency only.
- Oricon: label public page values with exactly what the page exposes. Never infer sales from rank.
- YouTube Data API: public video/channel observations when a key exists; preserve collection time and quota limits.
- Instagram, TikTok, and X: do not make competitor data a credential-free requirement. Use official authenticated interfaces only when later authorized.
- NamuWiki and other wikis: reference-only, short evidence, original link, no bulk commercial corpus, no access-control bypass.

## Access rules

Honor robots directives, rate limits, `Retry-After`, login boundaries, and site terms. Prefer static HTML or official interfaces. Use browser rendering only when necessary. Never bypass Cloudflare or reuse a person's authenticated session.
```

Write `references/data-schema.md` as:

````markdown
# Data Schema

## Release record

Required fields: `release_group_id`, `artist_name`, `title`, `first_release_date`, `release_type`, `editions`, and `sources`.

Allowed default release types: `studio_album`, `ep`, `single_album`, `digital_single`, and `repackage`.

Preserved non-default types: `member_solo`, `feature`, `ost`, `live_album`, `compilation`, `remix_album`, and `other`.

## Observation

```json
{
  "artist_id": "canonical-artist-id",
  "release_group_id": "canonical-release-group-id",
  "edition_id": null,
  "release_type": "studio_album",
  "metric": "album_units",
  "value": 1250000,
  "unit": "copies",
  "measurement_type": "shipment_net_returns",
  "market": "KR",
  "period_start": "2026-01-01",
  "period_end": "2026-01-31",
  "observed_at": "2026-07-19T12:00:00+09:00",
  "source_tier": "A",
  "source_name": "Circle Chart",
  "source_url": "https://example.com/source",
  "evidence": "The source field and period that support the value.",
  "confidence": 0.98
}
```

Allowed measurement types: `shipment_net_returns`, `retail_sale`, `estimated_sale`, `album_equivalent_unit`, `chart_rank`, and `certification_threshold`.

Never sum observations with different measurement types, markets, units, or periods. A comparison may show unlike values side by side only when the difference is labeled.

Source tiers: `A` official, `B` reliable corroborated, `C` wiki/community/single unofficial source, and `unverified` for unresolved evidence.
````

Write `references/report-format.md` as:

```markdown
# Report Format

## Default discography brief

1. Scope, artist identity, collection date, and missing-source warning
2. Complete release inventory with type and date
3. Release metadata, concept, positioning, and promotion matrix
4. Sales and chart evidence with measurement definitions
5. YouTube and other accessible public signals with observation times
6. Release-to-release changes and marketing implications
7. Conflicts, missing data, and confidence
8. Direct source links

## Drill-down

For a named release, keep the full inventory visible and add a detailed release card. Compare only same-market, same-period, same-unit, same-measurement observations.

## Visualization

Create a timeline for release history. Create line or bar charts only for comparable numeric observations. Put rank on a reversed rank axis when supported. Do not place unlike units on one axis and do not create a synthetic overall score. If comparable data is insufficient, use a table and state why a chart was omitted.

## Writing rules

Label factual evidence, AI interpretation, and limitations separately. Use `데이터 없음` or `확인 불가` instead of filling gaps. Keep article/wiki numbers in a reference-only subsection.
```

- [ ] **Step 6: Run contract and official scaffold validation**

Run:

```bash
python3 -m unittest tests.research_artist_discography.test_skill_contract -v
uv run --with pyyaml python /Users/mintplo/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/research-artist-discography
```

Expected: the unit test reports `OK`; the official validator reports `Skill is valid!`.

- [ ] **Step 7: Commit the written skill contract**

```bash
git add skills/research-artist-discography tests/research_artist_discography/test_skill_contract.py
git commit -m "feat: scaffold artist discography research skill"
```

---

### Task 2: Add typed records and metric-preserving serialization

**Files:**
- Create: `skills/research-artist-discography/scripts/research_artist_discography/__init__.py`
- Create: `skills/research-artist-discography/scripts/research_artist_discography/models.py`
- Create: `tests/research_artist_discography/test_models.py`

**Interfaces:**
- Consumes: measurement types and required fields from `references/data-schema.md`.
- Produces: `ReleaseCandidate`, `ReleaseRecord`, `ChartEntry`, `Observation`, `to_dict()`, and `observation_from_chart_entry()` for all later modules.

- [ ] **Step 1: Write failing model and semantic tests**

```python
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
```

- [ ] **Step 2: Run the tests and confirm the package is missing**

Run:

```bash
python3 -m unittest tests.research_artist_discography.test_models -v
```

Expected: `ERROR` with `ModuleNotFoundError: No module named 'research_artist_discography'`.

- [ ] **Step 3: Implement the model module**

Write `models.py` with frozen dataclasses and these exact invariants:

```python
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Dict, List, Optional, Tuple, Union


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
    return asdict(value)


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
```

Write `__init__.py` as:

```python
from .models import ChartEntry, Observation, ReleaseCandidate, ReleaseRecord

__all__ = ["ChartEntry", "Observation", "ReleaseCandidate", "ReleaseRecord"]
```

- [ ] **Step 4: Run the model tests**

Run:

```bash
python3 -m unittest tests.research_artist_discography.test_models -v
```

Expected: 3 tests pass and the command reports `OK`.

- [ ] **Step 5: Commit the typed domain model**

```bash
git add skills/research-artist-discography/scripts/research_artist_discography tests/research_artist_discography/test_models.py
git commit -m "feat: add discography evidence model"
```

---

### Task 3: Classify releases and group editions without losing identity

**Files:**
- Create: `skills/research-artist-discography/scripts/research_artist_discography/matching.py`
- Create: `tests/research_artist_discography/test_matching.py`

**Interfaces:**
- Consumes: `ReleaseCandidate` and `ReleaseRecord` from Task 2.
- Produces: `classify_release_type(candidate) -> str`, `group_release_candidates(candidates) -> List[ReleaseRecord]`, `filter_release_records(records, include_non_default=False) -> List[ReleaseRecord]`, and `find_release(records, artist_name, title) -> Optional[ReleaseRecord]`.

- [ ] **Step 1: Write failing classification and grouping tests**

```python
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
```

- [ ] **Step 2: Run the tests and verify the matching module is missing**

Run:

```bash
python3 -m unittest tests.research_artist_discography.test_matching -v
```

Expected: `ERROR` importing `research_artist_discography.matching`.

- [ ] **Step 3: Implement deterministic classification and grouping**

Write `matching.py` as:

```python
import hashlib
import re
import unicodedata
from collections import defaultdict
from datetime import date
from typing import Dict, Iterable, List, Optional, Tuple

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
```

- [ ] **Step 4: Run matching and model tests together**

Run:

```bash
python3 -m unittest \
  tests.research_artist_discography.test_models \
  tests.research_artist_discography.test_matching -v
```

Expected: 8 tests pass and the command reports `OK`.

- [ ] **Step 5: Commit release classification and identity matching**

```bash
git add skills/research-artist-discography/scripts/research_artist_discography/matching.py tests/research_artist_discography/test_matching.py
git commit -m "feat: classify and group artist releases"
```

---

### Task 4: Parse free catalog providers and support low-rate live collection

**Files:**
- Create: `skills/research-artist-discography/scripts/research_artist_discography/providers.py`
- Create: `tests/research_artist_discography/test_providers.py`
- Create: `tests/research_artist_discography/fixtures/musicbrainz_artist.json`
- Create: `tests/research_artist_discography/fixtures/musicbrainz_release_groups.json`
- Create: `tests/research_artist_discography/fixtures/itunes_albums.json`

**Interfaces:**
- Consumes: `ReleaseCandidate` from Task 2.
- Produces: `parse_musicbrainz_artists`, `parse_musicbrainz_release_groups`, `parse_itunes_albums`, `search_musicbrainz_artist`, `fetch_musicbrainz_release_groups`, and `fetch_itunes_albums`.

- [ ] **Step 1: Add minimal provider fixtures**

Use a fictional artist so tests never assert live third-party data. Store the following JSON shapes:

```json
{"artists":[{"id":"artist-mbid-1","name":"Example Artist","country":"KR","score":100,"disambiguation":"K-pop group"}]}
```

```json
{"release-groups":[{"id":"rg-1","title":"First EP","first-release-date":"2025-01-02","primary-type":"EP","secondary-types":[]},{"id":"rg-2","title":"First Album","first-release-date":"2026-02-03","primary-type":"Album","secondary-types":[]}]}
```

```json
{"resultCount":2,"results":[{"wrapperType":"collection","collectionType":"Album","artistName":"Example Artist","collectionName":"First EP","collectionId":101,"releaseDate":"2025-01-02T00:00:00Z","primaryGenreName":"K-Pop","trackCount":6,"collectionViewUrl":"https://music.apple.com/example/101"},{"wrapperType":"collection","collectionType":"Album","artistName":"Example Artist","collectionName":"First Album","collectionId":102,"releaseDate":"2026-02-03T00:00:00Z","primaryGenreName":"K-Pop","trackCount":10,"collectionViewUrl":"https://music.apple.com/example/102"}]}
```

- [ ] **Step 2: Write failing parser tests**

```python
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
```

- [ ] **Step 3: Run tests and verify the provider module is missing**

Run:

```bash
python3 -m unittest tests.research_artist_discography.test_providers -v
```

Expected: `ERROR` importing `research_artist_discography.providers`.

- [ ] **Step 4: Implement provider parsers and HTTP functions**

Write `providers.py` with URL encoding, an identifying MusicBrainz user agent, a 15-second timeout, and no third-party package:

```python
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


def parse_musicbrainz_release_groups(artist_name: str, payload: Dict[str, Any]) -> List[ReleaseCandidate]:
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
    return parse_musicbrainz_artists(_get_json("https://musicbrainz.org/ws/2/artist/?%s" % query))


def fetch_musicbrainz_release_groups(artist_name: str, artist_mbid: str) -> List[ReleaseCandidate]:
    rows = []
    offset = 0
    while True:
        time.sleep(1.1)
        query = urlencode({"artist": artist_mbid, "fmt": "json", "limit": 100, "offset": offset})
        payload = _get_json("https://musicbrainz.org/ws/2/release-group?%s" % query)
        page = payload.get("release-groups", [])
        rows.extend(parse_musicbrainz_release_groups(artist_name, payload))
        offset += len(page)
        total = int(payload.get("release-group-count", offset))
        if not page or offset >= total:
            return rows


def fetch_itunes_albums(artist_name: str, country: str = "KR") -> List[ReleaseCandidate]:
    query = urlencode({"term": artist_name, "country": country, "media": "music", "entity": "album", "limit": 200})
    return parse_itunes_albums(artist_name, _get_json("https://itunes.apple.com/search?%s" % query))
```

- [ ] **Step 5: Run provider, matching, and model tests**

Run:

```bash
python3 -m unittest \
  tests.research_artist_discography.test_models \
  tests.research_artist_discography.test_matching \
  tests.research_artist_discography.test_providers -v
```

Expected: 11 tests pass and the command reports `OK`.

- [ ] **Step 6: Commit the credential-free catalog providers**

```bash
git add skills/research-artist-discography/scripts/research_artist_discography/providers.py tests/research_artist_discography/test_providers.py tests/research_artist_discography/fixtures
git commit -m "feat: collect free discography catalog sources"
```

---

### Task 5: Parse saved Circle and Oricon evidence without silently inventing sales

**Files:**
- Create: `skills/research-artist-discography/scripts/research_artist_discography/charts.py`
- Create: `tests/research_artist_discography/test_charts.py`
- Create: `tests/research_artist_discography/fixtures/circle_album_week.json`
- Create: `tests/research_artist_discography/fixtures/oricon_album_week.html`

**Interfaces:**
- Consumes: `ChartEntry` from Task 2.
- Produces: `parse_circle_album(payload, source_url, period_start, period_end) -> List[ChartEntry]` and `parse_oricon_album(html_text, source_url, period_start, period_end) -> List[ChartEntry]`.

- [ ] **Step 1: Add representative, minimal chart fixtures**

Write the Circle fixture with the real public response keys but fictional values:

```json
{"List":{"0":{"ARTIST_NAME":"Example Artist","ALBUM_NAME":"First EP","SERVICE_RANKING":"1","Album_CNT":"12,345","Total_CNT":"45,678","CntYN":"Y","de_nm":"Example Distribution"}},"ResultStatus":"SUCCESS"}
```

Write the Oricon fixture as Shift_JIS-decoded UTF-8 HTML:

```html
<html><body>
<section class="box-rank-entry" itemprop="itemListElement">
  <p class="num">1</p>
  <h2 class="title" itemprop="name">First EP</h2>
  <p class="name">Example Artist</p>
</section>
</body></html>
```

- [ ] **Step 2: Write failing chart parser tests**

```python
import json
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).with_name("fixtures")
sys.path.insert(0, os.fspath(ROOT / "skills" / "research-artist-discography" / "scripts"))

from research_artist_discography.charts import parse_circle_album, parse_oricon_album


class ChartParserTests(unittest.TestCase):
    def test_circle_emits_rank_and_shipment_observations_separately(self):
        payload = json.loads((FIXTURES / "circle_album_week.json").read_text(encoding="utf-8"))
        rows = parse_circle_album(payload, "https://circlechart.kr/example", "2025-01-01", "2025-01-07")
        self.assertEqual(["chart_rank", "shipment_net_returns"], [row.measurement_type for row in rows])
        self.assertEqual([1, 12345], [row.value for row in rows])

    def test_oricon_public_rank_does_not_become_estimated_sales(self):
        html = (FIXTURES / "oricon_album_week.html").read_text(encoding="utf-8")
        rows = parse_oricon_album(html, "https://www.oricon.co.jp/rank/ja/w/example/", "2025-01-01", "2025-01-07")
        self.assertEqual(1, len(rows))
        self.assertEqual("chart_rank", rows[0].measurement_type)
        self.assertNotEqual("estimated_sale", rows[0].measurement_type)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run tests and verify the charts module is missing**

Run:

```bash
python3 -m unittest tests.research_artist_discography.test_charts -v
```

Expected: `ERROR` importing `research_artist_discography.charts`.

- [ ] **Step 4: Implement the two saved-response parsers**

Write `charts.py` as:

```python
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


def parse_circle_album(payload: Dict[str, Any], source_url: str, period_start: str, period_end: str) -> List[ChartEntry]:
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
        output.append(ChartEntry(
            metric="chart_rank",
            value=_integer(row["SERVICE_RANKING"]),
            unit="rank",
            measurement_type="chart_rank",
            evidence="SERVICE_RANKING=%s" % row["SERVICE_RANKING"],
            **common
        ))
        if str(row.get("CntYN", "N")).casefold() == "y" and str(row.get("Album_CNT", "")).strip():
            output.append(ChartEntry(
                metric="album_units",
                value=_integer(row["Album_CNT"]),
                unit="copies",
                measurement_type="shipment_net_returns",
                evidence="Album_CNT=%s; distributor=%s" % (row["Album_CNT"], row.get("de_nm", "")),
                **common
            ))
    return output


def parse_oricon_album(html_text: str, source_url: str, period_start: str, period_end: str) -> List[ChartEntry]:
    sections = re.findall(r'<section class="box-rank-entry".*?</section>', html_text, flags=re.DOTALL)
    output = []
    for section in sections:
        rank = re.search(r'<p class="num[^\"]*">\s*([0-9]+)\s*</p>', section)
        title = re.search(r'<h2 class="title"[^>]*>(.*?)</h2>', section, flags=re.DOTALL)
        artist = re.search(r'<p class="name">(.*?)</p>', section, flags=re.DOTALL)
        if not (rank and title and artist):
            continue
        clean = lambda value: html.unescape(re.sub(r"<[^>]+>", "", value)).strip()
        output.append(ChartEntry(
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
        ))
    return output
```

- [ ] **Step 5: Run chart and semantic tests**

Run:

```bash
python3 -m unittest \
  tests.research_artist_discography.test_models \
  tests.research_artist_discography.test_charts -v
```

Expected: 5 tests pass and the command reports `OK`.

- [ ] **Step 6: Commit chart evidence parsing**

```bash
git add skills/research-artist-discography/scripts/research_artist_discography/charts.py tests/research_artist_discography/test_charts.py tests/research_artist_discography/fixtures/circle_album_week.json tests/research_artist_discography/fixtures/oricon_album_week.html
git commit -m "feat: parse labeled album chart evidence"
```

---

### Task 6: Validate normalized datasets and export observations safely

**Files:**
- Create: `skills/research-artist-discography/scripts/research_artist_discography/validation.py`
- Create: `tests/research_artist_discography/test_validation.py`

**Interfaces:**
- Consumes: serialized `ReleaseRecord` and `Observation` dictionaries.
- Produces: `validate_dataset(dataset) -> List[str]` and `write_observations_csv(dataset, destination) -> None`.

- [ ] **Step 1: Write failing dataset-invariant tests**

```python
import csv
import io
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, os.fspath(ROOT / "skills" / "research-artist-discography" / "scripts"))

from research_artist_discography.validation import validate_dataset, write_observations_csv


def dataset(measurement_type="chart_rank"):
    return {
        "schema_version": "1.0",
        "artist": {"id": "artist-1", "name": "Example Artist"},
        "releases": [{"release_group_id": "release-1", "release_type": "ep"}],
        "observations": [{
            "artist_id": "artist-1",
            "release_group_id": "release-1",
            "metric": "chart_rank",
            "value": 1,
            "unit": "rank",
            "measurement_type": measurement_type,
            "market": "KR",
            "period_start": "2025-01-01",
            "period_end": "2025-01-07",
            "observed_at": "2025-01-08T00:00:00+09:00",
            "source_tier": "A",
            "source_name": "Circle Chart",
            "source_url": "https://circlechart.kr/example",
            "evidence": "SERVICE_RANKING=1",
            "confidence": 1.0,
        }],
        "warnings": [],
    }


class ValidationTests(unittest.TestCase):
    def test_valid_dataset_has_no_errors(self):
        self.assertEqual([], validate_dataset(dataset()))

    def test_unknown_measurement_type_is_rejected(self):
        errors = validate_dataset(dataset("sales"))
        self.assertTrue(any("measurement_type" in error for error in errors))

    def test_csv_preserves_measurement_type_column(self):
        output = io.StringIO()
        write_observations_csv(dataset(), output)
        output.seek(0)
        row = next(csv.DictReader(output))
        self.assertEqual("chart_rank", row["measurement_type"])

    def test_missing_evidence_is_rejected(self):
        payload = dataset()
        payload["observations"][0]["evidence"] = ""
        self.assertTrue(any("evidence" in error for error in validate_dataset(payload)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify the validation module is missing**

Run:

```bash
python3 -m unittest tests.research_artist_discography.test_validation -v
```

Expected: `ERROR` importing `research_artist_discography.validation`.

- [ ] **Step 3: Implement deterministic validation and CSV export**

Write `validation.py` as:

```python
import csv
from typing import Any, Dict, List, TextIO

from .models import MEASUREMENT_TYPES, SOURCE_TIERS


OBSERVATION_COLUMNS = [
    "artist_id", "release_group_id", "edition_id", "release_type", "metric", "value", "unit",
    "measurement_type", "market", "period_start", "period_end", "observed_at", "source_tier",
    "source_name", "source_url", "evidence", "confidence",
]


def validate_dataset(dataset: Dict[str, Any]) -> List[str]:
    errors = []
    if dataset.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    artist = dataset.get("artist", {})
    if not artist.get("id") or not artist.get("name"):
        errors.append("artist id and name are required")
    release_rows = dataset.get("releases", [])
    release_ids = {row.get("release_group_id") for row in release_rows}
    if None in release_ids:
        errors.append("every release requires release_group_id")
    if len(release_ids) != len(release_rows):
        errors.append("release_group_id values must be unique")
    for index, row in enumerate(dataset.get("observations", [])):
        prefix = "observations[%d]" % index
        required = [
            "artist_id", "release_group_id", "release_type", "metric", "value", "unit",
            "measurement_type", "market", "period_start", "period_end", "observed_at",
            "source_tier", "source_name", "source_url", "evidence", "confidence",
        ]
        missing = [key for key in required if key not in row or row[key] is None or row[key] == ""]
        if missing:
            errors.append("%s missing required fields: %s" % (prefix, ", ".join(missing)))
        if row.get("artist_id") != artist.get("id"):
            errors.append("%s references an unknown artist" % prefix)
        if row.get("release_group_id") not in release_ids:
            errors.append("%s references an unknown release" % prefix)
        if row.get("measurement_type") not in MEASUREMENT_TYPES:
            errors.append("%s has unknown measurement_type" % prefix)
        if row.get("source_tier") not in SOURCE_TIERS:
            errors.append("%s has unknown source_tier" % prefix)
        if not str(row.get("source_url", "")).startswith(("http://", "https://")):
            errors.append("%s requires source_url" % prefix)
        if not row.get("period_start") or not row.get("period_end") or not row.get("observed_at"):
            errors.append("%s requires period and observed_at" % prefix)
        confidence = row.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0.0 <= confidence <= 1.0:
            errors.append("%s confidence must be between 0 and 1" % prefix)
    return errors


def write_observations_csv(dataset: Dict[str, Any], destination: TextIO) -> None:
    writer = csv.DictWriter(destination, fieldnames=OBSERVATION_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(dataset.get("observations", []))
```

- [ ] **Step 4: Run validation tests**

Run:

```bash
python3 -m unittest tests.research_artist_discography.test_validation -v
```

Expected: 4 tests pass and the command reports `OK`.

- [ ] **Step 5: Commit dataset validation**

```bash
git add skills/research-artist-discography/scripts/research_artist_discography/validation.py tests/research_artist_discography/test_validation.py
git commit -m "feat: validate discography observations"
```

---

### Task 7: Build the fixture-capable collector CLI

**Files:**
- Create: `skills/research-artist-discography/scripts/collect_discography_data.py`
- Create: `tests/research_artist_discography/test_cli.py`

**Interfaces:**
- Consumes: provider parsers/live functions, matching, chart parsers, model serialization, and dataset validation.
- Produces: `collect_discography_data.py ARTIST --output FILE [--csv FILE] [--fixture-dir DIR] [--artist-mbid MBID] [--country KR] [--include-non-default] [--circle-json FILE] [--oricon-html FILE]`.

- [ ] **Step 1: Write the failing fixture-mode end-to-end test**

```python
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "research-artist-discography" / "scripts" / "collect_discography_data.py"
FIXTURES = Path(__file__).with_name("fixtures")


class CollectorCliTests(unittest.TestCase):
    def test_fixture_mode_outputs_complete_release_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "discography.json"
            csv_output = Path(directory) / "observations.csv"
            result = subprocess.run([
                sys.executable, str(SCRIPT), "Example Artist",
                "--fixture-dir", str(FIXTURES),
                "--circle-json", str(FIXTURES / "circle_album_week.json"),
                "--period-start", "2025-01-01",
                "--period-end", "2025-01-07",
                "--output", str(output),
                "--csv", str(csv_output),
            ], text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("Example Artist", payload["artist"]["name"])
            self.assertEqual(["First EP", "First Album"], [row["title"] for row in payload["releases"]])
            self.assertEqual(["chart_rank", "shipment_net_returns"], [row["measurement_type"] for row in payload["observations"]])
            self.assertTrue(csv_output.is_file())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify the CLI is missing**

Run:

```bash
python3 -m unittest tests.research_artist_discography.test_cli -v
```

Expected: `FAIL` because `collect_discography_data.py` does not exist.

- [ ] **Step 3: Implement fixture and live catalog orchestration**

Write the CLI with these complete functions and flow:

```python
#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from research_artist_discography.charts import parse_circle_album, parse_oricon_album
from research_artist_discography.matching import find_release, filter_release_records, group_release_candidates
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


def load_catalog(artist_name, fixture_dir, artist_mbid, country):
    warnings = []
    if fixture_dir:
        artist_rows = parse_musicbrainz_artists(read_json(fixture_dir / "musicbrainz_artist.json"))
        musicbrainz = parse_musicbrainz_release_groups(artist_name, read_json(fixture_dir / "musicbrainz_release_groups.json"))
        itunes = parse_itunes_albums(artist_name, read_json(fixture_dir / "itunes_albums.json"))
        return artist_rows[0]["id"], musicbrainz + itunes, warnings

    candidates = search_musicbrainz_artist(artist_name)
    if not candidates:
        raise RuntimeError("MusicBrainz returned no artist candidates")
    selected = next((row for row in candidates if row["id"] == artist_mbid), None) if artist_mbid else candidates[0]
    if selected is None:
        raise RuntimeError("--artist-mbid was not present in MusicBrainz candidates")
    if len(candidates) > 1 and not artist_mbid:
        warnings.append("MusicBrainz top artist candidate selected; verify same-name ambiguity")
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


def main():
    args = parse_args()
    artist_id, candidates, warnings = load_catalog(args.artist, args.fixture_dir, args.artist_mbid, args.country)
    all_records = group_release_candidates(candidates)
    records = filter_release_records(all_records, include_non_default=args.include_non_default)
    observed_at = datetime.now(timezone.utc).isoformat()
    chart_entries = []
    if args.circle_json:
        chart_entries.extend(parse_circle_album(read_json(args.circle_json), "https://circlechart.kr/page_chart/album.circle", args.period_start, args.period_end))
    if args.oricon_html:
        chart_entries.extend(parse_oricon_album(args.oricon_html.read_text(encoding="utf-8"), "https://www.oricon.co.jp/rank/ja/w/", args.period_start, args.period_end))
    observations = attach_chart_entries(chart_entries, records, artist_id, observed_at, warnings)
    payload = {
        "schema_version": "1.0",
        "artist": {"id": artist_id, "name": args.artist},
        "releases": [to_dict(record) for record in records],
        "observations": [to_dict(row) for row in observations],
        "warnings": warnings,
        "collected_at": observed_at,
    }
    errors = validate_dataset(payload)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", encoding="utf-8", newline="") as handle:
            write_observations_csv(payload, handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the CLI test and inspect the normalized artifact**

Run:

```bash
python3 -m unittest tests.research_artist_discography.test_cli -v
tmpdir="$(mktemp -d)"
python3 skills/research-artist-discography/scripts/collect_discography_data.py \
  'Example Artist' \
  --fixture-dir tests/research_artist_discography/fixtures \
  --circle-json tests/research_artist_discography/fixtures/circle_album_week.json \
  --period-start 2025-01-01 \
  --period-end 2025-01-07 \
  --output "$tmpdir/discography.json" \
  --csv "$tmpdir/observations.csv"
python3 -m json.tool "$tmpdir/discography.json" >/dev/null
test "$(wc -l < "$tmpdir/observations.csv" | tr -d ' ')" -eq 3
```

Expected: the unit test reports `OK`, JSON validation exits 0, and CSV contains one header plus two observations.

- [ ] **Step 5: Commit the collector CLI**

```bash
git add skills/research-artist-discography/scripts/collect_discography_data.py tests/research_artist_discography/test_cli.py
git commit -m "feat: add fixture-capable discography collector"
```

---

### Task 8: Verify the whole skill, smoke-test live catalog discovery, and install it locally

**Files:**
- Modify: `tests/research_artist_discography/test_skill_contract.py`
- Modify: `skills/research-artist-discography/SKILL.md`
- Modify only if stale: `skills/research-artist-discography/agents/openai.yaml`

**Interfaces:**
- Consumes: every artifact and command from Tasks 1–7.
- Produces: a validated, locally discoverable `$research-artist-discography` skill and a recorded deterministic test result.

- [ ] **Step 1: Strengthen the contract test for metric and access safeguards**

Add this method to `SkillContractTests`:

```python
    def test_skill_preserves_metric_and_access_boundaries(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        source_policy = (SKILL / "references" / "source-policy.md").read_text(encoding="utf-8")
        schema = (SKILL / "references" / "data-schema.md").read_text(encoding="utf-8")
        report = (SKILL / "references" / "report-format.md").read_text(encoding="utf-8")
        self.assertIn("Never estimate a missing number", skill)
        self.assertIn("Never bypass Cloudflare", source_policy)
        self.assertIn("shipment_net_returns", schema)
        self.assertIn("retail_sale", schema)
        self.assertIn("estimated_sale", schema)
        self.assertIn("Do not place unlike units on one axis", report)
```

- [ ] **Step 2: Run the complete deterministic suite and official validator**

Run:

```bash
python3 -m unittest discover -s tests/research_artist_discography -p 'test_*.py' -v
uv run --with pyyaml python /Users/mintplo/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/research-artist-discography
git diff --check
rg -n 'T[B]D|T[O]DO|FIX[M]E' skills/research-artist-discography tests/research_artist_discography && exit 1 || true
```

Expected: all deterministic tests pass, the validator prints `Skill is valid!`, `git diff --check` is silent, and the unfinished-marker scan finds no matches.

- [ ] **Step 3: Run a non-gating live catalog smoke test**

Run:

```bash
tmpdir="$(mktemp -d)"
python3 skills/research-artist-discography/scripts/collect_discography_data.py \
  'BTS' \
  --country KR \
  --output "$tmpdir/bts.json"
python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); assert p["artist"]["name"] == "BTS"; assert len(p["releases"]) > 0' "$tmpdir/bts.json"
```

Expected when providers are reachable: exit 0 with at least one normalized release. If the network, rate limit, or upstream schema fails, record the exact error as a live-provider limitation; do not weaken the deterministic acceptance suite and do not claim live collection passed.

- [ ] **Step 4: Commit final contract adjustments**

```bash
git add skills/research-artist-discography tests/research_artist_discography
git commit -m "test: verify artist discography skill end to end"
```

If Step 4 has no diff because the contract already matched, do not create an empty commit.

- [ ] **Step 5: Install the validated skill from the stable workspace path**

Run only after the implementation commit exists in `/Users/mintplo/Documents/음악 산업 분석`:

```bash
source_path='/Users/mintplo/Documents/음악 산업 분석/skills/research-artist-discography'
target_path="$HOME/.codex/skills/research-artist-discography"
test -f "$source_path/SKILL.md"
if [ -e "$target_path" ] || [ -L "$target_path" ]; then
  test "$(readlink "$target_path")" = "$source_path"
else
  ln -s "$source_path" "$target_path"
fi
test -f "$target_path/SKILL.md"
```

Expected: the target is either the already-correct symlink or a newly created symlink to the version-controlled skill. Stop and ask before replacing any pre-existing nonmatching path.

- [ ] **Step 6: Perform a user-shaped forward check without private credentials**

Start a fresh Codex task after the skill list reloads and request:

```text
Use $research-artist-discography to 조사해줘: 에스파의 전체 디스코그래피를 먼저 보여주고, 최근 세 발매작의 콘셉트·한국 차트 근거·YouTube 반응을 같은 기간 기준으로 비교해줘. 없는 판매량은 추정하지 마.
```

Acceptance criteria:

- The answer begins from the artist and preserves the complete release inventory.
- The latest-three filter changes detail, not the underlying inventory.
- Every numeric value has a direct source, period, market, observation time, and measurement type.
- Circle shipments, retail sales, Oricon ranks, and article claims are not combined.
- Missing authenticated SNS data is labeled unavailable rather than inferred.
- A chart appears only for comparable numeric observations; otherwise the answer explains the omission.

Record any failure as a focused change to `SKILL.md`, one reference, or one deterministic module, then rerun Step 2 before claiming completion.

---

## Completion Checklist

- [ ] The repository contains only essential skill files, scripts, tests, and the approved design/plan documents.
- [ ] Artist-name-only fixture mode returns the full default release inventory.
- [ ] Release editions remain traceable to original source identifiers.
- [ ] Default and excluded release types match the approved design.
- [ ] Catalog providers require no credentials; unavailable live providers fail visibly.
- [ ] Chart rank and quantity observations stay separate.
- [ ] Oricon rank-only HTML never produces estimated sales.
- [ ] Dataset validation rejects unknown metric semantics and missing source evidence.
- [ ] JSON and CSV exports retain measurement type and source fields.
- [ ] All deterministic tests pass in one fresh command.
- [ ] The official skill validator reports `Skill is valid!`.
- [ ] The installed path is a non-destructive symlink to the stable version-controlled skill.
- [ ] The user-shaped forward check either passes or produces explicitly documented limitations and a rerun.
