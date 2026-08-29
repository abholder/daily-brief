# Daily Brief

A personal news page built from vetted, low-bias/high-factuality outlets — no
algorithmic ranking, no personalization, no story-grouping. Every article each
outlet publishes to its own RSS feed within a 24-hour window, shown reverse-
chronological, exactly as published. Full reasoning and source-vetting behind
every decision here lives in the project proposal doc (ask Aaron for the link,
or check the "Informed" Claude project).

## One-time setup

1. **Create the GitHub repo.** On github.com, create a new **public** repository
   named `daily-brief` (public is required for free GitHub Pages hosting).
   Don't initialize it with a README — you're pushing this folder's contents in.

2. **Push this folder to it**, from inside this folder:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<your-username>/daily-brief.git
   git push -u origin main
   ```

3. **Allow the Action to publish.** In the repo on GitHub: **Settings → Actions →
   General → Workflow permissions** → select **"Read and write permissions"** →
   Save. (Without this, the Action can build the page but can't commit it back.)

4. **Turn on GitHub Pages.** **Settings → Pages** → under "Build and deployment",
   set **Source: Deploy from a branch**, **Branch: main**, **Folder: /docs** → Save.
   Your page will be live at `https://<your-username>.github.io/daily-brief/`.

5. **Trigger the first edition manually.** **Actions tab → "Build and publish
   Daily Brief" → Run workflow.** This builds immediately (it doesn't wait for
   6am/6pm) so you can see a real edition and confirm everything works. After
   that, it runs on its own schedule — see below.

## How the schedule works

The workflow fires every hour, but the script only does real work at ~6am and
~6pm **Central time**; every other hour it's a no-op. This is deliberate: GitHub's
scheduler only understands UTC, and Central shifts between UTC-5 and UTC-6 with
Daylight Saving Time, so a schedule hard-coded in UTC would silently drift an
hour off "6am Central" twice a year. Checking the actual local hour inside the
script keeps it correct automatically. Adjust the target hours in
`config/settings.json` (`refresh_hours_local`) if you ever want a different time.

## Changing things later

Everything you're likely to want to tweak lives in `config/`, not in the script:

- `config/settings.json` — lookback window (`lookback_hours`, currently 24),
  refresh times, timezone.
- `config/outlets.json` — the outlet list itself: add, remove, or fix a feed URL
  per outlet/beat here. Each outlet also carries a `rating_note` (why it's on
  the list) and a `verified` field — see below.

No code changes needed for either.

## Known limitations, read before relying on this

- **Feed verification.** This repo was built in a sandboxed dev session with
  restricted outbound network access, so most feed URLs (BBC, DW, WSJ, FT,
  Axios, Christian Science Monitor, The Economist) are marked `"verified":
  "assumed"` in `config/outlets.json` — they're well-documented public URLs,
  but weren't fetched live from that session. **PBS NewsHour, The Hill, and
  NewsNation were confirmed live** (`"verified": "live"`) with real, current
  articles. The very first real run (step 5 above) will tell you which of the
  "assumed" ones actually work — check the "N feed(s) did not return data"
  section at the bottom of the published page. If one's dead, the fix is a
  one-line URL edit in `config/outlets.json`, not a code change.

- **Reuters, AP, and AFP aren't automated.** None currently offer a free public
  RSS feed (verified via research, not assumed — see the proposal doc). They're
  listed as manual "check directly" links at the bottom of the page instead.

- **NewsNation and The Hill only have general feeds, not beat-scoped ones.**
  Every other outlet's feed is scoped to World/Politics/Economy/Science
  specifically, but these two didn't have confirmed topic-specific feeds, so
  their general feed is used as-is — meaning occasional off-beat items (local
  news, crime stories) can show up from just those two outlets. Worth revisiting
  once their real topic-feed URLs are confirmed or if this bothers you enough to
  drop the general feed.

## Testing locally

```bash
pip install -r requirements.txt
python3 scripts/fetch_and_build.py --force   # --force ignores the 6am/6pm check
open docs/index.html                          # or just open the file in a browser
```

A fixture-based logic test (no live network needed) lives in
`scripts/test_fixtures/` if you ever want to verify the pipeline's filtering/
sorting logic without hitting real feeds.
