"""Strategy simulator for F1 race strategy analysis."""

import json
from pathlib import Path

import joblib  # pyright: ignore[reportMissingImports]
import numpy as np
import pandas as pd

MODEL_PATH = Path("models") / "lap_time_model.pkl"
FEATURE_PATH = Path("models") / "lap_model_features.json"


def load_model_and_features():
    """Load the trained model and feature columns."""
    model = joblib.load(MODEL_PATH)
    with open(FEATURE_PATH) as f:
        feature_columns = json.load(f)
    print(f"Loaded model and {len(feature_columns)} feature columns")
    return model, feature_columns


def simulate_simple_lap(model, feature_columns):
    """Simulate a single lap with example data."""
    # Example row similar to training data
    example = {
        "year": 2021,
        "round": 1,
        "lap_number": 10,
        "lap_in_stint": 5,
        "fuel_lap_from_end": 47,
        "stint": 1,
        "tyre_life": 5,
        "position": 1,
        "driver_code": "VER",
        "compound": "MEDIUM",
        "race_name": "Bahrain Grand Prix",
    }

    df = pd.DataFrame([example])
    df = pd.get_dummies(
        df, columns=["driver_code", "compound", "race_name"], drop_first=True
    )
    df = df.reindex(columns=feature_columns, fill_value=0)

    pred = model.predict(df)
    print(f"Predicted lap time: {pred[0]:.3f} seconds")


def simulate_strategy(
    model,
    feature_columns,
    year,
    round_number,
    race_name,
    driver_code,
    total_laps,
    stints,
    pit_loss_s=22.0,
    starting_position=1,
):
    """
    Simulate a race strategy and return total time and lap times.

    Args:
        model: Trained lap time prediction model
        feature_columns: List of feature column names
        year: Race year
        round_number: Race round number
        race_name: Race name
        driver_code: Driver code (e.g., "VER")
        total_laps: Total number of laps in the race
        stints: List of stint dictionaries with "compound" and "laps" keys
        pit_loss_s: Time lost in pit stop (seconds)
        starting_position: Starting grid position

    Returns:
        Tuple of (total_time, lap_times)
    """
    lap_times = []
    current_lap = 0
    laps_remaining = total_laps
    stint_index = 0

    for stint in stints:
        stint_index += 1
        compound = stint["compound"]
        stint_len = min(stint["laps"], laps_remaining)

        for i in range(stint_len):
            current_lap += 1
            lap_in_stint = i + 1
            fuel_lap_from_end = total_laps - current_lap
            tyre_life = lap_in_stint

            df = pd.DataFrame(
                [
                    {
                        "year": year,
                        "round": round_number,
                        "race_name": race_name,
                        "driver_code": driver_code,
                        "lap_number": current_lap,
                        "lap_in_stint": lap_in_stint,
                        "fuel_lap_from_end": fuel_lap_from_end,
                        "stint": stint_index,
                        "compound": compound,
                        "tyre_life": tyre_life,
                        "position": starting_position,
                    }
                ]
            )
            df = pd.get_dummies(
                df, columns=["driver_code", "compound", "race_name"], drop_first=True
            )
            df = df.reindex(columns=feature_columns, fill_value=0)

            pred = float(model.predict(df)[0])
            lap_times.append(pred)

        laps_remaining -= stint_len
        if laps_remaining > 0:
            lap_times.append(pit_loss_s)

    total_time = sum(lap_times)
    return total_time, lap_times


def main():
    """Main function for testing strategy simulation."""
    # Load model + feature columns
    model, feature_columns = load_model_and_features()

    # Total laps for the race you want to simulate
    total_laps = 57  # example: Bahrain 2021

    # Define example strategies
    one_stop = [
        {"compound": "MEDIUM", "laps": 27},
        {"compound": "HARD", "laps": 30},
    ]

    two_stop = [
        {"compound": "SOFT", "laps": 15},
        {"compound": "MEDIUM", "laps": 20},
        {"compound": "HARD", "laps": 22},
    ]

    # Simulate both
    t1, laps1 = simulate_strategy(
        model,
        feature_columns,
        year=2021,
        round_number=1,
        race_name="Bahrain Grand Prix",
        driver_code="VER",
        total_laps=total_laps,
        stints=one_stop,
        pit_loss_s=22.0,
        starting_position=1,
    )

    t2, laps2 = simulate_strategy(
        model,
        feature_columns,
        year=2021,
        round_number=1,
        race_name="Bahrain Grand Prix",
        driver_code="VER",
        total_laps=total_laps,
        stints=two_stop,
        pit_loss_s=22.0,
        starting_position=1,
    )

    # Print results
    print(f"One-stop total time : {t1:.2f} s  (≈ {t1/60:.2f} min)")
    print(f"Two-stop total time : {t2:.2f} s  (≈ {t2/60:.2f} min)")
    diff = t2 - t1
    print(f"Difference (two-stop - one-stop): {diff:.2f} s")
    if diff < 0:
        print("→ Two-stop is faster.")
    elif diff > 0:
        print("→ One-stop is faster.")
    else:
        print("→ Both strategies are equal according to the model.")


if __name__ == "__main__":
    main()

