# Data dictionary — generated fields  [PoLin] [CharleneKhun] [MadalynKillian]

Every column the pipeline *creates*. Raw columns are documented in
[dataset-description.md](dataset-description.md); this file covers what did not exist in D.

Required deliverable for Step 4 (Po) and Step 3 (Charlene), and the staging portion for
Step 5 (Madalyn). Keep it in sync with `src/config.py` and `sql/01_schema_staging.sql` — a
data dictionary that disagrees with the code is worse than none.

The column names below are the ones named in the Phase-I plan. **Types, nullability, and the
rule that produces each value are yours to decide** in Step 3 and record here.

## Provenance columns (all cleaned files)  [PoLin] [CharleneKhun]

| Column | Type | Permitted values | Meaning |
| --- | --- | --- | --- |
| `cleaning_status` | | | |
| `warning_reason` | | | |
| `exclusion_reason` | | | |
| `source_file` | | | |
| `source_row_num` | | | |

Reason codes, from the Phase-I plan (`src/config.Reason`): `missing_required_id` ·
`malformed_id` · `missing_date` · `invalid_date` · `missing_currency` · `ambiguous_currency` ·
`missing_price` · `non_positive_price` · `malformed_price` · `no_valid_fallback_price`

Still to define (Step 3):

- [ ] Permitted values of `cleaning_status`
- [ ] Whether multiple reasons may appear on one row, or whether a precedence order applies.
      If they are concatenated, every consumer that counts by reason has to split first or the
      counts will be wrong.
- [ ] Whether `exclusion_reason` is mandatory whenever a row is excluded

## Menu_cleaned.csv  [PoLin]

| Column | Type | Derived from | Rule |
| --- | --- | --- | --- |
| `cleaned_year` | | `Menu.date` | |
| `currency_clean` | | `currency`, `currency_symbol` | |
| `status_clean` | | `Menu.status` | |

Raw `date`, `currency`, `currency_symbol`, and `status` are preserved unchanged alongside.

## Dish_cleaned.csv  [PoLin]

| Column | Type | Derived from | Rule |
| --- | --- | --- | --- |
| `name_clean` | | `Dish.name` | |
| `cleaned_lowest_price` | | `lowest_price` | |
| `cleaned_highest_price` | | `highest_price` | |

## MenuItem_cleaned.csv  [PoLin]

| Column | Type | Derived from | Rule |
| --- | --- | --- | --- |
| `clean_price_candidate` | | fallback chain (Phase-I plan §4.6) | |
| `price_source` | | fallback chain (Phase-I plan §4.6) | |

`price_source` domain, from the Phase-I plan (`src/config.PriceSource`): `menu_item_price` ·
`menu_item_high_price` · `dish_lowest_highest_average` · `dish_lowest_price` ·
`dish_highest_price` · `no_valid_price`

- [ ] Record what each `price_source` value means, and the relationship between
      `clean_price_candidate` and `no_valid_price`
- [ ] The checklist asks you to record the limitations of using dish-level values as
      item-level fallbacks. Work out what those are and state them here.

## MenuPage_cleaned.csv  [PoLin]

| Column | Type | Derived from | Rule |
| --- | --- | --- | --- |

## cleaning_log.csv  [PoLin]

Machine-readable record of every rule application — the source for the S5 change counts. The
Phase-I plan names this file; its columns are yours to design.

- [ ] Define the schema. It has to support the Phase-II summary table (which columns changed,
      how many cells per column) and tie each entry back to a rule ID in
      [cleaning-rules.md](cleaning-rules.md).

| Column | Type | Meaning |
| --- | --- | --- |

## excluded_records.csv  [PoLin]

- [ ] Define the schema. It has to preserve enough to trace an excluded row back to its raw
      source row and to the rule that excluded it.

| Column | Type | Meaning |
| --- | --- | --- |

## Final tables  [PoLin] [MadalynKillian]

`final_menu` and `final_item` columns are defined in
[../sql/06_schema_final.sql](../sql/06_schema_final.sql). Mirror them here once the DDL is
settled — the checklist requires a final-table data dictionary.
