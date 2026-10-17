-- Historical product sales performance.
-- SoldCount represents units sold, not revenue.

SELECT
    SoldFlag,
    COUNT(*) AS product_records,
    SUM(SoldCount) AS total_units_sold,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM historical_sales), 2)
        AS percentage_of_historical_records
FROM historical_sales
GROUP BY SoldFlag
ORDER BY SoldFlag DESC;
