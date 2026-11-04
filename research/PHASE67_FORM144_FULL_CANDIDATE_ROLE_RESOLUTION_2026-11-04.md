# Phase 67 — Full SEC Form 144 candidate issuer-role resolution

**Date:** 2026-11-04  
**Status:** Full XML identity-resolution run; no forward returns or alpha tests authorized.

## 1. Why Phase 67 is necessary

Phase 66 run 41821586407 completed successfully and uploaded artifact 13316983646 (645,793 bytes; SHA-256 8a72ae64b786828a896a5699c3c92947725142614976ea5163aabfb677d6f04e). It passed the Phase 65 sample schema/role gate, but it did not resolve the full candidate census. The workflow reused the 1,177-document stratified sample routine. The title "full candidate issuer-role resolution" must not be read as a full-census result.

Artifact review confirms:
- 1,177 XML documents: 841 Form 144 and 336 Form 144/A.
- 897 candidate-stratum rows: 701 Form 144 (698 issuer matches, two filer-only false positives, one ambiguous-pair issuer resolved) and 196 Form 144/A issuer matches.
- 280 controls, all with both distinct XML CIKs reconciled to the master-index pair.
- Zero XML fetch errors in the sample.
- Core proposed-sale field presence, numeric parsing and date parsing were 100% in this deterministic stratified sample.
- Proposed-sale tranches, acquisition lots and realized prior sales were separately parsed.

The sample is a schema diagnostic, not a random population estimate and not a full candidate resolution.

## 2. Full candidate census

Across the 14 quarterly master indexes from 2023Q2 through 2026Q3, after the 2023-04-13 electronic filing start:
- 56,167 Form 144/144-A accessions.
- 55,558 Form 144 originals and 609 Form 144/A amendments.
- 21,451 unique-current-candidate Form 144 pairs.
- 196 unique-current-candidate Form 144/A pairs.
- One additional ambiguous Form 144 pair.
- Total candidate-pair accessions requiring XML role resolution: 21,648.
- Current map: 308/335 tickers mapped to 309 candidate CIKs; 27 current tickers remain unresolved.

These are current-CIK candidate accessions, not confirmed issuer events or historical F80 constituents.

## 3. Resolution method

For every unique-candidate and ambiguous accession:
1. Fetch the primary XML using both master-index archive CIK paths as fallback.
2. Parse XML issuerCik and submission filer CIK independently.
3. Require both CIKs to be non-empty, distinct and present in the unlabelled two-CIK master-index pair.
4. Require XML form type to match the master index.
5. Classify every candidate row explicitly:
   - issuer_match
   - filer_only_false_positive
   - ambiguous_pair_issuer_match
   - ambiguous_pair_filer_only_false_positive
   - an explicit unresolved_* status for fetch, parsing, metadata or identity failures.
6. Only XML issuer CIKs that belong to the current candidate CIK set enter issuer_event_raw.csv.
7. Preserve filer-only rows in a separate diagnostic; never infer the issuer from the filer or archive path.

The run also fetches ten deterministic zero-candidate controls per form per quarter to monitor pair/form concordance. Controls are not target events.

## 4. Event payload

For confirmed issuer rows, preserve:
- accession, form, filing date, master-index CIK pair, candidate ticker/CIK set;
- XML issuer CIK/name and filer CIK, seller name and relationships;
- proposed-sale securitiesInformation tranches, including raw and numeric units/value/outstanding, approximate sale date, security class, exchange and broker;
- securitiesToBeSold acquisition lots separately;
- securitiesSoldInPast3Months realized prior sales separately;
- notice date, 10b5-1 mention, plan adoption dates and previousAccessionNumber;
- whether the referenced previous accession is present in the 14-quarter census.

A 144/A is retained as a filing/update record. It is not counted as a new supply event by default. previousAccessionNumber is a prior reference, not necessarily the immediate predecessor; seller, issuer and security-class lineage remain a separate gate.

## 5. Predeclared gates

- XML fetch success >=99.5% among rows for which an XML fetch was attempted.
- Explicit issuer/filer role resolution >=99.9% of all candidate rows; filer-only is a resolved false positive, not an issuer event.
- Both XML CIKs reconcile to the master-index pair >=99.9% of parsed rows.
- XML CIKs are distinct >=99.9% of parsed rows.
- XML form matches index >=99.9% of parsed rows.
- Zero duplicate candidate accessions after quarterly concatenation.
- Every candidate row has an explicit classification; no silent dropping.
- Zero filer-only rows enter the issuer event file.

Any failures remain in the unresolved/error artifacts. A gate failure is not repaired by dropping difficult rows or relaxing thresholds after seeing results.

## 6. Execution and reproducibility

- Five workers share the SEC request lock, spaced at 0.20 seconds per request (maximum planned rate: five requests/second).
- One quarter is processed at a time; checkpoint CSVs are written after each quarter and every 500 completed rows are logged.
- The Actions job timeout is 180 minutes. Artifact upload runs even if the job fails, preserving checkpoints and error rows.
- The output includes the code commit, quarter census, summary and separate candidate, issuer-event, filer-only, unresolved, error and control files.
- The workflow is not dispatched again while its concurrency group is active.

## 7. Remaining PIT and universe gates

Phase 67 does not establish:
- historical F80 membership or historical ticker/CIK effective dates;
- predecessor issuers, delisted securities, mergers or the 27 unmapped current tickers;
- SEC accepted timestamps or first-publication timestamps;
- complete amendment/seller/security-class lineage;
- actual execution of proposed sales.

Until those gates pass, filing date is only a conservative public-date proxy and no same-day close is used. The first full trading-session close after filing date remains the provisional execution boundary. Approximate sale date is never KnowledgeDate or proof of execution.

## 8. Economic test remains unauthorized

No forward returns, feature selection or alpha test is run in Phase 67. After identity resolution, the next phase must reconstruct PIT F80 issuer membership, accepted-time availability and amendment lineage, then measure issuer-day coverage by period, size and liquidity.

Only after all data gates pass may Proposed Supply Pressure be tested against frozen LTM/F80 with identical exposure, execution timing and costs, chronological OOS, block bootstrap and issuer leave-one-out. Form 144 is a proposed Rule 144 sale-order notice, not proof of sale; the feed is selective and must not be interpreted as a complete insider-selling dataset.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
