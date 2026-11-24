# Phase 593 — FINRA Phase 20C PIT adjudication and current short-flow disposition

**Audit date:** 2026-11-24  
**Main HEAD at preflight:** `ad8351d42c8052678ca0a56db106b3ec603670d3`  
**Disposition:** **NO-GO for promotion of the current Phase 20C implementation.** This is not a permanent rejection of FINRA data; the current same-day-close test is not point-in-time executable and its pseudo-OOS evidence is weak and unstable. The final six-signal holdout remains sealed.

## 1. Preflight

Reviewed the latest repository Actions runs, jobs, logs, artifacts, branches, open PRs, research state and relevant data files before continuing.

- Actions runs: 8,109 total; latest 100 = 90 successful / 10 failed.
- Active / queued runs: 0 / 0 (queried explicitly by status).
- Branches: 380 across four pages.
- Open PRs: 72.
- Workflow files: 96.
- Main HEAD: `ad8351d42c8052678ca0a56db106b3ec603670d3`, pushed 2026-11-24 09:18:59 UTC.
- No workflow was dispatched, rerun, cancelled or duplicated.

Latest relevant completed runs:
- [Form 4 Phase 476 — 45332760566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566): both feed watermarks found; 516 new accessions; 6,022 accession observations; 129 transaction rows in the structured ledger; 61 owner-sidecar rows; 24 new detail rows from a bounded 10-accession backfill; 11 owner rows from a bounded 10-accession backfill; zero signal-eligible rows.
- [Form 144 Phase 403 — 45330252226](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226): 118 new accessions; 801 new detail rows; 477 accessions / 3,360 detail rows cumulative; 238 detail backfills pending; five acceptance reconciliations unresolved; zero signal-eligible rows.
- [FINRA Reg SHO Phase 469 — 45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236): six HTTP-200 files, all rejected by the fail-closed duplicate-symbol check; 12 extra rows across BCPC and TPC; zero valid/first-seen/research-eligible/signal-eligible rows. The raw rows and volume values were not persisted.
- [CFTC TFF Phase 384 — 45338400329](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329): 3,043 rows; no new reports or revisions; zero historically signal-eligible rows.

The four relevant jobs and their artifacts were inspected. All are complete; artifacts are unexpired. The last relevant scheduled capture is FINRA at 06:15 UTC, so no later live data capture was available at this audit cutoff.

## 2. Phase 20C branch and artifact audit

The branch `phase20c-finra-walkforward` is **12 commits ahead / 596 behind main** (diverged). It has only two historical successful runs:
- [Run 39335227938](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39335227938), 2026-10-19.
- [Run 40098425254](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254), 2026-10-24.

The later run's artifact [12562171831](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254/artifacts/12562171831) was downloaded and inspected. It contains 1,382 raw CNMS daily files and a 412,645-row FINRA panel. A direct scan found **zero duplicate (Date, Symbol) keys** in those 1,382 historical source files. The Market field was generally a comma-separated facility list (e.g. `B,Q,N`). Thus the branch's `drop_duplicates(["Date","Symbol"])` was a no-op on this particular historical artifact; the 2026 BCPC/TPC duplicate anomaly is a separate unresolved current-file issue and must not be projected backward onto this history.

Run 40098425254 reported:
- 329 valid price histories from a 335-symbol configured universe; six failures.
- 24 total training signal dates, 20 FINRA-eligible training dates.
- Training end: 2024-10-30.
- 12 pseudo-OOS test dates.
- Six final OOS holdout signal dates, untouched.
- 2,020 unique calendar dates requested; 1,382 files downloaded and 638 returned HTTP 403/not-available. Those 638 dates were not separately reconciled to an exchange calendar, so they must not all be described as missing trading sessions.

The historical artifact is useful for a source-grain audit, but the price histories used by the run are not included in the artifact. The code calls `P12.download_universe(P12.DEFAULT_UNIVERSE)` at run time and does not persist a price snapshot/hash, corporate-action snapshot or effective-dated universe membership. The reported returns are therefore not fully reproducible from the artifact alone.

## 3. Critical point-in-time defect: same-day close entry

The Phase 20C code builds a feature panel using FINRA records with `Date <= signal_date`, then takes the signal-date record. Its forward-return function uses:

```python
FwdRet_nD = Close[signal_date + n] / Close[signal_date] - 1
```

This assumes execution at the signal-date close.

That is not executable with the FINRA daily file. FINRA's official rule-filing order says the daily short-sale volume file is posted after the end of regular trading hours on the trade date. The SEC's 2023 Federal Register discussion cites FINRA's publication deadline as no later than 6:00 p.m. ET on that same trade date. Therefore, the signal-date close has already occurred before the FINRA feature is public. Using that close as the entry price introduces look-ahead.

Official references:
- [FINRA SR-FINRA-2009-064 approval order](https://www.finra.org/sites/default/files/RuleFiling/p120246.pdf): daily file posted within a reasonable time after regular trading hours.
- [SEC Federal Register, 2023-23050](https://www.govinfo.gov/content/pkg/FR-2023-11-01/html/2023-23050.htm): cites FINRA's same-day publication no later than 6:00 p.m. ET.
- [FINRA Regulatory Notice 21-19](https://www.finra.org/rules-guidance/notices/21-19): daily short-sale volume covers reported short sales during normal market hours and is distinct from monthly transaction files.

The current pseudo-OOS returns cannot be treated as executable OOS evidence. A valid successor test must form the signal only after the file's actual/verified availability and enter no earlier than the next trading session. If only daily OHLC data are used, choose a pre-specified next-session open or next-session close convention and apply it identically to the replacement and blocked portfolios. The final six holdout signals must remain sealed until this correction, the data snapshots, universe rules and costs are frozen.

## 4. Recomputed descriptive statistics — not an OOS promotion test

The later artifact's 12 per-date replacement-minus-blocked deltas were independently summarized. Each date compared four replacement names with four blocked names. This is a small cross-sectional diagnostic, not a portfolio backtest.

| Horizon | Mean delta | Median delta | Positive dates | 95% t interval | 95% date-bootstrap interval |
|---|---:|---:|---:|---:|---:|
| H5 | +0.141% | -0.049% | 5/12 (41.7%) | [-3.209%, +3.491%] | [-2.664%, +3.037%] |
| H10 | -1.686% | -1.837% | 3/12 (25.0%) | [-6.453%, +3.080%] | [-5.802%, +2.301%] |
| H20 | -0.858% | -0.333% | 5/12 (41.7%) | [-11.362%, +9.647%] | [-10.386%, +7.565%] |

Bootstrap intervals resample the 12 signal dates with replacement (200,000 draws; fixed seed 20261124). The intervals are descriptive, unadjusted for the factor/horizon selection process and multiple testing. They all include zero. No horizon has a positive median and a majority of positive dates simultaneously.

The earlier run 39335227938 also had 12 pseudo-OOS dates but materially different summaries:
- H5 mean -0.497%, median +0.482%, 8/12 positive.
- H10 mean -1.303%, median -0.751%, 6/12 positive.
- H20 mean +1.654%, median +1.096%, 6/12 positive.

The two runs differed in available FINRA files (1,372 versus 1,382), universe coverage (328 versus 329 valid histories), and unarchived live price inputs. The changes demonstrate instability, but the source of that instability cannot be isolated without frozen inputs.

No transaction costs, portfolio-level identical-exposure test, bootstrap/LOO over a complete portfolio return series, or independent final-holdout evaluation was completed. No final-holdout data were opened.

## 5. Research disposition

**No-go for the current Phase 20C implementation and its existing performance claims.** Reasons:
1. Same-day-close entry is look-ahead relative to FINRA publication after the regular session.
2. Only 12 pseudo-OOS signal dates were tested; confidence intervals are wide and include zero.
3. The H10/H20 results are negative in the later run; the earlier run's H20 positive mean does not persist.
4. Price data, corporate actions and effective-dated universe membership were not frozen in the artifact.
5. Six price-history failures remain; the configured 335-symbol universe is not a demonstrated survivorship-free historical universe.
6. The final six signal dates have not been tested and remain sealed.

This kills the current same-day-close implementation as a promotion candidate. It does **not** prove that FINRA short-sale volume can never contain incremental information. A successor is justified only after:
- next-session execution and availability timestamps are implemented;
- source files, price histories, corporate actions and universe snapshots are hashed and persisted;
- the 2026 duplicate-symbol anomaly is resolved independently without guessing a sum/deduplication rule;
- identical exposure, realistic costs, chronological training/validation, bootstrap/LOO and independent OOS are pre-specified;
- the frozen LTM/F80 baseline remains unchanged.

## 6. Frozen strategy controls

- `F80_TOP20_PARTIAL50_BASELINE_C20`: unchanged and frozen.
- New signals admitted: **0**.
- Incremental alpha demonstrated: **none**.
- New valid OOS results: **0**.
- Universe, parameters, exposure, costs, holding-period policy and production: unchanged.
- No workflow was dispatched or rerun.
