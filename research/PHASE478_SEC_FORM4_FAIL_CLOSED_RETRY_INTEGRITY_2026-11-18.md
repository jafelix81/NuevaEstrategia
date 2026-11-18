# Phase 478 — SEC Form 4/4-A fail-closed timestamp and retry integrity hardening

**Audit cutoff:** 2026-11-18 11:13 UTC  
**Base main:** `b17b5c53d3dcc16d8bed70a64e7a292989988801`  
**Disposition:** fix two latent collector defects before the first scheduled Phase 476 live poll. No live feed was fetched or modified in this phase.

## 1. Preflight

- Repository default branch is `main`; main HEAD was `b17b5c53d3dcc16d8bed70a64e7a292989988801`.
- Actions inventory: 7,836 total runs. Explicit `in_progress` and `queued` queries returned 0/0.
- Latest Phase 476 PR CI [44292113931](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44292113931) completed successfully at 11:09:51 UTC. Its `offline-regression` job passed; `live-capture` was skipped as designed; no artifact was produced.
- The run's job log showed the mocked two-poll bounded-metadata test, but the suite did not cover timezone-less Atom timestamps or a failed-pagination candidate followed by a successful retry.
- No Phase 478 branch existed at preflight. No workflow was active or queued, and no run was dispatched.
- The Phase 476 schedule is `17 * * * 1-5` UTC. At this cutoff the next slot (11:17 UTC) had not occurred; there is no live Form 4/4-A baseline yet. The workflow's administrative enabled state is not exposed by the available read interface.

## 2. Defect A — timezone-less timestamps were silently interpreted as UTC

Phase 477 states that an Atom `updated` value must include an explicit timezone. However, Phase 476's `parse_utc` assigned UTC to a naive ISO datetime. A source value such as `2026-11-18T10:30:00` could therefore pass the event interval check if its clock text fell between the previous poll and local receipt.

That behavior contradicted the stated fail-closed rule. It also made an undocumented timezone assumption at the exact point where the collector is trying to establish temporal consistency.

**Correction:** `parse_utc` now returns `None` whenever the parsed datetime has no explicit UTC offset. Only timezone-aware values are normalized to UTC. A missing/naive Atom timestamp is classified as `FEED_OR_RECEIPT_TIMESTAMP_UNKNOWN`.

## 3. Defect B — candidates from incomplete pagination poisoned the canonical dedup ledger

When a prior accession watermark existed but pagination failed to reach it, `fetch_feed` correctly marked the poll unsuccessful and did not advance the watermark. However, it still returned entries collected before the failure. `run_capture` appended those rows to the canonical `events.csv` and `existing_accessions()` subsequently treated them as permanently seen.

A later successful poll could then find the watermark and establish a complete interval, but the accession would be skipped because the earlier incomplete poll had already inserted it into the canonical dedup set. The record remained ineligible, but the retry could not repair it. This was a lossy append-only failure mode.

**Correction:** canonical event rows are now emitted only when the feed poll succeeds (baseline polls without a prior watermark remain valid baseline captures). For incomplete polls, the collector retains page-level observation metadata, reports candidate and suppressed-candidate counts, leaves the last successful watermark/end unchanged, and does not add candidate accessions to the canonical event ledger. A later complete retry can then evaluate and record the accession against the unchanged last-successful interval.

This is conservative: no candidate from a partial poll is promoted, no watermark is advanced, and no signal is created.

## 4. Regression coverage

The Phase 476 suite now adds:
- explicit rejection of a timezone-less Atom timestamp;
- an end-to-end baseline → incomplete pagination → successful retry case;
- stronger assertions that an incomplete poll writes no canonical event row and that a later complete retry can record the same accession as bounded metadata.

The suite is expected to contain 37 tests (35 existing + 2 new). CI results will be reported only after GitHub Actions completes. The test suite remains offline and uses mocked feed responses.

## 5. Scope and controls

- No live SEC request, manual dispatch, schedule change, filing XML/text download, transaction-row extraction, owner attribution, or price download.
- No changes to the SEC feed endpoints, poll cadence, pagination limit, or watermark policy.
- `BOUNDED_METADATA_ONLY` remains metadata-only; it does not certify exact public availability.
- `research_observation_eligible`, `signal_eligible`, and same-day intraday authorization remain false.
- No event study, backtest, alpha, OOS, bootstrap, LOO, or holdout test.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, the 335-name universe, parameters, capital, exposure, costs, holdout and production remain frozen.

## 6. Next gate

Merge only after the offline CI passes. Then allow the existing 11:17 UTC scheduled run to create the initial baseline; do not manually dispatch a duplicate. The following successful scheduled poll must find the baseline accession watermark before any event can be classified as bounded metadata. Continue to quarantine all source timestamps without an explicit timezone.
