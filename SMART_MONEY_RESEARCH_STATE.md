# Smart Money Research State

Updated: 2026-11-04 (Phase 69 incremental scan complete; Phase 72 XML pilot failed; Phase 73 submission-text repair prepared)

## Frozen control
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- MOM120 is a validated control candidate but not promoted: realized portfolio metrics slightly exceeded LTM, but incremental daily excess was small and the block-bootstrap CI included zero.

## Phase 31 — FINRA short-flow × short-interest divergence
- Status: KILLED as independent alpha.
- Valid OOS run: 40164323397.
- PIT: short flow through signal close; short interest only after conservative knowledge date.
- Result: horizon-dependent sign reversal; economic spreads' bootstrap intervals included zero. Do not tune horizons to rescue.

## Phase 21C — SEC Form 4 insider transactions
- Status: KILLED as a standalone signal in the current frozen-universe diagnostic.
- Run 39369692938 completed successfully with 24 training signal dates and 6 untouched final OOS dates (2025-02-25 through 2026-09-29).
- Official SEC dataset coverage is strong from 2016Q1 through 2026Q3; 301/335 universe CIKs mapped in the current implementation. KnowledgeDate uses filing date and downstream requires KnowledgeDate < SignalDate; same-day filings are excluded.
- Training-selected features were BUY_DAYS20 (H5), BUY_EVENTS60 (H10), and BUY_ADTV20 (H20). Final OOS mean top-minus-bottom was -0.12% (H5), +0.65% (H10), and -0.46% (H20); all bootstrap 95% CIs included zero. Residualized Spearman means were negative at all three horizons (-6.33%, -2.54%, -2.99%).
- Decision: do not tune insider features/horizons to rescue this implementation. Reuse only for a materially different, pre-registered mechanism.

## Phase 22C — SEC 13F feasibility
- Status: NOT PRODUCTION-READY; identity-resolution research only if it materially improves worst-period coverage without lookahead.
- Latest run 41652405078 (2026-11-03) succeeded. Coverage remains 70.43% (2016Q1), 81.73% (2020Q1), and 93.02% (2024Q1); ambiguous candidates remain 51, 37, and 19 respectively. Conclusion: `INSUFFICIENT_COVERAGE_FOR_PRODUCTION`.
- Earlier PIT issuer/CUSIP audit produced minimum 54.8% coverage in 2016Q1. Direct PIT CUSIP is preferable to name fuzzy matching but still has class/ADR/legacy-CUSIP ambiguity.
- This is a data-identity feasibility result, not evidence against 13F economically. Park unless a deterministic security identity method materially improves the worst-quarter coverage.

## Phase 23C — CFTC COT positioning
- Status: KILLED for the tested equity-index positioning hypothesis.
- Run 39375172026 completed with 12 walk-forward test dates for NASDAQ and S&P 500 families.
- NASDAQ mean strategy return was +0.192% at H5 versus +0.890% unconditional and -0.460% at H20 versus -3.370% unconditional. S&P 500 mean strategy return was -0.049% at H5 versus +1.024% unconditional and -3.058% at H20 versus -1.443% unconditional; H20 hit rate was 16.7% for S&P 500.
- Decision: no robust incremental equity-selection edge; archive rather than optimize.

## Phase 24B — public listed-options historical feasibility
- Status: public OCC endpoint path is insufficient for event-level historical option-flow research.
- Run 39398787569 tested 11 historical sample dates. Contract-volume, DLP HTTP, and trade-volume endpoints returned effectively empty payloads; daily volume statistics were substantive, while volume-by-account-type was substantive on only 2/11 samples.
- Decision: do not infer historical options flow/OI/IV/skew from these endpoints.

## Phase 27O — SEC N-PORT institutional holdings dose-response
- Status: KILLED in the tested dose-response form.
- Run 39503800069 covered six annual formation periods (2020Q4–2025Q4) using the PIT 27N2 share-accumulation signal and fixed 63-trading-day forward return.
- Top-minus-bottom decile returns were -11.77%, -5.56%, +12.03%, +6.12%, -4.78%, and -1.74%; sign is not stable and no monotonic institutional-flow effect is established.
- Decision: do not optimize dose threshold or horizon.

## Phase 32 / 42B — market microstructure and SEC MIDAS
- Event-level historical order/quote data remain commercially licensed; do not synthesize them from inadequate aggregates.
- SEC MIDAS Metrics by Individual Security has quarterly history from 2012Q1 through 2026Q2 and useful daily security-level fields. However, no per-quarter first-publication timestamp was verified. Uniform 2/3/4-month lag sensitivity is exploratory only, not proof of PIT. Alpha authorization remains FALSE pending archived index snapshots or timestamped official publication evidence.

## Phases 43–45 — SEC fails-to-deliver (FTD)
- Phase 43 actual-file parser gate passed (runs 40800732551 and 40809120246): representative 2018/2026 files contained 43,567 and 66,693 records; SEC trailer counts/quantities reconciled, with no exact duplicate rows or missing CUSIPs.
- Phase 44 representative universe coverage was 253/335 (75.52%) in 2018 and 316/335 (94.33%) in 2026; 332/335 were observed in at least one sample.
- Phase 45 PIT identity gate (run 40973633206) found only 207/335 names observed in all five samples (61.79%); 21 of those 207 had changed/unresolved 2018–2026 CUSIP continuity. Crucially, absence from an FTD file cannot distinguish an active security with zero fails from an inactive/unlisted security.
- Decision: PARK FOR PUBLIC-DATA ALPHA. Restricting to always-observed names would create survivorship/selection bias. Reopen only with a deterministic historical security master/listing-status panel with PIT-effective dates. FTD is an aggregate balance, not a daily flow and not proof of naked short selling.

## Phase 46 / 52 — Cboe options data
- Public monthly symbol-level equity-option volume actual-file audit (run 40841944879) parsed successfully, but minimum frozen-universe coverage was 64.48%, below the predeclared 70% gate; representative 2019 samples were 69.55% and 71.04%. Historical release timestamps were also not available. Decision: KILL the public aggregate-volume candidate for this frozen-universe line.
- Cboe Trade-by-Trade (TBT) is materially richer: participant origin, side, open/close, contract, price, size and NBBO context; historical availability begins 2019-10-07. But the documented proposed price is $12,000/month, with $8,000/month ad-hoc historical access. Decision: PARK — commercial access required; no alpha test until licensed reproducible data is available.

## Phase 35/49 — initial submissions-by-CIK sample (superseded)
- Status: **INVALID FOR SUBJECT-ISSUER COVERAGE; no economic test authorized.** The 20,266-row submissions-by-CIK artifact is a filer-side retrieval sample, not a global subject-issuer census. Its issuer counts, ticker coverage, reporting-person coverage, and first-event diagnostics must not be used. The corrected subject-side discovery route is the global master-index + primary XML pilot documented below.
- Latest workflow run 41652405132 completed successfully (job 125973726145; artifact 13256930771). It retrieved 20,266 rows, but the artifact issuer_cik field is not consistently the subject issuer CIK. The reported 303 "issuers" are not validated subject-issuer counts.
- Root cause: submissions_for_cik() stores the ticker-mapped query CIK as issuer_cik; extract_fields() only searches the legacy text label CENTRAL INDEX KEY and falls back to that query CIK. Schedule 13G XML uses issuerCik, so the fallback can assign a reporting-person CIK as the subject issuer.
- Concrete artifact defect: accession 0000092230-25-000015 is assigned to TFC / CIK 0000092230, but its SEC XML identifies subject issuer Federated Hermes ETF Trust / CIK 0001849998 and reporting person Truist Financial Corp. The XML also contains exact previousAccessionNumber=0000092230-25-000001.
- There are 7,858 XML 13G rows (2024–2026) at risk pending subject-CIK re-extraction. All 7,858 have null reporting_person in the old artifact because its parser does not handle the 13G-specific coverPageHeaderReportingPersonDetails schema. The 437 XML 13D rows and legacy HTML/TXT rows also require a subject-CIK consistency audit; do not assume them correct.
- Consequently, current ticker coverage, unique-issuer counts, 13G ownership field coverage, and the earlier accession-prefix sequence counts are not valid issuer-level or economic-group statistics. The previous 3,115 sequences / 58.5% amendment-first diagnostic is superseded.
- The latest artifact still contains two future event_date values (MS filings 2024-02-09 and 2024-02-12 with event date 2024-12-31); event_date is not PIT-certified. Use filing_date only as KnowledgeDate after subject attribution is validated.
- A schema-aware parser prototype and five local unit tests are in branch phase35-13dg-issuer-attribution-repair; all five tests pass on synthetic fixtures modeled on SEC XML/index structures. It is not yet integrated or run against the full artifact.
- Next gate: reparse every XML 13G row for issuerCik; validate all XML 13D and stratified legacy rows; preserve query_cik, archive_path_cik, filed_by_cik, subject_issuer_cik, reporting-person IDs/names, and submission_cik as separate fields; deduplicate by accession; follow exact previousAccessionNumber links; rebuild historical issuer-universe coverage; then normalize events. No forward returns before these gates pass.
- Decision: **retrieval complete, issuer attribution failed, event normalization blocked, no alpha claim.** No change to F80_TOP20_PARTIAL50_BASELINE_C20.

## Current priority
- Keep `F80_TOP20_PARTIAL50_BASELINE_C20` frozen.
- Do not spend further cycles rescuing killed FINRA, Form 4 standalone, CFTC COT, N-PORT dose-response, public aggregate options volume, or public FTD without a historical security master.
- Continue 13D/13G only through corrected reporting-group identity and complete historical predecessor chains. MIDAS remains a conditional public-data candidate only if PIT publication dates can be verified. Cboe TBT remains conditional on commercial licensing.
- No source has earned alpha promotion in this cycle.

## Research principle
“Smart money” is a hypothesis, not an assumption. Every candidate must pass historical coverage, ex-ante availability, PIT timestamps, universe overlap, incremental-information, chronological OOS, bootstrap and LOO tests before portfolio promotion.


## Phase 35 source-census redesign — 2026-11-03
- **New structural finding:** the old pipeline queried the SEC submissions endpoint using the 307 ticker-mapped CIKs. That endpoint returns submissions made by the queried CIK (the filer/submitting entity), not a census of filings whose subject issuer is that CIK. Thus the old 20,266-row artifact is a filer-side sample, not an issuer-side 13D/13G universe. Parsing issuerCik fixes row attribution but cannot recover target-issuer filings that were never in the queried filer submissions.
- SEC filing detail pages expose distinct Filed-by and Subject entities. The reproducible Truist/Federated example shows Filed by CIK 0000092230 and Subject CIK 0001849998; the same separation appears in the SEC FMR/Sandisk filing detail page.
- Correct discovery path: scan each quarter's global EDGAR master.idx for SC 13D, SC 13D/A, SC 13G and SC 13G/A; fetch each filing detail index page; parse Filed-by and Subject CIK/name separately; filter on Subject CIK. Cross-check structured XML issuerCik/issuerCIK where available.
- The global index's CIK column is still the filer. It must never be treated as the subject issuer. The filing index page's Subject CIK is the primary legacy-compatible identity source; XML issuerInfo is an independent cross-check.
- Parser v3 corrects 13G field names and nesting: reportingCik (not reportingPersonCIK), memberGroup (not memberOfGroup), issuerInfo/issuerCik, and issuerCusips/issuerCusipNumber. A CIK-set fingerprint is only a reporting-person-set checksum, not an economic-group key.
- Parser v3 has six local unit tests covering 13D, 13G, SEC filing-index Filed-by/Subject metadata, master.idx filtering, and conservative person-set hashing. These are synthetic/schema fixtures, not full-artifact validation.
- New pilot: 2025Q1 global master-index census. It must parse at least 95% of Subject CIKs, pass the known Truist/Federated accession fixture, and report target-subject counts separately from target-filer counts. No forward returns.
- The pilot's 335-name CIK list uses current SEC ticker mapping plus fallback mapping only as a candidate set. It is not historical active-universe membership. Historical ticker/CIK continuity, delistings, predecessor chains, and reporting-group identity remain separate gates.
- The previous 20,266-row artifact, its 303 purported issuers, and ticker/form coverage statistics remain uncertified and must not be used for event counts, first-event claims, or alpha tests.
- Full census must extend back to the earliest usable EDGAR full-index history (1993 archive onward where available) to reduce left-censoring. If complete predecessor history cannot be established for a filer/subject pair, classify as left-censored; do not call it a true first event.
- Current state: parser prototype and global-census pilot are on this isolated branch; no main-branch workflow has been launched. F80 remains frozen.


## Pilot execution status
- The first hosted global-census run, 41707588968, completed with a validation failure after both test suites passed. Job 126166891297 fetched 1,306 filing-detail pages with zero HTTP errors, but the HTML parser extracted zero Subject CIKs and zero Filed-by CIKs, including the fixed Truist/Federated fixture. Artifact 13267337601 is preserved; its summary correctly reports FAILED_VALIDATION.
- The failure is a page-parser representation mismatch, not missing SEC filings. The master.idx census and candidate selection succeeded: 16,629 13D/G rows, 8,318 accessions, 1,100 target-relevant accessions, and 206 non-target validation accessions.
- A second pilot now uses each accession's candidate archive paths to fetch structured primary_doc.xml directly. It parses subject issuer CIK separately from the XML submission-filer CIK and retains reporting persons and previousAccessionNumber. The new script and tests are on this isolated branch.
- The branch-only workflow is being updated to run the XML pilot; its concurrency group has cancel-in-progress=false so a queued run will not overlap/replace an active run. No main-branch workflow or F80 code is changed.


## 2026-11-03 — 2025Q1 global master-index feasibility result
- The first pilot attempts exposed two implementation errors, not missing SEC data: raw master.idx uses SCHEDULE 13D/G and SCHEDULE 13D/G/A labels as well as SC variants; and filing-detail archive URLs require the accession-number subdirectory. The parser and URL construction are corrected in the isolated branch.
- The saved 2025Q1 master.idx is 30,623,221 bytes / 340,137 lines. It contains 16,629 13D/G rows after form normalization: 4,460 13G, 9,230 13G/A, 538 13D, 2,394 13D/A, and 7 SC 13D/A.
- Grouping by accession produces 8,318 unique accessions: 8,311 have two associated CIK/name rows and 7 have one. Known pairs: 0000092230-25-000015 maps to Federated Hermes ETF Trust (0001849998) and Truist Financial Corp (0000092230); 0000315066-25-000987 maps to Sandisk Corp (0002023554) and FMR LLC (0000315066).
- The master-index CIK pairs are not role-labelled. The pilot must verify Subject and Filed-by from the filing-detail page; row order is not used. The revised pilot fetches all accessions associated with a current candidate CIK plus a deterministic stratified non-target sample.
- Current candidate CIK mapping now includes SEC company_tickers.json, company_tickers_exchange.json, company_tickers_mf.json and a fallback mapper. Multiple CIKs and fund series/class IDs are retained. This is still not a PIT historical security master.
- No forward returns, no group inference, no alpha test. F80 remains frozen.


## 2026-11-03 — SEC ticker-map JSON schema correction
The corrected global-census pilot passed both parser test suites but stopped before the master-index download because company_tickers_exchange.json encodes rows as arrays under top-level fields and data, not as dictionaries. The SEC mutual-fund ticker file may use the same shape. The mapping reader now converts fields/data arrays into named records before extracting CIK, ticker, exchange, series and class. This is an ingestion-format fix, not evidence against SEC coverage; no returns or alpha test.


## 2026-11-03 — XML-based subject-census repair
- Run 41707588968 (job 126166891297; artifact 13267337601) completed as FAILED_VALIDATION. The 2025Q1 master.idx discovery was successful and 1,306 index pages were fetched without HTTP errors, but the HTML text parser returned zero role CIKs. The known Truist/Federated accession also failed its role check. No forward returns were used.
- The repair bypasses the failed HTML role parser for 2025Q1 and fetches `primary_doc.xml` through each CIK archive path associated with the accession in master.idx. Subject issuer CIK comes only from XML `issuerInfo/issuerCik`/`issuerCIK`; submission filer CIK comes separately from `filerCredentials/cik`. These are not reporting-group identifiers.
- Structured XML is a suitable Q1 2025 feasibility route because the SEC's Modernization of Beneficial Ownership Reporting rule required structured Schedule 13D/13G data beginning 2024-12-18 (official rule: https://www.sec.gov/files/rules/final/2023/33-11253.pdf).
- New code: `research/phase35_global_subject_census_pilot_xml.py`; tests: `research/test_phase35_global_subject_census_pilot_xml.py`; failure/repair audit: `research/PHASE35_GLOBAL_SUBJECT_CENSUS_XML_PILOT_FAILURE_2026-11-03.md`.
- Predeclared gates remain >=95% subject and submission-filer CIK coverage, >=95% role-to-master-index-pair consistency, >=95% form agreement, <=5% XML fetch errors, and exact Truist/Federated identity. Current ticker CIKs are still candidate mappings only; 27 tickers remain unresolved in the pilot mapping.
- KnowledgeDate remains the SEC filing date from master.idx, with signal date strictly later. No same-day signal assumption, no forward returns, no economic-group inference, and no alpha claim. F80 remains frozen.


## 2026-11-03 — XML pilot retry: test-fixture robustness fix
- Latest run 41714047979 completed with failure before any SEC census requests. The parser-v3 suite (6 tests) and master-index suite (4 tests) passed; the XML pilot suite had 2 passes and 1 error.
- The failing negative test intentionally used `https://example.invalid/primary_doc.xml` to verify that a missing reporting-person CIK does not invent a group. `identity_row()` unconditionally split the URL on `/data/` to derive archive_path_cik, causing IndexError. This is a local robustness defect, not a source-coverage or SEC HTTP failure.
- Replaced the unconditional split with a guarded SEC archive-path parser; non-archive URLs now yield null. Added assertions for both a real SEC archive URL and the negative URL.
- Latest run produced no artifact because the pilot step was skipped after the unit-test failure. No SEC census, forward returns, or economic test ran. The corrected branch push will trigger one new pilot run; no overlapping run was active at the time of the fix.
- F80 remains frozen; 13D/13G remains a data-feasibility project only.


## 2026-11-03 — XML pilot retry: regex escaping correction
- Run 41724302967 again stopped before the SEC census. The 6 parser-v3 tests and 4 master-index tests passed; the XML identity suite had 2 passes and one assertion failure.
- The first guarded archive-path patch was itself over-escaped: its regex matched a literal backslash-d rather than numeric path digits, so a valid SEC URL returned null. This was a patch-generation defect, not a data/source failure.
- Corrected the regex to match the numeric CIK segment in `/Archives/edgar/data/{cik}/`; the negative non-archive URL still returns null. The existing test asserts both behaviors.
- No census requests, artifact, forward returns, or economic test occurred in run 41724302967. A single corrected push will rerun the branch-only workflow.


## 2026-11-03 — Phase 35 global subject census: 2025Q1 XML pilot result
- Run [41724414979](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41724414979) succeeded; job 126225315601; artifact `phase35-global-subject-census-xml-2025q1` ID 13274405289 (SHA-256 `9cbcb2b7c9f19d008e56bbbd882ce7009f9628d0ed9a3f7c28930827feadd591`).
- **PASS is limited to 2025Q1 structured-XML subject/filer identity feasibility.** 16,629 master-index rows; 8,318 unique 13D/G accessions; 1,100 candidate-relevant accessions plus 206 non-target validation accessions; 1,299/1,306 XMLs parsed; seven 404s, all in non-target validation. Subject and submission-filer CIK coverage were 100% in the target-relevant sample and 96.60% in the non-target sample; XML form match 99.46%; fixed Truist/Federated fixture passed.
- Current candidate mapping: 307 CIKs for 335 tickers; 27 tickers unresolved. This is not a historical security master.
- Crucial distinction: 242 filings have a subject issuer CIK in the candidate universe (142 distinct subject CIKs: 16 with 13D-family filings and 130 with 13G-family filings, four overlapping). 904 filings have a candidate submission-filer CIK; 858 are filer-only cross-issuer records. The 1,100 discovery union is not the target-subject count.
- Target-subject filings: 4 SC 13D, 25 SC 13D/A, 49 SC 13G, 164 SC 13G/A. The 13D sample is sparse (29 filings, 16 subjects) for one quarter.
- The 13G schema makes `reportingCik` optional; all 474 target-subject 13G reporting-person records in this pilot lack an explicit CIK. This is not a parser failure and does not authorize substituting the submission-filer CIK. A deterministic type-aware name crosswalk uniquely matched the filer to one reporting person in 203/213 target-subject 13G filings (95.3%) and 91/100 non-target validation filings (91.0%); two cases in each sample were ambiguous. These are candidate-link coverage rates, not measured precision. Freeze and validate on separate quarters before use; do not infer a complete group from one matched person.
- 13D explicit reporting-person CIK coverage: 7/8 persons in originals (87.5%) and 37/73 in amendments (50.7%); explicit no-CIK flags account for many missing identifiers.
- Amendment lineage remains blocked: previousAccessionNumber exists in 19/25 13D/A and 126/164 13G/A records; six 13D/A and 38 13G/A are unresolved. The 13G/A field may be optional, and a pointer is not necessarily the immediately preceding amendment. The parser also needs to emit amendmentNo.
- Historical active-universe membership, the 27 unresolved tickers, legacy HTML/TXT subject attribution before structured XML, and economic-group normalization remain unpassed. No forward returns were used. Full audit: [PHASE35_GLOBAL_SUBJECT_CENSUS_XML_PILOT_RESULTS_2026-11-03.md](research/PHASE35_GLOBAL_SUBJECT_CENSUS_XML_PILOT_RESULTS_2026-11-03.md).
- Next: validate the frozen name crosswalk on 2025Q2/Q3; add amendmentNo and lineage diagnostics; extend quarter-by-quarter global discovery; then solve historical F80 membership and legacy filings. No economic test until all event/group gates pass.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-03 — Cross-quarter identity validation launch history
- Canonical research branch commit: `a73e60621fbe9abb76a2b98cc600c82fabc637ef`.
- Added `amendmentNo` extraction to parser v3, deterministic filer-to-reporting-person candidate crosswalk code/tests, and a Q2/Q3 validation workflow. The crosswalk never overwrites source CIKs and never infers an economic group.
- Runs [41729360514](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41729360514) (canonical branch) and [41729228829](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41729228829) (prototype branch) both completed successfully. They covered the same Q2/Q3 workload because the run list was delayed after the prototype branch push. The canonical-branch artifact is the reference result; the duplicate artifact is not pooled as an independent sample.
- The completed Q2/Q3 findings are recorded in `research/PHASE35_CROSS_QUARTER_13DG_IDENTITY_VALIDATION_2025Q2_Q3_2026-11-03.md`.


## 2026-11-03 — Phase 35 cross-quarter identity validation completed (2025Q2–Q3)
- Canonical run [41729360514](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41729360514) completed successfully (job 126242359519; artifact 13277920675; SHA-256 3ab744ca033ec1af94c7586004bbe3ce9dd0bed9b5d8677cfd5e27a41c06c5b4). Duplicate prototype-branch run 41729228829 also completed; use the canonical artifact as the reference. No workflow remains active.
- Q2/Q3 global XML subject/filer identity gates passed in the tested samples: target-relevant subject/filer CIK coverage 100% in both quarters; non-target validation coverage 98.52%/99.50%; form agreement 99.83%/99.92%. Target-subject counts were 289 (Q2) and 252 (Q3), not the larger filer/subject discovery unions. XML fetch errors (3 and 1) were confined to non-target validation samples.
- Frozen exact-name filer-to-reporting-person candidate crosswalk coverage: target 13G 252/264 (95.45%) Q2 and 209/216 (96.76%) Q3; non-target 13G 95/100 and 96/100. These are coverage rates only; 13G explicit reporting CIK was absent in all tested records, so do not claim measured 13G precision or infer a group.
- Independent label check: for unique 13D name matches, candidate filer CIK equaled the explicit XML reporting-person CIK in 57/57 target-subject matches and 180/180 non-target validation matches (237/237, zero mismatches; 197 distinct CIKs). This validates the exact-name link in the tested 13D subset, not all 13G records or group identity.
- Target-subject 13G group markers were mostly unavailable (337/480 all missing; 134 all “b”; 9 all “a”). Target-subject amendments totalled 406; amendmentNo was present in all 406, but previousAccessionNumber only in 197/406 (48.52%). Missing lineage remains unresolved; amendmentNo alone does not identify the immediately prior filing.
- Added reproducible validator and tests: `research/phase35_13dg_crosswalk_precision_validation.py` and `research/test_phase35_13dg_crosswalk_precision_validation.py` (5 tests pass). Full report: `research/PHASE35_CROSS_QUARTER_13DG_IDENTITY_VALIDATION_2025Q2_Q3_2026-11-03.md`.
- Current ticker map remains 307/335 with 27 unresolved ETF-like symbols; this is not historical F80 membership. No forward returns, economic-group inference, or alpha test. Keep F80 frozen.
- Next: keep the crosswalk rule frozen and test 2025Q4/2026Q1; retain unmatched names as unresolved; then tackle amendment chains, historical ticker/CIK/CUSIP/listing-status continuity, and pre-structured-XML legacy filings before any economic test.


## 2026-11-03 — Next frozen-rule validation queued
- Added manual/push-scoped workflow `.github/workflows/phase35_q4q1_crossquarter_validation.yml` to validate the unchanged crosswalk on 2025Q4 and 2026Q1 and run the explicit-13D-CIK precision check. It is isolated to this research branch and uses a distinct concurrency group.
- Run [41742690656](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41742690656) completed successfully on commit `fd7bf942634801fac9f4430e75e34ea81dc38f7f` (artifact 13282921575). No further Q4/Q1 run is needed.
- The Q2/Q3 crosswalk and precision rule are frozen; no aliases or fuzzy matching will be added after seeing those results.


## 2026-11-04 — Phase 35 Q4/Q1 validation and amendment-lineage audit
- Canonical run [41742690656](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41742690656) completed successfully (job 126287874908; artifact 13282921575). The Q4/Q1 XML subject/filer identity gate passed: 100% target subject/filer CIK coverage in both quarters; Q4 non-target validation 100%; Q1 non-target validation 99.01%; XML form match 100%/99.84%. Q1's two XML fetch errors were confined to the non-target validation sample.
- The Q1 pilot was the development sample. The frozen exact-name filer-to-reporting-person crosswalk then produced 237/237 exact matches against explicit 13D reporting-person CIKs in the first Q2/Q3 held-out validation and 231/231 in the second Q4/Q1 held-out validation (zero mismatches in both). The pooled two-holdout count is 468/468. This is conditional precision among unique matched 13D cases, not universal precision.
- 13G target unique-name-match coverage: Q4 219/224 (97.77%), Q1 457/463 (98.70%), Q4/Q1 held-out combined 676/687 (98.40%), and combined Q2–Q1 1,137/1,167 (97.43%). This remains coverage only; explicit reporting-person CIKs were absent in the tested 13G XMLs, so 13G precision and group identity are not established.
- The four-quarter target-subject panel contains 1,278 accessions (111 13D; 1,167 13G). Of 98 13D/A amendments, 57 contain previousAccessionNumber (58.2%); of 925 13G/A, 331 contain it (35.8%).
- In-panel explicit references: 23 13D and 94 13G. All 23 13D references match subject/family/person/CUSIP. Of 94 13G references, 92 have the same uniquely matched person name, 92 have CUSIP overlap, and 90 satisfy both. Among comparable person+CUSIP references, 19/23 13D and 75/90 13G point to the latest earlier in-panel candidate; 4/23 13D and 13/90 13G point to an older accession; 2/90 13G are same-day and cannot be ordered by filing date alone.
- **Methodology correction:** previousAccessionNumber is an explicit prior-filing reference, not a guaranteed immediate-predecessor edge. Preserve it as a chain anchor; never assume it identifies the immediately preceding amendment. A unique earlier same-subject/person/CUSIP candidate for a missing pointer remains unassigned because the four-quarter panel is left-censored.
- Missing-pointer candidate counts (not assignments): 13D/A — 11 unique, 8 multiple, 19 zero in-panel, 3 unmatched/missing CUSIP; 13G/A — 150 unique, 38 multiple, 400 zero in-panel, 6 unmatched/missing CUSIP. A zero in-panel candidate does not prove no earlier filing.
- Added reproducible audit script/tests and reports: research/phase35_13dg_lineage_feasibility_audit.py, research/test_phase35_13dg_lineage_feasibility_audit.py, research/PHASE35_13DG_LINEAGE_FEASIBILITY_AUDIT_2026-11-04.md. Four helper tests are included; the equivalent local prototype test harness passed, but the repository test file has not yet been run by GitHub Actions. Full artifact review and lineage analysis are recorded there.
- No forward returns, event-direction labels, threshold/horizon selection, or alpha test. The historical F80 universe, pre-2024 legacy filing coverage, reporting-group continuity and same-day accepted timestamps remain unpassed. F80 stays frozen.

## Phase 50 — SEC Form 144 feasibility review (2026-11-04)
- Latest run 40961563763 failed (job 123755365019; artifact 12936426126). The two Phase 50 runs are completed; no workflow is active.
- The failed artifact had 301/335 current CIK mappings, 165 issuer hits, 132 HTTP 403 query errors, and four successful no-hit queries. The 54.8% hit rate is a lower bound with 132 unresolved queries; among 169 successful queries, 165 had a hit (97.6%). Do not interpret this as a true coverage failure.
- Only 6/25 sampled XMLs downloaded. Field-presence zeros for securitiesClassTitle, noOfUnitsSold, acquiredDate, and natureOfAcquisitionTransaction are parser false negatives: the code searched incorrect tag names. The archive resolver also assumes accession-prefix CIK equals archive-path CIK, which is not reliable for Form 144.
- SEC examples show distinct accession prefix, archive-path/filer CIK, and subject issuer CIK. The XML includes explicit issuerCik, filer credentials, sale quantity/value/date, security class and acquisition fields. Form 144 remains conditional / not killed pending a corrected archive resolver, actual XML parser, rate-limited/batched discovery, 144/A lineage, and prospective-vs-retrospective classification.
- PIT caveat: Form 144 is a notice, not proof of execution. Some filings are retrospective/late and describe sales already executed before filing. Use SEC acceptance timestamp (or filing date with next-session use); never use approxSaleDate as KnowledgeDate. Exclude retrospective notices from prospective planned-supply features.
- Review: research/PHASE50_FORM144_FEASIBILITY_REVIEW_2026-11-04.md. No forward returns or alpha test.


## 2026-11-04 — Phase 54 Cboe Open-Close EOD candidate
- Reopened Cboe options data through a lower-cost EOD product distinct from the previously parked TBT feed. The Open-Close EOD summary classifies contract volume by Firm, Broker/Dealer, Market Maker, Customer and Professional Customer, with buy/sell and open/close dimensions; customer and professional-customer activity has contract-size buckets.
- Official EOD specification v1.3 documents next-morning delivery typically 00:30–01:00 US Eastern, C1 history from 2005-01-03 and BZX/C2/EDGX from 2018-01-02. The product is limited to Cboe exchanges, not all OPRA.
- Historical OI conventions require correction/exclusion: C1 shifted one day ahead through 2019-10-04; C2 through 2018-05-11. C2 total industry volume doubled through 2018-05-11. Total industry volume and OI are third-party best-effort fields.
- Current official Cboe fee schedule (2026-11-02) lists EOD daily updates at $600/month and historical downloads at $600 per month of history for 1–4 years and $300 per month of history for 5+ years. It lists a free historical sample for 2022-07-01 through 2022-12-31 for first-time recipients; this is a six-month sample, not a subscription trial. Exact price for a 335-symbol pick-list/multi-year order must be confirmed.
- Added sample-schema audit and tests: `research/phase54_cboe_open_close_eod_feasibility.py`, `research/test_phase54_cboe_open_close_eod_feasibility.py`, `research/PHASE54_CBOE_OPEN_CLOSE_EOD_FEASIBILITY_SPEC_2026-11-04.md`.
- No forward returns. Participant categories are capacity labels, not proof of institutional/informed behavior. Cboe exchange coverage, historical PIT mapping and price/licensing gates remain.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-04 — Phase 54 Cboe Open-Close sample result
- Run [41762583602](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762583602) passed; artifact 13291147097.
- Public ZIP contains 1m, 10m and EOD samples. EOD C1 20% sample for 2025-03-28: 23,179 rows, 288/335 current frozen tickers (85.97%), all required EOD/participant fields present and 100% non-null. EOD schema gate PASS.
- Cboe exchange-to-industry volume ratio median 0.5, p90 2.0; not accepted as market share until units/conventions are reconciled.
- Result recorded in `research/PHASE54_CBOE_OPEN_CLOSE_SAMPLE_RESULTS_2026-11-04.md`. This is sample schema/initial reach only, not full historical coverage or alpha.
- Cboe Open-Close EOD is now a high-priority options-flow candidate, paired with full-OPRA Option EOD Summary for IV/Greeks/OI. Licensing and PIT mapping remain gates. F80 remains frozen.


## 2026-11-04 — Cboe participant taxonomy / signal design
- Official Cboe factsheet defines Customer/Individual as retail **and institutional** clients; Pro Customer as professional traders and institutional participants; Firm as proprietary trading firms/market participants; Market Maker as designated liquidity providers. Do not equate these labels with investor identity.
- Opening Buy initiates/increases a long option position; Opening Sell initiates/increases a short; Closing Buy reduces/eliminates a short; Closing Sell reduces/eliminates a long. The factsheet's ~98% classification figure is for activity included within Cboe exchange data, not 98% of total OPRA market volume.
- Candidate hypothesis: participant-specific net opening delta, separately from closing flow and calls/puts, joined to full-OPRA 15:45 delta/IV. Normalize only after OI/volume convention reconciliation; control for prior returns/volatility to test prediction versus chasing. No alpha test yet.


## 2026-11-04 — Phase 56 Cboe integration design
- Added `research/PHASE56_CBOE_OPEN_CLOSE_OPTION_EOD_INTEGRATION_SPEC_2026-11-04.md`.
- Pre-registers participant-specific net opening delta, closing flow separately, call/put and size buckets, full-OPRA IV/OI join, controls for prior returns/volatility, chronological OOS, identical exposure/costs, block bootstrap, ticker-clustered inference and LOO.
- No return test until 335-ticker historical coverage, PIT KnowledgeDate, option-root mapping, field conventions and licensing pass. F80 remains frozen.


## 2026-11-04 — Phase 53B OCC Volume Query corrected post-run
- Canonical corrected run [41763113005](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41763113005), job 126356693552, artifact 13292225481: 3 parser tests PASS; 670 ticker/date queries; zero query errors.
- Valid/schema responses: 325/335 (97.01%) on 2025-01-03 and 320/335 (95.52%) on 2026-11-02; 645/670 combined (96.27%). ActivityDate matched the requested date in 100% of valid rows.
- Account-type presence: Customer C 325/325 and 318/320; Firm F 229/325 and 222/320; Market Maker M 325/325 and 320/320.
- OCC explicitly rejected 2024-01-03 as older than its 24-month retention. Data depth gate FAIL_FOR_LONG_OOS; PIT publication timestamp NOT VERIFIED.
- The response is underlying/root-level call/put volume by account type and exchange, with no strike, expiry, buy/sell, open/close or OI. Retain only as a recent complementary feature; no forward returns. Updated report: `research/PHASE53B_OCC_VOLUME_QUERY_FULL_UNIVERSE_RESULTS_2026-11-04.md` on branch `phase53-occ-daily-open-interest-audit`.

## 2026-11-04 — Phase 54/55 Cboe sample gates clarified
- Phase 54 run [41762583602](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762583602), artifact 13291147097: C1 EOD sample for 2025-03-28 is a 20% sample, 23,179 rows, 288/335 current symbols (85.97%); EOD schema gate PASS. The same ZIP has separate 10m/1m samples (78,468 rows, 302/335; 87,322 rows, 305/335). None establishes full historical or all-exchange coverage.
- Phase 55 run [41763011186](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41763011186), artifact 13290668468: 32,672 rows per variant, four underlyings (^SPX, SPY, TSLA, ^VIX), only TSLA overlaps current 335 (1/335). Base schema and Calcs gates PASS; universe coverage explicitly NOT TESTED. Positive IV 92.75%/91.26%, positive OI 77.20%, positive volume 40.35%; zero Greeks/IV require validity filters.
- Do not treat either public sample as evidence of full F80 universe coverage. Build denominator from point-in-time F80 members with OPRA-listed/traded options.

## 2026-11-04 — Phase 56 options panel methodology correction
- Added `research/PHASE56_CBOE_OPTIONS_PANEL_METHOD_CORRECTIONS_2026-11-04.md`.
- Net delta must use PIT contract multiplier/deliverable (no blanket 100 multiplier); 15:45 Delta is a common mark, not exact trade-time Delta for all-day Open-Close volume.
- Cboe participant flow is venue-specific, not all OPRA. Use full-OPRA volume and prior-available OI for normalization; retain Cboe venue share and optionability coverage separately. Use exact OCC series mapping and adjusted-root/deliverable controls.
- For the end-of-day strategy, use conservative next-session KnowledgeDate and next-session close execution for both baseline and augmented portfolios. No return test authorized.

## 2026-11-04 — Phase 57 MIAX Open-Close EOD candidate
- Added `research/PHASE57_MIAX_OPEN_CLOSE_EOD_FEASIBILITY_2026-11-04.md`.
- MIAX Options, Pearl and Emerald EOD reports start June 2021; Sapphire starts August 2024. MIAX says EOD files are available around 06:00 ET on the calendar date after trade date. Fields include origin, buy/sell and open/close by option series; EOD also includes first/high/low/close, industry volume and OI.
- MIAX origin labels differ from Cboe and must remain separate. The feed is venue-specific and requires a data agreement/Schedule B; no sample was acquired.
- Published historical EOD price is $500 per request/month per exchange; monthly EOD subscription $600 per exchange. The 20% discount through 2026-12-31 is subject to existing-subscriber/size conditions (Sapphire has no minimum purchase size). No purchase authorized.
- Decision: conditional independent venue-replication source, lower priority than completing Cboe full-OPRA and Cboe Open-Close gates. No forward returns.

## 2026-11-04 — Phase 50 Form 144 execution status
- [Run 41761510120](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41761510120) remains in progress in the global-index/Form 144 pilot; its XML-sample selection step is still running and no artifact is available.
- [Run 41761577180](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41761577180) is pending on a newer commit that fixes sample selection to use `master_index_form` rather than a missing `form` key. The two commits between the runs are `b3a391f` and `5b94e2f`.
- Do not launch another Phase 50 run while either existing execution is active/pending. Review both outcomes and use the latest corrected commit for any future rerun.


## 2026-11-04 — Phase 50 correction; MIAX 1-minute archive; Intrinio candidate

### Phase 50 — Form 144
- Run 41754622148 / artifact 13287867124 technically completed, but its 50-document sample contained 50 Form 144/A and zero original Form 144 notices. It is a parser/field pilot for amendments only, not a source-wide coverage pass.
- All 50 `approxSaleDate` values were incorrectly classified as unknown because the parser accepted ISO dates only; SEC XML values are MM/DD/YYYY. Independent reparse: 34/50 dates precede filing date, 16/50 same day. This does not establish execution.
- Global master-index pilot run 41761510120 remains in progress at the 2025Q1 global-index step; run 41761577180 is queued under the same concurrency group. Do not start another run. No artifact or source-coverage conclusion is available yet.
- Keep Form 144 conditional; no return test.

### Phase 57 — MIAX Open-Close
- Corrected historical-depth statement: EOD history starts at exchange inception (June 2021 for Options/Pearl/Emerald; August 2024 for Sapphire), but the newly announced 1-minute intraday archive reaches back to January 2013 (MIAX Options), March 2017 (Pearl), March 2019 (Emerald), and August 2024 (Sapphire).
- 1-minute history is materially more expensive: MIAX Options current 2026-11-01 schedule lists $4,000 per request per month historically and $9,000/month subscription. Its 10-minute history is $1,000 per request per month; EOD is $500 per request per month. A 1-minute historical request includes 10-minute and EOD data for the same range.
- For this daily EOD strategy, prefer EOD feasibility first; 1-minute history is conditional and not cost-justified without a specific intraday hypothesis.

### Phase 58 — Intrinio U.S. EOD Historical Options
- Status: CONDITIONAL LOW-COST FULL-OPRA CONTEXT; sample required.
- Official product page advertises OPRA-sourced daily full chains, bid/ask, volume, OI/OI change, IV change and Greeks; standard history from 2021-09-27, bulk history to 2008-01-02, and Individual plan from $150/month with free trial.
- The 3:00 a.m. ET delivery version suggests a conservative next-session KnowledgeDate, but actual historical delivery evidence is still required.
- Critical risk: the by-ticker API is described as returning contracts currently associated with a ticker. Expired contracts, delisted underlyings and historical option roots must be tested before any use; no historical coverage is inferred from marketing claims.
- Intrinio and Cboe Option EOD are both OPRA-sourced and therefore are vendor alternatives/cross-checks, not independent market venues. Intrinio does not identify participant origin or opening/closing status.
- No data purchased/downloaded, no forward returns, no alpha claim.

### Frozen control
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No source in Phases 50, 57 or 58 is promoted to alpha.


## 2026-11-04 — Phase 59 options-vendor cross-source audit

- Added `research/PHASE59_OPTIONS_VENDOR_CROSS_SOURCE_FEASIBILITY_2026-11-04.md` on isolated branch `phase59-options-vendor-cross-source-audit`.
- **New priority candidate: OptionMetrics IvyDB US + Signed Volume.** IvyDB US advertises all US exchange-traded equity/index options (including ETFs/ADRs) from 1996-01, permanent security IDs, ticker/name changes, corporate-action and split/spinoff adjustments, and delisted-security continuity. Signed Volume advertises buyer-/seller-initiated option volume since 2016-01, EOD and 5-/30-minute snapshots; lot-size fields begin in 2021. Direction is inferred from trade price versus contemporaneous bid/ask. This is signed aggressor-side demand, not opening/closing, beneficial-owner identity or proof of informed trading. Price, exact granularity history, field definitions, PIT release timestamps, coverage sample and license terms require written quote/sample.
- **ORATS Near-EOD** is a stronger lower-cost context candidate than assumed in Phase 58: full US options chains, 5,000+ symbols, history from 2007, snapshot 14 minutes before close, call/put volume and OI, NBBO bid/ask sizes/prices, IV, SMV and Greeks. The recurring data file is delivered nightly at midnight; use next-session KnowledgeDate and next-session close execution unless earlier availability is independently proven. A one-time historical archive is available through S3; exact archive pricing is not public. The $199/month delayed API plan advertises 20,000 requests/month and history endpoints; a full 335-symbol daily backfill through the API is roughly 34 calls/date (max 10 tickers/call), or ~163k calls for ~4,800 sessions (~9 monthly quotas before retries). Confirm archive/API entitlements and price before purchase.
- **Intrinio correction:** official Options Gold guide says the ticker contract endpoint returns all expired and active contracts available for a ticker; historical expirations before 2021-10-10 require a separate subscription. This partially addresses expired-contract risk, but not delisted-underlying or PIT-universe coverage. Individual $150/month is personal-use only; Startup starts at $333/month with commercial/business-wide rights. CSV delivery is offered for historical backfill.
- Databento OPRA history from 2013-04 is a conditional reconstruction route using trades + CBBO-1m to independently sign aggressor flow; no open/close or beneficial-owner fields. ThetaData remains a limited-history/sample alternative; its public free-tier statements need reconciliation.
- New flow terminology: for Signed Volume use `signed_delta_demand = Σ delta × PIT multiplier × (buyer_initiated_volume − seller_initiated_volume)`; never call this net opening delta or net position change. Exclude midpoint/unclassified volume from directional numerator unless a validated vendor rule is supplied. Lot size is a proxy hypothesis only from 2021 onward.
- Decision: request sample/quote for OptionMetrics Signed Volume first and ORATS Near-EOD second; retain Intrinio as backup. Do not purchase Cboe/MIAX multi-year archives before these broad-market gates. No data purchased/downloaded, no forward returns, no alpha claim.
- Phase 50 run 41761510120 remains marked in progress at the global-index step; queued run 41761577180 remains pending. The job-log download returned BlobNotFound and no artifact is available. No duplicate run launched.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; `main` unchanged.


## 2026-11-04 — Phase 59 options vendor re-ranking and Cboe artifact review
- ORATS official Near-EOD page confirms a complete 3:46 p.m. ET US equity-options chain snapshot, >5,000 symbols, history from 2007, bid/ask, volume, prior-night OCC OI, SMV IV and Greeks. Delisted tickers are stated to be retained from 2007-01-01. Individual historical archive is $599 one-time (~500 GB) and recurring daily files $99/month; professional/institutional pricing is separate. Archive access via S3 lasts 14 days. Default KnowledgeDate remains next trading session because recurring files arrive around midnight.
- ORATS volume is the session total only as of the 3:46 p.m. snapshot, not necessarily final daily volume; OI is previous-night OCC data. Underlying values are derived from put-call parity, not an independent stock-price series.
- OptionMetrics' current preferred product is IvyDB TradeFlow, an evolution of Signed Volume: all US options since 2016, 5/30-minute/EOD snapshots, bid/ask/midpoint, buy/sell pressure, lot sizes, trade-description codes, venue data, VWAP and NBBO aggressiveness. Retail/institutional categories are proxies until exact definitions and thresholds are supplied; no account identity or open/close claim is assumed. IvyDB US base history begins 1996 and documents permanent IDs, corporate-action continuity and delisted/name-changed securities.
- Databento OPRA offers trades, OHLCV, statistics, definitions and CBBO-1m from 2013-04-01; CMBP-1/TCBBO from 2023-03-28. Historical cost is usage-based and exact OPRA pricing must be estimated from the selected dataset/schema; do not assume the generic $199 Standard plan is an OPRA quote.
- Downloaded Cboe artifacts were independently rechecked: Open-Close EOD 20% sample contains 23,179 rows and 288/335 candidate tickers (85.97%); 1m and 10m samples contain 305/335 (91.04%) and 302/335 (90.15%). EOD sample has required participant and OI fields, but a header typo `cust_gt_199_clsoe_buy_qty` and a questionable total_exchange_vol/total_industry_vol ratio (median 0.5, p90 2.0, 32.7% above 1) mean no market-share normalization is authorized until reconciled. Cboe Option EOD Summary sample validates schema only: four underlyings, one target ticker.
- OCC artifact confirms 95.52–97.01% recent ticker coverage but a 24-month retention boundary and no aggressor-side/open-close/strike-level position data.
- Added `research/PHASE59_ORATS_TRADEFLOW_AND_CBOE_ARTIFACT_REVIEW_2026-11-04.md` and `research/PHASE59_VENDOR_SAMPLE_REQUEST_AND_ACCEPTANCE_CHECKLIST_2026-11-04.md`.
- Revised priority: ORATS Near-EOD for affordable historical context; OptionMetrics TradeFlow for directional/proxy flow; Databento OPRA for optional independent reconstruction; Cboe Open-Close for exchange-specific opening/closing. No data purchased, no vendor contacted, no forward returns or alpha tests. F80 baseline remains frozen.


## 2026-11-04 — Phase 60 OptionMetrics DOOD hypothesis preregistered
- Reviewed OptionMetrics' 2023 DOOD research note. It reports a 32 bp weekly high-minus-low spread, long/short Sharpe ~1.03 and weekly three-factor alpha ~0.26% over Jan 2016–Mar 2022. The study filters to optionable, top-90%-market-cap, >$5 stocks, excludes ETFs/indices, requires IV <300% and ask volume >=1,000, and rebalances weekly. This is vendor-produced prior evidence, not independent OOS validation for F80.
- The paper explicitly offers both informed-trading and dealer-hedging/momentum explanations; DOOD is autocorrelated. We will require the signal to survive controls for prior 1/5/20/60-session returns, volatility, liquidity, earnings and F80/LTM.
- Added `research/PHASE60_OPTIONMETRICS_DOOD_REPLICATION_PREREGISTRATION_2026-11-04.md` with a fixed data gate, signed delta-demand formula using historical contract multipliers, separate ambiguous/midpoint volume, competing hypotheses, chronological splits, horizon-decay tests and kill criteria.
- Phase 60 is preregistration only. No vendor sample acquired, no forward returns calculated, no alpha claim, no strategy change. F80 baseline remains frozen.


## 2026-11-04 — Phase 61 ORATS public sample audit launched
- Added `research/phase61_orats_near_eod_sample_audit.py`, four parser/coverage tests, workflow and specification to inspect ORATS' public 2024-01-03 Near-EOD ZIP without purchasing data.
- Run [41787946992](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41787946992) is queued. It will report schema, 335-name sample coverage, field completeness/zero rates, and whether multiplier/deliverable fields exist. A single-date sample cannot validate delisted retention or long-run historical coverage.
- No forward returns, alpha tests, data purchase or strategy change. F80 remains frozen.


## 2026-11-04 — Phase 61 ORATS public sample result
- Run [41787946992](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41787946992) completed successfully; artifact 13301409440 was downloaded and independently inspected.
- Public ORATS sample 2024-01-03: 716,822 rows, 5,787 underlyings, 39 columns, 324/335 current candidate tickers present (96.72%). This is one-date coverage against today's list, not historical PIT F80 coverage; 11 absent names may not have been listed/optionable on that date.
- Core trade-date/expiry/strike, call/put volume and prior-night OI, bid/ask, IV and Greeks fields were present and 100% non-null. Zero values are common and must be distinguished from missingness: call/put volume positive in 16.41%/13.36% of rows; call/put OI positive in 50.61%/41.45%; smoothed IV positive in 100%.
- `cOpra`/`pOpra` identifiers exist, but no explicit multiplier/deliverable field exists. `stkPx`/`spot_px` are derived option-implied values, not independent stock prices. External OCC contract-reference mapping is required.
- ORATS passes one-date schema and indicative coverage only. Delisted/expired continuity, historical PIT publication, historical F80 coverage and multipliers remain untested. The sample's Last-Modified header is a hosting timestamp, not historical availability evidence.
- Added `research/PHASE61_ORATS_NEAR_EOD_PUBLIC_SAMPLE_AUDIT_RESULTS_2026-11-04.md`. No data purchased or forward returns tested. F80 remains frozen.

- Added a classification caution: OptionMetrics' 2026 SPX/SPY 0DTE study reports retail-share estimates ranging roughly 10–60% across methodologies (its public-OPRA method ~30–35% SPX versus a cited Cboe proprietary ~50–60%). This is not generalizable to single names, but reinforces that TradeFlow retail/institutional categories are vendor proxies, not actual account identity. See `research/PHASE61_ORATS_NEAR_EOD_PUBLIC_SAMPLE_AUDIT_RESULTS_2026-11-04.md`.

- Concurrent SEC Form 144 global-index runner [41787233183](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41787233183) remains the only active Actions run. Its parser/PIT tests passed and the 2025Q1 detail-page census is still in progress; no artifact is available and the job-log endpoint currently returns BlobNotFound. No further Phase 50 execution was started.


## 2026-11-04 — Phase 62 IVolatility options data feasibility

- New highest-priority conditional vendor candidate: IVolatility EOD + Option Trades. Current official managed-DB documentation lists EOD NBBO/Raw IV, a 15:45 ET snapshot, non-standard options with adjusted deliverables, stable option IDs across corporate actions, full symbol history including listings/delistings, and trade-level price/size/exchange/condition with option NBBO and underlying quotes at trade time.
- US EOD options history is advertised from 2005 across 5,500+ underlyings. A legacy intraday guide (last updated June 2020) documents option trade history from 2014-03-13, daily updates, trade-condition codes, contemporaneous quotes and IV/Greeks. Exact current intraday depth, field schema and delivery schedule require written confirmation.
- This could allow a transparent buyer/seller aggressor-side reconstruction from execution price versus contemporaneous NBBO, while retaining midpoint/inside-spread/ambiguous trades as unknown. Complex, multi-leg, auction, late/out-of-sequence and cancellation conditions must be separated using date-aware condition-code versions.
- Current docs say daily updates include corrections to past history. A corrected backfill is not a PIT vintage. Require archived daily deliveries/correction history; until then use next-session KnowledgeDate conservatively and do not authorize returns.
- Important product-scope conflict: FAQ says listed and delisted names; Data Download page says currently listed; managed DB describes full listing/delisting history. Confirm per product and sample.
- Data Download retail indicative prices: $0.40 per ticker-day for NBBO/options prices + historical volatility; $0.60 for Raw IV/IV surface/IV index. At 335 symbols x 252 sessions, indicative cost is $33,768/$50,652 per year; five years $168,840/$253,260. Professional use and intraday trades are custom quote/contract. No purchase or vendor contact authorized.
- Phase 62 report: research/PHASE62_IVOLATILITY_OPTIONS_DATA_FEASIBILITY_2026-11-04.md. No sample downloaded, no forward returns, no alpha test. Phase 60 DOOD preregistration unchanged; F80 remains frozen.

## 2026-11-04 — Phase 50 role-label parser correction

- Run 41787233183 completed with all 9,104 index pages fetched and zero HTTP errors but failed the data gate because Subject/Reporting CIK extraction was 0%. The HTML-to-text adapter removes anchor tags and leaves spaces inside role labels, e.g. "( Subject ) CIK".
- Updated the parser to tolerate whitespace inside role-label parentheses and added an anchor-wrapped HTML regression test. Commits: 65a5930dc0095efdf883cd532805de1046c6d0a7 and 5001cb1aa5caeb34a4d9e7e531cac446e51fea6c.
- The correction is not yet considered hosted-verified. The next Phase 50 Actions result must pass the new regression test and recompute subject/reporting identity. No economic test authorized.


## 2026-11-04 — Phase 63 ThetaData OPRA trade/quote feasibility
- Added `research/PHASE63_THETADATA_OPRA_TRADEQUOTE_FEASIBILITY_2026-11-04.md` and `research/PHASE63_THETADATA_SIGNED_FLOW_PIT_SPEC_2026-11-04.md`.
- ThetaData v3 documents OPRA option trade/quote history with every trade paired to the last NBBO; historical quote matching uses millisecond timestamps. Use `exclusive=true` so quote_timestamp is strictly earlier than trade_timestamp.
- Pricing page: individual Standard $80/month/10 years; Pro $160/month/14 years. Pro is required for trade-Greeks endpoints. Individual plans explicitly prohibit business use/redistribution. Business options page lists $1,600/month billed annually and startup pricing from $500/month, subject to quote/eligibility.
- Options page advertises OPRA history since 2012-06 and 100% NBBO coverage. This is not a historical F80 or delisted-underlying coverage audit.
- Trade quote API multi-day requests are limited to one month and require an expiration; `expiration=*` is documented for all expirations. Request sizing recommends one week for option tick-level and one day for highly liquid names. Historical flat-file trade_quote/EOD pages document only the latest seven calendar days; longer historical flat files require sales.
- Trade-Greeks endpoint (Pro) supplies Delta, IV and underlying price/timestamp at trade time. It defaults to Black-Scholes, SOFR and no dividend; PIT rate/dividend inputs and binomial/own-Delta sensitivity are required. OI is normally reported around 06:30 ET and represents the previous trading day's close; zero-OI contracts may have no new message.
- Trade conditions include auto-execution, complex spreads/straddles/buy-writes/combos, contingent/cross and cancellation codes. Historical API schema does not document the flat-file `records_back` correction field; cancellation semantics remain an acceptance gate. The free sample bundle documents stock UTP/CTA data only, not options.
- Decision: **CONDITIONAL HIGH-PRIORITY RAW OPRA CANDIDATE**, not a data PASS. Require business-use license, historical sample including delisted/adjusted names, cancellation lineage, historical symbol coverage, PIT delivery timestamps and OCC multiplier/deliverable reconciliation. No vendor contacted, no data acquired, no cost incurred, no returns tested.

## 2026-11-04 — Phase 63 SEC Form 144 master-index CIK-pair diagnostic
- Added `research/PHASE63_FORM144_MASTER_INDEX_PAIR_IDENTITY_DIAGNOSTIC_2026-11-04.md`, `research/phase63_form144_master_index_pair_crosswalk_audit.py` and six unit tests.
- Reproducible audit of run 41793719745 artifact 13306814836 (2025Q1, 50 XML sample rows): both XML issuer CIK and XML filer CIK appear in the accession's two master-index CIKs in 50/50 rows; they are distinct in all 50. The current candidate CIK set contains exactly one CIK in 9/50 pairs; all 9 are the XML issuer, none is the filer. Form 144: 6/6 unique candidates are issuer; Form 144/A: 3/3.
- This sample is not random and the candidate CIK set is current, not PIT. Do not treat 9/9 as universal precision or coverage. Cases with two candidate CIKs, one master-index CIK, or corporate reporting persons remain ambiguous until XML confirms issuerCik.
- Potential redesign: use global master.idx CIK pairs for first-stage candidate discovery; fetch primary XML to confirm issuerCik for candidate accessions; fetch filing-detail pages only for confirmed target and stratified non-target validation rows to obtain Accepted timestamps. Validate across independent quarters and unusual filer/issuer structures before integrating.

## 2026-11-04 — Phase 50 latest Actions status (supersedes prior run references)
- Run 41793719745 (run 6, commit 65a5930) completed with failure; artifact 13306814836 contains the 50-row XML sample. The HTML role parser still returned zero Subject/Reporting CIKs despite successful detail-page retrieval.
- Run 41793724389 (run 7, commit 5001cb1) remains `in_progress`, job 126477286538. Parser/PIT tests passed; the 2025Q1 global-index pilot step is still running and no artifact is available. Do not launch another Phase 50 execution while this run is active.
- The Phase 63 master-index pair diagnostic is independent of run 7 and does not authorize a production identity rule or economic test.

## Current Phase 63 decision
- Highest-priority raw options-flow candidates: OptionMetrics TradeFlow (identity/delisted continuity benchmark) and ThetaData raw OPRA trade_quote (transparent NBBO aggressor-side reconstruction, conditional on license and historical correction semantics).
- ORATS remains the lower-cost EOD context candidate; Cboe/MIAX Open-Close remain venue-specific open/close complements.
- SEC Form 144 subject attribution should pivot toward the master-index pair + XML confirmation route only after cross-quarter validation.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No source has passed an economic alpha test.


## 2026-11-04 — Phase 50 run 7 artifact reanalysis and Phase 64 master-pair validation
- Supersedes the earlier note that run 41793724389 was still in progress: run 7 completed with failure at 2026-11-04 09:11 UTC. Job 126477286538; artifact 13309238537 (SHA-256 \`7171bb25407517256345298bcf1d630fff1286b7d8073fd04d9f63f8cb1e45e3\`).
- Run 7 fetched/parsed all 9,104 2025Q1 Form 144/144-A accessions with zero index-page errors. Accepted timestamps, index form and filing-date agreement were 100%. Subject/Reporting CIK parsing remained 0%, so target selection yielded zero target accessions and the 50 XML sample consisted entirely of non-target rows; the gate correctly failed. All 10 parser tests passed.
- Independently reanalyzed the downloaded artifact using the master-index pair + XML identity method. All 9,104 accessions had exactly two master-index CIKs. Of these, 1,618 had exactly one current candidate CIK in the pair (1,608 Form 144; 10 Form 144/A), 7,486 had none, and none had two. In the 50 XML sample, issuerCik and filer CIK were both present in the pair and distinct in 50/50. Nine rows had exactly one current candidate CIK in the pair; all 9 were the XML issuer (6/6 Form 144; 3/3 Form 144/A), none was the filer.
- This is an encouraging diagnostic, not a universal precision estimate: n=9 unique-candidate XML rows, the sample was not designed as a target-stratified sample, and current CIK/ticker mappings are not PIT historical issuer mappings.
- Added Phase 64 deterministic cross-quarter validation for 2023Q2, 2024Q1, 2024Q4, 2025Q1, 2025Q4 and 2026Q1. It samples unique-candidate pairs, zero-candidate controls and ambiguous pairs separately by form; fetches primary XML directly under both CIK archive paths; distinguishes issuerCik from filer CIK; and reports Wilson confidence bounds. It is a data gate only, not an economic test.
- Phase 64 requires at least 100 Form 144 and 20 Form 144/A target XML rows, high issuer-role concordance, pair/form concordance and zero XML fetch errors. Current ticker/CIK mappings, 27 unmapped names, historical active-universe membership, amendment lineage and accepted-time publication remain limitations.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No forward returns or alpha tests were run.


## 2026-11-04 — Phase 64 SEC Form 144 master-pair cross-quarter validation PASS
- Successful Actions run 41809802277, job 126505915044, commit c0e27577341c00c3cfed4e6a7003ec9a8e2fad3d; artifact 13312525216 (SHA-256 b40b1e9926c8093dcad8638a72e81ab503bfd4b01f55b46e36d3e78242ef72b1). First attempt run 41809763468 failed only because direct-file execution could not import the research namespace; workflow now invokes the script as a module. Phase 50 regression tests 10/10 and Phase 64 tests 8/8 passed.
- Six quarters (2023Q2, 2024Q1, 2024Q4, 2025Q1, 2025Q4, 2026Q1): 56,167 accessions (55,558 Form 144; 609 Form 144/A); every accession had exactly two distinct master-index CIKs.
- Against 309 current candidate CIKs (308/335 tickers mapped; 27 unresolved), 9,432 original Form 144 accessions and 76 amendments had exactly one candidate CIK in the pair; one additional 2025Q4 Form 144 pair had two candidate CIKs and remains ambiguous. 46,658 accessions had no current candidate CIK.
- Stratified XML validation: 150/150 unique-candidate Form 144 rows and 76/76 unique-candidate Form 144/A rows identified the candidate as XML issuerCik, never filer CIK or unresolved. These rows represented 97 and 51 distinct issuer CIKs respectively. Controls were 150/150 per form; all 527 XML rows had both distinct XML issuer/filer CIKs in the master pair, matched the master-index form, and had zero fetch errors. Deterministic hash sampling and issuer clustering mean Wilson bounds are diagnostic, not a calibrated population guarantee.
- Decision: PASS for the sampled master-index CIK-pair + XML issuerCik identity mechanism. Do not infer that all 9,508 candidate accessions are confirmed or that current CIK/ticker mappings are PIT. Full event-panel XML confirmation, historical F80 membership/CIK mapping, amendments and timestamp gates remain open.
- Regulatory timing review: eCFR 17 CFR 230.144(h)(3) requires Form 144 concurrently with sell-order placement/direct market-maker execution; SEC CFI 120.01 (Apr. 25, 2025) says 10b5-1 plan adoption does not change the trigger and the notice is effective for at most three months. SEC permits Form 144 EDGAR filings until 10 p.m. ET. Treat original Form 144 as a proposed-supply/order-placement event, not proof of execution; keep 144/A amendments separate. Use first full trading-session close after filing date until accepted-time timing is validated.
- Added research/PHASE65_FORM144_EVENT_PANEL_PIT_AND_SUPPLY_HYPOTHESIS_SPEC_2026-11-04.md. No forward returns or alpha tests were run; F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-04 — Form 144 coverage qualification
- Added the SEC's explicit coverage limitation: non-affiliates no longer need to file Form 144; the relevant electronic feed is therefore a selective record of qualifying affiliate proposed sales, not all insider sales and not all affiliate sales. The source is the SEC's Rule 144/145 small-entity compliance guide: https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/revisions-rules-144-145
- This reinforces the Phase 65 design: treat Form 144 as a potential affiliate-supply/order-placement feature, not a general insider sentiment measure.


## 2026-11-04 — Phase 65 Form 144 event-field coverage audit added
- Created branch \`phase65-form144-event-field-coverage-audit\` from Phase 64. Added a 14-quarter sample audit covering 2023Q2–2026Q3, after the 2023-04-13 electronic filing start.
- The audit samples each quarter/form separately (up to 50 unique-candidate, 20 ambiguous and 10 zero-candidate control accessions), fetches primary XML and measures issuer identity, core event fields, numeric/date parseability, 10b5-1/plan fields, multi-tranche blocks and previousAccessionNumber references.
- Initial Phase 65 code incorrectly treated securitiesToBeSold acquisition-lot blocks as proposed-sale tranches; that output is superseded and must not be used. Corrected code extracts securitiesInformation sale tranches, securitiesToBeSold acquisition lots, and securitiesSoldInPast3Months realized prior sales separately. In-window previousAccessionNumber only means the referenced accession is present in the census; it does not imply immediate-predecessor lineage.
- The phase is a schema/data-feasibility sample only. It does not estimate population completeness, establish PIT F80 membership or accepted-time availability, or authorize returns. Current ticker/CIK mappings remain candidate-only; 27 current tickers remain unresolved.
- Unit tests cover EDGAR/ISO dates, numeric parsing, accession normalization, deterministic stratification and multi-tranche extraction. Hosted Actions execution will run after the workflow file is added.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-04 — Phase 65 Form 144 XML schema correction
- SEC schema semantics: securitiesInformation = proposed sale tranches (1–40); securitiesToBeSold = acquisition history (1–40); securitiesSoldInPast3Months = realized prior sales (0–200).
- Corrected script commit 716f3420408678df11c857492109103a0ab5bdb5 and tests commit 2f9d7312b50e26e10c1b95f9be8c31bfd68116d.
- Obsolete run 41814071603 uses the old parser and must not be used for tranche results. Corrected run 41814314002 is queued behind it. Do not dispatch another run while either remains active/queued.
- Official SEC reference: https://www.sec.gov/submit-filings/technical-specifications.
- No forward returns or alpha tests; F80 remains frozen.


## Phase 64–66 — SEC Form 144 candidate-role and event-schema audit (2026-11-04)
- Phase 64 run 41809802277 passed its six-quarter sample: XML issuerCik and filer CIK were distinct and both present in the master-index pair. Its 150/150 Form 144 and 76/76 Form 144/A unique-candidate matches were sample-specific, not a universal rule.
- Phase 65 run 41814314002 parsed 1,177 XML documents across 14 quarters with zero fetch errors. All XML form types and CIK-pair checks reconciled. All core proposed-sale fields were present, numeric fields parsed, and approximate-sale dates parsed in 100% of the sample. Acquisition lots and prior realized sales are extracted separately from proposed-sale tranches.
- Critical role finding: two unique current-candidate CIKs were XML filer-only matches, not issuer matches: JD (accession 0001970673-23-000004; issuer GigaCloud, filer/seller JD.com) and QCOM (0001104659-26-005774; issuer MNTN, filer/seller Qualcomm). One ambiguous AMT/ASTS pair was resolved by XML to ASTS as issuer and AMT as filer.
- Form 144 unique-candidate sample: 698/700 issuer matches (99.714%) and 2 filer-only false positives. Form 144/A: 196/196 issuer matches. These deterministic/stratified sample rates are diagnostics, not population estimates.
- The hosted run failed only because its gate incorrectly required every candidate CIK to be XML issuerCik. Phase 66 changes the gate to require complete XML role resolution, reports issuer matches separately, and excludes filer-only candidates from target issuer events.
- Across 14 quarterly master indexes (2023Q2–2026Q3), 56,167 Form 144/144-A accessions were found. Current CIK-pair discovery produced 21,451 unique-candidate original filings, 196 unique-candidate amendments, and one ambiguous original. These are not yet confirmed issuer events.
- Next: run corrected schema/role gate, then resolve every candidate-pair accession by primary XML issuerCik/filer CIK. Only then build an amendment-aware event panel. Historical F80 membership, 27 unmapped current tickers, historical CIK continuity, accepted timestamps, and economic value remain untested.
- No forward returns or alpha tests. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


## 2026-11-04 — Phase 66 artifact reanalysis and Phase 67 full-census implementation
- Phase 66 run 41821586407 succeeded with artifact 13316983646 (SHA-256 8a72ae64b786828a896a5699c3c92947725142614976ea5163aabfb677d6f04e), but it executed the 1,177-row Phase 65 stratified sample, not the 21,648-row full candidate census. Sample: 841 Form 144 + 336 Form 144/A; 897 candidate-stratum rows; 280 controls; zero XML fetch errors. This is a schema/role sample PASS only.
- Reanalysis of 895 XML-confirmed issuer-candidate rows with sale tranches: Form 144 approximate sale date was same-day in 668, before filing in 12, and after filing in 19. Form 144/A was before filing in 123, same-day in 72, and after in 1. There were 22 notice-date/filing-date mismatches. These are deterministic sample diagnostics; they reinforce that approximate sale date and notice date are not KnowledgeDate. Use filing date and next full session conservatively.
- Two sampled amendments reported zero proposed units and zero proposed value (PayPal accession 0001972362-23-001045; Snowflake accession 0001959173-26-007025). Preserve these as zero/invalid-size records; do not impute positive supply.
- Phase 67 was added to resolve all 21,648 current-CIK candidate accessions across 14 quarters. First run 41827898110 failed before any XML requests because the script treated parse_master_index's metadata_conflict flag as a true form/date conflict. That flag also becomes true when the two expected archive-path CIKs differ. This was a script-gate defect, not missing XML data.
- The Phase 67 script now treats only unresolved form/date metadata as blocking; expected archive-path multiplicity is retained as a diagnostic and does not prevent XML retrieval. The run 41828139052 (commit b7f15bd799682507771f6039ca49a576b1da44f4) is in progress; all four test suites passed before the audit step. Later commits corrected the fetch-attempt denominator and added a regression test; their workflow runs 41828166351 and 41828179718 are pending/queued in the same concurrency group. No further dispatches should be started.
- New mapping issue identified for follow-up: current_cik_candidates reads SEC company_tickers_mf.json but extracts ticker/classTicker/class_ticker, not the official field name symbol. The official mutual-fund map uses fields cik, seriesId, classId, symbol. This likely explains why ETF/fund tickers remain among the 27 unresolved names despite the source being queried. Fix and test the symbol field before treating those 27 as genuinely unavailable. Registrant CIK alone may still be insufficient to assign a particular ETF series/class; retain seriesId/classId and require security-class resolution.
- Phase 67 remains identity/data assembly only. Historical F80 membership, predecessor/delisted issuers, accepted timestamps, amendment lineage and economics remain open. No forward returns or alpha tests. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-04 — Phase 68 SEC fund ticker mapping repair
- Found a parser defect: SEC company_tickers_mf.json uses the field symbol, while Phase 50 only looked for ticker/classTicker/class_ticker. The mutual-fund source was fetched without its ticker rows being recognized.
- Added ticker_from_sec_row() and a regression test for the official symbol field. Hosted Phase 68 run 41828426133 passed; artifact 13321546076 (SHA-256 ec09dc05f3b97d2a8b2ea3a8240e1582ef3ee50d28af91b3cb0593841c7d0c0e).
- Corrected current mapping: 335/335 tickers mapped, zero unresolved, 319 candidate registrant CIKs, zero source errors. All 27 tickers unresolved in Phase 66 were mapped through company_tickers_mf.json. The source contributed 28 ticker rows including QQQ.
- Six registrant CIKs are shared across multiple tickers, including ARK ETF Trust (five ARK funds), an iShares registrant (IEFA/IWM/SOXX), two VanEck/other registrants with paired funds, the SPDR sector ETF trust (ten sector funds), and Zillow's two share classes. Preserve seriesId/classId; a registrant CIK is not a unique fund-security identifier.
- Phase 68 closes the current ticker-to-registrant CIK gap only. Historical PIT ticker/CIK mapping, predecessor/delisted continuity, fund series/class-to-Form-144 security-class attribution and historical F80 membership remain NOT TESTED.
- Phase 67 full candidate XML resolution: first attempt 41827898110 failed before any XML fetch because expected multi-path archive metadata was misread as a form/date conflict. Corrected run 41828139052 is in progress; later run 41828179718 is pending in the same concurrency group. Do not dispatch another full-resolution run until those statuses are reconciled. The Phase 67 output must still be checked for any remaining script/data issues.
- No forward returns or alpha tests. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

- Scope note: Phase 67 run 41828139052 was triggered before the Phase 68 mapping fix and therefore uses the old 309-CIK candidate set. Once it completes, do not rerun the entire 21,648-row census solely for this mapping change. Scan the 14 quarter indexes incrementally for the ten newly added registrant CIKs, revisit any accessions whose pair also contains an old candidate CIK, and keep fund series/class attribution unresolved until matched.


## 2026-11-04 — Phase 70 historical security-master and universe PIT audit
- Inspected Phase 6/8 source: the research code embeds a fixed current 335-ticker DEFAULT_UNIVERSE and requests 10 years of prices by ticker; no effective-dated historical eligible-universe panel was found in the repository tree.
- This is a material limitation for general cross-sectional alpha claims: even perfect mapping of today's 335 tickers cannot recover names omitted from the current list because they delisted, were acquired or otherwise left the curated universe. Recover the original universe-selection rule or label fixed-335 historical results as conditional on a present-day survivor set.
- Phase 68's 335/335 mapping is current ticker-to-registrant-CIK only. CIK is not a tradable security/share-class ID; retain security/listing IDs and fund series/class IDs.
- Added research/PHASE70_PIT_EQUITY_SECURITY_MASTER_FEASIBILITY_2026-11-04.md. Databento is the leading PIT candidate because public schema documents both ts_record and ts_effective; AlgoSeek is a strong lifecycle alternative with SecId/ASID and ticker effective ranges but record-known timestamp semantics need confirmation. CRSP is the research-grade benchmark if WRDS access exists. Sharadar and Norgate are useful secondary lifecycle/listing-status checks but are not yet PIT-certified for historical vendor knowledge.
- No data purchase or vendor contact occurred. No forward returns or alpha tests were run.
- Phase 67 run 41828139052 remains in progress; run 41828179718 remains pending in the same concurrency group. Do not dispatch another full census. Active job log download returned BlobNotFound; no conclusion about progress/failure is inferred from the missing log object.
- Hard gate before promotion: recover the original 335-universe selection rule and/or reconstruct the broad historical eligible universe including delisted names; a historical security master for current symbols alone is insufficient.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-04 — Phase 67 full current-CIK Form 144 resolution completed; Phase 69 incremental expansion prepared

- **Completed baseline:** run 41828139052 succeeded (job 126568067820; artifact 13327123059; SHA-256 4d5660e6c9edd9fe40a3557919e28890a25971fcff8faf393ca500145e94eedb). Full 14-quarter census 2023Q2–2026Q3: 56,167 index accessions; 21,648 current-CIK candidates; 21,634 issuer-event rows (21,438 Form 144 + 196 Form 144/A); 14 filer-only false positives excluded; zero unresolved rows, XML errors or duplicate candidate accessions; 280/280 controls reconciled. XML role, pair, distinct-CIK and form checks were 100%.
- Phase 67 used the pre-Phase-68 map: 308/335 current tickers and 309 candidate CIKs. It is not a historical F80 or security-master panel.
- Artifact reanalysis found 289 distinct XML issuer CIKs. All 21,634 event rows had proposed-sale tranches and numeric units/value fields, but numeric parseability does not imply valid positive size: two amendments had zero units/value and one original had positive units but zero value. Preserve these as zero/invalid-size observations; do not impute.
- Approximate sale dates across proposed tranches: 568 before filing, 20,781 same day and 514 after filing. They are not KnowledgeDate or proof of execution.
- Amendment references: 196 Form 144/A; 195 previous-accession references appear in the 14-quarter master-index census; one is outside the census. Of the 195, 193 predecessor accessions are in the candidate-role output and two are in the broad index but not candidate rows. The 193 candidate-row predecessor pairs have matching issuer CIK and overlapping security-class labels; 188 point to Form 144 and five point to another Form 144/A. Seller text is exact after conservative normalization in 174, token-order-only in 6, and non-exact/ambiguous in 13. Do not fuzzy-merge seller/trust entities; resolve the three non-candidate predecessors and the out-of-window predecessor explicitly. Recursive amendment chains remain required.
- Phase 68 run 41828426133 / artifact 13321546076 passed current mapping: 335/335 tickers, 319 registrant CIKs, zero mapping-source errors. Ten additional fund registrant CIKs were identified.
- Phase 69 incremental script and six regression tests are committed on phase69-incremental-form144-fund-registrants. The scan validates the Phase 67 artifact, rechecks only accessions whose master-index pair contains one of the ten new CIKs, reclassifies old/new overlaps against all 319 CIKs, and merges without duplicates or retaining superseded filer-only events. Local isolated tests: 6/6 PASS. Hosted run intentionally not dispatched yet.
- Run 41828179718 is still marked in_progress in the Phase 67 concurrency group (job 126605281463); its test suites passed but the XML resolution step remains active and its job-log download currently returns BlobNotFound. The completed run 41828139052 already provides the validated baseline. Do not dispatch Phase 69 until the active duplicate run is reconciled.
- Phase 70 remains the hard blocker for broad alpha promotion: recover the original 335-universe selection rule and/or reconstruct a broad historical eligible universe including delisted securities, with PIT effective and record-known timestamps. Phase 68's current CIK map does not solve this.
- No forward returns or alpha tests were run. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-04 — Phase 71 original 335-name universe provenance trace

- Direct source inspection confirms Phase 0 says the 335-name DEFAULT_UNIVERSE must be copied from the current project; Phase 0, 5, 6 and 8 each hard-code/count-check the same 335 names and request ten years of price history by ticker. No dated inclusion/exclusion ledger or historical eligible-universe construction rule was found in the inspected repository tree.
- Git history for the Phase 0 file begins with a generic upload on 2026-10-14; Phase 6/8 were uploaded 2026-10-15. The inspected commit messages do not document the universe's source, screen date, thresholds or replacement process.
- This confirms Phase 70's limitation. A PIT security master can resolve lifecycle for known securities but cannot restore omitted names that were absent from the curated 335 list. Fixed-335 results remain conditional diagnostics; do not describe them as a general survivorship-bias-free cross-sectional test.
- If the original selection rule cannot be recovered from contemporaneous evidence, a new broad-universe benchmark must be a separate research line with predeclared PIT eligibility, permanent security/listing IDs, delisted names and terminal-return handling. Do not silently substitute it into F80 or tune the rule against historical returns.
- Report: research/PHASE71_ORIGINAL_UNIVERSE_RULE_TRACE_2026-11-04.md.
- No forward returns or alpha tests were run. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-04 — Phase 69 incremental scan implementation regression gate PASS

- Added the Phase 69 incremental Form 144 fund-registrant script and tests. Hosted unit-test run 41847339213 / job 126634182880 completed SUCCESS; all 7 tests passed.
- Strengthened the scan before any SEC index work: it replays the pre-Phase-68 ticker mapper with the old field list (excluding SEC mutual-fund symbol) and requires the exact 309-CIK legacy set, 27 previously unresolved ticker names and exact ten-CIK difference to the expanded 319-CIK map. This avoids accepting a changed CIK set merely because counts happen to match.
- The Phase 69 data scan has not been dispatched. Phase 67 run 41828179718 remains in_progress with its XML resolution step active and its job log unavailable (BlobNotFound). The completed Phase 67 run 41828139052 already provides the validated baseline artifact, but the redundant active run is left untouched because no cancellation action is available through the connected GitHub interface. Do not start the incremental SEC scan while it remains active.
- Phase 69 workflow coordination remains manual: after the active Phase 67 run is reconciled, download the completed Phase 67 artifact by run ID and run the incremental scan. The unit-test workflow does not make SEC requests.


## 2026-11-04 — Phase 69 strengthened legacy-map regression PASS

- Added an exact snapshot check for the 27 ticker names that were unresolved under the pre-Phase-68 parser, in addition to the exact 309-CIK legacy set and ten-CIK expansion checks.
- Hosted Actions run 41847627672 / job 126635192916 completed SUCCESS; all 8 Phase 69 unit tests passed.
- The full incremental SEC scan remains held because Phase 67 run 41828179718 is still in_progress and has no artifact. The completed baseline from 41828139052 is available; the active run uses the same production script with a later test-only commit. No second full census or Phase 69 data scan has been started.


## Phase 71 supplement — Phase 9D provenance trace

- Phase 9's accessible portfolio-persistence file contains the same 335-name list and comments that it is the exact frozen universe used by the preceding phase. Its empty-list error explicitly refers to a preceding “Phase 9D research file”.
- That referenced Phase 9D file was not found in the inspected repository tree or the matching Library search. The Phase 9 file itself has no selection source/date/criteria or historical membership ledger.
- In the 2026-10-14 prior conversation, the user's only stated provenance was that the script needed the frozen 335-ticker universe from the current project. A prior assistant asserted a Phase 9/9D origin but did not establish the actual selection methodology. Treat that prior assertion as unverified.
- This narrows the recovery target: locate the original Phase 9D artifact or contemporaneous screen/export; otherwise the 335 list remains a curated snapshot with unknown selection rule.


- The Phase 9D reference is absent not only from the default/Phase 70 trees but also from all 104 current branch names and the matching Library search results. The Phase 9 file is the only accessible artifact that contains the 335 list and points to Phase 9D.


## 2026-11-04 — Phase 67 latest rerun reconciled; Phase 69 data scan released
- Refreshed Actions runs/jobs/artifacts/branches before starting new work. No workflow is currently active. Phase 67 run 41828179718 completed SUCCESS (job 126605281463) at 2026-11-04T14:46:06Z and uploaded artifact 13334881835 (14.66 MB; SHA-256 digest 939d5564b14ce0f41df23a2c9ab681977cfde141cd0ea2b3c1213b1c5bfaf613). This resolves the stale "in_progress" entries above.
- Downloaded and inspected the actual artifact. Summary: 56,167 broad-index accessions; 21,648 candidate rows; 21,634 issuer-event rows (21,438 Form 144 + 196 Form 144/A); 14 filer-only false positives excluded; zero unresolved, XML errors or duplicate accessions; 280/280 controls; XML pair/form/role concordance 100%. The artifact still uses the pre-Phase-68 309-CIK set and maps 308/335 tickers, leaving the 27 known fund/ETF names unresolved. It is an issuer-role census, not PIT security membership or alpha evidence.
- Recomputed tranche-date diagnostics directly from the full CSV: across 21,863 proposed-sale tranches, 568 approximate sale dates precede filing date, 20,781 equal filing date and 514 follow it. Approximate sale date remains distinct from public KnowledgeDate. Original Form 144 rows include 1 zero aggregate-value record; amendments include 2 zero-unit/zero-value records. Preserve these as invalid/zero-size observations; do not impute.
- Phase 69 unit-test run 41847627672 passed all 8 tests but did not perform SEC requests. Updated the Phase 69 script to pin the latest successful baseline (run 41828179718 / artifact 13334881835), corrected the stale spec and added a dedicated Actions data-scan workflow. The scan is incremental: it requests XML only for accessions whose quarterly master-index CIK pair contains one of the ten new fund registrants, then reclassifies overlaps against all 319 current CIKs.
- Phase 71 remains a material blocker: the original 335-name selection rule / Phase 9D artifact was not found. Fixed-335 results remain conditional diagnostics; do not claim broad survivorship-bias-free evidence. Do not reverse-engineer eligibility thresholds from historical returns.
- No forward returns, alpha tests, purchases or strategy changes. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-04 — Phase 9D source artifact recovered from Library; original selection rule still missing
- Corrected the Phase 71 search record: a Phase 9D reconciliation script was recovered from the Library (`CERE_Phase9D_Reconciliacion_Economica_FIXED.py`, created 2026-10-14 00:19:38 UTC), with earlier/later copies. It had not been found in the GitHub tree, but it does exist as a prior Library file.
- The script contains 335 unique default tickers; the normalized set matches exactly the 335 symbols in repo Phase 0, Phase 6 and Phase 9. It calls this a frozen backup universe and sets MIN_UNIVERSE=335. It can load environment/file overrides and records UniverseSource at runtime.
- The recovered code still does not document the selection date, upstream source, screen thresholds, liquidity/market-cap criteria, replacement rules or historical membership. No Phase 9D runtime audit/artifact establishing the actual UniverseSource was found. Thus the file confirms the snapshot's existence/content, not the rule that generated it; Phase 71 remains a hard blocker for broad survivorship-bias-free claims.
- Updated `research/PHASE71_ORIGINAL_UNIVERSE_RULE_TRACE_2026-11-04.md` with this correction. Do not reverse-engineer selection thresholds from returns; keep a separate PIT broad-universe benchmark if the original rule cannot be recovered.
- Phase 67 latest run 41828179718 is SUCCESS with artifact 13334881835. Phase 69 incremental scan run 41862496090 and its unit-test run 41862477486 were queued after the pinned-baseline workflow commit; do not start another scan while either remains active.
- No forward returns or alpha tests; F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-04 — Phase 72 SEC 13D/13G structured XML parser
- Discovered that the SEC's mandatory schedule-specific XML requirement began 2024-12-18 (voluntary from 2023-12-18). The existing Phase 35 artifact contains 8,294 `primary_doc.xml` filings (40.91% of 20,265), including 88 voluntary pre-mandate filings and 8,206 on/after the mandate date.
- Directly audited the old flattened-regex fields on the 8,206 mandatory-era XML rows: reporting_person only 435/8,206 (5.30%), all 435 with a trailing numeric `2`; reporting_person_type 1,254/8,206 (15.28%), with 943/1,254 (75.20%) invalid values. This makes the current reporting-person/group normalization unusable as parsed, despite high numeric field presence.
- Added schema-aware parser `research/phase72_13dg_structured_xml_parser.py`. It handles distinct 13D vs 13G tags, multiple reporting persons, explicit no-CIK flags, group membership flags, repeated type codes, and exact `previousAccessionNumber` amendment edges. It never substitutes filer/accession-prefix CIK for a missing reporting-person CIK and does not infer KnowledgeDate from eventDate.
- Added five regression tests and a tests-only Actions workflow; no SEC requests are made by this workflow. The full 8,294-document parse is held until the Phase 69 incremental Form 144 scan finishes, to avoid concurrent SEC request load.
- Structured XML feasibility PASS; legacy HTML/group lineage and full historical universe remain open. No forward returns or alpha tests; `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


## 2026-11-04 — Phase 72 parser tests corrected and passed
- The first hosted test run 41863446169 had one flawed assertion: its no-CIK fixture lacked a filer CIK, so it compared two empty strings. The parser correctly left reporting-person CIK empty. Corrected the fixture to include filer CIK 0002081473 and assert that no substitution occurs.
- Rerun 41863595467 / job 126691849721 executed all five structured-XML parser tests successfully. Its decoded log shows `Ran 5 tests ... OK`; REST run metadata remains stale `queued`. No SEC requests were made.
- This validates the parser against representative schema-shaped 13D/13G fixtures only. The full 8,294-document XML corpus parse remains pending until Phase 69 SEC workflow queue/status is reconciled.


## 2026-11-04 — Phase 72 corpus-audit tooling ready; 11 tests pass
- Added the full-corpus 13D/13G structured XML audit script. It reads the immutable Phase 35 artifact, retrieves SEC submissions metadata (including acceptanceDateTime) and parses primary_doc.xml documents with 0.6-second request throttling, checkpoints and resumability.
- Added deterministic stratified sampling across 13D/13G, original/amendment and voluntary/mandatory XML periods. The data workflow is gated by a dedicated sentinel file; code and documentation pushes cannot launch a full SEC crawl.
- Hosted run 41864876578 / job 126696436238 passed all 11 tests (5 parser + 6 corpus-helper tests). The workflow supports an 80-filing pilot first; no Phase 72 SEC corpus requests have yet been made.
- Parser supports flat and nested filerInfo CIK schema layouts while keeping filer CIK separate from each reporting person's CIK. Full-corpus accuracy remains unproven until the actual XML sample is fetched and parsed.


## 2026-11-04 — Phase 72 parser v2: schemaVersion, multiple CUSIPs and filer identity
- SEC's current technical-specification index lists Schedule 13D/13G XML v2.3 (2026-04-15); the version history records multiple-CUSIP support from 2026-03-16. Parser upgraded to `phase72-v2`, recording root `schemaVersion` and supporting both current `issuerCusips/issuerCusipNumber` and legacy single-CUSIP fields for 13D and 13G.
- Corpus audit now compares XML filerInfo CIK to accession-prefix CIK separately from issuer CIK and reporting-person CIK, and reports submission filingDate concordance, acceptanceDateTime, event-date and amendment-number coverage, and schema-version distribution.
- Latest hosted run 41865309350 / job 126697927454 passed all 11 tests (5 parser + 6 corpus helper) with parser v2.
- The 80-filing pilot run 41865034118 / job 126696988419 remains queued/no logs; it predates parser v2 and will be treated only as a preliminary schema smoke test. No full 8,294-document corpus request has been launched.

## 2026-11-04 — Phase 69 incremental fund registrant scan / Phase 72 13D/G XML pilot

### Phase 69 — Form 144 incremental fund registrant scan
- Run 41863703923, artifact 13340957307: data gate PASS.
- Current ticker map: 335/335; 319 current candidate registrant CIKs.
- Ten newly mapped fund registrant CIKs produced zero incremental candidate accessions and zero incremental issuer events across the audited 14-quarter Form 144 candidate panel.
- Expanded panel remains 21,648 candidate accessions / 21,634 issuer-matched events, with 14 filer-only false positives excluded, 289 distinct issuer CIKs, and 280/280 control-pair concordance.
- This is a zero-incremental-coverage result for this sample, not proof that the registrants have no filings or historical series/class activity. Fund series/class-to-security mapping and historical F80 membership remain unresolved.

### Phase 72 — structured 13D/13G XML pilot
- Run 41865034118, artifact 13341118476: 80-filing stratified pilot executed; data gate FAIL.
- SEC submissions metadata matched all 80 accessions with zero submissions-index errors, but the direct primary_doc.xml retrieval/parser path produced 0/80 parses; all 80 failed with ElementTree mismatched-tag errors around repeated generated-document line locations.
- Do not interpret this as missing SEC filings or zero ownership. No reporting-person or lineage metrics are valid from the failed pilot.
- The source Phase 35 artifact is explicitly a filer-side retrieval sample, not a subject-issuer census. Its legacy issuer_cik field must not be treated as subject issuer identity.

### Phase 73 — complete-submission text XML recovery
- New isolated branch: phase73-13dg-submission-text-xml-recovery.
- SEC filing-detail and complete-submission examples confirm that the complete submission text file exposes separate SUBJECT COMPANY and FILED BY identities and contains the source primary_doc.xml XML payload within DOCUMENT/TEXT/XML markers.
- New fail-closed extractor and stratified 80-filing pilot use the complete-submission text file, compare XML issuer CIK to SEC header subject CIK, and compare XML filer CIK to SEC header filer CIK plus accession prefix.
- Unit-test workflow is triggered separately from the SEC data-pilot workflow. The 80-filing Phase 73 data pilot has not yet been triggered; wait for hosted tests and SEC public-data concurrency availability.
- Do not run the 8,294-document corpus until the 80-filing pilot passes all identity, form, filing-date, acceptance-time, reporting-person and lineage gates.
- No forward returns, alpha tests, purchases or production changes. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


### Phase 73 hosted test checkpoint — 2026-11-04 16:31 UTC
- Run 41867865628 passed 16 tests (5 Phase 72 parser, 7 Phase 72 audit-helper, 4 Phase 73 extractor).
- Timestamp normalization for SEC submissions API ISO acceptanceDateTime and explicit accession-header concordance were added afterward. Run 41868094850 is the corrected-revision regression run and remains queued; 41868027603 is an earlier queued revision.
- The separate 80-filing SEC data-pilot trigger has not been pushed. No Phase 73 SEC crawl is active.


## 2026-11-04 — Phase 73 pilot failure classified; Phase 74 subject-discovery audit prepared

### Phase 69 Form 144 incremental result
- Run 41863703923 / artifact 13340957307 passed its data gate.
- The ten newly mapped fund registrant CIKs added zero Form 144 candidate accessions and zero issuer events to the audited 14-quarter panel. This is a scoped negative coverage result, not proof that those registrants have no filings or historical series/class activity.
- Expanded panel remains 21,648 candidate accessions / 21,634 issuer-matched events / 14 filer-only false positives.

### Phase 73 complete-submission pilot — actual result
- Run 41868352940 / artifact 13342854701 failed the pilot data gate.
- Stratified sample: 80; parsed: 54; retrieval failures: 26. The 26 were HTTP 404 archive-path failures, not XML parse errors.
- Among the 54 retrieved rows: XML issuer vs SEC header SUBJECT COMPANY = 100%; XML filer vs SEC header FILED BY/accession prefix = 100%; accession/form/filing-date concordance = 100%; reporting-person count positive = 100%.
- Acceptance-time concordance was 0% because the SEC header timestamp is Eastern wall-clock time while submissions API acceptanceDateTime is UTC. A timezone-aware conversion is required; raw digit-string comparison is invalid.
- The Phase 35 input remains a filer-side retrieval sample with a mixed heuristic CIK field, not a subject-issuer census.

### Corrected Phase 73 rerun — do not duplicate
- Run 41872288761 on branch phase74-13dg-archive-path-and-utc-fix is the only active SEC data pilot.
- It tries subject/archive CIK before accession-prefix CIK and converts SEC header Eastern timestamps to UTC with America/New_York daylight-saving rules.
- It has passed parser tests and source-artifact validation; its 80-filing retrieval step remains in progress and has no final artifact yet. Do not start another SEC crawl while it runs.

### Phase 74 global subject-side discovery
- New isolated branch: phase74-13dg-global-subject-discovery-audit.
- Run 41872918484 passed all 12 offline tests and Python compilation. These tests make no SEC requests.
- The audit parser preserves master-index CIKs and Filename archive-path CIKs separately, groups rows by accession, and does not assume either field is the subject issuer.
- Complete-submission retrieval now requires exactly one archive-path CIK from the master index; missing/non-unique path rows are quarantined. The path is a retrieval locator only; SEC-HEADER SUBJECT COMPANY / FILED BY and primary XML remain identity ground truth.
- The sample stratification separates 13D vs 13G, original vs amendment, form-specific regulatory deadline regimes, and candidate/control/ambiguous identity status. Conflicting index metadata is retained but excluded from the pilot sample.
- A separate Phase 76 branch independently documented the FOXA agent-filed path mismatch and passed its offline tests (run 41872762613). The accession prefix can be a filing agent and must not be guessed as the archive directory.

### Additional subject-side discovery route
- SEC Full-Text Search is an official discovery candidate: SEC documentation states electronic filings are searchable since 2001, queries can use CIK and form/date filters, and XML element content is indexed (element names are not). Official sources: https://www.sec.gov/edgar/search/ ; https://www.sec.gov/edgar/search/efts-faq.html ; https://www.sec.gov/about/webmaster-frequently-asked-questions
- Exact quoted subject-CIK search is a hypothesis, not a proven complete API. Test both zero-padded/unpadded CIKs on known cross-filer controls (Revance 0001479290 / filer JPM 0000019617; Osisko 0001431852 / filer Double Zero 0002083861), dedupe document-level hits by accession, and verify primary ownership documents against SEC header/XML. Do not assume the undocumented ciks parameter is subject-aware.
- Another branch phase74-sec-subject-side-13dg-discovery contains an EFTS/Entity Landing Page test plan; no data crawl has been launched from it.

### Research boundary
- Phase 74 has not downloaded global 13D/13G filing documents or run the 14-quarter index scan yet; only offline code/tests and documentation were added.
- No full 8,294-document filer-side corpus parse until Phase 73 corrected pilot and subject-side discovery pass.
- No forward returns, alpha tests, purchases or production changes. Historical F80 membership and original universe selection rule remain unresolved.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
