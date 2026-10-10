"""Static matplotlib charts for the asteroid tracker."""
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


def size_vs_distance(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = df["hazardous"].map({True: "tab:red", False: "tab:blue"})
    ax.scatter(df["miss_lunar"], df["diameter_avg_m"], c=colors, alpha=0.7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Miss distance (lunar distances, log)")
    ax.set_ylabel("Estimated diameter (m, log)")
    ax.set_title("Asteroid size vs. miss distance (red = potentially hazardous)")
    fig.tight_layout()
    return fig


def approaches_per_day(df: pd.DataFrame):
    counts = df.groupby("date").size()
    fig, ax = plt.subplots(figsize=(8, 4))
    counts.plot(kind="bar", ax=ax)
    ax.set_xlabel("Date")
    ax.set_ylabel("Close approaches")
    ax.set_title("Close approaches per day")
    fig.tight_layout()
    return fig
