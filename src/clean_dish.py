"""Dish cleaning — S3 steps 4.1 (identifiers), 4.2 (names), 4.5 (prices).

Dish carries the project's only free-text column, so this is where problems
P1-P3 are addressed: the same dish written many ways, names that are entirely
numbers or symbols, and misspellings. Normalizing to a single character set is
what lets those variants collapse together.

The blank-price dishes were already excluded by the OpenRefine recipe. Zero
prices (problem P5) survive into this output deliberately -- whether a 0.00 is
a real "no charge" or a transcription artifact is a rule decision, and the
fallback join that needs the answer happens in SQL.

Run standalone with:  python -m src.clean_dish

Owner: Po Lin (Step 4)  [PoLin].
"""

from __future__ import annotations

import pandas as pd

from src import config, provenance
from src.cleaning_utils import clean_decimal_2dp, clean_dish_name, clean_int

TABLE_KEY = "dish"
PRICE_COLUMNS = ("lowest_price", "highest_price")


# @begin clean_dish
# @desc  Dish's cleaning chain: identifiers, name normalization, price decimals.
# @desc  Three stages -- fewer than Menu, more than MenuPage.
# @desc  Writes: Dish_cleaned.csv
# @in    dish_or      @uri file:data/dish/interim/open-refine/Dish_OR.csv
# @out   dish_cleaned @uri file:data/dish/interim/cleaned/Dish_cleaned.csv


# @begin clean_dish_identifiers
# @desc  Coerce Dish.id to an integer. Dish.id is the target of
# @desc  MenuItem.dish_id, so a key that will not parse breaks the price
# @desc  fallback join later.
# @desc  Writes: Dish_after_id-numeric.csv, Dish_summary_id-numeric.csv
# @in    dish_or   @uri file:data/dish/interim/open-refine/Dish_OR.csv
# @param NULL_LIKE_VALUES
# @out   dish_ids  @uri file:data/dish/interim/func-id-numeric/Dish_after_id-numeric.csv
# @end clean_dish_identifiers
def clean_identifiers(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert `id` to an integer, flagging any row whose key will not parse."""
    recorder = provenance.StepRecorder(TABLE_KEY, "id-numeric")
    frame = recorder.apply(frame, "id", clean_int, dtype="Int64")

    unparsed = int(frame["id"].isna().sum())
    if unparsed:
        recorder.note("id", config.Reason.MALFORMED_ID, unparsed)
        print(f"  WARNING: {unparsed:,} dishes have an unparseable id")

    return recorder.write(frame).frame


# @begin clean_dish_names
# @desc  Normalize dish names to uppercase ASCII alphanumerics plus apostrophe
# @desc  and comma. Folds accents so accented and unaccented spellings of one
# @desc  dish collapse together (P1, P3); marks non-Latin and symbol-only names
# @desc  UNKNOWN rather than deleting them (P2).
# @desc  Writes: Dish_after_dish-name.csv, Dish_changes_dish-name.csv
# @in    dish_ids   @uri file:data/dish/interim/func-id-numeric/Dish_after_id-numeric.csv
# @param DISH_NAME_ALLOWED
# @param DISH_NAME_SEPARATORS
# @param DISH_NAME_REPLACEMENTS
# @param DISH_NAME_QUOTE_MAP
# @param DISH_NAME_UNKNOWN
# @out   dish_names @uri file:data/dish/interim/func-dish-name/Dish_after_dish-name.csv
# @end clean_dish_names
def clean_names(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize `name`, recording the substantive changes.

    Uppercasing alone does not earn a change row. It applies to 380K of the
    394K names and would bury the accent folds, ampersand expansions, and
    UNKNOWN marks that are the actual evidence for P1-P3. The summary still
    counts every uppercase.
    """
    recorder = provenance.StepRecorder(TABLE_KEY, "dish-name")

    distinct_before = frame["name"].nunique()
    frame = recorder.apply(
        frame,
        "name",
        clean_dish_name,
        trivial_ops=frozenset({config.Operation.UPPERCASED}),
    )
    distinct_after = frame["name"].nunique()

    unknown = int((frame["name"] == config.DISH_NAME_UNKNOWN).sum())

    print(f"  distinct names: {distinct_before:,} -> {distinct_after:,} "
          f"({distinct_before - distinct_after:,} variants collapsed)")
    print(f"  marked {config.DISH_NAME_UNKNOWN}: {unknown:,}")

    return recorder.write(frame).frame


# @begin clean_dish_prices
# @desc  Render dish prices with two decimals so cents stay visible
# @desc  (0.2 -> 0.20). Formatting only, so changes are counted rather than
# @desc  recorded row by row -- the summary carries the same information at a
# @desc  fraction of the size.
# @desc  Writes: Dish_after_price-decimal.csv, Dish_summary_price-decimal.csv
# @in    dish_names   @uri file:data/dish/interim/func-dish-name/Dish_after_dish-name.csv
# @param PRICE_FORMAT
# @param PRICE_DECIMAL_PLACES
# @out   dish_prices  @uri file:data/dish/interim/func-price-decimal/Dish_after_price-decimal.csv
# @end clean_dish_prices
# (outlier capping is a separate stage below, so the effect of formatting and
#  the effect of capping can be told apart by diffing the two snapshots)
def clean_prices(frame: pd.DataFrame) -> pd.DataFrame:
    """Format `lowest_price` and `highest_price` to two decimals.

    Zero and non-positive prices are counted, not removed. Whether a 0.00 dish
    price is real is problem P5, and the decision needs the MenuItem join that
    happens in SQL.
    """
    recorder = provenance.StepRecorder(TABLE_KEY, "price-decimal")
    for column in PRICE_COLUMNS:
        frame = recorder.apply(frame, column, clean_decimal_2dp, record_changes=False)

    for column in PRICE_COLUMNS:
        numeric = pd.to_numeric(frame[column], errors="coerce")
        missing = int(numeric.isna().sum())
        non_positive = int((numeric <= 0).sum())

        if missing:
            recorder.note(column, config.Reason.MISSING_PRICE, missing)
        if non_positive:
            recorder.note(column, config.Reason.NON_POSITIVE_PRICE, non_positive)

        print(f"  {column}: {missing:,} missing, {non_positive:,} zero or negative, "
              f"{int((numeric > 0).sum()):,} positive")

    both_positive = (
        (pd.to_numeric(frame["lowest_price"], errors="coerce") > 0)
        & (pd.to_numeric(frame["highest_price"], errors="coerce") > 0)
    ).sum()
    print(f"  dishes usable as a price fallback (both > 0): {int(both_positive):,}")

    return recorder.write(frame).frame


# @begin clean_dish_price_outliers
# @desc  Cap dish prices above the 99.5th percentile at that percentile
# @desc  (winsorization, right tail only). Rows are never dropped and the left
# @desc  tail is untouched -- a cheap dish is real data, not an error.
# @desc  Writes: Dish_after_price-outlier.csv, Dish_changes_price-outlier.csv
# @in    dish_prices   @uri file:data/dish/interim/func-price-decimal/Dish_after_price-decimal.csv
# @param WINSORIZE_UPPER_LIMIT
# @param WINSORIZE_COLUMNS
# @out   dish_capped   @uri file:data/dish/interim/func-price-outlier/Dish_after_price-outlier.csv
# @end clean_dish_price_outliers
def cap_price_outliers(frame: pd.DataFrame) -> pd.DataFrame:
    """Winsorize the right tail of both dish price columns."""
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


def clean() -> pd.DataFrame:
    """Run Dish's full chain: load, four stages, write load-ready CSV."""
    frame = provenance.load_or_export(TABLE_KEY)
    print(f"Dish: {len(frame):,} rows from {config.TABLES[TABLE_KEY].or_file.name}")

    frame = clean_identifiers(frame)
    frame = clean_names(frame)
    frame = clean_prices(frame)
    frame = cap_price_outliers(frame)

    # @begin write_dish_cleaned
    # @desc  Strip the provenance columns and write the load-ready CSV.
    # @desc  Writes: Dish_cleaned.csv
    # @in    dish_capped  @uri file:data/dish/interim/func-price-outlier/Dish_after_price-outlier.csv
    # @param PROVENANCE_COLUMNS
    # @out   dish_cleaned @uri file:data/dish/interim/cleaned/Dish_cleaned.csv
    # @end write_dish_cleaned
    destination = provenance.write_cleaned(frame, TABLE_KEY)
    print(f"Dish: wrote {destination.relative_to(config.PROJECT_ROOT)}")
    return frame


# @end clean_dish


if __name__ == "__main__":
    clean()
