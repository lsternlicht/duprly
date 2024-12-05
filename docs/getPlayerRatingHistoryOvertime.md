# /player///rating-history

## request

```bash
curl -X POST "https://api.dupr.gg/player/v1.0/7752563844/rating-history" -H "accept: application/json" -H "Authorization: Bearer eyJhbGciOiJSUzUxMiJ9.eyJpc3MiOiJodHRwczovL2R1cHIuZ2ciLCJpYXQiOjE3MzM0MTMwNzksImp0aSI6IjczODk0NjUzOTUiLCJleHAiOjE3MzYwMDUwNzksInN1YiI6IlltbGpaWEF1Y0d4aGFXNWxjall5UUdsamJHOTFaQzVqYjIwPSJ9.Tj_tMthgRlweI9al6Jnazr9p0qrDcVLVN6BRLCV7QbW8yj_LYBbn3EEiPw6vjGqRp7uTudY-Y2WHEl6W75hQfLIqIGywkdBUsw_9NDxsOx2elDv5-j-24H7kY1O-NcLHaJKY4s3fTvpbDvuMq0T1mdS_KTNtPy4TLSE4zkfWzr_2NosaS2PNF7LJO2qz16QgO_vvlyC5lY2ciZAszVCekG6n2DnUie3JtnPwj3w2FWaxO2jYKiWad9bJH2yo9JRj8wN-1uoUCWfDrgaTgzLvJgb1ECPeY9CrN-qBfzPM02OtK-E_-nBYt7NzlCrJ1JftOm6fhiW_6pcOF4VicgIAag" -H "Content-Type: application/json" -d "{ \"endDate\": \"2024-12-05\", \"limit\": 100, \"offset\": 0, \"startDate\": \"2022-09-28\", \"sortBy\": \"asc\", \"type\": \"DOUBLES\"}"
```

## request notes

- id (this is the player id)
- request object (body) format example:

```json
{
    "endDate": "2024-12-05",
    "limit": 100,
    "offset": 0,
    "startDate": "2022-09-28",
    "sortBy": "asc",
    "type": "DOUBLES"
}
```

## response

```json
{
  "status": "SUCCESS",
  "result": {
    "playerId": 7752563844,
    "type": "DOUBLES",
    "ratingHistory": [
      {
        "date": "2023-06-05",
        "matchDate": null,
        "rating": 4.423,
        "changedByAdmin": true
      },
      {
        "date": "2023-07-20",
        "matchDate": "2023-07-19",
        "rating": 4.37236,
        "changedByAdmin": false
      },
      {
        "date": "2023-07-20",
        "matchDate": "2023-07-19",
        "rating": 4.38411,
        "changedByAdmin": false
      },
      {
        "date": "2023-07-20",
        "matchDate": "2023-07-19",
        "rating": 4.39382,
        "changedByAdmin": false
      },
      {
        "date": "2023-07-20",
        "matchDate": "2023-07-19",
        "rating": 4.37202,
        "changedByAdmin": false
      },
      {
        "date": "2023-07-20",
        "matchDate": null,
        "rating": 4.37202,
        "changedByAdmin": true
      },
      {
        "date": "2023-07-27",
        "matchDate": "2023-07-26",
        "rating": 4.44037,
        "changedByAdmin": false
      },
      {
        "date": "2023-07-27",
        "matchDate": "2023-07-26",
        "rating": 4.50941,
        "changedByAdmin": false
      },
      {
        "date": "2023-07-27",
        "matchDate": "2023-07-27",
        "rating": 4.47062,
        "changedByAdmin": false
      },
      {
        "date": "2023-07-27",
        "matchDate": "2023-07-27",
        "rating": 4.44275,
        "changedByAdmin": false
      },
      {
        "date": "2023-08-17",
        "matchDate": "2023-08-16",
        "rating": 4.45882,
        "changedByAdmin": false
      },
      {
        "date": "2023-08-17",
        "matchDate": "2023-08-16",
        "rating": 4.41554,
        "changedByAdmin": false
      },
      {
        "date": "2023-08-17",
        "matchDate": "2023-08-16",
        "rating": 4.42686,
        "changedByAdmin": false
      },
      {
        "date": "2023-08-17",
        "matchDate": "2023-08-16",
        "rating": 4.34925,
        "changedByAdmin": false
      },
      {
        "date": "2023-08-17",
        "matchDate": "2023-08-17",
        "rating": 4.38251,
        "changedByAdmin": false
      },
      {
        "date": "2023-08-25",
        "matchDate": null,
        "rating": 4.38251,
        "changedByAdmin": true
      },
      {
        "date": "2023-09-27",
        "matchDate": null,
        "rating": 4.4236815,
        "changedByAdmin": true
      },
      {
        "date": "2023-10-03",
        "matchDate": "2023-08-16",
        "rating": 4.4245461,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-08",
        "matchDate": "2023-10-08",
        "rating": 4.5011086,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-08",
        "matchDate": "2023-10-08",
        "rating": 4.5361023,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-08",
        "matchDate": "2023-10-08",
        "rating": 4.598698,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-08",
        "matchDate": "2023-10-08",
        "rating": 4.6212587,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-21",
        "matchDate": "2023-10-20",
        "rating": 4.667777,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-21",
        "matchDate": "2023-10-20",
        "rating": 4.6256404,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-21",
        "matchDate": "2023-10-20",
        "rating": 4.5631213,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-21",
        "matchDate": "2023-10-20",
        "rating": 4.633078,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-21",
        "matchDate": null,
        "rating": 4.7398825,
        "changedByAdmin": true
      },
      {
        "date": "2023-10-21",
        "matchDate": null,
        "rating": 4.6901693,
        "changedByAdmin": true
      },
      {
        "date": "2023-10-21",
        "matchDate": null,
        "rating": 4.633078,
        "changedByAdmin": true
      },
      {
        "date": "2023-10-21",
        "matchDate": "2023-10-20",
        "rating": 4.6901693,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-21",
        "matchDate": "2023-10-21",
        "rating": 4.755966,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-23",
        "matchDate": "2023-10-22",
        "rating": 4.7657285,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-23",
        "matchDate": "2023-10-22",
        "rating": 4.7337527,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-23",
        "matchDate": "2023-10-22",
        "rating": 4.7445993,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-23",
        "matchDate": "2023-10-22",
        "rating": 4.717926,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-23",
        "matchDate": "2023-10-22",
        "rating": 4.6952143,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-25",
        "matchDate": null,
        "rating": 4.6250038,
        "changedByAdmin": true
      },
      {
        "date": "2023-10-25",
        "matchDate": null,
        "rating": 4.6250038,
        "changedByAdmin": true
      },
      {
        "date": "2023-10-26",
        "matchDate": "2023-10-25",
        "rating": 4.642608,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-27",
        "matchDate": "2023-10-27",
        "rating": 4.5536823,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-27",
        "matchDate": "2023-10-27",
        "rating": 4.6440215,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-27",
        "matchDate": "2023-10-27",
        "rating": 4.600004,
        "changedByAdmin": false
      },
      {
        "date": "2023-10-31",
        "matchDate": null,
        "rating": 4.5531946,
        "changedByAdmin": true
      },
      {
        "date": "2023-11-04",
        "matchDate": "2023-11-03",
        "rating": 4.6453815,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-04",
        "matchDate": "2023-11-03",
        "rating": 4.677321,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-04",
        "matchDate": "2023-11-04",
        "rating": 4.745206,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-04",
        "matchDate": "2023-11-04",
        "rating": 4.7107463,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-04",
        "matchDate": "2023-11-03",
        "rating": 4.7570583,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-05",
        "matchDate": "2023-11-05",
        "rating": 4.7939396,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-05",
        "matchDate": null,
        "rating": 4.7939396,
        "changedByAdmin": true
      },
      {
        "date": "2023-11-05",
        "matchDate": "2023-11-05",
        "rating": 4.825346,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-05",
        "matchDate": "2023-11-05",
        "rating": 4.8516073,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-06",
        "matchDate": "2023-11-03",
        "rating": 4.8196543,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-17",
        "matchDate": null,
        "rating": null,
        "changedByAdmin": true
      },
      {
        "date": "2023-11-18",
        "matchDate": "2023-11-17",
        "rating": 4.77067,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-18",
        "matchDate": "2023-11-17",
        "rating": 4.803311,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-18",
        "matchDate": "2023-11-17",
        "rating": 4.759082,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-18",
        "matchDate": "2023-11-17",
        "rating": 4.7898946,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-18",
        "matchDate": "2023-11-17",
        "rating": 4.727162,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-18",
        "matchDate": "2023-11-17",
        "rating": 4.7012463,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-19",
        "matchDate": null,
        "rating": 4.7012463,
        "changedByAdmin": true
      },
      {
        "date": "2023-11-19",
        "matchDate": "2023-11-19",
        "rating": 4.7136273,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-19",
        "matchDate": "2023-11-19",
        "rating": 4.6786447,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-19",
        "matchDate": "2023-11-19",
        "rating": 4.700311,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-20",
        "matchDate": null,
        "rating": 4.8096493,
        "changedByAdmin": true
      },
      {
        "date": "2023-11-20",
        "matchDate": "2023-11-19",
        "rating": 4.8190675,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-20",
        "matchDate": "2023-11-19",
        "rating": 4.853455,
        "changedByAdmin": false
      },
      {
        "date": "2023-11-21",
        "matchDate": null,
        "rating": 4.83312,
        "changedByAdmin": true
      },
      {
        "date": "2023-11-21",
        "matchDate": "2023-11-19",
        "rating": 4.848098,
        "changedByAdmin": false
      },
      {
        "date": "2023-12-02",
        "matchDate": "2023-12-02",
        "rating": 4.7785053,
        "changedByAdmin": false
      },
      {
        "date": "2023-12-02",
        "matchDate": "2023-12-02",
        "rating": 4.8211884,
        "changedByAdmin": false
      },
      {
        "date": "2023-12-12",
        "matchDate": null,
        "rating": 4.852138,
        "changedByAdmin": true
      },
      {
        "date": "2023-12-12",
        "matchDate": "2023-10-23",
        "rating": 4.821659,
        "changedByAdmin": false
      },
      {
        "date": "2024-01-19",
        "matchDate": null,
        "rating": 4.821659,
        "changedByAdmin": true
      },
      {
        "date": "2024-01-21",
        "matchDate": "2024-01-21",
        "rating": 4.843406,
        "changedByAdmin": false
      },
      {
        "date": "2024-01-21",
        "matchDate": "2024-01-21",
        "rating": 4.7997813,
        "changedByAdmin": false
      },
      {
        "date": "2024-01-21",
        "matchDate": null,
        "rating": 4.7705483,
        "changedByAdmin": true
      },
      {
        "date": "2024-01-21",
        "matchDate": "2024-01-21",
        "rating": 4.798022,
        "changedByAdmin": false
      },
      {
        "date": "2024-01-30",
        "matchDate": null,
        "rating": 4.798022,
        "changedByAdmin": true
      },
      {
        "date": "2024-01-30",
        "matchDate": null,
        "rating": 4.85255462947715,
        "changedByAdmin": true
      },
      {
        "date": "2024-02-11",
        "matchDate": "2024-02-11",
        "rating": 4.858493571673026,
        "changedByAdmin": false
      },
      {
        "date": "2024-02-11",
        "matchDate": "2024-02-11",
        "rating": 4.836935614366338,
        "changedByAdmin": false
      },
      {
        "date": "2024-02-11",
        "matchDate": "2024-02-11",
        "rating": 4.85678752953923,
        "changedByAdmin": false
      },
      {
        "date": "2024-02-11",
        "matchDate": "2024-02-11",
        "rating": 4.846877117078061,
        "changedByAdmin": false
      },
      {
        "date": "2024-02-11",
        "matchDate": "2024-02-11",
        "rating": 4.837831697918033,
        "changedByAdmin": false
      },
      {
        "date": "2024-02-11",
        "matchDate": "2024-02-11",
        "rating": 4.846709933307787,
        "changedByAdmin": false
      },
      {
        "date": "2024-02-18",
        "matchDate": "2024-02-17",
        "rating": 4.837442949640436,
        "changedByAdmin": false
      },
      {
        "date": "2024-02-18",
        "matchDate": "2024-02-17",
        "rating": 4.849834585795337,
        "changedByAdmin": false
      },
      {
        "date": "2024-02-18",
        "matchDate": "2024-02-17",
        "rating": 4.874885697120123,
        "changedByAdmin": false
      },
      {
        "date": "2024-02-18",
        "matchDate": "2024-02-17",
        "rating": 4.887188161851601,
        "changedByAdmin": false
      },
      {
        "date": "2024-03-02",
        "matchDate": "2024-03-01",
        "rating": 4.89360804855435,
        "changedByAdmin": false
      },
      {
        "date": "2024-03-02",
        "matchDate": "2024-03-01",
        "rating": 4.916932712965442,
        "changedByAdmin": false
      },
      {
        "date": "2024-03-02",
        "matchDate": "2024-03-01",
        "rating": 4.922355450153007,
        "changedByAdmin": false
      },
      {
        "date": "2024-03-02",
        "matchDate": "2024-03-01",
        "rating": 4.911834201886439,
        "changedByAdmin": false
      },
      {
        "date": "2024-03-24",
        "matchDate": "2024-03-24",
        "rating": 4.901957759671955,
        "changedByAdmin": false
      },
      {
        "date": "2024-03-24",
        "matchDate": "2024-03-24",
        "rating": 4.9157754596861505,
        "changedByAdmin": false
      },
      {
        "date": "2024-04-11",
        "matchDate": null,
        "rating": 4.915611,
        "changedByAdmin": true
      },
      {
        "date": "2024-04-11",
        "matchDate": null,
        "rating": 4.9158106,
        "changedByAdmin": true
      },
      {
        "date": "2024-04-11",
        "matchDate": null,
        "rating": 4.915314,
        "changedByAdmin": true
      },
      {
        "date": "2024-04-11",
        "matchDate": null,
        "rating": 4.91504,
        "changedByAdmin": true
      }
    ]
  }
}```
```
