from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd


def _safe_get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def parse_openweather_forecast_to_df(payload: dict) -> pd.DataFrame:
    rows = []
    items = payload.get("list", [])

    for item in items:
        dt_unix = item.get("dt")
        if dt_unix is None:
            continue

        dt_utc = datetime.fromtimestamp(dt_unix, tz=timezone.utc)

        temp_c = _safe_get(item, "main", "temp")
        humidity = _safe_get(item, "main", "humidity")
        wind_speed = _safe_get(item, "wind", "speed")

        weather_main = None
        weather_desc = None
        weather_arr = item.get("weather") or []
        if weather_arr:
            weather_main = weather_arr[0].get("main")
            weather_desc = weather_arr[0].get("description")

        rain_3h = _safe_get(item, "rain", "3h", default=0.0)
        if rain_3h is None:
            rain_3h = 0.0

        rows.append(
            {
                "dt_utc": dt_utc,
                "temp_c": temp_c,
                "humidity_pct": humidity,
                "wind_speed": wind_speed,
                "weather_main": weather_main,
                "weather_desc": weather_desc,
                "rain_3h_mm": float(rain_3h),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    return df.sort_values("dt_utc").reset_index(drop=True)