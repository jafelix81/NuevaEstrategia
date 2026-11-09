# Smart Money Research — Current State

**Updated:** 2026-11-09  
**Repository:** jafelix81/NuevaEstrategia  
**Research branch:** phase99-broad-pit-universe-charter  
**PR:** #13, open and currently mergeable; do not merge automatically.

## Frozen controls and guardrails

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- The original 335-name F80 universe was manually selected and has no reproducible historical membership rule. Treat F80 results as conditional on that curated list; do not silently replace it.
- The legacy holdout is `CONSUMED_NOT_PRISTINE`; do not use it for new confirmation.
- No CAGR target or fixed holding period. Require chronological OOS, identical exposure/costs, bootstrap and LOO before any promotion.

## Killed or parked hypotheses

- FINRA short-flow × short-interest divergence: killed as independent alpha after horizon-dependent sign reversal and bootstrap intervals including zero.
- SEC Form 4 standalone feature set: killed in its tested frozen-universe OOS diagnostic; do not tune the same implementation to rescue it.
- CFTC TFF equity-index positioning: killed in the tested stock-selection form; TFF may remain regime context only if publication vintages are reconstructed.
- SEC N-PORT long-accumulation dose-response: killed in the tested form.
- OCC volume-by-account-type: parked; short recent history and no direction/open-close/beneficial-owner identity.
- SEC MIDAS: market-structure context only; historical daily rows were published in quarterly releases, so no daily PIT signal admission.
- Nasdaq Trade Outline: not economically justified at quoted acquisition cost and unresolved PIT/venue-routing semantics.

## Conditional source candidates

- **SEC 13D/G:** Phase 225 shows 13D and 13G event-date mechanics differ materially; keep them separate. Phase 226 recovered family-specific group flags, but Phase 227 found its repeated-signature totals included all-zero tuples. Correct positive repeated-signature filings are 20/34 13D and 21/68 13G; zero signatures are separate. Group flags remain contextual, not unique group IDs. Amendment state, owner identity and effective-dated security identity still block any economic test.
- **Form 144:** daily PIT clock is conservatively the first XNYS session after SEC filing date. Signal is not admitted: seller/security-class identity, historical active/delisted universe, independent PIT shares/float and ADV remain unresolved. Form 144 is a proposed sale notice, not execution.
- **N-PORT short exposure:** distinct short-quantity hypothesis is preregistered, but the 23-row example is purposive and from one filing. Raw filing retrieval/hashes, series lineage, class/security identity and broad PIT coverage remain pending.
- **Options:** Cboe C1 Open-Close EOD remains the leading conditional participant-capacity source; C1-only, not whole OPRA, and historical first-receipt/correction vintages are not established. IvyDB Open Interest / TradeFlow remain conditional candidates; no purchase or alpha admission.
- **FINRA ATS/OTC:** data reconcile, but revised final values cannot be backdated to first publication; historical vintages and broad PIT security identity remain unresolved.
- **SEC Companyfacts/XBRL:** Companyfacts is partial for entity-wide facts; class-specific raw accession XBRL is required for multi-class issuers. Phase 224 has synthetic regression tests but no live coverage census.
- **CFTC TFF:** regime candidate only, not stock-level institutional flow; historical publication-vintage reconstruction is required.

## Phase 225 — 13D/G event-time semantics

- Phase 124 source: 600 stratified index rows, 599 actual filings, one index alias quarantined; 600 raw hashes and SEC headers reverified.
- Event dates: 553/599 parsed (92.32% unweighted). Phase 214 independently reproduced all 497 legacy HTML parser outcomes, but this is not a gold-standard semantic validation.
- Weighted 13D: 96.04% date coverage; 2.63% quarter-end event dates; weighted median filing-event lag 4 days.
- Weighted 13G: 90.73% date coverage; 76.44% quarter-end event dates; weighted median filing-event lag 40 days.
- Keep 13D/13G and initial/amendment cohorts separate. Event date is never the knowledge clock; use SEC acceptance and next-session availability.
- No returns/alpha, holdout, bootstrap/LOO or production test in Phase 225.

## Technical blockers and repository state

- N-PORT raw SEC retrieval previously failed closed because the authorized SEC contact configuration was missing. Do not invent an email or bypass SEC fair-access requirements.
- PR #13 is open, 553 commits ahead / 1 behind main by compare after Phase 226; GitHub reports mergeable/clean. No merge was attempted.
- Branch inventory: 130 branches.
- Latest 100 Actions runs: 98 success, one failure and one cancellation; zero in-progress or queued. The Phase 214 failure was an earlier attempt; corrected run 42491346221 passed. The cancelled attempt was replaced.
- Latest CI fan-out is on older commit 5ac79c0; latest run 42491346732 (Phase 185) succeeded, its audit job completed and artifact 13621239943 was uploaded (945 bytes; SHA-256 d9575f5e9df29fce61eaef81955105b1d4f88827f65980f4630acaecd9e1efc9). The current PR head has no check-runs because research commits use `[skip ci]`.

## Promotion rule

No candidate becomes a model feature until historical coverage, ex-ante availability, stable identifiers, survivorship/delisting treatment, incremental information versus frozen LTM/F80, chronological OOS and economic costs all pass. A plausible institutional interpretation is a hypothesis, not evidence.


## Phase 226 — 13D/G reporting-person group flags

- Re-downloaded Phase 124 artifact 13436764625 and verified ZIP SHA-256 85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc, CSV SHA-256 be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5, and all 102 XML-bearing raw submission hashes.
- 310 reporting-person blocks: 33 affirmative group flags, 108 disclaimer/relationship flags and 169 unreported. Only 5/102 filings affirm group membership; 75/102 have all group flags unreported.
- Phase 226's 21/34 13D and 27/68 13G repeated-signature filing counts included zero-only repetitions. Phase 227 separates 50 positive repeated-signature groups from 8 all-zero groups; positive-repeat filings are 20/34 13D and 21/68 13G. Group flags do not establish a unique beneficial-owner graph.
- 13G reporting-person CIK remains absent in 158/158 owner blocks; group flags do not repair identity.
- Local validation: 14/14 tests passed, including full integration against the hash-pinned Phase 124 artifact. No hosted Phase 226 Actions run is claimed.
- No returns, alpha, bootstrap/LOO, holdout, vendor purchase, production or F80 change.


## Phase 227 — zero-signature exclusion and source-linked overlap adjudication

- Re-downloaded Phase 124 run 42073725379 / artifact 13436764625; ZIP SHA-256 85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc and CSV SHA-256 be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5 verified; all 102 XML-bearing raw-submission hashes reverified.
- 58 repeated signature groups split into 50 positive groups (162 owner rows) and 8 all-zero groups (27 rows). Of 48 filings with any repeat, 41 have a positive repeated group, 7 are zero-only, and one 13G filing has both positive and zero groups.
- Positive-repeat filings: 20/34 13D and 21/68 13G. Seven zero-only filings: Mobiquity, Instructure, Endeavor, SatixFy, CARGO Therapeutics, BlackRock MuniVest Fund II and Palisade Bio; Savara is the mixed 13G case.
- Twelve source-linked examples reviewed. Eight support common-holder/adviser/GP/trustee attribution; Korsana is a multi-fund/instrument group aggregate; Vislink and Plum remain unresolved; Mobiquity is a zero-position control. Never sum repeated reporting-person rows.
- Group flags a, b and missing all appear among overlap examples; they are not a deduplication key. Joint filing alone is not proof of a unique group or additive positions.
- Auditor: phase227_13dg_overlap_adjudication.py; tests: test_phase227_13dg_overlap_adjudication.py; result: phase227_13dg_overlap_adjudication_result.json. Local validation: 7/7 tests passed, including full integration against the hash-pinned 102-document sample. No hosted Phase 227 Actions run is claimed.
- No forward returns, alpha, bootstrap/LOO, final holdout, vendor purchase, production, universe or F80 change.


## Phase 228 — 13D/G regulatory-deadline regime split

- Re-downloaded Phase 124 artifact 13436764625 and verified ZIP SHA-256 `85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc`, CSV SHA-256 `be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5`, 600/600 raw hashes and SEC headers, 599 primary filings, and 102 structured XML event dates.
- Applied the correct distinct compliance cutoffs: 13D 2024-02-05; 13G 2024-09-30; structured-data mandate 2024-12-18 is a separate format break.
- 13D weighted median event-to-filing lag: 4 days pre / 2 days post; weighted P90 27 / 18. Post-reform initial cohort is small (21 filings) and its weighted P90 is 86 days due to a long-lag observation.
- 13G weighted median: 41 days pre / 38 post; weighted P90 remains 45 days; weighted quarter-end concentration 74.80% / 81.73%. 13G remains a delayed quarter-end ownership-disclosure cohort, not transaction-level flow.
- Split by initial/amendment cohort and kept all statistics descriptive. Sample is stratified; no causal inference, significance testing, returns or alpha.
- The committed Phase 225 result JSON omitted the regime split calculated by its audit logic. Phase 228 publishes a separate hash-pinned result; no historical artifact was overwritten.
- Files: `PHASE228_SEC_13DG_REGULATORY_DEADLINE_REGIME_SPLIT_AUDIT_2026-11-08.md`, `phase228_13dg_regulatory_regime_split_audit.py`, `test_phase228_13dg_regulatory_regime_split_audit.py`, and `phase228_13dg_regulatory_regime_split_audit_result.json`. Four local unit tests passed; the hash-pinned source was independently re-parsed locally.
- No alpha, forward returns, bootstrap/LOO, holdout, production, universe or F80 changes.


## Repository / Actions status after Phase 228

- Research branch head: `554dbce98d1c8a9f1b1ce5541491bb4da44729a7`.
- PR #13 remains open, unmerged and GitHub reports mergeable; compare is 565 commits ahead / 1 behind main, 497 changed files. No merge was attempted.
- Latest 100 repository Actions runs: 98 success, 1 failure, 1 cancelled; zero in-progress or queued. Latest run remains 42491346732 (Phase 185), completed successfully. Its audit job steps/log and artifact 13621239943 (945 bytes; digest d9575f5e9df29fce61eaef81955105b1d4f88827f65980f4630acaecd9e1efc9) were inspected.
- Phase 185 artifact/log confirms zero strict-PIT-admitted Cboe Open-Close rows; all audited 1-minute archive history before the 2025-07-13 product floor is retrospective, and even post-floor data require actual first-receipt logs and immutable correction vintages.
- The new Phase 228 head has no associated PR workflow runs because all research commits used `[skip ci]`; local tests are not represented as hosted CI.
- Branch inventory: 130 (100 first page + 30 second page).


## Phase 229 — regulatory cohort assignment by event-date proxy (2026-11-09)

- Phase 228's pre/post descriptive split used filing date. Phase 229 retains that view but adds event-date-proxy assignment, because the revised filing regime applies to the event/trigger that generated the obligation rather than the later disclosure date.
- Re-downloaded Phase 124 run 42073725379 / artifact 13436764625. ZIP SHA-256 `85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc`; CSV SHA-256 `be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5`.
- Rechecked 600/600 raw SHA-256 values, 600/600 SEC headers, 599 primary 13D/G documents, and 102/102 structured XML event-date values. Parsed event dates remain 553/599; 46 remain unknown and unclassified.
- Exactly one parsed 13D/A crosses the 2024-02-05 boundary: accession 0001554855-24-000055, event 2024-01-31, filed 2024-02-08. Filing-date assignment called it post-cutoff; event-date-proxy assignment calls it pre-cutoff. No parsed 13G filing crosses 2024-09-30.
- The event-date-proxy reclassification changes 13D amendment cohort membership (pre 93 vs 92; post 30 vs 31) but leaves family-level weighted medians/P90 unchanged: 13D 4/27 pre and 2/18 post; 13G 41/45 pre and 38/45 post. This is descriptive only; no compliance or causal inference.
- Eight Phase 229 helper-level assertions were reproduced locally; the full Phase 229 module was not run from a clean repository checkout. The full raw-source reparse and hash/header/XML integrity checks were independently run locally. No dedicated Phase 229 workflow exists. The commits carrying Phase 229 files unexpectedly triggered the existing PR workflow fan-out because their messages lacked a CI-skip marker; see the corrected operations record below.
- Files: `PHASE229_SEC_13DG_REGULATORY_COHORT_ASSIGNMENT_BY_EVENT_DATE_AUDIT_2026-11-09.md`, `phase229_13dg_event_date_regime_assignment_audit.py`, `test_phase229_13dg_event_date_regime_assignment_audit.py`, and `phase229_13dg_event_regime_assignment_audit_result.json`.
- 13G deadlines remain filer-category/trigger-specific. The cover-page event date is only a proxy, not a trade date or universal legal trigger. SEC acceptance datetime remains the knowledge clock; no same-session use.

## Repository / Actions status verified 2026-11-09

- Research branch at the start of Phase 229: `4779fd7be65666292f2be59d760d431dc29ec55c`; Phase 229 artifacts were then committed on the same research branch. Do not infer that the state-file update commit is the branch head.
- PR #13 remains open and unmerged; at the pre-Phase-229 check GitHub reported `mergeable=true`, 566 commits ahead / 1 behind main, 497 changed files. No merge or rebase was attempted.
- Latest 100 Actions runs: 98 success, 1 failure, 1 cancelled; zero in-progress or queued. The 100-result second page was also checked; no active run was found there.
- Latest run 42491346732 (Phase 185) succeeded. Job 128764198338 completed every step; artifact 13621239943 is 945 bytes with SHA-256 `d9575f5e9df29fce61eaef81955105b1d4f88827f65980f4630acaecd9e1efc9`. Its log still reports zero strict-PIT-admitted Cboe Open-Close rows.
- The only failure in the latest 100 was the first Phase 214 attempt 42491263644: two unit tests expected a three-value return while the parser returned two. It was superseded by successful run 42491346221; the cancelled attempt 42491341126 has no completed jobs.
- Branch inventory: 130 (100 first page + 30 second page).
- The Phase 229 file commits triggered 57 existing PR workflows on head `c2d733ea28112d1943d8842a6666339737ac9771`; all 57 completed successfully. Twelve older-head runs were cancelled/superseded. No failures or active runs remained. The latest 100 runs after that fan-out were 88 success / 12 cancelled / 0 failed / 0 active. No dedicated Phase 229 test job was run. All Phase 230 and provenance-correction commits used `[skip ci]`.
- N-PORT raw retrieval remains blocked by missing authorized `SEC_CONTACT_EMAIL`. No address was invented and no SEC fair-access control was bypassed.


## Phase 230 — Cboe Option Quotes locale reclassification (2026-11-09)

- Phase 174 run 42562292847 / artifact 13650205761 observed 115,617 populated public-sample row instances; 94,607 were rejected solely as `invalid_expiration_format` by its ISO-extended-only expiration parser. The five members had required headers and no unknown headers; Phase 174 did not persist raw rows or contract keys.
- Phase 175 run 42562292743 / artifact 13649604168 downloaded the identical sample archive (SHA-256 `7645a6cc94f1a984e98264a4b494f748e373c30ecde85de25ceadb83a5c56782`) and completed a conservative multi-format date diagnostic.
- Reclassification: 91,303 of the 94,607 originally rejected row instances have exactly one expiration-date interpretation; 3,304 row instances (826 in each of four 2023 sample members) remain ambiguous and must be quarantined. Across all five members, 112,313 row instances have one unique expiration interpretation. These are row instances, not unique contracts.
- All 115,617 quote_datetime values have one unique candidate interpretation: 94,607 US-slash minute-precision values from 2023-09-21 and 21,010 ISO-second values from 2022-02-02. The 2023 members show eight unique times from 10:30 to 16:15 ET; the 2022 member has one time (09:39 ET). No seconds were fabricated.
- Phase 230 is a metadata-level reclassification, not a full raw-row parser rerun. Contract keys, duplicate checks, numeric checks, quote checks, and SOD-OI consistency were not recomputed with locale-aware expiration parsing. The full sample/schema gate therefore remains NOT ADMITTED.
- Phase 230 auditor/tests/result and the condensed Phase 175 metadata input are committed. Local regression suite: 10/10 passed. No dedicated Phase 230 workflow was launched.
- Next gate: rerun the full sample parser using only unique date interpretations; quarantine ambiguous expiration rows; preserve timestamp precision; then recompute all row-level contract/numeric/duplicate/quote/OI checks. Even a clean sample result will not satisfy PIT, historical universe, first-receipt/correction-vintage, or license gates.
- Cboe Option Quotes remains a conditional interval/IV/OI context source, not signed institutional flow. No alpha or forward-return test.

## Repository / Actions status verified after Phase 230 (2026-11-09)

- PR #13 remains open, unmerged, and GitHub reports `mergeable=true`, `mergeable_state=clean`. Head: `be028d8f225802b5bbd5b3e4cb7b1abf6304bfdd`; compare: 579 commits ahead / 1 behind main; 506 changed files. No merge/rebase attempted.
- Branch inventory remains 130 (100 first page + 30 second page).
- Latest 100 Actions runs: 88 success, 12 cancelled, zero failed, zero active/queued. Of these, 57 runs associated with the Phase 229 file-push head `c2d733ea28112d1943d8842a6666339737ac9771` all succeeded; 12 runs on the immediately older head were cancelled/superseded. The fan-out is complete.
- Phase 175 date-locale job 128981504363 completed all steps successfully and uploaded artifact 13649604168 (2,369 bytes; ZIP SHA-256 `7a3f988b6edb6e41e987399f94b85122ae7b712b8922326203e03087e877ea7f`). The sample download and locale diagnostic completed; sample/PIT/alpha admission remained false.
- Phase 203 run 42562292699 / artifact 13650117276 and Phase 204 run 42562292773 / artifact 13650002696 both completed successfully. All six MIDAS ZIP archives passed CRC checks; three-quarter exchange/aggregate sample reconciliation was reproduced. Naive all-exchange sums fail for methodology-sensitive fields, while README/methodology-specific variants reconcile in the sampled quarters. First-publication time and permanent historical security identity remain unverified; MIDAS stays NOT ADMITTED for strict daily PIT.
- The Phase 229 push fan-out was an operational mistake: five file commits were created without a CI-skip marker, causing existing PR workflows to run. No run failed; 57 on the final pushed head succeeded and 12 superseded older-head runs were cancelled. All subsequent Phase 230 and audit-correction commits use `[skip ci]`; no new workflows are active.
- N-PORT raw retrieval remains blocked by missing authorized `SEC_CONTACT_EMAIL`. No contact identity was invented and no SEC access control was bypassed.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; legacy holdout remains `CONSUMED_NOT_PRISTINE`. No source has been admitted to alpha, no forward-return test was performed, and production/universe remain unchanged.
