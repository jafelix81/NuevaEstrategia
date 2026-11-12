# Phase 347 — SEC 13D/G CUSIP integrity and subject-consistency audit

**Date:** 2026-11-12 UTC  
**Status:** `COMPLETE_CUSIP_FIELD_AUDIT`  
**Disposition:** CUSIP is a promising direct filing-level security key in this pilot, but no historical security master, strict-PIT source admission, or event study is authorized.

## 1. Immutable input and reproducibility

- Phase 93 run: [41940675337](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41940675337).
- Phase 93 artifact: [13375652511](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41940675337/artifacts/13375652511).
- Downloaded ZIP SHA-256: `e9252a741d111319f7d93796658ebe4e1c439903444e905d557e8de0a023497a`, matching GitHub's artifact digest.
- Phase 93 contained 200 structured filings and reported 200/200 reparsed, zero raw SHA-256/XML identity errors.
- Phase 347 is offline only. No SEC request, vendor contact, or data purchase was made.

## 2. CUSIP field integrity

| Measure | Result |
|---|---:|
| Structured filings | 200 |
| Subject CIKs | 174 |
| CUSIP present | 200/200 |
| Exactly one CUSIP per filing | 200/200 |
| Check digit passes, including zero sentinel | 199/200 |
| Valid nonzero CUSIP rows | 197/200 (98.5%) |
| All-zero sentinel rows | 2 |
| Nonzero checksum-invalid rows | 1 |
| Unique nonzero CUSIPs, raw | 180 |
| Unique checksum-valid nonzero CUSIPs | 179 |

The two `000000000` values are treated as sentinels, not securities. One additional nonzero CUSIP fails the standard check digit: accession `0001493152-25-008094`, value `80512Q302`. It remains quarantined rather than corrected.

The valid-row split is 77/79 for 13D and 120/121 for 13G; 101/103 for initial filings and 96/97 for amendments.

## 3. Subject-issuer consistency and multiplicity

- All 179 unique checksum-valid nonzero CUSIPs map to exactly one subject CIK within this 200-filing sample.
- No valid nonzero CUSIP is observed under multiple subject CIKs.
- The all-zero sentinel appears under two different subject CIKs, confirming why it must not be treated as an identifier.
- Sixteen nonzero CUSIPs recur across filings, accounting for 18 additional filing instances; repeated observations are retained, not deduplicated as separate events.
- Four subject CIKs have more than one valid nonzero CUSIP; one has six. An issuer-to-single-security shortcut would therefore be wrong.

This is encouraging evidence that the cover-page CUSIP can preserve security-level identity better than a filer/accession-prefix CIK or a current ticker. It is still a purposive 200-filing pilot, not a population coverage estimate.

## 4. Event-mechanism limits remain

The Phase 93 keyword taxonomy found 7 activist/control-action tags, 33 generic governance references, 126 unclassified filings, and one explicit open-market-acquisition phrase. That one phrase co-occurs with conversion/exercise, corporate-reorganization, derivative/swap and generic-governance tags. It is not a clean verified open-market purchase. Tags are triage, not investor intent or a Smart Money label.

Amendment lineage is still incomplete: 97 amendments, 46 explicit previous-accession references (44 outside the 600-header sample and two with no structured XML in-sample), and 51 missing explicit references. Only two sample-limited candidate parent edges were generated and both remain unconfirmed; 49 amendments had no candidate parent in the structured sample.

## 5. Decision and next gate

**Advance CUSIP as a candidate identity key, not as an admitted security master.**

Next work should:
1. Retrieve and validate the 44 explicit predecessor accessions outside the sample, preserving subject CIK, form family, acceptance time, reporting-person identities and CUSIP as separate checks.
2. Keep the two zero CUSIPs and the checksum-invalid CUSIP quarantined.
3. Build an effective-dated CUSIP-to-security crosswalk that preserves multiple classes, ADRs, CUSIP changes, corporate actions and delistings.
4. Measure historical active-universe and price coverage, including inactive securities, before any forward-return calculation.
5. Only then preregister separate 13D activist/control and 13G passive/aggregate hypotheses with SEC acceptance UTC as knowledge time and conservative next-session execution.

No ticker, exchange, share-class continuity, delisting status or historical F80 membership is inferred from this CUSIP audit.

## 6. Controls

Seven offline regression tests passed locally. This phase has no dedicated hosted Actions run; the exact input artifact digest and deterministic script are pinned above and in the result JSON.

No forward returns, alpha, bootstrap, LOO, chronological OOS or holdout test was run. No source is strict-PIT admitted. `F80_TOP20_PARTIAL50_BASELINE_C20`, production, universe, capital and parameters remain unchanged. No vendor was contacted and no paid data was purchased.


## Hosted reproducibility corrections — 2026-11-12

- Run [43316355554](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43316355554) passed the seven Phase 347 unit tests and verified both immutable input artifact hashes, but the replay stopped when the generated JSON summary contained a literal backslash-n suffix. The writer now emits a real newline, and a regression test verifies that its output is parseable JSON.
- Run [43325269888](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43325269888) passed all eight Phase 347 tests and generated valid JSON. The reproducibility comparison then exposed a stale committed summary: it omitted the detailed `subject_ciks_with_multiple_cusips` mapping emitted by the script. The committed summary has been synchronized to the deterministic replay; this was an audit-artifact mismatch, not a source-data discrepancy.
- The same correction pass tightened two identity safeguards: filings with zero or multiple CUSIPs no longer receive an arbitrary first-CUSIP assignment, and Phase 348's `all_subject_ciks_match` now compares the parent subject CIK directly with the child subject CIK (rather than merely checking that the parent CIK is nonempty). A negative regression fixture covers the latter.
- Final hosted replay: [run 43326498877](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43326498877) passed all 22 regression tests across Phases 347–349. The artifact includes the Phase 349 row-level manifest and was independently inspected.
