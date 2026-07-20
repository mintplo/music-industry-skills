# Metric Compatibility

## Comparison key

Define every observation with `{market, metric, unit, measurement_type, period_basis, window_length}`.

## Compatible observations

Compare observations only when their full comparison keys match, unless the answer explicitly presents a documented normalization rather than a direct comparison.

## Incompatible observations

Keep different keys separate. Never create cross-key sums or synthetic scores.

## Rank display

Label rank source, market, chart, and period. When charting rank, reverse the rank axis so a better rank appears higher.

## Missing values

Show missing, unavailable, or non-comparable values as such; do not substitute zero or estimate a value without an explicit, sourced method.
