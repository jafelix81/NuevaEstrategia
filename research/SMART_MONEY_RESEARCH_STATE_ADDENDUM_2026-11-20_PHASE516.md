# Smart Money Research state addendum — Phase 516 (2026-11-20)

- Main HEAD at preflight: `cca5224c0980d6b0765b203ea618a335d9b88510`.
- Audited the committed SEC Form 144 structured ledger after scheduled run [44662324343](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44662324343), together with prior capture [44614323236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44614323236).
- The ledger contains 596 parsed detail rows across 80 filing headers and 61 issuer CIKs. All 596 source XML hashes match the event ledger. The 80 filing headers comprise 79 Form 144 and one Form 144/A.
- All 80 proposed-sale rows have numeric proposed units, aggregate value, class units outstanding and an approximate sale date. There are 169 acquisition-lot rows and 267 prior-three-month sale rows across 49 filings; the 31 `nothing to report` flags reconcile exactly.
- **Formal Rule 10b5-1 plan date is not the same field as a free-text Remarks keyword.** 27 filings have the formal plan-adoption/instruction date; only six mention 10b5-1 in Remarks; two overlap. The formal date is the primary explicit field in SEC Form 144; Remarks remain a separate semantic field. Formal plan dates precede notice by 72–528 days (median 183).
- Three proposed-sale rows have approximate sale dates before the notice date. One is a Form 144/A amendment whose Remarks explicitly say a Rule 10b5-1 plan was terminated and no further sales will be made; it is a termination/completed-sales event, not a fresh forward-supply event. Two other past-date filings remain in manual review.
- First-seen intervals are upper bounds, not exact publication timestamps: 70 filings in run 44662324343 have a 5.6531-hour interval; ten filings in run 44614323236 have an 18.1647-hour interval. Public availability certified = 0; signal eligible = 0.
- Added a reproducible audit script and tests. Phase 403 PR CI now runs the audit against the committed ledger; the PR job remains offline-only and does not execute a live capture.
- No returns, event study, backtest, OOS, bootstrap, LOO or holdout test. No signal admitted. `F80_TOP20_PARTIAL50_BASELINE_C20` and production remain frozen.
