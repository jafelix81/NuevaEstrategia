# Phase 533 — Post-Phase-525 SEC scheduled live-capture validation (2026-11-20)

## Executive disposition

The earlier SEC scheduled-capture delivery blocker is resolved by two natural scheduled runs after Phase 525 was merged. Both Form 4 and Form 144 workflows executed successfully on `main`; the Form 4 run executed the new owner-enrichment and crosswalk steps and created `reporting_owners.csv`.

This is an operational milestone, **not an alpha result**. Both collectors remain descriptive-only and signal-ineligible. The automated crosswalk produced zero matches in this bounded run; the current owner backfill has not yet reached the two Atea Form 4 accessions previously reviewed manually.

## Preflight

- Repository default branch: `main`.
- Main immediately before the two capture commits: `4e18bb55d675e44aa3bf98b41e1522720f639b69`.
- Latest main after both scheduled data commits: `c7080c0461885a92b7240597a711cebec3356814`.
- Latest Actions census: 7,980 total runs; the latest 100 contained no queued or in-progress run at the close of this audit.
- Both runs below were `event=schedule`, `head_branch=main`, `conclusion=success`.
- No manual dispatch, rerun, duplicate poll, or cancellation was made.

## Form 4 — Run 44794670480

[Run 44794670480](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44794670480) ran 2026-11-20 18:38:24–18:39:00 UTC.

Both jobs succeeded:
- `offline-regression`
- `live-capture`

The live job completed the Phase 525 owner-enrichment and crosswalk steps.

### First-seen metadata

- Form 4 feed: 91 new accessions; 91 canonical event observations.
- Form 4/A feed: no new accession.
- Two feeds polled successfully; 186 accession-observation rows persisted.
- No incomplete-poll candidates were suppressed and no feed error was reported.
- Latest Form 4 feed `updated`: 18:34:13 UTC.
- Poll interval: 18:38:38–18:38:51 UTC.
- The first-seen receipt is an upper bound, not exact public availability. Public availability remains uncertified.

### Structured transactions and owners

- Structured backfill: 10 accessions parsed, 27 detail rows appended, zero parse errors; 1,294 bounded accessions remain.
- Owner enrichment: 10 accessions parsed, 14 owner rows appended, zero parse errors.
- Owner mix: 9 single-owner filings and 1 multi-owner filing; the multi-owner filing remains quarantined for transaction-line attribution.
- Twenty bounded owner accessions remain in the current owner-enrichment queue.
- `research/data/sec_form4_first_seen/reporting_owners.csv` now exists (14 data rows).
- Transaction-line attribution is not verified; the owner sidecar is filing-grain identity only.

### Crosswalk

The Phase 525 crosswalk ran successfully but returned:
- 0 crosswalk rows / 0 matched Form 4 accessions.
- 20 Form 4 sale-disposition rows considered.
- 89 proposed-sale rows and 283 prior-sale rows considered from Form 144.
- 8 Form 144 amendment detail rows excluded.
- 1 multi-owner Form 4 accession quarantined.
- 0 signal-eligible matches; alpha testing remains unauthorized.

This zero-match result is **not a falsification of the previously manually reviewed Atea examples**. The two Form 4 accessions `0001193125-26-469037` and `0001193125-26-469038` are present in `transaction_details.csv`, and the corresponding Form 144 accessions `0001950047-26-011348` and `0001950047-26-011363` are present in `sale_details.csv`; neither Form 4 accession is yet present in the new owner sidecar. The bounded owner-enrichment step processed only 10 accessions, leaving 20 pending. Determine whether those Atea accessions are in that remaining queue before interpreting the automated crosswalk's zero count. Do not relax match keys or infer owner-to-line attribution.

Artifact: [phase476-sec-form4-first-seen — 14658766152](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44794670480/artifacts/14658766152), 2,807 bytes, SHA-256 `5bf866d1cfb19f59f9d5bda903ddc50e3f78d836229b1b9fcb5fea144f2a4f96`.

## Form 144 — Run 44796839433

[Run 44796839433](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44796839433) ran 2026-11-20 18:52:22–18:52:55 UTC.

Both jobs succeeded:
- `offline-regression`
- `live-capture`

### First-seen capture and acceptance reconciliation

- Form 144 and 144/A feeds both succeeded.
- 21 new event rows resolved; 53 feed-observation rows appended.
- 21 acceptance-date reconciliations added; zero unresolved.
- Zero failed feeds and zero possible feed-window gaps.
- The 144 feed returned 50 entries; the 144/A feed returned 3 entries, with one cross-feed overlap.
- The prior successful poll start was 10:35:01 UTC; the new poll began 18:52:36 UTC and completed 18:52:42 UTC.
- First-seen receipt is an interval upper bound; EDGAR acceptance time is not exact first public receipt.
- `public_availability_certified=false`, `same_day_intraday_use_authorized=false`, and `signal_eligible_count=0`.

### Structured detail backfill

- 10 accessions parsed; 110 detail rows appended; zero parse errors and zero source-hash mismatches.
- Ledger total: 121 accessions / 906 rows.
- 348 bounded accessions remain.
- No signal-eligible observations.

Artifact: [phase403-sec-form144-first-seen — 14658079177](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44796839433/artifacts/14658079177), 2,085 bytes, SHA-256 `e9a260c8216ddf1152d3316cf63d01e281142131037351624a6b6b280e4297c1`.

## Issue and operational disposition

The two successful natural schedule runs establish that both workflows are enabled and scheduled Actions are functioning on the default branch. The owner sidecar has been created. Close operational Issue [#185](https://github.com/jafelix81/NuevaEstrategia/issues/185) as completed.

Continue the existing schedules; do not dispatch duplicate polls. The next Form 4 scheduled run should continue the bounded owner-enrichment queue and rebuild the crosswalk. Verify whether the Atea accessions enter the sidecar. Do not treat a successful workflow or acceptance reconciliation as public-availability certification.

## Strategy controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- New signals admitted: 0.
- New alpha/forward-return tests: 0.
- New OOS, bootstrap, LOO or holdout tests: 0.
- Universe, parameters, exposure, costs, capital and production unchanged.
- SEC Form 4/Form 144 remain descriptive-only and signal-ineligible.
