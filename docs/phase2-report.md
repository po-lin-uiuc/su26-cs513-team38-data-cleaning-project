# CS 513 — Phase-II Report (scaffold)  [Team]

**Team 38** — Charlene Khun (ckhun2@illinois.edu), Madalyn Killian (killian7@illinois.edu),
Po Lin (pohungl2@illinois.edu)

**Dataset:** NYPL *"What's on the Menu?"*

> Section headings follow the Phase-II rubric exactly. Fill each section as the work lands;
> do not restructure. Export to `deliverables/phase2/CS513-Team38-Phase2-Report.pdf`.

## 1. Description of data cleaning performed

### 1.1 High-level cleaning steps (20 pts)  [PoLin] [CharleneKhun] [MadalynKillian]

Cleaning runs as three passes: OpenRefine for profiling and scope filtering (Charlene),
Python/pandas for repeatable type-based cleaning (Po), and SQL for validation and the joins U1
needs (Madalyn). Each pass writes files the next one reads; none writes back over its input.

Because the three passes are owned by different members, they were not run strictly in sequence —
§B below records the preliminary OpenRefine pass that let the Python and SQL work start in
parallel.

#### A. Repository organized for provenance (Step 1)

`data/` is organized **by source table**, and within each table by **processing stage**, so any
value in any output traces back to the file and row it came from. Every path below is a real
directory in the submitted data set.

```
data/
├── menu/  menu-page/  menu-item/  dish/      one tree per source table
│   ├── raw/<Name>.csv                        immutable input, never written to
│   └── interim/
│       ├── open-refine/<Name>_OR.csv         OpenRefine export — input to the pipeline
│       ├── func-<step>/                      one directory per cleaning function
│       │   ├── <Name>_after_<step>.csv         full snapshot after that function ran
│       │   ├── <Name>_changes_<step>.csv       cell-level before/after, where applicable
│       │   └── <Name>_summary_<step>.csv       rows affected per column and operation
│       └── cleaned/<Name>_cleaned.csv        load-ready for SQLite, provenance stripped
├── reports/cleaning_log.csv                  every stage summary concatenated
└── final/                                    SQL workflow outputs (Step 9)
```

**Reading a table's history.** The `func-<step>/` directories are the mechanism. Each cleaning
function writes a *complete* snapshot of the table as it stood when that function finished, so
the effect of any single rule is obtained by diffing two adjacent directories — no rule's effect
has to be inferred. Three files describe each stage at decreasing resolution:

| File | Answers |
| --- | --- |
| `<Name>_after_<step>.csv` | What did the whole table look like after this rule? |
| `<Name>_changes_<step>.csv` | Which individual cells changed, and from what to what? |
| `<Name>_summary_<step>.csv` | How many rows did each operation affect, per column? |

A change file is absent where a rule is formatting-only, because a row-level record of two-decimal
padding would be larger than the data and carries nothing the summary does not. `MenuItem`'s
omit stage additionally writes `MenuItem_before_omit-check.csv` and `MenuItem_omitted.csv`, so
the excluded rows can be inspected on their own.

**Directories are created by the code at run time**, not fixed in advance. Adding a cleaning rule
is therefore a single change — write the function; its directory appears on the next run — and a
deleted rule leaves no empty directory behind.

**The number of stage directories differs per table**, because each table runs only the rules its
column types require. That asymmetry is deliberate and is what the W2 model (§3.2) depicts:

| Table | Stages | Chain |
| --- | --- | --- |
| MenuPage | 1 | `id-numeric` |
| Menu | 4 | `id-numeric` → `date-split` → `currency-map` → `drop-status` |
| Dish | 4 | `id-numeric` → `dish-name` → `price-decimal` → `price-outlier` |
| MenuItem | 4 | `id-numeric` → `price-decimal` → `price-outlier` → `omit-check` |

**What ships.** 46 files, 788 MiB. Only **8 of them are inputs**: the four raw CSVs (146 MiB) and
the four OpenRefine exports (51 MiB). The other 37 files (591 MiB) and all 18 of their directories
are produced by the pipeline.

**Reproducing the data set.** With the eight input files in place:

```powershell
python -m src.run_pipeline     # rebuilds every generated file, ~33 seconds
```

**This was verified from an empty tree, not merely asserted.** We deleted all 37 generated files
and all 18 generated directories, leaving only the eight inputs, and re-ran the pipeline. Every
one of the 37 files was reproduced **byte-for-byte identically**, confirmed by comparing SHA-256
hashes recorded before the deletion against the rebuilt tree. Nothing in the generated data
depends on run history, on a partially populated directory, or on the order in which stages were
first written — which is what makes the `func-<step>/` snapshots usable as evidence rather than
as a record of one particular session. The determinism rests on two properties: no artifact
contains a timestamp, and each stage rewrites its own outputs and deletes any of its own files
that a run no longer produces.

#### B. Preliminary OpenRefine pass to unblock Step 4  [PoLin]

**OpenRefine profiling and cleaning is Charlene's work** (Steps 2 and 3). Her definitive pass —
the operation history submitted as `OpenRefineHistory.json`, and the cleaning-rule catalog in
[cleaning-rules.md](cleaning-rules.md) — is in progress.

Rather than hold Steps 4–10 until it lands, Po ran a **preliminary** OpenRefine pass over the four
raw tables and exported one `<Name>_OR.csv` per table. Those exports are the input to Step 4, and
they let the Python pipeline and the SQL staging work proceed concurrently with Charlene's
profiling instead of serially after it.

The preliminary pass applied the scope filters that define the U1 population: menus restricted to
complete records with a usable date and a dollar-denominated currency (17,545 → 5,236), and
dishes restricted to those carrying both a lowest and a highest price (423,397 → 394,297).
MenuPage and MenuItem were exported unfiltered.

**This is a deviation from the Phase-I plan** and is recorded in
[Plan vs. actual](#plan-vs-actual). The plan had Step 2 complete before Step 4 began; we ran them
in parallel instead. The cost is that Step 4 may need re-running if Charlene's definitive rules
differ from the preliminary filters — which is cheap, because the pipeline reruns from the exports
deterministically and produces byte-identical output. The benefit is that three members worked
concurrently rather than two waiting on one.

#### C. Python/pandas type-based cleaning (Step 4)

Thirteen functions across the four tables, each column-type specific. Every file is read as text
(`dtype=str`, no NA coercion) so a blank price stays distinguishable from a `0.00` price —
pandas' type inference would otherwise merge two different problems (P4 and P5) into one.

| Rule | Table.column | What it does |
| --- | --- | --- |
| R-1 | all `id`, `menu_id`, `menu_page_id`, `dish_id` | Coerce identifiers to integers, using a nullable integer type so a column containing absent values is not silently widened to floating point |
| R-2 | `Menu.date` | Split the ISO 8601 timestamp into separate `year`, `month`, `day` columns, then drop the original string |
| R-3 | `Menu.currency` | Map currency labels to ISO abbreviations (`Dollars` → `USD`) through a lookup table |
| R-4 | `Menu.status` | Drop the column, after confirming at run time that it holds a single value |
| R-5 | `Dish.name` | Normalize to uppercase ASCII alphanumerics plus apostrophe and comma: fold typographic quotes and dashes, fold accents, expand `&` to `AND`, convert separators to spaces, delete remaining punctuation, collapse whitespace, mark non-Latin and symbol-only names `UNKNOWN` |
| R-6 | `Dish.lowest_price`, `Dish.highest_price`, `MenuItem.price`, `MenuItem.high_price` | Render prices to two decimals so cent values are visible (`0.2` → `0.20`), preserving blanks as blanks |
| R-7 | the same four price columns | Winsorize the right tail: cap values above the 99.5th percentile at that percentile. Rows are never dropped and the left tail is untouched |
| R-8 | `MenuItem` | Flag and remove rows with neither a `dish_id` nor any positive price, writing the flagged set, the reduced set, and the removed rows as three separate files |

#### D. Provenance captured alongside every rule

Three machine-readable artifacts accompany each stage:

- a **`log` column** on every row, accumulating `<column>:<operation>` tags across the whole
  chain, so one row's history reads
  `date:date_split;date:column_dropped;currency:currency_mapped;status:column_dropped`;
- a **change log** recording the before and after value of each modified cell with its source row
  number;
- a **stage summary** counting rows affected per column and operation, concatenated into
  `data/reports/cleaning_log.csv` — the source for §2.1.

`log`, `source_file`, and `source_row_num` are carried through every stage snapshot but
**stripped from the load-ready CSVs**: they describe the pipeline, not the data, and no U1 query
refers to them.

The pipeline reruns from the OpenRefine exports with byte-identical output — no artifact contains
a timestamp, and every stage overwrites its own directory rather than appending.

#### E. SQL validation and final tables (Steps 5–10)

_Pending — staging and load, the IC/IND/FD checks, and the final operational tables. The price
fallback of §4.6 of our plan is resolved there rather than in pandas, because it needs MenuItem
joined to Dish._

### 1.2 Rationale per step (20 pts)  [PoLin] [CharleneKhun] [MadalynKillian]

U1 classifies menus into price tiers relative to other menus **of the same period**, so it needs
three things to be trustworthy: the menu's date, the prices of its items, and a currency making
those prices comparable. Each rule is justified against that, and three of the eight are only
partly required.

| Rule | Problem | Required for U1? | Why |
| --- | --- | --- | --- |
| R-1 identifiers | — | **Yes**, indirectly | U1 needs average price *per menu*, which exists only after joining MenuItem → MenuPage → Menu and MenuItem → Dish. A key in an inconsistent representation breaks that join. This rule caught a real instance: `dish_id` was being written `1.0` rather than `1`, which would not have matched `Dish.id` |
| R-2 date split | **P6, P7** | **Yes** | "Comparable time period" is the grouping key of the entire use case. A menu with no usable year belongs to no group; an impossible year (`0190`, `1091`, `2928`) puts it in the wrong one |
| R-3 currency mapping | **P8** | **Yes** | The same number means different purchasing power in different currencies, so prices are not comparable until currency is explicit and uniform. Mapping to `USD` makes the restriction visible in the data rather than implicit in a filter |
| R-4 drop status | — | **No** | Useful, not necessary. The column is constant after the preliminary OpenRefine filter, so it carries no information into staging, and dropping it keeps the staging schema honest about what actually varies. The rule refuses to drop if the column is *not* constant, so it cannot destroy a distinction by accident |
| R-5 dish names | **P1, P2, P3** | **Partly** | Not required to compute a menu's average price, which needs only prices and dates. It *is* required for the dish-level grouping that lets U1 compare like with like, and it makes the P1–P3 evidence quantifiable: 40,721 name variants collapsed |
| R-6 price decimals | **P4, P5** | **Yes** | Averaging requires a consistent numeric representation, and cents are the unit prices are recorded in. Preserving blanks rather than defaulting them to zero is what keeps P4 (missing) separate from P5 (recorded as zero); collapsing them would silently deflate every menu average |
| R-7 outlier capping | **P5** | **Partly** | Menu averages are sensitive to extremes, so an implausible price distorts the tier its menu lands in. In practice the effect is small, because the right tail turns out to be a currency artifact rather than transcription error — see below |
| R-8 omit check | **P4, P5** | **Yes** | A row with neither a `dish_id` nor a positive price cannot be priced by any route, including the dish-level fallback, so it can never contribute to a menu average. This is the only row deletion the pipeline performs: 236 rows, 0.018% |

**On R-7, the outlier rule, three decisions are worth stating because each rejects an obvious
alternative.**

*Capping rather than deleting.* Winsorization replaces an extreme value with the threshold and
keeps the row. Deleting would change how many priced items each menu has, which changes the
average that U1 compares — and would delete rows for being unusual rather than for being wrong.

*The right tail only.* The left tail of a menu price distribution is real data: the median item
is $0.40 and a $0.05 coffee is a genuine price. We tested a symmetric 3% trim and it moved the
per-menu average by **+8.7% for the cheapest quartile of menus and −32.0% for the priciest**,
compressing the very price range U1 exists to measure. Capping only the right tail at 0.5% moves
the priciest quartile by **−0.1%** and the other three by 0.0%.

*A 0.5% limit, chosen on evidence.* Of the 4,251 `MenuItem.price` values it caps, only **28
(0.7%) sit on dollar-denominated menus**. The extreme prices are overwhelmingly foreign-currency
amounts — 180,000 on an Italian Lire menu is an ordinary price, not an error — from menus the
currency filter already excludes from U1. The rule is therefore doing less work than it appears
to, and we prefer to say so rather than claim it repaired the data.

Two rules were deliberately **not** applied here, and both decisions are load-bearing:

**Missing prices are not a reason to exclude a row.** 445,974 MenuItem rows have a `dish_id` but
no price of their own. Resolving those is the fallback chain in §4.6 of our plan, which needs
Dish values alongside MenuItem and so belongs in SQL. Dropping them in pandas would have
pre-empted a decision this stage cannot make, and would have removed a third of the table.

**No currency conversion is performed.** Converting non-dollar menus to USD needs historical
exchange rates, which are external data — and our Phase-I argument for U1 rests on no external
data being required. Non-dollar menus are excluded and the limitation stated rather than papered
over; §A.2 records the investigation behind this.

## 2. Document data quality changes

### 2.1 Summary table of changes (10 pts)  [CharleneKhun] [PoLin]

Source: `data/reports/cleaning_log.csv`, generated by the pipeline rather than compiled by hand.

**Cells changed** counts cells whose value the pipeline rewrote. **Rows flagged** counts rows
where a condition was recorded without the value being altered — a missing or zero price is
reported, never filled or removed. The two are kept separate because conflating them would
overstate how much was changed.

| Table | Column | Cells changed | Rows flagged | Rows excluded | Problem ID |
| --- | --- | --- | --- | --- | --- |
| Menu | `currency` | 5,236 | 0 | 0 | P8 |
| Menu | `date` | 5,236 (dropped after split) | 0 | 0 | P6, P7 |
| Menu | `year`, `month`, `day` | 15,708 (5,236 × 3, created) | 0 | 0 | P6, P7 |
| Menu | `status` | 5,236 (column dropped) | 0 | 0 | — |
| Menu | `id` | 0 | 0 | 0 | — |
| MenuPage | `id`, `menu_id` | 0 | 0 | 0 | — |
| Dish | `name` | 383,289 | 647 marked `UNKNOWN` | 0 | P1, P2, P3 |
| Dish | `lowest_price` | 315,775 formatted · 767 capped | 222,566 zero or negative | 0 | P5 |
| Dish | `highest_price` | 320,522 formatted · 882 capped | 218,014 zero or negative | 0 | P5 |
| Dish | `id` | 0 | 0 | 0 | — |
| MenuItem | `price` | 508,661 formatted · 4,251 capped | 445,858 missing · 367 zero or negative | 0 | P4, P5 |
| MenuItem | `high_price` | 65,709 formatted · 459 capped | 1,240,821 missing · 7 zero or negative | 0 | P4, P5 |
| MenuItem | `dish_id` | 0 | 239 absent | 0 | — |
| MenuItem | (row level) | — | — | **236** | P4, P5 |

**Row counts through the pipeline.** Only MenuItem loses rows, and only 236 of them:

| Table | OpenRefine export | Load-ready output | Removed |
| --- | --- | --- | --- |
| Menu | 5,236 | 5,236 | 0 |
| MenuPage | 66,937 | 66,937 | 0 |
| Dish | 394,297 | 394,297 | 0 |
| MenuItem | 1,332,668 | 1,332,432 | 236 |

**Dish name normalization, by operation.** These overlap — one name can be uppercased *and* have
accents folded — so they sum to more than the 383,289 names changed:

| Operation | Names |
| --- | --- |
| uppercased | 380,613 |
| separators converted to spaces | 67,294 |
| whitespace collapsed | 62,095 |
| punctuation deleted | 40,806 |
| `&` expanded to `AND` | 11,029 |
| accents folded | 9,418 |
| marked `UNKNOWN` | 647 |
| typographic quotes normalized | 142 |

**Price outlier capping (P5), by column.** Values above the 99.5th percentile were capped at that
percentile. No row was removed:

| Column | Threshold | Values capped |
| --- | --- | --- |
| `MenuItem.price` | 300.00 | 4,251 |
| `MenuItem.high_price` | 260.00 | 459 |
| `Dish.highest_price` | 79.79 | 882 |
| `Dish.lowest_price` | 50.00 | 767 |

**Headline effect on P1/P3:** distinct dish names fell from **390,201 to 349,480**, so 40,721
name variants merged into an existing spelling. That is the aggregation improvement U1 depends on,
measured rather than asserted.

**Three columns report a measured zero**, which we record rather than omit: no identifier in any
table needed rewriting, and no price value in any of the four price columns was non-numeric. Both
are results — the OpenRefine export was already clean in those respects — and both are checks the
pipeline still performs on every run.

### 2.2 IC-violation report, before vs. after (10 pts)  [CharleneKhun] [MadalynKillian] [PoLin]

_Denial-constraint answers on D and on D′. Source:
`validation_ic_results.csv`, `validation_ind_results.csv`, `validation_fd_results.csv`._

| Constraint | Type | Violations in D | Violations in D′ |
| --- | --- | --- | --- |

Also report Q_U1 before/after (queries in [use-cases.md](use-cases.md)): running Q on D must
give an incorrect/misleading answer, and on D′ a correct one.

## 3. Workflow model

### 3.1 Outer workflow W1 (10 pts)  [Team]

_Key inputs, outputs, steps, and dependencies; explain the design and tool choices._
Artifacts in [../workflow/](../workflow/). Tool selection is also documented in
[Appendix A](#appendix-a--tool-use-and-ai-assistance).

### 3.2 Inner cleaning workflow W2 (10 pts)  [PoLin]

W2 models the Python/pandas cleaning in detail. The pipeline source carries **YesWorkflow
annotations**, so the graph is generated from the code that runs rather than drawn separately —
which means it cannot drift from the implementation:

```powershell
$src = 'workflow/W2_frame.yw',
       'src/clean_menu.py','src/clean_menu_page.py','src/clean_dish.py','src/clean_menu_item.py',
       'src/run_pipeline.py'
java -jar yesworkflow.jar graph @src -c "extract.comment=#" -c graph.view=combined > workflow\W2.gv
dot -Tpng workflow\W2.gv -o workflow\W2.png
```

Both the comment-delimiter flag and the file order are load-bearing; see
[../workflow/README.md](../workflow/README.md) for why, and §A.2.8 for how we found out.

**23 annotated blocks** across the frame file and five pipeline modules. Three annotation kinds
carry the model:

- `@in` / `@out` name the data flowing between stages, each bound to a real file path with
  `@uri`. Adjacent stages connect because one's `@out` name matches the next one's `@in`.
- `@param` marks the configuration values a stage consumes — the currency map, the plausible
  year range, the dish-name character rules. These render distinctly from data, so the graph
  shows which rules are driven by which constants.
- `@desc` names the files each stage writes, so a node in the graph points at the artifact it
  produced.

**What the graph shows that a prose description does not:** four independent tracks of different
lengths. MenuPage runs one stage; Menu runs four. The chains never join, because nothing in this
pipeline joins across tables — that happens in SQL. The asymmetry is the substantive claim of the
model: each table is processed according to the column types it actually has, not put through a
uniform sequence.

**Generated artifacts.** The top-level graph shows the four chains as sub-workflow nodes; a
per-table graph expands each one's stages:

| File | Contents | Nodes / edges |
| --- | --- | --- |
| `workflow/W2_frame.yw` | Outer frame: opens the workflow, declares its external ports | — |
| `workflow/W2.gv` | Top level: four table chains + the cleaning-log rollup | 21 / 24 |
| `workflow/W2_clean_menu.gv` | Menu's four stages | 16 / 18 |
| `workflow/W2_clean_dish.gv` | Dish's four stages | 16 / 23 |
| `workflow/W2_clean_menu_item.gv` | MenuItem's four stages, including the omit split | 17 / 21 |
| `workflow/W2_clean_menu_page.gv` | MenuPage's single stage | 10 / 8 |

Each is rendered to **PNG** beside its `.gv` source. The top level uses a
left-to-right layout; the per-table graphs use top-to-bottom, because a linear five-stage chain
laid out horizontally is 6,000 pixels wide and unreadable on a page.

**Annotation correctness was checked while the annotations were being written**, using a linter we
wrote for the purpose ([`src/lint_workflow.py`](../src/lint_workflow.py)). YesWorkflow exits
successfully on several mistakes that silently produce a wrong graph, so the linter verifies that
blocks are balanced, that every input has a producing output, that every parameter resolves to a
real constant in `src/config.py`, that every file reference exists, and that none of YesWorkflow's
keywords appears in ordinary prose. It is a development aid, not part of reproducing the data set.

It earned its keep before YesWorkflow was even installed: all four chains originally ended in an
output that nothing consumed, because the final write step had no block of its own — each chain
would have rendered disconnected from its own output, with no error from YesWorkflow.

**What the graphs show.** The top-level view is four parallel tracks — one per source table — each
running from its OpenRefine export through its cleaning block to its load-ready CSV, with the four
outputs converging on the cleaning-log rollup and MenuItem carrying a second output for its omitted
rows. The per-table views expand each block: Menu's shows five sequential stages with
`NULL_LIKE_VALUES`, `MIN_PLAUSIBLE_YEAR`, `MAX_PLAUSIBLE_YEAR`, `DATE_PART_COLUMNS`,
`CURRENCY_MAP`, and `PROVENANCE_COLUMNS` attached as parameter nodes to the specific stages that
consume them; MenuPage's shows one. That contrast is the model's substantive claim.

## 4. Conclusions & summary (10 pts)  [Team]

_Summary, lessons learned, problems encountered, next steps for implementing U1._

### Contributions

| Member | Contribution |
| --- | --- |
| Madalyn Killian | |
| Po Lin | |
| Charlene Khun | |

### Plan vs. actual

_Compare against [phase2-plan.md](phase2-plan.md): which steps executed as planned, what
changed, and why._

## 5. Supplementary materials (10 pts)  [Team]

See [deliverables-checklist.md](deliverables-checklist.md).

---

## Appendix A — Tool use and AI assistance  [Team]

The project instructions require this. On tools beyond those used in class, they state:

> "Or maybe you find a new way to use an LLM (e.g., ChatGPT). In all these cases your report
> will have to include sufficient documentation about how you used these tools."

Our Phase-I plan also anticipated "AI-assisted code generation where appropriate and permitted
by course guidelines" (S3) and listed ChatGPT among the S2 profiling tools, so this appendix
covers both the repository setup and any AI use during the cleaning work itself.

### A.1 Repository scaffolding

**Tool:** Claude Code (Anthropic Claude Opus), July 2026.

**What we asked it to do.** After Phase-I was submitted, we asked it to read the course
project instructions and our Phase-I report and lay out a repository structure for Phase-II.
It produced:

- the directory layout (`data/`, `src/`, `sql/`, `openrefine/`, `workflow/`, `docs/`,
  `deliverables/`) with a README in each explaining what belongs there, plus `.gitignore` and
  `requirements.txt`;
- our own Phase-I report content reorganized from the submitted document into per-topic
  markdown files (dataset description, use cases, data quality problems, Phase-II plan), so it
  could be revised during Phase-II rather than re-edited as one document. The data quality
  problems were given stable IDs (P1–P10) so cleaning rules and validation queries could cite
  them;
- our Phase-II task-division checklist split into one file per team member, with a search
  token (`[PoLin]`, `[CharleneKhun]`, `[MadalynKillian]`, `[Team]`) placed wherever a file
  needs someone's attention;
- empty templates for artifacts our checklist required but had no home for — the cleaning-rule
  catalog, the data dictionary, and the iteration log;
- comment-only stub files for each SQL script and Python module, stating the owner, the step,
  what the file must contain, and known pitfalls of the chosen tools.

**What it did not do.** No cleaning logic, SQL queries, profiling, cleaning rules, or analysis.
Every stub is comments and a `TODO` marker. Where it had begun drafting validation queries and
a profiling script, we had it remove them so the work would be ours; the same applied to
several design decisions it had filled in (the data dictionary field definitions, the
loop-stopping criteria, and the U1 query set), which we reset to blank for us to decide.

Two things it flagged that changed our plan, both recorded in
[Plan vs. actual](#plan-vs-actual):

1. Our Phase-I plan named MySQL, but our Phase-II task division assigned SQLite. We confirmed
   SQLite.
2. Our Phase-I task split assigned whole steps S1–S5 per member, while the Phase-II division
   splits by workflow step and tool, so all three of us work across S3–S5.

### A.2 AI assistance during the cleaning work  [Team]

**Tool:** Claude Code (Anthropic Claude Opus 5), July 2026, run locally against the repository.

Used across Step 4: profiling the data to decide what the cleaning rules should be, reorganizing
the `data/` tree for provenance tracking, writing the pipeline modules, generating the W2
workflow model, and rebuilding the whole data set from its inputs to verify reproducibility.
Cleaning decisions were made by us; the tool produced analysis and code against those decisions.
Where it disagreed with a decision it said so, and three of those objections changed the plan
(the currency-rescue idea in §A.2.8, the outlier method in §A.2.9, and the pre-created directories
in §A.2.2).

| Step | Tool | Used for | How the output was verified |
| --- | --- | --- | --- |
| 2 | Claude Code | Profiling scripts over the four raw CSVs — per-column blank/zero/non-numeric counts, year-range tails, currency cross-tabs, dish-name character census | Counts cross-checked against the preliminary OpenRefine facets. Three disagreements found and reconciled: `currency` distinct values (43 vs. our 39), `status = under review` (174 vs. our 167), `MenuItem.dish_id` blanks (241 vs. our 0) |
| 2 | Claude Code | Testing whether blank `Menu.currency` rows could be rescued by inferring location | Hypothesis rejected on the evidence it produced; re-verified with an independent join (menu-reported `dish_count`, total vs. priced items, orphan `menu_page_id` check) before we acted on it |
| 1 | Claude Code | Reorganizing `data/` into per-table `raw`/`interim`/`final` trees; moving 8 CSVs; rewriting `.gitignore` | Move script ran preflight assertions (every source present, no destination pre-existing) and compared byte sizes before and after each move; `git check-ignore` confirmed the new rules; file count on disk re-checked after untracking |
| 4 | Claude Code | Writing `src/config.py` — path objects, controlled vocabularies, dish-name character rules | Executed a check resolving every declared path against the filesystem, asserting each OpenRefine export's column shape, confirming no directory is created as a side effect, and spot-checking the log-tag and price formats |
| 4 | Claude Code | Writing `src/cleaning_utils.py` — the pure value-level cleaners each per-table module calls | Tested against real values taken from the profiling rather than invented ones; one fabrication bug found and fixed (a dish named `&` cleaned to `AND`). Re-run over all 394,297 dish names: no result outside the target charset, no empty results |
| 4 | Claude Code | Writing `src/provenance.py` — per-row log accumulation, cell-level change capture, stage snapshots, and the `cleaning_log.csv` rollup | Ran four real stages over `Menu_OR.csv` (5,236 rows) and checked the accumulated log, the change log contents, the column ordering, and that run directories appear only when a stage writes. Re-ran the sequence from scratch and compared SHA-256 hashes to confirm byte-identical output |
| 4 | Claude Code | Writing the four per-table cleaning modules and `src/run_pipeline.py`, each annotated for YesWorkflow | Each module run over its full export and its row counts checked against the input; one defect caught per module (see §A.2.6) |
| 4 | Claude Code | The price outlier rule — winsorizing the right tail, with the limit chosen by measuring candidates against the U1 metric | Thresholds confirmed against the maxima in the load-ready CSVs; row counts unchanged either side of the stage; 4,710 capped cells present in the change logs with before and after values |
| 4 | Claude Code | Clean-room rebuild: deleting all 37 generated files and 18 directories, then regenerating from the eight inputs | All 37 files reproduced byte-for-byte, verified by SHA-256 against a fingerprint taken before deletion |

Each task below records the instruction given, what came back, and how we checked it.

#### A.2.1 Profiling the raw data (Step 2)

> Review the project structure and the checklists to work out the scope of my portion. Profile
> the four raw CSVs with pandas to establish baseline row and column counts and to work out what
> the Python/pandas cleaning tasks should be — per-column missing, blank, zero, malformed and
> outlier counts across the U1 columns. Where a Phase-I assumption looks wrong, say so. Check
> the course instructions PDF for whether inferring location from the data is permitted.

Produced throwaway pandas scripts (not part of the pipeline) reporting baseline counts, blank
and zero-price rates, date-range tails, currency cross-tabs, and a dish-name character census.

We cross-checked its counts against the preliminary OpenRefine facets and found three disagreements:
`currency` distinct values (43 vs. our 39), `status = under review` (174 vs. our 167), and
`MenuItem.dish_id` blanks (241 vs. our 0). The `dish_id` figure was independently corroborated
by our Phase-I dataset description, which already recorded empty `dish_id` values.

#### A.2.2 Reorganizing the data tree (Step 1)

> Given my OpenRefine exports, reorganize `data/` so each source CSV has its own
> `raw`/`interim`/`final` tree, with one directory per cleaning function inside `interim` for
> provenance, and move the raw and OpenRefine files into it.

It first created the function directories up front. We rejected that: pre-created directories
have to be kept in sync with the code by hand, which makes adding a cleaning function a
two-place change. We had it move directory creation into the code so each function creates its
own run directory on first execution. It agreed and additionally dropped the numbering it had
applied to those directories, on the grounds that numbered directories have to be renumbered
whenever a stage is inserted — the same friction we were removing.

> Ignore the whole `data/` tree in git — the datasets go out over a shared drive instead.

Before making the change it reported that this was not merely a preference: `MenuItem.csv` is
113 MiB, above GitHub's 100 MiB per-file limit, so the push would have been rejected outright.
It also noted that the course instructions require the datasets to be shared via **Box** at
submission time, which is separate from whatever we use during development.

The move script ran preflight assertions (every source present, no destination pre-existing) and
compared byte sizes before and after each move; we confirmed the new ignore rules with
`git check-ignore` and re-counted the files on disk after untracking.

#### A.2.3 Pipeline configuration module (Step 4)

> Write the pipeline config module: path objects per table, a `Dollars → USD` currency map, the
> date-part columns, the dish-name character rules (uppercase ASCII alphanumerics plus
> apostrophe and comma; separators become spaces; `&` becomes AND; accents folded; non-Latin
> names marked UNKNOWN), and a per-row `log` column convention tagged `<column>:<operation>` so
> change counts can be reported per column.

Produced `src/config.py`. Two additions it argued for and we kept: an assertion of each
OpenRefine export's expected column shape, so that re-exporting with a renamed column fails
immediately rather than deep inside a cleaning function; and a `log_tag()` helper enforcing the
`<column>:<operation>` format, which is what makes the per-column change counts in §2.1
computable.

It proposed a `MIN_PRICED_ITEMS_PER_MENU` threshold, which we removed as premature.

Verified by executing a check that resolved every declared path against the filesystem, asserted
each export's column shape, confirmed no directory is created merely by referencing its path,
and spot-checked the log-tag and price formats.

#### A.2.4 Value-level cleaning functions (Step 4)

> Write the cleaning utilities — the pure value-level functions the per-table cleaners will call.

Produced `src/cleaning_utils.py`: `normalize_text`, `clean_int`, `clean_decimal_2dp`,
`split_iso_date`, `map_currency`, and `clean_dish_name`. Each returns the cleaned value together
with the list of operations that produced it, so the per-row `log` column is a byproduct of
cleaning rather than something reconstructed afterwards. It proposed the rule that an operation
is recorded only when it actually changed the value, on the grounds that a type coercion applied
uniformly would otherwise tag all 1.3M `MenuItem` rows identically and make the log useless.

We had it test the functions against real values drawn from the profiling rather than invented
ones. That run failed on one case: a dish named `"&"` was being cleaned to `"AND"`, because the
ampersand-to-word expansion ran before the check for symbol-only names — inventing a dish that
never appeared on any menu. It was corrected to detect symbol-only names before any
substitution. This class of name is problem P2 in our register.

Checked over the full column: 394,297 names processed, no result outside the target character
set, no empty result, 647 names marked `UNKNOWN`, and distinct names falling from 390,201 to
349,480 — that collapse is the P1/P3 near-duplicate merging we wanted.

#### A.2.5 Provenance module (Step 4)

> Write the provenance layer the per-table cleaners sit on: it should apply the value-level
> cleaners to columns, accumulate the per-row `log`, capture cell-level before/after changes,
> and write each stage's output directory. Row-level change logs for semantic transforms only —
> formatting-only work records counts instead. The cleaning functions create their own run
> directories, so directory creation belongs here.

Produced `src/provenance.py`. Each cleaning stage constructs a `StepRecorder`, which writes
three artifacts into `data/<table>/interim/func-<step>/`: the stage snapshot, a cell-level
change log, and a summary of counts per column and operation. The summaries are concatenated
into `data/reports/cleaning_log.csv`, which is the source for the change table in §2.1.

Two things it raised that we adopted. It moved the OpenRefine column-shape assertion into the
loader, so re-exporting from OpenRefine with a renamed column fails on load with a message
naming the file and the expected columns, rather than surfacing later as a confusing error
inside a cleaning function. And it wrote all CSVs with LF line endings and no timestamps, on the
grounds that our checklist requires the workflow be rerunnable — output that embeds a timestamp
cannot be diffed against a previous run to show it reproduced.

Verified by running four real stages over `Menu_OR.csv` (5,236 rows): identifiers coerced, date
split into year/month/day with the original `date` retained, currency mapped, `status` dropped.
We confirmed the accumulated log reads
`date:date_split;currency:currency_mapped;status:column_dropped`, that no run directory exists
until a stage writes one, that opting out of change recording suppresses the change file, and
that the change log records `Dollars → USD` for all 5,236 rows. We then re-ran the whole
sequence from scratch and compared SHA-256 hashes to confirm the output was byte-identical.

The identifier stage produced an empty summary, because the identifiers in the preliminary OpenRefine export
were already clean integers. We kept the stage rather than removing it: a measured no-op is
evidence, and §2.1 should report it as zero rather than omit it.

#### A.2.6 Per-table cleaning modules (Step 4)

> Write one cleaning module per source table, each calling the value-level cleaners through the
> provenance layer. Annotate each stage for YesWorkflow — inputs and outputs so the graph can be
> generated later, configuration constants marked as parameters, and the output filenames named
> in the stage description so a node in the graph points at the file it produced. Not every
> table runs the same stages; the graph should show that.

Written one at a time and reviewed before moving to the next.

**`src/clean_menu_page.py`** — a single stage, identifier coercion. MenuPage carries only `id`
and `menu_id`, so it has no dates, prices, text, or categoricals to clean, against Menu's four
stages. Run over the export: 66,937 rows in, 66,937 out, none dropped. The stage summary is
empty because the preliminary OpenRefine export already held clean integers — we kept the stage rather
than deleting it, so §2.1 can report a measured zero instead of omitting the column.

It declined to resolve dangling `menu_id` values in this module, on the grounds that inclusion
dependencies need a cross-table join and are Madalyn's Step 7; the module reports the distinct
`menu_id` count (19,816) so the two results can be reconciled rather than double-counted. It
also chose to flag unparseable identifiers rather than raise, since raising would stop the run
and hide the offending row, where our convention is to flag and carry every row forward.

**`src/clean_menu.py`** — four stages: identifiers, date split, currency mapping, status drop.
5,236 rows in and out. Observed year range 1851–2012, no unusable years, no identifiers that
failed to parse, and no currency outside our mapping — all measured rather than assumed.

It added a guard we had not asked for: the status column is dropped only after confirming it is
constant. The justification for dropping it is that the preliminary OpenRefine filter left only `complete`
rows, so if a later re-export widened that filter, dropping the column would destroy the
distinction with no trace. The module keeps the column and warns instead.

**`src/clean_dish.py`** — four stages: identifiers, name normalization, price decimals, outlier
capping. 394,297
rows in and out, in 10.7 seconds. Distinct names fell from 390,201 to 349,480, so **40,721 name
variants collapsed** — our P1/P3 evidence, quantified. 647 names were marked `UNKNOWN` (P2).
Prices confirmed the profiling exactly: 222,566 zero or negative `lowest_price` values, and
171,731 dishes (43.6%) usable as a price fallback with both prices positive.

The first run produced a 42 MiB change log, of which 380,613 of 383,289 rows recorded nothing
but a change in capitalization. We had it narrow the change log to rows where something beyond
uppercasing happened, which cut the file to 16 MiB while leaving every count in the summary
intact — the accent folds, ampersand expansions and `UNKNOWN` marks are now readable as
evidence instead of buried.

**`src/clean_menu_item.py`** — four stages: identifiers, price decimals, outlier capping, omit
check. 1,332,668
rows in, 1,332,432 out, 236 omitted and written to a separate file with the reason recorded on
each row. This is the only table the pipeline removes rows from.

We defined the omit rule as no `dish_id` **and** no positive price, since either one alone still
leaves a route to a price. The module reports the components separately so the narrowness is
visible: 239 rows have no `dish_id`, 446,210 have no positive price, and only 236 have both. The
445,974 rows with a dish but no price are explicitly kept for the step 4.6 fallback join, which
happens in SQL where Dish is available.

Checking the output caught a defect that would have reached Madalyn: `dish_id` was being written
as `1.0` rather than `1`. Because 239 rows have no `dish_id`, pandas had upcast the whole column
to floating point; `id` and `menu_page_id` escaped only because they contain no nulls. Written
that way, `MenuItem.dish_id` would not have matched `Dish.id` without a cast, breaking the price
fallback join. Fixed by using pandas' nullable integer type, and applied to every identifier
column in all four modules rather than only the one that failed.

#### A.2.7 Output layout correction (Step 4)

> The load-ready CSVs should not carry the provenance columns — SQLite has no use for
> `source_file`, `source_row_num`, or `log`. Put the load-ready output in a `cleaned` directory
> under `interim`, and remove the per-table `final` directories: `data/final/` belongs to the SQL
> workflow. Also drop the ISO date string from Menu now that year, month, and day exist.

Reviewing the first complete run showed the load-ready CSVs carrying three provenance columns
that no U1 query refers to. Stripping now happens at the final write only, so every upstream stage
snapshot still carries the full audit trail. The Menu date string is dropped through the same
logged mechanism as any other column removal, and the original remains visible one stage upstream
in `Menu_after_id-numeric.csv`, which keeps the derivation checkable.

Load-ready output after the correction:

| File | Columns |
| --- | --- |
| `Menu_cleaned.csv` | `id, currency, year, month, day` |
| `MenuPage_cleaned.csv` | `id, menu_id` |
| `Dish_cleaned.csv` | `id, name, lowest_price, highest_price` |
| `MenuItem_cleaned.csv` | `id, menu_page_id, price, high_price, dish_id` |

#### A.2.8 YesWorkflow model for W2 (Step 4)

> Annotate the pipeline for YesWorkflow — inputs, outputs, and configuration constants as
> parameters, with output filenames named in each stage description. The graph should show that
> not every table runs the same sequence.

Annotations were added to each cleaning module as it was written rather than retrofitted, so the
model derives from the code that runs. Because the YesWorkflow tool was not installed at the
time, it also wrote a linter for the annotations, which checks that blocks are balanced, that
every declared input has a producing output, that every parameter names a real constant in
`src/config.py`, and that every file reference exists. That linter caught a defect before the
tool was available: all four chains ended in an output nothing consumed, because the final write
step had no block of its own, so each chain would have rendered disconnected from its own output.

Installing YesWorkflow (0.2.1.2) then exposed two further problems that the tool reports no error
for, both now recorded in [../workflow/README.md](../workflow/README.md):

1. **Without `-c "extract.comment=#"`, YesWorkflow reads Python docstrings as the comment syntax**
   and finds no annotations at all, exiting successfully having produced nothing.
2. **Argument order is significant.** YesWorkflow concatenates its source arguments into a single
   stream, so a block opened in the first file is closed from the last. With the outer block
   opened inside `run_pipeline.py` it closed before the cleaning modules were read, and the tool
   produced a 21-block model rendered as a 6-node graph containing none of the cleaning chains.
   The outer frame was moved to `workflow/W2_frame.yw`, which is passed first.

A third mistake was self-inflicted and worth recording because it is easy to repeat: a comment
*explaining* the annotation structure mentioned the begin keyword in an ordinary sentence, and
YesWorkflow parsed that sentence as a real annotation, opening a duplicate block. Its matching is
loose enough that the keywords cannot appear in prose anywhere in the repository.

Final model: **21 nodes and 24 edges** at the top level, with per-table detail graphs of 16, 16,
17, and 10 nodes. Verified by checking that each generated file is well-formed DOT with balanced
braces, that the four table chains appear as sub-workflow nodes, and that each per-table graph
contains its own stages.

#### A.2.9 Price outlier rule (Step 4)

> Add the extreme-value check to the cleaning pipeline — it is more awkward to do in SQL.
> Reference the outlier method from our HW6 pandas assignment, keep the percentiles in
> `config.py`, and remove 3% of outliers from each tail.

Asked to implement a symmetric 3% trim with row removal, it measured the effect on the U1 metric
first and reported that the rule would break it. Trimming both tails moved the average price per
menu by **+8.7% for the cheapest quartile of menus and −32.0% for the priciest** — a distortion
that runs monotonically with price and would therefore compress the tier assignment U1 exists to
produce. The cause is that within dollar-denominated menus the median item is $0.40, so the 97th
percentile is only $4.00: trimming above it removes most of what makes an expensive menu
expensive, while the bottom trim deletes legitimate cheap items.

It also corrected an earlier claim of its own. It had previously described a `MenuItem.price` of
180,000 as a suspicious outlier; checking the menu behind it showed an **Italian Lire** menu at
the Grand Hotel Baglioni, where 180,000 is an ordinary price. Of the 1,183 items priced above
1,000, only **4 are dollar-denominated** — the rest are Lire, Francs, forint and Yen on menus our
currency filter already excludes.

On that evidence we changed the rule to **winsorization of the right tail only** — capping at a
percentile rather than deleting, and leaving the left tail alone. The limit was then chosen by
measuring candidates against the same tier test rather than by convention:

| Limit | Threshold | In-scope capped | cheapest | Q2 | Q3 | priciest |
| --- | --- | --- | --- | --- | --- | --- |
| 5.0% | $9 | 9,482 | −0.2% | −0.9% | −3.3% | −13.9% |
| 1.0% | $110 | 205 | 0.0% | 0.0% | 0.0% | −0.6% |
| **0.5%** | **$300** | **21** | **0.0%** | **0.0%** | **0.0%** | **−0.1%** |
| 0.1% | $1,500 | 2 | 0.0% | 0.0% | 0.0% | −0.0% |

0.5% caps 4,251 `MenuItem.price` values of which only 28 sit on dollar menus, so it targets the
currency artifacts almost exclusively while moving the priciest in-scope quartile by 0.1%. The
limit and the affected columns live in `src/config.py` with this evidence recorded beside them.

Verified by confirming the maxima in the load-ready CSVs match the thresholds, that the row count
is unchanged either side of the stage, that 4,710 capped cells appear in the change logs with
their before and after values, and that the capped rows carry a `winsorized` tag in the `log`
column.

#### A.2.10 Two provenance defects found by inventorying the output (Step 4)

> Write a section of the report describing the directory structure of the data directory.

Generating that description from the actual file inventory rather than from the intended design
surfaced two defects, neither of which the pipeline reported.

**A 65 MiB change log recording 1,332,668 changes that never happened.** `MenuItem`'s identifier
stage had produced a change file listing every row in the table, each showing an identical before
and after value and no operation. The cause is a pandas behaviour worth recording: calling
`Series.map()` on a nullable `Int64` column that contains `pd.NA` coerces the column to float
before invoking the function, so the integer 1 arrives as `1.0` and `pd.NA` arrives as
`float('nan')` — which fails an `is pd.NA` identity test and stringifies as `"nan"`. Every value
therefore compared unequal to its own original. Only `dish_id` was affected, because it is the
only identifier column containing nulls. The values written were always correct and the summary
counts derive from recorded operations rather than this comparison, so the defect was confined to
the change log; but that log is provenance evidence, and 1.3M false entries in it would have been
indefensible. Fixed by comparing through a vectorized string conversion that does not round-trip
through Python objects.

**Stale artifacts surviving a rerun.** Once the above was fixed the stage correctly produced no
change file — and the previous 65 MiB file remained on disk, because the writer only ever created
files and never removed one that had become obsolete. A directory could therefore describe a mix
of two different runs. Fixed by having each stage remove its own obsolete change file.

This also corrected a claim we had been making. Our determinism check compared only the four
load-ready CSVs, which passed throughout. Re-running the check across the whole tree — all 46
files — is what would have caught the stale file, and that is the check we now run.

#### A.2.11 Clean-room rebuild of the whole data set (Step 4)

> Remove every interim table we generated, leaving only the raw and OpenRefine CSVs. Run the
> pipeline end to end to regenerate them, regenerate the YesWorkflow graphs, and document each
> step.

The point of this run was to test a claim we had been making rather than to produce anything new.
Up to here the generated tree had accumulated across many sessions, so "the pipeline reproduces
the data" had never actually been demonstrated from nothing.

The sequence performed:

1. **Fingerprinted the existing output.** SHA-256 for each of the 37 generated files, recorded
   before anything was deleted, so the rebuild could be compared against it rather than merely
   inspected.
2. **Deleted every generated artifact** — 37 files (591 MiB) and 18 directories, keeping only the
   eight inputs (197 MiB): four raw CSVs and four OpenRefine exports. A preflight listed exactly
   what would be removed and confirmed all eight inputs were on the keep side before anything was
   deleted.
3. **Ran `python -m src.run_pipeline` from the empty tree.** 32.9 seconds. Every stage directory
   was created by the code as it ran; none had to exist beforehand.
4. **Compared the rebuilt tree against the fingerprint.** All 37 files reproduced
   **byte-for-byte identically**.
5. **Regenerated the workflow model from scratch** — deleted the ten existing graph artifacts and
   regenerated `W2.gv` plus the four per-table graphs and their PNG renders.

Row counts and every measured figure came out the same as the values reported in §2.1, which is
the result we wanted: the numbers in this report describe a data set that can be rebuilt from its
inputs, not one that exists only because of the order we happened to do things in.

**What we decided, not the tool.** The preliminary OpenRefine filtering that produced the
`*_OR.csv` exports was Po's own work, done in the OpenRefine UI — the tool never touched it. The
definitive OpenRefine profiling and cleaning is Charlene's and is outside the scope of this
appendix. Also ours: the directory scheme, the decision to keep the data out of git, the rule that
cleaning functions create their own run directories, and the choices among options it put to us —
how far to take the `UNKNOWN` rule for non-ASCII dish names, whether punctuation should be deleted
or converted to word boundaries, and whether the row-level change log should cover
formatting-only operations.

**What it flagged that changed our plan.** Two findings, both recorded in
[Plan vs. actual](#plan-vs-actual):

1. **Blank `Menu.currency` marks a menu that was never price-transcribed.** We had planned to
   recover those 11,089 menus — roughly tripling our sample — by inferring the country from
   `location` with an LLM and deriving the currency. Profiling showed the 11,089 blank-currency
   menus carry 361,600 transcribed items with **473 prices between them**, against 795,388
   prices on the 5,549 dollar-denominated menus. Currency is blank because there was nothing to
   denominate, so a correct currency label would have recovered no usable menu. We dropped the
   idea. It also showed the fallback our Phase-I plan relied on is narrower than assumed: about
   81% of items lacking a price sit on menus that were never price-transcribed at all.
2. **A column identity error in our own notes.** We had been treating `Menu.location` as the
   geographic field; it holds the venue name (`Hotel Eastman`), while `Menu.place` holds the
   geography (`HOT SPRINGS, AR`).

It also reported that the preliminary OpenRefine export had dropped 58 `MenuItem` rows that Po's summary to
the team did not mention, and that `Menu_OR.csv` contains only `Dollars` despite our summary
describing a `Dollars`-or-`Cents` filter.

**Verification standard applied.** No count in this report is quoted from the tool alone. Every
figure that reached a cleaning rule was reproduced either by the preliminary OpenRefine facets or by a
second, independently written check. The blank-currency finding above rests on a single pandas
join, so it is re-run in SQL once staging is loaded (see §2.2).

### A.3 Other tools

Tools used beyond the course toolset of RegEx, OpenRefine, Datalog/Logica, SQL, and Python. The
instructions require these to be documented.

| Tool | Version | Used for | Notes |
| --- | --- | --- | --- |
| **YesWorkflow** | 0.2.1.2 | Generating the W2 inner workflow model from annotations embedded in the pipeline source | Named in the project instructions as an option for the workflow model. Not a Python package — a Java jar, run as `java -jar`. Requires `-c "extract.comment=#"`, without which it silently finds no annotations in Python source |
| **Graphviz (`dot`)** | 15.1.0 | Rendering the generated `.gv` files to PDF | Only needed for the render; the `.gv` files themselves are produced by YesWorkflow. Its Windows installer does not add itself to PATH when installed non-interactively |
| **pandas** | see `requirements.txt` | The entire Step 4 cleaning pipeline | Within the course's Python toolset; noted for completeness since all type coercion, normalization, and provenance accounting run through it |
| **pypdf** | 6.14.2 | Reading the course instructions PDF while planning | Development-time only. Deliberately **not** in `requirements.txt` — the pipeline does not import it |
| **Git / GitHub** | — | Version control for code and documentation | The datasets are excluded: `MenuItem.csv` is 113 MiB, above GitHub's 100 MiB per-file limit, and the cleaned outputs are regenerated on every run. Raw and cleaned data are shared out of band and, at submission, via Box per the instructions |

**[OR2YW](https://github.com/idaks/OR2YWTool) — not yet applicable.** OR2YW derives a workflow
model from an OpenRefine operation history. The history it would consume is Charlene's Step 2
deliverable and is still in progress, so there is nothing for it to read yet. The W2 model
presented in §3.2 covers the Python/pandas cleaning; once the OpenRefine history exists, OR2YW is
the natural way to model that portion as a companion view, and `OpenRefineHistory.json` is
submitted regardless.
