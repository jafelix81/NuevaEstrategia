# Phase 50 — SEC Form 144 feasibility review

**Date:** 2026-11-04  
**Latest run inspected:** [40961563763](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40961563763), job `123755365019`, artifact `12936426126`. No Phase 50 workflow is currently running; the two recorded runs (40948690009 and 40961563763) both failed.

## What the failed pilot actually establishes

The artifact reports 301/335 current CIK mappings, 165 issuer hits, 132 HTTP 403 query errors and four successful queries with no hit. The apparent 54.8% hit rate (165/301) is therefore a **lower bound with 132 unresolved queries**, not a valid coverage estimate. Among the 169 queries that returned successfully, 165 had a hit (97.6%).

The 25-issuer XML sample had only six successful downloads. The field audit reported zero coverage for security title, shares to be sold, acquisition date and nature of acquisition. Those zeros are parser false negatives: the SEC XML uses tags such as `securitiesClassTitle`, `noOfUnitsSold`, `acquiredDate` and `natureOfAcquisitionTransaction`, not the patterns used by the pilot.

The archive resolver also assumes that the first ten digits of the accession are the archive-path CIK. That is not reliable for Form 144. For example, the SEC accession `0001213900-26-082095` is archived under CIK `1290008`; its XML separately identifies filer CIK `0001290008` and subject issuer CIK `0001879248`. Another SEC filing with accession prefix `0001493152` is archived under filer CIK `2025276`. See the actual [SEC XML example 1](https://www.sec.gov/Archives/edgar/data/1290008/000121390026082095/primary_doc.xml) and [SEC XML example 2](https://www.sec.gov/Archives/edgar/data/2025276/000149315226000279/primary_doc.xml).

## PIT/economic caveat

Form 144 is a notice concerning a proposed sale, not proof that the proposed sale occurred. The filing can also be retrospective or late: an SEC Form 144 filed on 2026-05-11 states that the sale had already been executed on 2026-04-06 ([SEC XML](https://www.sec.gov/Archives/edgar/data/1318484/000110465926058404/primary_doc.xml)). Therefore:
- KnowledgeDate must be the SEC acceptance timestamp (or conservatively filing date with next-session use).
- `approxSaleDate` is an event attribute, never KnowledgeDate.
- Notices where the sale date precedes filing/acceptance must be classified as retrospective and excluded from a prospective planned-supply feature.
- Include 144/A and reconstruct its prior-filing reference before counting unique notices.

## Decision

**Conditional / not killed / no alpha authorized.** The failed run does not establish that Form 144 lacks coverage. It establishes that the pilot is not yet valid because 132 queries were blocked and the archive/field parser is incomplete. A redesigned audit must resolve archive paths from the SEC filing index/CIK metadata, parse the actual XML tags, batch or rate-limit EFTS queries, include 144/A, and separately measure prospective versus retrospective notices. No forward returns were used.
