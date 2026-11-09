# Phase 119 — SEC 13D/13G XML schema and amendment-lineage feasibility

Date: 2026-11-05  
Status: **PASS_WITH_LINEAGE_CAVEATS**  
Scope: artifact-only analysis of the 200 XML-bearing rows in the Phase 84 600-filing pilot, joined to the 43 frozen Phase 82 quarterly master indexes. No live SEC retrieval and no forward-return calculations.

## 1. Schema coverage is strong, but 13D and 13G are not one schema

The 200 XML-bearing submissions comprise 79 Schedule 13D and 121 Schedule 13G filings. The parser must branch by form family:

- **13D:** 79/79 issuer CIKs and filer CIKs match the SEC header; 79/79 have dateOfEvent; 260 reportingPersonInfo nodes have names, ownership percentage, aggregate amount and reporting-person type. Reporting-person CIK is present on only 158/260 nodes (60.8%); sole voting/dispositive power is present on 260/260 and shared voting/dispositive power on 251/260.
- **13G:** 121/121 issuer CIKs and filer CIKs match the SEC header; 121/121 have eventDateRequiresFilingThisStatement; 210 coverPageHeaderReportingPersonDetails nodes have names, ownership percentage, aggregate amount, voting/dispositive power and reporting-person type. The per-person nodes do not carry a reporting-person CIK; the filing-level filer CIK matches the SEC header on 121/121 filings. Group-member text is populated on 25/121 filings and subsidiary text on 79/121.
- Across both families, amendmentNo is present on all 97/97 /A filings. Event dates are reporting-period/event reference dates, not knowledge timestamps.

A generic parser that searches only for 13D reportingPersonInfo would incorrectly treat all 121 13G filings as having no reporting persons. The family-specific schemas are mandatory.

## 2. Security identity must be part of the reporting-group key

The XML has an issuer class title on 200/200 filings, but issuerCUSIP/issuerCusip is populated on only 139/200 (69.5%). A reporting-group key built only from issuer CIK and filer/reporting-person names can merge distinct securities of the same issuer.

A concrete 13G example: six filings share issuer CIK 0001100663, filer CIK 0002012383 and reporting-person name BlackRock, Inc.; all six say “Common Stock” but carry six distinct CUSIP-field values (464287457, 46435G672, 464288679, 46438G588, BRYSJBKB1, 46435U853). Without the security identifier, these six positions collapse into one false group. With CUSIP first and class title only as a provisional fallback:

| Family | Repeated issuer/group keys without security | Repeated issuer/group/security keys |
|---|---:|---:|
| 13D | 4 groups / 9 rows | 3 groups / 6 rows |
| 13G | 3 groups / 10 rows | 1 group / 2 rows |

The remaining 13G repeated pair is a candidate original/amendment pair, not a verified chain: it has no explicit previous-accession link in this sample. The remaining repeated 13D groups contain amendments only; their original filings are outside this 200-row XML sample. Class-title fallback is diagnostic, not a substitute for a validated security master; ambiguous/missing class identity must be quarantined.

## 3. Explicit amendment pointers are useful but not sufficient

There are 97 amendments in the sample. All 97 carry amendmentNo, but only 46/97 carry previousAccessionNumber.

The Phase 119 audit scanned all 43 raw Phase 82 quarterly master-index files for those 46 predecessor accessions. Results:

| Validation | Result |
|---|---:|
| previousAccessionNumber present | 46/97 amendments |
| Predecessor accession found in frozen master index | 45/46 |
| Prior index contains current issuer CIK | 45/46 |
| Prior index contains current filer CIK | 45/46 |
| Prior form family matches current 13D/13G family | 45/46 |
| Prior filing date precedes current filing date | 45/46 |
| Amendments without an explicit predecessor | 51/97 |

The one unresolved pointer is on accession 0000886982-25-001416 (13G/A, issuer CIK 0000723612, filer CIK 0000886982, CUSIP field 053774105). Its SEC primary XML contains previousAccessionNumber=0000769993-25-000432, but that accession is absent from all 43 frozen master-index files. Do not guess a replacement accession or infer the chain from names/percentages. See the [SEC primary XML](https://www.sec.gov/Archives/edgar/data/886982/000088698225001416/primary_doc.xml).

The 45 resolved links are **index-level validated**: the previous accession appears with the current issuer and filer CIKs, the same form family, and an earlier date. The predecessor raw submissions have not yet been downloaded, so CUSIP, reporting-person set and ownership-state continuity still need verification.

## 4. Historical coverage limitation

Only 200/600 pilot rows contain structured XML. Phase 118 established that the 192 actual mandatory-XML 13D/G rows have XML after quarantining the one non-13D/G master-index alias; eight additional rows have optional XML. The other 400 rows need a legacy HTML parser. An XML-only pipeline therefore cannot backfill the 2016–2024 portion of the 13D/G history.

## 5. Decision and next gate

**Decision:** structured 13D/13G data is feasible for role-aware ownership extraction in the post-XML regime, but event lineage is only partially explicit. Promote to a narrowly scoped predecessor-content audit, not to returns testing.

Next steps:

1. Fetch only the 45 index-validated predecessor submissions and compare issuer CIK, filer CIK, CUSIP/class, reporting-person set and ownership fields. Keep the one unresolved pointer quarantined.
2. For the 51 amendments without explicit predecessor links, link only when issuer CIK + security key + reporting-group identity + amendment chronology produce a unique, auditable chain; otherwise keep them as standalone observations or exclude them from change features.
3. Preserve 13D activist/control-purpose and 13G passive/ordinary-course families separately.
4. Build a historical CIK-to-security crosswalk including inactive/delisted securities and historical ticker changes. The current 319-CIK candidate map is not PIT universe membership.
5. Build a legacy HTML parser and reconcile it against structured XML on overlapping filings before extending the panel pre-December 2024.
6. Use the SEC acceptance time only with a conservative next-session availability rule until public dissemination time is independently verified. Never use the XML event date as the signal's knowledge date.

No forward returns, feature selection, alpha inference, vendor purchases or production changes were performed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## 6. Reproduction

Inputs: Phase 84 artifact 13364856424 and Phase 82 artifact 13353118959 (same immutable inputs documented in Phase 118).

\`\`\`bash
python research/phase119_sec_13dg_xml_lineage_audit.py \\
  --phase84-zip phase84.zip \\
  --phase82-zip phase82.zip \\
  --output phase119_lineage_audit.json
python -m unittest -v research.test_phase119_sec_13dg_xml_lineage_audit
\`\`\`

The script performs no network calls. Six offline regression tests passed locally; CI is wired to run them on push/PR.
