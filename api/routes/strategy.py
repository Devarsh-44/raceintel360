"""Strategy simulation API routes."""

import json
from pathlib import Path

import joblib
from fastapi import APIRouter
from pydantic import BaseModel

from strategy.strategy_simulator import simulate_strategy

router = APIRouter()

MODEL_PATH = Path("models/lap_time_model.pkl")
FEATURE_PATH = Path("models/lap_model_features.json")


class Stint(BaseModel):
    """Represents a single stint in a race strategy."""

    compound: str
    laps: int


class StrategyInput(BaseModel):
    """Represents a complete race strategy."""

    name: str
    stints: list[Stint]


class SimulationRequest(BaseModel):
    """Request model for strategy simulation."""

    year: int
    round_number: int
    race_name: str
    driver_code: str
    total_laps: int
    strategies: list[StrategyInput]


@router.post("/strategy/simulate", tags=["Strategy"])
async def simulate(req: SimulationRequest):
    """Simulate multiple race strategies and return results sorted by total time."""
    model = joblib.load(MODEL_PATH)
    with open(FEATURE_PATH) as f:
        feature_columns = json.load(f)

    results = []
    for strat in req.strategies:
        stints = [s.model_dump() for s in strat.stints]
        total_time, _ = simulate_strategy(
            model,
            feature_columns,
            year=req.year,
            round_number=req.round_number,
            race_name=req.race_name,
            driver_code=req.driver_code,
            total_laps=req.total_laps,
            stints=stints,
            pit_loss_s=22.0,
            starting_position=1,
        )
        results.append(
            {
                "strategy": strat.name,
                "total_time_s": total_time,
                "total_time_min": round(total_time / 60.0, 2),
            }
        )

    results.sort(key=lambda r: r["total_time_s"])
    return {"results": results}
