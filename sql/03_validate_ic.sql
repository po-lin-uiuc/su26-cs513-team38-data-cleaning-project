-- S3 Step 7 — Integrity and domain constraint checks (IC).
-- Owner: Charlene Khun  [CharleneKhun]
-- Checklist: docs/checklists/charlene-khun.md  (Step 7)
-- Rule catalog: docs/cleaning-rules.md
-- Problems: docs/data-quality-problems.md  (P1-P10)
--
-- Run:  sqlite3 -header -csv data/cs513_team38.sqlite \
--           < sql/03_validate_ic.sql \
--           > data/reports/validation_ic_results.csv
--
-- Run this file twice:
--   1. against staging loaded from RAW data to record the before violations;
--   2. against staging loaded from CLEANED data to record the after violations.
--
-- Each query returns VIOLATING rows. An empty result means the corresponding
-- integrity or domain constraint holds. Source identifiers are included where
-- available so Step 8 can trace violations to their source rows.
--
-- PROJECT COLUMN ASSUMPTIONS
--   Menu:     id, source_row_num, eligibility, cleaned_year, month, day,
--             status_clean, currency_clean
--   MenuItem: id, source_row_num, menu_page_id, dish_id, price, high_price,
--             price_source, cleaning_status, exclusion_reason, warning_reason
--   Dish:     id, source_row_num, lowest_price, highest_price
--
-- CONTROLLED VALUES USED BELOW
--   Menu.eligibility          IN (0, 1)
--   Menu.status_clean         IN ('Complete', 'Incomplete')
--   Menu.currency_clean       IN ('Dollars', 'Cents')
--   MenuItem.price_source     IN ('original_price', 'high_price',
--                                 'fallback_average', 'missing')
--   MenuItem.cleaning_status  IN ('included', 'warned', 'excluded')
--
-- If docs/cleaning-rules.md uses different literal labels or a different
-- minimum valid-item threshold, update the corresponding IN (...) lists or
-- threshold constant below.
--
-- COVERAGE
--   Menu: required id, eligibility domain, cleaned_year validity/range,
--         valid date, status_clean domain, currency_clean domain
--   MenuItem: required id, numeric/positive cleaned price, price_source domain,
--             cleaning_status domain, exclusion and warning reasons,
--             no_valid_price handling
--   Price relationships: highest_price >= lowest_price, high_price >= price,
--                        valid fallback components, no non-positive fallbacks
--   Eligibility: complete menu, valid date, comparable currency, valid final
--                item price, minimum valid-item threshold

-- =====================================================================
-- IC-M-0   U1-eligible Menu must have a non-null menu id
-- =====================================================================
-- Denial constraint: there must not exist a U1-eligible Menu whose required
-- menu identifier is NULL or blank.

SELECT 'IC-M-0' AS rule_id,
       id,
       source_row_num,
       eligibility,
       'U1-eligible menu requires a non-null menu id' AS violation
FROM stg_menu
WHERE eligibility = 1
  AND (id IS NULL OR TRIM(CAST(id AS TEXT)) = '');


-- =====================================================================
-- IC-M-1   Menu eligibility must be a controlled Boolean domain
-- =====================================================================
-- Denial constraint: no Menu row may have eligibility outside {0,1}.

SELECT 'IC-M-1' AS rule_id,
       id,
       source_row_num,
       eligibility,
       'eligibility must be 0 or 1' AS violation
FROM stg_menu
WHERE eligibility IS NULL
   OR eligibility NOT IN (0, 1);


-- =====================================================================
-- IC-M-2A   U1-eligible Menu must have a valid cleaned_year
-- =====================================================================
-- Denial constraint: there must not exist a U1-eligible Menu whose
-- cleaned_year is NULL or is not stored as an integer.

SELECT 'IC-M-2A' AS rule_id,
       id,
       source_row_num,
       eligibility,
       cleaned_year,
       typeof(cleaned_year) AS stored_type,
       'U1-eligible menu requires an integer cleaned_year' AS violation
FROM stg_menu
WHERE eligibility = 1
  AND (cleaned_year IS NULL OR typeof(cleaned_year) <> 'integer');


-- =====================================================================
-- IC-M-2B   cleaned_year must fall within the accepted range
-- =====================================================================
-- Accepted project range: 1800 through 2026. Update the upper bound in the
-- rule catalog when the project is rerun in a later year.
-- Denial constraint: no non-null numeric cleaned_year may be outside the
-- accepted range.

SELECT 'IC-M-2B' AS rule_id,
       id,
       source_row_num,
       cleaned_year,
       typeof(cleaned_year) AS stored_type,
       'cleaned_year must fall between 1800 and 2026' AS violation
FROM stg_menu
WHERE cleaned_year IS NOT NULL
  AND (
       typeof(cleaned_year) <> 'integer'
       OR cleaned_year < 1800
       OR cleaned_year > 2026
      );


-- =====================================================================
-- IC-M-3   month and day must form valid calendar components
-- =====================================================================
-- Denial constraint: no Menu row may contain a month/day outside the basic
-- numeric ranges. IC-M-9 below additionally checks that the combined date is a
-- real calendar date.

SELECT 'IC-M-3' AS rule_id,
       id,
       source_row_num,
       cleaned_year,
       month,
       day,
       'month must be 1-12 and day must be 1-31' AS violation
FROM stg_menu
WHERE month IS NULL OR day IS NULL
   OR typeof(month) <> 'integer'
   OR typeof(day) <> 'integer'
   OR month NOT BETWEEN 1 AND 12
   OR day NOT BETWEEN 1 AND 31;


-- =====================================================================
-- IC-M-4   status_clean must use its controlled domain
-- =====================================================================
-- Denial constraint: no Menu row may use a status outside the rule catalog.

SELECT 'IC-M-4' AS rule_id,
       id,
       source_row_num,
       status_clean,
       'status_clean must be Complete or Incomplete' AS violation
FROM stg_menu
WHERE status_clean IS NULL
   OR status_clean NOT IN ('Complete', 'Incomplete');


-- =====================================================================
-- IC-M-5   currency_clean must use its controlled comparable domain
-- =====================================================================
-- Denial constraint: no cleaned Menu row may use a currency outside Dollars
-- or Cents. The cleaned export may ultimately contain only Dollars; allowing
-- Cents here reflects the documented cleaning rule before normalization.

SELECT 'IC-M-5' AS rule_id,
       id,
       source_row_num,
       currency_clean,
       'currency_clean must be Dollars or Cents' AS violation
FROM stg_menu
WHERE currency_clean IS NULL
   OR currency_clean NOT IN ('Dollars', 'Cents');


-- =====================================================================
-- IC-MI-1   MenuItem id must be present
-- =====================================================================
-- Denial constraint: no MenuItem row may have a missing item id.

SELECT 'IC-MI-1' AS rule_id,
       id,
       source_row_num,
       menu_page_id,
       dish_id,
       'MenuItem id is required' AS violation
FROM stg_menu_item
WHERE id IS NULL
   OR TRIM(CAST(id AS TEXT)) = '';


-- =====================================================================
-- IC-MI-2A   Retained cleaned item price must be numeric
-- =====================================================================
-- A retained U1 item is one whose cleaning_status is included or warned.
-- Denial constraint: no retained item may have a NULL or nonnumeric final
-- cleaned price.

SELECT 'IC-MI-2A' AS rule_id,
       id,
       source_row_num,
       menu_page_id,
       dish_id,
       price,
       typeof(price) AS stored_type,
       cleaning_status,
       'retained cleaned item price must be numeric' AS violation
FROM stg_menu_item
WHERE cleaning_status IN ('included', 'warned')
  AND (price IS NULL OR typeof(price) NOT IN ('integer', 'real'));


-- =====================================================================
-- IC-MI-2B   Retained cleaned item price must be positive
-- =====================================================================
-- Denial constraint: no retained item may have a numeric final cleaned price
-- that is zero or negative.

SELECT 'IC-MI-2B' AS rule_id,
       id,
       source_row_num,
       menu_page_id,
       dish_id,
       price,
       typeof(price) AS stored_type,
       cleaning_status,
       'retained cleaned item price must be greater than zero' AS violation
FROM stg_menu_item
WHERE cleaning_status IN ('included', 'warned')
  AND typeof(price) IN ('integer', 'real')
  AND price <= 0;


-- =====================================================================
-- IC-MI-3   price_source must use its controlled domain
-- =====================================================================
-- Denial constraint: no MenuItem row may use an undocumented price source.

SELECT 'IC-MI-3' AS rule_id,
       id,
       source_row_num,
       price_source,
       'price_source is outside the controlled domain' AS violation
FROM stg_menu_item
WHERE price_source IS NULL
   OR price_source NOT IN (
        'original_price',
        'high_price',
        'fallback_average',
        'missing'
      );


-- =====================================================================
-- IC-MI-4   cleaning_status must use its controlled domain
-- =====================================================================
-- Denial constraint: no MenuItem may have a status outside included, warned,
-- or excluded.

SELECT 'IC-MI-4' AS rule_id,
       id,
       source_row_num,
       cleaning_status,
       'cleaning_status is outside the controlled domain' AS violation
FROM stg_menu_item
WHERE cleaning_status IS NULL
   OR cleaning_status NOT IN ('included', 'warned', 'excluded');


-- =====================================================================
-- IC-MI-5   Excluded rows must carry an exclusion reason
-- =====================================================================
-- Denial constraint: no excluded MenuItem may have a blank exclusion_reason.

SELECT 'IC-MI-5' AS rule_id,
       id,
       source_row_num,
       cleaning_status,
       exclusion_reason,
       'excluded row requires exclusion_reason' AS violation
FROM stg_menu_item
WHERE cleaning_status = 'excluded'
  AND (exclusion_reason IS NULL OR TRIM(exclusion_reason) = '');


-- =====================================================================
-- IC-MI-6   Warned rows must carry a warning reason
-- =====================================================================
-- Adopted rule: every row assigned cleaning_status = 'warned' requires a
-- warning_reason. If the rule catalog defines only certain warning categories
-- as requiring a reason, add that category condition to the WHERE clause.
-- Denial constraint: no warned MenuItem may have a blank warning_reason.

SELECT 'IC-MI-6' AS rule_id,
       id,
       source_row_num,
       cleaning_status,
       warning_reason,
       'warned row requires warning_reason' AS violation
FROM stg_menu_item
WHERE cleaning_status = 'warned'
  AND (warning_reason IS NULL OR TRIM(warning_reason) = '');



-- =====================================================================
-- IC-MI-7   U1-retained item must not carry no_valid_price
-- =====================================================================
-- The project represents an unusable final price through price_source =
-- 'missing' and/or the reason code 'no_valid_price'. A retained U1 item must
-- not carry either marker.
-- Denial constraint: no included or warned MenuItem may be marked as having no
-- valid price.

SELECT 'IC-MI-7' AS rule_id,
       id,
       source_row_num,
       price_source,
       cleaning_status,
       exclusion_reason,
       warning_reason,
       'U1-retained item is marked no_valid_price' AS violation
FROM stg_menu_item
WHERE cleaning_status IN ('included', 'warned')
  AND (
       price_source = 'missing'
       OR LOWER(TRIM(COALESCE(exclusion_reason, ''))) = 'no_valid_price'
       OR LOWER(TRIM(COALESCE(warning_reason, ''))) = 'no_valid_price'
      );


-- =====================================================================
-- IC-P-1   Dish highest_price must be at least lowest_price
-- =====================================================================
-- Denial constraint: when both values are valid numeric values, highest_price
-- must not be less than lowest_price.

SELECT 'IC-P-1' AS rule_id,
       id,
       source_row_num,
       lowest_price,
       highest_price,
       'highest_price is lower than lowest_price' AS violation
FROM stg_dish
WHERE typeof(lowest_price) IN ('integer', 'real')
  AND typeof(highest_price) IN ('integer', 'real')
  AND lowest_price > 0
  AND highest_price > 0
  AND highest_price < lowest_price;


-- =====================================================================
-- IC-P-2   MenuItem high_price must not be below price
-- =====================================================================
-- This rule is active because high_price is retained as a price bound.
-- Denial constraint: where both values are valid, high_price must not be less
-- than price.

SELECT 'IC-P-2' AS rule_id,
       id,
       source_row_num,
       price,
       high_price,
       'high_price is lower than price' AS violation
FROM stg_menu_item
WHERE typeof(price) IN ('integer', 'real')
  AND typeof(high_price) IN ('integer', 'real')
  AND price > 0
  AND high_price > 0
  AND high_price < price;


-- =====================================================================
-- IC-P-3   fallback averages require two valid positive components
-- =====================================================================
-- Project-specific assumption: price and high_price are the two stored
-- component values used by fallback_average. Both must be numeric and positive,
-- and high_price must be at least price. If the schema stores separate raw
-- fallback-component columns, replace price/high_price below with those columns.
-- Denial constraint: no fallback average may be derived from fewer than two
-- valid components or from reversed bounds.

SELECT 'IC-P-3' AS rule_id,
       id,
       source_row_num,
       price_source,
       price,
       high_price,
       'fallback_average requires two valid positive ordered components' AS violation
FROM stg_menu_item
WHERE price_source = 'fallback_average'
  AND (
       price IS NULL
       OR high_price IS NULL
       OR typeof(price) NOT IN ('integer', 'real')
       OR typeof(high_price) NOT IN ('integer', 'real')
       OR price <= 0
       OR high_price <= 0
       OR high_price < price
      );



-- =====================================================================
-- IC-P-4   Non-positive values must not be used as valid fallbacks
-- =====================================================================
-- Denial constraint: no MenuItem using fallback_average may use price or
-- high_price as a fallback component when that component is zero or negative.

SELECT 'IC-P-4' AS rule_id,
       id,
       source_row_num,
       price_source,
       price,
       high_price,
       'non-positive value used as a fallback component' AS violation
FROM stg_menu_item
WHERE price_source = 'fallback_average'
  AND (
       (typeof(price) IN ('integer', 'real') AND price <= 0)
       OR
       (typeof(high_price) IN ('integer', 'real') AND high_price <= 0)
      );


-- =====================================================================
-- IC-E-1   Eligible menus must be complete
-- =====================================================================
-- Denial constraint: no eligible Menu may have a non-complete status.

SELECT 'IC-E-1' AS rule_id,
       id,
       source_row_num,
       eligibility,
       status_clean,
       'eligible menu must be Complete' AS violation
FROM stg_menu
WHERE eligibility = 1
  AND (status_clean IS NULL OR status_clean <> 'Complete');


-- =====================================================================
-- IC-E-2   Eligible menus must have a valid calendar date
-- =====================================================================
-- SQLite date() returns NULL for unparseable dates. The round-trip comparison
-- also rejects normalized impossible dates such as 2021-02-30.
-- Denial constraint: no eligible Menu may have an invalid cleaned date.

SELECT 'IC-E-2' AS rule_id,
       id,
       source_row_num,
       cleaned_year,
       month,
       day,
       'eligible menu must have a real calendar date' AS violation
FROM stg_menu
WHERE eligibility = 1
  AND (
       cleaned_year IS NULL
       OR month IS NULL
       OR day IS NULL
       OR typeof(cleaned_year) <> 'integer'
       OR typeof(month) <> 'integer'
       OR typeof(day) <> 'integer'
       OR cleaned_year NOT BETWEEN 1800 AND 2026
       OR month NOT BETWEEN 1 AND 12
       OR day NOT BETWEEN 1 AND 31
       OR date(
            printf('%04d-%02d-%02d', cleaned_year, month, day),
            '+0 days'
          ) IS NULL
       OR date(
            printf('%04d-%02d-%02d', cleaned_year, month, day),
            '+0 days'
          ) <> printf('%04d-%02d-%02d', cleaned_year, month, day)
      );


-- =====================================================================
-- IC-E-3   Eligible menus must use a comparable currency
-- =====================================================================
-- Denial constraint: no eligible Menu may use a currency outside the project
-- comparison population.

SELECT 'IC-E-3' AS rule_id,
       id,
       source_row_num,
       eligibility,
       currency_clean,
       'eligible menu must use Dollars or Cents' AS violation
FROM stg_menu
WHERE eligibility = 1
  AND (
       currency_clean IS NULL
       OR currency_clean NOT IN ('Dollars', 'Cents')
      );



-- =====================================================================
-- IC-E-6   Items without a valid final price must be ineligible for U1
-- =====================================================================
-- Item-level U1 eligibility is represented by cleaning_status. Rows with an
-- invalid final price must be excluded rather than included or warned.
-- Denial constraint: no included or warned item may have a NULL, nonnumeric,
-- zero, or negative final price.

SELECT 'IC-E-6' AS rule_id,
       id,
       source_row_num,
       menu_page_id,
       price,
       typeof(price) AS stored_type,
       cleaning_status,
       'item without a valid final price is retained for U1' AS violation
FROM stg_menu_item
WHERE cleaning_status IN ('included', 'warned')
  AND (
       price IS NULL
       OR typeof(price) NOT IN ('integer', 'real')
       OR price <= 0
      );


-- =====================================================================
-- IC-E-4   Eligible menus must contain at least one valid final price
-- =====================================================================
-- A valid item is included or warned and has a positive numeric cleaned price.
-- Denial constraint: no eligible Menu may have zero valid priced items.

SELECT 'IC-E-4' AS rule_id,
       m.id,
       m.source_row_num,
       COUNT(mi.id) AS valid_item_count,
       'eligible menu has no valid final-price MenuItem' AS violation
FROM stg_menu AS m
LEFT JOIN stg_menu_page AS mp
       ON mp.menu_id = m.id
LEFT JOIN stg_menu_item AS mi
       ON mi.menu_page_id = mp.id
      AND mi.cleaning_status IN ('included', 'warned')
      AND typeof(mi.price) IN ('integer', 'real')
      AND mi.price > 0
WHERE m.eligibility = 1
GROUP BY m.id, m.source_row_num
HAVING COUNT(mi.id) = 0;


-- =====================================================================
-- IC-E-5   Eligible menus must meet the adopted valid-item threshold
-- =====================================================================
-- The adopted minimum is 1 valid priced MenuItem. If the cleaning-rules file
-- specifies a larger threshold, replace the final numeric constant below.
-- Denial constraint: no eligible Menu may fall below the minimum threshold.

WITH valid_items_per_menu AS (
  SELECT m.id AS menu_id,
         m.source_row_num,
         COUNT(mi.id) AS valid_item_count
  FROM stg_menu AS m
  LEFT JOIN stg_menu_page AS mp
         ON mp.menu_id = m.id
  LEFT JOIN stg_menu_item AS mi
         ON mi.menu_page_id = mp.id
        AND mi.cleaning_status IN ('included', 'warned')
        AND typeof(mi.price) IN ('integer', 'real')
        AND mi.price > 0
  WHERE m.eligibility = 1
  GROUP BY m.id, m.source_row_num
)
SELECT 'IC-E-5' AS rule_id,
       menu_id AS id,
       source_row_num,
       valid_item_count,
       1 AS required_minimum,
       'eligible menu falls below the minimum valid-item threshold' AS violation
FROM valid_items_per_menu
WHERE valid_item_count < 1;