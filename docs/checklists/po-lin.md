# Po Lin — Phase-II checklist  [PoLin]

pohungl2@illinois.edu

> Search the repo for `[PoLin]` to find every file waiting on you.

Owns the main Python/pandas cleaning workflow, functional-dependency validation, the final
operational tables, and his portion of provenance and final export.

Code lives in [../../src/](../../src/); FD queries in
[../../sql/05_validate_fd.sql](../../sql/05_validate_fd.sql); final DDL in
[../../sql/06_schema_final.sql](../../sql/06_schema_final.sql).

Also complete the [shared responsibilities](README.md#shared-responsibilities) for each step.

---

## Step 1 — Collect raw datasets into a local repository (group activity)  [PoLin] [Team]

- [x] Confirm unchanged copies of `Menu.csv`, `MenuPage.csv`, `MenuItem.csv`, `Dish.csv`
- [x] Agree on a common repository structure
- [x] Confirm raw files will never be overwritten
- [x] Confirm folder locations for raw data, cleaned data, Python scripts, SQL scripts,
      OpenRefine artifacts, validation outputs, provenance logs, workflow diagrams, report
      figures — see [README.md](README.md#where-artifacts-go)
- [ ] Record raw file row counts and column counts
- [x] Confirm naming conventions for generated files — see [README.md](README.md#naming-conventions)
- [ ] Confirm all team members can access and run the project
- [x] Help establish source-row provenance conventions: `source_file`, `source_row_num`
      (defined in [`src/config.py`](../../src/config.py) `PROVENANCE_COLUMNS`)

### Baseline counts

| File | Rows | Columns |
| --- | --- | --- |
| Menu.csv | | |
| MenuPage.csv | | |
| MenuItem.csv | | |
| Dish.csv | | |

---

## Step 4 — Python/pandas repeatable type-based cleaning  [PoLin]

### Overall Python workflow

- [ ] Create a repeatable Python script or notebook
- [ ] Load all four raw CSV files
- [ ] Preserve raw columns before creating cleaned columns
- [ ] Preserve source-file and source-row identifiers
- [ ] Avoid silently dropping records
- [ ] Make output generation deterministic
- [ ] Make file paths configurable or clearly documented
- [ ] Add readable comments and function names
- [ ] Add validation or sanity checks after each major transformation
- [ ] Record the number of rows and cells affected by each cleaning rule
- [ ] Produce a machine-readable cleaning log
- [ ] Confirm the workflow can be rerun from raw files
- [ ] Save the Python script or notebook as supplementary material
- [ ] Document Step 4 as the inner cleaning workflow W2

### 4.1 Identifier and key fields

Fields: `Menu.id`, `MenuPage.id`, `MenuPage.menu_id`, `MenuItem.id`, `MenuItem.menu_page_id`,
`MenuItem.dish_id`, `Dish.id`

- [ ] Preserve original IDs
- [ ] Trim whitespace
- [ ] Convert IDs into a consistent representation
- [ ] Flag missing required IDs
- [ ] Flag malformed IDs
- [ ] Identify duplicate primary-key values
- [ ] Do not invent missing IDs
- [ ] Preserve optional null `dish_id` values where appropriate
- [ ] Record counts by identifier issue
- [ ] Add identifier-related warning and exclusion reasons

Evidence to retain: missing IDs per column · malformed IDs per column · duplicate IDs per
table · ID values converted or trimmed · examples of malformed values.

### 4.2 String and categorical fields

Fields: `Menu.status`, `Dish.name`

- [ ] Trim leading and trailing whitespace
- [ ] Normalize blank and null-like values
- [ ] Standardize menu status values
- [ ] Create `status_clean`
- [ ] Preserve original dish names
- [ ] Create a cleaned dish-name field if retained in scope
- [ ] Apply only defensible capitalization and punctuation normalization
- [ ] Incorporate Charlene's approved clustering/standardization rules
      (from [../cleaning-rules.md](../cleaning-rules.md))
- [ ] Flag numeric-only dish names
- [ ] Flag symbol-only dish names
- [ ] Avoid automatically merging semantically different dishes
- [ ] Log every changed dish-name value
- [ ] Record distinct dish-name counts before and after

Evidence to retain: status distribution before/after · status cells standardized · dish-name
cells trimmed · dish names standardized · clustered names merged · suspicious names flagged ·
cluster suggestions rejected.

### 4.3 Date and time-period fields

Field: `Menu.date`

- [ ] Preserve raw date values
- [ ] Trim whitespace
- [ ] Parse usable dates and years
- [ ] Create `cleaned_year`
- [ ] Flag missing dates
- [ ] Flag malformed dates
- [ ] Flag impossible years
- [ ] Apply the acceptable year range defined in Step 3
- [ ] Mark unusable dates as ineligible for U1
- [ ] Do not infer corrections without supporting evidence
- [ ] Ensure values such as `1091`, `0190`, or future years are handled per the agreed rule

Evidence to retain: dates parsed · missing dates before/after · invalid dates before/after ·
impossible years · menus excluded due to date · menus remaining eligible for U1.

### 4.4 Currency fields

Fields: `Menu.currency`, `Menu.currency_symbol`

- [ ] Preserve raw currency fields
- [ ] Trim whitespace
- [ ] Standardize agreed currency labels
- [ ] Standardize agreed symbols
- [ ] Compare label and symbol values
- [ ] Flag contradictory combinations
- [ ] Flag missing values
- [ ] Flag ambiguous values
- [ ] Create `currency_clean`
- [ ] Create a currency eligibility or scope field
- [ ] Apply the agreed U1 currency scope
- [ ] Do not perform unsupported historical currency conversion

Evidence to retain: labels standardized · symbols standardized · contradictory combinations ·
missing currency values · ambiguous currencies · menus excluded by currency · menus retained.

### 4.5 Numeric price fields

Fields: `MenuItem.price`, `MenuItem.high_price`, `Dish.lowest_price`, `Dish.highest_price`

- [ ] Preserve raw price values
- [ ] Trim whitespace
- [ ] Convert valid values to numeric
- [ ] Flag malformed values
- [ ] Flag missing values
- [ ] Flag zero values
- [ ] Flag negative values
- [ ] Flag suspicious extreme values
- [ ] Create cleaned numeric columns
- [ ] Check `high_price < price`
- [ ] Check `highest_price < lowest_price`
- [ ] Apply warning or exclusion rules defined in Step 3
- [ ] Confirm parsing does not misinterpret punctuation or formatting

Evidence to retain per column: missing · malformed · zero/non-positive · successfully parsed ·
suspicious · excluded · cells changed.

### 4.6 Fallback pricing logic

Priority order:

- [ ] Use valid `MenuItem.price`
- [ ] Otherwise use valid `MenuItem.high_price`
- [ ] Otherwise average valid `Dish.lowest_price` and `Dish.highest_price`
- [ ] Otherwise use valid `Dish.lowest_price`
- [ ] Otherwise use valid `Dish.highest_price`
- [ ] Otherwise assign `no_valid_price`

Create: `clean_price_candidate` · `price_source`

Allowed `price_source` values (see `src/config.PriceSource`): `menu_item_price` ·
`menu_item_high_price` · `dish_lowest_highest_average` · `dish_lowest_price` ·
`dish_highest_price` · `no_valid_price`

Testing:

- [ ] Test one example for every fallback path
- [ ] Test missing `dish_id`
- [ ] Test malformed dish prices
- [ ] Test non-positive dish prices
- [ ] Confirm invalid prices are not used
- [ ] Confirm averages are calculated only when both values are valid
- [ ] Confirm each row receives only one `price_source`
- [ ] Confirm all-source-missing cases become `no_valid_price`
- [ ] Confirm numeric precision is sufficient

Quantification:

- [ ] Count from `MenuItem.price`
- [ ] Count from `MenuItem.high_price`
- [ ] Count from dish-price average
- [ ] Count from dish lowest price
- [ ] Count from dish highest price
- [ ] Count with no valid price
- [ ] Count recovered through fallback
- [ ] Percentage of usable item records recovered
- [ ] Record limitations of using dish-level values as item-level fallbacks

### 4.7 Exclusion and warning tracking

Create: `cleaning_status` · `warning_reason` · `exclusion_reason` · `source_file` ·
`source_row_num`

- [ ] Define valid status values
- [ ] Distinguish warnings from exclusions
- [ ] Support multiple reasons or document reason precedence
- [ ] Use controlled reason codes
- [ ] Ensure no excluded row disappears without trace
- [ ] Ensure every unusable row has a reason
- [ ] Produce or contribute to `excluded_records.csv`

Reason codes (see `src/config.Reason`): `missing_required_id` · `malformed_id` ·
`missing_date` · `invalid_date` · `missing_currency` · `ambiguous_currency` · `missing_price` ·
`non_positive_price` · `malformed_price` · `no_valid_fallback_price`

Quantification: rows with no warnings · rows with warnings · rows excluded · counts by warning
reason · counts by exclusion reason · counts by source table.

### Step 4 outputs

- [ ] `Menu_cleaned.csv`
- [ ] `MenuPage_cleaned.csv`
- [ ] `MenuItem_cleaned.csv`
- [ ] `Dish_cleaned.csv`
- [ ] `cleaning_log.csv`
- [ ] Preliminary excluded-record file
- [ ] Python script/notebook
- [ ] Data dictionary for generated fields → [../data-dictionary.md](../data-dictionary.md)
- [ ] Change-count summary
- [ ] Inner workflow W2 documentation → [../../workflow/](../../workflow/)

---

## Step 7 — Functional dependency checks  [PoLin]

For each FD:

- [ ] Assign a rule ID
- [ ] State the FD in formal notation
- [ ] Explain it in plain English
- [ ] Write the SQL query
- [ ] Run it against staging data
- [ ] Export violating rows
- [ ] Record violation counts
- [ ] Explain whether violations require repair, warning, or exclusion
- [ ] Add the query to `queries.txt`

Candidate FDs — write them in [../../sql/05_validate_fd.sql](../../sql/05_validate_fd.sql):

- [ ] `Menu.id → cleaned_year, currency_clean, status_clean`
- [ ] `MenuPage.id → menu_id`
- [ ] `MenuItem.id → menu_page_id, dish_id, cleaned price fields`
- [ ] `Dish.id → cleaned name, cleaned lowest price, cleaned highest price`

Additional checks:

- [ ] Identify IDs mapping to multiple conflicting cleaned values
- [ ] Distinguish genuine FD violations from duplicate identical rows
- [ ] Confirm final FD definitions match the actual staging schema
- [ ] Compare violation counts across iterations
- [ ] Provide Madalyn with FD violation exports for Step 8

Deliverables: FD SQL queries · FD rule descriptions · FD violation counts ·
`validation_fd_results.csv` · FD section for `queries.txt` · FD before/after summary.

---

## Step 9 — Define final operational tables  [PoLin]

DDL goes in [../../sql/06_schema_final.sql](../../sql/06_schema_final.sql).

### `final_menu`

- [ ] Define table schema
- [ ] Include `menu_id`, `cleaned_year`, `currency_clean`, `status_clean`
- [ ] Include eligibility or exclusion status if useful
- [ ] Ensure one row per menu
- [ ] Ensure `menu_id` is unique
- [ ] Include only menus eligible for U1, or clearly distinguish eligible records

### `final_item`

- [ ] Define table schema
- [ ] Include `menu_item_id`, `menu_id`, `menu_page_id`, `dish_id`
- [ ] Include `clean_item_price`, `price_source`
- [ ] Include relevant raw price values for provenance
- [ ] Include relevant dish-level price values
- [ ] Ensure every final item references a final menu
- [ ] Ensure every final item has a valid positive price
- [ ] Ensure every final item has exactly one price source

### U1 readiness

- [ ] Count valid menu items per menu
- [ ] Define any minimum valid-item threshold
- [ ] Compute average cleaned item price per menu
- [ ] Group menus by comparable time periods
- [ ] Confirm all grouped menus use comparable currencies
- [ ] Produce a preliminary `$`, `$$`, `$$$`, `$$$$` categorization method
- [ ] Run at least one representative U1 query
- [ ] Compare raw-data results to cleaned-data results
- [ ] Explain why raw results were incomplete, distorted, or misleading
- [ ] Confirm that D′ is fit for U1

Deliverables: final operational DDL · population SQL or Python · final table data dictionary ·
final menu-level metrics · U1 demonstration query/results · final operational validation summary.

---

## Step 10 — Final export and provenance (Po's portion)  [PoLin] [Team]

- [ ] Export or verify `final_menu.csv`
- [ ] Export or verify `final_item.csv`
- [ ] Finalize Python-derived `cleaning_log.csv`
- [ ] Finalize Python-derived excluded-record evidence
- [ ] Verify source-row traceability
- [ ] Verify every Python transformation is documented
- [ ] Add Python scripts/notebooks to supplementary materials
- [ ] Add W2 source and rendered workflow files
- [ ] Provide Step 4 and Step 9 narrative sections
- [ ] Provide counts of cells and rows changed by Python rules
- [ ] Provide personal contribution summary
- [ ] Verify filenames used in the report match actual files
