# Phase 665 — Exact Form 144 accession-level PIT / plan-date join

**Audit cutoff:** 2026-11-27 15:22 UTC  
**Source snapshot:** `main` at `f875be29d740f7ac8dc861d8dae607e13eb34b44`  
**Capture source:** [Phase 403 run 46015828465](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46015828465)  
**Artifacts:** [poll audit 15206147627](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46015828465/artifacts/15206147627) · [post-capture 10b5 audit 15205892828](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46015828465/artifacts/15205892828)  
**Disposition:** resolve the previously unknown accession-level intersection; retain all existing signal and PIT exclusions.

## 1. Source snapshot and grain

The latest inspected Form 144 scheduled capture completed successfully. It reported no new accessions or economic events, appended 53 feed-observation rows, and enriched 10 previously known accessions with 56 structured detail rows. The structured detail backfill queue contained 148 accessions.

The committed source ledgers at the audit snapshot were:

| Ledger | Rows | Unique accessions | Git blob |
|---|---:|---:|---|
| `events.csv` | 1,003 | 1,003 | `6083364c45bc88ce369d11cf0806c276563bef1f` |
| `sale_details.csv` | 5,651 | 855 | `27eb199b2107d1322ae1817d27aa6cb8089eaa5f` |

The 148 accessions present in the feed-event ledger but absent from the structured detail ledger remain unclassified for formal plan-date status. They are not included in the plan-date denominator or the PIT intersection.

## 2. Accession-level join and integrity

Grouped all 5,651 detail rows by exact accession, then joined the 855 unique detail accessions to the feed-event ledger.

- All **855/855** structured-detail accessions were present in `events.csv`.
- **148** feed-event accessions had no structured detail yet.
- There were **zero** detail accessions missing from the event ledger.
- Six PIT fields matched exactly across the two ledgers for all 855 joined accessions: research-observation eligibility, public-availability certification, signal eligibility, interval status, lower bound and upper bound.
- Fourteen filing-grain fields were internally consistent across all detail rows for each accession, including the formal plan-date JSON, form, issuer/seller identity, notice date, remarks and PIT fields.
- No accession-level plan-date JSON conflicts or PIT-field mismatches were found.

The join is exact at accession grain; repeated securities/detail rows were not treated as independent filings.

## 3. Resolved result

The structured detail ledger contains **322** accessions with at least one parsed formal plan-adoption date across **134 distinct dates**:

| Filing form | Plan-date accessions |
|---|---:|
| Form 144 | 320 |
| Form 144/A | 2 |
| **Total** | **322** |

The exact accession-level PIT intersection is:

| PIT classification | With formal plan date | Without formal plan date | Total |
|---|---:|---:|---:|
| Bounded research-observation eligible | **290** | 517 | 807 |
| Initial baseline, no lower bound | **32** | 16 | 48 |
| **Total structured details** | **322** | 533 | **855** |

Therefore:

- **290/322 = 90.06%** of structured filings with a formal plan date have a bounded first-seen interval.
- **32/322 = 9.94%** are in the initial baseline with no lower bound.
- **290/807 = 35.94%** of research-observation-eligible structured accessions have a formal plan date.
- The corrected all-structured-ledger rate remains **322/855 = 37.66%**.

This resolves Phase 664's `NOT_COMPUTED_NO_ACCESSION_LEVEL_PIT_JOIN` status. It does **not** justify calculating 322/807: the correct numerator for that denominator is the joined intersection, 290.

## 4. Interpretation and hard limits

This is a data-coverage and measurement result, not an alpha result.

- The 148 event-only accessions have unknown plan-date status until structured-detail backfill is complete; results above apply only to the 855 accession detail cohort.
- A bounded first-seen interval is a conservative poll-receipt bound, not the exact instant of public dissemination.
- **Zero** accessions are public-availability-certified and **zero** are signal-eligible in this snapshot.
- A formal plan-adoption date is filing content. It does not establish that a sale was executed, that the plan remained active, or that the transaction was discretionary.
- Form 144 is a proposed-sale notice, not execution confirmation.
- No prices or forward returns were inspected. No event study, alpha test, chronological OOS, bootstrap, LOO or holdout test was run.

## 5. Reproducibility

The new standard-library audit script is `research/phase665_form144_accession_pit_plan_date_join.py`. It:

1. reads the committed `events.csv` and `sale_details.csv`;
2. validates filing-grain consistency before counting;
3. joins on exact accession only;
4. fails closed on missing detail-to-event links or PIT mismatches;
5. writes source SHA-256 values and the complete count/rate summary.

Fixture regressions cover repeated detail rows, event-only accessions, conflicting plan-date fields, cross-ledger PIT mismatches, malformed JSON and invalid boolean values. The PR workflow runs offline only and reproduces the actual committed-ledger totals; it performs no SEC requests.

### CI validation

[PR validation run 46025579803](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46025579803) completed successfully:

- **93 tests passed** across the existing Phase 403 offline regression suite and Phase 665 fixtures.
- The actual committed-ledger join reproduced all expected accession counts and zero PIT mismatches.
- Artifact [15212117265](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46025579803/artifacts/15212117265) contains the machine-generated summary.
- The live-capture job was skipped for the pull-request event; no SEC requests were made.

## 6. Supplemental audit: the 148 event-only backlog accessions

A separate exact join of `events.csv` to `feed_observations.csv`, excluding the 855 accessions already present in `sale_details.csv`, shows that the pending detail backlog is not currently a usable candidate-issuer PIT cohort.

| Backlog classification | Accessions |
|---|---:|
| Total event-only accessions | 148 |
| Form 144 | 138 |
| Form 144/A | 10 |
| Initial baseline, no lower bound | 94 |
| Possible feed-window gap | 50 |
| Bounded research-observation eligible | 4 |
| Static candidate-manifest issuer matches | 26 |
| Signal eligible | 0 |
| Public-availability certified | 0 |

The 26 candidate-manifest matches span 16 issuer names, but **none** is research-observation eligible and none has historical F80 membership verified. Their PIT states are:

- 12 initial-baseline records: 7 have two feed observations and 5 have six. Later repeated observations do not create a missing pre-first-seen lower bound.
- 14 possible-feed-gap records: 13 have one feed observation and one has two. The recorded gap remains unresolved; the repeated observation does not certify a complete prior feed window.
- The four bounded records are all non-candidate-manifest matches.

The pending 148 accessions account for 502 rows in `feed_observations.csv`. The full feed-observation ledger contains 2,381 rows across 1,003 accessions; its Git blob is `7580b566bafdd6b293c5901bc9f8ade30c09ecb2`.

**Interpretation:** structured-detail backfill alone will not repair PIT eligibility for the 26 static candidate-manifest matches. The binding issue is missing historical lower-bound/complete-feed evidence, not only missing parsed sale details. The candidate-manifest flag is a static CIK crosswalk, not proof of historical F80 membership.

## 7. Research decision

- Keep formal plan dates descriptive; do not treat them as trade signals.
- Keep the 148 event-only accessions outside the plan-date denominator until detail backfill.
- Preserve the distinction between bounded research observations, public-availability certification and signal eligibility.
- Next data task: complete the pending 148-accession structured-detail backfill, then repeat the exact accession join.
- Any later return test still requires an independently defensible public-availability clock, historical issuer/security identity and a preregistered incremental comparison against frozen F80/LTM.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No signal was admitted, no vendor was contacted and no data was purchased; budget USD 0.
