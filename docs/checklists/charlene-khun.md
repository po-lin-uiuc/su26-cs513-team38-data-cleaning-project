# Charlene Khun — Phase-II checklist  [CharleneKhun]

ckhun2@illinois.edu

> Search the repo for `[CharleneKhun]` to find every file waiting on you.

Owns OpenRefine profiling, cleaning-rule definition, domain/integrity constraints, and her
portion of provenance and final export.

Artifacts live in [../../openrefine/](../../openrefine/), the rule catalog in
[../cleaning-rules.md](../cleaning-rules.md), and IC queries in
[../../sql/03_validate_ic.sql](../../sql/03_validate_ic.sql).

Also complete the [shared responsibilities](README.md#shared-responsibilities) for each step.

---

## Step 1 — Collect raw datasets into a local repository (group activity)  [CharleneKhun] [Team]

- [ ] Confirm access to all four raw CSV files
- [ ] Confirm OpenRefine working directory/project location
- [ ] Confirm repository folders for OpenRefine projects, screenshots, profiling notes,
      operation histories, rule specifications — see [README.md](README.md#where-artifacts-go)
- [x] Confirm raw files will remain unchanged
- [x] Help record raw row and column counts
- [x] Confirm naming convention for profiling outputs
- [ ] Confirm the team can access OpenRefine evidence files

---

## Step 2 — Profile relevant columns in OpenRefine  [CharleneKhun]

### Menu

Profile: `id` · `date` · `currency` · `currency_symbol` · `status`

Check:

- [ ] Missing values
- [ ] Blank strings
- [ ] Unusual values
- [ ] Date formats
- [ ] Impossible or suspicious dates
- [ ] Currency labels
- [ ] Currency symbols
- [ ] Contradictory currency combinations
- [ ] Status-value distribution
- [ ] Non-complete menus

### MenuPage

Profile: `id` · `menu_id`

Check:

- [ ] Missing IDs
- [ ] Malformed IDs
- [ ] Duplicate IDs
- [ ] Suspicious `menu_id` values
- [ ] Potential unmatched references

### MenuItem

Profile: `id` · `menu_page_id` · `dish_id` · `price` · `high_price`

Check:

- [ ] Missing prices
- [ ] Blank prices
- [ ] Malformed numeric values
- [ ] Zero prices
- [ ] Negative prices
- [ ] Suspicious extremes
- [ ] Missing `dish_id`
- [ ] Potential unmatched references

> MenuItem.csv is by far the largest of the four files and OpenRefine may struggle with it in
> full. If you profile a sample or a column subset, say so in the notes — that is also the
> concrete scale argument for OpenRefine being a profiling tool here rather than the cleaning
> tool.

### Dish

Profile: `id` · `name` · `lowest_price` · `highest_price`

Check:

- [ ] Missing names
- [ ] Blank names
- [ ] Numeric-only names
- [ ] Symbol-only names
- [ ] Misspellings
- [ ] Capitalization differences
- [ ] Punctuation differences
- [ ] Word-order differences
- [ ] Missing prices
- [ ] Zero or negative prices
- [ ] Suspicious price ranges

### Clustering

- [ ] Run fingerprint clustering
- [ ] Run relevant phonetic clustering
- [ ] Review examples such as coffee variants
- [ ] Review examples such as tea variants
- [ ] Review examples such as roast beef variants
- [ ] Review examples such as broiled chicken variants
- [ ] Record accepted merge candidates
- [ ] Record rejected merge candidates
- [ ] Capture cases where clustering may over-merge
- [ ] Do not automatically merge all suggested clusters

> Record rejections as carefully as acceptances — "cluster suggestions rejected" is a required
> evidence count, and over-merging semantically different dishes is the main risk in this step.

### Baseline metrics

Record:

- [ ] Missing dates
- [ ] Invalid dates
- [ ] Missing prices by column
- [ ] Malformed prices by column
- [ ] Zero/non-positive prices by column
- [ ] Ambiguous currencies
- [ ] Contradictory currency values
- [ ] Non-complete menus
- [ ] Missing required IDs
- [ ] Potential broken references
- [ ] Suspicious dish names
- [ ] Distinct dish-name count

### Evidence and deliverables

- [ ] Save representative screenshots → `docs/figures/phase2/`
- [ ] Save profiling notes → `openrefine/notes/`
- [ ] Export `OpenRefineHistory.json` → `openrefine/history/`
- [ ] Create a baseline profiling summary table
- [ ] Create a list of discovered DQ problems
- [ ] Explain why each major problem affects U1
- [ ] Document OpenRefine's role as profiling and review rather than the primary scalable
      transformation tool

The Phase-I report already identifies inconsistent names, missing and zero prices, invalid
dates, ambiguous currencies, and broken or uncertain data relationships (P1–P10 in
[../data-quality-problems.md](../data-quality-problems.md)). Step 2 converts those
observations into **measurable baseline categories**.

---

## Step 3 — Define cleaning requirements from profiling  [CharleneKhun]

Build the rule catalog in [../cleaning-rules.md](../cleaning-rules.md). For every rule include:

- [ ] Rule ID
- [ ] Rule name
- [ ] Source table
- [ ] Source column or columns
- [ ] DQ problem addressed
- [ ] Detection condition
- [ ] Cleaning, warning, or exclusion action
- [ ] Output column
- [ ] Warning or exclusion reason
- [ ] Relevance to U1
- [ ] Expected validation query
- [ ] Expected post-cleaning outcome

### Identifier rules

- [ ] Define required IDs
- [ ] Define permitted ID format
- [ ] Define missing-ID behavior
- [ ] Define malformed-ID behavior
- [ ] Define duplicate-ID handling
- [ ] Confirm missing IDs will not be invented
- [ ] Define optional versus required `dish_id`

### String and categorical rules

- [ ] Define whitespace normalization
- [ ] Define blank/null normalization
- [ ] Define accepted `status_clean` values
- [ ] Define dish-name capitalization rules
- [ ] Define dish-name punctuation rules
- [ ] Define clustering acceptance criteria
- [ ] Define numeric-only and symbol-only name handling
- [ ] Define when original strings must be preserved

### Date rules

- [ ] Define acceptable date formats
- [ ] Define acceptable year range
- [ ] Define rules for extracting `cleaned_year`
- [ ] Define missing-date handling
- [ ] Define malformed-date handling
- [ ] Define impossible-year handling
- [ ] Define when a menu is excluded from U1

> Whatever range you settle on, mirror it in `src/config.py` so the Python rules and the SQL
> checks cannot drift apart.

### Currency rules

- [ ] Define accepted currency labels
- [ ] Define accepted symbols
- [ ] Define valid label-symbol combinations
- [ ] Define missing-currency handling
- [ ] Define contradictory-currency handling
- [ ] Define ambiguous-currency handling
- [ ] Define U1's currency scope
- [ ] Explicitly state whether U1 is restricted to U.S. dollars
- [ ] Explicitly state that no currency conversion occurs unless implemented and supported

> Likely the highest-impact decision in the project: the Phase-I inspection found currency
> fields frequently empty, so how missing currency is handled sets the U1 sample size. Quantify
> it first, then decide, and justify the decision in the report.

### Price rules

- [ ] Define valid numeric format
- [ ] Define zero-price handling
- [ ] Define negative-price handling
- [ ] Define malformed-price handling
- [ ] Define suspicious-value review criteria
- [ ] Define `high_price < price` behavior
- [ ] Define `highest_price < lowest_price` behavior
- [ ] Define cleaned price fields
- [ ] Review and approve Po's fallback logic requirements (§4.6 of [po-lin.md](po-lin.md))

### U1 eligibility rules

- [ ] Menu must have acceptable `status_clean`
- [ ] Menu must have valid `cleaned_year`
- [ ] Menu must have acceptable `currency_clean`
- [ ] Item must have a valid positive clean price
- [ ] Define minimum priced-item threshold, if used
- [ ] Define when a row is warned but retained
- [ ] Define when a row is excluded

### Deliverables

- [ ] Cleaning-rule catalog
- [ ] Data-quality requirements table
- [ ] Controlled warning-reason list
- [ ] Controlled exclusion-reason list
- [ ] Data dictionary for cleaned fields → [../data-dictionary.md](../data-dictionary.md)
- [ ] Candidate integrity/domain constraints for Step 7
- [ ] Notes documenting new requirements discovered after Phase I

---

## Step 7 — Integrity and domain constraints  [CharleneKhun]

For every IC/domain rule:

- [ ] Assign a rule ID
- [ ] State the rule in plain English
- [ ] State it as a denial constraint or SQL violation condition
- [ ] Identify affected tables and columns
- [ ] Explain why it matters for U1
- [ ] Write or coordinate the SQL query
- [ ] Run it on staging data
- [ ] Record violation counts
- [ ] Export violating rows
- [ ] Compare before and after counts where possible
- [ ] Explain whether zero violations are required
- [ ] Explain accepted remaining violations
- [ ] Add the query to `queries.txt`

Write them in [../../sql/03_validate_ic.sql](../../sql/03_validate_ic.sql).

### Menu

- [ ] U1-eligible menu has non-null `menu_id`
- [ ] U1-eligible menu has valid `cleaned_year`
- [ ] `cleaned_year` falls within the accepted range
- [ ] U1-eligible menu has accepted `status_clean`
- [ ] U1-eligible menu has accepted `currency_clean`
- [ ] `status_clean` belongs to its controlled domain
- [ ] `currency_clean` belongs to its controlled domain

### MenuItem / final item

- [ ] Required item ID is non-null
- [ ] Cleaned item price is numeric
- [ ] Cleaned item price is positive
- [ ] `price_source` belongs to its controlled domain
- [ ] U1-eligible item does not have `no_valid_price`
- [ ] `cleaning_status` belongs to its controlled domain
- [ ] Excluded rows have non-null `exclusion_reason`
- [ ] Warned rows have a warning reason where required

### Price relationships

- [ ] Valid `high_price` is not less than valid `price`, if adopted as a rule
- [ ] Valid `highest_price` is not less than valid `lowest_price`
- [ ] Fallback averages use two valid component values
- [ ] Non-positive values are not used as valid fallbacks

### Eligibility

- [ ] Only complete menus are eligible for U1
- [ ] Menus without valid date are ineligible
- [ ] Menus without comparable currency are ineligible
- [ ] Items without valid final price are ineligible
- [ ] Menus meet the minimum valid-item threshold, if adopted

Deliverables: IC/domain SQL queries · rule descriptions · before/after violation counts ·
`validation_ic_results.csv` · IC/domain section for `queries.txt` · explanation of remaining
acceptable violations · handoff of violating rows to Madalyn for Step 8.

> The rubric explicitly expects IC-violation reports showing the difference between violation
> counts **before and after** cleaning, so plan how you will produce the "before" number.

---

## Step 10 — Final export and provenance (Charlene's portion)  [CharleneKhun] [Team]

- [ ] Finalize `OpenRefineHistory.json`
- [ ] Finalize profiling screenshots and evidence
- [ ] Finalize the cleaning-rule catalog
- [ ] Finalize IC/domain query files
- [ ] Finalize IC/domain violation outputs
- [ ] Provide baseline profiling counts
- [ ] Provide before/after IC counts
- [ ] Provide narrative for Steps 2 and 3
- [ ] Provide narrative for the IC/domain portion of Step 7
- [ ] Explain OpenRefine tool selection
- [ ] Add OpenRefine profiling to W1
- [ ] Verify OpenRefine-related filenames used in the report
- [ ] Provide personal contribution summary
- [ ] Confirm her artifacts are included in the supplementary ZIP
