>  returns the players rating history

## get_player_rating_history

```bash
curl -X GET "https://api.dupr.gg/player-rating-history/v1.0?limit=10&obfuscatedUserId=7752563844&offset=0" -H "accept: application/json" -H "Authorization: Bearer eyJhbGciOiJSUzUxMiJ9.eyJpc3MiOiJodHRwczovL2R1cHIuZ2ciLCJpYXQiOjE3MzM0MTMwNzksImp0aSI6IjczODk0NjUzOTUiLCJleHAiOjE3MzYwMDUwNzksInN1YiI6IlltbGpaWEF1Y0d4aGFXNWxjall5UUdsamJHOTFaQzVqYjIwPSJ9.Tj_tMthgRlweI9al6Jnazr9p0qrDcVLVN6BRLCV7QbW8yj_LYBbn3EEiPw6vjGqRp7uTudY-Y2WHEl6W75hQfLIqIGywkdBUsw_9NDxsOx2elDv5-j-24H7kY1O-NcLHaJKY4s3fTvpbDvuMq0T1mdS_KTNtPy4TLSE4zkfWzr_2NosaS2PNF7LJO2qz16QgO_vvlyC5lY2ciZAszVCekG6n2DnUie3JtnPwj3w2FWaxO2jYKiWad9bJH2yo9JRj8wN-1uoUCWfDrgaTgzLvJgb1ECPeY9CrN-qBfzPM02OtK-E_-nBYt7NzlCrJ1JftOm6fhiW_6pcOF4VicgIAag"
```

## response

```json
{
  "status": "SUCCESS",
  "result": {
    "offset": 0,
    "limit": 10,
    "total": 0,
    "hits": [
      {
        "ratingHistoryId": 4805502035,
        "userId": 7752563844,
        "userName": "Aidan Bai",
        "userEmail": "aidanbai1203@gmail.com",
        "singles": 4.301750594749188,
        "singlesProvisional": false,
        "doubles": 5.00596695743585,
        "doublesProvisional": false,
        "changedByAdmin": true,
        "created": "2024-10-30T21:12:42Z",
        "matchDate": null,
        "status": "ACTIVE"
      },
      {
        "ratingHistoryId": 4945395042,
        "userId": 7752563844,
        "userName": "Aidan Bai",
        "userEmail": "aidanbai1203@gmail.com",
        "singles": 4.301750594749188,
        "singlesProvisional": false,
        "doubles": 4.94070285134642,
        "doublesProvisional": false,
        "changedByAdmin": false,
        "created": "2024-10-19T16:10:26Z",
        "matchDate": "2024-10-19",
        "status": "ACTIVE"
      },
      {
        "ratingHistoryId": 7923412886,
        "userId": 7752563844,
        "userName": "Aidan Bai",
        "userEmail": "aidanbai1203@gmail.com",
        "singles": 4.35552843428199,
        "singlesProvisional": false,
        "doubles": 4.94070285134642,
        "doublesProvisional": false,
        "changedByAdmin": false,
        "created": "2024-10-19T16:10:24Z",
        "matchDate": "2024-10-19",
        "status": "ACTIVE"
      },
      {
        "ratingHistoryId": 8310144792,
        "userId": 7752563844,
        "userName": "Aidan Bai",
        "userEmail": "aidanbai1203@gmail.com",
        "singles": 3.842910035472765,
        "singlesProvisional": false,
        "doubles": 4.94070285134642,
        "doublesProvisional": false,
        "changedByAdmin": false,
        "created": "2024-10-19T16:10:21Z",
        "matchDate": "2024-10-19",
        "status": "ACTIVE"
      },
      {
        "ratingHistoryId": 6754227535,
        "userId": 7752563844,
        "userName": "Aidan Bai",
        "userEmail": "aidanbai1203@gmail.com",
        "singles": 3.6028743388474465,
        "singlesProvisional": false,
        "doubles": 4.94070285134642,
        "doublesProvisional": false,
        "changedByAdmin": false,
        "created": "2024-10-19T16:10:20Z",
        "matchDate": "2024-10-19",
        "status": "ACTIVE"
      },
      {
        "ratingHistoryId": 5289476606,
        "userId": 7752563844,
        "userName": "Aidan Bai",
        "userEmail": "aidanbai1203@gmail.com",
        "singles": 3.2743310461963975,
        "singlesProvisional": false,
        "doubles": 4.94070285134642,
        "doublesProvisional": false,
        "changedByAdmin": false,
        "created": "2024-10-19T16:10:19Z",
        "matchDate": "2024-10-19",
        "status": "ACTIVE"
      },
      {
        "ratingHistoryId": 6392354813,
        "userId": 7752563844,
        "userName": "Aidan Bai",
        "userEmail": "aidanbai1203@gmail.com",
        "singles": 3.27755188758983,
        "singlesProvisional": false,
        "doubles": 4.94070285134642,
        "doublesProvisional": false,
        "changedByAdmin": false,
        "created": "2024-10-13T08:29:11.676033Z",
        "matchDate": "2023-10-08",
        "status": "ACTIVE"
      },
      {
        "ratingHistoryId": 8565896301,
        "userId": 7752563844,
        "userName": "Aidan Bai",
        "userEmail": "aidanbai1203@gmail.com",
        "singles": 3.27755188758983,
        "singlesProvisional": false,
        "doubles": 4.9410415057519,
        "doublesProvisional": false,
        "changedByAdmin": false,
        "created": "2024-10-13T08:29:11.460359Z",
        "matchDate": "2023-10-08",
        "status": "ACTIVE"
      },
      {
        "ratingHistoryId": 5128599603,
        "userId": 7752563844,
        "userName": "Aidan Bai",
        "userEmail": "aidanbai1203@gmail.com",
        "singles": 3.27755188758983,
        "singlesProvisional": false,
        "doubles": 4.94314278407349,
        "doublesProvisional": false,
        "changedByAdmin": false,
        "created": "2024-10-13T08:29:11.460296Z",
        "matchDate": "2023-10-08",
        "status": "ACTIVE"
      },
      {
        "ratingHistoryId": 7799355564,
        "userId": 7752563844,
        "userName": "Aidan Bai",
        "userEmail": "aidanbai1203@gmail.com",
        "singles": 3.27755188758983,
        "singlesProvisional": false,
        "doubles": 4.94295862960391,
        "doublesProvisional": false,
        "changedByAdmin": false,
        "created": "2024-10-13T08:29:11.460223Z",
        "matchDate": "2023-10-08",
        "status": "ACTIVE"
      }
    ],
    "totalValueRelation": null,
    "hasPrevious": false,
    "hasMore": false,
    "empty": false
  }
}
```
