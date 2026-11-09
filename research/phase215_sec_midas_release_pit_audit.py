"""Phase 215: SEC MIDAS public-release chronology and PIT admission gate.

Deterministic metadata-only evaluator. It deliberately does not infer a daily
knowledge timestamp from the observation date or from HTTP Last-Modified.
"""
import argparse
import json
from pathlib import Path


def evaluate(manifest: dict) -> dict:
    release = manifest["release_evidence"]
    scope = manifest["measurement_scope"]
    admission = manifest["admission"]

    quarterly = release["daily_stock_by_stock_release_cadence"] == "quarterly"
    exact_vintages = release["per_quarter_first_publication_timestamps_available"]
    lm_is_release = release["last_modified_is_first_publication_timestamp"]
    row_date_is_knowledge = scope["row_date_is_public_knowledge_date"]

    daily_pit = (
        not quarterly
        or (exact_vintages and lm_is_release and row_date_is_knowledge)
    )
    return {
        "phase": manifest["phase"],
        "status": (
            "PIT_ADMITTED" if daily_pit
            else "QUARTERLY_BATCH_RELEASE_CONFIRMED_EXACT_VINTAGES_MISSING"
        ),
        "daily_stock_by_stock_release_cadence": "quarterly",
        "public_site_launch_date": release["public_market_structure_site_launch_date"],
        "archive_quarters": release["current_archive_inventory"]["quarter_count"],
        "archive_period": [
            release["current_archive_inventory"]["first_quarter"],
            release["current_archive_inventory"]["last_quarter"],
        ],
        "exact_per_quarter_first_publication_timestamps_available": exact_vintages,
        "http_last_modified_is_first_publication": lm_is_release,
        "row_date_is_knowledge_date": row_date_is_knowledge,
        "strict_daily_pit_admitted": daily_pit and admission["strict_daily_pit_admitted"],
        "quarterly_context_candidate_only": admission["quarterly_context_candidate_only"],
        "off_exchange_execution_flow": scope["off_exchange_execution_flow"],
        "participant_identity_available": scope["participant_or_beneficial_owner_identity"],
        "hidden_order_equals_dark_pool_flow": scope["hidden_order_metrics_are_dark_pool_flow"],
        "alpha_test_authorized": admission["alpha_test_authorized"],
        "holdout_used": admission["holdout_used"],
        "f80_frozen": admission["f80_frozen"],
        "decision": (
            "Do not use daily observation dates as signal availability. "
            "Require the actual quarterly first-publication timestamp for each vintage; "
            "until then retain MIDAS only as non-PIT on-exchange context."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("phase215_sec_midas_release_pit_audit_manifest.json"),
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = evaluate(manifest)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
