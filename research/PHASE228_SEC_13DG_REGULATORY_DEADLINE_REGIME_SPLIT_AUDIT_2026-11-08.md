# Phase 228 — SEC 13D/G regulatory-deadline regime split

**Date:** 2026-11-08  
**Disposition:** KEEP 13D/13G SEPARATE; MODEL THE REGULATORY REGIME EXPLICITLY; NO ALPHA TEST.  
**Research class:** hash-pinned source re-analysis and descriptive event-to-filing timing audit.

## Executive decision

The Phase 124 stratified sample contains enough historical coverage to compare declared event-date-to-filing lags on either side of the two distinct compliance dates in the SEC's 2023 beneficial-ownership rule:

- **Schedule 13D:** revised deadlines effective **2024-02-05**.
- **Schedule 13G:** revised deadline compliance begins **2024-09-30**.
- Structured-data compliance is a separate date, **2024-12-18**.

The family-specific cutoffs matter. Applying the February 2024 date to 13G would misclassify the transition period. The 13G deadline changes were explicitly deferred until September 30, 2024. The structured-data date must not be treated as a change in knowledge time.

The sample shows a modest shortening in weighted median 13D event-to-filing lag, but 13G remains concentrated around quarter-end with a 45-day weighted P90. These are descriptive filing mechanics, not transaction timestamps or evidence of alpha.

## 1. Immutable source and reproduction

- Phase 124 run: [42073725379](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42073725379)
- Artifact: [13436764625](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42073725379/artifacts/13436764625)
- ZIP SHA-256: `85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc`
- CSV SHA-256: `be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5`
- 600 source rows; 599 actual filings; one index alias quarantined.
- 600/600 raw submission hashes and SEC headers verified.
- 599/599 primary 13D/G documents verified.
- 102/102 structured XML event-date values matched the Phase 124 source fields.

Event-date extraction was independently rerun from the raw submissions using the hash-pinned Phase 213 parsing rules. The legacy HTML dates remain label-nearest-date parses, not a legal gold standard.

## 2. Correct compliance cutoffs

| Family | Regime cutoff used | Rule transition |
|---|---|---|
| 13D | 2024-02-05 | Initial filing within five business days; material amendments within two business days |
| 13G | 2024-09-30 | Revised deadlines begin; exact deadline depends on filer category and trigger |
| 13D/G structured data | 2024-12-18 | Separate machine-readable filing compliance date |

Official SEC sources:
- [SEC adopting release 33-11253](https://www.sec.gov/files/rules/final/2023/33-11253.pdf)
- [SEC press release 2023-219](https://www.sec.gov/newsroom/press-releases/2023-219)
- [Federal Register 88 FR 76896](https://www.govinfo.gov/app/details/FR-2023-22678)

## 3. Family-level pre/post results

Weighted values use the original Phase 124 stratification weights. Weighted medians/P90 are descriptive weighted quantiles, not confidence intervals.

| Cohort | Filings / parsed | Weighted date coverage | Quarter-end event dates, weighted | Weighted median lag | Weighted P90 |
|---|---:|---:|---:|---:|---:|
| 13D before 2024-02-05 | 162 / 154 | 95.09% | 3.53% | 4 days | 27 days |
| 13D from 2024-02-05 | 52 / 51 | 98.95% | 0.00% | 2 days | 18 days |
| 13G before 2024-09-30 | 308 / 272 | 88.47% | 74.80% | 41 days | 45 days |
| 13G from 2024-09-30 | 77 / 76 | 98.89% | 81.73% | 38 days | 45 days |

### 13D initial versus amendments

| Cohort | Filings / parsed | Weighted median | Weighted P90 |
|---|---:|---:|---:|
| Pre-reform initial | 65 / 62 | 10 days | 48 days |
| Post-reform initial | 21 / 20 | 7 days | 86 days |
| Pre-reform amendments | 97 / 92 | 3 days | 17 days |
| Post-reform amendments | 31 / 31 | 2 days | 13 days |

The post-reform initial cohort is small (21 filings); its 86-day weighted P90 is driven by a long-lag observation. Do not read the median reduction as proof of universal compliance or a causal effect. The amendment lag shift is directionally consistent with the new two-business-day requirement, but event dates are not independently verified trade dates.

### 13G initial versus amendments

| Cohort | Filings / parsed | Weighted median | Weighted P90 | Quarter-end share, weighted |
|---|---:|---:|---:|---:|
| Pre-reform initial | 110 / 100 | 38 days | 47 days | 58.68% |
| Post-reform initial | 32 / 31 | 29 days | 45 days | 75.32% |
| Pre-reform amendments | 198 / 172 | 41 days | 45 days | 81.47% |
| Post-reform amendments | 45 / 45 | 39 days | 45 days | 85.02% |

13G amendment dates remain strongly quarter-end clustered. The observed 39-day post-cutoff weighted median and 45-day P90 are consistent with quarterly reporting windows. They do not identify the day an institution traded.

## 4. Important measurement caveats

1. **Different cutoffs:** 13D and 13G do not share one compliance date.
2. **Format break:** the December 18, 2024 structured-data mandate changes the availability of machine-readable fields. The higher post-cutoff parse coverage is partly a format/sample-composition effect, not proof of faster disclosure.
3. **Sample design:** this is a stratified 599-filing sample, not an unstratified random sample. Weighted estimates are descriptive; no standard errors, significance tests or causal claims are made.
4. **Small post-reform 13D cohort:** only 52 total filings, including 21 initial filings.
5. **Event date:** the declared event date is not necessarily a trade date and never replaces the knowledge clock.
6. **Knowledge time:** retain SEC-header ACCEPTANCE-DATETIME; for daily research, no same-day use and no event-date backdating.
7. **No population extrapolation:** the 13G XML rule-designation subset remains incomplete for legacy HTML filings.

The committed Phase 225 result JSON did not include the regulatory-era split present in the Phase 225 audit logic. Phase 228 publishes the split as a separate, hash-pinned result rather than silently rewriting the earlier artifact.

## 5. Research decision

- Keep 13D initial and 13D/A as separate event cohorts.
- Keep 13G initial and 13G/A as delayed ownership-disclosure cohorts, not transaction-level flow.
- Do not pool 13D and 13G into a single institutional-flow score.
- Any future event study must use acceptance datetime and next-session execution, an effective-dated security crosswalk, full historical active/delisted universe, and amendment-state reconstruction.
- No forward returns, incremental-alpha test, bootstrap/LOO, holdout use or production change is authorized by Phase 228.

## 6. Reproducibility

- Auditor: [phase228_13dg_regulatory_regime_split_audit.py](phase228_13dg_regulatory_regime_split_audit.py)
- Tests: [test_phase228_13dg_regulatory_regime_split_audit.py](test_phase228_13dg_regulatory_regime_split_audit.py)
- Result: [phase228_13dg_regulatory_regime_split_audit_result.json](phase228_13dg_regulatory_regime_split_audit_result.json)

The auditor checks the Phase 124 ZIP digest, delegates raw-file/header/XML validation to the Phase 213 immutable-source parser, calculates family-specific pre/post and initial/amendment cohorts, and asserts the key counts/weighted medians. Four local unit tests pass. The full hash-pinned raw source was independently re-parsed locally: 600 raw hashes, 600 headers, 599 primary filings and 102 XML event dates verified.

**Controls:** `F80_TOP20_PARTIAL50_BASELINE_C20` frozen; legacy holdout remains `CONSUMED_NOT_PRISTINE`; no return or alpha test; no vendor purchase; no production or universe change.
