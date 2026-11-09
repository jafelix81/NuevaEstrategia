# Phase 225 — SEC Schedule 13D/G event-time semantics and amendment audit

**Date:** 2026-11-08  
**Disposition:** KEEP 13D AND 13G SEPARATE; EVENT DATE IS NOT PUBLIC AVAILABILITY OR PROOF OF TRADE DATE  
**Research class:** immutable-source / event-semantics audit only. No forward returns or alpha test.

## Executive decision

The Phase 124 stratified filing sample shows a strong difference between Schedule 13D and Schedule 13G event-date behavior. In the weighted sample, 13G event dates are much more often quarter-end and have materially longer event-to-filing lags. This is consistent with distinct reporting and threshold mechanics. It is **not** proof that the event date is a transaction date, nor evidence of post-publication alpha.

Do not pool 13D and 13G into one generic institutional-flow feature. Preserve the event date for event characterization, but use SEC-HEADER ACCEPTANCE-DATETIME as the knowledge clock. The conservative daily availability boundary remains the first regular U.S. equity session whose open is strictly after acceptance.

## 1. Immutable source and integrity

Source: Phase 124 global SEC 13D/G stratified sample.

- Workflow run: [42073725379](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42073725379)
- Source artifact: [13436764625](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42073725379/artifacts/13436764625)
- Artifact ZIP SHA-256: `85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc`
- CSV SHA-256: `be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5`
- Sampling frame: 43 quarters, 2016Q1–2026Q3; quarter × form family × index-amendment strata.
- 600 source rows; 599 actual 13D/G submissions; one confirmed non-13D/G index alias quarantined.
- Phase 225 reverified 600/600 raw submission hashes and SEC-header accession, acceptance and filing-date fields; 599/599 actual primary 13D/G documents; 102/102 structured XML event dates.

Phase 213 recovered 553/599 event dates (92.32% unweighted): 451 HTML label-nearest-date parses and 102 structured XML dates. Unresolved: 35 HTML documents without the event label and 11 with the label but no unambiguous nearby date.

Phase 214 independently reproduced the 497 legacy-HTML date/status outcomes 497/497 using BeautifulSoup/lxml. That is parser reproducibility, not a legal/economic gold standard; both implementations use the same event-label/nearest-date rule.

## 2. Event-date lag differs materially by form family

Weighted estimates use the Phase 124 stratum design weights. Weighted medians and percentiles are descriptive weighted quantiles, not confidence intervals.

| Filing cohort | N / parsed | Weighted date coverage | Quarter-end among parsed | Weighted median filing − event | Weighted P90 | Maximum |
|---|---:|---:|---:|---:|---:|---:|
| 13D initial | 86 / 82 | 95.70% | 3.49% | 10 days | 48 days | 921 days |
| 13D amendments | 128 / 123 | 96.14% | 2.38% | 3 days | 17 days | 313 days |
| 13G initial | 142 / 131 | 92.98% | 63.08% | 37 days | 47 days | 379 days |
| 13G amendments | 243 / 217 | 89.79% | 82.27% | 41 days | 45 days | 181 days |

Overall family summaries:

- **13D:** 205/214 dates parsed; weighted coverage 96.04%; weighted quarter-end share 2.63%; weighted median filing-event lag 4 days; weighted P90 21 days.
- **13G:** 348/385 dates parsed; weighted coverage 90.73%; weighted quarter-end share 76.44%; weighted median filing-event lag 40 days; weighted P90 45 days.

There were 31 parsed rows whose event date equaled the filing date and zero future event dates. There were 19 parsed rows with lags over 90 days and three over 365 days. The longest observed lag was 921 calendar days on a 13D initial filing. These long-lag observations must not be backdated into a tradable signal.

**Interpretation:** 13G event dates—especially amendments—often behave like quarter-end reporting/threshold dates. They must not be treated as transaction-level institutional flow. 13D event dates are much less concentrated at quarter-end, but still do not establish public knowledge time.

## 3. 13G rule-designation subset

Only 68 XML 13G rows in this sample carried parsed rule designations. This is a limited structured-XML subset, not a representative estimate for all 13G filings.

| XML 13G rule | N | Quarter-end among parsed (weighted) | Weighted median filing − event |
|---|---:|---:|---:|
| Rule 13d-1(b) | 44 | 85.80% | 36 days |
| Rule 13d-1(c) | 15 | 73.84% | 43 days |
| Rule 13d-1(d) | 9 | 55.60% | 38 days |

Do not extrapolate these percentages to the 497 legacy HTML filings or to the entire filing population.

## 4. Amendment markers are not perfectly concordant

Across 599 actual filings:

- Index form suffix /A: 371.
- Positive cover-page amendment number: 376.
- Cover-page amendment number zero: 4.
- Cover-page amendment number missing/unresolved: 219.
- 11 rows were not indexed with /A but had a positive cover-page amendment number.
- Six rows were indexed with /A but had no positive cover-page amendment number.

The index suffix and cover-page marker must both be retained. Neither alone is a complete amendment-lineage solution. Previous-accession links, where present, still require validation; missing links must not be guessed from issuer or filer names.

## 5. Regulatory-era descriptive split

The sample was also split at the known rule-change dates, solely as a descriptive diagnostic:

- 13D, before/after 2024-02-05: weighted median lag 4/2 days.
- 13G, before/after 2024-09-30: weighted median lag 41/38 days; weighted quarter-end share 74.80%/81.73%.

These are not causal estimates of the rule changes. The post-reform strata are smaller and the sample was not designed to estimate a regulatory treatment effect.

## 6. Binding interpretation and next gates

1. Preserve event date, filing date and acceptance datetime as separate fields.
2. Never use event date as a public-knowledge timestamp. Use next-session-after-acceptance conservatively.
3. Keep 13D initial, 13D amendment, 13G initial and 13G amendment as separate event classes.
4. Treat 13G quarter-end observations as reporting/threshold snapshots unless the underlying filing establishes a different mechanism.
5. Continue deterministic amendment-state reconstruction, reporting-person/group normalization and effective-dated CUSIP/security-class identity, including ADRs, ETFs/series, corporate actions and delisted securities.
6. Only after those gates pass, preregister a 13D-specific event hypothesis and test post-publication returns separately from pre-filing run-up/return-chasing. Compare incremental information against frozen LTM/F80 with chronological OOS, identical exposure/costs, bootstrap and LOO.

## 7. Reproducibility and controls

- Auditor: `research/phase225_13dg_event_semantics_lag_audit.py`
- Tests: `research/test_phase225_13dg_event_semantics_lag_audit.py`
- Result: `research/phase225_13dg_event_semantics_lag_audit_result.json`
- Local validation: 7/7 tests passed, including full immutable-artifact integration with ZIP and CSV hashes.
- No Phase 225 hosted CI run is claimed; the commit is marked `[skip ci]` to avoid broad PR workflow fan-out.
- No forward returns, feature selection, alpha test, bootstrap/LOO, final holdout use, vendor purchase, universe change or production change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; legacy holdout remains `CONSUMED_NOT_PRISTINE`.

Related hosted runs:
- [Phase 213 event-date recovery](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42491346330) — success; artifact 13621103599.
- [Phase 214 independent DOM cross-parser](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42491346221) — success; artifact 13621163583.
