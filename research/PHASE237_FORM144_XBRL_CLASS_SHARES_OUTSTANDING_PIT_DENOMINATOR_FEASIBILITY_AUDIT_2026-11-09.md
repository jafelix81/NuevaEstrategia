# Phase 237 — Form 144 class-specific shares-outstanding denominator: SEC XBRL API scope and PIT feasibility audit

**Audit date:** 2026-11-09  
**Disposition:** `RAW_INLINE_XBRL_REQUIRED_FOR_MULTI_CLASS_SHARES`; `COMPANYFACTS_ONLY_PATH_INSUFFICIENT`; Form 144 denominator and alpha remain **NOT ADMITTED**.  
**Scope:** SEC documentation and source-example audit, normalized-fact guardrails, and as-filed/PIT rules. No raw filing download, SEC API request, coverage census, forward-return test, holdout use, purchase, or production change.

## Executive result

Phase 223 established that Form 144's filer-entered `units_outstanding` is not a reliable denominator. Phase 237 identifies a feasible independent source path for **total shares outstanding by class**: parse the original issuer filing's inline XBRL cover-page facts, rather than relying only on the SEC Company Facts API.

The SEC API documentation says Company Facts aggregates non-custom-taxonomy facts that apply to the entire filing entity. The SEC EDGAR XBRL Guide says `dei:EntityCommonStockSharesOutstanding` is an instant fact and, when an issuer has multiple common-stock classes, it is reported in separate class-dimensioned contexts using `StatementClassOfStockAxis` or `ClassesOfShareCapitalAxis`. Taken together, those rules mean Company Facts cannot be treated as a complete source for multi-class, class-specific share counts: the relevant dimensioned facts do not satisfy its entity-wide aggregation scope.

**Decision:** use Company Facts only as a candidate shortcut for proven single-class entity-wide facts. For multi-class issuers, retrieve the as-filed 10-K/10-Q/other relevant filing and parse the inline XBRL instance, preserving dimensions, member QNames, context dates, accession, filing/acceptance time and every amendment as a separate vintage.

This is a source-path feasibility result, not a measured coverage result. No Form 144 denominator is admitted yet.

## 1. Official SEC data/API scope

The SEC's EDGAR API documentation states:

- Company Facts includes XBRL facts from non-custom taxonomies such as US-GAAP, IFRS, DEI and SRT.
- The facts must apply to the entire filing entity.
- The submissions and XBRL APIs update as filings are disseminated; the SEC describes typical processing delays of under one second for submissions and under one minute for XBRL, with longer delays possible at peak times.
- The bulk ZIP files are republished nightly, approximately 3:00 a.m. ET.

This is useful for as-filed history, but the entity-wide restriction is material for class-specific denominators.

Source: [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).

## 2. SEC XBRL Guide: class shares are dimensioned

The July 2025 EDGAR XBRL Guide, section 3.2.3, specifies:

- Concept: `dei:EntityCommonStockSharesOutstanding`.
- Period type: instant, not duration.
- Zero or one common class: one fact in the required context, without dimensions.
- More than one common class: at least two facts in distinct contexts, dimensioned by either `StatementClassOfStockAxis` or `ClassesOfShareCapitalAxis`.
- The dimensioned cases require the accompanying custom taxonomy.
- The common-shares fact is in a subsequent-event instant context whose date is on or after the end of the required context.

Consequences for our parser:

1. Preserve the full axis and member QName; do not reduce a member to a ticker or fuzzy class string.
2. A multi-class fact set must contain at least two distinct class members on one supported axis.
3. Resolve the Form 144 security class to one exact XBRL member. If the mapping is missing or ambiguous, the denominator is UNKNOWN.
4. Do not sum class counts and assign the total to one listed class.
5. A no-dimension fact is usable for a class-specific denominator only when one common class is independently established.

Source: [SEC EDGAR XBRL Guide, July 2025](https://www.sec.gov/files/edgar/filer-information/specifications/xbrl-guide-2025-07-10.pdf), §3.2.3.

## 3. Primary-document examples

### Noodles & Company — amendment changes a class count

The 2015 Form 10-Q/A states that the original 10-Q cover page incorrectly reported 29,994,302 Class A shares because it included 1,522,098 Class B shares. The amendment corrects Class A to 28,472,204 and re-files the XBRL exhibit.

This is a concrete reason not to overwrite history with the latest value. A correction filed after a Form 144 event must update the denominator only from the amendment's own public-availability date; it cannot rewrite what was knowable before the amendment.

Source: [Noodles & Company 2015 Form 10-Q/A](https://www.sec.gov/Archives/edgar/data/1275158/000127515815000046/q1201510qa.htm).

### Flowco — separate class counts in a current filing

A 2026 Form 10-Q/A cover page reports 41,824,162 Class A shares and 48,521,254 Class B shares as of May 1, 2026. The filing explains that the amendment corrected certification language and did not otherwise update the original report. Its inline-XBRL page exposes the two class members in the hidden cover-page facts.

This illustrates why a single issuer-wide number is not a safe substitute for the listed class.

Source: [Flowco 2026 Form 10-Q/A](https://www.sec.gov/Archives/edgar/data/2035149/000119312526294682/floc-20260331.htm).

### Expedia — existing Phase 223 denominator contradiction

Phase 223 already documented an Expedia Form 144 that reported 1,775 common shares outstanding, while the latest prior 10-K disclosed 117,011,421 common shares and 5,523,452 Class B shares. This remains a primary-document cross-check, not a reason to rescale the Form 144 value.

See [Phase 223](PHASE223_FORM144_UNITS_OUTSTANDING_DENOMINATOR_INTEGRITY_AUDIT_2026-11-08.md).

## 4. Public float, shares outstanding and ADV are not interchangeable

The SEC XBRL Guide treats `dei:EntityPublicFloat` separately from common shares outstanding. Public float is a market-value fact, not a share-count fact. ADV is traded share volume. They answer different questions:

- **Class shares outstanding:** total issued/outstanding shares of the exact class.
- **Public float:** market value of common equity held by non-affiliates; it is not a count of freely tradable shares.
- **ADV:** average daily trading volume; it is not shares outstanding or float.

The only ratio this phase permits as a descriptive field is `proposed_units / class_shares_outstanding`, labelled as a proposed-to-total-shares ratio. It must not be called float pressure, market supply, or an executable sale fraction. A real supply-pressure feature still needs independently measured PIT float/ADV and evidence about completed sales.

## 5. Daily PIT and amendment rules

Phase 222 established a conservative daily Form 144 event clock: a notice filed on date D is usable only from the first XNYS session strictly after D; no same-day use. The same conservative date-level convention can be used for an issuer denominator filing:

- retain filing date, accession, acceptance datetime when available, fact end date, taxonomy, axis/member, value and raw-file hash;
- a share fact is eligible only if its filing date is on or before the Form 144 filing date and its instant fact date is not after the filing date;
- preserve each 10-K/A, 10-Q/A and other filing as a separate as-filed vintage;
- an amendment accepted after the Form 144 event cannot alter the earlier denominator;
- if two conflicting versions are filed on the same date and no acceptance ordering is available, return UNKNOWN;
- a later malformed or conflicting share fact must block silent fallback to a stale earlier value;
- execute the event study no earlier than the close of the first XNYS session after the Form 144 filing date, consistent with the project's end-of-day discipline.

This is a daily rule only. It does not authorize intraday use.

## 6. Fail-closed normalized-fact contract

Added an offline resolver that accepts normalized filing facts and rejects:

- wrong concept or unit;
- duration contexts;
- missing/invalid instant or filing dates;
- facts dated after their filing;
- negative or fractional share counts;
- missing accessions;
- unsupported/multiple dimensions;
- incomplete multi-class member sets;
- class-count mismatch or missing exact member mapping;
- conflicting same-day vintages without acceptance ordering;
- stale fallback when a newer as-of fact is invalid.

The resolver explicitly distinguishes entity-wide single-class facts from exact class-dimensioned facts. Its current prototype accepts the two US-GAAP axis QNames documented in the sample; other standard-taxonomy namespaces are not yet admitted and must be quarantined until explicitly supported. It does not fetch or parse raw inline XBRL and does not infer the number of issuer classes from tickers.

Local validation: **21/21 standard-library regression tests passed**, including amendment-as-of, multi-class, companyfacts-scope, unknown-vs-zero, and denominator non-substitution cases. These are fixture tests, not SEC raw-filing integration tests or hosted CI.

## 7. Admission gates

| Gate | Result |
|---|---|
| Official Company Facts aggregation scope | PASS |
| Official DEI common-shares concept and instant semantics | PASS |
| Official multi-class dimension rules | PASS |
| Raw inline-XBRL path identified | PASS |
| Amendment/as-filed PIT rule specified | PASS |
| Offline normalized-fact guardrails | PASS — 21/21 |
| Raw multi-class XBRL parser validated against filings | NOT TESTED |\n| Non-US-GAAP standard class axes supported | NOT TESTED / QUARANTINE |
| Company Facts vs raw-filing omission measured | NOT MEASURED |
| Class-member-to-Form-144 security mapping | NOT ESTABLISHED |
| Coverage across 289 Form 144 issuer CIKs | NOT MEASURED |
| Inactive/delisted/security-class continuity | NOT ESTABLISHED |
| Independent PIT public-float shares and ADV | NOT ESTABLISHED |
| Form 144 denominator admitted | NO |
| Alpha / forward-return test authorized | NO |

## 8. Next work

1. Build a representative raw-filing pilot across single-class, dual-class, ADR, foreign issuer, amended filing and inactive/delisted issuer cases.
2. Retrieve original filing index/headers and inline-XBRL bytes; hash each accession and retain amendments separately.
3. Parse the DEI common-shares facts with exact context/axis/member QNames and reconcile them to the visible cover page.
4. Compare the raw filing facts with Company Facts to measure exactly which multi-class cases are omitted from the entity-wide API.
5. Map Form 144 class text to registered-security title, ticker, exchange and exact XBRL member using filing evidence; quarantine unresolved classes.
6. Measure usable denominator coverage across the 289 issuers in the existing Form 144 panel and separately quantify single-class versus multi-class attrition.
7. Keep shares outstanding, public float and ADV separate. If coverage is weak, archive the denominator feature rather than substituting an issuer-wide or later value.

No returns, alpha, bootstrap/LOO, chronological OOS or holdout test was run. No SEC data API request or raw filing download was made in this phase. No vendor was contacted, no data purchased, no production/universe change made. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; the legacy holdout remains `CONSUMED_NOT_PRISTINE`.

## Repository artifacts

- [Auditor](phase237_form144_xbrl_class_shares_pit_audit.py)
- [Tests](test_phase237_form144_xbrl_class_shares_pit_audit.py)
- [Machine result](phase237_form144_xbrl_class_shares_pit_audit_result.json)
- [Current research state](SMART_MONEY_RESEARCH_CURRENT_STATE_2026-11-09.md)
