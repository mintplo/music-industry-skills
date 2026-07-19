# Research Music Skills Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a document-first `research-music` Codex skill library that chooses and combines music APIs, web research, and crawling tools according to each question instead of forcing a fixed album-report workflow.

**Architecture:** A concise model-invoked `SKILL.md` performs question decomposition and builds a query-specific **source stack**. Provider capabilities, access rules, fallbacks, and official documentation live in co-located Markdown cards; optional recipe documents describe common branches without becoming hard sub-skills. Existing deterministic discography code remains available and moves under the new skill only after the document-first workflow passes independent forward tests.

**Tech Stack:** Codex Agent Skills (`SKILL.md`, `agents/openai.yaml`), Markdown, Bash installation helpers, Python 3.9+ standard library, `unittest`, existing MusicBrainz/iTunes/Circle/Oricon parsers, web search and browser tools supplied by the active Codex runtime.

## Global Constraints

- Execute directly on the existing `main` branch; do not create or use a worktree.
- Benchmark only the structure and composition principles of `mattpocock/skills`; do not copy its skill content.
- Make `research-music` model-invoked with rich triggers for artists, releases, campaigns, charts, video/social signals, comparisons, and music-market trends.
- Keep provider discovery document-based; do not add a runtime Provider Registry, server, database, or mandatory MCP dependency.
- Keep question-specific procedures as optional recipe references, not nested or mandatory sub-skills.
- Put only steps common to every branch in `SKILL.md`; disclose provider, recipe, evidence, entity, and metric details behind explicit context pointers.
- Use official and primary sources first. Preserve source URL, market, period, measurement definition, observation date, and official/unofficial status whenever a performance number is used.
- Never bypass authentication, robots directives, rate limits, site terms, or anti-bot controls.
- Do not force a complete discography, fixed report template, JSON schema, chart, or table when the user's question does not require one.
- Add a script only when a repeated deterministic operation already exists or is proven necessary.
- Preserve the current `research-artist-discography` installation until the new skill passes independent forward tests.
- Use `apply_patch` for authored file edits. Mechanical path moves may use `git mv`.
- Use TDD for Python/Bash behavior and pressure-scenario forward tests for skill behavior.

## File Map

```text
skills/
├── music/
│   ├── README.md                                  # Human index and invocation split
│   └── research-music/
│       ├── SKILL.md                               # Common source-stack steps
│       ├── agents/openai.yaml                     # Codex model-invoked metadata
│       ├── providers/
│       │   ├── CATALOG.md                         # Capability → provider pointers
│       │   ├── musicbrainz.md                     # Identity/release groups
│       │   ├── wikidata.md                        # Identity/structured facts
│       │   ├── spotify.md                         # Credentialed catalog
│       │   ├── apple-music.md                     # No-key catalog fallback
│       │   ├── youtube.md                         # Video/channel observations
│       │   ├── circle-chart.md                    # Korean chart definitions
│       │   ├── oricon.md                          # Japanese public chart pages
│       │   ├── web-search.md                      # Primary-source discovery
│       │   └── web-crawling.md                    # Static/browser fallback
│       ├── recipes/
│       │   ├── artist-and-album.md                # Artist/release branch
│       │   ├── release-campaign.md                # Promotion timeline branch
│       │   ├── artist-comparison.md               # Comparable evidence branch
│       │   └── market-trend.md                    # Sampling/trend branch
│       ├── references/
│       │   ├── evidence-policy.md                 # Evidence/source ladder
│       │   ├── entity-resolution.md               # Artist/release/edition identity
│       │   └── metric-compatibility.md             # Comparison rules
│       └── scripts/                               # Added only during legacy migration
├── in-progress/
└── deprecated/

scripts/
├── list-skills.sh                                 # Recursive active-skill listing
└── link-skills.sh                                 # Safe Codex symlink installer

tests/
├── research_music/
│   ├── test_skill_contract.py                     # Invocation and common-step contract
│   ├── test_provider_catalog.py                   # Provider-card shape/pointers
│   ├── test_recipes.py                            # Branch disclosure contract
│   ├── test_skill_discovery.py                    # List/link helper behavior
│   └── forward_cases.md                           # Fresh-context evaluation prompts
└── research_music_discography/                    # Migrated deterministic legacy tests
```

---

### Task 1: Create the model-invoked core skill and a minimal working source stack

**Files:**
- Create: `skills/music/README.md`
- Create: `skills/music/research-music/SKILL.md`
- Create: `skills/music/research-music/agents/openai.yaml`
- Create: `skills/music/research-music/providers/CATALOG.md`
- Create: `skills/music/research-music/providers/musicbrainz.md`
- Create: `skills/music/research-music/providers/web-search.md`
- Create: `skills/music/research-music/references/evidence-policy.md`
- Create: `skills/music/research-music/references/entity-resolution.md`
- Create: `skills/music/research-music/references/metric-compatibility.md`
- Create: `skills/in-progress/README.md`
- Create: `skills/deprecated/README.md`
- Create: `tests/research_music/__init__.py`
- Create: `tests/research_music/test_skill_contract.py`

**Interfaces:**
- Consumes: approved design `docs/superpowers/specs/2026-07-19-music-research-skills-library-design.md`.
- Produces: a valid `$research-music` skill whose common steps and first two provider cards can answer basic artist/release questions without a fixed report shape.

- [ ] **Step 1: Write the failing skill contract**

Create `tests/research_music/test_skill_contract.py`:

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "music" / "research-music"


class ResearchMusicSkillContractTests(unittest.TestCase):
    def test_core_skill_is_model_invoked_and_document_first(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: research-music\n"))
        self.assertIn("source stack", text.casefold())
        self.assertIn("providers/CATALOG.md", text)
        self.assertIn("references/evidence-policy.md", text)
        self.assertIn("references/entity-resolution.md", text)
        self.assertIn("references/metric-compatibility.md", text)
        self.assertNotIn("disable-model-invocation", text)
        self.assertNotIn("Provider Registry", text)
        self.assertNotIn("complete discography", text.casefold())
        self.assertLessEqual(len(text.splitlines()), 180)

    def test_metadata_and_minimum_provider_cards_exist(self):
        required = [
            SKILL / "agents" / "openai.yaml",
            SKILL / "providers" / "CATALOG.md",
            SKILL / "providers" / "musicbrainz.md",
            SKILL / "providers" / "web-search.md",
        ]
        self.assertEqual([], [str(path) for path in required if not path.is_file()])
        metadata = required[0].read_text(encoding="utf-8")
        self.assertIn('$research-music', metadata)
        self.assertNotIn("allow_implicit_invocation: false", metadata)

    def test_common_steps_end_on_question_requirements_not_a_template(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Every requested branch", text)
        self.assertIn("supported, unavailable, or access-dependent", text)
        self.assertIn("Do not add sections the user did not ask for", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the contract test and verify RED**

Run:

```bash
python3 -m unittest tests.research_music.test_skill_contract -v
```

Expected: `ERROR` or `FAIL` because `skills/music/research-music/SKILL.md` does not exist.

- [ ] **Step 3: Initialize the official skill scaffold**

Run:

```bash
python3 /Users/mintplo/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  research-music \
  --path skills/music \
  --resources scripts,references \
  --interface 'display_name=Music Industry Researcher' \
  --interface 'short_description=음악 아티스트·발매·캠페인·성과·시장 정보를 출처 기반으로 조사' \
  --interface 'default_prompt=Use $research-music to research this music-industry question with the best available APIs and web sources.'
```

Expected: the scaffold creates `SKILL.md`, `agents/openai.yaml`, `scripts/`, and `references/` under `skills/music/research-music/`.

- [ ] **Step 4: Replace the scaffold with the common source-stack steps**

Write `SKILL.md` with this behavior:

```markdown
---
name: research-music
description: Research music artists, releases, songs, campaigns, charts, sales, video or public social signals, competitors, and market trends. Use when Codex needs to combine music APIs, official sites, web search, or permitted crawling to answer a music-industry question with sourced evidence.
---

# Research Music

Build a **source stack** for the question: the smallest useful combination of providers, search paths, and evidence rules that can close the user's requested branches.

## Steps

1. Decompose the request into concrete information needs. Preserve the user's scope; do not silently turn a narrow question into a full artist report.
2. Resolve artists, releases, songs, editions, markets, and dates before attaching performance evidence. Read `references/entity-resolution.md` when identity is not trivial.
3. Read `providers/CATALOG.md`, then load only the provider cards needed for this source stack. Check current tool and credential availability before choosing an access path.
4. Research from primary and official sources first. Read `references/evidence-policy.md` before using facts, numbers, articles, wikis, or crawled pages.
5. When comparing numbers, read `references/metric-compatibility.md` and compare only compatible observations. Keep incompatible evidence separate.
6. Synthesize in the shape the user asked for. Do not add sections the user did not ask for, and do not invent unavailable values.

## Completion criterion

Every requested branch is closed as supported, unavailable, or access-dependent. Every material factual claim has a direct source; every performance number retains its market, period, measurement, and observation date. The answer contains no forced report sections outside the user's request.
```

Keep `agents/openai.yaml` model-invoked and set its `default_prompt` to the scaffold command's exact value.

- [ ] **Step 5: Write the minimal catalog and common references**

Create `providers/CATALOG.md` with a capability table pointing identity/releases to `musicbrainz.md` and primary-source discovery to `web-search.md`. State that a source stack loads only relevant cards and that a new provider is registered by adding its card plus one capability pointer; do not describe runtime registration.

Write both provider cards with the Task 2 provider-card headings. Use these primary sources:

- MusicBrainz API and rate limits: `https://musicbrainz.org/doc/MusicBrainz_API` and `https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting`
- Codex web search: describe the active runtime's web tool, primary-source preference, date checking, and direct-link citation; do not claim a vendor API contract.

Write the references with these exact sections and completion rules:

- `evidence-policy.md`: `## Source ladder` (official/primary → corroborated press → reference-only), `## Claims` (direct adjacent source for material facts), `## Performance observations` (source URL, market, period, measurement, observed_at, official status), `## Missing and conflicting evidence`, `## Access boundaries`. End with: every requested claim is sourced, qualified, or explicitly unavailable.
- `entity-resolution.md`: `## Artist`, `## Release group and edition`, `## Participation role`, `## Matching order`, `## Unresolved identity`. Require stable provider IDs before fuzzy title/date matching, preserve editions under one group, and keep the researched artist's primary versus guest role explicit.
- `metric-compatibility.md`: `## Comparison key`, `## Compatible observations`, `## Incompatible observations`, `## Rank display`, `## Missing values`. Define the exact key `{market, metric, unit, measurement_type, period_basis, window_length}`, forbid cross-key sums or synthetic scores, and require reversed rank axes when rank is charted.

- [ ] **Step 6: Create the bucket README**

Write `skills/music/README.md`:

```markdown
# Music

Document-first skills for music-industry research.

## Model-invoked

- **[research-music](./research-music/SKILL.md)** — Build a question-specific source stack from music APIs, official pages, web search, and permitted crawling.

## User-invoked

No router yet. Add `ask-music` only when several user-invoked skills create real cognitive load.
```

Create `skills/in-progress/README.md` stating that experimental skills may change and are not promoted. Create `skills/deprecated/README.md` stating that historical skills are excluded from active listing and installation.

- [ ] **Step 7: Verify GREEN and validate the skill**

Run:

```bash
python3 -m unittest tests.research_music.test_skill_contract -v
uv run --with pyyaml python /Users/mintplo/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/music/research-music
git diff --check
```

Expected: all contract tests pass, validator prints `Skill is valid!`, and `git diff --check` exits 0.

- [ ] **Step 8: Commit**

```bash
git add skills/music skills/in-progress/README.md skills/deprecated/README.md tests/research_music
git commit -m "feat: scaffold document-first music research skill"
```

---

### Task 2: Expand the document-based Provider Catalog

**Files:**
- Create: `skills/music/research-music/providers/wikidata.md`
- Create: `skills/music/research-music/providers/spotify.md`
- Create: `skills/music/research-music/providers/apple-music.md`
- Create: `skills/music/research-music/providers/youtube.md`
- Create: `skills/music/research-music/providers/circle-chart.md`
- Create: `skills/music/research-music/providers/oricon.md`
- Create: `skills/music/research-music/providers/web-crawling.md`
- Modify: `skills/music/research-music/providers/CATALOG.md`
- Test: `tests/research_music/test_provider_catalog.py`

**Interfaces:**
- Consumes: source-stack pointer `providers/CATALOG.md` from Task 1.
- Produces: nine provider cards with one consistent information hierarchy and capability-to-provider pointers.

- [ ] **Step 1: Write the failing provider-card contract**

Create `tests/research_music/test_provider_catalog.py`:

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PROVIDERS = ROOT / "skills" / "music" / "research-music" / "providers"
EXPECTED = {
    "musicbrainz.md", "wikidata.md", "spotify.md", "apple-music.md",
    "youtube.md", "circle-chart.md", "oricon.md", "web-search.md",
    "web-crawling.md",
}
HEADINGS = {
    "## Capabilities", "## Use when", "## Do not use for", "## Access",
    "## Inputs and outputs", "## Evidence", "## Limits and terms",
    "## Fallbacks", "## Verification",
}


class ProviderCatalogTests(unittest.TestCase):
    def test_all_initial_provider_cards_exist_and_are_reachable(self):
        catalog = (PROVIDERS / "CATALOG.md").read_text(encoding="utf-8")
        actual = {path.name for path in PROVIDERS.glob("*.md")} - {"CATALOG.md"}
        self.assertEqual(EXPECTED, actual)
        for name in EXPECTED:
            self.assertIn(f"({name})", catalog)

    def test_every_card_uses_the_same_information_hierarchy(self):
        for name in EXPECTED:
            text = (PROVIDERS / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertTrue(text.startswith("# "))
                self.assertTrue(HEADINGS.issubset(set(text.splitlines())))
                self.assertIn("Last verified: 2026-07-19", text)
                self.assertRegex(text, r"https://")
                self.assertNotRegex(text, r"\b(T[B]D|T[O]DO|FIX[M]E)\b")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the contract and verify RED**

Run:

```bash
python3 -m unittest tests.research_music.test_provider_catalog -v
```

Expected: `FAIL` listing the seven missing provider cards.

- [ ] **Step 3: Write every provider card from primary sources**

Use the exact headings in the test and end each card with `Last verified: 2026-07-19`. Keep each fact in only one card. Populate the cards with this provider matrix:

| Card | Capabilities | Access | Never claim | Fallback | Primary documentation |
|---|---|---|---|---|---|
| `wikidata.md` | entity IDs, aliases, structured dates/links | SPARQL/Action API, no key | completeness or release performance | MusicBrainz, official pages | `https://www.wikidata.org/wiki/Wikidata:Data_access` |
| `spotify.md` | credentialed artist/album/track catalog | Web API client credentials/user auth as required | sales, historical popularity, universal availability | Apple Music, MusicBrainz | `https://developer.spotify.com/documentation/web-api` |
| `apple-music.md` | iTunes no-key catalog cross-check; Apple Music catalog when token exists | iTunes Search or MusicKit token | sales/performance from catalog fields | MusicBrainz, Spotify | `https://performance-partners.apple.com/search-api` and `https://developer.apple.com/documentation/applemusicapi` |
| `youtube.md` | video/channel identity and current public statistics | YouTube Data API key/OAuth | historical first-day metrics from current counters; YouTube Analytics without owner access | official video pages, clearly labelled public trackers | `https://developers.google.com/youtube/v3/docs` and `https://developers.google.com/youtube/v3/determine_quota_cost` |
| `circle-chart.md` | Korean chart ranks, album shipment versus retail definitions | public official pages; undocumented page routes only at low frequency | rank as sales; shipment as retail sale | official certification/press, unavailable | `https://circlechart.kr/` |
| `oricon.md` | Japanese public ranking evidence and values explicitly shown | public HTML, no assumed public API | sales inferred from rank | label/press, unavailable | `https://www.oricon.co.jp/rank/` |
| `web-crawling.md` | static page extraction and browser rendering when necessary | static HTML first, active browser/agent-browser second | permission to bypass login, Cloudflare, robots, or terms | web search snippets plus direct official pages | `https://www.rfc-editor.org/rfc/rfc9309` |

Update the existing MusicBrainz and web-search cards to the same headings if Task 1's minimal versions differ.

- [ ] **Step 4: Expand the capability catalog without duplicating card facts**

Make `CATALOG.md` a compact mapping with these branches:

```markdown
| Need | Start with | Add when needed |
|---|---|---|
| Artist/release identity | [MusicBrainz](musicbrainz.md), [Wikidata](wikidata.md) | [Spotify](spotify.md), [Apple Music](apple-music.md) |
| Album/track catalog | [MusicBrainz](musicbrainz.md), [Apple Music](apple-music.md) | [Spotify](spotify.md) |
| Korean chart evidence | [Circle Chart](circle-chart.md) | [Web search](web-search.md) |
| Japanese chart evidence | [Oricon](oricon.md) | [Web search](web-search.md) |
| Video/channel signals | [YouTube](youtube.md) | [Web search](web-search.md) |
| Concepts/interviews/campaigns | [Web search](web-search.md) | [Web crawling](web-crawling.md) |
```

State a checkable selection rule: load every card needed to close the request, but no unrelated cards; record why each selected provider is in the source stack.

- [ ] **Step 5: Verify and commit**

Run:

```bash
python3 -m unittest tests.research_music.test_provider_catalog -v
python3 -m unittest discover -s tests/research_music -p 'test_*.py' -v
git diff --check
```

Expected: all tests pass.

```bash
git add skills/music/research-music/providers tests/research_music/test_provider_catalog.py
git commit -m "docs: add music research provider catalog"
```

---

### Task 3: Add optional research recipes and branch pointers

**Files:**
- Create: `skills/music/research-music/recipes/artist-and-album.md`
- Create: `skills/music/research-music/recipes/release-campaign.md`
- Create: `skills/music/research-music/recipes/artist-comparison.md`
- Create: `skills/music/research-music/recipes/market-trend.md`
- Modify: `skills/music/research-music/SKILL.md`
- Test: `tests/research_music/test_recipes.py`

**Interfaces:**
- Consumes: provider names and evidence references from Tasks 1–2.
- Produces: four optional question branches that compose providers without introducing nested skills or fixed output templates.

- [ ] **Step 1: Write the failing recipe contract**

Create `tests/research_music/test_recipes.py`:

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "music" / "research-music"
RECIPES = {
    "artist-and-album.md": "artist, release, album, song, track-list, or discography",
    "release-campaign.md": "rollout, teaser, promotion, media, or comeback-campaign",
    "artist-comparison.md": "artist or release comparisons",
    "market-trend.md": "genre, platform, country, audience, or market-pattern",
}


class RecipeContractTests(unittest.TestCase):
    def test_every_branch_has_a_context_pointer_and_recipe(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for name, trigger in RECIPES.items():
            self.assertTrue((SKILL / "recipes" / name).is_file())
            self.assertIn(trigger, skill)
            self.assertIn(f"recipes/{name}", skill)

    def test_recipes_compose_source_stacks_without_fixed_outputs(self):
        for name in RECIPES:
            text = (SKILL / "recipes" / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertIn("## Source stack", text)
                self.assertIn("## Completion criterion", text)
                self.assertNotIn("must always return", text.casefold())
                self.assertNotIn("Provider Registry", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the contract and verify RED**

Run:

```bash
python3 -m unittest tests.research_music.test_recipes -v
```

Expected: `FAIL` because the recipe files do not exist.

- [ ] **Step 3: Write the four recipes**

Each recipe uses these headings: `#`, `## Use this branch`, `## Questions to resolve`, `## Source stack`, `## Evidence checks`, `## Completion criterion`.

Use these exact branch requirements:

- `artist-and-album.md`: resolve primary artist and release group; use catalog providers for identity, official pages/press for concept, performance providers only when asked; a single-album question never requires the full discography.
- `release-campaign.md`: define campaign window; collect official teaser/MV/event posts and attributable press; distinguish planned activity from observed reaction; produce a timeline only when chronology matters.
- `artist-comparison.md`: define entities, market, relative period, metric, unit, and measurement before collection; show incompatible evidence separately; never create an overall synthetic score.
- `market-trend.md`: define population, sample, geography, and observation window; gather multiple examples plus counterexamples; label inference and sampling limits; do not generalize from one artist.

Each recipe names relevant cards from `../providers/` but leaves final output shape conditional on the request.

- [ ] **Step 4: Tighten the SKILL context pointers**

Add a `## Branch pointers` section with the four exact trigger strings and recipe paths from the test. Each pointer says to read the recipe only when that branch appears in the user's request. Do not copy recipe steps into `SKILL.md`.

- [ ] **Step 5: Verify and commit**

Run:

```bash
python3 -m unittest discover -s tests/research_music -p 'test_*.py' -v
uv run --with pyyaml python /Users/mintplo/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/music/research-music
git diff --check
```

Expected: all tests pass and the skill validator prints `Skill is valid!`.

```bash
git add skills/music/research-music/SKILL.md skills/music/research-music/recipes tests/research_music/test_recipes.py
git commit -m "docs: add composable music research recipes"
```

---

### Task 4: Add recursive skill discovery and a safe local linker

**Files:**
- Create: `scripts/list-skills.sh`
- Create: `scripts/link-skills.sh`
- Test: `tests/research_music/test_skill_discovery.py`

**Interfaces:**
- Consumes: nested `skills/music/research-music/SKILL.md` layout.
- Produces: newline-delimited active skill paths and safe symlinks under `${CODEX_HOME:-$HOME/.codex}/skills/<skill-name>`.

- [ ] **Step 1: Write failing black-box tests**

Create `tests/research_music/test_skill_discovery.py` with `subprocess.run` tests that assert:

```python
def test_list_skills_finds_nested_active_skill_and_excludes_deprecated():
    result = subprocess.run(
        [str(ROOT / "scripts" / "list-skills.sh")],
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    self.assertIn("skills/music/research-music/SKILL.md", result.stdout.splitlines())
    self.assertFalse(any("/deprecated/" in line for line in result.stdout.splitlines()))

def test_link_skills_uses_codex_home_and_does_not_replace_regular_files():
    with tempfile.TemporaryDirectory() as directory:
        env = {**os.environ, "CODEX_HOME": directory}
        subprocess.run([str(ROOT / "scripts" / "link-skills.sh")], cwd=ROOT, env=env, check=True)
        target = Path(directory) / "skills" / "research-music"
        self.assertTrue(target.is_symlink())
        target.unlink()
        target.write_text("user-owned", encoding="utf-8")
        result = subprocess.run(
            [str(ROOT / "scripts" / "link-skills.sh")], cwd=ROOT, env=env,
            text=True, capture_output=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("user-owned", target.read_text(encoding="utf-8"))

def test_link_skills_does_not_replace_foreign_symlinks():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        foreign = root / "foreign"
        foreign.mkdir()
        target_dir = root / "skills"
        target_dir.mkdir()
        target = target_dir / "research-music"
        target.symlink_to(foreign, target_is_directory=True)
        env = {**os.environ, "CODEX_HOME": directory}
        result = subprocess.run(
            [str(ROOT / "scripts" / "link-skills.sh")], cwd=ROOT, env=env,
            text=True, capture_output=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(foreign, target.resolve())
```

Include imports for `os`, `Path`, `subprocess`, `tempfile`, and `unittest`; define `ROOT = Path(__file__).resolve().parents[2]`.

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python3 -m unittest tests.research_music.test_skill_discovery -v
```

Expected: `ERROR` because the scripts do not exist.

- [ ] **Step 3: Implement `list-skills.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
find skills -name SKILL.md \
  -not -path '*/deprecated/*' \
  -not -path '*/node_modules/*' \
  | sort
```

- [ ] **Step 4: Implement `link-skills.sh`**

Write the complete portable Bash script:

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${CODEX_HOME:-$HOME/.codex}/skills"
NAMES_FILE="$(mktemp)"
SKILLS_FILE="$(mktemp)"
trap 'rm -f "$NAMES_FILE" "$SKILLS_FILE"' EXIT

mkdir -p "$DEST"
"$REPO/scripts/list-skills.sh" > "$SKILLS_FILE"

while IFS= read -r skill_path; do
  source_dir="$REPO/${skill_path%/SKILL.md}"
  name="$(basename "$source_dir")"
  target="$DEST/$name"

  if grep -Fqx "$name" "$NAMES_FILE"; then
    echo "error: duplicate active skill name: $name" >&2
    exit 1
  fi
  printf '%s\n' "$name" >> "$NAMES_FILE"

  if { [ -e "$target" ] || [ -L "$target" ]; } && [ ! -L "$target" ]; then
    echo "error: refusing to replace non-symlink target: $target" >&2
    exit 1
  fi

  if [ -L "$target" ]; then
    current="$(readlink "$target")"
    case "$current" in
      "$REPO"/*) ;;
      *)
        echo "error: refusing to replace foreign symlink: $target -> $current" >&2
        exit 1
        ;;
    esac
  fi
done < "$SKILLS_FILE"

while IFS= read -r skill_path; do
  source_dir="$REPO/${skill_path%/SKILL.md}"
  name="$(basename "$source_dir")"
  target="$DEST/$name"
  ln -sfn "$source_dir" "$target"
  echo "linked $name -> $source_dir"
done < "$SKILLS_FILE"
```

Do not delete unrecognized files or stale links in this first version.

- [ ] **Step 5: Verify and commit**

Run:

```bash
chmod +x scripts/list-skills.sh scripts/link-skills.sh
python3 -m unittest tests.research_music.test_skill_discovery -v
git diff --check
```

Expected: both black-box tests pass.

```bash
git add scripts/list-skills.sh scripts/link-skills.sh tests/research_music/test_skill_discovery.py
git commit -m "feat: discover and link nested music skills"
```

---

### Task 5: Forward-test the document-first behavior across five branches

**Files:**
- Create: `tests/research_music/forward_cases.md`
- Modify only when a failure is observed: `skills/music/research-music/SKILL.md`, provider cards, recipes, or references
- Record ignored artifacts: `.superpowers/sdd/research-music-forward-*.md`

**Interfaces:**
- Consumes: complete document-first skill from Tasks 1–4.
- Produces: pressure-scenario evidence that the skill selects query-specific source stacks and does not regress to a fixed discography report.

- [ ] **Step 1: Write the forward cases before revising behavior**

Create `tests/research_music/forward_cases.md` containing these exact user prompts:

```markdown
# Research Music Forward Cases

1. 코르티스의 새 앨범이 어떤 앨범인지, 콘셉트와 공개 후 초기 반응을 조사해줘.
2. aespa의 LEMONADE 컴백에서 첫 티저부터 발매 후 일주일까지 프로모션 흐름을 조사해줘.
3. aespa와 IVE의 2025~2026년 일본 시장 반응을 같은 기준으로 비교해줘. 비교가 안 되는 수치는 분리해줘.
4. 최근 K-pop 걸그룹의 선공개 싱글 활용 방식에 공통 패턴이 있는지 조사해줘.
5. aespa의 Whiplash가 처음 발매된 날짜와 수록 앨범만 알려줘.
```

Success signals:

- Cases 1–4 name or visibly use more than one relevant provider family.
- Case 5 stays short and does not generate a full artist report.
- Every case closes unavailable branches explicitly rather than inventing data.
- No case loads unrelated provider cards or forces all recipes.

- [ ] **Step 2: Run each case in a fresh-context subagent**

For each prompt, dispatch a fresh agent with only the skill path and prompt. Instruct it not to inspect tests, plans, prior outputs, or `.superpowers`. Save each complete answer to `.superpowers/sdd/research-music-forward-<n>.md`.

Expected: five independent outputs exist.

- [ ] **Step 3: Dispatch a separate behavior reviewer**

Give the reviewer only `SKILL.md`, relevant disclosed documents, `forward_cases.md`, and raw outputs. Require a per-case PASS/FAIL on source-stack relevance, evidence discipline, scope preservation, and completion criterion. Do not ask the reviewer to fact-check live web values.

- [ ] **Step 4: Close observed loopholes with writing-skills TDD**

For every FAIL:

1. preserve the raw failing output;
2. add a focused contract assertion or forward success signal;
3. change the smallest authoritative document;
4. rerun only the failed branch in a new context;
5. rerun the reviewer.

Stop adding prose if the failure belongs to a deterministic existing script; link that script from the provider card instead.

- [ ] **Step 5: Verify and commit the evaluation contract**

Run:

```bash
python3 -m unittest discover -s tests/research_music -p 'test_*.py' -v
uv run --with pyyaml python /Users/mintplo/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/music/research-music
git diff --check
```

Expected: all deterministic tests pass, validator is valid, and all five final behavior reviews are PASS.

```bash
git add tests/research_music/forward_cases.md skills/music/research-music
git commit -m "test: verify adaptive music research behavior"
```

---

### Task 6: Migrate the optional deterministic collector and deprecate the narrow skill

**Files:**
- Move: `skills/research-artist-discography/scripts/*` → `skills/music/research-music/scripts/`
- Move: deterministic files in `tests/research_artist_discography/` → `tests/research_music_discography/`
- Delete: `tests/research_artist_discography/test_skill_contract.py`
- Move: `skills/research-artist-discography/` → `skills/deprecated/research-artist-discography/`
- Modify: `skills/music/research-music/providers/musicbrainz.md`
- Modify: `skills/music/research-music/providers/apple-music.md`
- Modify: `skills/music/research-music/recipes/artist-and-album.md`
- Modify: migrated test paths and CLI path references
- Test: `tests/research_music/test_skill_discovery.py`

**Interfaces:**
- Consumes: forward-tested `research-music` and the existing standard-library collector.
- Produces: one active installed skill; the legacy collector remains optional under its new owning skill; deprecated material is excluded from discovery.

- [ ] **Step 1: Extend discovery and optional-tool tests before moving files**

Add assertions that:

```python
self.assertFalse(any("research-artist-discography" in line for line in active_skill_lines))
self.assertTrue((ROOT / "skills" / "music" / "research-music" / "scripts" / "collect_discography_data.py").is_file())
```

Update the migrated CLI tests to expect the new script path. Run the focused tests before moving and confirm they fail for the expected old paths.

- [ ] **Step 2: Move the deterministic code and tests mechanically**

Run:

```bash
git mv skills/research-artist-discography skills/deprecated/research-artist-discography
git mv skills/deprecated/research-artist-discography/scripts/collect_discography_data.py skills/music/research-music/scripts/collect_discography_data.py
git mv skills/deprecated/research-artist-discography/scripts/research_artist_discography skills/music/research-music/scripts/research_artist_discography
git mv tests/research_artist_discography tests/research_music_discography
git rm tests/research_music_discography/test_skill_contract.py
```

Use `apply_patch` to update deterministic test script paths and preserve the Python package name `research_artist_discography`; renaming the package provides no user value. Delete the old fixed-report contract test because the deprecated skill is no longer an active product interface.

- [ ] **Step 3: Replace the deprecated skill body with a migration notice**

Keep valid frontmatter but remove the old fixed-report process. State that the skill is deprecated, `research-music` replaces it, and the optional collector now lives at `skills/music/research-music/scripts/collect_discography_data.py`. Because discovery excludes `deprecated/`, this file is historical documentation, not an active skill.

- [ ] **Step 4: Point only relevant documents to the optional collector**

In the MusicBrainz and Apple Music cards, mention the collector only for deterministic catalog normalization. In `artist-and-album.md`, say to use it when a complete release inventory is actually required. Do not mention it in unrelated campaign, comparison, or market branches.

- [ ] **Step 5: Run deterministic regression tests**

Run:

```bash
python3 -m unittest discover -s tests/research_music -p 'test_*.py' -v
python3 -m unittest discover -s tests/research_music_discography -p 'test_*.py' -v
python3 skills/music/research-music/scripts/collect_discography_data.py --help
uv run --with pyyaml python /Users/mintplo/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/music/research-music
git diff --check
```

Expected: both suites pass, CLI help exits 0, validator is valid, and whitespace checks are clean.

- [ ] **Step 6: Update the local installation safely**

Verify the old path is a symlink before unlinking it:

```bash
test -L /Users/mintplo/.codex/skills/research-artist-discography
unlink /Users/mintplo/.codex/skills/research-artist-discography
CODEX_HOME=/Users/mintplo/.codex scripts/link-skills.sh
test -L /Users/mintplo/.codex/skills/research-music
```

Expected: the old active link is gone and `research-music` resolves to `skills/music/research-music`.

- [ ] **Step 7: Commit**

```bash
git add skills tests scripts
git commit -m "refactor: migrate discography tools into music research skill"
```

---

### Task 7: Final whole-library review and verification

**Files:**
- Inspect: all changes from `f2aa44e` through `HEAD`
- Update only for validated findings: files named by the reviewer
- Update ignored progress ledger: `.superpowers/sdd/progress.md`

**Interfaces:**
- Consumes: all six implementation tasks.
- Produces: reviewed, installed, documented-first music research skill with no unfixed Critical/Important findings.

- [ ] **Step 1: Generate one review package from the fixed base**

Run:

```bash
/Users/mintplo/.codex/plugins/cache/openai-curated-remote/superpowers/6.1.1/skills/subagent-driven-development/scripts/review-package f2aa44e HEAD
```

Expected: a `.superpowers/sdd/review-f2aa44e..<head>.diff` package.

- [ ] **Step 2: Request broad code-and-skill review**

Dispatch a fresh senior reviewer with the approved spec, this plan, review package, forward-test verdicts, and these review axes:

- the product is a flexible music research skill, not a fixed album renderer;
- Provider Catalog is documentation, not runtime registry code;
- context pointers load only relevant cards and recipes;
- provider facts have current primary documentation and clear last-verified dates;
- no active dependency points into `deprecated/`;
- deterministic collector still passes its original behavioral tests;
- discovery/link scripts do not overwrite user-owned files;
- new skill is valid and installed, old link removed only after forward success.

Fix every Critical/Important finding with focused TDD and re-review the full range.

- [ ] **Step 3: Run fresh final verification**

Run:

```bash
python3 -m unittest discover -s tests/research_music -p 'test_*.py' -v
python3 -m unittest discover -s tests/research_music_discography -p 'test_*.py' -v
uv run --with pyyaml python /Users/mintplo/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/music/research-music
scripts/list-skills.sh
CODEX_HOME=/Users/mintplo/.codex scripts/link-skills.sh
test -L /Users/mintplo/.codex/skills/research-music
git diff --check
git status --short
```

Expected: both test suites pass, skill validator prints `Skill is valid!`, active listing includes `skills/music/research-music/SKILL.md` and no deprecated skill, the installation link exists, diff checks are clean, and the working tree is clean.

- [ ] **Step 4: Record completion**

Append task SHAs, per-task review verdicts, forward-case verdicts, final test counts, validator output, and final reviewer verdict to `.superpowers/sdd/progress.md`. Do not commit `.superpowers/`.
