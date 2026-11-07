# Phase 183 — Cross-source Smart Money data-admission and research-priority matrix

**Date:** 2026-11-07  
**Status:** `NO_SOURCE_PIT_ADMITTED_NO_ALPHA_TEST_AUTHORIZED`  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.  
**Scope:** Evidence synthesis of repository audits through Phase 182. No new raw-data download, vendor contact, purchase, return test, holdout use or production change.

## Executive decision

The broad research program now has several credible *measurement candidates*, but no source currently satisfies the complete chain needed for a strict historical feature:

1. representative raw data across early/middle/recent history and inactive securities;
2. first-receipt / knowledge-time evidence;
3. immutable correction and revision vintages;
4. effective-dated option/security identity;
5. versioned measurement methodology;
6. acceptable licensing and bulk-use terms.

The next work should not be another speculative signal or another single-day schema sample. It should be a deliberately small, matched-source data-admission exercise for the two complementary options measurements:

- **Cboe Open-Close:** opening/closing position buckets by participant-capacity and buy/sell side, limited to Cboe venues;
- **IvyDB TradeFlow:** OPRA-wide aggressor-side classification and vendor participant-size proxies.

These are not interchangeable. Agreement between them would be useful only after aligning venue, contract, interval, participant definitions and knowledge time. Neither is beneficial-owner identity or proof of informed trading.

IvyDB Open Interest is the natural contract-state complement, not a directional flow feature. IV/skew surfaces are context variables. Raw OPRA/TCBBO and PITCH are higher-cost microstructure alternatives with shorter or venue-specific strict-PIT windows.

The priority ranks below describe research sequencing and evidence efficiency, **not expected alpha**.

## 1. Cross-source gate matrix

| Source | Measurement role | Historical claim / sample evidence | Principal PIT or coverage blocker | Decision |
|---|---|---|---|---|
| Cboe Open-Close | Participant-capacity × buy/sell × open/close | C1 EOD from 2005; C1 10m from 2011; C1 1m from 2019-10; conservative multi-venue intraday floor 2020-03. Phase 167: 123,022 intraday rows / 2,642 underlyings; Phase 168: 23,179 EOD rows / 1,553 underlyings. | No historical first-receipt/vintage archive; cumulative snapshots revised by late trades and busts; Cboe venues only; adjusted contract/equity identity unresolved. | Top-tier conditional position-flow candidate. |
| IvyDB TradeFlow | OPRA-wide NBBO-signed aggressor flow and size proxies | Advertised from 2016; launched 2026-09-30; no representative raw sample audited. | Backfill is not live PIT; first receipt, corrections, classifier-version history, field-level 2016/2021 coverage, inactive names and licensing unresolved. | Top-tier conditional signed-flow candidate. |
| IvyDB US OI | Daily contract-level outstanding-position state | Advertised from 1996; permanent security/option IDs and delisted security history; no licensed raw sample. | Actual first receipt and patch vintages absent; OI timing regime break after 2000-11-28; optionable-universe coverage not measured. | Conditional long-history state complement; not directional flow. |
| IVolatility OPRA Signed Flow | NBBO-signed call/put flow, net premium/delta | Advertised from 2015; current same-evening delivery claim; no endpoint sample audited. | Methodology/conditions, first publication, revisions, identity, full-market bulk use and professional license unresolved. | Conditional broad signed-flow alternative. |
| Cboe Volatility Surfaces | IV/skew/term-structure context | Advertised from Aug 2011; Phase 136 sample: 360 rows, one underlying. | Calculation time is not receipt time; broad/inactive coverage and vintages absent; documented confidence/status exclusions required. | Conditional context only. |
| Databento OPRA + TCBBO | Raw trades and event-synchronous NBBO reconstruction | OPRA history from 2023-03-28; current docs list 20 venues. TCBBO strict live-PIT floor no earlier than 2025-05-27 absent delivery evidence. | Short strict-PIT window, earlier TCBBO backfill retrospective, corrections/receipt and contract identity still require audit. | Conditional raw microstructure cross-check. |
| Cboe Options PITCH | Sequenced order lifecycle / depth | Advertised archive from 2019-10; no complete project sample. | Venue-specific and anonymous; sequence-gap recovery, archive completeness, symbol/contract mapping, receipt and licensing unresolved. | Conditional venue microstructure; not participant identity. |
| FINRA ATS/OTC | Delayed off-exchange aggregate volume | Reconciliation passed; 1.735% of symbol aggregates revised, representing 10.08% of shares and 11.44% of trades. | No immutable first-publication panel; revisions materially affect economic volume; historical identity incomplete. | Context-only; no current alpha test. |
| FINRA short volume + short interest | Short-sale prints plus separately reported settlement position | Phase 20C: 1,382/2,020 daily files (68.42%); 329/335 names. | Incomplete daily panel, distinct denominators/semantics, after-close knowledge time, weak/inconsistent pseudo-OOS. | No promotion; only reconsider with new data and next-session execution. |
| CFTC TFF/COT | Aggregate futures positioning / market regime | Public index-futures reports; prior panel had 12 quarterly test dates. | Prior Phase 23C lacked horizon-specific label maturity embargo; report release calendar/vintages not fully reconstructed. | Quarantined; rebuild only with exchange calendar and full label embargo. |
| SEC 13D/G | Beneficial-ownership disclosure and stated purpose; not transaction-level flow | Phase 179 audited 497 legacy docs; no verified predecessor edge to an initial filing. | Insufficient issuer-level history, amendment/PAC lineage and effective-dated security identity. | No feature; lineage coverage insufficient. |
| SEC 13F | Delayed quarterly long holdings | EDGAR history; bulk data schema lacks accepted time-of-day. | Acceptance-time join, manager/shared-discretion graph, amendment state and effective CUSIP mapping required; long-only/incomplete. | Delayed context only; no alpha admission. |
| SEC Form 4 | Reported insider transactions | Existing Phase 21C tested six dates. | Bootstrap advantage intervals crossed zero at H5/H10/H20; tested feature family has no robust incremental edge. | Existing feature family killed for now. |

## 2. Complementary versus redundant measurements

### Complementary
- **Open-Close × TradeFlow:** position opening/closing versus aggressor direction. They can disagree for legitimate reasons; do not force a one-to-one mapping.
- **TradeFlow × OI:** signed execution pressure versus subsequent net contract-state change. OI is bilateral and cannot identify which side was informed.
- **Flow × IV/skew:** test whether trade pressure adds information beyond option-implied risk pricing, not whether a surface level alone predicts returns.
- **Raw OPRA/TCBBO:** independent reconstruction check for signing and trade-condition rules, subject to its shorter strict-PIT history.
- **PITCH:** order-book mechanism context; anonymous order IDs are not institutions or beneficial owners.

### Redundant or weakly independent
IVolatility Signed Flow, IvyDB TradeFlow and other OPRA-derived aggregates may share the same underlying OPRA prints. Cross-vendor agreement is not independent raw-market confirmation. Cboe Open-Close is a different venue-specific participant/open-close classification and is therefore complementary, not a duplicate.

FINRA short volume, FINRA ATS aggregates, CFTC positioning and SEC ownership filings measure different economic objects. They must not be merged into a generic “smart money” score without separate hypotheses and timing rules.

## 3. Recommended next data-admission sequence

### Stage A — matched sample / authorized access only
If lawful sample access becomes available, use one common specification across vendors:
- early, middle and recent years; include the 2016/2021 field-history boundary and 2025/2026 schema changes;
- high/low volatility, event/non-event, liquid/illiquid regimes;
- index, ETF and individual equities; include inactive/delisted names;
- expiries, moneyness, adjusted deliverables, multi-leg, midpoint, auction and complex conditions;
- preserve raw bytes, SHA-256, response headers, source version, first-received timestamp, retrieval timestamp and every later correction as a separate vintage.

Do not purchase data or accept terms until explicitly authorized. No vendor was contacted in this phase.

### Stage B — strict admission before feature construction
A source is admitted only when every required gate is evidenced:
1. representative raw sample and documented schema;
2. date × symbol coverage including inactive securities;
3. first-receipt / knowledge-time history;
4. immutable revision/correction lineage;
5. effective-dated underlying and option-contract identity;
6. methodology/schema version by date and field;
7. license, bulk-use and retention rights.

If first receipt cannot be reconstructed, historical backfill may support a clearly labelled *retrospective event-time study*, but not a strict historical PIT claim. It must not be mixed with live-PIT evidence.

### Stage C — preregistered economic test, only after admission
- Freeze feature definitions and a new prospective final holdout before outcome inspection.
- Use actual first-receipt time; execute no earlier than the next tradable session unless a replay proves intraday availability.
- Compare against frozen LTM/F80 and price/volume momentum controls.
- Separate continuation, temporary dealer-hedging pressure and reversal hypotheses.
- Use identical exposure, costs, turnover and capacity assumptions.
- Apply date-block bootstrap, leave-one-ticker-out, chronological walk-forward, multiple-testing control and horizon-specific label-maturity embargo.
- Report gross/net returns, drawdown, volatility, tail loss, turnover, capacity and regime stability.
- Reject any signal that only explains same-session price chasing or fails after costs.

No return test is authorized by this phase.

## 4. Research sequencing decision

1. First obtain representative, authorized Cboe Open-Close and IvyDB TradeFlow samples with delivery/vintage metadata. They provide the most complementary options measurements.
2. Add IvyDB OI only as contract-state confirmation, with the Phase 147 append-only correction ledger and post-2000-11-28 timing regime enforced.
3. Add IV/skew context after multi-symbol history and receipt evidence are demonstrated.
4. Use Databento TCBBO as an independent raw-signing cross-check from the strict schema-availability window; do not claim a long historical live-PIT sample.
5. Deprioritize repeating the same FINRA short-volume, SEC Form 4, CFTC 23C or 13D/G hypotheses on consumed/contaminated dates.

The ranking is based on measurement complementarity and feasibility, not on any assumption that institutional-looking flow predicts returns.

## 5. Reproducibility

- Snapshot: `research/phase183_options_smart_money_source_gate_matrix.json`
- Auditor: `research/phase183_options_smart_money_source_gate_matrix.py`
- Tests: `research/test_phase183_options_smart_money_source_gate_matrix.py`
- Workflow: `.github/workflows/phase183_options_smart_money_source_gate_matrix.yml`

The auditor is metadata-only and fail-closed. It asserts unique source IDs/ranks, exact gate schema, no implicit PIT admission, no alpha admission, no holdout use and no change to the frozen F80 baseline.

**Final disposition:** no source is PIT-admitted and no alpha test is authorized. No raw data were downloaded, no vendor was contacted, no purchase or terms acceptance occurred, no holdout was used, and production was not changed. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
