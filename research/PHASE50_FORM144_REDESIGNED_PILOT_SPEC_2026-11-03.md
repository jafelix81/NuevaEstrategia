# Phase 50 — Form 144 redesigned feasibility pilot v2

**Status:** implementation and parser tests added; empirical run pending.  
**Scope:** SEC Form 144 and 144/A for the frozen 335-name candidate universe, 2023-04-13 through 2026-11-03.  
**No forward returns or alpha tests are authorized.**

## Why the previous pilot is not usable

The prior implementation queried one CIK at a time, only requested one hit, used the accession prefix as the sole archive-directory CIK, and accepted a narrow XML-root regex. The completed run 40961563763 reported 132 HTTP 403 query errors, only 6 successful downloads in its 25-document sample, and zero presence for several fields. Its own logs show that some filing-detail pages were retrieved and XML links were found, but the downloaded XML was rejected by the old root/tag checks. Thus its apparent 54.8% hit rate is not an issuer-coverage estimate and its zero field rates are not evidence that the data fields are absent.

A further identity issue must remain explicit: Form 144 is filed by the selling security holder, not the issuer. EFTS CIK hits are candidate links only. The XML issuerCik is the subject issuer; the XML filer CIK, accession prefix and archive-path CIK are separate identifiers.

## Source facts and limits

The SEC Form 144 record is a notice concerning a proposed sale of restricted or control securities under Rule 144. It is not a record of every insider sale, and it does not prove execution. The electronic-filing population for securities of Exchange Act reporting issuers becomes substantially complete from 2023-04-13; earlier paper filings make historical coverage incomplete. Non-reporting issuers may still use paper filings.

The structured XML schema uses root edgarSubmission, with:
- headerData/filerInfo/filer/filerCredentials/cik for filer identity;
- headerData/submissionType and optional previousAccessionNumber;
- formData/issuerInfo/issuerCik and issuerName for subject identity;
- seller name and relationship fields;
- securitiesInformation for class, proposed units, aggregate market value and approximate sale date;
- one or more securitiesToBeSold tranches for acquisition date/nature;
- noticeSignature/noticeDate.

Form 144/A is an amendment that references the original filing; it must not be counted as an independent new sale event without lineage consolidation.

Schema/coverage cross-check: [Form 144 Files Dataset documentation](https://sec-api.io/datasets/form-144-files). This is third-party documentation, not an assumed licensed data feed. It reports 285,638 filings from 1996, but notes incomplete pre-2023 coverage because paper filing was permitted. Actual research ingestion remains based on public SEC EDGAR filings.

## v2 design

1. Keep the 335-name candidate universe and current SEC ticker/CIK mapping as a discovery aid only; current mapping is not PIT historical membership.
2. Query EFTS for both 144 and 144/A with a sequential, rate-limited request pattern. Preserve all result pages up to the SEC endpoint's 10,000-result ceiling and flag any capped query.
3. Treat each EFTS CIK result as a candidate association, not a subject match.
4. Resolve archive paths by trying CIKs present in EFTS metadata, then the accession prefix as a fallback. Never assume accession prefix equals archive-path CIK.
5. Parse raw primary_doc.xml using XML local names and the actual edgarSubmission schema.
6. Verify target subject identity only when XML issuerCik matches one of the CIKs that generated the candidate hit. Preserve XML filer CIK and archive-path CIK separately.
7. Retain the raw accepted timestamp from the SEC filing-detail index when available. If unavailable, use filing date conservatively and make the signal available no earlier than the next session.
8. Treat approxSaleDate as an event attribute, never KnowledgeDate. A sale date before filing is flagged sale_date_precedes_filing; it is not assumed to be a prospective planned-supply observation.
9. Preserve previousAccessionNumber for 144/A as a pointer to the original notice. Do not infer sequential amendment edges or count an amendment as an independent economic event.
10. Sample original notices and amendments deterministically, with issuer-level caps, and publish every exclusion/error.

## Pre-registered feasibility gates

- At least 300 current CIK mappings.
- At least 25 sampled filings.
- Zero EFTS query errors.
- No CIK query silently capped at 10,000 results.
- At least 95% sample XML parse success.
- At least 95% of parsed sample records have issuerCik matching one of the CIKs that generated the candidate hit.
- At least 95% accepted-timestamp coverage in the sample.
- At least 95% agreement between EFTS form and XML submissionType.
- At least 95% presence for the required issuer, seller, class, quantity, market-value, approximate-sale-date and notice-date fields.

These are data-quality gates, not evidence of predictive value. A pass does not certify historical active-universe membership, all-filing coverage, seller/group continuity, actual execution, or alpha.

## Next gates after a v2 pass

- Reconcile sample and full candidate accession counts against SEC filing-index Subject/Reporting metadata.
- Validate the parser on independent quarters and both 144/144-A.
- Build PIT issuer/security identity and historical F80 membership.
- Reconstruct original/amendment chains and deduplicate restated notices.
- Separate notices by seller relationship (director, officer, 10% owner, other), security class, size relative to float/ADTV, prior-sales disclosures and 10b5-1 plan status where reliably available.
- Only then pre-register a test of whether planned-sale intensity adds information beyond Form 4 and frozen LTM/F80. Control for price run-up/return-chasing, earnings windows, vesting/option exercises, and repeated seller/issuer clusters.
- Compare against the frozen control with identical exposure/costs, chronological OOS, block bootstrap, issuer-clustered uncertainty and LOO.

**Current decision:** conditional source, no alpha authorized. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
