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
- [x] Record raw file row counts and column counts
- [x] Confirm naming conventions for generated files — see [README.md](README.md#naming-conventions)
- [ ] Confirm all team members can access and run the project — **blocked on Charlene and Madalyn
      confirming**; the data archive and setup instructions went out over Slack
- [x] Help establish source-row provenance conventions: `source_file`, `source_row_num`
      (defined in [`src/config.py`](../../src/config.py) `PROVENANCE_COLUMNS`)

### Baseline counts

Raw files, read as text so nothing is coerced away.

| File | Rows | Columns |
| --- | --- | --- |
| Menu.csv | 17,545 | 20 |
| MenuPage.csv | 66,937 | 7 |
| MenuItem.csv | 1,332,726 | 9 |
| Dish.csv | 423,397 | 9 |

Row counts after the preliminary OpenRefine filtering, which is what the pipeline actually reads:

| File | Rows | Columns |
| --- | --- | --- |
| Menu_OR.csv | 5,236 | 4 |
| MenuPage_OR.csv | 66,937 | 2 |
| MenuItem_OR.csv | 1,332,668 | 5 |
| Dish_OR.csv | 394,297 | 4 |

---

## Step 4 — Python/pandas repeatable type-based cleaning  [PoLin]

> **Two design deviations affect many boxes below. Both were deliberate; both need recording in
> the report and reconciling with [../data-dictionary.md](../data-dictionary.md), which still
> describes the original plan.**
>
> 1. **Columns are cleaned in place, not duplicated.** The plan called for `cleaned_year`,
>    `currency_clean`, `status_clean`, `name_clean` alongside preserved raw columns. Instead the
>    pipeline rewrites `currency`, `name`, and the price columns in place, adds `year`/`month`/`day`,
>    and drops `date` and `status`. Provenance is preserved by the per-stage snapshots and the
>    cell-level change logs rather than by parallel columns.
> 2. **One `log` column replaces three flag columns.** `cleaning_status`, `warning_reason`, and
>    `exclusion_reason` are not written. A single accumulating `log` column carries
>    `<column>:<operation>` tags instead, plus an `omit` column on MenuItem.

### Overall Python workflow

- [x] Create a repeatable Python script or notebook — [`src/`](../../src/), entry point
      `python -m src.run_pipeline`
- [ ] Load all four raw CSV files — **the pipeline reads the four `*_OR.csv` exports, not the raw
      CSVs.** Raw files are never opened by the pipeline; OpenRefine is the first pass
- [ ] Preserve raw columns before creating cleaned columns — **see deviation 1.** Originals are
      recoverable from the stage snapshots and change logs, not from parallel columns
- [x] Preserve source-file and source-row identifiers — `source_file`, `source_row_num` stamped at
      load, carried through every stage snapshot
- [x] Avoid silently dropping records — only MenuItem loses rows (236), written to
      `MenuItem_omitted.csv` with the reason on each row
- [x] Make output generation deterministic — verified by rerunning and comparing SHA-256 hashes; no
      artifact contains a timestamp
- [x] Make file paths configurable or clearly documented — all paths derive from
      `config.TABLES`
- [x] Add readable comments and function names
- [x] Add validation or sanity checks after each major transformation — each stage reports counts
      and warns on anomalies
- [x] Record the number of rows and cells affected by each cleaning rule — per-stage summaries
- [x] Produce a machine-readable cleaning log — `data/reports/cleaning_log.csv`, 24 rule
      applications
- [ ] Confirm the workflow can be rerun from raw files — **rerunnable from the OpenRefine exports,
      not from raw.** Rerunning from raw would require re-running the OpenRefine recipe
- [ ] Save the Python script or notebook as supplementary material — code exists; not yet copied
      into `deliverables/phase2/supplementary/`
- [x] Document Step 4 as the inner cleaning workflow W2 — [../../workflow/](../../workflow/),
      annotated in source, 21 blocks, rendered to `.gv` + `.png`

### 4.1 Identifier and key fields

Fields: `Menu.id`, `MenuPage.id`, `MenuPage.menu_id`, `MenuItem.id`, `MenuItem.menu_page_id`,
`MenuItem.dish_id`, `Dish.id`

- [x] Preserve original IDs — values unchanged; only the representation is normalized
- [x] Trim whitespace — `normalize_text`
- [x] Convert IDs into a consistent representation — nullable `Int64`, so a column holding absent
      values is not widened to float. This caught `dish_id` writing as `1.0` instead of `1`
- [x] Flag missing required IDs — `Reason.MISSING_REQUIRED_ID`; 239 rows on `MenuItem.dish_id`
- [x] Flag malformed IDs — `Reason.MALFORMED_ID`; zero occurrences in the current export
- [ ] **Identify duplicate primary-key values — NOT DONE.** No duplicate-key check exists in the
      pipeline. Add one here, or rely on the SQL primary-key constraint in Step 7 and say so
- [x] Do not invent missing IDs — unparseable values become null and are flagged
- [x] Preserve optional null `dish_id` values where appropriate — 239 kept; 3 survive the omit
      check because they carry a price of their own
- [x] Record counts by identifier issue — in each stage summary
- [x] Add identifier-related warning and exclusion reasons — `config.Reason`

Evidence to retain: missing IDs per column · malformed IDs per column · **duplicate IDs per
table (missing)** · ID values converted or trimmed · examples of malformed values.

### 4.2 String and categorical fields

Fields: `Menu.status`, `Dish.name`

- [x] Trim leading and trailing whitespace — zero occurrences; OpenRefine had already trimmed
- [x] Normalize blank and null-like values — `config.NULL_LIKE_VALUES`
- [ ] Standardize menu status values — **not applicable as written.** `status` was constant
      (`complete`) after the preliminary filter, so the column was dropped instead of standardized.
      The rule refuses to drop if it is not constant
- [ ] Create `status_clean` — **not created**; see above and deviation 1
- [x] Preserve original dish names — in the change log and the `func-id-numeric` snapshot, not in a
      parallel column
- [ ] Create a cleaned dish-name field if retained in scope — **`name` is cleaned in place**; no
      `name_clean` column exists (deviation 1)
- [x] Apply only defensible capitalization and punctuation normalization — uppercase, accent
      folding, separator-to-space, punctuation removal; no semantic rewriting
- [ ] Incorporate Charlene's approved clustering/standardization rules — **blocked**;
      [../cleaning-rules.md](../cleaning-rules.md) is still empty
- [ ] Flag numeric-only dish names — **NOT DONE.** Symbol-only names become `UNKNOWN`, but a purely
      numeric name (`1900 4103`) passes through unflagged. This is problem P2 and is only half
      addressed
- [x] Flag symbol-only dish names — 647 marked `UNKNOWN`
- [x] Avoid automatically merging semantically different dishes — no clustering is applied; the
      40,721 collapses are all exact matches after normalization
- [ ] Log every changed dish-name value — **partially.** Row-level entries are written for 110,827
      of the 383,289 changed names; the excluded ones changed by capitalization alone. Every
      operation is still counted in the summary
- [x] Record distinct dish-name counts before and after — 390,201 → 349,480

Evidence to retain: status distribution before/after · status cells standardized · dish-name
cells trimmed · dish names standardized · **clustered names merged (pending Charlene)** ·
suspicious names flagged · **cluster suggestions rejected (pending Charlene)**.

### 4.3 Date and time-period fields

Field: `Menu.date`

- [x] Preserve raw date values — in `Menu_after_id-numeric.csv`, one stage upstream; `date` is
      dropped from the cleaned output once the parts exist
- [x] Trim whitespace — `normalize_text`
- [x] Parse usable dates and years — all 5,236 parsed
- [ ] Create `cleaned_year` — **named `year`, not `cleaned_year`**, and accompanied by `month` and
      `day` (deviation 1). Update the data dictionary to match
- [x] Flag missing dates — `Reason.MISSING_DATE`; zero in the current export
- [x] Flag malformed dates — `Reason.INVALID_DATE`; zero in the current export
- [x] Flag impossible years — rejected outside `MIN_PLAUSIBLE_YEAR`–`MAX_PLAUSIBLE_YEAR`
- [ ] Apply the acceptable year range defined in Step 3 — **the range is implemented but not yet
      ratified.** 1840–2026 is marked `PROPOSED` in `config.py`, pending Charlene's Step 3
- [x] Mark unusable dates as ineligible for U1 — a null `year` marks it; zero cases, since the
      preliminary OpenRefine filter already excluded them
- [x] Do not infer corrections without supporting evidence — no date is ever repaired
- [x] Ensure values such as `1091`, `0190`, or future years are handled per the agreed rule —
      unit-tested against all five real impossible values; observed range is 1851–2012

Evidence to retain: dates parsed · missing dates before/after · invalid dates before/after ·
impossible years · menus excluded due to date · menus remaining eligible for U1.

### 4.4 Currency fields

Fields: `Menu.currency`, `Menu.currency_symbol`

- [x] Preserve raw currency fields — every `Dollars` → `USD` change is in
      `Menu_changes_currency-map.csv`
- [x] Trim whitespace — `normalize_text`
- [x] Standardize agreed currency labels — `CURRENCY_MAP`, 5,236 rows mapped
- [ ] Standardize agreed symbols — **not applicable.** `currency_symbol` is blank on exactly the
      same 11,089 raw rows as `currency`, so it carries no independent signal and was dropped
- [ ] Compare label and symbol values — **a documented no-op, not a skipped step.** With the symbol
      column dropped there is nothing to compare; the justification is the blank-for-blank
      correlation above
- [ ] Flag contradictory combinations — **zero possible**, for the same reason
- [x] Flag missing values — `Reason.MISSING_CURRENCY`
- [x] Flag ambiguous values — `Reason.AMBIGUOUS_CURRENCY` for any label outside `CURRENCY_MAP`;
      zero in the current export
- [ ] Create `currency_clean` — **the column is named `currency` and cleaned in place**
      (deviation 1)
- [ ] Create a currency eligibility or scope field — **NOT DONE.** Eligibility is currently implicit
      in the OpenRefine filter rather than represented as a column. Worth adding if any non-dollar
      menu is ever admitted
- [x] Apply the agreed U1 currency scope — dollars only
- [x] Do not perform unsupported historical currency conversion — investigated and rejected; see
      the report §1.2 and §A.2

Evidence to retain: labels standardized · symbols standardized · contradictory combinations ·
missing currency values · ambiguous currencies · menus excluded by currency · menus retained.

### 4.5 Numeric price fields

Fields: `MenuItem.price`, `MenuItem.high_price`, `Dish.lowest_price`, `Dish.highest_price`

- [x] Preserve raw price values — in the `func-id-numeric` snapshot, one stage upstream
- [x] Trim whitespace — `normalize_text`
- [x] Convert valid values to numeric — rendered to two decimals; blanks stay blank so P4 stays
      distinct from P5
- [x] Flag malformed values — `Reason.MALFORMED_PRICE`; **zero occurrences**, no price value in any
      of the four columns is non-numeric. A measured zero, not a skipped check
- [x] Flag missing values — 445,858 `price`, 1,240,821 `high_price`, 0 on both Dish columns
- [x] Flag zero values — folded into `NON_POSITIVE_PRICE`
- [x] Flag negative values — same code; **zero negatives exist** in any column
- [x] Flag suspicious extreme values — winsorization of the right tail at the 99.5th percentile,
      capping rather than deleting. 4,251 + 459 `MenuItem` and 767 + 882 `Dish` values capped.
      Note the earlier reading of `MenuItem.price` = 180,000 as an outlier was **wrong**: it is an
      Italian Lire menu, where that is an ordinary price. Only 4 of the 1,183 items above 1,000
      are dollar-denominated, so the right tail is a currency artifact rather than transcription
      error, and those menus are already out of U1 scope
- [ ] Create cleaned numeric columns — **prices are cleaned in place**; no `cleaned_lowest_price`
      or `clean_item_price` column exists (deviation 1)
- [x] Check `high_price < price` — 1,274 rows reported, not corrected; handed to Step 7
- [ ] Check `highest_price < lowest_price` — **NOT DONE in the pipeline.** Profiling showed zero
      violations, but the check itself is missing from `clean_dish.py` and should be added so the
      zero is reported on every run
- [x] Apply warning or exclusion rules defined in Step 3 — as far as Step 3 has defined them; the
      zero-price rule is still open
- [x] Confirm parsing does not misinterpret punctuation or formatting — unit-tested against real
      values including `0.2`, `0.0`, `1.0`, `0.25`, comma and `$` forms

Evidence to retain per column: missing · malformed · zero/non-positive · successfully parsed ·
suspicious · excluded · cells changed.

### 4.6 Fallback pricing logic

> **ENTIRE SECTION NOT DONE — deliberately deferred to SQL.** The chain needs `MenuItem` joined to
> `Dish`, which pandas cannot do without duplicating the join SQL will perform anyway. `price` and
> `high_price` are therefore carried into staging with blanks preserved, and the chain is resolved
> after the load. Recorded as a plan deviation in the report.
>
> Two profiling findings should shape the implementation when it happens:
>
> - `MenuItem.high_price` rescues **57 rows** out of 1.33M — step 2 of the chain is very nearly
>   inert.
> - Only **171,731 dishes (43.6%)** have both prices positive, and ~361,000 of the ~446,000
>   unpriced items sit on menus that were never price-transcribed at all, so no dish-level
>   fallback can reach them.

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

> **See deviation 2.** `cleaning_status`, `warning_reason`, and `exclusion_reason` are **not
> written**. A single accumulating `log` column carries `<column>:<operation>` tags, and MenuItem
> carries an `omit` column. `source_file` and `source_row_num` are written as specified.

- [ ] Define valid status values — `config.CleaningStatus` defines `ok` / `cleaned` / `warning` /
      `excluded`, but **nothing writes it**. Either populate it or delete the class and record the
      `log` column as the agreed replacement
- [ ] Distinguish warnings from exclusions — **not as separate columns.** Distinguishable from the
      `log` tags and the `omit` column, but a consumer has to parse rather than filter
- [x] Support multiple reasons or document reason precedence — the `log` column accumulates every
      operation, so there is no precedence to resolve. Tags are `<column>:<operation>` so counting
      per column requires splitting first
- [x] Use controlled reason codes — `config.Reason` and `config.Operation`
- [x] Ensure no excluded row disappears without trace — the 236 omitted rows are written to
      `MenuItem_omitted.csv`, each carrying `omit:no_dish_id_and_no_price`
- [x] Ensure every unusable row has a reason — verified: all 236 carry the tag
- [ ] Produce or contribute to `excluded_records.csv` — **the content exists** as
      `MenuItem_omitted.csv`, but not under the agreed filename and not in `data/reports/`. Rename
      or copy at Step 10

Reason codes (see `src/config.Reason`): `missing_required_id` · `malformed_id` ·
`missing_date` · `invalid_date` · `missing_currency` · `ambiguous_currency` · `missing_price` ·
`non_positive_price` · `malformed_price` · `no_valid_fallback_price`

Quantification: rows with no warnings · rows with warnings · rows excluded · counts by warning
reason · counts by exclusion reason · counts by source table.

### Step 4 outputs

All land in `data/<table>/interim/cleaned/` rather than a shared directory.

- [x] `Menu_cleaned.csv` — 5,236 rows · `id, currency, year, month, day`
- [x] `MenuPage_cleaned.csv` — 66,937 rows · `id, menu_id`
- [x] `MenuItem_cleaned.csv` — 1,332,432 rows · `id, menu_page_id, price, high_price, dish_id`
- [x] `Dish_cleaned.csv` — 394,297 rows · `id, name, lowest_price, highest_price`
- [x] `cleaning_log.csv` — `data/reports/`, 24 rule applications
- [x] Preliminary excluded-record file — `MenuItem_omitted.csv`, 236 rows (rename pending, above)
- [x] Python script/notebook — `src/`, 8 modules
- [ ] **Data dictionary for generated fields — NOT DONE, and now actively wrong.**
      [../data-dictionary.md](../data-dictionary.md) still describes `cleaned_year`,
      `currency_clean`, `status_clean`, `name_clean`, `cleaning_status`, `warning_reason`, and
      `exclusion_reason` — none of which the pipeline produces. **This is the highest-priority
      remaining Step 4 item**: Madalyn's staging schema is built from it
- [x] Change-count summary — report §2.1, generated from `cleaning_log.csv`
- [x] Inner workflow W2 documentation — [../../workflow/](../../workflow/)

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
