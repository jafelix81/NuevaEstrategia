# Phase 607 — bounded original EDGAR XML reconciliation for 13F manager-reference exceptions

**Status: PASS — six original filing document sets reconciled at source level.**  
**Cutoff:** 2026-11-25 02:22 UTC.  
**Workflow:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/45532361067  
**Artifact:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/45532361067/artifacts/14985766313  
**Offline tests:** 4/4 passed.  
**Samples:** three 2018 and three 2026 accessions.

## Executive result

All six accessions were resolved to the correct filing CIK, their EDGAR filing-detail pages were fetched, and the raw primary-document / information-table XML files were parsed. This required using the filing CIK from the filing record rather than assuming the accession prefix is always the filer CIK; one 2026 accession was submitted through a filing agent.

The source evidence resolves the main Phase 606 ambiguity:

**INFOTABLE.OTHERMANAGER is a reference to a sequence group, not a unique individual manager row.** The cover page may contain several manager/member rows carrying the same sequence number. Those rows are group members. A position references the group, so the position cannot be attributed to one member without additional evidence.

## 1. Source-level findings

| Filing | Cover-page groups | Information-table result | Adjudication |
|---|---:|---|---|
| Marshall Wace North America, 0001325091-18-000003 | 1, 2 | 1,360 nonzero tokens all equal 2,811,304; 530 zero tokens; no token matches groups 1 or 2 | As-filed invalid numeric reference; do not repair |
| 2018 control, 0000950123-18-000878 | 1–91, all unique | 8,139 / 8,139 nonzero tokens match a group; 10,540 info rows | Clean sequence-group control |
| OppenheimerFunds, 0000728889-18-000299 | 17 member rows, 6 sequence groups; group 1 has 12 members | 2,434 numeric tokens all match a group; 411 point to group 1; 1,439 underscore placeholders | Repeated sequence 1 is a multi-member group, not a duplicate holding key |
| Dakota Wealth Management, 0001951757-26-001605 | 1, 2, 3, 8 | 204 / 229 numeric tokens match; 25 point to absent group 4 | As-filed invalid numeric reference; do not repair |
| XXEC, Inc., 0001828822-26-000007 | Zero other included managers | 23 information rows show the literal Other Manager label “XXEC, INC.” | Preserve as a nonnumeric as-filed label, not a sequence or manager signal |
| Allspring Global Investments Holdings, 0001890906-26-000061 | 5 member rows; sequence 1 has 2 members, sequence 2 has 3 | All 3,632 information rows reference group 1 or 2 | Group-level mapping is complete; individual-member attribution is ambiguous |

The SEC-rendered Allspring cover page explicitly reports five other included managers and shows sequence numbers 1, 1, 2, 2, 2. This is direct evidence that repeated sequence numbers are intentional group membership, not duplicate rows to delete. The information table's “Other Manager” field references those group numbers. See the original SEC cover page and filing detail.

The XXEC filing's cover page says there are zero other included managers, while its information table displays “XXEC, INC.” in the Other Manager column on all 23 rows. This is a literal as-filed label. It must not be split into separate “XXEC” and “INC.” manager tokens or treated as an extracted sequence number.

The Marshall Wace and Dakota examples show that numeric references can also be inconsistent with the cover-page sequence groups in the original filing. The source XML confirms these are not introduced by the flattened SEC data-set parser.

## 2. Correct data model

The prior row-level interpretation is superseded:

- OTHERMANAGER2 contains member rows.
- SEQUENCENUMBER identifies a group, and may repeat across multiple member rows.
- The natural group key is (ACCESSION_NUMBER, SEQUENCENUMBER).
- Member rows must be preserved separately within the group; do not deduplicate by sequence number.
- INFOTABLE.OTHERMANAGER links a position to the group, not to one unique manager.
- A group with multiple members cannot be used to assign the position to one individual manager.
- Nonnumeric Other Manager values are retained as raw as-filed text; they are not split into pseudo-identifiers.
- Zero is a no-other-manager / no-group sentinel.
- Numeric references absent from the cover-page group list remain unresolved as filed.

The current Phase 605 parser's assumption that (ACCESSION_NUMBER, SEQUENCENUMBER) uniquely identifies a manager row is therefore rejected. It may identify a group, but not an individual member.

## 3. Source coverage and limitations

Six of six filing document sets produced relevant primary-document and information-table XML. XSL transformation XML links were also present in the filing index; those style files are not filing data and were excluded after XML parse errors. The source-document URLs and SHA-256 hashes are retained in the artifact.

The parser currently extracts sequence numbers and information-table references; member-name/CIK fields are not yet fully normalized from every XML structure. The SEC-rendered cover pages were used to verify the group membership examples. The next implementation must preserve each member row and the exact source text/identifiers.

## 4. Decision and next gate

**Phase 605's manager graph must be redesigned around sequence groups.** Do not promote the current individual-manager graph or use its sequence-level links as unique manager attribution.

Next:
1. Implement an accession → sequence group → member rows graph.
2. Preserve raw nonnumeric labels and distinguish zero / valid group / unmatched numeric / group with multiple members.
3. Join INFOTABLE holdings to groups only.
4. Keep group-linked holdings out of single-manager signals unless the research hypothesis explicitly tests group-level ownership.
5. Rebuild as-of amendment state over group membership without future information.
6. Only then evaluate point-in-time coverage and any incremental signal versus frozen F80/LTM.

This source-integrity result is not alpha. No beneficial ownership, control, individual decision-maker, net exposure, short positions, predictive behavior, OOS, bootstrap, LOO or production eligibility is inferred.

No data purchase, vendor contact, options request, production change, exposure or capital change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; options budget USD 0.
