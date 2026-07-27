# Cleaning-rule catalog  [CharleneKhun]

Owner: **Charlene Khun** (Step 3). This catalog is the contract between profiling and code:
Po implements exactly these rules in [../src/](../src/), and the expected validation query
column tells Madalyn what to check in [../sql/](../sql/).

A rule is not done until all twelve columns are filled. Rule IDs are stable — never renumber,
mark superseded rules as such.

## Rule template

| Field | Meaning |
| --- | --- |
| Rule ID | `R-n`, stable forever |
| Rule name | Short imperative, e.g. "Parse menu year" |
| Source table / column | Where it applies |
| DQ problem | `P1`…`P10` from [data-quality-problems.md](data-quality-problems.md) |
| Detection condition | Precise, testable predicate — not prose |
| Action | `clean` \| `warn` \| `exclude` |
| Output column | Column written (blank if flag-only) |
| Reason code | From `src/config.Reason`, if warn/exclude |
| U1 relevance | Why U1 fails without it |
| Validation query | `IC-n` / `IND-n` / `FD-n` that proves it held |
| Expected outcome | What the count should be after cleaning |

## Identifier rules

| ID | Name | Table.column | P | Detection | Action | Output | Reason | U1 relevance | Check | Expected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-1 | | | | | | | | | | |

Decisions to record: required vs. optional IDs · permitted ID format · missing-ID behavior ·
malformed-ID behavior · duplicate-ID handling · `dish_id` optionality.

> Decide explicitly whether `MenuItem.dish_id` is optional. An item with no dish reference is
> a different finding from an item pointing at a dish that does not exist, and the two will be
> conflated in Step 7 unless this catalog separates them.

## String and categorical rules

| ID | Name | Table.column | P | Detection | Action | Output | Reason | U1 relevance | Check | Expected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-10 | | | | | | | | | | |

Decisions to record: whitespace normalization · blank/null normalization · accepted
`status_clean` values · dish-name capitalization · dish-name punctuation · clustering
acceptance criteria · numeric-only and symbol-only name handling · when originals must be
preserved.

### Accepted clusters

Record accepted merges so Po can apply them deterministically and the report can count them.

| Cluster ID | Method | Canonical value | Merged variants | Rows affected | Accepted by | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| C-1 | fingerprint | | | | | |

### Rejected clusters

Required evidence — "cluster suggestions rejected" is a reported count, and rejections show
judgment rather than blind acceptance.

| Cluster ID | Method | Suggested merge | Why rejected |
| --- | --- | --- | --- |
| C-R1 | | | |

## Date rules

| ID | Name | Table.column | P | Detection | Action | Output | Reason | U1 relevance | Check | Expected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-20 | | | | | | | | | | |

Decisions to record: acceptable date formats · acceptable year range · `cleaned_year`
extraction · missing-date handling · malformed-date handling · impossible-year handling · when
a menu is excluded from U1.

Mirror the agreed year range in `src/config.py` so the Python rules and the SQL checks cannot
drift apart.

## Currency rules

| ID | Name | Table.column | P | Detection | Action | Output | Reason | U1 relevance | Check | Expected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-30 | | | | | | | | | | |

Decisions to record: accepted labels · accepted symbols · valid label-symbol combinations ·
missing-currency handling · contradictory-currency handling · ambiguous-currency handling ·
U1 currency scope · **whether U1 is restricted to U.S. dollars** · explicit statement that no
currency conversion occurs unless implemented and supported.

> Whatever is decided here likely sets the U1 sample size more than any other rule, because
> the Phase-I inspection found currency fields frequently empty. Record the reasoning, not just
> the decision.

## Price rules  [CharleneKhun] [PoLin]

| ID | Name | Table.column | P | Detection | Action | Output | Reason | U1 relevance | Check | Expected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-40 | | | | | | | | | | |

Decisions to record: valid numeric format · zero-price handling · negative-price handling ·
malformed-price handling · suspicious-value review criteria · `high_price < price` behavior ·
`highest_price < lowest_price` behavior · cleaned price fields · approval of Po's fallback
logic.

## U1 eligibility rules

A menu or item is eligible for U1 only if:

- [ ] Menu has acceptable `status_clean`
- [ ] Menu has valid `cleaned_year`
- [ ] Menu has acceptable `currency_clean`
- [ ] Item has a valid positive clean price
- [ ] Menu meets the minimum priced-item threshold, if adopted

Also define: when a row is **warned but retained** versus **excluded**. The distinction drives
every count in S5, so it must be unambiguous.

## Requirements discovered after Phase I

Log anything profiling revealed that the Phase-I plan did not anticipate — the report must
explain how the plan changed and why.

| Date | Discovery | Rule added/changed | Impact on U1 |
| --- | --- | --- | --- |
