import sqlite3
import pandas as pd
import subprocess
import sys

# THIS FILE TAKES THE VALIDATION RESULTS FROM THE SQL FILES AND COMPARES THEM

# CLEANED DATA PATH: change as needed
DB_PATH = "../data/cs513_team38.sqlite"
SETUP = "../sql/04_validate_ind.py"

VIOLATION_FD_PATH = "../data/interim/validation_fd_results.csv"
VIOLATION_IC_PATH = "../data/interim/validation_ic_results.csv"


# =====================================================================
# IND VIOLATIONS + CLEANED TABLES SETUP:

print(f"---- LOAD TABLES, CHECK FOR IND VIOLATIONS (foreign key/primary key constraints) ----")
subprocess.run([sys.executable, SETUP], check=True)

# =====================================================================
# FC VIOLATIONS:
def check_fd_violations():
    # run the schema script to create the fd validation csv file
    with open('../sql/05_validate_fd.sql', 'r') as file:
        sql_file = file.read()
    sql_commands = sql_file.split(';')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    fd_violations = []

    for sql_query in sql_commands:
        if sql_query.strip():
            cursor.execute(sql_query)
            fd_violations.append(cursor.fetchall())

    fd_row_count = 0
    with open(VIOLATION_FD_PATH, 'w') as file:
        for violations in fd_violations:
            for violation in violations:
                file.write(','.join(map(str, violation)) + '\n')
                fd_row_count += 1

    conn.close()
    print(f"\n\n{fd_row_count} FD violations written to {VIOLATION_FD_PATH}")
    print(f"FD violations loaded into {VIOLATION_FD_PATH} successfully.")

# =====================================================================
# IC violations:
def check_ic_violations():
    # run the schema script to create the fd validation csv file
    with open('../sql/03_validate_ic.sql', 'r') as file:
        sql_file = file.read()
    sql_commands = sql_file.split(';')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    ic_violations = []

    for sql_query in sql_commands:
        if sql_query.strip():
            cursor.execute(sql_query)
            ic_violations.append(cursor.fetchall())

    ic_row_count = 0
    with open(VIOLATION_IC_PATH, 'w') as file:
        for violations in ic_violations:
            for violation in violations:
                file.write(','.join(map(str, violation)) + '\n')
                ic_row_count += 1

    conn.close()

    print(f"\n\n{ic_row_count} IC violations written to {VIOLATION_IC_PATH}")
    print(f"IC violations loaded into {VIOLATION_IC_PATH} successfully.")

# =====================================================================
# CLEANING THE violations:

check_fd_violations()
check_ic_violations()

print(f"---- BEGIN CLEANING THE VIOLATIONS, RECHECK FOR VIOLATIONS ----")

with open("../sql/06_clean_violations.sql", "r") as schema_file:
    subprocess.run(
        ["sqlite3", DB_PATH],
        stdin=schema_file,
        check=True,
    )

check_fd_violations()
check_ic_violations()

print(f"---- TABLES CLEANED ----")

print(f"\n\n---- BUILD FINAL TABLES ----")

with open("../sql/07_final_schema.sql", "r") as schema_file:
    subprocess.run(
        ["sqlite3", DB_PATH],
        stdin=schema_file,
        check=True,
    )

print(f"---- BUILD SUCCESSFUL ----")