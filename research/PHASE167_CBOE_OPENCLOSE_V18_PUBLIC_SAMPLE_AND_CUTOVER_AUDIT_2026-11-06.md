# Phase 167 — Cboe Open-Close public sample and November 8 cutover audit

**Date:** 2026-11-06  
**Status:** 1-minute sample schema gate passed; final previous-close classification audit is in the current revision.  
**Scope:** Validate the newly linked public 1-minute sample against the November 8, 2026 C1 v1.8 specification, test the 10-minute specification contract separately, and preserve the existing PIT/identity restrictions. No paid data, account, vendor contact, return test or production change.

## Source and cutover

- Product page: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- 1-minute specification: https://datashop.cboe.com/documents/Open_Close_1m_Spec_v1.8.pdf
- 10-minute specification link: https://datashop.cboe.com/documents/Open_Close_10m_Spec_v1.8.pdf
- Exact public sample: https://datashop.cboe.com/documents/Cboe_OpenClose_2026-09-30_15_20_1.csv.gz

The product page advertises C1 EOD from 2005-01-03, C1 10-minute from 2011-01-03, C1 1-minute from 2019-10-07, and BZX/C2/EDGX intraday from 2019-03-01. These are advertised start dates, not proof of complete date/security coverage or first-publication vintages.

The specifications state that intraday buckets aggregate throughout the day, and later snapshots can reflect late trades and trade breaks/busts/cancellations. Phase 139's conservative rule remains: preserve each snapshot; a first difference is a change in published cumulative state, not trade-time interval volume.

## First hosted sample retrieval

Run 42281643361 downloaded the exact public sample successfully. The first parser version passed all 19 offline tests but incorrectly expected 80 headers and stopped before uploading its summary.

Observed sample facts from the run log:

| Metric | Result |
|---|---:|
| Rows | 123,022 |
| Distinct underlyings | 2,642 |
| Distinct series keys | 123,022 |
| Duplicate series rows | 0 |
| Compressed / decompressed bytes | 1,662,958 / 26,954,796 |
| Calls / puts | 66,649 / 56,373 |
| Equity / ETF / index rows | 82,516 / 26,384 / 14,122 |
| Standard / nonstandard / Flex rows | 122,550 / 54 / 418 |

All rows had one trade_datetime matching the filename's 2026-09-30 15:20 ET timestamp; trading_dt matched 2026-09-30 and trading_segment matched suffix 1 on all 123,022 rows. The raw sample SHA-256 was e8e969df08c85069c3916b54f5b5d20b1b6aa05b98a68173b90c15bc7aa31020. No raw sample or underlying/option symbols were persisted.

## Schema correction prompted by the sample

The 1-minute PDF enumerates 88 field positions. Fields 10–17 are described as empty/not included in 1-minute intervals, rather than requiring their header labels to be absent. The sample has 88 lower-case headers and includes eight EOD-only placeholder columns. It also uses total_cboe_vol where the PDF names total_exchange_vol.

The revised parser therefore:
- validates all 88 sample columns, preserving the observed total_cboe_vol alias separately from the PDF's total_exchange_vol;
- counts nonblank values in all eight EOD-only placeholders and passes the schema gate only if they are empty;
- parses days_to_expire as an integer-valued decimal when the value is mathematically integral, while reporting the decimal formatting separately;
- reports field-level invalid/missing counts, row-key duplicates and date/segment concordance;
- retains only hashes, counts and metadata, never raw rows or symbols.

The first run's 26,258 aggregate base-value diagnostics were not sufficiently granular to interpret; the revised audit breaks them down by field. Its metadata-only artifact is uploaded even when the schema gate fails, so a mismatch is not hidden by a failed job.


## Second hosted sample run

Run 42282406737 passed 24 offline tests, sample download, schema gate and metadata-only artifact upload: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42282406737. Artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42282406737/artifacts/13536036202.

The 88-column lower-case sample header matched the revised sample contract. All eight EOD-only placeholder columns were present but completely empty. The sample uses total_cboe_vol rather than the PDF's total_exchange_vol; the alias column was also empty. Thus the parser/schema gate passes without treating the empty EOD placeholders as data.

The second run isolated the previous aggregate row-quality diagnostic: 26,258 of 123,022 rows (21.34%) have previous_close <= 0; blank previous_close is zero, and all other parsed field diagnostics are zero. Positive previous_close coverage is 78.66%. The third parser revision now distinguishes zero, negative, blank and nonnumeric previous_close values. Zero is preserved as a separate sentinel-like value without assuming it means missing; negative and nonnumeric values remain invalid. The follow-up hosted artifact is authoritative for the final split.

## 10-minute documentation discrepancy

The 10-minute linked PDF filename says v1.8, but its cover identifies v1.7 dated 2026-11-08. It uses call_put_flag rather than call_or_put. The product-page change log describes the corrected field as cust_gt_199_close_buy, while the PDF lists cust_gt_199_close_buy_qty. Keep these discrepancies explicit; do not silently rename the field. No 10-minute sample URL was inferred or downloaded.

## PIT and economic limitations

- The sample date 2026-09-30 precedes the announced 2026-11-08 cutover. It is a public format sample, not a post-cutover production capture.
- HTTP Date, Last-Modified and ETag identify the retrieved asset but do not prove the first public receipt of the historical snapshot.
- One timestamp cannot establish historical completeness, missing dates, inactive/delisted underlying coverage, or coverage of the broader PIT universe.
- Cboe capacity categories are trade-origin classifications, not named beneficial owners or proof of informed trading; this product is Cboe venue-specific, not whole-OPRA.
- Intraday files omit usable OI by specification; OI must be joined from a separate source with its own knowledge time and correction vintages.
- No feature or return test is authorized until first-receipt timestamps, historical coverage, effective-dated contract/underlying identity, delisted coverage, licensing and cost are resolved.

## Decision

The initial parser failure was an audit-contract defect, not evidence that Cboe data are unusable. The revised hosted artifact is the authoritative check of whether the eight placeholder columns are empty and whether the row-level fields conform. Even a schema pass promotes only the parser/sample gate; PIT, broad universe coverage, contract identity and alpha remain BLOCKED.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No forward returns, bootstrap/LOO, OOS or final-holdout data are used in this phase.
