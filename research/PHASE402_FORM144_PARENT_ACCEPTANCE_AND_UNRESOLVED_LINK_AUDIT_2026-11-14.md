# Phase 402 — Form 144 parent recovery and acceptance-time audit

**Status: targeted audit executed; archived with explicit unresolved records.** Research-only; no return calculations or signal authorization.

## Frozen scope and reproducibility

- Phase 401 source run: [43626453375](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43626453375).
- Frozen Phase 401 artifact: 14126667342; ZIP SHA-256: 6ce994213e507d6c0637162c520b003bb7e2a239b922f2a13cc24aaadd5d011c.
- Phase 402 run: [43632820744](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43632820744).
- Phase 402 artifact: 14129225020; ZIP SHA-256: 24a24b8cad6b37091863168a149cc33c5ec79f70814c6e65f3ad3e7a1c55e477.
- Artifact files: documents.csv, pair_audit.csv, quarter_index_search.csv, daily_index_search.csv, summary.json.
- Scope is immutable: four candidate-boundary transitions and four Phase 401 unresolved parent links. No second full-market census and no duplicate Form 144 → Form 4 linkage study.

## Retrieval result

| Measure | Result |
|---|---:|
| Parent/child pairs audited | 8/8 |
| Expected XML documents | 16 |
| XML documents retrieved | 14/16 (87.5%) |
| Parent XMLs retrieved | 6/8 (75.0%) |
| Acceptance timestamps found | 14/16 (87.5%) |
| Acceptance timestamps among retrieved XMLs | 14/14 (100%) |
| Candidate-boundary pairs fully recovered | 4/4 |
| Previously unresolved pairs fully recovered | 2/4 |
| Parent/child filing-date inversions | 0 |
| Parent/child acceptance-order inversions | 0 |
| Child previousAccessionNumber matches | 8/8 |

The 90% acceptance-time coverage gate remains failed because two expected parent documents and their acceptance times remain unavailable. The 100% figure among retrieved documents must not replace the 87.5% full-scope coverage.

## Candidate-boundary transitions

All four pairs now have both XML versions and both acceptance timestamps.

| Pair | Parent issuer → child issuer | Acceptance order (ET) | Interpretation |
|---|---|---|---|
| WFC, 2023-04 | Wells Fargo Bank N.A. (CIK 740906) → Wells Fargo & Company (CIK 72971) | Apr 10 11:39:15 → Apr 14 12:24:45 | Issuer-CIK boundary change; no explicit correction remark. Do not automatically call this a correction. |
| GIS, 2023-05 | Mason Investment Advisory Services (CIK 1635007) → General Mills (CIK 40704) | May 17 10:35:56 → May 17 12:29:58 | Issuer-CIK boundary change while security-class text refers to General Mills; no explicit correction remark. Preserve as ambiguous. |
| BKR, 2023-08 | Baker Hughes Holdings LLC (CIK 808362) → Baker Hughes Co. (CIK 1701605) | Aug 24 10:59:26 → Aug 24 15:02:25 | Child explicitly says issuer name and SEC file number were corrected. |
| Teradyne / Weatherford, 2025-12 | Teradyne (CIK 97210) → Weatherford International (CIK 1603923) | Dec 5 10:28:07 → Dec 5 12:03:06 | Child explicitly says issuer name was corrected. |

All four parent acceptance timestamps precede their child timestamps. Acceptance-time ordering is useful for version chronology only; it does not authorize intraday use.

## Two previously unresolved pairs recovered

### Music Licensing, Inc.

- Parent 0001213900-23-013351, Form 144, filed Feb 21, 2023; accepted Feb 21 at 17:27:00 ET.
- Child 0001213900-23-042097, Form 144/A, filed May 22, 2023; accepted May 22 at 19:00:17 ET.
- Issuer CIK is stable at 0001671132; filer CIK is stable at 0001777732.
- Seller text changes from “Noch Jake P.” to “Jake P. Noch”. Treat as a name-order variation pending controlled person-identity normalization, not as a new seller or a proven identity change.
- Parent remarks mention that several brokers had not yet cleared or approved deposits pending compliance review. This is descriptive context, not evidence of execution or predictive value.

### A10 Networks

- Parent 0001570462-23-000002, Form 144, accepted Mar 14, 2023 at 21:32:12 ET; filing date Mar 15.
- Child 0001580808-24-000063, Form 144/A, accepted Apr 23, 2024 at 16:15:53 ET.
- Issuer CIK remains 0001580808; filer CIK remains 0001570462.
- Seller changes from Brian Becker to Dhrupad Trivedi.
- The amendment expressly states that the original Form 144 incorrectly stated the name of the person for whose account the securities were to be sold.

**This is a confirmed seller-identity correction, not an issuer correction.** Preserve Brian Becker as the identity stated in the original version until the amendment's own availability date; only then recognize Dhrupad Trivedi. Do not backdate the corrected seller. This is the clearest new identity finding from Phase 402.

## Two parent documents remain unresolved

### Freightos Ltd — parent 0001976408-23-000153

- Child 0001976408-23-000167 was recovered as Form 144/A, filed and accepted Dec 5, 2023 at 09:30:31 ET.
- Child XML identifies Freightos Ltd (issuer CIK 0001927719), filer CIK 0001976386, seller Eytan Buchman, and references the missing parent accession.
- Parent was not found in the targeted quarterly or daily index searches; tested parent archive paths returned 404.
- **Disposition:** unresolved. Do not infer deletion, acceptance, original seller details, or parent filing date from the child alone.

### Legacy Housing Corp — parent 0001000275-24-000021

- Parent appears in the March 11, 2024 daily master index as Form 144, filer/path CIK 0001437795, company-name field “Hodgson Curtis Drew”.
- It is absent from the current 2024Q1 quarterly master index, and the indexed archive path, filing-detail pages, complete-submission path, and primary XML attempts returned 404.
- Child 0001000275-24-000022 was recovered as Form 144/A, filed Mar 12 and accepted at 10:04:50 ET. It identifies Legacy Housing Corp (issuer CIK 0001436208) and seller Hodgson Curtis Drew; it references the missing parent.
- SEC documentation says post-acceptance removals processed on later business days are not reflected in prior daily/feed/oldload indexes, while quarterly indexes are rebuilt to incorporate post-acceptance corrections/deletions. The daily-index-only footprint plus current archive 404 is **consistent with** a post-acceptance removal/correction, but the specific cause is not proven.
- **Disposition:** unresolved and excluded from pair-level payload comparison. A recovered daily-index row is not a recovered filing document.

## Acceptance-time and PIT interpretation

The SEC Form 144 electronic-filing guide states that, under the electronic Form 144 regime, submissions accepted 6 a.m.–10 p.m. ET on business days are deemed filed and publicly disseminated the same business day. The extension from 5:30 p.m. to 10 p.m. became effective March 20, 2023; electronic filing for covered Forms 144 began April 13, 2023.

Sources:
- [SEC — File Form 144 Electronically](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically)
- [SEC — Announcement extending EDGAR filing hours](https://www.sec.gov/newsroom/whats-new/edgar-extension-144-030323)
- [SEC — Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
- [SEC — Webmaster FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions)

The SEC also says there is no timestamp certifying exact first-public availability; availability is often 1–3 minutes after acceptance, can be longer, and is not guaranteed. Therefore:
- ACCEPTANCE-DATETIME is a version-ordering field, not first-public receipt.
- The existing date-level next-regular-session rule remains a conservative baseline for this research, not a certified intraday timestamp.
- No same-day or intraday strategy use is authorized.
- A prospective Latest Filings/RSS/PDS first-seen ledger remains necessary to validate actual receipt and delay tails.
- Never backdate issuer, seller, or tranche corrections.

## Instrumentation note

The run's daily_index_parent_hits=1 correctly counts one parent accession found in the daily index. The accompanying daily_index_parent_rows array currently contains all three target accessions found in daily indexes (including two child accessions); treat the array as target-index evidence, not as three parent recoveries. The row-level pair_audit.csv is authoritative for parent status.

## Decision and remaining gates

- Phase 402 is archived as **completed with explicit unresolved links**, not as a clean 100% recovery.
- Historical F80 membership/effective-dated security identity remains unproven.
- Complete seller/person identity normalization remains necessary.
- First-public-receipt is not certified.
- No forward returns, alpha, OOS, bootstrap, LOO, or holdout test was run.
- No Smart Money signal is admitted.
- noOfUnitsOutstanding remains killed as a denominator/feature; raw values only for version comparison.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; no capital, exposure, universe, parameter, or production changes.
- No vendor contacted and no data purchased.

## Next targeted step

Do not repeat the eight-pair retrieval. Investigate only the two remaining parents through SEC retained dissemination/oldload evidence where feasible, and separately add prospective SEC first-seen capture. If parent contents remain unavailable, preserve them as unresolved and proceed only with the fully documented subset after historical F80/security-identity gates are met.
