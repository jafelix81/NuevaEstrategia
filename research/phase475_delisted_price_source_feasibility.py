"""Phase 475: validate the documentation-only delisted-price source ranking.

No credentials, vendor requests, samples or prices are used. Unknown provider
capabilities fail closed and no source is admitted by this audit.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SUMMARY_PATH = Path(__file__).with_name(
    "PHASE475_DELISTED_PRICE_SOURCE_FEASIBILITY_SUMMARY_2026-11-18.json"
)
REQUIRED_PROVIDERS = {
    "Massive", "Sharadar SEP", "EOD Historical Data",
    "CRSP US Stock Database", "Norgate", "Tiingo", "Alpha Vantage",
}
REQUIRED_SYMBOLS = {"AVB", "EA", "EQR", "LPRO", "ROKU", "WBD", "WBS"}


def load_summary() -> dict[str, Any]:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def validate(summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    providers = summary.get("providers", [])
    names = {p.get("name") for p in providers}
    if names != REQUIRED_PROVIDERS or len(names) != len(providers):
        errors.append("provider_set_mismatch")

    phase20c = summary.get("phase20c", {})
    if phase20c.get("universe_count") != 335:
        errors.append("fixed_universe_count_mismatch")
    if set(phase20c.get("inactive_missing", [])) != REQUIRED_SYMBOLS:
        errors.append("inactive_symbol_set_mismatch")
    if phase20c.get("terminal_returns_reconstructed") is not False:
        errors.append("terminal_returns_must_remain_unreconstructed")

    massive = next((p for p in providers if p.get("name") == "Massive"), {})
    if massive.get("developer_plan_10y_exact_window_pass") is not False:
        errors.append("massive_developer_window_must_fail_exact_start_gate")
    if massive.get("raw_bars_available") is not True or massive.get("dividend_adjusted_bars") is not False:
        errors.append("massive_adjustment_contract_mismatch")
    if massive.get("sample_verified") is not False:
        errors.append("massive_sample_must_remain_unverified")

    eodhd = next((p for p in providers if p.get("name") == "EOD Historical Data"), {})
    if eodhd.get("delisted_completeness_guaranteed") is not False:
        errors.append("eodhd_delisted_completeness_must_not_be_assumed")
    if eodhd.get("historical_versioning") is not False or eodhd.get("change_timestamps") is not False:
        errors.append("eodhd_versioning_limit_must_be_preserved")

    sharadar = next((p for p in providers if p.get("name") == "Sharadar SEP"), {})
    if sharadar.get("record_known_vintages") != "not established by reviewed public docs":
        errors.append("sharadar_record_known_clock_must_remain_unknown")

    crsp = next((p for p in providers if p.get("name") == "CRSP US Stock Database"), {})
    if not {"DLRET", "DLRETX", "DLPRC", "DLPDT", "DLAMT"}.issubset(set(crsp.get("delisting_fields", []))):
        errors.append("crsp_delisting_field_set_incomplete")

    norgate = next((p for p in providers if p.get("name") == "Norgate"), {})
    if norgate.get("delisting_return_or_terminal_recovery_field") is not False:
        errors.append("norgate_terminal_return_limit_must_be_preserved")

    admission = summary.get("admission", {})
    for key in (
        "provider_fallback_admitted", "raw_price_download_performed",
        "sample_acquired", "vendor_contacted", "purchase_made",
        "terminal_returns_reconstructed", "forward_return_test_run",
        "alpha_test_authorized", "oos_test_run", "bootstrap_run",
        "loo_run", "holdout_used", "universe_changed", "f80_changed",
        "production_changed",
    ):
        if admission.get(key) is not False:
            errors.append(f"admission:{key}_must_be_false")

    if not providers or any(p.get("sample_verified") is True for p in providers):
        errors.append("documentation_audit_cannot_claim_sample_verification")
    return errors


def main() -> int:
    summary = load_summary()
    errors = validate(summary)
    print(f"PHASE475_PROVIDER_COUNT={len(summary.get('providers', []))}")
    print(f"PHASE475_VALIDATION={'PASS' if not errors else 'FAIL'}")
    print(f"PHASE475_FALLBACK_ADMITTED={summary.get('admission', {}).get('provider_fallback_admitted')}")
    print(f"PHASE475_RAW_PRICE_DOWNLOAD={summary.get('admission', {}).get('raw_price_download_performed')}")
    for error in errors:
        print("ERROR=" + error)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
