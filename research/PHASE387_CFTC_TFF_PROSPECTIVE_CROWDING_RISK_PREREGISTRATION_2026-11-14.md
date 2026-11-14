# Phase 387 — CFTC TFF prospective index-crowding / downside-risk hypothesis

**Date:** 2026-11-14 UTC  
**Status:** preregistered design only; no forward-return test or signal admission.  
**Source:** CFTC Traders in Financial Futures (TFF), Futures Only, dataset `gpe5-46if`.  
**Initial contracts:** CME E-mini S&P 500 (`13874A`) and CME Nasdaq-100 Mini (`209742`). Russell E-mini is excluded from the initial test to avoid adding another contract-era and market hypothesis before the first two are evaluated.

## 1. Why this is a new hypothesis rather than a rerun of Phase 23C

Phase 23C tested a small, adaptive directional COT feature/direction search over 12 pseudo-OOS dates. Its results were weak and selection-sensitive; it is killed and must not be repeated or optimized.

Phase 387 asks a materially different, preregistered question: **does extreme Leveraged Money net-long positioning contain incremental information about subsequent downside risk / drawdown, rather than directional mean return?** The intended first use, if supported, is risk-regime context, not stock ranking and not a claim that Leveraged Money is informed capital.

No Phase 23C feature search, threshold tuning, horizon search, or reused pseudo-OOS/holdout is allowed.

## 2. Availability and data policy

- Historical CFTC archive rows remain schema/contract diagnostics only. They are **not** used to calculate signal thresholds, feature history, training labels, returns, or backtest observations.
- Only new report-date/contract keys first observed by the scheduled Phase 384 pipeline are eligible for this prospective study. The pipeline first-receipt timestamp is the conservative knowledge clock; a late arrival or revision is never backdated.
- A report can be used only from the first regular NYSE session strictly after its recorded first receipt. No same-day close/open is assumed.
- The weekday capture schedule is 22:15 UTC. The official CFTC schedule lists the report for positions as of 2026-11-10 for release on 2026-11-16 at 3:30 p.m. ET. The workflow is now merged to `main`; the first eligible observation must still be verified in the resulting scheduled run.
- The TFF source may change from weekly to semiweekly. The capture workflow's cadence guard must label WEEKLY / SEMIWEEKLY / IRREGULAR. The Phase 387 weekly feature definition is suspended if the observed cadence is not weekly; no weekly-to-semiweekly stitching or annualization is allowed without a new preregistration.
- Contract codes remain separate. Do not splice the pre-2017 Russell Mini era into Russell E-mini, and do not combine ICE Russell codes.

## 3. Frozen feature definitions

All positions are divided by reported open interest. Spreading positions remain separate and are never added to directional net:

- `LM_NET_OI = (Leveraged Money long - Leveraged Money short) / open_interest`
- `AM_NET_OI = (Asset Manager long - Asset Manager short) / open_interest`
- `DEALER_NET_OI = (Dealer long - Dealer short) / open_interest`
- `LM_AM_DIVERGENCE = LM_NET_OI - AM_NET_OI`
- `LM_CHANGE_4 = LM_NET_OI(t) - LM_NET_OI(t-4)`, only when all four report intervals are valid and each adjacent report gap is 6–8 calendar days.

Primary crowding variable: empirical mid-rank percentile of current `LM_NET_OI` against the **prior 52 valid, prospectively first-seen weekly observations** for the same contract:

`P_t = (count(x_j < x_t) + 0.5 * count(x_j = x_t)) / 52`.

The current observation is excluded from its own reference distribution. All 52 prior observations must be valid and the weekly cadence gate must pass; static archive rows cannot fill gaps. The first 52 prospectively captured reports establish the feature-reference warm-up and are excluded from evaluation.

Primary exposure state: `HIGH_LM_CROWDING = P_t >= 0.80`. The threshold is fixed at the 80th percentile. No alternative thresholds are to be searched to rescue a failed result. The continuous percentile is a predeclared secondary dose-response descriptor; it is **not** co-entered with the high-crowding indicator in the primary incremental model.

The Asset Manager and Dealer variables are predeclared controls / secondary descriptors. They are not independently searched for a better result in this phase.

## 4. Primary hypothesis and outcomes

**H1 (one-sided):** for ES and NQ separately, a high Leveraged Money net-long crowding observation predicts worse downside risk over the next 20 NYSE sessions than non-high-crowding observations, after conditioning on information already available at the signal time.

Primary outcome:
- 20-session maximum peak-to-trough drawdown **severity**, expressed as a positive loss magnitude, on a split/dividend-adjusted OHLC total-return path. The path starts at the first eligible session's regular-session open and includes each session's adjusted close through the close of session 20. Define severity as `max(0, max_{i<j}(1 - TR_j / TR_i))` over that path; the entry open is the first path point. If the frozen price source cannot provide consistently adjusted open/close values, the price gate fails; do not silently substitute another series.

Co-primary robustness outcome:
- mean downside semivariance over the 20 sessions, using the first session's open-to-close total return and subsequent close-to-close total returns: `mean(min(r_t, 0)^2)`.

The price vendor, retrieval method and adjustment convention must be fixed and archived (raw response/hash plus retrieval timestamp) before the first outcome is inspected. No mid-study provider substitution is allowed.

Secondary, non-promotion outcomes:
- forward total returns at 5, 10, 20 and 40 sessions;
- 20-session realized volatility;
- frequency of a loss worse than the unconditional 90th-percentile loss threshold fixed from the prospective test sample only after the preregistered sample is complete.

Price and control data are aligned to the first eligible session. Entry reference is that session's regular-session open; no price observed after the entry timestamp may be used as a predictor.

## 5. Controls and incremental-information test

The baseline risk model is fixed before outcome inspection and contains:
- prior 20-session realized volatility;
- prior 20-session SPY/QQQ total return;
- prior 252-session momentum;
- VIX close available before the first eligible session.

For each contract, fit a fixed ordinary-least-squares baseline model of drawdown severity on an intercept and these four controls. Standardize controls using only the current expanding training sample. At each prospective evaluation date, train only on prior observations whose full 20-session outcome window had already ended before the current entry timestamp.

The primary incremental model adds **only** `HIGH_LM_CROWDING` to that same baseline. The continuous percentile is a secondary dose-response analysis and is not co-entered with the binary indicator. No interactions, splines, feature selection, alternative thresholds or category substitutions are permitted.

For each evaluation observation, retain the baseline out-of-sample residual `e_t = y_t - yhat_baseline_t`. The primary estimand is `Delta = mean(e_t | HIGH_LM_CROWDING) - mean(e_t | not HIGH_LM_CROWDING)`; positive values mean high crowding is associated with worse downside severity beyond the fixed baseline controls. The secondary incremental prediction metric is `MAE_baseline - MAE_augmented` on the same observations; positive values indicate improved out-of-sample risk prediction.

The first-stage question is whether TFF adds incremental information to this index-level risk model. Only if it passes may a separate portfolio-level shadow test be preregistered against frozen F80/LTM. That later test must use identical holdings, costs, execution assumptions and average realized exposure; a simple lower-exposure portfolio is not evidence of alpha.

## 6. Chronology, sample size and inference

- The first 52 valid prospectively captured weekly reports per contract establish the prior-only percentile reference and are excluded from evaluation. Their outcomes may enter the expanding training set only after each 20-session window has fully matured.
- Evaluation begins only when at least 52 prior prospective training observations have fully matured and the current 52-report percentile is valid. At weekly cadence this is approximately after 56 reports; use actual maturity timestamps, not a hard-coded row number.
- Thereafter, observations are evaluated strictly forward in capture order. No random train/test split. Each prediction uses only prior fully matured observations.
- Minimum primary evaluation sample: 150 valid prospective observations per contract, including at least 30 high-crowding observations and 100 non-high observations. If the gate is not met, continue collecting; do not relax the thresholds.
- The 20-session outcomes overlap for weekly signals. Inference must account for serial dependence using 10,000 paired moving-block bootstrap resamples with block length fixed at four weekly observations and a recorded fixed random seed, plus Newey-West/HAC sensitivity with lag 4. A naive IID bootstrap is prohibited.
- Report ES and NQ separately before any pooled summary. Pooled results cannot conceal opposite signs.
- The primary test is one-sided for worse downside risk. Report the effect size, two-sided 95% interval, one-sided 95% lower bound, event count, missingness and all eligible observations. Secondary horizons are descriptive and subject to Holm adjustment; they cannot be used to promote the hypothesis if H1 fails.
- Leave-one-calendar-year-out / leave-one-calendar-regime-out sensitivity is required once at least three calendar years of prospective evaluation data exist. Do not consume the legacy holdout.

## 7. Kill / advance rules

Kill the hypothesis as a risk signal if any of the following occurs:
1. The primary out-of-sample residual downside-risk effect is non-positive, its dependence-robust one-sided 95% lower confidence bound is not above zero, or the augmented model fails to improve paired out-of-sample MAE after the minimum sample is met.
2. The result disappears after the fixed baseline controls.
3. ES and NQ have materially opposite signs without a preregistered economic explanation.
4. The effect is explained by prior momentum / volatility / VIX or by return-chasing rather than incremental positioning information.
5. Data cadence, first-receipt lineage, contract identity or price alignment fails.

Advance only to a separately preregistered F80/LTM shadow-overlay test if the primary effect is positive in the hypothesized direction, survives block bootstrap and HAC, is not driven by one calendar year, and has a plausible economic magnitude after realistic implementation costs. No live trade or production change is authorized by Phase 387.

## 8. Explicit exclusions and controls

- No use of static CFTC historical backfill for predictor features or outcome selection.
- No use of the legacy Phase 23C pseudo-OOS dates to claim replication.
- No use of the consumed legacy holdout.
- No stock-level signal, no trade instruction, no portfolio allocation, and no capital/exposure change.
- No vendor contact or data purchase.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No CAGR target and no minimum/maximum holding-period constraint is imposed on the broader strategy research; the 20-session primary risk horizon here is a hypothesis-specific outcome, not a portfolio holding-period rule.

## 9. Current status

Phase 384's prospective capture workflow has been merged to `main` in commit `e88e553afc235916e37e9236e1890b714163c229`. The hosted branch-push bootstrap passed 11/11 tests and preserved the 3,035-row historical baseline without overwriting it. The first scheduled capture is pending; until a scheduled run verifies a new report's first receipt, Phase 387 has no eligible observations.

Phase 387 is a preregistration only. It contains no empirical result and authorizes no alpha, OOS, portfolio, or production claim.
