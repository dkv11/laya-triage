import numpy as np
import pandas as pd
from app.config import ASSETS

rng = np.random.default_rng(42)

FAULT_SCHEDULE = [
    {"asset_id": "P-101", "fault": "bearing_wear", "start": 600, "end": 900},
    {"asset_id": "B-201", "fault": "phase_imbalance", "start": 200, "end": 500},
    {"asset_id": "P-101", "fault": "flow_sensor_stuck", "start": 1100, "end": 1300},
]


def normal_reading(base):
    """One healthy reading: normal value + small random noise."""
    return {
        "vibration_mm_s": base["vibration"] + rng.normal(0, 0.15),
        "bearing_temp_c": base["bearing_temp"] + rng.normal(0, 0.5),
        "current_r_a": base["current"] + rng.normal(0, 0.3),
        "current_y_a": base["current"] + rng.normal(0, 0.3),
        "current_b_a": base["current"] + rng.normal(0, 0.3),
        "flow_m3h": base["flow"] * (1 + rng.normal(0, 0.02)),
        "pressure_bar": base["pressure"] * (1 + rng.normal(0, 0.02)),
    }

def apply_bearing_wear(row, progress):
    """Worn bearing: vibration and bearing temperature slowly rise."""
    row["vibration_mm_s"] += 4.0 * progress
    row["bearing_temp_c"] += 15 * progress
    return row

def apply_phase_imbalance(row, progress):
    """Phase imbalance: R phase current rises, B phase drops, motor heats up."""
    row["current_r_a"] *= 1 + 0.25 * progress
    row["current_b_a"] *= 1 - 0.10 * progress
    row["bearing_temp_c"] += 8 * progress
    return row

def apply_flow_sensor_stuck(row, progress):
    """Flow sensor stuck: reading freezes at one value while the pump runs normally."""
    row["flow_m3h"] = 118.4
    return row

FAULT_FUNCTIONS = {
    "bearing_wear": apply_bearing_wear,
    "phase_imbalance": apply_phase_imbalance,
    "flow_sensor_stuck": apply_flow_sensor_stuck,
}



if __name__ == "__main__":
    timestamps = pd.date_range("2026-10-10", periods=1440,freq="min")

    rows = []

    for asset_id,base in ASSETS.items():
        # for ts in timestamps:
        #     row = normal_reading(base)            
        #     row["timestamp"] = ts
        #     row["asset_id"] = asset_id
        #     row["fault"] = "none"
        #     rows.append(row)
        for i, ts in enumerate(timestamps):
            row = normal_reading(base)
            row["timestamp"] = ts
            row["asset_id"] = asset_id
            row["fault"] = "none"

            for f in FAULT_SCHEDULE:
                if f["asset_id"] == asset_id and f["start"] <= i < f["end"]:
                    progress = (i - f["start"]) / (f["end"] - f["start"])
                    fault_fn = FAULT_FUNCTIONS[f["fault"]]
                    row = fault_fn(row, progress)
                    row["fault"] = f["fault"]

            rows.append(row)


    df = pd.DataFrame(rows)
    df = df.round({c: 2 for c in df.select_dtypes("number").columns})
    df = df[["timestamp", "asset_id"] + [c for c in df.columns if c not in ("timestamp", "asset_id")]]
    df.to_csv("data/readings.csv", index=False)
    print(f"Saved {len(df)} readings to data/readings.csv")