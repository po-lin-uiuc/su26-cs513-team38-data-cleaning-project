"""Menu cleaning — S3 steps 4.1 (identifiers), 4.3 (dates), 4.2/4.4 (categoricals).

Menu has the longest chain of the four tables: it is the only one carrying a
date, a currency, and a status categorical, so it runs four stages where
MenuPage runs one. That difference is what the W2 graph is meant to show.

Stage order matters only in that identifiers come first -- a row whose key
cannot be read is worth knowing about before anything else is derived from it.

Run standalone with:  python -m src.clean_menu

Owner: Po Lin (Step 4)  [PoLin].
"""

from __future__ import annotations

import pandas as pd

from src import config, provenance
from src.cleaning_utils import clean_int, map_currency, split_iso_date

TABLE_KEY = "menu"


# @begin clean_menu
# @desc  Menu's full cleaning chain: identifiers, date split, currency mapping,
# @desc  status drop. Four stages -- the longest of the four tables.
# @desc  Writes: Menu_cleaned.csv
# @in    menu_or      @uri file:data/menu/interim/open-refine/Menu_OR.csv
# @out   menu_cleaned @uri file:data/menu/interim/cleaned/Menu_cleaned.csv


# @begin clean_menu_identifiers
# @desc  Coerce Menu.id to an integer.
# @desc  Writes: Menu_after_id-numeric.csv, Menu_summary_id-numeric.csv
# @in    menu_or   @uri file:data/menu/interim/open-refine/Menu_OR.csv
# @param NULL_LIKE_VALUES
# @out   menu_ids  @uri file:data/menu/interim/func-id-numeric/Menu_after_id-numeric.csv
# @end clean_menu_identifiers
def clean_identifiers(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert `id` to an integer, flagging any row whose key will not parse."""
    recorder = provenance.StepRecorder(TABLE_KEY, "id-numeric")
    frame = recorder.apply(frame, "id", clean_int, dtype="Int64")

    unparsed = int(frame["id"].isna().sum())
    if unparsed:
        recorder.note("id", config.Reason.MALFORMED_ID, unparsed)
        print(f"  WARNING: {unparsed:,} menus have an unparseable id")

    return recorder.write(frame).frame


# @begin clean_menu_dates
# @desc  Split the ISO date into year, month, and day for period grouping in U1,
# @desc  then drop the original string. The year/month/day triple carries
# @desc  everything U1 needs; the ISO string is still visible in the previous
# @desc  stage's snapshot, so the derivation stays inspectable.
# @desc  Writes: Menu_after_date-split.csv, Menu_summary_date-split.csv
# @in    menu_ids   @uri file:data/menu/interim/func-id-numeric/Menu_after_id-numeric.csv
# @param MIN_PLAUSIBLE_YEAR
# @param MAX_PLAUSIBLE_YEAR
# @param DATE_PART_COLUMNS
# @out   menu_dates @uri file:data/menu/interim/func-date-split/Menu_after_date-split.csv
# @end clean_menu_dates
def clean_dates(frame: pd.DataFrame) -> pd.DataFrame:
    """Derive `year`, `month`, and `day` from `date`, then drop `date`.

    A menu with no usable year cannot be placed in a time period and so cannot
    take part in U1. It is flagged here and kept; the decision to exclude it
    belongs to the query, not to this module.

    The ISO string is dropped rather than preserved alongside: `year`, `month`,
    and `day` are a lossless decomposition of the part U1 uses, and
    `Menu_after_id-numeric.csv` still holds the original for anyone checking the
    derivation.
    """
    recorder = provenance.StepRecorder(TABLE_KEY, "date-split")
    frame = recorder.expand(frame, "date", split_iso_date, config.DATE_PART_COLUMNS)

    unusable = int(frame["year"].isna().sum())
    if unusable:
        recorder.note("date", config.Reason.INVALID_DATE, unusable)
        print(f"  WARNING: {unusable:,} menus have no usable year "
              f"(outside {config.MIN_PLAUSIBLE_YEAR}-{config.MAX_PLAUSIBLE_YEAR}, "
              f"or unparseable)")

    years = frame["year"].dropna()
    if not years.empty:
        print(f"  year range: {int(years.min())}-{int(years.max())}")

    frame = recorder.drop_column(frame, "date")
    return recorder.write(frame).frame


# @begin clean_menu_currency
# @desc  Map currency labels to ISO abbreviations (Dollars -> USD). No exchange
# @desc  conversion is performed: rates are external data, which would undercut
# @desc  the claim that cleaning alone is sufficient for U1.
# @desc  Writes: Menu_after_currency-map.csv, Menu_changes_currency-map.csv
# @in    menu_dates    @uri file:data/menu/interim/func-date-split/Menu_after_date-split.csv
# @param CURRENCY_MAP
# @out   menu_currency @uri file:data/menu/interim/func-currency-map/Menu_after_currency-map.csv
# @end clean_menu_currency
def clean_currency(frame: pd.DataFrame) -> pd.DataFrame:
    """Map currency labels through `config.CURRENCY_MAP`.

    Unmapped labels pass through unchanged and are counted. Widening U1 beyond
    dollars is a scope decision for docs/cleaning-rules.md, so this module
    surfaces the count rather than quietly discarding the rows.
    """
    recorder = provenance.StepRecorder(TABLE_KEY, "currency-map")
    frame = recorder.apply(frame, "currency", map_currency)

    known = set(config.CURRENCY_MAP.values())
    unmapped = frame.loc[frame["currency"].notna() & ~frame["currency"].isin(known), "currency"]
    if not unmapped.empty:
        recorder.note("currency", config.Reason.AMBIGUOUS_CURRENCY, len(unmapped))
        print(f"  WARNING: {len(unmapped):,} menus carry a currency outside CURRENCY_MAP: "
              f"{sorted(unmapped.unique())}")

    return recorder.write(frame).frame


# @begin clean_menu_status
# @desc  Drop `status`. The OpenRefine export is already filtered to complete
# @desc  menus, so the column is constant and carries no information downstream.
# @desc  Writes: Menu_after_drop-status.csv, Menu_summary_drop-status.csv
# @in    menu_currency @uri file:data/menu/interim/func-currency-map/Menu_after_currency-map.csv
# @out   menu_status   @uri file:data/menu/interim/func-drop-status/Menu_after_drop-status.csv
# @end clean_menu_status
def drop_status(frame: pd.DataFrame) -> pd.DataFrame:
    """Remove the `status` column, refusing to do so if it is not constant.

    Dropping a column is only safe because every surviving row says "complete".
    If a re-export widens that, dropping would silently destroy the distinction,
    so the column is kept and the problem reported instead.
    """
    recorder = provenance.StepRecorder(TABLE_KEY, "drop-status")

    distinct = sorted(frame["status"].dropna().unique())
    if len(distinct) > 1:
        print(f"  WARNING: status is not constant ({distinct}) -- keeping the column. "
              f"Re-check the OpenRefine filter before loading to SQL.")
        return recorder.write(frame).frame

    print(f"  status was constant ({distinct[0] if distinct else 'empty'}) -- dropping")
    frame = recorder.drop_column(frame, "status")
    return recorder.write(frame).frame


def clean() -> pd.DataFrame:
    """Run Menu's full chain: load, four stages, write load-ready CSV."""
    frame = provenance.load_or_export(TABLE_KEY)
    print(f"Menu: {len(frame):,} rows from {config.TABLES[TABLE_KEY].or_file.name}")

    frame = clean_identifiers(frame)
    frame = clean_dates(frame)
    frame = clean_currency(frame)
    frame = drop_status(frame)

    # @begin write_menu_cleaned
    # @desc  Strip the provenance columns and write the load-ready CSV.
    # @desc  Writes: Menu_cleaned.csv
    # @in    menu_status  @uri file:data/menu/interim/func-drop-status/Menu_after_drop-status.csv
    # @param PROVENANCE_COLUMNS
    # @out   menu_cleaned @uri file:data/menu/interim/cleaned/Menu_cleaned.csv
    # @end write_menu_cleaned
    destination = provenance.write_cleaned(frame, TABLE_KEY)
    print(f"Menu: wrote {destination.relative_to(config.PROJECT_ROOT)}")
    return frame


# @end clean_menu


if __name__ == "__main__":
    clean()
