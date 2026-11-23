# Phase 583 — SEC Form 4 feed pagination recovery and live-capture audit

**Audit cutoff:** 2026-11-23 21:10 UTC  
**Main HEAD at preflight:** `197014b7cba5a063c48ebe1693a5c99cad28b97e`  
**Disposition:** operational data-integrity repair. No economic test, signal, alpha or OOS result.

## 1. Preflight

- Actions API: 8,102 total runs; explicit `in_progress` and `queued` queries returned 0.
- Latest SEC scheduled runs were inspected with their jobs, step summaries, logs and artifacts before any write.
- Phase 579/580 runs remain completed and successful; PRs #208/#209 are merged.
- Relevant branches were checked: `phase20c-finra-walkforward`, `phase579-finra-ats-stable-row-pit-gate`, `phase580-finra-ats-tier-and-identity-entry-guard`, `phase403-sec-form144-prospective-first-seen-capture`, and `phase476-sec-form4-first-seen-capture`.
- No active workflow was duplicated, no manual dispatch/rerun was made, and no live SEC request was initiated by this phase.

## 2. New natural SEC captures

### Form 144 — Phase 403

Run [45261140072](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072), started 2026-11-23 20:36:36 UTC. Both `offline-regression` and `live-capture` succeeded. Three artifacts are present and unexpired: [14861750489](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072/artifacts/14861750489), [14860761702](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072/artifacts/14860761702), and [14860501976](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072/artifacts/14860501976).

The live log reports:
- 34 new Form 144/144-A metadata events and 34 XML resolutions.
- 7 candidate issuer matches; no historical F80-membership certification.
- Structured ledger: 349 accessions / 2,486 detail rows; 169 new detail rows; 248 bounded backfill accessions remain.
- No source-hash mismatches; post-capture ledger reconciliation and Phase 565 10b5-1 audit passed.
- 129 formal plan-date entries; median plan-date-to-notice interval 185 days; no future plan dates.
- Public availability is not certified; signal-eligible count remains **0**.

The successful poll and descriptive enrichment are not an insider signal or a return test.

### Form 4 / 4-A — Phase 476

Run [45257913619](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45257913619), started 2026-11-23 20:17:54 UTC. Both jobs completed successfully and artifact [14859736409](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45257913619/artifacts/14859736409) is unexpired.

The job log reveals an important partial-capture condition hidden by the overall successful workflow conclusion:

- Form 4 feed: `GAP_OR_WATERMARK_NOT_FOUND`; 20 pages fetched through offset 1,900; prior watermark `0001493152-26-053593` was not found.
- 938 accession occurrences / 408 unique candidate accessions were retained as observations but correctly suppressed from the canonical event ledger.
- No Form 4 watermark advancement occurred; the committed state still records last successful Form 4 poll at 2026-11-23 07:48:52 UTC and `last_poll_status=GAP_OR_FETCH_ERROR`.
- Form 4-A feed did pass its watermark gate and emitted one new accession.
- The bounded detail job parsed 10 accessions / appended 26 rows; owner enrichment parsed 10 accessions / appended 11 owner rows.
- The Form 144/Form 4 crosswalk has 3 descriptive rows, 2 matched Form 4 accessions, and **0 signal-eligible matches**.
- Public availability, historical F80 membership and transaction-line owner attribution remain uncertified.

The collector's fail-closed behavior is correct: incomplete-poll candidates are not promoted and the previous successful watermark is not advanced. The operational defect is that the 20-page ceiling can leave the Form 4 feed unable to catch up, while the workflow still reports success.

## 3. Phase 583 repair

A narrow branch change is proposed:

1. Increase the bounded Form 4 catch-up ceiling from 20 to 50 pages (up to 5,000 raw Atom entries). The existing 0.35-second inter-page delay and shared SEC request throttle remain unchanged.
2. Preserve fail-closed semantics: no watermark, canonical event or signal is promoted unless the old watermark is found in a complete poll.
3. Add `all_feeds_successful` to the poll summary.
4. After state persistence and artifact upload, make the workflow fail visibly if either Form 4 or 4/A feed is incomplete. This preserves diagnostic artifacts while preventing a partial capture from appearing fully successful.
5. Add a deterministic 21-page mocked regression proving that a watermark beyond the former 20-page cap can be found; existing incomplete-poll suppression/retry tests remain in place.

The change does not claim that 50 pages will always be sufficient. If the watermark remains absent, the collector continues to fail closed and the gap must be investigated rather than silently re-baselined.

## 4. Broader source disposition

- **FINRA ATS:** Phase 579/580 remain synthetic PIT/identity guards only. No real source rows, certified security master, historical F80 membership or terminal-return panel has passed the gate.
- **FINRA consolidated short interest:** the 2026-11-13 settlement is scheduled for public release on 2026-11-24 at 16:40 ET / 21:40 UTC. Phase 447 remains conditional on authorized credentials and written permitted-use confirmation; no request or dispatch is authorized here.
- **Options:** Cboe OPRA/Open-Close and Massive/ThetaData remain conditional on license, actual first-receipt/correction vintages and exact historical universe coverage. No sample or purchase.
- **SEC MIDAS:** retain only as exchange-market-structure/liquidity context; kill the interpretation of hidden-volume metrics as dark-pool or institutional accumulation.
- **CFTC TFF / 13F / 13D-G:** retain existing coverage, PIT and identity restrictions; no new feature admitted.

## 5. Decision and controls

- New signals admitted: **0**.
- Incremental alpha / event-return / OOS evidence: **none**.
- No event study, backtest, bootstrap, LOO or final-holdout test.
- No universe, parameter, exposure, cost, holding-period, portfolio or production change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains **frozen**.
