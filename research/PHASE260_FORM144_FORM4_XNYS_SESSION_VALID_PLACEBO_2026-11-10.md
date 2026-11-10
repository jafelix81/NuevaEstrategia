# Phase 260 — Form 144/Form 4 XNYS-session-valid accession-preserving placebo

**Date:** 2026-11-10 UTC  
**Disposition:** document-linkage excess survives the broad and monthly XNYS-session-valid placebos, but not the sparse ISO-week placebo. This remains descriptive linkage evidence, not informed-trading or return-alpha evidence.

## Why this stricter null was needed

Phase 258 preserved multi-block Form 4 accessions and the original 0–4 calendar-day filing-lag envelope, but a shuffled calendar lag could reconstruct a transaction date on a weekend or market holiday. That creates an implausible synthetic transaction date for the exchange-traded subset and could make the null too permissive.

Phase 260 uses the XNYS calendar (exchange_calendars 4.13.1) and permutes only single-block accessions whose observed transaction date is an XNYS session. Each randomization group shares:
- issuer and permanent reporting-owner CIK;
- filing weekday;
- the identical set of 0–4 calendar-day lags that reconstruct to valid XNYS sessions;
- and, in separate sensitivity strata, filing month or ISO week.

Filing dates remain fixed. Multi-block accessions remain frozen intact. Single-block accessions with non-session transaction dates are also frozen, not silently discarded from the original linkage graph.

## Immutable sample

The SHA-pinned Phase 69 Form 144 and Phase 39 Form 4 artifacts are unchanged from Phase 258.

| Item | Count |
|---|---:|
| Form 144 panel rows | 21,634 |
| Eligible original notices / proposed-sale tranches | 1,451 / 1,460 |
| Form 4 submissions / non-derivative rows | 38,152 / 59,885 |
| Form 4 sale blocks / accessions | 10,525 / 8,897 |
| Single-block / multi-block accessions | 7,512 / 1,385 |
| Blocks frozen in multi-block accessions | 3,013 |
| Exact date/share links / lower-confidence fallbacks | 521 / 49 |
| Exact links in single-/multi-block accessions | 414 / 107 |
| Single-block accessions with XNYS-session transaction dates | 7,499 |
| Single-block non-session accessions frozen | 13 |

## Results — 1,000 permutations per stratum

| Conditional stratum | Mutable session-valid accessions | Observed exact links | Null mean | p95 | Max | Exceedances | Raw plus-one tail | Holm |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Issuer × owner CIK × filing weekday/signature | 492 | 25 | 12.481 | 18 | 23 | 0/1,000 | 0.000999 | 0.002997 |
| Issuer × owner CIK × month × weekday/signature | 166 | 9 | 4.486 | 8 | 9 | 21/1,000 | 0.021978 | 0.043956 |
| Issuer × owner CIK × ISO week × weekday/signature | 43 | 1 | 0.533 | 1 | 1 | 533/1,000 | 0.533467 | 0.533467 |

The broad and monthly conditional placebos retain an elevated exact-link count after preserving XNYS-session validity; the ISO-week result does not. The weekly stratum is very sparse (43 mutable accessions and one observed link), so it is inconclusive rather than evidence that the broader relationship disappears.

The mutable counts are much smaller than Phase 258's because Phase 260 also requires the same filing weekday and identical XNYS-valid candidate-lag signature within each group. The 521-link graph itself is unchanged; this is a stricter subset test, not a redefinition of the original matches.

## Interpretation and limits

- Phase 260 and Phase 258 use the same selected Form 144 issuer panel and the same 2026 Q3 Form 4 snapshot. They are nested sensitivity analyses, **not independent replications**.
- Form 144 is a proposed-sale notice, not proof of execution.
- Form 4 code S can include private dispositions; the 13 non-session single-block accessions are frozen rather than presumed to be exchange trades.
- Bulk filing dates are date-only. First-public-availability timestamps and full amendment/vintage lineage remain unresolved.
- The randomization assumes exchangeability within issuer/owner/time/weekday/candidate-signature strata. It is a conditional document-linkage placebo, not a causal design.
- No stock returns, PIT feature, alpha, bootstrap/LOO, chronological OOS or holdout test was run.

**Decision:** retain the finding only as document-linkage evidence and prioritize multi-quarter replication. Strict PIT, feature admission and alpha authorization remain false. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; production, universe and capital are unchanged.

## Reproducibility

- Hosted run: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42790753569
- Job: 129743242080; 15/15 tests passed.
- Artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42790753569/artifacts/13750319077, SHA-256 0962fa7dd62ecaba0992f0c2537b11ac79147e2466ddb23d5915909ee4daf565.
- Code: research/phase260_form144_form4_xnys_session_placebo.py
- Tests: research/test_phase260_form144_form4_xnys_session_placebo.py
- Workflow: .github/workflows/phase260_form144_form4_xnys_session_placebo.yml

Phase 260 used the immutable Phase 69 Form 144 artifact (41959603351 / 13385365595) and Phase 39 Form 4 artifact (40606706518 / 12781850078); both input SHA-256 values are recorded in the result artifact.
