#!/usr/bin/env python3
"""Field readings: render the public activity of a GitHub user into a dark SVG chart.

Free-only: uses the public GitHub REST API (no token) and Python's standard library.
Output: assets/metrics.svg
"""

import json
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone

USER = sys.argv[1] if len(sys.argv) > 1 else "jarlelauch"
OUT = "assets/metrics.svg"
DAYS = 14

W, H, PAD_L, PAD_R, PAD_T, PAD_B = 1160, 212, 26, 22, 34, 40
GOLD = "#e8b95c"
ROSE = "#c0487e"
INK = "#e7d5ae"


def fetch(url: str) -> dict | list:
    req = urllib.request.Request(url, headers={"User-Agent": "field-readings/1.0", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def main() -> int:
    try:
        events = fetch(f"https://api.github.com/users/{USER}/events/public?per_page=100")
    except Exception:
        return 0  # keep the previous chart on transient failures
    if not isinstance(events, list) or not events:
        return 0

    today = datetime.now(timezone.utc).date()
    bins = {today - timedelta(days=i): 0 for i in range(DAYS - 1, -1, -1)}
    for ev in events:
        day = datetime.fromisoformat(ev.get("created_at", "").replace("Z", "+00:00")).date()
        if day in bins:
            bins[day] += 1

    values = list(bins.values())
    peak = max(values) or 1
    plot_w = W - PAD_L - PAD_R
    plot_h = H - PAD_T - PAD_B
    bw = plot_w / DAYS
    max_y = max(4, (peak + 1) // 2 * 2)

    bars = []
    labels = []
    for i, (day, v) in enumerate(bins.items()):
        h = max(1, round(plot_h * v / max_y))
        x = PAD_L + i * bw + bw * 0.16
        w = bw * 0.68
        y = PAD_T + plot_h - h
        gold = f"url(#bar)"
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="4" fill="{gold}" opacity=".88"/>')
        labels.append(f'<text x="{PAD_L + i * bw + bw / 2:.1f}" y="{H - 16}" font-size="10" fill="{INK}" text-anchor="middle" opacity=".72">{day.day}</text>')

    grid = []
    for step in range(0, 5):
        yy = PAD_T + plot_h - step * plot_h / 4
        grid.append(f'<line x1="{PAD_L}" y1="{yy:.1f}" x2="{W - PAD_R}" y2="{yy:.1f}" stroke="{INK}" stroke-opacity=".09" stroke-width=".6"/>')
        grid.append(f'<text x="{PAD_L - 8}" y="{yy + 3:.1f}" font-size="9" fill="{INK}" text-anchor="end" opacity=".6">{int(max_y * step / 4)}</text>')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
  <title id="t">Field readings: public activity for {USER}</title>
  <desc id="d">Daily public event count for {USER} over the past {DAYS} days, refreshed daily by GitHub Actions.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#07070e"/><stop offset=".55" stop-color="#0d0a16"/><stop offset="1" stop-color="#06060b"/>
    </linearGradient>
    <linearGradient id="bar" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{GOLD}"/><stop offset="1" stop-color="{ROSE}"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/>
  {"".join(grid)}
  {"".join(bars)}
  <text x="{PAD_L}" y="21" font-size="12" fill="{GOLD}" font-family="Georgia, serif">FIELD READINGS / {USER} · PUBLIC SIGNAL · PAST {DAYS} DAYS</text>
  <text x="{W - PAD_R}" y="21" font-size="10" fill="{ROSE}" text-anchor="end" font-family="Georgia, serif">EVENT-HORIZON TELEMETRY</text>
  {"".join(labels)}
  <text x="{W / 2}" y="{H - 16}" font-size="9" fill="{ROSE}" text-anchor="middle" opacity=".8">AUTO-REFRESHED DAILY BY GITHUB ACTIONS · {today.isoformat()} UTC</text>
</svg>
"""
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())