import unittest

from research.phase145_ivydb_open_interest_pit import (
    build_oi_features,
    features_known_by,
)


def row(session, previous, oi, volume, received, **overrides):
    item = {
        "security_id": "1001",
        "option_id": "90001",
        "session_date": session,
        "previous_session_date": previous,
        "open_interest": oi,
        "volume": volume,
        "expiration_date": "2027-01-15",
        "contract_terms_key": "deliverable=100shares|multiplier=100|adj=1",
        "first_received_at": received,
        "source_file_hash": "sha256:abc123",
        "source_version": "ivydb-open-interest-v5",
    }
    item.update(overrides)
    return item


class Phase145Tests(unittest.TestCase):
    def pair(self, second_oi=125, second_volume=500, **overrides):
        return [
            row("2026-11-04", "", 100, 400, "2026-11-05T08:50:00-05:00"),
            row(
                "2026-11-05",
                "2026-11-04",
                second_oi,
                second_volume,
                "2026-11-06T08:50:00-05:00",
                **overrides,
            ),
        ]

    def test_positive_oi_change_is_state_not_buyer_direction(self):
        result = build_oi_features(self.pair())[1]
        self.assertEqual(result["delta_open_interest"], 25)
        self.assertEqual(result["delta_oi_to_volume"], 0.05)
        self.assertFalse(result["directional_buyer_signal"])

    def test_negative_oi_change_is_preserved(self):
        result = build_oi_features(self.pair(second_oi=80))[1]
        self.assertEqual(result["delta_open_interest"], -20)

    def test_first_observation_has_no_delta(self):
        result = build_oi_features(self.pair())[0]
        self.assertIsNone(result["delta_open_interest"])
        self.assertEqual(result["status"], "NO_PRIOR_SESSION")

    def test_missing_previous_session_is_not_bridged(self):
        rows = [
            row("2026-11-03", "", 90, 100, "2026-11-04T08:50:00-05:00"),
            row(
                "2026-11-05",
                "2026-11-04",
                110,
                200,
                "2026-11-06T08:50:00-05:00",
            ),
        ]
        result = build_oi_features(rows)[1]
        self.assertEqual(result["status"], "MISSING_PREVIOUS_SESSION")
        self.assertIsNone(result["delta_open_interest"])

    def test_contract_terms_change_blocks_delta(self):
        result = build_oi_features(
            self.pair(contract_terms_key="deliverable=101shares|multiplier=100|adj=1")
        )[1]
        self.assertEqual(result["status"], "CONTRACT_TERMS_BREAK")
        self.assertIsNone(result["delta_open_interest"])

    def test_expiry_session_blocks_delta(self):
        result = build_oi_features(
            self.pair(expiration_date="2026-11-05")
        )[1]
        self.assertEqual(result["status"], "EXPIRY_OR_EXERCISE_AFFECTED")
        self.assertIsNone(result["delta_open_interest"])

    def test_naive_receipt_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone_aware"):
            build_oi_features(
                self.pair()[0:1]
                + [
                    row(
                        "2026-11-05",
                        "2026-11-04",
                        125,
                        500,
                        "2026-11-06T08:50:00",
                    )
                ]
            )

    def test_receipt_must_follow_activity_session(self):
        with self.assertRaisesRegex(ValueError, "follow_activity_session"):
            build_oi_features(
                [
                    row(
                        "2026-11-05",
                        "2026-11-04",
                        125,
                        500,
                        "2026-11-05T08:50:00-05:00",
                    )
                ]
            )

    def test_duplicate_contract_session_is_rejected(self):
        rows = self.pair()
        rows.append(dict(rows[1]))
        with self.assertRaisesRegex(ValueError, "duplicate_contract_session"):
            build_oi_features(rows)

    def test_zero_volume_has_no_delta_to_volume_ratio(self):
        result = build_oi_features(self.pair(second_volume=0))[1]
        self.assertEqual(result["delta_open_interest"], 25)
        self.assertIsNone(result["delta_oi_to_volume"])

    def test_zero_prior_oi_has_no_ratio_denominator(self):
        rows = [
            row("2026-11-04", "", 0, 0, "2026-11-05T08:50:00-05:00"),
            row("2026-11-05", "2026-11-04", 10, 20, "2026-11-06T08:50:00-05:00"),
        ]
        result = build_oi_features(rows)[1]
        self.assertIsNone(result["volume_to_prior_oi"])
        self.assertIsNone(result["delta_oi_fraction_prior"])

    def test_feature_is_unavailable_before_actual_receipt(self):
        features = build_oi_features(self.pair())
        known = features_known_by(features, "2026-11-06T08:49:59-05:00")
        self.assertEqual(known, [])

    def test_feature_is_available_after_actual_receipt(self):
        features = build_oi_features(self.pair())
        known = features_known_by(features, "2026-11-06T08:50:01-05:00")
        self.assertEqual(len(known), 1)
        self.assertEqual(known[0]["delta_open_interest"], 25)

    def test_missing_source_provenance_is_rejected(self):
        rows = self.pair()
        rows[1]["source_file_hash"] = ""
        with self.assertRaisesRegex(ValueError, "source_provenance_missing"):
            build_oi_features(rows)



    def test_feature_is_unavailable_at_exact_receipt_timestamp(self):
        features = build_oi_features(self.pair())
        known = features_known_by(features, "2026-11-06T08:50:00-05:00")
        self.assertEqual(known, [])

    def test_expiration_date_change_blocks_delta(self):
        rows = self.pair()
        rows[1]["expiration_date"] = "2027-01-22"
        result = build_oi_features(rows)[1]
        self.assertEqual(result["status"], "EXPIRATION_DATE_BREAK")
        self.assertIsNone(result["delta_open_interest"])

    def test_stale_non_adjacent_previous_session_is_blocked(self):
        rows = [
            row("2026-11-03", "", 90, 100, "2026-11-04T08:50:00-05:00"),
            row("2026-11-04", "2026-11-03", 100, 150, "2026-11-05T08:50:00-05:00"),
            row("2026-11-05", "2026-11-03", 125, 500, "2026-11-06T08:50:00-05:00"),
        ]
        result = build_oi_features(rows)[2]
        self.assertEqual(result["status"], "NON_ADJACENT_PREVIOUS_SESSION")
        self.assertIsNone(result["delta_open_interest"])

    def test_input_order_does_not_change_results(self):
        rows = self.pair()
        forward = build_oi_features(rows)
        reverse = build_oi_features(list(reversed(rows)))
        self.assertEqual(forward, reverse)


if __name__ == "__main__":
    unittest.main()
