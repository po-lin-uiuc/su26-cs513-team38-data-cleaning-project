# CS 513 — Phase-II Report (scaffold)  [Team]

**Team 38** — Charlene Khun (ckhun2@illinois.edu), Madalyn Killian (killian7@illinois.edu),
Po Lin (pohungl2@illinois.edu)

**Dataset:** NYPL *"What's on the Menu?"*

> Section headings follow the Phase-II rubric exactly. Fill each section as the work lands;
> do not restructure. Export to `deliverables/phase2/CS513-Team38-Phase2-Report.pdf`.

## Brief Overview of Dataset and Project  [CharleneKhun]

Our group is using the NYPL What's on the Menu dataset. This dataset consists of a large
collection of historical restaurant-menu records dating from the mid-1800s through the modern era,
covering locations around the world. The dataset is split into four different tables: Menu,
MenuPage, MenuItem, and Dish and tells us information such as what kinds of dishes are on menus,
their corresponding prices as well as what when the dishes originated.

The group project focuses on using the NYPL dataset to categorize menus into relative price
ranges, ranging from one to three dollar signs (in American dollars) within comparable historical
time periods. Before any analysis can be made, the data must be cleaned because it contains
missing or invalid prices, incomplete and impossible dates, inconsistent currencies, and
unreliable dish names. We will use OpenRefine, Python, and SQL to profile, clean, validate, and
prepare the records for reliable historical menu-price comparisons.

## Project Use Case  [CharleneKhun]

U1 / Main: Our main use case is to categorize menu price ranges ($, $$, $$$, $$$$) relative to the
distribution of menu prices within comparable time periods. In order to achieve this analysis, we
would need to restrict usable data to menus with usable dates and valid menu item prices. Data
cleaning is necessary because:

- Menu item prices may be missing, malformed or inconsistent
- Menu dates and currencies may be incomplete or inconsistent
- Menus with too few priced items may produce misleading averages
- Dish names will need to be cleaned/normalized due to odd/vague attribute values
- Dish and menu items' prices would need to be inferred due to potentially missing prices between
  tables

We aim to get our data to a state where we are able to compare menus and their average dish prices
grouped by similar time periods, as well as identify most/least expensive menus within those time
periods.

> **should include…** — the overview says "ranging from one to three dollar signs" while the use
> case immediately below says `$, $$, $$$, $$$$`. Pick one and make both agree; the Step 9
> checklist and the final tables assume four tiers.
>
> - state the tier count once, in the overview, and let the use case reference it
> - if four tiers, correct "one to three dollar signs" to "one to four"
> - name the grouping unit for "comparable time periods" — decade, quarter-century, or something
>   else — since every U1 number depends on it and no section currently defines it
> - state the U1 population size the cleaning actually yields (5,236 menus) so the reader knows
>   the scale being described before §1.1 walks through the filters

## Data Quality Problems (P1–P10)

Ten data quality problems shape everything this report describes. Each has a short name and a
stable ID, and the rest of the report cites those IDs so that every cleaning rule, validation
query, and before/after count traces back to a specific documented problem rather than to a
general claim that the data was dirty.

| ID | Problem | Where | Why it matters for U1 |
| --- | --- | --- | --- |
| P1 | **Dish-name variants** — the same dish written many ways, differing in punctuation, capitalization, or word order | `Dish.name` | Identical dishes split into separate categories, degrading grouping |
| P2 | **Non-name dish names** — values that are entirely numbers or isolated symbols | `Dish.name` | Transcription artifacts rather than menu items; no analytic value |
| P3 | **Dish-name misspellings** — `Cafee`/`Cofee`/`Kafee` for coffee, `The`/`Thee` for tea | `Dish.name` | Duplicate categories reduce aggregation quality |
| P4 | **Missing prices** — the cell is blank, so no price was ever recorded | `MenuItem.price`, `high_price`, `Dish.lowest_price`, `highest_price` | An absent observation. Counting it as anything shrinks or distorts the usable sample |
| P5 | **Zero and implausible prices** — a value is recorded, but it is `0.00` or an extreme outlier | the same four price columns | A recorded `0.00` lowers menu averages; an extreme value pulls a menu into the wrong price tier |
| P6 | **Impossible dates** — typo'd or nonsensical years such as `1091`, `0190`, `2928` | `Menu.date` | Places a menu in the wrong historical period, corrupting the comparison group |
| P7 | **Missing dates** — the date is blank | `Menu.date` | An undated menu belongs to no chronological group and cannot participate in U1 at all |
| P8 | **Ambiguous currency** — the currency field is empty, and where present spans many distinct currencies | `Menu.currency`, `Menu.currency_symbol` | Identical numeric values represent different purchasing power, so prices are not comparable |
| P9 | **Impossible dish-lifespan years** — values such as `0`, `1`, or `2928` | `Dish.first_appeared`, `Dish.last_appeared` | Corrupts any time-period grouping derived from how long a dish was served |
| P10 | **Ambiguous locations** — broad or unidentifiable place values, including ship names and `New York` (city or state?) | `Menu.place` and related location fields | Blocks locality-based analysis; the reason U2 was ruled out |

**P4 and P5 are kept strictly separate throughout**, because they call for opposite treatment: a
blank price is an absent observation and must not be counted, while a zero is a recorded value
that may be either a genuine price or a transcription error. Collapsing the two — which pandas'
default type inference does silently — would deflate every menu average. §1.1-C explains how the
pipeline preserves the distinction.

P9 and P10 are documented but not acted on. `Dish.first_appeared` and `last_appeared` are outside
the column scope U1 needs, and P10 is the reason the U2 use case was ruled out rather than a
problem this cleaning attempts to fix.

## 1. Description of data cleaning performed

We cleaned the data in three layers using OpenRefine, Python/pandas, and SQLite. Each tool had a separate role: OpenRefine handled the initial profiling and scope reduction, Python applied repeatable value-level transformations, and SQLite checked the cleaned data against our relational constraints.

### 1.1 High-level cleaning steps (20 pts)  [PoLin] [CharleneKhun] [MadalynKillian]

The work was divided across the team: Charlene handled OpenRefine profiling and scope filtering (§1.1-B), Po built the Python/pandas cleaning pipeline (§1.1-C), and Madalyn handled SQL validation (§1.1-E). Each pass writes a new output for the next step and never overwrites its input. Python and SQL development started from a preliminary OpenRefine export so the team could work in parallel. When the OpenRefine export changes, the Python pipeline must be rerun, but that cost is low because the pipeline is deterministic and reproduces the same output byte-for-byte. We compare this parallel workflow against the original sequential plan in [Plan vs. actual](#plan-vs-actual).

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

**Tracing a table's history.** Each `func-<step>/` directory records one cleaning stage. Each cleaning
function writes a *complete* snapshot of the table as it stood when that function finished, so
the effect of any single rule comes from diffing two adjacent directories — no rule's effect
must be inferred. Each stage produces up to three levels of detail:

| File | Answers |
| --- | --- |
| `<Name>_after_<step>.csv` | What did the whole table look like after this rule? |
| `<Name>_changes_<step>.csv` | Which individual cells changed, and from what to what? |
| `<Name>_summary_<step>.csv` | How many rows did each operation affect, per column? |

We skip the change file for formatting-only rules because a row-level record of two-decimal
padding would be larger than the data and does not add anything beyond the summary. `MenuItem`'s
omit stage additionally writes `MenuItem_before_omit-check.csv` and `MenuItem_omitted.csv`, so
the excluded rows can be inspected on their own.

**The code creates stage directories at runtime** instead of requiring them in advance. Adding a cleaning rule
only requires one change — write the function; its directory appears on the next run — and a
deleted rule leaves no empty directory behind.

**The number of stage directories differs per table**, because each table runs only the rules its
column types require. This is intentional and is what the W2 model (§3.2) depicts:

| Table | Stages | Chain |
| --- | --- | --- |
| MenuPage | 1 | `id-numeric` |
| Menu | 4 | `id-numeric` → `date-split` → `currency-map` → `drop-status` |
| Dish | 4 | `id-numeric` → `dish-name` → `price-decimal` → `price-outlier` |
| MenuItem | 4 | `id-numeric` → `price-decimal` → `price-outlier` → `omit-check` |

**Submitted files.** 46 files, 788 MiB. Only **8 of them are inputs**: the four raw CSVs (146 MiB) and
the four OpenRefine exports (51 MiB). The other 37 files (591 MiB) and all 18 of their directories
are produced by the pipeline.

**Rebuilding the data set.** With the eight input files in place:

```powershell
python -m src.run_pipeline     # rebuilds every generated file, ~33 seconds
```

**We verified this from an empty generated-data tree.** We deleted all 37 generated files
and all 18 generated directories, leaving only the eight inputs, and re-ran the pipeline. Every
one of the 37 files was reproduced **byte-for-byte identically**, confirmed by comparing SHA-256
hashes recorded before the deletion against the rebuilt tree. Nothing in the generated data
depends on run history, on a partially populated directory, or on the order in which stages were
first written — this is what makes the `func-<step>/` snapshots usable as evidence rather than
as a record of one particular session. The rebuild is deterministic for two reasons: no artifact
contains a timestamp, and each stage rewrites its own outputs and deletes any of its own files
that a run no longer produces.

#### B. Open Refine  [CharleneKhun]

Step 1 **Selecting only the columns needed for U1**:
In OpenRefine, we reduced each table to the attributes needed for the historical menu-price
analysis. For Dish.csv we kept it limited to the following variables: ID, name, lowest_price, and
highest_price. For MenuItem.csv, we kept the variables id, menu_page_id, price, high_price, and
dish_id. Next for MenuPage.csv, we kept the id and menu_id. Lastly, for Menu we kept the id, date,
currency, and status. Modifying the table this way helped us remove unrelated descriptive fields
and made the datasets easier to inspect, process, and export. In addition, it also preserved the
identifiers needed to connect MenuItem to MenuPage, MenuPage to Menu, and MenuItem to Dish. Having
this reduction did not necessarily require us to calculate price ranges since unused columns would
not change the results. However, this step was still useful because it reduced unnecessary
complexity, lowered the amount of data carried into later stages, and made the OpenRefine workflow
more focused on U1.

Step 2 **Standardizing data types**:
We converted the identifier fields (ID fields) in Dish.csv, MenuItem.csv, and MenuPage.csv to
numeric values. We also converted the relevant price fields to numeric values as well. Menu dates
were standardized as date-time values in a consistent ISO 8601 format, while the currency and
status remained strings. This step was required for U1 because numeric prices are necessary to
calculate menu averages and assign menus to the different dollar sign groups. Consistent
identifier types are also necessary for connecting records across the four tables. Furthermore,
properly formatted dates allow menus to be grouped into comparable historical periods. Without
standardized types, values could be treated as text, joins could fail, and calculations or
chronological groupings could produce errors.

Step 3 **Handling blank Dish price values**:
In Dish.csv, records with blank values in both lowest_price and highest_price were excluded from
the OpenRefine output. We only need the dish price information when a MenuItem.csv does not
contain a usable price and we can use its corresponding dish prices as a backup. This step
directly supports U1 because a dish with no recorded price (low or high) cannot provide a valid
fallback price.
Keeping such rows could possibly skew the analysis and create the false impression that additional
menu items had usable pricing information. Therefore, excluding these records ensures that the
fallback table contains only dishes with at least one valid price that can be used to estimate a
missing MenuItem price.

Step 4 **Retaining blank MenuItem prices for later fallback processing**:
In contrast to the records in Dish.csv, records in MenuItem.csv were not automatically removed
when its corresponding price or high price was blank. These records were left as is because their
dish ID could connect them to a Dish record that has a valid lowest price or highest price. This
decision was required for U1 because immediately removing every MenuItem with a blank price would
unnecessarily reduce the dataset. A point to note is that a missing MenuItem price does not always
mean that the item has no recoverable price. The records in Dish.csv may still provide one.
Preserving these records allows subsequent steps in Python and SQL stages to apply the project's
price-fallback rules without OpenRefine prematurely getting rid of potentially useful data.

Step 5 **Preserving and standardizing the MenuPage relationship table**:
As mentioned in Step 1 and Step 2, for MenuPage.csv, we kept id and menu id and converted both
fields to numeric values. No null values were found in these selected columns. MenuPage
essentially connects MenuItem.csv and Menu.csv, since a menu item references a menu page rather
than directly referencing a menu.
This step was required for U1 because menu-item prices must eventually be grouped by their
corresponding menus. Even though MenuPage contains no pricing information itself, the preservation
of id and menu id is essential for calculating each menu's average item price and assigning the
menu to a relative price category.

Step 6 **Restricting the Menu table to comparable currencies**:
The data in Menu.csv was filtered to records where their currency value matched "Dollars" or
"Cents." Records in other currencies and records with missing currency information were not
included in the OpenRefine output. The currency symbol column was also removed because it did not
provide additional useful information for our U1 statement case. Also, we noticed when the
currency was null, currency_symbol was also null. This filtering was required for U1 because
prices expressed in different currencies cannot be directly compared as though they share the same
unit. The project could theoretically convert historical currencies, but doing so would require
outside exchange rate and historical economic data. Thus, it was outside the scope of U1 and was
identified as more appropriate for the "never enough" use case. Restricting the dataset to dollar
and cent denominated menus therefore provides a more comparable population without introducing
unverifiable assumptions.

Step 7 **Filtering menus by completion status**:
We kept only records whose menu status was "complete," which removed approximately 76 records.
This step supports U1 because an incomplete menu may contain only part of its original list of
items. Calculating an average price from an incomplete menu could produce a misrepresentation of
that menu's price range / category (one to three dollar signs). For instance, a menu missing
several expensive dishes could be classified as a less expensive restaurant than it actually was.
Restricting our analysis to only complete menus improves consistency among the menus being
compared. Although completion status does not guarantee perfect data quality, it is a reasonable
quality condition for deciding whether a menu contains enough information to support price
classification.

Step 8 **Cleaning and filtering menu dates**:
The Menu date field was inspected and filtered in OpenRefine. Blank dates, uninterpretable as
dates, and outliers were removed. This included 237 blank dates, 23 non-date values, and one
extreme outlier, resulting in a usable date range from 1850 through 2012. This step was required
for U1 because the use case compares menu prices within similar historical periods. A menu without
a valid date cannot be placed into a chronological group, and an impossible date could place the
menu in the wrong period and distort / inflate comparisons.

Step 9 **Profiling dish-name inconsistencies with clustering**:
OpenRefine's clustering functions were used to inspect inconsistent dish names, including
differences such as capitalization, punctuation, spelling inconsistencies. The profiling revealed
examples such as multiple representations of broiled chicken, roast beef, coffee, and tea, as well
as numeric or symbol-only dish names. This step was not ultimately required for our U1 case
because menus are classified using their numerical prices and dates rather than by grouping dishes
according to standardized names. Merging historical dish names could possibly also introduce
incorrect assumptions because many names are ambiguous or incomplete. Nevertheless, this profiling
was still useful because it documented an important limitation of the dataset. It also
demonstrated OpenRefine's ability to detect duplicate textual categories. These findings helped
justify our group's decision to focus U1 on numerical attributes rather than relying on
inconsistent dish names.

Takeaway:
Overall, the OpenRefine work served both as an initial cleaning stage as well as a profiling stage.
The steps involving prices, identifiers, dates, currencies, menu status, and table relationships
were directly required to produce a comparable set of historical menus for U1.
Column reduction and dish-name clustering were not strictly necessary for the final calculations.
However, they simplified the workflow, documented data limitations, and provided evidence for the
cleaning decisions implemented in the later Python and SQL stages.

> **should include…** — the nine steps were verified against the delivered `*_OR.csv` files, and
> the whole Menu chain reconciles: applying `currency` = Dollars, `status` = complete, non-blank
> `date`, and dropping the single year-2928 menu reproduces `Menu_OR.csv` **row for row**. Steps 3
> and 7 match exactly (29,100 Dish rows; 76 menus removed by status). Two lines in Steps 6 and 8
> describe that chain incorrectly, and both are the same mistake:
>
> - **Step 6 says Cents was kept; the export has none.** `Menu_OR.csv` is 5,236 rows, zero
>   `Cents`. Raw has 24 Cents menus and 23 survive the status and date filters. The filter that
>   actually ran was Dollars-only. Either correct the step, or re-export including Cents — but
>   note that keeping Cents means comparing unconverted units, which Step 6 itself argues against
> - **Step 8's "23 non-date values" are those same 23 Cents menus.** They carry perfectly valid
>   dates (`1900-04-22`, `1901-05-13`, …) and were removed for currency, not for being
>   unparseable — no raw date fails to parse at all. The "one extreme outlier" is exactly right:
>   a single Dollars menu dated 2928. So the date step removed 236 blanks and 1 impossible year,
>   and the 23 belong to Step 6. The stated range also starts at 1850 where the export starts at
>   **1851**
> - **Step 9's conclusion conflicts with §1.2 and §2.1.** It says dish-name work "was not
>   ultimately required for our U1 case", but §1.2 rule R-5 rates it partly required and §2.1
>   reports 40,721 name variants collapsed as a headline result. Both positions are defensible —
>   clustering-based *merging* was declined while mechanical *normalization* was performed — but
>   the report currently states them as if they contradict. One sentence distinguishing the two
>   would resolve it
> - **Attribution and the Phase-I deviation.** This section replaced a passage stating that Po ran
>   a preliminary OpenRefine pass so that Steps 4–10 could start before Charlene's pass landed,
>   recorded as a deviation in Plan vs. actual. That deviation is now undocumented. Decide who
>   ran the pass that produced the delivered exports and restate it, then re-add the deviation
>   note if it still applies
>
> Also missing, and required by the shared checklist for every step: the inputs and outputs of each
> step, the operation-history filename (`OpenRefineHistory.json`) and where it lives, and the
> profiling screenshots kept as evidence.

#### C. Python/pandas type-based cleaning (Step 4)

We use thirteen column-type-specific functions across the four tables. We read every file as text
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

Each stage writes three machine-readable provenance artifacts:

- a **`log` column** on every row, accumulating `<column>:<operation>` tags across the whole
  chain. For example, one row's history can read
  `date:date_split;date:column_dropped;currency:currency_mapped;status:column_dropped`;
- a **change log** recording the before and after value of each modified cell with its source row
  number;
- a **stage summary** counting rows affected per column and operation, concatenated into
  `data/reports/cleaning_log.csv` — the source for §2.1-B.

`log`, `source_file`, and `source_row_num` stay in every stage snapshot but are
**stripped from the load-ready CSVs**, because they describe the cleaning process rather than the cleaned data, and no U1 query
refers to them.

Rerunning the pipeline from the OpenRefine exports produces byte-identical output — no artifact contains
a timestamp, and every stage overwrites its own directory rather than appending.

#### E. SQL validation of the cleaned data (Steps 5–7)

The four load-ready CSVs are loaded into SQLite as staging tables and checked by query. Validation
is intentionally **separate from cleaning**: pandas rewrites values, SQL asks whether the result is
internally consistent. Nothing in this layer modifies data — every check returns the rows that
violate it, so an empty result means the constraint holds and a non-empty one is a countable
finding rather than a silent repair.

Three families of check run against staging, each catching a different class of defect and each
owned by a different member:

| Family | Question it answers | File | Semantics | Execution |
| --- | --- | --- | --- | --- |
| **IC** — integrity & domain | Is each value individually legal? Is a price non-negative, a year in range, a status drawn from its controlled vocabulary? | `sql/03_validate_ic.sql` | `[CharleneKhun]` | `[MadalynKillian]` |
| **IND** — inclusion dependency | Does every foreign key point at a row that exists? These are the U1 join path: menu → page → item → dish | `sql/04_validate_ind.sql` | `[MadalynKillian]` | `[MadalynKillian]` |
| **FD** — functional dependency | Does one key ever carry two conflicting values? | `sql/05_validate_fd.sql` | `[PoLin]` | `[MadalynKillian]` |

The three are complementary rather than overlapping. An IC check reads one row at a time and
cannot see that two rows contradict each other. An FD check compares rows sharing a key but cannot
see that a key points nowhere. An IND check follows references but says nothing about the values
at either end. A defect invisible to all three is not caught by this layer at all, which is why
§2.1-B's cell-level change counts and this section are both reported.

_The remainder of this section is **Madalyn's** to write, covering the staging schema, the load,
and how the three validation files are actually run (Steps 5–8)._

> **should cover…**
>
> - **How blanks are loaded.** The cleaned CSVs distinguish a missing price from a zero price
>   (P4 vs P5), but a CSV cannot express NULL and SQLite's `.import` writes `''` for an empty
>   field. State which one `02_load_staging.sql` produces — `sql/05_validate_fd.sql` is written
>   against NULL and its expected counts shift if blanks arrive as `''`
> - **Whether staging tables are `STRICT`.** SQLite applies type affinity rather than enforcement,
>   so a non-STRICT `INTEGER` column will accept `'abc'`. Say which behaviour was chosen and why
> - **Which constraints are enforced at load vs. checked by query.** A load-time constraint gives
>   a failed insert; a query gives a countable violation, and Step 7 needs counts
> - **The run order and the outputs**, so the three `validation_*_results.csv` files can be traced
>   back to the commands that produced them
> - **Row-count reconciliation** between each cleaned CSV and its staging table, with any
>   discrepancy explained
> - **Why staging is separate from the final operational tables** (Step 9)
> - **Steps 8–10**: iterating on the violations, the final operational tables, and the export. The
>   price fallback of §4.6 of our plan is resolved there rather than in pandas, because it needs
>   MenuItem joined to Dish

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

Two rules were intentionally **not** applied here, and both decisions are load-bearing:

**Missing prices are not a reason to exclude a row.** 445,974 MenuItem rows have a `dish_id` but
no price of their own. Resolving those is the fallback chain in §4.6 of our plan, which needs
Dish values alongside MenuItem and so belongs in SQL. Dropping them in pandas would have
pre-empted a decision this stage cannot make, and would have removed a third of the table.

**No currency conversion is performed.** Converting non-dollar menus to USD needs historical
exchange rates, which are external data — and our Phase-I argument for U1 rests on no external
data being required. Non-dollar menus are excluded and the limitation stated rather than papered
over; §A.1.11 records the investigation behind this.

## 2. Document data quality changes

### 2.1 Summary table of changes (10 pts)  [CharleneKhun] [PoLin] [MadalynKillian]

The three cleaning stages are reported separately because each one changes the data in a different
way, and collapsing them would make it impossible to tell which stage is responsible for a given
number. OpenRefine removes **rows and columns** from scope; Python rewrites **cell values**; SQL
resolves and **excludes** rows that validation shows cannot be used. The stages chain, so each
one's output row count is the next one's input:

```
raw CSV  ──OpenRefine──▶  <Name>_OR.csv  ──Python──▶  <Name>_cleaned.csv  ──SQL──▶  final_*.csv
  §2.1-A: rows/columns cut    §2.1-B: cell values rewritten  §2.1-C: rows resolved or excluded
```

#### A. OpenRefine stage — scope reduction  [CharleneKhun]

The narrative for these filters is §1.1-B. Row and column counts below are measured from the
delivered `*_OR.csv` files:

| Table | Raw rows | Export rows | Rows removed | Raw cols | Export cols |
| --- | --- | --- | --- | --- | --- |
| Menu | 17,545 | 5,236 | **12,309** | 20 | 4 |
| MenuPage | 66,937 | 66,937 | 0 | 7 | 2 |
| MenuItem | 1,332,726 | 1,332,668 | 58 | 9 | 5 |
| Dish | 423,397 | 394,297 | **29,100** | 9 | 4 |

The Menu reduction reconciles exactly against the delivered export. Applying these four filters to
the raw file reproduces `Menu_OR.csv` **row for row** — the same 5,236 menu ids, not merely the
same count:

| Filter | Menus remaining | Removed |
| --- | --- | --- |
| raw | 17,545 | — |
| `currency` = Dollars | 5,549 | 11,996 |
| `status` = complete | 5,473 | 76 |
| non-blank `date` | 5,237 | 236 |
| year 2928 excluded | **5,236** | 1 |

> **should cover…**
>
> - **The currency filter is Dollars-only, not "Dollars or Cents".** §1.1-B Step 6 says Cents was
>   kept, but the export contains zero Cents menus. 24 exist in raw and 23 survive the status and
>   date filters, so the step as written does not describe the file that was produced
> - **Step 8's "23 non-date values" are those same 23 Cents menus.** They carry valid dates
>   (`1900-04-22`, `1901-05-13`, …) and were removed for currency, not for being unparseable. No
>   raw date fails to parse at all. The "one extreme outlier" is exactly right — a single Dollars
>   menu dated 2928. Correcting these two lines makes the whole chain reconcile
> - **58 MenuItem rows were removed**, which §1.1-B Step 4 does not account for — that step says
>   MenuItem rows were deliberately *not* removed. Identify the filter that dropped them
> - the 29,100 Dish rows removed are exactly the rows blank in **both** price fields, matching
>   Step 3 precisely — worth stating, since it is the cleanest number in the stage
> - cells changed *within* the retained rows, if OpenRefine edited any values rather than only
>   filtering rows — the counts above measure scope reduction only

#### B. Python/pandas stage — value cleaning  [PoLin]

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

#### C. SQL stage — resolution and exclusion  [MadalynKillian]

_Pending — **to be completed by Madalyn** (Steps 8–9). This stage changes the data in a way
neither of the other two can, because it is the first point at which the tables are joined._

| Change | Rows affected | Where |
| --- | --- | --- |
| Prices resolved by the fallback chain (§4.6 of the plan) | | `final_item` |
| Rows excluded as U1-ineligible | | `final_item` / `final_menu` |
| Rows repaired during Step 8 iteration | | staging |

> **should cover…**
>
> - **Prices recovered by the §4.6 fallback chain, broken down by `price_source`.** This is the largest
>   single change the SQL stage makes: 445,974 MenuItem rows carry a `dish_id` but no price of
>   their own, and resolving them needs MenuItem joined to Dish. Report how many each path
>   recovered and how many end as `no_valid_price`
> - **Rows excluded from the final tables and why**, kept separate from rows merely *flagged* — the
>   same distinction §2.1-B draws between "cells changed" and "rows flagged"
> - **Anything Step 8 iteration repaired**, with before/after counts per iteration, so the
>   iteration log and this table agree
> - the row counts into and out of the final tables, continuing the chain: `*_cleaned.csv` in,
>   `final_menu.csv` / `final_item.csv` out
> - note that FD-4 in §2.2-A feeds this section: the (page, dish) pairs where one duplicate line
>   carries a price and the other is blank are repairable here by letting the group take the known
>   price. How many there are comes out of Madalyn's FD run

### 2.2 IC-violation report, before vs. after (10 pts)  [CharleneKhun] [MadalynKillian] [PoLin]

Every check is stated as a denial constraint and returns the violating rows, so an empty result
means the constraint holds. Each is run twice — against **D**, staging loaded from the raw CSVs,
and against **D′**, staging loaded from the cleaned CSVs — because a violation count means nothing
without the count it started from.

The three families are defined by different members but **all of them are executed by Madalyn in
SQLite**, against the staging tables from Steps 5–6. The rule sets below are final; the violation
columns are filled in from the actual runs, and the analysis of what the numbers mean is written
once the runs have happened. Source files: `validation_ic_results.csv`,
`validation_ind_results.csv`, `validation_fd_results.csv`.

**One caveat applies to every result.** The D → D′ difference has *two* causes, not one: the
OpenRefine pass removed rows (17,545 → 5,236 menus, 423,397 → 394,297 dishes, 1,332,726 →
1,332,432 items), and Step 4 rewrote values. A count that falls has not necessarily been repaired
— it may simply be measured over fewer rows. Each subsection should say which it was, or say that
the two cannot be separated.

#### A. Functional dependencies (Step 7) — semantics [PoLin], executed [MadalynKillian]

Rules and semantics in [`../sql/05_validate_fd.sql`](../sql/05_validate_fd.sql), which also records
the counts measured on the cleaned CSVs before load as a regression baseline: if a run disagrees
with the header, check the load before re-reading the finding.

FD-1's left side is the same in both columns; its right side is the raw `currency, date, status`
in D and the cleaned `currency, year, month, day` in D′, since Step 4 split the date and dropped
`status`.

| Rule | Constraint | Type | Violations in D | Violations in D′ |
| --- | --- | --- | --- | --- |
| FD-1 | `Menu.id → currency, date parts` | FD | | |
| FD-2 | `MenuPage.id → menu_id` | FD | | |
| FD-3 | `MenuItem.id → menu_page_id, price, high_price, dish_id` | FD | | |
| FD-4 | `MenuItem.(menu_page_id, dish_id) → price` | FD | | |
| FD-5 | `Dish.id → name, lowest_price, highest_price` | FD | | |
| R-1 | `Dish.name → id` | report | | |
| R-2 | `MenuItem.dish_id → price` | report | | |
| R-3 | `MenuPage.menu_id → id` | report | | |

> **should cover…**
>
> - **FD-1/2/3/5 are key dependencies and FD-4 is not**, and they mean different things. A key
>   dependency that holds proves the load was clean and says nothing about the data; FD-4 is over
>   a non-key pair, so it is the only rule in this family that can find a transcription error.
>   Say which kind each result is before interpreting it
> - **the disposition of each violation** — repair, warning, or exclusion. The SQL file states
>   these per rule: FD-1/2/3/5 are repair-and-stop (a violation means the load or the cleaning is
>   wrong), FD-4 splits into a repairable half and an unresolvable half
> - **R-1/R-2/R-3 are reports, not violations.** They are expected to return large results by
>   design and must not be counted as constraint failures. R-1 measures duplicate dish dictionary
>   entries (P1/P3); R-2 is the basis for keeping dish-sourced prices out of U1; R-3 confirms
>   Menu:MenuPage is 1:N
> - **for FD-4, split the violations by kind** — pairs where one line is priced and the duplicate
>   is blank (repairable by taking the known price, and a direct input to §2.1-C's price
>   grouping) versus pairs carrying two different real prices (not resolvable from `D` at all)
> - **whether any FD count moved because of cleaning or only because of scope reduction.** Two
>   rules of thumb: MenuPage passes through the pipeline untouched, so its numbers should not
>   move at all; and price formatting can only merge conflicts, never create them
> - a note that `Dish.name → lowest_price, highest_price` was asserted, measured, and **withdrawn**
>   — requiring same-named dishes to agree on a price *range* is wrong under either reading of the
>   table, since merging duplicates would union the ranges rather than require equality

#### B. Integrity and domain constraints (Step 7) — semantics [CharleneKhun], executed [MadalynKillian]

Rules and semantics in [`../sql/03_validate_ic.sql`](../sql/03_validate_ic.sql), against the rule
catalog in [cleaning-rules.md](cleaning-rules.md).

| Rule | Constraint | Type | Violations in D | Violations in D′ |
| --- | --- | --- | --- | --- |
| IC-1 | | IC | | |
| IC-2 | | IC | | |

> **should cover…**
>
> - one row per rule, using the same rule IDs as the SQL file so a row here and a query there are
>   the same object
> - the expected coverage: menu eligibility, `year` validity and range, controlled domains for
>   `currency`, price non-negativity, and `highest_price ≥ lowest_price`
> - for each rule, whether zero violations are *required* or whether some are accepted, and why
> - two checks the pandas pipeline does **not** perform, so the gap is recorded rather than
>   implied: `highest_price < lowest_price` on `Dish` (profiling showed zero, but the pipeline
>   does not re-check it on every run), and duplicate primary-key detection — which FD-1/2/3/5
>   in §2.2-A cover as a by-product

#### C. Inclusion dependencies (Step 7) — semantics [MadalynKillian], executed [MadalynKillian]

Rules and semantics in [`../sql/04_validate_ind.sql`](../sql/04_validate_ind.sql).

| Rule | Constraint | Type | Violations in D | Violations in D′ |
| --- | --- | --- | --- | --- |
| IND-1 | `MenuPage.menu_id ⊆ Menu.id` | IND | | |
| IND-2 | `MenuItem.menu_page_id ⊆ MenuPage.id` | IND | | |
| IND-3 | non-null `MenuItem.dish_id ⊆ Dish.id` | IND | | |
| IND-4 | `final_item.menu_id ⊆ final_menu.menu_id` | IND | | |

> **should cover…**
>
> - why these matter: they are the U1 join path, so a violation drops items out of a menu's
>   average and can shift its price tier — it changes the answer, it is not cosmetic
> - **IND-1 is expected to fail by construction on D′.** The scope filter leaves Menu at 5,236
>   rows while MenuPage still carries all 66,937, so most pages point at a filtered-out menu.
>   That is the filter, not a data defect, and the count needs separating from genuine dangling
>   references or it will read as tens of thousands of violations
> - a missing *optional* reference (a NULL `dish_id`) is not a violation — report it separately
>   rather than folding it into the count
> - NULL semantics: use `NOT EXISTS` or a `LEFT JOIN ... IS NULL` anti-join, never
>   `NOT IN (subquery)` — one NULL in that subquery makes the predicate NULL for every row and a
>   broken constraint returns zero rows
> - one already-known result to reconcile rather than double-count: profiling found **0**
>   `MenuItem.menu_page_id` values absent from `MenuPage.id`, and `clean_menu_page.py` reports the
>   distinct `menu_id` count (19,816) for the same reason — Po *flags* a dangling reference in
>   pandas, Madalyn *counts* it in SQL, and the two must not surface as separate findings

#### D. Use-case query, before vs. after

_Pending Steps 8–9._

> **should cover…**
>
> - Q_U1 (queries in [use-cases.md](use-cases.md)) run against D and against D′, with both results
>   shown
> - why the D result is incorrect or misleading — the rubric asks for the difference, so the raw
>   answer has to be shown being wrong, not merely asserted to be
> - a statement that D′ is fit for U1, supported by the three tables above rather than separately
>   argued

## 3. Workflow model

### 3.1 Outer workflow W1 (10 pts)  [Team]

W1 is the end-to-end project: raw CSVs in, validated final tables out. W2 (§3.2) is not a separate
workflow but the **expansion of Step 4 inside it** — where W1 shows one cleaning box, W2 shows the
thirteen functions that box contains.

The organising principle is that **each step writes new files and never overwrites its input**, so
every arrow below is a file on disk rather than an in-memory handoff. That is what makes the
workflow restartable from any step and auditable after the fact: any output can be traced back to
the file and row it came from.

#### Steps, inputs, and outputs

| # | Step | Tool | Owner | Key inputs | Key outputs |
| --- | --- | --- | --- | --- | --- |
| 1 | Collect raw data, fix repository conventions | — | Team | The four NYPL CSVs | `data/<table>/raw/<Name>.csv` |
| 2 | Profile columns | OpenRefine | Charlene | `raw/<Name>.csv` | Profiling notes, baseline counts, `OpenRefineHistory.json` |
| 3 | Define cleaning rules from the profile | — | Charlene | Step 2 profile | [cleaning-rules.md](cleaning-rules.md), controlled reason codes |
| 3b | Scope filtering and export | OpenRefine | Charlene | `raw/<Name>.csv` | `interim/open-refine/<Name>_OR.csv` |
| 4 | Repeatable type-based cleaning (**W2**) | Python/pandas | Po | `<Name>_OR.csv`, `src/config.py` | `interim/func-<step>/`, `interim/cleaned/<Name>_cleaned.csv`, `data/reports/cleaning_log.csv` |
| 5 | Define staging schema | SQLite | Madalyn | Cleaned column shapes | `sql/01_schema_staging.sql`, `data/cs513_team38.sqlite` |
| 6 | Load cleaned CSVs into staging | SQLite | Madalyn | `<Name>_cleaned.csv` | `stg_menu`, `stg_menu_page`, `stg_menu_item`, `stg_dish` |
| 7 | Validate: IC, IND, FD | SQLite | Charlene / Madalyn / Po | Staging tables | `sql/03`–`05_validate_*.sql`, `data/reports/validation_*_results.csv` |
| 8 | Export violations, iterate | SQLite | Madalyn | Step 7 outputs | Iteration log, revised rules routed back to Steps 3–5 |
| 9 | Build final operational tables | SQLite | Po | Validated staging | `sql/06_schema_final.sql`, `data/final/final_menu.csv`, `final_item.csv` |
| 10 | Final export and provenance | — | Team | Everything above | `deliverables/phase2/`, `queries.txt`, `DataLinks.txt` |

Step 3b is listed separately from Step 3 because the two produce different artifacts — a rule
catalog and a filtered export — and Step 4 depends only on the second.

#### Dependencies

The spine is sequential — a step cannot start before the file it reads exists:

```
raw ──▶ 2/3 profile+rules ──▶ 3b OR export ──▶ 4 Python ──▶ 5/6 staging ──▶ 7 validate ──▶ 9 final ──▶ 10
                                                   ▲                            │
                                                   └──────── 8 iterate ─────────┘
```

Two features of the graph are worth stating because they are design decisions rather than
accidents:

**Step 8 is a cycle, not a step.** Validation results feed back into Steps 3, 4 and 5 — a rule
changes, the pipeline reruns, staging reloads, the checks run again. The workflow is therefore not
a DAG, and the report has to say what stops the loop (Step 8's stopping rationale) rather than
implying it runs once.

**Step 7 fans out and rejoins.** The three validation families are independent of one another and
were written by three people against the same staging tables, so they can run in any order; Step 8
consumes all three together. Nothing in Step 7 writes to the data — the checks only read — which
is what makes running them in parallel safe.

**The dependency that was deliberately broken.** In the Phase-I plan Step 4 waited on Step 3.
In practice Python and SQL development started against a preliminary OpenRefine export so all
three members could work concurrently, at the cost of rerunning Step 4 if the export changes. That
cost is low because the pipeline is deterministic and reproduces byte-identical output. This is
recorded in [Plan vs. actual](#plan-vs-actual).

#### Tool choices

| Tool | Used for | Why this tool |
| --- | --- | --- |
| **OpenRefine** | Steps 2, 3b — profiling and scope filtering | _[CharleneKhun] to complete_ |
| **Python/pandas** | Step 4 — type-based cleaning | The cleaning is per-column, rule-based, and has to run identically on 1.3M rows every time. pandas gives vectorized column operations and, critically, explicit control over type coercion: reading with `dtype=str` is what keeps a blank price distinguishable from a `0.00` price (P4 vs P5), a distinction that OpenRefine's import silently destroys and that SQL cannot recover once lost. It is also the only stage where a change log can be produced as a byproduct of the transformation rather than reconstructed afterwards |
| **SQLite** | Steps 5–9 — staging, validation, final tables | _[MadalynKillian] to complete_ |
| **YesWorkflow** | W2 model | The annotations live in the pipeline source, so the graph is generated from the code that runs and cannot drift from it. See §3.2 |

> **should cover…**
>
> - **the W1 diagram itself.** No artifact exists yet — `workflow/` currently holds only the W2
>   graphs. Decide the tool (YesWorkflow over a driver script, or a drawing tool) and who produces
>   it, then deliver both the source file and the rendered image, as the rubric requires for W1
> - **why OpenRefine for Steps 2 and 3b** — the profiling affordances that made it the right
>   choice (faceting, clustering, the operation history as a reproducible artifact), and its
>   limits as a scalable transformation tool
> - **why SQLite for Steps 5–9** — why validation belongs in a relational engine rather than in
>   pandas, and why staging is separate from the final operational tables
> - **the stopping criteria for the Step 8 loop**, which is the one part of W1 that cannot be read
>   off the file graph
> - whether [OR2YW](https://github.com/idaks/OR2YWTool) is used to derive a model of the
>   OpenRefine portion from `OpenRefineHistory.json` — if so it becomes a companion view to W2 and
>   should be named here

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
[../workflow/README.md](../workflow/README.md) for why, and §A.1.8 for how we found out.

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

Cleaning ran as three stages in three tools, and the division was not arbitrary: OpenRefine
reduced **scope**, Python rewrote **values**, and SQLite validated **relationships**. Each stage
does something the other two cannot. OpenRefine's faceting makes a problem visible faster than
writing code to look for it, but its import silently coerces types. Python can hold the
blank-versus-zero distinction that the whole price analysis rests on, but it cannot see across
tables. SQLite can follow a foreign key, but it never sees the raw string that was cleaned away.
Conclusions are drawn per stage below for that reason.

**The most important finding is not a dirtiness problem at all.** Of 17,545 menus, 11,089 have a
blank `currency` — and those menus carry 361,600 transcribed items with **473 prices between
them**. Currency is blank because nothing on the menu was ever price-transcribed, not because a
label was lost. No amount of cleaning recovers them. Combined with the currency, status and date
filters, U1's usable population is **5,236 menus, 29.8% of the file**. That is a *completeness*
ceiling inherited from the source, and it bounds every conclusion the project can reach. We would
rather state it plainly than present a cleaned dataset that implies more coverage than it has.

Against that ceiling, the cleaning did what U1 needs: 1.8M rows across four tables are now
typed consistently, joinable on every key, denominated in one currency, grouped by year, and
carrying a row-level record of everything that was changed.

### A. OpenRefine  [CharleneKhun]

> **should cover…**
>
> - what profiling found that changed the cleaning plan, and what it ruled out
> - which problems (P1–P10) OpenRefine was best placed to detect, and which it could not
> - the limits of clustering on 423K distinct dish names, and why merges were declined
> - lessons learned and problems encountered in this stage
> - what remains unresolved in the OpenRefine portion

### B. Python/pandas  [PoLin]

**What the stage produced.** Thirteen column-type-specific functions across four tables, running
end to end in about 33 seconds and reproducing byte-identical output from the same inputs. The
substantive changes: 40,721 dish-name variants collapsed into an existing spelling, 6,359 extreme
prices capped across the four price columns, every date split into year/month/day, currency mapped
to a single ISO code, and 236 rows removed — 0.018% of MenuItem, and the only deletions the
pipeline performs.

**Four decisions carried most of the weight, and each rejected an obvious alternative.**

*Read everything as text.* Letting pandas infer types would have merged a blank price and a `0.00`
price into the same value, collapsing two different data-quality problems (P4 and P5) into one and
silently deflating every menu average. This one line of configuration is the reason the rest of
the analysis is trustworthy, and it is invisible in the output.

*Flag, don't drop.* Every rule records what it found and keeps the row. 445,974 MenuItem rows have
a `dish_id` but no price of their own; dropping them would have removed a third of the table and
pre-empted a decision this stage cannot make, because resolving them needs Dish joined to
MenuItem. Deferring that to SQL kept the option open.

*Cap outliers rather than delete them.* We were asked to implement a symmetric 3% trim and
measured its effect on the U1 metric before adopting it: it moved the per-menu average by **+8.7%
for the cheapest quartile and −32.0% for the priciest**, compressing exactly the price range U1
exists to measure. Right-tail winsorization at 0.5% moves the priciest quartile by −0.1%. The
lesson generalises — a cleaning rule has to be measured against the use case, not against
convention.

*Make provenance a byproduct.* Each cleaner returns the operations it applied alongside the value,
so the `log` column, the change logs and the summary counts fall out of the transformation instead
of being reconstructed afterwards. Every number in §2.1-B is generated by the pipeline rather than
compiled by hand.

**Problems encountered.** Three are worth recording because each was invisible in the code and
only appeared when the output was checked.

- **A fabricated dish.** A dish named `&` was being cleaned to `AND` — the ampersand-to-word
  expansion ran before the check for symbol-only names, inventing a dish that appears on no menu.
  Order of operations in a normalization chain is semantics, not style.
- **`dish_id` written as `1.0`.** Because 239 rows have no `dish_id`, pandas upcast the column to
  float. `MenuItem.dish_id` would not have matched `Dish.id` without a cast, breaking the price
  fallback join before it was written. The in-memory frame looked correct; only the CSV showed it.
  Fixed with a nullable integer type applied to every identifier column, not just the one that
  failed.
- **1.3M change-log entries for changes that never happened.** `Series.map()` on a nullable `Int64`
  column containing `pd.NA` coerces to float, so every value compared unequal to its own original.
  The data written was always correct, but the provenance evidence was not — and provenance that
  cannot be trusted is worse than none.

The common thread: **verify the artifact, not the intention.** Each of these passed every check we
had until we inspected the file that was actually written. It is also why the determinism claim is
now tested across all 46 files rather than the four we originally compared — the narrower check
passed while a stale 65 MiB artifact sat in the tree.

**What this stage deliberately does not do.** Fallback pricing (§4.6 of our plan) needs a
cross-table join and belongs in SQL. Duplicate dish entries are reported, not merged: consolidating
them would rewrite the identifiers that 57% of MenuItem rows depend on, which is a schema
migration rather than a cleaning rule. And two checks named in our plan are absent from the
pipeline — `highest_price < lowest_price` on Dish, and duplicate primary-key detection — the first
because profiling showed zero violations, the second because the FD checks now cover it.

**Next steps for U1.** The cleaned tables are ready to join. What remains is downstream: resolve
the fallback prices in SQL, build `final_menu` and `final_item`, compute the per-menu average over
comparable periods, and assign tiers. The one open question this stage cannot answer is what
"comparable time period" should mean — decade, quarter-century, or something adaptive — and every
tier assignment depends on that choice.

### C. SQLite  [MadalynKillian]

> **should cover…**
>
> - what the staging and validation layer confirmed, and what it caught that earlier stages missed
> - whether the IC/IND/FD results show D′ is materially cleaner than D, with the counts from §2.2
> - how many iterations the Step 8 loop ran and what stopped it
> - which violations remain, and why they are acceptable for U1
> - lessons learned and problems encountered in this stage

### Contributions

| Member | Contribution |
| --- | --- |
| Madalyn Killian | |
| Po Lin | Step 1 repository and provenance conventions (`data/` tree, `source_file`/`source_row_num`, deterministic rebuild). Step 4 in full: `src/config.py`, `cleaning_utils.py`, `provenance.py`, the four per-table cleaning modules and `run_pipeline.py` — 13 cleaning functions, the change logs and `cleaning_log.csv`. Step 7 functional-dependency semantics in `sql/05_validate_fd.sql` (rules, NULL handling, dispositions, D/D′ baseline) for Madalyn to execute. Step 9 final operational tables. W2 workflow model (§3.2) including the YesWorkflow annotations and the annotation linter. Report §1.1-A/C/D, §1.2, §2.1-B, §2.2-A, §3.1, §3.2, §4-B |
| Charlene Khun | |

### Plan vs. actual

Compared against [phase2-plan.md](phase2-plan.md). The deviations below are the ones arising from
Steps 1, 4, 7-FD and 9; the OpenRefine and SQL stages add their own.

| Planned | What happened | Why |
| --- | --- | --- |
| Step 2 completes before Step 4 begins | Ran in parallel, with Python and SQL working from a preliminary OpenRefine export | Serial execution left two members idle. The cost — rerunning Step 4 if the export changes — is low because the pipeline is deterministic and reproduces byte-identical output |
| Recover blank-currency menus by inferring location, roughly tripling the sample | **Abandoned** | The 11,089 blank-currency menus carry 473 prices between them. Currency is blank because nothing was price-transcribed, so a correct label recovers no usable menu. Documented as a limitation instead |
| `Menu.currency_symbol` cleaned alongside `currency` | Dropped from scope | Blank on exactly the same rows as `currency`, so it carries no independent signal. This makes the planned "compare label against symbol" check a documented no-op rather than a skipped step |
| §4.6 of the plan: fallback pricing implemented in pandas | Moved to SQL | It needs MenuItem joined to Dish, which is a relational operation. Implementing it in pandas would have duplicated the join |
| Remove 3% of price outliers from each tail | Right-tail winsorization at 0.5%, capping rather than deleting | Measured first: the symmetric trim moved the per-menu average by +8.7% for the cheapest quartile and −32.0% for the priciest, compressing the range U1 measures |
| A minimum priced-items-per-menu threshold | Not implemented | Premature — no evidence yet identifies a threshold that improves U1 rather than just shrinking it |
| MySQL as the database | SQLite | Phase-I named MySQL while the Phase-II task division assumed SQLite; SQLite needs no server and the database file ships with the deliverable |

> **should cover…**
>
> - the OpenRefine deviations — in particular whether the delivered export matches the filters
>   described in §1.1-B (see the note there on the currency step)
> - the SQL deviations: staging schema revisions, and how the Step 8 iteration loop actually ran
>   against the plan
> - any Phase-I use-case assumption that changed, especially the definition of "comparable time
>   period", which remains open
> - a note on the Phase-I task split: it assigned whole steps S1–S5 per member, while the work
>   actually divided by tool and workflow step, so all three of us worked across S3–S5

## 5. Supplementary materials (10 pts)  [Team]

See [deliverables-checklist.md](deliverables-checklist.md).

---

## Appendix A — Tool use and AI assistance  [Team]

The project instructions require this. On tools beyond those used in class, they state:

> "Or maybe you find a new way to use an LLM (e.g., ChatGPT). In all these cases your report
> will have to include sufficient documentation about how you used these tools."

Our Phase-I plan also anticipated "AI-assisted code generation where appropriate and permitted
by course guidelines" (S3) and listed ChatGPT among the S2 profiling tools, so this appendix
documents AI use during the cleaning work itself.

### A.1 AI assistance during the cleaning work  [Team]

**Tool:** Claude Code (Anthropic Claude Opus 5), July 2026, run locally against the repository.

Used across Step 4: turning our OpenRefine profile into a pandas rule set, reorganizing the
`data/` tree for provenance tracking, writing the pipeline modules, generating the W2 workflow
model, and rebuilding the whole data set from its inputs to verify reproducibility. **The
profiling that decided what needed cleaning is our own OpenRefine work** (Steps 2 and 3, §1.1-B);
the tool was given those findings as objectives and wrote code against them. Where it disagreed
with a decision it said so, and three of those objections changed the plan (the currency-rescue
idea in §A.1.11, the outlier method in §A.1.9, and the pre-created directories in §A.1.2).

| Step | Tool | Used for | How the output was verified |
| --- | --- | --- | --- |
| 4 | Claude Code | Turning our OpenRefine profiling findings into the Step-4 rule set, and confirming the counts we quoted still held in the raw files before code was written against them | Three of our stated figures did not match the files and were reconciled: `currency` distinct values (43 vs. our 39), `status = under review` (174 vs. our 167), `MenuItem.dish_id` blanks (241 vs. our 0) |
| 4 | Claude Code | Testing the two currency-rescue routes we proposed — historical conversion, and inferring country from `location` with an LLM | Both rejected on the evidence it produced; re-verified with an independent join (menu-reported `dish_count`, total vs. priced items, orphan `menu_page_id` check) before we acted on it |
| 1 | Claude Code | Reorganizing `data/` into per-table `raw`/`interim`/`final` trees; moving 8 CSVs; rewriting `.gitignore` | Move script ran preflight assertions (every source present, no destination pre-existing) and compared byte sizes before and after each move; `git check-ignore` confirmed the new rules; file count on disk re-checked after untracking |
| 4 | Claude Code | Writing `src/config.py` — path objects, controlled vocabularies, dish-name character rules | Executed a check resolving every declared path against the filesystem, asserting each OpenRefine export's column shape, confirming no directory is created as a side effect, and spot-checking the log-tag and price formats |
| 4 | Claude Code | Writing `src/cleaning_utils.py` — the pure value-level cleaners each per-table module calls | Tested against real values taken from the profiling rather than invented ones; one fabrication bug found and fixed (a dish named `&` cleaned to `AND`). Re-run over all 394,297 dish names: no result outside the target charset, no empty results |
| 4 | Claude Code | Writing `src/provenance.py` — per-row log accumulation, cell-level change capture, stage snapshots, and the `cleaning_log.csv` rollup | Ran four real stages over `Menu_OR.csv` (5,236 rows) and checked the accumulated log, the change log contents, the column ordering, and that run directories appear only when a stage writes. Re-ran the sequence from scratch and compared SHA-256 hashes to confirm byte-identical output |
| 4 | Claude Code | Writing the four per-table cleaning modules and `src/run_pipeline.py`, each annotated for YesWorkflow | Each module run over its full export and its row counts checked against the input; one defect caught per module (see §A.1.6) |
| 4 | Claude Code | The price outlier rule — winsorizing the right tail, with the limit chosen by measuring candidates against the U1 metric | Thresholds confirmed against the maxima in the load-ready CSVs; row counts unchanged either side of the stage; 4,710 capped cells present in the change logs with before and after values |
| 4 | Claude Code | Clean-room rebuild: deleting all 37 generated files and 18 directories, then regenerating from the eight inputs | All 37 files reproduced byte-for-byte, verified by SHA-256 against a fingerprint taken before deletion |

Each task below records the instruction given, what came back, and how we checked it.

#### A.1.1 Cleaning objectives handed over from the OpenRefine profile (Step 4)

The profiling behind this section is our own OpenRefine work (§1.1-B). What follows is the
direction we gave the tool once that profile existed — the objectives it was to write Step 4
against, not an analysis it performed:

> These are the results of my OpenRefine profiling. Use them as the objectives for the
> Python/pandas cleaning.
>
> **Menu** — `id` has no blanks. `date` has 586 blanks; ditch those rows, since a menu with no
> date cannot be grouped into a time period. There are extreme years — 1091, 0190 and 2928 —
> which are not workable data, so abandon those rows too. `currency` and `currency_symbol` line
> up, with the blanks on the same rows, so we do not need the symbol column. There are 39
> currency variants and a fair number of blanks, and I want to try to rescue some of those rows:
> possibly by converting the source currency to USD against the menu's own time period, or by
> clustering `location` and using an LLM to infer the country with a 0–1 confidence score.
> `status` has only 167 "under review" rows against complete; throw those away.
>
> **MenuPage** — the data is solid; `id` and `menu_id` are populated on every row. All we use is
> those two columns. Verify they are numeric, and leave foreign-key dependencies to SQL.
>
> **MenuItem** — `id` and `menu_page_id` have no blanks and look numeric. Around 446k rows have
> no price, and `high_price` is blank whenever `price` is, so there is no within-row substitute
> when `price` is missing — we need to see whether those rows can be rescued another way.
> `dish_id` is populated on every row.
>
> **Dish** — the good news is that most rows have a lowest and highest price, but only 171,731 of
> 423,397 have both. That may be a problem to solve at the SQL stage; for now this is as good as
> we can do.

These objectives became rules R-1 to R-8 in §1.1-C. Two of them were investigated and dropped
rather than implemented — the currency rescue (§A.1.11) and, later, the symmetric outlier trim
(§A.1.9) — and both rejections are recorded with the evidence that produced them.

Before writing code against the figures above, the tool checked them against the raw files and
reported three that did not hold: `currency` distinct values (43, not 39), `status = under review`
(174, not 167), and `MenuItem.dish_id` blanks (241, not none). The `dish_id` figure was
independently corroborated by our Phase-I dataset description, which had already recorded empty
`dish_id` values — so the correction stands, and the "no blanks" reading above was a facet we had
misread.

#### A.1.2 Reorganizing the data tree (Step 1)

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

Before making the change it reported that this was not just a preference: `MenuItem.csv` is
113 MiB, above GitHub's 100 MiB per-file limit, so the push would have been rejected outright.
It also noted that the course instructions require the datasets to be shared via **Box** at
submission time, which is separate from whatever we use during development.

The move script ran preflight assertions (every source present, no destination pre-existing) and
compared byte sizes before and after each move; we confirmed the new ignore rules with
`git check-ignore` and re-counted the files on disk after untracking.

#### A.1.3 Pipeline configuration module (Step 4)

> Write the pipeline config module: path objects per table, a `Dollars → USD` currency map, the
> date-part columns, the dish-name character rules (uppercase ASCII alphanumerics plus
> apostrophe and comma; separators become spaces; `&` becomes AND; accents folded; non-Latin
> names marked UNKNOWN), and a per-row `log` column convention tagged `<column>:<operation>` so
> change counts can be reported per column.

Produced `src/config.py`. Two additions it argued for and we kept: an assertion of each
OpenRefine export's expected column shape, so that re-exporting with a renamed column fails
immediately rather than deep inside a cleaning function; and a `log_tag()` helper enforcing the
`<column>:<operation>` format, which makes the per-column change counts in §2.1-B
computable.

It proposed a `MIN_PRICED_ITEMS_PER_MENU` threshold, which we removed as premature.

Verified by executing a check that resolved every declared path against the filesystem, asserted
each export's column shape, confirmed no directory is created merely by referencing its path,
and spot-checked the log-tag and price formats.

#### A.1.4 Value-level cleaning functions (Step 4)

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

#### A.1.5 Provenance module (Step 4)

> Write the provenance layer the per-table cleaners sit on: it should apply the value-level
> cleaners to columns, accumulate the per-row `log`, capture cell-level before/after changes,
> and write each stage's output directory. Row-level change logs for semantic transforms only —
> formatting-only work records counts instead. The cleaning functions create their own run
> directories, so directory creation belongs here.

Produced `src/provenance.py`. Each cleaning stage constructs a `StepRecorder`, which writes
three artifacts into `data/<table>/interim/func-<step>/`: the stage snapshot, a cell-level
change log, and a summary of counts per column and operation. The summaries are concatenated
into `data/reports/cleaning_log.csv`, which is the source for the change table in §2.1-B.

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
evidence, and §2.1-B should report it as zero rather than omit it.

#### A.1.6 Per-table cleaning modules (Step 4)

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
than deleting it, so §2.1-B can report a measured zero instead of omitting the column.

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

#### A.1.7 Output layout correction (Step 4)

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

#### A.1.8 YesWorkflow model for W2 (Step 4)

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

#### A.1.9 Price outlier rule (Step 4)

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

Based on those results we changed the rule to **winsorization of the right tail only** — capping at a
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

#### A.1.10 Clean-room rebuild of the whole data set (Step 4)

> Remove every interim table we generated, leaving only the raw and OpenRefine CSVs. Run the
> pipeline end to end to regenerate them, regenerate the YesWorkflow graphs, and document each
> step.

The goal of this run was to test a claim we had been making rather than to produce anything new.
Up to here the generated tree had accumulated across many sessions, so "the pipeline reproduces
the data" had never actually been demonstrated from nothing.

We used the following sequence:

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

Row counts and every measured figure came out the same as the values reported in §2.1-B, which is
the result we wanted: the numbers in this report describe a data set that can be rebuilt from its
inputs, not one that exists only because of the order we happened to do things in.

#### A.1.11 What we decided, what changed our plan, and how we checked it

This subsection closes out §A.1 as a whole rather than describing a single task.

**Decisions made by the team.** The preliminary OpenRefine filtering that produced the
`*_OR.csv` exports was Po's own work, done in the OpenRefine UI — the tool never touched it. The
definitive OpenRefine profiling and cleaning is Charlene's and is outside the scope of this
appendix. Also ours: the directory scheme, the decision to keep the data out of git, the rule that
cleaning functions create their own run directories, and the choices among options it put to us —
how far to take the `UNKNOWN` rule for non-ASCII dish names, whether punctuation should be deleted
or converted to word boundaries, and whether the row-level change log should cover
formatting-only operations.

**Findings that changed our plan.** Two findings, both recorded in
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

**Verification standard.** We did not copy any reported count directly from the tool without checking it. Every
figure that reached a cleaning rule was reproduced either by the preliminary OpenRefine facets or by a
second, independently written check. The blank-currency finding above rests on a single pandas
join, so it is re-run in SQL once staging is loaded (see §2.2).

### A.2 Other tools

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
deliverable and was not yet available, so OR2YW had no history file to process. The W2 model
presented in §3.2 covers the Python/pandas cleaning; once the OpenRefine history exists, OR2YW is
the natural way to model that portion as a companion view, and `OpenRefineHistory.json` is
submitted regardless.
