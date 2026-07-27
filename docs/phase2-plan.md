# Initial Plan for Phase-II

> Phase-I rubric item 4 (15 pts): steps S1–S5 with tool choices, owner assignment, timeline.

## Owners

Phase-I assignment (as submitted):

| Step | Owner | Scope |
| --- | --- | --- |
| S1 | Madalyn Killian (MK) | Review/update use case and dataset descriptions |
| S2 | Madalyn Killian (MK) | Profile D to identify DQ problems |
| S3 | Po Lin (P) | Perform data cleaning proper |
| S4 | Po Lin (P) | Data quality checking — is D′ really cleaner than D? |
| S5 | Charlene Khun (CK) | Document and quantify change |

**Superseded in Phase-II.** Work is now split by workflow step and tool rather than by whole
S-steps, so all three members contribute across S3–S5:

| Owner | Steps |
| --- | --- |
| Charlene Khun | 2 (OpenRefine profiling), 3 (cleaning-rule catalog), 7 IC/domain checks |
| Madalyn Killian | 5 (SQLite staging), 6 (load), 7 IND checks, 8 (violations & iteration) |
| Po Lin | 4 (Python/pandas cleaning), 7 FD checks, 9 (final operational tables) |

Steps 1 and 10 are shared. Per-person detail: [checklists/](checklists/).

## Tooling changes from Phase-I

| Item | Phase-I plan | Phase-II actual | Note |
| --- | --- | --- | --- |
| SQL engine | MySQL | **SQLite** | Record the reason in the Phase-II report |
| Task split | Whole S-steps per member | Split by workflow step and tool | Step 7 divides naturally into IC / IND / FD, which no single member owned before |

Both are deviations the Phase-II rubric asks you to report and explain — tracked in
[checklists/team.md](checklists/team.md#plan-vs-actual-differences-to-report).

## S1 — Review dataset and use case

Confirm the columns in scope for U1 (table in
[dataset-description.md](dataset-description.md#columns-used-for-u1)) and update the
descriptions if profiling contradicts them.

## S2 — Profile D

Tools: **OpenRefine** (initial profiling), **Python** (loading), **SQL**, LLM assistance
where permitted by course guidelines.

## S3 — Perform data cleaning

An iterative pipeline combining local file management, OpenRefine, Python/pandas, MySQL, and
AI-assisted code generation where appropriate and permitted.

### Step 1 — Collect raw datasets into a local repository

Keep the original files unchanged. The repository also stores OpenRefine profiling notes,
screenshots/evidence of dirty data, Python/pandas cleaning scripts, cleaned CSV outputs, SQL
schema/load scripts, SQL validation scripts, violation reports, cleaning logs, provenance
documentation, and final cleaned outputs. This preserves D, generates cleaned outputs
separately, and documents how D becomes D′.

### Step 2 — Profile relevant columns in OpenRefine

OpenRefine is used for **profiling and review, not as the main cleaning tool**, due to the
size of the data and its memory requirements on larger files. Profile all U1-relevant
columns for: missing values, blank values, unusual values, value distributions,
invalid-looking dates, currency inconsistencies, zero/suspicious prices, malformed numeric
fields, potential outliers, and examples to include in the report.

### Step 3 — Define cleaning requirements from profiling

Convert observed problems into explicit cleaning requirements and expected data types per
column. This is iterative (see Step 8). Examples:

- IDs preserved and converted into consistent ID formats where possible.
- String fields trimmed and standardized where appropriate.
- Date fields parsed into usable years / time periods.
- Price fields converted into valid numeric values.

### Step 4 — Python/pandas repeatable, type-based cleaning

Produces cleaned CSVs for SQL loading. The goal is correct shape and types — **not** the
final joined analysis model.

**4.1 Identifier / key fields** — `Menu.id`, `MenuPage.id`, `MenuPage.menu_id`,
`MenuItem.id`, `MenuItem.menu_page_id`, `MenuItem.dish_id`, `Dish.id`.
Preserve original ID values; trim whitespace; convert to a consistent numeric/string ID
format; flag missing or malformed required IDs; **do not invent missing IDs**; keep original
row numbers for provenance.

**4.2 String / categorical fields** — `Menu.status`, `Dish.name`.
Trim whitespace; standardize obvious capitalization; normalize blank/null-like values;
preserve originals where useful for provenance; create cleaned versions of important
categorical fields; establish acceptable values (enums).

**4.3 Date / time-period fields** — `Menu.date`.
Trim whitespace; parse usable years; create `cleaned_year`; flag missing, malformed, or
impossible dates; mark rows with unusable dates for exclusion from U1.

**4.4 Currency fields** — `Menu.currency`, `Menu.currency_symbol`.
Trim whitespace; standardize obvious currency labels and symbols; compare `currency` against
`currency_symbol` when both exist; create `currency_clean` / `currency_scope`; flag missing,
ambiguous, or non-comparable currencies; likely mark only dollar-denominated/comparable
menus as usable for U1.

**4.5 Numeric price fields** — `MenuItem.price`, `MenuItem.high_price`,
`Dish.lowest_price`, `Dish.highest_price`.
Preserve original raw values; trim whitespace; convert to numeric where possible; flag
blanks, malformed values, zero/negative values, and suspicious/extreme values; create
cleaned numeric price columns.

**4.6 Fallback pricing logic**

Profiling showed a significant number of missing prices, so item price is resolved in order:

1. `MenuItem.price` if present and valid.
2. Else `MenuItem.high_price` if present and valid.
3. Else the average of `Dish.lowest_price` and `Dish.highest_price` if both are present and valid.
4. Else `Dish.lowest_price` if valid.
5. Else `Dish.highest_price` if valid.
6. Else mark the item as having no valid price and exclude it from price-based analysis.

The cleaned MenuItem CSV records `clean_price_candidate` and `price_source`, where
`price_source` ∈ {`menu_item_price`, `menu_item_high_price`, `dish_lowest_highest_average`,
`dish_lowest_price`, `dish_highest_price`, `no_valid_price`}.

**4.7 Exclusion and warning tracking**

Rows are **flagged, not dropped**, which keeps provenance intact for D → D′ analysis.
Flag columns: `cleaning_status`, `warning_reason`, `exclusion_reason`, `source_file`,
`source_row_num`.

Reasons include (not limited to): `missing_required_id`, `malformed_id`, `missing_date`,
`invalid_date`, `missing_currency`, `ambiguous_currency`, `missing_price`,
`non_positive_price`, `malformed_price`, `no_valid_fallback_price`.

### Step 5 — Define/revise the SQL staging schema

Cleaning outputs: `Menu_cleaned.csv`, `MenuPage_cleaned.csv`, `MenuItem_cleaned.csv`,
`Dish_cleaned.csv`, `cleaning_log.csv`. Staging tables: `stg_menu`, `stg_menu_page`,
`stg_menu_item`, `stg_dish`. If pandas cleaning logic changes in a later iteration, the
staging schema may need revision too.

### Step 6 — Load cleaned CSVs into SQL staging

Data is already cleaned and type-normalized by pandas; SQL becomes the validation layer.

### Step 7 — Run SQL IC, IND, FD, and domain validation checks

- **IC** — integrity/domain constraints, e.g. "`Menu.cleaned_year` should be valid if the
  menu is used for U1."
- **IND** — inclusion dependencies, e.g. "`MenuPage.menu_id` should reference `Menu.id`."
- **FD** — functional dependencies, e.g.
  "`Dish.id → name, cleaned_lowest_price, cleaned_highest_price`."

### Step 8 — Export violating rows and repeat the loop

Violations export by type: `validation_ic_results.csv`, `validation_ind_results.csv`,
`validation_fd_results.csv`. Examine each separately and repeat Steps 2–7 until the staged
data is acceptable for U1 and usable records are exhausted. Keep every iteration's output
rows as provenance.

### Step 9 — Define final operational tables

- `final_menu`: `menu_id`, `cleaned_year`, `currency_clean`, `status_clean`
- `final_item`: `menu_item_id`, `menu_id`, `menu_page_id`, `dish_id`, `clean_item_price`,
  `price_source`, `original_price`, `original_high_price`, `dish_lowest_price`,
  `dish_highest_price`

### Step 10 — Export D′, validation reports, excluded records, provenance logs

`final_menu.csv`, `final_item.csv`, `cleaning_log.csv`, `excluded_records.csv`,
`validation_report.csv`.

## S4 — Data quality checks

S3 produces most of the evidence; S4 analyzes the output files.

**Cleaned source CSVs** — Did each load successfully into staging? Do cleaned columns match
expected types? Were original IDs and source row identifiers preserved? Which fields were
changed, standardized, or flagged? Which rows were marked unusable?

**SQL validation outputs** — Which ICs passed/failed? Which INDs failed? Which FD checks
showed violations? How many rows violated each rule? Are violations severe enough to require
another cleaning iteration? Can remaining violations be safely excluded from U1?

**Violation CSVs** — Are violations caused by dirty raw values or by our cleaning logic? Do
they reveal a pattern we did not account for? Can records be repaired with a better rule?
Should they be excluded? Do we need to repeat S3 Steps 2–7?

**Cleaning log** — What rules were applied? Which columns did each affect? How many rows
were changed, flagged, or excluded per rule? Were new rules added after reviewing validation
failures? How did the pricing fallback perform — how many records did it save? Can we
explain D → D′ from this log?

**Before/after summary** — How many missing dates, missing/invalid prices, ambiguous currency
values, and broken references existed before cleaning? How many records were repaired,
standardized, or excluded?

## S5 — Document and quantify change

Columns and cells changed, IC violations detected before vs. after, and the summary tables
required by the Phase-II rubric.

## Timeline  [Team]

| Window | Steps | Owner |
| --- | --- | --- |
| _TBD_ | S1, S2 | MK |
| _TBD_ | S3 (Steps 1–4) | P |
| _TBD_ | S3 (Steps 5–10) | P |
| _TBD_ | S4 | P |
| _TBD_ | S5 + report assembly | CK (all review) |

> Fill in dates from the **Key Dates** posting on Coursera/Campuswire, backing off the
> Phase-II due date. The rubric explicitly asks for a timeline.
