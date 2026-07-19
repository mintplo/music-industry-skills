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
