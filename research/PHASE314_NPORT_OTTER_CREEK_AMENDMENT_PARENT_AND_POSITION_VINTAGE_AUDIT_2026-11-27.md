# Phase 314 — N-PORT Otter Creek amendment parent-candidate and position-vintage audit

**Audit cutoff:** 2026-11-27 13:20 UTC  
**Workflow:** [run 46006090277](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46006090277) — success  
**Artifact:** [15201951527 — phase314-otter-creek-parent-audit](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46006090277/artifacts/15201951527)  
**Disposition:** unique metadata parent candidate found; 2022 amendment has no change in the 20 audited short-position rows. This is a filing-vintage reconciliation, not a trade or alpha result.

## 1. Preflight and execution

Before continuing, the repository-wide Actions run list, active runs, open PRs, branches, current main commit, relevant jobs/logs/artifacts and research files were checked. No workflow was active at preflight. The existing Phase 314 workflow on the Phase 313 branch was then advanced by adding a regression test that ensures registrant CIK is taken from the master-index registrant field, not inferred from the accession prefix. This matters because the accession prefix can identify a filing agent/submitting entity rather than the registrant.

The push triggered exactly one Phase 314 run. The job completed successfully; all **9/9 offline tests** passed. The workflow downloaded and SHA-256 hashed the 25 pre-filing NPORT-P candidates for registrant CIK 0000811030 in 2022Q3, plus the already archived Phase 312 amendment and Phase 310 same-series 2023 control. No paid data, vendor contact, email or non-SEC request was made.

## 2. Parent-candidate result

Target amendment:
- Accession: 0001145549-22-060851
- Form: NPORT-P/A
- Registrant CIK: 0000811030
- Report date: 2022-07-31
- Filed: 2022-10-03
- Series: S000043717 — Otter Creek Long/Short Opportunity Fund
- Classes: C000135565 and C000135566
- Short-position rows under the pre-registered narrow filter: 20

Among 25 candidate NPORT-P filings, exactly one matched the same registrant CIK, exact report date, exact series ID, original form type and an earlier filing date:

- Candidate accession: 0001145549-22-059178
- Filed: 2022-09-28
- Report date: 2022-07-31
- Series identity: MATCH
- Class identity: MATCH
- Series name and class-ID sets: exact match to the amendment
- Short-position rows: 20
- Raw SHA-256: bf72bdb691f7058cb52879610297d6dfde17ff00f718ba09910cde592ba4d433

The linkage status remains **UNIQUE_METADATA_PARENT_CANDIDATE_NOT_AUTHORITATIVE**. The matching rule is strong metadata evidence, but the filing does not provide an explicit authoritative parent-accession pointer in this audit. Do not upgrade this to an authoritative legal lineage edge.

All 25 downloaded candidates had series and class header/XML identity state MATCH. Their report-date counts were 2 for 2022-05-31, 17 for 2022-06-30 and 6 for 2022-07-31.

## 3. Position-vintage reconciliation

The 20 short-position rows in the candidate original and 20 rows in the amendment were compared by security identity (CUSIP, with controlled fallback), position type and reported balance/value/%NAV.

| Original vs amendment | Rows |
|---|---:|
| Unchanged | **20** |
| Modified | 0 |
| Added | 0 |
| Removed | 0 |

Thus the amendment does not change any of the 20 short-position rows under this comparison. It must not be counted as a second position event, a new short, or evidence of a new trade. This result is consistent with treating the amendment as a separate as-filed vintage that happens to carry the same audited short rows.

A same-series 2023 control was also reconciled:
- Accession: 0001145549-23-060491
- Report date: 2023-07-31
- Filed: 2023-09-29
- Short-position rows: 27

Compared with the 2022 amendment vintage, the 2023 control has 4 modified, 23 added, 16 removed and 0 unchanged short-position rows. This is a cross-period holdings comparison only. It cannot establish when positions were opened, covered, hedged, transferred or otherwise changed, and it is not a transaction tape.

Report-to-filing lags are 59 days for the 2022 original, 64 days for the 2022 amendment and 60 days for the 2023 control. These are filing-date lags, not verified first-public-receipt lags.

## 4. Research interpretation and remaining gates

N-PORT remains a **conditional slow institutional-positioning/context source**, with a useful advantage over 13F for certain reported short positions. It is not a direct smart-money trade-flow feed:
- position date is not knowledge date;
- acceptance datetime is not verified first public receipt;
- an amendment is a new disclosed vintage, not a new trade;
- short positions are holdings snapshots, not executed short-sale records;
- this one-fund lineage does not establish broad coverage or predictive value.

Still missing before a security-level feature or event study:
1. authoritative amendment-parent lineage or an explicitly conservative non-authoritative lineage policy;
2. effective-dated CUSIP/ISIN-to-listing/security mapping, including inactive, renamed, acquired and share-class cases;
3. representative fund/series/security/year sampling and measured coverage against historical F80 membership;
4. prospective first-public-receipt capture or a defensible conservative legal/publication floor;
5. a frozen price/corporate-action source and pre-specified next-executable-session labels;
6. incremental tests against frozen LTM/F80 with identical exposure and costs, chronological OOS, event-block bootstrap and leave-one-event/series-out checks.

The 56-filing Phase 312 sample was deterministic and stratified, not a representative prevalence sample. The two filings with short rows cannot be used to estimate short-position prevalence or universe coverage.

## 5. Controls

- No holdings were interpreted as trades.
- No event study, return test, alpha test, OOS, bootstrap, LOO or holdout test was run.
- No F80 membership, security universe, model, exposure, costs, capital, parameters or production behavior changed.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No vendor contact or purchase; data budget remains USD 0.
- Raw submissions remain in the expiring Actions artifact, not committed to the repository.

**Next disposition:** retain N-PORT as a slow-positioning candidate; do not promote a feature. The unique 2022 parent candidate and unchanged amendment rows resolve a data-lineage question, not an alpha hypothesis.
