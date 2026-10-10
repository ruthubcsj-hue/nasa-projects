"""Asteroid Tracker dashboard. Run with: streamlit run app.py"""
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

import earth_view
import tracker

st.set_page_config(page_title="Asteroid Tracker", page_icon="☄️", layout="wide")

ORANGE, BLUE, MUTED = "#ff7a45", "#4cc9f0", "#8892b0"

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1300px;}
    .hero h1 {
        font-size: 2.6rem; margin-bottom: 0;
        background: linear-gradient(90deg, #ff7a45, #4cc9f0);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero p {color: #8892b0; margin-top: 0.2rem;}
    .kpi {
        background: #131a2b; border: 1px solid #222c45; border-radius: 14px;
        padding: 1rem 1.2rem;
    }
    .kpi .label {color: #8892b0; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em;}
    .kpi .value {font-size: 1.9rem; font-weight: 700; color: #e6e9f2;}
    .kpi .sub {color: #8892b0; font-size: 0.8rem;}
    .kpi.hot .value {color: #ff7a45;}
    </style>
    <div class="hero">
      <h1>Near-Earth Asteroid Tracker</h1>
      <p>Live close-approach data from NASA's NeoWs API</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def kpi(col, label, value, sub="", hot=False):
    col.markdown(
        f'<div class="kpi {"hot" if hot else ""}"><div class="label">{label}</div>'
        f'<div class="value">{value}</div><div class="sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def style(fig, height=420):
    fig.update_layout(
        template="plotly_dark", height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=10), legend_title_text="",
    )
    return fig


@st.cache_data(ttl=3600, show_spinner="Contacting NASA...")
def load(days: int):
    return tracker.get_dataframe(days)


# ---------- Sidebar filters ----------
st.sidebar.header("Filters")
days = st.sidebar.slider("Days ahead", 1, 7, 7)
only_hazardous = st.sidebar.checkbox("Potentially hazardous only")

try:
    raw = load(days)
except Exception as exc:  # network error, rate limit, bad key
    st.error(f"Could not fetch NASA data: {exc}")
    st.stop()

if raw.empty:
    st.warning("NASA returned no objects for this range.")
    st.stop()

min_d = st.sidebar.slider("Min diameter (m)", 0, int(raw["diameter_avg_m"].max()), 0)
max_ld = st.sidebar.slider(
    "Max miss distance (lunar distances)", 1, int(raw["miss_lunar"].max()) + 1,
    int(raw["miss_lunar"].max()) + 1,
)
st.sidebar.caption("1 lunar distance (LD) = average Earth-Moon distance, about 384,400 km.")

df = raw[(raw["diameter_avg_m"] >= min_d) & (raw["miss_lunar"] <= max_ld)]
if only_hazardous:
    df = df[df["hazardous"]]
if df.empty:
    st.warning("No objects match these filters. Loosen them in the sidebar.")
    st.stop()

df = df.assign(status=df["hazardous"].map({True: "Hazardous", False: "Non-hazardous"}))
color_map = {"Hazardous": ORANGE, "Non-hazardous": BLUE}

# ---------- KPI cards ----------
c1, c2, c3, c4 = st.columns(4)
nearest = df.loc[df["miss_km"].idxmin()]
biggest = df.loc[df["diameter_avg_m"].idxmax()]
kpi(c1, "Close approaches", len(df), f"next {days} day(s)")
kpi(c2, "Potentially hazardous", int(df["hazardous"].sum()), "flagged by NASA", hot=True)
kpi(c3, "Nearest pass", f"{nearest['miss_lunar']:.1f} LD", nearest["name"])
kpi(c4, "Largest object", f"{biggest['diameter_avg_m']:.0f} m", biggest["name"])
st.write("")

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "3D Earth View", "Rankings", "Raw data"])

with tab1:
    left, right = st.columns([3, 2])
    scatter = px.scatter(
        df, x="miss_lunar", y="diameter_avg_m", color="status", size="velocity_kmh",
        hover_name="name", log_x=True, log_y=True, size_max=24, color_discrete_map=color_map,
        labels={"miss_lunar": "Miss distance (LD, log)", "diameter_avg_m": "Diameter (m, log)"},
        hover_data={"status": False, "velocity_kmh": ":,.0f", "date": True},
        title="Size vs. distance (bubble size = speed)",
    )
    scatter.add_vline(x=1, line_dash="dot", line_color=MUTED)  # Moon's orbit
    left.plotly_chart(style(scatter), width="stretch")

    per_day = df.groupby(["date", "status"]).size().reset_index(name="count")
    bars = px.bar(
        per_day, x="date", y="count", color="status", color_discrete_map=color_map,
        title="Close approaches per day", labels={"count": "Objects", "date": ""},
    )
    bars.update_xaxes(type="category")
    right.plotly_chart(style(bars), width="stretch")
    st.caption("Dotted line on the scatter plot = the Moon's orbit (1 LD).")

with tab2:
    max_n = min(25, len(df))
    n = st.slider("Objects to show (closest first)", 3, max_n, min(12, max_n)) if max_n > 3 else max_n
    components.html(earth_view.build_html(tracker.closest(df, n)), height=690)
    st.caption("Lines connect each asteroid to Earth and show its miss distance. Red = potentially hazardous, green = not. "
               "Distances use a log scale and sizes are exaggerated so everything fits on screen.")

with tab3:
    cols = ["name", "date", "diameter_avg_m", "miss_lunar", "velocity_kmh", "hazardous"]
    config = {
        "name": "Object", "date": "Date",
        "diameter_avg_m": st.column_config.NumberColumn("Diameter (m)", format="%.0f"),
        "miss_lunar": st.column_config.NumberColumn("Miss (LD)", format="%.1f"),
        "velocity_kmh": st.column_config.NumberColumn("Speed (km/h)", format="%,.0f"),
        "hazardous": st.column_config.CheckboxColumn("Hazardous"),
    }
    a, b = st.columns(2)
    a.subheader("Largest")
    a.dataframe(tracker.sort_by_size(df)[cols].head(10), hide_index=True, column_config=config, width="stretch")
    b.subheader("Closest")
    b.dataframe(tracker.closest(df, 10)[cols], hide_index=True, column_config=config, width="stretch")

with tab4:
    st.dataframe(df.drop(columns=["status"]), hide_index=True, width="stretch")
    st.download_button("Download CSV", df.drop(columns=["status"]).to_csv(index=False), "asteroids.csv", "text/csv")
