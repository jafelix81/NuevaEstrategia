# Smart Money Research — state addendum (2026-11-20, Phase 513)

## Phase 513 — first scheduled live Form 4 structured-detail capture

- Existing Phase 476 scheduled run [44656159115](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44656159115) executed after Phase 510 merged to main. Both jobs succeeded; 50 offline tests passed.
- The Form 4 and Form 4/A metadata feeds both returned successfully. The poll persisted 1,001 accession-observation rows, including 457 new canonical Form 4 accessions, zero new Form 4/A accessions, 538 same-feed duplicate occurrences and five cross-feed duplicate occurrences. Duplicate feed observations are not extra filings.
- The Phase 510 structured backfill attempted 10 accessions, parsed all 10 with zero parse errors and zero unresolved fetches, and appended 22 detail rows (10 filing headers plus 12 transaction rows). The bounded queue reports 1,190 accessions remaining.
- The 10 accessions comprise nine Form 4 and one Form 4/A. Nine are single-owner filings; one multiple-owner filing remains quarantined without line-level attribution. Transaction codes were preserved as filing semantics (P=3, M=2, F=1, A=5, S=1); no code is treated as proof of an exchange-executed discretionary trade.
- The live parser pass is operational only. All 22 rows remain non-signal: public availability, security identity, historical F80 membership, owner attribution and transaction semantics are not verified; no research-observation or signal-eligible rows were produced.
- The first-seen interval is bounded by 2026-11-19 19:31:20 UTC and 2026-11-20 01:47:52 UTC. SEC acceptance timestamps are not treated as exact public dissemination timestamps. No same-day intraday use is authorized.
- A key provenance limitation is now measured rather than hidden: 0/22 rows have a comparable original XML hash because the earlier first-seen metadata ledger did not store original XML hashes. The parser correctly marks these as `NOT_COMPARABLE_NO_ORIGINAL_XML_HASH_IN_EVENT_LEDGER`; no hash match is claimed.
- Report: [Phase 513 live validation](PHASE513_SEC_FORM4_STRUCTURED_LEDGER_FIRST_LIVE_VALIDATION_2026-11-20.md) · [machine-readable summary](PHASE513_SEC_FORM4_STRUCTURED_LEDGER_FIRST_LIVE_VALIDATION_SUMMARY_2026-11-20.json).

## Other active research gates

- **CFTC TFF:** Phase 512 found that the archive `Updated` date is not a conservative global PIT publication bound. Historical TFF backtests remain unauthorized pending report-level publication-date reconstruction. Phase 512 is documented in open draft PR #165; prospective first-receipt capture remains the strict route.
- **CFTC coverage:** the Phase 377 audit run [44648241623](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44648241623) passed the data/schema coverage audit (47,420 rows, 90 fields, 1,066 report dates through 2026-11-10). Coverage does not repair the publication-time gate.
- **FINRA Reg SHO:** latest real capture remains run 44453548570, before the Phase 495 parser change; a post-Phase-495 real capture is still required.
- **FINRA Consolidated Short Interest:** asynchronous retrieval pilot remains blocked on authorized credentials and a complete first snapshot.
- **SEC Form 144:** latest successful scheduled capture is run 44614323236, before Phase 509 merged. The main-branch `sale_details.csv` is absent; validate via the existing Phase 403 schedule rather than dispatching a duplicate.
- **OptionMetrics Dividend Gap:** remains a conditional data-feasibility candidate; no data purchase, PIT reconstruction, or model test is authorized yet.

## Strategy disposition

- No new signal admitted; no returns/event study/backtest/OOS/bootstrap/LOO or holdout test was run in Phase 513.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Universe, parameters, exposure, costs, holding rules, holdout and production are unchanged.
- Next: continue the existing Phase 476 bounded backfill; inspect the next existing Phase 403 scheduled run for Phase 509 live validation; keep the Form 4 parser's eligibility flags fail-closed; resolve security identity, historical universe membership, public-availability provenance and original-hash limitations before any predictive test.
