import sqlite3
import pandas as pd

conn = sqlite3.connect("sustainocpm.db")
df_w = pd.read_sql_query("SELECT * FROM workspaces", conn)
print(df_w)
df_org = pd.read_sql_query("SELECT * FROM organizations", conn)
print(df_org)
conn.close()
