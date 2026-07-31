-- S3 Step 5 — SQLite staging schema.
-- Owner: Madalyn Killian  [MadalynKillian]

PRAGMA foreign_keys = ON;

CREATE TABLE stg_menu(
    id int PRIMARY KEY,
    currency varchar,
    year int,
    month int,
    day int
);

CREATE TABLE stg_menu_item(
    id int PRIMARY KEY,
    menu_page_id int NOT NULL,
    price float,
    high_price float,
    dish_id int NOT NULL,
    FOREIGN KEY (menu_page_id) REFERENCES stg_menu_page(id),
    FOREIGN KEY (dish_id) REFERENCES stg_dish(id)
);

CREATE TABLE stg_menu_page(
    id int PRIMARY KEY,
    menu_id int NOT NULL,
    FOREIGN KEY (menu_id) REFERENCES stg_menu(id)
);

CREATE TABLE stg_dish(
    id int PRIMARY KEY,
    name varchar,
    lowest_price float NOT NULL,
    highest_price float NOT NULL
);