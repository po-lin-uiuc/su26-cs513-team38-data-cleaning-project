# CS 513 — Team 38 Data Cleaning Project

**Theory & Practice of Data Cleaning — University of Illinois Urbana-Champaign, Summer 2026**

Dataset: New York Public Library (NYPL) *"What's on the Menu?"* historic menus data
(`Menu.csv`, `MenuPage.csv`, `MenuItem.csv`, `Dish.csv`).

## Team

| Name | Illinois email | Phase-II ownership |
| --- | --- | --- |
| Charlene Khun | ckhun2@illinois.edu | OpenRefine profiling, cleaning-rule catalog, IC/domain constraints |
| Madalyn Killian | killian7@illinois.edu | SQLite staging, loading, inclusion dependencies, violation iteration |
| Po Lin | pohungl2@illinois.edu | Python/pandas cleaning, functional dependencies, final operational tables |

Per-person checklists: [docs/checklists/](docs/checklists/).

## Finding your work

Every file or section waiting on someone carries an **action token**. Search the repo for
yours and you get the complete list of what needs your attention — no need to know the layout.

| Owner | Token |
| --- | --- |
| Charlene Khun | `[CharleneKhun]` |
| Madalyn Killian | `[MadalynKillian]` |
| Po Lin | `[PoLin]` |
| All three | `[Team]` |

```powershell
git grep -n --untracked "\[PoLin\]"        # everything waiting on Po
git grep -n --untracked "\[Team\]"         # shared items
git grep -n --untracked "TODO \[PoLin\]"   # just the code stubs Po must fill in
```

`--untracked` matters: plain `git grep` searches only committed files, so it silently misses
anything not yet added. It also respects `.gitignore`, so `data/` never pollutes the results.

Editor search works the same way — type the token into VS Code's search box (Ctrl+Shift+F).

Rules for the tokens:

- A token marks **required action**, not authorship. Remove it when the work is done, so a
  clean search means you're finished.
- Shared work carries `[Team]` alongside the individual tokens, so `[Team]` never hides a
  personal task and vice versa.
- Code stubs use `TODO [Owner]:` so a search for `TODO` still finds them.
- Pure reference material (dataset description, use cases, DQ problems) carries no token —
  nothing there is waiting on anyone.

## Project description

The NYPL menus dataset transcribes historic restaurant menus from the mid-1800s to the
present, from locations worldwide. It is published as four linked tables: a menu, its
scanned pages, the items transcribed on each page, and a dish dictionary that aggregates
each distinct dish across all menus.

Our **main use case (U1)** is to classify menus into price tiers (`$`, `$$`, `$$$`, `$$$$`)
*relative to the distribution of menu prices within comparable time periods*. That analysis
is impossible on the raw data: menu dates include impossible values (`0190`, `1091`) and
535+ blanks, prices are missing or recorded as `0.0`, currency fields are frequently empty
and otherwise mix non-comparable currencies, and dish names carry heavy transcription noise
(`Cafee`/`Cofee`/`Kafee` for coffee; `Beef, Roast` vs `Roast Beef.`). Cleaning dates,
prices, currencies, and dish names is *necessary* to answer U1 — and *sufficient*, because
no external data is required once those fields are trustworthy.

Two corner cases bound the scope: **U0** (listing raw transcribed items for a menu, and
longest-running dishes by first/last appeared) needs no cleaning, and **U2** (menu
affordability versus local income and economic conditions) can never be answered from this
dataset alone, since it requires cost-of-living, inflation, and tax data plus a
locality precision the `place` column does not have.

Full write-ups: [dataset description](docs/dataset-description.md) ·
[use cases](docs/use-cases.md) · [data quality problems](docs/data-quality-problems.md) ·
[Phase-II plan](docs/phase2-plan.md).

## Approach

Cleaning runs as an iterative loop rather than a single pass. OpenRefine is used for
**profiling and review** — the raw files are too large to make it the primary cleaning
tool — while Python/pandas performs the repeatable, type-based cleaning, and **SQLite** acts
as the **validation layer** (integrity constraints, inclusion dependencies, functional
dependencies). Rows are never silently dropped: pandas writes `cleaning_status`,
`warning_reason`, and `exclusion_reason` flags alongside `source_file` / `source_row_num`
so every exclusion is explainable and D → D′ is quantifiable.

```
data/raw/  ──▶ OpenRefine profiling ──▶ src/ (pandas cleaning) ──▶ data/interim/
                                                                       │
                          data/reports/ ◀── sql/ validation (IC/IND/FD)┘
                                │                                      │
                                └── violations reviewed, loop repeats ──┘
                                                                       ▼
                                                                 data/final/  (D′)
```

## Repository layout

| Path | Contents |
| --- | --- |
| [docs/](docs/) | Report sources and reference write-ups (dataset, use cases, DQ problems, plans) |
| [docs/checklists/](docs/checklists/) | Per-person Phase-II checklists — the team's tracking surface |
| [docs/figures/](docs/figures/) | Screenshots and diagrams referenced by the reports |
| [data/](data/) | Local data tree — **git-ignored**, datasets are shared via Box |
| [src/](src/) | Python/pandas cleaning pipeline |
| [notebooks/](notebooks/) | Exploratory profiling notebooks (not the pipeline) |
| [sql/](sql/) | SQLite staging + final schema, load scripts, IC/IND/FD validation queries |
| [openrefine/](openrefine/) | OpenRefine operation history and profiling notes |
| [workflow/](workflow/) | Workflow models W1 (outer) and W2 (inner) |
| [deliverables/](deliverables/) | Exactly what gets submitted, per phase |

Working documents that fill in as Phase-II proceeds:
[cleaning-rules.md](docs/cleaning-rules.md) (rule catalog) ·
[data-dictionary.md](docs/data-dictionary.md) (generated fields) ·
[iteration-log.md](docs/iteration-log.md) (cleaning-loop iterations and stopping rationale).

## Getting started

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then download the four raw CSVs into `data/raw/` (see [data/README.md](data/README.md)).

The pipeline entry point is `python -m src.run_pipeline`; stages are added as they are built
(see [src/README.md](src/README.md)). The SQL layer needs the `sqlite3` CLI, which is a
separate install on Windows — see [sql/README.md](sql/README.md).

## Submission rules (read before submitting)

Each artifact may be submitted **once** — Phase-I report, Phase-II report, and the
supplementary ZIP are manually graded and cannot be resubmitted. Assemble and review in
[deliverables/](deliverables/), and confirm against
[docs/deliverables-checklist.md](docs/deliverables-checklist.md) before uploading.

Raw and cleaned datasets must **not** go in the ZIP; upload them to Box and put the link in
`deliverables/phase2/DataLinks.txt`.
