# Phase 206 — Cboe Open-Close EOD provenance, versioning and PIT admission audit

**Audit date:** 2026-11-08 UTC  
**Disposition:** conditional high-value options-positioning candidate; **not strict-PIT admitted and no alpha test authorized**.  
**Scope:** official Cboe DataShop product page, current EOD specification v1.3, legacy C1 EOD specification v2.7, Cboe FAQ, and the repository's Phase 168/173/185 sample and timing audits. No purchase, vendor contact, raw subscription download, holdout use or production change.

## 1. New finding: EOD has two publication vintages

The current EOD specification says a subscription normally produces **one preliminary and one final file per exchange per trade date**. Delivery is typically 00:30–01:00 U.S. Eastern the following morning. The preliminary file sources `total_industry_vol` and `open_interest` from OPRA; the final file sources authoritative values from OCC. Those values are usually the same, but can change, especially when OCC results are delayed.

This is not a cosmetic distinction. The two files are separate knowledge states. A historical panel that retains only the final file would erase what a subscriber could have known from the preliminary file; overwriting preliminary with final would create look-ahead in any intraday or early-next-session replay. Preserve both as append-only versions, with actual first-received timestamps and hashes.

The public sample audited in Phase 168 does **not** resolve this: it contains one C1 member named `C1OpenClose_2025-03-28_sample_20pct.csv`, classified as EOD, but the member is `SAMPLE_UNSPECIFIED`; the sample has no ETag or Last-Modified, no preliminary/final pair, and no file-version identity. It is a 20% schema sample, not evidence of historical subscriber delivery or a representative universe panel.

## 2. Delivery timing is not a guaranteed PIT clock

Three timing statements must remain distinct:

- EOD product page: delivered overnight after midnight ET.
- EOD specification: subscription files are typically delivered 00:30–01:00 ET next morning.
- Cboe FAQ: daily files are typically uploaded 00:05–03:00 ET next day, but delays can cause the prior day's file to arrive **after the next market open**.

The first two describe normal processing; the FAQ explicitly allows a late-delivery case. None supplies historical per-file first-receipt logs or a hard maximum latency. Therefore the trade-date close cannot be treated as the knowledge time, and a fixed T+1-open assumption is not defensible. A T+2 sensitivity can be reported in a separately labelled retrospective study, but it is not a substitute for actual receipt evidence and does not establish strict historical PIT.

For strict PIT, require immutable preliminary and final file bytes, source/version metadata, first-received timestamps, and correction/replacement lineage. A prospective shadow capture could establish these facts only after an authorized subscription and licensing review; no such purchase or contact was made here.

## 3. Historical coverage and structural breaks

The current product page advertises:

| Exchange | EOD archive start | Scope implication |
|---|---:|---|
| C1 | 2005-01-03 | Longest EOD history |
| BZX, C2, EDGX | 2018-01-02 | Four-venue Cboe panel only from 2018 |

The product captures option series with trading volume on the selected Cboe exchange(s), with one file per exchange. It is **not consolidated OPRA/all-market coverage**. C1 files include regular and global trading sessions, but C1 Global Trading Hours coverage begins only 2023-12-11.

The current and legacy specifications expose material breaks that must be encoded before any feature panel is built:

| Regime / field | Documented convention | Research consequence |
|---|---|---|
| C1 pre-migration, through 2010-12-31 | Legacy schema has customer and firm only; size buckets use original order size | Not comparable to post-2011 capacity or execution-size buckets |
| C1 post-migration, from 2011-01-02 | Expanded origin categories; size buckets based on execution size | New measurement regime, not a seamless continuation of legacy buckets |
| C1 OI / previous OI through 2019-10-04 | Values shifted one day ahead | Must correct the date convention before using OI changes |
| C2 OI / previous OI through 2018-05-11 | Values shifted one day ahead | Must correct the date convention |
| C2 total industry volume through 2018-05-11 | Values doubled | Do not compare raw values across the break |
| C1 total exchange volume through 2019-10-04 | Calculated as (buy + sell) / 2; current convention is buy + sell | Normalize or split the series |
| C1 previous close through 2019-10-04 | C1-only last trade; later convention differs | Not a stable industry-wide price field |
| C2 previous close through 2018-05-11 | C2-only last trade; later convention differs | Not a stable industry-wide price field |
| Series type from 2024-10-16 | New `F` value for FLEX; earlier history uses `S` / `N` | Preserve the FLEX classification boundary |
| C1 Global Trading Hours from 2023-12-11 | Session coverage expands | Avoid mixing RTH-only and RTH+GTH activity without a session control |

The legacy C1 specification documents a pre-migration file format for 1990–2010, but the current DataShop product page advertises the purchasable C1 EOD archive from 2005-01-03. Do not assume the 1990–2004 files are included in the current product without separate confirmation.

## 4. What the participant buckets mean — and do not mean

The EOD product is genuinely more informative than raw option volume because it classifies Cboe executions by origin/capacity, buy/sell and open/close, with customer and professional-customer execution-size buckets. It still does not identify beneficial owners or institutions.

The current mapping is:

- Firm: capacity codes F, L, J.
- Broker/dealer: B.
- Market maker: M, N.
- Customer: C (public customer).
- Professional customer: U and legacy W; W is documented as a legacy Cboe professional code before October 2019.

These are exchange capacity codes, not investor identities. “Professional customer” is not synonymous with an institution; “customer” is not necessarily retail; “firm” combines proprietary clearing-member, joint-back-office and affiliate categories. No bucket should be labelled “smart money” without a separately tested hypothesis.

The product page says raw data are licensed for internal use only; external distribution of derived data requires additional licensing and approval. No terms were accepted.

## 5. Reconciliation with prior repository evidence

- **Phase 168:** 23,179 unique option-series rows and 1,553 underlyings in one 20% C1 EOD sample dated 2025-03-28; zero duplicate series rows. The member's identity is sample-based, not a subscription file vintage. No raw rows/symbols were persisted, and no receipt/version evidence exists.
- **Phase 173:** concerns the separate Cboe Option EOD Summary product, not Open-Close. Its OCC open interest semantics are previous-night OCC EOD OI at the start of quote date, static during the session. Do not conflate that product with the Open-Close EOD preliminary/final files.
- **Phase 185:** already rejects historical intraday backfill as proof of live availability and notes the overnight EOD timing problem. This phase adds the EOD preliminary/final source distinction and the legacy C1 schema/capacity break.
- **Current Cboe page's 2026-11-08 enhancements apply to intraday 1-minute/10-minute files.** Do not apply those intraday schema/correction rules to the EOD product.

## 6. Decision and next gate

**Keep Cboe Open-Close EOD as a conditional high-value options-position/open-close candidate, but do not admit any historical row to strict PIT or alpha testing yet.**

If authorized access is later obtained, the minimum matched sample should include:
1. C1 dates before and after 2011, 2019-10-04 and 2023-12-11;
2. C2 dates before and after 2018-05-11;
3. BZX and EDGX post-2018-01-02;
4. at least one date with preliminary/final OCC differences, if available;
5. liquid and less-liquid underlyings, ETFs, equities and indices, plus adjusted/non-standard series;
6. raw bytes, hashes, exact file name, exchange, schema version, first-received timestamp, preliminary/final status and every later correction.

Only after coverage and effective-dated contract identity pass should features be preregistered. Candidate hypotheses must be separated (e.g., professional-customer opening imbalance, firm opening imbalance, customer closing pressure, and capacity interactions), normalized by eligible Cboe volume/open interest, and tested against frozen LTM/F80 plus price/volume momentum controls. Use identical exposure and costs, chronological walk-forward, label-maturity embargo, date-block bootstrap, leave-one-ticker-out, and a **new prospective final holdout** frozen before outcome inspection. The legacy holdout is `CONSUMED_NOT_PRISTINE`.

No feature, return test, bootstrap/LOO, OOS test or holdout test is authorized by this phase.

## 7. Sources

- Cboe Open-Close product page: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- Current EOD specification v1.3 (2025-11-10): https://datashop.cboe.com/documents/Open_Close_EOD_Spec_v1.3.pdf
- Legacy C1 EOD specification v2.7 (2026-02-17): https://datashop.cboe.com/documents/Legacy_C1_Open_Close_EOD_Spec_v2.7.pdf
- Cboe DataShop FAQ / SFTP delivery timing: https://datashop.cboe.com/faqs
- SEC SR-CBOE-2026-011: https://cdn.cboe.com/resources/regulation/rule_filings/approved/2026/SR-CBOE-2026-011.pdf

**Controls:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No holdout use, data purchase, vendor contact, production/universe change or strategy modification.

---

## Machine-readable disposition

```json
{
  "phase": 206,
  "audit_date": "2026-11-08",
  "source": "Cboe Open-Close Volume Summary EOD",
  "status": "CONDITIONAL_CANDIDATE_NOT_STRICT_PIT_ADMITTED",
  "archive_start": {
    "C1": "2005-01-03",
    "BZX_C2_EDGX": "2018-01-02"
  },
  "subscription_versions": {
    "preliminary": "OPRA total_industry_vol and open_interest",
    "final": "OCC authoritative total_industry_vol and open_interest",
    "typical_delivery_et": "00:30-01:00 next morning",
    "faq_delivery_window_et": "00:05-03:00 next morning; may be delayed until after next market open",
    "historical_first_receipt_verified": false,
    "hard_max_latency_documented": false,
    "sample_preliminary_final_pair_observed": false
  },
  "coverage": {
    "selected_cboe_exchanges_only": true,
    "consolidated_opra_coverage": false,
    "C1_GTH_start": "2023-12-11",
    "sample_is_20pct_C1_only": true,
    "sample_date": "2025-03-28",
    "sample_rows": 23179,
    "sample_underlyings": 1553,
    "sample_duplicate_series_rows": 0,
    "sample_file_version_identity_resolved": false
  },
  "methodology_breaks": {
    "C1_legacy_schema_through": "2010-12-31",
    "C1_post_migration_start": "2011-01-02",
    "C1_OI_shift_through": "2019-10-04",
    "C2_OI_shift_through": "2018-05-11",
    "C2_total_industry_volume_doubled_through": "2018-05-11",
    "C1_total_exchange_volume_half_sum_through": "2019-10-04",
    "series_type_FLEX_start": "2024-10-16"
  },
  "participant_identity": {
    "capacity_buckets_available": true,
    "beneficial_owner_identity": false,
    "professional_customer_equals_institution": false
  },
  "strict_pit_admitted": false,
  "alpha_test_authorized": false,
  "holdout_used": false,
  "production_changed": false,
  "data_purchase": false,
  "vendor_contact": false,
  "f80_frozen": true,
  "next_gate": "Authorized matched raw sample with preliminary/final vintages, first-receipt timestamps, correction lineage, effective-dated option identity and broad inactive/universe coverage."
}
```
