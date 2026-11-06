# Phase 167 — Cboe Open-Close v1.8 public sample and November 8 cutover audit

**Date:** 2026-11-06  
**Status:** Implementation committed; public sample workflow result pending.  
**Scope:** Validate the newly linked public 1-minute sample against the November 8, 2026 C1 v1.8 specification, test the 10-minute specification contract separately, and preserve the existing PIT/identity restrictions. No paid data, account, vendor contact, return test or production change.

## Why this phase

Phase 138 established that Cboe Open-Close is the strongest conditional participant-capacity/open-close options candidate in the current public research. Phase 139 built a conservative cumulative-snapshot state engine but did not download an Open-Close file. The current Cboe product page now exposes a new 1-minute sample and announces a schema/behavior cutover effective **2026-11-08**.

This phase uses only the exact public sample link surfaced by Cboe. It does not infer or construct a second sample URL.

## Source facts from current Cboe documentation

- Product page: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- New 1-minute specification: https://datashop.cboe.com/documents/Open_Close_1m_Spec_v1.8.pdf
- New 10-minute specification: https://datashop.cboe.com/documents/Open_Close_10m_Spec_v1.8.pdf
- Public 1-minute sample: https://datashop.cboe.com/documents/Cboe_OpenClose_2026-09-30_15_20_1.csv.gz

The product page advertises C1 EOD from 2005-01-03, C1 10-minute from 2011-01-03, C1 1-minute from 2019-10-07, and BZX/C2/EDGX intraday from 2019-03-01. These are advertised start dates, not proof of complete date/security coverage or first-publication vintages.

The page states that 1-minute and 10-minute files are cumulative snapshots, not interval-only volume. It also states that later snapshots reflect trade breaks/busts/cancellations and remove cancelled trades from subsequent snapshots. This reinforces Phase 139's rule: preserve snapshots; first differences are changes in published cumulative state, not trade-time interval volume.

## Schema contract frozen before sample execution

- 1-minute PDF cover: v1.8, dated 2026-11-08. Expected 80 columns; call_or_put; trading_dt; trading_segment; lower-case names.
- 10-minute linked PDF filename is v1.8, but its cover identifies itself as v1.7 dated 2026-11-08. Its 80-column contract uses call_put_flag, not call_or_put.
- Both specifications omit EOD-only fields 10–17 from intraday files.
- The 10-minute product-page change log describes the corrected field as cust_gt_199_close_buy, while the linked PDF lists cust_gt_199_close_buy_qty. This documentation discrepancy is retained unresolved; do not silently rename the field until an actual 10-minute sample or vendor confirmation resolves it.
- C1 uses a _1/_2 trading-segment suffix; C2/BZX/EDGX have null trading_segment. market_date and trading_dt remain separate.

## Audit implementation

The Phase 167 parser downloads the exact public 1-minute sample in memory, hashes it, parses gzip/CSV, validates the 80-column contract and row semantics, and writes only a metadata/count summary. Raw sample bytes, underlying symbols and option symbols are not persisted.

The tests cover both interval schema contracts, the 10-minute field-name ambiguity, filename parsing, gzip/CSV validation, row diagnostics, duplicate handling and no-raw-data persistence.

The workflow is PR-only and uploads a metadata-only artifact. It makes no purchase or authenticated request.

## PIT and economic limitations that remain

- The sample filename is dated 2026-09-30, before the announced 2026-11-08 cutover. It is a format sample, not evidence that post-cutover production files have been observed.
- Downloading a public sample on 2026-11-06 is archive/backfill retrieval. HTTP Date, Last-Modified or ETag do not prove first public receipt of the historical snapshot.
- The sample is one timestamp and cannot establish historical completeness, missing dates, inactive/delisted underlying coverage, or coverage of the broader PIT universe.
- The product covers Cboe exchanges only, not all OPRA venues. Capacity categories are trade-origin classifications, not named beneficial owners or proof of informed trading.
- The 1-minute/10-minute fields omit open interest. OI must be joined from a separately audited source with its own knowledge time and correction vintages.
- No feature or return test is authorized until first-receipt timestamps, historical coverage, effective-dated contract/underlying identity, delisted coverage, licensing and cost are resolved.

## Decision rule

If the public sample schema passes, promote only the parser/specification gate to PASS. Keep historical PIT, broad universe coverage, contract identity and alpha gates BLOCKED. If the sample fails, quarantine the conflicting field/schema and do not infer a data-source failure from a single sample.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No forward returns, bootstrap/LOO, OOS or final-holdout data are used in this phase.
