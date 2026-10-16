-- 03_data_quality_checks.sql
-- Data quality checks for the sample inventory table.

-- 1. Missing product IDs
SELECT *
FROM inventory
WHERE product_id IS NULL
   OR TRIM(product_id) = '';

-- 2. Negative inventory units
SELECT *
FROM inventory
WHERE units < 0;

-- 3. Missing or unexpected statuses
SELECT *
FROM inventory
WHERE status IS NULL
   OR TRIM(status) = ''
   OR status NOT IN (
       'Full Price',
       'Markdown T1',
       'Markdown T2',
       'Clearance'
   );

-- 4. Duplicate product IDs
SELECT product_id, COUNT(*) AS duplicate_count
FROM inventory
WHERE product_id IS NOT NULL
  AND TRIM(product_id) <> ''
GROUP BY product_id
HAVING COUNT(*) > 1;
