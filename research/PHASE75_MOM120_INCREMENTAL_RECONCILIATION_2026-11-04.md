# Phase 75 — MOM120 incremental evidence reconciliation
Date: 2026-11-04

## Executive decision

**KILL MOM120 as an incremental signal versus the frozen LTM comparator on the current 335-name snapshot.** The corrected Phase 30 artifact shows essentially zero mean daily excess return, a block-bootstrap interval spanning zero by a wide margin, and only 56.9% positive leave-one-out means. This is not a robust incremental edge.

This is a research decision only. It does not alter `F80_TOP20_PARTIAL50_BASELINE_C20`.

## Source and reproducibility

- Latest Phase 30 run: 40126095357, SUCCESS, commit 09bbc836c27cd3558d9a5f2037a861b3765e69f8.
- Artifact: 12573378046, `phase30-mom120-economic-validation`, SHA-256 `d9d56696e0d7051a527b2f84c31cebaa18bb9674b5fba4d880de8833f4726d28`.
- Earlier run 40105776797 / artifact 12564613355 had a return-accounting defect: DailyReturn was calculated as close equity divided by today's pre-equity at the open, omitting the prior-close-to-open component. That artifact is superseded and must not be used for performance inference.
- The latest source code at commit 09bbc836 uses sequential close-to-close equity returns; the artifact passes the return identity audit.

## Primary OOS comparison (2024-01-02 through 2026-10-23; 706 sessions; 20 bps cost setting)

| Metric | MOM120 | LTM |
|---|---:|---:|
| Final multiple | 3.5765x | 3.5962x |
| CAGR | 57.60% | 57.91% |
| Max drawdown | -38.45% | -39.01% |
| Sharpe | 1.2274 | 1.2424 |
| Mean daily return | 0.21536% | 0.21529% |
| Annualized volatility | 44.21% | 43.67% |
| Average positions | 193.28 | 198.03 |
| Maximum positions | 201 | 209 |

The very high absolute return is conditional on the fixed current 335-name universe and is not evidence of survivorship-bias-free generalizable performance. Both comparators share the same data, dates, exposure mechanics and cost assumption.

## Incremental result: MOM120 minus LTM

- Paired OOS observations: 706.
- Mean daily excess: +0.0000006326 (approximately +0.0063 basis points/day).
- 95% circular block-bootstrap interval (20-session blocks): [-0.00023151, +0.00022853].
- Positive leave-one-out mean fraction: 56.94%.
- LOO mean range: [-0.00002288, +0.00001705].

The estimated mean is economically negligible and statistically indistinguishable from zero under the preregistered block bootstrap. LOO stability is weak. MOM120 has slightly lower maximum drawdown in this sample, but lower CAGR and Sharpe; this isolated tradeoff does not establish an incremental signal.

## Accounting invariant recheck

Recomputed directly from both ledger CSVs in the artifact:

- Maximum absolute difference between stored DailyReturn and `Equity.pct_change()`: 5.3e-16 for MOM120 and 5.0e-16 for LTM.
- Minimum cash: 0.
- Maximum marked gross exposure: 1.0000000000000002 (floating-point tolerance).
- Equity multiple recomputed from first/last OOS equity matches report exactly.
- Average position count is high because PARTIAL50 explicitly moves halfway toward the target on each 80-session rebalance; residual holdings decay rather than being liquidated immediately. This is consistent with the encoded state transition, not by itself an accounting failure. However, it means this is not a literal 20-stock portfolio and must be described as a 20-name target with a diffuse residual book.

## Research disposition

1. Close the MOM120 standalone/incremental hypothesis against LTM for this protocol. Do not tune thresholds or holding periods to rescue it.
2. Retain the corrected artifact and this negative result in the audit trail.
3. If a new momentum variant is proposed, it must be a genuinely distinct, preregistered hypothesis, tested on the same dates, costs, exposure and historical universe with a fresh OOS holdout. No reuse of the current OOS window for parameter selection.
4. Broad claims remain blocked by the unresolved original F80 universe-selection rule and lack of PIT membership/delisted-name reconstruction.

## Frozen baseline

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No production promotion, no parameter changes, and no strategy deployment.
