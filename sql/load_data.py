import sqlite3
import csv

# conn = sqlite3.connect("../data/cs513_team38.sqlite")
# cur = conn.cursor()

# with open("../data/raw/MenuPage.csv") as f:
#     reader = csv.reader(f)
#     header = next(reader)
#     cur.executemany("INSERT INTO stg_menu_page VALUES (?,?,?,?,?,?,?)", reader)

# conn.commit()
# conn.close()

import pandas as pd
import sqlite3

conn = sqlite3.connect("../data/cs513_team38.sqlite")
df = pd.read_csv("../data/raw/MenuPage.csv")
df.to_sql("stg_menu_page", conn, if_exists="replace", index=False)
conn.close()
