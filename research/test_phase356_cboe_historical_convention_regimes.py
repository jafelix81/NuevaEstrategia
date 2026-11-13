import unittest

from research.phase356_cboe_historical_convention_regimes import (
    audit_matrix,
    convention_for,
)


class Phase356ConventionTests(unittest.TestCase):
    def test_c1_open_interest_shift_boundary_inclusive(self):
        self.assertEqual(
            convention_for("C1", "2019-10-04")["open_interest_regime"],
            "SHIFTED_ONE_DAY_AHEAD_VENDOR_DOCUMENTED",
        )
        self.assertEqual(
            convention_for("C1", "2019-10-07")["open_interest_regime"],
            "START_OF_DAY_CONVENTION_VENDOR_DOCUMENTED",
        )

    def test_c2_open_interest_shift_boundary_inclusive(self):
        self.assertEqual(
            convention_for("C2", "2018-05-11")["open_interest_regime"],
            "SHIFTED_ONE_DAY_AHEAD_VENDOR_DOCUMENTED",
        )
        self.assertEqual(
            convention_for("C2", "2018-05-14")["open_interest_regime"],
            "START_OF_DAY_CONVENTION_VENDOR_DOCUMENTED",
        )

    def test_bzx_and_edgx_start_of_day_oi_from_documented_history(self):
        for venue in ("BZX", "EDGX"):
            with self.subTest(venue=venue):
                self.assertEqual(
                    convention_for(venue, "2018-01-02")["open_interest_regime"],
                    "START_OF_DAY_CONVENTION_VENDOR_DOCUMENTED",
                )

    def test_c1_total_exchange_volume_scale_boundary(self):
        self.assertEqual(
            convention_for("C1", "2019-10-04")[
                "total_exchange_volume_normalization_factor_candidate"
            ],
            2.0,
        )
        self.assertEqual(
            convention_for("C1", "2019-10-07")[
                "total_exchange_volume_normalization_factor_candidate"
            ],
            1.0,
        )

    def test_other_venues_have_no_documented_exchange_volume_scale_break(self):
        for venue in ("C2", "BZX", "EDGX"):
            with self.subTest(venue=venue):
                self.assertEqual(
                    convention_for(venue, "2019-10-07")[
                        "total_exchange_volume_normalization_factor_candidate"
                    ],
                    1.0,
                )

    def test_c2_total_industry_volume_scale_boundary(self):
        self.assertEqual(
            convention_for("C2", "2018-05-11")[
                "total_industry_volume_normalization_factor_candidate"
            ],
            0.5,
        )
        self.assertEqual(
            convention_for("C2", "2018-05-14")[
                "total_industry_volume_normalization_factor_candidate"
            ],
            1.0,
        )

    def test_other_venues_have_no_documented_industry_volume_scale_break(self):
        for venue in ("C1", "BZX", "EDGX"):
            with self.subTest(venue=venue):
                self.assertEqual(
                    convention_for(venue, "2018-05-14")[
                        "total_industry_volume_normalization_factor_candidate"
                    ],
                    1.0,
                )

    def test_previous_close_is_venue_only_during_documented_legacy_periods(self):
        self.assertEqual(
            convention_for("C1", "2019-10-04")["previous_close_scope"],
            "VENUE_ONLY_NOT_INDUSTRY_WIDE",
        )
        self.assertEqual(
            convention_for("C1", "2019-10-07")["previous_close_scope"],
            "INDUSTRY_WIDE_VENDOR_DOCUMENTED",
        )
        self.assertEqual(
            convention_for("C2", "2018-05-11")["previous_close_scope"],
            "VENUE_ONLY_NOT_INDUSTRY_WIDE",
        )
        self.assertEqual(
            convention_for("C2", "2018-05-14")["previous_close_scope"],
            "INDUSTRY_WIDE_VENDOR_DOCUMENTED",
        )

    def test_bzx_edgx_previous_close_is_industry_wide(self):
        for venue in ("BZX", "EDGX"):
            with self.subTest(venue=venue):
                self.assertEqual(
                    convention_for(venue, "2018-01-02")["previous_close_scope"],
                    "INDUSTRY_WIDE_VENDOR_DOCUMENTED",
                )

    def test_c1_gth_session_boundary(self):
        self.assertEqual(
            convention_for("C1", "2023-12-08")["session_scope"],
            "RTH_ONLY",
        )
        self.assertEqual(
            convention_for("C1", "2023-12-11")["session_scope"],
            "RTH_PLUS_GLOBAL_TRADING_HOURS",
        )

    def test_non_c1_session_scope_is_rth(self):
        for venue in ("C2", "BZX", "EDGX"):
            with self.subTest(venue=venue):
                self.assertEqual(
                    convention_for(venue, "2024-01-02")["session_scope"],
                    "RTH_ONLY",
                )

    def test_c1_pre_2011_requires_legacy_parser(self):
        self.assertEqual(
            convention_for("C1", "2010-12-31")["format_regime"],
            "LEGACY_PRE_2011_FORMAT_REQUIRES_LEGACY_PARSER",
        )
        self.assertEqual(
            convention_for("C1", "2011-01-03")["format_regime"],
            "POST_2011_FORMAT",
        )

    def test_participant_volume_is_never_scaled_by_total_volume_rule(self):
        for venue, day in (
            ("C1", "2008-01-02"),
            ("C1", "2019-10-04"),
            ("C2", "2018-05-11"),
            ("BZX", "2024-01-02"),
        ):
            with self.subTest(venue=venue, day=day):
                self.assertEqual(
                    convention_for(venue, day)["participant_side_volume_scaling"],
                    "UNVERIFIED_DO_NOT_INFER_FROM_TOTAL_EXCHANGE_VOLUME_RULE",
                )

    def test_no_automatic_transforms_or_pit_admission(self):
        item = convention_for("C1", "2018-03-01")
        self.assertFalse(item["numeric_transforms_applied"])
        self.assertFalse(item["exact_first_receipt_utc_proven"])
        self.assertFalse(item["historical_correction_vintages_proven"])

    def test_documented_history_start_is_enforced(self):
        with self.assertRaises(ValueError):
            convention_for("C1", "2005-01-02")
        for venue in ("C2", "BZX", "EDGX"):
            with self.subTest(venue=venue):
                with self.assertRaises(ValueError):
                    convention_for(venue, "2017-12-29")

    def test_unknown_venue_and_invalid_date_rejected(self):
        with self.assertRaises(ValueError):
            convention_for("MIAX", "2024-01-02")
        with self.assertRaises(ValueError):
            convention_for("C1", "not-a-date")

    def test_matrix_is_policy_only_and_keeps_f80_frozen(self):
        result = audit_matrix()
        self.assertEqual(
            result["status"],
            "DOCUMENTED_POLICY_MATRIX_ONLY_NOT_HISTORICAL_DATA_VALIDATION",
        )
        self.assertEqual(len(result["matrix_rows"]), 31)
        self.assertEqual(len(result["pre_history_combinations_rejected"]), 9)
        self.assertFalse(result["gates"]["historical_sample_validation"])
        self.assertFalse(result["gates"]["return_test_authorized"])
        self.assertFalse(result["gates"]["alpha_admission"])
        self.assertFalse(result["gates"]["holdout_used"])
        self.assertTrue(result["gates"]["f80_frozen"])
        self.assertTrue(all(not row["numeric_transforms_applied"] for row in result["matrix_rows"]))


if __name__ == "__main__":
    unittest.main()
