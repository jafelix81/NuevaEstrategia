# Phase 46 — SEC 13D/13G amendment-aware state reconstruction specification — 2026-11-01

## Purpose
Convert the completed SEC 13D/13G PIT extraction into a pre-specified event/state dataset without treating filings or amendments as independent alpha observations.

## Current data audit
Latest Phase 35 artifact: `phase35-13dg-pit-event-crosswalk-audit`, run `41306633592`, artifact `13091036734`, digest `sha256:54243a2d73019cec9a20636723da1f8562dbbac0a60caf87312a2aad68ac0594`.

The artifact contains 20,254 successfully parsed filings from 20,266 candidates. Twelve document-resolution failures remain, all concentrated in one issuer CIK (`2012383`) and currently reflect SEC HTTP 503/time-out retrieval failures rather than parser/schema failures. This must be treated as a retrieval-quality issue and not silently dropped from coverage accounting.

Key field coverage in the latest artifact:
- filing_date: 20,254 / 20,254
- event_date: 19,668 / 20,254 (97.11%)
- percent_class: 19,969 / 20,254
- shares_beneficially_owned: 16,750 / 20,254
- reporting_person_type: 10,041 / 20,254
- reporting_person: 3,502 / 20,254
- purpose_text: 261 / 20,254
- report_date: unavailable in the parsed dataset

## PIT rule
`filing_date` is the information-availability date. No variable may use `event_date`, report date, or any later amendment to construct a signal before the corresponding filing_date.

If a filing is published after the market close, the implementation should use the next tradable session for execution. If exact acceptance/delivery time is unavailable, the conservative default is next-session execution for all filings rather than same-day execution.

## State key hierarchy
The preferred state key is:
1. issuer CIK + reporting person identifier, when a stable reporting-person identifier can be reconstructed;
2. issuer CIK + normalized reporting-person name, when reliable;
3. issuer CIK + filing-level reporting-person group only as a fallback.

Do NOT construct an ownership state by issuer alone when multiple reporting persons are present. Doing so would mechanically aggregate unrelated holders.

## Amendment handling
Two constructions must be generated once and evaluated independently:

### A. PIT-update construction
Every filing is an information update. For each reporting group, compare the newly disclosed ownership state with the most recent prior disclosed state available strictly before the filing date. The signal is the delta, not the absolute threshold.

### B. Original-only construction
Original 13D/13G filings create entry events. Amendments update the state but do not create independent entry observations. This construction is deliberately simpler and acts as a robustness check against amendment-driven pseudo-replication.

No ex-post selection between A and B is permitted.

## Candidate signals — pre-specified
The initial test set is deliberately small:

1. **New stake:** first observed beneficial ownership above 5% for a reporting group.
2. **Ownership increase:** positive delta in percent_class versus prior state.
3. **Ownership decrease:** negative delta in percent_class.
4. **Material increase/decrease:** delta above a pre-specified absolute threshold and above a relative-to-prior threshold.
5. **13D versus 13G:** separate families; no pooled estimate initially.
6. **Persistence:** repeated positive/negative updates by the same reporting group over a fixed ex-ante window.

Raw `percent_class > 5%` is explicitly excluded as an alpha signal because it is largely a regulatory threshold-selection effect.

## Coverage and missing-data policy
- Missing reporting-person identity is not imputed.
- Missing ownership fields do not become zero.
- Signals requiring a missing field are marked unavailable, not neutral.
- The 12 retrieval failures remain in the denominator for coverage reporting and are excluded only from the specific signal observation if they cannot be repaired.
- The 27 unresolved universe tickers remain a separate universe-coverage gate and cannot be silently removed without documenting historical-ticker/delisting/survivorship classification.

## Dependence controls
Because filings are highly concentrated by issuer and some financial institutions generate many observations, evaluation must include:
- issuer-clustered bootstrap;
- equal issuer weighting;
- equal-event weighting as a secondary diagnostic only;
- leave-one-issuer-out diagnostics for the largest contributors;
- no issuer may dominate the headline result solely through repeated amendments.

## Predictive versus return-chasing controls
For every signal, measure:
- pre-event momentum and abnormal return;
- market/sector-relative momentum;
- post-filing drift;
- signal strength conditional on pre-filing momentum buckets.

A positive result that disappears after controlling for pre-filing price movement is classified as return-chasing, not independent smart-money information.

## OOS protocol
No optimization on the final OOS period. Use chronological train/validation/OOS splits, with all signal thresholds frozen before the final OOS evaluation. Compare each candidate against `F80_TOP20_PARTIAL50_BASELINE_C20` using identical exposure, transaction costs and portfolio construction.

Required diagnostics: mean/median forward return, hit rate, Sharpe-like risk-adjusted metric, drawdown, turnover/cost impact, bootstrap confidence intervals, and leave-one-issuer-out stability. A signal must demonstrate incremental information rather than merely positive standalone returns.

## Kill criteria
Immediately archive a candidate as failed if:
- it is driven by one issuer or a small cluster of issuers;
- it disappears under issuer-clustered bootstrap/LOO;
- it disappears after controlling for pre-filing momentum;
- it depends materially on same-day execution unavailable ex ante;
- its apparent alpha is caused by the regulatory 5% threshold itself;
- it improves raw return but worsens risk-adjusted performance after identical costs/exposure.

## Decision
**Phase 46 specification: READY FOR IMPLEMENTATION once the remaining retrieval failures and 27 universe-mapping gaps are classified. No alpha result is claimed and `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.**
