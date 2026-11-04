#!/usr/bin/env python3
"""Offline, rule-aware Schedule 13D/G deadline and event-semantics audit."""
from __future__ import annotations

import argparse
import calendar
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

import holidays

from research.phase73_sec_submission_text_extractor import extract_primary_doc_xml


def parse_date(value):
    value = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def local_name(tag):
    return str(tag).rsplit("}", 1)[-1].split(":")[-1]


def parse_json(value, default):
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value) if str(value or "").strip() else default
    except (TypeError, ValueError):
        return default


def quarter_end(d):
    q_month = ((d.month - 1) // 3 + 1) * 3
    return date(d.year, q_month, calendar.monthrange(d.year, q_month)[1])


def month_end(d):
    return date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


def is_business_day(d, holiday_calendar):
    return d.weekday() < 5 and d not in holiday_calendar


def next_business_day(d, holiday_calendar):
    while not is_business_day(d, holiday_calendar):
        d += timedelta(days=1)
    return d


def add_business_days(start, count, holiday_calendar):
    d = start
    remaining = int(count)
    while remaining > 0:
        d += timedelta(days=1)
        if is_business_day(d, holiday_calendar):
            remaining -= 1
    return d


def add_calendar_days_adjust(start, count, holiday_calendar):
    return next_business_day(start + timedelta(days=int(count)), holiday_calendar)


def rule_set(value):
    values = parse_json(value, [])
    if isinstance(values, str):
        values = [values]
    return {str(v).strip().lower() for v in values}


def deadline_candidates(family, form, event_date, filing_date, rules, max_pct, holiday_calendar):
    """Return candidate dates, not a legal opinion. Trigger details may be missing."""
    if not event_date or not filing_date:
        return {"base_due_date": "", "accelerated_candidate_due_date": "",
                "deadline_basis": "missing_date", "deadline_status": "unresolved",
                "days_after_base_due": None}
    amendment = str(form or "").upper().endswith("/A")
    pct = float(max_pct or 0.0)
    rule_b = any("13d-1(b)" in r for r in rules)
    rule_c = any("13d-1(c)" in r for r in rules)
    rule_d = any("13d-1(d)" in r for r in rules)
    base = None
    accelerated = None
    basis = "unresolved"

    if family == "13D":
        if event_date < date(2024, 2, 5):
            if amendment:
                basis = "legacy_promptly_no_fixed_calendar_deadline"
            else:
                base = add_calendar_days_adjust(event_date, 10, holiday_calendar)
                basis = "legacy_13D_initial_10_calendar_days"
        else:
            base = add_business_days(event_date, 2 if amendment else 5, holiday_calendar)
            basis = "revised_13D_amendment_2_business_days" if amendment else "revised_13D_initial_5_business_days"
    elif family == "13G":
        if event_date < date(2024, 9, 30):
            # Legacy regime is retained as a coarse diagnostic; the Phase 91 XML sample is post-revision.
            if rule_c and not amendment:
                base = add_calendar_days_adjust(event_date, 10, holiday_calendar)
                basis = "legacy_passive_13G_initial_10_calendar_days"
            elif rule_b or rule_d or amendment:
                year_end = date(event_date.year, 12, 31)
                base = add_calendar_days_adjust(year_end, 45, holiday_calendar)
                basis = "legacy_13G_year_end_45_days_coarse"
        else:
            if amendment:
                base = add_calendar_days_adjust(quarter_end(event_date), 45, holiday_calendar)
                basis = "revised_13G_amendment_quarter_end_45_days_base"
                if pct > 10 and rule_b:
                    accelerated = add_business_days(month_end(event_date), 5, holiday_calendar)
                elif pct > 10 and rule_c:
                    accelerated = add_business_days(event_date, 2, holiday_calendar)
            elif rule_c:
                base = add_business_days(event_date, 5, holiday_calendar)
                basis = "revised_passive_13G_initial_5_business_days"
            elif rule_b or rule_d:
                base = add_calendar_days_adjust(quarter_end(event_date), 45, holiday_calendar)
                basis = "revised_QII_or_exempt_13G_initial_quarter_end_45_days"
                if pct > 10 and rule_b:
                    accelerated = add_business_days(month_end(event_date), 5, holiday_calendar)

    if base is None:
        return {"base_due_date": "", "accelerated_candidate_due_date": "",
                "deadline_basis": basis, "deadline_status": "unresolved",
                "days_after_base_due": None}
    late_days = (filing_date - base).days
    if filing_date <= base:
        status = "base_deadline_met"
    else:
        status = "base_deadline_missed_candidate"
    if accelerated and filing_date > accelerated:
        status += ";accelerated_threshold_candidate_missed_if_trigger_applies"
    elif accelerated:
        status += ";accelerated_threshold_candidate_not_missed_if_trigger_applies"
    return {
        "base_due_date": base.isoformat(),
        "accelerated_candidate_due_date": accelerated.isoformat() if accelerated else "",
        "deadline_basis": basis,
        "deadline_status": status,
        "days_after_base_due": late_days,
    }


def classify_event_text(text):
    t = str(text or "").lower()
    tags = []
    checks = {
        "employee_equity_award": ("award agreement", "stock award", "equity incentive plan", "compensation"),
        "business_combination_or_merger": ("business combination", "merger", "closing date", "acquired see id"),
        "capital_reorganization": ("reorganization", "share capital", "recapitalization", "reverse split"),
        "activist_or_governance_intent": ("declassify", "stockholder value", "communicating with the board", "board of directors", "strategic alternatives"),
        "litigation_or_dispute": ("complaint", "motion to dismiss", "lawsuit", "district court"),
        "aggregated_client_holdings": ("no one person has greater than 5% economic ownership", "held of record by clients", "relevant clients"),
        "investment_adviser_or_parent": ("investment adviser", "parent holding company", "control person"),
        "open_market_purchase": ("open market purchase", "purchased in the open market"),
        "gift_or_transfer": ("bona fide gifts", "transferred an aggregate", "gift of shares"),
        "issuer_employee_or_officer": ("chief financial officer", "chief executive officer", "employee equity", "services as the chief"),
        "no_recent_transactions_declared": ("has not effected any transactions", "no transactions in the past 60 days"),
    }
    matched = []
    for tag, phrases in checks.items():
        hits = [phrase for phrase in phrases if phrase in t]
        if hits:
            tags.append(tag)
            matched.extend(hits)
    if not tags:
        tags.append("unclassified_narrative")
    return tags, sorted(set(matched))


def extract_xml_details(xml_bytes):
    root = ET.fromstring(xml_bytes)
    text_parts = []
    persons = []
    rule_tags = []
    for element in root.iter():
        name = local_name(element.tag)
        value = (element.text or "").strip()
        if value:
            text_parts.append(value)
        if name in {"designateRulePursuantThisScheduleFiled", "rulePursuantThisScheduleFiled"} and value:
            rule_tags.append(value)
        if name == "reportingPersonInfo":
            fields = {}
            for child in list(element):
                child_name = local_name(child.tag)
                child_value = (child.text or "").strip()
                if child_value:
                    fields[child_name] = child_value
            persons.append(fields)
    text = "\n".join(text_parts)
    # Some schemas render rule selection in a nested checkbox/tag with a different spelling.
    for match in re.findall(r"Rule\s+13d-1\([bcd]\)", text, flags=re.I):
        rule_tags.append(match)
    return {"text": text, "persons": persons, "rules": sorted(set(rule_tags))}


def pct_value(persons):
    vals = []
    for person in persons:
        raw = person.get("percentOfClass", "")
        try:
            vals.append(float(str(raw).replace("%", "").strip()))
        except ValueError:
            continue
    return max(vals) if vals else 0.0


def load_csv(path):
    with Path(path).open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    if not rows:
        Path(path).write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict, tuple)) else v
                             for k, v in row.items()})


def run(args):
    raw_dir = Path(args.raw_artifact_dir) / "raw_submissions"
    events = load_csv(Path(args.phase91_artifact_dir) / "phase91_filing_events.csv")
    holiday_calendar = holidays.UnitedStates(years=range(2016, 2028), observed=True)
    rows, errors = [], []
    for event in events:
        accession = event.get("accession", "")
        raw_path = raw_dir / f"{accession}.txt"
        if not raw_path.is_file():
            errors.append({"accession": accession, "error": "raw_missing"})
            continue
        try:
            extracted = extract_primary_doc_xml(raw_path.read_bytes())
            details = extract_xml_details(extracted["xml_bytes"])
        except Exception as exc:
            errors.append({"accession": accession, "error": f"xml_parse:{exc!r}"})
            continue
        family = event.get("family", "")
        form = event.get("form", "")
        event_date = parse_date(event.get("event_date", ""))
        filing_date = parse_date(event.get("filing_date", ""))
        rules = rule_set(event.get("rule_designations", ""))
        if not rules:
            rules = {r.lower() for r in details["rules"]}
        max_pct = pct_value(details["persons"])
        deadline = deadline_candidates(family, form, event_date, filing_date, rules, max_pct, holiday_calendar)
        tags, matched = classify_event_text(details["text"])
        narrative_rule = sorted(set(re.findall(r"rule\s+13d-1\([a-d]\)", details["text"], flags=re.I)))
        form_rule_mismatch = family == "13D" and any("13d-1(d)" in x.lower() for x in narrative_rule)
        if form_rule_mismatch:
            tags.append("schedule_13D_text_references_13d_1_d_review")
        rows.append({
            **event,
            "parsed_rule_designations": sorted(rules),
            "narrative_rule_references": narrative_rule,
            "form_rule_mismatch_candidate": form_rule_mismatch,
            "max_reporting_person_pct": max_pct,
            "reporting_person_count": len(details["persons"]),
            "reporting_person_names": [p.get("reportingPersonName", "") for p in details["persons"]],
            "reporting_person_type_codes": [p.get("typeOfReportingPerson", "") for p in details["persons"]],
            "event_type_tags": sorted(set(tags)),
            "matched_event_keywords": matched,
            **deadline,
        })
    counts = Counter(tag for row in rows for tag in row["event_type_tags"])
    deadline_counts = Counter(
        "unresolved" if row["deadline_status"] == "unresolved"
        else ("base_deadline_met" if row["deadline_status"].startswith("base_deadline_met")
              else "base_deadline_missed_candidate")
        for row in rows
    )
    outliers = [
        {k: row.get(k) for k in ("accession", "family", "form", "filing_date", "event_date",
                                  "base_due_date", "days_after_base_due", "deadline_basis",
                                  "deadline_status", "event_type_tags", "filer_name", "subject_cik",
                                  "filer_cik", "acceptance_utc")}
        for row in rows if row.get("days_after_base_due") not in (None, "") and int(row["days_after_base_due"]) > 5
    ]
    summary = {
        "phase": "92-sec-13dg-deadline-and-event-semantics",
        "status": "COMPLETE" if not errors and len(rows) == 200 else "FAIL",
        "input_filings": len(events), "filings_classified": len(rows), "errors": errors,
        "event_type_tag_counts": dict(counts),
        "deadline_base_status_counts": dict(deadline_counts),
        "form_rule_mismatch_candidate_count": sum(bool(r["form_rule_mismatch_candidate"]) for r in rows),
        "filings_with_accelerated_threshold_candidate": sum(bool(r["accelerated_candidate_due_date"]) for r in rows),
        "base_due_date_outlier_count_gt_5_days": len(outliers),
        "base_due_date_outliers_gt_5_days": outliers,
        "interpretation_limits": [
            "Event-date text is not necessarily the date on which the market first learned the information.",
            "For Schedule 13G, the applicable deadline depends on filer category, initial versus amendment, quarter/month-end rules and threshold triggers; a rule designation and reported percentage do not prove the exact trigger date.",
            "Base due-date comparisons are candidate diagnostics, not legal compliance determinations. Threshold-accelerated dates are explicitly marked as candidates.",
            "Keyword event classes are triage labels, not proof of intent or 'smart money'.",
            "No forward returns, no alpha tests, no production changes."
        ],
        "forward_returns_used": False,
        "economic_test_authorized": False,
        "production_changes_authorized": False,
    }
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "phase92_event_deadline_audit.csv", rows)
    (outdir / "phase92_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    if summary["status"] != "COMPLETE":
        raise SystemExit(2)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-artifact-dir", required=True, type=Path)
    parser.add_argument("--phase91-artifact-dir", required=True, type=Path)
    parser.add_argument("--outdir", default=Path("phase92_audit"), type=Path)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
