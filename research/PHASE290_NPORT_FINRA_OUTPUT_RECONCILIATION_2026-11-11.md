# Phase 290 — N-PORT / FINRA output reconciliation and PIT admission correction

**Date:** 2026-11-11 UTC  
**Branch:** `phase290-evidence-reconciliation-nport-finra`  
**Status:** `LEGACY_NPORT_OUTPUT_INVALIDATED_FINRA_20C_NOT_PIT_ADMITTED`  
**Scope:** inspect existing GitHub Actions runs, jobs, logs and artifacts; reconcile the N-PORT Phase 27O output with the Phase 247 schema audit; re-evaluate the Phase 20C FINRA diagnostic. No new source requests, no return-model rerun, no holdout use and no production changes.

## Executive decisions

1. **Quarantine the Phase 27O N-PORT long-share accumulation output.** The existing successful workflow produced seven transitions with `n_ranked=0`, no eligible long/short baskets and no forward returns. The reason is the already documented flattened-schema defect: the script reads `UNITS`, while the official SEC flattened `FUND_REPORTED_HOLDING` table calls the column `UNIT`. The Phase 27O artifact now independently confirms the consequence. This is neither positive nor negative evidence about the economic hypothesis.
2. **Do not promote Phase 20C FINRA short-volume replacement.** Its 12 pseudo-OOS dates show weak, unstable incremental results; every horizon's date-level uncertainty interval includes zero. More importantly, the script forms the signal with same-day FINRA data and measures returns from that same day's close, although no first-public timestamp is retained or verified. It is not strict PIT.
3. **Retain the SEC Form 4 real-data sample as the highest-priority next source task, but pause all automated SEC retrieval until a real, authorized contact is configured.** The legacy Phase 27K/27O code hard-coded `research@example.com` in its SEC User-Agent. Do not reuse that placeholder. The SEC's current access guidance asks automated clients to declare a company/name and administrative contact email in the User-Agent.

## 1. GitHub state checked before research

At the start of this phase, the latest 100 Actions runs contained 67 completed successes, 33 cancellations, zero failures and zero queued/in-progress runs. No active workflow was duplicated.

- PR #14: open and mergeable, head `6dedb088d7289ca5155a319b5f88155c2d431be3`; 23 associated check-runs all completed successfully. [PR #14](https://github.com/jafelix81/NuevaEstrategia/pull/14)
- PR #13: open and mergeable, head `61f737f18b410bc6d85b8c56ed96bc1fd9c130f5`; zero check-runs registered on that SHA. [PR #13](https://github.com/jafelix81/NuevaEstrategia/pull/13)
- Branch inventory before this documentation branch: 138. This phase adds one documentation-only branch; no PR was opened and no merge was performed.
- Latest run: [Phase 286, 43031307177](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43031307177), job `metadata-audit` succeeded; artifact [13860368810](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43031307177/artifacts/13860368810), SHA-256 `0cb5694dfb5cc879479fd9ac9db9924440f8ce1b9a035620027d4cd46a33d4b9`.
- Latest Phase 278 targeted run [43030407560](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43030407560): job succeeded, 20/20 offline tests; 147,725 rows across 30 pages; two conflicting duplicate-grain groups remain quarantined. Artifact [13861545967](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43030407560/artifacts/13861545967), SHA-256 `1de1075b3a3e9161af17758000b80456fb32ae3c8e05898b4591d105adaa6380`.
- Phase 231 [43030407294](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43030407294) succeeded but remains a sample parser gate only: 115,617 populated rows; 112,313 unambiguous valid rows; 3,304 ambiguous expiration rows quarantined. Artifact [13860267856](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43030407294/artifacts/13860267856).

## 2. Phase 27O — inspect the actual artifact, not only the workflow conclusion

Historical run: [39493106882](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39493106882), branch `phase27o-nport-pit-flow-correction`, commit `c6849ae257f6815b38b3275535205396859760d1`. Its single `research` job completed successfully. Artifact [12296499022](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39493106882/artifacts/12296499022) is 192,206 bytes, SHA-256 `c8207cd99b5bc80be730db89da62ced1298a18af0330b11335e41864fca4478b`.

The artifact was downloaded from GitHub and its JSON inspected directly:

| Snapshot | Selected series | Eligible equity/long rows | Resolved universe tickers | Tickers with positive shares |
|---|---:|---:|---:|---:|
| 2019Q4 | 5,609 | 818,989 | 267 | 0 |
| 2020Q4 | 6,021 | 831,219 | 283 | 0 |
| 2021Q4 | 5,995 | 831,666 | 303 | 0 |
| 2022Q4 | 6,132 | 824,586 | 313 | 0 |
| 2023Q4 | 5,185 | 706,715 | 310 | 0 |
| 2024Q4 | 6,077 | 792,846 | 319 | 0 |
| 2025Q4 | 6,166 | 787,454 | 322 | 0 |
| 2026Q3 | 6,553 | 813,504 | 324 | 0 |

All eight snapshots show only a blank-string key in the artifact's `balance_units` diagnostic. All seven transitions have `n_ranked=0`, zero long/short names evaluated and an empty return dictionary. The run's success means the script completed and uploaded an artifact; it does **not** mean a signal was formed or tested.

### Root cause and additional admission defects

- The script reads `h.get("UNITS")`. The official SEC flattened TSV field is singular `UNIT`; `units` is the raw XML element spelling. The `UNIT == NS` test therefore never succeeds. This is exactly the defect documented by Phase 247, now confirmed in the actual Phase 27O artifact.
- Phase 27O's eight snapshots are long-equity accumulation snapshots (`PAYOFF_PROFILE` blank/`LONG`), not the distinct direct-short N-PORT hypothesis preregistered in Phases 219–221.
- The fixed report-date +75-day selection uses `FILING_DATE`, not accession-level EDGAR acceptance/verified first public availability. It is not a strict PIT event panel.
- Aggregation is performed by ticker across selected series; it does not establish same-series/security continuity, corporate-action-adjusted share basis, or a full as-filed amendment state machine.

**Disposition:** quarantine the Phase 27N/27O long-share return hypothesis output. Do not patch only the column and rerun the same annual return screen. A future N-PORT test must first build the asynchronous per-series accession/vintage panel, use the singular `UNIT` field fail-closed, resolve historical security identity and corporate actions, and separate long and direct-short hypotheses.

### SEC retrieval provenance correction

The Phase 27K and Phase 27O scripts contain a hard-coded User-Agent ending in `research@example.com`. The Phase 27O log shows all eight SEC archive periods being built, and the artifact contains parsed snapshots from those downloads. This confirms that historical automated SEC retrieval occurred in that workflow despite the later Phase 193 empty-secret gate. The placeholder is not an authorized contact identity and must not be reused. Preserve the historical artifact only as a quarantined diagnostic; do not repeat SEC requests until `SEC_CONTACT_EMAIL` is populated with an actual authorized contact and the code reads it from the secret. No secret was inspected or changed in this phase.

Official SEC guidance: [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) requests a declared User-Agent with a company name and administrative contact email; it also explains that daily indexes are updated nightly and some ownership filings submitted after 10 p.m. ET appear in the following business day's index.

## 3. Phase 20C — FINRA daily short-volume diagnostic

Historical run: [40098425254](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254), commit `b12015997cdb13ea46b48df46b82e52eeedd479f`; job `run` succeeded. Artifact [12562171831](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254/artifacts/12562171831), size 145,921,861 bytes, SHA-256 `c15f75340bdedfbb37c82f79bb563a450dd1da11989d09e18bb745d93b7d3a5c`.

### Retrieval coverage

The artifact's audit records 2,020 requested calendar dates and 1,382 successful daily files. Reconciliation against the XNYS session calendar shows that **all 1,382 requested XNYS sessions had a file**. The 638 HTTP 403 dates are non-session dates or dates before the source start: 572 weekends, 49 XNYS weekday closures on/after 2018-08-01, and 17 weekdays before the declared 2018-08-01 source start. The raw 68.4% ratio (1,382/2,020) is therefore not a trading-session coverage rate. This is a positive data-availability result for the particular signal lookback windows, not proof of full-market coverage or PIT availability.

### Pseudo-OOS results

- Valid price universe: 329; six download failures.
- 24 total F80 signal dates; 20 FINRA-eligible training dates.
- 12 pseudo-OOS test dates; six later signal dates were left untouched by this run.
- Each test date compared only four blocked F80 names with four replacements (20% of a 20-name target), not two full 20-name portfolios.
- Factor selection was unstable: `SHORT_RATIO_PERSIST20` once, `SHORT_RATIO_Z20` six times, and `SHORT_EXEMPT_RATIO` five times; selected direction changed across regimes.

| Horizon | Mean replacement-minus-blocked | Median | Positive dates |
|---|---:|---:|---:|
| 5 sessions | +0.141% | -0.049% | 5/12 |
| 10 sessions | -1.686% | -1.837% | 3/12 |
| 20 sessions | -0.858% | -0.333% | 5/12 |

Exploratory date-resampling 95% intervals for the mean delta were approximately [-2.67%, +3.01%] at 5 sessions, [-5.81%, +2.29%] at 10 sessions, and [-10.38%, +7.55%] at 20 sessions. These are not issuer/date-clustered inference; the sample has only 12 dates and four names per side/date. Costs, turnover slippage and a full portfolio-level net comparison were not included.

### PIT and interpretation defects

- The script forms each signal from FINRA rows with `Date <= signal_date`, then computes forward returns starting at that same date's close. The artifact has no first-public-receipt timestamp for the daily FINRA file. FINRA's public catalog describes daily short-sale volume files but does not establish an intraday first-public time for these historical files. A same-day-close fill is therefore not demonstrated to have been executable. Use the next full XNYS session as the conservative entry boundary unless a reliable receipt clock is captured.
- The CNMS short-volume file is off-exchange/TRF-family short-sale volume, not market-wide short interest or the net short position held overnight. FINRA's 2019 Information Notice explicitly distinguishes daily short-sale volume from twice-monthly short interest and explains that exchange-published short volume must be considered separately for a more complete market view. [FINRA Information Notice 5/10/2019](https://www.finra.org/sites/default/files/2019-07/information-notice-051019.pdf).
- The current FINRA catalog provides the daily short-sale volume product and links to longer-history files/API; the FINRA short-interest page separately publishes settlement, due and publication dates. [Short Sale Volume Data](https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data) · [Short Interest Reporting](https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest).

**Disposition:** no promotion and no parameter retuning. The existing same-day-close Phase 20C result is not strict PIT and does not show robust incremental improvement. If revisited, first shift execution to the next full session, preserve source-receipt evidence, keep short volume and short interest as separate features, add exchange short-volume coverage only with non-overlapping definitions, and rerun the chronological test with realistic costs and date/issuer-clustered uncertainty. Do not touch the six unused signals or the consumed legacy holdout.

## 4. Updated research priorities

1. **SEC Form 4:** retain highest priority for a real six-quarter sample, after a genuine `SEC_CONTACT_EMAIL` is configured; then reconcile daily index sightings, acceptance headers, PAC/amendment behavior, owner attribution and effective-dated share-class identity.
2. **SEC N-PORT direct short:** retain as a distinct registered-fund hypothesis, but require raw submission/XML hashes, full Part-C parsing, series/amendment lineage, first-public clock and effective-dated security identity. Do not reuse Phase 27O long-side output.
3. **FINRA short volume + short interest:** preserve as two different data constructs. Phase 20C needs a next-session PIT correction before any further economic interpretation; Phase 267/278 limitations remain.
4. **13F:** remain parked for broad-universe stock selection until historical identity coverage is repaired.
5. **Options / securities lending:** no purchase or subscription until an authorized sample, historical vintage terms, universe coverage and cost feasibility are established.

## Controls

No new SEC, FINRA or vendor requests were sent in this phase. No vendor was contacted, no data was purchased, no new workflow was started, and no holdout was used. No alpha, net portfolio return, cluster bootstrap, LOO or independent OOS result was produced. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; production, universe, capital and parameters are unchanged. The legacy holdout remains `CONSUMED_NOT_PRISTINE`. No CAGR target or minimum/maximum holding period is imposed.
