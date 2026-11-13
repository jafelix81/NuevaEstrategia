# Phase 384 — CFTC TFF prospective first-receipt capture bootstrap

**Date:** 2026-11-13  
**Status:** implementation and hosted baseline test pending.  
**Scope:** establish a reproducible, append-only prospective availability clock. No return or alpha test.

## Why this phase follows Phase 383

The CFTC TFF Futures Only archive is broad and internally consistent for the selected index contracts, but its historical static archive Updated date is not formally defined as first publication. Phase 380 found five missing pages, one report-heading mismatch and two stale Updated dates in the 851 post-launch report-date population. Phase 383 isolated Russell E-mini code 239742 and admitted 480/482 pages as a conservative archive proxy, explicitly not certified strict PIT.

Historical data remain backfill / feature warm-up only. This phase does not retroactively certify them.

## Contract panel

- 13874A — CME E-mini S&P 500, post-first-contemporaneous-TFF-report date 2010-07-20.
- 209742 — CME Nasdaq-100 Mini, post-2010-07-20.
- 124603 — CBOT Dow Jones Industrial Average $5, post-2010-07-20.
- 239742 — CME Russell E-mini, only the post-2017-08-15 E-mini contract era. Do not splice the 2006–2008 Russell Mini era or combine ICE code 23977A.

The source is the CFTC TFF Futures Only dataset gpe5-46if. The five CFTC business-purpose categories are aggregate classifications, not trader identities, beneficial owners or verified informed investors.

## Prospective availability policy

1. The branch-push run creates a historical backfill baseline and marks every row signal_eligible=false.
2. Manual dispatch is diagnostic only and never advances the state.
3. Scheduled capture runs Fridays at 22:15 UTC, after the normal 3:30 p.m. ET CFTC release time. If a holiday/backlog delays publication, no new row is invented; the next scheduled run observes it later.
4. A new report-date/code key first observed by a scheduled run after the baseline receives first_seen_utc and may be eligible only from the first regular equity session after that receipt timestamp.
5. A late-arriving older report date is recorded as a late arrival and is never backdated.
6. A changed hash for an existing key is recorded as a revision event, never overwritten as though it had been known earlier.
7. Missing contract-weeks remain missing; no forward-fill and no zero substitution.

The first receipt is the pipeline's conservative knowledge clock, not a claim about the exact CFTC publication second. The scheduled workflow is inactive until this draft branch is merged into the default branch.

## Feature warm-up fields

The baseline stores selected public aggregate position fields and derived normalized quantities:
- category net positions divided by open interest;
- spread positions divided by open interest, kept separate from directional net;
- Leveraged Money four-report change, only across continuous 6–8 day report intervals;
- rolling z-scores using only prior observations, requiring at least 26 prior weekly observations;
- Leveraged Money versus Asset Manager net-position divergence.

Open-interest reconciliation adds spread positions to both long and short sides. A row is rejected if category totals do not reconcile exactly to reported open interest. The baseline is not an alpha dataset because historical first-receipt dates are not certified.

## Prior COT diagnostic — do not duplicate

The legacy Phase 23C walk-forward used 12 pseudo-OOS dates, selected among eight features and directions at each date using training 5-session Spearman, and did not include transaction costs or an identical-exposure F80 comparison. Its reported mean strategy returns were:
- NASDAQ: +0.192% at 5 sessions, -0.460% at 20 sessions;
- S&P 500: -0.049% at 5 sessions, -3.058% at 20 sessions.

Hit rates were 66.7%/50.0% at 5 sessions and 50.0%/16.7% at 20 sessions for NASDAQ/S&P 500 respectively. This is a weak, selection-sensitive diagnostic, not evidence of incremental edge. The new work is a prospective timestamp/data-integrity bootstrap, not a repeat of that feature search.

## Acceptance gates

- API row counts reconcile before/retrieved/after by contract.
- Metadata rowsUpdatedAt is unchanged during each snapshot.
- Natural key (report_date, cftc_contract_market_code) is unique.
- Category position fields are complete and finite; open interest is positive.
- Long and short category totals, including spreads on both sides, reconcile exactly to open interest.
- Historical backfill rows are never marked signal-eligible.
- Manual runs, late arrivals and revisions are never signal-eligible.
- Only scheduled first-seen new report rows can be eligible, from the next regular session after receipt.
- No forward returns, alpha, OOS, bootstrap, LOO or holdout is used.

## Controls

No changes to F80_TOP20_PARTIAL50_BASELINE_C20, production, universe, capital, parameters or exposure. The legacy holdout remains consumed and unavailable. No vendor purchase/contact. No Smart Money signal is admitted by this phase.
