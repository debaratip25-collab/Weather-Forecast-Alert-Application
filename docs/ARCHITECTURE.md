# Architecture — Weather Forecast & Alert Application (Advanced)

## Goal
Convert raw forecast data into **actionable alerts** and **business-friendly reports** via:
- Single-city analysis
- Multi-city monitoring (CSV upload)

## High-level pipeline
```
[User Input]
  - Mode: API / Simulation
  - City OR Cities CSV
  - Thresholds (temp/humidity/rain)
  - Forecast window (default 24h)
        |
        v
[Provider Layer]
  - OpenWeatherProvider (requests -> JSON)
  - SimulationProvider (local JSON -> dict)
        |
        v
[Parser]
  - parse JSON -> pandas DataFrame (dt_utc, temp, humidity, rain...)
        |
        v
[Analyzer]
  - filter next N hours
  - compute max temp, avg humidity, total rain, weather types
        |
        v
[Alert Engine]
  - rule checks -> alerts with severity
        |
        v
[Outputs]
  - Streamlit UI tables/cards
  - CSV/JSON reports
  - PNG chart
  - Multi-city combined JSON artifact
```

## Modules (src/)
- `provider_openweather.py`: API requests + error handling
- `provider_simulation.py`: load sample JSON for offline demo
- `parser.py`: normalize API JSON to DataFrame
- `analyzer.py`: forecast window filter + summary stats
- `alerts.py`: alert rules + severity
- `reporting.py`: per-city CSV/JSON export
- `multi_city_reporting.py`: combined JSON export for multi-city runs
- `viz.py`: Matplotlib plotting

## Data contracts (important)
The analysis expects a DataFrame with:
- `dt_utc`, `temp_c`, `humidity_pct`, `rain_3h_mm`, `weather_main`

This contract makes the system easy to extend (new providers / new alerts).