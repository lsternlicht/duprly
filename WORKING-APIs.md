# WORKING APIs (DUPR)

This file tracks DUPR API endpoints that are verified from browser traffic and/or likely to work from Swagger/docs.

## Verified Working (browser-confirmed)

### `POST /player/v1.0/search`
- Status: verified.
- Minimal payload:
```json
{
  "limit": 10,
  "offset": 0,
  "query": "leo sternli",
  "exclude": [],
  "includeUnclaimedPlayers": true,
  "filter": {
    "lat": 40.7127753,
    "lng": -74.0059728,
    "rating": { "maxRating": null, "minRating": null },
    "locationText": ""
  }
}
```
- Result shape: `result.hits[]`.
- Implementation mapping: `DuprClient.search_players`.

### `POST /club/v1.0/all`
- Status: verified.
- Minimal payload:
```json
{
  "limit": 18,
  "offset": 0,
  "query": "nyc pi"
}
```
- Result shape: `result.hits[]`.
- Implementation mapping: `DuprClient.search_clubs`.

### `POST /player/v1.0/{id}/history`
- Status: verified.
- Minimal payload for full history paging:
```json
{
  "filters": { "eventFormat": null },
  "limit": 10,
  "offset": 0,
  "sort": { "order": "DESC", "parameter": "MATCH_DATE" }
}
```
- Minimal payload for bounded range:
```json
{
  "filters": {
    "eventFormat": null,
    "eventDate": { "startDate": "2025-01-01", "endDate": "2025-12-31" }
  },
  "limit": 100,
  "offset": 0,
  "sort": { "order": "DESC", "parameter": "MATCH_DATE" }
}
```
- Result shape: `result.hits[]` with full metadata (`teams`, `preMatchRatingAndImpact`, `scoreFormat`, `clientName`, etc.).
- Implementation mapping:
  - `DuprClient.get_member_match_history_all`
  - `DuprClient.get_member_match_history_range`
- Persistence mapping:
  - raw full-fidelity JSON is stored in `player_match_raw.match_json`.

### `GET /user/calculated/v1.0/stats/{id}`
- Status: verified.
- Payload: none.
- Result shape: `result.singles`, `result.doubles`, `result.resulOverview`.
- Implementation mapping: `DuprClient.get_player_calculated_stats`.

### `POST /player/v1.0/{id}/rating-history`
- Status: verified.
- Minimal payload:
```json
{
  "endDate": "2026-02-21",
  "limit": 100,
  "offset": 0,
  "startDate": "2025-12-14",
  "sortBy": "asc",
  "type": "DOUBLES"
}
```
- Result shape: `result.ratingHistory[]`.
- Implementation mapping: `DuprClient.get_player_rating_history`.
- Persistence mapping:
  - scoped snapshots stored in `player_rating_history`.

## Likely Working (Swagger/docs + existing codepath)

### `GET /player/v1.0/{id}`
- Confidence: high.
- Purpose: player profile/ratings.
- Result shape: `result`.
- Implementation mapping: `DuprClient.get_player`.

### `GET /user/v1.0/profile/`
- Confidence: high.
- Purpose: auth/profile health check.
- Result shape: `result`.
- Implementation mapping: `DuprClient.get_profile`.

### `POST /club/{clubId}/members/v1.0/all`
- Confidence: medium/high.
- Purpose: club member paging.
- Result shape: `result.hits[]`.
- Implementation mapping: `DuprClient.get_members_by_club`.

### `POST /club/{clubId}/v1.0/ranking`
- Confidence: medium/high.
- Purpose: club ranking export.
- Result shape: `result.memberRanking.hits[]`.
- Implementation mapping: `DuprClient.get_members_by_club_ranking`.

## Known Fragile / Payload Sensitive

### Match history endpoint (`POST /player/v1.0/{id}/history`)
- Do not rely on `GET /player/v1.0/{id}/history?limit=&offset=` for full history retrieval.
- Use browser-compatible POST body and server paging fields.
- Prefer these response fields for paging:
  - `result.total`
  - `result.offset`
  - `result.limit`
  - `result.hasMore` fallback when `total` is absent.

### Rating history endpoint (`POST /player/v1.0/{id}/rating-history`)
- `type` is required (`SINGLES` or `DOUBLES`).
- Use one request per type for “both”.
- Use `result.ratingHistory[]` as primary list; fallback to `result.hits[]` defensively.

## Notes

- API host expected: `https://api.dupr.gg`
- API version expected: `v1.0`
- These endpoints are unofficial and may change without notice.
