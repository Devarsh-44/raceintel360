# data_pipeline/fetch_f1_data.py
import os
import sys
import asyncio
import logging
import time
from datetime import date
from typing import Optional, Dict

import pandas as pd
import fastf1
from fastf1.req import RateLimitExceededError
from fastf1.core import DataNotLoadedError

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func


sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api.models import Base, Race, Driver, Lap  # type: ignore


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)
log = logging.getLogger("data_pipeline")

DEFAULT_SQLITE_URL = "sqlite+aiosqlite:///./raceintel.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)


SEASONS = list(range(2019, 2025))


LOAD_TELEMETRY = False
LOAD_WEATHER = True


async def get_sessionmaker() -> sessionmaker:
    engine = create_async_engine(DATABASE_URL, future=True, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def upsert_race(
    session: AsyncSession,
    year: int,
    round_number: int,
    name: str,
    circuit: Optional[str],
    event_date: Optional[date],
) -> Race:
    res = await session.execute(
        select(Race).where(Race.year == year, Race.round == round_number)
    )
    race = res.scalar_one_or_none()
    if race is None:
        race = Race(
            year=year, round=round_number, name=name, circuit=circuit, date=event_date
        )
        session.add(race)
        await session.flush()
    return race


async def upsert_driver(
    session: AsyncSession,
    code: str,
    full_name: Optional[str],
    number: Optional[int],
    team: Optional[str],
) -> Driver:
    res = await session.execute(select(Driver).where(Driver.code == code))
    drv = res.scalar_one_or_none()
    if drv is None:
        drv = Driver(code=code or "UNK", full_name=full_name or code, number=number, team=team)
        session.add(drv)
        await session.flush()
    return drv


async def race_has_laps(session: AsyncSession, race: Race) -> bool:
    res = await session.execute(select(func.count(Lap.lap_id)).where(Lap.race_id == race.race_id))
    return (res.scalar() or 0) > 0


async def insert_laps(session: AsyncSession, race: Race, df: pd.DataFrame, drivers_map: Dict[str, Driver]) -> None:
    def sec(x):
        if pd.isna(x):
            return None
        try:
            return float(x.total_seconds())
        except Exception:
            try:
                return float(x)
            except Exception:
                return None

    rows = []
    for _, r in df.iterrows():
        code = str(r.get("Driver", "") or "")
        drv = drivers_map.get(code)
        if not drv:
            continue
        rows.append(
            Lap(
                race_id=race.race_id,
                driver_id=drv.driver_id,
                lap_number=int(r.get("LapNumber", 0) or 0),
                lap_time_secs=sec(r.get("LapTime")),
                sector1_time_secs=sec(r.get("Sector1Time")),
                sector2_time_secs=sec(r.get("Sector2Time")),
                sector3_time_secs=sec(r.get("Sector3Time")),
                stint=int(r.get("Stint", 0) or 0),
                compound=(r.get("Compound") or None),
                tyre_life=int(r.get("TyreLife", 0) or 0) if pd.notna(r.get("TyreLife")) else None,
                fresh_tire=bool(r.get("FreshTyre")) if "FreshTyre" in r else None,
                pit_in_time_secs=sec(r.get("PitInTime")),
                pit_out_time_secs=sec(r.get("PitOutTime")),
                pit_stop=bool(r.get("PitInTime")) if "PitInTime" in r and pd.notna(r.get("PitInTime")) else False,
                position=int(r.get("Position", 0) or 0) if pd.notna(r.get("Position")) else None,
                is_fastest=False,
                is_personal_best=False,
            )
        )
    if rows:
        session.add_all(rows)
        await session.flush()


async def load_session_with_retry(year: int, rnd: int, max_retries: int = 10):
    """
    Retries politely when FastF1/Ergast rate limits are hit.
    Uses capped linear backoff to avoid hammering the API.
    """
    attempt = 0
    while True:
        try:
            sess = fastf1.get_session(year, rnd, "R")
            sess.load(
                laps=True,
                telemetry=LOAD_TELEMETRY,
                weather=LOAD_WEATHER,
                livedata=False
            )
            return sess
        except RateLimitExceededError as e:
            attempt += 1
            wait_sec = min(180, 20 * attempt)  
            log.warning(f"Rate limit hit ({e}). Waiting {wait_sec}s before retry (attempt {attempt}/{max_retries})...")
            time.sleep(wait_sec)
            if attempt >= max_retries:
                log.error("Max retries exceeded for rate limit.")
                return None
        except Exception as e:
            attempt += 1
            wait_sec = min(60, 5 * attempt)
            log.warning(f"Load failed ({type(e).__name__}: {e}). Retry in {wait_sec}s (attempt {attempt}/{max_retries})...")
            time.sleep(wait_sec)
            if attempt >= max_retries:
                log.error("Max retries exceeded for generic error.")
                return None


def filter_out_testing(schedule: pd.DataFrame) -> pd.DataFrame:
   
    if schedule is None or schedule.empty:
        return schedule

    df = schedule.copy()
    if "EventName" in df.columns:
        df = df[df["EventName"].notna()]
        df = df.loc[~df["EventName"].str.contains("Testing", case=False, na=False)]

    if "RoundNumber" in df.columns:
        df = df.loc[df["RoundNumber"].fillna(0).astype(int) >= 1]

    if "EventFormat" in df.columns:
        df = df.loc[~df["EventFormat"].astype(str).str.lower().eq("testing")]

    return df


async def main():
    # prepare cache dir (./cache locally, /tmp on Hugging Face)
    cache_dir = os.getenv("FASTF1_CACHE", "/tmp/fastf1_cache" if os.getenv("SPACE_ID") else "./cache")
    os.makedirs(cache_dir, exist_ok=True)
    fastf1.Cache.enable_cache(cache_dir)

    SessionLocal = await get_sessionmaker()

    async with SessionLocal() as session:
        for yr in SEASONS:
            log.info(f"Fetching schedule {yr}...")
            try:
                schedule = fastf1.get_event_schedule(yr)
                races = filter_out_testing(schedule)
            except Exception as e:
                log.error(f"Failed to get schedule for {yr}: {e}")
                continue

            for _, event in races.iterrows():
                
                if pd.isna(event.get("EventName")) or pd.isna(event.get("RoundNumber")):
                    continue

                gp = str(event["EventName"])
                rnd = int(event["RoundNumber"])
                event_date = (
                    pd.to_datetime(event.get("EventDate"), errors="coerce").date()
                    if pd.notna(event.get("EventDate"))
                    else None
                )
                circuit = str(event.get("EventFormat") or "") or None 
                race = await upsert_race(
                    session,
                    year=yr,
                    round_number=rnd,
                    name=gp,
                    circuit=circuit,
                    event_date=event_date,
                )
               
                if await race_has_laps(session, race):
                    log.info(f"Skipping {yr} R{rnd} – {gp} (already in DB)")
                    continue

                log.info(f"Loading {yr} R{rnd} – {gp}")
                sess = await load_session_with_retry(yr, rnd)
                if not sess:
                    log.warning(f"Skipping {yr} R{rnd} – {gp} (could not load after retries)")
                    continue

                # ensure laps are loaded
                try:
                    _ = sess.laps  # may raise DataNotLoadedError if not properly loaded
                except DataNotLoadedError:
                    log.warning(f"No laps available for {yr} R{rnd} – {gp}, skipping")
                    continue

                laps_df = sess.laps

                # ensure drivers exist
                drivers_map: Dict[str, Driver] = {}
                if "Driver" not in laps_df.columns or laps_df.empty:
                    log.warning(f"No driver column or empty laps for {yr} R{rnd} – {gp}, skipping")
                    continue

                for code in sorted(laps_df["Driver"].dropna().unique().tolist()):
                    drv = await upsert_driver(session, code=code, full_name=None, number=None, team=None)
                    drivers_map[code] = drv

                # insert laps and commit
                await insert_laps(session, race, laps_df, drivers_map)
                await session.commit()
                log.info(f"Inserted laps for {yr} R{rnd} – {gp}")

    log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
