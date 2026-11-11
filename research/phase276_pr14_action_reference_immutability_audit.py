#!/usr/bin/env python3
"""Phase 276: immutable action-reference and permission audit for PR #14."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

AUDIT_DATE = "2026-11-10"
WRITE_WORKFLOW = ".github/workflows/phase234_cftc_bpr_prospective_capture.yml"
EXPECTED_ACTIONS = {
    "actions/checkout": "11d5960a326750d5838078e36cf38b85af677262",
    "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
    "actions/download-artifact": "d3f86a106a0bac45b974a628896c90dbdf5c8093",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
}
WORKFLOW_PATHS = (
    ".github/workflows/phase231_cboe_option_quotes_full_row_reparse.yml",
    ".github/workflows/phase234_cftc_bpr_prospective_capture.yml",
    ".github/workflows/phase240_cftc_pit_state_guard.yml",
    ".github/workflows/phase246_cboe_all_access_option_trade_feasibility.yml",
    ".github/workflows/phase247_nport_unit_field_contract.yml",
    ".github/workflows/phase248_cboe_openclose_feature_contract.yml",
    ".github/workflows/phase249_cboe_openclose_real_sample_reprocessing.yml",
    ".github/workflows/phase250_cboe_openclose_convention_gate.yml",
    ".github/workflows/phase251_cboe_multi_exchange_convention_gate.yml",
    ".github/workflows/phase256_form144_form4_lag_preserving_placebo_audit.yml",
    ".github/workflows/phase257_form144_form4_temporal_stratified_placebo_audit.yml",
    ".github/workflows/phase258_form144_form4_accession_cluster_preserving_placebo.yml",
    ".github/workflows/phase259_mom120_incremental_portfolio_economic_audit.yml",
    ".github/workflows/phase260_form144_form4_xnys_session_placebo.yml",
    ".github/workflows/phase261_global_form144_form4_placebo_multiplicity_audit.yml",
    ".github/workflows/phase262_databento_security_master_pit_identity_gate.yml",
    ".github/workflows/phase263_cftc_tff_semiweekly_scope_gate.yml",
    ".github/workflows/phase265_finra_shortflow_pit_calendar_execution_audit.yml",
    ".github/workflows/phase266_cftc_capture_workflow_security.yml",
    ".github/workflows/phase267_finra_short_interest_pit_pagination_audit.yml",
    ".github/workflows/phase268_sec_form_sho_future_publication_gate.yml",
    ".github/workflows/phase269_nyse_group_short_interest_pit_gate.yml",
    ".github/workflows/phase270_nyse_short_interest_public_sample_scope_audit.yml",
    ".github/workflows/phase271_form4_open_market_purchase_screen.yml",
    ".github/workflows/phase272_form4_candidate_unit_price_basis_audit.yml",
    ".github/workflows/phase274_form4_conservative_date_only_pit_clusters.yml",
    ".github/workflows/phase275_form4_disclosure_event_unit_audit.yml",
    ".github/workflows/phase276_pr14_action_reference_immutability_audit.yml",
    ".github/workflows/phase277_finra_ats_stratified_coverage_audit.yml",
    ".github/workflows/phase278_finra_ats_duplicate_grain_followup.yml",
)

def extract_action_refs(text: str) -> list[str]:
    return re.findall(r"^[ \t]*(?:-[ \t]+)?uses:[ \t]*([^ \t\r\n#]+)", text, flags=re.MULTILINE)

def inspect_workflow(path: str, text: str) -> dict:
    refs = extract_action_refs(text)
    errors = []
    if not refs:
        errors.append("NO_ACTION_REFERENCES")
    explicit_permissions = bool(re.search(r"(?m)^permissions:[ \t]*$", text))
    if not explicit_permissions:
        errors.append("MISSING_EXPLICIT_PERMISSIONS")
    pull_target = bool(re.search(r"(?m)^[ \t]*pull_request_target[ \t]*:", text))
    if pull_target:
        errors.append("PULL_REQUEST_TARGET_PRESENT")
    for ref in refs:
        if "@" not in ref:
            errors.append("UNPINNED_ACTION_REF")
            continue
        action, revision = ref.rsplit("@", 1)
        expected = EXPECTED_ACTIONS.get(action)
        if expected is None:
            errors.append("UNREVIEWED_ACTION_SOURCE")
        elif not re.fullmatch(r"[0-9a-f]{40}", revision):
            errors.append("UNPINNED_ACTION_REF")
        elif revision != expected:
            errors.append("ACTION_SHA_NOT_IN_VERIFIED_PIN_SET")
    write = bool(re.search(r"(?m)^[ \t]+contents:[ \t]*write[ \t]*$", text))
    if write and path != WRITE_WORKFLOW:
        errors.append("UNEXPECTED_WRITE_CAPABLE_WORKFLOW")
    if path == WRITE_WORKFLOW:
        required = (
            "if: github.ref == 'refs/heads/main'",
            "persist-credentials: false",
            "GH_TOKEN: $" + "{{ github.token }}",
            'git -c http.extraheader="AUTHORIZATION: basic $AUTH_HEADER" push origin',
            "git diff --cached --name-status | grep -Ev '^A[[:space:]]'",
        )
        if not write:
            errors.append("CFTC_WRITE_PERMISSION_MISSING")
        if any(token not in text for token in required):
            errors.append("CFTC_WRITE_GUARD_MISSING")
    return {
        "path": path, "action_ref_count": len(refs), "action_refs": refs,
        "contents_write": write, "explicit_permissions": explicit_permissions,
        "pull_request_target": pull_target, "errors": sorted(set(errors)),
    }

def build_audit(root: Path) -> dict:
    rows, missing = [], []
    for rel in WORKFLOW_PATHS:
        path = root / rel
        if not path.is_file():
            missing.append(rel)
        else:
            rows.append(inspect_workflow(rel, path.read_text(encoding="utf-8")))
    errors = [f"{row['path']}:{err}" for row in rows for err in row["errors"]]
    errors.extend(f"MISSING_FILE:{path}" for path in missing)
    write_workflows = [row["path"] for row in rows if row["contents_write"]]
    mutable = sum(
        1 for row in rows for ref in row["action_refs"]
        if "@" not in ref or ref.rsplit("@", 1)[0] not in EXPECTED_ACTIONS
        or ref.rsplit("@", 1)[1] != EXPECTED_ACTIONS.get(ref.rsplit("@", 1)[0])
    )
    guarded = (
        write_workflows == [WRITE_WORKFLOW]
        and not any("CFTC_WRITE_GUARD_MISSING" in row["errors"]
                    for row in rows if row["path"] == WRITE_WORKFLOW)
    )
    return {
        "phase": 276, "audit_date": AUDIT_DATE,
        "scope": "All workflow files introduced by PR #14",
        "workflow_count_expected": len(WORKFLOW_PATHS),
        "workflow_count_audited": len(rows),
        "action_refs_total": sum(row["action_ref_count"] for row in rows),
        "mutable_or_unverified_action_refs": mutable,
        "workflows_missing_explicit_permissions": [r["path"] for r in rows if not r["explicit_permissions"]],
        "pull_request_target_workflows": [r["path"] for r in rows if r["pull_request_target"]],
        "write_capable_workflows": write_workflows,
        "cftc_write_workflow_main_guarded": guarded,
        "errors": errors, "workflows": rows,
        "controls": {
            "f80_frozen": True, "production_changed": False, "universe_changed": False,
            "capital_changed": False, "holdout_used": False, "pr_merged": False,
            "live_cftc_capture_executed": False,
        },
        "status": (
            "PASS_ALL_PR14_WORKFLOW_ACTIONS_IMMUTABLY_PINNED_AND_WRITE_PATH_GUARDED"
            if not errors and len(rows) == len(WORKFLOW_PATHS) and guarded
            else "FAIL_REVIEW_REQUIRED"
        ),
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="phase276_output/phase276_pr14_action_reference_audit.json")
    args = parser.parse_args()
    result = build_audit(Path(args.root))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PHASE276_STATUS=" + result["status"])
    print("WORKFLOWS=" + str(result["workflow_count_audited"]))
    print("ACTION_REFS=" + str(result["action_refs_total"]))
    print("MUTABLE_OR_UNVERIFIED_REFS=" + str(result["mutable_or_unverified_action_refs"]))
    if result["errors"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
