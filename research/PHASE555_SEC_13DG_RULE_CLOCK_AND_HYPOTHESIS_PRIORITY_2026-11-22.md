# Phase 555 — SEC 13D/G rule-clock re-ranking and event-hypothesis gate

**Audit cutoff:** 2026-11-22 13:36 UTC  
**Main HEAD at preflight:** `8a6d53cf408ebbf94942e81d29d5f293876a8df9`  
**Disposition:** prioritize a rebuilt Schedule 13D event panel ahead of broad 13F/N-PORT ownership-change work; keep the entire existing 13D/G panel quarantined until subject-issuer identity is rebuilt. Documentation and source-priority update only; no signal or return test.

## 1. Repository and operational preflight

- Actions total: 8,052. Latest 100: 98 completed success / 2 completed failure; zero queued, in-progress, waiting or requested.
- Branches: 370 (100 + 100 + 100 + 70). Open PRs: 71. Workflow files: 94.
- No workflow was dispatched, rerun, cancelled, merged or duplicated.
- Latest scheduled-run inventory: 49 schedule-triggered runs.
- Latest Form 144 run: [45012113618](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45012113618), 2026-11-22 10:22 UTC. Both jobs succeeded. The post-capture Phase 516 audit reconciled 275 accessions / 2,072 rows with the capture summary; 2,072/2,072 source hashes matched, with zero hash mismatches and zero parse errors. The poll observed 53 feed rows, no new accession/event, and backfilled 10 accessions / 166 detail rows. Artifact [14750197356](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45012113618/artifacts/14750197356) is present and unexpired. Signal-eligible count remains zero.
- Form 4 latest schedule run: [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134). Both jobs succeeded. It recorded 474 new accession events / 988 accession-observation rows; the ten-accession structured backfill added 24 detail rows. Owner enrichment parsed ten accessions (nine single-owner, one multi-owner) and appended 15 owner rows. The descriptive Form 144/Form 4 crosswalk has 3 rows; 2 multi-owner accessions remain quarantined, transaction-line owner attribution is not verified, and signal-eligible matches remain zero. Artifact [14683520646](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134/artifacts/14683520646).
- FINRA Reg SHO latest schedule run: [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600). Both jobs succeeded, but the run predates Phase 539 and its artifact reports zero eligible first-seen observations. It is not post-fix live validation. Artifact [14688803921](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600/artifacts/14688803921).
- CFTC TFF latest schedule run: [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977), successful; ledger total 3,043 rows and zero signal-eligible historical rows. Artifact [14689726870](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977/artifacts/14689726870).
- Phase 403 remains configured at minute 47 hourly. No later schedule event appears after 10:22 UTC through the 12:47 UTC nominal slot; 13:47 UTC had not yet arrived at this cutoff. This is an observed delivery gap, not proof of administrative disablement. Form 4, FINRA and CFTC are weekday schedules; their latest Friday/Saturday-UTC captures do not imply a missed weekend run.

## 2. New official rule-clock review

The SEC's current Regulation 13D-G interpretations page was last updated **2026-11-17**. It confirms that:

- An initial Schedule 13D is due within **five business days after the trade date** that creates beneficial ownership above 5%; use trade date, not settlement date, for the statutory filing clock.
- A Schedule 13D amendment is due within **two business days after a material change** in the facts previously reported.
- Schedule 13G timing depends on filer category and triggering event. The general material-change amendment is quarterly (45 days after quarter-end); certain institutional filers have faster month-end thresholds. Do not apply one generic 13G lag to all filers.
- Schedule 13G is not a reliable synonym for “no engagement” or “uninformed passive capital.” The SEC's September 2, 2026 interpretations explain that engagement with management does not by itself disqualify a 13G filer; the purpose, subject and context determine whether control is being influenced.

The 2023 final amendments also require structured machine-readable Schedule 13D/G filings, with structured-data compliance beginning December 18, 2024.

**Research implication:** Schedule 13D is the more promising public ownership-disclosure event family for an activist/control-intent hypothesis because its filing and amendment clocks are materially faster. Schedule 13G should remain a separate, slower ownership-state/context family. Neither filing type proves a trade was executed at the reported price or that the filer has predictive skill.

Official sources:
- SEC 2023 final-rule announcement: https://www.sec.gov/newsroom/press-releases/2023-219
- SEC Regulation 13D-G interpretations (last updated 2026-11-17): https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-sections-13d-13g-regulation-13d-g-beneficial-ownership-reporting
- SEC EDGAR access, dissemination and index guidance: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data

## 3. Existing panel remains quarantined

This source-priority change does **not** rehabilitate the old Phase 28D/35 panel:

- The historical artifact has 20,266 accessions; Phase 483 found two future-dated event-date candidates (filing dates 2024-02-09 and 2024-02-12, both carrying event date 2024-12-31). Phase 484 inspected the original documents and confirmed these dates are source-document anomalies; preserve them as filed and quarantine them from event timing.
- Phase 484 found the stored issuer CIK/ticker can be the reporting filer rather than the subject issuer. Two original filings explicitly identify different subject issuers. Therefore **zero rows in the old panel are certified subject-issuer-verified from that artifact alone**.
- Phase 485 added a fail-closed parser for the SEC index-header's separate SUBJECT COMPANY and FILED BY blocks, cross-checking the filer CIK against the accession prefix. It is a parser building block, not a completed 20,266-row rebuild.
- The full rebuild and 44 exact-parent retrievals remain blocked pending the repository Actions secret `SEC_USER_AGENT` with a project identifier and monitored contact email. Do not place the email in chat or commit it to the repository. Do not retry the SEC retrieval before the secret is configured and confirmed by the repository owner.

The SEC's EDGAR guidance states that automated requests must declare a descriptive User-Agent with a monitored contact, and that daily indexes list filing CIK, form type, filing date and document path. The accession prefix identifies the submitting filer (which may be an agent), not necessarily the subject issuer. The parser must preserve these as separate identities.

## 4. Re-entry design — preregister before any returns

After the human access prerequisite is met, rebuild the subject-issuer panel using:

1. `filing_cik` from accession/header FILED BY; `subject_issuer_cik` only from the SUBJECT COMPANY header/index. Never fall back from missing subject CIK to the accession CIK.
2. Reporting-person CIKs/names and joint-filer/reporting-group identity as separate entities. No accession-only transaction-to-owner or filer-to-issuer joins.
3. Subject CUSIP/security class and effective-dated listing/share-class identity, including inactive/delisted names and corporate actions. Unresolved identity remains null/quarantined.
4. Filing acceptance/publication clock as the knowledge boundary. Preserve event/trade date as a separate field; never use a future or ambiguous event date as availability. Use a conservative next-session rule unless actual public dissemination is certified.
5. Original 13D, 13D/A, 13G and 13G/A as separate regimes. Amendments update the state of the same reporting group × subject issuer; they are not automatically independent new events.

Candidate hypotheses, not admitted signals:
- Initial 13D: new beneficial ownership above 5%, reported percentage/shares, stated purpose, control/activist proposals, board/strategic demands and disclosed derivatives.
- 13D/A: material changes in ownership, purpose, group composition, derivatives or disposition; only new information versus the immediately preceding known state.
- 13G: slower holder-breadth/persistence/concentration context, with filer-category-specific reporting delays; do not label every 13G as disengaged or passive.

Any future return test must control for prior returns/momentum, size, liquidity, volatility, sector, corporate actions and contemporaneous issuer news; cluster dependence by subject issuer and reporting group; compare with frozen LTM/F80 under identical exposure and costs; and use chronological OOS, block bootstrap, LOO and multiplicity control. Do not test a reduced or misidentified subset.

## 5. Other source dispositions retained

- Form 13F remains parked: the historical 335-name coverage and effective-dated CUSIP/share-class mapping are insufficient for an identical-universe comparison; 45-day quarterly reporting makes it slow context rather than trade flow.
- N-PORT quarter-over-quarter aggregate share-growth remains killed as a standalone ranking after unstable/mostly negative six-transition diagnostics. The observed amendment-delta pair had no short-position changes.
- Form 144 Rule 10b5-1 remains descriptive only: current ledger quality is strong, but public-availability-certified headers and signal-eligible observations remain zero.
- FINRA Reg SHO still requires a natural post-Phase-539 capture before its corrected parser diagnostics can be accepted.
- Phase 20C remains at 328/335 price histories; no provider mixing, universe reduction or imputation is authorized.

## 6. Decision and frozen controls

**Priority change:** after the SEC_USER_AGENT prerequisite, rebuild Schedule 13D subject-issuer identity first; keep 13G separate as slower context. This is a source-priority decision, not an alpha result.

No signal admitted. No forward-return/event study, backtest, OOS, bootstrap or LOO was run. No universe, parameter, cost, exposure, holding-period, holdout or production change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
