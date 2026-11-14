#!/usr/bin/env python3
"""Prospective CFTC TFF first-receipt capture; historical backfill is never signal-eligible."""
from __future__ import annotations
import argparse,csv,hashlib,json,os,statistics
from datetime import date,datetime,timezone
from decimal import Decimal,InvalidOperation
from pathlib import Path
import requests

DATASET="gpe5-46if"
RESOURCE=f"https://publicreporting.cftc.gov/resource/{DATASET}.json"
META=f"https://publicreporting.cftc.gov/api/views/{DATASET}.json"
DATA_DIR=Path("research/data/cftc_tff_prospective")
STATE_PATH=DATA_DIR/"state.json"
BASELINE_PATH=DATA_DIR/"historical_backfill.csv"
MAX_ROWS=2000
CONTRACTS={
 "13874A":{"label":"E-MINI S&P 500","start":"2010-07-20"},
 "209742":{"label":"NASDAQ-100 STOCK INDEX (MINI)","start":"2010-07-20"},
 "124603":{"label":"DOW JONES INDUSTRIAL AVG - x $5","start":"2010-07-20"},
 "239742":{"label":"RUSSELL E-MINI","start":"2017-08-15"},
}
CATEGORIES={
 "dealer":("dealer_positions_long_all","dealer_positions_short_all","dealer_positions_spread_all"),
 "asset_manager":("asset_mgr_positions_long","asset_mgr_positions_short","asset_mgr_positions_spread"),
 "leveraged_money":("lev_money_positions_long","lev_money_positions_short","lev_money_positions_spread"),
 "other_reportables":("other_rept_positions_long","other_rept_positions_short","other_rept_positions_spread"),
 "non_reportables":("nonrept_positions_long_all","nonrept_positions_short_all",None),
}
FIELDS=list(dict.fromkeys([
 "report_date_as_yyyy_mm_dd","cftc_contract_market_code","contract_market_name",
 "market_and_exchange_names","open_interest_all"
]+[f for group in CATEGORIES.values() for f in group if f]))
CSV_FIELDS=[
 "report_date","contract_code","contract_market_name","market_and_exchange_names","open_interest_all",
 "dealer_net_oi","dealer_spread_oi","asset_manager_net_oi","asset_manager_spread_oi",
 "leveraged_money_net_oi","leveraged_money_spread_oi","other_reportables_net_oi",
 "other_reportables_spread_oi","non_reportables_net_oi","leveraged_money_net_oi_4w_change",
 "leveraged_money_net_oi_z52","asset_manager_net_oi_z52","dealer_net_oi_z52",
 "leveraged_asset_manager_divergence","historical_pit_status","signal_eligible","row_sha256"]

def now_utc():
 return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def day(v):
 if v is None or str(v).strip()=="": raise ValueError("missing report date")
 return date.fromisoformat(str(v).strip()[:10])
def num(v):
 if v is None or str(v).strip() in ("",".","NULL","null"): raise ValueError("missing numeric field")
 try: x=Decimal(str(v).replace(",","").strip())
 except InvalidOperation as e: raise ValueError(f"invalid numeric value {v!r}") from e
 if not x.is_finite(): raise ValueError("non-finite numeric")
 return x
def canonical(row): return {f:row.get(f) for f in FIELDS}
def key(row): return f"{row['cftc_contract_market_code']}|{day(row['report_date_as_yyyy_mm_dd']).isoformat()}"
def digest(row):
 raw=json.dumps(canonical(row),sort_keys=True,separators=(",",":"),ensure_ascii=False)
 return hashlib.sha256(raw.encode()).hexdigest()
def check_oi(row):
 oi=num(row.get("open_interest_all"))
 if oi<=0: raise ValueError("nonpositive open interest")
 long_total=Decimal(0); short_total=Decimal(0)
 for lf,sf,pf in CATEGORIES.values():
  lv,sv=num(row.get(lf)),num(row.get(sf))
  spread=num(row.get(pf)) if pf else Decimal(0)
  long_total+=lv+spread; short_total+=sv+spread
 if long_total!=oi or short_total!=oi:
  raise ValueError(f"OI mismatch: oi={oi} long={long_total} short={short_total}")
 return oi
def fetch_all():
 s=requests.Session(); s.headers.update({"User-Agent":"NuevaEstrategia-Phase384/1.0 CFTC TFF research"})
 mb=s.get(META,timeout=60); mb.raise_for_status(); mb=mb.json()
 all_rows=[]; counts={}
 for code,spec in CONTRACTS.items():
  where=f"cftc_contract_market_code = '{code}' AND report_date_as_yyyy_mm_dd >= '{spec['start']}T00:00:00.000'"
  cp={"$select":"count(*) as n","$where":where}
  a=s.get(RESOURCE,params=cp,timeout=60); a.raise_for_status(); before=int(a.json()[0]["n"])
  params={"$select":",".join(FIELDS),"$where":where,"$order":"report_date_as_yyyy_mm_dd ASC","$limit":MAX_ROWS}
  r=s.get(RESOURCE,params=params,timeout=90); r.raise_for_status(); rows=r.json()
  b=s.get(RESOURCE,params=cp,timeout=60); b.raise_for_status(); after=int(b.json()[0]["n"])
  if before!=len(rows) or after!=len(rows): raise RuntimeError(f"{code} count mismatch {before}/{len(rows)}/{after}")
  counts[code]={"before":before,"retrieved":len(rows),"after":after}
  for row in rows:
   if row.get("cftc_contract_market_code")!=code: raise RuntimeError("unexpected contract code")
   all_rows.append(canonical(row))
 ma=s.get(META,timeout=60); ma.raise_for_status(); ma=ma.json()
 if mb.get("rowsUpdatedAt")!=ma.get("rowsUpdatedAt"): raise RuntimeError("metadata changed during snapshot")
 return all_rows,counts,mb,ma
def features(rows):
 by={}
 for r in rows: by.setdefault(r["cftc_contract_market_code"],[]).append(r)
 out=[]; oi_exact={}; coverage={}
 for code,g in by.items():
  g.sort(key=lambda r:day(r["report_date_as_yyyy_mm_dd"]))
  dates=[day(r["report_date_as_yyyy_mm_dd"]) for r in g]
  keys=[(code,d.isoformat()) for d in dates]
  if len(keys)!=len(set(keys)): raise RuntimeError(f"duplicate natural key {code}")
  for r in g: check_oi(r)
  gaps=[(b-a).days for a,b in zip(dates,dates[1:])]
  oi_exact[code]=len(g)
  coverage[code]={"rows":len(g),"first":dates[0].isoformat(),"last":dates[-1].isoformat(),
                  "max_gap_days":max(gaps) if gaps else None,"gaps_over_8_days":sum(x>8 for x in gaps),
                  "contract_names":sorted({str(r.get("contract_market_name") or "") for r in g}),
                  "exchange_names":sorted({str(r.get("market_and_exchange_names") or "") for r in g})}
  series={c:[] for c in CATEGORIES}
  for i,r in enumerate(g):
   recent_gaps=gaps[max(0,i-4):i]
   weekly_gate=len(recent_gaps)==4 and all(6<=x<=8 for x in recent_gaps)
   semiweekly_gate=len(recent_gaps)==4 and all(2<=x<=5 for x in recent_gaps)
   cadence_regime="WEEKLY" if weekly_gate else ("SEMIWEEKLY" if semiweekly_gate else "IRREGULAR_OR_INSUFFICIENT")
   oi=num(r["open_interest_all"]); vals={}
   for c,(lf,sf,pf) in CATEGORIES.items():
    lv,sv=num(r[lf]),num(r[sf]); sp=num(r[pf]) if pf else Decimal(0)
    vals[c]={"net":float((lv-sv)/oi),"spread":float(sp/oi) if pf else None}
    series[c].append(vals[c]["net"])
   rec={
    "report_date":dates[i].isoformat(),"contract_code":code,
    "contract_market_name":r.get("contract_market_name"),"market_and_exchange_names":r.get("market_and_exchange_names"),
    "open_interest_all":str(oi),
    "dealer_net_oi":vals["dealer"]["net"],"dealer_spread_oi":vals["dealer"]["spread"],
    "asset_manager_net_oi":vals["asset_manager"]["net"],"asset_manager_spread_oi":vals["asset_manager"]["spread"],
    "leveraged_money_net_oi":vals["leveraged_money"]["net"],"leveraged_money_spread_oi":vals["leveraged_money"]["spread"],
    "other_reportables_net_oi":vals["other_reportables"]["net"],"other_reportables_spread_oi":vals["other_reportables"]["spread"],
    "non_reportables_net_oi":vals["non_reportables"]["net"],
    "leveraged_money_net_oi_4w_change":None,"leveraged_money_net_oi_z52":None,
    "asset_manager_net_oi_z52":None,"dealer_net_oi_z52":None,
    "leveraged_asset_manager_divergence":vals["leveraged_money"]["net"]-vals["asset_manager"]["net"],
    "cadence_regime":cadence_regime,"weekly_feature_gate":weekly_gate,
    "historical_pit_status":"UNVERIFIED_ARCHIVE_PROXY","signal_eligible":False,"row_sha256":digest(r)}
   if i>=4:
    w=dates[i-4:i+1]; wg=[(b-a).days for a,b in zip(w,w[1:])]
    if all(6<=x<=8 for x in wg):
     rec["leveraged_money_net_oi_4w_change"]=series["leveraged_money"][i]-series["leveraged_money"][i-4]
   if i>=26:
    start=max(0,i-52); prior_dates=dates[start:i]
    pg=[(b-a).days for a,b in zip(prior_dates,prior_dates[1:])]
    if all(6<=x<=8 for x in pg):
     for c,target in (("leveraged_money","leveraged_money_net_oi_z52"),("asset_manager","asset_manager_net_oi_z52"),("dealer","dealer_net_oi_z52")):
      prior=series[c][start:i]
      if len(prior)>=26:
       sd=statistics.pstdev(prior)
       if sd>0: rec[target]=(series[c][i]-statistics.mean(prior))/sd
   out.append(rec)
 out.sort(key=lambda x:(x["contract_code"],x["report_date"]))
 return out,oi_exact,coverage
def read_state(): return json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else None
def write_json(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
def write_csv(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open("w",newline="",encoding="utf-8") as h:
  w=csv.DictWriter(h,fieldnames=CSV_FIELDS,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
def classify(mode,old_hash,new_hash,report_date,latest_date):
 if old_hash is None:
  if latest_date is None or report_date>latest_date: return ("new_report",mode=="schedule")
  return ("late_arrival",False)
 if old_hash!=new_hash: return ("revision",False)
 return None

def classify_batch(rows,old_hashes,latest_report_date_by_code):
 """Treat one API snapshot as atomic; only the newest new report per contract is eligible."""
 newest_new={}
 for r in rows:
  k=key(r); code=r["cftc_contract_market_code"]
  rd=day(r["report_date_as_yyyy_mm_dd"]).isoformat()
  if old_hashes.get(k) is None and rd>latest_report_date_by_code.get(code,"0001-01-01"):
   if rd>newest_new.get(code,"0001-01-01"): newest_new[code]=rd
 decisions={}
 for r in rows:
  k=key(r); code=r["cftc_contract_market_code"]
  rd=day(r["report_date_as_yyyy_mm_dd"]).isoformat()
  old_hash=old_hashes.get(k); new_hash=digest(r)
  if old_hash is None and code in newest_new and rd>latest_report_date_by_code.get(code,"0001-01-01"):
   if rd==newest_new[code]: decision=("new_report",True)
   else: decision=("same_batch_catchup",False)
  else:
   decision=classify("schedule",old_hash,new_hash,rd,latest_report_date_by_code.get(code))
  if decision is not None: decisions[k]=decision
 return decisions

def build_event_record(row,event_type,first_seen_utc,research_observation_eligible,
                       previous_row_sha256,current_row_sha256):
 """Persist raw source fields only; downstream features must use prospective events only."""
 return {
  "event_type":event_type,
  "contract_code":row["cftc_contract_market_code"],
  "report_date":day(row["report_date_as_yyyy_mm_dd"]).isoformat(),
  "first_seen_utc":first_seen_utc,
  "earliest_research_use_session":"first regular equity session after first_seen_utc",
  "research_observation_eligible":bool(research_observation_eligible),
  "signal_eligible":False,
  "trade_signal_generated":False,
  "previous_row_sha256":previous_row_sha256,
  "current_row_sha256":current_row_sha256,
  "source_row":canonical(row),
  "historical_backfill_derived_features_included":False,
  "feature_engineering_policy":"RECOMPUTE_FROM_PROSPECTIVE_FIRST_SEEN_EVENTS_ONLY",
  "capture_batch_policy":"ONE_ELIGIBLE_LATEST_REPORT_PER_CONTRACT_PER_CAPTURE",
 }
def make_state(rows,mode,stamp,meta_updated):
 hashes={key(r):digest(r) for r in rows}; latest={}
 for r in rows:
  c=r["cftc_contract_market_code"]; d=day(r["report_date_as_yyyy_mm_dd"]).isoformat()
  latest[c]=max(d,latest.get(c,"0001-01-01"))
 return {"schema_version":1,"dataset_id":DATASET,"baseline_created_utc":stamp,"last_capture_utc":stamp,
         "last_capture_mode":mode,"metadata_rows_updated":meta_updated,"row_hashes":hashes,
         "latest_report_date_by_code":latest,"historical_rows_are_signal_eligible":False}
def run(mode,outdir,run_id):
 if mode not in ("push","schedule","manual"): raise ValueError("invalid mode")
 outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
 rows,counts,mb,ma=fetch_all(); feat,oi_exact,cov=features(rows); stamp=now_utc(); meta=ma.get("rowsUpdatedAt")
 summary={"phase":384,"mode":mode,"source":"CFTC TFF Futures Only gpe5-46if","observed_at_utc":stamp,
  "metadata_stable":mb.get("rowsUpdatedAt")==meta,"metadata_rows_updated":meta,"counts_by_code":counts,
  "accounting_exact_rows_by_code":oi_exact,"coverage_by_code":cov,"total_rows":len(rows),
  "natural_key_unique":len({key(r) for r in rows})==len(rows),"historical_backfill_signal_eligible":False,
  "scheduled_new_rows_research_observation_eligible_only_after_first_receipt":True,"trade_signal_generated":False,"revisions_signal_eligible":False,
  "cadence_policy":"4-report and 52-report features require weekly 6-8 day report gaps; semiweekly/irregular cadence suppresses weekly features until a separately pre-registered cadence specification is adopted.",
  "late_arrivals_signal_eligible":False,"forward_returns_used":False,"alpha_test_authorized":False,
  "historical_backfill_derived_features_attached_to_events":False,
  "prospective_feature_engineering_required":True,
  "holdout_used":False,"f80_changed":False,"production_changed":False,"state_write":False,"events_written":0}
 if not summary["natural_key_unique"]: raise RuntimeError("duplicate combined natural keys")
 if mode=="push":
  if STATE_PATH.exists(): summary["disposition"]="BASELINE_ALREADY_EXISTS_NO_OVERWRITE"
  else:
   write_csv(BASELINE_PATH,feat)
   write_json(STATE_PATH,make_state(rows,"branch_push_baseline",stamp,meta))
   write_json(DATA_DIR/"baseline_manifest.json",{"created_utc":stamp,"capture_mode":"branch_push_baseline",
    "row_count":len(rows),"counts_by_code":counts,"historical_availability":"NOT_CERTIFIED; feature warm-up only",
    "signal_eligible":False})
   summary["state_write"]=True; summary["disposition"]="HISTORICAL_BACKFILL_BASELINE_CREATED_NOT_SIGNAL_ELIGIBLE"
 elif mode=="manual":
  summary["disposition"]="MANUAL_DIAGNOSTIC_ONLY_NO_STATE_CHANGE"
 else:
  state=read_state()
  if state is None: raise RuntimeError("baseline missing; scheduled capture cannot initialize silently")
  old=state.get("row_hashes",{}); latest=state.get("latest_report_date_by_code",{})
  events=[]; new_hashes=dict(old); new_latest=dict(latest)
  batch_decisions=classify_batch(rows,old,latest)
  for r in rows:
   k=key(r); code=r["cftc_contract_market_code"]; rd=day(r["report_date_as_yyyy_mm_dd"]).isoformat(); h=digest(r)
   c=batch_decisions.get(k)
   if c is None: continue
   kind,eligible=c
   events.append(build_event_record(
    r,kind,stamp,eligible,old.get(k),h
   ))
   new_hashes[k]=h
   if rd>new_latest.get(code,"0001-01-01"): new_latest[code]=rd
  if events:
   safe=stamp.replace(":","").replace("-","")
   write_json(DATA_DIR/"events"/f"{safe}_run{run_id}.json",{"schema_version":1,"capture_mode":"scheduled","capture_run_id":str(run_id),"capture_batch_policy":"ONE_ELIGIBLE_LATEST_REPORT_PER_CONTRACT_PER_CAPTURE","observed_at_utc":stamp,"dataset_id":DATASET,"events":events})
   state["row_hashes"]=new_hashes; state["latest_report_date_by_code"]=new_latest
   state["last_capture_utc"]=stamp; state["last_capture_mode"]="scheduled"; state["metadata_rows_updated"]=meta
   write_json(STATE_PATH,state); summary["state_write"]=True; summary["events_written"]=len(events)
   summary["eligible_new_reports"]=sum(1 for e in events if e["event_type"]=="new_report" and e["research_observation_eligible"])
   summary["same_batch_catchup_events"]=sum(1 for e in events if e["event_type"]=="same_batch_catchup")
   summary["revisions_or_late_arrivals"]=sum(1 for e in events if e["event_type"] in ("revision","late_arrival"))
   summary["disposition"]="APPEND_ONLY_PROSPECTIVE_EVENTS_RECORDED"
  else: summary["disposition"]="NO_NEW_REPORTS_OR_REVISIONS_NO_STATE_CHANGE"
 write_json(outdir/"summary.json",summary)
 print("PHASE384_CFTC_TFF_PROSPECTIVE_CAPTURE=",summary["disposition"])
 print("TOTAL_ROWS=",len(rows)); print("COUNTS_BY_CODE=",json.dumps(counts,sort_keys=True))
 print("SIGNAL_ELIGIBLE_HISTORICAL_ROWS=0"); print("ALPHA_TEST=NOT_AUTHORIZED")
 return summary
def main():
 p=argparse.ArgumentParser(); p.add_argument("--mode",choices=("push","schedule","manual"),required=True)
 p.add_argument("--output",default="phase384_output"); p.add_argument("--run-id",default=os.environ.get("GITHUB_RUN_ID","local"))
 a=p.parse_args(); run(a.mode,a.output,a.run_id)
if __name__=="__main__": main()
