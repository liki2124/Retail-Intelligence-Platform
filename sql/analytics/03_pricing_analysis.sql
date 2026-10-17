-- Compare price fields for sold and unsold historical records.
-- These price fields are not realized transaction prices.

SELECT
    SoldFlag,
    COUNT(*) AS product_records,
    ROUND(AVG(PriceReg), 2) AS avg_regular_price,
    ROUND(AVG(LowUserPrice), 2) AS avg_low_user_price,
    ROUND(AVG(LowNetPrice), 2) AS avg_low_net_price,
    ROUND(MIN(PriceReg), 2) AS min_regular_price,
    ROUND(MAX(PriceReg), 2) AS max_regular_price
FROM historical_sales
GROUP BY SoldFlag
ORDER BY SoldFlag DESC;
