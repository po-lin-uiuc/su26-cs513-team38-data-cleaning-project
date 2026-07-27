# Python cleaning pipeline

Implements S3 of [../docs/phase2-plan.md](../docs/phase2-plan.md). pandas does the
repeatable, type-based cleaning; SQL does validation. This code's job is to get the raw CSVs
into the right shape and types — **not** to build the final joined analysis model.

Owner: **Po Lin** (Step 4)  [PoLin]. Checklist: [../docs/checklists/po-lin.md](../docs/checklists/po-lin.md)

## Modules

| File | Role | Status |
| --- | --- | --- |
| `config.py` | Paths, U1 column scope, flag/reason vocabularies | scaffolding |
| `run_pipeline.py` | Entry point; runs stages in order | skeleton |

To be written — one cleaner per table (S3 step 4), plus profiling:

| File | Handles | Owner |
| --- | --- | --- |
| `profile_raw.py` | S2 — per-column counts backing the before/after table | Charlene `[CharleneKhun]` |
| `clean_menu.py` | 4.3 dates (`cleaned_year`), 4.4 currency (`currency_clean`), status enum | Po `[PoLin]` |
| `clean_menu_page.py` | 4.1 identifiers, dangling `menu_id` flags | Po `[PoLin]` |
| `clean_dish.py` | 4.2 `name` normalization, 4.5 price fields | Po `[PoLin]` |
| `clean_menu_item.py` | 4.5 prices, 4.6 fallback pricing (`clean_price_candidate`, `price_source`) | Po `[PoLin]` |

## Rules

1. **Never write to `data/raw/`.** Cleaners read raw, write to `data/interim/`.
2. **Flag, don't drop.** Every row keeps `cleaning_status`, `warning_reason`,
   `exclusion_reason`, `source_file`, `source_row_num`. Dropping a row destroys the evidence
   S5 needs to quantify ΔD.
3. **Preserve originals.** When a column is cleaned, keep the raw value in a parallel column
   (e.g. `original_price` alongside `clean_item_price`) so a reviewer can see what changed.
4. **Never invent IDs.** A missing required ID is flagged `missing_required_id`, not filled.
5. **Read as strings.** Load raw CSVs with `dtype=str`; type conversion is an explicit, logged
   cleaning step. Letting pandas infer types hides the difference between a blank price (P4)
   and a `0.0` price (P5).
6. **New reason strings go in `config.Reason`** and must map to a problem ID in
   [../docs/data-quality-problems.md](../docs/data-quality-problems.md) and a rule in
   [../docs/cleaning-rules.md](../docs/cleaning-rules.md).
7. **Deterministic output.** Same raw input, same cleaned output — the checklist requires the
   workflow be rerunnable from the raw files.
