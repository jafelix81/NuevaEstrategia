#!/usr/bin/env python3
"""Phase 328: conservative SEC prior-filing XBRL identity pilot for Form 4 ticker collisions, sourced from the successful Phase 325 artifact.

This is an identity/coverage audit only. It uses the latest eligible periodic filing
strictly before each sampled Form 4 collision date, preserves XBRL contexts, and never
turns a ticker or free-text title into a permanent security key.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import re
import time
import zipfile
from collections import Counter
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

PHASE = 328
PHASE325_ARTIFACT_ID = 13931894766
PHASE325_ARTIFACT_SHA256 = "6d7930230a60036931857520df07b28087720d54ae9d3bee8f4b1cfe2fbcefa3"
EXPECTED_PAIRS = 28
ALLOWED_FORMS = {
    "10-K", "10-K/A", "10-Q", "10-Q/A", "20-F", "20-F/A", "40-F", "40-F/A",
    "N-2", "N-2/A", "N-CSR", "N-CSR/A", "N-CSRS", "N-CSRS/A",
}
FACT_NAMES = {
    "TradingSymbol", "NoTradingSymbolFlag", "Security12bTitle",
    "Security12gTitle", "SecurityExchangeName",
}
RETRY_STATUS = {429, 500, 502, 503, 504}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def norm_cik(value: str) -> str:
    s = re.sub(r"\D", "", str(value or ""))
    if not s or len(s) > 10:
        raise ValueError("invalid_cik")
    return str(int(s))


def norm_symbol(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").strip().upper())


def parse_event_date(value: str) -> date:
    return date.fromisoformat(value)


def latest_shared_date(value: str) -> str:
    dates = sorted({x.strip() for x in str(value or "").split(";") if x.strip()})
    if not dates:
        raise ValueError("collision_pair_has_no_shared_filing_date")
    for item in dates:
        date.fromisoformat(item)
    return dates[-1]


def load_collision_pairs(path: Path) -> list[dict]:
    raw = path.read_bytes()
    digest = sha256(raw)
    if digest != PHASE326_ARTIFACT_SHA256:
        raise ValueError(f"phase326_artifact_sha256_mismatch:{digest}")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = [n for n in zf.namelist() if n.endswith("phase325_same_day_symbol_collisions.csv")]
        if len(names) != 1:
            raise ValueError("expected_one_phase325_same_day_symbol_collisions_csv")
        rows = list(csv.DictReader(io.StringIO(zf.read(names[0]).decode("utf-8-sig"))))
    if len(rows) != EXPECTED_PAIRS:
        raise ValueError(f"phase325_pair_count_mismatch:{len(rows)}")
    required = {
        "ticker_candidate", "issuer_cik_a", "issuer_name_a",
        "issuer_cik_b", "issuer_name_b", "shared_filing_dates",
    }
    if not required.issubset(rows[0]):
        raise ValueError("phase325_collision_schema_mismatch")
    seen = set()
    shared_date_count = 0
    for index, row in enumerate(rows, 1):
        row["issuer_cik_a"] = norm_cik(row["issuer_cik_a"])
        row["issuer_cik_b"] = norm_cik(row["issuer_cik_b"])
        row["ticker_candidate"] = norm_symbol(row["ticker_candidate"])
        row["pair_id"] = f"P{index:02d}_{row['ticker_candidate']}_{row['issuer_cik_a']}_{row['issuer_cik_b']}"
        if row["pair_id"] in seen:
            raise ValueError("duplicate_collision_pair_id")
        seen.add(row["pair_id"])
        row["event_date"] = latest_shared_date(row["shared_filing_dates"])
        shared_date_count += len([x for x in row["shared_filing_dates"].split(";") if x.strip()])
    if shared_date_count != 42:
        raise ValueError(f"phase325_shared_date_count_mismatch:{shared_date_count}")
    return rows


class SECClient:
    def __init__(self, email: str, min_interval: float = 0.15):
        if not email or "@" not in email:
            raise ValueError("SEC_CONTACT_EMAIL_secret_required")
        self.ua = f"NuevaEstrategia Smart Money Research (contact: {email})"
        self.min_interval = min_interval
        self.last_request = 0.0
        self.cache: dict[str, tuple[bytes | None, int, str, dict]] = {}

    def get(self, url: str, max_bytes: int = 12_000_000):
        if url in self.cache:
            return self.cache[url]
        for attempt in range(4):
            wait = self.min_interval - (time.monotonic() - self.last_request)
            if wait > 0:
                time.sleep(wait)
            req = Request(url, headers={
                "User-Agent": self.ua,
                "Accept": "application/json, application/xml, text/html, */*",
                "Accept-Encoding": "identity",
            })
            self.last_request = time.monotonic()
            try:
                with urlopen(req, timeout=35) as response:
                    raw = response.read(max_bytes + 1)
                    headers = {k.lower(): v for k, v in response.headers.items()}
                    if len(raw) > max_bytes:
                        result = (None, response.status, "RESPONSE_TOO_LARGE", headers)
                    else:
                        result = (raw, response.status, "", headers)
                    self.cache[url] = result
                    return result
            except HTTPError as exc:
                status = int(exc.code)
                if status in RETRY_STATUS and attempt < 3:
                    time.sleep(0.5 * (2 ** attempt))
                    continue
                result = (None, status, f"HTTP_{status}", {})
                self.cache[url] = result
                return result
            except (URLError, TimeoutError, OSError) as exc:
                if attempt < 3:
                    time.sleep(0.5 * (2 ** attempt))
                    continue
                return (None, 0, f"{type(exc).__name__}:{str(exc)[:160]}", {})
        return (None, 0, "RETRY_EXHAUSTED", {})


def _parallel_rows(obj: dict) -> list[dict]:
    if not isinstance(obj, dict):
        return []
    keys = ("form", "filingDate", "accessionNumber", "primaryDocument", "reportDate")
    arrays = {k: obj.get(k, []) for k in keys}
    n = max((len(v) for v in arrays.values() if isinstance(v, list)), default=0)
    rows = []
    for i in range(n):
        row = {k: (arrays[k][i] if i < len(arrays[k]) else "") for k in keys}
        if row.get("form") and row.get("filingDate") and row.get("accessionNumber"):
            rows.append(row)
    return rows


def _eligible(row: dict, event_date: str) -> bool:
    form = str(row.get("form") or "").upper()
    filed = str(row.get("filingDate") or "")
    try:
        date.fromisoformat(filed)
    except ValueError:
        return False
    return form in ALLOWED_FORMS and filed < event_date


def select_prior_periodic_filing(submissions: dict, event_date: str, client: SECClient | None = None):
    """Select the latest supported periodic filing strictly before event_date.

    If the recent submissions window has no candidate, inspect only older filing
    shards whose filingFrom is not later than the event date.
    """
    recent = submissions.get("filings", {}).get("recent", {})
    candidates = [r for r in _parallel_rows(recent) if _eligible(r, event_date)]
    if candidates:
        return max(candidates, key=lambda r: (r["filingDate"], r["accessionNumber"])), "RECENT"
    if client is None:
        return None, "NO_PRIOR_PERIODIC_FILING_IN_RECENT_WINDOW"
    old_files = submissions.get("filings", {}).get("files", []) or []
    eligible_files = [
        f for f in old_files
        if str(f.get("filingFrom") or "") and str(f.get("filingFrom")) <= event_date
    ]
    for shard in sorted(eligible_files, key=lambda x: str(x.get("filingTo") or ""), reverse=True):
        name = str(shard.get("name") or "")
        if not name:
            continue
        raw, status, err, _ = client.get(f"https://data.sec.gov/submissions/{name}", max_bytes=20_000_000)
        if raw is None:
            continue
        try:
            rows = json.loads(raw).get("filings", {}).get("recent", {})
        except (ValueError, AttributeError):
            continue
        candidates = [r for r in _parallel_rows(rows) if _eligible(r, event_date)]
        if candidates:
            return max(candidates, key=lambda r: (r["filingDate"], r["accessionNumber"])), f"SHARD:{name}"
    return None, "NO_PRIOR_PERIODIC_FILING"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].split(":")[-1]


def parse_instance_xml(raw: bytes) -> list[dict]:
    root = ET.fromstring(raw)
    contexts: dict[str, list[dict]] = {}
    for element in root.iter():
        if local_name(element.tag).lower() != "context":
            continue
        context_id = element.attrib.get("id", "")
        dims = []
        for child in element.iter():
            if local_name(child.tag).lower() == "explicitmember":
                dims.append({
                    "dimension": child.attrib.get("dimension", ""),
                    "member": (child.text or "").strip(),
                })
        if context_id:
            contexts[context_id] = dims
    facts = []
    for element in root.iter():
        name = local_name(element.tag)
        if name not in FACT_NAMES:
            continue
        value = "".join(element.itertext()).strip()
        if not value:
            continue
        context_ref = element.attrib.get("contextRef", "")
        facts.append({
            "name": name,
            "value": value,
            "context_ref": context_ref,
            "dimensions": contexts.get(context_ref, []),
        })
    return facts


class InlineXBRLHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.facts: list[dict] = []
        self.active = None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.active is None and tag.lower() in {"ix:nonnumeric", "ix:nonfraction", "ix:fraction"}:
            self.active = {
                "name": str(attrs.get("name") or "").split(":")[-1],
                "value_parts": [],
                "context_ref": attrs.get("contextref", ""),
                "dimensions": [],
            }
            self.depth = 1
        elif self.active is not None:
            self.depth += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.active is not None:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self.active is not None:
            self.active["value_parts"].append(data)

    def handle_endtag(self, tag):
        if self.active is None:
            return
        self.depth -= 1
        if self.depth <= 0:
            value = html.unescape("".join(self.active.pop("value_parts")).strip())
            if self.active.get("name") in FACT_NAMES and value:
                self.active["value"] = value
                self.facts.append(self.active)
            self.active = None
            self.depth = 0


def parse_inline_html(raw: bytes) -> list[dict]:
    parser = InlineXBRLHTMLParser()
    parser.feed(raw.decode("utf-8", errors="replace"))
    return parser.facts


def choose_instance_file(index: dict, primary_document: str) -> str | None:
    items = index.get("directory", {}).get("item", []) or []
    names = [str(x.get("name") or "") for x in items]
    stem = primary_document.rsplit(".", 1)[0]
    preferred = stem + "_htm.xml"
    if preferred in names:
        return preferred
    for item in items:
        name = str(item.get("name") or "")
        typ = str(item.get("type") or "").upper()
        if name.lower().endswith(".xml") and typ == "EX-101.INS":
            return name
    excluded = ("_CAL.XML", "_DEF.XML", "_LAB.XML", "_PRE.XML", ".XSD")
    candidates = [
        n for n in names
        if n.lower().endswith(".xml") and not n.upper().endswith(excluded)
        and "FILING_SUMMARY" not in n.upper()
    ]
    return sorted(candidates)[0] if len(candidates) == 1 else None


def retrieve_filing_facts(client: SECClient, cik: str, filing: dict):
    accession = str(filing["accessionNumber"])
    accession_compact = accession.replace("-", "")
    cik_path = str(int(cik))
    base = f"https://www.sec.gov/Archives/edgar/data/{cik_path}/{accession_compact}/"
    index_raw, index_status, index_error, _ = client.get(base + "index.json", max_bytes=2_000_000)
    primary = str(filing.get("primaryDocument") or "")
    instance_name = None
    if index_raw:
        try:
            instance_name = choose_instance_file(json.loads(index_raw), primary)
        except (ValueError, AttributeError, TypeError):
            instance_name = None
    if instance_name:
        raw, status, err, _ = client.get(base + instance_name, max_bytes=8_000_000)
        if raw:
            try:
                facts = parse_instance_xml(raw)
                return facts, {
                    "document_status": "XBRL_INSTANCE_PARSED",
                    "document_name": instance_name,
                    "document_sha256": sha256(raw),
                    "document_bytes": len(raw),
                    "document_http_status": status,
                    "index_http_status": index_status,
                    "index_error": index_error,
                }
            except ET.ParseError:
                pass
    if primary:
        raw, status, err, _ = client.get(base + primary, max_bytes=12_000_000)
        if raw:
            facts = parse_inline_html(raw)
            return facts, {
                "document_status": "INLINE_HTML_PARSED" if facts else "PRIMARY_HTML_NO_TARGET_FACTS",
                "document_name": primary,
                "document_sha256": sha256(raw),
                "document_bytes": len(raw),
                "document_http_status": status,
                "index_http_status": index_status,
                "index_error": index_error,
            }
        return [], {
            "document_status": err or "PRIMARY_DOCUMENT_UNAVAILABLE",
            "document_name": primary,
            "document_sha256": "",
            "document_bytes": 0,
            "document_http_status": status,
            "index_http_status": index_status,
            "index_error": index_error,
        }
    return [], {
        "document_status": "NO_PRIMARY_DOCUMENT_OR_INSTANCE",
        "document_name": instance_name or "",
        "document_sha256": "",
        "document_bytes": 0,
        "document_http_status": 0,
        "index_http_status": index_status,
        "index_error": index_error,
    }


def summarize_facts(facts: list[dict], candidate: str) -> dict:
    by_name = Counter(f["name"] for f in facts)
    symbols = sorted({norm_symbol(f["value"]) for f in facts if f["name"] == "TradingSymbol" and norm_symbol(f["value"])})
    no_symbol = any(
        f["name"] == "NoTradingSymbolFlag" and str(f["value"]).strip().lower() in {"true", "1"}
        for f in facts
    )
    titles = sorted({re.sub(r"\s+", " ", f["value"]).strip() for f in facts if f["name"] in {"Security12bTitle", "Security12gTitle"}})
    exchanges = sorted({re.sub(r"\s+", " ", f["value"]).strip() for f in facts if f["name"] == "SecurityExchangeName"})
    class_members = sorted({
        f"{d['dimension']}={d['member']}"
        for f in facts for d in f.get("dimensions", [])
        if "StatementClassOfStockAxis" in d.get("dimension", "") or "ClassesOfShareCapitalAxis" in d.get("dimension", "")
    })
    listing_members = sorted({
        f"{d['dimension']}={d['member']}"
        for f in facts for d in f.get("dimensions", [])
        if "EntityListingsExchangeAxis" in d.get("dimension", "")
    })
    if len(symbols) == 1 and symbols[0] == candidate:
        match = "MATCH_SINGLE_SYMBOL"
    elif candidate in symbols:
        match = "MATCH_AMONG_MULTIPLE_SYMBOLS"
    elif symbols:
        match = "MISMATCH"
    elif no_symbol:
        match = "EXPLICIT_NO_SYMBOL"
    else:
        match = "TRADING_SYMBOL_FACT_MISSING"
    return {
        "fact_counts": dict(sorted(by_name.items())),
        "trading_symbols": symbols,
        "symbol_match_status": match,
        "security_titles": titles,
        "security_exchanges": exchanges,
        "class_axis_members": class_members,
        "listing_axis_members": listing_members,
        "has_security_title_fact": bool(titles),
        "has_class_axis": bool(class_members),
        "has_listing_axis": bool(listing_members),
        "has_trading_symbol_fact": bool(symbols) or no_symbol,
    }


def audit_observation(client: SECClient, pair: dict, side: str) -> dict:
    suffix = side.lower()
    cik = pair[f"issuer_cik_{suffix}"]
    name = pair[f"issuer_name_{suffix}"]
    event_date = pair["event_date"]
    submissions_url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    raw, status, err, _ = client.get(submissions_url, max_bytes=20_000_000)
    base = {
        "pair_id": pair["pair_id"], "ticker_candidate": pair["ticker_candidate"],
        "side": side, "issuer_cik": cik, "issuer_name": name,
        "event_date": event_date, "submissions_http_status": status,
        "submissions_status": "OK" if raw else (err or "UNAVAILABLE"),
        "selected_filing_accession": "", "selected_filing_form": "",
        "selected_filing_date": "", "selected_report_date": "",
        "filing_age_calendar_days": None, "selection_source": "",
    }
    if not raw:
        return {**base, "document_status": "NO_SUBMISSIONS_JSON", "symbol_match_status": "NOT_TESTED"}
    try:
        submissions = json.loads(raw)
    except ValueError:
        return {**base, "document_status": "SUBMISSIONS_JSON_PARSE_ERROR", "symbol_match_status": "NOT_TESTED"}
    filing, source = select_prior_periodic_filing(submissions, event_date, client)
    if not filing:
        return {**base, "document_status": source, "symbol_match_status": "NOT_TESTED"}
    age = (parse_event_date(event_date) - parse_event_date(filing["filingDate"])).days
    if age <= 0:
        raise ValueError("lookahead_or_same_day_periodic_filing_selected")
    facts, doc = retrieve_filing_facts(client, cik, filing)
    fact_summary = summarize_facts(facts, pair["ticker_candidate"])
    return {
        **base,
        "selected_filing_accession": filing["accessionNumber"],
        "selected_filing_form": filing["form"],
        "selected_filing_date": filing["filingDate"],
        "selected_report_date": filing.get("reportDate", ""),
        "filing_age_calendar_days": age,
        "selection_source": source,
        **doc,
        **fact_summary,
        "filing_date_strictly_before_event_date": True,
        "ticker_is_permanent_security_key": False,
        "security_title_is_permanent_security_key": False,
    }


def pair_summaries(pairs: list[dict], observations: list[dict]) -> list[dict]:
    by_key = {(r["pair_id"], r["side"]): r for r in observations}
    out = []
    for p in pairs:
        a = by_key[(p["pair_id"], "A")]
        b = by_key[(p["pair_id"], "B")]
        a_ok = a.get("symbol_match_status") in {"MATCH_SINGLE_SYMBOL", "MATCH_AMONG_MULTIPLE_SYMBOLS"}
        b_ok = b.get("symbol_match_status") in {"MATCH_SINGLE_SYMBOL", "MATCH_AMONG_MULTIPLE_SYMBOLS"}
        out.append({
            "pair_id": p["pair_id"], "ticker_candidate": p["ticker_candidate"],
            "event_date": p["event_date"],
            "issuer_cik_a": p["issuer_cik_a"], "issuer_name_a": p["issuer_name_a"],
            "issuer_cik_b": p["issuer_cik_b"], "issuer_name_b": p["issuer_name_b"],
            "side_a_symbol_status": a.get("symbol_match_status", ""),
            "side_b_symbol_status": b.get("symbol_match_status", ""),
            "both_sides_report_candidate_symbol": bool(a_ok and b_ok),
            "same_symbol_does_not_prove_same_security": True,
            "pair_is_security_identity_adjudicated": False,
        })
    return out


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                if isinstance(v, (dict, list)) else v
                for k, v in row.items()
            })


def run(input_zip: Path, outdir: Path, email: str) -> dict:
    pairs = load_collision_pairs(input_zip)
    client = SECClient(email)
    observations = []
    for n, pair in enumerate(pairs, 1):
        for side in ("A", "B"):
            observations.append(audit_observation(client, pair, side))
        if n % 5 == 0:
            print(f"PHASE328_PAIR_PROGRESS={n}/{len(pairs)}")
    pair_rows = pair_summaries(pairs, observations)
    counts = Counter(r.get("symbol_match_status", "UNKNOWN") for r in observations)
    docs = [r for r in observations if r.get("document_sha256")]
    periodic = [r for r in observations if r.get("selected_filing_accession")]
    ages = sorted(r["filing_age_calendar_days"] for r in periodic if isinstance(r.get("filing_age_calendar_days"), int))
    summary = {
        "collision_pairs": len(pairs),
        "issuer_date_observations": len(observations),
        "submissions_json_success": sum(r["submissions_status"] == "OK" for r in observations),
        "pre_event_periodic_filing_found": len(periodic),
        "source_document_retrieved": len(docs),
        "xbrl_symbol_status_counts": dict(sorted(counts.items())),
        "trading_symbol_fact_present": sum(bool(r.get("trading_symbols")) for r in observations),
        "unambiguous_single_symbol_match": counts["MATCH_SINGLE_SYMBOL"],
        "candidate_match_among_multiple_symbols": counts["MATCH_AMONG_MULTIPLE_SYMBOLS"],
        "symbol_mismatch": counts["MISMATCH"],
        "security_title_fact_present": sum(bool(r.get("has_security_title_fact")) for r in observations),
        "class_axis_present": sum(bool(r.get("has_class_axis")) for r in observations),
        "listing_axis_present": sum(bool(r.get("has_listing_axis")) for r in observations),
        "median_periodic_filing_age_days": ages[len(ages)//2] if ages else None,
        "pairs_both_sides_report_candidate_symbol": sum(r["both_sides_report_candidate_symbol"] for r in pair_rows),
        "source_documents_sha256d": len({r["document_sha256"] for r in docs}),
    }
    controls = {
        "f80_frozen": True, "strict_pit_admitted": False,
        "identity_crosswalk_admitted": False, "universe_coverage_admitted": False,
        "alpha_test_authorized": False, "return_test_run": False,
        "bootstrap_loo_run": False, "chronological_oos_run": False,
        "holdout_used": False, "production_changed": False,
        "universe_changed": False, "capital_changed": False,
        "parameters_changed": False, "raw_sec_bytes_uploaded": False,
        "vendor_contacted": False, "data_purchased": False, "email_sent": False,
        "ticker_only_join_used": False, "same_day_periodic_filing_used": False,
        "later_filing_used": False,
    }
    result = {
        "phase": PHASE,
        "status": "COMPLETED_IDENTITY_COVERAGE_PILOT",
        "generated_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "source": {
            "provider": "U.S. Securities and Exchange Commission",
            "phase325_run_id": 43196055022,
            "phase325_artifact_id": PHASE325_ARTIFACT_ID,
            "phase325_artifact_sha256": PHASE325_ARTIFACT_SHA256,
            "selection": "latest shared collision date per pair; latest supported periodic filing strictly before that date",
            "forms": sorted(ALLOWED_FORMS),
        },
        "summary": summary,
        "observations": observations,
        "pairs": pair_rows,
        "controls": controls,
        "interpretation": {
            "sample_is_purposive_collision_panel_not_universe_prevalence": True,
            "xbrl_fact_absence_means_unknown_not_no_security": True,
            "ticker_match_is_positive_label_evidence_not_permanent_identity": True,
            "security_title_text_is_not_permanent_identifier": True,
            "strict_intraday_first_public_availability_established": False,
            "broad_survivorship_aware_universe_coverage_established": False,
        },
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "phase328_identity_pilot.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(outdir / "phase328_issuer_crosswalk_pilot.csv", observations)
    write_csv(outdir / "phase328_pair_summary.csv", pair_rows)
    quarantine = [r for r in observations if r.get("symbol_match_status") not in {"MATCH_SINGLE_SYMBOL", "MATCH_AMONG_MULTIPLE_SYMBOLS"}]
    write_csv(outdir / "phase328_quarantine.csv", quarantine)
    print("PHASE328_SUMMARY=" + json.dumps(summary, sort_keys=True))
    print("PHASE328_CONTROLS=" + json.dumps(controls, sort_keys=True))
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-zip", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--email", default="")
    a = p.parse_args()
    run(a.input_zip, a.output_dir, a.email)


if __name__ == "__main__":
    main()
