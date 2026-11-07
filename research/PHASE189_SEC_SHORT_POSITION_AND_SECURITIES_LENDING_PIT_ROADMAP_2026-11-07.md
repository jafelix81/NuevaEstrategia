# Phase 189 — SEC institutional short-position and securities-lending transparency: PIT and future-availability audit

**Audit date:** 2026-11-07  
**Disposition:** FUTURE_PROSPECTIVE_CANDIDATES_ONLY — no current public panel, no PIT admission, no alpha test.

## Executive decision

Two regulatory data sources could materially improve the short-side research line, but neither is available as a compliant public historical panel today:

1. **SEC Rule 13f-2 / Form SHO** is scheduled to begin mandatory reporting for the January 2028 period. The first reports are due within 14 calendar days after month-end (February 14, 2028). Manager filings are confidential; the SEC publishes aggregated security-level information, not a named institutional short book.
2. **SEC Rule 10c-1a / FINRA SLATE** is scheduled to begin covered-person reporting on September 28, 2028, with required public dissemination beginning March 29, 2029. It can provide securities-loan terms and anonymized loan-level records, but lender/borrower identities remain confidential and loan size is delayed 20 business days.

These are potentially useful complements to FINRA short-sale volume and settlement short interest. They are not substitutes for either, and they do not establish beneficial-owner identity or prove informed trading. The dates are future compliance/dissemination gates, not evidence that a usable data feed will actually be available on those dates. Capture and validate the first real public deliveries before any feature construction.

## 1. Current regulatory status

The controlling SEC order is Exchange Act Release No. 34-104303, dated December 3, 2025. It grants temporary relief:
- from Rule 13f-2 and Form SHO reporting until January 2, 2028;
- from Rule 10c-1a reporting to the RNSA until September 28, 2028; and
- from the RNSA's public-dissemination requirements until March 29, 2029.

The SEC's September 30, 2026 Federal Register notice independently confirms that covered persons are not yet required to report Rule 10c-1a information until September 28, 2028, and the RNSA is not required to make certain information public until March 29, 2029.

The SEC states that the relief follows the Fifth Circuit's August 25, 2025 remand without vacatur and gives the Commission time to respond, potentially including amendments. Therefore these dates and field definitions must be rechecked before implementation; they are not immutable guarantees.

## 2. Rule 13f-2 / Form SHO

### What is reported

Covered institutional investment managers must file monthly for equity securities meeting the rule's thresholds.

For a reporting-company issuer, a manager is reportable if its monthly average gross short position at the close of regular trading hours is:
- at least USD 10 million; or
- at least 2.5% of shares outstanding.

For a non-reporting-company issuer, the threshold is a gross short position worth at least USD 500,000 at the close of regular trading hours on any settlement date during the month.

The reported gross short position is not netted against offsetting long or derivative positions. Form SHO also reports the manager's net change in gross short position for each settlement date during the month. This daily net activity is not a raw short-sale tape or gross short-sale volume.

### What the public receives

The manager's Form SHO filing and information that would reveal the manager's identity are confidential. The SEC plans to publish aggregated information by reported security across reporting managers, including gross short-position information and aggregated daily net activity. It does not provide a named manager-by-security history.

The SEC's original final rule expected aggregated information within one calendar month after the end of the reporting month, while allowing an initial dissemination delay. The first actual public release date and delivery format still require verification after the compliance restart.

The final rule also provides for amendment-and-restatement filings; prior-month aggregate data can be updated on a rolling 12-month basis. Preserve every public vintage rather than replacing earlier observations with the latest corrected value.

### Timing and limitations

- First reporting period: January 2028.
- First Form SHO reports: due within 14 calendar days after January month-end; calendar date February 14, 2028.
- Public data: aggregated and delayed; do not assume that the filing deadline is the public-release timestamp.
- Thresholds omit smaller positions and managers below the relevant thresholds. Coverage is therefore selective and threshold-censored.
- Public aggregation hides manager identities. In sparse cases, the SEC acknowledges that a single reporter may sometimes be inferable; anonymity should not be treated as mathematically guaranteed.
- The reported daily net change is calculated by managers and is not equivalent to daily short-sale volume.

**Research role:** a future aggregate institutional short-position state/flow complement. It cannot identify which hedge fund is short a security and cannot reconstruct a full historical manager-level short book.

## 3. Rule 10c-1a / FINRA SLATE

### What is reported

Covered persons report specified information about covered securities loans to a registered national securities association; FINRA is currently the relevant RNSA and operates the Securities Lending and Transparency Engine (SLATE).

The rule's public data elements include security/issuer identifiers, the date and time the loan was effected, venue/platform information, lending fee or rate/rebate terms, collateral information, termination information and borrower category. The public record is anonymized: legal names and regulatory identifiers of lenders, borrowers and intermediaries are confidential.

### Public dissemination and important exclusions

- Most public loan-level data elements are due by the morning of the next business day after a loan is effected or modified.
- Loan amount is not public until the twentieth business day after the loan is effected or modified.
- FINRA must also publish daily aggregate loan activity and loan-rate distributions for reportable securities.
- The SEC's final rule explains that the daily aggregate activity indicates magnitude, not direction: loan increases and decreases are not netted into a directional change in outstanding loans.
- The final rule removed the proposed "available to lend" data element. Do not assume that the public feed will contain a complete lendable-share inventory or support a direct utilization calculation.
- Pre-existing loans are not all loaded on day one. A pre-existing loan that is not modified after the reporting date is not subject to the new reporting obligation; it is reported only if a qualifying modification occurs after implementation.
- Public loan data must be retained and made available for at least five years under the rule, subject to the RNSA's implementation.

### Timing and limitations

- Covered-person reporting date: September 28, 2028.
- Required public dissemination date: March 29, 2029.
- Public loan amount: additional 20-business-day delay after effecting/modification.
- Party identities remain confidential; public borrower category is not a beneficial-owner identity.
- A securities loan is not identical to a short sale or a short position. Loans can support short selling, market making, settlement and other uses; some short exposure may not map one-to-one to a newly reported loan.
- The public daily aggregate is not directional, and the delayed loan size is unsuitable as a same-week execution signal without a separate timing study.

**Research role:** future borrow-market cost/activity/liquidity context, not a standalone directional short signal or named-institution tracker.

## 4. Why the two sources are complementary — but not interchangeable

| Source | Economic object | Main timing | Identity | What it does not measure |
|---|---|---|---|---|
| FINRA short-sale volume | Short-sale-marked transactions | Daily file availability after trading | Reporting/venue data, not beneficial owner | Persistent open short positions |
| FINRA short interest | Outstanding short position at settlement snapshots | Settlement/report publication lag | Aggregate by security | Daily gross short-sale activity |
| Form SHO | Threshold-qualified managers' gross short positions and daily net changes | Monthly reporting; delayed public aggregation | Manager identity confidential | Full-market short interest or trade-level flow |
| SLATE / Rule 10c-1a | Securities-loan transactions, terms and rates | Mostly next-business-day public fields; loan size T+20 | Parties confidential; borrower category public | Directional short-sale volume or complete lendable supply |

Do not collapse these into one "smart money" score. Their denominators, coverage, timing and economic meanings differ. A joint hypothesis is only justified after each series independently passes its own PIT and coverage gates.

## 5. Preregistered future hypotheses

Only after actual public deliveries begin and the data are admitted:

1. **Institutional short-position change:** test whether Form SHO gross-position levels and daily net changes add information beyond FINRA short interest, FINRA short-sale volume, momentum and liquidity.
2. **Borrow-cost pressure:** test whether SLATE loan-rate distributions and anonymized loan activity add information beyond existing short-interest/borrow proxies.
3. **Crowding and squeeze risk:** test whether high borrow cost plus rising loan activity and persistent short-position levels predict asymmetric upside tail risk or subsequent reversal. This is a squeeze-risk hypothesis, not automatically a bearish signal.
4. **Cross-source divergence:** test whether Form SHO, SLATE, FINRA short interest and options flow disagree in a way that contains incremental information. Preserve each source's own availability date and avoid denominator substitution.
5. **Instrument split:** evaluate underlying-stock returns and option-contract returns separately. Security-level short/loan data can inform the underlying; option profitability still requires option-specific entry price, IV, spread, theta and execution costs.

Falsify any hypothesis if it merely tracks past returns, is dominated by a few hard-to-borrow securities, fails after costs, lacks sufficient universe coverage, or does not survive chronological OOS, date-block bootstrap and issuer leave-one-out analysis.

## 6. Admission checklist for the first live/public data

Before any test:
1. Reconfirm the SEC's current compliance dates and any amendments to the rules.
2. Record actual first receipt, UTC timestamp, source URL/version, response headers and SHA-256 for every first publication and later revision.
3. Reconcile amendments/restatements and preserve immutable public vintages.
4. Measure issuer/security coverage, identifier completeness, inactive/delisted coverage and the effect of reporting thresholds.
5. For Form SHO, verify how the SEC publishes and revises monthly aggregate files, the first-publication lag and whether small aggregates are suppressed.
6. For SLATE, validate loan-ID continuity, modification/correction/cancellation semantics, public field availability, the T+20 loan-size release, pre-existing-loan treatment and the absence of explicit available-to-lend inventory.
7. Confirm actual FINRA access, fees, retention rights and bulk-download terms; no subscription or vendor contact is authorized by this audit.
8. Freeze a prospective holdout before looking at forward outcomes. Execute no earlier than the first verified public receipt and next executable market price.

No pre-compliance historical backfill is assumed. Treat both sources as prospective-only until an actual archive proves otherwise.

## 7. Decision

**Keep both sources on the future research roadmap; do not run a return test now.**

- Form SHO is the more direct future aggregate institutional short-position source, but it is delayed, threshold-censored and manager-anonymized.
- SLATE is the more granular future securities-lending source, but it measures loans rather than short positions, has non-directional aggregate activity and delayed loan amounts.
- Neither is available as a mandatory public panel during the current 2026 research window.
- Existing Phase 20C/FINRA short-volume stock-selection results remain killed; this phase does not reopen or rescue them.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

No data were downloaded, no account or vendor was contacted, no terms were accepted, no holdout was used, and no production signal or portfolio setting was changed.

## Official sources

- SEC, [Exchange Act Release No. 34-104303 (Dec. 3, 2025)](https://www.sec.gov/files/rules/exorders/2025/34-104303.pdf) — controlling temporary exemptions and future compliance dates.
- Federal Register / GPO, [Agency Information Collection Activities; Extension: Rule 10c-1a (Sep. 30, 2026)](https://www.govinfo.gov/content/pkg/FR-2026-09-30/html/2026-20056.htm) — confirms current 2028/2029 Rule 10c-1a dates.
- SEC, [Short Position and Short Activity Reporting by Institutional Investment Managers, Release 34-98738](https://public-inspection.federalregister.gov/2023-23050.pdf) — Form SHO thresholds, aggregate publication, confidentiality, daily net activity and amendments.
- SEC, [Reporting of Securities Loans, Release 34-98737](https://www.sec.gov/files/rules/final/2023/34-98737.pdf) — Rule 10c-1a data fields, public timing, loan-size delay, confidential identities and pre-existing-loan treatment.
- SEC, [Press Release 2023-220](https://www.sec.gov/newsroom/press-releases/2023-220) — adoption of Rule 10c-1a.
- FINRA, [Rule 6500 Series — Securities Lending and Transparency Engine](https://www.finra.org/rules-guidance/rulebooks/finra-rules/6500-series) — SLATE implementation framework.
