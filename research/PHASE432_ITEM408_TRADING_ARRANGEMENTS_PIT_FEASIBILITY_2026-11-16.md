# Phase 432 — Item 408 trading-arrangement PIT feasibility audit (2026-11-16)

## Executive decision

**Decision: CONDITIONAL DATA-FEASIBILITY PASS; NOT ADMITTED FOR ALPHA.**

Item 408(a) is a credible, low-cost, structured SEC source for *publicly disclosed future insider trading arrangements*. It can identify Rule 10b5-1 and non-Rule 10b5-1 plans adopted or terminated by directors and officers, with adoption/termination dates, duration/expiration, aggregate shares and narrative terms. A real 2023 Form 10-Q confirms that the SEC's ECD tags are present in filing-level Inline XBRL and can be available before the amended Rule 10b5-1 cooling-off period expires.

It is not a long-history source, does not cover all Section 16 reporting persons, does not reveal exact execution dates/prices, and does not identify beneficial owners by CIK. Its use must be strictly point-in-time at the filing's EDGAR acceptance timestamp. No alpha, OOS or holdout test was run and no signal was admitted.

## 1. Regulatory scope and historical start

The SEC's final rule (Release 33-11138 / 34-96492) became effective on **2023-02-27**. Section 16 filers had to comply with the amended Forms 4/5 for beneficial-ownership reports filed on or after **2023-04-01**. Item 408(a) periodic-report compliance began with the first full fiscal period starting on or after **2023-04-01** for issuers other than smaller reporting companies (SRCs), and on or after **2023-10-01** for SRCs.

Item 408(a) requires a domestic registrant to disclose in its quarterly Form 10-Q (and fourth-quarter Form 10-K) whether a director or Rule 16a-1(f) officer adopted or terminated during the fiscal quarter:
- a Rule 10b5-1(c) trading arrangement; and/or
- a non-Rule 10b5-1 trading arrangement as defined in Regulation S-K Item 408(c).

The material-terms disclosure includes the individual's name/title, adoption or termination date, duration and aggregate securities to be purchased or sold. Price terms are not required. The rule does **not** extend Item 408(a) to all Section 16 filers: the SEC expressly declined to extend this disclosure to insiders other than officers and directors. It applies to arrangements covering securities in which the officer/director has a direct or indirect pecuniary interest reportable under Section 16 and which that person decided to adopt or terminate.

Item 408(a) applies to domestic filers. Foreign private issuers, MJDS issuers and registered investment companies are not subject to Regulation S-K Item 408(a). Coverage is therefore structurally narrower than Form 4.

Important interpretation:
- A plan that ends by its own expiration or completion does **not** require an Item 408(a) termination disclosure (SEC C&DI 133A.01).
- A missing termination record is not evidence that a plan remains active.
- A missing Item 408 fact is not equivalent to a false flag or to no plan.
- Covered modifications to a Rule 10b5-1 plan are treated as termination of the existing plan and adoption of a new plan when they meet the amended Rule 10b5-1(c)(1)(iv) definition. Preserve both sides as a versioned event; do not silently overwrite the prior plan.

### Historical coverage gate

For calendar-year issuers, the expected first Item 408(a) quarter is Q2 2023 for non-SRCs and Q4 2023 for SRCs. Fiscal-year issuers must be classified by their own first full fiscal period. The public history can therefore begin in 2023, not 2006. As of the SEC page's latest listed quarter (2026 Q3), the source offers only roughly 3–3.5 years of potential history, with staggered issuer starts.

This is too short to support a standalone long-history OOS claim. It is adequate to build a prospective event ledger and conduct carefully bounded exploratory work once issuer/person coverage is measured.

The SEC's Insider Transactions Data Sets page states that the bulk datasets cover January 2006–September 2026, are quarterly and as-filed, and that the 2023–2025 datasets were updated in July 2025 to include AFF10B5ONE in SUBMISSION. The exact 2023 Q2/Q3 ZIP bytes were not independently downloaded and hash-verified in this phase; the official page is evidence of the update, not a substitute for that byte-level vintage audit.

## 2. Structured data feasibility: ECD Inline XBRL

The SEC's Executive Compensation Disclosure (ECD) taxonomy guide defines the Item 408(a) table and its dimensions:
- `ecd:IndividualAxis` — distinguishes each director/officer;
- `ecd:TradingArrAxis` — distinguishes multiple arrangements for the same person;
- `ecd:MtrlTermsOfTrdArrTextBlock`;
- `ecd:TrdArrIndName`, `ecd:TrdArrIndTitle`;
- `ecd:Rule10b51ArrAdoptedFlag`, `ecd:NonRule10b51ArrAdoptedFlag`;
- `ecd:TrdArrAdoptionDate`;
- `ecd:Rule10b51ArrTrmntdFlag`, `ecd:NonRule10b51ArrTrmntdFlag`;
- `ecd:TrdArrTerminationDate`;
- `ecd:TrdArrExpirationDate` (standard element in the 2024 ECD taxonomy);
- `ecd:TrdArrDuration`;
- `ecd:TrdArrSecuritiesAggAvailAmt`.

A 2023 SEC filing provides a real implementation check. NOW Inc.'s 10-Q for the quarter ended 2023-09-30 (CIK 1373715, accession 0001373715-23-000419) was accepted **2023-10-25 19:20:50 UTC**. Its Inline XBRL includes the standard ECD tags, individual names/titles, Rule 10b5-1 adoption flags, adoption dates, share amounts and narrative text. The filing describes:
- CEO William R. McDermott's plan adopted 2023-08-31, with sales of 30,489 common shares plus net shares resulting from 9,986 additional gross shares, and a stated expiration of 2025-02-18;
- director Paul E. Chamberlain's plan adopted 2023-08-21 for 540 common shares, with stated expiration 2024-09-03.

For these two Rule 10b5-1 examples, 90 days after adoption is 2023-11-29 and 2023-11-19 respectively. The 2023-10-25 filing acceptance therefore precedes those dates by 35 and 25 calendar days. This demonstrates a *possible* ex-ante disclosure window for a particular filing; it does not establish that every Item 408 filing precedes the first plan trade. Plans adopted early in a fiscal quarter can reach the 90-day point before the quarter's 10-Q is accepted.

The SEC ECD guide notes that Item 408 facts can use both Individual and Trading Arrangement dimensions. The parser must preserve contextRef, both dimensions, units, filing accession and fact-level identity. Some facts may be in Inline XBRL hidden sections; a FilingSummary example reports ECD facts in `ix:hidden`. Do not scrape only the rendered narrative table or discard hidden tagged facts.

## 3. Correct PIT clock and versioning

The only admissible public-availability timestamp is the filing's EDGAR acceptance timestamp (first public receipt), not:
- the plan adoption/termination date;
- the fiscal-quarter end;
- the filing date shown without a time;
- a later bulk-data publication date.

For every 10-Q/10-K version, persist accession, issuer CIK, form, period end, amendment flag, acceptance timestamp, source URL, raw-file hash, taxonomy/version metadata and extracted facts. A 10-Q/A is a new knowledge event/version; never rewrite the original record. The event is available only from its own acceptance time.

For Rule 10b5-1 plans adopted by directors/officers under the amended affirmative-defense conditions, the cooling-off period is the later of 90 days after adoption or two business days after disclosure of the issuer's financial results for the fiscal quarter in which the plan was adopted, and may not exceed 120 days after adoption/modification. This is a condition of relying on the affirmative defense, not a universal statutory prohibition on every insider trade. The actual first trade can be earlier if the plan does not qualify for that defense. Therefore, compute the rule-based earliest eligible date as a feature/diagnostic, but never assume that it proves when trading began.

At a given historical decision time, use only the latest Item 408 version accepted by that time. If a filing arrives after the first eligible trade date, mark the plan as already potentially active at disclosure; do not backdate the information to adoption. If it arrives before that date, it may be a genuinely prospective plan-disclosure event.

## 4. Identity, quantity and semantic risks

Item 408 identifies the person by name and title, not by a stable Section 16 owner CIK. The issuer CIK is available in the filing, but the individual-to-Form-4 owner bridge remains a separate task. Match on issuer CIK plus normalized person name, preserve aliases and titles, and use Form 4 owner CIK where independently established. Fuzzy name matching alone is not sufficient for alpha admission.

The aggregate securities amount is not an execution forecast. It may describe maximum shares, net shares after withholding, multiple award components or separate arrangements. Multiple facts can be reported under different contexts/dimensions. Never sum all facts for an individual without grouping by the TradingArrAxis member and inspecting the narrative. Price terms and exact trade schedules are not required.

Rule 10b5-1 and non-Rule 10b5-1 arrangements must remain separate. The latter are pre-arranged trading schedules but do not represent a Rule 10b5-1 affirmative-defense plan. A Form 4 AFF10B5ONE flag is accession/filing-level, not transaction-row-level; it is a complementary confirmation, not a substitute for Item 408 plan identity or per-row adjudication.

## 5. Candidate research questions (not yet tests)

Only after extraction, issuer coverage and person-linkage pass their gates, preregister these as separate hypotheses:

1. **Future disclosed supply:** Does the amount of planned sales, scaled by point-in-time shares outstanding and 20-day ADV, predict subsequent supply pressure or returns after the disclosure acceptance timestamp?
2. **Plan adoption vs termination/modification:** Do adoption and voluntary termination/modification events contain different information? Do not label natural expiry/completion as a termination event.
3. **Rule vs non-Rule arrangements:** Are their subsequent execution patterns or return associations different after controlling for size, insider role, liquidity, volatility, earnings timing and momentum?
4. **Disclosure lead:** Does a filing accepted before the rule-based earliest eligible date behave differently from a filing accepted after that date?
5. **Incremental value:** Does any feature add information beyond frozen LTM/F80 and existing Form 4/Form 144 information?

Any future test must use identical exposure and costs, strict chronological training/validation/OOS, point-in-time issuer/security mappings, bootstrap blocks and LOO. Test multiple horizons without imposing a holding-period constraint. Separate the plan-adoption date (economic event date) from the disclosure-acceptance date (information date). No signal may be promoted on the strength of the SEC's regulatory rationale or a single illustrative filing.

## 6. Admission decision and next work

| Gate | Decision |
|---|---|
| Official public source / reproducibility | PASS, SEC EDGAR filing-level iXBRL |
| Structured schema | PASS, standard ECD tags and dimensions |
| Ex-ante availability | CONDITIONAL PASS; must compare each acceptance time with plan eligibility/trade timing |
| Historical depth | LIMITED; staggered start in 2023, not enough for long-history standalone OOS |
| Universe coverage | UNMEASURED; domestic issuers only, directors/officers only |
| Person identity bridge | FAIL / unresolved pending deterministic mapping |
| Plan status completeness | LIMITED; natural expiry/completion need not be disclosed |
| Alpha/OOS admission | NOT AUTHORIZED |

Next:
1. Build a small filing-level parser with raw-iXBRL fixtures that preserves IndividualAxis and TradingArrAxis, including hidden facts and amendments.
2. Census Item 408 facts across a stratified set of 2023Q2/Q3, 2023Q4, 2024, 2025 and 2026 filings; record actual first acceptance timestamps and missing/false/unknown states.
3. Measure coverage against the frozen 335-name universe using effective-dated CIK/security mapping; separately report domestic/SRC/FPI eligibility and director/officer event density.
4. Link plan persons to Form 4 owners only with auditable match grades.
5. Build a prospective raw filing ledger before any alpha work.

No data were purchased. No production workflow, trading code, universe, parameters, holdout, capital or exposure policy was changed. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Sources

- SEC Insider Transactions Data Sets: https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
- SEC Final Rule 33-11138 / 34-96492: https://www.sec.gov/files/rules/final/2022/33-11138.pdf
- SEC ECD Taxonomy Guide (2026): https://xbrl.sec.gov/ecd/2026/ecd-taxonomy-guide-2026-03-16.pdf
- SEC Regulation S-K C&DI 133A.01–133A.02: https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/regulation-s-k
- Illustrative NOW Inc. 2023 Q3 10-Q XBRL instance: https://www.sec.gov/Archives/edgar/data/1373715/000137371523000419/now-20230930_htm.xml
- Filing directory / acceptance timestamp: https://www.sec.gov/Archives/edgar/data/1373715/000137371523000419/
