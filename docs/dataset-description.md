# Dataset Description (D)

> Phase-I rubric item 1 (25 pts): schema/ER diagram (10) + narrative description (15).

**Dataset:** NYPL *"What's on the Menu?"* — `Menu.csv`, `MenuPage.csv`, `MenuItem.csv`, `Dish.csv`.

## Schema

![Schema chart](figures/phase1/fig-1-1-schema.png)

<!-- [Team] export this figure from the Phase-I doc; see docs/figures/README.md -->

*Figure 1.1 — Table structure and join keys.*

```
Menu.id ◀──── MenuPage.menu_id
              MenuPage.id ◀──── MenuItem.menu_page_id
                                MenuItem.dish_id ────▶ Dish.id
```

## Narrative

This dataset is a collection of information taken from restaurant menus dating from the
mid-1800s to the present day, with locations spanning the world. The menu data is separated
into four tables linked by identification numbers.

### Menu.csv

Contains a physical description of the menu along with the location it is from. Each menu
has a primary key column `id`.

- Columns containing a `name` and `sponsor` value never contain an `event`, `venue`, or
  `place` value, and vice versa.
- `location_type` is completely empty and can be excluded during cleaning.
- `event` contains frequent misspellings and typos — `"DINNER;"`, `"DINNE"`, and
  `"[DINNER]"` all represent `"DINNER"`.
- `place` has similar inconsistencies, compounded by each entry potentially representing a
  city, street, boat/at-sea location (common enough to note separately), country, exact
  location (restaurant name), or simply `"?"`.

### MenuPage.csv

Contains identifiers linking `Menu.csv` and `MenuItem.csv`, along with page height and width.

- `menu_id` is a foreign key to `Menu.id`, **but there are `menu_id` values not present in
  `Menu.id`** — a broken inclusion dependency.
- Multiple pages share the same `menu_id`, so a menu may have several pages.
- No notable errors or typos in this table.
- `full_height` (600s–12,000s) and `full_width` (500s–9,000s) have no documented unit of
  measurement. The values are consistent with pixel dimensions, but this could not be
  confirmed — recorded as a limitation.
- `uuid` uniquely references the page but is not descriptive enough for analysis.

### MenuItem.csv

Contains information about each specific item transcribed on a menu page.

- `menu_page_id` is a foreign key to `MenuPage.id`; many items share a `menu_page_id`.
- `dish_id` is a foreign key to `Dish.id`; **over 100 records have an empty `dish_id`**,
  suggesting either non-dish items or missing information.
- `xpos` / `ypos` have no specified unit of measurement — a limitation.
- `price` may represent either the average cost of the item or the lowest recorded price
  across all instances; this is uncertain.
- `high_price` is inferred to be the highest recorded cost across all menus the item appears
  on. When null it may mean the high price equals `price`, but this is also uncertain.

### Dish.csv

Contains data about individual dishes across all menus: frequency, price data, year of
introduction, and last year of appearance.

- `id` is the primary key referenced by `MenuItem.dish_id`.
- Assuming `first_appeared` / `last_appeared` are years, some values are impossible —
  e.g. `1` and `2928`.
- `description` is empty — a limitation of the dataset.
- `lowest_price` / `highest_price` contain questionable values; several dishes list `0.0`
  for both, including items such as Caviar that are unlikely to have been free.
- `name` contains many typos, misspellings, and stray characters — e.g. `"?? Fry?? Stew"`,
  `".... GUESTS...."`, `", Raw, on Half Shell"`,
  `", Served with French, Mayonnaise or Russian DressingHearts of Lettuce"`. This column
  requires significant cleaning before it is viable for analysis.

## Columns used for U1

Only a subset of the schema is needed for the main use case (Phase-II step S1):

| Table | Columns |
| --- | --- |
| Menu | `id`, `date`, `currency`, `currency_symbol`, `status` (complete only) |
| MenuPage | `id`, `menu_id` |
| MenuItem | `id`, `menu_page_id`, `price`, `high_price`, `dish_id` |
| Dish | `id`, `name`, `lowest_price`, `highest_price` |
