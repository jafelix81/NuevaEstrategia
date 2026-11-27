# Phase 669 — SEC Form 4 live capture and Form 144/Form 4 crosswalk audit

**Source run:** [46057111964](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46057111964)  
**Audit disposition:** `CAPTURE_SUCCESS_DESCRIPTIVE_ONLY_NO_SIGNAL_PROMOTION`  
**Main base:** `193a246959ac053c3c020fe9ca7b9b2ea66b3925`

## 1. Preflight and repository state

- Reviewed the latest 50 Actions runs, job status, recent artifacts, branches, open PRs and current research files before continuing.
- No queued, in-progress, waiting or pending run was present in the reviewed run window.
- The documentation-only SEC 13F stack was integrated in dependency order:
  - [PR #255 — Phase 666](https://github.com/jafelix81/NuevaEstrategia/pull/255), merge commit `ef52fecfcc8711bd457fdcc805b27485fd897df4`.
  - [PR #256 — Phase 667](https://github.com/jafelix81/NuevaEstrategia/pull/256), merge commit `1a33991eb31fefc406ff8382ab7585ed8eee7794`.
  - [PR #257 — Phase 668](https://github.com/jafelix81/NuevaEstrategia/pull/257), merge commit `193a246959ac053c3c020fe9ca7b9b2ea66b3925`.
- These merges add research records only; they do not change capture logic, the trading model or the frozen baseline.

## 2. Latest natural Form 4 capture

The scheduled [Phase 476 run 46057111964](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46057111964) completed successfully on 2026-11-27.

- Offline regression: **82 tests passed**.
- Live capture: success; both Form 4 and Form 4/A feeds passed their watermark/continuity gates.
- Poll window: 19:30:15–19:30:46 UTC.
- Feed 4: 200 accession observations across 15 raw pages; 94 new canonical accessions.
- Feed 4/A: one observation and zero new accessions.
- The 94 new accessions have bounded metadata intervals, but not certified public-availability timestamps.

The append-only poll retained 201 entity observations: 96 issuer-entity occurrences and 103 reporting-entity occurrences. It recorded 105 same-feed repeated accession occurrences across page offsets, four exact duplicate entity-key groups across offsets, and two legitimate multi-entity accessions split across pages. No issuer CIK mismatch, unkeyed entity, unknown role or accession quarantine was recorded.

The 94 new accessions are metadata events, **not 94 verified economic transactions**.

## 3. Bounded structured enrichment

The scheduled run also advanced three existing queues:

| Enrichment | Attempted | Parsed | New rows | Remaining |
|---|---:|---:|---:|---:|
| Transaction details | 10 | 10 | 21 detail rows; 30 footnote references | 3,468 bounded accessions |
| Footnote-reference backfill | 10 | 10 | 50 references | 40 accessions |
| Reporting-owner identity | 10 | 10 | 10 owner rows | 20 accessions |

All three jobs had zero parse errors. Owner identity remains filing-level only: transaction-line attribution was not verified. No row became research-eligible or signal-eligible.

## 4. Form 144 / Form 4 crosswalk

The run rebuilt the descriptive crosswalk from the current ledgers.

| Measure | Result |
|---|---:|
| Proposed-sale/Form 4 crosswalk rows | 16 |
| Unique Form 4 accessions | 15 |
| Distinct issuer CIKs | 11 |
| Form 4 sale/disposition rows in ledger | 89 |
| Form 144 proposed-sale rows in ledger | 864 |
| Proposed-sale rows considered | 856 |
| Prior-sale rows considered | 2,383 |
| Matched prior-sale rows | 0 |

The 16 rows all carry transaction code `S` and acquired/disposed code `D`. Fourteen have a Form 144 acceptance timestamp earlier than the corresponding Form 4 acceptance timestamp. That ordering **does not establish that the Form 144 preceded execution**: the actual intraday execution time is unknown. Two Form 144 acceptance clocks remain unresolved.

The crosswalk quarantined three ambiguous transaction-reuse candidates and eight multi-owner accessions. Twenty-nine Form 4 accessions still lack a single-owner identity suitable for the strict crosswalk.

Remarks flags show two rows with exercise/tax context and fourteen with no specific remarks flag. Absence of a remarks flag is not proof that a transaction was discretionary.

**All 16 rows remain ineligible for signal use.** Historical F80 membership is unverified, and the crosswalk does not establish execution timing or transaction-line ownership sufficiently for an event-time test.

## 5. Artifact inspection

Artifact [15226433611](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46057111964/artifacts/15226433611) is a 5,979-byte ZIP containing seven compact files (20,104 bytes uncompressed): poll summary, entity summary, transaction-detail summary, footnote summary, owner summary, and crosswalk summary/CSV. It contains no raw filing XML and the poll explicitly records that raw transaction rows were not stored.

## 6. Research decision

**Decision: `CAPTURE_SUCCESS_DESCRIPTIVE_ONLY_NO_SIGNAL_PROMOTION`.**

- The latest Form 4 poll improved prospective metadata coverage and preserved entity/page-duplicate diagnostics.
- Structured enrichment progressed, but no transaction was promoted to a research observation.
- The 16 Form 144/Form 4 matches remain descriptive only; acceptance-clock order is not execution-clock order.
- No prices or post-event returns were inspected. No event study, OOS, bootstrap or LOO test was run. The holdout was not touched.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Data spend: **USD 0**.

## 7. Next gates

1. Continue natural Form 4 captures and bounded enrichment without treating metadata volume as signal sample size.
2. Keep proposed-sale notices, executed dispositions, plan/tax context, and filing amendments as separate event classes.
3. Require verified transaction-line owner, exact event clock, economic context and historical F80 membership before any Form 144/Form 4 test.
4. The reviewed latest 50 Actions runs contain no post-Phase-661 natural FINRA live capture. Phase 469's weekday schedule is 22:30/23:30 UTC; no duplicate/manual poll was started before the scheduled window.
5. Continue SEC 13F vintage and unit adjudication separately. PRs #255–#257 are now integrated, but the Canada Life amendment remains secondary-only pending its primary amendment XML and acceptance record.

## Repository records

- Machine-readable audit: `PHASE669_FORM4_NOV27_LIVE_CAPTURE_AND_CROSSWALK_AUDIT_2026-11-27.json`
- Research state: `SMART_MONEY_RESEARCH_STATE_ADDENDUM_2026-11-27_PHASE669.md`
