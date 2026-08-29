#!/usr/bin/env python3
"""
daily-brief fetch + build pipeline.

What this does, in order (see the project proposal doc for the full "why"):
  1. Load the outlet/beat lookup table (config/outlets.json) and settings (config/settings.json).
  2. Pull every configured RSS feed. No engagement data, no personalization, no ranking --
     every article published within the lookback window from every configured feed is included,
     exactly as published, sorted newest-first. Nothing is grouped or deduplicated (see Section 3
     of the proposal for why that's a deliberate choice, not an oversight).
  3. Render a single static HTML page (docs/index.html) that GitHub Pages serves directly.

A feed that fails to fetch (network hiccup, the outlet changed its URL, temporary block) is
skipped with a warning -- it does NOT crash the whole build. The "Sources this edition" footer
on the page lists which feeds succeeded and which didn't, so a silent gap is still visible
rather than hidden.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DOCS_DIR = ROOT / "docs"

LOCAL_TZ = ZoneInfo("America/Chicago")


def load_config():
    settings = json.loads((CONFIG_DIR / "settings.json").read_text())
    outlets = json.loads((CONFIG_DIR / "outlets.json").read_text())
    return settings, outlets


def should_run_now(settings, force=False):
    """DST-safe schedule check. The GitHub Action triggers this hourly; we only do
    real work when it's actually 6am or 6pm *Central* time, whatever the UTC offset
    currently is (Central shifts between UTC-5 and UTC-6 across the year)."""
    if force:
        return True
    now_local = datetime.now(LOCAL_TZ)
    return now_local.hour in settings["refresh_hours_local"]


def fetch_outlet_articles(outlet, cutoff_utc):
    """Fetch every beat feed for one outlet. Returns (articles, per_feed_status)."""
    articles = []
    statuses = []
    for beat, url in outlet["feeds"].items():
        try:
            parsed = feedparser.parse(url)
            if parsed.bozo and not parsed.entries:
                raise ValueError(str(parsed.bozo_exception))
            count = 0
            for entry in parsed.entries:
                published = _entry_datetime(entry)
                if published is None or published < cutoff_utc:
                    continue
                articles.append({
                    "title": entry.get("title", "(untitled)"),
                    "link": entry.get("link", "#"),
                    "summary": _clean_summary(entry.get("summary", "")),
                    "outlet": outlet["name"],
                    "rating_note": outlet["rating_note"],
                    "beat": beat,
                    "published": published,
                })
                count += 1
            statuses.append({"outlet": outlet["name"], "beat": beat, "url": url,
                              "ok": True, "count": count})
        except Exception as exc:  # noqa: BLE001 -- one bad feed must never kill the build
            statuses.append({"outlet": outlet["name"], "beat": beat, "url": url,
                              "ok": False, "error": str(exc)})
    return articles, statuses


def _entry_datetime(entry):
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None


def _clean_summary(raw_html, max_len=280):
    import re
    text = re.sub("<[^<]+?>", "", raw_html or "").strip()
    text = " ".join(text.split())
    return text[:max_len].rsplit(" ", 1)[0] + "..." if len(text) > max_len else text


def build(force=False):
    settings, config = load_config()

    if not should_run_now(settings, force=force):
        print("Not a scheduled refresh hour (Central time) -- skipping. Use --force to override.")
        return 0

    lookback_hours = settings["lookback_hours"]
    cutoff_utc = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

    all_articles = []
    all_statuses = []
    for outlet in config["outlets"]:
        articles, statuses = fetch_outlet_articles(outlet, cutoff_utc)
        all_articles.extend(articles)
        all_statuses.extend(statuses)

    all_articles.sort(key=lambda a: a["published"], reverse=True)

    generated_at_local = datetime.now(LOCAL_TZ)
    html = render_page(all_articles, all_statuses, config["manual_links"],
                        generated_at_local, lookback_hours)

    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "index.html").write_text(html, encoding="utf-8")

    ok_feeds = sum(1 for s in all_statuses if s["ok"])
    print(f"Wrote {len(all_articles)} articles from {ok_feeds}/{len(all_statuses)} feeds "
          f"to {DOCS_DIR / 'index.html'}")
    return 0


def render_page(articles, statuses, manual_links, generated_at_local, lookback_hours):
    edition = "Morning" if generated_at_local.hour < 12 else "Evening"
    date_str = generated_at_local.strftime("%A, %B %d, %Y")
    time_str = generated_at_local.strftime("%-I:%M %p %Z")

    article_html = "\n".join(_article_card(a) for a in articles) or (
        '<p class="empty">No articles in the last '
        f'{lookback_hours}h window -- check back at the next refresh.</p>'
    )

    manual_links_html = "\n".join(_manual_link_block(m) for m in manual_links)

    failed = [s for s in statuses if not s["ok"]]
    status_html = ""
    if failed:
        items = "\n".join(
            f'<li>{s["outlet"]} ({s["beat"]}) -- {s["error"]}</li>' for s in failed
        )
        status_html = f'''
        <details class="feed-status">
          <summary>{len(failed)} feed(s) did not return data this edition</summary>
          <ul>{items}</ul>
        </details>'''

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily Brief -- {date_str}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{
    max-width: 720px; margin: 0 auto; padding: 24px 16px 64px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Georgia, serif;
    line-height: 1.5; color: #1a1a1a; background: #fdfdfb;
  }}
  @media (prefers-color-scheme: dark) {{
    body {{ color: #e8e6e1; background: #16161a; }}
    a {{ color: #8ab4f8; }}
    .card {{ border-color: #333 !important; }}
    .rating {{ color: #9aa0a6 !important; }}
  }}
  header {{ margin-bottom: 32px; border-bottom: 2px solid currentColor; padding-bottom: 16px; }}
  h1 {{ font-size: 1.6rem; margin: 0 0 4px; }}
  .meta {{ opacity: 0.7; font-size: 0.9rem; }}
  .card {{ padding: 16px 0; border-bottom: 1px solid #ddd; }}
  .card h2 {{ font-size: 1.05rem; margin: 0 0 6px; }}
  .card h2 a {{ text-decoration: none; color: inherit; }}
  .card h2 a:hover {{ text-decoration: underline; }}
  .summary {{ margin: 6px 0; font-size: 0.95rem; opacity: 0.9; }}
  .rating {{ font-size: 0.8rem; opacity: 0.65; }}
  .outlet {{ font-weight: 600; }}
  .beat-tag {{ text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em; opacity: 0.6; }}
  .manual-links {{ margin-top: 40px; padding-top: 16px; border-top: 2px solid currentColor; }}
  .manual-links h2 {{ font-size: 1.1rem; }}
  .manual-links ul {{ padding-left: 20px; }}
  .feed-status {{ margin-top: 24px; font-size: 0.85rem; opacity: 0.7; }}
  .empty {{ opacity: 0.7; font-style: italic; }}
</style>
</head>
<body>
<header>
  <h1>Daily Brief -- {edition} Edition</h1>
  <div class="meta">{date_str} &middot; generated {time_str} &middot; last {lookback_hours}h,
  reverse-chronological, every vetted outlet's own feed, no ranking or grouping</div>
</header>
<main>
{article_html}
</main>
<section class="manual-links">
  <h2>Check directly (no free public RSS)</h2>
  {manual_links_html}
</section>
{status_html}
</body>
</html>
"""


def _article_card(a):
    published_local = a["published"].astimezone(LOCAL_TZ).strftime("%-I:%M %p")
    return f'''<article class="card">
  <div class="beat-tag">{a["beat"]}</div>
  <h2><a href="{a["link"]}" target="_blank" rel="noopener">{_escape(a["title"])}</a></h2>
  <p class="summary">{_escape(a["summary"])}</p>
  <p class="rating"><span class="outlet">{_escape(a["outlet"])}</span> &middot; {published_local}
  &middot; {_escape(a["rating_note"])}</p>
</article>'''


def _manual_link_block(m):
    links = " &middot; ".join(
        f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'
        for label, url in m["links"].items()
    )
    return f'<p><strong>{_escape(m["name"])}</strong> -- {_escape(m["reason"])}<br>{links}</p>'


def _escape(text):
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    force = "--force" in sys.argv
    sys.exit(build(force=force))
