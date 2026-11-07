# Phase 152 — SEC Form 4/A amendment lineage and acceptance-time pilot

**Date:** 2026-11-06  
**Status:** completed sample audit; no return/alpha test.

## Executive finding

A Form 4/A must not be treated as an independent set of new insider trades. SEC Form 4 instruction 9 says an amendment adding lines should report only the added lines; an amendment changing lines should provide the complete amended lines, but must not repeat unchanged lines. The SEC bulk-data README separately warns that its as-filed data may contain redundancies, inconsistencies and discrepancies.

We found a concrete 2026Q3 example where a Form 4/A repeats unchanged Table I and Table II lines from the original Form 4 and adds one new exercise line in each table. A naive sum of original plus amendment would double count the original sales and exercise.

**Clarification to Phase 151:** the rule against repeating unchanged lines is the SEC instruction, not a guarantee about observed filings. As-filed amendments can repeat unchanged lines. A line-level original-to-amendment diff is mandatory before constructing incremental event flow.

## 1. Candidate parent-accession linkage in the two source quarters

The SEC bulk schema contains DATE_OF_ORIG_SUB (date of original filing) but not an original accession-number foreign key. We tested a conservative within-quarter candidate heuristic:
- same issuer CIK;
- amendment DATE_OF_ORIG_SUB equals candidate original Form 4 FILING_DATE; and
- at least one shared reporting-owner CIK.

This is candidate generation, not a definitive parent link.

| Form 4/A sample | Unique candidate | Ambiguous candidates | No same-quarter candidate |
|---|---:|---:|---:|
| 2012Q1 (1,862 amendments) | 1,146 (61.5%) | 40 (2.1%) | 676 (36.3%) |
| 2026Q3 (627 amendments) | 341 (54.4%) | 7 (1.1%) | 279 (44.5%) |

“No same-quarter candidate” does not mean the original is missing; it may have been filed in a prior quarter or require broader accession/owner reconciliation. Ambiguous cases remain unresolved.

For unique candidate links, we compared Table I amendment lines against the candidate original using:
- loose signature: security title + transaction date + transaction code;
- strict signature: loose fields plus shares, price, acquired/disposed code, direct/indirect ownership and nature of ownership.

| Unique candidate links | Amendment Table I rows | Original Table I rows | Loose row overlaps | Strict row overlaps | Links with any loose overlap |
|---|---:|---:|---:|---:|---:|
| 2012Q1 (1,146 links) | 1,452 | 1,923 | 1,209 | 722 | 711 |
| 2026Q3 (341 links) | 552 | 642 | 356 | 231 | 190 |

These are structural diagnostics, not final deduplication labels. A loose match may be a changed line; a strict match is an identical line signature but can still be ambiguous if the original filing is not confirmed. Some amendments have no loose overlap with their heuristic candidate (435/1,146 and 151/341). Never auto-link or auto-deduplicate on the heuristic alone.

## 2. Verified SEC example: Eton Pharmaceuticals, 2026-08-28 / 2026-08-31

Original Form 4: accession 0001437749-26-029196. Amendment: 0001437749-26-029308. Both name reporting owner CIK 0001182615 and issuer CIK 0001710340. The amendment states its original filing date as 08/28/2026.

Official SEC acceptance timestamps:
- Original Form 4: 2026-08-28 16:51:30 ET.
- Form 4/A: 2026-08-31 16:06:45 ET.

Both were accepted after the regular 16:00 ET close. The original filing's first tradable session was Monday 2026-08-31; the amendment's first tradable session was Tuesday 2026-09-01. Filing date alone cannot establish the intraday knowledge boundary.

The original Form 4 contains:
- Table I: M 50,000 shares; S 36,387; S 13,485; S 128.
- Table II: one option M exercise for 50,000 underlying shares.

The Form 4/A repeats those same four Table I lines and the same Table II 50,000 option exercise, then adds:
- Table I: M 12,500 shares.
- Table II: a second option M exercise for 12,500 underlying shares.

The SEC instruction 9(a)–(b) says not to repeat unchanged lines. Nevertheless, this actual as-filed amendment does so. If an event model simply sums Form 4 and Form 4/A rows, it doubles the original 50,000-share exercise and 50,000 shares of sales, while the only new Table I line is the additional 12,500-share M exercise. The 4/A is not a second independent 50,000-share sale signal.

This is why the as-filed bulk dataset must be reconciled to the original filing before calculating net insider activity.

## 3. Point-in-time and event-state rules

1. Preserve every accession as immutable, with its EDGAR acceptance timestamp and source filing.
2. Resolve parent accession from original filing date, issuer, reporting owner and EDGAR filing history. DATE_OF_ORIG_SUB alone is not a unique foreign key.
3. For each confirmed amendment, diff Table I and Table II lines against the parent:
   - newly added line: incremental event known at amendment acceptance;
   - changed line: replace the prior reported line only from amendment acceptance; retain both vintages;
   - unchanged repeated line: do not count as a new transaction;
   - deleted/withdrawn line: record a tombstone/retraction at amendment acceptance.
4. Reconstruct latest reported ownership state separately from incremental event flow. An amendment may restate a state while contributing only one new transaction.
5. Never backdate amended values to the original transaction date or original acceptance.
6. Use actual acceptance time and market calendar. After-close acceptance is first tradable next session; intraday acceptance is usable only after its actual receipt.
7. If the parent cannot be uniquely resolved, quarantine the amendment from event-flow aggregation. Do not guess based on ticker, issuer name or date alone.

## 4. Decision

Form 4/A remains usable as a filing-time update only after parent accession and line-level diff. It is not an independent trade stream. The within-quarter heuristic recovers a candidate parent for a majority of the endpoint sample, but leaves 676/1,862 and 279/627 without a same-quarter candidate, plus 40 and 7 ambiguous cases. This is insufficient for a complete historical amendment ledger.

Next gate: use accession acceptance headers and reporting-owner CIK to resolve parents across adjacent quarters, manually adjudicate a stratified sample of additions/changes/repeated lines, then construct an immutable amendment ledger. Only then consider insider clusters or forward-return tests.

No alpha/backtest was run, no final holdout was consumed, no provider was contacted or purchased from, and no production code or F80 baseline was changed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Official SEC references
- [Form 4 instructions, General Instruction 9 (amendments), 2025 version](https://www.sec.gov/files/form4data.pdf).
- [SEC Insider Transactions Data Sets README](https://www.sec.gov/files/insider_transactions_readme.pdf): as-filed data may contain redundancies/inconsistencies; DATE_OF_ORIG_SUB is a date, not an original accession.
- [Original ETON Form 4 index](https://www.sec.gov/Archives/edgar/data/1710340/000143774926029196/0001437749-26-029196-index.html).
- [Original ETON Form 4 rendered document](https://www.sec.gov/Archives/edgar/data/1182615/000143774926029196/xslF345X06/rdgdoc.xml).
- [ETON Form 4/A index](https://www.sec.gov/Archives/edgar/data/1710340/000143774926029308/0001437749-26-029308-index.html).
- [ETON Form 4/A rendered document](https://www.sec.gov/Archives/edgar/data/1182615/000143774926029308/xslF345X06/rdgdoc.xml).
