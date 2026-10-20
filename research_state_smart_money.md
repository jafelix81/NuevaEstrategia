# Smart Money Research State

## 2026-10-20 — Phase 22 SEC 13F Feasibility

- Phase: `22_SEC_13F_FEASIBILITY`
- Result: `PROMOTE_TO_RESEARCH_WITH_MAPPING_CAUTION`
- SEC Form 13F datasets are available quarterly from 2013-05 through the current period.
- Reproducibility tests succeeded for 2016 Q1, 2018 Q1, 2020 Q1, 2022 Q1 and 2024 Mar-May; all returned HTTP 200 and valid ZIP payloads.
- Dataset schema includes CUSIP and, in newer releases, optional FIGI; ticker is not the stable primary identifier.
- Point-in-time rule: holdings must not be used before EDGAR acceptance/dissemination. Quarter-end holdings date is not the availability date.
- Material lag: managers report quarter-end holdings generally within 45 days. Therefore any predictive result must explicitly distinguish stale disclosure from information arrival and test whether apparent alpha is merely return-chasing.
- Historical identifier mapping is a gating issue. Do not map 13F positions to the frozen ticker universe using current ticker alone.

### Next research step
Build a transaction/holding-change research dataset with point-in-time filing availability, historical security mapping, institutional manager persistence/concentration, new positions/exits/increases/decreases, and consensus changes. Compare each feature against frozen LTM cross-sectionally and then under identical OOS exposure/cost rules. No F80 change without robust independent OOS evidence.

## FINRA
Phase 20C remains diagnostic only. No production change justified.

## SEC Form 4
Phase 21B remains in progress; do not duplicate its workflow while running.
