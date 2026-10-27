# Phase 43 — SEC fails-to-deliver feasibility gate

Date: 2026-10-27

## Objective
Evaluate SEC fails-to-deliver (FTD) data as a short-pressure / settlement-friction hypothesis source. FTD is **not** assumed to represent short selling or informed activity.

## Source and coverage — independently re-verified 2026-10-27
The SEC Fails-to-Deliver Data page documents coverage from February 2004 through September 2026. Since July 2009, each month is split into two files: the first half becomes available at the end of that month and the second half becomes available around the 15th of the following month. The files contain settlement date, CUSIP, ticker, issuer, price and total fails-to-deliver shares outstanding in the NSCC CNS system aggregated across NSCC members.

The SEC explicitly warns that FTD quantity is a cumulative balance as of a settlement date, not a daily flow, and that FTDs can arise from both long and short sales. Therefore the research hypothesis is settlement/short-pressure information, not "naked shorting".

Additional source caveat: before 2009-07 the archive is organized by calendar-quarter ZIP files and the SEC says accuracy cannot be guaranteed. Before 2008-09-16, records only include securities with at least 10,000 shares of aggregate fails. From 2008-09-16 onward, all non-zero balances are represented. These structural breaks must be preserved in any historical analysis rather than silently pooled.

## Why this is worth testing
FTD is distinct from the already-tested FINRA short-interest and short-sale-flow series:
- short interest measures outstanding reported short positions;
- short-sale flow measures reported short volume;
- FTD measures unsettled delivery balances.

The three can diverge economically. A useful hypothesis is therefore whether **changes or unusually persistent FTD balances contain incremental information conditional on short interest/short flow and frozen LTM/F80**, rather than whether raw FTD levels predict returns.

## Pre-registered candidate features
1. FTD shares / shares outstanding (where a defensible denominator is available).
2. FTD dollar value / market capitalization.
3. Change in FTD balance between successive settlement observations.
4. Persistence: consecutive observations above a security's own historical percentile.
5. FTD acceleration / change in log balance, with zero handling pre-specified.
6. Divergence: FTD change versus short-interest change and FINRA short-flow measures.
7. Reversal/control test: determine whether any apparent effect is merely a consequence of recent extreme returns or volume.

No thresholds or transformations are to be optimized on the final OOS sample.

## PIT rules
- Signal date must be strictly after the documented SEC publication availability date for the relevant half-month file.
- Settlement date is the economic observation date; publication date is the knowledge date.
- Never use the current web page's existence as evidence that a historical file was already available on the signal date.
- Where exact historical posting timestamps cannot be reconstructed, use the conservative documented availability convention and record the assumption.

## Feasibility gates before alpha testing
1. Download representative early- and late-history files.
2. Parse actual rows and verify schema/types.
3. Measure overlap with the frozen 335-stock universe across multiple periods.
4. Audit ticker/CUSIP continuity and corporate-action/name-change issues.
5. Confirm publication lag and construct a conservative knowledge-date field.
6. Check whether observations are sufficiently frequent for the intended holding horizons.
7. Preserve the pre-2009 and pre-2008-09-16 structural breaks explicitly; do not use them as a hidden source of survivorship/coverage bias.
8. Only then run chronological OOS incremental tests versus frozen F80/LTM.

## Statistical/economic gate
If feasible:
- frozen F80_TOP20_PARTIAL50_BASELINE_C20 remains untouched;
- identical universe, dates, execution and costs for control/candidate;
- primary test is incremental residual forward return conditional on LTM/F80;
- secondary tests: Spearman IC, bucket spread, hit rate, block bootstrap CI and LOO stability;
- test both standalone FTD and divergence with already-tested short-interest/short-flow measures;
- kill if there is no robust incremental OOS information or if the signal is simply return/volume chasing.

## Current decision
`FEASIBLE_PUBLIC_CANDIDATE_PENDING_ACTUAL_FILE_AUDIT`

The SEC source has now been independently re-verified as a viable historical candidate with explicit documented publication conventions. It is not an alpha signal and no production change is warranted. The next research gate is an actual-file parser/coverage audit, not an economic backtest.

## Official source
SEC Fails-to-Deliver Data: February 2004–September 2026; first-half files available at month-end and second-half files around the 15th of the following month. The SEC's current data page was last reviewed/updated September 1, 2026.
