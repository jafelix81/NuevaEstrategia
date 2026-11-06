# Phase 148 — Phase 29 independent-alpha cost and OOS audit

**Date:** 2026-11-06  
**Branch:** \`phase99-broad-pit-universe-charter\`  
**Status:** completed, artifact-only audit; no alpha promotion and no production change.

## Decision

**Do not promote the Phase 29 MOM120 candidate.** Its 20-session validation spread becomes negative after even a modest 5 bps-per-side cost assumption. Its 60-session validation mean remains positive, but the block-bootstrap confidence intervals include zero across all tested costs and block lengths. The previously reported 2024+ slice has already been inspected and is not an untouched holdout.

MOM120 is a price-momentum control, not a Smart Money feature. This audit is useful because future options/ownership signals must demonstrate incremental value beyond ordinary momentum and the frozen LTM/F80 control. No such comparison was present in Phase 29.

## Source and reproducibility

- GitHub Actions run: [40105752275](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40105752275).
- Source branch/head: \`phase29-independent-alpha-lab\` / \`a4fb2a8b4d6d5443605aaf9c04f99184712ce5ce\`.
- Artifact: \`12565060248\`, \`phase29-independent-alpha-lab\`, SHA-256 \`85480d28d6d24c8a167c67baee5b3c28c2915e0a3bc3b2eb2f13b490d4167d77\`.
- Original \`phase29_report.json\` SHA-256: \`a935ca2994a1041ad458a76fa203576cdd330e33fc253143879c9491bcc4db65\`.
- The repository retains a compact, derived input containing only the signal-date Q10–Q1 spreads, dates and cross-sectional counts. No ticker-level returns or raw Yahoo data are copied into the research branch.
- The compact input is hash-pinned and reconciles to the aggregate means in the original report.

## What was re-audited

Phase 29 selected MOM120 (long direction) for both horizons from its 2017–2020 discovery period. It then reported 2021–2023 validation and 2024+ final results:

| Horizon | Discovery dates | Validation dates | Previously reported final dates |
|---:|---:|---:|---:|
| 20 sessions | 54 | 36 | 33 |
| 60 sessions | 54 | 36 | 31 |

The Phase 29 script declares \`COST_BPS = 10.0\` as a per-side assumption, but that value is only written to the protocol metadata; it is not deducted from the Q10–Q1 return spread.

For a long-top-decile / short-bottom-decile spread, a one-way cost on each side of each leg means four one-way legs: long entry, long exit, short entry and short exit. The sensitivity therefore deducts \`4 × cost_bps_per_side\` from each Q10–Q1 spread. This is a transparent cost sensitivity, not an empirically estimated execution-cost or borrow model.

## Validation results

All returns below are percentages of the signal-date Q10–Q1 spread.

| Horizon | Gross mean | Net at 5 bps/side | Net at 10 bps/side | Net at 25 bps/side | Net at 50 bps/side |
|---:|---:|---:|---:|---:|---:|
| 20 sessions | +0.122% | **−0.078%** | **−0.278%** | **−0.878%** | **−1.878%** |
| 60 sessions | +4.089% | +3.889% | +3.689% | +3.089% | +2.089% |

At 10 bps per side:

| Horizon | Net block-bootstrap 95% CI, block 3 | Net block-bootstrap 95% CI, block 6 | Net leave-one-date-out range | Negative LOO means |
|---:|---:|---:|---:|---:|
| 20 sessions | −3.485% to +2.575% | −2.408% to +1.552% | −0.802% to +1.057% | 31 / 36 |
| 60 sessions | −1.586% to +8.884% | −1.328% to +7.948% | +2.989% to +4.757% | 0 / 36 |

The 20-session validation mean is particularly fragile: its median gross spread is +2.097%, but its mean is only +0.122%; the worst signal date is 2023-01-05 at −46.603%. We do not trim or winsorize that observation. The artifact lacks per-ticker holdings/returns, so the cause cannot be attributed to individual names.

The 60-session validation result is more coherent under leave-one-date-out, but the bootstrap lower bound remains negative for block lengths 1, 3, 6 and 9, including after the cost shifts. A positive sample mean is not enough to establish a robust edge.

## Previously reported 2024+ slice — exposed, not a holdout

| Horizon | Gross mean | Net mean at 10 bps/side | Net block-3 95% CI | Net block-6 95% CI |
|---:|---:|---:|---:|---:|
| 20 sessions | +3.188% | +2.788% | −0.156% to +5.708% | +0.097% to +5.308% |
| 60 sessions | +3.742% | +3.342% | −4.767% to +11.579% | −4.250% to +10.138% |

The 20-session lower bound changes sign with block length and cost, while the 60-session interval is very wide. More importantly, this slice was already included in the prior Phase 29 report and is now explicitly classified as **exposed exploratory evidence**, not a virgin final OOS. It cannot be reused to select a model or threshold.

## Strict decision gate

The audit requires a positive net validation mean, positive lower 95% bootstrap bounds at block lengths 3 and 6, and positive leave-one-date-out means. Neither horizon passes at any tested cost from 0 to 50 bps per side:

- **20 sessions:** fails the net-mean test at 5 bps per side and above; it also fails the confidence-interval and LOO robustness tests even at zero cost.
- **60 sessions:** has positive net mean and positive LOO means at all tested costs, but fails both bootstrap lower-bound tests at every tested cost.

The 10 bps assumption excludes stock borrow, financing, market impact, turnover variation, taxes and short-sale constraints. Actual implementation costs may be higher.

## Limitations that prevent promotion

1. The lab uses the fixed 335-symbol Phase-4 universe. The user has since clarified that 335 was an arbitrary historical selection, not a justified research-universe boundary.
2. Yahoo Finance adjusted history does not establish point-in-time universe membership, delisted coverage, permanent security identity or historical data vintages.
3. Phase 29 did not compare MOM120 or its candidate portfolios incrementally against frozen LTM/F80.
4. No multiple-testing correction across the ten candidate factor families was reported.
5. The artifact contains date-level spreads, not constituent holdings, so turnover, borrow and name-level attribution cannot be reconstructed here.
6. The 2024+ slice is exposed and cannot serve as a fresh holdout.

## Next action

Keep MOM120 as a descriptive price-momentum control only. Do not add it to F80 and do not use Phase 29's 335 names as the future universe. Any new independent-alpha or Smart Money candidate must use a survivorship-aware historical universe, verified PIT data, measured/defensible costs and a new untouched chronological OOS period. Smart Money candidates must show incremental value beyond both the frozen LTM/F80 control and ordinary price momentum.

**No Smart Money alpha was established.** \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen. No production code or portfolio parameter was changed.
