from app.db import get_recent_readings

for label, end_time in [("Healthy", "2026-10-10 05:00:00"), ("Bearing wear", "2026-10-10 12:00:00")]:
    df = get_recent_readings("P-101", end_time)
    print(f"\n=== {label}: P-101, 10 minutes up to {end_time} ===")
    print(df[["timestamp", "vibration_mm_s", "bearing_temp_c"]])
    print("Average vibration:", round(df["vibration_mm_s"].mean(), 2))
