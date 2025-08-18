# src/preprocessing.py
import pandas as pd

def get_drivers_for_year(enriched_results: pd.DataFrame, year: int):
    df = enriched_results.copy()
    df = df[df["year"] == int(year)]
    out = df[["driverId", "driverName"]].drop_duplicates().reset_index(drop=True)
    return out

def safe_int(i):
    try:
        return int(i)
    except:
        return None
