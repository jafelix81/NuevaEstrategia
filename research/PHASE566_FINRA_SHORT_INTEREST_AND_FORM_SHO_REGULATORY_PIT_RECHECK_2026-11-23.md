# Phase 566 — FINRA short-interest and SEC Form SHO regulatory/PIT recheck

**Audit cutoff:** 2026-11-23 02:49 UTC  
**Main HEAD before this report:** `4931420a27de1646fcc45f1d6e2de7482c2f15d1`  
**Disposition:** FINRA consolidated short interest remains a conditional public candidate, but the existing historical panel is incomplete and the async live-validation gate remains blocked by credentials/terms. SEC Form SHO is a future source only; current compliance is exempt until January 2, 2028. No new signal or alpha test.

## 1. Current FINRA short-interest release clock

FINRA's live 2026 calendar currently specifies:

| Settlement date | Member filing deadline | Public publication |
|---|---|---|
| 2026-11-13 (Friday) | 2026-11-17, 6:00 p.m. ET | **2026-11-24 (Tuesday)** |
| 2026-11-30 (Monday) | 2026-12-02, 6:00 p.m. ET | 2026-12-09 (Wednesday) |
| 2026-12-15 (Tuesday) | 2026-12-17, 6:00 p.m. ET | 2026-12-24 (Thursday) |

Source: [FINRA Short Interest Reporting calendar](https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest).

FINRA's API documentation, as recorded in Phase 445/448, states that the consolidated dataset is available by 4:40 p.m. ET on the publication date. That is after the regular-session close. Historical features must therefore be keyed to the publication/availability clock, not the settlement date; the earliest regular-session execution is the next trading session. Preserve actual prospective first receipt as an additional constraint and do not backdate it.

The source is a twice-monthly snapshot of reportable open short positions on FINRA member books, not daily short-sale flow, securities-lending utilization, total economic short exposure, or participant identity.

## 2. Regulatory status: two changes that must not be conflated

### 2.1 FINRA weekly short-interest proposal was withdrawn

SEC rulemaking page for SR-FINRA-2026-012 explicitly marks the proposal to amend Rule 4560 and adopt Rule 4321 as **withdrawn on 2026-08-05**: [SEC rulemaking status](https://www.sec.gov/rules-regulations/self-regulatory-organization-rulemaking/sr-finra-2026-012).

The proposed weekly reporting cadence and proposed deleted-symbol final report are not effective. Continue to use the operative twice-monthly FINRA calendar; do not simulate a weekly series or assume the proposed deleted-symbol coverage exists.

### 2.2 SEC Rule 13f-2 / Form SHO is exempt until 2028

SEC Release 34-104303, dated 2025-12-03, grants temporary relief from compliance with Rule 13f-2 and Form SHO reporting effective 2026-01-02 through **2028-01-02**. The order says Form SHO reports for the January 2028 reporting period would be due within 14 calendar days after January 2028 ends. See [official SEC order, lines 38–53](https://www.sec.gov/files/rules/exorders/2025/34-104303.pdf).

Rule 13f-2 was designed to require certain institutional investment managers above specified thresholds to file monthly short-position/short-activity reports; the SEC's public output is aggregated by security. It is not a named-manager public short book. As of this audit, Form SHO is not an available current historical source for this project. Keep it on a future regulatory watchlist, not in the current source matrix as usable data.

The same SEC order delays Rule 10c-1a securities-lending reporting until 2028-09-28 and public dissemination until 2029-03-29. That is another future source, not a present borrow/loan panel.

## 3. Daily FINRA Reg SHO volume is a separate and narrower measure

FINRA's investor explanation distinguishes short interest (open positions) from daily short-sale volume (executed short-sale transactions). FINRA describes the daily Short Sale Volume data as off-exchange activity reported to FINRA facilities; it is not exchange-wide short-sale volume and does not identify beneficial owners or net positioning: [FINRA — Short Interest: What It Is, What It Is Not](https://syndication.finra.org/content/short-interest-what-it-what-it-not).

Consequences:
- Do not label the FINRA daily file as total-market short flow.
- Do not interpret a high daily short-volume ratio as an increase in outstanding short interest.
- Do not infer institutional identity, bearish conviction, or manipulation from the ratio.
- Keep flow and position as separate features and test their interaction only after both panels pass their independent PIT/coverage gates.

## 4. Reconciliation with existing repository work

- **Phase 31 historical short-interest panel remains killed as retrieved.** Phase 446 found that all 102 successful synchronous requests returned exactly the 5,000-row cap; four settlement requests failed; the filtered artifact contained 9,420 rows and 98 observed A–D symbols. Those counts are not complete universe coverage and cannot support zero inference.
- **Phase 445 zero-vs-missing correction remains controlling.** An absent row can be treated as a structural zero only after a complete settlement snapshot and effective-dated proof that the security was active and in scope. Otherwise it is unknown/missing.
- **Phase 447 async client remains a retrieval contract, not a validated data feed.** Synthetic tests passed, but the recorded live attempt stopped at the credential guard and made no FINRA request. The one-settlement live sample remains the next gate.
- **Phase 448 terms/credential audit remains controlling.** Five-year current API history is not a preserved as-known vintage. Individual/Public credentials are limited to personal non-commercial use; do not assume they authorize firm, client or commercial strategy research. The appropriate FINRA credential and terms must be confirmed by an authorized maintainer.
- **PR #159 / Phase 505** remains open and Draft; its documentation-only disposition is conditional source / no alpha. No historical batch or live query is authorized until the bounded async sample passes.
- **FINRA Reg SHO Phase 469** has a prospective first-seen file-level capture design. The last known natural run [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600) predates the Phase 539 diagnostic merge; its eight files were rejected for duplicate symbols. The Phase 539 parser intentionally remains fail-closed; no aggregation or deduplication rule is authorized until a natural post-merge capture establishes the actual row grain.

## 5. Current operational preflight

- Main HEAD: `4931420a27de1646fcc45f1d6e2de7482c2f15d1`.
- Actions API: 8,072 total runs; latest 100 = 96 success / 4 failure; no active or queued run in the returned page.
- Latest run: [45096929863](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45096929863), a PR CI run. Offline regression succeeded; live-capture was skipped as designed. Its artifact [14783278471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45096929863/artifacts/14783278471) is the offline Phase 560 descriptive refresh, not the Phase 565 post-capture artifact.
- Latest natural Form 144 run remains [45085664016](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016), created 2026-11-22 23:53:30 UTC; both jobs succeeded. It predates the Phase 565 merge. The first natural post-merge run must still validate the new post-capture Phase 549 artifact.
- At 02:49 UTC, Form 144 cron remains `47 * * * *`. The 00:47 and 01:47 UTC slots were absent; the 02:47 slot was only two minutes old and is not classified as missed. Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) records the delivery gap. No manual dispatch, rerun, cancellation, cron change or duplicate collector was used.
- SEC FTD PR #204 remains Draft; `SEC_USER_AGENT` is still a human prerequisite for its bounded two-file test. No SEC request was made.

## 6. Next gates and research decision

1. On/after 2026-11-24 publication, run exactly one FINRA consolidated-short-interest settlement query only after an authorized maintainer has configured credentials appropriate to the project's use. Require async status metadata, exact `Record-Total` reconciliation, complete snapshot, preserved revision flags, and a private hash manifest. Do not start the 106-date historical batch.
2. Continue prospective first-receipt capture; preserve each revision as a new vintage. Current/restated history cannot reconstruct the historical information set.
3. Obtain an effective-dated security master and active-universe map before zero inference or frozen-335 coverage claims.
4. For daily Reg SHO, wait for the next natural weekday capture after Phase 539; retain fail-closed behavior until row-grain semantics are established.
5. Monitor SEC Form SHO and Rule 10c-1a regulatory implementation; do not create synthetic historical data before the applicable compliance/dissemination dates.

**Research disposition:** new signals admitted 0; no event/return/alpha/OOS/bootstrap/LOO test; no universe, exposure, costs, holding-period, holdout or production change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
