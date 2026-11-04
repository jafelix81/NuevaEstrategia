"""Full-corpus audit of SEC structured Schedule 13D/13G XML documents.

Uses the existing Phase 35 filing panel as its immutable input. It retrieves
only primary_doc.xml documents, obtains acceptanceDateTime from issuer
submissions metadata where available, and parses each filing with the
schema-aware Phase 72 parser. It does not calculate returns.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests

from research.phase72_13dg_structured_xml_parser import parse_schedule13_xml


SEC_DATA = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"
USER_AGENT = "NuevaEstrategia research contact research@example.com"
KNOWN_TYPE_CODES = {
    "AF", "AV", "BD", "BK", "CO", "CP", "CU", "EP", "FI", "GU", "HC",
    "IA", "IC", "IN", "IV", "NP", "OO", "OT", "PF", "PN", "RE", "SA",
    "SI", "ST", "TR",
}


def normalize_accession(value: str) -> str:
    return re.sub(r"\D", "", str(value or ""))


def normalize_cik(value: str) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.zfill(10) if digits and len(digits) <= 10 else digits


def expected_submission_type(form: str) -> str:
    value = str(form or "").strip().upper()
    if value.startswith("SC "):
        return "SCHEDULE " + value[3:]
    return value


def build_lineage_edge(
    current: dict,
    previous_accession: str,
    accession_index: dict[str, dict],
) -> dict:
    previous_key = normalize_accession(previous_accession)
    predecessor = accession_index.get(previous_key) if previous_key else None
    current_issuer = normalize_cik(current.get("issuer_cik", ""))
    if not previous_key:
        status = "no_declared_predecessor"
    elif predecessor is None:
        status = "predecessor_outside_input_panel"
    elif normalize_cik(predecessor.get("issuer_cik", "")) == current_issuer:
        status = "predecessor_in_panel_same_issuer"
    else:
        status = "predecessor_in_panel_cross_issuer"
    return {
        "accession": current.get("accession", ""),
        "accession_key": normalize_accession(current.get("accession", "")),
        "issuer_cik": current_issuer,
        "form": current.get("form", ""),
        "filing_date": current.get("filing_date", ""),
        "previous_accession_number": str(previous_accession or ""),
        "previous_accession_key": previous_key,
        "predecessor_in_input_panel": predecessor is not None,
        "predecessor_issuer_cik": normalize_cik(predecessor.get("issuer_cik", "")) if predecessor else "",
        "predecessor_form": predecessor.get("form", "") if predecessor else "",
        "predecessor_filing_date": predecessor.get("filing_date", "") if predecessor else "",
        "predecessor_same_issuer": (
            normalize_cik(predecessor.get("issuer_cik", "")) == current_issuer
            if predecessor else None
        ),
        "lineage_status": status,
    }


class SecClient:
    def __init__(self, sleep_seconds: float = 0.6, max_retries: int = 5, timeout: int = 40):
        self.sleep_seconds = sleep_seconds
        self.max_retries = max_retries
        self.timeout = timeout
        self.last_request = 0.0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/xml,text/xml,application/json,*/*",
        })
        self.request_count = 0

    def _wait(self):
        now = time.monotonic()
        delay = self.sleep_seconds - (now - self.last_request)
        if delay > 0:
            time.sleep(delay)
        self.last_request = time.monotonic()

    def get(self, url: str) -> requests.Response:
        last_error = None
        for attempt in range(self.max_retries + 1):
            self._wait()
            try:
                response = self.session.get(url, timeout=self.timeout)
                self.request_count += 1
                if response.status_code in {429, 500, 502, 503, 504}:
                    retry_after = response.headers.get("Retry-After", "")
                    try:
                        delay = float(retry_after)
                    except (TypeError, ValueError):
                        delay = min(60.0, 2.0 ** attempt)
                    if attempt < self.max_retries:
                        time.sleep(max(delay, self.sleep_seconds))
                        continue
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(min(60.0, 2.0 ** attempt))
        raise RuntimeError(f"GET failed after retries: {url}: {last_error}")

    def json(self, url: str) -> dict:
        return self.get(url).json()


def _array_value(block: dict, name: str, index: int) -> str:
    values = block.get(name, [])
    if index >= len(values):
        return ""
    value = values[index]
    return "" if value is None else str(value)


def _ingest_submission_block(block: dict, target: dict[str, dict], needed: set[str]) -> None:
    accessions = block.get("accessionNumber", [])
    for i, accession in enumerate(accessions):
        key = normalize_accession(accession)
        if key not in needed:
            continue
        item = {
            "accession": str(accession),
            "acceptance_datetime": _array_value(block, "acceptanceDateTime", i),
            "filing_date": _array_value(block, "filingDate", i),
            "form": _array_value(block, "form", i),
            "primary_document": _array_value(block, "primaryDocument", i),
        }
        prior = target.get(key)
        if prior is None or (not prior.get("acceptance_datetime") and item.get("acceptance_datetime")):
            target[key] = item


def fetch_submission_index(
    client: SecClient,
    issuer_cik: str,
    needed_accessions: set[str],
    min_filing_date: str,
    max_filing_date: str,
) -> tuple[dict[str, dict], list[dict]]:
    cik = normalize_cik(issuer_cik)
    index: dict[str, dict] = {}
    errors: list[dict] = []
    try:
        payload = client.json(SEC_DATA.format(cik=cik))
    except Exception as exc:
        return index, [{"issuer_cik": cik, "stage": "submissions_recent", "error": repr(exc)}]

    filings = payload.get("filings", {})
    _ingest_submission_block(filings.get("recent", {}), index, needed_accessions)
    missing = needed_accessions - set(index)
    if not missing:
        return index, errors

    files = filings.get("files", [])
    for old in files:
        if not missing:
            break
        filing_from = str(old.get("filingFrom", ""))
        filing_to = str(old.get("filingTo", ""))
        if filing_to and filing_to < min_filing_date:
            continue
        if filing_from and filing_from > max_filing_date:
            continue
        name = old.get("name")
        if not name:
            continue
        try:
            old_payload = client.json(f"https://data.sec.gov/submissions/{quote(str(name))}")
            _ingest_submission_block(old_payload, index, missing)
            missing = needed_accessions - set(index)
        except Exception as exc:
            errors.append({
                "issuer_cik": cik,
                "stage": "submissions_historical",
                "file": str(name),
                "error": repr(exc),
            })
    return index, errors


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _filing_row(source: dict, parsed: dict, submission: dict, fetch_url: str) -> dict:
    expected = expected_submission_type(source.get("form", ""))
    actual = str(parsed.get("submission_type", "")).upper()
    issuer_source = normalize_cik(source.get("issuer_cik", ""))
    issuer_xml = normalize_cik(parsed.get("issuer_cik", ""))
    accession_prefix_cik = normalize_cik(normalize_accession(source.get("accession", ""))[:10])
    filer_cik_xml = normalize_cik(parsed.get("filer_cik_xml", ""))
    filer_cik_match = (filer_cik_xml == accession_prefix_cik) if filer_cik_xml and accession_prefix_cik else None
    return {
        "ticker": source.get("ticker", ""),
        "issuer_cik_source": issuer_source,
        "issuer_cik_xml": issuer_xml,
        "issuer_cik_match": issuer_source == issuer_xml and bool(issuer_source),
        "issuer_name_xml": parsed.get("issuer_name", ""),
        "form_source": source.get("form", ""),
        "submission_type_xml": actual,
        "form_match": expected == actual,
        "filing_date": source.get("filing_date", ""),
        "knowledge_date": source.get("filing_date", ""),
        "knowledge_date_rule": "SEC submissions filingDate; conservative date-level; event_date not used",
        "accepted_datetime": submission.get("acceptance_datetime", ""),
        "submission_filing_date": submission.get("filing_date", ""),
        "submission_form": submission.get("form", ""),
        "submission_primary_document": submission.get("primary_document", ""),
        "report_date": source.get("report_date", ""),
        "event_date_xml": parsed.get("event_date", ""),
        "accession": source.get("accession", ""),
        "accession_key": normalize_accession(source.get("accession", "")),
        "primary_document": source.get("primary_document", ""),
        "primary_document_url": fetch_url,
        "accession_prefix_cik": accession_prefix_cik,
        "filer_cik_xml": filer_cik_xml,
        "filer_cik_match": filer_cik_match,
        "is_amendment": parsed.get("is_amendment", False),
        "amendment_number": parsed.get("amendment_number", ""),
        "previous_accession_number": parsed.get("previous_accession_number", ""),
        "lineage_status": parsed.get("lineage_status", ""),
        "reporting_person_count": parsed.get("reporting_person_count", 0),
        "cusips_json": _json(parsed.get("cusips", [])),
        "rule_designations_json": _json(parsed.get("rule_designations", [])),
        "filing_person_name_narrative": parsed.get("filing_person_name_narrative", ""),
        "group_members_narrative": parsed.get("group_members_narrative", ""),
        "purpose_text": parsed.get("purpose_text", ""),
        "parser_version": parsed.get("parser_version", ""),
        "schema_version": parsed.get("schema_version", ""),
        "parse_status": "success",
    }


def _person_rows(source: dict, parsed: dict, submission: dict) -> list[dict]:
    rows = []
    for i, person in enumerate(parsed.get("reporting_persons", []), 1):
        rows.append({
            "accession": source.get("accession", ""),
            "accession_key": normalize_accession(source.get("accession", "")),
            "ticker": source.get("ticker", ""),
            "issuer_cik": normalize_cik(source.get("issuer_cik", "")),
            "form": source.get("form", ""),
            "filing_date": source.get("filing_date", ""),
            "accepted_datetime": submission.get("acceptance_datetime", ""),
            "person_index": i,
            "person_cik": person.get("person_cik", ""),
            "person_cik_status": person.get("person_cik_status", ""),
            "person_no_cik_flag": person.get("person_no_cik_flag", ""),
            "name": person.get("name", ""),
            "member_of_group": person.get("member_of_group", ""),
            "citizenship_or_organization": person.get("citizenship_or_organization", ""),
            "type_codes_json": _json(person.get("type_codes", [])),
            "fund_types_json": _json(person.get("fund_types", [])),
            "sole_voting_power": person.get("sole_voting_power", ""),
            "shared_voting_power": person.get("shared_voting_power", ""),
            "sole_dispositive_power": person.get("sole_dispositive_power", ""),
            "shared_dispositive_power": person.get("shared_dispositive_power", ""),
            "aggregate_amount_owned": person.get("aggregate_amount_owned", ""),
            "percent_of_class": person.get("percent_of_class", ""),
            "comments": person.get("comments", ""),
        })
    return rows


def _write_csv(path: Path, rows: list[dict], columns: list[str] | None = None) -> None:
    frame = pd.DataFrame(rows)
    if frame.empty and columns:
        frame = pd.DataFrame(columns=columns)
    frame.to_csv(path, index=False)


def stratified_sample(xml: pd.DataFrame, limit: int | None) -> pd.DataFrame:
    if limit is None or limit >= len(xml):
        return xml.copy()
    frame = xml.copy()
    frame["_form_family"] = frame["form"].str.upper().apply(lambda x: "13D" if "13D" in x else ("13G" if "13G" in x else "OTHER"))
    frame["_is_amendment"] = frame["form"].str.upper().str.endswith("/A")
    frame["_period"] = frame["filing_date"].apply(lambda x: "voluntary_xml_pre_mandate" if str(x) < "2024-12-18" else "mandatory_era")
    groups = [g for _, g in frame.groupby(["_form_family", "_is_amendment", "_period"], sort=True)]
    quota = max(1, limit // max(1, len(groups)))
    selected = []
    remaining = limit
    for group in groups:
        if remaining <= 0:
            break
        n = min(quota, len(group), remaining)
        if n:
            selected.append(group.sample(n=n, random_state=42))
            remaining -= n
    if remaining > 0:
        selected_keys = {str(x) for g in selected for x in g["accession"].tolist()}
        rest = frame[~frame["accession"].astype(str).isin(selected_keys)]
        if not rest.empty:
            selected.append(rest.sample(n=min(remaining, len(rest)), random_state=43))
    result = pd.concat(selected, ignore_index=True) if selected else frame.head(0)
    return result.drop(columns=["_form_family", "_is_amendment", "_period"]).sort_values("accession").reset_index(drop=True)


def run_audit(
    input_csv: Path,
    outdir: Path,
    sleep_seconds: float = 0.6,
    max_retries: int = 5,
    checkpoint_every: int = 100,
    resume: bool = True,
    limit: int | None = None,
) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    source = pd.read_csv(input_csv, dtype=str, keep_default_na=False)
    required = {"ticker", "issuer_cik", "form", "filing_date", "accession", "primary_document"}
    missing_cols = sorted(required - set(source.columns))
    if missing_cols:
        raise ValueError(f"input CSV missing required columns: {missing_cols}")

    xml = source[source["primary_document"].str.lower().str.endswith(".xml")].copy()
    xml = xml[xml["primary_document"].str.lower().str.contains("primary_doc\\.xml", regex=True)].copy()
    xml = xml.drop_duplicates(subset=["accession"]).reset_index(drop=True)
    xml_rows_available = len(xml)
    xml = stratified_sample(xml, limit)
    if xml.empty:
        raise RuntimeError("no structured primary_doc.xml rows found in input artifact")

    accession_index = {}
    issuer_to_needed: dict[str, set[str]] = defaultdict(set)
    for row in xml.to_dict("records"):
        key = normalize_accession(row["accession"])
        issuer_to_needed[normalize_cik(row["issuer_cik"])].add(key)
        accession_index[key] = {
            "accession": row["accession"],
            "issuer_cik": row["issuer_cik"],
            "form": row["form"],
            "filing_date": row["filing_date"],
        }

    client = SecClient(sleep_seconds=sleep_seconds, max_retries=max_retries)
    submission_index: dict[str, dict] = {}
    submission_errors: list[dict] = []
    min_date = str(xml["filing_date"].min())
    max_date = str(xml["filing_date"].max())
    for n, (cik, needed) in enumerate(sorted(issuer_to_needed.items()), 1):
        idx, errs = fetch_submission_index(client, cik, needed, min_date, max_date)
        submission_index.update(idx)
        submission_errors.extend(errs)
        if n % 25 == 0 or n == len(issuer_to_needed):
            print(
                f"SUBMISSIONS {n}/{len(issuer_to_needed)} | accession_matches={len(submission_index)} "
                f"| errors={len(submission_errors)}",
                flush=True,
            )

    filing_rows: list[dict] = []
    person_rows: list[dict] = []
    lineage_rows: list[dict] = []
    errors: list[dict] = []
    checkpoint = outdir / "filings_checkpoint.csv"
    people_checkpoint = outdir / "reporting_persons_checkpoint.csv"
    lineage_checkpoint = outdir / "lineage_edges_checkpoint.csv"
    errors_checkpoint = outdir / "errors_checkpoint.csv"

    completed_keys: set[str] = set()
    if resume and checkpoint.exists():
        old = pd.read_csv(checkpoint, dtype=str, keep_default_na=False)
        filing_rows = old.to_dict("records")
        completed_keys = {
            normalize_accession(r.get("accession", ""))
            for r in filing_rows if r.get("parse_status") == "success"
        }
    if resume and people_checkpoint.exists():
        person_rows = pd.read_csv(people_checkpoint, dtype=str, keep_default_na=False).to_dict("records")
    if resume and lineage_checkpoint.exists():
        lineage_rows = pd.read_csv(lineage_checkpoint, dtype=str, keep_default_na=False).to_dict("records")
    if resume and errors_checkpoint.exists():
        errors = pd.read_csv(errors_checkpoint, dtype=str, keep_default_na=False).to_dict("records")

    processed_this_run = 0
    try:
        for i, row in enumerate(xml.to_dict("records"), 1):
            key = normalize_accession(row["accession"])
            if key in completed_keys:
                continue
            cik_path = str(int(normalize_cik(row["issuer_cik"])))
            acc_path = key
            document = quote(str(row["primary_document"]), safe="/._-")
            url = SEC_ARCHIVE.format(cik=cik_path, accession=acc_path, document=document)
            submission = submission_index.get(key, {})
            try:
                response = client.get(url)
                parsed = parse_schedule13_xml(response.content)
                frow = _filing_row(row, parsed, submission, url)
                filing_rows = [x for x in filing_rows if normalize_accession(x.get("accession", "")) != key]
                filing_rows.append(frow)
                person_rows = [x for x in person_rows if normalize_accession(x.get("accession", "")) != key]
                person_rows.extend(_person_rows(row, parsed, submission))
                if parsed.get("is_amendment"):
                    edge = build_lineage_edge(row, parsed.get("previous_accession_number", ""), accession_index)
                    edge["amendment_number"] = parsed.get("amendment_number", "")
                    lineage_rows = [x for x in lineage_rows if normalize_accession(x.get("accession", "")) != key]
                    lineage_rows.append(edge)
                errors = [x for x in errors if normalize_accession(x.get("accession", "")) != key]
                completed_keys.add(key)
            except Exception as exc:
                errors.append({
                    "accession": row["accession"],
                    "accession_key": key,
                    "ticker": row["ticker"],
                    "issuer_cik": row["issuer_cik"],
                    "form": row["form"],
                    "filing_date": row["filing_date"],
                    "url": url,
                    "error": repr(exc),
                })
            processed_this_run += 1
            if processed_this_run % checkpoint_every == 0 or i == len(xml):
                _write_csv(checkpoint, filing_rows)
                _write_csv(people_checkpoint, person_rows)
                _write_csv(lineage_checkpoint, lineage_rows)
                _write_csv(errors_checkpoint, errors)
                print(
                    f"XML {i}/{len(xml)} | parsed={len(completed_keys)} "
                    f"| people={len(person_rows)} | errors={len(errors)} "
                    f"| requests={client.request_count}",
                    flush=True,
                )
    finally:
        _write_csv(checkpoint, filing_rows)
        _write_csv(people_checkpoint, person_rows)
        _write_csv(lineage_checkpoint, lineage_rows)
        _write_csv(errors_checkpoint, errors)

    filing_frame = pd.DataFrame(filing_rows)
    person_frame = pd.DataFrame(person_rows)
    lineage_frame = pd.DataFrame(lineage_rows)
    if not filing_frame.empty:
        filing_frame = filing_frame.sort_values(["filing_date", "accession"]).reset_index(drop=True)
    if not person_frame.empty:
        person_frame = person_frame.sort_values(["filing_date", "accession", "person_index"]).reset_index(drop=True)
    if not lineage_frame.empty:
        lineage_frame = lineage_frame.sort_values(["filing_date", "accession"]).reset_index(drop=True)

    filing_frame.to_csv(outdir / "filings.csv", index=False)
    person_frame.to_csv(outdir / "reporting_persons.csv", index=False)
    lineage_frame.to_csv(outdir / "lineage_edges.csv", index=False)
    pd.DataFrame(errors).to_csv(outdir / "fetch_parse_errors.csv", index=False)
    pd.DataFrame(submission_errors).to_csv(outdir / "submission_index_errors.csv", index=False)

    parsed_n = int(len(filing_frame))
    total_n = int(len(xml))
    issuer_matches = int(filing_frame["issuer_cik_match"].astype(str).str.lower().eq("true").sum()) if parsed_n else 0
    form_matches = int(filing_frame["form_match"].astype(str).str.lower().eq("true").sum()) if parsed_n else 0
    people_positive = int((pd.to_numeric(filing_frame["reporting_person_count"], errors="coerce").fillna(0) > 0).sum()) if parsed_n else 0
    acceptance_n = int(filing_frame["accepted_datetime"].astype(str).ne("").sum()) if parsed_n else 0
    filer_present = int(filing_frame["filer_cik_xml"].astype(str).ne("").sum()) if parsed_n else 0
    filer_matches = int(filing_frame["filer_cik_match"].astype(str).str.lower().eq("true").sum()) if parsed_n else 0
    filer_match_rate = filer_matches / filer_present if filer_present else 0.0
    event_date_n = int(filing_frame["event_date_xml"].astype(str).ne("").sum()) if parsed_n else 0
    amendment_number_n = int(filing_frame["amendment_number"].astype(str).ne("").sum()) if parsed_n else 0
    submission_date_matches = int((filing_frame["filing_date"].astype(str) == filing_frame["submission_filing_date"].astype(str)).sum()) if parsed_n else 0
    submission_date_present = int(filing_frame["submission_filing_date"].astype(str).ne("").sum()) if parsed_n else 0
    submission_date_match_rate = submission_date_matches / submission_date_present if submission_date_present else 0.0

    schema_versions = Counter(filing_frame.get("schema_version", pd.Series(dtype=str)).fillna("").astype(str))
    cik_status = Counter(person_frame.get("person_cik_status", pd.Series(dtype=str)).fillna("").astype(str))
    group_flags = Counter(person_frame.get("member_of_group", pd.Series(dtype=str)).fillna("").astype(str))
    type_codes = Counter()
    for raw in person_frame.get("type_codes_json", pd.Series(dtype=str)).fillna("[]"):
        try:
            for code in json.loads(raw):
                type_codes[str(code).strip().upper()] += 1
        except Exception:
            continue
    unknown_type_codes = {k: v for k, v in type_codes.items() if k not in KNOWN_TYPE_CODES}

    amendments_n = int(filing_frame["is_amendment"].astype(str).str.lower().eq("true").sum()) if parsed_n else 0
    with_predecessor = int(filing_frame["previous_accession_number"].astype(str).ne("").sum()) if parsed_n else 0
    predecessor_same = int(lineage_frame["lineage_status"].eq("predecessor_in_panel_same_issuer").sum()) if not lineage_frame.empty else 0
    predecessor_cross = int(lineage_frame["lineage_status"].eq("predecessor_in_panel_cross_issuer").sum()) if not lineage_frame.empty else 0
    predecessor_outside = int(lineage_frame["lineage_status"].eq("predecessor_outside_input_panel").sum()) if not lineage_frame.empty else 0

    fetch_parse_rate = parsed_n / total_n if total_n else 0.0
    issuer_rate = issuer_matches / parsed_n if parsed_n else 0.0
    form_rate = form_matches / parsed_n if parsed_n else 0.0
    person_rate = people_positive / parsed_n if parsed_n else 0.0
    gates = {
        "xml_parse_rate_ge_99_5pct": fetch_parse_rate >= 0.995,
        "issuer_cik_concordance_ge_99_5pct": issuer_rate >= 0.995,
        "form_concordance_ge_99_5pct": form_rate >= 0.995,
        "filer_cik_concordance_ge_99_5pct_when_present": filer_match_rate >= 0.995 if filer_present else False,
        "submission_filing_date_concordance_ge_99_5pct_when_present": submission_date_match_rate >= 0.995 if submission_date_present else False,
        "reporting_person_count_positive_ge_99_5pct": person_rate >= 0.995,
        "no_cross_issuer_predecessor_edges": predecessor_cross == 0,
    }
    data_gate = "PASS" if all(gates.values()) else "FAIL"
    summary = {
        "phase": "72-13dg-structured-xml-corpus-audit",
        "status": "COMPLETE" if parsed_n == total_n else "PARTIAL",
        "data_gate": data_gate,
        "source_run_id": 41575083622,
        "source_artifact_id": 13212292743,
        "source_artifact_sha256": "1ba55129f8a2f2365b37e20f557759fbccd2ab2f22781f03930065c11f16337f",
        "source_input_rows": int(len(source)),
        "xml_rows_available": int(xml_rows_available),
        "xml_rows_expected": total_n,
        "sample_limit": limit,
        "sample_strata_counts": (xml.assign(form_family=xml["form"].str.upper().apply(lambda x: "13D" if "13D" in x else ("13G" if "13G" in x else "OTHER")), is_amendment=xml["form"].str.upper().str.endswith("/A"), period=xml["filing_date"].apply(lambda x: "voluntary_xml_pre_mandate" if str(x) < "2024-12-18" else "mandatory_era")).groupby(["form_family", "is_amendment", "period"]).size().reset_index(name="rows").to_dict("records")) if not xml.empty else [],
        "parsed_filings": parsed_n,
        "parse_errors": int(total_n - parsed_n),
        "reporting_person_rows": int(len(person_frame)),
        "issuer_cik_concordance_rate": issuer_rate,
        "form_concordance_rate": form_rate,
        "positive_reporting_person_count_rate": person_rate,
        "acceptance_datetime_rows": acceptance_n,
        "acceptance_datetime_coverage": acceptance_n / parsed_n if parsed_n else 0.0,
        "filer_cik_present_rows": filer_present,
        "filer_cik_match_rows": filer_matches,
        "filer_cik_match_rate_when_present": filer_match_rate,
        "event_date_rows": event_date_n,
        "event_date_coverage": event_date_n / parsed_n if parsed_n else 0.0,
        "amendment_number_rows": amendment_number_n,
        "amendment_number_coverage": amendment_number_n / amendments_n if amendments_n else 0.0,
        "submission_filing_date_match_rows": submission_date_matches,
        "submission_filing_date_match_rate_when_present": submission_date_match_rate,
        "submission_index_matches": int(len(submission_index)),
        "submission_index_errors": int(len(submission_errors)),
        "schema_version_counts": dict(schema_versions),
        "person_cik_status_counts": dict(cik_status),
        "member_group_flag_counts": dict(group_flags),
        "type_code_counts": dict(type_codes),
        "unknown_type_codes": unknown_type_codes,
        "amendments": amendments_n,
        "amendments_with_previous_accession": with_predecessor,
        "amendment_predecessor_in_panel_same_issuer": predecessor_same,
        "amendment_predecessor_in_panel_cross_issuer": predecessor_cross,
        "amendment_predecessor_outside_panel": predecessor_outside,
        "lineage_edges": int(len(lineage_frame)),
        "gate_checks": gates,
        "request_count": client.request_count,
        "started_utc": started,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_date_rule": "Use SEC submissions filingDate as conservative date-level KnowledgeDate; preserve acceptanceDateTime separately; never substitute XML eventDate.",
        "accepted_timestamp_rule": "acceptanceDateTime is preserved for later availability analysis; no intraday trading assumption or return test in this phase.",
        "forward_returns_used": False,
        "economic_test_authorized": False,
        "limitations": [
            "Structured XML only; legacy HTML filings require a separate parser and validation.",
            "A declared previousAccessionNumber is recorded as a direct edge but is not assumed to be a complete economic-group history.",
            "A missing reporting-person CIK is preserved; filer/accession-prefix CIK is never substituted.",
            "memberOfGroup/memberGroup flags are evidence, not a unique economic-group identifier.",
            "Historical F80 membership and delisted predecessor coverage remain untested.",
        ],
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("phase72_13dg_structured_xml_corpus_audit"))
    parser.add_argument("--sleep-seconds", type=float, default=0.6)
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--checkpoint-every", type=int, default=100)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Deterministic stratified sample size; omit for full corpus")
    args = parser.parse_args()
    summary = run_audit(
        input_csv=args.input_csv,
        outdir=args.outdir,
        sleep_seconds=args.sleep_seconds,
        max_retries=args.max_retries,
        checkpoint_every=args.checkpoint_every,
        resume=not args.no_resume,
        limit=args.limit,
    )
    if summary["status"] != "COMPLETE" or summary["data_gate"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
