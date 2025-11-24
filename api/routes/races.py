"""Race-related API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Race

router = APIRouter()


@router.get("/races")
async def list_races(session: AsyncSession = Depends(get_session)):
    """List all races ordered by year and round."""
    res = await session.execute(select(Race).order_by(Race.year, Race.round))
    rows = res.scalars().all()
    return [
        {
            "race_id": r.race_id,
            "year": r.year,
            "round": r.round,
            "name": r.name,
            "circuit": r.circuit,
            "date": r.date.isoformat() if r.date else None,
        }
        for r in rows
    ]


@router.get("/races/{race_id}")
async def get_race(race_id: int, session: AsyncSession = Depends(get_session)):
    """Get a specific race by ID."""
    res = await session.execute(select(Race).where(Race.race_id == race_id))
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Race not found")
    return {
        "race_id": r.race_id,
        "year": r.year,
        "round": r.round,
        "name": r.name,
        "circuit": r.circuit,
        "date": r.date.isoformat() if r.date else None,
    }
