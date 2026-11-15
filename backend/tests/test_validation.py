import unittest

import pandas as pd

from spaceapps.validation import compare_events


class OfficialEventComparisonTests(unittest.TestCase):
    def compare(self, dates, values, start="2026-02-01", end="2026-02-28", region="uba"):
        frame = pd.DataFrame({"flood_risk": values}, index=pd.to_datetime(dates))
        return compare_events(frame, region, start, end)

    def test_threshold_is_inclusive(self):
        result = self.compare(["2026-02-23", "2026-02-24"], [74.9, 75])
        self.assertEqual(result["matched"], 1)
        self.assertEqual(result["events"][0]["peak_index"], 75)

    def test_complete_event_below_threshold_is_reported(self):
        result = self.compare(["2026-02-23", "2026-02-24"], [40, 61.6])
        self.assertEqual(result["events"][0]["result"], "below_threshold")
        self.assertEqual(result["evaluated"], 1)

    def test_missing_day_cannot_establish_a_miss(self):
        result = self.compare(["2026-02-23"], [61.6])
        self.assertEqual(result["events"][0]["result"], "insufficient_data")
        self.assertEqual(result["evaluated"], 0)

    def test_missing_value_cannot_establish_a_miss(self):
        result = self.compare(["2026-02-23", "2026-02-24"], [None, 61.6])
        self.assertEqual(result["evaluated"], 0)

    def test_partial_window_can_confirm_a_threshold_crossing(self):
        result = self.compare(["2026-02-24"], [80])
        self.assertEqual(result["events"][0]["result"], "matched")
        self.assertFalse(result["events"][0]["complete_window"])

    def test_event_outside_selection_is_excluded(self):
        result = self.compare(["2026-03-01"], [90], start="2026-03-01", end="2026-03-31")
        self.assertEqual(result["events"], [])

    def test_unknown_catalog_is_not_treated_as_zero_floods(self):
        result = self.compare(["2026-02-23"], [90], region="custom")
        self.assertEqual(result["evaluated"], 0)
        self.assertFalse(result["catalog_complete"])


if __name__ == "__main__":
    unittest.main()
