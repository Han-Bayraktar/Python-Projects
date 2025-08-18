# src/visualizer.py
import matplotlib.pyplot as plt
from textwrap import shorten
import streamlit as st
import pandas as pd

def _auto_height(n: int, base: float = 0.45, min_h: float = 4.0, max_h: float = 20.0) -> float:
    return max(min_h, min(max_h, base * max(5, n)))

def plot_top_driver_points(points_df: pd.DataFrame, top_n: int = 15):
    data = points_df.head(top_n).copy()
    if "driverName" not in data.columns and "driverId" in data.columns:
        data["driverName"] = data["driverId"].astype(str)
    data["label"] = data["driverName"].apply(lambda s: shorten(str(s), width=28, placeholder="…"))
    h = _auto_height(len(data))
    fig, ax = plt.subplots(figsize=(10, h))
    ax.barh(data["label"], data["points"])
    ax.invert_yaxis()
    ax.set_xlabel("Points")
    ax.set_title(f"Top {min(top_n, len(points_df))} Drivers by Points")
    for i, v in enumerate(data["points"]):
        ax.text(v, i, f" {int(v)}", va='center', fontsize=8)
    fig.tight_layout()
    return fig

def plot_constructor_points(constructors_df: pd.DataFrame, top_n: int = 15):
    if "constructorName" not in constructors_df.columns and "constructorId" in constructors_df.columns:
        constructors_df["constructorName"] = constructors_df["constructorId"].astype(str)
    data = constructors_df.head(top_n).copy()
    data["label"] = data["constructorName"].apply(lambda s: shorten(str(s), width=28, placeholder="…"))
    h = _auto_height(len(data))
    fig, ax = plt.subplots(figsize=(10, h))
    ax.barh(data["label"], data["points"])
    ax.invert_yaxis()
    ax.set_xlabel("Points")
    ax.set_title("Top Constructors by Points")
    for i, v in enumerate(data["points"]):
        ax.text(v, i, f" {int(v)}", va='center', fontsize=8)
    fig.tight_layout()
    return fig

def plot_championship_pie(counts_df: pd.DataFrame, top_n: int = 10):
    data = counts_df.copy()
    if len(data) == 0:
        fig, ax = plt.subplots(figsize=(6,3))
        ax.text(0.5,0.5,"No championship data", ha='center', va='center')
        ax.axis('off')
        return fig
    data_top = data.head(top_n)
    labels = data_top["driverName"].astype(str)
    sizes = data_top["championships"].astype(int)
    fig, ax = plt.subplots(figsize=(6,6))
    ax.pie(sizes, labels=labels, autopct='%1.0f%%', startangle=140)
    ax.set_title("Championship Shares (Top {})".format(top_n))
    fig.tight_layout()
    return fig

def plot_driver_season_progress(driver_results_df: pd.DataFrame):
    if driver_results_df is None or driver_results_df.empty:
        fig, ax = plt.subplots(figsize=(6,3))
        ax.text(0.5,0.5,"No data", ha='center', va='center')
        ax.axis('off')
        return fig
    df = driver_results_df.copy()
    # ensure ordering by raceId (or round)
    if "round" in df.columns:
        df = df.sort_values("round")
        x = df["round"].astype(str)
    else:
        df = df.sort_values("raceId")
        x = df["raceId"].astype(str)
    df["cumulative"] = df["points"].cumsum()
    fig, ax = plt.subplots(figsize=(10,4))
    ax.plot(x, df["cumulative"], marker='o')
    ax.set_xlabel("Race")
    ax.set_ylabel("Cumulative Points")
    ax.set_title("Season Progress (Cumulative Points)")
    plt.xticks(rotation=45)
    fig.tight_layout()
    return fig

def show_results_table(df: pd.DataFrame):
    if df is None or df.empty:
        st.write("No results to show.")
        return
    st.dataframe(df)
