-- FIXES FOR THE CLEANED DATA:

-- =====================================================================
-- IC-8:
-- if price missing, check if high price exists, if so, set price = high price, else set price = NULL

-- take from high price if price is missing and high price exists
UPDATE stg_menu_item
SET price = high_price
WHERE price = 0
  AND high_price IS NOT NULL
  AND high_price <> 0;

-- no high price, set price to NULL
UPDATE stg_menu_item
SET price = NULL
WHERE price = 0
  AND high_price IS NULL;

-- if price is zero and high price also zero, just drop the row
DELETE FROM stg_menu_item
WHERE price = 0
  AND high_price = 0;


-- =====================================================================
-- FD-4:
-- price_and_blank (one real price, rest are NULL duplicates) - drop the NULL rows, keep the priced ones
-- conflicting_prices (two or more different real prices for the same page+dish) - collapse the whole group into a single row: price = average of the group's prices (BOTH HIGH AND NORMAL), then delete the rest

-- TEMP, WILL TURN BACK ON AFTER
PRAGMA foreign_keys = OFF;

-- GETTING AVERAGE PRICE FOR EACH (menu_page_id, dish_id) GROUP WITH CONFLICTING PRICES
CREATE TEMP TABLE fd4_conflict_avg AS
SELECT menu_page_id,
       dish_id,
       AVG(DISTINCT price)      AS avg_price,
       AVG(DISTINCT high_price) AS avg_high_price,
       MIN(id)                  AS keep_id
FROM stg_menu_item
WHERE dish_id IS NOT NULL
  AND price IS NOT NULL
GROUP BY menu_page_id, dish_id
HAVING COUNT(DISTINCT price) > 1;


DELETE FROM stg_menu_item
WHERE (menu_page_id, dish_id) IN (
        SELECT menu_page_id, dish_id FROM fd4_conflict_avg
      )
  AND id NOT IN (SELECT keep_id FROM fd4_conflict_avg);

UPDATE stg_menu_item
SET price = (
      SELECT avg_price FROM fd4_conflict_avg
      WHERE fd4_conflict_avg.keep_id = stg_menu_item.id
    ),
    high_price = (
      SELECT avg_high_price FROM fd4_conflict_avg
      WHERE fd4_conflict_avg.keep_id = stg_menu_item.id
    )
WHERE id IN (SELECT keep_id FROM fd4_conflict_avg);

DROP TABLE fd4_conflict_avg;

-- DROP NULL PRICES IN DUPLICATE GROUPS WHERE THE OTHER ROWS HAVE A PRICE
DELETE FROM stg_menu_item
WHERE price IS NULL
  AND dish_id IS NOT NULL
  AND (menu_page_id, dish_id) IN (
        SELECT menu_page_id, dish_id
        FROM stg_menu_item
        WHERE dish_id IS NOT NULL
        GROUP BY menu_page_id, dish_id
        HAVING COUNT(DISTINCT price) = 1
           AND COUNT(*) > COUNT(price)
      );

PRAGMA foreign_keys = ON;