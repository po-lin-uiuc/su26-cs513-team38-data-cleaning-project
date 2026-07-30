"""Pipeline entry point — the inner cleaning workflow W2.

    python -m src.run_pipeline              # every table
    python -m src.run_pipeline menu dish    # just these

Each table is cleaned independently: they share no state, and nothing joins
across them here. The joins that U1 needs happen in SQL, after Madalyn loads
these outputs into staging. That independence is why the four chains have
different lengths -- MenuPage needs one stage, Menu needs four -- and why the
W2 graph is four parallel tracks rather than one line.

Reruns are safe and produce byte-identical output: every stage overwrites its
own directory and nothing here appends.

Rendering the workflow graph (needs Java, the YesWorkflow jar, and Graphviz):

    java -jar yesworkflow.jar graph src/run_pipeline.py src/clean_*.py > workflow/W2.gv
    dot -Tpdf workflow/W2.gv -o workflow/W2.pdf

Owner: Po Lin (Step 4)  [PoLin]. Checklist: docs/checklists/po-lin.md
"""

from __future__ import annotations

import sys
from typing import Callable

import pandas as pd

from src import (
    clean_dish,
    clean_menu,
    clean_menu_item,
    clean_menu_page,
    config,
    provenance,
)

# Ascending size, so a failure surfaces on the 5K-row table rather than after
# the 1.3M-row one has finished.
STAGES: dict[str, Callable[[], pd.DataFrame]] = {
    "menu": clean_menu.clean,
    "menu_page": clean_menu_page.clean,
    "dish": clean_dish.clean,
    "menu_item": clean_menu_item.clean,
}


# The outer workflow block for W2 is opened in workflow/W2_frame.yw, which must
# precede the cleaning modules in YesWorkflow's argument list. This file is
# passed LAST and closes that block, which matches what it actually does: the
# rollup below is the final step. See workflow/W2_frame.yw for the full command.
#
# Do not write the YesWorkflow begin or end keywords in prose anywhere in this
# repository. YesWorkflow scans for them loosely, so a keyword mentioned inside
# an ordinary sentence is parsed as a real annotation and silently opens a
# duplicate block.


# @begin collect_cleaning_log
# @desc  Concatenate every stage summary into one machine-readable log. This is
# @desc  the source for the change table in the Phase-II report, section 2.1.
# @desc  Writes: cleaning_log.csv
# @in    menu_cleaned
# @in    menu_page_cleaned
# @in    dish_cleaned
# @in    menu_item_cleaned
# @out   cleaning_log @uri file:data/reports/cleaning_log.csv
# @end collect_cleaning_log
def summarize() -> None:
    """Roll the per-stage summaries up and report what changed, per column."""
    destination = provenance.collect_cleaning_log()
    log = pd.read_csv(destination)

    if log.empty:
        print("\nNo rule applications recorded.")
        return

    print(f"\nCleaning log -> {destination.relative_to(config.PROJECT_ROOT)}")
    print(f"{len(log)} rule applications across "
          f"{log['table'].nunique()} tables and {log['step'].nunique()} stages\n")

    for table in log["table"].unique():
        rows = log[log["table"] == table]
        total = int(rows["rows_affected"].sum())
        print(f"  {table:<10} {total:>10,} cell-level changes across {len(rows)} rules")


def run(table_keys: list[str]) -> int:
    """Clean the named tables, then roll up the cleaning log."""
    unknown = [key for key in table_keys if key not in STAGES]
    if unknown:
        print(f"Unknown table(s): {unknown}. Choose from {list(STAGES)}.")
        return 2

    counts: dict[str, int] = {}
    for key in table_keys:
        print()
        try:
            counts[key] = len(STAGES[key]())
        except FileNotFoundError as error:
            print(f"\nMissing input: {error.filename}")
            print("The raw and OpenRefine files are distributed separately -- unzip the "
                  "shared data archive into the project root and rerun.")
            return 1
        except provenance.OpenRefineShapeError as error:
            print(f"\n{error}")
            return 1

    print("\n" + "=" * 62)
    print("Rows written")
    print("=" * 62)
    for key, count in counts.items():
        print(f"  {key:<10} {count:>10,} -> "
              f"{config.TABLES[key].cleaned_file.relative_to(config.PROJECT_ROOT)}")

    summarize()
    return 0


def main(argv: list[str] | None = None) -> int:
    requested = argv if argv else list(STAGES)
    return run(requested)


# @end cleaning_workflow_W2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
