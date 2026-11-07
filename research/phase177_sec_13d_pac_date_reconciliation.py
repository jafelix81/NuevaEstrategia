from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


INPUT_PATH = Path(__file__).with_name("phase177_sec_13d_pac_date_reconciliation.json")
PAC_COMPATIBLE = "PAC_DATE_REVISION_COMPATIBLE_UNVERIFIED"


def _parse_day(value: str) -> datetime.date:
    value = str(value)
    fmt = "%Y-%m-%d" if "-" in value else "%Y%m%d"
    return datetime.strptime(value, fmt).date()


def reconcile_record(row: dict[str, Any]) -> dict[str, Any]:
    acceptance_raw = str(row["acceptance_datetime"])
    acceptance = datetime.strptime(acceptance_raw, "%Y%m%d%H%M%S")
    filed_day = _parse_day(row["filed_as_of_date"])
    change_raw = row.get("date_as_of_change")
    change_day = _parse_day(change_raw) if change_raw else None
    acceptance_day = acceptance.date()

    if acceptance_day > filed_day:
        status = PAC_COMPATIBLE if change_day == acceptance_day else "FORWARD_ACCEPTANCE_FILED_DATE_MISMATCH_UNRESOLVED"
    elif acceptance_day < filed_day:
        status = "ACCEPTANCE_DATE_PRECEDES_FILED_AS_OF_DATE"
    else:
        status = "SAME_ACCEPTANCE_AND_FILED_AS_OF_DATE"

    return {
        "accession": row["accession"],
        "status": status,
        "acceptance_datetime_raw": acceptance_raw,
        "acceptance_clock_semantics": "SEC header wall-clock; no timezone conversion applied",
        "filed_as_of_date": str(row["filed_as_of_date"]),
        "date_as_of_change": str(change_raw) if change_raw else None,
        "date_as_of_change_matches_acceptance_day": change_day == acceptance_day if change_day else False,
        "exact_pac_payload_verified": False,
        "first_public_availability_verified": False,
        "do_not_backdate_to_filed_as_of_date": True,
        "same_day_or_intraday_pit_allowed": False,
        "daily_eligibility_rule": "NEXT_FULL_REGULAR_SESSION_AFTER_ACCEPTANCE_DATE"
    }


def build_audit(data: dict[str, Any]) -> dict[str, Any]:
    results = [reconcile_record(row) for row in data["records"]]
    cohort = data["cohort_55"]
    return {
        "phase": 177,
        "status": "PAC_COMPATIBLE_HEADER_RECONCILIATION_COMPLETE_PIT_STILL_CONSERVATIVE",
        "record_count": len(results),
        "pac_compatible_unverified": sum(x["status"] == PAC_COMPATIBLE for x in results),
        "same_day_intraday_quarantined": sum(not x["same_day_or_intraday_pit_allowed"] for x in results),
        "cohort_55": cohort,
        "records": results,
        "alpha_test_performed": False,
        "final_holdout_used": False,
        "production_changed": False,
        "f80_changed": False
    }


def main() -> None:
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    print(json.dumps(build_audit(data), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
