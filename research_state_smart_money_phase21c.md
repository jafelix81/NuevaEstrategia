# Smart Money Research — Phase 21C SEC Form 4

## Status
KILLED_FOR_NOW — no robust predictive or incremental edge demonstrated.

## Run
- GitHub Actions run: 39362237089
- Commit: c4ea7a203b579098acd54e09536cc38fa6d3c042
- Policy: F80_TOP20_PARTIAL50_BASELINE_C20
- Final OOS dates: 2025-02-25, 2025-06-20, 2025-10-14, 2026-02-09, 2026-06-04, 2026-09-29
- Knowledge rule: KnowledgeDate < SignalDate; same-day filings excluded.

## Training-only feature selection
Selected per horizon from 24 chronological training signal dates:
- H5: BUY_DAYS20, direction -1, mean train Spearman -0.00926
- H10: BUY_EVENTS60, direction +1, mean train Spearman +0.01433
- H20: BUY_ADTV20, direction +1, mean train Spearman +0.01110

## Final OOS result
- H5: mean advantage -0.023 pp; median -0.196 pp; positive dates 2/6; mean Spearman -0.0226; residual Spearman -0.0642.
- H10: mean advantage +0.379 pp; median -0.186 pp; positive dates 3/6; mean Spearman +0.0110; residual Spearman -0.0244.
- H20: mean advantage -0.363 pp; median +1.244 pp; positive dates 3/5 mature; mean Spearman +0.0409; residual Spearman -0.0275.

Bootstrap mean-advantage intervals:
- H5: -0.659% to +0.667%
- H10: -0.900% to +1.776%
- H20: -5.370% to +3.249%

## Interpretation
Form 4 insider-buying activity, as tested here, does not show a stable standalone or incremental predictive edge across the six final OOS dates. Raw H20 rank correlation is positive but disappears after residualization versus LTM, and portfolio advantage is negative on average. H10 has a small positive mean advantage but negative median and wide interval. H5 is negative both in raw and residualized correlation.

This hypothesis is therefore NOT promoted to F80 and should not receive further model complexity at this stage. It may be revisited only with a materially different, pre-specified hypothesis (for example insider clustering/role/transaction-type conditioning) and a fresh chronological validation design; no tuning of the failed feature set is warranted.

## Integrity
- Final OOS dates were never used for feature selection.
- No production change.
- F80 remains frozen.
- No minimum or maximum holding period imposed.
