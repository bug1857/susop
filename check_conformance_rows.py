import sqlite3
conn = sqlite3.connect("sustainocpm.db")
c = conn.cursor()

c.execute("SELECT * FROM conformance_results WHERE analysis_id='520e8768ac0f4da083544540352ff8f1'")
cols = [d[0] for d in c.description]
rows = c.fetchall()
print("--- CONFORMANCE RESULTS ---")
if not rows:
    print("None")
for row in rows:
    print(dict(zip(cols, row)))

c.execute("SELECT * FROM carbon_attributions WHERE analysis_id='520e8768ac0f4da083544540352ff8f1'")
cols = [d[0] for d in c.description]
rows = c.fetchall()
print("\n--- CARBON ATTRIBUTIONS COUNT ---")
print(len(rows))

conn.close()
