> **Phase 607 source-XML erratum:** Repeated (ACCESSION_NUMBER, SEQUENCENUMBER) rows are not automatically duplicate records. The source filings show that multiple manager/member rows intentionally share a sequence number, which identifies a group. The 20 / 3 repeated sequence pairs reported below are therefore group-membership patterns unless the member rows themselves are exact duplicates. Nonnumeric Other Manager values are as-filed labels (for example, “XXEC, INC.”), not automatically malformed identifiers. See Phase 607 and Phase 608.

# Phase 606 — SEC Form 13F actual manager-table cardinality and reference audit

**Status: REVIEW — actual SEC samples parsed; source-filing reconciliation still required.**  
**Cutoff:** 2026-11-25 02:16 UTC.  
**Workflow:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/45531619890  
**Artifact:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/45531619890/artifacts/14985386673  
**Samples:** 2018 Q1 and 2026 June–August.

## Executive result

The live audit downloaded both official SEC ZIPs using the existing shared project contact fallback. All six required TSV members were present in both samples. The large INFOTABLE was streamed.

The key finding is that OTHERMANAGER2 is plainly one-to-many by accession in the actual data, despite the SEC PDF marking ACCESSION_NUMBER alone as its key. SUMMARYPAGE's OTHERINCLUDEDMANAGERSCOUNT reconciles exactly to the number of OTHERMANAGER2 rows in every compared record. However, duplicate (ACCESSION_NUMBER, SEQUENCENUMBER) pairs and non-resolving references remain; therefore the Phase 605 graph is not yet admitted.

## 1. Actual table cardinality

| Metric | 2018 Q1 | 2026 Jun–Aug |
|---|---:|---:|
| SUBMISSION accessions | 6,570 | 11,852 |
| OTHERMANAGER rows | 3,771 | 4,848 |
| OTHERMANAGER unique accessions | 1,864 | 2,456 |
| OTHERMANAGER duplicate accession/SK keys | 0 | 0 |
| OTHERMANAGER2 rows | 2,764 | 3,890 |
| OTHERMANAGER2 unique accessions | 968 | 1,206 |
| Collisions with accession-only key | 1,796 | 2,684 |
| Accessions with multiple OTHERMANAGER2 rows | 472 | 607 |
| Maximum OTHERMANAGER2 rows per accession | 91 | 85 |
| Duplicate accession/sequence pairs | 20 | 3 |
| SUMMARYPAGE count comparisons | 5,017 | 10,036 |
| SUMMARYPAGE count mismatches | 0 | 0 |

The exact SUMMARYPAGE reconciliation is strong evidence that the repeated OTHERMANAGER2 rows are intentional list entries, not simply accidental duplicate accessions. The accession-only key annotation in the PDF is insufficient for a row-level key. The candidate logical key is (ACCESSION_NUMBER, SEQUENCENUMBER), but it is not unique in every observed row because 20 / 3 duplicate pairs remain.

## 2. INFOTABLE.OTHERMANAGER reference hypotheses

The audit compared each nonzero token against both:
1. OTHERMANAGER2.SEQUENCENUMBER within the same accession.
2. OTHERMANAGER.OTHERMANAGER_SK within the same accession.

No nonzero token matched OTHERMANAGER_SK in either sample. The dominant valid reference hypothesis is therefore OTHERMANAGER2 sequence number, consistent with the SEC PDF's field description.

| Metric | 2018 Q1 | 2026 Jun–Aug |
|---|---:|---:|
| INFOTABLE rows | 1,879,731 | 3,830,274 |
| Rows joined to SUBMISSION/COVERPAGE | 1,879,731 | 3,830,274 |
| Rows containing manager references | 906,555 | 1,557,421 |
| Nonzero reference tokens | 1,043,472 | 1,463,649 |
| Zero tokens (separate sentinel bucket) | 80,538 | 309,742 |
| Matches to OTHERMANAGER2 sequence only | 882,575 | 1,356,301 |
| Matches to OTHERMANAGER_SK only | 0 | 0 |
| Matches to both tables | 0 | 0 |
| Unmatched to either table | 160,897 | 107,348 |
| Malformed nonzero tokens | 10,070 | 82,824 |

Tokenization now accepts comma- and whitespace-separated values. A literal zero is reported separately rather than incorrectly classified as malformed. This materially reduces false parsing exceptions, but does not resolve the remaining nonnumeric values or unmatched numeric references.

Examples requiring source-document adjudication include:
- 2018 accession 0001325091-18-000003, token 2811304.
- 2018 accession 0001606587-18-000252, nonnumeric token Wellesley.
- 2026 accession 0001951757-26-001605, token 4.
- 2026 accession 0001828822-26-000007, nonnumeric tokens XXEC and INC.

The unmatched and malformed rows are not discarded or guessed into a manager identity.

## 3. Manager identity resolution

CIK is used when explicit. File-number-only resolution is accepted only if the Form 13F file number maps to one CIK within the same bounded sample. Names are never identity keys.

For OTHERMANAGER2:
- 2018: 1,619 explicit CIK rows, 669 uniquely resolved by Form 13F file number, 471 unresolved without an identifier, and 5 invalid file numbers.
- 2026: 2,470 explicit CIK rows, 696 uniquely resolved by Form 13F file number, and 724 unresolved without an identifier.

For OTHERMANAGER:
- 2018: 2,486 explicit CIK, 1,118 file-number resolutions, 164 unresolved, 2 identity conflicts and 1 invalid file number.
- 2026: 3,361 explicit CIK, 1,116 file-number resolutions, 371 unresolved.

The unresolved rows are retained as unresolved. The current sample is not a global manager identity master.

## 4. Notice controls

- 2018: 1,572 notice accessions; all have an OTHERMANAGER roster; zero INFOTABLE holding rows.
- 2026: 1,952 notice accessions; all have an OTHERMANAGER roster; zero INFOTABLE holding rows.

This supports keeping notices separate from zero-holdings portfolios, but does not yet reconstruct notice amendment state as-of time.

## 5. Decision

**PASS:** actual table discovery, required schemas, SUBMISSION/COVERPAGE accession joins, SUMMARYPAGE included-manager count reconciliation, and the primary sequence-reference hypothesis.

**REVIEW / NOT ADMITTED:** duplicate sequence pairs, unmatched references, nonnumeric tokens, unresolved manager identities, original EDGAR XML reconciliation, notice/combination amendment state, and effective-dated security identity.

Next gate: fetch a stratified set of original EDGAR primary filing XML and information-table XML for the exception accessions above, compare the actual cover-page sequence numbers and information-table references, and adjudicate whether anomalies originate in filer submissions or SEC dataset extraction. Only then revise the Phase 605 relationship graph and its as-of state logic.

No manager-level signal, beneficial ownership, control, trade direction, alpha, OOS, bootstrap, LOO or production eligibility is inferred. Form 13F remains a delayed, quarterly ownership source, not a direct order-flow source.

No data purchase, vendor contact, options request, production change, portfolio change, exposure change or capital change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. Options budget remains USD 0.
