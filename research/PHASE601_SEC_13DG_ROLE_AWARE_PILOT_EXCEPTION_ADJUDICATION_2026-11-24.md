# Phase 601 — SEC 13D/G role-aware pilot: documented combined-filing exception adjudication

**Audit cutoff:** 2026-11-24 19:51 UTC  
**Main HEAD at preflight:** `0cc4cbdc558c8b249181bd71dbb3d569816e29ee`  
**Disposition:** **Phase 84 identity/data-feasibility gate passes after one narrowly documented SEC combined-filing exception is removed from the XML denominator.** No returns or alpha test.

## 1. Repository and Actions preflight

- Main Actions count: 8,111 total. Latest 100: 90 success / 10 failure; zero queued, in-progress, waiting or requested.
- Branches: 380. Open PRs: 72. Workflow files: 96. Research files: 516.
- No workflow was dispatched, rerun, cancelled, merged or duplicated in this phase.
- Latest scheduled capture runs were all complete:
  - Form 4 Phase 476 [run 45453400450](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45453400450), 2026-11-24 17:52:49 UTC; artifact [14948444955](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45453400450/artifacts/14948444955). Both jobs succeeded. The feed poll wrote 57 new accession events / 117 accession-observation rows from two feeds; 58 same-feed repeated observations were preserved, with zero cross-feed duplicates. No filing XML/text was downloaded by the metadata poll. Phase 510 backfilled 10 accessions / 30 detail rows, with 2,320 bounded accessions remaining. Phase 525 enriched 10 owner accessions / 11 owner rows; transaction-line owner attribution remains unverified. The crosswalk remains descriptive, with zero signal-eligible matches. No public-availability certification was produced.
  - Form 144 Phase 403 [run 45437675674](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45437675674), 2026-11-24 16:29:14 UTC; artifact [14941267954](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45437675674/artifacts/14941267954). The poll captured 27 new accession events / 53 feed observations; all 27 XML documents resolved. The ledger is 514 accessions / 3,549 detail rows, with 228 accessions remaining in the bounded structured-detail queue. The post-capture audit found zero parse errors and zero source-hash mismatches, but zero signal-eligible rows and zero public-availability-certified headers. Form 144 remains a proposed-sale notice, not proof of execution.
  - FINRA Reg SHO Phase 469 [run 45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236), 2026-11-24 06:15:11 UTC; artifact [14895571787](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236/artifacts/14895571787). Six HTTP-200 daily files were rejected by the fail-closed parser; the duplicate diagnostic records 12 extra rows across BCPC and TPC. No valid or first-seen observations were admitted, and raw market-volume rows are not persisted. This remains a data blocker, not a negative alpha result.
  - CFTC TFF Phase 384 [run 45338400329](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329), 2026-11-24 06:09:53 UTC; artifact [14895036288](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329/artifacts/14895036288). The 3,043-row archive was unchanged; no new reports, revisions or events were written. Weekly features remain suppressed until a cadence-specific specification is preregistered.
- Form 4's two latest main-branch scheduled runs occurred at 05:21:36 and 17:52:49 UTC, 12h31m apart despite the nominal hourly schedule. The workflow is demonstrably enabled (both runs succeeded), but schedule delivery gaps remain open under [issue 194](https://github.com/jafelix81/NuevaEstrategia/issues/194). This is not evidence that the workflow is disabled.

## 2. Existing global 13D/G discovery work — do not repeat it

The repository already completed the global index feasibility work:

- Phase 82 retrieved 43 quarterly master indexes covering 2016Q1–2026Q3: 324,964 unique 13D/G accessions, zero cross-quarter accession duplicates, zero unexplained metadata conflicts, and 34,400 accessions with at least one of 319 **current candidate CIKs** in the unlabelled index/path set. This is a discovery population, not historical F80 coverage.
- Phase 83's original 120-filing identity gate failure is preserved: among 44 unique-candidate rows, only 11 (25%) had the candidate CIK in the SUBJECT COMPANY role; 33 (75%) were FILED BY-only false positives. Do not relax or overwrite that result.
- Phase 84 then tested a disjoint 600-filing, role-aware sample in [run 41914491120](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41914491120), artifact [13364856424](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41914491120/artifacts/13364856424). All 600 submissions were retrieved, with zero fetch errors; header parse, accession/date concordance, subject/filer CIK presence, acceptance timestamp validity and raw-hash/retrieval-time coverage were 100%. The 319-CIK candidate set missed zero target-subject CIKs in this sample, but it also produced 143 filer-only false positives among 367 candidate rows (38.96%). The deterministic post-stratified estimate is 52.06% subject-target / 47.94% filer-only within the 34,400 candidate-accession population; this is descriptive, has no design-based confidence interval, and is not historical F80 coverage.

## 3. Why Phase 84 was reported FAIL — and the exact correction

The original Phase 84 code compared the master-index form to the submission's `CONFORMED SUBMISSION TYPE` and required XML for every sampled row classified into the post-2024-12-18 mandatory-XML regime. It therefore reported:

- form concordance 599/600 (99.833%);
- XML present in 192/193 mandatory-XML rows (99.482%);
- original `data_gate = FAIL`.

Both apparent defects are the same accession: `0001104659-26-057293`, filed 2026-05-07. Its SEC header has two SUBJECT COMPANY filing-value blocks: `SC 13D/A` and `SC TO-T/A`; the conformed submission type is `SC TO-T/A`. The public document is a combined Schedule TO amendment that also amends Schedule 13D. The filing's cover page expressly checks the box for an amendment to Schedule 13D and states that it is also Amendment No. 10 to the Schedule 13D.

The SEC EDGAR Filer Manual, Volume II, Version 76, effective September 15, 2025, explicitly states in §7.3.11.2 (page 7-76) and §8.1.10 (page 8-28) that the structured XML implementation of Schedule 13D/A is **not required** for a combined filing with SC TO-I, SC TO-I/A, SC TO-T or SC TO-T/A, because EDGAR does not support that combined submission in XML. This is a documented format exception, not a missing XML document. The SEC's own accession header and primary filing confirm this is exactly that combination.

Official source evidence:
- [SEC EDGAR Filer Manual, Volume II, Version 76](https://www.sec.gov/files/edgar/filermanual/archive/edgarfm-vol2-v76.pdf), §§7.3.11.2 and 8.1.10.
- [SEC accession header](https://www.sec.gov/Archives/edgar/data/1326200/000110465926057293/0001104659-26-057293-index-headers.html).
- [Primary combined Schedule TO-T/A document](https://www.sec.gov/Archives/edgar/data/1326200/000110465926057293/tm2612953-13_sctota.htm).

## 4. Phase 601 adjudication result

The new offline adjudicator reads the immutable Phase 84 artifact and the raw submission headers. It does not make SEC requests and does not alter the original Phase 84 run or artifact.

- Role-aware form concordance: **600/600 (100%)** when the index form is checked against the `SUBJECT COMPANY` filing-value blocks rather than the conformed submission type.
- Documented combined Schedule 13D/A + SC TO-T/A exception: **1** (`0001104659-26-057293`).
- XML-required sample rows after the exception: **192**.
- XML present in those required rows: **192/192 (100%)**.
- Other missing mandatory XML: **0**.
- Raw submission files present: **600/600**.
- Offline regression tests: **8/8 passed**.

**Adjudicated Phase 84 data gate: PASS.** The original run remains recorded as failed under its original overbroad rule; Phase 601 supplies the auditable correction rather than rewriting history. The exception is deliberately narrow: it applies only to a Schedule 13D/A that is actually combined with one of the SEC-listed SC TO submission types and is present in the SUBJECT COMPANY filing values. It does not excuse a standalone 13D/A or any 13G/G-A XML omission.

## 5. Research meaning and next gate

This is a meaningful improvement in 13D/G data feasibility, not a trading result:

1. Global master-index discovery plus header-role resolution is viable in the 600-row sample. A candidate CIK hit must never be treated as issuer identity without the SUBJECT COMPANY / FILED BY distinction.
2. The old 20,266-row Phase 35 panel remains quarantined. Phase 83's failed unique-candidate test remains intact.
3. Before any economic test, build an effective-dated issuer/security crosswalk for the frozen F80 names: historical CIK, CUSIP, class, ticker/listing, delisted entities and corporate actions. The 319 current CIK candidates are not a historical point-in-time security master, and the original 335-name F80 eligibility/membership rule is still undocumented (Phase 71).
4. Then reconstruct reporting-person/group identities and amendment lineage (`previousAccessionNumber`), preserve each filing's own acceptance/publication knowledge time, and separate 13D, 13D/A, 13G and 13G/A legal/schema regimes.
5. Only after those coverage and PIT gates pass should a preregistered 13D activist/ownership-change hypothesis be compared with frozen LTM/F80 under identical exposure and costs, chronological OOS, block bootstrap, issuer/reporting-group clustering and LOO.

The Phase 350 exact-parent retrieval PR remains separately gated on the repository `SEC_USER_AGENT` Actions secret. This phase neither inspected nor changed that secret. Do not expose its value in chat or commit it.

**No strategy change:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No forward returns, alpha, OOS, bootstrap, LOO, holdout use, production change, data purchase or vendor contact was made.
