# Phase 39 — Form 4 incremental gate / diagnostic disposition

Date: 2026-10-30

## Purpose
Assess whether the completed Phase 21C Form 4 diagnostic is strong enough to justify a new walk-forward alpha run against frozen `F80_TOP20_PARTIAL50_BASELINE_C20`.

## Evidence reviewed
Latest completed Phase 21C run: GitHub Actions `39369692938`, commit `8b4b75fbdb0e2953a71bbf121d307de45bb0c1fe`.

The run used chronological training dates through 2024-10-28 and six untouched final OOS signal dates from 2025-02-25 through 2026-09-29. Final-OOS dates were never used for feature selection.

Training selected:
- `BUY_DAYS20`, horizon 5, mean train Spearman -0.00906, direction -1
- `BUY_EVENTS60`, horizon 10, mean train Spearman +0.01486
- `BUY_ADTV20`, horizon 20, mean train Spearman +0.01128

Final OOS diagnostics:
- 5-day: mean advantage -0.1198%, median -0.0220%, 3/6 positive dates; bootstrap interval [-0.853%, +0.614%]; mean Spearman -0.0224; residual Spearman -0.0633.
- 10-day: mean advantage +0.6462%, median +0.1096%, 3/6 positive dates; bootstrap interval [-0.731%, +2.303%]; mean Spearman +0.0114; residual Spearman -0.0254.
- 20-day: mean advantage -0.4603%, median +1.2318%, 3/5 positive dates; bootstrap interval [-5.007%, +2.838%]; mean Spearman +0.0407; residual Spearman -0.0299.

## Decision
**Do not advance the current Phase 21C Form 4 feature-selection specification to a new walk-forward alpha run.**

Reason: the untouched OOS evidence is too weak and unstable to justify additional model degrees of freedom. All three horizons have very small OOS samples, only half of the 5/10-day dates are positive, and every bootstrap interval spans zero. The residual correlations are non-positive, which gives no evidence that the observed 10-day bump is incremental information rather than noise/return-chasing.

This is a **kill of the current feature-selection specification**, not a claim that all insider information is useless. The broader Form 4 hypothesis remains archived as a low-priority candidate only if a materially different, pre-specified construction can be justified without mining the existing OOS dates.

## Re-entry conditions
A future Form 4 test may be reopened only with:
1. a pre-specified transaction-code construction centered on discretionary open-market purchases;
2. security/ticker coverage demonstrated on the full frozen universe or an independently justified PIT universe;
3. acceptance-time PIT enforcement where available, otherwise a fixed conservative filing-date rule;
4. a new untouched chronological OOS block, not the six dates already inspected;
5. identical exposure/cost assumptions to F80/LTM;
6. bootstrap/LOO and residualized tests specified before OOS evaluation.

## Baseline protection
`F80_TOP20_PARTIAL50_BASELINE_C20` is unchanged. No production signal, ranking, or exposure rule is modified.
