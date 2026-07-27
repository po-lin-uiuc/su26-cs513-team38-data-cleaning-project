# Use Cases

> Phase-I rubric item 2 (30 pts): U1 (20) + U0 (5) + U2 (5).

## U1 — Target use case (cleaning is *necessary and sufficient*)

Categorize menu price ranges (`$`, `$$`, `$$$`, `$$$$`) **relative to the distribution of
menu prices within comparable time periods**.

To do this, usable data must be restricted to menus with usable dates and valid menu item
prices. Data cleaning is necessary because:

- Menu item prices may be missing, malformed, or inconsistent.
- Menu dates and currencies may be incomplete or inconsistent.
- Menus with too few priced items may produce misleading averages.
- Dish names need normalization due to odd/vague attribute values.
- Dish and menu item prices need to be inferred where prices are missing across tables.

**Target end state:** compare menus and their average dish prices grouped by similar time
periods, and identify the most/least expensive menus within those periods.

### Why cleaning is *sufficient*

Once prices, dates, currencies, and dish names are standardized, menus can be grouped into
comparable historical periods, average menu prices computed accurately, and menus classified
into price tiers. **No external data is required** — which is precisely what separates U1
from U2.

### Queries Q_U1  [Team]

The instructions note that stating U1 as a set of queries makes "necessary and sufficient"
precise: if `Q_U1(D)` gives an incorrect or misleading answer and `Q_U1(D′)` gives a correct
one, cleaning was both necessary and sufficient. Write those queries here — they become the
before/after evidence the Phase-II rubric grades.

## U0 — "Zero data cleaning" (cleaning is *not necessary*)

List the raw transcribed dish items that appeared on a selected menu, and the recorded menu
items with the greatest difference between `first_appeared` and `last_appeared`.

The dataset already contains the relationships between menus, menu pages, menu items, and
dishes, so this is answered by retrieving existing records associated with a menu. It
requires no price normalization, currency handling, or dish-name clustering — the original
data is good enough as-is. Evaluating longest-standing menu items only involves the
`first_appeared` / `last_appeared` values already present.

## U2 — "Never enough" (cleaning is *not sufficient*)

Analyze menu **affordability** based on income and economic conditions of a particular
restaurant/menu's location at a given time period.

This relates to U1, but affordability requires information the dataset does not contain:
cost of living, inflation, tipping customs, tax rates, and similar. Additionally, location
information is too ambiguous to associate menus with specific neighborhoods, cities, or
states — a value of `"New York"` does not distinguish city from state from borough from
neighborhood, so locality cannot be identified even after cleaning.

The distribution of menu item names is also frequently nonsensical. Even for U1 we assume
some menu item/dish rows may actually refer to the same item. And because the menu dimension
fields (`xpos`, `ypos`, `full_height`, `full_width`) have no documented unit, identifying
items at similar or identical positions on a page is not reliably possible.
