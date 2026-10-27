# Phase 42 — SEC MIDAS official coverage re-check

Date: 2026-10-27

## Result

A fresh check of the SEC's live Market Structure Data Downloads pages materially strengthens the feasibility case for the MIDAS line.

The SEC's **Metrics by Individual Security** page currently states:
- coverage: **January 2012 through June 2026**;
- **more than 4,800 securities**;
- daily security-level fields including Cancels, Trades, LitTrades, OddLots, Hidden, TradesForHidden, OrderVol, TradeVol, LitVol, OddLotVol, HiddenVol and TradeVolForHidden;
- quarterly downloadable ZIP files from **2012 Q1 through 2026 Q2**.

The SEC's main Market Structure Data Downloads page also separately lists the security-and-exchange series.

## Research implication

This is a materially stronger public candidate than a short historical sample: it offers more than 14 years of daily security-level observations and enough breadth to make frozen-universe coverage testing meaningful.

However, the decisive issue remains **PIT release timing**. The public index exposes quarter labels and update dates but not a simple per-file historical publication timestamp. Therefore observation date must never be treated as knowledge date. A conservative release-date mapping must be established before alpha testing.

The research should initially favor variables less exposed to the documented methodology breaks, especially trade-to-order and hidden-volume measures. Odd-lot features require explicit treatment of the SEC's November 3, 2025 round-lot definition change. The May 1, 2017 NYSE feed change also requires pre/post-regime controls.

## Next gate

1. Obtain and parse representative quarterly ZIPs from pre/post-2017 and pre/post-2025 periods.
2. Measure overlap with the frozen universe and ticker continuity.
3. Establish conservative knowledge dates for each quarterly release.
4. Verify whether the release cadence makes the information economically usable for the strategy's holding horizon.
5. Only then run the pre-registered incremental OOS test versus frozen LTM/F80.

No alpha claim is made. No production baseline change is authorized.

## Official verification

SEC Market Structure Data Downloads: https://www.sec.gov/data-research/market-structure-data
SEC Metrics by Individual Security: https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security
