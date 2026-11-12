# Phase 314 — Otter Creek N-PORT amendment parent audit

**Date:** 2026-11-12 UTC  
**Workflow:** [run 43160951691](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43160951691) — PASS  
**Artifact:** [13917229995](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43160951691/artifacts/13917229995)  
**Artifact SHA-256:** `ec1a61d1172350778b9da1d4ef0e49f25a6279c1b3b328747992fdccc92ebe2b`

## Scope and parent-candidate result

The audit examined the complete 2022 Q3 NPORT-P filing cohort for registrant CIK `0000811030` (Professionally Managed Portfolios): **25 original NPORT-P filings** filed before the target amendment.

The target amendment was accession `0001145549-22-060851`, filed 2022-10-03, for report date 2022-07-31 and series `S000043717` (Otter Creek Long/Short Opportunity Fund). Exactly one earlier NPORT-P candidate met all available metadata conditions:

- accession `0001145549-22-059178`, filed 2022-09-28;
- same registrant CIK, report date, series ID and exact series name;
- class-contract IDs matched the amendment;
- original NPORT-P form and earlier filing date.

This is a **unique metadata parent candidate**, not an authoritative accession-to-accession foreign key. The SEC submission header does not supply a direct original-accession reference in this case.

## Short-position vintage comparison

The original filing and the 2022-10-03 amendment each contain 20 sign-concordant rows satisfying the audited common-equity short-position filter. The comparison is exact:

| Original vs. amendment | Rows |
|---|---:|
| Original rows | 20 |
| Amendment rows | 20 |
| Unchanged | **20** |
| Modified | 0 |
| Added | 0 |
| Removed | 0 |

A same-series NPORT-P control, accession `0001145549-23-060491`, was filed 2023-09-29 for report date 2023-07-31 and contains 27 qualifying rows. Comparing the 2022 amendment snapshot with this 2023 snapshot gives 23 added, 4 modified, 16 removed and 0 unchanged rows.

These are differences between two delayed portfolio snapshots one year apart. They are **not trade records**, cannot identify execution dates, and do not establish that the fund initiated or covered a position at any particular time.

## Descriptive exposure (not a signal)

| Snapshot | Qualifying rows | Sum of absolute reported `valUSD` | Sum of absolute reported `pctVal` |
|---|---:|---:|---:|
| 2022 original | 20 | $49,202,870.08 | 25.6799 percentage points |
| 2022 amendment | 20 | $49,202,870.08 | 25.6799 percentage points |
| 2023 same-series control | 27 | $46,452,054.22 | 32.8880 percentage points |

These aggregates describe the reported short-position rows only. They are not gross fund leverage, a market-wide short-interest measure, or a return series.

## Cohort finding and limits

Only **1 of the 25** NPORT-P filings in this one-registrant/one-quarter cohort contained the audited short-position rows (20 rows). This is a complete cohort for that registrant and quarter, not a representative sample of funds or the market. It must not be used as a prevalence estimate.

The report-date-to-filing-date delays are 59 calendar days for the original, 64 days for the amendment and 60 days for the 2023 control. Report date is not the public-availability date; acceptance time is not independently proven to be first public receipt. No effective-dated security master or frozen-F80 coverage join was performed.

## Decision

- Keep N-PORT in the **delayed holdings-context** category, not trade flow.
- Preserve the unique parent as a high-confidence metadata candidate, not an authoritative link.
- Do not infer transactions from added/removed positions between annual snapshots.
- Expand to multiple registrants and quarters only with a documented sampling design, amendment-vintage handling and effective-dated CUSIP/ISIN security identity.

No alpha, return, bootstrap, LOO or OOS test was run. No holdout was used. F80, production, universe, capital and parameters were unchanged.
