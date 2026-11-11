# Phase 251 — Cboe Open-Close four-venue convention and aggregation gate

**Audit date:** 2026-11-10 UTC  
**Status:** HOSTED_MEASUREMENT_CONTRACT_PASS_42_OF_42 — NO PIT / NO ALPHA  
**Branch:** `phase231-cboe-option-quotes-full-row-reparse`  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## 1. Why this phase follows Phase 250

Phase 250 correctly separated C1 directional imbalance from C1 total-volume and open-interest conventions. The official product page, however, describes a four-exchange Open-Close product. Phase 206 had already identified the archive starts and several exchange-specific breaks, but Phase 250's helper is intentionally C1-only. This phase converts the Phase 206 multi-venue findings into a fail-closed measurement contract without changing the C1 helper or assuming that all four venues have complete files.

The official product page says the EOD product covers selected Cboe exchanges C1, BZX, C2 and EDGX; files are separate by exchange; the product is not consolidated OPRA. Its advertised historical starts are:

| Exchange | EOD history advertised | Current post-migration capacity-family eligibility |
|---|---:|---:|
| C1 | 2005-01-03 | 2011-01-02 |
| BZX | 2018-01-02 | 2018-01-02 |
| C2 | 2018-01-02 | 2018-01-02 |
| EDGX | 2018-01-02 | 2018-01-02 |

Therefore:
- C1-only post-migration participant-flow study can begin 2011-01-02, subject to actual file acquisition and PIT gates.
- A four-venue Cboe panel cannot begin before 2018-01-02.
- C1 2005–2010 is a separate legacy Customer/Firm, original-order-size schema and is not pooled into the post-2011 Customer/Pro-Customer/Broker-Dealer/Firm execution-size family.

## 2. Exchange-specific convention matrix

The current Cboe product page documents these breaks:

| Exchange / field | Historical convention | Gate |
|---|---|---|
| C1 total exchange volume through 2019-10-04 | (Buy + Sell) / 2; current convention is Buy + Sell | Multiply the reported historical C1 value by 2 before comparing it on the current both-sides scale |
| C1 OI / previous OI through 2019-10-04 | Values shifted one day ahead | Do not use without an independently validated date-alignment repair |
| C1 previous close through 2019-10-04 | C1-only last trade | Do not treat as industry-wide underlying/option close |
| C2 total industry volume through 2018-05-11 | Values doubled | A reported-to-current scale multiplier of 0.5 is recorded; this field is not summed across venues |
| C2 OI / previous OI through 2018-05-11 | Values shifted one day ahead | Do not use without an independently validated date-alignment repair |
| C2 previous close through 2018-05-11 | C2-only last trade | Do not treat as industry-wide close |
| BZX / EDGX OI | Consistent start-of-day convention throughout history | Convention is recorded; PIT and cross-file consistency still need validation |
| BZX / EDGX previous close | Industry-wide last traded price convention | Do not substitute for an independently sourced underlying price series |
| C1 GTH | Begins 2023-12-11 | Tag the session regime; do not mix with RTH-only history without a control |
| FLEX series | New `F` code from 2024-10-16 | Exclude from the primary S/N panel; analyze separately only with a separate contract |

C1's legacy `W` code may appear before October 2019 and maps to Pro-Customer. Capacity codes are clearing-origin classifications, not beneficial-owner identities. Pro-Customer is not synonymous with an institution.

## 3. Safe cross-exchange feature construction

The helper implements only the post-migration volume-based feature family and requires each row to identify its exchange.

For each venue-specific option-series row:
1. Validate the exchange/date against the advertised archive start.
2. Reject C1 legacy-schema rows before 2011-01-02 from the post-migration feature family.
3. Restrict the primary cohort to standard `S` series. Non-standard `N` and FLEX `F` series are quarantined until an OCC deliverable/multiplier crosswalk is available; raw contract counts are not economically comparable across adjusted deliverables by assumption.
4. Validate the EOD file-level option key and reject duplicate rows within the same exchange. The same standard option series appearing on different exchanges is allowed and is not treated as a duplicate. This file-level key is not represented as a permanent OCC deliverable identity.
5. Compute the Phase 250 call/put directional contract proxy for the requested capacity/action/size bucket.
5. Apply the C1 historical total-exchange-volume scale of 2 through 2019-10-04; no undocumented scale is applied to BZX, C2 or EDGX total exchange volume.
6. Aggregate signed net contracts, gross capacity contracts and adjusted venue-specific exchange volume across the observed exchange rows.

The underlying-level imbalance is:

`sum(signed net contracts across observed venues) / sum(gross capacity contracts across observed venues)`

It is a ratio of sums, not an unweighted average of venue imbalances.

The optional denominator is observed Cboe exchange volume after the documented C1 scale correction. It is **not** total OPRA volume or consolidated market volume.

The helper deliberately does **not**:
- sum `total_industry_vol` across exchange files (it is a series-level industry value and C2 has a historical convention break);
- sum open interest across exchanges (it is not a venue-position quantity);
- use previous close as an underlying-price series;
- interpret an absent venue row or absent venue file as zero;
- claim complete venue coverage from a partial set of rows;
- claim that the EOD file-level option key resolves OCC adjusted deliverables;
- infer that capacity categories identify institutions or informed traders.

## 4. Data-feasibility and PIT decision

This phase establishes that a four-venue feature panel is structurally plausible from 2018-01-02, and that its venue-specific convention breaks can be encoded. The primary feature cohort is standard `S` series only; `N` and `F` are excluded pending deliverable/multiplier identity work. It does **not** establish that daily files can be obtained lawfully and continuously for the full history, that every historical file is complete, or that every symbol is covered.

The EOD specification describes historical files as one file per trade date per exchange. Subscriptions normally deliver preliminary and final files the following morning (typically 00:30–01:00 ET). The preliminary file can use OPRA-sourced total industry volume and OI; the final file uses OCC-sourced values that may differ. The Cboe FAQ allows delays, including a prior-day file arriving after the next market open. A trade date or nominal delivery target is therefore not a historical first-receipt timestamp.

Strict PIT remains blocked until a lawful sample/subscription provides:
- exact exchange, trade date, preliminary/final status and file name;
- immutable raw bytes and SHA-256 for each version;
- actual first-received UTC timestamp and later correction/replacement lineage;
- daily archive completeness by exchange;
- effective-dated underlying and option-series identity, including inactive/delisted names and adjusted/non-standard series;
- licensing terms for internal research and derived-feature use.

Raw Cboe data are licensed for internal use; external redistribution of derived data requires additional licensing/approval. No trial, account, card, vendor contact, purchase or API query was initiated.

## 5. Validation and research boundary

The deterministic helper and regression suite validate exchange-date classification, volume/OI/previous-close conventions, cross-venue duplicate handling, ratio-of-sums aggregation, missing-venue semantics and fail-closed exclusions. Hosted validation status is recorded in the current-state file after the workflow completes.

No historical files were acquired in this phase. No return labels, momentum controls, identical-exposure comparison, costs, block bootstrap, leave-one-ticker-out, chronological OOS or holdout test were run. The one-day 20% C1 sample from Phase 249 is not reused as evidence of four-venue coverage.

**Decision:** retain a four-venue Cboe Open-Close measurement candidate from 2018-01-02, conditional on actual multi-date file coverage and PIT receipt/vintage evidence. Do not promote a signal, use the consumed legacy holdout, or change production.

## 6. Sources

- Cboe Open-Close product page (exchange scope, historical starts, conventions, delivery, licensing): https://datashop.cboe.com/cboe-options-open-close-volume-summary
- Current EOD file specification v1.3: https://datashop.cboe.com/documents/Open_Close_EOD_Spec_v1.3.pdf
- Legacy C1 EOD specification v2.7: https://datashop.cboe.com/documents/Legacy_C1_Open_Close_EOD_Spec_v2.7.pdf
- C1 Open-Close historical availability notice (effective 2020-11-23): https://datashop.cboe.com/c1-open-close-and-optsum-data-availability-change
- Prior repository provenance/PIT analysis: `research/PHASE206_CBOE_OPENCLOSE_EOD_PROVENANCE_AND_PIT_ADMISSION_AUDIT_2026-11-08.md`

## Controls

- `F80_TOP20_PARTIAL50_BASELINE_C20`: frozen.
- Legacy holdout: `CONSUMED_NOT_PRISTINE`, not used.
- No alpha admission, no production/universe/capital change.
- No vendor purchase, trial, card authorization or contact.


## Hosted validation — 2026-11-10 UTC

- GitHub Actions run [42743448141](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42743448141), job `129589843456`, completed successfully.
- **42/42 deterministic regression tests passed.** The workflow also passed its explicit exchange-date and closed-PIT/alpha boundary assertions.
- No artifact was produced; the workflow validates deterministic code only.
- This does not validate real four-venue raw files, archive continuity, first-receipt vintages, security coverage or return prediction.
