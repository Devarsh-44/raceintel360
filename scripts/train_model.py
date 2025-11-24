import os
from pathlib import Path

import pandas as pd

from sklearn.model_selection import train_test_split  
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib



DATA_PATH = Path("data") / "lap_model_dataset.csv"
MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "lap_time_model.pkl"




def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    df = pd.read_csv(path)
    print("Loaded dataset:", df.shape)
    return df


def prepare_features(df: pd.DataFrame):
    # Target: lap time in seconds
    y = df["lap_time_secs"]

    # Numeric features (example)
    numeric_cols = [
        "year",
        "round",
        "lap_number",
        "lap_in_stint",
        "fuel_lap_from_end",
        "stint",
        "tyre_life",
        "position",
    ]

    # Categorical features (example)
    cat_cols = [
        "driver_code",
        "compound",
        "race_name",
    ]

    # Keep only the columns we need
    use_cols = numeric_cols + cat_cols
    X = df[use_cols].copy()

    # One-hot encode categorical columns
    X = pd.get_dummies(X, columns=cat_cols, drop_first=True)

    print("Feature matrix shape:", X.shape)
    return X, y


def train_model(X, y):
    """
    Train/test split + simple RandomForestRegressor.
    You can try other models later.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = mse ** 0.5

    print(f"MAE  : {mae:.3f} s")
    print(f"RMSE : {rmse:.3f} s")

    return model


def save_model(model, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    print(f"Saved model to: {path}")


def main():
    df = load_dataset(DATA_PATH)
    X, y = prepare_features(df)
    model = train_model(X, y)

    # --- Save model ---
    save_model(model, MODEL_PATH)

    # --- NEW: Save feature column order ---
    import json
    from pathlib import Path

    feature_columns = list(X.columns)
    feature_path = Path("models") / "lap_model_features.json"
    feature_path.parent.mkdir(parents=True, exist_ok=True)

    with open(feature_path, "w") as f:
        json.dump(feature_columns, f)

    print(f"Saved feature columns to: {feature_path}")



if __name__ == "__main__":
    main()
