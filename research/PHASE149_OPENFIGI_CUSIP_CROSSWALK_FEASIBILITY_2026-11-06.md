# Phase 149 — OpenFIGI CUSIP-to-FIGI crosswalk feasibility

**Date:** 2026-11-06  
**Status:** complete — present-day identity mapping only  
**Scope:** 553 checksum-valid CUSIPs from the Phase 124/127 stratified 13D/13G sample. No return test, no purchase, no vendor contact, no production change.

## Question

Can OpenFIGI provide a sufficiently complete and stable identifier bridge from CUSIPs disclosed in SEC Schedule 13D/13G filings to FIGI/share-class identifiers, including older or delisted securities?

## Immutable input and provenance

- Phase 124 sample: run 42073725379, artifact 13436764625, SHA-256 85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc.
- Phase 127 corrected CUSIP sample: run 42079517644, artifact 13438903901, ZIP SHA-256 b80d15d736ba6c45f4f3c5dd569604175e221414b31a28fd58a62010a805c166.
- Phase 127 CSV SHA-256: 5fc30ba22d4e3ef99113761059a5761f1fd4ae61a6d0e3a69961fe194d739447.
- Population: 599 actual 13D/13G filings after index-alias quarantine; 571 checksum-valid CUSIP rows; 553 distinct CUSIPs.
- Input JSON SHA-256: 5c97aced36060bb89dafb57ba8e07f3487865ec5c5d6ce064aa285d50f3b90fb.

The earlier SEC header subject CIK/name fields remain provenance only. Phase 126 found legacy header subject/issuer discrepancies, so they are not treated as ground truth.

## API and reproducibility

OpenFIGI's public v3 mapping API accepts ID_CUSIP and ID_CUSIP_8_CHR. The audit used includeUnlistedEquities=true. Its documentation states that this includes unlisted and delisted equities, and that a FIGI, once issued to an instrument, does not change. The response fields include FIGI, ticker, name, exchange, shareClassFIGI and compositeFIGI.

The unauthenticated mapping limit is 25 requests per 60 seconds and 10 jobs per request. The audit made 68 requests: 56 exact 9-character batches and 12 8-character fallback batches, sequentially with a 2.5-second minimum interval. All 68 returned HTTP 200 on the first attempt; no 429 or API-level errors occurred. The lowest observed ratelimit-remaining header was 2.

Sources:
- https://www.openfigi.com/api/documentation
- https://www.openfigi.com/about/faq

OpenFIGI states that FIGI symbology is free to use and redistribute. The API does not return third-party proprietary identifiers; this audit supplies CUSIPs from the SEC filing sample and retains the returned FIGI metadata.

## Results

### Exact 9-character CUSIP mapping

| Result | CUSIPs |
|---|---:|
| One shareClassFIGI | 430 |
| One compositeFIGI only | 2 |
| One FIGI only | 4 |
| Multiple compositeFIGIs only — unresolved | 2 |
| No match | 115 |
| API errors | 0 |
| **Total** | **553** |

The four FIGI-only results are not all common stocks: three map to municipal instruments and one to preferred stock. The exact pass found 370 common-stock matches and 434 Equity-sector matches.

### 8-character fallback

The 115 exact-CUSIP no-matches were retried using ID_CUSIP_8_CHR and the first eight characters only.

| Result | CUSIPs |
|---|---:|
| One shareClassFIGI recovered | 6 |
| No match remains | 109 |
| Multiple/unstable fallback identities | 0 |
| API errors | 0 |

Five of the six fallback recoveries have a Common Stock classification; one is a REIT. The fallback therefore improves total mapped CUSIPs from 438/553 (79.2%) to 444/553 (80.3%), a gain of only 1.1 percentage points. It does not solve the remaining identity gap.

### Consolidated interpretation

- 444 CUSIPs return at least one mapping (80.3%).
- 442 CUSIPs have one identifier at the strongest available level: 436 with one shareClassFIGI (430 exact + 6 fallback), two with one compositeFIGI only, and four with one FIGI only.
- Two additional CUSIPs return multiple compositeFIGIs but no shareClassFIGI; they remain unresolved rather than being forced into one security.
- 109 CUSIPs remain unmatched (19.7%).
- The 436 share-class-mapped CUSIPs resolve to 435 distinct shareClassFIGIs. One shareClassFIGI links two different CUSIPs.

The cross-CUSIP link is:
- CUSIP 349915108 in a 2016-02-11 filing, with the name Fortuna Silver Mines Inc.
- CUSIP 349942102 in a 2026-02-17 filing, with the name Fortuna Mining Corp.
- Both map in the current API snapshot to shareClassFIGI BBG001S982M0.

This is a useful example of a stable share-class identifier bridging different CUSIPs and issuer names. It does not establish the effective date of the change or prove that the current mapping was knowable in 2016.

The API can return many venue-level FIGIs for one CUSIP. For example, CUSIP 00191G103 returned 132 venue FIGIs but only one shareClassFIGI. Deduplication must therefore use shareClassFIGI first, not count venue-level FIGIs as separate securities.

The 8-character fallback also illustrates the date problem: CUSIP 38983D300 maps to one shareClassFIGI but returns both Great Ajax Corp and Rithm Property Trust Inc names and multiple tickers. Without effective dates, the API cannot tell us which name/ticker applied at the filing date.

No-match cases are not confined to old HTML filings. In the stratified sample, 88 legacy-only CUSIPs, 20 XML-only CUSIPs and one CUSIP observed in both formats remain unmatched. The 8-character fallback recovered four legacy-only and two XML-only cases. The residual gap is therefore not explained solely by the legacy parser.

## Hard PIT limitations

The documented mapping response contains no issuer CIK, effective-from/effective-to dates, historical listing-status dates or first-publication timestamp for the CUSIP-to-FIGI relationship. includeUnlistedEquities=true broadens the result set but does not label which instrument is currently listed versus unlisted/delisted.

A permanent FIGI does not make a present-day CUSIP-to-FIGI lookup historically available. A current ticker or issuer name must not be backdated to the 13D/13G filing date. The 8-character fallback is preserved separately and is never silently substituted for the exact CUSIP result.

## Decision

**Keep OpenFIGI as a candidate present-day identity bridge for manual/independent validation; reject it as a standalone historical PIT security master.** The 80.3% any-match rate is useful but leaves 19.7% unresolved, and the response lacks the issuer and effective-date fields needed for a historical event-to-return join.

No 13D/13G alpha test is authorized from this crosswalk. Before such a test, obtain an independently verifiable effective-dated security master or a historical price source keyed by stable FIGI/CUSIP with delisted coverage and event-time identity. Do not use current tickers as historical identifiers.

## Execution and artifacts

- Final run: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42189666301
- Final artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42189666301/artifacts/13488819025
- Artifact ZIP SHA-256: dcf4265a19c28e822412517c5e65d72d69175e8cc762dd934f502923876d4269
- 16/16 offline regression tests passed.
- Code: research/phase149_openfigi_cusip_crosswalk_audit.py
- Input: research/phase149_cusip_input.json
- Tests: research/test_phase149_openfigi_cusip_crosswalk_audit.py
- Workflow: .github/workflows/phase149_openfigi_cusip_crosswalk_audit.yml

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No alpha was tested or demonstrated.
