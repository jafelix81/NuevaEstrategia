# Phase 357 — Cboe DataShop availability metadata and PIT-clock reconciliation

**Date:** 2026-11-13 UTC  
**Branch:** `phase357-cboe-product-metadata-pit-reconciliation`  
**Status:** `COMPLETED_DOCUMENTATION_CONFLICTS_IDENTIFIED_NO_DATA_ADMISSION`  
**Parent:** Phase 356, draft PR #43

## Objective

Recheck the current official Cboe DataShop product pages, FAQ and OCC public open-interest interface after Phases 352–356. Identify conflicting historical start dates and determine whether documented delivery times can support strict point-in-time (PIT) reconstruction.

## Official sources reviewed

1. [Cboe Open-Close Volume Summary product page](https://datashop.cboe.com/cboe-options-open-close-volume-summary), accessed 2026-11-13.
2. [Cboe DataShop FAQs](https://datashop.cboe.com/faqs), accessed 2026-11-13.
3. [Cboe Option EOD Summary product page](https://datashop.cboe.com/option-eod-summary), accessed 2026-11-13.
4. [OCC public Open Interest page](https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/open-interest), accessed 2026-11-13.
5. Internal Phase 354 OCC endpoint audit and Phase 352/353 source audits.

## 1. Availability metadata conflicts

### Open-Close interval products

The current product-specific Open-Close page distinguishes the interval products:

| Venue | Current product page | FAQ table |
|---|---:|---:|
| C1 interval | 10-min: 2011-01-03; 1-min: 2019-10-07 | “Interval”: Jan 2011 |
| BZX, C2, EDGX interval | 10-min and 1-min: 2019-03-01 | “Interval”: Mar 2020 |

The FAQ does not distinguish 1-minute from 10-minute intervals and conflicts with the product page for BZX/C2/EDGX. The product-specific page is the better current description, but the historical start is not treated as file-validated.

**Conservative disposition:** keep the product-page dates as documented claims, but do not admit disputed BZX/C2/EDGX interval history before March 2020 without actual dated files or written vendor clarification. Do not silently replace the Phase 352 product-page dates; this phase records the unresolved conflict.

### Option EOD Summary

- Product-specific Option EOD Summary page: historical availability from **January 2012**.
- DataShop FAQ table: **January 2010**.

The FAQ may reflect a prior product naming or availability regime, but the current evidence does not establish that. Use January 2012 as the provisional conservative start. Do not claim or use pre-2012 Option EOD data unless actual files or written vendor confirmation establish it.

### Open-Close EOD

The product-specific page and FAQ agree on the broad EOD start dates: C1 from January 2005 and BZX/C2/EDGX from January 2018. This agreement does not establish daily completeness, inactive/delisted underlying coverage, or historical PIT vintages.

## 2. Daily delivery is not an exact PIT timestamp

The Open-Close product page says EOD files are delivered overnight after midnight U.S. Eastern. The FAQ's broader daily-file guidance says files for a trade date are typically uploaded the following day between **00:05 and 03:00 ET**, but delays can push delivery until after the next market open.

Consequences:

- A fixed 00:30–01:00 ET assumption is not a safe first-receipt timestamp.
- Trade date, filename timestamp, scheduled delivery window and first-receipt time are different fields.
- A next-day feature is usable only after the exact file version has actually been received and validated.
- Historical backfill files do not establish the time at which that version was originally available.
- Any prospective archive must retain append-only raw bytes, observed UTC receipt time, exchange, trade date, file/version identifier and SHA-256. Preliminary and final versions must remain separate; replacements/corrections must never overwrite the original receipt.

**PIT decision:** the documented delivery schedule is insufficient to admit historical files as strict PIT. The prospective receipt-time gate remains closed because no capture process has been activated.

## 3. OCC public OI is not a long-history series-level validator

The OCC public Open Interest page currently states that its interactive daily data are available for the past **24 months**. This is useful for recent spot checks, not a long-history independent reference.

Phase 354 separately tested the OCC public Daily Open Interest batch endpoint for March 2025. Its successful response contained daily market-wide aggregate totals, not per-option-series OI. It therefore cannot validate Cboe's per-series OI rows. This is a granularity mismatch, not evidence that Cboe OI is incorrect; do not repeat the same endpoint query as if it could supply contract-level history.

The Cboe Open-Close final file documents OCC-sourced OI, but source lineage is not a substitute for independent contract-level reconciliation.

## 4. Updated source disposition

| Component | Current disposition | Reason |
|---|---|---|
| Open-Close EOD participant flow | Conditional candidate | Sample schema/accounting pass, but historical coverage and PIT vintages unproven |
| Option EOD OPRA context | Conditional companion | Product page says Jan 2012; FAQ conflicts at Jan 2010; session and S/N/F identity joins unresolved |
| Open-Close 1-minute history | Conditional, not admitted | Official product page and FAQ disagree on BZX/C2/EDGX start; cumulative snapshots and correction vintages require first-receipt capture |
| OCC public daily OI page | Recent spot-check only | Public page states past 24 months |
| OCC public daily OI batch endpoint | Killed for contract-level validation | Phase 354 found aggregate-only response |

The daily EOD pair remains preferable to the 1-minute route for a daily swing hypothesis, but this is a research-priority decision, not evidence of alpha.

## 5. Required next gates

1. If a permitted historical file sample later becomes available, verify actual dates and headers around the disputed availability windows; do not infer file existence from a product-page date alone.
2. Obtain explicit written clarification only if the user authorizes vendor contact. No contact, trial, quote request, subscription or purchase was made or initiated.
3. Before any PIT use, implement append-only prospective capture with actual UTC first-receipt timestamps and immutable preliminary/final/correction vintages.
4. Resolve RTH/GTH comparability and S/N/F/deliverable crosswalk before joining participant flow to OPRA Option EOD.
5. Quantify underlying/date coverage against a survivorship-aware historical universe, including inactive/delisted names and historical option roots.
6. Only after all data gates pass, preregister incremental tests against frozen LTM/F80 with matched exposure/costs, chronological OOS, block bootstrap, ticker/sector clustering, LOO and multiplicity controls.

## Decision and controls

**Complete the documentation/PIT-clock reconciliation only.** The official metadata contains unresolved conflicts, and scheduled delivery is not a historical first-receipt ledger. Keep the disputed periods quarantined. Do not infer historical PIT from product start dates or vendor schedules.

- No raw historical subscription files inspected in this phase.
- No historical coverage or inactive/delisted coverage established.
- No historical PIT vintages admitted; no prospective capture activated.
- No return, alpha, OOS, bootstrap, LOO or holdout test authorized or run.
- No vendor contact, quote request, trial, subscription, purchase or license acceptance.
- No universe, capital, parameter or production change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
