# src/analytics.py
import pandas as pd

def driver_points(enriched_results: pd.DataFrame, year: int | None = None):
    df = enriched_results.copy()
    if year is not None:
        df = df[df["year"] == int(year)]
    pts = (
        df.groupby(["driverId", "driverName"], dropna=False)["points"]
          .sum()
          .reset_index()
          .sort_values("points", ascending=False)
          .reset_index(drop=True)
    )
    return pts

def constructor_points(enriched_results: pd.DataFrame, year: int | None = None):
    if "constructorId" not in enriched_results.columns:
        return pd.DataFrame(columns=["constructorId", "constructorName", "points"])
    df = enriched_results.copy()
    if year is not None:
        df = df[df["year"] == int(year)]
    pts = (
        df.groupby(["constructorId", "constructorName"], dropna=False)["points"]
          .sum()
          .reset_index()
          .sort_values("points", ascending=False)
          .reset_index(drop=True)
    )
    return pts

def season_champions(enriched_results: pd.DataFrame):
    df = enriched_results.copy()
    season_pts = (
        df.groupby(["year", "driverId", "driverName"], dropna=False)["points"]
          .sum()
          .reset_index()
    )
    idx = season_pts.groupby("year")["points"].idxmax()
    champs = season_pts.loc[idx].sort_values("year").reset_index(drop=True)
    return champs

def championship_counts(enriched_results: pd.DataFrame):
    champs = season_champions(enriched_results)
    counts = (
        champs.groupby(["driverId", "driverName"]).size()
              .reset_index(name="championships")
              .sort_values(["championships", "driverName"], ascending=[False, True])
              .reset_index(drop=True)
    )
    return counts

def driver_race_results(enriched_results: pd.DataFrame, driver_id: int | str, year: int | None = None):
    df = enriched_results.copy()
    df = df[df["driverId"] == driver_id]
    if year is not None:
        df = df[df["year"] == int(year)]
    # Select useful columns if exist
    cols = [c for c in ["year", "raceId", "round", "raceName", "position", "points", "grid", "status"] if c in df.columns]
    if "raceId" not in cols:
        cols.insert(0, "raceId")
    cols = [c for c in cols if c in df.columns]
    out = df[cols].sort_values(["year", "raceId"]).reset_index(drop=True)
    return out

def sprint_results_for_driver(sprint_df: pd.DataFrame, driver_id: int | str, year: int | None = None):
    if sprint_df is None:
        return pd.DataFrame()  # empty
    df = sprint_df.copy()
    if year is not None and "year" in df.columns:
        df = df[df["year"] == int(year)]
    df = df[df["driverId"] == driver_id]
    return df.reset_index(drop=True)
