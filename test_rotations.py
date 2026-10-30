import unittest
import pandas as pd

from rotations import build_rotations


class RotationTests(unittest.TestCase):
    def setUp(self):
        self.flights = pd.DataFrame([
            {
                "FlightDate": "2025-01-01",
                "Tail_Number": "TEST01",
                "Origin": "ATL",
                "Dest": "JFK",
                "CRSDepTime": 1000,
                "CRSElapsedTime": 120,
                "Cancelled": 0,
                "Diverted": 0,
                "DepDelay": 0,
                "ArrDelay": 50,
            },
            {
                "FlightDate": "2025-01-01",
                "Tail_Number": "TEST01",
                "Origin": "JFK",
                "Dest": "ATL",
                "CRSDepTime": 1300,
                "CRSElapsedTime": 120,
                "Cancelled": 0,
                "Diverted": 0,
                "DepDelay": 25,
                "ArrDelay": 10,
            },
        ])

    def test_exposure_calculation(self):
        pairs = build_rotations(self.flights)

        self.assertEqual(len(pairs), 1)

        pair = pairs.iloc[0]
        self.assertEqual(pair["scheduled_ground_minutes"], 60)
        self.assertEqual(pair["available_slack"], 30)
        self.assertEqual(pair["estimated_exposure"], 20)

    def test_cancelled_inbound_is_excluded(self):
        self.flights.loc[0, "Cancelled"] = 1

        pairs = build_rotations(self.flights)

        self.assertTrue(pairs.empty)

    def test_airport_mismatch_is_excluded(self):
        self.flights.loc[1, "Origin"] = "BOS"

        pairs = build_rotations(self.flights)

        self.assertTrue(pairs.empty)
    def test_connection_across_time_zones(self):
        self.flights.loc[0, "Origin"] = "LAX"
        self.flights.loc[0, "Dest"] = "JFK"
        self.flights.loc[0, "CRSDepTime"] = 800
        self.flights.loc[0, "CRSElapsedTime"] = 300

        self.flights.loc[1, "Origin"] = "JFK"
        self.flights.loc[1, "CRSDepTime"] = 1700

        pairs = build_rotations(self.flights)

        self.assertEqual(len(pairs), 1)
        self.assertEqual(
            pairs.iloc[0]["scheduled_ground_minutes"], 60
        )

    def test_overnight_connection(self):
        self.flights.loc[0, "CRSDepTime"] = 2300

        self.flights.loc[1, "FlightDate"] = "2025-01-02"
        self.flights.loc[1, "CRSDepTime"] = 200

        pairs = build_rotations(self.flights)

        self.assertEqual(len(pairs), 1)
        self.assertEqual(
            pairs.iloc[0]["scheduled_ground_minutes"], 60
        )    


if __name__ == "__main__":
    unittest.main()