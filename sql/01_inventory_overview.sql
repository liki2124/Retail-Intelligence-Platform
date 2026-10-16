-- Retail Intelligence Platform
-- 01: Inventory overview
-- Expected SQLite table: inventory

SELECT
    COUNT(*) AS total_inventory_records,
    COUNT(DISTINCT product_id) AS unique_products,
    SUM(units) AS total_units
FROM inventory;

SELECT
    status,
    COUNT(*) AS inventory_records,
    COUNT(DISTINCT product_id) AS unique_products,
    SUM(units) AS total_units
FROM inventory
GROUP BY status
ORDER BY total_units DESC;

SELECT
    category,
    SUM(units) AS total_units,
    COUNT(DISTINCT product_id) AS unique_products
FROM inventory
GROUP BY category
ORDER BY total_units DESC;
