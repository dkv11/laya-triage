import pandas as pd

from app.config import ASSETS
from app.db import get_recent_readings
from app.rules import run_rules
from simulator.generate import FAULT_SCHEDULE

DAY_START = pd.Timestamp("2026-10-10")

FAULT_TEAM ={
    "bearing_wear": "mechanical",
    "phase_imbalance": "electrical",
    "flow_sensor_stuck": "instrumentation",
}

# 1. Walk through the day, remember the first time each (asset, rule) fires
first_seen = {}
for asset_id, baseline in ASSETS.items():
    for ts in pd.date_range(DAY_START + pd.Timedelta(minutes=10), periods=1430, freq="min"):
        end_time = ts.strftime("%Y-%m-%d %H:%M:%S")
        df = get_recent_readings(asset_id, end_time)
        for f in run_rules(df, baseline):
            key = (asset_id, f["team"])
            if key not in first_seen:
                first_seen[key] = (ts, f["rule"])

# 2. Compare with the answer key
print("Fault                        Started   Detected   Delay     By rule")
for fault in FAULT_SCHEDULE:
    start = DAY_START + pd.Timedelta(minutes=fault["start"])
    team = FAULT_TEAM[fault["fault"]]
    seen = first_seen.pop((fault["asset_id"], team), None)
    name = f"{fault['asset_id']} {fault['fault']}"
    if seen is None:
        print(f"{name:<28} {start:%H:%M}     MISSED")
    else:
        ts, rule = seen
        delay = int((ts - start).total_seconds() / 60)
        print(f"{name:<28} {start:%H:%M}     {ts:%H:%M}      {delay:<6}    {rule}")

for (asset_id, team), (ts, rule) in first_seen.items():
    print(f"FALSE ALARM: {asset_id} {team} ({rule}) at {ts:%H:%M}")
