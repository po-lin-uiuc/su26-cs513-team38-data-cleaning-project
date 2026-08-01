import os
import sqlite3
import pandas as pd
import subprocess

# THIS FILE LOADS CLEANED DATA INTO STAGING TABLES
# THIS FILE ALSO INCLUDES VALIDATION OF INCLUSION DEPENDENCIES (INDs) BETWEEN TABLES INSTEAD OF USING THE SQL FILE

# CLEANED DATA PATH: change as needed
DB_PATH = "../data/cs513_team38.sqlite"

# inclusion dependency violations: x determines y, etc.
VIOLATION_IND_PATH = "../data/interim/validation_ind_results.csv"

# delete the db if it exists, so we always start fresh
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

# run the schema script to create the staging tables (with PK/FK constraints)
with open("../sql/01_schema_staging.sql", "r") as schema_file:
    subprocess.run(
        ["sqlite3", DB_PATH],
        stdin=schema_file,
        check=True,
    )

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")

ind_violations = []

# combining all different violations for csv
def tag(df, IND_reason, source_table):
    df = df.copy()
    df.insert(0, "IND_reason", IND_reason)
    df.insert(1, "source_table", source_table)
    return df


# loading parent tables first (tables w/ no dependencies)
menu_df = pd.read_csv("../data/interim/Menu_cleaned.csv")
menu_df.to_sql("stg_menu", conn, if_exists="append", index=False)
print(f"stg_menu: loaded {len(menu_df)} rows")
 
dish_df = pd.read_csv("../data/interim/Dish_cleaned.csv")
dish_df.to_sql("stg_dish", conn, if_exists="append", index=False)
print(f"stg_dish: loaded {len(dish_df)} rows")

# loading stg_menu_page:
menu_page_df = pd.read_csv("../data/interim/MenuPage_cleaned.csv")
orphaned_mask = ~menu_page_df["menu_id"].isin(menu_df["id"])
orphaned = menu_page_df[orphaned_mask]

# =====================================================================
# IND-1: menu_id in table stg_menu_page MUST exist as an id in stg_menu
# adding violations to csv
if len(orphaned):
    ind_violations.append(tag(orphaned, "IND-1", "stg_menu_page"))
    print(f"stg_menu_page: dropped {len(orphaned)} rows with menu_id not found in stg_menu")
menu_page_df = menu_page_df[~orphaned_mask]
menu_page_df.to_sql("stg_menu_page", conn, if_exists="append", index=False)
print(f"stg_menu_page: loaded {len(menu_page_df)} rows")
 
# loading stg_menu_item:
menu_item_df = pd.read_csv("../data/interim/MenuItem_cleaned.csv")
orphaned_mask = ~menu_item_df["menu_page_id"].isin(menu_page_df["id"])
orphaned = menu_item_df[orphaned_mask]

# =====================================================================
# IND-2: menu_page_id in table stg_menu_item MUST exist as an id in stg_menu_page
#adding violations to csv
if len(orphaned):
    ind_violations.append(tag(orphaned, "IND-2", "stg_menu_item"))
    print(f"stg_menu_item: dropped {len(orphaned)} rows with menu_page_id not found in stg_menu_page")
menu_item_df = menu_item_df[~orphaned_mask]
 
# loading stg_menu_item:
orphaned_mask = ~menu_item_df["dish_id"].isin(dish_df["id"])
orphaned = menu_item_df[orphaned_mask]

# =====================================================================
# IND-3: dish_id in table stg_menu_item MUST exist as an id in stg_dish
#adding violations to csv
if len(orphaned):
    ind_violations.append(tag(orphaned, "IND-3", "stg_menu_item"))
    print(f"stg_menu_item: dropped {len(orphaned)} rows with dish_id not found in stg_dish")
menu_item_df = menu_item_df[~orphaned_mask]
 
menu_item_df.to_sql("stg_menu_item", conn, if_exists="append", index=False)
print(f"stg_menu_item: loaded {len(menu_item_df)} rows")
 
conn.close()
 
# write out all collected IND violations to a single CSV
os.makedirs(os.path.dirname(VIOLATION_IND_PATH), exist_ok=True)
if ind_violations:
    combined = pd.concat(ind_violations, ignore_index=True, sort=False)
else:
    combined = pd.DataFrame(columns=["IND_reason", "source_table"])
combined.to_csv(VIOLATION_IND_PATH, index=False)

print(f"Cleaned data loaded into {DB_PATH} successfully.")

print(f"\n\n{len(combined)} IND violations written to {VIOLATION_IND_PATH}")
print(f"IND violations loaded into {VIOLATION_IND_PATH} successfully.")