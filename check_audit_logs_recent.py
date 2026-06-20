import sqlite3
import pandas as pd

conn = sqlite3.connect("sustainocpm.db")
df_a = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 30", conn)
for idx, row in df_a.iterrows():
    print(f"{row['created_at']} | {row['action']} | {row['details']}")
conn.close()
