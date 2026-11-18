# Phase 487 — FINRA Phase 20A/B/C artifact adjudication

**Audit cutoff:** 2026-11-18 19:02 UTC  
**Base main HEAD:** \`182f02d933b342ff9ce2f44e6844f53f0d99da4f\`  
**Disposition:** reject the Phase 20B continuous replacement rule and Phase 20C adaptive rule for promotion; retain Phase 20A residual IC only as exploratory. No FINRA signal is admitted.

## 1. Preflight

- Actions history: 7,855 runs; latest 100 contained 74 success, 24 failure, 2 cancelled; zero active/in-progress and zero queued.
- Schedule-triggered history: 22 runs. Branch inventory: 315; open PRs: 56; workflow files: 82.
- Latest runs were Phase 485 push/PR checks [44356862612](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44356862612) and [44356946691](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44356946691), both successful 8-test offline checks with no artifacts or SEC requests.
- Main is still at \`182f02d933b342ff9ce2f44e6844f53f0d99da4f\`. No workflow was active or queued and none was dispatched, rerun, cancelled or duplicated.
- Phase 20C branch is diverged from main (12 ahead / 348 behind); Phase 24B is diverged (10 ahead / 345 behind). Neither branch is safe to merge wholesale.

## 2. Phase 20B — apparent OOS replacement gain is not attributable to a continuous signal

Source: [Run 39324762076](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39324762076), artifact 12222238141. The downloaded ZIP SHA-256 matches GitHub's artifact digest: \`e3f72540ce68c5c137e2e3de7393a4d83f7f346de0dba51215aceba3366a151c\`.

The training rule selected \`SHORT_EXEMPT_RATIO\` with inverse direction and training mean Spearman \`-0.0173295\`, from 20 FINRA-eligible training dates. It then replaced four of the 20 F80 names on each of six OOS dates.

Date-level equal-weight replacement-minus-blocked results:

| Horizon | OOS dates | Mean difference | 95% t CI | t p-value | Positive dates |
|---|---:|---:|---:|---:|---:|
| 5 sessions | 6 | +2.665% | -2.539% to +7.869% | 0.245 | 4/6 |
| 10 sessions | 6 | +1.307% | -7.311% to +9.925% | 0.713 | 4/6 |
| 20 sessions | 5 matured | +2.088% | -4.918% to +9.094% | 0.455 | 3/5 |

All confidence intervals include zero; none of the three horizons survives a three-horizon Bonferroni correction.

**Decisive implementation defect:** all 24 selected replacement names have \`RuleScore = 0\`. The replacement score has exactly one unique value, zero standard deviation and no within-replacement ranking power. The four replacements per date are therefore chosen from a complete score tie, with row-order/tie handling deciding which names enter. The apparent return difference cannot be attributed to the claimed continuous inverse ranking.

**Decision:** reject this Phase 20B rule for promotion. Do not describe the +2.665% / +1.307% / +2.088% raw differences as alpha. A separate binary zero-versus-positive hypothesis would be a new, untested hypothesis and must not inherit these results.

## 3. Phase 20C — adaptive selection is weak and unstable

Latest run: [40098425254](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254), artifact 12562171831. ZIP SHA-256: \`c15f75340bdedfbb37c82f79bb563a450dd1da11989d09e18bb745d93b7d3a5c\`.

The run had 24 total training-era F80 signal dates, 20 FINRA-eligible dates, 12 pseudo-OOS walk-forward dates and six final OOS holdout dates left untouched. The price universe contained 329/335 names. The collector requested 2,020 calendar dates and received 1,382 files; this raw calendar-day count includes weekends/holidays and is not a trading-day coverage percentage.

| Horizon | Pseudo-OOS dates | Mean replacement-minus-blocked | 95% t CI | t p-value | Positive dates |
|---|---:|---:|---:|---:|---:|
| 5 sessions | 12 | +0.141% | -3.209% to +3.491% | 0.928 | 5/12 |
| 10 sessions | 12 | -1.686% | -6.453% to +3.080% | 0.453 | 3/12 |
| 20 sessions | 12 | -0.858% | -11.362% to +9.647% | 0.861 | 5/12 |

The earlier Phase 20C run [39335227938](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39335227938) reported -0.497%, -1.303% and +1.654% at 5/10/20 sessions respectively. The 20-session mean changed sign between runs. Both runs are statistically inconclusive.

The adaptive selector chooses a factor using marginal factor/forward-return Spearman values across prior dates and horizons. Although LTM is present in the cross-sectional panel, the selector does not residualize or otherwise condition the factor on LTM. This is not an incremental-information test against F80.

**Decision:** reject the current adaptive replacement rule for promotion. Keep the final six-signal holdout untouched.

## 4. Phase 20A — exploratory residual IC, not an admitted signal

Source: [Run 39300615844](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39300615844), artifact 12211077155. ZIP SHA-256: \`a090438e77c2567790e68839b88c19134a644bd6343482460b15d7959dd74cd7\`.

The panel used 328/335 symbols, 1,902 rows and six OOS signal dates. Its \`FutureRowsUsed=0\` diagnostic does not certify historical first-publication time or executable entry.

Selected residual-IC diagnostics after linear cross-sectional residualization against LTM:

| Factor / horizon | Mean residual IC | 95% t CI | Nominal p | Positive dates |
|---|---:|---:|---:|---:|
| SHORT_EXEMPT_RATIO / 10 | -0.0755 | -0.1251 to -0.0259 | 0.0112 | 0/6 |
| SHORT_RATIO_Z60 / 5 | +0.0553 | -0.0231 to +0.1337 | 0.1295 | 5/6 |
| SHORT_RATIO_PERSIST20 / 5 | +0.0454 | -0.0154 to +0.1061 | 0.1130 | 5/6 |

There are 21 factor/horizon combinations. The nominal \`SHORT_EXEMPT_RATIO / 10\` p-value adjusts to 0.2359 under Bonferroni across the family. No combination survives the family-wise correction. These are cross-sectional ICs, not portfolio returns.

**Decision:** exploratory only; no feature or direction is admitted.

## 5. Common PIT and economic gates remain failed

The Phase 20A/B/C runs backfilled historical FINRA daily files by trade date. They did not possess a historical first-local-receipt ledger for those files. Phase 469's prospective capture has not yet produced a confirmed scheduled first receipt in the current Actions inventory.

A same-date file that is first received after the regular-session close cannot be traded at that same close. Under Phase 470, delayed first-seen observations require a prior scheduled non-availability poll; entry must be at the first supported XNYS open strictly after actual receipt. The historical Phase 20A/B/C close-to-close labels do not satisfy this clock.

Additional failures:
- 328/335 or 329/335 price coverage, not the frozen 335-name universe.
- The seven inactive/corporate-action names remain unresolved for terminal total returns.
- No executable-cost deduction, turnover/slippage model or portfolio risk comparison.
- Equal replacement count in Phase 20B is not identical risk/exposure or matched weights.
- No block bootstrap or leave-one-date-out validation on these artifacts.
- The Phase 20C pseudo-OOS dates are in the training era, not the final six-date holdout.

## 6. Other source lineages — do not duplicate existing work

- OCC Phase 24B's 11-date endpoint probe found 11/11 substantive small daily-volume-statistics responses, but only 2/11 substantive volume-by-account-type responses; contract-volume, DLP and trade-volume endpoints returned no substantive payload in all 11 samples (maximum 30 bytes). This does not establish contract-level historical options flow or OI coverage.
- OptionMetrics Signed Volume/TradeFlow and ThetaData Pro remain conditional candidates under Phases 391/429; neither is PIT/coverage/license admitted. Cboe Open-Close remains conditional on sample-specific rights and vintage/receipt evidence. Phase 472 treats Complex Order Flow as a possible control/confounder, not a directional smart-money signal.
- SEC 13D/G remains quarantined under Phases 484/485; reuse the existing Phase 84/87 and PR #37 parent-retrieval chain after the \`SEC_USER_AGENT\` prerequisite, not another crawler.
- CFTC TFF remains in prospective accumulation only; one captured report date is not a 52-week warm-up.
- FINRA ATS/MPID concentration remains venue/firm structure, not beneficial-owner flow.

## 7. Current schedule delivery at cutoff

At 19:02 UTC on November 18:
- Phase 476's 18:17 UTC Form 4/4-A slot and Phase 403's 18:47 UTC Form 144 slot were absent from the run inventory.
- The next existing slots are Phase 476 at 19:17, Phase 403 at 19:47, CFTC at 22:25 and FINRA Reg SHO at 22:30/23:30 UTC.
- Missing schedule events are a delivery gap, not proof that a workflow is disabled. No manual dispatch or replacement workflow was created.

## 8. Final disposition

1. **Kill for promotion:** Phase 20B's current \`SHORT_EXEMPT_RATIO\` continuous replacement ranking (zero-variance replacement ties).
2. **Kill for promotion:** Phase 20C's current adaptive factor-selection/replacement rule (small, unstable pseudo-OOS; no LTM-incremental selector).
3. **Retain as exploratory only:** Phase 20A residual IC diagnostics; no family-wise significance and no PIT clock.
4. No new FINRA signal, alpha, strategy overlay or production change.
5. Any future FINRA test must be preregistered, first-receipt/next-open PIT-safe, full-universe and terminal-return complete, incremental to frozen LTM/F80, exposure/cost matched, and include chronological OOS, bootstrap and leave-one-date/event-block-out. The 5/10/20-session horizons above are diagnostics only; no minimum or maximum holding period is imposed.

No new market data was requested. No backtest or final OOS holdout was run in Phase 487.

**F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.**
