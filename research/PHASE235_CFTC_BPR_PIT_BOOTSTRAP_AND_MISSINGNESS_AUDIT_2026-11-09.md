# Phase 235 — CFTC BPR capture PIT bootstrap, event/state semantics, and missingness hardening

**Date:** 2026-11-09  
**Decision:** \`CONDITIONAL_PROSPECTIVE_REGIME_RESEARCH_ONLY\`  
**Production baseline:** \`F80_TOP20_PARTIAL50_BASELINE_C20\` unchanged

## Executive decision

Phase 234 correctly avoided backdating BPR observations to the report date and recorded the actual pipeline page-receipt timestamp. The review found that the initial scheduled capture needed a clearer distinction between a **pre-existing baseline state** and a **newly published report event**. A first capture after activation can be safely used as a state snapshot only from its actual receipt time, but it must not be counted as a new release event or used to claim an event-time observation at the report date.

Phase 235 also found that the BPR parser converted blank long/short positions and percentage fields to numeric zero. The current CFTC page demonstrates that true zero positions are explicitly printed as \`0\`, while bank counts may be blank because of confidentiality suppression. The parser now preserves every blank numeric field as \`UNKNOWN\` and keeps explicit numeric zero as zero.

The capture workflow has not run and no BPR data snapshot has been captured. These are pre-activation hardening changes, not a correction to any live historical dataset.

## Repository / Actions pre-check

Before editing, inspected the latest 100 Actions runs, the latest Phase 231 job steps and full logs, its artifact, the only failed run's job/log/artifact, PR metadata, branch inventory, and Phase 234 source files.

- Latest 100 runs: **87 success, 1 failure, 12 cancelled; 0 queued/in-progress**.
- Latest completed run: Phase 231 run \`42568771468\`, success.
- Job: \`full-row-reparse\`; all 9 test/processing steps completed successfully.
- Artifact: \`13651429847\`, SHA-256 \`b65e594b48b1467bf22aefecf7b9afab78f4a18e2caf47e30569a57453f0a924\`, 2,422 bytes, metadata-only.
- The first Phase 231 attempt \`42568562899\` failed its final gate because \`archive_integrity_match\` was false; later attempts \`42568758485\` and \`42568771468\` succeeded. This was not a BPR failure.
- 131 branches were enumerated (100 on page 1, 31 on page 2).
- PR #13 and PR #14 remained open and unmerged. PR #14 head was \`8b181c4d1ca6866238604417082e56c9b8bfcb90\` before Phase 235 changes.
- No active workflow was duplicated or rerun.

## Official source verification

Official CFTC pages were inspected on 2026-11-09:

- [BPR index](https://www.cftc.gov/MarketReports/BankParticipationReports/index.htm)
- [November 2026 futures report](https://www.cftc.gov/MarketReports/BankParticipation/deanov26f)
- [Release schedule](https://www.cftc.gov/MarketReports/BankParticipationReports/ReleaseSchedule/index.htm)
- [Explanatory notes](https://www.cftc.gov/MarketReports/BankParticipationReports/ExplanatoryNotes/index.htm)

The live index lists November 2026 first, then October 2026 and earlier months. The November report identifies report date \`11/3/2026\`; the tentative schedule lists release date \`11/6/2026\`. The explanatory notes state that BPR is monthly and that CFTC retains only the most recent 25 months. The report table shows explicit numeric zero positions (for example, the November report's U.S. bank row for CBT DJIA x $5) and also shows blank bank-count cells in categories where counts are suppressed. Blank counts are not zero counts.

The exact first public receipt time is still not established by the report page or schedule. The capture pipeline's own page-receipt timestamp is therefore a conservative **system-availability** timestamp, not a claim about the CFTC's original publication second.

## Findings and fixes

### 1. Baseline state versus release event

A first scheduled capture may encounter a report that was already public before the workflow was activated. The previous code stored the receipt timestamp, so it did not need to backdate availability; however, the metadata did not clearly distinguish a baseline state from a newly indexed report event.

Protocol v2 now records:

- \`initial_baseline=true\` and \`event_type=INITIAL_BASELINE_STATE_ONLY\` for the first scheduled report.
- \`prospective_state_usable_after_receipt=true\` when the scheduled receipt is on a weekday at/after 15:30 ET. It may serve as a starting state only after the actual receipt timestamp.
- \`event_signal_eligible=false\` and \`pit_eligible_from_pipeline_receipt=false\` for the baseline. It is not a newly published event and cannot be backdated to the report date.
- Newly indexed report URLs and observed revisions after the baseline can be event/PIT candidates from their own report-page receipt timestamp, subject to the scheduled weekday/time gate.
- Manual dispatches remain non-PIT and do not advance the scheduled index baseline.
- Legacy protocol-v1 metadata cannot suppress the v2 bootstrap; a fresh baseline is required.

This is an event/state classification correction. No Phase 234 scheduled capture had run, so no live observation was mislabeled.

### 2. Blank numeric fields remain UNKNOWN

\`parse_bank_row\` now preserves blanks in bank count, long/short positions, percentages, and open interest as \`None\`. Explicit \`0\` remains numeric zero. Negative positions and negative percentages fail closed.

Combined bank net may be calculated from the explicit total row when both total long and total short are observed. If category rows are complete, their sums can reconstruct the total and are reconciled against any observed total-row values. A category breakdown remains unknown if any category position is blank. A positive market open-interest denominator is mandatory for net/OI.

### 3. Index selection and catch-up coverage

- Futures URLs are parsed and sorted by report month encoded in the CFTC URL, not assumed to be in HTML order.
- Conflicting URLs for the same report month fail closed.
- The report date month must match the URL's encoded month.
- Protocol v2 stores append-only raw index HTML plus a normalized futures-link set/hash and receipt metadata whenever the link set changes.
- Each scheduled run compares the full link set, captures every newly appearing report URL (including multiple catch-up links), and re-fetches the latest report page to detect a latest-page revision.
- Older, non-latest report pages are not polled continuously for later revisions; this remains a documented limitation.

## Validation

Local tests:

- Phase 234 capture regression suite: 13 tests.
- Phase 235 new tests: 10 tests.
- **23/23 passed**, 0 failures, 0 errors.
- Tests cover initial baseline state-only semantics, legacy metadata, manual versus scheduled capture, new report URLs, multiple catch-up links, revisions, URL/date consistency, blank versus explicit-zero semantics, total-only versus category-level coverage, reconciliation, and invalid values.

No hosted Phase 235 workflow was run. The commits are marked \`[skip ci]\` to avoid broad PR workflow fan-out. Local tests are not represented as GitHub Actions results.

## Current BPR admission decision

| Gate | Result |
|---|---|
| Official source semantics | PASS |
| Broad equity-index futures coverage | PASS |
| Long historical archive | FAIL (25-month rolling public retention) |
| Exact historical CFTC first-publication vintages | FAIL |
| Pipeline receipt timestamp after activation | IMPLEMENTED, not yet observed |
| Initial baseline usable as state after receipt | CONDITIONAL; not an event signal |
| Newly indexed report/revision event capture | IMPLEMENTED, awaiting default-branch activation |
| Stock-level universe coverage | FAIL / not applicable |
| Predictive alpha | NOT TESTED |
| Production admission | NO |

**Final status:** \`CONDITIONAL_PROSPECTIVE_REGIME_RESEARCH_ONLY\`.

\`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen. No BPR capture, backtest, holdout use, vendor purchase, production change, or universe change occurred.
