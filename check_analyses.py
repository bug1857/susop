import sqlite3
import pandas as pd

conn = sqlite3.connect("sustainocpm.db")

print("--- WORKSPACES ---")
df_w = pd.read_sql_query("SELECT id, name, organization_id FROM workspaces", conn)
print(df_w)

print("\n--- PROJECTS ---")
df_p = pd.read_sql_query("SELECT id, name, workspace_id FROM projects", conn)
print(df_p)

print("\n--- PROCESS ANALYSES ---")
df_pa = pd.read_sql_query("SELECT id, tenant_id, workspace_id, project_id, status, is_deleted FROM process_analyses", conn)
print(df_pa)

print("\n--- USERS & ROLES ---")
df_u = pd.read_sql_query("SELECT id, email FROM users", conn)
print(df_u)
df_ur = pd.read_sql_query("SELECT user_id, organization_id, role FROM user_roles", conn)
print(df_ur)

conn.close()
