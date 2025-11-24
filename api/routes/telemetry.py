"""Telemetry API routes for FastF1 data."""

import fastf1
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


@router.get("/telemetry/fastest-lap")
def fastest_lap_telemetry(
    year: int = Query(..., ge=1950),
    round: int = Query(..., ge=1),
    driver: str = Query(..., min_length=2, max_length=3),
):
    """Return core telemetry traces for the driver's fastest race lap."""
    try:
        sess = fastf1.get_session(year, round, "R")
        # Light load for API speed; we only need laps+telemetry
        sess.load(laps=True, telemetry=True, weather=False, livedata=False)

        laps = sess.laps.pick_driver(driver.upper())
        if laps is None or laps.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No laps for driver {driver} in {year} R{round}",
            )

        flap = laps.pick_fastest()
        if flap is None:
            raise HTTPException(
                status_code=404,
                detail=f"No fastest lap found for driver {driver} in {year} R{round}",
            )

        # Get car data with distance
        car = flap.get_car_data().add_distance()

        # Convert Time to seconds for JSON
        time_secs = car["Time"].dt.total_seconds().tolist()

        data = {
            "driver": driver.upper(),
            "year": year,
            "round": round,
            "samples": int(len(car)),
            "trace": {
                "Time": time_secs,
                "Speed": car["Speed"].tolist() if "Speed" in car else [],
                "Throttle": car["Throttle"].tolist() if "Throttle" in car else [],
                "Brake": car["Brake"].tolist() if "Brake" in car else [],
                "RPM": car["RPM"].tolist() if "RPM" in car else [],
                "nGear": car["nGear"].tolist() if "nGear" in car else [],
                "Distance": car["Distance"].tolist() if "Distance" in car else [],
            },
        }
        return data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

