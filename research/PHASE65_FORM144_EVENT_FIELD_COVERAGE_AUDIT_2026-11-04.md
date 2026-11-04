# Phase 65 — SEC Form 144 event-field coverage and amendment-lineage audit

**Date:** 2026-11-04  
**Status:** New data-feasibility sample registered; hosted execution pending. No forward returns are calculated.

## 1. Why this phase follows Phase 64

Phase 64 validated the current-CIK master-index pair + primary XML issuerCik identity mechanism across six separated quarters. It did not establish whether the actual economic fields required for a proposed-supply event panel are sufficiently complete, parseable, or linkable.

Phase 65 therefore audits the event payload before any full panel build or return test.

## 2. Coverage window and discovery

- Electronic Form 144/144-A reporting window starts 2023-04-13.
- Audit all 14 quarters from 2023Q2 through 2026Q3.
- Parse each quarterly SEC master index and retain Form 144/144-A accessions filed on or after 2023-04-13.
- Use the two-CIK pair and the current 335-ticker candidate CIK map only to stratify candidate discovery.
- Sample separately by quarter and form: up to 50 unique-candidate pairs, 20 ambiguous pairs and 10 zero-candidate controls.
- Use deterministic SHA-256 accession ordering. This is a schema diagnostic, not a probability sample of the population.

## 3. Fields audited

For each sampled primary XML, preserve and measure:

- XML issuer CIK, filer CIK, issuer name, seller name and relationship to issuer;
- security class, units proposed for sale, aggregate market value and approximate sale date;
- notice date, remarks, 10b5-1 mention and plan-adoption dates;
- previousAccessionNumber and whether its normalized accession falls inside the 14-quarter census;
- number of proposed-sale securitiesInformation blocks, acquisition-history securitiesToBeSold blocks, and realized-prior-sale securitiesSoldInPast3Months blocks.

The SEC XML schema has three economically distinct repeated groups: securitiesInformation (proposed sale tranches, 1–40); securitiesToBeSold (how/when the securities were acquired, 1–40); and securitiesSoldInPast3Months (realized sales in the prior three months, 0–200). The audit extracts each group separately and never treats acquisition lots or prior realized sales as the proposed sale. Numeric/date parsing is measured separately from raw field presence. See the SEC Form 144 XML technical specifications: https://www.sec.gov/submit-filings/technical-specifications.

## 4. Identity and lineage rules

- A unique current candidate CIK in the master-index pair remains only a candidate until primary XML issuerCik confirms it.
- For ambiguous pairs, require the XML issuer CIK to be one of the candidate CIKs; otherwise retain unresolved.
- For zero-candidate controls, verify that distinct XML issuer and filer CIKs are both present in the master-index pair.
- Normalize previousAccessionNumber to the canonical 10-2-6 accession format.
- An in-window previousAccessionNumber match establishes only that the referenced accession exists in the observed window. It does not establish that the referenced filing is the immediately preceding amendment or that seller/security-class lineage matches.
- References outside the window are left-censored, not invalid.

## 5. Sample schema gate

The workflow will report per-form field-presence, numeric/date parse rates, candidate identity concordance, amendment reference validity and multi-tranche counts.

Provisional sample gate:
- At least 100 candidate Form 144 XML rows and 20 candidate Form 144/A XML rows;
- zero XML fetch errors;
- every sampled unique/ambiguous candidate identity confirmed by XML;
- all sampled XML form types agree with the master index;
- core field presence at least 95% for Form 144 and 90% for Form 144/A.

A PASS applies only to the sampled schema/identity checks. It does not imply universe coverage, unbiased field completeness, historical CIK correctness or economic usefulness.

## 6. Point-in-time and universe limits

This phase deliberately does not collect accepted timestamps. Filing date is the only timestamp used for the audit. Any later event panel must map filing date to the first full trading-session close after filing, with no same-date use; a verified accepted timestamp may support a separately preregistered sensitivity.

Current CIK/ticker mappings are not historical active-universe membership. The 27 unresolved current tickers, historical predecessor issuers, delistings, ticker changes, mergers and actual F80 membership remain open. The Phase 65 result cannot authorize a forward-return test until those PIT identity and coverage gates pass.

## 7. Economic interpretation

Form 144 is a proposed Rule 144 sale-order notice, not proof of an executed sale. 144/A is an amendment/update and is not a new supply event by default. Proposed quantities and market values must be reconciled across tranches and amendments before aggregation. Do not infer coordinated seller groups without evidence.

No forward returns, alpha tests, strategy changes, vendor purchases or production changes are part of Phase 65.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
