# Phase 66 — Form 144 full candidate issuer-role resolution and event-panel gate

**Status:** Preregistered data-resolution phase; no forward returns or alpha tests authorized.

## 1. Motivation

Phase 65 run 41814314002 parsed 1,177 XML documents across 14 quarters with zero fetch errors and complete core proposed-sale field presence/numeric/date parsing. Its workflow failed because its original gate incorrectly required every unique candidate CIK in the master-index pair to be XML issuerCik.

The larger sample found two legitimate filer-only false positives:
- JD candidate CIK 0001549802 is the filer/seller in accession 0001970673-23-000004; XML issuer is GigaCloud Technology Inc. (0001857816).
- QCOM candidate CIK 0000804328 is the filer/seller in accession 0001104659-26-005774; XML issuer is MNTN, Inc. (0001891027).

A third ambiguous pair (AMT/ASTS) was resolved by XML: ASTS is issuer and AMT is filer. Therefore, the master-index pair is unlabelled. Only primary XML issuerCik can identify a target issuer; a filer-only candidate is excluded from issuer events.

## 2. Candidate census to resolve

Across 14 quarterly master indexes from 2023Q2 through 2026Q3:
- 56,167 total Form 144/144-A accessions.
- 21,451 original Form 144 accessions with exactly one current candidate CIK in the pair.
- 196 Form 144/A accessions with exactly one current candidate CIK in the pair.
- One additional original Form 144 accession with two candidate CIKs.
- 308 of 335 current tickers map to 309 candidate CIKs; 27 tickers remain unresolved.

The 21,647 unique-candidate accessions plus one ambiguous accession are candidate-pair rows, not confirmed issuer events. The current mapping is not historical F80 membership.

## 3. Resolution protocol

For every unique-candidate and ambiguous accession:
1. Fetch the primary Form 144 XML by trying both master-index archive CIK paths.
2. Parse XML issuerCik and submission filer CIK as separate roles.
3. Require distinct non-empty issuer/filer CIKs and reconcile both to the two-CIK master-index pair.
4. Verify XML form type against master-index form type and accession identity.
5. Classify unique candidate as `issuer_match`, `filer_only_false_positive`, or `unresolved`.
6. For ambiguous pairs, include only when XML issuerCik is in the candidate set; preserve filer role separately.
7. Preserve raw accession, filing date, issuer CIK/name, seller name, relationships, proposed-sale tranches, acquisition lots, prior realized sales, remarks/10b5-1 and previousAccessionNumber.
8. Never infer a target issuer from the master-index pair alone.

Only rows whose XML issuerCik belongs to the candidate CIK set may enter the issuer event panel. Filer-only rows are retained in a separate diagnostic table and excluded from target events.

## 4. Proposed-sale schema

- `securitiesInformation`: proposed-sale tranches; extract units, aggregate market value, outstanding units, approximate sale date, security class, exchange and broker/market maker.
- `securitiesToBeSold`: acquisition-lot history; never use as proposed-sale quantity.
- `securitiesSoldInPast3Months`: realized prior sales; never merge into proposed-sale quantity.

Amendments remain separate filings and must not be counted as new supply events by default. Follow exact previousAccessionNumber links; a reference outside the 14-quarter window is left-censored. Do not assume a previous reference is the immediate predecessor without seller/security-class lineage checks.

## 5. Predeclared gates

- XML fetch success at least 99.5%; every failed accession retained with an explicit error and retry status.
- At least 99.9% of parsed candidate XMLs have distinct issuer/filer CIKs and both roles reconcile to the master-index pair.
- XML form type agrees with the index in at least 99.9% of parsed rows.
- Every candidate row is explicitly classified as issuer match, filer-only false positive, or unresolved; no silent dropping.
- All proposed-sale numeric fields retain raw strings and parsed numeric values; parse failures are separately reported.
- Zero filer-only candidate rows enter the issuer event panel.
- Exact accession uniqueness after quarterly concatenation; no duplicate accession rows.
- No alpha gate in this phase.

A failure is not repaired by silently relaxing thresholds. Report the affected accessions and classify them as unresolved.

## 6. Point-in-time and universe constraints

This is a current-CIK candidate census, not historical F80 membership. Historical ticker/CIK continuity, predecessor issuers, delistings, mergers and the 27 unmapped tickers remain separate gates. The first full trading-session close after SEC filing date is the conservative KnowledgeDate/execution boundary; accepted timestamps are not yet collected. Approximate sale date is never KnowledgeDate and does not prove execution.

Before any return test, build the PIT F80 issuer membership panel, confirm issuer CIK effective dates, resolve amendments and seller/security lineage, and measure coverage by issuer-day, quarter, size and liquidity.

## 7. Economic hypothesis remains untested

The later hypothesis is Proposed Supply Pressure: proposed sale value/units relative to trailing dollar ADV, shares outstanding and liquidity. Form 144 is a proposed Rule 144 sale-order notice, not proof of execution; 144/A is an amendment/update, not a new event by default. The hypothesis must be tested incrementally versus frozen LTM/F80 with identical exposure/costs, chronological OOS, block bootstrap and issuer LOO. No horizon is fixed in advance beyond preregistered candidate horizons; no positive result is assumed.

**F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.**
