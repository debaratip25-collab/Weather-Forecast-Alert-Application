from __future__ import annotations

from dataclasses import asdict
import pandas as pd
from src.config import AlertThresholds


def generate_alerts(df_window: pd.DataFrame, thresholds: AlertThresholds) -> list[dict]:
    alerts: list[dict] = []

    if df_window.empty:
        return [{
            "type": "NO_DATA",
            "severity": "HIGH",
            "message": "No forecast data available to analyze.",
            "details": asdict(thresholds),
        }]

    max_temp = float(df_window["temp_c"].max())
    avg_humidity = float(df_window["humidity_pct"].mean())
    total_rain = float(df_window["rain_3h_mm"].sum())

    if max_temp >= thresholds.high_temp_c:
        alerts.append({
            "type": "HIGH_TEMPERATURE",
            "severity": "HIGH",
            "message": f"High temperature expected (max {max_temp:.1f}°C) in next {thresholds.forecast_hours}h.",
            "details": {"max_temp_c": max_temp, **asdict(thresholds)},
        })

    if avg_humidity >= thresholds.high_humidity_pct:
        alerts.append({
            "type": "HIGH_HUMIDITY",
            "severity": "MEDIUM",
            "message": f"High humidity expected (avg {avg_humidity:.1f}%) in next {thresholds.forecast_hours}h.",
            "details": {"avg_humidity_pct": avg_humidity, **asdict(thresholds)},
        })

    if thresholds.rain_alert_enabled and total_rain > 0.0:
        alerts.append({
            "type": "RAIN",
            "severity": "MEDIUM",
            "message": f"Rain expected (total ~{total_rain:.1f} mm) in next {thresholds.forecast_hours}h.",
            "details": {"total_rain_mm": total_rain, **asdict(thresholds)},
        })

    mains = set([str(x).lower() for x in df_window["weather_main"].dropna().tolist()])
    if "thunderstorm" in mains:
        alerts.append({
            "type": "STORM",
            "severity": "HIGH",
            "message": "Thunderstorm conditions detected in forecast window.",
            "details": {"weather_mains": sorted(list(mains)), **asdict(thresholds)},
        })

    if not alerts:
        alerts.append({
            "type": "NO_ALERTS",
            "severity": "LOW",
            "message": f"No alert thresholds crossed in next {thresholds.forecast_hours}h.",
            "details": asdict(thresholds),
        })

    return alerts