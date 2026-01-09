from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.dataset as ds

SILVER_DIR = Path("data/silver/kindle_reviews")
OUT_PATH = Path("data/gold/kindle_reviews_dashboard.parquet")


def main() -> None:
    if not SILVER_DIR.exists():
        raise FileNotFoundError(f"Silver dataset not found: {SILVER_DIR}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "asin",
        "overall",
        "review_ts",
        "reviewerID",
        "helpful_yes",
        "helpful_total",
        "reviewText",
    ]

    dataset = ds.dataset(str(SILVER_DIR), format="parquet")
    table = dataset.to_table(columns=columns)
    df = table.to_pandas()

    df["overall"] = pd.to_numeric(df["overall"], errors="coerce")
    df["helpful_yes"] = pd.to_numeric(df["helpful_yes"], errors="coerce")
    df["helpful_total"] = pd.to_numeric(df["helpful_total"], errors="coerce")

    df = df[df["asin"].notna() & df["reviewerID"].notna()]
    df = df[df["review_ts"].notna()]
    df = df[(df["overall"] >= 1) & (df["overall"] <= 5)]

    df = df.drop_duplicates(subset=["reviewerID", "asin", "review_ts"])

    invalid_helpful = (
        (df["helpful_yes"] < 0)
        | (df["helpful_total"] < 0)
        | (df["helpful_yes"] > df["helpful_total"])
    )
    df.loc[invalid_helpful, ["helpful_yes", "helpful_total"]] = np.nan

    df["review_year"] = df["review_ts"].dt.year.astype("int16")
    df["review_month"] = df["review_ts"].dt.month.astype("int8")

    for rating in [1, 2, 3, 4, 5]:
        df[f"rating_{rating}"] = (df["overall"] == rating).astype("int8")

    grouped = df.groupby(["asin", "review_year", "review_month"], as_index=False)

    monthly = grouped.agg(
        review_count=("overall", "size"),
        avg_rating=("overall", "mean"),
        median_rating=("overall", "median"),
        std_rating=("overall", "std"),
        helpful_yes_sum=("helpful_yes", "sum"),
        helpful_total_sum=("helpful_total", "sum"),
        distinct_reviewers=("reviewerID", "nunique"),
        pct_missing_text=("reviewText", lambda s: s.isna().mean()),
        rating_1_sum=("rating_1", "sum"),
        rating_2_sum=("rating_2", "sum"),
        rating_3_sum=("rating_3", "sum"),
        rating_4_sum=("rating_4", "sum"),
        rating_5_sum=("rating_5", "sum"),
    )

    monthly["period_start"] = pd.to_datetime(
        {
            "year": monthly["review_year"],
            "month": monthly["review_month"],
            "day": 1,
        }
    )

    monthly["pct_1"] = monthly["rating_1_sum"] / monthly["review_count"]
    monthly["pct_2"] = monthly["rating_2_sum"] / monthly["review_count"]
    monthly["pct_3"] = monthly["rating_3_sum"] / monthly["review_count"]
    monthly["pct_4"] = monthly["rating_4_sum"] / monthly["review_count"]
    monthly["pct_5"] = monthly["rating_5_sum"] / monthly["review_count"]

    monthly = monthly.drop(
        columns=[
            "rating_1_sum",
            "rating_2_sum",
            "rating_3_sum",
            "rating_4_sum",
            "rating_5_sum",
        ]
    )

    monthly["helpful_ratio"] = monthly["helpful_yes_sum"] / monthly["helpful_total_sum"]
    monthly.loc[monthly["helpful_total_sum"] <= 0, "helpful_ratio"] = np.nan

    lifetime = df.groupby("asin", as_index=False).agg(
        lifetime_review_count=("overall", "size"),
        lifetime_avg_rating=("overall", "mean"),
        lifetime_median_rating=("overall", "median"),
        lifetime_helpful_yes_sum=("helpful_yes", "sum"),
        lifetime_helpful_total_sum=("helpful_total", "sum"),
        lifetime_distinct_reviewers=("reviewerID", "nunique"),
    )
    lifetime["lifetime_helpful_ratio"] = (
        lifetime["lifetime_helpful_yes_sum"] / lifetime["lifetime_helpful_total_sum"]
    )
    lifetime.loc[
        lifetime["lifetime_helpful_total_sum"] <= 0, "lifetime_helpful_ratio"
    ] = np.nan

    lifetime = lifetime.drop(
        columns=["lifetime_helpful_yes_sum", "lifetime_helpful_total_sum"]
    )

    gold = monthly.merge(lifetime, on="asin", how="left")

    gold = gold.sort_values(["asin", "review_year", "review_month"]).reset_index(
        drop=True
    )

    table_out = pa.Table.from_pandas(gold, preserve_index=False)
    pq.write_table(table_out, OUT_PATH)


if __name__ == "__main__":
    main()
