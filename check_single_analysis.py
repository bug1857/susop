import sqlite3
import pandas as pd

conn = sqlite3.connect("sustainocpm.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM process_analyses WHERE id='520e8768ac0f4da083544540352ff8f1'")
row = cursor.fetchone()
cols = [d[0] for d in cursor.description]
if row:
    print(dict(zip(cols, row)))
else:
    print("Not found")
conn.close()
