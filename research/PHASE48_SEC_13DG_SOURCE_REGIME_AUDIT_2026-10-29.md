# Phase 48 — SEC 13D/13G source-regime feasibility audit

## Objective

Determine whether SEC Schedule 13D/13G can be used as a reproducible point-in-time research source across the historical period without treating the pre-2024 and post-2024 filing formats as the same data regime.

## Current evidence

SEC documentation states that structured Schedule 13D/13G filing became mandatory on December 18, 2024. Before that date, HTML/ASCII filings remained permitted; after the cutoff, the schedules use the structured XML regime, subject to limited exceptions for certain amendments. The audit therefore samples both regimes separately.

## PIT rule

`filing_date` is the knowledge date. Event/report dates are descriptive attributes only and may never be used as the information-availability timestamp.

## Gate

The audit checks:

1. Current frozen-universe CIK resolution.
2. Historical filing availability from 2020-10-01 through 2026-09-30.
3. Separate pre-cutoff and post-cutoff document regimes.
4. Download success and presence of issuer CIK, CUSIP, event date, reporting person and ownership percentage fields.
5. No inference that absence of a filing means zero ownership.
6. No authorization for alpha or historical-universe membership inference.

## Important limitation

This phase is a source-regime audit only. It does **not** establish historical F80 membership or a valid CUSIP/ticker crosswalk. A PASS here only permits the next identity/coverage gate.

## Next decision

If both regimes show reproducible field coverage, continue to historical issuer/security identity. If pre-cutoff extraction is materially incomplete, do not backfill missing observations as zeros; either kill the source for the F80 research universe or restrict any future test to a demonstrably comparable regime and document the loss of historical power.
