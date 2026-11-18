# Phase 472 — Cboe licensing, Complex Order Flow feasibility, and live-capture audit

**Audit time:** 2026-11-18 05:57 UTC  
**Base main:** `395363a92a7a5147bf2138f22bfaf334b85ec4ef`  
**Disposition:** Cboe Open-Close remains conditional; public sample redistribution rights are unresolved and require manual artifact cleanup or written permission. Cboe Complex Order Flow is a conditional *confounder/control* source, not an institutional-identity or directional-flow source. CFTC first prospective receipt is confirmed; SEC pagination is live-validated but still at its first post-upgrade baseline. No signal or strategy change.

## 1. Operational preflight — inspect before any work

- Main HEAD: `395363a92a7a5147bf2138f22bfaf334b85ec4ef`.
- Actions: 7,769 total runs. Among the latest 100: 79 success, 15 failure, 6 cancelled; 0 active/queued.
- Branches: 303 (four REST pages: 100 + 100 + 100 + 3).
- Open PRs: 56.
- Workflow files: 78.
- No workflow was dispatched, rerun, or duplicated.
- No Phase 472 branch existed at preflight.

### Latest scheduled production captures

| Source | Run | Job | Result | Artifact |
|---|---:|---:|---|---|
| SEC Form 144 / 144-A | [44228413864](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864) | 134547264687 live-capture; 134547201593 offline-regression | Success | [14393319006](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864/artifacts/14393319006) |
| CFTC TFF | [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204) | 134560838218 prospective-capture | Success | [14395926632](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204/artifacts/14395926632) |

The SEC live job migrated no rows (schema already current), paginated Form 144 over two pages / 200 raw Atom entries, found the prior accession watermark, reported no possible feed-window gap, resolved 90 XML filings and 90 acceptance datetimes, and appended 109 feed-observation rows. Form 144/A returned nine unique accessions and no new accession. The poll ran 03:09:51–03:10:13 UTC on Nov 18. Its interval lower bound remains null / `INITIAL_BASELINE_NO_LOWER_BOUND`: this is still the first post-Phase-465 poll. All 90 new filings remain research-ineligible and signal-ineligible; acceptance datetime is not treated as first public receipt. A second clean scheduled poll is required before bounded intervals can be considered.

CFTC appended four first-receipt report events for report date 2026-11-10 at 2026-11-18 03:44:57 UTC. Total historical/backfill rows are 3,039. The four new events cover ES (13874A), NQ (209742), DJIA (124603), and Russell E-mini (239742); only ES/NQ belong to Phase 387's primary preregistration. All four are observations, not signals. No historical backfill features, forward returns, or alpha tests were attached. The workflow's 17 offline tests passed.

FINRA Phase 469 remains scheduled for 22:30 and 23:30 UTC on weekdays. Those Nov 18 slots were still in the future at this audit cutoff; no live FINRA receipt is claimed. CFTC's next configured weekday slot is 22:25 UTC. Do not dispatch either workflow manually merely to accelerate the schedule.

## 2. Cboe Open-Close sample — rights remain unresolved

The public Phase 54 artifact [13291147097](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762583602/artifacts/13291147097) remains available until 2027-02-02. It contains the public Cboe sample bundle and parsed row-level sample material.

Official Cboe website Terms and Conditions (last updated 2022-11-16) state that users may view, print and download one copy for personal non-commercial use, but otherwise may not copy, store in an electronic retrieval system, publish, or distribute Materials without prior written consent (section 2): https://www.cboe.com/terms/ . The Terms also recognize that separate page-specific terms may apply. Cboe's market-data document library directs users to sign the Cboe Global Data Agreement and says use is subject to the applicable Data Policy and Fees: https://www.cboe.com/data/market-data-services/document-library .

The DataShop product page's public "Download sample" link is not, by itself, express permission to republish the sample inside a public GitHub Actions artifact. This is an unresolved rights question, not a legal conclusion that a violation occurred.

- Existing tracking issue: [#132](https://github.com/jafelix81/NuevaEstrategia/issues/132).
- An additional comment with the official Terms and recommended disposition was posted during this audit.
- Requested action: obtain sample-specific written permission or delete artifact 13291147097. The available GitHub connector exposes artifact listing/download but no artifact-delete action; deletion remains a manual GitHub Actions step.
- No new Cboe sample was downloaded, uploaded, or redistributed during this phase.

The Dec 2025 Federal Register filing documents an EOD Open-Close historical trial of up to six months for eligible new subscribers who have not previously subscribed or received a trial, and then-current ad-hoc historical charges of $600/month for 1–4 years and $300/month for 5+ years. These are dated filing disclosures, not a verified Nov 2026 quote; trial eligibility and current pricing must be confirmed before any acquisition. The trial does not imply public redistribution rights. Source: https://www.govinfo.gov/content/pkg/FR-2025-12-16/html/2025-22868.htm .

## 3. New candidate: Cboe Complex Order Flow EOD

Official product page: https://datashop.cboe.com/complex-order-flow  
Official v1.0 specification: https://datashop.cboe.com/documents/Complex_Order_Flow_Specifications_v1.0.pdf

The product advertises five daily zipped CSV files, one per strategy:

- Reversal conversion (RevCon)
- Box spread
- Jelly roll
- Tied outright
- Tied spread

The specification describes U.S.-listed options over OPRA and equity legs over CTA/UTP, with RTH and GTH executions. Files include trade date, underlying, strategy price/rate, option-leg root/expiry/strike/type/size/execution price and selected theoretical price/delta fields; tied strategies also include paired stock execution size, price, exchange, condition and time.

### Research interpretation

This is potentially useful to classify or control for non-directional financing, carry, conversions and delta-neutral hedging that can contaminate naive interpretations of option volume as directional informed buying. It is not direct evidence of institutional identity or directional intent.

The v1.0 specification does **not** document participant capacity, beneficial owner, aggressor side, contemporaneous NBBO, or a stable execution/sequence identifier. The product page/specification do not publish a historical start date or a product-specific first-receipt SLA. The page advertises a subscription and sample link, but no historical backfill range or explicit public redistribution grant was established in this audit.

The generic DataShop FAQ says daily files are typically uploaded the next day between 00:05 and 03:00 U.S. Eastern, but delays can push delivery until after the next market open. That is a generic convention, not a product-specific receipt guarantee. Any future use must record the actual first receipt and enter only after that receipt.

### Feasibility disposition

`CONDITIONAL_CONTROL_ONLY_HISTORY_AND_LICENSE_UNPROVEN`

Keep this source below Open-Close EOD / broad OPRA trade data in priority. Do not use it as a standalone smart-money signal. Reconsider only after written confirmation of historical coverage, file-version/correction policy, product-specific delivery, universe coverage, sample rights, and full license/cost terms. No vendor contact, trial, purchase, or data download was made.

## 4. Updated source decisions

| Source | Decision |
|---|---|
| Cboe Open-Close EOD | Conditional participant/open-close source; sample artifact rights unresolved |
| Cboe Complex Order Flow EOD | Conditional confounder/control source; history and PIT unproven |
| Cboe Option Trades / OPRA | Retain as independent raw-trade/NBBO reconstruction candidate, subject to existing gates |
| Cboe TBT / PITCH | Retain as higher-cost microstructure candidates; no new admission |
| CFTC TFF | First prospective receipt confirmed; sample still far below preregistered requirements |
| SEC Form 144 | Pagination validated; first post-upgrade poll only, no bounded PIT events yet |
| FINRA Daily Short Sale Volume | First scheduled post-merge capture still pending at audit cutoff |
| FINRA Short Interest / ATS | Existing completeness, identity, OAuth and PIT gates remain binding |

## 5. Controls and next gates

1. Resolve issue #132 manually: delete artifact 13291147097 unless Cboe confirms sample-specific public redistribution rights in writing.
2. Wait for a second clean SEC scheduled poll and verify the new lower bound is the prior successful poll start; keep all first-poll baseline events ineligible.
3. Inspect the first scheduled FINRA Phase 469 capture, including poll attempts, first receipt, file hash, schema, revisions and bootstrap/late-first-seen classification. Do not treat a CI run as a market-data capture.
4. Continue CFTC only under its first-receipt ledger and preserve the preregistered ES/NQ scope and cadence controls.
5. Do not begin Cboe/CFTC/FINRA forward-return testing until historical identity, survivorship, price/total-return series, executable entry, costs and coverage gates are met.

No forward-return test, feature selection, alpha test, OOS, bootstrap, LOO or holdout use was performed. No signal was admitted. No vendor contact, trial, purchase, or license acceptance occurred.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, holding period, capital, exposure, costs, holdout, or production settings changed.
