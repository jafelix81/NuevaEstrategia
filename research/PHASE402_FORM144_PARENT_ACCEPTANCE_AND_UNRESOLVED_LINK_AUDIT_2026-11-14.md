# Phase 402 — Form 144 parent recovery and acceptance-time audit

**Status:** targeted live audit ready; research-only. The eight-pair manifest is extracted from Phase 401 artifact 14126667342 after verifying its SHA-256. Two initial Phase 402 live attempts passed offline regressions but stopped before any SEC request because the cross-run artifact API returned HTTP 401 to the workflow token. The workflow now uses the pinned, compact manifest committed in the repository; no cross-run artifact download is required. No forward returns or signals.

## Purpose

Phase 401 completed the 14-quarter SEC Form 144/A census and resolved 1,442 of 1,446 parent links. Four parent links remained unresolved because their parents were outside the 14-quarter Phase 67 window or absent from the indexed lookup set. Phase 401 also found four candidate-boundary transitions where parent and child issuer CIK membership differ.

This phase does not repeat the broad census or the existing Form 144 → Form 4 descriptive linkage work in draft PRs #29/#30. It uses the immutable Phase 401 artifact and audits only those eight pairs.

## Frozen input

- Phase 401 workflow run: [43626453375](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43626453375)
- Phase 401 artifact: \`14126667342\`
- ZIP SHA-256: \`6ce994213e507d6c0637162c520b003bb7e2a239b922f2a13cc24aaadd5d011c\`
- Input rows: four \`parent_noncandidate_to_child_candidate\` / \`parent_candidate_to_child_noncandidate\` transitions and four \`parent_xml_unresolved\` links.

The artifact was downloaded and SHA-256 verified during this run. Its eight target rows are materialized as `research/PHASE402_FROZEN_INPUT_PAIRS_2026-11-14.json`, retaining the source run, artifact ID and digest. This avoids a cross-run artifact API permission dependency while preserving the exact frozen inputs.

## Scope

1. Recover and validate the original and amended XML for the four candidate-boundary pairs.
2. Revisit the four Phase 401 unresolved parent accessions using adjacent quarterly \`master.idx\` files and multiple filing-path CIK candidates.
3. Retrieve SEC filing-detail \`Accepted\` timestamps, falling back to \`ACCEPTANCE-DATETIME\` in the complete submission header.
4. Compare parent/child filing dates and acceptance ordering; preserve each document version separately.

The targeted quarterly-index lookup covers 2023Q1, 2023Q2, 2023Q3, 2023Q4, 2024Q1, 2024Q2 and 2025Q4. It is not a new all-market census.

The two parent accessions still missing after the first pass are additionally searched in daily master indexes for 2023-11-27 through 2023-12-08 and 2024-03-11/12/13. The daily parser retains the original filename, CIK and company-name columns and normalizes YYYYMMDD filing dates. The SEC documents that later post-acceptance removals are not reflected in prior daily/feed/oldload indexes, while quarterly indexes are rebuilt; therefore a daily index can preserve evidence of an accession no longer present in the current quarterly master index. This is a targeted recovery test, not an assumption that either parent was deleted. [SEC: Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data).

## PIT rules

- \`ACCEPTANCE-DATETIME\` is the SEC acceptance time, not a certified first-public-receipt timestamp.
- The SEC states that no timestamp records exactly when filing content first becomes available on sec.gov; typical delay is not guaranteed.
- Acceptance time is used only to order filing versions and diagnose same-day sequencing.
- No same-day/intraday trading use is authorized.
- Keep the conservative first eligible regular session after the filing-date rule until a prospective first-seen ledger establishes public availability.
- Never backdate a Form 144/A identity correction or revised tranche payload.

## Required output

- \`documents.csv\`: parent/child XML identity, filing date, acceptance time, source URL, XML hash and retrieval status.
- \`pair_audit.csv\`: parent/child accession, date/acceptance ordering, candidate-boundary or unresolved-link classification, and recovery status.
- \`quarter_index_search.csv\`: targeted index coverage.
- \`summary.json\`: counts and explicit quality gates.

## Interpretation limits

A Form 144 is a proposed-sale notice, not proof of execution. A Form 144/A is a version update, not a second sale by default. The \`noOfUnitsOutstanding\` field remains excluded as a denominator/feature. Neither acceptance timestamps nor a successful parent recovery establish predictive value.

## Authorization

- No forward returns, alpha, OOS, bootstrap, LOO or holdout tests.
- No new signal admitted.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No universe, capital, exposure, parameter or production change.
- No vendor purchase or contact.
- Historical F80 membership, complete effective-dated security identity and first-public-receipt timing remain separate gates.
