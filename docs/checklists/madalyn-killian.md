# Madalyn Killian — Phase-II checklist  [MadalynKillian]

killian7@illinois.edu

Owns the SQLite staging layer, loading cleaned files, inclusion-dependency validation,
violation exports and iteration coordination, and her portion of provenance and final export.

Scripts live in [../../sql/](../../sql/);
violation exports in `data/reports/`; 

---

## Step 1 — Collect raw datasets into a local repository (group activity)  [MadalynKillian] [Team]

- [X] Confirm access to all raw and cleaned data folders
- [x] Confirm SQLite database location — `data/cs513_team38.sqlite` (git-ignored)
- [x] Confirm SQL script folder structure — [../../sql/](../../sql/)
- [x] Confirm validation-output folder structure — `data/reports/`
- [x] Confirm naming conventions for SQLite database files, DDL scripts, load scripts,
      validation scripts, violation exports, iteration outputs — see
      [README.md](README.md#naming-conventions)
- [x] Confirm raw files remain unchanged
- [x] Help record baseline file counts
- [ ] Confirm SQLite version and execution environment (`sqlite3 --version`; Python's
      stdlib `sqlite3` module reports its own via `sqlite3.sqlite_version`)
- [ ] Confirm all team members can access or recreate the database

## Step 5 — Define or revise the SQLite staging schema  [MadalynKillian]

DDL goes in [../../sql/01_schema_staging.sql](../../sql/01_schema_staging.sql).

### Staging tables

Create or revise: `stg_menu` · `stg_menu_page` · `stg_menu_item` · `stg_dish`

### Schema design

- [X] Match SQLite types to cleaned pandas outputs
- [ ] Include raw and cleaned columns where needed
- [ ] Include provenance columns
- [ ] Include warning columns
- [ ] Include exclusion columns
- [ ] Include price-source fields
- [ ] Include source-file and source-row fields
- [X] Define primary-key expectations
- [ ] Define not-null expectations
- [ ] Define controlled-value checks where practical
- [ ] Decide which constraints are enforced during load
- [ ] Decide which constraints are checked afterward through validation queries
- [ ] Add useful indexes for joins and validation
- [ ] Document SQLite's flexible typing limitations
- [ ] Use `STRICT` tables if appropriate and supported, or compensate with explicit validation
      queries
- [ ] Keep staging tables source-shaped rather than prematurely creating the final analysis model


### Schema review

- [ ] Compare expected pandas dtypes to SQLite column definitions
- [ ] Review schema with Po before loading
- [ ] Revise schema after cleaning-field changes
- [ ] Record all schema revisions → [../iteration-log.md](../iteration-log.md)
- [ ] Explain why staging is separate from final operational tables

Deliverables: SQLite DDL script · staging data dictionary · schema-revision log · index
definitions · staging schema diagram or table summary · Step 5 narrative and rationale.

---

## Step 6 — Load cleaned CSVs into SQLite staging tables  [MadalynKillian]

Load script goes in [../../sql/02_load_staging.sql](../../sql/02_load_staging.sql).

Load: `Menu_cleaned.csv` · `MenuPage_cleaned.csv` · `MenuItem_cleaned.csv` · `Dish_cleaned.csv`

For each file:

- [ ] Record expected row count
- [ ] Load into the matching staging table
- [ ] Record actual row count
- [ ] Record rejected rows
- [ ] Record load warnings
- [ ] Confirm delimiter and encoding
- [ ] Confirm null handling
- [ ] Confirm numeric values did not become incorrect text values
- [ ] Confirm year fields loaded correctly
- [ ] Confirm IDs loaded consistently
- [ ] Confirm provenance columns loaded
- [ ] Reconcile CSV counts against SQLite counts
- [ ] Explain every discrepancy
- [ ] Save load command or script
- [ ] Save load logs

Post-load checks:

- [ ] Count rows in every staging table
- [ ] Inspect sample rows
- [ ] Check SQLite `typeof()` values for key cleaned columns
- [ ] Check null counts after loading
- [ ] Confirm no unexpected truncation
- [ ] Confirm clean-price numeric precision
- [ ] Confirm all intended columns exist

Reconcile against the raw baselines recorded in Step 1.

Deliverables: load script · load logs · CSV-to-SQLite reconciliation table · staging row-count
report · type-check report · Step 6 narrative and rationale.

---

## Step 7 — Inclusion dependency checks  [MadalynKillian]

Queries go in [../../sql/04_validate_ind.sql](../../sql/04_validate_ind.sql).

For every IND:

- [ ] Assign a rule ID
- [ ] State the inclusion dependency formally
- [ ] Explain it in plain English
- [ ] Write the SQLite query
- [ ] Run it on staging data
- [ ] Export violating rows
- [ ] Record violation counts
- [ ] Compare counts across iterations
- [ ] Explain whether violations require repair or exclusion
- [ ] Add the query to `queries.txt`

Candidate INDs:

- [ ] `stg_menu_page.menu_id ⊆ stg_menu.id`
- [ ] `stg_menu_item.menu_page_id ⊆ stg_menu_page.id`
- [ ] Non-null `stg_menu_item.dish_id ⊆ stg_dish.id`
- [ ] `final_item.menu_id ⊆ final_menu.menu_id`
- [ ] Final item source references resolve to staging/source rows
- [ ] Any generated final-table foreign keys resolve properly

Additional checks:

- [ ] Count orphan menu pages
- [ ] Count orphan menu items by page
- [ ] Count non-null orphan dish references
- [ ] Distinguish missing optional references from broken required references
- [ ] Record examples of each violation type
- [ ] Confirm NULL semantics are handled correctly in `NOT EXISTS` or anti-join queries
- [ ] Avoid `NOT IN` where nullable values could cause misleading results

> On the `NOT IN` warning — it is a real correctness trap, not style. If the subquery returns
> even one NULL, `x NOT IN (subquery)` evaluates to NULL (not TRUE) for every row, so the query
> returns **zero violations** and the constraint looks like it passes. `MenuItem.dish_id` is
> known to contain NULLs, so the dish reference check is exactly where this would bite. A
> `LEFT JOIN ... IS NULL` anti-join or `NOT EXISTS` is NULL-safe.
>
> The Phase-I inspection already found `MenuPage.menu_id` values absent from `Menu.id`, so
> expect violations from the first run. Missing *optional* references (NULL `dish_id`) are a
> different finding with a different disposition — report them separately.

Deliverables: IND SQL queries · IND rule descriptions · IND violation counts ·
`validation_ind_results.csv` · IND section for `queries.txt` · before/after IND summary.

---

## Step 8 — Export violating rows and repeat the cleaning loop  [MadalynKillian]

Record everything in [../iteration-log.md](../iteration-log.md).

### Violation exports

Collect:

- [ ] IC/domain violations from Charlene
- [ ] IND violations from Madalyn
- [ ] FD violations from Po

Each violation export must include:

- [ ] Rule ID
- [ ] Rule category
- [ ] Source table
- [ ] Relevant row ID
- [ ] Source row number
- [ ] Raw values
- [ ] Cleaned values
- [ ] Violation reason
- [ ] Iteration number
- [ ] Proposed disposition

Files: `validation_ic_results.csv` · `validation_ind_results.csv` ·
`validation_fd_results.csv` · any domain-specific violation files · combined iteration summary.

### Violation review

For each category, determine whether the cause is:

- [ ] Dirty raw data
- [ ] An incomplete cleaning rule
- [ ] An incorrect cleaning rule
- [ ] A staging/load problem
- [ ] Unavoidable ambiguity

Then:

- [ ] Assign disposition: repair · warning · exclusion · accepted limitation
- [ ] Route required Python changes to Po
- [ ] Route rule-definition changes to Charlene
- [ ] Revise SQLite schema or loading logic when necessary
- [ ] Rerun Steps 5–7 after new cleaned files are produced
- [ ] Preserve outputs from every iteration

### Iteration metrics

Record per iteration: IC violations · IND violations · FD violations · domain violations ·
number repaired · newly warned · newly excluded · remaining · new rules added · rules modified ·
schema changes · change in U1-eligible records · reason another iteration was or was not
performed.

### Stopping rationale

- [ ] Define criteria for stopping the loop
- [ ] Confirm remaining violations do not invalidate U1
- [ ] Confirm remaining problematic rows are excluded or documented
- [ ] Document unresolved limitations
- [ ] Explain how the actual iterative workflow differed from Phase I
- [ ] Add the validation feedback loop to W1

> Define the stopping criteria **before** iterating, not after. Without them the loop either
> runs forever or stops arbitrarily, and "we stopped when it looked good" is not a rationale.
> Record the agreed criteria in [../iteration-log.md](../iteration-log.md).

Deliverables: iteration-specific violation files · iteration log · combined validation summary ·
updated schema/load scripts · final unresolved-violation list · Step 8 narrative and stopping
rationale.

---

## Step 10 — Final export and provenance (Madalyn's portion)  [MadalynKillian] [Team]

- [ ] Finalize `validation_report.csv`
- [ ] Finalize IC/IND/FD combined summary
- [ ] Finalize SQLite database or recreation scripts
- [ ] Finalize staging DDL
- [ ] Finalize load scripts
- [ ] Finalize IND queries
- [ ] Finalize violation exports
- [ ] Finalize iteration logs
- [ ] Add SQLite scripts to supplementary materials
- [ ] Add all SQL queries to `queries.txt`
- [ ] Confirm row-count reconciliation
- [ ] Confirm final validation files match report counts
- [ ] Provide narrative for Steps 5, 6, and 8
- [ ] Provide narrative for the IND portion of Step 7
- [ ] Explain SQLite tool selection
- [ ] Add staging, loading, validation, and iteration steps to W1
- [ ] Provide personal contribution summary
