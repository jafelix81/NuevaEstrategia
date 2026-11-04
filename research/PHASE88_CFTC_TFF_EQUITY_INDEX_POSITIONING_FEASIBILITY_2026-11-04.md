# Phase 88 — CFTC Traders in Financial Futures: equity-index positioning feasibility

**Date:** 2026-11-04  
**Status:** SOURCE/HISTORICAL-COVERAGE PASS; STRICT HISTORICAL PIT RELEASE-DATE GATE FAIL  
**Scope:** S&P 500 and Nasdaq-100 futures positioning as a possible broad-market regime input, not a stock-level 335-name signal.

## 1. Why this source is worth screening

The CFTC's Traders in Financial Futures (TFF) report covers financial contracts, including stock-index futures and VIX. It reports positions by four large-trader categories—Dealer/Intermediary, Asset Manager/Institutional, Leveraged Funds, and Other Reportables—plus nonreportable positions. Both futures-only and futures-and-options-combined datasets are public and machine-readable.

This is a materially different hypothesis from FINRA short volume, 13D/13G ownership filings, or options participant flow. It may describe broad institutional positioning and hedging in index futures. It cannot identify the beneficial owners of individual stocks or directly select names from the F80 universe.

## 2. Historical availability and contract coverage

Official CFTC materials establish:
- The TFF report was announced on July 22, 2010.
- CFTC says historical TFF data are available back to June 13, 2006. Pre-launch history is backcast using recent trader classifications, not a contemporaneously preserved classification history.
- The historical archive contains annual TFF futures-only and futures/options-combined files, with the annual series listed from July 2010 and a combined 2006–2016 archive.
- Official historical reports contain S&P 500 and Nasdaq-100 futures markets. Examples include S&P 500 reports in 2010 and Nasdaq-100 reports in 2011.
- The current CFTC Public Reporting Environment has separate TFF Futures Only and TFF Combined datasets. The current combined dataset page reports 47.3K rows and 90 columns, last updated October 30, 2026.

Representative historical contract identifiers visible in official reports include S&P 500 Stock Index (CFTC code 138741), Nasdaq-100 Stock Index (209741), and Nasdaq-100 Stock Index Mini (209742). These are candidates for a canonical series map, not permission to combine consolidated, standard and mini contracts. Before extraction, verify the full contract-code/name history and select one non-duplicated index series per benchmark.

The CFTC reports only markets meeting the reporting threshold (20 or more traders at/above reportable levels). A market disappearing from a weekly report can mean it fell below the threshold; absence must not be filled with zero positioning.

## 3. Classification semantics: do not equate category with informed trading

CFTC explanatory notes say the categories reflect the trader's predominant business function:
- Dealer/Intermediary: sell-side participants that accommodate clients and manage matched books/risk.
- Asset Manager/Institutional: institutional investors and portfolio managers.
- Leveraged Funds: typically hedge funds, CTAs, CPOs and other leveraged money managers.
- Other Reportables: remaining reportable traders.

These are trader classifications, not labels for the motive of each position. The same participant can use futures for investment, hedging, arbitrage, duration changes or risk management. CFTC explicitly warns that staff classifies traders, not each trade, and cannot know with certainty whether all activity of a leveraged fund is speculative. The report's “spreading” positions are computed offsets and must be preserved separately from outright long/short exposure.

The CFTC also states that it does not maintain a historical record of trader classifications; recent classifications are backcast into earlier data. Accuracy diminishes further back in time. The 2006–2010 segment should therefore be treated as a separate, lower-confidence regime or excluded from the primary test.

## 4. Point-in-time gate — currently failed

Normal process:
- Position snapshot: Tuesday close.
- Typical publication: Friday at 3:30 p.m. Eastern.
- Holiday weeks can shift the release date.

However, the CFTC FAQ explicitly says there is **no list of historical release dates**; only the most recent 13 months of published release dates are available. That prevents a fully verified historical knowledge timestamp from the current archive alone.

The 2025 federal funding lapse proves this is not a theoretical concern. CFTC's November 18, 2025 notice says the September 30, 2025 report, originally scheduled for October 3, was actually released November 19. Subsequent weekly reports were also published on a catch-up schedule through December 29. A blanket “Tuesday plus Friday” rule would have introduced lookahead during this period.

A uniform conservative lag could be explored only as a separately preregistered sensitivity. An eight-week lag would cover the known 2025 catch-up example, but it is not proof of the actual historical release date for every report week and may make the feature too stale. It does not currently satisfy the strict PIT gate.

## 5. Feasible hypothesis — broad-market regime, not stock alpha

**H1:** changes in leveraged-fund and asset-manager net positioning in S&P 500/Nasdaq-100 futures contain incremental information about subsequent broad-market risk/return regimes beyond the existing QQQ Risk ON/Risk OFF state.

Competing explanations:
- positioning follows recent index returns (return-chasing);
- dealer positions reflect client flow/inventory hedging rather than directional views;
- leveraged-fund net positions proxy trend-following, basis trades or volatility strategies;
- changes reflect open-interest/contract-roll effects or classification changes.

Candidate features, frozen before any return analysis:
- category net position / total open interest, with outright long, short and spreading retained separately;
- weekly change and 4-/13-week change in category net share;
- trailing z-score of category net share using only prior observations;
- category gross long/short and top-4/top-8 concentration where available;
- separate futures-only primary specification and futures/options-combined sensitivity;
- S&P 500 and Nasdaq-100 tested separately, never double-counting mini and consolidated contracts.

The first economic test, if authorized, is incremental to the frozen QQQ regime and F80/LTM under identical exposure, entry/exit, costs and holding-period flexibility. Use chronological walk-forward splits, a locked OOS block, block bootstrap, leave-one-period-out, and explicit controls for prior index returns, volatility, open interest and regime. Do not label any category “Smart Money” by default.

## 6. Required gates before any return test

1. Reconstruct an official report-week → actual publication-date calendar. The current CFTC FAQ says historical dates are not centrally listed; document every exception and unresolved week.
2. Verify first available report date, archive completeness, report-type schema changes, contract codes, market names and dropped/reappearing markets.
3. Reconcile positions including spreading and open interest; preserve missing/suppressed values and never fill missing markets with zero.
4. Separate pre-launch/backcast classifications from contemporaneous TFF classification periods.
5. Freeze the canonical S&P 500 and Nasdaq-100 series, futures-only primary dataset, and futures/options-combined sensitivity before looking at returns.
6. Compare only as a broad-market overlay against existing QQQ Risk ON/OFF and frozen LTM/F80; do not claim security-level alpha.

## 7. Decision

**KEEP AS A SECONDARY MACRO-REGIME CANDIDATE; NO ALPHA TEST AUTHORIZED YET.**

The data are public, long-history and directly relevant to U.S. equity-index futures. The strict PIT release-date gap is the current hard blocker. If a reproducible historical release calendar cannot be built, park the source rather than selecting a convenient lag after seeing performance.

No forward returns, feature tuning, vendor purchase, production changes or baseline changes were made. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Official sources

- CFTC, Commitments of Traders / FAQs: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- CFTC, TFF explanatory notes: https://www.cftc.gov/idc/groups/public/@commitmentsoftraders/documents/file/tfmexplanatorynotes.pdf
- CFTC, Historical Compressed archives: https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm
- CFTC, TFF Futures Only dataset: https://publicreporting.cftc.gov/Commitments-of-Traders/TFF-Futures-Only/gpe5-46if
- CFTC, TFF Combined dataset: https://publicreporting.cftc.gov/Commitments-of-Traders/TFF-Combined/yw9f-hn96
- CFTC, 2026 release schedule: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
- CFTC, November 18, 2025 catch-up announcement: https://www.cftc.gov/PressRoom/PressReleases/9138-25
- CFTC, December 9, 2025 catch-up schedule: https://www.cftc.gov/PressRoom/PressReleases/9147-25
- Historical S&P 500 TFF report (December 28, 2010): https://www.cftc.gov/sites/default/files/files/dea/cotarchives/2010/futures/financial_lf122810.htm
- Historical Nasdaq-100 TFF report (October 4, 2011): https://www.cftc.gov/sites/default/files/files/dea/cotarchives/2011/futures/financial_lf100411.htm
