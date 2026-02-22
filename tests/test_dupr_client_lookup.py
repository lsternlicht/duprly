import unittest
from unittest.mock import MagicMock

from duprly.dupr_client import DuprClient


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class DuprClientLookupTests(unittest.TestCase):
    def setUp(self):
        self.client = DuprClient()

    def test_search_players_payload_and_hits(self):
        expected_hits = [{"id": 7752563844, "fullName": "Aidan Bai"}]
        self.client.dupr_post = MagicMock(
            return_value=FakeResponse(
                200,
                {"result": {"hits": expected_hits}},
            )
        )

        status, hits = self.client.search_players(
            query="aidan bai",
            limit=5,
            include_unclaimed=True,
            lat=40.7,
            lng=-74.0,
            radius_meters=16093.4,
        )

        self.assertEqual(status, 200)
        self.assertEqual(hits, expected_hits)
        self.client.dupr_post.assert_called_once()
        call = self.client.dupr_post.call_args
        self.assertEqual(call.kwargs["name"], "search_players")
        self.assertEqual(call.args[0], "/player/v1.0/search")
        payload = call.kwargs["json_data"]
        self.assertEqual(payload["query"], "aidan bai")
        self.assertEqual(payload["limit"], 5)
        self.assertTrue(payload["includeUnclaimedPlayers"])
        self.assertEqual(payload["filter"]["lat"], 40.7)
        self.assertEqual(payload["filter"]["lng"], -74.0)
        self.assertEqual(payload["filter"]["locationText"], "")
        self.assertIsNone(payload["filter"]["rating"]["minRating"])
        self.assertIsNone(payload["filter"]["rating"]["maxRating"])
        self.assertEqual(payload["filter"]["radiusInMeters"], 16093.4)

    def test_search_clubs_payload_matches_browser_shape(self):
        expected_hits = [{"clubId": 8436164521, "clubName": "NYC Pickleball"}]
        self.client.dupr_post = MagicMock(
            return_value=FakeResponse(
                200,
                {"result": {"hits": expected_hits}},
            )
        )

        status, hits = self.client.search_clubs(query="nyc pi", limit=18)

        self.assertEqual(status, 200)
        self.assertEqual(hits, expected_hits)
        call = self.client.dupr_post.call_args
        self.assertEqual(call.kwargs["name"], "search_clubs")
        self.assertEqual(call.args[0], "/club/v1.0/all")
        payload = call.kwargs["json_data"]
        self.assertEqual(payload["query"], "nyc pi")
        self.assertEqual(payload["limit"], 18)
        self.assertEqual(payload["offset"], 0)
        self.assertNotIn("own", payload)

    def test_get_member_match_history_all_paginates(self):
        page_1 = FakeResponse(
            200,
            {
                "result": {
                    "offset": 0,
                    "limit": 2,
                    "total": 3,
                    "hasMore": True,
                    "hits": [{"matchId": 1}, {"matchId": 2}],
                }
            },
        )
        page_2 = FakeResponse(
            200,
            {
                "result": {
                    "offset": 2,
                    "limit": 2,
                    "total": 3,
                    "hasMore": False,
                    "hits": [{"matchId": 3}],
                }
            },
        )
        self.client.dupr_post = MagicMock(side_effect=[page_1, page_2])

        status, matches = self.client.get_member_match_history_all("7752563844", limit=2)

        self.assertEqual(status, 200)
        self.assertEqual([m["matchId"] for m in matches], [1, 2, 3])
        self.assertEqual(self.client.dupr_post.call_count, 2)
        first_call = self.client.dupr_post.call_args_list[0]
        second_call = self.client.dupr_post.call_args_list[1]
        self.assertEqual(first_call.args[0], "/player/v1.0/7752563844/history")
        self.assertEqual(second_call.args[0], "/player/v1.0/7752563844/history")
        self.assertEqual(first_call.kwargs["json_data"]["offset"], 0)
        self.assertEqual(second_call.kwargs["json_data"]["offset"], 2)
        self.assertEqual(first_call.kwargs["json_data"]["filters"]["eventFormat"], None)
        self.assertEqual(first_call.kwargs["json_data"]["sort"]["parameter"], "MATCH_DATE")

    def test_get_member_match_history_range_posts_expected_body(self):
        response = FakeResponse(
            200,
            {
                "result": {
                    "offset": 0,
                    "limit": 50,
                    "total": 1,
                    "hasMore": False,
                    "hits": [{"matchId": 42}],
                }
            },
        )
        self.client.dupr_post = MagicMock(return_value=response)

        status, matches = self.client.get_member_match_history_range(
            member_id="7752563844",
            start_date="2024-01-01",
            end_date="2024-12-31",
            limit=50,
        )

        self.assertEqual(status, 200)
        self.assertEqual(matches[0]["matchId"], 42)
        call = self.client.dupr_post.call_args
        self.assertEqual(call.args[0], "/player/v1.0/7752563844/history")
        payload = call.kwargs["json_data"]
        self.assertEqual(payload["filters"]["eventDate"]["startDate"], "2024-01-01")
        self.assertEqual(payload["filters"]["eventDate"]["endDate"], "2024-12-31")
        self.assertEqual(payload["filters"]["eventFormat"], None)
        self.assertEqual(payload["sort"]["parameter"], "MATCH_DATE")
        self.assertEqual(payload["limit"], 50)
        self.assertNotIn("eventName", payload["filters"])
        self.assertNotIn("matchStatus", payload["filters"])

    def test_get_player_rating_history_posts_expected_body_and_paginates(self):
        page_1 = FakeResponse(
            200,
            {
                "result": {
                    "offset": 0,
                    "limit": 2,
                    "total": 3,
                    "hasMore": True,
                    "ratingHistory": [{"date": "2026-01-01", "rating": 4.1}, {"date": "2026-01-02", "rating": 4.2}],
                }
            },
        )
        page_2 = FakeResponse(
            200,
            {
                "result": {
                    "offset": 2,
                    "limit": 2,
                    "total": 3,
                    "hasMore": False,
                    "ratingHistory": [{"date": "2026-01-03", "rating": 4.3}],
                }
            },
        )
        self.client.dupr_post = MagicMock(side_effect=[page_1, page_2])

        status, rows = self.client.get_player_rating_history(
            member_id="7752563844",
            rating_type="DOUBLES",
            start_date="2025-12-14",
            end_date="2026-02-21",
            limit=2,
        )

        self.assertEqual(status, 200)
        self.assertEqual(len(rows), 3)
        self.assertEqual(self.client.dupr_post.call_count, 2)
        first_call = self.client.dupr_post.call_args_list[0]
        payload = first_call.kwargs["json_data"]
        self.assertEqual(first_call.args[0], "/player/v1.0/7752563844/rating-history")
        self.assertEqual(payload["type"], "DOUBLES")
        self.assertEqual(payload["startDate"], "2025-12-14")
        self.assertEqual(payload["endDate"], "2026-02-21")
        self.assertEqual(payload["sortBy"], "asc")

    def test_get_player_calculated_stats_returns_result(self):
        self.client.dupr_get = MagicMock(
            return_value=FakeResponse(
                200,
                {"result": {"doubles": {"wins": 3}, "singles": {"wins": 1}}},
            )
        )
        status, data = self.client.get_player_calculated_stats("7752563844")
        self.assertEqual(status, 200)
        self.assertEqual(data["doubles"]["wins"], 3)
        self.client.dupr_get.assert_called_once()
        self.assertEqual(
            self.client.dupr_get.call_args.args[0],
            "/user/calculated/v1.0/stats/7752563844",
        )


if __name__ == "__main__":
    unittest.main()
