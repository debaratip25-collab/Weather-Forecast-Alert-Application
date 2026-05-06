from __future__ import annotations

import os
from io import StringIO
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.config import AlertThresholds
from src.provider_openweather import OpenWeatherProvider
from src.provider_simulation import SimulationProvider
from src.parser import parse_openweather_forecast_to_df
from src.analyzer import filter_next_hours, build_forecast_summary
from src.alerts import generate_alerts
from src.viz import plot_temp_humidity
from src.reporting import save_reports
from src.multi_city_reporting import save_multi_city_alerts_json

DEFAULT_FORECAST_HOURS = 24

st.set_page_config(page_title="Weather Forecast & Alert Dashboard", layout="wide")

# ---- UI: Bigger fonts for readability ----
st.markdown(
    """
    <style>
      /* Base app font */
      html, body, [class*="css"]  {
        font-size: 16px !important;
      }

      /* Sidebar widgets + labels */
      section[data-testid="stSidebar"] * {
        font-size: 16px !important;
      }

      /* Headings */
      h1 { font-size: 34px !important; }
      h2 { font-size: 26px !important; }
      h3 { font-size: 20px !important; }

      /* Dataframe/table text */
      .stDataFrame, .stTable {
        font-size: 16px !important;
      }

      /* Metric widget text */
      div[data-testid="stMetricValue"] {
        font-size: 26px !important;
      }
      div[data-testid="stMetricLabel"] {
        font-size: 16px !important;
      }

      /* Alerts text blocks (markdown/paragraphs) */
      .stMarkdown p {
        font-size: 16px !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def severity_badge(sev: str) -> str:
    sev = (sev or "").upper()
    if sev == "HIGH":
        return "HIGH"
    if sev == "MEDIUM":
        return "MEDIUM"
    return "LOW"


@st.cache_data(ttl=300)
def fetch_payload_api(city: str) -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENWEATHER_API_KEY not found. Create a .env file (see .env.example).")

    provider = OpenWeatherProvider(api_key=api_key, units="metric")
    return provider.fetch_forecast(city)


def analyze_city_from_payload(payload: dict, thresholds: AlertThresholds, fallback_city: str) -> dict:
    df = parse_openweather_forecast_to_df(payload)
    df_window = filter_next_hours(df, thresholds.forecast_hours)
    summary = build_forecast_summary(df_window)
    alerts = generate_alerts(df_window, thresholds)

    city_name = payload.get("city", {}).get("name") or fallback_city

    return {"city": city_name, "df_window": df_window, "summary": summary, "alerts": alerts}


def main() -> None:
    # Load .env from the same folder as this file (more reliable in Streamlit)
    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

    st.title("Weather Forecast & Alert Application (Advanced)")
    st.caption("Single-city + Multi-city monitoring • API mode + Simulation mode • Alerts • Reports • Charts")

    with st.sidebar:
        st.header("Mode")
        mode = st.selectbox("Mode", ["sim", "api"], index=0)

        st.caption(f"API key loaded: {bool(os.getenv('OPENWEATHER_API_KEY'))}")

        st.header("Alert thresholds (applied to analysis window)")
        hours = st.slider("Forecast window (hours)", 6, 48, DEFAULT_FORECAST_HOURS, step=3)
        high_temp = st.number_input("High temp threshold (°C)", value=35.0, step=1.0)
        high_humidity = st.number_input("High humidity threshold (%)", value=85.0, step=1.0)
        rain_alert = st.checkbox("Enable rain alert", value=True)

        thresholds = AlertThresholds(
            high_temp_c=float(high_temp),
            high_humidity_pct=float(high_humidity),
            rain_alert_enabled=bool(rain_alert),
            forecast_hours=int(hours),
        )

        st.divider()
        st.header("Single city")
        city = st.text_input("City", value="Kolkata")
        sample_path = st.text_input("Simulation JSON path", value="data/sample_openweather_forecast.json")
        run_single = st.button("Run Single City", type="primary")

        st.divider()
        st.header("Multi-city monitoring (CSV)")
        st.write("Upload a CSV with a column named **city** (example in `data/sample_cities.csv`).")
        uploaded = st.file_uploader("Upload cities CSV", type=["csv"])
        run_multi = st.button("Run Multi-City Analysis")

    # -------------------------
    # SINGLE CITY
    # -------------------------
    if run_single:
        try:
            if mode == "api":
                payload = fetch_payload_api(city)
                result = analyze_city_from_payload(payload, thresholds, fallback_city=city)
            else:
                payload = SimulationProvider(sample_path=sample_path).fetch_forecast(city)
                # IMPORTANT: override sample payload city so outputs match user city
                payload["city"] = {"name": city}
                result = analyze_city_from_payload(payload, thresholds, fallback_city=city)
        except Exception as e:
            st.exception(e)
            return

        st.subheader(f"Single City Result — {result['city']}")
        c1, c2 = st.columns([1, 1])

        with c1:
            s = result["summary"]
            st.write("### Forecast Summary")
            st.metric("Rows analyzed", s["window_rows"])
            st.metric("Max Temp (°C)", s["max_temp_c"])
            st.metric("Avg Humidity (%)", s["avg_humidity_pct"])
            st.metric("Total Rain (mm)", s["total_rain_mm"])
            st.write("Weather types:", s["weather_mains"])

        with c2:
            st.write("### Alerts")
            for a in result["alerts"]:
                st.write(f"**{severity_badge(a['severity'])} — {a['type']}**")
                st.write(a["message"])
                st.caption(f"Details: {a['details']}")
                st.divider()

        st.write("### Forecast Window Data")
        st.dataframe(result["df_window"], use_container_width=True)

        # Save per-city reports
        try:
            paths = save_reports(result["df_window"], result["alerts"], result["city"])
            st.success(f"Saved CSV: {paths['csv_path']}")
            st.success(f"Saved JSON: {paths['json_path']}")
        except Exception as e:
            st.warning(f"Report save failed: {e}")

        # Plot chart
        try:
            chart_path = f"outputs/chart_{result['city'].replace(' ', '_')}.png"
            plot_path = plot_temp_humidity(result["df_window"], chart_path)
            st.write("### Chart")
            st.image(plot_path, caption=plot_path, use_column_width=True)
        except Exception as e:
            st.warning(f"Plot failed: {e}")

        return

    # -------------------------
    # MULTI CITY
    # -------------------------
    if run_multi:
        if uploaded is None:
            st.error("Please upload a CSV file first.")
            return

        try:
            content = uploaded.getvalue().decode("utf-8", errors="replace")
            cities_df = pd.read_csv(StringIO(content))
        except Exception as e:
            st.exception(e)
            return

        if "city" not in cities_df.columns:
            st.error("CSV must contain a column named 'city'.")
            return

        cities = [str(x).strip() for x in cities_df["city"].dropna().tolist() if str(x).strip()]
        if not cities:
            st.error("No valid cities found in the CSV.")
            return

        st.subheader(f"Multi-City Monitoring ({len(cities)} cities) — Mode: {mode}")

        rows: list[dict] = []
        errors: list[dict] = []
        all_city_results: list[dict] = []

        for c in cities:
            try:
                # Fetch payload
                if mode == "api":
                    payload = fetch_payload_api(c)
                else:
                    payload = SimulationProvider(sample_path="data/sample_openweather_forecast.json").fetch_forecast(c)
                    # IMPORTANT: override sample payload city so outputs match CSV city
                    payload["city"] = {"name": c}

                # Analyze
                result = analyze_city_from_payload(payload, thresholds, fallback_city=c)

                # Save per-city reports for EACH city (CSV + JSON)
                try:
                    save_reports(result["df_window"], result["alerts"], result["city"])
                except Exception as e:
                    errors.append({"city": c, "error": f"Report save failed: {e}"})

                # Save per-city chart for EACH city
                try:
                    chart_path = f"outputs/chart_{result['city'].replace(' ', '_')}.png"
                    plot_temp_humidity(result["df_window"], chart_path)
                except Exception as e:
                    errors.append({"city": c, "error": f"Chart failed: {e}"})

                # Store for combined JSON artifact
                all_city_results.append(
                    {
                        "city": result["city"],
                        "summary": result["summary"],
                        "alerts": result["alerts"],
                    }
                )

                # Build summary row
                s = result["summary"]
                alert_types = [a["type"] for a in result["alerts"]]

                highest_sev = "LOW"
                if any(a["severity"] == "HIGH" for a in result["alerts"]):
                    highest_sev = "HIGH"
                elif any(a["severity"] == "MEDIUM" for a in result["alerts"]):
                    highest_sev = "MEDIUM"

                rows.append(
                    {
                        "city": result["city"],
                        "max_temp_c": s["max_temp_c"],
                        "avg_humidity_pct": s["avg_humidity_pct"],
                        "total_rain_mm": s["total_rain_mm"],
                        "highest_severity": highest_sev,
                        "alerts": ", ".join(alert_types),
                    }
                )

            except Exception as e:
                errors.append({"city": c, "error": str(e)})

        results_df = pd.DataFrame(rows)
        if not results_df.empty:
            results_df = results_df.sort_values(["highest_severity", "city"], ascending=[False, True])

        st.write("### City Summary Table")
        st.dataframe(results_df, use_container_width=True)

        # Save multi-city summary CSV
        try:
            os.makedirs("reports", exist_ok=True)
            out_path = "reports/multi_city_summary.csv"
            results_df.to_csv(out_path, index=False)
            st.success(f"Saved multi-city summary CSV: {out_path}")
        except Exception as e:
            st.warning(f"Could not save multi-city summary: {e}")

        # Save combined JSON for portfolio
        try:
            thresholds_dict = {
                "forecast_hours": thresholds.forecast_hours,
                "high_temp_c": thresholds.high_temp_c,
                "high_humidity_pct": thresholds.high_humidity_pct,
                "rain_alert_enabled": thresholds.rain_alert_enabled,
            }

            json_out = save_multi_city_alerts_json(
                results=all_city_results,
                thresholds=thresholds_dict,
                mode=mode,
                source=uploaded.name,
                out_path="reports/multi_city_alerts.json",
            )
            st.success(f"Saved multi-city alerts JSON: {json_out}")
        except Exception as e:
            st.warning(f"Could not save multi-city alerts JSON: {e}")

        if errors:
            st.write("### Errors (cities that failed)")
            st.dataframe(pd.DataFrame(errors), use_container_width=True)

        st.write("### HIGH Severity Cities")
        if results_df.empty:
            st.info("No results generated.")
        else:
            high_df = results_df[results_df["highest_severity"] == "HIGH"]
            if high_df.empty:
                st.info("No HIGH severity cities in this run.")
            else:
                st.dataframe(high_df, use_container_width=True)

        return

    st.info("Choose Single City or Multi-City in the sidebar and run analysis.")


if __name__ == "__main__":
    main()