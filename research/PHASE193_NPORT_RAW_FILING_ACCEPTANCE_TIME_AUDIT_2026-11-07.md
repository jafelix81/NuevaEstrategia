# Phase 193 — SEC N-PORT raw filing, acceptance-time and direct-short reconciliation

**Audit date:** 2026-11-07  
**Disposition at commit:** hosted retrieval pending  
**Scope:** five purposively selected NPORT-P accessions from Phase 192. No representative prevalence estimate or return test.

## Objective

Move Phase 192 from search-indexed XML excerpts to reproducible raw-file evidence. For each accession, the hosted audit attempts to retrieve the SEC directory index, complete submission text and primary XML; hashes each byte stream; reconciles the accession, form and SEC-HEADER acceptance timestamp; parses every investment-security node; and checks the previously observed direct-short CUSIPs and minimum row counts.

The audit uses the SEC declared-contact requirement. It sends no request unless the GitHub Actions repository secret SEC_CONTACT_EMAIL is configured. The secret value is used only in the HTTP User-Agent and is never printed, committed or included in the artifact metadata.

## Sample

The sample remains purposive, not random:

| Filing year | Accession | Phase 192 expected direct-short CUSIPs |
|---|---|---|
| 2020 | 0001752724-20-163166 | 364760108, 222070203, 880779103, 674599105 |
| 2022 | 0001145549-22-056239 | 14448C104, 149123101, 166764100, 172908105 |
| 2023 | 0001145549-23-060491 | Partial discovery; no expected CUSIP |
| 2024 | 0001145549-24-075135 | 143130102, 26884L109 |
| 2025 | 0001145549-25-033457 | 31428X106 |

## Parsing and reconciliation rules

- The accession directory index must identify exactly one primary_doc.xml and exactly one complete-submission .txt whose filename contains the normalized accession.
- The complete submission header must match the expected accession and NPORT-P form and contain a 14-digit ACCEPTANCE-DATETIME.
- ACCEPTANCE-DATETIME is parsed as America/New_York local time and also emitted in UTC. FILED AS OF DATE is checked against its calendar date. A mismatch is retained as a diagnostic rather than silently corrected.
- XML parsing is namespace-independent and counts all invstOrSec nodes. The narrow direct-short candidate filter is payoffProfile=Short, assetCat=EC, issuerCat=CORP and invCountry=US.
- A row is sign-concordant only if units=NS and balance, valUSD and pctVal are all present and negative. Mismatches are counted, not silently discarded.
- CUSIP/ISIN/ticker are extracted from direct fields or identifier nodes where present. All expected Phase 192 CUSIPs must be found in the direct-short subset for the reconciliation gate to pass.
- Each raw index, complete submission and primary XML is hashed. Raw public documents are staged in a 90-day GitHub Actions artifact, not committed to the repository. The repo records metadata and hashes only.

## Point-in-time interpretation

SEC acceptance time is an official filing-processing timestamp, not proof of the exact first public receipt by every market participant. This phase does not verify first-publication or vendor receipt. It therefore does not authorize same-session or intraday trading. Any later daily study must use a conservative next-tradable-session rule and must preserve each NPORT-P/A accession as a separate append-only version.

## Admission gates

| Gate | Required result |
|---|---|
| Five complete raw XML files downloaded and SHA-256 hashed | All five |
| Five complete submission files downloaded and SHA-256 hashed | All five |
| SEC index resolves primary document and submission text | All five |
| Accession/form/acceptance header reconciliation | All five |
| Minimum direct-short row count and expected CUSIPs | All five |
| Series ID present | All five |
| First-public-receipt timestamp | Not established in this phase |
| NPORT-P/A amendment lineage | Not established in this phase |
| Effective-dated historical US listing identity | Not established |
| Broad active/delisted universe coverage | Not established |
| Strict PIT admission / alpha authorization | Not admitted |

## Hosted execution result

The current workflow artifact is the canonical record of the actual run. If the audit reports BLOCKED_MISSING_SEC_CONTACT_EMAIL, no SEC request was sent; an authorized project contact email must be added as the SEC_CONTACT_EMAIL repository secret before the workflow can retrieve public filings. If retrieval succeeds, use the artifact's per-accession hashes and row-level reconciliation to decide whether Phase 194 should proceed to amendments and a wider stratified sample.

## Controls

No data purchase, vendor contact, production change, holdout use, return test or alpha test. The Phase 27O long-accumulation result remains separate and is not reused as evidence against this short-side hypothesis. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
