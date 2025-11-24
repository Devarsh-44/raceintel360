import os
import sqlite3
from pathlib import Path

import pandas as pd


# ---------- CONFIG ----------

DB_PATH = "raceintel.db"           # adjust if your DB lives elsewhere
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "lap_model_dataset.csv"


# ---------- HELPERS ----------

def connect_db(db_path: str) -> sqlite3.Connection:
    """Create a SQLite connection."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    return conn


def load_raw_laps(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Load joined lap + race + driver data into a DataFrame.

    You can add or remove columns depending on what you need.
    """
    query = """
    SELECT
        l.lap_id,
        l.race_id,
        l.driver_id,
        r.year,
        r.round,
        r.name      AS race_name,
        d.code      AS driver_code,
        l.lap_number,
        l.lap_time_secs,
        l.stint,
        l.compound,
        l.tyre_life,
        l.position,
        l.pit_stop
    FROM lap   AS l
    JOIN race  AS r ON l.race_id   = r.race_id
    JOIN driver AS d ON l.driver_id = d.driver_id
    WHERE l.lap_time_secs IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    return df


def clean_and_engineer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Basic cleaning + feature engineering for lap-time model.

    Add your own ideas here if needed.
    """
    # Drop obvious bad lap times (<= 0 or extremely long)
    df = df[df["lap_time_secs"] > 0]

    # Example: per-race median filter to remove extreme outliers (e.g. in-laps)
    grouped = df.groupby(["race_id", "driver_id"])
    med = grouped["lap_time_secs"].transform("median")
    df["lap_time_med_ratio"] = df["lap_time_secs"] / med
    df = df[df["lap_time_med_ratio"] < 2.0]   # keep laps < 2x median
    df = df.drop(columns=["lap_time_med_ratio"])

    # Feature: lap index within stint
    df = df.sort_values(["race_id", "driver_id", "stint", "lap_number"])
    df["lap_in_stint"] = (
        df.groupby(["race_id", "driver_id", "stint"])
          .cumcount() + 1
    )

    # Feature: simple fuel proxy (how early in the race the lap is)
    max_laps = df.groupby("race_id")["lap_number"].transform("max")
    df["fuel_lap_from_end"] = max_laps - df["lap_number"]

    # Optional: normalise compound strings
    df["compound"] = df["compound"].str.upper().fillna("UNKNOWN")

    # Keep only columns you plan to model on
    keep_cols = [
        "race_id",
        "driver_id",
        "driver_code",
        "year",
        "round",
        "race_name",
        "lap_number",
        "lap_in_stint",
        "fuel_lap_from_end",
        "stint",
        "compound",
        "tyre_life",
        "position",
        "pit_stop",
        "lap_time_secs",   # target
    ]
    df = df[keep_cols]

    return df


def save_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Save dataset as CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved dataset to: {output_path}  (rows={len(df)}, cols={len(df.columns)})")


# ---------- MAIN ----------

def main() -> None:
    conn = connect_db(DB_PATH)
    try:
        raw_df = load_raw_laps(conn)
    finally:
        conn.close()

    print("Raw dataframe shape:", raw_df.shape)
    print("Raw columns:", list(raw_df.columns))

    dataset_df = clean_and_engineer(raw_df)

    print("Cleaned dataframe shape:", dataset_df.shape)
    print("Cleaned columns:", list(dataset_df.columns))

    save_dataset(dataset_df, OUTPUT_FILE)


if __name__ == "__main__":
    main()
