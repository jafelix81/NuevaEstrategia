# Phase 35 — global EDGAR subject-issuer census pilot
Date: 2026-11-03
Branch: phase35-13dg-issuer-attribution-repair
Status: pre-registered feasibility pilot; no return test.

## Research question
Can the SEC's public EDGAR global quarterly index plus filing-detail metadata produce a broad, reproducible 13D/13G filing census keyed by the security's Subject CIK, rather than by the reporting entity that submitted the filing?

## Why the previous sample is invalid
The previous workflow queried submissions for 307 CIKs obtained from the frozen ticker list. SEC submissions are indexed by the entity that submitted the filing. In Schedule 13D/G, the submitting entity is commonly an investor/reporting person; the subject issuer is a separate company. The previous 20,266-row artifact therefore represents filings made by the queried CIKs, not all filings about those CIKs. The TFC/Truist/Federated record is a direct counterexample: TFC CIK 0000092230 is the reporting entity, while Federated Hermes ETF Trust CIK 0001849998 is the subject issuer.

SEC filing-detail pages explicitly expose Filed by and Subject CIK/name separately. See the SEC examples:
- FMR LLC (Filed by) / Sandisk Corp (Subject): https://www.sec.gov/Archives/edgar/data/315066/000031506625000987/0000315066-25-000987-index.html
- Truist Financial Corp (Filed by) / Federated Hermes ETF Trust (Subject): https://www.sec.gov/Archives/edgar/data/92230/000009223025000138/0000092230-25-000138-index.htm

## Data source and method
1. Download the SEC quarterly global master.idx.
2. Parse its pipe-delimited CIK, company name, form type, filing date and filename.
3. Keep only SC 13D, SC 13D/A, SC 13G and SC 13G/A.
4. Treat the master-index CIK as filer/submitting CIK only.
5. For each accession, fetch its SEC filing-detail index page and parse Filed-by CIK/name and Subject CIK/name.
6. Filter on Subject CIK using the frozen 335-name universe's current CIK candidates. This mapping is only a feasibility candidate list, not historical membership.
7. Retain the accepted timestamp separately. Filing date remains the conservative KnowledgeDate; no same-day signal is assumed.
8. Where structured XML is available, independently parse issuerInfo/issuerCik or issuerCIK and compare it with the index Subject CIK. Quarantine disagreements.
9. Do not infer economic groups from filer CIK, accession prefix, names, or a reporting-person set hash.

## Pilot scope and validation
- Quarter: 2025Q1.
- Fixed validation accession: 0000092230-25-000015.
- Expected Filed-by CIK: 0000092230.
- Expected Subject CIK: 0001849998.
- Minimum Subject CIK parse coverage: 95% of all candidate 13D/G filing index pages.
- Report candidate filings by form, index fetch errors, Subject CIK coverage, Filed-by CIK coverage, target-subject filings, target-filer filings, filer=subject cases, and known-fixture result.
- The 95% threshold is a data-quality gate only, not an economic or alpha threshold.

## Historical extension
If the pilot passes, expand quarter-by-quarter to the earliest usable EDGAR full-index history (1993 archive onward where available). Do not claim a true first event unless predecessor history is sufficiently complete. Use exact previousAccessionNumber links for structured amendments; legacy links require explicit deterministic evidence. Otherwise mark the chain left-censored.

## Remaining gates after pilot
- Reconcile subject CIK from filing index against XML issuer CIK.
- Deduplicate accession records across any alternate archive paths.
- Build historical ticker/CIK/security-class crosswalk with PIT-effective dates, including renamed, delisted and predecessor securities.
- Reconstruct reporting persons, group markers, joint-filing evidence and ownership states without treating a filer as an economic group.
- Quantify left-censoring and predecessor-chain completeness by form/year.
- Only after those gates, preregister separate 13D and 13G incremental tests versus frozen F80/LTM with identical exposure/costs, chronological OOS, block bootstrap, issuer clustering and LOO.

## Explicit exclusions
- No forward returns, no announcement-window test, no horizon or threshold selection.
- No use of event_date as KnowledgeDate.
- No assumption that 13D is activist or 13G is passive/informed without evidence.
- No modification of F80_TOP20_PARTIAL50_BASELINE_C20.
- No use of the old 20,266-row artifact for issuer coverage, event counts or alpha.

## Files
- research/phase35_13dg_parser_v3.py
- research/test_phase35_13dg_parser_v3.py
- research/phase35_global_subject_census_pilot.py
- PHASE35_13DG_EVENT_NORMALIZATION_SPEC.md
