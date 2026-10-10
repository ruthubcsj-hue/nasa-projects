"""Fetch and process near-Earth object (NEO) data from NASA's NeoWs API."""
from __future__ import annotations

import os
import re
from datetime import date, timedelta

import pandas as pd
import requests

API_URL = "https://api.nasa.gov/neo/rest/v1/feed"
MAX_RANGE_DAYS = 7  # NeoWs limits the feed to a 7-day window


def fetch_feed(start: date, end: date, api_key: str | None = None) -> dict:
    """Retrieve raw JSON for asteroids approaching Earth between start and end."""
    if (end - start).days > MAX_RANGE_DAYS:
        raise ValueError(f"Date range cannot exceed {MAX_RANGE_DAYS} days")
    key = api_key or os.getenv("NASA_API_KEY", "DEMO_KEY")
    resp = requests.get(
        API_URL,
        params={"start_date": start.isoformat(), "end_date": end.isoformat(), "api_key": key},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def to_dataframe(raw: dict) -> pd.DataFrame:
    """Flatten the nested NeoWs response into one row per close approach."""
    rows = []
    for day, objects in raw.get("near_earth_objects", {}).items():
        for obj in objects:
            diameter = obj["estimated_diameter"]["meters"]
            for approach in obj.get("close_approach_data", []):
                rows.append(
                    {
                        "id": obj["id"],
                        "name": re.sub(r"^\((.*)\)$", r"\1", obj["name"].strip()),
                        "date": approach["close_approach_date"],
                        "diameter_min_m": diameter["estimated_diameter_min"],
                        "diameter_max_m": diameter["estimated_diameter_max"],
                        "hazardous": obj["is_potentially_hazardous_asteroid"],
                        "velocity_kmh": float(approach["relative_velocity"]["kilometers_per_hour"]),
                        "miss_km": float(approach["miss_distance"]["kilometers"]),
                        "miss_lunar": float(approach["miss_distance"]["lunar"]),
                    }
                )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["diameter_avg_m"] = (df["diameter_min_m"] + df["diameter_max_m"]) / 2
    return df


def sort_by_size(df: pd.DataFrame, ascending: bool = False) -> pd.DataFrame:
    return df.sort_values("diameter_avg_m", ascending=ascending).reset_index(drop=True)


def closest(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return df.nsmallest(n, "miss_km").reset_index(drop=True)


def get_dataframe(days: int = 7, api_key: str | None = None) -> pd.DataFrame:
    start = date.today()
    return to_dataframe(fetch_feed(start, start + timedelta(days=days), api_key))


if __name__ == "__main__":
    data = get_dataframe()
    print(f"{len(data)} close approaches in the next 7 days\n")
    print("Largest objects:")
    print(sort_by_size(data).head(5)[["name", "date", "diameter_avg_m", "miss_lunar"]].to_string(index=False))
    print("\nClosest approaches:")
    print(closest(data, 5)[["name", "date", "miss_lunar", "velocity_kmh"]].to_string(index=False))
