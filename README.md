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

The data do not show New England snowfall disappearing. If he was remembering
the 1960s and 1970s, he had a point. If he meant the whole 60 years, the
numbers say otherwise.

## What is in here

- `scripts/fetch_data.py` downloads the GHCN station files and builds a small
  station-by-winter table.
- `scripts/analyze.py` computes the regional numbers and writes
  `data/results.json`.
- `scripts/build_report.py` turns those results into the report page, with
  inline SVG charts. No JavaScript and no chart library.
- `.github/workflows/pages.yml` runs the three scripts and deploys the page to
  GitHub Pages.
- `docs/index.html` is the generated report page. It is gitignored because the
  workflow rebuilds it.

## Running it

```sh
python3 scripts/fetch_data.py
python3 scripts/analyze.py
python3 scripts/build_report.py
```

Then open `docs/index.html`. The download step uses NOAA's GHCN-Daily S3
mirror. Raw station files, `data/processed/station_seasonal.csv`,
`data/results.json`, and the generated page are not committed.

## Data and method

- Source: NOAA's GHCN-Daily.
- States: Maine, New Hampshire, Vermont, Massachusetts, Rhode Island,
  Connecticut.
- Periods: winters 1940-41 through 1999-2000, and 2000-01 through 2019-20.
- A station-winter is used if at least 80% of the October-May days have a snow
  observation.
- Stations need at least 35 usable winters in the old period and 15 in the
  recent period.
- I only downloaded stations whose inventory showed SNOW data from at least
  1945 to 2018, so the station could plausibly cover both periods.
- Each station is compared with its own 1940-1999 average before the regional
  average is taken.
