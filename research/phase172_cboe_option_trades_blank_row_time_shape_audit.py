#!/usr/bin/env python3
"""Phase 172: Cboe Option Trades blank-row and time-only shape audit."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, re
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from research.phase170_cboe_option_trades_public_sample_audit import SOURCE_URL, csv_members, schema_check

MAX_DOWNLOAD_BYTES = 100_000_000
CORE_FIELDS = ("underlying_symbol","sequence_number","root","expiration","strike","option_type","exchange_id","trade_size","trade_price","trade_condition_id")
TIME_ONLY_RE = re.compile(r"(?P<hour>\d{2}):(?P<minute>\d{2})\.(?P<digit>\d)")

def _text(value):
    return "" if value is None else str(value).strip()

def _parse_market_date(value):
    raw = _text(value)
    if not raw: return None
    try:
        if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", raw):
            return datetime.strptime(raw,"%m/%d/%Y").date()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            return date.fromisoformat(raw)
    except ValueError:
        return None
    return None

def _filename_date(name):
    base=name.replace("\\","/").rsplit("/",1)[-1]
    m=re.search(r"_(\d{4}-\d{2}-\d{2})\.csv$",base,re.I)
    if not m: return None
    try: return date.fromisoformat(m.group(1))
    except ValueError: return None

def audit_member(member_name,payload):
    reader=csv.DictReader(io.StringIO(payload.decode("utf-8-sig"),newline=""))
    headers=[str(x).strip().lower() for x in (reader.fieldnames or [])]
    schema=schema_check(headers)
    out={"member_basename":member_name.replace("\\","/").rsplit("/",1)[-1],
         "member_sha256":hashlib.sha256(payload).hexdigest(),**schema,
         "row_count":0,"all_columns_blank_rows":0,"all_columns_blank_runs":0,
         "max_all_columns_blank_run":0,"trailing_all_columns_blank_rows":0,
         "all_blank_rows_only_trailing":False,"all_blank_row_pattern":"NOT_EVALUATED",
         "first_nonblank_row_index":None,"last_nonblank_row_index":None,
         "date_time_joint_blankness":{},"both_date_fields_blank_all_columns_blank_rows":0,
         "both_date_fields_blank_any_column_nonblank_rows":0,
         "nonblank_fields_when_both_dates_blank":{},"both_date_fields_blank_core_complete_rows":0,
         "both_date_fields_blank_core_incomplete_rows":0,"market_date_parse_counts":{},
         "market_date_filename_match_rows":0,"market_date_filename_mismatch_rows":0,
         "quote_datetime_shape_signature_counts_top10":[],"quote_datetime_length_counts":{},
         "quote_time_only_shape_rows":0,"quote_time_only_valid_clock_rows":0,
         "quote_time_only_invalid_clock_rows":0,"quote_time_only_hour_minute_min":None,
         "quote_time_only_hour_minute_max":None,"raw_rows_persisted":False,
         "raw_symbols_persisted":False,"raw_contracts_persisted":False,"raw_clock_values_persisted":False}
    if schema["schema_status"]!="PASS": return out

    runs=current=maxrun=allblank=0
    first_nonblank=last_nonblank=first_blank=last_blank=None
    joint=Counter(); nonblank_when_blank=Counter(); md_counts=Counter()
    signatures=Counter(); lengths=Counter()
    filename_day=_filename_date(member_name); fmatch=fmismatch=0
    blank_all=blank_any=core_complete=core_incomplete=0
    time_rows=valid_clock=invalid_clock=0; min_hm=max_hm=None

    for idx,raw in enumerate(reader,1):
        out["row_count"]+=1
        row={str(k).strip().lower():v for k,v in raw.items() if k is not None}
        all_empty=all(not _text(row.get(k)) for k in headers)
        md=_text(row.get("market_date")); qt=_text(row.get("quote_datetime"))
        both_blank=not md and not qt
        joint["both_blank" if both_blank else "market_date_blank_only" if not md else "quote_datetime_blank_only" if not qt else "both_nonblank"]+=1

        if all_empty:
            allblank+=1; current+=1; maxrun=max(maxrun,current)
            if current==1:
                runs+=1
                if first_blank is None: first_blank=idx
            last_blank=idx
        else:
            current=0
            if first_nonblank is None: first_nonblank=idx
            last_nonblank=idx

        if both_blank:
            if all_empty: blank_all+=1
            else:
                blank_any+=1
                for field in headers:
                    if _text(row.get(field)): nonblank_when_blank[field]+=1
            if all(_text(row.get(f)) for f in CORE_FIELDS): core_complete+=1
            else: core_incomplete+=1

        parsed=_parse_market_date(md)
        md_counts["blank" if not md else "parsed" if parsed else "unparsed_or_invalid"]+=1
        if parsed is not None and filename_day is not None:
            if parsed==filename_day: fmatch+=1
            else: fmismatch+=1

        if qt:
            sig="".join("9" if c.isdigit() else "A" if c.isalpha() else c for c in qt)
            signatures[sig]+=1; lengths[str(len(qt))]+=1
            m=TIME_ONLY_RE.fullmatch(qt)
            if m:
                time_rows+=1
                hm=(int(m.group("hour")),int(m.group("minute")))
                if 0<=hm[0]<=23 and 0<=hm[1]<=59:
                    valid_clock+=1
                    min_hm=hm if min_hm is None or hm<min_hm else min_hm
                    max_hm=hm if max_hm is None or hm>max_hm else max_hm
                else: invalid_clock+=1

    trailing=current
    only_trailing=allblank>0 and allblank==trailing
    pattern="NONE" if not allblank else "TRAILING_PADDING_CANDIDATE" if only_trailing else "ONE_CONTIGUOUS_INTERNAL_BLOCK" if runs==1 else "MULTIPLE_OR_INTERSPERSED_RUNS"
    out.update({
      "all_columns_blank_rows":allblank,"all_columns_blank_runs":runs,
      "max_all_columns_blank_run":maxrun,"trailing_all_columns_blank_rows":trailing,
      "all_blank_rows_only_trailing":only_trailing,"all_blank_row_pattern":pattern,
      "first_nonblank_row_index":first_nonblank,"last_nonblank_row_index":last_nonblank,
      "date_time_joint_blankness":dict(sorted(joint.items())),
      "both_date_fields_blank_all_columns_blank_rows":blank_all,
      "both_date_fields_blank_any_column_nonblank_rows":blank_any,
      "nonblank_fields_when_both_dates_blank":dict(sorted(nonblank_when_blank.items())),
      "both_date_fields_blank_core_complete_rows":core_complete,
      "both_date_fields_blank_core_incomplete_rows":core_incomplete,
      "market_date_parse_counts":dict(sorted(md_counts.items())),
      "market_date_filename_match_rows":fmatch,"market_date_filename_mismatch_rows":fmismatch,
      "quote_datetime_shape_signature_counts_top10":[{"signature":k,"count":v} for k,v in sorted(signatures.items(),key=lambda x:(-x[1],x[0]))[:10]],
      "quote_datetime_length_counts":dict(sorted(lengths.items(),key=lambda x:int(x[0]))),
      "quote_time_only_shape_rows":time_rows,"quote_time_only_valid_clock_rows":valid_clock,
      "quote_time_only_invalid_clock_rows":invalid_clock,
      "quote_time_only_hour_minute_min":f"{min_hm[0]:02d}:{min_hm[1]:02d}" if min_hm else None,
      "quote_time_only_hour_minute_max":f"{max_hm[0]:02d}:{max_hm[1]:02d}" if max_hm else None})
    return out

def audit_archive(raw_zip,retrieved_at_utc=None):
    audits=[audit_member(n,p) for n,p in csv_members(raw_zip)]
    return {"phase":172,"source":"Cboe Option Trades","sample_url":SOURCE_URL,
      "archive_sha256":hashlib.sha256(raw_zip).hexdigest(),"compressed_bytes":len(raw_zip),
      "retrieved_at_utc":retrieved_at_utc or datetime.now(timezone.utc).isoformat(),
      "member_count":len(audits),"member_audits":audits,"status":"DIAGNOSTIC_COMPLETE",
      "alpha_admission":False,"strict_pit":False,"raw_archive_persisted":False,
      "raw_rows_persisted":False,"raw_symbols_persisted":False,"raw_contracts_persisted":False,
      "raw_clock_values_persisted":False,"vendor_contact_or_purchase":False,
      "production_change":False,"f80_change":False}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output-dir",default="phase172_output"); args=ap.parse_args()
    req=Request(SOURCE_URL,headers={"User-Agent":"NuevaEstrategia research audit"})
    with urlopen(req,timeout=60) as response: payload=response.read(MAX_DOWNLOAD_BYTES+1)
    if len(payload)>MAX_DOWNLOAD_BYTES: raise ValueError("sample_download_exceeds_limit")
    summary=audit_archive(payload); d=Path(args.output_dir); d.mkdir(parents=True,exist_ok=True)
    p=d/"phase172_cboe_option_trades_blank_row_time_shape_summary.json"
    p.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
