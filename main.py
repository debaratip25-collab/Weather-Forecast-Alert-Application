from __future__ import annotations

import argparse
import os
from dotenv import load_dotenv

from src.config import AlertThresholds
from src.provider_openweather import OpenWeatherProvider
from src.provider_simulation import SimulationProvider
from src.parser import parse_openweather_forecast_to_df
from src.analyzer import filter_next_hours, build_forecast_summary
from src.alerts import generate_alerts
from src.viz import plot_temp_humidity
from src.reporting import save_reports


def parse_args():
    p = argparse.ArgumentParser(description="Weather Forecast & Alert Application")
    p.add_argument("--city", type=str, default="Kolkata", help="City name (API mode)")
    p.add_argument("--mode", type=str, choices=["api", "sim"], default="sim", help="api or sim mode")
    p.add_argument("--sample", type=str, default="data/sample_openweather_forecast.json", help="Simulation JSON path")

    p.add_argument("--hours", type=int, default=24, help="Forecast window hours (default: 24)")
    p.add_argument("--high-temp", type=float, default=35.0, help="High temperature threshold in °C")
    p.add_argument("--high-humidity", type=float, default=85.0, help="High humidity threshold in %")
    p.add_argument("--no-rain-alert", action="store_true", help="Disable rain alert")

    return p.parse_args()


def main():
    args = parse_args()

    thresholds = AlertThresholds(
        high_temp_c=float(args.high_temp),
        high_humidity_pct=float(args.high_humidity),
        rain_alert_enabled=not bool(args.no_rain_alert),
        forecast_hours=int(args.hours),
    )

    # Provider selection
    if args.mode == "api":
        load_dotenv()
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENWEATHER_API_KEY not found. Create a .env file (see .env.example).")

        provider = OpenWeatherProvider(api_key=api_key, units="metric")
        payload = provider.fetch_forecast(args.city)
        city = args.city
    else:
        provider = SimulationProvider(sample_path=args.sample)
        payload = provider.fetch_forecast(args.city)
        city = payload.get("city", {}).get("name") or args.city

    # Parse + analyze
    df = parse_openweather_forecast_to_df(payload)
    df_window = filter_next_hours(df, thresholds.forecast_hours)
    summary = build_forecast_summary(df_window)
    alerts = generate_alerts(df_window, thresholds)

    # Display outputs
    print("\n==============================")
    print(" Weather Forecast & Alerts")
    print("==============================")
    print(f"City: {city}")
    print(f"Mode: {args.mode}")
    print(f"Forecast window: next {thresholds.forecast_hours} hours")

    print("\n--- Forecast Summary ---")
    print(f"Rows analyzed: {summary['window_rows']}")
    print(f"Max Temp (°C): {summary['max_temp_c']}")
    print(f"Min Temp (°C): {summary['min_temp_c']}")
    print(f"Avg Humidity (%): {summary['avg_humidity_pct']}")
    print(f"Total Rain (mm): {summary['total_rain_mm']}")
    print(f"Weather Types: {summary['weather_mains']}")

    print("\n--- Alerts ---")
    for a in alerts:
        print(f"[{a['severity']}] {a['type']}: {a['message']}")

    # Save reports
    paths = save_reports(df_window, alerts, city)

    # Plot
    chart_path = f"outputs/chart_{city.replace(' ', '_')}.png"
    try:
        plot_path = plot_temp_humidity(df_window, chart_path)
    except Exception as e:
        plot_path = None
        print(f"\n(Plot skipped) Reason: {e}")

    print("\n--- Saved Files ---")
    print(f"CSV Report:  {paths['csv_path']}")
    print(f"JSON Alerts: {paths['json_path']}")
    if plot_path:
        print(f"Chart PNG:   {plot_path}")
    print("==============================\n")


if __name__ == "__main__":
    main()