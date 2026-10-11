import pandas as pd

from app.rules import phase_imbalance_pct

df = pd.read_csv("data/readings.csv")

for asset_id, g in df.groupby("asset_id"):
    r = g["current_r_a"].rolling(10).mean()
    y = g["current_y_a"].rolling(10).mean()
    b = g["current_b_a"].rolling(10).mean()
    imbalance = phase_imbalance_pct(r, y, b)

    all_healthy = (g["fault"] == "none").astype(int).rolling(10).sum() == 10
    healthy = imbalance[all_healthy]

    print(f"{asset_id}: healthy imbalance max {healthy.max():.2f}%, "
          f"99th percentile {healthy.quantile(0.99):.2f}%")
