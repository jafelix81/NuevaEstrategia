import unittest
import numpy as np
import pandas as pd

from research.phase372_finra_shortflow_next_open_retest import (
    next_open_forward_return, portfolio_delta_net, matured_exit_date,
)

class Phase372Tests(unittest.TestCase):
    def setUp(self):
        self.calendar = [pd.Timestamp(x) for x in (
            "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05",
            "2024-01-08", "2024-01-09", "2024-01-10",
        )]
        self.index = {d:i for i,d in enumerate(self.calendar)}
        self.prices = pd.DataFrame(
            {"Open":[99,100,102,103,104,105,106],
             "Close":[100,101,102,110,105,106,107]},
            index=self.calendar,
        )

    def test_next_open_entry_and_horizon_close(self):
        # Signal Jan 2; H3 enters Jan 3 open=100 and exits Jan 5 close=110.
        value = next_open_forward_return(self.prices, self.calendar, self.index, "2024-01-02", 3)
        self.assertAlmostEqual(value, 0.10, places=10)

    def test_horizon_uses_next_common_session_not_signal_close(self):
        value = next_open_forward_return(self.prices, self.calendar, self.index, "2024-01-02", 1)
        self.assertAlmostEqual(value, 101/100-1, places=10)

    def test_missing_entry_session_is_not_skipped(self):
        frame = self.prices.drop(pd.Timestamp("2024-01-03"))
        value = next_open_forward_return(frame, self.calendar, self.index, "2024-01-02", 1)
        self.assertTrue(np.isnan(value))

    def test_maturity_date(self):
        self.assertEqual(
            matured_exit_date(self.calendar, self.index, "2024-01-02", 3),
            pd.Timestamp("2024-01-05"),
        )

    def test_incremental_cost_sensitivity(self):
        # 20% sleeve; two one-way legs at 10 bps each => 4 bps portfolio cost.
        net = portfolio_delta_net(0.01, 0.20, 10)
        self.assertAlmostEqual(net, 0.002 - 0.0004, places=12)

if __name__ == "__main__":
    unittest.main()
