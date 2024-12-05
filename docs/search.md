# DUPR API name search

> This API request is great for retrieving the user's id, which is used in many other types of requests (match history, rating, etc.)

## request

```bash
curl -X POST "https://api.dupr.gg/player/v1.0/search" -H "accept: application/json" -H "Authorization: Bearer eyJhbGciOiJSUzUxMiJ9.eyJpc3MiOiJodHRwczovL2R1cHIuZ2ciLCJpYXQiOjE3MzM0MTMwNzksImp0aSI6IjczODk0NjUzOTUiLCJleHAiOjE3MzYwMDUwNzksInN1YiI6IlltbGpaWEF1Y0d4aGFXNWxjall5UUdsamJHOTFaQzVqYjIwPSJ9.Tj_tMthgRlweI9al6Jnazr9p0qrDcVLVN6BRLCV7QbW8yj_LYBbn3EEiPw6vjGqRp7uTudY-Y2WHEl6W75hQfLIqIGywkdBUsw_9NDxsOx2elDv5-j-24H7kY1O-NcLHaJKY4s3fTvpbDvuMq0T1mdS_KTNtPy4TLSE4zkfWzr_2NosaS2PNF7LJO2qz16QgO_vvlyC5lY2ciZAszVCekG6n2DnUie3JtnPwj3w2FWaxO2jYKiWad9bJH2yo9JRj8wN-1uoUCWfDrgaTgzLvJgb1ECPeY9CrN-qBfzPM02OtK-E_-nBYt7NzlCrJ1JftOm6fhiW_6pcOF4VicgIAag" -H "Content-Type: application/json" -d "{ \"limit\": 10, \"offset\": 0, \"query\": \"aidan bai\", \"exclude\": [], \"includeUnclaimedPlayers\": true, \"filter\": { \"lat\": 40.7127753, \"lng\": -74.0059728, \"rating\": { \"maxRating\": null, \"minRating\": null }, \"locationText\": \"\" }}"
```

## request notes

- request object (body) format example:

```json
{
    "limit": 10,
    "offset": 0,
    "query": "aidan bai",
    "exclude": [],
    "includeUnclaimedPlayers": true,
    "filter": {
        "lat": 40.7127753,
        "lng": -74.0059728,
        "rating": {
            "maxRating": null,
            "minRating": null
        },
        "locationText": ""
    }
}
```

    - note that the query filters the results by matching player names

## response

```json
{
    "status": "SUCCESS",
    "result": {
        "offset": 0,
        "limit": 10,
        "total": 4,
        "hits": [
            {
                "id": 7752563844,
                "fullName": "Aidan Bai",
                "firstName": "Aidan",
                "lastName": "Bai",
                "shortAddress": "New York, NY, US",
                "gender": "MALE",
                "age": 19,
                "hand": "RIGHT",
                "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/image_cropper_1684951813472.jpg",
                "ratings": {
                    "singles": "4.302",
                    "singlesVerified": "NR",
                    "singlesProvisional": false,
                    "singlesReliabilityScore": 62,
                    "doubles": "5.006",
                    "doublesVerified": "NR",
                    "doublesProvisional": false,
                    "doublesReliabilityScore": 99,
                    "defaultRating": "DOUBLES",
                    "provisionalRatings": {
                        "singlesRating": 0,
                        "doublesRating": 0
                    }
                },
                "distance": "1.3 mi",
                "enablePrivacy": false,
                "distanceInMiles": 1.3,
                "isPlayer1": true,
                "verifiedEmail": true,
                "registered": true,
                "duprId": "3XLNYX",
                "showRatingBanner": false,
                "status": "ACTIVE",
                "sponsor": {},
                "lucraConnected": false
            },
            {
                "id": 7492993759,
                "fullName": "Aidan A Bailey",
                "firstName": "Aidan A",
                "lastName": "Bailey",
                "shortAddress": "Ogden, UT, US",
                "gender": "MALE",
                "age": 26,
                "hand": "RIGHT",
                "imageUrl": "https://dupr.s3.us-east-1.amazonaws.com/images/image_cropper_1668838338373.jpg",
                "ratings": {
                    "singles": "NR",
                    "singlesVerified": "NR",
                    "singlesProvisional": false,
                    "singlesReliabilityScore": 0,
                    "doubles": "2.689",
                    "doublesVerified": "NR",
                    "doublesProvisional": true,
                    "doublesReliabilityScore": 1,
                    "defaultRating": "DOUBLES",
                    "provisionalRatings": {
                        "singlesRating": 0,
                        "doublesRating": 0
                    }
                },
                "distance": "1965.2 mi",
                "enablePrivacy": false,
                "distanceInMiles": 1965.2,
                "isPlayer1": true,
                "verifiedEmail": true,
                "registered": true,
                "duprId": "17LO5N",
                "showRatingBanner": false,
                "status": "ACTIVE",
                "sponsor": {},
                "lucraConnected": false
            },
            {
                "id": 6560829353,
                "fullName": "Aidan Baigrie",
                "firstName": "Aidan",
                "lastName": "Baigrie",
                "shortAddress": "Laguna Beach, CA, US",
                "gender": "MALE",
                "age": 46,
                "ratings": {
                    "singles": "NR",
                    "singlesVerified": "NR",
                    "singlesProvisional": false,
                    "doubles": "NR",
                    "doublesVerified": "NR",
                    "doublesProvisional": false,
                    "defaultRating": "DOUBLES",
                    "provisionalRatings": {
                        "singlesRating": 0,
                        "doublesRating": 0
                    }
                },
                "distance": "2435.1 mi",
                "enablePrivacy": false,
                "distanceInMiles": 2435.1,
                "isPlayer1": true,
                "verifiedEmail": true,
                "registered": true,
                "duprId": "8MQWMG",
                "showRatingBanner": false,
                "status": "ACTIVE",
                "sponsor": {},
                "lucraConnected": false
            },
            {
                "id": 4586546062,
                "fullName": "Aidan Bai",
                "ratings": {
                    "singles": "4.211",
                    "singlesVerified": "NR",
                    "singlesProvisional": true,
                    "singlesReliabilityScore": 1,
                    "doubles": "NR",
                    "doublesVerified": "NR",
                    "doublesProvisional": false,
                    "doublesReliabilityScore": 0,
                    "defaultRating": "DOUBLES",
                    "provisionalRatings": {
                        "singlesRating": 0,
                        "doublesRating": 0
                    }
                },
                "distance": "5385.5 mi",
                "enablePrivacy": false,
                "distanceInMiles": 5385.5,
                "isPlayer1": true,
                "verifiedEmail": false,
                "registrationType": "UNCLAIMED",
                "registered": false,
                "duprId": "0YQDON",
                "showRatingBanner": false,
                "status": "INACTIVE",
                "sponsor": {},
                "lucraConnected": false
            }
        ],
        "totalValueRelation": "EQUAL_TO",
        "hasMore": false,
        "hasPrevious": false,
        "empty": false
    }
}```
```
