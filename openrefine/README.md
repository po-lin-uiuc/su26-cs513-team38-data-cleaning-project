# OpenRefine  [CharleneKhun]

OpenRefine is used for **profiling and review**, not as the primary cleaning tool — the raw
files are large enough that OpenRefine's memory requirements make it impractical for the full
cleaning pass. The repeatable cleaning lives in [../src/](../src/).

Where it *is* the right tool: cluster inspection. Fingerprint, metaphone, and cologne-phonetic
keying surfaced problems P1–P3 in [../docs/data-quality-problems.md](../docs/data-quality-problems.md),
and it stays the fastest way to review the violation CSVs that come back from SQL (S3 Step 8).

## Contents

| Path | Contents |
| --- | --- |
| `history/` | Exported operation history — `OpenRefineHistory.json` is a required deliverable |
| `notes/` | Profiling notes per column: what was inspected, what was found, which figure documents it |

## Exporting history

In the project: **Undo / Redo → Extract…** → select the operations → copy the JSON into
`history/OpenRefineHistory.json`. Export after each session; the history is lost if the
workspace is deleted.

One file per session or per table (e.g. `history/dish-name-clustering.json`) is easier to
review than one giant file. Concatenate into a single `OpenRefineHistory.json` at submission.

Optionally visualize with [OR2YW](https://github.com/idaks/OR2YWTool) to produce the inner
workflow W2 — output goes in [../workflow/](../workflow/).

## Cluster settings worth recording

For each clustering pass, note the method and parameters in `notes/` alongside the result —
the report needs to state *how* clusters were found, not just that they were.

| Method | Used for |
| --- | --- |
| key collision / fingerprint | P1 — `Broiled Chicken`, `Roast Beef` variants |
| key collision / metaphone | P2 — numeric and symbol-only names |
| key collision / cologne phonetic | P3 — `Cafee`/`Cofee`/`Kafee`, `The`/`Thee` |
