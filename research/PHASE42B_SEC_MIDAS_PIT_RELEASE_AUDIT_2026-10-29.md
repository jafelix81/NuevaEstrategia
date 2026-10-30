# Phase 42B — SEC MIDAS PIT release audit

Date: 2026-10-29

## Objective
Determine whether SEC MIDAS Metrics by Individual Security can be assigned a conservative point-in-time knowledge date before any incremental alpha test versus frozen LTM/F80.

## Fresh official verification
The SEC Metrics by Individual Security page currently states coverage from January 2012 through June 2026, more than 4,800 securities, daily security-level fields including Cancels, Trades, LitTrades, OddLots, Hidden, TradesForHidden, OrderVol, TradeVol, LitVol, OddLotVol, HiddenVol and TradeVolForHidden, and quarterly ZIP downloads from 2012 Q1 through 2026 Q2.

The page lists quarterly files by period label and size, and states "Last Reviewed or Updated: June 30, 2026." The page itself does not expose a historical publication/dissemination timestamp for each quarterly ZIP.

## Methodological decision
Do NOT use the quarter-end observation date as the information date. Do NOT use the current page's June 30, 2026 review date as the historical knowledge date for older files.

A conservative PIT mapping therefore remains unresolved from the live index alone. Before alpha testing, one of the following must be established reproducibly:
1. archived snapshots of the SEC download index showing when each quarterly file first became available;
2. SEC/EDGAR metadata or another official timestamped publication record that can bound first availability; or
3. a conservative lag convention justified independently and applied identically to every quarter, with sensitivity analysis showing that conclusions do not depend on the chosen lag.

## Research design if the PIT gate passes
Prefer hidden-volume and trade-to-order features initially. Treat odd-lot variables separately because of the SEC's November 3, 2025 round-lot definition change. Treat pre/post May 1, 2017 NYSE feed changes as separate regimes or include explicit controls.

Candidate daily features:
- HiddenVol / TradeVol
- Hidden / Trades
- Trades / OrderVol
- Cancels / OrderVol
- TradesForHidden / Trades

The first statistical test must be incremental information versus the frozen LTM/F80 signal, using chronological train/validation/OOS splits, identical exposure and costs, and no future revisions. Any evidence consistent with return-chasing must be explicitly separated from predictive content.

## Gate status
PIT release timing: NOT PROVEN.
Historical data feasibility: PASS at the source/catalog level.
Alpha authorization: FALSE.
Baseline modification: FORBIDDEN.

## Official source
SEC, Metrics by Individual Security:
https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security
