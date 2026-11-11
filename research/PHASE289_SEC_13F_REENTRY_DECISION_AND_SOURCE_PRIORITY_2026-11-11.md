# Phase 289 — SEC Form 13F re-entry decision and source-priority correction

**Date:** 2026-11-11 UTC  
**Status:** completed research-priority adjudication; documentation only. No raw source data acquired and no signal tested.  
**Branch:** `phase289-sec13f-reentry-adjudication` (based on the Phase 288 research branch; no PR opened).

## Executive decision

**Keep Form 13F parked for broad-universe stock selection. Defer a raw 13F holdings ZIP acquisition until the historical security-identity gate is materially improved.** Phase 288 correctly identified a free and extensive source and proposed a sample-acquisition stage, but the repository already contains direct evidence that its historical mapping coverage is too low for an identical-exposure comparison against the frozen 335-name universe.

This is a correction of research priority, not a claim that 13F contains no information. A slow, delayed ownership-change hypothesis may still be worth testing on a separately defined and frozen population if identity coverage, PIT event state, and comparability can first be demonstrated. Do not silently reduce the universe to mapped names and describe the result as a test of F80.

## 1. Reconcile the existing coverage evidence

Phase 22C V6 reports 335 names in the frozen universe, of which 301 had a current candidate mapping. Its historical table uses those 301 currently mapped names as the denominator:

| Quarter | Historical matches | Of 301 current candidates | Of full 335-name universe |
|---|---:|---:|---:|
| 2016Q1 | 212 | 70.43% | 63.28% |
| 2020Q1 | 246 | 81.73% | 73.43% |
| 2024Q1 | 280 | 93.02% | 83.58% |

The 34 names without a current candidate mapping are not historical successes. Using the full frozen-universe denominator makes the coverage limitation clearer. The direct report-date CUSIP/common-equity route had a 54.8% minimum in 2016Q1.

The 83.18% figure in Phase 166 is **not** Form 13F holdings coverage. It is a Section 13(f)-eligibility-list match for 553 unique CUSIPs in a separate 13D/G filing sample. It must not be used to support a 13F holdings-panel admission claim.

Sources within this repository:
- `research/PHASE22C_13F_MAPPING_V6_DECISION_2026-10-26.md`
- `research/PHASE205_SEC13F_ACCEPTANCE_CLOCK_AND_AMENDMENT_EVENT_AUDIT_2026-11-08.md`
- `research/PHASE166_SEC13F_CROSS_FORMAT_PIT_METADATA_BRIDGE_2026-11-06.md`

## 2. PIT and economic interpretation

The Phase 205 sample contains ten purposively selected accessions, not a representative prevalence sample:
- Four original 13F-HR filings were accepted 44–48 calendar days after quarter-end.
- Six amendments were accepted 60–1,137 days after quarter-end; median 361.5 days.
- Five of ten sample filing dates differ from the calendar date of EDGAR acceptance, and all five were accepted after 4:00 p.m. ET.

These observations demonstrate why report quarter, filing date, acceptance timestamp, and first executable session must remain separate. They do **not** estimate the population frequency of late amendments or filing-date/acceptance-date differences.

A 13F position is a delayed report of a quarter-end holding, not a transaction. It is long-biased/incomplete, excludes reported short positions, may omit confidential holdings, and has amendment semantics that can either replace an earlier state (restatement) or supplement it (add-new-holdings). A later confidentiality release is new public information on its own date, not evidence of a trade on the amendment date.

Any eventual hypothesis must use share quantities and manager/security identity, not just reported dollar-value changes. It must distinguish manager entry/exit from share changes and from mechanical price appreciation; resolve shared discretion/other-manager duplication; adjust for corporate actions; and apply each amendment only from its own public availability.

## 3. Source-priority decision

| Priority | Source | Current role | Gate before any return test |
|---:|---|---|---|
| 1 | SEC Form 4 bulk + daily EDGAR index route | Most direct historical insider-transaction candidate in the current workstream | Real six-quarter index/bulk sample, owner attribution, effective-dated security identity, PAC/delayed-sighting reconciliation |
| 2 | SEC N-PORT direct short-equity rows | Distinct registered-fund short-side hypothesis; not short interest or hedge-fund positioning | Hash and parse the purposive raw accession sample, series/amendment lineage, first-public clock, security identity and historical universe coverage |
| 3 | SEC Form 13F | Parked slow ownership-change hypothesis | Rebuild effective-dated historical CUSIP/class/ticker identity and show broad-universe coverage adequate for a predeclared identical-exposure design |
| 4 | Options and securities-lending vendors | Conditional complementary sources | Written sample/license scope, actual historical bytes, receipt/vintage evidence, security/contract identity and cost feasibility |

Form 13F's public/free status is attractive, but it does not cure the identity or coverage defects. N-PORT is not promoted: its prior research has discovered direct short-equity rows and preregistered a distinct share-quantity-change hypothesis, but the raw five-accession hashes, deterministic full parse, series/amendment lineage, effective-dated listing identity and broad-universe coverage remain unverified.

## 4. Admission and falsification rules

Do not start a 13F alpha test on the currently mapped subset. A future re-entry requires:
1. An effective-dated security master that covers active, inactive and delisted securities, share classes, ticker/CUSIP transitions, mergers and spin-offs.
2. A predeclared coverage threshold assessed against the full historical 335-name universe, not only the names that happen to map today.
3. Accession-level acceptance/public-availability and append-only amendment state reconstruction.
4. Manager graph/deduplication for shared investment discretion and other-manager relationships.
5. A frozen feature definition using reported share quantities and explicit return-chasing controls.
6. Only then, a new chronological test against frozen LTM/F80 with identical exposure, realistic costs, date/issuer/manager-clustered bootstrap, LOO, multiplicity control and a new untouched prospective holdout.

If these gates cannot be met, archive 13F as a delayed contextual source rather than repeatedly expanding metadata-only audits.

## 5. Current blockers and controls

- The current repository state records `SEC_CONTACT_EMAIL` as not configured for automated SEC retrieval. No secret was inspected or changed in this run. Do not invent a contact identity or issue SEC programmatic requests without an authorized User-Agent.
- No SEC 13F ZIP, Form 4 bulk ZIP, N-PORT raw filing or new market-data sample was downloaded in this phase.
- No alpha/forward-return test, bootstrap, LOO, OOS test or holdout use occurred.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Production, universe, capital, parameters and the consumed legacy holdout remain unchanged.
- No vendor was contacted, no trial or license was accepted, and no purchase was made.

## Decision

**Phase 13F broad-universe re-entry is deferred.** The next productive data step remains the smallest authorized real-data Form 4 sample under the Phase 281/283/284 daily-index contract. N-PORT is the next distinct public short-side sample candidate after that, subject to the same SEC retrieval and identity constraints. Do not add another synthetic 13F parser phase until real bytes expose a concrete schema or event-state defect.
