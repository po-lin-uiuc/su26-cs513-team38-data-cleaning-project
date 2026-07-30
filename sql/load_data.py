import os
import sqlite3
import pandas as pd
import subprocess

DB_PATH = "../data/cs513_team38.sqlite"

# delete the db if it exists, so we always start fresh
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

# run the schema script to create the staging tables (with PK/FK constraints)
with open("01_schema_staging.sql", "r") as schema_file:
    subprocess.run(
        ["sqlite3", DB_PATH],
        stdin=schema_file,
        check=True,
    )

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")

# loading parent tables first (tables w/ no dependencies)
menu_df = pd.read_csv("../data/interim/Menu_cleaned.csv")
menu_df.to_sql("stg_menu", conn, if_exists="append", index=False)
print(f"stg_menu: loaded {len(menu_df)} rows")

dish_df = pd.read_csv("../data/interim/Dish_cleaned.csv")
dish_df.to_sql("stg_dish", conn, if_exists="append", index=False)
print(f"stg_dish: loaded {len(dish_df)} rows")

# loading stg_menu_page:
# menu_id in table stg_menu_page MUST exist as an id in stg_menu
menu_page_df = pd.read_csv("../data/interim/MenuPage_cleaned.csv")
before = len(menu_page_df)
menu_page_df = menu_page_df[menu_page_df["menu_id"].isin(menu_df["id"])]
dropped = before - len(menu_page_df)

# printouts for debugging
if dropped:
    print(f"stg_menu_page: dropped {dropped} rows with menu_id not found in stg_menu")
menu_page_df.to_sql("stg_menu_page", conn, if_exists="append", index=False)
print(f"stg_menu_page: loaded {len(menu_page_df)} rows")

# loading stg_menu_item:
# menu_page_id in table stg_menu_item MUST exist as an id in stg_menu_page
menu_item_df = pd.read_csv("../data/interim/MenuItem_cleaned.csv")
before = len(menu_item_df)
menu_item_df = menu_item_df[menu_item_df["menu_page_id"].isin(menu_page_df["id"])]
dropped_page = before - len(menu_item_df)

# loading stg_menu_item:
# dish_id in table stg_menu_item MUST exist as an id in stg_dish
before_dish = len(menu_item_df)
menu_item_df = menu_item_df[menu_item_df["dish_id"].isin(dish_df["id"])]
dropped_dish = before_dish - len(menu_item_df)

# printouts for debugging
if dropped_page:
    print(f"stg_menu_item: dropped {dropped_page} rows with menu_page_id not found in stg_menu_page")
if dropped_dish:
    print(f"stg_menu_item: dropped {dropped_dish} rows with dish_id not found in stg_dish")

menu_item_df.to_sql("stg_menu_item", conn, if_exists="append", index=False)
print(f"stg_menu_item: loaded {len(menu_item_df)} rows")

conn.close()