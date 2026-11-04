# Phase 63 — SEC Form 144 master-index CIK-pair identity diagnostic
**Date:** 2026-11-04  
**Source artifact:** run 41793719745, artifact 13306814836 (2025Q1)  
**Status:** promising structural crosswalk; independent validation required.

## Executive finding

The failed HTML role-label parser is not the only way to identify the two entities associated with a Form 144 accession. In the 50-document XML validation sample, the two CIKs carried in the global master-index rows matched the XML's issuer CIK and filer CIK exactly in every case.

A reproducible local audit of the artifact found:

| Diagnostic | Result |
|---|---:|
| XML sample rows | 50 |
| Joined to master-index census | 50/50 |
| Master-index pair size | 2 CIKs in all 50 |
| XML issuer CIK found in pair | 50/50 |
| XML filer CIK found in pair | 50/50 |
| Issuer/filer CIKs distinct | 50/50 |
| Current candidate CIKs in pair | 9/50 |
| Exactly one candidate CIK in pair | 9 |
| Unique candidate is XML issuer | 9/9 |
| Unique candidate is XML filer | 0/9 |
| Ambiguous candidate pairs | 0 |
| Pairs with no current candidate CIK | 41 |

By form:
- Form 144: 25 XML rows; 6 pairs contained exactly one current candidate CIK; all six matched the XML issuer.
- Form 144/A: 25 XML rows; 3 pairs contained exactly one current candidate CIK; all three matched the XML issuer.

The candidate set contains 309 unique CIKs from the 335 current ticker-mapping rows. It is a current mapping, not a historical point-in-time universe.

## Why this matters

The 2025Q1 global master-index census contains 8,318 unique accessions. Earlier census diagnostics found 8,311 accessions with two CIK/name rows and seven with one. The XML sample shows that, for the 50 tested accessions, those two master-index CIKs correspond to the XML's issuer and filer, even though the master-index rows themselves are not role-labelled.

This suggests a more efficient subject-issuer discovery path:

1. Parse the global master.idx and retain all CIK/name rows by accession.
2. Intersect each accession's CIK pair with the current candidate CIK set.
3. If exactly one candidate appears, treat it only as a *candidate subject*, not a confirmed issuer.
4. Fetch the primary XML for every candidate accession and confirm `issuerCik` against the candidate CIK.
5. Fetch filing-detail pages only for confirmed target issuers (and a stratified non-target validation sample) to obtain Accepted timestamps and independently check role metadata.
6. If two candidate CIKs appear, or only one master-index CIK exists, classify the accession as ambiguous/unresolved until XML or another deterministic source resolves it.

This could avoid fetching every filing-detail page in the global census. It also avoids relying on the current HTML role-label parser for the first-stage candidate discovery. The filing-detail page remains useful for the Accepted timestamp, which the previous pilot extracted successfully.

## Important limits

- The 50-row XML sample is not a random or representative coverage sample. The 9/9 candidate-to-issuer match is not a universal precision estimate.
- A reporting person may itself be a public company, fund, trust or another CIK in the candidate set. Such cases can produce two candidate CIKs and must remain ambiguous; never infer subject from row order.
- Seven accessions in the global census have only one master-index CIK row. They cannot be resolved by a two-CIK pair rule alone.
- The candidate ticker-to-CIK mapping is current, not PIT. It does not establish historical F80 membership, listing status, ticker continuity or delisted issuer coverage.
- The XML sample covers 2025Q1 only. The crosswalk must be tested across independent quarters, both original and amendment forms, cases with zero/one/two candidate CIKs, corporate reporting persons, trusts/funds, and unusual filing structures.
- XML issuer/filer CIKs are identity fields; they do not establish that a Form 144 notice resulted in a completed sale or that the filing predicts returns.

## Reproducible audit

Added:
- `research/phase63_form144_master_index_pair_crosswalk_audit.py`
- `research/test_phase63_form144_master_index_pair_crosswalk_audit.py`

The script reads the global-index census, XML sample and ticker-CIK candidate CSVs; it preserves issuer and filer as separate roles and reports candidate-pair ambiguity rather than forcing an assignment. Six unit tests passed locally. Running the script against the downloaded artifact produced the table above.

## Phase 50 workflow status

- Run 41793719745 (run 6) completed with failure after fetching the 9,104 detail pages without HTTP errors. Artifact 13306814836 contains 50 XML sample rows. The HTML parser still extracted zero Subject/Reporting CIKs, so the page-role identity gate failed.
- Run 41793724389 (run 7, commit 5001cb1) remains `in_progress`; job 126477286538 passed the parser/PIT test step and is still in the 2025Q1 global-index pilot step. No artifact was available at the time of this audit.
- No duplicate Phase 50 run was launched. Do not dispatch another run while run 7 remains active.

## Decision

Retain the master-index pair crosswalk as a high-priority Phase 50 redesign candidate. Do not use it as a production subject-issuer classifier until it passes independent-quarter and ambiguity tests. No event counts, sale-completion inference, forward returns or alpha tests are authorized by this diagnostic. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
