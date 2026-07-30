"""Provenance: log accumulation, change capture, and stage snapshots.

One :class:`StepRecorder` per cleaning function. It applies value-level cleaners
from :mod:`src.cleaning_utils` to columns, accumulates the per-row ``log``, and
writes the stage's output directory:

    data/<table>/interim/func-<step>/<Table>_after_<step>.csv     the snapshot
    data/<table>/interim/func-<step>/<Table>_changes_<step>.csv   cell-level before/after
    data/<table>/interim/func-<step>/<Table>_summary_<step>.csv   counts per column/operation

The run directory is created here, on write -- which is why adding a cleaning
function needs no change to src/config.py and no directory committed to git.

Two deliberate asymmetries:

* **Change logs are opt-in per column.** Row-level before/after is recorded for
  semantic transforms (dish names, dates, currency) and skipped for
  formatting-only ones. Two-decimal padding alters ~886K MenuItem prices and
  ~788K Dish prices; recording each would produce change logs larger than the
  data while carrying no information the summary counts do not already give.
* **Nothing written here contains a timestamp.** The checklist requires the
  workflow be rerunnable with identical output, so a rerun must be diffable
  against the previous one.

Owner: Po Lin (Step 4)  [PoLin].
"""

from __future__ import annotations

import operator
from collections import Counter
from pathlib import Path
from typing import Any, Callable, NamedTuple

import pandas as pd

from src import config

# Deterministic, cross-platform CSV output: no index column, LF endings so a
# rerun on another machine diffs cleanly against this one.
_CSV_KWARGS: dict[str, Any] = {
    "index": False,
    "encoding": "utf-8",
    "lineterminator": "\n",
}

_READ_KWARGS: dict[str, Any] = {
    "dtype": str,
    "keep_default_na": False,
    "na_values": [],
    "encoding": "utf-8",
}

CHANGE_COLUMNS = (
    config.SOURCE_FILE_COLUMN,
    config.SOURCE_ROW_COLUMN,
    "row_id",
    "column",
    "before",
    "after",
    "operations",
)

SUMMARY_COLUMNS = ("table", "step", "column", "operation", "rows_affected")


class OpenRefineShapeError(ValueError):
    """An OpenRefine export does not have the columns config declares."""


def load_or_export(table_key: str) -> pd.DataFrame:
    """Read a table's OpenRefine export and stamp the provenance columns.

    Read as text (``dtype=str``, no NA coercion) so a blank price stays
    distinguishable from a ``0.0`` price -- problems P4 and P5 are different
    problems and pandas' type inference would merge them.

    ``source_row_num`` is the 1-based data row of the export, so any row in any
    downstream artifact can be traced back to the line it came from.
    """
    table = config.TABLES[table_key]
    frame = pd.read_csv(table.or_file, **_READ_KWARGS)

    expected = config.OR_EXPECTED_COLUMNS[table_key]
    actual = tuple(frame.columns)
    if actual != expected:
        raise OpenRefineShapeError(
            f"{table.or_file.name} has columns {actual}, expected {expected}. "
            f"If the OpenRefine recipe changed, update OR_EXPECTED_COLUMNS in "
            f"src/config.py so the pipeline and the export agree."
        )

    frame[config.SOURCE_FILE_COLUMN] = table.or_file.name
    frame[config.SOURCE_ROW_COLUMN] = range(1, len(frame) + 1)
    frame[config.LOG_COLUMN] = ""
    return frame


def _as_text(series: pd.Series) -> pd.Series:
    """Render a column as comparable text, with every flavour of null becoming ''.

    Deliberately vectorized rather than ``.map()`` with a lambda. On a nullable
    ``Int64`` column holding ``pd.NA``, ``.map()`` coerces the whole column to
    float before calling the function, so 1 arrives as ``1.0`` and ``pd.NA``
    arrives as ``float('nan')`` -- which is not ``pd.NA`` and stringifies to
    ``"nan"``. Every value then compares unequal to its own original, and the
    change log fills with a row per record showing ``before == after``.
    """
    return series.astype("string").fillna("")


def _join_tags(existing: pd.Series, incoming: pd.Series) -> pd.Series:
    """Append new log tags, keeping the separator out of empty entries."""
    both = existing.str.cat(incoming, sep=config.LOG_SEPARATOR)
    # str.cat unconditionally inserts the separator, so repair the ends.
    return (
        both.str.strip(config.LOG_SEPARATOR)
        .str.replace(
            f"{config.LOG_SEPARATOR}{config.LOG_SEPARATOR}",
            config.LOG_SEPARATOR,
            regex=False,
        )
    )


class StageOutput(NamedTuple):
    """Where one cleaning stage wrote its artifacts."""

    frame: pd.DataFrame
    directory: Path
    snapshot: Path
    changes: Path | None
    summary: Path


class StepRecorder:
    """Applies cleaners to one table for one stage, accumulating provenance.

    Typical use inside a cleaning function::

        rec = StepRecorder("menu", "currency-map")
        frame = rec.apply(frame, "currency", map_currency)
        return rec.write(frame).frame
    """

    def __init__(self, table_key: str, step: str) -> None:
        self.table_key = table_key
        self.table = config.TABLES[table_key]
        self.step = step
        self._changes: list[pd.DataFrame] = []
        self._counts: Counter[tuple[str, str]] = Counter()

    # -- applying cleaners ------------------------------------------------
    def apply(
        self,
        frame: pd.DataFrame,
        column: str,
        cleaner: Callable[[Any], Any],
        *,
        record_changes: bool = True,
        trivial_ops: frozenset[str] = frozenset(),
        dtype: str | None = None,
        id_column: str = "id",
    ) -> pd.DataFrame:
        """Clean one column in place, logging what each row's cleaning did.

        Set ``record_changes=False`` for formatting-only work, where the summary
        counts carry the same information at a fraction of the size.

        ``trivial_ops`` names operations that do not on their own justify a
        change row. A row is written only if something outside that set also
        happened, so uppercasing 380K dish names does not bury the 9K accent
        folds and 647 UNKNOWN marks that are the actual evidence. Counts are
        unaffected -- every operation is still tallied in the summary.

        ``dtype`` should be ``"Int64"`` for any integer column that can hold
        nulls. Without it pandas upcasts the column to float and writes ``1.0``
        where the value is 1, which silently breaks a join against a table whose
        key was written as ``1``.
        """
        frame = frame.copy()
        results = frame[column].map(cleaner)
        values = results.map(operator.attrgetter("value"))
        ops = results.map(operator.attrgetter("ops"))
        if dtype is not None:
            values = values.astype(dtype)

        self._record(frame, column, values, ops, record_changes, trivial_ops, id_column)
        frame[column] = values
        frame[config.LOG_COLUMN] = _join_tags(
            frame[config.LOG_COLUMN], self._tag_series(column, ops)
        )
        return frame

    def expand(
        self,
        frame: pd.DataFrame,
        column: str,
        expander: Callable[[Any], Any],
        new_columns: tuple[str, ...],
        *,
        id_column: str = "id",
    ) -> pd.DataFrame:
        """Derive several columns from one, keeping the source column intact.

        Used for the date split: ``date`` stays, and ``year``/``month``/``day``
        appear beside it. Preserving the original is rule 3 in src/README.md --
        a reviewer has to be able to see what the derived value came from.
        """
        frame = frame.copy()
        results = frame[column].map(expander)
        ops = results.map(operator.attrgetter("ops"))

        for position, name in enumerate(new_columns):
            frame[name] = results.map(operator.itemgetter(position))

        derived = ", ".join(new_columns)
        for row_ops in ops:
            for op in row_ops:
                self._counts[(derived, op)] += 1

        frame[config.LOG_COLUMN] = _join_tags(
            frame[config.LOG_COLUMN], self._tag_series(column, ops)
        )
        return frame

    def winsorize(
        self,
        frame: pd.DataFrame,
        column: str,
        upper_limit: float,
        *,
        id_column: str = "id",
    ) -> tuple[pd.DataFrame, float | None]:
        """Cap values above the ``1 - upper_limit`` quantile at that quantile.

        Unlike :meth:`apply`, this needs the whole column's distribution, so it
        cannot be expressed as a per-value cleaner in cleaning_utils.

        **Right tail only.** The left tail of a price distribution is real data,
        not error: capping it would inflate the cheap menus U1 has to rank as
        cheap. See the evidence in config.WINSORIZE_UPPER_LIMIT.

        The threshold is computed over *positive* values only, so the large
        blocks of zero and missing prices cannot drag it downward.

        Returns the frame and the threshold used (None if nothing to do).
        """
        numeric = pd.to_numeric(frame[column], errors="coerce")
        positive = numeric[numeric > 0]
        if positive.empty:
            return frame, None

        threshold = float(positive.quantile(1 - upper_limit))
        exceeded = numeric > threshold
        capped_count = int(exceeded.sum())
        if not capped_count:
            return frame, threshold

        frame = frame.copy()
        replacement = config.PRICE_FORMAT.format(threshold)
        values = frame[column].where(~exceeded, replacement)

        self._counts[(column, config.Operation.WINSORIZED)] += capped_count
        self._counts[(column, config.Reason.SUSPICIOUS_EXTREME_PRICE)] += capped_count
        self._changes.append(
            pd.DataFrame(
                {
                    config.SOURCE_FILE_COLUMN: frame.loc[exceeded, config.SOURCE_FILE_COLUMN],
                    config.SOURCE_ROW_COLUMN: frame.loc[exceeded, config.SOURCE_ROW_COLUMN],
                    "row_id": frame.loc[exceeded, id_column],
                    "column": column,
                    "before": frame.loc[exceeded, column],
                    "after": replacement,
                    "operations": config.Operation.WINSORIZED,
                }
            )
        )

        frame[column] = values
        incoming = pd.Series("", index=frame.index, dtype="object")
        incoming[exceeded] = config.log_tag(column, config.Operation.WINSORIZED)
        frame[config.LOG_COLUMN] = _join_tags(frame[config.LOG_COLUMN], incoming)
        return frame, threshold

    def drop_column(self, frame: pd.DataFrame, column: str) -> pd.DataFrame:
        """Remove a column, recording that it happened.

        Logged rather than done silently: a column vanishing between the
        OpenRefine export and the staging schema is exactly the kind of change
        the Step-5 summary has to account for.
        """
        frame = frame.copy()
        self._counts[(column, config.Operation.COLUMN_DROPPED)] += len(frame)
        frame = frame.drop(columns=[column])
        frame[config.LOG_COLUMN] = _join_tags(
            frame[config.LOG_COLUMN],
            pd.Series(
                [config.log_tag(column, config.Operation.COLUMN_DROPPED)] * len(frame),
                index=frame.index,
            ),
        )
        return frame

    def note(self, column: str, operation: str, rows: int) -> None:
        """Record an operation the recorder did not itself perform."""
        self._counts[(column, operation)] += rows

    def tag_rows(
        self, frame: pd.DataFrame, mask: pd.Series, column: str, operation: str
    ) -> pd.DataFrame:
        """Append a log tag to the rows selected by ``mask``, and count them.

        For decisions taken about whole rows rather than by cleaning a value --
        the omit rule being the only one in this pipeline.
        """
        frame = frame.copy()
        self._counts[(column, operation)] += int(mask.sum())

        tag = config.log_tag(column, operation)
        incoming = pd.Series("", index=frame.index, dtype="object")
        incoming[mask] = tag
        frame[config.LOG_COLUMN] = _join_tags(frame[config.LOG_COLUMN], incoming)
        return frame

    # -- internals --------------------------------------------------------
    def _tag_series(self, column: str, ops: pd.Series) -> pd.Series:
        return ops.map(
            lambda row_ops: config.LOG_SEPARATOR.join(
                config.log_tag(column, op) for op in row_ops
            )
        )

    def _record(
        self,
        frame: pd.DataFrame,
        column: str,
        values: pd.Series,
        ops: pd.Series,
        record_changes: bool,
        trivial_ops: frozenset[str],
        id_column: str,
    ) -> None:
        # Counted before any filtering, so the summary stays complete even when
        # the change log is narrowed.
        for row_ops in ops:
            for op in row_ops:
                self._counts[(column, op)] += 1

        if not record_changes:
            return

        changed = _as_text(frame[column]) != _as_text(values)
        if trivial_ops:
            changed &= ops.map(lambda row_ops: bool(set(row_ops) - trivial_ops))
        if not changed.any():
            return

        self._changes.append(
            pd.DataFrame(
                {
                    config.SOURCE_FILE_COLUMN: frame.loc[changed, config.SOURCE_FILE_COLUMN],
                    config.SOURCE_ROW_COLUMN: frame.loc[changed, config.SOURCE_ROW_COLUMN],
                    "row_id": frame.loc[changed, id_column],
                    "column": column,
                    "before": frame.loc[changed, column],
                    "after": values[changed],
                    "operations": ops[changed].map(config.LOG_SEPARATOR.join),
                }
            )
        )

    # -- writing ----------------------------------------------------------
    def summary(self) -> pd.DataFrame:
        rows = [
            {
                "table": self.table_key,
                "step": self.step,
                "column": column,
                "operation": operation,
                "rows_affected": count,
            }
            for (column, operation), count in sorted(self._counts.items())
        ]
        return pd.DataFrame(rows, columns=list(SUMMARY_COLUMNS))

    def write(self, frame: pd.DataFrame, *, suffix: str = "after") -> StageOutput:
        """Write the stage's snapshot, change log, and summary.

        Creates ``data/<table>/interim/func-<step>/`` if it does not exist.
        """
        directory = self.table.func_dir(self.step)
        directory.mkdir(parents=True, exist_ok=True)
        stem = self.table.name

        snapshot = directory / f"{stem}_{suffix}_{self.step}.csv"
        _order_columns(frame).to_csv(snapshot, **_CSV_KWARGS)

        # Named unconditionally so a stale file from an earlier run can be
        # removed. Without this, a stage that stops producing changes leaves the
        # previous run's change log behind, and the directory no longer
        # describes the run that produced it.
        candidate = directory / f"{stem}_changes_{self.step}.csv"
        changes_path: Path | None = None
        if self._changes:
            changes = pd.concat(self._changes, ignore_index=True)
            changes = changes.sort_values(
                [config.SOURCE_ROW_COLUMN, "column"], kind="stable"
            )
            changes_path = candidate
            changes[list(CHANGE_COLUMNS)].to_csv(changes_path, **_CSV_KWARGS)
        elif candidate.exists():
            candidate.unlink()

        summary_path = directory / f"{stem}_summary_{self.step}.csv"
        self.summary().to_csv(summary_path, **_CSV_KWARGS)

        return StageOutput(frame, directory, snapshot, changes_path, summary_path)


def _order_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Data columns first, provenance last.

    Keeps a snapshot diffable against the OpenRefine export it came from, and
    keeps the long ``log`` column out of the way when the file is opened.
    """
    trailing = [
        column
        for column in (
            config.SOURCE_FILE_COLUMN,
            config.SOURCE_ROW_COLUMN,
            config.OMIT_COLUMN,
            config.LOG_COLUMN,
        )
        if column in frame.columns
    ]
    leading = [column for column in frame.columns if column not in trailing]
    return frame[leading + trailing]


def write_table(frame: pd.DataFrame, destination: Path) -> Path:
    """Write a frame with the pipeline's deterministic CSV settings.

    For artifacts that sit outside the standard snapshot/changes/summary trio --
    the excluded-record file being the case that needs it.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    _order_columns(frame).to_csv(destination, **_CSV_KWARGS)
    return destination


PROVENANCE_ONLY_COLUMNS = (
    config.SOURCE_FILE_COLUMN,
    config.SOURCE_ROW_COLUMN,
    config.OMIT_COLUMN,
    config.LOG_COLUMN,
)


def strip_provenance(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop the columns that describe the pipeline rather than the data.

    Kept out of the load-ready CSV because they answer "how did this value get
    here", which no U1 query asks. The full audit trail stays in the
    func-<step>/ snapshots and in cleaning_log.csv.
    """
    present = [column for column in PROVENANCE_ONLY_COLUMNS if column in frame.columns]
    return frame.drop(columns=present)


def write_cleaned(frame: pd.DataFrame, table_key: str) -> Path:
    """Write the load-ready CSV to data/<table>/interim/cleaned/<Table>_cleaned.csv.

    Data columns only. Provenance columns are stripped here, not earlier, so
    every stage snapshot upstream still carries them.
    """
    table = config.TABLES[table_key]
    table.cleaned_dir.mkdir(parents=True, exist_ok=True)
    destination = table.cleaned_file
    strip_provenance(frame).to_csv(destination, **_CSV_KWARGS)
    return destination


def collect_cleaning_log() -> Path:
    """Concatenate every stage summary into data/reports/cleaning_log.csv.

    The machine-readable record of rule applications that the Step-5 change
    table is computed from -- see docs/data-dictionary.md.
    """
    frames = [
        pd.read_csv(path, **_READ_KWARGS)
        for table in config.TABLES.values()
        for path in sorted(table.interim_dir.glob("func-*/*_summary_*.csv"))
    ]

    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    destination = config.REPORTS_DIR / "cleaning_log.csv"

    combined = (
        pd.concat(frames, ignore_index=True)
        if frames
        else pd.DataFrame(columns=list(SUMMARY_COLUMNS))
    )
    combined.to_csv(destination, **_CSV_KWARGS)
    return destination
