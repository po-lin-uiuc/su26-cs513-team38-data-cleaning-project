-- IC RULES TO FOLLOW:

-- Menu (5 columns):
-- id: no null values here, all numeric
-- currency: I've translated from "Dollars" to "USD" to keep the currency identifier. Should all be "USD" for every row.
-- Original menu date is broken down into its date components:
-- year: all numeric, 4 digit representation of the year, no null or invalid values. Range is from 1851 to 2012
-- month: all numeric, 1-2 digit representation of the month, no null or invalid values. Range is 1-12.
-- day : all numeric, 1-2 digit representation of the day, no null or invalid values. Range is 1-31.


-- MenuItem (5 columns):
-- id:  no null values here, all numeric
-- menu_page_id: no null values here, all numeric
-- price : null or non-zero values. All numeric.
-- high_price : null or numeric values. Has some zeros, but for the 0 value rows the price columns has value. 
-- dish_id : no null values here, all numeric

-- MenuPage (2 columns):
-- id: no null values here, all numeric
-- menu_id: no null values here, all numeric

-- Dish (4 columns):
-- id: no null values here, all numeric
-- name: some transformations done here, all special characters removed except for some punctuations. All upper cased. For non-english dish names I've set the value to UNKNOWN .
-- lowest_price: no null values, range is 0 - 1100 (a good number of 0s FYI)
-- highest_price: no null values, range is 0 - 3100 (a good number of 0s FYI)



-- =====================================================================
-- IC-1: Menu.id primary key - cannot have NULL id
SELECT 'IC-1' AS rule_id,
       id,
       'Menu.id is required' AS violation
FROM stg_menu
WHERE id IS NULL;
 
-- =====================================================================
-- IC-2: Menu.currency must be USD
SELECT 'IC-2' AS rule_id,
       id,
       currency,
       'currency must be USD' AS violation
FROM stg_menu
WHERE currency IS NULL
   OR currency <> 'USD';
 
-- =====================================================================
-- IC-3: Menu.year must be a valid - year cannot be NULL, non-integer, or outside 1851-2012
SELECT 'IC-3' AS rule_id,
       id,
       year,
       typeof(year) AS stored_type,
       'year must be an integer between 1851 and 2012' AS violation
FROM stg_menu
WHERE year IS NULL
   OR typeof(year) <> 'integer'
   OR year < 1851
   OR year > 2012;

-- =====================================================================
-- IC-4: Menu.month must be a valid - cannot be NULL, non-integer, or outside 1-12
SELECT 'IC-4' AS rule_id,
       id,
       month,
       typeof(month) AS stored_type,
       'month must be an integer between 1 and 12' AS violation
FROM stg_menu
WHERE month IS NULL
   OR typeof(month) <> 'integer'
   OR month < 1
   OR month > 12;
 
-- =====================================================================
-- IC-5: Menu.day must be a valid - cannot be NULL, non-integer, or outside 1-31
SELECT 'IC-5' AS rule_id,
       id,
       day,
       typeof(day) AS stored_type,
       'day must be an integer between 1 and 31' AS violation
FROM stg_menu
WHERE day IS NULL
   OR typeof(day) <> 'integer'
   OR day < 1
   OR day > 31;
 
 
-- =====================================================================
-- IC-6: MenuItem.id primary key - cannot have NULL id
SELECT 'IC-6' AS rule_id,
       id,
       'MenuItem.id is required' AS violation
FROM stg_menu_item
WHERE id IS NULL;
 
-- =====================================================================
-- IC-7: MenuItem.menu_page_id primary key - cannot have NULL menu_page_id
SELECT 'IC-7' AS rule_id,
       id,
       menu_page_id,
       'MenuItem.menu_page_id is required' AS violation
FROM stg_menu_item
WHERE menu_page_id IS NULL;
 
-- =====================================================================
-- IC-8: MenuItem.price, if exists, must be nonzero - no non-null prices equal to zero
SELECT 'IC-8' AS rule_id,
       id,
       price,
       'price must be null or nonzero' AS violation
FROM stg_menu_item
WHERE price IS NOT NULL
  AND price = 0;
 
-- =====================================================================
-- IC-9: MenuItem.high_price, if exists, must be non-negative - cannot have non-null high_price below zero (zero is a valid price for high_price)
SELECT 'IC-9' AS rule_id,
       id,
       high_price,
       'high_price must be null or >= 0' AS violation
FROM stg_menu_item
WHERE high_price IS NOT NULL
  AND high_price < 0;
 
-- =====================================================================
-- IC-10: MenuItem.dish_id primary key - cannot have NULL dish_id
SELECT 'IC-10' AS rule_id,
       id,
       dish_id,
       'MenuItem.dish_id is required' AS violation
FROM stg_menu_item
WHERE dish_id IS NULL;
 
-- =====================================================================
-- IC-11: A zero high_price MUST have a non-null price - rows where high_price = 0 still need a price, so no MenuItem row can have high_price = 0 while price is NULL
SELECT 'IC-11' AS rule_id,
       id,
       price,
       high_price,
       'high_price = 0 requires a non-null price' AS violation
FROM stg_menu_item
WHERE high_price = 0
  AND price IS NULL;
 
-- =====================================================================
-- IC-12: MenuPage.id primary key - cannot have NULL id
SELECT 'IC-12' AS rule_id,
       id,
       'MenuPage.id is required' AS violation
FROM stg_menu_page
WHERE id IS NULL;

-- =====================================================================
-- IC-13: MenuPage.menu_id foreign key - cannot have NULL menu_id
SELECT 'IC-13' AS rule_id,
       id,
       menu_id,
       'MenuPage.menu_id is required' AS violation
FROM stg_menu_page
WHERE menu_id IS NULL;

-- =====================================================================
-- IC-14: Dish.id primary key - cannot have NULL id
SELECT 'IC-14' AS rule_id,
       id,
       'Dish.id is required' AS violation
FROM stg_dish
WHERE id IS NULL;

-- =====================================================================
-- IC-15: Dish.lowest_price must be in range - no dish row can have a lowest_price that is NULL or outside 0-1100
SELECT 'IC-15' AS rule_id,
       id,
       lowest_price,
       'lowest_price must be between 0 and 1100' AS violation
FROM stg_dish
WHERE lowest_price IS NULL
   OR lowest_price < 0
   OR lowest_price > 1100;

-- =====================================================================
-- IC-16: Dish.highest_price must be in range - no dish row can have a highest_price that is NULL or outside 0-3100
SELECT 'IC-16' AS rule_id,
       id,
       highest_price,
       'highest_price must be between 0 and 3100' AS violation
FROM stg_dish
WHERE highest_price IS NULL
   OR highest_price < 0
   OR highest_price > 3100;

-- =====================================================================
-- IC-17: Dish.highest_price must be >= Dish.lowest_price - no dish row can have highest_price less than lowest_price (because duh)
SELECT 'IC-17' AS rule_id,
       id,
       lowest_price,
       highest_price,
       'highest_price must be >= lowest_price' AS violation
FROM stg_dish
WHERE highest_price < lowest_price;