"""Database models for RaceIntel360."""

from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class Race(Base):
    """Race model representing an F1 race event."""

    __tablename__ = "race"

    race_id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, index=True)
    round = Column(Integer, index=True)
    name = Column(String(100), index=True)
    circuit = Column(String(100), nullable=True)
    date = Column(Date, nullable=True)

    laps = relationship("Lap", back_populates="race", cascade="all, delete-orphan")
    weather = relationship("Weather", back_populates="race", cascade="all, delete-orphan")


class Driver(Base):
    """Driver model representing an F1 driver."""

    __tablename__ = "driver"

    driver_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(3), index=True, unique=True)  # e.g., VER
    full_name = Column(String(100))
    number = Column(Integer, nullable=True)
    team = Column(String(50), nullable=True)

    laps = relationship("Lap", back_populates="driver", cascade="all, delete-orphan")


class Lap(Base):
    """Lap model representing a single lap in a race."""

    __tablename__ = "lap"

    lap_id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("race.race_id", ondelete="CASCADE"), index=True)
    driver_id = Column(Integer, ForeignKey("driver.driver_id", ondelete="CASCADE"), index=True)

    lap_number = Column(Integer, index=True)
    lap_time_secs = Column(Float)
    sector1_time_secs = Column(Float)
    sector2_time_secs = Column(Float)
    sector3_time_secs = Column(Float)
    stint = Column(Integer, index=True)
    compound = Column(String(15))
    tyre_life = Column(Integer)
    fresh_tire = Column(Boolean)
    pit_in_time_secs = Column(Float)
    pit_out_time_secs = Column(Float)
    pit_stop = Column(Boolean, default=False, index=True)
    position = Column(Integer)
    is_fastest = Column(Boolean, default=False)
    is_personal_best = Column(Boolean, default=False)

    race = relationship("Race", back_populates="laps")
    driver = relationship("Driver", back_populates="laps")


class Weather(Base):
    """Weather model representing weather conditions during a race."""

    __tablename__ = "weather"

    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("race.race_id", ondelete="CASCADE"), index=True)
    sample_time_secs = Column(Float)
    air_temp = Column(Float)
    track_temp = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    wind_speed = Column(Float)
    wind_dir = Column(Integer)
    rainfall = Column(Boolean)

    race = relationship("Race", back_populates="weather")
