from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
DEPLOYMENT_DB = PROJECT_ROOT / "dashboard_data" / "retail_analytics.db"
LOCAL_DB = PROJECT_ROOT / "data" / "processed" / "retail_analytics.db"
DB_PATH = DEPLOYMENT_DB if DEPLOYMENT_DB.exists() else LOCAL_DB

st.set_page_config(
    page_title="Retail Intelligence Platform",
    page_icon="📊",
    layout="wide",
)

st.title("Retail Intelligence Platform")
st.caption(
    "Interactive retail data exploration powered by Python, SQLite and Plotly"
)


@st.cache_data
def load_table(table_name: str) -> pd.DataFrame:
    """Load a known table from the project SQLite database."""
    allowed_tables = {"all_records", "active_products", "historical_sales"}
    if table_name not in allowed_tables:
        raise ValueError("Unsupported table name.")

    with sqlite3.connect(DB_PATH) as connection:
        return pd.read_sql_query(
            f'SELECT * FROM "{table_name}"',
            connection,
        )


if not DB_PATH.exists():
    st.error(f"Database not found: {DB_PATH}")
    st.info(
        "Run `python build_data_pipeline.py` from the project directory. "
        "If generated outputs already exist, review them before using "
        "`python build_data_pipeline.py --force`."
    )
    st.stop()

try:
    all_records = load_table("all_records")
    active = load_table("active_products")
    historical = load_table("historical_sales")
except Exception as exc:
    st.error(f"Could not load the SQLite database: {exc}")
    st.stop()

if all_records.empty:
    st.warning("The all_records table is empty.")
    st.stop()


# Sidebar filters
st.sidebar.header("Dashboard filters")

marketing_values = sorted(
    all_records["MarketingType"].dropna().astype(str).unique().tolist()
)
selected_marketing = st.sidebar.multiselect(
    "Marketing type",
    options=marketing_values,
    default=marketing_values,
)

year_values = pd.to_numeric(
    all_records["ReleaseYear"], errors="coerce"
).dropna()
if not year_values.empty:
    min_year = int(year_values.min())
    max_year = int(year_values.max())
    if min_year < max_year:
        selected_years = st.sidebar.slider(
            "Release year",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year),
        )
    else:
        selected_years = (min_year, max_year)
else:
    selected_years = None

filtered = all_records[
    all_records["MarketingType"].astype(str).isin(selected_marketing)
].copy()

filtered_years = pd.to_numeric(filtered["ReleaseYear"], errors="coerce")
if selected_years is not None:
    filtered = filtered[
        filtered_years.between(selected_years[0], selected_years[1])
    ].copy()

st.sidebar.caption(
    "Filters affect the overall-record analyses. Active and historical "
    "summary cards use their respective complete tables."
)


# KPI calculations
total_records = len(filtered)
unique_skus = filtered["SKU_number"].nunique(dropna=True)
historical_sold_count = pd.to_numeric(
    historical["SoldCount"], errors="coerce"
).sum()
active_records = len(active)
historical_records = len(historical)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Filtered records", f"{total_records:,}")
k2.metric("Distinct SKUs", f"{unique_skus:,}")
k3.metric("Active records", f"{active_records:,}")
k4.metric("Historical records", f"{historical_records:,}")
k5.metric("Historical SoldCount", f"{historical_sold_count:,.0f}")

st.caption(
    "Record counts are not necessarily unique-product counts. SoldCount is "
    "a recorded dataset measure, not verified revenue or customer conversion."
)

tab_overview, tab_sales, tab_pricing, tab_data = st.tabs(
    ["Overview", "Historical indicators", "Pricing analysis", "Data explorer"]
)


with tab_overview:
    st.subheader("Records by marketing type")

    if filtered.empty:
        st.info("No records match the selected filters.")
    else:
        marketing_summary = (
            filtered.groupby("MarketingType", dropna=False)
            .agg(
                Record_Count=("SKU_number", "size"),
                Distinct_SKUs=("SKU_number", "nunique"),
            )
            .reset_index()
        )
        marketing_summary["MarketingType"] = (
            marketing_summary["MarketingType"]
            .fillna("Missing")
            .astype(str)
        )

        fig = px.bar(
            marketing_summary,
            x="MarketingType",
            y="Record_Count",
            color="MarketingType",
            title="Record count by marketing type",
            labels={
                "MarketingType": "Marketing type",
                "Record_Count": "Records",
            },
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            marketing_summary.sort_values("Record_Count", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Records by release year")
    year_summary = filtered.copy()
    year_summary["ReleaseYear"] = pd.to_numeric(
        year_summary["ReleaseYear"], errors="coerce"
    )
    year_summary = year_summary.dropna(subset=["ReleaseYear"])
    year_summary["ReleaseYear"] = year_summary["ReleaseYear"].astype(int)

    if year_summary.empty:
        st.info("No valid release years are available for these filters.")
    else:
        year_summary = (
            year_summary.groupby("ReleaseYear")
            .agg(
                Record_Count=("SKU_number", "size"),
                Distinct_SKUs=("SKU_number", "nunique"),
            )
            .reset_index()
            .sort_values("ReleaseYear")
        )
        fig = px.line(
            year_summary,
            x="ReleaseYear",
            y="Record_Count",
            markers=True,
            title="Records by release year",
            labels={
                "ReleaseYear": "Release year",
                "Record_Count": "Records",
            },
        )
        st.plotly_chart(fig, use_container_width=True)


with tab_sales:
    st.subheader("Historical sales indicators")
    st.caption(
        "These are historical source-record indicators, not transaction-level "
        "sales over time."
    )

    sold = historical.copy()
    sold["SoldCount"] = pd.to_numeric(sold["SoldCount"], errors="coerce")
    sold["SoldFlag"] = pd.to_numeric(sold["SoldFlag"], errors="coerce")

    s1, s2, s3 = st.columns(3)
    s1.metric("Historical records", f"{len(sold):,}")
    s2.metric(
        "Records with SoldFlag = 1",
        f"{int(sold['SoldFlag'].eq(1).sum()):,}",
    )
    s3.metric(
        "Sum of recorded SoldCount",
        f"{sold['SoldCount'].sum():,.0f}",
    )

    sales_by_marketing = (
        sold.groupby("MarketingType", dropna=False)
        .agg(
            Record_Count=("SKU_number", "size"),
            SoldCount_Total=("SoldCount", "sum"),
        )
        .reset_index()
    )
    sales_by_marketing["MarketingType"] = (
        sales_by_marketing["MarketingType"].fillna("Missing").astype(str)
    )

    fig = px.bar(
        sales_by_marketing,
        x="MarketingType",
        y="SoldCount_Total",
        title="Recorded SoldCount by marketing type",
        labels={
            "MarketingType": "Marketing type",
            "SoldCount_Total": "Sum of SoldCount",
        },
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(sales_by_marketing, use_container_width=True, hide_index=True)


with tab_pricing:
    st.subheader("Price distributions and relationships")

    price_columns = [
        column
        for column in ["PriceReg", "LowUserPrice", "LowNetPrice"]
        if column in filtered.columns
    ]

    if not price_columns:
        st.warning("No supported price columns were found.")
    else:
        chosen_price = st.selectbox(
            "Choose a price field",
            options=price_columns,
        )
        prices = pd.to_numeric(filtered[chosen_price], errors="coerce")
        price_data = pd.DataFrame({"Price": prices}).dropna()
        price_data = price_data[price_data["Price"] >= 0]

        if price_data.empty:
            st.info("No non-negative numeric prices match these filters.")
        else:
            p1, p2, p3 = st.columns(3)
            p1.metric("Records with price", f"{len(price_data):,}")
            p2.metric("Median price", f"{price_data['Price'].median():,.2f}")
            p3.metric("Mean price", f"{price_data['Price'].mean():,.2f}")

            fig = px.histogram(
                price_data,
                x="Price",
                nbins=50,
                title=f"Distribution of {chosen_price}",
                labels={"Price": chosen_price},
            )
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("SQL-aligned pricing quality review")

    # Reuse the same source table as sql/analytics/05_price_quality_flags.sql.
    pricing_review = historical.copy()

    pricing_review = pricing_review[
        pricing_review["MarketingType"].astype(str).isin(selected_marketing)
    ].copy()

    if selected_years is not None:
        review_years = pd.to_numeric(
            pricing_review["ReleaseYear"], errors="coerce"
        )
        pricing_review = pricing_review[
            review_years.between(selected_years[0], selected_years[1])
        ].copy()

    price_fields = ["PriceReg", "LowUserPrice", "LowNetPrice"]
    for column in price_fields:
        pricing_review[column] = pd.to_numeric(
            pricing_review[column], errors="coerce"
        )

    # Match the six CASE rules in 05_price_quality_flags.sql.
    pricing_review["zero_regular_price_flag"] = (
        pricing_review["PriceReg"].eq(0).astype(int)
    )
    pricing_review["high_regular_price_review_flag"] = (
        pricing_review["PriceReg"].gt(500).astype(int)
    )
    pricing_review["low_user_above_regular_flag"] = (
        pricing_review["LowUserPrice"].gt(pricing_review["PriceReg"]).astype(int)
    )
    pricing_review["low_net_above_regular_flag"] = (
        pricing_review["LowNetPrice"].gt(pricing_review["PriceReg"]).astype(int)
    )
    pricing_review["extreme_low_user_price_review_flag"] = (
        pricing_review["LowUserPrice"].gt(1000).astype(int)
    )
    pricing_review["extreme_low_net_price_review_flag"] = (
        pricing_review["LowNetPrice"].gt(1000).astype(int)
    )

    flag_columns = [
        "zero_regular_price_flag",
        "high_regular_price_review_flag",
        "low_user_above_regular_flag",
        "low_net_above_regular_flag",
        "extreme_low_user_price_review_flag",
        "extreme_low_net_price_review_flag",
    ]

    pricing_review["Any_Review_Flag"] = (
        pricing_review[flag_columns].max(axis=1)
    )

    # Preserve the prioritisation used in the SQL ORDER BY clause.
    pricing_review["review_priority"] = 4
    pricing_review.loc[
        pricing_review["PriceReg"].gt(500), "review_priority"
    ] = 3

    above_regular = (
        pricing_review["LowUserPrice"].gt(pricing_review["PriceReg"])
        | pricing_review["LowNetPrice"].gt(pricing_review["PriceReg"])
    )
    pricing_review.loc[above_regular, "review_priority"] = 2
    pricing_review.loc[
        pricing_review["PriceReg"].eq(0), "review_priority"
    ] = 1

    extreme_price = (
        pricing_review["LowUserPrice"].gt(1000)
        | pricing_review["LowNetPrice"].gt(1000)
    )
    pricing_review.loc[extreme_price, "review_priority"] = 0

    pricing_review["extreme_price_sort"] = pricing_review[
        "LowUserPrice"
    ].where(
        pricing_review["LowUserPrice"].gt(1000),
        pricing_review["LowNetPrice"].where(
            pricing_review["LowNetPrice"].gt(1000), 0
        ),
    )

    flagged = pricing_review[
        pricing_review["Any_Review_Flag"].eq(1)
    ].sort_values(
        ["review_priority", "extreme_price_sort"],
        ascending=[True, False],
    )

    st.metric("Historical records reviewed", f"{len(pricing_review):,}")
    st.metric("Records flagged for review", f"{len(flagged):,}")

    st.caption(
        "These six flags match the conditions in "
        "sql/analytics/05_price_quality_flags.sql. They identify records "
        "for investigation, not confirmed pricing errors. Sidebar filters "
        "apply to marketing type and release year."
    )

    st.dataframe(
        flagged[
            [
                "SKU_number",
                "MarketingType",
                "SoldFlag",
                "SoldCount",
                "PriceReg",
                "LowUserPrice",
                "LowNetPrice",
                *flag_columns,
            ]
        ].head(500),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download pricing review as CSV",
        data=flagged.to_csv(index=False).encode("utf-8-sig"),
        file_name="retail_pricing_quality_review.csv",
        mime="text/csv",
    )

with tab_data:
    st.subheader("Filtered data explorer")
    st.write(f"Showing {len(filtered):,} filtered records.")

    display_columns = [
        column
        for column in [
            "SKU_number",
            "MarketingType",
            "ReleaseYear",
            "SoldFlag",
            "SoldCount",
            "PriceReg",
            "LowUserPrice",
            "LowNetPrice",
        ]
        if column in filtered.columns
    ]

    st.dataframe(
        filtered[display_columns].head(1000),
        use_container_width=True,
        hide_index=True,
    )
    st.caption("The table previews up to 1,000 rows for browser performance.")

    csv_bytes = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Download filtered records as CSV",
        data=csv_bytes,
        file_name="retail_filtered_records.csv",
        mime="text/csv",
    )

st.divider()
st.caption(
    "Retail Intelligence Platform | Python · SQLite · SQL · Streamlit · Plotly"
)
