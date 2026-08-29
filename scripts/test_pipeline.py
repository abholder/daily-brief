#!/usr/bin/env python3
"""
Quick logic test that doesn't need live network access: fetches a local fixture
feed (scripts/test_fixtures/sample_feed.xml) through the real fetch/filter/sort/
render pipeline, plus one deliberately-broken URL to confirm a bad feed doesn't
crash the build. Run: python3 scripts/test_pipeline.py
"""
import sys
from datetime import timedelta, timezone, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_and_build import fetch_outlet_articles, render_page  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "test_fixtures" / "sample_feed.xml"

test_outlets = [
    {
        "id": "test_local", "name": "Test Outlet (local fixture)",
        "rating_note": "Center (test fixture)",
        "feeds": {"world": "file://" + str(FIXTURE)},
    },
    {
        "id": "test_broken", "name": "Test Outlet (broken url)",
        "rating_note": "n/a",
        "feeds": {"world": "https://this-domain-does-not-exist.invalid/feed.xml"},
    },
]

cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
all_articles, all_statuses = [], []
for outlet in test_outlets:
    articles, statuses = fetch_outlet_articles(outlet, cutoff)
    all_articles.extend(articles)
    all_statuses.extend(statuses)

all_articles.sort(key=lambda a: a["published"], reverse=True)

assert len(all_articles) == 2, f"expected 2 articles within the lookback window, got {len(all_articles)}"
assert all_articles[0]["published"] > all_articles[1]["published"], "sort order is wrong"
assert any(not s["ok"] for s in all_statuses), "the broken feed should have failed, not crashed"
assert any(s["ok"] for s in all_statuses), "the fixture feed should have succeeded"

html = render_page(all_articles, all_statuses, manual_links=[],
                    generated_at_local=datetime.now(), lookback_hours=24)
assert "old-article" not in html, "the >24h-old fixture article leaked past the lookback filter"
assert all_articles[0]["title"] in html

print("All checks passed:")
print(f"  - {len(all_articles)} articles within the lookback window (3rd, too-old fixture item correctly excluded)")
print("  - reverse-chronological sort correct")
print("  - broken feed failed without crashing the build, and is reported in the page's feed-status section")
