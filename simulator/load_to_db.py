import pandas as pd

from app.db import get_connection, init_db

if __name__ == "__main__":
    init_db()

    # Load the CSV file into a DataFrame
    df = pd.read_csv("data/readings.csv")
    df = df.drop(columns=["fault"])

    # Insert the data into the database
    with get_connection() as conn:
        conn.execute("DELETE FROM readings")  # Clear existing data
        df.to_sql("readings", conn, if_exists="append", index=False)

    print(f"Loaded {len(df)} readings into data/laya.db")