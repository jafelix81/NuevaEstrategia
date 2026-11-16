# Phase 439 — Form 4 legacy identity bridge: unit-weighted coverage audit

**Date:** 2026-11-16 UTC  
**Disposition:** The previously repeated 53/96 figure is transaction-row-weighted and materially overstates independent identity evidence. Do not use it as coverage or as evidence that the 95% gate is close to passing. No alpha test is authorized.

## Executive finding

I re-opened the immutable Phase 346 output artifact and recalculated the same evidence at four levels: transaction rows, distinct issuer CIKs, distinct issuer-accession units, and distinct issuer-CIK × filing-date units.

The Phase 346 sample contains 112 candidate rows, of which 96 were eligible under its pre-transaction fresh-anchor rule. The reported 53 exact ticker-prose matches among those 96 rows (55.21%) are not 53 independent observations. **Forty-eight of the 53 matches come from one issuer, ONTC (CIK 1427352), across 11 accessions.**

| Unit of analysis | Exact ticker evidence | Denominator | Rate |
|---|---:|---:|---:|
| Transaction rows | 53 | 96 | 55.21% |
| Distinct issuer CIKs | 4 | 15 | 26.67% |
| Distinct issuer-accession units | 16 | 42 | 38.10% |
| Issuer CIK × filing-date units | 16 | 41 | 39.02% |

The 55.21% row rate is dominated by repeated transaction rows from one issuer. It is not a measure of breadth across issuers or independent filing events.

## 1. Immutable source and reproducibility

- Source: Phase 346 legacy HTML identity bridge artifact [13985120745](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43307873506/artifacts/13985120745).
- Artifact ZIP SHA-256: `b526112713cc4942db3c4a9050000e2da4190a17c1fe1f9cc6ded962693b6e9c`.
- Input member: `phase346_output/phase346_candidate_evidence.csv`.
- Candidate CSV SHA-256: `418c66f70c5ad67e065f59de312a961a0061dae79441ef116c1173424aedeb0b`.
- No new SEC request was made. The artifact was downloaded and hashed; the script rejects any other artifact/CSV hash.
- The 96-row denominator is the Phase 346 pre-transaction-fresh subset. Same-day/post-transaction and stale/no-anchor rows remain excluded.

## 2. Concentration of the 53 row matches

| Issuer CIK | Form 4 symbol | Matched rows | Distinct accessions | Share of matched rows |
|---|---|---:|---:|---:|
| 1427352 | ONTC | 48 | 11 | 90.57% |
| 1387713 | NLN | 2 | 2 | 3.77% |
| 749647 | CLSN | 2 | 2 | 3.77% |
| 1046356 | BMHC | 1 | 1 | 1.89% |
| **Total** | | **53** | **16** | **100%** |

ONTC alone contributes 48/96 (50.00%) of every PIT-eligible row in this purposive sample. The row-weighted rate is therefore heavily issuer-concentrated.

## 3. Period breakdown

| Cohort | PIT rows | Issuers | Exact-match rows | Matched issuers |
|---|---:|---:|---:|---:|
| 2006 Q1 | 6 | 4 | 1 | 1 |
| 2012 Q1 | 90 | 11 | 52 | 3 |
| **Total** | **96** | **15** | **53** | **4** |

In 2012 Q1, ONTC accounts for 48 of the 52 matched rows. The other two matched issuers contribute two rows each. This confirms that row duplication, not broad cross-issuer recovery, drives most of the apparent match count.

## 4. Interpretation and correction

The old 53/96 figure remains arithmetically correct **only as a transaction-row-weighted exact ticker-evidence rate**. It must not be described as:
- 55.21% issuer coverage;
- 55.21% independent filing coverage;
- 55.21% coverage of the frozen 335-name universe; or
- a pass, or near-pass, of the 95% security-identity admission gate.

The 4/15 issuer rate and 16/42 accession rate are still statistics from a small, purposively selected historical sample, not estimates of population coverage. They are nevertheless the more appropriate diagnostics for whether the bridge generalizes beyond one issuer. The current sample shows that it does not.

This phase does not claim that the other 11 issuers are unidentifiable by every possible source. It says only that the audited Phase 346 legacy-HTML exact-ticker evidence does not establish their security identity. Exchange-only prose, class-only evidence, ticker mismatches and missing evidence remain separate grades; none is silently promoted.

## 5. Decision and next gate

**Decision: RECLASSIFY_53_OF_96_AS_ROW_WEIGHTED_ONLY; LEGACY_IDENTITY_BRIDGE_NOT_ADMITTED.**

Before any Form 4 return test:
1. Reconstruct an issuer/security crosswalk at distinct issuer and filing-event level, not transaction-row level.
2. Resolve ticker/class/exchange conflicts with effective-dated evidence available no later than the transaction date.
3. Measure coverage against the actual frozen universe and historical membership, including inactive/delisted securities.
4. Keep the 95% admission threshold; do not lower it to compensate for this result.
5. Only after coverage passes, pre-register the discretionary-purchase hypothesis and test it chronologically against frozen LTM/F80 with identical exposure/costs, block bootstrap, LOO and untouched OOS.

No returns, alpha, OOS, bootstrap, LOO or holdout test was run. No universe, parameter, capital, exposure, production or frozen-baseline change was made.

## 6. Reproduction

Download the Phase 346 artifact linked above, then run:

```bash
python research/phase439_form4_identity_unit_coverage_audit.py \
  --input phase346_legacy_html.zip \
  --output phase439_summary.json
```

The script validates the artifact ZIP and embedded candidate CSV SHA-256 values before counting. Five offline tests cover duplicate-row inflation, PIT filtering, issuer/accession/filing-unit denominators, boolean unknowns and the no-alpha guard.
