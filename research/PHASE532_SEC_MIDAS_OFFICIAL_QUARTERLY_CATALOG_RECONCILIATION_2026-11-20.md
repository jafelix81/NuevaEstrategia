# Phase 532 — SEC MIDAS official quarterly catalog reconciliation

Date: 2026-11-20

## Objective

Independently reconcile Phase 531's Obscura claim that six SEC MIDAS quarters were absent "at source" against the current official SEC download index. No licensed vendor data or paid service is required for this catalog-level check.

## Repository and Actions preflight

- Default branch: main.
- Main HEAD at audit: 49bf4c2a6529fa1eb4b64e7a1f22a147952071f9.
- Latest overall Actions runs: [44784058203](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44784058203) and [44784057531](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44784057531), both PR checks for PR #189 at 17:31 UTC; both successful.
- The two jobs ran 16/16 and 21/21 offline tests respectively. Neither produced artifacts; neither was a live SEC capture.
- Latest 100-run query: 0 in-progress and 0 queued.
- Schedule-event inventory: 38 runs. Latest scheduled Form 4 remains [44716430351](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44716430351), completed 10:07 UTC. Latest scheduled Form 144 remains [44720422923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44720422923), completed 10:35 UTC. No later scheduled SEC capture is present.
- Form 4 artifact [14619333577](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44716430351/artifacts/14619333577), 1,311 bytes; Form 144 artifact [14621821685](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44720422923/artifacts/14621821685), 1,902 bytes.
- Form 4 log: 33 new bounded metadata rows; 10 accessions parsed into 37 transaction-detail rows; 1,213 bounded accessions remain; zero research-/signal-eligible rows. It predates Phase 525 and has no reporting-owner enrichment/crosswalk output.
- Form 144 log: 52 feed observations; no new accessions; 10 old accessions parsed into 64 detail rows; 358 accessions remain; zero signal-eligible rows. It predates Phase 525.
- reporting_owners.csv remains absent on main. Both workflows still declare their expected schedules. The available API does not expose the administrative workflow enabled/disabled setting; no manual dispatch or rerun was performed.
- PR #189 remains a draft on branch phase531-obscura-multisource-pit-audit; its latest Phase 460/461 checks passed. No active run was duplicated.

## Official SEC catalog finding

Current official SEC page:

https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security

The page currently states:
- Coverage: January 2012 through September 2026.
- More than 4,800 securities.
- 59 quarterly ZIP downloads, continuously from 2012 Q1 through 2026 Q3.
- Page last reviewed or updated: September 30, 2026.

The six quarters previously described by Obscura as missing are explicitly listed in the official SEC index:
- 2014 Q2;
- 2016 Q1, Q2, Q3 and Q4;
- 2019 Q4.

The SEC also has a dedicated static-file page for 2014 Q2:

https://www.sec.gov/file/individualsecurity2014q2updated

The official page lists the other five quarterly downloads directly. A browser attempt to retrieve the ZIP payloads was not supported by the web client, and a direct container download attempt failed. Therefore this audit verifies official index listing and direct-file-page presence, not the ZIP payload integrity or row counts.

## Correction to Phase 531

The statement that those six quarters were absent "at source" is not supported by the official SEC index. Reclassify them as **possible Obscura ingestion/coverage gaps**, pending an actual vendor sample or written coverage manifest.

The earlier Phase 42B branch already recorded that the SEC index and Data.gov catalog listed a continuous quarterly sequence through 2026 Q2. The current SEC index extends that sequence through 2026 Q3. Data.gov's 58-resource inventory through 2026 Q2 is now behind the current SEC index by one quarter; its generic modified timestamp remains unsuitable as a per-file publication timestamp.

## What this does and does not establish

**Pass:** official SEC catalog-level history and listed-quarter continuity, 2012 Q1–2026 Q3.

**Not proven:**
- first public release date for each quarterly ZIP;
- actual file integrity and row-level continuity;
- exact overlap with the frozen 335-symbol universe;
- ticker/CUSIP continuity and delisted-security coverage;
- whether the quarterly publication cadence is economically timely for the intended holding horizons.

The SEC page-level "Last Reviewed or Updated" date must not be applied to every quarterly file. Neither quarter-end observation dates, current download links, file mtimes nor Data.gov's dataset-level modified date establish historical availability.

## Decision

Keep SEC MIDAS as a promising public market-structure candidate. Do not buy Obscura solely to fill the six alleged gaps until the vendor explains its own ingestion status. Do not run alpha tests until actual ZIP integrity, 335-name universe overlap, historical identity and conservative per-quarter knowledge dates are established.

The variables remain market-structure measures (hidden volume, odd lots, trade/order activity), not direct institutional identity. Any future test must control for prior returns, momentum, turnover, volatility and liquidity and compare incrementally against frozen LTM/F80 under chronological OOS, identical exposure/costs, block bootstrap and LOO.

## Strategy protection

- F80_TOP20_PARTIAL50_BASELINE_C20 unchanged.
- New signals admitted: 0.
- New OOS results: 0.
- Backtests: 0.
- Holdout, universe, exposure, costs and production: unchanged.

This phase is a source-catalog correction only; it does not establish alpha.
