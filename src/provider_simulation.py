import json
from pathlib import Path


class SimulationProvider:
    def __init__(self, sample_path: str):
        self.sample_path = sample_path

    def fetch_forecast(self, city: str) -> dict:
        path = Path(self.sample_path)
        if not path.exists():
            raise FileNotFoundError(f"Simulation data file not found: {self.sample_path}")
        return json.loads(path.read_text(encoding="utf-8"))