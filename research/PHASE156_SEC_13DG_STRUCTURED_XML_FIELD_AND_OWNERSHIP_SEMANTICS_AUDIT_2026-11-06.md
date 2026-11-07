# Phase 156 — SEC 13D/G structured-XML field coverage and non-additive ownership semantics

**Date:** 2026-11-06  
**Status:** Completed hash-pinned source reanalysis; no returns, feature panel or alpha test.

## Executive decision

The structured 13D/G XML is machine-readable and carries useful issuer-level ownership facts, but it is not yet a viable stand-alone long-horizon Smart Money signal source. Three limitations are decisive:

1. Mandatory structured XML begins on **2024-12-18**, leaving fewer than two years of mandatory history as of this audit. The Phase 124 global sample contains XML in only eight quarters (2024Q4–2026Q3); pre-XML filings remain legacy HTML/ASCII and their event/owner extraction is not yet validated end-to-end.
2. Reporting-person identity is incomplete. In this sample, 13G has no reporting-person CIK in 158 owner blocks; 13D has a reporting-person CIK in only 90/152 blocks. The filer CIK must not be substituted for a reporting person.
3. Reporting-person positions are not additive. Identical aggregate/percent/voting/dispositive tuples repeat within 48/102 filings. Summing owner rows would overstate disclosed beneficial ownership unless control/group relationships are adjudicated.

The source remains a **conditional event/ownership-state candidate**, not a transaction tape and not an approved return feature. The next gate is identity/lineage normalization plus a broader historical panel; no return test is authorized yet.

## 1. Immutable source and reproducibility

Reused Phase 124 run **42073725379**, artifact **13436764625**. No new SEC requests were made.

- Artifact ZIP SHA-256: \`85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc\`
- CSV SHA-256: \`be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5\`
- Sample: 600 global index rows; 599 actual 13D/G filings plus one quarantined SC TO-T/A index alias.
- Structured XML: 102/599 actual filings (17.03%) in the deterministic stratified sample; 99/99 rows marked as requiring XML have it, plus three voluntary pre-compliance XML filings.
- All 102 raw submission hashes, XML subject issuer CIKs and XML filer CIKs reconcile to the pinned SEC-header fields.
- XML sample spans eight quarters: 2024Q4–2026Q3. The 2024Q4 XML rows are voluntary pre-compliance filings; the mandatory structured period begins 2024-12-18.

This is a stratified filing-index sample, not a complete security universe or a population-wide estimate. The 17.03% XML share must not be interpreted as the population's structured-filing rate because the sample spans the legacy and structured regimes.

## 2. Issuer/security identity and schema versions

The XML subject issuer CIK matches the SEC-header subject CIK in **102/102** filings; the XML filer CIK matches the SEC-header filer CIK in **102/102**. Keep those roles separate.

A schema correction from Phase 127 is preserved: CUSIP extraction must read \`issuerCUSIP\`, \`issuerCusip\` **and** \`issuerCusipNumber\`, scoped to \`issuerInfo\`. Reading only \`issuerCusip\` misses values in the newer XML structure. Phase 156 parses all values, deduplicates identical values, validates check digits and never silently selects among multiple distinct CUSIPs.

| Structured XML CUSIP status | Filings |
|---|---:|
| Checksum-valid | 98/102 |
| Zero placeholder (\`000000000\`) | 2 |
| Invalid check digit | 1 |
| Malformed length | 1 |
| Missing CUSIP element | 0 |

All 102 sample XML filings contain a CUSIP element, but four are not valid security identifiers. A valid check digit still does not establish historical effectiveness, the correct share class, listing status or investable-universe membership. Phase 149's current OpenFIGI crosswalk is not effective-dated and cannot be backdated.

The SEC's Schedule 13D/G technical specifications changed on 2026-03-16 to allow multiple CUSIP numbers; version 2.3 followed on 2026-04-15. The parser therefore preserves CUSIP arrays rather than assuming one scalar. No sample filing contains multiple distinct CUSIPs, but the implementation is tested for that case.

## 3. Reporting-person identity and ownership fields

| Measure | 13D | 13G | Combined |
|---|---:|---:|---:|
| Filings | 34 | 68 | 102 |
| Reporting-person blocks | 152 | 158 | 310 |
| Reporting-person name present | 152 | 158 | 310 |
| Reporting-person CIK present | 90 | 0 | 90 |
| Name + aggregate shares + percent complete | 152 | 158 | 310 |
| All four voting/dispositive power fields complete | 151 | 157 | 308 |

In the 13G sample, all 158 reporting-person blocks contain a name and ownership values but none contains a reporting-person CIK. The filer CIK identifies the EDGAR filer, not necessarily every beneficial owner. Do not use it as a substitute. In 13D, 90/152 reporting-person blocks have a CIK; 150/152 expose the no-CIK indicator. The remaining name-only cases require separate identity evidence.

The 13D Item 4 \`transactionPurpose\` text is populated in 23/34 filings (69,317 characters in the sample); funds-source text is present in 26/34. This is a candidate for a separate, pre-registered activism/purpose classification study, not a directional trade signal. No NLP or return test was run in this phase.

## 4. Non-additive reporting-person positions

Within each filing, Phase 156 compares the normalized tuple:

\`(aggregate shares, percent of class, sole/shared voting power, sole/shared dispositive power)\`.

Identical tuples repeat in:
- 21/34 13D filings, with 68 excess repeated owner rows;
- 27/68 13G filings, with 63 excess repeated owner rows;
- **48/102 filings overall**, with 131 excess repeated owner rows.

In 9/34 13D and 22/68 13G filings, every reporting-person block has the same tuple. This is consistent with overlapping attribution through control/adviser relationships; it is not proof that the reporting persons are independent positions. Never sum aggregate shares across reporting persons unless the reporting-person/group graph and disclaimed/shared powers have been adjudicated. The correct unit is a filing/issuer/class state with explicit owner relationships, not a naive sum of person rows.

## 5. Amendment lineage

There are 59 amendments in the 102 XML sample. \`amendmentNo\` is present in all 59, but \`previousAccessionNumber\` appears in only 32/59 (54.24%):

- 13D: 9/20 amendments;
- 13G: 23/39 amendments.

A missing previous accession is unresolved lineage, not evidence that the filing is an original. Amendments are updates to disclosed state at their own EDGAR acceptance time; they are not independent purchases or flows. The 32 pointers also cannot be fully followed within this 600-row random sample because none of their parent accessions is guaranteed to be sampled.

## 6. Point-in-time and OOS implications

- The reported event date is not the public-knowledge timestamp.
- Use the accession's EDGAR acceptance datetime as the conservative knowledge boundary; for a regular-session EOD process, after-16:00 ET acceptance is not available for that same regular session.
- Do not backdate amendments or corrected ownership state to the event date or original filing date.
- Mandatory XML begins 2024-12-18; the legacy period requires a separate body-first HTML parser, role validation and amendment-state reconstruction. The eight-quarter structured sample alone is too short for multi-regime OOS robustness.
- The 600-row sample is not an active/delisted security master. Subject CIK and CUSIP still require effective-dated share-class, ADR, successor, corporate-action and historical membership mapping.

## 7. Decision and next gate

**Keep 13D/G as a conditional ownership-event source; do not promote a feature.** The useful data are the issuer/class ownership snapshot, percent and voting/dispositive powers, 13D purpose text, and amendment state. The unverified hypotheses are whether changes in unique beneficial-owner groups, activist purpose, or ownership concentration predict returns beyond LTM/F80 and ordinary momentum.

Next work, in order:
1. Build a role-aware owner/group graph that does not sum overlapping reporting-person rows.
2. Reconcile every amendment's previous accession where present and use conservative accession-chain reconstruction where absent; quarantine unresolved chains.
3. Extend legacy HTML extraction only if it can meet the same subject/filer, CUSIP, owner, timestamp and amendment gates.
4. Build effective-dated subject-security/share-class and active/delisted membership mapping.
5. Only then consider a chronological, cost-aware test against frozen LTM/F80 and price-momentum controls. Keep a separate untouched holdout.

No forward-return test, no alpha claim, no final holdout use, no vendor contact/purchase and no production change. \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.

## Official references

- SEC, [EDGAR Release 23.4](https://www.sec.gov/submit-filings/edgar-news-announcements/edgar-release-23-4), Dec. 18, 2023: structured Schedule 13D/G XML compliance date of Dec. 18, 2024.
- SEC, [EDGAR Release 24.4](https://www.sec.gov/submit-filings/edgar-news-announcements/edgar-release-24-4): HTML/ASCII formats replaced by XML for the standard Schedule 13D/G flow; certain 13D amendments may continue in HTML for specified combined filings.
- SEC, [Technical Specifications](https://www.sec.gov/submit-filings/technical-specifications): Schedule 13D/G XML v2.2 (Mar. 16, 2026) permits multiple CUSIPs; v2.3 (Apr. 15, 2026) includes a CUSIP display fix for 13G/A.
- Repository: [Phase 124 global sample auditor](phase124_global_sec_13dg_stratified_submission_audit.py), [Phase 127 CUSIP schema correction](PHASE127_SEC_13DG_XML_CUSIP_SCHEMA_CORRECTION_2026-11-05.md), [Phase 149 OpenFIGI crosswalk](PHASE149_OPENFIGI_CUSIP_CROSSWALK_FEASIBILITY_2026-11-06.md), [Phase 155 role-aware event-date audit](PHASE155_SEC_13DG_ROLE_AWARE_EVENT_DATE_AND_PHASE154_QUARANTINE_2026-11-06.md).