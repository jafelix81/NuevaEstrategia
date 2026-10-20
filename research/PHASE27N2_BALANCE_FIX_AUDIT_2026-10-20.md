# Phase 27N2 — N-PORT balance-field correction audit

## Trigger
Phase 27N completed successfully but produced zero ranked names in every transition. This was a technical data-field defect, not a failed alpha result.

## Root cause
`FUND_REPORTED_HOLDING` does not contain a `SHARES` field. The SEC schema defines `BALANCE` as the holding quantity and `UNIT` as the unit type. For equity holdings, `UNIT` can identify number-of-shares units such as `NS`/`SH`.

The Phase 27N pilot therefore converted a nonexistent `SHARES` column to zero for every row, making all aggregate share quantities zero and forcing `n_ranked=0` in every period.

## Correction
Phase 27N2 uses:
- `BALANCE` as the quantity field;
- only rows with `UNIT in {NS, SH}` for the share-flow signal;
- the same PIT identifier resolution as 27M/27N;
- the same $50m prior aggregate market-value eligibility threshold;
- the same top/bottom decile cross-sectional signal;
- the same strictly-after-knowledge-cutoff, 63-trading-day OOS return rule.

No signal parameter was changed to manufacture an effect.

## Integrity
- Frozen universe remains 335 names.
- No current-ticker backfill is introduced.
- Exact ticker remains preferred; PIT CUSIP/ISIN candidates are used only when uniquely observed in the same PIT snapshot.
- Amendments/filings remain constrained by report date and a 75-day knowledge cutoff.
- F80 remains frozen.
- No production strategy change is authorized by this correction.

## Gate
If 27N2 produces nonzero coverage, analyze OOS returns and cross-sectional robustness. If coverage is still insufficient, diagnose the mapping/quantity construction before any alpha conclusion. If coverage is valid but OOS edge is absent, kill the N-PORT flow hypothesis rather than optimizing it.
