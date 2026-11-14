# Phase 401 — Full-market SEC Form 144/A parent-identity census

**Status:** completed and merged via PR #78. Corrected live run 43626453375 passed both offline regression (13 tests) and the full SEC census. Artifact 14126667342 (SHA-256 `6ce994213e507d6c0637162c520b003bb7e2a239b922f2a13cc24aaadd5d011c`). Research-only; no return calculations.

## Scope correction

The initial Phase 401 draft incorrectly described **56,167 accessions / 609 amendments** as the Phase 67 baseline. Those values do not match the frozen Phase 67 artifact and were invalid predeclared targets.

Reconciliation against Phase 67 run 41828179718 / artifact 13334881835 (SHA-256 `939d5564b14ce0f41df23a2c9ab681977cfde141cd0ea2b3c1213b1c5bfaf613`) gives the correct baseline for the 2023-04-13 through 2026Q3 window:

- 125,977 Form 144 / 144-A master-index accessions.
- 21,648 candidate-index accessions across the 290 frozen candidate CIKs.
- 196 candidate Form 144/A issuer events.
- The Phase 67 event panel contains 21,634 issuer events (21,438 Form 144 and 196 Form 144/A); the 14 filer-only false positives are excluded.

The Phase 401 live scan intentionally widened beyond candidate issuers to all **1,446 SEC-wide Form 144/A child filings** in the same date window. This is the correct all-market count observed in the live master-index retrieval, not 609. Candidate membership is evaluated from the exact 290-CIK snapshot and the parsed XML issuer CIK, not the filing agent.

## Initial hosted retrieval — run 43621827885

The offline regression job passed. The live SEC retrieval completed, but the workflow ended unsuccessfully because the initial script compared the full-market census to the invalid 56,167 / 609 targets. This was a validation-specification error, not an SEC retrieval failure.

Raw artifact:
- Artifact ID: 14124224348
- 1,446/1,446 child XMLs parsed; zero child XML errors.
- Child form/index match: 100%.
- Child filer + issuer CIK pair concordance: 100%.
- 1,442/1,446 parent links resolved (99.723%); four unresolved links are retained explicitly.
- Parent XML fetch errors: zero; the four unresolved parents were outside the indexed/curated lookup set.
- Parent form match and CIK-pair concordance: 100% among resolved parents.
- No parent/child filing-date inversions among resolved links with comparable dates.
- No duplicate accession rows.

The corrected gates now separately reconcile the 125,977 Phase 67 window accessions, 21,648 candidate-index accessions, and 196 candidate 144/A events, while reporting the 1,446 all-market child filings without falsely comparing them to a candidate-only count.

## Identity and payload findings

Across the 1,442 resolved amendment-parent pairs:

| Finding | Count |
|---|---:|
| Issuer CIK changed | 49 |
| Of those with explicit identity-correction remarks | 24 |
| Issuer name changed | 96 |
| Seller name changed | 108 |
| Proposed-sale tranche payload changed | 767 |
| Candidate-stable | 193 |
| Parent noncandidate → child candidate | 3 |
| Parent candidate → child noncandidate | 1 |
| Noncandidate → noncandidate CIK change | 45 |
| Noncandidate stable / unresolved identity | 1,200 |

The candidate-boundary rows are not automatically treated as corrections:

- Wells Fargo: parent issuer CIK 740906 (Wells Fargo Bank N.A.) → child 72971 (Wells Fargo & Company); no explicit correction remark.
- General Mills: parent issuer CIK 1635007 (Mason Investment Advisory Services) → child 40704 (General Mills); no explicit correction remark.
- Baker Hughes: parent 808362 (Baker Hughes Holdings LLC) → child 1701605 (Baker Hughes Co.); the child explicitly says the issuer name and SEC file number were corrected.
- Weatherford / Teradyne: parent 97210 (Teradyne) → child 1603923 (Weatherford); the child explicitly says the issuer name was corrected. This is a candidate-parent → noncandidate-child transition and shows why the correction must not be backdated.

### Direct SEC verification — Weatherford / Teradyne

The original Form 144 accession 0001959173-25-007533 identifies Teradyne (CIK 97210), accepted 2025-12-05 at 10:28:07 ET. Its Form 144/A child 0001959173-25-007544 identifies Weatherford (CIK 1603923), accepted at 12:03:06 ET the same day, and states: “The name of issuer has been corrected.” The proposed 2,129 shares and $164,465.25 are unchanged. This is one proposed-sale notice with a corrected issuer identity, not a second sale.

SEC filing detail and complete submission:
- Parent: https://www.sec.gov/Archives/edgar/data/97210/000195917325007533/0001959173-25-007533-index.htm
- Parent submission text: https://www.sec.gov/Archives/edgar/data/97210/000195917325007533/0001959173-25-007533.txt
- Amendment: https://www.sec.gov/Archives/edgar/data/1603923/000195917325007544/0001959173-25-007544-index.htm
- Amendment submission text: https://www.sec.gov/Archives/edgar/data/1603923/000195917325007544/0001959173-25-007544.txt

## Acceptance time is not first-public-receipt time

The SEC EDGAR filing detail page and complete submission text expose `Accepted` / `ACCEPTANCE-DATETIME`. However, the SEC Webmaster FAQ explicitly says there is no timestamp indicating when filing content first becomes available on sec.gov; availability is often 1–3 minutes after acceptance, can be significantly longer under load, and is not guaranteed. The SEC Form 144 electronic-filing guide says Form 144 submissions accepted from 6 a.m. to 10 p.m. ET on business days are publicly disseminated the same day, but does not provide an exact first-public timestamp.

Therefore:
- Acceptance time is a useful event-ordering field and a candidate conservative timing proxy.
- It is not certified first-public availability.
- Do not authorize same-day/intraday trading from acceptance time alone.
- Keep the conservative next-regular-session rule until a prospective Latest Filings / RSS / PDS first-seen ledger validates the public-availability clock.

Official SEC sources:
- Webmaster FAQ: https://www.sec.gov/about/webmaster-frequently-asked-questions
- Form 144 electronic filing guide: https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically
- Determine filing status: https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/determine-status-my-filing

## Existing Form 144 → Form 4 work (do not duplicate)

The repository's draft PRs #29 and #30 already contain a 2026Q3 descriptive conversion/linkage study: 1,451 notices / 1,460 tranches; 570 one-to-one links; 521 exact date-and-share matches; 481/521 class-family agreements. The separate selection audit matched 570/1,665 eligible Form 4 sale blocks. A global placebo audit reported 12/13 tests significant after Holm correction, but these tests concern document linkage, not forward-return prediction. Owner independence remains unproven. Phase 401 does not repeat that exercise.

## Interpretation and authorization

- Form 144 is a proposed sale/order notice, not proof of execution.
- Form 144/A is a version update, not a new sale by default.
- Issuer, filer and seller remain separate.
- A corrected issuer identity is usable only from the amendment's own public-availability time; never backdate it.
- `noOfUnitsOutstanding` remains killed as a numeric denominator/feature.
- Four parent links remain unresolved and are explicitly listed in `unresolved_parent_links.csv`; parent resolution is 99.723%, above the preregistered 99.5% threshold, but the unresolved records remain excluded from pair-level comparisons.
- Historical F80 membership, inactive/predecessor identity, complete security-class mapping, corporate actions, and exact first-public-receipt timing remain blockers.
- No forward returns, alpha, OOS, bootstrap, LOO or holdout test. No signal admitted; F80 and production unchanged.

## Next step

Rerun the corrected census gates once. If they pass, merge this research-only phase. Then perform a targeted acceptance-time audit of the four candidate-boundary pairs and the four unresolved parent links; do not broaden into a second Form 144/Form 4 linkage study.
