# Phase 261 — Form 144/Form 4 global placebo multiplicity audit

**Date:** 2026-11-10 UTC  
**Disposition:** the document-linkage excess remains below 5% after a global Holm correction across all 13 valid recorded placebo sensitivities; the sparse Phase 260 ISO-week stratum remains non-significant. This is exploratory document-linkage evidence, not PIT or return alpha.

## Why this audit was needed

Phases 256, 257, 258 and 260 progressively corrected and narrowed the conditional Form 144/Form 4 placebo design. Each reported a within-phase Holm adjustment, but the accumulated research record did not yet show one multiplicity correction across every valid recorded variant. Phase 261 treats all 13 completed tests as one exploratory family.

The audit uses the exact hosted result artifacts. It verifies the result JSON SHA-256, shared Form 144/Form 4 source hashes, common sample counts and plus-one Monte Carlo p-values before calculating the global Holm step-down adjustment.

## Immutable sample

- Form 144 CSV SHA-256: 7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659
- Form 4 Q3 2026 inner ZIP SHA-256: a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3
- 1,451 eligible original notices; 1,460 proposed-sale tranches
- 10,525 selected Form 4 sale blocks
- 521 exact date/share links; 49 lower-confidence fallback links
- Form 4 snapshot ends 2026-09-30

| Phase | Hosted run | Artifact | Tests | Global Holm result |
|---|---:|---:|---:|---:|
| 256 — lag-preserving variants | 42767357624 | 13739833787 | 4 | 0.012987 each |
| 257 — temporal strata | 42775383915 | 13743028950 | 3 | 0.012987 each |
| 258 — accession-cluster strata | 42787526319 | 13749584173 | 3 | 0.012987 each |
| 260 — broad XNYS weekday/signature | 42790753569 | 13750319077 | 1 | 0.012987 |
| 260 — monthly XNYS weekday/signature | 42790753569 | 13750319077 | 1 | 0.043956 |
| 260 — ISO-week XNYS weekday/signature | 42790753569 | 13750319077 | 1 | 0.533467 |

**Result: 12 of 13 tests remain below 0.05 after one global 13-test Holm correction.** Eleven tests had zero exceedances in 1,000 replicates; the Phase 260 monthly test had 21; the ISO-week test had 533.

The plus-one Monte Carlo tail is (exceedances + 1) / 1001. Zero exceedances therefore means p=0.000999, not zero; its one-sided 95% binomial upper bound is approximately 0.002991.

## Interpretation and limits

The document-linkage excess survives the known-family correction. The smallest adjusted tail increases from the within-phase 0.002997 to 0.012987. The monthly XNYS stratum remains at 0.043956; the sparse ISO-week stratum is not significant at 0.533467.

This is not independent replication: Phases 257, 258 and 260 are nested sensitivities on the same selected 2026 Q3 Form 4 snapshot and Phase 69 Form 144 issuer panel. Holm does not require independent tests, but it does not cure sample selection, post-hoc hypothesis construction or a misspecified exchangeability assumption.

Phase 210 raw-date/date-plus-share placebos are excluded because Phase 256 showed they failed to preserve the selected 0–4-day filing-lag envelope. Phase 238's plan-flag test is a different endpoint; Phase 259 MOM120 is a separate portfolio-return hypothesis.

Form 144 is a proposed-sale notice, not proof of execution. Form 4 code S can include private dispositions. These results do not establish exchange execution, informed trading, market impact or predictive returns.

## Decision and next gate

Retain this as an exploratory document-linkage finding only. No PIT feature admission or forward-return test is authorized. The next meaningful test is independent multi-quarter replication with new immutable SEC Form 144/Form 4 artifacts. Raw SEC retrieval remains blocked by the missing authorized SEC_CONTACT_EMAIL Actions secret. A licensed, delisted-inclusive security/price source is also required before ADV20 or return testing.

No SEC request, vendor contact, purchase, return test, bootstrap/LOO, chronological OOS or holdout use occurred. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; production, universe and capital are unchanged.

Files: phase261_global_form144_form4_placebo_multiplicity_audit.py, test_phase261_global_form144_form4_placebo_multiplicity_audit.py, phase261_global_form144_form4_placebo_multiplicity_audit_result.json and phase261_global_form144_form4_placebo_multiplicity_audit.yml.
