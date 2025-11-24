# api/routes/ai_analysis.py

from fastapi import APIRouter
from pydantic import BaseModel
from pathlib import Path
import json
import joblib
import os

from dotenv import load_dotenv  # load .env

from strategy.strategy_simulator import simulate_strategy

# Load environment variables from .env at project root
load_dotenv()

router = APIRouter()

MODEL_PATH = Path("models/lap_time_model.pkl")
FEATURE_PATH = Path("models/lap_model_features.json")


class Stint(BaseModel):
    compound: str
    laps: int


class StrategyInput(BaseModel):
    name: str
    stints: list[Stint]


class AgentRequest(BaseModel):
    year: int
    round_number: int
    race_name: str
    driver_code: str
    total_laps: int
    strategies: list[StrategyInput]
    question: str | None = None  # optional natural-language question


class ChatRequest(BaseModel):
    
    question: str
    year: int = 2021
    round_number: int = 1
    race_name: str = "Bahrain Grand Prix"
    driver_code: str = "VER"
    total_laps: int = 57

class HistoryQuestion(ChatRequest):
    """For general F1 history / info questions."""
    question: str



def _run_simulation(req: AgentRequest) -> list[dict]:
    """Run simulator for all strategies and return sorted results."""
    model = joblib.load(MODEL_PATH)
    with open(FEATURE_PATH) as f:
        feature_columns = json.load(f)

    results: list[dict] = []

    for strat in req.strategies:
        stints = [s.model_dump() for s in strat.stints]

        total_time, lap_times = simulate_strategy(
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

        avg_lap = (
            round(sum(lap_times) / len(lap_times), 3)
            if lap_times
            else None
        )

        results.append(
            {
                "strategy": strat.name,
                "stints": stints,
                "total_time_s": float(total_time),
                "total_time_min": float(round(total_time / 60.0, 2)),
                "avg_lap_s": float(avg_lap) if avg_lap is not None else None,
            }
        )

    # best strategy first
    results.sort(key=lambda r: r["total_time_s"])
    return results


def _simple_explanation(req: AgentRequest, results: list[dict]) -> str:
    """Fallback explanation if OpenAI is not available."""
    best = results[0]
    others = results[1:]
    parts: list[str] = []

    parts.append(
        f"Best strategy: {best['strategy']} "
        f"with total race time ≈ {best['total_time_min']:.2f} minutes."
    )

    if others:
        for other in others:
            diff = other["total_time_s"] - best["total_time_s"]
            parts.append(
                f"Compared to {best['strategy']}, "
                f"{other['strategy']} is slower by about {diff:.1f} seconds."
            )

    if req.question:
        parts.append(f"(Question from user: {req.question})")

    return " ".join(parts)


def _llm_explanation(req: AgentRequest, results: list[dict]) -> str:
    """Use OpenAI (if key is set) to generate a nicer explanation."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _simple_explanation(req, results)

    try:
        from openai import OpenAI
    except ImportError:
        return _simple_explanation(req, results)

    client = OpenAI(api_key=api_key)

    # Compact summary of each strategy
    summary_lines = []
    for r in results:
        summary_lines.append(
            f"- {r['strategy']}: total={r['total_time_s']:.1f}s "
            f"({r['total_time_min']:.2f} min), avg lap={r['avg_lap_s']} s"
        )
    summary_text = "\n".join(summary_lines)

    user_question = (
        req.question
        or "Explain which strategy is better and how big the difference is."
    )

    prompt = f"""
You are a friendly F1 race engineer helping a university student understand race strategy.

Race info:
- Year: {req.year}
- Round: {req.round_number}
- Race: {req.race_name}
- Driver: {req.driver_code}
- Total laps: {req.total_laps}

Simulated strategies and results:
{summary_text}

User question:
{user_question}

Write a short explanation (3–5 sentences) that:
- clearly names the best strategy,
- mentions how much faster it is vs the others (in seconds),
- is easy to understand for a student (no super advanced jargon).
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.4,
        messages=[
            {
                "role": "system",
                "content": "You are an F1 race engineer and data analyst.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    explanation = resp.choices[0].message.content.strip()
    return explanation


@router.post("/ai/strategy", tags=["AI Analysis"])
async def ai_strategy_helper(req: AgentRequest):
    """
    Agent-style endpoint:
    - runs the simulator for each strategy
    - returns all results sorted by total time
    - uses OpenAI (if OPENAI_API_KEY is set) to generate a natural-language explanation
    """
    results = _run_simulation(req)
    best = results[0]
    explanation = _llm_explanation(req, results)

    return {
        "results": results,
        "best_strategy": best["strategy"],
        "explanation": explanation,
        "used_openai": bool(os.getenv("OPENAI_API_KEY")),
    }


@router.post("/ai/chat", tags=["AI Analysis"])
async def ai_chat(req: ChatRequest):
    """
    Simpler, 'chatty' endpoint.

    You send:
      - a natural-language question
      - basic race info (year, round, race, driver, total_laps)

    It will:
      - build two default strategies (one-stop and two-stop),
      - run the simulator,
      - return the best strategy and an OpenAI-generated explanation.
    """

    # Build two default strategies based on total_laps
    total_laps = req.total_laps

    one_stop = StrategyInput(
        name="one_stop",
        stints=[
            Stint(compound="MEDIUM", laps=total_laps // 2),
            Stint(compound="HARD", laps=total_laps - total_laps // 2),
        ],
    )
    two_stop = StrategyInput(
        name="two_stop",
        stints=[
            Stint(compound="SOFT", laps=total_laps // 3),
            Stint(compound="MEDIUM", laps=total_laps // 3),
            Stint(
                compound="HARD",
                laps=total_laps - 2 * (total_laps // 3),
            ),
        ],
    )

    agent_req = AgentRequest(
        year=req.year,
        round_number=req.round_number,
        race_name=req.race_name,
        driver_code=req.driver_code,
        total_laps=req.total_laps,
        strategies=[one_stop, two_stop],
        question=req.question,
    )

    results = _run_simulation(agent_req)
    best = results[0]
    explanation = _llm_explanation(agent_req, results)

    return {
        "used_defaults": True,
        "agent_request": agent_req.model_dump(),
        "results": results,
        "best_strategy": best["strategy"],
        "explanation": explanation,
        "used_openai": bool(os.getenv("OPENAI_API_KEY")),
    }
@router.post("/ai/history", tags=["AI Analysis"])
async def ai_f1_history(req: HistoryQuestion):
    """
    F1 history / general knowledge agent.

    You send:
      { "question": "Who won the 2019 F1 championship?" }

    It returns:
      - a short answer focused on F1
      - a note if OpenAI wasn't available
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # No key available, give a friendly fallback
        return {
            "answer": (
                "F1 history mode is not available because OPENAI_API_KEY "
                "is not configured on the server."
            ),
            "used_openai": False,
        }

    try:
        from openai import OpenAI
    except ImportError:
        return {
            "answer": (
                "F1 history mode is not available because the 'openai' "
                "Python package is not installed on the server."
            ),
            "used_openai": False,
        }

    client = OpenAI(api_key=api_key)

    prompt = f"""
You are an expert Formula 1 historian and race analyst.
Answer the user's question clearly and accurately.

Guidelines:
- Stick to real F1 history and facts (drivers, teams, seasons, tracks, rules, major incidents).
- If the question is about very recent seasons or the future, explain that you might not have the very latest data.
- Keep the answer short: 3–6 sentences.
- Write in a way a university student doing a project can understand.

User question:
{req.question}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.5,
        messages=[
            {
                "role": "system",
                "content": "You are an expert in Formula 1 history and statistics.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    answer = resp.choices[0].message.content.strip()

    return {
        "answer": answer,
        "used_openai": True,
    }
