# Phase 434 — Item 408 / Form 4 cross-source temporal reconciliation

**Date:** 2026-11-16  
**Status:** source-semantics audit completed; no alpha admission  
**Scope:** one issuer, three Item 408 plans, selected linked Form 4 records

## Executive result

A hand-audited ServiceNow sample shows that Item 408 plan disclosures can be useful advance notice of potential supply, but they are not a reliable execution calendar and must be reconciled against Form 4 at transaction-row level.

Three findings matter:

1. **Gina Mastantuono:** the Form 4 record contains two plan-footnoted S-coded disposals dated 2023-10-09 (193 shares each; 386 total), while both Item 408 and the Form 4 footnote give a 2023-07-28 plan adoption date. The Form 4 submission has AFF10B5ONE=1. Under a straightforward date-only application of the director/officer cooling-off rule to the 2023-10-26 10-Q filing, the threshold is 2023-10-30 and the first subsequent weekday session is 2023-10-31. The observed 2023-10-09 S-coded transactions precede that threshold. This is an **apparent chronology inconsistency**, not a legal conclusion.
2. **Paul E. Chamberlain:** Item 408 says the plan was adopted 2023-08-21, while a later Form 4 footnote says 2023-08-31 — a 10-day cross-source discrepancy. The observed 2023-11-30 S-coded transaction (135 shares at $682) is after either calculated threshold.
3. **William R. McDermott:** Item 408 disclosed the 2023-08-31 plan in the 2023-10-26 10-Q; the first plan-footnoted S-coded Form 4 transaction in this audited sample is dated 2024-02-20. Here the periodic disclosure preceded the observed execution by 117 calendar days.

The casebook therefore supports a **potential future-supply / overhang hypothesis**, not a presumption that every disclosed plan is active, fully executable, compliant, or predictive.

## Source records

The 2023 Q3 ServiceNow 10-Q (CIK 0001373715, accession 0001373715-23-000419) disclosed:

| Insider | Item 408 adoption | Expiration | Disclosed plan quantity |
|---|---|---|---|
| Gina Mastantuono | 2023-07-28 | 2024-05-24 | 317 shares plus net shares from 8,019 gross vesting shares |
| William R. McDermott | 2023-08-31 | 2025-02-18 | 30,489 shares plus net shares from 9,986 gross vesting shares |
| Paul E. Chamberlain | 2023-08-21 | 2024-09-03 | 540 shares |

Source: [ServiceNow 2023 Q3 Form 10-Q](https://www.sec.gov/Archives/edgar/data/1373715/000137371523000419/now-20230930.htm).

The 10-Q was accepted at 2023-10-25 19:20:50 Eastern Daylight Time, after the 5:30 p.m. cutoff, and its official filing date was 2023-10-26. For point-in-time use, the adoption date is **not** the signal availability date. This audit uses 2023-10-26 as the conservative date-level availability boundary; it does not claim an exact first-public-byte timestamp.

### Cross-source event table

| Insider | Item 408 date | Form 4 footnote date | First observed plan-linked S date | Observed quantity | Item 408 before first observed S? |
|---|---|---|---|---:|---|
| Gina Mastantuono | 2023-07-28 | 2023-07-28 | 2023-10-09 | 386 | No |
| William R. McDermott | 2023-08-31 | 2023-08-31 | 2024-02-20 | Not aggregated here |
| Paul E. Chamberlain | 2023-08-21 | 2023-08-31 | 2023-11-30 | 135 | Yes |

Additional Gina Form 4 evidence: a later plan-footnoted S-coded disposal of 922 shares is dated 2023-11-01, after the conservative cooling-off boundary. The first 2023-10-09 Form 4 also includes M and F rows; these are not counted as S-coded plan supply. The F row is described as tax withholding. Only the two S rows carrying the plan footnote are counted in the 386-share event.

Official Form 4 source records:

- [Gina — accession 0001373715-23-000411](https://www.sec.gov/Archives/edgar/data/1373715/000137371523000411/wk-form4_1696971804.xml)
- [Gina — accession 0001373715-23-000423](https://www.sec.gov/Archives/edgar/data/1373715/000137371523000423/wk-form4_1698960226.xml)
- [William — accession 0001373715-24-000127](https://www.sec.gov/Archives/edgar/data/1373715/000137371524000127/wk-form4_1708562042.xml)
- [Paul — accession 0001373715-23-000496](https://www.sec.gov/Archives/edgar/data/1373715/000137371523000496/wk-form4_1701466248.xml)

## Cooling-off calculation and its limits

SEC Exchange Act Rules C&DI 120.29 says the required cooling-off period for directors and Section 16 officers ends at the later of 90 days after adoption/modification or two business days following disclosure of the relevant quarter's financial results, subject to a 120-day maximum. The filing date does not count as the first business day. The SEC's example is that a Monday filing permits trading on Thursday, absent holidays.

Source: [SEC Exchange Act Rules — C&DI 120.29](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-rules).

For the ServiceNow 10-Q filing date of Thursday 2023-10-26, the two following business days were Friday 2023-10-27 and Monday 2023-10-30; the first weekday session after that limb expired was Tuesday 2023-10-31.

| Insider | 90-day date using Item 408 adoption | Threshold using Item 408 date | First weekday session after threshold | Form 4 footnote date alternative |
|---|---|---|---|---|
| Gina | 2023-10-26 | 2023-10-30 | 2023-10-31 | Same date |
| William | 2023-11-29 | 2023-11-29 | 2023-11-30 | Same date |
| Paul | 2023-11-19 (Sunday) | 2023-11-19 | 2023-11-20 | 2023-11-29 threshold / 2023-11-30 next session |

The weekday-only helper is specific to these dates; no intervening federal holiday falls in the relevant calculation windows. It is not a general legal calendar engine.

**Important legal/methodological distinction:** the cooling-off rule is a condition for the Rule 10b5-1 affirmative defense, not a blanket prohibition on all insider trading. A Form 4 checkbox or footnote is a filer representation, not an SEC adjudication that all affirmative-defense conditions were satisfied. The apparent Gina chronology discrepancy must not be described as a violation. Possible explanations or corrections require source-level/legal review beyond this data audit.

## What this means for the research design

- Use the SEC filing's acceptance/first-seen timestamp, or a conservative next-session rule, as the Item 408 availability date. Never backdate the signal to plan adoption.
- Keep Item 408 plan facts, Form 4 transactions, and Form 144 notices as separate event types.
- Preserve AFF10B5ONE as a **submission-level filer flag**. Do not apply it blindly to every transaction row.
- Link plan transactions only when a row's footnote explicitly maps to the plan; preserve M/F/other codes separately.
- Do not assume Item 408 quantities equal actual sale quantities. Vesting, tax withholding, amendments, expiration, cancellation and other restrictions matter.
- A missing termination notice does not prove that a plan remains active. An expiration date is not proof that the plan executed in full.
- Do not assume S-coded Form 4 transactions are necessarily exchange executions; the code alone does not identify venue or beneficial-owner identity.
- The sample shows Item 408 preceded the first observed S-coded transaction for two of three plans, but this is a selected three-plan case study from one issuer. It is not a coverage estimate or evidence of alpha.

## Admission decision

| Gate | Result |
|---|---|
| Public source and filing provenance | PASS for this sample |
| Item 408 / Form 4 identity join | PASS for these three named insiders only |
| Cross-source plan-date consistency | PARTIAL — one 10-day discrepancy |
| Cooling-off chronology consistency | PARTIAL — one apparent pre-threshold reported event |
| 335-stock historical coverage | NOT AUDITED |
| Complete plan lifecycle / execution reconstruction | NOT ESTABLISHED |
| Incremental information vs LTM/F80 | NOT TESTED |
| Alpha / OOS / bootstrap / LOO | NOT RUN |

**Decision:** retain Item 408 as a conditional potential-supply source for a broader historical-coverage audit. Do not admit a signal, do not infer plan activity from a missing termination, and do not use the cooling-off date as a substitute for observed execution.

## Reproducibility

- Casebook: research/PHASE434_ITEM408_FORM4_CASES_2026-11-16.json
- Analyzer: research/phase434_item408_form4_temporal_reconciliation.py
- Tests: research/test_phase434_item408_form4_temporal_reconciliation.py
- The regression suite preserves unknown quantities, keeps form-level flags separate from row-level footnote linkage, and emits no legal-compliance classification.

No price returns were tested. No data was purchased. No workflow was manually dispatched. No production code or trading parameters were changed. F80_TOP20_PARTIAL50_BASELINE_C20, holdout, universe, parameters, capital, exposure and production remain frozen.
