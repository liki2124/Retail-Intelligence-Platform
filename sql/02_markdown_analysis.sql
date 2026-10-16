-- Retail Intelligence Platform
-- 02: Markdown Analysis
-- Uses the SQLite inventory table.

-- Inventory records and units by status
SELECT
    status,
    COUNT(*) AS inventory_records,
    SUM(units) AS total_units,
    ROUND(
        100.0 * SUM(units) / NULLIF(
            (SELECT SUM(units) FROM inventory), 0
        ), 2
    ) AS share_of_total_units_pct
FROM inventory
GROUP BY status
ORDER BY total_units DESC;

-- Compare full-price and markdown/clearance inventory
SELECT
    CASE
        WHEN status = 'Full Price' THEN 'Full Price'
        WHEN status IN ('Markdown T1', 'Markdown T2', 'Clearance')
            THEN 'Markdown / Clearance'
        ELSE 'Other'
    END AS inventory_group,
    COUNT(*) AS inventory_records,
    SUM(units) AS total_units
FROM inventory
GROUP BY inventory_group
ORDER BY total_units DESC;
