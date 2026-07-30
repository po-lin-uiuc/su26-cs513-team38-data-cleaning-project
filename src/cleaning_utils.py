"""Value-level cleaning functions.

Each function takes one raw cell and returns a :class:`CleanResult` -- the
cleaned value plus the operations that were applied to produce it. Keeping the
operations next to the value is what lets the per-row ``log`` column be built
without a second pass to guess at what changed.

Two rules hold throughout:

1. **An operation is recorded only when it altered the value.** ``"12"`` parsed
   to the integer 12 reports nothing, because the text form is unchanged;
   ``" 12 "`` reports a trim. Recording no-ops would put an identical tag on
   1.3M rows and drown the signal the log exists to carry.
2. **Nothing here reads or writes a file, and nothing knows about pandas.**
   These are pure functions over single values, so they can be unit-tested
   directly -- see the fallback-path testing required by
   docs/checklists/po-lin.md step 4.6.

Owner: Po Lin (Step 4)  [PoLin].
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Final, NamedTuple

from src import config
from src.config import Operation


class CleanResult(NamedTuple):
    """A cleaned value and the operations that produced it."""

    value: Any
    ops: tuple[str, ...] = ()


class DateParts(NamedTuple):
    """Year, month, and day pulled out of a date, plus the operations applied."""

    year: int | None
    month: int | None
    day: int | None
    ops: tuple[str, ...] = ()


# Translation tables are precomputed once: str.translate is a C-level operation,
# where a per-character Python loop over 394K dish names is not.
_QUOTE_TABLE: Final = str.maketrans(config.DISH_NAME_QUOTE_MAP)
_SEPARATOR_TABLE: Final = str.maketrans({ch: " " for ch in config.DISH_NAME_SEPARATORS})
_REPLACEMENT_TABLE: Final = str.maketrans(config.DISH_NAME_REPLACEMENTS)
_DISALLOWED_RE: Final = re.compile(
    "[^" + re.escape("".join(sorted(config.DISH_NAME_ALLOWED))) + "]"
)
_WHITESPACE_RE: Final = re.compile(r"\s+")
_ISO_DATE_RE: Final = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


def _is_null_like(text: str) -> bool:
    return text in config.NULL_LIKE_VALUES


def normalize_text(value: Any) -> CleanResult:
    """Trim, collapse internal whitespace, and map null-like tokens to None.

    The base every other cleaner builds on.
    """
    if value is None:
        return CleanResult(None)

    text = str(value)
    ops: list[str] = []

    # Non-breaking spaces read as whitespace but are not matched by \s in some
    # engines and survive .strip(); fold them before measuring anything.
    folded = text.replace(" ", " ")

    stripped = folded.strip()
    if stripped != folded:
        ops.append(Operation.TRIMMED)

    collapsed = _WHITESPACE_RE.sub(" ", stripped)
    if collapsed != stripped:
        ops.append(Operation.SPACES_COLLAPSED)

    if _is_null_like(collapsed):
        return CleanResult(None, tuple(ops))

    return CleanResult(collapsed, tuple(ops))


def clean_int(value: Any) -> CleanResult:
    """Parse an identifier or count to int, preserving None.

    Never invents a value: anything unparseable becomes None so the caller can
    flag it, per rule 4 in src/README.md.
    """
    text, ops = normalize_text(value)
    if text is None:
        return CleanResult(None, ops)

    candidate = text.replace(",", "")
    try:
        parsed = int(float(candidate))
    except ValueError:
        return CleanResult(None, ops)

    if str(parsed) != text:
        ops = (*ops, Operation.TO_INT)

    return CleanResult(parsed, tuple(ops))


def clean_decimal_2dp(value: Any) -> CleanResult:
    """Parse a price and render it with two decimals, so cents stay visible.

    Returns a *string* (``"0.00"``, ``"1.50"``) rather than a float: the point
    is the CSV's textual form. A blank stays None -- distinguishing a missing
    price (P4) from a zero price (P5) is the whole reason the raw files are read
    with ``dtype=str``.
    """
    text, ops = normalize_text(value)
    if text is None:
        return CleanResult(None, ops)

    candidate = text.replace(",", "").replace("$", "")
    try:
        parsed = float(candidate)
    except ValueError:
        return CleanResult(None, ops)

    formatted = config.PRICE_FORMAT.format(parsed)
    if formatted != text:
        ops = (*ops, Operation.TO_DECIMAL_2DP)

    return CleanResult(formatted, tuple(ops))


def split_iso_date(value: Any) -> DateParts:
    """Pull year, month, and day out of an ISO 8601 date.

    Menu_OR.csv carries a zero time part and a Z suffix
    (``1900-04-16T00:00:00Z``); only the date portion is read. Years outside the
    plausible band are rejected as a defensive re-check -- the OpenRefine export
    already excludes the five impossible years in the raw file.
    """
    text, ops = normalize_text(value)
    if text is None:
        return DateParts(None, None, None, ops)

    match = _ISO_DATE_RE.match(text)
    if not match:
        return DateParts(None, None, None, ops)

    year, month, day = (int(part) for part in match.groups())

    if not config.MIN_PLAUSIBLE_YEAR <= year <= config.MAX_PLAUSIBLE_YEAR:
        return DateParts(None, None, None, ops)
    if not 1 <= month <= 12 or not 1 <= day <= 31:
        return DateParts(None, None, None, ops)

    return DateParts(year, month, day, (*ops, Operation.DATE_SPLIT))


def map_currency(value: Any) -> CleanResult:
    """Map a currency label to its ISO-style abbreviation.

    Unmapped labels pass through unchanged rather than becoming None: dropping
    an unrecognised currency silently would hide a scope decision that belongs
    in docs/cleaning-rules.md, not here.
    """
    text, ops = normalize_text(value)
    if text is None:
        return CleanResult(None, ops)

    mapped = config.CURRENCY_MAP.get(text)
    if mapped is None:
        return CleanResult(text, ops)

    return CleanResult(mapped, (*ops, Operation.CURRENCY_MAPPED))


def _fold_accents(text: str) -> str:
    """Strip diacritics via canonical decomposition: ``Medoc`` from ``Médoc``."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def clean_dish_name(value: Any) -> CleanResult:
    """Normalize a dish name to uppercase ASCII alphanumerics, apostrophe, comma.

    Order matters and is fixed by config:

    1. trim and collapse whitespace
    2. fold typographic quotes and dashes to ASCII, so a curly apostrophe
       survives as an apostrophe instead of being dropped later
    3. fold accents (``Médoc`` -> ``MEDOC``), so accented and unaccented
       spellings of one dish cluster together
    4. uppercase
    5. mark names that still hold non-Latin characters as UNKNOWN -- deleting
       them would leave an empty string, losing the fact that a name was there
    6. expand ``&`` to the word AND
    7. turn separators into spaces, so ``Pflaumen-Kompott`` becomes two words
       rather than welding into ``PFLAUMENKOMPOTT``
    8. delete anything still outside the allowed set
    9. collapse the spaces those deletions opened up

    A name that cleans away to nothing (a symbol-only transcription artifact,
    problem P2) also becomes UNKNOWN, so no row silently loses its name.
    """
    text, ops = normalize_text(value)
    if text is None:
        return CleanResult(config.DISH_NAME_UNKNOWN, (*ops, Operation.MARKED_UNKNOWN))

    # Checked before any substitution: a name of "&" holds no dish, and
    # expanding it to AND would invent one. Catches the symbol-only
    # transcription artifacts of problem P2.
    if not any(ch.isalnum() for ch in text):
        return CleanResult(config.DISH_NAME_UNKNOWN, (*ops, Operation.MARKED_UNKNOWN))

    ops = list(ops)
    working = text

    requoted = working.translate(_QUOTE_TABLE)
    if requoted != working:
        ops.append(Operation.QUOTES_NORMALIZED)
    working = requoted

    folded = _fold_accents(working)
    if folded != working:
        ops.append(Operation.ACCENTS_FOLDED)
    working = folded

    uppered = working.upper()
    if uppered != working:
        ops.append(Operation.UPPERCASED)
    working = uppered

    # Anything non-ASCII that survived folding is a script this pipeline cannot
    # represent (CJK, Cyrillic, Greek). Mark rather than mangle.
    if any(ord(ch) > 127 for ch in working):
        return CleanResult(config.DISH_NAME_UNKNOWN, (*ops, Operation.MARKED_UNKNOWN))

    expanded = working.translate(_REPLACEMENT_TABLE)
    if expanded != working:
        ops.append(Operation.AMPERSAND_EXPANDED)
    working = expanded

    spaced = working.translate(_SEPARATOR_TABLE)
    if spaced != working:
        ops.append(Operation.PUNCT_TO_SPACE)
    working = spaced

    stripped = _DISALLOWED_RE.sub("", working)
    if stripped != working:
        ops.append(Operation.PUNCT_REMOVED)
    working = stripped

    tidied = _WHITESPACE_RE.sub(" ", working).strip()
    if tidied != working and Operation.SPACES_COLLAPSED not in ops:
        ops.append(Operation.SPACES_COLLAPSED)
    working = tidied

    # Backstop enforcing the invariant that this never returns an empty string.
    # The symbol-only check above should already have caught these.
    if not any(ch.isalnum() for ch in working):
        return CleanResult(config.DISH_NAME_UNKNOWN, (*ops, Operation.MARKED_UNKNOWN))

    return CleanResult(working, tuple(ops))
