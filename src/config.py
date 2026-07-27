"""Shared paths and controlled vocabularies for the Team 38 pipeline.

Scaffolding only. The vocabularies below are transcribed from the Phase-I plan
(docs/phase2-plan.md, S3 step 4.6 and 4.7) so that the cleaning code, the SQL
validation, and docs/data-dictionary.md all refer to the same strings. Extend
them as Step 3 settles the rules -- every new reason code should map to a problem
ID in docs/data-quality-problems.md and a rule in docs/cleaning-rules.md.
"""

from pathlib import Path
from typing import Final

# --- Paths --------------------------------------------------------------
PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent
DATA_DIR: Final = PROJECT_ROOT / "data"
RAW_DIR: Final = DATA_DIR / "raw"
INTERIM_DIR: Final = DATA_DIR / "interim"
FINAL_DIR: Final = DATA_DIR / "final"
REPORTS_DIR: Final = DATA_DIR / "reports"
SQL_DIR: Final = PROJECT_ROOT / "sql"
DB_PATH: Final = DATA_DIR / "cs513_team38.sqlite"

RAW_FILES: Final[dict[str, Path]] = {
    "menu": RAW_DIR / "Menu.csv",
    "menu_page": RAW_DIR / "MenuPage.csv",
    "menu_item": RAW_DIR / "MenuItem.csv",
    "dish": RAW_DIR / "Dish.csv",
}

CLEANED_FILES: Final[dict[str, Path]] = {
    "menu": INTERIM_DIR / "Menu_cleaned.csv",
    "menu_page": INTERIM_DIR / "MenuPage_cleaned.csv",
    "menu_item": INTERIM_DIR / "MenuItem_cleaned.csv",
    "dish": INTERIM_DIR / "Dish_cleaned.csv",
}

CLEANING_LOG: Final = INTERIM_DIR / "cleaning_log.csv"

# --- Column scope for U1 (docs/phase2-plan.md, S1) ----------------------
U1_COLUMNS: Final[dict[str, tuple[str, ...]]] = {
    "menu": ("id", "date", "currency", "currency_symbol", "status"),
    "menu_page": ("id", "menu_id"),
    "menu_item": ("id", "menu_page_id", "price", "high_price", "dish_id"),
    "dish": ("id", "name", "lowest_price", "highest_price"),
}

# --- Provenance columns added to every cleaned CSV (S3 step 4.7) --------
PROVENANCE_COLUMNS: Final = (
    "cleaning_status",
    "warning_reason",
    "exclusion_reason",
    "source_file",
    "source_row_num",
)


class CleaningStatus:
    """Row-level verdict written to `cleaning_status`.

    TODO [CharleneKhun] (Step 3): "Define valid status values" is a cleaning-rule
    decision. Agree the permitted values, record them in docs/data-dictionary.md,
    and mirror them here so the SQL domain check has something to check against.
    """


class Reason:
    """Controlled vocabulary for `warning_reason` / `exclusion_reason`."""

    MISSING_REQUIRED_ID = "missing_required_id"
    MALFORMED_ID = "malformed_id"
    MISSING_DATE = "missing_date"
    INVALID_DATE = "invalid_date"
    MISSING_CURRENCY = "missing_currency"
    AMBIGUOUS_CURRENCY = "ambiguous_currency"
    MISSING_PRICE = "missing_price"
    NON_POSITIVE_PRICE = "non_positive_price"
    MALFORMED_PRICE = "malformed_price"
    NO_VALID_FALLBACK_PRICE = "no_valid_fallback_price"


class PriceSource:
    """Which rule produced `clean_price_candidate` (S3 step 4.6 fallback order)."""

    MENU_ITEM_PRICE = "menu_item_price"
    MENU_ITEM_HIGH_PRICE = "menu_item_high_price"
    DISH_LOWEST_HIGHEST_AVERAGE = "dish_lowest_highest_average"
    DISH_LOWEST_PRICE = "dish_lowest_price"
    DISH_HIGHEST_PRICE = "dish_highest_price"
    NO_VALID_PRICE = "no_valid_price"


# --- Domain thresholds --------------------------------------------------
# TODO [CharleneKhun] (Step 3): the accepted year range and any minimum priced-item
# threshold are cleaning-rule decisions, not defaults. Define them in
# docs/cleaning-rules.md and mirror the agreed values here so the Python rules and
# the SQL checks cannot drift apart.
#
# MIN_PLAUSIBLE_YEAR: Final = ...
# MAX_PLAUSIBLE_YEAR: Final = ...
# MIN_PRICED_ITEMS_PER_MENU: Final = ...
