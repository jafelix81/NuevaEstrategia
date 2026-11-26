# Phase 643 — post-merge natural SEC Form 4 / 13F capture validation

**Audit cutoff:** 2026-11-26 15:27 UTC (08:27 America/Hermosillo)  
**Main HEAD before this documentation commit:** `1e85e7f038ebc6b93addb3d3e5fc7cda5859c98d`  
**Disposition:** the first natural scheduled Form 4 and SEC 13F polls after their respective fixes completed successfully. Together with the post-merge Form 144 run in Phase 642, all three SEC first-seen capture workflows now have natural post-merge success evidence. The operational capture pause is no longer supported by current Actions evidence. No investment signal or alpha evidence was created.

## 1. Actions preflight

Queried the repository's latest 100 Actions runs before making changes:

- Repository total: **8,350** runs.
- Latest 100: **71 success / 17 failure / 12 cancelled**.
- Queued, waiting, requested, pending or in-progress: **0**.
- No workflow was dispatched, rerun, cancelled or duplicated.
- Latest repository branch head before this document: `main = 1e85e7f038ebc6b93addb3d3e5fc7cda5859c98d`.

Latest relevant scheduled runs:

| Source | Run | UTC | Result |
|---|---:|---|---|
| SEC Form 4 / Phase 476 | [45848689364](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45848689364) | 15:23:55 | Success; post-merge PR #240 |
| SEC 13F / Phase 614 | [45839454376](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45839454376) | 14:29:01 | Success; post-merge PR #243 |
| SEC Form 144 / Phase 403 | [45827105431](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431) | 13:13:48 | Success; post-merge PRs #244/#245 |

Each run had successful `offline-regression` and `live-capture` jobs. Job steps, logs and artifact metadata were inspected. No active workflow was found.

## 2. Form 4 — natural post-merge validation of Phase 626 entity-duplicate audit

Run [45848689364](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45848689364) completed both jobs successfully on `main`.

### Feed / watermark result

- Both Form 4 and Form 4/A feeds succeeded.
- Both feed watermark and continuity gates passed.
- Poll window: 2026-11-26 15:24:08–15:24:09 UTC.
- One accession observation per feed; both were prior-watermark observations.
- **0 new accessions; 0 new canonical event rows.**
- Same-feed and cross-feed duplicate occurrence counts: **0**.
- No incomplete-feed suppression was required.

### Entity duplicate sidecar

The live job created and committed `research/data/sec_form4_first_seen/entity_duplicate_audit.csv`.

The natural poll produced two entity observations. Both have:
- `is_prior_watermark = true`;
- `is_exact_duplicate_entity_observation = false`;
- `is_exact_duplicate_across_page_offsets = false`;
- one distinct page offset and one distinct page hash.

This confirms that the post-merge sidecar is generated, persisted and populated by the natural workflow. It does **not** provide a positive duplicate case: both rows were pre-existing watermark observations. Duplicate-path coverage therefore still depends on the offline regression suite and future natural observations.

### Bounded structured backfill

- First 10-accession pass appended **23 transaction-detail rows** and **25 footnote-reference rows**.
- A second 10-accession footnote pass appended **24 additional references**.
- Owner-identity pass appended **10 owner rows**.
- All three passes reported zero parse errors.
- The refreshed Form 144/Form 4 crosswalk contained 12 rows and **0 signal-eligible matches**.
- Sixteen Form 4 accessions lacked a single-owner identity; seven multi-owner accessions remained quarantined.
- Two crosswalk rows had unresolved Form 144 acceptance clocks and were not made eligible.

The capture is a successful post-merge validation and useful append-only backfill, not a new insider event or predictive observation.

Artifacts:
- [Form 4 first-seen artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45848689364/artifacts/15132214284)

## 3. SEC 13F — natural post-merge validation of the User-Agent fallback

Run [45839454376](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45839454376) completed both jobs successfully.

The workflow environment showed an empty `SEC_USER_AGENT` secret. The integrated collector's `configure_sec_user_agent()` correctly falls back to the established shared project contact in Phase 401, without printing or persisting the contact. The successful HTTP responses and completed feed gates demonstrate that this fallback worked; no new secret or user action is required.

### Feed result

All four feeds returned complete HTTP-OK pages:

| Feed | New accession observations |
|---|---:|
| 13F-HR | 18 |
| 13F-HR/A | 9 |
| 13F-NT | 2 |
| 13F-NT/A | 0 |
| **Total** | **29** |

- Four page observations, one per feed.
- Zero same-feed duplicates and zero cross-feed duplicate occurrences.
- Poll window: 2026-11-26 14:29:24–14:29:28 UTC.
- All feed watermark and continuity gates passed.

### Eligibility disposition — baseline only

This was the first successful poll after the capture workflow was introduced. Each feed was explicitly classified `INITIAL_BASELINE_NO_LOWER_BOUND` / `NO_PRIOR_SUCCESSFUL_POLL`.

Consequently:
- Metadata-interval-eligible observations: **0**.
- Research-observation-eligible observations: **0**.
- Signal-eligible observations: **0**.
- Holdings rows downloaded: **false**.
- Raw transaction rows persisted: **false**.

The 29 accessions are retained as baseline observations. Their first-seen receipt time is an upper-bound observation, not an exact public-availability or executable timestamp. The baseline records cannot be retroactively assigned a prior-poll lower bound. A later natural poll can establish bounded intervals for newly observed entries only, subject to the remaining legal dissemination, acceptance-clock, manager identity, security identity and historical-universe gates.

Artifacts:
- [SEC 13F first-seen artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45839454376/artifacts/15125664876)

## 4. Form 144 — prior post-merge validation remains valid

Phase 642's [run 45827105431](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431) remains the latest scheduled Form 144 capture and passed after PRs #244/#245.

- 53 feed observations: 50 Form 144 and 3 Form 144/A.
- Both feeds complete; no errors or continuity gaps.
- Zero new accessions in that poll.
- Ten queued accessions backfilled, adding 52 structured detail rows.
- Ledger at 825 accessions / 5,495 detail rows.
- 807 bounded intervals and 18 initial-baseline rows without a lower bound.
- Zero malformed intervals, zero exact-public-availability certifications and zero signal-eligible filings.

Form 144 remains proposed-sale context and a negative-control source, not proof of executed selling.

## 5. Operational conclusion

The prior request to verify whether the three SEC workflows were enabled is no longer outstanding. Natural scheduled runs now demonstrate successful post-merge operation for:
- Form 4 after PR #240;
- SEC 13F after PR #243, including the fallback with an empty repository secret;
- Form 144 after PRs #244/#245.

No repository secret change is required. Do not manually dispatch duplicate captures. Continue on the natural schedule.

## 6. Other source and branch state

No newer scheduled run appeared in the latest 100 for CFTC TFF, FINRA Reg SHO or FINRA T1 ATS.

- **CFTC TFF:** latest scheduled run remains [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471); retain the 3,035 archive rows as unverified PIT proxies and the eight prospective observations across two report-date clusters as insufficient for a signal test.
- **FINRA Reg SHO:** latest [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648) still rejected all eight files under the BCPC/TPC row-grain gate; zero volumes admitted.
- **FINRA T1 ATS:** no new scheduled capture. The 209-week venue-concentration panel remains a conditional market-structure hypothesis, not beneficial-owner/institutional flow. PRs #50/#61 remain Draft and should not be merged wholesale.
- **SEC 13F research chain:** PRs #221–230 remain Draft; preserve the role-aware manager, amendment, dissemination-clock and security identity gates. Do not merge the stale branch chain wholesale.
- **SEC 13D/G:** PR #37 remains Draft; the 43/44 parent retrieval and CUSIP discrepancies remain unresolved as recorded in Phase 636.
- **Options / MIDAS:** continue feasibility only. No vendor contact, sample request, quote, license or purchase; options-data budget remains **USD 0**.

## 7. Quantitative disposition

- New Smart Money signals admitted: **0**.
- Incremental alpha versus frozen LTM/F80: **none demonstrated**.
- New valid OOS, bootstrap or LOO evidence: **0**.
- No return study, final-holdout access or production change.
- No change to universe, parameters, exposure, costs, capital or holding-period policy.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## 8. Next gates

1. Allow the next natural SEC 13F poll to establish first-seen intervals for genuinely new entries; do not promote the 29 baseline observations.
2. Continue natural Form 4 captures and bounded transaction/footnote/owner backfills; preserve multi-owner and unresolved-clock quarantines.
3. Continue Form 144 descriptive backfill and negative controls.
4. Start a return study only after PIT availability, historical identity, F80 membership and inactive/delisted price coverage are all established for the relevant source.
5. Keep FINRA Reg SHO, CFTC archive history, and paid options feeds quarantined until their respective row-grain, PIT, coverage and rights gates pass.

No baseline or production change is authorized by this phase.
