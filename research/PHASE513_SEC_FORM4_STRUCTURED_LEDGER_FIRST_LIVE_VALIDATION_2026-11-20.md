# Phase 513 — SEC Form 4 structured transaction ledger: first scheduled live validation

**Audit date:** 2026-11-20 UTC  
**Source run:** [44656159115](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44656159115)  
**Main capture commit:** [abf97fb7eab6a42e5db284382dca79b05017e212](https://github.com/jafelix81/NuevaEstrategia/commit/abf97fb7eab6a42e5db284382dca79b05017e212)  
**Disposition:** live parser execution passed; every parsed detail remains non-signal and ineligible for alpha research.

## 1. Scope

This phase verifies the first scheduled execution of the Phase 510 Form 4 structured transaction-detail parser after its merge to `main`. It is an operational and semantic validation, not an alpha test.

The workflow was the existing Phase 476 schedule. No new workflow, manual dispatch, or duplicate capture was started.

## 2. Workflow evidence

Run 44656159115 completed successfully on `main` at 2026-11-20 01:47:28–01:48:00 UTC.

- Offline regression job: success; 50 Phase 476/510 tests passed.
- Live capture job: success.
- Metadata poll: both Form 4 and Form 4/A feeds returned successfully.
- Structured-detail backfill: 10 accessions attempted, 10 parsed, zero parse errors, zero unresolved fetches.
- Append-only persistence: successful; workflow committed five changed files to `main`.
- Artifact: [phase476-sec-form4-first-seen, artifact 14592859142](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44656159115/artifacts/14592859142), 1,318 bytes, SHA-256 `faf88269277209efaf3f68c7920b300bd78448c44a6f2615fdd4b753e3062b8d`.

## 3. First live structured-detail result

The committed `research/data/sec_form4_first_seen/transaction_details.csv` contains 22 rows:

| Detail | Rows |
|---|---:|
| Filing headers | 10 |
| Non-derivative transaction rows | 12 |
| Total | 22 |

The 10 accessions comprise nine Form 4 filings and one Form 4/A. Nine filings have a single reporting owner. One filing has multiple owners and is correctly marked `QUARANTINED_MULTI_OWNER_NO_LINE_LINK`; its transaction rows are not attributed to an individual owner.

All 10 documents have `parse_status=parsed`. The 12 transaction rows contain transaction dates, numeric share quantities, and numeric price fields. The observed transaction-code counts are:

- P: 3
- M: 2
- F: 1
- A: 5
- S: 1

These codes are retained as filing semantics, not promoted to exchange-executed buys or sells. In particular, P/S do not alone establish an exchange execution; A/M/F may describe awards, exercises, or tax/exercise-price mechanics rather than discretionary directional trades. The official SEC transaction-code definitions remain the governing interpretation.

## 4. Critical PIT and integrity gates remain closed

The parser worked, but the current sample is not admissible as a predictive feature panel:

- Signal-eligible rows: **0/22**.
- Research-observation-eligible rows: **0/22**.
- Public availability certified: **0/22**.
- Security identity verified: **0/22**.
- Historical F80 membership verified: **0/22**.
- Owner attribution verified: **0/22**.
- Transaction semantics verified: **0/22**.
- Same-day intraday use authorized: **0/22**.
- Economic new-trade authorization: **0/22**.

The 22 rows have `acceptance_clock_status=PARSED_NOT_EXACT_PUBLIC_AVAILABILITY`. SEC acceptance timestamps are not treated as exact public dissemination timestamps.

The first-seen interval for the sampled accessions is bounded by 2026-11-19 19:31:20 UTC and 2026-11-20 01:47:52 UTC. The upper bound is the first successful poll in which the new metadata was observed; it is not an exact receipt timestamp. It falls after the regular U.S. equity session on November 19. Even the next regular session is not authorized for signal use because public availability, security identity, historical universe membership, owner attribution, and transaction semantics remain unverified.

A second integrity limitation is explicit: **0/22 rows have comparable original-document hashes**. The first-seen metadata ledger did not store an original XML hash because it did not download filing documents. The parser records the retrieved submission/XML hashes, but they cannot be compared with a first-seen XML hash that does not exist. The status is correctly `NOT_COMPARABLE_NO_ORIGINAL_XML_HASH_IN_EVENT_LEDGER`; this is not a hash match and must not be described as one.

The backfill processed 10 accessions and reports 1,190 bounded accessions remaining. This is a bounded queue, not a claim that the full historical backlog has been processed.

## 5. Metadata poll reconciliation

The same run reported:

- 1,001 accession-observation rows persisted.
- 457 new canonical Form 4 accessions.
- Zero new canonical Form 4/A accessions.
- 538 same-feed duplicate occurrences.
- Five cross-feed duplicate occurrences.
- 457 bounded metadata rows.
- Both feeds successful, with no incomplete-poll candidates suppressed.
- `public_availability_certified=false`, `research_observation_eligible_rows=0`, and `signal_eligible_rows=0`.

The large same-feed duplicate count is retained as feed-observation history and is not interpreted as additional filings.

## 6. Operational next steps

1. Continue using the existing scheduled Phase 476 workflow and its fixed 10-accession structured-detail limit. Do not dispatch duplicate runs.
2. Preserve the current fail-closed eligibility flags.
3. Improve the provenance design only through a separately tested change: first-seen metadata alone cannot retroactively provide an original XML hash. Do not fabricate comparability.
4. Resolve issuer/security identity and historical F80 membership through a point-in-time security master before any event study.
5. Validate transaction-code, owner, derivative, amendment, and footnote semantics on a larger stratified sample.
6. Keep Form 144 Phase 509 live validation separate. Its last successful scheduled capture, run 44614323236, predates the Phase 509 merge; `sale_details.csv` is not yet present on `main`. The existing Phase 403 schedule is the next validation path; no manual dispatch was made.

## 7. Research decision

**Phase 510 parser live execution: PASS (10/10 parsed, zero errors).**  
**Form 4 structured-detail ledger persistence: PASS.**  
**PIT/public-availability gate: FAIL / NOT CERTIFIED.**  
**Security and historical-universe identity gate: NOT PASSED.**  
**Owner and economic transaction interpretation gate: NOT PASSED.**  
**Alpha/backtest authorization: NO.**

No returns, event study, backtest, chronological OOS, bootstrap, LOO, or holdout test was run. No signal was admitted. `F80_TOP20_PARTIAL50_BASELINE_C20`, its universe, parameters, exposure, costs, holdout, and production remain frozen.

## 8. Reproducibility pointers

- Run: https://github.com/jafelix81/NuevaEstrategia/actions/runs/44656159115
- Artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/44656159115/artifacts/14592859142
- Main commit with the live append-only ledger: https://github.com/jafelix81/NuevaEstrategia/commit/abf97fb7eab6a42e5db284382dca79b05017e212
- Parser: `research/phase510_form4_structured_transaction_ledger.py`
- Tests: `research/test_phase510_form4_structured_transaction_ledger.py`
- Ledger: `research/data/sec_form4_first_seen/transaction_details.csv`
- Metadata state: `research/data/sec_form4_first_seen/state.json`
