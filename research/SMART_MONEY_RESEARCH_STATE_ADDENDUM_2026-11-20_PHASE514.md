# Smart Money Research state addendum — Phase 514 (2026-11-20)

Both SEC structured-detail pipelines have now completed scheduled live runs after integration:

- Form 4: [run 44656159115](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44656159115), artifact 14592859142. 10 accessions parsed, 22 rows appended, zero parse errors; 1,190 remain. All rows are non-signal and XML hashes are non-comparable because the original event ledger did not store them.
- Form 144: [run 44662324343](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44662324343), artifact 14595524069. 10 accessions processed in this run, 54 rows appended, zero parse errors; persisted ledger now has 80 accessions / 596 rows across 61 issuers, with all 596 source XML hashes matching the event ledger; 368 remain.

Both workflows' offline and live jobs succeeded. Both datasets retain bounded first-seen intervals rather than exact public-availability timestamps. Form 144 rows have public-availability and signal flags false despite the separate ingestion/research-observation flag. Form 4 rows remain ineligible for research observation and signal. No same-day intraday use is authorized.

Issue #136's recurring scheduled-delivery gap is operationally resolved. The bounded backfill queues remain open. No backtest, event study, OOS, bootstrap or LOO was run; no new signal admitted. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
