# Report Format

## Default discography brief

1. Scope, artist identity, collection date, and missing-source warning
2. Complete master inventory
3. Recent-N candidate ledger only for a latest-N or recent-N selection request
4. Release metadata, concept, positioning, and promotion matrix
5. Sales and chart evidence with measurement definitions
6. YouTube and other accessible public signals with observation times
7. Release-to-release changes and marketing implications
8. Conflicts, missing data, and confidence
9. Direct source links

## Master inventory and recent-N ledger

Build the master inventory before analysis and derive every later release view from it. Every master-inventory row must include first-release date, normalized type, role/status, and selection eligibility. Use one canonical row for each discovered release group, including excluded and uncertain releases; edition identifiers may remain in that row. A category summary cannot replace individually itemized excluded or uncertain rows, and those rows must not be labeled default-eligible.

For a latest-N or recent-N selection request, show a recent-N candidate ledger. After building the master inventory, apply explicit role, type, period, and album filters. Sort the remaining considered releases by normalized first-release date descending, with unknown dates last. Then mark every considered release `eligible`, `excluded`, or `uncertain` with its reason and select exactly the first N eligible rows. An official standalone `digital_single` remains eligible unless the documented default-type or role rules exclude it. Never substitute a lower candidate because data is unavailable. Retain the selected row and report `데이터 없음` or `비교 불가` for the unavailable metric.

## Drill-down

For a named release, keep the full inventory visible and add a detailed release card. Compare only same-market, same-period, same-unit, same-measurement observations.

## Numeric evidence fields

Assign a stable evidence ID to every complete numeric evidence row. Every numeric evidence row or table cell must expose source tier, source URL, market, period/window, `observed_at`, measurement type/unit, and confidence. Use compact columns or a per-row source block immediately adjacent to the value. A separate paragraph does not satisfy this requirement.

Before finalizing, run the audit below. Scan every performance number and quantified performance claim in prose and tables, including a number cited only to dismiss it. Treat quantified certifications and numeric labels—including multipliers, levels, and thresholds such as `3× Platinum`, ranks, percentages, and K/M abbreviations—as performance numbers. Require every such mention, including one in limitation or reference-only prose, to cite a complete evidence row by its evidence ID. If it lacks that mapping, remove the numeric part and keep the statement qualitative. Map each later performance claim by evidence ID to one complete evidence row. Cite that evidence ID whenever later prose or a table repeats a performance number; otherwise keep the later claim qualitative. Use the evidence ID instead of duplicating the complete provenance fields when the later claim maps to that row. If no complete mapping exists, remove the number or state the claim qualitatively without it. Release dates and catalog track counts may follow catalog citation rules; this exception never applies to performance claims.

## Visualization

Create a timeline for release history. For every metric family used in comparison, create its comparable chart when comparable numeric observations exist. Put rank on a reversed rank axis when supported. Do not place unlike units on one axis and do not create a synthetic overall score. When omitting a chart, state its concrete insufficiency or omission rationale adjacent to that metric family. A prose comparison is not a substitute for a required chart.

## Writing rules

Give every factual concept or promotion claim an adjacent direct citation in the same bullet or table cell. A bibliography or links later in the report do not satisfy this requirement. Apply this rule to factual premises in interpretation, change, and marketing-implications sections. The `interpretation` label exempts only the analytical inference, not embedded factual premises. Repeat the direct citation beside each factual premise, or state the inference without restating unlinked facts. Keep interpretations separately labeled. Label factual evidence and limitations separately. Use `데이터 없음` or `확인 불가` instead of filling gaps. Keep article/wiki numbers in a reference-only subsection.
