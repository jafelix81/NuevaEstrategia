# Phase 43 — CFTC COT feasibility audit V1 — 2026-11-01

## Status
**KEEP AS MARKET-REGIME / CROSS-ASSET CANDIDATE; NOT A STOCK-LEVEL SMART-MONEY SIGNAL. No alpha authorized.**

## Fresh official-source verification
CFTC states that COT reports break down each Tuesday's open interest and are released Fridays at 3:30 p.m. ET. The current reporting environment exposes Futures-Only, Futures-and-Options Combined, Disaggregated, Traders in Financial Futures (TFF), and Supplemental reports, with programmatic API access. Historical COT data are publicly available, with Futures-Only history back to 1986, Futures-and-Options Combined to 1995, and Supplemental to 2006. The historical compressed archive provides annual files from 2009 onward for Disaggregated and TFF series and annual legacy files back to 1986/1995 as applicable.

## PIT implications
The report's observation date is Tuesday, while publication is Friday. A simulated strategy may only use a COT observation after its actual Friday publication time (3:30 p.m. ET), unless a historical delivery timestamp demonstrates earlier availability. The observation date must never be mistaken for the information-availability date.

CFTC's 2025 funding lapse created an explicit historical example of publication-date disruption: reports covering 2025-09-30 through 2026-01-20 were published later under a catch-up schedule. Any historical OOS reconstruction therefore needs an actual publication calendar, not a simple `report_date + 3 days` assumption.

## Economic scope
COT is not a direct stock-level source for the frozen 335-equity universe. Its natural role is as a cross-asset/regime variable: equity-index futures, rates, FX, energy and metals positioning can potentially condition the effectiveness of equity signals. This is economically different from claiming that CFTC traders are 'smart money' in individual stocks.

## Testable hypotheses
H1: extreme changes in TFF/Disaggregated positioning in equity-index futures condition the expected return distribution of the frozen F80/LTM equity strategy.
H2: positioning changes in rates/FX/volatility-sensitive futures provide incremental regime information beyond the existing LTM/F80 state variables.
H3: COT positioning improves tail-risk management or signal selectivity rather than raw directional stock selection.
H4: any apparent improvement must survive chronological OOS validation, transaction costs, bootstrap/LOO, and controls for market momentum/volatility; it must not simply be a repackaged market-trend signal.

## Required gates before testing
1. Build a reproducible publication-date calendar, including exceptional delays.
2. Select only contract markets with economically defensible linkage to the equity strategy.
3. Measure historical coverage and symbol/contract continuity for the chosen markets.
4. Freeze feature definitions before touching returns.
5. Lag every feature to the first documented public availability timestamp.
6. Test incremental information versus frozen LTM/F80 with identical exposure and costs.
7. Reject the source if it only duplicates existing market regime variables or improves in-sample performance without stable OOS evidence.

## Decision
CFTC COT is feasible as a **secondary cross-asset conditioning source** with unusually long public history and clear publication rules. It is not suitable as a primary stock-level Smart Money source. No alpha test is authorized until the publication-calendar and coverage gates are implemented.

No change to `F80_TOP20_PARTIAL50_BASELINE_C20`.

## Execution state checked 2026-11-01
Phase 35 / 13D-13G run `41281874239` (#59) remains `in_progress`; job `124775311101` is still executing the corrected historical-CIK PIT audit. No duplicate Phase 35 execution was launched. Phase 22C / 13F run `41281874256` (#71) completed successfully but remains non-production because its historical-universe coverage gate is insufficient.
