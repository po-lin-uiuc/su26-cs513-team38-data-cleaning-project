import sqlite3
import csv

conn = sqlite3.connect("../data/cs513_team38.sqlite")
cur = conn.cursor()

cur.execute("SELECT * FROM stg_menu_page LIMIT 5")
rows = cur.fetchall()

for row in rows:
    print(row)

conn.close()

