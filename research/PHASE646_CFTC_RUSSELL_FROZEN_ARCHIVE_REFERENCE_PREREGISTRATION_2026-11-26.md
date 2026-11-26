# Phase 646 — CFTC Russell frozen-archive reference preregistration

**Preregistration timestamp:** 2026-11-26 18:18 UTC  
**Main HEAD at preflight:** `c6b77a7bc58babe2df7700ea8d82a4c2918a3fac`  
**Disposition:** preregister a new Russell E-mini small-cap downside-risk hypothesis using the 2026-11-13 historical snapshot only as a frozen pre-sample reference distribution. No feature values, forward outcomes, return tests, signal admission or F80 changes are produced in this phase.

## 1. Repository / Actions preflight

Checked the latest Actions runs, jobs, logs, artifact metadata, branches, open PRs and current research files before authoring this preregistration.

- Actions API: 8,350 total runs; latest 30 inspected; zero queued or in-progress runs.
- Latest completed natural SEC captures remain Form 4 [45848689364](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45848689364), 13F [45839454376](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45839454376), and Form 144 [45827105431](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431). Their offline/live jobs completed successfully and artifacts remain available.
- Form 4: 0 new accessions; the live entity sidecar contains two prior-watermark observations and zero exact duplicate groups. Bounded transaction/owner/footnote backfills completed with zero parse errors; zero signal-eligible rows.
- 13F: 29 accessions were recorded in the initial baseline (18 HR, 9 HR/A, 2 NT); all 29 have no prior successful poll/lower bound, no holdings were downloaded, and zero observations are research- or signal-eligible.
- Form 144: 825 accessions / 5,495 structured rows; 807 bounded intervals, 18 initial-baseline intervals, zero malformed intervals and zero signal-eligible rows.
- Latest CFTC scheduled capture [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471): no new reports/revisions; 3,043 persisted rows; zero signal-eligible rows.
- Latest FINRA Reg SHO [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648): eight HTTP-200 files, all eight rejected by the BCPC/TPC consolidated-symbol row-grain gate; 16 extra rows; zero market rows admitted.
- No newer natural SEC capture is visible after Form 4 at 15:23:55Z, 13F at 14:29:01Z and Form 144 at 13:13:48Z. This is an observed schedule-delivery gap, not proof that workflows are disabled. Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) remains the operational record. No manual dispatch, rerun, cancellation or duplicate poll was made.
- The legacy `phase20c-finra-walkforward` branch is 12 commits ahead / 680 behind main. Phase 593 remains authoritative: current Phase 20C is NO-GO for promotion due to same-day-close look-ahead, weak/unstable pseudo-OOS, incomplete price/corporate-action snapshots and incomplete historical universe coverage. No stale Phase 20C branch was merged.
- Main research tree contains no prior Russell-specific preregistration. Phase 387 remains a separate, frozen ES/NQ weekly study and is not modified.

## 2. Why a separate Russell design is justified

Phase 645 reconciled the post-2017 Russell E-mini TFF contract code `239742`:

- 482 API report-date rows from 2017-08-15 through 2026-11-03.
- 480/482 archive pages passed the date/heading and retrieval audit.
- Exclude 2018-09-25 (archive heading mismatch) and 2019-12-24 (archive page 404); do not fill either gap.
- The baseline snapshot was created at **2026-11-13 23:03:38Z**, before either prospective event below.
- Two prospective Russell report vintages were first received at 2026-11-18 03:44:57Z (report date 2026-11-10) and 2026-11-21 03:17:36Z (report date 2026-11-17).

The snapshot timestamp provides a defensible **project-knowledge time for the frozen snapshot as a whole**. This does not certify when each historical report was first published. The distinction permits a narrow use: historical values may define a fixed reference distribution for future observations received after 2026-11-13 23:03:38Z. Historical report dates must never be treated as historical signal-availability dates, and no historical return labels or backtest observations may be generated from them.

This is a new Russell-only design. It does not amend Phase 387's explicit rule that its ES/NQ percentile reference must consist of prior prospectively first-seen weekly observations. The Phase 387 design, thresholds, sample gates, outcomes and holdout remain unchanged.

## 3. Frozen data and feature definition

**Contract:** CFTC TFF Futures Only, CME Russell E-mini, code `239742` only. Do not splice the earlier Russell Mini contract era, ICE contracts or other contract codes.

**Frozen reference snapshot:**
- File: `research/data/cftc_tff_prospective/historical_backfill.csv`
- Blob SHA: `4711abbaeeb6107d1cb8f50a7c2e3627373b6d29`
- Manifest: `research/data/cftc_tff_prospective/baseline_manifest.json`
- Manifest SHA: `9e58849093f2144ce8cfbf1d3e5efc626a1aa250`
- Snapshot created: `2026-11-13T23:03:38Z`
- Russell reference observations: exactly 480 valid archive report dates after excluding the two exceptions above.

The baseline snapshot is immutable for this study. Do not update it, backfill it with later revisions, or add later prospective observations to its empirical reference distribution.

For each new scheduled prospective Russell event:

`LM_NET_OI(t) = (Leveraged Money long - Leveraged Money short) / open_interest_all`

Spreading positions are excluded from directional net and remain separate.

Primary feature:

`P_t = (count(x_j < LM_NET_OI(t)) + 0.5 * count(x_j = LM_NET_OI(t))) / 480`

where `x_j` are the 480 valid Russell reference observations in the frozen snapshot. The current observation is not in the reference sample.

Primary state: `HIGH_LM_CROWDING = 1[P_t >= 0.80]`.

- The 80th-percentile threshold is fixed.
- No threshold, direction, category, lookback, contract or outcome-horizon search is permitted.
- Asset Manager, Dealer and open-interest changes may be reported only as predeclared descriptive controls; they are not alternative primary predictors.
- Every signal timestamp is the actual scheduled collector `first_seen_utc`; the first eligible XNYS session is the first regular session strictly after receipt.
- The frozen archive may be used only as the reference distribution for prospective observations received after the snapshot timestamp. It may not create historical signals, training labels, return observations, or a historical backtest.

## 4. Hypothesis and outcomes

**H1 (one-sided):** an extreme high Leveraged Money net-long percentile in Russell E-mini positioning predicts greater subsequent small-cap downside risk than non-high observations, incremental to a fixed market-risk baseline.

**Primary outcome:** 20-XNYS-session maximum close-to-close drawdown severity on an investable Russell 2000 proxy, beginning at the first eligible session's adjusted regular-session open and ending at the adjusted close of session 20. The path includes the entry open and each subsequent adjusted close. Intraday lows are not mixed into this close-based measure.

**Price-source gate:** no price/outcome data were accessed in this phase. Before the first outcome is inspected, freeze one source and its research-use rights, exact retrieval method, adjusted OHLC convention, calendar, retrieval timestamp and response hash. No provider substitution or splicing is allowed. If a reproducible and permitted adjusted OHLC source cannot be established without an unapproved purchase, the outcome study remains blocked. No vendor contact, quote request or purchase is authorized.

Predeclared controls, all known before the eligible entry:
1. Prior 20-session realized volatility of the Russell proxy.
2. Prior 20-session total return of the Russell proxy.
3. Prior 252-session momentum of the Russell proxy.
4. Latest VIX close available before the entry timestamp.

The first-stage model is an expanding OLS model of drawdown severity on an intercept and these four controls. The incremental model adds only `HIGH_LM_CROWDING`. At each evaluation timestamp, training may use only prior observations whose complete 20-session outcome windows had matured before the current entry.

Primary estimand:

`Delta = mean(e_baseline | HIGH_LM_CROWDING) - mean(e_baseline | not HIGH_LM_CROWDING)`

where `e_baseline = observed drawdown severity - baseline-model prediction`. Positive `Delta` means high crowding is associated with greater downside severity beyond the controls.

Secondary predictive metric: `MAE_baseline - MAE_augmented` on identical out-of-sample observations; positive values indicate improved prediction.

The 20-session outcome is a fixed research outcome window, not a minimum or maximum strategy holding period. No portfolio holding-period rule is imposed.

## 5. Chronology, sample and inference

- The 480 historical observations are a fixed feature-reference snapshot only. They are not prospective training observations and have no historical return labels.
- Prospective training begins with the first actual scheduled first-seen Russell events after the snapshot. Each event can enter training only after its full 20-session outcome matures.
- Initial expanding-training gate: at least 52 matured prospective observations, including at least 20 high-crowding and 40 non-high observations.
- Minimum evaluation sample: 150 valid prospective observations, including at least 30 high-crowding and 100 non-high observations. If the gate is not met, continue collection; do not relax it. Plan for approximately 185 evaluation observations if the aim is a 90–95% chance of observing 30 high states under the simple 20.75% IID reference rate; this is only an event-count planning diagnostic, not a power calculation.
- Strict chronological walk-forward; no random split. No outcome window may overlap the current training information set.
- Because 20-session outcomes overlap weekly events, use 10,000 paired moving-block bootstrap resamples with four-report blocks and fixed seed `20261126`, plus Newey-West/HAC lag 4.
- Report the continuous percentile dose-response only as secondary, without threshold search.
- Leave-one-calendar-year-out sensitivity is required; report every year and do not hide sign reversals in a pooled statistic.
- No multiple-horizon or alternative-category fishing. The primary test is the single fixed 20-session downside-risk hypothesis.

**Pass criteria:** positive primary `Delta`; one-sided 95% moving-block bootstrap lower bound above zero; HAC one-sided p-value below 0.05; positive `MAE_baseline - MAE_augmented`; and positive primary-effect sign in at least 75% of eligible leave-one-year-out folds. Report effect sizes and all uncertainty intervals.

**Kill / no-go criteria:** non-positive `Delta`, bootstrap interval including zero, non-positive MAE improvement, or material instability under leave-one-year-out. A failed result is archived as failed; do not tune the threshold, substitute another CFTC category, change the horizon, or search another contract to rescue it.

## 6. Economic relevance and F80 boundary

This first stage tests an index-level small-cap risk-context hypothesis, not stock-level informed flow and not stock selection.

If and only if the first stage passes, a separate preregistration may test whether the risk-context feature adds value to the frozen F80/LTM portfolio. That later shadow test must preserve identical average gross exposure, holdings universe, execution convention, turnover/cost assumptions and calendar; a simple reduction in exposure is not evidence of incremental alpha. No F80 overlay or production change is authorized by this preregistration.

## 7. Current source disposition and controls

- CFTC Russell 239742: conditional prospective macro/small-cap risk candidate under this separate design.
- Broad CFTC archive: not a historical signal/backtest panel.
- Phase 387 ES/NQ: unchanged; its own prior-52-prospective-observation rule and 150-evaluation gate remain frozen.
- FINRA Phase 20C: current implementation remains NO-GO under Phase 593; no stale branch merge or holdout access.
- FINRA Reg SHO: all eight latest files remain rejected by the duplicate-symbol/facility-overlap gate.
- FINRA T1 ATS: date-level clock is validated, but effective-dated identity, historical universe membership and inactive-security prices remain unpassed; venue concentration is not investor identity.
- SEC Form 4 / 13F / Form 144: natural captures are operational, but current records remain metadata/backfill/baseline observations with zero signal-eligible rows.
- Options data: no sample, API request, quote, vendor contact, license or purchase; authorized options-data budget remains USD 0.
- No final holdout was opened. No price outcomes were inspected. No signal, alpha, OOS, bootstrap, LOO or portfolio test was performed.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, capital, exposure, costs, holding-period policy or production changes.
