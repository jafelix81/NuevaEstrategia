import unittest,statistics
from datetime import date,timedelta
from decimal import Decimal
from phase384_cftc_tff_prospective_capture import CATEGORIES,classify,classify_batch,features,digest,check_oi,num,canonical,build_event_record,key

def make_row(d,lev,am=0,dealer=None,oi=1000):
 r={"report_date_as_yyyy_mm_dd":d.isoformat()+"T00:00:00.000","cftc_contract_market_code":"13874A",
    "contract_market_name":"E-MINI S&P 500","market_and_exchange_names":"E-MINI S&P 500 - CME","open_interest_all":str(oi)}
 if dealer is None: dealer=-lev-am
 nets={"dealer":dealer,"asset_manager":am,"leveraged_money":lev,"other_reportables":0,"non_reportables":0}
 base=oi//5
 for c,(lf,sf,pf) in CATEGORIES.items():
  n=nets[c]; r[lf]=str(base+n//2); r[sf]=str(base-n//2)
  if pf:r[pf]="0"
 return r

class Tests(unittest.TestCase):
 def test_numeric_validation(self):
  with self.assertRaises(ValueError): num(None)
  with self.assertRaises(ValueError): num("NaN")
 def test_oi_accounting(self):
  self.assertEqual(check_oi(make_row(date(2026,1,6),100,40)),Decimal("1000"))
 def test_hash_detects_revision(self):
  r=make_row(date(2026,1,6),100); q=dict(r); q["lev_money_positions_long"]=str(int(q["lev_money_positions_long"])+1)
  self.assertNotEqual(digest(r),digest(q))
 def test_scheduled_new_report(self):
  self.assertEqual(classify("schedule",None,"new","2026-01-13","2026-01-06"),("new_report",True))
 def test_late_arrival_not_backdated(self):
  self.assertEqual(classify("schedule",None,"new","2025-12-30","2026-01-06"),("late_arrival",False))
 def test_revision_not_eligible(self):
  self.assertEqual(classify("schedule","old","new","2026-01-06","2026-01-06"),("revision",False))
 def test_manual_not_eligible(self):
  self.assertEqual(classify("manual",None,"new","2026-01-13","2026-01-06"),("new_report",False))
 def test_unchanged_no_event(self):
  self.assertIsNone(classify("schedule","same","same","2026-01-06","2026-01-06"))
 def test_prospective_event_contains_raw_source_only(self):
  row=make_row(date(2026,1,13),100,am=40)
  event=build_event_record(row,"new_report","2026-01-13T22:15:00Z",True,None,digest(row))
  self.assertEqual(event["source_row"],canonical(row))
  self.assertNotIn("derived_features",event)
  self.assertNotIn("observed_cadence_regime",event)
  self.assertNotIn("weekly_feature_gate",event)
  self.assertFalse(event["historical_backfill_derived_features_included"])
  self.assertEqual(event["feature_engineering_policy"],"RECOMPUTE_FROM_PROSPECTIVE_FIRST_SEEN_EVENTS_ONLY")
  self.assertTrue(event["research_observation_eligible"])
  self.assertFalse(event["signal_eligible"])
  self.assertFalse(event["trade_signal_generated"])
 def test_revision_event_is_never_research_observation_eligible(self):
  row=make_row(date(2026,1,6),100)
  event=build_event_record(row,"revision","2026-01-13T22:15:00Z",False,"old",digest(row))
  self.assertFalse(event["research_observation_eligible"])
  self.assertFalse(event["signal_eligible"])
 def test_zscore_uses_prior_rows_only(self):
  rows=[make_row(date(2024,1,2)+timedelta(days=7*i),10+2*i) for i in range(54)]
  f,_,_=features(rows); prior=[(10+2*i)/1000 for i in range(1,53)]
  expected=(f[-1]["leveraged_money_net_oi"]-statistics.mean(prior))/statistics.pstdev(prior)
  self.assertAlmostEqual(f[-1]["leveraged_money_net_oi_z52"],expected,places=10)
 def test_four_report_change_requires_continuity(self):
  ds=[date(2026,1,6),date(2026,1,13),date(2026,1,20),date(2026,1,27),date(2026,2,10)]
  f,_,_=features([make_row(d,100+10*i) for i,d in enumerate(ds)])
  self.assertIsNone(f[-1]["leveraged_money_net_oi_4w_change"])
 def test_semiweekly_cadence_suppresses_weekly_features(self):
  rows=[make_row(date(2026,1,6)+timedelta(days=3*i),10+2*i) for i in range(54)]
  f,_,_=features(rows)
  self.assertEqual(f[-1]["cadence_regime"],"SEMIWEEKLY")
  self.assertFalse(f[-1]["weekly_feature_gate"])
  self.assertIsNone(f[-1]["leveraged_money_net_oi_4w_change"])
  self.assertIsNone(f[-1]["leveraged_money_net_oi_z52"])

 def test_atomic_batch_only_latest_new_report_per_contract_is_eligible(self):
  rows=[make_row(date(2026,1,13),100),make_row(date(2026,1,15),120)]
  latest={"13874A":"2026-01-06"}
  decisions=classify_batch(rows,{},latest)
  self.assertEqual(decisions[key(rows[0])],("same_batch_catchup",False))
  self.assertEqual(decisions[key(rows[1])],("new_report",True))
  self.assertEqual(decisions,classify_batch(list(reversed(rows)),{},latest))
 def test_atomic_batch_keeps_contracts_independent(self):
  a=make_row(date(2026,1,13),100)
  b=make_row(date(2026,1,13),120); b["cftc_contract_market_code"]="209742"
  decisions=classify_batch([a,b],{},{"13874A":"2026-01-06","209742":"2026-01-06"})
  self.assertEqual(decisions[key(a)],("new_report",True))
  self.assertEqual(decisions[key(b)],("new_report",True))
 def test_atomic_batch_revisions_and_older_late_arrivals_stay_ineligible(self):
  prior=make_row(date(2026,1,6),100)
  revised=dict(prior); revised["lev_money_positions_long"]=str(int(revised["lev_money_positions_long"])+1)
  late=make_row(date(2025,12,30),80)
  decisions=classify_batch([revised,late],{key(prior):digest(prior)},{"13874A":"2026-01-06"})
  self.assertEqual(decisions[key(revised)],("revision",False))
  self.assertEqual(decisions[key(late)],("late_arrival",False))

if __name__=="__main__": unittest.main()
