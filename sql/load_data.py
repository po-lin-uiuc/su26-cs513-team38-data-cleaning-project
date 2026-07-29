import os
import sqlite3
import csv
import pandas as pd
import sqlite3
import subprocess

# conn = sqlite3.connect("../data/cs513_team38.sqlite")
# cur = conn.cursor()

# with open("../data/raw/MenuPage.csv") as f:
#     reader = csv.reader(f)
#     header = next(reader)
#     cur.executemany("INSERT INTO stg_menu_page VALUES (?,?,?,?,?,?,?)", reader)

# conn.commit()
# conn.close()



# delete cs513_team38.sqlite if it exists

if os.path.exists("../data/cs513_team38.sqlite"):
    os.remove("../data/cs513_team38.sqlite")

# run the 01_schema_staging.sql script to create the staging tables
# sqlite3 data/cs513_team38.sqlite < sql/01_schema_staging.sql
with open("01_schema_staging.sql", "r") as schema_file:
    subprocess.run(
        ["sqlite3", "../data/cs513_team38.sqlite"],
        stdin=schema_file,
        check=True
    )

conn = sqlite3.connect("../data/cs513_team38.sqlite")

# df = pd.read_csv("../data/raw/MenuPage.csv")
# df.to_sql("stg_menu_page", conn, if_exists="replace", index=False)
# conn.close()
