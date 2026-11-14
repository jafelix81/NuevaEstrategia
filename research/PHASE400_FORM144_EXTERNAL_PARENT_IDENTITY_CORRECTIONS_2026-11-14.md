# Phase 400 — Form 144 external amendment-parent identity corrections

**Audit date:** 2026-11-14  
**Disposition:** all three previously unretrieved Form 144 parent XML documents were recovered from SEC EDGAR. In every case, the original parent XML names a different issuer CIK than the linked 144/A. The 144/A carries the corrected issuer identity. This is a material point-in-time identity issue, not three additional sale events.

## 1. Executive result

The Phase 398 census had three unresolved parent accessions:

- Wells Fargo: outside the 14-quarter accession census.
- General Mills: present in the broader accession census but absent from the candidate issuer-event panel.
- Baker Hughes: present in the broader accession census but absent from the candidate issuer-event panel.

Targeted SEC EDGAR primary XML retrieval recovered all three original parent documents. All three parent-to-amendment links are explicit through the child's \`previousAccessionNumber\` field.

| Issuer target | Parent issuer CIK | Corrected issuer CIK | Filer CIK | Result |
|---|---:|---:|---:|---|
| WFC | 0000740906 | 0000072971 | 0001766264 | Wells Fargo Bank N.A. -> Wells Fargo & Company |
| GIS | 0001635007 | 0000040704 | 0001318751 | Mason Investment Advisory Services -> General Mills Inc. |
| BKR | 0000808362 | 0001701605 | 0001742205 | Baker Hughes Holdings LLC -> Baker Hughes Co |

The filer CIK is unchanged in all three pairs. The issuer CIK changes in all three. Proposed sale units and aggregate proposed value are unchanged in all three. The raw outstanding-share field changes in one pair (GIS), reinforcing that it is not a stable economic denominator.

This is a targeted set of three previously unmatched parent records, not a random sample. Do not interpret 3/3 as the prevalence of issuer-identity corrections across all Form 144/A filings.

## 2. Pair-level findings

### WFC — Wells Fargo Bank N.A. corrected to Wells Fargo & Company

- Parent: accession 0001766264-23-000002; issuer CIK 0000740906; issuer name Wells Fargo Bank N A; SEC file number 028-01341; security class "regular shares".
- Amendment: accession 0001766264-23-000004; explicit previousAccessionNumber 0001766264-23-000002; issuer CIK 0000072971; issuer name WELLS FARGO & COMPANY/MN; SEC file number 001-02979; security class "common".
- Filer CIK remains 0001766264; seller is Lester Owens.
- Proposed units remain 91,383 and proposed aggregate value remains $3,516,874. The raw outstanding field remains 582,647. Approximate sale date changes from 04/14/2023 to 04/17/2023.
- The parent is not the public common-stock issuer named by the corrected amendment. Do not map the parent to WFC using the child CIK retroactively.

SEC XML:
- Parent: https://www.sec.gov/Archives/edgar/data/740906/000176626423000002/primary_doc.xml
- Amendment: https://www.sec.gov/Archives/edgar/data/72971/000176626423000004/primary_doc.xml

### GIS — Mason Investment Advisory Services corrected to General Mills Inc.

- Parent: accession 0001318751-23-000002; issuer CIK 0001635007; issuer name Mason Investment Advisory Services, Inc.; SEC file number 150-05248; security class "General Mills Common Stock".
- Amendment: accession 0001318751-23-000003; explicit previousAccessionNumber 0001318751-23-000002; issuer CIK 0000040704; issuer name GENERAL MILLS INC; SEC file number 001-01185; security class "General Common Stock".
- Filer CIK remains 0001318751; seller is David Cordani.
- Proposed units remain 8,675 and proposed aggregate value remains $785,608. The raw outstanding field changes from 587,500,000 to 587,350,000. The acquisition-lot amount also changes from 14,251 to 8,675.
- The original issuer CIK identifies an investment adviser, while the security class refers to General Mills. The issuer-specific event must remain unresolved/conflicted until the amendment corrects the issuer identity.

SEC XML:
- Parent: https://www.sec.gov/Archives/edgar/data/1318751/000131875123000002/primary_doc.xml
- Amendment: https://www.sec.gov/Archives/edgar/data/1318751/000131875123000003/primary_doc.xml

### BKR — Baker Hughes Holdings LLC corrected to Baker Hughes Co.

- Parent: accession 0001959173-23-003484; issuer CIK 0000808362; issuer name Baker Hughes Holdings LLC; SEC file number 001-09397; security class "Class A".
- Amendment: accession 0001959173-23-003500; explicit previousAccessionNumber 0001959173-23-003484; issuer CIK 0001701605; issuer name Baker Hughes Co; SEC file number 001-38143.
- Filer CIK remains 0001742205; seller is Regina Jones.
- Proposed units remain 10,000, proposed aggregate value remains $351,900, and the raw outstanding field remains 1,009,653,944.
- The amendment remarks explicitly state that the issuer name and SEC file number were corrected.

SEC XML:
- Parent: https://www.sec.gov/Archives/edgar/data/808362/000195917323003484/primary_doc.xml
- Amendment: https://www.sec.gov/Archives/edgar/data/1701605/000195917323003500/primary_doc.xml

## 3. Reconciliation with the Phase 67 / Phase 398 panel

The Phase 67 artifact contains 21,634 issuer-event rows and 196 Form 144/A rows. Its summary says only rows whose XML issuerCik belongs to the current candidate CIK set enter issuer_event_raw.csv.

The Phase 398 parent reconciliation was:
- 193 parent rows matched inside issuer_event_raw.csv.
- Two parent accessions were in the broader 14-quarter accession census but not in the candidate issuer-event panel.
- One parent was outside/missing from that census.

Phase 400 now recovers all three external parent XMLs. The 193 in-panel parent-child pairs still have zero issuer-CIK changes; 16 have issuer-name text differences. That result applies only to the 193 pairs where both records were already in the candidate panel. It does not validate the three external parents.

The mechanism is now clear for these exceptions: the original parent issuer CIK did not match the current candidate CIK set, so the parent was excluded from the issuer-event panel. The amendment's corrected issuer CIK did match and was included. A current-issuer CIK filter therefore creates a selective blind spot for amendments that repair issuer identity.

## 4. Point-in-time feature policy

For a parent whose XML issuer CIK conflicts with the actual security issuer later stated in a 144/A:

1. Preserve the original Form 144 as the root proposed-sale event version.
2. Keep its original issuer CIK/name/file number exactly as filed; label issuer attribution conflicted/unresolved.
3. Do not attach the corrected issuer CIK or ticker to the parent date.
4. Treat the 144/A as a new version of the same proposed-sale order, not an independent sale.
5. The corrected issuer identity first becomes available on the amendment filing date. For a daily equity feature, use no earlier than the first regular NYSE session strictly after that amendment filing date.
6. Keep every original and amended payload/version; do not overwrite the parent.
7. If the amendment also changes units, proposed value, outstanding field, security class, broker, exchange or approximate sale date, each changed value is known only from the amendment's own filing date.

This is intentionally conservative. It prevents the current corrected issuer identity from leaking into a backtest at the earlier parent timestamp. It does not establish that the proposed sale was executed.

## 5. Research consequences

- Phase 400 resolves the three external parent documents and closes the specific parent-retrieval task from Phase 398.
- The Form 144 ingestion design needs an explicit versioned issuer-identity state, separate from filer identity and security-class identity.
- Candidate-CIK filtering must not silently discard a parent and then treat its amendment as a complete standalone event. Retain the amendment link and mark the parent as an external/unmatched root.
- A broader audit is still needed to estimate how often issuer identity is corrected outside the candidate panel. The three cases are selected exceptions and cannot estimate population prevalence.
- The noOfUnitsOutstanding field remains killed as a denominator/feature; Phase 400 does not rehabilitate it.
- Historical F80 security identity, delisted/predecessor coverage, independent prices/volume and the conservative PIT clock remain unpassed.

## 6. Reproducibility and controls

- Input: Phase 400 curated parent-child evidence JSON, with direct SEC primary XML URLs.
- Script: \`research/phase400_form144_external_parent_identity_audit.py\`.
- Tests: \`research/test_phase400_form144_external_parent_identity_audit.py\`.
- Command: \`python research/phase400_form144_external_parent_identity_audit.py\`.
- Offline only; no SEC crawler, price download, return calculation, vendor call or data purchase.
- No alpha/OOS/bootstrap/LOO/holdout test.
- F80_TOP20_PARTIAL50_BASELINE_C20, universe, capital, exposure, parameters and production remain unchanged.
