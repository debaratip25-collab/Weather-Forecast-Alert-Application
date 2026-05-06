from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def save_multi_city_alerts_json(
    *,
    results: list[dict],
    thresholds: dict,
    mode: str,
    source: str,
    out_path: str = "reports/multi_city_alerts.json",
) -> str:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "mode": mode,
        "source": source,
        "thresholds": thresholds,
        "city_results": results,
    }

    Path(out_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path