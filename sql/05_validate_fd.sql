-- =====================================================================
-- FD-1   stg_menu.id -> currency, year, month, day
-- =====================================================================
-- Formal:  {id} -> {currency, year, month, day}  on stg_menu
-- English: A menu id identifies exactly one menu. The same id must not carry
--          two different currencies or two different dates.

SELECT 'FD-1'   AS rule_id,
       id,
       COUNT(*) AS row_count,
       COUNT(DISTINCT currency) + (COUNT(*) > COUNT(currency)) AS currency_values,
       COUNT(DISTINCT year)     + (COUNT(*) > COUNT(year))     AS year_values,
       COUNT(DISTINCT month)    + (COUNT(*) > COUNT(month))    AS month_values,
       COUNT(DISTINCT day)      + (COUNT(*) > COUNT(day))      AS day_values,
       CASE WHEN MAX(COUNT(DISTINCT currency) + (COUNT(*) > COUNT(currency)),
                     COUNT(DISTINCT year)     + (COUNT(*) > COUNT(year)),
                     COUNT(DISTINCT month)    + (COUNT(*) > COUNT(month)),
                     COUNT(DISTINCT day)      + (COUNT(*) > COUNT(day))) > 1
            THEN 'fd_violation' ELSE 'duplicate_load' END AS disposition
FROM stg_menu
GROUP BY id
HAVING COUNT(*) > 1;


-- =====================================================================
-- FD-2   stg_menu_page.id -> menu_id
-- =====================================================================
-- Formal:  {id} -> {menu_id}  on stg_menu_page
-- English: A page belongs to exactly one menu.

SELECT 'FD-2'   AS rule_id,
       id,
       COUNT(*) AS row_count,
       COUNT(DISTINCT menu_id) + (COUNT(*) > COUNT(menu_id)) AS menu_id_values,
       CASE WHEN COUNT(DISTINCT menu_id) + (COUNT(*) > COUNT(menu_id)) > 1
            THEN 'fd_violation' ELSE 'duplicate_load' END AS disposition
FROM stg_menu_page
GROUP BY id
HAVING COUNT(*) > 1;


-- =====================================================================
-- FD-3   stg_menu_item.id -> menu_page_id, price, high_price, dish_id
-- =====================================================================
-- Formal:  {id} -> {menu_page_id, price, high_price, dish_id}  on stg_menu_item
-- English: An item id identifies exactly one transcribed line on one page.

SELECT 'FD-3'   AS rule_id,
       id,
       COUNT(*) AS row_count,
       COUNT(DISTINCT menu_page_id) + (COUNT(*) > COUNT(menu_page_id)) AS page_values,
       COUNT(DISTINCT price)        + (COUNT(*) > COUNT(price))        AS price_values,
       COUNT(DISTINCT high_price)   + (COUNT(*) > COUNT(high_price))   AS high_price_values,
       COUNT(DISTINCT dish_id)      + (COUNT(*) > COUNT(dish_id))      AS dish_id_values,
       CASE WHEN MAX(COUNT(DISTINCT menu_page_id) + (COUNT(*) > COUNT(menu_page_id)),
                     COUNT(DISTINCT price)        + (COUNT(*) > COUNT(price)),
                     COUNT(DISTINCT high_price)   + (COUNT(*) > COUNT(high_price)),
                     COUNT(DISTINCT dish_id)      + (COUNT(*) > COUNT(dish_id))) > 1
            THEN 'fd_violation' ELSE 'duplicate_load' END AS disposition
FROM stg_menu_item
GROUP BY id
HAVING COUNT(*) > 1;


-- =====================================================================
-- FD-4   (menu_page_id, dish_id) -> price
-- =====================================================================
-- Formal:  {menu_page_id, dish_id} -> {price}  on stg_menu_item
-- English: Where the same dish is listed more than once on the same menu page,
--          those lines must either be ALL unpriced or ALL carry the same price.
--          A page that prices the same dish two different ways contradicts
--          itself, and a page that prices it once and leaves the duplicate blank
--          has an incomplete transcription rather than a contradiction.

SELECT 'FD-4'                      AS rule_id,
       menu_page_id,
       dish_id,
       COUNT(*)                    AS line_count,
       COUNT(DISTINCT price) + (COUNT(*) > COUNT(price)) AS distinct_prices,
       COUNT(price)                AS priced_lines,
       CASE WHEN COUNT(DISTINCT price) > 1 THEN 'conflicting_prices'
            ELSE 'price_and_blank' END AS disposition,
       GROUP_CONCAT(price)         AS observed_prices
FROM stg_menu_item
WHERE dish_id IS NOT NULL
GROUP BY menu_page_id, dish_id
HAVING COUNT(DISTINCT price) + (COUNT(*) > COUNT(price)) > 1;


-- =====================================================================
-- FD-5   stg_dish.id -> name, lowest_price, highest_price
-- =====================================================================
-- Formal:  {id} -> {name, lowest_price, highest_price}  on stg_dish
-- English: A dish id identifies exactly one dictionary entry.

SELECT 'FD-5'   AS rule_id,
       id,
       COUNT(*) AS row_count,
       COUNT(DISTINCT name)          + (COUNT(*) > COUNT(name))          AS name_values,
       COUNT(DISTINCT lowest_price)  + (COUNT(*) > COUNT(lowest_price))  AS lowest_price_values,
       COUNT(DISTINCT highest_price) + (COUNT(*) > COUNT(highest_price)) AS highest_price_values,
       CASE WHEN MAX(COUNT(DISTINCT name)          + (COUNT(*) > COUNT(name)),
                     COUNT(DISTINCT lowest_price)  + (COUNT(*) > COUNT(lowest_price)),
                     COUNT(DISTINCT highest_price) + (COUNT(*) > COUNT(highest_price))) > 1
            THEN 'fd_violation' ELSE 'duplicate_load' END AS disposition
FROM stg_dish
GROUP BY id
HAVING COUNT(*) > 1;
