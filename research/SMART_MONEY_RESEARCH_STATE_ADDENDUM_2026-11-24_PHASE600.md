# Smart Money Research state addendum — Phase 600 (2026-11-24 17:14 UTC)

Main HEAD before documentation: `0fc20749b411f8965e85735dfd87345ca14ff049`.

## Operational
- 8,110 Actions runs; latest 100 = 90 success / 10 failure; 0 in-progress, queued, waiting or requested.
- 380 branches, 72 open PRs, 96 workflows, 495 research entries.
- Latest Form 144 schedule event: [45437675674](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45437675674), created 16:29:14 UTC. Both jobs succeeded; three unexpired artifacts inspected and downloaded.
- Form 144's declared cron remains `47 * * * *`; the 16:29 run is consistent with a delayed 15:47 event (~42 minutes late). The 16:47 slot was not visible by cutoff.
- Form 4's declared cron remains `17 * * * 1-5`; the 16:17 slot is absent. Persisted state still points to [45332760566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566), poll end 05:22:13 UTC.
- Issue #194 remains open. No manual dispatch, rerun, cron change or replacement workflow.

## Form 144 capture
- 27 new accession events, 53 feed observations, 27 XML resolutions, 32 acceptance reconciliations added / 0 unresolved, no feed errors or pagination gap.
- First-seen interval lower bound 05:00:47 UTC, upper bound 16:29:37 UTC (11h28m50s). Bounded poll receipt, not exact public availability.
- Current ledger: 514 accessions / 3,549 detail rows; +130 new detail rows and +59 backfill rows; 228 backfill accessions remain; zero parse/hash errors.
- Four candidate-manifest matches: JD.com, Axon Enterprise, Amazon and Verizon. The 290-CIK manifest is not a historical F80 security master. No matching issuer CIK appears in the current 61-row Form 4 owner sidecar / 199-row transaction ledger.
- Phase 549: 183 formal plan dates across 91 dates; median 183 days before notice; 16 sell-to-cover/tax-withholding accessions; four Fermi negative-control notices totaling 2,253,270 proposed units. Zero signal eligibility.

## Other sources
- Form 4: 516 new canonical accessions, 1,239 observations, +24 transaction rows, +11 owner rows; 2,273 transaction backfills and 20 owner enrichments pending; zero eligible.
- FINRA Reg SHO: six files rejected (BCPC/TPC repeated), 12 extra rows, zero valid/eligible; raw volumes not persisted.
- CFTC TFF: 3,043 rows, no new reports/revisions; no signal.
- Databento OPRA remains conditional; IvyDB TradeFlow remains the leading direct-flow hypothesis; ORATS remains context-only. No sample/license/account/data purchase.

## Decision
- No new signal, event-return study, backtest, OOS, bootstrap or LOO.
- No universe/exposure/cost/parameter/holdout/production changes.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- Full audit: [Phase 600](PHASE600_SEC_FORM144_CAPTURE_RECOVERY_AND_FORM4_CADENCE_GAP_AUDIT_2026-11-24.md).
