# Python cleaning pipeline

Implements S3 of [../docs/phase2-plan.md](../docs/phase2-plan.md). pandas does the
repeatable, type-based cleaning; SQL does validation. This code's job is to get the raw CSVs
into the right shape and types — **not** to build the final joined analysis model.

Owner: **Po Lin** (Step 4)  [PoLin]. Checklist: [../docs/checklists/po-lin.md](../docs/checklists/po-lin.md)

## Modules

| File | Role | Status |
| --- | --- | --- |
| `config.py` | Paths, controlled vocabularies, cleaning rules as constants | done |
| `cleaning_utils.py` | Pure value-level cleaners; each returns a value plus the operations applied | done |
| `provenance.py` | Log accumulation, change capture, stage snapshots, `cleaning_log.csv` rollup | done |
| `clean_menu.py` | 4.1 identifiers, 4.3 date split, 4.4 currency, status drop — 4 stages | done |
| `clean_menu_page.py` | 4.1 identifiers — 1 stage | done |
| `clean_dish.py` | 4.1 identifiers, 4.2 `name` normalization, 4.5 prices + outlier capping — 4 stages | done |
| `clean_menu_item.py` | 4.1 identifiers, 4.5 prices + outlier capping, 4.7 omit check — 4 stages | done |
| `run_pipeline.py` | Entry point; runs the four chains then rolls up the log | done |

Not part of the pipeline:

| File | Role |
| --- | --- |
| `lint_workflow.py` | Development aid — checks the YesWorkflow annotations for faults YesWorkflow itself reports no error for. Only needed when editing annotations; reproducing the data set does not run it |

Still to be written:

| File | Handles | Owner |
| --- | --- | --- |
| `profile_raw.py` | S2 — per-column counts backing the before/after table | Charlene `[CharleneKhun]` |

Step 4.6 fallback pricing (`clean_price_candidate`, `price_source`) is **not** implemented here.
It needs MenuItem joined to Dish, so it belongs in SQL — see
[../sql/](../sql/) and the rationale in [../docs/phase2-report.md](../docs/phase2-report.md) §1.2.

## Running it

```powershell
python -m src.run_pipeline              # all four tables, then the log rollup
python -m src.run_pipeline menu dish    # a subset
python -m src.clean_dish                # one table, standalone
```

Output layout per table:

```
data/<table>/interim/func-<step>/    one directory per cleaning function:
                                       <Table>_after_<step>.csv    full snapshot
                                       <Table>_changes_<step>.csv  cell-level before/after
                                       <Table>_summary_<step>.csv  counts per column/operation
data/<table>/interim/cleaned/        <Table>_cleaned.csv — load-ready, provenance stripped
data/reports/cleaning_log.csv        every stage summary concatenated
```

Adding a cleaning stage is one change: write the function, construct a
`provenance.StepRecorder(table_key, "step-name")`, and call `recorder.write(frame)`. The run
directory is created on first write — nothing to register in `config.py` and no placeholder to
commit.

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
