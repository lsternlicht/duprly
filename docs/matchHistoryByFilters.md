## request

```bash
curl -X POST "https://api.dupr.gg/player/v1.0/7752563844/history" -H "accept: application/json" -H "Authorization: Bearer eyJhbGciOiJSUzUxMiJ9.eyJpc3MiOiJodHRwczovL2R1cHIuZ2ciLCJpYXQiOjE3MzM0MTMwNzksImp0aSI6IjczODk0NjUzOTUiLCJleHAiOjE3MzYwMDUwNzksInN1YiI6IlltbGpaWEF1Y0d4aGFXNWxjall5UUdsamJHOTFaQzVqYjIwPSJ9.Tj_tMthgRlweI9al6Jnazr9p0qrDcVLVN6BRLCV7QbW8yj_LYBbn3EEiPw6vjGqRp7uTudY-Y2WHEl6W75hQfLIqIGywkdBUsw_9NDxsOx2elDv5-j-24H7kY1O-NcLHaJKY4s3fTvpbDvuMq0T1mdS_KTNtPy4TLSE4zkfWzr_2NosaS2PNF7LJO2qz16QgO_vvlyC5lY2ciZAszVCekG6n2DnUie3JtnPwj3w2FWaxO2jYKiWad9bJH2yo9JRj8wN-1uoUCWfDrgaTgzLvJgb1ECPeY9CrN-qBfzPM02OtK-E_-nBYt7NzlCrJ1JftOm6fhiW_6pcOF4VicgIAag" -H "Content-Type: application/json" -d "{ \"filters\": { \"eventFormat\": null }, \"limit\": 10, \"offset\": 0, \"sort\": { \"order\": \"DESC\", \"parameter\": \"MATCH_DATE\" }}"
```

### request notes

- id (required)
- request object body example:

```json
{
  "filters": {
    "eventFormat": null
  },
  "limit": 10,
  "offset": 0,
  "sort": {
    "order": "DESC",
    "parameter": "MATCH_DATE"
  }

```

### creating scraper notes

The response value will contain a total hits value. Use the total hits value to compute the number of requests necessary to retrieve all results. Each new request should increment the offset by the limit (e.g. 10 in the example above).

## response

```json




{
  "status": "SUCCESS",
  "result": {
    "offset": 0,
    "limit": 10,
    "total": 173,
    "hits": [
      {
        "id": 6506226886,
        "matchId": 6506226886,
        "userId": 5524434911,
        "displayIdentity": "XJRJ2WOX7",
        "venue": "235 W 33rd St, New York, NY 10119, USA",
        "location": "235 W 33rd St, New York, NY 10119, USA",
        "matchScoreAdded": true,
        "league": "Life Time NYC Mid-Week Singles Moneyball 4.5+",
        "eventDate": "2024-10-19",
        "eventFormat": "SINGLES",
        "confirmed": true,
        "teams": [
          {
            "id": 7911735156,
            "serial": 1,
            "player1": {
              "id": 5786824611,
              "fullName": "Justin Pagan",
              "duprId": "MYOJPL",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 4.807,
                "doubles": 5.386
              },
              "validatedMatch": false
            },
            "game1": 11,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": true,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": 4.77789,
              "matchSingleRatingImpactPlayer1": 0.029027371763906906,
              "preMatchDoubleRatingPlayer1": null,
              "matchDoubleRatingImpactPlayer1": null,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": null,
              "matchDoubleRatingImpactPlayer2": null
            }
          },
          {
            "id": 5096127533,
            "serial": 2,
            "player1": {
              "id": 7752563844,
              "fullName": "Aidan Bai",
              "duprId": "3XLNYX",
              "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/image_cropper_1684951813472.jpg",
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 4.302,
                "doubles": 4.941
              },
              "validatedMatch": false
            },
            "game1": 3,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": false,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": 4.35552,
              "matchSingleRatingImpactPlayer1": -0.05376940525081242,
              "preMatchDoubleRatingPlayer1": null,
              "matchDoubleRatingImpactPlayer1": null,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": null,
              "matchDoubleRatingImpactPlayer2": null
            }
          }
        ],
        "created": "2024-10-19T15:24:56.617903Z",
        "modified": "2024-10-19T16:10:26.555325Z",
        "eventName": "Life Time NYC Mid-Week Singles Moneyball 4.5+",
        "matchSource": "CLUB",
        "clubId": 4624955558,
        "noOfGames": 1,
        "status": "ACTIVE",
        "matchType": "SIDE_ONLY",
        "eloCalculated": true,
        "initialization": false
      },
      {
        "id": 6394542949,
        "matchId": 6394542949,
        "userId": 5524434911,
        "displayIdentity": "V7J07D67P",
        "venue": "235 W 33rd St, New York, NY 10119, USA",
        "location": "235 W 33rd St, New York, NY 10119, USA",
        "matchScoreAdded": true,
        "league": "Life Time NYC Mid-Week Singles Moneyball 4.5+",
        "eventDate": "2024-10-19",
        "eventFormat": "SINGLES",
        "confirmed": true,
        "teams": [
          {
            "id": 8563347153,
            "serial": 1,
            "player1": {
              "id": 7752563844,
              "fullName": "Aidan Bai",
              "duprId": "3XLNYX",
              "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/image_cropper_1684951813472.jpg",
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 4.356,
                "doubles": 4.941
              },
              "validatedMatch": false
            },
            "game1": 11,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": true,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": 3.84291,
              "matchSingleRatingImpactPlayer1": 0.5126184342819906,
              "preMatchDoubleRatingPlayer1": null,
              "matchDoubleRatingImpactPlayer1": null,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": null,
              "matchDoubleRatingImpactPlayer2": null
            }
          },
          {
            "id": 7295459627,
            "serial": 2,
            "player1": {
              "id": 6768050176,
              "fullName": "Simon corney",
              "duprId": "GG5EZQ",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 4.372,
                "doubles": 4.351
              },
              "validatedMatch": false
            },
            "game1": 1,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": false,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": 4.43121,
              "matchSingleRatingImpactPlayer1": -0.05906585026841871,
              "preMatchDoubleRatingPlayer1": null,
              "matchDoubleRatingImpactPlayer1": null,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": null,
              "matchDoubleRatingImpactPlayer2": null
            }
          }
        ],
        "created": "2024-10-19T15:24:56.427552Z",
        "modified": "2024-10-19T16:10:24.932697Z",
        "eventName": "Life Time NYC Mid-Week Singles Moneyball 4.5+",
        "matchSource": "CLUB",
        "clubId": 4624955558,
        "noOfGames": 1,
        "status": "ACTIVE",
        "matchType": "SIDE_ONLY",
        "eloCalculated": true,
        "initialization": false
      },
      {
        "id": 5374439410,
        "matchId": 5374439410,
        "userId": 5524434911,
        "displayIdentity": "NYX7Z0002",
        "venue": "235 W 33rd St, New York, NY 10119, USA",
        "location": "235 W 33rd St, New York, NY 10119, USA",
        "matchScoreAdded": true,
        "league": "Life Time NYC Mid-Week Singles Moneyball 4.5+",
        "eventDate": "2024-10-19",
        "eventFormat": "SINGLES",
        "confirmed": true,
        "teams": [
          {
            "id": 8459324377,
            "serial": 1,
            "player1": {
              "id": 7752563844,
              "fullName": "Aidan Bai",
              "duprId": "3XLNYX",
              "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/image_cropper_1684951813472.jpg",
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 3.843,
                "doubles": 4.941
              },
              "validatedMatch": false
            },
            "game1": 11,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": true,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": 3.60287,
              "matchSingleRatingImpactPlayer1": 0.2400400354727652,
              "preMatchDoubleRatingPlayer1": null,
              "matchDoubleRatingImpactPlayer1": null,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": null,
              "matchDoubleRatingImpactPlayer2": null
            }
          },
          {
            "id": 7267572543,
            "serial": 2,
            "player1": {
              "id": 6222856604,
              "fullName": "Gary Bachrach",
              "duprId": "KXZ5Y6",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 3.786,
                "doubles": null
              },
              "validatedMatch": false
            },
            "game1": 7,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": false,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": 4.02728,
              "matchSingleRatingImpactPlayer1": -0.24117136584577992,
              "preMatchDoubleRatingPlayer1": null,
              "matchDoubleRatingImpactPlayer1": null,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": null,
              "matchDoubleRatingImpactPlayer2": null
            }
          }
        ],
        "created": "2024-10-19T15:24:56.047247Z",
        "modified": "2024-10-19T16:10:21.612656Z",
        "eventName": "Life Time NYC Mid-Week Singles Moneyball 4.5+",
        "matchSource": "CLUB",
        "clubId": 4624955558,
        "noOfGames": 1,
        "status": "ACTIVE",
        "matchType": "SIDE_ONLY",
        "eloCalculated": true,
        "initialization": false
      },
      {
        "id": 4816573862,
        "matchId": 4816573862,
        "userId": 5524434911,
        "displayIdentity": "XJJO6PK94",
        "venue": "235 W 33rd St, New York, NY 10119, USA",
        "location": "235 W 33rd St, New York, NY 10119, USA",
        "matchScoreAdded": true,
        "league": "Life Time NYC Mid-Week Singles Moneyball 4.5+",
        "eventDate": "2024-10-19",
        "eventFormat": "SINGLES",
        "confirmed": true,
        "teams": [
          {
            "id": 5589854691,
            "serial": 1,
            "player1": {
              "id": 7752563844,
              "fullName": "Aidan Bai",
              "duprId": "3XLNYX",
              "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/image_cropper_1684951813472.jpg",
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 3.603,
                "doubles": 4.941
              },
              "validatedMatch": false
            },
            "game1": 11,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": true,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": 3.27433,
              "matchSingleRatingImpactPlayer1": 0.3285443388474465,
              "preMatchDoubleRatingPlayer1": null,
              "matchDoubleRatingImpactPlayer1": null,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": null,
              "matchDoubleRatingImpactPlayer2": null
            }
          },
          {
            "id": 6674618612,
            "serial": 2,
            "player1": {
              "id": 7585584689,
              "fullName": "Jeff Morse",
              "duprId": "4L62RM",
              "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/87SorX89Pxcd0UGCL2NiuJgO.jpg",
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 4.05,
                "doubles": 4.055
              },
              "validatedMatch": false
            },
            "game1": 9,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": false,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": 4.10723,
              "matchSingleRatingImpactPlayer1": -0.0576247342017977,
              "preMatchDoubleRatingPlayer1": null,
              "matchDoubleRatingImpactPlayer1": null,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": null,
              "matchDoubleRatingImpactPlayer2": null
            }
          }
        ],
        "created": "2024-10-19T15:24:55.9024Z",
        "modified": "2024-10-19T16:10:20.355994Z",
        "eventName": "Life Time NYC Mid-Week Singles Moneyball 4.5+",
        "matchSource": "CLUB",
        "clubId": 4624955558,
        "noOfGames": 1,
        "status": "ACTIVE",
        "matchType": "SIDE_ONLY",
        "eloCalculated": true,
        "initialization": false
      },
      {
        "id": 7517532348,
        "matchId": 7517532348,
        "userId": 5524434911,
        "displayIdentity": "DW24N0R06",
        "venue": "235 W 33rd St, New York, NY 10119, USA",
        "location": "235 W 33rd St, New York, NY 10119, USA",
        "matchScoreAdded": true,
        "league": "Life Time NYC Mid-Week Singles Moneyball 4.5+",
        "eventDate": "2024-10-19",
        "eventFormat": "SINGLES",
        "confirmed": true,
        "teams": [
          {
            "id": 8542698888,
            "serial": 1,
            "player1": {
              "id": 8149170258,
              "fullName": "Rohin Rajani",
              "duprId": "7D47W5",
              "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/d506b35d-d1c8-413b-b619-4f5016b820c0.jpg",
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 4.588,
                "doubles": 4.443
              },
              "validatedMatch": false
            },
            "game1": 15,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": true,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": 4.58728,
              "matchSingleRatingImpactPlayer1": 0.0006704601692986145,
              "preMatchDoubleRatingPlayer1": null,
              "matchDoubleRatingImpactPlayer1": null,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": null,
              "matchDoubleRatingImpactPlayer2": null
            }
          },
          {
            "id": 8517828727,
            "serial": 2,
            "player1": {
              "id": 7752563844,
              "fullName": "Aidan Bai",
              "duprId": "3XLNYX",
              "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/image_cropper_1684951813472.jpg",
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 3.274,
                "doubles": 4.941
              },
              "validatedMatch": false
            },
            "game1": 8,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": false,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": 3.27755,
              "matchSingleRatingImpactPlayer1": -0.0032189538036027088,
              "preMatchDoubleRatingPlayer1": null,
              "matchDoubleRatingImpactPlayer1": null,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": null,
              "matchDoubleRatingImpactPlayer2": null
            }
          }
        ],
        "created": "2024-10-19T15:24:55.853481Z",
        "modified": "2024-10-19T16:10:19.881217Z",
        "eventName": "Life Time NYC Mid-Week Singles Moneyball 4.5+",
        "matchSource": "CLUB",
        "clubId": 4624955558,
        "noOfGames": 1,
        "status": "ACTIVE",
        "matchType": "SIDE_ONLY",
        "eloCalculated": true,
        "initialization": false
      },
      {
        "id": 5051623833,
        "matchId": 5051623833,
        "userId": 0,
        "displayIdentity": "GG5YYNW7D",
        "venue": "NY, NY",
        "location": "NY, NY",
        "matchScoreAdded": true,
        "league": "Life Time NYC Fall Classic - Mixed Doubles Skill: (4.5 to Open) Age: (Any)",
        "eventDate": "2024-10-06",
        "eventFormat": "DOUBLES",
        "confirmed": true,
        "teams": [
          {
            "id": 6745528525,
            "serial": 1,
            "player1": {
              "id": 8134392502,
              "fullName": "Pearly Leung",
              "duprId": "9PZNQJ",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 4.562,
                "doubles": 4.824
              },
              "validatedMatch": false
            },
            "player2": {
              "id": 4480693670,
              "fullName": "Nick Retzkin",
              "duprId": "6ZVOMK",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 3.933,
                "doubles": 4.905
              },
              "validatedMatch": false
            },
            "game1": 11,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": true,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": null,
              "matchSingleRatingImpactPlayer1": null,
              "preMatchDoubleRatingPlayer1": 4.79576,
              "matchDoubleRatingImpactPlayer1": 0.02857637147115355,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": 4.89567,
              "matchDoubleRatingImpactPlayer2": 0.009027526758573323
            }
          },
          {
            "id": 6194452361,
            "serial": 2,
            "player1": {
              "id": 5353238939,
              "fullName": "Rosanne Hu",
              "duprId": "DW2WEY",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": null,
                "doubles": 4.156
              },
              "validatedMatch": false
            },
            "player2": {
              "id": 7752563844,
              "fullName": "Aidan Bai",
              "duprId": "3XLNYX",
              "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/image_cropper_1684951813472.jpg",
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 3.278,
                "doubles": 4.941
              },
              "validatedMatch": false
            },
            "game1": 3,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": false,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": null,
              "matchSingleRatingImpactPlayer1": null,
              "preMatchDoubleRatingPlayer1": 4.20421,
              "matchDoubleRatingImpactPlayer1": -0.04858968586690526,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": 4.95894,
              "matchDoubleRatingImpactPlayer2": -0.01802318170018591
            }
          }
        ],
        "created": "2024-10-06T20:01:33.022991Z",
        "modified": "2024-10-06T20:05:18.343814Z",
        "eventName": "Life Time NYC Fall Classic - Mixed Doubles Skill: (4.5 to Open) Age: (Any)",
        "matchSource": "PARTNER",
        "noOfGames": 1,
        "status": "ACTIVE",
        "matchType": "SIDE_ONLY",
        "eloCalculated": true,
        "initialization": false
      },
      {
        "id": 4563718936,
        "matchId": 4563718936,
        "userId": 0,
        "displayIdentity": "M5QE0EEL",
        "venue": "NY, NY",
        "location": "NY, NY",
        "matchScoreAdded": true,
        "league": "Life Time NYC Fall Classic - Mixed Doubles Skill: (4.5 to Open) Age: (Any)",
        "eventDate": "2024-10-06",
        "eventFormat": "DOUBLES",
        "confirmed": true,
        "teams": [
          {
            "id": 8523541893,
            "serial": 1,
            "player1": {
              "id": 5353238939,
              "fullName": "Rosanne Hu",
              "duprId": "DW2WEY",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": null,
                "doubles": 4.204
              },
              "validatedMatch": false
            },
            "player2": {
              "id": 7752563844,
              "fullName": "Aidan Bai",
              "duprId": "3XLNYX",
              "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/image_cropper_1684951813472.jpg",
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 3.278,
                "doubles": 4.959
              },
              "validatedMatch": false
            },
            "game1": 8,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": false,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": null,
              "matchSingleRatingImpactPlayer1": null,
              "preMatchDoubleRatingPlayer1": 4.20817,
              "matchDoubleRatingImpactPlayer1": -0.003950477637635785,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": 4.96031,
              "matchDoubleRatingImpactPlayer2": -0.0013654571351588984
            }
          },
          {
            "id": 5593894208,
            "serial": 2,
            "player1": {
              "id": 5848078031,
              "fullName": "Neely Sullivan",
              "duprId": "16XXXE",
              "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/91e11dd5-70eb-4909-98f6-ed97b1c84dd7.jpg",
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": null,
                "doubles": 5.236
              },
              "validatedMatch": false
            },
            "player2": {
              "id": 7983149761,
              "fullName": "Preston Gordon",
              "duprId": "L5WN66",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 5.583,
                "doubles": 5.522
              },
              "validatedMatch": false
            },
            "game1": 11,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": true,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": null,
              "matchSingleRatingImpactPlayer1": null,
              "preMatchDoubleRatingPlayer1": 5.23555,
              "matchDoubleRatingImpactPlayer1": 0.0009063707359624473,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": 5.52167,
              "matchDoubleRatingImpactPlayer2": 0.0006074586562681006
            }
          }
        ],
        "created": "2024-10-06T19:46:30.266627Z",
        "modified": "2024-10-06T19:50:47.375399Z",
        "eventName": "Life Time NYC Fall Classic - Mixed Doubles Skill: (4.5 to Open) Age: (Any)",
        "matchSource": "PARTNER",
        "noOfGames": 1,
        "status": "ACTIVE",
        "matchType": "SIDE_ONLY",
        "eloCalculated": true,
        "initialization": false
      },
      {
        "id": 4472535128,
        "matchId": 4472535128,
        "userId": 0,
        "displayIdentity": "65XDLZYG",
        "venue": "NY, NY",
        "location": "NY, NY",
        "matchScoreAdded": true,
        "league": "Life Time NYC Fall Classic - Mixed Doubles Skill: (4.5 to Open) Age: (Any)",
        "eventDate": "2024-10-06",
        "eventFormat": "DOUBLES",
        "confirmed": true,
        "teams": [
          {
            "id": 4399942893,
            "serial": 1,
            "player1": {
              "id": 5353238939,
              "fullName": "Rosanne Hu",
              "duprId": "DW2WEY",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": null,
                "doubles": 4.208
              },
              "validatedMatch": false
            },
            "player2": {
              "id": 7752563844,
              "fullName": "Aidan Bai",
              "duprId": "3XLNYX",
              "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/image_cropper_1684951813472.jpg",
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 3.278,
                "doubles": 4.96
              },
              "validatedMatch": false
            },
            "game1": 4,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": false,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": null,
              "matchSingleRatingImpactPlayer1": null,
              "preMatchDoubleRatingPlayer1": 4.25899,
              "matchDoubleRatingImpactPlayer1": -0.050816803991730275,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": 4.97649,
              "matchDoubleRatingImpactPlayer2": -0.016172128883638948
            }
          },
          {
            "id": 6047488747,
            "serial": 2,
            "player1": {
              "id": 6025701891,
              "fullName": "Sarah Mulhern",
              "duprId": "8JN5QW",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 5.467,
                "doubles": 4.455
              },
              "validatedMatch": false
            },
            "player2": {
              "id": 5786824611,
              "fullName": "Justin Pagan",
              "duprId": "MYOJPL",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 4.643,
                "doubles": 5.36
              },
              "validatedMatch": false
            },
            "game1": 11,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": true,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": null,
              "matchSingleRatingImpactPlayer1": null,
              "preMatchDoubleRatingPlayer1": 4.44695,
              "matchDoubleRatingImpactPlayer1": 0.00783031487193675,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": 5.34751,
              "matchDoubleRatingImpactPlayer2": 0.012789457897292245
            }
          }
        ],
        "created": "2024-10-06T19:12:40.610315Z",
        "modified": "2024-10-06T19:20:33.358935Z",
        "eventName": "Life Time NYC Fall Classic - Mixed Doubles Skill: (4.5 to Open) Age: (Any)",
        "matchSource": "PARTNER",
        "noOfGames": 1,
        "status": "ACTIVE",
        "matchType": "SIDE_ONLY",
        "eloCalculated": true,
        "initialization": false
      },
      {
        "id": 4545671297,
        "matchId": 4545671297,
        "userId": 0,
        "displayIdentity": "VWMEZKR5",
        "venue": "NY, NY",
        "location": "NY, NY",
        "matchScoreAdded": true,
        "league": "Life Time NYC Fall Classic - Mixed Doubles Skill: (4.5 to Open) Age: (Any)",
        "eventDate": "2024-10-06",
        "eventFormat": "DOUBLES",
        "confirmed": true,
        "teams": [
          {
            "id": 4879765765,
            "serial": 1,
            "player1": {
              "id": 5353238939,
              "fullName": "Rosanne Hu",
              "duprId": "DW2WEY",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": null,
                "doubles": 4.259
              },
              "validatedMatch": false
            },
            "player2": {
              "id": 7752563844,
              "fullName": "Aidan Bai",
              "duprId": "3XLNYX",
              "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/image_cropper_1684951813472.jpg",
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 3.278,
                "doubles": 4.976
              },
              "validatedMatch": false
            },
            "game1": 11,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": true,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": null,
              "matchSingleRatingImpactPlayer1": null,
              "preMatchDoubleRatingPlayer1": 4.15785,
              "matchDoubleRatingImpactPlayer1": 0.10114184472592669,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": 4.94732,
              "matchDoubleRatingImpactPlayer2": 0.02917426248552335
            }
          },
          {
            "id": 4605247584,
            "serial": 2,
            "player1": {
              "id": 6081726863,
              "fullName": "marina todd",
              "duprId": "0QLVDN",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 4.396,
                "doubles": 3.983
              },
              "validatedMatch": false
            },
            "player2": {
              "id": 6876956732,
              "fullName": "Dylan Debiase",
              "duprId": "1NKW42",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 5.087,
                "doubles": 4.621
              },
              "validatedMatch": false
            },
            "game1": 1,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": false,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": null,
              "matchSingleRatingImpactPlayer1": null,
              "preMatchDoubleRatingPlayer1": 4.00415,
              "matchDoubleRatingImpactPlayer1": -0.02096859383091365,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": 4.63211,
              "matchDoubleRatingImpactPlayer2": -0.010864272603338776
            }
          }
        ],
        "created": "2024-10-06T18:34:00.598025Z",
        "modified": "2024-10-06T18:35:25.004438Z",
        "eventName": "Life Time NYC Fall Classic - Mixed Doubles Skill: (4.5 to Open) Age: (Any)",
        "matchSource": "PARTNER",
        "noOfGames": 1,
        "status": "ACTIVE",
        "matchType": "SIDE_ONLY",
        "eloCalculated": true,
        "initialization": false
      },
      {
        "id": 5731476539,
        "matchId": 5731476539,
        "userId": 0,
        "displayIdentity": "ZN4PQDY9L",
        "venue": "NY, NY",
        "location": "NY, NY",
        "matchScoreAdded": true,
        "league": "Life Time NYC Fall Classic - Mixed Doubles Skill: (4.5 to Open) Age: (Any)",
        "eventDate": "2024-10-06",
        "eventFormat": "DOUBLES",
        "confirmed": true,
        "teams": [
          {
            "id": 6437362496,
            "serial": 1,
            "player1": {
              "id": 4482838298,
              "fullName": "Carina Szabo",
              "duprId": "8WQLNY",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 4.461,
                "doubles": 4.741
              },
              "validatedMatch": false
            },
            "player2": {
              "id": 7740296186,
              "fullName": "Jake Sandler",
              "duprId": "8GD6MX",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 5.18,
                "doubles": 5.025
              },
              "validatedMatch": false
            },
            "game1": 11,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": true,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": null,
              "matchSingleRatingImpactPlayer1": null,
              "preMatchDoubleRatingPlayer1": 4.71859,
              "matchDoubleRatingImpactPlayer1": 0.022150370129037533,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": 4.99767,
              "matchDoubleRatingImpactPlayer2": 0.026906646332190753
            }
          },
          {
            "id": 4763806316,
            "serial": 2,
            "player1": {
              "id": 5353238939,
              "fullName": "Rosanne Hu",
              "duprId": "DW2WEY",
              "imageUrl": null,
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": null,
                "doubles": 4.158
              },
              "validatedMatch": false
            },
            "player2": {
              "id": 7752563844,
              "fullName": "Aidan Bai",
              "duprId": "3XLNYX",
              "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/image_cropper_1684951813472.jpg",
              "allowSubstitution": true,
              "postMatchRating": {
                "singles": 3.278,
                "doubles": 4.947
              },
              "validatedMatch": false
            },
            "game1": 3,
            "game2": -1,
            "game3": -1,
            "game4": -1,
            "game5": -1,
            "winner": false,
            "delta": "",
            "teamRating": "",
            "preMatchRatingAndImpact": {
              "preMatchSingleRatingPlayer1": null,
              "matchSingleRatingImpactPlayer1": null,
              "preMatchDoubleRatingPlayer1": 4.24176,
              "matchDoubleRatingImpactPlayer1": -0.08390772602984509,
              "preMatchSingleRatingPlayer2": null,
              "matchSingleRatingImpactPlayer2": null,
              "preMatchDoubleRatingPlayer2": 4.9688,
              "matchDoubleRatingImpactPlayer2": -0.0214745882430476
            }
          }
        ],
        "created": "2024-10-06T18:17:40.048265Z",
        "modified": "2024-10-06T18:20:27.175695Z",
        "eventName": "Life Time NYC Fall Classic - Mixed Doubles Skill: (4.5 to Open) Age: (Any)",
        "matchSource": "PARTNER",
        "noOfGames": 1,
        "status": "ACTIVE",
        "matchType": "SIDE_ONLY",
        "eloCalculated": true,
        "initialization": false
      }
    ],
    "totalValueRelation": null,
    "hasMore": true,
    "hasPrevious": false,
    "empty": false
  }
}

```

```

```
