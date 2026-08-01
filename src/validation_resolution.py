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

subprocess.run([sys.executable, SETUP], check=True)

# =====================================================================
# FC VIOLATIONS:

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

with open(VIOLATION_FD_PATH, 'w') as file:
    for violations in fd_violations:
        for violation in violations:
            file.write(','.join(map(str, violation)) + '\n')

conn.close()

print(f"FD violations loaded into {VIOLATION_FD_PATH} successfully.")

# FD-4: 
# option 1: for the price and blank, go through and drop all of the dupes where price is blank, could be iterativly innificient
# for conflicting prices, make an average.

# no instances of fd1,2,3



# =====================================================================
# IC VOILATIONS:

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

with open(VIOLATION_IC_PATH, 'w') as file:
    for violations in ic_violations:
        for violation in violations:
            file.write(','.join(map(str, violation)) + '\n')

conn.close()

print(f"IC violations loaded into {VIOLATION_IC_PATH} successfully.")