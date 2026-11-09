# Phase 242 — CFTC BPR/TFF capture-vintage completeness and event-promotion hardening

**Date:** 2026-11-09  
**Branch:** `phase231-cboe-option-quotes-full-row-reparse`  
**Hosted validation:** [Run 42669436293 — success](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42669436293)  
**Status:** `CFTC_CAPTURE_PIT_STATE_HARDENED_NO_RAW_CAPTURE`  
**Scope:** code-path audit and regression tests for prospective capture only. No CFTC or SEC network data was retrieved in this phase.

## Executive decision

Phase 240 corrected three real state-machine defects, but a follow-up review found residual ways for the prospective CFTC panel to lose revisions or mislabel an already observed report as a new event.

1. **BPR did not poll older retained report pages.** Scheduled runs fetched newly indexed URLs and re-fetched the latest report, but did not re-fetch earlier report URLs. A correction to an older, non-latest monthly report could therefore remain invisible.
2. **BPR could promote a manual observation.** After a scheduled baseline, if a new report was first seen by a manual dispatch, its later scheduled receipt could be classified as a new report event even though the pipeline had already observed that report version.
3. **TFF had the analogous manual-promotion path.** The latest scheduled state ignored manual metadata. A manually observed newer report could later be treated as a fresh scheduled event.

These are data-availability and vintage-integrity defects, not evidence for or against predictive value. They are now guarded by new protocol versions and regression tests.

## 1. BPR protocol v3

### Complete retained-archive polling

The CFTC BPR index exposes a rolling archive of approximately 25 months. The revised scheduled capture now:

- On the first scheduled v3 run, fetches every currently indexed Futures report and stores each as `INITIAL_BASELINE_STATE_ONLY`. None is backdated to its report date or treated as a new release event.
- On every later scheduled run, re-fetches every Futures report URL still present in the index, not just the latest page and newly appearing URLs.
- Appends a new raw hash and metadata record whenever a previously observed report page changes.
- Classifies revisions to older or current report dates as state-only; a revision cannot create a directional event.
- Allows a never-before-observed newly indexed report to qualify only from the scheduled pipeline receipt, subject to the weekday 15:30 ET timing gate.

This adds roughly one request per retained monthly page per weekday poll. It is a small bounded archive, not a full-history bulk download. URLs that have already rolled out of the CFTC's retained index are no longer polled.

### Manual and prior-protocol observations

A version already present in metadata—whether from a manual dispatch or an earlier capture protocol—cannot be promoted into a new scheduled event merely because the current protocol observes it again.

Manual dispatch remains non-PIT and does not advance the scheduled index baseline. A later scheduled receipt can establish a conservative usable state, but the version is not re-labelled as a newly released event.

The protocol was bumped from v2 to v3. The first v3 scheduled observation is a fresh state-only bootstrap across all currently retained report URLs.

## 2. TFF protocol v2

TFF continues to capture the two current CFTC streams separately:

- `FinFutWk.txt` — futures-only;
- `FinComWk.txt` — futures-and-options combined.

The protocol was bumped from v1 to v2. Before classification, the capture checks whether the current report date has already appeared in the current protocol's metadata. If so, a later scheduled receipt is state-only rather than a new report event.

This closes the path where a manual observation of a newer report could be ignored by the scheduled-state selector and then promoted when the same report was downloaded on a later scheduled run. The first scheduled v2 observation remains a baseline, not an event; same-date revisions remain state-only; rollbacks remain non-PIT.

The current TFF files are still the latest stream snapshots. This phase does not create a historical weekly receipt archive or recover historical first-publication times.

## 3. Hosted validation

<badge color="success">47/47 tests passed</badge>

| Suite | Result |
|---|---:|
| BPR capture | 16/16 |
| TFF capture | 31/31 |
| **Total** | **47/47** |

The hosted workflow compiled all four modules and test files, then ran both suites. It was the existing Phase 240 workflow; no duplicate workflow was added.

The first run on the new code exposed a test expectation mismatch: the test compared the returned receipt-kind string with the internal event-type string. The implementation already returned a state-only receipt; the assertion was corrected, and the final hosted run passed both suites.

## 4. Remaining limitations

- No raw CFTC capture was executed. The workflow remains inactive on `main` until the stacked PR chain is merged.
- The first scheduled BPR bootstrap will preserve the current rolling archive only from the actual pipeline receipt. It cannot reconstruct historical publication vintages or create a historical PIT backtest.
- BPR polling covers only URLs still present in the current CFTC index. It cannot monitor reports after they roll out of the approximately 25-month archive.
- TFF historical release dates remain incomplete; the CFTC's reported position date is not its public-availability timestamp.
- The pipeline receipt is a conservative known-by time, not proof of the exact first public second.
- BPR and TFF are aggregate bank/trader-category positions in equity-index futures, not stock-level flows or verified beneficial-owner identities. They remain market-regime candidates only.

## 5. Research controls and disposition

- No return, bootstrap, leave-one-out, walk-forward, or OOS test.
- No holdout use; the legacy holdout remains `CONSUMED_NOT_PRISTINE`.
- No data purchase, vendor contact, production or universe change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

**Decision:** retain BPR/TFF as conditional prospective market-regime measurement candidates. Their historical PIT and alpha gates remain closed. No Smart Money feature is admitted and no strategy parameter changes.

