from app.config import ASSETS
from app.db import get_recent_readings
from app.rules import check_bearing_wear, check_phase_imbalance, check_flow_sensor_stuck

RULES = [check_bearing_wear, check_phase_imbalance, check_flow_sensor_stuck]

CASES = [
    ("P-101", "2026-10-10 05:00:00", "healthy"),
    ("P-101", "2026-10-10 14:50:00", "bearing_wear"),
    ("B-201", "2026-10-10 08:10:00", "phase_imbalance"),
    ("P-101", "2026-10-10 21:00:00", "flow_sensor_stuck"),
]

for asset_id, end_time, expected in CASES:
    df = get_recent_readings(asset_id, end_time)
    findings = [f for rule in RULES if (f := rule(df, ASSETS[asset_id]))]
    print(f"\n{asset_id} @ {end_time}  (expected: {expected})")
    if not findings:
        print("   no findings")
    for f in findings:
        print(f"   [{f['severity']}] {f['team']}: {f['rule']} - {f['evidence']}")
