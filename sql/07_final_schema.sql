-- BUILD FOR FINAL TABLES AND SCHEMA

DROP TABLE IF EXISTS final_menu;
DROP TABLE IF EXISTS final_item;
 
CREATE TABLE final_menu(
    menu_id        int PRIMARY KEY,
    cleaned_year   int,
    currency_clean varchar
);
 
INSERT INTO final_menu (menu_id, cleaned_year, currency_clean)
SELECT id,
       year,
       currency
FROM stg_menu;
 
 
CREATE TABLE final_item(
    menu_item_id      int PRIMARY KEY,
    menu_id           int NOT NULL,
    dish_name         varchar,
    clean_item_price  float,
    FOREIGN KEY (menu_id) REFERENCES final_menu(menu_id)
);
 
INSERT INTO final_item (menu_item_id, menu_id, dish_name, clean_item_price)
SELECT mi.id,
       mp.menu_id,
       d.name,
       mi.price
FROM stg_menu_item AS mi
JOIN stg_menu_page AS mp ON mp.id = mi.menu_page_id
JOIN stg_dish      AS d  ON d.id  = mi.dish_id;
