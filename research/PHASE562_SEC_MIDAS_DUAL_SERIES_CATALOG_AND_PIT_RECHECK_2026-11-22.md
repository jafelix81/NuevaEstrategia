# Phase 562 — SEC MIDAS dual-series catalog and PIT recheck

**Audit cutoff:** 2026-11-22 21:17 UTC  
**Main HEAD:** `20c7ab10690ce327195d235d804bb2864c26d2d1`  
**Disposition:** catalog/source audit only. No ZIP payload was downloaded, no PIT clock was established, and no signal or return test is authorized.

## 1. Actions and repository preflight

- Actions total: 8,069.
- Inspected four pages of 30 latest runs (120 total): 116 successes, 4 failures, zero active/queued/waiting/requested runs. The latest 100 are 96 successes / 4 failures. The two failures in the newest page are the initial Phase 44 offline-test attempts; later bounded Phase 44 runs succeeded.
- Repository: 372 branches across four pages; 72 open PRs.
- Latest 30 runs end with Phase 560 PR checks at 18:39:52 UTC. The latest natural scheduled Form 144 run remains [45052961790](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45052961790), created 18:04:20 UTC. No later `event=schedule` run is present in the latest 120-run inventory.
- Form 144 run [45052961790](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45052961790): `offline-regression` and `live-capture` succeeded; artifact [14765739720](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45052961790/artifacts/14765739720) is present. The live log shows the post-capture ledger reconciliation passed, the append-only ledger commit was pushed, and artifact upload completed. The run's audited state is 285 accessions / 2,114 detail rows, 278 backfill pending, zero parse/hash errors, zero public-availability-certified and zero signal-eligible rows.
- Phase 560 PR check [45056358699](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45056358699): offline regression succeeded and live capture was skipped by design; artifact [14767179586](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45056358699/artifacts/14767179586) was uploaded. Its log recomputed the current ledger classifier (103 formal plan-date entries, 14 remarks mentions); it is not a live SEC capture.
- The Phase 403 workflow file still declares `47 * * * *`. The 18:47, 19:47 and 20:47 UTC slots have no corresponding scheduled run in the observed inventory; 21:47 UTC had not yet occurred at this cutoff. This is a run-history delivery gap, not proof that the workflow is disabled. No dispatch, rerun, cron change or duplicate poll was made. Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) remains the tracking record.
- Weekend absence is not treated as a missed run for weekday-only Form 4, FINRA or CFTC schedules.
- Relevant open PRs remain Draft and stale/diverged: #200 (5 ahead / 25 behind main; not mergeable), #201 (2 ahead / 25 behind), and #204 (11 ahead / 5 behind). Do not merge or refresh these branches without a separate reconciliation. PR #204 still requires the human `SEC_USER_AGENT` secret before its bounded live SEC FTD sample.

## 2. SEC MIDAS: distinguish the two public series

The SEC currently lists two separate quarterly series, both spanning January 2012 through September 2026 and each listing 59 quarterly ZIP files:

1. **Metrics by Individual Security** — daily per-security metrics across the reported market structure. The 2026 Q3 ZIP is listed at 24.42 MB.
2. **Metrics by Individual Security and Exchange** — the corresponding metrics partitioned by exchange. The 2026 Q3 ZIP is listed at 201.18 MB (about 8.2 times the individual-security file size).

The distinction matters. The exchange-partitioned series can support exchange-level decomposition, but neither series identifies beneficial owners, customers, institutions or the direction of an investor's position.

Official SEC catalogs:
- https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security
- https://www.sec.gov/data-research/sec-markets-data/market-structure-data-security-exchange
- https://www.sec.gov/data-research/market-structure-data

## 3. Data.gov catalog is not a current PIT inventory

The Data.gov record titled **Metrics by Individual Security and Exchange** lists 58 resources, with its latest listed quarter 2026 Q2, and metadata `Dataset Last Updated: 2024-10-31`. The current SEC exchange-specific page lists 2026 Q3 as well (59 files) and says the page was last reviewed/updated 2026-09-30.

This is a catalog-maintenance discrepancy, not evidence that the SEC ZIP was first published on either date. The Data.gov record is for the exchange-partitioned series; do not conflate it with the separate Metrics by Individual Security series.

Data.gov record:
- https://catalog.data.gov/dataset/metrics-by-individual-security-and-exchange

**PIT conclusion:** neither the SEC page-level review date nor the Data.gov dataset-modified date establishes the first-public timestamp of any quarterly ZIP. The quarter label and the daily observation Date are not knowledge timestamps. Historical daily rows cannot be treated as if they were available to a strategy on each observation date.

## 4. Feasibility and research disposition

| Gate | Current evidence | Decision |
|---|---|---|
| Advertised history | 59 quarterly files, 2012 Q1–2026 Q3, for each SEC series | Pass at catalog level |
| Daily per-security observations | SEC schema description lists Date and per-security market-activity fields | Pass at schema-description level |
| Exchange decomposition | Separate security-by-exchange series exists | Candidate for venue heterogeneity |
| Exact historical F80 membership/coverage | No file-level 335-symbol/date matrix | Unverified; fail closed |
| Delisted/renamed identity | Ticker-based public schema does not itself provide an effective-dated security master | Unverified; fail closed |
| ZIP integrity/schema/row continuity | No payload downloaded or parsed in this phase | Unverified |
| Per-quarter first-public receipt | No per-file publication timestamp established | Fail for strict historical PIT |
| Participant/beneficial-owner identity | Not present in these public metrics | Fail for investor-identity hypothesis |
| Off-exchange interpretation | Published security metrics are exchange-market-structure measures; hidden executions are not dark-pool executions | Reject off-exchange/ATS-flow interpretation |

Retain both series only as conditional exchange-market-quality/liquidity-state candidates. The exchange-partitioned version may be useful for venue heterogeneity; it is not an institutional-flow proxy. The prior Phase 548 rejection of “hidden volume = dark/off-exchange institutional accumulation” remains in force.

Before any return test, require:
1. Actual ZIP integrity and schema checks across pre/post-2014, pre/post-2017 and post-2025-11-03 methodology regimes.
2. Exact symbol/date coverage against historical F80 membership, including inactive, acquired, renamed and delisted securities.
3. Effective-dated security identity and terminal total-return handling.
4. Prospective first-receipt logging for each quarterly release (URL, UTC receipt, bytes, SHA-256, schema/version and corrections).
5. Use only the first complete trading session after actual receipt; never backdate quarterly data to the daily observation dates.
6. Separate preregistered tests for hidden-volume rate, odd-lot rate, cancel/trade and trade/order metrics, with methodology/venue masks and controls for prior returns, volatility, turnover and market cap.
7. Compare incremental information with frozen LTM/F80 at identical exposure and costs, chronological OOS, block bootstrap and leave-one-time-block-out discipline.

Because quarterly archives may be available only after the quarter has ended, MIDAS may be too stale for short-horizon stock selection. That remains untested; no holding-period restriction is imposed, but same-quarter use is prohibited.

## 5. Controls

- New signals admitted: **0**.
- Incremental OOS evidence: **none**.
- New event/return/backtest/bootstrap/LOO/holdout test: **0**.
- No data purchase, vendor subscription, API key or licensed sample.
- No changes to universe, exposure, costs, holdout, holding-period policy or production.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

**Next valid work:** obtain the first-public release clock and actual file-integrity/coverage evidence before authorizing a MIDAS panel; separately resolve the SEC_USER_AGENT prerequisite for the bounded FTD/13D-G work. Keep FINRA Reg SHO rejected until a natural post-Phase-539 capture passes its file-validity gate.
