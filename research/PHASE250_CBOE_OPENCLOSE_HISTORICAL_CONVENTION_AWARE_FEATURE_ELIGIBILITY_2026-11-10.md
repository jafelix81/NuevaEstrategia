# Phase 250 — Cboe C1 EOD historical convention-aware feature eligibility

**Status:** HOSTED_CONVENTION_GATE_PASS_17_OF_17  
**Date:** 2026-11-10  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.  
**Scope:** source-specification and feature-contract audit only. No historical download, purchase, PIT admission, return test, holdout use, or production change.

## Finding

The current Cboe Open-Close product page lists C1 EOD history from 2005-01-03, while the official legacy specification separates pre-migration data (through 2010-12-31) from the post-migration format beginning 2011-01-02. The post-migration format changes origin granularity and size bucketing from original order size to execution size. The pre-2011 file has Customer/Firm categories and is not directly poolable with the post-2011 Customer/Pro-Customer/Broker-Dealer/Firm feature family.

For C1, the official product page documents:
- Total Exchange Volume calculated as (B+S)/2 through 2019-10-04, versus B+S under the current convention.
- Open Interest / Previous Open Interest shifted one day ahead through 2019-10-04.
- Previous Close as C1-only through 2019-10-04.
- C1 Global Trading Hours coverage beginning 2023-12-11.
- Final EOD files are typically delivered overnight; subscriptions provide preliminary and final versions, with OCC-sourced final Total Industry Volume and Open Interest potentially differing from OPRA preliminary values.

## Feature-level decision

Phase 248's 2019-10-07 cutoff is too restrictive for the raw participant directional-imbalance feature, because that feature is computed only from the same-day participant buy/sell contract-volume fields:
- Calls: opening/closing buy minus sell.
- Puts: opening/closing sell minus buy.
- Directional imbalance: signed net divided by gross volume for the same participant capacity.

This within-capacity imbalance does not require Total Exchange Volume, Total Industry Volume, Open Interest, Previous Open Interest, or Previous Close. The Phase 250 contract therefore allows a **separate post-migration 2011-01-02 through 2019-10-04 feature regime** for raw directional imbalance only.

The following remain blocked before 2019-10-07:
- Net flow divided by Total Exchange Volume.
- Any feature using C1 Open Interest or Previous Open Interest.
- Any denominator or feature that assumes the current C1 volume convention.

The participant-code regime is separately marked: Cboe's current spec maps legacy code W to Pro-Customer prior to October 2019. The GTH regime is separately marked from 2023-12-11 because EOD coverage then includes RTH and global sessions.

## Pre-2011 disposition

The pre-2011 C1 file uses a separate schema, Customer/Firm-only categories, and order-size rather than execution-size buckets. It is not admitted into the same panel. A distinct legacy parser and separately preregistered Customer-only hypothesis would be required; it must not be pooled with the post-2011 capacity family.

## PIT and economic limitations

Cboe's historical start date is a vendor-availability statement, not proof that each historical file was publicly or subscriber-available on its trade date. Current documentation says EOD subscriptions are typically delivered overnight and that preliminary/final files may differ for third-party-sourced volume/OI fields. No historical first-receipt logs or immutable vintage archive has been established.

No actual 2011–2019 daily files were acquired or inspected in this phase. Continuity, inactive/delisted coverage, security identity, corrections, licensing, and actual file completeness remain unverified. No return labels, F80 comparison, costs, bootstrap, LOO, chronological OOS, or holdout were used.

## Files

- `research/phase250_cboe_openclose_convention_gate.py`
- `research/test_phase250_cboe_openclose_convention_gate.py`
- `.github/workflows/phase250_cboe_openclose_convention_gate.yml`

## Hosted result

Pending. The workflow validates deterministic date boundaries and feature-level denominator eligibility only. Passing tests do not admit historical data to PIT or alpha.


## Hosted result — 2026-11-10 UTC

**PASS — 17/17 deterministic tests.** GitHub Actions run [42738486543](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42738486543), job 129573491343, completed successfully. The workflow compiled the Phase 250 module, ran all 17 regression tests, and enforced the 2011–2019 directional-only, pre-2019 volume-normalization block, pre-2019 OI block, and no historical PIT/alpha admission. No artifact was produced because the workflow contains only deterministic contract tests. This does not establish historical file continuity, PIT, or predictive value.
