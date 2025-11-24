import sqlite3

conn = sqlite3.connect("raceintel.db")
cur = conn.cursor()
for t in ["race", "driver", "lap"]:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"{t.title():<8} → {cur.fetchone()[0]} rows")
conn.close()
