# Phase 35 — SEC 13D/13G PIT crosswalk continuation

Date: 2026-10-25

## State audit
- Latest main Actions run: 40202378270, completed successfully.
- Its Phase 22C v6 artifact confirms SEC 13F issuer-name mapping remains production-infeasible: 2016Q1 coverage 70.4%, 2020Q1 81.7%, 2024Q1 93.0%, with substantial ambiguity.
- Phase 34 options research remains feasibility-only and access-blocked; no options alpha test has been run.
- Existing Phase 28D/28E SEC 13D/13G work is the strongest currently executable regulatory Smart Money path.

## Hypothesis status
13D/13G is not labeled Smart Money by assumption. The candidate hypothesis is that newly disclosed or materially changed >5% beneficial ownership, especially control-oriented 13D activity and repeated ownership increases, may contain incremental information after controlling for frozen LTM/F80.

## PIT rules
- `filing_date` is the earliest public knowledge date.
- Event/acquisition dates are diagnostic only and never substitute for filing availability.
- A signal may enter only on the next trading session after the filing becomes public.
- Historical CIK mapping is identity discovery only; SEC submissions are used to validate selected CIKs.
- Amendments are separate events and must not be double-counted as independent acquisitions without an explicit economic change.

## Phase 35 execution design
1. Run the existing 28D extractor with SEC-current plus historical CIK mapping across the frozen 335-name universe.
2. Measure issuer coverage, filing density, field coverage, filing lag, unresolved/ambiguous identifiers and event counts by period.
3. Do not run an alpha model unless the event audit passes the minimum coverage gate.
4. If passed, pre-register a small set of hypotheses: initial 13D vs 13G, ownership-change magnitude, multi-filer clustering, and repeated ownership increases.
5. Evaluate incremental information versus frozen LTM/F80 on identical dates/exposure using chronological OOS, bootstrap and LOO. No threshold/horizon optimization on OOS data.

## External rule verification
The SEC states that initial Schedule 13D filings are due within five business days of crossing 5%, while amended 13D filings generally follow within two business days; Schedule 13G deadlines depend on filer type and were accelerated under the 2023 amendments. The SEC also requires structured, machine-readable 13D/13G filings beginning December 18, 2024. These changes reinforce the need to use actual filing availability rather than transaction/event dates.

## Current decision
Phase 35 is **STAGED — NOT ALPHA EVIDENCE**. The executable audit branch is `phase35-13dg-pit-event-crosswalk`. The repository's available GitHub Actions interface does not expose a workflow-dispatch operation in this environment, so no new run is claimed until GitHub actually schedules one. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
