# Phase 609 — full-quarter SEC 13F sequence-group audit

<badge>Live audit: passed · 2/2 datasets</badge>

**Workflow:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/45533301261  
**Artifact:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/45533301261/artifacts/14984944160  
**Offline regressions:** 5/5 passed.  
**Samples:** SEC 2018 Q1 and 2026 June–August data sets.

## Executive result

The Phase 608 group-aware parser ran over both complete SEC data sets. Submission/CoverPage joins were exact, SummaryPage included-manager counts reconciled to member rows with zero mismatches, and the large INFOTABLE was streamed.

The source-confirmed model is viable structurally: sequence groups can be reconstructed across both full-quarter samples. The remaining unmatched numeric references and nonnumeric as-filed values are retained as exceptions, not repaired.

## 1. Full-quarter coverage and group structure

| Metric | 2018 Q1 | 2026 Jun–Aug |
|---|---:|---:|
| SUBMISSION accessions | 6,570 | 11,852 |
| COVERPAGE accessions | 6,570 | 11,852 |
| Missing / extra cover pages | 0 / 0 | 0 / 0 |
| OTHERMANAGER2 member rows | 2,764 | 3,890 |
| Distinct sequence groups | 2,744 | 3,887 |
| Multi-member groups | 6 | 2 |
| Maximum members in one group | 12 | 3 |
| Exact duplicate member rows | 0 | 0 |
| Invalid member rows | 0 | 0 |
| SUMMARYPAGE manager-count comparisons | 5,017 | 10,036 |
| SUMMARYPAGE mismatches | 0 | 0 |

Group-size distribution:
- 2018: 2,738 single-member groups; 2 two-member groups; 2 three-member groups; 1 four-member group; 1 twelve-member group.
- 2026: 3,885 single-member groups; 1 two-member group; 1 three-member group.

The 20 repeated sequence rows in 2018 and 3 in 2026 are exactly the extra member rows above the group count. There are zero exact duplicate member rows. This confirms that the Phase 606 repeated accession/sequence pairs are group membership, not duplicated records.

## 2. INFOTABLE group-reference audit

| Metric | 2018 Q1 | 2026 Jun–Aug |
|---|---:|---:|
| INFOTABLE rows | 1,879,731 | 3,830,274 |
| Joined to SUBMISSION/COVERPAGE | 100% | 100% |
| Numeric group-reference tokens | 1,042,851 | 1,463,186 |
| Matched to a sequence group | 1,018,107 (97.63%) | 1,448,672 (99.01%) |
| Unmatched numeric sequence tokens | 24,744 (2.37%) | 14,514 (0.99%) |
| Matched to multi-member groups | 4,086 (0.40% of matched) | 3,632 (0.25% of matched) |
| Matched to single-member groups | 1,014,021 | 1,445,040 |
| Zero sentinel tokens | 81,014 | 310,179 |
| Nonnumeric as-filed rows | 8,520 | 40,155 |
| Rows with no manager reference | 973,176 | 2,272,853 |
| Notice filing information rows | 0 | 0 |

The nonnumeric values include names and placeholders such as “James Fereday”, “Clearstead”, “Other”, “XXEC, INC.”, “NO”, “-”, and “_”. They remain raw filed values and are not converted into manager IDs. Numeric references that do not match a group remain unresolved; the known Marshall Wace and Dakota exceptions are present in the full-quarter unmatched sample.

The low multi-member-reference share means most matched numeric references resolve to a single-member group in these two samples. It does not prove that the member is the beneficial owner, decision-maker, or source of an informed trade.

## 3. Manager identity quality

OTHER_MANAGER2 member-row identifiers:
- 2018: 1,485 CIK + file number; 134 CIK only; 724 file number only; 421 with neither stable identifier.
- 2026: 2,075 CIK + file number; 395 CIK only; 716 file number only; 704 with neither stable identifier.

OTHERMANAGER roster table:
- 2018: 3,771 rows, 1,864 accessions, no duplicate accession/SK keys; 2 CIK/file-number conflicts, 1 invalid file number, 164 unresolved identities.
- 2026: 4,848 rows, 2,456 accessions, no duplicate accession/SK keys; 371 unresolved identities.

Names alone are never used as stable identity keys. Member rows without CIK or Form 13F file number remain unresolved.

## 4. Notice controls

- 2018: 1,572 notice accessions; all have an OTHERMANAGER roster; zero INFOTABLE rows.
- 2026: 1,952 notice accessions; all have an OTHERMANAGER roster; zero INFOTABLE rows.

This supports keeping 13F-NT separate from zero-holdings portfolios.

## 5. Decision

**PASS:** full-quarter group structure, 100% submission/cover-page join, exact SummaryPage member-count reconciliation, streaming INFOTABLE parse, and sequence-group reference mapping.

**REVIEW / NOT SIGNAL-ELIGIBLE:** unmatched numeric references, raw nonnumeric values, member rows without stable identifiers, filing acceptance timestamps, amendment state, and effective-dated F80 security identity.

The next gate is not a return backtest yet. First add accepted-at timestamps and as-of amendment state; then map holdings to the historical F80 universe with effective-dated CUSIP/FIGI/ticker identity. Only group-level ownership features with adequate point-in-time coverage should enter an incremental test versus frozen F80/LTM.

No alpha, OOS, bootstrap, LOO or production eligibility is claimed. No data purchase, vendor contact, options request, production change, exposure or capital change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; options budget USD 0.
