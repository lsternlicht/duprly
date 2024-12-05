>  this request gets a player stats by making a get request using their player ID

## request

```bash
curl -X GET "https://api.dupr.gg/user/calculated/v1.0/stats/7752563844" -H "accept: application/json" -H "Authorization: Bearer eyJhbGciOiJSUzUxMiJ9.eyJpc3MiOiJodHRwczovL2R1cHIuZ2ciLCJpYXQiOjE3MzM0MTMwNzksImp0aSI6IjczODk0NjUzOTUiLCJleHAiOjE3MzYwMDUwNzksInN1YiI6IlltbGpaWEF1Y0d4aGFXNWxjall5UUdsamJHOTFaQzVqYjIwPSJ9.Tj_tMthgRlweI9al6Jnazr9p0qrDcVLVN6BRLCV7QbW8yj_LYBbn3EEiPw6vjGqRp7uTudY-Y2WHEl6W75hQfLIqIGywkdBUsw_9NDxsOx2elDv5-j-24H7kY1O-NcLHaJKY4s3fTvpbDvuMq0T1mdS_KTNtPy4TLSE4zkfWzr_2NosaS2PNF7LJO2qz16QgO_vvlyC5lY2ciZAszVCekG6n2DnUie3JtnPwj3w2FWaxO2jYKiWad9bJH2yo9JRj8wN-1uoUCWfDrgaTgzLvJgb1ECPeY9CrN-qBfzPM02OtK-E_-nBYt7NzlCrJ1JftOm6fhiW_6pcOF4VicgIAag"
```

## response

```json

{
  "status": "SUCCESS",
  "result": {
    "singles": {
      "averagePartnerDupr": "-",
      "averageOpponentDupr": "4.45",
      "averagePointsWonPercent": "49.21%",
      "halfLife": "3.53",
      "wins": 3,
      "losses": 3
    },
    "doubles": {
      "averagePartnerDupr": "4.75",
      "averageOpponentDupr": "4.72",
      "averagePointsWonPercent": "54.98%",
      "halfLife": "17.56",
      "wins": 105,
      "losses": 62
    },
    "resulOverview": {
      "wins": 108,
      "losses": 65,
      "pending": 0
    }
  }
}
```
