#!/usr/bin/env python3
"""Download GHCN-Daily snowfall data for New England and build seasonal totals."""

import csv
import io
import time
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

BASE = "https://noaa-ghcn-pds.s3.amazonaws.com/"
STATES = {"ME", "NH", "VT", "MA", "CT", "RI"}
OUT = Path("data/processed/station_seasonal.csv")


def get(url):
    last_error = None
    for attempt in range(3):
        try:
            return urllib.request.urlopen(url, timeout=120)
        except Exception as error:
            last_error = error
            time.sleep(2 + attempt * 2)
    raise last_error


def read_stations():
    stations = {}
    with get(BASE + "ghcnd-stations.txt") as response:
        for line in io.TextIOWrapper(response, encoding="utf-8"):
            state = line[38:40]
            if state in STATES:
                sid = line[0:11]
                stations[sid] = {
                    "state": state,
                    "lat": float(line[12:20]),
                    "lon": float(line[21:30]),
                    "name": line[41:71].strip(),
                }
    return stations


def read_candidates(stations):
    found = set()
    with get(BASE + "ghcnd-inventory.txt") as response:
        for line in io.TextIOWrapper(response, encoding="utf-8"):
            sid = line[0:11]
            if sid not in stations:
                continue
            element = line[31:35]
            first = int(line[36:40])
            last = int(line[41:45])
            # keep stations whose records could span both periods
            if element == "SNOW" and first <= 1945 and last >= 2018:
                found.add(sid)
    return sorted(found)


def winter_days(season):
    return (date(season + 1, 5, 31) - date(season, 10, 1)).days + 1


def process_station(sid):
    seasons = defaultdict(
        lambda: {
            "snow_total": 0.0,
            "snow_days": 0,
            "snow_n": 0,
            "snwd_sum": 0.0,
            "snwd_n": 0,
            "cover_days": 0,
        }
    )

    with get(BASE + f"csv/by_station/{sid}.csv") as response:
        reader = csv.DictReader(
            io.TextIOWrapper(response, encoding="utf-8", newline="")
        )
        for row in reader:
            element = row["ELEMENT"]
            if element not in ("SNOW", "SNWD"):
                continue
            # skip any value with a quality flag
            if row["Q_FLAG"]:
                continue
            try:
                value = float(row["DATA_VALUE"])
            except ValueError:
                continue
            if value < 0:
                continue
            if element == "SNOW" and value > 3000:
                continue
            if element == "SNWD" and value > 5000:
                continue

            day = row["DATE"]
            year = int(day[0:4])
            month = int(day[4:6])
            if month < 10 and month > 5:
                continue
            season = year if month >= 10 else year - 1
            record = seasons[season]

            if element == "SNOW":
                record["snow_total"] += value
                record["snow_n"] += 1
                if value > 0:
                    record["snow_days"] += 1
            else:
                record["snwd_sum"] += value
                record["snwd_n"] += 1
                if value > 0:
                    record["cover_days"] += 1

    return seasons


def main():
    print("Loading station metadata...")
    stations = read_stations()
    candidates = read_candidates(stations)
    print(f"{len(candidates)} candidate stations")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "station",
        "state",
        "name",
        "lat",
        "lon",
        "season",
        "snow_total_in",
        "snow_days",
        "snow_cov",
        "cover_days",
        "snwd_mean_in",
        "snwd_cov",
    ]

    with OUT.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()

        for number, sid in enumerate(candidates, 1):
            print(f"[{number}/{len(candidates)}] {sid}", flush=True)
            seasons = process_station(sid)
            meta = stations[sid]
            days = {season: winter_days(season) for season in seasons}

            for season in sorted(seasons):
                record = seasons[season]
                snow_cov = record["snow_n"] / days[season]
                snwd_cov = record["snwd_n"] / days[season]
                writer.writerow(
                    {
                        "station": sid,
                        "state": meta["state"],
                        "name": meta["name"],
                        "lat": meta["lat"],
                        "lon": meta["lon"],
                        "season": season,
                        "snow_total_in": round(record["snow_total"] / 25.4, 2)
                        if record["snow_n"]
                        else "",
                        "snow_days": record["snow_days"] if record["snow_n"] else "",
                        "snow_cov": round(snow_cov, 3) if record["snow_n"] else "",
                        "cover_days": record["cover_days"] if record["snwd_n"] else "",
                        "snwd_mean_in": round(
                            record["snwd_sum"] / record["snwd_n"] / 25.4, 2
                        )
                        if record["snwd_n"]
                        else "",
                        "snwd_cov": round(snwd_cov, 3) if record["snwd_n"] else "",
                    }
                )

    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
