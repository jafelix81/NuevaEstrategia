# Phase 496 — SEC Form 4 accession payload, acceptance-clock and transaction-semantics audit

**Audit date:** 2026-11-19  
**Source capture:** Phase 476 run [44440313382](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44440313382)  
**Audit run:** [44474285899](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44474285899)  
**Artifact:** [14506425194](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44474285899/artifacts/14506425194)  
**Disposition:** PAYLOAD_AND_ACCEPTANCE_FEASIBILITY_ONLY. No event study, alpha test or signal admission.

## 1. Retrieval and reproducibility

The audit processed exactly 637 unique Form 4 accessions from the bounded first-seen metadata cohort in source run 44440313382.

| Control | Result |
|---|---:|
| Accessions attempted | 637 |
| SEC filing indexes retrieved | 637 |
| Index acceptance clocks parsed | 637 |
| Complete submission headers retrieved | 637 |
| SGML acceptance clocks parsed | 637 |
| Header/index acceptance matches | 637 |
| Filing-date matches | 637 |
| Ownership XML payloads parsed | 637 |
| Negative first-seen-minus-acceptance anomalies | 0 |

The complete-submission parser now accepts EDGAR's native `<ACCEPTANCE-DATETIME>YYYYMMDDhhmmss` header element as well as the legacy colon-delimited representation. Distinct conflicting values fail closed. Acceptance timestamps are interpreted in America/New_York and converted to UTC. The independent filing-index clock is reconciled separately.

The feed's `updated` timestamp matched the accepted timestamp to the second for all 637 accessions. This is a consistency check, not proof that the feed timestamp or acceptance time equals the first instant of public availability.

### First-seen upper-bound delay

The local first-seen timestamp is an upper bound on when the system had observed the filing, not the exact public-release time.

| Metric | Seconds | Approximate |
|---|---:|---:|
| Minimum | 190 | 3m 10s |
| Median | 14,983 | 4h 9m 43s |
| 90th percentile | 17,550 | 4h 52m 30s |
| Maximum | 23,181 | 6h 26m 21s |

All 637 observations retain the status `BOUNDED_METADATA_ONLY`, with a common prior successful poll lower bound of 2026-11-18 19:26:08 UTC and first-seen upper bounds between 2026-11-19 01:54:11 and 01:54:34 UTC.

## 2. Issuer and owner semantics

The ownership XML resolved an issuer CIK and an as-filed trading symbol for all 637 accessions.

| Filing-level characteristic | Count |
|---|---:|
| Distinct issuer CIKs | 321 |
| Distinct as-filed symbols | 321 |
| Issuers with multiple symbols in this cohort | 0 |
| Symbols linked to multiple issuer CIKs in this cohort | 0 |
| Single-reporting-owner filings | 619 |
| Multiple-reporting-owner filings | 18 |

These are cohort-level identity diagnostics, not a historical security master. The as-filed symbol does not establish the issuer's listed security class, exchange, active listing status, historical F80 membership or point-in-time universe membership. The filing-level owner count is not permission to multiply or attribute transaction rows to every named owner. Joint/group filings remain at filing grain unless the XML explicitly supports an owner-to-row link.

Role flags were present in the following counts across reporting-owner records: director 318, officer 399, ten-percent owner 79, and other 24. Role flags can overlap and are not mutually exclusive person counts.

## 3. Transaction semantics

The parser counted non-derivative Table I transaction rows. It did not persist transaction-level records.

| Transaction code / acquired-disposed | Rows |
|---|---:|
| S/D | 594 |
| F/D | 166 |
| M/A | 163 |
| P/A | 145 |
| A/A | 131 |
| G/D | 25 |
| C/A | 17 |
| G/A | 10 |
| J/D | 18 |
| J/A | 6 |
| D/D | 3 |
| I/A | 1 |
| I/D | 1 |

There were 145 Table I P/A rows: 133 in single-owner filings and 12 in multiple-owner filings. This is a transaction-row count, not a count of distinct filings, insiders, or independent economic purchases. The 12 rows in joint/multiple-owner filings are not attributed to individual owners.

The SEC defines code P as an **open-market or private purchase** of a non-derivative or derivative security. Thus P/A does not prove an exchange execution, personal discretionary buying, or an unplanned trade. It must not be relabelled “open-market insider buying” without additional evidence about security, price, footnotes, ownership form, and transaction context.

The document-level Rule 10b5-1 indication was:
- yes: 109 filings;
- no: 528 filings;
- unknown: 0 in this cohort.

This flag is preserved at filing grain. It is not expanded to owners or individual transaction rows, and a checked plan box is not by itself evidence of informed or uninformed behavior.

## 4. Integrity controls

- Source event ledger SHA-256: `e4e237a59fdd0ba73e1b0dcb1fcda115887281942dbb20a3ded53f0993be58d3`.
- Payload manifest SHA-256: `d6a4b7420618f681c2517bb1ba91a3768b47ee87a5f872c9874fa64512162704`.
- Artifact ZIP SHA-256: `1db6e8e9e48db719a91988d314b49e748d54f766ceca2804b5c2d37d6aaf1829`.
- Raw SEC payloads and transaction-level rows were not persisted.
- The artifact contains aggregate JSON only.

## 5. Eligibility decision and next gate

No observation is currently eligible for an alpha test. Public availability is not certified, historical F80 membership is not verified, and no effective-dated security-class/listing join has been completed for this cohort.

**Next gate:** reconcile the 321 issuer CIK/as-filed symbol pairs against an effective-dated security-class, listing and historical F80 membership source. Preserve ticker changes, multiple classes, ADRs, inactive securities and unresolved identities as distinct states. Separately, if transaction-level analysis is pursued, inspect Table I/II, dates, prices, ownership form, footnotes and filing amendments without double-counting joint owners or treating P as exchange-only.

The prior Phase 455 audit remains a warning: a static 335-symbol snapshot is not a historical security master. Its six exact accession matches across six sampled quarters do not establish historical membership or signal coverage.

No forward returns, event study, backtest, OOS, bootstrap, LOO or holdout test was run. No signal was admitted. F80_TOP20_PARTIAL50_BASELINE_C20, its universe, parameters, capital, exposure, costs, holdout and production remain unchanged.

## 6. Validation

Run 44474285899 completed successfully:
- `offline-regression`: success;
- `live-audit`: success;
- 637/637 header/index acceptance reconciliations;
- 637/637 ownership XML parses;
- no-promotion and no-persistence gates passed.

The workflow's live retrieval is a completed run; no duplicate was started.
