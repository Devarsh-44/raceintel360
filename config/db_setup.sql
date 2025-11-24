
CREATE TABLE IF NOT EXISTS race (
  race_id SERIAL PRIMARY KEY,
  year INT,
  round INT,
  name VARCHAR(100),
  circuit VARCHAR(100),
  date DATE
);

CREATE TABLE IF NOT EXISTS driver (
  driver_id SERIAL PRIMARY KEY,
  code VARCHAR(3) UNIQUE,
  full_name VARCHAR(100),
  number INT,
  team VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS lap (
  lap_id SERIAL PRIMARY KEY,
  race_id INT REFERENCES race(race_id) ON DELETE CASCADE,
  driver_id INT REFERENCES driver(driver_id) ON DELETE CASCADE,
  lap_number INT,
  lap_time_secs FLOAT,
  sector1_time_secs FLOAT,
  sector2_time_secs FLOAT,
  sector3_time_secs FLOAT,
  stint INT,
  compound VARCHAR(15),
  tyre_life INT,
  fresh_tire BOOLEAN,
  pit_in_time_secs FLOAT,
  pit_out_time_secs FLOAT,
  pit_stop BOOLEAN,
  position INT,
  is_fastest BOOLEAN,
  is_personal_best BOOLEAN
);

CREATE INDEX IF NOT EXISTS idx_lap_race ON lap (race_id);
CREATE INDEX IF NOT EXISTS idx_lap_driver ON lap (driver_id);
CREATE INDEX IF NOT EXISTS idx_lap_pit ON lap (pit_stop);
