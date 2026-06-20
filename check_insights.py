import sqlite3
import pandas as pd

conn = sqlite3.connect("sustainocpm.db")
c = conn.cursor()
c.execute("SELECT * FROM ai_insights")
rows = c.fetchall()
if not rows:
    print("No insights found.")
else:
    cols = [d[0] for d in c.description]
    for row in rows:
        print({col: val for col, val in zip(cols, row) if col in ['id', 'tenant_id', 'workspace_id', 'project_id', 'analysis_id', 'severity', 'insight_type']})
conn.close()
