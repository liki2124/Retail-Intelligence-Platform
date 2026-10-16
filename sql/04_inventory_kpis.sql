-- 04_inventory_kpis.sql
-- Key inventory performance indicators for the sample dataset.

-- 1. Overall inventory KPIs
SELECT
    COUNT(*) AS inventory_records,
    COUNT(DISTINCT product_id) AS unique_products,
    SUM(units) AS total_units,
    ROUND(AVG(units), 2) AS average_units_per_record
FROM inventory;

-- 2. Inventory units and record share by status
SELECT
    status,
    COUNT(*) AS record_count,
    SUM(units) AS total_units,
    ROUND(
        100.0 * COUNT(*) / (SELECT COUNT(*) FROM inventory),
        2
    ) AS record_share_pct,
    ROUND(
        100.0 * SUM(units) / NULLIF(
            (SELECT SUM(units) FROM inventory), 0
        ),
        2
    ) AS unit_share_pct
FROM inventory
GROUP BY status
ORDER BY total_units DESC;

-- 3. Inventory units by product category
SELECT
    category,
    COUNT(*) AS record_count,
    SUM(units) AS total_units,
    ROUND(AVG(units), 2) AS average_units
FROM inventory
GROUP BY category
ORDER BY total_units DESC;

-- 4. Markdown and clearance exposure
SELECT
    CASE
        WHEN status = 'Full Price' THEN 'Full Price'
        ELSE 'Markdown / Clearance'
    END AS inventory_group,
    COUNT(*) AS record_count,
    SUM(units) AS total_units,
    ROUND(
        100.0 * SUM(units) / NULLIF(
            (SELECT SUM(units) FROM inventory), 0
        ),
        2
    ) AS unit_share_pct
FROM inventory
GROUP BY inventory_group
ORDER BY total_units DESC;
