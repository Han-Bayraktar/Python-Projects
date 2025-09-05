import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from src.data_loader import load_core, build_enriched_results
from src.analytics import (
    driver_points, constructor_points, championship_counts,
    driver_race_results, sprint_results_for_driver
)
from src.preprocessing import get_drivers_for_year

st.set_page_config(
    page_title="🏎️ F1 Data Visualizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #FF1E00, #FF6B00, #FFD700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }

    .metric-container {
        background: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin: 0.5rem 0;
    }

    .season-header {
        font-size: 1.5rem;
        color: #FF6B00;
        font-weight: bold;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🏎️ Formula 1 Data Visualizer</div>', unsafe_allow_html=True)


@st.cache_data
def load_f1_data():
    data = load_core()
    drivers = data["drivers"]
    races = data["races"]
    results = data["results"]
    constructors = data["constructors"]
    sprint = data.get("sprint_results")

    enriched = build_enriched_results(drivers, races, results, constructors)
    return enriched, drivers, races, results, constructors, sprint


try:
    enriched, drivers, races, results, constructors, sprint = load_f1_data()
except Exception as e:
    st.error(f"❌ Data loading error: {e}")
    st.stop()

st.sidebar.markdown("### 🎛️ Controls")

years = sorted([int(y) for y in enriched["year"].dropna().unique().tolist()]) if "year" in enriched.columns else []
year_choice = st.sidebar.selectbox("📅 Select Year", ["All Time"] + years, index=len(years))

if year_choice == "All Time":
    drivers_all = enriched[["driverId", "driverName"]].drop_duplicates()
else:
    drivers_all = enriched[enriched["year"] == int(year_choice)][["driverId", "driverName"]].drop_duplicates()

driver_choice = st.sidebar.selectbox(
    "🏁 Select Driver",
    ["None"] + sorted(drivers_all["driverName"].tolist())
)

top_n = st.sidebar.slider("🏆 Top N Results", min_value=5, max_value=30, value=15, step=1)


def create_modern_bar_chart(df, x_col, y_col, title, color_sequence=px.colors.qualitative.Set3):
    fig = px.bar(
        df.head(top_n),
        x=y_col,
        y=x_col,
        orientation='h',
        title=title,
        color=y_col,
        color_continuous_scale='Viridis',
        text=y_col
    )

    fig.update_traces(
        texttemplate='%{text}',
        textposition='outside',
        textfont_size=10
    )

    fig.update_layout(
        height=max(400, len(df.head(top_n)) * 30),
        showlegend=False,
        title_font_size=18,
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        yaxis=dict(categoryorder='total ascending')
    )

    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(showgrid=False)

    return fig


def create_progress_chart(df):
    if df is None or df.empty:
        return None

    df_sorted = df.copy()
    if "round" in df_sorted.columns:
        df_sorted = df_sorted.sort_values("round")
        x_axis = "round"
    else:
        df_sorted = df_sorted.sort_values("raceId")
        x_axis = "raceId"

    df_sorted["cumulative_points"] = df_sorted["points"].cumsum()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_sorted[x_axis],
        y=df_sorted["cumulative_points"],
        mode='lines+markers',
        line=dict(color='#FF6B00', width=3),
        marker=dict(size=8, color='#FFD700'),
        name='Cumulative Points',
        hovertemplate='<b>Race %{x}</b><br>Points: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title="📈 Season Progress (Cumulative Points)",
        title_font_size=18,
        title_x=0.5,
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=False
    )

    fig.update_xaxes(title="Race", showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(title="Cumulative Points", showgrid=True, gridcolor='rgba(255,255,255,0.1)')

    return fig


def create_grid_vs_position_chart(df):
    if df is None or df.empty:
        return None

    df_clean = df.copy()
    df_clean["grid"] = pd.to_numeric(df_clean["grid"], errors="coerce")
    df_clean["position"] = pd.to_numeric(df_clean["position"], errors="coerce")
    df_clean = df_clean.dropna(subset=["grid", "position"])

    if df_clean.empty:
        return None

    race_names = df_clean["raceName"].unique() if "raceName" in df_clean.columns else df_clean["raceId"].unique()
    colors = px.colors.qualitative.Set3[:len(race_names)]

    fig = px.scatter(
        df_clean,
        x="grid",
        y="position",
        color="raceName" if "raceName" in df_clean.columns else "raceId",
        size="points",
        title="🏁 Grid Position vs Finish Position",
        hover_data=["points"],
        color_discrete_sequence=colors
    )

    max_pos = max(df_clean["grid"].max(), df_clean["position"].max())
    fig.add_trace(go.Scatter(
        x=[1, max_pos],
        y=[1, max_pos],
        mode='lines',
        line=dict(dash='dash', color='red'),
        name='Grid = Finish',
        showlegend=False
    ))

    fig.update_layout(
        height=500,
        title_font_size=18,
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    fig.update_xaxes(title="Grid Position", showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(title="Finish Position", showgrid=True, gridcolor='rgba(255,255,255,0.1)')

    return fig


def create_championship_donut(counts_df):
    if counts_df.empty:
        return None

    data = counts_df.head(10)

    fig = go.Figure(data=[go.Pie(
        labels=data["driverName"],
        values=data["championships"],
        hole=.4,
        textinfo='label+percent',
        textposition='outside',
        marker=dict(colors=px.colors.qualitative.Set3),
        hovertemplate='<b>%{label}</b><br>Championships: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])

    fig.update_layout(
        title="🏆 Championship Distribution",
        title_font_size=18,
        title_x=0.5,
        height=500,
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    return fig


def create_race_winners_chart(enriched_df, year):
    year_data = enriched_df[enriched_df["year"] == year]
    winners = year_data[year_data["position"] == 1]

    if winners.empty:
        return None

    winner_counts = winners["driverName"].value_counts()

    fig = px.bar(
        x=winner_counts.index,
        y=winner_counts.values,
        title=f"🏆 Race Winners in {year}",
        color=winner_counts.values,
        color_continuous_scale='Viridis',
        text=winner_counts.values
    )

    fig.update_traces(
        texttemplate='%{text}',
        textposition='outside'
    )

    fig.update_layout(
        height=400,
        title_font_size=18,
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=False
    )

    fig.update_xaxes(title="Driver", showgrid=False)
    fig.update_yaxes(title="Wins", showgrid=True, gridcolor='rgba(255,255,255,0.1)')

    return fig


tab_season, tab_driver, tab_constructors, tab_champs, tab_extras = st.tabs([
    "🏁 Season Overview",
    "👤 Driver Overview",
    "🏢 Constructors",
    "🏆 Championships",
    "📊 Extra Stats"
])

with tab_season:
    if year_choice != "All Time":
        year = int(year_choice)
        st.markdown(f'<div class="season-header">🏁 Season {year} Overview</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🏎️ Driver Standings")
            pts = driver_points(enriched, year=year)
            if not pts.empty:
                fig = create_modern_bar_chart(pts, "driverName", "points", f"Driver Points - {year}")
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("**Top 10 Drivers:**")
                pts_display = pts.head(10).copy()
                pts_display.index = range(1, len(pts_display) + 1)
                st.dataframe(pts_display, use_container_width=True)

        with col2:
            st.subheader("🏢 Constructor Standings")
            cons = constructor_points(enriched, year=year)
            if not cons.empty:
                fig = create_modern_bar_chart(cons, "constructorName", "points", f"Constructor Points - {year}")
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("**Constructor Standings:**")
                cons_display = cons.copy()
                cons_display.index = range(1, len(cons_display) + 1)
                st.dataframe(cons_display, use_container_width=True)

        st.subheader("🏆 Race Winners")
        winners_fig = create_race_winners_chart(enriched, year)
        if winners_fig:
            st.plotly_chart(winners_fig, use_container_width=True)

        if "raceName" in enriched.columns:
            race_data = enriched[enriched["year"] == year]
            race_winners = race_data[race_data["position"] == 1]
            if not race_winners.empty:
                race_summary = race_winners[["round", "raceName", "driverName", "constructorName"]].copy()
                race_summary = race_summary.rename(columns={
                    "round": "Round",
                    "raceName": "Race",
                    "driverName": "Winner",
                    "constructorName": "Team"
                }).sort_values("Round")

                st.markdown("**Race Results:**")
                st.dataframe(race_summary, use_container_width=True, hide_index=True)
    else:
        st.info("📊 Please select a specific year to see season overview")

with tab_driver:
    st.markdown(f'<div class="season-header">👤 Driver Analysis</div>', unsafe_allow_html=True)

    if driver_choice != "None":
        driver_id = drivers_all[drivers_all["driverName"] == driver_choice].iloc[0]["driverId"]

        if year_choice != "All Time":
            year = int(year_choice)
            dr_results = driver_race_results(enriched, driver_id, year=year)

            if not dr_results.empty:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader(f"📈 {driver_choice} - Season {year} Progress")
                    progress_fig = create_progress_chart(dr_results)
                    if progress_fig:
                        st.plotly_chart(progress_fig, use_container_width=True)

                    total_points = dr_results["points"].sum()
                    avg_points = dr_results["points"].mean()
                    races_completed = len(dr_results)

                    st.markdown("**Season Statistics:**")
                    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                    with metrics_col1:
                        st.metric("Total Points", f"{total_points:.0f}")
                    with metrics_col2:
                        st.metric("Avg Points/Race", f"{avg_points:.1f}")
                    with metrics_col3:
                        st.metric("Races", races_completed)

                with col2:
                    st.subheader("🏁 Starting vs Finishing Positions")
                    grid_fig = create_grid_vs_position_chart(dr_results)
                    if grid_fig:
                        st.plotly_chart(grid_fig, use_container_width=True)
                    else:
                        st.info("No grid/position data available")

                st.subheader(f"📋 {driver_choice} - Detailed Race Results")
                if not dr_results.empty:
                    results_display = dr_results.copy()
                    display_cols = ["round", "raceName", "position", "points", "grid"]
                    available_cols = [col for col in display_cols if col in results_display.columns]

                    if available_cols:
                        results_display = results_display[available_cols]
                        results_display.columns = [col.title() for col in available_cols]
                        st.dataframe(results_display, use_container_width=True, hide_index=True)
            else:
                st.warning(f"No race results found for {driver_choice} in {year}")
        else:
            st.subheader(f"🏎️ {driver_choice} - Career Overview")
            driver_data = enriched[enriched["driverId"] == driver_id]

            if not driver_data.empty:
                col1, col2, col3, col4 = st.columns(4)

                total_points = driver_data["points"].sum()
                total_races = len(driver_data)
                podiums = len(
                    driver_data[driver_data["position"].isin([1, 2, 3])]) if "position" in driver_data.columns else 0
                wins = len(driver_data[driver_data["position"] == 1]) if "position" in driver_data.columns else 0

                with col1:
                    st.metric("Career Points", f"{total_points:.0f}")
                with col2:
                    st.metric("Total Races", total_races)
                with col3:
                    st.metric("Podiums", podiums)
                with col4:
                    st.metric("Wins", wins)

                yearly_points = driver_data.groupby("year")["points"].sum().reset_index()

                fig = px.line(
                    yearly_points,
                    x="year",
                    y="points",
                    title=f"{driver_choice} - Career Points by Season",
                    markers=True
                )

                fig.update_layout(
                    height=400,
                    title_font_size=18,
                    title_x=0.5,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white')
                )

                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("👤 Please select a driver to see detailed analysis")

with tab_constructors:
    st.markdown('<div class="season-header">🏢 Constructor Analysis</div>', unsafe_allow_html=True)

    if year_choice == "All Time":
        cons = constructor_points(enriched, year=None)
        st.subheader("🏆 All-Time Constructor Points")
    else:
        year = int(year_choice)
        cons = constructor_points(enriched, year=year)
        st.subheader(f"🏆 Constructor Standings - {year}")

    if not cons.empty:
        fig = create_modern_bar_chart(cons, "constructorName", "points", "Constructor Championship Points")
        st.plotly_chart(fig, use_container_width=True)

        # Display table
        cons_display = cons.head(top_n).copy()
        cons_display.index = range(1, len(cons_display) + 1)
        st.dataframe(cons_display, use_container_width=True)

with tab_champs:
    st.markdown('<div class="season-header">🏆 Championship History</div>', unsafe_allow_html=True)

    try:
        from src.analytics import season_champions

        season_champs = season_champions(enriched)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📅 Champions by Season")
            if not season_champs.empty:
                champs_display = season_champs[["year", "driverName", "points"]].copy()
                champs_display.columns = ["Year", "Champion", "Points"]
                champs_display = champs_display.sort_values("Year", ascending=False)
                st.dataframe(champs_display, use_container_width=True, hide_index=True, height=400)

        with col2:
            st.subheader("🏆 Championship Distribution")
            counts = championship_counts(enriched)
            if not counts.empty:
                donut_fig = create_championship_donut(counts)
                if donut_fig:
                    st.plotly_chart(donut_fig, use_container_width=True)

                counts_display = counts.copy()
                counts_display.columns = ["Driver ID", "Driver", "Championships"]
                counts_display = counts_display[["Driver", "Championships"]]
                st.dataframe(counts_display, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading championship data: {e}")

with tab_extras:
    st.markdown('<div class="season-header">📊 Advanced Statistics</div>', unsafe_allow_html=True)

    if driver_choice != "None":
        driver_id = drivers_all[drivers_all["driverName"] == driver_choice].iloc[0]["driverId"]
        df_driver = enriched[enriched["driverId"] == driver_id]

        if year_choice != "All Time":
            df_driver = df_driver[df_driver["year"] == int(year_choice)]
            period = f"in {year_choice}"
        else:
            period = "in career"

        st.subheader(f"🔍 Advanced Stats for {driver_choice} {period}")

        col1, col2, col3, col4 = st.columns(4)

        if "position" in df_driver.columns:
            df_driver["position_num"] = pd.to_numeric(df_driver["position"], errors="coerce")
            podiums = len(df_driver[df_driver["position_num"].isin([1, 2, 3])])
            wins = len(df_driver[df_driver["position_num"] == 1])
            avg_finish = df_driver["position_num"].mean()
        else:
            podiums = wins = avg_finish = 0

        if "status" in df_driver.columns:
            dnf = len(df_driver[df_driver["status"].str.contains("DNF|Accident|Engine|Gearbox", case=False, na=False)])
            finish_rate = ((len(df_driver) - dnf) / len(df_driver)) * 100 if len(df_driver) > 0 else 0
        else:
            dnf = 0
            finish_rate = 100

        with col1:
            st.metric("🏆 Wins", wins)
        with col2:
            st.metric("🥇 Podiums", podiums)
        with col3:
            st.metric("💥 DNFs", dnf)
        with col4:
            st.metric("✅ Finish Rate", f"{finish_rate:.1f}%")

        if "grid" in df_driver.columns and "position" in df_driver.columns:
            df_analysis = df_driver.copy()
            df_analysis["grid"] = pd.to_numeric(df_analysis["grid"], errors="coerce")
            df_analysis["position_num"] = pd.to_numeric(df_analysis["position"], errors="coerce")
            df_analysis = df_analysis.dropna(subset=["grid", "position_num"])

            if not df_analysis.empty:
                df_analysis["position_change"] = df_analysis["grid"] - df_analysis["position_num"]
                avg_change = df_analysis["position_change"].mean()

                st.subheader("📈 Position Changes Analysis")

                change_fig = px.bar(
                    df_analysis,
                    x="raceId" if "raceName" not in df_analysis.columns else "raceName",
                    y="position_change",
                    title=f"Position Changes per Race (Avg: {avg_change:+.1f})",
                    color="position_change",
                    color_continuous_scale="RdYlGn"
                )

                change_fig.add_hline(
                    y=0,
                    line_dash="dash",
                    line_color="white",
                    annotation_text="No Change"
                )

                change_fig.update_layout(
                    height=400,
                    title_font_size=18,
                    title_x=0.5,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white')
                )

                st.plotly_chart(change_fig, use_container_width=True)

                gained_positions = df_analysis[df_analysis["position_change"] > 0]
                lost_positions = df_analysis[df_analysis["position_change"] < 0]

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📈 Races Gained Positions", len(gained_positions))
                with col2:
                    st.metric("📉 Races Lost Positions", len(lost_positions))
                with col3:
                    st.metric("🎯 Average Position Change", f"{avg_change:+.1f}")

    if year_choice != "All Time":
        year = int(year_choice)
        st.subheader(f"🏢 Team Performance Comparison - {year}")

        team_analysis = enriched[enriched["year"] == year].groupby(["constructorName", "driverName"])[
            "points"].sum().reset_index()

        if not team_analysis.empty:
            fig = px.bar(
                team_analysis,
                x="constructorName",
                y="points",
                color="driverName",
                title=f"Team vs Driver Performance - {year}",
                barmode="group"
            )

            fig.update_layout(
                height=500,
                title_font_size=18,
                title_x=0.5,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )

            st.plotly_chart(fig, use_container_width=True)

            pivot_table = team_analysis.pivot(index="constructorName", columns="driverName", values="points").fillna(0)
            st.dataframe(pivot_table, use_container_width=True)

st.markdown("---")
st.markdown("🏎️ **F1 Data Visualizer** - By Han-Bayraktar")