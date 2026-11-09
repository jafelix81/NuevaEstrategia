#!/usr/bin/env python3
"""Phase 149: current OpenFIGI CUSIP mapping and 8-character fallback feasibility.

This is an identity-mapping audit only. It does not infer historical ticker validity,
listing status, issuer CIK, or point-in-time security membership from current mappings.
"""
from __future__ import annotations
import argparse, hashlib, json, time, urllib.error, urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

API_URL = "https://api.openfigi.com/v3/mapping"
DOCS_URL = "https://www.openfigi.com/api/documentation"
INPUT_SHA256 = "5c97aced36060bb89dafb57ba8e07f3487865ec5c5d6ce064aa285d50f3b90fb"
EXPECTED_CUSIPS = 553
MAX_JOBS = 10
MIN_DELAY = 2.5
RETRYABLE = {429, 500, 502, 503, 504}
VALUES = {str(i): i for i in range(10)}
VALUES.update({chr(65+i): 10+i for i in range(26)})
VALUES.update({"*": 36, "@": 37, "#": 38})

def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def valid_cusip(value):
    value = str(value).strip().upper()
    if len(value) != 9 or value[0] not in VALUES:
        return False
    total = 0
    for i, char in enumerate(value[:8]):
        digit = VALUES.get(char)
        if digit is None:
            return False
        if i % 2:
            digit *= 2
        total += digit // 10 + digit % 10
    return value[8].isdigit() and (10-total%10)%10 == int(value[8])

def load_cusips(path):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != INPUT_SHA256:
        raise ValueError(f"Input SHA-256 mismatch: {digest}")
    values = json.loads(raw.decode("utf-8"))
    if not isinstance(values, list):
        raise ValueError("Input must be a JSON array")
    cusips = [str(x).strip().upper() for x in values]
    if len(cusips) != EXPECTED_CUSIPS or len(set(cusips)) != EXPECTED_CUSIPS:
        raise ValueError("Expected exactly 553 unique CUSIPs")
    invalid = [x for x in cusips if not valid_cusip(x)]
    if invalid:
        raise ValueError(f"Invalid CUSIP check digits: {invalid[:5]}")
    return cusips

def now_utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def post_mapping(jobs, opener=urllib.request.urlopen, sleeper=time.sleep, max_attempts=4):
    body = json.dumps(jobs, separators=(",", ":")).encode()
    for attempt in range(max_attempts):
        started = now_utc()
        req = urllib.request.Request(API_URL, data=body, method="POST", headers={
            "Content-Type": "application/json", "Accept": "application/json",
            "User-Agent": "NuevaEstrategia-Phase149-CUSIP-identity-feasibility"})
        try:
            with opener(req, timeout=30) as response:
                status, raw, headers = int(getattr(response, "status", 200)), response.read(), getattr(response, "headers", {})
        except urllib.error.HTTPError as exc:
            status, raw, headers = exc.code, exc.read(), exc.headers
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt + 1 < max_attempts:
                sleeper(float(2 ** (attempt+1)))
                continue
            raise RuntimeError(f"OpenFIGI network error: {exc}") from exc
        received = now_utc()
        if status in RETRYABLE and attempt + 1 < max_attempts:
            try:
                delay = max(1.0, float(headers.get("Retry-After")))
            except (TypeError, ValueError, AttributeError):
                delay = float(2 ** (attempt+1))
            sleeper(delay)
            continue
        if status != 200:
            raise RuntimeError(f"OpenFIGI HTTP {status}: {raw[:500].decode('utf-8', errors='replace')}")
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("OpenFIGI returned non-JSON") from exc
        if not isinstance(decoded, list) or len(decoded) != len(jobs):
            raise RuntimeError("Response count does not match request jobs")
        rate = {}
        for key in ("ratelimit-limit", "ratelimit-remaining", "ratelimit-reset", "retry-after"):
            try:
                value = headers.get(key)
            except AttributeError:
                value = None
            if value is not None:
                rate[key] = str(value)
        return {"status_code": status, "attempts": attempt+1, "started_at_utc": started,
                "received_at_utc": received, "response_sha256": hashlib.sha256(raw).hexdigest(),
                "rate_limit_headers": rate, "response": decoded}
    raise RuntimeError("OpenFIGI retries exhausted")

def classify_matches(matches):
    share_classes = sorted({str(x["shareClassFIGI"]) for x in matches if x.get("shareClassFIGI")})
    composites = sorted({str(x["compositeFIGI"]) for x in matches if x.get("compositeFIGI")})
    figis = sorted({str(x["figi"]) for x in matches if x.get("figi")})
    # Prefer shareClassFIGI: many venue FIGIs can represent one share class.
    if len(share_classes) == 1:
        status, level = "MAPPED_ONE_SHARE_CLASS", "shareClassFIGI"
    elif len(share_classes) > 1:
        status, level = "MAPPED_MULTIPLE_SHARE_CLASSES", "shareClassFIGI"
    elif len(composites) == 1:
        status, level = "MAPPED_ONE_COMPOSITE_ONLY", "compositeFIGI"
    elif len(composites) > 1:
        status, level = "MAPPED_MULTIPLE_COMPOSITES_ONLY", "compositeFIGI"
    elif len(figis) == 1:
        status, level = "MAPPED_ONE_FIGI_ONLY", "figi"
    elif len(figis) > 1:
        status, level = "MAPPED_MULTIPLE_FIGIS_ONLY", "figi"
    else:
        status, level = "MAPPED_WITHOUT_STABLE_ID", None
    return status, level, share_classes, composites, figis

def summarize(cusip, item, id_type):
    if not isinstance(item, dict):
        raise ValueError("Mapping response item must be an object")
    if item.get("error"):
        return {"cusip": cusip, "id_type": id_type, "status": "API_ERROR", "error": str(item["error"]), "matches": []}
    if item.get("warning"):
        return {"cusip": cusip, "id_type": id_type, "status": "NO_MATCH", "warning": str(item["warning"]), "matches": []}
    fields = ("figi","ticker","name","exchCode","marketSector","securityType","securityType2",
              "shareClassFIGI","compositeFIGI","securityDescription")
    matches = [{k: row.get(k) for k in fields} for row in (item.get("data") or []) if isinstance(row, dict)]
    if not matches:
        return {"cusip": cusip, "id_type": id_type, "status": "NO_MATCH", "matches": []}
    status, level, share_classes, composites, figis = classify_matches(matches)
    tickers = sorted({str(x["ticker"]) for x in matches if x.get("ticker")})
    names = sorted({str(x["name"]) for x in matches if x.get("name")})
    sectors = sorted({str(x["marketSector"]) for x in matches if x.get("marketSector")})
    types = sorted({str(x.get("securityType2") or x.get("securityType")) for x in matches if x.get("securityType2") or x.get("securityType")})
    common = any(str(x.get("securityType2") or x.get("securityType") or "").casefold()=="common stock" for x in matches)
    equity = any(str(x.get("marketSector") or "").casefold()=="equity" for x in matches)
    preferred = any(str(x.get("marketSector") or "").casefold()=="pfd" or str(x.get("securityType2") or x.get("securityType") or "").casefold()=="preferred stock" for x in matches)
    muni = any(str(x.get("marketSector") or "").casefold()=="muni" for x in matches)
    return {"cusip":cusip,"id_type":id_type,"status":status,"identity_level":level,
        "share_class_count":len(share_classes),"composite_count":len(composites),"figi_count":len(figis),
        "rows_missing_share_class_figi":sum(not bool(x.get("shareClassFIGI")) for x in matches),
        "share_class_figis":share_classes,"composite_figis":composites,"figis":figis,
        "tickers":tickers,"names":names,"market_sectors":sectors,"security_types":types,
        "has_equity_match":equity,"has_common_stock_match":common,
        "has_preferred_match":preferred,"has_muni_match":muni,"match_count":len(matches),"matches":matches}

def query_batches(values, id_type, post_func, sleeper, delay_seconds, pass_name):
    results, logs = [], []
    batches = [values[i:i+MAX_JOBS] for i in range(0,len(values),MAX_JOBS)]
    for i,batch in enumerate(batches):
        jobs = [{"idType":id_type,"idValue":value,"includeUnlistedEquities":True} for value in batch]
        response = post_func(jobs)
        logs.append({"pass":pass_name,"batch_number":i+1,"jobs":len(jobs),"status_code":response["status_code"],
            "attempts":response["attempts"],"started_at_utc":response["started_at_utc"],
            "received_at_utc":response["received_at_utc"],"response_sha256":response["response_sha256"],
            "rate_limit_headers":response.get("rate_limit_headers",{})})
        results.extend(summarize(value,item,id_type) for value,item in zip(batch,response["response"]))
        if i+1 < len(batches):
            sleeper(delay_seconds)
    return results, logs

def build_cross_cusip_links(results):
    index = defaultdict(set)
    for row in results:
        for share_class in row.get("share_class_figis",[]):
            index[share_class].add(row["cusip"])
    return [{"shareClassFIGI":key,"cusips":sorted(values)} for key,values in sorted(index.items()) if len(values)>1]

def run_audit(input_path, output_dir, post_func=post_mapping, sleeper=time.sleep, delay_seconds=MIN_DELAY):
    cusips = load_cusips(input_path)
    if delay_seconds < MIN_DELAY:
        raise ValueError("Delay must be at least 2.5 seconds to respect the unauthenticated rate limit")
    primary, primary_logs = query_batches(cusips,"ID_CUSIP",post_func,sleeper,delay_seconds,"primary_9_char")
    no_match = [x["cusip"] for x in primary if x["status"]=="NO_MATCH"]
    fallback_values = sorted({x[:8] for x in no_match})
    fallback_raw, fallback_logs = query_batches(fallback_values,"ID_CUSIP_8_CHR",post_func,sleeper,delay_seconds,"fallback_8_char") if fallback_values else ([],[])
    fallback_by_value = {x["cusip"]:x for x in fallback_raw}
    fallback = []
    for row in primary:
        if row["status"] != "NO_MATCH":
            continue
        value = row["cusip"][:8]
        fb = dict(fallback_by_value[value])
        fb["original_cusip"] = row["cusip"]
        fb["fallback_id_value"] = value
        fallback.append(fb)
    fallback_unique = {"MAPPED_ONE_SHARE_CLASS","MAPPED_ONE_COMPOSITE_ONLY","MAPPED_ONE_FIGI_ONLY"}
    recovered = [x for x in fallback if x["status"] in fallback_unique]
    counts, fb_counts = defaultdict(int), defaultdict(int)
    for row in primary: counts[row["status"]] += 1
    for row in fallback: fb_counts[row["status"]] += 1
    cross_links = build_cross_cusip_links(primary)
    summary = {
        "input_cusips":len(cusips),"primary_mapped_any":sum(x["status"].startswith("MAPPED") for x in primary),
        "primary_no_match":counts["NO_MATCH"],"primary_api_errors":counts["API_ERROR"],
        "primary_one_share_class":counts["MAPPED_ONE_SHARE_CLASS"],
        "primary_multiple_share_classes":counts["MAPPED_MULTIPLE_SHARE_CLASSES"],
        "primary_one_composite_only":counts["MAPPED_ONE_COMPOSITE_ONLY"],
        "primary_multiple_composites_only":counts["MAPPED_MULTIPLE_COMPOSITES_ONLY"],
        "primary_one_figi_only":counts["MAPPED_ONE_FIGI_ONLY"],
        "primary_multiple_figis_only":counts["MAPPED_MULTIPLE_FIGIS_ONLY"],
        "primary_without_stable_id":counts["MAPPED_WITHOUT_STABLE_ID"],
        "primary_equity_matches":sum(bool(x.get("has_equity_match")) for x in primary),
        "primary_common_stock_matches":sum(bool(x.get("has_common_stock_match")) for x in primary),
        "primary_preferred_matches":sum(bool(x.get("has_preferred_match")) for x in primary),
        "primary_muni_matches":sum(bool(x.get("has_muni_match")) for x in primary),
        "fallback_attempted":len(fallback),"fallback_mapped_any":sum(x["status"].startswith("MAPPED") for x in fallback),
        "fallback_unique_identity_recovered":len(recovered),"fallback_no_match":fb_counts["NO_MATCH"],
        "fallback_api_errors":fb_counts["API_ERROR"],"fallback_multiple_share_classes":fb_counts["MAPPED_MULTIPLE_SHARE_CLASSES"],
        "fallback_multiple_composites_only":fb_counts["MAPPED_MULTIPLE_COMPOSITES_ONLY"],
        "fallback_mixed_or_unstable":sum(x["status"] in {"MAPPED_WITHOUT_STABLE_ID","MAPPED_MULTIPLE_FIGIS_ONLY"} for x in fallback),
        "cross_cusip_shareclass_links":len(cross_links),
        "cusips_in_cross_cusip_shareclass_links":sum(len(x["cusips"]) for x in cross_links),
        "primary_status_counts":dict(sorted(counts.items())),"fallback_status_counts":dict(sorted(fb_counts.items()))}
    output = {"phase":149,"status":"COMPLETED_PRESENT_DAY_OPENFIGI_CUSIP_MAPPING_AUDIT",
        "source":{"provider":"OpenFIGI API v3","api_url":API_URL,"documentation_url":DOCS_URL,
        "retrieved_at_utc":now_utc(),"mapping_mode":"ID_CUSIP with includeUnlistedEquities=true; ID_CUSIP_8_CHR fallback for primary no-match only",
        "api_key_used":False,"unauthenticated_rate_limit_requests_per_minute":25,"max_jobs_per_request":10,
        "minimum_inter_request_delay_seconds":delay_seconds,"input_sha256":sha256_file(input_path),
        "input_cusip_count":len(cusips),"phase124_artifact_id":13436764625,"phase127_artifact_id":13438903901,
        "phase127_artifact_zip_sha256":"b80d15d736ba6c45f4f3c5dd569604175e221414b31a28fd58a62010a805c166",
        "phase127_csv_sha256":"5fc30ba22d4e3ef99113761059a5761f1fd4ae61a6d0e3a69961fe194d739447"},
        "summary":summary,"batch_log":primary_logs+fallback_logs,"primary_results":primary,
        "fallback_results":fallback,"cross_cusip_shareclass_links":cross_links,
        "limitations":["Present-day mapping snapshot, not a PIT CUSIP-to-ticker history.",
        "Documented response fields contain no effective-from/effective-to dates, historical listing-status dates or issuer CIK.",
        "includeUnlistedEquities=true broadens results but does not label which result is currently listed versus delisted.",
        "A current ticker must not be backdated to a filing date; a no-match is not proof the security did not exist.",
        "8-character fallback omits the CUSIP check digit and is a secondary lookup; keep it separate from exact 9-character results.",
        "A stable shareClassFIGI can link multiple CUSIPs ex post, but the API does not date when that relationship became knowable.",
        "The input is a stratified 599-filing 13D/G sample, not a census of the historical equity universe."],
        "decision":"Retain only as a candidate present-day CUSIP-to-FIGI bridge. Primary 9-character mappings may support manual identity review; 8-character fallbacks remain weaker and separate. Neither mapping may be used as a historical ticker or PIT feature until effective-dated security identity, issuer linkage and historical universe membership are independently established."}
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True)
    (output_dir/"phase149_openfigi_cusip_audit.json").write_text(json.dumps(output,indent=2,sort_keys=True),encoding="utf-8")
    return output

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True); p.add_argument("--delay-seconds",type=float,default=MIN_DELAY)
    a=p.parse_args(); result=run_audit(a.input,a.output_dir,delay_seconds=a.delay_seconds)
    print(json.dumps({"phase":149,"summary":result["summary"],"decision":result["decision"]},indent=2))

if __name__=="__main__": main()
