-- Compare historical sales outcomes by marketing type.
-- This is descriptive and does not establish causation.

SELECT
    MarketingType,
    COUNT(*) AS product_records,
    SUM(CASE WHEN SoldFlag = 1 THEN 1 ELSE 0 END) AS sold_records,
    ROUND(
        100.0 * SUM(CASE WHEN SoldFlag = 1 THEN 1 ELSE 0 END)
        / COUNT(*), 2
    ) AS sold_record_rate_pct,
    SUM(SoldCount) AS total_units_sold,
    ROUND(AVG(PriceReg), 2) AS avg_regular_price
FROM historical_sales
GROUP BY MarketingType
ORDER BY sold_record_rate_pct DESC;
