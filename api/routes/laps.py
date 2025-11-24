"""Lap-related API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Driver, Lap, Race

router = APIRouter()


@router.get("/races/{race_id}/laps")
async def race_laps(
    race_id: int,
    driver: str | None = Query(default=None, description="Driver code, e.g., VER"),
    session: AsyncSession = Depends(get_session),
):
    """Get lap data for a specific race, optionally filtered by driver."""
    # Validate race exists
    rres = await session.execute(select(Race).where(Race.race_id == race_id))
    if not rres.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Race not found")

    q = (
        select(
            Lap.lap_number,
            Lap.lap_time_secs,
            Lap.sector1_time_secs,
            Lap.sector2_time_secs,
            Lap.sector3_time_secs,
            Lap.stint,
            Lap.compound,
            Lap.tyre_life,
            Lap.fresh_tire,
            Lap.pit_stop,
            Lap.position,
            Driver.code.label("driver"),
        )
        .join(Driver, Driver.driver_id == Lap.driver_id)
        .where(Lap.race_id == race_id)
        .order_by(Driver.code, Lap.lap_number)
    )

    if driver:
        # Find driver id by code
        dres = await session.execute(select(Driver).where(Driver.code == driver.upper()))
        d = dres.scalar_one_or_none()
        if not d:
            return []
        q = q.where(Lap.driver_id == d.driver_id)

    res = await session.execute(q)
    rows = res.all()
    return [
        {
            "driver": row.driver,
            "lap_number": row.lap_number,
            "lap_time": row.lap_time_secs,
            "s1": row.sector1_time_secs,
            "s2": row.sector2_time_secs,
            "s3": row.sector3_time_secs,
            "stint": row.stint,
            "compound": row.compound,
            "tyre_life": row.tyre_life,
            "fresh_tire": row.fresh_tire,
            "pit_stop": row.pit_stop,
            "position": row.position,
        }
        for row in rows
    ]
