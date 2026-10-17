-- Historical sales outcomes by release year.
-- ReleaseYear = 0 is excluded because it may be a placeholder.
-- This does not represent sales by transaction date.

SELECT
    ReleaseYear,
    COUNT(*) AS product_records,
    SUM(CASE WHEN SoldFlag = 1 THEN 1 ELSE 0 END) AS sold_records,
    ROUND(
        100.0 * SUM(CASE WHEN SoldFlag = 1 THEN 1 ELSE 0 END)
        / COUNT(*), 2
    ) AS sold_record_rate_pct,
    SUM(SoldCount) AS total_units_sold,
    ROUND(AVG(PriceReg), 2) AS avg_regular_price
FROM historical_sales
WHERE ReleaseYear > 0
GROUP BY ReleaseYear
HAVING COUNT(*) >= 30
ORDER BY ReleaseYear;
