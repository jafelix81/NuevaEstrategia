# Phase 450 — N-PORT short-position disclosure and amendment-delta disposition

**Audit time:** 2026-11-17 08:43 UTC  
**Disposition:** The observed N-PORT amendment pair contains no short-position changes. Kill amendment-delta-as-flow for this pair; retain quarterly short-position levels only as a low-priority, delayed context candidate. No return/alpha test or source admission.

## 1. Preflight and source lineage

- Main HEAD before this audit: `89182f81bfd6d1275c596c4c75b4de1768f9b55d` (Phase 449).
- Actions total: 7,691 runs; explicit `in_progress` and `queued` queries both returned zero. Latest 100: 62 success / 37 failure / 1 cancelled.
- Branches: 285 across three pages (100/100/85); open PRs: 56; workflow files: 69.
- Latest overall run [44009082677](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44009082677): Phase 448 PR CI, offline-regression passed 18/18; live capture was skipped by design; no artifact.
- Latest main push [44007937167](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007937167): Phase 447 client compile and 14/14 synthetic contract tests passed; no artifact.
- FINRA validation [44007662531](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007662531) stopped at the credential guard with `FINRA_ACCESS_TOKEN`, `FINRA_CLIENT_ID` and `FINRA_CLIENT_SECRET` empty; no FINRA request was made.
- Latest scheduled SEC Form 144 run remains [43970444015](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43970444015), a pre-Phase-444 capture. The 144/A feed timed out after four retries; ledger commit was skipped and no artifact was produced. Schedule-filtered Actions query still shows this as the newest scheduled run. Phase 448's :47 UTC re-arm has not produced a later scheduled event. The workflow's enabled/disabled setting is not exposed by the available read interface; do not infer its state.
- CFTC's next configured weekday slot is 2026-11-17 22:25 UTC and was not yet due at this audit time. The latest known capture remains bootstrap [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200), with 3,035 warm-up rows, zero signal-eligible historical rows and artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705).

## 2. N-PORT evidence recovered from the existing stacked branch

This audit inspected the existing open PR chain #15–#17 and the completed Phase 311–314 runs. It did not start or rerun any workflow.

### Phase 311 — accession census

The census covers 28 quarterly master-index partitions from 2019Q4 through 2026Q3. It is a filing/accession inventory, not a holdings-level security coverage panel. Quarterly filing counts are large, but those counts do not establish that a particular equity security or short position is disclosed.

### Phase 312/313 — 56-filing raw sample and identity correction

- The 56-filing sample is deterministic (one SHA-minimum accession per quarter for each of NPORT-P and NPORT-P/A), spans 54 registrant CIKs, and is **not a representative prevalence sample**.
- Phase 313 re-verified all 56 raw submission hashes.
- Series and class identity: 53/56 MATCH, 3/56 MISSING_BOTH, zero mismatches.
- The sample contains 176 sign-concordant short-equity rows, concentrated in only two filings:
  - Otter Creek Long/Short Opportunity Fund, NPORT-P/A: 20 rows, report date 2022-07-31, filed 2022-10-03 (64 calendar days later).
  - Saba Capital Income & Opportunities Fund II, NPORT-P: 156 rows, report date 2025-10-31, filed 2025-12-30 (60 calendar days later).
- Across those rows: 173 unique CUSIPs, 173 unique ISINs and 20 ticker-reported rows. Only 6/20 reported tickers exactly match the legacy 335-name ticker strings. The other 156 rows have no ticker and remain UNKNOWN_NOT_REPORTED, not non-matches.
- The two filings are cross-fund observations at different report dates; overlapping CUSIPs do not establish continuous ownership or a trade.

The sample was deliberately deterministic, not randomly representative. The two positive filings therefore cannot be used to estimate short-position prevalence or universe coverage.

### Phase 314 — Otter Creek original-parent comparison

Completed run: [43160951691](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43160951691).  
Job: `parent-audit`, successful.  
Artifact: [13917229995](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43160951691/artifacts/13917229995), 467,273 bytes, SHA-256 `ec1a61d1172350778b9da1d4ef0e49f25a6279c1b3b328747992fdccc92ebe2b`.

- 8/8 Phase 314 offline tests passed.
- 25 candidate original NPORT-P submissions were examined for the 2022Q3 Otter Creek amendment.
- One unique metadata parent candidate was identified, but the audit correctly labels linkage `UNIQUE_METADATA_PARENT_CANDIDATE_NOT_AUTHORITATIVE`; it is not an authoritative parent relationship.
- Original versus amendment short positions: 20 original rows, 20 amendment rows, **20 unchanged, 0 modified, 0 added, 0 removed**.

The observed amendment did not alter the short-position rows. It is not a new position event and must not be treated as incremental short flow. Because the parent link is not authoritative and the sample is purposive, this does not prove that all N-PORT amendments are unchanged.

## 3. Research disposition

1. **`NPORT_AMENDMENT_SHORT_POSITION_DELTA`: KILL for the observed Otter Creek pair.** No position delta exists; no event or return test is warranted for this pair.
2. **`NPORT_QUARTERLY_SHORT_POSITION_LEVEL`: CONDITIONAL / LOW PRIORITY context only.** The two positive filings in a non-representative 56-filing sample are insufficient to establish historical coverage, signal frequency or predictive content.
3. **`NPORT_QOQ_AGGREGATE_SHARE_GROWTH_TOP_BOTTOM`: remains KILLED** under Phase 386. Do not reopen by changing thresholds or holding periods.
4. **Form 13F broad-universe ownership change: remains PARKED** under Phase 386 pending effective-dated security identity and adequate full-universe coverage.

N-PORT is a delayed fund-reported position snapshot, not transaction-level order flow. The observed 60–64 calendar-day report-to-filing lags are material. Do not backdate the knowledge date to the report date. Use actual EDGAR acceptance/first-public availability and retain each accession/amendment as a separate vintage. The current public-disclosure regime and SEC's delayed implementation of the 2024 amendments must be rechecked before any future cadence assumption; the 2026 proposal is not an effective rule.

## 4. Re-entry gates

Do not start a return test until all of the following pass:

1. A representative, predeclared filing sample stratified by registrant/fund type, year, form, and report period; distinguish filing census coverage from security-position coverage.
2. Effective-dated CUSIP/ISIN-to-listing/share-class mapping, including inactive/delisted securities, corporate actions and ticker changes.
3. Original accession, acceptance/public timestamp, amendment parent/child lineage and immutable raw hashes; amendments must never be backdated.
4. Coverage and missingness measured against the full historical universe, not only today's ticker list or rows with reported tickers.
5. Separate position-level changes from report amendments, valuation changes, class/series corrections and true new report periods.
6. A new, preregistered hypothesis that controls for prior returns, momentum, size, liquidity and sector, then compares incrementally with frozen LTM/F80 under identical exposure, costs, chronological validation, block bootstrap, LOO and multiplicity control.

No raw data were added to main. No N-PORT/13F signal, return, alpha, OOS, bootstrap, LOO or holdout test was run in this phase. The stacked PRs #15–#17 were not merged or modified.

## 5. Portfolio controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, capital, exposure, holdout, trading code or production settings changed.

## References

- [Phase 313 result and raw-hash reconciliation](https://github.com/jafelix81/NuevaEstrategia/blob/phase313-nport-sgml-header-identity-correction/research/PHASE313_NPORT_SGML_HEADER_IDENTITY_CORRECTION_2026-11-12.md)
- [Phase 314 completed run and artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43160951691)
- [Phase 386 N-PORT / 13F hypothesis disposition](https://github.com/jafelix81/NuevaEstrategia/blob/main/research/PHASE386_SEC_13F_NPORT_HYPOTHESIS_DISPOSITION_2026-11-13.md)
- [SEC Form N-PORT data sets](https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets)
- [SEC Form N-PORT Readme](https://www.sec.gov/files/nport_readme.pdf)
- [SEC April 2025 delay of Form N-PORT amendments](https://www.sec.gov/rules-regulations/2025/04/s7-26-22)
- [SEC February 2026 proposed Form N-PORT rule](https://www.sec.gov/files/rules/proposed/2026/ic-35962.pdf)
