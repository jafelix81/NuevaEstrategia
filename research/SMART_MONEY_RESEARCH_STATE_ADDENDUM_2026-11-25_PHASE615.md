# Smart Money Research state addendum — Phase 615

**Date:** 2026-11-25 UTC  
**Phase:** 615 — SEC 13F full-snapshot and late-index safety

- Phase 614's prior accession watermark is now diagnostic only; scheduled capture scans the complete current feed snapshot to a proven short/empty page and compares all accessions against the local append-only ledger.
- The first scheduled baseline also enumerates the complete available snapshot before setting a watermark; baseline rows have no historical lower bound.
- Only explicitly recognized neighboring form types are tolerated and counted separately from exact target-form entries. Unclassifiable or unexpected recognized forms and unparseable exact target-form entries fail closed.
- Atom `updated` is diagnostic only. It does not terminate pagination or establish an observation interval. A bounded collector interval is between two complete-snapshot poll receipts, not an exact public-release timestamp.
- Scheduled scans are capped at 50 pages / 5,000 raw entries per form feed. A cap, repeated page, parsing failure or incomplete pagination suppresses candidates and does not advance that feed's successful state.
- Manual mode remains one-page diagnostic-only and non-persistent. PR validation remains offline-only; scheduled capture starts only after merge to main.
- Offline validation passed **33/33 tests** in [Run 45569631053](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45569631053); the live-capture job was skipped as designed.

Source status at preflight:
- FINRA Reg SHO: 7/7 HTTP-200 daily files rejected for overlapping duplicate BCPC/TPC rows; 14 duplicate extra rows; zero accepted files or eligible first-seen events.
- CFTC TFF: 3,043 rows unchanged; no new reports/revisions; latest report date 2026-11-17; zero signal-eligible rows.
- SEC Form 4/Form 144 remain descriptive structured ledgers; no signal admitted by this phase.
- Cboe public monthly symbol-volume archive remains killed for F80 due coverage and PIT/contract-level limitations. OPRA-wide/Open-Close remains separately budget-gated.

No live SEC request, holdings download, alpha test, OOS test, bootstrap or LOO was performed. No production or baseline change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No paid data, vendor contact or quote request.


## 2026-11-25 08:50 UTC — operational and source-ledger checkpoint

### Pull requests and Actions evidence
- PR #231 (Phase 614) and PR #232 (Phase 615) remain open, draft and unmerged. PR #232 is stacked on the Phase 614 branch; its workflow will not begin scheduled capture until the stack reaches the default branch.
- PR #232 validation [Run 45569631053](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45569631053): offline-regression completed successfully (33/33); live-capture was skipped; no artifact was produced, as expected for offline-only PR validation.
- PR #231 validation [Run 45560522598](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45560522598): offline-regression completed successfully (27/27); live-capture was skipped; no artifact was produced.
- No reviews or review threads are recorded on PR #232.
- The connected GitHub read surface used for this checkpoint exposes run-specific jobs/logs/artifacts and commit-associated PR runs, but not the repository-wide Actions run-list endpoint. Therefore this checkpoint does not certify the latest-100 run inventory or all current queued/in-progress runs. Every run inspected directly below is complete.
- The latest commit returned by the repository's recent-commit search was [e2d7199](https://github.com/jafelix81/NuevaEstrategia/commit/e2d7199f37c32b9cbd3871705536be9e38be510c), 2026-11-25 06:26:30 UTC, archiving the failed public Cboe monthly-volume candidate. Phase 614 and Phase 615 branches are present; no Phase 616 branch exists.

### SEC Form 4 — Run 45533818624
- Both offline and live jobs completed successfully.
- 593 new unique accession events from 1,271 candidate occurrences; 669 same-feed duplicate occurrences and 9 cross-feed duplicate occurrences were recorded and deduplicated.
- Bounded backfill parsed 10 accessions and appended 24 structured transaction-detail rows; 2,903 bounded accessions remain.
- Filing-level owner enrichment appended 10 owner rows; 20 bounded accessions remain.
- Descriptive Form 144/Form 4 crosswalk: 11 rows, zero signal-eligible matches.
- Research-observation-eligible rows: 0; signal-eligible rows: 0.
- Artifact [14986800169](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45533818624/artifacts/14986800169) is present and unexpired.

### SEC Form 144 — Run 45523407949
- Both offline and live jobs completed successfully.
- 135 new accessions parsed; 912 detail rows appended; cumulative ledger: 659 accessions / 4,503 detail rows.
- Post-capture source-hash reconciliation: 4,503/4,503 matching rows, zero mismatches.
- The post-capture quality audit classified 659 filing headers as research-observation-eligible, but signal-eligible filings remain 0. Proposed-sale notices are not evidence of completed executions.
- Artifacts [14981126978](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45523407949/artifacts/14981126978), [14980699402](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45523407949/artifacts/14980699402) and [14980358401](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45523407949/artifacts/14980358401) are present and unexpired.

### FINRA Reg SHO — Run 45550366574
- Offline and live jobs completed successfully; 7 daily files returned HTTP 200.
- All 7 files were rejected by the fail-closed duplicate-symbol/facility-overlap gate; 14 extra duplicate rows were diagnosed (BCPC and TPC).
- Accepted files: 0; first-seen observations: 0; research-observation-eligible: 0; signal-eligible: 0.
- Artifact [14992784656](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45550366574/artifacts/14992784656) is present and unexpired.

### CFTC TFF — Run 45550124780
- Prospective capture and tests completed successfully.
- Historical ledger remains 3,043 rows; no new reports or revisions; zero signal-eligible historical rows.
- Artifact [14992729209](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45550124780/artifacts/14992729209) is present and unexpired.

### Research decision
- Phase 615 remains a metadata-capture hardening change only. No live 13F feed has been captured from the unmerged PR stack; no 13F holdings or institutional features are available from this work.
- Form 4 and Form 144 continue as descriptive ledgers. The 659 Form 144 research-eligible filing headers do not establish executed sales or a predictive signal; transaction-line attribution and event-outcome validation remain required.
- FINRA remains quarantined; CFTC remains contextual only. No alpha, OOS, bootstrap or LOO result is admitted.
- No live SEC 13F dispatch, rerun, manual duplicate poll, vendor contact, quote request or paid-data purchase was made.

Next: keep PR #231/#232 isolated until reviewed; after the stack reaches the default branch, validate the first natural 13F baseline and first subsequent bounded poll. In parallel, prioritize Form 4 transaction-line/owner attribution and Form 144 proposed-versus-executed outcome linkage before any economic test. Keep `F80_TOP20_PARTIAL50_BASELINE_C20` frozen.
