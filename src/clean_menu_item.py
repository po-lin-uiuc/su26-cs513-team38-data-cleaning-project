"""MenuItem cleaning — S3 steps 4.1 (identifiers), 4.5 (prices), 4.7 (exclusion).

MenuItem is the only table this pipeline removes rows from, and it removes very
few: a row is dropped only when it has neither a `dish_id` (so no dish-level
fallback is reachable) nor any positive price of its own. Such a row carries no
price signal by any route, so it cannot contribute to U1 under any later rule.

Missing prices are *not* treated as a reason to drop. 445,974 rows have a
`dish_id` but no price, and resolving those is the fallback join in step 4.6 --
which needs Dish alongside MenuItem and therefore happens in SQL, not here.
Dropping them now would pre-empt a decision this module is not entitled to make.

Run standalone with:  python -m src.clean_menu_item

Owner: Po Lin (Step 4)  [PoLin].
"""

from __future__ import annotations

import pandas as pd

from src import config, provenance
from src.cleaning_utils import clean_decimal_2dp, clean_int

TABLE_KEY = "menu_item"
ID_COLUMNS = ("id", "menu_page_id", "dish_id")
PRICE_COLUMNS = ("price", "high_price")


# @begin clean_menu_item
# @desc  MenuItem's cleaning chain: identifiers, price decimals, omit check.
# @desc  The only table producing an excluded-record file.
# @desc  Writes: MenuItem_cleaned.csv, MenuItem_omitted.csv
# @in    menu_item_or      @uri file:data/menu-item/interim/open-refine/MenuItem_OR.csv
# @out   menu_item_cleaned @uri file:data/menu-item/interim/cleaned/MenuItem_cleaned.csv
# @out   menu_item_omitted @uri file:data/menu-item/interim/func-omit-check/MenuItem_omitted.csv


# @begin clean_menu_item_identifiers
# @desc  Coerce id, menu_page_id, and dish_id to integers. dish_id is
# @desc  legitimately absent on some rows and stays null rather than being
# @desc  invented -- the omit check downstream depends on telling those apart.
# @desc  Writes: MenuItem_after_id-numeric.csv
# @in    menu_item_or  @uri file:data/menu-item/interim/open-refine/MenuItem_OR.csv
# @param NULL_LIKE_VALUES
# @out   menu_item_ids @uri file:data/menu-item/interim/func-id-numeric/MenuItem_after_id-numeric.csv
# @end clean_menu_item_identifiers
def clean_identifiers(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert the three identifier columns to integers.

    A missing `dish_id` is a fact about the data, not an error: it means the
    transcriber could not match the item to the dish dictionary. It is left
    null, never filled (rule 4, src/README.md).
    """
    recorder = provenance.StepRecorder(TABLE_KEY, "id-numeric")
    for column in ID_COLUMNS:
        frame = recorder.apply(frame, column, clean_int, dtype="Int64")

    for column in ("id", "menu_page_id"):
        unparsed = int(frame[column].isna().sum())
        if unparsed:
            recorder.note(column, config.Reason.MALFORMED_ID, unparsed)
            print(f"  WARNING: {unparsed:,} rows have an unparseable {column}")

    absent_dish = int(frame["dish_id"].isna().sum())
    recorder.note("dish_id", config.Reason.MISSING_REQUIRED_ID, absent_dish)
    print(f"  dish_id absent on {absent_dish:,} rows (kept, not invented)")

    return recorder.write(frame).frame


# @begin clean_menu_item_prices
# @desc  Render item prices with two decimals so cents stay visible. Blank
# @desc  prices stay blank: whether a row can be priced at all is settled by the
# @desc  fallback join in SQL, where Dish is available.
# @desc  Writes: MenuItem_after_price-decimal.csv
# @in    menu_item_ids    @uri file:data/menu-item/interim/func-id-numeric/MenuItem_after_id-numeric.csv
# @param PRICE_FORMAT
# @param PRICE_DECIMAL_PLACES
# @out   menu_item_prices @uri file:data/menu-item/interim/func-price-decimal/MenuItem_after_price-decimal.csv
# @end clean_menu_item_prices
def clean_prices(frame: pd.DataFrame) -> pd.DataFrame:
    """Format `price` and `high_price` to two decimals, preserving blanks."""
    recorder = provenance.StepRecorder(TABLE_KEY, "price-decimal")
    for column in PRICE_COLUMNS:
        frame = recorder.apply(frame, column, clean_decimal_2dp, record_changes=False)

    for column in PRICE_COLUMNS:
        numeric = pd.to_numeric(frame[column], errors="coerce")
        missing = int(numeric.isna().sum())
        non_positive = int((numeric <= 0).sum())
        recorder.note(column, config.Reason.MISSING_PRICE, missing)
        if non_positive:
            recorder.note(column, config.Reason.NON_POSITIVE_PRICE, non_positive)
        print(f"  {column}: {missing:,} missing, {non_positive:,} zero or negative, "
              f"{int((numeric > 0).sum()):,} positive")

    contradictory = int(
        (
            pd.to_numeric(frame["high_price"], errors="coerce")
            < pd.to_numeric(frame["price"], errors="coerce")
        ).sum()
    )
    if contradictory:
        print(f"  NOTE: {contradictory:,} rows have high_price < price "
              f"(flagged for Step 7, not corrected here)")

    return recorder.write(frame).frame


# @begin clean_menu_item_price_outliers
# @desc  Cap item prices above the 99.5th percentile at that percentile
# @desc  (winsorization, right tail only). Rows are never dropped and the left
# @desc  tail is untouched -- a $0.05 coffee is real data, not an error.
# @desc  Writes: MenuItem_after_price-outlier.csv, MenuItem_changes_price-outlier.csv
# @in    menu_item_prices @uri file:data/menu-item/interim/func-price-decimal/MenuItem_after_price-decimal.csv
# @param WINSORIZE_UPPER_LIMIT
# @param WINSORIZE_COLUMNS
# @out   menu_item_capped @uri file:data/menu-item/interim/func-price-outlier/MenuItem_after_price-outlier.csv
# @end clean_menu_item_price_outliers
def cap_price_outliers(frame: pd.DataFrame) -> pd.DataFrame:
    """Winsorize the right tail of both item price columns.

    Almost everything this caps is a foreign-currency price -- 180,000 on an
    Italian Lire menu is an ordinary amount -- from a menu the currency filter
    already excludes from U1. Only 0.7% of the capped values sit on a
    dollar-denominated menu.
    """
    recorder = provenance.StepRecorder(TABLE_KEY, "price-outlier")
    for column in config.WINSORIZE_COLUMNS[TABLE_KEY]:
        frame, threshold = recorder.winsorize(frame, column, config.WINSORIZE_UPPER_LIMIT)
        if threshold is None:
            continue
        capped = int(
            frame[config.LOG_COLUMN]
            .str.contains(config.log_tag(column, config.Operation.WINSORIZED), regex=False)
            .sum()
        )
        print(f"  {column}: {capped:,} values capped at {threshold:,.2f} "
              f"({config.WINSORIZE_UPPER_LIMIT:.2%} upper limit)")
    return recorder.write(frame).frame


# @begin clean_menu_item_omit
# @desc  Flag and remove rows carrying no price signal by any route: no dish_id
# @desc  and no positive price. Writes the flagged set before removal and the
# @desc  removed rows separately, so every exclusion is traceable.
# @desc  Writes: MenuItem_before_omit-check.csv, MenuItem_after_omit-check.csv,
# @desc  MenuItem_omitted.csv
# @in    menu_item_capped  @uri file:data/menu-item/interim/func-price-outlier/MenuItem_after_price-outlier.csv
# @param NO_DISH_ID_AND_NO_PRICE
# @out   menu_item_kept    @uri file:data/menu-item/interim/func-omit-check/MenuItem_after_omit-check.csv
# @out   menu_item_omitted @uri file:data/menu-item/interim/func-omit-check/MenuItem_omitted.csv
# @end clean_menu_item_omit
def apply_omit_check(frame: pd.DataFrame) -> pd.DataFrame:
    """Mark unusable rows, write the before/after pair, and return the keepers.

    "Unusable" is deliberately narrow: no `dish_id` **and** no positive price.
    Either one alone leaves a route to a price, so only their conjunction makes
    a row hopeless.
    """
    recorder = provenance.StepRecorder(TABLE_KEY, "omit-check")

    no_dish = frame["dish_id"].isna()
    price = pd.to_numeric(frame["price"], errors="coerce")
    high_price = pd.to_numeric(frame["high_price"], errors="coerce")
    no_price = ~(price > 0) & ~(high_price > 0)
    omit = no_dish & no_price

    frame = frame.copy()
    frame[config.OMIT_COLUMN] = omit.astype(int)
    frame = recorder.tag_rows(
        frame, omit, config.OMIT_COLUMN, config.Reason.NO_DISH_ID_AND_NO_PRICE
    )

    print(f"  no dish_id            : {int(no_dish.sum()):,}")
    print(f"  no positive price     : {int(no_price.sum()):,}")
    print(f"  omitted (both)        : {int(omit.sum()):,}")
    print(f"  no dish_id but priced : {int((no_dish & ~no_price).sum()):,} (kept)")
    print(f"  priceless but has dish: {int((~no_dish & no_price).sum()):,} (kept for SQL fallback)")

    before = recorder.write(frame, suffix="before")
    kept = frame.loc[~omit].drop(columns=[config.OMIT_COLUMN])
    recorder.write(kept, suffix="after")

    omitted_path = provenance.write_table(
        frame.loc[omit], before.directory / f"{config.TABLES[TABLE_KEY].name}_omitted.csv"
    )
    print(f"  wrote {omitted_path.relative_to(config.PROJECT_ROOT)} "
          f"({int(omit.sum()):,} rows)")

    return kept


def clean() -> pd.DataFrame:
    """Run MenuItem's full chain: load, three stages, write load-ready CSV."""
    frame = provenance.load_or_export(TABLE_KEY)
    starting = len(frame)
    print(f"MenuItem: {starting:,} rows from {config.TABLES[TABLE_KEY].or_file.name}")

    frame = clean_identifiers(frame)
    frame = clean_prices(frame)
    frame = cap_price_outliers(frame)
    frame = apply_omit_check(frame)

    # @begin write_menu_item_cleaned
    # @desc  Strip the provenance columns and write the load-ready CSV.
    # @desc  Writes: MenuItem_cleaned.csv
    # @in    menu_item_kept    @uri file:data/menu-item/interim/func-omit-check/MenuItem_after_omit-check.csv
    # @param PROVENANCE_COLUMNS
    # @out   menu_item_cleaned @uri file:data/menu-item/interim/cleaned/MenuItem_cleaned.csv
    # @end write_menu_item_cleaned
    destination = provenance.write_cleaned(frame, TABLE_KEY)
    print(f"MenuItem: wrote {destination.relative_to(config.PROJECT_ROOT)}")
    print(f"MenuItem: {starting:,} in, {len(frame):,} out, "
          f"{starting - len(frame):,} omitted and preserved separately")
    return frame


# @end clean_menu_item


if __name__ == "__main__":
    clean()
