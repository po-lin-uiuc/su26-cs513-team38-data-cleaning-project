# Data

**Everything under `data/` is git-ignored** (except this file and `.gitkeep` markers).
Datasets are shared through the team Box folder — the course instructions require datasets to
be linked, not bundled.

| Directory | Stage | Contents |
| --- | --- | --- |
| `raw/` | D | The four original CSVs, **never modified**: `Menu.csv`, `MenuPage.csv`, `MenuItem.csv`, `Dish.csv` |
| `interim/` | staging | pandas output: `Menu_cleaned.csv`, `MenuPage_cleaned.csv`, `MenuItem_cleaned.csv`, `Dish_cleaned.csv`, `cleaning_log.csv` |
| `final/` | D′ | `final_menu.csv`, `final_item.csv` |
| `reports/` | evidence | `validation_ic_results.csv`, `validation_ind_results.csv`, `validation_fd_results.csv`, `excluded_records.csv`, `validation_report.csv`, profiling summaries |

## Setup  [Team]

1. Download the four CSVs from the course Box folder into `data/raw/`.
2. Leave them untouched — the pipeline only reads from `raw/`. Every transformation writes to
   `interim/` or `final/`.
3. Record the Box link in `deliverables/phase2/DataLinks.txt` (a required deliverable).

## Provenance rule

Rows are **flagged, not dropped**. Cleaned files carry `cleaning_status`, `warning_reason`,
`exclusion_reason`, `source_file`, and `source_row_num` so every excluded record stays
traceable to its raw row, and D → D′ stays quantifiable. See
[../docs/phase2-plan.md](../docs/phase2-plan.md) §4.7.
