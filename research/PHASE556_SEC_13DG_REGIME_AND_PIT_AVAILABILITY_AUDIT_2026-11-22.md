# Phase 556 — SEC 13D/G regime and PIT availability audit
**Audit cutoff:** 2026-11-22 14:16 UTC  
**Main HEAD before this documentation phase:** `8ddaeabb18ef44cef0b3d590e7bcceb956e3115a`

## Executive decision

Schedule 13D remains the highest-priority public ownership-disclosure hypothesis, but the historical panel stays quarantined. The new audit establishes a practical accession-discovery route and, more importantly, confirms that filing acceptance time is not a public-availability timestamp. The 13D/G panel must be reconstructed with separate legal, schema, identity, and dissemination regimes before any return study.

No new signal, event study, forward-return test, backtest, OOS, bootstrap, LOO, or holdout use is authorized. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## 1. EDGAR historical discovery is feasible; subject identity is still not solved

The SEC's Accessing EDGAR Data page (last reviewed 2026-11-20) documents:
- Daily and quarterly/full indexes covering public filings from 1994 Q3 onward.
- Index entries include filer company name, form type, filer CIK, filing date, and filing path.
- Accession-specific SGML header files are available under the filing archive; the SEC also documents daily feed and oldloads archives containing filing headers.
- The accession prefix is the CIK of the submitting filer. That filer can be a third-party filing agent and is not necessarily the subject issuer.
- Indexes are updated nightly. Full/quarterly indexes are rebuilt weekly to incorporate later post-acceptance corrections/deletions; subsequent-day corrections are not necessarily reflected in prior daily/feed/oldload indexes.

The data.sec.gov Submissions API and nightly `submissions.zip` provide a practical all-filer filing-discovery layer. The API is updated during the day and the bulk ZIP is recompiled nightly. However, the SEC describes these APIs as submissions history by filer and extracted financial-statement XBRL; they do not replace accession-header parsing for Schedule 13D/G subject-company identity or extraction of the schedule's narrative/ownership fields.

**Disposition:** use submissions.zip and/or quarterly/daily indexes to enumerate and reconcile 13D, 13D/A, 13G and 13G/A accessions; then retrieve the accession header and primary filing only as required. Continue to parse SUBJECT COMPANY and FILED BY separately. Never use accession-prefix CIK as subject CIK. The Phase 485 parser is the identity gate, not a completed historical rebuild.

## 2. Three legal/schema regime breaks must be explicit

The SEC's final rule (Release 33-11253 / 34-98704) is effective 2024-02-05. Compliance dates differ by requirement:

| Regime | Before | New regime |
|---|---|---|
| Initial 13D | 10 calendar days after acquisition | 5 business days after acquisition, effective 2024-02-05 |
| 13D amendments | Promptly after material change | 2 business days after material change, effective 2024-02-05 |
| Initial 13G — QII / exempt | 45 days after calendar year-end | 45 days after calendar quarter-end, compliance from 2024-09-30 |
| Initial 13G — passive investor | 10 days after crossing 5% | 5 business days after crossing 5%, compliance from 2024-09-30 |
| 13G material-change amendments | Annual framework / any change | 45 days after calendar quarter-end with material change, from 2024-09-30 |
| 13G threshold amendments | Prior month-end / prompt rules | QII: 5 business days after month-end; passive: 2 business days after threshold/deviation, from 2024-09-30 |
| 13D/G submission cut-off | 5:30 p.m. ET | 10:00 p.m. ET, effective 2024-02-05 |
| Structured filing format | HTML / ASCII | XML-based structured data mandatory 2024-12-18; voluntary filing began 2023-12-18 |

The 13G timing is filer-category-specific. Do not assign one generic lag to all 13G observations. Retain filer category and rule regime as explicit fields; where filer category is unresolved, filing-delay assumptions must fail closed.

The XML transition also creates a parser regime: pre-2023-12-18 documents are unstructured; 2023-12-18 through 2024-12-17 may be mixed voluntary XML and legacy formats; from 2024-12-18 structured XML is required. A change in extraction completeness around this date must not be mistaken for a change in investor behavior.

## 3. Public availability: acceptance is not the market-knowledge clock

The SEC Webmaster FAQ (last reviewed 2026-11-20) explicitly states that:
- There is no timestamp indicating when filing content first becomes available on sec.gov.
- Filings are often available within 1–3 minutes of the EDGAR system timestamp, but the lag can increase significantly under load and is not guaranteed or predictable.
- `ACCEPTANCE-DATETIME` records when EDGAR accepted the submission; it does not certify the exact time the public document became available.
- The accession prefix identifies the submitting filer, which may be a filing agent.

The EDGAR access guide also states that daily indexes are updated nightly and that corrections/deletions can be incorporated later. Therefore acceptance time, filing date, index appearance, and first public-document availability must remain separate clocks.

### Observed collector timing from the latest verified Form 144 artifact

Run [45012113618](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45012113618), artifact [14750197356](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45012113618/artifacts/14750197356), contains a Phase 516 distribution for 213 records from EDGAR acceptance to the collector's first-seen upper bound:
- median: 3.818 hours;
- p25: 3.205 hours;
- p75: 4.996 hours;
- maximum: 7.201 hours;
- minimum: 0.019 hours.

This is **not** the SEC's dissemination latency. It includes our polling/collection interval and is only an upper bound on when the collector had observed the filing. The run's previous successful poll start was 02:40:46 UTC and its receipt was around 10:22:35 UTC, a 7h41m49s interval. This demonstrates that a nominally hourly collector cannot be assumed to have delivered an hourly observation in this sample.

The same run reports 275 filing headers / 2,072 detail rows, 2,072 source-hash matches, zero mismatches, zero public-availability-certified headers, and zero signal-eligible headers. The field `research_observation_eligible_filing_headers` is a data-quality/research-observation status, not signal eligibility; it must not be confused with the separate zero `signal_eligible_filing_headers` count.

**PIT rule:** prospective first-seen receipt is a conservative upper bound, not exact public-release time. For retrospective filings without a certified first-seen receipt, use the filing date only as a coarse knowledge boundary and a conservative next-full-session rule. Never backdate to acquisition/trade date or use acceptance as exact public availability. Preserve later corrections as new version observations rather than rewriting what was previously known.

## 4. Rebuild and validation sequence

1. Enumerate accessions from SEC submissions bulk history and/or EDGAR quarterly indexes; reconcile counts by form, filer CIK, filing date, and accession.
2. Retrieve accession headers under a declared SEC User-Agent; parse SUBJECT COMPANY and FILED BY separately; validate FILED BY against the accession prefix. Quarantine missing, duplicate, malformed, or conflicting subject blocks.
3. Retrieve/parse the primary schedule using a versioned parser: legacy HTML/ASCII and structured XML. Keep 13D, 13D/A, 13G and 13G/A distinct.
4. Build reporting-person and joint-filer/group identities separately from subject issuer. Model amendments as state transitions for reporting-group × subject-issuer × covered class, not independent events by default.
5. Reconcile subject CIK, CUSIP, class, share class, and listing to an effective-dated security master and the frozen 335-name universe. No current-only ticker mapping, symbol-only joins, or imputation.
6. Audit coverage and false-zero risk by quarter, legal regime, schema regime, filer category, subject issuer, form type, and historical F80 membership. Publish unknown/mismatch rates and unresolved accessions.
7. Separate event/acquisition date, acceptance datetime, filing date, first-seen receipt, public-availability certification, and correction/version timestamps.
8. Only after these gates pass, preregister hypotheses and test incremental information against frozen LTM/F80 with identical exposure/costs, chronological OOS, issuer/group clustering, block bootstrap, LOO, and multiplicity controls.

## 5. Hypotheses and kill criteria

- **13D initial:** potentially informative disclosure of a >5% beneficial ownership position with control/activist intent, purpose, proposals, derivatives, or group formation. Test disclosure impact after public availability, not a fictitious signal on acquisition date.
- **13D/A:** only the incremental change from the last known filing state is a candidate; an amendment is not automatically a new independent event or a new purchase.
- **13G:** separate ownership-state/context family. It is not synonymous with uninformed/passive capital; filer category, purpose, and engagement context matter.
- **Kill/park:** if subject-issuer identity, historical security mapping, filer category, or knowledge time cannot be resolved for adequate coverage, do not run returns. If coverage of the frozen universe is materially incomplete or regime-specific missingness cannot be bounded, keep the source descriptive or kill the feature.

## 6. Human prerequisite and operational snapshot

The historical rebuild remains blocked until repository secret `SEC_USER_AGENT` is configured with a project identifier and monitored contact. The connected GitHub read interface cannot inspect or set secret values. Do not place the secret or contact address in code, PR text, or chat. After configuration, perform only the already-planned bounded sample first; do not launch a full 20,266-accession rebuild until the sample, parser, hashes, and coverage checks pass.

Verified known workflow records during this audit:
- Form 144 Phase 403 [45012113618](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45012113618): both jobs completed successfully; post-capture reconciliation passed; artifact remains unexpired.
- FINRA Reg SHO [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600): both jobs completed, but the live summary has 8 invalid files, 0 valid files, and 0 signal-eligible observations. This run predates Phase 539 and is not post-fix validation.
- Form 4 [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134) and CFTC TFF [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977): known jobs completed successfully; their captures are older and do not establish new signal eligibility.

The connected GitHub toolset available in this run does not expose a repository-wide list-workflow-runs operation. Consequently the prior 8,052-run / 98-success / 2-failure inventory (cutoff 2026-11-22 11:50 UTC) remains the last available aggregate snapshot; this audit independently verified the named runs' jobs, logs, and artifacts but cannot certify whether a newer no-commit scheduled run exists. No dispatch, rerun, cancellation, cron change, or duplicate workflow was made.

## 7. Decision

Prioritize a regime-aware 13D/G accession rebuild after the SEC User-Agent prerequisite. This is a data-feasibility and PIT methodology result, not an alpha result. The 20,266-row legacy panel remains quarantined. Signals admitted: **0**. No return test/OOS/bootstrap/LOO was run. No universe, costs, exposure, holding period, holdout, or production change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Official SEC sources

- [SEC Release 2023-219 — beneficial ownership reporting amendments](https://www.sec.gov/newsroom/press-releases/2023-219)
- [Final rule 33-11253 / 34-98704 — Modernization of Beneficial Ownership Reporting](https://www.sec.gov/files/rules/final/2023/33-11253.pdf)
- [SEC Accessing EDGAR Data — indexes, dissemination, corrections, accession identity](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
- [SEC EDGAR APIs — submissions history and nightly bulk ZIP](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [SEC Webmaster FAQ — availability lag and timestamp semantics](https://www.sec.gov/about/webmaster-frequently-asked-questions)
