#!/usr/bin/env python3
"""Phase 549: accession-grain Form 144 Rule 10b5-1 plan/remarks audit."""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

FORM144_DEFAULT = Path("research/data/sec_form144_first_seen/sale_details.csv")
FORM4_DEFAULT = Path("research/data/sec_form4_first_seen/transaction_details.csv")

MENTION_RE = re.compile(r"10b5\s*-?\s*1", re.IGNORECASE)
NEGATIVE_PATTERNS = (
    re.compile(r"\bnot\s+(?:being\s+)?made\s+pursuant\s+to\s+(?:a\s+)?rule\s+10b5-1\b", re.I),
    re.compile(r"\bnot\s+pursuant\s+to\s+(?:a\s+)?rule\s+10b5-1\b", re.I),
    re.compile(r"\bnot\s+(?:being\s+)?made\s+under\s+(?:a\s+)?rule\s+10b5-1\b", re.I),
)
POSITIVE_PATTERNS = (
    re.compile(r"\bsold\s+pursuant\s+to\s+(?:a\s+)?(?:rule\s+)?10b5-1\b", re.I),
    re.compile(r"\bintended\s+to\s+comply\s+with\s+rule\s+10b5-1\b", re.I),
    re.compile(r"\b(?:sales?|transactions?|shares?)\b.{0,160}\b(?:pursuant\s+to|in\s+connection\s+with|under)\b.{0,160}\b10b5-1\b", re.I),
    re.compile(r"\bpursuant\s+to\s+(?:a\s+)?rule\s+10b5-1\s+(?:trading\s+)?plan\b", re.I),
)
TERMINATION_RE = re.compile(r"\bterminated\s+(?:the\s+)?plan\b|\bno\s+further\s+sales\b", re.I)
SELL_TO_COVER_RE = re.compile(r"sell[\s-]*to[\s-]*cover", re.I)
TAX_WITHHOLDING_RE = re.compile(r"tax\s+withholding", re.I)


def parse_date(value: str) -> date:
    value = (value or "").strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"invalid_date:{value}")


def normalize_flag(value: str | None) -> str:
    token = str(value or "").strip().lower()
    if token in {"1", "true", "yes", "y", "checked"}:
        return "checked"
    if token in {"0", "false", "no", "n", "unchecked"}:
        return "unchecked"
    return "unknown"


def classify_remarks_10b5(remarks: str, raw_mention_flag: str | None = None) -> str:
    text = str(remarks or "")
    mentioned = bool(MENTION_RE.search(text)) or str(raw_mention_flag or "").strip().lower() in {"1", "true", "yes", "y"}
    if not mentioned:
        return "NO_MENTION"
    if any(pattern.search(text) for pattern in NEGATIVE_PATTERNS):
        return "NEGATIVE_EXPLICIT"
    if any(pattern.search(text) for pattern in POSITIVE_PATTERNS):
        return "POSITIVE_EXPLICIT"
    return "AMBIGUOUS_MENTION"


def has_plan_termination(remarks: str) -> bool:
    return bool(TERMINATION_RE.search(str(remarks or "")))


def has_sell_to_cover_tax_context(remarks: str) -> bool:
    text = str(remarks or "")
    return bool(SELL_TO_COVER_RE.search(text) and TAX_WITHHOLDING_RE.search(text))


def _read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path}:missing_header")
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(f"{path}:missing_columns:{sorted(missing)}")
        return list(reader)


def _consistent(rows: list[dict[str, str]], field: str, accession: str) -> str:
    values = {str(row.get(field) or "").strip() for row in rows}
    values.discard("")
    if len(values) > 1:
        raise ValueError(f"inconsistent_{field}_within_accession:{accession}")
    return next(iter(values), "")


def _plan_dates(raw: str, accession: str) -> list[str]:
    try:
        values = json.loads(raw or "[]")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid_plan_dates_json:{accession}") from exc
    if not isinstance(values, list):
        raise ValueError(f"plan_dates_not_list:{accession}")
    parsed: list[str] = []
    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"plan_date_not_string:{accession}")
        parse_date(value)
        parsed.append(value)
    return sorted(set(parsed))


def _quantiles(values: list[int]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "min": None, "p25": None, "median": None, "p75": None, "max": None,
                "quantile_method": "lower_index_floor((n-1)*p)"}
    ordered = sorted(values)
    pick = lambda p: ordered[int((len(ordered) - 1) * p)]
    return {
        "n": len(ordered), "min": ordered[0], "p25": pick(0.25),
        "median": pick(0.50), "p75": pick(0.75), "max": ordered[-1],
        "quantile_method": "lower_index_floor((n-1)*p)",
    }


def summarize_form144(rows: list[dict[str, str]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        accession = str(row.get("accession") or "").strip()
        if not accession:
            raise ValueError("form144_row_missing_accession")
        grouped[accession].append(row)

    forms: Counter[str] = Counter()
    plan_by_form: Counter[str] = Counter()
    polarity: Counter[str] = Counter()
    cross_tab: Counter[str] = Counter()
    plan_dates_all: set[str] = set()
    lags: list[int] = []
    plan_accessions = 0
    termination_accessions = 0
    sell_to_cover_tax_accessions = 0
    negative_cases: list[dict[str, Any]] = []
    mechanical_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for accession, detail_rows in grouped.items():
        form = _consistent(detail_rows, "form", accession) or "UNKNOWN"
        issuer_cik = _consistent(detail_rows, "issuer_cik", accession)
        issuer_name = _consistent(detail_rows, "issuer_name", accession)
        seller_name = _consistent(detail_rows, "seller_name", accession)
        notice = _consistent(detail_rows, "notice_date_iso", accession)
        remarks = _consistent(detail_rows, "remarks", accession)
        raw_mention = _consistent(detail_rows, "mentions_10b5_1_in_remarks", accession)
        plan_raw = _consistent(detail_rows, "plan_adoption_dates_json", accession)
        plan_dates = _plan_dates(plan_raw, accession)
        forms[form] += 1
        plan_dates_all.update(plan_dates)
        has_formal_date = bool(plan_dates)
        if has_formal_date:
            plan_accessions += 1
            plan_by_form[form] += 1

        polarity_label = classify_remarks_10b5(remarks, raw_mention)
        polarity[polarity_label] += 1
        cross_tab[("FORMAL_PLAN_DATE" if has_formal_date else "NO_FORMAL_PLAN_DATE") + "|" + polarity_label] += 1

        if has_plan_termination(remarks):
            termination_accessions += 1
        sell_to_cover = has_sell_to_cover_tax_context(remarks)
        if sell_to_cover:
            sell_to_cover_tax_accessions += 1

        if has_formal_date and notice:
            notice_date = parse_date(notice)
            for plan_date_raw in plan_dates:
                lags.append((notice_date - parse_date(plan_date_raw)).days)

        proposed_units = Decimal("0")
        for row in detail_rows:
            if row.get("detail_section") == "securities_information":
                raw_units = str(row.get("proposed_units_numeric") or "").strip()
                if raw_units:
                    try:
                        proposed_units += Decimal(raw_units)
                    except InvalidOperation as exc:
                        raise ValueError(f"invalid_proposed_units:{accession}") from exc

        if polarity_label == "NEGATIVE_EXPLICIT" and sell_to_cover:
            negative_case = {
                "accession": accession, "issuer_cik": issuer_cik, "issuer_name": issuer_name,
                "seller_name": seller_name, "form": form, "notice_date": notice,
                "formal_plan_date_present": has_formal_date,
                "proposed_units": str(proposed_units),
            }
            negative_cases.append(negative_case)
            mechanical_groups[(issuer_cik, notice)].append(negative_case)

    clusters = []
    for (issuer_cik, notice), cases in sorted(mechanical_groups.items()):
        if len(cases) >= 2:
            clusters.append({
                "issuer_cik": issuer_cik, "notice_date": notice,
                "accession_count": len(cases),
                "proposed_units_sum": str(sum((Decimal(item["proposed_units"]) for item in cases), Decimal("0"))),
                "accessions": [item["accession"] for item in cases],
            })

    return {
        "detail_rows": len(rows),
        "accessions": len(grouped),
        "forms_by_accession": dict(sorted(forms.items())),
        "formal_plan_date_accessions": plan_accessions,
        "formal_plan_date_accessions_by_form": dict(sorted(plan_by_form.items())),
        "formal_plan_date_pct_of_bounded_accessions": round(100 * plan_accessions / len(grouped), 2) if grouped else None,
        "distinct_plan_adoption_dates": len(plan_dates_all),
        "plan_date_lag_days": _quantiles(lags),
        "plan_dates_before_notice": sum(value > 0 for value in lags),
        "plan_dates_same_as_notice": sum(value == 0 for value in lags),
        "plan_dates_after_notice": sum(value < 0 for value in lags),
        "remarks_polarity_accessions": {key: polarity.get(key, 0) for key in
            ("POSITIVE_EXPLICIT", "NEGATIVE_EXPLICIT", "AMBIGUOUS_MENTION", "NO_MENTION")},
        "formal_plan_date_remarks_crosstab": dict(sorted(cross_tab.items())),
        "plan_termination_accessions": termination_accessions,
        "sell_to_cover_and_tax_withholding_accessions": sell_to_cover_tax_accessions,
        "negative_sell_to_cover_cases": negative_cases,
        "negative_sell_to_cover_clusters": clusters,
    }


def summarize_form4(rows: list[dict[str, str]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        accession = str(row.get("accession") or "").strip()
        if not accession:
            raise ValueError("form4_row_missing_accession")
        grouped[accession].append(row)

    counts: Counter[str] = Counter()
    conflicts = 0
    for accession, detail_rows in grouped.items():
        flags = {normalize_flag(row.get("aff10b5one_filing_flag")) for row in detail_rows}
        flags.discard("unknown")
        if len(flags) > 1:
            counts["conflict"] += 1
            conflicts += 1
        elif flags:
            counts[next(iter(flags))] += 1
        else:
            counts["unknown"] += 1

    return {
        "detail_rows": len(rows),
        "accessions": len(grouped),
        "aff10b5one_by_accession": {
            "checked": counts.get("checked", 0),
            "unchecked": counts.get("unchecked", 0),
            "unknown": counts.get("unknown", 0),
            "conflict": conflicts,
        },
        "grain": "submission/accession; never count repeated transaction rows as independent filings",
    }


def build_summary(form144_rows: list[dict[str, str]], form4_rows: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "phase": 549,
        "audit_cutoff_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "disposition": "FORMAL_PLAN_DATE_PRIMARY; REMARKS_POLARITY_REQUIRED; NEGATIVE_CONTROL_FOUND; NO_ALPHA",
        "form144": summarize_form144(form144_rows),
        "form4": summarize_form4(form4_rows),
        "controls": {
            "raw_remarks_presence_flag_is_not_polarity": True,
            "formal_plan_date_is_not_signal_availability_time": True,
            "form144_is_proposed_sale_notice_not_execution_confirmation": True,
            "first_seen_interval_upper_bound_used_not_exact_public_receipt": True,
            "signal_admitted": False,
            "alpha_test_run": False,
            "oos_test_run": False,
            "bootstrap_run": False,
            "loo_run": False,
            "f80_frozen": True,
            "production_changed": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--form144", type=Path, default=FORM144_DEFAULT)
    parser.add_argument("--form4", type=Path, default=FORM4_DEFAULT)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    form144_rows = _read_csv(args.form144, {
        "accession", "form", "issuer_cik", "issuer_name", "seller_name", "remarks",
        "mentions_10b5_1_in_remarks", "notice_date_iso", "plan_adoption_dates_json",
        "detail_section", "proposed_units_numeric",
    })
    form4_rows = _read_csv(args.form4, {"accession", "aff10b5one_filing_flag"})
    summary = build_summary(form144_rows, form4_rows)
    rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
