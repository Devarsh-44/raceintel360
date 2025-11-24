"""Analytics and advanced query routes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Driver, Lap, Race

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/analytics/driver-comparison")
async def compare_drivers(
    driver_1: str = Query(..., description="First driver code, e.g., VER"),
    driver_2: str = Query(..., description="Second driver code, e.g., HAM"),
    race_id: Optional[int] = Query(None, description="Filter by race ID"),
    year: Optional[int] = Query(None, ge=1950, le=2100, description="Filter by year"),
    session: AsyncSession = Depends(get_session),
):
    """
    Compare lap times between two drivers.

    Args:
        driver_1: First driver code
        driver_2: Second driver code
        race_id: Optional race ID filter
        year: Optional year filter
        session: Database session

    Returns:
        Comparison statistics with lap-by-lap differences
    """
    try:
        # Get driver IDs
        d1_res = await session.execute(
            select(Driver).where(Driver.code == driver_1.upper())
        )
        driver1 = d1_res.scalar_one_or_none()
        if not driver1:
            raise HTTPException(
                status_code=404, detail=f"Driver {driver_1} not found"
            )

        d2_res = await session.execute(
            select(Driver).where(Driver.code == driver_2.upper())
        )
        driver2 = d2_res.scalar_one_or_none()
        if not driver2:
            raise HTTPException(
                status_code=404, detail=f"Driver {driver_2} not found"
            )

        # Build query - get laps for both drivers
        query = (
            select(
                Lap.lap_number,
                func.max(
                    case(
                        (Lap.driver_id == driver1.driver_id, Lap.lap_time_secs),
                        else_=None,
                    )
                ).label("driver_1_time"),
                func.max(
                    case(
                        (Lap.driver_id == driver2.driver_id, Lap.lap_time_secs),
                        else_=None,
                    )
                ).label("driver_2_time"),
            )
            .where(
                (Lap.driver_id.in_([driver1.driver_id, driver2.driver_id]))
                & (Lap.lap_time_secs.isnot(None))
            )
        )

        if race_id:
            query = query.where(Lap.race_id == race_id)
        elif year:
            query = query.join(Race).where(Race.year == year)

        query = query.group_by(Lap.lap_number).having(
            func.count(func.distinct(Lap.driver_id)) == 2
        ).order_by(Lap.lap_number)

        result = await session.execute(query)
        rows = result.all()

        comparisons = []
        for row in rows:
            if row.driver_1_time and row.driver_2_time:
                time_diff = row.driver_1_time - row.driver_2_time
                comparisons.append(
                    {
                        "lap_number": row.lap_number,
                        "driver_1_time": row.driver_1_time,
                        "driver_2_time": row.driver_2_time,
                        "time_difference": round(time_diff, 3),
                        "faster_driver": driver_1 if time_diff > 0 else driver_2,
                    }
                )

        return {
            "driver_1": driver_1.upper(),
            "driver_2": driver_2.upper(),
            "comparisons": comparisons,
            "total_comparable_laps": len(comparisons),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing drivers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/circuit-performance")
async def get_circuit_performance(
    circuit: str = Query(..., description="Circuit name"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of races"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get performance statistics for a specific circuit.

    Args:
        circuit: Circuit name
        limit: Maximum number of races to analyze
        session: Database session

    Returns:
        Circuit performance statistics
    """
    try:
        # Get races at this circuit
        races_query = (
            select(
                Race.race_id,
                Race.year,
                Race.name,
                Race.round,
                func.count(Lap.lap_id).label("total_laps"),
            )
            .outerjoin(Lap, Race.race_id == Lap.race_id)
            .where(func.lower(Race.circuit) == func.lower(circuit))
            .group_by(Race.race_id, Race.year, Race.name, Race.round)
            .order_by(Race.year.desc())
            .limit(limit)
        )

        races_result = await session.execute(races_query)
        races = races_result.all()

        # Get fastest lap times at this circuit (one per race)
        # SQLite doesn't support DISTINCT ON, so we'll use a subquery approach
        fastest_laps_subquery = (
            select(
                Lap.race_id,
                func.min(Lap.lap_time_secs).label("min_lap_time"),
            )
            .join(Race, Lap.race_id == Race.race_id)
            .where(
                (func.lower(Race.circuit) == func.lower(circuit))
                & (Lap.lap_time_secs.isnot(None))
            )
            .group_by(Lap.race_id)
            .subquery()
        )

        fastest_laps_query = (
            select(
                Race.year,
                Driver.code.label("driver"),
                Lap.lap_time_secs,
                Lap.compound,
            )
            .join(Lap, Race.race_id == Lap.race_id)
            .join(Driver, Lap.driver_id == Driver.driver_id)
            .join(
                fastest_laps_subquery,
                (Lap.race_id == fastest_laps_subquery.c.race_id)
                & (Lap.lap_time_secs == fastest_laps_subquery.c.min_lap_time),
            )
            .where(func.lower(Race.circuit) == func.lower(circuit))
            .order_by(Race.year.desc())
            .limit(limit)
        )

        fastest_laps_result = await session.execute(fastest_laps_query)
        fastest_laps = fastest_laps_result.all()

        return {
            "circuit": circuit,
            "races": [
                {
                    "race_id": r.race_id,
                    "year": r.year,
                    "race_name": r.name,
                    "round": r.round,
                    "total_laps": r.total_laps or 0,
                }
                for r in races
            ],
            "fastest_laps": [
                {
                    "year": fl.year,
                    "driver": fl.driver,
                    "lap_time": fl.lap_time_secs,
                    "compound": fl.compound,
                }
                for fl in fastest_laps
            ],
        }

    except Exception as e:
        logger.error(f"Error fetching circuit performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/season-summary")
async def get_season_summary(
    year: int = Query(..., ge=1950, le=2100, description="Season year"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get summary statistics for a season.

    Args:
        year: Season year
        session: Database session

    Returns:
        Season summary statistics
    """
    try:
        # Race count
        race_count_query = select(func.count(Race.race_id)).where(Race.year == year)
        race_count_result = await session.execute(race_count_query)
        race_count = race_count_result.scalar() or 0

        # Total laps
        total_laps_query = (
            select(func.count(Lap.lap_id))
            .join(Race, Lap.race_id == Race.race_id)
            .where(Race.year == year)
        )
        total_laps_result = await session.execute(total_laps_query)
        total_laps = total_laps_result.scalar() or 0

        # Unique drivers
        drivers_query = (
            select(func.count(func.distinct(Lap.driver_id)))
            .join(Race, Lap.race_id == Race.race_id)
            .where(Race.year == year)
        )
        drivers_result = await session.execute(drivers_query)
        unique_drivers = drivers_result.scalar() or 0

        # Fastest lap of season
        fastest_lap_query = (
            select(
                Driver.code.label("driver"),
                Lap.lap_time_secs,
                Race.name.label("race_name"),
                Race.circuit,
            )
            .join(Race, Lap.race_id == Race.race_id)
            .join(Driver, Lap.driver_id == Driver.driver_id)
            .where((Race.year == year) & (Lap.lap_time_secs.isnot(None)))
            .order_by(Lap.lap_time_secs.asc())
            .limit(1)
        )

        fastest_lap_result = await session.execute(fastest_lap_query)
        fastest_lap = fastest_lap_result.first()

        # Top drivers by fastest laps (simplified - counting fastest lap per race)
        top_drivers_query = (
            select(
                Driver.code.label("driver"),
                func.count(func.distinct(Race.race_id)).label("fastest_lap_count"),
            )
            .join(Lap, Driver.driver_id == Lap.driver_id)
            .join(Race, Lap.race_id == Race.race_id)
            .where(
                (Race.year == year)
                & (Lap.lap_time_secs.isnot(None))
                & (Lap.is_fastest == True)
            )
            .group_by(Driver.code)
            .order_by(func.count(func.distinct(Race.race_id)).desc())
            .limit(5)
        )

        top_drivers_result = await session.execute(top_drivers_query)
        top_drivers = top_drivers_result.all()

        return {
            "year": year,
            "race_count": race_count,
            "total_laps": total_laps,
            "unique_drivers": unique_drivers,
            "fastest_lap": {
                "driver": fastest_lap.driver,
                "lap_time": fastest_lap.lap_time_secs,
                "race": fastest_lap.race_name,
                "circuit": fastest_lap.circuit,
            }
            if fastest_lap
            else None,
            "top_drivers": [
                {
                    "driver": td.driver,
                    "fastest_lap_count": td.fastest_lap_count,
                }
                for td in top_drivers
            ],
        }

    except Exception as e:
        logger.error(f"Error fetching season summary for {year}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
