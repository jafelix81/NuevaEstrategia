# Phase 220 — N-PORT short-share quantity versus NAV-exposure measurement audit

**Audit date:** 2026-11-08  
**Status:** `MEASUREMENT_SPEC_SUPERSEDES_PHASE219_PRIMARY_FEATURE_NO_ALPHA`  
**Scope:** pre-data measurement review and synthetic falsification only. No SEC retrieval, return calculations, holdout use or production changes.

## Executive finding

Phase 219's primary feature, `delta_short_pct_nav`, is a change in reported portfolio exposure, but it is not a pure measure of position building. The SEC defines N-PORT's balance, value and percentage-of-net-assets fields separately: balance is the reported quantity (interpreted using the unit field), currency value is the position value, and percentage is the value compared with fund net assets. The payoff profile separately identifies Long, Short or N/A. [SEC N-PORT README](https://www.sec.gov/files/nport_readme.pdf).

A fund's short percentage of NAV can rise even when it does not add a single share:
- the shorted security appreciates, increasing the marked short notional;
- fund NAV falls, increasing the same position's weight in the denominator.

Calling either event an increase in short-selling behavior would confound portfolio revaluation with position adjustment.

## 1. Synthetic counterexamples

All examples use a prior short position of 100 shares, prior price USD 100 and prior NAV USD 1,000,000.

| Case | Shares | Price | NAV | Change in short % NAV | Change in short shares |
|---|---:|---:|---:|---:|---:|
| Price rises 20%, no trade | 100 → 100 | 100 → 120 | 1,000,000 → 1,000,000 | +0.20 percentage points | 0% |
| NAV falls, no trade | 100 → 100 | 100 → 100 | 1,000,000 → 833,333.33 | +0.20 percentage points | 0% |
| Fund adds 10 short shares | 100 → 110 | 100 → 100 | 1,000,000 → 1,000,000 | +0.10 percentage points | +10% |

Thus, `delta_short_pct_nav` remains useful as an exposure-state descriptor, but it should not be the primary behavioral variable.

## 2. Superseding primary measurement

Preserve Phase 219 unchanged as the original preregistration. For the first economic test, supersede its primary feature with:

`delta_short_shares_pct = 100 × (Q_t_adjusted / Q_{t-1} − 1)`

where:
- (Q) is the absolute reported `BALANCE` for an explicit `PAYOFF_PROFILE=Short`, `UNIT=NS` common-equity row;
- the same `SERIES_ID` and effective-dated security identifier must be present in both report periods;
- the current quantity must be mapped to the prior share basis using a verified corporate-action factor;
- pairs affected by unverified splits, recapitalizations, ADR-ratio changes, mergers or other quantity-changing events are excluded;
- both periods must contain explicit short rows. An absent row is unknown, not zero; initiation/covering features remain deferred.

This is a change in reported share quantity between report dates. It is **not trade flow**, and N-PORT does not reveal when during the reporting interval the position change occurred.

## 3. Keep exposure state as a separate measure

Retain `delta_short_pct_nav` as a secondary state variable. If all required fields are verified, decompose the exposure change into:
1. quantity change marked at the prior report's price and normalized by prior NAV;
2. mark-to-market effect;
3. NAV-denominator effect.

Do not derive prior NAV from `pctVal` until its percentage-point convention and sign are validated across complete raw filings. Prefer the fund-level net-assets field when its exact schema and as-filed vintage are available. A decomposition is diagnostic, not a substitute for the quantity feature.

## 4. Point-in-time and economic protocol

- Preserve every accession and amendment as an immutable as-filed vintage.
- Compare consecutive publicly disclosed report periods for the same series; do not use a later amendment to rewrite what was known earlier.
- The knowledge clock remains SEC `ACCEPTANCE-DATETIME`; daily eligibility begins at the first full regular U.S. equity session whose open is strictly after acceptance.
- The fixed direction remains: larger positive short-share quantity changes predict lower subsequent residual equity returns.
- Retain the predeclared 5/20/63/126-session diagnostic horizons, lagged-return/volatility/liquidity/size/beta/sector controls, identical-exposure/cost comparison against frozen LTM/F80, date/registrant bootstrap and registrant/fund-series/issuer LOO.
- Report age and filing lag remain controls; no fixed lag is assumed.

## 5. Validation and limitations

The pure-Python auditor validates the measurement contract and three synthetic counterexamples. The 10 local regression tests cover quantity changes, price/NAV confounding, split adjustment, missingness, PIT and frozen controls.

No raw N-PORT holdings were downloaded or hashed. Series/amendment lineage, complete-holdings semantics, corporate-action factors, effective-dated listing identity and broad PIT universe coverage remain unestablished. No return/alpha test is authorized.

**Decision:** Phase 220 supersedes only Phase 219's primary feature definition before outcome inspection. The hypothesis direction is unchanged. F80 remains frozen; the legacy holdout remains `CONSUMED_NOT_PRISTINE`.
