# Phase 410 — CFTC Bank Participation Report feasibility audit (2026-11-15)

## Decision

**Do not admit the Bank Participation Report (BPR) as a standalone stock-selection or alpha source.** Retain it only as a low-frequency macro-positioning candidate for possible future corroboration of CFTC TFF, contingent on a sufficiently long prospective archive and a pre-registered incremental test.

This is a data-feasibility kill for immediate historical/OOS work, not a claim that bank positioning is economically irrelevant.

## Verified source characteristics

- CFTC publishes BPR monthly, normally on the first Friday shortly after 3:30 p.m. ET, using positions as of the first Tuesday. If that Tuesday is a federal holiday, the report uses the following Tuesday and is published the following Friday.
- The CFTC states that it retains only the most recent **25 months** of BPR data on its website. The current index exposes November 2024 through November 2026 (25 monthly report vintages).
- The November 2026 futures report is dated **2026-11-03** and the release schedule records publication on **2026-11-06**.
- The report includes markets where at least five banks hold reportable positions. It aggregates positions into **U.S. Banks** and **Non-U.S. Banks**; individual bank identities are not published. When either category has fewer than four banks, that category's bank count is suppressed and only the total count is shown.
- CFTC describes the bank classification as based on trader responses to Form 40, subject to staff approval. A trader classified as a U.S. or Non-U.S. commercial bank in one commodity carries that designation across its BPR commodities. This is a regulated category proxy, not a beneficial-owner identity or a census of all institutional participants.
- Futures and gross-options reports are separate. Options positions are **gross and not delta-adjusted**, so they cannot be interpreted as directional delta exposure without an external adjustment model.

## Equity-index relevance

The November 2026 futures report explicitly contains:
- CME E-mini S&P 500;
- CME Nasdaq Mini;
- CME Russell E-mini;
- E-mini VIX futures.

This creates a plausible macro-regime/cross-check use case for a U.S. equity strategy. It does not create issuer-level coverage for the 335-name equity universe. The BPR is therefore not a replacement for FINRA, options-flow, or issuer-level insider data.

## Feasibility gates

| Gate | Finding | Decision |
|---|---|---|
| Historical depth | 25 monthly vintages retained | Fail for robust historical/OOS study |
| Frequency | Monthly | Low effective sample size |
| PIT date | First-Tuesday position date; normal first-Friday publication | Usable only after publication, not as-of position date |
| Exact first public receipt | No historical receipt-vintage ledger identified | Fail for exact intraday PIT |
| Universe | Selected futures markets, not individual equities | Macro-only |
| Participant identity | U.S./Non-U.S. bank aggregates; no bank identities | Proxy only |
| Category censoring | Minimum five banks per market; small category counts suppressed | Missingness/selection must be modeled |
| Options exposure | Gross, not delta-adjusted | Not directly comparable to net directional flow |
| Incremental information vs TFF | Not tested; likely overlapping large-trader system | Must be demonstrated before any use |

The 25-month historical limit means at most 25 monthly observations per continuously covered contract before further market/category censoring. That is not enough to support a credible chronological train/validation/test split, bootstrap/LOO inference, and a meaningful independent OOS evaluation. Expanding the archive prospectively would take years and still leave a low-frequency, selected-market panel.

## Hypothesis retained, tightly scoped

A future hypothesis may ask whether the change in aggregate U.S. versus Non-U.S. bank net positioning in E-mini S&P 500, Nasdaq Mini, Russell E-mini, or VIX futures provides **incremental monthly market-regime information** beyond TFF categories and the frozen LTM/F80 baseline.

It must be tested as a macro overlay/covariate, not as stock-level “smart money.” Any test requires:
1. A prospective first-receipt ledger and immutable raw monthly report vintages.
2. Contract continuity and effective-dated futures identifiers.
3. Explicit treatment of threshold-driven market/category missingness and suppressed counts.
4. Position normalization by open interest, with gross-options kept separate unless delta-adjusted independently.
5. A preregistered incremental comparison against TFF and LTM/F80, using identical exposure/costs, chronological OOS, bootstrap/LOO and no-lookahead controls.

Do not create a BPR capture workflow yet. Reconsider only if a future research plan specifically needs a monthly bank-position cross-check and the prospective archive can be maintained without duplicating the existing CFTC TFF process.

## Reproducible official references

- [CFTC BPR explanatory notes](https://www.cftc.gov/MarketReports/BankParticipationReports/ExplanatoryNotes/index.htm) — aggregation, Form 40 classification, report-date/publication clock, 25-month retention.
- [CFTC BPR release schedule](https://www.cftc.gov/MarketReports/BankParticipationReports/ReleaseSchedule/index.htm) — monthly report and release dates.
- [CFTC BPR archive index](https://www.cftc.gov/MarketReports/BankParticipationReports/index.htm) — visible monthly report vintages.
- [November 2026 BPR Futures report](https://www.cftc.gov/MarketReports/BankParticipation/deanov26f) — report date 2026-11-03 and equity-index futures rows.
- [CFTC TFF Futures Only dataset](https://publicreportinghub.cftc.gov/Commitments-of-Traders/TFF-Futures-Only/gpe5-46if) — comparator source; last updated 2026-11-06 at this audit.

## Research controls

- No BPR data were downloaded or persisted.
- No vendor/account/contact/purchase.
- No return, alpha, OOS, bootstrap, LOO or holdout test.
- No signal admitted; no feature added to F80/LTM.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, capital, exposure, holdout and production remain unchanged.

