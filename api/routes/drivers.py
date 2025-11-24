"""Driver-related API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Driver, Lap, Race

router = APIRouter()
logger = logging.getLogger(__name__)


class DriverStats(BaseModel):
    """Driver statistics response model."""

    driver_code: str
    driver_name: str
    total_laps: int
    fastest_lap: Optional[float]
    average_lap_time: Optional[float]
    best_position: Optional[int]
    worst_position: Optional[int]


@router.get("/drivers", response_model=List[str])
async def get_drivers(
    race_id: Optional[int] = Query(None, description="Filter by race ID"),
    year: Optional[int] = Query(None, ge=1950, le=2100, description="Filter by year"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get list of all driver codes.

    Args:
        race_id: Optional race ID filter
        year: Optional year filter
        session: Database session

    Returns:
        List of driver codes
    """
    try:
        query = select(func.distinct(Driver.code)).where(Driver.code.isnot(None))

        if race_id:
            query = query.join(Lap).where(Lap.race_id == race_id)
        elif year:
            query = query.join(Lap).join(Race).where(Race.year == year)

        query = query.order_by(Driver.code)

        result = await session.execute(query)
        drivers = [row[0] for row in result.all() if row[0]]

        return drivers

    except Exception as e:
        logger.error(f"Error fetching drivers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drivers/{driver_code}/stats", response_model=DriverStats)
async def get_driver_stats(
    driver_code: str,
    race_id: Optional[int] = Query(None, description="Filter by race ID"),
    year: Optional[int] = Query(None, ge=1950, le=2100, description="Filter by year"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get statistics for a specific driver.

    Args:
        driver_code: Driver code (e.g., VER)
        race_id: Optional race ID filter
        year: Optional year filter
        session: Database session

    Returns:
        Driver statistics
    """
    try:
        # Get driver
        driver_query = select(Driver).where(Driver.code == driver_code.upper())
        driver_result = await session.execute(driver_query)
        driver = driver_result.scalar_one_or_none()

        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")

        # Build stats query
        query = (
            select(
                func.count(Lap.lap_id).label("total_laps"),
                func.min(Lap.lap_time_secs).label("fastest_lap"),
                func.avg(Lap.lap_time_secs).label("average_lap_time"),
                func.min(Lap.position).label("best_position"),
                func.max(Lap.position).label("worst_position"),
            )
            .join(Driver, Lap.driver_id == Driver.driver_id)
            .where(Driver.driver_id == driver.driver_id)
        )

        if race_id:
            query = query.where(Lap.race_id == race_id)
        elif year:
            query = query.join(Race).where(Race.year == year)

        result = await session.execute(query)
        row = result.first()

        if not row or row.total_laps == 0:
            raise HTTPException(
                status_code=404, detail="Driver not found or no data available"
            )

        return DriverStats(
            driver_code=driver.code,
            driver_name=driver.full_name or driver.code,
            total_laps=row.total_laps,
            fastest_lap=float(row.fastest_lap) if row.fastest_lap else None,
            average_lap_time=float(row.average_lap_time) if row.average_lap_time else None,
            best_position=row.best_position,
            worst_position=row.worst_position,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching driver stats for {driver_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
