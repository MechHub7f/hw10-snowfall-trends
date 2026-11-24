# Did New England get less snow?

**Short answer: no.**

Live report: https://mechhub7f.github.io/hw10-snowfall-trends/

My uncle used to say winters were not what they used to be. He was born in
1939 and died in 2024, so he saw a lot of New England winters. I used daily
snowfall records from the Global Historical Climatology Network to compare the
2000s and 2010s with 1940-1999.

## What I found

- 1940-1999 average seasonal snowfall: **72.1 inches**
- 2000-2019 average: **73.4 inches**
- Change: **+1.3 inches (+1.8%)**
- Permutation test: **p = 0.82**

The '60s and '70s ran well above average and the '80s and '90s ran below it.
The 2000s and 2010s came back to about normal. Mean snow depth was about 8%
lower recently, but that difference is small and not statistically
significant.

So the data do not back up the idea that New England snowfall has been
disappearing. If he was remembering the 1960s and 1970s, he had a point. If he
meant the whole 60 years, the numbers don't back that up.

## What is in here

- `scripts/fetch_data.py` downloads the GHCN station files and builds a small
  station-by-winter table.
- `scripts/analyze.py` computes the regional numbers and writes the report.
- `scripts/report_template.html` is the report template, with Chart.js charts.
- `docs/index.html` is the generated static report served by GitHub Pages.
- `Makefile` runs the two steps in order.

## Running it

```sh
make all
```

or:

```sh
python3 scripts/fetch_data.py
python3 scripts/analyze.py
```

The download step uses NOAA's GHCN-Daily S3 mirror. It writes
`data/processed/station_seasonal.csv`, which is gitignored. The analysis writes
`docs/index.html` and `data/results.json`. Raw station files and processed data
are not committed to the repo.

## Data and method

- Source: NOAA GHCN-Daily.
- States: Maine, New Hampshire, Vermont, Massachusetts, Rhode Island,
  Connecticut.
- Periods: winters 1940-41 through 1999-2000, and 2000-01 through 2019-20.
- A station-winter is used if at least 80% of the October-May days have a snow
  observation.
- Stations need at least 35 usable winters in the old period and 15 in the
  recent period.
- Each station is compared with its own 1940-1999 average before the regional
  average is taken.
