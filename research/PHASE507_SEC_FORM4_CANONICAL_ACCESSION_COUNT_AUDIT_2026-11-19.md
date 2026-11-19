# Phase 507 — SEC Form 4 canonical accession-count and poll-receipt audit

**Audit cutoff:** 2026-11-19 20:21 UTC  
**Main before Phase 507:** `2e0848589e05385c2b4cb4f759970493d9f1a5a2`  
**Source capture:** [Actions run 44598981676](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44598981676)  
**Artifact:** [14566842676](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44598981676/artifacts/14566842676)  
**Disposition:** SUCCESSFUL METADATA CAPTURE; 88 CANONICAL EVENTS; 0 RESEARCH-ELIGIBLE; SUMMARY COUNT SEMANTICS CORRECTED.

## 1. Preflight and run status

The repository Actions inventory contained 7,895 runs. The latest 100 were checked; none was queued, in progress, waiting, requested or pending at the cutoff. The latest scheduled run was Phase 476 / run 44598981676:

- Workflow: `.github/workflows/phase476_sec_form4_first_seen_capture.yml`
- Trigger: `schedule`
- Run started: 2026-11-19 19:30:17 UTC
- Run completed: 2026-11-19 19:31:25 UTC
- `offline-regression`: success
- `live-capture`: success
- Artifact: 769 bytes, not expired at audit time
- The run committed its append-only metadata to main as `2e0848589e05385c2b4cb4f759970493d9f1a5a2`.

The workflow declares `17 * * * 1-5`. This run began 13m17s after its nominal 19:17 UTC slot. The prior successful poll ended at 10:27:06 UTC, so the new receipt interval remained approximately 9h wide. No manual catch-up, rerun, cron change or duplicate capture was initiated. No later scheduled run was visible by 20:21 UTC.

## 2. Immutable capture reconciliation

The run polled Form 4 and Form 4/A Atom feeds and persisted 184 accession-observation rows:

| Feed | Accession observations | Prior watermark | Candidate occurrences | Same-feed duplicates | Cross-feed duplicates | Canonical new events |
|---|---:|---:|---:|---:|---:|---:|
| Form 4 | 177 | 1 | 176 | 88 | 0 | 88 |
| Form 4/A | 7 | 1 | 6 | 3 | 3 | 0 |
| **Total** | **184** | **2** | **182** | **91** | **3** | **88** |

The 88 canonical event accessions are unique. Their form breakdown is 85 original Form 4 and 3 Form 4/A amendments. All 88 have filing date 2026-11-19.

Page-level parser counts are not the same as consumed accession observations: the parser records the number of parsed entries in a fetched page, but once the prior watermark is reached it stops consuming the remainder of that page. In this run, 7 parsed entries after the Form 4 watermark and 37 after the Form 4/A watermark were intentionally not added to the accession-observation ledger. This is expected watermark behavior, not missing rows within the bounded poll.

## 3. Receipt clock and conservative use

All 88 canonical event rows are `BOUNDED_METADATA_ONLY`.

| Clock | Result |
|---|---|
| Previous successful poll lower bound | 2026-11-19 10:27:06 UTC |
| Earliest first-seen receipt upper bound | 2026-11-19 19:30:35 UTC |
| Latest first-seen receipt upper bound | 2026-11-19 19:31:19 UTC |
| Interval width | 543.48–544.22 minutes |
| Feed `updated` range | 2026-11-19 11:02:47–19:28:52 UTC |

The first-seen time is a collector receipt upper bound, not the exact instant of public availability. The feed `updated` field is not substituted for the collector receipt. Receipt occurred around 14:30:35–14:31:19 ET, during the regular session. Under the conservative rule “first regular-session open strictly after the receipt upper bound,” the first safe daily session for this cohort is **2026-11-20**. Same-day intraday use is not authorized.

## 4. Eligibility and interpretation

For all 88 new rows:

- public availability certified: 0;
- security identity verified: 0;
- historical F80 membership verified: 0;
- owner attribution verified: 0;
- transaction semantics verified: 0;
- research-observation eligible: 0;
- signal eligible: 0;
- acceptance timestamps fetched: 0;
- filing XML/text downloaded: 0;
- raw transaction rows persisted: 0.

This is a successful feed/receipt-metadata capture, not a sample of verified insider purchases and not an alpha result. Form 4 and Form 4/A remain metadata-only until the separate issuer/security-class, reporting-owner, transaction-row, amendment, footnote, public-availability and historical-universe gates pass.

## 5. Summary-metric defect discovered and corrected

The live log reported per-feed `new_accession_count` values of 176 for Form 4 and 6 for Form 4/A. Those values counted candidate **occurrences before deduplication**, not unique accessions newly appended to the canonical event ledger. The global `new_event_rows=88` was correct, but the per-feed field name was misleading and could overstate the event count by counting repeated feed entries.

Phase 507 corrects the capture summary without changing the append-only ledgers or watermark behavior:

- `candidate_accession_occurrence_count`: raw candidate occurrences before deduplication;
- `candidate_accession_count`: distinct accession IDs within the feed;
- `new_accession_count`: canonical new accessions actually emitted after existing-ledger and cross-feed deduplication;
- global `unique_candidate_accession_count` and `candidate_accession_occurrence_count` expose both grains;
- incomplete-poll suppression now reports unique candidate accessions and candidate occurrences separately.

For run 44598981676, the corrected interpretation is Form 4: 176 occurrences, 88 distinct candidates, 88 canonical new events; Form 4/A: 6 occurrences, 3 distinct candidates, 0 canonical new events because all three were already encountered in the Form 4 feed. The existing 88 canonical event rows are unchanged.

Regression coverage now explicitly tests same-feed repeats, cross-feed repeats, per-feed canonical attribution and fail-closed suppression counts.

## 6. Other source gates at cutoff

- **FINRA Consolidated Short Interest:** PR #159 remains draft. The historical Phase 31 panel is incomplete; Phase 447 async retrieval has no successful live validation. The existing manual single-settlement workflow still requires authorized FINRA credentials before a one-date live test. No batch history retrieval is authorized.
- **FINRA Reg SHO:** the last real capture remains run 44453548570, which used pre-Phase-495 code. Post-fix offline validation does not replace a real capture. Existing next windows were 22:30 and 23:30 UTC.
- **CFTC TFF:** the last reviewed capture retained 3,039 rows with no new report/revision. Existing next window was 22:25 UTC.
- **SEC Form 144:** latest scheduled capture 44521745535 was partial; later 44534689780 was PR CI only, not a new live capture.
- **Cboe options:** Volatility Surfaces remains a conditional historical IV/skew/term-structure candidate; OPRA Trades/Quotes and other products remain gated by coverage, first-receipt PIT, correction, licensing and price. No data were purchased.

## 7. Validation and frozen controls

The Phase 476 workflow path runs offline regressions on pull requests and does not execute its live-capture job on a pull-request event. Phase 507 updates only summary semantics and regression tests; it does not alter capture cadence, feed URLs, watermarks, event fields, persisted ledgers, security identity or eligibility rules.

No forward-return test, event study, backtest, OOS, bootstrap, LOO or holdout test was run. No signal was admitted.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen: universe, parameters, holding period, exposure, costs, holdout and production unchanged.
