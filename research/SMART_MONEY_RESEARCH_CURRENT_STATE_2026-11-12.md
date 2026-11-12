# Smart Money Research — current state (2026-11-12 UTC)

**Active research branch:** `phase325-sec-form4-issuer-symbol-full-census`  
**Latest completed research:** Phase 325 — six-quarter SEC Form 4/4-A issuer-symbol full-census quality audit.  

## Latest verified research — Phase 325 (2026-11-12 UTC)

- Final GitHub Actions [run 43196055022](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43196055022) passed **7/7 offline regressions**, re-downloaded the immutable Phase 321 artifact and verified its ZIP SHA-256 before running the full-census audit. [Artifact 13931894766](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43196055022/artifacts/13931894766), ZIP SHA-256 `6d7930230a60036931857520df07b28087720d54ae9d3bee8f4b1cfe2fbcefa3`.
- Six selected quarters contain 317,267 Form 4/4-A accessions and 11,637 issuer CIKs. A conservative canonical as-filed symbol candidate exists on 311,245 rows (98.1019%); 474 CIKs have no canonical candidate across the sampled quarters.
- 1,293 CIKs show multiple canonical candidates across the sparse sampled quarters; 637 ticker candidates are reused across more than one issuer CIK. The exact-date diagnostic finds 28 issuer-CIK pairs sharing the same candidate ticker on at least one filing date (42 shared dates). This confirms that ticker alone is not a safe issuer/security key.
- Keep issuer CIK as primary filing identity and retain the SEC symbol as a descriptive, accession-vintage issuer label only. The 28 collision pairs and 1,293 multi-candidate CIKs require effective-dated class/listing adjudication; no security master or broad-universe mapping is admitted.
- Report: [Phase 325 full-census audit](PHASE325_SEC_FORM4_ISSUER_SYMBOL_FULL_CENSUS_AUDIT_2026-11-12.md). The artifact contains period summaries and the 28-row collision file; raw SEC bytes were not uploaded.
- No strict PIT/security-master admission, return/alpha, bootstrap/LOO, chronological OOS or holdout test. F80, production, universe, capital and parameters remain unchanged.

## Latest verified research — Phase 324 (2026-11-12 UTC)

- Final GitHub Actions [run 43192937006](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43192937006) passed 9/9 offline regressions and completed the source-level recheck. [Artifact 13930934547](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43192937006/artifacts/13930934547), ZIP SHA-256 \`e2828741eba0317dc5a582e0c70796f88ec438a606e268807f92cb9a2ef0f78b\`.
- Re-fetched all three original Form 4 submissions that remained quarantined after Phase 323. All 3/3 original header identity checks passed, including accession, form, header CIK, filed date, acceptance timestamp and XML issuer/reporting-owner CIK set.
- Retrieved and parsed 21 targeted SEC daily indexes with zero HTTP or parser errors. Six exact accession/index rows were recovered across two cases; all row CIK/path-CIK pairs matched.
- VIST accession \`0000775662-08-000044\`: four exact rows across 2008-10-02 and 2008-10-06, with conflicting row filed dates (2008-10-02 vs. 2006-02-15); acceptance lag 662 EDGAR business days. Remains quarantined.
- BeOne accession \`0001193125-26-393103\`: no exact row in six business-day indexes from 2026-09-16 through 2026-09-23, despite original header/XML identity confirmation. Six reporting owners plus issuer. XML transaction code M is exercise/conversion, not an open-market purchase. Remains quarantined.
- Nalco accession \`0001298341-06-000168\`: two exact entity rows on 2006-10-13 match acceptance/index date, but the header filed date is 2006-02-14 (168 business-day lag). XML code P means open-market **or private** purchase; not proof of a public-market execution. Remains quarantined.
- Decision: keep all three exceptions quarantined. Phase 323's 21/24 corroborated cases are date-level evidence only; the exception set is purposive, not a probability sample. Daily-index date is not an exact first-public receipt timestamp. Strict PIT remains closed.
- No alpha/return, bootstrap/LOO, chronological OOS or holdout test. F80 and production controls remain unchanged.

- [Phase 324 report](PHASE324_SEC_FORM4_EXCEPTION_SOURCE_LEVEL_ADJUDICATION_2026-11-12.md)

## Latest verified research — Phase 323 (2026-11-12 UTC)

- GitHub Actions [run 43188524842](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43188524842) passed. [Artifact 13928449264](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43188524842/artifacts/13928449264), ZIP SHA-256 \`dacc9f8374e4f86cc31dbe59de5d856ee1900902ce4096b879b69127e38e66fb\`.
- Corrected the semantic comparison between SEC bulk/header \`FILED AS OF DATE\`, \`ACCEPTANCE-DATETIME\` and the daily-index file/row date. Of 24 full-census exceptions, 21 had acceptance date and daily-index date agree; 20 were one EDGAR business day later than the header/bulk date, one was four business days later.
- One long-acceptance-lag case, one multi-index-date conflict and one daily-index-absent case remained quarantined. The 24 cases are the exception population, not a probability sample.
- No strict PIT admission or return test.

## Latest verified research — Phase 322 (2026-11-12 UTC)

- GitHub Actions [run 43187165781](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43187165781) passed. [Artifact 13928752264](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43187165781/artifacts/13928752264), SHA-256 \`c7eaf3cfc751e401d543bceeec20c3fe6643b09dfb8d2b0ff97df86070dca50d\`.
- All 24 exceptions from Phase 321 had an original SEC header and a master-index hit. Twenty-one initially differed between bulk/header filed date and daily-index evidence; three had no daily-index hit in the first search. Phase 323/324 further adjudicated these cases.

## Latest verified research — Phase 321 (2026-11-12 UTC)

- GitHub Actions [run 43177940904](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43177940904) passed. [Artifact 13925636412](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43177940904/artifacts/13925636412), SHA-256 \`e45cab68d1ebe15248cc76bad70b015c8f0bd2052689c0690478bbca4526965c\`.
- Full join census: 317,267 Form 4/4-A accessions across six SEC quarterly archives; 317,243 matched the daily index on the bulk filed date, leaving 24 exceptions. The six archives contain 6,706 multi-owner accessions (2.11%).
- Stratified original-header sample: 48/48 identity checks passed; 42/42 independent issuer-path vs. owner-path hashes matched. Six same-path cases are not independent crosschecks.
- This establishes broad index-join coverage in the six selected archive quarters, not uninterrupted daily coverage or strict PIT for all accessions.

## Latest verified research — Phase 320 (2026-11-12 UTC)

- GitHub Actions [run 43176308146](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43176308146) passed **10/10 Phase 320 regressions** plus live SEC validation. [Artifact 13924636727](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43176308146/artifacts/13924636727), ZIP SHA-256 `995f114e641443df2f6f32bc8f8cc0509fbf7efa3aeef18cc3bfd7d940aef150`.
- Six Phase 294 bulk archives (2006Q1, 2012Q1, 2023Q1, 2023Q2, 2025Q3, 2026Q3) passed manifest SHA-256 and ZIP CRC checks; 317,267 Form 4/4-A rows in total.
- A deterministic non-probability sample of 72 accessions (12/quarter; 8 Form 4 + 4 Form 4/A) spans 72 distinct filing dates. All 72 were found on their exact bulk `FILING_DATE` SEC daily index; none required next-business-day fallback, none were missing, and all index form/date/issuer-CIK checks passed.
- 72 daily indexes (58,389,807 bytes) parsed as legacy fixed-width files: 354,742 rows after headers, 124,741 Form 4/4-A entity rows, 230,001 other-form rows ignored, 60,222 multi-entity accession instances, 19 exact duplicate rows collapsed, zero malformed rows, zero CIK/path mismatches and zero conflicting accession identities.
- 72/72 original headers reconciled on accession, form and filed date; all had ACCEPTANCE-DATETIME. Header CIK was a reporting owner in 66 cases and the issuer in six; all header and issuer CIKs were present in the index rows. **66/66 independent issuer-path vs. owner-path hashes matched**; six issuer/header same-path cases are reported separately, not counted as independent crosschecks.
- 21/72 acceptance timestamps were at or after 17:30 ET. Acceptance is not transmission commencement or exact first-public receipt. Retain only the conservative date-level rule: first full XNYS session strictly after the official filed/index date. Strict PIT remains closed.
- All 72 sampled accessions were single-owner. The six source archives contain 6,706 multi-owner accessions (2.11%), with up to ten owners; they require a separate stratified live-header audit. The sample is not a probability sample and is not a prevalence estimate.
- No returns, alpha, bootstrap/LOO, chronological OOS or holdout test. No raw SEC bytes uploaded, vendor contacted, data purchased, email sent, or production/universe/capital/parameter change. F80 remains frozen.

**Next gate:** the six-archive daily-index join census and the 24-case exception adjudication are complete. Resolve effective-dated issuer/listing/security/share-class identity, survivorship-aware universe coverage and transaction-level security mapping before any Form 4 event study.

- [Phase 320 report](PHASE320_SEC_BULK_TO_DAILY_INDEX_JOIN_AUDIT_2026-11-12.md)

**Open PR:** [#17 — Phase 313](https://github.com/jafelix81/NuevaEstrategia/pull/17) remains open, as do PRs #13–#16; 14 PRs are open in total. Phase 318/319 are independent research branches and were not merged.

## Latest verified research — Phase 319

- GitHub Actions [run 43170779986](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43170779986) passed **39/39** offline regressions plus live SEC validation. [Artifact 13922595355](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43170779986/artifacts/13922595355). No workflow remains active.
- Seven actual daily form indexes (2006-01-03, 2012-01-03, 2023-01-03, 2023-04-03, 2025-07-01, 2026-07-01, 2026-11-10) were downloaded. All seven use the legacy fixed-width layout, including the 2026 sample.
- Across the seven files: 19,198 Form 4/Form 4/A entity rows encountered; 19,195 retained after collapsing three exact duplicates; 9,356 multi-entity accessions; 22,783 other-form rows ignored; zero malformed rows, zero row-CIK/path-CIK mismatches, zero filed-date/index-date ordering violations and zero conflicting accession identities.
- Fourteen accessions (seven Form 4 and seven Form 4/A) were selected deterministically. All 14 original submission headers matched the index on accession, form, issuer CIK and FILED AS OF DATE; all had ACCEPTANCE-DATETIME. Every sampled accession had two entity CIK rows. The original header's CENTRAL INDEX KEY identified the issuer row. In six of fourteen cases, the first selected path was under a non-issuer CIK; the issuer path returned the identical payload SHA-256. The parser must preserve entity rows and must not assume the first row is the issuer.
- All 14 sample index dates equaled their filed dates. Four acceptance timestamps were at/after 17:30 ET and none at/after 22:00 ET. These are acceptance times, not transmission-start times; they do not establish an exact first-public receipt timestamp.
- The live run exposed and corrected a fixed-width parser weakness: legacy form types may contain spaces (e.g. DEF 14A, APP ORDR, CT ORDER, 1-A POS). The parser now extracts CIK/date/path from the right, then splits the form/company prefix. Fixed-width test fixtures with double-escaped newlines were also corrected.
- Raw SEC index and filing bytes were not uploaded. The artifact contains hashes, metadata and parsed crosschecks only. This is a deterministic format/path smoke sample, not a probability sample and not yet a bulk-archive coverage estimate.

## Latest verified research — Phase 318

- GitHub Actions [run 43169018518](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43169018518) passed 10/10 regressions. [Artifact 13921710493](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43169018518/artifacts/13921710493).
- All 280 Phase 316 N-PORT sample filings were re-adjudicated against the SEC master-index FILED AS OF DATE. Fourteen had acceptance dates shifted to a later filed date; all fourteen matched the next EDGAR business day (12 one-day shifts, two Friday-to-Monday three-day shifts). One additional filing was accepted after 17:30 ET but retained the same filed date.
- 17 CFR 232.13 keys the cutoff to when transmission commences, not ACCEPTANCE-DATETIME. The fourteen shifts are consistent with next-business-day treatment, not proof of transmission start. The same-date/after-17:30 case remains unresolved, not a rule violation. Use FILED AS OF DATE as a date-level anchor and, conservatively, allow strategy use only from the first full XNYS session strictly after it. [SEC guidance](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/determine-status-my-filing) · [17 CFR 232.13](https://www.ecfr.gov/current/title-17/chapter-II/part-232/section-232.13).

## Latest verified research — Phase 317 and 316

- Phase 316 expanded N-PORT to 280 deterministic hash-ranked filings across 56 quarter/form strata (2019Q4–2026Q3), five registrants per stratum and 212 distinct CIKs. This is a QA sample, not a probability sample.
- The sample contained 194 sign-concordant reported short rows in only two filings, with 173 unique CUSIPs, 174 ISINs and zero reported tickers. This is not a prevalence estimate. These are holdings snapshots, not executions; no effective-dated security crosswalk exists yet.
- Phase 317 verified 280/280 FILED AS OF DATE values against the SEC master index and rechecked repeatability. The N-PORT-P report-date-to-filed-date lag was median 57 days (n=140); N-PORT-P/A median 119 days, with 85/140 at least 90 days and 49/140 at least 180 days. These are report-date-to-filing-date lags, not amendment delays from an original parent.

## Current broad-source disposition

- **Form 4 / Form 4/A:** strongest public insider-event candidate. Phase 321 completed a 317,267-accession join census across six quarterly archives (317,243 filed-date index matches; 24 exceptions); Phases 322–324 corroborated 21 exceptions at date level and kept three quarantined. Historical issuer/security/share-class identity, survivorship-aware universe coverage and exact first-public timing remain incomplete. The historical issuer-CIK coverage audit was only 54.6% (2016Q1), 65.4% (2020Q1), 76.4% (2024Q1) and 83.3% (2026Q3), below the 95% admission threshold.
- **Form 4 RSS:** seven successful captures, 30/30 requests per capture, 1,040 unique initial accessions (1,022 Form 4 and 18 Form 4/A). No new accession has appeared in those seven captures. All 1,040 initial records remain left-censored; no real new-event first-observation interval has yet been validated. Latest capture: [run 43152333818](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43152333818), [artifact 13914172674](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43152333818/artifacts/13914172674).
- **N-PORT:** delayed holdings snapshots, not trade flow. The short-position rows lack tickers; issuer/security mapping and public-availability vintages are hard gates. Do not promote N-PORT to an event signal yet.
- **13F:** prior issuer/security mapping coverage was 70.43% (2016Q1), 81.73% (2020Q1) and 93.02% (2024Q1), below the 95% gate; no signal admission.
- **Options (Cboe Open-Close / trade-by-trade):** remains a candidate only if historical licensed data can be sampled and its PIT timestamps, universe coverage and costs validated. No data purchase or vendor contact.
- **FINRA short volume/short interest and ATS/OTC:** continue as separate hypotheses; no evidence in this run justifies promotion.
- **CFTC positioning and OCC:** remain contextual or parked until a security-level, timestamped hypothesis and adequate historical coverage are demonstrated.

## Next research gates

1. Build an effective-dated CIK-to-listing/security/share-class crosswalk with permanent IDs, ticker changes, symbol reuse, ADRs, mergers, delistings and relistings. IssuerTradingSymbol remains an as-filed issuer label, not a transaction-security key.
2. Validate broad survivorship-aware universe coverage and transaction-level mapping. No N-PORT or Form 4 event study until the identity, PIT and coverage gates pass.
3. Only after those gates, construct ex-ante event features and test incremental information versus frozen LTM/F80 using identical exposure/costs, chronological OOS, bootstrap and LOO.
4. Keep failed hypotheses archived; do not promote a source because it is labelled "smart money".

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No alpha/return, bootstrap/LOO or chronological OOS test was run in Phases 316–319; the holdout was not used. Production, universe, capital and parameters were not changed. No vendor was contacted, no data was purchased and no email was sent.

## Prior verified research — Phase 313

- GitHub Actions [run 43160004366](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43160004366) completed successfully. It passed 8/8 offline regression tests and re-read all 56 Phase 312 raw submissions, verifying 56/56 original SHA-256 hashes. [Artifact 13916694212](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43160004366/artifacts/13916694212).
- Root cause: SEC N-PORT submission headers use unclosed SGML tags. Phase 312's closing-tag regex missed header identifiers and incorrectly labeled 53 records XML_ONLY. Corrected Phase 313 result: series 53 MATCH / 3 MISSING_BOTH; classes 53 MATCH / 3 MISSING_BOTH; zero mismatches. The three missing-ID cases remain fund/CIK/name-level only.
- The 56-filing Phase 312 sample contains 176 sign-concordant short rows, all in two filings: 20 Otter Creek Long/Short Opportunity Fund rows in a 2022 NPORT-P/A and 156 Saba Capital Income & Opportunities Fund II rows in a 2025 NPORT-P. The report-to-filing lags are 64 and 60 calendar days. This is a small deterministic QA sample, not a representative prevalence sample.
- Those 176 rows contain 173 unique CUSIPs, 173 unique ISINs and 20 reported tickers. A direct string comparison against the preserved legacy 335-ticker list yields 6 matches and 14 non-matches; the 156 rows without tickers remain unknown. This is not PIT security coverage.
- Three CUSIPs occur in both sampled filings (NVIDIA, Tesla and Watsco), but these are different funds and report dates; do not interpret them as one fund's position persistence.
- SEC N-PORT is still a delayed registered-fund holdings snapshot, not trade flow. Public data sets are quarterly; only the third month of each fiscal quarter is public under the current regime. The 2024 monthly-public amendments were delayed to 2027/2028, and the February 2026 proposal is not an effective rule. No first-public timestamp or broad-universe security mapping is admitted.
- Next: resolve the original parent of the Otter Creek 2022 NPORT-P/A by scanning 2022 Q3 NPORT-P filings for registrant CIK 811030, report date 2022-07-31 and series S000043717. Then expand the stratified sample and build an effective-dated CUSIP/ISIN-to-security crosswalk before any event study.
- The first Phase 313 workflow attempt (43159947904) failed only because the cross-run artifact token expression was escaped. The expression was corrected; run 43160004366 passed. No new SEC request was made in either Phase 313 run.
- The Phase 310 purposive positive-control filings remain separate from the Phase 312 sample and must not be mixed into a prevalence estimate. Phase 21C's earlier Form 4 alpha hypothesis remains killed; no signal has been promoted.

## Strategy and governance

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No production, universe, capital, parameter or holdout changes.
- No return/alpha test, bootstrap, LOO or chronological OOS test has been run for N-PORT.
- No vendor contact, data purchase or email was made.
- Phase 312 PR #16 and Phase 311 PR #15 remain open/unmerged. Phase 313 PR #17 is open/unmerged. No PR was merged.

## Historical audit trail

## Latest verified research — Phase 309 (2026-11-12 03:01 UTC)

- Phase 309 corrected the SEC RSS collector's first-observation timestamp. New accession timestamps now use the earliest successful Atom page `poll_completed_at_utc` containing the accession; poll-start time, page offset and label are stored separately. Event intervals are measured from the previous complete-capture end to that response completion. An event timestamp before the prior boundary is invalidated.
- The original Phase 308 run used capture start as a placeholder for all 1,040 initial accessions. Those values were not actual observations. Phase 309 migrates them to `legacy_capture_started_at_utc`, nulls `first_observed_at_utc` and interval end, and marks the timestamp `legacy_capture_start_pre_response_not_observation`. The fifth-capture artifact confirms **1,040/1,040** placeholders quarantined. They remain left-censored.
- Final hosted run [43145246814](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43145246814) passed **54/54** regressions (14 Phase 308 + 14 Phase 306 + 8 Phase 305 + 11 Phase 304 + 7 Phase 303) and completed 30/30 live SEC requests. Artifact [13911053496](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43145246814/artifacts/13911053496), 206,644 bytes, SHA-256 `acbbf03bae44d7d07fff1666896ae8d8e2bed6da5d7310ac8a71f4c9c0f9e597`.
- Five consecutive complete snapshots have now been captured. Latest: 1,022 Form 4 accessions / 2,111 entity rows; 18 Form 4/A accessions / 36 entity rows; 1,040 unique accession keys. Zero new accessions, zero changed entity-row sets, zero missing accessions, zero structural errors and zero row-fingerprint conflicts. Gap from prior complete capture end to latest capture start: 3.666 minutes.
- No new accession arrived in the five snapshots. The new event-level timestamp path is covered by deterministic tests but has not yet been exercised by a live newly arriving accession. Continue the prospective capture; do not claim a non-left-censored live interval yet.
- The migration-specific snapshot override forced a durable repository commit despite the same-day snapshot already existing: [ledger commit 1431ab323f37382fc9c6480e266db676b8afeee3](https://github.com/jafelix81/NuevaEstrategia/commit/1431ab323f37382fc9c6480e266db676b8afeee3). The five-capture migrated ledger is now committed; cache eviction cannot revert the branch file to the old pre-response placeholders.
- Reports: [Phase 309](PHASE309_SEC_RSS_EVENT_LEVEL_OBSERVATION_BOUND_CORRECTION_2026-11-12.md) and [Phase 308 capture ledger](PHASE308_SEC_RSS_PROSPECTIVE_CAPTURE_2026-11-12.md).
- No strict PIT admission, alpha/return test, bootstrap/LOO or chronological OOS. Holdout unused. `F80_TOP20_PARTIAL50_BASELINE_C20`, production, universe, capital and parameters unchanged. PR #13 and #14 remain open and unmerged; no new PR, email or vendor purchase.

## Prior verified research — Phase 307 (2026-11-12 02:34 UTC)

- Final run [43142273073](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43142273073) passed 48/48 regressions and 37/37 live SEC Atom requests. Artifact [13910211291](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43142273073/artifacts/13910211291), 155,654 bytes, SHA-256 028c6af605e771fd3362b269f509b09ab210d66ece1d1b328421fa0b6ff010d0.
- **owner=only passed** the ownership-form isolation, owner=exclude negative-control and page-zero accession-preservation tests. It returned 2,111 exact Form 4 entity rows / 1,022 accessions plus 36 Form 4/A prefix spillovers. Form 4 reached the current-feed tail at start=2,080 (final page 67 rows), with 26/26 ordered overlaps and stable page-zero recheck. Form 4/A returned 36 rows / 18 accessions in one page and also passed its recheck.
- No non-ownership forms appeared under owner=only; the only non-target token in type=4 was 4/A. owner=exclude returned zero exact Form 4/4/A accessions. The include control preserved the same 50 Form 4 accessions on page zero but contained 54 non-target rows across sampled offsets 0,80,320,400.
- **Decision:** use owner=only for prospective SEC Form 4/4-A capture, with exact form-token separation and accession-level reassembly. Preserve raw responses/hashes and first-observation intervals. Do not equate Atom updated with first-public time.
- Phase306 partial-page overlap expectation was corrected and regression-tested (14 tests). No strict PIT admission, return/alpha, bootstrap/LOO, chronological OOS or holdout test. F80, production, universe, capital and parameters unchanged. No PR/merge, email or vendor purchase.

## Prior verified research — Phase 306 (2026-11-12 02:26 UTC)

- Final Phase 306 run [43141258597](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43141258597) passed 39/39 regressions (13/8/11/7 across Phases 306/305/304/303) and completed 53/53 live SEC Atom requests. Artifact [13910016050](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43141258597/artifacts/13910016050), 225,439 bytes, SHA-256 1930481f22dae87525273ba028901df5ec0e10009c8b1edbffef4783c399720c.
- Form 4 type=4, owner=include: 50 contiguous pages, starts 0–3,920, count 100/step 80. The 4,020-position cap was reached with the last page full, so the Form 4 current feed remains **incomplete/capped**, not a complete snapshot. Exact-form filtering found 979 accessions / 2,025 entity rows; 1,939 unique non-target rows remained, including 1,510 424B2 rows. Target Form 4 rows were 51.1% of unique raw rows in the scanned window.
- All 49 adjacent 20-row overlaps matched in order after preserving duplicate rows; the page-zero recheck was identical. Zero row-fingerprint conflicts and zero target structural errors. 250 accessions spanned multiple page windows and 22 had different entity-row subsets across windows; reassemble by accession.
- The preliminary set-based overlap checker falsely flagged 19/20 where an exact duplicate Filer row reduced set cardinality. Raw-page inspection proved the ordered 20-row sequence was identical. The final implementation now compares ordered signatures, normalizes Filer role/CIK, and separately counts 65 within-page duplicates and 971 row identities repeated across pages.
- Form 4/A type=4/A, owner=include: one 36-row page / 18 accessions, followed by an empty page; page-zero recheck stable; zero target structural errors. This is only a current-snapshot observation.
- **Decision:** do not claim complete Form 4 feed coverage and do not admit strict PIT. Next test owner=only semantics to reduce the 4-prefix contamination, with exact form-token and negative-control checks. Then design prospective first-observation capture. Atom updated is still not first-public time.
- No return/alpha, bootstrap/LOO, chronological OOS or holdout test. F80, production, universe, capital and parameters remain unchanged. No email, vendor purchase, PR or merge.

## Prior verified research — Phase 302 (2026-11-12 00:33 UTC)

- Phase 302 [run 43127646850](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43127646850) passed 48/48 regression tests across Phases 153/299/300/301/302 and downloaded 71/71 SEC submissions plus 121/121 daily `form` indexes (90,998,369 bytes); all 71 accession windows were complete and identity-matched.
- All 71 earliest observed daily-index dates equaled the filing date. Among 24 unique original/amendment candidate pairs, 23 had the parent on an earlier index date and one shared a date (intraday order unresolved); eight ambiguous parent sets remain unassigned.
- Exact acceptance-time thresholds from the preserved artifact: 19/71 at or after 17:30 ET, 14/71 at/after 18:00, 7/71 at/after 20:00, 1/71 at/after 21:30, and 0/71 at/after 22:00. SEC rules specify a 17:30–22:00 same-day treatment for Forms 3/4/5; EDGAR closes at 22:00, so the next sample should target the late window and next-business-day rollovers—not impossible after-22:00 acceptances. See the [Phase 302 report](PHASE302_FORM4A_DAILY_INDEX_PAC_CLOCK_AUDIT_2026-11-12.md) and official SEC [filing-status guidance](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/determine-status-my-filing).
- This remains a date-granular knowledge bound, not exact first-public time or strict PIT. Phase 302 did not capture actual PAC `.pc`/Feed/Oldloads events; its correction chronology is Form 4/A only. No return/alpha/OOS/bootstrapping/LOO or holdout test. F80 and production controls remain frozen.

## Earlier verified research — Phase 300 (2026-11-11 22:59 UTC)

- Phase 299 SEC source capture [run 43115460066](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43115460066) downloaded 90 unique original/amended EDGAR complete submissions for a stratified sample of 46 Form 4/A candidate pairs. All 90 raw files and SHA-256 hashes are preserved in artifact [13898356586](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43115460066/artifacts/13898356586). All 90 XML documents parsed and their header/XML accession, form, filing date, issuer CIK and reporting-owner sets matched the bulk archive.
- Phase 300 offline XML-to-bulk reconciliation [run 43116245184](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43116245184) passed 6 new tests plus 6 Phase 299 and 17 Phase 153 regressions. Artifact [13898537038](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43116245184/artifacts/13898537038).
- **46/46** sampled candidate links were corroborated by issuer identity, reporting-owner overlap, amendment XML dateOfOriginalSubmission matching the candidate parent's filing date, and parent-before-amendment acceptance chronology. This remains metadata corroboration, not an authoritative accession foreign key.
- After normalizing dates to ISO and numeric values to the SEC bulk archive's two-decimal precision, 80/90 documents match the full transaction signature; 88/90 match core transaction fields after excluding only NATURE_OF_OWNERSHIP footnote association and TRANS_TIMELINESS metadata. All 90 Table I/II row counts match. Eight documents differ only in those footnote/timeliness fields (six NATURE_OF_OWNERSHIP, two TRANS_TIMELINESS).
- Two documents, both sides of candidate pair P299-022 (accessions 0001474427-12-000001 and 0001474427-12-000002), have derivative-table field-placement discrepancies between bulk and XML. Quarantine those derivative rows; the pair is also multi-owner/partial-overlap, so transaction-to-individual-owner attribution is unresolved.
- Pair-level: 45/46 pairs have both original and amendment filings matching on core transaction rows; 38/46 match full rows; core bulk/XML amendment-difference summaries agree for 46/46. The sample is purposive/stratified, not a prevalence estimate.
- Phase 299's first 3/90 full-row comparison is superseded: it did not normalize bulk DD-MMM-YYYY dates to XML ISO dates or account for the bulk archive's two-decimal numeric precision. Phase 300 corrected this using the preserved raw XML; no raw data was overwritten.
- No return/alpha/OOS/bootstrapping/LOO or holdout test. Strict PIT not admitted; acceptance chronology is not exact first-public availability. F80, production, universe, capital and parameters remain unchanged; no PR merged.

**Next Form 4 gates:** expand XML validation to an intermediate era and ambiguous/no-candidate amendments; preserve footnote/timeliness fields; quarantine derivative mapping exceptions or use XML-first parsing; resolve effective-dated issuer/security identity and owner attribution; complete the Phase 281 daily-index knowledge clock before any signal test.

## Latest verified correction — Phase 297 (2026-11-11 20:11 UTC)

- Hosted workflow [43094005689](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43094005689) passed; 6 deterministic tests passed and metadata artifact [13889458408](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43094005689/artifacts/13889458408) is present.
- Phase 296's conservative Form 4 cohort omitted the transaction-level `TRANS_FORM_TYPE=4` condition already required by the Phase 271 Table I contract. The 15,590-row cohort included 115 type-5 rows. Corrected cohort: **15,475 rows**, 10,997 accessions, 3,226 issuer CIKs and 6,677 reporting-owner CIKs.
- The 115 excluded rows occur across 97 accessions, 42 issuers and 70 owners; these gross counts overlap with valid type-4 rows, so net identity reductions are smaller.
- AFF10B5ONE status in the corrected cohort: 6,963 false, 201 true, 8,311 unknown. Unknown remains unknown. The gate uses actual filing date from 2023-04-01, not quarter label.
- Versioned Phase 271 explicit-open-market footnote screen reproduced 413 rows across the six purposive quarters; 365 also have positive price and shares. This remains text evidence only, not proof of discretionary intent or alpha.
- No returns, strict PIT, bootstrap/LOO, OOS or holdout test. F80, production, universe, capital and parameters remain unchanged.

**Frozen baseline:** `F80_TOP20_PARTIAL50_BASELINE_C20`  
**Legacy holdout:** `CONSUMED_NOT_PRISTINE`; never reuse.  
**Economic result:** no new Smart Money signal has demonstrated incremental, cost-adjusted OOS edge.

## Latest verified results — Phases 295–296 (2026-11-11 19:31 UTC)

- **Phase 295 passed:** 11/11 offline tests; 18/18 SEC complete-submission headers reconciled; 18/18 accession identities matched their first observed daily-index rows; 18/18 first index dates equaled the bulk filing date. The sample is purposive, not random. Exact first-public timestamp remains unverified.
- 57/88 requested daily index files downloaded and parsed; the other 31 were HTTP 403 on 27 weekends and four U.S. federal holidays. Zero parser errors occurred in the 57 retrieved files.
- SEC acceptance time was after 16:00 ET for 15/18 accessions, after 18:00 ET for 5/18, and after 20:00 ET for 2/18. The daily index date is date-granular and cannot establish the exact public-availability time. Use no earlier than the next full XNYS session after acceptance for any future test.
- **Phase 296 data-quality audit:** the six Phase 294 raw archives contain 317,267 Form 4/4-A accessions. 310,561 (97.89%) have one reporting owner; 6,706 have multiple owners. A conservative candidate filter leaves 15,590 direct, positive-price/positive-share, non-derivative P acquisitions in original Form 4 filings with one owner and a 0–2 calendar-day transaction-to-filing lag, across 11,088 accessions, 3,243 issuers and 6,728 owners. This is feasibility, not alpha.
- SEC Form 4 transaction code P explicitly includes **open-market or private purchases**. Footnotes, 10b5-1 status, delayed/amended filings, multiple-owner attribution and effective-dated issuer/security identity must be handled before any signal test. No strict PIT, return test, alpha, bootstrap/LOO or OOS result has been produced.
- `SEC_CONTACT_EMAIL` is operational in Actions. It is used only in the SEC User-Agent contact string; no email was sent by the workflow, and no inbox check is required for this data pull.


## Earlier material research result — Phase 281

SEC EDGAR's historical daily `form.YYYYMMDD.idx` archives provide a conditional route to reconstruct a conservative daily public-dissemination date for Form 4 accessions. SEC documentation says daily indexes extend from 1994Q3 to present, list form/CIK/date/path, are built nightly, and prior daily indexes are not rewritten by later-business-day post-acceptance corrections. Full and quarterly indexes are rebuilt weekly and do incorporate later PAC changes.

**Proposed Form 4 knowledge clock:** join each Phase 279 bulk-dataset accession to all historical daily form-index sightings; use the earliest verified index date; execute no earlier than the close of the next full XNYS session. Do not fall back to FILING_DATE or acceptance time when the index join is missing. This is a conservative daily-PIT candidate, not yet strict PIT: no raw index bytes have been downloaded, same-day PAC handling is not fully measured, the SEC does not publish an exact first-public timestamp, and owner/security identity remain open.

- [Phase 281 report](PHASE281_SEC_DAILY_INDEX_FIRST_PUBLICATION_PIT_FEASIBILITY_2026-11-11.md)
- Official sources: [SEC EDGAR access and daily indexes](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data), [SEC timestamp FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions).



## Phase 282 — SEC PDS public-clock adjudication

The SEC's current PDS system page says PDS is a paid subscriber service and that, following the 2025-05-19 system update, filings are available on sec.gov before they are made available to PDS subscribers. The inspected historical 2014 PDS specification documents EDGAR receipt/acceptance/build fields and PAC timestamps, but ordinary `.dissem` files and the daily EOD filename list do not provide a per-filing first-public timestamp. The 2014 specification is not assumed to represent every field in the current 2025 ZIP.

**Decision:** PDS is not a superior public-availability clock and no paid subscription/contact is justified. Retain the Phase 281 historical daily `form` index as the primary conservative Form 4 knowledge-date candidate; PDS may be only an optional acceptance/PAC cross-check if lawful existing archive bytes become available. No PDS or SEC raw bytes were downloaded, no automated SEC request was sent, and no alpha test was run.

- [Phase 282 report](PHASE282_SEC_PDS_VS_DAILY_INDEX_PUBLICATION_CLOCK_AUDIT_2026-11-11.md)
- Official SEC source: [PDS system and 2025 ordering change](https://www.sec.gov/oit/announcement/public-dissemination-service-system-contact.html).

## Phase 279 — SEC Insider Transactions bulk history

- SEC lists 83 quarterly archives from 2006Q1 through 2026Q3; listed ZIP sizes sum to about 887.43 MB.
- Eight documented tables include submissions, owners, transactions, holdings, footnotes and signatures.
- Critical issues: SUBMISSION has date-only FILING_DATE; NONDERIV_TRANS lacks owner CIK; transaction table lacks permanent security/CUSIP; AFF10B5ONE varies by archive era; P is not sufficient proof of open-market execution.
- Phase 279's documentation gate passed 17/17 deterministic tests, but no ZIP bytes were downloaded and no alpha test was run.
- [Phase 279 report](PHASE279_SEC_INSIDER_TRANSACTIONS_BULK_HISTORY_AND_PIT_FEASIBILITY_2026-11-11.md).

## Latest verified GitHub state — 2026-11-11 08:05 UTC

- Latest 100 Actions runs: **97 success, 3 cancelled, 0 failed, 0 queued/in-progress**. No workflow was duplicated.
- PR #14 head: `816662c125d626542763a1d0d034e3aaf6cd8119`; **23/23 check-runs successful**. It remains open, mergeable and stacked on PR #13. [PR #14](https://github.com/jafelix81/NuevaEstrategia/pull/14).
- PR #13 head: `61f737f18b410bc6d85b8c56ed96bc1fd9c130f5`; open/mergeable, with **zero check-runs registered on that SHA**. [PR #13](https://github.com/jafelix81/NuevaEstrategia/pull/13).
- Latest Phase 272 hosted run [42982871024](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42982871024) passed. The job log preserves the Phase 272 status gate; metadata-only artifact [13838231849](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42982871024/artifacts/13838231849), SHA-256 `459cea1eb615d83efb618310ff15d63a5fd655cddfe3df7b29934c31d566877d`.
- Latest Phase 278 targeted follow-up [42982870960](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42982870960) passed **20/20 tests** and re-fetched 147,725 rows over 30 pages. Two BQ/T2 candidate-key groups remain conflicting; no row was selected or summed. Artifact [13838767377](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42982870960/artifacts/13838767377), SHA-256 `22cfdeaed6616d487bf403d459a0778b5f5a86516c30656a1ea1bda5235179e8`.
- Phase 279 bulk-history gate passed 17/17 on the current PR head; Phase 276 security gate passed. The 31-workflow / 103-action inventory still has no mutable/unverified action refs or missing explicit permissions.
- Branch inventory: **134 branches** (100 on page 1, 34 on page 2). No CFTC capture was activated and no workflow was manually dispatched.
- No PR was merged. Do not merge either PR without explicit authorization.

## Source dispositions

| Source / line | Current disposition |
|---|---|
| FINRA short flow Phase 20C | Weak, incomplete and not strict PIT; no promotion; do not retune the consumed sample |
| FINRA short interest Phase 267 | Pagination/date-availability defects; no strict PIT panel |
| FINRA ATS/OTC Phases 264/277/278 | Context-only; later revisions and two unresolved duplicate-grain conflict groups; do not sum or choose arbitrarily |
| SEC Form 4 | Highest-priority historical candidate after Phase 281 daily-index route; owner attribution and effective-dated security identity still open |
| SEC 13D/G | Extensive event, amendment and identity audits; no broad issuer/security panel admitted |
| SEC 13F / N-PORT | Delayed context only; acceptance, amendment, CUSIP/security mapping and PIT issues remain |
| Form 144/Form 4 | Document-linkage and conditional placebo results only; no market-execution or return edge established |
| Cboe Open-Close | One C1 20% EOD sample date reprocessed; feature construction works, but no multi-date PIT/vintage proof |
| Cboe options quotes / sentiment / TradeFlow / OI | Conditional candidates; no full licensed historical sample with first-receipt and effective-dated identity admitted |
| CFTC BPR/TFF | Market-regime context candidate; prior walk-forward quarantined for label-maturity defects; prospective capture workflow remains research-branch only |
| Form SHO / SLATE | Future regulatory sources only; not a current historical public panel |

## Next research gates

1. Configure the authorized GitHub Actions secret `SEC_CONTACT_EMAIL` before automated SEC retrieval. Do not guess an address or send programmatic requests without the declared User-Agent.
2. Run the Phase 281 sample gate across the six Phase 279 quarters: download only the needed daily `form` index files, validate accession/path parsing, preserve hashes, and reconcile sampled index dates with acceptance headers and original Form 4/Form 4/A content.
3. Measure missing-index, duplicate-sighting, same-day PAC, missing-content and after-hours rates. Test Oldloads only as a targeted fallback; do not bulk-download all daily Oldloads archives.
4. Resolve joint/group transaction-owner attribution and effective-dated issuer/security-class identity, including inactive/delisted names.
5. Only after all data gates pass, preregister a new chronological test against frozen LTM/F80 with identical exposure/costs, label-maturity embargo, date/issuer/owner-clustered bootstrap, LOO and multiplicity controls. Use a new prospective holdout.

## Controls

No returns, alpha, economic optimization, bootstrap/LOO or fresh independent OOS evidence has been produced by Phases 279–281. No holdout was used. No vendor was contacted, no data purchased, no terms accepted, no PR merged, no production/universe/capital/parameter changes, and no F80 change occurred. No CAGR target or minimum/maximum holding period is imposed.


## Phase 283 — SEC daily-index parser contract (2026-11-11)

Implemented an offline parser/ledger for the conditional Phase 281 SEC daily-index route. It validates Form 4/Form 4-A accession paths, CIK consistency, filing-date/index-date consistency, duplicate/conflicting rows, multi-date accession sightings and the next full XNYS session close using timezone-aware calendar inputs. Synthetic tests are wired into the existing PR workflow. No SEC requests or raw index downloads were made; live format/PAC validation, six-quarter joins, owner attribution and effective-dated security identity remain open. See research/PHASE283_SEC_DAILY_INDEX_PARSER_CONTRACT_2026-11-11.md.

## GitHub verification correction — 2026-11-11 10:35 UTC

- Latest 100 Actions runs: 97 successful, 3 cancelled, 0 failed and 0 queued/in-progress. The three cancellations were Phase 258, Phase 259 and Phase 260; no active run was duplicated.
- PR #14 remains open/mergeable and stacked on PR #13. Before Phase 283 files are added, its head is 1f33ecb237521e4dda9101f1742862c2f18f2bb5; the 22 registered check-runs on that SHA all completed successfully.
- PR #13 remains open/mergeable with zero check-runs registered on head 61f737f18b410bc6d85b8c56ed96bc1fd9c130f5.
- Latest Phase 231 raw-row reparse run 42987915103 passed. Metadata-only artifact 13839449799, SHA-256 8127533c1d1fc1835cf6ef7718a2558b0fb6787fc1f8d6900af3e982ee86aa65.
- Phase 279 passed 17/17 tests in run 42987914989; artifact 13840302271, SHA-256 13be9e426f464d15a3d2135148c5df87de9b2685e2390b19da5565a655938b4d.
- Phase 278 passed 20/20 tests and reconciled 147,725 rows / 30 pages in run 42982870960; its two unresolved duplicate-grain conflict groups remain quarantined. Artifact 13838767377, SHA-256 22cfdeaed6616d487bf403d459a0778b5f5a86516c30656a1ea1bda5235179e8.
- Phase 272 passed in run 42982871024; artifact 13838231849, SHA-256 459cea1eb615d83efb618310ff15d63a5fd655cddfe3df7b29934c31d566877d.
- Branch inventory is 134 branches (100 on page 1, 34 on page 2). No PR was merged; F80, production, universe, capital and holdout remain unchanged.

Phase 283 is an offline parser contract only. Do not describe parser tests as passing until the final PR workflow run is inspected.


## Phase 283 refinement — delayed Form 4 index-date handling (2026-11-11)

A code review found that the original parser required `Date Filed == form.YYYYMMDD.idx`, making its advertised multi-date accession ledger unreachable for a later daily-index sighting. This was too strict for the SEC's documented next-business-day dissemination of some Forms 3/4/5 filed after 10 p.m. ET.

The parser now quarantines only index dates before `Date Filed`, retains later index sightings with explicit lag days, and never backdates a later-only sighting to FILING_DATE. Synthetic tests cover the delayed sighting, multi-date aggregation and no-backdating rule. Raw SEC bytes, actual late-sighting frequency and PAC behavior remain unverified.

This is a data-contract correction, not a new source or alpha result. SEC_CONTACT_EMAIL remains unconfigured; no SEC request was made. F80 and all production/holdout controls remain unchanged.


## Phase 284 — SEC delayed-sighting correction (2026-11-11)

The daily-index ledger now retains later index sightings of a Form 4 accession with explicit lag days and never backdates a later-only sighting to FILING_DATE. Synthetic regression suite passed 17/17 in run 43019575009; artifact 13855150143. Real SEC bytes/PAC behavior remain unverified. No SEC request was made.

## Phase 285 — FIS SLD and UREF source admission (2026-11-11)

Documented FIS Astec Securities Lending and Nasdaq UREF as candidates/controls, not admitted signals. Run 43030407555: 13/13 metadata-audit tests passed; artifact 13859064142. No data was purchased or downloaded.

## Phase 286 — Nasdaq NOTO/NOP feasibility (2026-11-11)

Documented NOTO EOD/intraday and NOP as options-flow candidates. Run 43031307177: 12/12 metadata-audit tests passed; artifact 13860368810. NOTO is one exchange only; participant classes are not beneficial-owner identities; intraday snapshots are cumulative. No data was purchased or downloaded.

## Phase 287 — Nasdaq ISE/PHLX options and TotalView-ITCH/NOII feasibility (2026-11-11)

Added research/PHASE287_NASDAQ_OPTIONS_TRADE_OUTLINE_AND_ITCH_NOII_FEASIBILITY_2026-11-11.md on branch phase287-nasdaq-options-and-itch-source-feasibility (documentation-only commit c4ace566a871c0b6b042da46ea46e3b1e761e09d). ISE Trade Outline EOD has history from Jan 2006 but the full-history ad-hoc cost is approximately $150,000 at current list rates; a first-time one-month EOD trial is documented. PHLX PHOTO history begins Jan 2009, with a free Jan-Jun 2014 sample formally documented but current retrieval path unverified. Nasdaq TotalView-ITCH/NOII offers high-resolution order/auction microstructure, but full SFTP access requires credentials, files are large, the public archive is sparse samples, and MPID attribution is partial. No raw sample was obtained, no subscription/contact/purchase was made, and no model test was run.

## Current verification — 2026-11-11 14:24 UTC

- PR #14 remains open/mergeable at head 6dedb088d7289ca5155a319b5f88155c2d431be3. Its 23 associated GitHub Actions runs are all completed successfully; no queued/in-progress run was found. The latest Phase 285 run completed 13/13 tests and its artifact 13859064142 is present and unexpired.
- Phase 286 run 43031307177 completed successfully with one metadata-audit job and artifact 13860368810 present and unexpired.
- PR #13 remains open/mergeable at head 61f737f18b410bc6d85b8c56ed96bc1fd9c130f5 with zero associated workflow runs/check-runs on that SHA.
- Phase 287 branch exists; no PR was opened and no merge was performed.
- SEC_CONTACT_EMAIL remains unconfigured; no SEC request was made. No Nasdaq trial, data purchase, or vendor contact was initiated.
- No raw new source data, return test, alpha, bootstrap/LOO or independent OOS result has been produced by Phases 284–287. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; production, universe, capital, parameters and holdout are unchanged. No CAGR target or holding-period constraint is imposed.


## Phase 288 — SEC Form 13F PIT feasibility (2026-11-11)

Added research/PHASE288_SEC_13F_HOLDINGS_PIT_COVERAGE_AMENDMENT_AUDIT_2026-11-11.md on branch phase288-sec-13f-pit-coverage-amendment-audit (report commit 84db69351977302c10f2721796e4f552696c1a4b). SEC 13F structured data is public/free, with quarterly packages from 2013 Q2 / July 2013 through August 2026. It includes accession numbers, filing date/type, CIK, report period, amendment/restatement/addition flags, confidential-treatment metadata, CUSIP, optional FIGI, shares/value, put/call and manager-discretion fields. It is a promising slow-frequency ownership source, but only a candidate: 45-day reporting lag, no shorts, incomplete Section 13(f) universe, confidential omissions, amendments, and CUSIP/FIGI mapping require strict PIT reconstruction. SEC Q3 2026 filings are due 2026-11-16; no Q3 holdings are available as of this run. No raw ZIP bytes were obtained because the runtime cannot resolve external SEC hosts; SEC_CONTACT_EMAIL remains unconfigured. No backtest or signal test was run.

## Current verification — 2026-11-11 14:24 UTC

- PR #14: head 6dedb088d7289ca5155a319b5f88155c2d431be3; 23 associated Actions runs, all completed successfully; no active run was found.
- Phase 285 run 43030407555: metadata-audit job succeeded, 13/13 tests; artifact 13859064142 present and unexpired.
- Phase 286 run 43031307177: metadata-audit job succeeded, 12/12 tests; artifact 13860368810 present and unexpired.
- PR #13: head 61f737f18b410bc6d85b8c56ed96bc1fd9c130f5; zero associated workflow runs/check-runs.
- Phase 287 and Phase 288 are documentation/source-audit branches only; no PRs were opened and no merges were made. No workflow was started by these documentation commits.
- No raw data was acquired from FIS, UREF, NOTO, ISE, PHLX, NYSE Open-Close, Nasdaq ITCH/NOII or SEC 13F. No vendor was contacted and no paid data/trial was requested.
- SEC_CONTACT_EMAIL remains the only previously identified human configuration blocker for automated SEC downloads. No SEC request was made.
- No model test, alpha estimate, bootstrap, LOO or independent OOS result has been produced by Phases 284–288. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; production, universe, capital, parameters and holdout are unchanged.


## Phase 289 — SEC 13F re-entry decision and source-priority correction (2026-11-11)

**Decision: keep 13F parked for broad-universe stock selection; defer raw ZIP acquisition until historical identity coverage improves.** Phase 22C already found only 301 current candidate mappings for the 335-name frozen universe. Its historical matches were 212/301 (70.43%) in 2016Q1, 246/301 (81.73%) in 2020Q1 and 280/301 (93.02%) in 2024Q1. Against the full 335-name universe these are 63.28%, 73.43% and 83.58%, respectively. The direct report-date CUSIP/common-equity route had a 54.8% minimum in 2016Q1. Phase 166's 83.18% is a 13(f)-eligibility match in a separate 13D/G sample, not 13F holdings coverage.

Phase 205's ten accessions are purposive edge cases, not a prevalence sample: four original reports were accepted 44–48 days after quarter-end; six amendments were 60–1,137 days after quarter-end (median 361.5 days); five of ten filing dates differ from acceptance calendar dates. The findings reinforce accession-level event clocks and append-only restatement/add-only amendment state, but do not establish population rates or alpha.

Source priority remains: (1) Form 4 bulk + daily-index real-data sample; (2) N-PORT direct short-equity sample as a distinct preregistered registered-fund hypothesis; (3) 13F only after effective-dated security identity and broad-universe coverage pass; (4) paid options/lending sources only after authorized sample/license and cost gates. No synthetic 13F workflow should be added until real bytes reveal a concrete issue.

- [Phase 289 report](PHASE289_SEC_13F_REENTRY_DECISION_AND_SOURCE_PRIORITY_2026-11-11.md) on branch `phase289-sec13f-reentry-adjudication`.
- Latest 30 Actions runs checked: 24 completed successfully, 6 cancelled, zero failed, zero queued/in-progress. Latest run 43031307177 (Phase 286) succeeded; its metadata-only artifact 13860368810 is present and unexpired. No workflow was duplicated.
- PR #14 head remains `6dedb088d7289ca5155a319b5f88155c2d431be3`, open/mergeable, 23/23 check-runs successful. PR #13 head `61f737f18b410bc6d85b8c56ed96bc1fd9c130f5`, open/mergeable, zero check-runs on that SHA.
- Phase 278 latest targeted run 43030407560 passed 20/20 tests but still found 147,725 rows, 30 pages and two conflicting duplicate-grain groups; no rows were selected or summed. Artifact 13861545967 is present and unexpired.
- Phase 231 run 43030407294 passed the raw-row reparse gate: 115,617 populated rows; 112,313 unambiguous valid rows; 3,304 ambiguous expiration rows quarantined. No PIT or alpha admission. Artifact 13860267856 is present and unexpired.
- Branch inventory before this Phase 289 branch was 137 (100 on page 1, 37 on page 2); Phase 289 adds one documentation-only branch. No PR or merge was created.
- The repository state records `SEC_CONTACT_EMAIL` as not configured; no secret was inspected or changed and no SEC request was made.

No raw data, return test, bootstrap/LOO, OOS result or holdout use occurred. F80, production, universe, capital and parameters remain unchanged. The legacy holdout remains consumed and unavailable for reuse.


## Phase 290 — N-PORT / FINRA output reconciliation (2026-11-11)

- Inspected the actual Phase 27O run 39493106882 and artifact 12296499022 (SHA-256 `c8207cd99b5bc80be730db89da62ced1298a18af0330b11335e41864fca4478b`). All eight snapshots have blank `balance_units`, zero tickers with positive shares, and all seven transitions have `n_ranked=0` with no forward returns. This confirms the Phase 247 `UNITS` versus official flattened `UNIT` defect in the real historical output. Quarantine Phase 27N/27O; this is not evidence for or against long accumulation alpha.
- The Phase 27O/27K scripts hard-code `research@example.com` in the SEC User-Agent. Phase 27O logs confirm that eight SEC archives were downloaded historically. Do not reuse that placeholder. No new SEC request was sent; automated SEC retrieval remains blocked until an actual authorized contact is configured in `SEC_CONTACT_EMAIL`.
- Reconciled Phase 20C run 40098425254 / artifact 12562171831 (SHA-256 `c15f75340bdedfbb37c82f79bb563a450dd1da11989d09e18bb745d93b7d3a5c`). All 1,382 XNYS sessions required by the run's signal lookback windows had FINRA CNMS files; the 638 HTTP 403 dates were weekends, XNYS closures or pre-source-start dates, not a 31.6% trading-session gap.
- Phase 20C's 12 pseudo-OOS dates compare four blocked and four replacement names per date. Mean replacement-minus-blocked: +0.141% (5D), -1.686% (10D), -0.858% (20D); positive dates 5/12, 3/12 and 5/12. Factor/direction selection is unstable. All exploratory date-level 95% intervals cross zero; no costs or cluster bootstrap/LOO were included.
- Phase 20C uses same-day FINRA data and starts forward returns at the same day's close without a verified first-public timestamp. Treat as not strict PIT; no promotion. Any revisit must enter no earlier than the next full XNYS session unless source receipt timing is proven.
- Phase 278 remains context-only: 147,725 rows, 30 pages and two unresolved conflicting duplicate-grain groups; do not sum or select those groups.
- Current Actions verification: latest 100 runs = 67 success, 33 cancelled, zero failed and zero active/queued. PR #14 remains open/mergeable with 23/23 checks successful; PR #13 remains open/mergeable with zero checks on its current SHA. Branch count was 138 before this Phase 290 branch; this documentation branch makes 139. No PR was opened or merged.
- [Phase 290 report](PHASE290_NPORT_FINRA_OUTPUT_RECONCILIATION_2026-11-11.md).

**Current decision:** Form 4 remains the first real-data priority after a valid SEC contact is configured; N-PORT direct-short remains a separate, unadmitted hypothesis; 13F remains parked; Phase 20C is not promoted pending next-session PIT correction and a stronger test. No holdout was used. F80, production, universe, capital and parameters remain unchanged.


## Phase 291 — N-PORT direct-short real public-filing positive control (2026-11-11)

A public SEC NPORT-P filing (accession 0001145549-24-071567; CIK 0001872253; series S000074017, Cromwell Long Short Fund) was inspected. It reports at least three explicit short U.S. common-equity positions: DAY (-4,447 shares), CLX (-1,920) and CDW (-1,115), each with negative USD value and negative percent of NAV. The filing was accepted 2024-11-22 12:10:57 ET for report date 2024-09-30; the conservative first full XNYS session after acceptance is 2024-11-25.

This exposed a real Phase 221 parser false-negative: the code required the descriptive ISSUER_TITLE to contain the literal words "Common Stock". The SEC filing uses issuer names such as "Dayforce Inc", while the structured fields identify the instrument as Equity-common / Corporate. The classifier now uses UNIT=NS + ASSET_CAT=EC + ISSUER_TYPE=CORP and leaves the title as descriptive metadata; non-finite balances fail closed. The old predicate rejected 3/3 actual rows; the corrected logic accepts 3/3. The 13 existing Phase 221 semantic cases were rechecked and pass; new tests cover the three real public rows and negative controls.

Important limit: the public SEC filing detail and EDGAR-rendered primary document were inspected, but raw XML/ZIP bytes were not downloaded or hashed. This validates a real filing row-classification path, not bulk-history coverage, series/security longitudinal identity, a PIT panel, or alpha. No return test, bootstrap/LOO, or holdout was run. SEC_CONTACT_EMAIL remains unconfigured; no automated SEC request was made.

- [Phase 291 report](PHASE291_NPORT_DIRECT_SHORT_PUBLIC_FILING_POSITIVE_CONTROL_2026-11-11.md) on branch `phase291-nport-public-short-positive-control`.
- Latest Actions inventory before this branch: 100 most recent runs = 67 success, 33 cancelled, zero failed, zero active/queued. PR #14 head 6dedb088d7289ca5155a319b5f88155c2d431be3 has 23/23 successful check-runs; PR #13 head 61f737f18b410bc6d85b8c56ed96bc1fd9c130f5 has zero check-runs. Phase 286, 285 and 278 logs/artifacts were inspected; all metadata/source-gate jobs succeeded but did not admit data or alpha. This new branch is documentation/parser correction only; no workflow was started.
- No PR opened or merge made. F80, production, universe, capital, parameters and holdout remain unchanged.


## Phase 292 — N-PORT direct-short classifier hardening (2026-11-11)

A review found the Phase 291 predicate did not fully preserve the preregistered Phase 219 row filter: it omitted U.S. investment-country validation, negative CURRENCY_VALUE/PERCENTAGE sign concordance, and row-level exact CUSIP/ISIN matching. The Phase 291 test commit used [skip ci] and had zero check-runs. Phase 292 adds these fail-closed gates, updates the 13 Phase 221 semantic fixtures, replays the three manually transcribed public SEC filing rows with all required fields, and adds five negative controls. A dedicated offline Actions workflow compiles/runs the tests and emits a metadata-only artifact. This remains a public rendered-document fixture, not raw XML parsing or a bulk-data/PIT admission.

- [Phase 292 report](PHASE292_NPORT_DIRECT_SHORT_CLASSIFIER_HARDENING_2026-11-11.md) on branch phase292-nport-short-classification-hardening.
- No SEC requests, raw bytes, hashes, return tests, bootstrap/LOO or holdout use. F80, production, universe, capital and parameters remain unchanged.


## GitHub Actions validation — completed 2026-11-11 18:05 UTC

Dedicated run [43074329311](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43074329311) completed successfully on commit `d20874ca28734d1d6ec05099eb51f877965b2e39`. Job `offline-classifier-audit` passed compilation, all three test modules and the final no-alpha/data-control gate.

- **26/26 tests passed**: 14 Phase 221 semantic tests, 3 Phase 291 public-filing controls and 9 Phase 292 hardening tests.
- Public rendered-document positive controls: 3/3.
- Negative controls: 5/5.
- Artifact: [13880167054](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43074329311/artifacts/13880167054), SHA-256 `321ef631c94d4a5a3b5909a07b7ddc1e497be2c2527ffc7a52a3aef9d5e6f3a2`.
- The artifact records raw XML bytes/hash, automated SEC requests, strict PIT admission, alpha, return tests, bootstrap/LOO, holdout use and all production changes as false; F80 remains frozen.

The validation is offline and fixture-based. It does not establish raw XML parsing, bulk-history coverage, first-public timing, longitudinal fund/security identity or economic predictability.


## Phase 293 — second-filer N-PORT public short controls (2026-11-11)

The hardened Phase 292 classifier was replayed against 23 selected, line-referenced U.S. common-equity short rows from ACAP Strategic Fund (CIK 0001467631, accession 0001145549-25-033457, report date 2025-03-31), a second registrant independent of the three Cromwell rows in Phase 291. Expected combined positive controls: 26 rows across two registrants and two report periods; Phase 292 negative controls remain 5. This is still a manually selected fixture sample; the ACAP filing has no EDGAR series ID in the fixture, and neither filing has raw bytes/hashes or first-public receipt verification. No PIT or alpha admission.

- [Phase 293 report](PHASE293_NPORT_SECOND_FILER_PUBLIC_POSITIVE_CONTROLS_2026-11-11.md) on branch phase293-nport-second-filer-public-positive-controls.
- Dedicated offline workflow runs the Phase 221/291/292/293 tests and emits a metadata-only artifact.
- No SEC requests, raw downloads, hashes, return tests, bootstrap/LOO or holdout use. F80, production, universe, capital and parameters remain unchanged.


## GitHub Actions validation — completed 2026-11-11 18:10 UTC

Dedicated run [43075250170](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43075250170) completed successfully on workflow-trigger commit `02d658aa82126a035aac32eadfe58bb5ee72f9a8`. Job `second-filer-audit` passed compilation, all four regression modules and the final cross-filer/no-alpha gate.

- **29/29 tests passed**.
- Second-filer ACAP selected positive controls: 23/23.
- Combined selected positive controls: 26 across two distinct registrants.
- Existing negative controls: 5/5.
- Artifact: [13879983178](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43075250170/artifacts/13879983178), SHA-256 `fdedf37b1d62674e114ae848e835f830feb39d700f3ca950b091955161b838f1`.

The artifact confirms the sample is non-exhaustive; raw XML/submission bytes and hashes, first-public receipt, longitudinal series identity, PIT admission, prevalence, alpha, return tests, bootstrap/LOO, holdout and production changes remain false. F80 remains frozen.


## Repository snapshot after Phase 293 (2026-11-11)

- Latest 100 Actions runs: 69 success, 31 cancelled, zero failed, zero queued/in-progress. No active workflow was duplicated.
- Phase 292 run 43074329311: success; 26 tests; artifact 13880167054, SHA-256 `321ef631c94d4a5a3b5909a07b7ddc1e497be2c2527ffc7a52a3aef9d5e6f3a2`.
- Phase 293 run 43075250170: success; 29 tests; 26 selected public positive rows across two registrants; five negative controls; artifact 13879983178, SHA-256 `fdedf37b1d62674e114ae848e835f830feb39d700f3ca950b091955161b838f1`.
- Branch inventory: 142. Phase 293 head `e12d7b8ff1ff2847a1a8e71296e599c562bf80bd`.
- PR #14 remains open on head `6dedb088d7289ca5155a319b5f88155c2d431be3` with 23/23 successful checks. PR #13 remains open on head `61f737f18b410bc6d85b8c56ed96bc1fd9c130f5` with zero checks on that SHA. No PR was opened or merged for Phases 291–293.
- SEC automated retrieval remains gated on a real authorized `SEC_CONTACT_EMAIL`; no secret was inspected or changed in these phases.

No raw SEC bytes, first-public receipt, broad-universe coverage, PIT panel, return test, bootstrap/LOO or alpha result was produced. F80, production, universe, capital, parameters and the consumed legacy holdout remain unchanged.


## Phase 294 — SEC Insider Transactions bulk archive raw sample and schema audit (2026-11-11)

- GitHub Actions successfully injected `SEC_CONTACT_EMAIL`; six sequential official SEC requests returned HTTP 200. The email value was not logged, stored or inspected.
- Six stratified raw archives downloaded, CRC-checked and SHA-256 hashed: 2006Q1, 2012Q1, 2023Q1, 2023Q2, 2025Q3 and 2026Q3. Total 72,767,570 bytes. All eight tables were present and all six passed the required schema/core-key/accession checks.
- Aggregate sample: 353,212 SUBMISSION rows; 308,940 Form 4 and 8,327 Form 4/A submissions (317,267 combined); 568,055 NONDERIV_TRANS rows; 377,553 REPORTINGOWNER rows; 766,389 FOOTNOTES rows.
- SUBMISSION schema differs by era: AFF10B5ONE absent in 2006Q1/2012Q1, present in 2023Q1 onward in the sample. Missing pre-field values remain UNKNOWN.
- SEC bulk FILING_DATE is `DD-MMM-YYYY`, not ISO; Phase 294 added explicit normalization. All 317,267 Form 4/4-A rows in the sample had valid accession and normalized date values.
- OWNER_SIGNATURE's documented two-field key is not unique: 1,107 repeated key rows across the sample (1,055 exact repeated rows; 52 same accession/name with different signature dates). This is a non-core-table warning. Do not deduplicate it on accession+name alone.
- 7,769 accessions in the sample have multiple REPORTINGOWNER rows. NONDERIV_TRANS lacks reporting-owner CIK; accession-only owner joins remain prohibited.
- Run [43083625013](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43083625013): 11/11 offline tests passed; six archives retrieved and schema gate passed. Artifact [13884014630](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43083625013/artifacts/13884014630), 72,791,924 bytes, 90-day retention. Raw ZIPs remain in the Actions artifact, not the repository.
- Report: [PHASE294_SEC_FORM4_BULK_ARCHIVE_RAW_SAMPLE_AND_SCHEMA_AUDIT_2026-11-11.md](PHASE294_SEC_FORM4_BULK_ARCHIVE_RAW_SAMPLE_AND_SCHEMA_AUDIT_2026-11-11.md) on branch `phase294-sec-form4-bulk-sample-acquisition`. No PR or merge was created.
- This is a purposive six-quarter sample, not all 83 archives or universe coverage. Acceptance-time joins, first daily-index sighting, exact first-public receipt, multi-owner transaction attribution and effective-dated security identity remain open. No PIT panel, return test, alpha, bootstrap/LOO or holdout use occurred. F80 and production controls remain unchanged.

**Next priority:** real-data Phase 283 daily-index reconciliation for a stratified Form 4 accession sample, plus SEC-HEADER acceptance-time validation. Preserve first observed index dates without backdating to FILING_DATE; do not treat the index date as exact first-public time.

## Repository snapshot after Phase 294 (2026-11-11)

- SEC_CONTACT_EMAIL is now verified operational for GitHub Actions by successful SEC HTTP 200 retrievals; its value remains secret and is not stored in repository files.
- Phase 294 branch is documentation/acquisition-only. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; production, universe, capital, parameters and the consumed legacy holdout are unchanged.
- No data purchase, vendor contact, model test, alpha promotion, chronological OOS, bootstrap/LOO or holdout use.

## Phase 295 — SEC Form 4 daily-index and acceptance-time real-data pilot (2026-11-11)

**Result: acquisition and header reconciliation passed; strict PIT did not pass and remains closed.**

- Run [43087726733](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43087726733) completed successfully. The workflow compiled and passed **11/11 tests** after adding a Form 4-specific SGML parser. The earlier failure was a parser-format mismatch: Form 4 complete-submission text uses `<ACCEPTANCE-DATETIME>YYYYMMDDHHMMSS`, while the reused N-PORT parser expected a colon-delimited field. Raw SEC responses are now preserved before parsing so future parser errors cannot discard evidence.
- Across 18 purposive accessions (first/middle/last sample from 2006Q1, 2012Q1, 2023Q1, 2023Q2, 2025Q3 and 2026Q3): **18/18** SEC-HEADER accession/form/filing-date/acceptance timestamps reconciled; **18/18** first observed daily-index sightings matched the bulk filing identity and had zero calendar-day lag.
- Of 88 daily-index date requests, 57 downloaded and parsed with zero parse errors. The 31 HTTP 403 dates were 27 weekends and four U.S. federal holidays, not parser failures.
- **15/18** acceptances were at or after 16:00 ET, **5/18** at or after 18:00 ET and **2/18** at or after 20:00 ET. All 18 acceptance local dates matched the SEC filing date and all 18 daily index first-sighting dates matched that date. This does not prove when the nightly index itself first became publicly reachable; no sample captured a later-index-date case.
- Artifact [13887641760](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43087726733/artifacts/13887641760), SHA-256 `89c9904d9bdd8f4cbde2706c40111a3e5ddeabed79788b77ed76b6a1e92390ed`, contains the 18 complete-submission text files, 57 raw daily indexes and manifest (60,334,796 downloaded bytes). Raw files are not committed to the repository.
- `SEC_CONTACT_EMAIL` was injected successfully and masked in logs. The value is used only in the SEC User-Agent; this workflow did not send email. No user action is required.
- Controls: `first_public_timestamp_verified=false`, `strict_pit_admitted=false`, `alpha_test_authorized=false`, `return_test_run=false`, `bootstrap_loo_run=false`, `holdout_used=false`, `f80_frozen=true`, and no production/universe/capital/parameter changes.

**Next clock gate:** deliberately sample after-22:00 ET filings, next-business-day index sightings, Forms 4/A and post-acceptance corrections. Preserve acceptance timestamp and first observed index date separately. For any later return test, enter no earlier than the next full XNYS session after acceptance; do not use same-day returns.

## Phase 296 — SEC Form 4 owner-attribution and purchase-quality feasibility (2026-11-11)

This offline audit re-read the six raw ZIPs from Phase 294 artifact [13884014630](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43083625013/artifacts/13884014630). The six nested archive SHA-256 hashes are recorded in the report [PHASE296_SEC_FORM4_OWNER_ATTRIBUTION_AND_PURCHASE_QUALITY_AUDIT_2026-11-11.md](PHASE296_SEC_FORM4_OWNER_ATTRIBUTION_AND_PURCHASE_QUALITY_AUDIT_2026-11-11.md).

- The six quarters contain **317,267** Form 4/4-A accessions: **310,561 (97.89%)** have exactly one reporting owner; **6,706 (2.11%)** have multiple owners; none have zero owners.
- Among **27,902** non-derivative P/acquired/direct transactions with positive shares and price, **25,997** are in single-owner accessions and **1,905** in multi-owner accessions. Multi-owner transactions remain quarantined; the bulk `NONDERIV_TRANS` table has no reporting-owner CIK on each transaction row.
- A conservative data-quality subset requiring original Form 4 (not 4/A), exactly one reporting owner, positive shares/price, P + acquired + direct, and 0–2 calendar days from transaction to filing contains **15,590 rows**, **11,088 accessions**, **3,243 issuers** and **6,728 owners**. All rows in this subset have an issuer ticker as filed, but effective-dated security-class identity is not verified.
- The transaction-to-filing lag has a long tail in the broader candidate set: median 2 days, p90 20 days, p95 94 days, p99 715 days, maximum 7,308 days, with seven negative-lag rows. The 0–2-day filter is a conservative screening choice, not proof of execution timing or public availability.
- The SEC data dictionary defines transaction code P as **“Open market or private purchase”**; it cannot be labeled open-market buying by itself. In a lexical footnote screen of 28,663 P/acquired/direct rows, 11,762 had at least one referenced footnote; overlapping keyword hits included 671 explicit open-market mentions, 147 private-purchase/placement mentions, 233 public-offering mentions, 3,339 weighted-average-price mentions, 1,697 trust/indirect mentions and 1,249 10b5-1 mentions. These are triage counts, not a mutually exclusive classification.
- In the 15,590-row conservative subset, `AFF10B5ONE` is explicitly negative on 6,995 rows, affirmative on 201 and unknown/blank/absent on 8,394. The field is absent in 2006Q1 and 2012Q1 in this sample; blanks must not be interpreted as false.

**Decision:** Form 4 is now a credible public-data candidate for a broad, next-session-only insider-transaction hypothesis. It is not an admitted signal. Continue with (1) after-hours/late-index/PAC sample expansion, (2) XML/footnote and multiple-owner adjudication, and (3) effective-dated issuer/security-class mapping and broad-universe price coverage. Only then preregister a chronological, cost-adjusted test against frozen LTM/F80 with independent OOS and a new holdout. No return test or alpha estimate was run in Phase 296.

## Current repository verification — 2026-11-11 19:31 UTC

- Latest 100 Actions runs: **67 successful, 8 failed, 25 cancelled, zero active/queued**. All eight failures were intermediate Phase 294/295 iterations; final Phase 294 run 43083625013 and final Phase 295 run 43087726733 succeeded. No workflow was duplicated while an earlier run was active.
- Branch inventory: **145** (100 branches on page 1, 45 on page 2) after creating this Phase 296 research-only branch. PR #14 remains open on head `6dedb088d7289ca5155a319b5f88155c2d431be3`; PR #13 remains open on head `61f737f18b410bc6d85b8c56ed96bc1fd9c130f5`. No PR was opened or merged for Phases 294–296.
- Historical statements in Phases 281–293 that `SEC_CONTACT_EMAIL` was unconfigured were accurate at the time and are superseded by the successful Phase 294/295 secret-injection checks.
- F80, production, universe, capital, parameters and the consumed legacy holdout remain unchanged. No paid data, vendor contact or data license was initiated.


## Phase 297 — Form 4 transaction-form-type reconciliation (2026-11-11)

- Corrected the Phase 296 Table I cohort by requiring transaction-level `TRANS_FORM_TYPE=4`. The candidate set fell from 15,590 to **15,475 rows**, 10,997 accessions, 3,226 issuers and 6,677 reporting owners; 115 type-5 rows were excluded.
- Recomputed the versioned high-precision open-market-footnote screen: 413 rows, 365 also with positive shares and price. Code P remains open-market **or private** purchase; it is not an open-market-only label.
- Workflow 43094005689 passed 6/6 deterministic tests. No return/alpha test or PIT admission.

## Phase 298 — Form 4/A cross-quarter parent-lineage live audit (2026-11-11)

- Downloaded and CRC-checked 2011Q4 and 2026Q2 SEC bulk archives. Including the immediately prior quarter increased unique candidate links to 1,355/1,862 (72.77%) for 2012Q1 and 518/627 (82.62%) for 2026Q3.
- Remaining candidates were ambiguous (44 and 8) or had no parent in the two-quarter search windows (463 and 101). Candidate links still lack an authoritative parent-accession foreign key.
- Workflow 43101285104 succeeded; no alpha/return test.

## Phase 299 — Form 4/A original EDGAR submission sample (2026-11-11)

- Deterministically selected 46 candidate original/amendment pairs across 2012Q1 and 2026Q3, including adjacent-quarter, line-difference and partial-owner strata; 90 raw SEC complete-submission documents were retrieved.
- The sample is a source-validation design, not a prevalence estimate. It does not establish parent accession identity, transaction-owner attribution, first-public availability or alpha.
- Final workflow 43115460066 succeeded after an intermediate failed attempt 43115373933.

## Phase 300 — Form 4/A XML-to-bulk reconciliation (2026-11-11)

- Corroborated all **46/46** candidate links using original EDGAR headers/XML: issuer, date-of-original-submission, owner overlap, form type and acceptance chronology.
- Of 90 documents, 88 matched the central transaction signature and 80 matched the broader signature. Remaining differences were limited to `NATURE_OF_OWNERSHIP` and/or `TRANS_TIMELINESS`; no transaction economics were promoted from an ambiguous line diff.
- Workflow 43116245184 succeeded. No return or alpha test.

## Phase 301 — 2023Q2 intermediate-era Form 4/A lineage and XML audit (2026-11-11)

- Retrieved and validated SEC bulk archives 2022Q4, 2023Q1 and 2023Q2 (151,185 Form 4/4-A accessions across the three quarters). Target 2023Q2 has 937 Form 4/A accessions with an original-submission date and owner: **719 unique owner-overlap candidates (76.73%)**, 24 ambiguous, 15 same-issuer/date with no owner overlap, and 179 with no parent candidate in the loaded three-quarter window.
- Adding 2022Q4 to the 2023Q1–Q2 window added 22 unique candidates and reduced the no-parent-in-window count from 202 to 179. No-parent means no candidate in the loaded window, not no parent anywhere in EDGAR.
- The deterministic sample contains 52 cases and 102 original EDGAR documents: 24 unique pairs, 8 ambiguous, 8 no-owner-overlap and 12 no-parent. All 24 unique pairs were corroborated by XML metadata; all 8 ambiguous cases remained ambiguous. Two no-owner-overlap cases were capped at 12 of 15 candidate parent documents.
- All 102 documents passed download, XML parse, header/XML identity and row-count checks; all 102 matched the core transaction signature. 98/102 matched the broader signature. The four full-signature differences were limited to `NATURE_OF_OWNERSHIP` and/or `TRANS_TIMELINESS` (one Table I document and three Table II documents).
- Final workflow 43121592821 succeeded with 35 regression tests across Phases 153/299/300/301. The first Phase 301 attempt 43121407654 stopped at the GitHub artifact endpoint with HTTP 401 before SEC requests; the final workflow retrieved all three archives directly from the SEC. Raw archives, 102 submissions, manifest and result are preserved in artifact 13901611120 (SHA-256 `5840790fac1d411f95dad60737e68d9a6bc26d08380a7be9b8d1d18d74b51333`).
- Decision: lineage is better supported but still not admitted for strict PIT/event-flow modeling. Date-only original-submission metadata is not a parent-accession foreign key; owner sets are accession-level, not transaction-line-level. Next gate: SEC daily-index first-appearance and PAC/correction audit for the 2023 sample, plus targeted longer lookback for no-parent cases and effective-dated security identity.
- No return/alpha, bootstrap/LOO, chronological OOS or holdout test. F80, production, universe, capital and parameters remain unchanged. No email was sent; the SEC contact secret was used only in the User-Agent.

## Current repository verification — 2026-11-11 23:42 UTC

- Latest 100 Actions runs: **63 successful, 12 failed, 25 cancelled, zero active/queued**. The final Phase 301 run 43121592821 succeeded; the earlier 43121407654 failed before any SEC request because the GitHub artifact-download endpoint returned HTTP 401. The final workflow avoided that dependency by retrieving the public SEC archives directly.
- Branch inventory: **150** (100 on page 1, 50 on page 2). The Phase 301 work remains on research-only branch `phase301-form4a-intermediate-era-lineage-audit`; no PR was opened or merged.
- PR #13 and PR #14 remain open and unchanged. Eleven PRs are currently open in the repository.
- The workflow's SEC contact expression was corrected for future runs; the final run's contact value was masked in logs and used only in the SEC User-Agent. No email was sent.
- F80, production, universe, capital, parameters and the consumed legacy holdout remain unchanged. No paid data, vendor contact or data license was initiated.


## Phase 302 — 2023 Form 4/A daily-index and PAC/correction clock audit (2026-11-12)

**Result: source acquisition and date-granular index reconciliation passed; strict PIT remains closed.**

- Reused the deterministic Phase 301 sample: 32 cases (24 unique owner-overlap candidates and 8 ambiguous parent sets), 71 unique original/amendment documents. The three SEC bulk archives 2022Q4, 2023Q1 and 2023Q2 were re-downloaded and matched their pinned SHA-256 values.
- Downloaded and SEC-header reconciled 71/71 complete submissions. All accession, form and filing-date checks passed.
- Downloaded and parsed 121/121 historical daily form.YYYYMMDD.idx files (90,998,369 raw index bytes). Zero HTTP/retrieval errors, zero index parse/write errors and zero pre-filing negative-control sightings.
- All 71/71 accessions had a complete requested index window, matching issuer/form/filing identity, and an earliest observed index date equal to the bulk filing date (0-day lag). No later index-date sighting occurred in the sample.
- Acceptance timestamps were at/after 16:00 ET for 42/71 documents; at/after 17:30 ET for 19/71; at/after 18:00 for 14/71; at/after 20:00 for 7/71; at/after 21:30 for 1/71; and at/after 22:00 for 0/71. The SEC's Form 3/4/5 special filing-date window is after 17:30 and before 22:00 ET. EDGAR closes at 22:00, so test late-window acceptances and next-business-day filing-date rollovers for submissions missing the cutoff, not after-22:00 acceptances.
- Among the 24 unique candidate original/amendment pairs, 23 had the parent on an earlier daily-index date; one pair shared the same daily-index date and remains intraday-unordered. All eight ambiguous parent sets remain unassigned; no candidate was selected.
- The daily index is date-granular and built nightly. Its date is not an exact first-public timestamp and does not prove same-day market availability. Phase 302 did not capture actual PAC `.pc`/Feed/Oldloads events; it compares Form 4/A amendment accessions only. A same-index-date pair cannot be ordered intraday by acceptance timestamps alone. Use no earlier than the close of the next full XNYS session after the earliest complete-window index date in any future conservative test; do not fall back to acceptance time or filing date when the index window is incomplete.
- Workflow [43127646850](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43127646850) succeeded. 48/48 tests passed across Phase 153, 299, 300, 301 and 302 (17 + 6 + 6 + 6 + 13). The final artifact is [13904715073](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43127646850/artifacts/13904715073), 44,933,819 bytes, SHA-256 e1be6ae8cf030d9e80769d93ce1d96d08e399cd3fb3f4b4fc826da20247628b5.
- Two preliminary Phase 302 attempts failed before any SEC request: one regression omitted the 2023-07-04 federal holiday; the next exposed a missing repository-root import path. Both were corrected before the final successful run. The final code also requires a window-verified index identity before comparing parent/amendment clocks.
- Report: [PHASE302_FORM4A_DAILY_INDEX_PAC_CLOCK_AUDIT_2026-11-12.md](PHASE302_FORM4A_DAILY_INDEX_PAC_CLOCK_AUDIT_2026-11-12.md).

**Decision:** Form 4/A now has a stronger 2023 daily-index date-granular knowledge-date pilot, but no exact first-public timestamp, no after-22:00 case, no broad prevalence estimate, no effective-dated security-class panel and no transaction-to-individual-owner proof. Keep it conditional; do not admit strict PIT or a stock-selection feature. Next, deliberately sample Form 4/4-A acceptances in the 17:30–22:00 ET window (especially 21:30–22:00), submissions that miss the cutoff and receive a next-business-day filing date, and same-day correction/PAC sequences; reconcile daily-index sightings and preserve each as-filed vintage. Continue issuer/security-class identity and owner attribution in parallel.

## Current GitHub verification — 2026-11-12 00:33 UTC

- Latest 100 Actions runs: 61 success, 14 failure, 25 cancelled, 0 queued/in-progress. The two preliminary Phase 302 failures were corrected before SEC retrieval; final Phase 302 run 43127646850 passed. No active workflow was duplicated.
- Branch inventory: 151. Phase 302 remains on research-only branch phase302-form4a-daily-index-pac-clock-audit; no PR was opened or merged.
- PR #13 remains open against main; PR #14 remains open and stacked on PR #13. Neither was merged or modified by Phase 302.
- SEC_CONTACT_EMAIL was injected only into the SEC User-Agent. Its value was not logged or stored, and no email was sent.
- F80_TOP20_PARTIAL50_BASELINE_C20, production, universe, capital, parameters and the consumed legacy holdout remain unchanged. No data purchase, vendor contact, alpha promotion, return test, bootstrap/LOO, chronological OOS or holdout use occurred.


## Phase 303 — SEC Feed archive and Latest Filings RSS feasibility (2026-11-12)

- SEC public Feed/Oldloads archives are daily concatenated filing payloads, not compact accession-level PAC ledgers. Directory samples show Feed archives of 642,473–8,728,562 KB per day in 2023 Q2 and 693,801–2,299,770 KB per day in 2026 Q4. **Disposition: reject as the primary broad historical PAC/clock source**; do not download multi-year archives. Retain a single-day extraction only for a specific high-value diagnostic.
- The SEC Webmaster FAQ identifies Latest Filings search and its associated RSS as the best public route to get close to real-time availability. The feed can be filtered for Ownership filings; SEC documentation still says exact first-public time is unavailable and the acceptance-to-availability lag is variable.
- **Disposition: conditional prospective pilot only; endpoint probe passed.** Both Form 4 and Form 4/A Atom queries returned HTTP 200. The feed yielded 136 entity rows representing 68 unique accessions (50 Form 4, 18 Form 4/A); each accession had one Issuer and one Reporting row, with path/title CIK agreement on 136/136 rows. Two complete-submission headers matched Atom `updated` to `ACCEPTANCE-DATETIME` exactly (2/2), so `updated` is not an independent first-public timestamp in the tested sample. A 30-day capture, cap/retention and gap recovery remain untested. No historical backfill or exact first-public timestamp is available.
- Phase 302 did not retrieve actual PAC .pc/Feed/Oldloads event records; it audits Form 4/A amendment chronology only. Keep PAC distinct from Form 4/A.
- Final live probe [run 43131625929](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43131625929) passed 7/7 tests and the two SEC complete-submission header cross-checks. Artifact [13904274568](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43131625929/artifacts/13904274568), SHA-256 `f55f880c3bb14a2744571e8988d907c27c1db6d3833dcc93e7c565eed4771e62`.
- Report: [PHASE303_SEC_FEED_ARCHIVES_AND_LIVE_FILINGS_RSS_FEASIBILITY_2026-11-12.md](PHASE303_SEC_FEED_ARCHIVES_AND_LIVE_FILINGS_RSS_FEASIBILITY_2026-11-12.md).
- No return/alpha, strict PIT admission, bootstrap/LOO, chronological OOS or holdout test. F80, production, universe, capital and parameters remain unchanged. No data purchase, vendor contact, PR or merge.


## Current GitHub verification — 2026-11-12 01:02 UTC

- Latest 100 Actions runs: **60 success, 15 failure, 25 cancelled, zero queued/in-progress**. Final Phase 303 run 43131625929 succeeded; run 43131396845 failed at offline tests before any SEC request (stale test file on an intermediate commit), and run 43131399974 was cancelled by concurrency before starting a job. No active workflow was duplicated.
- Branch inventory: **152** (100 on page 1, 52 on page 2). Active research branch is `phase303-sec-feed-live-rss-feasibility`; no PR was opened for Phase 303.
- PR #13 and PR #14 remain open and unmerged; 11 PRs are open in total. No PR was merged or retargeted.
- `SEC_CONTACT_EMAIL` was used only in the SEC User-Agent. No email was sent. No Feed/Oldloads archive or PDS subscription was downloaded/purchased.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, production, universe, capital, parameters and the consumed legacy holdout remain unchanged.


## Phase 304 — SEC Latest Filings RSS count-cap and accession-grain audit (2026-11-12 01:10 UTC)

- Latest Filings Atom was queried for Forms 4 and 4/A at requested `count` values 100, 200, 500 and 1,000. All 8 requests succeeded. Form 4 returned exactly 100 entity rows / 50 accessions at every requested count; Form 4/A returned 36 rows / 18 accessions at every count. Larger `count` values did not expand the result. The Form 4 endpoint therefore behaves as if limited to 100 entity rows, or ignores larger counts; a `start`-offset audit is required to distinguish cap from pagination semantics.
- Accession sets were nested across count requests. Zero orphan rows, Atom-id/link accession mismatches, query-form mismatches, path/title CIK mismatches, duplicate entity rows, form conflicts or `updated` conflicts. The sample happened to contain exactly one Issuer and one Reporting row per accession; code preserves arbitrary row multiplicity and does not assume two rows universally.
- Four additional complete submissions (newest/oldest for each form) matched Atom `updated` to SEC-HEADER `ACCEPTANCE-DATETIME` in 4/4. Combined Phase 303/304 cross-checks are 6/6; `updated` remains an acceptance-time proxy, not first-public time.
- Workflow [43132595262](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43132595262) passed 18/18 tests (11 Phase 304 + 7 Phase 303). Artifact [13905652996](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43132595262/artifacts/13905652996), ZIP SHA-256 `ae8a81b0d3067348fdcb36063b659cc38a8b9ef6a0987c250866bf5c3e4d2dda`.
- Next gate: test SEC RSS `start` offsets with `count=100`, including accession rows split across page boundaries. Do not infer exact public time or strict PIT from Atom `updated`.
- No return/alpha, bootstrap/LOO, chronological OOS or holdout test. F80, production, universe, capital and parameters remain unchanged. No email was sent.


## Phase 305 — SEC RSS start-offset pagination and exact-form audit (2026-11-12 01:17 UTC)

- Final workflow [43133481229](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43133481229) passed 26/26 regressions (8 Phase 305, 11 Phase 304, 7 Phase 303); all 14 live Atom requests succeeded. Artifact [13905777719](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43133481229/artifacts/13905777719), SHA-256 `b0306105144e91e6486f9b919ee1e1f7baf78a07c036c09755ff0fc6eb8b2bfd`.
- `start` pagination is effective and counts raw entity rows: observed overlaps were 1 row for starts 0/99 and 99 rows for starts 99/100 and 100/101. Form 4 pages 0, 100 and 200 contained 100 rows each and 50, 49 and 47 unique accessions; no accession split was observed across the 0/100 or 100/200 boundaries, but multiple-owner filings generated 4- and 8-row accession groups.
- Critical query semantics: SEC `type=4` is a prefix filter, not an exact Form 4 filter. At starts 500 and 1,000, 87/200 rows were other 4-prefixed forms (40-APP/A, 424B2/B3/B5, 425, 485BPOS and 497). Exact form parsing now isolates only `4` for the Form 4 panel. Across the sampled offsets, 202 unique exact Form 4 accessions / 413 unique entity rows were observed; this is a sampled offset union, not a complete historical count.
- Form 4/A returned 36 rows / 18 accessions at start=0 and no rows at later offsets. Target-form structural errors were zero.
- The next gate is a contiguous page scan with entity-row overlap and accession-level reassembly, then a separate prospective first-receipt capture protocol. `updated` remains an acceptance-time proxy, not exact first-public time.
- Latest 100 Actions runs after Phase 305: 56 success, 20 failure, 24 cancelled; zero queued/in-progress. 154 branches inventoried. PRs #13/#14 and the broader open research PR queue remain unmerged; no PR was merged in this phase. The Phase 305 branch is research-only.
- No return/alpha, bootstrap/LOO, chronological OOS or holdout test. F80, production, universe, capital and parameters remain unchanged. No email was sent.


## Current GitHub verification and prospective capture follow-up — 2026-11-12 03:39 UTC

- Latest 100 Actions runs: **56 success, 22 failure, 22 cancelled, zero active/queued**. The final Phase 308 capture run [43149574581](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43149574581) succeeded; no workflow was duplicated while active.
- Phase 308 capture #6 completed all 30 SEC requests. Form 4: 1,022 accessions / 2,111 entity rows; Form 4/A: 18 / 36. No new, missing or changed accessions; zero structural/fingerprint errors. Inter-capture gap: 37.4126 minutes.
- Artifact [13913710003](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43149574581/artifacts/13913710003) was downloaded and inspected (32 files; 30 raw Atom pages, result JSON, 1.1 MB ledger). Durable ledger: 6 captures, 1,040 accession keys; all 1,040 initial records remain left-censored/quarantined; zero live non-left-censored event intervals so far.
- Current branch inventory: 157 branches (100 on page 1, 57 on page 2). Eleven PRs remain open; PR #13 and #14 remain open/unmerged. No PR was opened or merged by this follow-up.
- `SEC_CONTACT_EMAIL` remains only in the masked SEC User-Agent; no email was sent. No paid data, vendor contact or purchase.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, production, universe, capital, parameters and legacy holdout remain unchanged. No strict PIT admission, alpha/return test, bootstrap/LOO or chronological OOS.


## Phase 308 prospective SEC RSS capture #7 — 2026-11-12 04:05 UTC

- Final capture run [43152333818](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43152333818) succeeded; all 30/30 SEC Atom requests completed.
- Form 4: 1,022 accessions / 2,111 entity rows. Form 4/A: 18 accessions / 36 entity rows.
- No new, missing or changed accessions; zero structural errors and zero fingerprint conflicts. Inter-capture gap: 24.9851 minutes.
- Artifact [13914172674](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43152333818/artifacts/13914172674) was inspected. Ledger now records 7 complete captures and 1,040 unique accession keys; all 1,040 initial records remain left-censored/quarantined. No live non-left-censored event interval has yet been observed.
- The absence of new accessions is a coverage observation only, not evidence about Form 4 predictive value.

## Phase 310 — SEC N-PORT raw filing, acceptance-clock and direct-short reconciliation — 2026-11-12 04:22 UTC

- Final workflow [43154326395](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43154326395) passed. It ran 14 Phase 193 regressions and 9 Phase 310 regressions (23 total).
- Artifact [13915126393](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43154326395/artifacts/13915126393), SHA-256 `f4827e6065b76bb2f8d4c6287e2026cf1b6eb06f136a407d6295ab530e47ef98`, contains 20 raw SEC files (directory JSON, filing-index HTML, complete submission text and primary XML for five accessions), 1,722,110 bytes total. Raw filing bytes remain in the 90-day artifact, not in the repository.
- The original Phase 193 parser expected `ACCEPTANCE-DATETIME:` but SEC N-PORT submission text uses the SGML tag `<ACCEPTANCE-DATETIME>...`. The parser was corrected; raw bytes are now staged and hashed before semantic parsing so a parser defect cannot discard evidence.
- All five accessions now reconcile accession/form/acceptance header. The SEC filing-index `Accepted` value and directory primary-document `last-modified` match the header acceptance time in 5/5 cases. These are acceptance metadata, not proof of first public receipt.
- All 11 expected positive-control CUSIPs are present on sign-concordant rows. The five purposive filings contain 327 sign-concordant U.S. corporate common-equity short rows under the narrow definition (`Short`, `EC`, `CORP`, `US`, `NS`, negative balance/value/%NAV).
- Series identity is partial: 4/5 accessions have a series ID in XML or filing-index HTML. Accession `0001145549-25-033457` (ACAP Strategic Fund, CIK 1467631) has no series or class ID in either source. It remains CIK/fund-level only; no series ID is invented.
- Conservative first-full-XNYS-session candidates after acceptance date: 2020-08-24, 2022-09-16, 2023-10-02, 2024-11-27 and 2025-05-29. These are conservative execution candidates, not first-public-receipt timestamps.
- Disposition remains partial: raw bytes, header/acceptance and direct-short sign controls pass; series identity is 4/5. The sample is purposive, not representative; no prevalence estimate, amendment lineage, effective-dated security master or broad universe coverage is established.
- Report: [Phase 310 audit](https://github.com/jafelix81/NuevaEstrategia/blob/phase310-nport-raw-filing-vintage-retrieval/research/PHASE310_NPORT_RAW_FILING_VINTAGE_RETRIEVAL_AUDIT_2026-11-12.md). Hash ledger: [Phase 310 result JSON](https://github.com/jafelix81/NuevaEstrategia/blob/phase310-nport-raw-filing-vintage-retrieval/research/phase310_nport_raw_vintage_validation_result_2026-11-12.json).
- The first index-HTML parser regression run failed because its synthetic fixture omitted the newly required index HTML entry; the fixture was corrected and the final run passed. No SEC data were lost or changed.

## Current repository verification — 2026-11-12 04:23 UTC

- Latest 100 Actions runs: 61 success, 23 failure, 16 cancelled; zero queued/in-progress. The final Phase 310 run is successful.
- Branch inventory: 158 (100 on page 1, 58 on page 2). Eleven PRs remain open; PR #13 and #14 remain open/unmerged. Phase 310 is a research-only branch; no PR was opened or merged.
- `SEC_CONTACT_EMAIL` was used only in the masked SEC User-Agent. No email was sent. No data purchase or vendor contact.
- No returns/alpha, bootstrap/LOO or chronological OOS test. No holdout use. `F80_TOP20_PARTIAL50_BASELINE_C20`, production, universe, capital and parameters remain unchanged.


## FINRA Short Interest prior-result re-adjudication — 2026-11-12

- Re-inspected the Phase 25B and Phase 25C workflow artifacts and the still-open Phase 25C corrected-incremental script. The prior return summaries remain **inadmissible**, consistent with Phase 267; this was not a new return test.
- Both artifacts use the same feature-file SHA-256, so they are not independent data replications. The old panel covers 98 tickers from the former arbitrary 335-name universe, 55 settlement dates and 5,115 rows.
- The legacy fetcher requested 10,000 rows, but FINRA's synchronous API ceiling is 5,000. All 55 successful responses returned exactly 5,000 rows, only offset 0 was preserved, and response-total headers were not retained. Historical completeness is unverified.
- The still-open Phase 25C corrected-incremental script continues to use `settlementDate + pandas BDay(7)` and the first close on/after that date. FINRA's documented 4:40 p.m. ET availability is after the regular close. Phase 267 reconstructed 55 unique cycle anchors and found all 292 repeated training-snapshot uses across Phases 25B/25C inherit pre-release price anchors; 19/55 legacy knowledge dates are also one XNYS session early.
- Decision: do not use the archived Phase 25B/25C return summaries for feature selection or promotion. The short-interest hypothesis is **not yet falsified**, but it remains quarantined until complete pagination, immutable revision vintages, official/XNYS settlement dates, next-session entry prices, and broad effective-dated security coverage are rebuilt.
- References: [Phase 267 PIT/pagination audit](https://github.com/jafelix81/NuevaEstrategia/blob/phase308-sec-rss-prospective-capture/research/PHASE267_FINRA_SHORT_INTEREST_PIT_PAGINATION_AUDIT_2026-11-10.md); [Phase 25C corrected-incremental code](https://github.com/jafelix81/NuevaEstrategia/blob/phase25c-finra-short-interest-incremental/Nueva_Estrategia_Fase25C_FINRA_ShortInterest_CorrectedIncremental.py).


## Phase 311 — SEC N-PORT historical accession census — 2026-11-12 04:44 UTC

- Final workflow [43156706936](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43156706936) passed; 13/13 regressions passed. Artifact [13916331861](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43156706936/artifacts/13916331861), SHA-256 `b03abc72c5ed9d59005ccca9a1285169c6bac7b7a607e9f415ec4c0fe1a342be`, contains the complete accession census CSV, 28-index hash manifest, quarter summary and 56 deterministic sample candidates.
- 28/28 quarterly master indexes from 2019 Q4 through 2026 Q3 were retrieved (98,553,317 compressed bytes). Exact forms: 349,076 NPORT-P, 5,343 NPORT-P/A, and 696 NT NPORT-P notices; 355,115 unique accessions, 2,458 distinct registrant CIKs, zero duplicate accessions across quarters. Data-bearing NPORT-P + NPORT-P/A = 354,419.
- NT NPORT-P is retained as a separate late-filing notice, never as a holdings row. The deterministic QA sample is 56 accessions (28 per data-bearing form), 54 distinct registrant CIKs; not representative.
- Parser handles legacy dashed accession filenames and 18-digit accession directories. It validates the master-index registrant/path CIK independently from the accession prefix because the SEC accession prefix may identify a filing agent. It also handles pipe characters in company names. The final three-form scope supersedes the initial two-form census.
- SEC N-PORT data are monthly portfolio snapshots with quarterly public data-set postings; the public data set excludes money-market funds and SBICs. No first-public timestamp, amendment lineage, series/security panel or F80-universe coverage is admitted yet. Phase 312 is raw filing sample reconciliation.
- Report: [Phase 311 audit](PHASE311_NPORT_HISTORICAL_ACCESSION_CENSUS_2026-11-12.md). Quarterly counts: [CSV](PHASE311_NPORT_QUARTER_SUMMARY_2019Q4_2026Q3.csv). Aggregate result: [JSON](phase311_nport_accession_census_summary_2026-11-12.json).
- PR #15 remains draft/unmerged. No production, F80, universe, capital, parameters or holdout changes. No return/alpha, bootstrap, LOO or chronological OOS test.
