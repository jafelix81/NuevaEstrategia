# Phase 524 — Form 144 / Form 4 cross-source event semantics

**Audit time:** 2026-11-20 10:44 UTC  
**Base main:** `e44ef875f4d1215387003c9c77cec603c65abe5a`  
**Disposition:** a current Form 144 record exactly matches a Form 4-reported sale that occurred nine days earlier and was filed seven days earlier. This is a material warning against treating Form 144's approximate sale date as a future execution timestamp or assuming every Form 144 is a leading signal.

## 1. Preflight

- Latest 100 GitHub Actions runs inspected; repository total 7,959.
- 0 active, queued, waiting or requested workflows.
- Main HEAD after Phase 523 merge: `e44ef875f4d1215387003c9c77cec603c65abe5a`.
- No capture workflow was dispatched or duplicated.

## 2. Exact Clean Energy Fuels cross-source match

### Form 4 — realized transaction

Public SEC Form 4 for Andrew J. Littlefair / Clean Energy Fuels Corp.:
- Accession: `0001400209-26-000018`.
- Transaction date: 2026-11-10.
- Transaction code: S.
- Disposed: 100,000 common shares.
- Price: $1.8391 per share.
- Gross proceeds: approximately $183,910.
- Direct shares held after: 1,882,832.
- SEC acceptance: 2026-11-12 21:02:10 UTC (16:02:10 ET).
- SEC XML: [Form 4 primary XML](https://www.sec.gov/Archives/edgar/data/1400209/000140020926000018/form4-11122026_091106.xml).

### Form 144 — notice with matching fields

Clean Energy Fuels Form 144:
- Accession: `0001974078-26-000422`.
- Seller: Andrew J. Littlefair, director.
- Notice / EDGAR acceptance: 2026-11-19 20:57:06 UTC (15:57:06 ET).
- Approximate sale date: 2026-11-10.
- Proposed quantity: 100,000 common shares.
- Aggregate market value: $183,391.
- Broker: Raymond James & Associates.
- Rule 10b5-1 adoption date: none reported.
- “Securities Sold During the Past 3 Months”: Nothing to Report.
- Issuer-hosted primary document: [Form 144, Nov. 19, 2026](https://investors.cleanenergyfuels.com/sec-filings/all-sec-filings/content/0001974078-26-000422/primary_doc.html).

The Form 144's date, quantity and seller match the Form 4 transaction. The Form 4 was accepted seven calendar days before the Form 144; the transaction date was nine calendar days before the Form 144. The Form 144's “Nothing to Report” flag also appears inconsistent with the matching Form 4 sale in the preceding three months.

The Form 144 was first observed by our collector at 2026-11-19 21:00:26 UTC. Its bounded first-seen interval is 2026-11-19 02:50:33–21:00:26 UTC; this is a conservative receipt bound, not the exact public dissemination time. The EDGAR acceptance timestamp is recorded separately.

**Classification:** `MATCHED_FORM4_SALE_PRECEDES_FORM144_NOTICE`; `PRIOR_SALES_FLAG_CONFLICT`; `FORM144_NOT_A_LEADING_EVENT_FOR_THIS_CASE`.

This is a strong exact match and an apparent filing/data inconsistency. It is not a legal conclusion about the filer, broker or transaction. The order-placement timestamp is not present in either filing, and we cannot determine from these records alone why the Form 144 was submitted after the reported transaction.

The matching Form 4 accession is not present in the current 1,268-row first-seen Form 4 event ledger or 20-accession structured-detail ledger. The public filing was located independently. Do not infer the reason; the collector is universe-scoped and this issuer may be outside its candidate universe.

## 3. Rule 144 timing: authoritative current guidance

The current eCFR text of 17 CFR 230.144(h)(3), up to date as of 2026-11-18, says the Form 144 is transmitted concurrently with either placing the order with a broker or executing the sale directly with a market maker:
- [eCFR §230.144(h)(3)](https://www.ecfr.gov/current/title-17/chapter-II/part-230/section-230.144).

SEC Division of Corporation Finance C&DI Question 136.09 interprets “concurrently” as the same day as the order placement or direct execution. Question 136.05 says no waiting period is required between order and execution if the form is transmitted concurrently. Question 136.01 says if the person does not sell the securities referred to in a Form 144, no amendment reflecting non-sale is required:
- [SEC Corporation Finance Interpretations, Questions 136.01 and 136.05–136.09](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations-cfis/consolidated-corporation-finance-interpretations) (updated 2026-11-17).

These rules make the Clean Energy pair a timing inconsistency worth preserving for source-quality review. They do not establish a legal violation: the broker order time, filing-agent context and any corrective facts are not observable in this dataset.

## 4. Reclassification of the other pre-notice dates

Phase 523 identified four Form 144 records whose approximate sale date precedes the notice date. They must not all be treated as anomalies or completed sales.

1. **Verano Holdings Corp. — 144/A:** the amendment explicitly reports that a Rule 10b5-1 plan adopted 2026-08-11 was terminated effective 2026-11-18 and that 15,100 shares had already been sold Nov 11–17. This is a post-event amendment / past-sales record, not a new future-sale signal.
2. **Clean Energy Fuels Corp. — 144:** exact Form 4 match described above; post-trade relative to the Form 4.
3. **Eagle Bancorp Montana, Inc. — 144:** approximate sale date 2026-11-18, notice 2026-11-19; no matching sale Form 4 located at the audit cutoff. The date alone does not prove execution. A follow-up filing may still arrive; if no sale occurs, SEC C&DI 136.01 says no amendment is required.
4. **Griffon Corp. — 144:** approximate sale date 2026-11-16, notice 2026-11-19, and “Nothing to Report” for past three months. The issuer-hosted filing confirms the fields. No matching Form 4 was located at the audit cutoff; do not infer execution or cancellation.

The correct label for the latter two is `FORM144_PROPOSED_OR_UNCONFIRMED`, not “executed sale” and not “invalid filing”.

## 5. Research implications and controls

- `approxSaleDate` is an approximate date supplied in a notice; it is not a reliable execution timestamp and must never be used as the public event time.
- Use the EDGAR acceptance time and the collector's first-seen upper bound as separate clocks. For conservative trading tests, use the later defensible availability bound.
- Treat Form 144 as an intent/order notice only when its actual filing/availability precedes execution. If a matching Form 4 transaction date precedes Form 144 availability, classify it as post-trade or unresolved and exclude it as a leading signal.
- Cross-link Form 144 and Form 4 on issuer CIK, reporting owner, security class, shares, transaction date, price/value and accession lineage. Require a high-confidence multi-field match; never join on ticker and date alone.
- Add a consistency check for `nothingToReportFlag=Y` when a matching Form 4 sale exists in the preceding three months. Quarantine the pair for review rather than automatically rewriting either filing.
- A missing Form 4 after a Form 144 is not proof of cancellation or non-execution: SEC C&DI 136.01 says no amendment is required if no sale occurs, and filing windows/collector scope matter.
- Do not treat Form 144 proposed quantity as executed supply. Use Form 4 as post-trade confirmation, while preserving the Form 144 notice as its own event.

## 6. Strategy controls

No return labels, event study, backtest, alpha test, OOS, bootstrap, LOO or holdout test was run. No signal admitted. The Clean Energy pair is an external source-quality case and is not eligible for F80 testing unless historical universe membership and identity are independently established.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No production, exposure, cost, universe or holdout changes.

**Conclusion:** Form 144 is not uniformly a pre-trade lead. The Clean Energy exact match shows why event-time semantics and Form 4 linkage must be resolved before testing any proposed-sale feature.
