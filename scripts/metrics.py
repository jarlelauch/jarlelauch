#!/usr/bin/env python3
"""Field readings: render public signal + language spectra into dark SVG charts.

Free-only: public GitHub REST API (no token) + Python standard library.
Outputs: assets/metrics.svg (signal) and assets/top-langs.svg (language mass).
"""

import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

USER = sys.argv[1] if len(sys.argv) > 1 else "jarlelauch"
DAYS = 14
W, H, PL, PR, PT, PB = 1160, 212, 30, 26, 30, 36
GOLD, ROSE, INK = "#e8b95c", "#c0487e", "#e7d5ae"
OUT_SIGNAL, OUT_LANGS = "assets/metrics.svg", "assets/top-langs.svg"

_BG = ('<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
       '<stop offset="0" stop-color="#07070e"/><stop offset=".55" stop-color="#0d0a16"/>'
       '<stop offset="1" stop-color="#06060b"/></linearGradient>')
_BARS = ('<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{GOLD}"/><stop offset="1" stop-color="{ROSE}"/></linearGradient>')


def fetch(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "field-readings/1.0", "Accept": "application/vnd.github+json"}
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.load(resp)


def fmt_bytes(n):
    if n >= 1048576:
        return f"{n / 1048576:.2f} MB"
    if n >= 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n} B"


def shell(title, subtitle, today, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
  <title id="t">{title}</title>
  <desc id="d">{subtitle}</desc>
  <defs>{_BG}{_BARS}</defs>
  <rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/>
  {body}
  <text x="{PL}" y="21" font-size="12" fill="{GOLD}" font-family="Georgia,serif">{title}</text>
  <text x="{W - PR}" y="21" font-size="10" fill="{ROSE}" text-anchor="end" font-family="Georgia,serif">EVENT-HORIZON TELEMETRY</text>
  <text x="{W / 2}" y="{H - 12}" font-size="9" fill="{ROSE}" text-anchor="middle" opacity=".8">AUTO-REFRESHED DAILY BY GITHUB ACTIONS · {today.isoformat()} UTC</text>
</svg>
"""


def signal_chart(events, today):
    bins = {today - timedelta(days=i): 0 for i in range(DAYS - 1, -1, -1)}
    for ev in events:
        try:
            day = datetime.fromisoformat(ev.get("created_at", "").replace("Z", "+00:00")).date()
        except Exception:
            continue
        if day in bins:
            bins[day] += 1
    values = list(bins.values())
    max_y = max(4, max(values) or 1)
    plot_w, plot_h = W - PL - PR, H - PT - PB
    bw = plot_w / DAYS
    parts = []
    for i in range(5):
        yy = PT + plot_h - i * plot_h / 4
        parts.append(f'<line x1="{PL}" y1="{yy:.1f}" x2="{W - PR}" y2="{yy:.1f}" stroke="{INK}" stroke-opacity=".09" stroke-width=".6"/>')
        parts.append(f'<text x="{PL - 8}" y="{yy + 3:.1f}" font-size="9" fill="{INK}" text-anchor="end" opacity=".6">{int(max_y * i / 4)}</text>')
    for i, (day, v) in enumerate(bins.items()):
        h = max(1, round(plot_h * v / max_y))
        x = PL + i * bw + bw * .16
        parts.append(f'<rect x="{x:.1f}" y="{PT + plot_h - h:.1f}" width="{bw * .68:.1f}" height="{h:.1f}" rx="4" fill="url(#bar)" opacity=".88"/>')
        parts.append(f'<text x="{PL + i * bw + bw / 2:.1f}" y="{H - 26}" font-size="10" fill="{INK}" text-anchor="middle" opacity=".72">{day.day}</text>')
    return "".join(parts)


def spectra_chart(mass, today):
    rows = sorted(mass.items(), key=lambda kv: -kv[1])[:7]
    if not rows:
        return f'<text x="{PL}" y="120" font-size="11" fill="{INK}">no language mass recorded yet</text>'
    total = sum(mass.values())
    plot_w = W - PL - PR - 210
    parts = []
    for i, (lang, n) in enumerate(rows):
        y = PT + i * 22
        w = max(7, plot_w * n / rows[0][1])
        parts.append(f'<text x="{PL}" y="{y + 14}" font-size="13" fill="{INK}">{lang}</text>')
        parts.append(f'<rect x="{PL + 150}" y="{y}" width="{w:.1f}" height="9" rx="4" fill="url(#bar)" opacity=".85"/>')
        parts.append(f'<text x="{PL + 150 + w + 10:.0f}" y="{y + 12}" font-size="11" fill="{ROSE}" opacity=".85">{fmt_bytes(n)}</text>')
    parts.append(f'<text x="{PL}" y="{H - 26}" font-size="10" fill="{ROSE}" opacity=".9">TOTAL MASS {fmt_bytes(total)} · TOP {len(rows)} LANGUAGES</text>')
    return "".join(parts)


def main():
    try:
        events = fetch(f"https://api.github.com/users/{USER}/events/public?per_page=100")
        repos = fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=updated")
    except Exception:
        return 0
    today = datetime.now(timezone.utc).date()
    if isinstance(events, list) and events:
        with open(OUT_SIGNAL, "w", encoding="utf-8") as fh:
            fh.write(shell(f"FIELD READINGS / {USER} · SIGNAL · PAST {DAYS} DAYS",
                           "Daily public event count.", today, signal_chart(events, today)))
    mass = {}
    if isinstance(repos, list):
        for repo in repos[:12]:
            try:
                langs = fetch(f"https://api.github.com/repos/{USER}/{repo['name']}/languages")
            except Exception:
                continue
            for lang, n in langs.items():
                mass[lang] = mass.get(lang, 0) + n
    if mass:
        with open(OUT_LANGS, "w", encoding="utf-8") as fh:
            fh.write(shell(f"SPECTRA / {USER} · LANGUAGE MASS",
                           "Bytes of source per language across public repos.", today, spectra_chart(mass, today)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())