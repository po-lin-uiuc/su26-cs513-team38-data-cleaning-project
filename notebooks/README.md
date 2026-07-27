# Notebooks

Exploratory profiling and figure generation only. **Nothing in the cleaning pipeline should
depend on a notebook** — anything that must be reproducible belongs in [../src/](../src/).

Suggested:

| Notebook | Purpose |
| --- | --- |
| `01-profile-raw.ipynb` | Distributions, missing-value counts, outliers (S2) [CharleneKhun] |
| `02-price-coverage.ipynb` | How much price data each fallback rule recovers (S3 §4.6) [PoLin] |
| `03-before-after.ipynb` | Charts for the Phase-II before/after section [Team] |

## Conventions

- Number notebooks so the reading order is obvious.
- Import from `src` rather than redefining paths: `from src import config`.
- **Restart and run all** before committing — a notebook whose outputs do not match its code
  is worse than no notebook.
- Notebooks are supplementary-material deliverables (Phase-II, "other scripts, provenance
  files"), so keep them presentable.
