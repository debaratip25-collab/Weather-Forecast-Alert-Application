from dataclasses import dataclass


@dataclass
class AlertThresholds:
    high_temp_c: float = 35.0
    high_humidity_pct: float = 85.0
    rain_alert_enabled: bool = True
    forecast_hours: int = 24