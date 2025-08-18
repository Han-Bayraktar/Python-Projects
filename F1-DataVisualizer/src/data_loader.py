# src/data_loader.py
import os
import pandas as pd

DATA_DIR_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def _read_csv_safe(path):
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)

def load_core(data_dir: str = DATA_DIR_DEFAULT):
    """
    Load core CSVs. Returns a dict with keys:
    drivers, races, results, constructors, sprint_results (optional)
    """
    drivers = _read_csv_safe(os.path.join(data_dir, "drivers.csv"))
    races = _read_csv_safe(os.path.join(data_dir, "races.csv"))
    results = _read_csv_safe(os.path.join(data_dir, "results.csv"))
    constructors = _read_csv_safe(os.path.join(data_dir, "constructors.csv"))
    sprint_results = _read_csv_safe(os.path.join(data_dir, "sprint_results.csv"))  # optional

    return {
        "drivers": drivers,
        "races": races,
        "results": results,
        "constructors": constructors,
        "sprint_results": sprint_results
    }

def build_enriched_results(drivers, races, results, constructors=None):
    """
    Merge results with drivers, races (year), and constructors (optional).
    Returns DataFrame with guaranteed: driverId, driverName, raceId, year, constructorId, constructorName, points, position, etc.
    """
    if results is None:
        raise FileNotFoundError("results.csv not found in data folder.")

    df = results.copy()
    # driverName
    if drivers is not None:
        if {"forename", "surname"}.issubset(drivers.columns):
            drivers = drivers.copy()
            drivers["driverName"] = (drivers["forename"].astype(str) + " " + drivers["surname"].astype(str)).str.strip()
        elif "name" in drivers.columns:
            drivers = drivers.copy()
            drivers["driverName"] = drivers["name"].astype(str)
        else:
            drivers = drivers.copy()
            drivers["driverName"] = drivers["driverId"].astype(str)
        df = df.merge(drivers[["driverId", "driverName"]].drop_duplicates(), on="driverId", how="left")
    else:
        df["driverName"] = df["driverId"].astype(str)

    # constructor name
    if constructors is not None and "constructorId" in df.columns:
        if "name" in constructors.columns:
            df = df.merge(constructors[["constructorId", "name"]].rename(columns={"name": "constructorName"}), on="constructorId", how="left")
        else:
            df = df.merge(constructors[["constructorId"]], on="constructorId", how="left")
            df["constructorName"] = df["constructorId"].astype(str)
    else:
        if "constructorId" in df.columns:
            df["constructorName"] = df["constructorId"].astype(str)

    # year/season from races
    if races is not None:
        # handle column name differences
        year_col = "year" if "year" in races.columns else ("season" if "season" in races.columns else None)
        if year_col is None:
            raise KeyError("races.csv must contain 'year' or 'season' column.")
        df = df.merge(races[["raceId", year_col]].rename(columns={year_col: "year"}), on="raceId", how="left")
    else:
        # no races.csv -> create empty year
        df["year"] = None

    return df
