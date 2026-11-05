# Phase 120 — SEC 13D/13G predecessor-content audit specification

Date: 2026-11-05  
Status: LIVE AUDIT IN PROGRESS  
Scope: retrieve and reconcile the 45 predecessor submissions whose explicit `previousAccessionNumber` pointers passed the Phase 119 frozen-index checks. This is a targeted content/lineage gate, not a global 13D/13G census.

## Inputs and quarantines

- Immutable Phase 84 artifact: run 41914491120, artifact 13364856424 (`phase84-13dg-role-aware-identity-validation`).
- Phase 82 global master-index artifact: run 41892370262, artifact 13353118959.
- Phase 119 found 46 explicit predecessor pointers in the 200 XML-bearing current filings. Forty-five predecessor accessions appeared in the frozen 43-quarter master indexes with matching issuer CIK, filer CIK, form family and earlier filing date.
- One pointer remains quarantined: current accession `0000886982-25-001416` points to `0000769993-25-000432`, which was absent from all frozen Phase 82 indexes. Do not infer or substitute a predecessor.
- The committed manifest preserves both candidate SEC archive paths (subject-side and filer-side index rows) for each of the 45 validated predecessor accessions. It also binds each current filing to its immutable Phase 84 raw-submission path.

## Retrieval and integrity rules

1. Download only the 45 manifest predecessor accessions from official SEC Archives URLs.
2. Try both exact archive paths from the Phase 82 master index. Accept a response only when HTTP 200 and the SEC header accession exactly matches the requested predecessor.
3. If both paths return valid content, require byte-identical SHA-256 hashes. A content conflict is quarantined; do not choose a path by preference.
4. Preserve raw predecessor submissions, URLs, HTTP outcomes and hashes in the run artifact.
5. Respect SEC fair-access controls with an identifying User-Agent, conservative request spacing and bounded retries for 429/5xx responses.

## Reconciliation

For each current/predecessor pair, validate:
- exact accession and 13D-vs-13G family;
- predecessor SEC-header subject CIK and filer CIK against the current filing's header roles;
- predecessor filing date strictly earlier than current filing date;
- XML issuer/filer CIKs against SEC-header roles where structured XML exists;
- CUSIP equality where both sides expose a valid nine-character CUSIP; otherwise use exact normalized class-title equality only as weaker evidence;
- 13D `reportingPersonInfo` and 13G `coverPageHeaderReportingPersonDetails` separately, comparing names and per-person ownership fields without summing overlapping group members.

Legacy HTML predecessors receive only a conservative CUSIP/class-title probe. Failure to parse a legacy reporting-person table is **not** evidence that the person or position was absent. Such cases remain limited/uncertain.

## Interpretation and hard stops

- A header/accession/form/CIK/date mismatch is a lineage conflict.
- A CUSIP mismatch is a security conflict requiring quarantine or manual identity review, not an automatic claim of a bad filing.
- A class-title-only match is weaker than CUSIP and must remain explicitly labelled.
- SEC acceptance time is not independently proven public dissemination time. Use the next regular trading session after acceptance as a conservative availability convention until dissemination timing is verified.
- This sample is selected from the Phase 84 pilot and cannot establish population-wide recall or historical universe coverage.
- No forward returns, feature selection, alpha test, vendor purchase, production change or F80 modification is authorized in Phase 120.

## Reproduction

The workflow downloads the immutable Phase 84 artifact and runs:

```bash
python -m unittest -v research.test_phase120_sec_13dg_predecessor_content_audit
python research/phase120_sec_13dg_predecessor_content_audit.py \
  --phase84-dir inputs/phase84 \
  --manifest research/phase120_sec_13dg_predecessor_manifest.csv \
  --output-dir out
```

The output artifact contains raw predecessor submissions, a JSON adjudication and a row-level CSV. The live result supersedes this specification's in-progress status.
