# main.py
from src.data_loader import load_core, build_enriched_results
from src.analytics import driver_points, constructor_points, championship_counts, driver_race_results
from src.visualizer import plot_top_driver_points, plot_constructor_points, plot_championship_pie, plot_driver_season_progress
import matplotlib.pyplot as plt

def main():
    data = load_core()
    drivers = data["drivers"]
    races = data["races"]
    results = data["results"]
    constructors = data["constructors"]
    sprint = data.get("sprint_results")

    enriched = build_enriched_results(drivers, races, results, constructors)

    # All-time driver points
    pts = driver_points(enriched)
    fig1 = plot_top_driver_points(pts, top_n=10)
    fig1.show()

    # All-time constructors
    cons = constructor_points(enriched)
    fig2 = plot_constructor_points(cons, top_n=10)
    fig2.show()

    # Championship counts pie
    ch = championship_counts(enriched)
    fig3 = plot_championship_pie(ch, top_n=8)
    fig3.show()

    # Example: pick first driver in pts and show season progress for 2020 if available
    if not pts.empty:
        driver_id = pts.iloc[0]["driverId"]
        dr2020 = driver_race_results(enriched, driver_id, year=2020)
        fig4 = plot_driver_season_progress(dr2020)
        fig4.show()

if __name__ == "__main__":
    main()
