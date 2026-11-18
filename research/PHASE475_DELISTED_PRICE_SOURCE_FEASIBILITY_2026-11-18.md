# Phase 475 — Historical price-source feasibility for the seven inactive Phase 20C symbols

**Audit cutoff:** 2026-11-18 09:52 UTC  
**Base main:** `66f759045afa073da35e2e947e5f9949b521f5ad`  
**Disposition:** Massive Advanced is the strongest documented practical candidate for a complete historical OHLC panel, with Sharadar SEP as a second candidate and CRSP as the preferred terminal-return benchmark. **No source is admitted yet.** No credentials, trial, sample, vendor contact, purchase, price download or return test was performed.

## 1. Preflight — repository and live workflows

- Main HEAD: `66f759045afa073da35e2e947e5f9949b521f5ad` (Phase 474).
- Actions runs: 7,795 total at preflight; explicit queries returned zero `in_progress` and zero `queued`.
- Branches: 305; open PRs: 56; workflow files: 80.
- Latest Phase 473/474 audit jobs completed successfully: [44264686167](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44264686167) and [44264686208](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44264686208). Phase 474 is offline metadata regression only; no artifact.
- Full Phase 473 universe census [44258810704](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44258810704) completed successfully; artifact [14408145092](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44258810704/artifacts/14408145092) records 328/335 valid and seven inactive symbols.
- Latest scheduled CFTC capture [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204) succeeded.
- Latest scheduled SEC Form 144 capture [44228413864](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864) succeeded, but remains the first post-pagination capture/baseline without a prior bounded polling interval.
- Latest FINRA Phase 469 run [44228802578](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228802578) was a pull-request CI run, not a scheduled live capture. No first scheduled FINRA receipt is established at this cutoff.
- Cboe sample-rights issue [#132](https://github.com/jafelix81/NuevaEstrategia/issues/132) remains open; public artifact 13291147097 was not deleted because the available connector exposes no artifact-delete action.

No running workflow was duplicated, dispatched or rerun.

## 2. Exact Phase 20C data requirement

Phase 473's reproducible Phase 11 path needs the fixed 335-symbol universe and a daily history window of 2016-10-24 through 2026-10-24. The current census has 328 symbols above the 220-feature-row gate. The seven unresolved price histories are AVB, EA, EQR, LPRO, ROKU, WBD and WBS.

Phase 474 established their inactive/acquired/renamed status and contractual consideration, but all seven still have `last_trade_date=null`; no terminal total-return series exists. A provider must not be selected merely because it returns a close price for a legacy ticker. It must supply enough daily history, the final valid trading session, stable symbol/security linkage and data-use rights. Merger consideration still requires issuer/SEC evidence and, for stock deals, a successor price at the effective valuation time.

## 3. Provider comparison

### A. Massive (formerly Polygon) — conditional primary price-panel candidate

Official documentation states:
- Listed US stock bars begin 2003-09-10.
- Delisted tickers remain in the universe with their full history; the vendor describes this as free of survivorship bias.
- Stocks Advanced advertises 20+ years of history for $199/month, while Stocks Developer advertises a rolling 10-year window for $79/month.
- The exact Phase 20C start date, 2016-10-24, is 25 calendar days earlier than the Developer plan's ten-year lookback as of 2026-11-18. Developer therefore does not meet the exact frozen window at this audit date; Advanced is the documented individual-plan tier that does.
- Aggregate bars are split-adjusted by default; `adjusted=false` returns as-traded prices. Neither series is dividend-adjusted. Trades/quotes and flat files are unadjusted. Corporate-action documentation covers splits/dividends, with the stock product page describing corporate actions back to 2008.
- Individual plans are for personal/non-professional use; business use/display/redistribution requires a Business plan.

**Assessment:** best documented practical candidate for recovering daily bars for the seven delisted symbols and, if a full-universe sample passes, a single-source 335-symbol panel. Use raw/as-traded bars plus separately captured split/dividend events to construct a reproducible return series; do not use today's split-adjusted history as a permanent raw record. Massive's historical All Tickers endpoint is not a record-known vintage security master (Phase 390 already rejected it for strict PIT identity). Merger consideration and delisting terminal returns are not assumed to be supplied by its bar endpoint.

Official references:
- [Stocks product and plan history/pricing](https://massive.com/stocks)
- [Historical coverage and delisted tickers](https://massive.com/knowledge-base/article/how-much-historical-stock-data-does-massive-have)
- [Split/dividend adjustment methodology](https://massive.com/knowledge-base/article/is-massives-stock-data-adjusted-for-splits-or-dividends)
- [Pricing tiers](https://massive.com/pricing?product=stocks)

### B. Sharadar SEP — conditional second price/corporate-action candidate

Official documentation describes:
- EOD history from December 1997.
- Approximately 21,000 US stock tickers, including active and delisted securities.
- Split-adjusted OHLCV, unadjusted close and a close adjusted for splits, cash dividends and spinoffs.
- Corporate-action history from January 1998, including ticker changes, splits, dividends, spinoffs, listing/delisting dates/reasons and acquisition counterparties.
- Daily delivery and a stated reporting lag below one day.

**Assessment:** strong documented breadth and long history; potentially useful for a second independent cross-check or an alternative price panel. The public schema reviewed here does not establish a complete record-known vintage clock for historical corrections, nor does it establish a CRSP-equivalent delisting return field. Exact 335-symbol coverage, seven legacy rows, final trading dates, fractional cash-in-lieu, price revisions and license/subscription terms remain unverified. Do not treat the actions table's effective date as its first public availability time.

Official references:
- [Sharadar Prices / SEP](https://sharadar.com/prices)
- [SEP stock schema](https://sharadar.com/docs/stocks)
- [Corporate Actions schema](https://sharadar.com/docs/actions)

### C. EOD Historical Data — lower-cost secondary cross-check only

The personal EOD Historical plan is listed at $19.99/month and advertises 30+ years of EOD history and delisted tickers. Its own methodology FAQ explicitly warns that delisted coverage varies by ticker, may contain gaps or end before the last trading day, and is not guaranteed complete. It also states that corrections overwrite current records and there is no historical versioning or change timestamp. Raw OHLC is not rewritten for corporate actions; adjusted-close history is recalculated when new splits/dividends are added.

**Assessment:** useful only as a candidate secondary cross-check after a symbol-by-symbol sample. Not accepted as the sole source for final trading dates or terminal returns. For a reproducible price-label dataset, any future acquisition would need immutable dated snapshots/hashes and raw OHLC plus effective-dated actions; that still would not create historical record-known vintages.

Official references:
- [Pricing](https://eodhd.com/pricing)
- [Delisted ticker and correction methodology](https://eodhd.com/help/methodology)
- [Plan/history limitations](https://eodhd.com/help/plans)

### D. CRSP US Stock Database — preferred terminal-return benchmark if access exists

The existing Phase 97/390 audits document CRSP's active/inactive US security history, PERMNO/PERMCO identifiers, corporate actions and delisting fields including DLRET, DLRETX, DLPRC, DLPDT and DLAMT. It remains the strongest benchmark for terminal/delisting-return treatment among reviewed sources. Access and license are subscription/institution dependent, and the public material reviewed does not establish a complete record-known vintage clock for every mutable security-master field.

**Assessment:** preferred independent benchmark for terminal-return reconciliation, not assumed to be immediately accessible or a standalone strict-PIT identity feed.

### E. Norgate — not selected for this fixed-335 terminal-return repair

Phase 442 already documented listed/delisted history and stable asset IDs, but also found no delisting-return/terminal-recovery field, no record-known vintages, no prior-symbol history for this use case, and a personal/noncommercial-only EULA. Its paid Platinum pricing was $346.50 for six months or $630 for twelve months; its three-week trial is limited to two years. It is more appropriate for a separately defined index-universe research line than for the present custom 335-name terminal-return repair.

### F. Tiingo and Alpha Vantage — not admitted

Their public documentation describes long EOD histories and adjusted/raw price endpoints, but the reviewed pages do not provide sufficiently explicit guarantees for the seven inactive symbols' complete historical bars through the final trade, corporate-action consideration and terminal-return treatment. Alpha Vantage's historical listing-status endpoint is not itself a price-history guarantee. No sample or key was obtained.

## 4. Ranked decision

1. **Massive Advanced:** first candidate for a controlled, single-provider 335-symbol historical OHLC feasibility sample; strongest public claim for full delisted history and enough history for the exact window. Conditional on license fit, access and symbol-level verification.
2. **Sharadar SEP:** second candidate for a controlled coverage and corporate-action sample; strong active/delisted breadth and 1997 history, but PIT revision and terminal-return details remain unresolved.
3. **CRSP:** terminal/delisting-return benchmark if legitimate access exists.
4. **EODHD:** secondary cross-check only; explicitly incomplete delisted history and no data vintages.
5. **Norgate:** separate index-universe use only; not the current fixed-335 terminal-return source.
6. **Tiingo / Alpha Vantage:** no documented inactive-history contract sufficient for admission.

This is a documentation ranking, not a data-quality finding. No provider has passed an actual seven-symbol or 335-symbol sample.

## 5. Admission gates before any price fallback

A source may be admitted only after all of the following are evidenced:

1. Exact 2016-10-24 to 2026-10-24 daily window for all 335 original symbols, including all seven inactive names; no ticker dropped or replaced.
2. Raw/as-traded OHLC (or a fully documented equivalent) and a reproducible split/dividend/spinoff adjustment method.
3. First/last available date, missing sessions, final regular trading session, halt/delisting date and symbol/class lineage for each inactive security.
4. Contractual cash/share consideration reconciled to primary issuer/SEC filings; successor prices and fractional cash-in-lieu treated explicitly.
5. A permanent/effective-dated security identity layer. Price-provider historical ticker lookups are not assumed to be a record-known PIT security master.
6. Cross-provider price/return reconciliation on all seven plus a stratified sample of active controls, with corporate-action dates inspected individually.
7. Snapshot timestamp, exact request parameters, source/schema version and SHA-256 for every acquired file; no public repository artifact containing raw or licensed rows.
8. License explicitly permits the intended personal/non-professional research and private processing environment. No redistribution or client use is inferred.
9. The same provider and adjustment convention must cover the full 335 panel. No mixed-provider splice unless a separate, pre-registered reconciliation passes.

## 6. Research disposition

- No API key, account, trial, vendor contact, purchase, sample or raw price download was made.
- No provider is admitted as a fallback.
- No last-trade dates or terminal returns were reconstructed.
- No price labels, forward returns, alpha, OOS, bootstrap, LOO or holdout test was run.
- The seven names remain in the frozen 335 universe; none is dropped or replaced.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No capital, exposure, parameters, holding rules or production settings changed.

**Next gate:** if a legitimate data entitlement is later available, run a metadata-first, seven-symbol sample and a separate 335-symbol coverage census before downloading or retaining a full panel. If no source passes the exact coverage and rights gates, Phase 20C remains blocked rather than silently accepting a partial universe.
