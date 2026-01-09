from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA_PATH = Path("data/gold/kindle_reviews_dashboard.parquet")

st.set_page_config(page_title="Customer Service Dashboard", layout="wide")


@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Gold dataset not found: {DATA_PATH}")
    df = pd.read_parquet(DATA_PATH)
    df["period_start"] = pd.to_datetime(df["period_start"])
    return df


def main() -> None:
    st.title("Customer Service Dashboard - Kindle Reviews")

    df = load_data()

    st.sidebar.header("Filtros")

    min_date = df["period_start"].min()
    max_date = df["period_start"].max()
    date_range = st.sidebar.date_input(
        "Rango de fechas",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date(),
    )

    asin_options = ["(Todos)"] + sorted(df["asin"].unique().tolist())
    asin = st.sidebar.selectbox("Producto (ASIN)", asin_options)

    min_reviews = st.sidebar.number_input(
        "Mínimo de reviews mensuales", min_value=0, max_value=10_000, value=10
    )

    start_date, end_date = date_range
    mask = (df["period_start"].dt.date >= start_date) & (
        df["period_start"].dt.date <= end_date
    )

    if asin != "(Todos)":
        mask &= df["asin"] == asin

    filtered = df[mask & (df["review_count"] >= min_reviews)].copy()

    st.subheader("KPIs principales")
    col1, col2, col3, col4 = st.columns(4)

    avg_rating = filtered["avg_rating"].mean()
    neg_rate = (filtered["pct_1"] + filtered["pct_2"]).mean()
    review_count = filtered["review_count"].sum()
    helpful_ratio = filtered["helpful_ratio"].mean()

    col1.metric("Avg Rating", f"{avg_rating:.2f}")
    col2.metric("% Negativas (1-2)", f"{neg_rate:.2%}")
    col3.metric("Total Reviews", f"{review_count:,}")
    if np.isnan(helpful_ratio):
        col4.metric("Helpfulness Ratio", "N/A")
    else:
        col4.metric("Helpfulness Ratio", f"{helpful_ratio:.2%}")

    st.subheader("Tendencias")
    trend = (
        filtered.groupby("period_start", as_index=False)
        .agg(
            avg_rating=("avg_rating", "mean"),
            pct_1=("pct_1", "mean"),
            pct_2=("pct_2", "mean"),
            review_count=("review_count", "sum"),
        )
        .sort_values("period_start")
    )
    trend["neg_rate"] = trend["pct_1"] + trend["pct_2"]

    st.line_chart(trend.set_index("period_start")["avg_rating"], height=240)
    st.line_chart(trend.set_index("period_start")["neg_rate"], height=240)
    st.line_chart(trend.set_index("period_start")["review_count"], height=240)

    st.subheader("Ranking de productos (peores por % negativas)")
    risk = filtered.copy()
    risk["neg_rate"] = risk["pct_1"] + risk["pct_2"]
    worst = (
        risk.groupby("asin", as_index=False)
        .agg(
            avg_rating=("avg_rating", "mean"),
            neg_rate=("neg_rate", "mean"),
            review_count=("review_count", "sum"),
        )
        .sort_values("neg_rate", ascending=False)
        .head(10)
    )
    st.dataframe(worst, use_container_width=True)

    st.subheader("Scatter: rating vs volumen")
    scatter = (
        filtered.groupby("asin", as_index=False)
        .agg(
            avg_rating=("avg_rating", "mean"),
            review_count=("review_count", "sum"),
        )
    )
    st.scatter_chart(scatter, x="review_count", y="avg_rating")

    st.subheader("Detalle por producto")
    if asin != "(Todos)":
        detail = filtered.sort_values("period_start")
        detail["neg_rate"] = detail["pct_1"] + detail["pct_2"]
        st.line_chart(detail.set_index("period_start")["avg_rating"], height=240)
        st.line_chart(detail.set_index("period_start")["neg_rate"], height=240)
    else:
        st.info("Selecciona un ASIN para ver el detalle por producto.")

    st.sidebar.caption("Fuente: data/gold/kindle_reviews_dashboard.parquet")


if __name__ == "__main__":
    main()
