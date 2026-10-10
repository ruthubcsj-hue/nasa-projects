"""Interactive dashboard. Run with: streamlit run app.py"""
import streamlit as st

import plots
import tracker

st.set_page_config(page_title="Asteroid Tracker", layout="wide")
st.title("Near-Earth Asteroid Tracker")
st.caption("Data: NASA NeoWs API")

days = st.sidebar.slider("Days ahead", 1, 7, 7)
only_hazardous = st.sidebar.checkbox("Potentially hazardous only")


@st.cache_data(ttl=3600)
def load(days: int):
    return tracker.get_dataframe(days)


try:
    df = load(days)
except Exception as exc:  # network error, rate limit, bad key
    st.error(f"Could not fetch NASA data: {exc}")
    st.stop()

if only_hazardous:
    df = df[df["hazardous"]]

c1, c2, c3 = st.columns(3)
c1.metric("Close approaches", len(df))
c2.metric("Potentially hazardous", int(df["hazardous"].sum()))
c3.metric("Largest (m)", f"{df['diameter_avg_m'].max():.0f}" if len(df) else "-")

left, right = st.columns(2)
left.pyplot(plots.size_vs_distance(df))
right.pyplot(plots.approaches_per_day(df))

st.subheader("Sorted by size")
st.dataframe(tracker.sort_by_size(df)[["name", "date", "diameter_avg_m", "miss_lunar", "velocity_kmh", "hazardous"]])
