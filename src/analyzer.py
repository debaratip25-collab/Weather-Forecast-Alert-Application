from __future__ import annotations

from datetime import timedelta
import pandas as pd


def filter_next_hours(df: pd.DataFrame, hours: int) -> pd.DataFrame:
    if df.empty:
        return df

    start = df["dt_utc"].min()
    end = start + timedelta(hours=hours)
    return df[(df["dt_utc"] >= start) & (df["dt_utc"] <= end)].copy()


def build_forecast_summary(df_window: pd.DataFrame) -> dict:
    if df_window.empty:
        return {
            "window_rows": 0,
            "max_temp_c": None,
            "min_temp_c": None,
            "avg_humidity_pct": None,
            "total_rain_mm": None,
            "weather_mains": [],
        }

    return {
        "window_rows": int(len(df_window)),
        "max_temp_c": float(df_window["temp_c"].max()),
        "min_temp_c": float(df_window["temp_c"].min()),
        "avg_humidity_pct": float(df_window["humidity_pct"].mean()),
        "total_rain_mm": float(df_window["rain_3h_mm"].sum()),
        "weather_mains": sorted([w for w in df_window["weather_main"].dropna().unique().tolist()]),
    }