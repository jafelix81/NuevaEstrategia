# Phase 139 — Cboe Open-Close snapshot state and Nov-08 schema cutover

**Date:** 2026-11-05  
**Status:** Offline state-engine PASS (23/23 synthetic tests). Historical PIT, universe and alpha gates remain blocked.  
**Scope:** Source-contract audit and pure validator only. No paid data, account/trial, vendor contact, terms acceptance, forward-return test or production change.

## 1. Repository preflight

- Repository: jafelix81/NuevaEstrategia
- Branch: phase99-broad-pit-universe-charter
- Pre-write head: 3ee949cde31d2437e74e0d3cfd36e843178b3859
- main head: 36d8eabb348d6a959bd2e7f4f9ffa31fc94087c9
- PR #13: open, unmerged, mergeable/clean; 261 commits ahead and 1 behind main; 119 changed files.
- Actions API: 759 total runs; latest 30 inspected; zero in progress or queued.
- Latest run: Phase 136, 42115525546, success. Job 127554052107 passed setup, compile, six tests, sample audit and upload. Artifact 13455975956 (2,425 bytes; ZIP SHA-256 a0f3d7fd5dbde7302dbacdcc6cf368e342a5d7d2880af35535fa182fc790829a).
- Phase 136's 2025-04-07 sample has four files/360 rows but only one underlying. It is a schema pass, not universe coverage.
- Phase 129 (42081987897) remains cancelled at the 45-minute limit with no final artifact; do not rerun unchanged.

## 2. New Cboe schema/behavior cutover effective 2026-11-08

The current Cboe product page announces a cutover effective Sunday, November 8, 2026.

**1-minute specification v1.8**
- Lowercase column names; adds trading_dt and trading_segment.
- Later snapshots reflect breaks/busts/cancellations by removing cancelled trades.
- Removes indicative/unsettled trades to avoid duplicate rows.

**10-minute specification v1.7**
- trade_datetime format changes to YYYY-MM-DD HH:MM:SS; adds trading_dt and trading_segment.
- Corrects cust_gt_199_clsoe_buy_qty to cust_gt_199_close_buy.
- Removes indicative/unsettled trades.
- Final 10-minute file changes to 17:00 for C1 and 16:15 for BZX/C2/EDGX.
- Customer files change from ZIP to gzip (.csv.gz).

Official references:
- Product page: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- 1-minute spec: https://datashop.cboe.com/documents/Open_Close_1m_Spec_v1.8.pdf
- 10-minute spec: https://datashop.cboe.com/documents/Open_Close_10m_Spec_v1.8.pdf (document identifies v1.7, dated 2026-11-08)

Do not difference across the schema/behavior cutover. market_date and trading_dt are separate identity fields. For C1, trading_segment is integer 1 or 2; it is null for C2/BZX/EDGX. It is not an RTH/GTH label. C1 GTH may span calendar days and a market date may have multiple segments. Keep segment and date fields in every key.

## 3. Critical semantics: first differences are not interval trade volume

The new 1-minute and 10-minute specifications state that volume/count buckets are aggregated throughout the day, not only over the latest interval. They also say trades may be processed late and appear in a later snapshot; subsequent busts/breaks/cancellations remove trades from later snapshots.

Therefore current cumulative state minus prior cumulative state is only the change in the published aggregate since the previous received file. It can include late-reported trades and corrections. It is not necessarily the volume executed during the clock interval.

Use the name reported_increment_since_prior_received_snapshot. Do not call it interval_volume, do not clip negative differences, and do not backdate late-reported volume to an earlier trade time. Negative differences are retained and flagged as corrections.

## 4. Historical coverage discrepancy

The product page advertises:
- C1 EOD from 2005-01-03; C1 10-minute from 2011-01-03; C1 1-minute from 2019-10-07.
- BZX/C2/EDGX EOD from 2018-01-02; both intraday intervals from 2019-03-01.

The current FAQ instead says C2/BZX/EDGX interval Open-Close begins March 2020. Until Cboe resolves the discrepancy, use 2020-03-01 as the conservative multi-venue intraday history floor for C2/BZX/EDGX. Keep the product-page 2019 date as an unverified lead, not a validated coverage claim.

Sources:
- https://datashop.cboe.com/cboe-options-open-close-volume-summary
- https://datashop.cboe.com/faqs

Neither advertised start date proves complete symbol/day coverage, inactive/delisted underlying coverage or first-publication timestamps.

## 5. PIT-safe state engine

Added:
- research/phase139_cboe_openclose_snapshot_state.py
- research/test_phase139_cboe_openclose_snapshot_state.py

The validator requires separate market_date/trading_dt; exchange, interval, C1 segment (1/2) or null for other venues; schema and contract-map versions; timezone-aware snapshot and first-received times; receipt not before snapshot; monotonic knowledge time; raw-file SHA-256 metadata; unique option-series keys; and nonnegative integer cumulative metrics.

It differences only common series/metric keys. New and removed series are listed separately, never assumed to have zero. Missing metrics are counted, not filled. Negative differences are preserved. Same cutoff/same hash is a duplicate; same cutoff/different hash is a revision, not a time increment. Archive backfills cannot pass the live-capture PIT-pair gate.

The output is explicitly called reported_increment and says it is not trade-time interval volume. strict_pit_pair is only pair-level provenance for two LIVE_FIRST_RECEIPT snapshots; it is not a historical archive claim or alpha admission. Alpha remains blocked pending universe, identity, coverage and cost gates.

Offline regression: 23/23 synthetic tests passed locally. They cover positive increments, negative corrections, new/removed series, archive/live capture, snapshot/knowledge ordering, timezone, schema and contract-map changes, C1 segment semantics, non-C1 null segment, market-date/trading-date distinction, duplicates/revisions, missing metrics, invalid cumulative values and hash format. No Cboe file was downloaded in Phase 139.

## 6. Decision

- Historical archive: NOT STRICT PIT until immutable first-publication vintages and per-file receipt times are evidenced.
- Prospective capture: technically feasible candidate only if every original file is captured on first receipt, timestamped, hashed, versioned and never overwritten. The pipeline may act only after its actual receipt time.
- Coverage: unverified beyond advertised date floors; the FAQ/product-page discrepancy remains open.
- Universe/identity: blocked pending option-series mapping, adjusted deliverables/multipliers, permanent underlying IDs and inactive/delisted coverage.
- Alpha: not authorized. If the gates pass, compare with frozen LTM/F80 under identical exposure/costs and chronological OOS, bootstrap and LOO discipline.

Cboe states raw data are licensed for internal use and redistribution is restricted. No order, account/trial, vendor contact, purchase, terms acceptance or production change occurred. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
