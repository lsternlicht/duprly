# duprly

A CLI for downloading and processing DUPR data into a local SQLite database.

## What Changed

The CLI has been rebuilt around a single entrypoint with task-based commands:

- `duprly sync ...`
- `duprly browse ...`
- `duprly explore ...`
- `duprly export ...`
- `duprly db ...`
- `duprly doctor ...`

Running `duprly` with no subcommand opens an interactive menu in TTY sessions.

## Setup

Create a `.env` file (or pass one via `--config`):

```dotenv
DUPR_USERNAME=<username>
DUPR_PASSWORD=<password>
DUPR_CLUB_ID=8436164521
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## CLI Usage

### Global options

```bash
duprly [--verbose] [--quiet] [--no-color] [--json] [--config PATH] [--interactive|--no-interactive] ...
```

### Core workflows

```bash
# interactive mode (TTY)
duprly

# sync everything
duprly sync all

# sync only players from a specific club
duprly sync players --club-id 8436164521

# sync matches for everyone currently in local DB
duprly sync matches --all-players

# refresh ratings only where missing
duprly sync ratings

# browse a player and persist to DB
duprly browse player 6886613721

# fetch one player's full match history (ALL by default) and persist
duprly browse matches 6886613721

# fetch one player's match history in a bounded date range
duprly browse matches 6886613721 --start-date 2025-01-01 --end-date 2025-12-31

# fetch one player's rating history (defaults: both types, last 2 years)
duprly browse rating-history 6886613721

# fetch only doubles rating history for a specific date range
duprly browse rating-history 6886613721 --type doubles --start-date 2025-12-14 --end-date 2026-02-21

# live lookup by player name with suggestions, then optional match download
duprly browse lookup --entity player --query "aidan bai"

# open interactive saved-data explorer (no API calls)
duprly explore

# list saved players and export to CSV
duprly explore players --query "sternlicht" --export csv --output explore_players.csv

# inspect one saved player and drill into ratings/matches
duprly explore player 6886613721
duprly explore player 6886613721 ratings --type both
duprly explore player 6886613721 matches

# inspect one saved match with full raw payload
duprly explore match 4295493637 --export json --output explore_match_4295493637.json

# browse raw metadata snapshots from local tables
duprly explore raw --kind player --player-dupr-id 6886613721

# launch local web explorer (Datasette)
duprly explore web --open

# import DUPR auth token from browser cookies (top-level shortcut)
duprly import-browser-token --browser comet --domain dupr.com

# import DUPR auth token from browser cookies (Safari default)
duprly auth import-browser-token --browser safari

# search clubs
duprly browse clubs "NYC pickle"

# export club players (search/select)
duprly export club-players "NYC pickle"

# export rankings
duprly export rankings 8436164521

# export workbook from local DB
duprly export workbook --output dupr.xlsx

# DB stats / rebuild reporting table
duprly db stats
duprly db rebuild-match-detail

# diagnostics
duprly doctor check
duprly doctor check --api
```

## Question-Driven Datasette

`duprly explore web --open` now launches a guided Datasette dashboard with canned analytics queries for pickleball ratings.

### Common question URLs

```bash
# this player's rating over time (default doubles)
http://127.0.0.1:8001/dupr/player_rating_over_time?dupr_id=6886613721&rating_type=DOUBLES

# recent form (last 90 days by default)
http://127.0.0.1:8001/dupr/player_recent_form?dupr_id=6886613721&days=90

# partner breakdown
http://127.0.0.1:8001/dupr/player_partner_breakdown?dupr_id=6886613721&days=90

# opponent breakdown
http://127.0.0.1:8001/dupr/player_opponent_breakdown?dupr_id=6886613721&days=90

# club top risers
http://127.0.0.1:8001/dupr/club_top_risers?club_id=7735643894&days=90&rating_type=DOUBLES
```

### Parameter glossary

- `dupr_id`: numeric DUPR player ID
- `club_id`: numeric DUPR club ID (optional in club queries)
- `rating_type`: `DOUBLES` (default) or `SINGLES`
- `days`: rolling window for \"recent\" analysis (default `90`)
- `start_date` / `end_date`: optional `YYYY-MM-DD` date bounds for trend queries

## Legacy Compatibility

Old command names are still available with deprecation warnings:

- `get-data` -> `sync all`
- `get-all-players` -> `sync players`
- `get-all-player-matches` -> `sync matches --all-players`
- `get-player` -> `browse player`
- `get-matches` -> `browse matches`
- `update-ratings` -> `sync ratings`
- `build-match-detail` -> `db rebuild-match-detail`
- `stats` -> `db stats`
- `write-excel` -> `export workbook`

The old script entrypoint still works:

```bash
python /Users/leosternlicht/repos/duprly/duprly.py --help
```

Standalone helper scripts are now thin wrappers:

- `get_players.py`
- `get_club_rankings.py`
- `get_matches.py`

## Notes

- DUPR endpoints used here are unofficial and may change.
- Match history uses the browser-proven request shape (`POST /player/v1.0/{id}/history`).
- `duprly explore` is read-only and works entirely from local SQLite data.
- Explorer export supports CSV/JSON to file and best-effort clipboard copy.
- `duprly explore web` depends on Datasette `0.59`, which currently needs `setuptools<81` (`pkg_resources`).
- `duprly explore web` now generates guided metadata and templates at launch for canned analytics queries.
- `datasette-vega` enables richer chart rendering; if missing, query pages still work in table mode.
- For easier web browsing, `rating` now includes cached `player_dupr_id` and `player_full_name` columns.
- Data is written to `dupr.sqlite`.
- `duprly doctor check` is useful before first sync.
