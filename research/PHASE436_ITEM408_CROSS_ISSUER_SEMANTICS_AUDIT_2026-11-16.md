# Phase 436 — Item 408 cross-issuer schema and plan-semantics stress audit

**Date:** 2026-11-16  
**Status:** six-issuer purposive source-semantics audit completed; no alpha admission  
**Scope:** six public SEC filings from Juniper Networks, Dexcom, CarGurus, Powell Industries, Celanese and General Mills. This is a deliberately selected stress sample, not a random sample, a coverage census or an estimate of Item 408 prevalence in the frozen 335-name universe.

## Executive result

Phase 435 established a second issuer-level Item 408 / Form 4 / Form 144 case. Phase 436 tested whether the same normalized interpretation can be applied safely across multiple issuers.

The six filings contain **12 plan actions: 11 adoptions and one termination**. The normalized direction classes are **nine sell, one buy, one exercise-and-sell, and one unresolved direction**. One termination is expressed as a $45,000 value rather than a share count. We do not add amounts across those categories or bases.

The main result is methodological: **Item 408 is not a single homogeneous “future insider selling” field.** A robust pipeline must distinguish transaction direction, lifecycle action, amount unit/basis, vesting/withholding, option exercise, trust ownership, explicit transaction windows, and public availability. The current ECD fact list contains aggregate-available and text-block facts but no dedicated buy/sell direction concept; direction must be resolved from the actual narrative/table semantics or left unknown.

## Cross-issuer sample

All filing-index acceptance timestamps below are Eastern wall time. Acceptance is not certified first-public receipt. For a daily close-to-close strategy, this audit conservatively sets the first eligible session to the next regular trading session after the filing date, regardless of whether acceptance was intraday or after the close.

| Issuer | Filing / accepted ET | First eligible session | Item 408 semantic issue |
|---|---|---|---|
| Juniper Networks (JNPR) | 10-Q, 2024-04-26 16:32:36 ET | 2024-04-29 | 188,669-share ceiling appears under “purchased or sold”; direction is not resolved by the row |
| Dexcom (DXCM) | 10-Q, 2024-04-25 17:17:02 ET | 2024-04-26 | Three sell plans; gross/conditional quantities depend on vesting, tax withholding, PSUs, ESPP and limit orders; one plan is adopted on behalf of a trust |
| CarGurus (CARG) | 10-Q, 2024-05-09 16:11:18 ET | 2024-05-10 | Three new sell plans plus a prior plan termination in the same filing; two stated share quantities are gross future-award shares before withholding, and one prior plan is expressed in dollars |
| Powell Industries (POWL) | 10-Q, 2024-05-01 12:40:02 ET | 2024-05-02 | Two sell plans disclose explicit future transaction-window start dates |
| Celanese (CE) | 10-K, 2024-02-23 16:19:23 ET | 2024-02-26 | Separate sold and purchased columns; the 4,000-share plan is a purchase, not sale supply |
| General Mills (GIS) | 10-Q, 2024-09-18 15:35:07 ET | 2024-09-19 | 57,879-share plan is tied to stock-option exercise and sale, not simply disposal of already-owned common shares |

### Source-level observations

**Juniper Networks — unresolved direction**

The filing's row reports “Up to 188,669 shares” under a column headed “Aggregate Number of Shares of Common Stock to be Purchased or Sold.” The inspected row does not state whether the plan is a purchase or sale. It is encoded as `direction=unknown`, not defaulted to sell.

- Filing index: https://www.sec.gov/Archives/edgar/data/1043604/000104360424000066/0001043604-24-000066-index.htm
- Structured rendering: https://www.sec.gov/Archives/edgar/data/1043604/000104360424000066/R24.htm

**Dexcom — gross/conditional future awards and trust ownership**

Three plans list 6,000, 3,352 and 102,732 shares to be sold. The issuer's footnote explains that actual sale quantities may depend on net vesting, tax withholding, PSU vesting, ESPP purchases and limit orders. The Foletta plan was adopted on behalf of a trust for which he serves as trustee. The stated figures are not clean, immediately executable share supply.

- Filing index: https://www.sec.gov/Archives/edgar/data/1093557/000109355724000079/0001093557-24-000079-index.htm
- Structured rendering: https://www.sec.gov/Archives/edgar/data/1093557/000109355724000079/R18.htm

**CarGurus — adoption, termination, dollar amounts and gross/net mismatch**

The filing lists three new sell plans: 30,000 shares for CEO Jason Trevisan, 50,757 gross future-award shares for CTO Matthew Quinn, and 22,808 gross future-award shares for General Counsel Javier Zamora. Quinn's plan sells 40% of net shares vesting; the disclosed 50,757 is gross before tax withholding. The same filing reports termination of Quinn's prior December 5, 2023 plan, described as $45,000 in shares to be sold. The termination is a lifecycle event and must not be counted as another active plan or converted into a share count.

- Filing index: https://www.sec.gov/Archives/edgar/data/1494259/000095017024056957/0000950170-24-056957-index.htm
- Structured rendering: https://www.sec.gov/Archives/edgar/data/1494259/000095017024056957/R10.htm

**Powell Industries — explicit future sale windows**

The filing reports two plans: CFO Michael W. Metcalf, up to 10,100 shares with a disclosed window beginning June 7, 2024; and CEO Brett A. Cope, up to 11,000 shares with a disclosed window beginning June 14, 2024. These explicit starts are more informative than inferring an execution date solely from the adoption date or a generic cooling-off rule. They still describe permitted/expected plan windows, not proof of execution.

- Filing index: https://www.sec.gov/Archives/edgar/data/80420/000008042024000030/0000080420-24-000030-index.htm
- Structured rendering: https://www.sec.gov/Archives/edgar/data/80420/000008042024000030/R20.htm

**Celanese — purchase is not sale supply**

The 10-K's table has separate aggregate-share columns for purchases and sales. Scott A. Richardson's 4,000-share plan appears in the purchase column, with a disclosed transaction window from March 14 through June 28, 2024. A pipeline that treats every Item 408 quantity as a sale would invert this observation.

- Filing index: https://www.sec.gov/Archives/edgar/data/1306830/000130683024000029/0001306830-24-000029-index.htm
- Structured rendering: https://www.sec.gov/Archives/edgar/data/1306830/000130683024000029/R34.htm

**General Mills — option exercise and sale**

CEO Jeffrey L. Harmening's plan covers exercise and sale of up to 57,879 shares subject to a company-granted stock-option award. The quantity is therefore not equivalent to a sale of 57,879 already-owned common shares; the underlying award and exercise mechanics matter.

- Filing index: https://www.sec.gov/Archives/edgar/data/40704/000119312524221344/0001193125-24-221344-index.htm
- Filing: https://www.sec.gov/Archives/edgar/data/40704/000119312524221344/d874379d10q.htm

## Normalization results

The reproducible casebook/analyzer reports:

- 6 issuer filings.
- 12 plan actions: 11 adoptions and one termination.
- Direction classes: 9 sell, 1 buy, 1 exercise-and-sell, 1 unknown.
- Amount units: 11 share-denominated records and one USD-denominated record.
- 3 actions with an explicit scheduled transaction-window start date.
- 9 share-denominated records have a basis other than a plain stated share ceiling (for example gross future awards, conditional vesting, purchase column, option exercise or unresolved direction).

**No aggregate share total is produced.** A USD amount, purchase plan, exercise-and-sell award, gross pre-tax award quantity, conditional net vesting and unresolved direction are not interchangeable.

## Required data model changes before any signal test

1. Keep `action` separate from `direction`: adopt, modify and terminate are lifecycle events; buy, sell, exercise-and-sell and unknown describe transaction semantics.
2. Preserve raw narrative/table text and original ECD facts. Do not infer direction from `TrdArrSecuritiesAggAvailAmt` alone.
3. Preserve amount value, unit and basis separately. Never sum USD and shares or gross awards and net shares.
4. Keep direct, indirect and trust relationships separate; do not assume a trust is the named officer's personal account.
5. Keep option exercise/vesting, tax withholding, pricing triggers and future award contingencies explicit.
6. Preserve explicit scheduled start/earliest-sale dates where disclosed, but do not treat them as proof of execution.
7. Maintain plan lifecycle by person + issuer + plan identity. A termination must close or supersede the relevant prior plan state only when linkage is established; do not count it as a new sell signal.
8. Use SEC filing acceptance plus a conservative next-session boundary unless a validated first-public-receipt timestamp exists. Filing acceptance is not itself certified first public receipt.
9. Validate all plan records against subsequent Form 4 footnotes and Form 144 where applicable, while using those later records only as retrospective reconciliation—not as same-day signal inputs.

## Admission decision

| Gate | Result |
|---|---|
| Six-issuer schema/semantics stress sample | PASS |
| Direction classification | PARTIAL; one unresolved case retained as unknown |
| Lifecycle action separation | PASS for this sample |
| Amount-unit/basis preservation | PASS in normalized casebook |
| Historical / frozen-335 universe coverage | NOT TESTED |
| Full EDGAR first-public-receipt history | NOT ESTABLISHED |
| Person-to-issuer historical identity | NOT ESTABLISHED |
| Plan amendments/cancellations and full lifecycle | NOT ESTABLISHED |
| Form 4 / Form 144 execution reconciliation across all six | NOT RUN |
| Return impact / incremental value vs LTM/F80 | NOT TESTED |
| OOS / bootstrap / LOO / holdout | NOT RUN |

**Decision:** retain Item 408 as a conditional potential-supply and plan-activity source, but do not admit a signal. The cross-issuer audit demonstrates that a naive “shares in 10b5-1 plan = future selling” feature would contain direction errors, lifecycle errors, unit errors and award/withholding errors.

No stock-return data was acquired or tested. No signal was admitted. No trading code, F80 baseline, universe, holdout, capital, exposure or production configuration was changed.

## Reproducibility

- Casebook: `research/PHASE436_ITEM408_CROSS_ISSUER_SEMANTICS_CASEBOOK_2026-11-16.json`
- Analyzer: `research/phase436_item408_cross_issuer_semantics.py`
- Tests: `research/test_phase436_item408_cross_issuer_semantics.py`
- Regression workflow: existing `.github/workflows/phase433_item408_ixbrl_parser.yml` extended; no new workflow or live capture was created.
