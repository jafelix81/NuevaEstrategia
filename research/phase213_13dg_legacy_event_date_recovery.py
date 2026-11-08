#!/usr/bin/env python3
"""Phase 213: hash-pinned SEC Schedule 13D/G event-date and amendment-marker audit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from statistics import median

RUN_ID = 42073725379
ARTIFACT_ID = 13436764625
ARTIFACT_SHA256 = "85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc"
CSV_SHA256 = "be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5"
CSV_NAME = "phase124_global_13dg_submission_audit.csv"
MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE_PATTERNS = (
    re.compile(rf"\b{MONTH}\.?\s+\d{{1,2}}(?:st|nd|rd|th)?[,]?\s+\d{{4}}\b", re.I),
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
)
EVENT_LABEL = re.compile(
    r"date\s+of\s+event(?:\s+which\s+requires)?\s+filing\s+(?:of\s+)?this\s+statement", re.I
)
AMENDMENT_LABEL = re.compile(r"amendment\s*(?:no\.?|#)", re.I)


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

    def value(self):
        return " ".join(self.parts)


def parse_date(value):
    value = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", str(value).strip(), flags=re.I)
    value = re.sub(r"\s*,\s*", " ", value)
    value = re.sub(r"\s+", " ", value).replace("\xa0", " ")
    value = re.sub(r"^Sept\b", "Sep", value, flags=re.I)
    for fmt in ("%B %d %Y", "%b %d %Y", "%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def family(value):
    value = (value or "").upper()
    if "13D" in value:
        return "13D"
    if "13G" in value:
        return "13G"
    return None


def is_true(value):
    return str(value or "").strip().lower() == "true"


def primary_document(raw):
    for block in re.findall(r"<DOCUMENT>(.*?)</DOCUMENT>", raw, flags=re.I | re.S):
        type_match = re.search(r"<TYPE>\s*([^\r\n<]+)", block, flags=re.I)
        doc_type = type_match.group(1).strip() if type_match else ""
        if doc_type.upper().startswith(("SC 13D", "SC 13G", "SCHEDULE 13D", "SCHEDULE 13G")):
            text_match = re.search(r"<TEXT>(.*?)</TEXT>", block, flags=re.I | re.S)
            return doc_type, text_match.group(1) if text_match else block
    return None


def xml_value(body, tag):
    match = re.search(
        rf"<(?:\w+:)?{tag}\b[^>]*>\s*([^<]+?)\s*</(?:\w+:)?{tag}\s*>",
        body, flags=re.I | re.S
    )
    return match.group(1).strip() if match else None


def extract_event(body):
    # Structured 13D and 13G use different event-date tag names.
    for tag in ("dateOfEvent", "eventDateRequiresFilingThisStatement"):
        raw = xml_value(body, tag)
        if raw:
            parsed = parse_date(raw)
            if parsed:
                return parsed, f"XML_{tag}"
    parser = Text()
    parser.feed(body)
    visible = parser.value()
    labels = list(EVENT_LABEL.finditer(visible))
    if not labels:
        return None, "NO_LABEL"
    candidates = []
    for label in labels:
        left, right = max(0, label.start() - 220), min(len(visible), label.end() + 220)
        for pattern in DATE_PATTERNS:
            for match in pattern.finditer(visible[left:right]):
                parsed = parse_date(match.group(0))
                if not parsed:
                    continue
                start, end = left + match.start(), left + match.end()
                distance = start - label.start() if start >= label.start() else label.start() - end
                side = 0 if end <= label.start() else 1
                candidates.append((distance, side, start, parsed))
    if not candidates:
        return None, "LABEL_NO_DATE"
    candidates.sort(key=lambda item: item[:3])
    return candidates[0][3], "HTML_LABEL_NEAREST_DATE"


def extract_amendment_marker(body, xml_present):
    if xml_present:
        raw = xml_value(body, "amendmentNo")
        if raw and raw.isdigit():
            return int(raw), "XML_AMENDMENT_NO_TAG"
        return None, "XML_AMENDMENT_NO_ABSENT"
    parser = Text()
    parser.feed(body)
    visible = parser.value()[:3000]
    label_present = bool(AMENDMENT_LABEL.search(visible))
    patterns = (
        re.compile(r"amendment\s*(?:no\.?|#)\s*[:.]?\s*[_\s]*([0-9]{1,3})", re.I),
        re.compile(r"amendment\s+([0-9]{1,3})\b", re.I),
    )
    for pattern in patterns:
        match = pattern.search(visible)
        if match:
            return int(match.group(1)), "HTML_COVER_AMENDMENT_NUMBER"
    return None, "HTML_AMENDMENT_LABEL_NO_NUMBER" if label_present else "HTML_AMENDMENT_LABEL_ABSENT"


def weighted_share(rows, predicate):
    total = sum(row["sample_weight"] for row in rows)
    return sum(row["sample_weight"] for row in rows if predicate(row)) / total if total else None


def pct(value):
    return round(100 * value, 4) if value is not None else None


def quantile(values, q):
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    pos = (len(ordered) - 1) * q
    lo, hi = int(pos), min(int(pos) + 1, len(ordered) - 1)
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def summarize(rows):
    parsed = [row for row in rows if row["event_date"]]
    lags = [int(row["filing_minus_event_days"]) for row in parsed]
    qend = lambda row: row["event_date_is_quarter_end"] is True
    suffix_groups = {
        "index_form_suffix_A": [row for row in parsed if row["index_form_suffix_is_amendment"]],
        "index_form_suffix_not_A": [row for row in parsed if not row["index_form_suffix_is_amendment"]],
    }
    return {
        "n": len(rows),
        "event_date_n": len(parsed),
        "event_date_coverage_unweighted_pct": pct(len(parsed) / len(rows)) if rows else None,
        "event_date_coverage_sample_weighted_pct": pct(weighted_share(rows, lambda row: bool(row["event_date"]))),
        "quarter_end_event_date": {
            "n": sum(qend(row) for row in parsed),
            "unweighted_pct_within_parsed": pct(sum(qend(row) for row in parsed) / len(parsed)) if parsed else None,
            "sample_weighted_pct_within_parsed": pct(weighted_share(parsed, qend)),
        },
        "filing_minus_event_calendar_days": {
            "median": median(lags) if lags else None,
            "p25": round(quantile(lags, .25), 4) if lags else None,
            "p75": round(quantile(lags, .75), 4) if lags else None,
            "p90": round(quantile(lags, .90), 4) if lags else None,
            "max": max(lags) if lags else None,
            "same_day_n": sum(value == 0 for value in lags),
            "over_30_days_n": sum(value > 30 for value in lags),
            "over_90_days_n": sum(value > 90 for value in lags),
            "over_365_days_n": sum(value > 365 for value in lags),
        },
        "by_index_form_suffix": {
            label: {
                "n": len(group),
                "median_filing_minus_event_days": median([int(row["filing_minus_event_days"]) for row in group]) if group else None,
            }
            for label, group in suffix_groups.items()
        },
    }


def validate_header(raw, row):
    header = raw.split("</SEC-HEADER>", 1)[0]
    acc = re.search(r"ACCESSION NUMBER:\s*([0-9-]+)", header, re.I)
    accepted = re.search(r"<ACCEPTANCE-DATETIME>\s*(\d{14})", header, re.I)
    filed = re.search(r"FILED AS OF DATE:\s*(\d{8})", header, re.I)
    form_match = re.search(r"CONFORMED SUBMISSION TYPE:\s*([^\r\n]+)", header, re.I)
    if not all((acc, accepted, filed, form_match)):
        raise ValueError(f"Incomplete SEC header: {row['accession']}")
    if acc.group(1).replace("-", "") != row["accession"].replace("-", ""):
        raise ValueError(f"Accession mismatch: {row['accession']}")
    if accepted.group(1) != row["acceptance_datetime"]:
        raise ValueError(f"Acceptance mismatch: {row['accession']}")
    if datetime.strptime(filed.group(1), "%Y%m%d").date().isoformat() != row["filing_date_header"]:
        raise ValueError(f"Filing-date mismatch: {row['accession']}")
    if family(form_match.group(1)) != family(row["form"]):
        raise ValueError(f"Form-family mismatch: {row['accession']}")


def audit(input_dir):
    csv_path = input_dir / CSV_NAME
    payload = csv_path.read_bytes()
    csv_hash = hashlib.sha256(payload).hexdigest()
    if csv_hash != CSV_SHA256:
        raise ValueError(f"CSV SHA-256 mismatch: {csv_hash}")
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        source = list(csv.DictReader(handle))
    if len(source) != 600:
        raise ValueError(f"Expected 600 source rows, found {len(source)}")

    output = []
    raw_hash_ok = header_ok = primary_ok = xml_event_ok = xml_amendment_ok = 0
    for row in source:
        raw_bytes = (input_dir / row["raw_file"]).read_bytes()
        if hashlib.sha256(raw_bytes).hexdigest() != row["raw_sha256"]:
            raise ValueError(f"Raw SHA-256 mismatch: {row['accession']}")
        raw_hash_ok += 1
        raw = raw_bytes.decode("latin1")
        validate_header(raw, row)
        header_ok += 1

        is_alias = is_true(row.get("is_index_alias"))
        form_family = family(row.get("form"))
        primary = primary_document(raw)
        if is_alias:
            if form_family:
                raise ValueError(f"Alias classified as 13D/G: {row['accession']}")
            body = ""
            event, event_method = None, "INDEX_ALIAS_QUARANTINED"
            amend_no, amend_method = None, "INDEX_ALIAS_QUARANTINED"
        else:
            if form_family not in {"13D", "13G"} or primary is None:
                raise ValueError(f"Primary 13D/G document missing: {row['accession']}")
            _primary_type, body = primary
            if family(_primary_type) != form_family:
                raise ValueError(f"Primary form-family mismatch: {row['accession']}")
            primary_ok += 1
            event, event_method = extract_event(body)
            amend_no, amend_method = extract_amendment_marker(body, is_true(row.get("xml_present")))
            if is_true(row.get("xml_present")):
                csv_event = parse_date(row.get("event_date")) if row.get("event_date") else None
                if event != csv_event or event is None:
                    raise ValueError(f"XML event-date mismatch: {row['accession']}")
                xml_event_ok += 1
                csv_amend = row.get("amendment_no")
                csv_amend = int(float(csv_amend)) if csv_amend not in (None, "") else None
                if amend_no != csv_amend:
                    raise ValueError(f"XML amendment-number mismatch: {row['accession']}")
                xml_amendment_ok += 1

        filing = datetime.strptime(row["filing_date_header"], "%Y-%m-%d").date()
        acceptance = datetime.strptime(row["acceptance_datetime"], "%Y%m%d%H%M%S")
        lag = (filing - event).days if event else None
        output.append({
            "accession": row["accession"],
            "form": row["form"],
            "family": form_family or "",
            "filing_date": filing.isoformat(),
            "acceptance_datetime_header_wall_clock": acceptance.strftime("%Y-%m-%dT%H:%M:%S"),
            "subject_cik": row.get("subject_cik", ""),
            "filer_cik": row.get("filer_cik", ""),
            "cusip": row.get("cusip", ""),
            "class_title": row.get("class_title", ""),
            "event_date": event.isoformat() if event else "",
            "event_date_method": event_method,
            "filing_minus_event_days": lag if lag is not None else "",
            "event_date_is_quarter_end": bool((event.month, event.day) in {(3,31),(6,30),(9,30),(12,31)}) if event else "",
            "index_form_suffix_is_amendment": is_true(row.get("is_amendment")),
            "cover_amendment_no": amend_no if amend_no is not None else "",
            "cover_amendment_method": amend_method,
            "sample_weight": float(row["sample_weight"]),
            "sample_stratum": row.get("sample_stratum", ""),
            "xml_present": is_true(row.get("xml_present")),
            "rule_designations": row.get("rule_designations", "[]"),
        })

    actual = [row for row in output if row["cover_amendment_method"] != "INDEX_ALIAS_QUARANTINED"]
    aliases = [row for row in output if row["cover_amendment_method"] == "INDEX_ALIAS_QUARANTINED"]
    if len(actual) != 599 or len(aliases) != 1 or primary_ok != 599:
        raise ValueError("Unexpected actual/alias/primary-document counts")
    if xml_event_ok != 102 or xml_amendment_ok != 102:
        raise ValueError("Structured XML event/amendment fields did not match Phase 124 gold")

    parsed = [row for row in actual if row["event_date"]]
    unresolved = [row for row in actual if not row["event_date"]]
    by_family = {fam: summarize([row for row in actual if row["family"] == fam]) for fam in ("13D", "13G")}

    reform = {}
    for fam, cutoff in (("13D", date(2024, 2, 5)), ("13G", date(2024, 9, 30))):
        group = [row for row in actual if row["family"] == fam]
        pre = [row for row in group if date.fromisoformat(row["filing_date"]) < cutoff]
        post = [row for row in group if date.fromisoformat(row["filing_date"]) >= cutoff]
        reform[fam] = {"cutoff": cutoff.isoformat(), "pre": summarize(pre), "post": summarize(post)}

    marker = Counter(row["cover_amendment_method"] for row in actual)
    positive = [row for row in actual if row["cover_amendment_no"] != "" and int(row["cover_amendment_no"]) > 0]
    zero = [row for row in actual if row["cover_amendment_no"] != "" and int(row["cover_amendment_no"]) == 0]
    missing = [row for row in actual if row["cover_amendment_no"] == ""]
    index_a = [row for row in actual if row["index_form_suffix_is_amendment"]]
    xml_13g = [row for row in actual if row["family"] == "13G" and row["xml_present"] and row["event_date"]]
    rules = {}
    for rule in ("Rule 13d-1(b)", "Rule 13d-1(c)", "Rule 13d-1(d)"):
        subset = []
        for row in xml_13g:
            try:
                values = json.loads(row["rule_designations"] or "[]")
            except json.JSONDecodeError:
                values = []
            if rule in values:
                subset.append(row)
        rules[rule] = {
            "n": len(subset),
            "quarter_end_event_date_unweighted_pct": pct(sum(row["event_date_is_quarter_end"] for row in subset) / len(subset)) if subset else None,
            "quarter_end_event_date_sample_weighted_pct": pct(weighted_share(subset, lambda row: row["event_date_is_quarter_end"])) if subset else None,
        }

    total_weight = sum(row["sample_weight"] for row in actual)
    parsed_weight = sum(row["sample_weight"] for row in parsed)
    summary = {
        "phase": 213,
        "status": "COMPLETED_HASH_PINNED_13DG_LEGACY_EVENT_DATE_AND_AMENDMENT_AUDIT",
        "source": {
            "run_id": RUN_ID, "artifact_id": ARTIFACT_ID,
            "artifact_zip_sha256_from_github": ARTIFACT_SHA256,
            "csv_sha256_verified": csv_hash,
            "source_run_conclusion": "failure",
            "source_run_exit_code": 2,
            "source_run_summary_status": "PASS_WITH_INDEX_ALIAS_QUARANTINE",
            "source_run_note": "The Phase 124 artifact was uploaded despite the failed job. Its summary reports 599 actual submissions validated, one non-13D/G index alias quarantined and zero download/mirror failures. This phase independently verifies all 600 raw hashes and SEC headers.",
        },
        "integrity": {
            "source_rows": len(source), "actual_13dg": len(actual), "index_aliases_quarantined": len(aliases),
            "raw_file_sha256_verified": raw_hash_ok, "sec_header_accession_acceptance_filing_date_verified": header_ok,
            "primary_13dg_documents_found": primary_ok, "structured_xml_event_dates_exact_to_phase124": xml_event_ok,
            "structured_xml_amendment_numbers_exact_to_phase124_including_absence": xml_amendment_ok,
        },
        "event_date_recovery": {
            "parsed_n": len(parsed), "parsed_unweighted_pct": pct(len(parsed) / len(actual)),
            "parsed_sample_weighted_pct": pct(parsed_weight / total_weight),
            "unresolved_n": len(unresolved),
            "unresolved_method_counts": dict(sorted(Counter(row["event_date_method"] for row in unresolved).items())),
            "method_counts": dict(sorted(Counter(row["event_date_method"] for row in actual).items())),
            "by_family": by_family,
            "reform_era_descriptives": reform,
            "13g_rule_designation_structured_xml_subset": rules,
        },
        "amendment_marker_audit": {
            "index_form_suffix_A_n": len(index_a),
            "cover_amendment_number_positive_n": len(positive),
            "cover_amendment_number_zero_n": len(zero),
            "cover_amendment_number_missing_n": len(missing),
            "html_legacy_number_parsed_n": marker["HTML_COVER_AMENDMENT_NUMBER"],
            "html_legacy_label_no_number_n": marker["HTML_AMENDMENT_LABEL_NO_NUMBER"],
            "html_legacy_label_absent_n": marker["HTML_AMENDMENT_LABEL_ABSENT"],
            "xml_amendment_number_tag_n": marker["XML_AMENDMENT_NO_TAG"],
            "xml_amendment_number_absent_n": marker["XML_AMENDMENT_NO_ABSENT"],
            "index_not_A_but_positive_cover_number_n": sum(not row["index_form_suffix_is_amendment"] for row in positive),
            "index_A_but_no_positive_cover_number_n": sum(row["index_form_suffix_is_amendment"] for row in actual if row not in positive),
            "interpretation": "The index /A suffix is useful but not a complete document-level amendment marker. Preserve it separately from the cover-page/XML amendment number; missing cover numbers remain unknown, not zero.",
        },
        "sample_design": {
            "sample_n": 599, "quarters": 43, "nonempty_strata": 172,
            "frame": "2016Q1-2026Q3 global SEC master-index 13D/G accession frame after prior-pilot exclusions",
            "weighting_caveat": "Sample-weighted rates are descriptive within the stratified sample and conditional on parseable event dates; format-dependent missingness prevents complete population inference.",
        },
        "knowledge_clock": {
            "event_date_is_knowledge_timestamp": False,
            "availability_field": "SEC-header ACCEPTANCE-DATETIME",
            "acceptance_treatment": "Retain header wall-clock; no timezone conversion or exact public-dissemination claim.",
            "daily_feature_rule": "No same-day use; earliest candidate is next full regular session after acceptance, subject to separate dissemination and security-identity validation.",
        },
        "decision": "Event-date recovery materially improves 13D/G document normalization, but event_date is neither a trade timestamp nor a public-knowledge timestamp. 13G dates are often quarter-end reporting references; 13D dates are less often quarter-end but can be stale by many months. Keep 13D and 13G separate, preserve both index /A and document amendment markers, and do not construct ownership-state edges from previousAccessionNumber alone.",
        "alpha_test_performed": False, "forward_returns_used": False, "final_holdout_used": False,
        "production_changed": False, "f80_changed": False,
        "limitations": [
            "Only a 599-submission stratified sample is processed; no full historical active/delisted security universe is reconstructed.",
            "The 46 unresolved event dates are not imputed: 35 lack the recognized label and 11 contain a label but no unambiguous four-digit-year date.",
            "The 451 legacy HTML event dates are label-anchored nearest-date extractions, manually spot-checked across four form/amendment types; no independent structured-field gold exists for HTML.",
            "The 102 XML event dates and amendment-number fields match Phase 124 exactly; this validates only the structured XML subset.",
            "CUSIP is not a permanent security identifier; effective-dated issuer/class/corporate-action mapping remains required.",
            "Phase 160/163 show previousAccessionNumber is not a verified immediate-predecessor edge.",
            "No feature, return, incremental-alpha, bootstrap, LOO or OOS test is authorized.",
        ],
    }
    return output, summary


def write_outputs(rows, summary, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "phase213_13dg_event_date_recovery_rows.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / "phase213_13dg_event_date_recovery_result.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    rows, summary = audit(args.input_dir)
    write_outputs(rows, summary, args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
