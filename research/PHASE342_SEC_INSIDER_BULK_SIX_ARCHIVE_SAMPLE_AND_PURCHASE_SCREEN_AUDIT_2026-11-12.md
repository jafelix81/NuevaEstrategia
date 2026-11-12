# Phase 342 — SEC Insider Transactions six-archive sample and high-precision Form 4 screen audit

**Date:** 2026-11-12 UTC  
**Status:** PASS — six official SEC quarterly ZIP archives downloaded, hash-pinned, schema-audited and reconciled.  
**GitHub Actions:** [run 43265704634](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43265704634) — success; 6/6 offline regression tests passed.  
**Artifact:** [13965917386](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43265704634/artifacts/13965917386)  
**Artifact ZIP SHA-256:** `16614b404f007b78f47951ef84604660ea6612f0c86f1b2ba5a6fa7b7d52d80c`  
**Disposition:** historical bulk source and high-precision candidate screen reproduced; no security identity, strict PIT, price panel or alpha admission.

## 1. Executive finding

The SEC Insider Transactions Data Sets provide a long public history (January 2006–September 2026), published quarterly and as filed. Six archives were downloaded from the official SEC page: 2006Q1, 2012Q1, 2023Q1, 2023Q2, 2025Q3 and 2026Q3.

All six ZIPs passed integrity checks. All eight documented tables were present in every archive. Required schema fields were present, all child-table accession joins were complete, and no referenced footnote IDs were missing in the screened purchase rows.

The Phase 271 high-precision screen produced **413 candidate transaction rows**, across **262 accessions**, **109 unique issuer CIKs**, and **224 issuer-CIK × filing-date event units**. This is a deterministic six-quarter source sample, not a continuous panel or probability sample. The counts are candidate yields, not prevalence estimates and not confirmed discretionary purchases.

The 2012Q1 and 2026Q3 archive bytes exactly match the immutable Phase 39 source artifact. The Phase 271 candidate counts reproduce exactly for both periods. This closes the bulk-archive reproducibility question for those two endpoints.

## 2. Immutable source coverage

| Period | ZIP bytes | ZIP SHA-256 | Last-Modified (SEC) | Submission rows | Non-derivative transaction rows |
|---|---:|---|---|---:|---:|
| 2006Q1 | 17,306,804 | `62becdadbe5eaff68f03edefe2ba2357c8bb498a1f825b697003e087cf98e6ce` | 2022-09-02 | 83,657 | 171,549 |
| 2012Q1 | 14,219,288 | `0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357` | 2022-09-02 | 71,282 | 106,815 |
| 2023Q1 | 13,882,049 | `0b476188f52a0862e71886eb31a81f6345fc6616403b52188484aef0438cfcfb` | 2025-07-23 | 69,457 | 106,093 |
| 2023Q2 | 10,742,628 | `7e636787231ae0f00accf5c3627298402dedd1aefffd7c50fb48292e5d3a8fbb` | 2025-07-22 | 55,207 | 68,588 |
| 2025Q3 | 7,956,025 | `9c57f272b7230500771f661bc1fe181527ed6b76a6f45d23a910c7fc7e9fcfa4` | 2025-11-18 | 35,457 | 55,125 |
| 2026Q3 | 8,660,776 | `a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3` | 2026-10-07 | 38,152 | 59,885 |
| **Total** | **72,767,570** | | | **353,212** | **568,055** |

The 2012Q1 and 2026Q3 SHA-256 values match Phase 39's pinned inner ZIP hashes exactly. Their candidate screen counts also reproduce Phase 271 exactly:

- 2012Q1: 102 rows / 47 accessions / 16 issuers.
- 2026Q3: 85 rows / 59 accessions / 31 issuers.

The other four periods are new source vintages in this audit. Raw ZIPs, response headers, the Phase 39 reference artifact, JSON results and CSV summary are retained in the 90-day artifact; no raw data were committed to the repository.

## 3. Table/schema and relational integrity

The SEC Readme documents eight tab-delimited UTF-8 tables. All 8/8 were present in each of the six archives; no required fields were missing.

- Total reporting-owner rows: 377,553.
- Total footnote rows: 766,389.
- Orphan rows across child tables: **0**.
- Missing referenced footnote IDs in screened base rows: **0**.
- Duplicate SUBMISSION accession keys: **0**.
- Duplicate keys in REPORTINGOWNER, NONDERIV_TRANS, NONDERIV_HOLDING, DERIV_TRANS, DERIV_HOLDING and FOOTNOTES: **0**.

### OWNER_SIGNATURE exception

The documented compound key (ACCESSION_NUMBER, OWNERSIGNATURENAME) is not unique in these as-filed archives:

| Period | Duplicate key groups | Conflicting duplicate groups |
|---|---:|---:|
| 2006Q1 | 168 | 30 |
| 2012Q1 | 87 | 0 |
| 2023Q1 | 48 | 1 |
| 2023Q2 | 42 | 0 |
| 2025Q3 | 64 | 0 |
| 2026Q3 | 8 | 0 |
| **Total** | **417** | **31** |

The 30 conflicting 2006 groups include repeated power-of-attorney signature names with two different signature dates. The one 2023Q1 conflict also has one signature name with two dates. The remaining duplicate groups are exact repeated rows.

**Treatment:** OWNER_SIGNATURE is quarantined as a unique-key/owner-attribution source. It is not used by the purchase screen. The repeated signature rows do not contaminate the transaction-table keys or the accession joins, but the SEC Readme's key definition should not be assumed to hold for this table in every vintage.

## 4. High-precision purchase screen

The screen is deliberately narrow and low-recall. A candidate row must satisfy all of the following:

1. Original Form 4, Table I non-derivative transaction.
2. Transaction form type 4, code P, acquired/disposed code A.
3. A referenced footnote explicitly says “open market”.
4. No referenced footnote says private, plan/10b5-1/ESPP, or mechanical/compensation/vesting/exercise/tax/gift/automatic.
5. Direct ownership.
6. Exactly one reporting owner on the accession.
7. Security title explicitly says common stock or common shares.
8. For filings on or after 2023-04-01, AFF10B5ONE must be explicitly false. Blank/unknown is not treated as false.

The checkbox gate is applied using each submission's actual FILING_DATE, not the quarter label. This corrects the year-level shortcut that would incorrectly apply the post-April rule to all of 2023Q1.

| Period | Base code-P acquired rows | Candidate rows | Candidate accessions | Issuers | Issuer × filing-date events | Candidate rows / base |
|---|---:|---:|---:|---:|---:|---:|
| 2006Q1 | 12,786 | 10 | 8 | 7 | 8 | 0.078% |
| 2012Q1 | 6,702 | 102 | 47 | 16 | 43 | 1.522% |
| 2023Q1 | 5,989 | 59 | 41 | 19 | 32 | 0.985% |
| 2023Q2 | 7,980 | 92 | 63 | 27 | 57 | 1.153% |
| 2025Q3 | 4,480 | 65 | 44 | 25 | 36 | 1.451% |
| 2026Q3 | 5,007 | 85 | 59 | 31 | 48 | 1.698% |
| **Total** | **42,944** | **413** | **262** | **109 unique issuers** | **224** | **0.962%** |

The event unit is issuer CIK × date-only filing date; multiple accessions on the same issuer/date are not counted as independent events. The six quarters are widely spaced and not a continuous panel. The 109-issuer union and candidate rates are descriptive of these selected quarters only.

### AFF10B5ONE schema and effective-date boundary

| Period | Field present? | Candidate-row AFF status | Gate treatment |
|---|---|---|---|
| 2006Q1 | No | 10 unknown | Pre-checkbox; no false inference |
| 2012Q1 | No | 102 unknown | Pre-checkbox; no false inference |
| 2023Q1 | Yes | 7 false / 52 unknown | All filings precede 2023-04-01; no gate applied |
| 2023Q2 | Yes | 92 false | Gate applied; all 92 pass |
| 2025Q3 | Yes | 65 false | Gate applied; all 65 pass |
| 2026Q3 | Yes | 85 false | Gate applied; all 85 pass |

The SEC notes that the 2023–2025 datasets were updated in July 2025 to add AFF10B5ONE to SUBMISSION, and future datasets would be processed similarly. Field presence in 2023Q1 does not make the checkbox an effective plan-status disclosure for pre-April filings. The 7 false and 52 unknown 2023Q1 candidate rows are therefore not filtered by this field.

Even when AFF10B5ONE is false, it does not prove that no other trading plan or arrangement exists. The screen is not a legal or economic determination of discretionary intent.

## 5. Important limitation: no identity overlap with Phase 341's broad sample

The 2026Q3 candidate cohort contains 59 accessions and 31 issuer CIKs. The 2026Q3 portion of the Phase 341 broad 72-accession identity sample contains 12 accessions. **There are zero accession overlaps and zero issuer-CIK overlaps** between those two samples.

Therefore Phase 341's 41.67% broad-sample crosswalk rate cannot be applied to this high-precision candidate cohort. The candidate cohort needs its own issuer-symbol-class-exchange crosswalk. This is the next gate, not an extrapolation from the broad sample.

## 6. PIT and interpretation limits

- The bulk SUBMISSION table provides a date-only FILING_DATE. It does not contain the exact first-public receipt timestamp for each filing.
- SEC acceptance time is not substituted for first-public receipt. The conservative event-use rule remains the first full XNYS session strictly after the official filed date.
- Code P means “open market or private purchase”; code P alone does not prove an exchange execution.
- A footnote that says “open market” is a candidate text signal, not proof of discretionary intent or a completed market trade.
- The screen is not a transaction-price validation, security-class mapping, historical listing map or survivorship-aware universe panel.
- Form 4/A remains a separate as-filed vintage; it must not be silently overwritten or treated as a new trade.

The SEC explicitly says the data are as filed, may contain filer/extraction inconsistencies, are updated quarterly, and are not a substitute for reviewing the full filing. Data filed after 5:30 p.m. Eastern on the final business day of a quarter may be included in the next quarterly posting.

## 7. Research decision and next gate

**Decision: retain the high-precision Form 4 cohort as a candidate-only research line; do not run an event study yet.**

Next phase: crosswalk the 2026Q3 candidate cohort itself (59 accessions / 31 issuer CIKs / 48 issuer-filing events) against original Form 4 XML and the latest supported periodic filing strictly before each Form 4 filing date. Require:

- original Form 4 issuer CIK, symbol, title, transaction row and footnote reconciliation;
- prior periodic XBRL filing no more than 365 calendar days old;
- exact same-CIK TradingSymbol + Security12bTitle + SecurityExchangeName context;
- compatible common-stock class/title with no fuzzy ticker join;
- separate event-time and transaction-date identity flags;
- preservation of all unresolved and no-anchor cases.

If that candidate-specific identity gate passes, expand across the remaining five sampled quarters and then test historical price availability. Do not infer that the 2026Q3 cohort is representative of the full historical universe.

No returns, alpha, bootstrap/LOO, chronological OOS or holdout test was run. No security master or strict PIT identity was admitted. F80, production, universe, capital and parameters remain unchanged. No data purchase, vendor contact or email was made; the SEC contact secret was used only in the masked request User-Agent.

## 8. Reproducibility

- Auditor: `research/phase342_sec_insider_bulk_sample_audit.py`
- Tests: `research/test_phase342_sec_insider_bulk_sample_audit.py` — 5/5 passed.
- Workflow: `.github/workflows/phase342_sec_insider_bulk_sample_audit.yml`
- Result: `phase342_output/phase342_sec_insider_bulk_sample_audit.json` (in artifact).
- Candidate summary: `phase342_output/phase342_candidate_summary.csv` (in artifact).
- Source response headers and all six original SEC ZIP archives are in artifact 13965917386.

Official sources:
- [SEC Insider Transactions Data Sets](https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets)
- [SEC Insider Transactions Data Sets Readme](https://www.sec.gov/files/insider_transactions_readme.pdf)
