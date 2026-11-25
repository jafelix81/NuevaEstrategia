# Phase 618 — Form 144 / Form 4 acceptance-clock reconciliation audit

**Audit cutoff:** 2026-11-25 11:11 UTC  
**Base:** `main` at `d163d1d7e4074b558c7282be50a42208727c9c97`  
**Disposition:** descriptive reconciliation hardening; no signal admission.

## 1. Preflight

The latest 100 Actions runs were inspected before changes. No queued, in-progress, waiting or requested runs were present. The latest successful Form 144 scheduled run was [45595957832](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45595957832); the latest successful Form 4 scheduled run remained [45533818624](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45533818624).

The Form 4 workflow state on `main` still points to run 45533818624, with last successful poll end `2026-11-25T02:34:18Z`. No later Form 4 schedule event was present in the latest 100 Actions runs at the audit cutoff. The workflow YAML still declares `17 * * * 1-5`. This is an observed schedule-delivery gap, not proof of administrative disablement. No manual dispatch, rerun, cron change or replacement poller was used.

## 2. Source artifacts inspected

### Form 4 — run 45533818624, artifact 14986800169

- 593 new accession metadata observations; both Form 4 and Form 4/A watermark gates passed.
- 10 bounded accessions parsed into 24 transaction-detail rows; zero parse errors.
- 10 filing-level owner enrichments appended; 20 bounded owner accessions remain.
- Strict Form 144/Form 4 crosswalk: 10 proposed-sale rows plus one prior-sale-history row across 9 Form 4 accessions.
- Zero signal-eligible rows; public availability and transaction-line owner attribution are not certified.

### Form 144 — run 45595957832, artifact 15013625637

- 53 feed-observation rows; 50 Form 144 and 3 Form 144/A entries.
- Zero new accessions; both prior watermarks found, pagination complete, no possible feed gap.
- Ten bounded backfills parsed and 57 detail rows appended; zero parse errors and zero source-hash mismatches.
- Ledger: 669 structured accessions / 4,560 detail rows; 208 bounded backfills remain.
- Zero signal-eligible filing headers.

## 3. Independent crosswalk artifact QA

The 10 proposed-sale rows were independently recalculated from the Form 4 artifact CSV:

- All ten are Form 4 transaction code `S` / disposition `D`.
- All ten have exact Form 144 ↔ Form 4 share-quantity matches.
- Absolute relative difference between Form 144 reported aggregate value and Form 4 shares × reported price: median **0.00334%**, maximum **0.16209%**. This validates record-level consistency only; it does not establish execution time or predictive value.
- Eight of ten proposed-sale rows have a Form 144 acceptance timestamp. Two are missing:
  - Upstart Holdings, 2026-11-18, accession `0001921094-26-001212`, 3,000 shares.
  - Fold Holdings, 2026-11-18, accession `0001959173-26-008140`, 10,798 shares.
- For the eight rows with known acceptance timestamps, Form 144 acceptance precedes Form 4 acceptance by a median 5.385 hours (range 4.213–63.363 hours). Form 4 acceptance is not execution time; first-seen fields are poll-receipt upper bounds, not exact public-release times.

The four-row Upstart cluster contains four reporting owners and 19,502 proposed shares across 2026-11-18 and 2026-11-20. The 2026-11-18 row has a missing Form 144 acceptance timestamp. The absence of remarks flags does not prove discretionary selling or the absence of a Rule 10b5-1 plan.

The Phase 617 issue body said one match had an unresolved Form 144 acceptance clock. The independently inspected artifact contains two proposed-sale rows with missing Form 144 acceptance timestamps. A correction was added to [Issue #234](https://github.com/jafelix81/NuevaEstrategia/issues/234).

## 4. Code hardening

The existing Phase 525 crosswalk summary did not expose missing Form 144 and Form 4 acceptance timestamps separately. Phase 618 adds an `acceptance_clock_audit` object containing:
- proposed-sale row count;
- missing Form 144 acceptance row count and accession list;
- missing Form 4 acceptance row count and accession list;
- total proposed-sale rows with unresolved acceptance clocks.

Two offline regressions independently test missing Form 144 acceptance and missing Form 4 acceptance. The row-level `availability_relation` behavior is unchanged.

## 5. Research boundary

This is a data-reconciliation and auditability improvement, not a smart-money signal. Form 144 is a proposed-sale notice, not proof of execution. Historical F80 membership, exact public availability, and intraday execution remain unverified. No event study, return test, OOS, bootstrap or LOO was run.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, capital, exposure, cost, parameter, holdout or production change. No paid data were acquired and no provider was contacted.
