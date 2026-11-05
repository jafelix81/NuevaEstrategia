# Phase 138 — Cboe Open-Close intraday, PIT/correction semantics and OPRA cross-check

**Date:** 2026-11-05  
**Status:** **PROMOTE CBOE OPEN-CLOSE TO TOP-TIER CONDITIONAL PARTICIPANT-POSITION-FLOW CANDIDATE.** Its public product specification is materially richer than the earlier EOD-only framing: intraday 1-minute and 10-minute cumulative snapshots are offered, with multi-year history across C1/C2/BZX/EDGX. Strict historical PIT, immutable first-publication vintages, complete universe coverage, exchange-share representativeness, and licensing remain unverified. No data purchase, vendor contact, trial, return test or production change.

## 1. Repository preflight — current as of this audit

- Repository: `jafelix81/NuevaEstrategia`; working branch: `phase99-broad-pit-universe-charter`.
- Branch head at preflight: `8cb00f306b67a728161958628eabf82346e8060d` (2026-11-05 22:19:04 UTC). This supersedes the earlier Phase 137 preflight's `1dd8c69...` head.
- GitHub Actions repository run list: 759 total runs; inspected the 30 most recent. The latest was Phase 136 run [42115525546](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115525546), completed successfully. Separate repository queries returned **0 in-progress and 0 queued** runs.
- Phase 136 job `127554052107`: setup, checkout, Python setup, compile, six offline regression tests, public sample audit and artifact upload all completed successfully. Artifact [13455975956](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115525546/artifacts/13455975956), 2,425 bytes, ZIP SHA-256 `a0f3d7fd5dbde7302dbacdcc6cf368e342a5d7d2880af35535fa182fc790829a`.
- The immediately preceding Phase 136 run [42115519293](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115519293) failed on a stale regression expectation that conflated negative extrapolation codes with low positive confidence; the next run corrected that expectation and passed. This is not a remaining data-integrity failure.
- Phase 133 OCC Flex run [42097577204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42097577204) completed successfully with artifact [13448395010](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42097577204/artifacts/13448395010).
- Phase 129 run [42081987897](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42081987897) is completed/cancelled, not active. Its job log explicitly shows the 45-quarter serial audit was cancelled at 18:57:42 UTC and no `out/` files or artifact were produced. Do not rerun unchanged.
- Current branch has zero check runs on head `8cb00f3`; no new workflow was dispatched. Documentation-only Phase 138 does not require another copy of Phase 136's path-filtered sample workflow.
- PR [#13](https://github.com/jafelix81/NuevaEstrategia/pull/13) remains open, unmerged and mergeable (`mergeable_state=clean`). It is 252 commits ahead and 1 commit behind `main` (118 changed files). No merge was performed.

## 2. Material correction: Open-Close is not merely EOD

The current official Cboe DataShop product page documents summaries for all selected Cboe options exchanges **C1, C2, BZX and EDGX**, with EOD, 10-minute and 1-minute versions. Each trade is bucketed by origin/capacity, buy/sell side and opening/closing position. Customer and Professional Customer trades have additional size buckets (<100, 100–199, >=200 contracts).

Official product page: https://datashop.cboe.com/cboe-options-open-close-volume-summary

### Historical coverage by product

| Exchange | EOD | 10-minute | 1-minute |
|---|---:|---:|---:|
| C1 | 2005-01-03 | 2011-01-03 | 2019-10-07 |
| BZX | 2018-01-02 | 2019-03-01 | 2019-03-01 |
| C2 | 2018-01-02 | 2019-03-01 | 2019-03-01 |
| EDGX | 2018-01-02 | 2019-03-01 | 2019-03-01 |

C1 Global Trading Hours coverage begins 2023-12-11. Before that, C1 intraday history does not contain GTH intervals. This is venue-specific coverage, not all OPRA venues or all U.S. options trading.

### Delivery / knowledge-time distinction

- EOD subscription files are delivered overnight after midnight U.S. Eastern.
- Intraday 1-minute and 10-minute snapshots are described as published minutes after each interval closes.
- The page does not provide an exact historical first-publication timestamp or immutable delivery log for each archived file.

Official product page and file specifications:
- Product: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- EOD specification: https://datashop.cboe.com/documents/Open_Close_EOD_Spec_v1.3.pdf
- 10-minute specification (announced effective 2026-11-08): https://datashop.cboe.com/documents/Open_Close_10m_Spec_v1.8.pdf
- 1-minute specification (announced effective 2026-11-08): https://datashop.cboe.com/documents/Open_Close_1m_Spec_v1.8.pdf

## 3. Critical data semantics — cumulative snapshots, not interval increments

The 1-minute and 10-minute specifications explicitly say trade count and volume in buckets are **aggregated throughout the day, not just for the latest interval**. Thus a file timestamped 10:30 is a cumulative snapshot through that point, not the incremental activity from 10:20–10:30.

Consequences:
1. Preserve raw snapshots. Do not sum consecutive files.
2. Derive interval activity only by first differences of the same cumulative bucket across consecutive snapshots, with explicit trading-date, exchange, session/segment and option-series keys.
3. Do not clip negative differences. They may represent subsequent corrections/busts/cancellations, not negative economic volume.
4. Late-processed trades may appear in a later snapshot than their trade time.
5. Use the file's actual first-received/publication time as `KnowledgeTime`, not `trade_datetime` or the filename interval.
6. Preserve every received version and hash. A backfilled/final corrected archive must not be substituted for the snapshot that was actually available at the historical decision time.

The new 1-minute and 10-minute specifications state that later trade breaks/busts/cancellations are reflected in subsequent snapshots, removing the canceled trades from later cumulative files. The 1-minute/10-minute files omit fields 10–17 (trade prices, total exchange volume, total industry volume, open interest and previous open interest); participant/capacity, buy/sell, open/close and contract-series fields remain.

**PIT gate:** Cboe's "minutes after interval close" statement is encouraging for prospective collection, but not sufficient for strict historical backtests unless archived snapshots can be shown to preserve first-publication vintages and actual delivery timestamps. Without that, only a conditional/final-state analysis is possible, not a strict PIT alpha test.

## 4. Participant taxonomy is not beneficial-owner identity

The published capacity mapping is:
- Firm: OCC codes F, L, J (clearing-member firm proprietary, non-Trading Permit Holder affiliate, joint back-office).
- Broker/Dealer: B.
- Market Maker: M, N.
- Customer: C (public customer).
- Professional Customer: U, W (professional account; W is a legacy Cboe code before October 2019).

These are trade-capacity categories, not named institutions, beneficial owners or proof of informed trading. Professional Customer is not synonymous with institutional investor. Customer size buckets are trade-size buckets, not account-size or capital measures. The dataset should be described as **participant-capacity / opening-closing position-side activity**, never as identified "smart money."

The file contains buy/sell and open/close by capacity. It does not, by itself, provide a complete OPRA-wide aggressor-side classification or identify the beneficial owner. Buy/sell side must not be equated with NBBO aggressor direction.

## 5. Historical convention and schema breaks to handle

The product page documents historical convention changes:
- C1 open interest / previous open interest values were shifted one day ahead through 2019-10-04.
- C2 open interest / previous open interest values were shifted one day ahead through 2018-05-11.
- C2 total industry volume was doubled through 2018-05-11.
- C1 total exchange volume was calculated as (buy + sell)/2 through 2019-10-04; current convention is buy + sell.
- C1 previous close was C1-only through 2019-10-04; C2 previous close was C2-only through 2018-05-11.
- Series type added explicit Flex ('F') from 2024-10-16; before that, standard/nonstandard were represented by S/N.

The EOD specification says preliminary files use OPRA for total-industry volume/open interest, while final files use OCC values; those fields may change between preliminary and final files. The product page also describes total-industry volume and open interest as third-party/best-effort value-adds. Treat these as a separate, versioned data family; do not mix preliminary and final OI or silently carry historical values across the documented convention changes.

## 6. Databento OPRA cross-check — a useful independent reconstruction route, with a hard 2023 boundary

Official OPRA dataset page: https://databento.com/datasets/OPRA.PILLAR  
Official schema documentation: https://databento.com/docs/datasets/opra-pillar  
Official 2025 history/normalization announcement: https://www.databento.tech/blog/opra-improvements-coming-soon  
Original 2023 product launch: https://databento.com/blog/opra-data

Established from the vendor's public documentation:
- OPRA.PILLAR covers 18 U.S. equity-options venues and has normalized trade/quote/definition schemas from 2013-04-01; schema availability differs by date.
- From 2023-03-28 onward, event-level TCBBO provides the NBBO immediately before each trade; CMBP-1 and CBBO-1s are also available. This is the viable event-synchronous trade/NBBO signing period.
- Before 2023-03-28, data are explicitly described as subsampled rather than packet-capture generated. TCBBO, CMBP-1 and CBBO-1s are unavailable; CBBO-1m is the highest BBO granularity. `ts_recv` equals the event timestamp and carries `F_BAD_TS_RECV`; the venue showing the NBBO is not identified, and Statistics contains only aggregated open interest.

Decision:
- Do **not** sign 2013–2023 trades using minute-end CBBO-1m as if it were the contemporaneous NBBO. That would introduce stale-quote/misclassification risk and false event-time precision.
- Treat 2013-04-01 to 2023-03-27 as coarse historical options context only.
- Treat 2023-03-28 onward as the first viable period for event-synchronous, all-OPRA trade/NBBO signing using TCBBO, subject to sample, correction/condition, security-identity, historical availability and licensing audits.
- Databento's 2023 launch announcement describes continuous T+1 historical availability from 2023-03-28; its 2025 addition of pre-2013-04-01 history is a retrospective extension. Do not backdate that later-added history as if it had been available in 2013.
- This route has no participant-capacity or beneficial-owner identity; it is an independent raw-market microstructure/signing comparison, not a "smart money" label.

## 7. Pre-registered feature architecture — design only, no returns test

If data gates pass, keep three constructs separate:

1. **Opening-position flow:** by option series and capacity, `open_buy_volume - open_sell_volume`, separately for calls/puts and customer-size buckets.
2. **Closing-position flow:** `close_buy_volume - close_sell_volume`, separately; do not merge with opening activity.
3. **Net delta-position change:** only after a valid contemporaneous option-delta join, `(buy_volume - sell_volume) × signed_option_delta × contract_multiplier`, separately for opening and closing. Do not infer direction from calls/puts without valid delta and corporate-action-aware contract deliverables.

Use trade-volume fields for contract counts and quantity-of-trades fields for event counts. Do not multiply by 100 blindly for adjusted/nonstandard/Flex contracts; require effective-dated deliverable/multiplier mapping. Intraday Open-Close has no IV/Greeks in fields 10–17, so delta must come from a separately validated contemporaneous quote/IV source. A close-of-day Greek cannot be backfilled into earlier intraday snapshots.

Before any alpha test:
- Validate all four exchange samples over early/middle/recent dates, all file timestamps, schema versions, holiday/early-close sessions, C1 GTH segments and missing files.
- Measure historical issuer-day and optionable-series coverage against the historical active universe, including delisted issuers; separately measure Cboe's share of total OPRA activity rather than assuming it is representative.
- Validate cumulative-difference reconciliation, late trades, negative correction deltas, duplicate rows, cross-exchange aggregation and EOD preliminary/final states.
- Establish immutable first-received snapshots and exact knowledge timestamps. If unavailable for the archive, do not call the historical test strict PIT; prospectively capture each snapshot with receipt time and SHA-256.
- Require the existing Phase 86 minimum of 95% coverage of historically optionable F80 issuer-days for any F80 comparison, while separately acknowledging the fixed-335 universe's unresolved survivorship/membership limitations.
- Compare against frozen LTM/F80 with identical exposure, execution assumptions and costs; chronological development/validation/locked OOS; horizons 1/2/5/10/20/40 sessions; block bootstrap and ticker/sector leave-one-out. Distinguish predictive information from price-chasing and control multiple testing.

## Decision

Promote Cboe Open-Close intraday/EOD to the **top-tier conditional participant-capacity and opening/closing activity candidate**. It is more useful than the prior EOD-only framing, especially for prospective 1-minute/10-minute capture. Keep strict historical PIT and coverage gates closed until immutable snapshots, delivery timestamps and historical security identity are demonstrated.

Databento OPRA is the strongest broad multi-venue route for independent trade/NBBO reconstruction from 2023-03-28 onward; pre-boundary data are not suitable for event-level signing. IVolatility's new 2015 signed-flow history remains a retrospective backfill until historical knowledge-time/vintages are shown. Cboe Volatility Surfaces remains a separate volatility-context candidate.

No raw data purchase, account/trial, vendor contact, terms acceptance, return test, portfolio change or production change occurred. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
