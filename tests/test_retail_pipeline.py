import sqlite3

import pandas as pd
import pytest

import build_data_pipeline as pipeline


@pytest.fixture
def sample_retail_df():
    return pd.DataFrame({
        "Order": [1, 2, 3, 4],
        "File_Type": ["Active", "Active", "Historical", "Historical"],
        "SKU_number": ["00123", "00456", "00123", "00789"],
        "SoldFlag": [None, None, 1, 0],
        "SoldCount": [None, None, 3, 0],
        "MarketingType": ["D", "S", "D", "S"],
        "ReleaseNumber": [1, 2, 3, 4],
        "New_Release_Flag": [0, 1, 0, 1],
        "StrengthFactor": [1.0, 1.1, 1.2, 1.3],
        "PriceReg": [50.0, 75.0, 100.0, 80.0],
        "ReleaseYear": [2020, 2021, 2022, 2023],
        "ItemCount": [10, 20, 30, 40],
        "LowUserPrice": [40.0, 60.0, 70.0, 90.0],
        "LowNetPrice": [35.0, 55.0, 65.0, 85.0],
    })


def test_report_counts_records_and_sku_overlap(sample_retail_df):
    report = pipeline.build_report(sample_retail_df)

    assert report["row_count"] == 4
    assert report["column_count"] == 14
    assert report["active_records"] == 2
    assert report["historical_records"] == 2
    assert report["skus_in_both_groups"] == 1
    assert report["active_only_skus"] == 1
    assert report["historical_only_skus"] == 1
    assert report["historical_total_sold_count"] == 3
    assert report["validation_status"] == "passed"


def test_sku_identifiers_remain_text_when_loaded(
    tmp_path, monkeypatch, sample_retail_df
):
    source = tmp_path / "retail.csv"
    sample_retail_df.to_csv(source, index=False)

    monkeypatch.setattr(pipeline, "RAW_FILE", source)

    loaded = pipeline.load_and_validate()

    assert loaded["SKU_number"].dtype.name in ("string", "object")
    assert loaded.loc[0, "SKU_number"] == "00123"


def test_validation_rejects_missing_required_column(
    tmp_path, monkeypatch, sample_retail_df
):
    source = tmp_path / "retail.csv"
    sample_retail_df.drop(columns=["PriceReg"]).to_csv(source, index=False)
    monkeypatch.setattr(pipeline, "RAW_FILE", source)

    with pytest.raises(ValueError, match="Column schema mismatch"):
        pipeline.load_and_validate()


def test_validation_rejects_inconsistent_sales_values(
    tmp_path, monkeypatch, sample_retail_df
):
    sample_retail_df.loc[2, "SoldCount"] = 0
    source = tmp_path / "retail.csv"
    sample_retail_df.to_csv(source, index=False)
    monkeypatch.setattr(pipeline, "RAW_FILE", source)

    with pytest.raises(ValueError, match="inconsistent SoldFlag/SoldCount"):
        pipeline.load_and_validate()


def test_price_quality_sql_flags_suspicious_price_relationships():
    sql_path = (
        pipeline.ROOT / "sql" / "analytics" / "05_price_quality_flags.sql"
    )
    sql = sql_path.read_text(encoding="utf-8")

    with sqlite3.connect(":memory:") as connection:
        connection.execute("""
            CREATE TABLE historical_sales (
                SKU_number TEXT,
                MarketingType TEXT,
                SoldFlag REAL,
                SoldCount REAL,
                PriceReg REAL,
                LowUserPrice REAL,
                LowNetPrice REAL
            )
        """)

        connection.executemany(
            """
            INSERT INTO historical_sales
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("001", "D", 0, 0, 0, 20, 1500),
                ("002", "S", 1, 2, 100, 120, 80),
                ("003", "D", 0, 0, 600, 400, 300),
                ("004", "S", 0, 0, 100, 50, 40),
            ],
        )

        result = pd.read_sql_query(sql, connection)

    assert len(result) == 4

    zero_price = result.loc[result["SKU_number"] == "001"].iloc[0]
    assert zero_price["zero_regular_price_flag"] == 1
    assert zero_price["extreme_low_net_price_review_flag"] == 1

    user_price = result.loc[result["SKU_number"] == "002"].iloc[0]
    assert user_price["low_user_above_regular_flag"] == 1

    high_price = result.loc[result["SKU_number"] == "003"].iloc[0]
    assert high_price["high_regular_price_review_flag"] == 1

    ordinary_price = result.loc[result["SKU_number"] == "004"].iloc[0]
    assert ordinary_price["zero_regular_price_flag"] == 0
    assert ordinary_price["high_regular_price_review_flag"] == 0
