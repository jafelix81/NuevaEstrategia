# Phase 264 — FINRA ATS final live-artifact adjudication

**Date:** 2026-11-10  
**Status:** completed artifact adjudication; source remains **not admitted** for strict PIT or alpha.  
**Scope:** inspect and reconcile the corrected Phase 100 FINRA live run that the preliminary Phase 107 note still described as in progress. No new API pull, return test, vendor contact, purchase, production change or universe change.

## 1. Execution and artifact

The corrected live revalidation did finish successfully:

- [GitHub Actions run 41978867803](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41978867803)
- Job `revalidation`: `127084556636`, conclusion `success`
- [Artifact 13394110956](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41978867803/artifacts/13394110956)
- Artifact ZIP SHA-256: `803c58a5301df8b505b487c5367a449696c6bc467cab39121c50eda762d1f3e9`

I downloaded the artifact and independently recomputed the ZIP digest; it matches GitHub's artifact digest. The four extracted files also have pinned SHA-256 values in the accompanying result JSON.

The workflow used synchronous pagination and completed with `FINRA_API_TOKEN` absent. This corrects the earlier implication that a FINRA token was blocking this particular public historical endpoint. It does not establish access or licensing for every FINRA dataset or use case.

## 2. Actual sample and coverage

Ten of ten requested partitions completed across five historical weeks and two NMS tiers.

| Measure | Result |
|---|---:|
| Total rows | 968,139 |
| T1 rows | 269,163 |
| T2 rows | 698,976 |
| Page-hash records / unique request IDs | 199 / 199 |
| API Record-Total reconciliations | 10/10 |
| Invalid or negative quantity fields | 0 |
| Symbol-level aggregate rows | 108,444 |
| Initial publication date non-null | 100.0% |
| Rows with lastUpdateDate later than initialPublishedDate | 1,882 (1.735%) |

Median initial-publication lag was 21 calendar days for T1 and 35 for T2 in these five sampled weeks. The 335-name overlap values (94.63%–99.10% by week) are legacy comparability diagnostics only; the manually selected 335 names are not a representative universe and these percentages are not broad-market coverage.

## 3. Two row-integrity errors

The 2022-01-03 T2 partition contains two symbol-bearing rows without `issueSymbolIdentifier`:

- Row 103583: `OTC_W_SMBL_FIRM`
- Row 115658: `OTC_W_SMBL`

Both rows remain errors and must be quarantined. They are not zero activity and cannot be assigned to a security.

A nuance in the Phase 100 result: the field named `exact_requested_week_and_tier` is false because the implementation combines row-level symbol validation with its no-partition-errors boolean. The recorded examples are missing-symbol errors; the artifact does not report an incorrect `weekStartDate` or `tierIdentifier` value.

## 4. Two conflicting LND aggregate-key groups

The 2025-01-06 T2 partition contains two conflicting duplicate groups for LND, product type CTS:

| Summary type | Shares / trades | lastReportedDate | initialPublishedDate / lastUpdateDate |
|---|---:|---|---|
| ATS_W_SMBL | 6,224 / 37 | 2025-01-10 | 2025-02-10 / 2025-02-10 |
| ATS_W_SMBL | 5,226 / 144 | 2025-01-08 | 2025-02-10 / 2025-02-10 |
| OTC_W_SMBL | 28,543 / 137 | 2025-01-10 | 2025-02-10 / 2025-02-10 |
| OTC_W_SMBL | 67,210 / 320 | 2025-01-08 | 2025-02-10 / 2025-02-10 |

The Phase 100 duplicate key omitted `lastReportedDate`. Adding that field mechanically separates both pairs, but the official FINRA schema does not declare it a primary or natural key. FINRA describes it as the last time a firm sent an update to underlying data contributing to the aggregate. That definition alone does not establish whether the rows are independent contributions, alternative aggregate vintages or a data-quality defect.

**Decision:** do not choose the later date, sum the rows, or silently deduplicate them. Preserve both rows as unresolved until the source semantics are confirmed.

## 5. Publication revisions and PIT

The publication gate passed: every sampled symbol aggregate had a non-null `initialPublishedDate`, and no observed initial publication was earlier than the minimum delay check.

That does **not** establish strict PIT. 1,882 of 108,444 symbol-level aggregate rows (1.735%) have `lastUpdateDate` later than `initialPublishedDate`. The artifact contains the current historical values, not the immutable value as first published. A conservative availability date of `max(initialPublishedDate,lastUpdateDate)`, followed by next-session execution, can prevent using a current revised value too early; it cannot reconstruct the earlier value vintage.

FINRA's official Weekly Summary documentation says the historic dataset is a rolling four-year window beginning one year before the current date and that data older than one year is static. It also defines `lastReportedDate` as the last time a firm sent an update to underlying data contributing to the aggregate. See [FINRA Developer Center — Weekly Summary](https://developer.finra.org/docs), section “Weekly Summary”.

## 6. Final disposition

| Gate | Result |
|---|---|
| All 10 API Record-Total counts reconcile | PASS |
| Nonnegative quantities | PASS |
| Symbol aggregates present in all sampled week/tier partitions | PASS |
| Initial publication date / delay check | PASS |
| Missing-symbol row integrity | FAIL |
| Conflicting duplicate aggregate keys | FAIL / REVIEW |
| Strict historical value vintages | NOT PROVEN |
| Effective-dated security identity | NOT ADMITTED |
| Forward-return / alpha admission | NOT AUTHORIZED |

FINRA weekly ATS/non-ATS remains a **conditional off-exchange activity/context source**, not a “smart money” signal. It does not identify aggressor direction, beneficial owner or informed trader. No feature construction or return test is authorized.

The next useful work is narrow: preserve the two missing-symbol rows and both LND pairs as explicit exceptions, establish the documented natural grain or obtain FINRA clarification, and obtain immutable first-publication/revision vintages plus point-in-time security identity before any economic test. Do not repeatedly download weeks that FINRA documents as static after one year.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. The legacy holdout remains `CONSUMED_NOT_PRISTINE` and unused.
