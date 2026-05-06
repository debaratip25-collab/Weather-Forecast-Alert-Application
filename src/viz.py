from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def plot_temp_humidity(df_window: pd.DataFrame, out_path: str) -> str:
    if df_window.empty:
        raise ValueError("No data to plot")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    x = df_window["dt_utc"]
    temp = df_window["temp_c"]
    hum = df_window["humidity_pct"]

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(x, temp, color="tab:red", label="Temp (°C)")
    ax1.set_ylabel("Temp (°C)", color="tab:red")
    ax1.tick_params(axis="y", labelcolor="tab:red")

    ax2 = ax1.twinx()
    ax2.plot(x, hum, color="tab:blue", label="Humidity (%)")
    ax2.set_ylabel("Humidity (%)", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")

    ax1.set_title("Forecast Window: Temperature & Humidity")
    ax1.set_xlabel("Datetime (UTC)")
    fig.autofmt_xdate()

    lines, labels = [], []
    for ax in (ax1, ax2):
        lns, lbls = ax.get_legend_handles_labels()
        lines += lns
        labels += lbls
    ax1.legend(lines, labels, loc="upper left")

    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path