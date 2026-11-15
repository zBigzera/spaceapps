import unittest

import pandas as pd

from spaceapps.validation import estimate_signals


class EstimatedSignalTests(unittest.TestCase):
    def frame(self, rain, risk):
        return pd.DataFrame({"precip_mm": rain, "flood_risk": risk, "precip_7d": rain},
                            index=pd.date_range("2026-01-01", periods=len(rain)))

    def test_extreme_rain_is_separate_from_other_rainy_high_risk_days(self):
        result = estimate_signals(self.frame(list(range(1, 21)), [80] * 20))
        self.assertAlmostEqual(result["wet_day_p95_mm"], 19.05)
        self.assertEqual(result["events"][-1]["kind"], "flash_flood_proxy")
        self.assertEqual(result["events"][-2]["kind"], "flood_signal")
        self.assertFalse(result["confirmed"])

    def test_no_rain_or_missing_values_do_not_create_estimates(self):
        result = estimate_signals(self.frame([0, None, 10, 12], [90, 90, None, 74.99]))
        self.assertEqual(result["events"], [])

    def test_risk_and_extreme_rain_thresholds_are_inclusive(self):
        result = estimate_signals(self.frame([10] * 20, [75] * 20))
        self.assertEqual(len(result["events"]), 20)
        self.assertTrue(all(e["kind"] == "flash_flood_proxy" for e in result["events"]))

    def test_dry_days_are_excluded_from_percentile_baseline(self):
        result = estimate_signals(self.frame([0] * 100 + [10, 20], [80] * 102))
        self.assertEqual(result["wet_day_count"], 2)
        self.assertEqual(result["wet_day_p95_mm"], 19.5)

    def test_all_dry_record_has_no_threshold_or_signals(self):
        result = estimate_signals(self.frame([0, 0], [90, 90]))
        self.assertIsNone(result["wet_day_p95_mm"])
        self.assertEqual(result["events"], [])
