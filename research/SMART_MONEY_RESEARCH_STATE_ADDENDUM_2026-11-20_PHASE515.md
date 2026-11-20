# Smart Money Research state addendum — Phase 515 (2026-11-20)

## FINRA Reg SHO — current CNMS schema incompatibility identified

- Preflight main HEAD: `1fa5e7c427caba657c74b4e4268f57e47cc82b00`.
- Latest Actions inventory reviewed: 100 most recent runs; zero active and zero queued at preflight. Relevant jobs, logs, artifacts, recent branches, open PRs and current research files were inspected. No manual dispatch or rerun was started.
- Latest scheduled Phase 469 run [44669121290](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44669121290) completed both jobs successfully; 56 offline tests passed. The live poll received eight HTTP-200 responses but rejected all eight as `market_code_invalid`. It produced zero valid files, zero first-seen events, zero eligible research observations and zero signals. No raw market rows were persisted; response hashes and sizes remain in the append-only poll ledger.
- The current parser required a single-character Market field. FINRA's Developer Center describes Reg SHO daily volume as aggregated by security; current CNMS documentation shows one security row with a comma-separated Market list (for example B,Q,N). The older FINRA file-layout PDF still describes a one-character reporting-facility identifier. This mismatch is why the parser now supports both consolidated security rows and legacy single-code facility rows without double-counting.
- Prior run [44453548570](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453548570) also rejected eight HTTP-200 files, then under a duplicate-symbol assumption. Neither run produced valid observations.
- The repair preserves two modes: comma-separated Market lists mean already-consolidated security rows and are never summed; single-code rows can be facility-grain and are aggregated only across distinct facilities. Duplicate composite symbols, duplicate facility pairs, malformed codes, numeric inconsistencies and trailer mismatches remain fail-closed.
- Four new tests cover consolidated Market lists, no double aggregation, duplicate composite symbols, malformed tokens and duplicate facility codes. The existing facility-row aggregation tests remain.
- The next existing scheduled Phase 469 run is the live validation gate. The PR CI run is offline-only; do not manually dispatch or rerun a scheduled poll.

## Latest source captures

- **SEC Form 144:** [Run 44662324343](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44662324343) succeeded for both feeds with complete pagination. It resolved 70 new XML blocks and parsed 70 new accessions into 542 detail rows; the separate bounded backfill attempted 10 older accessions and appended 54 more rows. The ledger now has 80 accessions, 596 detail rows and 61 issuer CIKs; all 596 source hashes match. There are 368 accessions remaining in the bounded backfill. Public availability and signal eligibility remain false.
- **SEC Form 4:** [Run 44656159115](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44656159115) succeeded. It recorded 457 new canonical Form 4 accessions; the bounded structured backfill parsed 10 documents and appended 22 rows. 1,190 accessions remain. Original XML hashes are not comparable to the first-seen metadata ledger because the original ledger did not store them. Public availability and signal eligibility remain false.
- **CFTC TFF:** [Run 44668300202](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44668300202) succeeded with 3,039 rows unchanged and no new reports or revisions. Zero historical rows are signal-eligible; the CFTC archive Updated-date PIT clock remains rejected.

## Other open research gates

- PR #159: FINRA Consolidated Short Interest remains conditional on authorized credentials and a complete asynchronous pilot snapshot.
- PR #164: OptionMetrics Dividend Gap remains a data-feasibility candidate; no data purchase or model test.
- PR #165: CFTC archive Updated-date PIT falsification remains documented in draft.
- PR #166/#167: SEC Form 4/Form 144 live-validation documentation remains in draft; the live collectors themselves are operating on their existing schedules.

## Strategy disposition

- No Smart Money signal admitted.
- No returns, event study, backtest, chronological OOS, bootstrap, LOO or holdout test was run in this phase.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Universe, parameters, exposure, costs, holding-period rules, holdout and production remain unchanged.
- The invalid FINRA dates are not backdated into eligibility. An `invalid_file` response is not proof that the source was unavailable; older dates first accepted after the repair remain bootstrap-only unless a prior scheduled `not_available` observation satisfies the strict late-first-seen rule.
