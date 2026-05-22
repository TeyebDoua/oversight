import pandas as pd
from math import comb


def compute_variance(df):
    df = df.copy()
    df["variance"] = df["mgmt_value"] - df["actual_value"]
    df["variance_pct"] = (df["variance"] / df["actual_value"].replace(0, 1)) * 100

    def direction(v):
        if v > 0:
            return "over"
        elif v < 0:
            return "under"
        return "on target"

    df["direction"] = df["variance"].apply(direction)
    return df


def binomial_one_sided_pvalue(k, n, p=0.5):
    if n == 0:
        return 1.0
    if k > n:
        return 0.0
    return sum(
        comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
        for i in range(k, n + 1)
    )


def interpret_pvalue(p):
    if p < 0.05:
        return "Strong statistical evidence of directional bias"
    elif p < 0.10:
        return "Moderate statistical evidence of directional bias"
    elif p < 0.20:
        return "Weak statistical evidence; treat with caution"
    return "Pattern consistent with random estimation noise"


def detect_bias_pattern(df, materiality=0):
    results = []

    for estimate_id, group in df.groupby("estimate_id"):
        years_count = len(group)
        under_count = (group["direction"] == "under").sum()
        over_count = (group["direction"] == "over").sum()

        if under_count > over_count:
            dominant = "under"
            score = under_count / years_count
            dominant_count = int(under_count)
        elif over_count > under_count:
            dominant = "over"
            score = over_count / years_count
            dominant_count = int(over_count)
        else:
            dominant = "mixed"
            score = 0.5
            dominant_count = max(int(under_count), int(over_count))

        p_value = binomial_one_sided_pvalue(dominant_count, years_count, p=0.5)
        avg_variance_pct = group["variance_pct"].abs().mean()
        max_abs_variance = group["variance"].abs().max()
        is_material = max_abs_variance >= materiality if materiality > 0 else True

        if not is_material:
            flag = "below_materiality"
            label = f"Below materiality threshold (max variance: {max_abs_variance:,.0f})"
        elif score == 1.0 and years_count >= 4:
            flag = "red"
            label = f"{dominant.capitalize()}-estimated {dominant_count} of {years_count} years"
        elif score >= 0.75 and years_count >= 4:
            flag = "amber"
            label = f"{dominant.capitalize()}-estimated {dominant_count} of {years_count} years"
        elif avg_variance_pct > 15:
            flag = "amber"
            label = f"High average variance ({avg_variance_pct:.1f}%) with mixed direction"
        else:
            flag = "green"
            label = "No bias pattern detected"

        results.append({
            "estimate_id": estimate_id,
            "category": group["category"].iloc[0],
            "years_count": years_count,
            "under_count": int(under_count),
            "over_count": int(over_count),
            "dominant_direction": dominant,
            "pattern_score": round(score, 2),
            "avg_variance_pct": round(avg_variance_pct, 2),
            "max_abs_variance": round(max_abs_variance, 0),
            "p_value": round(p_value, 4),
            "p_interpretation": interpret_pvalue(p_value),
            "is_material": bool(is_material),
            "flag": flag,
            "pattern_label": label,
        })

    return pd.DataFrame(results)


def load_benchmark(csv_path="industry_benchmarks.csv"):
    try:
        return pd.read_csv(csv_path)
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "category", "industry_avg_variance_pct",
            "industry_red_flag_rate", "industry_n_companies", "source_note",
        ])


def compare_to_benchmark(summary, benchmark):
    if len(summary) == 0:
        return pd.DataFrame()

    company_agg = summary.groupby("category").agg(
        company_estimate_count=("estimate_id", "count"),
        company_avg_variance_pct=("avg_variance_pct", "mean"),
        company_red_flag_rate=("flag", lambda s: (s == "red").mean()),
    ).reset_index()

    merged = company_agg.merge(benchmark, on="category", how="left")

    def verdict(row):
        if pd.isna(row.get("industry_avg_variance_pct")):
            return "No benchmark available"
        variance_delta = row["company_avg_variance_pct"] - row["industry_avg_variance_pct"]
        flag_delta = row["company_red_flag_rate"] - row["industry_red_flag_rate"]
        if variance_delta > 2 and flag_delta > 0.05:
            return "Worse than industry"
        if variance_delta < -2 and flag_delta < -0.05:
            return "Better than industry"
        return "In line with industry"

    def variance_delta(row):
        if pd.isna(row.get("industry_avg_variance_pct")):
            return None
        return round(row["company_avg_variance_pct"] - row["industry_avg_variance_pct"], 2)

    def flag_rate_delta(row):
        if pd.isna(row.get("industry_red_flag_rate")):
            return None
        return round(row["company_red_flag_rate"] - row["industry_red_flag_rate"], 3)

    merged["variance_delta"] = merged.apply(variance_delta, axis=1)
    merged["flag_rate_delta"] = merged.apply(flag_rate_delta, axis=1)
    merged["verdict"] = merged.apply(verdict, axis=1)

    merged["company_avg_variance_pct"] = merged["company_avg_variance_pct"].round(2)
    merged["company_red_flag_rate"] = merged["company_red_flag_rate"].round(3)
    return merged


def load_and_analyse(csv_path, materiality=0):
    raw = pd.read_csv(csv_path)
    detailed = compute_variance(raw)
    summary = detect_bias_pattern(detailed, materiality=materiality)
    return detailed, summary