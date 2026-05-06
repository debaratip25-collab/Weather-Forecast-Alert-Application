from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import pandas as pd


def timestamp_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_reports(df_window: pd.DataFrame, alerts: list[dict], city: str) -> dict:
    Path("reports").mkdir(exist_ok=True)

    tag = timestamp_tag()
    safe_city = city.replace(" ", "_")

    csv_path = f"reports/forecast_{safe_city}_{tag}.csv"
    json_path = f"reports/alerts_{safe_city}_{tag}.json"

    df_window.to_csv(csv_path, index=False)

    Path(json_path).write_text(
        json.dumps(
            {"city": city, "generated_at": datetime.now().isoformat(), "alerts": alerts},
            indent=2,
        ),
        encoding="utf-8",
    )

    return {"csv_path": csv_path, "json_path": json_path}