#!/usr/bin/env python3
"""
Generates a one-off PREVIEW of the rendered page using real headlines this session
fetched directly from PBS NewsHour, The Hill, and NewsNation during development
(this sandbox can't make live outbound calls to news sites the way the real GitHub
Action will, so this stands in for a live run). Not part of the production pipeline --
run manually, once, just so Aaron can see what the actual page design looks like.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_and_build import render_page, ROOT  # noqa: E402

import json

manual_links = json.loads((ROOT / "config" / "outlets.json").read_text())["manual_links"]


def dt(y, m, d, h, mi):
    return datetime(y, m, d, h, mi, tzinfo=timezone.utc)


# Real headlines fetched live during this session (2026-08-29) from confirmed-working feeds.
articles = [
    {"title": "Trump says U.S. has entered deal with Venezuela to control 65 billion barrels of its oil reserves",
     "link": "https://www.pbs.org/newshour/", "summary": "The administration announced what it billed as a major energy agreement with Venezuela.",
     "outlet": "PBS NewsHour", "rating_note": "Center (AllSides, Ad Fontes); publicly funded",
     "beat": "world", "published": dt(2026, 8, 28, 19, 35)},
    {"title": "Devastating scale of Himalayan floods comes into focus as rescuers arrive",
     "link": "https://www.pbs.org/newshour/", "summary": "Rescue teams are reaching remote areas days after flooding displaced tens of thousands.",
     "outlet": "PBS NewsHour", "rating_note": "Center (AllSides, Ad Fontes); publicly funded",
     "beat": "world", "published": dt(2026, 8, 28, 18, 55)},
    {"title": "NASA is preparing to launch the Nancy Grace Roman Space Telescope. Here's what to know",
     "link": "https://www.pbs.org/newshour/", "summary": "The long-delayed observatory is set to expand humanity's view of the cosmos.",
     "outlet": "PBS NewsHour", "rating_note": "Center (AllSides, Ad Fontes); publicly funded",
     "beat": "science", "published": dt(2026, 8, 28, 18, 51)},
    {"title": "Fed Chair Warsh not ruling out interest rate hike amid inflation concerns",
     "link": "https://www.pbs.org/newshour/", "summary": "Warsh signaled the central bank is watching inflation data closely ahead of its next meeting.",
     "outlet": "PBS NewsHour", "rating_note": "Center (AllSides, Ad Fontes); publicly funded",
     "beat": "economy", "published": dt(2026, 8, 28, 18, 45)},
    {"title": "Live updates: Warsh hints at potential Fed interest rate hike; March on Washington focuses on voting rights",
     "link": "https://thehill.com/", "summary": "Rolling coverage of the day's top political stories.",
     "outlet": "The Hill", "rating_note": "Center / Balance-Certified",
     "beat": "politics", "published": dt(2026, 8, 28, 14, 37)},
    {"title": "Fetterman: Democratic Party has 'socialism problem'",
     "link": "https://thehill.com/", "summary": "The senator's comments add to an ongoing intra-party debate.",
     "outlet": "The Hill", "rating_note": "Center / Balance-Certified",
     "beat": "politics", "published": dt(2026, 8, 28, 14, 33)},
    {"title": "Deputies on hunt for reported lion, cub in Indiana",
     "link": "https://thehill.com/", "summary": "Local officials are investigating reported sightings.",
     "outlet": "The Hill", "rating_note": "Center / Balance-Certified",
     "beat": "general (not world/politics/economy/science)", "published": dt(2026, 8, 28, 14, 33)},
    {"title": "Vance calls for probe into Biden admin's East Palestine response after contamination report",
     "link": "https://www.newsnationnow.com/", "summary": "The vice president is calling for renewed scrutiny of the 2023 derailment response.",
     "outlet": "NewsNation", "rating_note": "AllSides Balance Certified",
     "beat": "politics", "published": dt(2026, 8, 28, 21, 46)},
    {"title": "Why Apple Maps search may be key to Lindsay Clancy's fate",
     "link": "https://www.newsnationnow.com/", "summary": "New details have emerged in the ongoing case.",
     "outlet": "NewsNation", "rating_note": "AllSides Balance Certified",
     "beat": "general (not world/politics/economy/science)", "published": dt(2026, 8, 28, 18, 31)},
]
articles.sort(key=lambda a: a["published"], reverse=True)

statuses = [
    {"outlet": "BBC News", "beat": "world", "url": "...", "ok": False,
     "error": "Not independently verified this session (sandbox network could not reach it) -- expected to work from GitHub Actions"},
    {"outlet": "Deutsche Welle", "beat": "world", "url": "...", "ok": False,
     "error": "Not independently verified this session -- expected to work from GitHub Actions"},
]

html = render_page(articles, statuses, manual_links, datetime(2026, 8, 29, 6, 0), lookback_hours=24)
out = ROOT / "preview_output"
out.mkdir(exist_ok=True)
(out / "index.html").write_text(html, encoding="utf-8")
print(f"Wrote preview to {out / 'index.html'}")
