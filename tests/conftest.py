import pandas as pd
import pytest


@pytest.fixture
def inventory_df():
    return pd.DataFrame({
        "product_id": ["P001", "P002", "P003", "P004"],
        "category": ["Apparel", "Footwear", "Apparel", "Accessories"],
        "status": [
            "Full Price",
            "Markdown T1",
            "Markdown T2",
            "Clearance",
        ],
        "units": [120, 60, 35, 15],
    })
