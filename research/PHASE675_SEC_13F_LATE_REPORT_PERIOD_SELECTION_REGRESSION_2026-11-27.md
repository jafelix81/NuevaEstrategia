# Phase 675 — SEC 13F late-filing and latest report-period selection regression

**Research date:** 2026-11-27 local (UTC execution: 2026-11-28)  
**Branch:** \`phase675-13f-latest-report-period-selector\`  
**Base branch:** \`phase613-sec-13f-legal-dissemination-floor\`  
**Disposition:** offline state-selection control added; GitHub Actions validation pending. No holdings or signals admitted.

## 1. Motivation

Phase 674 identified four new original 13F-HR filings first observed in the 2026-11-27 SEC 13F feed:

- IronOak Wealth LLC (CIK 2037081): report periods 2025-12-31, 2026-03-31 and 2026-06-30, all filed 2026-11-27.
- AMS Capital Ltda (CIK 1717977): report period 2026-09-30, filed 2026-11-27.

IronOak's Q3 2026 original filing (accession \`0002037081-26-000003\`) had already been filed on 2026-11-06. The three later-filed IronOak originals describe older reporting periods. Filing-date sorting therefore does not identify the latest portfolio measurement period.

Phase 48 already reconstructs each manager/report-period amendment chain as of a conservative first eligible session. It returns multiple manager-period snapshots but did not provide a separate manager-level selector for the latest *report period*. Phase 675 adds that missing layer without changing the underlying amendment reconstruction.

## 2. New selector

Added \`select_latest_holdings_period(reconstruction)\` to \`phase48_sec_13f_asof_amendment_state_machine.py\`.

The selector:

1. Selects the maximum \`report_period\` among manager-period snapshots visible in the supplied as-of reconstruction. Filing date and accession order are not selection keys.
2. Keeps older report periods in the historical panel; late originals and late restatements may update those periods without displacing a newer period.
3. Fails closed if the newest report-period snapshot is blocked. It never silently falls back to an older portfolio and labels it as the latest.
4. Treats a newer 13F-NT as a notice-only freshness warning, never as a zero-holdings portfolio.
5. Preserves older blocked periods as historical gaps. A latest snapshot can be present while period-to-period change features remain unavailable.
6. Preserves pending-calendar status and never upgrades the result to a complete as-of state when the supplied session calendar cannot establish availability.

Every output remains \`signal_eligible=false\`. The function is a data-state selector, not an alpha feature.

## 3. Regression cases added

Eight offline cases were added to the existing Phase 48 test module:

- Three late original filings for older periods do not displace IronOak's newer Q3 2026 report period.
- A late restatement updates an older period's historical holdings but does not replace the newer period.
- A blocked newest period does not fall back to an older holdings snapshot.
- A newer 13F-NT notice warns that the latest public holdings are older, without creating a zero portfolio.
- An older blocked period is retained as a historical gap while the newer period remains the latest snapshot.
- A notice without any public holdings remains notice-only.
- A truncated session calendar keeps the result pending.
- Duplicate manager/report-period input fails closed.

Fixtures are synthetic and test ordering/semantics only; they do not imply that holdings XML for the four Phase 674 filings has been downloaded.

## 4. Validation and scope

The PR workflow compiles the state-machine module and runs the complete Phase 48 test suite, including the eight new cases. The workflow result is pending at the time this report was authored; no test pass is claimed until GitHub Actions reports success.

No SEC request or filing download was performed. Phase 614's latest run (46084129349) captured four bounded metadata observations but zero XML or holdings rows. No CUSIP/ticker mapping, value-unit normalization, return test, OOS test, bootstrap, LOO or holdout use was performed.

## 5. Research disposition

- Latest public holdings selection is now explicitly keyed to \`report_period\`, not filing date.
- Historical amendment reconstruction remains separate for every manager/report-period pair.
- A late older filing is historical disclosure, not a new trade or current-quarter portfolio change.
- The selector is not production-promoted until the stacked Phase 48/612/613 chain is reviewed and merged in order.
- \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.
