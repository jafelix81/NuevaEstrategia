# Phase 657 — SEC 13D/G subject-versus-filer role × form-family cross-tab

**Audit cutoff:** 2026-11-27 05:13 UTC  
**Source:** Phase 603 bounded SEC global-index pilot, run [45493730680](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45493730680), artifact [14966963205](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45493730680/artifacts/14966963205).  
**Artifact ZIP SHA-256:** `e7f7cfdee99744258f61079c9f9f720114f07a715345a99531392b56b81918e6`  
**Sample CSV SHA-256:** `6850653ec5b8be716f475417efa9c736b7891d742a66c08c04df0524b6b6c3ce`  
**Disposition:** descriptive role/form diagnostic only; prioritize issuer-side 13D content classification for the next feasibility gate. No signal or alpha admitted.

## 1. Reproducible sample cross-tab

The 147-row sample contains four distinct SEC form types. Each row was classified using the already-parsed header roles and the current-F80 mapping fields in the immutable Phase 603 artifact:

- **Subject match:** `subject_current_f80_tickers` is non-empty.
- **Filer match:** `filer_current_f80_tickers` is non-empty.
- **Both:** both fields are non-empty.
- **Subject-only / filer-only:** exactly one of those role-specific fields is non-empty.

| Form | Sample rows | Subject match | Filer match | Both | Subject-only | Filer-only |
|---|---:|---:|---:|---:|---:|---:|
| SC 13D | 27 | 6 | 1 | 0 | 6 | 1 |
| SC 13D/A | 40 | 10 | 10 | 0 | 10 | 10 |
| SC 13G | 40 | 4 | 17 | 1 | 3 | 16 |
| SC 13G/A | 40 | 4 | 17 | 1 | 3 | 16 |
| **Total** | **147** | **24** | **45** | **2** | **22** | **43** |

The 22 subject-only rows comprise 16 Schedule 13D/13D-A rows and six Schedule 13G/13G-A rows. Conversely, 32 of the 43 filer-only rows are in the 13G family. Both-role overlaps occur only in the two 13G-family rows.

## 2. Research interpretation

This reinforces a strict **issuer-role** rule:

1. A filing is an issuer event only when the header's **SUBJECT COMPANY** maps to the security/issuer under study. A current-F80 match on **FILED BY** alone is not an issuer event.
2. The 13D family is the first content-classification candidate: 16 of the 22 subject-only sample rows are 13D/13D-A. This is a research-priority observation, not a prevalence estimate.
3. Initial SC 13D filings and SC 13D/A amendments must be treated separately. Amendments update an existing reporting-group × subject issuer × covered-class state; repeated amendments are not independent events.
4. SC 13G/13G-A is better retained initially as institutional ownership-state context and a separate comparison/negative-control family. It is not automatically a buy, sell, or informed-trading signal.

The sample is deliberately stratified by form and current-F80 index presence. These counts are **not representative population rates**, cannot be extrapolated to the full quarter, and have no inferential confidence intervals. A current CIK mapping is not historical F80 membership.

## 3. Data and PIT gates still fail

- Phase 603's current ticker-file mapping resolves 300/335 frozen tickers to 299 unique CIKs; 35 remain unmapped in that artifact.
- The Phase 604 improvement to 328/335 exists in Draft PR [#220](https://github.com/jafelix81/NuevaEstrategia/pull/220), not merged mainline, and is still a set of current snapshots rather than an effective-dated historical security master.
- The quarterly master index is a retrospective/corrected snapshot. SEC ACCEPTANCE-DATETIME is chronology metadata, not certified first-public availability.
- The 147-row sample contains headers, not the primary schedules needed to classify Item 4 purpose, Item 5 ownership, group agreements, derivatives, tender/merger context, or amendment changes.
- No historical F80 membership, security-class continuity, exact first-seen clock, returns, OOS, bootstrap, LOO, or holdout results are established.

## 4. Next research sequence

1. Complete the merged Phase 616 preregistered 44-accession, five-quarter header sample. Its workflow is manual-only with `run_live_sample=true`; the script requires a non-placeholder `SEC_USER_AGENT` containing a monitored contact email before any SEC request.
2. Reconstruct effective-dated subject CIK × covered class × security identity × historical F80 membership. Keep unmapped and delisted names as unknown, never false zero.
3. Only after the identity gate passes, classify a bounded primary-schedule sample: initial 13D purpose/ownership, 13D/A state deltas, reporting-group lineage, derivatives and transaction context; keep 13G family separate.
4. Establish a conservative ex-ante knowledge clock from prospective first-seen evidence or a documented next-session bound.
5. Only then preregister an issuer-event hypothesis and compare it incrementally with frozen LTM/F80 using identical exposure/costs, chronological OOS, block bootstrap and time-block/issuer LOO.

## 5. Controls

- `F80_TOP20_PARTIAL50_BASELINE_C20`: **frozen**.
- New signal promoted: **none**.
- Incremental alpha demonstrated: **none**.
- No price or forward-return data inspected.
- No event study, OOS, bootstrap, LOO or holdout test performed.
- No production, universe, capital, exposure, costs, parameters or holding-period rules changed.
- No paid data, vendor contact, quote request or purchase; budget remains **USD 0**.
