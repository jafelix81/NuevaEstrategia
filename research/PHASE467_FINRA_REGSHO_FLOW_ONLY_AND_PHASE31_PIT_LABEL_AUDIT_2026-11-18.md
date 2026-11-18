# Phase 467 — FINRA Reg SHO flow-only feasibility and Phase 31 PIT label audit

**Audit date:** 2026-11-18 UTC  
**Disposition:** **REOPEN DAILY FLOW AS A CONDITIONAL, FLOW-ONLY DATA CANDIDATE; INVALIDATE PHASE 31 RETURN LABELS FOR STRICT PIT; NO ALPHA ADMISSION.**  
**Scope:** latest repository/Actions preflight, independent inspection of the existing Phase 31 GitHub Actions artifact, source semantics, availability clock, and executable-label alignment. No new market-data download or backtest was run.

## 1. Repository and Actions preflight

Preflight was completed before creating this audit branch.

- Main HEAD: `bc4a2ccecd32962340831eea54563743dadfe6c6`, commit time 2026-11-17 23:54:41 UTC (Phase 466).
- Latest Actions inventory: 7,728 total runs; latest 100 contain 69 success, 30 failure, 1 cancelled; zero queued, waiting, requested, or in-progress runs.
- Branch enumeration: 300 branches across three API pages.
- Open PRs: 56. PR #61, “Phase 385 — FINRA T1 date-level publication-clock census,” remains draft/open and is based on `phase375-finra-t1-ats-full-weekly-revision-audit`, not main. It was not changed.
- Workflow files on main: 76.
- Latest run in the latest-100 inventory: PR-triggered run 44195226738, not a scheduled market-data capture.

### Scheduled delivery status

**SEC Form 144**
- Workflow: `.github/workflows/phase403_sec_form144_first_seen_capture.yml`.
- Configured cron: `47 * * * *`.
- Latest verified scheduled run: 44179257367, created 2026-11-17 21:23:10 UTC; successful poll ran 21:23:27–21:23:39 UTC.
- Current SEC ledger state: 106 event rows, 388 feed-observation rows, 106 acceptance reconciliations; latest poll run 44179257367; 58 new feed observations; Form 144 possible-gap flag remains true; Form 144/A gap flag false; signal_eligible=false.
- The successful run predates Phase 465 pagination. No later scheduled run appears in the latest-100 inventory through this audit at 2026-11-18 00:29 UTC. The next :47 slot had not yet occurred at the audit cutoff. Phase 465 pagination therefore remains **not live-validated**.

**CFTC TFF**
- Workflow: `.github/workflows/phase384_cftc_tff_prospective_capture.yml`.
- Configured cron: `25 22 * * 1-5` UTC.
- Latest verified run: 43525140200, a branch-push/bootstrap on 2026-11-13 23:03:38 UTC, not a scheduled capture.
- Persisted state remains at the 2026-11-13 bootstrap: 3,035 historical warm-up rows; all four contract codes have latest report date 2026-11-03; zero prospective observations.
- No CFTC scheduled run appears in the latest-100 Actions inventory after the expected 2026-11-17 22:25 UTC poll.

The connector exposes workflow YAML and run history but not the administrative enabled/disabled state. Therefore it is not possible to distinguish a disabled workflow from GitHub schedule delivery being delayed/dropped. **Human check required:** verify that the existing Phase 403 SEC Form 144 and Phase 384 CFTC TFF workflows are enabled in GitHub Actions. Do not create replacement workflows or change the crons before that check.

## 2. Existing Phase 31 artifact independently inspected

No new FINRA request was made. The existing successful artifact was downloaded from:

- Run: [40164323397](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40164323397), event `push`, branch `phase31-finra-flow-si-divergence`, commit `44c2fda9ea03fcfbce662e4dd26ca876ac03961b`.
- Artifact: [12588045711](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40164323397/artifacts/12588045711).
- ZIP size: 26,495,313 bytes.
- ZIP SHA-256: `91f7683cf984cb2b00a6bd772608c3243ac9a56717930c6fd2092696e092a266` (matches GitHub artifact metadata).

The extracted `flow_features.csv` contains:

| Metric | Observed |
|---|---:|
| Rows | 362,727 |
| Unique symbols | 334 |
| Configured frozen universe | 335 |
| First / last trade date | 2022-06-01 / 2026-10-23 |
| XNYS sessions | 1,104 |
| Downloaded session files | 1,104 |
| Missing / extra XNYS sessions | 0 / 0 |
| Daily cross-section, min / median / max | 321 / 330 / 333 |
| Symbols with at least 1,100 observations | 313 / 334 |

The download audit contains 1,148 weekday attempts: 1,104 successful trading-session files and 44 HTTP 403 responses. All 1,104 XNYS sessions in the sample window were present; the 44 rejected weekdays were non-sessions under the XNYS calendar. This is a strong historical *file-delivery* result for 2022-06 through 2026-10, not proof of exact historical publication timestamps or full 335-name tradability.

The short-volume ratio distribution in the extracted panel was: minimum 0.0014, median 0.4947, 1st percentile 0.1917, 99th percentile 0.7909, maximum 0.9793. Across retained rows, short-exempt volume was no greater than short volume and the ratio did not exceed one. A sample raw daily file had one row per symbol and combined facility marker `B,Q,N`; this does not replace a full all-date raw-file schema audit.

Coverage limitations:
- One of the 335 configured symbols never appeared in the 334-symbol panel.
- Daily cross-section varied from 321 to 333; 21 observed symbols had fewer than 1,100 sessions, often because their listing/history began later or ended earlier.
- No effective-dated identity or active-listing proof was reconstructed for every absent row. Do not infer a structural zero or use ticker-only joins to fill gaps.
- The verified sample begins in June 2022. FINRA's 2009 rule filing announced daily publication beginning in 2009, but the consolidated `CNMSshvol` file's full 2009-to-present schema and universe coverage have not been independently audited here.

## 3. Material Phase 31 timing defect

The Phase 31 source file is on branch `phase31-finra-flow-si-divergence`:

[Nueva_Estrategia_Fase31_FINRA_Flow_SI_Divergence.py](https://github.com/jafelix81/NuevaEstrategia/blob/phase31-finra-flow-si-divergence/Nueva_Estrategia_Fase31_FINRA_Flow_SI_Divergence.py)

The code selects the latest flow row with `flow.Date <= sig`, then sets `base = close.iloc[pos]` and labels `FWD5/FWD10/FWD20 = close[t+h] / close[t] - 1`. The file's module comment describes flow through close t and a close-t-to-open-t+1 execution convention, but the actual label begins at **close t** and uses close-only prices.

FINRA's 2009 publication rule says the daily file is posted **within a reasonable amount of time after the end of regular trading hours**. Thus the same-day short-volume observation is not known at the close used as the label's starting price. The close-t-to-close-t+h return includes the close-t-to-next-open move, which cannot be earned by a strategy that first receives the file after close t.

**Decision:** Phase 31's reported forward-return/IC/spread results are not valid strict-PIT evidence for a same-day close-t signal. Retain them as historical diagnostics only; do not cite them as alpha, do not use them for feature selection, and do not promote either joint factor. The factor-level output also contains only 36 signal dates and its bootstrap intervals for the reported spreads include zero. `JOINT_RISE` and `JOINT_FALL` are exact sign reversals of the same product, not independent confirmation.

The short-interest side of Phase 31 remains separately non-admissible: the old synchronous extracts hit the 5,000-row ceiling on all 102 successful requests, four settlement requests failed, and snapshot completeness was not recorded. Phase 447's asynchronous client is ready for a controlled live validation, but the credential guard previously found `FINRA_ACCESS_TOKEN`, `FINRA_CLIENT_ID`, and `FINRA_CLIENT_SECRET` empty. No FINRA API request was made in this phase.

## 4. Source semantics: this is not “smart money” by default

FINRA describes Daily Short Sale Volume as aggregated volume of off-exchange short-sale trades reported to FINRA facilities. It excludes activity not publicly disseminated and is not consolidated with exchange trading. FINRA explicitly says daily short-sale volume is not equivalent to the twice-monthly short-interest position snapshot; a short sale can be covered on the same day and never appear in short interest.

Therefore:
- `ShortVolume / TotalVolume` is a short-marked share of **FINRA-reported off-exchange facility volume**, not a short share of all U.S. market volume.
- It is not net short flow, persistent short positioning, beneficial ownership, or institutional identity.
- Short-exempt volume is a subset of short volume, not an additional independent flow.
- Plausible competing explanations include market making, hedging, internalization, liquidity provision, and directional short demand. These remain hypotheses.

Official references:
- FINRA SR-FINRA-2009-064, daily-file timing and original publication design: https://www.finra.org/sites/default/files/RuleFiling/p120246.pdf
- FINRA Short Sale Volume Daily Data User Guide: https://www.finra.org/sites/default/files/2020-12/short-sale-volume-user-guide.pdf
- FINRA, “Short Interest — What It Is, What It Is Not”: https://syndication.finra.org/content/short-interest-what-it-what-it-not

## 5. Research disposition and re-entry gates

| Candidate | Decision |
|---|---|
| Phase 31 joint flow × short-interest panel | **Not admissible**: incomplete SI snapshots plus same-close label timing defect |
| Daily Reg SHO flow-only panel | **Conditional data candidate**: strong 2022–2026 file coverage, but historical exact PIT clock and 335-name identity/price coverage are not proven |
| Daily short-volume ratio as “smart money” | **Rejected as an interpretation**; only a market-microstructure/short-marked-flow hypothesis remains |

Before any flow-only return test:
1. Add a prospective first-seen ledger for each daily CNMS file: trade date, poll start, first-seen UTC, HTTP status, response bytes, raw SHA-256, row count, schema version, XNYS session status, and revision hash. Keep raw market data private; commit only compact manifests.
2. For historical data, use lagged availability only as an explicitly labelled sensitivity, never as an exact historical first-seen timestamp. Do not use same-day flow at close t.
3. Align the first executable price after information receipt (normally next regular-session open for a post-close receipt) and preregister the exit convention. The label must not begin at a price observed before the signal became available.
4. Require an effective-dated security master and price panel for all 335 baseline members, including ticker changes, delistings, corporate actions, and explicit unknown/zero states. Do not reduce the frozen universe to 334 or to a vendor-available subset for an F80 incremental claim.
5. Test flow-only features against F80/LTM using identical exposure, turnover, costs, and the same chronological OOS/holdout discipline. Control for prior returns, volatility, liquidity, off-exchange total volume, short-exempt share, and market regime. Use bootstrap and leave-one-date-out/event-block sensitivity. Separate prediction from return-chasing.
6. Only after the flow-only gate passes should the joint flow × short-interest hypothesis be reconsidered; SI requires a complete async snapshot and effective-coverage audit first.

No return test, portfolio simulation, OOS test, bootstrap, LOO, or signal-admission test was run in Phase 467. No raw data or credentials were committed.

## 6. Frozen strategy

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No change to universe, parameters, holding period, capital, exposure, costs, holdout, or production was made.
