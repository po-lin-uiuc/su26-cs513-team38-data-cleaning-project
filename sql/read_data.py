import sqlite3
import csv

conn = sqlite3.connect("../data/cs513_team38.sqlite")
cur = conn.cursor()

# TODO: test to make sure there are rows in all tables

# TODO: check if id's in specific tables match up with other id's in other tables (foreign key relationships)

cur.execute("SELECT * FROM stg_menu_page LIMIT 5")
rows = cur.fetchall()

for row in rows:
    print(row)

conn.close()
