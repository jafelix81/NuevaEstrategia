import unittest
import numpy as np
import pandas as pd
from research.phase259_mom120_incremental_portfolio_economic_audit import (
    audit_ledger_frame, corrected_oos_metrics, circular_block_bootstrap_mean,
    hac_mean, trade_cost_audit,
)

class Phase259EconomicAuditTests(unittest.TestCase):
    def valid_ledger(self):
        dates=pd.to_datetime(["2023-12-28","2023-12-29","2024-01-02","2024-01-03"])
        equity=np.array([1000.,1010.,1000.,1020.])
        ret=np.array([0.,0.01,1000./1010.-1.,1.02])
        cash=np.zeros(4)
        gross_value=equity.copy()
        return pd.DataFrame({"Date":dates,"Equity":equity,"DailyReturn":ret,
                             "Cash":cash,"GrossValue":gross_value,"Positions":[20]*4,"Gross":[1.]*4})

    def test_valid_ledger_passes_accounting(self):
        row, x=audit_ledger_frame(self.valid_ledger())
        self.assertEqual(row["max_positions"],20)
        self.assertLess(row["max_equity_cash_error"],1e-9)

    def test_equity_cash_identity_fails(self):
        x=self.valid_ledger();x.loc[2,"Cash"]=1.
        with self.assertRaises(ValueError):audit_ledger_frame(x)

    def test_sequential_return_identity_fails(self):
        x=self.valid_ledger();x.loc[2,"DailyReturn"]=0.0
        with self.assertRaises(ValueError):audit_ledger_frame(x)

    def test_top_n_limit_fails(self):
        x=self.valid_ledger();x.loc[2,"Positions"]=21
        with self.assertRaises(ValueError):audit_ledger_frame(x)

    def test_gross_cap_fails(self):
        x=self.valid_ledger();x.loc[2,"Gross"]=1.01
        with self.assertRaises(ValueError):audit_ledger_frame(x)

    def test_nonchronological_dates_fail(self):
        x=self.valid_ledger();x.loc[2,"Date"]=pd.Timestamp("2023-12-27")
        with self.assertRaises(ValueError):audit_ledger_frame(x)

    def test_oos_metrics_use_pre_oos_close_base(self):
        x=self.valid_ledger()
        m=corrected_oos_metrics(x)
        self.assertEqual(m["pre_oos_close_date"],"2023-12-29")
        self.assertEqual(m["oos_return_observations"],2)
        self.assertAlmostEqual(m["corrected_final_multiple"],1020/1010)

    def test_report_boundary_multiple_is_distinct(self):
        x=self.valid_ledger()
        m=corrected_oos_metrics(x)
        self.assertNotAlmostEqual(m["corrected_final_multiple"],m["published_multiple_end_over_first_oos_close"])

    def test_bootstrap_is_deterministic(self):
        d=np.linspace(-0.01,0.02,120)
        a=circular_block_bootstrap_mean(d,reps=200,block=10,seed=9)
        b=circular_block_bootstrap_mean(d,reps=200,block=10,seed=9)
        self.assertEqual(a,b)

    def test_bootstrap_reports_block_and_sample(self):
        d=np.random.default_rng(1).normal(0.0001,0.01,150)
        r=circular_block_bootstrap_mean(d,reps=100,block=20,seed=3)
        self.assertEqual(r["reps"],100);self.assertEqual(r["block_length"],20)

    def test_hac_mean_known_constant(self):
        r=hac_mean(np.repeat(0.001,100),max_lag=5)
        self.assertAlmostEqual(r["mean"],0.001)
        self.assertAlmostEqual(r["se"],0.0)

    def test_hac_confidence_interval_contains_mean(self):
        d=np.random.default_rng(2).normal(0.0,0.01,300)
        r=hac_mean(d,20)
        self.assertLessEqual(r["ci95_low"],r["mean"])
        self.assertGreaterEqual(r["ci95_high"],r["mean"])

    def test_trade_cost_identity(self):
        x=pd.DataFrame({"Notional":[1000.,2500.],"Cost":[2.,5.],"Side":["BUY","SELL"],
                        "Date":["2024-01-02","2024-01-03"],"Ticker":["A","B"]})
        r=trade_cost_audit(x,20)
        self.assertAlmostEqual(r["total_cost"],7.0)

    def test_trade_cost_mismatch_fails(self):
        x=pd.DataFrame({"Notional":[1000.],"Cost":[1.],"Side":["BUY"],
                        "Date":["2024-01-02"],"Ticker":["A"]})
        with self.assertRaises(ValueError):trade_cost_audit(x,20)

if __name__=="__main__":
    unittest.main()
