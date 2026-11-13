# Phase 351 — Cboe TBT public sample row-grain and execution-linkage audit

**Date:** 2026-11-13 UTC  
**Branch:** `phase351-cboe-tbt-public-sample-row-grain-audit`  
**Scope:** one publicly offered Cboe TBT sample; schema, row grain, execution IDs, complex IDs, quotes, capacity and timestamps. No paid data, vendor contact, historical return test or production change.

## Why this phase

Phase 236 identified TBT as a higher-information C1 options-flow candidate but did not obtain or parse the public sample. The current Cboe product page exposes a public sample and documents 22 execution-level fields. Phase 351 closes that implementation gap without treating the sample as historical PIT data.

Official product page: https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail  
Official v1.1 specification (2026-10-05): https://datashop.cboe.com/documents/TBT_Spec_v1.1.pdf  
Public sample endpoint: https://datashop.cboe.com/download/sample/289

## Measurement contract

The parser preserves the distinction between:
- `TRANSACT_TIME` and `TRADING_DT` (which can differ around GTH midnight);
- `SIDE` (Buy/Sell) and `OPEN_CLOSE` (Open/Close);
- capacity categories and actual beneficial-owner identity;
- `EXEC_ID` (simple buy/sell linkage) and `COMPLEX_EXEC_ID` (complex-to-complex leg linkage);
- NBBO and executing-exchange BBO;
- trade type, session and trading segment.

It measures, rather than assumes, rows per execution ID, buy/sell pairing, multi-capacity groups, complex-ID leg cardinality, exact duplicate rows, crossed quotes, trade prices outside NBBO, missing quote fields and floor-action lags of at least 90 seconds. Raw sample rows and underlying names are not persisted in the artifact.

The parser fails closed on header drift, row-width mismatch, invalid side/open-close/call-put/capacity/session codes, missing required trade fields and non-positive/non-integer size. It does not infer aggressor direction from `SIDE`.

## PIT and economic boundary

Cboe documents the current TBT archive from 2019-10-07, T+1 delivery, and C1-only coverage. Phase 236 found public launch documentation only on 2026-02-20. Therefore:
- pre-2026-02-20 archive records are retrospective backfill, not strict historical PIT;
- post-launch records require actual per-file first-receipt timestamps, immutable revisions and licensing evidence;
- a public sample download timestamp is not a historical first-receipt record.

No forward returns, alpha, OOS, bootstrap, LOO or holdout tests are run. This phase does not promote TBT to production or claim a Smart Money signal.

## Expected outputs

The workflow uploads only a metadata/aggregate JSON artifact with archive/member hashes, counts, categorical distributions, row-grain diagnostics and closed PIT/alpha gates. No raw ZIP, CSV, symbol list or trade-level record is uploaded.

## Controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No vendor was contacted, no paid data was ordered, no card or trial was requested, and no terms were accepted. No production, universe, capital or parameter changes.
