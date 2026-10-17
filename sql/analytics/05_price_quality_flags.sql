SELECT
    SKU_number,
    MarketingType,
    SoldFlag,
    SoldCount,
    PriceReg,
    LowUserPrice,
    LowNetPrice,

    CASE WHEN PriceReg = 0
        THEN 1 ELSE 0
    END AS zero_regular_price_flag,

    CASE WHEN PriceReg > 500
        THEN 1 ELSE 0
    END AS high_regular_price_review_flag,

    CASE WHEN LowUserPrice > PriceReg
        THEN 1 ELSE 0
    END AS low_user_above_regular_flag,

    CASE WHEN LowNetPrice > PriceReg
        THEN 1 ELSE 0
    END AS low_net_above_regular_flag,

    CASE WHEN LowUserPrice > 1000
        THEN 1 ELSE 0
    END AS extreme_low_user_price_review_flag,

    CASE WHEN LowNetPrice > 1000
        THEN 1 ELSE 0
    END AS extreme_low_net_price_review_flag

FROM historical_sales
ORDER BY
    CASE
        WHEN LowUserPrice > 1000 OR LowNetPrice > 1000 THEN 0
        WHEN PriceReg = 0 THEN 1
        WHEN LowUserPrice > PriceReg OR LowNetPrice > PriceReg THEN 2
        WHEN PriceReg > 500 THEN 3
        ELSE 4
    END,
    CASE
        WHEN LowUserPrice > 1000 THEN LowUserPrice
        WHEN LowNetPrice > 1000 THEN LowNetPrice
        ELSE 0
    END DESC;
