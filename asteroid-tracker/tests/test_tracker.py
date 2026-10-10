import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tracker

SAMPLE = {
    "near_earth_objects": {
        "2026-10-06": [
            {
                "id": "1", "name": "(2020 AB)", "is_potentially_hazardous_asteroid": False,
                "estimated_diameter": {"meters": {"estimated_diameter_min": 10.0, "estimated_diameter_max": 30.0}},
                "close_approach_data": [{
                    "close_approach_date": "2026-10-06",
                    "relative_velocity": {"kilometers_per_hour": "50000.5"},
                    "miss_distance": {"kilometers": "3000000", "lunar": "7.8"},
                }],
            },
            {
                "id": "2", "name": "(2019 XY)", "is_potentially_hazardous_asteroid": True,
                "estimated_diameter": {"meters": {"estimated_diameter_min": 100.0, "estimated_diameter_max": 300.0}},
                "close_approach_data": [{
                    "close_approach_date": "2026-10-06",
                    "relative_velocity": {"kilometers_per_hour": "70000"},
                    "miss_distance": {"kilometers": "1000000", "lunar": "2.6"},
                }],
            },
        ]
    }
}


def test_to_dataframe_flattens():
    df = tracker.to_dataframe(SAMPLE)
    assert len(df) == 2
    assert df.loc[0, "diameter_avg_m"] == 20.0


def test_sort_by_size():
    df = tracker.sort_by_size(tracker.to_dataframe(SAMPLE))
    assert df.loc[0, "name"] == "2019 XY"


def test_closest():
    assert tracker.closest(tracker.to_dataframe(SAMPLE), 1).loc[0, "name"] == "2019 XY"
