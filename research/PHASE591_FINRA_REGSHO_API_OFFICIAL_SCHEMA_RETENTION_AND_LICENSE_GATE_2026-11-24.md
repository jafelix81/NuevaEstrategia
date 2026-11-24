# Phase 591 — FINRA Reg SHO Query API: official schema, retention and license gate

**Audit cutoff:** 2026-11-24 08:37 UTC  
**Main HEAD at preflight:** `101f5872aaa93b60031227c6c1010b23db030efc`  
**Disposition:** official documentation confirms a facility-coded Query API sample, but the dataset is limited to a rolling 12-month period and its mock metadata description is internally inconsistent with its own sample. Use it only as a bounded recent reconciliation source after permitted-use rights and credentials are confirmed. Keep Phase 469 fail-closed. No live API request, parser change, signal or return test was made.

## 1. Actions/repository preflight

The latest main commit at the audit cutoff is `101f5872` (2026-11-24 08:00:02 UTC), which records Phase 590.

The GitHub connector exposes specific run/job/artifact retrieval but no repository-wide Actions run-list endpoint. A commit-associated run lookup returned no PR-triggered runs; this does not establish that there are no scheduled, queued or in-progress runs. No global active/queued assertion is made. The four latest relevant scheduled runs inspected below have all jobs completed.

| Workflow | Run | Job result | Artifact |
|---|---:|---|---|
| FINRA Reg SHO / Phase 469 | [45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236) | offline regression success; live poll job success, but 6/6 files rejected | [14895571787](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236/artifacts/14895571787), downloaded and inspected |
| SEC Form 4 / Phase 476 | [45332760566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566) | both jobs success | [14892950135](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566/artifacts/14892950135), downloaded and inspected |
| SEC Form 144 / Phase 403 | [45330252226](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226) | both jobs success; post-capture quality and 10b5-1 gates passed | [14891955642](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891955642) and [14891416912](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891416912), downloaded and inspected |
| CFTC TFF / Phase 384 | [45338400329](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329) | prospective capture success | [14895036288](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329/artifacts/14895036288), downloaded and inspected |

All four artifacts were unexpired at retrieval. No workflow was dispatched, rerun, cancelled or duplicated.

### Branch comparison against current main

| Branch | Ahead | Behind | Disposition |
|---|---:|---:|---|
| `phase20c-finra-walkforward` | 12 | 592 | diverged; do not merge/replay |
| `phase515-finra-cnms-market-list-schema-repair` | 5 | 161 | diverged; inspect changes selectively only |
| `phase547-cboe-opra-options-pit-feasibility` | 5 | 94 | diverged; no merge |
| `phase530-massive-options-history-pit-license-audit` | 5 | 138 | diverged; no merge |
| `phase548-sec-midas-methodology-pit-reclassification` | 2 | 94 | diverged; no merge |

The Phase 590 repository snapshot listed 380 branches, 72 open PRs and 96 workflow files. This run rechecked the relevant branches and the current main commit, but did not claim a fresh exhaustive repository-wide count.

## 2. FINRA CNMS: downloaded artifact confirms the duplicate pattern

Run 45339067236 completed its scheduled poll with HTTP 200 for six daily files, but all six were rejected by the duplicate-symbol guard. The downloaded artifact contains only compact diagnostics and counts; raw rows and volume values were not persisted.

| Trade date | BCPC market-token sets | TPC market-token sets |
|---|---|---|
| 2026-11-23 | B,N,Q and N,Q | B,N,Q and B,N,Q |
| 2026-11-20 | B,N,Q and N,Q | B,N,Q and B,N,Q |
| 2026-11-19 | B,N,Q and Q | B,N,Q and B,N,Q |
| 2026-11-18 | B,N,Q and Q | B,N,Q and B,N,Q |
| 2026-11-17 | B,N,Q and Q | B,N,Q and N,Q |
| 2026-11-16 | B,N,Q and Q | B,N,Q and B,N,Q |

None of the repeated rows is an exact raw-row duplicate. TPC has two rows with the same facility-token set on five dates; BCPC has overlapping but different sets. This is not safely resolvable by ticker-level deduplication or by summing the rows without an authoritative cross-check.

Run summary:
- HTTP 200: 6; HTTP errors: 0.
- Valid files: 0; invalid files: 6.
- Duplicate-symbol occurrences: 12; extra rows: 12.
- First-seen events: 0; research-observation-eligible: 0; signal-eligible: 0.
- Raw market data persisted: false.

**Decision:** retain the parser's fail-closed behavior. Do not sum or discard either row.

## 3. Official FINRA Query API: what is now confirmed

FINRA's official Developer Center documents `otcMarket/regShoDaily` as daily short-sale volume aggregated by security for short-sale trades executed and reported to a FINRA trade reporting facility.

Official documentation:
- [FINRA Developer Center — Reg SHO Daily Short Sale Volume](https://developer.finra.org/docs)
- [FINRA Query API POST filters and request structure](https://developer.finra.org/docs)
- [FINRA Equity Data specific terms](https://developer.finra.org/specific-terms-equity-data)

### Published sample fields

The official sample and mock metadata expose these seven fields:

- `tradeReportDate`
- `securitiesInformationProcessorSymbolIdentifier`
- `shortParQuantity`
- `shortExemptParQuantity`
- `totalParQuantity`
- `marketCode`
- `reportingFacilityCode`

The official sample contains facility-coded rows such as:
- `marketCode=Q`, `reportingFacilityCode=NQTRF`
- `marketCode=N`, `reportingFacilityCode=NYTRF`
- `marketCode=B`, `reportingFacilityCode=NCTRF`

However, the mock metadata's description for `reportingFacilityCode` lists one-letter values N/Q/B/D, while the sample response uses three-letter facility identifiers in that field and one-letter values in `marketCode`. This is a documentation inconsistency. Do not hard-code a mapping based on the metadata description alone; verify the live production metadata and returned rows.

The documented fields contain no CUSIP, issuer CIK, share-class identifier or other stable security/issue identifier. A symbol/facility/date comparison may validate arithmetic aggregation, but it cannot by itself prove the identity of multiple securities sharing one SIP symbol.

### Critical history limitation

FINRA explicitly states that `regShoDaily` provides a **rolling 12-month period only**. It is therefore unsuitable as the sole source for a multi-year 2022–2026 historical panel or a long OOS reconstruction. It can serve as:
1. A recent, bounded reconciliation source for the six CNMS files.
2. A prospective daily source from the first successful receipt onward, if the API and use rights are approved.

Historical API retrieval now cannot be backdated into first-seen PIT eligibility. The older CNMS archive may retain longer history, but historical exact first-public timestamps and the current duplicate-row grain remain unresolved.

### Volume semantics

The mock metadata describes:
- `shortParQuantity`: aggregate share volume of executed short-sale **and short-sale-exempt** trades during regular trading hours.
- `shortExemptParQuantity`: aggregate share volume of short-sale-exempt trades during regular trading hours.
- `totalParQuantity`: aggregate share volume of all executed trades during regular trading hours.

Therefore `shortExemptParQuantity` is a subset of `shortParQuantity`; it must not be added to short volume a second time. The ratio `shortParQuantity / totalParQuantity` is not net short flow, short interest, investor identity or proof of institutional intent.

## 4. Bounded one-date reconciliation design

After credentials and permitted-use rights are confirmed, a separate manual-only Query API client should:

1. Retrieve and persist the live production dataset metadata, data version, field names/types, partition fields and available partitions.
2. Query one date (`2026-11-23`) separately for BCPC and TPC, using the documented `compareFilters` equality syntax for `tradeReportDate` and `securitiesInformationProcessorSymbolIdentifier`.
3. Request all seven fields, including both `marketCode` and `reportingFacilityCode`.
4. Validate unique row grain at the returned date/symbol/facility/market combination; preserve all rows and response hashes.
5. Compare short, short-exempt and total quantities independently against the CNMS rows and facility-token sets. Do not infer an issue-level mapping from ticker alone.
6. Determine whether API quantities reconcile to one CNMS row, the sum of both rows, or neither. Even an exact sum establishes only symbol-level arithmetic compatibility, not the underlying security identity.
7. Keep BCPC/TPC quarantined if metadata, row grain, market/facility mapping or any quantity fails exact reconciliation. Do not mutate Phase 469's parser based on a mock response.

Only after the one-date production response passes should the same check extend to the other five dates and a bounded recent sample. Those historical requests are reconciliation/bootstrap evidence, not first-seen signal observations.

## 5. Credential and use-right correction

The existing Phase 447 workflow is **not reusable as-is for Reg SHO**: its client hard-codes `otcMarket/consolidatedShortInterest` and its input is a settlement date. It can inform the OAuth implementation, but a separate narrow `regShoDaily` request client is required. No new workflow was created in this phase.

FINRA's Equity Data terms state that the data may be accessed only by Developers with Public, Firm or Organization Query API credentials, and that internal use is limited to non-commercial personal or professional use. FINRA's individual-user documentation separately says Individual accounts are not intended for commercial purposes. Confirm the intended use and the appropriate credential/entitlement before querying. Do not place credentials in repository files or chat.

No FINRA credential was inspected or changed. No FIP/FINRA API request was made.

## 6. Other latest source evidence from downloaded artifacts

### SEC Form 4
Run 45332760566 confirms:
- 516 new canonical accession events; 20 pages.
- Form 4 and Form 4/A watermarks both found.
- Form 4/A had no new accession event in this poll.
- 1,239 accession-observation rows and 516 canonical event-observation rows.
- 579 unique candidate accessions; six cross-feed duplicate occurrences and 653 same-feed duplicate occurrences are retained as observations, not independent events.
- No filing XML was downloaded in this poll; public availability is not certified.
- Zero research-observation-eligible and zero signal-eligible rows.
- Bounded transaction-detail backfill: 10 accessions, 24 rows appended, 2,273 accessions remain.
- Owner identity sidecar: 10 accessions processed, 11 owner rows appended; 20 accessions remain. The current crosswalk has 46 single-owner accessions with identity and four multi-owner accessions quarantined; transaction-line attribution remains unverified.

### SEC Form 144
Run 45330252226 confirms:
- 118 new accession events; 153 feed-observation rows.
- 118 XML documents resolved and parsed; 801 new detail rows.
- Ledger total: 477 accessions / 3,360 detail rows.
- Bounded backfill: 10 accessions parsed, 73 detail rows appended; 238 remain.
- Five acceptance reconciliations remain unresolved.
- 22 new candidate-issuer matches and one cross-feed overlap; the 290-CIK candidate manifest is not a historical F80 security master.
- 118 research-observation-eligible filing headers, but zero signal-eligible; public availability is not certified.
- Phase 549 post-capture audit: 174 accessions with formal Rule 10b5-1 plan-adoption dates across 89 distinct dates; remarks polarity is separately classified. Four explicit negative sell-to-cover cases (Fermi), 15 positive explicit mentions, one ambiguous mention, and 457 no-mention cases. Form 144 remains a proposed-sale notice, not proof of execution. No alpha/OOS/bootstrap/LOO test.

### CFTC TFF
Run 45338400329 confirms:
- 3,043 historical rows across four index contracts.
- No new reports or revisions; no state change.
- Three contracts begin 2010-07-20; Russell E-mini begins 2017-08-15.
- All four latest report dates are 2026-11-17.
- Historical rows remain ineligible for signals; prospective feature engineering is still required.

## 7. Research decision

- New signals admitted: **0**.
- Incremental alpha demonstrated: **none**.
- New return/OOS/bootstrap/LOO evidence: **none**.
- No raw market data or credentials added.
- No parser, workflow, universe, exposure, cost, parameter, holding-period or production change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

**Next gate:** obtain authorized FINRA API credentials and written/clear confirmation that the intended use is permitted; then implement a separate manual-only, one-date `regShoDaily` reconciliation client. Until its live metadata and quantities reconcile exactly, keep all six CNMS files rejected. Independently continue Form 4 owner/transaction attribution and the broader options/13D-G feasibility work; do not treat the API's 12-month window as a multi-year OOS dataset.
