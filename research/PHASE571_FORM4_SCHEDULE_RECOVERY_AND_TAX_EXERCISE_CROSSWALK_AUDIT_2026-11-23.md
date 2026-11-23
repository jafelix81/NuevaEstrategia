# Phase 571 — SEC Form 4 scheduled recovery, first-seen metadata and ATEA crosswalk audit

**Audit cutoff:** 2026-11-23 08:00 UTC  
**Repository:** `jafelix81/NuevaEstrategia`  
**Main HEAD at capture completion:** `bfadf949333f30557148979b31fbce9ca04df6b1`  
**Prior research checkpoint:** Phase 570, `18db199089eb3603d779ca4789d0ea55a11b31ae`

## Executive disposition

The Phase 476 SEC Form 4 scheduled collector completed one natural run after the previously observed delivery gap. This is a real recovery of prospective metadata capture, not proof of uninterrupted scheduling. It observed 28 new Form 4 accession IDs and persisted the append-only observation ledger. It did **not** certify exact public availability, download filing XML for the new accessions, or admit any row as a research signal.

The same run's bounded historical enrichment produced a useful descriptive crosswalk: two ATEA Pharmaceuticals Form 4 accessions matched two proposed Form 144 sale events, and one additional prior-sale row matched. The matching quantities and reported/gross values reconcile closely. However, remarks indicate option-exercise, exercise-price and tax-planning/withholding context; execution intraday time is unknown, historical F80 membership is unverified, and public-availability clocks are not certified. Treat these as a crosswalk/parser validation and a negative-control candidate, **not discretionary insider selling or alpha**.

## 1. Natural Form 4 run: jobs, logs and artifact

Run: [45133809578](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578)  
Created: 2026-11-23 07:48:40 UTC; completed: 07:49:00 UTC.  
Workflow cron on main: `17 * * * 1-5`; the run appeared 31m40s after the nominal 07:17 UTC minute.

Both jobs succeeded:
- `offline-regression`: 62/62 unit tests passed.
- `live-capture`: capture, structured-detail backfill, owner enrichment, crosswalk, append-only commit and artifact upload all succeeded.

Artifact: [14798359037](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578/artifacts/14798359037)  
Artifact ZIP SHA-256: `55a7d8fa26c06b523318c5b7e829d396a7afbcfadcdf181904ad834c18297033`.

### First-seen metadata poll

From `phase476_output/poll_summary.json`:
- 2 feeds (Form 4 and Form 4/A) polled successfully; watermark-bounded intervals; no page errors or incomplete-poll suppressions.
- 28 unique new candidate accession IDs; 57 candidate accession occurrences; 59 accession-observation rows including 2 pre-existing observations; 28 canonical event-observation rows.
- 29 repeated same-feed accession occurrences; 0 cross-feed duplicate occurrences. Repeated occurrences are not 29 additional distinct filings.
- Poll began 2026-11-23 07:48:51 UTC and ended 07:48:52 UTC.
- Latest SEC feed `updated` timestamp in the Form 4 feed was 2026-11-21 02:48:30 UTC; the new accession filings carry filing date 2026-11-20.
- The collector persisted metadata, but `filing_xml_or_text_downloaded=false`, `raw_transaction_rows_stored=false`, `public_availability_certified=false`, and `signal_eligible_rows=0`.

**PIT interpretation:** the poll's first-seen timestamp is our first observed time after the gap, not proof of the SEC's exact first-public timestamp. Use it only as a conservative collector-observation clock; do not backdate knowledge to filing date, transaction date, or feed `updated` time.

### Bounded enrichment

- Phase 510 structured detail: 10 accessions attempted and parsed; 39 detail rows appended; 0 parse errors; 0 unresolved fetches; 1,776 bounded accessions remain in the structured-detail queue; 0 signal-eligible.
- Phase 525 owner identity: 10 accessions parsed; 10 filing-level owner rows appended; 0 parse errors; 20 bounded owner accessions remain; transaction-line attribution remains unverified; 0 signal-eligible.
- The scheduled run committed append-only data as `bfadf949` (`[skip ci] SEC Form 4 first-seen metadata 45133809578`), 6 files changed, 148 insertions and 10 deletions.

## 2. Descriptive ATEA Form 144 / Form 4 crosswalk

The artifact `phase525_output/form144_form4_crosswalk.csv` contains three reconciled rows:

| Role | Reporting owner | Form 4 transaction date | Shares | Code | Form 144 reported value | Form 4 gross value | Difference |
|---|---|---:|---:|---|---:|---:|---:|
| Proposed sale | Bruce Polsky | 2026-11-19 | 8,750 | S / D | $35,299.25 | $35,298.3750 | +$0.8750 |
| Proposed sale | Bruno Lucidi | 2026-11-19 | 22,619 | S / D | $89,219.37 | $89,220.6455 | -$1.2755 |
| Prior sale history | Bruno Lucidi | 2026-11-17 | 6,741 | S / D | $27,189.82 | $27,189.8235 | -$0.0035 |

All three rows are ATEA Pharmaceuticals, Inc. The two proposed-sale Form 144 accessions were accepted on 2026-11-19 before the corresponding Form 4 accessions were accepted on 2026-11-20. This establishes filing-order metadata, **not execution intraday time**.

Form 4 remarks flags mention option exercise, exercise-price payment, tax withholding and tax planning; they do not mention open-market trading or Rule 10b5-1 in these matched rows. The exact value reconciliation is useful evidence that the issuer/owner/date/quantity crosswalk works for these cases, but the economic context is not a clean discretionary-insider-sale observation.

Crosswalk summary:
- 3 descriptive crosswalk rows.
- 2 matched Form 4 accessions.
- 2 proposed-sale matches and 1 prior-sale-history match.
- 0 signal-eligible matches.
- Historical F80 membership not verified.
- Execution intraday time unknown.
- Filing-level single-owner identity does not establish transaction-line owner attribution.

**Disposition:** retain as a descriptive crosswalk validation and tax/option-exercise negative-control case. Do not use as a bearish insider signal or as an alpha event.

## 3. SEC scheduled-delivery recheck

The repository-wide Actions API snapshot at the cutoff:
- 8,073 total runs.
- Latest 100: 96 success / 4 failure.
- 0 active or queued runs.
- 373 branches.
- 72 open PRs.

Form 4 has one successful natural recovery: [45133809578](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578). It does not prove every missed hourly weekday slot ran; the observed run was delayed relative to its cron minute.

Form 144 / Phase 403 remains unresolved:
- Cron on main: `47 * * * *`.
- Latest natural schedule run still [45085664016](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016), 2026-11-22 23:53:30 UTC.
- At 08:00 UTC on 2026-11-23, schedule slots 00:47 through 07:47 UTC are not present in the repository-wide latest-run inventory.
- No natural post-Phase-565 Form 144 run or Phase 549 post-capture artifact has yet been validated.

This remains an observed delivery/visibility gap, not proof that the workflow is administratively disabled. The connected API cannot inspect repository Actions enablement or schedule-permission settings. No manual dispatch, rerun, cancellation, cron edit or duplicate poll was performed.

Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) records the continuing human check.

## 4. Open research PRs — no stale merges

Current PR status/compare against main:
- #204 SEC FTD credentials: Draft, 11 ahead / 27 behind, diverged.
- #159 FINRA short interest PIT: Draft, 7 ahead / 150 behind, diverged.
- #200 Cboe options: Draft, 5 ahead / 47 behind, diverged.
- #201 SEC MIDAS: Draft, 2 ahead / 47 behind, diverged.
- #199 Form 4 crosswalk: Draft, 5 ahead / 47 behind, diverged.
- #188 Massive Options: Draft, 5 ahead / 91 behind, diverged.
- #186 ThetaData: Draft, 3 ahead / 94 behind, diverged.

No PR was merged or rebased. No new workflow was created.

## 5. Research decision and next gates

- New signals admitted: **0**.
- Incremental alpha / return test / event study / OOS / bootstrap / LOO: **none**.
- Form 4 first-seen metadata is a prospective observation ledger, not a reconstructed historical PIT panel.
- Keep Form 4 sales, proposed Form 144 sales, option exercise, tax withholding and Rule 10b5-1 plan contexts separate.
- Next SEC gate: validate the first natural post-Phase-565 Form 144 capture and its same-run Phase 516/549 post-capture artifact; verify Phase 403/476 schedule enablement in GitHub Settings → Actions.
- Next FINRA gate remains the authorized one-settlement Phase 447 validation for settlement 2026-11-13 after the 2026-11-24 publication; credentials and permitted-use terms remain prerequisites.
- Keep `F80_TOP20_PARTIAL50_BASELINE_C20` frozen. No universe, exposure, costs, holding rules, holdout or production changes.

