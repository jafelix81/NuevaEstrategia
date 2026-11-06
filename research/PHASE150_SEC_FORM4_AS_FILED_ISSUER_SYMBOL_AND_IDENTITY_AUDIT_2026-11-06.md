# Phase 150 — SEC Form 4 as-filed issuer-symbol and identity audit

**Date:** 2026-11-06  
**Status:** PASS for historical issuer-symbol label feasibility; security identity and economic gates remain open.  
**Source artifact:** Phase 39 run `40606706518`, artifact `12781850078`, ZIP SHA-256 `203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66`.

## Executive decision

The SEC's Form 3/4/5 data set carries `ISSUERCIK`, `ISSUERNAME`, and `ISSUERTRADINGSYMBOL` in its as-filed `SUBMISSION` table. In two real endpoint samples, 98.49% (2012Q1) and 98.32% (2026Q3) of Form 4/4-A rows contain a conservative single-symbol candidate after preserving exchange-prefixed values. This is a useful historical issuer-label field that was not promoted in the earlier Form 4 feasibility gate.

**This does not make the symbol a permanent security identifier, establish target-universe coverage, or authorize an insider-alpha test.** Use issuer CIK as the primary issuer key; preserve the symbol exactly as filed and keep ambiguous/multi-class values quarantined.

## 1. Official data semantics and PIT boundary

The SEC currently advertises Insider Transactions Data Sets from January 2006 through September 2026. The data are extracted from the XML-based Forms 3, 4 and 5 and presented without change from as-filed submissions; the data set is published quarterly. The SEC warns that extraction/compilation errors are possible and that the bulk data are not a substitute for the original filings.

The SEC technical documentation defines the `SUBMISSION` row with:

- `ACCESSION_NUMBER`: unique EDGAR submission identifier;
- `ISSUERCIK`: Central Index Key of issuer;
- `ISSUERNAME`: issuer name;
- `ISSUERTRADINGSYMBOL`: issuer trading symbol;
- `FILING_DATE`: date only; and
- `PERIOD_OF_REPORT`: date of event requiring the statement; and
- `AFF10B5ONE` (in newer schemas): filing-level indicator that the reported transaction was made pursuant to a Rule 10b5-1(c) plan.

The SEC's final rule became effective February 27, 2023, and the mandatory Form 4/5 checkbox applies to beneficial-ownership reports filed on or after April 1, 2023. In July 2025, the SEC updated its 2023–2025 bulk data sets to include `AFF10B5ONE`; future data sets are processed similarly. The field is absent from the 2012Q1 schema and present in 2026Q3. This is a structural break: do not convert pre-April-2023 absence into `false` or compare the raw flag across eras as if coverage were uniform.

In the 2026Q3 Form 4/4-A sample, all 34,148 rows have a recognized value: 5,035 true (14.74%) and 29,113 false (85.26%). It is an accession-level field in `SUBMISSION`, not a verified transaction-row attribution when a filing contains multiple transactions. `false` means no Rule 10b5-1(c) affirmative-defense checkbox indication in that filing; it does **not** prove discretionary/public-market execution or absence of a non-Rule 10b5-1 trading arrangement. The SEC did not adopt the proposed optional checkbox for non-Rule 10b5-1 plans. The plan-adoption date and transaction-specific footnote linkage were not audited here; recover them from original filings before finer classification.

The bulk `SUBMISSION` table does not contain the accession's acceptance time-of-day. Therefore:

1. `PERIOD_OF_REPORT` is the transaction/event date, not public knowledge time.
2. `FILING_DATE` is a date-only field and cannot establish intraday ordering.
3. Join every accession to EDGAR acceptance metadata and preserve the exact accepted timestamp; if the join fails, do not impute an intraday time.
4. The quarterly bulk-file publication date is not the event-level knowledge time. For strict PIT, reconstruct from the original accession or verify that the filing itself was publicly available at the accepted timestamp.
5. Amendments are separate as-filed accessions. Apply each correction only from its own acceptance time; never backdate it to the original transaction date.

Phase 39 previously demonstrated that acceptance timestamps can be parsed from representative 2012 and 2026 EDGAR filing headers. That was a representative parser gate, not an all-accession acceptance-time reconciliation.

## 2. Sample and method

Reused the immutable Phase 39 artifact; no new SEC crawl or download was performed. The audit rechecked the outer artifact digest and both nested ZIP digests, then parsed `SUBMISSION.tsv` and its W3C tabular metadata.

Only `DOCUMENT_TYPE` values `4` and `4/A` were included. Form 3, 5 and their amendments were excluded. Symbol values were classified conservatively:

- `SINGLE_TOKEN`: one ticker-like token;
- `EXCHANGE_PREFIXED_SINGLE`: one token with an exchange prefix, preserving the raw value;
- `MULTI_OR_FREEFORM`: comma/slash/semicolon/space-separated or otherwise multi-value text; never split;
- `MISSING_OR_PLACEHOLDER`; and
- `OTHER_NONCANONICAL`.

“Canonical symbol candidate” is an audit classification, not an SEC-defined quality status. It means only `SINGLE_TOKEN` plus `EXCHANGE_PREFIXED_SINGLE`; it does not assert that the value is the correct share class or a unique security key.

## 3. Results

| Metric | 2012Q1 | 2026Q3 |
|---|---:|---:|
| All `SUBMISSION` rows | 71,282 | 38,152 |
| Form 4 / 4-A rows | 63,678 | 34,148 |
| Original Form 4 rows | 61,816 | 33,521 |
| Form 4/A rows | 1,862 | 627 |
| Unique issuer CIKs | 4,630 | 4,260 |
| Canonical symbol-candidate rows | 62,717 | 33,576 |
| Canonical symbol-candidate coverage | **98.49%** | **98.32%** |
| Missing/placeholder rows | 499 (0.78%) | 430 (1.26%) |
| Multi/free-form rows | 323 (0.51%) | 120 (0.35%) |
| Other noncanonical rows | 139 (0.22%) | 22 (0.06%) |
| Exchange-prefixed single values | 183 | 79 |
| Issuer CIKs with one canonical candidate | 4,429 | 4,110 |
| Issuer CIKs with multiple canonical candidates | 75 | 24 |
| Issuer CIKs with no canonical candidate | 126 | 126 |
| CIKs with multiple raw symbol values | 108 | 32 |
| Candidate symbols reused across CIKs | 16 | 6 |
| Maximum CIKs per reused candidate | 2 | 2 |
| Missing filing-date / event-date rows | 0 / 0 | 0 / 0 |
| `AFF10B5ONE` in schema | No | Yes |
| `AFF10B5ONE` true / false | Not available | 5,035 (14.74%) / 29,113 (85.26%) |

Examples of values that must not be force-normalized include `NYSE:SSD`, `NYSE: SCS`, `CBS, CBS.A`, `LEN, LEN.B`, `JWA/JWB`, `NYSE/TRN`, `(NYSE:FBC)` and `[NONE]`. These demonstrate that the issuer-level field can encode exchange prefixes, multiple share classes or free-form text.

The 126 issuer CIKs without a canonical candidate in each sample still have raw field values, but those values are only noncanonical or placeholder values. They are not 126 proven missing issuers.

## 4. Interpretation

**Positive:** the source has a high rate of as-filed issuer-symbol labels in these two endpoint samples. The SEC schema directly supplies the issuer CIK and the symbol on the same accession row, so the symbol can be retained as filing-time provenance without relying on a current ticker-to-CIK map.

**Limits:**

- The symbol field is issuer-level, not guaranteed class-specific. A value such as `CBS, CBS.A` must not be assigned to one class without a separate security-class key.
- Some CIKs show multiple candidate symbols within a quarter. This may reflect multiple listed classes, symbol changes or inconsistent filing values; it is not safe to collapse automatically.
- Some ticker candidates occur under more than one issuer CIK in the same quarter. Ticker-only joins are therefore not a permanent identity method.
- The audit covers two real quarters, not every quarter from 2006 to 2026. It establishes feasibility at two endpoints, not uninterrupted field-quality stability.
- High field coverage among Form 4 filers is not coverage of the broad investable universe. It does not resolve the prior 54.6%–83.3% mapping figures for the arbitrary legacy 335-name list, and that list is not the research universe.
- The SEC's transaction-code table defines `P` and `S` as “open market or private” purchase/sale. Those codes alone do not prove a public-market execution. Grants, awards, tax withholding, exercises, gifts, private transactions and footnoted exceptions require separate treatment.
- `AFF10B5ONE` provides a useful post-April-2023 control for Rule 10b5-1(c)-indicated filings, but its filing-level scope and adoption-date/footnote linkage must be preserved. The SEC did not adopt an optional non-Rule 10b5-1 checkbox, so `false` is not a clean “discretionary” label.

## 5. Decision and next gates

1. **Promote `ISSUERTRADINGSYMBOL` to a historical issuer-label/provenance field for Form 4 research.** Keep `ISSUERCIK` as the primary issuer key and retain the raw symbol string.
2. Do not split multi-symbol values, use ticker alone as a permanent key, or assign an issuer-level symbol to a specific share class without validating `SECURITY_TITLE` and an effective-dated class map.
3. Reconcile accession-level acceptance timestamps across the intended Form 4/4-A sample; keep event date, filing date, acceptance timestamp and first tradable session separate.
4. Build a broad, survivorship-aware point-in-time universe and effective-dated CIK-to-security/return crosswalk, including multiple classes, ticker changes, mergers, delistings and ADRs. Do not substitute the historical 335-name list.
5. Separate discretionary open-market purchases/sales from private transactions and non-discretionary codes using original filings, footnotes and transaction details. Recover Rule 10b5-1 plan-adoption dates and the filing-level checkbox's scope; treat non-Rule 10b5-1 arrangements as unclassified and do not backfill pre-April-2023 missing flags as false. The SEC bulk data disclaimer requires spot-checking original accessions.
6. Only after identity, coverage and PIT gates pass, preregister clustered insider-purchase hypotheses and compare them incrementally with frozen LTM/F80, using identical exposure/costs, chronological OOS, bootstrap and leave-one-out diagnostics. Control for prior returns, liquidity, volatility and event timing to distinguish information from return-chasing.

**No forward-return test, alpha claim, vendor contact/purchase, final-holdout use or production change was made.** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Official sources

- SEC, [Insider Transactions Data Sets](https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets) — history, as-filed status, quarterly publication, disclaimer and archive.
- SEC, [Insider Transactions Data Sets technical documentation](https://www.sec.gov/files/insider_transactions_readme.pdf) — `SUBMISSION` fields, issuer trading symbol, filing/event dates, amendments and transaction-code meanings.
- SEC, [Insider Trading Arrangements and Related Disclosures guide](https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/insider-trading-arrangements-and-related-disclosures) and [Release 33-11138](https://www.sec.gov/files/rules/final/2022/33-11138.pdf) — Form 4/5 Rule 10b5-1 checkbox requirements, effective date and April 1, 2023 compliance date.
- Prior repository gate: [Phase 39 Form 4 feasibility](PHASE39_SEC_FORM4_INSIDER_FEASIBILITY_2026-10-26.md).
