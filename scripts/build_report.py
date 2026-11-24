#!/usr/bin/env python3
"""Build the static report page from the regional results."""

import json
from html import escape
from pathlib import Path

RESULTS = Path("data/results.json")
OUTPUT = Path("docs/index.html")


def fmt(value, digits=1):
    return f"{value:.{digits}f}"


def signed(value, digits=1):
    if abs(round(value, digits)) == 0:
        return f"{0:.{digits}f}"
    return f"{value:+.{digits}f}"


def tick_label(value):
    if abs(value) < 0.5:
        return "0"
    return f"{value:.0f}"


def line_chart(series, y_label, width=720, height=320, color="#3f6491"):
    if not series:
        return '<p class="note">No data for this chart.</p>'
    if len(series) < 2:
        return '<p class="note">Not enough data for this chart.</p>'
    years = [item["season"] for item in series]
    values = [item["anomaly"] for item in series]
    x_min, x_max = min(years), max(years)
    y_min, y_max = min(0, min(values)), max(0, max(values))
    padding = (y_max - y_min) * 0.10 or 1
    y_min -= padding
    y_max += padding

    left, right, top, bottom = 58, 18, 30, 44
    plot_w = width - left - right
    plot_h = height - top - bottom

    def x(year):
        return left + (year - x_min) / (x_max - x_min) * plot_w

    def y(value):
        return top + (y_max - value) / (y_max - y_min) * plot_h

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{escape(y_label)}">',
        f"<title>{escape(y_label)}</title>",
        f'<text x="{left}" y="16" font-size="12" fill="#222">{escape(y_label)}</text>',
    ]

    for step in range(5):
        value = y_min + (y_max - y_min) * step / 4
        parts.append(
            f'<line x1="{left}" y1="{y(value):.1f}" x2="{left + plot_w}" '
            f'y2="{y(value):.1f}" stroke="#e8e8e8" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{left - 8}" y="{y(value) + 4:.1f}" text-anchor="end" '
            f'font-size="11" fill="#666">{tick_label(value)}</text>'
        )

    tick_years = [year for year in range(1940, 2021, 10) if x_min <= year <= x_max]
    if x_min not in tick_years:
        tick_years.insert(0, x_min)
    if x_max not in tick_years:
        tick_years.append(x_max)

    for year in tick_years:
        parts.append(
            f'<line x1="{x(year):.1f}" y1="{top}" x2="{x(year):.1f}" '
            f'y2="{top + plot_h}" stroke="#f2f2f2" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x(year):.1f}" y="{height - 20}" text-anchor="middle" '
            f'font-size="11" fill="#666">{year}</text>'
        )

    parts.append(
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" '
        f'stroke="#999" stroke-width="1"/>'
    )
    parts.append(
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" '
        f'y2="{top + plot_h}" stroke="#999" stroke-width="1"/>'
    )
    parts.append(
        f'<line x1="{left}" y1="{y(0):.1f}" x2="{left + plot_w}" '
        f'y2="{y(0):.1f}" stroke="#999" stroke-width="1" stroke-dasharray="4 4"/>'
    )
    parts.append(
        f'<text x="{left + plot_w / 2:.1f}" y="{height - 4}" text-anchor="middle" '
        f'font-size="12" fill="#444">Winter starting year</text>'
    )

    points = " ".join(f"{x(year):.1f},{y(value):.1f}" for year, value in zip(years, values))
    parts.append(
        f'<polyline fill="none" stroke="{color}" stroke-width="1.5" points="{points}"/>'
    )
    for year, value in zip(years, values):
        parts.append(
            f'<circle cx="{x(year):.1f}" cy="{y(value):.1f}" r="1.8" fill="{color}"/>'
        )

    averages = []
    for index in range(9, len(series)):
        chunk = series[index - 9:index + 1]
        averages.append(
            (
                series[index]["season"],
                sum(entry["anomaly"] for entry in chunk) / 10,
            )
        )
    if averages:
        average_points = " ".join(
            f"{x(year):.1f},{y(value):.1f}" for year, value in averages
        )
        parts.append(
            f'<polyline fill="none" stroke="#222" stroke-width="2.2" '
            f'points="{average_points}"/>'
        )

    parts.append("</svg>")
    return "".join(parts)


def bar_chart(data, y_label, width=720, height=320):
    if not data:
        return '<p class="note">No data for this chart.</p>'
    values = [item["anomaly"] for item in data]
    y_min, y_max = min(0, min(values)), max(0, max(values))
    padding = (y_max - y_min) * 0.10 or 1
    y_min -= padding
    y_max += padding

    left, right, top, bottom = 58, 18, 30, 44
    plot_w = width - left - right
    plot_h = height - top - bottom

    def y(value):
        return top + (y_max - value) / (y_max - y_min) * plot_h

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{escape(y_label)}">',
        f"<title>{escape(y_label)}</title>",
        f'<text x="{left}" y="16" font-size="12" fill="#222">{escape(y_label)}</text>',
    ]

    for step in range(5):
        value = y_min + (y_max - y_min) * step / 4
        parts.append(
            f'<line x1="{left}" y1="{y(value):.1f}" x2="{left + plot_w}" '
            f'y2="{y(value):.1f}" stroke="#e8e8e8" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{left - 8}" y="{y(value) + 4:.1f}" text-anchor="end" '
            f'font-size="11" fill="#666">{tick_label(value)}</text>'
        )

    slot = plot_w / len(data)
    bar_width = slot * 0.62
    for index, item in enumerate(data):
        center = left + slot * (index + 0.5)
        value = item["anomaly"]
        top_y = min(y(0), y(value))
        height_px = abs(y(value) - y(0))
        color = "#3f6491" if value >= 0 else "#a95845"
        parts.append(
            f'<rect x="{center - bar_width / 2:.1f}" y="{top_y:.1f}" '
            f'width="{bar_width:.1f}" height="{height_px:.1f}" fill="{color}"/>'
        )
        parts.append(
            f'<text x="{center:.1f}" y="{height - 20}" text-anchor="middle" '
            f'font-size="11" fill="#666">{escape(item["decade"])}</text>'
        )

    parts.append(
        f'<line x1="{left}" y1="{y(0):.1f}" x2="{left + plot_w}" '
        f'y2="{y(0):.1f}" stroke="#555" stroke-width="1"/>'
    )
    parts.append(
        f'<text x="{left + plot_w / 2:.1f}" y="{height - 4}" text-anchor="middle" '
        f'font-size="12" fill="#444">Decade</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def summary_table(summary):
    rows = []
    for item in summary:
        rows.append(
            "<tr>"
            f"<td>{escape(item['label'])}</td>"
            f"<td>{fmt(item['old'])} {escape(item['unit'])}</td>"
            f"<td>{fmt(item['new'])} {escape(item['unit'])}</td>"
            f"<td>{signed(item['change'])} {escape(item['unit'])} "
            f"({signed(item['pct'])}%)</td>"
            f"<td>{signed(item['ci_low'])} to {signed(item['ci_high'])} "
            f"{escape(item['unit'])}</td>"
            f"<td>{item['p']:.3f}</td>"
            f"<td>{signed(item['trend'])} {escape(item['unit'])}/decade</td>"
            "</tr>"
        )
    return "".join(rows)


def subregion_table(subregions):
    rows = []
    for item in subregions:
        rows.append(
            "<tr>"
            f"<td>{escape(item['label'])}</td>"
            f"<td>{escape(item['region'])}</td>"
            f"<td>{item['n']}</td>"
            f"<td>{signed(item['change'])} {escape(item['unit'])} "
            f"({signed(item['pct'])}%)</td>"
            f"<td>{item['p']:.3f}</td>"
            "</tr>"
        )
    return "".join(rows)


def sensitivity_table(sensitivity):
    rows = []
    for item in sensitivity:
        rows.append(
            "<tr>"
            f"<td>{escape(item['label'])}</td>"
            f"<td>{round(item['threshold'] * 100)}%</td>"
            f"<td>{item['n']}</td>"
            f"<td>{signed(item['change'])} {escape(item['unit'])} "
            f"({signed(item['pct'])}%)</td>"
            f"<td>{item['p']:.3f}</td>"
            "</tr>"
        )
    return "".join(rows)


def build_page(results):
    by_key = {item["key"]: item for item in results["summary"]}
    if "snow_total_in" not in by_key or not results["series"].get("snow_total_in"):
        raise SystemExit("No snowfall results. Run fetch_data.py and analyze.py first.")
    snow = by_key["snow_total_in"]
    depth = by_key.get("snwd_mean_in")

    snow_chart = line_chart(results["series"]["snow_total_in"], "Snowfall anomaly (inches)")
    decade_data = results["decadal"].get("snow_total_in")
    decade_chart = (
        bar_chart(decade_data, "Snowfall anomaly (inches)")
        if decade_data
        else '<p class="note">No decadal data for this chart.</p>'
    )
    cover_series = results["series"].get("cover_days")
    cover_chart = (
        line_chart(
            cover_series,
            "Snow-cover anomaly (days)",
            color="#5d7f5a",
        )
        if cover_series
        else '<p class="note">No snow-cover data for this chart.</p>'
    )

    station_note = (
        f"{snow['below']} of {snow['n']} snowfall stations had a lower "
        "2000-2019 average than their own 1940-1999 average."
    )

    css = """
    :root {
      --ink: #222;
      --muted: #666;
      --rule: #ddd;
      --blue: #3f6491;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #fff;
      color: var(--ink);
      font-family: Georgia, "Times New Roman", serif;
      line-height: 1.55;
    }
    main {
      max-width: 780px;
      margin: 0 auto;
      padding: 40px 22px 60px;
    }
    .kicker {
      margin: 0 0 8px;
      color: var(--muted);
      font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
      font-size: 13px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    h1 {
      margin: 0 0 6px;
      font-size: 2.1rem;
      line-height: 1.15;
      font-weight: normal;
    }
    .byline {
      margin: 0 0 34px;
      color: var(--muted);
      font-size: 14px;
    }
    h2 {
      margin: 38px 0 12px;
      font-size: 1.35rem;
      font-weight: normal;
      border-bottom: 1px solid var(--rule);
      padding-bottom: 6px;
    }
    p { margin: 0 0 14px; }
    .answer h2 {
      margin-top: 0;
      border: 0;
      padding: 0;
      font-size: 3.2rem;
      font-weight: bold;
      line-height: 1;
    }
    .answer p { font-size: 1.08rem; }
    .stats {
      display: flex;
      flex-wrap: wrap;
      gap: 10px 30px;
      margin: 20px 0 8px;
      padding: 14px 0;
      border-top: 1px solid var(--rule);
      border-bottom: 1px solid var(--rule);
    }
    .stats div { min-width: 150px; }
    .stat-label {
      display: block;
      color: var(--muted);
      font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .stat-value { display: block; font-size: 1.25rem; }
    .chart { margin: 18px 0 8px; }
    .chart svg { width: 100%; height: auto; display: block; }
    .legend {
      margin: 4px 0 0;
      color: var(--muted);
      font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
      font-size: 12px;
    }
    .legend span {
      display: inline-block;
      width: 18px;
      height: 3px;
      margin-right: 5px;
      vertical-align: middle;
    }
    .legend .blue { background: var(--blue); }
    .legend .dark { background: #222; }
    .legend .grey { background: #999; }
    .caption {
      color: var(--muted);
      font-size: 13.5px;
      line-height: 1.45;
    }
    .table-wrap { overflow-x: auto; margin: 14px 0 10px; }
    table {
      width: 100%;
      border-collapse: collapse;
      font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
      font-size: 13px;
    }
    th, td {
      padding: 7px 8px;
      border-bottom: 1px solid var(--rule);
      text-align: left;
      vertical-align: top;
      white-space: nowrap;
    }
    th {
      color: var(--muted);
      font-weight: 600;
      background: #fafafa;
    }
    .note {
      color: var(--muted);
      font-size: 13.5px;
    }
    a { color: var(--blue); }
    footer {
      margin-top: 44px;
      padding-top: 14px;
      border-top: 1px solid var(--rule);
      color: var(--muted);
      font-size: 13px;
    }
    @media (max-width: 520px) {
      h1 { font-size: 1.7rem; }
      .answer h2 { font-size: 2.6rem; }
    }
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Did New England Get Less Snow?</title>
<style>{css}</style>
</head>
<body>
<main>
  <p class="kicker">HW10 &middot; Snowfall Trends</p>
  <h1>Did New England get less snow?</h1>
  <p class="byline">Christian Dow &middot; report generated {results['generated']}</p>

  <section class="answer">
    <h2>No.</h2>
    <p>
      My uncle complained for years that winters were not what they used to be.
      He was born in 1939 and died in 2024, so he saw a lot of New England snow.
      I used daily records from the Global Historical Climatology Network to
      compare the 2000s and 2010s with 1940&ndash;1999. Seasonal snowfall did
      not go down.
    </p>
    <p>
      The 1940&ndash;1999 average was <strong>{fmt(snow['old'])} in</strong> per
      winter. The 2000&ndash;2019 average was <strong>{fmt(snow['new'])} in</strong>.
      That is a change of <strong>{signed(snow['change'])} in</strong>
      ({signed(snow['pct'])}%). The 95% bootstrap range for the recent anomaly is
      <strong>{signed(snow['ci_low'])} to {signed(snow['ci_high'])} in</strong>,
      and a permutation test gives p = <strong>{snow['p']:.3f}</strong>. The
      difference is small enough to be noise.
    </p>
    <div class="stats">
      <div><span class="stat-label">1940&ndash;1999</span><span class="stat-value">{fmt(snow['old'])} in</span></div>
      <div><span class="stat-label">2000&ndash;2019</span><span class="stat-value">{fmt(snow['new'])} in</span></div>
      <div><span class="stat-label">Change</span><span class="stat-value">{signed(snow['change'])} in</span></div>
    </div>
    <p class="note">{escape(station_note)}</p>
    <p class="note">
      A winter is counted by its starting year, so 2000 means the 2000&ndash;01 winter.
      Snowfall is measured in inches of new snow.
    </p>
  </section>

  <section>
    <h2>What I did</h2>
    <p>
      I started with {results['stations']} stations that had snowfall records in
      the six states. I kept the ones with records in both periods and enough
      observations to trust a seasonal total. A station-winter only counts if at
      least 80% of the October&ndash;May days have a snow observation. That left
      {snow['n']} stations for snowfall and {depth['n'] if depth else 0} for snow
      depth.
    </p>
    <p>
      For each station I added up the winter snowfall, then compared every
      station to its own 1940&ndash;1999 average. This keeps one snowy spot from
      dominating the regional number just because it is snowy. The regional
      value is the average of those station anomalies.
    </p>
  </section>

  <section>
    <h2>Snowfall over time</h2>
    <div class="chart">{snow_chart}</div>
    <div class="legend">
      <span class="blue"></span>winter
      &nbsp; <span class="dark"></span>10-year average
      &nbsp; <span class="grey"></span>1940&ndash;1999 baseline
    </div>
    <p class="caption">
      Each blue point is one winter compared with the station&rsquo;s
      1940&ndash;1999 average. The dark line is a 10-year running average. The
      dashed line is the old baseline. The recent winters scatter around zero,
      and the line just wobbles.
    </p>
  </section>

  <section>
    <h2>Decade by decade</h2>
    <div class="chart">{decade_chart}</div>
    <p class="caption">
      This is where the memory comes from. The 1960s and 1970s were well above
      average, the 1980s and 1990s below it, and the 2000s and 2010s back
      around normal.
    </p>
  </section>

  <section>
    <h2>Snow depth and cover</h2>
    <div class="chart">{cover_chart}</div>
    <div class="legend">
      <span class="blue" style="background:#5d7f5a"></span>snow-cover days
      &nbsp; <span class="dark"></span>10-year average
      &nbsp; <span class="grey"></span>1940&ndash;1999 baseline
    </div>
    <p class="caption">
      Snow depth is a different measure. The chart shows snow-cover days; the
      table below also includes average snow depth. Snow depth was slightly
      lower recently, but cover days were basically flat. Either way, the change
      is small and the uncertainty is large. That hints at a decline, but the
      signal is too noisy to trust.
    </p>
  </section>

  <section>
    <h2>Numbers</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Measure</th>
            <th>1940&ndash;1999</th>
            <th>2000&ndash;2019</th>
            <th>Change</th>
            <th>95% range (anomaly)</th>
            <th>p</th>
            <th>Trend / decade</th>
          </tr>
        </thead>
        <tbody>{summary_table(results['summary'])}</tbody>
      </table>
    </div>
    <p class="note">
      Positive changes mean more snow or more days in 2000&ndash;2019. The change
      column is the difference between the station averages. The 95% range and
      p-value are for the regional winter anomaly, not a confidence interval
      for the station-mean change. The trend is a straight line through the
      whole record, so it is sensitive to the very snowy 1960s and 1970s.
    </p>
  </section>

  <section>
    <h2>Does the answer hold up?</h2>
    <p>
      I split the region into southern New England (Connecticut, Rhode Island,
      Massachusetts) and northern New England (Vermont, New Hampshire, Maine).
      I also changed the coverage cutoff. These checks don't show a real drop
      in snowfall.
    </p>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Measure</th>
            <th>Area</th>
            <th>Stations</th>
            <th>Change</th>
            <th>p</th>
          </tr>
        </thead>
        <tbody>{subregion_table(results['subregions'])}</tbody>
      </table>
    </div>
    <p class="note">
      Southern New England did not have enough long snow-depth stations to
      report those two measures, so the southern rows are missing.
    </p>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Measure</th>
            <th>Coverage cutoff</th>
            <th>Stations</th>
            <th>Change</th>
            <th>p</th>
          </tr>
        </thead>
        <tbody>{sensitivity_table(results['sensitivity'])}</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>What this means</h2>
    <p>
      I do not think my uncle was making things up. The 1960s and 1970s really
      were snowy in this record, and if those are the winters he was thinking
      of, he has a point. But that 60-year stretch includes the mild '80s and
      '90s too, and against the whole thing the 2000s and 2010s come out about
      average.
    </p>
    <p>
      I would tell my uncle he was wrong about the trend, at least for snowfall.
      New England did not get less snow in the seasonal totals. Snow depth may
      be inching down, but the data are too weak to make much of it.
    </p>
  </section>

  <section>
    <h2>Limits</h2>
    <p>
      Station records are not perfect. Observers change over time and stations
      get moved. Measuring snow in wind is always going to be rough. The network
      is not spread evenly across New England, and the snow-depth record is
      shorter than the snowfall record. I used long-record stations to limit
      those problems, but I cannot make them disappear. This is a regional
      average, so one town can still have a very different run of winters.
    </p>
  </section>

  <section>
    <h2>Data and code</h2>
    <p>
      Data come from NOAA&rsquo;s Global Historical Climatology Network Daily
      (GHCN-Daily), downloaded from the NOAA S3 mirror. The Python scripts
      rebuild the station-season file, compute the results, and generate this
      page. Raw data files are not stored in the repo.
    </p>
    <p>
      The report page is built and deployed by GitHub Actions from the Python
      scripts. The code is at
      <a href="https://github.com/MechHub7f/hw10-snowfall-trends">github.com/MechHub7f/hw10-snowfall-trends</a>.
    </p>
  </section>

  <footer>
    HW10 &middot; Snowfall Trends. Analysis ends with the 2019&ndash;20 winter.
  </footer>
</main>
</body>
</html>
"""


def main():
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    page = build_page(results)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()
