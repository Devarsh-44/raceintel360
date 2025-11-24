import sqlite3
from textwrap import dedent

conn = sqlite3.connect("raceintel.db")
cur = conn.cursor()

# Races per year
print("=== Races per year ===")
cur.execute("""
SELECT year, COUNT(*) AS races
FROM race
GROUP BY year
ORDER BY year;
""")
for y, c in cur.fetchall():
    print(f"{y}: {c}")

print("\n=== Laps per year ===")
cur.execute("""
SELECT r.year, COUNT(l.lap_id) AS laps
FROM lap l
JOIN race r ON r.race_id = l.race_id
GROUP BY r.year
ORDER BY r.year;
""")
for y, c in cur.fetchall():
    print(f"{y}: {c}")

print("\n=== Distinct drivers per year (by laps) ===")
cur.execute("""
SELECT r.year, COUNT(DISTINCT d.code) AS drivers
FROM lap l
JOIN race r ON r.race_id = l.race_id
JOIN driver d ON d.driver_id = l.driver_id
GROUP BY r.year
ORDER BY r.year;
""")
for y, c in cur.fetchall():
    print(f"{y}: {c}")

conn.close()
