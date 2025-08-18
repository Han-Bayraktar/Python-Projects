# app.py
import streamlit as st
from src.data_loader import load_core, build_enriched_results
from src.analytics import driver_points, constructor_points, championship_counts, driver_race_results, sprint_results_for_driver
from src.preprocessing import get_drivers_for_year
from src.visualizer import (
    plot_top_driver_points, plot_constructor_points, plot_championship_pie,
    plot_driver_season_progress, show_results_table
)
import pandas as pd

st.set_page_config(page_title="F1 Data Visualizer", layout="wide")
st.title("F1 Data Visualizer")

# Load data
data = load_core()
drivers = data["drivers"]
races = data["races"]
results = data["results"]
constructors = data["constructors"]
sprint = data.get("sprint_results")

# Build enriched results
try:
    enriched = build_enriched_results(drivers, races, results, constructors)
except Exception as e:
    st.error(f"Data loading error: {e}")
    st.stop()

# Sidebar controls
years = sorted([int(y) for y in enriched["year"].dropna().unique().tolist()]) if "year" in enriched.columns else []
year_choice = st.sidebar.selectbox("Select Year", ["All Time"] + years)
top_n = st.sidebar.slider("Top N", min_value=5, max_value=30, value=12, step=1)
show_sprints = st.sidebar.checkbox("Show Sprint Results (if available)", value=False)

# Tabs
tab_overview, tab_drivers, tab_constructors, tab_champs = st.tabs(["Overview", "Drivers", "Constructors", "Championships"])

# Overview tab
with tab_overview:
    st.header("Overview")
    if year_choice == "All Time":
        pts = driver_points(enriched, year=None)
        fig = plot_top_driver_points(pts, top_n=top_n)
        st.pyplot(fig, clear_figure=True)

        cons = constructor_points(enriched, year=None)
        figc = plot_constructor_points(cons, top_n=top_n)
        st.pyplot(figc, clear_figure=True)
    else:
        year = int(year_choice)
        pts = driver_points(enriched, year=year)
        fig = plot_top_driver_points(pts, top_n=top_n)
        st.pyplot(fig, clear_figure=True)

        cons = constructor_points(enriched, year=year)
        figc = plot_constructor_points(cons, top_n=top_n)
        st.pyplot(figc, clear_figure=True)

# Drivers tab
with tab_drivers:
    st.header("Drivers")
    if year_choice == "All Time":
        pts_all = driver_points(enriched, year=None)
        driver_options = pts_all["driverName"].tolist()
        selected_driver_name = st.selectbox("Select Driver (All Time)", ["None"] + driver_options)
        if selected_driver_name != "None":
            driver_row = pts_all[pts_all["driverName"] == selected_driver_name].iloc[0]
            driver_id = driver_row["driverId"]
            # show aggregated career points and championships
            st.subheader(f"{selected_driver_name} — Career Points: {int(driver_row['points'])}")
            # show per-season table
            per_season = enriched[enriched["driverId"] == driver_id].groupby("year")["points"].sum().reset_index()
            st.dataframe(per_season)
    else:
        year = int(year_choice)
        drivers_in_year = get_drivers_for_year(enriched, year)
        driver_map = drivers_in_year["driverName"].tolist()
        selected_driver_name = st.selectbox("Select Driver", ["None"] + driver_map)
        if selected_driver_name != "None":
            driver_id = drivers_in_year[drivers_in_year["driverName"] == selected_driver_name].iloc[0]["driverId"]
            st.subheader(f"{selected_driver_name} — {year} Season Results")
            # race by race results
            dr_results = driver_race_results(enriched, driver_id, year=year)
            show_results_table(dr_results)
            # cumulative progress
            fig_prog = plot_driver_season_progress(dr_results)
            st.pyplot(fig_prog, clear_figure=True)
            # sprint results if requested
            if show_sprints:
                sprint_df = sprint_results_for_driver(sprint, driver_id, year=year)
                if sprint_df is None or sprint_df.empty:
                    st.info("No sprint results available for this driver/year.")
                else:
                    st.subheader("Sprint Results")
                    st.dataframe(sprint_df)

# Constructors tab
with tab_constructors:
    st.header("Constructors / Teams")
    if year_choice == "All Time":
        cons = constructor_points(enriched, year=None)
        figc = plot_constructor_points(cons, top_n=top_n)
        st.pyplot(figc, clear_figure=True)
        st.dataframe(cons.head(top_n))
    else:
        year = int(year_choice)
        cons = constructor_points(enriched, year=year)
        figc = plot_constructor_points(cons, top_n=top_n)
        st.pyplot(figc, clear_figure=True)
        st.dataframe(cons)

# Championships tab
with tab_champs:
    st.header("Championships")
    # season champions table
    season_champs = None
    try:
        from src.analytics import season_champions, championship_counts
        season_champs = season_champions(enriched)
        st.subheader("Season Champions")
        st.dataframe(season_champs)
    except Exception:
        st.write("Season champions not available.")
    # championship counts & pie
    counts = championship_counts(enriched)
    figpie = plot_championship_pie(counts, top_n=10)
    st.pyplot(figpie, clear_figure=True)
    st.dataframe(counts)

st.caption("Tip: 'Show Sprint Results' option only works if sprint_results.csv does exist.")
