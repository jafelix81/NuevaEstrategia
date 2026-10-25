# Phase 36 — FINRA ATS / off-exchange historical feasibility

Date: 2026-10-25

## Motivation
Phase 35 SEC 13D/13G failed the production universe-coverage gate (83.3% resolved issuer coverage). The next Smart Money candidate should capture institutional/off-exchange behavior directly and have a reproducible historical publication boundary.

## Candidate source
FINRA Alternative Trading System (ATS) Transparency / OTC Transparency data.

FINRA documentation states that ATS weekly equity volume and trade-count information is published by security and ATS. Tier 1 NMS aggregate data are published with a two-week delay; other NMS/OTC categories with a four-week delay. The historical download archive is documented back to 2016 in the public user guide, while the underlying ATS reporting requirement dates to 2014.

## PIT rule
The signal knowledge date must be the publication/download availability date, not the trading week itself. For any weekly report, only the following week's first eligible trading session after the documented publication delay may enter the signal. `Shares_Last_Updated` and `Trades_Last_Updated` are data-revision diagnostics, not signal dates.

## Initial hypotheses (pre-registered, no threshold tuning)
1. Abnormal ATS share-volume ratio versus the stock's own recent history.
2. Abnormal ATS share-volume ratio relative to total consolidated volume.
3. ATS share-volume change plus subsequent price/volume confirmation.
4. Large ATS block activity as a separate hypothesis, not conflated with ordinary ATS volume.
5. ATS vs non-ATS divergence where both are available.

## Feasibility gates
- Frozen-universe coverage >= 90% in the core OOS window and >= 85% in earlier training periods.
- Historical reports available without survivorship filtering; unresolved symbols must be measured explicitly.
- Publication delay and last-update fields reproducible.
- No use of revised weekly totals before their publication date.
- Enough weekly observations per issuer to support chronological OOS testing.
- Signal can be residualized against frozen LTM/F80 and tested with identical exposure.

## Research rule
Do not run an economic alpha test until the historical coverage/PIT audit passes. If coverage or publication timing fails, archive the source without forcing an alpha conclusion.

## Current state
STAGED — feasibility only. The official FINRA documentation confirms the source is public and historically downloadable, but the actual historical archive still needs to be sampled programmatically in a GitHub Actions environment before any coverage claim is made.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
