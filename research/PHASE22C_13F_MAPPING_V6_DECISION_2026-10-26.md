# Phase 22C — SEC 13F Mapping Feasibility V6 Decision

Date: 2026-10-26
Source artifact: phase22c-sec-13f-mapping-audit-v6 (run 40263943529, artifact 12625179380)

## Result

The corrected bounded mapping audit remains **INSUFFICIENT COVERAGE FOR PRODUCTION**.

Frozen universe: 335 names; SEC current matches: 301.

Historical candidate coverage:

| Quarter | Matched | Candidate | Coverage |
|---|---:|---:|---:|
| 2016Q1 | 212 | 301 | 70.43% |
| 2020Q1 | 246 | 301 | 81.73% |
| 2024Q1 | 280 | 301 | 93.02% |

The mapping logic correctly rejects ambiguous candidates and uses current names, SEC former-name aliases, and deterministic token matches. However, historical coverage is materially below the frozen-universe requirement in earlier periods.

## Decision

Do not run 13F economic alpha tests against the reduced matched subset. That would change universe composition and make the comparison with frozen LTM/F80 non-identical.

13F remains an institutional-positioning hypothesis, but is **parked for production** unless a better historical security identifier / issuer crosswalk can recover sufficient coverage without look-ahead or survivorship leakage.

## Research implication

The declining coverage problem is consistent with identifier/name drift rather than evidence that institutional ownership is uninformative. A future crosswalk could use stable identifiers (CIK + historical CUSIP/issuer mappings) if a reproducible source is found. No commercial or manually curated mapping should be introduced silently.

## Frozen baseline

`F80_TOP20_PARTIAL50_BASELINE_C20` remains unchanged.
