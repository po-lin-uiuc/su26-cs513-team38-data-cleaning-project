# SQL — validation layer

Implements S3 steps 5–10 of [../docs/phase2-plan.md](../docs/phase2-plan.md). By the time
data reaches SQL it is already cleaned and type-normalized by pandas; **SQL's job is to prove
the constraints hold**, not to clean.

Target engine: **SQLite** (changed from the Phase-I plan's MySQL — record the reason in the
report; see [../docs/checklists/team.md](../docs/checklists/team.md#plan-vs-actual-differences-to-report)).

Database file: `data/cs513_team38.sqlite` — git-ignored, because it is a build artifact.
Reproducibility comes from the scripts here, which are tracked.

## Run order

| Script | Step | Owner | Purpose |
| --- | --- | --- | --- |
| `01_schema_staging.sql` | 5 | Madalyn `[MadalynKillian]` | `stg_menu`, `stg_menu_page`, `stg_menu_item`, `stg_dish` |
| `02_load_staging.sql` | 6 | Madalyn `[MadalynKillian]` | Load `data/interim/*_cleaned.csv` into staging |
| `03_validate_ic.sql` | 7 | Charlene `[CharleneKhun]` | Integrity / domain constraints |
| `04_validate_ind.sql` | 7 | Madalyn `[MadalynKillian]` | Inclusion dependencies |
| `05_validate_fd.sql` | 7 | Po `[PoLin]` | Functional dependencies |
| `06_schema_final.sql` | 9 | Po `[PoLin]` | `final_menu`, `final_item` — the D′ operational tables |

```powershell
sqlite3 data\cs513_team38.sqlite ".read sql/01_schema_staging.sql"
```

Steps 7–8 loop: export violations to `data/reports/`, review them in OpenRefine, tighten the
pandas rules, re-run. Keep each iteration's output as provenance — see
[../docs/iteration-log.md](../docs/iteration-log.md).

## Before you start

**The `sqlite3` CLI is not installed on this machine.** It ships separately on Windows
(download the "sqlite-tools" bundle from sqlite.org, or `winget install SQLite.SQLite`).
This matters because `.import`, `.mode`, and the other dot commands are *CLI* features —
Python's `sqlite3` module and every other driver will reject them. Either install the CLI or
write the load in Python, and document which in the Step 6 narrative.

Python's stdlib `sqlite3` is fine for running the plain-SQL scripts:

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/cs513_team38.sqlite'); c.executescript(open('sql/03_validate_ic.sql').read())"
```

## Conventions

- Every validation query returns **violating rows**, so an empty result means the constraint
  holds. Give each rule a stable ID (`IC-n`, `IND-n`, `FD-n`) and a plain-English statement.
- Include source identifiers (`id`, `source_row_num`) in violation output, so Step 8 can trace
  a violation back to its raw row.
- Run the checks against staging loaded from **raw** as well as from cleaned data. Without the
  "before" run there is no before/after comparison, which is what the rubric grades.

### SQLite specifics worth knowing

- **Type affinity, not enforcement.** A plain `INTEGER` column will happily store `'abc'`.
  `STRICT` tables (3.37+) enforce declared types; `typeof(col)` shows what was actually stored.
- **No `REGEXP`** by default — use `GLOB` (e.g. `'*[A-Za-z]*'`) or `LIKE`.
- **`NOT IN` with NULLs** silently returns zero rows. Use `NOT EXISTS` or a
  `LEFT JOIN ... IS NULL` anti-join for inclusion checks.
- **Window functions** (`NTILE`, etc.) are available from 3.25.

## Deliverable

`queries.txt` is the required supplementary file: all profiling and IC-checking queries in one
plain-text file. Assemble it at the end from the scripts here rather than maintaining it in
parallel:

```powershell
Get-ChildItem sql\0*.sql | ForEach-Object {
    "-- ===== $($_.Name) =====", (Get-Content $_.FullName -Raw)
} | Set-Content sql\queries.txt
```
