"""Pipeline entry point — runs the cleaning stages in order.

    python -m src.run_pipeline

Skeleton only. Add each stage as it is built (docs/phase2-plan.md, S3 steps 1-10).
Every stage reads from the previous stage's output directory and must never write
back into data/raw/.

Owner: Po Lin (Step 4)  [PoLin]. Checklist: docs/checklists/po-lin.md
"""

from __future__ import annotations

import sys

from src import config


def main() -> int:
    config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    config.FINAL_DIR.mkdir(parents=True, exist_ok=True)

    # === S2: profiling ===  [CharleneKhun]
    #   profile_raw.profile_all()   -> data/reports/

    # === S3 step 4: cleaning ===  [PoLin]
    # One cleaner per table, each writing to data/interim/ plus rows in the
    # cleaning log. Flag rows, never drop them.
    #   clean_menu.clean()       -> Menu_cleaned.csv       dates P6/P7, currency P8
    #   clean_menu_page.clean()  -> MenuPage_cleaned.csv   key integrity
    #   clean_dish.clean()       -> Dish_cleaned.csv       names P1-P3, prices P4/P5
    #   clean_menu_item.clean()  -> MenuItem_cleaned.csv   price fallback, step 4.6

    # === S3 step 6: load staging ===  [MadalynKillian]
    #   see sql/02_load_staging.sql

    print("No stages implemented yet — see docs/phase2-plan.md and docs/checklists/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
