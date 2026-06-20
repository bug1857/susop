import sqlite3
conn = sqlite3.connect("sustainocpm.db")
c = conn.cursor()
c.execute("SELECT * FROM workspaces")
cols = [d[0] for d in c.description]
for row in c.fetchall():
    print(dict(zip(cols, row)))
conn.close()
