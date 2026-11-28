# Phase 676 — Form 4 first-seen cohort and refreshed Form 144/Form 4 crosswalk

**Audit cutoff:** 2026-11-28 02:46 UTC  
**Main HEAD after scheduled capture:** `5a85dcc2ff90d92c277f8544642d4c69e4b7e97d`  
**Disposition:** successful prospective metadata capture and descriptive crosswalk refresh; no research or signal observations admitted.

## 1. Repository preflight

- Latest 100 Actions runs: 79 success / 17 failure / 4 cancelled; zero queued or in-progress.
- Total Actions runs reported by GitHub: 8,405.
- Branch inventory: 422 branches (100 + 100 + 100 + 100 + 22).
- Open pull requests: 86.
- Latest scheduled Form 4 run: [46099559273](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46099559273), success.
- Phase 675 PR #262 remains a draft stacked on draft PR #230 / Phase 613. Its two latest validation runs, [46092474064](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46092474064) and [46092535366](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46092535366), passed 22/22 tests. It is not merged into main.
- No workflow was dispatched, rerun, cancelled or duplicated.

## 2. New scheduled Form 4 / 4-A capture

Run [46099559273](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46099559273), artifact [15244348107](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46099559273/artifacts/15244348107).

The live job completed all steps, persisted append-only metadata, generated the descriptive crosswalk and passed both feed watermark/continuity gates.

### Feed and event counts

- Form 4: 156 new unique accessions / 156 canonical issuer events.
- Form 4/A: zero new accessions; prior watermark found.
- Both feeds: successful polls, no page errors, no incomplete-poll candidates suppressed.
- Latest Form 4 Atom `updated`: 2026-11-28 02:32:43 UTC.
- Page-received / first-seen upper bound for the latest page: 2026-11-28 02:45:03 UTC.
- 156 metadata intervals were bounded by the prior successful poll and the current page receipt.
- The Atom `updated` value is not treated as exact public availability or acceptance time.

### Entity-structure reconciliation

The append-only entity ledger contains 353 observations for this run: 351 candidate entity occurrences plus two watermark-boundary observations. The 351 candidate occurrences resolve to 156 unique accessions.

| Control | Result |
|---|---:|
| Unique accessions | 156 |
| Issuer entity rows | 156 |
| Reporting-owner occurrences | 195 |
| Distinct issuer CIKs | 86 |
| Distinct reporting-owner CIKs | 180 |
| Filings with one reporting owner | 149 |
| Filings with multiple reporting owners | 7 |
| Missing issuer entity | 0 |
| Multiple issuer CIKs per accession | 0 |
| Unknown entity roles | 0 |
| Quarantined accessions | 0 |
| Path/entity CIK mismatches | 0 |
| Exact duplicate entity-key groups | 0 |
| Legitimate multi-entity accessions split across pages | 2 |

The accession-prefix CIK equals the issuer CIK for only 36 of 156 accessions. It must not be used as a substitute for issuer identity. EDGAR's `owner=include` feed repeats one accession for issuer and reporting-owner entities; 195 repeated accession occurrences are not 195 additional filings or transactions.

### PIT and eligibility boundary

- 156 rows are `BOUNDED_METADATA_ONLY`.
- `public_availability_certified=false` for all 156.
- `research_observation_eligible=0`.
- `signal_eligible=0`.
- Filing XML/text was not downloaded by the first-seen collector; raw transaction rows were not stored by that collector.
- No same-day/intraday use is authorized.
- Use of the filing date or Atom `updated` as an exact tradable timestamp is prohibited. A future study must use a conservative, reproducible availability rule and separately verify acceptance/public-availability clocks, security identity, historical F80 membership, owner attribution and transaction semantics.

## 3. Backfill and transaction-detail state

The scheduled workflow's bounded backfills completed without parser errors:

- Transaction-detail backfill: 10 accessions parsed; 32 detail rows appended; zero parse errors; 3,614 bounded accessions remain.
- Reporting-owner identity: 10 accessions parsed; 12 owner rows appended; 9 single-owner and 1 multi-owner accession; zero parse errors; 20 bounded accessions remain in this owner-identity queue. Transaction-line attribution is not verified.
- Footnote references: 10 accessions parsed; 29 reference rows appended; zero parse errors; 30 accessions remain pending.
- Raw XML is not persisted in these backfills.

These are ingestion/enrichment counts, not independent insider decisions.

## 4. Refreshed Form 144 / Form 4 crosswalk

The same Form 4 run rebuilt the descriptive crosswalk after the prior scheduled Form 144 capture [46079844681](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46079844681).

| Metric | Result |
|---|---:|
| Proposed-sale matches | 17 |
| Distinct Form 4 accessions | 16 |
| Distinct issuers | 12 |
| Distinct reporting owners | 16 |
| Form 4 sale/disposition rows considered | 96 |
| Multi-owner accessions quarantined | 9 |
| Ambiguous transaction-reuse cases quarantined | 3 |
| Form 144 acceptance clocks missing | 2 |
| Signal-eligible matches | **0** |

The crosswalk remains descriptive only. A Form 144 is a proposed-sale notice, not proof of execution; intraday execution time is unknown. Historical F80 membership is not verified. Exercise/tax context and other remarks remain separate from transaction codes.

The descriptive crosswalk is now refreshed against the 2026-11-27 Form 144 capture. However, the first natural scheduled Form 144 capture after Phase 673's merge has not yet occurred. Run 46088870898 was PR validation and its live-capture job did not run. Therefore the Phase 673 post-capture accession-level PIT/plan-date join still requires natural-run confirmation.

## 5. Other source checks

- **SEC 13F:** latest scheduled run [46084129349](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46084129349) found four new metadata accessions; no holdings XML/table was downloaded; zero research observations and zero signals. Phase 675's report-period selector remains draft PR #262, not production code.
- **FINRA Reg SHO:** latest scheduled capture in the reviewed 100-run window is [45939887443](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45939887443). Seven files returned HTTP 200, but 14 duplicate symbols caused 28 row occurrences to be quarantined; zero first-seen observations were eligible. Later Phase 661 PR validation runs did not execute live capture. No volume was summed across unresolved duplicate symbols.
- **CFTC TFF:** [45939298160](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45939298160) completed with no new report or revision; 3,043 rows remain; zero historical rows are signal-eligible in that capture.
- **SEC 13D/G:** latest [45988473657](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45988473657) passed offline regression, but the `live-sample` job was skipped. The global live sample remains pending.
- **Options / OPRA / Cboe:** no new workflow run appeared in the latest 100 Actions runs. Historical-vintage, PIT and redistribution/licensing gates remain unresolved; no vendor contact, quote request or purchase was made.

## 6. Research disposition

The new Form 4 cohort expands the prospective metadata panel and improves issuer/owner identity coverage, but it does not create an investable signal. The repeated accession rows are entity relationships, not extra transactions. The refreshed 17-row crosswalk remains non-signal and cannot establish execution timing or historical F80 membership.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No new signal, alpha claim, return test, OOS result, bootstrap/LOO result or holdout use was admitted. Data spend remains USD 0.
