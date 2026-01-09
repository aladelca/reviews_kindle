import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds

RAW_PATH = Path("data/kindle_reviews.json")
OUT_DIR = Path("data/silver/kindle_reviews")
DQ_REPORT_PATH = Path("docs/dq_kindle_reviews_silver.md")
CHUNK_SIZE = 200_000

MIN_REVIEW_TS = pd.Timestamp("1997-01-01", tz="UTC")


def parse_helpful(value):
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return value[0], value[1]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return np.nan, np.nan
        if isinstance(parsed, (list, tuple)) and len(parsed) == 2:
            return parsed[0], parsed[1]
    return np.nan, np.nan


def clean_text(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype("string")
        .str.replace(r"[\r\t]+", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    return cleaned.replace({"": pd.NA})


def accumulate_nulls(null_counts: dict, df: pd.DataFrame) -> None:
    for col in df.columns:
        null_counts[col] += int(df[col].isna().sum())


def update_value_counts(counter: dict, series: pd.Series) -> None:
    counts = series.value_counts(dropna=False)
    for key, value in counts.items():
        counter[key] += int(value)


def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw file not found: {RAW_PATH}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DQ_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    dq = {
        "total_read": 0,
        "total_valid": 0,
        "total_discarded": 0,
        "outlier_overall": 0,
        "outlier_helpful_negative": 0,
        "outlier_helpful_yes_gt_total": 0,
        "outlier_review_ts_null": 0,
        "outlier_review_ts_out_of_range": 0,
        "null_counts": defaultdict(int),
        "overall_dist": defaultdict(int),
    }

    max_review_ts = pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=1)

    reader = pd.read_json(RAW_PATH, lines=True, chunksize=CHUNK_SIZE)
    for chunk in reader:
        dq["total_read"] += len(chunk)

        for col in ["reviewerName", "reviewText", "summary"]:
            if col in chunk.columns:
                chunk[col] = clean_text(chunk[col])

        if "helpful" in chunk.columns:
            helpful_pairs = chunk["helpful"].apply(parse_helpful)
            chunk["helpful_yes"] = helpful_pairs.apply(lambda x: x[0])
            chunk["helpful_total"] = helpful_pairs.apply(lambda x: x[1])

        if "overall" in chunk.columns:
            chunk["overall"] = pd.to_numeric(chunk["overall"], errors="coerce")

        if "unixReviewTime" in chunk.columns:
            chunk["unixReviewTime"] = pd.to_numeric(
                chunk["unixReviewTime"], errors="coerce"
            )
            chunk["review_ts"] = pd.to_datetime(
                chunk["unixReviewTime"], unit="s", errors="coerce", utc=True
            )

        if "reviewTime" in chunk.columns:
            chunk["review_date"] = pd.to_datetime(
                chunk["reviewTime"], errors="coerce"
            ).dt.date

        if "review_ts" in chunk.columns:
            chunk["review_year"] = (
                chunk["review_ts"].dt.year.fillna(-1).astype("int16")
            )
            chunk["review_month"] = (
                chunk["review_ts"].dt.month.fillna(-1).astype("int8")
            )
        else:
            chunk["review_year"] = -1
            chunk["review_month"] = -1

        accumulate_nulls(dq["null_counts"], chunk)

        if "overall" in chunk.columns:
            update_value_counts(dq["overall_dist"], chunk["overall"])
            outlier_overall = chunk["overall"].notna() & (
                (chunk["overall"] < 1) | (chunk["overall"] > 5)
            )
            dq["outlier_overall"] += int(outlier_overall.sum())

        if "helpful_yes" in chunk.columns and "helpful_total" in chunk.columns:
            helpful_yes = pd.to_numeric(chunk["helpful_yes"], errors="coerce")
            helpful_total = pd.to_numeric(chunk["helpful_total"], errors="coerce")
            dq["outlier_helpful_negative"] += int(
                ((helpful_yes < 0) | (helpful_total < 0)).sum()
            )
            dq["outlier_helpful_yes_gt_total"] += int(
                (helpful_yes > helpful_total).sum()
            )

        if "review_ts" in chunk.columns:
            review_ts_null = chunk["review_ts"].isna()
            dq["outlier_review_ts_null"] += int(review_ts_null.sum())
            review_ts_out = (~review_ts_null) & (
                (chunk["review_ts"] < MIN_REVIEW_TS) | (chunk["review_ts"] > max_review_ts)
            )
            dq["outlier_review_ts_out_of_range"] += int(review_ts_out.sum())

        required_cols = ["reviewerID", "asin", "overall"]
        valid_mask = pd.Series(True, index=chunk.index)
        for col in required_cols:
            if col in chunk.columns:
                valid_mask &= chunk[col].notna()

        if "overall" in chunk.columns:
            valid_mask &= (chunk["overall"] >= 1) & (chunk["overall"] <= 5)

        cleaned = chunk[valid_mask].copy()
        dq["total_valid"] += len(cleaned)
        dq["total_discarded"] += len(chunk) - len(cleaned)

        table = pa.Table.from_pandas(cleaned, preserve_index=False)
        ds.write_dataset(
            table,
            base_dir=str(OUT_DIR),
            format="parquet",
            partitioning=["review_year", "review_month"],
            existing_data_behavior="overwrite_or_ignore",
        )

    total_read = dq["total_read"]
    def pct(value):
        return 0 if total_read == 0 else (value / total_read) * 100

    lines = [
        "# Data Quality Report - kindle_reviews (silver)",
        "",
        f"Generated at: {datetime.utcnow().isoformat()}Z",
        "",
        "## Totals",
        f"- Total read: {dq['total_read']}",
        f"- Total valid: {dq['total_valid']}",
        f"- Total discarded: {dq['total_discarded']}",
        "",
        "## Nulls by column",
    ]

    for col, count in sorted(dq["null_counts"].items()):
        lines.append(f"- {col}: {count} ({pct(count):.2f}%)")

    lines += [
        "",
        "## Outliers",
        f"- overall_out_of_range: {dq['outlier_overall']} ({pct(dq['outlier_overall']):.2f}%)",
        f"- helpful_negative: {dq['outlier_helpful_negative']} ({pct(dq['outlier_helpful_negative']):.2f}%)",
        f"- helpful_yes_gt_total: {dq['outlier_helpful_yes_gt_total']} ({pct(dq['outlier_helpful_yes_gt_total']):.2f}%)",
        f"- review_ts_null: {dq['outlier_review_ts_null']} ({pct(dq['outlier_review_ts_null']):.2f}%)",
        f"- review_ts_out_of_range: {dq['outlier_review_ts_out_of_range']} ({pct(dq['outlier_review_ts_out_of_range']):.2f}%)",
        "",
        "## Overall distribution",
    ]

    for key, count in sorted(dq["overall_dist"].items(), key=lambda x: (str(x[0]))):
        lines.append(f"- {key}: {count} ({pct(count):.2f}%)")

    DQ_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
