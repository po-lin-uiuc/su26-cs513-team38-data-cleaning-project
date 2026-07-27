# Data Quality Problems (P)

> Phase-I rubric item 3 (30 pts): list problems with evidence (20) + explain why cleaning is
> necessary for U1 (10).

Each problem carries a stable ID (`P1`…`P10`). Use these IDs in cleaning rules
([../src/](../src/)), validation queries ([../sql/](../sql/)), and the Phase-II before/after
summary so every rule traces back to a documented problem.

## Problem register

| ID | Table.column | Problem | Evidence | U1 impact |
| --- | --- | --- | --- | --- |
| P1 | `Dish.name` | Same dish written many ways (punctuation, capitalization, word order) | Fig. 3.1–3.3 — *Broiled Chicken* variants; *roast beef* in 5 forms (`Beef, Roast`, `Roast beef,`, `Roast beef.`) | Identical dishes split into separate categories, degrading grouping |
| P2 | `Dish.name` | Names that are entirely numbers or isolated symbols | Fig. 3.4 (metaphone clustering) | Transcription artifacts, not menu items — no analytic value |
| P3 | `Dish.name` | Misspellings of the same item | Fig. 3.5–3.6 (cologne phonetic) — `Cafee`/`Cofee`/`Kafee`; `The`/`Thee` for tea | Duplicate categories reduce aggregation quality |
| P4 | `Dish.lowest_price`, `Dish.highest_price` | Missing prices (blank cells) | Fig. 3.7 | Incomplete pricing blocks menu averages, shrinks usable observations |
| P5 | `Dish` / `MenuItem` prices | Zero-valued prices | Fig. 3.8 — e.g. Caviar at `0.0` | Artificially lowers menu averages, distorts price-tier classification |
| P6 | `Menu.date` | Impossible / typo'd dates | Fig. 3.9 — `1091`, `0190` | Menus cannot be assigned to the correct historical period |
| P7 | `Menu.date` | Missing dates | Fig. 3.10 — at least **535** blank | Undated menus cannot be placed in any chronological group |
| P8 | `Menu.currency`, `Menu.currency_symbol` | Empty currency fields, and many distinct currencies where present | Fig. 3.11 (blank), Fig. 3.12 (many currencies) | Identical numeric values represent different purchasing power — not directly comparable |
| P9 | `Dish.first_appeared`, `Dish.last_appeared` | Impossible year values | Fig. 3.13 — ≥5 values of `0`, 62 values of `1`; Fig. 3.14–3.15 — `0` and `2928` (likely `1928`) | Corrupts any time-period grouping derived from dish lifespan |
| P10 | `Menu.place` / location fields | Ambiguous, broad geographic identifiers | Fig. 3.16–3.18 — unidentifiable places, boat names, `New York` (city or state?) | Blocks locality-based analysis; drives U2 being unachievable |

Structural problem carried from the schema (see
[dataset-description.md](dataset-description.md)): `MenuPage.menu_id` contains values absent
from `Menu.id`, and 100+ `MenuItem.dish_id` values are empty — both are inclusion-dependency
violations checked in [../sql/04_validate_ind.sql](../sql/04_validate_ind.sql).

Figures live in [figures/phase1/](figures/phase1/).

## Why cleaning is necessary for U1

U1 classifies menus into price tiers by comparing average menu prices across similar
historical periods. That requires accurate menu **dates**, reliable menu **prices**, and
standardized **dish** information. Uncleaned, the resulting classifications would be
unreliable and potentially misleading:

- **Prices (P4, P5):** missing or invalid prices prevent accurate averages; zero values
  artificially deflate them and distort tier assignment.
- **Dates (P6, P7):** menus with missing or impossible dates cannot be assigned to the
  correct period, making chronological comparison inaccurate.
- **Currency (P8):** multiple currency systems prevent direct comparison — the same number
  can mean entirely different purchasing power.
- **Text (P1, P2, P3):** differing spelling, punctuation, capitalization, and word order
  cause identical dishes to appear as separate records.

Required cleaning operations: trim whitespace; standardize capitalization and punctuation;
merge equivalent dish names using Fingerprint and Cologne Phonetic clustering; filter
records with impossible dates or invalid prices; handle missing values where appropriate;
restrict analysis to records with complete pricing and chronological information; and
standardize or filter currency values.

These steps are both necessary **and sufficient**: once prices, dates, currencies, and dish
names are standardized, no additional external information is needed to perform U1.
