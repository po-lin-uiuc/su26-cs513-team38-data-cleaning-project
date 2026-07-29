-- S3 Step 5 — SQLite staging schema.
-- Owner: Madalyn Killian  [MadalynKillian]
-- Checklist: docs/checklists/madalyn-killian.md  (Step 5)
--
-- Run:  sqlite3 data/cs513_team38.sqlite < sql/01_schema_staging.sql
--
-- WHAT THIS FILE MUST CONTAIN
--   CREATE TABLE for stg_menu, stg_menu_page, stg_menu_item, stg_dish, each with:
--     - the raw columns preserved
--     - the cleaned columns produced by Step 4 (see docs/data-dictionary.md)
--     - the provenance columns: cleaning_status, warning_reason,
--       exclusion_reason, source_file, source_row_num
--   Indexes supporting the Step 7 validation joins.
--
-- DESIGN DECISIONS TO MAKE AND RECORD (Step 5 narrative)
--   - Which constraints are enforced at load time vs. checked afterward by query.
--     A constraint enforced at load gives a failed insert; a constraint checked by
--     query gives a countable violation. Step 7 needs counts.
--   - Whether to declare staging tables STRICT. SQLite applies type *affinity*,
--     not enforcement, so an unSTRICT INTEGER column will happily store 'abc'.
--     STRICT (SQLite 3.37+) rejects it instead. Decide which behaviour serves the
--     validation layer, and justify the choice.
--   - Whether the cleaned CSVs land in TEXT tables first. SQLite's .import writes
--     '' rather than NULL for blank fields, and '' passes an IS NOT NULL check.
--   - Why staging is separate from the final operational tables.
--
-- Record every later revision in docs/iteration-log.md (schema revision log).

-- TODO [MadalynKillian]: staging DDL

CREATE TABLE stg_menu(
    id int PRIMARY KEY,
    -- name varchar,
    -- spnsor varchar, varchar,
    -- event varchar,
    -- venue varchar,
    -- place varchar,
    -- physical_description varchar,
    -- occasion varchar,
    -- notes varchar,
    -- call_number varchar,
    -- keywords varchar,
    -- language varchar,
    date datetime,
    -- location varchar,
    -- location_type varchar,
    currency varchar,
    -- currency_symbol varchar,
    status varchar,
    -- page_count varchar,
    -- dish_count varchar
);

CREATE TABLE stg_menu_page(
    id int PRIMARY KEY,
    menu_id int NOT NULL,
    -- page_number varchar,
    -- image_id varchar,
    -- full_height varchar,
    -- full_width varchar,
    -- uuid varchar
);

CREATE TABLE stg_menu_item(
    id int PRIMARY KEY,
    menu_page_id int NOT NULL,
    price float,
    high_price float,
    dish_id int,
    -- created_at varchar,
    -- updated_at varchar,
    -- xpos varchar,
    -- ypos varchar
);

CREATE TABLE stg_dish(
    id int PRIMARY KEY,
    name varchar,
    -- description varchar,
    -- menus_appeared varchar,
    -- times_appeared varchar,
    -- first_appeared varchar,
    -- last_appeared varchar,
    lowest_price float NOT NULL,
    highest_price float NOT NULL,
);