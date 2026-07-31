import os
import sqlite3
import pandas as pd

# THIS FILE TAKES THE VALIDATION RESULTS FROM THE SQL FILES AND COMPARES THEM

# CLEANED DATA PATH: change as needed
DB_PATH = "../data/cs513_team38.sqlite"

# functional dependency violations: x determines y, etc.
VIOLATION_FD_PATH = "../data/interim/validation_fd_results.csv"

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
            # print(violation)
            file.write(','.join(map(str, violation)) + '\n')
            # break
        # print(len(violations))
        # break
        # file.write(','.join(map(str, row)) + '\n')