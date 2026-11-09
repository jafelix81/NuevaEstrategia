# Phase 244 — SEC FTD external release/receipt timeline audit

**Date:** 2026-11-09  
**Status:** `CONDITIONAL_EXTERNAL_OBSERVATION_PROXY_NOT_STRICT_PIT`  
**Research role:** settlement-friction / fails-to-deliver context; not short-sale flow or institutional identity.  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Executive finding

A new, potentially useful timing source was located: ChartExchange's public **FTD Release History** page reports three distinct dates for SEC fails-to-deliver archives: the expected release date, the file's reported modification date, and the date ChartExchange says its importer retrieved the file.

This is materially better timing evidence than assuming the SEC's nominal month-end / 15th schedule or using the ZIP's `Last-Modified` header. It is not yet a strict historical PIT ledger: the page provides date-only retrieval values, does not document whether each is the first or most recent importer retrieval, and does not expose immutable raw receipt bytes/hashes or prior data vintages.

**Decision:** retain the retrieval date as a conditional external observation-date proxy for a future conservative audit. Do not admit historical FTD values to a PIT backtest until both the receipt-log semantics and the value-vintage problem are resolved.

## 1. Official SEC schedule and measurement boundary

The SEC currently lists FTD data from February 2004 through September 2026. Since July 2009, the archive is split into first-half and second-half files. The SEC says the first half is generally available at month-end and the second half at about the 15th of the following month, but explicitly does not guarantee a particular posting date.

The SEC also confirms that:
- The row contains settlement date, CUSIP, ticker, issuer name, price and total fails.
- FTD is an aggregate net balance outstanding in NSCC's Continuous Net Settlement system across all NSCC members.
- Before 2008-09-16, the public data include only balances of at least 10,000 shares; on/after that date all positive balances are included.
- Fails can occur on both long and short sales and are not, by themselves, evidence of abusive or naked short selling.

Official source: https://www.sec.gov/data/foiadocsfailsdatahtm

## 2. New third-party retrieval evidence

ChartExchange's documentation defines:
- **Expected:** date implied by the SEC release schedule.
- **File Time:** modification date reported for the SEC file.
- **Retrieved:** date ChartExchange's importer retrieved the file.

The page-level summary reports 28.4% early, 50.8% on time and 20.7% late among its completed release records. These percentages are descriptive of ChartExchange's displayed history; its page does not provide a complete methodological denominator or a downloadable immutable receipt ledger.

Selected examples visible on the page:

| FTD file | Expected | File Time | Retrieved | Timing implication |
|---|---|---|---|---|
| Sep 2026, second half | 2026-10-15 | 2026-10-01 | 2026-10-15 | File time preceded retrieval by 14 days |
| Sep 2026, first half | 2026-09-30 | 2026-09-15 | 2026-09-29 | Retrieved one day before nominal date |
| Jan 2026, first half | 2026-02-02 | 2026-01-15 | 2026-02-03 | Retrieved one day late |
| Oct 2025, first half | 2025-10-31 | 2025-10-15 | 2025-11-13 | Retrieved 13 days late |
| Oct 2023, first half | 2023-10-31 | 2023-11-21 | 2023-11-21 | Retrieved 21 days late |
| Oct 2026, first half | 2026-11-02 | 2026-10-15 | 2026-10-30 | Retrieved three days before nominal date |

The timeline displays a monthly first-/second-half sequence from October 2021 through September 2026, plus October 2026 first-half. Earlier records include obvious backfills: the August/September 2021 files shown on the page carry a common 2021-10-08 retrieval date; July 2009 files carry a 2022-05-03 retrieval date. Those dates are not contemporaneous publication records for the underlying historical observations.

Source: https://chartexchange.com/docs/ftd-release-history/  
Audit method: manual review of the rendered public timeline on 2026-11-09. This was not a programmatic full-page census and no source HTML snapshot or cryptographic hash was obtained.

## 3. What the new evidence does and does not establish

### Useful

1. A third party's importer has recorded an observation date for many recent FTD archive files.
2. The examples demonstrate that expected dates and file modification dates can precede actual importer retrieval by days or weeks.
3. If the retrieval date is independently shown to be the first time the importer obtained the exact file bytes, it is a conservative **known-by date**. For daily trading research, use the first XNYS session strictly after that date; do not backdate to settlement date, expected date or file modification date.
4. The October 2023 and October 2025 delays make a fixed expected-date convention unsafe.

### Still blocked

1. **First versus latest retrieval:** the documentation says “date our importer retrieved the file,” but does not explicitly say whether the field is immutable first receipt, latest re-fetch or a backfill/import date.
2. **Time of day:** only a calendar date is shown. A same-day close is therefore never justified; the next-session rule is required even if the date is later verified.
3. **Value vintages:** the page does not preserve the exact ZIP bytes/hash associated with each retrieval date, nor a sequence of historical corrections. A current SEC ZIP may contain values that were not present in the version first retrieved.
4. **Coverage census:** the visible timeline is a useful lead, not a machine-verified proof that every file and every revision is represented.
5. **Security identity:** prior Phase 102/106 work still requires effective-dated CUSIP-to-permanent-ID mapping and inactive/delisted return linkage.
6. **Measurement regime:** pre-2008-09-16 observations have a 10,000-share threshold and cannot be pooled naively with later files.

## 4. Research decision

| Gate | Result |
|---|---|
| Official historical archive / schema | PASS from prior Phases 102/106 |
| Official nominal release cadence | PASS, but dates are not guaranteed |
| Independent date-only retrieval proxy | CONDITIONAL |
| Exact first-receipt timestamp and semantics | NOT ESTABLISHED |
| Immutable historical ZIP/value vintages | NOT ESTABLISHED |
| Effective-dated permanent security identity | NOT ESTABLISHED |
| Inactive/delisted return linkage | NOT ESTABLISHED |
| Historical FTD feature / return test | NOT AUTHORIZED |
| PIT / alpha admission | NO |

**Do not treat the ChartExchange retrieval date as an official SEC publication timestamp or as proof that its current data values are the original values available on that date.** It may be useful as a conservative external observation-date proxy only after its first-versus-latest retrieval semantics and raw-version linkage are verified.

## 5. Next admissible work

1. Preserve a dated snapshot of the ChartExchange timeline and SEC index as evidence, without treating either as an immutable historical receipt ledger.
2. If a prospective SEC FTD capture is later implemented, store the exact index and ZIP bytes, SHA-256, pipeline receipt timestamp, response headers, archive URL and append-only revision lineage. The first scheduled observation is baseline-only; later new files/revisions are state updates unless a never-before-observed report can be proven.
3. Resolve CUSIP to effective-dated permanent security identifiers with inactive/delisted coverage.
4. Keep the 2008-09-16 reporting-threshold break explicit.
5. Only after all data gates pass, preregister level/change/persistence and scale-normalized FTD hypotheses. Execute no earlier than the first regular XNYS session after verified receipt and compare incrementally with frozen LTM/F80 under identical exposure, costs, bootstrap/LOO and chronological OOS.

No return data were joined; no feature or alpha was tested; no bootstrap/LOO, OOS or holdout was used; no vendor was contacted; no data was purchased; no production or universe change occurred.
