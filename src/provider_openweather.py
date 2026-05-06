import requests


class OpenWeatherProvider:
    def __init__(self, api_key: str, units: str = "metric"):
        self.api_key = api_key
        self.units = units

    def fetch_forecast(self, city: str) -> dict:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {"q": city, "appid": self.api_key, "units": self.units}

        resp = requests.get(url, params=params, timeout=20)

        if resp.status_code == 401:
            raise RuntimeError("Unauthorized (401). Check OPENWEATHER_API_KEY in .env")
        if resp.status_code == 404:
            raise RuntimeError(f"City not found (404): {city}")
        if not resp.ok:
            raise RuntimeError(f"API request failed: {resp.status_code} - {resp.text}")

        return resp.json()