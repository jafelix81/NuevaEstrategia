# Smart Money Research — state addendum (Phase 679)

**Updated:** 2026-11-28 05:00 UTC  
**Main HEAD after latest natural capture:** `3f7a6cc4968b372e7629d91ce4b79682fa54f12b`.

## Phase 679 — Form 144 post-Phase 673 natural-run validation

- Confirmed Phase 673 PR [#261](https://github.com/jafelix81/NuevaEstrategia/pull/261) merged at 00:38:02 UTC.
- First subsequent natural scheduled Phase 403 run [46110032075](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46110032075) completed both jobs successfully. Offline regression passed 103/103 tests.
- Live capture executed the post-capture Phase 665 PIT/plan-date join, Phase 560/565 10b5-1 refreshes, Phase 516 ledger audit and Phase 525 Form 144/Form 4 crosswalk.
- Both Form 144 and 144/A feeds completed with no pagination gap and no new accessions/events. 52 feed-observation rows were appended; these are poll observations, not new economic events.
- Structured backfill parsed 10 existing accessions and appended 46 rows with zero parse errors, unresolved records or source-hash mismatches. The queue has 128 event accessions remaining.
- Ledger: 1,104 event accessions; 976 structured-detail accessions; 6,360 detail rows; 908 research-observation-eligible accessions; 389 formal plan-date accessions; 146 distinct formal plan dates.
- Public-availability-certified accessions: 0. Signal-eligible accessions: 0.
- Refreshed crosswalk: 17 proposed-sale matches, 16 Form 4 accessions, 3 ambiguous transaction-reuse cases quarantined, 9 multi-owner accessions quarantined, 2 unresolved Form 144 acceptance clocks, 0 signal-eligible matches.
- This closes the natural-run integration confirmation left pending in Phases 676/677. It does not establish a predictive selling signal.

Full report: [Phase 679](PHASE679_FORM144_POST_PHASE673_NATURAL_RUN_VALIDATION_2026-11-28.md).

## Cross-source current state

- **FINRA Reg SHO:** run [46105917821](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46105917821) succeeded; one prospective symbol-panel date (2026-11-27), 327/335 symbols observed, 97.61% coverage. All rows remain signal-ineligible; raw source bytes are not persisted and the first-seen capture ran after the session close. Earliest daily-bar test session is 2026-11-30.
- **CFTC TFF:** run [46105422375](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46105422375) succeeded; no new report/revision; history remains 3,043 rows and the preregistered Russell OOS gates remain unmet.
- **SEC Form 4:** run [46099559273](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46099559273) succeeded; 156 new unique accession observations, but 0 research-observation-eligible and 0 signal-eligible rows. Backfills appended 32 transaction rows, 29 footnote references and 12 owner rows.
- **SEC 13F:** run [46084129349](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46084129349) succeeded; four new metadata accessions, no holdings downloaded and zero research/signal-eligible observations. AMS Capital's 13F remains a retrospective 1,000× unit candidate with only 7/15 rows price-checked; raw XML still needs hashing and complete row reconciliation.
- **SEC 13D/G:** Phase 616's 44-accession global-index sample remains the highest-priority free institutional-disclosure feasibility action. PR [#252](https://github.com/jafelix81/NuevaEstrategia/pull/252) merged the shared User-Agent fallback, but the live sample is manual-dispatch-only. The available GitHub connection can inspect runs/files but cannot dispatch this workflow. Required maintainer action: open Actions → “Phase 616 - SEC 13D/G global-index bounded identity sample” → Run workflow → set `run_live_sample=true`. No new credential should be necessary if the existing shared project contact is valid.
- **13F selector:** PR [#262](https://github.com/jafelix81/NuevaEstrategia/pull/262) remains a draft stacked on draft PR [#230](https://github.com/jafelix81/NuevaEstrategia/pull/230); neither should be merged before its dependency chain is reconciled.
- **Options / OPRA / Cboe:** no rights-cleared, reproducible historical options source has been admitted. No quote request, vendor contact or purchase.

## Strategy controls

- Signals promoted: **0**.
- Incremental alpha demonstrated: **none**.
- New valid OOS / bootstrap / LOO: **0**.
- `F80_TOP20_PARTIAL50_BASELINE_C20`: **frozen**.
- No production, universe, parameter, exposure, cost, capital or holding-period changes.
- Data spend: **USD 0**.

## Next priorities

1. Continue Form 144 detail backfill and preserve the 128 remaining accessions as unresolved until successfully parsed.
2. Run the existing bounded 13D/G live sample when the maintainer performs the required manual dispatch.
3. Accumulate FINRA prospective observations and resolve raw-source reproducibility, security identity and total-return labels before testing returns.
4. Continue Form 4 identity/transaction enrichment, but do not treat code-P rows or filing-level owner data as discretionary purchases without primary-document proof.
5. Complete the AMS Capital raw-XML and all-15-row reconciliation before any unit normalization.
