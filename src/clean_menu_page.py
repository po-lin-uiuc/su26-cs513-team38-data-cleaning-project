"""MenuPage cleaning — S3 step 4.1 (identifiers).

MenuPage is a pure join bridge for U1: it carries only `id` and `menu_id`, both
fully populated in the OpenRefine export. So its chain is a single step, where
Menu's runs four. That asymmetry is the point of modelling W2 per table rather
than as one pipeline.

Dangling `menu_id` values (a MenuPage pointing at a Menu that is not in the
filtered export) are *not* resolved here. That is an inclusion dependency, owned
by Madalyn in Step 7, and it needs a cross-table join this module has no
business doing. The count is reported so the two of us can reconcile.

Run standalone with:  python -m src.clean_menu_page

Owner: Po Lin (Step 4)  [PoLin].
"""

from __future__ import annotations

import pandas as pd

from src import config, provenance
from src.cleaning_utils import clean_int

TABLE_KEY = "menu_page"
ID_COLUMNS = ("id", "menu_id")


# @begin clean_menu_page
# @desc  MenuPage's cleaning chain: identifiers only. One stage, against Menu's
# @desc  four -- MenuPage is a pure join bridge carrying no dates, prices, text,
# @desc  or categoricals.
# @desc  Writes: MenuPage_cleaned.csv
# @in    menu_page_or      @uri file:data/menu-page/interim/open-refine/MenuPage_OR.csv
# @out   menu_page_cleaned @uri file:data/menu-page/interim/cleaned/MenuPage_cleaned.csv


# @begin clean_menu_page_identifiers
# @desc  Coerce MenuPage identifiers to integers. The only cleaning MenuPage
# @desc  needs -- it holds no dates, prices, text, or categoricals.
# @desc  Writes: MenuPage_after_id-numeric.csv, MenuPage_summary_id-numeric.csv
# @in    menu_page_or  @uri file:data/menu-page/interim/open-refine/MenuPage_OR.csv
# @param NULL_LIKE_VALUES
# @out   menu_page_ids @uri file:data/menu-page/interim/func-id-numeric/MenuPage_after_id-numeric.csv
# @end clean_menu_page_identifiers
def clean_identifiers(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert `id` and `menu_id` to integers, logging any row that changed.

    Changes are recorded row-level rather than counted. Identifier volume is
    high but the change *rate* is nil in the current export, and a key being
    rewritten is exactly the event worth having a before/after row for.
    """
    recorder = provenance.StepRecorder(TABLE_KEY, "id-numeric")
    for column in ID_COLUMNS:
        frame = recorder.apply(frame, column, clean_int, dtype="Int64")

    _report_identifier_health(frame, recorder)
    return recorder.write(frame).frame


def _report_identifier_health(
    frame: pd.DataFrame, recorder: provenance.StepRecorder
) -> None:
    """Count identifiers that failed to parse, without dropping any row.

    A null key here would be a real problem, but this raises nothing: rows are
    flagged, never dropped (rule 2, src/README.md), and the SQL layer reports it
    as a countable integrity violation in Step 7. Crashing would hide the row.
    """
    for column in ID_COLUMNS:
        unparsed = int(frame[column].isna().sum())
        if unparsed:
            recorder.note(column, config.Reason.MALFORMED_ID, unparsed)
            print(f"  WARNING: {unparsed:,} rows have an unparseable {column}")


def clean() -> pd.DataFrame:
    """Run MenuPage's full chain: load, clean identifiers, write load-ready CSV."""
    frame = provenance.load_or_export(TABLE_KEY)
    print(f"MenuPage: {len(frame):,} rows from {config.TABLES[TABLE_KEY].or_file.name}")

    frame = clean_identifiers(frame)

    # @begin write_menu_page_cleaned
    # @desc  Strip the provenance columns and write the load-ready CSV.
    # @desc  Writes: MenuPage_cleaned.csv
    # @in    menu_page_ids     @uri file:data/menu-page/interim/func-id-numeric/MenuPage_after_id-numeric.csv
    # @param PROVENANCE_COLUMNS
    # @out   menu_page_cleaned @uri file:data/menu-page/interim/cleaned/MenuPage_cleaned.csv
    # @end write_menu_page_cleaned
    destination = provenance.write_cleaned(frame, TABLE_KEY)
    print(f"MenuPage: wrote {destination.relative_to(config.PROJECT_ROOT)}")

    distinct_menus = frame["menu_id"].nunique()
    print(f"MenuPage: {distinct_menus:,} distinct menu_id values "
          f"(inclusion against Menu.id is Step 7, not here)")
    return frame


# @end clean_menu_page


if __name__ == "__main__":
    clean()
