#!/usr/bin/env python3
"""Turn the station-season file into the regional results used by the report."""

import csv
import json
import random
from collections import defaultdict
from datetime import date
from pathlib import Path

INPUT = Path("data/processed/station_seasonal.csv")
RESULTS = Path("data/results.json")

OLD = (1940, 1999)
NEW = (2000, 2019)
COVERAGE = 0.80
MIN_OLD = 35
MIN_NEW = 15
BOOTSTRAPS = 5000
PERMUTATIONS = 5000

METRICS = [
    {
        "key": "snow_total_in",
        "cov": "snow_cov",
        "label": "Seasonal snowfall",
        "unit": "in",
    },
    {"key": "snow_days", "cov": "snow_cov", "label": "Snowfall days", "unit": "days"},
    {
        "key": "cover_days",
        "cov": "snwd_cov",
        "label": "Snow-cover days",
        "unit": "days",
    },
    {
        "key": "snwd_mean_in",
        "cov": "snwd_cov",
        "label": "Mean snow depth",
        "unit": "in",
    },
]

REGIONS = [("South", {"CT", "RI", "MA"}), ("North", {"VT", "NH", "ME"})]


def load_data():
    data = defaultdict(dict)
    meta = {}
    with INPUT.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            sid = row["station"]
            season = int(row["season"])
            meta[sid] = {"state": row["state"]}
            record = {}
            for key in ("snow_total_in", "snow_days", "cover_days", "snwd_mean_in"):
                record[key] = float(row[key]) if row[key] != "" else None
            for key in ("snow_cov", "snwd_cov"):
                record[key] = float(row[key]) if row[key] != "" else None
            data[sid][season] = record
    return data, meta


def mean(values):
    return sum(values) / len(values)


def eligible_stations(data, meta, metric, region=None, threshold=COVERAGE):
    stations = []
    for sid, seasons in data.items():
        if region is not None and meta[sid]["state"] not in region:
            continue
        old = [
            season
            for season in seasons
            if OLD[0] <= season <= OLD[1]
            and seasons[season][metric["key"]] is not None
            and seasons[season][metric["cov"]] >= threshold
        ]
        recent = [
            season
            for season in seasons
            if NEW[0] <= season <= NEW[1]
            and seasons[season][metric["key"]] is not None
            and seasons[season][metric["cov"]] >= threshold
        ]
        if len(old) >= MIN_OLD and len(recent) >= MIN_NEW:
            stations.append(sid)
    return stations


def bootstrap_ci(values, seed):
    rng = random.Random(seed)
    size = len(values)
    means = []
    for _ in range(BOOTSTRAPS):
        means.append(sum(rng.choices(values, k=size)) / size)
    means.sort()
    return means[int(0.025 * BOOTSTRAPS)], means[int(0.975 * BOOTSTRAPS)]


def permutation_p(old_values, new_values, seed):
    rng = random.Random(seed)
    observed = abs(mean(new_values) - mean(old_values))
    pooled = old_values + new_values
    old_size = len(old_values)
    hits = 0
    for _ in range(PERMUTATIONS):
        rng.shuffle(pooled)
        difference = abs(mean(pooled[:old_size]) - mean(pooled[old_size:]))
        if difference >= observed:
            hits += 1
    return (hits + 1) / (PERMUTATIONS + 1)


def trend_per_decade(series):
    years = [item["season"] for item in series]
    values = [item["anomaly"] for item in series]
    mean_year = mean(years)
    mean_value = mean(values)
    denominator = sum((year - mean_year) ** 2 for year in years)
    if denominator == 0:
        return 0.0
    slope = sum(
        (year - mean_year) * (value - mean_value)
        for year, value in zip(years, values)
    ) / denominator
    return slope * 10


def compute(data, metric, stations, threshold=COVERAGE):
    if len(stations) < 5:
        return None

    baseline = {}
    for sid in stations:
        values = [
            data[sid][season][metric["key"]]
            for season in data[sid]
            if OLD[0] <= season <= OLD[1]
            and data[sid][season][metric["key"]] is not None
            and data[sid][season][metric["cov"]] >= threshold
        ]
        if values:
            baseline[sid] = mean(values)

    series = []
    for season in range(1940, 2020):
        values = []
        for sid in stations:
            record = data[sid].get(season)
            if record is None or sid not in baseline:
                continue
            value = record[metric["key"]]
            coverage = record[metric["cov"]]
            if value is None or coverage is None or coverage < threshold:
                continue
            values.append(value - baseline[sid])
        if len(values) >= 10:
            series.append(
                {"season": season, "anomaly": mean(values), "n": len(values)}
            )

    old_values = [
        item["anomaly"] for item in series if OLD[0] <= item["season"] <= OLD[1]
    ]
    recent_values = [
        item["anomaly"] for item in series if NEW[0] <= item["season"] <= NEW[1]
    ]
    if not old_values or not recent_values:
        return None

    old_mean = mean(baseline.values())
    station_recent = {}
    below = 0
    for sid in stations:
        recent = [
            data[sid][season][metric["key"]]
            for season in data[sid]
            if NEW[0] <= season <= NEW[1]
            and data[sid][season][metric["key"]] is not None
            and data[sid][season][metric["cov"]] >= threshold
        ]
        if recent and sid in baseline:
            station_recent[sid] = mean(recent)
            if station_recent[sid] < baseline[sid]:
                below += 1
    if not station_recent:
        return None

    new_mean = mean(station_recent.values())
    change = new_mean - old_mean
    ci_low, ci_high = bootstrap_ci(recent_values, 1)

    return {
        "n": len(stations),
        "old": old_mean,
        "new": new_mean,
        "change": change,
        "pct": 100 * change / old_mean if old_mean else 0.0,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "p": permutation_p(old_values, recent_values, 2),
        "trend": trend_per_decade(series),
        "below": below,
        "series": [
            {"season": item["season"], "anomaly": round(item["anomaly"], 2)}
            for item in series
        ],
    }


def decadal_means(series):
    output = []
    for decade in range(1940, 2020, 10):
        values = [
            item["anomaly"]
            for item in series
            if decade <= item["season"] <= decade + 9
        ]
        if values:
            output.append(
                {"decade": f"{decade}s", "anomaly": round(mean(values), 2)}
            )
    return output


def round_stats(stats):
    return {
        "n": stats["n"],
        "old": round(stats["old"], 2),
        "new": round(stats["new"], 2),
        "change": round(stats["change"], 2),
        "pct": round(stats["pct"], 1),
        "ci_low": round(stats["ci_low"], 2),
        "ci_high": round(stats["ci_high"], 2),
        "p": round(stats["p"], 3),
        "trend": round(stats["trend"], 2),
        "below": stats["below"],
    }


def main():
    data, meta = load_data()

    summary = []
    series = {}
    decadal = {}

    for metric in METRICS:
        stations = eligible_stations(data, meta, metric)
        stats = compute(data, metric, stations)
        if stats is None:
            continue
        summary.append(
            {
                "key": metric["key"],
                "label": metric["label"],
                "unit": metric["unit"],
                **round_stats(stats),
            }
        )
        series[metric["key"]] = stats["series"]
        decadal[metric["key"]] = decadal_means(stats["series"])

    subregions = []
    for metric in METRICS:
        for region_name, states in REGIONS:
            stations = eligible_stations(data, meta, metric, region=states)
            stats = compute(data, metric, stations)
            if stats is None:
                continue
            subregions.append(
                {
                    "label": metric["label"],
                    "unit": metric["unit"],
                    "region": region_name,
                    "n": stats["n"],
                    "change": round(stats["change"], 2),
                    "pct": round(stats["pct"], 1),
                    "p": round(stats["p"], 3),
                }
            )

    sensitivity = []
    for threshold in (0.70, 0.80, 0.90):
        for metric in METRICS:
            stations = eligible_stations(data, meta, metric, threshold=threshold)
            stats = compute(
                data,
                metric,
                stations,
                threshold=threshold,
            )
            if stats is None:
                continue
            sensitivity.append(
                {
                    "label": metric["label"],
                    "unit": metric["unit"],
                    "threshold": threshold,
                    "n": stats["n"],
                    "change": round(stats["change"], 2),
                    "pct": round(stats["pct"], 1),
                    "p": round(stats["p"], 3),
                }
            )

    results = {
        "generated": date.today().isoformat(),
        "stations": len(meta),
        "summary": summary,
        "series": series,
        "decadal": decadal,
        "subregions": subregions,
        "sensitivity": sensitivity,
    }

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"Saved {RESULTS}")
    for item in summary:
        print(
            f"{item['label']}: {item['old']:.1f} -> {item['new']:.1f} "
            f"{item['unit']} ({item['pct']:+.1f}%), p={item['p']:.3f}, n={item['n']}"
        )


if __name__ == "__main__":
    main()
